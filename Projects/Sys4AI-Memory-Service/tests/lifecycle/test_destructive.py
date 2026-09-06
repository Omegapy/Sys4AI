from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    AuthorityTier,
    MemoryScope,
    RecordStatus,
    ScopeReference,
    Sensitivity,
    TrustClass,
)
from sys4ai_memory.lifecycle import (
    CanonicalDeletionChangeRequest,
    DestructiveLifecycleService,
    DestructiveRequest,
    FilesystemImpactResolver,
    ForgetMode,
    GovernedCanonicalDeletionExecutor,
    LifecycleCatalog,
    LifecycleRecord,
    ResourceSpec,
    StorageLocation,
)
from sys4ai_memory.security import (
    IdempotencyConflictError,
    InMemoryAuditSink,
    PolicyDisabledError,
    ProjectBoundary,
    ProjectIsolationError,
    StaleStateError,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


def _write_permissions(root: Path, *, revision: str = "perm-delete-1") -> None:
    document = {
        "schema_version": "1.0",
        "revision": revision,
        "project_id": "project-a",
        "dataset_id": "dataset-a",
        "issued_at": "2026-09-03T12:00:00Z",
        "grants": [
            {
                "grant_id": "grant-eraser",
                "principal_id": "eraser",
                "permissions": ["delete"],
                "operations": [
                    "memory.forget.expire",
                    "memory.forget.withdraw",
                    "memory.forget.delete-derived",
                    "memory.forget.delete-source",
                    "memory.forget.privacy-erase",
                ],
                "scopes": [{"level": "project", "scope_id": "project-a", "parent_scopes": []}],
                "target_prefixes": [],
                "shared_project_ids": [],
                "valid_until": None,
            }
        ],
        "approval_policy": None,
    }
    path = root / "canonical" / "permissions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")


def _request(mode: ForgetMode, selectors: tuple[str, ...]) -> DestructiveRequest:
    return DestructiveRequest(
        operation_id=f"operation-{mode.value}",
        principal_id="eraser",
        project_id="project-a",
        dataset_id="dataset-a",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id="project-a"),
        mode=mode,
        selector_ids=selectors,
        trace_id=f"trace-{mode.value}",
    )


def _authorization(boundary: ProjectBoundary) -> AuthorizationService:
    return AuthorizationService(
        CanonicalPermissionEnvelopeLoader(boundary, "canonical/permissions.json")
    )


def _resource(
    resource_id: str,
    location: StorageLocation,
    path: str | None,
    *,
    canonical: bool = False,
    record_id: str | None = None,
) -> ResourceSpec:
    return ResourceSpec(
        resource_id=resource_id,
        project_id="project-a",
        dataset_id="dataset-a",
        location=location,
        relative_path=path,
        record_id=record_id,
        source_id="src_source" if canonical else None,
        sensitivity=Sensitivity.RESTRICTED,
        canonical=canonical,
    )


def _service(
    root: Path,
    resources: tuple[ResourceSpec, ...],
    *,
    lifecycle: LifecycleCatalog | None = None,
    canonical_executor: GovernedCanonicalDeletionExecutor | None = None,
    audit: InMemoryAuditSink | None = None,
) -> DestructiveLifecycleService:
    boundary = ProjectBoundary("project-a", "dataset-a", root)
    return DestructiveLifecycleService(
        boundary,
        _authorization(boundary),
        FilesystemImpactResolver(boundary, resources),
        deletable_roots=("derived",),
        lifecycle=lifecycle,
        canonical_executor=canonical_executor,
        audit=audit,
    )


