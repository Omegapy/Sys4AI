"""Observable query ordering, evidence and nonmutation contracts."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from support import PACKAGE, add_records, core_id, make_project, project_id, record, write_json
from ontology_core import OntologyError, canonical_bytes, load_project, read_json, sha256
from ontology_retrieval import human, read, search, term
from ontology_graph import neighbors, path
from ontology_knowledge import capability, current_sources, knowledge
from ontology_wiki import build_wiki, filename, render_wiki, validate_links
from check_ontology import run_checks


def manifest(root):
    return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = make_project(Path(self.temp.name) / "project")

    def tearDown(self):
        self.temp.cleanup()

    def test_stable_exact_alias_lexical_lifecycle_and_no_match(self):
        add_records(self.root, [record("loose", definition="Task work Task work.", lifecycle="draft"),
                                record("approved", label="Unambiguous", aliases=["precise alias"])])
        before = manifest(self.root)
        exact = term(self.root, "Task")
        self.assertEqual(exact["results"][0]["@id"], core_id("Task"))
        self.assertEqual(exact["results"][0]["match_reason"], "preferred_label")
        self.assertEqual(read(self.root, core_id("Task"))["results"][0]["match_reason"], "stable_id")
        self.assertEqual(term(self.root, "precise alias")["results"][0]["match_reason"], "alias")
        self.assertEqual(term(self.root, "qzxv-unmatched")["status"], "no_match")
        deprecated = term(self.root, "TaskRequirementDocument")["results"][0]
        self.assertEqual(deprecated["lifecycle"], "deprecated")
        self.assertEqual(deprecated["replacement"], core_id("TRD"))
        self.assertIn(core_id("Task"), human(exact))
        self.assertEqual(search(self.root, "Task"), search(self.root, "Task"))
        self.assertEqual(before, manifest(self.root))
        self.assertFalse((self.root / ".sys4ai").exists())

    def test_modeled_alias_ambiguity_returns_distinct_ids(self):
        add_records(self.root, [record("alpha", aliases=["shared"], ambiguity_with=[project_id("beta")], scope_note="Alpha fixture semantics."),
                                record("beta", aliases=["shared"], ambiguity_with=[project_id("alpha")], scope_note="Beta fixture semantics.")])
        result = term(self.root, "shared")
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual([r["@id"] for r in result["results"]], [project_id("alpha"), project_id("beta")])
        with self.assertRaises(OntologyError) as error:
            neighbors(self.root, "shared")
        self.assertEqual(error.exception.code, "ambiguous_term")

    def test_binding_freshness_and_current_operational_source(self):
        binding = record("task-source", kind="binding", type_name="Artifact", entity=core_id("Task"), binding_type="artifact")
        add_records(self.root, [binding], binding=True)
        self.assertIn("SPECS.md", [s["path"] for s in term(self.root, "Task")["results"][0]["source_status"]])
        (self.root / "SPECS.md").write_text("# Specification\n\nCurrent authority requires explicit owner approval.\n")
        before = manifest(self.root)
        self.assertEqual(term(self.root, "Task")["results"][0]["freshness"], "stale")
        current = current_sources(self.root, "Task")["results"][0]
        self.assertEqual(current["discrepancy"], "recorded_source_version_changed")
        self.assertIn("Current authority", current["excerpt"])
        self.assertNotEqual(current["sha256"], current["recorded_sha256"])
        self.assertEqual(before, manifest(self.root))

    def test_direction_cycles_path_and_serialized_bounds(self):
        rows = [record("a"), record("b"), record("c")]
        for number, (source, target) in enumerate((("a", "b"), ("b", "c"), ("c", "a"))):
            rows.append(record("edge" + str(number), kind="relation", type_name="OntologyConcept",
                               subject=project_id(source), predicate=core_id("relatedTo"), object=project_id(target)))
        add_records(self.root, rows)
        out = neighbors(self.root, "a", direction="outgoing", hops=1)
        self.assertEqual(out["results"][0]["object"], project_id("b"))
        self.assertEqual(out["results"][0]["direction"], "outgoing")
        incoming = neighbors(self.root, "a", direction="incoming", hops=1)
        self.assertEqual(incoming["results"][0]["subject"], project_id("c"))
        route = path(self.root, "a", "c", hops=2)
        self.assertEqual(route["status"], "ok")
        self.assertEqual(len(route["results"]), 2)
        self.assertEqual(path(self.root, "a", "c", hops=1)["status"], "no_path")
        self.assertEqual(len(neighbors(self.root, "a", hops=8)["results"]), 3)
        self.assertTrue(neighbors(self.root, "a", limit=1)["truncation"]["truncated"])
        bounded = search(self.root, "project", max_bytes=3000)
        self.assertLessEqual(len(canonical_bytes(bounded)), 3000)
        self.assertTrue(bounded["truncation"]["truncated"])
        with self.assertRaises(OntologyError): neighbors(self.root, "a", hops=9)

    def test_wiki_repeatability_navigation_and_edited_projection(self):
        first = render_wiki(self.root)
        self.assertEqual(first, render_wiki(self.root))
        task_page = first["ONTOLOGY/WIKI/" + filename(core_id("Task"))].decode()
        self.assertIn("TRD", task_page)
        self.assertIn("Canonical edit location", task_page)
        self.assertTrue(validate_links(self.root, first)["valid"])
        build_wiki(self.root)
        canonical = (self.root / "ONTOLOGY/modules/sys4ai-core/1.0.0/core.jsonld").read_bytes()
        page = self.root / "ONTOLOGY/WIKI/INDEX.md"
        page.write_text(page.read_text() + "\n[broken](missing.md)\n")
        self.assertFalse(validate_links(self.root)["valid"])
        with self.assertRaises(OntologyError) as error: build_wiki(self.root)
        self.assertEqual(error.exception.code, "generated_conflict")
        self.assertEqual(canonical, (self.root / "ONTOLOGY/modules/sys4ai-core/1.0.0/core.jsonld").read_bytes())

    def test_combined_entry_fails_structural_and_semantic_negative_independently(self):
        self.assertTrue(run_checks(self.root)["valid"])
        cfg = read_json(self.root / "ontology.yaml")
        cfg["competency_files"] = ["ONTOLOGY/modules/project/competency.json"]
        write_json(self.root / "ontology.yaml", cfg)
        write_json(self.root / cfg["competency_files"][0], {"schema_version": 1, "questions": [{"id": "negative", "intent": "definition", "query": "Task", "expected_ids": [core_id("TRD")]}]})
        result = run_checks(self.root)
        self.assertTrue(result["structural"]["valid"])
        self.assertFalse(result["competency"]["valid"])
        self.assertFalse(result["valid"])
        add_records(self.root, [record("invalid", definition="")])
        result = run_checks(self.root)
        self.assertFalse(result["structural"]["valid"])
        self.assertFalse(result["valid"])

    def test_all_cli_reads_preserve_missing_and_stale_generated_state(self):
        from ontology_build import compile_project
        cli = PACKAGE / "scripts/ontology.py"
        commands = [["health"], ["term", "Task"], ["search", "memory"], ["read", core_id("Task")],
                    ["neighbors", "Task"], ["path", "Task", "MemoryRecord"], ["validate"],
                    ["capability", "memory retrieval"], ["knowledge", "Task", "--intent", "current"]]
        for state in ("missing", "stale"):
            if state == "stale":
                compile_project(self.root)
                (self.root / ".sys4ai/ontology/compiled/index.json").write_text("{}\n")
            before = manifest(self.root)
            for command in commands:
                cp = subprocess.run([sys.executable, "-B", str(cli), "--project-root", str(self.root), *command], capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
                self.assertIsInstance(json.loads(cp.stdout), dict)
            self.assertEqual(before, manifest(self.root))


if __name__ == "__main__":
    unittest.main()
