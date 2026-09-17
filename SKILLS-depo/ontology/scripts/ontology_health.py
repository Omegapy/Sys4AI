"""Scoped, read-only readiness. Observations confer no mutation authority."""
from datetime import datetime, timezone
from pathlib import Path

from ontology_core import OntologyError, load_project, require, sha256, safe_path

PROFILES = {"standards", "inference", "semantic", "guards", "workbench"}
PRODUCTS = {"compile", "build-wiki", "link-memory"}


def arguments(parser, *, advanced=False):
    parser.add_argument("--scope", choices=("canonical", "selected"), default="selected")
    parser.add_argument("--level", choices=("static", "operational"), default="static")
    parser.add_argument("--require", action="append", default=[], choices=sorted(PROFILES if advanced else PRODUCTS))
    if advanced:
        parser.add_argument("--workbench-url", help="Explicit http://127.0.0.1:PORT origin; never a bootstrap URL.")


def aggregate(result, root, scope, level, components, context=None):
    require(scope in {"canonical", "selected"} and level in {"static", "operational"},
            "invalid_assessment", "Select canonical/selected scope and static/operational level.")
    failures = [name for name, value in components.items() if value.get("required") and not value.get("ready")]
    status = result.get("status") if result.get("status") in {"absent", "invalid"} else "degraded" if failures else "ready"
    result.setdefault("project_id", (context or {}).get("project_id"))
    result.update(health_schema_version=2, status=status, aggregate=status, ready=status == "ready",
                  assessment={"project_root": str(Path(root).absolute()), "scope": scope, "level": level,
                              "observed_at": datetime.now(timezone.utc).isoformat(),
                              "input_versions": context or {}, "components": components,
                              "failed_required": failures}, mutated=False)
    return result


