from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sys4ai_memory.contracts import AuthorityTier, RecordStatus, Sensitivity, TrustClass
from sys4ai_memory.lifecycle import LifecycleCatalog, LifecycleRecord, LifecycleStateError

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


def _record(record_id: str, *, status: RecordStatus = RecordStatus.ACTIVE) -> LifecycleRecord:
    return LifecycleRecord(
        record_id=record_id,
        project_id="project-a",
        dataset_id="dataset-a",
        status=status,
        authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust_class=TrustClass.PROJECT_AUTHORED,
        sensitivity=Sensitivity.INTERNAL,
        canonical=True,
        source_ids=("src_source",),
        valid_from=NOW,
    )


def test_supersession_preserves_bidirectional_history_and_current_filter() -> None:
    catalog = LifecycleCatalog()
    catalog.add(_record("mem_prior"))
    catalog.add(_record("mem_replacement"))

    prior, replacement = catalog.supersede("mem_prior", "mem_replacement")

    assert prior.status is RecordStatus.SUPERSEDED
    assert prior.superseded_by == ("mem_replacement",)
    assert replacement.supersedes == ("mem_prior",)
    assert [
        item.record_id for item in catalog.query(project_id="project-a", dataset_id="dataset-a")
    ] == ["mem_replacement"]
    assert [
        item.record_id
        for item in catalog.query(
            project_id="project-a",
            dataset_id="dataset-a",
            historical=True,
        )
    ] == ["mem_prior", "mem_replacement"]
    assert catalog.supersede("mem_prior", "mem_replacement") == (prior, replacement)


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        ("invalidate", RecordStatus.INVALIDATED),
        ("expire", RecordStatus.EXPIRED),
        ("withdraw", RecordStatus.WITHDRAWN),
        ("mark_deleted", RecordStatus.DELETED),
    ],
)
def test_active_lifecycle_transitions_leave_history(method: str, expected: RecordStatus) -> None:
    catalog = LifecycleCatalog()
    catalog.add(_record("mem_target"))

    transitioned = getattr(catalog, method)("mem_target")

    assert transitioned.status is expected
    assert catalog.query(project_id="project-a", dataset_id="dataset-a") == ()
    assert catalog.query(
        project_id="project-a",
        dataset_id="dataset-a",
        historical=True,
    ) == (transitioned,)


def test_proposal_review_activation_and_rejection_transitions() -> None:
    catalog = LifecycleCatalog()
    catalog.add(_record("mem_candidate", status=RecordStatus.PROPOSED))
    assert catalog.transition("mem_candidate", RecordStatus.STAGED).status is RecordStatus.STAGED
    assert (
        catalog.transition("mem_candidate", RecordStatus.APPROVED).status is RecordStatus.APPROVED
    )
    assert catalog.transition("mem_candidate", RecordStatus.ACTIVE).status is RecordStatus.ACTIVE

    catalog.add(_record("mem_rejected", status=RecordStatus.PROPOSED))
    rejected = catalog.transition("mem_rejected", RecordStatus.REJECTED)
    assert rejected.status is RecordStatus.REJECTED
    assert catalog.transition("mem_rejected", RecordStatus.DELETED).status is RecordStatus.DELETED

    catalog.add(_record("mem_withdrawn", status=RecordStatus.STAGED))
    assert (
        catalog.transition("mem_withdrawn", RecordStatus.WITHDRAWN).status is RecordStatus.WITHDRAWN
    )


def test_invalid_transition_and_cross_project_supersession_are_denied() -> None:
    catalog = LifecycleCatalog()
    catalog.add(_record("mem_active"))
    with pytest.raises(LifecycleStateError, match="invalid lifecycle transition"):
        catalog.transition("mem_active", RecordStatus.APPROVED)

    other = _record("mem_other").model_copy(update={"project_id": "project-b"})
    catalog.add(other)
    with pytest.raises(LifecycleStateError, match="cross project"):
        catalog.supersede("mem_active", "mem_other")
