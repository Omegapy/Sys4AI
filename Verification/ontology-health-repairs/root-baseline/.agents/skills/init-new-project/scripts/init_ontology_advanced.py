"""Initializer v9 capability inventory and scoped advanced adoption planning.

The owning initializer supplies transactions, authority hooks and its one receipt.
This module reads selected sources and returns exact plans; it opens no runtime.
"""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

MODULE = "ontology-advanced"
CONFIG = "ontology-advanced.yaml"
EDITION = "governance-starter-v9"
PROFILES = {"standards", "inference", "semantic", "guards", "workbench"}
GUARD_SKILLS = ("ontology", "memory", "agent-task", "to-trd", "to-implementation-plan", "manage-subagent-roles", "init-new-project")
PACKAGES = tuple(".agents/skills/" + name for name in GUARD_SKILLS) + ("reference-assets/ONTOLOGY-depo",)
TOOL = "tools/template_update.py"
REFERENCE_FILES = {"reference-assets/ONTOLOGY-depo/" + name for name in (
    "advanced-profile.md", "advanced-limits.md", "advanced-provenance.md", "proposal-workflow.md", "reasoning-profile.md",
    "schema/advanced-v1.json", "schema/advanced-extension-v1.json", "schema/proposal-v1.json",
    "profiles/ontology-advanced-v1.json", "rules/finite-profile-v1.json", "shapes/ontology-v1.ttl",
    "actions/contracts-v1.json", "actions/action-shapes-v1.ttl", "actions/repair-v1.json")}
HELPERS = {".agents/skills/ontology/scripts/" + name for name in (
    "ontology_advanced.py", "ontology_advanced_cli.py", "ontology_advanced_packet.py", "ontology_profiles.py",
    "ontology_limits.py", "ontology_worker.py", "ontology_backend.py", "ontology_rdf.py", "ontology_interchange.py",
    "ontology_provenance.py", "ontology_sparql.py", "ontology_shacl.py", "ontology_reasoning.py", "ontology_derivations.py",
    "ontology_semantic.py", "ontology_semantic_worker.py", "ontology_proposals.py", "ontology_generation.py",
    "ontology_proposal_validation.py", "ontology_workbench.py", "ontology_guards.py", "ontology_guard_setup.py")}
RESOURCES = HELPERS | {".agents/skills/ontology/" + name for name in (
    "profiles/standards-v1.json", "profiles/semantic-v1.json", "requirements-standards.txt", "requirements-semantic.txt",
    "references/proposal-generation.md", "workbench/index.html", "workbench/app.js", "workbench/editor.js",
    "workbench/review.js", "workbench/advanced.js", "workbench/styles.css")} | {
    ".agents/skills/init-new-project/scripts/init_ontology_advanced.py"}
STARTERS = {CONFIG, TOOL, *REFERENCE_FILES}
SPECIAL_FILES = {CONFIG, TOOL, "ontology.yaml"}
FROZEN = ("new_ontology", "new_advanced", "protected_inventory", "prerequisites")


def fail(h, condition, message):
    if not condition:
        raise h.InitializationError(message)


def source_files(h, depot):
    original = h.template_sources(depot)[0]
    return {name: raw for name, raw in original.items()
            if name in SPECIAL_FILES or name.startswith("ONTOLOGY/") or any(name.startswith(root + "/") for root in PACKAGES)}


