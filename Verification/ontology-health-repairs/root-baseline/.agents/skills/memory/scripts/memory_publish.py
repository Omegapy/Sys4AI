"""Scoped cooperative publication; native receipts are evidence, not OS authentication."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re

from memory_paths import MemoryError, require, safe_path, safe_read_bytes, relative_path, project_root
from memory_core import (decode_json_yaml, exact, digest, text, timestamp, strings, sha256,
                         json_bytes, load_config, parse_record, validate_record, render_record, reject_sensitive)
from memory_evidence import read_task, validate_publication_evidence


def within(path, prefix):
    return path == prefix or path.startswith(prefix.rstrip("/") + "/")


def _native_receipt(value, actor):
    exact(value, ("tool", "result"))
    require(value["tool"] == "collaboration.list_agents", "native_receipt", "Current native list_agents evidence is required.")
    exact(value["result"], ("agents",))
    require(isinstance(value["result"]["agents"], list), "native_receipt", "Native roster is malformed.")
    seen = set()
    for entry in value["result"]["agents"]:
        exact(entry, ("agent_name", "agent_status"))
        require(isinstance(entry["agent_name"], str) and entry["agent_name"] not in seen,
                "native_receipt", "Native roster identities must be distinct.")
        seen.add(entry["agent_name"])
        if entry["agent_name"] == actor:
            require(entry["agent_status"] == "running", "publisher_not_running", "Publisher is not observed running.")
    require(actor in seen, "publisher_unconfirmed", "Publisher is absent from the native receipt.")


def _task_bindings(root):
    """Read canonical ownership only; never discover Tasks through memory recall."""
    tasks = safe_path(root, "Tasks", must_exist=False, kind="dir")
    if not tasks.exists():
        return []
    bindings = []
    for folder in sorted(tasks.iterdir()):
        if folder.name.startswith("."):
            continue
        if folder.is_symlink():
            raise MemoryError("unsafe_task", "Task ownership contains an unsafe folder.")
        if not folder.is_dir():
            continue
        relative = (folder / "task.json").relative_to(root).as_posix()
        if not (folder / "task.json").exists():
            continue
        state = decode_json_yaml(safe_read_bytes(root, relative, max_bytes=2_000_000))
        orch = state.get("orchestration")
        if orch and orch.get("manager_id") and orch.get("stage") not in {"unassigned", "finished"}:
            # A paused or uncertain manager remains an owner until reconciled.
            assignment = orch.get("assignments", {}).get(orch["manager_id"], {})
            if assignment.get("state") != "revoked":
                bindings.append((relative, state, assignment))
    return bindings


def authorize(root, config, grant_file, operation, payload_sha256, actor, *, paths, now=None):
    root = project_root(root)
    require(config == load_config(root), "config_changed", "Supplied configuration is not the current project configuration.")
    grant = decode_json_yaml(safe_read_bytes(root, str(grant_file), max_bytes=250000))
    exact(grant, ("schema_version", "grant_id", "project_id", "actor_id", "actor_kind", "operation", "payload_sha256", "config_sha256", "scope", "native_receipt", "observed_at", "expires_at", "task", "reviewed_records", "privacy_redaction"))
    require(grant["schema_version"] == 1 and grant["project_id"] == config["project"]["id"], "grant_project", "Grant schema or project identity is incompatible.")
    text(grant["grant_id"]); text(actor)
    require(grant["actor_id"] == actor and grant["actor_kind"] in {"director", "manager"}, "publisher_forbidden", "Grant must name the actual Director or confirmed manager.")
    digest(payload_sha256); digest(grant["payload_sha256"]); digest(grant["config_sha256"])
    require(grant["operation"] == operation and grant["payload_sha256"] == payload_sha256,
            "grant_payload", "Grant is not bound to this exact operation and reviewed payload.")
    require(grant["config_sha256"] == sha256(safe_read_bytes(root, "memory.yaml")), "config_changed", "Configuration changed after grant review.")
    observed, expires = timestamp(grant["observed_at"]), timestamp(grant["expires_at"])
    now = now or datetime.now(timezone.utc)
    require(observed <= now <= expires and 0 < (expires - observed).total_seconds() <= 300,
            "grant_expired", "Publication requires a current native receipt and unexpired bounded grant.")
    _native_receipt(grant["native_receipt"], actor)
    strings(grant["scope"], nonempty=True)
    require(type(grant["privacy_redaction"]) is bool, "invalid_grant", "Privacy-redaction authority must be explicit.")
    for scoped in grant["scope"]:
        relative_path(scoped)
    for path in paths:
        safe_path(root, path, must_exist=False, kind="any")
        require(any(within(path, prefix) for prefix in grant["scope"]), "grant_scope", "Operation path is outside granted scope.")
    require(isinstance(grant["reviewed_records"], list), "invalid_grant", "Expected explicit reviewed record versions.")
    for ref in grant["reviewed_records"]:
        exact(ref, ("path", "sha256", "expected_sha256")); relative_path(ref["path"])
        digest(ref["sha256"]); digest(ref["expected_sha256"], nullable=True)
    if grant["actor_kind"] == "director":
        binding = config["publication"]["director"]
        require(binding is not None and binding["actor_id"] == actor and grant["task"] is None,
                "director_unbound", "Director lacks a current project binding.")
        for ref in binding["authority"]:
            require(sha256(safe_read_bytes(root, ref["path"])) == ref["sha256"], "authority_changed", "Current governing instructions changed after publisher binding.")
        require(all(any(within(p, prefix) for prefix in binding["scope"]) for p in grant["scope"]),
                "director_scope", "Grant exceeds the configured Director scope.")
        for _, state, assignment in _task_bindings(root):
            writes = assignment.get("fit", {}).get("writes", [])
            require(not any(within(p, scope) or within(scope, p) for p in paths for scope in writes),
                    "manager_owns_scope", "An unreconciled Task manager owns an overlapping assignment.")
    else:
        binding = grant["task"]
        exact(binding, ("path", "sha256", "task_id", "execution_id", "generation", "assignment_id"))
        digest(binding["sha256"])
        require(sha256(safe_read_bytes(root, binding["path"], max_bytes=2_000_000)) == binding["sha256"], "task_changed", "Canonical Task changed after review.")
        state, helper = read_task(root, binding["path"])
        orch = state.get("orchestration", {})
        require(state["task_id"] == binding["task_id"] and orch.get("execution_id") == binding["execution_id"] and
                orch.get("generation") == binding["generation"] and orch.get("manager_id") == binding["assignment_id"] and
                orch.get("stage") == "active" and orch.get("writer") == actor,
                "manager_unconfirmed", "Task does not confirm this actor's current manager ownership.")
        assignment = orch.get("assignments", {}).get(binding["assignment_id"], {})
        require(assignment.get("function") == "manager" and assignment.get("state") == "active" and
                assignment.get("generation") == binding["generation"] and assignment.get("native_id") == actor and
                assignment.get("role_reads"), "manager_unconfirmed", "Manager lacks current activation, generation, or role-read evidence.")
        try:
            require(helper.orch.receipt(assignment["native_receipt"], launch=True) == actor, "manager_unconfirmed", "Launch identity differs.")
            helper.orch.role(assignment["role"], root)
        except helper.orch.OrchestrationError as exc:
            raise MemoryError("manager_role_invalid", "Current role or launch provenance failed the installed helper.") from exc
        writes = assignment["fit"]["writes"]
        require(all(any(within(p, prefix) for prefix in writes) for p in paths), "manager_scope", "Manager activation does not grant this memory write scope.")
    grant["_path"] = str(grant_file)
    grant["_sha256"] = sha256(safe_read_bytes(root, str(grant_file), max_bytes=250000))
    return grant


def transaction_payload(operation_id, operation, changes, reason):
    """Each change contains exact reviewed content; no silent publication rewrite."""
    return {"operation_id": operation_id, "operation": operation, "reason": reason, "changes": changes}


def validate_payload_structure(payload):
    """Validate a request before any semantic or operational authorization check."""
    exact(payload, ("operation_id", "operation", "reason", "changes"))
    require(isinstance(payload["operation_id"], str) and re.fullmatch(r"MEMOP-[A-Za-z0-9-]{4,100}", payload["operation_id"]), "invalid_operation", "Use a stable MEMOP operation identity.")
    require(payload["operation"] in {"publish", "supersede", "retract", "redact"}, "unsupported_operation", "Unsupported canonical operation; schema migrations are not automatic.")
    text(payload["reason"])
    reject_sensitive(payload["reason"])
    require(isinstance(payload["changes"], list) and 1 <= len(payload["changes"]) <= 50, "invalid_changes", "Expected bounded canonical changes.")
    seen = set()
    for change in payload["changes"]:
        exact(change, ("path", "content", "reviewed_record_sha256", "expected_sha256"))
        require(isinstance(change["path"], str) and change["path"] not in seen, "ambiguous_target", "Each memory target must be a unique path.")
        relative_path(change["path"])
        seen.add(change["path"])
        require(isinstance(change["content"], str), "invalid_record", "Memory replacement content must be text.")
        require(isinstance(change["reviewed_record_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", change["reviewed_record_sha256"]), "invalid_digest", "Reviewed record requires SHA256.")
        require(change["expected_sha256"] is None or isinstance(change["expected_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", change["expected_sha256"]), "invalid_digest", "Expected record requires SHA256 or explicit absence.")
        parse_record(change["content"])
    return payload


def validate_payload(root, config, payload, grant, *, recovering=False):
    validate_payload_structure(payload)
    paths, records, previous = set(), {}, {}
    existing_ids = {}
    memory_root = safe_path(root, "MEMORY", must_exist=False, kind="dir")
    if memory_root.exists():
        import os
        for directory, dirs, files in os.walk(memory_root, followlinks=False):
            for dirname in dirs:
                safe_path(root, (Path(directory) / dirname).relative_to(root).as_posix(), kind="dir")
            for name in files:
                rel = (Path(directory) / name).relative_to(root).as_posix()
                if rel == "MEMORY/README.md":
                    continue
                require(name.endswith(".md"), "unclassified_memory", "Unclassified canonical content prevents publication.")
                existing = parse_record(safe_read_bytes(root, rel, max_bytes=250000))["metadata"]
                text(existing.get("id"))
                require(existing.get("id") not in existing_ids, "duplicate_identity", "Existing canonical memory has duplicate stable identity.")
                existing_ids[existing.get("id")] = rel
    for change in payload["changes"]:
        exact(change, ("path", "expected_sha256", "content", "reviewed_record_sha256"))
        path = change["path"]
        digest(change["expected_sha256"], nullable=True); digest(change["reviewed_record_sha256"])
        require(isinstance(change["content"], str) and sha256(change["content"]) == change["reviewed_record_sha256"], "reviewed_content_changed", "Record bytes differ from reviewed content.")
        record = validate_record(parse_record(change["content"]), config["project"]["id"])
        meta = record["metadata"]
        require(path.startswith("MEMORY/") and Path(path).name == meta["id"] + ".md" and path not in paths,
                "record_path", "Publication path or duplicate identity is invalid.")
        require(meta["id"] not in records and (meta["id"] not in existing_ids or existing_ids[meta["id"]] == path), "duplicate_identity", "Stable record identity already belongs to another canonical path.")
        paths.add(path); records[meta["id"]] = record
        pub = meta["publication"]
        require(pub is not None and pub["operation_id"] == payload["operation_id"] and
                (recovering or (pub["actor_id"] == grant["actor_id"] and pub["actor_kind"] == grant["actor_kind"])),
                "publication_attribution", "Record publication must attribute the exact reviewed operation and publisher.")
        require({"path": path, "sha256": change["reviewed_record_sha256"], "expected_sha256": change["expected_sha256"]} in grant["reviewed_records"],
                "record_unreviewed", "Grant omits the exact reviewed record and expected version.")
        target = safe_path(root, path, must_exist=False)
        if target.exists():
            old_raw = safe_read_bytes(root, path, max_bytes=250000)
            old_hash = sha256(old_raw)
            require(old_hash == change["expected_sha256"] or (recovering and old_hash == change["reviewed_record_sha256"]),
                    "record_conflict", "Canonical record changed since review.", {"path": path})
            previous[meta["id"]] = parse_record(old_raw)
            old_meta = previous[meta["id"]]["metadata"]
            require(old_meta["id"] == meta["id"] and old_meta["project_id"] == meta["project_id"] and old_meta["created"] == meta["created"],
                    "identity_changed", "Correction cannot replace record identity, owner, or creation chronology.")
            require(timestamp(meta["modified"]) >= timestamp(old_meta["modified"]), "invalid_chronology", "Correction cannot reverse chronology.")
        else:
            require(change["expected_sha256"] is None, "record_conflict", "Expected prior record is absent.")
        if meta["state"] == "active":
            validate_publication_evidence(root, record, config)
    operation = payload["operation"]
    if operation == "publish":
        require(len(records) == 1 and all(r["metadata"]["state"] == "active" for r in records.values()), "invalid_transition", "Publish activates one reviewed record.")
        require(recovering or all(r["metadata"]["state"] == "draft" for r in previous.values()), "invalid_transition", "Correct an active record through supersession or explicit redaction.")
        require(all(not r["metadata"]["lifecycle"]["supersedes"] for r in records.values()), "invalid_transition", "Linked successors require a complete supersession transaction.")
    elif operation == "supersede":
        new = [r for r in records.values() if r["metadata"]["state"] == "active"]
        old = [r for r in records.values() if r["metadata"]["state"] == "superseded"]
        require(len(new) == 1 and old and len(new) + len(old) == len(records), "invalid_transition", "Supersession needs one active successor and its historical predecessors.")
        successor = new[0]["metadata"]
        require(set(successor["lifecycle"]["supersedes"]) == {r["metadata"]["id"] for r in old}, "invalid_transition", "Successor must name every predecessor.")
        for old_record in old:
            meta = old_record["metadata"]
            require(meta["id"] in previous and meta["lifecycle"]["superseded_by"] == successor["id"] and meta["lifecycle"]["reason"] == payload["reason"], "invalid_transition", "Every predecessor must retain its successor and correction reason.")
            require(recovering or previous[meta["id"]]["metadata"]["state"] == "active", "invalid_transition", "Only active predecessors can be superseded.")
            require(old_record["body"] == previous[meta["id"]]["body"], "history_changed", "Supersession retains the predecessor body.")
            protected = set(meta) - {"state", "modified", "lifecycle", "publication"}
            require(all(meta[key] == previous[meta["id"]]["metadata"][key] for key in protected), "history_changed", "Supersession retains predecessor claims and provenance.")
    elif operation == "retract":
        require(len(records) == 1 and len(previous) == 1, "invalid_transition", "Retraction requires one existing record.")
        record = next(iter(records.values())); meta = record["metadata"]
        require(meta["state"] == "retracted" and meta["lifecycle"]["reason"] == payload["reason"] and record["body"] == previous[meta["id"]]["body"], "invalid_transition", "Retraction retains original content and its explicit reason.")
        require(recovering or previous[meta["id"]]["metadata"]["state"] == "active", "invalid_transition", "Only active records can be retracted.")
        protected = set(meta) - {"state", "modified", "lifecycle", "publication"}
        require(all(meta[key] == previous[meta["id"]]["metadata"][key] for key in protected), "history_changed", "Retraction retains the original claim and provenance.")
    else:
        require(grant["privacy_redaction"] and len(records) == len(previous), "redaction_authority", "Redaction requires explicit scoped privacy authority for existing records.")
        require(all(r["metadata"]["lifecycle"]["reason"] == payload["reason"] for r in records.values()), "redaction_reason", "Every redacted record must retain the correction reason.")
    return records


def publish(root, payload, grant_file, actor, *, fault=None):
    from memory_recovery import transact
    return transact(root, payload, grant_file, actor, fault=fault)


supersede = publish
retract = publish
redact = publish


def propose(root, record, *, output=None, grant_file=None, actor=None):
    config = load_config(root)
    validate_record(record, config["project"]["id"])
    require(record["metadata"]["state"] == "draft", "proposal_state", "Proposals must remain draft.")
    content = render_record(record)
    if output is None:
        return {"operation": "propose", "state": "draft", "content": content, "sha256": sha256(content), "written": False}
    require(grant_file is not None and actor is not None and not str(output).startswith(("MEMORY/", ".sys4ai/")), "proposal_scope", "Saving a proposal requires a bounded evidence-output grant.")
    payload = {"output": str(output), "sha256": sha256(content)}
    authorize(root, config, grant_file, "propose", sha256(json_bytes(payload)), actor, paths=[str(output)])
    from memory_recovery import project_lock, atomic_replace
    with project_lock(root):
        authorize(root, config, grant_file, "propose", sha256(json_bytes(payload)), actor, paths=[str(output)])
        atomic_replace(root, str(output), content.encode(), None)
    return {"operation": "propose", "state": "draft", "path": str(output), "sha256": sha256(content), "written": True}


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
    return MemoryError(code, message, details)

ONTOLOGY_GUARDED_ACTIONS = ['propose']
propose = _ontology_guard_adapter(propose, 'memory', 'root', ['MEMORY'])
