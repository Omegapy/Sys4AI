"""Typed write-policy matrix for provider-neutral memory operations."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sys4ai_memory.authorization import AuthorizationRequest, AuthorizationService
from sys4ai_memory.contracts import (
    AuthorityTier,
    Permission,
    PolicyAction,
    RecordStatus,
    ScopeReference,
    Sensitivity,
    TrustClass,
)
from sys4ai_memory.contracts.models import PolicyResult, RequesterIdentity
from sys4ai_memory.security import AuditEvent, AuditSink, InMemoryAuditSink, require_secret_free
from sys4ai_memory.util import sha256_bytes, utc_now


class WriteTargetClass(StrEnum):
    SESSION = "session"
    EPISODIC = "episodic"
    OBSERVATION = "observation"
    FEEDBACK = "feedback"
    DERIVED = "derived"
    PROJECT_FACT = "project_fact"
    DECISION = "decision"
    REQUIREMENT = "requirement"
    GOVERNANCE = "governance"
    PERMISSION = "permission"
    CANONICAL_CODE = "canonical_code"
    CANONICAL_CONFIGURATION = "canonical_configuration"
    EXTERNAL_EVIDENCE = "external_evidence"


class WritePolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)


class WriteRequest(WritePolicyModel):
    """All fields required to classify a durable write safely."""

    project_id: str
    dataset_id: str
    requester: RequesterIdentity
    record_type: str | None
    target_class: WriteTargetClass
    scope: ScopeReference | None
    evidence_ids: tuple[str, ...]
    requested_status: RecordStatus | None
    trust_class: TrustClass | None
    sensitivity: Sensitivity | None
    authority_tier: AuthorityTier | None
    requested_target: str | None
    idempotency_key: str | None
    trace_id: str
    content: Any
    external_source: bool = False
    automatic_feedback: bool = False


class WritePolicySettings(WritePolicyModel):
    policy_id: str = "memory-write-policy@1"
    compatibility_allows_untyped: bool = False
    episodic_auto_commit: bool = False
    derived_commit_enabled: bool = True
    automatic_feedback_enabled: bool = False


class WritePolicyDecision(WritePolicyModel):
    action: PolicyAction
    policy_id: str
    reasons: tuple[str, ...] = Field(min_length=1)
    effective_principal: str
    required_permission: Permission | None
    permission_revision: str | None = None
    canonical_permission_sha256: str | None = None

    def to_contract(self) -> PolicyResult:
        return PolicyResult(action=self.action, policy_id=self.policy_id, reasons=self.reasons)


_HUMAN_REVIEW_TARGETS = frozenset(
    {
        WriteTargetClass.PROJECT_FACT,
        WriteTargetClass.DECISION,
        WriteTargetClass.REQUIREMENT,
        WriteTargetClass.GOVERNANCE,
        WriteTargetClass.PERMISSION,
        WriteTargetClass.CANONICAL_CODE,
        WriteTargetClass.CANONICAL_CONFIGURATION,
    }
)


class WritePolicyEngine:
    """Pure matrix classification; use AuthorizedWritePolicy at persistence boundaries."""

    def __init__(self, settings: WritePolicySettings | None = None) -> None:
        self._settings = settings or WritePolicySettings()

    def evaluate(
        self,
        request: WriteRequest,
        *,
        current_permissions: frozenset[Permission],
    ) -> WritePolicyDecision:
        principal = request.requester.principal_id
        missing = self._missing_required_fields(request)
        if missing and not self._settings.compatibility_allows_untyped:
            return self._decision(
                PolicyAction.REJECT,
                principal,
                f"typed write is missing required fields: {','.join(missing)}",
            )
        try:
            require_secret_free(request.content, field_path="write.content")
        except RuntimeError:
            return self._decision(
                PolicyAction.REJECT,
                principal,
                "secret-like content is prohibited",
            )
        if request.sensitivity is Sensitivity.SECRET_PROHIBITED:
            return self._decision(
                PolicyAction.REJECT,
                principal,
                "secret-prohibited content cannot enter memory",
            )
        if not self._scope_belongs_to_project(request):
            return self._decision(
                PolicyAction.REJECT,
                principal,
                "requested scope does not belong to the project boundary",
            )
        if request.external_source and request.target_class in {
            WriteTargetClass.GOVERNANCE,
            WriteTargetClass.PERMISSION,
        }:
            return self._decision(
                PolicyAction.REJECT,
                principal,
                "external evidence cannot authorize or become governance directly",
            )
        if request.automatic_feedback and not self._settings.automatic_feedback_enabled:
            return self._decision(
                PolicyAction.REJECT,
                principal,
                "automatic feedback collection is disabled",
            )
        if Permission.PROPOSE not in current_permissions:
            return self._decision(
                PolicyAction.REJECT,
                principal,
                "principal lacks propose permission",
                Permission.PROPOSE,
            )

        if request.target_class is WriteTargetClass.SESSION:
            if request.scope is None or request.scope.level.value != "session":
                return self._decision(
                    PolicyAction.REJECT,
                    principal,
                    "session writes require session scope",
                )
            return self._decision(
                PolicyAction.SESSION_ONLY,
                principal,
                "session content is temporary and non-authoritative",
                Permission.PROPOSE,
            )

        if request.target_class in {WriteTargetClass.EPISODIC, WriteTargetClass.OBSERVATION}:
            if (
                self._settings.episodic_auto_commit
                and Permission.WRITE_DERIVED in current_permissions
            ):
                return self._decision(
                    PolicyAction.EPISODIC_COMMIT,
                    principal,
                    "approved task policy permits a bounded episodic event",
                    Permission.WRITE_DERIVED,
                )
            return self._decision(
                PolicyAction.STAGE_FOR_REVIEW,
                principal,
                "episodic durable retention or auto-commit is not approved",
                Permission.PROPOSE,
            )

        if request.target_class in {
            WriteTargetClass.FEEDBACK,
            WriteTargetClass.DERIVED,
            WriteTargetClass.EXTERNAL_EVIDENCE,
        }:
            if (
                self._settings.derived_commit_enabled
                and Permission.WRITE_DERIVED in current_permissions
            ):
                return self._decision(
                    PolicyAction.DERIVED_COMMIT,
                    principal,
                    "typed derived write is permitted within the current scope",
                    Permission.WRITE_DERIVED,
                )
            return self._decision(
                PolicyAction.STAGE_FOR_REVIEW,
                principal,
                "derived persistence is not authorized for this principal",
                Permission.PROPOSE,
            )

        if request.target_class in _HUMAN_REVIEW_TARGETS:
            return self._decision(
                PolicyAction.STAGE_FOR_REVIEW,
                principal,
                "canonical or privileged target requires human review",
                Permission.PROPOSE,
            )

        return self._decision(PolicyAction.REJECT, principal, "write target is not supported")

    @staticmethod
    def _missing_required_fields(request: WriteRequest) -> tuple[str, ...]:
        missing: list[str] = []
        if request.record_type is None or not request.record_type.strip():
            missing.append("record_type")
        if request.scope is None:
            missing.append("scope")
        if not request.evidence_ids:
            missing.append("evidence_ids")
        if request.requested_status is None:
            missing.append("status")
        if request.trust_class is None:
            missing.append("trust_class")
        if request.sensitivity is None:
            missing.append("sensitivity")
        if request.authority_tier is None:
            missing.append("authority_tier")
        if request.requested_target is None or not request.requested_target.strip():
            missing.append("requested_target")
        if request.idempotency_key is None or not request.idempotency_key.strip():
            missing.append("idempotency_key")
        return tuple(missing)

    @staticmethod
    def _scope_belongs_to_project(request: WriteRequest) -> bool:
        if request.scope is None:
            return False
        scopes = (request.scope, *request.scope.parent_scopes)
        project_scopes = tuple(scope for scope in scopes if scope.level.value == "project")
        return bool(project_scopes) and all(
            scope.scope_id == request.project_id for scope in project_scopes
        )

    def _decision(
        self,
        action: PolicyAction,
        principal: str,
        reason: str,
        permission: Permission | None = None,
    ) -> WritePolicyDecision:
        return WritePolicyDecision(
            action=action,
            policy_id=self._settings.policy_id,
            reasons=(reason,),
            effective_principal=principal,
            required_permission=permission,
        )


class AuthorizedWritePolicy:
    """Resolve current canonical permissions before applying the write matrix."""

    def __init__(
        self,
        engine: WritePolicyEngine,
        authorization: AuthorizationService,
        *,
        audit: AuditSink | None = None,
    ) -> None:
        self._engine = engine
        self._authorization = authorization
        self._audit = audit or InMemoryAuditSink()

    def evaluate(self, request: WriteRequest) -> WritePolicyDecision:
        permissions: set[Permission] = set()
        decisions = []
        for permission in (Permission.PROPOSE, Permission.WRITE_DERIVED):
            if request.scope is None:
                continue
            operation = (
                "memory.propose" if permission is Permission.PROPOSE else "memory.write-derived"
            )
            authorization = self._authorization.evaluate(
                AuthorizationRequest(
                    principal_id=request.requester.principal_id,
                    project_id=request.project_id,
                    dataset_id=request.dataset_id,
                    operation=operation,
                    permission=permission,
                    scope=request.scope,
                    target_path=request.requested_target,
                    trace_id=request.trace_id,
                )
            )
            decisions.append(authorization)
            if authorization.allowed:
                permissions.add(permission)

        permission_states = {
            (decision.permission_revision, decision.canonical_sha256) for decision in decisions
        }
        if len(permission_states) > 1:
            result = WritePolicyDecision(
                action=PolicyAction.REJECT,
                policy_id="memory-write-policy@1",
                reasons=("canonical permission changed during write evaluation",),
                effective_principal=request.requester.principal_id,
                required_permission=None,
            )
        else:
            result = self._engine.evaluate(
                request,
                current_permissions=frozenset(permissions),
            )
            if permission_states:
                revision, content_sha256 = next(iter(permission_states))
                result = WritePolicyDecision.model_validate(
                    {
                        **result.model_dump(),
                        "permission_revision": revision,
                        "canonical_permission_sha256": content_sha256,
                    }
                )

        target_hash = (
            sha256_bytes(request.requested_target.encode("utf-8"))
            if request.requested_target
            else "no-target"
        )
        self._audit.record(
            AuditEvent(
                event_id=f"{request.trace_id}:write-policy",
                occurred_at=utc_now(),
                principal_id=request.requester.principal_id,
                project_id=request.project_id,
                dataset_id=request.dataset_id,
                operation="memory.propose.policy",
                target_ids=(target_hash,),
                policy_decision=result.action.value,
                outcome="allowed" if result.action is not PolicyAction.REJECT else "rejected",
                trace_id=request.trace_id,
                policy_id=result.policy_id,
                permission_revision=result.permission_revision,
            )
        )
        return result