def validate_static(h, files, *, neutral, identity=None):
    required = STARTERS | RESOURCES
    fail(h, required <= files.keys(), "advanced ontology capability resources are missing: " + ", ".join(sorted(required - files.keys())))
    cfg = h.unique_json(files[CONFIG])
    fail(h, isinstance(cfg, dict) and set(cfg) == {"schema_version", "project_id", "profiles", "extensions", "limits", "publication"}
         and type(cfg["schema_version"]) is int and cfg["schema_version"] == 1, "advanced ontology companion has unsupported fields or edition")
    fail(h, isinstance(cfg["profiles"], dict) and set(cfg["profiles"]) == PROFILES
         and all(isinstance(value, dict) and type(value.get("enabled")) is bool for value in cfg["profiles"].values()),
         "advanced ontology profiles must explicitly declare all five enabled states")
    if neutral:
        fail(h, cfg["project_id"] is None and cfg["extensions"] == [] and cfg["limits"] == {}
             and all(value == {"enabled": False} for value in cfg["profiles"].values())
             and cfg["publication"] == {"enabled": False, "binding": None},
             "Template advanced ontology must be neutral, empty and disabled without authority or runtime settings")
    else:
        fail(h, isinstance(cfg["project_id"], str) and (identity is None or cfg["project_id"] == identity["project_id"]),
             "advanced ontology identity differs from the selected destination")
        fail(h, isinstance(cfg["extensions"], list) and len(cfg["extensions"]) <= 100 and isinstance(cfg["limits"], dict),
             "advanced ontology extension selection or resource limits are incompatible")
        seen = set()
        for ref in cfg["extensions"]:
            fail(h, isinstance(ref, dict) and set(ref) == {"path", "sha256"} and isinstance(ref["path"], str)
                 and ref["path"].startswith("ONTOLOGY/extensions/") and ref["path"].endswith(".json")
                 and ref["path"] not in seen and isinstance(ref["sha256"], str) and h.SHA256.fullmatch(ref["sha256"]),
                 "advanced ontology extension lock is incompatible")
            fail(h, ref["path"] in files and h.sha(files[ref["path"]]) == ref["sha256"], "advanced ontology extension differs from its exact preserved lock")
            seen.add(ref["path"])
        publication = cfg["publication"]
        fail(h, isinstance(publication, dict) and set(publication) == {"enabled", "binding"} and type(publication["enabled"]) is bool,
             "advanced publication binding is incompatible")
        binding = publication["binding"]
        if binding is not None:
            fail(h, isinstance(binding, dict) and set(binding) == {"actor_id", "scope", "authority"}
                 and isinstance(binding["actor_id"], str) and binding["actor_id"]
                 and isinstance(binding["scope"], list) and set(binding["scope"]) == {CONFIG, "ONTOLOGY/extensions"} and len(binding["scope"]) == 2
                 and isinstance(binding["authority"], list) and len(binding["authority"]) == 3
                 and {r.get("path") for r in binding["authority"] if isinstance(r, dict)} == {"SOUL.md", "AGENTS.md", "ROLE.md"},
                 "advanced publication authority is not destination-local and explicitly scoped")
            for ref in binding["authority"]:
                fail(h, set(ref) == {"path", "sha256"} and isinstance(ref["sha256"], str) and h.SHA256.fullmatch(ref["sha256"]),
                     "advanced governing source reference is incompatible")
        fail(h, not publication["enabled"] or binding is not None, "enabled advanced publication lacks a local binding")
    for path in HELPERS | {TOOL, ".agents/skills/init-new-project/scripts/init_ontology_advanced.py"}:
        try:
            ast.parse(files[path], filename=path)
        except (SyntaxError, UnicodeError) as error:
            raise h.InitializationError("advanced helper syntax is incompatible: " + path) from error
    guarded = {".agents/skills/ontology/scripts/ontology_publication.py": {"preview", "publish", "recover"},
               ".agents/skills/memory/scripts/memory_capture.py": None,
               ".agents/skills/agent-task/scripts/task_state.py": None,
               ".agents/skills/to-trd/scripts/trd.py": None,
               ".agents/skills/to-implementation-plan/scripts/plan_state.py": None,
               ".agents/skills/manage-subagent-roles/scripts/role_catalog.py": None,
               ".agents/skills/init-new-project/scripts/init_new_project.py": {"run_initialization", "run_module_adoption"},
               TOOL: None}
    for path, required_operations in guarded.items():
        fail(h, path in files and b"ONTOLOGY_GUARDED_ACTIONS" in files[path], "advanced setup lacks a guarded helper family: " + path)
        if required_operations:
            tree = ast.parse(files[path], filename=path)
            definitions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
            fail(h, required_operations <= definitions, "advanced setup lacks required guarded entry points: " + path)
    return cfg


