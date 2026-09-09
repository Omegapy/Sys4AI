"""Run the plan's affected installed and repository checks with retained output."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GROUPS = {
    "initializer": [(".agents/skills/init-new-project/tests", "test_*.py")],
    "memory": [(".agents/skills/what-did-you-learn/tests", "test_*.py")]
              + [(".agents/skills/memory/tests", pattern) for pattern in
                 ("test_learning_integration.py", "test_automatic_capture.py", "test_publication.py",
                  "test_recovery.py", "test_task_integration.py")],
    "repository": [("tests", "test_repository_contract.py"), ("tests", "test_template_update.py"),
                   ("Projects/Sys4AI-Template-Project/tests", "test_template_contract.py")],
}


def run(group):
    records = []
    log = HERE / ("installed-" + group + ".log")
    with log.open("w") as stream:
        for folder, pattern in GROUPS[group]:
            command = [str(ROOT / ".venv/bin/python"), "-B", "-m", "unittest", "discover", "-s", folder, "-p", pattern, "-v"]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            stream.write(json.dumps(command) + "\n" + result.stdout + result.stderr + "\n")
            stream.flush()
            counts = re.findall(r"Ran (\d+) tests?", result.stderr)
            skipped = re.findall(r"OK \(skipped=(\d+)\)", result.stderr)
            record = {"command": command, "exit_code": result.returncode,
                      "observed_at": datetime.now(timezone.utc).isoformat(),
                      "tests_run": int(counts[-1]) if counts else None,
                      "skipped": int(skipped[-1]) if skipped else 0}
            records.append(record)
            print(json.dumps(record), flush=True)
            if result.returncode:
                print(result.stderr[-5000:], flush=True)
                break
    report = {"group": group, "status": "passed" if all(r["exit_code"] == 0 for r in records)
              and len(records) == len(GROUPS[group]) else "failed", "runs": records,
              "log": str(log.relative_to(ROOT))}
    (HERE / ("installed-" + group + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=GROUPS, required=True)
    raise SystemExit(run(parser.parse_args().group))
