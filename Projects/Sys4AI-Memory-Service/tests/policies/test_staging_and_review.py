from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
    PermissionDeniedError,
)
from sys4ai_memory.contracts import MemoryScope, PolicyAction, ScopeReference, WriteProposal
from sys4ai_memory.policies import (
    CanonicalPromotionPlanner,
    ProposalStager,
    RejectedMetadataField,
    RejectedProposalRetentionPolicy,
    ReviewDisposition,
    ReviewerAuthorizationGate,
)
from sys4ai_memory.security import (
    IdempotencyConflictError,
    PolicyDisabledError,
    ProjectBoundary,
    SecretDetectedError,
    StaleStateError,
)


def _proposal(
    *, content: str = "new value\n", idempotency_key: str = "run-a:proposal-1"
) -> WriteProposal:
    return WriteProposal.model_validate(
        {
            "schema_version": "1.0",
            "api_version": "1.0",
            "proposal_id": "mwp_test-proposal",
            "idempotency_key": idempotency_key,
            "project_id": "project-a",
            "requester": {
                "principal_id": "agent-a",
                "agent_type": "implementation-agent",
                "run_id": "run-a",
            },
            "requested_record_type": "Decision",
            "requested_scope": {
                "level": "project",
                "scope_id": "project-a",
                "parent_scopes": [],
            },
            "requested_target": {"path": "control/decision.md"},
            "proposal": {"title": "Change decision", "content": content},
            "evidence": [{"source_id": "src_evidence-a", "record_id": None}],
            "trust_class": "agent-generated",
            "sensitivity": "internal",
            "policy_result": {
                "action": "stage_for_review",
                "policy_id": "memory-write-policy@1",
                "reasons": ["Decision requires review"],
            },
            "status": "staged",
            "created_at": "2026-09-03T12:00:00Z",
        }
    )


def _write_permissions(root: Path, *, reviewer_policy: bool, allow_approve: bool = True) -> None:
    approval = None
    if reviewer_policy:
        approval = {
            "status": "approved",
            "policy_id": "review-policy@1",
            "reviewers": [
                {
                    "principal_id": "reviewer-a",
                    "kind": "human",
                    "higher_system_policy_ref": None,
                }
            ],
            "record_types": ["Decision"],
            "target_prefixes": ["control"],
            "human_review_required": True,
        }
    grants = [
        {
            "grant_id": "grant-agent-a",
            "principal_id": "agent-a",
            "permissions": ["propose"],
            "operations": ["memory.propose"],
            "scopes": [{"level": "project", "scope_id": "project-a", "parent_scopes": []}],
            "target_prefixes": ["control"],
            "shared_project_ids": [],
            "valid_until": None,
        }
    ]
    if allow_approve:
        grants.append(
            {
                "grant_id": "grant-reviewer-a",
                "principal_id": "reviewer-a",
                "permissions": ["approve"],
                "operations": ["memory.approve"],
                "scopes": [{"level": "project", "scope_id": "project-a", "parent_scopes": []}],
                "target_prefixes": ["control"],
                "shared_project_ids": [],
                "valid_until": None,
            }
        )
    document = {
        "schema_version": "1.0",
        "revision": "perm-review-1" if allow_approve else "perm-review-2",
        "project_id": "project-a",
        "dataset_id": "dataset-a",
        "issued_at": "2026-09-03T12:00:00Z",
        "grants": grants,
        "approval_policy": approval,
    }
    path = root / "canonical" / "permissions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")


def _components(
    root: Path,
) -> tuple[
    ProjectBoundary,
    ProposalStager,
    ReviewerAuthorizationGate,
    CanonicalPromotionPlanner,
]:
    boundary = ProjectBoundary("project-a", "dataset-a", root)
    loader = CanonicalPermissionEnvelopeLoader(boundary, "canonical/permissions.json")
    authorization = AuthorizationService(loader)
    gate = ReviewerAuthorizationGate(authorization, loader)
    return (
        boundary,
        ProposalStager(boundary, "derived/staging", authorization),
        gate,
        CanonicalPromotionPlanner(boundary, gate),
    )


