"""Reopen every protected baseline path without changing project state."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def snapshot(target):
    if target.is_symlink():
        return {"kind": "symlink", "target": os.readlink(target)}
    if target.is_file():
        raw = target.read_bytes()
        return {"kind": "file", "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)}
    if target.is_dir():
        files = {}
        for base, directories, names in os.walk(target, followlinks=False):
            for name in list(directories):
                path = Path(base) / name
                if path.is_symlink():
                    files[path.relative_to(target).as_posix()] = snapshot(path)
                    directories.remove(name)
            for name in names:
                path = Path(base) / name
                files[path.relative_to(target).as_posix()] = snapshot(path)
        return {"kind": "directory", "files": files}
    return {"kind": "absent"}


def inspect():
    baseline = json.loads((HERE / "baseline.json").read_text())
    results = []
    for relative, before in baseline["protected"].items():
        after = snapshot(ROOT / relative)
        results.append({"path": relative, "result": "preserved" if before == after else "changed",
                        "kind": after["kind"],
                        "before_inventory_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
                        "after_inventory_sha256": hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest(),
                        "files": len(after.get("files", {})) if after["kind"] == "directory" else None})
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "baseline": "Verification/what-did-you-learn/baseline.json",
            "status": "passed" if all(x["result"] == "preserved" for x in results) else "failed",
            "protected_paths": results}


if __name__ == "__main__":
    report = inspect()
    if len(sys.argv) > 1:
        (HERE / sys.argv[1]).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "protected_paths": len(report["protected_paths"]),
                      "changes": [x["path"] for x in report["protected_paths"] if x["result"] != "preserved"]}))
    raise SystemExit(0 if report["status"] == "passed" else 1)
