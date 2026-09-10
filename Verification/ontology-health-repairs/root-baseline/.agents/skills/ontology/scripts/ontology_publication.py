"""Exact reviewed canonical publication with immutable accepted intents and receipts."""
from pathlib import Path
import copy
import re
from ontology_core import (OntologyError, load_project, canonical_bytes, sha256, safe_path, read_json,
                           read_bytes, decode_json, require, exact, digest, atomic_write, operation_lock)
from ontology_validate import validate_project
from ontology_lifecycle import validate_transition
from ontology_authority import authorize

CONTROL = "control_records/ontology/"
ONTOLOGY_GUARDED_ACTIONS = ["preview", "publish", "recover"]


def _guard(root, operation, arguments, targets):
    from ontology_guards import begin_action, require_adapter, GuardError
    try:
        decision = begin_action(root, "ontology", operation, arguments, targets)
        require_adapter(decision, __file__)
        return decision
    except GuardError as exc:
        raise OntologyError(exc.code, str(exc)) from exc


def _recheck(decision, *, targets=True):
    from ontology_guards import GuardError
    try:
        decision.recheck(targets=targets)
        if targets and decision.operation != "preview":
            decision.lock_checked = True
    except GuardError as exc:
        raise OntologyError(exc.code, str(exc)) from exc


def _root(value):
    path = Path(value).absolute()
    require(path.is_dir() and not path.is_symlink() and path == path.resolve(), "unsafe_root", "Select an existing resolved project root without symlink aliases.")
    return path


def check_proposal(root, proposal):
    exact(proposal, ("schema_version", "operation_id", "operation", "reason", "changes"))
    require(type(proposal["schema_version"]) is int and proposal["schema_version"] in {1, 2} and proposal["operation"] == "publish", "unsupported_operation", "Expected explicit versioned ontology publication.")
    require(isinstance(proposal["operation_id"], str) and re.fullmatch(r"ONTOP-[A-Za-z0-9-]{4,100}", proposal["operation_id"]), "invalid_operation", "Use a stable ONTOP operation identity.")
    require(isinstance(proposal["reason"], str) and 0 < len(proposal["reason"].strip()) <= 2000, "missing_reason", "Exact review requires a bounded reason.")
    require(isinstance(proposal["changes"], list) and 1 <= len(proposal["changes"]) <= 50, "invalid_changes", "Select one to fifty exact canonical files.")
    cfg = read_json(safe_path(root, "ontology.yaml"))
    permitted = set(cfg["project_files"] + cfg["binding_files"] + cfg.get("competency_files", []))
    if proposal["schema_version"] == 2:
        from ontology_advanced import load_advanced
        advanced = load_advanced(root, required=True)
        permitted.update(ref["path"] for ref in advanced["extensions"])
        permitted.add("ontology-advanced.yaml")
        for ref in advanced["extensions"]:
            permitted.update(s["path"] for s in read_json(safe_path(root, ref["path"])).get("shapes", []))
    seen = set()
    for change in proposal["changes"]:
        exact(change, ("path", "expected_sha256", "content", "sha256"))
        require(isinstance(change["path"], str) and change["path"] in permitted and change["path"] not in seen, "canonical_scope", "Change must select one distinct configured project canonical file.", path=change["path"] if isinstance(change["path"], str) else None)
        seen.add(change["path"]); safe_path(root, change["path"], must_exist=False)
        require(isinstance(change["content"], str) and len(change["content"].encode()) <= 250000, "invalid_content", "Provide exact reviewed UTF-8 content up to 250000 bytes.")
        digest(change["sha256"])
        if change["expected_sha256"] is not None: digest(change["expected_sha256"])
        require(sha256(change["content"].encode()) == change["sha256"], "content_digest", "Proposed content differs from its reviewed digest.")
        if not change["path"].endswith(".ttl"):
            decode_json(change["content"].encode(), path=change["path"])
    if proposal["schema_version"] == 2:
        overrides = {c["path"]: c["content"].encode() for c in proposal["changes"]}
        updated = load_advanced(root, required=True, _overrides=overrides)
        old_other = {k:v for k,v in advanced.items() if k != "extensions"}
        new_other = {k:v for k,v in updated.items() if k != "extensions"}
        require(old_other == new_other and [r["path"] for r in advanced["extensions"]] == [r["path"] for r in updated["extensions"]],
                "advanced_config_scope", "Semantic publication may update existing extension locks only; profiles, authority, limits and new imports use selected setup.")
        for ref in advanced["extensions"]:
            if ref["path"] in overrides:
                before = read_json(safe_path(root, ref["path"]))
                after = decode_json(overrides[ref["path"]])
                require(before["id"] == after.get("id") and before["project_id"] == after.get("project_id"), "identity_recycled", "An extension retains its stable identity and project.")
                for key in ("axioms", "annotations", "negative_assertions"):
                    old_statements = {r["id"]: r for r in before[key]}
                    new_statements = {r["id"]: r for r in after.get(key, [])}
                    require(all(new_statements.get(rid) == record for rid,record in old_statements.items()),
                            "extension_history", "Published extension statement identities and their meaning are immutable; add distinct sourced statements through review.")
                require(before.get("shapes", []) == after.get("shapes", []) or
                        [s["path"] for s in before.get("shapes", [])] == [s["path"] for s in after.get("shapes", [])],
                        "advanced_config_scope", "New shape selection requires selected setup.")
    return proposal


