"""Focused Project-app identity, provenance, permission and adapter checks."""
from pathlib import Path
import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "scripts"))
from project_app_core import ProjectReader
from project_app_sources import AppError, read_bytes
from project_app_work import compatibility, detail


class ProjectAppReaders(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.put("project.json", {"project_id": "sample-project", "project_name": "Sample project", "purpose": "Read local research", "relative_path": "."})
        (self.root / "README.md").write_text("# Sample project\nA local research project.\n")
        digest = hashlib.sha256((self.root / "README.md").read_bytes()).hexdigest()
        section = {"text": "A local research project.", "sources": [{"path": "README.md", "sha256": digest}],
                   "reviewed_sha256": hashlib.sha256(b"A local research project.").hexdigest(), "reviewed_at": "2026-09-29T00:00:00Z"}
        self.config = {"schema_version": 1, "project_id": "sample-project", "home": {"purpose": section, "scope": section, "audience": section, "sections": []},
                       "documents": [{"title": "Project overview", "path": "README.md"}], "start_here": {"label": "Read the overview", "path": "README.md"}}
        self.put("project-app.json", self.config)
        self.reader = ProjectReader(self.root, PACKAGE)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def test_child_identity_provenance_revocation_and_preservation(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        first = self.reader.read("home")
        self.assertEqual(first["identity"]["id"], "sample-project")
        self.assertEqual(first["content"]["purpose"]["status"], "reviewed")
        second = self.reader.read("home")
        for key in ("purpose", "scope", "audience"):
            self.assertEqual(first["content"][key]["text"], second["content"][key]["text"])
            self.assertEqual(first["content"][key]["reviewed_sha256"], second["content"][key]["reviewed_sha256"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        handle = first["content"]["documents"][0]["source_id"]
        self.assertIn("local research", self.reader.read("source", {"source_id": handle})["text"])
        (self.root / "README.md").write_text("Changed source content.")
        self.assertEqual(self.reader.read("home")["content"]["purpose"]["status"], "review_needed")
        self.config["documents"] = []
        self.config["start_here"] = None
        self.put("project-app.json", self.config)
        revoked = self.reader.read("home")
        self.assertEqual(revoked["content"]["purpose"]["status"], "withheld")
        self.assertNotIn("A local research project", json.dumps(revoked))
        self.assertEqual(self.reader.read("source", {"source_id": handle})["status"], "unavailable")

    def test_optional_identity_failure_is_local_and_primary_change_revokes(self):
        self.put("ontology.yaml", {"project": {"id": "another-project", "root": "."}})
        self.assertEqual(self.reader.read("context")["status"], "ready")
        self.assertEqual(self.reader.read("knowledge")["status"], "unavailable")
        self.put("project.json", {"project_id": "changed", "project_name": "Changed"})
        self.assertEqual(self.reader.read("home")["issues"], ["identity_changed"])

    def test_no_path_traversal_symlink_hardlink_or_unknown_owner_execution(self):
        for path in ("../README.md", "/etc/passwd"):
            with self.assertRaises(AppError):
                read_bytes(self.root, path)
        os.symlink(self.root / "README.md", self.root / "alias.md")
        with self.assertRaises(AppError):
            read_bytes(self.root, "alias.md")
        os.link(self.root / "README.md", self.root / "hardlink.md")
        with self.assertRaises(AppError):
            read_bytes(self.root, "README.md")
        script = self.root / ".agents/skills/agent-task/scripts/task_state.py"
        script.parent.mkdir(parents=True)
        script.write_text("raise RuntimeError('MUST NOT EXECUTE')")
        with self.assertRaises(AppError):
            compatibility(self.reader, "task")
        self.assertFalse((self.root / "MUST NOT EXECUTE").exists())

    def test_public_task_projection_omits_native_material(self):
        identifier = "TASK-20260929-12345678"
        packet = {"continuation": {"task_id": identifier, "revision": 2, "description": "Build a reader", "status": "active", "current_summary": "Reader prepared", "definition_of_done": ["Read Home"], "relevant_files": [], "private_native_material": "DO_NOT_RETURN", "collaboration": {"count": 777}}}
        last_response = {"response_id": "RESP-0002", "sequence": 2, "created_at": "2026-09-29T00:00:00Z", "path": "responses/Task-Response-0002-2026-09-29T00-00-00Z.md", "supersedes_response_id": "RESP-0001", "authority_basis": "DO_NOT_RETURN", "native_count": 777}
        def owner(*args):
            return packet if args[2] == "continue" else {"task": {"name": "Build reader", "revision": 2, "last_response": last_response, "thread_refs": ["DO_NOT_RETURN"], "orchestration": {"count": 777}}}
        with patch("project_app_work.owner_read", side_effect=owner):
            result = detail(self.reader, identifier)
        serialized = json.dumps(result)
        self.assertNotIn("DO_NOT_RETURN", serialized)
        self.assertNotIn("777", serialized)
        self.assertEqual(result["item"]["criteria"], ["Read Home"])
        history = result["item"]["history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["response_id"], "RESP-0002")
        self.assertEqual(history[0]["sequence"], 2)
        self.assertEqual(history[0]["created_at"], "2026-09-29T00:00:00Z")
        self.assertEqual(history[0]["supersedes_response_id"], "RESP-0001")
        self.assertEqual(history[0]["recorded_path"], last_response["path"])
        self.assertIn("Earlier responses", history[0]["coverage"])
        plan_history = [{"revision": n, "action_id": "EDIT", "timestamp": "2026-09-29T00:00:00Z", "status_before": None, "status_after": "draft", "summary": "Recorded change", "authority_basis": "DO_NOT_RETURN", "affected_ids": ["DO_NOT_RETURN"], "native_count": 777} for n in range(1, 15)]
        with patch("project_app_work.owner_read", return_value={"data": {"canonical": {"history": plan_history}}}):
            planned = detail(self.reader, "PLAN-20260929-12345678")
        self.assertEqual([row["revision"] for row in planned["item"]["history"][1:]], list(range(3, 15)))
        self.assertIn("Earlier entries may be omitted", planned["item"]["history"][0]["coverage"])
        self.assertNotIn("DO_NOT_RETURN", json.dumps(planned))
        self.assertNotIn("777", json.dumps(planned))
        with patch("project_app_work.owner_read", return_value={"document": {}}):
            requirements = detail(self.reader, "TRD-20260929-12345678")
        self.assertIn("unavailable through the supported TRD show route", requirements["item"]["history"][0])

    def test_permission_change_during_read_discards_result(self):
        def changed():
            self.config["documents"] = []
            self.config["start_here"] = None
            self.put("project-app.json", self.config)
            return {"status": "ready", "content": {"text": "DO_NOT_RETURN"}}
        with patch.object(self.reader, "home", side_effect=changed):
            result = self.reader.read("home")
        self.assertEqual(result["issues"], ["permissions_changed"])
        self.assertNotIn("DO_NOT_RETURN", json.dumps(result))

    def test_real_memory_owner_exact_read_and_corpus_revocation(self):
        depot = PACKAGE.parents[1]
        manifest = json.loads((PACKAGE / "assets/project-app/owner-compatibility.json").read_text())
        for path, digest in manifest["owners"]["memory"]["files"].items():
            raw = (depot / path).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            dest = self.root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
        config = json.loads((depot / "MEMORY-depo/starter/memory.yaml").read_text())
        config["project"] = {"id": "sample-project", "name": "Sample project", "root": "."}
        self.put("memory.yaml", config)
        identifier = "MEM-20260929-12345678"
        timestamp = "2026-09-29T00:00:00Z"
        meta = {"schema_version": 1, "id": identifier, "project_id": "sample-project", "type": "lesson", "title": "A saved fixture finding", "state": "active",
                "created": timestamp, "modified": timestamp, "claim": {"level": "performed_work", "summary": "A fixture source was inspected."}, "applicability": ["This synthetic fixture"],
                "limitations": [], "confidence": "high", "sources": [{"path": "README.md", "sha256": hashlib.sha256((self.root / "README.md").read_bytes()).hexdigest(), "locator": "section:Sample project", "kind": "source"}],
                "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None}, "lifecycle": {"supersedes": [], "superseded_by": None, "reason": None},
                "publication": {"actor_id": "/fixture", "actor_kind": "director", "operation_id": "fixture-publication", "approved_at": timestamp}}
        folder = self.root / "MEMORY"
        folder.mkdir()
        record = folder / (identifier + ".md")
        record.write_text("---\n" + json.dumps(meta) + "\n---\nA saved fixture finding.\n")
        result = self.reader.read("memory", {"query": identifier})
        self.assertEqual(len(result.get("items", [])), 1, result)
        handle = result["items"][0]["source"]["source_id"]
        opened = self.reader.read("source", {"source_id": handle})
        self.assertEqual(opened["status"], "ready", opened)
        self.assertEqual(opened["metadata"]["applicability"], ["This synthetic fixture"])
        record.unlink()
        self.assertEqual(self.reader.read("source", {"source_id": handle})["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
