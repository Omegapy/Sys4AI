"""Assemble evidence without changing the canonical plan, TRD or Task ledgers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PLAN_PATH = next(ROOT.glob("Implementation_Plans/Plan_sys4ai-project-memory-first-release*/plan.json"))
PLAN = json.loads(PLAN_PATH.read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def ref(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def run(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    return {"command": argv, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def task_matches(path):
    result = set()
    for task in PLAN["tasks"]:
        for target in task["target_artifacts"]:
            if path == target or path.startswith(target.rstrip("/") + "/"):
                result.add(task["task_id"])
    if path.startswith("SKILLS-depo/init-new-project/"):
        result.update(("TASK-031", "TASK-032"))
    if path == "SKILLS-depo/memory/tests/test_release_workflows.py":
        result.update(("TASK-024", "TASK-045", "TASK-046", "TASK-047"))
    if path.startswith("Projects/Sys4AI-Template-Project/"):
        result.add("TASK-034")
    if path in {"tests/test_repository_contract.py", "tests/test_task_project_director_adoption.py"}:
        result.add("TASK-037")
    if path.startswith("Verification/project-memory/"):
        # Reports, reproducible runners and disposable fixtures are validation
        # artifacts even where the plan named an aggregate result file.
        result.add("TASK-049")
        if "/native-project/" in path or "native-bootstrap" in path:
            result.update(("TASK-044", "TASK-045", "TASK-046", "TASK-047"))
        elif "/fresh-context" in path or "end-to-end" in path:
            result.add("TASK-048")
        elif "/pilot-work/" in path or "/backend-" in path or "root-backend-" in path:
            result.update(("TASK-040", "TASK-041", "TASK-042", "TASK-043"))
    return sorted(result)


def assemble(native_complete=False):
    py = str(ROOT / ".venv/bin/python")
    host_scope = HERE / "host-testing-scope.json"
    host_direct = host_scope.is_file()
    if host_direct:
        scope = json.loads(host_scope.read_text())
        if scope["user_instruction"] != "so do not used sub-agent and finish testing":
            raise RuntimeError("Unexpected verification-method authority.")
    checks = {}
    updater = run([py, "-B", "tools/template_update.py", "check"])
    watcher = run([py, "-B", "tools/template_watch.py", "status"])
    diff = run(["git", "diff", "--check"])
    updater_value = json.loads(updater["stdout"])
    watcher_value = json.loads(watcher["stdout"])
    checks["Template_current"] = updater["returncode"] == 0 and updater_value["status"] == "current"
    checks["watcher_current_PID_ready"] = watcher["returncode"] == 0 and watcher_value["ready"]
    checks["diff_whitespace"] = diff["returncode"] == 0
    write("watcher-restoration-final.json", watcher)
    write("template-current-final.json", updater)
    suites = []
    memory_suites = ("host-source-memory", "host-installed-memory", "host-template-memory", "host-installed-task") if host_direct else ("final-source-memory", "final-installed-memory", "final-template-memory", "installed-task")
    for name in (*memory_suites, "installed-initializer", "source-role", "final-root", "final-template-contract"):
        result = json.loads((HERE / (name + "-results.json")).read_text())
        log = (ROOT / result["log"]).read_text()
        count = re.search(r"Ran (\d+) tests?", log)
        skips = re.search(r"OK \(skipped=(\d+)\)", log)
        suites.append({"suite": name, "run": int(count.group(1)) if count else None,
            "skipped": int(skips.group(1)) if skips else 0, "returncode": result["returncode"],
            "evidence": ref("Verification/project-memory/" + name + "-results.json")})
    checks["required_test_suites"] = all(s["returncode"] == 0 for s in suites)
    for name in ("root-adoption-current", "root-validation", "backend-root-results", "root-backend-enablement-results", "end-to-end-results", "final-preservation"):
        checks[name] = json.loads((HERE / (name + ".json")).read_text())["status"] == "passed"
    isolated = json.loads((HERE / "backend-isolated-assessment.json").read_text())
    checks["isolated_backend"] = all(isolated["checks"].values())
    checks["canonical_plan_preserved"] = hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest() == "6cd29af3938797c9bb15c7d699f416d50b43e26d7a8103b99afd0c01679a58c6"
    fixture = HERE / "native-project"
    fixture_scripts = []
    for p in (fixture / ".agents/skills/memory/scripts").glob("*.py"):
        fixture_scripts.append({"path": p.relative_to(ROOT).as_posix(), "matches_root": p.read_bytes() == (ROOT / ".agents/skills/memory/scripts" / p.name).read_bytes()})
    checks["native_fixture_current_executable_code"] = all(x["matches_root"] for x in fixture_scripts)
    native_paths = ["Verification/project-memory/native-" + name + "-results.json" for name in ("generic", "complex", "extra-complex", "change-recovery")]
    if any(not (ROOT / p).exists() for p in native_paths):
        raise RuntimeError("Record every native result and unexercised gate before assessment.")
    native = [ref(p) for p in native_paths]
    if host_direct:
        checks["remaining_verification_method_authorized"] = True
        checks["host_direct_workflows"] = json.loads((HERE / "host-testing-results.json").read_text())["status"] == "passed"
    else:
        checks["complete_required_native_scenarios"] = native_complete
    mapping = json.loads((HERE / "task-evidence-map.json").read_text())["tasks"]
    live_tasks = {"TASK-045", "TASK-046", "TASK-047"}
    partial_tasks = set() if native_complete or host_direct else live_tasks
    assessments = []
    for requirement in PLAN["requirements"]:
        linked = [t for t in mapping if requirement["requirement_id"] in t["requirement_ids"]]
        partial = any(t["task_id"] in partial_tasks for t in linked)
        local_override = host_direct and any(t["task_id"] in live_tasks for t in linked)
        evidence = sorted({p for t in linked for p in t["evidence_paths"] if (ROOT / p).is_file()
                           and not p.endswith(("evidence-index.json", "RELEASE-ASSESSMENT.md", "final-validation.json"))})
        if local_override:
            evidence.extend(("Verification/project-memory/host-testing-scope.json", "Verification/project-memory/host-testing-results.json"))
        assessments.append({"requirement_id": requirement["requirement_id"], "title": requirement["title"],
            "acceptance_criteria": requirement["acceptance_criteria"],
            "result": "native-validation-incomplete" if partial else "verified-locally-live-agent-checks-excluded-by-user" if local_override else "verified-within-recorded-scope",
            "implementation": "implemented", "tasks": [t["task_id"] for t in linked],
            "evidence": [ref(p) for p in evidence],
            "limitation": "Required complex/extra-complex/material-change native gates remain incomplete because native launch rejected the reserved senior despite observed stopped workers." if partial else "The user explicitly directed completion without further sub-agents. Functional contracts passed host-run tests; the remaining live-agent runs were not performed or represented as passed." if local_override else "Use each evidence artifact's stated scope; deterministic, vendor, native and fresh-context results are distinct."})
    baseline = json.loads((HERE / "preservation-baseline.json").read_text())["files"]
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode().split("\0")
    closing = {"Verification/project-memory/RELEASE-ASSESSMENT.md", "Verification/project-memory/evidence-index.json",
               "Verification/project-memory/final-validation.json", "Verification/project-memory/release-file-digests.json"}
    artifacts = []
    for path in sorted(set(tracked)):
        p = ROOT / path
        if not path or path in closing or not p.is_file() or "__pycache__" in p.parts:
            continue
        checksum = hashlib.sha256(p.read_bytes()).hexdigest()
        if path in baseline and checksum == baseline[path]["sha256"]:
            continue
        tasks = task_matches(path)
        if not tasks:
            # Unrelated work predating this goal is outside its artifact manifest.
            continue
        reqs = sorted({rid for t in PLAN["tasks"] if t["task_id"] in tasks for rid in t["requirement_ids"]})
        artifacts.append({"path": path, "sha256": checksum, "bytes": p.stat().st_size,
            "change": "modified" if path in baseline else "added", "tasks": tasks, "requirements": reqs})
    changed = json.loads((HERE / "final-preservation.json").read_text())["changed_existing"]
    checks["every_existing_change_mapped"] = all(any(a["path"] == item["path"] for a in artifacts) for item in changed)
    validation = {"schema_version": 1, "observed_at": datetime.now(timezone.utc).isoformat(),
        "status": ("passed-under-user-directed-host-testing" if host_direct else "passed") if all(checks.values()) else "incomplete-native-runtime-blocker",
        "checks": checks, "test_suites": suites, "native_evidence": native, "native_fixture_code": fixture_scripts,
        "verification_method": "host-directed-local-tests" if host_direct else "original-live-agent-scenarios",
        "verification_method_authority": ref("Verification/project-memory/host-testing-scope.json") if host_direct else None,
        "historical_native_scenarios_complete": native_complete,
        "updater": updater_value, "watcher": watcher_value,
        "plan": {"id": PLAN["plan_id"], "revision": PLAN["revision"], "status": PLAN["status"], **ref(PLAN_PATH.relative_to(ROOT).as_posix())},
        "blocked_tasks": sorted(partial_tasks), "reviewed_changes": len(artifacts),
        "implementation_variations": ["Reusable TeX/HTML samples are supplied in the planned tests/fixtures/research directory. Tests copy their exact bytes into temporary projects and generate the PDF fixture locally.",
            "Task integration uses the unchanged existing Task schema and helper; the memory packet is a normal registered immutable artifact.",
            "Native frozen-input probes used a backend-disabled new-project profile and actual packet filtering. Real indexed filtering was separately exercised with the vendor; synthetic Task attribution in that fixture is explicitly identified.",
            "The canonical plan and TRD lifecycle records remain unchanged under the explicit native goal execution boundary."],
        "unexercised": (["Completion of the native complex senior/acceptance, full extra-complex team and material-change native cycle; further sub-agent work excluded by the user." if host_direct else "Completion of the native complex senior/acceptance, full extra-complex team and material-change native cycle."] if not native_complete else []) +
            ["Existing-product adoption or migration", "Git commit/publication", "Host MCP registration", "Cloud/provider routing", "Deployment or GitHub Pages", "Other hosts/platforms or large/scanned research corpora"]}
    if any(not value for key, value in checks.items() if key != "complete_required_native_scenarios"):
        raise RuntimeError("An additional final validation check failed: " + json.dumps(checks))
    write("final-validation.json", validation)
    write("evidence-index.json", {"schema_version": 1, "plan_id": PLAN["plan_id"], "status": validation["status"],
        "requirements": assessments, "tasks": mapping, "artifacts": artifacts,
        "closing_artifacts": sorted(closing),
        "note": "Closing reports are versioned by release-file-digests.json to avoid a self-referential digest cycle. Prior failed attempts remain retained; current passing revisions are identified by exact evidence references."})
    print(json.dumps({"status": validation["status"], "requirements": len(assessments), "artifacts": len(artifacts), "checks": checks}))


if __name__ == "__main__":
    assemble(native_complete=False)