def specialize(h, raw, identity, files, *, destination=None, owned_governance=frozenset()):
    cfg = deepcopy(h.unique_json(raw))
    cfg["project_id"] = identity["project_id"]
    core = h.unique_json(files["ontology.yaml"])
    if destination is not None and h.destination_file(destination, "ontology.yaml").exists():
        core = h.unique_json(h.file_bytes(h.destination_file(destination, "ontology.yaml")))
    actor = (core.get("publication", {}).get("binding") or {}).get("actor_id", "/root")
    refs = []
    for name in ("SOUL.md", "AGENTS.md", "ROLE.md"):
        target = h.destination_file(destination, name) if destination is not None else None
        value = h.file_bytes(target) if target is not None and target.exists() and name not in owned_governance else files[name]
        refs.append({"path": name, "sha256": h.sha(value)})
    cfg["publication"] = {"enabled": True, "binding": {"actor_id": actor, "scope": [CONFIG, "ONTOLOGY/extensions"], "authority": refs}}
    return h.encoded(cfg)


def protected_inventory(h, destination, *, new_ontology=False, new_advanced=False):
    inventory = {}
    for root in (("ONTOLOGY",) if not new_ontology else ()) + ("MEMORY", "control_records/ontology"):
        inventory.update(h.package_inventory(destination, root))
    inventory.update(h.license_inventory(destination))
    for name in (h.IDENTITY, "SOUL.md", "AGENTS.md", "ROLE.md", "memory.yaml") + (("ontology.yaml",) if not new_ontology else ()) + ((CONFIG,) if not new_advanced else ()):
        path = h.destination_file(destination, name)
        if path.exists():
            inventory[name] = h.sha(h.file_bytes(path))
    return inventory


def check_protected(h, destination, operation):
    current = protected_inventory(h, destination, new_ontology=operation["new_ontology"], new_advanced=operation["new_advanced"])
    fail(h, current == operation["protected_inventory"], "authored ontology, imports, proposals, configuration, memory or licensing changed during the selected advanced adoption")


def packages(operation):
    return PACKAGES + (("ONTOLOGY",) if operation.get("new_ontology") else ())


def proposed_files(h, destination, identity, original, *, new_ontology, new_advanced):
    proposed = {name: raw for name, raw in original.items() if name == TOOL or any(name.startswith(root + "/") for root in PACKAGES)}
    if new_ontology:
        baseline = h.ontology_proposed_files(destination, identity, {name: raw for name, raw in original.items() if h.ontology_path(name)}, new_ontology=True)
        proposed.update({name: raw for name, raw in baseline.items() if name == "ontology.yaml" or name.startswith("ONTOLOGY/")})
    if new_advanced:
        governing = {name: h.file_bytes(h.destination_file(destination, name)) for name in ("SOUL.md", "AGENTS.md", "ROLE.md")}
        proposed[CONFIG] = specialize(h, original[CONFIG], identity, {**original, **proposed, **governing}, destination=destination)
    return proposed


