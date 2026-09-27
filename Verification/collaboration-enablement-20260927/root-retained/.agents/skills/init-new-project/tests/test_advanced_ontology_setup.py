"""Actual v9 create/first-prepare, neutral profiles and no runtime provisioning."""
import json
import shutil
import unittest
from unittest.mock import patch

import test_initializer as fixture


class AdvancedSetupTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def test_new_and_first_prepare_have_distinct_local_neutral_capability(self):
        first = self.run_setup()
        second = self.root / "Projects/Second"
        second.mkdir(); (second / "owned.txt").write_text("Preserve project content.\n")
        prepared = self.run_setup(mode="prepare-existing", destination=second, project_id="second", project_name="Second")
        for root, receipt in ((self.target, first), (second, prepared)):
            self.assertEqual(receipt["setup_contract"], "governance-starter-v9")
            config = json.loads((root / "ontology-advanced.yaml").read_text())
            self.assertEqual(config["project_id"], receipt["identity"]["project_id"])
            self.assertTrue(all(p == {"enabled": False} for p in config["profiles"].values()))
            self.assertEqual(config["extensions"], [])
            self.assertEqual(config["publication"]["binding"]["scope"], ["ontology-advanced.yaml", "ONTOLOGY/extensions"])
            for ref in config["publication"]["binding"]["authority"]:
                self.assertEqual(self.helper.sha((root / ref["path"]).read_bytes()), ref["sha256"])
            self.assertTrue(receipt["ontology_advanced"]["installed"], receipt["ontology_advanced"])
            self.assertEqual(receipt["ontology_advanced"]["runtime"], "not-exercised")
            self.assertFalse(receipt["ontology_advanced"]["provisioned"])
            self.assertFalse((root / ".venv-ontology-standards").exists())
            self.assertFalse((root / ".sys4ai").exists())
            self.assertFalse((root / "control_records/ontology").exists())
            self.helper.validate_record(receipt, root, receipt["identity"])
        self.assertEqual((second / "owned.txt").read_text(), "Preserve project content.\n")

    def test_neutral_template_rejects_enabled_profiles_identity_or_proposal_data(self):
        path = self.root / self.helper.TEMPLATE / "ontology-advanced.yaml"
        original = path.read_bytes()
        for mutate in (lambda c:c.update(project_id="sys4ai-depot"), lambda c:c["profiles"]["workbench"].update(enabled=True), lambda c:c.update(extensions=[{"path":"ONTOLOGY/extensions/private.json","sha256":"0"*64}])):
            config = json.loads(original);mutate(config);path.write_bytes(self.helper.encoded(config))
            before = fixture.manifest(self.root)
            with self.assertRaisesRegex(self.helper.InitializationError, "neutral"):
                self.helper.run_initialization(**self.arguments)
            self.assertEqual(fixture.manifest(self.root), before)
            path.write_bytes(original)

    def test_manual_template_copy_specializes_companion_without_starting_profiles(self):
        shutil.copytree(self.root / self.helper.TEMPLATE, self.target)
        receipt = self.run_setup(mode="prepare-existing")
        self.assertEqual(json.loads((self.target/"ontology-advanced.yaml").read_text())["project_id"], "orchard")
        self.assertTrue(receipt["ontology_advanced"]["installed"])
        before = (self.target/"ontology-advanced.yaml").read_bytes()
        self.run_setup(mode="prepare-existing")
        self.assertEqual((self.target/"ontology-advanced.yaml").read_bytes(), before)

    def test_assessment_never_executes_custom_project_python(self):
        self.run_setup()
        path=self.target/".agents/skills/ontology/scripts/ontology_workbench.py"
        path.write_bytes(b"raise RuntimeError('never execute project code during setup assessment')\n"+path.read_bytes())
        before=fixture.manifest(self.target)
        with patch.object(self.helper.subprocess,"run",side_effect=AssertionError("no subprocess assessment")):
            report=self.helper._advanced("assess",self.target)
        self.assertEqual(report["inspector_execution"],"none")
        self.assertEqual(before,fixture.manifest(self.target))


if __name__ == "__main__":
    unittest.main()
