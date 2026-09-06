"""Strict provider-neutral envelopes shared by every public interface."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, JsonValue, StringConstraints, field_validator, model_validator

from sys4ai_memory.contracts import (
    API_VERSION,
    PUBLIC_OPERATION_CATALOG,
    SCHEMA_VERSION,
    ErrorEnvelope,
    MemoryScope,
    OperationName,
    RetrievalMode,
    ScopeReference,
)
from sys4ai_memory.contracts._base import (
    ApiVersion,
    ContractModel,
    MemoryRecordId,
    NonEmptyString,
    ProposalId,
    RequestId,
    SchemaVersion,
    Sha256,
    StableIdentifier,
    TraceId,
    require_non_blank,
)
from sys4ai_memory.observability import LONG_RUNNING_OPERATIONS, OperationState
from sys4ai_memory.security import require_secret_free

IdempotencyKey = Annotated[str, StringConstraints(min_length=1, max_length=512)]
OperationId = Annotated[
    str,
    StringConstraints(pattern=r"^op_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]


class InterfaceKind(StrEnum):
    PYTHON = "python"
    HTTP = "http"
    CLI = "cli"
    MCP = "mcp"


class ControlAction(StrEnum):
    """Interface actions that support, but do not extend, the public operation catalog."""

    INITIALIZE_DIRECT = "memory.initialize"
    INITIALIZE_PREVIEW = "memory.initialize.preview"
    INITIALIZE_APPLY = "memory.initialize.apply"
    OPERATION_STATUS = "memory.operations.status"


type InterfaceAction = OperationName | ControlAction


class InterfaceIdentity(ContractModel):
    """Authenticated caller identity; permissions are never asserted by a client."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    principal_id: StableIdentifier
    agent_type: StableIdentifier
    run_id: StableIdentifier


def _scope_identifies_project(scope: ScopeReference, project_id: str) -> bool:
    pending = [scope]
    while pending:
        current = pending.pop()
        if current.level is MemoryScope.PROJECT and current.scope_id == project_id:
            return True
        pending.extend(current.parent_scopes)
    return False


class AuthorizationContext(ContractModel):
    """Unambiguous project and query scope supplied to canonical authorization."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    identity: InterfaceIdentity
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    scope: ScopeReference
    query_project_ids: Annotated[tuple[StableIdentifier, ...], Field(min_length=1)]
    explicit_cross_project: bool = False

    @model_validator(mode="after")
    def validate_project_scope(self) -> Self:
        if not _scope_identifies_project(self.scope, self.project_id):
            raise ValueError("authorization scope must identify the request project")
        if len(self.query_project_ids) != len(set(self.query_project_ids)):
            raise ValueError("query_project_ids must not contain duplicates")
        if self.project_id not in self.query_project_ids:
            raise ValueError("query_project_ids must include the request project")
        if len(self.query_project_ids) > 1 and not self.explicit_cross_project:
            raise ValueError("cross-project scope must be explicit")
        return self


class AuditContext(ContractModel):
    """Metadata-only audit origin carried unchanged to the service boundary."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    interface: InterfaceKind
    client_id: StableIdentifier
    purpose: NonEmptyString

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        return require_non_blank(value, "audit purpose")


class OperationInput(ContractModel):
    """Closed base for action-specific JSON input."""


class HealthInput(OperationInput):
    detailed: bool = False


class SourcesListInput(OperationInput):
    include_excluded: bool = False


