from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    AuthorityTier,
    MemoryScope,
    Permission,
    PolicyAction,
    RecordStatus,
    ScopeReference,
    Sensitivity,
    TrustClass,
)
from sys4ai_memory.contracts.models import RequesterIdentity
from sys4ai_memory.policies import (
    AuthorizedWritePolicy,
    WritePolicyEngine,
    WritePolicySettings,
    WriteRequest,
    WriteTargetClass,
)
from sys4ai_memory.security import InMemoryAuditSink, ProjectBoundary


def _request(target: WriteTargetClass) -> WriteRequest:
    project = ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a")
    scope = (
        ScopeReference(level=MemoryScope.SESSION, scope_id="session-a", parent_scopes=(project,))
        if target is WriteTargetClass.SESSION
        else project
    )
    return WriteRequest(
        project_id="project-a",
        dataset_id="dataset-a",
        requester=RequesterIdentity(
            principal_id="agent-a",
            agent_type="implementation-agent",
            run_id="run-a",
        ),
        record_type="Event" if target is WriteTargetClass.EPISODIC else "Observation",
        target_class=target,
        scope=scope,
        evidence_ids=("src_evidence-a",),
        requested_status=RecordStatus.PROPOSED,
        trust_class=TrustClass.AGENT_GENERATED,
        sensitivity=Sensitivity.INTERNAL,
        authority_tier=AuthorityTier.AGENT_DURABLE_MATERIAL,
        requested_target="control/proposals/candidate.json",
        idempotency_key="run-a:observation-1",
        trace_id="trace-write-policy",
        content={"statement": "bounded observation"},
    )


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        (WriteTargetClass.SESSION, PolicyAction.SESSION_ONLY),
        (WriteTargetClass.EPISODIC, PolicyAction.STAGE_FOR_REVIEW),
        (WriteTargetClass.OBSERVATION, PolicyAction.STAGE_FOR_REVIEW),
        (WriteTargetClass.FEEDBACK, PolicyAction.DERIVED_COMMIT),
        (WriteTargetClass.DERIVED, PolicyAction.DERIVED_COMMIT),
        (WriteTargetClass.EXTERNAL_EVIDENCE, PolicyAction.DERIVED_COMMIT),
        (WriteTargetClass.PROJECT_FACT, PolicyAction.STAGE_FOR_REVIEW),
        (WriteTargetClass.DECISION, PolicyAction.STAGE_FOR_REVIEW),
        (WriteTargetClass.REQUIREMENT, PolicyAction.STAGE_FOR_REVIEW),
        (WriteTargetClass.GOVERNANCE, PolicyAction.STAGE_FOR_REVIEW),
        (WriteTargetClass.PERMISSION, PolicyAction.STAGE_FOR_REVIEW),
        (WriteTargetClass.CANONICAL_CODE, PolicyAction.STAGE_FOR_REVIEW),
        (WriteTargetClass.CANONICAL_CONFIGURATION, PolicyAction.STAGE_FOR_REVIEW),
    ],
)
def test_default_write_policy_matrix(
    target: WriteTargetClass,
    expected: PolicyAction,
) -> None:
    decision = WritePolicyEngine().evaluate(
        _request(target),
        current_permissions=frozenset({Permission.PROPOSE, Permission.WRITE_DERIVED}),
    )
    assert decision.action is expected
    assert decision.effective_principal == "agent-a"


def test_episodic_commit_requires_explicit_task_policy_and_write_permission() -> None:
    engine = WritePolicyEngine(WritePolicySettings(episodic_auto_commit=True))
    request = _request(WriteTargetClass.EPISODIC)

    staged = engine.evaluate(request, current_permissions=frozenset({Permission.PROPOSE}))
    committed = engine.evaluate(
        request,
        current_permissions=frozenset({Permission.PROPOSE, Permission.WRITE_DERIVED}),
    )

    assert staged.action is PolicyAction.STAGE_FOR_REVIEW
    assert committed.action is PolicyAction.EPISODIC_COMMIT


