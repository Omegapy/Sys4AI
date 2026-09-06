from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import JsonValue

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    AuthorityTier,
    ErrorCategory,
    ErrorEnvelope,
    OperationName,
    RecordStatus,
    Sensitivity,
    TrustClass,
)
from sys4ai_memory.interfaces import (
    DispatchRequest,
    DispatchSuccess,
    InterfaceIdentity,
    MemoryClient,
)
from sys4ai_memory.lifecycle import (
    CanonicalDeletionChangeRequest,
    DestructiveLifecycleService,
    FilesystemImpactResolver,
    LifecycleCatalog,
    LifecycleRecord,
    ResourceSpec,
    StorageLocation,
)
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import ServiceComponents
from tests.service.test_dispatcher import (
    DATASET_ID,
    PROJECT_ID,
    _identity,
    _request,
    _service,
)

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]

NOW = datetime(2026, 9, 3, 21, 15, tzinfo=UTC)


def _install_destructive_acceptance_permissions(permission_path: Path) -> None:
    document = json.loads(permission_path.read_text(encoding="utf-8"))
    document["revision"] = "permissions-destructive-acceptance-1"
    document["grants"][0]["operations"].extend(
        [
            "memory.forget.delete-derived",
            "memory.forget.delete-source",
        ]
    )
    document["grants"].append(
        {
            "grant_id": "general-agent-read-propose",
            "principal_id": "agent-general",
            "permissions": ["read", "propose"],
            "operations": [
                "memory.health",
                "memory.recall",
                "memory.get",
                "memory.graph",
                "memory.propose",
                "memory.explain",
            ],
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
    permission_path.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")


def _as_general_agent(request: DispatchRequest) -> DispatchRequest:
    identity = InterfaceIdentity(
        principal_id="agent-general",
        agent_type="general-agent",
        run_id="run-general-agent",
    )
    return request.model_copy(
        update={
            "authorization": request.authorization.model_copy(
                update={"identity": identity}
            )
        }
    )


@pytest.mark.parametrize(
    ("case", "operation", "payload"),
    [
        (
            "mass_forget",
            OperationName.FORGET,
            {
                "record_ids": ["mem_MASS_A", "mem_MASS_B"],
                "action": "delete-derived",
                "reason": "attempted mass deletion",
                "execute": False,
            },
        ),
        (
            "delete_source",
            OperationName.FORGET,
            {
                "record_ids": ["mem_CANONICAL_SOURCE"],
                "action": "delete-source",
                "reason": "attempted canonical deletion",
                "execute": False,
            },
        ),
        (
            "rebuild_activation",
            OperationName.REBUILD,
            {
                "preview_only": False,
                "operation_id": "op_general_rebuild",
                "impact_digest": "e" * 64,
            },
        ),
        (
            "import_replacement",
            OperationName.IMPORT,
            {
                "package_path": "imports/memory.zip",
                "activate": True,
                "impact_digest": "e" * 64,
            },
        ),
    ],
)
def test_general_agent_cannot_invoke_destructive_operations(
    tmp_path: Path,
    case: str,
    operation: OperationName,
    payload: dict[str, JsonValue],
) -> None:
    root = tmp_path.resolve()
    service, audit, permission_path = _service(root)
    _install_destructive_acceptance_permissions(permission_path)

    response = service.dispatch(
        _as_general_agent(
            _request(
                operation,
                payload,
                suffix=f"general_denied_{case}",
                idempotency_key=f"general-denied-{case}",
            )
        )
    )

    assert isinstance(response, ErrorEnvelope)
    assert response.error.category is ErrorCategory.PERMISSION_DENIED
    assert response.error.trace_id == f"trace_general_denied_{case}"
    assert [event.outcome for event in audit.events()] == ["denied"]
    assert not (root / ".sys4ai/memory").exists()


def _lifecycle_record(record_id: str, *, canonical: bool = False) -> LifecycleRecord:
    return LifecycleRecord(
        record_id=record_id,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        status=RecordStatus.ACTIVE,
        authority_tier=(
            AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE
            if canonical
            else AuthorityTier.AGENT_DURABLE_MATERIAL
        ),
        trust_class=(
            TrustClass.PROJECT_AUTHORED if canonical else TrustClass.AGENT_GENERATED
        ),
        sensitivity=Sensitivity.INTERNAL,
        canonical=canonical,
        source_ids=(f"src_{record_id.removeprefix('mem_')}",),
        valid_from=NOW,
    )


def _authorization(root: Path) -> AuthorizationService:
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    return AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            boundary,
            "control_records/memory/permissions.json",
        )
    )