def test_delete_derived_uses_nonmutating_preview_and_idempotent_execution(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    derived = root / "derived" / "provider" / "record.bin"
    canonical = root / "canonical" / "source.md"
    derived.parent.mkdir(parents=True)
    canonical.parent.mkdir(exist_ok=True)
    derived.write_text("derived representation", encoding="utf-8")
    canonical.write_text("canonical source", encoding="utf-8")
    resources = (
        _resource(
            "resource-derived",
            StorageLocation.DERIVED_PROVIDER,
            "derived/provider/record.bin",
        ),
        _resource(
            "resource-canonical",
            StorageLocation.CANONICAL_SOURCE,
            "canonical/source.md",
            canonical=True,
        ),
    )
    audit = InMemoryAuditSink()
    service = _service(root, resources, audit=audit)
    request = _request(ForgetMode.DELETE_DERIVED, ("resource-derived",))

    preview = service.preview(request, previewed_at=NOW)

    assert not preview.mutating
    assert derived.exists()
    assert canonical.exists()
    assert preview.affected_counts == (("derived-provider", 1),)

    receipt = service.execute(request, preview, completed_at=NOW)
    repeated = service.execute(request, preview, completed_at=NOW)

    assert receipt == repeated
    assert not derived.exists()
    assert canonical.exists()
    assert len(receipt.deleted_path_hashes) == 1
    assert "derived representation" not in receipt.model_dump_json()
    assert [event.operation for event in audit.events()] == [
        "memory.forget.delete-derived.preview",
        "memory.forget.delete-derived.execute",
    ]


def test_changed_impact_denies_execution_without_deleting(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    target = root / "derived" / "record.bin"
    target.parent.mkdir()
    target.write_text("first", encoding="utf-8")
    service = _service(
        root,
        (_resource("resource-derived", StorageLocation.CACHE, "derived/record.bin"),),
    )
    request = _request(ForgetMode.DELETE_DERIVED, ("resource-derived",))
    preview = service.preview(request, previewed_at=NOW)
    target.write_text("changed", encoding="utf-8")

    with pytest.raises(StaleStateError, match="impact"):
        service.execute(request, preview, completed_at=NOW)
    assert target.read_text(encoding="utf-8") == "changed"


def test_changed_canonical_permission_denies_execution(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    target = root / "derived" / "record.bin"
    target.parent.mkdir()
    target.write_text("derived", encoding="utf-8")
    service = _service(
        root,
        (_resource("resource-derived", StorageLocation.CACHE, "derived/record.bin"),),
    )
    request = _request(ForgetMode.DELETE_DERIVED, ("resource-derived",))
    preview = service.preview(request, previewed_at=NOW)
    _write_permissions(root, revision="perm-delete-2")

    with pytest.raises(StaleStateError, match="permission"):
        service.execute(request, preview, completed_at=NOW)
    assert target.exists()


def test_delete_source_requires_and_uses_governed_canonical_executor(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    canonical = root / "canonical" / "source.md"
    canonical.write_text("canonical source", encoding="utf-8")
    denied_service = _service(
        root,
        (
            _resource(
                "resource-canonical",
                StorageLocation.CANONICAL_SOURCE,
                "canonical/source.md",
                canonical=True,
            ),
        ),
    )
    request = _request(ForgetMode.DELETE_SOURCE, ("resource-canonical",))
    denied_preview = denied_service.preview(request, previewed_at=NOW)
    change = denied_service.canonical_change_request(denied_preview)

    assert change.requires_governed_project_workflow
    assert not change.canonical_write_performed
    assert change.target_paths == ("canonical/source.md",)
    with pytest.raises(PolicyDisabledError, match="governed canonical executor"):
        denied_service.execute(request, denied_preview, completed_at=NOW)
    assert canonical.read_text(encoding="utf-8") == "canonical source"

    service = _service(
        root,
        (
            _resource(
                "resource-canonical",
                StorageLocation.CANONICAL_SOURCE,
                "canonical/source.md",
                canonical=True,
            ),
        ),
        canonical_executor=_CanonicalExecutor(root),
    )
    preview = service.preview(request, previewed_at=NOW)
    receipt = service.execute(request, preview, completed_at=NOW)

    assert not canonical.exists()
    assert receipt.canonical_workflow_resource_ids == ("resource-canonical",)
    assert receipt.outcome == "succeeded"


class _CanonicalExecutor:
    def __init__(self, root: Path) -> None:
        self.root = root

    def execute(self, request: CanonicalDeletionChangeRequest) -> tuple[str, ...]:
        for relative in request.target_paths:
            (self.root / relative).unlink()
        return request.resource_ids


class _NoOpCanonicalExecutor:
    def execute(self, request: CanonicalDeletionChangeRequest) -> tuple[str, ...]:
        return request.resource_ids


def test_canonical_executor_must_remove_every_previewed_path(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    canonical = root / "canonical" / "source.md"
    canonical.write_text("canonical source", encoding="utf-8")
    service = _service(
        root,
        (
            _resource(
                "resource-canonical",
                StorageLocation.CANONICAL_SOURCE,
                "canonical/source.md",
                canonical=True,
            ),
        ),
        canonical_executor=_NoOpCanonicalExecutor(),
    )
    request = _request(ForgetMode.DELETE_SOURCE, ("resource-canonical",))
    preview = service.preview(request, previewed_at=NOW)

    with pytest.raises(StaleStateError, match="left a previewed target present"):
        service.execute(request, preview, completed_at=NOW)
    assert canonical.read_text(encoding="utf-8") == "canonical source"


def test_delete_source_rejects_a_noncanonical_only_scope(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    derived = root / "derived" / "record.bin"
    derived.parent.mkdir()
    derived.write_text("derived", encoding="utf-8")
    service = _service(
        root,
        (_resource("resource-derived", StorageLocation.CACHE, "derived/record.bin"),),
        canonical_executor=_NoOpCanonicalExecutor(),
    )
    request = _request(ForgetMode.DELETE_SOURCE, ("resource-derived",))
    preview = service.preview(request, previewed_at=NOW)

    with pytest.raises(PolicyDisabledError, match="previewed canonical source"):
        service.execute(request, preview, completed_at=NOW)
    assert derived.read_text(encoding="utf-8") == "derived"


def test_privacy_erase_requires_governed_canonical_executor_and_covers_all_copies(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    derived = root / "derived" / "cache.bin"
    canonical = root / "canonical" / "source.md"
    derived.parent.mkdir()
    canonical.parent.mkdir(exist_ok=True)
    sensitive = "prohibited-runtime-content"
    derived.write_text(sensitive, encoding="utf-8")
    canonical.write_text(sensitive, encoding="utf-8")
    resources = (
        _resource("resource-cache", StorageLocation.CACHE, "derived/cache.bin"),
        _resource(
            "resource-source",
            StorageLocation.CANONICAL_SOURCE,
            "canonical/source.md",
            canonical=True,
        ),
    )
    request = _request(
        ForgetMode.PRIVACY_ERASE,
        ("resource-cache", "resource-source"),
    )
    denied_service = _service(root, resources)
    denied_preview = denied_service.preview(request, previewed_at=NOW)
    with pytest.raises(PolicyDisabledError, match="governed canonical executor"):
        denied_service.execute(request, denied_preview, completed_at=NOW)
    assert derived.exists() and canonical.exists()

    service = _service(root, resources, canonical_executor=_CanonicalExecutor(root))
    preview = service.preview(request, previewed_at=NOW)
    receipt = service.execute(request, preview, completed_at=NOW)

    assert not derived.exists() and not canonical.exists()
    assert receipt.canonical_workflow_resource_ids == ("resource-source",)
    assert sensitive not in receipt.model_dump_json()


@pytest.mark.parametrize(
    ("mode", "expected_status"),
    [
        (ForgetMode.EXPIRE, RecordStatus.EXPIRED),
        (ForgetMode.WITHDRAW, RecordStatus.WITHDRAWN),
    ],
)
def test_non_file_lifecycle_modes_use_same_preview_protocol(
    tmp_path: Path,
    mode: ForgetMode,
    expected_status: RecordStatus,
) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    catalog = LifecycleCatalog()
    catalog.add(
        LifecycleRecord(
            record_id="mem_target",
            project_id="project-a",
            dataset_id="dataset-a",
            status=RecordStatus.ACTIVE,
            authority_tier=AuthorityTier.AGENT_DURABLE_MATERIAL,
            trust_class=TrustClass.AGENT_GENERATED,
            sensitivity=Sensitivity.INTERNAL,
            canonical=False,
            source_ids=("src_source",),
            valid_from=NOW,
        )
    )
    resources = (
        _resource(
            "resource-lifecycle",
            StorageLocation.LIFECYCLE,
            None,
            record_id="mem_target",
        ),
    )
    service = _service(root, resources, lifecycle=catalog)
    request = _request(mode, ("resource-lifecycle",))
    preview = service.preview(request, previewed_at=NOW)
    service.execute(request, preview, completed_at=NOW)
    assert catalog.get("mem_target").status is expected_status


def test_cross_project_impact_is_rejected(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    boundary = ProjectBoundary("project-a", "dataset-a", root)
    resource = _resource("resource-other", StorageLocation.CACHE, None).model_copy(
        update={"project_id": "project-b"}
    )
    resolver = FilesystemImpactResolver(boundary, (resource,))
    with pytest.raises(ProjectIsolationError):
        resolver.resolve(_request(ForgetMode.DELETE_DERIVED, ("resource-other",)))


def test_operation_id_cannot_be_reused_for_different_impact(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _write_permissions(root)
    first = root / "derived" / "first"
    second = root / "derived" / "second"
    first.parent.mkdir()
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    resources = (
        _resource("resource-first", StorageLocation.CACHE, "derived/first"),
        _resource("resource-second", StorageLocation.CACHE, "derived/second"),
    )
    service = _service(root, resources)
    first_request = _request(ForgetMode.DELETE_DERIVED, ("resource-first",))
    first_preview = service.preview(first_request, previewed_at=NOW)
    service.execute(first_request, first_preview, completed_at=NOW)
    conflicting = first_request.model_copy(update={"selector_ids": ("resource-second",)})
    conflicting_preview = service.preview(conflicting, previewed_at=NOW)
    with pytest.raises(IdempotencyConflictError):
        service.execute(conflicting, conflicting_preview, completed_at=NOW)


def test_provider_forget_is_not_an_exposed_lifecycle_mode() -> None:
    assert {mode.value for mode in ForgetMode} == {
        "expire",
        "withdraw",
        "delete-derived",
        "delete-source",
        "privacy-erase",
    }
