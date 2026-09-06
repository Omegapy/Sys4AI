"""Inspectable weighted ranking for provider-neutral retrieval candidates."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sys4ai_memory.contracts import AuthorityTier, RecordStatus, RetrievalMode, TrustClass
from sys4ai_memory.contracts.models import RetrievalScores

from .models import RankingContext, RankingWeights, RetrievalCandidate

_TRUST_SCORE: dict[TrustClass, float] = {
    TrustClass.SYSTEM_CONTROLLED: 1.00,
    TrustClass.HUMAN_APPROVED: 0.95,
    TrustClass.SCHEMA_VALIDATED: 0.90,
    TrustClass.PROJECT_AUTHORED: 0.85,
    TrustClass.EXTERNALLY_AUTHENTICATED: 0.70,
    TrustClass.USER_SUPPLIED: 0.60,
    TrustClass.EXTERNAL_UNVERIFIED: 0.50,
    TrustClass.AGENT_GENERATED: 0.45,
    TrustClass.MODEL_EXTRACTED: 0.35,
    TrustClass.UNTRUSTED: 0.00,
}


class Ranker(Protocol):
    """Explicit interface required for replaceable profile-specific rankers."""

    @property
    def weights(self) -> RankingWeights: ...

    def score(
        self, candidate: RetrievalCandidate, context: RankingContext
    ) -> RetrievalCandidate: ...


class WeightedRanker:
    """Apply configured channel, authority, trust, freshness, and penalty signals."""

    def __init__(self, weights: RankingWeights | None = None) -> None:
        self._weights = weights or RankingWeights()

    @property
    def weights(self) -> RankingWeights:
        return self._weights

    def score(self, candidate: RetrievalCandidate, context: RankingContext) -> RetrievalCandidate:
        source_scores = candidate.record.scores
        channel_values = {
            RetrievalMode.EXACT: source_scores.exact,
            RetrievalMode.LEXICAL: source_scores.lexical,
            RetrievalMode.SEMANTIC: source_scores.semantic,
            RetrievalMode.GRAPH: source_scores.graph,
            RetrievalMode.TEMPORAL: source_scores.temporal or 0.0,
        }
        channel_weights = {
            RetrievalMode.EXACT: self.weights.exact,
            RetrievalMode.LEXICAL: self.weights.lexical,
            RetrievalMode.SEMANTIC: self.weights.semantic,
            RetrievalMode.GRAPH: self.weights.graph,
            RetrievalMode.TEMPORAL: self.weights.temporal,
        }
        active_weight = sum(channel_weights[channel] for channel in context.channels)
        relevance_numerator = sum(
            channel_values[channel] * channel_weights[channel] for channel in context.channels
        )
        relevance = relevance_numerator / active_weight if active_weight else 0.0

        authority_score = _authority_score(candidate.record.authority.tier)
        trust_score = trust_score_for(candidate.record.authority.trust_class)
        freshness_score = _freshness_score(candidate, context, self.weights)
        secondary_weight = self.weights.authority + self.weights.trust + self.weights.freshness
        denominator = active_weight + secondary_weight
        authority_boost = self.weights.authority * authority_score / denominator
        trust_boost = self.weights.trust * trust_score / denominator
        freshness_boost = self.weights.freshness * freshness_score / denominator

        superseded_penalty = (
            self.weights.superseded_penalty
            if candidate.record.lifecycle.status is RecordStatus.SUPERSEDED
            and not context.historical
            else 0.0
        )
        scope_distance = _scope_distance(candidate, context)
        scope_penalty = self.weights.scope_distance_penalty * min(scope_distance, 1.0)
        unverified_penalty = self.weights.unverified_penalty if _is_unverified(candidate) else 0.0
        duplicate_penalty = source_scores.duplicate_penalty or 0.0

        if relevance <= 0.0:
            final = 0.0
        else:
            final = relevance + authority_boost + trust_boost + freshness_boost
            final -= duplicate_penalty + superseded_penalty + scope_penalty + unverified_penalty
            final = min(1.0, max(0.0, final))

        if context.exact_identifier_query:
            if source_scores.exact >= 1.0:
                final = max(final, self.weights.exact_identifier_floor)
            else:
                final = min(final, self.weights.non_exact_identifier_ceiling)

        scores = RetrievalScores(
            exact=source_scores.exact,
            lexical=source_scores.lexical,
            semantic=source_scores.semantic,
            graph=source_scores.graph,
            temporal=source_scores.temporal or 0.0,
            authority_boost=authority_boost,
            trust=trust_score,
            freshness=freshness_score,
            duplicate_penalty=duplicate_penalty,
            superseded_penalty=superseded_penalty,
            scope_distance_penalty=scope_penalty,
            unverified_penalty=unverified_penalty,
            final=final,
        )
        reasons = tuple(
            dict.fromkeys(
                (
                    *candidate.record.selection_reason,
                    f"rank:channels={_channel_summary(scores)}",
                    f"rank:authority={candidate.record.authority.tier.value}:{authority_score:.3f}",
                    f"rank:trust={candidate.record.authority.trust_class.value}:{trust_score:.3f}",
                    f"rank:freshness={freshness_score:.3f}",
                    "rank:penalties="
                    f"duplicate:{duplicate_penalty:.3f},"
                    f"superseded:{superseded_penalty:.3f},"
                    f"scope:{scope_penalty:.3f},"
                    f"unverified:{unverified_penalty:.3f}",
                    f"rank:final={final:.3f}",
                )
            )
        )
        return RetrievalCandidate(
            record=candidate.record.model_copy(
                update={"scores": scores, "selection_reason": reasons}
            ),
            namespace=candidate.namespace,
            scope=candidate.scope,
            valid_from=candidate.valid_from,
            valid_to=candidate.valid_to,
            updated_at=candidate.updated_at,
            verification=candidate.verification,
            content_origin=candidate.content_origin,
            instruction_like=candidate.instruction_like,
            canonical=candidate.canonical,
            relation_unverified=candidate.relation_unverified,
        )


def trust_score_for(trust: TrustClass) -> float:
    return _TRUST_SCORE[trust]


def _authority_score(tier: AuthorityTier) -> float:
    return 1.0 - int(tier.value[1:]) / 7.0


def _freshness_score(
    candidate: RetrievalCandidate,
    context: RankingContext,
    weights: RankingWeights,
) -> float:
    if context.at_time is not None:
        if candidate.valid_from is None:
            return 0.0
        if candidate.valid_from > context.at_time:
            return 0.0
        if candidate.valid_to is not None and context.at_time > candidate.valid_to:
            return 0.0
        return 1.0
    reference: datetime | None = candidate.updated_at or candidate.valid_from
    if reference is None:
        return 0.5
    age_days = max(0.0, (context.now - reference).total_seconds() / 86_400.0)
    return max(0.0, 1.0 - age_days / weights.freshness_horizon_days)


def _scope_distance(candidate: RetrievalCandidate, context: RankingContext) -> float:
    if candidate.scope is None:
        return 0.0
    target = (candidate.scope.level, candidate.scope.scope_id)
    if target == (context.scope.level, context.scope.scope_id):
        return 0.0
    pending = [(parent, 1) for parent in context.scope.parent_scopes]
    seen: set[tuple[object, str]] = set()
    while pending:
        parent, distance = pending.pop(0)
        identity = (parent.level, parent.scope_id)
        if identity in seen:
            continue
        seen.add(identity)
        if target == identity:
            return min(1.0, distance / 4.0)
        pending.extend((ancestor, distance + 1) for ancestor in parent.parent_scopes)
    return 1.0


def _is_unverified(candidate: RetrievalCandidate) -> bool:
    verification = (candidate.verification or "").casefold()
    return (
        verification in {"unverified", "model-extracted", "model_extracted", "unknown"}
        or candidate.record.authority.trust_class
        in {
            TrustClass.EXTERNAL_UNVERIFIED,
            TrustClass.AGENT_GENERATED,
            TrustClass.MODEL_EXTRACTED,
            TrustClass.UNTRUSTED,
        }
        or candidate.relation_unverified
    )


def _channel_summary(scores: RetrievalScores) -> str:
    return ",".join(
        (
            f"exact:{scores.exact:.3f}",
            f"lexical:{scores.lexical:.3f}",
            f"semantic:{scores.semantic:.3f}",
            f"graph:{scores.graph:.3f}",
            f"temporal:{(scores.temporal or 0.0):.3f}",
        )
    )