def test_staging_is_human_readable_idempotent_and_concurrency_safe(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    target = root / "control" / "decision.md"
    target.parent.mkdir(parents=True)
    target.write_text("old value\n", encoding="utf-8")
    _write_permissions(root, reviewer_policy=False)
    _, stager, _, _ = _components(root)
    proposal = _proposal()

    with ThreadPoolExecutor(max_workers=8) as pool:
        artifacts = tuple(
            pool.map(
                lambda _: stager.stage(proposal, trace_id="trace-stage"),
                range(16),
            )
        )

    assert sum(artifact.created for artifact in artifacts) == 1
    assert len({artifact.staging_digest for artifact in artifacts}) == 1
    artifact = artifacts[0]
    review = (root / artifact.human_review_path).read_text(encoding="utf-8")
    assert "control/decision.md" in review
    assert "Decision requires review" in review
    assert "src_evidence-a" in review
    assert "-old value" in review
    assert "+new value" in review
    assert target.read_text(encoding="utf-8") == "old value\n"


def test_idempotency_key_and_proposal_id_conflicts_are_rejected(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "control").mkdir()
    _write_permissions(root, reviewer_policy=False)
    _, stager, _, _ = _components(root)
    first = _proposal()
    stager.stage(first, trace_id="trace-stage", base_content="old\n")

    changed = WriteProposal.model_validate(
        {**deepcopy(first.to_json_dict()), "proposal": {"title": "Change", "content": "other\n"}}
    )
    with pytest.raises(IdempotencyConflictError):
        stager.stage(changed, trace_id="trace-stage", base_content="old\n")


def test_secret_proposals_are_rejected_before_staging(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "control").mkdir()
    _write_permissions(root, reviewer_policy=False)
    _, stager, _, _ = _components(root)
    secret = "api_key=" + "runtime-only-value"

    with pytest.raises(SecretDetectedError):
        stager.stage(_proposal(content=secret), trace_id="trace-stage", base_content="")
    assert not (root / "derived" / "staging").exists()


def test_review_fails_closed_until_canonical_reviewer_policy_exists(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "control").mkdir()
    _write_permissions(root, reviewer_policy=False)
    _, stager, gate, _ = _components(root)
    artifact = stager.stage(_proposal(), trace_id="trace-stage", base_content="")
    scope = ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a")

    with pytest.raises(PolicyDisabledError):
        gate.decide(
            artifact,
            reviewer_id="reviewer-a",
            project_id="project-a",
            dataset_id="dataset-a",
            scope=scope,
            record_type="Decision",
            disposition=ReviewDisposition.APPROVED,
            rationale_summary="Evidence supports the change.",
            trace_id="trace-review",
        )


def test_review_rereads_canonical_permission_and_rejects_stale_grant(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "control").mkdir()
    _write_permissions(root, reviewer_policy=True)
    _, stager, gate, _ = _components(root)
    artifact = stager.stage(_proposal(), trace_id="trace-stage", base_content="")
    _write_permissions(root, reviewer_policy=True, allow_approve=False)

    with pytest.raises(PermissionDeniedError):
        gate.decide(
            artifact,
            reviewer_id="reviewer-a",
            project_id="project-a",
            dataset_id="dataset-a",
            scope=ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a"),
            record_type="Decision",
            disposition=ReviewDisposition.APPROVED,
            rationale_summary="Evidence supports the change.",
            trace_id="trace-review",
        )


def test_automated_reviewer_requires_higher_system_policy_reference(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "control").mkdir()
    _write_permissions(root, reviewer_policy=True)
    _, stager, gate, _ = _components(root)
    artifact = stager.stage(_proposal(), trace_id="trace-stage", base_content="")
    permission_path = root / "canonical" / "permissions.json"
    payload = json.loads(permission_path.read_text(encoding="utf-8"))
    payload["approval_policy"]["reviewers"][0] = {
        "principal_id": "reviewer-a",
        "kind": "system-automation",
        "higher_system_policy_ref": None,
    }
    permission_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PermissionDeniedError):
        gate.decide(
            artifact,
            reviewer_id="reviewer-a",
            project_id="project-a",
            dataset_id="dataset-a",
            scope=ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a"),
            record_type="Decision",
            disposition=ReviewDisposition.APPROVED,
            rationale_summary="System policy explicitly authorizes this review.",
            trace_id="trace-review",
        )


def test_promotion_returns_normal_change_artifact_and_rereads_target(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    target = root / "control" / "decision.md"
    target.parent.mkdir()
    target.write_text("old value\n", encoding="utf-8")
    _write_permissions(root, reviewer_policy=True)
    _, stager, gate, planner = _components(root)
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
        rationale_summary="Evidence supports the change.",
        trace_id="trace-review",
    )

    request = planner.create_request(
        artifact,
        review,
        project_id="project-a",
        dataset_id="dataset-a",
        scope=scope,
        record_type="Decision",
        trace_id="trace-promote",
    )

    assert request.requires_governed_project_workflow
    assert request.policy_action is PolicyAction.CANONICAL_PROMOTION
    assert request.reviewer_kind.value == "human"
    assert not request.canonical_write_performed
    assert request.synchronize_after_accepted_write
    assert "+new value" in request.unified_patch
    assert target.read_text(encoding="utf-8") == "old value\n"

    target.write_text("changed after review\n", encoding="utf-8")
    with pytest.raises(StaleStateError):
        planner.create_request(
            artifact,
            review,
            project_id="project-a",
            dataset_id="dataset-a",
            scope=scope,
            record_type="Decision",
            trace_id="trace-promote-again",
        )


