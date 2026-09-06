"""Replaceable async memory-provider boundary."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sys4ai_memory.contracts.errors import ErrorCategory

from .contracts import (
    ExportRequest,
    ExportResult,
    ForgetRequest,
    ForgetResult,
    HealthRequest,
    ImportRequest,
    ImportResult,
    ImproveRequest,
    ImproveResult,
    MigrationRequest,
    MigrationResult,
    PolicyEnvelope,
    ProviderCapabilities,
    ProviderContext,
    ProviderHealth,
    ProviderInitializationRequest,
    ProviderInitializationResult,
    ProviderMutation,
    ProviderName,
    ProviderRecallResult,
    RecallRequest,
    RememberRequest,
    RememberResult,
)
from .errors import provider_error


@runtime_checkable
class MemoryProvider(Protocol):
    """The only provider call shape visible to Sys4AI service code."""

    @property
    def provider_name(self) -> ProviderName: ...

    @property
    def provider_version(self) -> str: ...

    async def initialize(
        self, request: ProviderInitializationRequest
    ) -> ProviderInitializationResult: ...

    async def capabilities(self, context: ProviderContext) -> ProviderCapabilities: ...

    async def remember(self, request: RememberRequest) -> RememberResult: ...

    async def recall(self, request: RecallRequest) -> ProviderRecallResult: ...

    async def improve(self, request: ImproveRequest) -> ImproveResult: ...

    async def forget(self, request: ForgetRequest) -> ForgetResult: ...

    async def health(self, request: HealthRequest) -> ProviderHealth: ...

    async def export(self, request: ExportRequest) -> ExportResult: ...

    async def import_snapshot(self, request: ImportRequest) -> ImportResult: ...

    async def migrate(self, request: MigrationRequest) -> MigrationResult: ...


def require_context(
    context: ProviderContext,
    *,
    project_id: str,
    dataset_id: str,
) -> None:
    """Fail closed when a request crosses the configured provider boundary."""

    if context.project_id != project_id or context.dataset_id != dataset_id:
        raise provider_error(
            ErrorCategory.PERMISSION_DENIED,
            trace_id=context.trace_id,
            message="The request is outside the configured project and dataset boundary.",
            recoverable=False,
            remediation_hint="Use the provider instance configured for the authorized project.",
        )


def require_authorization(
    authorization: PolicyEnvelope | None,
    *,
    operation: ProviderMutation,
    context: ProviderContext,
    impact_digest: str | None = None,
) -> PolicyEnvelope:
    """Validate an action-specific canonical policy decision before mutation."""

    if authorization is None:
        raise provider_error(
            ErrorCategory.APPROVAL_REQUIRED,
            trace_id=context.trace_id,
            message="The provider mutation requires an explicit Sys4AI policy decision.",
            recoverable=False,
            remediation_hint="Resolve current canonical authorization for this exact operation.",
        )
    if not authorization.allowed:
        raise provider_error(
            ErrorCategory.PERMISSION_DENIED,
            trace_id=context.trace_id,
            message="The canonical Sys4AI policy decision denied the provider mutation.",
            recoverable=False,
            remediation_hint="Do not retry unless the canonical permission state changes.",
        )
    identity_matches = (
        authorization.operation is operation
        and authorization.principal_id == context.principal_id
        and authorization.project_id == context.project_id
        and authorization.dataset_id == context.dataset_id
        and authorization.scope == context.scope
        and authorization.trace_id == context.trace_id
    )
    if not identity_matches:
        raise provider_error(
            ErrorCategory.AUTHORITY_VIOLATION,
            trace_id=context.trace_id,
            message="The policy decision does not match the requested mutation scope.",
            recoverable=False,
            remediation_hint=(
                "Resolve a new decision for the exact principal, operation, and scope."
            ),
        )
    if impact_digest is not None and authorization.impact_digest != impact_digest:
        raise provider_error(
            ErrorCategory.AUTHORITY_VIOLATION,
            trace_id=context.trace_id,
            message="The authorized impact set no longer matches the requested mutation.",
            recoverable=False,
            remediation_hint="Create a new preview and authorize its current impact digest.",
        )
    return authorization
