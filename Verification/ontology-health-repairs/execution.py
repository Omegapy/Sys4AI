"""Reviewable repair evidence and exact source adoption; no inferred publication."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run(label, command, timeout=1800, cwd=ROOT):
    folder = OUT / "commands" / label
    folder.mkdir(parents=True, exist_ok=False)
    start = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(command, cwd=cwd, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                     stdout=stdout, stderr=stderr, timeout=timeout)
            code, timed_out = process.returncode, False
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    result = {"command": command, "cwd": str(cwd), "started_at": start,
              "elapsed_seconds": round(time.monotonic() - clock, 4), "exit_code": code,
              "timed_out": timed_out, "stdout_sha256": digest((folder / "stdout.log").read_bytes()),
              "stderr_sha256": digest((folder / "stderr.log").read_bytes())}
    save(folder / "receipt.json", result)
    print(json.dumps(result))
    return code or (1 if timed_out else 0)


def direct_test_receipt(label):
    """Account for a retained ordinary unittest CLI run, without import patches."""
    folder = OUT / "commands" / label
    command = json.loads((folder / "receipt.json").read_text())
    raw = (folder / "stderr.log").read_text()
    inventory = json.loads((OUT / "required-test-inventory.json").read_text())
    expected = {row["id"] for row in inventory["tests"]}
    rows = []
    for line in raw.splitlines():
        match = re.fullmatch(r"(test_\w+) \(([\w.]+)\) \.\.\. (ok|FAIL|ERROR|skipped .+)", line)
        if match:
            method, identity, outcome = match.groups()
            if not identity.endswith("." + method):
                identity += "." + method
            rows.append({"id": identity, "outcome": "passed" if outcome == "ok" else outcome})
    found = {row["id"] for row in rows}
    count_match = re.search(r"^Ran (\d+) tests? in ", raw, re.M)
    valid = (command["exit_code"] == 0 and not command["timed_out"] and expected <= found
             and len(found) == len(rows) and count_match and int(count_match[1]) == len(rows)
             and all(row["outcome"] == "passed" for row in rows))
    result = {"status": "passed" if valid else "failed", "command_receipt": command,
              "inventory_sha256": digest((OUT / "required-test-inventory.json").read_bytes()),
              "required_count": len(expected), "observed_count": len(rows), "missing": sorted(expected - found),
              "new_ids": sorted(found - expected), "tests": rows, "optional_skips_permitted": False,
              "route": "ordinary python -m unittest discover; exact verbose-output accounting"}
    save(folder / "test-identities.json", result)
    print(json.dumps({k: result[k] for k in ("status", "required_count", "observed_count", "missing")}))
    return 0 if valid else 1


def manifest():
    baseline = json.loads((OUT / "baseline.json").read_text())["files"]
    rows = []
    review = []
    selections = [("SKILLS-depo/" + name, ".agents/skills/" + name) for name in ("ontology", "memory", "init-new-project")]
    selections += [(name, "reference-assets/" + name) for name in ("ONTOLOGY-depo", "MEMORY-depo")]
    for source_root, target_root in selections:
        for file in sorted((ROOT / source_root).rglob("*")):
            if not file.is_file() or any(x in file.parts for x in ("__pycache__", ".git")) or file.suffix == ".pyc":
                continue
            relative = file.relative_to(ROOT).as_posix()
            after = digest(file.read_bytes())
            if after == baseline.get(relative, {}).get("sha256"):
                continue
            suffix = file.relative_to(ROOT / source_root).as_posix()
            if suffix.startswith("starter/"):
                raise ValueError("Starter edit needs explicit active-path review: " + relative)
            destination = target_root + "/" + suffix
            target = ROOT / destination
            expected = baseline.get(destination, {}).get("sha256")
            actual = digest(target.read_bytes()) if target.exists() else None
            if actual != expected:
                raise ValueError("Root target differs from pre-edit baseline: " + destination)
            previous = target.read_bytes() if target.exists() else b""
            if expected:
                retained = OUT / "root-baseline" / destination
                retained.parent.mkdir(parents=True, exist_ok=True)
                if retained.exists() and digest(retained.read_bytes()) != expected:
                    raise ValueError("Prior retained baseline changed: " + destination)
                if not retained.exists():
                    retained.write_bytes(previous)
            review.extend(difflib.unified_diff(previous.decode().splitlines(True), file.read_text().splitlines(True),
                                              fromfile=destination, tofile=relative))
            guarded = destination.startswith(tuple(".agents/skills/" + n + "/scripts/" for n in ("ontology", "memory", "init-new-project")))
            rows.append({"source": relative, "path": destination, "expected_sha256": expected,
                         "sha256": after, "owner": "guard-repair" if guarded else "exact-root-adoption"})
    save(OUT / "change-manifest.json", {"schema_version": 1, "plan": "PLAN-20260910-2C3A0863", "changes": rows})
    (OUT / "source-review.patch").write_text("".join(review))
    print(json.dumps({"changes": len(rows), "guarded": sum(r["owner"] == "guard-repair" for r in rows)}))


def guard_preview(operation="ONTGUARD-health-reliability-20260910"):
    sys.path.insert(0, str(ROOT / ".agents/skills/ontology/scripts"))
    from ontology_guard_setup import preview_repair
    from ontology_core import canonical_bytes
    from ontology_guards import profile
    selection = profile(ROOT)
    config = json.loads((ROOT / "ontology-advanced.yaml").read_text())
    bootstrap = json.loads((ROOT / selection["bootstrap"]["path"]).read_text())
    adapters = json.loads((ROOT / selection["adapters"]["path"]).read_text())
    manifest = json.loads((OUT / "change-manifest.json").read_text())["changes"]
    changes = []
    def add(path, raw):
        target = ROOT / path
        before = digest(target.read_bytes()) if target.exists() else None
        after = digest(raw)
        if before != after:
            changes.append({"path": path, "expected_sha256": before, "sha256": after, "content": raw.decode()})
        return {"path": path, "sha256": after}
    for row in manifest:
        raw = (ROOT / row["source"]).read_bytes()
        assert digest(raw) == row["sha256"], row["source"]
        if row["owner"] == "guard-repair":
            add(row["path"], raw)
    proposed = {row["path"]: row["sha256"] for row in changes}
    for family in adapters["families"].values():
        for adapter in family:
            adapter["sha256"] = proposed.get(adapter["path"], adapter["sha256"])
    prefix = "control_records/ontology/guard-bootstrap/" + operation
    adapter_ref = add(prefix + "-adapters.json", canonical_bytes(adapters))
    future = dict(bootstrap, operation_id=operation, adapters=adapter_ref)
    # Bind the reviewed engine and setup versions. Retain original
    # dispatch proof as historical evidence; final installed tests supply the
    # current observation in the release report, without relabeling old proof.
    for key, name in (("engine", "ontology_guards.py"), ("setup", "ontology_guard_setup.py")):
        path = ".agents/skills/ontology/scripts/" + name
        future[key] = {"path": path, "sha256": proposed.get(path, digest((ROOT / path).read_bytes()))}
    future_ref = add(prefix + "-bootstrap.json", canonical_bytes(future))
    config["profiles"]["guards"] = dict(selection, adapters=adapter_ref, bootstrap=future_ref)
    add("ontology-advanced.yaml", canonical_bytes(config))
    result = preview_repair(ROOT, operation_id=operation, changes=changes)
    save(OUT / "root-guard-preview.json", result)
    print(json.dumps({"preview_sha256": result["preview_sha256"], "changes": len(changes), "paths": [r["path"] for r in changes]}))


def adopt_unbound():
    sys.path.insert(0, str(ROOT / ".agents/skills/ontology/scripts"))
    from ontology_core import atomic_write
    rows = json.loads((OUT / "change-manifest.json").read_text())["changes"]
    for row in rows:
        raw = (ROOT / row["source"]).read_bytes()
        target = ROOT / row["path"]
        assert digest(raw) == row["sha256"], row["source"]
        actual = digest(target.read_bytes()) if target.exists() else None
        assert actual == (row["sha256"] if row["owner"] == "guard-repair" else row["expected_sha256"]), row["path"]
    for row in rows:
        if row["owner"] == "exact-root-adoption":
            atomic_write(ROOT, row["path"], (ROOT / row["source"]).read_bytes(), row["expected_sha256"])
    actual = {row["path"]: digest((ROOT / row["path"]).read_bytes()) for row in rows}
    assert all(actual[r["path"]] == r["sha256"] for r in rows)
    save(OUT / "root-adoption.json", {"status": "adopted", "manifest_sha256": digest((OUT / "change-manifest.json").read_bytes()), "reopened": actual})
    print(json.dumps({"adopted": len(rows), "reopened": True}))


def apply_guard(observation_path):
    sys.path.insert(0, str(ROOT / ".agents/skills/ontology/scripts"))
    from ontology_guard_setup import apply
    review = json.loads((OUT / "root-guard-preview.json").read_text())
    observation = json.loads(Path(observation_path).read_text())
    now = datetime.fromisoformat(observation["observed_at"])
    assert 0 <= (datetime.now(timezone.utc) - now).total_seconds() < 240
    assert observation["native_receipt"]["tool"] == "collaboration.list_agents"
    assert any(a["agent_name"] == "/root" and a["agent_status"] == "running"
               for a in observation["native_receipt"]["result"]["agents"])
    changes = review["payload"]["changes"]
    rows = json.loads((OUT / "change-manifest.json").read_text())["changes"]
    for row in rows:
        assert digest((ROOT / row["source"]).read_bytes()) == row["sha256"], row["source"]
    grant = {"schema_version": 1, "operation": "guard-repair", "preview_sha256": review["preview_sha256"],
             "actor_id": "/root", "actor_kind": "director", "observed_at": now.isoformat(),
             "expires_at": (now + timedelta(seconds=300)).isoformat(), "native_receipt": observation["native_receipt"],
             "scope": [r["path"] for r in changes], "reviewed_records": [{k:r[k] for k in ("path", "expected_sha256", "sha256")} for r in changes],
             "task": None, "project_id": "sys4ai-depot", "config_sha256": digest((ROOT / "ontology.yaml").read_bytes())}
    save(OUT / "root-guard-grant.json", grant)
    result = apply(ROOT, review, grant)
    save(OUT / "root-guard-receipt.json", result)
    assert result["status"] == "complete"
    assert all(digest((ROOT / r["path"]).read_bytes()) == r["sha256"] for r in changes)
    print(json.dumps({"status": result["status"], "reopened": len(changes), "preview_sha256": review["preview_sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "run-at", "test-receipt", "manifest", "guard-preview", "guard-apply", "adopt-unbound"))
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.mode == "run":
        raise SystemExit(run(args.args[0], args.args[1:]))
    if args.mode == "run-at":
        raise SystemExit(run(args.args[0], args.args[2:], cwd=Path(args.args[1])))
    if args.mode == "test-receipt":
        raise SystemExit(direct_test_receipt(args.args[0]))
    if args.mode == "guard-apply":
        apply_guard(args.args[0])
        raise SystemExit(0)
    if args.mode == "guard-preview" and args.args:
        guard_preview(args.args[0])
        raise SystemExit(0)
    {"manifest": manifest, "guard-preview": guard_preview, "adopt-unbound": adopt_unbound}[args.mode]()
