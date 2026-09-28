"""Exact, optional semantic checks at the owning helpers' mutation boundaries.

This module grants no authority.  The public helper runs its existing authorizer
after this check.  Context variables only carry a decision down that helper's
current call stack; no reusable pass or authorization is cached.
"""
from __future__ import annotations

import argparse
import ast
from contextvars import ContextVar
from dataclasses import fields, is_dataclass
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import re
import sys
import time

ACTIVE = ContextVar("sys4ai_ontology_guard_actions", default=())
BASE = "urn:sys4ai:ontology:action:"
FAMILIES = {"ontology", "memory", "task", "trd", "plan", "role", "template", "setup"}
MAX_FILES = 10000
MAX_BYTES = 128 * 1024 * 1024
ENGINE_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
CAPABILITIES = {
    "ontology": "OntologyPublication", "memory": "MemoryMaintenance",
    "task": "TaskLifecycleManagement", "trd": "RequirementsManagement",
    "plan": "ImplementationPlanManagement", "role": "RoleCatalogManagement",
    "template": "TemplateDistribution", "setup": "ProjectCapabilitySetup",
}
PROVIDERS = {
    ".agents/skills/ontology/scripts/ontology_publication.py": "ontology",
    ".agents/skills/ontology/scripts/ontology_profiles.py": "setup",
    ".agents/skills/memory/scripts/memory_recovery.py": "memory",
    ".agents/skills/memory/scripts/memory_publish.py": "memory",
    ".agents/skills/memory/scripts/memory_capture.py": "memory",
    ".agents/skills/memory/scripts/memory_maintenance.py": "memory",
    ".agents/skills/agent-task/scripts/task_state.py": "task",
    ".agents/skills/to-trd/scripts/trd.py": "trd",
    ".agents/skills/to-implementation-plan/scripts/plan_state.py": "plan",
    ".agents/skills/manage-subagent-roles/scripts/role_catalog.py": "role",
    "tools/template_update.py": "template",
    ".agents/skills/init-new-project/scripts/init_new_project.py": "setup",
}
RULES = {"typed-input", "owned-targets", "installed-capability", "current-governance", "owner-semantics"}
LIFECYCLES = {("task", "response_transaction"): "task", ("trd", "set_status"): "trd", ("plan", "handle_set_status"): "plan"}


def validate_contract(contract):
    """Reject unknown executable meaning, rather than silently ignoring a rule."""
    fail(isinstance(contract, dict) and set(contract) == {"schema_version", "id", "semantic_profile", "shapes", "actions", "optional_actions", "lifecycles", "uncovered"}
         and contract.get("schema_version") == 1 and contract.get("semantic_profile") == "sys4ai-actions-v1",
         "guard_unsupported", "Select the supported complete typed action contract (sys4ai-actions-v1).")
    fail(set(contract["lifecycles"]) == {"task", "trd", "plan"}, "guard_unsupported", "Unsupported or missing lifecycle vocabulary.")
    for name, lifecycle in contract["lifecycles"].items():
        fail(isinstance(lifecycle, dict) and set(lifecycle) == {"identity_pattern", "transitions"}
             and isinstance(lifecycle["identity_pattern"], str) and isinstance(lifecycle["transitions"], dict)
             and lifecycle["transitions"], "guard_schema", "Malformed semantic lifecycle contract.", lifecycle=name)
        for state, after in lifecycle["transitions"].items():
            fail(isinstance(state, str) and isinstance(after, list) and len(after) == len(set(after))
                 and all(value in lifecycle["transitions"] for value in after), "guard_schema", "Lifecycle edges must resolve to declared states.", lifecycle=name)
    fail(isinstance(contract["actions"], list) and isinstance(contract["optional_actions"], list), "guard_schema", "Action definitions must be arrays.")
    for action in contract["actions"] + contract["optional_actions"]:
        fields = {"id", "family", "operation", "input_type", "target_type", "capability", "governing_sources", "dispatch", "semantic_rules", "lifecycle"}
        if action in contract["optional_actions"]:
            fields.add("applicability")
        fail(isinstance(action, dict) and set(action) == fields,
             "guard_unsupported", "Unknown or incomplete action rule contract.")
        family, operation = action["family"], action["operation"]
        fail(family in FAMILIES and isinstance(operation, str) and re.fullmatch(r"[a-z_]+", operation)
             and action["id"] == BASE + family + ":" + operation, "guard_schema", "Action identity must name its exact family and operation.")
        fail(action["input_type"] == family + "-" + operation + "-request" and action["target_type"] in {value + "-owned-artifact" for value in FAMILIES}
             and action["capability"] in {BASE + "capability:" + value for value in CAPABILITIES.values()}, "guard_unsupported", "Unsupported input, target or concrete capability type.", action_id=action["id"])
        fail(isinstance(action["semantic_rules"], list) and set(action["semantic_rules"]) == RULES and len(action["semantic_rules"]) == len(RULES)
             and action["lifecycle"] == LIFECYCLES.get((family, operation)), "guard_unsupported", "Unsupported, duplicate or missing semantic rules.", action_id=action["id"])
        fail(action["governing_sources"] == ["SOUL.md", "AGENTS.md", "ROLE.md"], "guard_unsupported", "Action governance must name the current destination-local source trio.")
        dispatch = action["dispatch"]
        fail(isinstance(dispatch, dict) and set(dispatch) == {"path", "symbol"} and PROVIDERS.get(dispatch["path"]) == family
             and dispatch["symbol"] == ("Store." + operation if family == "trd" else operation), "guard_unsupported", "Unsupported owning dispatch interface.", action_id=action["id"])
    return contract


class GuardError(ValueError):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code, self.details = code, details or {}

    def __str__(self):
        # Some owning CLIs retain only exception text. Keep their diagnostic
        # useful without serializing arguments, RDF values, or full contexts.
        selected = ["condition=" + self.code] if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", self.code) else []
        action = self.details.get("action_id")
        if isinstance(action, str) and len(action) <= 160 and re.fullmatch(r"urn:sys4ai:ontology:action:[a-z_]+:[a-z_]+", action):
            selected.append("action=" + action)
        binding = self.details.get("contract", self.details.get("configuration"))
        if isinstance(binding, dict) and isinstance(binding.get("path"), str) and isinstance(binding.get("sha256"), str) and re.fullmatch(r"[A-Za-z0-9_./-]{1,200}", binding["path"]) and re.fullmatch(r"[0-9a-f]{64}", binding["sha256"]):
            selected.append("source=" + binding["path"] + "@" + binding["sha256"])
        backend = self.details.get("backend", {})
        if isinstance(backend, dict):
            status = backend.get("status")
            if isinstance(status, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", status):
                selected.append("backend=" + status)
            identifiers = set()
            records = [row for name in ("findings", "diagnostics") for row in (backend[name] if isinstance(backend.get(name), list) else [])]
            for finding in records:
                if not isinstance(finding, dict):
                    continue
                value = finding.get("code") or str(finding.get("constraint", "")).rsplit("#", 1)[-1]
                if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
                    identifiers.add(value)
            if identifiers:
                selected.append("findings=" + ",".join(sorted(identifiers)[:3]))
        return (super().__str__()[:300] + (" [" + "; ".join(selected) + "]" if selected else ""))[:1200]


def fail(condition, code, message, **details):
    if not condition:
        raise GuardError(code, message, details)


class _GuardBudget:
    """One deadline shared by every backend phase of one semantic decision."""
    def __init__(self, root, *, clock=None):
        from ontology_limits import limits
        self.clock = clock or time.monotonic
        self.started = self.clock()
        self.bounds = limits(_json(Path(root) / "ontology-advanced.yaml").get("limits", {}))
        self.seconds = min(5, self.bounds["guard_seconds"])
        self.deadline = self.started + self.seconds

    def is_set(self):
        # The existing supervised worker polls this while running and kills
        # its process group on expiry. No background thread may dispatch work.
        return self.clock() >= self.deadline

    def check(self, backend=None):
        fail(not self.is_set(), "guard_timeout",
             "The shared semantic evaluation budget expired; no action was dispatched. Resolve the expensive input or retry with a smaller selected graph.",
             limit_seconds=self.seconds, elapsed_seconds=round(self.clock() - self.started, 4),
             **({"backend": backend} if isinstance(backend, dict) else {}))

    def evaluate(self, function, *args, **kwargs):
        self.check()
        remaining = max(1, math.ceil(self.deadline - self.clock()))
        bounds = {key: min(remaining, self.bounds[key]) for key in ("query_seconds", "reasoning_seconds")}
        result = function(*args, **kwargs, limits=bounds, cancel=self)
        self.check(result)
        return result


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else encoded(value)).hexdigest()


