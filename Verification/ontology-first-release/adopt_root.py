"""Adopt the exact reviewed first-release packages into the active depot root.

The Template updater must already have published the reviewed source candidate.
This operation does not publish project ontology definitions or change a Task.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "Verification/ontology-first-release"
TEMPLATE = ROOT / "Projects/Sys4AI-Template-Project"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def files(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*"))
            if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts and p.name != ".DS_Store"}


def candidate():
    desired, origins = {}, {}
    for package in ("ontology", "init-new-project"):
        source = ROOT / "SKILLS-depo" / package
        payload = files(source)
        if payload != files(TEMPLATE / ".agents/skills" / package):
            raise ValueError("Source and Template package differ: " + package)
        for relative, data in payload.items():
            target = ".agents/skills/" + package + "/" + relative
            desired[target], origins[target] = data, "SKILLS-depo/" + package + "/" + relative
    for directory in ("reference-assets/ONTOLOGY-depo", "ONTOLOGY"):
        for relative, data in files(TEMPLATE / directory).items():
            target = directory + "/" + relative
            if target == "ONTOLOGY/bindings/bindings.jsonld":
                continue
            desired[target], origins[target] = data, "Projects/Sys4AI-Template-Project/" + target
    empty = {"@context": "ONTOLOGY/contexts/context-v1.jsonld", "@graph": []}
    for name in ("skills", "roles", "artifacts", "projects"):
        target = "ONTOLOGY/bindings/" + name + ".json"
        desired[target], origins[target] = encoded(empty), "Reviewed empty project-local binding initialization"
    desired["ONTOLOGY/modules/project/competency.json"] = encoded({"schema_version": 1, "questions": []})
    origins["ONTOLOGY/modules/project/competency.json"] = "Reviewed empty project-local competency initialization"
    config = json.loads((TEMPLATE / "ontology.yaml").read_text())
    config["project"] = {"id": "sys4ai-depot", "name": "Sys4AI depot", "root": ".",
                         "purpose": "Manage reusable Sys4AI assets and factual local project inventory.",
                         "namespace": "urn:sys4ai:ontology:project:sys4ai-depot:"}
    config["binding_files"] = ["ONTOLOGY/bindings/" + name + ".json" for name in ("skills", "roles", "artifacts", "projects")]
    config["competency_files"] = ["ONTOLOGY/modules/project/competency.json"]
    config["source_allowlist"] = sorted({
        "SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md", "depot/projects.json", "depot/template-update.json",
        *[".agents/skills/" + skill + "/SKILL.md" for skill in ("memory", "to-trd", "to-implementation-plan", "task", "agent-task", "ontology")],
        ".agents/skills/memory/references/publication-examples.md",
        *["Roles/" + role + "/" + filename for role in ("project-sub-agent", "task-manager") for filename in ("AGENTS.md", "ROLE.md")],
        "ONTOLOGY/modules/sys4ai-core/1.0.0/core.jsonld",
    })
    config["publication"] = {"enabled": True, "binding": {"actor_id": "/root",
        "scope": ["ONTOLOGY/modules/project", "ONTOLOGY/bindings"],
        "authority": [{"path": p, "sha256": sha((ROOT / p).read_bytes())} for p in ("SOUL.md", "AGENTS.md", "ROLE.md")]}}
    desired["ontology.yaml"], origins["ontology.yaml"] = encoded(config), "Specialized neutral Template ontology.yaml under sys4ai-depot identity"
    for name in ("README.md", "SPECS.md", ".gitignore"):
        desired[name] = (HERE / "staging" / name).read_bytes()
        origins[name] = "Verification/ontology-first-release/staging/" + name
    return desired, origins


def prepare():
    desired, origins = candidate()
    entries = []
    for name, data in sorted(desired.items()):
        target = ROOT / name
        if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != ROOT.parent):
            raise ValueError("Symlink adoption path: " + name)
        before = sha(target.read_bytes()) if target.is_file() else None
        entries.append({"source": origins[name], "destination": name, "before_sha256": before,
                        "after_sha256": sha(data), "action": "unchanged" if before == sha(data) else "add" if before is None else "replace"})
    for directory in (".agents/skills/ontology", "reference-assets/ONTOLOGY-depo", "ONTOLOGY"):
        unknown = set(files(ROOT / directory)) - {p[len(directory) + 1:] for p in desired if p.startswith(directory + "/")}
        if unknown:
            raise ValueError("Existing project-owned files need review: " + directory + " " + repr(sorted(unknown)))
    manifest = {"schema_version": 1, "plan_id": "PLAN-20260909-731308FD", "status": "preview",
                "project_id": "sys4ai-depot", "project_root": str(ROOT),
                "overwrite_boundary": "Exact reviewed ontology and initializer packages, selected root docs/configuration and empty ontology bootstrap only. Root governance, memory, learning, roles, licenses, registry, history and independent projects are preserved.",
                "entries": entries}
    (HERE / "root-adoption-preview.json").write_bytes(encoded(manifest))
    return manifest


def apply():
    preview = json.loads((HERE / "root-adoption-preview.json").read_text())
    desired, origins = candidate()
    if set(desired) != {e["destination"] for e in preview["entries"]}:
        raise ValueError("Reviewed file set changed.")
    receipt_path = ROOT / "control_records/ontology/root-adoption.json"
    if receipt_path.exists():
        raise ValueError("Existing root adoption receipt requires its exact reviewed successor; do not overwrite it.")
    for entry in preview["entries"]:
        target = ROOT / entry["destination"]
        before = sha(target.read_bytes()) if target.is_file() else None
        if before != entry["before_sha256"] or sha(desired[entry["destination"]]) != entry["after_sha256"]:
            raise ValueError("Source or destination changed after review: " + entry["destination"])
    # The accepted intent retains previous content before any active installation
    # is replaced. Per-file atomic writes expose only complete files.
    recovery = HERE / "root-adoption-before"
    recovery.mkdir(exist_ok=True)
    for entry in preview["entries"]:
        if entry["before_sha256"] is not None and entry["action"] != "unchanged":
            old = ROOT / entry["destination"]
            saved = recovery / entry["before_sha256"]
            if not saved.exists():
                saved.write_bytes(old.read_bytes())
    intent_path = ROOT / "control_records/ontology/root-adoption-intent.json"
    intent_path.parent.mkdir(parents=True, exist_ok=True)
    intent_path.write_bytes(encoded({**preview, "status": "accepted", "preview_sha256": sha(encoded(preview))}))
    for entry in preview["entries"]:
        if entry["action"] == "unchanged":
            continue
        target = ROOT / entry["destination"]
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".ontology-adoption.tmp")
        with temporary.open("xb") as stream:
            stream.write(desired[entry["destination"]])
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    assert all(sha((ROOT / e["destination"]).read_bytes()) == e["after_sha256"] for e in preview["entries"])
    receipt = {**preview, "status": "applied", "applied_at": datetime.now(timezone.utc).isoformat(),
               "preview_sha256": sha(encoded(preview)), "recovery": "Every prior replaced file retained by digest under Verification/ontology-first-release/root-adoption-before; no interrupted writes observed.",
               "canonical_definitions": "Empty bootstrap only. Reviewed project seed publication is a separate ontology operation."}
    receipt_path.write_bytes(encoded(receipt))
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation", choices=["preview", "apply"])
    a = p.parse_args()
    value = prepare() if a.operation == "preview" else apply()
    print(json.dumps({"status": value["status"], "entries": len(value["entries"]),
                      "changes": sum(e["action"] != "unchanged" for e in value["entries"])}, indent=2))
