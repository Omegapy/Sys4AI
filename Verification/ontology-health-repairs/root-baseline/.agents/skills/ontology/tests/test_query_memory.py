"""Integration with the actual installed memory read/search/packet implementation."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from support import PACKAGE, add_records, core_id, make_project, project_id, record, write_json
from test_query_retrieval import manifest
from ontology_core import OntologyError, load_project, read_json, sha256
from ontology_knowledge import capability, knowledge
from ontology_memory import link_memory, read_links, search_memory

MEMORY = PACKAGE.parent / "memory"
sys.path.insert(0, str(MEMORY / "scripts"))
from memory_core import default_config, render_record


def setup_memory(root, identity="example"):
    shutil.copytree(MEMORY, root / ".agents/skills/memory", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    config = default_config(identity, "Ontology memory integration fixture")
    write_json(root / "memory.yaml", config)
    (root / "MEMORY").mkdir(exist_ok=True)
    (root / "README.md").write_text("# Project\nAccepted fixture design: Task manager recovery is explicit.\n")
    return config


def note(root, suffix="A1B2C3D4", body="Task manager failures retained ERROR-421 in historical evidence.", state="active"):
    r = {"metadata": {"schema_version": 1, "id": "MEM-20260908-" + suffix,
         "project_id": read_json(root / "memory.yaml")["project"]["id"], "type": "decision", "title": "Task manager recovery",
         "state": state, "created": "2026-09-08T12:00:00Z", "modified": "2026-09-08T12:00:00Z",
         "claim": {"level": "accepted_design", "summary": "Fixture historical design only."},
         "applicability": ["Disposable integration tests."], "limitations": ["No real native outcome asserted."], "confidence": "medium",
         "sources": [{"path": "README.md", "sha256": sha256(root / "README.md"), "locator": "line:2", "kind": "design"}],
         "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None},
         "lifecycle": {"supersedes": [], "superseded_by": None, "reason": "Retracted fixture." if state == "retracted" else None},
         "publication": None if state == "draft" else {"actor_id": "/root", "actor_kind": "director", "operation_id": "fixture", "approved_at": "2026-09-08T12:00:00Z"}},
         "body": body + "\n"}
    path = "MEMORY/" + r["metadata"]["id"] + ".md"
    (root / path).write_text(render_record(r))
    return path


class MemoryQueryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = make_project(Path(self.temp.name) / "project")
        self.config = setup_memory(self.root)
        self.note = note(self.root)

    def tearDown(self): self.temp.cleanup()

    def test_real_memory_search_expansion_source_separation_and_preservation(self):
        before = manifest(self.root)
        result = knowledge(self.root, "prior Task manager failures", intent="mixed")
        memory = [r for r in result["results"] if r["source_type"] == "historical_memory"]
        self.assertTrue(memory)
        self.assertEqual(memory[0]["path"], self.note)
        self.assertIn("ERROR-421", memory[0]["excerpt"])
        self.assertEqual(result["memory"]["mode"], "lexical")
        self.assertTrue(result["memory"]["expansion"]["concept_ids"])
        self.assertIn("ontology", {r["source_type"] for r in result["results"]})
        self.assertEqual(before, manifest(self.root))

    def test_unavailable_no_evidence_stale_and_identity_boundaries(self):
        self.assertEqual(search_memory(self.root, "ZZQ-no-history")["status"], "no_matching_historical_evidence")
        (self.root / "README.md").write_text("# Changed evidence\nCurrent bytes differ.\n")
        result = search_memory(self.root, "Task manager failures")
        self.assertFalse(result["results"])
        self.assertTrue(result["excluded"])
        cfg = read_json(self.root / "memory.yaml")
        cfg["project"]["id"] = "different-project"
        write_json(self.root / "memory.yaml", cfg)
        self.assertEqual(search_memory(self.root, "Task")["status"], "unavailable")
        (self.root / "memory.yaml").unlink()
        result = knowledge(self.root, "Task", intent="mixed")
        self.assertTrue(result["results"])
        self.assertEqual(result["memory"]["status"], "unavailable")

    def test_links_repeat_exact_versions_stale_detection_and_no_canonical_changes(self):
        canonical = {k: v for k, v in manifest(self.root).items() if not k.startswith(".sys4ai/")}
        first = link_memory(self.root, record_paths=[self.note], concept_queries=["Task", "qzx-unknown"])
        sidecar = self.root / ".sys4ai/ontology/links/memory-records.json"
        initial = sidecar.read_bytes()
        link_memory(self.root, record_paths=[self.note], concept_queries=["Task", "qzx-unknown"])
        self.assertEqual(initial, sidecar.read_bytes())
        links = read_links(self.root)
        self.assertEqual(links["status"], "current")
        self.assertEqual({r["status"] for r in links["results"]}, {"derived_association", "unmatched"})
        self.assertEqual(canonical, {k: v for k, v in manifest(self.root).items() if not k.startswith(".sys4ai/")})
        (self.root / self.note).write_text((self.root / self.note).read_text().replace("ERROR-421", "ERROR-422"))
        self.assertEqual(read_links(self.root)["status"], "stale")
        self.assertEqual(read_links(self.root)["results"], [])

    def test_sidecar_invalid_shape_and_tampering_are_not_evidence(self):
        link_memory(self.root, record_paths=[self.note], concept_queries=["Task"])
        sidecar = self.root / ".sys4ai/ontology/links/memory-records.json"
        value = read_json(sidecar)
        value["associations"][0]["concept_ids"] = [core_id("TRD")]
        write_json(sidecar, value)
        self.assertEqual(read_links(self.root)["status"], "stale")
        write_json(sidecar, {"kind": "derived-memory-concept-links", "project_id": "example"})
        with self.assertRaises(OntologyError) as error: read_links(self.root)
        self.assertEqual(error.exception.code, "invalid_sidecar")

    def test_drafts_child_sources_and_frozen_live_memory_are_excluded(self):
        note(self.root, "00000001", body="DRAFT-ONLY-SENTINEL", state="draft")
        child = self.root / "Projects/other"
        child.mkdir(parents=True)
        (child / "record.md").write_text("CHILD-ONLY-SENTINEL")
        self.assertFalse(search_memory(self.root, "DRAFT-ONLY-SENTINEL")["results"])
        self.assertFalse(search_memory(self.root, "CHILD-ONLY-SENTINEL")["results"])
        self.assertEqual(search_memory(self.root, "Task", frozen_ontology=True)["status"], "unavailable")

    def test_capability_discovers_installed_sources_without_invocation(self):
        cap = record("memory-cap", type_name="Capability", label="Fixture memory search")
        skill = record("memory-skill", type_name="Skill", label="Installed memory")
        relation = record("provides", kind="relation", type_name="OntologyConcept", subject=skill["@id"], predicate=core_id("providesCapability"), object=cap["@id"])
        add_records(self.root, [cap, skill, relation])
        cfg = read_json(self.root / "ontology.yaml")
        cfg["source_allowlist"].append(".agents/skills/memory/SKILL.md")
        write_json(self.root / "ontology.yaml", cfg)
        add_records(self.root, [record("memory-binding", kind="binding", entity=skill["@id"], binding_type="skill",
            sources=[{"path": ".agents/skills/memory/SKILL.md", "sha256": sha256(self.root / ".agents/skills/memory/SKILL.md"), "locator": "line:1"}])], binding=True)
        before = manifest(self.root)
        result = capability(self.root, "Fixture memory search")
        selected = next(r for r in result["results"] if r["@id"] == skill["@id"])
        self.assertFalse(selected["executed"])
        self.assertIn(".agents/skills/memory/SKILL.md", {s["path"] for s in selected["source_status"]})
        self.assertEqual(before, manifest(self.root))

    def test_exact_capability_precedes_unrelated_lexical_matches_and_keeps_provider(self):
        skill = record("memory-provider", type_name="Skill")
        relation = record("memory-provider-edge", kind="relation", type_name="OntologyConcept", subject=skill["@id"], predicate=core_id("providesCapability"), object=core_id("MemoryRetrieval"))
        add_records(self.root, [skill, relation, record("loose-capability", type_name="Capability", definition="Memory retrieval ontology operation.")])
        result = capability(self.root, "memory retrieval")
        self.assertEqual([r["@id"] for r in result["results"]], [core_id("MemoryRetrieval"), skill["@id"]])
        self.assertFalse(result["truncation"]["truncated"])

    def test_ambiguous_links_and_corrupt_sidecar_do_not_change_mixed_definitions(self):
        add_records(self.root, [record("alpha", aliases=["shared-link"], ambiguity_with=[project_id("beta")], scope_note="Alpha meaning."),
                                record("beta", aliases=["shared-link"], ambiguity_with=[project_id("alpha")], scope_note="Beta meaning.")])
        link_memory(self.root, record_paths=[self.note], concept_queries=["shared-link"])
        self.assertEqual(read_links(self.root)["results"][0]["status"], "ambiguous")
        write_json(self.root / ".sys4ai/ontology/links/memory-records.json", {"broken": True})
        result = knowledge(self.root, "Task", intent="mixed")
        self.assertEqual(result["associations_status"], "invalid")
        self.assertTrue(any(r.get("@id") == core_id("Task") for r in result["results"]))


if __name__ == "__main__": unittest.main()
