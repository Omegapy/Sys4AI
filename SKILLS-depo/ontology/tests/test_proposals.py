import copy
from pathlib import Path
import tempfile
import unittest

from support import make_project, bind_director, record, proposal, grant, sha256, canonical_bytes, read_json
from ontology_core import OntologyError, safe_path
from ontology_proposals import save, open_proposal, decide
from ontology_proposal_validation import validate_candidate, publish_revision
from ontology_authority import review_binding


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = make_project(Path(self.temp.name) / "project")
        bind_director(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def saved(self, records=None):
        payload = proposal(self.root, records or [record("new-meaning")])
        return save(self.root, payload, rationale="A supported local meaning.", evidence=[record("x")["sources"][0]], uncertainty=["This candidate requires exact human review."])

    def eligible(self):
        value = self.saved()
        return validate_candidate(self.root, value["head"]["proposal_id"], expected_revision=1)

    def reviewed(self):
        value = self.eligible()
        self.assertTrue(value["validation"]["eligible"], value["validation"]["findings"])
        return decide(self.root, value["head"]["proposal_id"], expected_revision=1, decision="accept", reason="Reviewed exact source, meaning and checks.", validation_sha256=value["head"]["validation_sha256"])

    def v2grant(self, value):
        result = grant(self.root, value["revision"]["candidate"])
        companion=self.root/"ontology-advanced.yaml"
        result.update(schema_version=2, advanced_config_sha256=sha256(companion) if companion.exists() else None, proposal_review=review_binding(value))
        return result

    def test_revision_history_rejection_and_stale_save_preserve_canonical(self):
        before = sha256(self.root / "ONTOLOGY/modules/project/project.jsonld")
        first = self.saved();pid = first["head"]["proposal_id"]
        reviewed = validate_candidate(self.root, pid, expected_revision=1)
        reviewed = decide(self.root, pid, expected_revision=1, decision="accept", reason="Exact reviewed fixture.", validation_sha256=reviewed["head"]["validation_sha256"])
        changed = proposal(self.root, [record("new-meaning", definition="A revised local meaning.")], operation_id="ONTOP-revision-2")
        revised = save(self.root, changed, proposal_id=pid, expected_revision=1, rationale="Resolve an observed wording defect.")
        self.assertEqual(revised["head"]["revision"], 2)
        self.assertIsNone(revised["head"]["review_sha256"])
        self.assertEqual(open_proposal(self.root, pid, revision=1)["revision"], first["revision"])
        with self.assertRaisesRegex(OntologyError, "newer saved revision"):
            save(self.root, changed, proposal_id=pid, expected_revision=1, rationale="Stale concurrent edit.")
        rejected = decide(self.root, pid, expected_revision=2, decision="reject", reason="The candidate needs more evidence.")
        self.assertEqual(rejected["head"]["state"], "rejected")
        self.assertEqual(before, sha256(self.root / "ONTOLOGY/modules/project/project.jsonld"))

    def test_validation_impact_and_publish_reopen(self):
        value = self.reviewed()
        self.assertTrue(value["validation"]["impact"]["wiki_pages"])
        self.assertTrue(value["validation"]["impact"]["query_results"])
        result = publish_revision(self.root, value["head"]["proposal_id"], self.v2grant(value), expected_revision=1, expected_review_sha256=value["head"]["review_sha256"])
        self.assertEqual(result["status"], "published")
        self.assertTrue(all(item["matches_candidate"] for item in result["reopened"]))
        self.assertTrue(safe_path(self.root, "control_records/ontology/receipts/" + value["revision"]["candidate"]["operation_id"] + ".json").exists())

    def test_invalid_definition_never_becomes_eligible(self):
        value = self.saved([record("missing-definition", definition="")])
        checked = validate_candidate(self.root, value["head"]["proposal_id"], expected_revision=1)
        self.assertFalse(checked["validation"]["eligible"])
        self.assertIn("missing_metadata", {f["code"] for f in checked["validation"]["findings"]})
        with self.assertRaises(OntologyError):
            decide(self.root, value["head"]["proposal_id"], expected_revision=1, decision="accept", reason="Model endorsement is insufficient.", validation_sha256=checked["head"]["validation_sha256"])

    def test_changed_target_and_sources_invalidate_exact_review(self):
        value = self.reviewed();authority = self.v2grant(value)
        (self.root / "SPECS.md").write_text("Changed source evidence.\n")
        with self.assertRaisesRegex(OntologyError, "changed after validation"):
            publish_revision(self.root, value["head"]["proposal_id"], authority, expected_revision=1, expected_review_sha256=value["head"]["review_sha256"])
        self.assertEqual(open_proposal(self.root, value["head"]["proposal_id"])["head"]["state"], "reviewed")

    def test_partial_receipt_retains_accepted_review_for_exact_recovery(self):
        value = self.reviewed();authority = self.v2grant(value)
        result = publish_revision(self.root, value["head"]["proposal_id"], authority, expected_revision=1, expected_review_sha256=value["head"]["review_sha256"], fail_at="after_commit")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["proposal"]["head"]["review_sha256"], value["head"]["review_sha256"])
        from ontology_publication import recover
        receipt = recover(self.root, value["revision"]["candidate"]["operation_id"], authority)
        self.assertEqual(receipt["status"], "complete")


if __name__ == "__main__":
    unittest.main()
