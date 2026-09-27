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
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import types
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
SETUP_CONTRACT = "governance-starter-v10"
ADVANCED_CONTRACT = "governance-starter-v9"
CURATOR_CONTRACTS = {SETUP_CONTRACT}
ONTOLOGY_CONTRACT = "governance-starter-v8"
LEARNING_CONTRACT = "governance-starter-v7"
CAPTURE_CONTRACT = "governance-starter-v6"
MEMORY_CONTRACT = "governance-starter-v5"
MEMORY_CONTRACTS = {MEMORY_CONTRACT, CAPTURE_CONTRACT, LEARNING_CONTRACT, ONTOLOGY_CONTRACT, ADVANCED_CONTRACT, SETUP_CONTRACT}
CAPTURE_CONTRACTS = {CAPTURE_CONTRACT, LEARNING_CONTRACT, ONTOLOGY_CONTRACT, ADVANCED_CONTRACT, SETUP_CONTRACT}
LEARNING_CONTRACTS = {LEARNING_CONTRACT, ONTOLOGY_CONTRACT, ADVANCED_CONTRACT, SETUP_CONTRACT}
ONTOLOGY_CONTRACTS = {ONTOLOGY_CONTRACT, ADVANCED_CONTRACT, SETUP_CONTRACT}
ADVANCED_CONTRACTS = {ADVANCED_CONTRACT, SETUP_CONTRACT}
LICENSE_CONTRACT = "governance-starter-v4"
PRE_LICENSE_CONTRACT = "governance-starter-v3"
LOWERCASE_CONTRACT = "governance-starter-v2"
LEGACY_CONTRACT = "governance-starter-v1"
ROLE_ROOTS = {SETUP_CONTRACT: "Roles", ADVANCED_CONTRACT: "Roles", ONTOLOGY_CONTRACT: "Roles", LEARNING_CONTRACT: "Roles", CAPTURE_CONTRACT: "Roles", MEMORY_CONTRACT: "Roles", LICENSE_CONTRACT: "Roles", PRE_LICENSE_CONTRACT: "Roles", LOWERCASE_CONTRACT: "roles",
              LEGACY_CONTRACT: "sub-agent-roles"}
LICENSE_CONTRACTS = {LICENSE_CONTRACT, *MEMORY_CONTRACTS}
LICENSE_FILES = {"LICENSE", "LICENSE-CODE", "LICENSE-DOCS"}
MEMORY_FILES = {"memory.yaml", "MEMORY/README.md"}
MEMORY_CONTRACT_ROOT = "reference-assets/MEMORY-depo"
MEMORY_CONTRACT_FILES = {MEMORY_CONTRACT_ROOT + "/" + name for name in (
    "README.md", "policy.md", "publication-and-recovery.md",
    "schema/config-v1.json", "schema/record-v1.json",
    "schema/backend-projection-v1.json", "schema/normalization-v1.json",
    "profiles/basic-memory-v0.23.0.json",
)}
MEMORY_TREES = ("MEMORY", MEMORY_CONTRACT_ROOT, ".agents/skills/memory")
MEMORY_HELPER_FILES = {".agents/skills/memory/scripts/" + name for name in ("memory_core.py", "memory_paths.py")}
CAPTURE_HELPER_FILES = {".agents/skills/memory/scripts/memory_capture.py",
                        ".agents/skills/memory/references/automatic-capture.md"}
LEARNING_MODULE = "what-did-you-learn"
LEARNING_ROOT = "reference-assets/LEARNING-depo"
LEARNING_SKILL = ".agents/skills/what-did-you-learn"
LEARNING_RESOLVER = LEARNING_SKILL + "/scripts/learning_contract.py"
LEARNING_FILES = {LEARNING_ROOT + "/" + name for name in (
    "contract.json", "README.md", "policy.md", "review-contract.md", "assets/lesson-body-template.md")}
LEARNING_TREES = (LEARNING_ROOT, LEARNING_SKILL)
ONTOLOGY_MODULE = "ontology"
ONTOLOGY_CONTEXT_SHA256 = "7dd394c9ed0bb5398781b690988403e7ae60f6f70195fed24088dd1ef8654d92"
ONTOLOGY_ROOT = "reference-assets/ONTOLOGY-depo"
ONTOLOGY_SKILL = ".agents/skills/ontology"
ONTOLOGY_TREES = ("ONTOLOGY", ONTOLOGY_ROOT, ONTOLOGY_SKILL)
ONTOLOGY_FILES = {"ontology.yaml", "ONTOLOGY/contexts/context-v1.jsonld",
    "ONTOLOGY/modules/project/project.jsonld", "ONTOLOGY/bindings/bindings.jsonld",
    *("ONTOLOGY/modules/sys4ai-core/1.0.0/" + name for name in
      ("manifest.json", "core.jsonld", "context-v1.jsonld", "vocabulary-source.md", "competency.json"))}
ONTOLOGY_REFERENCE_FILES = {ONTOLOGY_ROOT + "/" + name for name in
    ("contract.json", "profile.md", "state-paths.md", "publication-and-recovery.md",
     "contexts/context-v1.jsonld", "schema/record-v1.json")}
ONTOLOGY_FILES |= ONTOLOGY_REFERENCE_FILES
ONTOLOGY_HELPERS = {ONTOLOGY_SKILL + "/scripts/" + name for name in
    ("ontology.py", "ontology_core.py", "ontology_modules.py", "ontology_validate.py", "ontology_build.py",
     "ontology_publication.py", "ontology_authority.py", "ontology_lifecycle.py", "ontology_retrieval.py", "ontology_graph.py",
     "ontology_wiki.py", "ontology_knowledge.py", "ontology_memory.py", "ontology_packet.py", "check_ontology.py")}
ONTOLOGY_SKILL_RESOURCES = ONTOLOGY_HELPERS | {ONTOLOGY_SKILL + "/" + name for name in
    ("SKILL.md", "README.md", "references/commands.md", "references/knowledge-routing.md",
     "references/memory-integration.md", "references/task-integration.md", "references/verification.md")}
COMPLETION_REFERENCE = ".agents/skills/memory/references/automatic-capture.md"
# Supported pure inspectors are pinned with this initializer edition. Unknown
# project customizations are preserved and never executed for assessment.
LEARNING_INSPECTOR_SHA256 = "2d28d84bc560012ca7fa105155ed1081205de1c82bccabdda864790005ec8d8d"
MEMORY_INSPECTOR_SHA256 = {
    ".agents/skills/memory/scripts/memory_core.py": "48592604ac950e32e4c80aab24edd2e90d26d09df1b6af912dcad24bbc490a54",
    ".agents/skills/memory/scripts/memory_paths.py": "5e7c01db65adf4296d97b166945a80a18875055a46811eeb30c701ab7040f7de",
}
# Earlier reviewed pure config validators remain usable for read-only assessment
# of preserved editions; new Template source must use the current pin above.
MEMORY_COMPATIBLE_INSPECTORS = {
    ".agents/skills/memory/scripts/memory_core.py": {"a41175553ec3e4d81b7cede8cc26b81676eddb4a7a697db6c1a47aab5929d874"},
}
ROLE_INSPECTOR_SHA256 = {
    "Roles": "b649dc368d9b4f2d8eec032aaf2ae28e08ff493bbaf07d20ef21a55a52fd0cb2",
    "roles": "65f39e7f394b851e1b9018d896417eb67449406f73e32bd981ebe4ddbce37352",
    "sub-agent-roles": "ed0bd7f33650afbed0808d6bb83f8a8be5bd0404294efbeb26dd95fba28e7368",
}
SPECIALIZED_FILES = {"README.md", IDENTITY, "memory.yaml", "ontology.yaml", "ontology-advanced.yaml", "curator.yaml", "Roles/INDEX.md", "AGENTS.md"}
LICENSE_MARKER = re.compile(
    r"(?:licen[cs]e(?:s|[._-].+)?|copying(?:[._-].+)?|copyright(?:[._-].+)?|unlicense(?:[._-].+)?)",
    re.IGNORECASE,
)
ROLE_INDEX = "Roles/INDEX.md"
ROLE_HELPER = ".agents/skills/manage-subagent-roles/scripts/role_catalog.py"
CASE_RECEIPT = ".sys4ai/roles-case-rename.json"
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
    ".transition.json",
}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".log", ".zip", ".whl", ".egg")
RESERVED = {
    "sys4ai",
    "sys4ai-depot",
    "sys4ai-template-project",
    "template",
}

_advanced_spec = importlib.util.spec_from_file_location("_sys4ai_initializer_advanced", Path(__file__).with_name("init_ontology_advanced.py"))
ADVANCED = importlib.util.module_from_spec(_advanced_spec)
_advanced_spec.loader.exec_module(ADVANCED)
ADVANCED_MODULE = ADVANCED.MODULE
_curator_spec = importlib.util.spec_from_file_location("_sys4ai_initializer_curator", Path(__file__).with_name("init_curator.py"))
CURATOR = importlib.util.module_from_spec(_curator_spec)
_curator_spec.loader.exec_module(CURATOR)
CURATOR_MODULE = CURATOR.MODULE
_static_spec = importlib.util.spec_from_file_location("_sys4ai_initializer_static", Path(__file__).with_name("init_static_health.py"))
STATIC = importlib.util.module_from_spec(_static_spec)
_static_spec.loader.exec_module(STATIC)


def _advanced(name, *args, **kwargs):
    return getattr(ADVANCED, name)(types.SimpleNamespace(**globals()), *args, **kwargs)


def _curator(name, *args, **kwargs):
    return getattr(CURATOR, name)(types.SimpleNamespace(**globals()), *args, **kwargs)


def _static(name, *args, **kwargs):
    return getattr(STATIC, name)(types.SimpleNamespace(**globals()), *args, **kwargs)


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


def exact_role_root(root: Path, name: str, *, allow_absent: bool = False) -> None:
    """Check directory entries, never case-insensitive path lookup."""
    matches = sorted(entry.name for entry in root.iterdir() if entry.name.casefold() == name.casefold()) if root.is_dir() else []
    if matches != [name]:
        if not matches and allow_absent:
            return
        raise InitializationError("role directory spelling differs from its setup edition; an explicit case-rename transition is required")
    target = safe(root / name)
    if not target.is_dir():
        raise InitializationError("role collection is not a regular directory")


@contextmanager
def role_validator(raw: bytes, *, role_root: str = "Roles") -> Iterator[Any]:
    """Use the reviewed Template helper bytes, including its receipt validator."""
    if sha(raw) != ROLE_INSPECTOR_SHA256.get(role_root):
        raise InitializationError("unknown role inspector preserved without execution; select explicit compatible role helper adoption: " + ROLE_HELPER)
    module_name = "_initializer_role_catalog_" + sha(raw)
    helper = types.ModuleType(module_name)
    helper.__file__ = ROLE_HELPER
    sys.modules[module_name] = helper
    try:
        exec(compile(raw, ROLE_HELPER, "exec"), helper.__dict__)
        if helper.ROLE_ROOT_NAME != role_root:
            raise InitializationError("role helper requires an explicit active-layout transition")
        yield helper
    except (RuntimeError, AttributeError, OSError, UnicodeError, SyntaxError, ValueError) as error:
        if isinstance(error, InitializationError):
            raise
        raise InitializationError(f"role validation failed: {error}") from error
    finally:
        sys.modules.pop(module_name, None)


