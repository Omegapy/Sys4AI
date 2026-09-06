from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
    PermissionDeniedError,
)
from sys4ai_memory.contracts import MemoryScope, ScopeReference
from sys4ai_memory.providers import ProviderContext, ProviderMutation
from sys4ai_memory.security import ProjectBoundary, StaleStateError
from sys4ai_memory.service import (
    PROVIDER_OPERATION_NAMES,
    ProviderAuthorizationBridge,
    ProviderAuthorizationError,
)


def _write_permissions(root: Path, *, revision: str = "permissions-1") -> Path:
    path = root / "control_records/memory/permissions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "revision": revision,
                "project_id": "project-a",
                "dataset_id": "dataset-a",
                "issued_at": "2026-09-03T12:00:00Z",
                "grants": [
                    {
                        "grant_id": "provider-operations",
                        "principal_id": "agent-a",
                        "permissions": [
                            "administer",
                            "write-derived",
                            "delete",
                            "share",
                        ],
                        "operations": list(PROVIDER_OPERATION_NAMES.values()),
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
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _components(root: Path) -> tuple[ProviderAuthorizationBridge, ProviderContext]:
    boundary = ProjectBoundary("project-a", "dataset-a", root)
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    bridge = ProviderAuthorizationBridge(AuthorizationService(loader), loader)
    context = ProviderContext(
        project_id="project-a",
        dataset_id="dataset-a",
        principal_id="agent-a",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a"),
        trace_id="trace_provider_auth",
    )
    return bridge, context


@pytest.mark.parametrize("mutation", tuple(ProviderMutation))
def test_bridge_binds_each_provider_mutation_to_current_canonical_policy(
    tmp_path: Path,
    mutation: ProviderMutation,
) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    bridge, context = _components(root)
    impact = "a" * 64 if mutation is ProviderMutation.FORGET else None

    envelope = bridge.authorize(
        context,
        mutation,
        impact_digest=impact,
        evaluated_at=datetime(2026, 9, 3, 12, 30, tzinfo=UTC),
    )

    assert envelope.operation is mutation
    assert envelope.principal_id == context.principal_id
    assert envelope.project_id == context.project_id
    assert envelope.dataset_id == context.dataset_id
    assert envelope.scope == context.scope
    assert envelope.trace_id == context.trace_id
    assert envelope.policy_id == "provider-operations"
    assert envelope.policy_revision == "permissions-1"
    assert envelope.canonical_source == "control_records/memory/permissions.json"
    assert envelope.impact_digest == impact


def test_bridge_denies_a_grant_without_the_exact_operation(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    path = _write_permissions(root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["grants"][0]["operations"] = ["memory.recall"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    bridge, context = _components(root)

    with pytest.raises(PermissionDeniedError, match="no_matching_current_grant"):
        bridge.authorize(context, ProviderMutation.REMEMBER)


def test_bridge_allows_remember_for_typed_proposal_but_rejects_unmapped_action(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    path = _write_permissions(root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["grants"][0]["operations"] = ["memory.propose"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    bridge, context = _components(root)

    envelope = bridge.authorize(
        context,
        ProviderMutation.REMEMBER,
        authorization_operation="memory.propose",
    )
    assert envelope.operation is ProviderMutation.REMEMBER

    with pytest.raises(ProviderAuthorizationError, match="cannot be bound"):
        bridge.authorize(
            context,
            ProviderMutation.REMEMBER,
            authorization_operation="memory.approve",
        )


def test_bridge_rejects_permission_change_during_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path.resolve()
    path = _write_permissions(root)
    boundary = ProjectBoundary("project-a", "dataset-a", root)
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    bridge = ProviderAuthorizationBridge(AuthorizationService(loader), loader)
    _, context = _components(root)
    original = loader.load_snapshot
    calls = 0

    def changing_snapshot():
        nonlocal calls
        calls += 1
        if calls == 2:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["revision"] = "permissions-2"
            path.write_text(json.dumps(payload), encoding="utf-8")
        return original()

    monkeypatch.setattr(loader, "load_snapshot", changing_snapshot)
    with pytest.raises(StaleStateError, match="changed while binding"):
        bridge.authorize(context, ProviderMutation.REMEMBER)