def test_administrator_previews_and_executes_mass_forget_with_receipt(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    components = ServiceComponents()
    service, _, permission_path = _service(root, components=components)
    _install_destructive_acceptance_permissions(permission_path)
    record_ids = ("mem_MASS_A", "mem_MASS_B")
    lifecycle = LifecycleCatalog()
    resources: list[ResourceSpec] = []
    for record_id in record_ids:
        lifecycle.add(_lifecycle_record(record_id))
        relative = f".sys4ai/memory/provider/{record_id}.bin"
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"disposable {record_id}\n", encoding="utf-8")
        resources.append(
            ResourceSpec(
                resource_id=record_id,
                project_id=PROJECT_ID,
                dataset_id=DATASET_ID,
                location=StorageLocation.DERIVED_PROVIDER,
                relative_path=relative,
                record_id=record_id,
                source_id=None,
                sensitivity=Sensitivity.INTERNAL,
                canonical=False,
            )
        )
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    components.destructive = DestructiveLifecycleService(
        boundary,
        _authorization(root),
        FilesystemImpactResolver(boundary, tuple(resources)),
        deletable_roots=(".sys4ai/memory",),
        lifecycle=lifecycle,
    )
    client = MemoryClient(
        service,
        identity=_identity(),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )

    previewed = client.forget(
        record_ids,
        action="delete-derived",
        reason="approved disposable mass deletion",
        idempotency_key="mass-forget-preview",
        request_id="mrq_mass_forget_preview",
        trace_id="trace_mass_forget_preview",
    )
    assert isinstance(previewed, DispatchSuccess)
    preview = previewed.result["preview"]
    assert isinstance(preview, dict)
    assert preview["mutating"] is False
    assert dict(preview["affected_counts"]) == {"derived-provider": 2}
    assert all((root / str(item.relative_path)).is_file() for item in resources)

    executed = client.forget(
        record_ids,
        action="delete-derived",
        reason="approved disposable mass deletion",
        idempotency_key="mass-forget-execute",
        execute=True,
        operation_id=str(preview["operation_id"]),
        impact_digest=str(preview["impact_digest"]),
        request_id="mrq_mass_forget_execute",
        trace_id="trace_mass_forget_execute",
    )

    assert isinstance(executed, DispatchSuccess)
    receipt = executed.result["receipt"]
    assert isinstance(receipt, dict)
    assert receipt["outcome"] == "succeeded"
    assert set(receipt["affected_resource_ids"]) == set(record_ids)
    assert set(receipt["transitioned_record_ids"]) == set(record_ids)
    assert all(not (root / str(item.relative_path)).exists() for item in resources)
    assert all(lifecycle.get(record_id).status is RecordStatus.DELETED for record_id in record_ids)


class _GovernedDeletionExecutor:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.requests: list[CanonicalDeletionChangeRequest] = []

    def execute(self, request: CanonicalDeletionChangeRequest) -> tuple[str, ...]:
        self.requests.append(request)
        for relative in request.target_paths:
            (self.root / relative).unlink()
        return request.resource_ids


def test_administrator_previews_and_executes_governed_delete_source_with_receipt(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    components = ServiceComponents()
    service, _, permission_path = _service(root, components=components)
    _install_destructive_acceptance_permissions(permission_path)
    record_id = "mem_CANONICAL_SOURCE"
    canonical = root / "canonical/source.md"
    canonical.parent.mkdir()
    canonical.write_text("disposable canonical source\n", encoding="utf-8")
    lifecycle = LifecycleCatalog()
    lifecycle.add(_lifecycle_record(record_id, canonical=True))
    resource = ResourceSpec(
        resource_id=record_id,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        location=StorageLocation.CANONICAL_SOURCE,
        relative_path="canonical/source.md",
        record_id=record_id,
        source_id="src_CANONICAL_SOURCE",
        sensitivity=Sensitivity.INTERNAL,
        canonical=True,
    )
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    executor = _GovernedDeletionExecutor(root)
    components.destructive = DestructiveLifecycleService(
        boundary,
        _authorization(root),
        FilesystemImpactResolver(boundary, (resource,)),
        deletable_roots=(".sys4ai/memory",),
        lifecycle=lifecycle,
        canonical_executor=executor,
    )
    client = MemoryClient(
        service,
        identity=_identity(),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )

    previewed = client.forget(
        (record_id,),
        action="delete-source",
        reason="approved disposable canonical deletion",
        idempotency_key="delete-source-preview",
        request_id="mrq_delete_source_preview",
        trace_id="trace_delete_source_preview",
    )
    assert isinstance(previewed, DispatchSuccess)
    preview = previewed.result["preview"]
    change = previewed.result["canonical_change_request"]
    assert isinstance(preview, dict)
    assert isinstance(change, dict)
    assert change["requires_governed_project_workflow"] is True
    assert change["canonical_write_performed"] is False
    assert change["target_paths"] == ["canonical/source.md"]
    assert canonical.is_file()

    executed = client.forget(
        (record_id,),
        action="delete-source",
        reason="approved disposable canonical deletion",
        idempotency_key="delete-source-execute",
        execute=True,
        operation_id=str(preview["operation_id"]),
        impact_digest=str(preview["impact_digest"]),
        request_id="mrq_delete_source_execute",
        trace_id="trace_delete_source_execute",
    )

    assert isinstance(executed, DispatchSuccess)
    receipt = executed.result["receipt"]
    assert isinstance(receipt, dict)
    assert receipt["outcome"] == "succeeded"
    assert receipt["canonical_workflow_resource_ids"] == [record_id]
    assert receipt["transitioned_record_ids"] == [record_id]
    assert not canonical.exists()
    assert lifecycle.get(record_id).status is RecordStatus.DELETED
    assert len(executor.requests) == 1
    assert executor.requests[0].target_paths == ("canonical/source.md",)
