"""Incremental, checkpointed source synchronization."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Protocol, cast, runtime_checkable

from sys4ai_memory.contracts import ErrorCategory, MemoryRecord, SourceRecord
from sys4ai_memory.profiles import ProfileSet
from sys4ai_memory.sources.discovery import DiscoveryReport

from .adapters import DEFAULT_PROFILE_VERSION, OptionalSourceAdapter, normalize_source
from .manifest import compare_manifests
from .models import (
    IngestionFailure,
    NormalizedDocument,
    SourceChange,
    SourceChangeKind,
    SourceDelta,
    SourceManifest,
    SourceManifestEntry,
    SyncCheckpoint,
    SyncResult,
)


class IndexWriter(Protocol):
    """Narrow exact-index boundary used by source synchronization."""

    def upsert_document(
        self, document: NormalizedDocument, *, generation_id: str | None = None
    ) -> object: ...

    def mark_source_deleted(
        self, project_id: str, source_id: str, *, generation_id: str | None = None
    ) -> object: ...


@runtime_checkable
class RecordHistoryReader(Protocol):
    """Read current typed records before assigning the next source revision."""

    def current_source_records(
        self,
        *,
        project_id: str,
        source_id: str,
    ) -> tuple[MemoryRecord, ...]: ...


def _comparison_payload(record: MemoryRecord) -> dict[str, object]:
    payload = cast(dict[str, object], record.to_json_dict())
    payload.pop("version", None)
    payload.pop("created_at", None)
    payload.pop("updated_at", None)
    processing = payload.get("processing")
    if isinstance(processing, dict):
        processing.pop("processed_at", None)
    return payload


def _assign_record_versions(
    document: NormalizedDocument,
    prior_records: tuple[MemoryRecord, ...],
) -> NormalizedDocument:
    prior_by_id = {record.record_id: record for record in prior_records}
    revised: list[MemoryRecord] = []
    for record in document.records:
        prior = prior_by_id.get(record.record_id)
        if prior is None:
            revised.append(record)
        elif _comparison_payload(prior) == _comparison_payload(record):
            revised.append(prior)
        else:
            revised.append(
                record.model_copy(
                    update={
                        "version": prior.version + 1,
                        "created_at": prior.created_at,
                    }
                )
            )
    return replace(document, records=tuple(revised))


class IngestionSynchronizer:
    """Synchronize each source independently so one failure preserves others."""

    def __init__(
        self,
        *,
        project_root: Path,
        index_writer: IndexWriter | None = None,
        max_file_bytes: int = 8 * 1024 * 1024,
        max_chunk_chars: int = 64 * 1024,
        profile_version: str = DEFAULT_PROFILE_VERSION,
        profile_set: ProfileSet | None = None,
        optional_adapters: tuple[OptionalSourceAdapter, ...] = (),
    ) -> None:
        self.project_root = project_root
        self.index_writer = index_writer
        self.max_file_bytes = max_file_bytes
        self.max_chunk_chars = max_chunk_chars
        self.profile_version = profile_version
        self.profile_set = profile_set
        self.optional_adapters = optional_adapters
        self.record_history = (
            index_writer if isinstance(index_writer, RecordHistoryReader) else None
        )

    def synchronize(
        self,
        report: DiscoveryReport,
        *,
        previous_manifest: SourceManifest | None = None,
        checkpoint: SyncCheckpoint | None = None,
        processed_at: datetime | None = None,
        generation_id: str | None = None,
        force: bool = False,
    ) -> SyncResult:
        if report.project_root.resolve(strict=True) != self.project_root.resolve(strict=True):
            raise ValueError("discovery report root does not match synchronizer root")
        previous = previous_manifest or SourceManifest(report.project_id, ())
        if previous.project_id != report.project_id:
            raise ValueError("previous manifest project does not match discovery report")
        current_checkpoint = checkpoint or SyncCheckpoint(report.project_id)
        if current_checkpoint.project_id != report.project_id:
            raise ValueError("checkpoint project does not match discovery report")

        sources = self._recover_moved_ids(report.records, previous)
        planned_manifest = SourceManifest.from_records(report.project_id, sources)
        planned_delta = compare_manifests(previous, planned_manifest)
        change_by_id = {change.source_id: change for change in planned_delta.changes}
        documents: list[NormalizedDocument] = []
        failures: list[IngestionFailure] = []
        skipped: list[str] = []
        manifest_entries: list[SourceManifestEntry] = []

        for source in sorted(sources, key=lambda item: item.source_id):
            assert source.content_sha256 is not None
            change = change_by_id.get(source.source_id)
            failed_before = current_checkpoint.failure_for(source.source_id) is not None
            unchanged = change is not None and change.change is SourceChangeKind.UNCHANGED
            if (
                not force
                and not failed_before
                and (
                    unchanged
                    or current_checkpoint.is_complete(source.source_id, source.content_sha256)
                )
            ):
                manifest_entries.append(SourceManifestEntry.from_source_record(source))
                skipped.append(source.source_id)
                continue
            try:
                profile_version, profile_lineage = self._source_profile(source)
                document = normalize_source(
                    self.project_root,
                    source,
                    processed_at=processed_at,
                    profile_version=profile_version,
                    max_file_bytes=self.max_file_bytes,
                    max_chunk_chars=self.max_chunk_chars,
                    optional_adapters=self.optional_adapters,
                )
                self._validate_profile_document(document, profile_lineage)
                if self.record_history is not None:
                    document = _assign_record_versions(
                        document,
                        self.record_history.current_source_records(
                            project_id=source.project_id,
                            source_id=source.source_id,
                        ),
                    )
                if self.index_writer is not None:
                    self.index_writer.upsert_document(document, generation_id=generation_id)
            except IngestionFailure as error:
                failures.append(error)
                current_checkpoint = current_checkpoint.mark_failed(
                    source.source_id, error.category.value
                )
                manifest_entries.append(
                    replace(
                        SourceManifestEntry.from_source_record(source),
                        status="failed",
                        error_category=error.category.value,
                    )
                )
                continue
            except Exception as error:
                failure = IngestionFailure(
                    source_id=source.source_id,
                    adapter=source.ingestion_adapter,
                    stage="index",
                    category=ErrorCategory.INGESTION_FAILED,
                    message="the derived exact index rejected this source transaction",
                    recovery_action=(
                        "inspect the index health and resume from the source checkpoint"
                    ),
                )
                failure.__cause__ = error
                failures.append(failure)
                current_checkpoint = current_checkpoint.mark_failed(
                    source.source_id, failure.category.value
                )
                manifest_entries.append(
                    replace(
                        SourceManifestEntry.from_source_record(source),
                        status="failed",
                        error_category=failure.category.value,
                    )
                )
                continue
            documents.append(document)
            manifest_entries.append(SourceManifestEntry.from_source_record(source))
            current_checkpoint = current_checkpoint.mark_complete(
                source.source_id, source.content_sha256
            )

        deleted = planned_delta.of_kind(SourceChangeKind.DELETED)
        for change in deleted:
            if self.index_writer is None:
                continue
            try:
                self.index_writer.mark_source_deleted(
                    report.project_id, change.source_id, generation_id=generation_id
                )
            except Exception as error:
                failure = IngestionFailure(
                    source_id=change.source_id,
                    adapter="exact_index",
                    stage="delete_reconciliation",
                    category=ErrorCategory.INGESTION_FAILED,
                    message="the exact index could not reconcile a deleted source",
                    recovery_action="inspect index health and resume deletion reconciliation",
                )
                failure.__cause__ = error
                failures.append(failure)
                current_checkpoint = current_checkpoint.mark_failed(
                    change.source_id, failure.category.value
                )

        final_manifest = SourceManifest(
            project_id=report.project_id,
            entries=tuple(sorted(manifest_entries, key=lambda item: item.source_id)),
        )
        delta = compare_manifests(previous, final_manifest)
        resumed_ids = {
            document.source.source_id
            for document in documents
            if checkpoint is not None
            and checkpoint.failure_for(document.source.source_id) is not None
        }
        if resumed_ids:
            delta = SourceDelta(
                project_id=delta.project_id,
                changes=tuple(
                    SourceChange(
                        SourceChangeKind.RESUMED,
                        change.source_id,
                        change.before,
                        change.after,
                        "checkpoint",
                    )
                    if change.source_id in resumed_ids
                    else change
                    for change in delta.changes
                ),
            )
        return SyncResult(
            manifest=final_manifest,
            delta=delta,
            documents=tuple(documents),
            failures=tuple(failures),
            checkpoint=current_checkpoint,
            skipped_source_ids=tuple(sorted(skipped)),
        )

    def _source_profile(self, source: SourceRecord) -> tuple[str, frozenset[str]]:
        if self.profile_set is None:
            return self.profile_version, frozenset()
        by_id = {item.profile.profile_id: item for item in self.profile_set.profiles}
        selected = by_id.get(source.profile_id)
        if selected is None:
            raise self._profile_failure(
                source,
                stage="profile_selection",
                message="source profile is not present in the active profile set",
            )
        lineage: set[str] = set()
        pending = [source.profile_id]
        while pending:
            profile_id = pending.pop()
            if profile_id in lineage:
                continue
            item = by_id.get(profile_id)
            if item is None:
                raise self._profile_failure(
                    source,
                    stage="profile_selection",
                    message="source profile inheritance is incomplete",
                )
            lineage.add(profile_id)
            pending.extend(item.profile.extends)
        adapter_owner = self.profile_set.adapter_owners.get(source.ingestion_adapter)
        if adapter_owner not in lineage:
            raise self._profile_failure(
                source,
                stage="profile_selection",
                message="source adapter is not declared by the active profile lineage",
            )
        return selected.profile.version, frozenset(lineage)

    def _validate_profile_document(
        self,
        document: NormalizedDocument,
        profile_lineage: frozenset[str],
    ) -> None:
        if self.profile_set is None:
            return
        source = document.source
        for record in document.records:
            owner = self.profile_set.record_type_owners.get(record.record_type)
            if owner not in profile_lineage:
                raise self._profile_failure(
                    source,
                    stage="profile_validation",
                    message="adapter emitted a record type outside the source profile lineage",
                )
            if record.processing.profile_id != source.profile_id:
                raise self._profile_failure(
                    source,
                    stage="profile_validation",
                    message="adapter output does not preserve the selected source profile",
                )

    @staticmethod
    def _profile_failure(
        source: SourceRecord,
        *,
        stage: str,
        message: str,
    ) -> IngestionFailure:
        return IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage=stage,
            category=ErrorCategory.PROFILE_INCOMPATIBLE,
            message=message,
            recovery_action=(
                "load a compatible registered profile and adapter before synchronizing"
            ),
        )

    @staticmethod
    def _recover_moved_ids(
        sources: tuple[SourceRecord, ...], previous: SourceManifest
    ) -> tuple[SourceRecord, ...]:
        current = SourceManifest.from_records(previous.project_id, sources)
        delta = compare_manifests(previous, current)
        replacements: dict[str, str] = {}
        for change in delta.of_kind(SourceChangeKind.MOVED):
            if (
                change.matched_by == "unique_content_sha256"
                and change.after is not None
                and change.after.source_id != change.source_id
            ):
                replacements[change.after.source_id] = change.source_id
        if not replacements:
            return sources
        recovered: list[SourceRecord] = []
        for source in sources:
            replacement = replacements.get(source.source_id)
            if replacement is None:
                recovered.append(source)
                continue
            values = source.to_json_dict()
            values["source_id"] = replacement
            locator = dict(source.locator)
            locator["discovered_source_id"] = source.source_id
            locator["identity_recovered_by"] = "unique_content_sha256"
            values["locator"] = locator
            recovered.append(SourceRecord.model_validate(values))
        return tuple(recovered)


def synchronize_sources(
    report: DiscoveryReport,
    *,
    project_root: Path,
    previous_manifest: SourceManifest | None = None,
    checkpoint: SyncCheckpoint | None = None,
    index_writer: IndexWriter | None = None,
    profile_set: ProfileSet | None = None,
    optional_adapters: tuple[OptionalSourceAdapter, ...] = (),
    force: bool = False,
) -> SyncResult:
    return IngestionSynchronizer(
        project_root=project_root,
        index_writer=index_writer,
        profile_set=profile_set,
        optional_adapters=optional_adapters,
    ).synchronize(
        report,
        previous_manifest=previous_manifest,
        checkpoint=checkpoint,
        force=force,
    )
