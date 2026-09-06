from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import AuthorityTier, MemoryScope, ScopeReference, TrustClass
from sys4ai_memory.policies import (
    APPROVED_EXPLICIT_TYPED_FEEDBACK_POLICY,
    APPROVED_LOCAL_RETENTION_POLICY,
    AuthorizedImprovementService,
    ConsolidationInput,
    EpisodicEntry,
    EpisodicMemoryStore,
    FeedbackOrigin,
    FeedbackPolicy,
    FeedbackRecord,
    FeedbackService,
    ImprovementRequest,
    ImprovementSuggestionKind,
    RetentionPolicy,
    SessionEntry,
    SessionMemoryStore,
)
from sys4ai_memory.security import (
    InMemoryAuditSink,
    PolicyDisabledError,
    ProjectBoundary,
    SecretDetectedError,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


class _SessionPersistence:
    def __init__(self) -> None:
        self.saved: list[str] = []
        self.deleted: list[str] = []

    def save(self, entry: SessionEntry) -> None:
        self.saved.append(entry.entry_id)

    def delete(self, entry_ids: tuple[str, ...]) -> None:
        self.deleted.extend(entry_ids)


class _EpisodicPersistence:
    def __init__(self) -> None:
        self.saved: list[str] = []
        self.deleted: list[str] = []

    def save(self, entry: EpisodicEntry) -> None:
        self.saved.append(entry.episode_id)

    def delete(self, episode_ids: tuple[str, ...]) -> None:
        self.deleted.extend(episode_ids)


def _session_entry(*, expires_at: datetime = NOW + timedelta(minutes=5)) -> SessionEntry:
    return SessionEntry(
        entry_id="session-entry-1",
        project_id="project-a",
        session_id="session-a",
        scope=ScopeReference(level=MemoryScope.SESSION, scope_id="session-a"),
        content={"context": "temporary"},
        created_at=NOW,
        expires_at=expires_at,
        trust_class=TrustClass.USER_SUPPLIED,
    )


def _episode(*, expires_at: datetime = NOW + timedelta(days=1)) -> EpisodicEntry:
    return EpisodicEntry(
        episode_id="episode-1",
        project_id="project-a",
        task_id="task-a",
        actor_id="agent-a",
        started_at=NOW,
        completed_at=NOW + timedelta(minutes=1),
        tools=("pytest",),
        input_refs=("src_input",),
        output_refs=("artifact_output",),
        outcome="targeted tests passed",
        related_record_ids=("mem_related",),
        rationale_summary="The observed result supports the bounded change.",
        evidence_refs=("receipt_test",),
        expires_at=expires_at,
    )


def test_session_store_expires_and_deletes_only_session_entries() -> None:
    store = SessionMemoryStore()
    entry = _session_entry()
    store.put(entry)
    assert store.get(entry.entry_id, now=NOW + timedelta(minutes=1)) == entry
    assert store.get(entry.entry_id, now=NOW + timedelta(minutes=6)) is None

    store.put(entry)
    assert store.delete_session("another-session") == ()
    assert store.delete_session("session-a") == (entry.entry_id,)
    assert store.get(entry.entry_id, now=NOW) is None


def test_durable_retention_is_disabled_until_durations_are_approved() -> None:
    pending = RetentionPolicy(status="pending-user-decision")
    with pytest.raises(PolicyDisabledError):
        SessionMemoryStore(retention_policy=pending, persistence=_SessionPersistence())
    with pytest.raises(PolicyDisabledError):
        EpisodicMemoryStore(retention_policy=pending, persistence=_EpisodicPersistence())

    approved = RetentionPolicy(
        status="approved",
        policy_id="retention@1",
        session_ttl_seconds=600,
        episodic_ttl_seconds=172800,
    )
    persistence = _SessionPersistence()
    store = SessionMemoryStore(retention_policy=approved, persistence=persistence)
    store.put(_session_entry())
    assert store.durable_enabled
    assert persistence.saved == ["session-entry-1"]


def test_product_retention_policy_is_exact_and_does_not_silently_extend() -> None:
    policy = APPROVED_LOCAL_RETENTION_POLICY
    assert policy.session_ttl_seconds == 72 * 60 * 60
    assert policy.episodic_ttl_seconds == 365 * 24 * 60 * 60

    sessions = SessionMemoryStore(
        retention_policy=policy,
        persistence=_SessionPersistence(),
    )
    with pytest.raises(ValueError, match="exceeds the approved retention TTL"):
        sessions.put(_session_entry(expires_at=NOW + timedelta(hours=73)))


def test_approved_retention_ttl_is_enforced() -> None:
    approved = RetentionPolicy(
        status="approved",
        policy_id="retention@1",
        session_ttl_seconds=60,
        episodic_ttl_seconds=60,
    )
    sessions = SessionMemoryStore(
        retention_policy=approved,
        persistence=_SessionPersistence(),
    )
    episodes = EpisodicMemoryStore(
        retention_policy=approved,
        persistence=_EpisodicPersistence(),
    )

    with pytest.raises(ValueError, match="session expiration"):
        sessions.put(_session_entry(expires_at=NOW + timedelta(minutes=2)))
    with pytest.raises(ValueError, match="episode expiration"):
        episodes.record(_episode(expires_at=NOW + timedelta(minutes=3)))


def test_episodic_records_use_references_and_expire() -> None:
    store = EpisodicMemoryStore()
    entry = _episode()
    store.record(entry)
    assert entry.authority_tier is AuthorityTier.AGENT_DURABLE_MATERIAL
    assert not entry.durable_authority
    assert store.get(entry.episode_id, now=NOW + timedelta(hours=1)) == entry
    assert store.purge_expired(now=NOW + timedelta(days=2)) == (entry.episode_id,)

    with pytest.raises(SecretDetectedError):
        EpisodicEntry.model_validate(
            {
                **entry.model_dump(),
                "rationale_summary": "password=" + "runtime-only-value",
            }
        )


def _feedback(*, automatic: bool = False) -> FeedbackRecord:
    return FeedbackRecord(
        feedback_id="feedback-1",
        project_id="project-a",
        target_record_id="mem_target",
        origin=FeedbackOrigin.VALIDATION_RESULT,
        actor_id="agent-a",
        evidence_refs=("receipt_validation",),
        rationale_summary="The validation result contradicted the generated summary.",
        source_authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        source_trust_class=TrustClass.PROJECT_AUTHORED,
        effective_authority_tier=AuthorityTier.AGENT_DURABLE_MATERIAL,
        effective_trust_class=TrustClass.AGENT_GENERATED,
        automatic=automatic,
        created_at=NOW,
    )


def test_feedback_is_explicit_by_default_and_cannot_raise_authority() -> None:
    service = FeedbackService()
    assert service.validate(_feedback()) == _feedback()
    with pytest.raises(PolicyDisabledError):
        service.validate(_feedback(automatic=True))

    invalid = _feedback().model_dump()
    invalid["effective_authority_tier"] = AuthorityTier.SYS4AI_GOVERNANCE
    with pytest.raises(ValidationError, match="cannot raise"):
        FeedbackRecord.model_validate(invalid)


def test_product_feedback_policy_collects_no_automatic_signals() -> None:
    policy = APPROVED_EXPLICIT_TYPED_FEEDBACK_POLICY
    assert policy.status == "approved"
    assert policy.automatic_collection is False
    assert policy.allowed_automatic_origins == frozenset()
    assert FeedbackService(policy).validate(_feedback()) == _feedback()
    with pytest.raises(PolicyDisabledError, match="automatic feedback"):
        FeedbackService(policy).validate(_feedback(automatic=True))


def test_provider_reweight_receipt_preserves_authority_and_trust() -> None:
    receipt = FeedbackService.reweight_receipt(
        receipt_id="improve-1",
        project_id="project-a",
        record_id="mem_target",
        feedback_ids=("feedback-1",),
        evidence_refs=("receipt_validation",),
        configuration_fingerprint="a" * 64,
        authority=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust=TrustClass.PROJECT_AUTHORED,
        created_at=NOW,
    )
    assert receipt.authority_after is receipt.authority_before
    assert receipt.trust_after is receipt.trust_before


def test_consolidation_keeps_evidence_and_rejects_false_consensus() -> None:
    first = ConsolidationInput(
        record_id="mem_first",
        authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust_class=TrustClass.PROJECT_AUTHORED,
        evidence_refs=("src_first",),
    )
    second = ConsolidationInput(
        record_id="mem_second",
        authority_tier=AuthorityTier.EXTERNAL_EVIDENCE,
        trust_class=TrustClass.EXTERNAL_UNVERIFIED,
        evidence_refs=("src_second",),
    )
    pattern = FeedbackService.consolidate(
        record_id="mem_pattern",
        inputs=(first, second),
        configuration_fingerprint="b" * 64,
    )
    assert pattern.generated
    assert pattern.source_record_ids == ("mem_first", "mem_second")
    assert pattern.evidence_refs == ("src_first", "src_second")
    assert pattern.authority_tier is AuthorityTier.AGENT_DURABLE_MATERIAL
    assert not pattern.canonical

    conflicting = second.model_copy(update={"conflicts_with": frozenset({"mem_first"})})
    with pytest.raises(ValueError, match="remain separate"):
        FeedbackService.consolidate(
            record_id="mem_false-consensus",
            inputs=(first, conflicting),
            configuration_fingerprint="c" * 64,
        )


def test_pending_feedback_policy_cannot_enable_automatic_collection() -> None:
    with pytest.raises(ValidationError, match="must remain disabled"):
        FeedbackPolicy(
            status="pending-user-decision",
            automatic_collection=True,
            allowed_automatic_origins=frozenset({FeedbackOrigin.RETRIEVAL_SELECTION}),
        )


@pytest.mark.parametrize("kind", tuple(ImprovementSuggestionKind))
def test_improvement_can_classify_records_for_review_without_active_change(
    kind: ImprovementSuggestionKind,
) -> None:
    suggestion = FeedbackService.suggest_for_review(
        target_record_id="mem_target",
        kind=kind,
        evidence_refs=("receipt_validation",),
    )

    assert suggestion.kind is kind
    assert suggestion.evidence_refs == ("receipt_validation",)
    assert suggestion.active_change_performed is False


def test_improvement_is_scoped_to_canonical_dataset_and_enabled_profile(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    permission_path = root / "canonical" / "permissions.json"
    permission_path.parent.mkdir()
    permission_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "revision": "perm-improve-1",
                "project_id": "project-a",
                "dataset_id": "dataset-a",
                "issued_at": "2026-09-03T12:00:00Z",
                "grants": [
                    {
                        "grant_id": "grant-improver",
                        "principal_id": "agent-a",
                        "permissions": ["write-derived"],
                        "operations": ["memory.improve"],
                        "scopes": [
                            {
                                "level": "project",
                                "scope_id": "project-a",
                                "parent_scopes": [],
                            }
                        ],
                        "target_prefixes": [],
                        "shared_project_ids": [],
                        "valid_until": None,
                    }
                ],
                "approval_policy": None,
            }
        ),
        encoding="utf-8",
    )
    boundary = ProjectBoundary("project-a", "dataset-a", root)
    authorization = AuthorizationService(
        CanonicalPermissionEnvelopeLoader(boundary, "canonical/permissions.json")
    )
    audit = InMemoryAuditSink()
    service = AuthorizedImprovementService(
        authorization,
        enabled_profile_ids=frozenset({"base@1"}),
        audit=audit,
    )
    request = ImprovementRequest(
        principal_id="agent-a",
        project_id="project-a",
        dataset_id="dataset-a",
        profile_id="base@1",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a"),
        trace_id="trace-improve",
        target_record_ids=("mem_target",),
        feedback=(_feedback(),),
        configuration_fingerprint="d" * 64,
    )

    receipt = service.reweight(
        request,
        receipt_id="improve-authorized",
        authority=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust=TrustClass.PROJECT_AUTHORED,
        created_at=NOW,
    )

    assert receipt.target_record_ids == ("mem_target",)
    assert audit.events()[0].principal_id == "agent-a"
    assert audit.events()[0].operation == "memory.improve.reweight"

    first_feedback = _feedback().model_copy(
        update={"feedback_id": "feedback-first", "target_record_id": "mem_first"}
    )
    second_feedback = _feedback().model_copy(
        update={"feedback_id": "feedback-second", "target_record_id": "mem_second"}
    )
    consolidation_request = request.model_copy(
        update={
            "target_record_ids": ("mem_first", "mem_second"),
            "feedback": (first_feedback, second_feedback),
        }
    )
    inputs = (
        ConsolidationInput(
            record_id="mem_first",
            authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
            trust_class=TrustClass.PROJECT_AUTHORED,
            evidence_refs=("src_first",),
        ),
        ConsolidationInput(
            record_id="mem_second",
            authority_tier=AuthorityTier.EXTERNAL_EVIDENCE,
            trust_class=TrustClass.EXTERNAL_UNVERIFIED,
            evidence_refs=("src_second",),
        ),
    )
    pattern, consolidation_receipt = service.consolidate(
        consolidation_request,
        record_id="mem_failure_pattern",
        inputs=inputs,
        created_at=NOW,
    )
    assert pattern.source_record_ids == ("mem_first", "mem_second")
    assert pattern.evidence_refs == ("src_first", "src_second")
    assert pattern.authority_tier is AuthorityTier.AGENT_DURABLE_MATERIAL
    assert not pattern.canonical
    assert consolidation_receipt.operation == "consolidate"
    assert consolidation_receipt.feedback_ids == ("feedback-first", "feedback-second")
    assert audit.events()[-1].operation == "memory.improve.consolidate"

    with pytest.raises(ValueError, match="authorized targets"):
        service.consolidate(
            consolidation_request,
            record_id="mem_mismatched_pattern",
            inputs=(inputs[0],),
            created_at=NOW,
        )

    with pytest.raises(PolicyDisabledError, match="profile"):
        AuthorizedImprovementService(
            authorization,
            enabled_profile_ids=frozenset(),
        ).reweight(
            request,
            receipt_id="improve-disabled",
            authority=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
            trust=TrustClass.PROJECT_AUTHORED,
            created_at=NOW,
        )
