#!/usr/bin/env python3
"""Publish validated depot files into the one Sys4AI project template.

The receipt owns individual destination bytes. The explicit role-case migration
also binds the original directory identity and preserves its complete tree. A
pending record permits forward recovery after interrupted per-file atomic
writes; this is not a transactionally swapped template tree. Initializers
coordinate their template reads with a shared lock on the same lock file.
"""

from __future__ import annotations

import argparse
import ast
import base64
import binascii
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import types
import unicodedata
from typing import Any, Iterator

TEMPLATE = "Projects/Sys4AI-Template-Project"
MANIFEST = "depot/template-update.json"
CONTROL = ".sys4ai/template-update"
STATE = CONTROL + "/state.json"
PENDING = CONTROL + "/pending.json"
LOCK = CONTROL + "/lock"
BASELINE_SKILLS = (
    "agent-task", "communication", "manage-subagent-roles", "task",
    "to-implementation-plan", "to-trd",
)
LEGACY_BASELINE_FILES = {
    "SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md", ".gitignore",
    "sub-agent-roles/project-sub-agent/AGENTS.md",
    "sub-agent-roles/project-sub-agent/ROLE.md", ".template/baseline-assets.json",
    ".template/project-readme.md",
    *(f".agents/skills/{name}/SKILL.md" for name in BASELINE_SKILLS),
}
ROLE_INDEX = "Roles/INDEX.md"
PREVIOUS_ROLE_INDEX = "roles/INDEX.md"
ROLE_HELPER = ".agents/skills/manage-subagent-roles/scripts/role_catalog.py"
BASELINE_FILES = (LEGACY_BASELINE_FILES - {
    "sub-agent-roles/project-sub-agent/AGENTS.md", "sub-agent-roles/project-sub-agent/ROLE.md",
}) | {ROLE_INDEX, ROLE_HELPER, *(f"Roles/{name}/{filename}" for name in
      ("project-sub-agent", "task-manager") for filename in ("AGENTS.md", "ROLE.md"))}
EXCLUDED = {
    ".git", ".gitmodules", ".gitignore_global", ".venv", "venv", "env",
    ".sys4ai", "__pycache__", ".ds_store", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", ".cache", "models", "logs", ".cognee", ".cognee_system",
    ".data_storage", "dist", "build", "node_modules", ".env", ".envrc",
    ".secrets", "secrets", "credentials", ".credentials", "credentials.json",
    ".credentials.json", ".aws", ".ssh", ".netrc", ".pypirc", ".npmrc",
    "id_rsa", "id_ed25519", ".transition.json",
}
EXCLUDED_SUFFIXES = (
    ".pyc", ".pyo", ".log", ".zip", ".whl", ".egg", ".pem", ".key",
    ".p12", ".pfx", ".swp", ".swo", "~",
)
HASH = re.compile(r"[0-9a-f]{64}\Z")
SKILL_NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