def _candidate(root, proposal, *, old_overrides=None):
    prior_all = dict(old_overrides or {})
    config = read_json(safe_path(root, "ontology.yaml"))
    core_paths = set(config["project_files"] + config["binding_files"] + config.get("competency_files", []))
    prior = {p:b for p,b in prior_all.items() if p in core_paths}
    for change in proposal["changes"]:
        if change["expected_sha256"] is None and change["path"] in core_paths:
            empty = {"schema_version": 1, "questions": []} if change["path"] in config.get("competency_files", []) else {"@context": config["context"]["path"], "@graph": []}
            prior[change["path"]] = canonical_bytes(empty)
    old = load_project(root, validate=False, _overrides=prior)
    for change in proposal["changes"]:
        if change["expected_sha256"] is None: old.snapshot["inputs"][change["path"]] = None
    overrides = {c["path"]: c["content"].encode() for c in proposal["changes"]}
    new = load_project(root, _overrides={p:b for p,b in overrides.items() if p in core_paths})
    if proposal["schema_version"] == 2:
        from ontology_advanced import load_advanced, load_extensions
        for project, selected in ((old, prior_all), (new, overrides)):
            advanced = load_advanced(root, required=True, _overrides=selected)
            extensions, inputs, sources = load_extensions(project, advanced, _overrides=selected)
            require(all(s["status"] == "current" for s in sources), "source_not_current", "Extensions must cite current selected source bytes.")
            inputs["ontology-advanced.yaml"] = sha256(selected.get("ontology-advanced.yaml", read_bytes(safe_path(root, "ontology-advanced.yaml"))))
            project.snapshot["inputs"].update(inputs)
            project.snapshot["advanced"] = {"config": advanced, "extensions": extensions}
    require(all(s["status"] == "current" for s in new.sources), "source_not_current", "Proposed complete graph must cite current selected sources.")
    findings = validate_transition(old.records, new.records)
    require(not findings, findings[0]["code"] if findings else "invalid_transition", findings[0]["message"] if findings else "", record_id=findings[0]["record_id"] if findings else None)
    return old, new


def _advanced_checks(root, proposal):
    if proposal["schema_version"] != 2:
        return None
    from ontology_advanced import load_advanced
    from ontology_standards import validate, infer, health
    cfg = load_advanced(root, required=True)
    require(cfg["profiles"].get("standards", {}).get("enabled"), "standards_required", "Advanced publication requires selected standards validation.")
    overrides = {c["path"]: c["content"].encode() for c in proposal["changes"]}
    checked = validate(root, overrides=overrides)
    require(checked.get("complete") is True and checked.get("conforms") is True,
            "advanced_validation_failed", "The exact advanced candidate did not complete conformant standards validation: " + str(checked.get("status")))
    if cfg["profiles"].get("inference", {}).get("enabled"):
        inferred = infer(root, overrides=overrides)
        require(inferred.get("complete") is True and inferred.get("status") == "ok" and inferred.get("trusted") is True,
                "advanced_consistency_failed", "The exact advanced candidate did not establish consistent finite reasoning: " + str(inferred.get("status")))
    return {"standards": "conformant", "inference": "consistent" if cfg["profiles"].get("inference", {}).get("enabled") else "not_applicable",
            "context": checked.get("context"), "versions": checked.get("versions"), "readiness": health(root)}


