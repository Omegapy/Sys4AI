"""Contract, unit, fault-injection, and cold-process tests for Task state."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import re
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "task_state.py"
SOURCE_LAYOUT = SKILL_ROOT.parent.name == "SKILLS-depo"
PROJECT_ROOT = SKILL_ROOT.parent.parent if SOURCE_LAYOUT else Path(__file__).resolve().parents[4]
WORKFLOW_ROOT = Path(os.environ["SYS4AI_WORKFLOW_ROOT"]).resolve() if os.environ.get("SYS4AI_WORKFLOW_ROOT") else None


def document_path(relative):
    """Read this package's source or installed context; explicit overlays may omit unchanged files."""
    if SOURCE_LAYOUT:
        if relative.startswith(".agents/skills/"):
            mapped = "SKILLS-depo/" + relative.removeprefix(".agents/skills/")
        else:
            mapped = {"AGENTS.md":"AGENTS-depo/project-template-AGENTS.md", "ROLE.md":"ROLES-depo/project-director-ROLE.md"}.get(relative, relative)
    else:
        mapped = relative
    if WORKFLOW_ROOT is not None and (WORKFLOW_ROOT / mapped).exists():
        return WORKFLOW_ROOT / mapped
    return PROJECT_ROOT / mapped


SPEC = importlib.util.spec_from_file_location("task_state", SCRIPT)
assert SPEC and SPEC.loader
task_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task_state)


