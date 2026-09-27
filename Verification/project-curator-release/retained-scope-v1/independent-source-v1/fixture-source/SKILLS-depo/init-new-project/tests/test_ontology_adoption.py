"""Explicit ontology adoption preserves every earlier base setup edition."""
import json
from pathlib import Path
import shutil
import unittest

import test_initializer as fixture


class OntologyAdoptionTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def historical(self, edition=7):
        h = self.helper
        contract = f"governance-starter-v{edition}"
        template = self.root / h.TEMPLATE
        backup = Path(self.temporary.name) / "current-template"
        shutil.copytree(template, backup)
        fixture.remove_ontology_edition(template)
        if edition < 7:
            fixture.remove_learning_edition(template)
        if edition < 5:
            fixture.remove_memory_edition(template)
        elif edition == 5:
            config = json.loads((template / "memory.yaml").read_text())
            config["integration"]["automatic_capture"] = False
            (template / "memory.yaml").write_bytes(h.encoded(config))
        role_root = h.ROLE_ROOTS[contract]
        if role_root != "Roles":
            (template / "Roles").rename(template / role_root)
            if edition == 1:
                shutil.rmtree(template / role_root / "task-manager")
                (template / role_root / "INDEX.md").unlink()
            script = template / h.ROLE_HELPER
            script.write_text(script.read_text().replace('ROLE_ROOT_NAME = "Roles"', f'ROLE_ROOT_NAME = "{role_root}"'))
            if edition == 2:
                files = {"SOUL.md": (template / "SOUL.md").read_bytes(), h.ROLE_HELPER: script.read_bytes()}
                files.update({role_root + "/" + name: raw for name, raw in h.tree_files(template / role_root).items() if name != "INDEX.md"})
                (template / role_root / "INDEX.md").write_bytes(h.role_index_bytes(files, required=True, contract=contract))
        policy = json.loads((template / h.TEMPLATE_POLICY).read_text())
        policy.update(roles=role_root, starter_files=sorted(h.required_starters(contract)))
        (template / h.TEMPLATE_POLICY).write_bytes(h.encoded(policy))
        identity = {"schema_version": 1, "project_id": "orchard", "project_name": "Orchard", "purpose": self.arguments["purpose"], "relative_path": "Projects/Orchard"}
        proposed, sources, original = h.source_snapshot(self.root, fixture.SOURCE_SKILL, identity, contract=contract)
        for entry in sources:
            name = entry["destination"]
            entry["adoption"] = "specialized" if contract in h.MEMORY_CONTRACTS and name in h.SPECIALIZED_FILES and proposed[name] != original.get(name) else "adopted"
        record = {"schema_version": 1, "setup_contract": contract, "status": "partial", "mode": "create",
                  "operation_id": "project-setup-" + str(edition) * 32, "identity": identity, "project_root": str(self.target),
                  "sources": sources, "owned_files": {name: h.sha(raw) for name, raw in proposed.items()}, "preserved_files": {},
                  "recovery_before": {name: None for name in proposed}, "completed_stages": [], "active_stage": "assets", "checks": [],
                  "created_at": "2026-09-09T00:00:00+00:00", "git_setup": "separate"}
        if contract in h.LICENSE_CONTRACTS:
            record["preserved_licenses"] = {}
        if contract in h.MEMORY_CONTRACTS:
            record["preserved_memory"] = {}
        if contract in h.LEARNING_CONTRACTS:
            record["preserved_learning"] = {}
        receipt = self.target / h.RECORD
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(h.encoded(record))
        first = self.run_setup()
        shutil.rmtree(template); backup.rename(template)
        return first

    def adopt(self, refresh=False):
        return self.run_setup(mode="prepare-existing", adopt_module="ontology", refresh_module=["ontology"] if refresh else [])

    def assert_base(self, first, after):
        for key in self.helper.BASE_IMMUTABLE:
            self.assertEqual(first.get(key), after.get(key), key)

    def test_v1_through_v7_require_selection_and_preserve_their_exact_base(self):
        for edition in range(1, 8):
            with self.subTest(edition=edition):
                if edition != 1:
                    self.setUp()
                first = self.historical(edition)
                repeated = self.run_setup()
                self.assert_base(first, repeated)
                self.assertFalse((self.target / "ontology.yaml").exists())
                protected = {name: digest for name, digest in fixture.manifest(self.target).items() if not name.startswith("control_records/project-setup")}
                after = self.adopt()
                self.assert_base(first, after)
                current = fixture.manifest(self.target)
                self.assertEqual(protected, {name: current[name] for name in protected})
                self.assertEqual("available", after["module_adoptions"][-1]["capabilities"]["structural_readiness"], after["module_adoptions"][-1]["capabilities"])
                self.assertEqual("current", after["module_adoptions"][-1]["capabilities"]["director_binding"])
                self.assertNotIn("preserved_ontology", after)
                repeat = self.adopt()
                self.assertEqual(1, len(repeat["module_adoptions"]))
                self.assert_base(first, repeat)

    def test_refresh_requires_unchanged_complete_ownership_and_retains_memory_settings(self):
        first = self.historical()
        config_path = self.target / "memory.yaml"
        config = json.loads(config_path.read_text()); config["integration"]["automatic_capture"] = False
        config["backend"]["enabled"] = True
        config_path.write_bytes(self.helper.encoded(config))
        memory_before = self.helper.memory_inventory(self.target)
        after = self.adopt()
        before = self.helper.ontology_inventory(self.target)
        source = self.root / self.helper.TEMPLATE / self.helper.ONTOLOGY_ROOT / "profile.md"
        source.write_bytes(source.read_bytes() + b"\nReviewed later documentation edition.\n")
        self.adopt()
        self.assertEqual(before, self.helper.ontology_inventory(self.target))
        refreshed = self.adopt(refresh=True)
        self.assert_base(first, refreshed)
        operation = refreshed["module_adoptions"][-1]
        self.assertEqual({"refreshed-owned-package"}, {x["decision"] for x in operation["packages"].values()})
        self.assertEqual(memory_before, self.helper.memory_inventory(self.target))
        self.assertEqual(source.read_bytes(), (self.target / self.helper.ONTOLOGY_ROOT / "profile.md").read_bytes())
        self.assertEqual(2, len(self.adopt(refresh=True)["module_adoptions"]))
        # A later source release and a missing project resource preserve all parts.
        source.write_bytes(source.read_bytes() + b"\nAnother reviewed edition.\n")
        (self.target / self.helper.ONTOLOGY_SKILL / "scripts/ontology_wiki.py").unlink()
        before = self.helper.ontology_inventory(self.target)
        with self.assertRaisesRegex(self.helper.InitializationError, "incomplete") as caught:
            self.adopt(refresh=True)
        preserved = caught.exception.report["module_adoptions"][-1]
        self.assertEqual(before, self.helper.ontology_inventory(self.target))
        self.assertEqual({"preserved-incompatible-refresh"}, {x["decision"] for x in preserved["packages"].values()})
        self.assertEqual("unavailable", preserved["capabilities"]["structural_readiness"])
        self.assertEqual("partial", preserved["status"])
        self.assertFalse(preserved["static_health"]["static_ready"])
        self.assertIn(self.helper.ONTOLOGY_SKILL + "/scripts/ontology_wiki.py", preserved["packages"]["ONTOLOGY"]["diagnostic"]["different_resources"])

    def test_custom_incomplete_group_preserves_all_parts_without_first_adoption_merge(self):
        self.historical()
        target = self.target / self.helper.ONTOLOGY_SKILL / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("Project custom ontology skill.\n")
        before = self.helper.ontology_inventory(self.target)
        with self.assertRaisesRegex(self.helper.InitializationError, "incomplete") as caught:
            self.adopt()
        after = caught.exception.report
        self.assertEqual(before, self.helper.ontology_inventory(self.target))
        self.assertFalse((self.target / "ontology.yaml").exists())
        self.assertEqual("unavailable", after["module_adoptions"][-1]["capabilities"]["structural_readiness"])
        self.assertEqual("partial", after["module_adoptions"][-1]["status"])
        self.assertFalse(after["static_ready"])
        saved = json.loads((self.target / self.helper.RECORD).read_text())
        self.assertEqual("completed", saved["status"])
        self.helper.validate_record(saved, self.target, saved["identity"])


if __name__ == "__main__":
    unittest.main()