def role_index_bytes(files: dict[str, bytes], *, required: bool = False,
                     contract: str = SETUP_CONTRACT) -> bytes:
    """Render with one frozen role helper and disposable role files only."""
    if not {ROLE_HELPER, "SOUL.md"} <= files.keys():
        raise InitializationError("role index lacks its required helper or instruction source")
    role_root = ROLE_ROOTS[contract]
    role_index = role_root + "/INDEX.md"
    with role_validator(files[ROLE_HELPER], role_root=role_root) as helper:
        with tempfile.TemporaryDirectory(prefix="sys4ai-initializer-roles-") as temporary:
            root = Path(temporary).resolve()
            (root / role_root).mkdir()
            for relative, raw in files.items():
                if relative == "SOUL.md" or relative.startswith(role_root + "/") and relative != role_index:
                    target = destination_file(root, relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
            catalog = helper.build_catalog(root)
            if required and (catalog.invalid_roles or not {"project-sub-agent", "task-manager"} <= {entry.name for entry in catalog.valid_roles}):
                raise InitializationError("template role pairs are invalid or required roles are missing")
            return helper.render_index(catalog).encode()


def template_sources(
    depot: Path, *, contract: str = SETUP_CONTRACT,
) -> tuple[dict[str, bytes], dict[str, Path], dict[str, str], bytes, bytes]:
    template = safe(depot / TEMPLATE)
    policy = file_bytes(template / TEMPLATE_POLICY)
    specification = unique_json(policy)
    if contract not in ROLE_ROOTS:
        raise InitializationError("unsupported starter edition")
    role_root = ROLE_ROOTS[contract]
    exact_role_root(template, role_root)
    if (
        not isinstance(specification, dict)
        or specification.get("schema_version") != 2
        or specification.get("skills") != ".agents/skills"
        or specification.get("roles") != role_root
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
        or set(starter_files) != required_starters(contract)
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
    for collection in (".agents/skills", role_root):
        names = package_names(template / collection)
        required = required_skills(contract) if collection == ".agents/skills" else ({"project-sub-agent"} if contract == LEGACY_CONTRACT else {"project-sub-agent", "task-manager"})
        if not required.issubset(names):
            raise InitializationError("template lacks required governance packages or generic role")
        for name in names:
            source = template / collection / name
            package = package_files(source) if collection == ".agents/skills" else tree_files(source)
            if collection == role_root and not {"AGENTS.md", "ROLE.md"}.issubset(package):
                raise InitializationError("template role bundle lacks AGENTS.md or ROLE.md")
            version = "sha256:" + sha(encoded({relative: sha(raw) for relative, raw in package.items()}))
            for relative, raw in package.items():
                include(f"{collection}/{name}/{relative}", raw, version=version)
    if contract != LEGACY_CONTRACT:
        role_index = role_root + "/INDEX.md"
        index = file_bytes(template / role_index)
        if index != role_index_bytes(copied, required=True, contract=contract):
            raise InitializationError("template role index is stale; run the reviewed Template update")
        include(role_index, index)
    reference = safe(template / "reference-assets")
    if reference.exists():
        for relative, raw in tree_files(reference).items():
            include("reference-assets/" + relative, raw)
    if contract in MEMORY_CONTRACTS:
        if not (MEMORY_CONTRACT_FILES | MEMORY_HELPER_FILES) <= copied.keys():
            raise InitializationError("template lacks required memory contract assets")
        if set(tree_files(template / "MEMORY")) != {"README.md"}:
            raise InitializationError("template memory is not empty")
    if contract in CAPTURE_CONTRACTS and not CAPTURE_HELPER_FILES <= copied.keys():
        raise InitializationError("template lacks automatic memory capture support")
    if contract in LEARNING_CONTRACTS:
        validate_learning_sources(template, copied)
    if contract in ONTOLOGY_CONTRACTS:
        validate_ontology_sources(template, copied)
    if contract in ADVANCED_CONTRACTS:
        _advanced("validate_static", copied, neutral=True)
        _static("validate_source", copied, contract=contract)
    if contract in CURATOR_CONTRACTS:
        _curator("validate_static", copied, neutral=True)
    renderer = file_bytes(template / README_RENDERER)
    return copied, origins, versions, renderer, policy


def required_starters(contract: str) -> set[str]:
    # Older receipts retain the file inventory of their original edition.
    return (STARTER_FILES | (LICENSE_FILES if contract in LICENSE_CONTRACTS else set())
            | (MEMORY_FILES if contract in MEMORY_CONTRACTS else set())
            | (LEARNING_FILES if contract in LEARNING_CONTRACTS else set())
            | (ONTOLOGY_FILES if contract in ONTOLOGY_CONTRACTS else set())
            | (ADVANCED.STARTERS if contract in ADVANCED_CONTRACTS else set())
            | (CURATOR.STARTERS if contract in CURATOR_CONTRACTS else set()))


def required_skills(contract: str) -> set[str]:
    return (REQUIRED_SKILLS | ({"memory"} if contract in MEMORY_CONTRACTS else set())
            | ({LEARNING_MODULE} if contract in LEARNING_CONTRACTS else set())
            | ({ONTOLOGY_MODULE} if contract in ONTOLOGY_CONTRACTS else set())
            | ({"curate"} if contract in CURATOR_CONTRACTS else set()))


@contextmanager
def learning_resolver(raw: bytes) -> Iterator[Any]:
    """Load the reviewed pure resolver without importing a project runtime."""
    if sha(raw) != LEARNING_INSPECTOR_SHA256:
        raise InitializationError("unknown learning inspector preserved without execution: " + LEARNING_RESOLVER)
    name = "_initializer_learning_" + sha(raw)
    module = types.ModuleType(name)
    module.__file__ = LEARNING_RESOLVER
    previous = sys.modules.get(name)
    bytecode = sys.dont_write_bytecode
    sys.modules[name] = module
    try:
        exec(compile(raw, LEARNING_RESOLVER, "exec"), module.__dict__)
        yield module
    except (AttributeError, ImportError, UnicodeError, SyntaxError, ValueError, RuntimeError) as error:
        if isinstance(error, InitializationError):
            raise
        raise InitializationError("learning resolver is unavailable or incompatible") from error
    finally:
        sys.dont_write_bytecode = bytecode
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous


def validate_learning_sources(template: Path, files: dict[str, bytes]) -> None:
    if not (LEARNING_FILES | {LEARNING_RESOLVER}) <= files.keys():
        raise InitializationError("template lacks required learning module resources")
    manifest = unique_json(files[LEARNING_ROOT + "/contract.json"])
    check_memory_inspectors(files)
    with learning_resolver(files[LEARNING_RESOLVER]) as helper:
        try:
            helper._validate_manifest(manifest, LEARNING_ROOT + "/contract.json")
        except helper.ContractError as error:
            raise InitializationError("template learning compatibility inventory is invalid") from error
        declared = {LEARNING_ROOT + "/" + name for name in manifest["required_resources"]}
        actual = {name for name in files if name.startswith(LEARNING_ROOT + "/")}
        if actual != declared:
            raise InitializationError("template learning resource inventory differs from its contract")
        resolution = helper.resolve(template)
        if not resolution["capabilities"]["shared_automatic_checkpoint"]:
            paths = sorted({item["path"] for item in resolution["errors"]})
            raise InitializationError("template learning interfaces or completion routing are incompatible: " + ", ".join(paths))


def check_memory_inspectors(files: dict[str, bytes], *, preserved: bool = False) -> None:
    for name, expected in MEMORY_INSPECTOR_SHA256.items():
        allowed = {expected} | (MEMORY_COMPATIBLE_INSPECTORS.get(name, set()) if preserved else set())
        if name not in files or sha(files[name]) not in allowed:
            raise InitializationError("unknown memory inspector preserved without execution: " + name)


def validate_memory_config(config: Any, files: dict[str, bytes], *, allow_template: bool) -> None:
    """Run the pure validator from the same frozen Template skill edition."""
    names = ("memory_paths", "_initializer_memory_core")
    previous = {name: sys.modules.get(name) for name in names}
    try:
        modules = []
        for name, filename in zip(names, ("memory_paths.py", "memory_core.py")):
            relative = ".agents/skills/memory/scripts/" + filename
            module = types.ModuleType(name)
            module.__file__ = relative
            sys.modules[name] = module
            exec(compile(files[relative], relative, "exec"), module.__dict__)
            modules.append(module)
        try:
            modules[1].validate_config(config, allow_template=allow_template)
        except modules[0].MemoryError as error:
            raise InitializationError(f"memory configuration failed validation: {error}") from error
    except (KeyError, AttributeError, ImportError, UnicodeError, SyntaxError, ValueError) as error:
        raise InitializationError("template memory configuration validator is unavailable or invalid") from error
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def specialize_memory(raw: bytes, identity: dict[str, Any], files: dict[str, bytes],
                      *, automatic: bool = False, destination: Path | None = None,
                      owned_governance: frozenset[str] = frozenset()) -> bytes:
    """Specialize only an empty, portable Template configuration."""
    config = unique_json(raw)
    validate_memory_config(config, files, allow_template=True)
    if (not isinstance(config, dict) or config.get("schema_version") != 1
            or config.get("project") != {"id": None, "name": None, "root": "."}
            or config.get("canonical_root") != "MEMORY"
            or config.get("contract_root") != MEMORY_CONTRACT_ROOT
            or config.get("backend") != {"name": "basic-memory", "enabled": False, "semantic_enabled": False}
            or config.get("publication") != {"director": None}
            or config.get("corpus", {}).get("source_groups") != []):
        raise InitializationError("template memory configuration is not an empty portable starter")
    config["project"] = {"id": identity["project_id"], "name": identity["project_name"], "root": "."}
    if automatic:
        config["integration"]["automatic_capture"] = True
        # Bind the new installation to this project's final governance, including
        # preserved existing instructions, never to the depot's authority.
        authority = []
        for name in ("SOUL.md", "AGENTS.md", "ROLE.md"):
            target = destination_file(destination, name) if destination is not None else None
            raw_authority = (file_bytes(target) if name not in owned_governance
                             and target is not None and target.exists() else files[name])
            authority.append({"path": name, "sha256": sha(raw_authority)})
        config["publication"]["director"] = {"actor_id": "/root", "authority": authority,
            "scope": ["MEMORY", "control_records/memory", ".sys4ai/memory"]}
    validate_memory_config(config, files, allow_template=False)
    return encoded(config)


def source_snapshot(
    depot: Path, skill: Path, identity: dict[str, Any], *, contract: str = SETUP_CONTRACT,
    destination: Path | None = None,
    owned_governance: frozenset[str] = frozenset(),
) -> tuple[dict[str, bytes], list[dict[str, str]], dict[str, bytes]]:
    # The installed skill provides code only. Every starter input, including the
    # allowlist and README renderer, is read from the registered template.
    original, origins, versions, renderer, policy = template_sources(depot, contract=contract)
    proposed = dict(original)
    # Never copy a populated Task index as the new project's empty state.
    if (
        b"| None |" not in proposed["Tasks/INDEX.md"]
        or b"TASK-" in proposed["Tasks/INDEX.md"]
    ):
        raise InitializationError("template Task index is not empty")
    proposed["README.md"] = renderer.decode().format(**identity).encode()
    proposed[IDENTITY] = encoded(identity)
    if contract in MEMORY_CONTRACTS:
        memory_files = original
        binding_owned = owned_governance
        if contract in LEARNING_CONTRACTS and destination is not None:
            config_path = destination_file(destination, "memory.yaml")
            first_binding = (not config_path.exists() or "memory.yaml" in owned_governance
                             or not (destination / IDENTITY).exists()
                             and file_bytes(config_path) == original["memory.yaml"])
            if first_binding:
                memory_files = dict(original)
                for name in ("SOUL.md", "AGENTS.md", "ROLE.md"):
                    target = destination_file(destination, name)
                    if target.exists():
                        memory_files[name] = file_bytes(target)
                if not any(COMPLETION_REFERENCE.encode() in memory_files[name]
                           for name in ("SOUL.md", "AGENTS.md", "ROLE.md")):
                    memory_files["AGENTS.md"] += completion_link()
                proposed["AGENTS.md"] = memory_files["AGENTS.md"]
                binding_owned = owned_governance | {"SOUL.md", "AGENTS.md", "ROLE.md"}
        proposed["memory.yaml"] = specialize_memory(original["memory.yaml"], identity, memory_files,
            automatic=contract in CAPTURE_CONTRACTS, destination=destination, owned_governance=binding_owned)
    if contract in ONTOLOGY_CONTRACTS:
        proposed["ontology.yaml"] = specialize_ontology(original["ontology.yaml"], identity, proposed,
            destination=destination, owned_governance=owned_governance | ({"AGENTS.md"} if proposed["AGENTS.md"] != original["AGENTS.md"] else set()))
    if contract in ADVANCED_CONTRACTS:
        proposed[ADVANCED.CONFIG] = _advanced("specialize", original[ADVANCED.CONFIG], identity, proposed,
            destination=destination, owned_governance=owned_governance | ({"AGENTS.md"} if proposed["AGENTS.md"] != original["AGENTS.md"] else set()))
    if contract in CURATOR_CONTRACTS:
        proposed[CURATOR.CONFIG] = _curator("specialize", original[CURATOR.CONFIG], identity, destination=destination)
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


def check_sources(depot: Path, records: list[dict[str, str]], *, contract: str = SETUP_CONTRACT) -> None:
    expected = {entry["source"]: entry["source_sha256"] for entry in records}
    try:
        copied, origins, _, renderer, policy = template_sources(depot, contract=contract)
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


def completion_link() -> bytes:
    return ("\n\n## Learning and memory completion\n\n"
            "At substantive work completion, follow the project-local "
            f"[shared completion checkpoint]({COMPLETION_REFERENCE}) when memory automatic capture is enabled.\n").encode()


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
            _ontology_checkpoint(targets=False)
            os.link(staging, target, follow_symlinks=False)
        else:
            _ontology_checkpoint(targets=False)
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
        _ontology_checkpoint()
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
        _ontology_checkpoint()
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


def license_inventory(destination: Path) -> dict[str, str]:
    """Record root license markers and their trees without changing project terms."""
    result = {}
    if destination.exists():
        for marker in sorted(destination.iterdir()):
            if not LICENSE_MARKER.fullmatch(marker.name):
                continue
            safe(marker)
            for item in [marker, *sorted(marker.rglob("*"))] if marker.is_dir() else [marker]:
                safe(item)
                result[item.relative_to(destination).as_posix()] = (
                    "directory" if item.is_dir() else sha(file_bytes(item)))
    return result


def check_license_adoption(destination: Path, record: dict[str, Any]) -> None:
    """Recheck the reviewed licensing set, allowing only already-published starters."""
    if record["setup_contract"] not in LICENSE_CONTRACTS:
        return
    expected = dict(record["preserved_licenses"])
    for name in LICENSE_FILES & record["owned_files"].keys():
        target = destination_file(destination, name)
        if target.exists():
            expected[name] = record["owned_files"][name]
    if license_inventory(destination) != expected:
        raise InitializationError("project licensing changed during asset adoption")


def memory_path(name: str) -> bool:
    return name == "memory.yaml" or any(name == root or name.startswith(root + "/") for root in MEMORY_TREES)


def memory_inventory(destination: Path) -> dict[str, str]:
    """Observe complete project-owned memory collections without filtering files."""
    result = {}
    for name in ("memory.yaml", *MEMORY_TREES):
        marker = safe(destination / name)
        if not marker.exists():
            continue
        if name != "memory.yaml" and not marker.is_dir():
            raise InitializationError("existing memory collection is not a directory")
        for item in [marker, *sorted(marker.rglob("*"))] if marker.is_dir() else [marker]:
            safe(item)
            result[item.relative_to(destination).as_posix()] = (
                "directory" if item.is_dir() else sha(file_bytes(item)))
    return result


def check_memory_adoption(destination: Path, record: dict[str, Any]) -> None:
    if record["setup_contract"] not in MEMORY_CONTRACTS:
        return
    expected = dict(record["preserved_memory"])
    for name, checksum in record["owned_files"].items():
        if memory_path(name) and destination_file(destination, name).exists():
            prior = record.get("recovery_before", {}).get(name)
            actual = sha(file_bytes(destination_file(destination, name)))
            expected[name] = prior if prior is not None and actual == prior else checksum
            parent = Path(name).parent
            while memory_path(parent.as_posix()):
                expected[parent.as_posix()] = "directory"
                parent = parent.parent
    if memory_inventory(destination) != expected:
        raise InitializationError("project memory changed during asset adoption")


def asset_plan(destination: Path, *, mode: str, proposed: dict[str, bytes],
               original: dict[str, bytes], saved_identity: dict[str, Any] | None,
               preserved_licenses: dict[str, str]
               ) -> tuple[dict[str, bytes], dict[str, str | None], dict[str, str]]:
    selected, before, preserved = {}, {}, {}
    curator_starter = CURATOR.CONFIG in proposed and "CURATOR.md" in proposed
    ontology_before = ontology_inventory(destination)
    preserve_ontology = bool(ontology_before) and ontology_before != ontology_files_inventory(original)
    for name, raw in proposed.items():
        if name in LICENSE_FILES and preserved_licenses and safe(destination / name).is_dir():
            # A project may use LICENSE/ as a directory. Preserve it without
            # trying to publish a regular starter file at the same path.
            continue
        target = destination_file(destination, name)
        present = file_bytes(target) if target.exists() else None
        if mode == "prepare-existing" and preserve_ontology and ontology_path(name):
            if present is not None:
                preserved[name] = sha(present)
            continue
        if mode == "create":
            if present is not None:
                raise InitializationError("new project changed before asset adoption")
            selected[name], before[name] = raw, None
            continue
        # A project owns an existing package as a whole. Filling missing resources
        # from a newer Template could combine incompatible package versions.
        parts = Path(name).parts
        curator_role = curator_starter and len(parts) > 2 and parts[0] == "Roles" and parts[1] in CURATOR.ROLES
        package_exists = ((name.startswith(".agents/skills/") and len(parts) > 3
                           and (destination / Path(*parts[:3])).is_dir())
                          or (name.startswith("Roles/") and name != ROLE_INDEX
                              and (destination / Path(*parts[:2]) if curator_role else destination / "Roles").is_dir())
                          or any(name.startswith(root + "/") and (destination / root).is_dir()
                                 for root in (*MEMORY_TREES, *LEARNING_TREES, *ONTOLOGY_TREES, *((CURATOR.REFERENCE,) if curator_starter else ()))))
        existing_tasks = (name.startswith("Tasks/") and (destination / "Tasks").is_dir()
                          and any((destination / "Tasks").iterdir()))
        if present is not None:
            if (name == "AGENTS.md" and raw != original.get(name) and raw != present and raw == present + completion_link()):
                selected[name], before[name] = raw, sha(present)
            elif saved_identity is None and name in {"README.md", "memory.yaml", "ontology.yaml", ADVANCED.CONFIG, CURATOR.CONFIG} and present == original.get(name):
                selected[name], before[name] = raw, sha(present)
            else:
                preserved[name] = sha(present)
        elif not (package_exists or existing_tasks or name in LICENSE_FILES and preserved_licenses):
            selected[name], before[name] = raw, None
    if ROLE_INDEX in proposed:
        index = planned_role_index(destination, proposed, selected)
        present = file_bytes(destination / ROLE_INDEX) if (destination / ROLE_INDEX).exists() else None
        if present is not None and present != index:
            curator_additions = any(name.startswith(tuple("Roles/" + role + "/" for role in CURATOR.ROLES)) for name in selected)
            prior_selected = {name: raw for name,raw in selected.items() if not name.startswith("Roles/")}
            if curator_starter and curator_additions and present == planned_role_index(destination, proposed, prior_selected):
                selected[ROLE_INDEX], before[ROLE_INDEX] = index, sha(present)
                preserved.pop(ROLE_INDEX, None)
            else:
                raise InitializationError("existing role index differs from current pairs; preserve it for explicit reindex")
        if ROLE_INDEX in selected:
            selected[ROLE_INDEX] = index
    return selected, before, preserved


def planned_role_index(destination: Path, proposed: dict[str, bytes], owned: dict[str, Any],
                       *, contract: str = SETUP_CONTRACT) -> bytes:
    effective = {name: proposed[name] if name in owned else file_bytes(destination / name) for name in ("SOUL.md", ROLE_HELPER)}
    role_name = ROLE_ROOTS[contract]
    role_index = role_name + "/INDEX.md"
    exact_role_root(destination, role_name, allow_absent=True)
    role_root = safe(destination / role_name)
    if role_root.exists():
        effective.update({role_name + "/" + name: raw for name, raw in tree_files(role_root).items() if name != "INDEX.md"})
    effective.update({name: proposed[name] for name in owned if name.startswith(role_name + "/") and name != role_index})
    return role_index_bytes(effective, contract=contract)


def check_existing_role_layout(destination: Path, validator_raw: bytes) -> None:
    exact_role_root(destination, "Roles", allow_absent=True)
    legacy = safe(destination / "sub-agent-roles")
    package = safe(destination / ".agents/skills/manage-subagent-roles")
    if legacy.exists() and not package.exists():
        raise InitializationError("existing legacy roles require an explicit reviewed transition before new starter adoption")
    if package.exists():
        helper = destination / ROLE_HELPER
        if not helper.is_file():
            raise InitializationError("existing role helper package needs explicit compatibility review")
        try:
            tree = ast.parse(file_bytes(helper))
        except (SyntaxError, ValueError) as error:
            raise InitializationError("existing role helper package needs explicit compatibility review") from error
        roots = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "ROLE_ROOT_NAME" for target in node.targets)
                 and isinstance(node.value, ast.Constant)]
        if roots != ["Roles"]:
            raise InitializationError("existing role helper requires an explicit active-layout transition")
    if not legacy.exists():
        return
    # A copy-first transition retains the legacy directory. Its presence is not
    # completion evidence; validate the exact receipt and live bytes read-only.
    receipt_path = safe(destination / "Roles/.transition.json")
    if not receipt_path.is_file():
        raise InitializationError("retained legacy roles lack an explicit completed transition receipt")
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if not {"build_catalog", "render_index", "transition_apply", "validate_transition_receipt"} <= functions:
        raise InitializationError("existing role helper lacks the current transition contract")
    with role_validator(validator_raw) as validator:
        receipt = validator.load_manifest(receipt_path)
        destinations = validator.validate_transition_receipt(receipt, destination)
        current_paths = validator.transition_destination_paths(receipt, destination)
        if receipt["status"] != "completed":
            raise InitializationError("explicit role transition is incomplete; recover it before preparation")
        preview = receipt["preview"]
        fresh = validator.transition_preview(destination)
        if fresh["legacy_fingerprint"] != preview["legacy_fingerprint"] or fresh["conflicts"]:
            raise InitializationError("completed transition provenance changed or has a destination collision")
        for pair in preview["pairs"]:
            for entry in pair["files"]:
                if sha(file_bytes(destination_file(destination, entry["source"]))) != entry["source_sha256"]:
                    raise InitializationError("retained legacy role bytes changed after their reviewed transition")
        if any(sha(file_bytes(destination_file(destination, current_paths[name]))) != checksum for name, checksum in destinations.items()):
            raise InitializationError("active role bytes differ from the completed transition receipt")
        catalog = validator.build_catalog(destination)
        if catalog.invalid_roles or catalog.index_status != "current":
            raise InitializationError("completed transition lacks current valid active roles and index")


