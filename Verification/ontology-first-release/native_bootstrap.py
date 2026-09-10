"""Host bootstrap for the isolated, actual native ontology acceptance flow.

Only an observed tool receipt may supply the native roster or launch identity.
Canonical Task changes always use the installed Task helper.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

DEPOT = Path(__file__).resolve().parents[2]
PYTHON = DEPOT / ".venv/bin/python"


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


class Bootstrap:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.folder = self.root / "Verification/native"
        self.folder.mkdir(parents=True, exist_ok=True)
        self.helper = self.root / ".agents/skills/agent-task/scripts/task_state.py"

    def write(self, relative, value):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value if isinstance(value, bytes) else encode(value))
        return self.ref(relative)

    def ref(self, relative):
        return {"path": relative, "sha256": hashlib.sha256((self.root / relative).read_bytes()).hexdigest()}

    def run(self, command, *args, payload=None):
        cp = subprocess.run([str(PYTHON), str(self.helper), "--project-root", str(self.root), command, *args],
                            input=json.dumps(payload) if payload else None, capture_output=True, text=True)
        receipt = {"command": command, "returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr}
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        self.write(f"Verification/native/bootstrap-{command}-{stamp}.json", receipt)
        if cp.returncode:
            raise RuntimeError(cp.stdout + cp.stderr)
        return json.loads(cp.stdout)

    def event(self, kind, data):
        binding = json.loads((self.folder / "task-binding.json").read_text())
        state = json.loads((self.root / binding["path"]).read_text())
        return self.run("orchestrate", state["task_id"], "--expected-revision", str(state["revision"]),
                        payload={"event": {"event_id": "bootstrap-" + kind.replace(".", "-"),
                                           "actor": "/root", "execution_id": binding["execution_id"],
                                           "generation": 1, "kind": kind, "data": data},
                                 "response": {
                                     "work_completed": ["Recorded " + kind + " for the authorized isolated native acceptance."],
                                     "verification_evidence": ["Actual native receipt and inspected inputs are retained under Verification/native."],
                                     "user_response_summary": "Bootstrap the ontology packet acceptance manager.",
                                     "current_summary": "Only the exact recorded activated manager may own this execution.",
                                     "next_step": "Complete the actual manager handoff and native acceptance.",
                                     "blockers": [], "open_questions": [],
                                     "relevant_files": [{"path": "context/native-requirements.json", "note": "Bounded acceptance criteria."}]}})

    def prepare(self, roster_file):
        if (self.folder / "task-binding.json").exists():
            raise ValueError("Existing reservation requires inspection, not another bootstrap.")
        receipt = json.loads(Path(roster_file).read_text())
        if receipt.get("tool") != "collaboration.list_agents":
            raise ValueError("Provide the actual current native list_agents receipt.")
        self.write("Verification/native/bootstrap-native-roster.json", receipt)
        now = datetime.now(timezone.utc).isoformat()
        requirements = {
            "plan_id": "PLAN-20260909-731308FD", "plan_revision": 4,
            "requirements": ["REQ-039", "REQ-040", "REQ-041", "REQ-054"],
            "authority": "The current user requested implementation of this exact approved plan, including its isolated native Task acceptance. This grant permits fixture-local Task state and scoped fixture ontology publication, with the existing manager and required-team gates. It grants no real root or product Task activation.",
            "objective": "Observe frozen ontology input delivery and material change handling through a real governed complex Task.",
            "criteria": [
                "A confirmed native manager registers one immutable ontology packet through the installed Task helper.",
                "Distinct independent initial solvers, including a queued solver, receive identical registered packet bytes and version references.",
                "Post-dispatch ontology publication cannot enter frozen solver context; altered permitted sources are rejected and the manager handles material inputs through native messaging and assignment.inputs.",
                "The complete complex team produces a coherent accepted analysis with current helper verification, reconciled children and a truthful terminal Task Response."
            ],
            "protected": "Real Sys4AI root and products, all inherited role/helper files, fixture memory corpus/configuration, and unrelated fixture files.",
            "excluded": ["dependency installation", "services", "Git or remote actions", "memory publication", "root Task or plan mutations"],
        }
        self.write("context/native-requirements.json", requirements)
        runtime = {
            "observed_at": now,
            "inheritance": "The available native spawn_agent description guarantees full-history forks inherit parent model and reasoning effort, and accepts no overrides in that mode. Use fork_turns all and omit overrides throughout.",
            "settings_inspection": "Root config has model gpt-6-astra and effort max, with no agents.default_subagent_model, agents.default_subagent_reasoning_effort or custom agent overrides observed. Runtime inheritance is the effective identity guarantee.",
            "native_capability": "spawn_agent, list_agents, send_message, followup_task, wait_agent and interrupt_agent are available; the runtime reports four concurrent slots including the root. Queue the logical team while retaining every required role and candidate.",
            "context": "No solver candidate for this new fixture has been read or supplied. Every initial solver must return only path/hash/status until all initial solvers are launched, including queued ones. Manager defers reading candidate bodies until that boundary.",
        }
        self.write("Verification/native/bootstrap-runtime-settings.json", runtime)
        cp = subprocess.run([str(PYTHON), str(self.root / ".agents/skills/manage-subagent-roles/scripts/role_catalog.py"),
                             "--repo-root", str(self.root), "list", "--format", "json"], capture_output=True, text=True)
        if cp.returncode:
            raise RuntimeError(cp.stdout + cp.stderr)
        self.write("Verification/native/bootstrap-role-catalog.json", cp.stdout.encode())
        catalog = json.loads(cp.stdout)
        if catalog["invalid_roles"] or catalog["index_status"] != "current":
            raise ValueError("Native fixture needs a valid current role catalog.")
        pair = next(p for p in catalog["valid_roles"] if p["name"] == "task-manager")
        role = {"name": pair["name"], "agents_path": pair["agents_file"], "role_path": pair["role_file"],
                "agents_sha256": pair["agents_sha256"], "role_sha256": pair["role_sha256"],
                "catalog": self.ref("Verification/native/bootstrap-role-catalog.json")}
        new = self.run("new", payload={"name": "Native ontology frozen input acceptance",
                                       "description": requirements["objective"],
                                       "definition_of_done": requirements["criteria"], "orchestration_enabled": True})
        task_file = Path(new["task_folder"]) / "task.json"
        state = json.loads(task_file.read_text())
        binding = {"path": task_file.relative_to(self.root).as_posix(), "task_id": state["task_id"],
                   "execution_id": "native-ontology-first-release", "generation": 1, "assignment_id": "ontology-manager"}
        self.write("Verification/native/task-binding.json", binding)
        context = [self.ref(p) for p in ("context/native-requirements.json", "Verification/native/bootstrap-runtime-settings.json")]
        fit = {
            "objective": requirements["objective"],
            "capabilities": ["Task management", "native bounded delegation", "immutable source inspection", "version and recovery verification"],
            "reads": ["SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md", ".agents/skills", "Roles", "Tasks", "ONTOLOGY", "ontology.yaml", "context", "Verification", "control_records/ontology"],
            "writes": ["packets", "coordination", "Verification/manager", "context/selected-source.md",
                       "ONTOLOGY/modules/project", "ONTOLOGY/bindings", "control_records/ontology", ".sys4ai/ontology"],
            "deliverable": "Actual native context/receipt comparison, material-change evidence and the accepted canonical Task outcome.",
            "tools": ["native collaboration", "exec_command", "installed Task and ontology helpers"],
            "skills": ["task", "agent-task", "manage-subagent-roles", "ontology"],
            "authority": requirements["authority"],
            "risk": "Cooperative shared-filesystem ownership requires exact native receipts and disjoint writes. No synthesized native identities.",
            "stop": "All four criteria verified and native owners reconciled before completion; report an exact non-complete blocker if a required gate cannot be met.",
            "rationale": "The fresh task-manager pair supplies explicit execution ownership and nested coordination; the ordinary project-sub-agent does not.",
        }
        self.event("manager.reserve", {"assignment_id": binding["assignment_id"], "role": role, "fit": fit,
                                      "runtime": {"tools": ["spawn_agent", "list_agents", "send_message", "followup_task", "interrupt_agent"],
                                                  "depth": 2, "available_slots": 1,
                                                  "evidence": [self.ref("Verification/native/bootstrap-native-roster.json"), context[1]]},
                                      "settings": {"mode": "verified_inheritance", "model": None, "effort": None, "evidence": [context[1]]},
                                      "context": context, "source_refs": context, "authority": fit["authority"], "bootstrap_receipt": receipt})
        return binding


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", required=True, type=Path)
    p.add_argument("--roster-file", required=True, type=Path)
    a = p.parse_args()
    print(json.dumps(Bootstrap(a.project_root).prepare(a.roster_file), indent=2))
