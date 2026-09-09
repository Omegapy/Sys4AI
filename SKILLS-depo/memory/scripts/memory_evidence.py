"""Evidence diagnostics do not rewrite history or mutate Task/role state."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys

from memory_paths import MemoryError, require, safe_path, safe_read_bytes, sensitive_path
from memory_core import decode_json_yaml, digest, exact, sha256, text, timestamp, reject_sensitive


def installed_helper(root, name):
    paths = {"task": ".agents/skills/agent-task/scripts/task_state.py",
             "role": ".agents/skills/manage-subagent-roles/scripts/role_catalog.py"}
    path = safe_path(root, paths[name])
    # Governance inspection must remain free of bytecode/cache creation.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("_memory_inspect_" + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_task(root, path):
    require(path.startswith("Tasks/") and path.endswith("/task.json"), "invalid_task_path", "Expected exact canonical Task path.")
    canonical = decode_json_yaml(safe_read_bytes(root, path, max_bytes=2_000_000))
    helper = installed_helper(root, "task")
    try:
        state, errors, _ = helper.validate_task_folder(safe_path(root, path).parent)
    except helper.TaskError as exc:
        raise MemoryError("invalid_task", "Installed Task inspection is unavailable or reports invalid state.") from exc
    require(not errors and state == canonical, "invalid_task", "Canonical Task fails the installed read-only validator.", {"codes": [e.get("code") for e in errors]})
    return state, helper


def check_role(root, role):
    helper = installed_helper(root, "role")
    catalog = helper.build_catalog(Path(root))
    try:
        entry = helper.find_valid_role(catalog, role["name"])
    except helper.CatalogError as exc:
        raise MemoryError("role_ineligible", "Role does not qualify in the current filesystem catalog.") from exc
    require(entry.valid and entry.agents_file == role["agents_path"] and entry.role_file == role["role_path"], "role_ineligible", "Current role pair is not eligible.")
    for key, hashkey in (("agents_path", "agents_sha256"), ("role_path", "role_sha256")):
        require(sha256(safe_read_bytes(root, role[key])) == role[hashkey], "role_changed", "Role provenance is historical; inspect the current pair.")


def check_origin(root, origin):
    if origin["task_id"] is not None:
        state, _ = read_task(root, origin["task_path"])
        require(state["task_id"] == origin["task_id"], "false_origin", "Task origin ID does not match its canonical source.")
        if origin["execution_id"] is not None:
            orch = state.get("orchestration", {})
            require(orch.get("execution_id") == origin["execution_id"] and orch.get("generation") == origin["generation"],
                    "execution_changed", "The cited execution/generation is not the current canonical origin.")
    if origin["role"] is not None:
        check_role(root, origin["role"])


def _locator(raw, locator):
    match = re.fullmatch(r"lines?:(\d+)(?:-(\d+))?", locator)
    if match:
        start, end = int(match[1]), int(match[2] or match[1])
        require(1 <= start <= end <= len(raw.decode("utf-8").splitlines()), "invalid_locator", "Line locator is outside the cited source.")
        return
    if locator.startswith("section:"):
        wanted = locator[8:].strip()
        require(wanted and wanted in raw.decode("utf-8"), "invalid_locator", "Section locator is absent from the source.")
        return
    if locator.startswith("label:"):
        require(("\\label{" + locator[6:] + "}").encode() in raw, "invalid_locator", "TeX label is absent from the source.")
        return
    if locator.startswith("json:"):
        value = decode_json_yaml(raw)
        for part in locator[5:].strip("/").split("/") if locator[5:].strip("/") else []:
            part = part.replace("~1", "/").replace("~0", "~")
            try:
                value = value[int(part)] if isinstance(value, list) else value[part]
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                raise MemoryError("invalid_locator", "JSON pointer is absent from the source.") from exc
        return
    if re.fullmatch(r"page:[1-9][0-9]*", locator):
        require(raw.startswith(b"%PDF"), "invalid_locator", "Page locator requires a PDF source.")
        # No optional extractor is imported by the core. The exact byte digest
        # is checked; page content needs the separate extraction/visual route.
        return
    require(locator == "document", "invalid_locator", "Supported locators are document, line(s), section, label, json, and page.")


def _verification(root, raw, claim_level):
    receipt = decode_json_yaml(raw)
    exact(receipt, ("schema_version", "claim_level", "outcome", "command", "observed_at", "artifacts"), ("limitations", "details"))
    require(receipt["schema_version"] == 1 and receipt["claim_level"] == claim_level, "claim_unsupported", "Verification receipt does not support this claim level.")
    outcomes = {"performed_work": {"performed"}, "verified_outcome": {"passed"},
                "observed_failure": {"failed"}, "cancelled_work": {"cancelled"}}
    require(receipt["outcome"] in outcomes.get(claim_level, set()), "claim_unsupported", "Observed outcome does not support the stated claim.")
    text(receipt["command"]); timestamp(receipt["observed_at"])
    require(isinstance(receipt["artifacts"], list) and 1 <= len(receipt["artifacts"]) <= 200, "claim_unsupported", "Performed-work receipts require inspected artifact versions.")
    for ref in receipt["artifacts"]:
        exact(ref, ("path", "sha256")); digest(ref["sha256"])
        require(sha256(safe_read_bytes(root, ref["path"])) == ref["sha256"], "evidence_changed", "Observed artifact differs from the verification receipt.")


def inspect_evidence(root, record, config=None):
    diagnostics = []
    meta = record["metadata"]
    level = meta["claim"]["level"]
    supported = level == "historical_context"
    for source in meta["sources"]:
        try:
            raw = safe_read_bytes(root, source["path"])
            require(sha256(raw) == source["sha256"], "evidence_changed", "Source bytes changed; historical conclusions require applicability review.")
            if not raw.startswith(b"%PDF"):
                reject_sensitive(raw.decode("utf-8"))
            _locator(raw, source["locator"])
            if level == "accepted_design" and source["kind"] == "design":
                supported = True
            elif source["kind"] == "verification" and level != "historical_context":
                _verification(root, raw, level)
                supported = True
        except (MemoryError, UnicodeDecodeError) as exc:
            diagnostics.append({"code": exc.code if isinstance(exc, MemoryError) else "invalid_encoding",
                                "severity": "warning", "path": source["path"],
                                "message": "Evidence is changed, missing, unsafe, or cannot support the claim; this does not prove the historical conclusion false."})
    if not supported:
        diagnostics.append({"code": "claim_unsupported", "severity": "error", "message": "Current cited evidence does not support the stated claim level."})
    try:
        check_origin(root, meta["origin"])
    except MemoryError as exc:
        diagnostics.append({"code": exc.code, "severity": "warning", "message": "Origin is absent, changed, or ineligible; current Task and role sources retain authority."})
    return diagnostics


def validate_publication_evidence(root, record, config=None):
    diagnostics = inspect_evidence(root, record, config)
    require(not diagnostics, "evidence_unqualified", "Publication requires current evidence and real origin references.", {"diagnostics": diagnostics})
    return diagnostics
