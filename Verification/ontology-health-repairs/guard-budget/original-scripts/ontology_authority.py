"""Ontology-specific cooperative authority checks; no memory grant is imported."""
from datetime import datetime, timezone
import importlib.util
import sys
from ontology_core import (OntologyError, safe_path, read_json, sha256, canonical_bytes, require, exact, digest)


def within(path, prefix):
    return path == prefix or path.startswith(prefix.rstrip("/") + "/")


def read_task(root, path):
    require(path.startswith("Tasks/") and path.endswith("/task.json"), "invalid_task_path", "Expected an exact canonical Task record.")
    source = safe_path(root, path)
    helper_path = safe_path(root, ".agents/skills/agent-task/scripts/task_state.py")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("_ontology_current_task", helper_path)
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    spec.loader.exec_module(helper)
    try:
        state, errors, _ = helper.validate_task_folder(source.parent)
    except (helper.TaskError, OSError) as exc:
        raise OntologyError("invalid_task", "Installed read-only Task inspection failed.") from exc
    require(not errors and state == read_json(source), "invalid_task", "Canonical Task is not valid under its current installed helper.")
    return state, helper


def active_managers(root):
    tasks = safe_path(root, "Tasks", must_exist=False)
    if not tasks.exists(): return []
    result = []
    for folder in sorted(tasks.iterdir()):
        if folder.name.startswith("."): continue
        require(not folder.is_symlink(), "unsafe_task", "Task ownership folder may not be a symlink.")
        if not folder.is_dir(): continue
        relative = folder.relative_to(root).as_posix() + "/task.json"
        selected = safe_path(root, relative, must_exist=False)
        if not selected.exists(): continue
        task = read_json(selected)
        orch = task.get("orchestration", {}) or {}
        if orch.get("manager_id") and orch.get("stage") not in {"unassigned", "finished"}:
            assignment = orch.get("assignments", {}).get(orch["manager_id"], {})
            if assignment.get("state") != "revoked":
                verified, _ = read_task(root, relative)
                result.append((relative, verified, assignment))
    return result


def review_binding(current):
    return {"proposal_id": current["head"]["proposal_id"], "revision": current["head"]["revision"],
            "revision_sha256": current["revision"]["revision_sha256"],
            "validation_sha256": current["head"]["validation_sha256"],
            "review_sha256": current["head"]["review_sha256"]}


def validate_native_observation(grant, *, now=None):
    """Shared current native evidence gate, also usable by separately scoped setup."""
    require(grant.get("actor_kind") in {"director", "manager"} and isinstance(grant.get("actor_id"), str)
            and grant["actor_id"], "publisher_forbidden", "Only a current Director or confirmed manager may authorize this operation.")
    try:
        observed, expires = [datetime.fromisoformat(grant[k].replace("Z", "+00:00")) for k in ("observed_at", "expires_at")]
        current = now or datetime.now(timezone.utc)
        valid = observed.tzinfo is not None and expires.tzinfo is not None and observed <= current <= expires and 0 < (expires - observed).total_seconds() <= 300
    except (ValueError, TypeError, AttributeError, KeyError):
        valid = False
    require(valid, "grant_expired", "A current native observation and grant lasting at most five minutes are required.")
    native = grant["native_receipt"]
    exact(native, ("tool", "result"))
    require(native["tool"] == "collaboration.list_agents", "native_receipt", "Use actual current native list_agents evidence.")
    exact(native["result"], ("agents",))
    agents = native["result"]["agents"]
    require(isinstance(agents, list), "native_receipt", "Malformed native roster.")
    seen = set()
    for actor in agents:
        exact(actor, ("agent_name", "agent_status"))
        require(isinstance(actor["agent_name"], str) and actor["agent_name"] not in seen, "native_receipt", "Native identities must be distinct.")
        seen.add(actor["agent_name"])
    require(any(a["agent_name"] == grant["actor_id"] and a["agent_status"] == "running" for a in agents), "publisher_not_running", "Publisher is not observed running.")
    return grant


