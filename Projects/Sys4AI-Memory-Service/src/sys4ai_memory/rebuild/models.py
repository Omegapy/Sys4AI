"""Provider-neutral generation rebuild contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sys4ai_memory.authorization import AuthorizationDecision
from sys4ai_memory.contracts import Permission, RebuildReceipt
from sys4ai_memory.contracts._base import Sha256, UtcDateTime


class RebuildModel(BaseModel):
    """Closed immutable base for rebuild orchestration metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class RebuildMode(StrEnum):
    FULL = "full"
    INCREMENTAL = "incremental"


class RebuildOutcome(StrEnum):
    PREVIEWED = "previewed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RebuildStage(StrEnum):
    PREVIEW = "preview"
    DISCOVERY = "discovery"
    NORMALIZATION = "normalization"
    EXACT_INDEX = "exact_index"
    PROVIDER = "provider"
    VALIDATION = "validation"
    ACTIVATION = "activation"
    COMPLETE = "complete"


class SourceRevision(RebuildModel):
    source_id: str = Field(pattern=r"^src_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
    path: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    content_sha256: Sha256


class SourceDeltaSummary(RebuildModel):
    unchanged: int = Field(ge=0)
    added: int = Field(ge=0)
    changed: int = Field(ge=0)
    moved: int = Field(ge=0)
    deleted: int = Field(ge=0)
    failed: int = Field(ge=0)
    resumed: int = Field(ge=0)


class GenerationFingerprints(RebuildModel):
    source_registry_sha256: Sha256
    profile_registry_sha256: Sha256
    external_manifest_sha256: Sha256 | None
    schema_set_sha256: Sha256
    configuration_sha256: Sha256
    adapter_versions: dict[str, str] = Field(min_length=1)
    provider_name: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    model_identifiers: tuple[str, ...]
    deterministic: bool


class RebuildImpact(RebuildModel):
    project_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    mode: RebuildMode
    planned_generation_id: str = Field(pattern=r"^gen_[A-Za-z0-9_.:@-]+$")
    previous_generation_id: str | None
    source_revisions: tuple[SourceRevision, ...]
    delta: SourceDeltaSummary
    generated_paths: tuple[str, ...]

    @model_validator(mode="after")
    def validate_sources(self) -> Self:
        source_ids = tuple(item.source_id for item in self.source_revisions)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("rebuild impact source IDs must be unique")
        if any(path.startswith("/") or ".." in path.split("/") for path in self.generated_paths):
            raise ValueError("generated paths must be safe project-relative paths")
        return self


class RebuildPreview(RebuildModel):
    schema_version: Literal["1.0"] = "1.0"
    operation_id: str = Field(min_length=1)
    generated_at: UtcDateTime
    fingerprints: GenerationFingerprints
    impact: RebuildImpact
    source_manifest_sha256: Sha256
    impact_digest: Sha256


class AuthorizedRebuildImpact(RebuildModel):
    """A fresh canonical permission result bound to one exact rebuild preview."""

    decision: AuthorizationDecision
    impact_digest: Sha256

    @model_validator(mode="after")
    def validate_decision(self) -> Self:
        decision = self.decision
        if not decision.allowed:
            raise ValueError("rebuild authorization must be allowed")
        if decision.operation != "memory.rebuild.activate":
            raise ValueError("authorization is not for rebuild activation")
        if decision.permission is not Permission.REBUILD:
            raise ValueError("rebuild activation requires rebuild permission")
        if decision.permission_revision is None or decision.canonical_sha256 is None:
            raise ValueError("rebuild authorization must identify current canonical policy")
        return self


class RebuildProgress(RebuildModel):
    sequence: int = Field(ge=1)
    stage: RebuildStage
    detail_code: str = Field(min_length=1)
    completed_items: int = Field(ge=0)
    total_items: int = Field(ge=0)
    observed_at: UtcDateTime


class RebuildCheckpoint(RebuildModel):
    generation_id: str = Field(pattern=r"^gen_[A-Za-z0-9_.:@-]+$")
    stage: RebuildStage
    completed_source_ids: tuple[str, ...]
    failed_source_ids: tuple[str, ...]
    sequence: int = Field(ge=0)
    cancel_requested: bool
    updated_at: UtcDateTime


class RebuildExecutionReceipt(RebuildModel):
    """Public receipt plus activation, rollback, and validation evidence."""

    receipt: RebuildReceipt
    dataset_id: str = Field(min_length=1)
    generation_id: str = Field(pattern=r"^gen_[A-Za-z0-9_.:@-]+$")
    previous_generation_id: str | None
    mode: RebuildMode
    outcome: RebuildOutcome
    activated: bool
    prior_generation_preserved: bool
    impact_digest: Sha256
    generation_manifest_sha256: Sha256 | None
    source_count: int = Field(ge=0)
    record_count: int = Field(ge=0)
    relation_count: int = Field(ge=0)
    provider_snapshot_sha256: Sha256 | None
    delta: SourceDeltaSummary
    validation_checks: tuple[str, ...]
    checkpoint: RebuildCheckpoint
    progress: tuple[RebuildProgress, ...]
    failure_code: str | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        if self.outcome is RebuildOutcome.SUCCEEDED:
            if not self.activated or self.generation_manifest_sha256 is None:
                raise ValueError("successful rebuild must activate a validated generation")
            if self.failure_code is not None:
                raise ValueError("successful rebuild cannot carry a failure code")
        elif self.activated:
            raise ValueError("failed or cancelled rebuild cannot be activated")
        if self.receipt.outcome != self.outcome.value:
            raise ValueError("public and generation receipt outcomes must match")
        return self


class DriftKind(StrEnum):
    SOURCE = "source"
    CONFIGURATION = "configuration"
    PROFILE = "profile"
    SCHEMA = "schema"
    ADAPTER = "adapter"
    PROVIDER = "provider"
    MODEL = "model"
    GENERATION = "generation"


class DriftItem(RebuildModel):
    kind: DriftKind
    identity: str = Field(min_length=1)
    expected: str | None
    observed: str | None


class DriftReport(RebuildModel):
    project_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    active_generation_id: str | None
    checked_at: UtcDateTime
    drifted: bool
    items: tuple[DriftItem, ...]

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.drifted != bool(self.items):
            raise ValueError("drifted must match whether drift items exist")
        return self
