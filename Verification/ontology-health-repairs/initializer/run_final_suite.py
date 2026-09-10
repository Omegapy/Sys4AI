"""Capture ordinary full unittest execution and its exact initializer inputs."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main():
    baseline = json.loads((OUT / "source-freeze.json").read_text())
    started = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    command = [sys.executable, "-m", "unittest", "discover", "-s", "SKILLS-depo/init-new-project/tests", "-v"]
    stdout, stderr = OUT / "final-suite.stdout.log", OUT / "final-suite.stderr.log"
    with stdout.open("w") as out, stderr.open("w") as err:
        run = subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                             stdout=out, stderr=err, timeout=1800)
    text = stderr.read_text()
    cases = [{"id": match[2], "method": match[1], "outcome": match[3]}
             for match in re.finditer(r"^(test_\S+) \(([^)]+)\) \.\.\. (ok|ERROR|FAIL|skipped[^\n]*)$", text, re.M)]
    changed = [name for name, data in baseline.items()
               if not (ROOT / name).is_file() or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != data["sha256"]]
    summary = re.search(r"Ran (\d+) tests in ([\d.]+)s", text)
    receipt = {"schema_version": 1, "command": command, "cwd": str(ROOT),
               "environment": {"PYTHONDONTWRITEBYTECODE": "1"}, "started_at": started,
               "ended_at": datetime.now(timezone.utc).isoformat(), "duration_seconds": time.monotonic() - clock,
               "exit_code": run.returncode, "source_changed_during_run": changed,
               "status": "passed" if run.returncode == 0 and not changed else "failed",
               "tests_run": int(summary[1]) if summary else None, "test_cases": cases,
               "stdout": stdout.name, "stderr": stderr.name,
               "source_manifest": {"path": "source-freeze.json", "sha256": hashlib.sha256((OUT / "source-freeze.json").read_bytes()).hexdigest()}}
    (OUT / "final-suite.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in ("status", "tests_run", "duration_seconds", "exit_code", "source_changed_during_run")}))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
