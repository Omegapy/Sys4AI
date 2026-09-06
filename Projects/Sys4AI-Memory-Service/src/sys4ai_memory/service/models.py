"""Service-local models for policy evaluation and optional operation ports."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from sys4ai_memory.authorization import AuthorizationDecision
from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    AuthorityTier,
    MemoryRecord,
    RecordStatus,
    RelationRecord,
    RetrievalResult,
    ScopeReference,
    Sensitivity,
    SourceRecord,
    TrustClass,
)
from sys4ai_memory.contracts._base import (
    ApiVersion,
    MemoryRecordId,
    NonEmptyString,
    ProposalId,
    RequestId,
    SchemaVersion,
    Sha256,
    SourceId,
    StableIdentifier,
    TraceId,
    UtcDateTime,
)
from sys4ai_memory.contracts.models import (
    EvidenceReference,
    ProposalPayload,
    RequestedTarget,
    RequesterIdentity,
    RetrievalSource,
)
from sys4ai_memory.observability.models import RecallTrace
from sys4ai_memory.policies import (
    ConsolidationInput,
    EpisodicEntry,
    FeedbackRecord,
    SessionEntry,
    WriteTargetClass,
)
from sys4ai_memory.providers import PolicyEnvelope, ProviderContext


class ServiceModel(BaseModel):
    """Closed immutable base for data that crosses an internal service port."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class ProposalSubmission(ServiceModel):
    """Typed proposal input before the service computes its policy result."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    proposal_id: ProposalId
    project_id: NonEmptyString
    requester: RequesterIdentity
    requested_record_type: NonEmptyString
    requested_scope: ScopeReference
    requested_target: RequestedTarget
    proposal: ProposalPayload
    evidence: Annotated[tuple[EvidenceReference, ...], Field(min_length=1)]
    trust_class: TrustClass
    sensitivity: Sensitivity
    authority_tier: AuthorityTier
    target_class: WriteTargetClass
    requested_status: RecordStatus = RecordStatus.PROPOSED
    created_at: UtcDateTime
    external_source: bool = False
    automatic_feedback: bool = False
    base_content: str | None = None
    session_entry: SessionEntry | None = None
    episodic_entry: EpisodicEntry | None = None
    records: tuple[MemoryRecord, ...] = ()
    relations: tuple[RelationRecord, ...] = ()
    sources: tuple[SourceRecord, ...] = ()

    @model_validator(mode="after")
    def validate_action_material(self) -> Self:
        if self.target_class is WriteTargetClass.SESSION and self.session_entry is None:
            raise ValueError("session proposal requires a typed session_entry")
        if self.target_class is WriteTargetClass.EPISODIC and self.episodic_entry is None:
            raise ValueError("episodic proposal requires a typed episodic_entry")
        if self.records and any(record.project_id != self.project_id for record in self.records):
            raise ValueError("proposal records must match the proposal project")
        if self.sources and any(source.project_id != self.project_id for source in self.sources):
            raise ValueError("proposal sources must match the proposal project")
        if self.relations and any(
            relation.project_id != self.project_id for relation in self.relations
        ):
            raise ValueError("proposal relations must match the proposal project")
        return self


class ImprovementSubmission(ServiceModel):
    """Explicit, auditable improvement data carried inside ``ImproveInput``."""

    profile_id: NonEmptyString
    action: Literal["reweight", "consolidate"] = "reweight"
    feedback: Annotated[tuple[FeedbackRecord, ...], Field(min_length=1)]
    authority: AuthorityTier
    trust: TrustClass
    receipt_id: NonEmptyString | None = None
    consolidation_record_id: NonEmptyString | None = None
    consolidation_inputs: tuple[ConsolidationInput, ...] = ()

    @model_validator(mode="after")
    def validate_action(self) -> Self:
        if self.action == "reweight" and self.receipt_id is None:
            raise ValueError("reweight requires receipt_id")
        if self.action == "consolidate" and (
            self.consolidation_record_id is None or not self.consolidation_inputs
        ):
            raise ValueError("consolidate requires a record ID and consolidation inputs")
        return self


class SynthesisCitation(ServiceModel):
    """A claim citation bound to one record in the authorized evidence bundle."""

    record_id: MemoryRecordId
    source_id: SourceId | None = None
    source: RetrievalSource

    @model_validator(mode="after")
    def validate_source_identity(self) -> Self:
        if self.source.source_id != self.source_id:
            raise ValueError("synthesis citation source ID does not match its anchor")
        return self


class SynthesizedClaim(ServiceModel):
    """One material claim with at least one source anchor."""

    claim: NonEmptyString
    citations: Annotated[tuple[SynthesisCitation, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_claim(self) -> Self:
        if not self.claim.strip():
            raise ValueError("synthesized claim must not be blank")
        identities = tuple(
            (item.record_id, item.source.to_stable_json()) for item in self.citations
        )
        if len(identities) != len(set(identities)):
            raise ValueError("synthesis claim citations must be unique")
        return self


class EvidenceSynthesisRequest(ServiceModel):
    """Explicit opt-in synthesis input containing only authorized evidence."""

    request_id: RequestId
    project_id: StableIdentifier
    requester: RequesterIdentity
    llm_profile_id: NonEmptyString
    evidence: RetrievalResult
    trace_id: TraceId

    @model_validator(mode="after")
    def validate_boundary(self) -> Self:
        if (
            self.evidence.request_id != self.request_id
            or self.evidence.project_id != self.project_id
            or self.evidence.trace_id != self.trace_id
        ):
            raise ValueError("synthesis request does not match its evidence boundary")
        return self


class EvidenceSynthesisResult(ServiceModel):
    """Provider-neutral answer whose declared material claims are all cited."""

    request_id: RequestId
    project_id: StableIdentifier
    provider_name: NonEmptyString
    model_profile_id: NonEmptyString
    answer: NonEmptyString
    claims: Annotated[tuple[SynthesizedClaim, ...], Field(min_length=1)]
    trace_id: TraceId
    material_claims_cited: Literal[True] = True

    @model_validator(mode="after")
    def validate_answer(self) -> Self:
        if not self.answer.strip():
            raise ValueError("synthesized answer must not be blank")
        return self


class CanonicalLifecycleChangeRequest(ServiceModel):
    """A governed project-change request that never edits a canonical record."""

    record_id: NonEmptyString
    replacement_record_id: NonEmptyString
    reason: NonEmptyString
    requires_governed_project_workflow: Literal[True] = True
    canonical_write_performed: Literal[False] = False
    synchronize_after_accepted_write: Literal[True] = True


class PortableExportCall(ServiceModel):
    """Narrow provider-neutral export-port request."""

    context: ProviderContext
    request_id: RequestId
    idempotency_key: NonEmptyString
    output_path: NonEmptyString
    format: Literal["sys4ai", "cogx"]
    include_sensitive: bool
    age_recipient: str | None = None
    authorization: PolicyEnvelope


class PortableImportCall(ServiceModel):
    """Narrow provider-neutral import-port request."""

    context: ProviderContext
    request_id: RequestId
    idempotency_key: NonEmptyString
    package_path: NonEmptyString
    activate: bool
    expected_sha256: Sha256 | None
    accepted_impact_digest: Sha256 | None
    authorization: PolicyEnvelope | None = None
    activation_decision: AuthorizationDecision | None = None

    @model_validator(mode="after")
    def validate_activation_material(self) -> Self:
        if self.activate and (self.authorization is None or self.activation_decision is None):
            raise ValueError("import activation requires service and provider authorization")
        if not self.activate and (
            self.authorization is not None or self.activation_decision is not None
        ):
            raise ValueError("import preview must not carry activation authorization")
        return self


class PortResult(ServiceModel):
    """Validated JSON result returned by an optional rebuild or exchange port."""

    result: dict[str, JsonValue]
    target_ids: tuple[str, ...] = ()
    impact_digest: Sha256 | None = None
    recall_trace: RecallTrace | None = None
