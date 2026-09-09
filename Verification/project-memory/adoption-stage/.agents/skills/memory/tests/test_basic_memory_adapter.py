"""Dependency-absent contracts; these tests are not vendor pilot evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import basic_memory_adapter as adapter
import basic_memory_projection as projection
import memory_maintenance as maintenance
from memory_core import default_config, render_record
from memory_paths import MemoryError
from memory_search import collect_documents


class AdapterContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.config = default_config("pilot-a", "Pilot A")
        self.write("memory.yaml", json.dumps(self.config))
        self.write("README.md", "# Local retrieval\nERR-ALPHA-731 requires a second independent measurement.\n")
        self.write("docs/experiment.md", "# Thermal result\nPassive heat pipes keep a small spacecraft cool without a fan.\n")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, value):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(value if isinstance(value, bytes) else value.encode())
        return p

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.root.rglob("*") if p.is_file()}

    def project(self):
        docs, _ = collect_documents(self.root, self.config)
        files, manifest = projection.render_projection(self.root, self.config, docs)
        for name, raw in files.items():
            self.write(self.config["state"]["projection"] + "/" + name, raw)
        self.write(self.config["state"]["projection"] + "/manifest.json", projection.canonical_json(manifest))
        return docs, files, manifest

    def enable(self):
        self.config["backend"].update(enabled=True, semantic_enabled=True)
        self.write("memory.yaml", json.dumps(self.config))

    def note(self, kind, number, state="active"):
        stamp = "2026-09-08T00:00:00+00:00"
        meta = {"schema_version": 1, "id": f"MEM-20260908-{number:08X}", "project_id": "pilot-a",
                "type": kind, "title": kind + " chronology", "state": state, "created": stamp, "modified": stamp,
                "claim": {"level": "historical_context" if kind == "handoff" else "verified_outcome", "summary": "Fixture result"},
                "applicability": ["isolated fixture"], "limitations": ["Not project evidence"], "confidence": "high",
                "sources": [{"path": "README.md", "sha256": projection.digest((self.root / "README.md").read_bytes()), "locator": "README.md:1", "kind": "verification"}],
                "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None},
                "lifecycle": {"supersedes": [], "superseded_by": None, "reason": None},
                "publication": None if state == "draft" else {"actor_id": "/root", "actor_kind": "director", "operation_id": "fixture", "approved_at": stamp}}
        self.write("MEMORY/" + meta["id"] + ".md", render_record({"metadata": meta, "body": "Fixture approved meaning."}))
        return meta

    def test_disabled_and_missing_state_reads_preserve_bytes_and_mtimes(self):
        before = self.snapshot()
        with patch.object(adapter, "run_worker", side_effect=AssertionError("Must not start vendor")):
            self.assertEqual(adapter.health(self.root)["mode"], "lexical")
            self.assertFalse(adapter.query(self.root, "ERR-ALPHA-731")["available"])
        self.assertEqual(before, self.snapshot())
        self.enable()
        before = self.snapshot()
        self.assertFalse(adapter.query(self.root, "heat removal")["available"])
        self.assertEqual(before, self.snapshot())

    def test_projection_retains_all_five_metadata_types_and_chronology(self):
        expected = [self.note(kind, n) for n, kind in enumerate(["decision", "finding", "experiment", "lesson", "handoff"], 1)]
        before = self.snapshot()
        docs, _ = collect_documents(self.root, self.config)
        files, manifest = projection.render_projection(self.root, self.config, docs)
        actual = [e for e in manifest["entries"] if e["kind"] == "memory"]
        self.assertEqual([e["metadata"] for e in actual], expected)
        for e in actual:
            projected = json.loads(files[e["projection_path"]].decode().split("\n---\n")[0][4:])
            self.assertEqual(projected["sys4ai_metadata"], e["metadata"])
            self.assertEqual(projected["modified"], e["metadata"]["modified"])
        self.assertEqual(before, self.snapshot())

    def test_source_formats_keep_original_identity_and_locator(self):
        self.write("research/physics.tex", "\\section{Motion}\\label{eq:drag} F=ma")
        self.write("research/context.html", "<h1 id='thermal'>Thermal system</h1><p>heat pipe</p>")
        docs, files, manifest = self.project()
        for entry in manifest["entries"]:
            self.assertEqual(projection.digest((self.root / entry["path"]).read_bytes()), entry["sha256"])
            self.assertTrue(entry["segments"])
        self.assertEqual({e["path"] for e in manifest["entries"]}, {"README.md", "docs/experiment.md", "research/physics.tex", "research/context.html"})
        self.assertEqual(projection.verify_projection(self.root, self.config), manifest)

    def test_foreign_project_and_disallowed_alias_never_project(self):
        docs, _ = collect_documents(self.root, self.config)
        other = copy.deepcopy(docs[0]); other["path"] = "Projects/B/sentinel.md"
        with self.assertRaises(MemoryError):
            projection.render_projection(self.root, self.config, [other])
        (self.root / "docs/alias.md").symlink_to(self.root / "README.md")
        with self.assertRaises(MemoryError):
            collect_documents(self.root, self.config)

    def test_projection_rejects_backend_modified_metadata_and_unknown_file(self):
        docs, files, manifest = self.project()
        name = next(iter(files))
        self.write(self.config["state"]["projection"] + "/" + name, b"backend-mutated metadata")
        with self.assertRaises(MemoryError) as caught:
            projection.verify_projection(self.root, self.config)
        self.assertEqual(caught.exception.code, "projection_changed")
        self.write(self.config["state"]["projection"] + "/" + name, files[name])
        self.write(self.config["state"]["projection"] + "/unknown.txt", "sole durable copy")
        with self.assertRaises(MemoryError):
            maintenance._classified(self.root, self.config)

    def test_changed_source_and_new_lifecycle_are_rejected(self):
        self.note("lesson", 1)
        docs, files, manifest = self.project()
        self.write("README.md", "changed source")
        with self.assertRaises(MemoryError) as caught:
            projection.verify_projection(self.root, self.config)
        self.assertEqual(caught.exception.code, "projection_stale")

    def test_draft_is_not_ingested(self):
        self.note("lesson", 1, "draft")
        docs, files, manifest = self.project()
        self.assertTrue(all(e["kind"] == "source" for e in manifest["entries"]))

    def test_fake_transport_cannot_return_foreign_or_invented_content(self):
        self.enable()
        docs, files, manifest = self.project()
        entry = manifest["entries"][0]
        fake = {"ok": True, "results": [
            {"projection_path": "forbidden.md", "project_id": 1, "score": 900},
            {"projection_path": entry["projection_path"], "project_id": 2, "score": 800},
            {"projection_path": entry["projection_path"], "project_id": 1, "score": 0.8, "body": "injected", "metadata": {"state": "approved"}}]}
        with patch.object(adapter, "_read_certificate", return_value=({}, {"profile_sha256": "a"*64}, manifest)), patch.object(adapter, "run_worker", return_value=fake):
            result = adapter.query(self.root, "thermal")
        self.assertTrue(result["available"])
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["sha256"], entry["sha256"])
        self.assertNotIn("body", result["results"][0])
        self.assertNotIn("metadata", result["results"][0])

    def test_packet_filter_is_applied_after_backend_ranking(self):
        self.enable()
        docs, files, manifest = self.project()
        fake = {"results": [{"projection_path": e["projection_path"], "project_id": 1, "score": 1.0} for e in manifest["entries"]]}
        with patch.object(adapter, "_read_certificate", return_value=({}, {"profile_sha256": "a"*64}, manifest)), patch.object(adapter, "run_worker", return_value=fake), patch("memory_packet.filter_documents", return_value=[]):
            result = adapter.query(self.root, "thermal", packet={"path": "frozen.json", "sha256": "a"*64})
        self.assertEqual(result["results"], [])

    def test_wrong_query_mode_and_writer_operation_rejected(self):
        for mode in ("write_note", "delete_note", "project", "config", "cloud", "reindex"):
            with self.assertRaises(MemoryError):
                adapter.query(self.root, "payload", mode=mode)
        self.assertEqual(adapter.OPERATIONS, ("search", "health"))

    def test_changed_profile_or_backend_outage_degrades_without_repair(self):
        self.enable()
        before = self.snapshot()
        with patch.object(adapter, "_read_certificate", side_effect=MemoryError("backend_profile_changed", "changed")):
            response = adapter.query(self.root, "thermal")
        self.assertFalse(response["available"])
        self.assertEqual(response["limitations"], ["backend_profile_changed"])
        self.assertEqual(before, self.snapshot())

    def test_pending_maintenance_is_reported_without_mutation(self):
        self.write(self.config["state"]["maintenance"] + "/backend-one.json", json.dumps({"schema_version": 1, "operation": "reindex", "status": "failed"}))
        before = self.snapshot()
        self.assertEqual(len(maintenance.pending_reindexes(self.root, self.config)), 1)
        self.assertEqual(before, self.snapshot())

    def test_maintenance_rejects_missing_authority_before_creating_state(self):
        source = Path(__file__).resolve().parents[3] / "MEMORY-depo/profiles/basic-memory-v0.23.0.json"
        self.write(self.config["contract_root"] + "/profiles/basic-memory-v0.23.0.json", source.read_bytes())
        payload = maintenance.reindex_payload(self.root)
        before = self.snapshot()
        with self.assertRaises(MemoryError):
            maintenance.reindex(self.root, grant_file="grant.json", actor="/root", expected_payload_sha256=projection.digest(projection.canonical_json(payload)))
        self.assertEqual(before, self.snapshot())

    def test_interrupted_build_leaves_recoverable_receipt_and_canonical_bytes(self):
        source = Path(__file__).resolve().parents[3] / "MEMORY-depo/profiles/basic-memory-v0.23.0.json"
        self.write(self.config["contract_root"] + "/profiles/basic-memory-v0.23.0.json", source.read_bytes())
        payload = maintenance.reindex_payload(self.root)
        before = {k: v for k, v in self.snapshot().items() if not k.startswith(".sys4ai/")}
        with patch("memory_publish.authorize"), patch.object(adapter, "_model_directory", return_value=self.root), patch.object(adapter, "run_worker", side_effect=MemoryError("controlled_outage", "Interrupted fixture worker")):
            with self.assertRaises(MemoryError):
                maintenance.reindex(self.root, grant_file="grant.json", actor="/root", expected_payload_sha256=projection.digest(projection.canonical_json(payload)))
            pending = maintenance.pending_reindexes(self.root, self.config)
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["status"], "failed")
            result = maintenance.recover_reindex(self.root, pending[0]["operation_id"], grant_file="grant.json", actor="/root")
        self.assertEqual(result["status"], "aborted")
        self.assertEqual(before, {k: v for k, v in self.snapshot().items() if not k.startswith(".sys4ai/")})
        self.assertEqual(maintenance.pending_reindexes(self.root, self.config), [])

    def test_query_worker_python_guard_denies_write_and_network(self):
        code = """import sys,socket,pathlib