def test_rejected_review_cannot_request_promotion(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "control").mkdir()
    _write_permissions(root, reviewer_policy=True)
    _, stager, gate, planner = _components(root)
    artifact = stager.stage(_proposal(), trace_id="trace-stage", base_content="")
    scope = ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a")
    review = gate.decide(
        artifact,
        reviewer_id="reviewer-a",
        project_id="project-a",
        dataset_id="dataset-a",
        scope=scope,
        record_type="Decision",
        disposition=ReviewDisposition.REJECTED,
        rationale_summary="Evidence is insufficient.",
        trace_id="trace-review",
    )
    with pytest.raises(PermissionDeniedError):
        planner.create_request(
            artifact,
            review,
            project_id="project-a",
            dataset_id="dataset-a",
            scope=scope,
            record_type="Decision",
            trace_id="trace-promote",
        )
    stager.discard_rejected(artifact, review)
    stager.discard_rejected(artifact, review)
    assert not (root / artifact.artifact_directory).exists()
    assert not (root / "derived" / "staging" / ".rejected").exists()


def test_proposal_requester_cannot_approve_own_proposal(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "control").mkdir()
    _write_permissions(root, reviewer_policy=True)
    permission_path = root / "canonical" / "permissions.json"
    payload = json.loads(permission_path.read_text(encoding="utf-8"))
    payload["approval_policy"]["reviewers"] = [
        {
            "principal_id": "agent-a",
            "kind": "human",
            "higher_system_policy_ref": None,
        }
    ]
    payload["grants"][0]["permissions"].append("approve")
    payload["grants"][0]["operations"].append("memory.approve")
    permission_path.write_text(json.dumps(payload), encoding="utf-8")
    _, stager, gate, _ = _components(root)
    artifact = stager.stage(_proposal(), trace_id="trace-stage", base_content="")

    with pytest.raises(PermissionDeniedError, match="own proposal"):
        gate.decide(
            artifact,
            reviewer_id="agent-a",
            project_id="project-a",
            dataset_id="dataset-a",
            scope=ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a"),
            record_type="Decision",
            disposition=ReviewDisposition.APPROVED,
            rationale_summary="The requester attempts to self-approve.",
            trace_id="trace-review",
        )


def test_rejected_proposal_retains_only_explicit_policy_metadata(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "control").mkdir()
    _write_permissions(root, reviewer_policy=True)
    _, stager, gate, _ = _components(root)
    artifact = stager.stage(_proposal(), trace_id="trace-stage", base_content="")
    scope = ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a")
    review = gate.decide(
        artifact,
        reviewer_id="reviewer-a",
        project_id="project-a",
        dataset_id="dataset-a",
        scope=scope,
        record_type="Decision",
        disposition=ReviewDisposition.REJECTED,
        rationale_summary="Evidence is insufficient and must not become active knowledge.",
        trace_id="trace-review",
        reviewed_at=datetime(2026, 9, 3, 12, 0, tzinfo=UTC),
    )
    retention = RejectedProposalRetentionPolicy(
        status="approved",
        policy_id="rejected-metadata@1",
        retained_fields=frozenset(
            {
                RejectedMetadataField.PROPOSAL_ID,
                RejectedMetadataField.PROPOSAL_DIGEST,
                RejectedMetadataField.REVIEWED_AT,
            }
        ),
        retain_until=review.reviewed_at + timedelta(days=1),
    )

    receipt = stager.dispose_rejected(
        artifact,
        review,
        retention_policy=retention,
    )
    replay = stager.dispose_rejected(
        artifact,
        review,
        retention_policy=retention,
    )

    assert replay == receipt
    assert receipt.proposal_content_removed
    assert not receipt.active_knowledge
    assert not (root / artifact.artifact_directory).exists()
    assert receipt.retained_metadata_path is not None
    retained_path = root / receipt.retained_metadata_path
    payload = json.loads(retained_path.read_text(encoding="utf-8"))
    assert set(payload) == {
        "active_knowledge",
        "metadata",
        "retain_until",
        "retention_policy_id",
        "schema_version",
    }
    assert payload["active_knowledge"] is False
    assert set(payload["metadata"]) == {
        "proposal_digest",
        "proposal_id",
        "reviewed_at",
    }
    assert "new value" not in retained_path.read_text(encoding="utf-8")
    assert "Evidence is insufficient" not in retained_path.read_text(encoding="utf-8")


def test_unresolved_rejection_retention_cannot_select_metadata() -> None:
    with pytest.raises(ValidationError, match="cannot retain metadata"):
        RejectedProposalRetentionPolicy(
            status="pending-user-decision",
            retained_fields=frozenset({RejectedMetadataField.PROPOSAL_ID}),
        )
