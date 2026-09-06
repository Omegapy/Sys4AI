from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sys4ai_memory.contracts import OperationName
from sys4ai_memory.observability import (
    JsonlMetadataStore,
    OperationState,
    OperationTracker,
    OperationTransitionError,
)

START = datetime(2026, 9, 3, 18, 0, tzinfo=UTC)


def test_operation_progress_cancel_checkpoint_resume_and_reload(tmp_path: Path) -> None:
    store = JsonlMetadataStore(tmp_path.resolve(), "operations/status.jsonl")
    tracker = OperationTracker(store)
    idempotency_key = "runtime-idempotency-value"
    created = tracker.create(
        project_id="project-alpha",
        operation=OperationName.REBUILD,
        trace_id="trace_rebuild",
        idempotency_key=idempotency_key,
        total_units=10,
        created_at=START,
    )
    assert created.state is OperationState.PENDING
    replay = tracker.create(
        project_id="project-alpha",
        operation=OperationName.REBUILD,
        trace_id="trace_duplicate",
        idempotency_key=idempotency_key,
        total_units=99,
        created_at=START + timedelta(seconds=1),
    )
    assert replay == created

    running = tracker.start(created.operation_id, at=START + timedelta(seconds=1))
    progressed = tracker.update_progress(
        running.operation_id,
        completed_units=4,
        at=START + timedelta(seconds=2),
    )
    checkpointed = tracker.checkpoint(
        progressed.operation_id,
        checkpoint_ref="rebuild_checkpoint_1",
        checkpoint_metadata={
            "generation": "gen_next",
            "runtime_secret": "not-persisted-in-plaintext",
        },
        at=START + timedelta(seconds=3),
    )
    requested = tracker.request_cancel(
        checkpointed.operation_id,
        at=START + timedelta(seconds=4),
    )
    assert requested.state is OperationState.CANCEL_REQUESTED
    cancelled = tracker.acknowledge_cancel(
        requested.operation_id,
        at=START + timedelta(seconds=5),
    )
    assert cancelled.state is OperationState.CANCELLED
    resumed = tracker.resume(cancelled.operation_id, at=START + timedelta(seconds=6))
    assert resumed.state is OperationState.RUNNING
    assert resumed.attempt == 2
    completed = tracker.update_progress(
        resumed.operation_id,
        completed_units=10,
        at=START + timedelta(seconds=7),
    )
    succeeded = tracker.succeed(completed.operation_id, at=START + timedelta(seconds=8))
    assert succeeded.state is OperationState.SUCCEEDED
    assert succeeded.progress.fraction == 1.0

    serialized = store.path.read_text(encoding="utf-8")
    assert idempotency_key not in serialized
    assert "not-persisted-in-plaintext" not in serialized
    reloaded = OperationTracker(store)
    assert reloaded.get(created.operation_id) == succeeded
    assert len(store.read_payloads()) == 9


def test_operation_transitions_fail_closed_and_pending_cancel_is_terminal() -> None:
    tracker = OperationTracker()
    pending = tracker.create(
        project_id="project-alpha",
        operation=OperationName.SYNC,
        trace_id="trace_sync",
        idempotency_key="sync-key",
        retry_safe=False,
        created_at=START,
    )
    with pytest.raises(OperationTransitionError, match="running operation"):
        tracker.succeed(pending.operation_id, at=START)
    cancelled = tracker.request_cancel(pending.operation_id, at=START + timedelta(seconds=1))
    assert cancelled.state is OperationState.CANCELLED
    with pytest.raises(OperationTransitionError, match="checkpoint"):
        tracker.resume(cancelled.operation_id, at=START + timedelta(seconds=2))


def test_failed_operation_resumes_only_from_checkpoint() -> None:
    tracker = OperationTracker()
    pending = tracker.create(
        project_id="project-alpha",
        operation=OperationName.EXPORT,
        trace_id="trace_export",
        idempotency_key="export-key",
        total_units=3,
        created_at=START,
    )
    running = tracker.start(pending.operation_id, at=START + timedelta(seconds=1))
    with pytest.raises(OperationTransitionError, match="progress must be complete"):
        tracker.succeed(running.operation_id, at=START + timedelta(seconds=2))
    progressed = tracker.update_progress(
        running.operation_id,
        completed_units=1,
        at=START + timedelta(seconds=2),
    )
    with pytest.raises(OperationTransitionError, match="move backwards"):
        tracker.update_progress(
            progressed.operation_id,
            completed_units=0,
            at=START + timedelta(seconds=3),
        )
    checkpointed = tracker.checkpoint(
        progressed.operation_id,
        checkpoint_ref="export_checkpoint_1",
        checkpoint_metadata={"package_index": 1},
        at=START + timedelta(seconds=3),
    )
    failed = tracker.fail(
        checkpointed.operation_id,
        error_code="export_failed",
        warning_codes=("retry_available",),
        at=START + timedelta(seconds=4),
    )
    assert failed.state is OperationState.FAILED
    resumed = tracker.resume(failed.operation_id, at=START + timedelta(seconds=5))
    assert resumed.state is OperationState.RUNNING
    assert resumed.error_code is None


def test_missing_status_and_blank_idempotency_fail_closed() -> None:
    tracker = OperationTracker()
    with pytest.raises(KeyError, match="not found"):
        tracker.get("op_missing")
    with pytest.raises(ValueError, match="must not be blank"):
        tracker.create(
            project_id="project-alpha",
            operation=OperationName.SYNC,
            trace_id="trace_sync",
            idempotency_key=" ",
            created_at=START,
        )
    with pytest.raises(ValueError, match="byte bound"):
        tracker.create(
            project_id="project-alpha",
            operation=OperationName.SYNC,
            trace_id="trace_sync",
            idempotency_key="x" * 4097,
            created_at=START,
        )


def test_operation_idempotency_keys_cannot_cross_operation_scope() -> None:
    tracker = OperationTracker()
    tracker.create(
        project_id="project-alpha",
        operation=OperationName.SYNC,
        trace_id="trace_sync",
        idempotency_key="shared-key",
        created_at=START,
    )
    with pytest.raises(OperationTransitionError, match="another project or operation"):
        tracker.create(
            project_id="project-alpha",
            operation=OperationName.REBUILD,
            trace_id="trace_rebuild",
            idempotency_key="shared-key",
            created_at=START,
        )


def test_only_declared_long_running_operations_can_be_tracked() -> None:
    tracker = OperationTracker()
    with pytest.raises(ValueError, match="does not use"):
        tracker.create(
            project_id="project-alpha",
            operation=OperationName.HEALTH,
            trace_id="trace_health",
            idempotency_key="health-key",
            created_at=START,
        )
