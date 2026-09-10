"""Run installed guard tests with a verification-local fixture root correction.

No source file is changed. DEPOT is rebound before decorators/imports, and
fixture adapters explicitly come from the installed root through the supported
environment selector. Synthetic native receipts remain fixture evidence.
"""
from pathlib import Path
import json
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
os.environ["SYS4AI_GUARD_INSTALLED_ROOT"] = str(ROOT)
sys.path.insert(0, str(ROOT / ".agents/skills/ontology/tests"))
import guard_support

original_root = guard_support.DEPOT
guard_support.DEPOT = ROOT
names = ["test_guard_engine", "test_guarded_dispatch", "test_guard_recovery",
         "test_guard_deadline", "test_guard_profiles", "test_action_semantics"]
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
summary = {"test_modules": names, "fixture_root_original": str(original_root),
           "fixture_root_selected": str(ROOT), "installed_adapter_root": str(ROOT),
           "tests_run": result.testsRun, "skipped": [(test.id(), reason) for test, reason in result.skipped],
           "failures": [(test.id(), trace) for test, trace in result.failures],
           "errors": [(test.id(), trace) for test, trace in result.errors],
           "successful": result.wasSuccessful()}
(OUT / "selected-guard-result.json").write_text(json.dumps(summary, indent=2) + "\n")
sys.exit(0 if result.wasSuccessful() else 1)
