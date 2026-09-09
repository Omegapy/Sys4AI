"""Isolated real-vendor fixture runner. Requires a fresh saved native receipt."""
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

DEPOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DEPOT / "SKILLS-depo/memory/scripts"))
from memory_core import default_config, render_record
from memory_search import collect_documents, search
from basic_memory_projection import canonical_json, digest
from memory_maintenance import reindex_payload, reindex, pending_reindexes, recover_reindex
from basic_memory_adapter import query, health, run_worker

BASE = Path(__file__).resolve().parent
ACTOR = "/root/memory_backend"
PROFILE = DEPOT / "MEMORY-depo/profiles/basic-memory-v0.23.0.json"


def write(root, rel, value):
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(value if isinstance(value, bytes) else value.encode())


def snapshot(root, governed=False):
    result = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if not path.is_file() or (governed and rel.startswith((".sys4ai/", "Verification/"))):
            continue
        result[rel] = {"sha256": hashlib.file_digest(path.open("rb"), "sha256").hexdigest(),
                       "mtime_ns": path.stat().st_mtime_ns, "bytes": path.stat().st_size}
    return result


def fixture(name):
    root = BASE / "fixtures" / name
    if (root / "memory.yaml").exists():
        return root
    root.mkdir(parents=True)
    config = default_config("pilot-" + name, "Isolated pilot " + name)
    for rel in ("SOUL.md", "AGENTS.md", "ROLE.md"):
        write(root, rel, "Synthetic fixture governance: permit the assigned local memory pilot inside this fixture only.\n")
    config["backend"].update(enabled=True, semantic_enabled=True)
    config["publication"]["director"] = {"actor_id": ACTOR,
        "scope": list(config["state"].values()),
        "authority": [{"path": rel, "sha256": digest((root / rel).read_bytes())} for rel in ("SOUL.md", "AGENTS.md", "ROLE.md")]}
    write(root, "memory.yaml", json.dumps(config, indent=2) + "\n")
    write(root, config["contract_root"] + "/profiles/basic-memory-v0.23.0.json", PROFILE.read_bytes())
    write(root, "README.md", "# Local retrieval\nERR-ALPHA-731 requires a second independent measurement.\n" if name == "alpha" else "# Bravo\nBRAVO-ONLY-SENTINEL is retained only in project bravo.\n")
    write(root, "docs/experiment.md", "# Thermal result\nPassive heat pipes radiate waste heat from a tiny satellite into space without a fan or moving parts.\n")
    write(root, "research/physics.tex", "\\section{Motion}\\label{eq:drag}\nDrag force equals one half of density times velocity squared times area times coefficient.\n")
    write(root, "research/context.html", "<h1 id='thermal'>Heat pipe tests</h1><p>Passive thermal transfer requires no moving parts.</p>")
    write(root, "Tasks/fixture-sentinel/candidate.md", "SIBLING-DRAFT-SENTINEL excluded candidate data.\n")
    write(root, "Roles/fixture/AGENTS.md", "ROLE-ONLY-SENTINEL protected role instructions.\n")
    write(root, "Roles/fixture/ROLE.md", "Protected fixture role.\n")
    write(root, "docs/secrets/ignored.md", "SENSITIVE-PATH-SENTINEL excluded by path.\n")
    stamp = "2026-09-08T00:00:00+00:00"
    for n, kind in enumerate(("decision", "finding", "experiment", "lesson", "handoff"), 1):
        meta = {"schema_version": 1, "id": f"MEM-20260908-{n:08X}", "project_id": "pilot-" + name,
            "type": kind, "title": kind + " pilot chronology", "state": "active", "created": stamp, "modified": stamp,
            "claim": {"level": "historical_context" if kind == "handoff" else "verified_outcome", "summary": "Synthetic pilot record; not actual project findings"},
            "applicability": ["isolated pilot fixture"], "limitations": ["Synthetic fixture data only"], "confidence": "high",
            "sources": [{"path": "README.md", "sha256": digest((root / "README.md").read_bytes()), "locator": "README.md:1", "kind": "verification"}],
            "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None},
            "lifecycle": {"supersedes": [], "superseded_by": None, "reason": None},
            "publication": {"actor_id": ACTOR, "actor_kind": "director", "operation_id": "synthetic-fixture", "approved_at": stamp}}
        write(root, "MEMORY/" + meta["id"] + ".md", render_record({"metadata": meta, "body": "Fixture result retains source provenance and chronology."}))
    model = json.loads(PROFILE.read_text())["model"]
    shutil.copytree(DEPOT / ".sys4ai/memory/model-cache" / model["revision"], root / config["state"]["model_cache"] / model["revision"])
    return root


