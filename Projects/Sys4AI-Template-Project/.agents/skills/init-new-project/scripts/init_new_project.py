#!/usr/bin/env python3
"""Create or prepare one selected Sys4AI project from governance starter assets.

The installed skill determines the owning depot. Starter assets come only from
its registered Template. The helper uses Python standard library facilities and
read-only Git observations; project dependencies are managed separately.
"""

from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from copy import deepcopy
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

TEMPLATE = "Projects/Sys4AI-Template-Project"
REQUIRED_SKILLS = {
    "agent-task", "communication", "init-new-project", "manage-subagent-roles", "task",
    "to-implementation-plan", "to-trd",
}
TEMPLATE_POLICY = ".template/baseline-assets.json"
README_RENDERER = ".template/project-readme.md"
STARTER_FILES = {
    "AGENTS.md", "ROLE.md", ".gitignore", "README.md", "SPECS.md",
    "Implementation_Plans/subagent_role_system_implementation_plan.md",
    "Implementation_Plans/task_system_implementation_plan.md", "Tasks/INDEX.md",
}
IDENTITY = "project.json"
RECORD = "control_records/project-setup.json"
SETUP_CONTRACT = "governance-starter-v1"
STAGES = ["assets", "registration", "verification"]
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
EXCLUDED = {
    ".git",
    ".gitmodules",
    ".gitignore_global",
    ".venv",
    "venv",
    "env",
    "ENV",
    ".sys4ai",
    ".template",
    "__pycache__",
    ".DS_Store",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".cache",
    "models",
    "logs",
    ".cognee",
    ".cognee_system",
    ".data_storage",
    "dist",
    "build",
    "node_modules",
    ".env",
    ".envrc",
    ".secrets",
    "secrets",
}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".log", ".zip", ".whl", ".egg")
RESERVED = {
    "sys4ai",
    "sys4ai-depot",
    "sys4ai-template-project",
    "template",
}


class InitializationError(RuntimeError):
    """A bounded conflict or recorded incomplete operation."""

    def __init__(self, reason: str, *, report: dict[str, Any] | None = None):
        super().__init__(reason)
        self.report = report


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()


