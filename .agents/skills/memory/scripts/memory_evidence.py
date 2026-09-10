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


def _retained_companion(root, receipt_path, raw, receipt):
    """Optional reviewed proof locator for an unchanged legacy receipt."""
    companion_path = "Verification/project-memory/evidence/verification-" + sha256(raw) + ".json"
    target = safe_path(root, companion_path, must_exist=False)
    if not target.exists():
        return receipt, None
    companion_raw = safe_read_bytes(root, companion_path, max_bytes=250000)
    reject_sensitive(companion_raw.decode("utf-8"))
    companion = decode_json_yaml(companion_raw)
    exact(companion, ("schema_version", "receipt", "applicability", "artifacts"))
    require(companion["schema_version"] == 1 and companion["applicability"] == "historical",
            "evidence_companion", "A retained-proof companion has historical applicability only.")
    require(companion["receipt"] == {"path": receipt_path, "sha256": sha256(raw)},
            "evidence_companion_mismatch", "Companion does not bind the exact original receipt path and digest.")
    require(isinstance(companion["artifacts"], list) and len(companion["artifacts"]) == len(receipt["artifacts"]),
            "evidence_companion_mismatch", "Companion must preserve every original artifact reference.")
    for original, retained in zip(receipt["artifacts"], companion["artifacts"]):
        exact(retained, ("path", "sha256", "retained_path"))
        require({key: retained[key] for key in ("path", "sha256")} == {key: original[key] for key in ("path", "sha256")},
                "evidence_companion_mismatch", "Companion must preserve original artifact order, paths and digests.")
    return {**receipt, "artifacts": companion["artifacts"], "applicability": "historical"}, {
        "path": companion_path, "sha256": sha256(companion_raw), "purpose": "historical proof locator; no new execution claim"}