def record_role_paths(record: dict[str, Any], destination: Path
                      ) -> tuple[str, dict[str, str], dict[str, str] | None]:
    """Resolve an earlier edition only through its explicit completed rename."""
    role_root = ROLE_ROOTS[record["setup_contract"]]
    names = sorted(entry.name for entry in destination.iterdir()
                   if entry.name.casefold() == "roles") if destination.is_dir() else []
    if record["setup_contract"] == LOWERCASE_CONTRACT and names == ["Roles"]:
        if "assets" not in record["completed_stages"]:
            raise InitializationError("finish interrupted lowercase asset adoption before its explicit case rename")
        receipt_path = destination_file(destination, CASE_RECEIPT)
        if not receipt_path.is_file():
            raise InitializationError("lowercase setup receipt requires an explicit completed case-rename receipt")
        raw = file_bytes(receipt_path)
        with role_validator(file_bytes(destination / ROLE_HELPER)) as validator:
            proof = validator.validate_case_rename_receipt(unique_json(raw), destination)
        paths = proof["destination_paths"]
        for key in ("owned_files", "preserved_files"):
            files = record.get(key)
            if isinstance(files, dict) and any(isinstance(name, str) and name.startswith("roles/")
                                               and name not in paths for name in files):
                raise InitializationError("case-rename proof omits a recorded lowercase role file")
        evidence = {"path": CASE_RECEIPT, "sha256": sha(raw), "source": "roles", "destination": "Roles"}
        if "role_case_transition" in record and record["role_case_transition"] != evidence:
            raise InitializationError("setup case-rename evidence changed since verification")
        return "Roles", paths, evidence
    if "role_case_transition" in record:
        raise InitializationError("setup case-rename evidence has no matching current role layout")
    exact_role_root(destination, role_root, allow_absent="assets" not in record["completed_stages"])
    return role_root, {}, None


def validate_record(record: Any, destination: Path, identity: dict[str, Any]) -> None:
    if (not isinstance(record, dict) or record.get("schema_version") != 1
            or not isinstance(record.get("setup_contract"), str)
            or record.get("setup_contract") not in ROLE_ROOTS):
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
                or entry.get("adoption") not in {"adopted", "specialized", "preserved-project-owned", "skipped-existing-package", "skipped-existing-license"}):
            raise InitializationError("existing setup receipt has invalid source provenance")
        relative_source = entry["source"].removeprefix(TEMPLATE + "/")
        expected_destination = {README_RENDERER: "README.md", TEMPLATE_POLICY: IDENTITY}.get(
            relative_source, relative_source)
        if entry.get("destination") != expected_destination:
            raise InitializationError("existing setup receipt changes a source destination")
        if entry["adoption"] == "specialized" and (record["setup_contract"] not in MEMORY_CONTRACTS
                                                   or expected_destination not in SPECIALIZED_FILES
                                                   or expected_destination == "AGENTS.md" and record["setup_contract"] not in LEARNING_CONTRACTS
                                                   or expected_destination == ADVANCED.CONFIG and record["setup_contract"] not in ADVANCED_CONTRACTS
                                                   or expected_destination == "ontology.yaml" and record["setup_contract"] not in ONTOLOGY_CONTRACTS):
            raise InitializationError("existing setup receipt has an unsupported specialization")
        if (record["setup_contract"] in LICENSE_CONTRACTS
                and expected_destination in LICENSE_FILES
                and entry["adoption"] == "skipped-existing-license"):
            safe(destination / expected_destination)
        else:
            destination_file(destination, expected_destination)
        checksum = entry.get("destination_sha256")
        skipped = entry["adoption"] in {"skipped-existing-package", "skipped-existing-license"}
        if (skipped and checksum is not None
                or not skipped
                and (not isinstance(checksum, str) or not SHA256.fullmatch(checksum))):
            raise InitializationError("existing setup receipt has an invalid adoption digest")
        adoption = (entry["adoption"], checksum)
        if (expected_destination in source_adoptions
                and source_adoptions[expected_destination] != adoption):
            raise InitializationError("existing setup receipt has conflicting source adoption decisions")
        source_adoptions[expected_destination] = adoption
        seen_sources.add(entry["source"])
    legacy = record["setup_contract"] == LEGACY_CONTRACT
    role_root = ROLE_ROOTS[record["setup_contract"]]
    role_sources = ({"sub-agent-roles/project-sub-agent/AGENTS.md", "sub-agent-roles/project-sub-agent/ROLE.md"} if legacy else
        {role_root + "/INDEX.md", ROLE_HELPER, *(f"{role_root}/{role}/{filename}" for role in ("project-sub-agent", "task-manager") for filename in ("AGENTS.md", "ROLE.md"))})
    incompatible = set(ROLE_ROOTS.values()) - {role_root}
    if any(entry["destination"].startswith(tuple(name + "/" for name in incompatible)) for entry in record["sources"]):
        raise InitializationError("existing setup receipt mixes incompatible role layouts")
    required_sources = {TEMPLATE + "/" + name for name in
        required_starters(record["setup_contract"]) | {"SOUL.md", TEMPLATE_POLICY, README_RENDERER}
        | {f".agents/skills/{name}/SKILL.md" for name in required_skills(record["setup_contract"])}
        | (MEMORY_CONTRACT_FILES | MEMORY_HELPER_FILES if record["setup_contract"] in MEMORY_CONTRACTS else set())
        | (CAPTURE_HELPER_FILES if record["setup_contract"] in CAPTURE_CONTRACTS else set())
        | (LEARNING_FILES | {LEARNING_RESOLVER} if record["setup_contract"] in LEARNING_CONTRACTS else set())
        | (ONTOLOGY_FILES | ONTOLOGY_SKILL_RESOURCES if record["setup_contract"] in ONTOLOGY_CONTRACTS else set())
        | (ADVANCED.STARTERS | ADVANCED.RESOURCES if record["setup_contract"] in ADVANCED_CONTRACTS else set())
        | role_sources}
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
    if record["setup_contract"] in LICENSE_CONTRACTS:
        markers = record.get("preserved_licenses")
        if not isinstance(markers, dict):
            raise InitializationError("existing setup receipt lacks its licensing decision")
        for name, checksum in markers.items():
            if (not isinstance(name, str) or not name or Path(name).as_posix() != name
                    or Path(name).is_absolute() or ".." in Path(name).parts
                    or not LICENSE_MARKER.fullmatch(Path(name).parts[0])
                    or not isinstance(checksum, str)
                    or checksum != "directory" and not SHA256.fullmatch(checksum)):
                raise InitializationError("existing setup receipt has invalid preserved licensing")
            target = safe(destination / name)
            if checksum == "directory":
                if not target.is_dir():
                    raise InitializationError("preserved license directory is missing")
            elif not target.is_file():
                raise InitializationError("preserved license file is missing")
            else:
                # Validate type/alias safety before any receipt or history write;
                # current content may differ from the original preserved hash.
                file_bytes(target)
            if len(Path(name).parts) > 1 and markers.get(Path(name).parent.as_posix()) != "directory":
                raise InitializationError("preserved license tree lacks its parent evidence")
        for name in LICENSE_FILES:
            adoption, checksum = source_adoptions[name]
            if not markers:
                if adoption != "adopted":
                    raise InitializationError("license starter skip lacks preserved licensing")
            elif adoption == "preserved-project-owned":
                target = destination_file(destination, name)
                if not any(value == checksum and value != "directory"
                           and target.samefile(destination / marker)
                           for marker, value in markers.items()):
                    raise InitializationError("preserved license lacks matching marker evidence")
            elif adoption != "skipped-existing-license":
                raise InitializationError("existing setup receipt mixes project licensing with starters")
    elif "preserved_licenses" in record or any(value[0] == "skipped-existing-license" for value in source_adoptions.values()):
        raise InitializationError("older setup receipt contains a later licensing decision")
    if record["setup_contract"] in MEMORY_CONTRACTS:
        inventory = record.get("preserved_memory")
        if not isinstance(inventory, dict):
            raise InitializationError("existing setup receipt lacks its memory preservation decision")
        for name, checksum in inventory.items():
            if (not isinstance(name, str) or not memory_path(name)
                    or not isinstance(checksum, str)
                    or checksum != "directory" and not SHA256.fullmatch(checksum)):
                raise InitializationError("existing setup receipt has invalid memory preservation evidence")
            target = destination_file(destination, name) if checksum != "directory" else safe(destination / name)
            if (Path(name).as_posix() != name or Path(name).is_absolute() or ".." in Path(name).parts
                    or checksum == "directory" and name not in MEMORY_TREES
                    and inventory.get(Path(name).parent.as_posix()) != "directory"):
                raise InitializationError("existing setup receipt has an invalid memory preservation path")
            if (checksum == "directory" and not target.is_dir()
                    or checksum != "directory" and not target.is_file()):
                raise InitializationError("preserved memory file or collection is missing")
            if checksum != "directory":
                file_bytes(target)
                if name != "memory.yaml" and inventory.get(Path(name).parent.as_posix()) != "directory":
                    raise InitializationError("preserved memory file lacks its parent evidence")
        for name, (adoption, checksum) in source_adoptions.items():
            if not memory_path(name):
                continue
            existing = (name == "memory.yaml" and name in inventory or any(
                name.startswith(root + "/") and inventory.get(root) == "directory" for root in MEMORY_TREES))
            expected_adoption = "preserved-project-owned" if name in inventory else "skipped-existing-package"
            pristine_config = (name == "memory.yaml" and adoption == "specialized"
                               and record["setup_contract"] in CAPTURE_CONTRACTS
                               and inventory.get(name) == next(entry["source_sha256"] for entry in record["sources"]
                                                               if entry["destination"] == name))
            if (existing and adoption != expected_adoption and not pristine_config
                    or not existing and adoption == "skipped-existing-package"):
                raise InitializationError("memory source adoption mixes an existing collection with new starters")
            if adoption == "preserved-project-owned" and inventory.get(name) != checksum:
                raise InitializationError("memory source preservation differs from its original inventory")
            if name == "memory.yaml" and adoption not in {"specialized", "preserved-project-owned"}:
                raise InitializationError("memory configuration lacks its specialization or preservation decision")
    elif "preserved_memory" in record or "current_memory" in record:
        raise InitializationError("older setup receipt contains a later memory decision")
    current_role_root, _, _ = record_role_paths(record, destination)
    expected_owned, expected_preserved = {}, {}
    for name, (adoption, checksum) in source_adoptions.items():
        if adoption in {"adopted", "specialized"}:
            expected_owned[name] = checksum
        elif adoption == "preserved-project-owned":
            expected_preserved[name] = checksum
        elif adoption == "skipped-existing-license":
            if name not in LICENSE_FILES or not record.get("preserved_licenses"):
                raise InitializationError("unsupported skipped license starter")
        else:
            # Only resources omitted to preserve an existing whole package or
            # nonempty Task tree can lack an adopted/preserved file digest.
            parts = Path(name).parts
            if record["setup_contract"] in ONTOLOGY_CONTRACTS and ontology_path(name) and record.get("preserved_ontology"):
                continue
            if name.startswith(".agents/skills/") and len(parts) > 3:
                preserved_root = destination / Path(*parts[:3])
            elif legacy and name.startswith("sub-agent-roles/") and len(parts) > 2:
                preserved_root = destination / Path(*parts[:2])
            elif not legacy and name.startswith(role_root + "/") and len(parts) > 2:
                preserved_root = destination / current_role_root
            elif name == "Tasks/INDEX.md":
                preserved_root = destination / "Tasks"
            elif record["setup_contract"] in MEMORY_CONTRACTS and any(
                    name.startswith(root + "/") and record["preserved_memory"].get(root) == "directory"
                    for root in MEMORY_TREES):
                preserved_root = destination / next(root for root in MEMORY_TREES if name.startswith(root + "/"))
            elif record["setup_contract"] in LEARNING_CONTRACTS and any(name.startswith(root + "/") for root in LEARNING_TREES):
                preserved_root = destination / next(root for root in LEARNING_TREES if name.startswith(root + "/"))
            else:
                raise InitializationError("existing setup receipt skips a required standalone starter")
            safe(preserved_root)
            if (not preserved_root.is_dir()
                    or name == "Tasks/INDEX.md" and not any(preserved_root.iterdir())):
                raise InitializationError("existing setup receipt lacks its preserved package or Task tree")
    if record["owned_files"] != expected_owned or record["preserved_files"] != expected_preserved:
        raise InitializationError("existing setup receipt file inventories differ from source adoption decisions")
    if record["setup_contract"] in LEARNING_CONTRACTS:
        inventory = record.get("preserved_learning")
        if not isinstance(inventory, dict):
            raise InitializationError("learning setup receipt lacks complete package preservation evidence")
        for name, digest in inventory.items():
            if (not isinstance(name, str) or not any(name == root or name.startswith(root + "/") for root in LEARNING_TREES)
                    or not isinstance(digest, str) or digest != "directory" and not SHA256.fullmatch(digest)
                    or Path(name).as_posix() != name or ".." in Path(name).parts
                    or name not in LEARNING_TREES and inventory.get(Path(name).parent.as_posix()) != "directory"):
                raise InitializationError("invalid learning preservation inventory")
            safe(destination / name)
        for name, (adoption, digest) in source_adoptions.items():
            root = next((root for root in LEARNING_TREES if name.startswith(root + "/")), None)
            if root and inventory.get(root) == "directory":
                expected = "preserved-project-owned" if name in inventory else "skipped-existing-package"
                if adoption != expected or digest != inventory.get(name):
                    raise InitializationError("learning source adoption mixes an existing whole package")
    validate_ontology_preservation(record, destination, source_adoptions)
    if "assets" not in stages:
        before = record.get("recovery_before")
        if (not isinstance(before, dict) or before.keys() != record["owned_files"].keys()
                or any(value is not None and (not isinstance(value, str) or not SHA256.fullmatch(value))
                       for value in before.values())):
            raise InitializationError("partial setup receipt lacks its asset recovery inventory")
    if record["status"] == "completed" and (stages != STAGES or record["active_stage"] is not None):
        raise InitializationError("completed setup receipt lacks required stages")
    validate_module_adoptions(record, destination)


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


