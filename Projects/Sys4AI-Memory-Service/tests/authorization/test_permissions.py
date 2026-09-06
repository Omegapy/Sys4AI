from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationRequest,
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
    CanonicalPermissionError,
    ScopeResolver,
)
from sys4ai_memory.contracts import MemoryScope, Permission, ScopeReference
from sys4ai_memory.security import ProjectBoundary

PROJECT_ROOT = Path(__file__).parents[2]


def _scope(level: MemoryScope, scope_id: str, *parents: ScopeReference) -> ScopeReference:
    return ScopeReference(level=level, scope_id=scope_id, parent_scopes=parents)


def _write_permission_document(
    root: Path,
    *,
    revision: str = "perm-rev-1",
    permissions: tuple[str, ...] = ("read",),
    operations: tuple[str, ...] = (),
    shared_projects: tuple[str, ...] = (),
    include_unknown: bool = False,
) -> None:
    document: dict[str, object] = {
        "schema_version": "1.0",
        "revision": revision,
        "project_id": "project-a",
        "dataset_id": "dataset-a",
        "issued_at": "2026-09-03T12:00:00Z",
        "grants": [
            {
                "grant_id": "grant-agent-a",
                "principal_id": "agent-a",
                "permissions": list(permissions),
                "operations": list(operations),
                "scopes": [{"level": "project", "scope_id": "project-a", "parent_scopes": []}],
                "target_prefixes": ["docs"],
                "shared_project_ids": list(shared_projects),
                "valid_until": None,
            }
        ],
        "approval_policy": None,
    }
    if include_unknown:
        document["remembered_role"] = "administrator"
    path = root / "control" / "permissions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")


def _service(root: Path) -> AuthorizationService:
    boundary = ProjectBoundary("project-a", "dataset-a", root)
    loader = CanonicalPermissionEnvelopeLoader(boundary, "control/permissions.json")
    return AuthorizationService(loader)


def _request(
    *,
    permission: Permission = Permission.READ,
    scope: ScopeReference | None = None,
    operation: str = "memory.recall",
    target_path: str | None = "docs/file.md",
    query_project_ids: tuple[str, ...] = (),
    explicit_cross_project: bool = False,
    require_action_specific: bool = False,
) -> AuthorizationRequest:
    return AuthorizationRequest(
        principal_id="agent-a",
        project_id="project-a",
        dataset_id="dataset-a",
        operation=operation,
        permission=permission,
        scope=scope or _scope(MemoryScope.PROJECT, "project-a"),
        target_path=target_path,
        query_project_ids=query_project_ids,
        explicit_cross_project=explicit_cross_project,
        trace_id="trace-auth-test",
        require_action_specific=require_action_specific,
    )


def test_loader_builds_effective_envelope_from_current_canonical_file(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permission_document(root)
    service = _service(root)

    envelope = service.resolve_envelope("agent-a")

    assert envelope.project_id == "project-a"
    assert envelope.dataset_id == "dataset-a"
    assert envelope.revision == "perm-rev-1"
    assert len(envelope.canonical_sha256) == 64
    assert {grant.grant_id for grant in envelope.grants} == {"grant-agent-a"}


def test_invalid_or_missing_canonical_permissions_fail_closed(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    service = _service(root)
    assert service.evaluate(_request()).reason_code == "canonical_permission_unavailable"

    _write_permission_document(root, include_unknown=True)
    assert service.evaluate(_request()).reason_code == "canonical_permission_unavailable"
    with pytest.raises(CanonicalPermissionError):
        service.resolve_envelope("agent-a")


def test_scope_resolution_requires_explicit_ancestry(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permission_document(root)
    service = _service(root)
    project = _scope(MemoryScope.PROJECT, "project-a")
    task = _scope(MemoryScope.TASK, "task-1", project)
    unrelated = _scope(
        MemoryScope.TASK,
        "task-2",
        _scope(MemoryScope.PROJECT, "project-b"),
    )

    assert ScopeResolver.allows(service.resolve_envelope("agent-a").grants[0], task)
    assert service.evaluate(_request(scope=task)).allowed
    assert not service.evaluate(_request(scope=unrelated)).allowed


def test_permission_is_reread_before_every_operation(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permission_document(root, permissions=("read",))
    service = _service(root)
    first = service.evaluate(_request())
    assert first.allowed

    _write_permission_document(root, revision="perm-rev-2", permissions=("propose",))
    second = service.evaluate(_request())

    assert not second.allowed
    assert second.permission_revision == "perm-rev-2"
    assert second.canonical_sha256 != first.canonical_sha256


def test_action_specific_grants_do_not_authorize_another_operation(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permission_document(
        root,
        permissions=("delete",),
        operations=("memory.forget.delete-derived",),
    )
    service = _service(root)

    allowed = service.evaluate(
        _request(
            permission=Permission.DELETE,
            operation="memory.forget.delete-derived",
            require_action_specific=True,
        )
    )
    denied = service.evaluate(
        _request(
            permission=Permission.DELETE,
            operation="memory.forget.privacy-erase",
            require_action_specific=True,
        )
    )

    assert allowed.allowed
    assert not denied.allowed


def test_cross_project_recall_requires_explicit_scope_and_grant(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permission_document(root, shared_projects=("project-b",))
    service = _service(root)
    projects = ("project-a", "project-b")

    assert not service.evaluate(_request(query_project_ids=projects)).allowed
    assert service.evaluate(
        _request(query_project_ids=projects, explicit_cross_project=True)
    ).allowed
    assert not service.evaluate(
        _request(
            query_project_ids=("project-a", "project-c"),
            explicit_cross_project=True,
        )
    ).allowed


def test_expired_grant_is_denied(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permission_document(root)
    path = root / "control" / "permissions.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["grants"][0]["valid_until"] = "2026-09-03T12:30:00Z"
    path.write_text(json.dumps(payload), encoding="utf-8")

    decision = _service(root).evaluate(
        _request(),
        now=datetime(2026, 9, 3, 13, 0, tzinfo=UTC),
    )

    assert not decision.allowed
    assert decision.reason_code == "no_matching_current_grant"


def test_product_permission_document_enforces_the_approved_single_reviewer_policy() -> None:
    boundary = ProjectBoundary(
        "sys4ai-memory-service",
        "sys4ai-memory-service",
        PROJECT_ROOT,
    )
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )

    snapshot = loader.load_snapshot()
    policy = snapshot.document.approval_policy
    assert policy is not None
    assert policy.policy_id == "local-owner-single-review@1"
    assert policy.approvals_required == 1
    assert policy.self_approval_allowed is False
    assert [(reviewer.principal_id, reviewer.kind.value) for reviewer in policy.reviewers] == [
        ("local-owner", "human")
    ]
    general_permissions = {
        permission
        for grant in loader.resolve("general-agent").grants
        for permission in grant.permissions
    }
    owner_permissions = {
        permission
        for grant in loader.resolve("local-owner").grants
        for permission in grant.permissions
    }
    assert general_permissions == {Permission.READ, Permission.PROPOSE}
    assert Permission.APPROVE in owner_permissions
    assert Permission.DELETE not in owner_permissions
    assert Permission.ADMINISTER not in owner_permissions
    assert Permission.REBUILD not in owner_permissions