def plan(h, depot, destination, record, previous_raw):
    original = source_files(h, depot)
    validate_static(h, original, neutral=True)
    canonical = h.destination_file(destination, "ontology.yaml")
    has_graph = bool(h.package_inventory(destination, "ONTOLOGY"))
    new_ontology = not canonical.exists() and not has_graph
    fail(h, new_ontology or canonical.exists() and has_graph, "partial baseline ontology must be repaired explicitly before advanced adoption")
    new_advanced = not h.destination_file(destination, CONFIG).exists()
    if not new_ontology:
        current = {name: h.file_bytes(h.destination_file(destination, name)) for name, digest in h.ontology_inventory(destination).items() if digest != "directory"}
        h.validate_ontology_static(destination, current, neutral=False)
    if not new_advanced:
        cfg = h.unique_json(h.file_bytes(h.destination_file(destination, CONFIG)))
        fail(h, cfg.get("project_id") == record["identity"]["project_id"] and cfg.get("schema_version") == 1, "preserve incompatible or unspecialized advanced configuration for selected repair")
        fail(h, not cfg.get("profiles", {}).get("guards", {}).get("enabled"), "enabled destination guards require exact reviewed adapter repair before a capability upgrade")
    proposed = proposed_files(h, destination, record["identity"], original, new_ontology=new_ontology, new_advanced=new_advanced)
    owned = h.module_owned_files(record)
    package_changes, files = {}, {}
    for root in PACKAGES + (("ONTOLOGY",) if new_ontology else ()):
        before = h.package_inventory(destination, root)
        after = h.inventory_from_files(root, {name: raw for name,raw in proposed.items() if name.startswith(root + "/")})
        prior_owned = {name: digest for name,digest in owned.items() if name.startswith(root + "/")}
        expected = h.inventory_from_files(root, prior_owned) if prior_owned else {}
        if not before:
            fail(h, not prior_owned, "receipt-owned advanced capability package is missing; preserve it for exact repair: " + root)
            decision = "adopted"
        elif before == after:
            decision = "preserved-package"
        elif prior_owned and before == expected:
            decision = "refreshed-owned-package"
        else:
            difference = sorted(name for name in before.keys() | expected.keys() if before.get(name) != expected.get(name))
            raise h.InitializationError("customized, incomplete or unowned capability package is preserved; exact adoption needs separate repair: " + root,
                                        report={"status": "blocked", "diagnostics": [{"code": "scoped_capability_adoption_required", "path": root, "different_resources": difference}]})
        fail(h, not any((before[name] == "directory") != (after[name] == "directory") for name in before.keys() & after.keys()), "advanced capability file/directory transition needs separate selected repair")
        package_changes[root] = {"decision": decision, "before": before, "after": after, "diagnostic": None}
        if decision != "preserved-package":
            for name in sorted(before.keys() | after.keys()):
                if before.get(name) != "directory" and after.get(name) != "directory":
                    files[name] = {"before": before.get(name), "after": after.get(name)}
    for name in (TOOL,) + (("ontology.yaml",) if new_ontology else ()) + ((CONFIG,) if new_advanced else ()):
        path = h.destination_file(destination, name)
        before = h.sha(h.file_bytes(path)) if path.exists() else None
        after = h.sha(proposed[name])
        fail(h, before is None or before == after or owned.get(name) == before,
             "customized or unowned standalone capability is preserved: " + name)
        if before != after:
            files[name] = {"before": before, "after": after}
    preserved = {}
    for name in (h.IDENTITY, "SOUL.md", "AGENTS.md", "ROLE.md", "memory.yaml", "ontology.yaml", CONFIG, TOOL):
        path = h.destination_file(destination, name)
        if name not in files and path.exists():
            preserved[name] = h.sha(h.file_bytes(path))
    selected = {name: raw for name, raw in original.items() if name == TOOL or name == CONFIG or name == "ontology.yaml" or
                name.startswith("ONTOLOGY/") and new_ontology or any(name.startswith(root + "/") for root in PACKAGES)}
    sources = []
    for name, raw in sorted(selected.items()):
        root = next((prefix for prefix in package_changes if name.startswith(prefix + "/")), None)
        final = files[name]["after"] if name in files else package_changes[root]["after"].get(name) if root else preserved.get(name)
        adoption = ("specialized" if name in {CONFIG, "ontology.yaml"} else "adopted") if name in files else "preserved-project-owned" if final else "skipped-existing-package"
        sources.append({"source": h.TEMPLATE + "/" + name, "destination": name, "source_sha256": h.sha(raw), "source_version": "sha256:" + h.sha(raw), "destination_sha256": final, "adoption": adoption})
    checksum = h.sha(previous_raw)
    operation = {"schema_version": 1, "module_id": MODULE, "module_version": "2.0.0", "operation_id": "module-adoption-" + uuid4().hex,
                 "project_root": str(destination), "identity": deepcopy(record["identity"]),
                 "base_receipt": {"path": "control_records/project-setup-history/" + checksum + ".json", "sha256": checksum},
                 "refresh_dependencies": [], "new_memory": False, "sources": sources, "packages": package_changes,
                 "files": files, "preserved_files": preserved, "new_ontology": new_ontology, "new_advanced": new_advanced,
                 "protected_inventory": protected_inventory(h, destination, new_ontology=new_ontology, new_advanced=new_advanced),
                 "prerequisites": [{"module_id": "ontology", "disposition": "install-neutral-baseline" if new_ontology else "preserve-existing-authored-baseline"}],
                 "status": "partial", "completed_stages": [], "active_stage": "assets", "checks": [], "created_at": datetime.now(timezone.utc).isoformat()}
    operation["manifest_sha256"] = h.sha(h.encoded({key: operation[key] for key in h.module_frozen(operation)}))
    return operation, proposed