def _json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            fail(key not in result, "guard_schema", "Duplicate configuration key.", key=key)
            result[key] = value
        return result
    try:
        return json.loads(path.read_text(), object_pairs_hook=pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GuardError("guard_unavailable", "Guard configuration cannot be read as strict JSON.", {"path": str(path)}) from exc


def profile(root):
    root = Path(root).absolute()
    path = root / "ontology-advanced.yaml"
    if not path.exists() and not path.is_symlink():
        return None
    fail(not path.is_symlink() and path.is_file(), "guard_unavailable", "Unsafe advanced configuration path.")
    config = _json(path)
    fail(isinstance(config, dict) and config.get("schema_version") == 1 and isinstance(config.get("profiles"), dict),
         "guard_schema", "Unsupported advanced configuration.")
    selected = config["profiles"].get("guards", {"enabled": False})
    fail(isinstance(selected, dict) and type(selected.get("enabled")) is bool,
         "guard_schema", "Guard profile must explicitly select a Boolean enabled value.")
    if not selected["enabled"]:
        fail(set(selected) == {"enabled"}, "guard_schema", "Disabled guard profile has unsupported fields.")
        return None
    fail(set(selected) == {"enabled", "contract", "adapters", "bootstrap"}, "guard_schema", "Enabled guard profile requires the exact contract, adapters and bootstrap bindings.")
    return selected


def checked_path(root, value):
    path = Path(value)
    fail(not path.is_absolute() and path.parts and ".." not in path.parts, "guard_scope", "Guard paths must be project relative.", path=str(value))
    current = Path(root)
    for part in path.parts:
        current /= part
        fail(not current.is_symlink(), "guard_scope", "Guard paths cannot traverse symbolic links.", path=str(value))
    return current


def read_bound(root, binding):
    fail(isinstance(binding, dict) and set(binding) == {"path", "sha256"} and isinstance(binding["path"], str)
         and isinstance(binding["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", binding["sha256"]),
         "guard_schema", "Malformed exact file binding.")
    path = checked_path(root, binding["path"])
    fail(path.is_file(), "guard_unavailable", "Required guard file is absent.", path=binding["path"])
    raw = path.read_bytes()
    fail(digest(raw) == binding["sha256"], "guard_stale", "A bound guard source changed; select an exact reviewed repair.", path=binding["path"])
    return raw


def normalize(value, depth=0):
    fail(depth <= 32, "guard_schema", "Action nesting exceeds its bound.")
    if value is None or type(value) in (bool, int, str):
        if isinstance(value, str):
            fail(len(value.encode()) <= 4 * 1024 * 1024, "guard_schema", "Action text exceeds its bound.")
        return value
    if isinstance(value, float):
        fail(math.isfinite(value), "guard_schema", "Action numbers must be finite.")
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return {"bytes_sha256": digest(value), "byte_count": len(value)}
    if isinstance(value, argparse.Namespace):
        value = vars(value)
    elif is_dataclass(value):
        value = {field.name: getattr(value, field.name) for field in fields(value)}
    if isinstance(value, dict):
        fail(len(value) <= 20000 and all(isinstance(key, str) for key in value), "guard_schema", "Action objects require bounded string keys.")
        return {key: normalize(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        fail(len(value) <= 20000, "guard_schema", "Action collection exceeds its bound.")
        items = [normalize(item, depth + 1) for item in value]
        return sorted(items, key=lambda item: encoded(item)) if isinstance(value, (set, frozenset)) else items
    if callable(value):
        code = getattr(value, "__code__", None)
        result = {"callable": getattr(value, "__qualname__", type(value).__name__),
                  "code_sha256": digest(code.co_code) if code else None}
        if getattr(value, "__name__", None) == "mutate" and code:
            result["captured_request"] = {name: normalize(cell.cell_contents, depth + 1)
                for name, cell in zip(code.co_freevars, value.__closure__ or ())}
        return result
    # Store instances only supply their project root, never private object state.
    for key in ("project_root", "root"):
        if isinstance(getattr(value, key, None), Path):
            return {key: str(getattr(value, key)), **{name: str(getattr(value, name)) for name in ("folder", "lock_path") if isinstance(getattr(value, name, None), Path)}}
    raise GuardError("guard_schema", "Unsupported action argument type.", {"type": type(value).__name__})


def _snapshot(root, paths):
    result, count = {}, 0
    for relative in sorted(set(paths)):
        path = checked_path(root, relative)
        if not path.exists():
            result[relative] = None
            continue
        if path.is_dir():
            result[relative] = None  # A helper may create its empty lock parent.
        found = sorted(path.rglob("*")) if path.is_dir() else [path]
        for item in found:
            rel = item.relative_to(root).as_posix()
            # Lock bookkeeping and projection temporaries are owned by the helper.
            if any(part.startswith(".") for part in Path(rel).parts if part != ".sys4ai"):
                continue
            fail(not item.is_symlink(), "guard_scope", "Target inventory contains a symbolic link.", path=rel)
            if not item.is_file():
                continue
            raw = item.read_bytes()
            count += len(raw)
            fail(len(result) < MAX_FILES and count <= MAX_BYTES, "guard_resource_limit", "Guard target inventory exceeds its supported bound.")
            result[rel] = digest(raw)
    return result


PATH_FIELDS = {"path", "grant_file", "input", "input_file", "source_path", "receipt_path", "file_path", "journal_path"}
CONTENT_FIELDS = {"content", "content_base64", "content_b64", "data", "data_base64", "body", "text", "stdout", "stderr", "raw"}
FILE_MAP_FIELDS = {"files", "file_contents", "source_files", "original_files", "proposed_files", "prior_contents"}


def _selected_argument_files(root, value, key=""):
    """Only explicit path fields are paths; filenames and content are not hints.

    Setup maps can use a filename such as ontology_profiles.py as a dictionary
    key and base64 file content as its value. Substring matching that key would
    treat the entire content as a filename and could expose it in an OSError.
    """
    if key in CONTENT_FIELDS:
        return []
    if isinstance(value, dict):
        if key in FILE_MAP_FIELDS:
            return []
        result = []
        for name, item in value.items():
            field = name + "_path" if name in {"source", "destination"} and name + "_sha256" in value else name
            result.extend(_selected_argument_files(root, item, field))
        return result
    if isinstance(value, list):
        return [path for item in value for path in _selected_argument_files(root, item, key)]
    if key not in PATH_FIELDS or not isinstance(value, str) or value == "-":
        return []
    if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        return []  # A selected URI is not a request to inspect a local file.
    fail(0 < len(value.encode()) <= 4096 and not any(ord(char) < 32 for char in value),
         "guard_invalid_path", "An explicit request path is malformed or exceeds its bound.", field=key)
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    try:
        return [path] if path.is_file() else []
    except OSError as exc:
        raise GuardError("guard_invalid_path", "An explicit request path cannot be inspected safely.",
                         {"field": key, "errno": exc.errno}) from None


def _argument_paths(root, value, key=""):
    return {path.relative_to(root).as_posix() for path in _selected_argument_files(root, value, key)
            if path.is_relative_to(root)}


def _external_argument_context(root, value, key=""):
    found = {}
    for path in _selected_argument_files(root, value, key):
        if path.is_relative_to(root):
            continue
        fail(not any(parent.is_symlink() for parent in (path, *path.parents)), "guard_scope", "External reviewed input cannot traverse a symbolic link.")
        try:
            fail(path.stat().st_size <= 8 * 1024 * 1024, "guard_resource_limit", "Reviewed input exceeds the guard bound.")
            found[str(path)] = digest(path.read_bytes())
        except OSError as exc:
            raise GuardError("guard_invalid_path", "A reviewed external input cannot be read safely.", {"errno": exc.errno}) from None
    return found


def _accepted_publication(root, arguments):
    proposal = arguments.get("proposal", arguments.get("intent", {}).get("proposal"))
    if isinstance(proposal, dict) and proposal.get("operation") == "integrate-curator":
        from ontology_integration import _paths, _intent
        path = _paths(proposal.get("operation_id"))[0]
        if not checked_path(root, path).is_file(): return None
        intent = _intent(root, proposal["operation_id"])
        fail(intent["proposal"] == proposal, "guard_stale", "Integration differs from its accepted intent.")
        return path, intent
    if not isinstance(proposal, dict) or proposal.get("schema_version") != 2:
        return None
    identity = proposal.get("operation_id")
    if not isinstance(identity, str) or not re.fullmatch(r"ONTOP-[A-Za-z0-9-]{4,100}", identity):
        return None
    path = "control_records/ontology/intents/" + identity + ".json"
    if not checked_path(root, path).is_file():
        return None
    from ontology_publication import _read_intent
    intent = _read_intent(root, identity)
    fail(intent["proposal"] == proposal and ("intent" not in arguments or arguments["intent"] == intent),
         "guard_stale", "The request differs from its actual accepted publication intent.")
    return path, intent


def _context(root, selected, arguments):
    files = {"ontology-advanced.yaml", "ontology.yaml", "AGENTS.md", "SOUL.md", "ROLE.md"}
    for binding in (selected["contract"], selected["adapters"], selected["bootstrap"]):
        read_bound(root, binding)
        files.add(binding["path"])
    contract = validate_contract(json.loads(read_bound(root, selected["contract"])))
    adapters = json.loads(read_bound(root, selected["adapters"]))
    bootstrap = json.loads(read_bound(root, selected["bootstrap"]))
    fail(contract.get("schema_version") == adapters.get("schema_version") == bootstrap.get("schema_version") == 1,
         "guard_schema", "Unsupported action contract, adapter inventory or bootstrap version.")
    fail(bootstrap.get("contract") == selected["contract"] and bootstrap.get("adapters") == selected["adapters"],
         "guard_stale", "Bootstrap does not bind the selected contract and complete adapter inventory.")
    fail(set(adapters.get("families", {})) == FAMILIES, "guard_coverage", "All eight action families are required before guard enablement.")
    fail(bootstrap.get("status") == "verified" and bootstrap.get("repair"), "guard_bootstrap", "No verified immutable bootstrap and repair binding.")
    read_bound(root, bootstrap["repair"])
    files.add(bootstrap["repair"]["path"])
    for name in ("engine", "setup"):
        fail(name in bootstrap, "guard_bootstrap", "Bootstrap omits an exact guard implementation binding.", binding=name)
        read_bound(root, bootstrap[name])
        files.add(bootstrap[name]["path"])
    for family in adapters["families"].values():
        fail(isinstance(family, list) and family, "guard_coverage", "Empty action family adapter coverage.")
        for adapter in family:
            fail(isinstance(adapter, dict) and set(adapter) == {"path", "sha256", "operations"}
                 and isinstance(adapter["operations"], list) and adapter["operations"], "guard_schema", "Malformed adapter declaration.")
            read_bound(root, {key: adapter[key] for key in ("path", "sha256")})
            files.add(adapter["path"])
    shape = contract.get("shapes")
    read_bound(root, shape)
    files.add(shape["path"])
    files.update(_argument_paths(root, arguments))
    config = _json(root / "ontology-advanced.yaml")
    accepted = _accepted_publication(root, arguments)
    accepted_changes = {row["path"]: row for row in accepted[1]["proposal"]["changes"]} if accepted else {}
    if accepted:
        files.add(accepted[0])
    for binding in config.get("extensions", []):
        change = accepted_changes.get(binding["path"])
        if change and binding["sha256"] == change["expected_sha256"]:
            actual = checked_path(root, binding["path"])
            fail(actual.is_file() and digest(actual.read_bytes()) in {change["expected_sha256"], change["sha256"]},
                 "guard_stale", "Accepted extension recovery requires its exact retained pre/post bytes.", path=binding["path"])
        else:
            read_bound(root, binding)
        files.add(binding["path"])
    # Exact asserted semantics and grants are current context, never authority.
    for relative in ("ONTOLOGY/modules", "ONTOLOGY/bindings", "ONTOLOGY/extensions", "Tasks", "Roles"):
        if (root / relative).exists():
            files.add(relative)
    return contract, adapters, {**_snapshot(root, files), **_external_argument_context(root, arguments)}


def _direct_facts(root, family, operation, arguments, budget):
    """The two direct owning APIs supply real proposals/profile previews.

    All other families enter through dispatch and its actual owner readers.
    A JSON field named _semantic_state is never a source of observed facts.
    """
    facts = {"input_type": family + "-" + operation + "-request", "input_valid": True, "requested_paths": []}
    if family == "ontology" and operation in {"integration_preview", "integration_publish", "integration_recover"}:
        from ontology_integration import check_proposal
        proposal = arguments.get("proposal", arguments.get("intent", {}).get("proposal"))
        accepted = _accepted_publication(root, arguments)
        prior = accepted[1]["prior_contents"] if accepted else None
        old, candidate = check_proposal(root, proposal, prior)
        facts["requested_paths"] = [change["path"] for change in proposal["changes"]]
        facts["input_valid"] = not any(row["severity"] == "error" for row in candidate.diagnostics)
        return facts
    if family == "ontology" and operation in {"preview", "publish", "recover"}:
        from ontology_publication import check_proposal
        from ontology_core import load_project, OntologyError
        from ontology_lifecycle import validate_transition
        proposal = arguments.get("proposal", arguments.get("intent", {}).get("proposal"))
        fail(isinstance(proposal, dict), "guard_schema", "Ontology action requires its actual normalized publication proposal.")
        check_proposal(root, proposal)
        facts["requested_paths"] = [change["path"] for change in proposal["changes"]]
        cfg = _json(root / "ontology.yaml")
        core = set(cfg["project_files"] + cfg["binding_files"] + cfg.get("competency_files", []))
        try:
            old = load_project(root, validate=False)
            candidate = load_project(root, validate=False, _overrides={change["path"]: change["content"].encode()
                for change in proposal["changes"] if change["path"] in core})
            facts["input_valid"] = not any(row["severity"] == "error" for row in candidate.diagnostics) and not validate_transition(old.records, candidate.records)
            facts["input_valid"] &= all(source["status"] == "current" for source in candidate.sources)
        except OntologyError:
            facts["input_valid"] = False
        if proposal["schema_version"] == 2 and facts["input_valid"]:
            from ontology_advanced import load_advanced, load_extensions
            from ontology_standards import validate, infer, dataset
            overrides = {change["path"]: change["content"].encode() for change in proposal["changes"]}
            configured = load_advanced(root, required=True, _overrides=overrides)
            extensions, _, _ = load_extensions(candidate, configured, _overrides=overrides)
            # load_project already ran the complete core record validator.
            # Validate selected authored shapes over the exact RDF projection
            # without regenerating hundreds of equivalent per-record shapes.
            graph = budget.evaluate(dataset, root, graphs=["asserted", "derived", "external"], overrides=overrides)
            fail(graph.get("complete") is True and graph.get("status") == "ok", "guard_unavailable",
                 "The exact candidate dataset is unavailable; restore its selected backend before retrying.", backend=graph)
            budget.candidate_graph = graph
            checked = budget.evaluate(validate, root, triples=[row[:3] for row in graph["quads"]], overrides=overrides)
            fail(isinstance(checked, dict) and checked.get("complete") is True and checked.get("status") == "conformant" and checked.get("conforms") is True,
                 "guard_candidate_invalid", "The exact v2 candidate did not establish complete semantic conformance; resolve its selected standards findings before retrying.", backend=checked)
            facts["candidate_validation"] = {"standards": {"status": checked["status"], "context_sha256": digest(checked.get("context", {})),
                "scope": "Complete core record checks plus actual selected project SHACL over the exact candidate RDF graph."}}
            formal = any(extension.get("axioms") or extension.get("negative_assertions") for extension in extensions)
            fail(not formal or configured["profiles"].get("inference", {}).get("enabled") is True,
                 "guard_inference_required", "This guarded extension contains formal assertions; explicitly enable its inference profile before validating the action.", backend={"status": "profile_disabled"})
            if configured["profiles"].get("inference", {}).get("enabled"):
                inferred = budget.evaluate(infer, root, overrides=overrides)
                fail(isinstance(inferred, dict) and inferred.get("complete") is True and inferred.get("status") == "ok" and inferred.get("trusted") is True,
                     "guard_candidate_inconsistent", "The exact v2 candidate did not establish consistent finite inference; resolve its conflicts or unavailable profile before retrying.", backend=inferred)
                facts["candidate_validation"]["inference"] = {"status": inferred["status"], "context_sha256": digest(inferred.get("context", {}))}
        # An accepted operation may resume its exact already-written post-state.
        accepted = operation == "recover" or (root / ("control_records/ontology/intents/" + proposal["operation_id"] + ".json")).is_file()
        for change in proposal["changes"]:
            path = checked_path(root, change["path"])
            actual = digest(path.read_bytes()) if path.is_file() else None
            facts["input_valid"] &= actual == change["expected_sha256"] or accepted and actual == change["sha256"]
        return facts
    if family == "setup" and operation == "configure_profile":
        from ontology_advanced import load_advanced
        preview = arguments.get("preview", {})
        change = preview.get("change", {})
        fail(isinstance(change.get("content"), str), "guard_schema", "Profile configuration requires its actual exact preview.")
        current = load_advanced(root, required=True)
        proposed = load_advanced(root, required=True, _overrides={"ontology-advanced.yaml": change["content"].encode()})
        selected = arguments.get("profile")
        facts["requested_paths"] = [change.get("path", "")]
        facts["input_valid"] = selected in {"standards", "inference", "semantic", "workbench"} and type(arguments.get("enabled")) is bool
        facts["input_valid"] &= proposed["profiles"].get(selected, {}).get("enabled") is arguments.get("enabled")
        old_other, new_other = normalize(current), normalize(proposed)
        old_other["profiles"].pop(selected, None); new_other["profiles"].pop(selected, None)
        facts["input_valid"] &= old_other == new_other
        facts["input_valid"] &= not (selected == "standards" and arguments.get("enabled") is False)
        return facts
    raise GuardError("guard_missing_evidence", "This action requires the actual owning dispatch and its current structural readers; caller-supplied semantic state is not evidence.", {"action_id": BASE + family + ":" + operation})


def _target_type(root, path):
    """Classify actual selected paths against the current owned stores."""
    checked_path(root, path)
    if path == "ontology-advanced.yaml":
        return {"ontology-owned-artifact", "setup-owned-artifact"}
    mapping = {"MEMORY": "memory", "memory.yaml": "memory", "Tasks": "task", "TRDs": "trd",
               "Implementation_Plans": "plan", "Roles": "role", "roles": "role", "control_records/roles": "role",
               "Projects/Sys4AI-Template-Project": "template", ".sys4ai/template-update/state.json": "template",
               "depot/projects.json": "setup"}
    result = {family + "-owned-artifact" for prefix, family in mapping.items() if path == prefix or path.startswith(prefix + "/")}
    cfg = _json(root / "ontology.yaml")
    canonical = cfg["project_files"] + cfg["binding_files"] + cfg.get("competency_files", [])
    advanced = _json(root / "ontology-advanced.yaml")
    for binding in advanced.get("extensions", []):
        canonical.append(binding["path"])
        canonical.extend(row["path"] for row in _json(checked_path(root, binding["path"])).get("shapes", []))
    if path in canonical:
        result.add("ontology-owned-artifact")
    if path.startswith("Projects/") and len(Path(path).parts) >= 2 and Path(path).parts[1] not in {"Sys4AI-Template-Project", ".", ".."}:
        result.add("setup-owned-artifact")
    return result


def _semantic_triples(root, family, operation, arguments, targets, facts, action, adapters, node, contract):
    fail(isinstance(facts, dict) and set(facts) <= {"input_type", "input_valid", "requested_paths", "targetIdentity", "currentState", "nextState", "targetRevision", "transition_valid", "candidate_validation"},
         "guard_schema", "Unsupported owner observation fields.")
    triples = []
    def literal(key, value):
        term = {"value": str(value).lower() if type(value) is bool else str(value)}
        if type(value) in {bool, int}:
            term["datatype"] = "http://www.w3.org/2001/XMLSchema#" + ("boolean" if type(value) is bool else "integer")
        triples.append([node, BASE + key, term])
    literal("inputType", facts.get("input_type", "unobserved"))
    literal("inputValid", facts.get("input_valid") is True and facts.get("transition_valid", True) is True)
    requested = facts.get("requested_paths", [])
    fail(isinstance(requested, list) and all(isinstance(path, str) for path in requested), "guard_schema", "Owner target paths are malformed.")
    all_targets = list(dict.fromkeys([*targets, *requested]))
    for target in all_targets:
        literal("target", target)
        types = _target_type(root, target)
        if family == "ontology" and operation in {"integration_preview", "integration_publish", "integration_recover"}:
            from ontology_integration import TARGETS
            # The direct owner validator proved the exact four-file candidate;
            # this classification does not widen ordinary publication targets.
            if target in TARGETS: types.add("ontology-owned-artifact")
        observed_type = family + "-owned-artifact" if family + "-owned-artifact" in types else (sorted(types)[0] if types else "unclassified-artifact")
        literal("targetType", observed_type)
    for key in ("targetIdentity", "currentState", "nextState", "targetRevision"):
        if key in facts:
            literal(key, facts[key])
    observed_capabilities = set()
    for binding in adapters["families"][family]:
        if operation not in binding["operations"]:
            continue
        source = read_bound(root, {key: binding[key] for key in ("path", "sha256")})
        tree = ast.parse(source)
        declarations = []
        for statement in tree.body:
            if isinstance(statement, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "ONTOLOGY_GUARDED_ACTIONS" for target in statement.targets):
                declarations = ast.literal_eval(statement.value)
        # Ontology publication uses direct checks rather than the generic wrapper.
        declared = operation in declarations or "Store." + operation in declarations
        if binding["path"] == ".agents/skills/ontology/scripts/ontology_publication.py":
            declared = operation in {"preview", "publish", "recover", "integration_preview", "integration_publish", "integration_recover"} and any(isinstance(n, ast.FunctionDef) and n.name == operation for n in tree.body)
        provider_family = PROVIDERS.get(binding["path"])
        if declared and provider_family:
            observed_capabilities.add(BASE + "capability:" + CAPABILITIES[provider_family])
    for capability in sorted(observed_capabilities):
        triples.append([node, BASE + "requiredCapability", capability])
    present = 0
    for name in action["governing_sources"]:
        path = checked_path(root, name)
        if path.is_file() and path.read_bytes().strip():
            present += 1
            source = BASE + "source:" + digest({"path": name, "sha256": digest(path.read_bytes())})
            triples.extend([[node, BASE + "governingSource", source], [source, BASE + "sourcePath", {"value": name}],
                            [source, BASE + "sourceDigest", {"value": digest(path.read_bytes())}]])
    literal("governingSourceCount", present)
    # The shared delivered shape defines observed facts. The selected action
    # adds its declared type/capability and lifecycle constraints as SHACL data.
    def quoted(value):
        return json.dumps(value, ensure_ascii=False)
    properties = ["sh:path action:inputType; sh:hasValue " + quoted(action["input_type"]),
                  "sh:path action:targetType; sh:in (" + quoted(action["target_type"]) + ")",
                  "sh:path action:requiredCapability; sh:hasValue <" + action["capability"] + ">"]
    if action["lifecycle"]:
        lifecycle = contract["lifecycles"][action["lifecycle"]]
        transitions = lifecycle["transitions"]
        states = " ".join(quoted(state) for state in transitions)
        allowed = transitions.get(facts.get("currentState"), [])
        if family != "task" or facts.get("currentState") not in {"completed", "cancelled", "close-old-task"}:
            allowed = list(dict.fromkeys([facts.get("currentState", "unobserved"), *allowed]))
        properties += ["sh:path action:targetIdentity; sh:minCount 1; sh:maxCount 1; sh:pattern " + quoted(lifecycle["identity_pattern"]),
                       "sh:path action:targetRevision; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:integer; sh:minInclusive 1",
                       "sh:path action:currentState; sh:minCount 1; sh:maxCount 1; sh:in (" + states + ")",
                       "sh:path action:nextState; sh:minCount 1; sh:maxCount 1; sh:in (" + " ".join(quoted(state) for state in allowed) + ")"]
    shape = "\naction:SelectedActionShape a sh:NodeShape; sh:targetNode <" + node + ">;\n  " + ";\n  ".join("sh:property [ " + value + " ]" for value in properties) + " .\n"
    return triples, shape


class Decision:
    def __init__(self, root, family, operation, arguments, targets, observed=None):
        self.root, self.family, self.operation = root, family, operation
        self.action_id = BASE + family + ":" + operation
        self.arguments, self.targets = arguments, tuple(targets)
        self.live_arguments = None
        self.selected = profile(root)
        self.lock_checked = False
        self.request_sha256 = digest(arguments)
        self.pre = self.context = self.backend = None
        if self.selected is None:
            return
        budget = _GuardBudget(root)
        fail("_semantic_state" not in arguments, "guard_missing_evidence", "Caller-supplied semantic state is not current owning-helper evidence.", action_id=self.action_id)
        fail(family in FAMILIES, "guard_unsupported", "Unsupported guarded action family.", action_id=self.action_id)
        contract, adapters, self.context = _context(root, self.selected, arguments)
        bootstrap = json.loads(read_bound(root, self.selected["bootstrap"]))
        engine = bootstrap["engine"]
        fail(checked_path(root, engine["path"]).resolve() == Path(__file__).resolve()
             and engine["sha256"] == ENGINE_SOURCE_SHA256,
             "guard_stale", "Loaded guard engine is not the selected project's exact installed engine.", action_id=self.action_id)
        definitions = contract.get("actions", []) + contract.get("optional_actions", [])
        matches = [item for item in definitions if item.get("family") == family and item.get("operation") == operation]
        fail(len(matches) == 1, "guard_ambiguous" if len(matches) > 1 else "guard_unsupported",
             "Action must resolve to exactly one current semantic contract.", action_id=self.action_id)
        fail(any(operation in item["operations"] for item in adapters["families"][family]), "guard_coverage", "No current adapter binds this operation.", action_id=self.action_id)
        fail(len(targets) == len(set(targets)), "guard_ambiguous", "Duplicate action targets are ambiguous.", action_id=self.action_id)
        self.pre = _snapshot(root, targets)
        facts = observed if observed is not None else _direct_facts(root, family, operation, arguments, budget)
        self.request_sha256 = digest({"arguments": arguments, "observations": facts})
        self.facts = facts
        node = self.action_id + ":request:" + self.request_sha256
        triples = [[node, "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", BASE + "Request"],
                   [node, BASE + "family", {"value": family}], [node, BASE + "operation", {"value": operation}],
                   [node, BASE + "requestDigest", {"value": self.request_sha256}],
                   [node, BASE + "targetDigest", {"value": digest(self.pre)}]]
        observed_triples, selected_shape = _semantic_triples(root, family, operation, arguments, targets, facts, matches[0], adapters, node, contract)
        triples.extend(observed_triples)
        try:
            from ontology_standards import validate
        except ImportError as exc:
            raise GuardError("guard_unavailable", "Enabled action guards require the provisioned standards backend.", {"action_id": self.action_id}) from exc
        shapes = read_bound(root, contract["shapes"]).decode() + selected_shape
        proposal = arguments.get("proposal", arguments.get("intent", {}).get("proposal")) if family == "ontology" else None
        candidate_overrides = {change["path"]: change["content"].encode() for change in proposal["changes"]} if isinstance(proposal, dict) and proposal.get("schema_version") == 2 else None
        from ontology_advanced import load_advanced
        configured = load_advanced(root, required=True, _overrides=candidate_overrides)
        has_selected_shapes = any(json.loads((candidate_overrides or {}).get(ref["path"], checked_path(root, ref["path"]).read_bytes())).get("shapes") for ref in configured["extensions"])
        if has_selected_shapes:
            # The standards interface applies selected project shapes as well
            # as action shapes. Supply their actual authoring data so a valid
            # project shape does not fail against an action-only graph.
            from ontology_standards import dataset
            graph = getattr(budget, "candidate_graph", None)
            if graph is None:
                graph = budget.evaluate(dataset, root, graphs=["asserted", "derived", "external"], overrides=candidate_overrides)
            fail(graph.get("complete") is True and graph.get("status") == "ok", "guard_unavailable", "Selected shape data could not be read completely; restore its backend before retrying.", backend=graph)
            triples.extend(row[:3] for row in graph["quads"])
        try:
            self.backend = budget.evaluate(validate, root, triples=triples, shapes=shapes, overrides=candidate_overrides)
        except GuardError:
            raise
        except Exception as exc:
            raise GuardError("guard_processing_failure", "The enabled validation backend failed; no mutation was dispatched.",
                             {"action_id": self.action_id, "failure_type": type(exc).__name__}) from exc
        backend_status = self.backend.get("status") if isinstance(self.backend, dict) else None
        condition = backend_status if isinstance(backend_status, str) and re.fullmatch(r"[a-z_]{1,60}", backend_status) else "processing_failure"
        fail(isinstance(self.backend, dict) and backend_status == "conformant" and self.backend.get("complete") is True,
             "guard_" + condition,
             "Enabled semantic validation did not establish conformance; restore the backend or resolve its findings before retrying.",
             action_id=self.action_id, contract=self.selected["contract"],
             governing_versions={name: self.context.get(name) for name in matches[0]["governing_sources"]}, backend=self.backend)
        # The backend may have run while a governing file or target changed.
        self.recheck()
        budget.check()
        self.evaluation_seconds = round(budget.clock() - budget.started, 4)
        self.evaluation_budget_seconds = budget.seconds

    def recheck(self, *, targets=True):
        try:
            return self._recheck(targets=targets)
        except GuardError as exc:
            exc.details.setdefault("action_id", self.action_id)
            if self.selected:
                exc.details.setdefault("contract", self.selected["contract"])
            raise

    def _recheck(self, *, targets=True):
        if self.selected is None:
            fail(profile(self.root) is None, "guard_stale", "Guard profile changed before dispatch.")
            return
        fail(profile(self.root) == self.selected, "guard_stale", "Guard profile changed before dispatch.", action_id=self.action_id)
        fail(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == ENGINE_SOURCE_SHA256,
             "guard_stale", "Loaded guard-engine bytes changed after import; the prior decision cannot continue.", action_id=self.action_id)
        _, _, current = _context(self.root, self.selected, self.arguments)
        def retained(values):
            # An owning transaction checks its selected writes against its own
            # exact accepted pre/post digests.  Keep every other source bound.
            accepted = _accepted_publication(self.root, self.arguments) if self.family == "ontology" else None
            own_new_intent = accepted[0] if accepted and self.lock_checked and accepted[0] not in self.context else None
            return {key: value for key, value in values.items() if key != own_new_intent and (targets or not any(
                key == target or key.startswith(target.rstrip("/") + "/") for target in self.targets))}
        fail(retained(current) == retained(self.context), "guard_stale", "Ontology, rules, source or authority context changed before dispatch.", action_id=self.action_id)
        current_arguments = normalize(self.live_arguments) if self.live_arguments is not None else self.arguments
        def request_fields(values):
            # Setup's record is its mutable owned transaction state, not a new
            # request; its original bytes stay in the target/receipt snapshots.
            return {key: value for key, value in values.items() if not (
                self.family == "setup" and self.lock_checked and key == "record")}
        fail(digest(request_fields(current_arguments)) == digest(request_fields(self.arguments)), "guard_stale", "Action arguments changed before dispatch.", action_id=self.action_id)
        if targets:
            fail(_snapshot(self.root, self.targets) == self.pre, "guard_stale", "Action target changed before its owning lock was acquired.", action_id=self.action_id)

    def finish(self, receipt):
        if self.selected is None:
            return receipt
        evidence = {"schema_version": 1, "action_id": self.action_id, "request_sha256": self.request_sha256,
                    "semantic_status": "conformant", "context_sha256": digest(self.context),
                    "backend_context": self.backend.get("context"), "pre_state_sha256": digest(self.pre),
                    "post_state_sha256": digest(_snapshot(self.root, self.targets)),
                    "owning_helper": "returned", "authorization": "retained_in_owning_helper",
                    "execution_and_verification": "see_owning_helper_receipt", "lock_rechecked": self.lock_checked}
        evidence["observations_sha256"] = digest(self.facts)
        evidence["evaluation_budget_seconds"] = self.evaluation_budget_seconds
        # Publication previews are hashed and recomputed before dispatch.
        # Keep measured time in actual execution receipts, not exact review
        # identity: equivalent semantic previews must retain identical hashes.
        if not (self.family == "ontology" and self.operation == "preview"):
            evidence["evaluation_seconds"] = self.evaluation_seconds
        if "candidate_validation" in self.facts:
            evidence["candidate_validation"] = self.facts["candidate_validation"]
        if isinstance(receipt, dict):
            return dict(receipt, ontology_guard=evidence)
        if isinstance(receipt, tuple) and receipt and isinstance(receipt[0], dict):
            return (dict(receipt[0], ontology_guard=evidence), *receipt[1:])
        return receipt


def begin_action(root, family, operation, arguments, targets=(), *, _observed=None):
    root = Path(root).absolute()
    try:
        normalized = normalize(arguments)
        fail(isinstance(normalized, dict), "guard_schema", "Action arguments must be an object.")
        fail(len(encoded(normalized)) <= 8 * 1024 * 1024, "guard_resource_limit", "Action request exceeds the guard input bound.")
        decision = Decision(root, family, operation, normalized, list(targets), _observed)
    except GuardError as exc:
        exc.details.setdefault("action_id", BASE + family + ":" + operation)
        try:
            current = profile(root)
        except GuardError:
            current = None  # Retain the original failed configuration diagnostic.
        if current:
            exc.details.setdefault("contract", current["contract"])
        else:
            configuration = root / "ontology-advanced.yaml"
            if configuration.is_file() and not configuration.is_symlink():
                exc.details.setdefault("configuration", {"path": "ontology-advanced.yaml", "sha256": digest(configuration.read_bytes())})
        raise
    decision.live_arguments = arguments
    return decision


def checkpoint(*, targets=True):
    """Called by owning lock/replace helpers; never acquires a competing lock."""
    for decision in ACTIVE.get():
        decision.recheck(targets=targets and not decision.lock_checked)
        if targets:
            decision.lock_checked = True


def require_adapter(decision, actual):
    if decision.selected is not None:
        fail(isinstance(actual, str) and Path(actual).is_file(), "guard_stale", "The executing owning helper has no current file binding.", action_id=decision.action_id, contract=decision.selected["contract"])
        adapters = json.loads(read_bound(decision.root, decision.selected["adapters"]))
        checksum = digest(Path(actual).read_bytes())
        fail(any(decision.operation in item["operations"] and item["sha256"] == checksum for item in adapters["families"][decision.family]),
             "guard_stale", "The executing helper differs from the selected current dispatch binding.", action_id=decision.action_id, contract=decision.selected["contract"])


def dispatch(function, family, operation, root, arguments, targets):
    try:
        facts = schema_check(function.__globals__, family, operation, root, arguments)
    except GuardError as exc:
        exc.details.setdefault("action_id", BASE + family + ":" + operation)
        current = profile(root)
        if current:
            exc.details.setdefault("contract", current["contract"])
        raise
    decision = begin_action(root, family, operation, arguments, targets, _observed=facts)
    require_adapter(decision, function.__globals__.get("__file__"))
    token = ACTIVE.set((*ACTIVE.get(), decision))
    try:
        return decision.finish(function())
    finally:
        ACTIVE.reset(token)


def schema_check(namespace, family, operation, root, arguments):
    """Run the owner's structural readers before semantic evaluation, without auth."""
    normalize(arguments)
    fail("_semantic_state" not in arguments, "guard_missing_evidence", "Caller-supplied semantic state is not owning-helper evidence.")
    root = Path(root).absolute()
    facts = {"input_type": family + "-" + operation + "-request", "input_valid": True, "requested_paths": []}
    def relative(path):
        selected = Path(path).absolute()
        fail(selected.is_relative_to(root), "guard_scope", "Actual owning target escapes the selected project.")
        return selected.relative_to(root).as_posix()
    if family == "memory":
        if operation in {"transact", "capture", "recover"}:
            from memory_publish import validate_payload_structure
            payload = arguments.get("payload")
            recovering = operation == "recover"
            if recovering:
                journal = namespace["_read_journal"](root, str(arguments["journal_path"]))
                payload = journal["payload"]
            validate_payload_structure(payload)
            from memory_core import load_config, parse_record, validate_record
            config = load_config(root)
            if not recovering:
                journal_path = config["state"]["maintenance"] + "/transactions/" + payload["operation_id"] + ".json"
                if checked_path(root, journal_path).is_file():
                    from memory_recovery import _read_journal
                    accepted = _read_journal(root, journal_path)
                    recovering = accepted["payload"] == payload
            next_states = []
            for change in payload["changes"]:
                value = validate_record(parse_record(change["content"]), config["project"]["id"])
                meta = value["metadata"]
                next_states.append(meta["state"])
                facts["requested_paths"].append(change["path"])
                facts["input_valid"] &= change["path"] == "MEMORY/" + meta["id"] + ".md" and digest(change["content"].encode()) == change["reviewed_record_sha256"]
                target = checked_path(root, change["path"])
                previous = parse_record(target.read_bytes())["metadata"] if target.is_file() else None
                if previous:
                    facts["input_valid"] &= previous["id"] == meta["id"]
                current_state = previous["state"] if previous else "absent"
                actual_sha = digest(target.read_bytes()) if target.is_file() else None
                facts["input_valid"] &= actual_sha == change["expected_sha256"] or (recovering and actual_sha == change["reviewed_record_sha256"])
                transition = payload["operation"]
                if not recovering:
                    if transition == "publish":
                        facts["input_valid"] &= current_state in {"absent", "draft"} and meta["state"] == "active"
                    elif transition == "supersede":
                        facts["input_valid"] &= (current_state == "active" and meta["state"] == "superseded") or (current_state in {"absent", "draft"} and meta["state"] == "active")
                    elif transition == "retract":
                        facts["input_valid"] &= current_state == "active" and meta["state"] == "retracted"
                    elif transition == "redact":
                        facts["input_valid"] &= previous is not None
                if meta["state"] == "active":
                    from memory_evidence import validate_publication_evidence
                    validate_publication_evidence(root, value, config)
            if payload["operation"] == "publish":
                facts["input_valid"] &= next_states == ["active"]
            elif payload["operation"] == "supersede":
                facts["input_valid"] &= next_states.count("active") == 1 and next_states.count("superseded") == len(next_states) - 1 and len(next_states) > 1
            elif payload["operation"] == "retract":
                facts["input_valid"] &= next_states == ["retracted"]
        elif operation == "propose":
            namespace["validate_record"](arguments["record"], namespace["load_config"](root)["project"]["id"])
            facts["input_valid"] &= arguments["record"]["metadata"]["state"] == "draft"
            output = arguments.get("output")
            if output is not None:
                facts["input_valid"] &= not str(output).startswith(("MEMORY/", ".sys4ai/"))
        elif operation == "set_capture":
            fail(type(arguments["enabled"]) is bool, "guard_schema", "Capture setting must be Boolean.")
        elif operation in {"reindex", "recover_reindex"}:
            config = namespace["load_config"](root)
            facts["input_valid"] &= config["project"]["id"] == _json(root / "ontology.yaml")["project"]["id"]
            if operation == "recover_reindex":
                identity = arguments["operation_id"]
                fail(isinstance(identity, str) and re.fullmatch(r"[0-9a-f]{32}", identity), "guard_schema", "Malformed memory maintenance identity.")
                journal = _json(checked_path(root, config["state"]["maintenance"] + "/backend-" + identity + ".json"))
                facts["input_valid"] &= journal.get("operation_id") == identity and journal.get("status") not in namespace["TERMINAL"]
    elif family == "task":
        if "tasks_root" in arguments:
            facts["requested_paths"] = [relative(arguments["tasks_root"])]
        if operation in {"command_new", "command_intake"}:
            payload = arguments.get("payload", arguments.get("raw_payload"))
            if operation == "command_intake":
                payload = {key: value for key, value in payload.items() if key != "intake_actor"}
            namespace["validate_new_payload"](payload)
        elif operation == "response_transaction":
            catalog = namespace["scan_catalog"](arguments["tasks_root"])
            namespace["require_valid_catalog"](catalog)
            state, _ = namespace["resolve_task"](arguments["selector"], catalog)
            payload = arguments["raw_payload"]
            if arguments["command"] == "orchestrate":
                namespace["require_object_keys"](payload, required={"event", "response"}, optional=set(), label="orchestration payload")
                fail(state.get("schema_version") == 2, "guard_schema", "Typed orchestration requires an explicitly enabled schema-2 Task.")
                event = payload["event"]
                orch = namespace["orch"]
                orch.keys(event, ("event_id", "actor", "execution_id", "generation", "kind", "data"))
                orch.validate_event_data(event["kind"], event["data"])
                current = state["orchestration"]
                starting = event["kind"] == "manager.reserve" and current["stage"] in {"unassigned", "finished"}
                if starting:
                    facts["input_valid"] &= event["generation"] == 1 and event["execution_id"] is not None and event["execution_id"] != current["execution_id"]
                    facts["input_valid"] &= state["status"] == "open" and not orch.unresolved(current)
                else:
                    facts["input_valid"] &= event["generation"] == current["generation"] and event["execution_id"] == current["execution_id"]
                facts["input_valid"] &= not any(row["event_id"] == event["event_id"] for row in current["events"])
                if "assignment_id" in event["data"] and event["kind"] not in {"manager.reserve", "assignment.reserve"}:
                    facts["input_valid"] &= event["data"]["assignment_id"] in current["assignments"]
                if event["kind"] == "manager.activate":
                    facts["input_valid"] &= current["stage"] == "receipt_recorded" and event["data"]["assignment_id"] == current["manager_id"]
                payload = payload["response"]
            checked = namespace["validate_response_payload"](payload, arguments["command"], state, root)
            command = arguments["command"]
            target = {"pause": "paused", "complete": "completed", "cancel": "cancelled", "reopen": "open", "close-old-task": "close-old-task"}.get(command, checked.get("status_after") or state["status"])
            facts.update(targetIdentity=state["task_id"], currentState=state["status"], nextState=target, targetRevision=state["revision"])
            facts["transition_valid"] = state["status"] not in namespace["TERMINAL"] or command == "reopen" and state["status"] == "completed"
            facts["input_valid"] &= type(arguments["expected_revision"]) is int and arguments["expected_revision"] == state["revision"]
        elif operation == "command_reconcile":
            # The existing validator combines schema and current confirmation.
            # Validate the structural copy here; the untouched actual request
            # still passes through the owner's confirmation check after guard.
            structural = dict(arguments["payload"])
            structural["user_authorized"] = True
            namespace["validate_reconcile_payload"](structural)
    elif family == "trd":
        if "self" in arguments:
            facts["requested_paths"] = [relative(arguments["self"].folder)]
        payload = arguments.get("payload")
        if operation in {"create", "update"}:
            fail(isinstance(payload, dict) and bool(payload) and set(payload) <= {"title", "body"}
                 and (operation != "create" or set(payload) == {"title", "body"}), "guard_schema", "TRD authoring accepts its exact title/body schema.")
            if "title" in payload:
                namespace["text_value"](payload["title"], "title", 160)
            if "body" in payload:
                namespace["validate_body"](namespace["normalized_body"](payload["body"]), allow_legacy_open_questions=False)
        elif operation == "set_status":
            fail(isinstance(arguments["status"], str), "guard_schema", "TRD status must be text.")
        if "selector" in arguments:
            store = arguments["self"]
            selected = store.resolve(arguments["selector"], store.read()[0])
            facts.update(targetIdentity=selected.meta["trd_id"], currentState=selected.meta["status"], targetRevision=selected.meta["revision"])
            if operation == "set_status":
                target = arguments["status"]
                facts["nextState"] = target
            if "expected" in arguments:
                facts["input_valid"] &= arguments["expected"] == selected.sha256
    elif family == "role":
        if operation == "create_role":
            namespace["validate_role_name"](arguments["args"].name)
            namespace["render_role_bundle"](arguments["args"])
        elif operation == "transition_apply":
            namespace["validate_preview"](arguments["preview"], root)
        elif operation == "case_rename_apply":
            namespace["validate_case_rename_preview"](arguments["preview"], root)
        elif operation in {"reindex", "publish_index"}:
            catalog = namespace["build_catalog"](root)
            facts["input_valid"] &= not catalog.invalid_roles
            if arguments.get("expected_fingerprint") is not None:
                facts["input_valid"] &= catalog.fingerprint == arguments["expected_fingerprint"]
    elif family == "plan":
        if "context" in arguments:
            facts["requested_paths"] = [relative(arguments["context"].plans_root)]
        if operation == "handle_create":
            raw = namespace["read_input"](arguments["args"].input)
            namespace["guard_prohibited_content"](raw)
            namespace["normalize_plan_input"](raw, arguments["context"])
        elif operation == "mutate_existing_plan":
            fail(type(arguments["expected_revision"]) is int and arguments["expected_revision"] > 0,
                 "guard_schema", "Plan mutation requires a positive exact revision.")
            namespace["parse_expected_hash"](arguments["expected_sha256"])
            selected = namespace["select_plan"](arguments["context"], arguments["selector"])
            facts["input_valid"] &= arguments["expected_revision"] == selected.plan["revision"] and arguments["expected_sha256"] == selected.sha256
            facts.update(targetIdentity=selected.plan["plan_id"], currentState=selected.plan["status"], targetRevision=selected.plan["revision"])
        elif operation in {"handle_update", "handle_update_phase", "handle_update_task", "handle_record_evidence"}:
            args = arguments["args"]
            raw = namespace["read_input"](args.input)
            namespace["guard_prohibited_content"](raw)
            fail(isinstance(raw, dict), "guard_schema", "Plan update requires a structured request.")
            selected = namespace["select_plan"](arguments["context"], args.selector)
            facts["input_valid"] &= args.expect_revision == selected.plan["revision"] and args.expect_sha256 == selected.sha256
            facts.update(targetIdentity=selected.plan["plan_id"], currentState=selected.plan["status"], targetRevision=selected.plan["revision"])
            if operation != "handle_record_evidence":
                command, prefix = {"handle_update": ("update", "BASELINE"), "handle_update_phase": ("update-phase", "PHASE"), "handle_update_task": ("update-task", "TASK")}[operation]
                patch, *_ = namespace["_operation_controls"](raw, command=command, allowed_patch_fields=namespace[prefix + "_PATCH_FIELDS"])
                namespace["validate_patch_value_types"](patch, namespace[prefix + "_PATCH_TYPES"], command)
                collection = "phases" if operation == "handle_update_phase" else "tasks" if operation == "handle_update_task" else None
                if collection:
                    key = "phase_id" if collection == "phases" else "task_id"
                    target = namespace["_find_record"](selected.plan[collection], key, getattr(args, key), collection)
                    if "status" in patch:
                        facts["input_valid"] &= patch["status"] == target["status"] or patch["status"] in namespace["TASK_TRANSITIONS"].get(target["status"], set())
                if patch and operation != "handle_update_task":
                    facts["input_valid"] &= selected.plan["status"] not in {"completed", "retired", "cancelled"}
            else:
                collection = "tasks" if namespace["TASK_ID_RE"].fullmatch(args.target_id) else "requirements"
                key = "task_id" if collection == "tasks" else "requirement_id"
                namespace["_find_record"](selected.plan[collection], key, args.target_id, "evidence target")
                facts["input_valid"] &= raw.get("evidence_type", "planned_check") == "planned_check" or selected.plan["status"] == "in_progress"
        elif operation == "handle_set_status":
            args = arguments["args"]
            selected = namespace["select_plan"](arguments["context"], args.selector)
            state = selected.plan["status"]
            facts.update(targetIdentity=selected.plan["plan_id"], currentState=state, nextState=args.status_value, targetRevision=selected.plan["revision"])
            revision = getattr(args, "expect_revision", getattr(args, "expected_revision", None))
            checksum = getattr(args, "expect_sha256", getattr(args, "expected_sha256", None))
            facts["input_valid"] &= revision == selected.plan["revision"] and checksum == selected.sha256
    elif family == "setup":
        if "destination" in arguments:
            facts["requested_paths"] = [relative(arguments["destination"])]
        if operation == "run_initialization":
            namespace["validate_identity"](arguments["project_id"], arguments["project_name"], arguments["purpose"])
            fail(arguments["mode"] in {"create", "prepare-existing"}, "guard_schema", "Unsupported setup mode.")
        elif operation == "run_module_adoption":
            record = arguments["record"]
            fail(isinstance(record, dict) and isinstance(arguments["previous_raw"], bytes), "guard_schema", "Module adoption requires the current receipt and exact original bytes.")
            receipt = arguments["destination"] / namespace["RECORD"]
            facts["input_valid"] &= record.get("status") == "completed" and record.get("completed_stages") == namespace["STAGES"]
            facts["input_valid"] &= receipt.is_file() and receipt.read_bytes() == arguments["previous_raw"]
            selected = arguments.get("module_id", namespace["LEARNING_MODULE"])
            facts["input_valid"] &= selected in {namespace["LEARNING_MODULE"], namespace["ONTOLOGY_MODULE"], namespace["ADVANCED_MODULE"], namespace["CURATOR_MODULE"], namespace["COLLABORATION_MODULE"]}
    elif family == "template":
        if operation == "update":
            fail(arguments["command"] in {"check", "apply"}, "guard_schema", "Unsupported Template operation.")
        elif operation == "recover":
            fail(isinstance(arguments["pending"], dict), "guard_schema", "Template recovery requires the exact pending record.")
        if arguments.get("retire_collection"):
            state_path = root / ".sys4ai/template-update/state.json"
            state = _json(state_path) if state_path.is_file() else {}
            # Retirement must refer to an actually recorded collection, not an
            # arbitrary name supplied as a semantic capability.
            facts["input_valid"] &= arguments["retire_collection"] in state.get("collections", {})
    return facts
