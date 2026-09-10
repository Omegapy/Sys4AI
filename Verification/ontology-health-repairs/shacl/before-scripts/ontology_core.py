"""Confined, strict local JSON-LD profile; no network, services or implicit writes."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
import copy
import hashlib
import json
import os
import re
import stat
import tempfile
import fcntl
from contextlib import contextmanager

VERSION = "1.0.0"
CORE = "urn:sys4ai:ontology:core:"
PROJECT = "urn:sys4ai:ontology:project:"
CONTEXT_PATH = "ONTOLOGY/contexts/context-v1.jsonld"
COMMON_KEYS = {"@id", "@type", "kind", "label", "definition", "lifecycle", "module", "sources", "fact_kind", "aliases", "scope_note", "examples", "non_examples", "ambiguity_with", "deprecation_reason", "replacement", "history"}
KIND_KEYS = {"concept": set(), "instance": set(), "predicate": {"domain", "range", "acyclic", "cardinality", "qualifiers"}, "relation": {"subject", "predicate", "object", "qualifiers"}, "binding": {"entity", "binding_type"}}
RECORD_KEYS = sorted(COMMON_KEYS | set().union(*KIND_KEYS.values()))
TRUSTED_CONTEXT = {"@context": {"@version": 1.1, **{k: CORE + "field:" + k for k in RECORD_KEYS if not k.startswith("@")} }}
DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
IDENTITY_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,79}\Z")
ID_RE = re.compile(r"urn:sys4ai:ontology:(?:core:|project:[a-z0-9][a-z0-9-]{0,79}:)[A-Za-z0-9][A-Za-z0-9._:-]{0,159}\Z")


class OntologyError(ValueError):
    def __init__(self, code, message, *, path=None, record_id=None):
        super().__init__(message)
        self.code, self.message, self.path, self.record_id = code, str(message)[:1000], path, record_id

    def as_dict(self):
        return {"code": self.code, "message": self.message, "path": self.path, "record_id": self.record_id, "severity": "error"}


def require(condition, code, message, **location):
    if not condition:
        raise OntologyError(code, message, **location)


def exact(value, required, optional=(), *, path=None):
    require(isinstance(value, dict), "invalid_object", "Expected an object.", path=path)
    require(set(required) <= set(value) <= set(required) | set(optional), "unsupported_fields", "Missing required fields or unsupported profile fields: " + ", ".join(sorted((set(required)-set(value)) | (set(value)-set(required)-set(optional)))), path=path)


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def sha256(value):
    if isinstance(value, Path):
        value = read_bytes(value)
    return hashlib.sha256(value).hexdigest()


def relative_path(value):
    require(isinstance(value, str) and value and "\\" not in value and "\x00" not in value, "unsafe_path", "Expected a nonempty relative POSIX path.")
    p = PurePosixPath(value)
    require(not p.is_absolute() and all(x not in {"", ".", ".."} for x in value.split("/")) and not any(ord(c)<32 for c in value), "unsafe_path", "Absolute, traversal, empty and control-character paths are forbidden.", path=value)
    return p


def safe_path(root, relative, *, must_exist=True):
    root = Path(root)
    rel = relative_path(relative)
    candidate = root
    for component in rel.parts:
        candidate /= component
        require(not candidate.is_symlink(), "unsafe_symlink", "Symlink components are forbidden.", path=relative)
    require(candidate.resolve(strict=False).is_relative_to(root.resolve(strict=True)), "unsafe_path", "Path escaped selected project root.", path=relative)
    if must_exist:
        require(candidate.exists(), "missing_file", "Selected file or directory is absent.", path=relative)
    return candidate


def read_bytes(path, *, max_bytes=2_000_000):
    path = Path(path)
    try:
        parent = directory_fd(path.absolute().parent)
        try:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        finally:
            os.close(parent)
        with os.fdopen(fd, "rb") as stream:
            st = os.fstat(stream.fileno())
            require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, "unsafe_file", "Expected a regular file without hardlink aliases.", path=str(path))
            require(st.st_size <= max_bytes, "input_too_large", "Selected file exceeds the bounded input size.", path=str(path))
            data = stream.read(max_bytes + 1)
            require(len(data) <= max_bytes, "input_too_large", "Selected file exceeds the bounded input size.", path=str(path))
            return data
    except OSError as exc:
        raise OntologyError("unavailable_file", "Cannot read selected regular file.", path=str(path)) from exc


def directory_fd(path, *, create=False):
    """Open every directory without following symlinks; caller owns the returned fd."""
    p = Path(path).absolute()
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in p.parts[1:]:
            if create:
                try: os.mkdir(part, mode=0o755, dir_fd=fd)
                except FileExistsError: pass
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = next_fd
        return fd
    except BaseException:
        os.close(fd); raise


def atomic_write(root, relative, data, expected):
    """Expected-byte replacement in a confined opened directory, followed by fsync."""
    path = safe_path(root, relative, must_exist=False)
    fd = directory_fd(path.parent, create=True)
    temporary = ".ontology-" + os.urandom(12).hex()
    try:
        actual = sha256(read_bytes(path)) if path.exists() else None
        require(actual == expected, "write_conflict", "Destination changed before replacement.", path=relative)
        out = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        with os.fdopen(out, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        actual = sha256(read_bytes(path)) if path.exists() else None
        require(actual == expected, "write_conflict", "Destination changed at replacement boundary.", path=relative)
        require(os.fstat(fd).st_ino == os.stat(path.parent, follow_symlinks=False).st_ino, "write_conflict", "Destination directory identity changed.", path=relative)
        safe_path(root, relative, must_exist=False)
        os.replace(temporary, path.name, src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
        require(sha256(read_bytes(path)) == sha256(data), "write_conflict", "Written destination differs from accepted content.", path=relative)
    finally:
        try: os.unlink(temporary, dir_fd=fd)
        except FileNotFoundError: pass
        os.close(fd)


@contextmanager
def operation_lock(root, relative):
    path = safe_path(root, relative, must_exist=False)
    parent = directory_fd(path.parent, create=True)
    fd = None
    try:
        fd = os.open(path.name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent)
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, "unsafe_lock", "Lock path must be an unaliased regular file.")
        try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc: raise OntologyError("operation_locked", "A potentially active writer holds the ontology lock.") from exc
        yield
    finally:
        if fd is not None: os.close(fd)
        os.close(parent)


def decode_json(data, *, path=None):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate_json_key", "Duplicate JSON key: " + key, path=path)
            result[key] = value
        return result
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(OntologyError("invalid_json", "Non-finite JSON numbers are forbidden.", path=path)))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise OntologyError("invalid_json", "Expected strict UTF-8 JSON; YAML features are unsupported.", path=path) from exc


def read_json(path):
    return decode_json(read_bytes(path), path=str(path))


def digest(value):
    require(isinstance(value, str) and DIGEST_RE.fullmatch(value), "invalid_digest", "Expected lowercase SHA256 hex.")


def allowed_source_path(path):
    parts = relative_path(path).parts
    folded = tuple(p.casefold() for p in parts)
    forbidden_roots = {"projects", "electronics", "memory", "tasks", "control_records"}
    forbidden = {"node_modules", "__pycache__", ".git", ".sys4ai", ".venv", ".ssh", ".aws", "cache", "caches"}
    require(folded[0] not in forbidden_roots and not any(p in forbidden or p.startswith(".venv") for p in folded), "source_forbidden", "Private runtime, child projects, Tasks and memory are not ontology source bindings.", path=path)
    require(not any(p.startswith(".") for p in parts) or parts[:2] == (".agents", "skills"), "source_forbidden", "Hidden source paths are not permitted.", path=path)
    require(not re.search(r"(?:^|[._-])(secret|secrets|credential|credentials|password|token|env)(?:$|[._-])", "/".join(parts).lower()), "source_forbidden", "Sensitive source names are excluded.", path=path)
    require(not path.casefold().startswith("ontology/wiki/"), "source_forbidden", "Generated wiki content is not a canonical source.", path=path)


def parse_document(data, context_path, location):
    value = decode_json(data, path=location)
    exact(value, ("@context", "@graph"), path=location)
    require(value["@context"] == context_path, "untrusted_context", "Only the configured trusted local context is supported; remote or nested contexts are forbidden.", path=location)
    require(isinstance(value["@graph"], list) and len(value["@graph"]) <= 10000, "invalid_graph", "Expected a bounded graph array.", path=location)
    result = []
    for index, record in enumerate(value["@graph"]):
        where = f"{location}#/@graph/{index}"
        require(isinstance(record, dict), "invalid_record", "Graph entries must be objects.", path=where)
        kind = record.get("kind")
        require(isinstance(kind, str) and kind in KIND_KEYS, "unsupported_kind", "Unsupported record kind.", path=where)
        require(set(record) <= COMMON_KEYS | KIND_KEYS[kind], "unsupported_profile", "Unsupported JSON-LD or record property.", path=where, record_id=record.get("@id"))
        require(isinstance(record.get("@id"), str) and ID_RE.fullmatch(record["@id"]), "invalid_id", "Expected a stable project-separated ontology URN.", path=where)
        for key in ("label", "definition", "lifecycle", "module", "fact_kind", "scope_note", "deprecation_reason", "replacement", "subject", "predicate", "object", "entity", "binding_type"):
            if key in record:
                require(isinstance(record[key], str), "invalid_metadata", key + " must be a string.", path=where, record_id=record["@id"])
        for key in ("@type", "aliases", "examples", "non_examples", "ambiguity_with", "domain", "range"):
            if key in record:
                require(isinstance(record[key], list) and all(isinstance(v, str) for v in record[key]), "invalid_metadata", key + " must be a string array.", path=where, record_id=record["@id"])
        result.append((record, where))
    return result


def load_config(root, expected_project_id=None):
    cfg = read_json(safe_path(root, "ontology.yaml"))
    exact(cfg, ("schema_version", "project", "context", "modules", "project_files", "binding_files", "source_allowlist", "retrieval", "publication"), ("competency_files",))
    require(type(cfg["schema_version"]) is int and cfg["schema_version"] == 1, "unsupported_schema", "Unsupported ontology configuration schema.")
    p = cfg["project"]
    exact(p, ("id", "name", "purpose", "namespace", "root"))
    require(isinstance(p["id"], str) and IDENTITY_RE.fullmatch(p["id"]) and all(isinstance(p[x], str) and p[x].strip() for x in ("name", "purpose")), "unresolved_identity", "Specialize the neutral project identity, name and purpose before use.")
    require(p["root"] == "." and p["namespace"] == PROJECT+p["id"]+":", "identity_mismatch", "Project root or namespace does not match its selected identity.")
    require(expected_project_id is None or expected_project_id == p["id"], "identity_mismatch", "Caller selected a different project identity.")
    identity = safe_path(root, "project.json", must_exist=False)
    if identity.exists():
        saved = read_json(identity)
        require(saved.get("project_id") == p["id"] and saved.get("project_name") == p["name"] and saved.get("purpose") == p["purpose"], "identity_mismatch", "Ontology identity differs from project.json.")
    registry = safe_path(root, "depot/projects.json", must_exist=False)
    if registry.exists():
        own = [r for r in read_json(registry).get("projects", []) if r.get("path") == "."]
        require(len(own) == 1 and own[0].get("id") == p["id"], "identity_mismatch", "Ontology identity differs from the local registry root.")
    exact(cfg["context"], ("path", "sha256"))
    require(cfg["context"]["path"] == CONTEXT_PATH, "untrusted_context", "Only the versioned local profile context path is supported.")
    digest(cfg["context"]["sha256"])
    context_file = safe_path(root, CONTEXT_PATH)
    require(sha256(context_file) == cfg["context"]["sha256"] and read_json(context_file) == TRUSTED_CONTEXT, "untrusted_context", "Trusted context content or digest differs from the supported profile.")
    for key in ("modules", "project_files", "binding_files", "source_allowlist"):
        require(isinstance(cfg[key], list), "invalid_config", f"{key} must be an array.")
    for key, prefix in (("project_files", "ONTOLOGY/modules/project/"), ("binding_files", "ONTOLOGY/bindings/")):
        require(cfg[key] and all(isinstance(p, str) for p in cfg[key]) and len(cfg[key]) == len(set(cfg[key])), "invalid_config", f"{key} must select distinct file paths.")
        for path in cfg[key]:
            relative_path(path)
            endings = (".jsonld", ".json") if key == "binding_files" else (".jsonld",)
            require(path.startswith(prefix) and path.endswith(endings), "canonical_scope", "Canonical file lies outside its selected scope.", path=path)
    require(all(isinstance(p, str) for p in cfg["source_allowlist"]) and len(cfg["source_allowlist"]) == len(set(cfg["source_allowlist"])), "invalid_config", "Source allowlist must contain distinct file paths.")
    for path in cfg["source_allowlist"]:
        allowed_source_path(path)
        safe_path(root, path, must_exist=False)
    require(isinstance(cfg.get("competency_files", []), list), "invalid_config", "competency_files must be an array.")
    for path in cfg.get("competency_files", []):
        relative_path(path)
        require(path.startswith("ONTOLOGY/modules/project/") and path.endswith(".json"), "canonical_scope", "Project competency files must be explicit local JSON files.")
    exact(cfg["retrieval"], ("default_hops", "max_hops", "default_limit", "max_limit", "max_context_bytes"))
    r = cfg["retrieval"]
    require(all(type(v) is int for v in r.values()) and 0 <= r["default_hops"] <= r["max_hops"] <= 8 and 1 <= r["default_limit"] <= r["max_limit"] <= 100 and 1024 <= r["max_context_bytes"] <= 32000, "invalid_limits", "Retrieval settings exceed the release bounds.")
    exact(cfg["publication"], ("enabled", "binding"))
    require(type(cfg["publication"]["enabled"]) is bool, "invalid_publication", "Publication enabled must be boolean.")
    binding = cfg["publication"]["binding"]
    if binding is not None:
        exact(binding, ("actor_id", "scope", "authority"))
        require(isinstance(binding["actor_id"], str) and binding["actor_id"] and isinstance(binding["scope"], list), "invalid_publication", "Expected destination-local Director and explicit scope.")
        require(binding["scope"] and all(isinstance(p, str) for p in binding["scope"]) and set(binding["scope"]) <= {"ONTOLOGY/modules/project", "ONTOLOGY/bindings"}, "invalid_publication", "Publication binding exceeds canonical project scope.")
        require(isinstance(binding["authority"], list) and all(isinstance(v, dict) and isinstance(v.get("path"), str) for v in binding["authority"]) and {v.get("path") for v in binding["authority"]} == {"SOUL.md", "AGENTS.md", "ROLE.md"} and len(binding["authority"]) == 3, "invalid_publication", "Bind exactly the current governing source trio.")
        for ref in binding["authority"]:
            exact(ref, ("path", "sha256")); digest(ref["sha256"])
    require(not cfg["publication"]["enabled"] or binding is not None, "invalid_publication", "Enabled publication requires destination-local authority.")
    return cfg


@dataclass
class Project:
    root: Path
    config: dict
    records: list
    by_id: dict
    relations: list
    modules: list
    locations: dict
    sources: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    snapshot: dict = field(default_factory=dict)

    @property
    def project_id(self):
        return self.config["project"]["id"]

    @property
    def namespace(self):
        return self.config["project"]["namespace"]

    def context(self):
        result = copy.deepcopy(self.snapshot)
        result["snapshot_sha256"] = sha256(canonical_bytes(self.snapshot))
        return result


def check_locator(data, locator):
    require(isinstance(locator, str) and 0 < len(locator) <= 300, "invalid_locator", "Expected a bounded useful source locator.")
    if locator.startswith("section:"):
        require(locator[8:].strip() and locator[8:].strip() in data.decode("utf-8"), "invalid_locator", "Source section is absent.")
    elif re.fullmatch(r"lines?:[1-9][0-9]*(?:-[1-9][0-9]*)?", locator):
        bounds = [int(x) for x in locator.split(":")[1].split("-")]
        require(1 <= bounds[0] <= bounds[-1] <= len(data.decode("utf-8").splitlines()), "invalid_locator", "Source line locator is outside the selected file.")
    elif locator.startswith("json:"):
        value = decode_json(data)
        try:
            for part in locator[5:].strip("/").split("/") if locator[5:].strip("/") else []:
                part = part.replace("~1", "/").replace("~0", "~")
                value = value[int(part)] if isinstance(value, list) else value[part]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OntologyError("invalid_locator", "Source JSON pointer is absent.") from exc
    else:
        raise OntologyError("invalid_locator", "Supported locators are section:, line:/lines:, and json:.")


def source_status(project, source):
    exact(source, ("path", "sha256", "locator"))
    digest(source["sha256"]); allowed_source_path(source["path"])
    require(isinstance(source["locator"], str) and 0 < len(source["locator"]) <= 300 and source["locator"].startswith(("section:", "line:", "lines:", "json:")), "invalid_locator", "Expected an exact supported source locator.", path=source["path"])
    permitted = set(project.config["source_allowlist"])
    for module in project.modules:
        permitted.update(module["path"] + "/" + name for name in module["files"])
    require(source["path"] in permitted, "source_unselected", "Source is not an explicitly selected file.", path=source["path"])
    path = safe_path(project.root, source["path"], must_exist=False)
    result = {**source, "status": "unavailable", "actual_sha256": None, "diagnostic": None}
    try:
        data = read_bytes(path)
        result["actual_sha256"] = sha256(data)
        result["status"] = "current" if result["actual_sha256"] == source["sha256"] else "stale"
        if result["status"] == "current":
            check_locator(data, source["locator"])
        else:
            result["diagnostic"] = "Source bytes differ from the recorded version."
    except OntologyError as exc:
        if exc.code == "invalid_locator":
            raise
        result["diagnostic"] = "Selected source is missing or inaccessible."
    return result


def load_project(root, *, expected_project_id=None, validate=True, _overrides=None):
    selected = Path(root).absolute()
    require(selected.is_dir() and not selected.is_symlink(), "invalid_root", "Select an existing explicit project directory.")
    require(selected.resolve() == selected, "unsafe_root", "Project root must be resolved without symlink aliases.")
    cfg = load_config(selected, expected_project_id)
    overrides = _overrides or {}
    require(set(overrides) <= set(cfg["project_files"] + cfg["binding_files"] + cfg.get("competency_files", [])), "canonical_scope", "Preview override lies outside selected canonical files.")
    from ontology_modules import load_modules
    records, modules, locations, inputs = load_modules(selected, cfg)
    inputs.update({"ontology.yaml": sha256(selected / "ontology.yaml"), CONTEXT_PATH: cfg["context"]["sha256"]})
    for path in cfg.get("competency_files", []):
        competency = safe_path(selected, path, must_exist=path not in overrides)
        data = overrides[path] if path in overrides else read_bytes(competency)
        decode_json(data)
        inputs[path] = sha256(data)
    for identity_path in ("project.json", "depot/projects.json"):
        p = safe_path(selected, identity_path, must_exist=False)
        if p.exists(): inputs[identity_path] = sha256(p)
    for path in cfg["project_files"] + cfg["binding_files"]:
        data = overrides[path] if path in overrides else read_bytes(safe_path(selected, path))
        inputs[path] = sha256(data)
        for record, location in parse_document(data, CONTEXT_PATH, path):
            require(record["@id"].startswith(cfg["project"]["namespace"]), "core_redefinition", "Project records cannot redefine core or other-project identities.", path=location, record_id=record["@id"])
            require(record.get("module") == "project", "module_ownership", "Project records must belong to the project module.", path=location, record_id=record["@id"])
            require(record["@id"] not in locations, "duplicate_id", "Duplicate ontology identity.", path=location, record_id=record["@id"])
            if path in cfg["binding_files"]:
                require(record["kind"] == "binding", "binding_scope", "Only bindings belong in binding files.", path=location)
            else:
                require(record["kind"] != "binding", "binding_scope", "Bindings belong in explicit binding files.", path=location)
            records.append(record); locations[record["@id"]] = location
    records.sort(key=lambda record: record["@id"])
    project = Project(selected, cfg, records, {r["@id"]: r for r in records}, [r for r in records if r["kind"] == "relation"], modules, locations)
    seen = set()
    for record in records:
        sources = record.get("sources", [])
        require(isinstance(sources, list), "invalid_sources", "Sources must be an array.", path=locations[record["@id"]], record_id=record["@id"])
        for source in sources:
            key = canonical_bytes(source)
            if key not in seen:
                project.sources.append(source_status(project, source)); seen.add(key)
    project.sources.sort(key=lambda x: (x["path"], x["sha256"], x["locator"]))
    for source in project.sources:
        inputs[source["path"]] = source["actual_sha256"]
        if source["status"] != "current":
            project.diagnostics.append({"code": "source_" + source["status"], "message": source["diagnostic"], "path": source["path"], "record_id": None, "severity": "warning"})
    helpers = {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("ontology*.py")) if not p.is_symlink()}
    project.snapshot = {"project_id": project.project_id, "profile_version": VERSION, "generator_version": VERSION, "inputs": dict(sorted(inputs.items())), "modules": [{k: m[k] for k in ("id", "version", "path", "sha256", "manifest_sha256")} for m in modules], "sources": copy.deepcopy(project.sources), "helpers": helpers}
    from ontology_validate import validate_records
    findings = validate_records(project)
    project.diagnostics.extend(findings)
    project.diagnostics.sort(key=lambda d: (d["code"], d.get("record_id") or "", d.get("path") or ""))
    if validate and any(d["severity"] == "error" for d in findings):
        d = next(d for d in findings if d["severity"] == "error")
        raise OntologyError(d["code"], d["message"], path=d["path"], record_id=d["record_id"])
    return project


def assert_current(project):
    require(not any(s["status"] != "current" for s in project.sources), "source_not_current", "Explicit builds/publication require current selected source bytes.")
    for path, expected in project.snapshot["inputs"].items():
        p = safe_path(project.root, path, must_exist=False)
        actual = sha256(p) if p.exists() else None
        require(actual == expected, "input_changed", "Selected input changed after loading.", path=path)
    helpers = {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("ontology*.py")) if not p.is_symlink()}
    require(helpers == project.snapshot["helpers"], "helper_changed", "Ontology helper files changed after loading.")