def unique_json(raw: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise InitializationError("duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as error:
        raise InitializationError("invalid JSON document") from error


def safe(candidate: Path) -> Path:
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise InitializationError("absolute paths without traversal are required")
    if any(item.is_symlink() for item in (candidate, *candidate.parents)):
        raise InitializationError("paths must not cross symbolic links")
    return candidate


def file_bytes(candidate: Path) -> bytes:
    safe(candidate)
    info = candidate.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise InitializationError("inputs must be regular non-aliased files")
    data = candidate.read_bytes()
    after = candidate.stat()
    if (info.st_ino, info.st_size, info.st_mtime_ns) != (
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise InitializationError("input changed while being read")
    return data


def installed_locations() -> tuple[Path, Path]:
    script = safe(Path(__file__).absolute())
    skill = script.parent.parent
    if skill.name != "init-new-project" or script.parent.name != "scripts":
        raise InitializationError("helper must run from its installed skill package")
    if skill.parent.name == "SKILLS-depo":
        owner = skill.parent.parent
    elif skill.parent.name == "skills" and skill.parent.parent.name == ".agents":
        owner = skill.parent.parent.parent
    else:
        raise InitializationError(
            "skill must be installed in the depot or a registered project's active skills"
        )
    # A copied initializer may live in the registered template or a consumer.
    # Only its nearest owning registry can establish the depot; no cwd or caller
    # argument can redirect it to another workspace.
    for depot in (owner, *owner.parents):
        registry_path = safe(depot / "depot/projects.json")
        if not registry_path.exists():
            continue
        registry, _ = read_registry(depot)
        relative = owner.relative_to(depot).as_posix()
        if not any(entry["path"] == relative for entry in registry["projects"]):
            raise InitializationError("installed skill owner is not a registered project")
        if skill.parent.name == "SKILLS-depo" and owner != depot:
            raise InitializationError("reusable source skills must belong to the depot root")
        return depot, skill
    raise InitializationError("the installed skill has no owning Sys4AI registry")


def text_value(value: str, field: str, maximum: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or any(ord(char) < 32 for char in value)
    ):
        raise InitializationError(f"{field} must be a nonblank single line")
    if re.search(
        r"(?i)(?:sk-[a-z0-9_-]{16,}|(?:password|api[_-]?key|secret|token)\s*[=:]|-----BEGIN|https?://[^ /]+:[^ /]+@)",
        value,
    ):
        raise InitializationError(
            "identity and purpose must not contain credential-like text"
        )


def validate_identity(
    project_id: str, project_name: str, purpose: str
) -> None:
    if (
        not isinstance(project_id, str)
        or not ID_PATTERN.fullmatch(project_id)
        or len(project_id) > 100
        or project_id in RESERVED
    ):
        raise InitializationError("project ID is malformed or reserved")
    text_value(project_name, "project name", 200)
    text_value(purpose, "purpose", 4000)
    if "sys4ai template project" in project_name.casefold():
        raise InitializationError("a product needs its own name")


def read_registry(depot: Path) -> tuple[dict[str, Any], bytes]:
    registry_path = depot / "depot/projects.json"
    raw = file_bytes(registry_path)
    if len(raw) > 5_000_000:
        raise InitializationError("registry is oversized")
    registry = unique_json(raw)
    if (
        not isinstance(registry, dict)
        or registry.get("schema_version") != 2
        or registry.get("workspace_name") != "Sys4AI"
        or not isinstance(registry.get("projects"), list)
    ):
        raise InitializationError(
            "expected the Sys4AI schema-2 factual project registry"
        )
    ids: set[str] = set()
    paths: set[str] = set()
    for entry in registry["projects"]:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("id"), str)
            or not ID_PATTERN.fullmatch(entry["id"])
        ):
            raise InitializationError("registry project ID is invalid")
        path = entry.get("path")
        if (
            not isinstance(path, str)
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or Path(path).as_posix() != path
        ):
            raise InitializationError("registry path is not canonical and relative")
        if path != "." and not path.startswith("Projects/"):
            raise InitializationError("registry project path is outside Projects")
        if entry["id"] in ids or path.casefold() in paths:
            raise InitializationError("registry contains duplicate identity or path")
        ids.add(entry["id"])
        paths.add(path.casefold())
        if (
            entry.get("registered") is not True
            or not isinstance(entry.get("name"), str)
            or not entry["name"].strip()
            or entry.get("kind")
            not in {"depot-manager", "project-template", "product-project"}
        ):
            raise InitializationError("registry entry is incomplete")
        for section, values in (
            ("repository", {"initialized", "not_initialized"}),
            ("github_pages", {"configured", "not_configured"}),
        ):
            state = entry.get(section)
            link = "remote" if section == "repository" else "url"
            if (
                not isinstance(state, dict)
                or state.get("status") not in values
                or link not in state
                or not (state[link] is None or isinstance(state[link], str))
            ):
                raise InitializationError(
                    "registry external-state observation is invalid"
                )
            if state["status"].startswith("not_") and state[link] is not None:
                raise InitializationError(
                    "registry invents unconfigured external state"
                )
        target = safe(depot / path)
        if not target.is_dir():
            raise InitializationError("registry project does not exist")
    required = {
        "sys4ai-depot": (".", "depot-manager"),
        "sys4ai-template-project": (TEMPLATE, "project-template"),
    }
    for identifier, (relative, kind) in required.items():
        entries = [entry for entry in registry["projects"] if entry["id"] == identifier]
        if (
            len(entries) != 1
            or entries[0]["path"] != relative
            or entries[0]["kind"] != kind
        ):
            raise InitializationError(
                "exact registered depot and template identities are required"
            )
    return registry, raw


def validate_destination(
    depot: Path, registry: dict[str, Any], destination: Path, project_id: str
) -> str:
    safe(destination)
    projects = safe(depot / "Projects")
    if destination == projects or not destination.is_relative_to(projects):
        raise InitializationError(
            "destination must be beneath this depot's Projects container"
        )
    relative = destination.relative_to(depot).as_posix()
    if any(
        part in EXCLUDED or part.startswith(".")
        for part in destination.relative_to(projects).parts
    ):
        raise InitializationError("destination uses a reserved path component")
    if not destination.parent.is_dir():
        raise InitializationError(
            "destination parent must already exist beneath Projects"
        )
    for entry in registry["projects"]:
        other = depot / entry["path"]
        if entry["path"] == ".":
            continue
        same = relative.casefold() == entry["path"].casefold()
        if entry["id"] == project_id and not same:
            raise InitializationError(
                "project ID is already registered at another path"
            )
        if same and entry["id"] != project_id:
            raise InitializationError("destination is registered to another project")
        if not same and (
            destination.is_relative_to(other) or other.is_relative_to(destination)
        ):
            raise InitializationError("destination overlaps another registered project")
    if relative == TEMPLATE:
        raise InitializationError("source projects cannot be initialization targets")
    return relative


def excluded(relative: Path) -> bool:
    return any(
        part in EXCLUDED or part.startswith(("._", ".env.")) for part in relative.parts
    ) or relative.name.endswith(EXCLUDED_SUFFIXES)


def tree_files(root: Path) -> dict[str, bytes]:
    safe(root)
    if not root.is_dir():
        raise InitializationError("template asset tree is missing")
    collected: dict[str, bytes] = {}
    for current, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name for name in directories if not excluded(Path(name))
        )
        for name in directories:
            safe(Path(current) / name)
        for name in sorted(filenames):
            candidate = Path(current) / name
            relative = candidate.relative_to(root)
            if not excluded(relative):
                collected[relative.as_posix()] = file_bytes(candidate)
    return collected


def package_files(package: Path) -> dict[str, bytes]:
    collected = tree_files(package)
    if "SKILL.md" not in collected:
        raise InitializationError("template skill has no SKILL.md")
    validate_package(package.name, collected)
    return collected


