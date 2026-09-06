"""Install canonical consumer files without initializing derived memory.

All entry routes call this function before the shared ``init-memory`` operation.
Resource templates are read through importlib.resources, never from a sibling
checkout. Conflicts are detected before publication; an interrupted publication
can be completed by retrying the same identity without replacing existing files.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from sys4ai_memory.authorization import CanonicalPermissionDocument
from sys4ai_memory.configuration import load_configuration
from sys4ai_memory.contracts import AuthorityTier
from sys4ai_memory.profiles import (
    ProfileSourceAuthority,
    load_profile_set,
    validate_profile_registrations,
)
from sys4ai_memory.security import SecretDetectedError, require_secret_free
from sys4ai_memory.sources import load_registry_bundle
from sys4ai_memory.util import resolve_within

_PROJECT_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_PRINCIPAL_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:@-]*$")
_PERMISSIONS_PATH = "control_records/memory/permissions.json"
_CONFIGURATION_PATH = "config/memory.toml"
_CAPABILITIES = frozenset(
    {
        "service_health",
        "source_registry",
        "ingestion",
        "exact",
        "lexical",
        "provenance_explanation",
        "semantic",
        "graph",
    }
)


class PreparationError(ValueError):
    """Consumer preparation failed before initialization or an unsafe overwrite."""


@dataclass(frozen=True, slots=True)
class PreparationResult:
    project_root: Path
    project_id: str
    project_name: str
    principal_id: str
    dataset_id: str
    resource_version: str
    configuration_path: str
    created_files: tuple[str, ...]
    updated_files: tuple[str, ...]
    preserved_files: tuple[str, ...]
    initialization_performed: bool = False
    semantic_status: str = "deferred"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "prepared",
            "project_root": str(self.project_root),
            "project_id": self.project_id,
            "project_name": self.project_name,
            "principal_id": self.principal_id,
            "dataset_id": self.dataset_id,
            "resource_version": self.resource_version,
            "configuration_path": self.configuration_path,
            "created_files": list(self.created_files),
            "updated_files": list(self.updated_files),
            "preserved_files": list(self.preserved_files),
            "initialization_performed": self.initialization_performed,
            "semantic_status": self.semantic_status,
            "next_operation": "init-memory",
        }


def _trusted_root(project_root: Path) -> Path:
    if (
        not project_root.is_absolute()
        or ".." in project_root.parts
        or not project_root.is_dir()
        or any(item.is_symlink() for item in (project_root, *project_root.parents))
    ):
        raise PreparationError("project_root must be an existing absolute non-symlink directory")
    return project_root.resolve(strict=True)


def _target(root: Path, relative: str) -> Path:
    try:
        target = resolve_within(root, relative, must_exist=False)
    except (OSError, ValueError) as error:
        raise PreparationError(f"unsafe preparation path: {relative}") from error
    for item in target.parents:
        if item == root:
            break
        if item.exists() and not item.is_dir():
            raise PreparationError(f"preparation parent is not a directory: {relative}")
    if target.exists() and (not target.is_file() or target.stat().st_nlink != 1):
        raise PreparationError(f"preparation target must be one regular file: {relative}")
    return target


def _replace_values(value: Any, substitutions: dict[str, str]) -> Any:
    if isinstance(value, str):
        # One substitution pass prevents user text containing a template marker
        # from being interpreted as a second template instruction.
        return re.sub(
            r"__(PROJECT_ID|PROJECT_NAME|PRINCIPAL_ID|DATASET_ID|ISSUED_AT)__",
            lambda match: substitutions[match[1]],
            value,
        )
    if isinstance(value, dict):
        return {key: _replace_values(item, substitutions) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_values(item, substitutions) for item in value]
    return value


def _render(relative: str, raw: str, substitutions: dict[str, str]) -> bytes:
    if relative.endswith(".json"):
        payload = _replace_values(json.loads(raw), substitutions)
        return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode()
    if relative.endswith(".jsonl"):
        return "".join(
            json.dumps(_replace_values(json.loads(line), substitutions), ensure_ascii=False) + "\n"
            for line in raw.splitlines()
            if line
        ).encode()
    if relative.endswith(".csv"):
        rows = csv.reader(io.StringIO(raw, newline=""), strict=True)
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerows(_replace_values(list(row), substitutions) for row in rows)
        return stream.getvalue().encode()
    return str(_replace_values(raw, substitutions)).encode()


def _equivalent(relative: str, current: bytes, proposed: bytes) -> bool:
    if current == proposed:
        return True
    try:
        if relative.endswith(".json"):
            return bool(_unique_json(current) == _unique_json(proposed))
        if relative.endswith(".jsonl"):
            return [json.loads(line) for line in current.splitlines() if line.strip()] == [
                json.loads(line) for line in proposed.splitlines() if line.strip()
            ]
        if relative.endswith(".toml"):
            return tomllib.loads(current.decode()) == tomllib.loads(proposed.decode())
        if relative.endswith((".yaml", ".yml")):
            return bool(yaml.safe_load(current) == yaml.safe_load(proposed))
        if relative.endswith(".csv"):
            return list(csv.reader(io.StringIO(current.decode()), strict=True)) == list(
                csv.reader(io.StringIO(proposed.decode()), strict=True)
            )
    except (ValueError, UnicodeError, yaml.YAMLError, csv.Error):
        return False
    return False


def _unique_json(raw: bytes) -> Any:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("ambiguous JSON object has duplicate keys")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=object_pairs)


def _permission_timestamp(root: Path) -> str:
    target = _target(root, _PERMISSIONS_PATH)
    if target.exists():
        try:
            existing = CanonicalPermissionDocument.model_validate(_unique_json(target.read_bytes()))
            return existing.issued_at.isoformat()
        except ValueError as error:
            raise PreparationError(f"conflicting canonical file: {_PERMISSIONS_PATH}") from error
    return datetime.now(UTC).isoformat()


def _validate_generated(root: Path) -> None:
    loaded = load_configuration(root / _CONFIGURATION_PATH, trusted_project_root=root)
    registry = load_registry_bundle(
        source_registry=loaded.resolved_paths["source_registry"],
        profile_registry=loaded.resolved_paths["profile_registry"],
        relation_registry=loaded.resolved_paths["relation_registry"],
        project_root=root,
    )
    if any(row.project_id != loaded.configuration.memory.project_id for row in registry.sources):
        raise PreparationError("generated registry identity differs from configuration")
    profiles = load_profile_set(
        tuple(root / row.config_ref for row in registry.profiles),
        trusted_project_root=root,
        enabled_capabilities=_CAPABILITIES,
        source_authorities={
            row.profile_id: ProfileSourceAuthority(
                source_ref="consumer-preparation@1",
                authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
            )
            for row in registry.profiles
        },
    )
    validate_profile_registrations(profiles, registry.profiles)
    permission = CanonicalPermissionDocument.model_validate_json(
        (root / _PERMISSIONS_PATH).read_bytes()
    )
    if (
        permission.project_id != loaded.configuration.memory.project_id
        or permission.dataset_id != loaded.configuration.memory.provider.cognee.dataset
    ):
        raise PreparationError("generated permissions differ from configuration identity")


def _publish_new_file(root: Path, relative: str, proposed: bytes) -> None:
    target = _target(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target = _target(root, relative)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    identity = os.fstat(descriptor)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(proposed)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        # Remove only the incomplete file created by this call, never a file
        # another writer substituted. Earlier complete resources remain retryable.
        if not target.is_symlink() and target.exists():
            current = target.stat()
            if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                target.unlink()
        raise


def prepare_project_memory(
    project_root: Path,
    project_id: str,
    project_name: str,
    principal_id: str,
    *,
    allow_source_registration: bool = False,
) -> PreparationResult:
    """Prepare one consumer; callers supply identity and project-write authority.

    This operation grants only the named owner's confined read, synchronization,
    and initialization operations. Reviewed source-registration authority is a
    separate opt-in. Semantic models, providers, servers and derived storage are
    never activated here. An existing canonical file is accepted only when its
    contents are equivalent to the requested template specialization.
    """

    root = _trusted_root(Path(project_root))
    if not _PROJECT_ID.fullmatch(project_id) or len(project_id) > 100:
        raise PreparationError("project_id must be a lowercase hyphenated identifier")
    if not _PRINCIPAL_ID.fullmatch(principal_id) or len(principal_id) > 128:
        raise PreparationError("principal_id must be a stable caller identifier")
    if (
        not project_name.strip()
        or project_name != project_name.strip()
        or len(project_name) > 200
        or any(ord(char) < 32 for char in project_name)
    ):
        raise PreparationError("project_name must be one nonblank line without outer whitespace")
    try:
        require_secret_free(
            (project_id, project_name, principal_id), field_path="consumer_identity"
        )
    except SecretDetectedError as error:
        raise PreparationError("consumer identity must not contain credential-like text") from error
    # Preparation must reject unsafe future derived paths before canonical writes.
    for relative in (".sys4ai/memory", ".sys4ai/memory/models"):
        try:
            target = resolve_within(root, relative, must_exist=False)
            if target.exists() and not target.is_dir():
                raise ValueError("derived target is not a directory")
            for parent in target.parents:
                if parent == root:
                    break
                if parent.exists() and not parent.is_dir():
                    raise ValueError("derived parent is not a directory")
        except (OSError, ValueError) as error:
            raise PreparationError("unsafe future derived-memory path") from error

    package = files("sys4ai_memory.package_data").joinpath("consumer_v1")
    manifest = json.loads(package.joinpath("manifest.json").read_text(encoding="utf-8"))
    dataset_id = f"{project_id}-memory"
    substitutions = {
        "PROJECT_ID": project_id,
        "PROJECT_NAME": project_name,
        "PRINCIPAL_ID": principal_id,
        "DATASET_ID": dataset_id,
        "ISSUED_AT": _permission_timestamp(root),
    }
    proposed: dict[str, bytes] = {}
    for relative in manifest["files"]:
        _target(root, relative)
        proposed[relative] = _render(
            relative, package.joinpath(relative).read_text(encoding="utf-8"), substitutions
        )
    if allow_source_registration:
        permissions = json.loads(proposed[_PERMISSIONS_PATH])
        permissions["grants"].append(
            {
                "grant_id": "consumer-owner-reviewed-registration",
                "principal_id": principal_id,
                "permissions": ["administer"],
                "operations": ["memory.sources.register"],
                "scopes": [{"level": "project", "scope_id": project_id, "parent_scopes": []}],
                "target_prefixes": ["registries/memory_source_registry.csv"],
                "shared_project_ids": [],
                "valid_until": None,
            }
        )
        proposed[_PERMISSIONS_PATH] = (json.dumps(permissions, indent=2) + "\n").encode()

    current = {
        relative: target.read_bytes() if target.exists() else None
        for relative in proposed
        for target in (_target(root, relative),)
    }
    conflicts = [
        relative
        for relative, raw in current.items()
        if raw is not None and not _equivalent(relative, raw, proposed[relative])
    ]
    if conflicts:
        raise PreparationError("conflicting canonical files: " + ", ".join(sorted(conflicts)))

    ignore_path = _target(root, ".gitignore")
    ignore_before = ignore_path.read_bytes() if ignore_path.exists() else None
    try:
        ignore_text = (ignore_before or b"").decode("utf-8")
    except UnicodeError as error:
        raise PreparationError(".gitignore must be UTF-8") from error
    required_rules = package.joinpath("ignore-rules.txt").read_text(encoding="utf-8").splitlines()
    # A final block also defeats an earlier negation that would otherwise expose
    # generated memory. An unchanged rerun adds no repeated block.
    existing_lines = ignore_text.rstrip().splitlines()
    rules_at_end = existing_lines[-len(required_rules) :] == required_rules
    ignore_after = ignore_before or b""
    if not rules_at_end:
        separator = "\n" if ignore_text and not ignore_text.endswith("\n") else ""
        ignore_after += (
            separator
            + "\n# Project-local memory, environments, caches and secrets\n"
            + "\n".join(required_rules)
            + "\n"
        ).encode()

    # Validate the effective bytes, including equivalent project-owned formatting,
    # in an isolated tree before touching any live destination.
    with TemporaryDirectory(prefix="sys4ai-consumer-validation-") as temporary:
        staging = Path(temporary).resolve(strict=True)
        for relative, raw in proposed.items():
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            existing = current[relative]
            target.write_bytes(existing if existing is not None else raw)
        _validate_generated(staging)

    # Recheck all destinations after validation. Never replace a canonical file.
    for relative, expected in {**current, ".gitignore": ignore_before}.items():
        target = _target(root, relative)
        actual = target.read_bytes() if target.exists() else None
        if actual != expected:
            raise PreparationError(f"preparation destination changed during validation: {relative}")
    created: list[str] = []
    updated: list[str] = []
    if ignore_before is None:
        _publish_new_file(root, ".gitignore", ignore_after)
        created.append(".gitignore")
    elif ignore_after != ignore_before:
        # Append only; retain every pre-existing rule and its order.
        descriptor = os.open(ignore_path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "ab") as stream:
            stream.write(ignore_after[len(ignore_before) :])
            stream.flush()
            os.fsync(stream.fileno())
        updated.append(".gitignore")
    for relative, raw in proposed.items():
        if current[relative] is None:
            _publish_new_file(root, relative, raw)
            created.append(relative)
    return PreparationResult(
        project_root=root,
        project_id=project_id,
        project_name=project_name,
        principal_id=principal_id,
        dataset_id=dataset_id,
        resource_version=manifest["resource_version"],
        configuration_path=_CONFIGURATION_PATH,
        created_files=tuple(sorted(created)),
        updated_files=tuple(updated),
        preserved_files=tuple(
            sorted(relative for relative, raw in current.items() if raw is not None)
        ),
    )
