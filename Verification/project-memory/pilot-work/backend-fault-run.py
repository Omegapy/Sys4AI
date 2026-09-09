"""Fault observations on the actual installed backend; synthetic fixture data."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import uuid

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot", BASE / "backend-fixture-run.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
from basic_memory_adapter import query, health, run_worker, _read_certificate
from basic_memory_projection import canonical_json, digest
from memory_core import load_config, parse_record, render_record
from memory_maintenance import reindex_payload, reindex, pending_reindexes, recover_reindex
from memory_paths import MemoryError
from memory_search import collect_documents, search

root = pilot.fixture("alpha")
config = load_config(root)
results = {"schema_version": 1, "level": "actual-vendor-with-synthetic-fixtures", "cases": [], "native_orchestration": "not exercised by this runner"}


def record(name, run):
    before = pilot.snapshot(root)
    try:
        result = run()
        outcome = {"case": name, "result": result}
    except Exception as exc:
        outcome = {"case": name, "error": {"code": getattr(exc, "code", type(exc).__name__), "message": str(exc), "details": getattr(exc, "details", {})}}
    outcome["inspection_preserved"] = before == pilot.snapshot(root)
    results["cases"].append(outcome)
    (BASE.parent / "backend-fault-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(name, "preserved", outcome["inspection_preserved"], outcome.get("error", {}).get("code", "observed"))
    return outcome


def build(label):
    payload = reindex_payload(root)
    rel, sha = pilot.grant(root, payload, label + "-" + str(time.time_ns()))
    return reindex(root, grant_file=rel, actor=pilot.ACTOR, expected_payload_sha256=sha)


def main():
    record("wrong-project-config", lambda: query(root, "BRAVO-ONLY-SENTINEL", config=load_config(pilot.fixture("bravo"))))
    profile_path = root / config["contract_root"] / "profiles/basic-memory-v0.23.0.json"
    profile_bytes, profile_stat = profile_path.read_bytes(), profile_path.stat()
    profile_path.write_bytes(profile_bytes + b"\n")
    record("altered-profile-rejected", lambda: query(root, "thermal"))
    profile_path.write_bytes(profile_bytes)
    os.utime(profile_path, ns=(profile_stat.st_atime_ns, profile_stat.st_mtime_ns))
    alias = root / "docs/alias.md"
    alias.symlink_to(pilot.fixture("bravo") / "README.md")
    record("cross-project-alias", lambda: query(root, "BRAVO-ONLY-SENTINEL"))
    alias.unlink()
    unknown = root / config["state"]["projection"] / "unclassified.txt"
    unknown.write_text("sole copy sentinel")
    record("unclassified-projection-query", lambda: query(root, "thermal"))
    record("unclassified-projection-reindex", lambda: reindex_payload(root))
    unknown.unlink()
    projected = next((root / config["state"]["projection"]).glob("*.md"))
    projected_bytes, projected_stat = projected.read_bytes(), projected.stat()
    projected.write_bytes(projected_bytes + b"\nBackend-altered projection sentinel.\n")
    record("altered-projection-rejected", lambda: query(root, "thermal"))
    projected.write_bytes(projected_bytes)
    os.utime(projected, ns=(projected_stat.st_atime_ns, projected_stat.st_mtime_ns))
    source = root / "README.md"
    original, info = source.read_bytes(), source.stat()
    source.write_bytes(original + b"\nAFTER-INDEX-CHANGE\n")
    record("stale-canonical-projection", lambda: query(root, "ERR-ALPHA-731"))
    record("stale-direct-fallback", lambda: search(root, "AFTER-INDEX-CHANGE", mode="lexical"))
    source.write_bytes(original)
    os.utime(source, ns=(info.st_atime_ns, info.st_mtime_ns))
    note = root / "MEMORY/MEM-20260908-00000001.md"
    note_bytes, note_stat = note.read_bytes(), note.stat()
    retracted = parse_record(note_bytes)
    retracted["metadata"]["state"] = "retracted"
    retracted["metadata"]["lifecycle"]["reason"] = "Synthetic lifecycle compatibility test"
    note.write_text(render_record(retracted))
    record("retracted-note-backend-excluded", lambda: query(root, "decision pilot chronology"))
    record("retracted-note-lexical-excluded", lambda: search(root, "decision pilot chronology", mode="lexical"))
    note.write_bytes(note_bytes)
    os.utime(note, ns=(note_stat.st_atime_ns, note_stat.st_mtime_ns))
    db = root / config["state"]["index"] / "basic-memory.db"
    hold = root / config["state"]["maintenance"] / "pilot-outage.db"
    db.rename(hold)
    record("backend-unavailable-fallback", lambda: search(root, "ERR-ALPHA-731", mode="hybrid"))
    hold.rename(db)
    model = root / config["state"]["model_cache"] / json.loads(pilot.PROFILE.read_text())["model"]["revision"] / "model_optimized.onnx"
    absent = model.with_suffix(".held")
    model.rename(absent)
    record("missing-model-no-download", lambda: search(root, "ERR-ALPHA-731", mode="hybrid"))
    absent.rename(model)
    cfg_path = root / "memory.yaml"
    cfg_bytes, cfg_stat = cfg_path.read_bytes(), cfg_path.stat()
    disabled = copy.deepcopy(config)
    disabled["backend"].update(enabled=False, semantic_enabled=False)
    cfg_path.write_text(json.dumps(disabled))
    record("disabled-backend-fallback", lambda: search(root, "ERR-ALPHA-731", mode="hybrid"))
    cfg_path.write_bytes(cfg_bytes)
    os.utime(cfg_path, ns=(cfg_stat.st_atime_ns, cfg_stat.st_mtime_ns))
    profile_sha = digest(pilot.PROFILE.read_bytes())
    record("worker-write-tool-rejection", lambda: run_worker(root, config, {"root": str(root), "profile_sha256": profile_sha, "operation": "write_note", "query": "writer sentinel", "mode": "text", "limit": 10}))
    payload = reindex_payload(root)
    rel, sha = pilot.grant(root, payload, "writer-scope-" + str(time.time_ns()))
    opid = uuid.uuid4().hex
    request = {"root": str(root), "operation": "reindex", "profile_sha256": profile_sha,
        "payload": payload, "grant_file": rel, "actor": pilot.ACTOR, "operation_id": opid,
        "projection_manifest": payload["projection_manifest"],
        "projection_stage": config["state"]["maintenance"] + "/backend-" + opid + "/projection",
        "database": "MEMORY/MEM-20260908-00000001.md"}
    record("worker-canonical-target-rejection", lambda: run_worker(root, config, request, build=True))

    # Frozen packet validates actual canonical text/digests. Its Task attribution
    # is explicitly synthetic; this tests filtering, not manager activation.
    documents, _ = collect_documents(root, config)
    chosen = [d for d in documents if d["path"] == "docs/experiment.md"]
    packet = {"schema_version": 1, "kind": "sys4ai-memory-context", "project_id": config["project"]["id"],
        "created_at": "2026-09-08T00:00:00+00:00", "config_sha256": digest((root / "memory.yaml").read_bytes()),
        "task": {"path": "Tasks/synthetic/task.json", "id": "TASK-20260908-000000AA", "execution_id": "synthetic-filter-evaluation", "generation": 1, "manager": pilot.ACTOR, "inspected_sha256": "0"*64, "subtask_id": "synthetic-filter", "revision_reason": "Bounded packet filter fixture only"},
        "limits": {"max_records": 10, "max_bytes": 200000}, "documents": chosen,
        "references": [{"path": d["path"], "sha256": d["sha256"]} for d in chosen],
        "excluded": [], "empty": False, "authority": "Synthetic fixture; does not authorize a Task or action."}
    pilot.write(root, "Verification/frozen-packet.json", canonical_json(packet))
    packet_ref = {"path": "Verification/frozen-packet.json", "sha256": digest(canonical_json(packet))}
    new_source = root / "docs/sibling-copy.md"
    new_source.write_text("# Sibling copy\nSIBLING-DRAFT-SENTINEL this candidate proposes a new fan-based system.\n")
    new_note = copy.deepcopy(next(d["metadata"] for d in documents if d["kind"] == "memory"))
    new_note.update(id="MEM-20260908-000000AA", title="New fixture knowledge")
    note_path = "MEMORY/" + new_note["id"] + ".md"
    pilot.write(root, note_path, render_record({"metadata": new_note, "body": "SIBLING-DRAFT-SENTINEL new fixture note after the baseline."}))
    governed_before = pilot.snapshot(root, True)
    results["expanded_reindex"] = build("expanded-frozen-index")
    results["expanded_reindex_canonical_preserved"] = pilot.snapshot(root, True) == governed_before
    record("frozen-backend-retrieval", lambda: query(root, "SIBLING-DRAFT-SENTINEL", packet=packet_ref))
    record("frozen-baseline-thermal", lambda: query(root, "passive satellite cooling", packet=packet_ref))
    saved = chosen[0]["path"]
    existing, stat = (root / saved).read_bytes(), (root / saved).stat()
    (root / saved).write_bytes(existing + b"\nChanged approved evidence.\n")
    record("changed-frozen-evidence", lambda: query(root, "passive satellite cooling", packet=packet_ref))
    results["changed_evidence_reindex"] = build("changed-evidence-index")
    record("changed-frozen-after-reindex", lambda: query(root, "passive satellite cooling", packet=packet_ref))
    (root / saved).write_bytes(existing)
    os.utime(root / saved, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    new_source.unlink()
    (root / note_path).unlink()
    results["restored_reindex"] = build("restored-index")
    record("restored-hybrid", lambda: query(root, "passive satellite cooling"))
    (BASE.parent / "backend-fault-results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
