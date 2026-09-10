"""Explicit guard enablement and exact pre/post repair in ontology control records.

The setup grant is separate from semantic publication. It reuses the current
ontology authorizer's native identity, time, Director and Task ownership checks.
"""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import re

from ontology_core import load_project, atomic_write, operation_lock, canonical_bytes, sha256
from ontology_guards import (GuardError, fail, digest, read_bound, checked_path, profile,
                             FAMILIES, normalize)
from ontology_authority import (validate_native_observation, validate_director_binding,
                                active_managers, read_task, within)

CONTROL = "control_records/ontology/guard-bootstrap/"
CASES = {"positive", "invalid", "unauthorized", "stale", "ambiguous", "backend-failure"}


def _read(root, path):
    return json.loads(checked_path(root, path).read_bytes())


def _binding(root, path):
    return {"path": path, "sha256": digest(checked_path(root, path).read_bytes())}


def coverage_manifest(root, contract):
    """Inspect actual installed declarations; no source or test run is invented."""
    from ontology_guards import validate_contract
    validate_contract(contract)
    grouped = {family: {} for family in FAMILIES}
    for action in contract["actions"] + contract.get("optional_actions", []):
        family, operation = action["family"], action["operation"]
        fail(family in FAMILIES, "guard_coverage", "Unknown action family.")
        path, symbol = action["dispatch"]["path"], action["dispatch"]["symbol"]
        source = checked_path(root, path)
        fail(source.is_file(), "guard_coverage", "Required owning adapter is missing.", path=path)
        tree = ast.parse(source.read_text())
        if action in contract.get("optional_actions", []) and not any(isinstance(node, ast.FunctionDef) and node.name == symbol for node in tree.body):
            continue
        declarations = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "ONTOLOGY_GUARDED_ACTIONS" for target in node.targets):
                declarations = ast.literal_eval(node.value)
        fail(symbol in declarations or operation in declarations, "guard_coverage", "Owning helper does not declare this guarded action.", path=path, operation=operation)
        grouped[family].setdefault(path, []).append(operation)
    fail(all(grouped.values()), "guard_coverage", "All eight declared action families must be installed before enablement.")
    return {"schema_version": 1, "families": {family: [dict(_binding(root, path), operations=sorted(operations))
            for path, operations in sorted(paths.items())] for family, paths in sorted(grouped.items())}}


def _verify_evidence(root, binding, adapters):
    evidence = json.loads(read_bound(root, binding))
    fail(evidence.get("schema_version") == 1 and evidence.get("backend") == "actual-selected-standards"
         and evidence.get("status") == "passed", "guard_verification", "Guard enablement requires actual selected-backend dispatch evidence.")
    observed = evidence.get("observations", [])
    fail(isinstance(observed, list), "guard_verification", "Malformed dispatch observations.")
    for family in FAMILIES:
        rows = [row for row in observed if row.get("family") == family and row.get("passed") is True]
        fail(CASES <= {row.get("case") for row in rows}, "guard_verification", "A family is missing required actual dispatch cases.", family=family)
        fail(any(row.get("reopened") is True for row in rows if row.get("case") == "positive"), "guard_verification", "Positive helper result must be reopened.", family=family)
        fail(all(row.get("intended_side_effect") is False for row in rows if row.get("case") != "positive"), "guard_verification", "Negative requests must establish no intended side effect.", family=family)
    fail(evidence.get("adapters_sha256") == digest(adapters), "guard_verification_stale", "Dispatch evidence belongs to different helper bytes.")
    for row in observed:
        if row.get("case") != "positive":
            continue
        helpers = row.get("receipt", {}).get("ontology_guard", {}).get("backend_context", {}).get("helpers", {})
        for name in ("ontology_guards.py", "ontology_guard_setup.py"):
            fail(helpers.get(name) == digest(checked_path(root, ".agents/skills/ontology/scripts/" + name).read_bytes()),
                 "guard_verification_stale", "Dispatch evidence belongs to different guard-engine or repair code.", helper=name)
    return evidence


