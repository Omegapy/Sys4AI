"""Trusted static setup assessment; unknown target Python is never executed.

The manifest pins the complete current starter inventory. Recovery and reruns
retain their recorded edition's source inventory instead of acquiring a new one.
"""
import ast
from datetime import datetime, timezone
from pathlib import Path

INVENTORY = "assets/static-capability-v1.json"
INVENTORY_SHA256 = "d7835f611ccbe5e6b91ceb3a06df09975347a57fb81c0e227c0a5ae4c51783c0"


def inventory(h):
    raw = h.file_bytes(Path(__file__).resolve().parent.parent / INVENTORY)
    if h.sha(raw) != INVENTORY_SHA256:
        raise h.InitializationError("unknown static capability inventory; preserve it for reviewed helper adoption")
    return h.unique_json(raw)


def validate_source(h, files, *, contract=None):
    selected = inventory(h)
    required = {name for package,names in selected["packages"].items() for name in names if package not in selected.get("curator_packages", []) or contract in h.CURATOR_CONTRACTS}
    missing = sorted(required - files.keys())
    if missing:
        raise h.InitializationError("complete starter capability inventory is missing: " + ", ".join(missing[:20]))
    for name in sorted(required):
        if name.endswith(".py"):
            try:
                ast.parse(files[name], filename=name)
            except (SyntaxError, UnicodeError) as error:
                raise h.InitializationError("starter capability Python syntax is invalid: " + name) from error
        elif name.endswith((".json", ".jsonld")):
            try:
                h.unique_json(files[name])
            except (ValueError, UnicodeError, h.InitializationError) as error:
                raise h.InitializationError("starter capability JSON is invalid: " + name) from error
    locks = dict(selected["locked_resources"])
    if contract in h.CURATOR_CONTRACTS: locks.update(selected.get("curator_locked_resources", {}))
    for name, expected in locks.items():
        if h.sha(files[name]) != expected:
            raise h.InitializationError("starter profile or dependency lock differs from the reviewed static inventory: " + name)


def _paths(h, module):
    if module == h.CURATOR_MODULE:
        return (*h.CURATOR.SPECIAL_FILES, *h.CURATOR.PACKAGES)
    if module == "memory":
        return ("memory.yaml", ".agents/skills/memory", h.MEMORY_CONTRACT_ROOT)
    if module == h.LEARNING_MODULE:
        return (*h.LEARNING_TREES, *_paths(h, "memory"))
    if module == h.ONTOLOGY_MODULE:
        return ("ontology.yaml", *h.ONTOLOGY_TREES)
    return (h.ADVANCED.CONFIG, h.ADVANCED.TOOL, *h.ADVANCED.PACKAGES, *_paths(h, h.ONTOLOGY_MODULE))


def _inside(name, paths):
    return any(name == root or name.startswith(root + "/") for root in paths)


