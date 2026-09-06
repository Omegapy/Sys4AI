"""Convert fresh canonical authorization into strict provider policy envelopes."""

from __future__ import annotations

from datetime import datetime

from sys4ai_memory.authorization import (
    AuthorizationRequest,
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.providers import (
    MUTATION_PERMISSION,
    PolicyEnvelope,
    ProviderContext,
    ProviderMutation,
)
from sys4ai_memory.security import StaleStateError
from sys4ai_memory.util import ensure_utc, stable_id, utc_now


class ProviderAuthorizationError(RuntimeError):
    """A canonical grant cannot be represented by a provider authorization."""


PROVIDER_OPERATION_NAMES: dict[ProviderMutation, str] = {
    ProviderMutation.INITIALIZE: "memory.initialize",
    ProviderMutation.REMEMBER: "memory.sync",
    ProviderMutation.IMPROVE: "memory.improve",
    ProviderMutation.FORGET: "memory.forget",
    ProviderMutation.EXPORT: "memory.export",
    ProviderMutation.IMPORT: "memory.import",
    ProviderMutation.MIGRATE: "memory.migrate",
}

PROVIDER_AUTHORIZATION_OPERATIONS: dict[ProviderMutation, frozenset[str]] = {
    mutation: frozenset({operation}) for mutation, operation in PROVIDER_OPERATION_NAMES.items()
}
PROVIDER_AUTHORIZATION_OPERATIONS[ProviderMutation.INITIALIZE] = frozenset(
    {"memory.initialize", "memory.initialize.apply"}
)
PROVIDER_AUTHORIZATION_OPERATIONS[ProviderMutation.REMEMBER] = frozenset(
    {"memory.sync", "memory.propose"}
)
PROVIDER_AUTHORIZATION_OPERATIONS[ProviderMutation.IMPORT] = frozenset(
    {"memory.import", "memory.import.activate"}
)


class ProviderAuthorizationBridge:
    """Reread canonical policy and bind it to one exact provider mutation."""

    def __init__(
        self,
        authorization: AuthorizationService,
        loader: CanonicalPermissionEnvelopeLoader,
    ) -> None:
        self._authorization = authorization
        self._loader = loader

    def authorize(
        self,
        context: ProviderContext,
        mutation: ProviderMutation,
        *,
        authorization_operation: str | None = None,
        target_path: str | None = None,
        impact_digest: str | None = None,
        evaluated_at: datetime | None = None,
    ) -> PolicyEnvelope:
        """Return a non-semantic, action-specific, stale-state-safe envelope."""

        permission = MUTATION_PERMISSION[mutation]
        operation_name = authorization_operation or PROVIDER_OPERATION_NAMES[mutation]
        if operation_name not in PROVIDER_AUTHORIZATION_OPERATIONS[mutation]:
            raise ProviderAuthorizationError(
                "provider mutation cannot be bound to the requested service operation"
            )
        decision = self._authorization.require(
            AuthorizationRequest(
                principal_id=context.principal_id,
                project_id=context.project_id,
                dataset_id=context.dataset_id,
                operation=operation_name,
                permission=permission,
                scope=context.scope,
                target_path=target_path,
                trace_id=context.trace_id,
                require_action_specific=True,
            ),
            now=evaluated_at,
        )
        if (
            decision.grant_id is None
            or decision.permission_revision is None
            or decision.canonical_sha256 is None
        ):
            raise ProviderAuthorizationError(
                "allowed canonical decision is missing provider authorization metadata"
            )

        snapshot = self._loader.load_snapshot()
        if (
            snapshot.document.revision != decision.permission_revision
            or snapshot.content_sha256 != decision.canonical_sha256
        ):
            raise StaleStateError(
                "canonical permission changed while binding provider authorization"
            )
        timestamp = ensure_utc(evaluated_at or utc_now())
        identifier = stable_id(
            "provider-policy-decision",
            decision.canonical_sha256,
            decision.permission_revision,
            decision.grant_id,
            mutation.value,
            operation_name,
            context.principal_id,
            context.trace_id,
            impact_digest or "no-impact-digest",
        )
        return PolicyEnvelope(
            decision_id=f"decision_{identifier.replace('-', '')}",
            operation=mutation,
            principal_id=context.principal_id,
            project_id=context.project_id,
            dataset_id=context.dataset_id,
            scope=context.scope,
            permission=permission,
            allowed=True,
            policy_id=decision.grant_id,
            policy_revision=decision.permission_revision,
            canonical_source=self._loader.source_path,
            evaluated_at=timestamp,
            trace_id=context.trace_id,
            impact_digest=impact_digest,
        )
