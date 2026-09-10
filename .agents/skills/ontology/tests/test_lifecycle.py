import copy
import unittest
from support import record,project_id,core_id
from ontology_lifecycle import transition,validate_transition
from ontology_core import OntologyError


class LifecycleTests(unittest.TestCase):
    def test_draft_approval_and_deprecation_preserve_id_and_history(self):
        draft=record("meaning",lifecycle="draft")
        approved=transition(draft,"approved",reason="Accept reviewed meaning")
        deprecated=transition(approved,"deprecated",reason="Use replacement",replacement=core_id("Artifact"))
        self.assertEqual(deprecated["@id"],draft["@id"])
        self.assertEqual(len(deprecated["history"]),2)
        self.assertEqual(validate_transition([approved],[deprecated]),[])
        with self.assertRaises(OntologyError):transition(deprecated,"approved",reason="Reuse old identity")

    def test_approved_meaning_change_needs_renewed_review(self):
        old=record("meaning");changed=copy.deepcopy(old);changed["definition"]="Different meaning"
        self.assertEqual(validate_transition([old],[changed])[0]["code"],"renewed_review_required")
        reviewed=transition(old,"approved",reason="Explicitly review revised semantics")
        reviewed["definition"]="Refined meaning"
        self.assertEqual(validate_transition([old],[reviewed]),[])

    def test_removal_or_type_recycling_is_rejected(self):
        old=record("meaning")
        self.assertEqual(validate_transition([old],[])[0]["code"],"identity_removed")
        changed=copy.deepcopy(old);changed["@type"]=[core_id("Skill")]
        self.assertIn("identity_recycled",{d["code"] for d in validate_transition([old],[changed])})

    def test_suggestion_transition_produces_candidate_without_mutating_input(self):
        old=record("meaning");original=copy.deepcopy(old)
        draft=transition(old,"draft",reason="Provisional suggestion")
        draft["definition"]="Candidate refinement"
        self.assertEqual(old,original)
        self.assertEqual(validate_transition([old],[draft]),[])


if __name__ == "__main__":unittest.main()
