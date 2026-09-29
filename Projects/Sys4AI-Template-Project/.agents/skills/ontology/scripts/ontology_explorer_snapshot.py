"""Coherent memory-only Explorer views; no publisher, authoring or optional imports.

``open_store`` compiles a private read closure from captured, checked source bytes.
The service must include its complete installed asset/build/CLI manifest in
``package_files`` and compare ``package.manifest``/``loaded_digests`` in its worker
handshake. Deadlines here are cooperative; the owning supervisor must enforce
opaque parser/loader deadlines and RSS. No on-disk cache or lock is created.
"""
from __future__ import annotations

import builtins
import _imp
import importlib.machinery
from contextlib import contextmanager
from dataclasses import dataclass
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import sys
import threading
import time
from types import MappingProxyType, ModuleType
import uuid

VERSION = "1.0.0"
LOCK = "control_records/ontology/publication.lock"
FAMILIES = {"ordinary": "control_records/ontology", "integration": "control_records/ontology/integrations"}
OP_RE = re.compile(r"ONTOP-[A-Za-z0-9-]{4,100}\Z")
DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
INTEGRATION_TARGETS = ("ONTOLOGY/modules/project/curator.jsonld", "ONTOLOGY/bindings/curator.jsonld",
                       "ONTOLOGY/modules/project/curator-competency.json", "ontology.yaml")
DEFAULT_LIMITS = {"selected_files": 512, "selected_input_bytes": 32 * 1024**2,
                  "source_files": 512, "records": 60000, "relationships": 50000,
                  "journal_files": 4096, "journal_bytes": 32 * 1024**2,
                  "snapshot_bytes": 32 * 1024**2, "request_seconds": 5}
MINIMUM_LIMITS = {"relationships": 0, "snapshot_bytes": 1048576, "selected_input_bytes": 1048576, "journal_bytes": 1048576}
MESSAGES = {
    "snapshot_changed": "Knowledge changed. Refresh the current reading view.",
    "package_changed": "The reader package changed. Reopen with a verified current package.",
    "canonical_invalid": "Selected canonical knowledge failed validation.",
    "presentation_invalid": "Selected reader configuration failed validation.",
    "configuration_needed": "Specialize the selected project configuration before opening the reader.",
    "identity_mismatch": "Configuration does not match the selected project.",
    "source_unavailable": "The selected source is unavailable.",
    "source_locator_invalid": "The recorded locator is invalid for current source bytes.",
    "service_busy": "The local reader is at its request capacity.",
    "knowledge_updating": "A coherent current knowledge view is not yet available.",
    "package_incomplete": "The installed reader package is incomplete.",
    "resource_limit": "This read cannot fit the selected resource limits. Narrow the request.",
    "deadline_exceeded": "The bounded local read deadline expired.",
}


class SnapshotError(ValueError):
    """Fixed safe diagnostics only. Filesystem/parser text never crosses this API."""
    def __init__(self, code):
        self.code = code
        super().__init__(MESSAGES[code])

    def as_dict(self):
        return {"code": self.code, "message": str(self)}


def _need(condition, code="knowledge_updating"):
    if not condition:
        raise SnapshotError(code)


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def _is_digest(value):
    return isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None


def _exact(value, required, optional=()):
    _need(isinstance(value, dict) and set(required) <= value.keys() <= set(required) | set(optional))


def _json(raw, code="canonical_invalid"):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate")
            result[key] = value
        return result
    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
        def depth(value, level=0):
            if level > 16:
                raise ValueError("depth")
            if isinstance(value, dict):
                for child in value.values(): depth(child, level + 1)
            elif isinstance(value, list):
                for child in value: depth(child, level + 1)
        depth(result)
        return result
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise SnapshotError(code) from None


def validate_configuration_shape(value, schema):
    """Evaluate the pinned configuration schema's finite keyword vocabulary.

    This is not a general JSON Schema implementation or a remote resolver.
    Exact canonical selector/source semantics belong to the reader adapter.
    """
    def matches(v, rule):
        supported = {"$ref", "$defs", "$schema", "title", "description", "default", "type", "const", "enum",
                     "allOf", "anyOf", "oneOf", "not", "properties", "required", "additionalProperties", "items",
                     "minItems", "maxItems", "uniqueItems", "minLength", "maxLength", "pattern", "minimum", "maximum",
                     "x-contract", "x-semantic-validation", "x-max-utf8-bytes", "x-json-token-type"}
        _need(isinstance(rule, dict) and rule.keys() <= supported, "package_incomplete")
        if "$ref" in rule:
            ref = rule["$ref"]
            _need(ref.startswith("#/$defs/"), "package_incomplete")
            if not matches(v, schema["$defs"][ref[8:]]): return False
        types = {"object": lambda x: type(x) is dict, "array": lambda x: type(x) is list,
                 "string": lambda x: type(x) is str, "integer": lambda x: type(x) is int,
                 "boolean": lambda x: type(x) is bool, "null": lambda x: x is None}
        if "type" in rule and not types[rule["type"]](v): return False
        if "const" in rule and (type(v) is not type(rule["const"]) or v != rule["const"]): return False
        if "enum" in rule and not any(type(v) is type(x) and v == x for x in rule["enum"]): return False
        for key, pred in (("allOf", all), ("anyOf", any)):
            if key in rule and not pred(matches(v, r) for r in rule[key]): return False
        if "oneOf" in rule and sum(matches(v, r) for r in rule["oneOf"]) != 1: return False
        if "not" in rule and matches(v, rule["not"]): return False
        if type(v) is dict:
            props = rule.get("properties", {})
            if not set(rule.get("required", ())) <= v.keys(): return False
            if rule.get("additionalProperties") is False and not v.keys() <= props.keys(): return False
            for k, x in v.items():
                if k in props and not matches(x, props[k]): return False
        if type(v) is list:
            if not rule.get("minItems", 0) <= len(v) <= rule.get("maxItems", 100000): return False
            if rule.get("uniqueItems") and len({canonical_bytes(x) for x in v}) != len(v): return False
            if "items" in rule and not all(matches(x, rule["items"]) for x in v): return False
        if type(v) is str:
            if not rule.get("minLength", 0) <= len(v) <= rule.get("maxLength", 2000000): return False
            if len(v.encode()) > rule.get("x-max-utf8-bytes", 8000000): return False
            if "pattern" in rule and re.fullmatch(rule["pattern"], v) is None: return False
        if type(v) is int:
            if not rule.get("minimum", -10**20) <= v <= rule.get("maximum", 10**20): return False
        return True
    _need(matches(value, schema), "presentation_invalid")


