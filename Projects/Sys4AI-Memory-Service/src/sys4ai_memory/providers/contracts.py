"""Typed, provider-neutral contracts for memory provider adapters.

These contracts are internal to the Sys4AI service boundary.  They deliberately
carry Sys4AI records rather than provider-native objects so adapters can be
replaced without changing service or agent call shapes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, JsonValue, field_validator, model_validator

from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    CapabilityName,
    MemoryRecord,
    MemoryScope,
    Permission,
    RecordStatus,
    RelationRecord,
    RetrievalMode,
    ScopeReference,
    SourceRecord,
)
from sys4ai_memory.contracts._base import (
    ApiVersion,
    ContractModel,
    NonEmptyString,
    RequestId,
    SchemaVersion,
    SemanticVersion,
    Sha256,
    StableIdentifier,
    TraceId,
    UtcDateTime,
    require_non_blank,
)

PROVIDER_CONTRACT_VERSION: Literal["1.0"] = "1.0"
COGNEE_PROVIDER_VERSION: Literal["1.5.3"] = "1.5.3"
IN_MEMORY_PROVIDER_VERSION = "1.0.0"


class ProviderName(StrEnum):
    """Built-in provider identifiers accepted by the factory."""

    IN_MEMORY = "in_memory"
    COGNEE = "cognee"


class ProviderMutation(StrEnum):
    """Mutation names used to bind a canonical authorization decision."""

    INITIALIZE = "initialize"
    REMEMBER = "remember"
    IMPROVE = "improve"
    FORGET = "forget"
    EXPORT = "export"
    IMPORT = "import"
    MIGRATE = "migrate"


MUTATION_PERMISSION: dict[ProviderMutation, Permission] = {
    ProviderMutation.INITIALIZE: Permission.ADMINISTER,
    ProviderMutation.REMEMBER: Permission.WRITE_DERIVED,
    ProviderMutation.IMPROVE: Permission.WRITE_DERIVED,
    ProviderMutation.FORGET: Permission.DELETE,
    ProviderMutation.EXPORT: Permission.SHARE,
    ProviderMutation.IMPORT: Permission.ADMINISTER,
    ProviderMutation.MIGRATE: Permission.ADMINISTER,
}


class ProviderHealthProbe(StrEnum):
    """Liveness never opens a provider store; readiness may inspect runtime state."""

    LIVENESS = "liveness"
    READINESS = "readiness"


class ProviderHealthState(StrEnum):
    ALIVE = "alive"
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ForgetAction(StrEnum):
    EXPIRE = "expire"
    WITHDRAW = "withdraw"
    SUPERSEDE = "supersede"
    DELETE_DERIVED = "delete-derived"
    DELETE_SOURCE = "delete-source"
    PRIVACY_ERASE = "privacy-erase"


class ProviderExportFormat(StrEnum):
    SYS4AI = "sys4ai"
    COGX = "cogx"


class ProviderContract(ContractModel):
    """Closed versioned base used by every provider request and result."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION


def _scope_contains_project(scope: ScopeReference, project_id: str) -> bool:
    if scope.level is MemoryScope.PROJECT and scope.scope_id == project_id:
        return True
    return any(
        parent.level is MemoryScope.PROJECT and parent.scope_id == project_id
        for parent in scope.parent_scopes
    )


class ProviderContext(ContractModel):
    """Explicit identity and isolation context required at the provider boundary."""

    project_id: StableIdentifier
    dataset_id: StableIdentifier
    principal_id: StableIdentifier
    scope: ScopeReference
    trace_id: TraceId

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if not _scope_contains_project(self.scope, self.project_id):
            raise ValueError("provider scope must identify its project boundary")
        return self