def package_names(root: Path) -> list[str]:
    safe(root)
    if not root.is_dir():
        raise InitializationError("template package collection is missing")
    names = []
    for package in sorted(root.iterdir()):
        if excluded(Path(package.name)):
            continue
        safe(package)
        if not package.is_dir():
            continue
        if not ID_PATTERN.fullmatch(package.name) or len(package.name) > 64:
            raise InitializationError("template package name is invalid")
        if package.name.casefold() in {name.casefold() for name in names}:
            raise InitializationError("template package name collides")
        names.append(package.name)
    return names


def validate_package(name: str, files: dict[str, bytes]) -> None:
    body = files["SKILL.md"].decode()
    if not body.startswith("---\n") or "\n---" not in body[4:]:
        raise InitializationError("baseline skill frontmatter is missing")
    frontmatter = body.split("---", 2)[1]
    if not re.search(
        r"(?m)^name:\s*[\"']?" + re.escape(name) + r"[\"']?\s*$", frontmatter
    ) or not re.search(r"(?m)^description:\s*\S", frontmatter):
        raise InitializationError(
            "baseline skill metadata differs from its package identity"
        )
    for relative, raw in files.items():
        if relative.endswith(".py"):
            try:
                ast.parse(raw, filename=relative)
            except SyntaxError as error:
                raise InitializationError(
                    "baseline Python resource is invalid"
                ) from error
        elif relative.endswith(".json"):
            unique_json(raw)


def template_sources(
    depot: Path,
) -> tuple[dict[str, bytes], dict[str, Path], dict[str, str], bytes, bytes]:
    template = safe(depot / TEMPLATE)
    policy = file_bytes(template / TEMPLATE_POLICY)
    specification = unique_json(policy)
    if (
        not isinstance(specification, dict)
        or specification.get("schema_version") != 2
        or specification.get("skills") != ".agents/skills"
        or specification.get("roles") != "sub-agent-roles"
        or specification.get("soul") != "SOUL.md"
        or specification.get("template") != TEMPLATE
        or specification.get("readme_template") != README_RENDERER
        or specification.get("optional_trees") != ["reference-assets"]
    ):
        raise InitializationError("template starter policy has unapproved source paths")
    if set(specification) != {"schema_version", "skills", "roles", "soul", "template",
                              "readme_template", "starter_files", "optional_starter_files", "optional_trees"}:
        raise InitializationError("template starter policy has unsupported fields")
    starter_files = specification.get("starter_files")
    optional_files = specification.get("optional_starter_files")
    if (
        not isinstance(starter_files, list)
        or not isinstance(optional_files, list)
        or any(not isinstance(item, str) for item in starter_files + optional_files)
        or len(set(starter_files + optional_files)) != len(starter_files + optional_files)
        or set(starter_files) != STARTER_FILES
        or optional_files != []
    ):
        raise InitializationError("template starter file allowlist is invalid")
    copied: dict[str, bytes] = {}
    origins: dict[str, Path] = {}
    versions: dict[str, str] = {}

    def include(relative: str, raw: bytes, *, version: str | None = None) -> None:
        copied[relative] = raw
        origins[relative] = template / relative
        versions[relative] = version or "sha256:" + sha(raw)

    for relative in starter_files + optional_files:
        source = safe(template / relative)
        if relative in optional_files and not source.exists():
            continue
        include(relative, file_bytes(source))
    include("SOUL.md", file_bytes(template / "SOUL.md"))
    for collection in (".agents/skills", "sub-agent-roles"):
        names = package_names(template / collection)
        required = REQUIRED_SKILLS if collection == ".agents/skills" else {"project-sub-agent"}
        if not required.issubset(names):
            raise InitializationError("template lacks required governance packages or generic role")
        for name in names:
            source = template / collection / name
            package = package_files(source) if collection == ".agents/skills" else tree_files(source)
            if collection == "sub-agent-roles" and not {"AGENTS.md", "ROLE.md"}.issubset(package):
                raise InitializationError("template role bundle lacks AGENTS.md or ROLE.md")
            version = "sha256:" + sha(encoded({relative: sha(raw) for relative, raw in package.items()}))
            for relative, raw in package.items():
                include(f"{collection}/{name}/{relative}", raw, version=version)
    reference = safe(template / "reference-assets")
    if reference.exists():
        for relative, raw in tree_files(reference).items():
            include("reference-assets/" + relative, raw)
    renderer = file_bytes(template / README_RENDERER)
    return copied, origins, versions, renderer, policy


