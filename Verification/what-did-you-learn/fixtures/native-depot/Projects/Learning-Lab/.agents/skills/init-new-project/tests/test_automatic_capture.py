"""New installation defaults, actual installed capture, opt-out, and old receipts."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_initializer as fixture


class AutomaticCaptureEditionTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def cli(self, *args):
        result = subprocess.run([sys.executable, "-B", str(self.target / ".agents/skills/memory/scripts/memory.py"),
                                 "--project-root", str(self.target), *args], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_existing_project_first_install_is_on_and_binds_preserved_governance(self):
        self.target.mkdir()
        raw = b"# Existing project instructions\nPreserve the product's content.\n"
        (self.target / "AGENTS.md").write_bytes(raw)
        report = self.run_setup(mode="prepare-existing")
        self.assertEqual("on", report["memory_capture"]["status"])
        self.assertIsNotNone(report["memory_capture"]["opt_out_question"])
        final_governance = raw + self.helper.completion_link()
        self.assertEqual(final_governance, (self.target / "AGENTS.md").read_bytes())
        config = json.loads((self.target / "memory.yaml").read_text())
        self.assertTrue(config["integration"]["automatic_capture"])
        authority = {ref["path"]: ref["sha256"] for ref in config["publication"]["director"]["authority"]}
        self.assertEqual(self.helper.sha(final_governance), authority["AGENTS.md"])
        self.assertEqual(["MEMORY", "control_records/memory", ".sys4ai/memory"], config["publication"]["director"]["scope"])

    def test_opt_out_survives_completed_setup_rerun_and_preserves_notes(self):
        first = self.run_setup()
        note = self.target / "MEMORY/local.txt"; note.write_bytes(b"Existing learned content")
        state = self.cli("capture-status")
        self.cli("set-capture", "off", "--expected-config-sha256", state["config_sha256"])
        before = (self.target / "memory.yaml").read_bytes()
        repeated = self.run_setup()
        self.assertEqual("off", repeated["memory_capture"]["status"])
        self.assertIsNone(repeated["memory_capture"]["opt_out_question"])
        self.assertEqual(before, (self.target / "memory.yaml").read_bytes())
        self.assertEqual(b"Existing learned content", note.read_bytes())
        self.assertEqual(first["sources"], repeated["sources"])

    def test_pristine_manual_template_configuration_is_specialized_once(self):
        self.target.mkdir()
        original = (self.root / self.helper.TEMPLATE / "memory.yaml").read_bytes()
        (self.target / "memory.yaml").write_bytes(original)
        report = self.run_setup(mode="prepare-existing")
        self.assertEqual("on", report["memory_capture"]["status"])
        config = json.loads((self.target / "memory.yaml").read_text())
        self.assertEqual("orchard", config["project"]["id"])
        self.assertEqual(self.helper.sha(original), report["preserved_memory"]["memory.yaml"])
        entry = next(e for e in report["sources"] if e["destination"] == "memory.yaml")
        self.assertEqual("specialized", entry["adoption"])
        self.run_setup(mode="prepare-existing")

    def test_incompatible_preserved_memory_has_no_false_on_notice(self):
        self.target.mkdir()
        (self.target / "memory.yaml").write_text("legacy: project-owned\n")
        report = self.run_setup(mode="prepare-existing")
        self.assertEqual("unavailable", report["memory_capture"]["status"])
        self.assertIsNone(report["memory_capture"]["opt_out_question"])
        self.assertEqual("legacy: project-owned\n", (self.target / "memory.yaml").read_text())

    def test_first_capture_through_newly_installed_cli(self):
        report = self.run_setup()
        self.assertEqual("on", report["memory_capture"]["status"])
        # Native receipts below are explicit test fixtures, not live-agent proof.
        from hashlib import sha256
        digest = lambda raw: sha256(raw).hexdigest()
        source = b"# Accepted design\nKeep learned knowledge local to this project.\n"
        (self.target / "docs").mkdir(); (self.target / "docs/design.md").write_bytes(source)
        now = datetime.now(timezone.utc); stamp = now.isoformat()
        meta = {"schema_version": 1, "id": "MEM-20260908-ABC12345", "project_id": "orchard",
                "type": "decision", "title": "Keep project knowledge local", "state": "active", "created": stamp, "modified": stamp,
                "claim": {"level": "accepted_design", "summary": "Keep learned knowledge local to this project."},
                "applicability": ["This project"], "limitations": ["Design evidence only"], "confidence": "high",
                "sources": [{"path": "docs/design.md", "sha256": digest(source), "locator": "line:2", "kind": "design"}],
                "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None},
                "lifecycle": {"supersedes": [], "superseded_by": None, "reason": None},
                "publication": {"actor_id": "/root", "actor_kind": "director", "operation_id": "MEMOP-initialized-0001", "approved_at": stamp}}
        content = b"---\n" + self.helper.encoded(meta) + b"---\n# Local knowledge\nKeep learned knowledge local.\n"
        payload = {"operation_id": "MEMOP-initialized-0001", "operation": "publish", "reason": "Record accepted project decision.",
                   "changes": [{"path": "MEMORY/MEM-20260908-ABC12345.md", "expected_sha256": None,
                                "content": content.decode(), "reviewed_record_sha256": digest(content)}]}
        # Payload content uses the same string representation as transaction_payload.
        grant = {"schema_version": 1, "grant_id": "initialized-test-grant", "project_id": "orchard", "actor_id": "/root", "actor_kind": "director",
                 "operation": "publish", "payload_sha256": digest(self.helper.encoded(payload)), "config_sha256": digest((self.target / "memory.yaml").read_bytes()),
                 "scope": ["MEMORY"], "native_receipt": {"tool": "collaboration.list_agents", "result": {"agents": [{"agent_name": "/root", "agent_status": "running"}]}},
                 "observed_at": stamp, "expires_at": (now + timedelta(minutes=4)).isoformat(), "task": None,
                 "reviewed_records": [{"path": payload["changes"][0]["path"], "sha256": digest(content), "expected_sha256": None}], "privacy_redaction": False}
        for name, value in (("payload", payload), ("grant", grant)):
            path = self.target / f"control_records/memory/{name}.json"; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(self.helper.encoded(value))
        result = self.cli("capture", "control_records/memory/payload.json", "--trigger", "work-completed",
                          "--grant-file", "control_records/memory/grant.json", "--actor", "/root")
        self.assertEqual("captured", result["status"])
        self.assertEqual(content, (self.target / "MEMORY/MEM-20260908-ABC12345.md").read_bytes())

    def test_v5_receipt_recovers_and_keeps_original_off_configuration(self):
        template = self.root / self.helper.TEMPLATE
        fixture.remove_learning_edition(template)
        config_path = template / "memory.yaml"; current = config_path.read_bytes()
        config = json.loads(current); config["integration"]["automatic_capture"] = False
        config_path.write_bytes(self.helper.encoded(config))
        identity = {"schema_version": 1, "project_id": "orchard", "project_name": "Orchard",
                    "purpose": self.arguments["purpose"], "relative_path": "Projects/Orchard"}
        proposed, sources, original = self.helper.source_snapshot(self.root, fixture.SOURCE_SKILL, identity, contract=self.helper.MEMORY_CONTRACT)
        for entry in sources:
            name = entry["destination"]
            entry["adoption"] = "specialized" if name in self.helper.SPECIALIZED_FILES and proposed[name] != original.get(name) else "adopted"
        record = {"schema_version": 1, "setup_contract": self.helper.MEMORY_CONTRACT, "status": "partial", "mode": "create",
                  "operation_id": "project-setup-" + "5" * 32, "identity": identity, "project_root": str(self.target), "sources": sources,
                  "owned_files": {name: self.helper.sha(raw) for name, raw in proposed.items()}, "preserved_files": {}, "preserved_licenses": {}, "preserved_memory": {},
                  "recovery_before": {name: None for name in proposed}, "completed_stages": [], "active_stage": "assets", "checks": [],
                  "created_at": "2026-09-08T00:00:00+00:00", "git_setup": "separate"}
        receipt = self.target / self.helper.RECORD; receipt.parent.mkdir(parents=True); receipt.write_bytes(self.helper.encoded(record))
        first = self.run_setup(); before = (self.target / "memory.yaml").read_bytes()
        config_path.write_bytes(current)
        repeated = self.run_setup()
        self.assertEqual("governance-starter-v5", repeated["setup_contract"])
        self.assertEqual("off", repeated["memory_capture"]["status"])
        self.assertEqual(before, (self.target / "memory.yaml").read_bytes())
        self.assertEqual(first["sources"], repeated["sources"])


if __name__ == "__main__": unittest.main()