class PolicyEnvelope(ProviderContract):
    """A current Sys4AI authorization decision resolved outside semantic memory."""

    decision_id: StableIdentifier
    operation: ProviderMutation
    principal_id: StableIdentifier
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    scope: ScopeReference
    permission: Permission
    allowed: bool
    policy_id: NonEmptyString
    policy_revision: NonEmptyString
    canonical_source: NonEmptyString
    evaluated_at: UtcDateTime
    trace_id: TraceId
    impact_digest: Sha256 | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> Self:
        if not _scope_contains_project(self.scope, self.project_id):
            raise ValueError("policy scope must identify its project boundary")
        expected = MUTATION_PERMISSION[self.operation]
        if self.permission is not expected:
            raise ValueError(
                f"policy operation {self.operation.value} requires permission {expected.value}"
            )
        require_non_blank(self.canonical_source, "canonical_source")
        canonical_path = PurePosixPath(self.canonical_source)
        if (
            canonical_path.is_absolute()
            or ".." in canonical_path.parts
            or canonical_path.parts[:2] != ("control_records", "memory")
        ):
            raise ValueError(
                "policy decisions must identify a canonical control_records/memory source"
            )
        return self


class ProviderInitializationRequest(ProviderContract):
    context: ProviderContext
    configuration_fingerprint: Sha256
    dry_run: bool = True
    path_boundaries_validated: bool = False
    exclusions_validated: bool = False
    discovery_dry_run_approved: bool = False
    authorization: PolicyEnvelope | None = None


