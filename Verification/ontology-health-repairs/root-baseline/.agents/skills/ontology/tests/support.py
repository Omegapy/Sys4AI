"""Isolated fixtures; no root or memory mutation, network or optional dependency."""
from pathlib import Path
import copy
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "scripts"))
from ontology_core import CORE, PROJECT, CONTEXT_PATH, canonical_bytes, sha256, read_json

SOURCE_TEXT = "# Specification\n\nFixture sources define local test artifacts and scoped ownership.\n"


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def core_id(local):
    return CORE + local


def project_id(local, identity="example"):
    return PROJECT + identity + ":" + local


def make_project(path, project_id="example"):
    path = Path(path).resolve()
    # Works in source, installed root and Template copies of the skill package.
    possible = [PACKAGE.parents[1] / "ONTOLOGY-depo/starter", PACKAGE.parents[2] / "reference-assets/ONTOLOGY-depo/starter", PACKAGE.parents[1] / "reference-assets/ONTOLOGY-depo/starter"]
    starter = next((p for p in possible if (p / "ontology.yaml").is_file()), None)
    if starter is None:
        for ancestor in PACKAGE.parents:
            for tail in ("ONTOLOGY-depo/starter", "reference-assets/ONTOLOGY-depo/starter"):
                candidate = ancestor / tail
                if (candidate / "ontology.yaml").is_file(): starter = candidate; break
            if starter is not None: break
    if starter is None: raise RuntimeError("Neutral ontology starter fixture is unavailable")
    shutil.copytree(starter, path, dirs_exist_ok=True)
    config = read_json(path / "ontology.yaml")
    config["project"] = {"id": project_id, "name": "Example project", "purpose": "Validate the local ontology capability.", "namespace": PROJECT + project_id + ":", "root": "."}
    config["source_allowlist"] = ["SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md"]
    write_json(path / "ontology.yaml", config)
    companion = path / "ontology-advanced.yaml"
    if companion.exists():
        advanced = read_json(companion)
        if advanced.get("project_id") is None:
            advanced["project_id"] = project_id
            write_json(companion, advanced)
    companion = path / "ontology-advanced.yaml"
    if companion.exists():
        advanced = read_json(companion)
        advanced["project_id"] = project_id
        write_json(companion, advanced)
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
