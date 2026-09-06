"""Provider-neutral ingestion and synchronization result types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from sys4ai_memory.contracts import ErrorCategory, MemoryRecord, SourceRecord
from sys4ai_memory.util.time import utc_now


class IngestionFailure(Exception):
    """Safe, structured ingestion failure that never retains source content."""

    def __init__(
        self,
        *,
        source_id: str,
        adapter: str,
        stage: str,
        category: ErrorCategory,
        message: str,
        recovery_action: str,
    ) -> None:
        super().__init__(message)
        self.source_id = source_id
        self.adapter = adapter
        self.stage = stage
        self.category = category
        self.message = message
        self.recovery_action = recovery_action

    def as_metadata(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "adapter": self.adapter,
            "stage": self.stage,
            "error_category": self.category.value,
            "message": self.message,
            "recovery_action": self.recovery_action,
        }


@dataclass(frozen=True, slots=True)
class NormalizedDocument:
    """One exact source plus the public records deterministically derived from it."""

    source: SourceRecord
    raw_bytes: bytes
    records: tuple[MemoryRecord, ...]
    adapter_id: str
    adapter_version: str
    profile_version: str
    processed_at: datetime

    def __post_init__(self) -> None:
        if not self.records:
            raise ValueError("a normalized document must contain at least one record")
        if self.source.content_sha256 is None:
            raise ValueError("normalized source requires content_sha256")
        record_ids = tuple(record.record_id for record in self.records)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("normalized record IDs must be unique within a source")
        for record in self.records:
            if record.source.source_id != self.source.source_id:
                raise ValueError("normalized record source_id does not match its source")
            if record.source.content_sha256 != self.source.content_sha256:
                raise ValueError("normalized record source hash does not match its source")


@dataclass(frozen=True, slots=True)
class IngestionBatchResult:
    documents: tuple[NormalizedDocument, ...]
    failures: tuple[IngestionFailure, ...]


class SourceChangeKind(StrEnum):
    UNCHANGED = "unchanged"
    ADDED = "added"
    CHANGED = "changed"
    MOVED = "moved"
    DELETED = "deleted"
    FAILED = "failed"
    RESUMED = "resumed"


@dataclass(frozen=True, slots=True)
class SourceManifestEntry:
    source_id: str
    path: str
    content_sha256: str
    revision: str | None = None
    status: str = "active"
    error_category: str | None = None

    @classmethod
    def from_source_record(cls, source: SourceRecord) -> SourceManifestEntry:
        if source.content_sha256 is None:
            raise ValueError("included source is missing content_sha256")
        revision = (
            source.git_commit
            or source.git_blob_sha
            or source.working_tree_state
            or source.content_sha256
        )
        return cls(
            source_id=source.source_id,
            path=source.path_or_uri,
            content_sha256=source.content_sha256,
            revision=revision,
        )


@dataclass(frozen=True, slots=True)
class SourceManifest:
    project_id: str
    entries: tuple[SourceManifestEntry, ...]
    manifest_id: str | None = None
    snapshot_root: str | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        source_ids = tuple(item.source_id for item in self.entries)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("manifest source IDs must be unique")
        paths = tuple(item.path for item in self.entries if item.status != "deleted")
        if len(paths) != len(set(paths)):
            raise ValueError("manifest current paths must be unique")

    @classmethod
    def from_records(
        cls,
        project_id: str,
        records: tuple[SourceRecord, ...],
        *,
        manifest_id: str | None = None,
    ) -> SourceManifest:
        return cls(
            project_id=project_id,
            manifest_id=manifest_id,
            entries=tuple(
                sorted(
                    (SourceManifestEntry.from_source_record(record) for record in records),
                    key=lambda item: item.source_id,
                )
            ),
        )

    @classmethod
    def from_json_dict(cls, value: Mapping[str, Any]) -> SourceManifest:
        raw_sources = value.get("sources")
        if not isinstance(raw_sources, list):
            raise ValueError("manifest sources must be a list")
        entries: list[SourceManifestEntry] = []
        for raw in raw_sources:
            if not isinstance(raw, dict):
                raise ValueError("manifest source must be an object")
            source_id = raw.get("source_id")
            path = raw.get("path")
            digest = raw.get("content_sha256")
            if not isinstance(source_id, str) or not source_id:
                raise ValueError("manifest source requires source_id, path, and content_sha256")
            if not isinstance(path, str) or not path:
                raise ValueError("manifest source requires source_id, path, and content_sha256")
            if not isinstance(digest, str) or not digest:
                raise ValueError("manifest source requires source_id, path, and content_sha256")
            revision = raw.get("revision")
            status = raw.get("status", "active")
            error_category = raw.get("error_category")
            if revision is not None and not isinstance(revision, str):
                raise ValueError("manifest revision must be a string or null")
            if not isinstance(status, str):
                raise ValueError("manifest status must be a string")
            if error_category is not None and not isinstance(error_category, str):
                raise ValueError("manifest error_category must be a string or null")
            entries.append(
                SourceManifestEntry(
                    source_id=source_id,
                    path=path,
                    content_sha256=digest,
                    revision=revision,
                    status=status,
                    error_category=error_category,
                )
            )
        project_id = value.get("project_id")
        if not isinstance(project_id, str) or not project_id:
            raise ValueError("manifest project_id is required")
        manifest_id = value.get("manifest_id")
        snapshot_root = value.get("snapshot_root")
        schema_version = value.get("schema_version", "1.0")
        for label, candidate in (
            ("manifest_id", manifest_id),
            ("snapshot_root", snapshot_root),
        ):
            if candidate is not None and not isinstance(candidate, str):
                raise ValueError(f"manifest {label} must be a string or null")
        if schema_version != "1.0":
            raise ValueError("unsupported manifest schema_version")
        return cls(
            project_id=project_id,
            entries=tuple(entries),
            manifest_id=manifest_id,
            snapshot_root=snapshot_root,
            schema_version=schema_version,
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "project_id": self.project_id,
            "snapshot_root": self.snapshot_root,
            "sources": [
                {
                    "source_id": item.source_id,
                    "path": item.path,
                    "content_sha256": item.content_sha256,
                    "revision": item.revision,
                    "status": item.status,
                    "error_category": item.error_category,
                }
                for item in self.entries
            ],
        }


@dataclass(frozen=True, slots=True)
class SourceChange:
    change: SourceChangeKind
    source_id: str
    before: SourceManifestEntry | None
    after: SourceManifestEntry | None
    matched_by: str


@dataclass(frozen=True, slots=True)
class SourceDelta:
    project_id: str
    changes: tuple[SourceChange, ...]

    def of_kind(self, kind: SourceChangeKind) -> tuple[SourceChange, ...]:
        return tuple(item for item in self.changes if item.change is kind)


@dataclass(frozen=True, slots=True)
class SyncCheckpoint:
    """Immutable checkpoint safe to serialize in a caller-owned location."""

    project_id: str
    completed_revisions: tuple[tuple[str, str], ...] = ()
    failed_sources: tuple[tuple[str, str], ...] = ()
    updated_at: datetime | None = None

    def is_complete(self, source_id: str, content_sha256: str) -> bool:
        return (source_id, content_sha256) in self.completed_revisions

    def failure_for(self, source_id: str) -> str | None:
        return dict(self.failed_sources).get(source_id)

    def mark_complete(self, source_id: str, content_sha256: str) -> SyncCheckpoint:
        completed = dict(self.completed_revisions)
        completed[source_id] = content_sha256
        failed = dict(self.failed_sources)
        failed.pop(source_id, None)
        return replace(
            self,
            completed_revisions=tuple(sorted(completed.items())),
            failed_sources=tuple(sorted(failed.items())),
            updated_at=utc_now(),
        )

    def mark_failed(self, source_id: str, category: str) -> SyncCheckpoint:
        failed = dict(self.failed_sources)
        failed[source_id] = category
        return replace(
            self,
            failed_sources=tuple(sorted(failed.items())),
            updated_at=utc_now(),
        )


@dataclass(frozen=True, slots=True)
class SyncResult:
    manifest: SourceManifest
    delta: SourceDelta
    documents: tuple[NormalizedDocument, ...]
    failures: tuple[IngestionFailure, ...]
    checkpoint: SyncCheckpoint
    skipped_source_ids: tuple[str, ...]


def load_manifest(path: Path) -> SourceManifest:
    """Load a JSON manifest from a caller-selected canonical or fixture path."""

    import json

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid source manifest: {path}") from error
    if not isinstance(value, dict):
        raise ValueError("source manifest root must be an object")
    return SourceManifest.from_json_dict(value)
