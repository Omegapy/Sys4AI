from pathlib import Path
import tempfile
import unittest
import copy
from support import *
from ontology_core import load_project, OntologyError, operation_lock
from ontology_publication import preview,publish,recover


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=make_project(Path(self.temp.name)/"project");bind_director(self.root)
        self.proposal=proposal(self.root,[record("fixture")]);self.grant=grant(self.root,self.proposal)

    def run_publish(self,fail_at=None):
        return publish(self.root,self.proposal,self.grant,expected_preview_sha256=self.grant["preview_sha256"],fail_at=fail_at)

    def test_preview_is_read_only_and_publication_preserves_memory_and_governance(self):
        write_json(self.root/"MEMORY/preserved.json",{"keep":"memory"})
        before={name:(self.root/name).read_bytes() for name in ["MEMORY/preserved.json","SOUL.md","AGENTS.md","ROLE.md","SPECS.md"]}
        preview(self.root,self.proposal)
        self.assertFalse((self.root/"control_records").exists())
        result=self.run_publish();self.assertEqual(result["status"],"complete")
        self.assertEqual(result["projection"]["status"],"complete")
        self.assertIn(project_id("fixture"),load_project(self.root).by_id)
        self.assertEqual(before,{name:(self.root/name).read_bytes() for name in before})

    def test_same_operation_is_idempotent_and_different_payload_is_rejected(self):
        result=self.run_publish()
        target=self.root/self.proposal["changes"][0]["path"];mtime=target.stat().st_mtime_ns
        self.assertEqual(self.run_publish(),result)
        self.assertEqual(target.stat().st_mtime_ns,mtime)
        altered=copy.deepcopy(self.proposal);altered["reason"]="Different reason"
        with self.assertRaises(OntologyError):publish(self.root,altered,self.grant,expected_preview_sha256=self.grant["preview_sha256"])

    def test_changed_expected_content_and_active_lock_prevent_mutation(self):
        target=self.root/self.proposal["changes"][0]["path"]
        original=target.read_bytes()
        with operation_lock(self.root,"control_records/ontology/publication.lock"):
            with self.assertRaises(OntologyError):self.run_publish()
        self.assertEqual(target.read_bytes(),original)
        target.write_bytes(original+b" ")
        with self.assertRaises(OntologyError):self.run_publish()

    def test_failure_before_intent_creates_no_accepted_change(self):
        with self.assertRaises(OntologyError):self.run_publish("before_intent")
        self.assertFalse((self.root/"control_records/ontology/intents").exists())
        self.assertNotIn(project_id("fixture"),load_project(self.root).by_id)

    def test_commit_projection_and_receipt_failures_recover_exact_operation(self):
        for fault in ("before_commit","after_commit","projection","receipt"):
            with self.subTest(fault=fault):
                root=make_project(Path(self.temp.name)/fault);bind_director(root)
                prop=proposal(root,[record("fixture")]);g=grant(root,prop)
                partial=publish(root,prop,g,expected_preview_sha256=g["preview_sha256"],fail_at=fault)
                self.assertEqual(partial["status"],"partial")
                intent_path=root/("control_records/ontology/intents/"+prop["operation_id"]+".json")
                intent=intent_path.read_bytes()
                final=recover(root,prop["operation_id"],g)
                self.assertEqual(final["status"],"complete")
                self.assertEqual(intent_path.read_bytes(),intent)

    def test_recovery_does_not_overwrite_unrelated_changes(self):
        result=self.run_publish("after_commit");self.assertEqual(result["status"],"partial")
        target=self.root/self.proposal["changes"][0]["path"]
        target.write_text('{"user":"changed"}')
        with self.assertRaises(OntologyError):recover(self.root,self.proposal["operation_id"],self.grant)
        self.assertEqual(target.read_text(),'{"user":"changed"}')

    def test_stale_source_can_be_rebound_by_current_reviewed_proposal(self):
        self.run_publish()
        (self.root/"SPECS.md").write_text("# Specification\n\nUpdated source for fixture.\n")
        changed=copy.deepcopy(load_project(self.root).by_id[project_id("fixture")])
        changed["sources"][0]["sha256"]=sha256(self.root/"SPECS.md")
        prop=proposal(self.root,[changed],operation_id="ONTOP-fixture-0002");g=grant(self.root,prop)
        self.assertEqual(publish(self.root,prop,g,expected_preview_sha256=g["preview_sha256"])["status"],"complete")

    def test_new_exact_selected_file_can_be_published_and_recovered(self):
        cfg = read_json(self.root / "ontology.yaml")
        relative = "ONTOLOGY/modules/project/new.jsonld"
        cfg["project_files"].append(relative); write_json(self.root / "ontology.yaml", cfg)
        content = canonical_bytes({"@context": cfg["context"]["path"], "@graph": [record("new-file-meaning")]}).decode()
        prop = {"schema_version": 1, "operation_id": "ONTOP-new-file-0001", "operation": "publish", "reason": "Add the exact newly selected canonical file.", "changes": [{"path": relative, "expected_sha256": None, "content": content, "sha256": sha256(content.encode())}]}
        g = grant(self.root, prop)
        partial = publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"], fail_at="after_commit")
        self.assertEqual(partial["status"], "partial")
        self.assertEqual(recover(self.root, prop["operation_id"], g)["status"], "complete")
        self.assertEqual((self.root / relative).read_text(), content)


if __name__ == "__main__":unittest.main()