def guard_health(root):
    from ontology_guards import profile, _context, GuardError, fail
    from ontology_guard_setup import coverage_manifest
    from ontology_profiles import health
    try:
        selected = profile(root)
        if selected is None:
            return {"status": "disabled", "enabled": False, "observed_dispatch": "not_exercised"}
        contract, adapters, inputs = _context(Path(root), selected, {})
        current = coverage_manifest(root, contract)
        fail(adapters == current, "guard_coverage", "Current dispatch declarations differ from the complete bound adapter inventory.")
        backend = health(root)
        ready = backend["status"] == "ready"
        return {"status": "ready" if ready else "backend_unavailable", "enabled": True,
                "integrity": "current", "families": sorted(current["families"]),
                "adapters": current, "inputs": inputs, "backend": backend,
                "observed_dispatch": "not_exercised", "coverage": "declared owning helper dispatch only",
                "next_operation": None if ready else "profile-setup standards"}
    except (GuardError, OntologyError, OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        return {"status": "unavailable", "enabled": True, "observed_dispatch": "not_exercised",
                "diagnostics": [{"code": getattr(exc, "code", "invalid_guard"), "message": str(exc)[:1000],
                                 "details": getattr(exc, "details", {})}], "next_operation": "guard preview/repair"}


def advanced_health(root, *, scope="selected", level="static", required=(), workbench_url=None):
    from ontology_advanced import load_advanced
    from ontology_profiles import health
    from ontology_semantic import health as semantic_health
    from ontology_workbench import assess_service
    require(set(required) <= PROFILES, "invalid_assessment", "Unknown required advanced component.")
    try:
        cfg = load_advanced(root)
        project = load_project(root, validate=False)
        context = project.context()
        config_path = safe_path(root, "ontology-advanced.yaml", must_exist=False)
        context = {**context, "advanced_config_sha256": sha256(config_path) if config_path.exists() else None}
        profiles = {"standards": health(root), "inference": health(root, "inference"),
                    "semantic": semantic_health(root), "guards": guard_health(root)}
        enabled = bool(cfg and cfg["profiles"].get("workbench", {}).get("enabled"))
        profiles["workbench"] = assess_service(root, workbench_url) if workbench_url else {
            "status": "ready" if enabled else "disabled", "enabled": enabled,
            "service_state": "not_assessed", "running": None, "mode": "on_demand",
            "observed_operation": "not_exercised"}
        components = {}
        for name, detail in profiles.items():
            selected = bool(cfg and cfg["profiles"].get(name, {}).get("enabled"))
            needed = name in required or (scope == "selected" and selected) or (name == "workbench" and bool(workbench_url))
            components[name] = {"required": needed, "enabled": selected,
                                "ready": detail["status"] == "ready", "status": detail["status"],
                                "observed_operation": "not_exercised"}
        components["canonical"] = {"required": True, "ready": not any(d["severity"] == "error" for d in project.diagnostics)
                                    and all(s["status"] == "current" for s in project.sources)}
        if level == "operational":
            from ontology_standards import query, validate, infer_diagnostic
            from ontology_semantic import search
            for name, component in components.items():
                if not component["required"] or name == "canonical":
                    continue
                observed = None
                if component["ready"]:
                    if name == "standards":
                        observed = {"query": query(root, "ASK { ?s ?p ?o }"), "validation": validate(root)}
                        component["ready"] = all(x.get("complete") and x.get("status") not in {"violation", "processing_failure"} for x in observed.values())
                    elif name == "inference":
                        observed = infer_diagnostic(root)
                        component['probe_scope'] = 'full_selected_closure; counts_and_digests_only'
                        component['full_proof_delivery'] = 'not_exercised; default full infer may return output_limit'
                        component["ready"] = observed.get("complete") is True and observed.get("status") == "ok" and observed.get("trusted") is True
                    elif name == "semantic":
                        try:
                            observed = search(project, "recollections", limit=3)
                            component["ready"] = observed.get("semantic", {}).get("used") is True
                        except OntologyError as exc:
                            observed = {"status": exc.code, "complete": False, "diagnostics": [exc.as_dict()]}
                            component["ready"] = False
                    elif name == "guards":
                        from ontology_guards import profile, read_bound, GuardError
                        from ontology_guard_setup import _backend
                        import json
                        try:
                            contract = json.loads(read_bound(root, profile(root)["contract"]))
                            observed = _backend(root, read_bound(root, contract["shapes"]).decode())
                            component["ready"] = observed.get("complete") is True
                            component["dispatch"] = "not_exercised; read-only validator probe only"
                        except GuardError as exc:
                            component["ready"] = False
                            observed = {"status": exc.code, "diagnostics": [{"message": str(exc)[:1000]}]}
                    elif name == "workbench":
                        component["ready"] = bool(workbench_url) and profiles[name].get("running") is True
                        observed = profiles[name]
                component["observed_operation"] = observed or "not_exercised"
        result = {"operation": "advanced-health", "implemented": True, "profiles": profiles}
        if cfg is None:
            result["status"] = "absent"
        return aggregate(result, root, scope, level, components, context)
    except OntologyError as exc:
        return aggregate({"operation": "advanced-health", "status": "invalid", "error": exc.as_dict()},
                         root, scope, level, {"configuration": {"required": True, "ready": False}})


def maintenance_status(root):
    """Report the current dependency closure; this function performs no repair."""
    from ontology import health
    core = health(root)
    advanced = advanced_health(root)
    pending = []
    for result in (core, advanced):
        for name, component in result["assessment"]["components"].items():
            if component.get("required") and not component.get("ready"):
                pending.append({"component": name, "status": component.get("status", "invalid"),
                                "next_operation": component.get("next_operation") or {
                                    "semantic": "build-semantic-index", "standards": "profile-setup standards",
                                    "inference": "profile-setup standards", "guards": "guard preview/repair",
                                    "canonical": "inspect source/configuration diagnostics"}.get(name, "inspect selected component")})
    # No advanced companion is a valid first-release configuration.
    static_ready = core["ready"] and (advanced["ready"] or advanced["status"] == "absent")
    return {"static_ready": static_ready, "operational_readiness": "not_exercised",
            "maintenance_pending": pending, "required_operations": sorted({x["next_operation"] for x in pending}),
            "assessment": {"core": core["assessment"], "advanced": advanced["assessment"]},
            "mutated": False}