def _backend(root, shapes, request=None):
    from ontology_standards import validate
    request = request or {"operation": "guard-setup", "phase": "preview"}
    base = "urn:sys4ai:ontology:action:"
    node = base + "setup-check:" + digest(request)
    # An interrupted upgrade retains its accepted old rules. Fresh new setup
    # code must still evaluate that old request class when resuming the intent.
    request_type = "GuardSetupRequest" if "action:GuardSetupRequest" in shapes or base + "GuardSetupRequest" in shapes else "Request"
    result = validate(root, triples=[
        [node, "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", base + request_type],
        [node, base + "family", {"value": "setup"}],
        [node, base + "operation", {"value": request["operation"]}],
        [node, base + "requestDigest", {"value": digest(request)}],
        [node, base + "targetDigest", {"value": digest(request.get("changes", []))}]],
        shapes=shapes, limits={"query_seconds": 5, "reasoning_seconds": 5})
    fail(isinstance(result, dict) and result.get("status") == "conformant" and result.get("complete") is True,
         "guard_unavailable", "Guard setup or repair requires the actual available standards validator.", backend=result)
    return result


def _change(root, path, content):
    file = checked_path(root, path)
    return {"path": path, "expected_sha256": digest(file.read_bytes()) if file.exists() else None,
            "sha256": digest(content.encode()), "content": content}


def preview_enablement(root, *, operation_id, contract, repair, verification):
    root = Path(root).absolute()
    fail(profile(root) is None, "guard_already_enabled", "Use selected exact repair for an enabled guard.")
    fail(re.fullmatch(r"ONTGUARD-[A-Za-z0-9-]{4,100}", operation_id), "guard_schema", "Use a stable ONTGUARD operation identity.")
    config = _read(root, "ontology-advanced.yaml")
    definitions = json.loads(read_bound(root, contract))
    repair_contract = json.loads(read_bound(root, repair))
    fail(repair_contract.get("schema_version") == 1 and repair_contract.get("profile_disable") == "forbidden", "guard_repair_contract", "Missing immutable fail-closed repair contract.")
    adapters = coverage_manifest(root, definitions)
    _verify_evidence(root, verification, adapters)
    shapes = read_bound(root, definitions["shapes"]).decode()
    backend = _backend(root, shapes)
    adapters_path = CONTROL + operation_id + "-adapters.json"
    bootstrap_path = CONTROL + operation_id + "-bootstrap.json"
    adapter_binding = {"path": adapters_path, "sha256": digest(canonical_bytes(adapters))}
    bootstrap = {"schema_version": 1, "status": "verified", "operation_id": operation_id,
                 "contract": contract, "repair": repair, "adapters": adapter_binding, "verification": verification,
                 "engine": _binding(root, ".agents/skills/ontology/scripts/ontology_guards.py"),
                 "setup": _binding(root, ".agents/skills/ontology/scripts/ontology_guard_setup.py")}
    selected = {"enabled": True, "contract": contract, "adapters": adapter_binding,
                "bootstrap": {"path": bootstrap_path, "sha256": digest(canonical_bytes(bootstrap))}}
    config["profiles"]["guards"] = selected
    changes = [_change(root, adapters_path, canonical_bytes(adapters).decode()),
               _change(root, bootstrap_path, canonical_bytes(bootstrap).decode()),
               _change(root, "ontology-advanced.yaml", canonical_bytes(config).decode())]
    return _preview(root, operation_id, "guard-setup", changes, repair_contract, shapes, backend,
                    {"contract": contract, "repair": repair, "verification": verification})


def _preview(root, operation_id, operation, changes, repair_contract, shapes, backend, inputs):
    payload = {"schema_version": 1, "operation_id": operation_id, "operation": operation,
               "changes": changes, "reason": "Apply this exact reviewed guard capability setup or repair."}
    _validate_changes(root, payload, repair_contract)
    current = {change["path"]: checked_path(root, change["path"]).read_text() if change["expected_sha256"] is not None else None for change in changes}
    result = {"schema_version": 1, "payload": payload, "prior_contents": current,
              "repair_contract": repair_contract, "retained_shapes": shapes, "inputs": inputs,
              "governance": [_binding(root, name) for name in ("SOUL.md", "AGENTS.md", "ROLE.md")],
              "backend_context": backend.get("context"), "old_config_sha256": digest(checked_path(root, "ontology-advanced.yaml").read_bytes())}
    result["preview_sha256"] = digest(result)
    _validate_bundle(root, result)
    return result


