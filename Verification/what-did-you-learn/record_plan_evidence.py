"""Submit reviewed verification reports through the existing canonical helper.

This script stores no alternate plan state. Each mutation uses a fresh show
receipt, and any failure or partial publication stops the sequence.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PLAN_ID = "PLAN-20260909-2AB7D4CC"
HELPER = [str(ROOT / ".venv/bin/python"), str(ROOT / ".agents/skills/to-implementation-plan/scripts/plan_state.py"), "--project-root", str(ROOT)]
AUTHORITY = "Current explicit /goal implement PLAN-20260909-2AB7D4CC, including its verification and final tracking work."


def call(args, payload=None):
    proc = subprocess.run(HELPER + args, input=json.dumps(payload) if payload is not None else None,
                          text=True, capture_output=True, cwd=ROOT)
    try:
        result = json.loads(proc.stdout)
    except ValueError:
        raise SystemExit(proc.stdout + proc.stderr)
    if proc.returncode or result["status"] not in {"ok", "no_op"}:
        raise SystemExit(proc.stdout + proc.stderr)
    if result.get("mutation"):
        with (Path(__file__).parent / "plan-helper-receipts.jsonl").open("a") as stream:
            stream.write(json.dumps({k: result[k] for k in ("command", "status", "plan", "errors", "warnings")}) + "\n")
    return result


def mutate(route, target=None, payload=None):
    shown = call(["show", PLAN_ID])["plan"]
    args = [route, PLAN_ID] + ([target] if target else [])
    args += ["--expect-revision", str(shown["revision"]), "--expect-sha256", shown["sha256"], "--input", "-"]
    return call(args, payload)


def record(reports):
    for target, report in reports.items():
        shown = call(["show", PLAN_ID])
        canonical = json.loads(Path(shown["plan"]["canonical_path"]).read_text())
        items = canonical["tasks"] if target.startswith("TASK-") else canonical["requirements"]
        key = "task_id" if target.startswith("TASK-") else "requirement_id"
        item = next(x for x in items if x[key] == target)
        if target.startswith("TASK-") and item["status"] == "planned" and report.get("complete", True):
            mutate("update-task", target, {"patch": {"status": "in_progress"}, "summary": "Begin the authorized " + item["title"], "authority_basis": AUTHORITY})
        description = report.get("description") or "Acceptance criteria inspected: " + "\n".join(item["acceptance_criteria"])
        if target.startswith("TASK-"):
            description += "\nPlanned verification reports: " + "\n".join(item["verification_steps"])
        payload = {k: report[k] for k in ("evidence_type", "result_status", "locator_or_command", "observed_result", "verification_level")}
        payload.update(description=description, observation_source="agent", summary="Record observed evidence for " + target, authority_basis=AUTHORITY)
        mutate("record-evidence", target, payload)
        if target.startswith("TASK-") and report.get("complete", True) and report["result_status"] == "passed":
            mutate("update-task", target, {"patch": {"status": "completed"}, "summary": "Accept verified " + item["title"], "authority_basis": AUTHORITY})
        print(target + ": " + report["result_status"], flush=True)
    result = call(["validate", PLAN_ID])
    print(json.dumps(result["plan"]), flush=True)


if __name__ == "__main__":
    record(json.loads(Path(sys.argv[1]).read_text()))