def assess(h, destination, record, *, operation=None):
    """Required adopted/selected failures block; preserved gaps stay explicit."""
    contract = record["setup_contract"]
    selected = [operation["module_id"]] if operation else []
    if operation is None:
        selected = (["memory"] if contract in h.MEMORY_CONTRACTS else [])
        selected += ([h.LEARNING_MODULE] if contract in h.LEARNING_CONTRACTS else [])
        selected += ([h.ONTOLOGY_MODULE] if contract in h.ONTOLOGY_CONTRACTS else [])
        selected += ([h.ADVANCED_MODULE] if contract in h.ADVANCED_CONTRACTS else [])
        selected += ([h.CURATOR_MODULE] if contract in h.CURATOR_CONTRACTS else [])
        selected += [op["module_id"] for op in record.get("module_adoptions", [])]
    source_rows = operation["sources"] if operation else record["sources"]
    if operation is None:
        current_sources = {row["destination"]: row for row in source_rows}
        for adopted in record.get("module_adoptions", []):
            roots = h.module_packages(adopted)
            current_sources = {name: row for name, row in current_sources.items() if not _inside(name, roots)}
            current_sources.update({row["destination"]: row for row in adopted["sources"]})
        source_rows = [current_sources[name] for name in sorted(current_sources)]
    locked = inventory(h)["locked_resources"]
    components = []
    for module in dict.fromkeys(selected):
        module_locks = {**locked, **(inventory(h).get("curator_locked_resources", {}) if module == h.CURATOR_MODULE else {})}
        paths = _paths(h, module)
        sources = [row for row in source_rows if _inside(row["destination"], paths)]
        preserved = any(row["adoption"] in {"preserved-project-owned", "skipped-existing-package"} for row in sources)
        diagnostics, observed = [], {}
        for row in sources:
            name = row["destination"]
            target = h.destination_file(destination, name)
            if not target.is_file():
                diagnostics.append({"code": "capability_resource_missing", "path": name})
                continue
            raw = h.file_bytes(target)
            observed[name] = h.sha(raw)
            if name in module_locks and observed[name] != module_locks[name]:
                diagnostics.append({"code": "capability_lock_changed", "path": name})
            if name.endswith(".py"):
                try:
                    ast.parse(raw, filename=name)
                except (SyntaxError, UnicodeError):
                    diagnostics.append({"code": "capability_syntax_invalid", "path": name})
            elif name.endswith((".json", ".jsonld")):
                try:
                    h.unique_json(raw)
                except (ValueError, UnicodeError, h.InitializationError):
                    diagnostics.append({"code": "capability_json_invalid", "path": name})
        if module == "memory":
            detail = h.memory_capture_notice(destination)
            available = detail["status"] in {"on", "off"}
            try:
                config = h.unique_json(h.file_bytes(h.destination_file(destination, "memory.yaml")))
                expected = {"id": record["identity"]["project_id"], "name": record["identity"]["project_name"], "root": "."}
                available = available and config.get("project") == expected
                detail["identity_matches"] = config.get("project") == expected
            except (h.InitializationError, OSError, ValueError, KeyError, TypeError):
                available = False
        elif module == h.LEARNING_MODULE:
            detail = h.assess_learning(destination)
            available = detail["manual_review"] == "available"
            memory_selected = operation is None or operation.get("new_memory") or bool(operation.get("refresh_dependencies"))
            if memory_selected and detail["automatic_capture"]:
                available = available and detail["shared_automatic_checkpoint"] == "available" and detail["director_binding"] == "current"
            elif detail["shared_automatic_checkpoint"] == "unavailable":
                detail["excluded_dependency"] = "Preserved memory was not selected for compatible refresh; shared capture is unverified."
        elif module == h.CURATOR_MODULE:
            detail = h._curator("assess", destination)
            available = detail["structural_readiness"] == "available" and detail["compatible"]
        else:
            detail = h.assess_ontology(destination) if module == h.ONTOLOGY_MODULE else h._advanced("assess", destination)
            available = detail["structural_readiness"] == "available"
            if detail.get("publication_enabled", True):
                available = available and detail.get("director_binding") == "current"
        available = available and not diagnostics
        required = operation is not None or not preserved
        outcome = "passed" if available else "failed" if required else "preserved-unverified"
        if not available:
            diagnostics.extend(detail.get("diagnostics", []))
            if not diagnostics:
                diagnostics.append({"code": "static_capability_unverified", "message": detail.get("message", "The selected local capability or binding could not be verified.")})
        components.append({"component": module, "required": required, "outcome": outcome,
                           "installed": bool(observed), "assessment": detail,
                           "input_inventory_sha256": h.sha(h.encoded(observed)), "input_file_count": len(observed),
                           "diagnostics": diagnostics[:20], "diagnostics_omitted": max(0, len(diagnostics) - 20),
                           "next_operation": None if available else "Review explicit compatible capability adoption or local configuration/binding repair; preserve project-owned files."})
    ready = all(row["outcome"] == "passed" and not row["assessment"].get("excluded_dependency") for row in components)
    return {"health_schema_version": 2, "assessment": {"project_root": str(destination),
                "project_id": record["identity"]["project_id"], "level": "static", "scope": "selected-module" if operation else "setup-edition",
                "setup_contract": contract, "observed_at": datetime.now(timezone.utc).isoformat(),
                "inspector_sha256": h.sha(h.file_bytes(Path(__file__).resolve())),
                "source_inventory_sha256": h.sha(h.encoded(source_rows))},
            "aggregate": "ready" if ready else "degraded", "ready": ready, "static_ready": ready,
            "runtime": "not-exercised", "provisioned": False, "unknown_target_code_executed": False,
            "trusted_inspector_execution": "Only hash-pinned memory configuration, learning and role-index inspectors may execute; role inspection uses disposable files for rendering.",
            "committed_boundary": list((operation or record)["completed_stages"]), "components": components,
            "required_failures": [row["component"] for row in components if row["required"] and row["outcome"] != "passed"]}


def apply(h, destination, record, *, operation=None):
    report = assess(h, destination, record, operation=operation)
    target = operation if operation is not None else record
    target["static_health"] = report
    record.update(static_ready=report["static_ready"], aggregate=report["aggregate"], ready=report["ready"])
    target["checks"].extend({"check": "static-capability:" + row["component"], "outcome": row["outcome"]}
                            for row in report["components"])
    if report["required_failures"]:
        raise h.InitializationError("required static capability verification failed: " + ", ".join(report["required_failures"]))
    return report
