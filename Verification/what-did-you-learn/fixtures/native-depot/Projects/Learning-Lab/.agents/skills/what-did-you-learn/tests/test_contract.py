"""Static capability checks are read-only; these tests do not model agent judgment."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from learning_contract import MARKER, resolve


def sources():
    if SKILL.parent.name == "SKILLS-depo":
        return SKILL.parent.parent, "source"
    if SKILL.parent.name == "skills" and SKILL.parent.parent.name == ".agents":
        return SKILL.parents[2], "installed"
    raise RuntimeError("Tests require the supported source or installed layout.")


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        origin, layout = sources()
        self.module_source = origin / ("LEARNING-depo" if layout == "source" else "reference-assets/LEARNING-depo")
        self.memory_source = origin / ("SKILLS-depo/memory" if layout == "source" else ".agents/skills/memory")
        self.contract_source = origin / ("MEMORY-depo" if layout == "source" else "reference-assets/MEMORY-depo")
        self.manifest = json.loads((self.module_source / "contract.json").read_text())

    def fixture(self, layout="installed"):
        module = self.root / ("LEARNING-depo" if layout == "source" else "reference-assets/LEARNING-depo")
        skill = self.root / ("SKILLS-depo/what-did-you-learn" if layout == "source" else ".agents/skills/what-did-you-learn")
        memory = self.root / ("SKILLS-depo/memory" if layout == "source" else ".agents/skills/memory")
        contracts = self.root / ("MEMORY-depo" if layout == "source" else "reference-assets/MEMORY-depo")
        for source, target, resources in ((self.module_source, module, self.manifest["required_resources"]),
                                         (SKILL, skill, self.manifest["skill"]["required_resources"]),
                                         (self.memory_source, memory, self.manifest["memory"]["required_resources"]),
                                         (self.contract_source, contracts, self.manifest["memory"]["contract_resources"])):
            for rel in resources:
                destination = target / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / rel, destination)
        for rel, content in {
            "SOUL.md": "# Fixture soul\n", "ROLE.md": "# Fixture owner\n",
            "AGENTS.md": "Follow [completion](.agents/skills/memory/references/automatic-capture.md).\n",
            "memory.yaml": '{"configuration":"not assessed by the static resolver"}\n',
            "Tasks/task.json": '{"fixture":"read-only sentinel"}\n',
            ".sys4ai/memory/index/sentinel.json": '{"index":"unchanged"}\n',
            "MEMORY/README.md": "# No learned fixture records\n",
        }.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        return module, skill, memory

    def test_source_and_installed_layouts_have_identical_static_interfaces(self):
        for layout in ("source", "installed"):
            with self.subTest(layout=layout):
                module, skill, _ = self.fixture(layout)
                before = snapshot(self.root)
                result = resolve(self.root, skill if layout == "source" else None)
                self.assertEqual(layout, result["layout"])
                self.assertTrue(result["module"]["compatible"])
                self.assertEqual(str(module), result["module"]["root"])
                self.assertTrue(result["capabilities"]["manual_review"])
                self.assertTrue(result["capabilities"]["shared_automatic_checkpoint"])
                self.assertEqual("not_assessed", result["capabilities"]["authorized_publication"])
                self.assertEqual("not_assessed", result["capabilities"]["optional_backend"])
                self.assertEqual([], result["errors"])
                self.assertEqual(before, snapshot(self.root))

    def test_missing_module_does_not_fall_back_to_present_depot_sources(self):
        self.fixture("source")
        before = snapshot(self.root)
        result = resolve(self.root)
        self.assertFalse(result["capabilities"]["manual_review"])
        self.assertIn("reference-assets/LEARNING-depo/contract.json", result["missing_resources"])
        self.assertEqual(before, snapshot(self.root))

    def test_missing_dependency_internals_are_not_treated_as_complete_package(self):
        _, _, memory = self.fixture()
        for rel in ("scripts/memory_recovery.py", "references/publication-examples.md"):
            (memory / rel).unlink()
        before = snapshot(self.root)
        result = resolve(self.root)
        self.assertFalse(result["memory"]["interface_compatible"])
        self.assertFalse(result["capabilities"]["manual_review"])
        self.assertEqual(2, len(result["memory"]["missing_resources"]))
        self.assertEqual(before, snapshot(self.root))

    def test_legacy_checkpoint_and_absent_governance_route_keep_manual_review(self):
        _, _, memory = self.fixture()
        checkpoint = memory / "references/automatic-capture.md"
        checkpoint.write_text(checkpoint.read_text().replace(MARKER, ""))
        (self.root / "AGENTS.md").write_text("# Custom instructions without a completion binding\n")
        before = snapshot(self.root)
        result = resolve(self.root)
        self.assertTrue(result["capabilities"]["manual_review"])
        self.assertFalse(result["capabilities"]["shared_automatic_checkpoint"])
        self.assertIn("shared_checkpoint_unavailable", [error["code"] for error in result["errors"]])
        self.assertFalse(result["governance"]["completion_routing"])
        self.assertEqual(before, snapshot(self.root))

    def test_invalid_manifest_and_unsafe_resource_paths_return_no_write_diagnostics(self):
        module, _, _ = self.fixture()
        manifest_path = module / "contract.json"
        for change in (lambda data: data.update(module_version="9.0.0"),
                       lambda data: data.update(project_id="not-portable"),
                       lambda data: data["required_resources"].append("../outside.md"),
                       lambda data: data["memory"].update(capture_triggers=["user-corrected"])):
            data = copy.deepcopy(self.manifest)
            change(data)
            manifest_path.write_text(json.dumps(data))
            before = snapshot(self.root)
            result = resolve(self.root)
            self.assertFalse(result["capabilities"]["manual_review"])
            self.assertTrue(result["errors"])
            self.assertEqual(before, snapshot(self.root))

    def test_symlink_file_and_directory_are_never_followed(self):
        module, _, memory = self.fixture()
        outside = self.root / "external.txt"
        outside.write_text("External sentinel remains unread and unchanged.\n")
        policy = module / "policy.md"
        policy.unlink()
        policy.symlink_to(outside)
        before = snapshot(self.root)
        result = resolve(self.root)
        self.assertIn("reference-assets/LEARNING-depo/policy.md", result["incompatible_resources"])
        self.assertEqual(before, snapshot(self.root))
        scripts = memory / "scripts"
        scripts.rename(memory / "original-scripts")
        scripts.symlink_to(memory / "original-scripts", target_is_directory=True)
        before = snapshot(self.root)
        result = resolve(self.root)
        self.assertFalse(result["memory"]["interface_compatible"])
        self.assertEqual(before, snapshot(self.root))

    def test_ast_inspection_does_not_execute_memory_package_code(self):
        _, _, memory = self.fixture()
        entry = memory / "scripts/memory.py"
        entry.write_text(entry.read_text().replace('commands.add_parser("health")', 'commands.add_parser("obsolete-health")')
                         + '\nraise RuntimeError("dependency code must never execute")\n')
        before = snapshot(self.root)
        result = resolve(self.root)
        self.assertFalse(result["memory"]["interface_compatible"])
        self.assertNotIn("health", result["memory"]["helper_commands"])
        self.assertIn("supersede", result["memory"]["helper_commands"])
        self.assertEqual(before, snapshot(self.root))

    def test_manifest_cannot_hide_missing_required_memory_runtime(self):
        module, _, memory = self.fixture()
        missing = "scripts/memory_recovery.py"
        (memory / missing).unlink()
        manifest = copy.deepcopy(self.manifest)
        manifest["memory"]["required_resources"].remove(missing)
        (module / "contract.json").write_text(json.dumps(manifest))
        before = snapshot(self.root)
        result = resolve(self.root)
        self.assertFalse(result["capabilities"]["manual_review"])
        self.assertIn(missing, result["errors"][0]["message"])
        self.assertEqual(before, snapshot(self.root))

    def test_present_broken_publication_runtime_is_incompatible(self):
        _, _, memory = self.fixture()
        (memory / "scripts/memory_publish.py").write_text("def incomplete(\n")
        before = snapshot(self.root)
        result = resolve(self.root)
        self.assertFalse(result["memory"]["interface_compatible"])
        self.assertIn(".agents/skills/memory/scripts/memory_publish.py", result["memory"]["incompatible_resources"])
        self.assertEqual(before, snapshot(self.root))

    def test_cli_reports_static_status_without_bytecode_or_state_writes(self):
        _, skill, _ = self.fixture()
        before = snapshot(self.root)
        run = subprocess.run([sys.executable, "-S", str(skill / "scripts/learning_contract.py"),
                              "--project-root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        result = json.loads(run.stdout)
        self.assertTrue(result["read_only"])
        self.assertEqual(before, snapshot(self.root))
        self.assertEqual([], list(self.root.rglob("__pycache__")))

    def test_linked_or_unrelated_root_is_rejected(self):
        self.fixture()
        before = snapshot(self.root)
        result = resolve(self.root, self.root / "elsewhere/what-did-you-learn")
        self.assertFalse(result["capabilities"]["manual_review"])
        self.assertEqual("skill_layout", result["errors"][0]["code"])
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        result = resolve(alias)
        self.assertEqual("project_root", result["errors"][0]["code"])
        self.assertEqual(before, snapshot(self.root))


if __name__ == "__main__":
    unittest.main()