def validate_director_binding(project, actor):
    binding = project.config["publication"]["binding"]
    require(binding and binding["actor_id"] == actor, "director_unbound", "Current destination-local Director binding differs.")
    for ref in binding["authority"]:
        require(sha256(safe_path(project.root, ref["path"])) == ref["sha256"], "authority_changed", "Current governing source differs from the Director binding.", path=ref["path"])
    return binding


def validate_manager_binding(project, actor, binding, paths):
    """Validate exact active manager ownership without performing any state write."""
    exact(binding, ("path", "sha256", "task_id", "execution_id", "generation", "assignment_id"))
    require(sha256(safe_path(project.root, binding["path"])) == binding["sha256"], "task_changed", "Canonical Task changed after exact review.")
    state, helper = read_task(project.root, binding["path"])
    orch = state.get("orchestration", {})
    require(state["task_id"] == binding["task_id"] and orch.get("execution_id") == binding["execution_id"] and orch.get("generation") == binding["generation"] and orch.get("manager_id") == binding["assignment_id"] and orch.get("stage") == "active" and orch.get("writer") == actor, "manager_unconfirmed", "Task does not confirm this exact active manager generation.")
    assignment = orch.get("assignments", {}).get(binding["assignment_id"], {})
    require(assignment.get("function") == "manager" and assignment.get("state") == "active" and assignment.get("generation") == binding["generation"] and assignment.get("native_id") == actor and assignment.get("role_reads"), "manager_unconfirmed", "Manager lacks current activation, native identity and role-read evidence.")
    try:
        require(helper.orch.receipt(assignment["native_receipt"], launch=True) == actor, "manager_unconfirmed", "Manager native launch identity differs.")
        helper.orch.role(assignment["role"], project.root)
    except (helper.orch.OrchestrationError, KeyError) as exc:
        raise OntologyError("manager_role_invalid", "Current manager role or native launch provenance is invalid.") from exc
    require(all(any(within(path, prefix) for prefix in assignment.get("fit", {}).get("writes", [])) for path in paths), "manager_scope", "Assigned Task writes do not include every proposed ontology file.")
    for other_path, _, other in active_managers(project.root):
        if other_path == binding["path"]: continue
        writes = other.get("fit", {}).get("writes", [])
        require(not any(within(path, scope) or within(scope, path) for path in paths for scope in writes), "manager_owns_scope", "A different unreconciled manager owns overlapping ontology writes.")
    return assignment


