"""Interruption boundaries, lifecycle linkage, conflict and redaction recovery."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from test_core import (build_project, make_record, make_payload, make_grant, write, snapshot,
                       json_bytes, sha256, load_record, load_records, MemoryError)
from memory_core import render_record
from memory_publish import publish, transaction_payload
from memory_recovery import recover, pending_transactions, JOURNAL_ROOT


def supersession(root):
    old = make_record(root); initial = make_payload(root, old); grant = make_grant(root, initial)
    publish(root, initial, grant, "/root")
    before = initial["changes"][0]["reviewed_record_sha256"]
    successor = make_record(root, record_id="MEM-20260908-B1B2C3D4", operation_id="MEMOP-supersede-0001")
    successor["metadata"]["lifecycle"].update(supersedes=[old["metadata"]["id"]], reason="Revised design with reviewed evidence.")
    old["metadata"]["state"] = "superseded"
    old["metadata"]["modified"] = successor["metadata"]["modified"]
    old["metadata"]["publication"] = copy.deepcopy(successor["metadata"]["publication"])
    old["metadata"]["lifecycle"].update(superseded_by=successor["metadata"]["id"], reason="Revised design with reviewed evidence.")
    # Append successor first to prove pending-state recall never silently emits
    # two active controlling conclusions during an interrupted transaction.
    changes = make_payload(root, successor)["changes"] + make_payload(root, old, expected=before)["changes"]
    payload = transaction_payload("MEMOP-supersede-0001", "supersede", changes, "Revised design with reviewed evidence.")
    return payload, make_grant(root, payload, suffix="supersede")


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = build_project(Path(self.temp.name))

    def test_faults_at_every_commit_boundary_recover_without_duplicate_identity(self):
        for index, boundary in enumerate(("before_journal", "after_journal", "before_record_0", "before_replace_0", "after_record_0",
                                          "before_record_1", "after_record_1", "before_receipt", "after_receipt")):
            with self.subTest(boundary=boundary):
                root = build_project(self.root / ("case-" + str(index)))
                payload, grant = supersession(root)
                def fail(actual):
                    if actual == boundary: raise OSError("injected interruption")
                with self.assertRaises((MemoryError, OSError)): publish(root, payload, grant, "/root", fault=fail)
                if boundary == "before_journal":
                    self.assertFalse(pending_transactions(root)); self.assertEqual(len(load_records(root)), 1)
                    result = publish(root, payload, grant, "/root")
                else:
                    journal = JOURNAL_ROOT + "/" + payload["operation_id"] + ".json"
                    recovery_grant = make_grant(root, payload, operation="recover", suffix="recover")
                    result = recover(root, journal, recovery_grant, "/root")
                    before = snapshot(root)
                    self.assertEqual(recover(root, journal, recovery_grant, "/root"), result)
                    self.assertEqual(snapshot(root), before)
                self.assertEqual(result["state"], "complete")
                self.assertEqual(len(load_records(root)), 1)
                self.assertEqual(len(load_records(root, historical=True)), 2)
                self.assertEqual(load_records(root)[0]["metadata"]["id"], "MEM-20260908-B1B2C3D4")

    def test_pending_shared_recall_and_human_edit_block_unsafe_recovery(self):
        payload, grant = supersession(self.root)
        def fail(boundary):
            if boundary == "after_record_0": raise OSError("interrupted")
        with self.assertRaises(MemoryError): publish(self.root, payload, grant, "/root", fault=fail)
        with self.assertRaises(MemoryError) as error: load_records(self.root)
        self.assertEqual(error.exception.code, "recovery_required")
        path = payload["changes"][1]["path"]; write(self.root, path, (self.root / path).read_text() + "Human revision.\n")
        before = (self.root / path).read_bytes()
        recovery_grant = make_grant(self.root, payload, operation="recover", suffix="recover")
        with self.assertRaises(MemoryError): recover(self.root, JOURNAL_ROOT + "/" + payload["operation_id"] + ".json", recovery_grant, "/root")
        self.assertEqual((self.root / path).read_bytes(), before)

    def test_retraction_retains_body_and_reason(self):
        record = make_record(self.root); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        publish(self.root, payload, grant, "/root"); original_body = record["body"]
        record["metadata"].update(state="retracted", modified=datetime.now(timezone.utc).isoformat())
        record["metadata"]["publication"].update(operation_id="MEMOP-retract-0001", approved_at=record["metadata"]["modified"])
        record["metadata"]["lifecycle"]["reason"] = "The conclusion is no longer applicable."
        retract = make_payload(self.root, record, operation="retract", reason=record["metadata"]["lifecycle"]["reason"], expected=payload["changes"][0]["reviewed_record_sha256"])
        result = publish(self.root, retract, make_grant(self.root, retract), "/root")
        self.assertEqual(result["state"], "complete"); self.assertEqual(load_records(self.root), [])
        self.assertEqual(load_records(self.root, historical=True)[0]["body"], original_body)

    def test_privacy_redaction_does_not_retain_sensitive_original(self):
        record = make_record(self.root); payload = make_payload(self.root, record); grant = make_grant(self.root, payload)
        publish(self.root, payload, grant, "/root")
        path = payload["changes"][0]["path"]
        secret = "password=" + "fixture" * 5
        write(self.root, path, (self.root / path).read_text() + secret + "\n")
        expected = sha256((self.root / path).read_bytes())
        record["metadata"].update(modified=datetime.now(timezone.utc).isoformat())
        record["metadata"]["publication"].update(operation_id="MEMOP-redact-0001", approved_at=record["metadata"]["modified"])
        record["metadata"]["lifecycle"]["reason"] = "Remove an accidentally added credential."
        redaction = make_payload(self.root, record, operation="redact", expected=expected, reason=record["metadata"]["lifecycle"]["reason"])
        redaction_grant = make_grant(self.root, redaction)
        denied = json.loads((self.root / redaction_grant).read_text()); denied["privacy_redaction"] = False
        write(self.root, redaction_grant, json_bytes(denied))
        with self.assertRaises(MemoryError): publish(self.root, redaction, redaction_grant, "/root")
        redaction_grant = make_grant(self.root, redaction)
        result = publish(self.root, redaction, redaction_grant, "/root")
        self.assertEqual(result["state"], "complete")
        for item in (self.root / ".sys4ai/memory").rglob("*"):
            if item.is_file(): self.assertNotIn(secret.encode(), item.read_bytes())
        self.assertNotIn(secret, (self.root / path).read_text())
        self.assertEqual(load_record(self.root, path)["metadata"]["lifecycle"]["reason"], record["metadata"]["lifecycle"]["reason"])

    def test_redaction_preserves_unrelated_content_in_shared_history(self):
        payload, grant = supersession(self.root)
        publish(self.root, payload, grant, "/root")
        journal_path = JOURNAL_ROOT + "/" + payload["operation_id"] + ".json"
        successor_content = payload["changes"][0]["content"]
        old_path = payload["changes"][1]["path"]
        record = load_record(self.root, old_path)
        record = {"metadata": record["metadata"], "body": "# Historical conclusion\nSelected detail removed under scoped privacy authority.\n"}
        record["metadata"].update(modified=datetime.now(timezone.utc).isoformat())
        record["metadata"]["publication"].update(operation_id="MEMOP-redact-history-0001", approved_at=record["metadata"]["modified"])
        record["metadata"]["lifecycle"]["reason"] = "Remove selected unnecessary detail."
        redaction = make_payload(self.root, record, operation="redact", expected=sha256((self.root / old_path).read_bytes()), reason=record["metadata"]["lifecycle"]["reason"])
        result = publish(self.root, redaction, make_grant(self.root, redaction), "/root")
        self.assertEqual(result["state"], "complete")
        journal = json.loads((self.root / journal_path).read_text())
        self.assertEqual(journal["payload"]["changes"][0]["content"], successor_content)
        self.assertIsNone(journal["payload"]["changes"][1]["content"])
        self.assertEqual(len(load_records(self.root)), 1)


if __name__ == "__main__": unittest.main()

class NativeMemoryRecoveryTests(unittest.TestCase):
    def test_original_journal_requires_fresh_verified_recovery_context(self):
        from test_publication import NativeMemoryFixture
        fixture=NativeMemoryFixture();self.addCleanup(fixture.close)
        context=fixture.driver.context('memory.publish');path,_=fixture.grant(context)
        def fail(boundary):
            if boundary=='after_record_0':raise OSError('synthetic interruption')
        with fixture.driver.authority.invoke(context):
            with self.assertRaises(MemoryError):publish(fixture.root,fixture.payload,path,fixture.driver.actor,fault=fail)
        fresh=fixture.driver.context('memory.recover');recovery_path,value=fixture.grant(fresh,'native-recover')
        value['operation']='recover';write(fixture.root,recovery_path,json_bytes(value))
        journal=JOURNAL_ROOT+'/'+fixture.payload['operation_id']+'.json'
        with self.assertRaises(MemoryError):recover(fixture.root,journal,recovery_path,fixture.driver.actor)
        with fixture.driver.authority.invoke(fresh):
            result=recover(fixture.root,journal,recovery_path,fixture.driver.actor)
        self.assertEqual(result['state'],'complete')
        self.assertEqual(result['operation_id'],fixture.payload['operation_id'])

    def test_later_human_edit_survives_rejected_native_recovery(self):
        from test_publication import NativeMemoryFixture
        fixture=NativeMemoryFixture();self.addCleanup(fixture.close)
        context=fixture.driver.context('memory.publish');path,_=fixture.grant(context)
        def fail(boundary):
            if boundary=='after_record_0':raise OSError('synthetic interruption')
        with fixture.driver.authority.invoke(context):
            with self.assertRaises(MemoryError):publish(fixture.root,fixture.payload,path,fixture.driver.actor,fault=fail)
        target=fixture.root/fixture.payload['changes'][0]['path']
        target.write_bytes(target.read_bytes()+b'\nLater human text.\n');later=target.read_bytes()
        fresh=fixture.driver.context('memory.recover');recovery_path,value=fixture.grant(fresh,'later-recover')
        value['operation']='recover';write(fixture.root,recovery_path,json_bytes(value))
        with fixture.driver.authority.invoke(fresh):
            with self.assertRaises(MemoryError):
                recover(fixture.root,JOURNAL_ROOT+'/'+fixture.payload['operation_id']+'.json',recovery_path,fixture.driver.actor)
        self.assertEqual(target.read_bytes(),later)
