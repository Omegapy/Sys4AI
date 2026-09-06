from __future__ import annotations

import json
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
    PermissionDeniedError,
)
from sys4ai_memory.contracts import MemoryScope, ScopeReference
from sys4ai_memory.observability import (
    AdministrativeActionExecutor,
    AdministrativeOperation,
    AuditRecorder,
    VersionContext,
)
from sys4ai_memory.security import InMemoryAuditSink, ProjectBoundary


def _write_permissions(
    root: Path,
    *,
    operations: tuple[AdministrativeOperation, ...],
    revision: str,
    target_prefixes: tuple[str, ...] = (),
) -> None:
    path = root / "control_records" / "memory" / "permissions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "revision": revision,
                "project_id": "project-alpha",
                "dataset_id": "project-alpha-memory",
                "issued_at": "2026-09-03T00:00:00Z",
                "grants": [
                    {
                        "grant_id": "grant-admin",
                        "principal_id": "local-owner",
                        "permissions": ["read", "administer"],
                        "operations": [item.value for item in operations],
                        "scopes": [{"level": "project", "scope_id": "project-alpha"}],
                        "target_prefixes": target_prefixes,
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _executor(
    root: Path,
    versions: VersionContext,
    sink: InMemoryAuditSink,
) -> AdministrativeActionExecutor:
    boundary = ProjectBoundary(
        project_id="project-alpha",
        dataset_id="project-alpha-memory",
        root=root,
    )
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    return AdministrativeActionExecutor(
        authorization=AuthorizationService(loader),
        audit=AuditRecorder(sink),
        project_id="project-alpha",
        dataset_id="project-alpha-memory",
        versions=versions,
        policy_decision_ref="control_records/memory/permissions.json",
    )


def _scope() -> ScopeReference:
    return ScopeReference(level=MemoryScope.PROJECT, scope_id="project-alpha")


def test_source_registration_executes_only_after_fresh_authorization_and_is_audited(
    tmp_path: Path,
    versions: VersionContext,
) -> None:
    operation = AdministrativeOperation.SOURCE_REGISTER
    _write_permissions(
        tmp_path,
        operations=(operation,),
        revision="permissions-1",
        target_prefixes=("registries",),
    )
    sink = InMemoryAuditSink()
    executor = _executor(tmp_path, versions, sink)
    registry = tmp_path / "registries" / "memory_source_registry.csv"

    result = executor.execute(
        operation,
        principal_id="local-owner",
        scope=_scope(),
        trace_id="trace_source_register",
        target_path="registries/memory_source_registry.csv",
        target_ids=("src_operations",),
        action=lambda: _write_registry(registry),
    )

    assert result == "registered"
    assert registry.read_text(encoding="utf-8") == "source_id\nsrc_operations\n"
    assert sink.events()[0].outcome == "authorized"
    event = sink.events()[1]
    assert event.operation == operation.value
    assert event.outcome == "succeeded"
    assert event.target_ids == ("src_operations",)

    _write_permissions(
        tmp_path,
        operations=(),
        revision="permissions-2",
        target_prefixes=("registries",),
    )
    with pytest.raises(PermissionDeniedError, match="no_matching_current_grant"):
        executor.execute(
            operation,
            principal_id="local-owner",
            scope=_scope(),
            trace_id="trace_denied_register",
            target_path="registries/memory_source_registry.csv",
            action=lambda: pytest.fail("denied action must not run"),
        )
    assert sink.events()[-1].outcome == "denied"


def test_each_administrative_operation_uses_the_execution_boundary(
    tmp_path: Path,
    versions: VersionContext,
) -> None:
    operations = tuple(AdministrativeOperation)
    _write_permissions(tmp_path, operations=operations, revision="permissions-all")
    sink = InMemoryAuditSink()
    executor = _executor(tmp_path, versions, sink)

    observed: list[str] = []
    for index, operation in enumerate(operations):
        observed.append(
            executor.execute(
                operation,
                principal_id="local-owner",
                scope=_scope(),
                trace_id=f"trace_{index}",
                action=operation.value.__str__,
            )
        )

    assert observed == [operation.value for operation in operations]
    assert [event.operation for event in sink.events()[1::2]] == observed
    assert [event.outcome for event in sink.events()] == [
        outcome for _operation in operations for outcome in ("authorized", "succeeded")
    ]


def test_failed_administrative_callback_is_audited_and_reraised(
    tmp_path: Path,
    versions: VersionContext,
) -> None:
    operation = AdministrativeOperation.CONFIGURATION_CHANGE
    _write_permissions(tmp_path, operations=(operation,), revision="permissions-1")
    sink = InMemoryAuditSink()
    executor = _executor(tmp_path, versions, sink)

    def fail() -> None:
        raise RuntimeError("fixture failure")

    with pytest.raises(RuntimeError, match="fixture failure"):
        executor.execute(
            operation,
            principal_id="local-owner",
            scope=_scope(),
            trace_id="trace_config_failed",
            action=fail,
        )
    assert [event.outcome for event in sink.events()] == ["authorized", "failed"]


def _write_registry(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("source_id\nsrc_operations\n", encoding="utf-8")
    return "registered"
