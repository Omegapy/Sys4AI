"""Actual Task helper integration with explicitly synthetic native receipts."""
import copy
import json
from pathlib import Path
import shutil
import sys
import unittest

from support import PACKAGE, add_records, core_id, make_project, record, write_json
from test_query_retrieval import manifest
from test_query_memory import setup_memory, note
from ontology_core import OntologyError, canonical_bytes, read_json, sha256
from ontology_packet import (assess_change, build_packet, freeze_packet, frozen_project, load_packet,
                             search_packet, validate_assignment)
from ontology_knowledge import knowledge
from ontology_memory import search_memory

TASK = PACKAGE.parent / "agent-task"
sys.path.insert(0, str(TASK / "tests"))
import test_orchestration_state as task_fixture


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.driver = task_fixture.OrchestrationTests(methodName="test_legacy_and_v2_read_only_and_strict_keys")
        original = self.driver.manager_data
        def manager_data(aid):
            data = original(aid)
            data["fit"]["writes"] = ["packets"]
            return data
        self.driver.manager_data = manager_data
        self.driver.setUp()
        self.root = make_project(self.driver.root)
        shutil.copytree(TASK, self.root / ".agents/skills/agent-task", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        self.task_path = str(self.driver.folder.relative_to(self.root) / "task.json")
        cfg = read_json(self.root / "ontology.yaml")
        cfg["project_files"].append("ONTOLOGY/modules/project/late.jsonld")
        write_json(self.root / "ontology.yaml", cfg)
        write_json(self.root / cfg["project_files"][-1], {"@context": cfg["context"]["path"], "@graph": []})

    def tearDown(self): self.driver.tearDown()

    def build(self, **overrides):
        d = self.driver
        kwargs = dict(task_path=self.task_path, execution_id=d.exec_id, generation=d.generation,
                      actor=d.actor, concept_ids=[core_id("Task"), core_id("TRD")])
        kwargs.update(overrides)
        return build_packet(self.root, **kwargs)

    def freeze(self, **overrides):
        packet = self.build(**overrides)
        ref = freeze_packet(self.root, packet, "packets/ontology-v1.json", actor=self.driver.actor)
        return packet, ref

    def register(self, ref, artifact="ontology1"):
        d = self.driver
        d.event("artifact.register", {"artifact_id": artifact, "assignment_id": "manager1", "source_path": ref["path"]})
        entry = d.state["orchestration"]["artifacts"][artifact]
        return {"path": str(d.folder.relative_to(self.root) / entry["path"]), "sha256": entry["sha256"]}

    def test_actual_registration_equal_solver_inputs_and_frozen_late_isolation(self):
        d = self.driver
        packet, ref = self.freeze()
        registered = self.register(ref)
        d.context = [*d.context, registered]
        d.define("complex", False)
        d.assign("solver1", "solver1")
        cfg = read_json(self.root / "ontology.yaml")
        write_json(self.root / cfg["project_files"][-1], {"@context": cfg["context"]["path"], "@graph": [record("late", label="LATE-SENTINEL")]})
        d.assign("solver2", "solver2")
        before = manifest(self.root)
        for aid in ("solver1", "solver2"):
            self.assertEqual(validate_assignment(self.root, registered, task_path=self.task_path, assignment_id=aid)["status"], "bound")
        self.assertFalse(search_packet(self.root, registered, "LATE-SENTINEL")["results"])
        self.assertTrue(search_packet(self.root, registered, "Task")["results"])
        self.assertEqual(before, manifest(self.root))
        self.assertEqual(packet, load_packet(self.root, registered))
        with self.assertRaises(OntologyError) as error: self.build()
        self.assertEqual(error.exception.code, "packet_dispatch_started")
        d.observe("solver1"); d.observe("solver2")
        revised = self.build(subtask_id="subtask1", revision_reason="Owners reconciled for an explicit input assessment.")
        self.assertFalse(assess_change(packet, revised, "Unselected late input only.")["material"])

    def test_wrong_owner_scope_empty_size_and_immutability(self):
        with self.assertRaises(OntologyError): self.build(actor="/root")
        with self.assertRaises(OntologyError): self.build(generation=999)
        with self.assertRaises(OntologyError) as oversized: self.build(max_bytes=1024)
        self.assertEqual(oversized.exception.code, "packet_too_large")
        packet = self.build(concept_ids=[])
        self.assertTrue(packet["empty"])
        with self.assertRaises(OntologyError) as scope: freeze_packet(self.root, packet, "ungranted/result.json", actor=self.driver.actor)
        self.assertEqual(scope.exception.code, "packet_scope")
        ref = freeze_packet(self.root, packet, "packets/ontology-v1.json", actor=self.driver.actor)
        with self.assertRaises(OntologyError) as duplicate: freeze_packet(self.root, packet, ref["path"], actor=self.driver.actor)
        self.assertEqual(duplicate.exception.code, "packet_exists")
        self.assertFalse(search_packet(self.root, ref, "Task")["results"])
        self.assertNotIn("sha256", packet)

    def test_changed_exact_source_and_forged_definition_are_rejected(self):
        packet, ref = self.freeze(allowed_sources=[{"path": "SPECS.md", "sha256": sha256(self.root / "SPECS.md")}])
        current = knowledge(frozen_project(self.root, ref), "ownership", intent="current", frozen_ontology=True)
        self.assertEqual(current["results"][0]["path"], "SPECS.md")
        forged = copy.deepcopy(packet)
        forged["records"][0]["definition"] = "Injected text never present in the source."
        write_json(self.root / "packets/forged.json", forged)
        with self.assertRaises(OntologyError): load_packet(self.root, {"path": "packets/forged.json", "sha256": sha256(self.root / "packets/forged.json")})
        task_before = (self.root / self.task_path).read_bytes()
        (self.root / "SPECS.md").write_text("# Specification\nChanged selected source.\n")
        before = manifest(self.root)
        with self.assertRaises(OntologyError) as changed: search_packet(self.root, ref, "Task")
        self.assertEqual(changed.exception.code, "stale_packet")
        self.assertEqual(before, manifest(self.root))
        self.assertEqual(task_before, (self.root / self.task_path).read_bytes())
        revised = copy.deepcopy(packet)
        revised["records"][0]["definition"] = "Revised selected meaning."
        self.assertTrue(assess_change(packet, revised, "The definition changed.")["material"])
        with self.assertRaises(OntologyError): assess_change(packet, revised, "")

    def test_unselected_and_sibling_sources_and_unregistered_assignment_fail(self):
        with self.assertRaises(OntologyError) as outside:
            self.build(allowed_sources=[{"path": "evidence.txt", "sha256": sha256(self.root / "evidence.txt")}])
        self.assertEqual(outside.exception.code, "excluded_source")
        _, ref = self.freeze()
        d = self.driver
        d.context = [*d.context, ref]
        d.define("complex", False)
        d.assign("solver1", "solver1")
        with self.assertRaises(OntologyError) as unregistered:
            validate_assignment(self.root, ref, task_path=self.task_path, assignment_id="solver1")
        self.assertEqual(unregistered.exception.code, "packet_unregistered")

    def test_real_frozen_memory_interface_excludes_new_live_records(self):
        setup_memory(self.root)
        note(self.root)
        from memory_packet import build_packet as memory_build, freeze_packet as memory_freeze
        d = self.driver
        memory = memory_build(self.root, task_path=self.task_path, execution_id=d.exec_id, generation=d.generation, actor=d.actor)
        memory_ref = memory_freeze(self.root, memory, "packets/memory-v1.json", actor=d.actor)
        _, ontology_ref = self.freeze()
        note(self.root, suffix="00000004", body="LATE-MEMORY-SENTINEL")
        before = manifest(self.root)
        p = frozen_project(self.root, ontology_ref)
        result = search_memory(p, "ERROR-421", packet=memory_ref, frozen_ontology=True)
        self.assertTrue(result["results"])
        self.assertEqual(result["mode"], "frozen-lexical")
        self.assertFalse(search_memory(p, "LATE-MEMORY-SENTINEL", packet=memory_ref, frozen_ontology=True)["results"])
        self.assertEqual(before, manifest(self.root))


if __name__ == "__main__": unittest.main()
