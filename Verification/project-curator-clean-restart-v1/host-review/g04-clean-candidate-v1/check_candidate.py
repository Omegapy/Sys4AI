"""Ordinary dependency-candidate evidence using only the existing interpreter."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).parent
SOURCE = ROOT / ".curator-supported-CD80544E/candidate"
SEED = ROOT / ".curator-supported-CD80544E/setup_compatibility/fixtures/release-layout/Sys4AI/Projects/software"


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def snapshot(root, excluded=()):
    rows = []
    for folder, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in excluded)
        for name in sorted(directories + names):
            path = Path(folder) / name
            relative = str(path.relative_to(root))
            if path.is_symlink():
                rows.append({"path": relative, "link": os.readlink(path)})
            elif path.is_file():
                rows.append({"path": relative, "sha256": sha(path), "bytes": path.stat().st_size})
    rows.sort(key=lambda row: row["path"])
    return {"count": len(rows), "sha256": hashlib.sha256(canonical(rows)).hexdigest(), "files": rows}


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


CHILD = '''import hashlib, importlib.metadata, json, platform, sys, tomllib
from pathlib import Path
project, owner_scripts = map(Path, sys.argv[1:])
declaration = tomllib.loads((project / "pyproject.toml").read_text())["project"]["requires-python"]
lock = json.loads((project / "runtime.lock.json").read_text())
version = platform.python_version()
executable = Path(sys.executable).resolve()
executable_sha = hashlib.sha256(executable.read_bytes()).hexdigest()
distributions = sorted(d.metadata["Name"] for d in importlib.metadata.distributions())
checks = {
    "isolated_prefix": sys.prefix != sys.base_prefix,
    "no_installed_distributions": distributions == [],
    "declaration_matches_runtime": declaration == "==" + version,
    "lock_matches_runtime": lock["python"] == version,
    "lock_matches_executable": lock["executable_sha256"] == executable_sha,
}
result = {"runtime": {"version": version, "prefix": sys.prefix, "base_prefix": sys.base_prefix,
                     "executable": str(executable), "executable_sha256": executable_sha,
                     "installed_distributions": distributions}, "checks": checks,
          "product": {"state": "not_run", "reason": "compatibility_required"}}
if all(checks.values()):
    sys.path.insert(0, str(owner_scripts))
    from ontology_build import compile_project
    outcome = compile_project(project)
    outputs = outcome.get("outputs", {})
    inspected = {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in outputs}
    passed = outcome.get("status") == "complete" and bool(outputs) and inspected == outputs
    result["product"] = {"state": "complete" if passed else "failed", "owner": "ontology_build.compile_project",
                         "owner_sha256": hashlib.sha256((owner_scripts / "ontology_build.py").read_bytes()).hexdigest(),
                         "outputs": outputs, "inspected_outputs": inspected,
                         "context": outcome.get("context"), "manifest": outcome.get("manifest")}
    result["checks"]["affected_product"] = passed
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if all(checks.values()) and result["product"]["state"] == "complete" else 2)
'''


def main():
    run = EVIDENCE / (sys.argv[1] if len(sys.argv) > 1 else "run-v1")
    run.mkdir()
    live_before = snapshot(ROOT / ".venv")
    live_before_ref = save(run / "live-environment-before.json", live_before)
    binary = (ROOT / ".venv/bin/python").resolve()
    binary_before = sha(binary)
    source_hash = sha(SOURCE / "SKILLS-depo/curate/scripts/curator_dependencies.py")
    environment = run / "environment"
    command = [str(ROOT / ".venv/bin/python"), "-B", "-m", "venv", "--without-pip", str(environment)]
    created = subprocess.run(command, capture_output=True, timeout=60, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    (run / "venv.stdout").write_bytes(created.stdout)
    (run / "venv.stderr").write_bytes(created.stderr)
    assert created.returncode == 0, created.stderr.decode()[:500]
    candidate_before = snapshot(environment)
    candidate_before_ref = save(run / "candidate-environment-before.json", candidate_before)
    runner = run / "run_compatibility.py"
    runner.write_text(CHILD)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
    observed = subprocess.run([str(environment / "bin/python"), "-I", "-B", "-c", "import platform; print(platform.python_version())"], capture_output=True, check=True, env=env)
    version = observed.stdout.decode().strip()
    parts = [int(part) for part in version.split(".")]
    incompatible = ".".join(map(str, [parts[0], parts[1], parts[2] + 1]))
    save(run / "selected-declaration-change.json", {
        "dependency": "Python interpreter", "owner": "existing Python venv and interpreter",
        "existing_version": version, "compatible_candidate": version, "incompatible_candidate": incompatible,
        "selection": "Exact declaration and lock compatibility in a clean environment; no installation selected.",
        "affected_product": "ontology compilation", "permissions": ["declaration"],
        "runtime_install": False, "package_source": False, "service_start": False,
    })
    sys.path.insert(0, str(SOURCE / "SKILLS-depo/curate/scripts"))
    from curator_dependencies import candidate
    cases = []
    for name, selected_version, expected_code, expected_state in (
        ("compatible", version, 0, "verified_candidate"),
        ("incompatible", incompatible, 2, "held"),
    ):
        project = run / name / "project"
        project.parent.mkdir()
        seed_before = snapshot(SEED, excluded=(".sys4ai", ".venv", ".git", "__pycache__"))
        shutil.copytree(SEED, project, ignore=shutil.ignore_patterns(".sys4ai", ".venv", ".git", "__pycache__"))
        assert snapshot(SEED, excluded=(".sys4ai", ".venv", ".git", "__pycache__"))["sha256"] == seed_before["sha256"]
        (project / "pyproject.toml").write_text('[project]\nname = "ordinary-curator-candidate-fixture"\nversion = "0.0.0"\nrequires-python = "==' + selected_version + '"\n')
        save(project / "runtime.lock.json", {"python": selected_version, "executable_sha256": binary_before})
        before = snapshot(project)
        args = [str(environment / "bin/python"), "-I", "-B", str(runner), str(project), str(SOURCE / "SKILLS-depo/ontology/scripts")]
        process = subprocess.run(args, capture_output=True, timeout=60, env=env)
        stdout = run / (name + ".stdout.json")
        stdout.write_bytes(process.stdout)
        (run / (name + ".stderr")).write_bytes(process.stderr)
        assert process.returncode == expected_code, (name, process.returncode, process.stderr.decode()[:1000])
        observed = json.loads(process.stdout)
        after = snapshot(project, excluded=(".sys4ai",))
        assert after["sha256"] == before["sha256"], name
        receipt = {"path": str(stdout.relative_to(ROOT)), "sha256": sha(stdout)}
        checks = [{"name": key, "passed": passed, "evidence": receipt} for key, passed in observed["checks"].items()]
        checks.append({"name": "affected_product_complete", "passed": observed["product"]["state"] == "complete", "evidence": receipt})
        change = {key: False for key in ("declaration", "package_source", "runtime_install", "service_start", "major", "backend", "schema", "storage")}
        change.update(declaration=True, environment_sha256=candidate_before["sha256"])
        current_environment = snapshot(environment)
        outcome = candidate(change, ["declaration"], checks=checks, current_environment_sha256=current_environment["sha256"])
        assert outcome["state"] == expected_state, outcome
        assert current_environment["sha256"] == candidate_before["sha256"]
        if name == "incompatible":
            assert not (project / ".sys4ai").exists()
        cases.append({"name": name, "returncode": process.returncode, "declaration": "==" + selected_version,
                      "source_files_preserved": before["count"], "product": observed["product"],
                      "candidate_outcome": outcome, "raw_result": receipt,
                      "candidate_environment_unchanged": True})
    live_after = snapshot(ROOT / ".venv")
    live_after_ref = save(run / "live-environment-after.json", live_after)
    assert live_after["sha256"] == live_before["sha256"]
    assert sha(binary) == binary_before
    assert sha(SOURCE / "SKILLS-depo/curate/scripts/curator_dependencies.py") == source_hash
    summary = {
        "kind": "CleanDependencyCandidateVerification", "state": "passed", "criteria": ["TASK-031:1", "TASK-031:2"],
        "runner": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
        "source_owner": {"path": str((SOURCE / "SKILLS-depo/curate/scripts/curator_dependencies.py").relative_to(ROOT)), "sha256": source_hash},
        "existing_interpreter_sha256": binary_before, "observed_python_version": version,
        "candidate_environment": candidate_before_ref, "venv_command": command, "venv_returncode": created.returncode,
        "cases": cases, "live_environment_files": live_before["count"], "live_environment_unchanged": True,
        "live_before": live_before_ref, "live_after": live_after_ref,
        "installation_performed": False, "network_used": False, "service_started": False,
        "limits": ["This is a selected Python declaration/lock candidate with no package installation.",
                   "It does not establish compatibility of unselected dependencies or real project adoption."],
    }
    result_ref = save(run / "summary.json", summary)
    print(json.dumps({"state": summary["state"], "cases": [(c["name"], c["candidate_outcome"]["state"]) for c in cases],
                      "live_environment_files": live_before["count"], "live_environment_unchanged": True, "summary": result_ref}))


if __name__ == "__main__":
    main()
