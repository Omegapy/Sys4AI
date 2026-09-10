"""Shared decision deadlines: actual workers and explicit clock-controlled cases."""
import importlib
import inspect
import json
import os
from pathlib import Path
import time
import types
import unittest
from unittest.mock import patch

from guard_support import DEPOT, canonical_snapshot, preserve_imports
import test_action_semantics as action_tests


@unittest.skipUnless((DEPOT / ".venv-ontology-standards/certification.json").is_file(), "Selected real backend is unavailable")
class GuardDeadlineTests(unittest.TestCase):
    observations = []

    def setUp(self):
        preserve_imports(self)
        self.factory = action_tests.ActionSemanticsTests()
        self.addCleanup(self.factory.doCleanups)

    @classmethod
    def tearDownClass(cls):
        selected = os.environ.get("SYS4AI_GUARD_DEADLINE_EVIDENCE")
        if selected:
            Path(selected).write_text(json.dumps({"schema_version": 1, "status": "passed" if len(cls.observations) == 4 else "incomplete",
                "observations": cls.observations, "limits": "The existing worker supervisor polls the shared deadline. Synchronous filesystem/preparation calls are checked at phase boundaries; a late result cannot be conformant or dispatch an owner."}, indent=2) + "\n")

    def test_all_v2_backend_phases_share_one_remaining_budget(self):
        root, owner, proposal = self.factory.extension_candidate()
        guards = importlib.import_module("ontology_guards")
        standards = importlib.import_module("ontology_standards")
        calls = []
        def wrap(name):
            actual = getattr(standards, name)
            def observe(*args, **kwargs):
                calls.append({"phase": name, "limits": kwargs.get("limits"), "cancel": kwargs.get("cancel")})
                return actual(*args, **kwargs)
            return observe
        before = canonical_snapshot(root, "ONTOLOGY")
        with patch.object(standards, "validate", wrap("validate")), patch.object(standards, "infer", wrap("infer")), patch.object(standards, "dataset", wrap("dataset")):
            decision = guards.begin_action(root, "ontology", "publish", {"proposal": proposal}, [c["path"] for c in proposal["changes"]])
        self.assertEqual([c["phase"] for c in calls], ["dataset", "validate", "infer", "validate"])
        self.assertEqual(len({id(c["cancel"]) for c in calls}), 1)
        self.assertTrue(all(c["cancel"] is not None and max(c["limits"].values()) <= 5 for c in calls))
        self.assertLess(decision.evaluation_seconds, 5)
        self.assertEqual(before, canonical_snapshot(root, "ONTOLOGY"))
        self.observations.append({"case": "actual_v2_phases", "phase_limits": [{k: v for k, v in c.items() if k != "cancel"} for c in calls],
            "shared_cancel_object": True, "elapsed_seconds": decision.evaluation_seconds, "budget_seconds": 5, "canonical_unchanged": True})

    def test_actual_worker_is_cancelled_at_selected_shared_deadline(self):
        root, _, _, _, _, _ = self.factory.fixture("trd")
        guards = importlib.import_module("ontology_guards")
        standards = importlib.import_module("ontology_standards")
        cfg_path = root / "ontology-advanced.yaml"
        cfg = json.loads(cfg_path.read_text()); cfg["limits"]["guard_seconds"] = 1
        cfg_path.write_text(json.dumps(cfg))
        budget = guards._GuardBudget(root)
        observed = []
        def actual(*args, **kwargs):
            result = standards.call(*args, **kwargs); observed.append(result); return result
        started = time.monotonic()
        with self.assertRaises(guards.GuardError) as rejected:
            budget.evaluate(actual, root, "probe_timeout")
        elapsed = time.monotonic() - started
        self.assertEqual(rejected.exception.code, "guard_timeout")
        self.assertEqual(observed[0]["status"], "cancelled")
        self.assertFalse(observed[0]["complete"])
        self.assertLess(elapsed, 2)
        self.observations.append({"case": "actual_worker_deadline", "budget_seconds": 1, "elapsed_seconds": elapsed,
            "backend_status": observed[0]["status"], "complete": False, "worker": observed[0]["worker"]})

    def test_late_conformant_result_never_invokes_owner(self):
        root, owner, _, target, call, _ = self.factory.fixture("trd")
        guards = importlib.import_module("ontology_guards")
        standards = importlib.import_module("ontology_standards")
        current = [0.0]
        budget_class = guards._GuardBudget
        budget = budget_class(root, clock=lambda: current[0])
        actual_validate = standards.validate
        def late(*args, **kwargs):
            result = actual_validate(*args, **kwargs)
            self.assertEqual(result["status"], "conformant")
            current[0] = 5.01
            return result
        invoked = []
        actual_dispatch = guards.dispatch
        def observed_dispatch(function, *args, **kwargs):
            def continuation():
                invoked.append(True); return function()
            actual_namespace = types.FunctionType(continuation.__code__, function.__globals__, closure=continuation.__closure__)
            return actual_dispatch(actual_namespace, *args, **kwargs)
        before = canonical_snapshot(root, target)
        with patch.object(guards, "_GuardBudget", return_value=budget), patch.object(guards, "dispatch", observed_dispatch), patch.object(standards, "validate", late):
            with self.assertRaises(Exception) as rejected:
                call()
        self.assertIn("guard_timeout", str(rejected.exception))
        self.assertFalse(invoked)
        self.assertEqual(before, canonical_snapshot(root, target))
        self.observations.append({"case": "late_conformant_result", "backend": "actual selected standards",
            "clock": "explicit test-controlled deadline advance, not a wall-time measurement", "owner_invoked": False, "canonical_unchanged": True})

    def test_equivalent_previews_keep_the_same_review_hash(self):
        root, owner, _, _, call, _ = self.factory.fixture("ontology")
        payload = inspect.getclosurevars(call).nonlocals["payload"]
        first = owner.preview(root, payload)
        second = owner.preview(root, payload)
        self.assertEqual(first["preview_sha256"], second["preview_sha256"])
        self.assertNotIn("evaluation_seconds", first["ontology_guard"])
        self.assertEqual(first["ontology_guard"]["evaluation_budget_seconds"], 5)
        self.observations.append({"case": "stable_review_identity", "backend": "actual selected standards",
            "matching_preview_sha256": first["preview_sha256"], "nondeterministic_elapsed_time_excluded": True})


if __name__ == "__main__":
    unittest.main()