def authorize(project, grant, proposal, preview_sha256, *, now=None):
    version = grant.get("schema_version") if isinstance(grant, dict) else None
    extra = ("advanced_config_sha256", "proposal_review") if version == 2 else ()
    exact(grant, ("schema_version", "grant_id", "project_id", "actor_id", "actor_kind", "operation", "payload_sha256", "preview_sha256", "config_sha256", "scope", "native_receipt", "observed_at", "expires_at", "task", "reviewed_records", *extra))
    require(type(version) is int and version in {1, 2} and isinstance(grant["grant_id"], str) and grant["grant_id"].startswith("ONTGRANT-"), "invalid_grant", "Expected a versioned ontology-specific grant.")
    require(proposal["schema_version"] == 1 or version == 2, "grant_version", "Advanced publication needs an explicit v2 grant.")
    advanced = None
    if version == 2:
        from ontology_advanced import load_advanced
        advanced = load_advanced(project.root)
        config_file = safe_path(project.root, "ontology-advanced.yaml", must_exist=False)
        # Recovery retains the originally accepted companion digest, checked in its pre/post transaction.
        accepted_hash = project.snapshot["inputs"].get("ontology-advanced.yaml", sha256(config_file) if config_file.exists() else None)
        require(grant["advanced_config_sha256"] == accepted_hash, "config_changed", "Advanced configuration changed after exact review.")
        binding = grant["proposal_review"]
        if binding is not None:
            exact(binding, ("proposal_id", "revision", "revision_sha256", "validation_sha256", "review_sha256"))
            from ontology_proposals import open_proposal
            current = open_proposal(project.root, binding["proposal_id"])
            require(review_binding(current) == binding and current["revision"]["candidate"] == proposal,
                    "grant_review", "Grant review names different candidate, evidence or review bytes.")
            require(current["head"]["state"] in {"reviewed", "partial", "published"}, "grant_review", "Current candidate has no accepted review.")
            require(current["review"] and current["review"]["validation_sha256"] == binding["validation_sha256"]
                    and current["review"]["revision_sha256"] == binding["revision_sha256"], "grant_review", "Current review does not bind this exact validation and candidate.")
        require(proposal["schema_version"] == 1 or advanced is not None,
                "advanced_absent", "Advanced publication requires its selected companion.")
    require(project.config["publication"]["enabled"], "publication_disabled", "Ontology publication is disabled in this project.")
    require(grant["project_id"] == project.project_id, "grant_project", "Grant names a different project.")
    require(isinstance(grant["actor_kind"], str) and grant["actor_kind"] in {"director", "manager"} and isinstance(grant["actor_id"], str) and grant["actor_id"], "publisher_forbidden", "Ordinary child actors cannot publish canonical ontology.")
    require(grant["operation"] == "publish" and proposal["operation"] == "publish" and grant["payload_sha256"] == sha256(canonical_bytes(proposal)) and grant["preview_sha256"] == preview_sha256, "grant_payload", "Grant must bind this exact ontology payload and reviewed preview.")
    require(grant["config_sha256"] == sha256(safe_path(project.root, "ontology.yaml")), "config_changed", "Ontology configuration changed after review.")
    validate_native_observation(grant, now=now)
    paths = {c["path"] for c in proposal["changes"]}
    require(isinstance(grant["scope"], list) and all(isinstance(p, str) for p in grant["scope"]) and len(grant["scope"]) == len(paths) and set(grant["scope"]) == paths, "grant_scope", "Grant scope must name the exact reviewed changed files.")
    reviewed = [{k: c[k] for k in ("path", "sha256", "expected_sha256")} for c in proposal["changes"]]
    require(grant["reviewed_records"] == reviewed, "grant_records", "Grant reviewed records differ from exact proposed bytes.")
    actor = grant["actor_id"]
    if grant["actor_kind"] == "director":
        binding = project.config["publication"]["binding"]
        require(binding and binding["actor_id"] == actor and grant["task"] is None, "director_unbound", "Publisher differs from destination-local Director binding.")
        for ref in binding["authority"]:
            require(sha256(safe_path(project.root, ref["path"])) == ref["sha256"], "authority_changed", "Current governing source differs from the Director binding.", path=ref["path"])
        core_paths = {p for p in paths if p != "ontology-advanced.yaml" and not p.startswith("ONTOLOGY/extensions/")}
        advanced_paths = paths - core_paths
        require(all(any(within(path, prefix) for prefix in binding["scope"]) for path in core_paths), "director_scope", "Publication exceeds the Director's bound core scope.")
        if advanced_paths:
            require(version == 2 and advanced and advanced.get("publication", {}).get("enabled"), "advanced_publication_disabled", "Advanced publication requires separately bound destination-local authority.")
            advanced_binding = advanced["publication"].get("binding")
            require(advanced_binding and advanced_binding["actor_id"] == actor, "director_unbound", "Advanced authority names a different current Director.")
            require(all(any(within(path, prefix) for prefix in advanced_binding["scope"]) for path in advanced_paths), "director_scope", "Advanced publication exceeds its separately bound scope.")
            for ref in advanced_binding["authority"]:
                require(sha256(safe_path(project.root, ref["path"])) == ref["sha256"], "authority_changed", "Advanced governing authority changed after binding.", path=ref["path"])
        for _, _, assignment in active_managers(project.root):
            writes = assignment.get("fit", {}).get("writes", [])
            require(not any(within(path, scope) or within(scope, path) for path in paths for scope in writes), "manager_owns_scope", "An unreconciled manager owns overlapping canonical writes.")
    else:
        validate_manager_binding(project, actor, grant["task"], paths)
    return grant