class ProviderInitializationResult(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    initialized: bool
    dry_run: bool
    planned_actions: tuple[NonEmptyString, ...]
    trace_id: TraceId


class ProviderCapabilities(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    supported: tuple[CapabilityName, ...]
    enabled: tuple[CapabilityName, ...]
    disabled_reasons: dict[CapabilityName, NonEmptyString] = Field(default_factory=dict)
    native_interface_exposed: Literal[False] = False

    @model_validator(mode="after")
    def validate_capabilities(self) -> Self:
        if len(self.supported) != len(set(self.supported)):
            raise ValueError("supported capabilities must not contain duplicates")
        if len(self.enabled) != len(set(self.enabled)):
            raise ValueError("enabled capabilities must not contain duplicates")
        if not set(self.enabled).issubset(self.supported):
            raise ValueError("enabled capabilities must be supported")
        if any(capability not in self.supported for capability in self.disabled_reasons):
            raise ValueError("disabled reasons may name only supported capabilities")
        return self


class RememberRequest(ProviderContract):
    context: ProviderContext
    request_id: RequestId
    idempotency_key: NonEmptyString
    records: Annotated[tuple[MemoryRecord, ...], Field(min_length=1)]
    relations: tuple[RelationRecord, ...] = ()
    sources: tuple[SourceRecord, ...] = ()
    authorization: PolicyEnvelope | None = None

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        return require_non_blank(value, "idempotency_key")

    @model_validator(mode="after")
    def validate_project_membership(self) -> Self:
        project_id = self.context.project_id
        if any(record.project_id != project_id for record in self.records):
            raise ValueError("every memory record must match the request project")
        if any(relation.project_id != project_id for relation in self.relations):
            raise ValueError("every relation must match the request project")
        if any(source.project_id != project_id for source in self.sources):
            raise ValueError("every source must match the request project")
        record_ids = tuple(record.record_id for record in self.records)
        relation_ids = tuple(relation.relation_id for relation in self.relations)
        source_ids = tuple(source.source_id for source in self.sources)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("records must not contain duplicate IDs")
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("relations must not contain duplicate IDs")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("sources must not contain duplicate IDs")
        return self


class RememberResult(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    request_id: RequestId
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    record_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    skipped_record_ids: tuple[str, ...] = ()
    idempotent_replay: bool
    trace_id: TraceId


class RecallRequest(ProviderContract):
    context: ProviderContext
    request_id: RequestId
    query: NonEmptyString
    mode: RetrievalMode
    namespaces: tuple[NonEmptyString, ...] = ()
    status_filters: tuple[RecordStatus, ...] = ()
    current_only: bool = True
    at_time: UtcDateTime | None = None
    include_relations: bool = True
    relation_types: tuple[NonEmptyString, ...] = ()
    top_k: Annotated[int, Field(ge=1, le=100)] = 15
    case_sensitive: bool = False

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        return require_non_blank(value, "query")

    @model_validator(mode="after")
    def validate_time_mode(self) -> Self:
        if self.at_time is not None and self.current_only:
            raise ValueError("historical at_time recall requires current_only=false")
        if len(self.namespaces) != len(set(self.namespaces)):
            raise ValueError("namespaces must not contain duplicates")
        if len(self.status_filters) != len(set(self.status_filters)):
            raise ValueError("status_filters must not contain duplicates")
        if len(self.relation_types) != len(set(self.relation_types)):
            raise ValueError("relation_types must not contain duplicates")
        return self


class ProviderChannelScores(ContractModel):
    exact: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    lexical: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    semantic: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    graph: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    temporal: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    final: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0


class ProviderRecallCandidate(ContractModel):
    record: MemoryRecord
    scores: ProviderChannelScores
    selection_reason: Annotated[tuple[NonEmptyString, ...], Field(min_length=1)]


class ProviderRecallResult(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    request_id: RequestId
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    query: NonEmptyString
    mode: RetrievalMode
    candidates: tuple[ProviderRecallCandidate, ...]
    relations: tuple[RelationRecord, ...]
    omitted_result_count: Annotated[int, Field(ge=0)]
    trace_id: TraceId


class ImproveRequest(ProviderContract):
    context: ProviderContext
    request_id: RequestId
    idempotency_key: NonEmptyString
    record_ids: tuple[str, ...] = ()
    profile_ids: tuple[NonEmptyString, ...] = ()
    authorization: PolicyEnvelope | None = None


class ImproveResult(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    request_id: RequestId
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    processed_record_ids: tuple[str, ...]
    changed_record_ids: tuple[str, ...]
    idempotent_replay: bool
    trace_id: TraceId


class ForgetRequest(ProviderContract):
    context: ProviderContext
    request_id: RequestId
    idempotency_key: NonEmptyString
    action: ForgetAction
    record_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    replacement_record_id: str | None = None
    execute: bool = False
    preview_digest: Sha256 | None = None
    authorization: PolicyEnvelope | None = None

    @model_validator(mode="after")
    def validate_selection(self) -> Self:
        if not self.record_ids and not self.source_ids:
            raise ValueError("forget requires explicit record_ids or source_ids")
        if self.action is ForgetAction.SUPERSEDE and self.replacement_record_id is None:
            raise ValueError("supersede requires replacement_record_id")
        if self.action is not ForgetAction.SUPERSEDE and self.replacement_record_id is not None:
            raise ValueError("replacement_record_id is valid only for supersede")
        if self.execute and self.preview_digest is None:
            raise ValueError("forget execution requires a preview_digest")
        return self


class ForgetResult(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    request_id: RequestId
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    action: ForgetAction
    executed: bool
    impact_digest: Sha256
    affected_record_ids: tuple[str, ...]
    affected_relation_ids: tuple[str, ...]
    canonical_source_changed: Literal[False] = False
    idempotent_replay: bool = False
    trace_id: TraceId


class SnapshotChecksums(ContractModel):
    sources_sha256: Sha256
    records_sha256: Sha256
    relations_sha256: Sha256
    package_sha256: Sha256


def _stable_json(value: object) -> str:
    def default(item: object) -> object:
        if isinstance(item, datetime):
            return item.isoformat().replace("+00:00", "Z")
        if isinstance(item, ContractModel):
            return item.to_json_dict()
        raise TypeError(f"unsupported digest value type: {type(item).__name__}")

    return json.dumps(
        value,
        default=default,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sha256(value: object) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


class ProviderSnapshot(ProviderContract):
    """Inspectable provider-neutral snapshot used by the conformance provider."""

    snapshot_version: Literal["1.0"] = PROVIDER_CONTRACT_VERSION
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    created_at: UtcDateTime
    origin_provider: ProviderName
    origin_provider_version: SemanticVersion
    profile_versions: dict[StableIdentifier, SemanticVersion]
    sources: tuple[SourceRecord, ...]
    records: tuple[MemoryRecord, ...]
    relations: tuple[RelationRecord, ...]
    checksums: SnapshotChecksums

    @classmethod
    def build(
        cls,
        *,
        project_id: str,
        dataset_id: str,
        created_at: datetime,
        origin_provider: ProviderName,
        origin_provider_version: str,
        profile_versions: dict[str, str],
        sources: tuple[SourceRecord, ...],
        records: tuple[MemoryRecord, ...],
        relations: tuple[RelationRecord, ...],
    ) -> ProviderSnapshot:
        source_values = [source.to_json_dict() for source in sources]
        record_values = [record.to_json_dict() for record in records]
        relation_values = [relation.to_json_dict() for relation in relations]
        sources_sha256 = _sha256(source_values)
        records_sha256 = _sha256(record_values)
        relations_sha256 = _sha256(relation_values)
        manifest = {
            "snapshot_version": PROVIDER_CONTRACT_VERSION,
            "project_id": project_id,
            "dataset_id": dataset_id,
            "created_at": created_at,
            "origin_provider": origin_provider,
            "origin_provider_version": origin_provider_version,
            "profile_versions": profile_versions,
            "sources_sha256": sources_sha256,
            "records_sha256": records_sha256,
            "relations_sha256": relations_sha256,
        }
        checksums = SnapshotChecksums(
            sources_sha256=sources_sha256,
            records_sha256=records_sha256,
            relations_sha256=relations_sha256,
            package_sha256=_sha256(manifest),
        )
        return cls(
            project_id=project_id,
            dataset_id=dataset_id,
            created_at=created_at,
            origin_provider=origin_provider,
            origin_provider_version=origin_provider_version,
            profile_versions=profile_versions,
            sources=sources,
            records=records,
            relations=relations,
            checksums=checksums,
        )

    @model_validator(mode="after")
    def validate_checksums(self) -> Self:
        if not self.profile_versions:
            raise ValueError("provider snapshots require at least one profile version")
        if any(source.project_id != self.project_id for source in self.sources):
            raise ValueError("snapshot sources must match the snapshot project")
        if any(record.project_id != self.project_id for record in self.records):
            raise ValueError("snapshot records must match the snapshot project")
        if any(relation.project_id != self.project_id for relation in self.relations):
            raise ValueError("snapshot relations must match the snapshot project")
        source_ids = {source.source_id for source in self.sources}
        if any(record.source.source_id not in source_ids for record in self.records):
            raise ValueError("snapshot records require complete source metadata")
        record_ids = {record.record_id for record in self.records}
        if any(
            relation.source_record_id not in record_ids
            or relation.target_record_id not in record_ids
            for relation in self.relations
        ):
            raise ValueError("snapshot relations require both endpoint records")
        source_values = [source.to_json_dict() for source in self.sources]
        record_values = [record.to_json_dict() for record in self.records]
        relation_values = [relation.to_json_dict() for relation in self.relations]
        expected_sources = _sha256(source_values)
        expected_records = _sha256(record_values)
        expected_relations = _sha256(relation_values)
        manifest = {
            "snapshot_version": self.snapshot_version,
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "created_at": self.created_at,
            "origin_provider": self.origin_provider,
            "origin_provider_version": self.origin_provider_version,
            "profile_versions": self.profile_versions,
            "sources_sha256": expected_sources,
            "records_sha256": expected_records,
            "relations_sha256": expected_relations,
        }
        expected_package = _sha256(manifest)
        actual = self.checksums
        if (
            actual.sources_sha256 != expected_sources
            or actual.records_sha256 != expected_records
            or actual.relations_sha256 != expected_relations
            or actual.package_sha256 != expected_package
        ):
            raise ValueError("provider snapshot checksum validation failed")
        return self


class ExportRequest(ProviderContract):
    context: ProviderContext
    request_id: RequestId
    idempotency_key: NonEmptyString
    format: ProviderExportFormat = ProviderExportFormat.SYS4AI
    profile_versions: dict[StableIdentifier, SemanticVersion] = Field(default_factory=dict)
    destination: NonEmptyString | None = None
    authorization: PolicyEnvelope | None = None

    @model_validator(mode="after")
    def validate_profile_versions(self) -> Self:
        if self.format is ProviderExportFormat.SYS4AI and not self.profile_versions:
            raise ValueError("Sys4AI export requires at least one profile version")
        return self


class ExportResult(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    request_id: RequestId
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    format: ProviderExportFormat
    snapshot: ProviderSnapshot | None = None
    destination: NonEmptyString | None = None
    checksum: Sha256 | None = None
    record_count: Annotated[int, Field(ge=0)]
    relation_count: Annotated[int, Field(ge=0)]
    idempotent_replay: bool = False
    trace_id: TraceId

    @model_validator(mode="after")
    def validate_artifact(self) -> Self:
        if self.format is ProviderExportFormat.SYS4AI and self.snapshot is None:
            raise ValueError("Sys4AI export requires a provider-neutral snapshot")
        if self.format is ProviderExportFormat.COGX and self.destination is None:
            raise ValueError("COGX export requires a destination")
        return self


class ImportRequest(ProviderContract):
    context: ProviderContext
    request_id: RequestId
    idempotency_key: NonEmptyString
    format: ProviderExportFormat
    snapshot: ProviderSnapshot | None = None
    source: NonEmptyString | None = None
    source_checksum: Sha256 | None = None
    execute: bool = False
    replace_existing: bool = False
    preview_digest: Sha256 | None = None
    authorization: PolicyEnvelope | None = None

    @model_validator(mode="after")
    def validate_source(self) -> Self:
        if self.format is ProviderExportFormat.SYS4AI and self.snapshot is None:
            raise ValueError("Sys4AI import requires a provider-neutral snapshot")
        if self.format is ProviderExportFormat.COGX and self.source is None:
            raise ValueError("COGX import requires a source")
        if self.format is ProviderExportFormat.COGX and self.source_checksum is None:
            raise ValueError("COGX import requires a verified source_checksum")
        if self.execute and self.preview_digest is None:
            raise ValueError("import execution requires a preview_digest")
        return self


class ImportResult(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    request_id: RequestId
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    format: ProviderExportFormat
    executed: bool
    impact_digest: Sha256
    imported_record_ids: tuple[str, ...]
    imported_relation_ids: tuple[str, ...]
    idempotent_replay: bool = False
    trace_id: TraceId


class MigrationRequest(ProviderContract):
    context: ProviderContext
    request_id: RequestId
    idempotency_key: NonEmptyString
    source_version: SemanticVersion
    target_version: SemanticVersion
    execute: bool = False
    preview_digest: Sha256 | None = None
    authorization: PolicyEnvelope | None = None

    @model_validator(mode="after")
    def validate_execution(self) -> Self:
        if self.execute and self.preview_digest is None:
            raise ValueError("migration execution requires a preview_digest")
        return self


class MigrationResult(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    request_id: RequestId
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    source_version: SemanticVersion
    target_version: SemanticVersion
    executed: bool
    impact_digest: Sha256
    transformed_record_ids: tuple[str, ...]
    warnings: tuple[NonEmptyString, ...]
    idempotent_replay: bool = False
    trace_id: TraceId


class HealthRequest(ProviderContract):
    context: ProviderContext
    probe: ProviderHealthProbe = ProviderHealthProbe.LIVENESS


class ProviderHealthComponent(ContractModel):
    name: StableIdentifier
    state: ProviderHealthState
    detail_code: StableIdentifier


class ProviderHealth(ProviderContract):
    provider_name: ProviderName
    provider_version: SemanticVersion
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    probe: ProviderHealthProbe
    state: ProviderHealthState
    checked_at: UtcDateTime
    initialized: bool
    components: tuple[ProviderHealthComponent, ...]
    trace_id: TraceId


class InMemoryProviderConfig(ContractModel):
    provider_name: Literal[ProviderName.IN_MEMORY] = ProviderName.IN_MEMORY
    project_id: StableIdentifier
    dataset_id: StableIdentifier


class CogneeProviderConfig(ContractModel):
    """Deny-safe Cognee configuration with no credential-bearing fields."""

    provider_name: Literal[ProviderName.COGNEE] = ProviderName.COGNEE
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    version_constraint: Literal["==1.5.3"] = "==1.5.3"
    expected_version: Literal["1.5.3"] = COGNEE_PROVIDER_VERSION
    mode: Literal["standalone"] = "standalone"
    initialize_on_load: Literal[False] = False
    allow_native_client_access: Literal[False] = False
    outbound_network: Literal["deny"] = "deny"
    allow_remote: Literal[False] = False
    allow_cloud_fallback: Literal[False] = False
    telemetry_enabled: Literal[False] = False
    project_root: NonEmptyString
    derived_data_root: NonEmptyString
    model_cache_root: NonEmptyString | None = None
    semantic_enabled: bool = False
    llm_provider: Literal["ollama", "llama_cpp"] | None = None
    llm_model: NonEmptyString | None = None
    llm_endpoint: NonEmptyString | None = None
    embedding_provider: Literal["fastembed"] | None = None
    embedding_model: NonEmptyString | None = None
    embedding_dimensions: Annotated[int, Field(gt=0)] | None = None
    allow_improve: bool = False
    allow_forget: bool = False
    allow_native_export: bool = False
    allow_native_import: bool = False
    allow_migrate: bool = False

    @model_validator(mode="after")
    def validate_local_profile(self) -> Self:
        project_root = Path(self.project_root).expanduser()
        data_root = Path(self.derived_data_root).expanduser()
        if not project_root.is_absolute() or not data_root.is_absolute():
            raise ValueError("Cognee project and derived-data roots must be absolute")
        resolved_project = project_root.resolve(strict=False)
        resolved_data = data_root.resolve(strict=False)
        if resolved_data == resolved_project or resolved_project not in resolved_data.parents:
            raise ValueError("Cognee derived-data root must be below the project root")
        model_root = Path(self.model_cache_root) if self.model_cache_root else data_root / "models"
        if not model_root.is_absolute():
            raise ValueError("Cognee model-cache root must be absolute")
        resolved_models = model_root.resolve(strict=False)
        if resolved_models == resolved_data or resolved_data not in resolved_models.parents:
            raise ValueError("Cognee model-cache root must be below the derived-data root")
        for candidate in (project_root, data_root, model_root):
            if ".." in candidate.parts or any(
                part.is_symlink() for part in (candidate, *candidate.parents)
            ):
                raise ValueError("Cognee paths cannot contain traversal or symlinks")
        if self.dataset_id == "main_dataset":
            raise ValueError("Cognee must not use the unscoped default dataset")

        model_fields = (
            self.llm_provider,
            self.llm_model,
            self.llm_endpoint,
            self.embedding_provider,
            self.embedding_model,
            self.embedding_dimensions,
        )
        if self.semantic_enabled and any(value is None for value in model_fields):
            raise ValueError("semantic Cognee use requires explicit local model profiles")
        if not self.semantic_enabled and any(value is not None for value in model_fields):
            raise ValueError("local model settings require semantic_enabled=true")
        if self.llm_endpoint is not None:
            parsed = urlsplit(self.llm_endpoint)
            if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
                "localhost",
                "127.0.0.1",
                "::1",
            }:
                raise ValueError("local LLM endpoint must use an explicit loopback URL")
        return self

    @property
    def resolved_model_cache_root(self) -> Path:
        return Path(self.model_cache_root or str(Path(self.derived_data_root) / "models"))


ProviderConfig = InMemoryProviderConfig | CogneeProviderConfig


def stable_digest(payload: object) -> str:
    """Return a deterministic SHA-256 digest for previews and idempotency."""

    return _sha256(payload)


def json_value(value: object) -> JsonValue:
    """Round-trip a value through JSON, rejecting provider-native objects."""

    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return json.loads(serialized)  # type: ignore[no-any-return]