def _verification(root, raw, claim_level, receipt_path=None):
    receipt = decode_json_yaml(raw)
    exact(receipt, ("schema_version", "claim_level", "outcome", "command", "observed_at", "artifacts"),
          ("limitations", "details", "applicability"))
    require(receipt["schema_version"] == 1 and receipt["claim_level"] == claim_level, "claim_unsupported", "Verification receipt does not support this claim level.")
    outcomes = {"performed_work": {"performed"}, "verified_outcome": {"passed"},
                "observed_failure": {"failed"}, "cancelled_work": {"cancelled"}}
    require(receipt["outcome"] in outcomes.get(claim_level, set()), "claim_unsupported", "Observed outcome does not support the stated claim.")
    text(receipt["command"]); timestamp(receipt["observed_at"])
    require(receipt.get("applicability", "current") in {"current", "historical"},
            "evidence_applicability", "Receipt applicability must be current or historical.")
    require(isinstance(receipt["artifacts"], list) and 1 <= len(receipt["artifacts"]) <= 200, "claim_unsupported", "Performed-work receipts require inspected artifact versions.")
    receipt, companion = _retained_companion(root, receipt_path, raw, receipt) if receipt_path else (receipt, None)
    artifacts, diagnostics, retained_bytes, seen = [], [], 0, set()
    for ref in receipt["artifacts"]:
        exact(ref, ("path", "sha256"), ("retained_path",)); digest(ref["sha256"]); text(ref["path"])
        require(ref["path"] not in seen, "evidence_duplicate", "Verification artifacts must be distinct.")
        seen.add(ref["path"])
        item = {"path": ref["path"], "expected_sha256": ref["sha256"],
                "current_sha256": None, "historical_support": "unsupported", "current_applicability": "unverified",
                "retained_path": ref.get("retained_path"), "retained": False}
        try:
            current = safe_read_bytes(root, ref["path"])
            item["current_sha256"] = sha256(current)
            item["current_applicability"] = "current" if item["current_sha256"] == ref["sha256"] else "changed"
            if item["current_applicability"] == "current":
                item["historical_support"] = "supported"
        except MemoryError as exc:
            item["current_error"] = exc.as_dict()
        if "retained_path" in ref:
            try:
                retained = ref["retained_path"]
                require(isinstance(retained, str) and retained.startswith(("Verification/", "control_records/memory/evidence/"))
                        and retained != ref["path"], "evidence_retention_scope", "Retained proof needs a distinct governed evidence path.")
                archived = safe_read_bytes(root, retained, max_bytes=16_000_000 - retained_bytes)
                retained_bytes += len(archived)
                require(sha256(archived) == ref["sha256"], "retained_evidence_changed", "Retained bytes differ from the observed artifact.",
                        {"path": retained, "expected_sha256": ref["sha256"], "current_sha256": sha256(archived)})
                if not archived.startswith(b"%PDF"):
                    reject_sensitive(archived.decode("utf-8"))
                item.update(retained=True, historical_support="supported")
            except (MemoryError, UnicodeDecodeError) as exc:
                item["historical_support"] = "unsupported"
                diagnostics.append({"code": exc.code if isinstance(exc, MemoryError) else "invalid_encoding",
                                    "severity": "warning", "path": ref["path"], "retained_path": ref["retained_path"],
                                    "expected_sha256": ref["sha256"], "message": "Selected retained proof is absent, altered, unsafe, or unavailable."})
        if item["current_applicability"] != "current":
            diagnostics.append({"code": "evidence_changed" if item["current_sha256"] else "evidence_artifact_absent",
                                "severity": "info" if item["historical_support"] == "supported" else "warning", "path": ref["path"], "expected_sha256": ref["sha256"],
                                "current_sha256": item["current_sha256"], "historical_support": item["historical_support"],
                                "message": "Observed artifact version is not current; this does not prove the historical observation false."})
        if item["historical_support"] != "supported":
            diagnostics.append({"code": "historical_evidence_unsupported", "severity": "warning", "path": ref["path"],
                                "expected_sha256": ref["sha256"], "message": "Exact observed bytes are not accessible as valid proof."})
        artifacts.append(item)
    if receipt.get("applicability") == "historical":
        diagnostics.append({"code": "claim_not_current", "severity": "info",
                            "message": "The verification receipt explicitly limits this observation to historical applicability."})
    historical = all(a["historical_support"] == "supported" for a in artifacts)
    current = all(a["current_applicability"] == "current" for a in artifacts)
    return {"historical_support": "supported" if historical else "unsupported",
            "current_applicability": "current" if current else "changed" if any(a["current_applicability"] == "changed" for a in artifacts) else "unverified",
            "durable": all(a["retained"] for a in artifacts), "applicability": receipt.get("applicability", "legacy-current"),
            "observed_at": receipt["observed_at"], "companion": companion, "artifacts": artifacts, "diagnostics": diagnostics}


def _retained_direct_source(root, source, verifications):
    """Resolve only exact proof already qualified by this record's receipts."""
    for verification in verifications:
        if (verification["historical_support"] != "supported"
                or any(d["severity"] != "info" for d in verification["diagnostics"])):
            continue
        for artifact in verification["artifacts"]:
            if (artifact["path"] != source["path"] or artifact["expected_sha256"] != source["sha256"]
                    or not artifact["retained"]):
                continue
            raw = safe_read_bytes(root, artifact["retained_path"], max_bytes=16_000_000)
            require(sha256(raw) == source["sha256"], "retained_evidence_changed",
                    "Retained direct-source proof changed after receipt inspection.",
                    {"path": artifact["retained_path"], "expected_sha256": source["sha256"], "current_sha256": sha256(raw)})
            if not raw.startswith(b"%PDF"):
                reject_sensitive(raw.decode("utf-8"))
            _locator(raw, source["locator"])
            return {"receipt_path": verification["receipt_path"], "receipt_sha256": verification["receipt_sha256"],
                    "retained_path": artifact["retained_path"], "retained_sha256": sha256(raw)}
    return None


