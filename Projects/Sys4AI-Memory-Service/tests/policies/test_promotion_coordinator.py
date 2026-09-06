from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.contracts import MemoryScope, ScopeReference
from sys4ai_memory.policies import (
    CanonicalPromotionCoordinator,
    CanonicalPromotionPlanner,
    CanonicalPromotionReceipt,
    CanonicalPromotionRecoveryRequiredError,
    CanonicalPromotionRequest,
    CanonicalPromotionRolledBackError,
    CanonicalRollbackReceipt,
    CanonicalSourceSynchronizationReceipt,
    CanonicalSourceSynchronizationRequest,
    CanonicalWriteReceipt,
    PreparedCanonicalWrite,
    PromotionRecoveryState,
    ReviewDisposition,
    ReviewReceipt,
    SourceSynchronizationMode,
    StagedProposalArtifact,
)
from sys4ai_memory.security import IdempotencyConflictError, ProjectBoundary
from sys4ai_memory.util import atomic_write_text, sha256_bytes, sha256_file

from .test_staging_and_review import _components, _proposal, _write_permissions

NOW = datetime(2026, 9, 3, 12, 30, tzinfo=UTC)


class _FixtureRepository:
    def __init__(
        self,
        target: Path,
        replacement: str,
        events: list[str],
        *,
        after_prepare: Callable[[], None] | None = None,
        fail_commit_after_write: bool = False,
        fail_rollback: bool = False,
    ) -> None:
        self.target = target
        self.replacement = replacement
        self.events = events
        self.after_prepare = after_prepare
        self.fail_commit_after_write = fail_commit_after_write
        self.fail_rollback = fail_rollback
        self.before_exists = target.exists()
        self.before = target.read_text(encoding="utf-8") if self.before_exists else ""

    def prepare(
        self,
        request: CanonicalPromotionRequest,
        *,
        operation_id: str,
    ) -> PreparedCanonicalWrite:
        assert sha256_bytes(self.before.encode("utf-8")) == request.base_content_sha256
        assert sha256_bytes(self.replacement.encode("utf-8")) == request.proposed_content_sha256
        self.events.append("repository.prepare")
        prepared = PreparedCanonicalWrite(
            transaction_id=operation_id,
            proposal_id=request.proposal_id,
            proposal_digest=request.proposal_digest,
            target_path=request.target_path,
            before_sha256=request.base_content_sha256,
            after_sha256=request.proposed_content_sha256,
            repository_change_ref="fixture-change-1",
            repository_review_ref="fixture-review-1",
        )
        if self.after_prepare is not None:
            self.after_prepare()
        return prepared

    def commit(self, prepared: PreparedCanonicalWrite) -> CanonicalWriteReceipt:
        self.events.append("repository.commit")
        atomic_write_text(self.target, self.replacement)
        if self.fail_commit_after_write:
            raise RuntimeError("fixture commit failed after replacement")
        return CanonicalWriteReceipt(
            transaction_id=prepared.transaction_id,
            target_path=prepared.target_path,
            before_sha256=prepared.before_sha256,
            after_sha256=prepared.after_sha256,
            repository_change_ref=prepared.repository_change_ref,
            repository_review_ref=prepared.repository_review_ref,
            committed_at=NOW,
        )

    def rollback(
        self,
        prepared: PreparedCanonicalWrite,
        committed: CanonicalWriteReceipt | None,
    ) -> CanonicalRollbackReceipt:
        del committed
        self.events.append("repository.rollback")
        if self.fail_rollback:
            raise RuntimeError("fixture rollback failed")
        if self.before_exists:
            atomic_write_text(self.target, self.before)
        else:
            self.target.unlink(missing_ok=True)
        return CanonicalRollbackReceipt(
            transaction_id=prepared.transaction_id,
            target_path=prepared.target_path,
            restored_sha256=prepared.before_sha256,
            repository_change_ref=prepared.repository_change_ref,
            rolled_back_at=NOW,
        )


