"""Authorized and audited execution boundary for local control-plane changes."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from sys4ai_memory.authorization import (
    AuthorizationRequest,
    AuthorizationService,
    PermissionDeniedError,
)
from sys4ai_memory.contracts import Permission, ScopeReference

from .audit import AuditRecorder
from .models import AdministrativeOperation, CountMetric, VersionContext

_Result = TypeVar("_Result")


class AdministrativeActionExecutor:
    """Reread canonical authority, run one local change, and audit its outcome.

    Administrative changes intentionally remain outside the public memory API.
    An operator-facing control plane can provide a reviewed callback here without
    creating a second authorization or audit implementation.
    """

    def __init__(
        self,
        *,
        authorization: AuthorizationService,
        audit: AuditRecorder,
        project_id: str,
        dataset_id: str,
        versions: VersionContext,
        policy_decision_ref: str,
    ) -> None:
        if not project_id.strip() or not dataset_id.strip() or not policy_decision_ref.strip():
            raise ValueError("administrative boundary identifiers must not be blank")
        self._authorization = authorization
        self._audit = audit
        self._project_id = project_id
        self._dataset_id = dataset_id
        self._versions = versions
        self._policy_decision_ref = policy_decision_ref

    def execute(
        self,
        operation: AdministrativeOperation,
        *,
        principal_id: str,
        scope: ScopeReference,
        trace_id: str,
        action: Callable[[], _Result],
        target_path: str | None = None,
        target_ids: tuple[str, ...] = (),
    ) -> _Result:
        """Execute only after a fresh, action-specific canonical decision."""

        decision = self._authorization.evaluate(
            AuthorizationRequest(
                principal_id=principal_id,
                project_id=self._project_id,
                dataset_id=self._dataset_id,
                operation=operation.value,
                permission=self._permission(operation),
                scope=scope,
                target_path=target_path,
                trace_id=trace_id,
                require_action_specific=True,
            )
        )
        if not decision.allowed:
            self._audit.capture(
                decision=decision,
                actor_id=principal_id,
                policy_decision_ref=self._policy_decision_ref,
                outcome_code="denied",
                trace_id=trace_id,
                versions=self._versions,
                target_ids=target_ids,
                counts=(CountMetric(name="target_count", value=len(target_ids)),),
            )
            raise PermissionDeniedError(f"permission denied: {decision.reason_code}")

        # Persist the current permission decision before a reviewed callback is
        # allowed to change control-plane state. A sink failure therefore stops
        # execution rather than leaving a mutation with no authorization event.
        self._audit.capture(
            decision=decision,
            actor_id=principal_id,
            policy_decision_ref=self._policy_decision_ref,
            outcome_code="authorized",
            trace_id=trace_id,
            versions=self._versions,
            target_ids=target_ids,
            counts=(CountMetric(name="target_count", value=len(target_ids)),),
        )
        try:
            result = action()
        except Exception:
            self._audit.capture(
                decision=decision,
                actor_id=principal_id,
                policy_decision_ref=self._policy_decision_ref,
                outcome_code="failed",
                trace_id=trace_id,
                versions=self._versions,
                target_ids=target_ids,
                counts=(CountMetric(name="target_count", value=len(target_ids)),),
            )
            raise

        self._audit.capture(
            decision=decision,
            actor_id=principal_id,
            policy_decision_ref=self._policy_decision_ref,
            outcome_code="succeeded",
            trace_id=trace_id,
            versions=self._versions,
            target_ids=target_ids,
            counts=(CountMetric(name="target_count", value=len(target_ids)),),
        )
        return result

    @staticmethod
    def _permission(operation: AdministrativeOperation) -> Permission:
        if operation is AdministrativeOperation.OPERATION_STATUS:
            return Permission.READ
        return Permission.ADMINISTER
