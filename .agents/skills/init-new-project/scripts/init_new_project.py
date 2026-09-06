#!/usr/bin/env python3
"""Create one Sys4AI project or prepare one explicitly selected manual copy.

Only the installed skill location determines the depot and its source projects.
The shared Memory Service wheel owns canonical memory preparation and direct
initialization. This standard-library helper never imports a native provider.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILLS = (
    "agent-task",
    "communication",
    "manage-subagent-roles",
    "task",
    "to-implementation-plan",
    "to-trd",
)
TEMPLATE = "Projects/Sys4AI-Template-Project"
PRODUCT = "Projects/Sys4AI-Memory-Service"
IDENTITY = "project.json"
RECORD = "control_records/project-initialization.json"
FINAL_RECEIPT = ".sys4ai/memory/receipts/project-initialization.json"
ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
PRINCIPAL_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_.:@-]*\Z")
EXCLUDED = {
    ".git",
    ".gitmodules",
    ".gitignore_global",
    ".venv",
    "venv",
    "env",
    "ENV",
    ".sys4ai",
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
    "sys4ai-memory-service",
    "template",
    "main-dataset",
    "main_dataset",
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
        depot = skill.parent.parent
    elif skill.parent.name == "skills" and skill.parent.parent.name == ".agents":
        depot = skill.parent.parent.parent
    else:
        raise InitializationError(
            "skill must be installed in this depot's source or active skills"
        )
    safe(depot)
    if not (depot / "Projects").is_dir():
        raise InitializationError(
            "the installed skill has no Sys4AI Projects container"
        )
    return depot, skill


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
    project_id: str, project_name: str, purpose: str, principal_id: str
) -> None:
    if (
        not ID_PATTERN.fullmatch(project_id)
        or len(project_id) > 100
        or project_id in RESERVED
    ):
        raise InitializationError("project ID is malformed or reserved")
    text_value(project_name, "project name", 200)
    text_value(purpose, "purpose", 4000)
    text_value(principal_id, "principal ID", 128)
    if not PRINCIPAL_PATTERN.fullmatch(principal_id):
        raise InitializationError("principal ID is malformed")
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
        "sys4ai-memory-service": (PRODUCT, "product-project"),
    }
    for identifier, (relative, kind) in required.items():
        entries = [entry for entry in registry["projects"] if entry["id"] == identifier]
        if (
            len(entries) != 1
            or entries[0]["path"] != relative
            or entries[0]["kind"] != kind
        ):
            raise InitializationError(
                "exact registered depot, template and Memory Service identities are required"
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
    if relative in {TEMPLATE, PRODUCT}:
        raise InitializationError("source projects cannot be initialization targets")
    return relative


def excluded(relative: Path) -> bool:
    return any(
        part in EXCLUDED or part.startswith(("._", ".env.")) for part in relative.parts
    ) or relative.name.endswith(EXCLUDED_SUFFIXES)


def package_files(package: Path) -> dict[str, bytes]:
    safe(package)
    if not package.is_dir():
        raise InitializationError("baseline skill package is missing")
    collected: dict[str, bytes] = {}
    for current, directories, filenames in os.walk(package, followlinks=False):
        directories[:] = sorted(
            name for name in directories if not excluded(Path(name))
        )
        for name in directories:
            safe(Path(current) / name)
        for name in sorted(filenames):
            candidate = Path(current) / name
            relative = candidate.relative_to(package)
            if not excluded(relative):
                collected[relative.as_posix()] = file_bytes(candidate)
    if "SKILL.md" not in collected:
        raise InitializationError("baseline skill has no SKILL.md")
    validate_package(package.name, collected)
    return collected


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


def source_snapshot(
    depot: Path, skill: Path, identity: dict[str, Any]
) -> tuple[dict[str, bytes], list[dict[str, str]], dict[str, bytes]]:
    specification = unique_json(file_bytes(skill / "assets/baseline-assets.json"))
    if (
        tuple(specification["skills"]) != SKILLS
        or specification["soul"] != "SOULS-depo/SOUL.md"
        or specification["template"] != TEMPLATE
    ):
        raise InitializationError(
            "baseline source specification differs from the approved sources"
        )
    proposed: dict[str, bytes] = {}
    origins: dict[str, Path] = {}
    source_bytes: dict[str, bytes] = {}
    original: dict[str, bytes] = {}
    versions: dict[str, str] = {}
    for relative in (
        specification["starter_files"] + specification["optional_starter_files"]
    ):
        source = depot / TEMPLATE / relative
        if relative in specification["optional_starter_files"] and not source.exists():
            continue
        proposed[relative] = file_bytes(source)
        original[relative] = proposed[relative]
        origins[relative] = source
        source_bytes[relative] = proposed[relative]
    # Never copy a populated Task index as the new project's empty state.
    if (
        b"| None |" not in proposed["Tasks/INDEX.md"]
        or b"TASK-" in proposed["Tasks/INDEX.md"]
    ):
        raise InitializationError("template Task index is not empty")
    renderer = file_bytes(skill / "assets/project-readme.md")
    proposed["README.md"] = (
        renderer.decode()
        .format(
            **identity,
            manual_guide="\nSee [INIT_MEMORY.md](./INIT_MEMORY.md) for the separate manual-copy route.\n"
            if "INIT_MEMORY.md" in proposed
            else "",
        )
        .encode()
    )
    if "INIT_MEMORY.md" in proposed:
        # A permitted destination may be deeper than Projects/<name>. Keep the
        # guide's local links aimed at the same reviewed depot assets while the
        # source receipt retains the original template bytes and digest.
        destination = depot / identity["relative_path"]

        def rebase_guide_link(match: re.Match[str]) -> str:
            label, target = match.groups()
            if target.startswith(("#", "http://", "https://", "mailto:")):
                return match.group(0)
            relative, separator, fragment = target.partition("#")
            original_target = (depot / TEMPLATE / relative).resolve()
            rebased = Path(os.path.relpath(original_target, destination)).as_posix()
            return f"{label}{rebased}{separator}{fragment})"

        proposed["INIT_MEMORY.md"] = re.sub(
            r"(\[[^\]\n]+\]\()([^\)\n]+)\)",
            rebase_guide_link,
            proposed["INIT_MEMORY.md"].decode(),
        ).encode()
    proposed[IDENTITY] = encoded(identity)
    proposed["SOUL.md"] = file_bytes(depot / "SOULS-depo/SOUL.md")
    origins["SOUL.md"] = depot / "SOULS-depo/SOUL.md"
    source_bytes["SOUL.md"] = proposed["SOUL.md"]
    for name in SKILLS:
        source = depot / "SKILLS-depo" / name
        package = package_files(source)
        versions[name] = "sha256:" + sha(
            encoded({relative: sha(raw) for relative, raw in package.items()})
        )
        for relative, raw in package.items():
            target = f".agents/skills/{name}/{relative}"
            proposed[target] = raw
            origins[target] = source / relative
            source_bytes[target] = raw
    records = [
        {
            "source": source.relative_to(depot).as_posix(),
            "source_sha256": sha(source_bytes[relative]),
            "destination": relative,
            "destination_sha256": sha(proposed[relative]),
            "source_version": versions[Path(relative).parts[2]]
            if relative.startswith(".agents/skills/")
            else "sha256:" + sha(source_bytes[relative]),
        }
        for relative, source in sorted(origins.items())
    ]
    records.append(
        {
            "source": (skill / "assets/project-readme.md")
            .relative_to(depot)
            .as_posix(),
            "source_sha256": sha(renderer),
            "destination": "README.md",
            "destination_sha256": sha(proposed["README.md"]),
            "source_version": "1",
        }
    )
    for relative, raw in proposed.items():
        if relative in {"README.md", IDENTITY} and b"Sys4AI Template Project" in raw:
            raise InitializationError("product identity retains the template name")
    return proposed, records, original


def check_sources(depot: Path, records: list[dict[str, str]]) -> None:
    for entry in records:
        if sha(file_bytes(depot / entry["source"])) != entry["source_sha256"]:
            raise InitializationError("reviewed source changed during adoption")
    for name in SKILLS:
        prefix = f"SKILLS-depo/{name}/"
        expected = {
            entry["source"].removeprefix(prefix): entry["source_sha256"]
            for entry in records
            if entry["source"].startswith(prefix)
        }
        actual = {
            relative: sha(raw)
            for relative, raw in package_files(depot / "SKILLS-depo" / name).items()
        }
        if actual != expected:
            raise InitializationError(
                "reviewed source package file set changed during adoption"
            )


def destination_file(root: Path, relative: str) -> Path:
    candidate = safe(root / relative)
    if (
        not candidate.is_relative_to(root)
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


def inspect_manual(
    depot: Path,
    destination: Path,
    proposed: dict[str, bytes],
    original: dict[str, bytes],
) -> dict[str, bytes | None]:
    before: dict[str, bytes | None] = {}
    for relative, raw in proposed.items():
        candidate = destination_file(destination, relative)
        present = file_bytes(candidate) if candidate.exists() else None
        allowed = [None, raw, original.get(relative)]
        template = depot / TEMPLATE / relative
        if template.exists() and template.is_file():
            allowed.append(file_bytes(template))
        if present not in allowed:
            raise InitializationError(
                f"project-customized content conflicts: {relative}"
            )
        before[relative] = present
    for name in SKILLS:
        copied = destination / ".agents/skills" / name
        if not copied.exists():
            continue
        # Remove only obsolete, byte-identical template resources within the six
        # replaced packages. Unknown project additions require a separate review.
        for relative, raw in package_files(copied).items():
            target = f".agents/skills/{name}/{relative}"
            if target in proposed:
                continue
            source = depot / TEMPLATE / target
            if not source.is_file() or raw != file_bytes(source):
                raise InitializationError(
                    f"project-owned package addition conflicts: {target}"
                )
            before[target] = raw
    return before


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
def exclusive(lock: Path) -> Iterator[None]:
    safe(lock)
    try:
        descriptor = os.open(
            lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
    except FileExistsError as error:
        raise InitializationError(
            "an initializer operation is already coordinated; inspect the existing lock before recovery"
        ) from error
    info = os.fstat(descriptor)
    os.close(descriptor)
    try:
        yield
    finally:
        if (
            lock.exists()
            and not lock.is_symlink()
            and lock.stat().st_ino == info.st_ino
        ):
            lock.unlink()


def process(arguments: list[str], cwd: Path, *, json_output: bool = True) -> Any:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.update(
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        GIT_OPTIONAL_LOCKS="0",
        UV_NO_CACHE="1",
        UV_PYTHON_DOWNLOADS="never",
    )
    result = subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )
    if result.returncode:
        raise InitializationError(
            f"{Path(arguments[0]).name} operation failed with exit code {result.returncode}"
        )
    if not json_output:
        return result.stdout.strip()
    return unique_json(result.stdout.encode())


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
    depot: Path, candidate: dict[str, Any], expected: bytes
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
            identity["principal_id"],
        )
        validate_destination(depot, registry, target, identity["project_id"])
        if not target.is_dir() or candidate != registry_candidate(identity, target):
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


def artifact_selection(
    depot: Path, selected: Path | None
) -> tuple[Path, dict[str, Any]]:
    product = depot / PRODUCT
    builder = product / "tools/build_consumer_artifact.py"
    file_bytes(builder)
    if selected is None:
        result = process(
            [sys.executable, str(builder), "build", "--project-root", str(product)],
            product,
        )
        selected = Path(result["artifact_receipt"])
    safe(selected)
    if (
        not selected.is_relative_to(product / "dist/consumer")
        or selected.name != "artifact.json"
    ):
        raise InitializationError(
            "artifact must be an immutable receipt under the registered Memory Service dist/consumer"
        )
    process([sys.executable, str(builder), "verify", str(selected)], product)
    receipt = unique_json(file_bytes(selected))
    if receipt.get("source_root") != str(product):
        raise InitializationError(
            "artifact source is not this depot's registered Memory Service"
        )
    return selected, receipt


def memory_arguments(
    destination: Path, identity: dict[str, Any], *command: str
) -> list[str]:
    return [
        str(destination / ".venv/bin/sys4ai-memory"),
        "--project-root",
        str(destination),
        "--project-id",
        identity["project_id"],
        "--dataset-id",
        identity["dataset_id"],
        "--principal-id",
        identity["principal_id"],
        "--agent-type",
        "project-initializer",
        "--run-id",
        "initialize-" + identity["project_id"],
        *command,
    ]


def verify_files(destination: Path, files: dict[str, str]) -> None:
    for relative, expected in files.items():
        target = destination_file(destination, relative)
        if not target.exists() or sha(file_bytes(target)) != expected:
            raise InitializationError(
                f"owned project file changed or is missing: {relative}"
            )


def verify_completed(
    depot: Path, destination: Path, record: dict[str, Any]
) -> dict[str, Any]:
    verify_files(destination, record["owned_files"])
    registry, _ = read_registry(depot)
    if record["registry"]["entry"] not in registry["projects"]:
        raise InitializationError(
            "recorded factual registry entry changed or is missing"
        )
    install = record["runtime"]
    observed = process(
        [
            str(destination / ".venv/bin/python"),
            "-I",
            "-c",
            "import importlib.metadata as m,importlib.util as u,json;d=m.distribution('sys4ai-memory-service');print(json.dumps({'version':d.version,'origin':u.find_spec('sys4ai_memory').origin,'direct_url':json.loads(d.read_text('direct_url.json') or '{}'),'dependencies':{x.metadata['Name']:x.version for x in m.distributions()}}))",
        ],
        destination,
    )
    if (
        observed["version"] != install["version"]
        or observed["origin"] != install["observed"]["origin"]
        or observed["direct_url"] != install["observed"]["direct_url"]
    ):
        raise InitializationError(
            "installed runtime differs from the recorded immutable package"
        )
    if any(
        observed["dependencies"].get(name) != version
        for name, version in install["observed"]["dependencies"].items()
    ):
        raise InitializationError("installed dependency version changed")
    verify_files(destination, record["installed_package_files"])
    if record["status"] == "completed":
        receipt = unique_json(
            file_bytes(destination / ".sys4ai/memory/receipts/initialization.json")
        )
        expected_fingerprint = record["initialization"].get("configuration_fingerprint")
        if (
            receipt.get("project_id") != record["identity"]["project_id"]
            or receipt.get("dataset_id") != record["identity"]["dataset_id"]
            or not expected_fingerprint
            or receipt.get("configuration_fingerprint") != expected_fingerprint
            or not receipt.get("exact_index_initialized")
        ):
            raise InitializationError(
                "functional initialization receipt differs from recorded context"
            )
        import sqlite3

        import tomllib

        configuration = tomllib.loads(
            file_bytes(destination / "config/memory.toml").decode()
        )
        index = safe(destination / configuration["memory"]["exact_index"]["path"])
        if (
            not index.is_relative_to(destination / ".sys4ai/memory")
            or not index.is_file()
        ):
            raise InitializationError("recorded exact index is missing")
        try:
            with sqlite3.connect(
                index.as_uri() + "?mode=ro&immutable=1", uri=True
            ) as connection:
                if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
                    raise InitializationError(
                        "recorded exact index failed its integrity check"
                    )
                projects = {
                    row[0]
                    for row in connection.execute(
                        "SELECT DISTINCT project_id FROM records"
                    )
                }
                if projects != {record["identity"]["project_id"]}:
                    raise InitializationError(
                        "recorded exact index project identity differs"
                    )
        except sqlite3.DatabaseError as error:
            raise InitializationError("recorded exact index is invalid") from error
    return {**record, "rerun": "verified-existing", "mutations_performed": False}


def run_initialization(
    *,
    mode: str,
    destination: Path,
    project_id: str,
    project_name: str,
    purpose: str,
    principal_id: str,
    artifact_receipt: Path | None = None,
) -> dict[str, Any]:
    if mode not in {"create", "prepare-existing"}:
        raise InitializationError("unknown initialization route")
    depot, skill = installed_locations()
    validate_identity(project_id, project_name, purpose, principal_id)
    registry, registry_before = read_registry(depot)
    relative = validate_destination(depot, registry, destination, project_id)
    identity = {
        "schema_version": 1,
        "project_id": project_id,
        "project_name": project_name,
        "purpose": purpose,
        "relative_path": relative,
        "principal_id": principal_id,
        "dataset_id": project_id + "-memory",
    }
    record_path = destination_file(destination, RECORD)
    if record_path.exists():
        record = unique_json(file_bytes(record_path))
        if (
            record.get("schema_version") != 1
            or record.get("identity") != identity
            or record.get("mode") != mode
        ):
            raise InitializationError(
                "existing initialization record belongs to another request"
            )
        if (
            artifact_receipt is not None
            and str(artifact_receipt) != record["artifact_receipt"]
        ):
            raise InitializationError(
                "an existing project cannot silently adopt another artifact"
            )
        if record.get("status") in {"completed", "prepared"}:
            return verify_completed(depot, destination, record)
        if record.get("status") != "partial":
            raise InitializationError(
                "initialization record has an unknown lifecycle state"
            )
        artifact_receipt = Path(record["artifact_receipt"])
        proposed, sources, original = source_snapshot(depot, skill, identity)
        if "assets" not in record["completed_stages"] and sources != record["sources"]:
            raise InitializationError(
                "partial adoption source changed; separate repair is required"
            )
        before = record.get("recovery_before", {})
    else:
        if destination.exists() and not destination.is_dir():
            raise InitializationError("destination is not a directory")
        if mode == "create" and destination.exists() and any(destination.iterdir()):
            raise InitializationError("new project destination is not empty")
        if mode == "prepare-existing" and not destination.is_dir():
            raise InitializationError(
                "manual preparation requires an existing copied project"
            )
        matches = [
            entry
            for entry in registry["projects"]
            if entry["id"] == project_id
            or entry["path"].casefold() == relative.casefold()
        ]
        if matches and (
            len(matches) != 1 or matches[0] != registry_candidate(identity, destination)
        ):
            raise InitializationError(
                "requested identity conflicts with existing factual registration"
            )
        proposed, sources, original = source_snapshot(depot, skill, identity)
        raw_before = (
            inspect_manual(depot, destination, proposed, original)
            if mode == "prepare-existing"
            else {key: None for key in proposed}
        )
        before = {
            key: sha(value) if value is not None else None
            for key, value in raw_before.items()
        }
        for forbidden in (
            ".venv",
            ".sys4ai",
            "config/memory.toml",
            "registries/memory_source_registry.csv",
            "control_records/memory",
            "schemas/memory",
            "profiles/base",
            "profiles/software-engineering",
        ):
            if (destination / forbidden).exists() or (
                destination / forbidden
            ).is_symlink():
                raise InitializationError(
                    "manual or new destination has pre-existing memory/runtime state"
                )
        artifact_receipt, artifact = artifact_selection(depot, artifact_receipt)
        check_sources(depot, sources)
        if file_bytes(depot / "depot/projects.json") != registry_before:
            raise InitializationError("registry changed during preflight")
        record = {
            "schema_version": 1,
            "status": "partial",
            "mode": mode,
            "identity": identity,
            "project_root": str(destination),
            "artifact_receipt": str(artifact_receipt),
            "artifact_sha256": sha(file_bytes(artifact_receipt)),
            "sources": sources,
            "owned_files": {},
            "completed_stages": [],
            "active_stage": "assets",
            "checks": [],
            "recovery_before": before,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "semantic_provider_status": "deferred",
            "models_status": "deferred",
            "git_setup": "separate",
        }
    lock = depot / "depot" / (".initialize-" + sha(relative.encode())[:16] + ".lock")
    with exclusive(lock):
        if (
            mode == "create"
            and not record_path.exists()
            and destination.exists()
            and any(destination.iterdir())
        ):
            raise InitializationError("new destination changed after preflight")
        if not destination.exists():
            destination.mkdir()
        destination_file(destination, RECORD)
        previous = file_bytes(record_path) if record_path.exists() else None

        def checkpoint(stage: str | None = None) -> None:
            nonlocal previous
            if stage and stage not in record["completed_stages"]:
                record["completed_stages"].append(stage)
            atomic_write(record_path, encoded(record), previous, mode=0o600)
            previous = file_bytes(record_path)

        try:
            checkpoint()
            if "assets" not in record["completed_stages"]:
                check_sources(depot, record["sources"])
                for target_relative, expected in before.items():
                    target = destination_file(destination, target_relative)
                    current = file_bytes(target) if target.exists() else None
                    after = proposed.get(target_relative)
                    if current == after:
                        continue
                    if (sha(current) if current is not None else None) != expected:
                        raise InitializationError(
                            "owned asset changed during interrupted adoption"
                        )
                    if after is None:
                        target.unlink()
                    else:
                        atomic_write(target, after, current)
                check_sources(depot, record["sources"])
                record["owned_files"] = {
                    key: sha(value) for key, value in proposed.items()
                }
                record["checks"].append(
                    {
                        "check": "six complete source packages, source drift, starter allowlist and identity",
                        "outcome": "passed",
                    }
                )
                checkpoint("assets")
            pending_preparation = (
                "runtime-installation" in record["completed_stages"]
                and "memory-preparation" not in record["completed_stages"]
            )
            # The common preparation helper appends its protective ignore block
            # before publishing canonical resources. Let that helper validate and
            # finish an interrupted preparation while preserving the existing
            # ignore content; all other adopted assets retain their exact hashes.
            verify_files(
                destination,
                {
                    key: value
                    for key, value in record["owned_files"].items()
                    if not (pending_preparation and key == ".gitignore")
                },
            )
            record["active_stage"] = "registration"
            checkpoint()
            if "registration" not in record["completed_stages"]:
                record["registry"] = register_project(
                    depot, registry_candidate(identity, destination), registry_before
                )
                checkpoint("registration")
            else:
                latest, _ = read_registry(depot)
                if record["registry"]["entry"] not in latest["projects"]:
                    raise InitializationError(
                        "registered project changed during recovery"
                    )
            record["active_stage"] = "runtime-installation"
            checkpoint()
            artifact_receipt, artifact = artifact_selection(depot, artifact_receipt)
            if sha(file_bytes(artifact_receipt)) != record["artifact_sha256"]:
                raise InitializationError("recorded artifact receipt changed")
            if "runtime-installation" not in record["completed_stages"]:
                record["runtime"] = process(
                    [
                        sys.executable,
                        str(depot / PRODUCT / "tools/build_consumer_artifact.py"),
                        "install",
                        str(artifact_receipt),
                        "--project-root",
                        str(destination),
                        "--python",
                        sys.executable,
                    ],
                    destination,
                )
                record["checks"].append(
                    {
                        "check": "immutable wheel installation and installed byte provenance",
                        "outcome": "passed",
                    }
                )
                checkpoint("runtime-installation")
            record["active_stage"] = "memory-preparation"
            checkpoint()
            if "memory-preparation" not in record["completed_stages"]:
                record["preparation"] = process(
                    [
                        str(destination / ".venv/bin/python"),
                        "-I",
                        "-m",
                        "sys4ai_memory.bootstrap",
                        "prepare",
                        "--project-root",
                        str(destination),
                        "--project-id",
                        project_id,
                        "--project-name",
                        project_name,
                        "--principal-id",
                        principal_id,
                    ],
                    destination,
                )
                preparation = record["preparation"]
                for key in ("created_files", "updated_files", "preserved_files"):
                    for path in preparation[key]:
                        record["owned_files"][path] = sha(
                            file_bytes(destination_file(destination, path))
                        )
                record["owned_files"][".gitignore"] = sha(
                    file_bytes(destination / ".gitignore")
                )
                for source in record["sources"]:
                    final_hash = sha(
                        file_bytes(destination_file(destination, source["destination"]))
                    )
                    if source["destination_sha256"] != final_hash:
                        source["adopted_sha256"] = source["destination_sha256"]
                        source["destination_sha256"] = final_hash
                        source["local_change"] = (
                            "common memory preparation protection rules"
                        )
                record["owned_files"][
                    "control_records/memory/runtime-installation.json"
                ] = sha(
                    file_bytes(
                        destination / "control_records/memory/runtime-installation.json"
                    )
                )
                installed_parent = Path(
                    record["runtime"]["observed"]["origin"]
                ).parent.parent
                record["installed_package_files"] = {
                    (installed_parent / name).relative_to(destination).as_posix(): value
                    for name, value in artifact["wheel"]["files"].items()
                    if name.startswith("sys4ai_memory/")
                }
                checkpoint("memory-preparation")
            if mode == "create":
                record["active_stage"] = "memory-initialization"
                checkpoint()
                if "memory-initialization" not in record["completed_stages"]:
                    initialized = process(
                        memory_arguments(
                            destination,
                            identity,
                            "init-memory",
                            "--idempotency-key",
                            "project-initializer-direct-v1",
                        ),
                        destination,
                    )
                    record["initialization"] = initialized["result"]["initialization"]
                    checkpoint("memory-initialization")
                record["active_stage"] = "memory-verification"
                checkpoint()
                if "memory-verification" not in record["completed_stages"]:
                    synchronized = process(
                        memory_arguments(
                            destination,
                            identity,
                            "sync",
                            "--idempotency-key",
                            "project-initializer-sync-v1",
                        ),
                        destination,
                    )
                    if synchronized["result"].get("failure_count") != 0:
                        raise InitializationError(
                            "registered source synchronization reported failures"
                        )
                    recalled = process(
                        memory_arguments(
                            destination,
                            identity,
                            "recall",
                            project_id,
                            "--mode",
                            "exact",
                        ),
                        destination,
                    )
                    results = recalled["result"]["retrieval"]["results"]
                    if not results:
                        raise InitializationError(
                            "installed exact recall returned no project evidence"
                        )
                    record["functional_memory"] = {
                        "synchronization": synchronized["result"],
                        "exact_recall_result_count": len(results),
                        "query": project_id,
                        "canonical_readme_sha256": sha(
                            file_bytes(destination / "README.md")
                        ),
                    }
                    record["checks"].append(
                        {
                            "check": "installed subprocess direct initialization, synchronization and exact retrieval",
                            "outcome": "passed",
                        }
                    )
                    checkpoint("memory-verification")
                record["status"] = "completed"
            else:
                record["status"] = "prepared"
                record["next_command"] = memory_arguments(
                    destination,
                    identity,
                    "init-memory",
                    "--idempotency-key",
                    "manual-project-direct-v1",
                )
                record["next_command_shell"] = shlex.join(record["next_command"])
            record["active_stage"] = None
            # Source content is unnecessary after adoption; retain only digests in
            # the final non-secret receipt rather than bulk recovery byte copies.
            record.pop("recovery_before", None)
            record.setdefault("finished_at", datetime.now(timezone.utc).isoformat())
            verify_files(destination, record["owned_files"])
            checkpoint()
            if mode == "create":
                final_path = destination_file(destination, FINAL_RECEIPT)
                existing = file_bytes(final_path) if final_path.exists() else None
                if existing != encoded(record):
                    atomic_write(final_path, encoded(record), None, mode=0o600)
            return record
        except (
            InitializationError,
            OSError,
            subprocess.TimeoutExpired,
            KeyError,
            ValueError,
        ) as error:
            record["status"] = "partial"
            observed_owned = {}
            for owned_relative, expected_data in proposed.items():
                try:
                    owned_path = destination_file(destination, owned_relative)
                    if owned_path.exists() and file_bytes(owned_path) == expected_data:
                        observed_owned[owned_relative] = sha(expected_data)
                except (InitializationError, OSError):
                    observed_owned[owned_relative] = (
                        "changed-or-unsafe; separate inspection required"
                    )
            record["recovery"] = {
                "stage": record["active_stage"],
                "completed_stages": list(record["completed_stages"]),
                "owned_record": str(record_path),
                "observed_owned_files": observed_owned,
                "environment_present": (destination / ".venv").exists(),
                "memory_state_present": (destination / ".sys4ai/memory").exists(),
                "next_action": "Inspect the recorded owned state, then repeat the identical command to resume. Preserve unrelated project files; Git and provider/model activation remain separate.",
                "error_type": type(error).__name__,
                "reason": str(error)
                if isinstance(error, InitializationError)
                else "Local operation failed; inspect the owned stage without publishing raw logs.",
            }
            try:
                checkpoint()
            except (InitializationError, OSError):
                record["recovery"]["record_update"] = (
                    "failed; inspect the returned record and preserve the on-disk version"
                )
            raise InitializationError(
                "project initialization is incomplete; owned state was retained for recovery",
                report=record,
            ) from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    for mode in ("create", "prepare-existing"):
        route = commands.add_parser(mode)
        route.add_argument("--destination", type=Path, required=True)
        route.add_argument("--project-id", required=True)
        route.add_argument("--project-name", required=True)
        route.add_argument("--purpose", required=True)
        route.add_argument("--principal-id", required=True)
        route.add_argument("--artifact-receipt", type=Path)
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
