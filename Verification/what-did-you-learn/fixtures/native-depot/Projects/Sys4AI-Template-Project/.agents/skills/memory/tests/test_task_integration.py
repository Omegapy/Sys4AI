"""Actual helper compatibility with synthetic receipts; not native evidence."""
import copy
import json
from pathlib import Path
import shutil
import sys
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent / "agent-task/tests"))
import test_orchestration_state as orchestration_fixture
from test_retrieval import setup_project, note, manifest
from memory_core import MemoryError, parse_record, render_record
from memory_packet import (build_packet, freeze_packet, load_packet, search_packet,
                           validate_assignment, filter_documents, assess_change, packet_bytes)
from memory_search import collect_documents
from memory_normalization import digest


class TaskMemoryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.driver = orchestration_fixture.OrchestrationTests(methodName="test_legacy_and_v2_read_only_and_strict_keys")
        original = self.driver.manager_data
        def manager_data(aid):
            data = original(aid)
            data["fit"]["writes"] = ["packets"]
            return data
        self.driver.manager_data = manager_data
        self.driver.setUp()
        self.root = self.driver.root
        shutil.copytree(SKILL.parent / "agent-task", self.root / ".agents/skills/agent-task",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.config = setup_project(self.root)
        self.note_path = note(self.root)
        self.task_path = str(self.driver.folder.relative_to(self.root) / "task.json")

    def tearDown(self):
        self.driver.tearDown()

    def packet(self):
        d = self.driver
        return build_packet(self.root, task_path=self.task_path, execution_id=d.exec_id,
                            generation=d.generation, actor=d.actor)

    def freeze(self):
        packet = self.packet()
        ref = freeze_packet(self.root, packet, "packets/initial.json", actor=self.driver.actor)
        return packet, ref

    def test_packet_is_frozen_and_bound_through_existing_interfaces(self):
        d = self.driver
        packet, ref = self.freeze()
        d.event("artifact.register", {"artifact_id": "memory1", "assignment_id": "manager1", "source_path": ref["path"]})
        artifact = d.state["orchestration"]["artifacts"]["memory1"]
        registered = {"path": str(d.folder.relative_to(self.root) / artifact["path"]), "sha256": artifact["sha256"]}
        d.context = [*d.context, registered]
        d.define("complex", False)
        d.assign("solver1", "solver1")
        d.assign("solver2", "solver2")
        before = manifest(self.root)
        for aid in ("solver1", "solver2"):
            result = validate_assignment(self.root, registered, task_path=self.task_path, assignment_id=aid)
            self.assertEqual(result["status"], "bound")
        self.assertEqual(search_packet(self.root, registered, "ERROR-421")["mode"], "frozen-lexical")
        self.assertEqual(before, manifest(self.root))
        self.assertNotIn("memory_state", d.state)
        self.assertEqual(packet["task"]["manager"], "/root/manager1")
        with self.assertRaises(MemoryError) as late:
            self.packet()
        self.assertEqual(late.exception.code, "packet_dispatch_started")
        d.observe("solver1")
        d.observe("solver2")
        revised = build_packet(self.root, task_path=self.task_path, execution_id=d.exec_id,
                               generation=d.generation, actor=d.actor, subtask_id="subtask1",
                               revision_reason="Owners reconciled for an inspected input change.")
        self.assertEqual(revised["task"]["subtask_id"], "subtask1")

    def test_new_note_and_sibling_copies_cannot_expand_frozen_recall(self):
        _, ref = self.freeze()
        note(self.root, suffix="99887766", body="SIBLING-SENTINEL invented current candidate.")
        (self.root / "docs/copied.md").write_text("SIBLING-SENTINEL candidate copy")
        self.assertFalse(search_packet(self.root, ref, "SIBLING-SENTINEL")["results"])
        docs, _ = collect_documents(self.root, self.config)
        filtered = filter_documents(self.root, self.config, docs, ref)
        self.assertEqual([d["path"] for d in filtered], [self.note_path])

    def test_changed_evidence_requires_rebind_without_any_task_write(self):
        old, ref = self.freeze()
        before_task = (self.root / self.task_path).read_bytes()
        (self.root / "README.md").write_text("Current evidence changed materially.\n")
        before = manifest(self.root)
        with self.assertRaises(MemoryError):
            search_packet(self.root, ref, "ERROR-421")
        self.assertEqual(before, manifest(self.root))
        self.assertEqual(before_task, (self.root / self.task_path).read_bytes())
        new = copy.deepcopy(old)
        new["documents"] = []
        assessment = assess_change(old, new, "The accepted evidence changed.")
        self.assertTrue(assessment["material"])
        self.assertFalse(assessment["task_events_replayed"])
        self.assertFalse(assess_change(old, old, "Receipt timestamp only.")["material"])

    def test_wrong_manager_and_forged_packet_text_fail_closed(self):
        with self.assertRaises(MemoryError):
            build_packet(self.root, task_path=self.task_path, execution_id=self.driver.exec_id,
                         generation=1, actor="/root")
        packet, _ = self.freeze()
        packet["documents"][0]["segments"][0]["text"] = "Injected conclusion absent from its cited source."
        path = self.root / "packets/forged.json"
        path.write_bytes(packet_bytes(packet))
        with self.assertRaises(MemoryError):
            load_packet(self.root, {"path": "packets/forged.json", "sha256": digest(path.read_bytes())})

    def test_unqualified_active_claim_does_not_seed_a_solver_packet(self):
        path = self.root / self.note_path
        record = parse_record(path.read_bytes())
        record["metadata"]["claim"]["level"] = "verified_outcome"
        record["metadata"]["sources"][0]["kind"] = "verification"
        path.write_text(render_record(record))
        packet = self.packet()
        self.assertTrue(packet["empty"])
        self.assertEqual(packet["excluded"][0]["reason"], "evidence_or_origin_requires_review")

    def test_legacy_schema_and_unsupported_events_stay_unchanged(self):
        d = self.driver
        cp, result = d.run_cli("new", payload={"name": "Legacy memory fixture", "description": "Historical fixture.", "definition_of_done": ["Inspected."]})
        self.assertEqual(cp.returncode, 0, result)
        legacy = Path(result["task_folder"])
        before = (legacy / "task.json").read_bytes()
        cp, result = d.run_cli("show", legacy.name)
        self.assertEqual(cp.returncode, 0, result)
        self.assertEqual(result["task"]["schema_version"], 1)
        self.assertEqual(before, (legacy / "task.json").read_bytes())
        raw = copy.deepcopy(d.state)
        raw["memory_state"] = "active"
        import test_task_state
        self.assertTrue(test_task_state.task_state.validate_state_shape(raw, d.folder, json.dumps(raw)))


if __name__ == "__main__":
    unittest.main()
