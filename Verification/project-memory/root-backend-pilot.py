"""Scoped real root backend pilot; no provisioning or canonical capture."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".agents/skills/memory/scripts"))
from memory_core import load_config
from basic_memory_projection import canonical_json, digest
from basic_memory_adapter import health, query
from memory_maintenance import reindex_payload, reindex
from memory_search import collect_documents, search


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def snapshot(runtime=False):
    paths = set()
    for raw in ("SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md", "README.md", "memory.yaml", "depot/projects.json",
                "Tasks", "Roles", "MEMORY", ".agents/skills/memory", "reference-assets/MEMORY-depo", "docs", "research"):
        base = ROOT / raw
        paths.update(p for p in (base.rglob("*") if base.is_dir() else [base]) if p.is_file() and "__pycache__" not in p.parts)
    if runtime:
        paths.update(p for p in (ROOT / ".sys4ai/memory").rglob("*") if p.is_file())
    return {p.relative_to(ROOT).as_posix(): {"sha256": hashlib.file_digest(p.open("rb"), "sha256").hexdigest(),
            "mtime_ns": p.stat().st_mtime_ns, "bytes": p.stat().st_size} for p in sorted(paths)}


def observed_grant(payload, label):
    saved = json.loads((HERE / "root-backend-native-observation.json").read_text())
    observed = datetime.fromisoformat(saved["observed_at"])
    config = load_config(ROOT)
    grant = {"schema_version": 1, "grant_id": label, "project_id": config["project"]["id"],
        "actor_id": "/root", "actor_kind": "director", "operation": "reindex", "payload_sha256": digest(canonical_json(payload)),
        "config_sha256": digest((ROOT / "memory.yaml").read_bytes()), "scope": payload["paths"],
        "native_receipt": {"tool": saved["tool"], "result": saved["result"]}, "observed_at": saved["observed_at"],
        "expires_at": (observed + timedelta(minutes=5)).isoformat(), "task": None, "reviewed_records": [], "privacy_redaction": False}
    write(label + "-payload.json", payload)
    write(label + "-grant.json", grant)
    return "Verification/project-memory/" + label + "-grant.json", grant["payload_sha256"]


def rebuild(label):
    payload = reindex_payload(ROOT)
    grant, sha = observed_grant(payload, label)
    start = time.perf_counter()
    result = reindex(ROOT, grant_file=grant, actor="/root", expected_payload_sha256=sha)
    result["parent_seconds"] = time.perf_counter() - start
    return result


def pilot():
    config = load_config(ROOT)
    assert config["backend"]["enabled"] is False and config["backend"]["semantic_enabled"] is False
    report = {"schema_version": 1, "evidence_level": "actual-active-root-vendor-pilot", "observed_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": digest((ROOT / "memory.yaml").read_bytes()), "profile_sha256": digest((ROOT / "reference-assets/MEMORY-depo/profiles/basic-memory-v0.23.0.json").read_bytes()),
        "adapter_sha256": digest((ROOT / ".agents/skills/memory/scripts/basic_memory_adapter.py").read_bytes()), "checks": {}}
    before = snapshot()
    report["first_rebuild"] = rebuild("root-backend-pilot-001")
    report["second_rebuild"] = rebuild("root-backend-pilot-002")
    report["checks"]["rebuilds_preserved_canonical"] = snapshot() == before
    reads_before = snapshot(True)
    report["ordinary_disabled_health"] = health(ROOT)
    report["ordinary_disabled_search"] = search(ROOT, "Root lexical lookup", mode="hybrid")
    report["queries"] = []
    cases = [("exact-note", "Root lexical lookup", "MEMORY/MEM-20260908-6A59F482.md", ["text", "hybrid"]),
             ("conceptual-note", "Inspect stored information without changing files or their timestamps", "MEMORY/MEM-20260908-6A59F482.md", ["vector", "hybrid"]),
             ("exact-source", "project-local", "README.md", ["text", "hybrid"]),
             ("absent-identifier", "ROOT_ABSENT_9923847", None, ["text"])]
    for name, phrase, expected, modes in cases:
        for mode in modes:
            start = time.perf_counter()
            result = query(ROOT, phrase, mode=mode, pilot=True)
            passed = result["available"] and (any(r["path"] == expected for r in result["results"]) if expected else not result["results"])
            report["queries"].append({"id": name, "query": phrase, "requested_mode": mode, "expected_path": expected,
                "result": result, "parent_seconds": time.perf_counter() - start, "passed": passed})
    try:
        query(ROOT, "invalid mutation request", mode="delete", pilot=True)
        report["checks"]["unsupported_operation_rejected"] = False
    except Exception as exc:
        report["unsupported_operation"] = {"code": getattr(exc, "code", type(exc).__name__), "message": str(exc)}
        report["checks"]["unsupported_operation_rejected"] = report["unsupported_operation"]["code"] == "backend_query"
    wrong = json.loads(json.dumps(config)); wrong["project"]["id"] = "wrong-project"
    report["wrong_project"] = query(ROOT, "Root lexical lookup", config=wrong, pilot=True)
    report["checks"]["wrong_project_rejected"] = not report["wrong_project"]["available"]
    report["checks"]["disabled_public_route_preserved"] = report["ordinary_disabled_search"]["mode"] == "lexical" and not report["ordinary_disabled_health"]["available"]
    report["checks"]["known_queries_passed"] = all(q["passed"] for q in report["queries"])
    report["checks"]["read_bytes_and_mtimes_preserved"] = snapshot(True) == reads_before
    report["checks"]["canonical_preserved"] = snapshot() == before
    report["limitations"] = ["Only the current root corpus and one accepted root note were exercised.",
        "Ranking is retrieval relevance, not evidence of truth.", "Pilot calls permit the exact prebuilt local profile while ordinary backend flags stay disabled.",
        "Parent timings include current-source integrity checks; subprocess timing is separately reported."]
    report["status"] = "passed" if all(report["checks"].values()) else "failed"
    write("backend-root-results.json", report)
    write("backend-root-preservation.json", {"before_canonical": before, "after_canonical": snapshot(),
        "before_reads": reads_before, "after_reads": snapshot(True)})
    print(json.dumps({"status": report["status"], "checks": report["checks"], "documents": report["second_rebuild"]["projection_documents"],
        "queries": [{"id": q["id"], "mode": q["requested_mode"], "passed": q["passed"], "limitations": q["result"].get("limitations")} for q in report["queries"]]}))


if __name__ == "__main__":
    pilot()
