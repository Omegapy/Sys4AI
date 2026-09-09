"""Apply the passed, exact root pilot decision and inspect public outage fallback."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("root_pilot", HERE / "root-backend-pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
ROOT = pilot.ROOT
from memory_core import json_bytes
from memory_recovery import atomic_replace


def reference(rel):
    return {"path": rel, "sha256": pilot.digest((ROOT / rel).read_bytes())}


def public(*args):
    argv = [str(ROOT / ".venv/bin/python"), "-B", str(ROOT / ".agents/skills/memory/scripts/memory.py"), "--project-root", str(ROOT), *args]
    cp = subprocess.run(argv, capture_output=True, text=True, check=False)
    return {"command": argv, "returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr, "result": json.loads(cp.stdout)}


isolated = json.loads((HERE / "backend-isolated-assessment.json").read_text())
observed = json.loads((HERE / "backend-root-results.json").read_text())
assert all(isolated["checks"].values()) and observed["status"] == "passed" and all(observed["checks"].values())
for label in ("profile_sha256", "adapter_sha256"):
    assert isolated[label] == observed[label]
old = (ROOT / "memory.yaml").read_bytes()
assert pilot.digest(old) == observed["config_sha256"]
config = json.loads(old)
config["backend"].update(enabled=True, semantic_enabled=True)
config["retrieval"]["mode"] = "hybrid"
after = json_bytes(config)
decision = {"schema_version": 1, "decision": "enable-tested-local-profile", "actor": "/root", "observed_at": datetime.now(timezone.utc).isoformat(),
    "project_id": "sys4ai-depot", "before_config_sha256": pilot.digest(old), "after_config_sha256": pilot.digest(after),
    "profile_sha256": observed["profile_sha256"], "adapter_sha256": observed["adapter_sha256"],
    "changed_fields": {"backend.enabled": [False, True], "backend.semantic_enabled": [False, True], "retrieval.mode": ["lexical", "hybrid"]},
    "basis": [reference("Verification/project-memory/backend-isolated-assessment.json"), reference("Verification/project-memory/backend-root-results.json")],
    "scope": "This exact current root, pinned Basic Memory 0.23.0, local model and guarded repository adapter only.",
    "limitations": ["No automatic host MCP registration or external/cloud provider.", "No existing product adoption or cross-project retrieval.", "Small-corpus compatibility does not establish large-corpus or other-platform behavior.", "Native Task integration is a separate release gate."],
    "certification": "requires current config-bound reindex and actual public queries"}
pilot.write("backend-compatibility-decision.json", decision)
atomic_replace(ROOT, "memory.yaml", after, pilot.digest(old))
checks = {}
result = {"schema_version": 1, "decision": reference("Verification/project-memory/backend-compatibility-decision.json"), "checks": checks}
result["reindex"] = pilot.rebuild("root-backend-enable-001")
before = pilot.snapshot(True)
result["health"] = public("health")
result["exact"] = public("search", "Root lexical lookup")
result["conceptual"] = public("search", "Inspect stored information without changing files or their timestamps")
result["validate"] = public("validate")
checks["public_reads_preserved_bytes_and_mtimes"] = pilot.snapshot(True) == before
checks["public_exact_hybrid"] = result["exact"]["result"].get("mode") == "hybrid" and any(x["path"] == "MEMORY/MEM-20260908-6A59F482.md" for x in result["exact"]["result"].get("results", []))
checks["public_conceptual_hybrid"] = result["conceptual"]["result"].get("mode") == "hybrid" and any(x["path"] == "MEMORY/MEM-20260908-6A59F482.md" for x in result["conceptual"]["result"].get("results", []))
checks["public_commands_succeeded"] = all(result[k]["returncode"] == 0 for k in ("health", "exact", "conceptual", "validate"))
database = ROOT / config["state"]["index"] / "basic-memory.db"
held = HERE / "root-outage-basic-memory.db"
assert not held.exists()
database.rename(held)
try:
    outage_before = pilot.snapshot(True)
    result["outage_health"] = public("health")
    result["outage_search"] = public("search", "Root lexical lookup")
    checks["outage_inspections_preserved_bytes_and_mtimes"] = pilot.snapshot(True) == outage_before
    degraded = result["outage_search"]["result"]
    checks["outage_falls_back_with_note"] = degraded.get("mode") == "lexical" and any(x["path"] == "MEMORY/MEM-20260908-6A59F482.md" for x in degraded.get("results", [])) and any("unavailable" in x.lower() or "absent" in x.lower() for x in degraded.get("limitations", []))
finally:
    assert not database.exists()
    held.rename(database)
checks["restored_runtime_bytes_and_mtimes"] = pilot.snapshot(True) == before
result["restored_health"] = public("health")
result["restored_search"] = public("search", "Root lexical lookup")
checks["restored_hybrid"] = result["restored_search"]["result"].get("mode") == "hybrid"
result["status"] = "passed" if all(checks.values()) else "failed"
pilot.write("root-backend-enablement-results.json", result)
pilot.write("root-backend-enablement-preservation.json", {"before_reads": before, "after_reads": pilot.snapshot(True)})
print(json.dumps({"status": result["status"], "checks": checks, "config_sha256": pilot.digest(after), "health": result["restored_health"]["result"]}))