def source_snapshot(
    depot: Path, skill: Path, identity: dict[str, Any]
) -> tuple[dict[str, bytes], list[dict[str, str]], dict[str, bytes]]:
    # The installed skill provides code only. Every starter input, including the
    # allowlist and README renderer, is read from the registered template.
    original, origins, versions, renderer, policy = template_sources(depot)
    proposed = dict(original)
    # Never copy a populated Task index as the new project's empty state.
    if (
        b"| None |" not in proposed["Tasks/INDEX.md"]
        or b"TASK-" in proposed["Tasks/INDEX.md"]
    ):
        raise InitializationError("template Task index is not empty")
    proposed["README.md"] = renderer.decode().format(**identity).encode()
    proposed[IDENTITY] = encoded(identity)
    records = [
        {
            "source": source.relative_to(depot).as_posix(),
            "source_sha256": sha(original[relative]),
            "destination": relative,
            "destination_sha256": sha(proposed[relative]),
            "source_version": versions[relative],
        }
        for relative, source in sorted(origins.items())
    ]
    for relative, raw, destination in (
        (README_RENDERER, renderer, "README.md"),
        (TEMPLATE_POLICY, policy, IDENTITY),
    ):
        records.append({
            "source": f"{TEMPLATE}/{relative}",
            "source_sha256": sha(raw),
            "destination": destination,
            "destination_sha256": sha(proposed[destination]),
            "source_version": "sha256:" + sha(raw),
        })
    for relative, raw in proposed.items():
        if relative in {"README.md", IDENTITY} and b"Sys4AI Template Project" in raw:
            raise InitializationError("product identity retains the template name")
    return proposed, records, original


def check_sources(depot: Path, records: list[dict[str, str]]) -> None:
    expected = {entry["source"]: entry["source_sha256"] for entry in records}
    try:
        copied, origins, _, renderer, policy = template_sources(depot)
    except (InitializationError, OSError) as error:
        raise InitializationError("reviewed template source changed during adoption") from error
    actual = {
        origins[relative].relative_to(depot).as_posix(): sha(raw)
        for relative, raw in copied.items()
    }
    actual[f"{TEMPLATE}/{README_RENDERER}"] = sha(renderer)
    actual[f"{TEMPLATE}/{TEMPLATE_POLICY}"] = sha(policy)
    if actual.keys() != expected.keys():
        raise InitializationError("reviewed template source file set changed during adoption")
    if actual != expected:
        raise InitializationError("reviewed template source changed during adoption")


def destination_file(root: Path, relative: str) -> Path:
    candidate = safe(root / relative)
    if (
        not candidate.is_relative_to(root)
        or relative in {"", "."}
        or Path(relative).as_posix() != relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
    ):
        raise InitializationError("unsafe project file path")
    for parent in candidate.parents:
        if parent == root:
            break
        if parent.exists() and not parent.is_dir():
            raise InitializationError("project file parent is not a directory")
    if candidate.exists():
        file_bytes(candidate)
    return candidate


def atomic_write(
    target: Path, data: bytes, expected: bytes | None, *, mode: int = 0o644
) -> None:
    safe(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    safe(target)
    current = file_bytes(target) if target.exists() else None
    if current != expected:
        raise InitializationError("destination changed before publication")
    published_mode = (
        stat.S_IMODE(target.stat().st_mode) if current is not None else mode
    )
    descriptor, name = tempfile.mkstemp(prefix=".initializer-", dir=target.parent)
    staging = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), published_mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if (file_bytes(target) if target.exists() else None) != expected:
            raise InitializationError("destination changed during publication")
        if expected is None:
            # Hard-link publication gives create-only semantics even if another
            # writer appears after the last check. The staging alias is removed.
            os.link(staging, target, follow_symlinks=False)
        else:
            os.replace(staging, target)
    finally:
        staging.unlink(missing_ok=True)


