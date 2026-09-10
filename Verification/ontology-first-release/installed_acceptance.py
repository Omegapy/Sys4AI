"""Observe actual installed interfaces and byte/mtime-preserving read behavior."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "Verification/ontology-first-release"
PYTHON = ROOT / ".venv/bin/python"
CLI = ROOT / ".agents/skills/ontology/scripts/ontology.py"


def inventory():
    result = {}
    for name in ("ontology.yaml", "ONTOLOGY", ".sys4ai/ontology", "control_records/ontology",
                 "memory.yaml", "MEMORY", "Tasks", ".agents/skills/ontology", ".agents/skills/memory"):
        base = ROOT / name
        for path in ([base, *sorted(base.rglob("*"))] if base.is_dir() else [base]):
            if not path.exists() or path.is_symlink() or "__pycache__" in path.parts:
                continue
            stat = path.stat()
            result[path.relative_to(ROOT).as_posix()] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
                "kind": "file" if path.is_file() else "directory", "mtime_ns": stat.st_mtime_ns,
                "ctime_ns": stat.st_ctime_ns}
    return result


def main():
    scenarios = {
        "health": ["health"], "validation": ["validate"], "task": ["term", "Task"], "trd": ["term", "TRD"],
        "lexical": ["search", "memory retrieval"], "exact-read": ["read", "urn:sys4ai:ontology:core:Task"],
        "neighbors": ["neighbors", "Task"], "path": ["path", "Task", "MemoryRecord"],
        "memory-capability": ["capability", "memory retrieval"],
        "skill-capabilities": ["capability", "Installed memory skill"],
        "deprecated": ["term", "TaskRequirementDocument"],
        "current-governance": ["knowledge", "Task", "--intent", "current"],
        "mixed-history": ["knowledge", "prior Task manager failures", "--intent", "mixed"],
        "manager-role": ["term", "Sys4AI confirmed Task manager role"],
        "unknown": ["term", "no-such-frobnicator-987654321"],
    }
    before = inventory()
    observations = []
    for name, args in scenarios.items():
        command = [str(PYTHON), str(CLI), "--project-root", str(ROOT), *args]
        run = subprocess.run(command, capture_output=True, text=True)
        value = json.loads(run.stdout)
        record = {"scenario": name, "command": command, "returncode": run.returncode, "result": value,
                  "stderr": run.stderr}
        (HERE / ("installed-" + name + ".json")).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        assert run.returncode == 0, record
        assert value.get("mutated") is False, name
        observations.append({"scenario": name, "returncode": run.returncode, "status": value.get("status"),
                             "valid": value.get("valid"), "project_id": value.get("project_id", value.get("context", {}).get("project_id")),
                             "identities": [r.get("@id", r.get("record_id", r.get("path"))) for r in value.get("results", [])],
                             "source_types": sorted({r.get("source_type", "ontology") for r in value.get("results", [])}),
                             "truncation": value.get("truncation"), "evidence": "Verification/ontology-first-release/installed-" + name + ".json"})
    after = inventory()
    differences = [p for p in sorted(before.keys() | after.keys()) if before.get(p) != after.get(p)]
    result = {"schema_version": 1, "plan_id": "PLAN-20260909-731308FD", "observed_at": datetime.now(timezone.utc).isoformat(),
              "verification_level": "actual installed CLI observations", "observations": observations,
              "read_only": {"paths_checked": len(before), "bytes_mtime_ctime_preserved": not differences, "differences": differences},
              "not_exercised": ["remote services or publication", "real product adoption", "optional memory backend provisioning"]}
    (HERE / "installed-interface-observations.json").write_text(json.dumps(result, indent=2) + "\n")
    assert not differences, differences
    print(json.dumps({"scenarios": len(observations), "paths_preserved": len(before), "read_mutations": differences}, indent=2))


if __name__ == "__main__":
    main()
