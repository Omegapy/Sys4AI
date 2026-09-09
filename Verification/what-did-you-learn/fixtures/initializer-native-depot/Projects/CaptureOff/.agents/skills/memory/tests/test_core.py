"""Disposable-project contract, source, identity and read-only behavior tests."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from memory_paths import MemoryError, safe_read_bytes, safe_path, iter_corpus, corpus_allowed
from memory_core import (default_config, json_bytes, sha256, render_record, parse_record, validate_record,
                         validate_config, load_config, load_record, load_records, health, reject_sensitive, decode_json_yaml)
from memory_publish import transaction_payload


def contract_source():
    skill = SCRIPTS.parent
    if skill.parent.name == "SKILLS-depo":
        return skill.parent.parent / "MEMORY-depo"
    if skill.parent.name == "skills" and skill.parent.parent.name == ".agents":
        return skill.parents[2] / "reference-assets/MEMORY-depo"
    raise RuntimeError("Tests require the documented depot or adopted skill layout.")


def write(root, path, raw):
    target = root / path; target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw.encode() if isinstance(raw, str) else raw)
    return target


def build_project(root, project_id="sample-project"):
    root = Path(root).resolve(); root.mkdir(parents=True, exist_ok=True)
    for path in ("SOUL.md", "AGENTS.md", "ROLE.md"):
        write(root, path, "# Project Director governance\nLocal fixture scope for project memory.\n")
    write(root, "README.md", "# Fixture project\n")
    write(root, "docs/design.md", "# Approved design\nThe project uses bounded reusable records.\n")
    write(root, "MEMORY/README.md", "# Project memory\nNo learned starter records.\n")
    config = default_config(project_id, "Memory test project")
    config["publication"]["director"] = {"actor_id": "/root", "scope": ["MEMORY", "Verification", "control_records", ".sys4ai/memory"],
                                            "authority": [{"path": p, "sha256": sha256((root / p).read_bytes())} for p in ("SOUL.md", "AGENTS.md", "ROLE.md")]}
    write(root, "memory.yaml", json_bytes(config))
    source_contracts = contract_source()
    for rel in ("README.md", "policy.md", "publication-and-recovery.md", "schema/record-v1.json", "schema/config-v1.json"):
        write(root, "reference-assets/MEMORY-depo/" + rel, (source_contracts / rel).read_bytes())
    return root


def make_record(root, *, record_id="MEM-20260908-A1B2C3D4", operation_id="MEMOP-fixture-0001", state="active", kind="decision", level="accepted_design"):
    now = datetime.now(timezone.utc).isoformat()
    meta = {"schema_version": 1, "id": record_id, "project_id": load_config(root)["project"]["id"], "type": kind,
            "title": "Use bounded project records", "state": state, "created": now, "modified": now,
            "claim": {"level": level, "summary": "The accepted design uses bounded project records."},
            "applicability": ["This project and its current design."], "limitations": ["Design approval does not establish implementation."],
            "confidence": "high", "sources": [{"path": "docs/design.md", "sha256": sha256((root / "docs/design.md").read_bytes()), "locator": "line:2", "kind": "design"}],
            "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None},
            "lifecycle": {"supersedes": [], "superseded_by": None, "reason": None},
            "publication": None if state == "draft" else {"actor_id": "/root", "actor_kind": "director", "operation_id": operation_id, "approved_at": now}}
    return {"metadata": meta, "body": "# Design conclusion\nUse bounded, project-owned records.\n"}


def make_payload(root, record, *, operation="publish", reason="Reviewed project design.", expected=None, operation_id=None):
    operation_id = operation_id or record["metadata"]["publication"]["operation_id"]
    content = render_record(record)
    return transaction_payload(operation_id, operation, [{"path": "MEMORY/" + record["metadata"]["id"] + ".md",
        "expected_sha256": expected, "content": content, "reviewed_record_sha256": sha256(content)}], reason)


def make_grant(root, payload, *, operation=None, actor="/root", suffix="grant"):
    now = datetime.now(timezone.utc)
    grant = {"schema_version": 1, "grant_id": "grant-" + suffix, "project_id": load_config(root)["project"]["id"],
             "actor_id": actor, "actor_kind": "director", "operation": operation or payload["operation"],
             "payload_sha256": sha256(json_bytes(payload)), "config_sha256": sha256((root / "memory.yaml").read_bytes()),
             "scope": ["MEMORY"], "native_receipt": {"tool": "collaboration.list_agents", "result": {"agents": [{"agent_name": actor, "agent_status": "running"}]}},
             "observed_at": now.isoformat(), "expires_at": (now + timedelta(minutes=4)).isoformat(), "task": None,
             "reviewed_records": [{"path": c["path"], "sha256": c["reviewed_record_sha256"], "expected_sha256": c["expected_sha256"]} for c in payload["changes"]],
             "privacy_redaction": payload["operation"] == "redact"}
    rel = "control_records/" + suffix + ".json"; write(root, rel, json_bytes(grant)); return rel


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = build_project(Path(self.temp.name))

    def test_five_types_non_task_origins_and_roundtrip(self):
        for kind in ("decision", "finding", "experiment", "lesson", "handoff"):
            record = make_record(self.root, kind=kind, level="historical_context" if kind == "handoff" else "accepted_design")
            self.assertEqual(parse_record(render_record(record)), record)
            self.assertIsNone(validate_record(record)["metadata"]["origin"]["task_id"])

    def test_strict_yaml_and_invalid_records(self):
        for raw in ('schema_version: 1', '{"x":1,"x":2}', '{"x":NaN}', '[]'):
            with self.assertRaises(MemoryError): decode_json_yaml(raw)
        for key, value in (("schema_version", 2), ("id", "MEM-20260230-ABCDEF12"), ("type", "task"), ("state", "approved"), ("title", "TODO")):
            record = make_record(self.root); record["metadata"][key] = value
            with self.assertRaises(MemoryError): validate_record(record)
        record = make_record(self.root); record["metadata"]["modified"] = "2020-01-01T00:00:00Z"
        with self.assertRaises(MemoryError): validate_record(record)
        with self.assertRaises(MemoryError): validate_record(make_record(self.root), "another-project")
        for field in ("type", "state", "confidence"):
            record = make_record(self.root); record["metadata"][field] = []
            with self.assertRaises(MemoryError): validate_record(record)
        for field in ("claim", "origin", "lifecycle", "publication"):
            record = make_record(self.root); record["metadata"][field] = []
            with self.assertRaises(MemoryError): validate_record(record)

    def test_configuration_and_existing_initializer_ids(self):
        for identity in ("a", "abc-9", "a" * 100):
            validate_config(default_config(identity, "Project"))
        validate_config(default_config(), allow_template=True)
        with self.assertRaises(MemoryError): validate_config(default_config())
        for change in (lambda c: c.update(schema_version=2), lambda c: c["project"].update(root=".."),
                       lambda c: c["state"].update(index="/tmp/index"), lambda c: c["corpus"]["include"].append("Tasks/**"),
                       lambda c: c["backend"].update(semantic_enabled=True)):
            config = default_config("sample", "Sample"); change(config)
            with self.assertRaises(MemoryError): validate_config(config)

    def test_path_scope_hardlinks_symlinks_case_and_secrets(self):
        write(self.root, "Projects/child/README.md", "child sentinel")
        for rel in ("../outside", "Projects/child/README.md", "docs/../README.md", "docs//design.md", "docs/design.md/evil"):
            with self.assertRaises(MemoryError): safe_path(self.root, rel)
        os.symlink(self.root / "docs/design.md", self.root / "docs/alias.md")
        with self.assertRaises(MemoryError): safe_read_bytes(self.root, "docs/alias.md")
        os.link(self.root / "docs/design.md", self.root / "docs/hard.md")
        with self.assertRaises(MemoryError): safe_read_bytes(self.root, "docs/hard.md")
        write(self.root, "research/credentials.md", "credential sentinel")
        with self.assertRaises(MemoryError): safe_path(self.root, "research/credentials.md")
        with self.assertRaises(MemoryError): safe_path(self.root, "readme.md")

    @unittest.skipUnless(sys.platform == "darwin", "Finder aliases use Darwin extended attributes")
    def test_native_finder_alias_rejected_without_os_getxattr(self):
        import ctypes
        target = write(self.root, "docs/finder-alias.md", "Native alias metadata fixture.\n")
        value = bytearray(32); value[8:10] = (0x8000).to_bytes(2, "big")
        buffer = ctypes.create_string_buffer(bytes(value))
        libc = ctypes.CDLL(None, use_errno=True); setter = libc.setxattr
        setter.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p,
                           ctypes.c_size_t, ctypes.c_uint32, ctypes.c_int]
        setter.restype = ctypes.c_int
        self.assertEqual(setter(os.fsencode(target), b"com.apple.FinderInfo", buffer, 32, 0, 0x0001), 0)
        with self.assertRaises(MemoryError) as error: safe_read_bytes(self.root, "docs/finder-alias.md")
        self.assertEqual(error.exception.code, "unsafe_alias")

    def test_corpus_exclusions_and_zero_segment_glob(self):
        config = load_config(self.root)
        for rel in ("docs/one.md", "docs/deep/two.md", "research/paper.tex", "README.md"):
            self.assertTrue(corpus_allowed(rel, config)); write(self.root, rel, "permitted source")
        for rel in ("Tasks/task.md", "docs/Tasks/task.md", "docs/foo-depo/a.md", "research/.env", "research/Projects/child.md", "docs/Roles/a.md", "docs/build/a.md"):
            self.assertFalse(corpus_allowed(rel, config)); write(self.root, rel, "excluded sentinel")
        paths = [p.relative_to(self.root).as_posix() for p in iter_corpus(self.root, config)]
        self.assertIn("docs/one.md", paths); self.assertNotIn("docs/Tasks/task.md", paths)

    def test_claim_staleness_false_origin_and_current_role(self):
        record = make_record(self.root); path = "MEMORY/" + record["metadata"]["id"] + ".md"
        write(self.root, path, render_record(record)); self.assertEqual(load_record(self.root, path)["diagnostics"], [])
        write(self.root, "docs/design.md", "Changed design\n")
        self.assertEqual(load_record(self.root, path)["diagnostics"][0]["code"], "evidence_changed")
        record["metadata"]["origin"].update(task_id="TASK-20260908-1234ABCD", task_path="Tasks/Task-absent/task.json")
        write(self.root, path, render_record(record))
        self.assertIn("file_absent", [d["code"] for d in load_record(self.root, path)["diagnostics"]])

    def test_sensitive_content_is_rejected_without_echo(self):
        for content in ("api_key=" + "x" * 30, "-----BEGIN PRIVATE KEY-----\nabcdef", "<analysis>private</analysis>", "User: full text\nAssistant: full response", "Identifier 123-45-6789"):
            with self.assertRaises(MemoryError) as caught: reject_sensitive(content)
            self.assertNotIn(content, str(caught.exception))

    def test_read_routes_preserve_bytes_and_mtimes_backend_absent(self):
        record = make_record(self.root); path = "MEMORY/" + record["metadata"]["id"] + ".md"; write(self.root, path, render_record(record))
        before = snapshot(self.root)
        load_record(self.root, path); load_records(self.root); self.assertEqual(health(self.root)["backend"], "disabled")
        for args in (("read", path), ("validate",), ("health",)):
            run = subprocess.run([sys.executable, "-S", str(SCRIPTS / "memory.py"), "--project-root", str(self.root), *args], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(snapshot(self.root), before)
        (self.root / "memory.yaml").unlink(); before = snapshot(self.root)
        self.assertEqual(health(self.root)["status"], "absent"); self.assertEqual(snapshot(self.root), before)

    def test_health_reports_missing_adopted_contract_without_repair(self):
        (self.root / "reference-assets/MEMORY-depo/schema/record-v1.json").unlink()
        before = snapshot(self.root)
        self.assertEqual(health(self.root)["status"], "invalid")
        self.assertEqual(snapshot(self.root), before)


if __name__ == "__main__":
    unittest.main()