def preview(root, proposal):
    root = _root(root)
    check_proposal(root, proposal)
    decision = _guard(root, "preview", {"proposal": proposal}, [c["path"] for c in proposal["changes"]])
    for change in proposal["changes"]:
        path = safe_path(root, change["path"], must_exist=False)
        require((sha256(path) if path.exists() else None) == change["expected_sha256"], "expected_changed", "Canonical bytes changed since the proposed review.", path=change["path"])
    old, new = _candidate(root, proposal)
    advanced_validation = _advanced_checks(root, proposal)
    value = {"schema_version": 1, "operation_id": proposal["operation_id"], "payload_sha256": sha256(canonical_bytes(proposal)), "reason": proposal["reason"], "changes": [{k: c[k] for k in ("path", "expected_sha256", "sha256")} for c in proposal["changes"]], "before": old.context(), "after": new.context(), "valid": True}
    if advanced_validation is not None:
        value["advanced_validation"] = advanced_validation
    _recheck(decision)
    value = decision.finish(value)
    value["preview_sha256"] = sha256(canonical_bytes(value))
    return value


def _intent_paths(operation_id):
    require(isinstance(operation_id, str) and re.fullmatch(r"ONTOP-[A-Za-z0-9-]{4,100}", operation_id), "invalid_operation", "Expected exact ONTOP operation identity.")
    return tuple(CONTROL + kind + "/" + operation_id + ".json" for kind in ("intents", "receipts", "recovery"))


def _read_intent(root, operation_id):
    path, _, _ = _intent_paths(operation_id)
    intent = read_json(safe_path(root, path))
    exact(intent, ("schema_version", "proposal", "preview", "prior_contents", "publisher", "intent_sha256"))
    checked = dict(intent); checked.pop("intent_sha256")
    require(sha256(canonical_bytes(checked)) == intent["intent_sha256"], "intent_changed", "Accepted intent integrity differs.")
    require(intent["proposal"]["operation_id"] == operation_id, "intent_changed", "Accepted intent operation identity differs.")
    check_proposal(root, intent["proposal"])
    require(intent["preview"]["payload_sha256"] == sha256(canonical_bytes(intent["proposal"])), "intent_changed", "Accepted intent payload differs from its reviewed preview.")
    reviewed = dict(intent["preview"]); reviewed.pop("preview_sha256", None)
    require(sha256(canonical_bytes(reviewed)) == intent["preview"].get("preview_sha256"), "intent_changed", "Accepted preview no longer matches the reviewed digest.")
    for change in intent["proposal"]["changes"]:
        content = intent["prior_contents"].get(change["path"])
        require((sha256(content.encode()) if isinstance(content, str) else None) == change["expected_sha256"], "intent_changed", "Accepted prior content differs from the reviewed expected version.")
    return intent


def _advance(root, intent, grant, *, fail_at=None, decision=None):
    proposal, pre = intent["proposal"], intent["preview"]
    journal_path, receipt_path, recovery_path = _intent_paths(proposal["operation_id"])
    old, new = _candidate(root, proposal, old_overrides={p: value.encode() for p, value in intent["prior_contents"].items() if value is not None})
    advanced_validation = _advanced_checks(root, proposal)
    require(advanced_validation == pre.get("advanced_validation"), "advanced_context_changed", "Advanced rules, shapes, helpers or certified runtime changed after accepted review.")
    if decision is not None:
        _recheck(decision)
    authorize(old, grant, proposal, pre["preview_sha256"])
    changed = {c["path"] for c in proposal["changes"]}
    for relative, expected in pre["before"]["inputs"].items():
        if relative in changed: continue
        file = safe_path(root, relative, must_exist=False)
        require((sha256(file) if file.exists() else None) == expected, "recovery_input_changed", "Accepted source/configuration/module input changed.", path=relative)
    require(old.context()["helpers"] == pre["before"]["helpers"], "helper_changed", "Helper version changed after accepted review.")
    states = []
    for c in proposal["changes"]:
        path = safe_path(root, c["path"], must_exist=False)
        actual = sha256(path) if path.exists() else None
        require(actual in {c["expected_sha256"], c["sha256"]}, "recovery_conflict", "Canonical file contains unrelated edits; preserve them.", path=c["path"])
        states.append({"path": c["path"], "before_sha256": c["expected_sha256"], "sha256": c["sha256"], "state": "committed" if actual == c["sha256"] else "pending"})
    existing_receipt = safe_path(root, receipt_path, must_exist=False)
    if existing_receipt.exists():
        receipt = read_json(existing_receipt)
        require(receipt.get("intent_sha256") == intent["intent_sha256"] and all(s["state"] == "committed" for s in states), "receipt_conflict", "Completed receipt no longer agrees with actual canonical files.")
        return receipt
    try:
        if fail_at == "before_commit": raise OSError("Injected pre-commit failure")
        for index, (change, state) in enumerate(zip(proposal["changes"], states)):
            if state["state"] != "committed":
                if decision is not None:
                    _recheck(decision, targets=False)
                atomic_write(root, change["path"], change["content"].encode(), change["expected_sha256"])
                state["state"] = "committed"
            if fail_at == "after_commit" or fail_at == f"after_commit:{index+1}": raise OSError("Injected post-commit failure")
        if fail_at == "projection": raise OSError("Injected projection failure")
        from ontology_build import compile_project
        projection = compile_project(root)
        receipt = {"schema_version": 1, "status": "complete", "operation_id": proposal["operation_id"], "payload_sha256": pre["payload_sha256"], "preview_sha256": pre["preview_sha256"], "intent_sha256": intent["intent_sha256"], "reason": proposal["reason"], "publisher": intent["publisher"], "files": states, "projection": projection, "context": load_project(root).context()}
        if fail_at == "receipt": raise OSError("Injected receipt failure")
        atomic_write(root, receipt_path, canonical_bytes(receipt), None)
        return receipt
    except (OSError, OntologyError) as exc:
        recovery = {"schema_version": 1, "status": "partial", "operation_id": proposal["operation_id"], "intent_sha256": intent["intent_sha256"], "files": states, "error": {"code": getattr(exc, "code", "write_failure"), "message": str(exc)[:1000]}, "recovery": "Renew the current grant for the original payload/preview and recover this exact operation."}
        path = safe_path(root, recovery_path, must_exist=False)
        atomic_write(root, recovery_path, canonical_bytes(recovery), sha256(path) if path.exists() else None)
        return recovery


