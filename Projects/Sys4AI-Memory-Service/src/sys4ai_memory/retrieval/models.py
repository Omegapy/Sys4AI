"""Provider-neutral query planning and ranking models for evidence recall."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    AuthorityTier,
    EvidenceState,
    RecordStatus,
    RelationRecord,
    RetrievalMode,
    ScopeReference,
    TrustClass,
)
from sys4ai_memory.contracts._base import (
    ContractModel,
    MemoryRecordId,
    NonEmptyString,
    RequestId,
    StableIdentifier,
    TraceId,
    UtcDateTime,
    VersionedContract,
    require_non_blank,
)
from sys4ai_memory.contracts.models import RequesterIdentity, RetrievedRecord


class QueryIntent(StrEnum):
    """The eleven query intents required by PRD section 21.2."""

    EXACT_LOOKUP = "exact_lookup"
    SOURCE_LOOKUP = "source_lookup"
    REQUIREMENT_LOOKUP = "requirement_lookup"
    DECISION_LOOKUP = "decision_lookup"
    PROCEDURE_LOOKUP = "procedure_lookup"
    SEMANTIC_QUESTION = "semantic_question"
    DEPENDENCY_QUERY = "dependency_query"
    PROVENANCE_QUERY = "provenance_query"
    HISTORICAL_QUERY = "historical_query"
    SIMILAR_CASE_QUERY = "similar_case_query"
    CURRENT_STATE_QUERY = "current_state_query"


class ContentOrigin(StrEnum):
    """Inspectable content lineage used in every selected-result explanation."""

    DIRECT_SOURCE_TEXT = "direct_source_text"
    DETERMINISTIC_EXTRACTION = "deterministic_extraction"
    MODEL_EXTRACTION = "model_extraction"
    GENERATED_SUMMARY = "generated_summary"


class ContextBudget(ContractModel):
    """Hard context limits applied after filtering, ranking, and deduplication."""

    max_records: Annotated[int, Field(ge=1, le=100)] = 10
    max_characters: Annotated[int, Field(ge=1, le=1_000_000)] = 40_000
    max_tokens: Annotated[int, Field(ge=1, le=250_000)] = 10_000
    # The current provider-neutral RecallRequest exposes relations as a
    # one-hop inclusion flag. Reject deeper budgets until that contract can
    # represent and enforce them rather than silently exceeding the limit.
    max_relation_depth: Annotated[int, Field(ge=0, le=1)] = 1
    minimum_source_diversity: Annotated[int, Field(ge=1, le=100)] = 1

    @model_validator(mode="after")
    def validate_diversity(self) -> Self:
        if self.minimum_source_diversity > self.max_records:
            raise ValueError("minimum_source_diversity cannot exceed max_records")
        return self


class RankingWeights(ContractModel):
    """Visible initial ranking configuration from PRD section 21.3."""

    exact: Annotated[float, Field(ge=0.0)] = 1.00
    lexical: Annotated[float, Field(ge=0.0)] = 0.45
    semantic: Annotated[float, Field(ge=0.0)] = 0.55
    graph: Annotated[float, Field(ge=0.0)] = 0.35
    temporal: Annotated[float, Field(ge=0.0)] = 0.30
    authority: Annotated[float, Field(ge=0.0)] = 0.15
    trust: Annotated[float, Field(ge=0.0)] = 0.15
    freshness: Annotated[float, Field(ge=0.0)] = 0.10
    duplicate_penalty: Annotated[float, Field(ge=0.0, le=1.0)] = 0.20
    superseded_penalty: Annotated[float, Field(ge=0.0, le=1.0)] = 0.35
    scope_distance_penalty: Annotated[float, Field(ge=0.0, le=1.0)] = 0.10
    unverified_penalty: Annotated[float, Field(ge=0.0, le=1.0)] = 0.20
    exact_identifier_floor: Annotated[float, Field(ge=0.0, le=1.0)] = 0.99
    non_exact_identifier_ceiling: Annotated[float, Field(ge=0.0, le=1.0)] = 0.98
    minimum_final_score: Annotated[float, Field(ge=0.0, le=1.0)] = 0.05
    freshness_horizon_days: Annotated[int, Field(ge=1)] = 365

    @model_validator(mode="after")
    def validate_exact_dominance(self) -> Self:
        if self.exact_identifier_floor <= self.non_exact_identifier_ceiling:
            raise ValueError("exact_identifier_floor must exceed non_exact_identifier_ceiling")
        if not any(
            value > 0.0
            for value in (
                self.exact,
                self.lexical,
                self.semantic,
                self.graph,
                self.temporal,
            )
        ):
            raise ValueError("at least one retrieval-channel weight must be positive")
        return self


class RecallQuery(ContractModel):
    """Complete read request accepted by the provider-neutral retrieval engine."""

    request_id: RequestId
    trace_id: TraceId
    project_id: StableIdentifier
    dataset_id: StableIdentifier
    requester: RequesterIdentity
    scope: ScopeReference
    query: NonEmptyString
    mode: RetrievalMode | None = None
    intent: QueryIntent | None = None
    requested_project_ids: tuple[StableIdentifier, ...] = ()
    explicit_cross_project: bool = False
    namespaces: tuple[NonEmptyString, ...] = ()
    status_filters: tuple[RecordStatus, ...] = ()
    trust_filters: tuple[TrustClass, ...] = ()
    trust_minimum: TrustClass | None = None
    authority_filters: tuple[AuthorityTier, ...] = ()
    at_time: UtcDateTime | None = None
    current_only: bool | None = None
    case_sensitive: bool = False
    exact_field: NonEmptyString | None = None
    lexical_field: NonEmptyString | None = None
    lexical_phrase: bool = False
    lexical_prefix: bool = False
    relation_types: tuple[NonEmptyString, ...] = ()
    authorization_target: NonEmptyString | None = None
    authorization_operation: Literal["memory.recall", "memory.graph"] = "memory.recall"
    retrieval_only: bool = True
    budget: ContextBudget = Field(default_factory=ContextBudget)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        return require_non_blank(value, "query")

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        project_scopes = {
            item.scope_id for item in _walk_scopes(self.scope) if item.level.value == "project"
        }
        if self.project_id not in project_scopes:
            raise ValueError("scope must identify the recall project")
        requested_projects = self.effective_project_ids
        if len(requested_projects) != len(set(requested_projects)):
            raise ValueError("requested_project_ids must not contain duplicates")
        if self.project_id not in requested_projects:
            raise ValueError("requested_project_ids must include project_id")
        for field_name, values in (
            ("namespaces", self.namespaces),
            ("status_filters", self.status_filters),
            ("trust_filters", self.trust_filters),
            ("authority_filters", self.authority_filters),
            ("relation_types", self.relation_types),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
        if self.lexical_phrase and self.lexical_prefix:
            raise ValueError("lexical_phrase and lexical_prefix are mutually exclusive")
        if self.at_time is not None and self.current_only is True:
            raise ValueError("at_time recall requires current_only=false or automatic routing")
        if not self.retrieval_only:
            raise ValueError("this subsystem provides retrieval-only evidence, not synthesis")
        governance_requested = any(is_governance_namespace(item) for item in self.namespaces)
        external_requested = any(is_external_namespace(item) for item in self.namespaces)
        if governance_requested and external_requested:
            raise ValueError(
                "governance and external-evidence namespaces require separate recall requests"
            )
        return self

    @property
    def effective_project_ids(self) -> tuple[str, ...]:
        return self.requested_project_ids or (self.project_id,)


class QueryPlan(ContractModel):
    """Deterministic and inspectable routing decision."""

    intent: QueryIntent
    intent_overridden: bool
    channels: tuple[RetrievalMode, ...]
    result_mode: RetrievalMode
    provider_mode: RetrievalMode | None
    current_only: bool
    governance_isolated: bool
    explanations: tuple[NonEmptyString, ...]

    @model_validator(mode="after")
    def validate_channels(self) -> Self:
        if not self.channels or len(self.channels) != len(set(self.channels)):
            raise ValueError("query plan channels must be non-empty and unique")
        if RetrievalMode.HYBRID in self.channels:
            raise ValueError("query plan channels must contain concrete channels")
        return self


class StructuredGraphPath(ContractModel):
    """One authorized typed-relation hop with its complete evidence metadata."""

    start_record_id: MemoryRecordId
    end_record_id: MemoryRecordId
    traversal_direction: Literal["forward", "reverse"]
    depth: Literal[1] = 1
    relation: RelationRecord

    @model_validator(mode="after")
    def validate_path(self) -> Self:
        expected = (
            (self.relation.source_record_id, self.relation.target_record_id)
            if self.traversal_direction == "forward"
            else (self.relation.target_record_id, self.relation.source_record_id)
        )
        if (self.start_record_id, self.end_record_id) != expected:
            raise ValueError("graph path direction does not match its relation endpoints")
        return self


class StructuredGraphResult(VersionedContract):
    """Bounded graph paths returned alongside the ordinary evidence bundle."""

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    api_version: Literal["1.0"] = API_VERSION
    request_id: RequestId
    project_id: StableIdentifier
    query_record_id: MemoryRecordId
    max_depth: Literal[1] = 1
    evidence_state: EvidenceState
    paths: tuple[StructuredGraphPath, ...]
    trace_id: TraceId

    @model_validator(mode="after")
    def validate_evidence_state(self) -> Self:
        if self.evidence_state is EvidenceState.SUFFICIENT and not self.paths:
            raise ValueError("sufficient graph evidence requires at least one path")
        if any(path.start_record_id != self.query_record_id for path in self.paths):
            raise ValueError("every graph path must start at the queried record")
        if any(path.relation.project_id != self.project_id for path in self.paths):
            raise ValueError("graph paths must remain inside the result project")
        return self


@dataclass(frozen=True, slots=True)
class RetrievalCandidate:
    """Internal candidate enriched with metadata needed for fail-closed filters."""

    record: RetrievedRecord
    namespace: str | None
    scope: ScopeReference | None
    valid_from: datetime | None
    valid_to: datetime | None
    updated_at: datetime | None
    verification: str | None
    content_origin: ContentOrigin
    instruction_like: bool
    canonical: bool | None
    relation_unverified: bool = False


@dataclass(frozen=True, slots=True)
class RankingContext:
    query: str
    intent: QueryIntent
    channels: tuple[RetrievalMode, ...]
    scope: ScopeReference
    current_only: bool
    historical: bool
    at_time: datetime | None
    now: datetime
    exact_identifier_query: bool


def is_governance_namespace(namespace: str) -> bool:
    normalized = namespace.casefold().strip("/")
    return normalized == "governance" or normalized.startswith("governance/")


def is_external_namespace(namespace: str) -> bool:
    normalized = namespace.casefold().strip("/")
    return (
        normalized in {"external", "evidence/external"}
        or normalized.startswith("external/")
        or normalized.startswith("evidence/external/")
    )


def _walk_scopes(scope: ScopeReference) -> tuple[ScopeReference, ...]:
    pending = [scope]
    ordered: list[ScopeReference] = []
    seen: set[tuple[str, str]] = set()
    while pending:
        item = pending.pop(0)
        identity = (item.level.value, item.scope_id)
        if identity in seen:
            continue
        seen.add(identity)
        ordered.append(item)
        pending.extend(item.parent_scopes)
    return tuple(ordered)
