"""Rollback-safe orchestration for exact-index and provider generations."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol

from sys4ai_memory.contracts import API_VERSION, SCHEMA_VERSION, RebuildReceipt
from sys4ai_memory.contracts.models import RebuildSourceRevision, RelationRecord
from sys4ai_memory.exact_index import ExactIndex, IndexGeneration
from sys4ai_memory.ingestion import (
    IngestionSynchronizer,
    NormalizedDocument,
    SourceChangeKind,
    SourceManifest,
    compare_manifests,
)
from sys4ai_memory.providers import (
    ExportRequest,
    MemoryProvider,
    PolicyEnvelope,
    ProviderContext,
    ProviderExportFormat,
    RememberRequest,
)
from sys4ai_memory.security.isolation import ProjectBoundary
from sys4ai_memory.sources import DiscoveryReport, RegistryBundle, SourceDiscovery
from sys4ai_memory.util import (
    atomic_write_bytes,
    canonical_json_bytes,
    sha256_bytes,
    sha256_file,
    stable_id,
    utc_now,
)

from .models import (
    AuthorizedRebuildImpact,
    DriftItem,
    DriftKind,
    DriftReport,
    GenerationFingerprints,
    RebuildCheckpoint,
    RebuildExecutionReceipt,
    RebuildImpact,
    RebuildMode,
    RebuildModel,
    RebuildOutcome,
    RebuildPreview,
    RebuildProgress,
    RebuildStage,
    SourceDeltaSummary,
    SourceRevision,
)


class RebuildError(RuntimeError):
    """A generation could not be planned or built safely."""


class RebuildAuthorizationError(RebuildError):
    """The execution decision does not match the current preview."""


class RebuildConflictError(RebuildError):
    """A candidate generation path already exists or current inputs changed."""


class _CancellationRequested(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ProviderStage:
    """An isolated, initialized provider generation with bounded write decisions."""

    provider: MemoryProvider
    context: ProviderContext
    remember_authorization: PolicyEnvelope
    export_authorization: PolicyEnvelope
    isolated_generation: bool = True


class ProviderStageFactory(Protocol):
    async def __call__(self, generation_root: Path, generation_id: str) -> ProviderStage: ...


ProgressCallback = Callable[[RebuildProgress], None]
CancelCheck = Callable[[RebuildStage], bool]
FaultHook = Callable[[RebuildStage], None]


def _source_revision(source: object) -> SourceRevision:
    from sys4ai_memory.contracts import SourceRecord

    if not isinstance(source, SourceRecord) or source.content_sha256 is None:
        raise RebuildError("rebuild sources require validated content hashes")
    revision = (
        source.git_commit
        or source.git_blob_sha
        or source.working_tree_state
        or source.content_sha256
    )
    return SourceRevision(
        source_id=source.source_id,
        path=source.path_or_uri,
        revision=revision,
        content_sha256=source.content_sha256,
    )


def _manifest_payload(manifest: SourceManifest) -> dict[str, object]:
    return manifest.to_json_dict()


def _delta_summary(changes: Iterable[object]) -> SourceDeltaSummary:
    counts = {kind: 0 for kind in SourceChangeKind}
    for change in changes:
        kind = getattr(change, "change", None)
        if isinstance(kind, SourceChangeKind):
            counts[kind] += 1
    return SourceDeltaSummary(**{kind.value: counts[kind] for kind in SourceChangeKind})


def _registry_payload(bundle: RegistryBundle) -> dict[str, object]:
    sources = [
        {
            "source_id": item.source_id,
            "project_id": item.project_id,
            "path_or_uri": item.path_or_uri,
            "path_pattern": item.path_pattern,
            "source_kind": item.source_kind,
            "format": item.format,
            "canonicality": item.canonicality,
            "content_role": item.content_role,
            "authority_tier": item.authority_tier.value,
            "trust_class": item.trust_class.value,
            "sensitivity": item.sensitivity.value,
            "namespace": item.namespace,
            "profile_id": item.profile_id,
            "ingestion_adapter": item.ingestion_adapter,
            "chunking_profile": item.chunking_profile,
            "schema_ref": item.schema_ref,
            "refresh_mode": item.refresh_mode,
            "retention_policy": item.retention_policy,
            "owner": item.owner,
            "write_policy": item.write_policy,
            "include_flag": item.include_flag,
            "notes": item.notes,
            "one_time": item.one_time,
            "generated_from": item.generated_from,
        }
        for item in sorted(bundle.sources, key=lambda value: value.source_id)
    ]
    profiles = [
        {
            "profile_id": item.profile_id,
            "profile_version": item.profile_version,
            "schema_ref": item.schema_ref,
            "config_ref": item.config_ref,
            "migration_ref": item.migration_ref,
            "implementation_status": item.implementation_status,
        }
        for item in sorted(bundle.profiles, key=lambda value: value.profile_id)
    ]
    relations = [
        {
            "relation_id": item.relation_id,
            "relation_name": item.relation_name,
            "relation_version": item.relation_version,
            "schema_ref": item.schema_ref,
            "implementation_status": item.implementation_status,
        }
        for item in sorted(bundle.relations, key=lambda value: value.relation_id)
    ]
    return {"sources": sources, "profiles": profiles, "relations": relations}


class GenerationRebuilder:
    """Build a complete candidate in derived storage and activate one pointer last."""

    def __init__(
        self,
        *,
        boundary: ProjectBoundary,
        registry: RegistryBundle,
        derived_root: str,
        profile_versions: Mapping[str, str],
        profile_registry_sha256: str,
        schema_paths: tuple[str, ...],
        configuration_sha256: str,
        adapter_versions: Mapping[str, str],
        provider_name: str,
        provider_version: str,
        model_identifiers: tuple[str, ...],
        provider_factory: ProviderStageFactory,
        relations: tuple[RelationRecord, ...] = (),
        external_documents: tuple[NormalizedDocument, ...] = (),
        external_manifest: SourceManifest | None = None,
    ) -> None:
        self.boundary = boundary
        self.registry = registry
        self.derived_relative = self._validate_derived_relative(derived_root)
        self.derived_root = boundary.resolve_path(self.derived_relative, must_exist=False)
        self.profile_versions = dict(profile_versions)
        self.profile_registry_sha256 = profile_registry_sha256
        self.schema_paths = schema_paths
        self.configuration_sha256 = configuration_sha256
        self.adapter_versions = dict(adapter_versions)
        self.provider_name = provider_name
        self.provider_version = provider_version
        self.model_identifiers = tuple(model_identifiers)
        self.provider_factory = provider_factory
        self.relations = relations
        self.external_documents = external_documents
        self.external_manifest = external_manifest
        self._validate_inputs()

    @staticmethod
    def _validate_derived_relative(value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("derived root must be a normalized project-relative path")
        if path.parts[:2] != (".sys4ai", "memory"):
            raise ValueError("rebuild output must remain below .sys4ai/memory")
        return path.as_posix()

    def _validate_inputs(self) -> None:
        if not self.profile_versions or not self.adapter_versions:
            raise ValueError("rebuild requires profile and adapter versions")
        hashes = (
            self.profile_registry_sha256,
            self.configuration_sha256,
        )
        if any(
            len(value) != 64 or any(char not in "0123456789abcdef" for char in value)
            for value in hashes
        ):
            raise ValueError("rebuild fingerprints must be lowercase SHA-256")
        if any(
            item.source.project_id != self.boundary.project_id for item in self.external_documents
        ):
            raise ValueError("external documents must match the rebuild project")
        if any(item.project_id != self.boundary.project_id for item in self.relations):
            raise ValueError("relations must match the rebuild project")
        if self.external_documents and self.external_manifest is None:
            raise ValueError("external documents require their validated external manifest")
        if self.external_manifest is not None:
            if self.external_manifest.project_id != self.boundary.project_id:
                raise ValueError("external manifest must match the rebuild project")
            expected = SourceManifest.from_records(
                self.boundary.project_id,
                tuple(item.source for item in self.external_documents),
            )
            if expected.entries != self.external_manifest.entries:
                raise ValueError("external documents do not match their manifest")

    def _fingerprints(self, *, deterministic: bool) -> GenerationFingerprints:
        schema_entries: list[dict[str, str]] = []
        for relative in sorted(self.schema_paths):
            path = self.boundary.resolve_path(relative)
            if path.is_symlink() or not path.is_file():
                raise RebuildError(f"schema is not a regular project file: {relative}")
            schema_entries.append({"path": relative, "sha256": sha256_file(path)})
        return GenerationFingerprints(
            source_registry_sha256=sha256_bytes(
                canonical_json_bytes(_registry_payload(self.registry))
            ),
            profile_registry_sha256=self.profile_registry_sha256,
            external_manifest_sha256=(
                sha256_bytes(canonical_json_bytes(self.external_manifest.to_json_dict()))
                if self.external_manifest is not None
                else None
            ),
            schema_set_sha256=sha256_bytes(canonical_json_bytes(schema_entries)),
            configuration_sha256=self.configuration_sha256,
            adapter_versions=dict(sorted(self.adapter_versions.items())),
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            model_identifiers=tuple(sorted(self.model_identifiers)),
            deterministic=deterministic,
        )

    def _discover(self) -> DiscoveryReport:
        return SourceDiscovery(
            project_root=self.boundary.root,
            project_id=self.boundary.project_id,
            entries=self.registry.sources,
        ).discover()

    def _read_active_pointer(self) -> dict[str, object] | None:
        path = self.derived_root / "active-generation.json"
        if not path.exists():
            return None
        if path.is_symlink() or not path.is_file():
            raise RebuildError("active generation pointer is not a regular file")
        import json

        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RebuildError("active generation pointer is invalid") from error
        if not isinstance(value, dict):
            raise RebuildError("active generation pointer must be an object")
        if (
            value.get("project_id") != self.boundary.project_id
            or value.get("dataset_id") != self.boundary.dataset_id
        ):
            raise RebuildError("active generation pointer crosses the project boundary")
        generation_id = value.get("generation_id")
        if (
            not isinstance(generation_id, str)
            or re.fullmatch(r"gen_[A-Za-z0-9_.:@-]+", generation_id) is None
        ):
            raise RebuildError("active generation pointer has an invalid generation ID")
        manifest_sha256 = value.get("manifest_sha256")
        if (
            not isinstance(manifest_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is None
        ):
            raise RebuildError("active generation pointer has an invalid manifest hash")
        return value

    def _active_manifest(self, pointer: dict[str, object] | None) -> SourceManifest | None:
        if pointer is None:
            return None
        generation_id = str(pointer["generation_id"])
        path = self.derived_root / "generations" / generation_id / "generation-manifest.json"
        if path.is_symlink() or not path.is_file():
            raise RebuildError("active generation manifest is unavailable")
        import json

        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RebuildError("active generation manifest is invalid") from error
        if not isinstance(value, dict) or not isinstance(value.get("source_manifest"), dict):
            raise RebuildError("active generation manifest omits source metadata")
        return SourceManifest.from_json_dict(value["source_manifest"])

    def _plan(
        self,
        *,
        operation_id: str,
        mode: RebuildMode,
        deterministic: bool,
    ) -> tuple[RebuildPreview, DiscoveryReport, SourceManifest | None]:
        if not operation_id.strip():
            raise ValueError("operation_id must not be blank")
        report = self._discover()
        all_sources = [*report.records, *(item.source for item in self.external_documents)]
        source_ids = [item.source_id for item in all_sources]
        if len(source_ids) != len(set(source_ids)):
            raise RebuildError("discovered and external source IDs overlap")
        current_manifest = SourceManifest.from_records(self.boundary.project_id, tuple(all_sources))
        pointer = self._read_active_pointer()
        previous = self._active_manifest(pointer)
        baseline = previous or SourceManifest(self.boundary.project_id, ())
        delta = compare_manifests(baseline, current_manifest)
        fingerprints = self._fingerprints(deterministic=deterministic)
        manifest_sha256 = sha256_bytes(canonical_json_bytes(_manifest_payload(current_manifest)))
        fingerprint_sha256 = sha256_bytes(
            canonical_json_bytes(fingerprints.model_dump(mode="json"))
        )
        generation_identity = stable_id(
            "memory-generation",
            self.boundary.project_id,
            self.boundary.dataset_id,
            operation_id,
            mode.value,
            manifest_sha256,
            fingerprint_sha256,
        ).replace("-", "")
        generation_id = f"gen_{generation_identity}"
        paths = (
            f"{self.derived_relative}/generations/{generation_id}",
            f"{self.derived_relative}/active-generation.json",
        )
        impact = RebuildImpact(
            project_id=self.boundary.project_id,
            dataset_id=self.boundary.dataset_id,
            mode=mode,
            planned_generation_id=generation_id,
            previous_generation_id=(str(pointer["generation_id"]) if pointer else None),
            source_revisions=tuple(
                sorted(
                    (_source_revision(source) for source in all_sources),
                    key=lambda item: item.source_id,
                )
            ),
            delta=_delta_summary(delta.changes),
            generated_paths=paths,
        )
        digest_payload = {
            "operation_id": operation_id,
            "fingerprints": fingerprints.model_dump(mode="json"),
            "impact": impact.model_dump(mode="json"),
            "source_manifest_sha256": manifest_sha256,
        }
        preview = RebuildPreview(
            operation_id=operation_id,
            generated_at=utc_now(),
            fingerprints=fingerprints,
            impact=impact,
            source_manifest_sha256=manifest_sha256,
            impact_digest=sha256_bytes(canonical_json_bytes(digest_payload)),
        )
        return preview, report, previous

    def preview(
        self,
        *,
        operation_id: str,
        mode: RebuildMode,
        deterministic: bool = True,
    ) -> RebuildPreview:
        """Inspect all rebuild inputs without creating provider or filesystem state."""

        preview, _, _ = self._plan(
            operation_id=operation_id,
            mode=mode,
            deterministic=deterministic,
        )
        return preview

    def _require_authorization(
        self, preview: RebuildPreview, authorization: AuthorizedRebuildImpact
    ) -> None:
        decision = authorization.decision
        if authorization.impact_digest != preview.impact_digest:
            raise RebuildAuthorizationError("rebuild authorization does not match preview")
        if (
            decision.project_id != self.boundary.project_id
            or decision.dataset_id != self.boundary.dataset_id
        ):
            raise RebuildAuthorizationError("rebuild authorization crosses project scope")

    def _safe_create_stage(self, generation_id: str) -> Path:
        for path in (self.derived_root, self.derived_root / "staging"):
            if path.exists() and (path.is_symlink() or not path.is_dir()):
                raise RebuildError("derived rebuild path is not a regular directory")
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
        stage = self.derived_root / "staging" / generation_id
        final = self.derived_root / "generations" / generation_id
        if stage.exists() or final.exists():
            raise RebuildConflictError("candidate generation path already exists")
        stage.mkdir(mode=0o700)
        return stage

    @staticmethod
    def _write_model(path: Path, model: object) -> None:
        if not isinstance(model, RebuildModel):
            raise TypeError("rebuild metadata must use a rebuild model")
        atomic_write_bytes(path, canonical_json_bytes(model.model_dump(mode="json")))

    @staticmethod
    def _write_checkpoint(path: Path, checkpoint: RebuildCheckpoint) -> None:
        atomic_write_bytes(path, canonical_json_bytes(checkpoint.model_dump(mode="json")))

    async def execute(
        self,
        preview: RebuildPreview,
        *,
        authorization: AuthorizedRebuildImpact,
        progress_callback: ProgressCallback | None = None,
        cancel_requested: CancelCheck | None = None,
        fault_hook: FaultHook | None = None,
    ) -> RebuildExecutionReceipt:
        """Build and validate an isolated generation, then atomically activate it."""

        current, report, previous_manifest = self._plan(
            operation_id=preview.operation_id,
            mode=preview.impact.mode,
            deterministic=preview.fingerprints.deterministic,
        )
        if current.impact_digest != preview.impact_digest:
            raise RebuildConflictError("rebuild inputs changed after preview")
        self._require_authorization(current, authorization)
        started_at = utc_now()
        stage_root = self._safe_create_stage(preview.impact.planned_generation_id)
        checkpoint = RebuildCheckpoint(
            generation_id=preview.impact.planned_generation_id,
            stage=RebuildStage.PREVIEW,
            completed_source_ids=(),
            failed_source_ids=(),
            sequence=0,
            cancel_requested=False,
            updated_at=started_at,
        )
        progress: list[RebuildProgress] = []
        source_count = 0
        record_count = 0
        relation_count = 0
        snapshot_sha256: str | None = None
        manifest_sha256: str | None = None
        validation_checks: list[str] = []

        def update(
            stage: RebuildStage,
            detail: str,
            completed: int,
            total: int,
            *,
            completed_ids: tuple[str, ...] | None = None,
            failed_ids: tuple[str, ...] = (),
        ) -> None:
            nonlocal checkpoint
            event = RebuildProgress(
                sequence=len(progress) + 1,
                stage=stage,
                detail_code=detail,
                completed_items=completed,
                total_items=total,
                observed_at=utc_now(),
            )
            progress.append(event)
            checkpoint = RebuildCheckpoint(
                generation_id=preview.impact.planned_generation_id,
                stage=stage,
                completed_source_ids=completed_ids or checkpoint.completed_source_ids,
                failed_source_ids=failed_ids,
                sequence=event.sequence,
                cancel_requested=False,
                updated_at=event.observed_at,
            )
            self._write_checkpoint(stage_root / "checkpoint.json", checkpoint)
            if progress_callback is not None:
                progress_callback(event)
            if fault_hook is not None:
                fault_hook(stage)
            if cancel_requested is not None and cancel_requested(stage):
                checkpoint = checkpoint.model_copy(
                    update={"cancel_requested": True, "updated_at": utc_now()}
                )
                self._write_checkpoint(stage_root / "checkpoint.json", checkpoint)
                raise _CancellationRequested

        outcome = RebuildOutcome.FAILED
        failure_code: str | None = None
        activated = False
        try:
            update(RebuildStage.DISCOVERY, "sources_discovered", 0, len(report.records))
            synchronizer = IngestionSynchronizer(project_root=self.boundary.root)
            sync = synchronizer.synchronize(
                report,
                previous_manifest=(
                    previous_manifest
                    if preview.impact.mode is RebuildMode.INCREMENTAL
                    else SourceManifest(self.boundary.project_id, ())
                ),
                force=True,
            )
            if sync.failures:
                failed = tuple(sorted(item.source_id for item in sync.failures))
                update(
                    RebuildStage.NORMALIZATION,
                    "source_normalization_failed",
                    len(sync.documents),
                    len(report.records),
                    completed_ids=tuple(sorted(item.source.source_id for item in sync.documents)),
                    failed_ids=failed,
                )
                raise RebuildError("one or more sources failed deterministic normalization")
            documents = (*sync.documents, *self.external_documents)
            source_count = len(documents)
            record_count = sum(len(item.records) for item in documents)
            relation_count = len(self.relations)
            completed_ids = tuple(sorted(item.source.source_id for item in documents))
            update(
                RebuildStage.NORMALIZATION,
                "sources_normalized",
                source_count,
                source_count,
                completed_ids=completed_ids,
            )

            exact_path = stage_root / "exact-index.sqlite3"
            generation = IndexGeneration(
                generation_id=preview.impact.planned_generation_id,
                project_id=self.boundary.project_id,
                configuration_fingerprint=self.configuration_sha256,
                profile_versions=tuple(sorted(self.profile_versions.items())),
                adapter_versions=tuple(sorted(self.adapter_versions.items())),
                created_at=started_at,
            )
            with ExactIndex(exact_path) as index:
                result = index.rebuild(generation, documents)
                health = index.health(self.boundary.project_id)
                if (
                    result.sources_written != source_count
                    or result.records_written != record_count
                    or health.active_generation_id != generation.generation_id
                    or health.current_source_count != source_count
                    or health.current_record_count != record_count
                ):
                    raise RebuildError("exact generation reconciliation failed")
            validation_checks.append("exact_index_counts_and_generation_match")
            update(RebuildStage.EXACT_INDEX, "exact_generation_built", source_count, source_count)

            provider_stage = await self.provider_factory(
                stage_root / "provider", preview.impact.planned_generation_id
            )
            if (
                provider_stage.context.project_id != self.boundary.project_id
                or provider_stage.context.dataset_id != self.boundary.dataset_id
                or provider_stage.provider.provider_name.value != self.provider_name
                or provider_stage.provider.provider_version != self.provider_version
                or not provider_stage.isolated_generation
            ):
                raise RebuildError("provider stage identity does not match rebuild inputs")
            records = tuple(record for document in documents for record in document.records)
            sources = tuple(document.source for document in documents)
            request_suffix = stable_id(
                "rebuild-provider-request", preview.impact.planned_generation_id
            )
            if records:
                await provider_stage.provider.remember(
                    RememberRequest(
                        context=provider_stage.context,
                        request_id=f"mrq_rebuild_{request_suffix}",
                        idempotency_key=f"rebuild:{preview.impact.planned_generation_id}",
                        records=records,
                        relations=self.relations,
                        sources=sources,
                        authorization=provider_stage.remember_authorization,
                    )
                )
            exported = await provider_stage.provider.export(
                ExportRequest(
                    context=provider_stage.context,
                    request_id=f"mrq_rebuild_export_{request_suffix}",
                    idempotency_key=f"rebuild-export:{preview.impact.planned_generation_id}",
                    format=ProviderExportFormat.SYS4AI,
                    profile_versions=self.profile_versions,
                    authorization=provider_stage.export_authorization,
                )
            )
            snapshot = exported.snapshot
            if snapshot is None:
                raise RebuildError("provider did not return a neutral validation snapshot")
            if (
                snapshot.project_id != self.boundary.project_id
                or snapshot.dataset_id != self.boundary.dataset_id
                or len(snapshot.records) != record_count
                or len(snapshot.relations) != relation_count
                or len(snapshot.sources) != source_count
            ):
                raise RebuildError("provider generation reconciliation failed")
            snapshot_bytes = canonical_json_bytes(snapshot.model_dump(mode="json"))
            atomic_write_bytes(stage_root / "provider-snapshot.json", snapshot_bytes)
            snapshot_sha256 = sha256_bytes(snapshot_bytes)
            validation_checks.append("provider_snapshot_counts_scope_and_checksums_match")
            update(RebuildStage.PROVIDER, "provider_generation_built", record_count, record_count)

            source_manifest = SourceManifest.from_records(
                self.boundary.project_id, tuple(document.source for document in documents)
            )
            index_sha256 = sha256_file(exact_path)
            generation_manifest = {
                "schema_version": "1.0",
                "project_id": self.boundary.project_id,
                "dataset_id": self.boundary.dataset_id,
                "generation_id": preview.impact.planned_generation_id,
                "previous_generation_id": preview.impact.previous_generation_id,
                "mode": preview.impact.mode.value,
                "fingerprints": preview.fingerprints.model_dump(mode="json"),
                "source_manifest": source_manifest.to_json_dict(),
                "source_manifest_sha256": sha256_bytes(
                    canonical_json_bytes(source_manifest.to_json_dict())
                ),
                "exact_index_sha256": index_sha256,
                "provider_snapshot_sha256": snapshot_sha256,
                "counts": {
                    "sources": source_count,
                    "records": record_count,
                    "relations": relation_count,
                },
            }
            manifest_bytes = canonical_json_bytes(generation_manifest)
            atomic_write_bytes(stage_root / "generation-manifest.json", manifest_bytes)
            manifest_sha256 = sha256_bytes(manifest_bytes)
            if sha256_file(stage_root / "generation-manifest.json") != manifest_sha256:
                raise RebuildError("generation manifest write verification failed")
            validation_checks.append("generation_manifest_checksum_verified")
            update(RebuildStage.VALIDATION, "candidate_validated", 3, 3)
            update(RebuildStage.ACTIVATION, "candidate_ready_for_activation", 1, 1)

            completed_at = utc_now()
            success_checkpoint = checkpoint.model_copy(
                update={"stage": RebuildStage.COMPLETE, "updated_at": completed_at}
            )
            receipt = self._receipt(
                preview=preview,
                started_at=started_at,
                completed_at=completed_at,
                outcome=RebuildOutcome.SUCCEEDED,
                activated=True,
                source_count=source_count,
                record_count=record_count,
                relation_count=relation_count,
                snapshot_sha256=snapshot_sha256,
                manifest_sha256=manifest_sha256,
                validation_checks=tuple(validation_checks),
                checkpoint=success_checkpoint,
                progress=tuple(progress),
                failure_code=None,
            )
            self._write_checkpoint(stage_root / "checkpoint.json", success_checkpoint)
            self._write_model(stage_root / "rebuild-receipt.json", receipt)
            generations_root = self.derived_root / "generations"
            generations_root.mkdir(parents=True, exist_ok=True, mode=0o700)
            final_root = generations_root / preview.impact.planned_generation_id
            if final_root.exists():
                raise RebuildConflictError("generation appeared during candidate build")
            os.replace(stage_root, final_root)
            pointer = {
                "schema_version": "1.0",
                "project_id": self.boundary.project_id,
                "dataset_id": self.boundary.dataset_id,
                "generation_id": preview.impact.planned_generation_id,
                "previous_generation_id": preview.impact.previous_generation_id,
                "manifest_sha256": manifest_sha256,
                "activated_at": completed_at.isoformat().replace("+00:00", "Z"),
            }
            atomic_write_bytes(
                self.derived_root / "active-generation.json", canonical_json_bytes(pointer)
            )
            activated = True
            outcome = RebuildOutcome.SUCCEEDED
            return receipt
        except _CancellationRequested:
            outcome = RebuildOutcome.CANCELLED
            failure_code = "cancellation_requested"
        except Exception as error:
            outcome = RebuildOutcome.FAILED
            failure_code = type(error).__name__

        completed_at = utc_now()
        checkpoint = checkpoint.model_copy(
            update={
                "stage": checkpoint.stage,
                "cancel_requested": outcome is RebuildOutcome.CANCELLED,
                "updated_at": completed_at,
            }
        )
        receipt = self._receipt(
            preview=preview,
            started_at=started_at,
            completed_at=completed_at,
            outcome=outcome,
            activated=activated,
            source_count=source_count,
            record_count=record_count,
            relation_count=relation_count,
            snapshot_sha256=snapshot_sha256,
            manifest_sha256=None,
            validation_checks=tuple(validation_checks),
            checkpoint=checkpoint,
            progress=tuple(progress),
            failure_code=failure_code,
        )
        candidate_root = (
            self.derived_root / "generations" / preview.impact.planned_generation_id
            if not stage_root.exists()
            else stage_root
        )
        candidate_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._write_model(candidate_root / "rebuild-receipt.json", receipt)
        return receipt

    def _receipt(
        self,
        *,
        preview: RebuildPreview,
        started_at: object,
        completed_at: object,
        outcome: RebuildOutcome,
        activated: bool,
        source_count: int,
        record_count: int,
        relation_count: int,
        snapshot_sha256: str | None,
        manifest_sha256: str | None,
        validation_checks: tuple[str, ...],
        checkpoint: RebuildCheckpoint,
        progress: tuple[RebuildProgress, ...],
        failure_code: str | None,
    ) -> RebuildExecutionReceipt:
        from datetime import datetime

        if not isinstance(started_at, datetime) or not isinstance(completed_at, datetime):
            raise TypeError("receipt timestamps must be datetimes")
        receipt_identifier = stable_id(
            "rebuild-receipt",
            self.boundary.project_id,
            preview.impact.planned_generation_id,
            outcome.value,
        ).replace("-", "")
        trace_identifier = stable_id(
            "rebuild-trace", self.boundary.project_id, preview.operation_id
        ).replace("-", "")
        public = RebuildReceipt(
            schema_version=SCHEMA_VERSION,
            api_version=API_VERSION,
            receipt_id=f"rbr_{receipt_identifier}",
            project_id=self.boundary.project_id,
            source_revisions=tuple(
                RebuildSourceRevision(
                    source_id=item.source_id,
                    revision=item.revision,
                    content_sha256=item.content_sha256,
                )
                for item in preview.impact.source_revisions
            ),
            configuration_fingerprint=self.configuration_sha256,
            profile_versions=self.profile_versions,
            adapter_versions=self.adapter_versions,
            provider_version=self.provider_version,
            model_identifiers=self.model_identifiers,
            started_at=started_at,
            completed_at=completed_at,
            warnings=(
                ("deterministic_mode_disabled",) if not preview.fingerprints.deterministic else ()
            ),
            outcome=outcome.value,
            trace_id=f"trace_rebuild_{trace_identifier}",
        )
        current_pointer = self._read_active_pointer()
        current_id = str(current_pointer["generation_id"]) if current_pointer else None
        prior_preserved = activated or current_id == preview.impact.previous_generation_id
        return RebuildExecutionReceipt(
            receipt=public,
            dataset_id=self.boundary.dataset_id,
            generation_id=preview.impact.planned_generation_id,
            previous_generation_id=preview.impact.previous_generation_id,
            mode=preview.impact.mode,
            outcome=outcome,
            activated=activated,
            prior_generation_preserved=prior_preserved,
            impact_digest=preview.impact_digest,
            generation_manifest_sha256=manifest_sha256,
            source_count=source_count,
            record_count=record_count,
            relation_count=relation_count,
            provider_snapshot_sha256=snapshot_sha256,
            delta=preview.impact.delta,
            validation_checks=validation_checks,
            checkpoint=checkpoint,
            progress=progress,
            failure_code=failure_code,
        )

    def drift(self, *, deterministic: bool = True) -> DriftReport:
        """Compare current canonical inputs with the active generation without mutation."""

        checked_at = utc_now()
        pointer = self._read_active_pointer()
        if pointer is None:
            item = DriftItem(
                kind=DriftKind.GENERATION,
                identity="active_generation",
                expected="present",
                observed=None,
            )
            return DriftReport(
                project_id=self.boundary.project_id,
                dataset_id=self.boundary.dataset_id,
                active_generation_id=None,
                checked_at=checked_at,
                drifted=True,
                items=(item,),
            )
        generation_id = str(pointer["generation_id"])
        generation_path = self.derived_root / "generations" / generation_id
        manifest_path = generation_path / "generation-manifest.json"
        items: list[DriftItem] = []
        expected_manifest_hash = pointer.get("manifest_sha256")
        if not manifest_path.is_file() or manifest_path.is_symlink():
            items.append(
                DriftItem(
                    kind=DriftKind.GENERATION,
                    identity=generation_id,
                    expected=str(expected_manifest_hash),
                    observed=None,
                )
            )
            return DriftReport(
                project_id=self.boundary.project_id,
                dataset_id=self.boundary.dataset_id,
                active_generation_id=generation_id,
                checked_at=checked_at,
                drifted=True,
                items=tuple(items),
            )
        observed_manifest_hash = sha256_file(manifest_path)
        if observed_manifest_hash != expected_manifest_hash:
            items.append(
                DriftItem(
                    kind=DriftKind.GENERATION,
                    identity=f"{generation_id}/manifest",
                    expected=str(expected_manifest_hash),
                    observed=observed_manifest_hash,
                )
            )
        import json

        value = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise RebuildError("active generation manifest must be an object")
        for identity, filename, checksum_field in (
            ("exact_index", "exact-index.sqlite3", "exact_index_sha256"),
            ("provider_snapshot", "provider-snapshot.json", "provider_snapshot_sha256"),
        ):
            expected = value.get(checksum_field)
            if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
                items.append(
                    DriftItem(
                        kind=DriftKind.GENERATION,
                        identity=f"{generation_id}/{identity}",
                        expected="valid_manifest_sha256",
                        observed=None,
                    )
                )
                continue
            artifact_path = generation_path / filename
            observed = (
                sha256_file(artifact_path)
                if artifact_path.is_file() and not artifact_path.is_symlink()
                else None
            )
            if observed != expected:
                items.append(
                    DriftItem(
                        kind=DriftKind.GENERATION,
                        identity=f"{generation_id}/{identity}",
                        expected=expected,
                        observed=observed,
                    )
                )
        stored_manifest_value = value.get("source_manifest")
        stored_fingerprints_value = value.get("fingerprints")
        if not isinstance(stored_manifest_value, dict) or not isinstance(
            stored_fingerprints_value, dict
        ):
            raise RebuildError("active generation manifest is incomplete")
        stored_manifest = SourceManifest.from_json_dict(stored_manifest_value)
        current_report = self._discover()
        current_sources = (
            *current_report.records,
            *(item.source for item in self.external_documents),
        )
        current_manifest = SourceManifest.from_records(self.boundary.project_id, current_sources)
        for change in compare_manifests(stored_manifest, current_manifest).changes:
            if change.change is SourceChangeKind.UNCHANGED:
                continue
            items.append(
                DriftItem(
                    kind=DriftKind.SOURCE,
                    identity=change.source_id,
                    expected=(change.before.content_sha256 if change.before else None),
                    observed=(change.after.content_sha256 if change.after else None),
                )
            )
        current_fingerprints = self._fingerprints(deterministic=deterministic)
        stored_fingerprints = GenerationFingerprints.model_validate(stored_fingerprints_value)
        comparisons = (
            (
                DriftKind.SOURCE,
                "external_manifest",
                stored_fingerprints.external_manifest_sha256,
                current_fingerprints.external_manifest_sha256,
            ),
            (
                DriftKind.CONFIGURATION,
                "configuration",
                stored_fingerprints.configuration_sha256,
                current_fingerprints.configuration_sha256,
            ),
            (
                DriftKind.PROFILE,
                "profile_registry",
                stored_fingerprints.profile_registry_sha256,
                current_fingerprints.profile_registry_sha256,
            ),
            (
                DriftKind.SCHEMA,
                "schema_set",
                stored_fingerprints.schema_set_sha256,
                current_fingerprints.schema_set_sha256,
            ),
            (
                DriftKind.ADAPTER,
                "adapter_versions",
                sha256_bytes(canonical_json_bytes(stored_fingerprints.adapter_versions)),
                sha256_bytes(canonical_json_bytes(current_fingerprints.adapter_versions)),
            ),
            (
                DriftKind.PROVIDER,
                "provider",
                (f"{stored_fingerprints.provider_name}@{stored_fingerprints.provider_version}"),
                (f"{current_fingerprints.provider_name}@{current_fingerprints.provider_version}"),
            ),
            (
                DriftKind.MODEL,
                "models",
                "\x1f".join(stored_fingerprints.model_identifiers),
                "\x1f".join(current_fingerprints.model_identifiers),
            ),
        )
        for kind, identity, expected, observed in comparisons:
            if expected != observed:
                items.append(
                    DriftItem(
                        kind=kind,
                        identity=identity,
                        expected=expected,
                        observed=observed,
                    )
                )
        return DriftReport(
            project_id=self.boundary.project_id,
            dataset_id=self.boundary.dataset_id,
            active_generation_id=generation_id,
            checked_at=checked_at,
            drifted=bool(items),
            items=tuple(items),
        )
