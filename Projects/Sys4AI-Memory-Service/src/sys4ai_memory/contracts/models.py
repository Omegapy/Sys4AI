"""Provider-neutral public data contracts from PRD sections 14 through 19."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import (
    Field,
    JsonValue,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

from ._base import (
    ContractModel,
    MemoryRecordId,
    NonEmptyString,
    ProposalId,
    RebuildReceiptId,
    RelationId,
    RequestId,
    SemanticVersion,
    Sha256,
    SourceId,
    StableIdentifier,
    TraceId,
    UtcDateTime,
    VersionedContract,
    require_non_blank,
)
from .enums import (
    AuthorityTier,
    CoreRecordType,
    EpistemicStatus,
    EvidenceState,
    MemoryScope,
    PolicyAction,
    RecordStatus,
    RetrievalMode,
    Sensitivity,
    SourceRole,
    TrustClass,
)

RecordTypeName = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z][A-Za-z0-9_]*$", min_length=1, max_length=128),
]
RelationTypeName = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$", min_length=1, max_length=128),
]
FieldPath = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_.]*$", min_length=1, max_length=255),
]
UnitScore = Annotated[float, Field(ge=0.0, le=1.0)]
NonNegativeScore = Annotated[float, Field(ge=0.0)]


class ScopeReference(ContractModel):
    level: MemoryScope
    scope_id: StableIdentifier
    parent_scopes: tuple[ScopeReference, ...] = ()

    @model_validator(mode="after")
    def validate_parent_scopes(self) -> Self:
        identities = tuple((scope.level, scope.scope_id) for scope in self.parent_scopes)
        if len(identities) != len(set(identities)):
            raise ValueError("parent_scopes must not contain duplicates")
        if (self.level, self.scope_id) in identities:
            raise ValueError("a scope must not list itself as a parent")
        return self


class MemoryContent(ContractModel):
    exact: NonEmptyString
    summary: NonEmptyString | None
    structured: dict[str, JsonValue]

    @field_validator("exact")
    @classmethod
    def validate_exact(cls, value: str) -> str:
        return require_non_blank(value, "content.exact")


class SourceAnchor(ContractModel):
    source_id: SourceId
    source_kind: NonEmptyString
    path: NonEmptyString | None = None
    origin_uri: NonEmptyString | None = None
    locator: dict[str, JsonValue]
    git_commit: NonEmptyString | None = None
    git_blob_sha: NonEmptyString | None = None
    working_tree_state: NonEmptyString | None = None
    content_sha256: Sha256

    @model_validator(mode="after")
    def validate_anchor(self) -> Self:
        if self.path is None and self.origin_uri is None:
            raise ValueError("source must identify path or origin_uri")
        if not self.locator:
            raise ValueError("source.locator must contain an exact source anchor")
        if self.source_kind in {"git_file", "repository", "repository_file"} and not any(
            (self.git_commit, self.git_blob_sha, self.working_tree_state)
        ):
            raise ValueError("repository source must record Git revision or working-tree state")
        return self


class AuthorityBinding(ContractModel):
    tier: AuthorityTier
    trust_class: TrustClass
    canonical: bool


class EpistemicMetadata(ContractModel):
    status: EpistemicStatus
    verification: NonEmptyString
    confidence: UnitScore | None

    @model_validator(mode="after")
    def validate_verified_fact(self) -> Self:
        if self.status is EpistemicStatus.VERIFIED_FACT and self.verification.casefold() in {
            "model-extracted",
            "model_extracted",
            "unverified",
        }:
            raise ValueError("verified_fact requires evidence beyond model extraction")
        return self


class LifecycleMetadata(ContractModel):
    status: RecordStatus
    valid_from: UtcDateTime
    valid_to: UtcDateTime | None
    supersedes: tuple[MemoryRecordId, ...]
    superseded_by: tuple[MemoryRecordId, ...]

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("lifecycle.valid_to must not precede valid_from")
        if len(self.supersedes) != len(set(self.supersedes)):
            raise ValueError("lifecycle.supersedes must not contain duplicates")
        if len(self.superseded_by) != len(set(self.superseded_by)):
            raise ValueError("lifecycle.superseded_by must not contain duplicates")
        return self


class SecurityMetadata(ContractModel):
    sensitivity: Sensitivity
    contains_secret: bool
    retention_policy: NonEmptyString

    @model_validator(mode="after")
    def prohibit_secrets(self) -> Self:
        if self.sensitivity is Sensitivity.SECRET_PROHIBITED or self.contains_secret:
            raise ValueError("secret-prohibited content must not enter durable memory")
        return self


class ProcessingMetadata(ContractModel):
    parsed_by: NonEmptyString
    adapter_version: NonEmptyString
    profile_id: NonEmptyString
    deterministic_fields: tuple[FieldPath, ...]
    model_extracted_fields: tuple[FieldPath, ...]
    model_id: NonEmptyString | None
    prompt_fingerprint: Sha256 | None
    # MEM-FR-035 names "processing time" but its example omits a field name.
    # `processed_at` is the explicit provider-neutral representation used here.
    processed_at: UtcDateTime

    @model_validator(mode="after")
    def validate_field_provenance(self) -> Self:
        deterministic = set(self.deterministic_fields)
        extracted = set(self.model_extracted_fields)
        if deterministic & extracted:
            raise ValueError("deterministic and model-extracted fields must be disjoint")
        if len(deterministic) != len(self.deterministic_fields):
            raise ValueError("deterministic_fields must not contain duplicates")
        if len(extracted) != len(self.model_extracted_fields):
            raise ValueError("model_extracted_fields must not contain duplicates")
        if extracted and (self.model_id is None or self.prompt_fingerprint is None):
            raise ValueError("model-extracted fields require model_id and prompt_fingerprint")
        return self


class IndexingMetadata(ContractModel):
    exact_fields: tuple[FieldPath, ...]
    lexical_fields: tuple[FieldPath, ...]
    semantic_fields: tuple[FieldPath, ...]
    graph_enabled: bool

    @model_validator(mode="after")
    def validate_unique_fields(self) -> Self:
        for field_name, fields in (
            ("exact_fields", self.exact_fields),
            ("lexical_fields", self.lexical_fields),
            ("semantic_fields", self.semantic_fields),
        ):
            if len(fields) != len(set(fields)):
                raise ValueError(f"indexing.{field_name} must not contain duplicates")
        return self


class MemoryRecord(VersionedContract):
    record_id: MemoryRecordId
    record_type: RecordTypeName
    profile_type: NonEmptyString | None
    project_id: StableIdentifier
    namespace: NonEmptyString
    scope: ScopeReference
    title: NonEmptyString
    content: MemoryContent
    source: SourceAnchor
    authority: AuthorityBinding
    epistemic: EpistemicMetadata
    lifecycle: LifecycleMetadata
    security: SecurityMetadata
    processing: ProcessingMetadata
    indexing: IndexingMetadata
    created_at: UtcDateTime
    updated_at: UtcDateTime
    version: Annotated[int, Field(ge=1)]

    @field_validator("title", "namespace")
    @classmethod
    def validate_non_blank_fields(cls, value: str, info: ValidationInfo) -> str:
        return require_non_blank(value, info.field_name or "field")

    @model_validator(mode="after")
    def validate_record(self) -> Self:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not precede created_at")
        core_types = {item.value for item in CoreRecordType}
        if self.record_type not in core_types and self.profile_type is None:
            raise ValueError("extension record types require profile_type")
        linked_ids = set(self.lifecycle.supersedes) | set(self.lifecycle.superseded_by)
        if self.record_id in linked_ids:
            raise ValueError("a record must not supersede itself")
        return self


class SourceRecord(VersionedContract):
    """Durable source metadata from PRD 13.2 and MEM-FR-019 through 028."""

    source_id: SourceId
    project_id: StableIdentifier
    path_or_uri: NonEmptyString
    path_pattern: NonEmptyString | None
    source_kind: NonEmptyString
    format: NonEmptyString
    canonicality: NonEmptyString
    content_role: SourceRole
    authority_tier: AuthorityTier
    trust_class: TrustClass
    sensitivity: Sensitivity
    namespace: NonEmptyString
    scope: ScopeReference
    profile_id: NonEmptyString
    ingestion_adapter: NonEmptyString
    chunking_profile: NonEmptyString
    schema_ref: NonEmptyString | None
    refresh_mode: NonEmptyString
    retention_policy: NonEmptyString
    owner: NonEmptyString
    write_policy: NonEmptyString
    include_flag: bool
    notes: str | None
    content_sha256: Sha256 | None
    locator: dict[str, JsonValue]
    git_commit: NonEmptyString | None
    git_blob_sha: NonEmptyString | None
    working_tree_state: NonEmptyString | None
    origin_uri: NonEmptyString | None
    retrieved_at: UtcDateTime | None
    # PRD 13.3 requires available licensing or access metadata but does not name
    # its SourceRecord field. These explicit maps preserve that information.
    licensing_metadata: dict[str, JsonValue]
    access_metadata: dict[str, JsonValue]
    generated_from: tuple[SourceId, ...]

    @model_validator(mode="after")
    def validate_source_kind_requirements(self) -> Self:
        if self.include_flag and self.content_sha256 is None:
            raise ValueError("included durable sources require content_sha256")
        if self.include_flag and self.sensitivity is Sensitivity.SECRET_PROHIBITED:
            raise ValueError("secret-prohibited sources must remain excluded")

        repository_kinds = {"git_file", "repository", "repository_file"}
        if self.include_flag and self.source_kind in repository_kinds:
            if not self.locator:
                raise ValueError("repository sources require locator metadata")
            if not any((self.git_commit, self.git_blob_sha, self.working_tree_state)):
                raise ValueError("repository sources require Git revision or working-tree state")

        external_kinds = {"external", "external_uri", "web", "web_page"}
        if (
            self.include_flag
            and self.source_kind in external_kinds
            and (self.origin_uri is None or self.retrieved_at is None)
        ):
            raise ValueError("external sources require origin_uri and retrieved_at")

        if self.content_role is SourceRole.GENERATED:
            if not self.generated_from:
                raise ValueError("generated sources must link to canonical inputs")
            if self.canonicality.casefold() in {"canonical", "authoritative"}:
                raise ValueError("generated sources must not claim canonical authority")
        if len(self.generated_from) != len(set(self.generated_from)):
            raise ValueError("generated_from must not contain duplicates")
        return self


class RelationSource(ContractModel):
    source_id: SourceId
    locator: dict[str, JsonValue]

    @model_validator(mode="after")
    def validate_locator(self) -> Self:
        if not self.locator:
            raise ValueError("relation source requires a locator")
        return self


class RelationValidation(ContractModel):
    state: NonEmptyString
    confidence: UnitScore | None


class TemporalMetadata(ContractModel):
    valid_from: UtcDateTime
    valid_to: UtcDateTime | None

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("temporal.valid_to must not precede valid_from")
        return self


class RelationLifecycle(ContractModel):
    status: RecordStatus


class RelationRecord(VersionedContract):
    relation_id: RelationId
    project_id: StableIdentifier
    relation_type: RelationTypeName
    source_record_id: MemoryRecordId
    target_record_id: MemoryRecordId
    source: RelationSource
    validation: RelationValidation
    temporal: TemporalMetadata
    lifecycle: RelationLifecycle


class RequesterIdentity(ContractModel):
    principal_id: StableIdentifier
    agent_type: StableIdentifier
    run_id: StableIdentifier


class RequestedTarget(ContractModel):
    path: NonEmptyString

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return require_non_blank(value, "requested_target.path")


class ProposalPayload(ContractModel):
    title: NonEmptyString
    content: JsonValue

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        require_non_blank(self.title, "proposal.title")
        if self.content is None or isinstance(self.content, str) and not self.content.strip():
            raise ValueError("proposal.content must not be empty")
        return self


class EvidenceReference(ContractModel):
    record_id: MemoryRecordId | None = None
    source_id: SourceId | None = None

    @model_validator(mode="after")
    def validate_exactly_one_reference(self) -> Self:
        if (self.record_id is None) == (self.source_id is None):
            raise ValueError("evidence must identify exactly one record_id or source_id")
        return self


class PolicyResult(ContractModel):
    action: PolicyAction
    policy_id: NonEmptyString
    reasons: Annotated[tuple[NonEmptyString, ...], Field(min_length=1)]


class WriteProposal(VersionedContract):
    proposal_id: ProposalId
    idempotency_key: NonEmptyString
    project_id: StableIdentifier
    requester: RequesterIdentity
    requested_record_type: RecordTypeName
    requested_scope: ScopeReference
    requested_target: RequestedTarget
    proposal: ProposalPayload
    evidence: Annotated[tuple[EvidenceReference, ...], Field(min_length=1)]
    trust_class: TrustClass
    sensitivity: Sensitivity
    policy_result: PolicyResult
    status: RecordStatus
    created_at: UtcDateTime

    @model_validator(mode="after")
    def validate_policy_state(self) -> Self:
        require_non_blank(self.idempotency_key, "idempotency_key")
        if self.sensitivity is Sensitivity.SECRET_PROHIBITED:
            raise ValueError("secret-prohibited content must not be proposed for durable memory")
        expected_status = {
            PolicyAction.REJECT: RecordStatus.REJECTED,
            PolicyAction.STAGE_FOR_REVIEW: RecordStatus.STAGED,
        }.get(self.policy_result.action)
        if expected_status is not None and self.status is not expected_status:
            raise ValueError(
                f"policy action {self.policy_result.action.value} requires status "
                f"{expected_status.value}"
            )
        return self


class RetrievalSource(ContractModel):
    source_id: SourceId | None = None
    path: NonEmptyString | None = None
    origin_uri: NonEmptyString | None = None
    git_commit: NonEmptyString | None = None
    content_sha256: Sha256 | None = None
    locator: dict[str, JsonValue]

    @model_validator(mode="after")
    def validate_source_anchor(self) -> Self:
        if self.source_id is None and self.path is None and self.origin_uri is None:
            raise ValueError("retrieval source must identify source_id, path, or origin_uri")
        if not self.locator:
            raise ValueError("retrieval source must include a source locator")
        return self


class RetrievalAuthority(ContractModel):
    tier: AuthorityTier
    trust_class: TrustClass


class RetrievalLifecycle(ContractModel):
    status: RecordStatus


class RetrievalScores(ContractModel):
    exact: UnitScore
    lexical: UnitScore
    semantic: UnitScore
    graph: UnitScore
    authority_boost: float
    final: UnitScore
    temporal: UnitScore | None = None
    trust: UnitScore | None = None
    freshness: UnitScore | None = None
    duplicate_penalty: NonNegativeScore | None = None
    superseded_penalty: NonNegativeScore | None = None
    scope_distance_penalty: NonNegativeScore | None = None
    unverified_penalty: NonNegativeScore | None = None


class RetrievedRecord(ContractModel):
    record_id: MemoryRecordId
    record_type: RecordTypeName
    title: NonEmptyString
    content: NonEmptyString
    source: RetrievalSource
    authority: RetrievalAuthority
    lifecycle: RetrievalLifecycle
    scores: RetrievalScores
    selection_reason: Annotated[tuple[NonEmptyString, ...], Field(min_length=1)]


class RetrievalFilters(ContractModel):
    project_scope: bool
    permission: bool
    current_only: bool
    trust_minimum: TrustClass | None
    namespaces: tuple[NonEmptyString, ...] = ()
    status_filters: tuple[RecordStatus, ...] = ()
    time_constraints: dict[str, JsonValue] = Field(default_factory=dict)
    omitted_result_count: Annotated[int, Field(ge=0)] = 0


class RetrievalResult(VersionedContract):
    request_id: RequestId
    project_id: StableIdentifier
    query: NonEmptyString
    mode: RetrievalMode
    evidence_state: EvidenceState
    results: tuple[RetrievedRecord, ...]
    filters_applied: RetrievalFilters
    trace_id: TraceId

    @model_validator(mode="after")
    def validate_evidence_state(self) -> Self:
        require_non_blank(self.query, "query")
        if self.evidence_state is EvidenceState.SUFFICIENT and not self.results:
            raise ValueError("sufficient evidence_state requires at least one result")
        return self


class ProfileCompatibility(ContractModel):
    sys4ai_memory_api: NonEmptyString
    required_capabilities: tuple[NonEmptyString, ...]


class ProfileRecordType(ContractModel):
    name: RecordTypeName
    schema_ref: NonEmptyString
    semantic_fields: tuple[FieldPath, ...] = ()
    exact_fields: tuple[FieldPath, ...] = ()


class ProfileSourceAdapter(ContractModel):
    id: StableIdentifier
    formats: Annotated[tuple[NonEmptyString, ...], Field(min_length=1)]


class ProfileReference(ContractModel):
    ref: NonEmptyString


class MemoryProfile(VersionedContract):
    profile_id: StableIdentifier
    version: SemanticVersion
    extends: tuple[NonEmptyString, ...]
    compatibility: ProfileCompatibility
    record_types: tuple[ProfileRecordType, ...]
    relations: tuple[RelationTypeName, ...]
    source_adapters: tuple[ProfileSourceAdapter, ...]
    write_policies: tuple[ProfileReference, ...]
    retrieval_strategies: tuple[ProfileReference, ...]
    evaluations: tuple[ProfileReference, ...]

    @model_validator(mode="after")
    def validate_unique_definitions(self) -> Self:
        names = tuple(item.name for item in self.record_types)
        adapter_ids = tuple(item.id for item in self.source_adapters)
        collections = {
            "record type names": names,
            "relations": self.relations,
            "source adapter IDs": adapter_ids,
            "required capabilities": self.compatibility.required_capabilities,
        }
        for label, values in collections.items():
            if len(values) != len(set(values)):
                raise ValueError(f"profile {label} must not contain duplicates")
        return self


class RebuildSourceRevision(ContractModel):
    source_id: SourceId
    revision: NonEmptyString
    content_sha256: Sha256


class RebuildReceipt(VersionedContract):
    """Rebuild receipt fields required by MEM-FR-124."""

    receipt_id: RebuildReceiptId
    project_id: StableIdentifier
    source_revisions: tuple[RebuildSourceRevision, ...]
    configuration_fingerprint: Sha256
    profile_versions: Annotated[dict[StableIdentifier, SemanticVersion], Field(min_length=1)]
    adapter_versions: Annotated[dict[StableIdentifier, NonEmptyString], Field(min_length=1)]
    provider_version: NonEmptyString
    model_identifiers: tuple[NonEmptyString, ...]
    started_at: UtcDateTime
    completed_at: UtcDateTime
    warnings: tuple[NonEmptyString, ...]
    # MEM-FR-124 requires an outcome but does not enumerate allowed values.
    outcome: NonEmptyString
    trace_id: TraceId

    @model_validator(mode="after")
    def validate_receipt(self) -> Self:
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        source_ids = tuple(item.source_id for item in self.source_revisions)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source_revisions must not contain duplicate source IDs")
        return self
