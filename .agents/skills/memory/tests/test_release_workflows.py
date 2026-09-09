"""Host-run integration tests. All native receipts are synthetic fixture data.

These tests invoke real Task/memory helpers and inspect actual files. They never
launch, message, impersonate, or supply evidence of a real native agent.
"""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent / "agent-task/tests"))
import test_orchestration_state as fixture
from test_retrieval import setup_project, note, manifest
from test_core import make_grant, make_record, make_payload, write
from memory_core import MemoryError, json_bytes, parse_record, render_record, sha256
from memory_packet import build_packet, freeze_packet, search_packet, validate_assignment, assess_change
from memory_publish import publish, transaction_payload
from memory_recovery import recover, JOURNAL_ROOT


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.d = fixture.OrchestrationTests(methodName="test_legacy_and_v2_read_only_and_strict_keys")
        original = self.d.manager_data
        def manager_data(aid):
            data = original(aid)
            data["fit"]["writes"] = ["packets", "MEMORY", "Verification", ".sys4ai/memory/maintenance"]
            return data
        self.d.manager_data = manager_data
        self.d.setUp()
        self.addCleanup(self.d.tearDown)
        self.root = self.d.root
        shutil.copytree(SKILL.parent / "agent-task", self.root / ".agents/skills/agent-task",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.config = setup_project(self.root)
        self.config["publication"]["director"] = {"actor_id": "/root", "scope": ["MEMORY"],
            "authority": [self.d.ref(p) for p in ("SOUL.md", "AGENTS.md", "ROLE.md")]}
        (self.root / "memory.yaml").write_bytes(json_bytes(self.config))
        self.note_path = note(self.root)
        self.task_path = str(self.d.folder.relative_to(self.root) / "task.json")

    def packet(self, name, reason=None):
        d = self.d
        packet = build_packet(self.root, task_path=self.task_path, execution_id=d.exec_id,
            generation=d.generation, actor=d.actor, subtask_id="subtask1" if reason else None,
            revision_reason=reason)
        ref = freeze_packet(self.root, packet, "packets/" + name + ".json", actor=d.actor)
        d.event("artifact.register", {"artifact_id": name, "assignment_id": "manager1", "source_path": ref["path"]})
        a = d.state["orchestration"]["artifacts"][name]
        return packet, {"path": str(d.folder.relative_to(self.root) / a["path"]), "sha256": a["sha256"]}

    def manager_grant(self, payload, name):
        d = self.d
        rel = make_grant(self.root, payload, actor=d.actor, suffix=name)
        grant = json.loads((self.root / rel).read_text())
        grant.update(actor_kind="manager", task={"path": self.task_path,
            "sha256": sha256((self.root / self.task_path).read_bytes()), "task_id": d.state["task_id"],
            "execution_id": d.exec_id, "generation": d.generation, "assignment_id": "manager1"})
        (self.root / rel).write_bytes(json_bytes(grant))
        return rel

    def supersede_prior_design(self):
        old_raw = (self.root / self.note_path).read_bytes()
        old = parse_record(old_raw)
        new = copy.deepcopy(old)
        stamp = datetime.now(timezone.utc).isoformat()
        operation = "MEMOP-local-material-0001"
        pub = {"actor_id": self.d.actor, "actor_kind": "manager", "operation_id": operation, "approved_at": stamp}
        new["metadata"].update(id="MEM-20260908-11112222", created=stamp, modified=stamp, publication=pub)
        new["metadata"]["lifecycle"].update(supersedes=[old["metadata"]["id"]], reason="Clarified prior fixture design.")
        new["body"] = "The clarified prior design uses ERROR-922 and preserves original source locators.\n"
        old["metadata"].update(state="superseded", modified=stamp, publication=pub)
        old["metadata"]["lifecycle"].update(superseded_by=new["metadata"]["id"], reason="Clarified prior fixture design.")
        changes = make_payload(self.root, new)["changes"] + make_payload(self.root, old, expected=sha256(old_raw))["changes"]
        payload = transaction_payload(operation, "supersede", changes, "Clarified prior fixture design.")
        task_before = manifest(self.root / "Tasks")
        receipt = publish(self.root, payload, self.manager_grant(payload, "material"), self.d.actor)
        self.assertEqual(receipt["state"], "complete")
        self.assertEqual(manifest(self.root / "Tasks"), task_before)

    def test_material_memory_revision_requires_current_reviews_and_new_implementation(self):
        d = self.d
        old, ref = self.packet("memory1")
        d.context = [d.ev, ref]
        d.define("extra-complex", True)
        for aid in ("solver1", "solver2"):
            d.assign(aid, aid)
        d.candidate("solver1", "candidate1")
        d.candidate("solver2", "candidate2")
        for aid in ("reviewer1", "reviewer2"):
            d.assign(aid, aid)
        d.review("reviewer1", "candidate1", "review1")
        d.review("reviewer2", "candidate2", "review2")
        d.candidate("solver1", "candidate1v2", supersedes="candidate1")
        d.event("assignment.reserve", d.assignment_data("senior1", "senior"), fail="ORCH_REVIEW_GATE")
        d.review("reviewer1", "candidate1v2", "review1v2")
        d.assign("senior1", "senior")
        d.synthesis(["candidate1v2", "candidate2"], ["review1v2", "review2"])
        d.assign("implementer1", "implementer")
        d.artifact("implementer1", "deliverable", "Implementation under the old accepted memory.")
        d.result("implementer1", "deliverable", "accept_synthesis1")
        identities = {aid: a["native_id"] for aid, a in d.state["orchestration"]["assignments"].items()}
        self.assertEqual(len(set(identities.values())), 7)
        self.supersede_prior_design()
        before = manifest(self.root)
        with self.assertRaises(MemoryError):
            search_packet(self.root, ref, "ERROR-421")
        self.assertEqual(manifest(self.root), before)
        with self.assertRaises(MemoryError) as active:
            build_packet(self.root, task_path=self.task_path, execution_id=d.exec_id, generation=1,
                actor=d.actor, subtask_id="subtask1", revision_reason="Material memory changed.")
        self.assertEqual(active.exception.code, "packet_dispatch_started")
        for aid in identities:
            if aid != "manager1":
                d.observe(aid)
        new, replacement = self.packet("memory2", "Material memory changed; owners reconciled.")
        self.assertTrue(assess_change(old, new, "Prior design was superseded.")["material"])
        self.assertFalse(assess_change(new, new, "No source or meaning changed.")["material"])
        d.context = [d.ev, replacement]
        d.event("subtask.revise", {"subtask_id": "subtask1", "baseline": d.base("extra-complex", True),
                                  "reason": "Accepted memory changed materially."})
        with self.assertRaises(fixture.task_state.orch.OrchestrationError):
            fixture.task_state.orch.acceptance_current(d.state["orchestration"], "accept_synthesis1", d.state, self.root, d.folder)
        for aid in ("solver1", "solver2"):
            d.rebind(aid)
            self.assertEqual(validate_assignment(self.root, replacement, task_path=self.task_path, assignment_id=aid)["status"], "bound")
        self.assertTrue(search_packet(self.root, replacement, "ERROR-922")["results"])
        d.candidate("solver1", "candidate1v3", supersedes="candidate1v2")
        d.candidate("solver2", "candidate2v2", supersedes="candidate2", revalidation="Updated memory inspected.")
        d.review("reviewer1", "candidate1v3", "review1v3")
        data = d.assignment_data("senior1", "senior")
        d.event("assignment.inputs", {"assignment_id": "senior1", "role": data["role"], "fit": data["fit"],
            "runtime": data["runtime"], "context": data["context"], "receipt": {"tool": "collaboration.send_message",
            "native_id": identities["senior1"], "artifact_sha256s": sorted({r["sha256"] for r in data["context"]}),
            "evidence": "Synthetic input-handoff negative control; no native message sent."},
            "reason": "One current mapped review is still missing."}, fail="ORCH_REVIEW_GATE")
        d.review("reviewer2", "candidate2v2", "review2v2")
        d.synthesis(["candidate1v3", "candidate2v2"], ["review1v3", "review2v2"], synid="synthesis2")
        d.rebind("implementer1")
        d.artifact("implementer1", "deliverable2", "Implementation uses ERROR-922 and the revised accepted memory.")
        st = d.state["orchestration"]["subtasks"]["subtask1"]
        d.event("result.record", {"result_id": "result2", "assignment_id": "implementer1", "acceptance_id": "accept_synthesis2",
            "baseline": st["digest"], "round": st["round"], "artifact_ids": ["deliverable2"],
            "changes": d.context, "checks": d.context, "limitations": ["Synthetic native identities; actual helper and file operations."]})
        for aid in identities:
            if aid != "manager1":
                d.observe(aid)
        d.verify(result="result2", acceptance="accept_synthesis2", artifacts=["deliverable2"])
        self.assertEqual(identities, {aid: a["native_id"] for aid, a in d.state["orchestration"]["assignments"].items()})
        cp, result = d.run_cli("validate")
        self.assertEqual(cp.returncode, 0, result)

    def test_optional_recovery_after_terminal_Task_preserves_all_Task_files(self):
        d = self.d
        d.define()
        d.assign("worker1", "worker")
        d.artifact("worker1", "deliverable", "Completed local fixture output.")
        d.result("worker1", "deliverable")
        d.observe("worker1")
        d.verify()
        d.event("execution.finish", {"outcome": "delivered", "criteria": [{"criterion": "Delivered and inspected.",
            "evidence": "Actual local fixture output inspected."}], "inspection": d.context})
        body = d.response_payload(d.state, completion=True)
        body.update(actor=d.actor, execution_id=d.exec_id, generation=1)
        cp, result = d.run_cli("complete", d.state["task_id"], "--expected-revision", str(d.state["revision"]), payload=body)
        self.assertEqual(cp.returncode, 0, result)
        d.state = d.read_state(d.folder)
        self.assertEqual(d.state["status"], "completed")
        write(self.root, "docs/design.md", "# Prior design\nThe approved fixture uses bounded project memory.\n")
        record = make_record(self.root, record_id="MEM-20260908-33334444", operation_id="MEMOP-terminal-optional-001")
        payload = make_payload(self.root, record)
        grant = make_grant(self.root, payload, suffix="terminal-publish")
        task_before = manifest(self.root / "Tasks")
        def interrupt(boundary):
            if boundary == "after_journal":
                raise OSError("Deliberate optional capture interruption.")
        with self.assertRaises(MemoryError):
            publish(self.root, payload, grant, "/root", fault=interrupt)
        repair = make_grant(self.root, payload, operation="recover", suffix="terminal-recover")
        receipt = recover(self.root, JOURNAL_ROOT + "/" + payload["operation_id"] + ".json", repair, "/root")
        self.assertEqual(receipt["state"], "complete")
        self.assertFalse(receipt["task_events_replayed"])
        self.assertEqual(manifest(self.root / "Tasks"), task_before)
        before_retry = manifest(self.root)
        self.assertEqual(recover(self.root, JOURNAL_ROOT + "/" + payload["operation_id"] + ".json", repair, "/root"), receipt)
        self.assertEqual(manifest(self.root), before_retry)
        self.assertEqual(d.read_state(d.folder)["status"], "completed")


if __name__ == "__main__":
    unittest.main()
