"""Ordinary unittest discovery in self-contained source and installed layouts."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from support import PACKAGE, fixture_context, standards_environment, semantic_acceptance_root
from guard_support import SKILLS


class FixtureDiscoveryTests(unittest.TestCase):
    def install_layout(self, base, relative, *, source=False):
        root = base / relative
        skills = root / ("SKILLS-depo" if source else ".agents/skills")
        context = fixture_context()
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        for name in SKILLS:
            shutil.copytree(context["skills"] / name, skills / name, ignore=ignore)
        contracts = root / ("ONTOLOGY-depo" if source else "reference-assets/ONTOLOGY-depo")
        shutil.copytree(context["contracts"], contracts, ignore=shutil.ignore_patterns("starter", "__pycache__", "*.pyc"))
        (root / "tools").mkdir()
        shutil.copyfile(context["root"] / "tools/template_update.py", root / "tools/template_update.py")
        return root, skills / "ontology"

    def assert_layout(self, relative, *, source=False):
        with tempfile.TemporaryDirectory(prefix="ontology layout ") as directory:
            base = Path(directory).resolve()
            root, package = self.install_layout(base, relative, source=source)
            context = fixture_context(package)
            self.assertEqual(context["root"], root)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            for key in ("SYS4AI_STANDARDS_PYTHON", "SYS4AI_SEMANTIC_ACCEPTANCE_ROOT",
                        "SYS4AI_TEST_DEPOT_ROOT", "SYS4AI_GUARD_INSTALLED_ROOT"):
                env.pop(key, None)
            for pattern in ("test_loading.py", "test_guard_engine.py"):
                command = [sys.executable, "-m", "unittest", "discover", "-s", str(package / "tests"), "-p", pattern, "-v"]
                run = subprocess.run(command, cwd=base, env=env, capture_output=True, text=True, timeout=90)
                print(json.dumps({"fixture_root": str(root), "layout": context["layout"],
                                  "command": command, "cwd": str(base), "exit_code": run.returncode,
                                  "stdout": run.stdout, "stderr": run.stderr}))
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_source_layout(self):
        self.assert_layout("source with spaces", source=True)

    def test_installed_root_layout(self):
        self.assert_layout("installed root")

    def test_template_layout(self):
        self.assert_layout("workspace/Projects/Sys4AI-Template-Project")

    def test_deep_initialized_project_layout(self):
        self.assert_layout("one/two with spaces/three/Projects/prepared project")

    def test_missing_own_contract_does_not_borrow_an_ancestor(self):
        with tempfile.TemporaryDirectory(prefix="ontology no fallback ") as directory:
            base = Path(directory).resolve()
            root, package = self.install_layout(base, "owner", source=True)
            nested, nested_package = self.install_layout(root, "Projects/nested")
            (nested / "reference-assets/ONTOLOGY-depo/contract.json").unlink()
            with self.assertRaisesRegex(RuntimeError, "own ontology contracts"):
                fixture_context(nested_package)

    def test_runtime_selection_is_exact_and_never_provisioned(self):
        with tempfile.TemporaryDirectory(prefix="ontology runtime ") as directory:
            base = Path(directory).resolve()
            context = {"root": base / "project"}
            with patch.dict(os.environ, {"SYS4AI_STANDARDS_PYTHON": "", "SYS4AI_SEMANTIC_ACCEPTANCE_ROOT": ""}):
                self.assertIsNone(standards_environment(context))
                self.assertIsNone(semantic_acceptance_root())
            external = base / "selected venv"
            (external / "bin").mkdir(parents=True)
            for name in ("bin/python", "pyvenv.cfg", "certification.json"):
                (external / name).write_text("Fixture selection marker; no backend execution")
            with patch.dict(os.environ, {"SYS4AI_STANDARDS_PYTHON": str(external / "bin/python")}):
                self.assertEqual(standards_environment(context), external)
                (external / "certification.json").unlink()
                with self.assertRaisesRegex(RuntimeError, "incomplete"):
                    standards_environment(context)
            with patch.dict(os.environ, {"SYS4AI_SEMANTIC_ACCEPTANCE_ROOT": str(base / "missing")}):
                with self.assertRaisesRegex(RuntimeError, "incomplete"):
                    semantic_acceptance_root()
            self.assertFalse(context["root"].exists())
            self.assertFalse((base / "missing").exists())


if __name__ == "__main__":
    unittest.main()