def ontology_path(name: str) -> bool:
    return name == "ontology.yaml" or any(name == root or name.startswith(root + "/") for root in ONTOLOGY_TREES)


def ontology_inventory(destination: Path) -> dict[str, str]:
    result = {name: digest for root in ONTOLOGY_TREES for name, digest in package_inventory(destination, root).items()}
    config = destination_file(destination, "ontology.yaml")
    if config.exists():
        result["ontology.yaml"] = sha(file_bytes(config))
    return result


def ontology_files_inventory(files: dict[str, Any]) -> dict[str, str]:
    result = {name: digest for root in ONTOLOGY_TREES
              for name, digest in inventory_from_files(root, files).items()}
    if "ontology.yaml" in files:
        raw = files["ontology.yaml"]
        result["ontology.yaml"] = sha(raw) if isinstance(raw, bytes) else raw
    return result


def validate_ontology_static(root: Path, files: dict[str, bytes], *, neutral: bool) -> dict[str, Any]:
    """Check bounded declarations and import integrity without executing copied code."""
    missing = sorted((ONTOLOGY_FILES | ONTOLOGY_SKILL_RESOURCES) - files.keys())
    if missing:
        raise InitializationError("ontology resources are missing: " + ", ".join(missing))
    config = unique_json(files["ontology.yaml"])
    keys = {"schema_version", "project", "context", "modules", "project_files", "binding_files", "source_allowlist", "retrieval", "publication"}
    project = config.get("project") if isinstance(config, dict) else None
    if (not isinstance(config, dict) or not keys <= set(config) or not set(config) <= keys | {"competency_files"} or type(config["schema_version"]) is not int or config["schema_version"] != 1
            or not isinstance(project, dict) or set(project) != {"id", "name", "purpose", "namespace", "root"} or project["root"] != "."):
        raise InitializationError("ontology configuration has an incompatible schema or project identity")
    if neutral:
        if project != {"id": None, "name": None, "purpose": None, "namespace": None, "root": "."} or config["publication"] != {"enabled": False, "binding": None}:
            raise InitializationError("template ontology configuration is not a neutral starter")
    elif (not isinstance(project["id"], str) or not ID_PATTERN.fullmatch(project["id"])
          or any(not isinstance(project[key], str) or not project[key].strip() for key in ("name", "purpose", "namespace"))
          or project["namespace"] != "urn:sys4ai:ontology:project:" + project["id"] + ":"):
        raise InitializationError("ontology project identity or namespace is unspecialized or incompatible")
    context = config["context"]
    if (not isinstance(context, dict) or set(context) != {"path", "sha256"}
            or context["path"] != "ONTOLOGY/contexts/context-v1.jsonld"
            or context["sha256"] != ONTOLOGY_CONTEXT_SHA256 or context["sha256"] != sha(files[context["path"]])
            or files[context["path"]] != files[ONTOLOGY_ROOT + "/contexts/context-v1.jsonld"]):
        raise InitializationError("ontology trusted local context does not match its exact lock")
    contract = unique_json(files[ONTOLOGY_ROOT + "/contract.json"])
    if (not isinstance(contract, dict) or contract.get("schema_version") != 1
            or contract.get("module_version") != "1.0.0" or contract.get("profile_version") != "1.0.0"):
        raise InitializationError("ontology contract edition is incompatible")
    modules = config["modules"]
    if not isinstance(modules, list) or not modules:
        raise InitializationError("ontology module selection is missing")
    seen = set()
    for module in modules:
        if (not isinstance(module, dict) or set(module) != {"id", "version", "path", "sha256"}
                or not isinstance(module["id"], str) or not ID_PATTERN.fullmatch(module["id"])
                or not isinstance(module["version"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", module["version"])
                or module["id"] in seen or module["path"] != "ONTOLOGY/modules/" + module["id"] + "/" + module["version"]):
            raise InitializationError("ontology module import is incompatible")
        seen.add(module["id"])
        prefix = module["path"] + "/"
        manifest_path = prefix + "manifest.json"
        if manifest_path not in files:
            raise InitializationError("ontology module manifest is missing: " + manifest_path)
        manifest = unique_json(files[manifest_path])
        if (not isinstance(manifest, dict) or set(manifest) != {"schema_version", "module_id", "version", "files", "record_files"}
                or manifest["schema_version"] != 1 or manifest["module_id"] != module["id"] or manifest["version"] != module["version"]
                or not isinstance(manifest["files"], dict) or not manifest["files"]
                or not isinstance(manifest["record_files"], list) or not manifest["record_files"]):
            raise InitializationError("ontology module manifest is incompatible: " + manifest_path)
        for name, digest in manifest["files"].items():
            destination_file(root, prefix + name)
            if (not isinstance(name, str) or not isinstance(digest, str) or not SHA256.fullmatch(digest)
                    or Path(name).as_posix() != name or name == "manifest.json"
                    or prefix + name not in files or sha(files[prefix + name]) != digest):
                raise InitializationError("ontology module file differs from its lock: " + prefix + str(name))
        for name in manifest["record_files"]:
            if not isinstance(name, str) or prefix + name not in files:
                raise InitializationError("ontology module record file is missing: " + str(name))
            graph = unique_json(files[prefix + name])
            if (not isinstance(graph, dict) or set(graph) != {"@context", "@graph"}
                    or graph["@context"] != context["path"] or not isinstance(graph["@graph"], list)):
                raise InitializationError("ontology module record file is incompatible: " + prefix + name)
        actual = {name.removeprefix(prefix) for name in files if name.startswith(prefix)}
        if (actual != set(manifest["files"]) | {"manifest.json"}
                or module["sha256"] != sha(encoded(manifest["files"]))
                or not set(manifest["record_files"]) <= manifest["files"].keys()
                or manifest["files"].get("context-v1.jsonld") != context["sha256"]):
            raise InitializationError("ontology module inventory or module digest does not match its lock: " + module["id"])
    if neutral and ([(m["id"], m["version"]) for m in modules] != [("sys4ai-core", "1.0.0")]
                    or config["project_files"] != ["ONTOLOGY/modules/project/project.jsonld"]
                    or config["binding_files"] != ["ONTOLOGY/bindings/bindings.jsonld"]):
        raise InitializationError("template ontology selects non-neutral project modules")
    for key in ("project_files", "binding_files"):
        if not isinstance(config[key], list) or not config[key]:
            raise InitializationError("ontology lacks its declared local " + key)
        for name in config[key]:
            prefix = "ONTOLOGY/modules/project/" if key == "project_files" else "ONTOLOGY/bindings/"
            endings = (".jsonld",) if key == "project_files" else (".jsonld", ".json")
            if not isinstance(name, str) or not name.startswith(prefix) or not name.endswith(endings):
                raise InitializationError("ontology canonical file path is incompatible")
            destination_file(root, name)
            if name not in files:
                raise InitializationError("ontology canonical file is missing: " + name)
            graph = unique_json(files[name])
            if (not isinstance(graph, dict) or set(graph) != {"@context", "@graph"}
                    or graph["@context"] != context["path"] or not isinstance(graph["@graph"], list)
                    or neutral and graph["@graph"] != []):
                raise InitializationError("ontology canonical graph is incompatible or non-neutral: " + name)
    if not isinstance(config["source_allowlist"], list):
        raise InitializationError("ontology source allowlist is incompatible")
    for name in config["source_allowlist"]:
        destination_file(root, name)
        if any(char in name for char in "*?[]"):
            raise InitializationError("ontology source allowlist must contain exact paths")
    if not isinstance(config.get("competency_files", []), list):
        raise InitializationError("ontology competency_files must be an array")
    for name in config.get("competency_files", []):
        if not isinstance(name, str) or not name.startswith("ONTOLOGY/modules/project/") or not name.endswith(".json"):
            raise InitializationError("ontology competency path is incompatible")
        destination_file(root, name)
        if name not in files:
            raise InitializationError("ontology competency file is missing: " + name)
        unique_json(files[name])
    if neutral and config.get("competency_files", []) != []:
        raise InitializationError("template ontology contains project competency data")
    if neutral:
        allowed = {name for name in ONTOLOGY_FILES if name.startswith("ONTOLOGY/")}
        if {name for name in files if name.startswith("ONTOLOGY/")} != allowed:
            raise InitializationError("template ontology contains undeclared canonical or generated data")
    retrieval = config["retrieval"]
    if (not isinstance(retrieval, dict) or set(retrieval) != {"default_hops", "max_hops", "default_limit", "max_limit", "max_context_bytes"}
            or any(type(value) is not int for value in retrieval.values())
            or not 0 <= retrieval["default_hops"] <= retrieval["max_hops"] <= 8
            or not 1 <= retrieval["default_limit"] <= retrieval["max_limit"] <= 100
            or not 1024 <= retrieval["max_context_bytes"] <= 32000):
        raise InitializationError("ontology retrieval settings exceed the release bounds")
    interfaces = {"ontology.py": {"main"}, "ontology_core.py": {"load_project"},
                  "ontology_modules.py": {"load_modules"}, "ontology_validate.py": {"validate_project"}}
    for name in ONTOLOGY_HELPERS:
        try:
            tree = ast.parse(files[name], filename=name)
            names = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
            if not interfaces.get(Path(name).name, set()) <= names:
                raise InitializationError("ontology helper lacks its static interface: " + name)
        except (SyntaxError, UnicodeError) as error:
            raise InitializationError("ontology helper is syntactically incompatible: " + name) from error
    return config


def validate_ontology_sources(template: Path, files: dict[str, bytes]) -> None:
    validate_ontology_static(template, files, neutral=True)


def specialize_ontology(raw: bytes, identity: dict[str, Any], files: dict[str, bytes], *,
                        destination: Path | None = None, owned_governance=frozenset()) -> bytes:
    config = unique_json(raw)
    config["project"] = {"id": identity["project_id"], "name": identity["project_name"],
        "purpose": identity["purpose"], "namespace": "urn:sys4ai:ontology:project:" + identity["project_id"] + ":", "root": "."}
    authority = []
    for name in ("SOUL.md", "AGENTS.md", "ROLE.md"):
        target = destination_file(destination, name) if destination is not None else None
        current = file_bytes(target) if target is not None and target.exists() and name not in owned_governance else files[name]
        authority.append({"path": name, "sha256": sha(current)})
    config["publication"] = {"enabled": True, "binding": {"actor_id": "/root",
        "scope": ["ONTOLOGY/modules/project", "ONTOLOGY/bindings"], "authority": authority}}
    return encoded(config)


def assess_ontology(destination: Path) -> dict[str, Any]:
    result = {"module_id": ONTOLOGY_MODULE, "read_only": True, "structural_readiness": "unavailable",
        "runtime": "not-exercised", "semantic_validation": "not-assessed", "source_freshness": "not-assessed", "inspector_execution": "none", "helper_code": "syntax-and-declarations-only", "director_binding": "not-assessed",
        "authorized_publication": "unavailable", "operation_grant_checked": False, "diagnostics": []}
    try:
        inventory = ontology_inventory(destination)
        files = {name: file_bytes(destination_file(destination, name)) for name, value in inventory.items() if value != "directory"}
        config = validate_ontology_static(destination, files, neutral=False)
        identity = unique_json(file_bytes(destination_file(destination, IDENTITY)))
        if config["project"] != {"id": identity["project_id"], "name": identity["project_name"], "purpose": identity["purpose"],
                                 "namespace": "urn:sys4ai:ontology:project:" + identity["project_id"] + ":", "root": "."}:
            raise InitializationError("ontology.yaml identity differs from the selected destination")
        result.update(structural_readiness="available", config_sha256=sha(files["ontology.yaml"]), project=config["project"], modules=config["modules"])
        publication = config["publication"]
        binding = publication.get("binding") if isinstance(publication, dict) else None
        if (not isinstance(publication, dict) or set(publication) != {"enabled", "binding"} or type(publication["enabled"]) is not bool):
            raise InitializationError("ontology publication configuration is incompatible")
        result["director_binding"] = "absent"
        result["publication_enabled"] = publication["enabled"]
        if binding is not None:
            if (not isinstance(binding, dict) or set(binding) != {"actor_id", "scope", "authority"} or not isinstance(binding["actor_id"], str) or not binding["actor_id"].strip()
                    or not isinstance(binding["scope"], list) or not binding["scope"]
                    or any(not isinstance(name, str) or name not in {"ONTOLOGY/modules/project", "ONTOLOGY/bindings"} for name in binding["scope"])
                    or not isinstance(binding["authority"], list) or len(binding["authority"]) != 3
                    or {ref.get("path") for ref in binding["authority"] if isinstance(ref, dict)} != {"SOUL.md", "AGENTS.md", "ROLE.md"}):
                raise InitializationError("ontology publication binding is incompatible or outside ontology scope")
            result["director_binding"] = "current"
            result["publication_scope"] = list(binding["scope"])
            result["publication_actor"] = binding["actor_id"]
            for ref in binding["authority"]:
                if set(ref) != {"path", "sha256"} or sha(file_bytes(destination_file(destination, ref["path"]))) != ref["sha256"]:
                    result["director_binding"] = "stale"
                    result["diagnostics"].append({"code": "stale_authority", "path": ref["path"], "message": "Current governance differs from the preserved ontology binding."})
            if publication["enabled"] and result["director_binding"] == "current":
                result["authorized_publication"] = "requires-current-operation-grant"
        result["message"] = "Static configuration, import integrity and local binding assessed. Run ontology health for current semantic and source readiness."
    except (InitializationError, OSError, ValueError, KeyError, TypeError) as error:
        result["structural_readiness"] = "unavailable"
        result["diagnostics"].append({"code": "ontology_unavailable", "path": "ontology.yaml or installed ontology package",
            "message": str(error) if isinstance(error, InitializationError) else "Required ontology configuration or resources are incompatible."})
    return result


def validate_ontology_preservation(record, destination, source_adoptions):
    if record["setup_contract"] not in ONTOLOGY_CONTRACTS:
        if "preserved_ontology" in record or "current_ontology" in record:
            raise InitializationError("older setup receipt contains a later ontology decision")
        return
    inventory = record.get("preserved_ontology")
    if not isinstance(inventory, dict):
        raise InitializationError("ontology setup receipt lacks complete preservation evidence")
    for name, digest in inventory.items():
        if (not isinstance(name, str) or not ontology_path(name) or not isinstance(digest, str)
                or digest != "directory" and not SHA256.fullmatch(digest)
                or name not in {"ontology.yaml", *ONTOLOGY_TREES} and inventory.get(Path(name).parent.as_posix()) != "directory"):
            raise InitializationError("invalid ontology preservation inventory")
        safe(destination / name)
        if Path(name).as_posix() != name or ".." in Path(name).parts or Path(name).is_absolute():
            raise InitializationError("invalid ontology preservation path")
    if inventory:
        original = {entry["destination"]: entry["source_sha256"] for entry in record["sources"] if ontology_path(entry["destination"])}
        pristine = inventory == ontology_files_inventory(original)
        for name, (adoption, digest) in source_adoptions.items():
            if not ontology_path(name):
                continue
            expected = "preserved-project-owned" if name in inventory else "skipped-existing-package"
            if not (pristine and name == "ontology.yaml" and adoption == "specialized") and (adoption != expected or digest != inventory.get(name)):
                raise InitializationError("ontology source adoption mixes an existing whole installation")


def check_ontology_adoption(destination: Path, record: dict[str, Any]) -> None:
    if record["setup_contract"] not in ONTOLOGY_CONTRACTS:
        return
    expected = dict(record["preserved_ontology"])
    owned = {name: digest for name, digest in record["owned_files"].items() if ontology_path(name)}
    for name, digest in ontology_files_inventory(owned).items():
        target = safe(destination / name)
        if target.exists():
            if digest == "directory":
                expected[name] = digest
            else:
                current = sha(file_bytes(target))
                if current not in {digest, record.get("recovery_before", {}).get(name)}:
                    raise InitializationError("ontology file changed during asset adoption: " + name)
                expected[name] = current
    if ontology_inventory(destination) != expected:
        raise InitializationError("ontology installation changed during asset adoption")


def memory_capture_notice(destination: Path) -> dict[str, Any]:
    """Describe the installed state; never enable a preserved configuration here."""
    result = {"automatic_capture": None, "status": "unavailable", "opt_out_question": None}
    if not (destination / "memory.yaml").exists():
        return {**result, "status": "not-installed", "message": "Project memory is not installed by this setup edition."}
    try:
        raw = file_bytes(destination_file(destination, "memory.yaml"))
        config = unique_json(raw)
        files = {name: file_bytes(destination_file(destination, name)) for name in MEMORY_HELPER_FILES}
        check_memory_inspectors(files, preserved=True)
        validate_memory_config(config, files, allow_template=False)
        enabled = config["integration"]["automatic_capture"]
        result.update(automatic_capture=enabled, config_sha256=sha(raw))
        if enabled:
            if not destination_file(destination, ".agents/skills/memory/scripts/memory_capture.py").is_file():
                raise InitializationError("the preserved memory package lacks automatic capture support")
            director = config["publication"]["director"]
            if not director or any(sha(file_bytes(destination_file(destination, ref["path"]))) != ref["sha256"]
                                   for ref in director["authority"]):
                raise InitializationError("project memory publication authority needs current local binding")
        result.update(status="on" if enabled else "off",
                      message="Memory automatic capture is " + ("on." if enabled else "off; your existing preference was preserved."),
                      opt_out_question="Would you like to turn it off?" if enabled else None)
    except (InitializationError, OSError, ValueError, KeyError, TypeError):
        result["message"] = "Existing project memory was preserved; automatic capture readiness could not be verified. Inspect its configuration and installed memory package."
    return result


def assess_learning(destination: Path) -> dict[str, Any]:
    """Report local capability separately from grants and backend readiness."""
    result = {"module_id": LEARNING_MODULE, "read_only": True,
              "manual_review": "unavailable", "shared_automatic_checkpoint": "unavailable",
              "authorized_publication": "unavailable", "optional_backend": "not-assessed",
              "automatic_capture": None, "director_binding": "not-assessed",
              "operation_grant_checked": False, "diagnostics": []}
    try:
        raw = file_bytes(destination_file(destination, LEARNING_RESOLVER))
        with learning_resolver(raw) as helper:
            resolution = helper.resolve(destination)
        result["resolution"] = resolution
        result["diagnostics"].extend(resolution["errors"])
        if resolution["capabilities"]["manual_review"]:
            result["manual_review"] = "available"
        config_raw = file_bytes(destination_file(destination, "memory.yaml"))
        config = unique_json(config_raw)
        files = {name: file_bytes(destination_file(destination, name)) for name in MEMORY_HELPER_FILES}
        check_memory_inspectors(files, preserved=True)
        validate_memory_config(config, files, allow_template=False)
        identity = unique_json(file_bytes(destination_file(destination, IDENTITY)))
        if config["project"] != {"id": identity["project_id"], "name": identity["project_name"], "root": "."}:
            raise InitializationError("memory.yaml identity does not match this destination")
        result["config_sha256"] = sha(config_raw)
        result["automatic_capture"] = config["integration"]["automatic_capture"]
        if not result["automatic_capture"]:
            result["shared_automatic_checkpoint"] = "off"
        elif resolution["capabilities"]["shared_automatic_checkpoint"]:
            result["shared_automatic_checkpoint"] = "available"
        result["optional_backend"] = "configured-not-verified" if config["backend"]["enabled"] else "disabled"
        director = config["publication"]["director"]
        result["director_binding"] = "absent"
        if director:
            result["publication_scope"] = list(director["scope"])
            result["director_binding"] = "unverified"
            for ref in director["authority"]:
                if sha(file_bytes(destination_file(destination, ref["path"]))) != ref["sha256"]:
                    result["director_binding"] = "stale"
                    result["diagnostics"].append({"path": ref["path"], "code": "stale_authority",
                                                   "message": "Preserved publication authority no longer matches this governing file."})
            if result["director_binding"] == "unverified":
                result["director_binding"] = "current"
            if result["director_binding"] == "current" and resolution["memory"]["interface_compatible"]:
                result["authorized_publication"] = "requires-current-operation-grant"
        result["publication_requirement"] = "The memory helper must verify the exact operation grant, actor and current Task ownership before each write."
    except (InitializationError, OSError, ValueError, KeyError, TypeError) as error:
        result["manual_review"] = "unavailable"
        result["shared_automatic_checkpoint"] = "unavailable"
        result["diagnostics"].append({"path": "memory.yaml or installed learning/memory package",
                                       "code": "capability_unavailable",
                                       "message": str(error) if isinstance(error, InitializationError) else "Required local configuration or resource could not be verified."})
    return result


def verify_project(destination: Path, record: dict[str, Any], *, allow_module_gaps: bool = False) -> dict[str, str]:
    """Observe current adopted files without resetting normal project edits."""
    validate_record(record, destination, record["identity"])
    role_root, current_paths, case_evidence = record_role_paths(record, destination)
    current = {}
    current_owned = module_owned_files(record)
    for name in sorted(current_owned.keys() | record["preserved_files"].keys()):
        current_name = current_paths.get(name, name)
        target = destination_file(destination, current_name)
        if not target.is_file():
            if allow_module_gaps and (ontology_path(current_name) or any(current_name.startswith(root + "/") for root in MODULE_PACKAGES)):
                continue
            raise InitializationError(f"project setup file is missing: {name}")
        current[current_name] = sha(file_bytes(target))
    identity = record["identity"]
    observed, saved = selected_identity(destination, **{key: identity[key] for key in
        ("project_id", "project_name", "purpose")}, relative=identity["relative_path"])
    if saved is None or observed != identity:
        raise InitializationError("project identity changed during setup")
    if record["setup_contract"] != LEGACY_CONTRACT:
        current_contract = SETUP_CONTRACT if role_root == "Roles" else LOWERCASE_CONTRACT
        if file_bytes(destination / role_root / "INDEX.md") != planned_role_index(destination, {}, {}, contract=current_contract):
            raise InitializationError("project role index is stale; preserve role edits and explicitly reindex")
    if case_evidence is not None:
        record["role_case_transition"] = case_evidence
    if record["setup_contract"] in LICENSE_CONTRACTS:
        record["current_licenses"] = license_inventory(destination)
    if record["setup_contract"] in MEMORY_CONTRACTS:
        record["current_memory"] = memory_inventory(destination)
    if record["setup_contract"] in LEARNING_CONTRACTS:
        record["current_learning"] = {name: digest for root in LEARNING_TREES for name, digest in package_inventory(destination, root).items()}
    if record["setup_contract"] in ONTOLOGY_CONTRACTS:
        record["current_ontology"] = ontology_inventory(destination)
    return current


MODULE_PACKAGES = (*LEARNING_TREES, ".agents/skills/memory", MEMORY_CONTRACT_ROOT, "MEMORY")
REFRESH_PACKAGES = {".agents/skills/memory", MEMORY_CONTRACT_ROOT}
MODULE_STAGES = ["assets", "verification"]
BASE_IMMUTABLE = ("schema_version", "setup_contract", "operation_id", "identity", "project_root",
                  "sources", "owned_files", "preserved_files", "preserved_memory", "preserved_licenses", "preserved_learning", "preserved_ontology", "created_at")
MODULE_FROZEN = ("module_id", "module_version", "project_root", "identity", "base_receipt",
                 "refresh_dependencies", "new_memory", "sources", "packages", "files", "preserved_files")


def module_packages(operation: dict[str, Any]) -> tuple[str, ...]:
    if isinstance(operation, dict) and operation.get("module_id") == CURATOR_MODULE:
        return CURATOR.PACKAGES
    if isinstance(operation, dict) and operation.get("module_id") == ADVANCED_MODULE:
        return ADVANCED.packages(operation)
    return ONTOLOGY_TREES if isinstance(operation, dict) and operation.get("module_id") == ONTOLOGY_MODULE else MODULE_PACKAGES


def module_frozen(operation: dict[str, Any]) -> tuple[str, ...]:
    if isinstance(operation, dict) and operation.get("module_id") == CURATOR_MODULE:
        return MODULE_FROZEN + CURATOR.FROZEN
    if isinstance(operation, dict) and operation.get("module_id") == ADVANCED_MODULE:
        return MODULE_FROZEN + ADVANCED.FROZEN
    return MODULE_FROZEN + (("refresh_modules", "new_ontology") if isinstance(operation, dict) and operation.get("module_id") == ONTOLOGY_MODULE else ())


def ontology_source_files(depot: Path) -> dict[str, bytes]:
    original, _, _, _, _ = template_sources(depot)
    return {name: raw for name, raw in original.items() if ontology_path(name)}


def ontology_proposed_files(destination: Path, identity: dict[str, Any], original: dict[str, bytes], *, new_ontology: bool) -> dict[str, bytes]:
    proposed = dict(original)
    if new_ontology:
        proposed["ontology.yaml"] = specialize_ontology(original["ontology.yaml"], identity, original, destination=destination)
    else:
        target = destination_file(destination, "ontology.yaml")
        if target.exists():
            try:
                current = unique_json(file_bytes(target))
                config = unique_json(original["ontology.yaml"])
                # The selected package refresh updates imports, retaining existing
                # project settings and its authority rather than renewing grants.
                if isinstance(current, dict) and set(config) == set(current):
                    current["context"], current["modules"] = config["context"], config["modules"]
                    proposed["ontology.yaml"] = encoded(current)
            except (InitializationError, ValueError, TypeError):
                pass  # Preserved incompatible installation is never published.
    return proposed


def plan_ontology_adoption(depot: Path, destination: Path, record: dict[str, Any], previous_raw: bytes,
                          refresh_modules: list[str]) -> tuple[dict[str, Any], dict[str, bytes]]:
    before = ontology_inventory(destination)
    original = ontology_source_files(depot)
    proposed = ontology_proposed_files(destination, record["identity"], original, new_ontology=not bool(before))
    after = ontology_files_inventory(proposed)
    owned = {name: digest for name, digest in module_owned_files(record).items() if ontology_path(name)}
    owned_before = ontology_files_inventory(owned) if owned else {}
    decision, diagnostic = "adopted", None
    if before:
        decision = "preserved-package"
        if refresh_modules:
            if before == owned_before and owned:
                decision = "refreshed-owned-package"
            else:
                decision = "preserved-incompatible-refresh"
                diagnostic = {"code": "scoped_ontology_adoption_required", "path": "ontology.yaml and complete ontology installation",
                    "different_resources": sorted(name for name in before.keys() | owned_before.keys() if before.get(name) != owned_before.get(name)),
                    "message": "Preserved complete ontology installation: refresh requires every file and directory to match receipt-owned evidence. Customized, missing and incompatible content needs a separate reviewed adoption."}
        if decision.startswith("preserved"):
            after = dict(before)
    packages, changes, preserved = {}, {}, {}
    for root in ONTOLOGY_TREES:
        prior = {name: digest for name, digest in before.items() if name == root or name.startswith(root + "/")}
        final = {name: digest for name, digest in after.items() if name == root or name.startswith(root + "/")}
        if not decision.startswith("preserved") and any((prior[name] == "directory") != (final[name] == "directory") for name in prior.keys() & final.keys()):
            raise InitializationError("ontology package file/directory transition requires separate scoped adoption: " + root)
        packages[root] = {"decision": decision, "before": prior, "after": final, "diagnostic": diagnostic}
    if not decision.startswith("preserved"):
        changes = {name: {"before": before.get(name), "after": after.get(name)} for name in sorted(before.keys() | after.keys())
                   if before.get(name) != "directory" and after.get(name) != "directory"}
    for name in (IDENTITY, "SOUL.md", "AGENTS.md", "ROLE.md", "memory.yaml", "ontology.yaml"):
        target = destination_file(destination, name)
        if name not in changes and target.exists():
            preserved[name] = sha(file_bytes(target))
    sources = []
    for name, raw in sorted(original.items()):
        digest = after.get(name)
        adoption = ("specialized" if name == "ontology.yaml" else "adopted") if name in changes else "preserved-project-owned" if digest else "skipped-existing-package"
        sources.append({"source": TEMPLATE + "/" + name, "destination": name, "source_sha256": sha(raw),
            "source_version": "sha256:" + sha(raw), "destination_sha256": digest, "adoption": adoption})
    digest = sha(previous_raw)
    operation = {"schema_version": 1, "module_id": ONTOLOGY_MODULE,
        "module_version": unique_json(original[ONTOLOGY_ROOT + "/contract.json"])["module_version"],
        "operation_id": "module-adoption-" + uuid4().hex, "project_root": str(destination), "identity": deepcopy(record["identity"]),
        "base_receipt": {"path": "control_records/project-setup-history/" + digest + ".json", "sha256": digest},
        "refresh_dependencies": [], "new_memory": False, "refresh_modules": refresh_modules, "new_ontology": not bool(before),
        "sources": sources, "packages": packages, "files": changes, "preserved_files": preserved,
        "status": "partial", "completed_stages": [], "active_stage": "assets", "checks": [], "created_at": datetime.now(timezone.utc).isoformat()}
    operation["manifest_sha256"] = sha(encoded({key: operation[key] for key in module_frozen(operation)}))
    return operation, proposed


def package_inventory(destination: Path, root: str) -> dict[str, str]:
    target = safe(destination / root)
    if not target.exists():
        return {}
    if not target.is_dir():
        raise InitializationError("module package is not a directory: " + root)
    result = {}
    for path in (target, *sorted(target.rglob("*"))):
        safe(path)
        result[path.relative_to(destination).as_posix()] = "directory" if path.is_dir() else sha(file_bytes(path))
    return result


def inventory_from_files(root: str, files: dict[str, Any]) -> dict[str, str]:
    result = {root: "directory"}
    for name, value in files.items():
        if not name.startswith(root + "/"):
            continue
        result[name] = sha(value) if isinstance(value, bytes) else value
        parent = Path(name).parent
        while parent.as_posix() != root:
            result[parent.as_posix()] = "directory"
            parent = parent.parent
    return result


def check_learning_adoption(destination: Path, record: dict[str, Any]) -> None:
    if record["setup_contract"] not in LEARNING_CONTRACTS:
        return
    expected = dict(record["preserved_learning"])
    for root in LEARNING_TREES:
        planned = inventory_from_files(root, {name: digest for name, digest in record["owned_files"].items() if name.startswith(root + "/")})
        expected.update({name: digest for name, digest in planned.items() if digest == "directory" and safe(destination / name).is_dir()})
        published = {name: digest for name, digest in record["owned_files"].items()
                     if name.startswith(root + "/") and destination_file(destination, name).exists()}
        if published:
            expected.update(inventory_from_files(root, published))
    current = {name: digest for root in LEARNING_TREES for name, digest in package_inventory(destination, root).items()}
    if current != expected:
        raise InitializationError("project learning packages changed during asset adoption")


def module_owned_files(record: dict[str, Any]) -> dict[str, str]:
    owned = dict(record["owned_files"])
    for operation in record.get("module_adoptions", []):
        if operation["status"] == "completed":
            for name, change in operation["files"].items():
                if change["after"] is None:
                    owned.pop(name, None)
                else:
                    owned[name] = change["after"]
    return owned


def module_source_files(depot: Path, *, new_memory: bool) -> dict[str, bytes]:
    original, _, _, _, _ = template_sources(depot)
    selected = {name: raw for name, raw in original.items()
                if name == "memory.yaml" or any(name.startswith(root + "/") for root in MODULE_PACKAGES)}
    if new_memory:
        selected["AGENTS.md"] = original["AGENTS.md"]
    return selected


def module_proposed_files(destination: Path, identity: dict[str, Any], original: dict[str, bytes],
                          *, new_memory: bool) -> dict[str, bytes]:
    proposed = dict(original)
    if new_memory:
        governance = {name: file_bytes(destination_file(destination, name)) for name in ("SOUL.md", "AGENTS.md", "ROLE.md")}
        if not any(COMPLETION_REFERENCE.encode() in raw for raw in governance.values()):
            governance["AGENTS.md"] += completion_link()
        proposed["AGENTS.md"] = governance["AGENTS.md"]
        proposed["memory.yaml"] = specialize_memory(original["memory.yaml"], identity, {**original, **governance},
            automatic=True, destination=destination, owned_governance=frozenset(governance))
    return proposed


def plan_module_adoption(depot: Path, destination: Path, record: dict[str, Any], previous_raw: bytes,
                         refresh_dependencies: list[str]) -> tuple[dict[str, Any], dict[str, bytes]]:
    new_memory = not destination_file(destination, "memory.yaml").exists()
    original = module_source_files(depot, new_memory=new_memory)
    proposed = module_proposed_files(destination, record["identity"], original, new_memory=new_memory)
    owned = module_owned_files(record)
    packages, changes, preserved = {}, {}, {}
    for root in MODULE_PACKAGES:
        before = package_inventory(destination, root)
        source = {name: raw for name, raw in proposed.items() if name.startswith(root + "/")}
        after = inventory_from_files(root, source)
        type_changes = sorted(name for name in before.keys() & after.keys()
                              if (before[name] == "directory") != (after[name] == "directory"))
        if type_changes:
            raise InitializationError("module package file/directory transition requires separate scoped adoption: " + ", ".join(type_changes))
        decision, diagnostic = "adopted", None
        if before:
            decision = "preserved-package"
            if root in REFRESH_PACKAGES and "memory" in refresh_dependencies and before != after:
                owned_package = {name: digest for name, digest in owned.items() if name.startswith(root + "/")}
                expected_owned = inventory_from_files(root, owned_package) if owned_package else {}
                if owned_package and before == expected_owned:
                    decision = "refreshed-owned-package"
                else:
                    decision = "preserved-incompatible-refresh"
                    different = sorted(name for name in before.keys() | expected_owned.keys() if before.get(name) != expected_owned.get(name))
                    diagnostic = {"code": "scoped_dependency_adoption_required", "path": root,
                        "different_resources": different,
                        "message": "Preserved whole package: explicit refresh requires its complete unchanged receipt-owned inventory; review a separate scoped custom-package adoption."}
            if decision.startswith("preserved"):
                after = dict(before)
        packages[root] = {"decision": decision, "before": before, "after": after, "diagnostic": diagnostic}
        if not decision.startswith("preserved"):
            for name in sorted(before.keys() | after.keys()):
                if before.get(name) == "directory" or after.get(name) == "directory":
                    continue
                changes[name] = {"before": before.get(name), "after": after.get(name)}
    for name in (IDENTITY, "SOUL.md", "AGENTS.md", "ROLE.md", "memory.yaml"):
        target = destination_file(destination, name)
        present = file_bytes(target) if target.exists() else None
        if new_memory and name in {"AGENTS.md", "memory.yaml"} and present != proposed[name]:
            changes[name] = {"before": sha(present) if present is not None else None, "after": sha(proposed[name])}
        elif present is not None:
            preserved[name] = sha(present)
    sources = []
    for name, raw in sorted(original.items()):
        if name in changes:
            after = changes[name]["after"]
            adoption = "specialized" if name in {"AGENTS.md", "memory.yaml"} else "adopted"
        else:
            root = next((root for root in MODULE_PACKAGES if name.startswith(root + "/")), None)
            after = packages[root]["after"].get(name) if root else preserved.get(name)
            adoption = "preserved-project-owned" if after else "skipped-existing-package"
        sources.append({"source": TEMPLATE + "/" + name, "destination": name, "source_sha256": sha(raw),
                        "source_version": "sha256:" + sha(raw), "destination_sha256": after, "adoption": adoption})
    digest = sha(previous_raw)
    operation = {"schema_version": 1, "module_id": LEARNING_MODULE,
        "module_version": unique_json(original[LEARNING_ROOT + "/contract.json"])["module_version"],
        "operation_id": "module-adoption-" + uuid4().hex, "project_root": str(destination), "identity": deepcopy(record["identity"]),
        "base_receipt": {"path": "control_records/project-setup-history/" + digest + ".json", "sha256": digest},
        "refresh_dependencies": refresh_dependencies, "new_memory": new_memory,
        "sources": sources, "packages": packages, "files": changes, "preserved_files": preserved,
        "status": "partial", "completed_stages": [], "active_stage": "assets", "checks": [],
        "created_at": datetime.now(timezone.utc).isoformat()}
    operation["manifest_sha256"] = sha(encoded({key: operation[key] for key in MODULE_FROZEN}))
    return operation, proposed


def validate_module_adoptions(record: dict[str, Any], destination: Path) -> None:
    operations = record.get("module_adoptions", [])
    if not isinstance(operations, list) or len(operations) > 100:
        raise InitializationError("invalid module adoption collection")
    seen = set()
    for index, operation in enumerate(operations):
        required = {"schema_version", "operation_id", "manifest_sha256", "status", "completed_stages", "active_stage", "checks", "created_at", *module_frozen(operation)}
        optional = {"capabilities", "current_files", "verified_at", "recovery", "rerun", "static_health"}
        if (not isinstance(operation, dict) or not required <= operation.keys() or not operation.keys() <= required | optional
                or type(operation["schema_version"]) is not int or operation["schema_version"] != 1
                or any(not isinstance(operation[name], str) for name in ("module_id", "module_version", "project_root", "operation_id", "manifest_sha256", "status", "created_at"))
                or operation["active_stage"] is not None and not isinstance(operation["active_stage"], str)
                or not isinstance(operation["checks"], list)
                or operation["module_id"] not in {LEARNING_MODULE, ONTOLOGY_MODULE, ADVANCED_MODULE, CURATOR_MODULE}
                or operation["module_version"] != ("2.0.0" if operation["module_id"] == ADVANCED_MODULE else "1.0.0")
                or operation["project_root"] != str(destination) or operation["identity"] != record["identity"]
                or not isinstance(operation["operation_id"], str)
                or not re.fullmatch(r"module-adoption-[0-9a-f]{32}", operation["operation_id"])
                or operation["operation_id"] in seen or operation["refresh_dependencies"] not in ([], ["memory"])
                or operation["module_id"] == ONTOLOGY_MODULE and (operation["refresh_dependencies"] != [] or operation["new_memory"] is not False
                    or operation["refresh_modules"] not in ([], [ONTOLOGY_MODULE]) or type(operation["new_ontology"]) is not bool)
                or operation["module_id"] == ADVANCED_MODULE and (operation["refresh_dependencies"] != [] or operation["new_memory"] is not False
                    or type(operation["new_ontology"]) is not bool or type(operation["new_advanced"]) is not bool)
                or operation["module_id"] == CURATOR_MODULE and (operation["refresh_dependencies"] != [] or operation["new_memory"] is not False)
                or type(operation["new_memory"]) is not bool
                or operation["manifest_sha256"] != sha(encoded({key: operation[key] for key in module_frozen(operation)}))):
            raise InitializationError("invalid module adoption identity or frozen manifest")
        seen.add(operation["operation_id"])
        stages = operation["completed_stages"]
        if (operation["status"] not in {"partial", "completed"} or not isinstance(stages, list)
                or stages != MODULE_STAGES[:len(stages)] or operation["active_stage"] not in {*MODULE_STAGES, None}
                or operation["status"] == "completed" and (stages != MODULE_STAGES or operation["active_stage"] is not None)
                or operation["status"] == "partial" and index != len(operations) - 1):
            raise InitializationError("invalid module adoption lifecycle")
        archive = operation["base_receipt"]
        if (not isinstance(archive, dict) or set(archive) != {"path", "sha256"}
                or not isinstance(archive["sha256"], str) or not SHA256.fullmatch(archive["sha256"])
                or archive["path"] != "control_records/project-setup-history/" + archive["sha256"] + ".json"):
            raise InitializationError("invalid module base receipt provenance")
        raw = file_bytes(destination_file(destination, archive["path"]))
        old = unique_json(raw)
        if not isinstance(old, dict) or sha(raw) != archive["sha256"] or any(old.get(key) != record.get(key) for key in BASE_IMMUTABLE):
            raise InitializationError("module adoption changed its original base setup evidence")
        old_operations = old.get("module_adoptions", [])
        if (not isinstance(old_operations, list) or len(old_operations) != index
                or any(not isinstance(prior, dict) or prior.get("operation_id") != operations[position]["operation_id"]
                       or prior.get("manifest_sha256") != operations[position]["manifest_sha256"]
                       or prior.get("status") != "completed" for position, prior in enumerate(old_operations))):
            raise InitializationError("module adoption lacks its exact earlier operation provenance")
        previous_owned = module_owned_files(old)
        if not isinstance(operation["packages"], dict) or set(operation["packages"]) != set(module_packages(operation)):
            raise InitializationError("invalid module package scope")
        for root, package in operation["packages"].items():
            if (not isinstance(package, dict) or set(package) != {"decision", "before", "after", "diagnostic"}
                    or not isinstance(package["decision"], str)
                    or package["diagnostic"] is not None and not isinstance(package["diagnostic"], dict)
                    or package["decision"] not in {"adopted", "preserved-package", "refreshed-owned-package", "preserved-incompatible-refresh"}
                    or package["decision"] == "refreshed-owned-package" and (operation["module_id"] == LEARNING_MODULE and (root not in REFRESH_PACKAGES or operation["refresh_dependencies"] != ["memory"])
                         or operation["module_id"] == ONTOLOGY_MODULE and operation["refresh_modules"] != [ONTOLOGY_MODULE])):
                raise InitializationError("invalid module package adoption decision")
            for phase in ("before", "after"):
                inventory = package[phase]
                if not isinstance(inventory, dict):
                    raise InitializationError("invalid module package inventory")
                for name, digest in inventory.items():
                    if (not isinstance(name, str) or name != root and not name.startswith(root + "/")
                            or not isinstance(digest, str) or digest != "directory" and not SHA256.fullmatch(digest)
                            or Path(name).as_posix() != name or ".." in Path(name).parts):
                        raise InitializationError("invalid module package path or digest")
                    if name != root and inventory.get(Path(name).parent.as_posix()) != "directory":
                        raise InitializationError("module package inventory lacks parent evidence")
                    safe(destination / name)
                if inventory and inventory.get(root) != "directory":
                    raise InitializationError("module package lacks its directory evidence")
            if package["decision"].startswith("preserved") and package["before"] != package["after"]:
                raise InitializationError("module preservation changed a whole package")
            if package["decision"] == "adopted" and package["before"]:
                raise InitializationError("module adoption cannot relabel an existing package as missing")
            if package["decision"] == "refreshed-owned-package":
                owned_package = {name: digest for name, digest in previous_owned.items() if name.startswith(root + "/")}
                expected_owned = inventory_from_files(root, owned_package) if owned_package else {}
                if not owned_package or package["before"] != expected_owned:
                    raise InitializationError("module refresh lacks complete prior receipt ownership")
        if not isinstance(operation["files"], dict) or not isinstance(operation["preserved_files"], dict):
            raise InitializationError("invalid module target inventory")
        for name, change in operation["files"].items():
            if not isinstance(name, str):
                raise InitializationError("invalid module target path")
            allowed = any(name.startswith(root + "/") for root in module_packages(operation))
            if not allowed and not (operation["new_memory"] and name in {"AGENTS.md", "memory.yaml"} or operation["module_id"] == ONTOLOGY_MODULE and name == "ontology.yaml"
                    or operation["module_id"] == CURATOR_MODULE and name in CURATOR.SPECIAL_FILES
                    or operation["module_id"] == ADVANCED_MODULE and (name == ADVANCED.TOOL or name == "ontology.yaml" and operation["new_ontology"] or name == ADVANCED.CONFIG and operation["new_advanced"])):
                raise InitializationError("module adoption target is outside its selected scope")
            destination_file(destination, name)
            if (not isinstance(change, dict) or set(change) != {"before", "after"}
                    or any(value is not None and (not isinstance(value, str) or not SHA256.fullmatch(value)) for value in change.values())
                    or change["before"] is None and change["after"] is None):
                raise InitializationError("invalid module before/after evidence")
        allowed_preserved = {IDENTITY, "SOUL.md", "AGENTS.md", "ROLE.md", "memory.yaml"} | ({"ontology.yaml"} if operation["module_id"] == ONTOLOGY_MODULE else set()) | ({"ontology.yaml", ADVANCED.CONFIG, ADVANCED.TOOL} if operation["module_id"] == ADVANCED_MODULE else set())
        if operation["module_id"] == CURATOR_MODULE:
            allowed_preserved |= {"ontology.yaml", "ontology-advanced.yaml", *CURATOR.SPECIAL_FILES}
        for name, digest in operation["preserved_files"].items():
            if name not in allowed_preserved or not isinstance(digest, str) or not SHA256.fullmatch(digest) or name in operation["files"]:
                raise InitializationError("invalid module preserved governing file")
            destination_file(destination, name)
        if not {IDENTITY, "SOUL.md", "ROLE.md"} <= operation["preserved_files"].keys():
            raise InitializationError("module adoption lacks frozen project identity and governance")
        if operation["new_memory"] and (operation["files"].get("memory.yaml", {}).get("before", "absent") is not None
                                        or operation["files"].get("memory.yaml", {}).get("after") is None):
            raise InitializationError("new memory binding lacks a missing-before configuration")
        sources = operation["sources"]
        if not isinstance(sources, list) or not sources:
            raise InitializationError("module adoption lacks source evidence")
        source_names = set()
        for source in sources:
            name = source.get("destination") if isinstance(source, dict) else None
            if (not isinstance(name, str) or name in source_names or source.get("source") != TEMPLATE + "/" + name
                    or not (operation["module_id"] == LEARNING_MODULE and (name == "memory.yaml" or operation["new_memory"] and name == "AGENTS.md")
                            or operation["module_id"] == ONTOLOGY_MODULE and name == "ontology.yaml"
                            or operation["module_id"] == ADVANCED_MODULE and name in ADVANCED.SPECIAL_FILES
                            or operation["module_id"] == CURATOR_MODULE and name in CURATOR.SPECIAL_FILES
                            or any(name.startswith(root + "/") for root in module_packages(operation)))
                    or not isinstance(source.get("source_sha256"), str) or not SHA256.fullmatch(source["source_sha256"])
                    or source.get("source_version") != "sha256:" + source["source_sha256"]):
                raise InitializationError("invalid nested module source provenance")
            source_names.add(name)
            destination_file(destination, name)
            root = next((root for root in module_packages(operation) if name.startswith(root + "/")), None)
            after = (operation["files"][name]["after"] if name in operation["files"] else
                     operation["packages"][root]["after"].get(name) if root else operation["preserved_files"].get(name))
            adoption = ("specialized" if name in {"memory.yaml", "AGENTS.md", "ontology.yaml", ADVANCED.CONFIG, CURATOR.CONFIG, "Roles/INDEX.md"} else "adopted") if name in operation["files"] else "preserved-project-owned" if after else "skipped-existing-package"
            if source.get("destination_sha256") != after or source.get("adoption") != adoption:
                raise InitializationError("module source and target decisions disagree")
            if adoption == "adopted" and source["source_sha256"] != after:
                raise InitializationError("module adopted bytes differ from their frozen source")
        required_sources = (CURATOR.STARTERS | CURATOR.RESOURCES if operation["module_id"] == CURATOR_MODULE else
                            ONTOLOGY_FILES | ONTOLOGY_SKILL_RESOURCES if operation["module_id"] == ONTOLOGY_MODULE else
                            ADVANCED.STARTERS | ADVANCED.RESOURCES | (ONTOLOGY_FILES if operation["new_ontology"] else ONTOLOGY_REFERENCE_FILES) if operation["module_id"] == ADVANCED_MODULE else
                            LEARNING_FILES | {LEARNING_RESOLVER, "memory.yaml"})
        if not required_sources <= source_names:
            raise InitializationError("module adoption omits required source evidence")
        for root, package in operation["packages"].items():
            selected = {name for name in package["before"].keys() | package["after"].keys()
                        if package["before"].get(name) != "directory" and package["after"].get(name) != "directory"}
            actual = {name for name in operation["files"] if name.startswith(root + "/")}
            if package["decision"].startswith("preserved"):
                if actual:
                    raise InitializationError("module adoption writes a preserved package")
            elif actual != selected or any(operation["files"][name] != {"before": package["before"].get(name), "after": package["after"].get(name)} for name in actual):
                raise InitializationError("module package and target inventories disagree")
            if not {name for name, digest in package["after"].items() if digest != "directory" and not package["decision"].startswith("preserved")} <= source_names:
                raise InitializationError("module adopted package omits source provenance")

        if operation["module_id"] == ONTOLOGY_MODULE:
            decisions = {package["decision"] for package in operation["packages"].values()}
            if len(decisions) != 1:
                raise InitializationError("ontology adoption mixes preserved and replaced packages")
            config_change = operation["files"].get("ontology.yaml")
            if any(item.startswith("preserved") for item in decisions) and config_change is not None:
                raise InitializationError("ontology adoption writes preserved configuration")
            if not any(item.startswith("preserved") for item in decisions) and config_change is None:
                raise InitializationError("ontology adoption omits its configuration decision")
            if operation["new_ontology"] and (decisions != {"adopted"} or config_change["before"] is not None):
                raise InitializationError("new ontology installation lacks missing-before evidence")
            if decisions == {"refreshed-owned-package"} and ("ontology.yaml" not in previous_owned or config_change["before"] != previous_owned["ontology.yaml"]):
                raise InitializationError("ontology refresh lacks exact prior configuration ownership")
        if operation["module_id"] == ADVANCED_MODULE:
            _advanced("validate_operation", destination, operation)
        if operation["module_id"] == CURATOR_MODULE:
            _curator("validate_operation", destination, operation)


def check_module_state(destination: Path, operation: dict[str, Any], *, complete: bool = False) -> None:
    if operation["module_id"] == CURATOR_MODULE:
        _curator("check_protected", destination, operation)
    if operation["module_id"] == ADVANCED_MODULE:
        _advanced("check_protected", destination, operation)
    for name, digest in operation["preserved_files"].items():
        if sha(file_bytes(destination_file(destination, name))) != digest:
            raise InitializationError("preserved module input changed: " + name)
    for name, change in operation["files"].items():
        target = destination_file(destination, name)
        current = sha(file_bytes(target)) if target.exists() else None
        if current not in ({change["after"]} if complete else {change["before"], change["after"]}):
            raise InitializationError("module adoption target changed: " + name)
    for root, package in operation["packages"].items():
        current = package_inventory(destination, root)
        if complete or package["decision"].startswith("preserved"):
            if current != package["after"]:
                raise InitializationError("module package changed during adoption: " + root)
        else:
            possible = package["before"].keys() | package["after"].keys()
            if not current.keys() <= possible or any(value not in {package["before"].get(name), package["after"].get(name)} for name, value in current.items()):
                raise InitializationError("module package gained conflicting content: " + root)


def check_module_sources(depot: Path, operation: dict[str, Any]) -> dict[str, bytes]:
    original = (_curator("selected_source_files", depot, operation) if operation["module_id"] == CURATOR_MODULE else
                ontology_source_files(depot) if operation["module_id"] == ONTOLOGY_MODULE else
                _advanced("selected_source_files", depot, operation) if operation["module_id"] == ADVANCED_MODULE else
                module_source_files(depot, new_memory=operation["new_memory"]))
    expected = {entry["destination"]: entry["source_sha256"] for entry in operation["sources"]}
    if {name: sha(raw) for name, raw in original.items()} != expected:
        raise InitializationError("frozen module Template sources changed; restore the reviewed edition before recovery")
    return original


def verify_module_current(destination: Path, operation: dict[str, Any], record: dict[str, Any] | None = None) -> None:
    operation["current_files"] = {name: digest for root in module_packages(operation) for name, digest in package_inventory(destination, root).items()}
    operation["capabilities"] = (_curator("assess", destination) if operation["module_id"] == CURATOR_MODULE else
                                 assess_ontology(destination) if operation["module_id"] == ONTOLOGY_MODULE else
                                 _advanced("assess", destination) if operation["module_id"] == ADVANCED_MODULE else assess_learning(destination))
    operation["checks"] = [{"check": name, "outcome": "passed"} for name in ("module-manifest", "current-project-identity")]
    if record is not None:
        _static("apply", destination, record, operation=operation)
    operation["verified_at"] = datetime.now(timezone.utc).isoformat()


def run_module_adoption(depot: Path, destination: Path, record: dict[str, Any], previous_raw: bytes,
                         refresh_dependencies: list[str], *, module_id: str = LEARNING_MODULE, refresh_modules: list[str] | None = None) -> dict[str, Any]:
    refresh_modules = refresh_modules or []
    if record["status"] != "completed" or record["completed_stages"] != STAGES:
        raise InitializationError("finish the incomplete base setup before selected module adoption")
    pending = [op for op in record.get("module_adoptions", []) if op["status"] != "completed"]
    if pending and (pending[0]["module_id"] != module_id or pending[0]["refresh_dependencies"] != refresh_dependencies
                    or pending[0].get("refresh_modules", []) != refresh_modules):
        raise InitializationError("resume the exact pending module request and dependency selection")
    matches = [op for op in record.get("module_adoptions", []) if op["module_id"] == module_id
               and (module_id == ONTOLOGY_MODULE and not refresh_modules or op["refresh_dependencies"] == refresh_dependencies and op.get("refresh_modules", []) == refresh_modules)]
    operation = pending[0] if pending else matches[-1] if matches else None
    record_path = destination_file(destination, RECORD)
    lock = depot / "depot" / (".initialize-" + sha(record["identity"]["relative_path"].encode())[:16] + ".lock")
    with exclusive(lock), ExitStack() as guard:
        if file_bytes(record_path) != previous_raw:
            raise InitializationError("setup receipt changed before module adoption")
        template_locked = False
        if (module_id == ONTOLOGY_MODULE and refresh_modules or module_id == ADVANCED_MODULE) and operation is not None and operation["status"] == "completed":
            guard.enter_context(template_read_lock(depot))
            template_locked = True
            selected_sources = {name: sha(raw) for name, raw in (ontology_source_files(depot) if module_id == ONTOLOGY_MODULE else _advanced("selected_source_files", depot, operation)).items()}
            if selected_sources != {entry["destination"]: entry["source_sha256"] for entry in operation["sources"]}:
                operation = None
        if operation is None or operation["status"] != "completed":
            if not template_locked:
                guard.enter_context(template_read_lock(depot))
            if operation is None:
                verify_project(destination, deepcopy(record), allow_module_gaps=True)
                original, _, _, _, _ = template_sources(depot)
                if module_id == LEARNING_MODULE:
                    check_existing_role_layout(destination, original[ROLE_HELPER])
                operation, proposed = (_curator("plan", depot, destination, record, previous_raw) if module_id == CURATOR_MODULE else
                                       plan_ontology_adoption(depot, destination, record, previous_raw, refresh_modules)
                                       if module_id == ONTOLOGY_MODULE else
                                       _advanced("plan", depot, destination, record, previous_raw) if module_id == ADVANCED_MODULE else
                                       plan_module_adoption(depot, destination, record, previous_raw, refresh_dependencies))
                record.setdefault("module_adoptions", []).append(operation)
            else:
                proposed = (_curator("proposed_files", destination, record["identity"], check_module_sources(depot, operation), new_curator_files=operation["new_curator_files"]) if module_id == CURATOR_MODULE else
                            ontology_proposed_files(destination, record["identity"], check_module_sources(depot, operation), new_ontology=operation["new_ontology"])
                            if module_id == ONTOLOGY_MODULE else
                            _advanced("proposed_files", destination, record["identity"], check_module_sources(depot, operation), new_ontology=operation["new_ontology"], new_advanced=operation["new_advanced"]) if module_id == ADVANCED_MODULE else
                            module_proposed_files(destination, record["identity"], check_module_sources(depot, operation), new_memory=operation["new_memory"]))
            check_module_sources(depot, operation)
            check_module_state(destination, operation)
            for name, change in operation["files"].items():
                if change["after"] is not None and (name not in proposed or sha(proposed[name]) != change["after"]):
                    raise InitializationError("module recovery no longer produces its frozen after bytes")
        archived = archive_record(destination, previous_raw)
        if archived not in record.setdefault("history", []):
            record["history"].append(archived)
        validate_module_adoptions(record, destination)
        current_raw = previous_raw

        def checkpoint() -> None:
            nonlocal current_raw
            raw = encoded(record)
            atomic_write(record_path, raw, current_raw, mode=0o600)
            current_raw = raw

        try:
            if operation["status"] == "completed":
                verify_project(destination, deepcopy(record), allow_module_gaps=True)
                verify_module_current(destination, operation, record)
                operation["rerun"] = "verified-current-module-without-refresh"
                checkpoint()
                return record
            checkpoint()
            operation["active_stage"] = "assets"
            if "assets" not in operation["completed_stages"]:
                for name, change in operation["files"].items():
                    target = destination_file(destination, name)
                    current = file_bytes(target) if target.exists() else None
                    current_digest = sha(current) if current is not None else None
                    if current_digest == change["after"]:
                        continue
                    if current_digest != change["before"]:
                        raise InitializationError("module adoption target changed before publication: " + name)
                    if change["after"] is None:
                        _ontology_checkpoint(targets=False)
                        target.unlink()
                    else:
                        atomic_write(target, proposed[name], current)
                for package in operation["packages"].values():
                    for name in sorted(package["before"].keys() - package["after"].keys(), key=lambda value: len(Path(value).parts), reverse=True):
                        target = safe(destination / name)
                        if package["before"][name] == "directory" and target.exists():
                            _ontology_checkpoint(targets=False)
                            target.rmdir()
                check_module_state(destination, operation, complete=True)
                check_module_sources(depot, operation)
                operation["completed_stages"].append("assets")
                checkpoint()
            operation["active_stage"] = "verification"
            checkpoint()
            check_module_state(destination, operation, complete=True)
            check_module_sources(depot, operation)
            verify_module_current(destination, operation, record)
            if "verification" not in operation["completed_stages"]:
                operation["completed_stages"].append("verification")
            checkpoint()
            operation.update(status="completed", active_stage=None)
            operation.pop("recovery", None)
            checkpoint()
            return record
        except (InitializationError, OSError, ValueError, KeyError) as error:
            operation["status"] = "partial"
            operation["active_stage"] = operation["active_stage"] or "verification"
            operation["recovery"] = {"stage": operation["active_stage"], "completed_stages": list(operation["completed_stages"]),
                "owned_record": RECORD, "reason": str(error) if isinstance(error, InitializationError) else "A local module adoption stage failed.",
                "next_action": "Preserve working files and repeat the exact selected module and dependency request after resolving the cause."}
            try:
                checkpoint()
            except (InitializationError, OSError):
                operation["recovery"]["record_update"] = "failed; retain the saved setup receipt"
            raise InitializationError("selected module adoption is incomplete; working state was retained",
                                      report={**record, "status": "partial", "base_setup_status": record["status"]}) from error


def run_initialization(
    *, mode: str, destination: Path, project_id: str, project_name: str, purpose: str,
    adopt_module: str | None = None, refresh_dependency: list[str] | None = None,
    refresh_module: list[str] | None = None,
) -> dict[str, Any]:
    if adopt_module == "curator":
        adopt_module = CURATOR_MODULE
    if mode not in {"create", "prepare-existing"}:
        raise InitializationError("unknown initialization route")
    refresh = sorted(set(refresh_dependency or []))
    refresh_modules = sorted(set(refresh_module or []))
    if refresh_modules == [ONTOLOGY_MODULE] and adopt_module is None:
        adopt_module = ONTOLOGY_MODULE
    if (adopt_module not in {None, LEARNING_MODULE, ONTOLOGY_MODULE, ADVANCED_MODULE, CURATOR_MODULE} or refresh not in ([], ["memory"])
            or refresh_modules not in ([], [ONTOLOGY_MODULE]) or adopt_module is not None and mode != "prepare-existing"
            or refresh and adopt_module != LEARNING_MODULE or refresh_modules and adopt_module != ONTOLOGY_MODULE):
        raise InitializationError("refresh requires its exact selected prepare-existing module; memory is a separate learning dependency")
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
    if adopt_module is not None:
        if record is None:
            raise InitializationError("module adoption requires a valid completed base setup receipt")
        return run_module_adoption(depot, destination, record, previous_raw, refresh, module_id=adopt_module, refresh_modules=refresh_modules)
    if record is not None:
        if any(operation["status"] != "completed" for operation in record.get("module_adoptions", [])):
            raise InitializationError("resume the exact pending selected module adoption before ordinary setup")
        record["mode"] = mode
    contract = record["setup_contract"] if record is not None else SETUP_CONTRACT
    with ExitStack() as template_guard:
        proposed = {}
        if record is None or "assets" not in record["completed_stages"]:
            proposed_all, sources, original = source_snapshot(depot, skill, identity, contract=contract,
                destination=destination, owned_governance=frozenset(record["owned_files"]) if record else frozenset())
            if record is None:
                if mode == "prepare-existing":
                    check_existing_role_layout(destination, proposed_all[ROLE_HELPER])
                preserved_licenses = license_inventory(destination)
                preserved_memory = memory_inventory(destination)
                proposed, before, preserved = asset_plan(destination, mode=mode,
                    proposed=proposed_all, original=original, saved_identity=saved_identity,
                    preserved_licenses=preserved_licenses)
                record = {"schema_version": 1, "setup_contract": SETUP_CONTRACT,
                          "status": "partial", "mode": mode, "operation_id": "project-setup-" + uuid4().hex,
                          "identity": identity, "project_root": str(destination), "sources": sources,
                          "owned_files": {name: sha(raw) for name, raw in proposed.items()},
                          "preserved_files": preserved, "preserved_licenses": preserved_licenses,
                          "preserved_memory": preserved_memory,
                          "preserved_learning": {name: digest for root in LEARNING_TREES for name, digest in package_inventory(destination, root).items()},
                          "preserved_ontology": ontology_inventory(destination),
                          "recovery_before": before,
                          "completed_stages": [], "active_stage": "assets", "checks": [],
                          "created_at": datetime.now(timezone.utc).isoformat(), "git_setup": "separate"}
                for entry in sources:
                    name = entry["destination"]
                    if name in preserved:
                        entry.update(adoption="preserved-project-owned", destination_sha256=preserved[name])
                    elif name not in proposed:
                        entry.update(adoption="skipped-existing-license" if name in LICENSE_FILES
                                     else "skipped-existing-package", destination_sha256=None)
                    else:
                        entry["adoption"] = ("specialized" if name in SPECIALIZED_FILES
                                             and proposed[name] != original.get(name) else "adopted")
                        entry["destination_sha256"] = sha(proposed[name])
            else:
                expected_sources = {(entry["source"], entry["source_sha256"]) for entry in record["sources"]}
                actual_sources = {(entry["source"], entry["source_sha256"]) for entry in sources}
                if expected_sources != actual_sources:
                    raise InitializationError("partial asset adoption source changed; preserve existing owned state")
                if contract != LEGACY_CONTRACT:
                    role_index = ROLE_ROOTS[contract] + "/INDEX.md"
                    proposed_all[role_index] = planned_role_index(destination, proposed_all, record["owned_files"], contract=contract)
                for name, checksum in record["owned_files"].items():
                    if name not in proposed_all or sha(proposed_all[name]) != checksum:
                        raise InitializationError("partial asset adoption differs from the saved plan")
                    proposed[name] = proposed_all[name]
            template_guard.enter_context(template_read_lock(depot))
            check_sources(depot, record["sources"], contract=contract)
            if file_bytes(depot / "depot/projects.json") != registry_before:
                raise InitializationError("registry changed during preflight")
            check_license_adoption(destination, record)
            check_memory_adoption(destination, record)
            check_learning_adoption(destination, record)
            check_ontology_adoption(destination, record)
        lock = depot / "depot" / (".initialize-" + sha(relative.encode())[:16] + ".lock")
        with exclusive(lock):
            if mode == "create" and previous_raw is None and destination.exists() and any(destination.iterdir()):
                raise InitializationError("new project destination changed after preflight")
            if (file_bytes(record_path) if record_path.exists() else None) != previous_raw:
                raise InitializationError("setup receipt changed since preflight")
            if "assets" not in record["completed_stages"]:
                check_license_adoption(destination, record)
                check_memory_adoption(destination, record)
                check_learning_adoption(destination, record)
                check_ontology_adoption(destination, record)
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
            for key in ("verified_at", "current_files", "current_licenses", "current_memory", "current_learning", "current_ontology", "ontology", "memory_capture", "recovery", "rerun", "static_health", "static_ready", "aggregate", "ready"):
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
                    check_sources(depot, record["sources"], contract=contract)
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
                    check_sources(depot, record["sources"], contract=contract)
                    check_license_adoption(destination, record)
                    check_memory_adoption(destination, record)
                    check_learning_adoption(destination, record)
                    check_ontology_adoption(destination, record)
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
                record["memory_capture"] = memory_capture_notice(destination)
                if contract in LEARNING_CONTRACTS or any(op["module_id"] == LEARNING_MODULE for op in record.get("module_adoptions", [])):
                    record["learning"] = assess_learning(destination)
                if contract in ONTOLOGY_CONTRACTS or any(op["module_id"] == ONTOLOGY_MODULE for op in record.get("module_adoptions", [])):
                    record["ontology"] = assess_ontology(destination)
                if contract in ADVANCED_CONTRACTS or any(op["module_id"] == ADVANCED_MODULE for op in record.get("module_adoptions", [])):
                    record["ontology_advanced"] = _advanced("assess", destination)
                _static("apply", destination, record)
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
        if mode == "prepare-existing":
            route.add_argument("--adopt-module", choices=[LEARNING_MODULE, ONTOLOGY_MODULE, ADVANCED_MODULE, CURATOR_MODULE, "curator"])
            route.add_argument("--refresh-dependency", action="append", choices=["memory"])
            route.add_argument("--refresh-module", action="append", choices=[ONTOLOGY_MODULE])
    assessment = commands.add_parser("assess-learning", help="Inspect local learning capability without writing or contacting a backend")
    assessment.add_argument("--destination", type=Path, required=True)
    ontology_assessment = commands.add_parser("assess-ontology", help="Statically inspect local ontology configuration and imports without executing copied code")
    ontology_assessment.add_argument("--destination", type=Path, required=True)
    advanced_assessment = commands.add_parser("assess-ontology-advanced", help="Inspect local advanced capability without executing project code or provisioning")
    advanced_assessment.add_argument("--destination", type=Path, required=True)
    curator_assessment = commands.add_parser("assess-curator", help="Inspect installed Curator identity and owner compatibility without writes or runtime activation")
    curator_assessment.add_argument("--destination", type=Path, required=True)
    arguments = vars(parser.parse_args(argv))
    try:
        result = (_curator("assess", arguments["destination"]) if arguments["mode"] == "assess-curator" else
                  assess_learning(arguments["destination"]) if arguments["mode"] == "assess-learning" else
                  assess_ontology(arguments["destination"]) if arguments["mode"] == "assess-ontology" else
                  _advanced("assess", arguments["destination"]) if arguments["mode"] == "assess-ontology-advanced" else run_initialization(**arguments))
        print(encoded(result).decode(), end="")
        return 1 if result.get("static_ready") is False else 0
    except (InitializationError, OSError, subprocess.TimeoutExpired) as error:
        result = {"status": "failed", "error_type": type(error).__name__}
        if isinstance(error, InitializationError):
            result["reason"] = str(error)
            if error.report:
                result = {**error.report, "reason": str(error)}
        print(encoded(result).decode(), end="")
        return 2



# Optional action guard adapter.  Standalone/core use imports no ontology runtime.
def _ontology_checkpoint(*, targets=True):
    import sys as _sys
    _module = _sys.modules.get("ontology_guards")
    if _module is not None:
        _module.checkpoint(targets=targets)


def _ontology_guard_adapter(function, family, root_argument, target_paths):
    import functools as _functools
    import inspect as _inspect
    @_functools.wraps(function)
    def guarded(*args, **kwargs):
        import importlib.util as _util
        import sys as _sys
        from pathlib import Path as _Path
        arguments = dict(_inspect.signature(function).bind(*args, **kwargs).arguments)
        if root_argument == "@depot":
            selected_root = installed_locations()[0]
        else:
            selected_root = arguments[root_argument]
            if not isinstance(selected_root, (_Path, str)):
                selected_root = getattr(selected_root, "project_root", getattr(selected_root, "root", selected_root))
        selected_root = _Path(selected_root).absolute()
        config_path = selected_root / "ontology-advanced.yaml"
        if not config_path.exists() and not config_path.is_symlink():
            return function(*args, **kwargs)
        if family == "template" and arguments.get("command") == "check":
            return function(*args, **kwargs)
        import json as _json
        import hashlib as _hashlib
        def unique_pairs(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate guard configuration key")
                value[key] = item
            return value
        try:
            if config_path.is_symlink():
                raise ValueError("symbolic guard configuration")
            config = _json.loads(config_path.read_text(), object_pairs_hook=unique_pairs)
            selected = config.get("profiles", {}).get("guards", {"enabled": False})
            if config.get("schema_version") != 1 or not isinstance(selected, dict) or type(selected.get("enabled")) is not bool:
                raise ValueError("unsupported guard configuration")
        except (OSError, ValueError, AttributeError) as exc:
            raise _ontology_adapter_error("guard_schema", "Guard configuration is unreadable or unsupported.", {}) from exc
        if not selected["enabled"]:
            if set(selected) != {"enabled"}:
                raise _ontology_adapter_error("guard_schema", "Disabled guard configuration has unsupported fields.", {})
            return function(*args, **kwargs)
        script = selected_root / ".agents/skills/ontology/scripts/ontology_guards.py"
        if not script.is_file() or any(parent.is_symlink() for parent in (script, *script.parents)):
            raise _ontology_adapter_error("guard_unavailable", "Enabled guards require their current project-local installed adapter.", {})
        current_sha256 = _hashlib.sha256(script.read_bytes()).hexdigest()
        module = _sys.modules.get("ontology_guards")
        if module is not None and (_Path(module.__file__).resolve() != script.resolve()
                or getattr(module, "ENGINE_SOURCE_SHA256", None) != current_sha256):
            raise _ontology_adapter_error("guard_stale", "Loaded guard code differs from this selected project's current installed bytes; use a fresh owning-helper process after reviewed repair.", {})
        if module is None:
            spec = _util.spec_from_file_location("ontology_guards", script)
            module = _util.module_from_spec(spec)
            _sys.modules["ontology_guards"] = module
            _sys.path.insert(0, str(script.parent))
            spec.loader.exec_module(module)
        targets = list(target_paths)
        if family == "setup":
            destination = _Path(arguments["destination"]).absolute()
            try:
                relative = destination.relative_to(selected_root).as_posix()
            except ValueError:
                raise _ontology_adapter_error("guard_scope", "Setup target escapes the selected depot.", {})
            targets.extend([relative + "/control_records/project-setup.json", relative + "/AGENTS.md", relative + "/ROLE.md"])
        try:
            return module.dispatch(lambda: function(*args, **kwargs), family, function.__name__, selected_root, arguments, targets)
        except module.GuardError as exc:
            raise _ontology_adapter_error(exc.code, str(exc), exc.details) from exc
    return guarded


def _ontology_adapter_error(code, message, details):
    return InitializationError(code + ": " + message, report=details)

ONTOLOGY_GUARDED_ACTIONS = ['run_initialization', 'run_module_adoption']
run_initialization = _ontology_guard_adapter(run_initialization, 'setup', '@depot', ['depot/projects.json'])

run_module_adoption = _ontology_guard_adapter(run_module_adoption, "setup", "depot", ["depot/projects.json"])

if __name__ == "__main__":
    raise SystemExit(main())
