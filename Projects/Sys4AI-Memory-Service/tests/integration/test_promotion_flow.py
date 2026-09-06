from __future__ import annotations

import json
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import ErrorCategory, ErrorEnvelope, OperationName
from sys4ai_memory.interfaces import DispatchRequest, DispatchSuccess, InterfaceIdentity
from sys4ai_memory.policies import (
    AuthorizedWritePolicy,
    CanonicalPromotionCoordinator,
    CanonicalPromotionPlanner,
    ProposalStager,
    ReviewerAuthorizationGate,
    WritePolicyEngine,
)
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import ProposalSubmission, ServiceComponents
from tests.policies.test_promotion_coordinator import (
    _FixtureRepository,
    _FixtureSynchronizer,
)
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _request, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]


def _with_principal(request: DispatchRequest, principal_id: str) -> DispatchRequest:
    identity = InterfaceIdentity(
        principal_id=principal_id,
        agent_type="test-agent",
        run_id=f"run-{principal_id}",
    )
    return request.model_copy(
        update={
            "authorization": request.authorization.model_copy(
                update={"identity": identity}
            )
        }
    )


def _install_review_policy(permission_path: Path) -> None:
    document = json.loads(permission_path.read_text(encoding="utf-8"))
    document["revision"] = "permissions-promotion-integration-1"
    document["approval_policy"] = {
        "status": "approved",
        "policy_id": "review-policy-integration@1",
        "reviewers": [
            {
                "principal_id": "agent-service",
                "kind": "human",
                "higher_system_policy_ref": None,
            }
        ],
        "record_types": ["Decision"],
        "target_prefixes": ["control"],
        "human_review_required": True,
    }
    document["grants"].append(
        {
            "grant_id": "promotion-author",
            "principal_id": "agent-author",
            "permissions": ["propose"],
            "operations": ["memory.propose"],
            "scopes": [
                {
                    "level": "project",
                    "scope_id": PROJECT_ID,
                    "parent_scopes": [],
                }
            ],
            "target_prefixes": [],
            "shared_project_ids": [],
            "valid_until": None,
        }
    )
    permission_path.write_text(json.dumps(document), encoding="utf-8")


def _submission() -> ProposalSubmission:
    return ProposalSubmission.model_validate(
        {
            "proposal_id": "mwp_promotion-integration",
            "project_id": PROJECT_ID,
            "requester": {
                "principal_id": "agent-author",
                "agent_type": "test-agent",
                "run_id": "run-agent-author",
            },
            "requested_record_type": "Decision",
            "requested_scope": {
                "level": "project",
                "scope_id": PROJECT_ID,
                "parent_scopes": [],
            },
            "requested_target": {"path": "control/decision.md"},
            "proposal": {
                "title": "Promote reviewed decision",
                "content": "new value\n",
            },
            "evidence": [{"source_id": "src_promotion-evidence"}],
            "trust_class": "agent-generated",
            "sensitivity": "internal",
            "authority_tier": "A5",
            "target_class": "decision",
            "requested_status": "proposed",
            "created_at": "2026-09-03T18:00:00Z",
            "base_content": "old value\n",
        }
    )