def _relative(value):
    _need(isinstance(value, str) and value and len(value.encode("utf-8")) <= 1024
          and not value.startswith("/") and "\\" not in value
          and all(part not in ("", ".", "..") for part in value.split("/"))
          and not any(ord(c) < 32 or ord(c) == 127 for c in value), "canonical_invalid")
    return value


def _identity(st):
    return (st.st_dev, st.st_ino)


def _directory(path):
    """Descriptor walk from /, never resolve a symlink or create a directory."""
    path = Path(path).absolute()
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def _file(path, maximum=2_000_000):
    parent = _directory(Path(path).parent)
    try:
        fd = os.open(Path(path).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        before = os.fstat(fd)
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1)
        _need(before.st_size <= maximum, "resource_limit")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(maximum + 1)
        _need(len(raw) <= maximum, "resource_limit")
        after = os.fstat(fd)
        _need((_identity(before), before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
              (_identity(after), after.st_size, after.st_mtime_ns, after.st_ctime_ns), "snapshot_changed")
        return raw
    finally:
        os.close(fd)


def _chain(root, relative):
    """An absent marker binds every existing ancestor, not merely the leaf."""
    fd = _directory(root)
    values = [(".", *_identity(os.fstat(fd)))]
    parts = relative.split("/")
    try:
        for index, part in enumerate(parts):
            try:
                st = os.stat(part, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                return tuple(values + [("/".join(parts[:index+1]), "absent")])
            _need(not stat.S_ISLNK(st.st_mode))
            values.append(("/".join(parts[:index+1]), *_identity(st), stat.S_IFMT(st.st_mode), st.st_nlink))
            if index < len(parts)-1:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd); fd = child
        return tuple(values)
    finally:
        os.close(fd)


def _tree(root, relative, max_files):
    """Bounded descriptor-relative file-set inventory, including empty directories."""
    result = []
    def visit(fd, prefix):
        # scandir is incremental; stop before admitting an unbounded directory.
        with os.scandir(fd) as items:
            for item in items:
                name = prefix + item.name
                _relative(name)
                st = item.stat(follow_symlinks=False)
                _need(not stat.S_ISLNK(st.st_mode))
                _need(len(result) < max_files, "resource_limit")
                if stat.S_ISDIR(st.st_mode):
                    result.append((name + "/", "directory"))
                    child = os.open(item.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try: visit(child, name + "/")
                    finally: os.close(child)
                else:
                    _need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1)
                    result.append((name, "file"))
    fd = _directory(Path(root) / relative)
    try: visit(fd, "")
    finally: os.close(fd)
    return tuple(sorted(result))


class VerifiedPackage:
    """Trusted startup input, never populated from a browser or canonical document.

    Captures all ontology*.py and project_app*.py helper bytes. Only explicitly named modules may
    execute, through a private import function; normal sys.modules entries and
    bytecode caches are ignored. Other package members (schema, assets, CLI,
    package/lock/build) are supplied by the launcher as an exact path map.
    """
    def __init__(self, scripts, package_files, *, allowed_modules=("ontology_core", "ontology_modules", "ontology_validate", "ontology_explorer_snapshot")):
        self.scripts = Path(scripts).absolute()
        _need(isinstance(package_files, dict) and len(package_files) <= 512, "package_incomplete")
        self.package_files = {str(k): Path(v).absolute() for k, v in package_files.items()}
        self.allowed_modules = frozenset(allowed_modules)
        self.changed = False
        self.error_type = SnapshotError
        self.modules = {}
        self.loaded_digests = {}
        self._names = []
        self._prefix = "_explorer_verified_" + uuid.uuid4().hex + "_"
        self._stdlib = Path(sys._stdlib_dir).resolve(strict=True)
        self._stdlib_paths = [str(self._stdlib), str(self._stdlib / "lib-dynload")]
        try:
            self.helpers = self._helpers()
            self.raw, self.member_bytes, captured = {}, {}, {}
            total = 0
            for key, path, destination, maximum in (
                [(name, self.scripts / name, self.raw, 2_000_000) for name in self.helpers] +
                [(name, path, self.member_bytes, 8 * 1024**2) for name, path in self.package_files.items()]
            ):
                if path not in captured:
                    _need(len(captured) < 512, "resource_limit")
                    # Enforce remaining aggregate budget before allocation.
                    raw = _file(path, min(maximum, 32 * 1024**2 - total))
                    total += len(raw)
                    _need(total <= 32 * 1024**2, "resource_limit")
                    captured[path] = raw
                destination[key] = captured[path]
            _need({k:digest(v) for k,v in self.raw.items()} == self.helpers, "package_changed")
            self.manifest = {"schema": 1, "helpers": self.helpers,
                             "members": {k: digest(v) for k, v in self.member_bytes.items()},
                             "interpreter": {"implementation": platform.python_implementation(), "version": platform.python_version()}}
            self.code_epoch = digest(canonical_bytes(self.manifest))
            self.verify()
            self._audit_stdlib()
        except (OSError, SnapshotError):
            raise SnapshotError("package_incomplete") from None

    def _helpers(self):
        fd = _directory(self.scripts)
        names = []
        try:
            with os.scandir(fd) as items:
                for item in items:
                    if item.name.startswith(("ontology", "project_app")) and item.name.endswith(".py"):
                        _need(len(names) < 512, "resource_limit")
                        st = item.stat(follow_symlinks=False)
                        _need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1)
                        names.append(item.name)
            result, total = {}, 0
            for name in sorted(names):
                raw = _file(self.scripts / name, min(2_000_000, 32 * 1024**2 - total))
                total += len(raw)
                _need(total <= 32 * 1024**2, "resource_limit")
                result[name] = digest(raw)
            return result
        finally:
            os.close(fd)

    def verify(self):
        if self.changed:
            raise SnapshotError("package_changed")
        try:
            _need(self._helpers() == self.helpers, "package_changed")
            _need({k: digest(_file(v, 8 * 1024**2)) for k, v in self.package_files.items()} == self.manifest["members"], "package_changed")
            _need(all(self.helpers.get(k + ".py") == v for k, v in self.loaded_digests.items()), "package_changed")
        except (OSError, SnapshotError):
            self.changed = True
            raise SnapshotError("package_changed") from None

    def _audit_stdlib(self):
        # A stdlib-looking name is insufficient: reject preloaded ambient modules
        # and constrain dependency imports to the selected interpreter's stdlib.
        for name, module in tuple(sys.modules.items()):
            if name.split(".")[0] not in sys.stdlib_module_names or module is None: continue
            if name in ("typing.io", "typing.re"):
                parent = sys.modules.get("typing")
                _need(parent is not None and getattr(parent, name.split(".")[1], None) is module
                      and type(module).__module__ == "typing", "package_incomplete")
                continue
            spec = getattr(module, "__spec__", None)
            origin = getattr(spec, "origin", None)
            if origin in ("built-in", "frozen"): continue
            _need(isinstance(origin, str), "package_incomplete")
            path = Path(origin).resolve(strict=True)
            _need(path.is_relative_to(self._stdlib) and "site-packages" not in path.parts
                  and "dist-packages" not in path.parts, "package_incomplete")

    def _stdlib_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        self._audit_stdlib()
        machinery = importlib.machinery
        _imp.acquire_lock()
        previous = (sys.path, sys.meta_path, sys.path_hooks, sys.path_importer_cache, sys.dont_write_bytecode)
        try:
            sys.path = list(self._stdlib_paths)
            sys.meta_path = [machinery.BuiltinImporter, machinery.FrozenImporter, machinery.PathFinder]
            sys.path_hooks = [machinery.FileFinder.path_hook(
                (machinery.ExtensionFileLoader, machinery.EXTENSION_SUFFIXES),
                (machinery.SourceFileLoader, machinery.SOURCE_SUFFIXES),
                (machinery.SourcelessFileLoader, machinery.BYTECODE_SUFFIXES))]
            sys.path_importer_cache = {}
            sys.dont_write_bytecode = True
            result = builtins.__import__(name, globals, locals, fromlist, level)
            self._audit_stdlib()
            return result
        finally:
            sys.path, sys.meta_path, sys.path_hooks, sys.path_importer_cache, sys.dont_write_bytecode = previous
            _imp.release_lock()

    def load(self, name):
        _need(name in self.allowed_modules and name + ".py" in self.raw, "package_incomplete")
        if name in self.modules:
            return self.modules[name]
        self.verify()
        fullname = self._prefix + name
        module = ModuleType(fullname)
        module.__file__ = str(self.scripts / (name + ".py"))
        module.__package__ = ""
        def checked_import(selected, globals=None, locals=None, fromlist=(), level=0):
            if selected.startswith(("ontology", "project_app")):
                _need(level == 0, "package_incomplete")
                return self.load(selected)
            _need(level == 0 and selected.split(".")[0] in sys.stdlib_module_names, "package_incomplete")
            return self._stdlib_import(selected, globals, locals, fromlist, level)
        module.__dict__["__builtins__"] = {**vars(builtins), "__import__": checked_import}
        self.modules[name] = module
        sys.modules[fullname] = module  # dataclasses resolves only this private name
        self._names.append(fullname)
        try:
            raw = self.raw[name + ".py"]
            _need(digest(raw) == self.helpers[name + ".py"], "package_changed")
            exec(compile(raw, module.__file__, "exec", dont_inherit=True), module.__dict__)
            self.loaded_digests[name] = digest(raw)
            self.verify()
            return module
        except BaseException:
            self.modules.pop(name, None)
            sys.modules.pop(fullname, None)
            raise

    def close(self):
        for name in self._names: sys.modules.pop(name, None)
        self.modules.clear()
        self.raw.clear()
        self.member_bytes.clear()


