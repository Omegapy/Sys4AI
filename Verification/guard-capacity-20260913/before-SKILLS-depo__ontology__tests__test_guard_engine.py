"""Guard decision unit regressions; mocked backend cases are not acceptance."""
import copy
import importlib
import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch

from guard_support import project, fixture_selection, load, preserve_imports
from ontology_guards import GuardError, begin_action, digest
from support import write_json


class GuardEngineTests(unittest.TestCase):
    def setUp(self):
        preserve_imports(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = project(Path(self.temp.name), backend=False)
        self.guards = importlib.import_module("ontology_guards")

    def begin(self, root, family, operation, arguments, targets):
        # These are mocked decision-unit observations, never dispatch acceptance.
        return self.guards.begin_action(root, family, operation, arguments, targets,
            _observed={"input_type": family + "-" + operation + "-request",
                       "input_valid": True, "requested_paths": list(targets)})

    def conformant(self):
        return patch("ontology_standards.validate", return_value={"status": "conformant", "complete": True, "context": {"test": "mocked-unit-only"}})

    def test_disabled_profile_imports_no_optional_backend(self):
        write_json(self.root / "ontology-advanced.yaml", {"schema_version": 1, "profiles": {"guards": {"enabled": False}}, "extensions": [], "limits": {}})
        with patch("ontology_standards.validate", side_effect=AssertionError("must not call backend")):
            result = self.begin(self.root, "trd", "create", {}, ["TRDs"]).finish({"ok": True})
        self.assertEqual(result, {"ok": True})

    def test_each_unknown_or_failed_backend_result_is_closed(self):
        for status in ("violation", "unsupported_feature", "processing_failure", "unavailable", "timeout", "ambiguous", "stale_input"):
            with self.subTest(status=status), patch("ontology_standards.validate", return_value={"status": status, "complete": False}):
                with self.assertRaises(self.guards.GuardError):
                    self.begin(self.root, "trd", "create", {"payload": {}}, ["TRDs"])

    def test_malformed_backend_diagnostics_retain_bounded_failure_text(self):
        for findings, diagnostics in ((None, None), ({"unsafe": "not a list"}, 4), ([None, 7, {"value": "DO_NOT_ECHO_DATA"}], "invalid")):
            error = self.guards.GuardError("guard_processing_failure", "Validation did not complete.", {
                "action_id": "urn:sys4ai:ontology:action:role:reindex",
                "contract": {"path": "reference-assets/ONTOLOGY-depo/actions/contracts-v1.json", "sha256": "a" * 64},
                "backend": {"status": "unknown", "findings": findings, "diagnostics": diagnostics}})
            message = str(error)
            self.assertIn("action=urn:sys4ai:ontology:action:role:reindex", message)
            self.assertIn("condition=guard_processing_failure", message)
            self.assertNotIn("DO_NOT_ECHO_DATA", message)
            self.assertLessEqual(len(message), 1200)
        with patch("ontology_standards.validate", return_value={"status": {"private": "DO_NOT_ECHO_DATA"}, "complete": False}):
            with self.assertRaises(self.guards.GuardError) as rejected:
                self.begin(self.root, "trd", "create", {}, ["TRDs"])
        self.assertEqual(rejected.exception.code, "guard_processing_failure")
        self.assertNotIn("DO_NOT_ECHO_DATA", str(rejected.exception))

    def test_argument_target_rule_and_authority_changes_invalidate_pass(self):
        with self.conformant():
            request = {"payload": {"title": "One"}}
            decision = self.begin(self.root, "trd", "create", request, ["TRDs"])
            request["payload"]["title"] = "Two"
            with self.assertRaises(self.guards.GuardError): decision.recheck()
            decision = self.begin(self.root, "trd", "create", {}, ["TRDs"])
            (self.root / "TRDs").mkdir()
            (self.root / "TRDs/changed.md").write_text("A concurrent target change")
            with self.assertRaises(self.guards.GuardError): decision.recheck()
            decision = self.begin(self.root, "trd", "create", {}, ["TRDs"])
            (self.root / "SOUL.md").write_text("Current authority changed")
            with self.assertRaises(self.guards.GuardError): decision.recheck(targets=False)
            decision = self.begin(self.root, "trd", "create", {}, ["TRDs"])
            path = self.root / "reference-assets/ONTOLOGY-depo/actions/action-shapes-v1.ttl"
            path.write_text(path.read_text() + "\n# Changed reviewed rules\n")
            with self.assertRaises(self.guards.GuardError): decision.recheck(targets=False)

    def test_missing_duplicate_stale_and_unsupported_bindings_fail_closed(self):
        with self.conformant():
            with self.assertRaises(self.guards.GuardError): self.begin(self.root, "trd", "create", {}, ["TRDs", "TRDs"])
            with self.assertRaises(self.guards.GuardError): self.begin(self.root, "trd", "unknown", {}, [])
            source = self.root / ".agents/skills/to-trd/scripts/trd.py"
            source.write_text(source.read_text() + "\n# changed helper\n")
            with self.assertRaises(self.guards.GuardError): self.begin(self.root, "trd", "create", {}, ["TRDs"])

    def test_selected_own_post_targets_do_not_invalidate_other_sources(self):
        target = "ONTOLOGY/modules/project/project.jsonld"
        with self.conformant():
            decision = self.begin(self.root, "ontology", "publish", {}, [target])
            (self.root / target).write_text((self.root / target).read_text() + "\n")
            decision.recheck(targets=False)
            with self.assertRaises(self.guards.GuardError): decision.recheck(targets=True)

    def test_loaded_engine_and_manager_generation_cannot_change_after_check(self):
        with self.conformant():
            task = self.root / "Tasks/Task-fixture/task.json"
            task.parent.mkdir(parents=True)
            task.write_text('{"generation": 1}')
            decision = self.begin(self.root, "memory", "transact", {}, ["MEMORY"])
            task.write_text('{"generation": 2}')
            with self.assertRaises(self.guards.GuardError): decision.recheck(targets=False)
            decision = self.begin(self.root, "trd", "create", {}, ["TRDs"])
            engine = self.root / ".agents/skills/ontology/scripts/ontology_guards.py"
            engine.write_bytes(engine.read_bytes() + b"\n# changed loaded code\n")
            with self.assertRaises(self.guards.GuardError): decision.recheck(targets=False)

    def test_actual_owner_rejects_cached_other_project_engine_and_duplicate_config(self):
        previous = self.guards
        second_temp = tempfile.TemporaryDirectory()
        self.addCleanup(second_temp.cleanup)
        second = project(Path(second_temp.name), backend=False)
        owner = load(second / ".agents/skills/to-trd/scripts/trd.py", "guard_cross_project_trd")
        payload = json.loads((second / ".agents/skills/to-trd/assets/example-input.json").read_text())
        current_module = sys.modules["ontology_guards"]
        try:
            sys.modules["ontology_guards"] = previous
            with self.assertRaises(owner.TrdError) as caught:
                owner.Store(second).create(payload)
            self.assertIn("Loaded guard code differs", str(caught.exception))
            self.assertFalse((second / "TRDs").exists())
            (second / "ontology-advanced.yaml").write_text('{"schema_version":1,"profiles":{"guards":{"enabled":true,"enabled":false}}}')
            with self.assertRaises(owner.TrdError): owner.Store(second).create(payload)
            self.assertFalse((second / "TRDs").exists())
            write_json(second / "ontology-advanced.yaml", {"schema_version": 1, "profiles": {"guards": {"enabled": False}}, "extensions": [], "limits": {}})
            result = owner.Store(second).create(payload)
            self.assertNotIn("ontology_guard", result)
            self.assertTrue((second / result["document"]["path"]).is_file())
        finally:
            sys.modules["ontology_guards"] = current_module

    def test_inline_file_envelopes_are_not_paths_and_bad_paths_are_bounded(self):
        private_payload = "INLINE-CONTENT-SENTINEL" * 4000
        request = {"files": {".agents/skills/ontology/scripts/ontology_profiles.py": private_payload, "input": private_payload, "path": private_payload},
                   "before_content": private_payload,
                   "nested": {"content_base64": private_payload, "bytes_sha256": "a" * 64}}
        with self.conformant():
            decision = self.begin(self.root, "setup", "run_module_adoption", request, [])
            decision.recheck()
        with self.assertRaises(self.guards.GuardError) as rejected:
            self.guards._argument_paths(self.root, {"input_file": private_payload})
        self.assertEqual(rejected.exception.code, "guard_invalid_path")
        self.assertNotIn("INLINE-CONTENT-SENTINEL", str(rejected.exception))
        self.assertNotIn("INLINE-CONTENT-SENTINEL", str(rejected.exception.details))
        self.assertLess(len(str(rejected.exception)) + len(str(rejected.exception.details)), 300)


if __name__ == "__main__":
    unittest.main()