def test_untyped_secret_and_overbroad_writes_are_rejected() -> None:
    engine = WritePolicyEngine()
    base = _request(WriteTargetClass.DERIVED).model_dump()

    untyped = deepcopy(base)
    untyped["record_type"] = None
    secret = deepcopy(base)
    secret["content"] = {"message": "api_key=" + "runtime-only-value"}
    overbroad = deepcopy(base)
    overbroad["scope"] = ScopeReference(level=MemoryScope.SYSTEM, scope_id="sys4ai")

    permissions = frozenset({Permission.PROPOSE, Permission.WRITE_DERIVED})
    assert (
        engine.evaluate(
            WriteRequest.model_validate(untyped), current_permissions=permissions
        ).action
        is PolicyAction.REJECT
    )
    assert (
        engine.evaluate(WriteRequest.model_validate(secret), current_permissions=permissions).action
        is PolicyAction.REJECT
    )
    assert (
        engine.evaluate(
            WriteRequest.model_validate(overbroad), current_permissions=permissions
        ).action
        is PolicyAction.REJECT
    )


def test_external_content_and_automatic_feedback_fail_closed() -> None:
    engine = WritePolicyEngine()
    external = _request(WriteTargetClass.GOVERNANCE).model_copy(update={"external_source": True})
    automatic = _request(WriteTargetClass.FEEDBACK).model_copy(update={"automatic_feedback": True})
    permissions = frozenset({Permission.PROPOSE, Permission.WRITE_DERIVED})

    assert engine.evaluate(external, current_permissions=permissions).action is PolicyAction.REJECT
    assert engine.evaluate(automatic, current_permissions=permissions).action is PolicyAction.REJECT


def test_lack_of_propose_permission_rejects_every_write() -> None:
    decision = WritePolicyEngine().evaluate(
        _request(WriteTargetClass.DERIVED),
        current_permissions=frozenset({Permission.WRITE_DERIVED}),
    )
    assert decision.action is PolicyAction.REJECT
    assert decision.required_permission is Permission.PROPOSE


def test_authorized_write_policy_uses_current_canonical_permissions_and_audits(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    permission_path = root / "canonical" / "permissions.json"
    permission_path.parent.mkdir()

    def write_permissions(permissions: tuple[str, ...], revision: str) -> None:
        permission_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "revision": revision,
                    "project_id": "project-a",
                    "dataset_id": "dataset-a",
                    "issued_at": "2026-09-03T12:00:00Z",
                    "grants": [
                        {
                            "grant_id": "grant-agent",
                            "principal_id": "agent-a",
                            "permissions": list(permissions),
                            "operations": [],
                            "scopes": [
                                {
                                    "level": "project",
                                    "scope_id": "project-a",
                                    "parent_scopes": [],
                                }
                            ],
                            "target_prefixes": ["control"],
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
    loader = CanonicalPermissionEnvelopeLoader(boundary, "canonical/permissions.json")
    audit = InMemoryAuditSink()
    policy = AuthorizedWritePolicy(
        WritePolicyEngine(),
        AuthorizationService(loader),
        audit=audit,
    )

    write_permissions(("propose", "write-derived"), "perm-1")
    committed = policy.evaluate(_request(WriteTargetClass.DERIVED))
    assert committed.action is PolicyAction.DERIVED_COMMIT
    assert committed.permission_revision == "perm-1"
    assert audit.events()[-1].principal_id == "agent-a"
    assert audit.events()[-1].policy_decision == "derived_commit"

    write_permissions(("propose",), "perm-2")
    staged = policy.evaluate(_request(WriteTargetClass.DERIVED))
    assert staged.action is PolicyAction.STAGE_FOR_REVIEW
    assert staged.permission_revision == "perm-2"

    write_permissions(("read",), "perm-3")
    denied = policy.evaluate(_request(WriteTargetClass.DERIVED))
    assert denied.action is PolicyAction.REJECT
    assert denied.permission_revision == "perm-3"
