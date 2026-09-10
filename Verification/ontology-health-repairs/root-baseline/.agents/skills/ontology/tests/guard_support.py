"""Disposable guard fixtures. Bootstrap/native records here are labeled fixtures.

They establish no installation or actor authority in the real depot. Actual
selected-backend calls remain unmocked in dispatch tests.
"""
from pathlib import Path
import importlib.util
import json
import os
import shutil
import sys

from support import make_project, bind_director, write_json
from ontology_guards import digest
from ontology_core import canonical_bytes

DEPOT = Path(__file__).resolve().parents[3]
SKILLS = ("ontology", "memory", "agent-task", "to-trd", "to-implementation-plan",
          "manage-subagent-roles", "init-new-project")


def preserve_imports(test):
    """Restore the caller's package identity after a selected installed fixture.

    Fixtures deliberately reload ontology modules to exercise their exact local
    engine. Leaving those modules cached makes later tests use deleted fixture
    files and a different OntologyError class than the one they imported.
    """
    def selected(name):
        return name.startswith(("ontology_", "memory_")) or name == "basic_memory_adapter"
    original = {name: module for name, module in sys.modules.items() if selected(name)}
    paths = list(sys.path)
    def restore():
        for name in list(sys.modules):
            if selected(name):
                del sys.modules[name]
        sys.modules.update(original)
        sys.path[:] = paths
    test.addCleanup(restore)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def install_adapters(root):
    installed_root = Path(os.environ["SYS4AI_GUARD_INSTALLED_ROOT"]).resolve() if os.environ.get("SYS4AI_GUARD_INSTALLED_ROOT") else None
    for skill in SKILLS:
        origin = installed_root / ".agents/skills" / skill if installed_root else DEPOT / "SKILLS-depo" / skill
        shutil.copytree(origin, root / ".agents/skills" / skill,
                        dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if installed_root and (root / "SKILLS-depo" / skill).exists():
            shutil.copytree(origin, root / "SKILLS-depo" / skill, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    target = root / "tools/template_update.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile((installed_root or DEPOT) / "tools/template_update.py", target)
    contracts = installed_root / "reference-assets/ONTOLOGY-depo" if installed_root else DEPOT / "ONTOLOGY-depo"
    shutil.copytree(contracts, root / "reference-assets/ONTOLOGY-depo", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("starter", "__pycache__", "*.pyc"))


def fixture_selection(root, *, contract=None):
    """Compose a conspicuously synthetic initial selection for guard tests only."""
    from ontology_guard_setup import coverage_manifest
    rel = "reference-assets/ONTOLOGY-depo/actions/contracts-v1.json"
    if contract is not None:
        write_json(root / rel, contract)
    definitions = json.loads((root / rel).read_text())
    adapters = coverage_manifest(root, definitions)
    base = "control_records/ontology/guard-bootstrap/fixture-"
    write_json(root / (base + "adapters.json"), adapters)
    bound = lambda name: {"path": name, "sha256": digest((root / name).read_bytes())}
    bootstrap = {"schema_version": 1, "status": "verified", "contract": bound(rel),
                 "adapters": bound(base + "adapters.json"),
                 "repair": bound("reference-assets/ONTOLOGY-depo/actions/repair-v1.json"),
                 "engine": bound(".agents/skills/ontology/scripts/ontology_guards.py"),
                 "setup": bound(".agents/skills/ontology/scripts/ontology_guard_setup.py"),
                 "fixture_only": "Synthetic bootstrap for testing; never a production coverage receipt."}
    write_json(root / (base + "bootstrap.json"), bootstrap)
    cfg_path = root / "ontology-advanced.yaml"
    config = json.loads(cfg_path.read_text()) if cfg_path.exists() else {
        "schema_version": 1, "profiles": {"standards": {"enabled": True}}, "extensions": [], "limits": {}}
    config["project_id"] = json.loads((root / "ontology.yaml").read_text())["project"]["id"]
    config["profiles"]["standards"] = {"enabled": True}
    config["profiles"]["guards"] = {"enabled": True, "contract": bound(rel),
                                  "adapters": bound(base + "adapters.json"), "bootstrap": bound(base + "bootstrap.json")}
    write_json(cfg_path, config)
    return adapters


def project(root, *, backend=True):
    registry = Path(root) / "depot/projects.json"
    identity = "sys4ai-depot" if registry.exists() else "example"
    root = make_project(root, project_id=identity)
    install_adapters(root)
    bind_director(root)
    if backend:
        origin = DEPOT / ".venv-ontology-standards"
        shutil.copytree(origin, root / origin.name, symlinks=True, copy_function=shutil.copy2,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # Exercise an isolated installed package so concurrent source work does
    # not change a fixture's immutable reviewed helper context mid-request.
    for name in list(sys.modules):
        if name.startswith("ontology_"):
            del sys.modules[name]
    sys.path.insert(0, str(root / ".agents/skills/ontology/scripts"))
    fixture_selection(root)
    return root


def canonical_snapshot(root, relative):
    path = root / relative
    if not path.exists():
        return {}
    files = path.rglob("*") if path.is_dir() else [path]
    return {file.relative_to(root).as_posix(): digest(file.read_bytes()) for file in files
            if file.is_file() and not any(part.startswith(".") for part in file.relative_to(root).parts)}
