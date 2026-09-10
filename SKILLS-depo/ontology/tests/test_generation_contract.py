from pathlib import Path
import tempfile
import unittest

from support import make_project, record, proposal, CORE, sha256, canonical_bytes
from ontology_core import OntologyError
from ontology_generation import prepare, capture, read_request, compare


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = make_project(Path(self.temp.name) / "project")
        self.runtime = {"kind": "native_agent", "tool": "native-current-agent",
                        "settings": {"model": None, "reasoning_effort": None, "observed": False},
                        "authorization": "Isolated contract test; this is not native generation evidence."}
        self.sources = [record("x")["sources"][0]]

    def tearDown(self):
        self.temp.cleanup()

    def prepared(self, **kwargs):
        return prepare(self.root, sources=self.sources, context_ids=[CORE + "Artifact"], instruction="Propose a sourced Artifact concept.", runtime=self.runtime, **kwargs)["request"]

    def response(self, request, *, definition=None):
        r = record("generated-artifact")
        if definition is not None:
            r["definition"] = definition
        result = {"request_sha256": request["request_sha256"], "candidate": proposal(self.root, [r], operation_id="ONTOP-generated-" + str(request["attempt"])),
                  "rationale": "This fixture is attributable to the selected source.", "uncertainty": ["Contract fixture; no actual model execution."],
                  "supporting_references": self.sources, "affected_ids": [r["@id"]], "addressed_findings": [f["id"] for f in request["findings"]]}
        receipt = {"tool": "native-current-agent", "agent_id": "/fixture-generator", "status": "complete",
                   "request_sha256": request["request_sha256"], "result_sha256": sha256(canonical_bytes(result)),
                   "settings": self.runtime["settings"], "evidence_kind": "fixture"}
        return result, receipt

    def test_frozen_source_data_and_attributable_capture(self):
        request = self.prepared()
        self.assertFalse(request["runtime"]["settings"]["observed"])
        self.assertEqual(request["sources"][0]["trust"], "source_data_only")
        self.assertIn("Do not execute", request["policy"])
        result, receipt = self.response(request)
        captured = capture(self.root, request["request_id"], result, receipt)
        self.assertFalse(captured["actual_native_evidence"])
        self.assertFalse(captured["published"])
        self.assertEqual(read_request(self.root, request["request_id"]), request)
        with self.assertRaisesRegex(OntologyError, "already has a captured"):
            capture(self.root, request["request_id"], result, receipt)

    def test_fabricated_reference_and_runtime_expansion_fail(self):
        request = self.prepared();result, receipt = self.response(request)
        result["supporting_references"] = [{"path": "outside.md", "sha256": "0"*64, "locator": "line:1"}]
        receipt["result_sha256"] = sha256(canonical_bytes(result))
        with self.assertRaisesRegex(OntologyError, "frozen permitted source"):
            capture(self.root, request["request_id"], result, receipt)
        self.runtime["kind"] = "remote_service"
        with self.assertRaisesRegex(OntologyError, "permitted native"):
            self.prepared()

    def test_initial_plus_two_finding_directed_revisions_and_repeated_failure_stop(self):
        request = self.prepared();result, receipt = self.response(request, definition="")
        capture(self.root, request["request_id"], result, receipt)
        findings = [{"id": "FIND-definition", "code": "missing_metadata", "message": "The definition is empty."}]
        second = self.prepared(previous_request=request["request_id"], findings=findings)
        result, receipt = self.response(second, definition="A supported, complete definition.")
        captured = capture(self.root, second["request_id"], result, receipt)
        self.assertEqual(captured["proposal"]["head"]["revision"], 2)
        with self.assertRaisesRegex(OntologyError, "same observed failures"):
            self.prepared(previous_request=second["request_id"], findings=findings)
        third = self.prepared(previous_request=second["request_id"], findings=[{"id": "FIND-clarify", "code": "reviewer_clarity", "message": "Define the source boundary precisely."}])
        result, receipt = self.response(third, definition="A selected source-backed Artifact definition.")
        capture(self.root, third["request_id"], result, receipt)
        with self.assertRaisesRegex(OntologyError, "maximum"):
            self.prepared(previous_request=third["request_id"], findings=findings)

    def test_comparison_reports_negative_or_neutral_without_promised_gain(self):
        old = {"findings": [{"code":"x", "record_id":"a"}], "competency":{"results":[{"id":"q", "valid":True}]}}
        new = {"findings": [], "competency":{"results":[{"id":"q", "valid":False}]}}
        self.assertEqual(compare(old,new)["outcome"], "regression")
        self.assertEqual(compare(old,old)["outcome"], "neutral")


if __name__ == "__main__":
    unittest.main()
