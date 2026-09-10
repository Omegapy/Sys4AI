"""Run the changed Template contract test against a disposable source fixture."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "SKILLS-depo/init-new-project/tests"))
import test_initializer as fixture


def main():
    with tempfile.TemporaryDirectory(prefix="ontology static template ") as directory:
        depot = fixture.fixture_depot(Path(directory).resolve())
        template = depot / "Projects/Sys4AI-Template-Project"
        tests = template / "tests"
        tests.mkdir()
        shutil.copyfile(ROOT / "SPECS-depo/template-tests/test_template_contract.py", tests / "test_template_contract.py")
        command = [sys.executable, "-m", "unittest", "test_template_contract.TemplateContractTests.test_complete_static_capability_inventory_includes_health_and_test_delivery", "-v"]
        run = subprocess.run(command, cwd=tests, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                             capture_output=True, text=True, timeout=60)
        receipt = {"schema_version": 1, "command": command, "cwd": str(tests),
                   "observed_at": datetime.now(timezone.utc).isoformat(), "exit_code": run.returncode,
                   "stdout": run.stdout, "stderr": run.stderr, "fixture_only": True,
                   "live_template_written": False}
        (OUT / "template-static-contract.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))
        return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
