"""Isolated fixtures; no root or memory mutation, network or optional dependency."""
from pathlib import Path
import copy
import json
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "scripts"))
from ontology_core import CORE, PROJECT, CONTEXT_PATH, canonical_bytes, sha256, read_json

SOURCE_TEXT = "# Specification\n\nFixture sources define local test artifacts and scoped ownership.\n"


def fixture_context(package=PACKAGE):
    """Resolve only this package's owner; never search an ancestor project."""
    package = Path(package).resolve()
    skills = package.parent
    if package.name != "ontology" or not (package / "scripts/ontology_core.py").is_file():
        raise RuntimeError("Select an actual ontology skill package for fixture discovery.")
    if skills.name == "SKILLS-depo":
        root, layout = skills.parent, "source"
        contracts = root / "ONTOLOGY-depo"
    elif skills.name == "skills" and skills.parent.name == ".agents":
        root, layout = skills.parent.parent, "installed"
        contracts = root / "reference-assets/ONTOLOGY-depo"
    else:
        raise RuntimeError("Ontology fixtures require a source or installed skill layout.")
    required = ("contract.json", "contexts/context-v1.jsonld", "modules/sys4ai-core/1.0.0/manifest.json", "profiles/ontology-advanced-v1.json")
    missing = [name for name in required if not (contracts / name).is_file()]
    if missing:
        raise RuntimeError("Selected fixture owner lacks its own ontology contracts: " + ", ".join(missing))
    return {"root": root, "skills": skills, "contracts": contracts, "layout": layout}


def standards_environment(context=None):
    """Select an existing venv without resolving its Python executable symlink."""
    selected = os.environ.get("SYS4AI_STANDARDS_PYTHON")
    if selected:
        python = Path(selected).expanduser().absolute()
        if python.name != "python" or python.parent.name != "bin":
            raise RuntimeError("SYS4AI_STANDARDS_PYTHON must select an existing venv/bin/python.")
        environment = python.parent.parent.resolve()
    else:
        environment = (context or fixture_context())["root"] / ".venv-ontology-standards"
        if not environment.exists():
            return None
    required = ("bin/python", "pyvenv.cfg", "certification.json")
    missing = [name for name in required if not (environment / name).is_file()]
    if missing:
        raise RuntimeError("Selected standards environment is incomplete: " + ", ".join(missing))
    return environment


def standards_available():
    return standards_environment() is not None


def semantic_acceptance_root():
    selected = os.environ.get("SYS4AI_SEMANTIC_ACCEPTANCE_ROOT")
    if not selected:
        return None
    root = Path(selected).expanduser().resolve()
    required = (".venv-ontology-semantic/bin/python", ".venv-ontology-semantic/pyvenv.cfg",
                ".sys4ai/ontology/semantic/model.json")
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise RuntimeError("Selected semantic acceptance root is incomplete: " + ", ".join(missing))
    return root


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def core_id(local):
    return CORE + local


def project_id(local, identity="example"):
    return PROJECT + identity + ":" + local