def selected_source_files(h, depot, operation):
    original = source_files(h, depot)
    return {name: raw for name,raw in original.items() if name in SPECIAL_FILES
            or name.startswith("ONTOLOGY/") and operation["new_ontology"]
            or any(name.startswith(root + "/") for root in PACKAGES)}


def validate_operation(h, destination, operation):
    fail(h, isinstance(operation["protected_inventory"], dict), "advanced operation lacks exact authored-data preservation evidence")
    for name, digest in operation["protected_inventory"].items():
        fail(h, isinstance(name, str) and Path(name).as_posix() == name and not Path(name).is_absolute() and ".." not in Path(name).parts
             and isinstance(digest, str) and (digest == "directory" or h.SHA256.fullmatch(digest)), "advanced protected inventory has an invalid path or hash")
        h.safe(destination / name)
        fail(h, name not in operation["files"], "advanced capability upgrade attempts to rewrite a protected authored resource")
    fail(h, operation["prerequisites"] == [{"module_id": "ontology", "disposition": "install-neutral-baseline" if operation["new_ontology"] else "preserve-existing-authored-baseline"}],
         "advanced operation has unsupported prerequisite provenance")
    for name, selected in (("ontology.yaml", operation["new_ontology"]), (CONFIG, operation["new_advanced"])):
        change = operation["files"].get(name)
        fail(h, (change is not None and change["before"] is None and change["after"] is not None) if selected else change is None,
             "advanced operation cannot rebind an existing configuration or omit a selected missing prerequisite")
    if not operation["new_ontology"]:
        fail(h, not any(name.startswith("ONTOLOGY/") for name in operation["files"]), "advanced upgrade must preserve authored graphs and locked imports")


def assess(h, destination):
    result = {"module_id": MODULE, "module_version": "2.0.0", "implemented": True, "installed": False,
              "structural_readiness": "unavailable", "runtime": "not-exercised", "inspector_execution": "none",
              "profiles": {}, "authorized_publication": "requires-current-operation-grant", "diagnostics": [], "provisioned": False}
    try:
        files = {}
        roots = PACKAGES + ("ONTOLOGY",)
        for root in roots:
            files.update({name: h.file_bytes(h.destination_file(destination, name)) for name,digest in h.package_inventory(destination, root).items() if digest != "directory"})
        for name in (CONFIG, TOOL, "ontology.yaml", h.IDENTITY, "SOUL.md", "AGENTS.md", "ROLE.md"):
            path = h.destination_file(destination, name)
            if path.exists():
                files[name] = h.file_bytes(path)
        identity = h.unique_json(files[h.IDENTITY])
        cfg = validate_static(h, files, neutral=False, identity=identity)
        h.validate_ontology_static(destination, files, neutral=False)
        result.update(installed=True, structural_readiness="available", project_id=cfg["project_id"], config_sha256=h.sha(files[CONFIG]),
                      profiles={name: {"enabled": profile["enabled"], "installed_runtime": "not-inspected", "ready": "not-exercised"} for name,profile in cfg["profiles"].items()},
                      guarded="enabled-needs-current-coverage-check" if cfg["profiles"]["guards"]["enabled"] else "disabled")
        binding = cfg["publication"]["binding"]
        result["publication_enabled"] = cfg["publication"]["enabled"]
        result["director_binding"] = "current" if binding and all(h.sha(files[ref["path"]]) == ref["sha256"] for ref in binding["authority"]) else "unbound-or-stale"
    except (h.InitializationError, OSError, ValueError, KeyError, TypeError) as error:
        result["diagnostics"].append({"code": "advanced_capability_unavailable", "message": str(error)[:1200]})
    return result
