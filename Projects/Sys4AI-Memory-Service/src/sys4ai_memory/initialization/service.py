"""Shared preflight and project-confined initialization entry points."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from sys4ai_memory.configuration import LoadedConfiguration, load_configuration
from sys4ai_memory.contracts._base import ContractModel
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.security.locks import exclusive_file_lock
from sys4ai_memory.sources import RegistryBundle, SourceDiscovery, load_registry_bundle
from sys4ai_memory.sources.discovery import DiscoveryReason, DiscoveryReport
from sys4ai_memory.util import (
    PathBoundaryError,
    atomic_write_text,
    canonical_json_bytes,
    resolve_within,
    sha256_bytes,
)


class InitializationError(RuntimeError):
    """Initialization could not satisfy configuration, source, or path safety."""


class PlannedPath(ContractModel):
    relative_path: str
    purpose: str
    kind: Literal["directory", "file"]
    mode: Annotated[int, Field(ge=0, le=0o777)]


class InitializationPreview(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    project_id: str
    project_root: str
    provider: str
    provider_version: str
    deployment_profile: str
    configuration_fingerprint: str
    included_source_count: Annotated[int, Field(ge=0)]
    excluded_source_count: Annotated[int, Field(ge=0)]
    planned_paths: tuple[PlannedPath, ...]
    security_posture: tuple[str, ...]
    warnings: tuple[str, ...]
    impact_digest: str

    def without_digest(self) -> dict[str, object]:
        return self.model_dump(mode="json", exclude={"impact_digest"})


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _planned_paths(loaded: LoadedConfiguration) -> tuple[PlannedPath, ...]:
    data_root = loaded.resolved_paths["local_data"]
    return (
        PlannedPath(
            relative_path=_relative(loaded.project_root, data_root),
            purpose="private derived-memory root",
            kind="directory",
            mode=0o700,
        ),
        PlannedPath(
            relative_path=_relative(loaded.project_root, data_root / "exact_index"),
            purpose="deterministic exact and lexical index",
            kind="directory",
            mode=0o700,
        ),
        PlannedPath(
            relative_path=_relative(loaded.project_root, data_root / "provider"),
            purpose="provider-owned disposable storage",
            kind="directory",
            mode=0o700,
        ),
        PlannedPath(
            relative_path=_relative(loaded.project_root, data_root / "generations"),
            purpose="rebuild generations and activation pointer",
            kind="directory",
            mode=0o700,
        ),
        PlannedPath(
            relative_path=_relative(loaded.project_root, data_root / "staging"),
            purpose="noncanonical operation staging",
            kind="directory",
            mode=0o700,
        ),
        PlannedPath(
            relative_path=_relative(loaded.project_root, data_root / "exports"),
            purpose="policy-filtered local export staging",
            kind="directory",
            mode=0o700,
        ),
        PlannedPath(
            relative_path=_relative(loaded.project_root, data_root / "audit"),
            purpose="metadata-only local audit output",
            kind="directory",
            mode=0o700,
        ),
        PlannedPath(
            relative_path=_relative(loaded.project_root, data_root / "receipts"),
            purpose="derived initialization and operation receipts",
            kind="directory",
            mode=0o700,
        ),
        PlannedPath(
            relative_path=_relative(loaded.project_root, loaded.resolved_paths["model_cache"]),
            purpose="project-local disposable model cache",
            kind="directory",
            mode=0o700,
        ),
    )


def build_initialization_preview(
    loaded: LoadedConfiguration,
    *,
    included_source_count: int,
    excluded_source_count: int,
    warnings: tuple[str, ...] = (),
) -> InitializationPreview:
    """Legacy/root-adoption preview; the direct entry point never calls this."""

    if included_source_count < 0 or excluded_source_count < 0:
        raise InitializationError("source counts must be non-negative")
    memory = loaded.configuration.memory
    planned = _planned_paths(loaded)
    provisional = {
        "schema_version": "1.0",
        "project_id": memory.project_id,
        "project_root": str(loaded.project_root),
        "provider": memory.provider.name,
        "provider_version": memory.provider.version_constraint,
        "deployment_profile": memory.deployment_profile,
        "configuration_fingerprint": loaded.fingerprint,
        "included_source_count": included_source_count,
        "excluded_source_count": excluded_source_count,
        "planned_paths": [item.model_dump(mode="json") for item in planned],
        "security_posture": [
            "project-root confined paths",
            "secret scanning required",
            "cloud fallback denied",
            "native provider clients denied",
            "single writer required",
        ],
        "warnings": list(warnings),
    }
    digest = sha256_bytes(canonical_json_bytes(provisional))
    return InitializationPreview.model_validate({**provisional, "impact_digest": digest})


def validate_initialization_paths(loaded: LoadedConfiguration) -> None:
    """Check every target before creating the first derived directory."""

    root = loaded.project_root
    data_root = loaded.resolved_paths["local_data"]
    try:
        relative_root = data_root.relative_to(root)
        if relative_root.as_posix() != ".sys4ai/memory":
            raise InitializationError("derived root must be the project-local .sys4ai/memory")
        directories = [root / item.relative_path for item in _planned_paths(loaded)]
        directories += [loaded.resolved_paths["model_cache"]]
        files = [
            data_root / "receipts" / "initialization.json",
            data_root / "receipts" / "sync-state.json",
            data_root / ".runtime.lock",
            loaded.resolved_paths["exact_index"],
            loaded.resolved_paths["audit_log"],
            Path(str(loaded.resolved_paths["audit_log"]) + ".lock"),
            *(
                Path(str(loaded.resolved_paths["exact_index"]) + suffix)
                for suffix in ("-wal", "-shm", "-journal")
            ),
        ]
        if (
            len(files) != len(set(files))
            or any(
                path == directory or path in directory.parents
                for path in files
                for directory in directories
            )
            or any(path in other.parents for path in files for other in files if path != other)
        ):
            raise InitializationError("derived file and directory targets must not overlap")
        for target in (*directories, *files):
            target.relative_to(data_root)
            resolve_within(root, target.relative_to(root), must_exist=False)
            for parent in target.parents:
                if parent == root:
                    break
                if parent.exists() and not parent.is_dir():
                    raise InitializationError("initialization path parent is not a directory")
        if any(target.exists() and not target.is_dir() for target in directories):
            raise InitializationError("initialization directory target is not a directory")
        if any(
            target.exists() and (not target.is_file() or target.stat().st_nlink != 1)
            for target in files
        ):
            raise InitializationError("initialization file target must be one regular file")
        if loaded.resolved_paths["exact_index"] == loaded.resolved_paths["audit_log"]:
            raise InitializationError("derived index and audit targets must be distinct")
    except (ValueError, PathBoundaryError) as error:
        raise InitializationError("initialization path is unsafe or crosses a symlink") from error


@dataclass(frozen=True, slots=True)
class InitializationPreflight:
    """Internal validation result, never an approval artifact or preview digest."""

    discovery: DiscoveryReport


def _validate_existing_receipt(loaded: LoadedConfiguration) -> None:
    """Refuse to rebind an initialized directory to another identity or config."""

    receipt = loaded.resolved_paths["local_data"] / "receipts/initialization.json"
    if not receipt.exists():
        return
    try:
        if not receipt.is_file() or receipt.is_symlink() or receipt.stat().st_nlink != 1:
            raise InitializationError("existing initialization receipt must be one regular file")
        if receipt.stat().st_size > 64 * 1024:
            raise InitializationError("existing initialization receipt is oversized")
        payload = json.loads(receipt.read_bytes())
    except (OSError, ValueError, UnicodeError) as error:
        raise InitializationError("existing initialization receipt is invalid") from error
    memory = loaded.configuration.memory
    if not isinstance(payload, dict) or (
        payload.get("schema_version") != "1.0"
        or payload.get("project_id") != memory.project_id
        or payload.get("dataset_id") != memory.provider.cognee.dataset
        or payload.get("configuration_fingerprint") != loaded.fingerprint
        or payload.get("provider") != memory.provider.name
        or payload.get("exact_index_initialized") is not True
        or not isinstance(payload.get("provider_initialized"), bool)
        or not isinstance(payload.get("models_activated"), bool)
        or payload.get("initialization_mode") not in {"direct", "reviewed"}
    ):
        raise InitializationError(
            "existing initialization receipt identity or configuration differs"
        )


def preflight_initialization(
    loaded: LoadedConfiguration,
    *,
    registry: RegistryBundle | None = None,
    require_enabled: bool = True,
) -> InitializationPreflight:
    """Reread configuration and validate registered sources without storage I/O."""

    validate_initialization_paths(loaded)
    _validate_existing_receipt(loaded)
    current = load_configuration(
        loaded.configuration_path, trusted_project_root=loaded.project_root
    )
    if current.fingerprint != loaded.fingerprint or current.resolved_paths != loaded.resolved_paths:
        raise InitializationError("configuration changed before initialization")
    if require_enabled:
        loaded.require("exact")
    memory = loaded.configuration.memory
    if (
        memory.sources.default_include
        or not memory.sources.require_registered_rule
        or not memory.sources.require_discovery_dry_run
        or not memory.sources.respect_gitignore
        or not memory.security.secret_scan
    ):
        raise InitializationError("initialization requires registered, excluded, scanned sources")
    bundle = registry or load_registry_bundle(
        source_registry=loaded.resolved_paths["source_registry"],
        profile_registry=loaded.resolved_paths["profile_registry"],
        relation_registry=loaded.resolved_paths["relation_registry"],
        project_root=loaded.project_root,
    )
    if any(entry.project_id != memory.project_id for entry in bundle.sources):
        raise InitializationError("source registry belongs to a different project")
    report = SourceDiscovery(
        project_root=loaded.project_root,
        project_id=memory.project_id,
        entries=bundle.sources,
        respect_gitignore=True,
        secret_scan=True,
    ).discover()
    unsafe = {DiscoveryReason.UNSAFE_PATH, DiscoveryReason.SYMLINK, DiscoveryReason.AMBIGUOUS}
    if any(decision.reason in unsafe for decision in report.decisions):
        raise InitializationError("source discovery rejected an unsafe or ambiguous registration")
    return InitializationPreflight(discovery=report)


def _mkdir_private(path: Path, *, root: Path) -> None:
    target = resolve_within(root, path.relative_to(root), must_exist=False)
    missing = [target]
    parent = target.parent
    while parent != root and not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700, exist_ok=True)
    os.chmod(target, 0o700)


def _initialize_storage(
    loaded: LoadedConfiguration,
    *,
    receipt_fields: dict[str, object],
    initialize_provider: Callable[[], bool] | None = None,
) -> Path:
    """One storage implementation for both direct and digest-bound callers."""

    validate_initialization_paths(loaded)
    data_root = loaded.resolved_paths["local_data"]
    _mkdir_private(data_root, root=loaded.project_root)
    with exclusive_file_lock(data_root / ".runtime.lock"):
        return _publish_initialized_storage(
            loaded, receipt_fields=receipt_fields, initialize_provider=initialize_provider
        )


def _publish_initialized_storage(
    loaded: LoadedConfiguration,
    *,
    receipt_fields: dict[str, object],
    initialize_provider: Callable[[], bool] | None,
) -> Path:
    validate_initialization_paths(loaded)
    _validate_existing_receipt(loaded)
    planned = _planned_paths(loaded)
    for item in planned:
        _mkdir_private(loaded.project_root / item.relative_path, root=loaded.project_root)
    index_path = loaded.resolved_paths["exact_index"]
    _mkdir_private(index_path.parent, root=loaded.project_root)
    with ExactIndex(index_path):
        os.chmod(index_path, 0o600)
    provider_initialized = initialize_provider() if initialize_provider is not None else False
    receipt = loaded.resolved_paths["local_data"] / "receipts" / "initialization.json"
    payload = {
        "schema_version": "1.0",
        "project_id": loaded.configuration.memory.project_id,
        "dataset_id": loaded.configuration.memory.provider.cognee.dataset,
        "configuration_fingerprint": loaded.fingerprint,
        "provider": loaded.configuration.memory.provider.name,
        "provider_initialized": provider_initialized,
        "exact_index_initialized": True,
        "models_activated": False,
        "created_paths": [item.relative_path for item in planned],
        **receipt_fields,
    }
    # Publication is last. Failed index/provider initialization never publishes success.
    atomic_write_text(receipt, json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    return receipt


def initialize_memory(
    loaded: LoadedConfiguration,
    *,
    authorized: bool,
    registry: RegistryBundle | None = None,
    initialize_provider: Callable[[], bool] | None = None,
) -> Path:
    """Initialize project memory directly after preflight, with no preview or digest.

    Callers authenticate the operation before setting ``authorized``. A configured
    provider callback runs only after validation and exact-index initialization.
    The receipt distinguishes exact storage, provider storage, and model activation.
    """

    if not authorized:
        raise InitializationError("explicit initialization authorization is required")
    checked = preflight_initialization(loaded, registry=registry)
    return _initialize_storage(
        loaded,
        receipt_fields={
            "initialization_mode": "direct",
            "included_source_count": len(checked.discovery.records),
            "excluded_source_count": len(checked.discovery.excluded),
        },
        initialize_provider=initialize_provider,
    )


def apply_initialization(
    loaded: LoadedConfiguration,
    preview: InitializationPreview,
    *,
    accepted_impact_digest: str,
    authorized: bool,
    registry: RegistryBundle | None = None,
    initialize_provider: Callable[[], bool] | None = None,
) -> Path:
    """Create only previewed derived directories and a non-sensitive receipt."""

    if not authorized:
        raise InitializationError("explicit initialization authorization is required")
    if accepted_impact_digest != preview.impact_digest:
        raise InitializationError("accepted impact digest does not match the current preview")
    recalculated = sha256_bytes(canonical_json_bytes(preview.without_digest()))
    if recalculated != preview.impact_digest:
        raise InitializationError("preview content does not match its impact digest")
    if preview.configuration_fingerprint != loaded.fingerprint:
        raise InitializationError("configuration changed after preview")
    if preview.project_root != str(loaded.project_root):
        raise InitializationError("project root changed after preview")
    memory = loaded.configuration.memory
    if (
        preview.project_id != memory.project_id
        or preview.provider != memory.provider.name
        or preview.provider_version != memory.provider.version_constraint
        or preview.deployment_profile != memory.deployment_profile
    ):
        raise InitializationError("preview identity does not match the current configuration")
    if preview.planned_paths != _planned_paths(loaded):
        raise InitializationError("preview paths differ from the allowed initialization paths")
    preflight_initialization(loaded, registry=registry)
    return _initialize_storage(
        loaded,
        receipt_fields={
            "initialization_mode": "reviewed",
            "impact_digest": preview.impact_digest,
        },
        initialize_provider=initialize_provider,
    )
