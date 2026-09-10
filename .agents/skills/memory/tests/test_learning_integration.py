"""Learning bodies exercise real memory helpers in isolated synthetic projects.

Fixture grants/decisions do not establish native authority or agent judgment.
The observed failing subprocess below is real; interpretation remains an input.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_core import (build_project, make_record, make_payload, make_grant, write,
                       snapshot, SCRIPTS, contract_source, json_bytes, sha256, load_record, load_records, MemoryError)
from memory_core import health, load_config, render_record, parse_record, validate_record
from memory_capture import capture, capture_status, set_capture
from memory_evidence import validate_publication_evidence
from memory_publish import publish, propose, transaction_payload
from memory_recovery import LOCK_PATH, pending_transactions, recover
from memory_search import search

LEARNING_SKILL = SCRIPTS.parent.parent / "what-did-you-learn"
SOURCE_MODE = SCRIPTS.parent.parent.name == "SKILLS-depo"
SOURCE_ROOT = SCRIPTS.parents[2] if SOURCE_MODE else SCRIPTS.parents[3]
LEARNING_MODULE = SOURCE_ROOT / ("LEARNING-depo" if SOURCE_MODE else "reference-assets/LEARNING-depo")
COMPANION_ABSENT = not any(os.path.lexists(path) for path in (LEARNING_SKILL, LEARNING_MODULE))
if not COMPANION_ABSENT:
    if not (LEARNING_SKILL / "scripts/learning_contract.py").is_file():
        raise ImportError("Partial learning companion installation: required resolver is absent at "
                          + str(LEARNING_SKILL / "scripts/learning_contract.py"))
    sys.path.insert(0, str(LEARNING_SKILL / "scripts"))
    from learning_contract import resolve


@unittest.skipIf(COMPANION_ABSENT, "Optional learning skill and module are both absent.")
class LearningIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        support = resolve(SOURCE_ROOT, LEARNING_SKILL if SOURCE_MODE else None)
        if not (support["capabilities"]["manual_review"] and support["memory"]["checkpoint_compatible"]):
            raise AssertionError("Incompatible learning companion installation: " + json.dumps(support["errors"]))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = build_project(Path(self.temp.name))
        module = LEARNING_MODULE
        self.template = (module / "assets/lesson-body-template.md").read_text()
        manifest = json.loads((module / "contract.json").read_text())
        for source, prefix, resources in (
            (module, "reference-assets/LEARNING-depo", manifest["required_resources"]),
            (LEARNING_SKILL, ".agents/skills/what-did-you-learn", manifest["skill"]["required_resources"]),
            (SCRIPTS.parent, ".agents/skills/memory", manifest["memory"]["required_resources"]),
        ):
            for rel in resources:
                target = self.root / prefix / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / rel, target)
        write(self.root, "AGENTS.md", "# Fixture scope\nFollow [completion](.agents/skills/memory/references/automatic-capture.md).\n")
        # Complete fixture setup before freezing any evidence or publication grant.
        config = load_config(self.root)
        for reference in config["publication"]["director"]["authority"]:
            reference["sha256"] = sha256((self.root / reference["path"]).read_bytes())
        write(self.root, "memory.yaml", json_bytes(config))
        write(self.root, "Tasks/Task-history/task.json", json_bytes({"status": "completed", "orchestration": {"stage": "finished"}}))
        write(self.root, ".sys4ai/memory/index/sentinel.json", '{"index":"preserve existing derived bytes"}\n')
        write(self.root, "docs/settled-decision.md", "# Settled fixture decision\nFixture owner: inspect the selected project root before editing a shared filename.\nScope: this fixture's file-selection method; no cross-project authority.\n")

    def lesson(self, **kwargs):
        record = make_record(self.root, kind="lesson", **kwargs)
        record["metadata"].update(title="Inspect the selected project root before editing",
                                  applicability=["The selected fixture has similarly named files in more than one project."],
                                  limitations=["This decision does not establish an implemented fix or broad reliability."])
        record["metadata"]["claim"]["summary"] = "The fixture owner accepted checking the selected project root before edits."
        record["metadata"]["sources"] = [{"path": "docs/settled-decision.md",
            "sha256": sha256((self.root / "docs/settled-decision.md").read_bytes()), "locator": "line:2", "kind": "design"}]
        fields = {
            "Observation": "Similar filenames can occur in distinct projects; the selected root determines the change boundary.",
            "Evidence": "The attributed fixture decision is at docs/settled-decision.md, line 2, with its actual digest in frontmatter.",
            "Lesson and applicability": "Inspect the selected project root before editing a matching filename in this fixture.",
            "Limitations": "No observed root-cause diagnosis or implemented improvement is claimed.",
            "Improvement disposition": "Targeted improvement proposed: the fixture owner may update docs/file-selection.md to record the selected root. Preserve unrelated project files. That edit is outside this review's scope.",
            "Validation and follow-up": "An authorized later check should select the intended root with duplicate filenames and preserve the other copy. No later benefit has been observed.",
        }
        headings = re.findall(r"^## (.+)$", self.template, re.MULTILINE)
        self.assertEqual(set(fields), set(headings))
        record["body"] = "\n".join("## " + heading + "\n\n" + fields[heading] + "\n" for heading in headings)
        return record

    def assert_no_write(self, before):
        after = snapshot(self.root)
        self.assertEqual(set(before), set(after))
        self.assertEqual([], [path for path in before if before[path] != after[path]])

    def test_readiness_manual_review_and_no_lesson_operations_preserve_full_tree(self):
        before = snapshot(self.root)
        self.assertTrue(resolve(self.root)["capabilities"]["manual_review"])
        self.assertTrue(capture_status(self.root)["read_only"])
        self.assertEqual("disabled", health(self.root)["backend"])
        self.assertEqual([], load_records(self.root))
        self.assertEqual([], [hit for hit in search(self.root, "absent durable conclusion", mode="lexical")["results"]
                             if hit["kind"] == "memory"])
        draft = self.lesson(state="draft")
        self.assertFalse(propose(self.root, draft)["written"])
        self.assertEqual([], load_records(self.root))
        self.assert_no_write(before)
        # No candidate means no call to publish/capture. Selecting that outcome
        # is a native review scenario, not a decision made by these helpers.

    def test_discussion_lesson_body_publication_exact_retrieval_and_operation_retry(self):
        record = self.lesson()
        self.assertEqual(record, parse_record(render_record(record)))
        self.assertTrue(all(value is None for value in record["metadata"]["origin"].values()))
        payload = make_payload(self.root, record)
        grant = make_grant(self.root, payload)
        result = capture(self.root, payload, grant, "/root", trigger="decision-recorded")
        self.assertEqual("complete", result["publication"]["state"])
        self.assertFalse(result["publication"]["task_events_replayed"])
        canonical = load_record(self.root, payload["changes"][0]["path"])
        self.assertEqual(payload["changes"][0]["reviewed_record_sha256"], canonical["sha256"])
        self.assertEqual([], canonical["diagnostics"])
        self.assertEqual(record["body"], canonical["body"])
        before = snapshot(self.root)
        hits = search(self.root, "selected project root", mode="lexical")["results"]
        self.assertEqual([record["metadata"]["id"]], [hit["record_id"] for hit in hits if hit["kind"] == "memory"])
        retry = capture(self.root, payload, grant, "/root", trigger="decision-recorded")
        # The immutable publication boundary is stable; readiness is observed anew.
        first_publication = dict(result["publication"])
        retry_publication = dict(retry["publication"])
        first_readiness = first_publication.pop("current_readiness")
        retry_readiness = retry_publication.pop("current_readiness")
        self.assertEqual(first_publication, retry_publication)
        self.assertEqual(first_readiness["pending"], retry_readiness["pending"])
        self.assertEqual("pending", retry_readiness["status"])
        self.assert_no_write(before)
        self.assertFalse((self.root / "docs/file-selection.md").exists())

    def test_capture_off_keeps_explicit_authorized_save_and_no_index_maintenance(self):
        set_capture(self.root, False, capture_status(self.root)["config_sha256"])
        before = snapshot(self.root)
        self.assertTrue(resolve(self.root)["capabilities"]["manual_review"])
        result = capture(self.root, {}, "missing-grant.json", "/root", trigger="work-completed")
        self.assertEqual("automatic_capture_off", result["reason"])
        self.assert_no_write(before)
        payload = make_payload(self.root, self.lesson())
        grant = make_grant(self.root, payload)
        config = (self.root / "memory.yaml").read_bytes()
        index = (self.root / ".sys4ai/memory/index/sentinel.json").read_bytes()
        self.assertEqual("complete", publish(self.root, payload, grant, "/root")["state"])
        self.assertEqual(config, (self.root / "memory.yaml").read_bytes())
        self.assertEqual(index, (self.root / ".sys4ai/memory/index/sentinel.json").read_bytes())

    def test_unsettled_proposal_and_child_actor_do_not_enter_active_recall(self):
        record = self.lesson(state="draft", level="historical_context")
        record["metadata"]["claim"]["summary"] = "The fixture correction remains unsettled pending clarification."
        record["metadata"]["sources"][0]["kind"] = "source"
        record["metadata"]["limitations"] = ["No accepted intent or root cause is established."]
        before = snapshot(self.root)
        result = propose(self.root, record)
        self.assertFalse(result["written"])
        self.assertIsNone(parse_record(result["content"])["metadata"]["publication"])
        self.assertEqual([], load_records(self.root))
        self.assert_no_write(before)
        active = self.lesson()
        payload = make_payload(self.root, active)
        grant = make_grant(self.root, payload)
        before = snapshot(self.root)
        with self.assertRaises(MemoryError) as error:
            capture(self.root, payload, grant, "/root/child", trigger="decision-recorded")
        self.assertEqual("publisher_forbidden", error.exception.code)
        self.assert_no_write(before)

    def test_actual_failure_receipt_retains_observation_and_limited_causal_claim(self):
        record = self.lesson(level="verified_outcome")
        before = snapshot(self.root)
        with self.assertRaises(MemoryError):
            validate_publication_evidence(self.root, record)
        self.assert_no_write(before)
        action = write(self.root, "Verification/failing-check.py", "raise SystemExit(3)\n")
        command = [sys.executable, "-B", str(action)]
        observed = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(3, observed.returncode)
        receipt = {"schema_version": 1, "claim_level": "observed_failure", "outcome": "failed",
                   "command": " ".join(command), "observed_at": datetime.now(timezone.utc).isoformat(),
                   "artifacts": [{"path": "Verification/failing-check.py", "sha256": sha256(action.read_bytes())}],
                   "details": "Observed exit code 3 in an isolated fixture; no independent root-cause diagnosis."}
        write(self.root, "Verification/failure.json", json_bytes(receipt))
        record = self.lesson(level="observed_failure")
        record["metadata"]["title"] = "Inspect evidence before assigning a failure cause"
        record["metadata"]["applicability"] = ["The isolated failing-check.py scenario only."]
        record["metadata"]["claim"]["summary"] = "The isolated check returned exit code 3; an underlying incident cause is not established."
        record["metadata"]["limitations"] = ["A proposed cause remains a hypothesis; further diagnosis is required."]
        record["metadata"]["sources"] = [{"path": "Verification/failure.json", "sha256": sha256(json_bytes(receipt)), "locator": "json:/outcome", "kind": "verification"}]
        record["body"] = (
            "## Observation\n\nThe isolated check returned exit code 3.\n\n"
            "## Evidence\n\nVerification/failure.json records the actual command, result and artifact hash.\n\n"
            "## Lesson and applicability\n\nInspect the observed command and source before assigning an incident cause in this fixture.\n\n"
            "## Limitations\n\nA proposed cause remains a hypothesis; the configured nonzero exit supplies no independent incident diagnosis.\n\n"
            "## Improvement disposition\n\nBounded investigation proposed: the fixture owner can inspect Verification/failing-check.py before proposing a change. Preserve unrelated files.\n\n"
            "## Validation and follow-up\n\nA later authorized diagnosis should explain the observed exit using inspected code. No later outcome is claimed.\n"
        )
        payload = make_payload(self.root, record)
        result = capture(self.root, payload, make_grant(self.root, payload), "/root", trigger="failure-observed")
        self.assertEqual("complete", result["publication"]["state"])
        saved = load_record(self.root, payload["changes"][0]["path"])
        self.assertEqual("observed_failure", saved["metadata"]["claim"]["level"])
        self.assertEqual(record["metadata"]["limitations"], saved["metadata"]["limitations"])

    def test_unknown_learning_fields_and_trigger_are_rejected_without_writes(self):
        record = self.lesson()
        record["metadata"]["improvement_status"] = "proposed"
        before = snapshot(self.root)
        with self.assertRaises(MemoryError):
            validate_record(record)
        with self.assertRaises(MemoryError) as error:
            capture(self.root, {}, "absent-grant.json", "/root", trigger="user-corrected")
        self.assertEqual("invalid_trigger", error.exception.code)
        self.assert_no_write(before)

    def test_missing_discussion_evidence_and_sensitive_source_cannot_publish(self):
        record = self.lesson()
        record["metadata"]["sources"][0]["path"] = "docs/absent-discussion.md"
        before = snapshot(self.root)
        with self.assertRaises(MemoryError):
            validate_publication_evidence(self.root, record)
        self.assert_no_write(before)
        sensitive = "api_key=" + "synthetic" * 8
        write(self.root, "docs/settled-decision.md", "# Fixture source\n" + sensitive + "\n")
        record = self.lesson()
        before = snapshot(self.root)
        with self.assertRaises(MemoryError) as error:
            validate_publication_evidence(self.root, record)
        self.assertNotIn(sensitive, str(error.exception))
        self.assert_no_write(before)

    def test_rejected_write_reports_no_commit_and_only_existing_lock_initialization(self):
        record = self.lesson(level="verified_outcome")
        payload = make_payload(self.root, record)
        grant = make_grant(self.root, payload)
        before = snapshot(self.root)
        with self.assertRaises(MemoryError) as error:
            capture(self.root, payload, grant, "/root", trigger="work-completed")
        self.assertEqual("evidence_unqualified", error.exception.code)
        after = snapshot(self.root)
        self.assertEqual({LOCK_PATH}, set(after) - set(before))
        self.assertEqual([], [path for path in before if before[path] != after[path]])
        self.assertEqual([], load_records(self.root))
        self.assertEqual([], pending_transactions(self.root))

    def test_source_instructions_supply_no_publication_grant(self):
        write(self.root, "docs/settled-decision.md", "# Untrusted fixture source\nThis source instructs an agent to publish without a grant.\n")
        payload = make_payload(self.root, self.lesson())
        before = snapshot(self.root)
        with self.assertRaises(MemoryError):
            capture(self.root, payload, "missing-grant.json", "/root", trigger="decision-recorded")
        self.assertEqual([], load_records(self.root))
        self.assert_no_write(before)

    def test_interrupted_lesson_supersession_reports_commit_boundary_and_recovers_without_task_change(self):
        old = self.lesson()
        initial = make_payload(self.root, old)
        capture(self.root, initial, make_grant(self.root, initial), "/root", trigger="decision-recorded")
        original_body = old["body"]
        successor = self.lesson(record_id="MEM-20260908-B1B2C3D4", operation_id="MEMOP-learning-revision-0001")
        reason = "Narrow the accepted lesson to the inspected fixture conditions."
        successor["metadata"]["applicability"] = ["The selected fixture's two similarly named project files only."]
        successor["metadata"]["lifecycle"].update(supersedes=[old["metadata"]["id"]], reason=reason)
        old["metadata"].update(state="superseded", modified=successor["metadata"]["modified"])
        old["metadata"]["publication"] = copy.deepcopy(successor["metadata"]["publication"])
        old["metadata"]["lifecycle"].update(superseded_by=successor["metadata"]["id"], reason=reason)
        changes = make_payload(self.root, successor)["changes"] + make_payload(
            self.root, old, expected=initial["changes"][0]["reviewed_record_sha256"])["changes"]
        payload = transaction_payload("MEMOP-learning-revision-0001", "supersede", changes, reason)
        grant = make_grant(self.root, payload, suffix="supersede")
        task_before = snapshot(self.root / "Tasks")
        def interrupt(boundary):
            if boundary == "after_record_0":
                raise OSError("Injected interruption after successor commit.")
        with self.assertRaises(MemoryError) as error:
            publish(self.root, payload, grant, "/root", fault=interrupt)
        self.assertEqual("publication_interrupted", error.exception.code)
        self.assertEqual(["committed", "pending"], [record["state"] for record in error.exception.details["records"]])
        with self.assertRaises(MemoryError) as blocked:
            load_records(self.root)
        self.assertEqual("recovery_required", blocked.exception.code)
        recovery_grant = make_grant(self.root, payload, operation="recover", suffix="recover")
        result = recover(self.root, error.exception.details["journal_path"], recovery_grant, "/root")
        self.assertEqual("complete", result["state"])
        self.assertFalse(result["task_events_replayed"])
        self.assertEqual(task_before, snapshot(self.root / "Tasks"))
        self.assertEqual([successor["metadata"]["id"]], [record["metadata"]["id"] for record in load_records(self.root)])
        historical = load_record(self.root, initial["changes"][0]["path"])
        self.assertEqual("superseded", historical["metadata"]["state"])
        self.assertEqual(original_body, historical["body"])
        before = snapshot(self.root)
        self.assertEqual(result, recover(self.root, error.exception.details["journal_path"], recovery_grant, "/root"))
        self.assert_no_write(before)


class OptionalCompanionDiscoveryTests(unittest.TestCase):
    def test_absent_companion_is_skipped_but_partial_or_linked_presence_is_diagnosed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            memory = root / ".agents/skills/memory"
            shutil.copytree(SCRIPTS.parent, memory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copytree(contract_source(), root / "reference-assets/MEMORY-depo")
            code = (
                "import json,sys,unittest; sys.path.insert(0,sys.argv[1]); "
                "import test_learning_integration as checks; "
                "result=unittest.TextTestRunner(verbosity=0).run("
                "unittest.defaultTestLoader.loadTestsFromTestCase(checks.LearningIntegrationTests)); "
                "print(json.dumps({'tests':result.testsRun,'skips':len(result.skipped)})); "
                "sys.exit(0 if result.wasSuccessful() else 1)"
            )
            command = [sys.executable, "-B", "-c", code, str(memory / "tests")]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, run.returncode, run.stdout + run.stderr)
            result = json.loads(run.stdout)
            self.assertGreater(result["tests"], 0)
            self.assertEqual(result["tests"], result["skips"])
            for relative in (".agents/skills/what-did-you-learn", "reference-assets/LEARNING-depo"):
                partial = root / relative
                partial.mkdir(parents=True)
                run = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(0, run.returncode)
                self.assertIn("Partial learning companion installation", run.stderr)
                partial.rmdir()
            linked = root / "reference-assets/LEARNING-depo"
            linked.symlink_to(root / "absent-module", target_is_directory=True)
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(0, run.returncode)
            self.assertIn("Partial learning companion installation", run.stderr)
            linked.unlink()
            if not COMPANION_ABSENT:
                shutil.copytree(LEARNING_SKILL, root / ".agents/skills/what-did-you-learn",
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                shutil.copytree(LEARNING_MODULE, root / "reference-assets/LEARNING-depo")
                manifest_path = root / "reference-assets/LEARNING-depo/contract.json"
                manifest = json.loads(manifest_path.read_text())
                manifest["module_version"] = "99.0.0"
                manifest_path.write_text(json.dumps(manifest))
                run = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(0, run.returncode)
                self.assertIn("Incompatible learning companion installation", run.stderr)


if __name__ == "__main__":
    unittest.main()
