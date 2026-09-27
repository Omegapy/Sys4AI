"""Real backend and owning recovery paths on isolated fixture projects."""
from datetime import datetime, timedelta, timezone
import copy
import importlib
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from guard_support import standards_available, DEPOT, project, canonical_snapshot, preserve_imports
from support import write_json
import test_guarded_dispatch as dispatch_tests


def setup_grant(root, preview):
    """Explicit synthetic native record; never exported as real actor evidence."""
    from ontology_guards import digest
    now = datetime.now(timezone.utc)
    changes = preview["payload"]["changes"]
    return {"schema_version": 1, "operation": preview["payload"]["operation"],
            "preview_sha256": preview["preview_sha256"], "actor_id": "/root", "actor_kind": "director",
            "observed_at": now.isoformat(), "expires_at": (now + timedelta(minutes=4)).isoformat(),
            "native_receipt": {"tool": "collaboration.list_agents", "result": {"agents": [{"agent_name": "/root", "agent_status": "running"}]}},
            "scope": [row["path"] for row in changes], "reviewed_records": [{key: row[key] for key in ("path", "expected_sha256", "sha256")} for row in changes],
            "task": None, "project_id": json.loads((root / "ontology.yaml").read_text())["project"]["id"],
            "config_sha256": digest((root / "ontology.yaml").read_bytes())}


