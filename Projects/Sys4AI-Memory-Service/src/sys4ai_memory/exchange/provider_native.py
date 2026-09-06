"""Explicitly gated delegation metadata for provider-owned COGX exchange."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from sys4ai_memory.providers import MemoryProvider

from .models import CogxDelegation


def plan_cogx_delegation(
    provider: MemoryProvider,
    *,
    direction: Literal["export", "import"],
    artifact_path: str,
    provider_native_enabled: bool,
    format_decision_status: str,
) -> CogxDelegation:
    """Describe a provider-native handoff without accessing provider storage."""

    path = PurePosixPath(artifact_path)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("COGX artifact path must be normalized and project-relative")
    approved = provider_native_enabled and not format_decision_status.startswith("pending-")
    return CogxDelegation(
        provider_name=provider.provider_name.value,
        provider_version=provider.provider_version,
        direction=direction,
        artifact_path=path.as_posix(),
        approved=approved,
        reason_code=(
            "provider_native_delegation_approved"
            if approved
            else "provider_native_exchange_policy_disabled_or_unresolved"
        ),
    )
