"""CLI workflows using isolated Python and a disposable governance-only depot."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import test_initializer as fixture


class CommandLineTests(unittest.TestCase):
    def test_create_prepare_nested_identity_preservation_and_reruns(self):
        with tempfile.TemporaryDirectory(prefix="sys4ai-governance-e2e-", dir="/private/tmp") as temporary:
            root = fixture.fixture_depot(Path(temporary))
            (root / "Projects/Group").mkdir()
            script = root / "SKILLS-depo/init-new-project/scripts/init_new_project.py"
            # Only read-only Git observations are permitted. Socket access and
            # arbitrary command execution fail in the actual CLI process.
            launcher = """import runpy,sys
from pathlib import Path
def audit(event,args):
 if event.startswith('socket.') or event == 'os.system':
  raise RuntimeError('network or shell execution is forbidden in this fixture')
 if event == 'subprocess.Popen':
  argv=args[1]
  if not isinstance(argv,list) or argv[0] != 'git' or not any(x in argv for x in ('rev-parse','config')):
   raise RuntimeError('only read-only Git observations are allowed')
sys.addaudithook(audit)
script=sys.argv[1];sys.argv=sys.argv[1:]
runpy.run_path(script,run_name='__main__')
"""
            def run(mode, target, identifier, *extra):
                argv = [sys.executable, "-I", "-S", "-c", launcher, str(script), mode,
                        "--destination", str(target), "--project-id", identifier,
                        "--project-name", identifier.title(), "--purpose", "Verify governance setup.", *extra]
                result = subprocess.run(argv, cwd=root, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                        capture_output=True, text=True, timeout=60, check=False)
                return result
            fresh = root / "Projects/Group/Fresh"
            result = run("create", fresh, "fresh")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual("completed", report["status"])
            self.assertEqual("Projects/Group/Fresh", report["identity"]["relative_path"])
            self.assertEqual(list(fixture.BASELINE), sorted(p.name for p in (fresh / ".agents/skills").iterdir()))
            self.assertEqual(["project-sub-agent", "task-manager"], sorted(p.name for p in (fresh / "roles").iterdir() if p.is_dir()))
            self.assertTrue((fresh / "roles/INDEX.md").is_file())
            for name in (".venv", ".sys4ai", "Ontology", "config", "models", "INIT_MEMORY.md"):
                self.assertFalse((fresh / name).exists(), name)
            self.assertEqual(["assets", "registration", "verification"], report["completed_stages"])
            self.assertTrue(all(item["source"].startswith("Projects/Sys4AI-Template-Project/") for item in report["sources"]))
            for name in ("--principal-id", "--dataset-id", "--artifact-receipt"):
                before = fixture.manifest(fresh)
                rejected = run("create", fresh, "fresh", name, "retired-option")
                self.assertEqual(2, rejected.returncode)
                self.assertIn("unrecognized arguments", rejected.stderr)
                self.assertEqual(before, fixture.manifest(fresh))
            manual = root / "Projects/Manual"
            shutil.copytree(root / "Projects/Sys4AI-Template-Project", manual)
            custom = {"README.md": b"Owned README\n", "SPECS.md": b"Owned specifications\n",
                      ".agents/skills/communication/SKILL.md": b"Owned skill\n", "notes.txt": b"Keep notes\n"}
            for name, raw in custom.items():
                (manual / name).write_bytes(raw)
            result = run("prepare-existing", manual, "manual")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            for target, mode, identifier in ((fresh, "create", "fresh"), (manual, "prepare-existing", "manual")):
                identity_before = (target / "project.json").read_bytes()
                result = run(mode, target, identifier)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                repeated = json.loads(result.stdout)
                self.assertEqual("verified-current-files-and-registration", repeated["rerun"])
                self.assertEqual(identity_before, (target / "project.json").read_bytes())
                for name in (".venv", ".sys4ai", "Ontology", "config", "models", "INIT_MEMORY.md"):
                    self.assertFalse((target / name).exists(), name)
            for name, raw in custom.items():
                self.assertEqual(raw, (manual / name).read_bytes())
            registry = json.loads((root / "depot/projects.json").read_text())
            self.assertEqual(4, len(registry["projects"]))
            self.assertEqual(1, sum(entry["id"] == "fresh" for entry in registry["projects"]))
            self.assertEqual(1, sum(entry["id"] == "manual" for entry in registry["projects"]))
            before = fixture.manifest(root)
            conflict = run("prepare-existing", manual, "foreign")
            self.assertEqual(2, conflict.returncode)
            self.assertEqual(before, fixture.manifest(root))
            self.assertFalse((root / "Projects/Sys4AI-Memory-Service").exists())


if __name__ == "__main__":
    unittest.main()