class UpdateError(RuntimeError):
    def __init__(self, message: str, *, report: dict[str, Any] | None = None):
        super().__init__(message)
        self.report = report or {"status": "blocked", "conflicts": [message]}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def json_document(raw: bytes) -> Any:
    def unique(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise UpdateError("duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=unique)
    except (UnicodeError, ValueError) as error:
        raise UpdateError("invalid JSON document") from error


def relative(value: str) -> str:
    if (
        not isinstance(value, str) or not value or "\\" in value
        or any(ord(char) < 32 for char in value)
        or PurePosixPath(value).is_absolute()
        or any(part in {".", "..", ""} for part in value.split("/"))
    ):
        raise UpdateError("expected a relative path without traversal")
    return value


def safe(path: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise UpdateError("absolute paths without traversal are required")
    for item in reversed((path, *path.parents)):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise UpdateError(f"symbolic link is not allowed: {item}")
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise UpdateError(f"parent is not a directory: {item}")
    return path


def read_file(path: Path, *, optional: bool = False) -> bytes | None:
    safe(path)
    try:
        before = path.lstat()
    except FileNotFoundError:
        if optional:
            return None
        raise UpdateError(f"required file is missing: {path}")
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise UpdateError(f"expected a regular non-aliased file: {path}")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise UpdateError(f"file changed while opening: {path}")
        data = stream.read()
        after = os.fstat(stream.fileno())
    current = path.lstat()
    signature = lambda item: (
        item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns
    )
    if signature(before) != signature(after) or signature(after) != signature(current):
        raise UpdateError(f"file changed while reading: {path}")
    return data


def excluded(path: str) -> bool:
    # Generated Explorer fixtures and captured test output are retained source
    # evidence, not neutral starter assets. Do not parse or copy their contents.
    fixtures = "SKILLS-depo/ontology/tests/fixtures/explorer"
    if path == fixtures or path.startswith(fixtures + "/"):
        return True
    parts = PurePosixPath(path).parts
    return any(
        part.lower() in EXCLUDED or part.lower().startswith(("._", ".env."))
        for part in parts
    ) or parts[-1].lower().endswith(EXCLUDED_SUFFIXES)


def destination(value: str) -> str:
    value = relative(value)
    if excluded(value):
        raise UpdateError(f"destination is a protected or transient path: {value}")
    return value


def source(value: str) -> str:
    value = relative(value)
    parts = value.split("/")
    if len(parts) < 2 or not parts[0].endswith("-depo") or excluded(value):
        raise UpdateError(f"source must be a nontransient depot file: {value}")
    return value


def validate_skill(name: str, raw: bytes) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeError as error:
        raise UpdateError(f"skill metadata must be UTF-8: {name}") from error
    front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not SKILL_NAME.fullmatch(name) or not front:
        raise UpdateError(f"skill needs a valid name and frontmatter: {name}")
    fields: dict[str, str] = {}
    lines = front.group(1).splitlines()
    for index, line in enumerate(lines):
        field = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", line)
        if not field:
            continue
        key, value = field.groups()
        if key in fields:
            raise UpdateError(f"duplicate skill metadata field: {name}/{key}")
        if value in {">", "|", ">-", "|-", ">+", "|+"}:
            continuation = []
            for following in lines[index + 1:]:
                if following and not following[0].isspace():
                    break
                continuation.append(following.strip())
            value = " ".join(continuation).strip()
        if value.startswith(("\"", "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise UpdateError(f"unterminated skill metadata value: {name}/{key}")
            value = value[1:-1]
        fields[key] = value
    if fields.get("name") != name or not fields.get("description", "").strip():
        raise UpdateError(f"skill name must match its folder and have a description: {name}")


def role_index_inputs(files: dict[str, Any], role_root: str = "Roles") -> dict[str, dict[str, str]]:
    if not isinstance(files, dict) or any(not isinstance(name, str) for name in files):
        raise UpdateError("invalid generated role index file inventory")
    targets = {"SOUL.md", ROLE_HELPER} | {name for name in files if name.startswith(role_root + "/") and name != role_root + "/INDEX.md"}
    if not targets <= files.keys():
        raise UpdateError("role index lacks its validator or instruction source")
    if any(not isinstance(files[target], dict) or not {"source", "sha256"} <= files[target].keys()
           or not all(isinstance(files[target][key], str) for key in ("source", "sha256")) for target in targets):
        raise UpdateError("invalid generated role index input binding")
    return {target: {key: files[target][key] for key in ("source", "sha256")} for target in sorted(targets)}


def render_role_index(inputs: dict[str, bytes], role_root: str = "Roles") -> bytes:
    """Validate and render from frozen bytes; never write into the Template."""
    if not {"SOUL.md", ROLE_HELPER} <= inputs.keys():
        raise UpdateError("role index lacks its frozen inputs")
    module_name = "_template_role_catalog_" + digest(inputs[ROLE_HELPER])
    helper = types.ModuleType(module_name)
    helper.__file__ = ROLE_HELPER
    sys.modules[module_name] = helper
    try:
        exec(compile(inputs[ROLE_HELPER], ROLE_HELPER, "exec"), helper.__dict__)
        if helper.ROLE_ROOT_NAME != role_root:
            raise UpdateError("role validator does not support the active roles layout")
        with tempfile.TemporaryDirectory(prefix="sys4ai-role-index-") as temporary:
            root = Path(temporary).resolve()
            (root / role_root).mkdir()
            for target, raw in inputs.items():
                if target == ROLE_HELPER:
                    continue
                path = root / destination(target)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            catalog = helper.build_catalog(root)
            if catalog.invalid_roles or not {"project-sub-agent", "task-manager"} <= {entry.name for entry in catalog.valid_roles}:
                raise UpdateError("template role pairs are invalid or required roles are missing")
            return helper.render_index(catalog).encode()
    except (AttributeError, RuntimeError, OSError, UnicodeError) as error:
        if isinstance(error, UpdateError):
            raise
        raise UpdateError(f"role index validation failed: {error}") from error
    finally:
        sys.modules.pop(module_name, None)


def validate_curator_distribution(files, blobs):
    """The selected Curator module must be complete and remain neutral in Template."""
    if not any(name in files for name in ("CURATOR.md", "curator.yaml", "document-ownership.json")):
        return
    contract_path = "CURATION-depo/contract.json"
    if contract_path not in blobs:
        raise UpdateError("selected Curator starter lacks its current application contract")
    contract = json_document(blobs[contract_path])
    if not isinstance(contract, dict) or contract.get("schema_version") != 2 or contract.get("module_id") != "project-curator":
        raise UpdateError("selected Curator application contract is unsupported")
    required = {"CURATOR.md", "curator.yaml", "document-ownership.json"}
    for key, prefix in (("required_skill_resources", ".agents/skills/curate/"), ("required_contract_resources", "reference-assets/CURATION-depo/")):
        resources = contract.get(key)
        if not isinstance(resources, list) or not resources or any(not isinstance(name, str) for name in resources):
            raise UpdateError("Curator contract requires exact resource paths")
        required.update(prefix + relative(name) for name in resources)
    owners = {"CURATOR.md": "ROLES-depo/project-curator-CURATOR.md", "curator.yaml": "CURATION-depo/starter/curator.yaml", "document-ownership.json": "CURATION-depo/starter/document-ownership.json"}
    for role in ("curator-manager", "documentation-curator", "knowledge-curator", "improvement-maintenance"):
        for leaf in ("AGENTS.md", "ROLE.md"):
            owners["Roles/" + role + "/" + leaf] = "ROLES-depo/" + role + "-" + leaf
    required.update(owners)
    missing = sorted(required - files.keys())
    if missing:
        raise UpdateError("incomplete Curator distribution: " + ", ".join(missing))
    if any(files[target]["source"] != source for target, source in owners.items()):
        raise UpdateError("Curator charter, configuration and paired roles require their exact source owners")
    config = json_document(blobs[owners["curator.yaml"]])
    inactive = {"schema_version": 1, "module_id": "project-curator", "module_version": "1.0.0",
        "project": {"id": None, "repository_id": None, "coordination_root": None}, "branches": [],
        "controller": {"kind": None, "charter": None}, "runtime": None, "accepted_policy": None,
        "entitlements": [], "autonomous_write": False,
        "schedule": {"enabled": False, "debounce_seconds": None, "catch_up_seconds": None, "dependency_cadence_seconds": None},
        "bounds": {"model_calls": None, "work_seconds": None, "candidate_bytes": None, "concurrent_agents": None},
        "trusted_sources": [], "tools": [], "network": [], "notifications": {"enabled": False, "destinations": []},
        "service_installed": False, "hook_installed": False, "capabilities": []}
    if encoded(config) != encoded(inactive):
        raise UpdateError("Curator Template must remain neutral without project selection, standing grants, runtime or schedules")
    if "ontology_integration" in contract:
        # The integrated edition ships a neutral recipe, never populated active
        # semantics, configured identities or enabled session authority.
        session_source = "CURATION-depo/starter/curator-session.yaml"
        if files.get("curator-session.yaml", {}).get("source") != session_source or session_source not in blobs:
            raise UpdateError("integrated Curator distribution lacks its exact session starter owner")
        session = json_document(blobs[session_source])
        if session.get("project_id") is not None or session.get("enabled") is not False or session.get("unattended_background_ai") is not False:
            raise UpdateError("Curator Template session must remain neutral and disabled")
        recipe = "ONTOLOGY-depo/integrations/curator/1.0.0/"
        manifest = json_document(blobs.get(recipe + "manifest.json", b"{}"))
        if manifest.get("edition") != "curator-ontology-1.0.0" or set(manifest.get("files", {})) != {"recipe.json", "locators.json", "competency.json", "contract.md"}:
            raise UpdateError("integrated Curator recipe manifest is incomplete")
        for name, expected in manifest["files"].items():
            source = recipe + name
            if source not in blobs or digest(blobs[source]) != expected or files.get("reference-assets/" + source, {}).get("source") != source:
                raise UpdateError("integrated Curator recipe resource is missing or changed: " + name)
        config_source = files.get("ontology.yaml", {}).get("source")
        if config_source not in blobs:
            raise UpdateError("integrated Curator distribution requires neutral ontology configuration")
        ontology = json_document(blobs[config_source])
        if ontology.get("project", {}).get("id") is not None or ontology.get("publication") != {"enabled": False, "binding": None}:
            raise UpdateError("Template ontology identity and publication authority must remain neutral")
        if (ontology.get("project_files") != ["ONTOLOGY/modules/project/project.jsonld"]
                or ontology.get("binding_files") != ["ONTOLOGY/bindings/bindings.jsonld"]
                or ontology.get("competency_files", []) != []):
            raise UpdateError("Template must retain its empty neutral canonical graph selection")
        for name in ontology.get("project_files", []) + ontology.get("binding_files", []):
            source = files.get(name, {}).get("source")
            if source not in blobs or json_document(blobs[source]).get("@graph") != []:
                raise UpdateError("Template active ontology graphs must remain empty")
    ownership = json_document(blobs[owners["document-ownership.json"]])
    if (not isinstance(ownership, dict) or ownership.get("schema_version") != 1 or not isinstance(ownership.get("entries"), list)
            or any(not isinstance(entry, dict) or entry.get("sha256") is not None or any(section.get("sha256") is not None for section in entry.get("sections", [])) for entry in ownership["entries"])):
        raise UpdateError("Curator Template ownership examples cannot carry selected project versions")


def snapshot(root: Path) -> dict[str, Any]:
    """Read one validated source snapshot without touching the template."""
    safe(root)
    if not root.is_dir():
        raise UpdateError("depot root is missing")
    manifest_raw = read_file(root / MANIFEST)
    manifest = json_document(manifest_raw)
    if (
        not isinstance(manifest, dict) or manifest.get("schema_version") != 1
        or manifest.get("template") != TEMPLATE
        or set(manifest) != {"schema_version", "template", "overrides", "mirrors"}
    ):
        raise UpdateError("expected a schema-1 manifest for the Sys4AI template")
    for key in ("overrides", "mirrors"):
        if not isinstance(manifest[key], dict):
            raise UpdateError(f"manifest {key} must contain exact file mappings")
        for origin, target in manifest[key].items():
            source(origin)
            destination(target)

    mapped_sources = set(manifest["overrides"]) | set(manifest["mirrors"])
    collections: list[str] = []
    blobs: dict[str, bytes] = {}
    modes: dict[str, int] = {}
    skill_dirs: list[str] = []

    def walk(folder: Path) -> None:
        for item in sorted(folder.iterdir()):
            rel = item.relative_to(root).as_posix()
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise UpdateError(f"symbolic link in depot source: {rel}")
            if excluded(rel):
                continue
            if stat.S_ISDIR(info.st_mode):
                if item.parent == root / "SKILLS-depo":
                    skill_dirs.append(item.name)
                walk(item)
            elif stat.S_ISREG(info.st_mode):
                raw = read_file(item)
                if item.suffix == ".json":
                    try:
                        json_document(raw)
                    except UpdateError as error:
                        raise UpdateError(f"invalid JSON source: {rel}") from error
                if item.suffix == ".py":
                    try:
                        ast.parse(raw, filename=rel)
                    except (SyntaxError, ValueError) as error:
                        raise UpdateError(f"invalid Python source: {rel}") from error
                blobs[rel] = raw
                modes[rel] = 0o755 if info.st_mode & 0o111 else 0o644
            else:
                raise UpdateError(f"non-regular depot source: {rel}")

    for folder in sorted(root.iterdir()):
        if folder.name.endswith("-depo"):
            safe(folder)
            if not folder.is_dir():
                raise UpdateError(f"depot collection is not a directory: {folder.name}")
            collections.append(folder.name)
            walk(folder)
    missing_mapped = sorted(mapped_sources - blobs.keys())
    if missing_mapped:
        raise UpdateError("mapped source is missing: " + ", ".join(missing_mapped))
    for name in skill_dirs:
        header = blobs.get(f"SKILLS-depo/{name}/SKILL.md")
        if header is None:
            raise UpdateError(f"incomplete skill package, SKILL.md is missing: {name}")
        validate_skill(name, header)

    files: dict[str, dict[str, Any]] = {}
    identities: dict[str, str] = {}
    for origin, raw in sorted(blobs.items()):
        parts = origin.split("/")
        default = (
            ".agents/skills/" + "/".join(parts[1:])
            if parts[0] == "SKILLS-depo" and len(parts) > 2
            else "reference-assets/" + origin
        )
        targets = [manifest["overrides"].get(origin, default)]
        if origin in manifest["mirrors"]:
            targets.append(manifest["mirrors"][origin])
        for target in targets:
            destination(target)
            identity = unicodedata.normalize("NFD", target).casefold()
            if identity in identities:
                raise UpdateError(f"duplicate template destination: {target}")
            identities[identity] = target
            files[target] = {"source": origin, "sha256": digest(raw), "mode": modes[origin]}
    for key in identities:
        if any(parent.as_posix() in identities for parent in PurePosixPath(key).parents):
            raise UpdateError(f"template file/directory mapping collision: {identities[key]}")
    reserved_index = unicodedata.normalize("NFD", ROLE_INDEX).casefold()
    if reserved_index in identities:
        raise UpdateError("Roles/INDEX.md is generated; a static source mapping cannot own it")
    if any(reserved_index in {parent.as_posix() for parent in PurePosixPath(name).parents}
           or name in {parent.as_posix() for parent in PurePosixPath(reserved_index).parents} for name in identities):
        raise UpdateError("generated role index has a file/directory mapping collision")
    missing = sorted((BASELINE_FILES - {ROLE_INDEX}) - files.keys())
    if missing:
        raise UpdateError("required template governance source is missing: " + ", ".join(missing))
    for target in BASELINE_FILES - {ROLE_INDEX}:
        if not blobs[files[target]["source"]].strip():
            raise UpdateError(f"required template governance source is empty: {target}")
    policy = json_document(blobs[files[".template/baseline-assets.json"]["source"]])
    if (not isinstance(policy, dict) or type(policy.get("schema_version")) is not int
            or policy["schema_version"] != 2):
        raise UpdateError("template initialization policy must use schema 2")
    if policy.get("roles") != "Roles":
        raise UpdateError("template initialization policy must use the active roles layout")
    validate_curator_distribution(files, blobs)
    inputs = role_index_inputs(files)
    index = render_role_index({target: blobs[entry["source"]] for target, entry in inputs.items()})
    files[ROLE_INDEX] = {"source": files[ROLE_HELPER]["source"], "sha256": digest(index), "mode": 0o644,
                         "generated": {"kind": "role-index-v1", "inputs": inputs}}
    state = {"schema_version": 1, "template": TEMPLATE, "collections": collections, "files": files}
    return {
        "state": state, "blobs": blobs, "generated": {ROLE_INDEX: index},
        "fingerprint": digest(manifest_raw + encoded(state)),
    }


def validate_state(state: Any) -> dict[str, Any]:
    if (
        not isinstance(state, dict) or state.get("schema_version") != 1
        or state.get("template") != TEMPLATE
        or not isinstance(state.get("collections"), list)
        or not isinstance(state.get("files"), dict)
    ):
        raise UpdateError("invalid template update state")
    collections = state["collections"]
    if any(
        not isinstance(name, str) or "/" in relative(name) or not name.endswith("-depo")
        for name in collections
    ) or len(set(collections)) != len(collections):
        raise UpdateError("invalid recorded depot collections")
    identities: set[str] = set()
    for target, entry in state["files"].items():
        destination(target)
        identity = unicodedata.normalize("NFD", target).casefold()
        if identity in identities:
            raise UpdateError("case-equivalent recorded destinations are ambiguous")
        identities.add(identity)
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("sha256"), str)
            or not HASH.fullmatch(entry["sha256"])
            or not isinstance(entry.get("mode"), int)
            or entry.get("mode") not in {0o644, 0o755}
        ):
            raise UpdateError("invalid recorded destination ownership")
        if source(entry.get("source")).split("/")[0] not in collections:
            raise UpdateError("recorded source collection is missing")
        if "generated" in entry and (target not in {ROLE_INDEX, PREVIOUS_ROLE_INDEX} or entry["generated"] != {
            "kind": "role-index-v1", "inputs": role_index_inputs(state["files"], target.split("/")[0])
        } or entry["source"] != state["files"][ROLE_HELPER]["source"]):
            raise UpdateError("invalid generated role index ownership")
    role_roots = {target.split("/")[0] for target in state["files"] if target.split("/")[0].casefold() == "roles"}
    if len(role_roots) > 1 or role_roots - {"Roles", "roles"}:
        raise UpdateError("recorded role directory casing is ambiguous")
    for index in (ROLE_INDEX, PREVIOUS_ROLE_INDEX):
        if index in state["files"] and "generated" not in state["files"][index]:
            raise UpdateError("recorded role index must have generated ownership")
    return state


def load_state(root: Path) -> dict[str, Any]:
    raw = read_file(root / STATE, optional=True)
    if raw is None:
        return {"schema_version": 1, "template": TEMPLATE, "collections": [], "files": {}}
    return validate_state(json_document(raw))


def file_hash(path: Path) -> str | None:
    raw = read_file(path, optional=True)
    return None if raw is None else digest(raw)


def retirement_targets(
    root: Path, before: dict[str, Any], after: dict[str, Any], collection: str,
) -> list[str]:
    """Validate the exact collection transition independently of destination bytes."""
    if "/" in relative(collection) or not collection.endswith("-depo"):
        raise UpdateError("retirement requires one exact depot collection name")
    if collection not in before["collections"]:
        raise UpdateError("retired collection is not in the recorded state")
    if safe(root / collection).exists() or collection in after["collections"]:
        raise UpdateError("retired source collection must be absent")
    lost = set(before["collections"]) - set(after["collections"])
    if lost != {collection}:
        raise UpdateError("unexpected missing source collection during retirement")
    targets = sorted(
        target for target, entry in before["files"].items()
        if entry["source"].split("/")[0] == collection
    )
    if set(targets) & after["files"].keys():
        raise UpdateError("retired collection destinations must not be remapped")
    return targets


def role_layout(state: dict[str, Any]) -> str:
    return "roles" if any(name.startswith("roles/") for name in state["files"]) else "Roles"


def role_case_mapping(before: dict[str, Any], after: dict[str, Any]) -> dict[str, str]:
    """Translate only the reviewed complete managed lowercase role collection."""
    if role_layout(before) != "roles" or role_layout(after) != "Roles":
        return {}
    mapping = {name: "Roles/" + name.removeprefix("roles/")
               for name in before["files"] if name.startswith("roles/")}
    for old, new in mapping.items():
        if new not in after["files"] or before["files"][old]["source"] != after["files"][new]["source"]:
            raise UpdateError("case transition requires every old role destination and its exact source")
    return mapping


def role_case_entries(template: Path) -> list[str]:
    return sorted(item.name for item in template.iterdir()
                  if unicodedata.normalize("NFD", item.name).casefold() == "roles")


def role_tree(folder: Path) -> dict[str, Any]:
    """Capture all bytes and directory entries, including unmanaged preserved files."""
    safe(folder)
    if not folder.is_dir():
        raise UpdateError("role case transition requires a directory")
    files, directories, identities = {}, [], set()
    for item in sorted(folder.rglob("*")):
        safe(item)
        name = item.relative_to(folder).as_posix()
        identity = unicodedata.normalize("NFD", name).casefold()
        if identity in identities:
            raise UpdateError("case-equivalent role tree entries are ambiguous")
        identities.add(identity)
        if item.is_dir():
            directories.append(name)
        else:
            files[name] = {"sha256": digest(read_file(item)), "mode": stat.S_IMODE(item.stat().st_mode)}
    return {"files": files, "directories": directories}


def case_preview(root: Path, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any] | None:
    mapping = role_case_mapping(before, after)
    if not mapping:
        return None
    template = root / TEMPLATE
    if role_case_entries(template) != ["roles"]:
        raise UpdateError("case transition requires exactly the recorded lowercase roles directory")
    folder = safe(template / "roles")
    tree = role_tree(folder)
    for old in mapping:
        if tree["files"].get(old.removeprefix("roles/"), {}).get("sha256") != before["files"][old]["sha256"]:
            raise UpdateError("managed role changed before case transition")
    info = folder.stat()
    temporary = ".template-roles-case-" + digest(encoded([before, after]))[:24]
    if safe(template / temporary).exists():
        raise UpdateError("role case transition temporary directory already exists")
    return {"schema_version": 1, "from": "roles", "to": "Roles", "temporary": temporary,
            "directory_identity": {"device": info.st_dev, "inode": info.st_ino},
            "before_state_sha256": file_hash(root / STATE), "mapping": mapping, "tree": tree}


def case_record(root: Path, preview: dict[str, Any]) -> dict[str, Any]:
    folder = root / TEMPLATE / "roles"
    raw_state = read_file(root / STATE)
    if digest(raw_state) != preview["before_state_sha256"] or role_tree(folder) != preview["tree"]:
        raise UpdateError("role case transition input changed before recovery capture")
    payloads = {}
    for name, entry in preview["tree"]["files"].items():
        raw = read_file(folder / name)
        if digest(raw) != entry["sha256"]:
            raise UpdateError("role case transition bytes changed during recovery capture")
        payloads[name] = base64.b64encode(raw).decode("ascii")
    info = folder.stat()
    if (role_case_entries(root / TEMPLATE) != ["roles"] or role_tree(folder) != preview["tree"]
            or {"device": info.st_dev, "inode": info.st_ino} != preview["directory_identity"]
            or file_hash(root / STATE) != preview["before_state_sha256"]):
        raise UpdateError("role case transition input changed during recovery capture")
    return {"preview": preview, "before_state": base64.b64encode(raw_state).decode("ascii"), "payloads": payloads}


def validate_case_record(root: Path, record: Any, before: dict[str, Any], after: dict[str, Any]) -> str | None:
    """Validate saved history and return the one actual directory spelling/location."""
    mapping = role_case_mapping(before, after)
    if not mapping:
        if record is not None:
            raise UpdateError("unexpected role case transition record")
        return None
    if not isinstance(record, dict) or set(record) != {"preview", "before_state", "payloads"}:
        raise UpdateError("role case transition recovery record is missing or invalid")
    preview = record["preview"]
    if (not isinstance(preview, dict) or set(preview) != {"schema_version", "from", "to", "temporary", "directory_identity", "before_state_sha256", "mapping", "tree"}
            or type(preview["schema_version"]) is not int or preview["schema_version"] != 1
            or preview["from"] != "roles" or preview["to"] != "Roles" or preview["mapping"] != mapping
            or preview["temporary"] != ".template-roles-case-" + digest(encoded([before, after]))[:24]):
        raise UpdateError("role case transition recovery preview is invalid")
    try:
        raw_state = base64.b64decode(record["before_state"], validate=True)
    except (ValueError, TypeError, binascii.Error) as error:
        raise UpdateError("role case transition state payload is invalid") from error
    if digest(raw_state) != preview["before_state_sha256"] or json_document(raw_state) != before:
        raise UpdateError("role case transition original state changed")
    tree = preview["tree"]
    if (not isinstance(tree, dict) or set(tree) != {"files", "directories"}
            or not isinstance(tree["files"], dict) or not isinstance(tree["directories"], list)
            or not isinstance(record["payloads"], dict) or set(record["payloads"]) != set(tree["files"])):
        raise UpdateError("role case transition tree inventory is invalid")
    for name in tree["directories"]:
        relative(name)
    for name, entry in tree["files"].items():
        relative(name)
        try:
            raw = base64.b64decode(record["payloads"][name], validate=True)
        except (ValueError, TypeError, binascii.Error) as error:
            raise UpdateError("role case transition file payload is invalid") from error
        if (not isinstance(entry, dict) or set(entry) != {"sha256", "mode"}
                or digest(raw) != entry["sha256"] or type(entry["mode"]) is not int):
            raise UpdateError("role case transition file checksum is invalid")
    for old in mapping:
        if tree["files"].get(old.removeprefix("roles/"), {}).get("sha256") != before["files"][old]["sha256"]:
            raise UpdateError("role case transition archive differs from original ownership")
    template = root / TEMPLATE
    names = role_case_entries(template)
    temporary = safe(template / preview["temporary"])
    if temporary.exists():
        names.append(temporary.name)
    if len(names) != 1 or names[0] not in {"roles", "Roles", temporary.name}:
        raise UpdateError("role case transition has missing or ambiguous directories")
    location = names[0]
    folder = safe(template / location)
    info = folder.stat()
    if {"device": info.st_dev, "inode": info.st_ino} != preview["directory_identity"]:
        raise UpdateError("role case transition directory identity changed")
    actual = role_tree(folder)
    if location != "Roles":
        if actual != tree:
            raise UpdateError("role case transition tree changed before rename")
    else:
        allowed_files = dict(tree["files"])
        allowed_dirs = set(tree["directories"])
        for target, entry in after["files"].items():
            if target.startswith("Roles/"):
                name = target.removeprefix("Roles/")
                allowed_files.setdefault(name, entry)
                allowed_dirs.update(parent.as_posix() for parent in PurePosixPath(name).parents if parent.as_posix() != ".")
        if not tree["files"].keys() <= actual["files"].keys() <= allowed_files.keys() or not set(tree["directories"]) <= set(actual["directories"]) <= allowed_dirs:
            raise UpdateError("role case transition tree inventory changed during publication")
        for name, entry in actual["files"].items():
            old_hash = tree["files"].get(name, {}).get("sha256")
            new_hash = after["files"].get("Roles/" + name, {}).get("sha256")
            if entry["sha256"] not in {old_hash, new_hash}:
                raise UpdateError("role case transition bytes changed during publication")
            if "Roles/" + name not in after["files"] and entry != tree["files"][name]:
                raise UpdateError("preserved role file changed during publication")
    if load_state(root) == before and file_hash(root / STATE) != preview["before_state_sha256"]:
        raise UpdateError("role case transition state digest changed")
    return location


def rename_role_directory(source: Path, destination: Path) -> None:
    """Refuse even an empty destination created after the caller's preflight."""
    import ctypes
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(library, "renamex_np"):
        rename = library.renamex_np
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        args = (os.fsencode(source), os.fsencode(destination), 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        rename = library.renameat2
        rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        args = (-100, os.fsencode(source), -100, os.fsencode(destination), 1)  # AT_FDCWD, RENAME_NOREPLACE
    else:
        raise UpdateError("this host has no supported exclusive directory rename")
    rename.restype = ctypes.c_int
    if rename(*args) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def finish_case_rename(root: Path, record: dict[str, Any], before: dict[str, Any], after: dict[str, Any]) -> None:
    """Move the same owned directory through a non-aliasing intermediate name."""
    template = root / TEMPLATE
    for old, new in (("roles", record["preview"]["temporary"]), (record["preview"]["temporary"], "Roles")):
        location = validate_case_record(root, record, before, after)
        if location != old:
            continue
        if safe(template / new).exists():
            raise UpdateError("role case transition rename destination appeared")
        rename_role_directory(template / old, template / new)
        descriptor = os.open(template, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    if validate_case_record(root, record, before, after) != "Roles":
        raise UpdateError("role case transition did not reach the exact Roles spelling")


def plan(
    root: Path, before: dict[str, Any], after: dict[str, Any],
    *, retire_collection: str | None = None,
) -> dict[str, Any]:
    template = safe(root / TEMPLATE)
    if not template.is_dir():
        raise UpdateError("template directory is missing; updater never creates a replacement root")
    report: dict[str, Any] = {
        "status": "current", "additions": [], "updates": [], "deletions": [],
        "adoptions": [], "conflicts": [], "managed_files": len(after["files"]),
        "source_files": len({item["source"] for item in after["files"].values()}),
    }
    lost = sorted(set(before["collections"]) - set(after["collections"]))
    if retire_collection is not None:
        report["retired_collection"] = retire_collection
        report["retired_destinations"] = retirement_targets(root, before, after, retire_collection)
        lost.remove(retire_collection)
    if lost:
        report["conflicts"].append("recorded source collection is missing: " + ", ".join(lost))
    transition = case_preview(root, before, after)
    mapping = role_case_mapping(before, after)
    previous_files = {mapping.get(name, name): entry for name, entry in before["files"].items()}
    if transition is not None:
        report["role_case_transition"] = transition
    report["conflicts"].extend(role_scope_conflicts(template, before, after, case_root="roles" if mapping else None))
    for target in sorted(previous_files.keys() | after["files"].keys()):
        previous = previous_files.get(target)
        desired = after["files"].get(target)
        try:
            physical = "roles/" + target.removeprefix("Roles/") if mapping and target.startswith("Roles/") else target
            current = file_hash(template / physical)
        except (UpdateError, OSError) as error:
            report["conflicts"].append(f"{target}: {error}")
            continue
        if previous:
            if current != previous["sha256"] and not (
                retire_collection is None and current is None and desired is None
            ):
                report["conflicts"].append(f"managed destination was customized: {target}")
            elif desired is None:
                report["deletions"].append(target)
            elif previous != desired:
                report["updates"].append(target)
        elif current is None:
            report["additions"].append(target)
        elif current == desired["sha256"]:
            report["adoptions"].append(target)
        else:
            report["conflicts"].append(f"unmanaged destination differs from source: {target}")
    if report["conflicts"]:
        report["status"] = "conflict"
    elif before != after:
        report["status"] = "outdated"
    retired = role_retirements(before, after)
    if retired:
        report["role_retirements"] = retired
    return report


def role_retirements(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, str]]:
    result = []
    for target, entry in sorted(before["files"].items()):
        if not target.startswith("sub-agent-roles/") or target in after["files"]:
            continue
        active = role_layout(after) + "/" + target.removeprefix("sub-agent-roles/")
        if active not in after["files"] or after["files"][active]["source"] != entry["source"]:
            raise UpdateError("legacy role retirement lacks an exact source-to-active mapping")
        result.append({"legacy": target, "active": active, "source": entry["source"], "sha256": entry["sha256"]})
    return result


def role_scope_conflicts(template: Path, before: dict[str, Any], after: dict[str, Any], *, case_root: str | None = None) -> list[str]:
    """A managed index cannot silently omit project-owned role directories."""
    conflicts = []
    active_root = role_layout(after)
    entries = role_case_entries(template)
    if case_root is None and entries not in ([], [active_root]):
        conflicts.append("role directory spelling differs from the active mapping or has case aliases")
        return conflicts
    mapping = role_case_mapping(before, after)
    before_files = {mapping.get(name, name): entry for name, entry in before["files"].items()}
    for prefix in (active_root, "sub-agent-roles"):
        physical = case_root if prefix == active_root and case_root is not None else prefix
        folder = safe(template / physical)
        if not folder.exists():
            continue
        if not folder.is_dir():
            conflicts.append(f"role collection is not a directory: {prefix}")
            continue
        desired = {Path(name).parts[1] for name in after["files"] if name.startswith(prefix + "/") and len(Path(name).parts) > 2}
        previous = {Path(name).parts[1] for name in before_files if name.startswith(prefix + "/") and len(Path(name).parts) > 2}
        for child in folder.iterdir():
            safe(child)
            if not child.is_dir() or child.name in desired:
                continue
            if prefix == "sub-agent-roles":
                if role_retirements(before, after) and child.name not in previous and any((child / name).exists() for name in ("AGENTS.md", "ROLE.md")):
                    conflicts.append(f"unmanaged legacy role needs reviewed transition: {prefix}/{child.name}")
                continue
            files = [item for item in child.rglob("*") if safe(item).is_file()]
            names = [prefix + "/" + item.relative_to(folder).as_posix() for item in files]
            retiring = child.name in previous and all(name in before_files and name not in after["files"] for name in names)
            if not retiring:
                conflicts.append(f"unmanaged role directory needs explicit adoption: {prefix}/{child.name}")
    return conflicts


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe(path.parent)
    fd, temporary = tempfile.mkstemp(prefix=".template-update-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        safe(path)
        _ontology_checkpoint(targets=False)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked(root: Path, *, readonly: bool = False) -> Iterator[None]:
    path = safe(root / LOCK)
    if readonly and not path.exists():
        _ontology_checkpoint(targets=False)
        yield
        return
    if not readonly:
        path.parent.mkdir(parents=True, exist_ok=True)
        safe(path.parent)
    flags = os.O_RDONLY if readonly else os.O_RDWR | os.O_CREAT
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise UpdateError("template lock must be a regular non-aliased file")
        try:
            fcntl.flock(fd, (fcntl.LOCK_SH if readonly else fcntl.LOCK_EX) | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise UpdateError("template is busy; another update or initializer holds the lock") from error
        _ontology_checkpoint()
        yield
    finally:
        os.close(fd)


def make_pending(
    before: dict[str, Any], snap: dict[str, Any],
    *, retirement: dict[str, str] | None = None, root: Path | None = None,
    reviewed_case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    after = snap["state"]
    payloads = {
        target: base64.b64encode(snap["generated"][target] if "generated" in entry else snap["blobs"][entry["source"]]).decode("ascii")
        for target, entry in after["files"].items()
        if before["files"].get(target) != entry
    }
    pending = {"schema_version": 1, "before": before, "after": after, "payloads": payloads}
    if role_case_mapping(before, after):
        if root is None:
            raise UpdateError("role case transition needs current bytes for recovery")
        preview = case_preview(root, before, after)
        if reviewed_case is not None and preview != reviewed_case:
            raise UpdateError("role case transition changed after preflight")
        pending["role_case_transition"] = case_record(root, preview)
    if retirement is not None:
        pending["retirement"] = retirement
    retired = role_retirements(before, after)
    if retired:
        if root is None:
            raise UpdateError("role retirement needs current legacy bytes for recovery")
        retained = {}
        for entry in retired:
            raw = read_file(root / TEMPLATE / entry["legacy"])
            if digest(raw) != entry["sha256"]:
                raise UpdateError("legacy role changed before recovery capture")
            retained[entry["legacy"]] = base64.b64encode(raw).decode("ascii")
        pending["role_retirement"] = {"schema_version": 1, "mapping": retired, "payloads": retained}
    return pending


def recover(root: Path, pending: dict[str, Any]) -> None:
    """Resume only if every destination still has its recorded old or new bytes."""
    if not isinstance(pending, dict) or pending.get("schema_version") != 1:
        raise UpdateError("invalid pending template update")
    before = validate_state(pending.get("before"))
    after = validate_state(pending.get("after"))
    active_root = role_layout(after)
    active_index = active_root + "/INDEX.md"
    required = ({name.replace("Roles/", active_root + "/", 1) for name in BASELINE_FILES}
                if active_index in after["files"] else LEGACY_BASELINE_FILES)
    if not required.issubset(after["files"]):
        raise UpdateError("pending update would remove required template governance")
    state_raw = read_file(root / STATE, optional=True)
    current_state = load_state(root)
    if current_state not in (before, after):
        raise UpdateError("template state changed after the interrupted update")
    retirement = pending.get("retirement")
    if retirement is not None:
        if (not isinstance(retirement, dict)
                or set(retirement) != {"collection", "state_sha256"}
                or not isinstance(retirement["state_sha256"], str)
                or not HASH.fullmatch(retirement["state_sha256"])):
            raise UpdateError("invalid pending collection retirement")
        retirement_targets(root, before, after, retirement["collection"])
        # Recheck the surviving sources before resuming any partial deletion.
        retirement_targets(root, before, snapshot(root)["state"], retirement["collection"])
        if current_state == before and (
            state_raw is None or digest(state_raw) != retirement["state_sha256"]
        ):
            raise UpdateError("retirement state digest changed after the interrupted update")
    elif set(before["collections"]) - set(after["collections"]):
        raise UpdateError("pending collection loss requires an explicit retirement record")
    payloads = pending.get("payloads")
    expected = {
        target for target, entry in after["files"].items()
        if before["files"].get(target) != entry
    }
    if not isinstance(payloads, dict) or set(payloads) != expected:
        raise UpdateError("pending update payload inventory is invalid")
    decoded: dict[str, bytes] = {}
    for target, payload in payloads.items():
        try:
            decoded[target] = base64.b64decode(payload, validate=True)
        except (ValueError, TypeError, binascii.Error) as error:
            raise UpdateError("pending update payload is invalid") from error
        if digest(decoded[target]) != after["files"][target]["sha256"]:
            raise UpdateError(f"pending update payload checksum mismatch: {target}")
    template = safe(root / TEMPLATE)
    if not template.is_dir():
        raise UpdateError("template directory is missing during recovery")
    case = pending.get("role_case_transition")
    case_location = validate_case_record(root, case, before, after)
    mapping = role_case_mapping(before, after)
    previous_files = {mapping.get(name, name): entry for name, entry in before["files"].items()}
    scope_conflicts = role_scope_conflicts(template, before, after, case_root=case_location)
    if scope_conflicts:
        raise UpdateError("role ownership conflict", report={"status": "conflict", "conflicts": scope_conflicts})
    if active_index in after["files"]:
        inputs = {}
        for target, binding in role_index_inputs(after["files"], active_root).items():
            raw = decoded[target] if target in decoded else read_file(template / target)
            if digest(raw) != binding["sha256"]:
                raise UpdateError("generated role index input changed during recovery")
            inputs[target] = raw
        if digest(render_role_index(inputs, active_root)) != after["files"][active_index]["sha256"]:
            raise UpdateError("generated role index does not match its frozen role pairs")
    retired = role_retirements(before, after)
    retained = pending.get("role_retirement")
    archive_raw = None
    if retired:
        if (not isinstance(retained, dict) or set(retained) != {"schema_version", "mapping", "payloads"}
                or type(retained["schema_version"]) is not int or retained["schema_version"] != 1
                or retained["mapping"] != retired or not isinstance(retained["payloads"], dict)
                or set(retained["payloads"]) != {entry["legacy"] for entry in retired}):
            raise UpdateError("legacy role retirement recovery inventory is invalid")
        for entry in retired:
            try:
                raw = base64.b64decode(retained["payloads"][entry["legacy"]], validate=True)
            except (ValueError, TypeError, binascii.Error) as error:
                raise UpdateError("legacy role recovery payload is invalid") from error
            if digest(raw) != entry["sha256"]:
                raise UpdateError("legacy role recovery payload checksum mismatch")
        archive_raw = encoded(retained)
    elif retained is not None:
        raise UpdateError("unexpected legacy role retirement record")
    targets = sorted(previous_files.keys() | after["files"].keys())
    conflicts = []
    observed: dict[str, str | None] = {}
    for target in targets:
        old = previous_files.get(target, {}).get("sha256")
        new = after["files"].get(target, {}).get("sha256")
        physical = case_location + "/" + target.removeprefix("Roles/") if case_location and target.startswith("Roles/") else target
        observed[target] = file_hash(template / physical)
        if observed[target] not in {old, new}:
            conflicts.append(f"destination changed during interrupted update: {target}")
    if conflicts:
        raise UpdateError("recovery conflict", report={"status": "conflict", "conflicts": conflicts})
    archives = ([] if archive_raw is None else [archive_raw]) + ([] if case is None else [encoded(case)])
    for raw in archives:
        archive = root / CONTROL / "role-layout-history" / (digest(raw) + ".json")
        existing = read_file(archive, optional=True)
        if existing is not None and existing != raw:
            raise UpdateError("legacy role recovery archive was customized")
        if existing is None:
            atomic_write(archive, raw, 0o600)
    if case is not None:
        finish_case_rename(root, case, before, after)
    for target in targets:
        desired = after["files"].get(target)
        new = None if desired is None else desired["sha256"]
        candidate = template / target
        if file_hash(candidate) != observed[target]:
            raise UpdateError(f"destination changed during update: {target}")
        if observed[target] == new:
            continue
        if desired is None:
            safe(candidate).unlink()
            parent = candidate.parent
            while parent != template:
                safe(parent)
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
        else:
            atomic_write(candidate, decoded[target], desired["mode"])
    for target in targets:
        expected_hash = after["files"].get(target, {}).get("sha256")
        if file_hash(template / target) != expected_hash:
            raise UpdateError(f"post-write verification failed: {target}")
    if case is not None:
        validate_case_record(root, case, before, after)
    if role_scope_conflicts(template, after, after):
        raise UpdateError("role directory changed during update; preserve it for reviewed recovery")
    if read_file(root / STATE, optional=True) != state_raw:
        raise UpdateError("template state changed during update")
    if current_state != after:
        atomic_write(root / STATE, encoded(after), 0o600)
    safe(root / PENDING).unlink()


def update(
    root: Path, command: str, *, retire_collection: str | None = None,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    root = safe(root.absolute())
    if command not in {"check", "apply"}:
        raise UpdateError("expected check or apply")
    if (retire_collection is None) != (expected_state_sha256 is None):
        raise UpdateError("collection retirement requires both collection and expected state digest")
    if expected_state_sha256 is not None and (
        not isinstance(expected_state_sha256, str) or not HASH.fullmatch(expected_state_sha256)
    ):
        raise UpdateError("expected state digest must be a lowercase SHA256")
    if not root.is_dir():
        raise UpdateError("depot root is missing")
    with locked(root, readonly=command == "check"):
        pending_raw = read_file(root / PENDING, optional=True)
        recovered = pending_raw is not None
        if recovered:
            if retire_collection is not None:
                raise UpdateError("pending update must recover with ordinary apply before starting retirement")
            if command == "check":
                raise UpdateError("interrupted update needs recovery; run apply")
            recover(root, json_document(pending_raw))
        before = load_state(root)
        if expected_state_sha256 is not None and file_hash(root / STATE) != expected_state_sha256:
            raise UpdateError("expected state digest is stale or the recorded state is missing")
        first = snapshot(root)
        report = plan(root, before, first["state"], retire_collection=retire_collection)
        if report["conflicts"]:
            raise UpdateError("template update has conflicts", report=report)
        second = snapshot(root)
        if first["fingerprint"] != second["fingerprint"]:
            raise UpdateError("depot source changed during preflight; retry after edits settle")
        if load_state(root) != before:
            raise UpdateError("template state changed during preflight")
        if expected_state_sha256 is not None and file_hash(root / STATE) != expected_state_sha256:
            raise UpdateError("expected state digest changed during preflight")
        # Repeat the destination preflight after reading the source a second time.
        final_report = plan(root, before, second["state"], retire_collection=retire_collection)
        if final_report != report:
            raise UpdateError("template destination changed during preflight")
        if command == "apply" and report["status"] == "outdated":
            retirement = None if retire_collection is None else {
                "collection": retire_collection, "state_sha256": expected_state_sha256,
            }
            pending = make_pending(before, second, retirement=retirement, root=root,
                                   reviewed_case=report.get("role_case_transition"))
            atomic_write(root / PENDING, encoded(pending), 0o600)
            recover(root, pending)
            report["status"] = "applied"
        report["recovered"] = recovered
        return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).absolute().parents[1])
    parser.add_argument("command", choices=("check", "apply"))
    parser.add_argument("--retire-collection", help="exact recorded collection, already absent and unmapped")
    parser.add_argument("--expected-state-sha256", help="SHA256 of the current raw state.json; required for retirement")
    args = parser.parse_args(argv)
    try:
        report = update(
            args.project_root, args.command, retire_collection=args.retire_collection,
            expected_state_sha256=args.expected_state_sha256,
        )
    except UpdateError as error:
        print(json.dumps(error.report, sort_keys=True))
        return 2
    except OSError as error:
        print(json.dumps({"status": "blocked", "conflicts": [str(error)]}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 1 if report["status"] == "outdated" else 0



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
    return UpdateError(code + ": " + message, report=details)

ONTOLOGY_GUARDED_ACTIONS = ['update', 'recover']
update = _ontology_guard_adapter(update, 'template', 'root', ['Projects/Sys4AI-Template-Project', '.sys4ai/template-update/state.json'])
recover = _ontology_guard_adapter(recover, 'template', 'root', ['Projects/Sys4AI-Template-Project', '.sys4ai/template-update/state.json'])

if __name__ == "__main__":
    raise SystemExit(main())
