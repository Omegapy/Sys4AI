"""Authorized multi-channel retrieval and bounded evidence assembly."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import JsonValue

from sys4ai_memory.authorization import (
    AuthorizationDecision,
    AuthorizationRequest,
)
from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    AuthorityTier,
    EvidenceState,
    MemoryScope,
    Permission,
    RecordStatus,
    RelationRecord,
    RetrievalMode,
    RetrievalResult,
    ScopeReference,
    TrustClass,
)
from sys4ai_memory.contracts.models import (
    LifecycleMetadata,
    MemoryRecord,
    RetrievalAuthority,
    RetrievalFilters,
    RetrievalLifecycle,
    RetrievalScores,
    RetrievalSource,
    RetrievedRecord,
)
from sys4ai_memory.observability.models import (
    RecallChannelCount,
    RecallFilterTrace,
    RecallRankingTrace,
    RecallTrace,
)
from sys4ai_memory.providers import (
    ProviderContext,
    ProviderRecallCandidate,
    ProviderRecallResult,
    RecallRequest,
)
from sys4ai_memory.security import classify_external_content
from sys4ai_memory.util import ensure_utc, utc_now

from .models import (
    ContentOrigin,
    QueryIntent,
    QueryPlan,
    RankingContext,
    RankingWeights,
    RecallQuery,
    RetrievalCandidate,
    StructuredGraphPath,
    StructuredGraphResult,
    is_external_namespace,
    is_governance_namespace,
)
from .planner import QueryPlanner, looks_like_exact_identifier
from .ranker import Ranker, WeightedRanker, trust_score_for

_CURRENT_STATUSES = frozenset({RecordStatus.ACTIVE, RecordStatus.APPROVED})
_EXTERNAL_TRUST = frozenset(
    {
        TrustClass.EXTERNALLY_AUTHENTICATED,
        TrustClass.EXTERNAL_UNVERIFIED,
        TrustClass.USER_SUPPLIED,
        TrustClass.UNTRUSTED,
    }
)
_GENERATED_TRUST = frozenset({TrustClass.AGENT_GENERATED, TrustClass.MODEL_EXTRACTED})
_TOKEN = re.compile(r"\S+")


class ExactRetrievalBackend(Protocol):
    """The read-only ExactIndex methods consumed by evidence recall."""

    def query_exact(
        self,
        *,
        project_id: str,
        query: str,
        case_sensitive: bool = True,
        field: str | None = None,
        current_only: bool = True,
        limit: int = 20,
    ) -> tuple[RetrievedRecord, ...]: ...

    def query_lexical(
        self,
        *,
        project_id: str,
        query: str,
        phrase: bool = False,
        prefix: bool = False,
        field: str | None = None,
        current_only: bool = True,
        limit: int = 20,
    ) -> tuple[RetrievedRecord, ...]: ...


@runtime_checkable
class ExactRecordResolver(Protocol):
    """Hydrate exact hits so security filters can verify full record metadata."""

    def resolve_record(
        self,
        *,
        project_id: str,
        record_id: str,
        source_revision: str,
        source_path: str,
    ) -> MemoryRecord | None: ...


@runtime_checkable
class IndexedLifecycleResolver(Protocol):
    """Resolve the deterministic lifecycle status used to gate provider hits."""

    def resolve_lifecycle(
        self,
        *,
        project_id: str,
        record_id: str,
    ) -> LifecycleMetadata | None: ...


class RecallProvider(Protocol):
    """Provider-neutral read slice implemented by every MemoryProvider."""

    async def recall(self, request: RecallRequest) -> ProviderRecallResult: ...


class RecallAuthorizer(Protocol):
    """Fresh canonical authorization gate used before retrieval and assembly."""

    def require(
        self,
        request: AuthorizationRequest,
        *,
        now: datetime | None = None,
    ) -> AuthorizationDecision: ...


class RetrievalIntegrityError(RuntimeError):
    """A backend returned data outside its declared provider-neutral boundary."""


class RetrievalEngine:
    """Combine deterministic and provider recall into one public evidence bundle."""

    def __init__(
        self,
        *,
        project_id: str,
        dataset_id: str,
        authorizer: RecallAuthorizer,
        exact_backend: ExactRetrievalBackend | None = None,
        exact_record_resolver: ExactRecordResolver | None = None,
        lifecycle_resolver: IndexedLifecycleResolver | None = None,
        provider: RecallProvider | None = None,
        planner: QueryPlanner | None = None,
        ranker: Ranker | None = None,
        ranking_weights: RankingWeights | None = None,
        candidate_limit: int = 100,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        if not project_id.strip() or not dataset_id.strip():
            raise ValueError("project_id and dataset_id must not be blank")
        if not 1 <= candidate_limit <= 100:
            raise ValueError("candidate_limit must be between 1 and 100")
        if ranker is not None and ranking_weights is not None:
            raise ValueError("provide ranker or ranking_weights, not both")
        self._project_id = project_id
        self._dataset_id = dataset_id
        self._authorizer = authorizer
        self._exact = exact_backend
        self._exact_resolver = exact_record_resolver
        if self._exact_resolver is None and isinstance(exact_backend, ExactRecordResolver):
            self._exact_resolver = exact_backend
        self._lifecycle_resolver = lifecycle_resolver
        if self._lifecycle_resolver is None and isinstance(
            exact_backend, IndexedLifecycleResolver
        ):
            self._lifecycle_resolver = exact_backend
        self._provider = provider
        self._planner = planner or QueryPlanner()
        self._ranker = ranker or WeightedRanker(ranking_weights)
        self._candidate_limit = candidate_limit
        self._clock = clock

    @property
    def ranker(self) -> Ranker:
        return self._ranker

    def plan(self, request: RecallQuery) -> QueryPlan:
        """Expose the deterministic plan without reading an index or provider."""

        return self._planner.plan(request)

    async def recall(self, request: RecallQuery) -> RetrievalResult:
        """Return the stable public retrieval result."""

        result, _trace = await self.recall_with_trace(request)
        return result

    async def recall_with_trace(
        self,
        request: RecallQuery,
    ) -> tuple[RetrievalResult, RecallTrace]:
        """Return a result plus actual channel/filter/ranking execution metadata."""

        result, trace, _relations = await self._recall_with_trace_and_relations(request)
        return result, trace

    async def graph_paths_with_trace(
        self,
        request: RecallQuery,
        *,
        start_record_id: str,
    ) -> tuple[StructuredGraphResult, RetrievalResult, RecallTrace]:
        """Return authorized one-hop typed paths plus their evidence bundle."""

        if request.mode is not RetrievalMode.GRAPH:
            raise ValueError("structured graph paths require graph retrieval mode")
        if request.authorization_operation != "memory.graph":
            raise ValueError("structured graph paths require memory.graph authorization")
        if request.query != start_record_id:
            raise ValueError("graph query text must equal the starting record ID")
        if request.budget.max_relation_depth != 1:
            raise ValueError("structured graph paths currently require one-hop depth")
        evidence, trace, relations = await self._recall_with_trace_and_relations(request)
        selected_ids = {item.record_id for item in evidence.results}
        paths: list[StructuredGraphPath] = []
        for relation in relations:
            if not self._relation_visible(relation, request, selected_ids):
                continue
            if relation.source_record_id == start_record_id:
                direction: Literal["forward", "reverse"] = "forward"
                end_record_id = relation.target_record_id
            elif relation.target_record_id == start_record_id:
                direction = "reverse"
                end_record_id = relation.source_record_id
            else:
                continue
            paths.append(
                StructuredGraphPath(
                    start_record_id=start_record_id,
                    end_record_id=end_record_id,
                    traversal_direction=direction,
                    relation=relation,
                )
            )
        paths.sort(key=lambda item: (item.relation.relation_type, item.relation.relation_id))
        result = StructuredGraphResult(
            request_id=request.request_id,
            project_id=request.project_id,
            query_record_id=start_record_id,
            evidence_state=(EvidenceState.SUFFICIENT if paths else EvidenceState.INSUFFICIENT),
            paths=tuple(paths),
            trace_id=request.trace_id,
        )
        return result, evidence, trace

    async def _recall_with_trace_and_relations(
        self,
        request: RecallQuery,
    ) -> tuple[RetrievalResult, RecallTrace, tuple[RelationRecord, ...]]:
        """Run recall while retaining provider relations for graph projection."""

        plan = self._planner.plan(request)
        authorization_request = self._authorization_request(request)
        self._authorizer.require(authorization_request, now=ensure_utc(self._clock()))
        self._require_engine_boundary(request)

        candidates: list[RetrievalCandidate] = []
        channel_counts = {channel: 0 for channel in plan.channels}
        duplicate_channel_count = 0
        provider_omitted = 0
        provider_relations: tuple[RelationRecord, ...] = ()
        limit = min(
            self._candidate_limit,
            max(20, request.budget.max_records * 4),
        )
        if self._exact is not None and RetrievalMode.EXACT in plan.channels:
            exact_results = self._exact.query_exact(
                project_id=request.project_id,
                query=request.query,
                case_sensitive=request.case_sensitive,
                field=request.exact_field,
                current_only=plan.current_only,
                limit=limit,
            )
            channel_counts[RetrievalMode.EXACT] = len(exact_results)
            candidates.extend(
                self._from_exact(item, request.project_id)
                for item in exact_results
            )
        if self._exact is not None and RetrievalMode.LEXICAL in plan.channels:
            lexical_results = self._exact.query_lexical(
                project_id=request.project_id,
                query=request.query,
                phrase=request.lexical_phrase,
                prefix=request.lexical_prefix,
                field=request.lexical_field,
                current_only=plan.current_only,
                limit=limit,
            )
            channel_counts[RetrievalMode.LEXICAL] = len(lexical_results)
            candidates.extend(
                self._from_exact(item, request.project_id)
                for item in lexical_results
            )
        if self._provider is not None and plan.provider_mode is not None:
            provider_result = await self._provider.recall(
                self._provider_request(request, plan.provider_mode, plan.current_only, limit)
            )
            self._validate_provider_result(provider_result, request)
            provider_relations = provider_result.relations
            for channel in plan.channels:
                channel_counts[channel] += sum(
                    getattr(candidate.scores, channel.value) > 0
                    for candidate in provider_result.candidates
                )
            candidates.extend(
                self._apply_indexed_lifecycle(
                    self._from_provider(
                        item,
                        relations=provider_result.relations,
                        graph_channel=RetrievalMode.GRAPH in plan.channels,
                    ),
                    project_id=request.project_id,
                )
                for item in provider_result.candidates
            )
            provider_omitted = provider_result.omitted_result_count

        # The canonical permission source is read again after backend work and
        # before any content is assembled into the agent-facing result.
        self._authorizer.require(authorization_request, now=ensure_utc(self._clock()))

        merged, duplicate_channel_count = _merge_record_channels(candidates)
        visible: list[RetrievalCandidate] = []
        filtered_count = 0
        for candidate in merged:
            if self._visible(candidate, request, plan.current_only):
                visible.append(self._label_candidate(candidate, request, plan.explanations))
            else:
                filtered_count += 1
        visibility_filtered = filtered_count

        now = ensure_utc(self._clock())
        rank_context = RankingContext(
            query=request.query,
            intent=plan.intent,
            channels=plan.channels,
            scope=request.scope,
            current_only=plan.current_only,
            historical=not plan.current_only or plan.intent is QueryIntent.HISTORICAL_QUERY,
            at_time=request.at_time,
            now=now,
            exact_identifier_query=looks_like_exact_identifier(request.query),
        )
        ranked = [self._ranker.score(candidate, rank_context) for candidate in visible]
        ranked = [
            candidate
            for candidate in ranked
            if candidate.record.scores.final >= self._ranker.weights.minimum_final_score
        ]
        score_filtered = len(visible) - len(ranked)
        filtered_count += score_filtered
        ranked.sort(key=_rank_key)
        deduplicated, overlap_count = _deduplicate_overlap(ranked)
        selected, budget_omitted = _apply_budget(deduplicated, request)
        source_count = len({_source_key(item.record) for item in selected})
        character_count = sum(len(value.record.content) for value in selected)
        token_count = sum(estimate_tokens(value.record.content) for value in selected)
        finalized = tuple(
            item.record.model_copy(
                update={
                    "selection_reason": tuple(
                        dict.fromkeys(
                            (
                                *item.record.selection_reason,
                                "retrieval_only:no_synthesis",
                                f"budget:records={len(selected)}/{request.budget.max_records}",
                                "budget:characters="
                                f"{character_count}/{request.budget.max_characters}",
                                f"budget:tokens={token_count}/{request.budget.max_tokens}",
                                f"budget:relation_depth={request.budget.max_relation_depth}",
                                "budget:source_diversity="
                                f"{source_count}/{request.budget.minimum_source_diversity}",
                            )
                        )
                    )
                }
            )
            for item in selected
        )
        omitted = (
            provider_omitted
            + duplicate_channel_count
            + filtered_count
            + overlap_count
            + budget_omitted
        )
        time_constraints: dict[str, JsonValue] = {}
        if request.at_time is not None:
            time_constraints["at_time"] = request.at_time.isoformat().replace("+00:00", "Z")
        result = RetrievalResult(
            schema_version=SCHEMA_VERSION,
            api_version=API_VERSION,
            request_id=request.request_id,
            project_id=request.project_id,
            query=request.query,
            mode=plan.result_mode,
            evidence_state=(EvidenceState.SUFFICIENT if finalized else EvidenceState.INSUFFICIENT),
            results=finalized,
            filters_applied=RetrievalFilters(
                project_scope=True,
                permission=True,
                current_only=plan.current_only,
                trust_minimum=request.trust_minimum,
                namespaces=request.namespaces,
                status_filters=request.status_filters,
                time_constraints=time_constraints,
                omitted_result_count=omitted,
            ),
            trace_id=request.trace_id,
        )
        trace = RecallTrace(
            selected_channels=plan.channels,
            candidates=tuple(
                RecallChannelCount(
                    channel=channel,
                    candidate_count=channel_counts[channel],
                )
                for channel in plan.channels
            ),
            filters=(
                RecallFilterTrace(
                    filter_code="scope_authority_lifecycle",
                    examined_count=len(merged),
                    excluded_count=visibility_filtered,
                    reason_codes=("not_visible",) if visibility_filtered else (),
                ),
                RecallFilterTrace(
                    filter_code="minimum_score",
                    examined_count=len(visible),
                    excluded_count=score_filtered,
                    reason_codes=("below_score_floor",) if score_filtered else (),
                ),
                RecallFilterTrace(
                    filter_code="overlap_deduplication",
                    examined_count=len(ranked),
                    excluded_count=overlap_count,
                    reason_codes=("overlapping_evidence",) if overlap_count else (),
                ),
                RecallFilterTrace(
                    filter_code="context_budget",
                    examined_count=len(deduplicated),
                    excluded_count=budget_omitted,
                    reason_codes=("budget_exceeded",) if budget_omitted else (),
                ),
            ),
            ranking_stages=(
                RecallRankingTrace(
                    stage_code="weighted_rank",
                    input_count=len(visible),
                    output_count=len(ranked),
                ),
                RecallRankingTrace(
                    stage_code="overlap_deduplication",
                    input_count=len(ranked),
                    output_count=len(deduplicated),
                ),
                RecallRankingTrace(
                    stage_code="context_budget",
                    input_count=len(deduplicated),
                    output_count=len(selected),
                ),
            ),
            returned_source_ids=tuple(
                sorted(
                    {
                        item.source.source_id
                        for item in finalized
                        if item.source.source_id is not None
                    }
                )
            ),
            omitted_result_count=omitted,
        )
        return result, trace, provider_relations

    def _authorization_request(self, request: RecallQuery) -> AuthorizationRequest:
        return AuthorizationRequest(
            principal_id=request.requester.principal_id,
            project_id=request.project_id,
            dataset_id=request.dataset_id,
            operation=request.authorization_operation,
            permission=Permission.READ,
            scope=request.scope,
            target_path=request.authorization_target,
            query_project_ids=request.effective_project_ids,
            explicit_cross_project=request.explicit_cross_project,
            trace_id=request.trace_id,
        )

    def _require_engine_boundary(self, request: RecallQuery) -> None:
        if request.project_id != self._project_id or request.dataset_id != self._dataset_id:
            raise RetrievalIntegrityError(
                "recall request does not match the configured project and dataset boundary"
            )
        if request.effective_project_ids != (self._project_id,):
            raise RetrievalIntegrityError(
                "one project retrieval engine cannot execute a multi-project recall"
            )

    def _provider_request(
        self,
        request: RecallQuery,
        mode: RetrievalMode,
        current_only: bool,
        limit: int,
    ) -> RecallRequest:
        return RecallRequest(
            context=ProviderContext(
                project_id=request.project_id,
                dataset_id=request.dataset_id,
                principal_id=request.requester.principal_id,
                scope=request.scope,
                trace_id=request.trace_id,
            ),
            request_id=request.request_id,
            query=request.query,
            mode=mode,
            namespaces=request.namespaces,
            status_filters=request.status_filters,
            current_only=current_only,
            at_time=request.at_time,
            include_relations=request.budget.max_relation_depth > 0,
            relation_types=request.relation_types,
            top_k=limit,
            case_sensitive=request.case_sensitive,
        )

    def _validate_provider_result(self, result: ProviderRecallResult, request: RecallQuery) -> None:
        if (
            result.project_id != request.project_id
            or result.dataset_id != request.dataset_id
            or result.request_id != request.request_id
            or result.trace_id != request.trace_id
        ):
            raise RetrievalIntegrityError(
                "provider recall result does not match the requested identity boundary"
            )
        if any(
            candidate.record.project_id != request.project_id for candidate in result.candidates
        ):
            raise RetrievalIntegrityError("provider returned a cross-project candidate")
        if any(relation.project_id != request.project_id for relation in result.relations):
            raise RetrievalIntegrityError("provider returned a cross-project relation")

    @staticmethod
    def _relation_visible(
        relation: RelationRecord,
        request: RecallQuery,
        selected_record_ids: set[str],
    ) -> bool:
        endpoints = {relation.source_record_id, relation.target_record_id}
        if not endpoints.issubset(selected_record_ids):
            return False
        if request.relation_types and relation.relation_type not in request.relation_types:
            return False
        if relation.lifecycle.status is RecordStatus.DELETED:
            return False
        if request.current_only and relation.lifecycle.status not in _CURRENT_STATUSES:
            return False
        if request.at_time is None:
            return True
        return relation.temporal.valid_from <= request.at_time and (
            relation.temporal.valid_to is None or request.at_time <= relation.temporal.valid_to
        )

    def _from_exact(self, record: RetrievedRecord, project_id: str) -> RetrievalCandidate:
        hydrated = self._resolve_exact_record(record, project_id)
        external = (
            _is_external_memory_record(hydrated)
            if hydrated is not None
            else _is_external_record(record)
        )
        instruction_like = (
            classify_external_content(
                record.content,
                authenticated=(record.authority.trust_class is TrustClass.EXTERNALLY_AUTHENTICATED),
            ).instruction_like
            if external
            else False
        )
        if hydrated is not None:
            return RetrievalCandidate(
                record=record,
                namespace=hydrated.namespace,
                scope=hydrated.scope,
                valid_from=hydrated.lifecycle.valid_from,
                valid_to=hydrated.lifecycle.valid_to,
                updated_at=hydrated.updated_at,
                verification=hydrated.epistemic.verification,
                content_origin=_content_origin(hydrated),
                instruction_like=instruction_like,
                canonical=hydrated.authority.canonical,
            )
        return RetrievalCandidate(
            record=record,
            namespace=None,
            scope=None,
            valid_from=None,
            valid_to=None,
            updated_at=None,
            verification="deterministic-index",
            content_origin=ContentOrigin.DETERMINISTIC_EXTRACTION,
            instruction_like=instruction_like,
            canonical=None,
        )

    def _resolve_exact_record(
        self, record: RetrievedRecord, project_id: str
    ) -> MemoryRecord | None:
        if self._exact_resolver is None:
            return None
        source_revision = record.source.locator.get("source_revision")
        source_path = record.source.path or record.source.origin_uri
        if not isinstance(source_revision, str) or source_path is None:
            return None
        hydrated = self._exact_resolver.resolve_record(
            project_id=project_id,
            record_id=record.record_id,
            source_revision=source_revision,
            source_path=source_path,
        )
        if hydrated is None:
            return None
        if (
            hydrated.project_id != project_id
            or hydrated.record_id != record.record_id
            or hydrated.content.exact != record.content
            or hydrated.authority.tier is not record.authority.tier
            or hydrated.authority.trust_class is not record.authority.trust_class
            or hydrated.lifecycle.status is not record.lifecycle.status
            or hydrated.source.source_id != record.source.source_id
            or hydrated.source.content_sha256 != record.source.content_sha256
        ):
            raise RetrievalIntegrityError(
                "exact record metadata does not match the retrieved stable record"
            )
        return hydrated

    @staticmethod
    def _from_provider(
        candidate: ProviderRecallCandidate,
        *,
        relations: tuple[RelationRecord, ...],
        graph_channel: bool,
    ) -> RetrievalCandidate:
        record = candidate.record
        origin = _content_origin(record)
        external = _is_external_memory_record(record)
        instruction_like = (
            classify_external_content(
                record.content.exact,
                authenticated=(record.authority.trust_class is TrustClass.EXTERNALLY_AUTHENTICATED),
            ).instruction_like
            if external
            else False
        )
        locator = dict(record.source.locator)
        if record.source.git_commit is not None:
            locator.setdefault("source_revision", f"git:{record.source.git_commit}")
        elif record.source.git_blob_sha is not None:
            locator.setdefault("source_revision", f"git-blob:{record.source.git_blob_sha}")
        elif record.source.working_tree_state is not None:
            locator.setdefault(
                "source_revision", f"working-tree:{record.source.working_tree_state}"
            )
        else:
            locator.setdefault("source_revision", f"sha256:{record.source.content_sha256}")
        graph_score = candidate.scores.graph
        relation_unverified = False
        relation_reasons: tuple[str, ...] = ()
        if graph_channel and graph_score > 0.0:
            graph_score, relation_unverified, relation_reasons = _relation_signal(
                record.record_id, graph_score, relations
            )
        retrieved = RetrievedRecord(
            record_id=record.record_id,
            record_type=record.record_type,
            title=record.title,
            content=record.content.exact,
            source=RetrievalSource(
                source_id=record.source.source_id,
                path=record.source.path,
                origin_uri=record.source.origin_uri,
                git_commit=record.source.git_commit,
                content_sha256=record.source.content_sha256,
                locator=locator,
            ),
            authority=RetrievalAuthority(
                tier=record.authority.tier,
                trust_class=record.authority.trust_class,
            ),
            lifecycle=RetrievalLifecycle(status=record.lifecycle.status),
            scores=RetrievalScores(
                exact=candidate.scores.exact,
                lexical=candidate.scores.lexical,
                semantic=candidate.scores.semantic,
                graph=graph_score,
                temporal=candidate.scores.temporal,
                authority_boost=0.0,
                trust=0.0,
                freshness=0.0,
                duplicate_penalty=0.0,
                superseded_penalty=0.0,
                scope_distance_penalty=0.0,
                unverified_penalty=0.0,
                final=candidate.scores.final,
            ),
            selection_reason=tuple(
                dict.fromkeys(
                    (
                        *(f"provider:{reason}" for reason in candidate.selection_reason),
                        *relation_reasons,
                    )
                )
            ),
        )
        return RetrievalCandidate(
            record=retrieved,
            namespace=record.namespace,
            scope=record.scope,
            valid_from=record.lifecycle.valid_from,
            valid_to=record.lifecycle.valid_to,
            updated_at=record.updated_at,
            verification=record.epistemic.verification,
            content_origin=origin,
            instruction_like=instruction_like,
            canonical=record.authority.canonical,
            relation_unverified=relation_unverified,
        )

    def _apply_indexed_lifecycle(
        self,
        candidate: RetrievalCandidate,
        *,
        project_id: str,
    ) -> RetrievalCandidate:
        if self._lifecycle_resolver is None:
            return candidate
        lifecycle = self._lifecycle_resolver.resolve_lifecycle(
            project_id=project_id,
            record_id=candidate.record.record_id,
        )
        if lifecycle is None:
            return candidate
        projected = candidate.record.model_copy(
            update={
                "lifecycle": RetrievalLifecycle(status=lifecycle.status),
                "selection_reason": (
                    *candidate.record.selection_reason,
                    "lifecycle_from_deterministic_index",
                ),
            }
        )
        return replace(
            candidate,
            record=projected,
            valid_from=lifecycle.valid_from,
            valid_to=lifecycle.valid_to,
        )

    def _visible(
        self,
        candidate: RetrievalCandidate,
        request: RecallQuery,
        current_only: bool,
    ) -> bool:
        record = candidate.record
        if request.namespaces and (
            candidate.namespace is None
            or not any(
                _namespace_matches(candidate.namespace, namespace)
                for namespace in request.namespaces
            )
        ):
            return False
        if request.status_filters:
            if record.lifecycle.status not in request.status_filters:
                return False
        elif current_only and record.lifecycle.status not in _CURRENT_STATUSES:
            return False
        if record.lifecycle.status is RecordStatus.DELETED:
            return False
        if request.trust_filters and record.authority.trust_class not in request.trust_filters:
            return False
        if request.trust_minimum is not None and trust_score_for(
            record.authority.trust_class
        ) < trust_score_for(request.trust_minimum):
            return False
        if request.authority_filters and record.authority.tier not in request.authority_filters:
            return False
        if not _scope_visible(candidate.scope, request.scope, request.project_id):
            return False
        if request.at_time is not None:
            if candidate.valid_from is None:
                return False
            if candidate.valid_from > request.at_time:
                return False
            if candidate.valid_to is not None and request.at_time > candidate.valid_to:
                return False
        if candidate.namespace is not None and is_governance_namespace(candidate.namespace):
            if record.authority.tier not in {
                AuthorityTier.SYSTEM_POLICY,
                AuthorityTier.SYS4AI_GOVERNANCE,
            }:
                return False
            if record.authority.trust_class in _EXTERNAL_TRUST | _GENERATED_TRUST:
                return False
            if candidate.canonical is not True:
                return False
            if candidate.content_origin in {
                ContentOrigin.MODEL_EXTRACTION,
                ContentOrigin.GENERATED_SUMMARY,
            }:
                return False
            if record.source.origin_uri is not None:
                return False
        return True

    @staticmethod
    def _label_candidate(
        candidate: RetrievalCandidate,
        request: RecallQuery,
        plan_reasons: tuple[str, ...],
    ) -> RetrievalCandidate:
        record = candidate.record
        external = _is_external_record(record) or (
            candidate.namespace is not None and is_external_namespace(candidate.namespace)
        )
        generated = record.authority.trust_class in _GENERATED_TRUST
        control = _is_control_candidate(candidate)
        lane = (
            "governance"
            if candidate.namespace is not None and is_governance_namespace(candidate.namespace)
            else "control_state"
            if control
            else "evidence_only"
            if external or generated
            else "project_knowledge"
        )
        reasons = [
            *record.selection_reason,
            *plan_reasons,
            f"content_origin={candidate.content_origin.value}",
            f"authority_lane={lane}",
            f"authority_tier={record.authority.tier.value}",
            f"trust_class={record.authority.trust_class.value}",
            "canonicality="
            + (
                "canonical"
                if candidate.canonical is True
                else "noncanonical"
                if candidate.canonical is False
                else "unresolved_from_exact_contract"
            ),
            f"filter:project={request.project_id}",
            f"filter:dataset={request.dataset_id}",
        ]
        if candidate.namespace is not None:
            reasons.append(f"filter:namespace={candidate.namespace}")
        if control:
            reasons.append("control_record=canonical_revalidation_required_before_action")
        if external:
            reasons.append("external_content=data_not_instruction")
        if candidate.instruction_like:
            reasons.append("instruction_like_external_text=data_only")
        return replace(
            candidate,
            record=record.model_copy(update={"selection_reason": tuple(dict.fromkeys(reasons))}),
        )


def estimate_tokens(content: str) -> int:
    """Return a deterministic conservative whitespace-token estimate."""

    return len(_TOKEN.findall(content))


def _content_origin(record: MemoryRecord) -> ContentOrigin:
    if "content.exact" in record.processing.model_extracted_fields:
        return ContentOrigin.MODEL_EXTRACTION
    parser = record.processing.parsed_by.casefold()
    if "summary" in parser or "generated" in parser:
        return ContentOrigin.GENERATED_SUMMARY
    if record.record_type in {"SourceArtifact", "SourceFragment"}:
        return ContentOrigin.DIRECT_SOURCE_TEXT
    return ContentOrigin.DETERMINISTIC_EXTRACTION


def _is_external_record(record: RetrievedRecord) -> bool:
    return (
        record.authority.tier in {AuthorityTier.EXTERNAL_EVIDENCE, AuthorityTier.UNTRUSTED_CONTENT}
        or record.authority.trust_class in _EXTERNAL_TRUST
        or record.source.origin_uri is not None
    )


def _is_external_memory_record(record: MemoryRecord) -> bool:
    return (
        record.authority.tier in {AuthorityTier.EXTERNAL_EVIDENCE, AuthorityTier.UNTRUSTED_CONTENT}
        or record.authority.trust_class in _EXTERNAL_TRUST
        or is_external_namespace(record.namespace)
        or record.source.origin_uri is not None
    )


def _is_control_candidate(candidate: RetrievalCandidate) -> bool:
    namespace = (candidate.namespace or "").casefold().strip("/")
    path = (candidate.record.source.path or "").casefold().lstrip("/")
    return (
        namespace == "control"
        or namespace.startswith("control/")
        or path.startswith("control/")
        or path.startswith("control_records/")
    )


def _relation_signal(
    record_id: str,
    graph_score: float,
    relations: tuple[RelationRecord, ...],
) -> tuple[float, bool, tuple[str, ...]]:
    connected = tuple(
        relation
        for relation in relations
        if record_id in {relation.source_record_id, relation.target_record_id}
    )
    if not connected:
        return (
            graph_score,
            True,
            ("graph_relation=provider_score_without_returned_relation_evidence",),
        )
    signals: list[tuple[float, RelationRecord]] = []
    for relation in connected:
        state = relation.validation.state.casefold().replace("_", "-")
        validated = state in {
            "approved",
            "deterministic",
            "human-approved",
            "schema-validated",
            "verified",
        }
        confidence = relation.validation.confidence
        effective_confidence = confidence if confidence is not None else 1.0 if validated else 0.25
        signals.append((effective_confidence, relation))
    best_confidence, best_relation = max(
        signals,
        key=lambda item: (item[0], item[1].relation_id),
    )
    adjusted = min(graph_score, best_confidence)
    reasons = (
        f"graph_relation={best_relation.relation_id}",
        f"graph_relation_validation={best_relation.validation.state}:{best_confidence:.3f}",
        f"graph_relation_source={best_relation.source.source_id}",
    )
    return adjusted, best_confidence < 0.75, reasons


def _scope_visible(
    candidate: ScopeReference | None,
    requested: ScopeReference,
    project_id: str,
) -> bool:
    if candidate is None:
        return requested.level is MemoryScope.PROJECT and requested.scope_id == project_id
    visible: set[tuple[object, str]] = set()
    pending = [requested]
    while pending:
        item = pending.pop()
        identity = (item.level, item.scope_id)
        if identity in visible:
            continue
        visible.add(identity)
        pending.extend(item.parent_scopes)
    return (candidate.level, candidate.scope_id) in visible


def _namespace_matches(candidate: str, requested: str) -> bool:
    candidate_value = candidate.casefold().strip("/")
    requested_value = requested.casefold().strip("/")
    return candidate_value == requested_value or candidate_value.startswith(requested_value + "/")


def _merge_record_channels(
    candidates: list[RetrievalCandidate],
) -> tuple[list[RetrievalCandidate], int]:
    merged: dict[tuple[str, str, str], RetrievalCandidate] = {}
    duplicate_count = 0
    for candidate in candidates:
        identity = _record_version_key(candidate.record)
        prior = merged.get(identity)
        if prior is None:
            merged[identity] = candidate
            continue
        duplicate_count += 1
        merged[identity] = _merge_same_record(prior, candidate)
    return list(merged.values()), duplicate_count


def _merge_same_record(left: RetrievalCandidate, right: RetrievalCandidate) -> RetrievalCandidate:
    if (
        left.record.content != right.record.content
        or left.record.authority != right.record.authority
        or left.record.lifecycle != right.record.lifecycle
    ):
        raise RetrievalIntegrityError(
            "retrieval channels returned conflicting data for one stable record ID"
        )
    for label, left_value, right_value in (
        ("namespace", left.namespace, right.namespace),
        ("scope", left.scope, right.scope),
        ("valid_from", left.valid_from, right.valid_from),
        ("valid_to", left.valid_to, right.valid_to),
    ):
        if left_value is not None and right_value is not None and left_value != right_value:
            raise RetrievalIntegrityError(
                f"retrieval channels returned conflicting {label} metadata"
            )
    left_source = left.record.source
    right_source = right.record.source
    for label, left_value, right_value in (
        ("source_id", left_source.source_id, right_source.source_id),
        ("path", left_source.path, right_source.path),
        ("origin_uri", left_source.origin_uri, right_source.origin_uri),
        ("git_commit", left_source.git_commit, right_source.git_commit),
        ("content_sha256", left_source.content_sha256, right_source.content_sha256),
    ):
        if left_value is not None and right_value is not None and left_value != right_value:
            raise RetrievalIntegrityError(
                f"retrieval channels returned conflicting {label} for one record ID"
            )
    primary, secondary = (right, left) if right.namespace is not None else (left, right)
    scores = RetrievalScores(
        exact=max(left.record.scores.exact, right.record.scores.exact),
        lexical=max(left.record.scores.lexical, right.record.scores.lexical),
        semantic=max(left.record.scores.semantic, right.record.scores.semantic),
        graph=max(left.record.scores.graph, right.record.scores.graph),
        temporal=max(left.record.scores.temporal or 0.0, right.record.scores.temporal or 0.0),
        authority_boost=0.0,
        trust=0.0,
        freshness=0.0,
        duplicate_penalty=0.0,
        superseded_penalty=0.0,
        scope_distance_penalty=0.0,
        unverified_penalty=0.0,
        final=max(left.record.scores.final, right.record.scores.final),
    )
    locator = dict(secondary.record.source.locator)
    locator.update(primary.record.source.locator)
    source = primary.record.source.model_copy(update={"locator": locator})
    record = primary.record.model_copy(
        update={
            "source": source,
            "scores": scores,
            "selection_reason": tuple(
                dict.fromkeys((*left.record.selection_reason, *right.record.selection_reason))
            ),
        }
    )
    return RetrievalCandidate(
        record=record,
        namespace=primary.namespace or secondary.namespace,
        scope=primary.scope or secondary.scope,
        valid_from=primary.valid_from or secondary.valid_from,
        valid_to=primary.valid_to or secondary.valid_to,
        updated_at=primary.updated_at or secondary.updated_at,
        verification=primary.verification or secondary.verification,
        content_origin=primary.content_origin,
        instruction_like=primary.instruction_like or secondary.instruction_like,
        canonical=(primary.canonical if primary.canonical is not None else secondary.canonical),
        relation_unverified=primary.relation_unverified or secondary.relation_unverified,
    )


def _rank_key(candidate: RetrievalCandidate) -> tuple[float, float, int, float, int, str]:
    scores = candidate.record.scores
    return (
        -scores.exact,
        -round(scores.final, 2),
        0 if candidate.canonical is True else 1 if candidate.canonical is None else 2,
        -scores.final,
        int(candidate.record.authority.tier.value[1:]),
        candidate.record.record_id,
    )


def _deduplicate_overlap(
    ranked: list[RetrievalCandidate],
) -> tuple[list[RetrievalCandidate], int]:
    selected: list[RetrievalCandidate] = []
    omitted = 0
    for candidate in ranked:
        if any(_overlaps(candidate.record, prior.record) for prior in selected):
            omitted += 1
            continue
        selected.append(candidate)
    return selected, omitted


def _overlaps(left: RetrievedRecord, right: RetrievedRecord) -> bool:
    if _source_key(left) != _source_key(right):
        return False
    if (
        left.source.content_sha256 is not None
        and right.source.content_sha256 is not None
        and left.source.content_sha256 != right.source.content_sha256
    ):
        return False
    if " ".join(left.content.casefold().split()) == " ".join(right.content.casefold().split()):
        return True
    left_range = _locator_range(left.source.locator)
    right_range = _locator_range(right.source.locator)
    if left_range is not None and right_range is not None and left_range[0] == right_range[0]:
        return max(left_range[1], right_range[1]) <= min(left_range[2], right_range[2])
    anchor_keys = ("json_pointer", "heading", "label", "symbol", "key")
    same_anchor = any(
        left.source.locator.get(key) is not None
        and left.source.locator.get(key) == right.source.locator.get(key)
        for key in anchor_keys
    )
    return same_anchor and _token_overlap(left.content, right.content) >= 0.8


def _locator_range(locator: dict[str, JsonValue]) -> tuple[str, int, int] | None:
    for start_key, end_key in (
        ("line_start", "line_end"),
        ("character_start", "character_end"),
        ("start", "end"),
    ):
        start = locator.get(start_key)
        end = locator.get(end_key)
        if (
            isinstance(start, int)
            and not isinstance(start, bool)
            and isinstance(end, int)
            and not isinstance(end, bool)
        ):
            return start_key, start, end
    return None


def _token_overlap(left: str, right: str) -> float:
    left_tokens = {token.casefold() for token in _TOKEN.findall(left)}
    right_tokens = {token.casefold() for token in _TOKEN.findall(right)}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))


def _apply_budget(
    ranked: list[RetrievalCandidate], request: RecallQuery
) -> tuple[list[RetrievalCandidate], int]:
    budget = request.budget
    selected: list[RetrievalCandidate] = []
    selected_ids: set[tuple[str, str, str]] = set()
    source_ids: set[str] = set()
    character_count = 0
    token_count = 0

    def try_add(candidate: RetrievalCandidate) -> bool:
        nonlocal character_count, token_count
        identity = _record_version_key(candidate.record)
        if identity in selected_ids or len(selected) >= budget.max_records:
            return False
        characters = len(candidate.record.content)
        tokens = estimate_tokens(candidate.record.content)
        if (
            character_count + characters > budget.max_characters
            or token_count + tokens > budget.max_tokens
        ):
            return False
        selected.append(candidate)
        selected_ids.add(identity)
        source_ids.add(_source_key(candidate.record))
        character_count += characters
        token_count += tokens
        return True

    exact = next((item for item in ranked if item.record.scores.exact >= 1.0), None)
    if exact is not None:
        try_add(exact)
    for candidate in ranked:
        if len(source_ids) >= budget.minimum_source_diversity:
            break
        if _source_key(candidate.record) not in source_ids:
            try_add(candidate)
    for candidate in ranked:
        try_add(candidate)
    selected.sort(key=_rank_key)
    return selected, len(ranked) - len(selected)


def _source_key(record: RetrievedRecord) -> str:
    source = record.source
    return source.source_id or source.path or source.origin_uri or record.record_id


def _record_version_key(record: RetrievedRecord) -> tuple[str, str, str]:
    source = record.source
    revision = source.content_sha256
    if revision is None:
        locator_revision = source.locator.get("source_revision")
        revision = locator_revision if isinstance(locator_revision, str) else "unknown-revision"
    location = source.path or source.origin_uri or source.source_id or "unknown-source"
    return record.record_id, revision, location
