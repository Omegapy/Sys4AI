"""Actual on-disk publication, authorization and conflict tests."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import threading
import unittest
import shutil
import sys

from test_core import (build_project, make_record, make_payload, make_grant, write, snapshot,
                       json_bytes, sha256, load_record, load_records, MemoryError)
from memory_core import load_config, render_record
from memory_publish import publish, propose, authorize
from memory_recovery import project_lock, atomic_replace


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = build_project(Path(self.temp.name))

    def test_exact_reviewed_publication_and_idempotent_retry(self):
        record = make_record(self.root); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        result = publish(self.root, payload, grant, "/root")
        self.assertEqual(result["state"], "complete")
        self.assertFalse(result["task_events_replayed"])
        self.assertEqual(load_record(self.root, payload["changes"][0]["path"])["sha256"], payload["changes"][0]["reviewed_record_sha256"])
        before = snapshot(self.root)
        self.assertEqual(publish(self.root, payload, grant, "/root"), result)
        self.assertEqual(before, snapshot(self.root))

    def test_grant_actor_scope_receipt_expiry_and_source_changes(self):
        record = make_record(self.root); payload = make_payload(self.root, record)
        for change in (lambda g: g.update(actor_id="/root/child"), lambda g: g.update(scope=["Verification"]),
                       lambda g: g["native_receipt"]["result"].update(agents=[]),
                       lambda g: g.update(expires_at="2020-01-01T00:00:00Z"),
                       lambda g: g.update(reviewed_records=[]), lambda g: g.update(actor_kind="worker")):
            grant_path = make_grant(self.root, payload)
            grant = json.loads((self.root / grant_path).read_text()); change(grant); write(self.root, grant_path, json_bytes(grant))
            with self.assertRaises(MemoryError): publish(self.root, payload, grant_path, "/root")
            self.assertEqual(load_records(self.root), [])
        grant = make_grant(self.root, payload); write(self.root, "docs/design.md", "Changed source\n")
        with self.assertRaises(MemoryError): publish(self.root, payload, grant, "/root")
        self.assertEqual(load_records(self.root), [])

    def test_changed_evidence_at_actual_replacement_boundary_prevents_activation(self):
        record = make_record(self.root); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        def changed(boundary):
            if boundary == "before_replace_0": write(self.root, "docs/design.md", "Changed while publication was prepared.\n")
        with self.assertRaises(MemoryError) as error: publish(self.root, payload, grant, "/root", fault=changed)
        self.assertEqual(error.exception.code, "publication_interrupted")
        self.assertEqual(error.exception.details["records"][0]["state"], "pending")
        self.assertFalse((self.root / payload["changes"][0]["path"]).exists())

    def test_current_instructions_and_manager_overlap_prevent_host_write(self):
        record = make_record(self.root); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        write(self.root, "ROLE.md", "Changed project role\n")
        with self.assertRaises(MemoryError) as error: publish(self.root, payload, grant, "/root")
        self.assertEqual(error.exception.code, "authority_changed")
        self.root = build_project(self.root)
        grant = make_grant(self.root, payload)
        write(self.root, "Tasks/Task-owner/task.json", json_bytes({"orchestration": {"stage": "active", "manager_id": "manager", "assignments": {"manager": {"state": "active", "fit": {"writes": ["MEMORY"]}}}}}))
        with self.assertRaises(MemoryError) as error: publish(self.root, payload, grant, "/root")
        self.assertEqual(error.exception.code, "manager_owns_scope")

    def test_unsupported_implementation_claim_and_observed_failure_receipt(self):
        record = make_record(self.root, level="verified_outcome"); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        with self.assertRaises(MemoryError): publish(self.root, payload, grant, "/root")
        record = make_record(self.root, kind="experiment", level="observed_failure")
        record["metadata"]["claim"]["summary"] = "An observed experiment failed under the recorded conditions."
        receipt = {"schema_version": 1, "claim_level": "observed_failure", "outcome": "failed", "command": "fixture experiment", "observed_at": datetime.now(timezone.utc).isoformat(),
                   "artifacts": [{"path": "docs/design.md", "sha256": sha256((self.root / "docs/design.md").read_bytes())}]}
        write(self.root, "Verification/experiment.json", json_bytes(receipt))
        record["metadata"]["sources"] = [{"path": "Verification/experiment.json", "sha256": sha256(json_bytes(receipt)), "locator": "json:/outcome", "kind": "verification"}]
        payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        self.assertEqual(publish(self.root, payload, grant, "/root")["state"], "complete")

    def test_child_proposal_is_stdout_draft_without_canonical_write(self):
        record = make_record(self.root, state="draft")
        before = snapshot(self.root); result = propose(self.root, record)
        self.assertFalse(result["written"]); self.assertEqual(snapshot(self.root), before)
        self.assertEqual(load_records(self.root), [])
        with self.assertRaises(MemoryError): propose(self.root, record, output="MEMORY/proposal.md")

    def test_active_lock_competing_writers_and_human_edit(self):
        record = make_record(self.root); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        with project_lock(self.root):
            with self.assertRaises(MemoryError) as error: publish(self.root, payload, grant, "/root")
            self.assertEqual(error.exception.code, "memory_locked")
        sentinel = write(self.root, "Verification/human.md", "original")
        with self.assertRaises(MemoryError):
            atomic_replace(self.root, "Verification/human.md", b"new", sha256(b"original"), before_replace=lambda: sentinel.write_text("human edit"))
        self.assertEqual(sentinel.read_text(), "human edit")
        outcomes = []; barrier = threading.Barrier(2)
        def writer():
            barrier.wait()
            try: outcomes.append(publish(self.root, payload, grant, "/root")["state"])
            except MemoryError as exc: outcomes.append(exc.code)
        one = threading.Thread(target=writer); two = threading.Thread(target=writer)
        one.start(); two.start(); one.join(); two.join()
        self.assertIn("complete", outcomes)
        self.assertTrue(all(result in {"complete", "memory_locked"} for result in outcomes))
        self.assertEqual(len(load_records(self.root)), 1)

    def test_stale_expected_version_and_duplicate_operation_preserve_records(self):
        record = make_record(self.root); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        publish(self.root, payload, grant, "/root")
        path = payload["changes"][0]["path"]; write(self.root, path, (self.root / path).read_text() + "Human addition.\n")
        current = (self.root / path).read_bytes()
        with self.assertRaises(MemoryError): publish(self.root, payload, grant, "/root")
        self.assertEqual((self.root / path).read_bytes(), current)
        changed = copy.deepcopy(payload); changed["reason"] = "Different operation reason."
        grant = make_grant(self.root, changed)
        with self.assertRaises(MemoryError): publish(self.root, changed, grant, "/root")
        self.assertEqual((self.root / path).read_bytes(), current)

    def test_duplicate_identity_at_another_canonical_path_is_rejected(self):
        record = make_record(self.root); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        publish(self.root, payload, grant, "/root")
        record["metadata"]["publication"]["operation_id"] = "MEMOP-duplicate-0001"
        payload = make_payload(self.root, record)
        payload["changes"][0]["path"] = "MEMORY/nested/" + record["metadata"]["id"] + ".md"
        grant = make_grant(self.root, payload)
        with self.assertRaises(MemoryError) as error: publish(self.root, payload, grant, "/root")
        self.assertEqual(error.exception.code, "duplicate_identity")
        self.assertFalse((self.root / payload["changes"][0]["path"]).exists())
        self.assertEqual(len(load_records(self.root)), 1)

    def test_real_task_helper_manager_scope_generation_and_current_role(self):
        from test_core import SCRIPTS
        task_skill = SCRIPTS.parent.parent / "agent-task"
        sys.path.insert(0, str(task_skill / "tests"))
        import test_orchestration_state as fixtures
        driver = fixtures.OrchestrationTests(methodName="test_legacy_and_v2_read_only_and_strict_keys")
        original = driver.manager_data
        def manager_data(aid):
            data = original(aid); data["fit"]["writes"] = ["MEMORY/accepted"]
            return data
        driver.manager_data = manager_data
        driver.setUp(); self.addCleanup(driver.tearDown)
        root = build_project(driver.root)
        shutil.copytree(task_skill, root / ".agents/skills/agent-task", ignore=shutil.ignore_patterns("__pycache__"))
        record = make_record(root); record["metadata"]["publication"].update(actor_id=driver.actor, actor_kind="manager")
        payload = make_payload(root, record); payload["changes"][0]["path"] = "MEMORY/accepted/" + record["metadata"]["id"] + ".md"
        task_path = (driver.folder / "task.json").relative_to(root).as_posix()
        grant_path = make_grant(root, payload, actor=driver.actor)
        grant = json.loads((root / grant_path).read_text()); grant["actor_kind"] = "manager"
        grant["task"] = {"path": task_path, "sha256": sha256((root / task_path).read_bytes()), "task_id": driver.state["task_id"],
                         "execution_id": driver.exec_id, "generation": driver.generation, "assignment_id": "manager1"}
        grant["scope"] = ["MEMORY/accepted"]
        write(root, grant_path, json_bytes(grant))
        original_task = (root / task_path).read_bytes()
        for change in (lambda g: g["task"].update(generation=999), lambda g: g["task"].update(assignment_id="missing")):
            wrong = copy.deepcopy(grant); change(wrong); write(root, grant_path, json_bytes(wrong))
            with self.assertRaises(MemoryError): publish(root, payload, grant_path, driver.actor)
        write(root, grant_path, json_bytes(grant))
        with self.assertRaises(MemoryError) as error:
            authorize(root, load_config(root), grant_path, "publish", sha256(json_bytes(payload)), driver.actor, paths=["MEMORY/outside.md"])
        self.assertEqual(error.exception.code, "grant_scope")
        role_path = root / driver.role["role_path"]; old_role = role_path.read_bytes(); role_path.write_bytes(old_role + b"\nChanged role.\n")
        with self.assertRaises(MemoryError): publish(root, payload, grant_path, driver.actor)
        role_path.write_bytes(old_role)
        result = publish(root, payload, grant_path, driver.actor)
        self.assertEqual(result["state"], "complete")
        self.assertEqual((root / task_path).read_bytes(), original_task)


if __name__ == "__main__": unittest.main()

class NativeMemoryFixture:
    """Actual owner publication fixture; native request frames are synthetic."""
    def __init__(self,protocol_version=1):
        from test_core import SCRIPTS
        sys.path.insert(0,str(SCRIPTS.parent.parent/'agent-task/tests'))
        from test_orchestration_state import NativeOrchestrationFixture
        self.driver=NativeOrchestrationFixture(writes=['MEMORY','control_records/memory'],protocol_version=protocol_version)
        self.root=build_project(self.driver.root)
        self.record=make_record(self.root)
        self.record['metadata']['publication'].update(actor_id=self.driver.actor,actor_kind='manager')
        self.payload=make_payload(self.root,self.record)

    def grant(self,context,suffix='native'):
        path=make_grant(self.root,self.payload,actor=self.driver.actor,suffix=suffix)
        value=json.loads((self.root/path).read_text())
        value.update(schema_version=2,actor_kind='manager',controller_origin='curator',
            native_receipt=self.driver.roster(self.driver.actor),task=self.driver.binding(),
            broker_binding=self.driver.owner_binding(context,'memory'))
        write(self.root,path,json_bytes(value));return path,value

    def close(self):self.driver.close()


class NativeMemoryPublicationTests(unittest.TestCase):
    def test_current_verified_manager_publishes_through_existing_owner(self):
        fixture=NativeMemoryFixture();self.addCleanup(fixture.close)
        context=fixture.driver.context('memory.publish');path,grant=fixture.grant(context)
        with fixture.driver.authority.invoke(context):
            result=publish(fixture.root,fixture.payload,path,fixture.driver.actor)
        self.assertEqual(result['state'],'complete')
        self.assertEqual((fixture.root/fixture.payload['changes'][0]['path']).exists(),True)
        self.assertEqual(grant['schema_version'],2)

    def test_serialized_context_worker_and_changed_owner_fail(self):
        fixture=NativeMemoryFixture();self.addCleanup(fixture.close)
        context=fixture.driver.context('memory.publish');path,grant=fixture.grant(context)
        with self.assertRaises(MemoryError):publish(fixture.root,fixture.payload,path,fixture.driver.actor)
        with fixture.driver.authority.invoke(context):
            for change in (lambda g:g.update(actor_kind='director'),
                           lambda g:g['broker_binding'].update(owner='ontology'),
                           lambda g:g['task'].update(generation=999)):
                bad=copy.deepcopy(grant);change(bad);write(fixture.root,path,json_bytes(bad))
                with self.assertRaises(MemoryError):publish(fixture.root,fixture.payload,path,fixture.driver.actor)
        self.assertFalse((fixture.root/fixture.payload['changes'][0]['path']).exists())


class ForkMemoryPublicationTests(unittest.TestCase):
    def test_new_load_cannot_publish_until_canonical_reconnect_then_existing_owner_commits(self):
        fixture=NativeMemoryFixture(protocol_version=2);self.addCleanup(fixture.close);driver=fixture.driver
        released=driver.release_receipt('native-manager');resumed=driver.resume_receipt('native-manager')
        context=driver.context('memory_publish');path,value=fixture.grant(context,'new-epoch-held')
        with driver.authority.invoke(context),self.assertRaises(MemoryError):publish(fixture.root,fixture.payload,path,driver.actor)
        self.assertFalse((fixture.root/fixture.payload['changes'][0]['path']).exists())
        driver.event('manager.reconnect',{'assignment_id':'native-manager','receipt':resumed,'release_receipt':released,
            'role_reads':driver.role_acknowledgement('native-manager')})
        context=driver.context('memory_publish');path,value=fixture.grant(context,'new-epoch-authorized')
        with driver.authority.invoke(context):result=publish(fixture.root,fixture.payload,path,driver.actor)
        self.assertEqual(result['state'],'complete');self.assertEqual(value['broker_binding']['call']['actor']['load_epoch'],2)
        self.assertEqual(value['schema_version'],2);self.assertEqual(driver.historical_path.read_bytes(),driver.historical_bytes)
