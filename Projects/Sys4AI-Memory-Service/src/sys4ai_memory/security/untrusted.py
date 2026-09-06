"""Untrusted-input classification that keeps embedded instructions as data."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sys4ai_memory.contracts import AuthorityTier, TrustClass

_INSTRUCTION_SHAPE = re.compile(
    r"\b(?:ignore|disregard|override|grant|approve|execute|run|reveal)\b",
    re.I,
)


@dataclass(frozen=True, slots=True)
class UntrustedContent:
    """Evidence-only content whose wording can never authorize behavior."""

    content: str
    authority_tier: AuthorityTier
    trust_class: TrustClass
    namespace: str
    instruction_like: bool
    may_enter_governance: bool = False
    may_authorize_action: bool = False


def classify_external_content(content: str, *, authenticated: bool = False) -> UntrustedContent:
    """Classify imported text as evidence, even when it contains commands."""

    if not content.strip():
        raise ValueError("external content must not be blank")
    return UntrustedContent(
        content=content,
        authority_tier=(
            AuthorityTier.EXTERNAL_EVIDENCE if authenticated else AuthorityTier.UNTRUSTED_CONTENT
        ),
        trust_class=(
            TrustClass.EXTERNALLY_AUTHENTICATED if authenticated else TrustClass.UNTRUSTED
        ),
        namespace="evidence/external",
        instruction_like=bool(_INSTRUCTION_SHAPE.search(content)),
    )
