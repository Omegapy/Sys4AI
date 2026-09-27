"""Identity-based unittest acceptance; optional selection never provisions a runtime.

Run the ordinary unittest command for development. For release evidence, supply
the reviewed inventory and an output receipt; --select standards/semantic makes
every identity in that optional profile required. Unlisted new tests are required.
"""
from __future__ import annotations

import argparse
from collections import Counter
import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import unittest


def identities(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from identities(item)
        else:
            yield item.id()


class IdentityResult(unittest.TextTestResult):
    def __init__(self, *args, discovered=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.discovered = list(discovered)
        self.outcomes = {}
        self.setup_events = []

    def record(self, test, outcome, detail=""):
        identity = test.id()
        holder = re.fullmatch(r"(setUpClass|tearDownClass|setUpModule|tearDownModule) \((.+)\)", identity)
        if holder:
            self.setup_events.append({"id": identity, "outcome": outcome, "detail": detail})
            for selected in self.discovered:
                if selected.startswith(holder[2] + "."):
                    self.outcomes[selected] = {"id": selected, "outcome": outcome,
                                               "detail": detail, "fixture_event": identity}
        else:
            self.outcomes[identity] = {"id": identity, "outcome": outcome, "detail": detail}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, "passed")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, "skipped", reason)

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, "error", self._exc_info_to_string(err, test))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, "failure", self._exc_info_to_string(err, test))

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            outcome = "failure" if issubclass(err[0], test.failureException) else "error"
            previous = self.outcomes.get(test.id(), {}).get("detail", "")
            self.record(test, outcome, previous + subtest.id() + "\n" + self._exc_info_to_string(err, subtest))

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.record(test, "expected_failure", self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.record(test, "unexpected_success")


def assess(inventory, discovered, outcomes, *, selected=(), setup_events=(), unittest_exit=0):
    """Compare exact identities, retaining baseline obligations after additions."""
    expected = {row["id"]: row for row in inventory["tests"]}
    profiles = {"core", *selected}
    discovered = list(discovered)
    found = set(discovered)
    rows = {row["id"]: row for row in outcomes}
    permitted_reasons = inventory.get("optional_skip_reasons", {})
    missing = sorted(set(expected) - found)
    duplicates = sorted(identity for identity, count in Counter(discovered).items() if count > 1)
    required_skips, optional_skips, incomplete = [], [], []
    for identity in sorted(found):
        result = rows.get(identity)
        profile = expected.get(identity, {}).get("profile", "core")
        if result is None:
            incomplete.append(identity)
        elif result["outcome"] == "skipped":
            if (profile in {"standards", "semantic"} and profile not in profiles
                    and result.get("detail") in permitted_reasons.get(profile, [])):
                optional_skips.append({**result, "profile": profile,
                                       "acceptance": "optional profile unselected; behavior not exercised"})
            else:
                required_skips.append(result)
    bad = [row for row in rows.values() if row["outcome"] not in {"passed", "skipped"}]
    setup_errors = [row for row in setup_events if row["outcome"] != "skipped"]
    invalid_inventory = len(expected) != len(inventory["tests"])
    successful = not (missing or duplicates or required_skips or incomplete or bad or setup_errors
                      or unittest_exit or invalid_inventory)
    return {"status": "passed" if successful else "failed", "exit_code": 0 if successful else 1,
            "selected_profiles": sorted(profiles), "inventory_count": len(expected),
            "discovered_count": len(discovered), "counts": dict(Counter(row["outcome"] for row in rows.values())),
            "missing_identities": missing, "duplicate_identities": duplicates,
            "duplicate_inventory_identities": invalid_inventory,
            "new_identities": sorted(found - set(expected)), "incomplete_identities": incomplete,
            "unexpected_required_skips": required_skips, "permitted_optional_skips": optional_skips,
            "failed_outcomes": bad, "setup_errors": setup_errors,
            "tests": [rows[key] for key in sorted(rows)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--tests-dir", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--select", action="append", default=[], choices=("standards", "semantic"))
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    clock_start = time.monotonic()
    inventory_path = Path(args.inventory).resolve()
    receipt = Path(args.receipt).resolve()
    tests_dir = Path(args.tests_dir).resolve()
    receipt.parent.mkdir(parents=True, exist_ok=True)
    inventory_bytes = inventory_path.read_bytes()
    inventory = json.loads(inventory_bytes)
    sys.path.insert(0, str(tests_dir))
    discovered, outcomes, setup_events, selection_errors = [], [], [], []
    context, runtime = {}, {}
    stdout_path, stderr_path = receipt.with_suffix(".stdout.log"), receipt.with_suffix(".stderr.log")
    with stdout_path.open("w") as out, stderr_path.open("w") as err:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                from support import fixture_context, standards_environment, semantic_acceptance_root
                context = {key: str(value) for key, value in fixture_context(tests_dir.parent).items()}
                standards = standards_environment()
                semantic = semantic_acceptance_root()
                runtime = {"standards_environment": str(standards) if standards else None,
                           "semantic_acceptance_root": str(semantic) if semantic else None}
                for name, value in (("standards", standards), ("semantic", semantic)):
                    if name in args.select and value is None:
                        selection_errors.append("Required " + name + " acceptance has no selected existing runtime.")
                if standards:
                    runtime["standards_certificate_sha256"] = hashlib.sha256((standards / "certification.json").read_bytes()).hexdigest()
                suite = unittest.defaultTestLoader.discover(str(tests_dir), pattern="test_*.py")
                discovered = list(identities(suite))
                factory = lambda *a, **kw: IdentityResult(*a, discovered=discovered, **kw)
                result = unittest.TextTestRunner(stream=err, verbosity=2, resultclass=factory).run(suite)
                outcomes, setup_events = list(result.outcomes.values()), result.setup_events
                unittest_exit = 0 if result.wasSuccessful() else 1
                tests_run = result.testsRun
            except Exception:
                detail = traceback.format_exc()
                err.write(detail)
                setup_events.append({"id": "acceptance_setup", "outcome": "error", "detail": detail})
                unittest_exit, tests_run = 1, 0
    report = assess(inventory, discovered, outcomes, selected=args.select,
                    setup_events=setup_events, unittest_exit=unittest_exit)
    if selection_errors:
        report.update(status="failed", exit_code=1)
    report.update(schema_version=1, command=[sys.executable, *sys.argv], cwd=str(Path.cwd().resolve()),
                  started_at=started, ended_at=datetime.now(timezone.utc).isoformat(),
                  duration_seconds=time.monotonic() - clock_start, context=context,
                  python={"executable": sys.executable, "version": sys.version}, runtime=runtime,
                  environment_selection={key: os.environ.get(key) for key in (
                      "SYS4AI_STANDARDS_PYTHON", "SYS4AI_SEMANTIC_ACCEPTANCE_ROOT",
                      "SYS4AI_TEST_DEPOT_ROOT", "SYS4AI_GUARD_INSTALLED_ROOT")},
                  inventory={"path": str(inventory_path), "sha256": hashlib.sha256(inventory_bytes).hexdigest()},
                  tests_directory=str(tests_dir), tests_run=tests_run, unittest_exit_code=unittest_exit,
                  selection_errors=selection_errors, stdout=str(stdout_path), stderr=str(stderr_path),
                  discovered_identities=discovered)
    receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "counts": report["counts"], "receipt": str(receipt)}))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
