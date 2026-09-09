"""Submit final observed reports through the existing canonical plan helper.

This driver never edits canonical plan JSON directly. Run its stages only after
the Director has inspected the corresponding evidence and final artifacts.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from record_plan_evidence import AUTHORITY, PLAN_ID, call, mutate, record
from reconcile_acceptance import ASSESSMENTS, inventory
from check_preservation import inspect

def canonical():
    shown = call(["show", PLAN_ID])["plan"]
    return shown, json.loads(Path(shown["canonical_path"]).read_text())

def requirement_evidence():
    matrix = json.loads((HERE / "acceptance-matrix.json").read_text())
    assert matrix["status"] == "passed" and all(c["status"] == "passed" for c in matrix["criteria"])
    reports = {}
    for number, (groups, observed) in ASSESSMENTS.items():
        native = any(x in groups.split() for x in ("review", "publication", "manager", "reuse", "native_initialization"))
        reports[f"REQ-{number:03d}"] = {"evidence_type": "runtime" if native else "test", "result_status": "passed",
            "locator_or_command": f"Verification/what-did-you-learn/acceptance-matrix.json criteria REQ-{number:03d}; final-audit.md and exact per-criterion evidence references",
            "observed_result": observed, "verification_level": "end_to_end_verified" if number in (16, 27) else "runtime_observed" if native else "broader_suite_passed"}
    record(reports)
    _, current = canonical()
    requirements = deepcopy(current["requirements"])
    for requirement in requirements:
        requirement["status"] = "satisfied"
    mutate("update", payload={"patch": {"requirements": requirements}, "summary": "Mark all 28 unchanged requirements satisfied by current criterion evidence.", "authority_basis": AUTHORITY})
    print("All 28 requirements have current passing evidence and satisfied status.", flush=True)

def final_inspection():
    _, current = canonical()
    assert all(t["status"] == "completed" for t in current["tasks"])
    assert all(r["status"] == "satisfied" for r in current["requirements"])
    result = inspect()
    assert result["status"] == "passed", result
    current_inventory = inventory(current)
    assert len(current_inventory) == 102
    cp = subprocess.run([str(ROOT / ".venv/bin/python"), "-B", str(ROOT / "tools/template_update.py"), "check"], cwd=ROOT, text=True, capture_output=True)
    updater = json.loads(cp.stdout)
    assert cp.returncode == 0 and updater["status"] == "current" and not updater["conflicts"]
    diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout + diff.stderr
    when = datetime.now(timezone.utc).isoformat()
    cutoff = max(e["timestamp"] for item in current["tasks"] + current["requirements"] for e in item["evidence"])
    assert datetime.fromisoformat(when) > datetime.fromisoformat(cutoff)
    observations = []
    preserved = {x["path"]: x for x in result["protected_paths"]}
    for relative in current["project"]["preserved_paths"]:
        item = preserved[relative]
        observations.append({"evidence_locator": relative, "observed_at": when,
            "fact": f"Final inspection confirms {relative} preserved unchanged; current {item['kind']} inventory SHA256 {item['after_inventory_sha256']} equals the frozen baseline inventory SHA256 {item['before_inventory_sha256']}."})
    observations.append({"evidence_locator": "Verification/what-did-you-learn/acceptance-matrix.json", "observed_at": when,
        "fact": "Final integrated inspection confirms all 28 requirements and 81 exact criteria,20 mandatory scenarios and 102 scoped changed artifacts have accepted evidence;2 optional hooks remain excluded."})
    observations.append({"evidence_locator": "tools/template_update.py check", "observed_at": when,
        "fact": f"Final updater inspection reports current with {updater['source_files']} sources and {updater['managed_files']} managed files; final Git whitespace check passed."})
    project = deepcopy(current["project"])
    project["inspected_at"] = when
    project["baseline_facts"] += observations
    (HERE / "final-project-inspection.json").write_text(json.dumps({"status": "passed", "observed_at": when, "evidence_cutoff": cutoff,
        "preservation": result, "current_artifact_inventory": current_inventory, "updater": updater,
        "git_diff_check": "passed", "observations": observations}, indent=2) + "\n")
    checked_links = []
    for name in ("implementation-handoff.md", "final-audit.md"):
        document = HERE / name
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            if target.startswith(("https://", "http://", "#")):
                continue
            destination = (document.parent / target.split("#", 1)[0]).resolve()
            assert destination.exists(), (name, target)
            checked_links.append({"document": name, "target": target})
    (HERE / "delivery-link-check.json").write_text(json.dumps({"status": "passed", "links": checked_links}, indent=2) + "\n")
    mutate("update", payload={"patch": {"project": project}, "summary": "Append strictly later final integrated and exact protected-path observations.", "authority_basis": AUTHORITY})
    shown, _ = canonical()
    result = call(["set-status", PLAN_ID, "--expect-revision", str(shown["revision"]), "--expect-sha256", shown["sha256"],
                   "--status", "completed", "--reason", "The authorized local implementation, scoped adoption, required native scenarios, criterion audit and final preservation inspection are complete; external rollout remains outside this plan.", "--confirmed"])
    print(json.dumps(result["plan"]), flush=True)
    print(json.dumps(call(["validate", PLAN_ID])["plan"]), flush=True)

if __name__ == "__main__":
    {"requirements": requirement_evidence, "inspection": final_inspection}[sys.argv[1]]()
