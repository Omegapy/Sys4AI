#!/usr/bin/env python3
"""Deterministic project-local Task ledger helper.

The root Project Director uses this CLI for every Task ledger operation. The
implementation uses only the Python standard library and keeps canonical state
under <project-root>/Tasks.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
import uuid
from typing import Any, Iterator


_orch_spec = importlib.util.spec_from_file_location("sys4ai_orchestration_state", Path(__file__).with_name("orchestration_state.py"))
orch = importlib.util.module_from_spec(_orch_spec)
_orch_spec.loader.exec_module(orch)

SCHEMA_VERSION = 1
RESULT_SCHEMA_VERSION = 1

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_NOT_FOUND = 3
EXIT_AMBIGUOUS = 4
EXIT_INTEGRITY = 5
EXIT_REVISION = 6
EXIT_LOCK = 7
EXIT_LIFECYCLE = 8
EXIT_TRANSACTION = 9

STATUSES = (
    "open",
    "paused",
    "awaiting_user",
    "blocked",
    "completed",
    "cancelled",
    "close-old-task",
)
NONTERMINAL = {"open", "paused", "awaiting_user", "blocked"}
TERMINAL = {"completed", "cancelled", "close-old-task"}
OLD_TASK_INACTIVITY = dt.timedelta(days=30)
OLD_TASK_CONCLUSION = "Task closed after 30 days of inactivity. Completion was not verified."
ALLOWED_TRANSITIONS = {
    "open": {"paused", "awaiting_user", "blocked", "completed", "cancelled", "close-old-task"},
    "paused": {"open", "awaiting_user", "blocked", "completed", "cancelled", "close-old-task"},
    "awaiting_user": {"open", "paused", "blocked", "completed", "cancelled", "close-old-task"},
    "blocked": {"open", "paused", "awaiting_user", "completed", "cancelled", "close-old-task"},
    "completed": {"open"},
    "cancelled": set(),
    "close-old-task": set(),
}

STATE_FIELDS = (
    "schema_version",
    "task_id",
    "name",
    "original_name",
    "slug",
    "folder_name",
    "description",
    "definition_of_done",
    "created_at",
    "updated_at",
    "status",
    "parent_task_id",
    "revision",
    "response_count",
    "last_response",
    "current_summary",
    "next_step",
    "blockers",
    "open_questions",
    "thread_refs",
)
LAST_RESPONSE_FIELDS = (
    "response_id",
    "sequence",
    "created_at",
    "path",
    "supersedes_response_id",
)
THREAD_REQUIRED_FIELDS = ("thread_id", "first_seen_at", "last_seen_at")
THREAD_OPTIONAL_FIELDS = ("title",)

TASK_ID_RE = re.compile(r"^TASK-(\d{8})-([0-9A-F]{8})$")
TASK_FOLDER_RE = re.compile(
    r"^Task-([a-z0-9]+(?:-[a-z0-9]+)*)-(\d{4}-\d{2}-\d{2})--([0-9A-F]{8})$"
)
RESPONSE_FILE_RE = re.compile(
    r"^Task-Response-(\d{4,})-(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}[+-]\d{2}-\d{2})\.md$"
)
RESPONSE_ID_RE = re.compile(r"^RESP-(\d{4,})$")
OPERATION_ID_RE = re.compile(r"^TXN-[0-9a-f]{32}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
MARKDOWN_LINK_RE = re.compile(r"\]\(([^)]+)\)")

SECRET_PATTERNS = (
    ("PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("OPENAI_KEY", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b")),
    ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("BEARER_TOKEN", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}")),
    (
        "NAMED_CREDENTIAL",
        re.compile(
            r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|authorization)"
            r"\s*[:=]\s*[^\s,;]{6,}"
        ),
    ),
)

MAX_PAYLOAD_BYTES = 1_000_000
MAX_PRETTY_JSON_BYTES = 1_000_000
MAX_JSON_BYTES = 2_000_000
MAX_RESPONSE_BYTES = 250_000
MAX_NAME = 300
MAX_DESCRIPTION = 20_000
MAX_TEXT = 40_000
MAX_ITEM = 5_000
MIN_ID_PREFIX = 13


class TaskError(Exception):
    """Expected, user-facing failure with a stable exit category."""

    def __init__(
        self,
        exit_code: int,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        recovery_required: bool = False,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.code = code
        self.message = message
        self.details = details or {}
        self.recovery_required = recovery_required

    def finding(self) -> dict[str, Any]:
        finding: dict[str, Any] = {"code": self.code, "message": self.message}
        finding.update(self.details)
        return finding


def orchestration_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except orch.OrchestrationError as exc:
        raise TaskError(EXIT_INVALID, exc.code, str(exc)) from exc


def state_fields(state):
    return STATE_FIELDS + (("orchestration",) if state.get("schema_version") == 2 else ())


def finding(code: str, message: str, **details: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "message": message}
    item.update(details)
    return item


def now_local() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def parse_timestamp(value: Any, field_name: str) -> dt.datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a nonblank ISO 8601 string")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not a valid ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must include an explicit UTC offset")
    return parsed


def safe_timestamp(value: str) -> str:
    parse_timestamp(value, "timestamp")
    return value.replace(":", "-")


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    slug = re.sub(r"-+", "-", slug)[:60].rstrip("-")
    return slug or "task"


def canonical_response_id(sequence: int) -> str:
    return f"RESP-{sequence:0{max(4, len(str(sequence)))}d}"


def canonical_response_filename(sequence: int, timestamp: str) -> str:
    width = max(4, len(str(sequence)))
    return f"Task-Response-{sequence:0{width}d}-{safe_timestamp(timestamp)}.md"


def contains_control(value: str) -> bool:
    return bool(CONTROL_RE.search(value))


def within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def establish_project_root(raw: str) -> Path:
    candidate = Path(raw).expanduser()
    if candidate.is_symlink():
        raise TaskError(EXIT_INVALID, "UNSAFE_PROJECT_ROOT", "Project root cannot be a symlink.")
    try:
        root = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise TaskError(EXIT_NOT_FOUND, "PROJECT_ROOT_NOT_FOUND", "Project root does not exist.") from exc
    if not root.is_dir():
        raise TaskError(EXIT_NOT_FOUND, "PROJECT_ROOT_NOT_DIRECTORY", "Project root is not a directory.")
    missing = [name for name in ("AGENTS.md", "SOUL.md", "ROLE.md") if not (root / name).is_file()]
    if missing:
        raise TaskError(
            EXIT_NOT_FOUND,
            "PROJECT_MARKERS_MISSING",
            "Project root is missing required root guidance files.",
            details={"missing": missing},
        )
    return root


def get_tasks_root(project_root: Path, *, required: bool = True) -> Path:
    tasks_root = project_root / "Tasks"
    if not tasks_root.exists():
        if required:
            raise TaskError(EXIT_NOT_FOUND, "TASKS_ROOT_NOT_FOUND", "Tasks/ does not exist.")
        return tasks_root
    if tasks_root.is_symlink():
        raise TaskError(EXIT_INTEGRITY, "TASKS_ROOT_SYMLINK", "Tasks/ cannot be a symlink.")
    if not tasks_root.is_dir():
        raise TaskError(EXIT_INTEGRITY, "TASKS_ROOT_NOT_DIRECTORY", "Tasks/ is not a directory.")
    resolved = tasks_root.resolve(strict=True)
    if resolved.parent != project_root:
        raise TaskError(EXIT_INTEGRITY, "TASKS_ROOT_ESCAPE", "Tasks/ resolves outside the project root.")
    return resolved


def check_regular_file(path: Path, label: str) -> None:
    if path.is_symlink():
        raise TaskError(EXIT_INTEGRITY, "UNSAFE_SYMLINK", f"{label} cannot be a symlink.", details={"path": str(path)})
    if not path.is_file():
        raise TaskError(EXIT_INTEGRITY, "FILE_NOT_FOUND", f"{label} is missing.", details={"path": str(path)})


def validate_selector_text(selector: str) -> None:
    if not selector or not selector.strip():
        raise TaskError(EXIT_INVALID, "EMPTY_SELECTOR", "Task selector cannot be blank.")
    if contains_control(selector):
        raise TaskError(EXIT_INVALID, "UNSAFE_SELECTOR", "Task selector contains a control character.")
    if Path(selector).is_absolute() or "/" in selector or "\\" in selector:
        raise TaskError(EXIT_INVALID, "UNSAFE_SELECTOR", "Task selector cannot be a path.")
    if selector.startswith(".") or selector in {"..", "."}:
        raise TaskError(EXIT_INVALID, "UNSAFE_SELECTOR", "Hidden or traversal task selectors are not allowed.")


def no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json_bytes(data: bytes, source: str) -> dict[str, Any]:
    if len(data) > MAX_PAYLOAD_BYTES:
        raise TaskError(EXIT_INVALID, "PAYLOAD_TOO_LARGE", f"{source} exceeds the payload size limit.")
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TaskError(EXIT_INVALID, "PAYLOAD_ENCODING", f"{source} must be UTF-8 JSON.") from exc
    try:
        value = json.loads(decoded, object_pairs_hook=no_duplicate_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise TaskError(EXIT_INVALID, "INVALID_JSON", f"{source} is not valid unambiguous JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise TaskError(EXIT_INVALID, "PAYLOAD_TYPE", f"{source} must contain one JSON object.")
    return value


def load_payload(payload_file: str, project_root: Path, tasks_root: Path) -> tuple[dict[str, Any], Path | None]:
    if payload_file == "-":
        data = sys.stdin.buffer.read(MAX_PAYLOAD_BYTES + 1)
        return parse_json_bytes(data, "standard input"), None

    path = Path(payload_file).expanduser()
    if path.is_symlink():
        raise TaskError(EXIT_INVALID, "PAYLOAD_SYMLINK", "Payload file cannot be a symlink.")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise TaskError(EXIT_NOT_FOUND, "PAYLOAD_NOT_FOUND", "Payload file does not exist.") from exc
    if not resolved.is_file():
        raise TaskError(EXIT_INVALID, "PAYLOAD_NOT_FILE", "Payload path is not a regular file.")
    if within(resolved, tasks_root):
        tmp_root = tasks_root / ".tmp"
        if not tmp_root.exists() or tmp_root.is_symlink() or not within(resolved, tmp_root.resolve(strict=True)):
            raise TaskError(
                EXIT_INVALID,
                "PAYLOAD_IN_DURABLE_LEDGER",
                "Payload files under Tasks/ must be confined to Tasks/.tmp/.",
            )
    if within(resolved, project_root) and resolved in {
        project_root / "AGENTS.md",
        project_root / "SOUL.md",
        project_root / "ROLE.md",
    }:
        raise TaskError(EXIT_INVALID, "PROTECTED_PAYLOAD_PATH", "A root guidance file cannot be used as a one-use payload.")
    try:
        data = resolved.read_bytes()
        return parse_json_bytes(data, "payload file"), resolved
    except Exception:
        # Explicit payload files are one-use even when validation fails.
        if not resolved.is_symlink():
            resolved.unlink(missing_ok=True)
        raise


def remove_payload(path: Path | None) -> None:
    if path is None:
        return
    try:
        if path.is_symlink():
            return
        path.unlink(missing_ok=True)
    except OSError:
        # Payload cleanup is reported by the caller when it matters; never mask
        # the primary Task result with a second exception.
        pass


def flatten_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from flatten_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from flatten_strings(child)


def reject_secrets(value: Any) -> None:
    for text in flatten_strings(value):
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise TaskError(
                    EXIT_INVALID,
                    "SECRET_PATTERN",
                    "Durable Task content matches a prohibited credential pattern.",
                    details={"pattern": label},
                )


def require_object_keys(
    payload: dict[str, Any],
    *,
    required: set[str],
    optional: set[str],
    label: str,
) -> None:
    missing = sorted(required - set(payload))
    unknown = sorted(set(payload) - required - optional)
    if missing or unknown:
        raise TaskError(
            EXIT_INVALID,
            "PAYLOAD_KEYS",
            f"{label} has missing or unsupported fields.",
            details={"missing": missing, "unknown": unknown},
        )


def require_text(value: Any, field_name: str, *, max_length: int = MAX_TEXT, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        raise TaskError(EXIT_INVALID, "FIELD_TYPE", f"{field_name} must be a nonblank string.")
    if contains_control(value.replace("\n", "").replace("\t", "")):
        raise TaskError(EXIT_INVALID, "CONTROL_CHARACTER", f"{field_name} contains a prohibited control character.")
    if len(value) > max_length:
        raise TaskError(EXIT_INVALID, "FIELD_TOO_LONG", f"{field_name} exceeds its length limit.")
    return value.strip()


def require_string_list(value: Any, field_name: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise TaskError(EXIT_INVALID, "FIELD_TYPE", f"{field_name} must be an array of strings.")
    if nonempty and not value:
        raise TaskError(EXIT_INVALID, "FIELD_EMPTY", f"{field_name} cannot be empty.")
    result: list[str] = []
    for index, item in enumerate(value):
        text = require_text(item, f"{field_name}[{index}]", max_length=MAX_ITEM)
        assert isinstance(text, str)
        result.append(text)
    return result


def validate_thread_ref(value: Any, field_name: str = "thread_ref") -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError(EXIT_INVALID, "FIELD_TYPE", f"{field_name} must be an object.")
    allowed = set(THREAD_REQUIRED_FIELDS) | set(THREAD_OPTIONAL_FIELDS)
    missing = sorted(set(THREAD_REQUIRED_FIELDS) - set(value))
    unknown = sorted(set(value) - allowed)
    if missing or unknown:
        raise TaskError(
            EXIT_INVALID,
            "THREAD_REF_KEYS",
            f"{field_name} has missing or unsupported fields.",
            details={"missing": missing, "unknown": unknown},
        )
    result = {
        "thread_id": require_text(value["thread_id"], f"{field_name}.thread_id", max_length=500),
    }
    if "title" in value:
        result["title"] = require_text(value["title"], f"{field_name}.title", max_length=500)
    first = require_text(value["first_seen_at"], f"{field_name}.first_seen_at", max_length=50)
    last = require_text(value["last_seen_at"], f"{field_name}.last_seen_at", max_length=50)
    assert isinstance(first, str) and isinstance(last, str)
    try:
        first_dt = parse_timestamp(first, f"{field_name}.first_seen_at")
        last_dt = parse_timestamp(last, f"{field_name}.last_seen_at")
    except ValueError as exc:
        raise TaskError(EXIT_INVALID, "THREAD_REF_TIMESTAMP", str(exc)) from exc
    if last_dt < first_dt:
        raise TaskError(EXIT_INVALID, "THREAD_REF_ORDER", f"{field_name}.last_seen_at precedes first_seen_at.")
    result["first_seen_at"] = first
    result["last_seen_at"] = last
    return result


def validate_relevant_files(value: Any, project_root: Path) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise TaskError(EXIT_INVALID, "FIELD_TYPE", "relevant_files must be an array.")
    result: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if isinstance(item, str):
            item = {"path": item, "note": "Relevant to this Task Response."}
        if not isinstance(item, dict) or set(item) != {"path", "note"}:
            raise TaskError(EXIT_INVALID, "RELEVANT_FILE_KEYS", f"relevant_files[{index}] must have path and note.")
        raw_path = require_text(item["path"], f"relevant_files[{index}].path", max_length=2_000)
        note = require_text(item["note"], f"relevant_files[{index}].note", max_length=2_000)
        assert isinstance(raw_path, str) and isinstance(note, str)
        candidate = Path(raw_path)
        if candidate.is_absolute() or ".." in candidate.parts or contains_control(raw_path):
            raise TaskError(EXIT_INVALID, "UNSAFE_RELEVANT_PATH", f"relevant_files[{index}] is not project-relative.")
        resolved = (project_root / candidate).resolve(strict=False)
        if not within(resolved, project_root):
            raise TaskError(EXIT_INVALID, "UNSAFE_RELEVANT_PATH", f"relevant_files[{index}] escapes the project root.")
        result.append({"path": candidate.as_posix(), "note": note})
    return result


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def task_json_text(state: dict[str, Any]) -> str:
    """Preserve small-state bytes; encode larger complete states within the cap."""
    content = json_text(state)
    if len(content.encode("utf-8")) <= MAX_PRETTY_JSON_BYTES:
        return content
    content = json.dumps(state, ensure_ascii=False, separators=(",", ":")) + "\n"
    if len(content.encode("utf-8")) > MAX_JSON_BYTES:
        raise TaskError(EXIT_INVALID, "ORCH_STATE_LIMIT", "Canonical state exceeds its bounded size; preserve history and report a resource blocker.")
    return content


def canonical_state(state: dict[str, Any]) -> dict[str, Any]:
    fields = state_fields(state)
    if set(state) != set(fields):
        raise TaskError(EXIT_INTEGRITY, "STATE_FIELDS", "Canonicalization cannot discard unknown or missing state fields.")
    ordered: dict[str, Any] = {key: state[key] for key in fields}
    if state.get("schema_version") == 2:
        ordered["orchestration"] = json.loads(json.dumps(state["orchestration"], sort_keys=True))
    last_response = ordered["last_response"]
    if isinstance(last_response, dict):
        ordered["last_response"] = {key: last_response[key] for key in LAST_RESPONSE_FIELDS}
    refs: list[Any] = []
    if isinstance(ordered["thread_refs"], list):
        for ref in ordered["thread_refs"]:
            if isinstance(ref, dict):
                item: dict[str, Any] = {"thread_id": ref["thread_id"]}
                if "title" in ref:
                    item["title"] = ref["title"]
                item["first_seen_at"] = ref["first_seen_at"]
                item["last_seen_at"] = ref["last_seen_at"]
                refs.append(item)
            else:
                refs.append(ref)
    ordered["thread_refs"] = refs
    return ordered


def atomic_write_text(path: Path, content: str) -> None:
    if path.exists() and path.is_symlink():
        raise TaskError(EXIT_INTEGRITY, "UNSAFE_SYMLINK", "Atomic write target cannot be a symlink.", details={"path": str(path)})
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise TaskError(EXIT_INTEGRITY, "UNSAFE_PARENT", "Atomic write parent is not a safe directory.", details={"path": str(path.parent)})
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _ontology_checkpoint(targets=False)
        os.replace(tmp_path, path)
    finally:
        tmp_path.unlink(missing_ok=True)


def write_staged_text(path: Path, content: str) -> Path:
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise TaskError(EXIT_INTEGRITY, "UNSAFE_PARENT", "Staged write parent is not safe.")
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".txn", dir=path.parent)
    tmp_path = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return tmp_path
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(path, json_text(value))


def transaction_intent_text(value: dict[str, Any]) -> str:
    """Bound durable intent bytes without adding indentation to embedded state."""
    content = json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    if len(content.encode("utf-8")) > MAX_JSON_BYTES:
        raise TaskError(EXIT_INVALID, "ORCH_INTENT_LIMIT", "Transaction evidence exceeds bounded intent size.")
    return content


def read_json_file(path: Path, label: str) -> tuple[dict[str, Any], str]:
    check_regular_file(path, label)
    data = path.read_bytes()
    if len(data) > MAX_JSON_BYTES:
        raise TaskError(EXIT_INTEGRITY, "JSON_TOO_LARGE", f"{label} exceeds the size limit.", details={"path": str(path)})
    try:
        text = data.decode("utf-8")
        value = json.loads(text, object_pairs_hook=no_duplicate_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise TaskError(EXIT_INTEGRITY, "MALFORMED_JSON", f"{label} is malformed: {exc}", details={"path": str(path)}) from exc
    if not isinstance(value, dict):
        raise TaskError(EXIT_INTEGRITY, "JSON_OBJECT_REQUIRED", f"{label} must contain one JSON object.")
    return value, text


def template_root() -> Path:
    root = Path(__file__).resolve().parent.parent / "assets"
    if root.is_symlink() or not root.is_dir():
        raise TaskError(EXIT_INTEGRITY, "ASSET_ROOT_INVALID", "Task template asset directory is unavailable.")
    return root


def render_template(name: str, values: dict[str, str]) -> str:
    path = template_root() / name
    check_regular_file(path, f"template {name}")
    content = path.read_text(encoding="utf-8")
    for key, value in values.items():
        content = content.replace("{{" + key + "}}", value)
    leftovers = sorted(set(re.findall(r"\{\{([a-z_]+)\}\}", content)))
    if leftovers:
        raise TaskError(EXIT_INTEGRITY, "TEMPLATE_PLACEHOLDER", "Template has unresolved placeholders.", details={"placeholders": leftovers})
    if not content.endswith("\n"):
        content += "\n"
    return content


def markdown_inline(value: Any) -> str:
    if value is None:
        return "None"
    text = str(value).replace("\r", " ").replace("\n", "<br>")
    return text.replace("|", "\\|")


def markdown_block(value: str) -> str:
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    safe: list[str] = []
    for line in lines:
        if line.startswith("#") or line.startswith("<!--"):
            line = "\\" + line
        safe.append(line)
    return "\n".join(safe).strip()


def markdown_list(items: list[str]) -> str:
    if not items:
        return "None"
    return "\n".join(f"- {markdown_block(item).replace(chr(10), ' ')}" for item in items)


def render_task_markdown(state: dict[str, Any]) -> str:
    last = state["last_response"]
    latest = "None"
    if isinstance(last, dict):
        latest = f"[{last['response_id']}]({last['path']})"
    rendered = render_template(
        "TASK.md.template",
        {
            "revision": str(state["revision"]),
            "name": markdown_block(state["name"]),
            "task_id": markdown_inline(state["task_id"]),
            "status": markdown_inline(state["status"]),
            "created_at": markdown_inline(state["created_at"]),
            "updated_at": markdown_inline(state["updated_at"]),
            "parent_task_id": markdown_inline(state["parent_task_id"]),
            "description": markdown_block(state["description"]),
            "definition_of_done": markdown_list(state["definition_of_done"]),
            "current_summary": markdown_block(state["current_summary"]),
            "blockers": markdown_list(state["blockers"]),
            "open_questions": markdown_list(state["open_questions"]),
            "next_step": markdown_block(state["next_step"]) if state["next_step"] is not None else "None",
            "latest_response": latest,
        },
    )
    if state.get("schema_version") == 2:
        rendered += orch.summary(state["orchestration"])
    return rendered


def render_relevant_files(files: list[dict[str, str]]) -> str:
    if not files:
        return "None"
    rows = []
    for item in files:
        path = item["path"].replace("`", "\\`")
        note = markdown_block(item["note"]).replace("\n", " ")
        rows.append(f"- `{path}` - {note}")
    return "\n".join(rows)


def render_response_markdown(
    state_before: dict[str, Any],
    state_after: dict[str, Any],
    payload: dict[str, Any],
    response_id: str,
    timestamp: str,
) -> str:
    thread = payload.get("thread_ref")
    thread_text = "Not available"
    if isinstance(thread, dict):
        thread_text = thread["thread_id"]
        if thread.get("title"):
            thread_text += f" ({thread['title']})"
    blocker_parts: list[str] = []
    if state_after["blockers"]:
        blocker_parts.append("Blockers:\n" + markdown_list(state_after["blockers"]))
    if state_after["open_questions"]:
        blocker_parts.append("Open questions:\n" + markdown_list(state_after["open_questions"]))
    blockers_and_questions = "\n\n".join(blocker_parts) or "None"
    if state_after["status"] == "completed":
        next_step = "Task completed. No next step required."
    elif state_after["status"] == "close-old-task":
        next_step = OLD_TASK_CONCLUSION
    else:
        next_step = markdown_block(state_after["next_step"]) if state_after["next_step"] is not None else "None"
    rendered = render_template(
        "Task-Response.md.template",
        {
            "timestamp": timestamp,
            "task_name": markdown_inline(state_after["name"]),
            "task_id": markdown_inline(state_after["task_id"]),
            "response_id": markdown_inline(response_id),
            "status_before": markdown_inline(state_before["status"]),
            "status_after": markdown_inline(state_after["status"]),
            "thread_reference": markdown_inline(thread_text),
            "supersedes": markdown_inline(payload.get("supersedes_response_id")),
            "task_description": markdown_block(state_after["description"]),
            "work_completed": markdown_list(payload["work_completed"]),
            "verification_evidence": markdown_list(payload["verification_evidence"]),
            "user_response_summary": markdown_block(payload["user_response_summary"]),
            "blockers_and_questions": blockers_and_questions,
            "next_step": next_step,
            "relevant_files": render_relevant_files(payload["relevant_files"]),
        },
    )

    if state_after.get("schema_version") == 2:
        o = state_after["orchestration"]
        actor = payload.get("actor")
        if actor is None:
            rendered += "\n## Orchestration receipt\n\nNo native identity was assigned by this schema upgrade.\n"
        else:
            rendered += f"\n## Orchestration receipt\n\nActor: {markdown_inline(actor)}; execution: {markdown_inline(payload.get('execution_id'))}; generation: {payload.get('generation')}; writer after: {markdown_inline(o['writer'])}.\n"
    return rendered


def task_sort_key(state: dict[str, Any]) -> tuple[int, float, str]:
    group = 0 if state["status"] in NONTERMINAL else 1
    parsed = parse_timestamp(state["updated_at"], "updated_at")
    return (group, -parsed.timestamp(), state["task_id"])


def render_index_markdown(states: list[dict[str, Any]], generated_at: str) -> str:
    counts = {status: 0 for status in STATUSES}
    for state in states:
        counts[state["status"]] += 1
    count_text = ", ".join(f"{status}={counts[status]}" for status in STATUSES)
    rows: list[str] = []
    for state in sorted(states, key=task_sort_key):
        last = state["last_response"]
        latest = "None"
        if isinstance(last, dict):
            target = f"{state['folder_name']}/{last['path']}"
            latest = f"[{last['response_id']}]({target})"
        rows.append(
            "| "
            + " | ".join(
                markdown_inline(value)
                for value in (
                    state["task_id"],
                    state["name"],
                    state["status"],
                    state["created_at"],
                    state["updated_at"],
                    state["parent_task_id"],
                    latest,
                    state["next_step"],
                )
            )
            + " |"
        )
    if not rows:
        rows.append("| None | None | None | None | None | None | None | None |")
    return render_template(
        "INDEX.md.template",
        {
            "generated_at": generated_at,
            "integrity": "valid",
            "counts": count_text,
            "task_rows": "\n".join(rows),
        },
    )


def parse_response_text(path: Path, text: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    title_match = re.search(r"^# Task Response - (.+)$", text, re.MULTILINE)
    title_timestamp = title_match.group(1).strip() if title_match else ""
    if not title_match:
        errors.append(finding("RESPONSE_TITLE", "Task Response title is missing.", path=str(path)))
    else:
        try:
            parse_timestamp(title_timestamp, "Task Response title")
        except ValueError as exc:
            errors.append(finding("RESPONSE_TIMESTAMP", str(exc), path=str(path)))

    required_headings = (
        "## Task description",
        "## Work completed this turn",
        "## Verification and evidence",
        "## User-facing response summary",
        "## Current blockers and open questions",
        "## Next step",
        "## Relevant files",
    )
    for heading in required_headings:
        count = text.count(heading)
        if count != 1:
            errors.append(
                finding(
                    "RESPONSE_SECTION",
                    f"Task Response must contain {heading!r} exactly once.",
                    path=str(path),
                    count=count,
                )
            )
        else:
            section = re.search(
                rf"^{re.escape(heading)}\n\n(.*?)(?=\n## |\Z)",
                text,
                re.MULTILINE | re.DOTALL,
            )
            if not section or not section.group(1).strip():
                errors.append(
                    finding(
                        "RESPONSE_SECTION_EMPTY",
                        f"Task Response section {heading!r} cannot be empty.",
                        path=str(path),
                    )
                )

    table: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^\| ([^|]+?) \| (.*) \|$", line)
        if not match:
            continue
        key = match.group(1).strip()
        if key in {
            "Task",
            "Task ID",
            "Response ID",
            "Status before",
            "Status after",
            "Thread reference",
            "Supersedes",
        }:
            table[key] = match.group(2).strip().replace("\\|", "|")
    for key in ("Task", "Task ID", "Response ID", "Status before", "Status after", "Thread reference", "Supersedes"):
        if key not in table:
            errors.append(finding("RESPONSE_TABLE", f"Task Response table is missing {key}.", path=str(path)))
    table["Timestamp"] = title_timestamp
    if table.get("Status after") == "close-old-task":
        next_step = re.search(r"^## Next step\n\n(.*?)(?=\n## |\Z)", text, re.MULTILINE | re.DOTALL)
        if not next_step or next_step.group(1).strip() != OLD_TASK_CONCLUSION:
            errors.append(finding("CLOSURE_CONCLUSION", "Age closure must explicitly state that completion was not verified.", path=str(path)))
    return table, errors


def validate_markdown_links(text: str, base: Path, path: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for target in MARKDOWN_LINK_RE.findall(text):
        if "://" in target or target.startswith("#"):
            continue
        candidate = Path(target)
        if candidate.is_absolute() or ".." in candidate.parts or contains_control(target):
            errors.append(finding("UNSAFE_LINK", "Generated Task file contains an unsafe local link.", path=str(path), target=target))
            continue
        resolved = (base / candidate).resolve(strict=False)
        if not within(resolved, base.resolve(strict=True)):
            errors.append(finding("UNSAFE_LINK", "Generated Task link escapes its allowed directory.", path=str(path), target=target))
    return errors


def validate_state_shape(state: dict[str, Any], folder: Path, raw_text: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    missing = sorted(set(state_fields(state)) - set(state))
    unknown = sorted(set(state) - set(state_fields(state)))
    if missing or unknown:
        errors.append(finding("STATE_FIELDS", "task.json has missing or unsupported fields.", path=str(folder / "task.json"), missing=missing, unknown=unknown))
        return errors

    if type(state["schema_version"]) is not int or state["schema_version"] not in (1, 2):
        errors.append(finding("SCHEMA_VERSION", "Unsupported task schema version.", task_id=state.get("task_id")))

    if state.get("schema_version") == 2:
        try:
            orch.validate(state["orchestration"])
        except (orch.OrchestrationError, KeyError, TypeError, ValueError) as exc:
            errors.append(finding(getattr(exc, "code", "ORCH_STATE"), str(exc), task_id=state.get("task_id")))

    for key, limit in (("name", MAX_NAME), ("original_name", MAX_NAME), ("description", MAX_DESCRIPTION), ("current_summary", MAX_TEXT)):
        value = state[key]
        if not isinstance(value, str) or not value.strip() or len(value) > limit or contains_control(value.replace("\n", "").replace("\t", "")):
            errors.append(finding("STATE_FIELD_TYPE", f"{key} must be a bounded nonblank string.", task_id=state.get("task_id")))

    task_id = state["task_id"]
    id_match = TASK_ID_RE.fullmatch(task_id) if isinstance(task_id, str) else None
    if not id_match:
        errors.append(finding("TASK_ID", "task_id does not match the canonical pattern.", task_id=task_id))

    folder_name = state["folder_name"]
    folder_match = TASK_FOLDER_RE.fullmatch(folder_name) if isinstance(folder_name, str) else None
    if not folder_match or folder.name != folder_name:
        errors.append(finding("FOLDER_IDENTITY", "Task folder and folder_name do not match the canonical pattern.", task_id=task_id, folder=folder.name))

    if isinstance(state["original_name"], str) and state["slug"] != slugify(state["original_name"]):
        errors.append(finding("SLUG_MISMATCH", "slug does not match original_name.", task_id=task_id))
    if folder_match and isinstance(state["slug"], str) and folder_match.group(1) != state["slug"]:
        errors.append(finding("FOLDER_SLUG_MISMATCH", "Folder slug does not match canonical slug.", task_id=task_id))
    if id_match and folder_match:
        id_date, id_suffix = id_match.groups()
        folder_date, folder_suffix = folder_match.group(2), folder_match.group(3)
        if id_suffix != folder_suffix or id_date != folder_date.replace("-", ""):
            errors.append(finding("FOLDER_ID_MISMATCH", "Folder date or suffix does not match task_id.", task_id=task_id))

    created: dt.datetime | None = None
    updated: dt.datetime | None = None
    try:
        created = parse_timestamp(state["created_at"], "created_at")
    except ValueError as exc:
        errors.append(finding("CREATED_AT", str(exc), task_id=task_id))
    try:
        updated = parse_timestamp(state["updated_at"], "updated_at")
    except ValueError as exc:
        errors.append(finding("UPDATED_AT", str(exc), task_id=task_id))
    if created and updated and updated < created:
        errors.append(finding("TIMESTAMP_ORDER", "updated_at precedes created_at.", task_id=task_id))
    if created and id_match and created.strftime("%Y%m%d") != id_match.group(1):
        errors.append(finding("CREATION_DATE_MISMATCH", "created_at date does not match task_id.", task_id=task_id))

    if state["status"] not in STATUSES:
        errors.append(finding("STATUS", "status is not an allowed lifecycle value.", task_id=task_id))
    parent = state["parent_task_id"]
    if parent is not None and (not isinstance(parent, str) or not TASK_ID_RE.fullmatch(parent) or parent == task_id):
        errors.append(finding("PARENT_ID", "parent_task_id is invalid or self-referential.", task_id=task_id))
    if not isinstance(state["revision"], int) or isinstance(state["revision"], bool) or state["revision"] < 1:
        errors.append(finding("REVISION", "revision must be a positive integer.", task_id=task_id))
    if not isinstance(state["response_count"], int) or isinstance(state["response_count"], bool) or state["response_count"] < 0:
        errors.append(finding("RESPONSE_COUNT", "response_count must be a nonnegative integer.", task_id=task_id))

    for key, nonempty in (("definition_of_done", True), ("blockers", False), ("open_questions", False)):
        value = state[key]
        if not isinstance(value, list) or (nonempty and not value) or any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(finding("STATE_LIST", f"{key} is not a valid string array.", task_id=task_id))

    count = state["response_count"]
    valid_count = isinstance(count, int) and not isinstance(count, bool) and count >= 0
    if state["next_step"] is not None and (not isinstance(state["next_step"], str) or not state["next_step"].strip()):
        errors.append(finding("NEXT_STEP", "next_step must be null or a nonblank string.", task_id=task_id))
    if state["status"] in {"completed", "close-old-task"} and state["next_step"] is not None:
        errors.append(finding("COMPLETION_NEXT_STEP", "A completed or age-closed task must have next_step null.", task_id=task_id))
    if state["status"] not in {"completed", "close-old-task"} and state["next_step"] is None:
        errors.append(finding("NEXT_STEP_REQUIRED", "A task without completion or age closure must name a next action or decision.", task_id=task_id))
    if valid_count and count == 0 and state["status"] != "open":
        errors.append(finding("INITIAL_STATUS", "A task with no responses must remain in its initial open status.", task_id=task_id))

    refs = state["thread_refs"]
    if not isinstance(refs, list):
        errors.append(finding("THREAD_REFS", "thread_refs must be an array.", task_id=task_id))
    else:
        seen_ids: set[str] = set()
        for index, ref in enumerate(refs):
            try:
                valid = validate_thread_ref(ref, f"thread_refs[{index}]")
                if valid["thread_id"] in seen_ids:
                    errors.append(finding("THREAD_REF_DUPLICATE", "thread_refs contains a duplicate thread_id.", task_id=task_id))
                seen_ids.add(valid["thread_id"])
            except TaskError as exc:
                errors.append(finding(exc.code, exc.message, task_id=task_id, index=index))

    last = state["last_response"]
    if valid_count and count == 0 and last is not None:
        errors.append(finding("LAST_RESPONSE_UNEXPECTED", "last_response must be null when response_count is zero.", task_id=task_id))
    if valid_count and count > 0:
        if not isinstance(last, dict):
            errors.append(finding("LAST_RESPONSE_MISSING", "last_response is required when responses exist.", task_id=task_id))
        else:
            missing_last = sorted(set(LAST_RESPONSE_FIELDS) - set(last))
            unknown_last = sorted(set(last) - set(LAST_RESPONSE_FIELDS))
            if missing_last or unknown_last:
                errors.append(finding("LAST_RESPONSE_FIELDS", "last_response has missing or unsupported fields.", task_id=task_id, missing=missing_last, unknown=unknown_last))
            elif (
                last["sequence"] != count
                or last["response_id"] != canonical_response_id(count)
                or not isinstance(last["path"], str)
            ):
                errors.append(finding("LAST_RESPONSE_IDENTITY", "last_response does not match response_count.", task_id=task_id))
            else:
                valid_last_timestamp = isinstance(last["created_at"], str)
                try:
                    parse_timestamp(last["created_at"], "last_response.created_at")
                except (TypeError, ValueError) as exc:
                    valid_last_timestamp = False
                    errors.append(finding("LAST_RESPONSE_TIMESTAMP", str(exc), task_id=task_id))
                if valid_last_timestamp:
                    expected_name = canonical_response_filename(count, last["created_at"])
                    expected_path = f"responses/{expected_name}"
                    if last["path"] != expected_path:
                        errors.append(finding("LAST_RESPONSE_PATH", "last_response path is not canonical.", task_id=task_id))
                    if last["created_at"] != state["updated_at"]:
                        errors.append(finding("LAST_RESPONSE_UPDATE_MISMATCH", "updated_at must match the latest response timestamp.", task_id=task_id))
                supersedes = last["supersedes_response_id"]
                if supersedes is not None and not isinstance(supersedes, str):
                    errors.append(finding("SUPERSEDES_TYPE", "supersedes_response_id must be null or a response ID.", task_id=task_id))

    try:
        canonical_text = task_json_text(canonical_state(state))
        if raw_text != canonical_text:
            errors.append(finding("CANONICAL_JSON_FORMAT", "task.json does not use canonical key order or formatting.", task_id=task_id))
    except (KeyError, TypeError):
        pass
    return errors


def scan_responses(state: dict[str, Any], folder: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, dict[str, str]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    metadata: dict[int, dict[str, str]] = {}
    responses = folder / "responses"
    if responses.is_symlink() or not responses.is_dir():
        errors.append(finding("RESPONSES_DIRECTORY", "responses/ is missing or unsafe.", task_id=state.get("task_id")))
        return errors, warnings, metadata
    seen: dict[int, Path] = {}
    for entry in sorted(responses.iterdir(), key=lambda item: item.name):
        if entry.is_symlink() or not entry.is_file():
            errors.append(finding("UNSAFE_RESPONSE_ENTRY", "responses/ contains a symlink or non-file entry.", path=str(entry), task_id=state.get("task_id")))
            continue
        match = RESPONSE_FILE_RE.fullmatch(entry.name)
        if not match:
            if entry.name.startswith(".") and entry.name.endswith(".txn"):
                warnings.append(finding("STAGED_RESPONSE", "A staged response file requires transaction inspection.", path=str(entry), task_id=state.get("task_id")))
            else:
                errors.append(finding("RESPONSE_FILENAME", "Response filename is not canonical.", path=str(entry), task_id=state.get("task_id")))
            continue
        sequence = int(match.group(1))
        if sequence in seen:
            errors.append(finding("DUPLICATE_RESPONSE_SEQUENCE", "Duplicate response sequence.", task_id=state.get("task_id"), sequence=sequence))
            continue
        seen[sequence] = entry
        if entry.stat().st_size > MAX_RESPONSE_BYTES:
            errors.append(finding("RESPONSE_TOO_LARGE", "Task Response exceeds the size limit.", path=str(entry), task_id=state.get("task_id")))
            continue
        try:
            text = entry.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(finding("RESPONSE_ENCODING", "Task Response must be UTF-8.", path=str(entry), task_id=state.get("task_id")))
            continue
        table, response_errors = parse_response_text(entry, text)
        errors.extend(response_errors)
        metadata[sequence] = table
        if table.get("Timestamp"):
            try:
                if safe_timestamp(table["Timestamp"]) != match.group(2):
                    errors.append(finding("RESPONSE_FILENAME_TIMESTAMP", "Response filename timestamp disagrees with its title.", path=str(entry), task_id=state.get("task_id")))
            except ValueError:
                pass
        if table.get("Task ID") != state.get("task_id"):
            errors.append(finding("RESPONSE_TASK_ID", "Task Response task ID disagrees with task.json.", path=str(entry), task_id=state.get("task_id")))
        if table.get("Response ID") != canonical_response_id(sequence):
            errors.append(finding("RESPONSE_ID", "Task Response ID disagrees with its sequence.", path=str(entry), task_id=state.get("task_id")))
        if table.get("Status before") not in STATUSES or table.get("Status after") not in STATUSES:
            errors.append(finding("RESPONSE_STATUS", "Task Response contains an invalid status.", path=str(entry), task_id=state.get("task_id")))
        supersedes = table.get("Supersedes")
        if supersedes and supersedes != "None":
            match_id = RESPONSE_ID_RE.fullmatch(supersedes)
            if not match_id or int(match_id.group(1)) >= sequence:
                errors.append(finding("SUPERSEDES_TARGET", "Task Response supersedes an invalid or non-prior response.", path=str(entry), task_id=state.get("task_id")))
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(finding("SECRET_IN_RESPONSE", "Stored Task Response matches a prohibited credential pattern.", path=str(entry), task_id=state.get("task_id"), pattern=label))
        errors.extend(validate_markdown_links(text, responses, entry))

    count = state.get("response_count")
    if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
        expected = set(range(1, count + 1))
        present = set(seen)
        missing = sorted(expected - present)
        orphan = sorted(present - expected)
        if missing:
            errors.append(finding("RESPONSE_SEQUENCE_GAP", "Committed response sequence has gaps.", task_id=state.get("task_id"), missing=missing))
        if orphan:
            errors.append(finding("ORPHAN_RESPONSE", "Published response is not committed in task.json.", task_id=state.get("task_id"), sequences=orphan))
        if count > 0 and isinstance(state.get("last_response"), dict):
            last_path = folder / state["last_response"]["path"]
            if last_path.is_symlink() or not last_path.is_file():
                errors.append(finding("MISSING_REFERENCED_RESPONSE", "task.json references a missing or unsafe response.", task_id=state.get("task_id"), path=str(last_path)))
            latest = metadata.get(count)
            if latest:
                if latest.get("Status after") != state.get("status"):
                    errors.append(finding("LATEST_STATUS_MISMATCH", "Latest response status disagrees with task.json.", task_id=state.get("task_id")))
                if latest.get("Timestamp") != state["last_response"].get("created_at"):
                    errors.append(finding("LATEST_TIMESTAMP_MISMATCH", "Latest response timestamp disagrees with task.json.", task_id=state.get("task_id")))
                supersedes = latest.get("Supersedes")
                expected_supersedes = state["last_response"].get("supersedes_response_id") or "None"
                if supersedes != expected_supersedes:
                    errors.append(finding("LATEST_SUPERSEDES_MISMATCH", "Latest response supersession disagrees with task.json.", task_id=state.get("task_id")))

    previous_status = "open"
    previous_timestamp = state.get("created_at")
    for sequence in sorted(metadata):
        item = metadata[sequence]
        before = item.get("Status before")
        after = item.get("Status after")
        if before in STATUSES and before != previous_status:
            errors.append(finding("RESPONSE_STATUS_CHAIN", "Task Response status chain is discontinuous.", task_id=state.get("task_id"), sequence=sequence))
        if before in STATUSES and after in STATUSES and before != after and after not in ALLOWED_TRANSITIONS[before]:
            errors.append(finding("RESPONSE_TRANSITION", "Task Response records a prohibited lifecycle transition.", task_id=state.get("task_id"), sequence=sequence))
        if after == "close-old-task" and before != "close-old-task":
            try:
                elapsed = parse_timestamp(item.get("Timestamp"), "closure timestamp") - parse_timestamp(previous_timestamp, "prior updated_at")
                if before not in NONTERMINAL or elapsed < OLD_TASK_INACTIVITY:
                    errors.append(finding("CLOSURE_AGE", "Age closure history does not prove 30 days of inactivity.", task_id=state.get("task_id"), sequence=sequence))
            except ValueError as exc:
                errors.append(finding("CLOSURE_AGE", str(exc), task_id=state.get("task_id"), sequence=sequence))
        supersedes = item.get("Supersedes")
        if supersedes and supersedes != "None":
            match_id = RESPONSE_ID_RE.fullmatch(supersedes)
            if match_id and int(match_id.group(1)) not in metadata:
                errors.append(finding("SUPERSEDES_TARGET", "Task Response supersedes a missing prior response.", task_id=state.get("task_id"), sequence=sequence))
        if after in STATUSES:
            previous_status = after
        previous_timestamp = item.get("Timestamp")
    return errors, warnings, metadata


def validate_task_folder(folder: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if folder.is_symlink() or not folder.is_dir():
        return None, [finding("UNSAFE_TASK_FOLDER", "Task folder is a symlink or not a directory.", path=str(folder))], warnings
    if not TASK_FOLDER_RE.fullmatch(folder.name):
        errors.append(finding("TASK_FOLDER_NAME", "Task folder name is not canonical.", path=str(folder)))
    task_json = folder / "task.json"
    try:
        state, raw_text = read_json_file(task_json, "task.json")
    except TaskError as exc:
        return None, [exc.finding()], warnings
    errors.extend(validate_state_shape(state, folder, raw_text))
    response_errors, response_warnings, _ = scan_responses(state, folder)
    errors.extend(response_errors)
    warnings.extend(response_warnings)

    task_md = folder / "TASK.md"
    if task_md.is_symlink():
        errors.append(finding("TASK_PROJECTION_SYMLINK", "TASK.md cannot be a symlink.", task_id=state.get("task_id")))
    elif not task_md.is_file():
        warnings.append(finding("TASK_PROJECTION_MISSING", "TASK.md is missing and can be rebuilt.", task_id=state.get("task_id")))
    elif not errors:
        expected = render_task_markdown(state)
        actual = task_md.read_text(encoding="utf-8")
        if actual != expected:
            warnings.append(finding("TASK_PROJECTION_DRIFT", "TASK.md differs from canonical task.json and can be rebuilt.", task_id=state.get("task_id")))
        warnings.extend(validate_markdown_links(actual, folder, task_md))
    return state, errors, warnings


def read_lock_owner(lock_dir: Path) -> dict[str, Any]:
    owner_path = lock_dir / "owner.json"
    if owner_path.is_symlink() or not owner_path.is_file():
        return {"owner_state": "missing_or_unsafe"}
    try:
        owner, _ = read_json_file(owner_path, "lock owner")
    except TaskError as exc:
        return {"owner_state": "invalid", "diagnostic": exc.finding()}
    allowed = {"operation_id", "command", "task_id", "acquired_at", "process_id"}
    return {key: owner[key] for key in owner if key in allowed}


def active_catalog_lock(tasks_root: Path) -> tuple[Path, dict[str, Any]] | None:
    locks = tasks_root / ".locks"
    if not locks.exists():
        return None
    if locks.is_symlink() or not locks.is_dir():
        raise TaskError(EXIT_INTEGRITY, "LOCK_ROOT_UNSAFE", "Tasks/.locks is not a safe directory.")
    lock_dir = locks / "catalog.lock"
    if lock_dir.exists():
        if lock_dir.is_symlink() or not lock_dir.is_dir():
            raise TaskError(EXIT_INTEGRITY, "CATALOG_LOCK_UNSAFE", "Catalog lock is not a safe directory.")
        return lock_dir, read_lock_owner(lock_dir)
    return None


def inspect_transaction_intents(tasks_root: Path, states: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    tmp_root = tasks_root / ".tmp"
    if not tmp_root.exists():
        return errors, warnings
    if tmp_root.is_symlink() or not tmp_root.is_dir():
        errors.append(finding("TMP_ROOT_UNSAFE", "Tasks/.tmp is not a safe directory."))
        return errors, warnings
    for entry in sorted(tmp_root.iterdir(), key=lambda item: item.name):
        if entry.name.startswith("reconciled-") and entry.name.endswith(".json"):
            continue
        if entry.is_symlink():
            errors.append(finding("TMP_SYMLINK", "Tasks/.tmp contains a symlink.", path=str(entry)))
            continue
        if entry.is_dir():
            warnings.append(finding("ABORTED_TEMP_DIRECTORY", "A transaction-owned temporary directory remains.", path=str(entry)))
            continue
        if not entry.is_file() or not OPERATION_ID_RE.fullmatch(entry.stem):
            warnings.append(finding("UNCLASSIFIED_TEMP_ENTRY", "An unclassified temporary entry requires inspection.", path=str(entry)))
            continue
        try:
            intent, _ = read_json_file(entry, "transaction intent")
        except TaskError as exc:
            errors.append(exc.finding())
            continue
        if intent.get("operation_id") != entry.stem:
            errors.append(finding("TRANSACTION_INTENT_SCHEMA", "Transaction intent identity is invalid.", path=str(entry)))
            continue
        task_id = intent.get("task_id")
        state = states.get(task_id)
        if state is None:
            errors.append(finding("TRANSACTION_TASK_MISSING", "Transaction intent references a missing task.", operation_id=entry.stem, task_id=task_id))
            continue
        task_folder = tasks_root / state["folder_name"]
        if intent.get("kind") == "redaction_transaction":
            try:
                old_path = validate_intent_response_path(
                    task_folder,
                    intent.get("old_response_path"),
                    "old_response_path",
                )
                correction_path = validate_intent_response_path(
                    task_folder,
                    intent.get("correction_response_path"),
                    "correction_response_path",
                )
            except TaskError as exc:
                errors.append(exc.finding())
                continue
            expected_revision = intent.get("expected_revision")
            planned_state = intent.get("planned_state")
            planned_revision = planned_state.get("revision") if isinstance(planned_state, dict) else None
            correction_exists = correction_path.is_file() and not correction_path.is_symlink()
            old_hash = hashlib.sha256(old_path.read_bytes()).hexdigest() if old_path.is_file() and not old_path.is_symlink() else None
            if state["revision"] == expected_revision and not correction_exists:
                warnings.append(finding("ABORTED_REDACTION_TRANSACTION", "Redaction stopped before its correction response was published.", operation_id=entry.stem, task_id=task_id))
            elif state["revision"] == expected_revision and correction_exists:
                errors.append(finding("ORPHAN_REDACTION_CORRECTION", "A redaction correction response was published before canonical state advanced.", operation_id=entry.stem, task_id=task_id))
            elif state["revision"] == planned_revision and not correction_exists:
                errors.append(finding("REDACTION_CORRECTION_MISSING", "Canonical state references a missing redaction correction response.", operation_id=entry.stem, task_id=task_id))
            elif state["revision"] == planned_revision and old_hash == intent.get("original_sha256"):
                errors.append(finding("PENDING_RESPONSE_REDACTION", "Canonical correction is committed but the approved old-response redaction is pending.", operation_id=entry.stem, task_id=task_id))
            elif state["revision"] == planned_revision and old_hash == intent.get("redacted_sha256"):
                warnings.append(finding("STALE_REDACTION_INTENT", "Response redaction is complete but its transaction intent remains.", operation_id=entry.stem, task_id=task_id))
            else:
                errors.append(finding("REDACTION_STATE_UNKNOWN", "Redaction intent cannot be reconciled with current files.", operation_id=entry.stem, task_id=task_id))
            continue
        if intent.get("kind") != "response_transaction":
            errors.append(finding("TRANSACTION_INTENT_SCHEMA", "Transaction intent kind is invalid.", path=str(entry)))
            continue
        response_path = task_folder / intent.get("response_path", "")
        expected_revision = intent.get("expected_revision")
        planned_state = intent.get("planned_state")
        planned_revision = planned_state.get("revision") if isinstance(planned_state, dict) else None
        if response_path.is_file() and state["revision"] == expected_revision:
            errors.append(finding("ORPHAN_RESPONSE_TRANSACTION", "A response was published before canonical state advanced.", operation_id=entry.stem, task_id=task_id))
        elif response_path.is_file() and state["revision"] == planned_revision:
            warnings.append(finding("STALE_TRANSACTION_INTENT", "Canonical response and state agree but a transaction intent remains.", operation_id=entry.stem, task_id=task_id))
        elif not response_path.exists() and state["revision"] == expected_revision:
            warnings.append(finding("ABORTED_TRANSACTION", "Transaction stopped before durable canonical mutation.", operation_id=entry.stem, task_id=task_id))
        elif not response_path.exists() and state["revision"] == planned_revision:
            errors.append(finding("INTENT_BACKED_RESPONSE_MISSING", "Canonical state advanced but its intended response is missing.", operation_id=entry.stem, task_id=task_id))
        else:
            errors.append(finding("TRANSACTION_STATE_UNKNOWN", "Transaction intent cannot be reconciled with current state.", operation_id=entry.stem, task_id=task_id))
    return errors, warnings


def scan_catalog(
    tasks_root: Path,
    *,
    ignore_catalog_lock: bool = False,
    check_projections: bool = True,
    check_transactions: bool = True,
) -> dict[str, Any]:
    if not ignore_catalog_lock:
        lock = active_catalog_lock(tasks_root)
        if lock:
            lock_dir, owner = lock
            raise TaskError(
                EXIT_LOCK,
                "CATALOG_BUSY",
                "A Task catalog writer lock is active.",
                details={"lock": str(lock_dir), "owner": owner},
                recovery_required=True,
            )
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    states: dict[str, dict[str, Any]] = {}
    folders: dict[str, Path] = {}
    for entry in sorted(tasks_root.iterdir(), key=lambda item: item.name):
        if entry.name in {"INDEX.md", ".locks", ".tmp", ".DS_Store"}:
            continue
        if entry.is_symlink() or not entry.is_dir():
            errors.append(finding("UNEXPECTED_TASK_ENTRY", "Tasks/ contains an unsafe or unexpected entry.", path=str(entry)))
            continue
        state, task_errors, task_warnings = validate_task_folder(entry)
        errors.extend(task_errors)
        warnings.extend(task_warnings)
        if state is None:
            continue
        task_id = state.get("task_id")
        if isinstance(task_id, str):
            if task_id in states:
                errors.append(finding("DUPLICATE_TASK_ID", "Two task folders use the same task ID.", task_id=task_id, folders=[str(folders[task_id]), str(entry)]))
            else:
                states[task_id] = state
                folders[task_id] = entry

    for task_id, state in states.items():
        parent = state.get("parent_task_id")
        if isinstance(parent, str) and parent not in states:
            errors.append(finding("PARENT_NOT_FOUND", "parent_task_id does not resolve.", task_id=task_id, parent_task_id=parent))

    for task_id in states:
        seen: set[str] = set()
        current: str | None = task_id
        while isinstance(current, str) and current in states:
            if current in seen:
                errors.append(finding("PARENT_CYCLE", "Task parent links form a cycle.", task_id=task_id))
                break
            seen.add(current)
            current = states[current].get("parent_task_id")

    locks_root = tasks_root / ".locks"
    if locks_root.exists() and not locks_root.is_symlink() and locks_root.is_dir() and not ignore_catalog_lock:
        for entry in locks_root.iterdir():
            if entry.name != "catalog.lock":
                errors.append(finding("ORPHAN_TASK_LOCK", "A task lock exists without the catalog lock.", path=str(entry), owner=read_lock_owner(entry) if entry.is_dir() else {}))

    if check_transactions:
        transaction_errors, transaction_warnings = inspect_transaction_intents(tasks_root, states)
        errors.extend(transaction_errors)
        warnings.extend(transaction_warnings)

    if check_projections and not errors:
        index_path = tasks_root / "INDEX.md"
        if index_path.is_symlink():
            errors.append(finding("INDEX_SYMLINK", "Tasks/INDEX.md cannot be a symlink."))
        elif not index_path.is_file():
            warnings.append(finding("INDEX_MISSING", "Tasks/INDEX.md is missing and can be rebuilt."))
        else:
            actual = index_path.read_text(encoding="utf-8")
            match = re.search(r"^- Generated: (.+)$", actual, re.MULTILINE)
            if not match:
                warnings.append(finding("INDEX_PROJECTION_DRIFT", "INDEX.md has no valid generation timestamp and can be rebuilt."))
            else:
                generated_at = match.group(1).strip()
                try:
                    parse_timestamp(generated_at, "INDEX generated timestamp")
                    expected = render_index_markdown(list(states.values()), generated_at)
                    if actual != expected:
                        warnings.append(finding("INDEX_PROJECTION_DRIFT", "INDEX.md differs from canonical task.json files and can be rebuilt."))
                except ValueError as exc:
                    warnings.append(finding("INDEX_PROJECTION_DRIFT", str(exc)))
            warnings.extend(validate_markdown_links(actual, tasks_root, index_path))

    return {"states": states, "folders": folders, "errors": errors, "warnings": warnings}


def require_valid_catalog(catalog: dict[str, Any]) -> None:
    if catalog["errors"]:
        raise TaskError(
            EXIT_INTEGRITY,
            "CATALOG_INVALID",
            "Task catalog integrity could not be proved.",
            details={"findings": catalog["errors"]},
            recovery_required=True,
        )


def resolve_task(selector: str, catalog: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    validate_selector_text(selector)
    states: dict[str, dict[str, Any]] = catalog["states"]
    folders: dict[str, Path] = catalog["folders"]
    upper = selector.upper()
    if upper in states:
        return states[upper], folders[upper]

    lowered = selector.casefold()
    by_name = [state for state in states.values() if state["name"].casefold() == lowered]
    if len(by_name) == 1:
        state = by_name[0]
        return state, folders[state["task_id"]]
    if len(by_name) > 1:
        raise TaskError(EXIT_AMBIGUOUS, "AMBIGUOUS_TASK_NAME", "Task name matches more than one task.", details={"candidates": sorted(state["task_id"] for state in by_name)})

    if len(selector) >= MIN_ID_PREFIX and re.fullmatch(r"[A-Za-z0-9-]+", selector) and upper.startswith("TASK-"):
        by_prefix = [state for state in states.values() if state["task_id"].startswith(upper)]
        if len(by_prefix) == 1:
            state = by_prefix[0]
            return state, folders[state["task_id"]]
        if len(by_prefix) > 1:
            raise TaskError(EXIT_AMBIGUOUS, "AMBIGUOUS_TASK_PREFIX", "Task ID prefix matches more than one task.", details={"candidates": sorted(state["task_id"] for state in by_prefix)})

    by_folder = [state for state in states.values() if state["folder_name"].casefold() == lowered]
    if len(by_folder) == 1:
        state = by_folder[0]
        return state, folders[state["task_id"]]
    if len(by_folder) > 1:
        raise TaskError(EXIT_AMBIGUOUS, "AMBIGUOUS_TASK_FOLDER", "Task folder selector is ambiguous.", details={"candidates": sorted(state["task_id"] for state in by_folder)})
    raise TaskError(EXIT_NOT_FOUND, "TASK_NOT_FOUND", "No task matches the exact selector.", details={"selector": selector})


def counts_for(states: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for state in states:
        status = state.get("status")
        if isinstance(status, str) and status in counts:
            counts[status] += 1
    counts["nonterminal"] = sum(counts[status] for status in NONTERMINAL)
    counts["terminal"] = sum(counts[status] for status in TERMINAL)
    counts["total"] = len(states)
    return counts


def base_result(command: str, project_root: Path, tasks_root: Path) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "command": command,
        "status": "ok",
        "project_root": str(project_root),
        "tasks_root": str(tasks_root),
        "mutated": False,
        "task_id": None,
        "revision_before": None,
        "revision_after": None,
        "response_id": None,
        "response_path": None,
        "warnings": [],
        "errors": [],
        "recovery_required": False,
    }


def state_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": state["task_id"],
        "name": state["name"],
        "status": state["status"],
        "description": state["description"],
        "created_at": state["created_at"],
        "updated_at": state["updated_at"],
        "parent_task_id": state["parent_task_id"],
        "revision": state["revision"],
        "response_count": state["response_count"],
        "latest_response": state["last_response"],
        "next_step": state["next_step"],
    }


def command_status(project_root: Path, tasks_root: Path, limit: int) -> dict[str, Any]:
    result = base_result("status", project_root, tasks_root)
    catalog = scan_catalog(tasks_root)
    states = list(catalog["states"].values())
    result["counts"] = counts_for(states)
    result["integrity"] = "invalid" if catalog["errors"] else "valid"
    result["projection_drift"] = [item for item in catalog["warnings"] if "PROJECTION" in item["code"] or item["code"].endswith("_MISSING")]
    safe_states = [
        state
        for state in states
        if isinstance(state.get("task_id"), str)
        and isinstance(state.get("status"), str)
        and state.get("status") in STATUSES
        and isinstance(state.get("updated_at"), str)
    ]
    try:
        candidates = [state for state in sorted(safe_states, key=task_sort_key) if state["status"] in NONTERMINAL]
    except (TypeError, ValueError):
        candidates = []
    result["nonterminal_candidates"] = [state_summary(state) for state in candidates[:limit]]
    result["warnings"] = catalog["warnings"]
    result["errors"] = catalog["errors"]
    if catalog["errors"]:
        result["status"] = "integrity_error"
        result["recovery_required"] = True
    elif catalog["warnings"]:
        result["status"] = "valid_with_warnings"
    return result


def command_list(project_root: Path, tasks_root: Path, statuses: list[str] | None) -> dict[str, Any]:
    result = base_result("list", project_root, tasks_root)
    catalog = scan_catalog(tasks_root)
    states = [
        state
        for state in catalog["states"].values()
        if isinstance(state.get("task_id"), str)
        and isinstance(state.get("status"), str)
        and state.get("status") in STATUSES
        and isinstance(state.get("updated_at"), str)
    ]
    try:
        states = sorted(states, key=task_sort_key)
    except (TypeError, ValueError):
        states = []
    if statuses:
        allowed = set(statuses)
        states = [state for state in states if state["status"] in allowed]
    result["tasks"] = [state_summary(state) for state in states]
    result["counts"] = counts_for(list(catalog["states"].values()))
    result["integrity"] = "invalid" if catalog["errors"] else "valid"
    result["warnings"] = catalog["warnings"]
    result["errors"] = catalog["errors"]
    if catalog["errors"]:
        result["status"] = "integrity_error"
        result["recovery_required"] = True
    elif catalog["warnings"]:
        result["status"] = "valid_with_warnings"
    return result


def command_show(project_root: Path, tasks_root: Path, selector: str, *, continuation: bool = False) -> dict[str, Any]:
    command = "continue" if continuation else "show"
    result = base_result(command, project_root, tasks_root)
    catalog = scan_catalog(tasks_root)
    require_valid_catalog(catalog)
    state, folder = resolve_task(selector, catalog)
    result["task_id"] = state["task_id"]
    result["revision_before"] = state["revision"]
    result["revision_after"] = state["revision"]
    result["warnings"] = catalog["warnings"]
    if not continuation:
        result["task"] = state
        result["task_folder"] = str(folder)
        result["latest_response_path"] = str(folder / state["last_response"]["path"]) if state["last_response"] else None
        return result

    latest_path = folder / state["last_response"]["path"] if state["last_response"] else None
    relevant_files: list[str] = []
    if latest_path and latest_path.is_file():
        text = latest_path.read_text(encoding="utf-8")
        section = re.search(r"^## Relevant files\n\n(.*?)(?=\n## |\Z)", text, re.MULTILINE | re.DOTALL)
        if section:
            relevant_files = re.findall(r"^- `([^`]+)`", section.group(1), re.MULTILINE)
    result["continuation"] = {
        "task_id": state["task_id"],
        "folder": state["folder_name"],
        "status": state["status"],
        "revision": state["revision"],
        "description": state["description"],
        "definition_of_done": state["definition_of_done"],
        "current_summary": state["current_summary"],
        "blockers": state["blockers"],
        "open_questions": state["open_questions"],
        "next_step": state["next_step"],
        "latest_response_path": str(latest_path) if latest_path else None,
        "task_brief_path": str(folder / "TASK.md"),
        "canonical_state_path": str(folder / "task.json"),
        "parent_task_id": state["parent_task_id"],
        "relevant_files": relevant_files,
        "integrity_warnings": catalog["warnings"],
    }
    if state["status"] in TERMINAL:
        result["status"] = "terminal_history"
        result["next_action"] = "For renewed work, use intake to create a related successor automatically. This inspection does not reopen or change the terminal task."
    return result


def validate_new_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_object_keys(
        payload,
        required={"name", "description", "definition_of_done"},
        optional={"parent_task_id", "current_summary", "next_step", "blockers", "open_questions", "thread_refs", "orchestration_enabled"},
        label="new payload",
    )
    if "orchestration_enabled" in payload and type(payload["orchestration_enabled"]) is not bool:
        raise TaskError(EXIT_INVALID, "ORCH_ENABLE", "orchestration_enabled must be boolean.")
    name = require_text(payload["name"], "name", max_length=MAX_NAME)
    description = require_text(payload["description"], "description", max_length=MAX_DESCRIPTION)
    assert isinstance(name, str) and isinstance(description, str)
    result: dict[str, Any] = {
        "name": name,
        "description": description,
        "definition_of_done": require_string_list(payload["definition_of_done"], "definition_of_done", nonempty=True),
        "parent_task_id": payload.get("parent_task_id"),
        "current_summary": require_text(payload.get("current_summary", "Task created; work has not started."), "current_summary"),
        "next_step": require_text(payload.get("next_step", "Begin the approved task work."), "next_step"),
        "blockers": require_string_list(payload.get("blockers", []), "blockers"),
        "open_questions": require_string_list(payload.get("open_questions", []), "open_questions"),
        "thread_refs": [],
        "orchestration_enabled": payload.get("orchestration_enabled", False),
    }
    if result["parent_task_id"] is not None:
        result["parent_task_id"] = require_text(result["parent_task_id"], "parent_task_id", max_length=MAX_NAME)
    refs = payload.get("thread_refs", [])
    if not isinstance(refs, list):
        raise TaskError(EXIT_INVALID, "FIELD_TYPE", "thread_refs must be an array.")
    result["thread_refs"] = [validate_thread_ref(ref, f"thread_refs[{index}]") for index, ref in enumerate(refs)]
    if len({ref["thread_id"] for ref in result["thread_refs"]}) != len(result["thread_refs"]):
        raise TaskError(EXIT_INVALID, "THREAD_REF_DUPLICATE", "thread_refs contains a duplicate thread_id.")
    reject_secrets(result)
    return result


def new_operation_id() -> str:
    return f"TXN-{uuid.uuid4().hex}"


def ensure_runtime_directories(tasks_root: Path) -> tuple[Path, Path]:
    locks = tasks_root / ".locks"
    tmp = tasks_root / ".tmp"
    for path in (locks, tmp):
        if path.exists():
            if path.is_symlink() or not path.is_dir():
                raise TaskError(EXIT_INTEGRITY, "RUNTIME_PATH_UNSAFE", "Task runtime path is not a safe directory.", details={"path": str(path)})
        else:
            path.mkdir(mode=0o700)
    return locks, tmp


@contextlib.contextmanager
def acquire_lock(
    tasks_root: Path,
    lock_name: str,
    *,
    operation_id: str,
    command: str,
    task_id: str | None,
) -> Iterator[Path]:
    locks, _ = ensure_runtime_directories(tasks_root)
    lock_dir = locks / f"{lock_name}.lock"
    if lock_dir.exists():
        owner = read_lock_owner(lock_dir) if lock_dir.is_dir() and not lock_dir.is_symlink() else {"owner_state": "unsafe"}
        raise TaskError(
            EXIT_LOCK,
            "LOCK_CONFLICT",
            "Task ledger lock could not be acquired.",
            details={"lock": str(lock_dir), "owner": owner},
            recovery_required=True,
        )
    try:
        lock_dir.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise TaskError(EXIT_LOCK, "LOCK_CONFLICT", "Task ledger lock was acquired by another writer.", recovery_required=True) from exc
    owner = {
        "operation_id": operation_id,
        "command": command,
        "task_id": task_id,
        "acquired_at": now_local(),
        "process_id": os.getpid(),
    }
    try:
        atomic_write_json(lock_dir / "owner.json", owner)
        _ontology_checkpoint()
        yield lock_dir
    finally:
        owner_path = lock_dir / "owner.json"
        if owner_path.is_file() and not owner_path.is_symlink():
            owner_path.unlink(missing_ok=True)
        try:
            lock_dir.rmdir()
        except OSError:
            # An unexpected entry makes ownership ambiguous. Leave the lock for
            # explicit recovery rather than deleting it recursively.
            pass


def allocate_identity(states: dict[str, dict[str, Any]], name: str, timestamp: str) -> tuple[str, str, str]:
    date_compact = parse_timestamp(timestamp, "created_at").strftime("%Y%m%d")
    date_folder = parse_timestamp(timestamp, "created_at").strftime("%Y-%m-%d")
    slug = slugify(name)
    existing_folders = {state["folder_name"] for state in states.values()}
    for _ in range(100):
        suffix = uuid.uuid4().hex[:8].upper()
        task_id = f"TASK-{date_compact}-{suffix}"
        folder = f"Task-{slug}-{date_folder}--{suffix}"
        if task_id not in states and folder not in existing_folders:
            return task_id, folder, slug
    raise TaskError(EXIT_TRANSACTION, "IDENTITY_ALLOCATION", "Could not allocate a unique task identity.")


def cleanup_temp_task(temp_folder: Path) -> None:
    if temp_folder.is_symlink() or not temp_folder.exists() or not temp_folder.is_dir():
        return
    responses = temp_folder / "responses"
    for name in ("task.json", "TASK.md"):
        target = temp_folder / name
        if target.is_file() and not target.is_symlink():
            target.unlink(missing_ok=True)
    if responses.is_dir() and not responses.is_symlink():
        try:
            responses.rmdir()
        except OSError:
            return
    try:
        temp_folder.rmdir()
    except OSError:
        pass


def write_index(tasks_root: Path, states: list[dict[str, Any]]) -> None:
    atomic_write_text(tasks_root / "INDEX.md", render_index_markdown(states, now_local()))


def command_new(
    project_root: Path,
    tasks_root: Path,
    payload: dict[str, Any],
    *,
    _catalog_locked: bool = False,
) -> dict[str, Any]:
    validated = validate_new_payload(payload)
    initial_catalog = scan_catalog(tasks_root, ignore_catalog_lock=_catalog_locked)
    require_valid_catalog(initial_catalog)
    operation_id = new_operation_id()
    result = base_result("new", project_root, tasks_root)
    catalog_lock = contextlib.nullcontext() if _catalog_locked else acquire_lock(
        tasks_root, "catalog", operation_id=operation_id, command="new", task_id=None
    )
    with catalog_lock:
        catalog = scan_catalog(tasks_root, ignore_catalog_lock=True)
        require_valid_catalog(catalog)
        parent_id = validated["parent_task_id"]
        if parent_id is not None:
            parent, _ = resolve_task(parent_id, catalog)
            parent_id = parent["task_id"]
        timestamp = now_local()
        task_id, folder_name, slug = allocate_identity(catalog["states"], validated["name"], timestamp)
        state = canonical_state(
            {
                "schema_version": 2 if validated["orchestration_enabled"] else 1,
                "task_id": task_id,
                "name": validated["name"],
                "original_name": validated["name"],
                "slug": slug,
                "folder_name": folder_name,
                "description": validated["description"],
                "definition_of_done": validated["definition_of_done"],
                "created_at": timestamp,
                "updated_at": timestamp,
                "status": "open",
                "parent_task_id": parent_id,
                "revision": 1,
                "response_count": 0,
                "last_response": None,
                "current_summary": validated["current_summary"],
                "next_step": validated["next_step"],
                "blockers": validated["blockers"],
                "open_questions": validated["open_questions"],
                "thread_refs": validated["thread_refs"],
                **({"orchestration": orch.empty()} if validated["orchestration_enabled"] else {}),
            }
        )
        _, tmp_root = ensure_runtime_directories(tasks_root)
        temp_folder = tmp_root / f"{operation_id}-task"
        final_folder = tasks_root / folder_name
        if temp_folder.exists() or final_folder.exists():
            raise TaskError(EXIT_TRANSACTION, "TASK_FOLDER_COLLISION", "Allocated task folder already exists.")
        temp_folder.mkdir(mode=0o700)
        try:
            (temp_folder / "responses").mkdir(mode=0o700)
            atomic_write_text(temp_folder / "task.json", task_json_text(state))
            atomic_write_text(temp_folder / "TASK.md", render_task_markdown(state))
            validation_errors = validate_state_shape(state, final_folder, task_json_text(state))
            if validation_errors:
                raise TaskError(EXIT_INTEGRITY, "INITIAL_STATE_INVALID", "Generated initial task state failed validation.", details={"findings": validation_errors})
            os.replace(temp_folder, final_folder)
        except Exception:
            cleanup_temp_task(temp_folder)
            raise

        result.update(
            {
                "status": "created",
                "mutated": True,
                "task_id": task_id,
                "task_folder": str(final_folder),
                "revision_after": 1,
            }
        )
        try:
            updated_catalog = scan_catalog(tasks_root, ignore_catalog_lock=True, check_transactions=False, check_projections=False)
            require_valid_catalog(updated_catalog)
            write_index(tasks_root, list(updated_catalog["states"].values()))
        except Exception as exc:
            result["status"] = "created_with_warnings"
            result["warnings"].append(
                finding("INDEX_REBUILD_FAILED", "Task was created, but INDEX.md needs regeneration.", diagnostic=str(exc))
            )
            result["recovery_required"] = True
    return result


def validate_completion_evidence(value: Any, criteria: list[str]) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise TaskError(EXIT_INVALID, "COMPLETION_EVIDENCE", "completion_evidence must cover every definition-of-done criterion.")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != {"criterion", "evidence"}:
            raise TaskError(EXIT_INVALID, "COMPLETION_EVIDENCE_KEYS", f"completion_evidence[{index}] must contain criterion and evidence.")
        criterion = require_text(item["criterion"], f"completion_evidence[{index}].criterion", max_length=MAX_ITEM)
        evidence = require_text(item["evidence"], f"completion_evidence[{index}].evidence", max_length=MAX_ITEM)
        assert isinstance(criterion, str) and isinstance(evidence, str)
        if criterion in seen:
            raise TaskError(EXIT_INVALID, "COMPLETION_EVIDENCE_DUPLICATE", "A completion criterion appears more than once.")
        seen.add(criterion)
        result.append({"criterion": criterion, "evidence": evidence})
    if seen != set(criteria) or len(result) != len(criteria):
        raise TaskError(
            EXIT_INVALID,
            "COMPLETION_EVIDENCE_COVERAGE",
            "Completion evidence must map exactly to the current definition of done.",
            details={"missing": sorted(set(criteria) - seen), "extra": sorted(seen - set(criteria))},
        )
    return result


def validate_response_payload(payload: dict[str, Any], command: str, state: dict[str, Any], project_root: Path) -> dict[str, Any]:
    required = {
        "work_completed",
        "verification_evidence",
        "user_response_summary",
        "current_summary",
        "next_step",
        "blockers",
        "open_questions",
        "relevant_files",
    }
    optional = {
        "status_after",
        "status_reason",
        "thread_ref",
        "supersedes_response_id",
        "updates",
        "completion_evidence",
        "user_authorized",
        "actor", "execution_id", "generation", "legacy_sha256", "reconciliation", "policy_receipt",
    }
    require_object_keys(payload, required=required, optional=optional, label=f"{command} payload")
    if state["schema_version"] == 1 and any(key in payload for key in ("actor", "execution_id", "generation", "reconciliation")):
        raise TaskError(EXIT_INVALID, "ORCH_LEGACY_PAYLOAD", "Orchestration actor fields require schema 2.")
    if "legacy_sha256" in payload and command != "upgrade-orchestration":
        raise TaskError(EXIT_INVALID, "ORCH_UPGRADE_PAYLOAD", "legacy_sha256 is valid only for explicit upgrade.")
    if "reconciliation" in payload and command != "reopen":
        raise TaskError(EXIT_INVALID, "ORCH_RECOVERY_PAYLOAD", "Reopening reconciliation is valid only for explicit reopen.")
    result: dict[str, Any] = {
        "work_completed": require_string_list(payload["work_completed"], "work_completed", nonempty=True),
        "verification_evidence": require_string_list(payload["verification_evidence"], "verification_evidence", nonempty=True),
        "user_response_summary": require_text(payload["user_response_summary"], "user_response_summary"),
        "current_summary": require_text(payload["current_summary"], "current_summary"),
        "next_step": require_text(payload["next_step"], "next_step", nullable=True),
        "blockers": require_string_list(payload["blockers"], "blockers"),
        "open_questions": require_string_list(payload["open_questions"], "open_questions"),
        "relevant_files": validate_relevant_files(payload["relevant_files"], project_root),
        "status_after": payload.get("status_after"),
        "status_reason": None,
        "thread_ref": None,
        "supersedes_response_id": payload.get("supersedes_response_id"),
        "updates": None,
        "completion_evidence": None,
        "user_authorized": payload.get("user_authorized", False),
        **{key: payload[key] for key in ("actor", "execution_id", "generation", "legacy_sha256", "reconciliation", "policy_receipt") if key in payload},
    }
    if "status_reason" in payload:
        result["status_reason"] = require_text(payload["status_reason"], "status_reason")
    if "thread_ref" in payload:
        result["thread_ref"] = validate_thread_ref(payload["thread_ref"])
    supersedes = result["supersedes_response_id"]
    if supersedes is not None:
        supersedes = require_text(supersedes, "supersedes_response_id", max_length=30)
        assert isinstance(supersedes, str)
        match = RESPONSE_ID_RE.fullmatch(supersedes)
        if not match or int(match.group(1)) < 1 or int(match.group(1)) > state["response_count"]:
            raise TaskError(EXIT_INVALID, "SUPERSEDES_TARGET", "supersedes_response_id must identify an existing prior response.")
        result["supersedes_response_id"] = supersedes
    if command == "update":
        updates = payload.get("updates")
        if not isinstance(updates, dict) or not updates:
            raise TaskError(EXIT_INVALID, "UPDATE_FIELDS", "update requires a nonempty updates object.")
        allowed_updates = {"name", "description", "definition_of_done", "next_step", "blockers", "open_questions"}
        unknown = sorted(set(updates) - allowed_updates)
        if unknown:
            raise TaskError(EXIT_INVALID, "UPDATE_FIELDS", "updates contains unsupported fields.", details={"unknown": unknown})
        valid_updates: dict[str, Any] = {}
        for key, value in updates.items():
            if key == "name":
                valid_updates[key] = require_text(value, "updates.name", max_length=MAX_NAME)
            elif key == "description":
                valid_updates[key] = require_text(value, "updates.description", max_length=MAX_DESCRIPTION)
            elif key == "definition_of_done":
                valid_updates[key] = require_string_list(value, "updates.definition_of_done", nonempty=True)
            elif key == "next_step":
                valid_updates[key] = require_text(value, "updates.next_step", nullable=True)
            else:
                valid_updates[key] = require_string_list(value, f"updates.{key}")
        result["updates"] = valid_updates
    elif "updates" in payload:
        raise TaskError(EXIT_INVALID, "UPDATE_FIELDS", "updates is valid only for the update command.")

    if "completion_evidence" in payload:
        result["completion_evidence"] = validate_completion_evidence(payload["completion_evidence"], state["definition_of_done"])
    reject_secrets(result)
    return result


def merge_thread_ref(refs: list[dict[str, Any]], new_ref: dict[str, Any] | None) -> list[dict[str, Any]]:
    if new_ref is None:
        return refs
    result: list[dict[str, Any]] = []
    replaced = False
    for ref in refs:
        if ref["thread_id"] == new_ref["thread_id"]:
            merged = dict(ref)
            merged["last_seen_at"] = new_ref["last_seen_at"]
            if new_ref.get("title"):
                merged["title"] = new_ref["title"]
            result.append(merged)
            replaced = True
        else:
            result.append(ref)
    if not replaced:
        result.append(new_ref)
    return result


def choose_status(command: str, payload: dict[str, Any], state: dict[str, Any]) -> str:
    forced = {"pause": "paused", "complete": "completed", "cancel": "cancelled", "reopen": "open", "close-old-task": "close-old-task"}
    if state["status"] in TERMINAL and command != "reopen":
        if state["status"] == "completed":
            raise TaskError(EXIT_LIFECYCLE, "EXPLICIT_REOPEN_REQUIRED", "A completed task requires explicit reopen before further mutation.")
        if state["status"] == "close-old-task":
            raise TaskError(EXIT_LIFECYCLE, "AGE_CLOSED_TERMINAL", "An age-closed task cannot be mutated or reopened; intake creates related work.")
        raise TaskError(EXIT_LIFECYCLE, "CANCELLED_TERMINAL", "A cancelled task cannot be mutated or reopened.")
    target = forced.get(command, payload.get("status_after") or state["status"])
    if target not in STATUSES:
        raise TaskError(EXIT_INVALID, "STATUS_AFTER", "status_after is not an allowed lifecycle value.")
    if target == state["status"]:
        if command in forced:
            raise TaskError(EXIT_LIFECYCLE, "NOOP_TRANSITION", f"Task is already {target}.")
        return target
    if target not in ALLOWED_TRANSITIONS[state["status"]]:
        raise TaskError(
            EXIT_LIFECYCLE,
            "PROHIBITED_TRANSITION",
            f"Transition from {state['status']} to {target} is prohibited.",
        )
    if state["status"] == "completed" and command != "reopen":
        raise TaskError(EXIT_LIFECYCLE, "EXPLICIT_REOPEN_REQUIRED", "A completed task can reopen only through the explicit reopen command.")
    if state["status"] == "cancelled":
        raise TaskError(EXIT_LIFECYCLE, "CANCELLED_TERMINAL", "A cancelled task cannot be reopened.")
    return target


def validate_transition_authority(command: str, payload: dict[str, Any], state: dict[str, Any], target: str) -> None:
    if target == "cancelled" or command == "reopen":
        if payload.get("user_authorized") is not True or not payload.get("status_reason"):
            raise TaskError(EXIT_INVALID, "USER_AUTHORIZATION_REQUIRED", f"{command} requires explicit user authorization and a reason.")
    if target == "completed":
        validate_completion_evidence(payload.get("completion_evidence"), state["definition_of_done"])
        if payload.get("next_step") is not None:
            raise TaskError(EXIT_INVALID, "COMPLETION_NEXT_STEP", "Completing a task requires next_step null.")
    elif command == "complete":
        raise TaskError(EXIT_LIFECYCLE, "COMPLETION_TARGET", "complete must transition to completed.")
    if target == "close-old-task":
        if payload.get("next_step") is not None:
            raise TaskError(EXIT_INVALID, "CLOSURE_NEXT_STEP", "Age closure requires next_step null.")
        if payload.get("completion_evidence") is not None:
            raise TaskError(EXIT_INVALID, "CLOSURE_NOT_COMPLETION", "Age closure cannot claim completion evidence.")


def eligible_for_age_closure(state: dict[str, Any], timestamp: str) -> bool:
    return state["status"] in NONTERMINAL and (
        parse_timestamp(timestamp, "closure timestamp") - parse_timestamp(state["updated_at"], "updated_at")
        >= OLD_TASK_INACTIVITY
    )


def validate_age_closure(state: dict[str, Any], timestamp: str) -> str:
    if not eligible_for_age_closure(state, timestamp):
        raise TaskError(
            EXIT_LIFECYCLE,
            "TASK_NOT_OLD",
            "Age closure requires an unfinished task with at least 30 elapsed days since updated_at.",
            details={"task_id": state["task_id"], "updated_at": state["updated_at"], "checked_at": timestamp},
        )
    elapsed = parse_timestamp(timestamp, "closure timestamp") - parse_timestamp(state["updated_at"], "updated_at")
    return (
        f"Age closure checked against updated_at={state['updated_at']} at {timestamp}; "
        f"{elapsed.total_seconds():.0f} elapsed seconds meets the 2592000-second inactivity threshold."
    )


def apply_state_updates(state: dict[str, Any], payload: dict[str, Any], target: str, timestamp: str) -> dict[str, Any]:
    try:
        if parse_timestamp(timestamp, "updated_at") < parse_timestamp(state["updated_at"], "prior updated_at"):
            raise TaskError(EXIT_TRANSACTION, "CLOCK_ROLLBACK", "Local time precedes the task's prior update timestamp.")
    except ValueError as exc:
        raise TaskError(EXIT_INTEGRITY, "UPDATED_AT", str(exc)) from exc
    updated = dict(state)
    updates = payload.get("updates") or {}
    for key, value in updates.items():
        updated[key] = value
    for key in ("current_summary", "next_step", "blockers", "open_questions"):
        payload_value = payload[key]
        if key in updates and updates[key] != payload_value:
            raise TaskError(EXIT_INVALID, "UPDATE_STATE_CONFLICT", f"updates.{key} disagrees with top-level {key}.")
        updated[key] = payload_value
    updated["status"] = target
    updated["updated_at"] = timestamp
    updated["revision"] = state["revision"] + 1
    updated["response_count"] = state["response_count"] + 1
    updated["thread_refs"] = merge_thread_ref(list(state["thread_refs"]), payload.get("thread_ref"))
    return updated


def inject_fault(stage: str) -> None:
    if os.environ.get("TASK_STATE_FAULT") == stage:
        raise OSError(f"injected transaction fault at {stage}")


def response_transaction(
    command: str,
    project_root: Path,
    tasks_root: Path,
    selector: str,
    expected_revision: int,
    raw_payload: dict[str, Any],
    *,
    _catalog_locked: bool = False,
) -> dict[str, Any]:
    initial_catalog = scan_catalog(tasks_root, ignore_catalog_lock=_catalog_locked)
    require_valid_catalog(initial_catalog)
    initial_state, _ = resolve_task(selector, initial_catalog)
    event = None
    if command == "orchestrate":
        require_object_keys(raw_payload, required={"event", "response"}, optional=set(), label="orchestrate payload")
        event = raw_payload["event"]
        if not isinstance(raw_payload["response"], dict):
            raise TaskError(EXIT_INVALID, "ORCH_RESPONSE", "response must be an object.")
        raw_payload = raw_payload["response"]
        if initial_state["schema_version"] != 2:
            raise TaskError(EXIT_INVALID, "ORCH_UPGRADE_REQUIRED", "Enable orchestration on a new record or explicitly upgrade this selected legacy Task.")
    payload = validate_response_payload(raw_payload, command, initial_state, project_root)
    operation_id = new_operation_id()
    result = base_result(command, project_root, tasks_root)
    intent_path: Path | None = None
    response_path: Path | None = None
    response_id: str | None = None
    staged_response: Path | None = None
    core_committed = False
    try:
        catalog_lock = contextlib.nullcontext() if _catalog_locked else acquire_lock(
            tasks_root, "catalog", operation_id=operation_id, command=command, task_id=initial_state["task_id"]
        )
        with catalog_lock:
            with acquire_lock(tasks_root, initial_state["task_id"], operation_id=operation_id, command=command, task_id=initial_state["task_id"]):
                catalog = scan_catalog(tasks_root, ignore_catalog_lock=True)
                require_valid_catalog(catalog)
                state, folder = resolve_task(initial_state["task_id"], catalog)
                if state["revision"] != expected_revision:
                    raise TaskError(
                        EXIT_REVISION,
                        "REVISION_CONFLICT",
                        "Expected revision does not match canonical state.",
                        details={"expected_revision": expected_revision, "actual_revision": state["revision"], "task_id": state["task_id"]},
                    )
                payload = validate_response_payload(raw_payload, command, state, project_root)
                artifact_writes = []
                reopened_orchestration = None
                if command == "upgrade-orchestration":
                    if state["schema_version"] != 1 or payload.get("user_authorized") is not True or not payload.get("status_reason"):
                        raise TaskError(EXIT_INVALID, "ORCH_UPGRADE_AUTHORITY", "Upgrade requires an explicitly authorized schema-1 selection and reason.")
                    original_bytes = (folder / "task.json").read_bytes()
                    if payload.get("legacy_sha256") != hashlib.sha256(original_bytes).hexdigest():
                        raise TaskError(EXIT_REVISION, "ORCH_UPGRADE_DIGEST", "Previewed legacy bytes changed.")
                    if payload.get("status_after") not in (None, state["status"]):
                        raise TaskError(EXIT_INVALID, "ORCH_UPGRADE_STATUS", "Upgrade cannot alter lifecycle meaning.")
                    target = state["status"]
                else:
                    target = choose_status(command, payload, state)
                    validate_transition_authority(command, payload, state, target)
                    if command != "orchestrate":
                        if target == "close-old-task" and state["schema_version"] == 2:
                            reopened_orchestration = validate_root_age_writer(state, payload)
                        else:
                            reopened_orchestration = orchestration_call(orch.lifecycle, state, payload, command, target, project_root, folder)
                timestamp = now_local()
                if target == "close-old-task":
                    age_evidence = validate_age_closure(state, timestamp)
                    payload["verification_evidence"] = [*payload["verification_evidence"], age_evidence]
                updated = apply_state_updates(state, payload, target, timestamp)
                if reopened_orchestration is not None:
                    updated["orchestration"] = reopened_orchestration
                if command == "upgrade-orchestration":
                    updated.update(schema_version=2, orchestration=orch.empty())
                    artifact_writes = [{"path": "artifacts/orchestration/legacy-v1-" + payload["legacy_sha256"] + ".json", "content": original_bytes}]
                elif event is not None:
                    updated["orchestration"], artifact_writes = orchestration_call(orch.apply, state, event, project_root, folder, list(catalog["states"].values()))
                    # Typed events may not smuggle a lifecycle transition through response.status_after.
                    if target != state["status"]:
                        raise TaskError(EXIT_INVALID, "ORCH_EVENT_LIFECYCLE", "Record the typed event first; use the separately gated lifecycle command.")
                for artifact_write in artifact_writes:
                    try:
                        artifact_text = artifact_write["content"].decode("utf-8")
                    except UnicodeDecodeError:
                        artifact_text = None
                    if artifact_text is not None:
                        reject_secrets(artifact_text)
                if event is not None:
                    payload.update(actor=event["actor"], execution_id=event["execution_id"], generation=event["generation"])
                sequence = updated["response_count"]
                response_id = canonical_response_id(sequence)
                filename = canonical_response_filename(sequence, timestamp)
                relpath = f"responses/{filename}"
                updated["last_response"] = {
                    "response_id": response_id,
                    "sequence": sequence,
                    "created_at": timestamp,
                    "path": relpath,
                    "supersedes_response_id": payload.get("supersedes_response_id"),
                }
                updated = canonical_state(updated)
                response_text = render_response_markdown(state, updated, payload, response_id, timestamp)
                reject_secrets(response_text)
                response_path = folder / relpath
                if response_path.exists() or response_path.is_symlink():
                    raise TaskError(EXIT_INTEGRITY, "RESPONSE_COLLISION", "Next Task Response path already exists.", details={"path": str(response_path)})
                planned_errors = validate_state_shape(updated, folder, task_json_text(updated))
                if planned_errors:
                    raise TaskError(EXIT_INTEGRITY, "PLANNED_STATE_INVALID", "Planned task state failed validation.", details={"findings": planned_errors})
                table, response_errors = parse_response_text(response_path, response_text)
                if response_errors or table.get("Status after") != target:
                    raise TaskError(EXIT_INTEGRITY, "PLANNED_RESPONSE_INVALID", "Rendered Task Response failed validation.", details={"findings": response_errors})

                _, tmp_root = ensure_runtime_directories(tasks_root)
                staged_response = write_staged_text(response_path, response_text)
                intent = {
                    "schema_version": 1,
                    "kind": "response_transaction",
                    "operation_id": operation_id,
                    "command": command,
                    "task_id": state["task_id"],
                    "expected_revision": expected_revision,
                    "response_id": response_id,
                    "response_path": relpath,
                    "response_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
                    "response_content": response_text,
                    "staged_response_path": str(staged_response.relative_to(tasks_root)),
                    "planned_state": updated,
                    "created_at": timestamp,
                }
                if state["schema_version"] == 2 or command == "upgrade-orchestration":
                    intent.update(schema_version=2, pre_state_sha256=hashlib.sha256((folder / "task.json").read_bytes()).hexdigest(), post_state_sha256=hashlib.sha256(task_json_text(updated).encode()).hexdigest(), actor=event["actor"] if event else payload.get("actor"), execution_id=event["execution_id"] if event else payload.get("execution_id"), generation=event["generation"] if event else payload.get("generation"), event_id=event["event_id"] if event else None, event_sha256=orch.hash_json(event) if event else None, artifacts=[{"path": w["path"], "sha256": hashlib.sha256(w["content"]).hexdigest(), "content_base64": base64.b64encode(w["content"]).decode()} for w in artifact_writes])
                intent_content = transaction_intent_text(intent)
                intent_path = tmp_root / f"{operation_id}.json"
                atomic_write_text(intent_path, intent_content)
                inject_fault("before_response_publish")
                publish_orchestration_artifacts(folder, intent, allow_existing=False)
                inject_fault("after_artifact_publish")
                _ontology_checkpoint(targets=False)
                os.replace(staged_response, response_path)
                staged_response = None
                inject_fault("after_response_publish")
                atomic_write_text(folder / "task.json", task_json_text(updated))
                core_committed = True
                inject_fault("after_state_publish")
                atomic_write_text(folder / "TASK.md", render_task_markdown(updated))
                inject_fault("after_task_projection")
                current_catalog = scan_catalog(
                    tasks_root,
                    ignore_catalog_lock=True,
                    check_projections=False,
                    check_transactions=False,
                )
                require_valid_catalog(current_catalog)
                write_index(tasks_root, list(current_catalog["states"].values()))
                inject_fault("after_index_projection")
                intent_path.unlink(missing_ok=True)
                intent_path = None
                final_catalog = scan_catalog(
                    tasks_root,
                    ignore_catalog_lock=True,
                    check_transactions=False,
                )
                require_valid_catalog(final_catalog)
                result.update(
                    {
                        "status": "recorded",
                        "mutated": True,
                        "task_id": updated["task_id"],
                        "revision_before": state["revision"],
                        "revision_after": updated["revision"],
                        "response_id": response_id,
                        "response_path": str(response_path),
                        "warnings": final_catalog["warnings"],
                    }
                )
                return result
    except TaskError as exc:
        if intent_path is None and not core_committed and not (response_path and response_path.exists()):
            if staged_response is not None:
                cleanup_staged_response(tasks_root, str(staged_response.relative_to(tasks_root)))
            raise
        details: dict[str, Any] = {
            "operation_id": operation_id,
            "diagnostic": exc.message,
            "task_id": initial_state["task_id"],
            "canonical_core_committed": core_committed,
            "response_published": bool(response_path and response_path.is_file()),
        }
        if response_id:
            details["response_id"] = response_id
        if response_path:
            details["response_path"] = str(response_path)
        raise TaskError(
            EXIT_TRANSACTION,
            "TRANSACTION_INCOMPLETE",
            "Task response transaction did not complete; explicit validation and reconciliation are required.",
            details=details,
            recovery_required=True,
        ) from exc
    except Exception as exc:
        details: dict[str, Any] = {"operation_id": operation_id, "diagnostic": str(exc)}
        if initial_state:
            details["task_id"] = initial_state["task_id"]
        if response_id:
            details["response_id"] = response_id
        if response_path:
            details["response_path"] = str(response_path)
        details["canonical_core_committed"] = core_committed
        details["response_published"] = bool(response_path and response_path.is_file())
        raise TaskError(
            EXIT_TRANSACTION,
            "TRANSACTION_INCOMPLETE",
            "Task response transaction did not complete; explicit validation and reconciliation are required.",
            details=details,
            recovery_required=True,
        ) from exc


def intent_profile(value: dict[str, Any]) -> tuple[str, str, tuple[str, ...]]:
    """Exact normalized fallback only; semantic selection belongs to the Director."""
    def normalize(text: str) -> str:
        return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

    return (
        normalize(value["name"]),
        normalize(value["description"]),
        tuple(sorted(normalize(criterion) for criterion in value["definition_of_done"])),
    )


def select_intake_match(
    payload: dict[str, Any],
    catalog: dict[str, Any],
    selector: str | None,
    timestamp: str,
) -> dict[str, Any] | None:
    for old in catalog["states"].values():
        if eligible_for_age_closure(old, timestamp):
            orchestration_call(orch.age_guard, old)
    parent_id = payload["parent_task_id"]
    if parent_id is not None:
        parent, _ = resolve_task(parent_id, catalog)
        payload["parent_task_id"] = parent_id = parent["task_id"]
    if selector is not None:
        selected, _ = resolve_task(selector, catalog)
    else:
        profile = intent_profile(payload)
        matches = [state for state in catalog["states"].values() if intent_profile(state) == profile]
        active = [state for state in matches if state["status"] in NONTERMINAL and not eligible_for_age_closure(state, timestamp)]
        if len(active) > 1:
            raise TaskError(EXIT_AMBIGUOUS, "AMBIGUOUS_INTAKE", "More than one unfinished task matches the work objective; supply one exact --match-task selector.", details={"candidates": sorted(state["task_id"] for state in active)})
        if active:
            selected = active[0]
        elif parent_id is not None:
            # An explicit parent supplies lineage for a new objective without
            # allowing a similarly named historical task to replace that choice.
            return None
        else:
            ancestors: set[str] = set()
            for state in matches:
                ancestor = state["parent_task_id"]
                while ancestor is not None:
                    ancestors.add(ancestor)
                    ancestor = catalog["states"][ancestor]["parent_task_id"]
            latest_lineage = [state for state in matches if state["task_id"] not in ancestors]
            # Independent terminal histories cannot supply a unique parent,
            # but they must not prevent automatic creation of renewed work.
            selected = latest_lineage[0] if len(latest_lineage) == 1 else None
    if selected is not None and parent_id is not None:
        expected_parent = selected["parent_task_id"]
        if selected["status"] in TERMINAL or eligible_for_age_closure(selected, timestamp):
            expected_parent = selected["task_id"]
        if parent_id != expected_parent:
            raise TaskError(EXIT_INVALID, "INTAKE_PARENT_CONFLICT", "The supplied parent disagrees with the selected task's lineage.", details={"task_id": selected["task_id"], "expected_parent_task_id": expected_parent})
    return selected


def validate_root_age_writer(state, payload):
    orchestration_call(orch.age_guard, state)
    o = json.loads(json.dumps(state["orchestration"]))
    actor = payload.get("actor")
    if payload.get("execution_id") != o["execution_id"] or payload.get("generation") != o["generation"] or type(payload.get("generation")) is not int:
        raise TaskError(EXIT_INVALID, "ORCH_STALE_GENERATION", "Age closure has stale execution binding.")
    if o["bootstrap"] is not None and actor != o["bootstrap"]:
        raise TaskError(EXIT_INVALID, "ORCH_WRITER", "Only the confirmed original bootstrap can take reconciled age-closure ownership.")
    if orchestration_call(orch.receipt, payload.get("policy_receipt"), subject=actor) != "running":
        raise TaskError(EXIT_INVALID, "ORCH_INTAKE_ACTOR", "Age closure needs a current native bootstrap receipt.")
    if o["execution_id"] is not None:
        for assignment in o["assignments"].values():
            assignment["state"] = "revoked"
        o.update(writer=actor, stage="stopped")
    return o


def age_closure_payload(state: dict[str, Any]) -> dict[str, Any]:
    prior_next_step = state["next_step"]
    prior_summary = state["current_summary"]
    return {
        "work_completed": [OLD_TASK_CONCLUSION],
        "verification_evidence": [
            "The intake operation inspected canonical Task status and updated_at.",
            "The previously recorded current summary is preserved in the following item(s):",
            *(prior_summary[index:index + MAX_ITEM] for index in range(0, len(prior_summary), MAX_ITEM)),
            "The previously recorded next step is preserved in the following item(s):",
            *(prior_next_step[index:index + MAX_ITEM] for index in range(0, len(prior_next_step), MAX_ITEM)),
        ],
        "user_response_summary": OLD_TASK_CONCLUSION,
        "current_summary": OLD_TASK_CONCLUSION,
        "next_step": None,
        "blockers": state["blockers"],
        "open_questions": state["open_questions"],
        "relevant_files": [],
    }


def command_intake(
    project_root: Path,
    tasks_root: Path,
    raw_payload: dict[str, Any],
    match_task: str | None = None,
) -> dict[str, Any]:
    intake_actor = raw_payload.get("intake_actor")
    raw_payload = {k: v for k, v in raw_payload.items() if k != "intake_actor"}
    if intake_actor is not None:
        require_object_keys(intake_actor, required={"native_id", "receipt"}, optional=set(), label="intake_actor")
        if orchestration_call(orch.receipt, intake_actor["receipt"], subject=intake_actor["native_id"]) != "running":
            raise TaskError(EXIT_INVALID, "ORCH_INTAKE_ACTOR", "Intake actor needs a current native running receipt.")
    payload = validate_new_payload(raw_payload)
    if match_task is not None:
        validate_selector_text(match_task)
    initial_catalog = scan_catalog(tasks_root)
    require_valid_catalog(initial_catalog)
    # Fail invalid identity/lineage before acquiring locks or closing old work.
    select_intake_match(dict(payload), initial_catalog, match_task, now_local())
    closed_tasks: list[dict[str, Any]] = []
    operation_id = new_operation_id()
    result = base_result("intake", project_root, tasks_root)
    result["closed_tasks"] = closed_tasks
    result["intake_result"] = None
    try:
        with acquire_lock(tasks_root, "catalog", operation_id=operation_id, command="intake", task_id=None):
            catalog = scan_catalog(tasks_root, ignore_catalog_lock=True)
            require_valid_catalog(catalog)
            timestamp = now_local()
            selected = select_intake_match(payload, catalog, match_task, timestamp)
            expired = sorted(
                (state for state in catalog["states"].values() if eligible_for_age_closure(state, timestamp)),
                key=lambda state: (parse_timestamp(state["updated_at"], "updated_at"), state["task_id"]),
            )
            # Validate all generated closure fields before committing the first
            # closure. Filesystem failures still use per-task recovery receipts.
            closure_payloads = {
                state["task_id"]: age_closure_payload(state)
                for state in expired
            }
            for state in expired:
                orchestration_call(orch.age_guard, state)
                if state["schema_version"] == 2:
                    if intake_actor is None:
                        raise TaskError(EXIT_INVALID, "ORCH_INTAKE_ACTOR", "Schema-2 age closure requires a current intake_actor receipt.")
                    o = state["orchestration"]
                    closure_payloads[state["task_id"]].update(actor=intake_actor["native_id"], execution_id=o["execution_id"], generation=o["generation"], policy_receipt=intake_actor["receipt"])
                    validate_root_age_writer(state, closure_payloads[state["task_id"]])
                validate_response_payload(closure_payloads[state["task_id"]], "close-old-task", state, project_root)
            for state in expired:
                receipt = response_transaction(
                    "close-old-task", project_root, tasks_root, state["task_id"],
                    state["revision"], closure_payloads[state["task_id"]], _catalog_locked=True,
                )
                receipt["status_after"] = "close-old-task"
                receipt["previous_updated_at"] = state["updated_at"]
                closed_tasks.append(receipt)
            catalog = scan_catalog(tasks_root, ignore_catalog_lock=True)
            require_valid_catalog(catalog)
            if selected is not None:
                selected = catalog["states"][selected["task_id"]]
            if selected is not None and selected["status"] in NONTERMINAL:
                folder = catalog["folders"][selected["task_id"]]
                selection = base_result("intake", project_root, tasks_root)
                selection.update({
                    "status": "matched", "task_id": selected["task_id"], "task_folder": str(folder),
                    "task": selected, "revision_before": selected["revision"], "revision_after": selected["revision"],
                    "warnings": catalog["warnings"],
                })
            else:
                if selected is not None:
                    payload["parent_task_id"] = selected["task_id"]
                selection = command_new(project_root, tasks_root, payload, _catalog_locked=True)
                result["intake_result"] = selection
                selection["task"] = read_json_file(Path(selection["task_folder"]) / "task.json", "created task")[0]
            result["intake_result"] = selection
            for key in ("task_id", "task_folder", "task", "revision_before", "revision_after", "warnings", "recovery_required"):
                result[key] = selection[key]
            result["status"] = selection["status"]
            result["mutated"] = bool(closed_tasks) or selection["mutated"]
            return result
    except (TaskError, OSError) as exc:
        error = exc if isinstance(exc, TaskError) else TaskError(EXIT_TRANSACTION, "INTAKE_IO_FAILURE", "Task intake encountered a filesystem error.", details={"diagnostic": str(exc)})
        if not closed_tasks and error.exit_code != EXIT_TRANSACTION:
            raise
        details = dict(error.details)
        details.update({
            "closed_tasks": closed_tasks,
            "intake_result": result["intake_result"],
            "mutated": bool(closed_tasks) or bool(error.details.get("canonical_core_committed")) or bool(error.details.get("response_published")) or bool(result["intake_result"] and result["intake_result"]["mutated"]),
            "result_status": "partial",
        })
        raise TaskError(
            error.exit_code, "INTAKE_INCOMPLETE",
            "Task intake stopped. Inspect the committed closure receipts and the failing operation before continuing; do not retry a partial transaction blindly.",
            details={**details, "failed_operation": error.finding()},
            recovery_required=error.recovery_required,
        ) from exc


def publish_orchestration_artifacts(folder, intent, *, allow_existing):
    for artifact in intent.get("artifacts", []):
        require_object_keys(artifact, required={"path", "sha256", "content_base64"}, optional=set(), label="artifact publication")
        target = orchestration_call(orch.confined, folder, artifact["path"])
        if not artifact["path"].startswith("artifacts/orchestration/"):
            raise TaskError(EXIT_INTEGRITY, "ORCH_ARTIFACT_PATH", "Invalid artifact publication target.")
        try:
            content = base64.b64decode(artifact["content_base64"], validate=True)
        except (ValueError, TypeError) as exc:
            raise TaskError(EXIT_INTEGRITY, "ORCH_ARTIFACT_CONTENT", "Malformed staged artifact bytes.") from exc
        if hashlib.sha256(content).hexdigest() != artifact["sha256"]:
            raise TaskError(EXIT_INTEGRITY, "ORCH_ARTIFACT_HASH", "Staged artifact digest differs.")
        if target.exists():
            if not allow_existing or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != artifact["sha256"]:
                raise TaskError(EXIT_INTEGRITY, "ORCH_ARTIFACT_COLLISION", "Artifact version was changed or already exists.")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".artifact-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content); handle.flush(); os.fsync(handle.fileno())
            os.replace(name, target)
        finally:
            Path(name).unlink(missing_ok=True)


def upgrade_preview(project_root, tasks_root, selector):
    catalog = scan_catalog(tasks_root); require_valid_catalog(catalog)
    state, folder = resolve_task(selector, catalog)
    result = base_result("upgrade-preview", project_root, tasks_root)
    result.update(status="preview", task_id=state["task_id"], revision_before=state["revision"], revision_after=state["revision"], schema_before=state["schema_version"], schema_after=2, sha256=hashlib.sha256((folder / "task.json").read_bytes()).hexdigest(), native_identity_created=False)
    return result


def command_validate(project_root: Path, tasks_root: Path, selector: str | None) -> dict[str, Any]:
    result = base_result("validate", project_root, tasks_root)
    catalog = scan_catalog(tasks_root)
    if selector is not None:
        if catalog["errors"]:
            # Resolution cannot be trusted when canonical identity is corrupt.
            result["errors"] = catalog["errors"]
        else:
            state, _ = resolve_task(selector, catalog)
            result["task_id"] = state["task_id"]
            result["revision_before"] = state["revision"]
            result["revision_after"] = state["revision"]
    else:
        result["errors"] = catalog["errors"]
    result["warnings"] = catalog["warnings"]
    result["integrity"] = "invalid" if catalog["errors"] else "valid"
    result["validated_task_count"] = len(catalog["states"])
    if catalog["errors"]:
        result["status"] = "invalid"
        result["recovery_required"] = True
    elif catalog["warnings"]:
        result["status"] = "valid_with_warnings"
    else:
        result["status"] = "valid"
    return result


def command_rebuild(project_root: Path, tasks_root: Path, selector: str | None, actor_payload=None) -> dict[str, Any]:
    catalog = scan_catalog(tasks_root)
    require_valid_catalog(catalog)
    selected_id: str | None = None
    if selector:
        selected, _ = resolve_task(selector, catalog)
        selected_id = selected["task_id"]
    operation_id = new_operation_id()
    result = base_result("rebuild-projections", project_root, tasks_root)
    with acquire_lock(tasks_root, "catalog", operation_id=operation_id, command="rebuild-projections", task_id=selected_id):
        current = scan_catalog(tasks_root, ignore_catalog_lock=True, check_transactions=False)
        require_valid_catalog(current)
        targets = list(current["states"].values())
        if selected_id:
            targets = [current["states"][selected_id]]
        for state in targets:
            if state["schema_version"] == 2:
                orchestration_call(orch.auth, state, actor_payload or {}, allow_unassigned=True)
        for state in targets:
            folder = current["folders"][state["task_id"]]
            atomic_write_text(folder / "TASK.md", render_task_markdown(state))
        write_index(tasks_root, list(current["states"].values()))
    result.update(
        {
            "status": "projections_rebuilt",
            "mutated": True,
            "task_id": selected_id,
            "rebuilt_task_count": len(targets),
        }
    )
    return result


def validate_reconcile_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cooperative = {key: payload[key] for key in ("actor", "execution_id", "generation", "bootstrap_receipt") if key in payload}
    if cooperative:
        stripped = {key: value for key, value in payload.items() if key not in cooperative}
        return {**validate_reconcile_payload(stripped), **cooperative}

    repair_type = payload.get("repair_type")
    if repair_type == "transaction":
        require_object_keys(payload, required={"repair_type", "operation_id"}, optional=set(), label="transaction reconcile payload")
        operation_id = require_text(payload["operation_id"], "operation_id", max_length=40)
        assert isinstance(operation_id, str)
        if not OPERATION_ID_RE.fullmatch(operation_id):
            raise TaskError(EXIT_INVALID, "OPERATION_ID", "operation_id is not canonical.")
        return {"repair_type": repair_type, "operation_id": operation_id}
    if repair_type == "remove-lock":
        require_object_keys(
            payload,
            required={"repair_type", "lock_name", "expected_owner", "user_authorized"},
            optional=set(),
            label="lock reconcile payload",
        )
        if payload["user_authorized"] is not True:
            raise TaskError(EXIT_INVALID, "USER_AUTHORIZATION_REQUIRED", "Lock recovery requires explicit user authorization.")
        lock_name = require_text(payload["lock_name"], "lock_name", max_length=100)
        assert isinstance(lock_name, str)
        if lock_name != "catalog" and not TASK_ID_RE.fullmatch(lock_name):
            raise TaskError(EXIT_INVALID, "LOCK_NAME", "lock_name must be catalog or an exact task ID.")
        if not isinstance(payload["expected_owner"], dict):
            raise TaskError(EXIT_INVALID, "EXPECTED_OWNER", "expected_owner must be an exact object.")
        return {
            "repair_type": repair_type,
            "lock_name": lock_name,
            "expected_owner": payload["expected_owner"],
            "user_authorized": True,
        }
    if repair_type == "redact-response":
        require_object_keys(
            payload,
            required={
                "repair_type",
                "response_id",
                "redactions",
                "reason",
                "correction_response",
                "user_authorized",
            },
            optional=set(),
            label="response redaction payload",
        )
        if payload["user_authorized"] is not True:
            raise TaskError(EXIT_INVALID, "USER_AUTHORIZATION_REQUIRED", "Response redaction requires explicit user authorization.")
        response_id = require_text(payload["response_id"], "response_id", max_length=30)
        reason = require_text(payload["reason"], "reason", max_length=MAX_ITEM)
        assert isinstance(response_id, str) and isinstance(reason, str)
        if not RESPONSE_ID_RE.fullmatch(response_id):
            raise TaskError(EXIT_INVALID, "RESPONSE_ID", "response_id is not canonical.")
        redactions = require_string_list(payload["redactions"], "redactions", nonempty=True)
        if len(set(redactions)) != len(redactions):
            raise TaskError(EXIT_INVALID, "REDACTION_DUPLICATE", "redactions contains a duplicate exact value.")
        if not isinstance(payload["correction_response"], dict):
            raise TaskError(EXIT_INVALID, "CORRECTION_RESPONSE", "correction_response must be a response payload object.")
        return {
            "repair_type": repair_type,
            "response_id": response_id,
            "redactions": redactions,
            "reason": reason,
            "correction_response": payload["correction_response"],
            "user_authorized": True,
        }
    raise TaskError(EXIT_INVALID, "REPAIR_TYPE", "Unsupported reconcile repair_type.")


def cleanup_staged_response(tasks_root: Path, raw_relative: Any) -> None:
    if not isinstance(raw_relative, str):
        return
    candidate = Path(raw_relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return
    target = (tasks_root / candidate).resolve(strict=False)
    if not within(target, tasks_root) or target.is_symlink():
        return
    if target.is_file() and target.name.endswith(".txn"):
        target.unlink(missing_ok=True)


def write_reconcile_receipt(tasks_root: Path, operation_id: str, task_id: str | None, status: str) -> Path:
    _, tmp_root = ensure_runtime_directories(tasks_root)
    receipt = tmp_root / f"reconciled-{operation_id}.json"
    atomic_write_json(
        receipt,
        {
            "schema_version": 1,
            "operation_id": operation_id,
            "task_id": task_id,
            "status": status,
            "reconciled_at": now_local(),
        },
    )
    return receipt


def task_response_path_from_id(state: dict[str, Any], folder: Path, response_id: str) -> Path:
    match = RESPONSE_ID_RE.fullmatch(response_id)
    if not match:
        raise TaskError(EXIT_INVALID, "RESPONSE_ID", "Response ID is not canonical.")
    sequence = int(match.group(1))
    if sequence < 1 or sequence > state["response_count"]:
        raise TaskError(EXIT_NOT_FOUND, "RESPONSE_NOT_FOUND", "Response ID is not committed in the selected task.")
    candidates: list[Path] = []
    responses = folder / "responses"
    if responses.is_symlink() or not responses.is_dir():
        raise TaskError(EXIT_INTEGRITY, "RESPONSES_DIRECTORY", "responses/ is missing or unsafe.")
    for entry in responses.iterdir():
        match_file = RESPONSE_FILE_RE.fullmatch(entry.name)
        if match_file and int(match_file.group(1)) == sequence:
            candidates.append(entry)
    if len(candidates) != 1 or candidates[0].is_symlink() or not candidates[0].is_file():
        raise TaskError(
            EXIT_INTEGRITY,
            "RESPONSE_IDENTITY",
            "Response ID does not resolve to exactly one safe response file.",
            details={"response_id": response_id, "candidate_count": len(candidates)},
            recovery_required=True,
        )
    return candidates[0]


def validate_intent_response_path(folder: Path, raw_path: Any, label: str) -> Path:
    if not isinstance(raw_path, str):
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_RESPONSE_PATH", f"{label} is missing or invalid.", recovery_required=True)
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("responses",):
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_RESPONSE_PATH", f"{label} is unsafe.", recovery_required=True)
    target = folder / relative
    if not within(target.resolve(strict=False), folder.resolve(strict=True)):
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_RESPONSE_PATH", f"{label} escapes the task folder.", recovery_required=True)
    if target.is_symlink():
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_RESPONSE_SYMLINK", f"{label} cannot be a symlink.", recovery_required=True)
    return target


def reconcile_redaction_intent(
    project_root: Path,
    tasks_root: Path,
    selector: str | None,
    expected_revision: int | None,
    operation_id: str,
    intent_path: Path,
    intent: dict[str, Any],
    actor_payload=None,
) -> dict[str, Any]:
    result = base_result("reconcile", project_root, tasks_root)
    task_id = intent.get("task_id")
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_TASK_ID", "Redaction intent has an invalid task ID.", recovery_required=True)
    if selector is not None and selector.upper() != task_id:
        raise TaskError(EXIT_INVALID, "RECONCILE_SELECTOR", "Reconcile selector must be the exact task ID from the intent.")
    if expected_revision is None or expected_revision != intent.get("expected_revision"):
        raise TaskError(EXIT_REVISION, "RECONCILE_REVISION", "Reconcile requires the redaction intent's exact expected revision.")
    planned = intent.get("planned_state")
    if not isinstance(planned, dict):
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_PLANNED_STATE", "Redaction intent has no exact planned state.", recovery_required=True)
    try:
        planned = canonical_state(planned)
    except (KeyError, TypeError) as exc:
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_PLANNED_STATE", "Redaction planned state is malformed.", recovery_required=True) from exc
    operation = new_operation_id()
    with acquire_lock(tasks_root, "catalog", operation_id=operation, command="reconcile-redaction", task_id=task_id):
        with acquire_lock(tasks_root, task_id, operation_id=operation, command="reconcile-redaction", task_id=task_id):
            catalog = scan_catalog(
                tasks_root,
                ignore_catalog_lock=True,
                check_projections=False,
                check_transactions=False,
            )
            if task_id not in catalog["states"]:
                raise TaskError(EXIT_INTEGRITY, "RECONCILE_TASK_MISSING", "Redaction task is missing.", recovery_required=True)
            state = catalog["states"][task_id]
            folder = catalog["folders"][task_id]
            planned_errors = validate_state_shape(planned, folder, task_json_text(planned))
            if planned_errors:
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_PLANNED_STATE", "Redaction planned state is invalid.", details={"findings": planned_errors})
            if intent.get("schema_version") == 2:
                expected_keys = {"schema_version", "kind", "operation_id", "command", "task_id", "expected_revision", "old_response_id", "old_response_path", "original_sha256", "redacted_sha256", "redacted_content", "correction_response_id", "correction_response_path", "correction_response_sha256", "correction_response_content", "staged_response_path", "planned_state", "created_at", "pre_state_sha256", "post_state_sha256", "actor", "execution_id", "generation"}
                require_object_keys(intent, required=expected_keys, optional=set(), label="schema-2 redaction intent")
                live_sha = hashlib.sha256((folder / "task.json").read_bytes()).hexdigest()
                if live_sha not in (intent["pre_state_sha256"], intent["post_state_sha256"]) or hashlib.sha256(task_json_text(planned).encode()).hexdigest() != intent["post_state_sha256"]:
                    raise TaskError(EXIT_INTEGRITY, "ORCH_RECOVERY_STATE_HASH", "Redaction state bytes differ from the exact reviewed transaction.")
                if any((actor_payload or {}).get(k) != intent[k] for k in ("actor", "execution_id", "generation")):
                    orchestration_call(orch.auth, state, actor_payload or {})
            elif intent.get("schema_version") != 1:
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_INTENT_SCHEMA", "Unsupported redaction intent version.")
            old_path = validate_intent_response_path(folder, intent.get("old_response_path"), "old_response_path")
            correction_path = validate_intent_response_path(
                folder,
                intent.get("correction_response_path"),
                "correction_response_path",
            )
            redacted_content = intent.get("redacted_content")
            correction_content = intent.get("correction_response_content")
            if not isinstance(redacted_content, str) or hashlib.sha256(redacted_content.encode("utf-8")).hexdigest() != intent.get("redacted_sha256"):
                raise TaskError(EXIT_INTEGRITY, "REDACTION_INTENT_HASH", "Redacted content evidence is missing or changed.", recovery_required=True)
            if not isinstance(correction_content, str) or hashlib.sha256(correction_content.encode("utf-8")).hexdigest() != intent.get("correction_response_sha256"):
                raise TaskError(EXIT_INTEGRITY, "REDACTION_CORRECTION_HASH", "Correction response evidence is missing or changed.", recovery_required=True)
            if not old_path.is_file():
                raise TaskError(EXIT_INTEGRITY, "REDACTION_TARGET_MISSING", "The response selected for redaction is missing.", recovery_required=True)

            if correction_path.exists():
                if not correction_path.is_file() or hashlib.sha256(correction_path.read_bytes()).hexdigest() != intent["correction_response_sha256"]:
                    raise TaskError(EXIT_INTEGRITY, "REDACTION_CORRECTION_MISMATCH", "Published correction response differs from intent evidence.", recovery_required=True)
            else:
                staged = write_staged_text(correction_path, correction_content)
                _ontology_checkpoint(targets=False)
                os.replace(staged, correction_path)

            if state["revision"] == intent["expected_revision"]:
                atomic_write_text(folder / "task.json", task_json_text(planned))
                state = planned
            elif state["revision"] == planned["revision"]:
                state = planned
            else:
                raise TaskError(
                    EXIT_INTEGRITY,
                    "REDACTION_STATE_MISMATCH",
                    "Current revision does not match the redaction transaction.",
                    details={
                        "current_revision": state["revision"],
                        "expected_revision": intent["expected_revision"],
                        "planned_revision": planned["revision"],
                    },
                    recovery_required=True,
                )

            old_hash = hashlib.sha256(old_path.read_bytes()).hexdigest()
            if old_hash == intent.get("original_sha256"):
                atomic_write_text(old_path, redacted_content)
            elif old_hash != intent.get("redacted_sha256"):
                raise TaskError(EXIT_INTEGRITY, "REDACTION_TARGET_CHANGED", "The response selected for redaction changed after approval.", recovery_required=True)

            atomic_write_text(folder / "TASK.md", render_task_markdown(state))
            refreshed = scan_catalog(
                tasks_root,
                ignore_catalog_lock=True,
                check_projections=False,
                check_transactions=False,
            )
            require_valid_catalog(refreshed)
            write_index(tasks_root, list(refreshed["states"].values()))
            cleanup_staged_response(tasks_root, intent.get("staged_response_path"))
            receipt = write_reconcile_receipt(tasks_root, operation_id, task_id, "response_redaction_reconciled")
            intent_path.unlink(missing_ok=True)
            result.update(
                {
                    "status": "response_redaction_reconciled",
                    "mutated": True,
                    "task_id": task_id,
                    "revision_before": intent["expected_revision"],
                    "revision_after": state["revision"],
                    "response_id": intent.get("correction_response_id"),
                    "response_path": str(correction_path),
                    "reconciliation_receipt": str(receipt),
                }
            )
            return result


def reconcile_transaction(
    project_root: Path,
    tasks_root: Path,
    selector: str | None,
    expected_revision: int | None,
    operation_id: str,
    actor_payload=None,
) -> dict[str, Any]:
    result = base_result("reconcile", project_root, tasks_root)
    _, tmp_root = ensure_runtime_directories(tasks_root)
    intent_path = tmp_root / f"{operation_id}.json"
    receipt_path = tmp_root / f"reconciled-{operation_id}.json"
    if not intent_path.exists():
        if receipt_path.is_file() and not receipt_path.is_symlink():
            receipt, _ = read_json_file(receipt_path, "reconciliation receipt")
            result.update({"status": "already_reconciled", "task_id": receipt.get("task_id"), "reconciliation_receipt": str(receipt_path)})
            return result
        raise TaskError(EXIT_NOT_FOUND, "TRANSACTION_INTENT_NOT_FOUND", "Exact transaction intent was not found.")
    intent, _ = read_json_file(intent_path, "transaction intent")
    if intent.get("operation_id") != operation_id:
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_INTENT_SCHEMA", "Transaction intent identity is invalid.", recovery_required=True)
    if intent.get("kind") == "redaction_transaction":
        return reconcile_redaction_intent(
            project_root,
            tasks_root,
            selector,
            expected_revision,
            operation_id,
            intent_path,
            intent,
            actor_payload=actor_payload,
        )
    if intent.get("kind") != "response_transaction":
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_INTENT_SCHEMA", "Transaction intent kind is invalid.", recovery_required=True)
    task_id = intent.get("task_id")
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise TaskError(EXIT_INTEGRITY, "TRANSACTION_TASK_ID", "Transaction intent has an invalid task ID.", recovery_required=True)
    if selector is not None and selector.upper() != task_id:
        raise TaskError(EXIT_INVALID, "RECONCILE_SELECTOR", "Reconcile selector must be the exact task ID from the intent.")
    if expected_revision is None or expected_revision != intent.get("expected_revision"):
        raise TaskError(EXIT_REVISION, "RECONCILE_REVISION", "Reconcile requires the intent's exact expected revision.")
    operation = new_operation_id()
    with acquire_lock(tasks_root, "catalog", operation_id=operation, command="reconcile", task_id=task_id):
        with acquire_lock(tasks_root, task_id, operation_id=operation, command="reconcile", task_id=task_id):
            catalog = scan_catalog(
                tasks_root,
                ignore_catalog_lock=True,
                check_projections=False,
                check_transactions=False,
            )
            if task_id not in catalog["states"]:
                raise TaskError(EXIT_INTEGRITY, "RECONCILE_TASK_MISSING", "Transaction task is missing.", recovery_required=True)
            state = catalog["states"][task_id]
            folder = catalog["folders"][task_id]
            planned = intent.get("planned_state")
            if not isinstance(planned, dict):
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_PLANNED_STATE", "Transaction intent has no exact planned state.", recovery_required=True)
            planned_errors = validate_state_shape(planned, folder, task_json_text(planned))
            if planned_errors:
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_PLANNED_STATE", "Exact planned state is invalid.", details={"findings": planned_errors}, recovery_required=True)
            if intent.get("schema_version") == 2:
                expected_keys = {"schema_version", "kind", "operation_id", "command", "task_id", "expected_revision", "response_id", "response_path", "response_sha256", "response_content", "staged_response_path", "planned_state", "created_at", "pre_state_sha256", "post_state_sha256", "actor", "execution_id", "generation", "event_id", "event_sha256", "artifacts"}
                require_object_keys(intent, required=expected_keys, optional=set(), label="schema-2 transaction intent")
                if hashlib.sha256(task_json_text(planned).encode()).hexdigest() != intent["post_state_sha256"]:
                    raise TaskError(EXIT_INTEGRITY, "ORCH_POST_STATE_HASH", "Planned state digest differs from intent.")
                live_sha = hashlib.sha256((folder / "task.json").read_bytes()).hexdigest()
                if live_sha not in (intent["pre_state_sha256"], intent["post_state_sha256"]):
                    raise TaskError(EXIT_INTEGRITY, "ORCH_RECOVERY_STATE_HASH", "Same revision does not authorize recovery over different bytes.")
                if intent["command"] != "upgrade-orchestration":
                    auth_input = actor_payload or {}
                    if any(auth_input.get(k) != intent[k] for k in ("actor", "execution_id", "generation")):
                        orchestration_call(orch.auth, state, auth_input)
            elif intent.get("schema_version") != 1:
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_INTENT_SCHEMA", "Unsupported transaction intent version.")
            try:
                planned = canonical_state(planned)
            except (KeyError, TypeError) as exc:
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_PLANNED_STATE", "Transaction planned state is malformed.", recovery_required=True) from exc
            response_rel = intent.get("response_path")
            if not isinstance(response_rel, str):
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_RESPONSE_PATH", "Transaction response path is invalid.", recovery_required=True)
            response_candidate = Path(response_rel)
            if response_candidate.is_absolute() or ".." in response_candidate.parts or response_candidate.parts[:1] != ("responses",):
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_RESPONSE_PATH", "Transaction response path is unsafe.", recovery_required=True)
            response_path = folder / response_candidate
            if response_path.is_symlink():
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_RESPONSE_SYMLINK", "Transaction response target cannot be a symlink.", recovery_required=True)
            response_content = intent.get("response_content")
            if not isinstance(response_content, str) or hashlib.sha256(response_content.encode("utf-8")).hexdigest() != intent.get("response_sha256"):
                raise TaskError(EXIT_INTEGRITY, "TRANSACTION_RESPONSE_HASH", "Transaction response evidence is missing or changed.", recovery_required=True)

            expected = intent["expected_revision"]
            planned_revision = planned["revision"]
            artifacts_published = any((folder / a["path"]).exists() for a in intent.get("artifacts", []))
            if state["revision"] == expected and not response_path.exists() and not artifacts_published:
                cleanup_staged_response(tasks_root, intent.get("staged_response_path"))
                receipt = write_reconcile_receipt(tasks_root, operation_id, task_id, "aborted_transaction_cleaned")
                intent_path.unlink(missing_ok=True)
                result.update(
                    {
                        "status": "aborted_transaction_cleaned",
                        "mutated": True,
                        "task_id": task_id,
                        "revision_before": state["revision"],
                        "revision_after": state["revision"],
                        "reconciliation_receipt": str(receipt),
                    }
                )
                return result

            if intent.get("schema_version") == 2 and intent.get("artifacts"):
                publish_orchestration_artifacts(folder, intent, allow_existing=True)
                if state["revision"] == expected and not response_path.exists():
                    staged = write_staged_text(response_path, response_content)
                    _ontology_checkpoint(targets=False)
                    os.replace(staged, response_path)
            if state["revision"] == expected and response_path.is_file() and not response_path.is_symlink():
                if hashlib.sha256(response_path.read_bytes()).hexdigest() != intent["response_sha256"]:
                    raise TaskError(EXIT_INTEGRITY, "ORPHAN_RESPONSE_HASH", "Published orphan response differs from transaction evidence.", recovery_required=True)
                atomic_write_text(folder / "task.json", task_json_text(planned))
                state = planned
            elif state["revision"] == planned_revision and not response_path.exists():
                staged = write_staged_text(response_path, response_content)
                _ontology_checkpoint(targets=False)
                os.replace(staged, response_path)
                state = planned
            elif state["revision"] == planned_revision and response_path.is_file() and not response_path.is_symlink():
                if hashlib.sha256(response_path.read_bytes()).hexdigest() != intent["response_sha256"]:
                    raise TaskError(EXIT_INTEGRITY, "COMMITTED_RESPONSE_HASH", "Committed response differs from transaction evidence.", recovery_required=True)
                state = planned
            else:
                raise TaskError(
                    EXIT_INTEGRITY,
                    "RECONCILE_STATE_MISMATCH",
                    "Current state does not match the transaction's recoverable classes.",
                    details={"current_revision": state["revision"], "expected_revision": expected, "planned_revision": planned_revision},
                    recovery_required=True,
                )

            atomic_write_text(folder / "TASK.md", render_task_markdown(state))
            refreshed = scan_catalog(
                tasks_root,
                ignore_catalog_lock=True,
                check_projections=False,
                check_transactions=False,
            )
            require_valid_catalog(refreshed)
            write_index(tasks_root, list(refreshed["states"].values()))
            cleanup_staged_response(tasks_root, intent.get("staged_response_path"))
            receipt = write_reconcile_receipt(tasks_root, operation_id, task_id, "transaction_reconciled")
            intent_path.unlink(missing_ok=True)
            result.update(
                {
                    "status": "transaction_reconciled",
                    "mutated": True,
                    "task_id": task_id,
                    "revision_before": expected,
                    "revision_after": state["revision"],
                    "response_id": intent.get("response_id"),
                    "response_path": str(response_path),
                    "reconciliation_receipt": str(receipt),
                }
            )
            return result


def reconcile_lock(project_root: Path, tasks_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    lock_name = payload["lock_name"]
    locks_root = tasks_root / ".locks"
    if locks_root.is_symlink() or not locks_root.is_dir():
        raise TaskError(EXIT_INTEGRITY, "LOCK_ROOT_UNSAFE", "Tasks/.locks is not a safe directory.")
    lock_dir = locks_root / f"{lock_name}.lock"
    if lock_dir.is_symlink() or not lock_dir.is_dir():
        raise TaskError(EXIT_NOT_FOUND, "LOCK_NOT_FOUND", "Exact lock directory was not found.")
    owner_path = lock_dir / "owner.json"
    if owner_path.is_symlink() or not owner_path.is_file():
        raise TaskError(EXIT_LOCK, "LOCK_OWNER_UNSAFE", "Lock owner metadata is missing or unsafe.", recovery_required=True)
    actual_owner, _ = read_json_file(owner_path, "lock owner")
    expected_owner_fields = {"operation_id", "command", "task_id", "acquired_at", "process_id"}
    if set(actual_owner) != expected_owner_fields:
        raise TaskError(
            EXIT_LOCK,
            "LOCK_OWNER_FIELDS",
            "Lock owner metadata contains missing or unexpected fields.",
            details={"fields": sorted(actual_owner)},
            recovery_required=True,
        )
    if actual_owner != payload["expected_owner"]:
        raise TaskError(
            EXIT_LOCK,
            "LOCK_OWNER_MISMATCH",
            "Lock owner metadata changed or does not match the approved recovery plan.",
            details={"actual_owner": actual_owner},
            recovery_required=True,
        )
    if lock_name != "catalog":
        catalog = scan_catalog(tasks_root, ignore_catalog_lock=True, check_transactions=False, check_projections=False)
        if lock_name in catalog["states"]:
            orchestration_call(orch.auth, catalog["states"][lock_name], payload, allow_unassigned=True)
    entries = list(lock_dir.iterdir())
    if len(entries) != 1 or entries[0].name != "owner.json" or entries[0].is_symlink() or not entries[0].is_file():
        raise TaskError(EXIT_LOCK, "LOCK_CONTENT_AMBIGUOUS", "Lock directory contains unexpected data and was not removed.", recovery_required=True)
    entries[0].unlink()
    lock_dir.rmdir()
    result = base_result("reconcile", project_root, tasks_root)
    result.update({"status": "lock_removed", "mutated": True, "task_id": None if lock_name == "catalog" else lock_name})
    return result


def reconcile_response_redaction(
    project_root: Path,
    tasks_root: Path,
    selector: str | None,
    expected_revision: int | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if selector is None:
        raise TaskError(EXIT_INVALID, "REDACTION_SELECTOR", "Response redaction requires an exact task ID selector.")
    validate_selector_text(selector)
    task_id = selector.upper()
    if not TASK_ID_RE.fullmatch(task_id):
        raise TaskError(EXIT_INVALID, "REDACTION_SELECTOR", "Response redaction selector must be an exact canonical task ID.")
    if expected_revision is None or expected_revision < 1:
        raise TaskError(EXIT_REVISION, "REDACTION_REVISION", "Response redaction requires the current expected revision.")
    reject_secrets(payload["reason"])
    operation_id = new_operation_id()
    result = base_result("reconcile", project_root, tasks_root)
    intent_path: Path | None = None
    correction_path: Path | None = None
    correction_id: str | None = None
    staged_response: Path | None = None
    core_committed = False
    try:
        with acquire_lock(tasks_root, "catalog", operation_id=operation_id, command="redact-response", task_id=task_id):
            with acquire_lock(tasks_root, task_id, operation_id=operation_id, command="redact-response", task_id=task_id):
                catalog = scan_catalog(
                    tasks_root,
                    ignore_catalog_lock=True,
                    check_projections=False,
                    check_transactions=False,
                )
                if task_id not in catalog["states"]:
                    raise TaskError(EXIT_NOT_FOUND, "TASK_NOT_FOUND", "Exact task ID was not found for response redaction.")
                state = catalog["states"][task_id]
                folder = catalog["folders"][task_id]
                if state["revision"] != expected_revision:
                    raise TaskError(
                        EXIT_REVISION,
                        "REVISION_CONFLICT",
                        "Expected revision does not match canonical state.",
                        details={"expected_revision": expected_revision, "actual_revision": state["revision"], "task_id": task_id},
                    )
                orchestration_call(orch.auth, state, payload, allow_unassigned=True)
                old_path = task_response_path_from_id(state, folder, payload["response_id"])
                unrelated_errors = [
                    item
                    for item in catalog["errors"]
                    if item.get("code") != "SECRET_IN_RESPONSE" or item.get("path") != str(old_path)
                ]
                if unrelated_errors:
                    raise TaskError(
                        EXIT_INTEGRITY,
                        "CATALOG_INVALID",
                        "Unrelated integrity errors prevent safe response redaction.",
                        details={"findings": unrelated_errors},
                        recovery_required=True,
                    )
                old_text = old_path.read_text(encoding="utf-8")
                redacted_text = old_text
                for exact_value in payload["redactions"]:
                    if exact_value not in redacted_text:
                        raise TaskError(
                            EXIT_INVALID,
                            "REDACTION_VALUE_NOT_FOUND",
                            "An approved exact redaction value is not present in the selected response.",
                        )
                    redacted_text = redacted_text.replace(exact_value, "[REDACTED]")
                reject_secrets(redacted_text)
                redacted_table, redacted_errors = parse_response_text(old_path, redacted_text)
                if redacted_errors or redacted_table.get("Response ID") != payload["response_id"]:
                    raise TaskError(
                        EXIT_INTEGRITY,
                        "REDACTED_RESPONSE_INVALID",
                        "Redaction would damage the Task Response structure.",
                        details={"findings": redacted_errors},
                    )

                raw_correction = dict(payload["correction_response"])
                supplied_supersedes = raw_correction.get("supersedes_response_id")
                if supplied_supersedes not in (None, payload["response_id"]):
                    raise TaskError(EXIT_INVALID, "SUPERSEDES_TARGET", "Correction response must supersede the redacted response.")
                raw_correction["supersedes_response_id"] = payload["response_id"]
                correction = validate_response_payload(raw_correction, "record-response", state, project_root)
                if correction.get("status_after") not in (None, state["status"]):
                    raise TaskError(EXIT_INVALID, "REDACTION_STATUS_CHANGE", "A response redaction cannot change lifecycle status.")
                for key in ("current_summary", "next_step", "blockers", "open_questions"):
                    if correction[key] != state[key]:
                        raise TaskError(EXIT_INVALID, "REDACTION_MEANING_CHANGE", f"A response redaction cannot change canonical {key}.")
                correction["work_completed"] = [
                    f"Applied an explicitly authorized security or privacy correction: {payload['reason']}"
                ] + correction["work_completed"]
                reject_secrets(correction)

                timestamp = now_local()
                updated = apply_state_updates(state, correction, state["status"], timestamp)
                sequence = updated["response_count"]
                correction_id = canonical_response_id(sequence)
                filename = canonical_response_filename(sequence, timestamp)
                relpath = f"responses/{filename}"
                updated["last_response"] = {
                    "response_id": correction_id,
                    "sequence": sequence,
                    "created_at": timestamp,
                    "path": relpath,
                    "supersedes_response_id": payload["response_id"],
                }
                updated = canonical_state(updated)
                correction_text = render_response_markdown(
                    state,
                    updated,
                    correction,
                    correction_id,
                    timestamp,
                )
                reject_secrets(correction_text)
                correction_path = folder / relpath
                if correction_path.exists() or correction_path.is_symlink():
                    raise TaskError(EXIT_INTEGRITY, "RESPONSE_COLLISION", "Correction Task Response path already exists.")
                planned_errors = validate_state_shape(updated, folder, task_json_text(updated))
                if planned_errors:
                    raise TaskError(EXIT_INTEGRITY, "PLANNED_STATE_INVALID", "Planned correction state failed validation.", details={"findings": planned_errors})
                _, correction_errors = parse_response_text(correction_path, correction_text)
                if correction_errors:
                    raise TaskError(EXIT_INTEGRITY, "PLANNED_RESPONSE_INVALID", "Correction Task Response failed validation.", details={"findings": correction_errors})

                _, tmp_root = ensure_runtime_directories(tasks_root)
                staged_response = write_staged_text(correction_path, correction_text)
                intent = {
                    "schema_version": 1,
                    "kind": "redaction_transaction",
                    "operation_id": operation_id,
                    "command": "redact-response",
                    "task_id": task_id,
                    "expected_revision": expected_revision,
                    "old_response_id": payload["response_id"],
                    "old_response_path": str(old_path.relative_to(folder)),
                    "original_sha256": hashlib.sha256(old_text.encode("utf-8")).hexdigest(),
                    "redacted_sha256": hashlib.sha256(redacted_text.encode("utf-8")).hexdigest(),
                    "redacted_content": redacted_text,
                    "correction_response_id": correction_id,
                    "correction_response_path": relpath,
                    "correction_response_sha256": hashlib.sha256(correction_text.encode("utf-8")).hexdigest(),
                    "correction_response_content": correction_text,
                    "staged_response_path": str(staged_response.relative_to(tasks_root)),
                    "planned_state": updated,
                    "created_at": timestamp,
                }
                if state["schema_version"] == 2:
                    intent.update(schema_version=2, pre_state_sha256=hashlib.sha256((folder / "task.json").read_bytes()).hexdigest(), post_state_sha256=hashlib.sha256(task_json_text(updated).encode()).hexdigest(), actor=payload.get("actor"), execution_id=payload.get("execution_id"), generation=payload.get("generation"))
                intent_content = transaction_intent_text(intent)
                intent_path = tmp_root / f"{operation_id}.json"
                atomic_write_text(intent_path, intent_content)
                inject_fault("before_redaction_correction_publish")
                _ontology_checkpoint(targets=False)
                os.replace(staged_response, correction_path)
                staged_response = None
                inject_fault("after_redaction_correction_publish")
                atomic_write_text(folder / "task.json", task_json_text(updated))
                core_committed = True
                inject_fault("after_redaction_state_publish")
                atomic_write_text(old_path, redacted_text)
                inject_fault("after_redaction_publish")
                atomic_write_text(folder / "TASK.md", render_task_markdown(updated))
                refreshed = scan_catalog(
                    tasks_root,
                    ignore_catalog_lock=True,
                    check_projections=False,
                    check_transactions=False,
                )
                require_valid_catalog(refreshed)
                write_index(tasks_root, list(refreshed["states"].values()))
                intent_path.unlink(missing_ok=True)
                intent_path = None
                result.update(
                    {
                        "status": "response_redacted",
                        "mutated": True,
                        "task_id": task_id,
                        "revision_before": state["revision"],
                        "revision_after": updated["revision"],
                        "response_id": correction_id,
                        "response_path": str(correction_path),
                        "redacted_response_id": payload["response_id"],
                        "redacted_response_path": str(old_path),
                    }
                )
                return result
    except TaskError as exc:
        if intent_path is None and not core_committed and not (correction_path and correction_path.exists()):
            if staged_response is not None:
                cleanup_staged_response(tasks_root, str(staged_response.relative_to(tasks_root)))
            raise
        details = {
            "operation_id": operation_id,
            "diagnostic": exc.message,
            "task_id": task_id,
            "canonical_core_committed": core_committed,
        }
        if correction_id:
            details["response_id"] = correction_id
        if correction_path:
            details["response_path"] = str(correction_path)
        raise TaskError(
            EXIT_TRANSACTION,
            "REDACTION_TRANSACTION_INCOMPLETE",
            "Response redaction did not complete; explicit validation and reconciliation are required.",
            details=details,
            recovery_required=True,
        ) from exc
    except Exception as exc:
        details = {
            "operation_id": operation_id,
            "diagnostic": str(exc),
            "task_id": task_id,
            "canonical_core_committed": core_committed,
        }
        if correction_id:
            details["response_id"] = correction_id
        if correction_path:
            details["response_path"] = str(correction_path)
        raise TaskError(
            EXIT_TRANSACTION,
            "REDACTION_TRANSACTION_INCOMPLETE",
            "Response redaction did not complete; explicit validation and reconciliation are required.",
            details=details,
            recovery_required=True,
        ) from exc


def command_reconcile(
    project_root: Path,
    tasks_root: Path,
    selector: str | None,
    expected_revision: int | None,
    raw_payload: dict[str, Any],
) -> dict[str, Any]:
    payload = validate_reconcile_payload(raw_payload)
    if payload["repair_type"] == "remove-lock":
        return reconcile_lock(project_root, tasks_root, payload)
    if payload["repair_type"] == "redact-response":
        return reconcile_response_redaction(
            project_root,
            tasks_root,
            selector,
            expected_revision,
            payload,
        )
    return reconcile_transaction(project_root, tasks_root, selector, expected_revision, payload["operation_id"], actor_payload=payload)


def format_markdown(result: dict[str, Any]) -> str:
    if result["command"] == "status":
        counts = result.get("counts", {})
        lines = ["# Task status", "", f"Integrity: {result.get('integrity', result['status'])}", ""]
        lines.append("Counts: " + ", ".join(f"{key}={counts.get(key, 0)}" for key in STATUSES))
        candidates = result.get("nonterminal_candidates", [])
        if candidates:
            lines.extend(["", "| Task ID | Name | Status | Description | Next step |", "| --- | --- | --- | --- | --- |"])
            for item in candidates:
                lines.append(
                    "| "
                    + " | ".join(markdown_inline(item[key]) for key in ("task_id", "name", "status", "description", "next_step"))
                    + " |"
                )
        return "\n".join(lines) + "\n"
    if result["command"] == "list":
        lines = ["# Tasks", "", "| Task ID | Name | Status | Updated | Next step |", "| --- | --- | --- | --- | --- |"]
        for item in result.get("tasks", []):
            lines.append(
                "| "
                + " | ".join(markdown_inline(item[key]) for key in ("task_id", "name", "status", "updated_at", "next_step"))
                + " |"
            )
        if not result.get("tasks"):
            lines.append("| None | None | None | None | None |")
        return "\n".join(lines) + "\n"
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def emit(result: dict[str, Any], output_format: str) -> None:
    if output_format == "markdown":
        sys.stdout.write(format_markdown(result))
    else:
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the project-local Task ledger.")
    parser.add_argument("--project-root", required=True, help="Exact project root containing AGENTS.md, SOUL.md, and ROLE.md")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def allow_documented_format_position(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument(
            "--format",
            choices=("json", "markdown"),
            default=argparse.SUPPRESS,
            help="Output format; accepted here for the documented command form",
        )

    status = subparsers.add_parser("status", help="Read-only catalog status")
    allow_documented_format_position(status)
    status.add_argument("--limit", type=int, default=3)

    list_parser = subparsers.add_parser("list", help="Read-only deterministic task list")
    allow_documented_format_position(list_parser)
    list_parser.add_argument("--status", action="append", choices=STATUSES, dest="statuses")

    for command in ("show", "continue", "upgrade-preview"):
        sub = subparsers.add_parser(command, help=f"Read-only {command} operation")
        allow_documented_format_position(sub)
        sub.add_argument("selector")

    new = subparsers.add_parser("new", help="Create a task from JSON")
    allow_documented_format_position(new)
    new.add_argument("--payload-file", default="-", help="One-use JSON payload path, or - for stdin")

    intake = subparsers.add_parser("intake", help="Close inactive tasks and match or create explicitly requested work")
    allow_documented_format_position(intake)
    intake.add_argument("--match-task", help="Exact task selector chosen by the Director after reviewing the work objective")
    intake.add_argument("--payload-file", default="-", help="One-use new-task JSON payload path, or - for stdin")

    for command in ("update", "record-response", "pause", "complete", "cancel", "reopen", "close-old-task", "orchestrate", "upgrade-orchestration"):
        sub = subparsers.add_parser(command, help=f"Run a {command} response transaction")
        allow_documented_format_position(sub)
        sub.add_argument("selector")
        sub.add_argument("--expected-revision", required=True, type=int)
        sub.add_argument("--payload-file", default="-", help="One-use JSON payload path, or - for stdin")

    validate = subparsers.add_parser("validate", help="Validate the catalog or one task")
    allow_documented_format_position(validate)
    validate.add_argument("selector", nargs="?")

    rebuild = subparsers.add_parser("rebuild-projections", help="Regenerate TASK.md and INDEX.md")
    allow_documented_format_position(rebuild)
    rebuild.add_argument("selector", nargs="?")
    rebuild.add_argument("--actor")
    rebuild.add_argument("--execution-id")
    rebuild.add_argument("--generation", type=int)
    rebuild.add_argument("--bootstrap-receipt", help="Project-relative native roster JSON for maintenance before an execution exists")

    reconcile = subparsers.add_parser("reconcile", help="Apply an explicit bounded recovery payload")
    allow_documented_format_position(reconcile)
    reconcile.add_argument("selector", nargs="?")
    reconcile.add_argument("--expected-revision", type=int)
    reconcile.add_argument("--payload-file", default="-", help="One-use JSON payload path, or - for stdin")
    return parser


def run(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    project_root = establish_project_root(args.project_root)
    tasks_root = get_tasks_root(project_root)
    command = args.command
    if command == "status":
        if args.limit < 1 or args.limit > 100:
            raise TaskError(EXIT_INVALID, "LIMIT", "status --limit must be between 1 and 100.")
        result = command_status(project_root, tasks_root, args.limit)
        return result, EXIT_INTEGRITY if result["errors"] else EXIT_OK
    if command == "list":
        result = command_list(project_root, tasks_root, args.statuses)
        return result, EXIT_INTEGRITY if result["errors"] else EXIT_OK
    if command == "show":
        return command_show(project_root, tasks_root, args.selector), EXIT_OK
    if command == "continue":
        return command_show(project_root, tasks_root, args.selector, continuation=True), EXIT_OK
    if command == "upgrade-preview":
        return upgrade_preview(project_root, tasks_root, args.selector), EXIT_OK
    if command == "validate":
        result = command_validate(project_root, tasks_root, args.selector)
        return result, EXIT_INTEGRITY if result["errors"] else EXIT_OK
    if command == "rebuild-projections":
        actor_payload = {"actor": args.actor, "execution_id": args.execution_id, "generation": args.generation}
        if args.bootstrap_receipt:
            receipt_path = orchestration_call(orch.confined, project_root, args.bootstrap_receipt, must_exist=True)
            actor_payload["bootstrap_receipt"] = read_json_file(receipt_path, "bootstrap receipt")[0]
        return command_rebuild(project_root, tasks_root, args.selector, actor_payload), EXIT_OK

    payload: dict[str, Any] | None = None
    payload_path: Path | None = None
    try:
        payload, payload_path = load_payload(args.payload_file, project_root, tasks_root)
        if command == "new":
            return command_new(project_root, tasks_root, payload), EXIT_OK
        if command == "intake":
            return command_intake(project_root, tasks_root, payload, args.match_task), EXIT_OK
        if command == "reconcile":
            return command_reconcile(project_root, tasks_root, args.selector, args.expected_revision, payload), EXIT_OK
        return (
            response_transaction(
                command,
                project_root,
                tasks_root,
                args.selector,
                args.expected_revision,
                payload,
            ),
            EXIT_OK,
        )
    finally:
        remove_payload(payload_path)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result, exit_code = run(args)
    except TaskError as exc:
        try:
            project_root = Path(args.project_root).expanduser().resolve(strict=False)
        except Exception:
            project_root = Path(args.project_root)
        tasks_root = project_root / "Tasks"
        result = base_result(args.command, project_root, tasks_root)
        result.update(
            {
                "status": "error",
                "errors": [exc.finding()],
                "recovery_required": exc.recovery_required,
            }
        )
        for key in ("task_id", "response_id", "response_path"):
            if key in exc.details:
                result[key] = exc.details[key]
        for key in ("closed_tasks", "intake_result", "failed_operation", "mutated"):
            if key in exc.details:
                result[key] = exc.details[key]
        if "result_status" in exc.details:
            result["status"] = exc.details["result_status"]
        if "expected_revision" in exc.details:
            result["revision_before"] = exc.details["expected_revision"]
        if "actual_revision" in exc.details:
            result["revision_after"] = exc.details["actual_revision"]
        emit(result, args.format)
        return exc.exit_code
    emit(result, args.format)
    return exit_code



# Optional action guard adapter.  Standalone/core use imports no ontology runtime.
def _ontology_checkpoint(*, targets=True):
    import sys as _sys
    _module = _sys.modules.get("ontology_guards")
    if _module is not None:
        _module.checkpoint(targets=targets)


def _ontology_guard_adapter(function, family, root_argument, target_paths):
    import functools as _functools
    import inspect as _inspect
    @_functools.wraps(function)
    def guarded(*args, **kwargs):
        import importlib.util as _util
        import sys as _sys
        from pathlib import Path as _Path
        arguments = dict(_inspect.signature(function).bind(*args, **kwargs).arguments)
        if root_argument == "@depot":
            selected_root = installed_locations()[0]
        else:
            selected_root = arguments[root_argument]
            if not isinstance(selected_root, (_Path, str)):
                selected_root = getattr(selected_root, "project_root", getattr(selected_root, "root", selected_root))
        selected_root = _Path(selected_root).absolute()
        config_path = selected_root / "ontology-advanced.yaml"
        if not config_path.exists() and not config_path.is_symlink():
            return function(*args, **kwargs)
        if family == "template" and arguments.get("command") == "check":
            return function(*args, **kwargs)
        import json as _json
        import hashlib as _hashlib
        def unique_pairs(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate guard configuration key")
                value[key] = item
            return value
        try:
            if config_path.is_symlink():
                raise ValueError("symbolic guard configuration")
            config = _json.loads(config_path.read_text(), object_pairs_hook=unique_pairs)
            selected = config.get("profiles", {}).get("guards", {"enabled": False})
            if config.get("schema_version") != 1 or not isinstance(selected, dict) or type(selected.get("enabled")) is not bool:
                raise ValueError("unsupported guard configuration")
        except (OSError, ValueError, AttributeError) as exc:
            raise _ontology_adapter_error("guard_schema", "Guard configuration is unreadable or unsupported.", {}) from exc
        if not selected["enabled"]:
            if set(selected) != {"enabled"}:
                raise _ontology_adapter_error("guard_schema", "Disabled guard configuration has unsupported fields.", {})
            return function(*args, **kwargs)
        script = selected_root / ".agents/skills/ontology/scripts/ontology_guards.py"
        if not script.is_file() or any(parent.is_symlink() for parent in (script, *script.parents)):
            raise _ontology_adapter_error("guard_unavailable", "Enabled guards require their current project-local installed adapter.", {})
        current_sha256 = _hashlib.sha256(script.read_bytes()).hexdigest()
        module = _sys.modules.get("ontology_guards")
        if module is not None and (_Path(module.__file__).resolve() != script.resolve()
                or getattr(module, "ENGINE_SOURCE_SHA256", None) != current_sha256):
            raise _ontology_adapter_error("guard_stale", "Loaded guard code differs from this selected project's current installed bytes; use a fresh owning-helper process after reviewed repair.", {})
        if module is None:
            spec = _util.spec_from_file_location("ontology_guards", script)
            module = _util.module_from_spec(spec)
            _sys.modules["ontology_guards"] = module
            _sys.path.insert(0, str(script.parent))
            spec.loader.exec_module(module)
        targets = list(target_paths)
        if family == "setup":
            destination = _Path(arguments["destination"]).absolute()
            try:
                relative = destination.relative_to(selected_root).as_posix()
            except ValueError:
                raise _ontology_adapter_error("guard_scope", "Setup target escapes the selected depot.", {})
            targets.extend([relative + "/control_records/project-setup.json", relative + "/AGENTS.md", relative + "/ROLE.md"])
        try:
            return module.dispatch(lambda: function(*args, **kwargs), family, function.__name__, selected_root, arguments, targets)
        except module.GuardError as exc:
            raise _ontology_adapter_error(exc.code, str(exc), exc.details) from exc
    return guarded


def _ontology_adapter_error(code, message, details):
    return TaskError(EXIT_INVALID, code, message, details=details)

ONTOLOGY_GUARDED_ACTIONS = ['command_new', 'response_transaction', 'command_rebuild', 'command_reconcile', 'reconcile_transaction', 'reconcile_redaction_intent', 'reconcile_lock', 'reconcile_response_redaction', 'command_intake']
command_new = _ontology_guard_adapter(command_new, 'task', 'project_root', ['Tasks'])
response_transaction = _ontology_guard_adapter(response_transaction, 'task', 'project_root', ['Tasks'])
command_rebuild = _ontology_guard_adapter(command_rebuild, 'task', 'project_root', ['Tasks'])
command_reconcile = _ontology_guard_adapter(command_reconcile, 'task', 'project_root', ['Tasks'])
reconcile_transaction = _ontology_guard_adapter(reconcile_transaction, 'task', 'project_root', ['Tasks'])
reconcile_redaction_intent = _ontology_guard_adapter(reconcile_redaction_intent, 'task', 'project_root', ['Tasks'])
reconcile_lock = _ontology_guard_adapter(reconcile_lock, 'task', 'project_root', ['Tasks'])
reconcile_response_redaction = _ontology_guard_adapter(reconcile_response_redaction, 'task', 'project_root', ['Tasks'])

command_intake = _ontology_guard_adapter(command_intake, 'task', 'project_root', ['Tasks'])

if __name__ == "__main__":
    raise SystemExit(main())