def test_public_approval_reports_success_only_after_canonical_sync(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    target = root / "control/decision.md"
    target.parent.mkdir(parents=True)
    target.write_text("old value\n", encoding="utf-8")
    components = ServiceComponents()
    service, _, permission_path = _service(root, components=components)
    _install_review_policy(permission_path)

    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    authorization = AuthorizationService(loader)
    stager = ProposalStager(boundary, ".sys4ai/memory/staging", authorization)
    reviewer = ReviewerAuthorizationGate(authorization, loader)
    planner = CanonicalPromotionPlanner(boundary, reviewer)
    events: list[str] = []
    components.write_policy = AuthorizedWritePolicy(WritePolicyEngine(), authorization)
    components.proposal_stager = stager
    components.reviewer_gate = reviewer
    components.promotion = CanonicalPromotionCoordinator(
        boundary,
        planner,
        _FixtureRepository(target, "new value\n", events),
        _FixtureSynchronizer(target, events),
    )

    proposed = service.dispatch(
        _with_principal(
            _request(
                OperationName.PROPOSE,
                {"proposal": _submission().model_dump(mode="json")},
                suffix="promotion_propose",
                idempotency_key="promotion-propose-key",
            ),
            "agent-author",
        )
    )
    assert isinstance(proposed, DispatchSuccess)
    assert proposed.result["effect"] == "stage_for_review"
    assert target.read_text(encoding="utf-8") == "old value\n"

    approved = service.dispatch(
        _request(
            OperationName.APPROVE,
            {
                "proposal_id": "mwp_promotion-integration",
                "decision": "approve",
                "reason": "The evidence supports this canonical change.",
            },
            suffix="promotion_approve",
            idempotency_key="promotion-approve-key",
        )
    )

    assert isinstance(approved, DispatchSuccess)
    assert approved.result["promotion_request"] is None
    receipt = approved.result["promotion_receipt"]
    assert isinstance(receipt, dict)
    assert receipt["public_result"] == "succeeded"
    assert receipt["canonical_write_performed"] is True
    assert receipt["synchronization_completed"] is True
    assert receipt["separate_memory_write_performed"] is False
    assert target.read_text(encoding="utf-8") == "new value\n"
    assert events == [
        "repository.prepare",
        "repository.commit",
        "source.synchronize:promotion",
    ]


def test_public_promotion_failure_after_write_is_compensated_before_error(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    target = root / "control/decision.md"
    target.parent.mkdir(parents=True)
    target.write_text("old value\n", encoding="utf-8")
    components = ServiceComponents()
    service, audit, permission_path = _service(root, components=components)
    _install_review_policy(permission_path)

    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    authorization = AuthorizationService(loader)
    stager = ProposalStager(boundary, ".sys4ai/memory/staging", authorization)
    reviewer = ReviewerAuthorizationGate(authorization, loader)
    planner = CanonicalPromotionPlanner(boundary, reviewer)
    events: list[str] = []
    components.write_policy = AuthorizedWritePolicy(WritePolicyEngine(), authorization)
    components.proposal_stager = stager
    components.reviewer_gate = reviewer
    components.promotion = CanonicalPromotionCoordinator(
        boundary,
        planner,
        _FixtureRepository(
            target,
            "new value\n",
            events,
            fail_commit_after_write=True,
        ),
        _FixtureSynchronizer(target, events),
    )

    proposed = service.dispatch(
        _with_principal(
            _request(
                OperationName.PROPOSE,
                {"proposal": _submission().model_dump(mode="json")},
                suffix="rollback_propose",
                idempotency_key="rollback-propose-key",
            ),
            "agent-author",
        )
    )
    assert isinstance(proposed, DispatchSuccess)
    artifact = proposed.result["artifact"]
    assert isinstance(artifact, dict)
    artifact_directory = root / str(artifact["artifact_directory"])
    assert artifact_directory.is_dir()

    approved = service.dispatch(
        _request(
            OperationName.APPROVE,
            {
                "proposal_id": "mwp_promotion-integration",
                "decision": "approve",
                "reason": "The evidence supports this canonical change.",
            },
            suffix="promotion_rollback",
            idempotency_key="promotion-rollback-key",
        )
    )

    assert isinstance(approved, ErrorEnvelope)
    assert approved.error.category is ErrorCategory.WRITE_REJECTED
    assert approved.error.trace_id == "trace_promotion_rollback"
    assert approved.error.recoverable is False
    assert target.read_text(encoding="utf-8") == "old value\n"
    assert artifact_directory.is_dir()
    assert events == [
        "repository.prepare",
        "repository.commit",
        "repository.rollback",
        "source.synchronize:rollback",
    ]
    assert [event.outcome for event in audit.events()] == [
        "authorized",
        "succeeded",
        "authorized",
        "failed",
    ]


def test_public_rejection_purges_content_when_retention_is_unresolved(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    target = root / "control/decision.md"
    target.parent.mkdir(parents=True)
    target.write_text("old value\n", encoding="utf-8")
    components = ServiceComponents()
    service, _, permission_path = _service(root, components=components)
    _install_review_policy(permission_path)

    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    authorization = AuthorizationService(loader)
    stager = ProposalStager(boundary, ".sys4ai/memory/staging", authorization)
    components.write_policy = AuthorizedWritePolicy(WritePolicyEngine(), authorization)
    components.proposal_stager = stager
    components.reviewer_gate = ReviewerAuthorizationGate(authorization, loader)

    proposed = service.dispatch(
        _with_principal(
            _request(
                OperationName.PROPOSE,
                {"proposal": _submission().model_dump(mode="json")},
                suffix="rejection_propose",
                idempotency_key="rejection-propose-key",
            ),
            "agent-author",
        )
    )
    assert isinstance(proposed, DispatchSuccess)
    artifact = proposed.result["artifact"]
    assert isinstance(artifact, dict)
    artifact_directory = root / str(artifact["artifact_directory"])
    assert artifact_directory.is_dir()

    rejected = service.dispatch(
        _request(
            OperationName.APPROVE,
            {
                "proposal_id": "mwp_promotion-integration",
                "decision": "reject",
                "reason": "The evidence does not support this canonical change.",
            },
            suffix="promotion_reject",
            idempotency_key="promotion-reject-key",
        )
    )

    assert isinstance(rejected, DispatchSuccess)
    assert rejected.result["promotion_request"] is None
    assert rejected.result["promotion_receipt"] is None
    disposition = rejected.result["rejected_disposition"]
    assert isinstance(disposition, dict)
    assert disposition["proposal_content_removed"] is True
    assert disposition["active_knowledge"] is False
    assert disposition["retained_fields"] == []
    assert not artifact_directory.exists()
    assert target.read_text(encoding="utf-8") == "old value\n"
