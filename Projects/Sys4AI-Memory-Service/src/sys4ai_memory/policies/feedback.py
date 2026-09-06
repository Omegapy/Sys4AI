"""Explicit feedback and auditable, authority-preserving improvement records."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sys4ai_memory.authorization import AuthorizationRequest, AuthorizationService
from sys4ai_memory.contracts import AuthorityTier, Permission, ScopeReference, TrustClass
from sys4ai_memory.security import (
    AuditEvent,
    AuditSink,
    InMemoryAuditSink,
    PolicyDisabledError,
    authority_rank,
    least_authoritative,
    require_secret_free,
)
from sys4ai_memory.util import ensure_utc, utc_now


class FeedbackOrigin(StrEnum):
    CORRECTION = "correction"
    REUSE = "reuse"
    RETRIEVAL_SELECTION = "retrieval_selection"
    EXPLICIT_RATING = "explicit_rating"
    VALIDATION_RESULT = "validation_result"


class ImprovementSuggestionKind(StrEnum):
    STALE = "stale"
    DUPLICATE = "duplicate"
    WEAKLY_SUPPORTED = "weakly-supported"
    FREQUENTLY_USEFUL = "frequently-useful"


class FeedbackModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class FeedbackPolicy(FeedbackModel):
    status: Literal["approved", "pending-user-decision"] = "pending-user-decision"
    policy_id: str | None = None
    automatic_collection: bool = False
    allowed_automatic_origins: frozenset[FeedbackOrigin] = frozenset()

    @model_validator(mode="after")
    def validate_policy(self) -> Self:
        if self.status != "approved" and (
            self.policy_id is not None
            or self.automatic_collection
            or self.allowed_automatic_origins
        ):
            raise ValueError("pending feedback policy must remain disabled")
        if self.status == "approved" and not self.policy_id:
            raise ValueError("approved feedback policy requires a policy ID")
        return self


APPROVED_EXPLICIT_TYPED_FEEDBACK_POLICY = FeedbackPolicy(
    status="approved",
    policy_id="explicit-typed-feedback-only@1",
    automatic_collection=False,
    allowed_automatic_origins=frozenset(),
)


class FeedbackRecord(FeedbackModel):
    feedback_id: str
    project_id: str
    target_record_id: str
    origin: FeedbackOrigin
    actor_id: str
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    rationale_summary: str = Field(min_length=1, max_length=2000)
    source_authority_tier: AuthorityTier
    source_trust_class: TrustClass
    effective_authority_tier: AuthorityTier
    effective_trust_class: TrustClass
    automatic: bool
    created_at: datetime
    changes_source_authority: Literal[False] = False

    @model_validator(mode="after")
    def preserve_authority(self) -> Self:
        ensure_utc(self.created_at)
        if authority_rank(self.effective_authority_tier) < authority_rank(
            self.source_authority_tier
        ):
            raise ValueError("feedback cannot raise source authority")
        require_secret_free(
            {
                "actor_id": self.actor_id,
                "evidence_refs": self.evidence_refs,
                "rationale_summary": self.rationale_summary,
            },
            field_path="feedback",
        )
        return self


class ImprovementReceipt(FeedbackModel):
    receipt_id: str
    project_id: str
    operation: Literal["reweight", "consolidate", "classify-for-review"]
    target_record_ids: tuple[str, ...] = Field(min_length=1)
    feedback_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    configuration_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    authority_before: AuthorityTier
    authority_after: AuthorityTier
    trust_before: TrustClass
    trust_after: TrustClass
    created_at: datetime

    @model_validator(mode="after")
    def validate_receipt(self) -> Self:
        ensure_utc(self.created_at)
        if self.authority_before is not self.authority_after:
            raise ValueError("provider improvement cannot change record authority")
        if self.trust_before is not self.trust_after:
            raise ValueError("provider improvement cannot change record trust")
        return self


class ImprovementRequest(FeedbackModel):
    principal_id: str
    project_id: str
    dataset_id: str
    profile_id: str
    scope: ScopeReference
    trace_id: str
    target_record_ids: tuple[str, ...] = Field(min_length=1)
    feedback: tuple[FeedbackRecord, ...] = Field(min_length=1)
    configuration_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_unique_targets(self) -> Self:
        if len(set(self.target_record_ids)) != len(self.target_record_ids):
            raise ValueError("improvement targets must not contain duplicates")
        return self


class ImprovementSuggestion(FeedbackModel):
    target_record_id: str
    kind: ImprovementSuggestionKind
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    active_change_performed: Literal[False] = False


class ConsolidationInput(FeedbackModel):
    record_id: str
    authority_tier: AuthorityTier
    trust_class: TrustClass
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    conflicts_with: frozenset[str] = frozenset()


class DerivedPattern(FeedbackModel):
    record_id: str
    generated: Literal[True] = True
    generator_configuration_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_record_ids: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    authority_tier: AuthorityTier
    trust_class: Literal[TrustClass.AGENT_GENERATED] = TrustClass.AGENT_GENERATED
    canonical: Literal[False] = False


class FeedbackService:
    """Accept explicit typed feedback; automatic signals remain opt-in and gated."""

    def __init__(self, policy: FeedbackPolicy | None = None) -> None:
        self._policy = policy or APPROVED_EXPLICIT_TYPED_FEEDBACK_POLICY

    def validate(self, record: FeedbackRecord) -> FeedbackRecord:
        if record.automatic and (
            self._policy.status != "approved"
            or not self._policy.automatic_collection
            or record.origin not in self._policy.allowed_automatic_origins
        ):
            raise PolicyDisabledError("automatic feedback collection is not approved")
        return record

    @staticmethod
    def reweight_receipt(
        *,
        receipt_id: str,
        project_id: str,
        record_id: str,
        feedback_ids: tuple[str, ...],
        evidence_refs: tuple[str, ...],
        configuration_fingerprint: str,
        authority: AuthorityTier,
        trust: TrustClass,
        created_at: datetime | None = None,
    ) -> ImprovementReceipt:
        return ImprovementReceipt(
            receipt_id=receipt_id,
            project_id=project_id,
            operation="reweight",
            target_record_ids=(record_id,),
            feedback_ids=feedback_ids,
            evidence_refs=evidence_refs,
            configuration_fingerprint=configuration_fingerprint,
            authority_before=authority,
            authority_after=authority,
            trust_before=trust,
            trust_after=trust,
            created_at=created_at or utc_now(),
        )

    @staticmethod
    def consolidate(
        *,
        record_id: str,
        inputs: tuple[ConsolidationInput, ...],
        configuration_fingerprint: str,
    ) -> DerivedPattern:
        if not inputs:
            raise ValueError("consolidation requires source records")
        source_ids = frozenset(item.record_id for item in inputs)
        if any(item.conflicts_with & source_ids for item in inputs):
            raise ValueError("conflicting records must remain separate")
        evidence = tuple(sorted({ref for item in inputs for ref in item.evidence_refs}))
        source_authority = least_authoritative(*(item.authority_tier for item in inputs))
        effective_rank = max(
            authority_rank(source_authority),
            authority_rank(AuthorityTier.AGENT_DURABLE_MATERIAL),
        )
        return DerivedPattern(
            record_id=record_id,
            generator_configuration_fingerprint=configuration_fingerprint,
            source_record_ids=tuple(sorted(source_ids)),
            evidence_refs=evidence,
            authority_tier=AuthorityTier(f"A{effective_rank}"),
        )

    @staticmethod
    def suggest_for_review(
        *,
        target_record_id: str,
        kind: ImprovementSuggestionKind,
        evidence_refs: tuple[str, ...],
    ) -> ImprovementSuggestion:
        return ImprovementSuggestion(
            target_record_id=target_record_id,
            kind=kind,
            evidence_refs=evidence_refs,
        )


class AuthorizedImprovementService:
    """Authorize improvement for one dataset/profile without editing canonical sources."""

    def __init__(
        self,
        authorization: AuthorizationService,
        *,
        enabled_profile_ids: frozenset[str],
        feedback_service: FeedbackService | None = None,
        audit: AuditSink | None = None,
    ) -> None:
        self._authorization = authorization
        self._profiles = enabled_profile_ids
        self._feedback = feedback_service or FeedbackService()
        self._audit = audit or InMemoryAuditSink()

    def reweight(
        self,
        request: ImprovementRequest,
        *,
        receipt_id: str,
        authority: AuthorityTier,
        trust: TrustClass,
        created_at: datetime | None = None,
    ) -> ImprovementReceipt:
        if len(request.target_record_ids) != 1:
            raise ValueError("reweight requires exactly one target record")
        permission_revision = self._authorize(request)
        feedback = tuple(self._feedback.validate(item) for item in request.feedback)
        self._validate_feedback_scope(request, feedback)
        evidence_refs = tuple(sorted({ref for item in feedback for ref in item.evidence_refs}))
        receipt = self._feedback.reweight_receipt(
            receipt_id=receipt_id,
            project_id=request.project_id,
            record_id=request.target_record_ids[0],
            feedback_ids=tuple(item.feedback_id for item in feedback),
            evidence_refs=evidence_refs,
            configuration_fingerprint=request.configuration_fingerprint,
            authority=authority,
            trust=trust,
            created_at=created_at,
        )
        self._record_audit(request, permission_revision, receipt.created_at, "reweight")
        return receipt

    def consolidate(
        self,
        request: ImprovementRequest,
        *,
        record_id: str,
        inputs: tuple[ConsolidationInput, ...],
        created_at: datetime | None = None,
    ) -> tuple[DerivedPattern, ImprovementReceipt]:
        permission_revision = self._authorize(request)
        feedback = tuple(self._feedback.validate(item) for item in request.feedback)
        self._validate_feedback_scope(request, feedback)
        input_ids = frozenset(item.record_id for item in inputs)
        if input_ids != frozenset(request.target_record_ids):
            raise ValueError("consolidation inputs must match the authorized targets")
        pattern = self._feedback.consolidate(
            record_id=record_id,
            inputs=inputs,
            configuration_fingerprint=request.configuration_fingerprint,
        )
        timestamp = ensure_utc(created_at or utc_now())
        weakest = least_authoritative(*(item.authority_tier for item in inputs))
        receipt = ImprovementReceipt(
            receipt_id=f"improve-{record_id}",
            project_id=request.project_id,
            operation="consolidate",
            target_record_ids=request.target_record_ids,
            feedback_ids=tuple(item.feedback_id for item in feedback),
            evidence_refs=pattern.evidence_refs,
            configuration_fingerprint=request.configuration_fingerprint,
            authority_before=weakest,
            authority_after=weakest,
            trust_before=TrustClass.AGENT_GENERATED,
            trust_after=TrustClass.AGENT_GENERATED,
            created_at=timestamp,
        )
        self._record_audit(request, permission_revision, timestamp, "consolidate")
        return pattern, receipt

    def _authorize(self, request: ImprovementRequest) -> str:
        if request.profile_id not in self._profiles:
            raise PolicyDisabledError("improvement profile is not enabled")
        decision = self._authorization.require(
            AuthorizationRequest(
                principal_id=request.principal_id,
                project_id=request.project_id,
                dataset_id=request.dataset_id,
                operation="memory.improve",
                permission=Permission.WRITE_DERIVED,
                scope=request.scope,
                trace_id=request.trace_id,
                require_action_specific=True,
            )
        )
        assert decision.permission_revision is not None
        return decision.permission_revision

    @staticmethod
    def _validate_feedback_scope(
        request: ImprovementRequest,
        feedback: tuple[FeedbackRecord, ...],
    ) -> None:
        targets = frozenset(request.target_record_ids)
        if any(
            item.project_id != request.project_id or item.target_record_id not in targets
            for item in feedback
        ):
            raise ValueError("feedback falls outside the authorized improvement scope")

    def _record_audit(
        self,
        request: ImprovementRequest,
        permission_revision: str,
        timestamp: datetime,
        operation: str,
    ) -> None:
        self._audit.record(
            AuditEvent(
                event_id=f"{request.trace_id}:{operation}",
                occurred_at=timestamp,
                principal_id=request.principal_id,
                project_id=request.project_id,
                dataset_id=request.dataset_id,
                operation=f"memory.improve.{operation}",
                target_ids=request.target_record_ids,
                policy_decision="authorized-derived-only",
                outcome="succeeded",
                trace_id=request.trace_id,
                policy_id="memory-improvement-policy@1",
                permission_revision=permission_revision,
                counts=(("records", len(request.target_record_ids)),),
            )
        )
