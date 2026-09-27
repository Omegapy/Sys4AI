"""A successful unittest process cannot conceal omitted or skipped obligations."""
import io
import unittest

from acceptance_runner import IdentityResult, assess, identities


class AcceptanceCoverageTests(unittest.TestCase):
    def run_case(self, methods, *, profile="core", selected=()):
        case = type("InjectedCoverage", (unittest.TestCase,), methods)
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
        found = list(identities(suite))
        result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=lambda *a, **k:
            IdentityResult(*a, discovered=found, **k)).run(suite)
        inventory = {"tests": [{"id": identity, "profile": profile} for identity in found],
                     "optional_skip_reasons": {"standards": ["Optional standards acceptance is unselected"]}}
        return assess(inventory, found, result.outcomes.values(), selected=selected,
                      setup_events=result.setup_events, unittest_exit=0 if result.wasSuccessful() else 1)

    def test_required_skip_fails_even_when_unittest_succeeds(self):
        def skipped(case):
            case.skipTest("Injected missing selected runtime")
        result = self.run_case({"test_required": skipped})
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(len(result["unexpected_required_skips"]), 1)

    def test_optional_skip_requires_an_unselected_named_profile_and_reason(self):
        def skipped(case):
            case.skipTest("Optional standards acceptance is unselected")
        methods = {"test_optional": skipped}
        result = self.run_case(methods, profile="standards")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(len(result["permitted_optional_skips"]), 1)
        self.assertEqual(result["counts"], {"skipped": 1})
        self.assertEqual(self.run_case(methods, profile="standards", selected=["standards"])["exit_code"], 1)
        def unexplained(case):
            case.skipTest("Some other coverage was not implemented")
        self.assertEqual(self.run_case({"test_optional": unexplained}, profile="standards")["exit_code"], 1)

    def test_setup_error_is_retained_for_each_unexecuted_identity(self):
        def broken(cls):
            raise RuntimeError("Injected setup error")
        result = self.run_case({"setUpClass": classmethod(broken), "test_one": lambda case: None,
                                "test_two": lambda case: None})
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["counts"], {"error": 2})
        self.assertIn("Injected setup error", result["setup_errors"][0]["detail"])

    def test_optional_class_skip_accounts_for_all_discovered_methods(self):
        def unavailable(cls):
            raise unittest.SkipTest("Optional standards acceptance is unselected")
        result = self.run_case({"setUpClass": classmethod(unavailable), "test_one": lambda case: None,
                                "test_two": lambda case: None}, profile="standards")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["counts"], {"skipped": 2})
        self.assertEqual(result["incomplete_identities"], [])

    def test_missing_duplicate_and_unclassified_skips_cannot_replace_baseline(self):
        inventory = {"tests": [{"id": "old.required", "profile": "core"}]}
        result = assess(inventory, ["new.case", "new.case"],
                        [{"id": "new.case", "outcome": "skipped", "detail": "Unclassified"}])
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["missing_identities"], ["old.required"])
        self.assertEqual(result["duplicate_identities"], ["new.case"])
        self.assertEqual(len(result["unexpected_required_skips"]), 1)

    def test_subtest_failure_is_retained_on_its_parent_identity(self):
        def failed(case):
            with case.subTest(selected="required"):
                case.fail("Injected subtest failure")
        result = self.run_case({"test_subtest": failed})
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["counts"], {"failure": 1})
        self.assertIn("Injected subtest failure", result["failed_outcomes"][0]["detail"])


if __name__ == "__main__":
    unittest.main()
