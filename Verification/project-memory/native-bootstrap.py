"""Host bootstrap for the authorized disposable native-memory verification."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

DEPOT = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parent / "native-project"
HERE = ROOT / "Verification/native"
PYTHON = str(DEPOT / ".venv/bin/python")
HELPER = str(ROOT / ".agents/skills/agent-task/scripts/task_state.py")
sys.path.insert(0, str(ROOT / ".agents/skills/memory/scripts"))
from memory_core import json_bytes, render_record, sha256
from memory_publish import publish, transaction_payload


def write(rel, value):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(value if isinstance(value, bytes) else json_bytes(value))
    return ref(rel)


def ref(rel):
    return {"path": rel, "sha256": sha256((ROOT / rel).read_bytes())}


def run(command, *arguments, payload=None):
    cp = subprocess.run([PYTHON, HELPER, "--project-root", str(ROOT), command, *arguments],
                        input=json.dumps(payload) if payload else None, text=True, capture_output=True)
    receipt = {"command": command, "returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr}
    write(f"Verification/native/bootstrap-{command}-{datetime.now().timestamp()}.json", receipt)
    if cp.returncode:
        raise RuntimeError(cp.stdout + cp.stderr)
    return json.loads(cp.stdout)


def response(kind):
    return {"work_completed": ["Recorded " + kind + " for the bounded native verification."],
            "verification_evidence": ["Actual native observation and inspected local inputs are retained under Verification/native."],
            "user_response_summary": "Native memory verification bootstrap.",
            "current_summary": "Reserved manager; activate only the actual launched identity after its role reads.",
            "next_step": "Complete the exact native manager handoff.", "blockers": [], "open_questions": [],
            "relevant_files": ["context/native-requirements.json"]}


def event(kind, data):
    task = json.loads((HERE / "task-binding.json").read_text())
    state = json.loads((ROOT / task["path"]).read_text())
    return run("orchestrate", state["task_id"], "--expected-revision", str(state["revision"]),
               payload={"event": {"event_id": "bootstrap-" + kind.replace(".", "-"), "actor": "/root",
                   "execution_id": task["execution_id"], "generation": 1, "kind": kind, "data": data},
                   "response": response(kind)})


def prepare():
    if (HERE / "task-binding.json").exists():
        raise RuntimeError("Existing native bootstrap must be inspected, not repeated.")
    now = datetime.now(timezone.utc)
    receipt = {"tool": "collaboration.list_agents", "result": {"agents": [
        {"agent_name": "/root", "agent_status": "running"},
        *[{"agent_name": "/root/" + x, "agent_status": "completed"} for x in ("memory_backend", "memory_core", "memory_initializer")]]}}
    write("Verification/native/bootstrap-native-observation.json", {"observed_at": now.isoformat(), **receipt})
    operation = "MEMOP-native-prior-design-001"
    meta = {"schema_version": 1, "id": "MEM-20260908-10203040", "project_id": "native-memory-fixture",
        "type": "decision", "title": "Fixture representations share an explicit evidence identity", "state": "active",
        "created": now.isoformat(), "modified": now.isoformat(),
        "claim": {"level": "accepted_design", "summary": "The approved disposable fixture design groups only explicitly related representations under one evidence identity."},
        "applicability": ["The approved native-memory fixture only."],
        "limitations": ["This is a prior design input, not a performed experiment or proof of scientific validity."],
        "confidence": "high", "sources": [{**ref("README.md"), "locator": "document", "kind": "design"}],
        "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None},
        "lifecycle": {"supersedes": [], "superseded_by": None, "reason": None},
        "publication": {"actor_id": "/root", "actor_kind": "director", "operation_id": operation, "approved_at": now.isoformat()}}
    content = render_record({"metadata": meta, "body": "Use one evidence identity only when the source relationship is explicit. Preserve each representation and its original locator. Unrelated documents must retain separate identities.\n"})
    rel = "MEMORY/" + meta["id"] + ".md"
    reviewed = {"path": rel, "sha256": sha256(content), "expected_sha256": None}
    payload = transaction_payload(operation, "publish", [{"path": rel, "expected_sha256": None,
        "content": content, "reviewed_record_sha256": reviewed["sha256"]}], "Approve the exact prior design input for the authorized isolated native verification.")
    grant = {"schema_version": 1, "grant_id": "native-prior-design-001", "project_id": meta["project_id"],
        "actor_id": "/root", "actor_kind": "director", "operation": "publish", "payload_sha256": sha256(json_bytes(payload)),
        "config_sha256": ref("memory.yaml")["sha256"], "scope": ["MEMORY"], "native_receipt": receipt,
        "observed_at": now.isoformat(), "expires_at": (now + timedelta(minutes=5)).isoformat(), "task": None,
        "reviewed_records": [reviewed], "privacy_redaction": False}
    if not (ROOT / rel).exists():
        write("Verification/native/seed-reviewed.md", content.encode())
        write("Verification/native/seed-payload.json", payload)
        write("Verification/native/seed-grant.json", grant)
        write("Verification/native/seed-publication-result.json", publish(ROOT, payload, "Verification/native/seed-grant.json", "/root"))
    else:
        assert (ROOT / rel).read_bytes() == (HERE / "seed-reviewed.md").read_bytes()
        assert json.loads((HERE / "seed-publication-result.json").read_text())["state"] == "complete"
    role_cp = subprocess.run([PYTHON, str(ROOT / ".agents/skills/manage-subagent-roles/scripts/role_catalog.py"),
        "--repo-root", str(ROOT), "list", "--format", "json"], capture_output=True, text=True, check=True)
    write("Verification/native/bootstrap-role-catalog.json", role_cp.stdout.encode())
    catalog = json.loads(role_cp.stdout)
    assert catalog["index_status"] == "current" and not catalog["invalid_roles"]
    pair = next(x for x in catalog["valid_roles"] if x["name"] == "task-manager")
    settings = {"observed_at": now.isoformat(), "configured_model": "gpt-6-astra", "configured_effort": "max",
        "effective_agents_defaults": {}, "custom_agents": [],
        "runtime_guarantee": "The available native spawn_agent tool guarantees full-history forks inherit the parent model and reasoning effort and accept no overrides. All role assignments use fork_turns all with overrides omitted.",
        "capacity": "Native runtime exposes four total active slots including the root. Three old workers are actually completed. The manager can queue its required logical team.",
        "context": "Prior implementation history contains no candidates for the new native fixture. Each initial solver must return paths, hashes and status only; the manager must defer reading initial candidates until every initial solver has launched."}
    write("Verification/native/bootstrap-runtime-settings.json", settings)
    context = [ref(x) for x in ("context/native-requirements.json", "Verification/native/bootstrap-runtime-settings.json", rel)]
    new = run("new", payload={"name": "Native project memory release verification",
        "description": "Exercise actual generic, complex, extra-complex and changed-memory input/recovery workflows in this disposable project, using the installed memory and Task helpers.",
        "definition_of_done": ["Actual generic capture and recall are verified.", "Actual complex solvers share a frozen eligible packet and retain independent candidate context.",
            "Actual extra-complex team retains current one-to-one reviews, senior acceptance and dedicated implementation.",
            "Material memory input change and optional recovery preserve native identity, version gates and Task history."],
        "orchestration_enabled": True})
    folder = Path(new["task_folder"])
    state = json.loads((folder / "task.json").read_text())
    binding = {"path": (folder / "task.json").relative_to(ROOT).as_posix(), "task_id": state["task_id"],
        "execution_id": "native-memory-release-001", "generation": 1, "assignment_id": "memory-manager"}
    write("Verification/native/task-binding.json", binding)
    role = {"name": pair["name"], "agents_path": pair["agents_file"], "role_path": pair["role_file"],
        "agents_sha256": pair["agents_sha256"], "role_sha256": pair["role_sha256"], "catalog": ref("Verification/native/bootstrap-role-catalog.json")}
    fit = {"objective": "Complete all four native-memory verification scenarios in this disposable project.",
        "capabilities": ["Task management", "native bounded delegation", "memory evidence inspection", "version and recovery verification"],
        "reads": ["SOUL.md", "ROLE.md", "AGENTS.md", "SPECS.md", ".agents/skills", "Roles", "Tasks", "MEMORY", "README.md", "research", "context", "Verification/native"],
        "writes": ["MEMORY", "coordination", "packets", "Verification/manager", ".sys4ai/memory/maintenance"],
        "deliverable": "Four versioned native evidence reports plus a truthful canonical Task outcome, with actual identities and reconciled stopping.",
        "tools": ["native collaboration", "exec_command", "installed Task and memory helpers"],
        "skills": ["task", "agent-task", "manage-subagent-roles", "memory"],
        "authority": "User goal implements PLAN-20260908-5F47ADB2, whose TASK-044 through TASK-047 authorize disposable native verification. Manager may use nested real native agents and scoped canonical memory publication in this fixture only. No root or product adoption, installation, Git or external authority.",
        "risk": "Cooperative controls on shared filesystem; use separate writes and actual receipts, never synthetic identities.",
        "stop": "All mandatory criteria verified with reconciled children and completed canonical Task; otherwise report an actual non-complete blocker without weakening a gate.",
        "rationale": "Fresh task-manager pair explicitly supports canonical execution ownership and the required nested topology; project-sub-agent lacks manager authority."}
    event("manager.reserve", {"assignment_id": binding["assignment_id"], "role": role, "fit": fit,
        "runtime": {"tools": ["spawn_agent", "list_agents", "send_message", "followup_task", "interrupt_agent"], "depth": 2, "available_slots": 3,
            "evidence": [ref("Verification/native/bootstrap-native-observation.json"), ref("Verification/native/bootstrap-runtime-settings.json")]},
        "settings": {"mode": "verified_inheritance", "model": None, "effort": None, "evidence": [ref("Verification/native/bootstrap-runtime-settings.json")]},
        "context": context, "source_refs": context, "authority": fit["authority"], "bootstrap_receipt": receipt})
    print(json.dumps(binding))


if __name__ == "__main__":
    prepare()
