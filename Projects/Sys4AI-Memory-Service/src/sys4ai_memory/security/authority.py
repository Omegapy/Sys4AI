"""Authority binding for source, summary, and provider-derived material."""

from __future__ import annotations

from dataclasses import dataclass

from sys4ai_memory.contracts import AuthorityTier, TrustClass

from .errors import AuthorityEscalationError


def authority_rank(tier: AuthorityTier) -> int:
    """Return the numeric rank where a larger value means less authority."""

    return int(tier.value[1:])


@dataclass(frozen=True, slots=True)
class DerivedAuthority:
    """Write-time authority provenance for a generated artifact."""

    source_tier: AuthorityTier
    source_trust: TrustClass
    effective_tier: AuthorityTier
    derived_trust: TrustClass
    canonical: bool = False
    may_authorize_action: bool = False


def bind_derived_authority(
    source_tier: AuthorityTier,
    source_trust: TrustClass,
    *,
    model_generated: bool,
) -> DerivedAuthority:
    """Bind a summary/provider result without inheriting source authority upward."""

    minimum_derived_rank = authority_rank(AuthorityTier.AGENT_DURABLE_MATERIAL)
    effective_rank = max(authority_rank(source_tier), minimum_derived_rank)
    return DerivedAuthority(
        source_tier=source_tier,
        source_trust=source_trust,
        effective_tier=AuthorityTier(f"A{effective_rank}"),
        derived_trust=(
            TrustClass.MODEL_EXTRACTED if model_generated else TrustClass.AGENT_GENERATED
        ),
    )


def require_no_authority_elevation(
    source_tier: AuthorityTier,
    candidate_tier: AuthorityTier,
    *,
    candidate_canonical: bool,
) -> None:
    """Reject summaries or provider output that claim stronger or canonical authority."""

    if candidate_canonical or authority_rank(candidate_tier) < authority_rank(source_tier):
        raise AuthorityEscalationError(
            "derived content cannot become canonical or exceed its source authority"
        )


def least_authoritative(*tiers: AuthorityTier) -> AuthorityTier:
    """Return the weakest authority represented in a derivation set."""

    if not tiers:
        raise ValueError("at least one authority tier is required")
    return max(tiers, key=authority_rank)
