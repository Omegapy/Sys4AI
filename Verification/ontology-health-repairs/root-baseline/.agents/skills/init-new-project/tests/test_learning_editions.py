"""Learning edition, local capability assessment and first binding boundaries."""
from copy import deepcopy
import json
import shutil
import unittest

import test_initializer as fixture


class LearningEditionTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def test_explicit_feature_sets_and_v7_local_capabilities(self):
        h = self.helper
        self.assertEqual({f"governance-starter-v{v}" for v in (5, 6, 7, 8, 9)}, h.MEMORY_CONTRACTS)
        self.assertEqual({f"governance-starter-v{v}" for v in (6, 7, 8, 9)}, h.CAPTURE_CONTRACTS)
        self.assertEqual({"governance-starter-v7", "governance-starter-v8", "governance-starter-v9"}, h.LEARNING_CONTRACTS)
        report = self.run_setup()
        self.assertEqual("governance-starter-v9", report["setup_contract"])
        capability = report["learning"]
        self.assertEqual("available", capability["manual_review"])
        self.assertEqual("available", capability["shared_automatic_checkpoint"])
        self.assertEqual("requires-current-operation-grant", capability["authorized_publication"])
        self.assertEqual("disabled", capability["optional_backend"])
        self.assertFalse(capability["operation_grant_checked"])
        before = fixture.manifest(self.root)
        self.assertEqual(capability, h.assess_learning(self.target))
        self.assertEqual(before, fixture.manifest(self.root))
        self.assertEqual({"README.md"}, set(h.tree_files(self.target / "MEMORY")))
        self.assertFalse((self.target / ".sys4ai").exists())

    def test_first_binding_appends_only_completion_link_before_hashing(self):
        self.target.mkdir()
        custom = b"# Project rules\n\nRetain these exact instructions.\n"
        (self.target / "AGENTS.md").write_bytes(custom)
        report = self.run_setup(mode="prepare-existing")
        final = (self.target / "AGENTS.md").read_bytes()
        self.assertEqual(custom + self.helper.completion_link(), final)
        config = json.loads((self.target / "memory.yaml").read_text())
        binding = {ref["path"]: ref["sha256"] for ref in config["publication"]["director"]["authority"]}
        self.assertEqual(self.helper.sha(final), binding["AGENTS.md"])
        self.assertEqual("available", report["learning"]["shared_automatic_checkpoint"])
        repeated = self.run_setup(mode="prepare-existing")
        self.assertEqual(final, (self.target / "AGENTS.md").read_bytes())
        self.assertEqual(report["sources"], repeated["sources"])

    def test_narrower_current_scope_is_reported_without_widening_it(self):
        self.run_setup()
        path = self.target / "memory.yaml"
        config = json.loads(path.read_text())
        scope = ["MEMORY", "control_records/memory", ".sys4ai/memory/maintenance"]
        config["publication"]["director"]["scope"] = scope
        path.write_bytes(self.helper.encoded(config))
        before = path.read_bytes()
        capability = self.helper.assess_learning(self.target)
        self.assertEqual("current", capability["director_binding"])
        self.assertEqual("requires-current-operation-grant", capability["authorized_publication"])
        self.assertEqual(scope, capability["publication_scope"])
        self.assertEqual(before, path.read_bytes())

    def test_bound_missing_route_stale_authority_capture_off_and_custom_package(self):
        self.run_setup()
        config_path = self.target / "memory.yaml"
        config = json.loads(config_path.read_text())
        (self.target / "AGENTS.md").write_text("# Owned rules\n")
        capability = self.helper.assess_learning(self.target)
        self.assertEqual("available", capability["manual_review"])
        self.assertEqual("unavailable", capability["shared_automatic_checkpoint"])
        self.assertEqual("stale", capability["director_binding"])
        self.assertEqual("unavailable", capability["authorized_publication"])
        config["integration"]["automatic_capture"] = False
        config_path.write_bytes(self.helper.encoded(config))
        before = fixture.manifest(self.target)
        report = self.run_setup()
        self.assertEqual("off", report["learning"]["shared_automatic_checkpoint"])
        for name in ("memory.yaml", "AGENTS.md"):
            self.assertEqual(before[name], fixture.manifest(self.target)[name])
        missing = self.target / ".agents/skills/memory/scripts/memory_recovery.py"
        missing.unlink()
        before = fixture.manifest(self.target)
        capability = self.helper.assess_learning(self.target)
        self.assertEqual("unavailable", capability["manual_review"])
        self.assertIn(".agents/skills/memory/scripts/memory_recovery.py", capability["resolution"]["memory"]["missing_resources"])
        self.assertEqual(before, fixture.manifest(self.target))

    def test_missing_or_unlisted_learning_source_rejects_before_writes(self):
        template = self.root / self.helper.TEMPLATE
        source = template / self.helper.LEARNING_ROOT / "review-contract.md"
        raw = source.read_bytes()
        source.unlink()
        before = fixture.manifest(self.root)
        with self.assertRaises((self.helper.InitializationError, OSError)):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(before, fixture.manifest(self.root))
        source.write_bytes(raw)
        (source.parent / "project-note.md").write_text("Must not enter a portable module.\n")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "resource inventory"):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(before, fixture.manifest(self.root))

    def test_manual_template_copy_has_local_learning_without_depot_sources(self):
        template = self.root / self.helper.TEMPLATE
        shutil.copytree(template, self.target)
        shutil.rmtree(self.root / "SKILLS-depo/memory")
        shutil.rmtree(self.root / "SKILLS-depo/what-did-you-learn")
        report = self.run_setup(mode="prepare-existing")
        self.assertEqual("available", report["learning"]["shared_automatic_checkpoint"])
        self.assertEqual("orchard", json.loads((self.target / "memory.yaml").read_text())["project"]["id"])
        self.assertEqual([], report["learning"]["diagnostics"])

    def test_unknown_inspectors_never_execute_during_assessment_or_template_preflight(self):
        self.run_setup()
        sentinel = self.root / "must-not-execute.txt"
        payload = (f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n"
                   "raise RuntimeError('unknown inspector executed')\n").encode()
        for relative in (self.helper.LEARNING_RESOLVER, *self.helper.MEMORY_HELPER_FILES):
            with self.subTest(relative=relative):
                target = self.target / relative
                original = target.read_bytes()
                target.write_bytes(payload + original.replace(b"from __future__ import annotations\n", b""))
                before = fixture.manifest(self.root)
                result = self.helper.assess_learning(self.target)
                self.assertEqual("unavailable", result["authorized_publication"])
                self.assertTrue(any("without execution" in item["message"] for item in result["diagnostics"]))
                self.assertFalse(sentinel.exists())
                self.assertEqual(before, fixture.manifest(self.root))
                target.write_bytes(original)
                source = self.root / self.helper.TEMPLATE / relative
                original_source = source.read_bytes()
                source.write_bytes(payload + original_source.replace(b"from __future__ import annotations\n", b""))
                before = fixture.manifest(self.root)
                with self.assertRaisesRegex(self.helper.InitializationError, "without execution"):
                    self.helper.run_initialization(**{**self.arguments, "destination": self.root / "Projects/Second", "project_id": "second", "project_name": "Second"})
                self.assertFalse(sentinel.exists())
                self.assertEqual(before, fixture.manifest(self.root))
                source.write_bytes(original_source)

    def test_existing_custom_learning_packages_are_preserved_without_filling_gaps(self):
        self.target.mkdir()
        custom = {self.helper.LEARNING_ROOT + "/README.md": b"Custom module edition.\n",
                  self.helper.LEARNING_ROOT + "/local.txt": b"Preserve every custom resource.\n",
                  self.helper.LEARNING_SKILL + "/SKILL.md": b"Custom entry skill.\n"}
        for name, raw in custom.items():
            path = self.target / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        before = {name: digest for root in self.helper.LEARNING_TREES for name, digest in self.helper.package_inventory(self.target, root).items()}
        result = self.run_setup(mode="prepare-existing")
        self.assertEqual(before, result["preserved_learning"])
        self.assertEqual(before, result["current_learning"])
        self.assertEqual("unavailable", result["learning"]["manual_review"])
        self.assertFalse((self.target / self.helper.LEARNING_ROOT / "contract.json").exists())
        self.assertFalse((self.target / self.helper.LEARNING_RESOLVER).exists())
        self.run_setup(mode="prepare-existing")


if __name__ == "__main__":
    unittest.main()