def publish(root, proposal, grant, *, expected_preview_sha256, fail_at=None):
    root = _root(root)
    check_proposal(root, proposal)
    decision = _guard(root, "publish", {"proposal": proposal, "grant": grant, "expected_preview_sha256": expected_preview_sha256}, [c["path"] for c in proposal["changes"]])
    journal_path, _, _ = _intent_paths(proposal["operation_id"])
    journal_file = safe_path(root, journal_path, must_exist=False)
    if journal_file.exists():
        intent = _read_intent(root, proposal["operation_id"])
        require(intent["proposal"] == proposal and intent["preview"]["preview_sha256"] == expected_preview_sha256, "operation_reused", "Operation identity cannot be reused for a different accepted change.")
        with operation_lock(root, CONTROL + "publication.lock"):
            return decision.finish(_advance(root, intent, grant, fail_at=fail_at, decision=decision))
    pre = preview(root, proposal)
    require(pre["preview_sha256"] == expected_preview_sha256, "preview_changed", "Exact reviewed preview differs from current proposed state.")
    project, _ = _candidate(root, proposal)
    authorize(project, grant, proposal, expected_preview_sha256)
    with operation_lock(root, CONTROL + "publication.lock"):
        _recheck(decision)
        require(not journal_file.exists(), "operation_race", "Another writer accepted this operation; retry its exact recorded payload.")
        pre = preview(root, proposal)
        require(pre["preview_sha256"] == expected_preview_sha256, "preview_changed", "Inputs changed while acquiring publication lock.")
        authorize(project, grant, proposal, expected_preview_sha256)
        intent = {"schema_version": 1, "proposal": copy.deepcopy(proposal), "preview": pre, "prior_contents": {c["path"]: read_bytes(safe_path(root, c["path"])).decode() if c["expected_sha256"] is not None else None for c in proposal["changes"]}, "publisher": {"actor_id": grant["actor_id"], "actor_kind": grant["actor_kind"], "grant_id": grant["grant_id"], "grant_sha256": sha256(canonical_bytes(grant)), "task": grant["task"]}}
        intent["intent_sha256"] = sha256(canonical_bytes(intent))
        require(len(canonical_bytes(intent)) <= 2_000_000, "intent_too_large", "Accepted operation exceeds bounded durable intent size.")
        if fail_at == "before_intent": raise OntologyError("injected_failure", "Injected failure before accepted intent.")
        atomic_write(root, journal_path, canonical_bytes(intent), None)
        return decision.finish(_advance(root, intent, grant, fail_at=fail_at, decision=decision))


def recover(root, operation_id, grant, *, fail_at=None):
    root = _root(root)
    intent = _read_intent(root, operation_id)
    decision = _guard(root, "recover", {"intent": intent, "grant": grant, "operation_id": operation_id}, [c["path"] for c in intent["proposal"]["changes"]])
    with operation_lock(root, CONTROL + "publication.lock"):
        require(_read_intent(root, operation_id) == intent, "intent_changed", "Accepted intent changed while acquiring recovery lock.")
        return decision.finish(_advance(root, intent, grant, fail_at=fail_at, decision=decision))