sys.path.insert(0, sys.argv[1])
from basic_memory_adapter import _audit_guard
_audit_guard()
blocked=[]
for label, action in [('write',lambda:pathlib.Path(sys.argv[2]).write_text('bad')),('network',lambda:socket.getaddrinfo('example.com',443))]:
    try: action()
    except PermissionError: blocked.append(label)
assert blocked == ['write','network'], blocked
"""
        result = subprocess.run([sys.executable, "-B", "-c", code, str(Path(adapter.__file__).parent), str(self.root / "write-attempt")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "write-attempt").exists())

    def test_matching_shape_cache_still_requires_completed_ownership_receipt(self):
        docs, _ = collect_documents(self.root, self.config)
        document = docs[0]
        name = projection.digest(document["path"].encode()) + ".json"
        self.write(self.config["state"]["normalized"] + "/" + name,
                   projection.canonical_json({"schema_version": 1, "normalization_version": "normalization-1", "document": document}))
        with self.assertRaises(MemoryError) as caught:
            maintenance._classified(self.root, self.config)
        self.assertEqual(caught.exception.code, "unclassified_state")

    def test_unknown_empty_directory_blocks_replacement(self):
        (self.root / self.config["state"]["index"] / "unclassified").mkdir(parents=True)
        with self.assertRaises(MemoryError):
            maintenance._classified(self.root, self.config)


if __name__ == "__main__":
    unittest.main()