def make_project(path, project_id="example"):
    path = Path(path).resolve()
    contracts = fixture_context()["contracts"]
    # Reconstruct neutral authored fixture data from this delivery's contracts.
    # Installed projects need neither a depot ancestor nor copied project history.
    context = "ONTOLOGY/contexts/context-v1.jsonld"
    module = "ONTOLOGY/modules/sys4ai-core/1.0.0"
    shutil.copytree(contracts / "modules/sys4ai-core/1.0.0", path / module, dirs_exist_ok=True)
    (path / context).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(contracts / "contexts/context-v1.jsonld", path / context)
    for relative in ("ONTOLOGY/modules/project/project.jsonld", "ONTOLOGY/bindings/bindings.jsonld"):
        write_json(path / relative, {"@context": context, "@graph": []})
    from ontology_modules import module_digest
    manifest = read_json(path / module / "manifest.json")
    config = {"schema_version": 1, "context": {"path": context, "sha256": sha256(path / context)},
              "modules": [{"id": "sys4ai-core", "version": "1.0.0", "path": module,
                           "sha256": module_digest(manifest["files"])}],
              "project_files": ["ONTOLOGY/modules/project/project.jsonld"],
              "binding_files": ["ONTOLOGY/bindings/bindings.jsonld"], "competency_files": [],
              "publication": {"enabled": False, "binding": None},
              "retrieval": {"default_hops": 2, "default_limit": 20, "max_context_bytes": 32000,
                            "max_hops": 8, "max_limit": 100}}
    config["project"] = {"id": project_id, "name": "Example project", "purpose": "Validate the local ontology capability.", "namespace": PROJECT + project_id + ":", "root": "."}
    config["source_allowlist"] = ["SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md"]
    write_json(path / "ontology.yaml", config)
    advanced = read_json(contracts / "profiles/ontology-advanced-v1.json")
    advanced["project_id"] = project_id
    write_json(path / "ontology-advanced.yaml", advanced)
    for name in ("SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md"):
        (path / name).write_text(SOURCE_TEXT)
    return path


def record(local, *, identity="example", kind="instance", type_name="Artifact", **overrides):
    value = {"@id": project_id(local, identity), "@type": [core_id(type_name)], "kind": kind, "label": local.replace("-", " "), "definition": "A selected fixture meaning for " + local + ".", "lifecycle": "approved", "module": "project", "sources": [{"path": "SPECS.md", "sha256": sha256(SOURCE_TEXT.encode()), "locator": "section:Specification"}], "fact_kind": "asserted"}
    value.update(overrides)
    return value


def add_records(root, records, *, binding=False):
    cfg = read_json(Path(root) / "ontology.yaml")
    path = Path(root) / cfg["binding_files" if binding else "project_files"][0]
    value = read_json(path)
    value["@graph"].extend(copy.deepcopy(records))
    write_json(path, value)


def bind_director(root, actor="/root"):
    cfg = read_json(Path(root) / "ontology.yaml")
    cfg["publication"] = {"enabled": True, "binding": {"actor_id": actor, "scope": ["ONTOLOGY/modules/project", "ONTOLOGY/bindings"], "authority": [{"path": name, "sha256": sha256(Path(root) / name)} for name in ("SOUL.md", "AGENTS.md", "ROLE.md")]}}
    write_json(Path(root) / "ontology.yaml", cfg)


def proposal(root, records, operation_id="ONTOP-fixture-0001", *, binding=False):
    cfg = read_json(Path(root) / "ontology.yaml")
    relative = cfg["binding_files" if binding else "project_files"][0]
    content = canonical_bytes({"@context": CONTEXT_PATH, "@graph": records}).decode()
    return {"schema_version": 1, "operation_id": operation_id, "operation": "publish", "reason": "Review this exact local fixture change.", "changes": [{"path": relative, "expected_sha256": sha256(Path(root) / relative), "content": content, "sha256": sha256(content.encode())}]}


def grant(root, payload, actor="/root"):
    from ontology_publication import preview
    pre = preview(root, payload)
    now = datetime.now(timezone.utc)
    return {"schema_version": 1, "grant_id": "ONTGRANT-fixture", "project_id": read_json(Path(root) / "ontology.yaml")["project"]["id"], "actor_id": actor, "actor_kind": "director", "operation": "publish", "payload_sha256": sha256(canonical_bytes(payload)), "preview_sha256": pre["preview_sha256"], "config_sha256": sha256(Path(root) / "ontology.yaml"), "scope": [c["path"] for c in payload["changes"]], "native_receipt": {"tool": "collaboration.list_agents", "result": {"agents": [{"agent_name": actor, "agent_status": "running"}]}}, "observed_at": now.isoformat(), "expires_at": (now + timedelta(minutes=4)).isoformat(), "task": None, "reviewed_records": [{k: c[k] for k in ("path", "sha256", "expected_sha256")} for c in payload["changes"]]}
