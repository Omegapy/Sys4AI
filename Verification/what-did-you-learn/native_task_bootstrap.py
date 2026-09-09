"""Bounded host bootstrap; all Task writes use the installed Task helper."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
B = json.loads((HERE / "native-fixture-binding.json").read_text())
ROOT = Path(B["project"])
PYTHON = B["python"]
HELPER = ROOT / ".agents/skills/agent-task/scripts/task_state.py"
sys.path.insert(0, str(ROOT / ".agents/skills/memory/scripts"))
from memory_core import json_bytes, sha256

def write(rel, value):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(value if isinstance(value, bytes) else value.encode() if isinstance(value, str) else json_bytes(value))
    return ref(rel)

def ref(rel):
    return {"path": rel, "sha256": sha256((ROOT / rel).read_bytes())}

def run(command, *arguments, payload=None):
    cp = subprocess.run([PYTHON, "-B", str(HELPER), "--project-root", str(ROOT), command, *arguments],
                        input=json.dumps(payload) if payload is not None else None, capture_output=True, text=True, cwd=ROOT)
    receipt = {"command": command, "arguments": list(arguments), "exit_code": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr}
    write(f"evidence/manager-bootstrap/{command}-{datetime.now().timestamp()}.json", receipt)
    if cp.returncode:
        raise SystemExit(cp.stdout + cp.stderr)
    return json.loads(cp.stdout)

def response(kind):
    return {"work_completed": ["Recorded the actual bounded manager " + kind + "."],
        "verification_evidence": ["Current local role pair, actual native tool receipt, and exact source hashes are retained in evidence/manager-bootstrap."],
        "user_response_summary": "Isolated native learning-manager verification bootstrap.",
        "current_summary": "Only the reserved real native manager receives canonical ownership after activation.",
        "next_step": "Complete the exact manager activation handoff.", "blockers": [], "open_questions": [],
        "relevant_files": ["context/manager-requirements.md"]}

def event(kind, data):
    binding = json.loads((ROOT / "evidence/manager-bootstrap/binding.json").read_text())
    state = json.loads((ROOT / binding["path"]).read_text())
    return run("orchestrate", binding["task_id"], "--expected-revision", str(state["revision"]),
               payload={"event": {"event_id": "wdyl-bootstrap-" + kind.replace(".", "-"), "actor": "/root",
                         "execution_id": binding["execution_id"], "generation": 1, "kind": kind, "data": data}, "response": response(kind)})

def prepare():
    if (ROOT / "evidence/manager-bootstrap/binding.json").exists():
        raise SystemExit("Existing reservation must be inspected, not replaced.")
    native = json.loads((HERE / "native-manager-bootstrap-roster.json").read_text())
    write("evidence/manager-bootstrap/native-observation.json", native)
    write("context/manager-requirements.md", """# Authorized isolated native manager verification

User goal implements PLAN-20260909-2AB7D4CC. Its TASK-021 explicitly authorizes
this isolated canonical Task, native manager, independent solver context and
bounded memory publication. Root depot Tasks are outside this scope.

Verify actual manager-only ownership with MEMORY and control_records/memory
reserved initially. Use the installed learning skill and shared completion
contract. Review after relevant verification and before the terminal response;
child findings remain proposals until the actual owner publishes reviewed bytes.

Use a complex analysis-only subtask with two independent full-problem solvers
and a distinct senior. Their coherent objective is to assess how current fixture
intent requirements and accepted lessons should guide missing-field clarification
while preserving already-clear drafting, and what evidence permits safe reuse.
The current fixture code is intentionally defective; leave implementation to the
separate TASK-022 work unit. No dedicated implementer is required for this
analysis-only Task. Preserve initial solver independence: freeze and register
one identical eligible memory packet before either launch; both initial solvers
return only paths/hashes/status until both have been dispatched. Never inspect
an initial candidate before all initial solver launches.

Demonstrate that a newly published supported note and a sibling proposal never
enter the old frozen packet. A material input change must use actual existing
baseline/input/review gates, including current version binding and stopped-state
reconciliation. For a same-native-instance update use send_message, then the
assignment.inputs helper event, then followup_task. Keep every required solver
and senior. Design the smallest coherent material change with explicit evidence;
do not change the fixture's existing sources or production skills.

Required owner publication is an explicit completion criterion and remains
unmet until its canonical receipt and retrieval are verified. An optional
publication failure must be reported separately without replaying a terminal
event or failing otherwise accepted work. Observe an actual bounded rejection
and preserve the exact failure evidence. Complete through the helper once after
all relevant verification and the manager learning checkpoint. No terminal
reopen/replay, root policy change, dependency installation, backend provision,
external action, Git publication or other project adoption is authorized.

Allowed supporting project-local writes: MEMORY, control_records/memory,
.sys4ai/memory/maintenance, coordination, packets and Verification/manager.
The Task helper owns the Task ledger. Preserve governance, config, existing
context/evidence/fixture files, existing memory record bodies and parent
bootstrap evidence. New memory records use the existing guarded publication
route with actual native manager/Task/config/source grants. No root learned
memory capture or global memory writes are authorized.

