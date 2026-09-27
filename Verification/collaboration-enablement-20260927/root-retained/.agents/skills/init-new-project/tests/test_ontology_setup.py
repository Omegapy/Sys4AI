"""Ontology setup specializes neutral assets and keeps existing installations whole."""
import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import test_initializer as fixture


class OntologySetupTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def test_distinct_local_identities_locks_and_ontology_only_binding(self):
        first = self.run_setup()
        other = self.root / "Projects/Second"
        second = self.run_setup(destination=other, project_id="second", project_name="Orchard")
        namespaces = set()
        for destination, report in ((self.target, first), (other, second)):
            config = json.loads((destination / "ontology.yaml").read_text())
            namespaces.add(config["project"]["namespace"])
            self.assertEqual("governance-starter-v9", report["setup_contract"])
            self.assertEqual(report["identity"]["project_id"], config["project"]["id"])
            self.assertEqual(report["identity"]["project_name"], config["project"]["name"])
            self.assertEqual(report["identity"]["purpose"], config["project"]["purpose"])
            self.assertEqual(".", config["project"]["root"])
            binding = config["publication"]["binding"]
            self.assertEqual(["ONTOLOGY/modules/project", "ONTOLOGY/bindings"], binding["scope"])
            for ref in binding["authority"]:
                self.assertEqual(self.helper.sha((destination / ref["path"]).read_bytes()), ref["sha256"])
            self.assertEqual("specialized", next(x["adoption"] for x in report["sources"] if x["destination"] == "ontology.yaml"))
            self.assertEqual("available", report["ontology"]["structural_readiness"], report["ontology"])
            self.assertEqual("not-exercised", report["ontology"]["runtime"])
            self.assertEqual("requires-current-operation-grant", report["ontology"]["authorized_publication"])
            self.assertFalse((destination / ".sys4ai").exists())
            self.assertFalse((destination / "control_records/ontology").exists())
            for name in ("modules/project/project.jsonld", "bindings/bindings.jsonld"):
                self.assertEqual([], json.loads((destination / "ONTOLOGY" / name).read_text())["@graph"])
        self.assertEqual(2, len(namespaces))

    def test_pristine_manual_copy_specializes_only_config_and_preserves_bound_governance(self):
        shutil.copytree(self.root / self.helper.TEMPLATE, self.target)
        (self.target / "AGENTS.md").write_text("# Local rules\n")
        report = self.run_setup(mode="prepare-existing")
        config = json.loads((self.target / "ontology.yaml").read_text())
        self.assertEqual("orchard", config["project"]["id"])
        self.assertEqual("available", report["ontology"]["structural_readiness"])
        self.assertEqual("current", report["ontology"]["director_binding"])
        before = fixture.manifest(self.target / "ONTOLOGY")
        self.run_setup(mode="prepare-existing")
        self.assertEqual(before, fixture.manifest(self.target / "ONTOLOGY"))

    def test_partial_custom_installation_is_preserved_without_filling_missing_components(self):
        self.target.mkdir()
        owned = self.target / "ONTOLOGY/modules/custom.jsonld"
        owned.parent.mkdir(parents=True)
        owned.write_text("Project-owned ontology format.\n")
        before = fixture.manifest(self.target / "ONTOLOGY")
        report = self.run_setup(mode="prepare-existing")
        self.assertEqual(before, fixture.manifest(self.target / "ONTOLOGY"))
        for name in ("ontology.yaml", self.helper.ONTOLOGY_ROOT, self.helper.ONTOLOGY_SKILL):
            self.assertFalse((self.target / name).exists(), name)
        self.assertEqual("unavailable", report["ontology"]["structural_readiness"])
        self.assertIn("ontology resources are missing", report["ontology"]["diagnostics"][0]["message"])
        self.helper.validate_record(report, self.target, report["identity"])

    def test_import_tampering_and_unknown_inspector_do_not_execute_copied_code(self):
        self.run_setup()
        helper = self.target / self.helper.ONTOLOGY_SKILL / "scripts/ontology_core.py"
        helper.write_bytes(helper.read_bytes() + b"\nraise RuntimeError('must never execute')\n")
        before = fixture.manifest(self.root)
        with patch.object(self.helper.subprocess, "run", side_effect=AssertionError("no subprocess assessment")):
            assessment = self.helper.assess_ontology(self.target)
        self.assertEqual("none", assessment["inspector_execution"])
        self.assertEqual("not-exercised", assessment["runtime"])
        self.assertEqual(before, fixture.manifest(self.root))
        core = self.target / "ONTOLOGY/modules/sys4ai-core/1.0.0/core.jsonld"
        core.write_bytes(core.read_bytes() + b"\n")
        assessment = self.helper.assess_ontology(self.target)
        self.assertEqual("unavailable", assessment["structural_readiness"])
        self.assertIn("lock", assessment["diagnostics"][0]["message"])
        (self.target / self.helper.ONTOLOGY_SKILL / "scripts/ontology_knowledge.py").unlink()
        assessment = self.helper.assess_ontology(self.target)
        self.assertIn("ontology_knowledge.py", assessment["diagnostics"][0]["message"])

    def test_current_narrow_binding_is_reported_without_rebinding_or_widening_scope(self):
        self.run_setup()
        target = self.target / "ontology.yaml"
        config = json.loads(target.read_text())
        binding = config["publication"]["binding"]
        binding["actor_id"] = "/root/selected-director"
        binding["scope"] = ["ONTOLOGY/modules/project"]
        binding["authority"].reverse()
        target.write_bytes(self.helper.encoded(config))
        before = fixture.manifest(self.target)
        result = self.helper.assess_ontology(self.target)
        self.assertEqual("available", result["structural_readiness"], result)
        self.assertEqual("current", result["director_binding"])
        self.assertEqual(binding["scope"], result["publication_scope"])
        self.assertEqual(binding["actor_id"], result["publication_actor"])
        self.assertEqual(before, fixture.manifest(self.target))

    def test_non_neutral_or_missing_template_assets_refuse_before_writes(self):
        template = self.root / self.helper.TEMPLATE
        for name in ("ontology.yaml", "ONTOLOGY/modules/project/project.jsonld", "ONTOLOGY/modules/sys4ai-core/1.0.0/core.jsonld"):
            target = template / name
            original = target.read_bytes()
            if name == "ontology.yaml":
                data = json.loads(original); data["project"]["id"] = "sys4ai-depot"
                target.write_bytes(self.helper.encoded(data))
            elif name.endswith("project.jsonld"):
                data = json.loads(original); data["@graph"] = [{"@id": "urn:private:record"}]
                target.write_bytes(self.helper.encoded(data))
            else:
                target.unlink()
            before = fixture.manifest(self.root)
            with self.subTest(name=name), self.assertRaises((self.helper.InitializationError, OSError)):
                self.helper.run_initialization(**self.arguments)
            self.assertEqual(before, fixture.manifest(self.root))
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