class _FixtureSynchronizer:
    def __init__(
        self,
        target: Path,
        events: list[str],
        *,
        fail_promotion: bool = False,
        fail_rollback: bool = False,
        wrong_promotion_digest: bool = False,
    ) -> None:
        self.target = target
        self.events = events
        self.fail_promotion = fail_promotion
        self.fail_rollback = fail_rollback
        self.wrong_promotion_digest = wrong_promotion_digest

    def synchronize(
        self,
        request: CanonicalSourceSynchronizationRequest,
    ) -> CanonicalSourceSynchronizationReceipt:
        self.events.append(f"source.synchronize:{request.mode.value}")
        if request.mode is SourceSynchronizationMode.PROMOTION and self.fail_promotion:
            raise RuntimeError("fixture promotion synchronization failed")
        if request.mode is SourceSynchronizationMode.ROLLBACK and self.fail_rollback:
            raise RuntimeError("fixture rollback synchronization failed")
        observed = sha256_file(self.target) if self.target.exists() else sha256_bytes(b"")
        if request.mode is SourceSynchronizationMode.PROMOTION and self.wrong_promotion_digest:
            observed = "f" * 64
        return CanonicalSourceSynchronizationReceipt(
            synchronization_id=f"sync-{request.mode.value}",
            transaction_id=request.transaction_id,
            project_id=request.project_id,
            dataset_id=request.dataset_id,
            target_path=request.target_path,
            synchronized_content_sha256=observed,
            repository_change_ref=request.repository_change_ref,
            mode=request.mode,
            source_ids=("src_control-decision",),
            completed_at=NOW,
        )


def _approved_fixture(
    root: Path,
) -> tuple[
    ProjectBoundary,
    CanonicalPromotionPlanner,
    tuple[StagedProposalArtifact, ReviewReceipt, ScopeReference],
    Path,
]:
    target = root / "control" / "decision.md"
    target.parent.mkdir()
    target.write_text("old value\n", encoding="utf-8")
    _write_permissions(root, reviewer_policy=True)
    boundary, stager, gate, planner = _components(root)
    artifact = stager.stage(_proposal(), trace_id="trace-stage")
    scope = ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a")
    review = gate.decide(
        artifact,
        reviewer_id="reviewer-a",
        project_id="project-a",
        dataset_id="dataset-a",
        scope=scope,
        record_type="Decision",
        disposition=ReviewDisposition.APPROVED,
        rationale_summary="Evidence supports the governed project change.",
        trace_id="trace-review",
        reviewed_at=NOW,
    )
    return boundary, planner, (artifact, review, scope), target


def _execute(
    coordinator: CanonicalPromotionCoordinator,
    approved: tuple[StagedProposalArtifact, ReviewReceipt, ScopeReference],
    *,
    idempotency_key: str = "promotion-key-1",
) -> CanonicalPromotionReceipt:
    artifact, review, scope = approved
    return coordinator.execute(
        artifact,
        review,
        project_id="project-a",
        dataset_id="dataset-a",
        scope=scope,
        record_type="Decision",
        trace_id="trace-promote",
        idempotency_key=idempotency_key,
    )


def test_promotion_reports_success_only_after_canonical_sync_and_replays_idempotently(
    tmp_path: Path,
) -> None:
    boundary, planner, approved, target = _approved_fixture(tmp_path.resolve())
    events: list[str] = []
    repository = _FixtureRepository(target, "new value\n", events)
    synchronizer = _FixtureSynchronizer(target, events)
    coordinator = CanonicalPromotionCoordinator(boundary, planner, repository, synchronizer)

    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = tuple(pool.map(lambda _: _execute(coordinator, approved), range(16)))

    assert target.read_text(encoding="utf-8") == "new value\n"
    assert len({receipt.operation_id for receipt in receipts}) == 1
    receipt = receipts[0]
    assert receipt.public_result == "succeeded"
    assert receipt.canonical_write_performed
    assert receipt.synchronization_completed
    assert not receipt.separate_memory_write_performed
    assert receipt.source_synchronization.source_ids == ("src_control-decision",)
    assert events == [
        "repository.prepare",
        "repository.commit",
        "source.synchronize:promotion",
    ]