def _validate_bundle(root, preview):
    """Validate future bindings without executing any candidate helper code."""
    overrides = {row["path"]: row["content"].encode() for row in preview["payload"]["changes"]}
    def data(path):
        return overrides[path] if path in overrides else checked_path(root, path).read_bytes()
    def bound(ref):
        fail(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "guard_schema", "Malformed proposed guard binding.")
        raw = data(ref["path"])
        fail(digest(raw) == ref["sha256"], "guard_stale", "Proposed guard dependency differs from its selected digest.", path=ref["path"])
        return raw
    config = json.loads(data("ontology-advanced.yaml"))
    selected = config.get("profiles", {}).get("guards", {})
    fail(set(selected) == {"enabled", "contract", "adapters", "bootstrap"} and selected["enabled"] is True,
         "guard_disable_forbidden", "Setup must retain a complete enabled guard profile.")
    definitions = json.loads(bound(selected["contract"]))
    from ontology_guards import validate_contract
    validate_contract(definitions)
    adapters = json.loads(bound(selected["adapters"]))
    bootstrap = json.loads(bound(selected["bootstrap"]))
    fail(bootstrap.get("contract") == selected["contract"] and bootstrap.get("adapters") == selected["adapters"]
         and bootstrap.get("status") == "verified", "guard_bootstrap", "Proposed bootstrap omits the exact contract and adapter hashes.")
    bound(bootstrap["repair"])
    bound(bootstrap["engine"])
    bound(bootstrap["setup"])
    bound(definitions["shapes"])
    fail(set(adapters.get("families", {})) == FAMILIES, "guard_coverage", "Proposed guard bundle omits an action family.")
    for family in adapters["families"].values():
        fail(isinstance(family, list) and family, "guard_coverage", "Proposed action family has no adapters.")
        for adapter in family:
            raw = bound({key: adapter[key] for key in ("path", "sha256")})
            tree = ast.parse(raw)
            declared = []
            for node in tree.body:
                if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "ONTOLOGY_GUARDED_ACTIONS" for target in node.targets):
                    declared = ast.literal_eval(node.value)
            fail(all(op in declared or "Store." + op in declared for op in adapter["operations"]), "guard_coverage", "Proposed helper lost a declared public adapter.")


def preview_repair(root, *, operation_id, changes):
    root = Path(root).absolute()
    selected = profile(root)
    fail(selected is not None, "guard_disabled", "Exact guard repair requires an enabled profile.")
    from ontology_guards import _context
    definitions, _, _ = _context(root, selected, {})
    bootstrap = json.loads(read_bound(root, selected["bootstrap"]))
    repair_contract = json.loads(read_bound(root, bootstrap["repair"]))
    shapes = read_bound(root, definitions["shapes"]).decode()
    backend = _backend(root, shapes)
    return _preview(root, operation_id, "guard-repair", copy.deepcopy(changes), repair_contract, shapes,
                    backend, {"bootstrap": selected["bootstrap"], "repair": bootstrap["repair"]})


def _validate_changes(root, payload, repair_contract):
    fail(payload.get("operation") in {"guard-setup", "guard-repair"}, "guard_schema", "Unsupported setup operation.")
    fail(isinstance(payload.get("operation_id"), str) and re.fullmatch(r"ONTGUARD-[A-Za-z0-9-]{4,100}", payload["operation_id"]), "guard_schema", "Malformed setup operation identity.")
    changes = payload.get("changes")
    fail(isinstance(changes, list) and 1 <= len(changes) <= repair_contract["maximum_changes"], "guard_schema", "Invalid bounded setup manifest.")
    seen = set()
    for change in changes:
        fail(isinstance(change, dict) and set(change) == {"path", "expected_sha256", "sha256", "content"}, "guard_schema", "Malformed exact repair change.")
        name = change["path"]
        checked_path(root, name)
        fail(name not in seen and (name == "ontology-advanced.yaml" or any(within(name, prefix) for prefix in repair_contract["allowed_prefixes"])), "guard_scope", "Repair selected duplicate or ungranted files.", path=name)
        seen.add(name)
        fail(isinstance(change["content"], str) and digest(change["content"].encode()) == change["sha256"], "guard_stale", "Repair post-content differs from review.")
        if name == "ontology-advanced.yaml":
            value = json.loads(change["content"])
            fail(value.get("profiles", {}).get("guards", {}).get("enabled") is True, "guard_disable_forbidden", "Repair cannot disable the guard.")
            current = _read(root, name)
            old_other, new_other = copy.deepcopy(current), copy.deepcopy(value)
            old_other.get("profiles", {}).pop("guards", None)
            new_other.get("profiles", {}).pop("guards", None)
            fail(old_other == new_other, "guard_scope", "Guard setup may change its own profile only; backend, publication, imports and limits require their separately selected owner.")


