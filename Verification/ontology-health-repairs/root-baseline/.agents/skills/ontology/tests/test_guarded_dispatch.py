"""Actual installed owning functions and actual selected SHACL backend.

Native receipts/selected requests are synthetic isolated fixtures. The validator
is never mocked in this matrix. It is source-stage evidence, not live root setup.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
import inspect
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from guard_support import DEPOT, project, load, fixture_selection, canonical_snapshot, preserve_imports
from support import make_project, bind_director, proposal, record, grant, write_json
from ontology_guards import digest


def helper_fixture(name, path):
    return load(DEPOT / path, "guard_fixture_" + name)


@unittest.skipUnless((DEPOT / ".venv-ontology-standards/certification.json").is_file(), "Actual selected standards backend is not provisioned in this checkout")
class GuardedDispatchTests(unittest.TestCase):
    observations = []

    def setUp(self):
        preserve_imports(self)

    @classmethod
    def tearDownClass(cls):
        selected = os.environ.get("SYS4AI_GUARD_EVIDENCE")
        if selected:
            evidence = {"schema_version": 1, "status": "passed" if len(cls.observations) == 48 else "incomplete",
                        "backend": "actual-selected-standards", "native_identity": "synthetic isolated fixture receipts",
                        "observations": cls.observations,
                        "uncovered": ["Raw host/shell/third-party writes", "Private low-level primitives outside owning public helpers"]}
            fingerprints = {row["adapters_sha256"] for row in cls.observations if "adapters_sha256" in row}
            if len(fingerprints) == 1:
                evidence["adapters_sha256"] = next(iter(fingerprints))
            else:
                evidence["status"] = "incomplete"
            write_json(Path(selected), evidence)

    def fixtures(self, family):
        preserve_imports(self)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()
        r = base / "project"
        if family == "setup":
            data = helper_fixture("initializer", "SKILLS-depo/init-new-project/tests/test_initializer.py")
            r = data.fixture_depot(base)
        elif family == "template":
            data = helper_fixture("template", "tests/test_template_update.py")
            r.mkdir()
            data.fixture(r)
        r = project(r)
        if family == "memory":
            sys.path.insert(0, str(DEPOT / "SKILLS-depo/memory/tests"))
            data = helper_fixture("memory", "SKILLS-depo/memory/tests/test_core.py")
            data.build_project(r)
            bind_director(r)
            for name in list(sys.modules):
                if name.startswith("memory_") or name == "basic_memory_adapter":
                    del sys.modules[name]
            sys.path.insert(0, str(r / ".agents/skills/memory/scripts"))
            module = load(r / ".agents/skills/memory/scripts/memory_publish.py", "guard_memory_owner")
            payload = data.make_payload(r, data.make_record(r))
            selected_grant = data.make_grant(r, payload)
            call = lambda: module.publish(r, payload, selected_grant, "/root")
            unauthorized = lambda: module.publish(r, payload, selected_grant, "/root/child")
            return r, module, "transact", "MEMORY", call, unauthorized
        if family == "ontology":
            module = load(r / ".agents/skills/ontology/scripts/ontology_publication.py", "guard_ontology_owner")
            payload = proposal(r, [record("selected-result")])
            selected_grant = grant(r, payload)
            call = lambda: module.publish(r, payload, selected_grant, expected_preview_sha256=selected_grant["preview_sha256"])
            def refresh():
                selected_grant.clear()
                selected_grant.update(grant(r, payload))
            call.refresh = refresh
            def unauthorized():
                next_payload = proposal(r, [record("selected-result")], "ONTOP-unauthorized-0001")
                bad = grant(r, next_payload)
                bad["actor_id"] = "/root/child"
                return module.publish(r, next_payload, bad, expected_preview_sha256=bad["preview_sha256"])
            return r, module, "publish", "ONTOLOGY/modules/project", call, unauthorized
        if family == "trd":
            module = load(r / ".agents/skills/to-trd/scripts/trd.py", "guard_trd_owner")
            store = module.Store(r)
            payload = json.loads((r / ".agents/skills/to-trd/assets/example-input.json").read_text())
            call = lambda: store.create(payload)
            def unauthorized():
                # Separate actual owner lifecycle operation against a prepared
                # record; no synthetic approval is inferred from preparation.
                records, _ = store.read()
                chosen = records[0]
                return store.set_status(chosen.meta["trd_id"], chosen.sha256, "trd_done", "Fixture lifecycle request.", False)
            return r, module, "create", "TRDs", call, unauthorized
        if family == "task":
            sys.path.insert(0, str(r / ".agents/skills/agent-task/scripts"))
            module = load(r / ".agents/skills/agent-task/scripts/task_state.py", "guard_task_owner")
            tasks = r / "Tasks"
            tasks.mkdir()
            module.write_index(tasks, [])
            payload = {"name": "Guarded fixture task", "description": "Verify an isolated owning Task mutation.", "definition_of_done": ["Reopen the exact created Task."]}
            call = lambda: module.command_new(r, tasks, payload)
            def unauthorized():
                state = json.loads(next(tasks.glob("*/task.json")).read_text())
                response = {"work_completed": ["Prepared isolated cancellation request."], "verification_evidence": ["Fixture only."], "user_response_summary": "Fixture request", "current_summary": "Fixture request", "next_step": None, "blockers": [], "open_questions": [], "relevant_files": [], "status_after": "cancelled", "status_reason": "Fixture request", "user_authorized": False}
                return module.response_transaction("cancel", r, tasks, state["task_id"], state["revision"], response)
            return r, module, "command_new", "Tasks", call, unauthorized
        if family == "plan":
            module = load(r / ".agents/skills/to-implementation-plan/scripts/plan_state.py", "guard_plan_owner")
            context = module.resolve_context(str(r), "Implementation_Plans")
            input_path = r / "guard-plan-input.json"
            input_path.write_bytes((r / ".agents/skills/to-implementation-plan/assets/example-input.json").read_bytes())
            args = argparse.Namespace(input=str(input_path))
            call = lambda: module.handle_create(context, args)
            def unauthorized():
                selected = module.discover_managed_plans(context)[0][0]
                args2 = argparse.Namespace(selector=selected.plan["plan_id"], expected_revision=selected.plan["revision"], expected_sha256=selected.sha256, status_value="cancelled", reason="Fixture cancellation request.", confirmed=False)
                return module.handle_set_status(context, args2)
            return r, module, "handle_create", "Implementation_Plans", call, unauthorized
        if family == "role":
            module = load(r / ".agents/skills/manage-subagent-roles/scripts/role_catalog.py", "guard_role_owner")
            role_dir = r / "Roles/project-sub-agent"
            role_dir.mkdir(parents=True)
            for filename in ("AGENTS.md", "ROLE.md"):
                shutil.copyfile(DEPOT / "Roles/project-sub-agent" / filename, role_dir / filename)
            shutil.copytree(role_dir, r / "sub-agent-roles/project-sub-agent")
            call = lambda: module.reindex(r)
            unauthorized = lambda: module.transition_apply(r, module.transition_preview(r), confirmed=False)
            return r, module, "reindex", "Roles", call, unauthorized
        if family == "template":
            module = load(r / "tools/template_update.py", "guard_template_owner")
            call = lambda: module.update(r, "apply")
            unauthorized = lambda: module.update(r, "apply", retire_collection=json.loads((r / ".sys4ai/template-update/state.json").read_text())["collections"][0], expected_state_sha256="0" * 64)
            return r, module, "update", "Projects/Sys4AI-Template-Project", call, unauthorized
        module = load(r / "SKILLS-depo/init-new-project/scripts/init_new_project.py", "guard_setup_owner")
        args = {"mode": "create", "destination": r / "Projects/guard-created", "project_id": "guard-created", "project_name": "Guard created", "purpose": "Verify isolated setup through its owning helper."}
        call = lambda: module.run_initialization(**args)
        denied = dict(args, project_id="different-project-identity")
        unauthorized = lambda: module.run_initialization(**denied)
        return r, module, "run_initialization", "Projects/guard-created", call, unauthorized

    def natural_invalid(self, family, root, owner, call):
        """Structurally representable requests, with unchanged delivered rules."""
        values = inspect.getclosurevars(call).nonlocals
        if family == "ontology":
            original = copy.deepcopy(values["payload"])
            change = values["payload"]["changes"][0]
            document = json.loads(change["content"])
            document["@graph"][0]["@type"] = ["urn:sys4ai:ontology:core:UndeclaredType"]
            change["content"] = json.dumps(document)
            change["sha256"] = digest(change["content"].encode())
            return call, lambda: (values["payload"].clear(), values["payload"].update(original)), "undeclared canonical input type"
        if family == "memory":
            change = values["payload"]["changes"][0]
            before = change["path"]
            change["path"] = "ONTOLOGY/" + Path(before).name
            return call, lambda: change.update(path=before), "memory record targets the ontology store"
        if family == "task":
            return lambda: owner.command_new(root, root / "ONTOLOGY", values["payload"]), lambda: None, "Task creation targets the ontology store"
        if family == "trd":
            store = values["store"]
            before = store.folder
            store.folder = root / "ONTOLOGY"
            return call, lambda: setattr(store, "folder", before), "TRD store points to ontology files"
        if family == "plan":
            context = owner.resolve_context(str(root), "ONTOLOGY")
            return lambda: owner.handle_create(context, values["args"]), lambda: None, "plan creation targets the ontology store"
        if family == "role":
            path = root / "Roles/project-sub-agent/ROLE.md"
            before = path.read_bytes()
            path.write_text("# Missing required role frontmatter\n")
            return call, lambda: path.write_bytes(before), "role index contains an untyped role bundle"
        if family == "template":
            return lambda: owner.update(root, "apply", retire_collection="unknown-collection", expected_state_sha256="0" * 64), lambda: None, "retirement requests an unrecorded source collection"
        args = dict(values["args"], destination=root / "outside-projects")
        return lambda: owner.run_initialization(**args), lambda: None, "setup targets an unclassified destination"

    def test_actual_family_matrix(self):
        for family in ("trd", "memory", "task", "plan", "role", "template", "setup", "ontology"):
            with self.subTest(family=family):
                r, owner, operation, target, call, unauthorized = self.fixtures(family)
                definitions_path = r / "reference-assets/ONTOLOGY-depo/actions/contracts-v1.json"
                original_contract = json.loads(definitions_path.read_text())
                invalid, restore, condition = self.natural_invalid(family, r, owner, call)
                before = canonical_snapshot(r, target)
                import ontology_guards
                import ontology_standards
                invoked = []
                backend_observations = []
                real_validate = ontology_standards.validate
                def observed_validate(*args, **kwargs):
                    result = real_validate(*args, **kwargs)
                    backend_observations.append({"status": result.get("status"), "complete": result.get("complete"), "findings": result.get("findings", [])})
                    return result
                real_dispatch = ontology_guards.dispatch
                def observed_dispatch(function, *args, **kwargs):
                    def continuation():
                        invoked.append(True)
                        return function()
                    actual_namespace = types.FunctionType(continuation.__code__, function.__globals__, closure=continuation.__closure__)
                    return real_dispatch(actual_namespace, *args, **kwargs)
                try:
                    from contextlib import nullcontext
                    with patch.object(ontology_guards, "dispatch", observed_dispatch), patch.object(ontology_standards, "validate", observed_validate), patch.object(owner, "_candidate", wraps=owner._candidate) if family == "ontology" else nullcontext():
                        with self.assertRaises(Exception) as rejected:
                            invalid()
                        if family == "ontology":
                            self.assertEqual(owner._candidate.call_count, 0)
                    self.assertIn("semantic", str(rejected.exception).lower())
                    self.assertEqual(invoked, [])
                    self.assertEqual([(row["status"], row["complete"]) for row in backend_observations], [("violation", True)])
                    self.assertEqual(before, canonical_snapshot(r, target))
                    self.observations.append({"family": family, "operation": operation, "case": "invalid", "passed": True, "intended_side_effect": False, "underlying_continuation_invoked": False, "condition": condition, "rules": "unchanged delivered typed contract and SHACL", "backend": "actual-selected-standards", "backend_observations": backend_observations})
                finally:
                    restore()
                before = canonical_snapshot(r, target)
                # Duplicate stable action bindings are ambiguous, even though
                # both are individually structurally valid.
                ambiguous = copy.deepcopy(original_contract)
                chosen = next(item for item in ambiguous["actions"] if item["family"] == family and item["operation"] == operation)
                ambiguous["actions"].append(copy.deepcopy(chosen))
                fixture_selection(r, contract=ambiguous)
                with self.assertRaises(Exception): call()
                self.assertEqual(before, canonical_snapshot(r, target))
                self.observations.append({"family": family, "operation": operation, "case": "ambiguous", "passed": True, "intended_side_effect": False})
                fixture_selection(r, contract=original_contract)
                # Removing the independently provisioned environment observes
                # actual unavailable-backend handling, not a mocked response.
                env = r / ".venv-ontology-standards"
                hidden = r / ".guard-backend-unavailable"
                env.rename(hidden)
                try:
                    with self.assertRaises(Exception): call()
                finally:
                    hidden.rename(env)
                self.assertEqual(before, canonical_snapshot(r, target))
                self.observations.append({"family": family, "operation": operation, "case": "backend-failure", "passed": True, "intended_side_effect": False})
                # A changed installed adapter binding invalidates this action.
                helper_path = r / chosen["dispatch"]["path"]
                old_helper = helper_path.read_bytes()
                helper_path.write_bytes(old_helper + b"\n# Changed after reviewed coverage\n")
                try:
                    with self.assertRaises(Exception): call()
                finally:
                    helper_path.write_bytes(old_helper)
                self.assertEqual(before, canonical_snapshot(r, target))
                self.observations.append({"family": family, "operation": operation, "case": "stale", "passed": True, "intended_side_effect": False})
                if hasattr(call, "refresh"):
                    call.refresh()
                receipt = call()
                after = canonical_snapshot(r, target)
                self.assertTrue(after, (family, receipt))
                result = receipt[0] if isinstance(receipt, tuple) else receipt
                self.assertEqual(result["ontology_guard"]["semantic_status"], "conformant")
                self.assertEqual(result["ontology_guard"]["owning_helper"], "returned")
                cfg = json.loads((r / "ontology-advanced.yaml").read_text())
                adapters = json.loads((r / cfg["profiles"]["guards"]["adapters"]["path"]).read_text())
                self.observations.append({"family": family, "operation": operation, "case": "positive", "passed": True, "reopened": True, "post_state_sha256": digest(after), "backend": "actual-selected-standards", "receipt": result, "adapters_sha256": digest(adapters)})
                authorization_before = canonical_snapshot(r, target)
                with self.assertRaises(Exception) as rejected:
                    unauthorized()
                self.assertTrue(str(rejected.exception))
                self.assertTrue(any(word in str(rejected.exception).lower() for word in
                    ("confirmation", "confirmed", "authorization", "publisher", "grant", "actor", "scope", "destination", "retirement", "state digest", "owner", "project root", "identity")), str(rejected.exception))
                self.assertEqual(authorization_before, canonical_snapshot(r, target))
                self.observations.append({"family": family, "operation": operation, "case": "unauthorized", "passed": True, "intended_side_effect": False, "boundary": "owning helper confirmation, actor or selected-scope gate", "diagnostic": str(rejected.exception)})

    def test_actual_under_lock_context_changes_block_each_family(self):
        for family in ("trd", "memory", "task", "plan", "role", "template", "setup", "ontology"):
            with self.subTest(family=family):
                r, owner, operation, target, call, _ = self.fixtures(family)
                before = canonical_snapshot(r, target)
                soul = r / "SOUL.md"
                original_soul = soul.read_bytes()
                changed = []
                if family == "memory":
                    import memory_recovery
                    owner = memory_recovery
                if family == "ontology":
                    original = owner._recheck
                    def inject(decision, *, targets=True):
                        if decision.operation == "publish" and not changed:
                            soul.write_bytes(original_soul + b"\nChanged after semantic check.\n")
                            changed.append(True)
                        return original(decision, targets=targets)
                    name = "_recheck"
                else:
                    original = owner._ontology_checkpoint
                    def inject(*, targets=True):
                        if targets and not changed:
                            soul.write_bytes(original_soul + b"\nChanged after semantic check.\n")
                            changed.append(True)
                        return original(targets=targets)
                    name = "_ontology_checkpoint"
                try:
                    with patch.object(owner, name, inject):
                        with self.assertRaises(Exception) as rejected:
                            call()
                    self.assertEqual(changed, [True], str(rejected.exception))
                    self.assertTrue(any(word in str(rejected.exception).lower() for word in ("changed", "stale")), str(rejected.exception))
                    self.assertEqual(before, canonical_snapshot(r, target))
                finally:
                    soul.write_bytes(original_soul)

    def test_every_declared_public_boundary_rejects_without_backend(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = project(Path(temporary.name))
        env = root / ".venv-ontology-standards"
        env.rename(root / ".fixture-unavailable-backend")
        definitions = json.loads((root / "reference-assets/ONTOLOGY-depo/actions/contracts-v1.json").read_text())
        modules, rows = {}, []
        before = {name: canonical_snapshot(root, name) for name in ("ONTOLOGY", "MEMORY", "Tasks", "TRDs", "Implementation_Plans", "Roles", "Projects")}
        for action in definitions["actions"] + definitions.get("optional_actions", []):
            relative, symbol = action["dispatch"]["path"], action["dispatch"]["symbol"]
            if relative not in modules:
                path = root / relative
                sys.path.insert(0, str(path.parent))
                modules[relative] = load(path, "guard_boundary_" + str(len(modules)))
            module = modules[relative]
            if symbol.startswith("Store."):
                function = getattr(module.Store(root), symbol.split(".")[1])
            elif not hasattr(module, symbol) and action in definitions.get("optional_actions", []):
                continue
            else:
                function = getattr(module, symbol)
            values = {"root": root, "project_root": root, "depot": root, "tasks_root": root / "Tasks",
                      "destination": root / "Projects/rejected-fixture", "payload": {}, "raw_payload": {}, "record": {}, "pending": {}, "preview": {},
                      "grant": {}, "grant_file": "Verification/no-current-grant.json", "actor": "/root/child",
                      "operation_id": "ONTGUARD-rejected-fixture", "journal_path": ".sys4ai/memory/maintenance/transactions/MEMOP-absent.json",
                      "selector": "absent-fixture", "expected": "0" * 64, "expected_sha256": "0" * 64,
                      "expected_revision": 1, "expected_preview_sha256": "0" * 64, "expected_config_sha256": "0" * 64,
                      "expected_payload_sha256": "0" * 64, "enabled": False, "confirmed": False,
                      "status": "retired", "reason": "Explicit rejected isolated request.", "command": "apply",
                      "action_id": "TO-IP-004", "mutator": lambda current: None,
                      "mode": "create", "project_id": "rejected-fixture", "project_name": "Rejected fixture", "purpose": "Verify a failed dispatch writes no intended result.",
                      "args": argparse.Namespace(input=str(root / "absent-input.json"), selector="absent", name="fixture", confirmed=False)}
            if "context" in inspect.signature(function).parameters:
                values["context"] = module.resolve_context(str(root), "Implementation_Plans")
            kwargs = {}
            for name, parameter in inspect.signature(function).parameters.items():
                if parameter.default is inspect.Parameter.empty:
                    kwargs[name] = values.get(name, None)
            with self.subTest(action=action["id"]):
                with self.assertRaises(Exception) as rejected:
                    function(**kwargs)
                after = {name: canonical_snapshot(root, name) for name in before}
                self.assertEqual(after, before)
                rows.append({"action_id": action["id"], "dispatch": action["dispatch"], "called": True,
                             "result": "rejected", "intended_side_effect": False,
                             "phase": "owning structural check or enabled unavailable-backend guard",
                             "diagnostic_type": type(rejected.exception).__name__})
        expected = len(definitions["actions"]) + sum(hasattr(modules[action["dispatch"]["path"]], action["dispatch"]["symbol"])
            for action in definitions.get("optional_actions", []))
        self.assertEqual(len(rows), expected)
        destination = os.environ.get("SYS4AI_GUARD_BOUNDARY_EVIDENCE")
        if destination:
            write_json(Path(destination), {"schema_version": 1, "backend": "actual environment made unavailable",
                       "status": "passed", "observations": rows,
                       "limit": "Malformed fixture requests can fail structural validation before semantic evaluation; valid enabled family dispatch and recovery are tested separately."})


if __name__ == "__main__":
    unittest.main()
