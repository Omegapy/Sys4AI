"""Index integrity, stale inputs and no implicit rebuild at public read boundaries."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from support import make_project, write_json
from ontology_core import OntologyError, load_project, read_json, sha256
from ontology_semantic import INDEX, PACKAGE, build_index, load_index


class SemanticIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = make_project(Path(self.temp.name) / "project")
        write_json(self.root / "ontology-advanced.yaml", {"schema_version": 1, "extensions": [], "limits": {},
                   "profiles": {"semantic": {"enabled": True, "python": ".venv-ontology-semantic/bin/python",
                                             "model_manifest": ".sys4ai/ontology/semantic/model.json"}}})
        self.model = {"dimension": 384, "revision": "unit-fixture"}
        self.runtime = {"model": self.model, "packages": {"fastembed": "0.8.0"},
                        "worker_sha256": sha256(PACKAGE / "scripts/ontology_semantic_worker.py"),
                        "requirements_sha256": sha256(PACKAGE / "requirements-semantic.txt"),
                        "truncated_inputs": [], "offline": True}

    def tearDown(self):
        self.temp.cleanup()

    def build(self, side_effect=None):
        def embed(root, texts, **kwargs):
            if side_effect: side_effect()
            return [[1.0] + [0.0]*383 for text in texts], self.runtime
        with patch("ontology_semantic._embed", side_effect=embed):
            return build_index(self.root)

    def test_explicit_build_and_read_does_not_rebuild(self):
        self.assertEqual(self.build()["status"], "built")
        raw = (self.root / INDEX).read_bytes()
        with patch("ontology_semantic.model_context", return_value=self.model), \
             patch("ontology_semantic.backend_versions", return_value=self.runtime["packages"]), \
             patch("ontology_semantic._embed", side_effect=AssertionError("Index read must not embed")):
            self.assertTrue(load_index(load_project(self.root))["rows"])
        self.assertEqual(raw, (self.root / INDEX).read_bytes())

    def test_changed_profile_is_stale_and_saved_matrix_is_preserved(self):
        self.build(); raw = (self.root / INDEX).read_bytes()
        cfg = read_json(self.root / "ontology-advanced.yaml")
        cfg["limits"] = {"query_seconds": 5}
        write_json(self.root / "ontology-advanced.yaml", cfg)
        with self.assertRaises(OntologyError) as stale:
            load_index(load_project(self.root))
        self.assertEqual(stale.exception.code, "stale_semantic_index")
        self.assertEqual(raw, (self.root / INDEX).read_bytes())

    def test_changed_inputs_during_build_do_not_publish(self):
        def change():
            cfg = read_json(self.root / "ontology.yaml")
            cfg["project"]["purpose"] = "Changed after source selection."
            write_json(self.root / "ontology.yaml", cfg)
        with self.assertRaises(OntologyError) as stale:
            self.build(change)
        self.assertEqual(stale.exception.code, "source_changed")
        self.assertFalse((self.root / INDEX).exists())

    def test_forged_or_nonfinite_vectors_are_rejected(self):
        self.build()
        value = read_json(self.root / INDEX)
        value["vectors"][0] = [0.1]
        write_json(self.root / INDEX, value)
        with patch("ontology_semantic.model_context", return_value=self.model), \
             patch("ontology_semantic.backend_versions", return_value=self.runtime["packages"]):
            with self.assertRaises(OntologyError) as invalid:
                load_index(load_project(self.root))
        self.assertEqual(invalid.exception.code, "invalid_semantic_index")


if __name__ == "__main__":
    unittest.main()