def authorize_setup(root, grant, preview):
    """Exact setup authority remains separate from a semantic publication grant."""
    required = {"schema_version", "operation", "preview_sha256", "actor_id", "actor_kind", "observed_at", "expires_at",
                "native_receipt", "scope", "reviewed_records", "task", "project_id", "config_sha256"}
    fail(isinstance(grant, dict) and set(grant) == required and grant["schema_version"] == 1, "guard_grant_schema", "Use the separately reviewed exact setup grant.")
    project = load_project(root, validate=False)
    payload = preview["payload"]
    fail(grant["project_id"] == project.project_id and grant["operation"] == payload["operation"] and grant["preview_sha256"] == preview["preview_sha256"], "guard_grant_scope", "Setup grant does not select this exact project, operation and review.")
    fail(grant["config_sha256"] == sha256(checked_path(root, "ontology.yaml")), "guard_grant_stale", "Core authority configuration changed after setup review.")
    validate_native_observation(grant)
    paths = [change["path"] for change in payload["changes"]]
    fail(grant["scope"] == paths and grant["reviewed_records"] == [{key: change[key] for key in ("path", "expected_sha256", "sha256")} for change in payload["changes"]], "guard_grant_scope", "Setup grant must bind every exact selected pre/post file.")
    if grant["actor_kind"] == "director":
        fail(grant["task"] is None, "guard_grant_scope", "Director setup grant cannot claim a Task owner.")
        validate_director_binding(project, grant["actor_id"])
        for _, _, assignment in active_managers(root):
            fail(not any(within(path, scope) or within(scope, path) for path in paths for scope in assignment.get("fit", {}).get("writes", [])), "guard_manager_owns_scope", "An unreconciled manager owns a selected repair path.")
    else:
        binding = grant["task"]
        fail(isinstance(binding, dict) and set(binding) == {"path", "sha256", "task_id", "execution_id", "generation", "assignment_id"}, "guard_grant_schema", "Manager setup requires its exact Task binding.")
        read_bound(root, {key: binding[key] for key in ("path", "sha256")})
        state, helper = read_task(root, binding["path"])
        orch = state.get("orchestration", {})
        assignment = orch.get("assignments", {}).get(binding["assignment_id"], {})
        fail(state["task_id"] == binding["task_id"] and orch.get("stage") == "active" and orch.get("execution_id") == binding["execution_id"] and orch.get("generation") == binding["generation"] and orch.get("manager_id") == binding["assignment_id"] and orch.get("writer") == grant["actor_id"] and assignment.get("state") == "active" and assignment.get("native_id") == grant["actor_id"], "guard_manager_unconfirmed", "Manager identity or generation changed after setup review.")
        fail(assignment.get("function") == "manager" and assignment.get("generation") == binding["generation"]
             and assignment.get("role_reads") and helper.orch.receipt(assignment["native_receipt"], launch=True) == grant["actor_id"],
             "guard_manager_unconfirmed", "Current setup owner lacks confirmed manager role reads or launch identity.")
        helper.orch.role(assignment["role"], root)
        fail(all(any(within(path, prefix) for prefix in assignment.get("fit", {}).get("writes", [])) for path in paths), "guard_manager_scope", "Selected repair exceeds current manager writes.")
        for other_path, _, other in active_managers(root):
            if other_path != binding["path"]:
                fail(not any(within(path, scope) or within(scope, path) for path in paths for scope in other.get("fit", {}).get("writes", [])),
                     "guard_manager_owns_scope", "Another unreconciled manager owns a selected repair path.")
    return grant


