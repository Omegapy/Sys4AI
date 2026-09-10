"""Exercise the shipped acceptance CLI with disposable injected test outcomes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACKAGE = ROOT / "SKILLS-depo/ontology"
CASES = {
    "required-skip": ("def test_one(self): self.skipTest('Injected required skip')\n    def test_two(self): pass", "core", 1),
    "setup-error": ("@classmethod\n    def setUpClass(cls): raise RuntimeError('Injected setup error')\n    def test_one(self): pass\n    def test_two(self): pass", "core", 1),
    "optional-unselected": ("def test_one(self): self.skipTest('Select an existing local pinned semantic runtime for actual model acceptance.')\n    def test_two(self): pass", "semantic", 0),
    "missing-identity": ("def test_one(self): pass", "core", 1),
}


def main():
    summaries = []
    with tempfile.TemporaryDirectory(prefix="ontology gate injection ") as directory:
        root = Path(directory).resolve() / "deep/project with spaces"
        package = root / ".agents/skills/ontology"
        tests = package / "tests"
        tests.mkdir(parents=True)
        shutil.copytree(PACKAGE / "scripts", package / "scripts", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(PACKAGE / "tests/support.py", tests / "support.py")
        shutil.copytree(ROOT / "ONTOLOGY-depo", root / "reference-assets/ONTOLOGY-depo",
                        ignore=shutil.ignore_patterns("starter", "__pycache__", "*.pyc"))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for key in ("SYS4AI_STANDARDS_PYTHON", "SYS4AI_SEMANTIC_ACCEPTANCE_ROOT", "SYS4AI_TEST_DEPOT_ROOT", "SYS4AI_GUARD_INSTALLED_ROOT"):
            env.pop(key, None)
        for name, (methods, profile, expected) in CASES.items():
            (tests / "test_injected.py").write_text("import unittest\nclass Injected(unittest.TestCase):\n    " + methods + "\n")
            inventory = {"schema_version": 1, "tests": [{"id": "test_injected.Injected." + method, "profile": profile}
                                                       for method in ("test_one", "test_two")],
                         "optional_skip_reasons": {"semantic": ["Select an existing local pinned semantic runtime for actual model acceptance."]}}
            selected_inventory = OUT / ("injected-" + name + ".inventory.json")
            selected_inventory.write_text(json.dumps(inventory, indent=2) + "\n")
            receipt = OUT / ("injected-" + name + ".receipt.json")
            command = [sys.executable, str(PACKAGE / "tests/acceptance_runner.py"), "--tests-dir", str(tests),
                       "--inventory", str(selected_inventory), "--receipt", str(receipt)]
            run = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=30)
            result = json.loads(receipt.read_text())
            assert run.returncode == expected, (name, run.returncode, run.stdout, run.stderr)
            assert result["exit_code"] == expected, (name, result)
            assert result["context"]["root"] == str(root), result["context"]
            summaries.append({"case": name, "expected_exit": expected, "actual_exit": run.returncode,
                              "counts": result["counts"], "receipt": receipt.name,
                              "stdout": run.stdout, "stderr": run.stderr})
    (OUT / "gate-injection-summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
