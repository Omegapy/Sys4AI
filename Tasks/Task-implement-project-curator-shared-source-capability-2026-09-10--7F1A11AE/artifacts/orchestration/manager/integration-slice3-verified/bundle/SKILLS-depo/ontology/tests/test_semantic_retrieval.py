"""Semantic boundaries; actual pinned-model acceptance is recorded separately."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from support import core_id, make_project, write_json
from ontology_core import OntologyError, load_project
from ontology_retrieval import search, term
from ontology_semantic import _corpus, profile, search as semantic_search


class SemanticRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = make_project(Path(self.temp.name) / "project")

    def tearDown(self):
        self.temp.cleanup()

    def test_absent_profile_retains_lexical_and_exact_results(self):
        self.assertFalse(profile(self.root)[0]["enabled"])
        with patch("ontology_semantic._embed", side_effect=AssertionError("Exact lookup must not load a model")):
            self.assertEqual(search(self.root, "Task")["results"][0]["@id"], core_id("Task"))
            self.assertEqual(semantic_search(self.root, "Task")["results"][0]["match_reason"], "preferred_label")
            self.assertEqual(term(self.root, core_id("Task"))["results"][0]["@id"], core_id("Task"))
        self.assertEqual(search(self.root, "unfindablezzword")["status"], "no_match")

    def test_source_selection_excludes_memory_and_arbitrary_documents(self):
        p = load_project(self.root)
        for sources in (["MEMORY/notes.md"], ["outside.txt"], ["SPECS.md", "SPECS.md"]):
            with self.assertRaises(OntologyError):
                _corpus(p, sources)
        rows, _ = _corpus(p)
        self.assertTrue(rows)
        self.assertTrue(all(row["sources"] for row in rows))
        self.assertTrue(all(p.by_id[row["id"]]["lifecycle"] == "approved" for row in rows))

    def test_selected_neutral_profile_uses_only_the_dedicated_defaults(self):
        write_json(self.root / "ontology-advanced.yaml", {"schema_version": 1,
            "profiles": {"semantic": {"enabled": True}}, "extensions": [], "limits": {}})
        selected, _ = profile(self.root)
        self.assertEqual(selected["python"], ".venv-ontology-semantic/bin/python")
        self.assertEqual(selected["model_manifest"], ".sys4ai/ontology/semantic/model.json")
        self.assertFalse((self.root / ".venv-ontology-semantic").exists())

    def test_enabled_unavailable_profile_preserves_lexical_with_diagnostic(self):
        with patch("ontology_semantic.profile", return_value=({"enabled": True}, {})), \
             patch("ontology_semantic.load_index", side_effect=OntologyError("stale_semantic_index", "Inputs changed.")):
            result = search(self.root, "project artifact")
        self.assertFalse(result["semantic"]["used"])
        self.assertEqual(result["semantic"]["diagnostic"]["code"], "stale_semantic_index")
        self.assertTrue(result["results"])

    def test_frozen_queries_cannot_open_live_embeddings(self):
        p = load_project(self.root)
        p.frozen_packet = {"schema_version": 1}
        with patch("ontology_semantic._embed", side_effect=AssertionError("Live model was accessed")):
            result = search(p, "project artifact")
            self.assertTrue(result["results"])
            with self.assertRaises(OntologyError) as stopped:
                semantic_search(p, "project artifact")
        self.assertEqual(stopped.exception.code, "frozen_semantic_scope")


if __name__ == "__main__":
    unittest.main()
