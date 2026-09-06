"""Project, dataset, query-scope, path, and deployment isolation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from sys4ai_memory.util import PathBoundaryError, resolve_within

from .errors import PolicyDisabledError, ProjectIsolationError, UnsafePathError


@dataclass(frozen=True, slots=True)
class ProjectBoundary:
    """A trusted project root and its one allowed dataset identity."""

    project_id: str
    dataset_id: str
    root: Path

    def __post_init__(self) -> None:
        if not self.project_id.strip() or not self.dataset_id.strip():
            raise ValueError("project_id and dataset_id must not be blank")
        if not self.root.is_absolute() or not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("project root must be an absolute existing non-symlink directory")

    def require_identity(self, *, project_id: str, dataset_id: str) -> None:
        if project_id != self.project_id or dataset_id != self.dataset_id:
            raise ProjectIsolationError("project or dataset does not match the service boundary")

    def resolve_path(
        self,
        candidate: str | Path,
        *,
        must_exist: bool = True,
    ) -> Path:
        try:
            return resolve_within(self.root, candidate, must_exist=must_exist)
        except PathBoundaryError as error:
            raise UnsafePathError("path is outside the registered project boundary") from error


class DatasetIsolationMap:
    """One-to-one project/dataset mapping independent of provider storage."""

    def __init__(self, mappings: dict[str, str]) -> None:
        if not mappings or any(
            not key.strip() or not value.strip() for key, value in mappings.items()
        ):
            raise ValueError("dataset mappings must contain nonblank identities")
        if len(set(mappings.values())) != len(mappings):
            raise ProjectIsolationError("one dataset cannot represent multiple projects")
        self._mappings = dict(mappings)

    def dataset_for(self, project_id: str) -> str:
        try:
            return self._mappings[project_id]
        except KeyError as error:
            raise ProjectIsolationError("project has no isolated dataset mapping") from error

    def require_pair(self, project_id: str, dataset_id: str) -> None:
        if self.dataset_for(project_id) != dataset_id:
            raise ProjectIsolationError("dataset does not belong to the requested project")


class DeploymentMode(StrEnum):
    SINGLE_USER_DEVELOPMENT = "single-user-development"
    SHARED = "shared"


@dataclass(frozen=True, slots=True)
class DeploymentSecurityPosture:
    """Explicitly distinguish local development from secured shared service."""

    mode: DeploymentMode
    authenticated: bool
    backend_access_control: bool
    dataset_isolation: bool

    @property
    def security_label(self) -> str:
        if self.mode is DeploymentMode.SINGLE_USER_DEVELOPMENT:
            return "single-user development; not a secure shared configuration"
        return "authenticated shared deployment"

    def validate(self) -> None:
        require_shared_security(
            shared_enabled=self.mode is DeploymentMode.SHARED,
            authenticated=self.authenticated,
            backend_access_control=self.backend_access_control,
            dataset_isolation=self.dataset_isolation,
        )


def require_explicit_query_scope(
    *,
    service_project_id: str,
    requested_project_ids: tuple[str, ...],
    authorized_project_ids: frozenset[str],
    explicit_cross_project: bool,
) -> None:
    """Reject implicit or partially authorized cross-project recall."""

    if not requested_project_ids or len(set(requested_project_ids)) != len(requested_project_ids):
        raise ProjectIsolationError("query scope must name unique project identities")
    requested = frozenset(requested_project_ids)
    if service_project_id not in requested:
        raise ProjectIsolationError("query scope must include the current project")
    if len(requested) > 1 and not explicit_cross_project:
        raise ProjectIsolationError("cross-project recall requires an explicit query scope")
    if not requested.issubset(authorized_project_ids):
        raise ProjectIsolationError("query scope includes an unauthorized project")


def require_shared_security(
    *,
    shared_enabled: bool,
    authenticated: bool,
    backend_access_control: bool,
    dataset_isolation: bool,
) -> None:
    """Block shared mode unless every required access-control gate is active."""

    if shared_enabled and not (authenticated and backend_access_control and dataset_isolation):
        raise PolicyDisabledError(
            "shared mode requires authentication, backend access control, and dataset isolation"
        )
