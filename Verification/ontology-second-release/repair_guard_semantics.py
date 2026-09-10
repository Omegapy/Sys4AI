"""Stage an exact enabled-guard repair and apply its separately observed grant.

Run only after the correction implementation and actual installed-adapter
matrix have passed. The existing installed repair owner executes the mutation;
this script never disables a profile or overwrites a bound helper directly.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import hashlib
import json
import shutil
import sys

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "Verification/ontology-second-release"
PACKAGES = ("ontology", "memory", "agent-task", "to-trd", "to-implementation-plan", "manage-subagent-roles", "init-new-project")


def raw_hash(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def selected_sources():
    # The source worker's explicit manifest is checked when selecting files.
    manifest = json.loads((OUT / "guard-semantics-correction-files-r3.json").read_text())
    rows = manifest["files"]
    if isinstance(rows, dict):
        rows = [{"path": p, "sha256": h} for p, h in rows.items()]
    for row in rows:
        assert raw_hash((BASE / row["path"]).read_bytes()) == row["sha256"], row["path"]
    return rows


def destination(source):
    if source.startswith("SKILLS-depo/ontology/"):
        return source.replace("SKILLS-depo/", ".agents/skills/", 1)
    if source.startswith("ONTOLOGY-depo/actions/"):
        return "reference-assets/" + source
    raise ValueError("Source outside the selected correction: " + source)


def stage_clone():
    clone = OUT / "fixtures/guard-correction-installation-r3-final"
    assert not clone.exists(), "Keep prior staged evidence; use its exact current directory"
    for package in PACKAGES:
        shutil.copytree(BASE / ".agents/skills" / package, clone / ".agents/skills" / package,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    shutil.copytree(BASE / "reference-assets/ONTOLOGY-depo", clone / "reference-assets/ONTOLOGY-depo")
    (clone / "tools").mkdir(parents=True)
    shutil.copyfile(BASE / "tools/template_update.py", clone / "tools/template_update.py")
    changed = []
    for row in selected_sources():
        source = row["path"]
        if not source.startswith(("SKILLS-depo/ontology/", "ONTOLOGY-depo/actions/")):
            continue
        relative = destination(source)
        target = clone / relative
        before = raw_hash(target.read_bytes()) if target.exists() else None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((BASE / source).read_bytes())
        changed.append({"source": source, "destination": relative, "expected_sha256": before, "sha256": row["sha256"]})
    save(OUT / "guard-correction-stage.json", {"schema_version": 1, "clone": str(clone), "changes": changed,
         "purpose": "Exact current root owner bytes plus verified source correction; disposable selected installation for actual matrix acceptance."})
    print(json.dumps({"clone": str(clone), "changes": len(changed)}))


def preview(root, name):
    sys.path.insert(0, str(root / ".agents/skills/ontology/scripts"))
    from ontology_guard_setup import preview_repair
    from ontology_core import canonical_bytes
    from ontology_guards import profile
    selected = profile(root)
    assert selected is not None, "Only exact enabled-profile repair is supported"
    before_config = json.loads((root / "ontology-advanced.yaml").read_text())
    bootstrap = json.loads((root / selected["bootstrap"]["path"]).read_text())
    changes = []
    def add(relative, data):
        path = root / relative
        before = raw_hash(path.read_bytes()) if path.is_file() else None
        after = raw_hash(data)
        if before != after:
            changes.append({"path": relative, "expected_sha256": before, "sha256": after, "content": data.decode()})
        return {"path": relative, "sha256": after}
    for row in selected_sources():
        source = row["path"]
        if not source.startswith(("SKILLS-depo/ontology/scripts/", "ONTOLOGY-depo/actions/")):
            continue
        add(destination(source), (BASE / source).read_bytes())
    contract_path = selected["contract"]["path"]
    contract_bytes = (BASE / "ONTOLOGY-depo/actions/contracts-v1.json").read_bytes()
    contract_binding = {"path": contract_path, "sha256": raw_hash(contract_bytes)}
    # The matrix was run against the proposed exact root installation. All
    # actual helper adapter hashes must be unchanged or explicitly selected.
    matrix_path = "control_records/ontology/guard-bootstrap/ONTGUARD-typed-" + name + "-verification.json"
    verification = add(matrix_path, (OUT / "root-guarded-dispatch-corrected.json").read_bytes())
    operation = "ONTGUARD-typed-" + name + "-20260910"
    future = dict(bootstrap, operation_id=operation, contract=contract_binding, verification=verification)
    repair_change = next((c for c in changes if c["path"] == bootstrap["repair"]["path"]), None)
    if repair_change:
        future["repair"] = {"path": repair_change["path"], "sha256": repair_change["sha256"]}
    for key, filename in (("engine", "ontology_guards.py"), ("setup", "ontology_guard_setup.py")):
        relative = ".agents/skills/ontology/scripts/" + filename
        candidate = next((c for c in changes if c["path"] == relative), None)
        future[key] = {"path": relative, "sha256": candidate["sha256"] if candidate else raw_hash((root / relative).read_bytes())}
    bootstrap_path = "control_records/ontology/guard-bootstrap/" + operation + "-bootstrap.json"
    future_binding = add(bootstrap_path, canonical_bytes(future))
    before_config["profiles"]["guards"] = dict(selected, contract=contract_binding, bootstrap=future_binding)
    add("ontology-advanced.yaml", canonical_bytes(before_config))
    result = preview_repair(root, operation_id=operation, changes=changes)
    save(OUT / (name + "-guard-correction-preview.json"), result)
    print(json.dumps({"name": name, "preview_sha256": result["preview_sha256"], "changes": len(changes),
                      "paths": [c["path"] for c in changes]}))


def apply(root, name, observation):
    sys.path.insert(0, str(root / ".agents/skills/ontology/scripts"))
    from ontology_guard_setup import apply as owner_apply
    review = json.loads((OUT / (name + "-guard-correction-preview.json")).read_text())
    observed = json.loads(observation.read_text())
    timestamp = datetime.fromisoformat(observed["observed_at"])
    assert (datetime.now(timezone.utc) - timestamp).total_seconds() < 240
    assert observed["native_receipt"]["tool"] == "collaboration.list_agents"
    assert any(a["agent_name"] == "/root" and a["agent_status"] == "running" for a in observed["native_receipt"]["result"]["agents"])
    config = json.loads((root / "ontology.yaml").read_text())
    changes = review["payload"]["changes"]
    grant = {"schema_version": 1, "operation": review["payload"]["operation"], "preview_sha256": review["preview_sha256"],
             "actor_id": "/root", "actor_kind": "director", "observed_at": timestamp.isoformat(),
             "expires_at": (timestamp + timedelta(seconds=300)).isoformat(), "native_receipt": observed["native_receipt"],
             "scope": [c["path"] for c in changes],
             "reviewed_records": [{k: c[k] for k in ("path", "expected_sha256", "sha256")} for c in changes],
             "task": None, "project_id": config["project"]["id"], "config_sha256": raw_hash((root / "ontology.yaml").read_bytes())}
    save(OUT / (name + "-guard-correction-grant.json"), grant)
    result = owner_apply(root, review, grant)
    save(OUT / (name + "-guard-correction-receipt.json"), result)
    assert result["status"] == "complete"
    assert all(raw_hash((root / c["path"]).read_bytes()) == c["sha256"] for c in changes)
    assert json.loads((root / "ontology-advanced.yaml").read_text())["profiles"]["guards"]["enabled"]
    print(json.dumps({"name": name, "status": result["status"], "reopened": len(changes), "guards_enabled": True}))


def adopt_documents():
    sys.path.insert(0, str(BASE / ".agents/skills/ontology/scripts"))
    from ontology_core import atomic_write
    stage = json.loads((OUT / "guard-correction-stage.json").read_text())
    documentation = json.loads((OUT / "guard-correction-documentation.json").read_text())
    changes = stage["changes"] + documentation["changes"]
    receipt = json.loads((OUT / "root-guard-correction-receipt.json").read_text())
    assert receipt["status"] == "complete"
    bound = {row["path"]: row["sha256"] for row in receipt["files"]}
    for row in changes:
        target = BASE / row["destination"]
        actual = raw_hash(target.read_bytes()) if target.is_file() else None
        expected = row["sha256"] if row["destination"] in bound else row["expected_sha256"]
        assert actual == expected, (row["destination"], actual, expected)
        assert raw_hash((BASE / row["source"]).read_bytes()) == row["sha256"]
    save(OUT / "guard-correction-adoption.json", {"schema_version": 1, "changes": changes,
         "reason": "Exact typed-guard repair plus its source tests and maintainer documentation.",
         "bound_code_owner": "root-guard-correction-receipt.json",
         "source_manifest": "guard-semantics-correction-files-r2.json"})
    for row in changes:
        if row["destination"] not in bound:
            atomic_write(BASE, row["destination"], (BASE / row["source"]).read_bytes(), row["expected_sha256"])
    reopened = {row["destination"]: raw_hash((BASE / row["destination"]).read_bytes()) for row in changes}
    assert all(reopened[row["destination"]] == row["sha256"] for row in changes)
    save(OUT / "guard-correction-adoption-receipt.json", {"schema_version": 1, "status": "adopted", "reopened": reopened,
         "manifest_sha256": raw_hash((OUT / "guard-correction-adoption.json").read_bytes())})
    # The already selected integration fixture receives the same non-runtime
    # tests/docs; bound engine changes were made only by its own repair owner.
    fixture = OUT / "fixtures/generation-native"
    for row in changes:
        target = fixture / row["destination"]
        if row["destination"].startswith((".agents/skills/ontology/tests/", ".agents/skills/ontology/references/")) or row["destination"] == ".agents/skills/ontology/README.md":
            before = raw_hash(target.read_bytes()) if target.is_file() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(fixture, row["destination"], (BASE / row["source"]).read_bytes(), before)
    print(json.dumps({"root_adoption": "reopened", "files": len(changes)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("stage-clone", "preview", "apply", "adopt-documents"))
    parser.add_argument("--root", type=Path, default=BASE)
    parser.add_argument("--name", default="root")
    parser.add_argument("--observation", type=Path)
    args = parser.parse_args()
    if args.mode == "stage-clone": stage_clone()
    elif args.mode == "preview": preview(args.root.resolve(), args.name)
    elif args.mode == "apply": apply(args.root.resolve(), args.name, args.observation)
    else: adopt_documents()