class TaskStateTests(unittest.TestCase):
    maxDiff = None

    def test_native_version_requires_explicit_enable_without_touching_history(self):
        _,folder=self.create_task('Preserved historical Task')
        historical=(folder/'task.json').read_bytes();before=self.tree_hash()
        payload={'name':'Unselected native Task','description':'Check explicit version selection.',
                 'definition_of_done':['No implicit native execution.'],'orchestration_version':2}
        for enabled in (None,False):
            candidate=dict(payload)
            if enabled is not None:candidate['orchestration_enabled']=enabled
            completed,result=self.run_cli('new',payload=candidate)
            self.assertNotEqual(completed.returncode,0)
            self.assertEqual(result['errors'][0]['code'],'ORCH_ENABLE')
            self.assertEqual(self.tree_hash(),before)
            self.assertEqual((folder/'task.json').read_bytes(),historical)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        for name in ("AGENTS.md", "SOUL.md", "ROLE.md"):
            (self.root / name).write_text(f"# {name}\n", encoding="utf-8")
        (self.root / "Tasks").mkdir()
        self.write_index(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_index(self, root: Path, states: list[dict] | None = None) -> None:
        tasks = root / "Tasks"
        tasks.mkdir(exist_ok=True)
        content = task_state.render_index_markdown(states or [], "2026-08-27T12:00:00-06:00")
        (tasks / "INDEX.md").write_text(content, encoding="utf-8")

    def run_cli(
        self,
        command: str,
        *arguments: str,
        payload: dict | None = None,
        root: Path | None = None,
        fault: str | None = None,
        output_format: str = "json",
    ) -> tuple[subprocess.CompletedProcess[str], dict | str]:
        project = root or self.root
        argv = [
            sys.executable,
            str(SCRIPT),
            "--project-root",
            str(project),
            "--format",
            output_format,
            command,
            *arguments,
        ]
        environment = os.environ.copy()
        if fault:
            environment["TASK_STATE_FAULT"] = fault
        completed = subprocess.run(
            argv,
            input=json.dumps(payload) if payload is not None else None,
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        if output_format == "json":
            try:
                output: dict | str = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                self.fail(f"CLI did not return JSON. rc={completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}\n{exc}")
        else:
            output = completed.stdout
        return completed, output

    def create_task(
        self,
        name: str = "Example Task",
        *,
        root: Path | None = None,
        parent: str | None = None,
        definition: list[str] | None = None,
    ) -> tuple[dict, Path]:
        payload: dict = {
            "name": name,
            "description": f"Complete the durable objective for {name}.",
            "definition_of_done": definition or ["The requested result is verified."],
        }
        if parent:
            payload["parent_task_id"] = parent
        completed, result = self.run_cli("new", payload=payload, root=root)
        self.assertEqual(completed.returncode, 0, result)
        assert isinstance(result, dict)
        folder = Path(result["task_folder"])
        state = json.loads((folder / "task.json").read_text(encoding="utf-8"))
        return state, folder

    def read_state(self, folder: Path) -> dict:
        return json.loads((folder / "task.json").read_text(encoding="utf-8"))

    def response_payload(
        self,
        state: dict,
        *,
        status_after: str | None = None,
        completion: bool = False,
        authorized: bool = False,
        updates: dict | None = None,
        supersedes: str | None = None,
    ) -> dict:
        payload: dict = {
            "work_completed": ["Completed one bounded and observed work unit."],
            "verification_evidence": ["Inspected the resulting local artifact."],
            "user_response_summary": "Reported the observed result and current Task state.",
            "current_summary": "The current bounded work unit is complete.",
            "next_step": "Continue with the next approved work unit.",
            "blockers": [],
            "open_questions": [],
            "relevant_files": [],
        }
        if status_after:
            payload["status_after"] = status_after
        if authorized:
            payload["user_authorized"] = True
            payload["status_reason"] = "The user explicitly approved this lifecycle action."
        if updates is not None:
            payload["updates"] = updates
            for key in ("next_step", "blockers", "open_questions"):
                if key in updates:
                    payload[key] = updates[key]
        if supersedes:
            payload["supersedes_response_id"] = supersedes
        if completion:
            payload["next_step"] = None
            payload["status_after"] = "completed"
            payload["completion_evidence"] = [
                {"criterion": criterion, "evidence": f"Direct evidence for: {criterion}"}
                for criterion in state["definition_of_done"]
            ]
        return payload

    def mutate(
        self,
        state: dict,
        command: str = "record-response",
        *,
        status_after: str | None = None,
        completion: bool = False,
        authorized: bool = False,
        fault: str | None = None,
        root: Path | None = None,
        payload: dict | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        body = payload or self.response_payload(
            state,
            status_after=status_after,
            completion=completion,
            authorized=authorized,
        )
        completed, result = self.run_cli(
            command,
            state["task_id"],
            "--expected-revision",
            str(state["revision"]),
            payload=body,
            root=root,
            fault=fault,
        )
        assert isinstance(result, dict)
        return completed, result

    def tree_hash(self, root: Path | None = None) -> str:
        base = (root or self.root) / "Tasks"
        digest = hashlib.sha256()
        for path in sorted(base.rglob("*"), key=lambda item: item.as_posix()):
            digest.update(path.relative_to(base).as_posix().encode())
            if path.is_symlink():
                digest.update(os.readlink(path).encode())
            elif path.is_file():
                digest.update(path.read_bytes())
        return digest.hexdigest()

    def set_source_status(self, source: str, label: str) -> tuple[dict, Path]:
        state, folder = self.create_task(f"{label} source {source}")
        if source == "open":
            return state, folder
        if source == "paused":
            completed, result = self.mutate(state, "pause")
        elif source in {"awaiting_user", "blocked"}:
            completed, result = self.mutate(state, status_after=source)
        elif source == "completed":
            completed, result = self.mutate(state, "complete", completion=True)
        else:
            raise AssertionError(source)
        self.assertEqual(completed.returncode, 0, result)
        return self.read_state(folder), folder

    def test_t001_empty_status_is_valid_and_read_only(self) -> None:
        before = self.tree_hash()
        completed, result = self.run_cli("status")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result["counts"]["total"], 0)
        self.assertFalse(result["mutated"])
        for key in (
            "schema_version",
            "command",
            "status",
            "project_root",
            "tasks_root",
            "mutated",
            "warnings",
            "errors",
            "recovery_required",
        ):
            self.assertIn(key, result)
        self.assertEqual(before, self.tree_hash())
        markdown = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(self.root), "status", "--format", "markdown"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(markdown.returncode, 0, markdown.stdout + markdown.stderr)
        self.assertTrue(markdown.stdout.startswith("# Task status\n"))
        self.assertEqual(before, self.tree_hash())

    def test_t002_absent_tasks_root_is_not_created_by_status(self) -> None:
        other = Path(self.temp.name) / "absent"
        other.mkdir()
        for name in ("AGENTS.md", "SOUL.md", "ROLE.md"):
            (other / name).write_text("# marker\n", encoding="utf-8")
        completed, result = self.run_cli("status", root=other)
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(result["errors"][0]["code"], "TASKS_ROOT_NOT_FOUND")
        self.assertFalse((other / "Tasks").exists())

    def test_t003_new_creates_canonical_folder_and_required_contents(self) -> None:
        state, folder = self.create_task("Create Task System")
        self.assertRegex(folder.name, r"^Task-create-task-system-\d{4}-\d{2}-\d{2}--[0-9A-F]{8}$")
        self.assertRegex(state["task_id"], r"^TASK-\d{8}-[0-9A-F]{8}$")
        self.assertTrue((folder / "TASK.md").is_file())
        self.assertEqual(list((folder / "responses").iterdir()), [])
        one_use = Path(self.temp.name) / "new-payload.json"
        one_use.write_text(
            json.dumps(
                {
                    "name": "Payload File Task",
                    "description": "Exercise one-use payload cleanup.",
                    "definition_of_done": ["The payload file is removed."],
                }
            ),
            encoding="utf-8",
        )
        completed, _ = self.run_cli("new", "--payload-file", str(one_use))
        self.assertEqual(completed.returncode, 0)
        self.assertFalse(one_use.exists())

    def test_t004_same_name_and_date_get_distinct_ids_and_folders(self) -> None:
        first, first_folder = self.create_task("Repeated Name")
        second, second_folder = self.create_task("Repeated Name")
        self.assertNotEqual(first["task_id"], second["task_id"])
        self.assertNotEqual(first_folder, second_folder)
        self.assertEqual(first["original_name"], second["original_name"])

    def test_t005_unicode_slug_and_punctuation_fallback_are_safe(self) -> None:
        unicode_state, _ = self.create_task("Crème brûlée!!!")
        fallback_state, _ = self.create_task("💥 !!!")
        self.assertEqual(unicode_state["slug"], "creme-brulee")
        self.assertEqual(fallback_state["slug"], "task")

    def test_t006_unsafe_selectors_and_symlink_escape_are_rejected(self) -> None:
        state, _ = self.create_task()
        for selector in ("../escape", "/absolute/task", ".hidden", "bad\nname"):
            completed, _ = self.run_cli("show", selector)
            self.assertEqual(completed.returncode, 2, selector)
        unsafe_payload = self.response_payload(state)
        unsafe_payload["relevant_files"] = [{"path": "../outside", "note": "Unsafe."}]
        before = self.tree_hash()
        completed, _ = self.mutate(state, payload=unsafe_payload)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(before, self.tree_hash())
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.root / "Tasks" / "Task-escape-2026-08-27--ABCDEF12").symlink_to(outside, target_is_directory=True)
        completed, result = self.run_cli("validate")
        self.assertEqual(completed.returncode, 5)
        self.assertTrue(
            {"UNSAFE_TASK_FOLDER", "UNEXPECTED_TASK_ENTRY"}
            & {item["code"] for item in result["errors"]}
        )

    def test_t007_valid_initial_state_passes_at_revision_one(self) -> None:
        state, _ = self.create_task()
        completed, result = self.run_cli("validate", state["task_id"])
        self.assertEqual(completed.returncode, 0, result)
        self.assertEqual(result["revision_after"], 1)
        self.assertEqual(result["status"], "valid")

    def test_t008_corrupt_required_field_type_returns_schema_diagnostic(self) -> None:
        _, folder = self.create_task()
        state = self.read_state(folder)
        state["revision"] = "one"
        (folder / "task.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        completed, result = self.run_cli("validate")
        self.assertEqual(completed.returncode, 5)
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("REVISION", codes)
        self.assertNotIn("Traceback", completed.stderr)
        state["revision"] = 1
        state["next_step"] = None
        (folder / "task.json").write_text(task_state.json_text(task_state.canonical_state(state)), encoding="utf-8")
        completed, result = self.run_cli("validate")
        self.assertEqual(completed.returncode, 5)
        self.assertIn("NEXT_STEP_REQUIRED", {item["code"] for item in result["errors"]})
        invalid_payload = Path(self.temp.name) / "invalid-payload.json"
        invalid_payload.write_text("{not json", encoding="utf-8")
        completed, _ = self.run_cli("new", "--payload-file", str(invalid_payload))
        self.assertEqual(completed.returncode, 2)
        self.assertFalse(invalid_payload.exists())

    def test_t009_folder_state_identity_mismatch_is_detected(self) -> None:
        state, folder = self.create_task()
        moved = folder.with_name(folder.name.replace("--", "-changed--"))
        folder.rename(moved)
        completed, result = self.run_cli("validate")
        self.assertEqual(completed.returncode, 5)
        self.assertTrue({"TASK_FOLDER_NAME", "FOLDER_IDENTITY"} & {item["code"] for item in result["errors"]})
        self.assertEqual(state["task_id"], json.loads((moved / "task.json").read_text())["task_id"])

    def test_t010_task_projection_has_every_required_section_and_revision(self) -> None:
        state, folder = self.create_task()
        text = (folder / "TASK.md").read_text(encoding="utf-8")
        self.assertIn(f"revision {state['revision']}", text)
        for heading in (
            "## Identity",
            "## Description",
            "## Definition of done",
            "## Current summary",
            "## Blockers",
            "## Open questions",
            "## Next step",
            "## Latest Task Response",
        ):
            self.assertIn(heading, text)

    def test_t011_projection_drift_is_detected_and_rebuilt(self) -> None:
        state, folder = self.create_task()
        canonical = (folder / "task.json").read_bytes()
        (folder / "TASK.md").write_text("altered\n", encoding="utf-8")
        completed, result = self.run_cli("validate")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("TASK_PROJECTION_DRIFT", {item["code"] for item in result["warnings"]})
        rebuilt, _ = self.run_cli("rebuild-projections", state["task_id"])
        self.assertEqual(rebuilt.returncode, 0)
        self.assertEqual((folder / "task.json").read_bytes(), canonical)
        self.assertIn("Generated from task.json revision", (folder / "TASK.md").read_text())
        with_unsafe_link = (folder / "TASK.md").read_text(encoding="utf-8") + "\n[unsafe](../outside)\n"
        (folder / "TASK.md").write_text(with_unsafe_link, encoding="utf-8")
        completed, result = self.run_cli("validate")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("UNSAFE_LINK", {item["code"] for item in result["warnings"]})
        self.assertEqual(self.run_cli("rebuild-projections", state["task_id"])[0].returncode, 0)
        self.assertNotIn("../outside", (folder / "TASK.md").read_text(encoding="utf-8"))

    def test_t012_index_groups_nonterminal_before_terminal_and_lists_fields(self) -> None:
        open_state, _ = self.create_task("Open item")
        paused_state, paused_folder = self.create_task("Paused item")
        complete_state, complete_folder = self.create_task("Completed item")
        self.assertEqual(self.mutate(paused_state, "pause")[0].returncode, 0)
        self.assertEqual(self.mutate(complete_state, "complete", completion=True)[0].returncode, 0)
        text = (self.root / "Tasks" / "INDEX.md").read_text(encoding="utf-8")
        terminal_pos = text.index("Completed item")
        self.assertLess(text.index("Open item"), terminal_pos)
        self.assertLess(text.index("Paused item"), terminal_pos)
        self.assertIn("Latest response", text)
        self.assertIn(self.read_state(paused_folder)["task_id"], text)
        self.assertIn(self.read_state(complete_folder)["task_id"], text)
        self.assertIn(open_state["task_id"], text)

    def test_t013_missing_index_does_not_hide_tasks_and_rebuild_restores_it(self) -> None:
        state, _ = self.create_task()
        (self.root / "Tasks" / "INDEX.md").unlink()
        completed, result = self.run_cli("status")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result["counts"]["total"], 1)
        self.assertIn("INDEX_MISSING", {item["code"] for item in result["warnings"]})
        rebuilt, _ = self.run_cli("rebuild-projections")
        self.assertEqual(rebuilt.returncode, 0)
        self.assertIn(state["task_id"], (self.root / "Tasks" / "INDEX.md").read_text())

    def test_t014_first_response_has_canonical_identity_sections_and_revision(self) -> None:
        state, folder = self.create_task()
        completed, result = self.mutate(state)
        self.assertEqual(completed.returncode, 0, result)
        self.assertEqual(result["response_id"], "RESP-0001")
        response = Path(result["response_path"])
        self.assertRegex(response.name, r"^Task-Response-0001-.*\.md$")
        text = response.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Task Response - "))
        for heading in ("## Task description", "## Work completed this turn", "## Verification and evidence", "## User-facing response summary", "## Current blockers and open questions", "## Next step", "## Relevant files"):
            self.assertIn(heading, text)
        self.assertEqual(self.read_state(folder)["revision"], 2)

    def test_t015_completion_requires_full_evidence_and_exact_statement(self) -> None:
        state, folder = self.create_task(definition=["Criterion A", "Criterion B"])
        invalid = self.response_payload(state, completion=True)
        invalid["completion_evidence"].pop()
        before = self.tree_hash()
        completed, _ = self.mutate(state, "complete", payload=invalid)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(before, self.tree_hash())
        completed, result = self.mutate(state, "complete", completion=True)
        self.assertEqual(completed.returncode, 0, result)
        text = Path(result["response_path"]).read_text(encoding="utf-8")
        self.assertIn("Task completed. No next step required.", text)
        self.assertIsNone(self.read_state(folder)["next_step"])

    def test_t016_superseding_response_preserves_prior_file(self) -> None:
        state, folder = self.create_task()
        first_completed, first = self.mutate(state)
        self.assertEqual(first_completed.returncode, 0)
        first_path = Path(first["response_path"])
        first_bytes = first_path.read_bytes()
        current = self.read_state(folder)
        payload = self.response_payload(current, supersedes="RESP-0001")
        second_completed, second = self.mutate(current, payload=payload)
        self.assertEqual(second_completed.returncode, 0, second)
        self.assertEqual(first_bytes, first_path.read_bytes())
        self.assertIn("| Supersedes | RESP-0001 |", Path(second["response_path"]).read_text())

    def test_t017_known_secret_rejection_and_authorized_redaction_are_enforced(self) -> None:
        state, folder = self.create_task()
        payload = self.response_payload(state)
        secret = "sk-proj-ABCDEFGHIJKLMNOPQRSTUV"
        payload["work_completed"] = [f"Observed token {secret}"]
        before = self.tree_hash()
        completed, result = self.mutate(state, payload=payload)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["errors"][0]["code"], "SECRET_PATTERN")
        self.assertEqual(before, self.tree_hash())
        skill = document_path(".agents/skills/agent-task/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Keep hidden reasoning, credentials, transcripts", re.sub(r"\s+", " ", skill))

        recorded, recorded_result = self.mutate(state)
        self.assertEqual(recorded.returncode, 0, recorded_result)
        old_response = Path(recorded_result["response_path"])
        old_text = old_response.read_text(encoding="utf-8")
        old_response.write_text(old_text.replace("Completed one bounded", f"{secret} Completed one bounded"), encoding="utf-8")
        self.assertEqual(self.run_cli("validate")[0].returncode, 5)
        current = self.read_state(folder)
        correction = self.response_payload(current)
        redacted, redaction_result = self.run_cli(
            "reconcile",
            current["task_id"],
            "--expected-revision",
            str(current["revision"]),
            payload={
                "repair_type": "redact-response",
                "response_id": "RESP-0001",
                "redactions": [secret],
                "reason": "Remove an accidentally stored API credential.",
                "correction_response": correction,
                "user_authorized": True,
            },
        )
        self.assertEqual(redacted.returncode, 0, redaction_result)
        self.assertNotIn(secret, old_response.read_text(encoding="utf-8"))
        self.assertIn("[REDACTED]", old_response.read_text(encoding="utf-8"))
        self.assertIn("| Supersedes | RESP-0001 |", Path(redaction_result["response_path"]).read_text(encoding="utf-8"))
        self.assertEqual(self.read_state(folder)["response_count"], 2)
        self.assertEqual(self.run_cli("validate")[0].returncode, 0)

        fault_state, fault_folder = self.create_task("Recover redaction")
        recorded, fault_record = self.mutate(fault_state)
        self.assertEqual(recorded.returncode, 0, fault_record)
        fault_secret = "sk-proj-ZYXWVUTSRQPONMLKJIHG"
        fault_old = Path(fault_record["response_path"])
        fault_old.write_text(
            fault_old.read_text(encoding="utf-8").replace("Completed one bounded", f"{fault_secret} Completed one bounded"),
            encoding="utf-8",
        )
        fault_current = self.read_state(fault_folder)
        failed, failed_result = self.run_cli(
            "reconcile",
            fault_current["task_id"],
            "--expected-revision",
            str(fault_current["revision"]),
            payload={
                "repair_type": "redact-response",
                "response_id": "RESP-0001",
                "redactions": [fault_secret],
                "reason": "Remove a credential through the recovery path.",
                "correction_response": self.response_payload(fault_current),
                "user_authorized": True,
            },
            fault="after_redaction_state_publish",
        )
        self.assertEqual(failed.returncode, 9, failed_result)
        operation_id = failed_result["errors"][0]["operation_id"]
        repaired, repair_result = self.run_cli(
            "reconcile",
            fault_current["task_id"],
            "--expected-revision",
            str(fault_current["revision"]),
            payload={"repair_type": "transaction", "operation_id": operation_id},
        )
        self.assertEqual(repaired.returncode, 0, repair_result)
        self.assertNotIn(fault_secret, fault_old.read_text(encoding="utf-8"))
        self.assertEqual(self.run_cli("validate")[0].returncode, 0)

    def test_t018_every_allowed_lifecycle_transition_succeeds(self) -> None:
        allowed = {
            "open": {"paused", "awaiting_user", "blocked", "completed", "cancelled"},
            "paused": {"open", "awaiting_user", "blocked", "completed", "cancelled"},
            "awaiting_user": {"open", "paused", "blocked", "completed", "cancelled"},
            "blocked": {"open", "paused", "awaiting_user", "completed", "cancelled"},
            "completed": {"open"},
        }
        for source, destinations in allowed.items():
            for destination in destinations:
                with self.subTest(source=source, destination=destination):
                    state, folder = self.set_source_status(source, f"{source}-{destination}")
                    if destination == "paused":
                        completed, result = self.mutate(state, "pause")
                    elif destination == "completed":
                        completed, result = self.mutate(state, "complete", completion=True)
                    elif destination == "cancelled":
                        completed, result = self.mutate(state, "cancel", authorized=True)
                    elif source == "completed" and destination == "open":
                        completed, result = self.mutate(state, "reopen", authorized=True)
                    else:
                        completed, result = self.mutate(state, status_after=destination)
                    self.assertEqual(completed.returncode, 0, result)
                    self.assertEqual(self.read_state(folder)["status"], destination)

    def test_t019_prohibited_terminal_transitions_leave_files_unchanged(self) -> None:
        unauthorized, _ = self.create_task("Unauthorized cancellation")
        before = self.tree_hash()
        completed, _ = self.mutate(unauthorized, "cancel")
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(before, self.tree_hash())

        cancelled, cancelled_folder = self.create_task("Cancelled terminal")
        self.assertEqual(self.mutate(cancelled, "cancel", authorized=True)[0].returncode, 0)
        cancelled = self.read_state(cancelled_folder)
        before = self.tree_hash()
        completed, _ = self.mutate(cancelled, "reopen", authorized=True)
        self.assertEqual(completed.returncode, 8)
        self.assertEqual(before, self.tree_hash())

        done, done_folder = self.create_task("Completed terminal")
        self.assertEqual(self.mutate(done, "complete", completion=True)[0].returncode, 0)
        done = self.read_state(done_folder)
        before = self.tree_hash()
        completed, _ = self.mutate(done, status_after="paused")
        self.assertEqual(completed.returncode, 8)
        self.assertEqual(before, self.tree_hash())

    def test_t020_continue_completed_is_read_only_and_requests_decision(self) -> None:
        state, folder = self.create_task()
        self.assertEqual(self.mutate(state, "complete", completion=True)[0].returncode, 0)
        state = self.read_state(folder)
        before = self.tree_hash()
        completed, result = self.run_cli("continue", state["task_id"])
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "decision_required")
        self.assertIn("reopen", result["decision"])
        self.assertEqual(before, self.tree_hash())

    def test_t021_valid_child_resolves_and_stores_existing_parent(self) -> None:
        parent, _ = self.create_task("Parent")
        child, _ = self.create_task("Child", parent=parent["task_id"])
        self.assertEqual(child["parent_task_id"], parent["task_id"])
        self.assertEqual(self.run_cli("validate")[0].returncode, 0)

    def test_t022_missing_parent_and_parent_cycle_are_rejected(self) -> None:
        completed, result = self.run_cli(
            "new",
            payload={
                "name": "Missing parent",
                "description": "Must fail.",
                "definition_of_done": ["Failure observed."],
                "parent_task_id": "TASK-20260827-FFFFFFFF",
            },
        )
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(result["errors"][0]["code"], "TASK_NOT_FOUND")
        first, first_folder = self.create_task("Cycle A")
        second, _ = self.create_task("Cycle B", parent=first["task_id"])
        first["parent_task_id"] = second["task_id"]
        (first_folder / "task.json").write_text(task_state.json_text(task_state.canonical_state(first)), encoding="utf-8")
        (first_folder / "TASK.md").write_text(task_state.render_task_markdown(first), encoding="utf-8")
        completed, result = self.run_cli("validate")
        self.assertEqual(completed.returncode, 5)
        self.assertIn("PARENT_CYCLE", {item["code"] for item in result["errors"]})

    def test_t023_exact_task_id_resolves_first(self) -> None:
        first, _ = self.create_task("Alpha")
        self.create_task(first["task_id"])
        completed, result = self.run_cli("show", first["task_id"])
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result["task_id"], first["task_id"])

    def test_t024_unique_exact_name_and_safe_id_prefix_resolve(self) -> None:
        state, _ = self.create_task("Unique Name")
        self.assertEqual(self.run_cli("show", "unique name")[1]["task_id"], state["task_id"])
        prefix = state["task_id"][:-4]
        self.assertGreaterEqual(len(prefix), task_state.MIN_ID_PREFIX)
        self.assertEqual(self.run_cli("show", prefix)[1]["task_id"], state["task_id"])

    def test_t025_ambiguous_name_and_prefix_return_candidates_without_mutation(self) -> None:
        first, _ = self.create_task("Duplicate")
        second, _ = self.create_task("Duplicate")
        before = self.tree_hash()
        completed, result = self.run_cli("show", "duplicate")
        self.assertEqual(completed.returncode, 4)
        self.assertEqual(set(result["errors"][0]["candidates"]), {first["task_id"], second["task_id"]})
        common = os.path.commonprefix([first["task_id"], second["task_id"]])
        if len(common) >= task_state.MIN_ID_PREFIX:
            completed, _ = self.run_cli("show", common)
            self.assertEqual(completed.returncode, 4)
        self.assertEqual(before, self.tree_hash())

    def test_t026_task_skill_covers_zero_one_and_multiple_selection_dialogs(self) -> None:
        skill = document_path(".agents/skills/task/SKILL.md").read_text(encoding="utf-8")
        for phrase in ("with none, obtain the objective", "with one, show its ID", "with multiple, show the choices"):
            skill = re.sub(r"\s+", " ", skill)
            self.assertIn(phrase, skill)
        self.assertEqual(self.run_cli("status")[1]["counts"]["nonterminal"], 0)
        self.create_task("One")
        self.assertEqual(self.run_cli("status")[1]["counts"]["nonterminal"], 1)
        self.create_task("Two")
        self.assertEqual(self.run_cli("status")[1]["counts"]["nonterminal"], 2)

    def test_t027_status_and_list_are_byte_identical_read_only_operations(self) -> None:
        self.create_task()
        before = self.tree_hash()
        self.assertEqual(self.run_cli("status")[0].returncode, 0)
        self.assertEqual(before, self.tree_hash())
        self.assertEqual(self.run_cli("list")[0].returncode, 0)
        self.assertEqual(before, self.tree_hash())

    def test_t028_ordinary_prompt_policy_does_not_authorize_task_mutation(self) -> None:
        skill = document_path(".agents/skills/task/SKILL.md").read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", skill)
        self.assertIn("Do not use for ordinary untracked questions or unrelated project work", normalized)
        self.assertIn("Opening or approving a document does not start Task execution", normalized)
        self.assertIn("They never create or age Tasks", normalized)

    def test_t029_skill_metadata_has_exact_names_and_explicit_only_policy(self) -> None:
        task_yaml = document_path(".agents/skills/task/agents/openai.yaml").read_text(encoding="utf-8")
        agent_yaml = document_path(".agents/skills/agent-task/agents/openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Task"', task_yaml)
        self.assertIn('display_name: "Agent Task"', agent_yaml)
        self.assertEqual(task_yaml.count("allow_implicit_invocation: false"), 1)
        self.assertEqual(agent_yaml.count("allow_implicit_invocation: false"), 1)

    def test_t030_task_routes_to_exact_agent_task_contract_before_state_action(self) -> None:
        task_skill = document_path(".agents/skills/task/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("[Agent Task skill](../agent-task/SKILL.md)", task_skill)
        self.assertIn("before state operations and use its helper", re.sub(r"\s+", " ", task_skill))
        agent_skill = document_path(".agents/skills/agent-task/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/task-system-contract.md", agent_skill)

    def test_t031_child_role_is_forbidden_from_ledger_mutation(self) -> None:
        agent_skill = document_path(".agents/skills/agent-task/SKILL.md").read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", agent_skill)
        self.assertIn("Ordinary workers, solvers, reviewers, seniors and implementers return evidence", normalized)
        self.assertIn("they do not mutate canonical state, final Task Responses or role indexes", normalized)
        self.assertIn("Only the confirmed manager records the final Task Response", normalized)
        task_skill = document_path(".agents/skills/task/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Reading root guidance alone does not promote any ordinary child to manager or writer", re.sub(r"\s+", " ", task_skill))

    def test_t032_second_writer_gets_lock_exit_and_first_files_are_unchanged(self) -> None:
        locks = self.root / "Tasks" / ".locks" / "catalog.lock"
        locks.mkdir(parents=True)
        owner = {
            "operation_id": "TXN-" + "a" * 32,
            "command": "record-response",
            "task_id": None,
            "acquired_at": "2026-08-27T12:00:00-06:00",
            "process_id": 123,
        }
        (locks / "owner.json").write_text(json.dumps(owner, indent=2) + "\n", encoding="utf-8")
        before = self.tree_hash()
        completed, result = self.run_cli(
            "new",
            payload={"name": "Locked", "description": "Must not write.", "definition_of_done": ["No write."]},
        )
        self.assertEqual(completed.returncode, 7)
        self.assertTrue(result["recovery_required"])
        self.assertEqual(before, self.tree_hash())
        recovered, recovery = self.run_cli(
            "reconcile",
            payload={
                "repair_type": "remove-lock",
                "lock_name": "catalog",
                "expected_owner": owner,
                "user_authorized": True,
            },
        )
        self.assertEqual(recovered.returncode, 0, recovery)
        self.assertEqual(recovery["status"], "lock_removed")
        self.assertFalse(locks.exists())
        self.assertEqual(self.run_cli("status")[0].returncode, 0)

    def test_t033_expected_revision_conflict_rejects_stale_write(self) -> None:
        state, folder = self.create_task()
        self.assertEqual(self.mutate(state)[0].returncode, 0)
        before = self.tree_hash()
        completed, result = self.mutate(state)
        self.assertEqual(completed.returncode, 6)
        self.assertEqual(result["errors"][0]["code"], "REVISION_CONFLICT")
        self.assertEqual(before, self.tree_hash())
        self.assertEqual(self.read_state(folder)["revision"], 2)

    def test_t034_fault_before_response_publish_is_classified_and_cleanable(self) -> None:
        state, folder = self.create_task()
        completed, result = self.mutate(state, fault="before_response_publish")
        self.assertEqual(completed.returncode, 9, result)
        self.assertEqual(self.read_state(folder)["response_count"], 0)
        operation_id = result["errors"][0]["operation_id"]
        validated, validation = self.run_cli("validate")
        self.assertEqual(validated.returncode, 0)
        self.assertIn("ABORTED_TRANSACTION", {item["code"] for item in validation["warnings"]})
        reconciled, repair = self.run_cli(
            "reconcile",
            state["task_id"],
            "--expected-revision",
            "1",
            payload={"repair_type": "transaction", "operation_id": operation_id},
        )
        self.assertEqual(reconciled.returncode, 0, repair)
        self.assertEqual(repair["status"], "aborted_transaction_cleaned")

    def test_t035_orphan_response_is_detected_and_reconciled_without_duplicate(self) -> None:
        state, folder = self.create_task()
        completed, result = self.mutate(state, fault="after_response_publish")
        self.assertEqual(completed.returncode, 9)
        operation_id = result["errors"][0]["operation_id"]
        validated, validation = self.run_cli("validate")
        self.assertEqual(validated.returncode, 5)
        self.assertTrue({"ORPHAN_RESPONSE", "ORPHAN_RESPONSE_TRANSACTION"} & {item["code"] for item in validation["errors"]})
        reconciled, repair = self.run_cli(
            "reconcile",
            state["task_id"],
            "--expected-revision",
            "1",
            payload={"repair_type": "transaction", "operation_id": operation_id},
        )
        self.assertEqual(reconciled.returncode, 0, repair)
        current = self.read_state(folder)
        self.assertEqual(current["response_count"], 1)
        self.assertEqual(len(list((folder / "responses").glob("Task-Response-*.md"))), 1)

    def test_t036_post_state_fault_accepts_core_and_rebuilds_projections(self) -> None:
        state, folder = self.create_task()
        completed, result = self.mutate(state, fault="after_state_publish")
        self.assertEqual(completed.returncode, 9)
        self.assertEqual(self.read_state(folder)["revision"], 2)
        operation_id = result["errors"][0]["operation_id"]
        validated, validation = self.run_cli("validate")
        self.assertEqual(validated.returncode, 0, validation)
        warning_codes = {item["code"] for item in validation["warnings"]}
        self.assertIn("TASK_PROJECTION_DRIFT", warning_codes)
        self.assertIn("STALE_TRANSACTION_INTENT", warning_codes)
        reconciled, repair = self.run_cli(
            "reconcile",
            state["task_id"],
            "--expected-revision",
            "1",
            payload={"repair_type": "transaction", "operation_id": operation_id},
        )
        self.assertEqual(reconciled.returncode, 0, repair)
        self.assertEqual(self.run_cli("validate")[0].returncode, 0)

    def test_t037_missing_response_referenced_by_state_is_integrity_failure(self) -> None:
        state, folder = self.create_task()
        completed, result = self.mutate(state)
        self.assertEqual(completed.returncode, 0)
        Path(result["response_path"]).unlink()
        validated, validation = self.run_cli("validate")
        self.assertEqual(validated.returncode, 5)
        self.assertIn("MISSING_REFERENCED_RESPONSE", {item["code"] for item in validation["errors"]})
        self.assertEqual(self.read_state(folder)["response_count"], 1)

    def test_t038_reconciliation_is_idempotent(self) -> None:
        state, _ = self.create_task()
        completed, result = self.mutate(state, fault="after_response_publish")
        self.assertEqual(completed.returncode, 9)
        operation_id = result["errors"][0]["operation_id"]
        arguments = (state["task_id"], "--expected-revision", "1")
        payload = {"repair_type": "transaction", "operation_id": operation_id}
        first, first_result = self.run_cli("reconcile", *arguments, payload=payload)
        second, second_result = self.run_cli("reconcile", *arguments, payload=payload)
        self.assertEqual(first.returncode, 0, first_result)
        self.assertEqual(second.returncode, 0, second_result)
        self.assertEqual(second_result["status"], "already_reconciled")

    def test_t039_first_turn_policy_covers_zero_one_and_multiple_task_notices(self) -> None:
        agents = document_path("AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("first assistant turn", agents)
        self.assertIn("non-blocking resume", agents)
        self.assertIn("Do not interrupt unrelated work", agents)
        self.assertEqual(self.run_cli("status")[1]["counts"]["nonterminal"], 0)
        self.create_task("First")
        self.assertEqual(self.run_cli("status")[1]["counts"]["nonterminal"], 1)
        self.create_task("Second")
        self.assertEqual(self.run_cli("status")[1]["counts"]["nonterminal"], 2)

    def test_t040_continuation_works_without_thread_reference(self) -> None:
        state, _ = self.create_task()
        completed, result = self.run_cli("continue", state["task_id"])
        self.assertEqual(completed.returncode, 0, result)
        self.assertEqual(result["continuation"]["task_id"], state["task_id"])
        self.assertEqual(state["thread_refs"], [])

    def test_t041_continuation_carries_path_but_live_artifact_remains_authority(self) -> None:
        live = self.root / "result.txt"
        live.write_text("version one\n", encoding="utf-8")
        state, folder = self.create_task()
        payload = self.response_payload(state)
        payload["relevant_files"] = [{"path": "result.txt", "note": "Current result."}]
        self.assertEqual(self.mutate(state, payload=payload)[0].returncode, 0)
        live.write_text("version two\n", encoding="utf-8")
        current = self.read_state(folder)
        continued, result = self.run_cli("continue", current["task_id"])
        self.assertEqual(continued.returncode, 0)
        self.assertEqual(result["continuation"]["relevant_files"], ["result.txt"])
        self.assertEqual(live.read_text(), "version two\n")
        contract = (SKILL_ROOT / "references/task-system-contract.md").read_text()
        self.assertIn("never replace\nlive-project verification", contract)

    def test_t042_continuation_by_id_has_no_memory_dependency(self) -> None:
        state, _ = self.create_task()
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("memory", source.lower())
        self.assertEqual(self.run_cli("continue", state["task_id"])[0].returncode, 0)

    def test_t043_native_goal_and_task_state_are_explicitly_separate(self) -> None:
        contract = (SKILL_ROOT / "references/task-system-contract.md").read_text(encoding="utf-8")
        task_skill = document_path(".agents/skills/task/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Codex conversations, native goals", re.sub(r"\s+", " ", task_skill))
        root_agents = re.sub(r"\s+", " ", document_path("AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("native goal state", root_agents)
        self.assertIn("Report any mismatch", root_agents)
        self.assertIn("task.json", contract)

    def test_t044_delegated_work_returns_evidence_and_only_director_records(self) -> None:
        role = re.sub(r"\s+", " ", document_path("ROLE.md").read_text(encoding="utf-8"))
        self.assertIn("Ordinary children own only their delegated work and evidence", role)
        self.assertIn("truthful final Task Response", role)
        agents = re.sub(r"\s+", " ", document_path("AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("return evidence without ledger or role-index writes", agents)

    def test_t045_task_activation_does_not_broaden_external_authority(self) -> None:
        task_skill = document_path(".agents/skills/task/SKILL.md").read_text(encoding="utf-8")
        for phrase in ("destruction", "dependency installation", "external messages", "Git publication", "deployment"):
            task_skill = re.sub(r"\s+", " ", task_skill)
            self.assertIn(phrase, task_skill)

    def test_t046_both_skills_pass_bundled_validator(self) -> None:
        validator = Path("/Users/alex.omegapy/.codex/skills/.system/skill-creator/scripts/quick_validate.py")
        uv = Path("/Users/alex.omegapy/.local/bin/uv")
        for skill in (document_path(".agents/skills/task"), document_path(".agents/skills/agent-task")):
            completed = subprocess.run(
                [str(uv), "run", "--offline", "--with", "PyYAML", "--", "python", str(validator), str(skill)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("Skill is valid!", completed.stdout)

    def test_t047_helper_compiles_and_uses_only_standard_library_imports(self) -> None:
        py_compile.compile(str(SCRIPT), cfile=str(self.root / "task_state.pyc"), doraise=True)
        module = SCRIPT.with_name("orchestration_state.py")
        py_compile.compile(str(module), cfile=str(self.root / "orchestration_state.pyc"), doraise=True)
        for script in (SCRIPT, module):
            tree = ast.parse(script.read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module]
                    for name in imports:
                        self.assertIn(name.split(".")[0], sys.stdlib_module_names)
        source = SCRIPT.read_text(encoding="utf-8")
        for prohibited in ("yaml", "requests", "filelock", "sqlalchemy"):
            self.assertNotRegex(source, rf"^(?:from|import) {prohibited}\b")
        documented = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(self.root),
                "validate",
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(documented.returncode, 0, documented.stdout + documented.stderr)
        self.assertEqual(json.loads(documented.stdout)["status"], "valid")
        state, _ = self.create_task("Clock guard")
        with self.assertRaises(task_state.TaskError) as raised:
            task_state.apply_state_updates(
                state,
                self.response_payload(state),
                "open",
                "2000-01-01T00:00:00+00:00",
            )
        self.assertEqual(raised.exception.code, "CLOCK_ROLLBACK")

    def test_t048_all_task_system_artifacts_are_project_local(self) -> None:
        for path in (
            document_path(".agents/skills/task"),
            document_path(".agents/skills/agent-task"),
            document_path("Tasks"),
        ):
            self.assertTrue(path.resolve().is_relative_to(PROJECT_ROOT.resolve()))
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("~/.agents", source)
        self.assertNotIn("~/.codex", source)

    def test_t049_two_cold_processes_complete_cross_thread_style_continuation(self) -> None:
        state, folder = self.create_task("Cold process task")
        first, first_result = self.mutate(state)
        self.assertEqual(first.returncode, 0, first_result)
        current = self.read_state(folder)
        cold_status, status_result = self.run_cli("status")
        self.assertEqual(cold_status.returncode, 0)
        self.assertEqual(status_result["nonterminal_candidates"][0]["task_id"], current["task_id"])
        cold_continue, continue_result = self.run_cli("continue", current["task_id"])
        self.assertEqual(cold_continue.returncode, 0)
        self.assertEqual(continue_result["continuation"]["revision"], 2)
        second, second_result = self.mutate(current)
        self.assertEqual(second.returncode, 0, second_result)
        final = self.read_state(folder)
        self.assertEqual(final["response_count"], 2)
        self.assertEqual(final["revision"], 3)

    def test_t050_final_project_tree_contains_only_approved_task_artifacts(self) -> None:
        expected = {
            ".agents/skills/task/SKILL.md",
            ".agents/skills/task/agents/openai.yaml",
            ".agents/skills/agent-task/SKILL.md",
            ".agents/skills/agent-task/agents/openai.yaml",
            ".agents/skills/agent-task/references/task-system-contract.md",
            ".agents/skills/agent-task/scripts/task_state.py",
            ".agents/skills/agent-task/scripts/orchestration_state.py",
            ".agents/skills/agent-task/references/orchestration-contract.md",
            ".agents/skills/agent-task/assets/TASK.md.template",
            ".agents/skills/agent-task/assets/Task-Response.md.template",
            ".agents/skills/agent-task/assets/INDEX.md.template",
            ".agents/skills/agent-task/tests/test_task_state.py",
            "Tasks/INDEX.md",
        }
        for relative in expected:
            self.assertTrue((self.root / relative if relative.startswith("Tasks/") else document_path(relative)).is_file(), relative)
        for runtime in (self.root / "Tasks/.locks", self.root / "Tasks/.tmp"):
            self.assertFalse(runtime.exists(), runtime)

    def test_t051_update_changes_mutable_fields_and_preserves_identity(self) -> None:
        state, folder = self.create_task("Original Name")
        identity = {key: state[key] for key in ("task_id", "original_name", "slug", "folder_name", "created_at")}
        updates = {
            "name": "Updated Name",
            "description": "Updated approved scope.",
            "definition_of_done": ["Updated result is verified."],
            "next_step": "Verify the updated scope.",
            "blockers": ["One current blocker."],
            "open_questions": ["One current question?"],
        }
        payload = self.response_payload(state, updates=updates)
        completed, result = self.mutate(state, "update", payload=payload)
        self.assertEqual(completed.returncode, 0, result)
        current = self.read_state(folder)
        for key, value in identity.items():
            self.assertEqual(current[key], value)
        for key, value in updates.items():
            self.assertEqual(current[key], value)
        self.assertEqual(current["response_count"], 1)

    def test_t052_status_reports_catalog_writer_lock_without_mutation(self) -> None:
        lock = self.root / "Tasks/.locks/catalog.lock"
        lock.mkdir(parents=True)
        owner = {
            "operation_id": "TXN-" + "b" * 32,
            "command": "new",
            "task_id": None,
            "acquired_at": "2026-08-27T12:00:00-06:00",
            "process_id": 456,
        }
        (lock / "owner.json").write_text(json.dumps(owner, indent=2) + "\n", encoding="utf-8")
        before = self.tree_hash()
        completed, result = self.run_cli("status")
        self.assertEqual(completed.returncode, 7)
        self.assertEqual(result["errors"][0]["code"], "CATALOG_BUSY")
        self.assertEqual(result["errors"][0]["owner"]["operation_id"], owner["operation_id"])
        self.assertEqual(before, self.tree_hash())


if __name__ == "__main__":
    unittest.main()