Deliver Verification/manager/result.json and concise result.md with each criterion,
actual native identities and receipts, role/source/packet hashes, observed checks,
proposal/publication sequence, material-input gates, final canonical Task state,
stopped child roster, and precise limits. Do not save transcripts or hidden
reasoning. Stop after actual completion or an evidence-backed unmet condition.
""")
    cp = subprocess.run([PYTHON, "-B", str(ROOT / ".agents/skills/manage-subagent-roles/scripts/role_catalog.py"),
                         "--repo-root", str(ROOT), "list", "--format", "json"], capture_output=True, text=True, check=True)
    write("evidence/manager-bootstrap/role-catalog.json", cp.stdout)
    catalog = json.loads(cp.stdout)
    assert catalog["index_status"] == "current" and not catalog["invalid_roles"]
    pair = next(x for x in catalog["valid_roles"] if x["name"] == "task-manager")
    settings = {"observed_at": datetime.now(timezone.utc).isoformat(), "configured_model": "gpt-6-astra", "configured_effort": "max",
        "agent_default_model": None, "agent_default_effort": None, "custom_agent_names": [],
        "native_guarantee": "Full-history collaboration.spawn_agent forks inherit the parent model and reasoning effort and accept no overrides.",
        "dispatch": "fork_turns all; model/effort omitted", "capacity": "Four total active native slots including root; queue within currently observed capacity without reducing the logical team.",
        "independence": "No candidates for the new complex subtask exist in parent history. Both initial solver responses must be paths/hashes/status only until both launch."}
    write("evidence/manager-bootstrap/settings.json", settings)
    context = [ref(x) for x in ("context/manager-requirements.md", "context/intent-requirements.md", "evidence/manager-bootstrap/settings.json")]
    criteria = [
        "Actual native manager ownership and initially reserved bounded memory scope are verified.",
        "Independent solvers share one frozen packet; new notes and sibling proposals stay excluded and material changes use current native input gates.",
        "Required reviewed owner publication and canonical retrieval succeed; optional failure remains separate without terminal replay.",
        "Manager review follows relevant verification and precedes the one terminal Task response with all required team members reconciled."]
    new = run("new", payload={"name": "Native learning manager and frozen inputs", "description": "Verify the installed learning completion contract in a real isolated Task with current owner publication, independent solver packets and material-input gates.",
                               "definition_of_done": criteria, "orchestration_enabled": True})
    folder = Path(new["task_folder"])
    state = json.loads((folder / "task.json").read_text())
    binding = {"path": (folder / "task.json").relative_to(ROOT).as_posix(), "task_id": state["task_id"], "execution_id": "wdyl-native-manager-001", "generation": 1, "assignment_id": "wdyl-manager"}
    write("evidence/manager-bootstrap/binding.json", binding)
    role = {"name": pair["name"], "agents_path": pair["agents_file"], "role_path": pair["role_file"], "agents_sha256": pair["agents_sha256"], "role_sha256": pair["role_sha256"], "catalog": ref("evidence/manager-bootstrap/role-catalog.json")}
    fit = {"objective": "Complete the authorized isolated learning-manager Task and its four observed criteria.",
        "capabilities": ["Task ownership", "native delegation", "frozen independent context", "learning review", "scoped publication and evidence verification"],
        "reads": ["SOUL.md", "ROLE.md", "AGENTS.md", "SPECS.md", ".agents/skills", "Roles", "Tasks", "MEMORY", "memory.yaml", "context", "evidence", "fixture", "coordination", "packets", "Verification/manager"],
        "writes": ["MEMORY", "control_records/memory", ".sys4ai/memory/maintenance", "coordination", "packets", "Verification/manager"],
        "deliverable": "Verified canonical Task and Verification/manager/result.json plus result.md, with current native and exact source evidence.",
        "tools": ["native collaboration", "exec_command", "installed Task/memory/role helpers"], "skills": ["task", "agent-task", "manage-subagent-roles", "memory", "what-did-you-learn"],
        "authority": "Explicit user goal implements PLAN-20260909-2AB7D4CC including its isolated TASK-021; after activation this manager is sole canonical Task writer and may use bounded nested native teams, local evidence and reviewed memory publication only in Learning-Lab.",
        "risk": "Shared filesystem cooperative ownership; preserve required topology and real identity/version gates.",
        "stop": "All four criteria directly verified, required children reconciled and one canonical final Task response completed, or report an actual unmet condition.",
        "rationale": "Fresh task-manager pair supplies canonical execution and nested delegation; generic role cannot own the Task."}
    event("manager.reserve", {"assignment_id": binding["assignment_id"], "role": role, "fit": fit,
        "runtime": {"tools": ["spawn_agent", "list_agents", "send_message", "followup_task", "interrupt_agent"], "depth": 2,
                    "available_slots": 4 - sum(a["agent_status"] == "running" for a in native["receipt"]["result"]["agents"]),
                    "evidence": [ref("evidence/manager-bootstrap/native-observation.json"), ref("evidence/manager-bootstrap/settings.json")]},
        "settings": {"mode": "verified_inheritance", "model": None, "effort": None, "evidence": [ref("evidence/manager-bootstrap/settings.json")]},
        "context": context, "source_refs": context, "authority": fit["authority"], "bootstrap_receipt": native["receipt"]})
    (HERE / "native-manager-binding.json").write_bytes(json_bytes({"project": str(ROOT), **binding}))
    print(json.dumps(binding))

if __name__ == "__main__":
    prepare()