def grant(root, payload, label):
    receipt = json.loads((BASE / "native-receipt.json").read_text())
    observed = datetime.fromisoformat(receipt["observed_at"])
    config = json.loads((root / "memory.yaml").read_text())
    value = {"schema_version": 1, "grant_id": label, "project_id": config["project"]["id"],
        "actor_id": ACTOR, "actor_kind": "director", "operation": "reindex", "payload_sha256": digest(canonical_json(payload)),
        "config_sha256": digest((root / "memory.yaml").read_bytes()), "scope": payload["paths"],
        "native_receipt": {"tool": receipt["tool"], "result": receipt["result"]},
        "observed_at": receipt["observed_at"], "expires_at": (observed + timedelta(minutes=5)).isoformat(),
        "task": None, "reviewed_records": [], "privacy_redaction": False}
    rel = "Verification/" + label + ".json"
    write(root, rel, json.dumps(value, indent=2) + "\n")
    return rel, value["payload_sha256"]


def run():
    report = {"schema_version": 1, "evidence_level": "actual-vendor-isolated-fixture", "profile_sha256": digest(PROFILE.read_bytes()), "projects": {}, "failures": []}
    for name in ("alpha", "bravo"):
        root = fixture(name)
        config = json.loads((root / "memory.yaml").read_text())
        before = snapshot(root, True)
        for pending in pending_reindexes(root, config):
            rel, sha = grant(root, pending["payload"], "recovery-" + pending["operation_id"])
            recover_reindex(root, pending["operation_id"], grant_file=rel, actor=ACTOR)
        payload = reindex_payload(root)
        rel, sha = grant(root, payload, "reindex-" + str(time.time_ns()))
        current = {"root": str(root), "before_governed": before}
        report["projects"][name] = current
        try:
            current["reindex"] = reindex(root, grant_file=rel, actor=ACTOR, expected_payload_sha256=sha)
            current["after_governed"] = snapshot(root, True)
            current["canonical_preserved"] = current["after_governed"] == before
            before_reads = snapshot(root)
            current["health"] = health(root)
            current["queries"] = []
            cases = json.loads((BASE.parent / "pilot-query-manifest.json").read_text())["queries"]
            for case in cases:
                for mode in case["modes"]:
                    found = query(root, case["query"], mode=mode)
                    current["queries"].append({"case": case["id"], "query": case["query"], "requested_mode": mode, "response": found})
            current["reads_preserved_all_files"] = snapshot(root) == before_reads
        except Exception as exc:
            current["error"] = {"code": getattr(exc, "code", type(exc).__name__), "message": str(exc), "details": getattr(exc, "details", {})}
            current["after_governed"] = snapshot(root, True)
            current["canonical_preserved"] = current["after_governed"] == before
            report["failures"].append({"project": name, **current["error"]})
            print(json.dumps(current["error"]))
        (BASE.parent / "backend-fixture-results.json").write_text(json.dumps(report, indent=2) + "\n")
        print(name, "complete", "preserved", current.get("canonical_preserved"), "reindex", current.get("reindex", {}).get("status"))
    return report


if __name__ == "__main__":
    run()