@unittest.skipUnless(standards_available(), "Selected real backend is unavailable")
class GuardRecoveryTests(unittest.TestCase):
    def setUp(self):
        preserve_imports(self)

    def fixture(self, family):
        factory = dispatch_tests.GuardedDispatchTests()
        self.addCleanup(factory.doCleanups)
        return factory.fixtures(family)

    def test_memory_and_ontology_actual_partial_recovery(self):
        for family in ("memory", "ontology"):
            with self.subTest(family=family):
                root, owner, operation, target, call, _ = self.fixture(family)
                values = inspect.getclosurevars(call).nonlocals
                payload = values["payload"]
                if family == "memory":
                    from memory_recovery import recover
                    from memory_core import json_bytes, sha256
                    grant_path = values["selected_grant"]
                    def stop(boundary):
                        if boundary == "after_journal":
                            raise OSError("Observed injected interruption after immutable memory intent")
                    with self.assertRaises(Exception): owner.publish(root, payload, grant_path, "/root", fault=stop)
                    self.assertFalse((root / payload["changes"][0]["path"]).exists())
                    grant = json.loads((root / grant_path).read_text())
                    grant["operation"] = "recover"
                    write_json(root / grant_path, grant)
                    receipt = recover(root, ".sys4ai/memory/maintenance/transactions/" + payload["operation_id"] + ".json", grant_path, "/root")
                    self.assertEqual(receipt["state"], "complete")
                else:
                    grant = values["selected_grant"]
                    result = owner.publish(root, payload, grant, expected_preview_sha256=grant["preview_sha256"], fail_at="before_commit")
                    self.assertEqual(result["status"], "partial")
                    receipt = owner.recover(root, payload["operation_id"], grant)
                    self.assertEqual(receipt["status"], "complete")
                self.assertTrue(canonical_snapshot(root, target))
                self.assertEqual(receipt["ontology_guard"]["semantic_status"], "conformant")

    def test_actual_trd_task_and_plan_projection_recovery(self):
        for family in ("trd", "task", "plan"):
            with self.subTest(family=family):
                root, owner, operation, target, call, _ = self.fixture(family)
                result = call()
                if family == "trd":
                    index = root / "TRDs/INDEX.md"
                    index.unlink()
                    receipt = owner.Store(root).reindex()
                elif family == "task":
                    index = root / "Tasks/INDEX.md"
                    index.unlink()
                    receipt = owner.command_rebuild(root, root / "Tasks", None)
                else:
                    index = root / "Implementation_Plans/INDEX.md"
                    index.unlink()
                    context = owner.resolve_context(str(root), "Implementation_Plans")
                    import argparse
                    receipt = owner.handle_reindex(context, argparse.Namespace())
                    receipt = receipt[0]
                self.assertTrue(index.is_file())
                self.assertEqual(receipt["ontology_guard"]["semantic_status"], "conformant")

    def test_template_and_setup_resume_their_actual_pending_operations(self):
        for family in ("template", "setup"):
            with self.subTest(family=family):
                root, owner, operation, target, call, _ = self.fixture(family)
                original = owner.atomic_write
                stopped = []
                def interrupt(*args, **kwargs):
                    result = original(*args, **kwargs)
                    selected = str(args[0])
                    marker = str(owner.PENDING) if family == "template" else "project-setup.json"
                    if marker in selected and not stopped:
                        stopped.append(True)
                        raise OSError("Observed injected failure after the existing owner saved its pending receipt")
                    return result
                with patch.object(owner, "atomic_write", interrupt):
                    with self.assertRaises(Exception): call()
                self.assertEqual(stopped, [True])
                result = call()
                self.assertTrue(canonical_snapshot(root, target))
                self.assertEqual(result["ontology_guard"]["semantic_status"], "conformant")

    def test_guard_repair_preserves_accepted_pre_post_and_blocks_missing_backend(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = project(Path(temp.name))
        setup = importlib.import_module("ontology_guard_setup")
        guards = importlib.import_module("ontology_guards")
        from ontology_core import canonical_bytes
        config = json.loads((root / "ontology-advanced.yaml").read_text())
        selected = config["profiles"]["guards"]
        adapters = json.loads((root / selected["adapters"]["path"]).read_text())
        bootstrap = json.loads((root / selected["bootstrap"]["path"]).read_text())
        helper = ".agents/skills/to-trd/scripts/trd.py"
        changed = (root / helper).read_text() + "\n# Exact reviewed repair fixture.\n"
        for adapter in adapters["families"]["trd"]:
            adapter["sha256"] = guards.digest(changed.encode())
        adapter_path = setup.CONTROL + "repair-fixture-adapters.json"
        bootstrap_path = setup.CONTROL + "repair-fixture-bootstrap.json"
        bootstrap["adapters"] = {"path": adapter_path, "sha256": guards.digest(canonical_bytes(adapters))}
        config["profiles"]["guards"]["adapters"] = bootstrap["adapters"]
        config["profiles"]["guards"]["bootstrap"] = {"path": bootstrap_path, "sha256": guards.digest(canonical_bytes(bootstrap))}
        changes = [setup._change(root, helper, changed), setup._change(root, adapter_path, canonical_bytes(adapters).decode()),
                   setup._change(root, bootstrap_path, canonical_bytes(bootstrap).decode()), setup._change(root, "ontology-advanced.yaml", canonical_bytes(config).decode())]
        widened = copy.deepcopy(changes)
        broad_config = json.loads(widened[-1]["content"])
        broad_config["profiles"]["standards"]["enabled"] = False
        widened[-1]["content"] = canonical_bytes(broad_config).decode()
        widened[-1]["sha256"] = guards.digest(widened[-1]["content"].encode())
        with self.assertRaises(guards.GuardError) as rejected:
            setup.preview_repair(root, operation_id="ONTGUARD-widened-fixture", changes=widened)
        self.assertIn("own profile only", str(rejected.exception))
        pre = setup.preview_repair(root, operation_id="ONTGUARD-repair-fixture", changes=changes)
        grant = setup_grant(root, pre)
        denied = copy.deepcopy(grant)
        denied["actor_id"] = "/root/child"
        with self.assertRaises(Exception): setup.apply(root, pre, denied)
        self.assertFalse((root / (setup.CONTROL + "ONTGUARD-repair-fixture-intent.json")).exists())
        with self.assertRaises(guards.GuardError): setup.apply(root, pre, grant, fail_after=1)
        self.assertEqual((root / helper).read_text(), changed)
        with self.assertRaises(guards.GuardError): guards.begin_action(root, "trd", "create", {}, ["TRDs"])
        env = root / ".venv-ontology-standards"
        other = root / ".fixture-backend-unavailable"
        env.rename(other)
        try:
            with self.assertRaises(guards.GuardError): setup.recover(root, "ONTGUARD-repair-fixture", grant)
        finally:
            other.rename(env)
        (root / helper).write_text(changed + "# Unrecognized bytes\n")
        with self.assertRaises(guards.GuardError): setup.recover(root, "ONTGUARD-repair-fixture", grant)
        self.assertTrue((root / helper).read_text().endswith("# Unrecognized bytes\n"))
        (root / helper).write_text(changed)
        result = setup.recover(root, "ONTGUARD-repair-fixture", grant)
        self.assertEqual(result["status"], "complete")
        self.assertTrue(json.loads((root / "ontology-advanced.yaml").read_text())["profiles"]["guards"]["enabled"])
        self.assertEqual(setup.recover(root, "ONTGUARD-repair-fixture", grant), result)


if __name__ == "__main__":
    unittest.main()