def assess_evidence(root, record, config=None):
    diagnostics, verifications = [], []
    source_integrity = True
    meta = record["metadata"]
    level = meta["claim"]["level"]
    supported = level == "historical_context"
    # A direct old source can use its exact retained receipt proof regardless
    # of citation order. Design/context citations do not create such proof.
    for source in sorted(meta["sources"], key=lambda item: item["kind"] != "verification"):
        try:
            raw = safe_read_bytes(root, source["path"])
            require(sha256(raw) == source["sha256"], "evidence_changed", "Cited evidence bytes changed.",
                    {"path": source["path"], "expected_sha256": source["sha256"], "current_sha256": sha256(raw)})
            if not raw.startswith(b"%PDF"):
                reject_sensitive(raw.decode("utf-8"))
            _locator(raw, source["locator"])
            if level == "accepted_design" and source["kind"] == "design":
                supported = True
            elif source["kind"] == "verification" and level != "historical_context":
                verification = _verification(root, raw, level, source["path"])
                verification["receipt_path"] = source["path"]
                verification["receipt_sha256"] = source["sha256"]
                verifications.append(verification)
                diagnostics.extend(dict(d, receipt_path=source["path"]) for d in verification["diagnostics"])
                supported = supported or verification["historical_support"] == "supported"
        except (MemoryError, UnicodeDecodeError) as exc:
            if (source["kind"] == "source" and isinstance(exc, MemoryError)
                    and exc.code in {"evidence_changed", "file_absent"}):
                try:
                    retained = _retained_direct_source(root, source, verifications)
                    if retained is not None:
                        diagnostics.append({"code": "current_source_changed", "severity": "info", "path": source["path"],
                                            "expected_sha256": source["sha256"], "current_sha256": exc.details.get("current_sha256"),
                                            "historical_support": "supported", **retained,
                                            "message": "The direct source is changed or absent; exact retained verification bytes support its historical locator only."})
                        continue
                except (MemoryError, UnicodeDecodeError) as retained_error:
                    exc = retained_error
            source_integrity = False
            detail = exc.as_dict() if isinstance(exc, MemoryError) else {"code": "invalid_encoding", "details": {}}
            diagnostics.append({"code": detail["code"], "severity": "warning", "path": source["path"],
                                "details": detail["details"],
                                "message": "Evidence is changed, missing, unsafe, or cannot support the claim; this does not prove the historical conclusion false."})
    if not supported:
        diagnostics.append({"code": "claim_unsupported", "severity": "error", "message": "Accessible cited evidence does not support the stated claim level."})
    try:
        check_origin(root, meta["origin"])
    except MemoryError as exc:
        diagnostics.append({"code": exc.code, "severity": "warning", "details": exc.details,
                            "message": "Origin is absent, changed, or ineligible; current Task and role sources retain authority."})
    applicability = ("not_claimed" if level == "historical_context" else
                     "changed" if any(v["current_applicability"] == "changed" for v in verifications) else
                     "unverified" if diagnostics or any(v["applicability"] == "historical" for v in verifications) else "current")
    return {"historical_support": ("context_only" if level == "historical_context" and not diagnostics else
                                   "supported" if supported and source_integrity and not any(v["historical_support"] == "unsupported" for v in verifications) else "unsupported"),
            "current_applicability": applicability, "durable": bool(verifications) and all(v["durable"] for v in verifications),
            "verified_current": level == "verified_outcome" and applicability == "current" and not diagnostics and meta["state"] == "active",
            "verifications": verifications, "diagnostics": diagnostics}


def inspect_evidence(root, record, config=None):
    """Legacy list interface; richer support/applicability is available separately."""
    return assess_evidence(root, record, config)["diagnostics"]


def validate_publication_evidence(root, record, config=None):
    evidence = assess_evidence(root, record, config)
    require(not evidence["diagnostics"], "evidence_unqualified", "Publication requires supported evidence and real origin references.", {"diagnostics": evidence["diagnostics"]})
    if record["metadata"]["claim"]["level"] == "verified_outcome":
        require(evidence["durable"] and evidence["current_applicability"] == "current"
                and all(v["applicability"] == "current" for v in evidence["verifications"]),
                "durable_evidence_required", "New verified claims require retained observed bytes and explicit current applicability; legacy records remain readable.")
    return evidence["diagnostics"]
