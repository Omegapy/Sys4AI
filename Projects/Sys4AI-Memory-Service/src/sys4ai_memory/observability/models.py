"""Strict metadata-only contracts shared by observability components."""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from sys4ai_memory.contracts import API_VERSION, SCHEMA_VERSION, OperationName, RetrievalMode
from sys4ai_memory.contracts._base import Sha256, TraceId, UtcDateTime
from sys4ai_memory.security import AuditEvent, require_secret_free
from sys4ai_memory.util import canonical_json_bytes, sha256_bytes

MetadataCode = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_.:@/-]*$", min_length=1, max_length=255),
]
MetadataToken = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:@/+~-]*$", min_length=1, max_length=255),
]
CommandToken = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9_./:@+=,~-][A-Za-z0-9_.:/@+=,~-]*$", max_length=255),
]
SourceIdentifier = Annotated[
    str,
    StringConstraints(pattern=r"^src_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]


class ObservabilityModel(BaseModel):
    """Closed immutable base for records that may be persisted."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class HealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class OperationState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DirtyState(StrEnum):
    CLEAN = "clean"
    DIRTY = "dirty"
    NOT_VERSIONED = "not_versioned"
    UNKNOWN = "unknown"


class EvidenceLocatorKind(StrEnum):
    ARTIFACT = "artifact"
    REQUIREMENT = "requirement"
    SCHEMA = "schema"
    TEST = "test"
    VALIDATION = "validation"


class AdministrativeOperation(StrEnum):
    """Governed control-plane actions that sit outside the public memory API."""

    INITIALIZE_DIRECT = "memory.initialize"
    INITIALIZE_PREVIEW = "memory.initialize.preview"
    INITIALIZE_APPLY = "memory.initialize.apply"
    OPERATION_STATUS = "memory.operations.status"
    SOURCE_REGISTER = "memory.sources.register"
    PROFILE_INSTALL = "memory.profile.install"
    CONFIGURATION_CHANGE = "memory.configuration.change"
    PERMISSION_CHANGE = "memory.permissions.change"
    TELEMETRY_CHANGE = "memory.telemetry.change"


type AuditedOperation = OperationName | AdministrativeOperation


class VersionContext(ObservabilityModel):
    """Versions and fingerprints needed to interpret one operation."""

    configuration_version: MetadataToken
    configuration_fingerprint: Sha256
    profile_versions: dict[MetadataCode, MetadataToken] = Field(default_factory=dict)
    profile_fingerprints: dict[MetadataCode, Sha256] = Field(default_factory=dict)
    provider_name: MetadataCode
    provider_version: MetadataToken
    provider_fingerprint: Sha256
    source_registry_fingerprint: Sha256 | None = None

    @model_validator(mode="after")
    def validate_profile_sets(self) -> Self:
        if set(self.profile_fingerprints) != set(self.profile_versions):
            raise ValueError("every profile version requires one matching fingerprint")
        require_secret_free(self.model_dump(mode="json"), field_path="version_context")
        return self


class CountMetric(ObservabilityModel):
    name: MetadataCode
    value: Annotated[int, Field(ge=0)]


class RecallChannelCount(ObservabilityModel):
    channel: RetrievalMode
    candidate_count: Annotated[int, Field(ge=0)]


class RecallFilterTrace(ObservabilityModel):
    filter_code: MetadataCode
    examined_count: Annotated[int, Field(ge=0)]
    excluded_count: Annotated[int, Field(ge=0)]
    reason_codes: tuple[MetadataCode, ...] = ()

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        if self.excluded_count > self.examined_count:
            raise ValueError("filter exclusions cannot exceed examined candidates")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("filter reason codes must be unique")
        return self


class RecallRankingTrace(ObservabilityModel):
    stage_code: MetadataCode
    input_count: Annotated[int, Field(ge=0)]
    output_count: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        if self.output_count > self.input_count:
            raise ValueError("ranking output cannot exceed its input candidate count")
        return self


class RecallTrace(ObservabilityModel):
    """Inspectable retrieval decisions with no query or returned content."""

    selected_channels: tuple[RetrievalMode, ...]
    candidates: tuple[RecallChannelCount, ...]
    filters: tuple[RecallFilterTrace, ...]
    ranking_stages: tuple[RecallRankingTrace, ...]
    returned_source_ids: tuple[SourceIdentifier, ...]
    omitted_result_count: Annotated[int, Field(ge=0)] = 0

    @model_validator(mode="after")
    def validate_trace(self) -> Self:
        if not self.selected_channels:
            raise ValueError("a recall trace requires at least one selected channel")
        if len(self.selected_channels) != len(set(self.selected_channels)):
            raise ValueError("selected recall channels must be unique")
        candidate_channels = tuple(item.channel for item in self.candidates)
        if len(candidate_channels) != len(set(candidate_channels)):
            raise ValueError("candidate channels must be unique")
        if set(candidate_channels) != set(self.selected_channels):
            raise ValueError("candidate counts must cover every selected channel exactly once")
        if len(self.returned_source_ids) != len(set(self.returned_source_ids)):
            raise ValueError("returned source IDs must be unique")
        return self


class OperationAuditRecord(ObservabilityModel):
    """Allowlisted audit record for one public or control-plane operation."""

    record_kind: Literal["operation_audit"] = "operation_audit"
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    api_version: Literal["1.0"] = API_VERSION
    event_id: MetadataCode
    occurred_at: UtcDateTime
    actor_id: MetadataCode
    effective_principal_id: MetadataCode
    project_id: MetadataCode
    dataset_id: MetadataCode
    operation: AuditedOperation
    target_ids: tuple[MetadataCode, ...] = ()
    policy_allowed: bool
    policy_reason_code: MetadataCode
    decision_reason_codes: tuple[MetadataCode, ...] = ()
    policy_decision_ref: MetadataCode
    permission_revision: MetadataCode | None = None
    canonical_policy_sha256: Sha256 | None = None
    grant_id: MetadataCode | None = None
    outcome_code: MetadataCode
    trace_id: TraceId
    versions: VersionContext
    counts: tuple[CountMetric, ...] = ()
    warning_codes: tuple[MetadataCode, ...] = ()
    recall: RecallTrace | None = None

    @model_validator(mode="after")
    def validate_record(self) -> Self:
        policy_path = PurePosixPath(self.policy_decision_ref)
        if policy_path.parts[:2] != ("control_records", "memory"):
            raise ValueError("audit policy decision must reference canonical control records")
        if (self.permission_revision is None) != (self.canonical_policy_sha256 is None):
            raise ValueError("policy revision and canonical fingerprint must be recorded together")
        if self.policy_allowed and self.permission_revision is None:
            raise ValueError("allowed policy decisions require current canonical evidence")
        if len(self.target_ids) != len(set(self.target_ids)):
            raise ValueError("audit target IDs must be unique")
        count_names = tuple(item.name for item in self.counts)
        if len(count_names) != len(set(count_names)):
            raise ValueError("audit count names must be unique")
        if len(self.warning_codes) != len(set(self.warning_codes)):
            raise ValueError("audit warning codes must be unique")
        if len(self.decision_reason_codes) != len(set(self.decision_reason_codes)):
            raise ValueError("audit decision reason codes must be unique")
        successful_recall = (
            self.operation is OperationName.RECALL
            and self.policy_allowed
            and self.outcome_code in {"succeeded", "idempotent_replay"}
        )
        if successful_recall and self.recall is None:
            raise ValueError("successful memory.recall audit records require a recall trace")
        if self.operation is not OperationName.RECALL and self.recall is not None:
            raise ValueError("recall traces are valid only for memory.recall")
        require_secret_free(self.model_dump(mode="json"), field_path="operation_audit")
        return self

    def to_security_event(self) -> AuditEvent:
        """Project this richer record onto the established security audit contract."""

        return AuditEvent(
            event_id=self.event_id,
            occurred_at=self.occurred_at,
            principal_id=self.effective_principal_id,
            project_id=self.project_id,
            dataset_id=self.dataset_id,
            operation=self.operation.value,
            target_ids=self.target_ids,
            policy_decision=self.policy_reason_code,
            outcome=self.outcome_code,
            trace_id=self.trace_id,
            policy_id=self.policy_decision_ref,
            permission_revision=self.permission_revision,
            counts=tuple((item.name, item.value) for item in self.counts),
            warning_codes=self.warning_codes,
        )


class EvidenceLocator(ObservabilityModel):
    kind: EvidenceLocatorKind
    reference: MetadataCode
    content_sha256: Sha256 | None = None
    line: Annotated[int, Field(ge=1)] | None = None

    @model_validator(mode="after")
    def validate_reference(self) -> Self:
        if self.kind in {
            EvidenceLocatorKind.ARTIFACT,
            EvidenceLocatorKind.SCHEMA,
            EvidenceLocatorKind.TEST,
            EvidenceLocatorKind.VALIDATION,
        }:
            path_text = self.reference.split("::", maxsplit=1)[0]
            path = PurePosixPath(path_text)
            if path.is_absolute() or ".." in path.parts or "\\" in path_text:
                raise ValueError("evidence path must be project-relative and normalized")
        return self


class ValidationReceipt(ObservabilityModel):
    """Deterministic evidence metadata supplied after a validation command ran."""

    record_kind: Literal["validation_receipt"] = "validation_receipt"
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    api_version: Literal["1.0"] = API_VERSION
    receipt_id: Annotated[
        str,
        StringConstraints(pattern=r"^vrc_[0-9a-f]{64}$"),
    ]
    command_id: MetadataCode
    command: Annotated[tuple[CommandToken, ...], Field(min_length=1, max_length=64)]
    exit_status: Annotated[int, Field(ge=0, le=255)]
    recorded_at: UtcDateTime
    source_revision: MetadataToken | None
    dirty_state: DirtyState
    dirty_state_fingerprint: Sha256 | None = None
    versions: VersionContext
    warning_codes: Annotated[tuple[MetadataCode, ...], Field(max_length=256)] = ()
    evidence: Annotated[tuple[EvidenceLocator, ...], Field(min_length=1, max_length=256)]

    @model_validator(mode="after")
    def validate_receipt(self) -> Self:
        if self.dirty_state is DirtyState.DIRTY and self.dirty_state_fingerprint is None:
            raise ValueError("dirty source state requires a fingerprint")
        if self.dirty_state is not DirtyState.DIRTY and self.dirty_state_fingerprint is not None:
            raise ValueError("only dirty source state may carry a dirty-state fingerprint")
        versioned_state = self.dirty_state in {DirtyState.CLEAN, DirtyState.DIRTY}
        if versioned_state and self.source_revision is None:
            raise ValueError("versioned source state requires a source revision")
        if self.dirty_state is DirtyState.NOT_VERSIONED and self.source_revision is not None:
            raise ValueError("not-versioned source state cannot claim a source revision")
        for token in self.command:
            path = PurePosixPath(token.split("=", maxsplit=1)[-1])
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("validation command tokens cannot contain unsafe paths")
        if len(self.warning_codes) != len(set(self.warning_codes)):
            raise ValueError("validation warning codes must be unique")
        references = tuple((item.kind, item.reference, item.line) for item in self.evidence)
        if len(references) != len(set(references)):
            raise ValueError("validation evidence locators must be unique")
        require_secret_free(self.model_dump(mode="json"), field_path="validation_receipt")
        expected = "vrc_" + sha256_bytes(canonical_json_bytes(self.digest_payload()))
        if self.receipt_id != expected:
            raise ValueError("validation receipt ID does not match its deterministic payload")
        return self

    def digest_payload(self) -> dict[str, object]:
        payload = self.model_dump(mode="json")
        payload.pop("receipt_id")
        return payload
