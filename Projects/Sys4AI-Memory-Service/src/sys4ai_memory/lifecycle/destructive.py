"""Digest-bound two-phase lifecycle and filesystem deletion protocol."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sys4ai_memory.authorization import AuthorizationRequest, AuthorizationService
from sys4ai_memory.contracts import Permission, RecordStatus, ScopeReference, Sensitivity
from sys4ai_memory.security import (
    AuditEvent,
    AuditSink,
    IdempotencyConflictError,
    InMemoryAuditSink,
    PolicyDisabledError,
    ProjectBoundary,
    ProjectIsolationError,
    StaleStateError,
    require_secret_free,
)
from sys4ai_memory.util import canonical_json_bytes, ensure_utc, sha256_bytes, sha256_file, utc_now

from .state import LifecycleCatalog


class ForgetMode(StrEnum):
    EXPIRE = "expire"
    WITHDRAW = "withdraw"
    DELETE_DERIVED = "delete-derived"
    DELETE_SOURCE = "delete-source"
    PRIVACY_ERASE = "privacy-erase"


class StorageLocation(StrEnum):
    DERIVED_PROVIDER = "derived-provider"
    EXACT_INDEX = "exact-index"
    CACHE = "cache"
    STAGING = "staging"
    AUDIT = "audit"
    EXPORT = "export"
    BACKUP = "backup"
    REBUILD_INPUT = "rebuild-input"
    CANONICAL_SOURCE = "canonical-source"
    LIFECYCLE = "lifecycle"


class DestructiveModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class DestructiveRequest(DestructiveModel):
    operation_id: str
    principal_id: str
    project_id: str
    dataset_id: str
    scope: ScopeReference
    mode: ForgetMode
    selector_ids: tuple[str, ...] = Field(min_length=1)
    trace_id: str

    @model_validator(mode="after")
    def validate_request(self) -> DestructiveRequest:
        if len(set(self.selector_ids)) != len(self.selector_ids):
            raise ValueError("destructive selectors must not contain duplicates")
        require_secret_free(
            {
                "operation_id": self.operation_id,
                "principal_id": self.principal_id,
                "project_id": self.project_id,
                "dataset_id": self.dataset_id,
                "selector_ids": self.selector_ids,
                "trace_id": self.trace_id,
            },
            field_path="destructive_request",
        )
        return self


class ResourceSpec(DestructiveModel):
    resource_id: str
    project_id: str
    dataset_id: str
    location: StorageLocation
    relative_path: str | None
    record_id: str | None = None
    source_id: str | None = None
    sensitivity: Sensitivity
    canonical: bool = False


class ImpactResource(DestructiveModel):
    resource_id: str
    project_id: str
    dataset_id: str
    location: StorageLocation
    relative_path: str | None
    record_id: str | None
    source_id: str | None
    sensitivity: Sensitivity
    canonical: bool
    exists: bool
    size_bytes: int | None = Field(default=None, ge=0)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class ImpactPreview(DestructiveModel):
    operation_id: str
    project_id: str
    dataset_id: str
    mode: ForgetMode
    selector_ids: tuple[str, ...]
    resources: tuple[ImpactResource, ...]
    affected_counts: tuple[tuple[str, int], ...]
    sensitivity_classes: tuple[Sensitivity, ...]
    canonical_source_effects: tuple[str, ...]
    blocked_resource_ids: tuple[str, ...]
    warning_codes: tuple[str, ...]
    permission_revision: str
    permission_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    impact_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    previewed_at: datetime
    mutating: bool = False

    @model_validator(mode="after")
    def validate_preview(self) -> ImpactPreview:
        ensure_utc(self.previewed_at)
        if self.mutating:
            raise ValueError("impact preview must be non-mutating")
        return self


class DeletionReceipt(DestructiveModel):
    operation_id: str
    project_id: str
    dataset_id: str
    mode: ForgetMode
    principal_id: str
    trace_id: str
    impact_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    permission_revision: str
    affected_resource_ids: tuple[str, ...]
    deleted_path_hashes: tuple[str, ...]
    transitioned_record_ids: tuple[str, ...]
    canonical_workflow_resource_ids: tuple[str, ...]
    outcome: str
    completed_at: datetime

    @model_validator(mode="after")
    def validate_receipt(self) -> DeletionReceipt:
        ensure_utc(self.completed_at)
        require_secret_free(
            {
                "operation_id": self.operation_id,
                "principal_id": self.principal_id,
                "trace_id": self.trace_id,
                "affected_resource_ids": self.affected_resource_ids,
            },
            field_path="deletion_receipt",
        )
        return self


class CanonicalDeletionChangeRequest(DestructiveModel):
    operation_id: str
    project_id: str
    mode: ForgetMode
    resource_ids: tuple[str, ...]
    target_paths: tuple[str, ...]
    requires_governed_project_workflow: bool = True
    canonical_write_performed: bool = False
    repreview_required_after_change: bool = True


class ImpactResolver(Protocol):
    def resolve(self, request: DestructiveRequest) -> tuple[ImpactResource, ...]: ...


class GovernedCanonicalDeletionExecutor(Protocol):
    """Complete canonical deletion through an atomic governed project workflow."""

    def execute(
        self,
        request: CanonicalDeletionChangeRequest,
    ) -> tuple[str, ...]: ...


class FilesystemImpactResolver:
    """Recompute registered resource hashes without exposing file content."""

    def __init__(self, boundary: ProjectBoundary, resources: tuple[ResourceSpec, ...]) -> None:
        self._boundary = boundary
        self._resources = resources

    def resolve(self, request: DestructiveRequest) -> tuple[ImpactResource, ...]:
        self._boundary.require_identity(
            project_id=request.project_id,
            dataset_id=request.dataset_id,
        )
        selectors = frozenset(request.selector_ids)
        resolved: list[ImpactResource] = []
        for item in self._resources:
            identities = {item.resource_id, item.record_id, item.source_id} - {None}
            if not selectors.intersection(identities):
                continue
            if item.project_id != request.project_id or item.dataset_id != request.dataset_id:
                raise ProjectIsolationError("impact resolver encountered a cross-project resource")
            exists = False
            size: int | None = None
            digest: str | None = None
            if item.relative_path is not None:
                path = self._boundary.resolve_path(item.relative_path, must_exist=False)
                exists = path.exists()
                if exists:
                    if not path.is_file() or path.is_symlink():
                        raise ValueError("destructive resources must be regular non-symlink files")
                    size = path.stat().st_size
                    digest = sha256_file(path)
            resolved.append(
                ImpactResource(
                    **item.model_dump(),
                    exists=exists,
                    size_bytes=size,
                    content_sha256=digest,
                )
            )
        return tuple(sorted(resolved, key=lambda item: item.resource_id))


def _impact_digest(
    request: DestructiveRequest,
    resources: tuple[ImpactResource, ...],
    permission_revision: str,
    permission_sha256: str,
) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "operation_id": request.operation_id,
                "project_id": request.project_id,
                "dataset_id": request.dataset_id,
                "mode": request.mode.value,
                "selector_ids": list(request.selector_ids),
                "resources": [item.model_dump(mode="json") for item in resources],
                "permission_revision": permission_revision,
                "permission_sha256": permission_sha256,
            }
        )
    )


class DestructiveLifecycleService:
    """Preview and execute only an unchanged, freshly authorized impact set."""

    def __init__(
        self,
        boundary: ProjectBoundary,
        authorization: AuthorizationService,
        resolver: ImpactResolver,
        *,
        deletable_roots: tuple[str, ...],
        lifecycle: LifecycleCatalog | None = None,
        canonical_executor: GovernedCanonicalDeletionExecutor | None = None,
        audit: AuditSink | None = None,
    ) -> None:
        self._boundary = boundary
        self._authorization = authorization
        self._resolver = resolver
        self._deletable_roots = tuple(
            boundary.resolve_path(root, must_exist=False) for root in deletable_roots
        )
        self._lifecycle = lifecycle
        self._canonical_executor = canonical_executor
        self._audit = audit or InMemoryAuditSink()
        self._receipts: dict[str, DeletionReceipt] = {}
        self._lock = RLock()

    def preview(
        self,
        request: DestructiveRequest,
        *,
        previewed_at: datetime | None = None,
    ) -> ImpactPreview:
        resources = self._resolver.resolve(request)
        revision, permission_sha256 = self._authorize(request, resources)
        blocked = self._blocked_resources(request.mode, resources)
        warnings: list[str] = []
        if blocked:
            warnings.append("canonical-workflow-required")
        if not resources:
            warnings.append("no-matching-resources")
        counts = Counter(item.location.value for item in resources)
        canonical_effects = tuple(
            item.resource_id
            for item in resources
            if item.canonical or item.location is StorageLocation.CANONICAL_SOURCE
        )
        digest = _impact_digest(request, resources, revision, permission_sha256)
        timestamp = ensure_utc(previewed_at or utc_now())
        preview = ImpactPreview(
            operation_id=request.operation_id,
            project_id=request.project_id,
            dataset_id=request.dataset_id,
            mode=request.mode,
            selector_ids=request.selector_ids,
            resources=resources,
            affected_counts=tuple(sorted(counts.items())),
            sensitivity_classes=tuple(sorted({item.sensitivity for item in resources}, key=str)),
            canonical_source_effects=canonical_effects,
            blocked_resource_ids=blocked,
            warning_codes=tuple(warnings),
            permission_revision=revision,
            permission_sha256=permission_sha256,
            impact_digest=digest,
            previewed_at=timestamp,
        )
        self._audit.record(self._audit_event(request, preview, "preview", "allowed", timestamp))
        return preview

    def canonical_change_request(self, preview: ImpactPreview) -> CanonicalDeletionChangeRequest:
        resources = tuple(
            item
            for item in preview.resources
            if item.canonical or item.location is StorageLocation.CANONICAL_SOURCE
        )
        return CanonicalDeletionChangeRequest(
            operation_id=preview.operation_id,
            project_id=preview.project_id,
            mode=preview.mode,
            resource_ids=tuple(item.resource_id for item in resources),
            target_paths=tuple(
                item.relative_path for item in resources if item.relative_path is not None
            ),
        )

    def execute(
        self,
        request: DestructiveRequest,
        preview: ImpactPreview,
        *,
        completed_at: datetime | None = None,
    ) -> DeletionReceipt:
        with self._lock:
            existing = self._receipts.get(request.operation_id)
            if existing is not None:
                if existing.impact_digest != preview.impact_digest:
                    raise IdempotencyConflictError(
                        "operation ID already identifies a different destructive impact"
                    )
                return existing
            self._require_preview_matches(request, preview)
            current_resources = self._resolver.resolve(request)
            revision, permission_sha256 = self._authorize(request, current_resources)
            current_digest = _impact_digest(
                request,
                current_resources,
                revision,
                permission_sha256,
            )
            if current_digest != preview.impact_digest:
                raise StaleStateError("destructive impact or canonical permission changed")

            canonical = tuple(
                item
                for item in current_resources
                if item.canonical or item.location is StorageLocation.CANONICAL_SOURCE
            )
            if request.mode is ForgetMode.DELETE_SOURCE and not canonical:
                raise PolicyDisabledError(
                    "delete-source requires a previewed canonical source resource"
                )
            if request.mode is ForgetMode.DELETE_DERIVED and canonical:
                raise PolicyDisabledError("delete-derived cannot delete canonical sources")
            self._validate_record_transitions(request, current_resources)
            self._preflight_files(request.mode, current_resources)
            canonical_completed: tuple[str, ...] = ()
            if request.mode in {ForgetMode.DELETE_SOURCE, ForgetMode.PRIVACY_ERASE} and canonical:
                if self._canonical_executor is None:
                    operation = (
                        "canonical source deletion"
                        if request.mode is ForgetMode.DELETE_SOURCE
                        else "privacy erasure with canonical effects"
                    )
                    raise PolicyDisabledError(
                        f"{operation} requires a governed canonical executor"
                    )
                canonical_request = self.canonical_change_request(preview)
                canonical_completed = tuple(
                    sorted(self._canonical_executor.execute(canonical_request))
                )
                expected = tuple(sorted(item.resource_id for item in canonical))
                if canonical_completed != expected:
                    raise StaleStateError(
                        "governed canonical deletion did not cover the previewed scope"
                    )
                self._require_canonical_paths_removed(canonical)

            deleted_path_hashes = self._delete_files(request.mode, current_resources)
            transitioned = self._transition_records(request, current_resources)
            timestamp = ensure_utc(completed_at or utc_now())
            receipt = DeletionReceipt(
                operation_id=request.operation_id,
                project_id=request.project_id,
                dataset_id=request.dataset_id,
                mode=request.mode,
                principal_id=request.principal_id,
                trace_id=request.trace_id,
                impact_digest=preview.impact_digest,
                permission_revision=revision,
                affected_resource_ids=tuple(item.resource_id for item in current_resources),
                deleted_path_hashes=deleted_path_hashes,
                transitioned_record_ids=transitioned,
                canonical_workflow_resource_ids=canonical_completed,
                outcome="succeeded",
                completed_at=timestamp,
            )
            self._receipts[request.operation_id] = receipt
            self._audit.record(
                self._audit_event(request, preview, "execute", "succeeded", timestamp)
            )
            return receipt

    def _authorize(
        self,
        request: DestructiveRequest,
        resources: tuple[ImpactResource, ...],
    ) -> tuple[str, str]:
        targets = tuple(
            sorted({item.relative_path for item in resources if item.relative_path is not None})
        ) or (None,)
        revisions: set[tuple[str, str]] = set()
        for target in targets:
            decision = self._authorization.require(
                AuthorizationRequest(
                    principal_id=request.principal_id,
                    project_id=request.project_id,
                    dataset_id=request.dataset_id,
                    operation=f"memory.forget.{request.mode.value}",
                    permission=Permission.DELETE,
                    scope=request.scope,
                    target_path=target,
                    trace_id=request.trace_id,
                    require_action_specific=True,
                )
            )
            assert decision.permission_revision is not None
            assert decision.canonical_sha256 is not None
            revisions.add((decision.permission_revision, decision.canonical_sha256))
        if len(revisions) != 1:
            raise StaleStateError("canonical permission changed while resolving destructive scope")
        return next(iter(revisions))

    @staticmethod
    def _blocked_resources(
        mode: ForgetMode,
        resources: tuple[ImpactResource, ...],
    ) -> tuple[str, ...]:
        if mode not in {ForgetMode.DELETE_SOURCE, ForgetMode.PRIVACY_ERASE}:
            return tuple(
                item.resource_id
                for item in resources
                if item.canonical or item.location is StorageLocation.CANONICAL_SOURCE
            )
        return tuple(
            item.resource_id
            for item in resources
            if item.canonical or item.location is StorageLocation.CANONICAL_SOURCE
        )

    @staticmethod
    def _require_preview_matches(
        request: DestructiveRequest,
        preview: ImpactPreview,
    ) -> None:
        if (
            request.operation_id != preview.operation_id
            or request.project_id != preview.project_id
            or request.dataset_id != preview.dataset_id
            or request.mode is not preview.mode
            or request.selector_ids != preview.selector_ids
        ):
            raise StaleStateError("preview does not match the destructive request")
        if preview.mutating:
            raise ValueError("impact preview must be non-mutating")

    def _delete_files(
        self,
        mode: ForgetMode,
        resources: tuple[ImpactResource, ...],
    ) -> tuple[str, ...]:
        if mode not in {ForgetMode.DELETE_DERIVED, ForgetMode.PRIVACY_ERASE}:
            return ()
        targets = self._preflight_files(mode, resources)
        deleted: list[str] = []
        for item, path in targets:
            path.unlink()
            assert item.relative_path is not None
            deleted.append(sha256_bytes(item.relative_path.encode("utf-8")))
        return tuple(sorted(deleted))

    def _require_canonical_paths_removed(
        self,
        resources: tuple[ImpactResource, ...],
    ) -> None:
        for item in resources:
            if item.relative_path is None:
                continue
            path = self._boundary.resolve_path(item.relative_path, must_exist=False)
            if path.exists():
                raise StaleStateError(
                    "governed canonical deletion left a previewed target present"
                )

    def _preflight_files(
        self,
        mode: ForgetMode,
        resources: tuple[ImpactResource, ...],
    ) -> tuple[tuple[ImpactResource, Path], ...]:
        if mode not in {ForgetMode.DELETE_DERIVED, ForgetMode.PRIVACY_ERASE}:
            return ()
        targets: list[tuple[ImpactResource, Path]] = []
        for item in resources:
            if item.canonical or item.location is StorageLocation.CANONICAL_SOURCE:
                continue
            if item.relative_path is None or not item.exists:
                continue
            path = self._boundary.resolve_path(item.relative_path)
            if not any(path.is_relative_to(root) for root in self._deletable_roots):
                raise PolicyDisabledError("resource is outside every configured deletable root")
            if not path.is_file() or path.is_symlink():
                raise StaleStateError("resource changed before deletion")
            if item.content_sha256 is None or sha256_file(path) != item.content_sha256:
                raise StaleStateError("resource content changed before deletion")
            targets.append((item, path))
        return tuple(targets)

    def _validate_record_transitions(
        self,
        request: DestructiveRequest,
        resources: tuple[ImpactResource, ...],
    ) -> None:
        if self._lifecycle is None:
            return
        record_ids = tuple(
            sorted({item.record_id for item in resources if item.record_id is not None})
        )
        target_status = self._target_status(request.mode)
        if target_status is not None:
            self._lifecycle.validate_transition_many(record_ids, target_status)

    def _transition_records(
        self,
        request: DestructiveRequest,
        resources: tuple[ImpactResource, ...],
    ) -> tuple[str, ...]:
        if self._lifecycle is None:
            return ()
        record_ids = tuple(
            sorted({item.record_id for item in resources if item.record_id is not None})
        )
        target_status = self._target_status(request.mode)
        if target_status is None:
            return ()
        self._lifecycle.transition_many(record_ids, target_status)
        return record_ids

    @staticmethod
    def _target_status(mode: ForgetMode) -> RecordStatus | None:
        return {
            ForgetMode.EXPIRE: RecordStatus.EXPIRED,
            ForgetMode.WITHDRAW: RecordStatus.WITHDRAWN,
            ForgetMode.DELETE_DERIVED: RecordStatus.DELETED,
            ForgetMode.DELETE_SOURCE: RecordStatus.DELETED,
            ForgetMode.PRIVACY_ERASE: RecordStatus.DELETED,
        }.get(mode)

    @staticmethod
    def _audit_event(
        request: DestructiveRequest,
        preview: ImpactPreview,
        phase: str,
        outcome: str,
        timestamp: datetime,
    ) -> AuditEvent:
        return AuditEvent(
            event_id=f"{request.operation_id}:{phase}",
            occurred_at=timestamp,
            principal_id=request.principal_id,
            project_id=request.project_id,
            dataset_id=request.dataset_id,
            operation=f"memory.forget.{request.mode.value}.{phase}",
            target_ids=tuple(item.resource_id for item in preview.resources),
            policy_decision="authorized",
            outcome=outcome,
            trace_id=request.trace_id,
            policy_id="destructive-lifecycle-policy@1",
            permission_revision=preview.permission_revision,
            counts=preview.affected_counts,
            warning_codes=preview.warning_codes,
        )