class SourcesExplainInput(OperationInput):
    target: NonEmptyString

    @field_validator("target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        return require_non_blank(value, "source target")


class SyncInput(OperationInput):
    source_ids: tuple[StableIdentifier, ...] = ()
    full: bool = False
    dry_run: bool = False

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("source_ids must not contain duplicates")
        return value


class RecallInput(OperationInput):
    query: NonEmptyString
    mode: RetrievalMode = RetrievalMode.HYBRID
    limit: Annotated[int, Field(ge=1, le=100)] = 10
    namespaces: tuple[NonEmptyString, ...] = ()
    current_only: bool = True
    synthesize: bool = False

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        return require_non_blank(value, "query")


class GetInput(OperationInput):
    record_id: MemoryRecordId
    include_history: bool = False


class GraphInput(OperationInput):
    record_id: MemoryRecordId
    max_depth: Annotated[int, Field(ge=1, le=1)] = 1
    relation_types: tuple[NonEmptyString, ...] = ()


class ProposeInput(OperationInput):
    proposal: Annotated[dict[str, JsonValue], Field(min_length=1)]


class ApproveInput(OperationInput):
    proposal_id: ProposalId
    decision: Literal["approve", "reject"]
    reason: NonEmptyString


class SupersedeInput(OperationInput):
    record_id: MemoryRecordId
    replacement_record_id: MemoryRecordId
    reason: NonEmptyString

    @model_validator(mode="after")
    def validate_distinct_records(self) -> Self:
        if self.record_id == self.replacement_record_id:
            raise ValueError("a record cannot supersede itself")
        return self


class ImproveInput(OperationInput):
    record_id: MemoryRecordId | None = None
    feedback: Annotated[dict[str, JsonValue], Field(min_length=1)]


class ForgetInput(OperationInput):
    record_ids: Annotated[tuple[MemoryRecordId, ...], Field(min_length=1)]
    action: Literal["expire", "withdraw", "delete-derived", "delete-source", "privacy-erase"]
    reason: NonEmptyString
    execute: bool = False
    operation_id: OperationId | None = None
    impact_digest: Sha256 | None = None

    @field_validator("record_ids")
    @classmethod
    def validate_record_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("record_ids must not contain duplicates")
        return value

    @model_validator(mode="after")
    def validate_execution_digest(self) -> Self:
        if self.execute and (self.operation_id is None or self.impact_digest is None):
            raise ValueError(
                "forget execution requires the preview operation ID and reviewed impact digest"
            )
        return self


class RebuildInput(OperationInput):
    preview_only: bool = True
    generation_label: StableIdentifier | None = None
    operation_id: OperationId | None = None
    impact_digest: Sha256 | None = None

    @model_validator(mode="after")
    def validate_activation_digest(self) -> Self:
        if not self.preview_only and (
            self.operation_id is None or self.impact_digest is None
        ):
            raise ValueError(
                "rebuild activation requires the preview operation ID and reviewed impact digest"
            )
        return self


class ExportInput(OperationInput):
    output_path: NonEmptyString
    format: Literal["sys4ai", "cogx"] = "sys4ai"
    include_sensitive: bool = False
    age_recipient: str | None = None


class ImportInput(OperationInput):
    package_path: NonEmptyString
    activate: bool = False
    expected_sha256: Sha256 | None = None
    impact_digest: Sha256 | None = None

    @model_validator(mode="after")
    def validate_activation_digest(self) -> Self:
        if self.activate and self.impact_digest is None:
            raise ValueError("import activation requires the reviewed impact digest")
        return self


class ExplainInput(OperationInput):
    record_id: MemoryRecordId


class InitializationPreviewInput(OperationInput):
    configuration_path: NonEmptyString = "config/memory.toml"


class InitializationDirectInput(OperationInput):
    configuration_path: NonEmptyString = "config/memory.toml"


class InitializationApplyInput(OperationInput):
    configuration_path: NonEmptyString = "config/memory.toml"
    impact_digest: Sha256


class OperationStatusInput(OperationInput):
    operation_id: OperationId


OPERATION_INPUT_MODELS: dict[InterfaceAction, type[OperationInput]] = {
    OperationName.HEALTH: HealthInput,
    OperationName.SOURCES_LIST: SourcesListInput,
    OperationName.SOURCES_EXPLAIN: SourcesExplainInput,
    OperationName.SYNC: SyncInput,
    OperationName.RECALL: RecallInput,
    OperationName.GET: GetInput,
    OperationName.GRAPH: GraphInput,
    OperationName.PROPOSE: ProposeInput,
    OperationName.APPROVE: ApproveInput,
    OperationName.SUPERSEDE: SupersedeInput,
    OperationName.IMPROVE: ImproveInput,
    OperationName.FORGET: ForgetInput,
    OperationName.REBUILD: RebuildInput,
    OperationName.EXPORT: ExportInput,
    OperationName.IMPORT: ImportInput,
    OperationName.EXPLAIN: ExplainInput,
    ControlAction.INITIALIZE_PREVIEW: InitializationPreviewInput,
    ControlAction.INITIALIZE_DIRECT: InitializationDirectInput,
    ControlAction.INITIALIZE_APPLY: InitializationApplyInput,
    ControlAction.OPERATION_STATUS: OperationStatusInput,
}

_PUBLIC_MUTATING_OPERATIONS = frozenset(
    operation.name for operation in PUBLIC_OPERATION_CATALOG if operation.mutating
)
MUTATING_ACTIONS = _PUBLIC_MUTATING_OPERATIONS | {
    ControlAction.INITIALIZE_DIRECT,
    ControlAction.INITIALIZE_APPLY,
}


def action_value(action: InterfaceAction) -> str:
    return action.value


def parse_action(value: object) -> InterfaceAction:
    if isinstance(value, OperationName | ControlAction):
        return value
    if not isinstance(value, str):
        raise ValueError("operation must be a string")
    try:
        return OperationName(value)
    except ValueError:
        return ControlAction(value)


class DispatchRequest(ContractModel):
    """The sole invocation shape accepted by a memory service dispatcher."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    operation: InterfaceAction
    request_id: RequestId
    trace_id: TraceId
    authorization: AuthorizationContext
    audit: AuditContext
    idempotency_key: IdempotencyKey | None = None
    payload: dict[str, JsonValue]

    @model_validator(mode="before")
    @classmethod
    def normalize_action_payload(cls, value: object) -> object:
        if isinstance(value, cls) or not isinstance(value, Mapping):
            return value
        normalized = dict(value)
        action = parse_action(normalized.get("operation"))
        payload = OPERATION_INPUT_MODELS[action].model_validate(normalized.get("payload", {}))
        normalized["operation"] = action
        normalized["payload"] = payload.model_dump(mode="json", exclude_none=False)
        return normalized

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency(cls, value: str | None) -> str | None:
        return None if value is None else require_non_blank(value, "idempotency_key")

    @model_validator(mode="after")
    def validate_context_and_safety(self) -> Self:
        if self.operation in MUTATING_ACTIONS and self.idempotency_key is None:
            raise ValueError("mutating operations require an idempotency key")
        if self.operation not in MUTATING_ACTIONS and self.idempotency_key is not None:
            raise ValueError("read-only operations do not accept an idempotency key")
        require_secret_free(self.payload, field_path="request.payload")
        return self

    def typed_payload(self) -> OperationInput:
        return OPERATION_INPUT_MODELS[self.operation].model_validate(self.payload)


class LongOperationReference(ContractModel):
    """Stable polling metadata returned for every long-running operation."""

    operation_id: OperationId
    project_id: StableIdentifier
    operation: OperationName
    trace_id: TraceId
    state: OperationState
    retry_safe: bool
    retry_after_seconds: Annotated[int, Field(ge=0, le=3600)] | None = None
    status_action: Literal["memory.operations.status"] = "memory.operations.status"


class DispatchSuccess(ContractModel):
    """Successful result envelope shared byte-for-byte across adapters."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    operation: InterfaceAction
    project_id: StableIdentifier
    request_id: RequestId
    trace_id: TraceId
    result: dict[str, JsonValue]
    operation_status: LongOperationReference | None = None

    @model_validator(mode="after")
    def validate_long_operation(self) -> Self:
        if (
            isinstance(self.operation, OperationName)
            and self.operation in LONG_RUNNING_OPERATIONS
            and self.operation_status is None
        ):
            raise ValueError("long-running operations require operation status metadata")
        if self.operation_status is not None:
            if self.operation_status.project_id != self.project_id:
                raise ValueError("operation status project does not match the result")
            if self.operation_status.trace_id != self.trace_id:
                raise ValueError("operation status trace does not match the result")
            if self.operation_status.operation != self.operation:
                raise ValueError("operation status operation does not match the result")
        require_secret_free(self.result, field_path="response.result")
        return self


type DispatchResponse = DispatchSuccess | ErrorEnvelope
