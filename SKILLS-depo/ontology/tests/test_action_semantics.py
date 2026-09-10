"""Typed action regressions with the delivered rules and actual pySHACL.

Native grant records are explicitly synthetic disposable test receipts. No
test here supplies actor authority or modifies a selected installed project.
"""
import argparse
import copy
import importlib
import inspect
import json
import sys
import types
from pathlib import Path
import unittest
from unittest.mock import patch

from guard_support import standards_available, helper_path, DEPOT, fixture_selection, canonical_snapshot, preserve_imports, project
from support import write_json, grant
import test_guarded_dispatch as dispatch_tests


@unittest.skipUnless(standards_available(), "Selected real backend is unavailable")
class ActionSemanticsTests(unittest.TestCase):
    def test_candidate_validation_includes_external_authored_metadata(self):
        from support import add_records, record
        root, owner, proposal = self.extension_candidate()
        add_records(root, [record("external-artifact", fact_kind="external")])
        guards = importlib.import_module("ontology_guards")
        before = canonical_snapshot(root, "ONTOLOGY")
        decision = guards.begin_action(root, "ontology", "publish", {"proposal": proposal},
                                       [row["path"] for row in proposal["changes"]])
        self.assertEqual(decision.backend["status"], "conformant")
        self.assertTrue(decision.backend["complete"])
        self.assertEqual(before, canonical_snapshot(root, "ONTOLOGY"))

    def setUp(self):
        preserve_imports(self)

    def fixture(self, family):
        factory = dispatch_tests.GuardedDispatchTests()
        self.addCleanup(factory.doCleanups)
        return factory.fixtures(family)

    def rejected_by_backend(self, root, call, target):
        backend = importlib.import_module("ontology_standards")
        actual = backend.validate
        results = []
        invoked = []
        guards = importlib.import_module("ontology_guards")
        actual_dispatch = guards.dispatch
        def dispatch(function, *args, **kwargs):
            def continuation():
                invoked.append(True)
                return function()
            return actual_dispatch(types.FunctionType(continuation.__code__, function.__globals__, closure=continuation.__closure__), *args, **kwargs)
        def observe(*args, **kwargs):
            result = actual(*args, **kwargs)
            results.append(result)
            return result
        before = canonical_snapshot(root, target)
        with patch.object(backend, "validate", observe), patch.object(guards, "dispatch", dispatch):
            with self.assertRaises(Exception):
                call()
        self.assertEqual([(r["status"], r["complete"]) for r in results], [("violation", True)])
        self.assertTrue(results[0]["findings"])
        self.assertEqual(invoked, [])
        self.assertEqual(canonical_snapshot(root, target), before)
        return results[0]

    def test_caller_forged_task_state_is_not_current_evidence(self):
        root, owner, operation, target, call, _ = self.fixture("task")
        guards = importlib.import_module("ontology_guards")
        with self.assertRaises(guards.GuardError) as rejected:
            guards.begin_action(root, "task", "response_transaction", {"_semantic_state": {
                "currentState": "completed", "nextState": "not-a-task-state",
                "targetIdentity": "urn:sys4ai:ontology:core:Artifact", "targetRevision": -1}},
                ["ONTOLOGY/modules/project/project.jsonld"])
        self.assertEqual(rejected.exception.code, "guard_missing_evidence")
        self.assertFalse(next((root / "Tasks").glob("*/task.json"), None))

    def test_real_task_trd_and_plan_lifecycle_values_are_constrained(self):
        for family in ("task", "trd", "plan"):
            with self.subTest(family=family):
                root, owner, operation, target, call, _ = self.fixture(family)
                call()
                if family == "task":
                    state = json.loads(next((root / "Tasks").glob("*/task.json")).read_text())
                    payload = {"work_completed": ["Read current state."], "verification_evidence": ["Actual fixture Task."],
                        "user_response_summary": "Reject impossible transition.", "current_summary": "Current fixture.", "next_step": None,
                        "blockers": [], "open_questions": [], "relevant_files": [], "status_after": "not-a-task-state"}
                    invalid = lambda: owner.response_transaction("respond", root, root / "Tasks", state["task_id"], state["revision"], payload)
                elif family == "trd":
                    store = owner.Store(root); selected = store.read()[0][0]
                    invalid = lambda: store.set_status(selected.meta["trd_id"], selected.sha256, "completed", "Invalid TRD lifecycle value.", True)
                else:
                    context = owner.resolve_context(str(root), "Implementation_Plans")
                    selected = owner.discover_managed_plans(context)[0][0]
                    args = argparse.Namespace(selector=selected.plan["plan_id"], expected_revision=selected.plan["revision"],
                        expected_sha256=selected.sha256, status_value="completed", reason="Cannot complete directly from draft.", confirmed=True)
                    invalid = lambda: owner.handle_set_status(context, args)
                result = self.rejected_by_backend(root, invalid, target)
                self.assertTrue(any(row.get("path", "").endswith("nextState") for row in result["findings"]))

    def test_concrete_capability_is_observed_from_the_provider_for_every_family(self):
        for family in ("ontology", "memory", "task", "trd", "plan", "role", "template", "setup"):
            with self.subTest(family=family):
                root, owner, operation, target, call, _ = self.fixture(family)
                path = root / "reference-assets/ONTOLOGY-depo/actions/contracts-v1.json"
                contract = json.loads(path.read_text())
                selected = next(row for row in contract["actions"] if row["family"] == family and row["operation"] == operation)
                selected["capability"] = "urn:sys4ai:ontology:action:capability:" + ("MemoryMaintenance" if family != "memory" else "TaskLifecycleManagement")
                fixture_selection(root, contract=contract)
                result = self.rejected_by_backend(root, call, target)
                self.assertTrue(any(row.get("path", "").endswith("requiredCapability") for row in result["findings"]))

    def test_current_task_orchestration_generation_is_read_before_dispatch(self):
        root, owner, operation, target, call, _ = self.fixture("task")
        inspect.getclosurevars(call).nonlocals["payload"]["orchestration_enabled"] = True
        call()
        state = json.loads(next((root / "Tasks").glob("*/task.json")).read_text())
        response = {"work_completed": ["Read current Task."], "verification_evidence": ["Actual current generation."],
            "user_response_summary": "Reject stale orchestration.", "current_summary": "Fixture current state.",
            "next_step": None, "blockers": [], "open_questions": [], "relevant_files": []}
        event = {"event_id": "GUARD_STALE_GENERATION", "actor": "/root", "execution_id": "WRONG_EXECUTION",
            "generation": state["orchestration"]["generation"] + 1, "kind": "block", "data": {"reason": "Fixture blocking event.", "next_step": "Inspect current generation."}}
        invalid = lambda: owner.response_transaction("orchestrate", root, root / "Tasks", state["task_id"], state["revision"], {"event": event, "response": response})
        self.rejected_by_backend(root, invalid, target)

    def test_actual_plan_cli_revision_fields_and_nested_transaction_succeed(self):
        root, owner, operation, target, call, _ = self.fixture("plan")
        call()
        context = owner.resolve_context(str(root), "Implementation_Plans")
        selected = owner.discover_managed_plans(context)[0][0]
        args = argparse.Namespace(selector=selected.plan["plan_id"], expect_revision=selected.plan["revision"],
            expect_sha256=selected.sha256, status_value="cancelled", reason="Cancel the isolated guard acceptance plan.", confirmed=True)
        result = owner.handle_set_status(context, args)[0]
        self.assertEqual(result["ontology_guard"]["semantic_status"], "conformant")
        self.assertEqual(owner.select_plan(context, selected.plan["plan_id"]).plan["status"], "cancelled")

    def test_guarded_populated_v8_adoption_retains_its_receipt_and_authored_files(self):
        sys.path.insert(0, str(helper_path("SKILLS-depo/init-new-project/tests")))
        module = dispatch_tests.helper_fixture("advanced_adoption", "SKILLS-depo/init-new-project/tests/test_advanced_ontology_adoption.py")
        case = module.AdvancedAdoptionTests()
        self.addCleanup(case.doCleanups)
        case.setUp()
        first = case.historical()
        case.populate()
        protected = {name: canonical_snapshot(case.target, name) for name in ("ONTOLOGY", "MEMORY", "control_records/ontology", "ontology.yaml", "memory.yaml")}
        project(case.root)
        result = case.adopt()
        self.assertEqual(result["ontology_guard"]["semantic_status"], "conformant")
        case.assert_base(first, result)
        self.assertEqual(result["module_adoptions"][-1]["module_id"], "ontology-advanced")
        self.assertEqual({name: canonical_snapshot(case.target, name) for name in protected}, protected)

    def test_missing_governing_source_and_unrecognized_rules_cannot_pass(self):
        root, owner, operation, target, call, _ = self.fixture("trd")
        (root / "SOUL.md").unlink()
        result = self.rejected_by_backend(root, call, target)
        self.assertTrue(any("governingSource" in row.get("path", "") for row in result["findings"]))
        guards = importlib.import_module("ontology_guards")
        contract = json.loads((root / "reference-assets/ONTOLOGY-depo/actions/contracts-v1.json").read_text())
        for field, value in (("semantic_rules", ["execute-python"]), ("capability", "urn:sys4ai:ontology:core:Capability"), ("lifecycle", "arbitrary-graph")):
            malformed = copy.deepcopy(contract)
            malformed["actions"][0][field] = value
            with self.subTest(field=field), self.assertRaises(guards.GuardError) as rejected:
                guards.validate_contract(malformed)
            self.assertEqual(rejected.exception.code, "guard_unsupported")

    def test_real_role_and_ontology_errors_retain_safe_action_and_version_text(self):
        for family in ("role", "ontology"):
            with self.subTest(family=family):
                root, owner, operation, target, call, _ = self.fixture(family)
                factory = dispatch_tests.GuardedDispatchTests()
                invalid, restore, _ = factory.natural_invalid(family, root, owner, call)
                try:
                    with self.assertRaises(Exception) as rejected:
                        invalid()
                    text = str(rejected.exception)
                    contract = json.loads((root / "ontology-advanced.yaml").read_text())["profiles"]["guards"]["contract"]
                    self.assertIn("action=urn:sys4ai:ontology:action:" + family + ":" + operation, text)
                    self.assertIn(contract["path"] + "@" + contract["sha256"], text)
                    self.assertIn("condition=guard_violation", text)
                    self.assertIn("backend=violation", text)
                    self.assertIn("findings=", text)
                    self.assertLess(len(text), 1100)
                finally:
                    restore()

    def extension_candidate(self):
        from advanced_support import extension, statement, project_id
        from ontology_core import canonical_bytes, sha256
        from ontology_advanced import RDF, RDFS
        root, owner, _, target, _, _ = self.fixture("ontology")
        shape_path = "ONTOLOGY/extensions/constraints.ttl"
        shape = '@prefix sh:<http://www.w3.org/ns/shacl#>. <urn:fixture:shape> a sh:NodeShape; sh:targetNode <' + project_id("subject") + '>; sh:property [sh:path <' + RDFS + 'label>; sh:minCount 0].'
        (root / shape_path).parent.mkdir(parents=True, exist_ok=True)
        (root / shape_path).write_text(shape)
        ext = extension(root)
        ext["shapes"] = [{"path": shape_path, "sha256": sha256(root / shape_path)}]
        ext_path = "ONTOLOGY/extensions/semantics.json"
        write_json(root / ext_path, ext)
        cfg = json.loads((root / "ontology-advanced.yaml").read_text())
        cfg["profiles"]["inference"] = {"enabled": True}
        cfg["extensions"][0]["sha256"] = sha256(root / ext_path)
        cfg["publication"] = {"enabled": True, "binding": {"actor_id": "/root", "scope": ["ontology-advanced.yaml", "ONTOLOGY/extensions"],
            "authority": [{"path": name, "sha256": sha256(root / name)} for name in ("SOUL.md", "AGENTS.md", "ROLE.md")]}}
        write_json(root / "ontology-advanced.yaml", cfg)
        proposed_shape = shape.replace("sh:minCount 0", "sh:minCount 1").encode()
        ext["version"] = "1.0.1"
        ext["shapes"][0]["sha256"] = sha256(proposed_shape)
        ext["annotations"] = [statement(root, "label", project_id("subject"), RDFS + "label", {"value": "Observed label"})]
        ext["axioms"] = [statement(root, "subclass", project_id("LocalClass"), RDFS + "subClassOf", project_id("OtherClass"))]
        raw = canonical_bytes(ext); cfg["extensions"][0]["sha256"] = sha256(raw)
        proposal = {"schema_version": 2, "operation_id": "ONTOP-guarded-v2-fixture", "operation": "publish", "reason": "Private fixture marker DO_NOT_ECHO_BODY.", "changes": [
            {"path": path, "expected_sha256": sha256(root / path), "content": content.decode(), "sha256": sha256(content)}
            for path, content in ((ext_path, raw), (shape_path, proposed_shape), ("ontology-advanced.yaml", canonical_bytes(cfg)))]}
        return root, owner, proposal

    def test_v2_selected_shape_failure_and_formal_inconsistency_stop_before_owner(self):
        from advanced_support import statement, project_id
        from ontology_advanced import RDF, OWL
        from ontology_core import canonical_bytes, sha256
        for case in ("shape", "unsupported", "inconsistent"):
            with self.subTest(case=case):
                root, owner, proposal = self.extension_candidate()
                ext = json.loads(proposal["changes"][0]["content"])
                if case == "shape":
                    ext["annotations"] = []
                elif case == "unsupported":
                    ext["axioms"].append(statement(root, "unsupported", project_id("P"), RDF + "type", OWL + "FunctionalProperty"))
                else:
                    ext["axioms"] += [statement(root, "type-a", project_id("subject"), RDF + "type", project_id("A")),
                        statement(root, "type-b", project_id("subject"), RDF + "type", project_id("B")),
                        statement(root, "disjoint", project_id("A"), OWL + "disjointWith", project_id("B"))]
                raw = canonical_bytes(ext)
                proposal["changes"][0].update(content=raw.decode(), sha256=sha256(raw))
                cfg = json.loads(proposal["changes"][-1]["content"]); cfg["extensions"][0]["sha256"] = sha256(raw)
                raw = canonical_bytes(cfg); proposal["changes"][-1].update(content=raw.decode(), sha256=sha256(raw))
                before = canonical_snapshot(root, "ONTOLOGY")
                backend = importlib.import_module("ontology_standards")
                observed = []
                real_validate, real_infer = backend.validate, backend.infer
                def validate(*args, **kwargs):
                    result = real_validate(*args, **kwargs); observed.append(("validate", result["status"], result["complete"])); return result
                def infer(*args, **kwargs):
                    result = real_infer(*args, **kwargs); observed.append(("infer", result["status"], result["complete"])); return result
                with patch.object(backend, "validate", validate), patch.object(backend, "infer", infer), patch.object(owner, "_advanced_checks", wraps=owner._advanced_checks), patch.object(owner, "_candidate", wraps=owner._candidate):
                    with self.assertRaises(Exception) as rejected:
                        owner.publish(root, proposal, {}, expected_preview_sha256="0" * 64)
                    self.assertEqual(owner._advanced_checks.call_count, 0)
                    self.assertEqual(owner._candidate.call_count, 0)
                expected = "violation" if case == "shape" else "unsupported_semantics" if case == "unsupported" else "inconsistent"
                self.assertEqual(observed[-1][1], expected)
                self.assertIn("action=urn:sys4ai:ontology:action:ontology:publish", str(rejected.exception))
                self.assertIn("source=reference-assets/ONTOLOGY-depo/actions/contracts-v1.json@", str(rejected.exception))
                self.assertNotIn("DO_NOT_ECHO_BODY", str(rejected.exception))
                self.assertEqual(canonical_snapshot(root, "ONTOLOGY"), before)

    def test_v2_guarded_publication_recovers_accepted_extension_and_shape_pre_post(self):
        from ontology_core import sha256
        root, owner, proposal = self.extension_candidate()
        authority = grant(root, proposal)
        authority.update(schema_version=2, advanced_config_sha256=sha256(root / "ontology-advanced.yaml"), proposal_review=None)
        receipt = owner.publish(root, proposal, authority, expected_preview_sha256=authority["preview_sha256"], fail_at="after_commit:1")
        self.assertEqual(receipt["status"], "partial")
        self.assertEqual(receipt["ontology_guard"]["candidate_validation"]["inference"]["status"], "ok")
        recovered = owner.recover(root, proposal["operation_id"], authority)
        self.assertEqual(recovered["status"], "complete")
        self.assertEqual(recovered["ontology_guard"]["semantic_status"], "conformant")
        self.assertTrue(recovered["ontology_guard"]["lock_rechecked"])
        for change in proposal["changes"]:
            self.assertEqual(sha256(root / change["path"]), change["sha256"])


if __name__ == "__main__":
    unittest.main()