def apply(root, preview, grant, *, fail_after=None):
    """Resume immutable accepted setup with current authority and retained rules."""
    root = Path(root).absolute()
    fail(isinstance(preview, dict) and preview.get("schema_version") == 1, "guard_schema", "Malformed guard setup review.")
    content = dict(preview)
    reviewed = content.pop("preview_sha256", None)
    fail(digest(content) == reviewed, "guard_stale", "Reviewed setup content changed.")
    payload = preview["payload"]
    _validate_changes(root, payload, preview["repair_contract"])
    _validate_bundle(root, preview)
    # Retained rules are data under the actual same constrained backend. Missing
    # or failed validation cannot enter the authorization or mutation stage.
    _backend(root, preview["retained_shapes"], payload)
    authorize_setup(root, grant, preview)
    intent_path = CONTROL + payload["operation_id"] + "-intent.json"
    receipt_path = CONTROL + payload["operation_id"] + "-receipt.json"
    with operation_lock(root, "control_records/ontology/publication.lock"):
        _backend(root, preview["retained_shapes"], payload)
        authorize_setup(root, grant, preview)
        for binding in preview["governance"]:
            read_bound(root, binding)
        intent = checked_path(root, intent_path)
        if intent.exists():
            accepted = _read(root, intent_path)
            fail(accepted.get("review") == preview, "guard_stale", "Accepted setup identity belongs to a different immutable review.")
        else:
            fail(digest(checked_path(root, "ontology-advanced.yaml").read_bytes()) == preview["old_config_sha256"],
                 "guard_stale", "Guard configuration changed before accepting the exact setup intent.")
            for binding in preview["inputs"].values():
                read_bound(root, binding)
            selected = profile(root)
            if payload["operation"] == "guard-repair":
                from ontology_guards import _context
                definitions, _, _ = _context(root, selected, {})
                fail(read_bound(root, definitions["shapes"]).decode() == preview["retained_shapes"], "guard_stale", "Repair substituted its retained semantic rules.")
        for change in payload["changes"]:
            file = checked_path(root, change["path"])
            current = digest(file.read_bytes()) if file.exists() else None
            fail(current in {change["expected_sha256"], change["sha256"]}, "guard_repair_unknown_state", "Repair target is neither accepted pre-state nor post-state.", path=change["path"])
        if not intent.exists():
            accepted = {"schema_version": 1, "review": preview, "accepted_actor": grant["actor_id"], "accepted_grant_sha256": digest(grant)}
            atomic_write(root, intent_path, canonical_bytes(accepted), None)
        states = []
        # The companion is always last, so interrupted upgrades retain enabled
        # old configuration until its selected new dependency files are ready.
        for index, change in enumerate(sorted(payload["changes"], key=lambda row: row["path"] == "ontology-advanced.yaml")):
            authorize_setup(root, grant, preview)
            file = checked_path(root, change["path"])
            current = digest(file.read_bytes()) if file.exists() else None
            if current == change["expected_sha256"]:
                atomic_write(root, change["path"], change["content"].encode(), current)
            fail(digest(file.read_bytes()) == change["sha256"], "guard_repair_post_conflict", "Reopened repair target differs from accepted post-state.")
            states.append({"path": change["path"], "sha256": change["sha256"], "state": "committed"})
            if fail_after is not None and index + 1 == fail_after:
                raise GuardError("guard_repair_interrupted", "Setup was interrupted; resume its exact retained review.", {"intent": intent_path, "committed": states})
        # Verify the new enabled graph of exact guard dependencies, including all
        # adapter hashes, before issuing a completed operation receipt.
        from ontology_guards import _context
        _context(root, profile(root), {})
        receipt = {"schema_version": 1, "operation_id": payload["operation_id"], "operation": payload["operation"],
                   "status": "complete", "preview_sha256": reviewed, "actor_id": grant["actor_id"], "files": states,
                   "accepted_actor": accepted["accepted_actor"], "accepted_grant_sha256": accepted["accepted_grant_sha256"],
                   "semantic_validation": "conformant", "authorization": "current_setup_grant", "post_verification": "reopened_exact_hashes"}
        file = checked_path(root, receipt_path)
        if file.exists():
            previous = _read(root, receipt_path)
            fail(all(previous.get(key) == receipt[key] for key in receipt if key != "actor_id"), "guard_receipt_conflict", "A different immutable repair receipt already exists.")
            return previous
        else:
            atomic_write(root, receipt_path, canonical_bytes(receipt), None)
        return receipt


def recover(root, operation_id, grant, *, fail_after=None):
    fail(isinstance(operation_id, str) and re.fullmatch(r"ONTGUARD-[A-Za-z0-9-]{4,100}", operation_id), "guard_schema", "Malformed exact recovery identity.")
    return apply(root, _read(root, CONTROL + operation_id + "-intent.json")["review"], grant, fail_after=fail_after)
