"""Setup completion and static capability readiness retain separate evidence."""
import json
import contextlib
import io
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_initializer as fixture
import test_advanced_ontology_adoption as advanced_fixture
import test_ontology_adoption as ontology_fixture


class StaticReadinessTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def test_new_manual_and_deep_space_preparation_report_static_only(self):
        first = self.run_setup()
        manual = self.root / "Projects/Manual Copy"
        shutil.copytree(self.root / self.helper.TEMPLATE, manual)
        reports = [first, self.run_setup(mode="prepare-existing", destination=manual, project_id="manual", project_name="Manual")]
        parent = self.root / "Projects/Deep Space/one/two"
        parent.mkdir(parents=True)
        reports.append(self.run_setup(destination=parent / "Prepared Project", project_id="deep-project", project_name="Deep project"))
        for report in reports:
            health = report["static_health"]
            self.assertTrue(report["static_ready"], health)
            self.assertEqual(report["aggregate"], "ready")
            self.assertEqual(health["assessment"]["level"], "static")
            self.assertEqual(health["runtime"], "not-exercised")
            self.assertFalse(health["unknown_target_code_executed"])
            self.assertFalse(health["provisioned"])
            self.assertTrue(all(item["outcome"] == "passed" for item in health["components"]))

    def test_current_source_inventory_rejects_missing_shipped_test_before_copy(self):
        template = self.root / self.helper.TEMPLATE
        for name in (".agents/skills/ontology/scripts/ontology_health.py", ".agents/skills/ontology/tests/acceptance_runner.py",
                     ".agents/skills/ontology/tests/guard_support.py"):
            target = template / name
            original = target.read_bytes()
            target.unlink()
            before = fixture.manifest(self.root)
            with self.subTest(path=name), self.assertRaisesRegex(self.helper.InitializationError, "capability"):
                self.helper.run_initialization(**self.arguments)
            self.assertEqual(fixture.manifest(self.root), before)
            target.write_bytes(original)
        lock = template / ".agents/skills/ontology/requirements-standards.txt"
        lock.write_bytes(lock.read_bytes() + b"\nunsupported-package==1.0\n")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "dependency lock"):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(fixture.manifest(self.root), before)

    def test_copy_success_with_invalid_adopted_test_is_partial_and_recoverable(self):
        original = self.helper.verify_project
        bad = self.target / ".agents/skills/ontology/tests/test_loading.py"
        saved = None
        def corrupt(destination, record, **kwargs):
            nonlocal saved
            result = original(destination, record, **kwargs)
            saved = bad.read_bytes()
            bad.write_text("def invalid Python(:\n")
            return result
        with patch.object(self.helper, "verify_project", side_effect=corrupt):
            with self.assertRaisesRegex(self.helper.InitializationError, "incomplete") as caught:
                self.helper.run_initialization(**self.arguments)
        partial = caught.exception.report
        self.assertEqual(partial["completed_stages"], ["assets", "registration"])
        self.assertEqual(partial["active_stage"], "verification")
        self.assertFalse(partial["static_ready"])
        self.assertIn("ontology", partial["static_health"]["required_failures"])
        bad.write_bytes(saved)
        recovered = self.run_setup()
        self.assertTrue(recovered["static_ready"])
        self.assertEqual(recovered["operation_id"], partial["operation_id"])
        self.assertEqual(recovered["sources"], partial["sources"])

    def test_preserved_custom_gap_retains_base_completion_and_no_readiness_claim(self):
        self.target.mkdir()
        owned = self.target / "ONTOLOGY/custom-format.txt"
        owned.parent.mkdir()
        owned.write_text("Preserve this project-owned ontology format.\n")
        report = self.run_setup(mode="prepare-existing")
        self.assertEqual(report["status"], "completed")
        self.assertFalse(report["static_ready"])
        self.assertEqual(report["aggregate"], "degraded")
        ontology = next(row for row in report["static_health"]["components"] if row["component"] == "ontology")
        self.assertFalse(ontology["required"])
        self.assertEqual(ontology["outcome"], "preserved-unverified")
        self.assertTrue(ontology["diagnostics"])
        self.assertEqual(owned.read_text(), "Preserve this project-owned ontology format.\n")
        self.helper.validate_record(report, self.target, report["identity"])
        with contextlib.redirect_stdout(io.StringIO()) as output:
            exit_code = self.helper.main(["prepare-existing", "--destination", str(self.target),
                "--project-id", self.arguments["project_id"], "--project-name", self.arguments["project_name"],
                "--purpose", self.arguments["purpose"]])
        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(output.getvalue())["status"], "completed")

    def test_disabled_publication_capture_off_and_valid_custom_sources_remain_unchanged(self):
        self.run_setup()
        for name in ("ontology.yaml", "ontology-advanced.yaml"):
            path = self.target / name
            value = json.loads(path.read_text())
            value["publication"] = {"enabled": False, "binding": None}
            path.write_bytes(self.helper.encoded(value))
        path = self.target / "memory.yaml"
        value = json.loads(path.read_text()); value["integration"]["automatic_capture"] = False
        path.write_bytes(self.helper.encoded(value))
        before = {name: (self.target / name).read_bytes() for name in ("ontology.yaml", "ontology-advanced.yaml", "memory.yaml")}
        report = self.run_setup()
        self.assertTrue(report["static_ready"], report["static_health"])
        self.assertEqual(report["memory_capture"]["status"], "off")
        self.assertEqual(before, {name: (self.target / name).read_bytes() for name in before})

    def test_unknown_copied_python_is_not_executed_and_earlier_receipt_stays_v8(self):
        first = advanced_fixture.AdvancedAdoptionTests.historical(self)
        path = self.target / ".agents/skills/ontology/scripts/ontology_core.py"
        path.write_bytes(path.read_bytes() + b"\nraise RuntimeError('never execute this copied project module')\n")
        original = path.read_bytes()
        report = self.run_setup()
        self.assertEqual(report["setup_contract"], "governance-starter-v8")
        self.assertEqual(first["owned_files"], report["owned_files"])
        self.assertEqual(original, path.read_bytes())
        self.assertFalse(report["static_health"]["unknown_target_code_executed"])
        self.assertFalse((self.target / "ontology-advanced.yaml").exists())

    def test_relocated_copy_has_local_static_evidence_but_cannot_replay_old_receipt(self):
        self.run_setup()
        relocated = self.root / "Projects/Relocated Project"
        shutil.copytree(self.target, relocated)
        before = fixture.manifest(relocated)
        with patch.object(self.helper.subprocess, "run", side_effect=AssertionError("static assessment has no subprocess")):
            current = self.helper.assess_ontology(relocated)
        self.assertEqual(current["structural_readiness"], "available", current)
        self.assertEqual(current["director_binding"], "current")
        with self.assertRaisesRegex(self.helper.InitializationError, "already registered at another path"):
            self.helper.run_initialization(**{**self.arguments, "destination": relocated, "mode": "prepare-existing"})
        self.assertEqual(before, fixture.manifest(relocated))

    def test_ordinary_rerun_checks_later_adoption_sources_without_rewriting_base(self):
        first = ontology_fixture.OntologyAdoptionTests.historical(self, 4)
        adopted = self.run_setup(mode="prepare-existing", adopt_module="ontology")
        path = self.target / ".agents/skills/ontology/tests/test_loading.py"
        original = path.read_bytes()
        path.write_text("def invalid syntax(:\n")
        with self.assertRaisesRegex(self.helper.InitializationError, "incomplete") as caught:
            self.helper.run_initialization(**self.arguments)
        result = caught.exception.report
        self.assertFalse(result["static_ready"])
        self.assertIn("ontology", result["static_health"]["required_failures"])
        component = next(row for row in result["static_health"]["components"] if row["component"] == "ontology")
        self.assertGreater(component["input_file_count"], 0)
        self.assertEqual(first["sources"], result["sources"])
        self.assertEqual(adopted["module_adoptions"][0]["manifest_sha256"], result["module_adoptions"][0]["manifest_sha256"])
        path.write_bytes(original)
        recovered = self.run_setup()
        self.assertTrue(recovered["static_ready"])
        self.assertEqual(first["setup_contract"], recovered["setup_contract"])

    def test_unknown_role_inspector_cannot_execute_or_overwrite_project_content(self):
        self.run_setup()
        helper = self.target / self.helper.ROLE_HELPER
        sentinel = self.target / "unknown-role-execution-sentinel.txt"
        original = helper.read_bytes()
        helper.write_bytes(original + ("\nfrom pathlib import Path\nPath(" + repr(str(sentinel)) + ").write_text('executed')\n").encode())
        altered = helper.read_bytes()
        before = {name: (self.target / name).read_bytes() for name in ("AGENTS.md", "ROLE.md", "SOUL.md")}
        with self.assertRaisesRegex(self.helper.InitializationError, "unknown role inspector"):
            self.helper.planned_role_index(self.target, {}, {})
        self.assertFalse(sentinel.exists())
        self.assertEqual(altered, helper.read_bytes())
        self.assertEqual(before, {name: (self.target / name).read_bytes() for name in before})
        for role_root, expected in self.helper.ROLE_INSPECTOR_SHA256.items():
            selected = original.replace(b'ROLE_ROOT_NAME = "Roles"', ('ROLE_ROOT_NAME = "' + role_root + '"').encode())
            self.assertEqual(self.helper.sha(selected), expected)
            with self.helper.role_validator(selected, role_root=role_root) as verified:
                self.assertEqual(verified.ROLE_ROOT_NAME, role_root)


if __name__ == "__main__":
    unittest.main()