@contextmanager
def template_read_lock(depot: Path) -> Iterator[None]:
    """Coordinate authorized adoption with the optional depot-to-template updater."""
    lock = safe(depot / ".sys4ai/template-update/lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise InitializationError("template update lock must be a regular non-aliased file")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise InitializationError("template update is active; retry initialization after it finishes") from error
        yield
    finally:
        os.close(descriptor)


@contextmanager
def exclusive(lock: Path) -> Iterator[None]:
    """Hold a crash-releasing lock on a stable inode; its presence is not a lease."""
    safe(lock)
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise InitializationError("initializer lock must be a regular non-aliased file")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise InitializationError("an initializer operation is active; retry after its writer exits") from error
        yield
    finally:
        # Unlinking permits another writer to create and lock a different inode
        # while a contender still holds this one. Closing releases the kernel lock.
        os.close(descriptor)


def process(arguments: list[str], cwd: Path, *, json_output: bool = False,
            timeout: int = 15) -> Any:
    environment = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    result = subprocess.run(arguments, cwd=cwd, env=environment, text=True,
                            capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise InitializationError(
            f"{Path(arguments[0]).name} observation failed with exit code {result.returncode}"
        )
    return unique_json(result.stdout.encode()) if json_output else result.stdout.strip()


def repository_observation(destination: Path) -> dict[str, Any]:
    marker = destination / ".git"
    if not marker.exists() and not marker.is_symlink():
        return {"status": "not_initialized", "remote": None}
    safe(marker)
    top = process(
        ["git", "-C", str(destination), "rev-parse", "--show-toplevel"],
        destination,
        json_output=False,
    )
    if Path(top) != destination:
        raise InitializationError(
            "Git metadata does not belong to this exact child root"
        )
    # A configured remote is optional, including for an empty new repository.
    environment = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    result = subprocess.run(
        ["git", "-C", str(destination), "config", "--get", "remote.origin.url"],
        cwd=destination,
        env=environment,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise InitializationError("child Git remote observation failed")
    remote = result.stdout.strip() or None
    if remote:
        text_value(remote, "observed remote", 2000)
    return {"status": "initialized", "remote": remote}


def registry_candidate(identity: dict[str, Any], destination: Path) -> dict[str, Any]:
    return {
        "id": identity["project_id"],
        "name": identity["project_name"],
        "path": identity["relative_path"],
        "kind": "product-project",
        "registered": True,
        "repository": repository_observation(destination),
        "github_pages": {"status": "not_configured", "url": None},
        "notes": identity["purpose"],
    }


def register_project(
    depot: Path, candidate: dict[str, Any], expected: bytes, *, preserve_existing: bool = False
) -> dict[str, Any]:
    with exclusive(depot / "depot/.projects-initializer.lock"):
        registry, current = read_registry(depot)
        if not isinstance(candidate, dict) or not isinstance(
            candidate.get("path"), str
        ):
            raise InitializationError("registration candidate is malformed")
        target = safe(depot / candidate["path"])
        identity = unique_json(file_bytes(target / IDENTITY))
        validate_identity(
            identity["project_id"],
            identity["project_name"],
            identity["purpose"],
        )
        validate_destination(depot, registry, target, identity["project_id"])
        if not target.is_dir() or (not preserve_existing and candidate != registry_candidate(identity, target)):
            raise InitializationError(
                "registration must match the specialized identity and observed repository"
            )
        same = [
            entry
            for entry in registry["projects"]
            if entry["id"] == candidate["id"]
            or entry["path"].casefold() == candidate["path"].casefold()
        ]
        if same:
            if len(same) == 1 and same[0] == candidate:
                return {"entry": candidate, "changed": False, "sha256": sha(current)}
            if (preserve_existing and len(same) == 1 and same[0]["id"] == identity["project_id"]
                    and same[0]["path"] == identity["relative_path"] and same[0]["kind"] == "product-project"):
                return {"entry": same[0], "changed": False, "sha256": sha(current)}
            raise InitializationError("registry identity or path conflicts")
        if current != expected:
            raise InitializationError(
                "registry changed since preflight; retry after inspecting the current inventory"
            )
        if (
            not target.is_dir()
            or identity["project_id"] != candidate["id"]
            or identity["relative_path"] != candidate["path"]
            or identity["project_name"] != candidate["name"]
        ):
            raise InitializationError(
                "specialized project must exist before registration"
            )
        registry["projects"].append(candidate)
        updated = encoded(registry)
        atomic_write(depot / "depot/projects.json", updated, current)
        read_registry(depot)
        return {"entry": candidate, "changed": True, "sha256": sha(updated)}


def selected_identity(
    destination: Path, *, project_id: str, project_name: str, purpose: str, relative: str
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    validate_identity(project_id, project_name, purpose)
    identity_path = destination_file(destination, IDENTITY)
    saved = unique_json(file_bytes(identity_path)) if identity_path.exists() else None
    if saved is not None:
        if not isinstance(saved, dict) or saved.get("project_id") != project_id:
            raise InitializationError("existing project identity differs from the selected project")
        if not {"project_id", "project_name", "purpose", "relative_path"} <= saved.keys():
            raise InitializationError("existing project identity is incomplete; preserve and resolve it before setup")
        if saved.get("relative_path", relative) != relative:
            raise InitializationError("existing project identity belongs to another destination")
        project_name = saved.get("project_name", project_name)
        purpose = saved.get("purpose", purpose)
        validate_identity(project_id, project_name, purpose)
    identity = {"schema_version": 1, "project_id": project_id, "project_name": project_name,
                "purpose": purpose, "relative_path": relative}
    return identity, saved


def asset_plan(destination: Path, *, mode: str, proposed: dict[str, bytes],
               original: dict[str, bytes], saved_identity: dict[str, Any] | None
               ) -> tuple[dict[str, bytes], dict[str, str | None], dict[str, str]]:
    selected, before, preserved = {}, {}, {}
    for name, raw in proposed.items():
        target = destination_file(destination, name)
        present = file_bytes(target) if target.exists() else None
        if mode == "create":
            if present is not None:
                raise InitializationError("new project changed before asset adoption")
            selected[name], before[name] = raw, None
            continue
        # A project owns an existing package as a whole. Filling missing resources
        # from a newer Template could combine incompatible package versions.
        parts = Path(name).parts
        package_exists = ((name.startswith(".agents/skills/") and len(parts) > 3
                           and (destination / Path(*parts[:3])).is_dir())
                          or (name.startswith("sub-agent-roles/") and len(parts) > 2
                              and (destination / Path(*parts[:2])).is_dir()))
        existing_tasks = (name.startswith("Tasks/") and (destination / "Tasks").is_dir()
                          and any((destination / "Tasks").iterdir()))
        if present is not None:
            if saved_identity is None and name == "README.md" and present == original.get(name):
                selected[name], before[name] = raw, sha(present)
            else:
                preserved[name] = sha(present)
        elif not (package_exists or existing_tasks):
            selected[name], before[name] = raw, None
    return selected, before, preserved


def validate_record(record: Any, destination: Path, identity: dict[str, Any]) -> None:
    if (not isinstance(record, dict) or record.get("schema_version") != 1
            or record.get("setup_contract") != SETUP_CONTRACT):
        raise InitializationError("existing setup receipt has an unsupported contract")
    if record.get("project_root") != str(destination) or record.get("identity") != identity:
        raise InitializationError("existing setup receipt belongs to another project or request")
    stages = record.get("completed_stages")
    if (record.get("status") not in {"partial", "completed"}
            or record.get("mode") not in {"create", "prepare-existing"}
            or not isinstance(stages, list) or stages != STAGES[:len(stages)]
            or record.get("active_stage") not in {*STAGES, None}
            or not isinstance(record.get("sources"), list)
            or not record["sources"]):
        raise InitializationError("existing setup receipt has an invalid lifecycle")
    if (not isinstance(record.get("operation_id"), str)
            or not re.fullmatch(r"project-setup-[0-9a-f]{32}", record["operation_id"])):
        raise InitializationError("existing setup receipt has an invalid operation identity")
    source_adoptions = {}
    seen_sources = set()
    for entry in record["sources"]:
        if (not isinstance(entry, dict) or not isinstance(entry.get("source"), str)
                or not entry["source"].startswith(TEMPLATE + "/")
                or entry["source"] in seen_sources
                or not isinstance(entry.get("source_sha256"), str)
                or not SHA256.fullmatch(entry["source_sha256"])
                or not isinstance(entry.get("source_version"), str)
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", entry["source_version"])
                or entry.get("adoption") not in {"adopted", "preserved-project-owned", "skipped-existing-package"}):
            raise InitializationError("existing setup receipt has invalid source provenance")
        relative_source = entry["source"].removeprefix(TEMPLATE + "/")
        expected_destination = {README_RENDERER: "README.md", TEMPLATE_POLICY: IDENTITY}.get(
            relative_source, relative_source)
        if entry.get("destination") != expected_destination:
            raise InitializationError("existing setup receipt changes a source destination")
        destination_file(destination, expected_destination)
        checksum = entry.get("destination_sha256")
        if (entry["adoption"] == "skipped-existing-package" and checksum is not None
                or entry["adoption"] != "skipped-existing-package"
                and (not isinstance(checksum, str) or not SHA256.fullmatch(checksum))):
            raise InitializationError("existing setup receipt has an invalid adoption digest")
        adoption = (entry["adoption"], checksum)
        if (expected_destination in source_adoptions
                and source_adoptions[expected_destination] != adoption):
            raise InitializationError("existing setup receipt has conflicting source adoption decisions")
        source_adoptions[expected_destination] = adoption
        seen_sources.add(entry["source"])
    required_sources = {TEMPLATE + "/" + name for name in
        STARTER_FILES | {"SOUL.md", TEMPLATE_POLICY, README_RENDERER}
        | {f".agents/skills/{name}/SKILL.md" for name in REQUIRED_SKILLS}
        | {"sub-agent-roles/project-sub-agent/AGENTS.md", "sub-agent-roles/project-sub-agent/ROLE.md"}}
    if not required_sources <= seen_sources:
        raise InitializationError("existing setup receipt omits required starter source provenance")
    for key in ("owned_files", "preserved_files"):
        files = record.get(key)
        if not isinstance(files, dict):
            raise InitializationError("existing setup receipt has an invalid file inventory")
        for name, checksum in files.items():
            if not isinstance(name, str) or not isinstance(checksum, str) or not SHA256.fullmatch(checksum):
                raise InitializationError("existing setup receipt has an invalid file digest")
            if name not in source_adoptions:
                raise InitializationError("existing setup receipt names an unreviewed project file")
            destination_file(destination, name)
    if (record["owned_files"].keys() & record["preserved_files"].keys()
            or IDENTITY not in record["owned_files"].keys() | record["preserved_files"].keys()):
        raise InitializationError("existing setup receipt has conflicting file ownership")
    expected_owned, expected_preserved = {}, {}
    for name, (adoption, checksum) in source_adoptions.items():
        if adoption == "adopted":
            expected_owned[name] = checksum
        elif adoption == "preserved-project-owned":
            expected_preserved[name] = checksum
        else:
            # Only resources omitted to preserve an existing whole package or
            # nonempty Task tree can lack an adopted/preserved file digest.
            parts = Path(name).parts
            if name.startswith(".agents/skills/") and len(parts) > 3:
                preserved_root = destination / Path(*parts[:3])
            elif name.startswith("sub-agent-roles/") and len(parts) > 2:
                preserved_root = destination / Path(*parts[:2])
            elif name == "Tasks/INDEX.md":
                preserved_root = destination / "Tasks"
            else:
                raise InitializationError("existing setup receipt skips a required standalone starter")
            safe(preserved_root)
            if (not preserved_root.is_dir()
                    or name == "Tasks/INDEX.md" and not any(preserved_root.iterdir())):
                raise InitializationError("existing setup receipt lacks its preserved package or Task tree")
    if record["owned_files"] != expected_owned or record["preserved_files"] != expected_preserved:
        raise InitializationError("existing setup receipt file inventories differ from source adoption decisions")
    if "assets" not in stages:
        before = record.get("recovery_before")
        if (not isinstance(before, dict) or before.keys() != record["owned_files"].keys()
                or any(value is not None and (not isinstance(value, str) or not SHA256.fullmatch(value))
                       for value in before.values())):
            raise InitializationError("partial setup receipt lacks its asset recovery inventory")
    if record["status"] == "completed" and (stages != STAGES or record["active_stage"] is not None):
        raise InitializationError("completed setup receipt lacks required stages")


def archive_record(destination: Path, raw: bytes) -> dict[str, str]:
    checksum = sha(raw)
    relative = "control_records/project-setup-history/" + checksum + ".json"
    target = destination_file(destination, relative)
    if target.exists():
        if file_bytes(target) != raw:
            raise InitializationError("setup history differs from its captured digest")
    else:
        atomic_write(target, raw, None, mode=0o600)
    return {"path": relative, "sha256": checksum}


def verify_project(destination: Path, record: dict[str, Any]) -> dict[str, str]:
    """Observe current adopted files without resetting normal project edits."""
    validate_record(record, destination, record["identity"])
    current = {}
    for name in sorted(record["owned_files"].keys() | record["preserved_files"].keys()):
        target = destination_file(destination, name)
        if not target.is_file():
            raise InitializationError(f"project setup file is missing: {name}")
        current[name] = sha(file_bytes(target))
    identity = record["identity"]
    observed, saved = selected_identity(destination, **{key: identity[key] for key in
        ("project_id", "project_name", "purpose")}, relative=identity["relative_path"])
    if saved is None or observed != identity:
        raise InitializationError("project identity changed during setup")
    return current


def run_initialization(
    *, mode: str, destination: Path, project_id: str, project_name: str, purpose: str
) -> dict[str, Any]:
    if mode not in {"create", "prepare-existing"}:
        raise InitializationError("unknown initialization route")
    depot, skill = installed_locations()
    validate_identity(project_id, project_name, purpose)
    registry, registry_before = read_registry(depot)
    relative = validate_destination(depot, registry, destination, project_id)
    if destination.exists() and not destination.is_dir():
        raise InitializationError("destination is not a directory")
    record_path = destination_file(destination, RECORD)
    previous_raw = file_bytes(record_path) if record_path.exists() else None
    if mode == "create" and previous_raw is None and destination.exists() and any(destination.iterdir()):
        raise InitializationError("new project destination is not empty")
    if mode == "prepare-existing" and not destination.is_dir():
        raise InitializationError("existing-project setup requires an existing selected directory")
    identity, saved_identity = selected_identity(destination, project_id=project_id,
        project_name=project_name, purpose=purpose, relative=relative)
    record = unique_json(previous_raw) if previous_raw is not None else None
    if record is not None:
        validate_record(record, destination, identity)
        record = deepcopy(record)
        record["mode"] = mode
    with ExitStack() as template_guard:
        proposed = {}
        if record is None or "assets" not in record["completed_stages"]:
            proposed_all, sources, original = source_snapshot(depot, skill, identity)
            if record is None:
                proposed, before, preserved = asset_plan(destination, mode=mode,
                    proposed=proposed_all, original=original, saved_identity=saved_identity)
                record = {"schema_version": 1, "setup_contract": SETUP_CONTRACT,
                          "status": "partial", "mode": mode, "operation_id": "project-setup-" + uuid4().hex,
                          "identity": identity, "project_root": str(destination), "sources": sources,
                          "owned_files": {name: sha(raw) for name, raw in proposed.items()},
                          "preserved_files": preserved, "recovery_before": before,
                          "completed_stages": [], "active_stage": "assets", "checks": [],
                          "created_at": datetime.now(timezone.utc).isoformat(), "git_setup": "separate"}
                for entry in sources:
                    name = entry["destination"]
                    if name in preserved:
                        entry.update(adoption="preserved-project-owned", destination_sha256=preserved[name])
                    elif name not in proposed:
                        entry.update(adoption="skipped-existing-package", destination_sha256=None)
                    else:
                        entry["adoption"] = "adopted"
            else:
                expected_sources = {(entry["source"], entry["source_sha256"]) for entry in record["sources"]}
                actual_sources = {(entry["source"], entry["source_sha256"]) for entry in sources}
                if expected_sources != actual_sources:
                    raise InitializationError("partial asset adoption source changed; preserve existing owned state")
                for name, checksum in record["owned_files"].items():
                    if name not in proposed_all or sha(proposed_all[name]) != checksum:
                        raise InitializationError("partial asset adoption differs from the saved plan")
                    proposed[name] = proposed_all[name]
            template_guard.enter_context(template_read_lock(depot))
            check_sources(depot, record["sources"])
            if file_bytes(depot / "depot/projects.json") != registry_before:
                raise InitializationError("registry changed during preflight")
        lock = depot / "depot" / (".initialize-" + sha(relative.encode())[:16] + ".lock")
        with exclusive(lock):
            if mode == "create" and previous_raw is None and destination.exists() and any(destination.iterdir()):
                raise InitializationError("new project destination changed after preflight")
            if (file_bytes(record_path) if record_path.exists() else None) != previous_raw:
                raise InitializationError("setup receipt changed since preflight")
            if not destination.exists():
                destination.mkdir()
            if previous_raw is not None:
                archived = archive_record(destination, previous_raw)
                if archived not in record.setdefault("history", []):
                    record["history"].append(archived)
            current_record = previous_raw
            was_completed = record["status"] == "completed"
            record.update(status="partial", checks=[])
            record["completed_stages"] = [stage for stage in record["completed_stages"] if stage == "assets"]
            for key in ("verified_at", "current_files", "recovery", "rerun"):
                record.pop(key, None)

            def checkpoint(stage: str | None = None) -> None:
                nonlocal current_record
                if stage and stage not in record["completed_stages"]:
                    record["completed_stages"].append(stage)
                raw = encoded(record)
                atomic_write(record_path, raw, current_record, mode=0o600)
                current_record = raw

            def begin(stage: str) -> None:
                record["active_stage"] = stage
                checkpoint()

            try:
                if "assets" not in record["completed_stages"]:
                    begin("assets")
                    check_sources(depot, record["sources"])
                    for name, checksum in record["preserved_files"].items():
                        if sha(file_bytes(destination_file(destination, name))) != checksum:
                            raise InitializationError("preserved project file changed during adoption")
                    for name, expected in record["recovery_before"].items():
                        target = destination_file(destination, name)
                        present = file_bytes(target) if target.exists() else None
                        after = proposed[name]
                        if present != after:
                            if (sha(present) if present is not None else None) != expected:
                                raise InitializationError("owned asset changed during interrupted adoption")
                            atomic_write(target, after, present)
                    check_sources(depot, record["sources"])
                    checkpoint("assets")
                template_guard.close()
                begin("registration")
                record["registry"] = register_project(depot, registry_candidate(identity, destination), registry_before,
                    preserve_existing=mode == "prepare-existing" or previous_raw is not None)
                checkpoint("registration")
                begin("verification")
                record["current_files"] = verify_project(destination, record)
                current_registry, registry_raw = read_registry(depot)
                if record["registry"]["entry"] not in current_registry["projects"]:
                    raise InitializationError("project registration changed during setup")
                record["registry"]["sha256"] = sha(registry_raw)
                record["checks"] = [{"check": name, "outcome": "passed"}
                                    for name in ("project-identity", "project-files", "registration")]
                checkpoint("verification")
                record.update(status="completed", active_stage=None,
                              verified_at=datetime.now(timezone.utc).isoformat())
                record.pop("recovery_before", None)
                if was_completed:
                    record["rerun"] = "verified-current-files-and-registration"
                checkpoint()
                return record
            except (InitializationError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
                record["status"] = "partial"
                record["recovery"] = {"stage": record["active_stage"],
                    "completed_stages": list(record["completed_stages"]), "owned_record": str(record_path),
                    "next_action": "Resolve the reported cause and repeat the same setup request; preserve project files.",
                    "error_type": type(error).__name__,
                    "reason": str(error) if isinstance(error, InitializationError) else "A local setup stage failed."}
                try:
                    checkpoint()
                except (InitializationError, OSError):
                    record["recovery"]["record_update"] = "failed; preserve the existing setup receipt"
                raise InitializationError("project setup is incomplete; working state was retained", report=record) from error

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    for mode in ("create", "prepare-existing"):
        route = commands.add_parser(mode)
        route.add_argument("--destination", type=Path, required=True)
        route.add_argument("--project-id", required=True)
        route.add_argument("--project-name", required=True)
        route.add_argument("--purpose", required=True)
    arguments = vars(parser.parse_args(argv))
    try:
        result = run_initialization(**arguments)
        print(encoded(result).decode(), end="")
        return 0
    except (InitializationError, OSError, subprocess.TimeoutExpired) as error:
        result = {"status": "failed", "error_type": type(error).__name__}
        if isinstance(error, InitializationError):
            result["reason"] = str(error)
            if error.report:
                result = {**error.report, "reason": str(error)}
        print(encoded(result).decode(), end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