def _freeze(value):
    if isinstance(value, dict): return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list): return tuple(_freeze(v) for v in value)
    return value


def thaw(value):
    if isinstance(value, (dict, MappingProxyType)): return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple): return [thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class FrozenProject:
    root: Path
    config: object
    records: tuple
    by_id: object
    relations: tuple
    modules: tuple
    locations: object
    sources: tuple
    diagnostics: tuple
    snapshot: object

    @property
    def project_id(self): return self.config["project"]["id"]
    @property
    def namespace(self): return self.config["project"]["namespace"]
    def context(self):
        result = thaw(self.snapshot)
        result["snapshot_sha256"] = digest(canonical_bytes(result))
        return result


@dataclass(frozen=True)
class View:
    project: FrozenProject
    snapshot_id: str
    root_scope_id: str
    code_epoch: str
    manifest: object
    presentation: object
    presentation_sha256: str | None
    source_paths: frozenset
    outgoing: object
    incoming: object
    key: tuple
    accounted_bytes: int


def _publisher(value, family):
    _exact(value, ("actor_id", "actor_kind", "grant_id", "grant_sha256", *(["task"] if family == "ordinary" else [])))
    if family == "ordinary":
        task = value["task"]
        if value["actor_kind"] == "director": _need(task is None)
        else:
            _exact(task, ("path", "sha256", "task_id", "execution_id", "generation", "assignment_id"))
            _relative(task["path"]); _need(_is_digest(task["sha256"]) and type(task["generation"]) is int and task["generation"] > 0)
    _need(value["actor_kind"] in ("director", "manager") and _is_digest(value["grant_sha256"]))
    _need(all(isinstance(value[k], str) and value[k] for k in ("actor_id", "grant_id")))


def _context(value):
    _exact(value, ("project_id", "profile_version", "generator_version", "inputs", "modules", "sources", "helpers", "snapshot_sha256"), ("advanced",))
    _need(isinstance(value["project_id"], str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", value["project_id"]) is not None)
    _need(value["profile_version"] == "1.0.0" and value["generator_version"] == "1.0.0"
          and isinstance(value["inputs"], dict) and isinstance(value["helpers"], dict)
          and isinstance(value["modules"], list) and isinstance(value["sources"], list))
    _need(value["snapshot_sha256"] == digest(canonical_bytes({k:v for k,v in value.items() if k != "snapshot_sha256"})))
    for p, h in value["inputs"].items():
        _relative(p); _need(h is None or _is_digest(h))
    _need(all(isinstance(k, str) and _is_digest(v) for k, v in value["helpers"].items()))


def _intent(value, family, op):
    _exact(value, ("schema_version", "proposal", "preview", "prior_contents", "publisher", "intent_sha256"))
    _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
    _need(_is_digest(value["intent_sha256"]) and value["intent_sha256"] == digest(canonical_bytes({k:v for k,v in value.items() if k != "intent_sha256"})))
    prop, pre = value["proposal"], value["preview"]
    ordinary = family == "ordinary"
    _exact(prop, ("schema_version", "operation_id", "operation", "reason", "changes") if ordinary else
           ("schema_version", "operation_id", "operation", "reason", "changes", "edition", "resources", "sources"))
    _need(type(prop["schema_version"]) is int and prop["schema_version"] in ((1, 2) if ordinary else (1,)))
    _need(prop["operation_id"] == op and prop["operation"] == ("publish" if ordinary else "integrate-curator"))
    _need(isinstance(prop["reason"], str) and 0 < len(prop["reason"].strip()) <= 2000)
    _need(isinstance(prop["changes"], list) and 1 <= len(prop["changes"]) <= 50)
    changes = {}
    for c in prop["changes"]:
        _exact(c, ("path", "expected_sha256", "sha256", "content"))
        p = _relative(c["path"])
        _need(p not in changes and (c["expected_sha256"] is None or _is_digest(c["expected_sha256"])))
        _need(isinstance(c["content"], str) and len(c["content"].encode()) <= 250000
              and digest(c["content"].encode()) == c["sha256"])
        changes[p] = c
    _need(isinstance(value["prior_contents"], dict) and set(value["prior_contents"]) == set(changes))
    for p, raw in value["prior_contents"].items():
        _need(raw is None or isinstance(raw, str))
        _need((digest(raw.encode()) if raw is not None else None) == changes[p]["expected_sha256"])
    _publisher(value["publisher"], family)
    if ordinary:
        _exact(pre, ("schema_version", "operation_id", "payload_sha256", "reason", "changes", "before", "after", "valid", "preview_sha256"), ("advanced_validation", "ontology_guard"))
        _need(pre["operation_id"] == op and pre["reason"] == prop["reason"]
              and pre["changes"] == [{k:c[k] for k in ("path", "expected_sha256", "sha256")} for c in prop["changes"]])
    else:
        _need(prop["edition"] == "curator-ontology-1.0.0" and tuple(changes) == INTEGRATION_TARGETS)
        for key in ("resources", "sources"):
            _need(isinstance(prop[key], dict))
            for p, h in prop[key].items(): _relative(p); _need(_is_digest(h))
        _exact(pre, ("schema_version", "operation", "proposal", "payload_sha256", "before", "after", "valid", "mutated", "preview_sha256"))
        _need(pre["operation"] == "integrate-curator" and pre["proposal"] == prop and pre["mutated"] is False)
    _need(type(pre["schema_version"]) is int and pre["schema_version"] == 1 and pre["valid"] is True)
    _need(pre["payload_sha256"] == digest(canonical_bytes(prop)))
    _need(pre["preview_sha256"] == digest(canonical_bytes({k:v for k,v in pre.items() if k != "preview_sha256"})))
    _context(pre["before"]); _context(pre["after"])
    # Review binds predecessor and target digests; never compare historical target
    # digests with today's bytes, which may belong to a later completed operation.
    for p, c in changes.items():
        _need(p in pre["after"]["inputs"] and (p in pre["before"]["inputs"] or (not ordinary and c["expected_sha256"] is None)))
        if p in pre["before"]["inputs"]: _need(pre["before"]["inputs"][p] == c["expected_sha256"])
        if p in pre["after"]["inputs"]: _need(pre["after"]["inputs"][p] == c["sha256"])
    return changes


def _file_records(rows, changes, family, *, partial=False):
    _need(isinstance(rows, list) and len(rows) == len(changes))
    seen = set()
    for row in rows:
        _exact(row, ("path", "before_sha256", "sha256", "state") if family == "ordinary" else ("path", "expected_sha256", "sha256"))
        p = row["path"]
        _need(isinstance(p, str) and p in changes and p not in seen)
        seen.add(p)
        _need(row["sha256"] == changes[p]["sha256"] and row["before_sha256" if family == "ordinary" else "expected_sha256"] == changes[p]["expected_sha256"])
        if family == "ordinary": _need(row["state"] in (("pending", "committed") if partial else ("committed",)))


def _receipt(value, intent, family, changes, *, partial=False):
    prop, pre = intent["proposal"], intent["preview"]
    required = ("schema_version", "status", "operation_id", "intent_sha256")
    if partial:
        _exact(value, (*required, "error", "recovery", *(["files"] if family == "ordinary" else [])))
        _exact(value["error"], ("code", "message"))
        _need(all(isinstance(value["error"][k], str) for k in ("code", "message")) and isinstance(value["recovery"], str))
        if family == "ordinary": _file_records(value["files"], changes, family, partial=True)
    else:
        _exact(value, (*required, "preview_sha256", "payload_sha256", "files", "publisher", "context", "projection", *(["reason"] if family == "ordinary" else ["edition", "operation"])))
        _need(value["preview_sha256"] == pre["preview_sha256"] and value["payload_sha256"] == pre["payload_sha256"])
        _need(value["publisher"] == intent["publisher"] and isinstance(value["projection"], dict))
        _context(value["context"])
        if family == "ordinary": _need(value["reason"] == prop["reason"])
        else: _need(value["edition"] == "curator-ontology-1.0.0" and value["operation"] == "integrate-curator")
        _file_records(value["files"], changes, family)
    _need(type(value["schema_version"]) is int and value["schema_version"] == 1
          and value["status"] == ("partial" if partial else "complete")
          and value["operation_id"] == prop["operation_id"] and value["intent_sha256"] == intent["intent_sha256"])


def _read_journals(root, limits, deadline):
    manifest, documents, total = {}, {}, 0
    for family, base in FAMILIES.items():
        documents[family] = {kind: {} for kind in ("intents", "receipts", "recovery")}
        for kind in documents[family]:
            relative = base + "/" + kind
            _check_time(deadline)
            chain = _chain(root, relative)
            manifest[relative] = chain
            if chain[-1][-1] == "absent": continue
            for name, typ in _tree(root, relative, limits["journal_files"] + 1):
                _need(typ == "file" and name.endswith(".json") and OP_RE.fullmatch(name[:-5]))
                _need(sum(len(v) for f in documents.values() for v in f.values()) < limits["journal_files"], "resource_limit")
                raw = _file(root / relative / name)
                total += len(raw)
                _need(total <= limits["journal_bytes"], "resource_limit")
                manifest[relative + "/" + name] = digest(raw)
                documents[family][kind][name[:-5]] = _json(raw, "knowledge_updating")
    unresolved = []
    for family, rows in documents.items():
        _need(set(rows["receipts"]) <= rows["intents"].keys() and set(rows["recovery"]) <= rows["intents"].keys())
        for op, intent in rows["intents"].items():
            changes = _intent(intent, family, op)
            if op in rows["recovery"]: _receipt(rows["recovery"][op], intent, family, changes, partial=True)
            if op in rows["receipts"]: _receipt(rows["receipts"][op], intent, family, changes)
            else: unresolved.append(frozenset(changes))
    return manifest, tuple(unresolved)


def _journals(root, limits, deadline):
    try:
        return _read_journals(root, limits, deadline)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, SnapshotError) and exc.code in ("resource_limit", "deadline_exceeded"):
            raise
        raise SnapshotError("knowledge_updating") from None


def _check_time(deadline):
    _need(time.monotonic() < deadline, "deadline_exceeded")


class SnapshotStore:
    def __init__(self, root, package, *, expected_project_id=None, limits=None, validate_view=None):
        self.validate_view = validate_view
        self.root = Path(root).absolute()
        self.error_type = SnapshotError
        self.package = package
        self.expected_project_id = expected_project_id
        self.limits = dict(DEFAULT_LIMITS)
        for k, v in (limits or {}).items():
            _need(k in self.limits and type(v) is int and MINIMUM_LIMITS.get(k, 1) <= v <= self.limits[k], "presentation_invalid")
            self.limits[k] = v
        _need(package.loaded_digests.get("ontology_explorer_snapshot") == package.helpers.get("ontology_explorer_snapshot.py"), "package_incomplete")
        try:
            _need(self.root == self.root.resolve(strict=True), "identity_mismatch")
            fd = _directory(self.root)
            try: self.root_identity = _identity(os.fstat(fd))
            finally: os.close(fd)
        except OSError: raise SnapshotError("identity_mismatch") from None
        self.schema = _json(package.member_bytes["schema"], "package_incomplete")
        self.core = package.load("ontology_core")
        self._core_read_original = self.core.read_bytes
        self._active_bytes = None
        # Private freshly compiled modules only. The unchanged loader parses and
        # validates precisely the captured bytes. Unknown file reads fail closed.
        def captured_read(path, *, max_bytes=2_000_000):
            p = str(Path(path).absolute())
            if self._active_bytes is None or p not in self._active_bytes or self._active_bytes[p] is None:
                raise self.core.OntologyError("unavailable_file", "Selected captured bytes are unavailable.")
            raw = self._active_bytes[p]
            if len(raw) > max_bytes:
                raise self.core.OntologyError("input_too_large", "Selected captured bytes exceed the limit.")
            return raw
        self.core.read_bytes = captured_read
        package.load("ontology_modules")
        package.load("ontology_validate")
        self.current = None
        self.retiring = None
        self._readers = {}
        self._mutex = threading.RLock()
        self._selected_identity = None
        self.closed = False

    def _verify_package(self):
        try: self.package.verify()
        except self.package.error_type as exc:
            raise SnapshotError(exc.code) from None

    def _root_check(self):
        try:
            fd = _directory(self.root)
            try: _need(_identity(os.fstat(fd)) == self.root_identity, "package_changed")
            finally: os.close(fd)
        except (OSError, SnapshotError):
            self.package.changed = True
            raise SnapshotError("package_changed") from None

    @contextmanager
    def _coordination(self):
        self._root_check()
        lockfd = None
        try:
            before = _chain(self.root, LOCK)
            if before[-1][-1] != "absent":
                parent = _directory((self.root / LOCK).parent)
                try: lockfd = os.open("publication.lock", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                finally: os.close(parent)
                st = os.fstat(lockfd)
                _need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1)
                _need(_identity(st) == before[-1][1:3], "snapshot_changed")
                try: fcntl.flock(lockfd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                except BlockingIOError: raise SnapshotError("knowledge_updating") from None
            yield
            _need(_chain(self.root, LOCK) == before, "snapshot_changed")
            self._root_check()
        except OSError:
            raise SnapshotError("knowledge_updating") from None
        finally:
            if lockfd is not None: os.close(lockfd)

    def _policy(self):
        try: raw = _file(self.root / "ontology-explorer.yaml")
        except FileNotFoundError: raw = None
        except OSError: raise SnapshotError("presentation_invalid") from None
        limits = dict(self.limits)
        if raw is not None:
            value = _json(raw, "presentation_invalid")
            validate_configuration_shape(value, self.schema)
            for key, val in value.get("limits", {}).items():
                if key in limits: limits[key] = min(limits[key], val)
        return raw, limits

    def _capture(self, deadline):
        raw, manifest, source_paths, module_sets = {}, {}, set(), {}
        limits = dict(self.limits)
        package_inputs = {str(self.package.scripts / p): b for p,b in self.package.raw.items()}
        package_inputs.update({str(self.package.package_files[p]): b for p,b in self.package.member_bytes.items()})
        total = sum(len(v) for v in package_inputs.values())
        admitted = set(package_inputs)
        def get(relative, *, optional=False, source=False):
            nonlocal total
            _relative(relative); _check_time(deadline)
            if relative in manifest: return raw[relative]
            absolute = str(self.root / relative)
            _need(absolute in admitted or len(admitted) < limits["selected_files"], "resource_limit")
            try:
                data = _file(self.root / relative)
                marker = {"state": "present", "sha256": digest(data), "bytes": len(data)}
            except FileNotFoundError:
                _need(optional or source, "canonical_invalid")
                data = None; marker = {"state": "unavailable" if source else "absent", "sha256": None,
                                      "chain": _chain(self.root, relative)}
            except (OSError, SnapshotError) as exc:
                if isinstance(exc, SnapshotError) and exc.code in ("resource_limit", "snapshot_changed"): raise
                _need(source, "canonical_invalid")
                data = None; marker = {"state": "unavailable", "sha256": None, "reason": "unsafe_or_unreadable"}
            if absolute not in admitted:
                total += len(data) if data else 0
                admitted.add(absolute)
            _need(total <= limits["selected_input_bytes"], "resource_limit")
            raw[relative] = data; manifest[relative] = marker
            return data
        cfg = _json(get("ontology.yaml"))
        _need(isinstance(cfg, dict), "canonical_invalid")
        # These are untrusted JSON containers. Guard shapes before discovery;
        # the unchanged canonical loader still owns complete schema semantics.
        for key in ("project", "context", "retrieval", "publication"):
            _need(isinstance(cfg.get(key), dict), "canonical_invalid")
        for key in ("project_files", "binding_files", "source_allowlist", "competency_files"):
            values = cfg.get(key, [] if key == "competency_files" else None)
            _need(isinstance(values, list) and all(isinstance(v, str) for v in values), "canonical_invalid")
        _need(isinstance(cfg.get("modules"), list) and all(isinstance(v, dict) for v in cfg["modules"]), "canonical_invalid")
        publication_binding = cfg["publication"].get("binding")
        if publication_binding is not None:
            _need(isinstance(publication_binding, dict), "canonical_invalid")
            _need(isinstance(publication_binding.get("scope"), list)
                  and all(isinstance(v, str) for v in publication_binding["scope"]), "canonical_invalid")
            _need(isinstance(publication_binding.get("authority"), list)
                  and all(isinstance(v, dict) for v in publication_binding["authority"]), "canonical_invalid")
        presentation_raw = get("ontology-explorer.yaml", optional=True)
        presentation = _json(presentation_raw, "presentation_invalid") if presentation_raw is not None else None
        if presentation is not None:
            validate_configuration_shape(presentation, self.schema)
            plimits = presentation.get("limits", {})
            _need(isinstance(plimits, dict), "presentation_invalid")
            for k in DEFAULT_LIMITS.keys() & plimits.keys():
                v = plimits[k]
                _need(type(v) is int and MINIMUM_LIMITS.get(k, 1) <= v <= DEFAULT_LIMITS[k], "presentation_invalid")
                limits[k] = min(limits[k], v)
            _need(presentation.get("project_id") is not None, "configuration_needed")
            _need(presentation.get("project_id") == cfg.get("project", {}).get("id"), "identity_mismatch")
        for relative in ("project.json", "depot/projects.json"):
            identity_raw = get(relative, optional=True)
            if identity_raw is not None:
                identity = _json(identity_raw)
                _need(isinstance(identity, dict), "canonical_invalid")
                if relative == "depot/projects.json":
                    projects = identity.get("projects", [])
                    _need(isinstance(projects, list) and all(isinstance(v, dict) for v in projects), "canonical_invalid")
        get(cfg["context"]["path"])
        graph_files = []
        selected = cfg["project_files"] + cfg["binding_files"] + cfg.get("competency_files", [])
        _need(isinstance(selected, list), "canonical_invalid")
        for relative in selected: get(relative)
        graph_files.extend(cfg["project_files"] + cfg["binding_files"])
        module_sources = set()
        for mod in cfg["modules"]:
            base = _relative(mod["path"])
            value = _json(get(base + "/manifest.json"))
            _need(isinstance(value, dict) and isinstance(value.get("files"), dict), "canonical_invalid")
            _need(isinstance(value.get("record_files"), list)
                  and all(isinstance(v, str) for v in value["record_files"]), "canonical_invalid")
            module_sets[base] = _tree(self.root, base, limits["selected_files"])
            _need({name for name, typ in module_sets[base] if typ == "file"} == set(value["files"]) | {"manifest.json"}, "canonical_invalid")
            for name in value["files"]:
                relative = base + "/" + _relative(name)
                get(relative); module_sources.add(relative)
            graph_files.extend(base + "/" + name for name in value["record_files"])
        references, records, relations = set(), 0, 0
        permitted = set(cfg["source_allowlist"]) | module_sources
        for relative in graph_files:
            document = _json(raw[relative])
            _need(isinstance(document, dict), "canonical_invalid")
            rows = document.get("@graph")
            _need(isinstance(rows, list) and len(rows) <= 10000, "canonical_invalid")
            for row in rows:
                records += 1
                _need(records <= limits["records"], "resource_limit")
                _need(isinstance(row, dict), "canonical_invalid")
                relations += row.get("kind") == "relation"
                _need(relations <= limits["relationships"], "resource_limit")
                sources = row.get("sources", [])
                _need(isinstance(sources, list) and all(isinstance(v, dict) for v in sources), "canonical_invalid")
                for source in sources:
                    self.core.allowed_source_path(source["path"])
                    _need(source["path"] in permitted, "canonical_invalid")
                    reference = {"owner_id": row["@id"], "binding_id": None, "path": source["path"], "locator": source["locator"], "recorded_sha256": source["sha256"]}
                    references.add(digest(canonical_bytes(reference)))
                    if row.get("kind") == "binding":
                        references.add(digest(canonical_bytes({**reference, "owner_id": row["entity"], "binding_id": row["@id"]})))
                    _need(len(references) <= 1024, "resource_limit")
                    source_paths.add(source["path"])
                    _need(len(source_paths) <= limits["source_files"], "resource_limit")
        canonical_paths = tuple(sorted(manifest))
        for relative in sorted(source_paths): get(relative, source=True)
        _need(len(admitted) <= limits["selected_files"] and total <= limits["selected_input_bytes"], "resource_limit")
        return {"raw": raw, "manifest": manifest, "module_sets": module_sets, "source_paths": source_paths,
                "presentation": presentation, "limits": limits, "references": len(references), "canonical_paths": canonical_paths}

    def _materialize(self, capture):
        package = self.package
        self._active_bytes = {str(self.root / p): b for p,b in capture["raw"].items()}
        self._active_bytes.update({str(package.scripts / p): b for p,b in package.raw.items()})
        try:
            project = self.core.load_project(self.root, expected_project_id=self.expected_project_id, validate=True)
        finally:
            self._active_bytes = None
        # The canonical ontology compiler records its ontology-owned helpers only.
        # App helpers are independently bound by the verified executing package.
        _need(project.context()["helpers"] == {k:v for k,v in package.helpers.items() if k.startswith("ontology")}, "package_changed")
        identity = (project.project_id, project.namespace)
        if self._selected_identity is not None and identity != self._selected_identity:
            package.changed = True
            raise SnapshotError("package_changed")
        root_scope = digest(canonical_bytes({"domain": "sys4ai-explorer-root-scope-v1", "root": str(self.root),
                            "device": str(self.root_identity[0]), "inode": str(self.root_identity[1]),
                            "project_id": identity[0], "namespace": identity[1]}))
        presentation_sha = capture["manifest"]["ontology-explorer.yaml"]["sha256"]
        additional = {"files": capture["manifest"], "module_sets": capture["module_sets"], "canonical_paths": capture["canonical_paths"]}
        snapshot = digest(canonical_bytes({"schema": 1, "root_identity_digest": root_scope, "project_id": identity[0],
                          "code_epoch": package.code_epoch, "canonical_context": project.context(),
                          "additional_inputs": additional, "adapter_version": VERSION, "presentation_sha256": presentation_sha}))
        frozen_records = tuple(_freeze(r) for r in project.records)
        by_id = MappingProxyType({r["@id"]: r for r in frozen_records})
        outgoing, incoming = {}, {}
        for relation in project.relations:
            outgoing.setdefault(relation["subject"], []).append(relation["@id"])
            incoming.setdefault(relation["object"], []).append(relation["@id"])
        accounted = len(canonical_bytes({"records": project.records, "config": project.config, "modules": project.modules,
                        "locations": project.locations, "sources": project.sources, "diagnostics": project.diagnostics,
                        "context": project.context(), "manifest": additional, "outgoing": outgoing, "incoming": incoming,
                        "presentation": capture["presentation"]}))
        _need(accounted <= capture["limits"]["snapshot_bytes"], "resource_limit")
        frozen = FrozenProject(self.root, _freeze(project.config), frozen_records, by_id,
                    tuple(by_id[r["@id"]] for r in project.relations), _freeze(project.modules), _freeze(project.locations),
                    _freeze(project.sources), _freeze(project.diagnostics), _freeze(project.snapshot))
        return View(frozen, snapshot, root_scope, package.code_epoch, _freeze(additional), _freeze(capture["presentation"]),
                    presentation_sha, frozenset(capture["source_paths"]), _freeze(outgoing), _freeze(incoming),
                    (str(self.root), self.root_identity, *identity, snapshot, package.code_epoch, VERSION, presentation_sha), accounted)

    def _validated(self, deadline, source_view=None, source_path=None, *, started=None):
        started = time.monotonic() if started is None else started
        last = "snapshot_changed"
        for _ in range(3):
            _check_time(deadline)
            self._verify_package()
            try:
                with self._coordination():
                    policy_raw, limits = self._policy()
                    deadline = min(deadline, started + limits["request_seconds"])
                    _check_time(deadline)
                    journal, unresolved = _journals(self.root, limits, deadline)
                    first = self._capture(deadline)
                    _need(first["raw"]["ontology-explorer.yaml"] == policy_raw, "snapshot_changed")
                    selected = set(first["manifest"])
                    if self.current: selected.update(self.current.manifest["files"])
                    _need(not any("ontology.yaml" in paths or "ontology-explorer.yaml" in paths or paths & selected for paths in unresolved))
                    if source_view is not None:
                        _need(source_path in source_view.source_paths, "source_unavailable")
                        old = thaw(source_view.manifest)
                        candidate = thaw(_freeze({"files": first["manifest"], "module_sets": first["module_sets"], "canonical_paths": first["canonical_paths"]}))
                        if source_path not in first["canonical_paths"]:
                            old["files"].pop(source_path, None)
                            candidate["files"].pop(source_path, None)
                        _need(old == candidate, "snapshot_changed")
                        view = source_view
                    elif self.current and canonical_bytes(thaw(self.current.manifest)) == canonical_bytes({"files": first["manifest"], "module_sets": first["module_sets"], "canonical_paths": first["canonical_paths"]}):
                        view = self.current
                    else:
                        _need(self.retiring is None, "service_busy")
                        view = self._materialize(first)
                        # The reader provides complete selector/source/process
                        # semantic validation before this candidate can be current.
                        if self.validate_view is None:
                            _need(not any((first["presentation"] or {}).get(k) for k in
                                  ("starting_ids", "categories", "predicate_labels", "process_views")), "presentation_invalid")
                        else:
                            try: self.validate_view(view)
                            except SnapshotError: raise
                            except (ValueError, TypeError, KeyError):
                                raise SnapshotError("presentation_invalid") from None
                    second = self._capture(deadline)
                    after_journal, _ = _journals(self.root, first["limits"], deadline)
                    _need(first["manifest"] == second["manifest"] and first["module_sets"] == second["module_sets"] and journal == after_journal, "snapshot_changed")
                    self._verify_package()
                    _check_time(deadline)
                return view, second
            except self.core.OntologyError as exc:
                if exc.code == "identity_mismatch": raise SnapshotError("identity_mismatch") from None
                if exc.code == "unresolved_identity": raise SnapshotError("configuration_needed") from None
                if exc.code == "invalid_locator": raise SnapshotError("source_locator_invalid") from None
                raise SnapshotError("canonical_invalid") from None
            except (OSError, KeyError, TypeError, ValueError) as exc:
                if isinstance(exc, SnapshotError):
                    if exc.code in ("snapshot_changed", "knowledge_updating"):
                        last = exc.code; continue
                    raise
                raise SnapshotError("canonical_invalid") from None
        raise SnapshotError(last)

    @contextmanager
    def lease(self, *, expected_snapshot=None, deadline=None):
        started = time.monotonic()
        deadline = min(deadline if deadline is not None else float("inf"), started + self.limits["request_seconds"])
        with self._mutex:
            _need(not self.closed, "package_changed")
            _need(sum(self._readers.values()) < 2, "service_busy")
            view, _ = self._validated(deadline, started=started)
            if view is not self.current:
                if self.current and self._readers.get(self.current.snapshot_id, 0): self.retiring = self.current
                self.current = view
                self._selected_identity = (view.project.project_id, view.project.namespace)
            _need(expected_snapshot is None or expected_snapshot == view.snapshot_id, "snapshot_changed")
            self._readers[view.snapshot_id] = self._readers.get(view.snapshot_id, 0) + 1
        try:
            yield view
        finally:
            with self._mutex:
                count = self._readers[view.snapshot_id] - 1
                if count: self._readers[view.snapshot_id] = count
                else:
                    del self._readers[view.snapshot_id]
                    if self.retiring is view: self.retiring = None

    def observe_source(self, view, relative, *, deadline=None):
        """Revalidate all inputs except one registered source, without advancing view.

        Returns fresh bounded bytes plus a marker for the source adapter to apply
        locator/tuple authority and pagination. Source identity/authorization must
        already have been resolved in ``view``. No body is retained by this store.
        """
        started = time.monotonic()
        deadline = min(deadline if deadline is not None else float("inf"), started + self.limits["request_seconds"])
        with self._mutex:
            _need(not self.closed and view.code_epoch == self.package.code_epoch, "package_changed")
            _need(view.key[0] == str(self.root) and view.key[1] == self.root_identity, "snapshot_changed")
            _, capture = self._validated(deadline, view, relative, started=started)
            return capture["raw"][relative], _freeze(capture["manifest"][relative])

    def close(self):
        with self._mutex:
            _need(not self._readers, "service_busy")
            self.closed = True
            self.current = self.retiring = None
            self.package.close()


def open_store(root, *, schema_path, scripts=None, package_files=None, expected_project_id=None, limits=None, validate_view=None):
    """Standalone/core bootstrap. Production launcher supplies all package members."""
    members = {"schema": Path(schema_path), **(package_files or {})}
    package = VerifiedPackage(scripts or Path(__file__).parent, members)
    try:
        verified = package.load("ontology_explorer_snapshot")
        return verified.SnapshotStore(root, package, expected_project_id=expected_project_id, limits=limits, validate_view=validate_view)
    except BaseException:
        package.close()
        raise
