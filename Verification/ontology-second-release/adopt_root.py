"""Stage, inspect, then apply only the selected source changes to the depot installation."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "Verification/ontology-second-release"
STAGING = ROOT / ".sys4ai/ontology/root-adoption"
PACKAGES = {"ontology", "memory", "agent-task", "to-trd", "to-implementation-plan", "manage-subagent-roles", "init-new-project"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    current = ROOT
    for part in Path(path).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("Adoption refuses symlinks: " + str(current))
    return current.read_bytes() if current.is_file() else None


def baseline_merge(relative, source, before, baseline):
    original_source = baseline.get(source)
    original_destination = baseline.get(relative)
    proposed = read(source)
    if original_destination is None:
        if before is not None:
            raise ValueError("A new root destination appeared after the baseline: " + relative)
        return proposed, "new-capability"
    if before is None or sha(before) != original_destination["sha256"]:
        raise ValueError("Root bytes changed since the reviewed baseline: " + relative)
    if original_source and original_destination["sha256"] == original_source["sha256"]:
        return proposed, "refresh-identical-base"
    # The depot Task helper owns additional intake policy. Merge source changes
    # into its separate root version, leaving the root policy intact.
    original = subprocess.check_output(["git", "show", "HEAD:" + source], cwd=ROOT)
    if not original_source or sha(original) != original_source["sha256"]:
        raise ValueError("A differing root package lacks exact original source bytes: " + relative)
    with tempfile.TemporaryDirectory(prefix="ontology-adoption-merge-") as directory:
        files = [Path(directory) / name for name in ("root", "base", "source")]
        for file, data in zip(files, (before, original, proposed)):
            file.write_bytes(data)
        merge = subprocess.run(["git", "merge-file", "-p", *map(str, files)], capture_output=True)
        if merge.returncode:
            raise ValueError("Root-local changes need a reviewed merge: " + relative)
    return merge.stdout, "merge-preserving-root-policy"


def stage():
    baseline = json.loads((EVIDENCE / "baseline.json").read_text())["files"]
    selected = []
    for package in sorted(PACKAGES):
        prefix = "SKILLS-depo/" + package + "/"
        for path in sorted((ROOT / prefix).rglob("*")):
            if not path.is_file() or path.is_symlink() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            source = path.relative_to(ROOT).as_posix()
            if source in baseline and sha(path.read_bytes()) == baseline[source]["sha256"]:
                continue
            relative = ".agents/skills/" + package + "/" + source[len(prefix):]
            before = read(relative)
            data, mode = baseline_merge(relative, source, before, baseline)
            if relative == ".agents/skills/agent-task/scripts/task_state.py":
                text = data.decode()
                if "def command_intake(" not in text:
                    raise ValueError("The root intake policy was lost during merge")
                declaration = next(node for node in ast.parse(text).body if isinstance(node, ast.Assign)
                                   and any(isinstance(target, ast.Name) and target.id == "ONTOLOGY_GUARDED_ACTIONS" for target in node.targets))
                actions = ast.literal_eval(declaration.value)
                if "command_intake" in actions:
                    raise ValueError("Unexpected preexisting root intake adapter")
                lines = text.splitlines(keepends=True)
                lines[declaration.lineno-1:declaration.end_lineno] = ["ONTOLOGY_GUARDED_ACTIONS = " + repr([*actions, "command_intake"]) + "\n"]
                text = "".join(lines)
                tail = "\ncommand_intake = _ontology_guard_adapter(command_intake, 'task', 'project_root', ['Tasks'])\n"
                marker = '\nif __name__ == "__main__":'
                if marker not in text or tail in text:
                    raise ValueError("Unexpected root Task guard integration state")
                data = text.replace(marker, tail + marker).encode()
                mode += "+root-intake-guard"
            selected.append((source, relative, before, data, mode))
    # Adopt the exact destinations emitted by the checked Template mapping,
    # preserving non-mapped root references and every canonical ontology record.
    state = json.loads((ROOT / ".sys4ai/template-update/state.json").read_text())
    managed = state.get("files", state.get("managed_files", {}))
    if not isinstance(managed, dict):
        raise ValueError("Inspect the current Template state schema before reference adoption")
    for destination, entry in sorted(managed.items()):
        relative = destination.removeprefix("Projects/Sys4AI-Template-Project/")
        if not relative.startswith("reference-assets/ONTOLOGY-depo/"):
            continue
        source = entry.get("source") if isinstance(entry, dict) else None
        if not source or not source.startswith("ONTOLOGY-depo/"):
            continue
        data = read("Projects/Sys4AI-Template-Project/" + relative)
        if data != read(source):
            raise ValueError("Template reference parity failed: " + relative)
        before = read(relative)
        if before == data:
            continue
        if relative in baseline and (before is None or sha(before) != baseline[relative]["sha256"]):
            raise ValueError("Root reference changed since baseline: " + relative)
        if relative not in baseline and before is not None:
            raise ValueError("A new root reference appeared after baseline: " + relative)
        selected.append((source, relative, before, data, "exact-template-reference"))
    STAGING.mkdir(parents=True, exist_ok=True)
    changes = []
    for source, relative, before, data, mode in selected:
        if data is None:
            raise ValueError("Selected source is absent: " + source)
        if relative.endswith(".py"):
            ast.parse(data, filename=relative)
        staged = STAGING / "after" / relative
        staged.parent.mkdir(parents=True, exist_ok=True); staged.write_bytes(data)
        if before is not None:
            backup = STAGING / "before" / relative
            backup.parent.mkdir(parents=True, exist_ok=True); backup.write_bytes(before)
        changes.append({"source": source, "source_sha256": sha(read(source)), "destination": relative,
                        "expected_sha256": sha(before) if before is not None else None, "sha256": sha(data), "mode": mode,
                        "staged": staged.relative_to(ROOT).as_posix()})
    manifest = {"schema_version": 1, "plan_id": "PLAN-20260909-4B15BB49", "root": str(ROOT),
                "scope": "Changed reusable capability files and exact mapped ontology references; preserve root-specific Task policy and all other files.",
                "changes": changes, "canonical_ontology_changed": False, "registry_changed": False}
    target = EVIDENCE / "root-adoption-manifest.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": "staged", "files": len(changes), "manifest": str(target), "sha256": sha(target.read_bytes())}))


def apply(expected):
    target = EVIDENCE / "root-adoption-manifest.json"
    raw = target.read_bytes()
    if sha(raw) != expected:
        raise ValueError("The reviewed adoption manifest changed")
    manifest = json.loads(raw)
    import sys
    sys.path.insert(0, str(ROOT / "SKILLS-depo/ontology/scripts"))
    from ontology_core import atomic_write, operation_lock
    journal = EVIDENCE / "root-adoption-progress.json"
    recovering = journal.exists()
    if recovering and json.loads(journal.read_text()).get("manifest_sha256") != expected:
        raise ValueError("Existing adoption progress belongs to a different exact manifest")
    for change in manifest["changes"]:
        if sha(read(change["source"])) != change["source_sha256"] or sha(read(change["staged"])) != change["sha256"]:
            raise ValueError("A selected source/staged artifact changed: " + change["source"])
    committed = []
    with operation_lock(ROOT, "control_records/ontology/root-adoption.lock"):
        for change in manifest["changes"]:
            before = read(change["destination"])
            current = sha(before) if before is not None else None
            accepted = {change["expected_sha256"], change["sha256"]} if recovering else {change["expected_sha256"]}
            if current not in accepted:
                raise ValueError("A selected root destination differs from the accepted pre/post snapshots: " + change["destination"])
        def progress(state):
            data = json.dumps({"status": state, "manifest_sha256": expected, "committed": committed}, indent=2).encode()+b"\n"
            relative = journal.relative_to(ROOT).as_posix()
            previous = read(relative)
            atomic_write(ROOT, relative, data, sha(previous) if previous else None)
        progress("applying")
        for change in manifest["changes"]:
            before = read(change["destination"])
            if (sha(before) if before is not None else None) != change["sha256"]:
                atomic_write(ROOT, change["destination"], read(change["staged"]), change["expected_sha256"])
            committed.append(change["destination"])
            progress("applying")
        progress("adopted")
    receipt = {"status": "adopted", "manifest_sha256": expected, "committed": committed,
               "reopened": {c["destination"]: sha(read(c["destination"])) for c in manifest["changes"]}}
    (EVIDENCE / "root-adoption-receipt.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps({"status": receipt["status"], "files": len(committed)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("stage", "apply"))
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args()
    stage() if args.operation == "stage" else apply(args.expected_manifest_sha256)