def test_failed_source_sync_restores_canonical_and_resynchronizes_prior_content(
    tmp_path: Path,
) -> None:
    boundary, planner, approved, target = _approved_fixture(tmp_path.resolve())
    events: list[str] = []
    repository = _FixtureRepository(target, "new value\n", events)
    synchronizer = _FixtureSynchronizer(target, events, fail_promotion=True)
    coordinator = CanonicalPromotionCoordinator(boundary, planner, repository, synchronizer)

    with pytest.raises(CanonicalPromotionRolledBackError) as caught:
        _execute(coordinator, approved)

    assert target.read_text(encoding="utf-8") == "old value\n"
    assert caught.value.receipt.public_result == "failed"
    assert caught.value.receipt.recovery_state is PromotionRecoveryState.ROLLED_BACK
    assert caught.value.receipt.canonical_restored
    assert caught.value.receipt.derived_state_reconciled
    assert events == [
        "repository.prepare",
        "repository.commit",
        "source.synchronize:promotion",
        "repository.rollback",
        "source.synchronize:rollback",
    ]


def test_mismatched_sync_evidence_cannot_produce_success(tmp_path: Path) -> None:
    boundary, planner, approved, target = _approved_fixture(tmp_path.resolve())
    events: list[str] = []
    coordinator = CanonicalPromotionCoordinator(
        boundary,
        planner,
        _FixtureRepository(target, "new value\n", events),
        _FixtureSynchronizer(target, events, wrong_promotion_digest=True),
    )

    with pytest.raises(CanonicalPromotionRolledBackError) as caught:
        _execute(coordinator, approved)

    assert target.read_text(encoding="utf-8") == "old value\n"
    assert caught.value.receipt.failed_phase == "synchronize_canonical_source"
    assert caught.value.receipt.recovery_state is PromotionRecoveryState.ROLLED_BACK


def test_failed_rollback_returns_recovery_required_and_never_success(
    tmp_path: Path,
) -> None:
    boundary, planner, approved, target = _approved_fixture(tmp_path.resolve())
    events: list[str] = []
    repository = _FixtureRepository(
        target,
        "new value\n",
        events,
        fail_commit_after_write=True,
        fail_rollback=True,
    )
    synchronizer = _FixtureSynchronizer(target, events)
    coordinator = CanonicalPromotionCoordinator(boundary, planner, repository, synchronizer)

    with pytest.raises(CanonicalPromotionRecoveryRequiredError) as caught:
        _execute(coordinator, approved)

    assert target.read_text(encoding="utf-8") == "new value\n"
    assert caught.value.receipt.public_result == "failed"
    assert caught.value.receipt.recovery_state is PromotionRecoveryState.RECOVERY_REQUIRED
    assert not caught.value.receipt.canonical_restored
    assert events == [
        "repository.prepare",
        "repository.commit",
        "repository.rollback",
    ]
    with pytest.raises(CanonicalPromotionRecoveryRequiredError) as replay:
        _execute(coordinator, approved)
    assert replay.value.receipt == caught.value.receipt
    assert events == [
        "repository.prepare",
        "repository.commit",
        "repository.rollback",
    ]


def test_permission_change_after_prepare_aborts_before_canonical_commit(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    boundary, planner, approved, target = _approved_fixture(root)
    events: list[str] = []
    repository = _FixtureRepository(
        target,
        "new value\n",
        events,
        after_prepare=lambda: _write_permissions(
            root,
            reviewer_policy=True,
            allow_approve=False,
        ),
    )
    coordinator = CanonicalPromotionCoordinator(
        boundary,
        planner,
        repository,
        _FixtureSynchronizer(target, events),
    )

    with pytest.raises(CanonicalPromotionRolledBackError) as caught:
        _execute(coordinator, approved)

    assert target.read_text(encoding="utf-8") == "old value\n"
    assert caught.value.receipt.failed_phase == "revalidate_review_and_target"
    assert events == ["repository.prepare", "repository.rollback"]


def test_completed_promotion_rejects_changed_attempt_with_same_idempotency_key(
    tmp_path: Path,
) -> None:
    boundary, planner, approved, target = _approved_fixture(tmp_path.resolve())
    events: list[str] = []
    coordinator = CanonicalPromotionCoordinator(
        boundary,
        planner,
        _FixtureRepository(target, "new value\n", events),
        _FixtureSynchronizer(target, events),
    )
    _execute(coordinator, approved)
    artifact, review, scope = approved
    changed_review = review.model_copy(update={"rationale_summary": "A different review."})

    with pytest.raises(IdempotencyConflictError):
        _execute(coordinator, (artifact, changed_review, scope))
