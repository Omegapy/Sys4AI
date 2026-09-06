"""Metadata and operation results for the embedded deterministic index."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from sys4ai_memory.util.hashing import sha256_bytes
from sys4ai_memory.util.ids import stable_id
from sys4ai_memory.util.time import ensure_utc, utc_now


@dataclass(frozen=True, slots=True)
class IndexGeneration:
    generation_id: str
    project_id: str
    configuration_fingerprint: str
    profile_versions: tuple[tuple[str, str], ...]
    adapter_versions: tuple[tuple[str, str], ...]
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.generation_id.startswith("gen_"):
            raise ValueError("generation_id must use the gen_ prefix")
        if len(self.configuration_fingerprint) != 64 or any(
            character not in "0123456789abcdef" for character in self.configuration_fingerprint
        ):
            raise ValueError("configuration_fingerprint must be lowercase SHA-256")
        ensure_utc(self.created_at)
        if len(self.profile_versions) != len(dict(self.profile_versions)):
            raise ValueError("profile versions must have unique IDs")
        if len(self.adapter_versions) != len(dict(self.adapter_versions)):
            raise ValueError("adapter versions must have unique IDs")

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        configuration_fingerprint: str,
        profile_versions: Mapping[str, str],
        adapter_versions: Mapping[str, str],
        created_at: datetime | None = None,
        identity: str | None = None,
    ) -> IndexGeneration:
        timestamp = ensure_utc(created_at) if created_at is not None else utc_now()
        identity_value = identity or timestamp.isoformat()
        identifier = stable_id(
            "exact-index-generation", project_id, configuration_fingerprint, identity_value
        )
        return cls(
            generation_id=f"gen_{identifier.replace('-', '')}",
            project_id=project_id,
            configuration_fingerprint=configuration_fingerprint,
            profile_versions=tuple(sorted(profile_versions.items())),
            adapter_versions=tuple(sorted(adapter_versions.items())),
            created_at=timestamp,
        )

    @classmethod
    def incremental(cls, project_id: str) -> IndexGeneration:
        fingerprint = sha256_bytes(b"sys4ai-exact-index-incremental-v1")
        identifier = stable_id("exact-index-generation", project_id, "incremental-v1")
        return cls(
            generation_id=f"gen_{identifier.replace('-', '')}",
            project_id=project_id,
            configuration_fingerprint=fingerprint,
            profile_versions=(),
            adapter_versions=(),
            created_at=utc_now(),
        )


@dataclass(frozen=True, slots=True)
class IndexMutationResult:
    project_id: str
    source_id: str
    action: str
    records_written: int
    generation_id: str


@dataclass(frozen=True, slots=True)
class RebuildResult:
    project_id: str
    generation_id: str
    sources_written: int
    records_written: int


@dataclass(frozen=True, slots=True)
class ExclusionExplanation:
    project_id: str
    path_or_uri: str
    disposition: str
    reason: str
    rule_ids: tuple[str, ...]
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class IndexHealth:
    schema_version: str
    fts5_available: bool
    active_generation_id: str | None
    current_source_count: int
    current_record_count: int
