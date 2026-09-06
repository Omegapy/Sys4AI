from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest

from sys4ai_memory.cli import build_parser, main
from sys4ai_memory.contracts import ErrorCategory, OperationName
from sys4ai_memory.interfaces import ControlAction
from tests.interfaces.helpers import TRACE_ID, RecordingDispatcher

BASE = (
    "--project-id",
    "project-alpha",
    "--dataset-id",
    "dataset-alpha",
    "--principal-id",
    "agent_test",
    "--agent-type",
    "test-agent",
    "--run-id",
    "run_test",
)

CASES = (
    (("init-memory", "--idempotency-key", "direct-init-key"), ControlAction.INITIALIZE_DIRECT),
    (("init", "preview"), ControlAction.INITIALIZE_PREVIEW),
    (
        (
            "init",
            "apply",
            "--impact-digest",
            "a" * 64,
            "--idempotency-key",
            "init-key",
        ),
        ControlAction.INITIALIZE_APPLY,
    ),
    (("sources", "list"), OperationName.SOURCES_LIST),
    (("sources", "explain", "docs/requirements.md"), OperationName.SOURCES_EXPLAIN),
    (("health",), OperationName.HEALTH),
    (("sync", "--dry-run", "--idempotency-key", "sync-key"), OperationName.SYNC),
    (("recall", "source authority"), OperationName.RECALL),
    (("get", "mem_ALPHA"), OperationName.GET),
    (("graph", "mem_ALPHA"), OperationName.GRAPH),
    (
        (
            "propose",
            "--proposal-json",
            '{"record_type":"Observation"}',
            "--idempotency-key",
            "propose-key",
        ),
        OperationName.PROPOSE,
    ),
    (
        (
            "approve",
            "mwp_ALPHA",
            "--decision",
            "approve",
            "--reason",
            "reviewed",
            "--idempotency-key",
            "approve-key",
        ),
        OperationName.APPROVE,
    ),
    (
        (
            "supersede",
            "mem_ALPHA",
            "mem_BETA",
            "--reason",
            "replacement",
            "--idempotency-key",
            "supersede-key",
        ),
        OperationName.SUPERSEDE,
    ),
    (
        (
            "improve",
            "--feedback-json",
            '{"relevant":true}',
            "--idempotency-key",
            "improve-key",
        ),
        OperationName.IMPROVE,
    ),
    (
        (
            "forget",
            "--record-id",
            "mem_ALPHA",
            "--action",
            "expire",
            "--reason",
            "retention",
            "--idempotency-key",
            "forget-key",
        ),
        OperationName.FORGET,
    ),
    (("rebuild", "--idempotency-key", "rebuild-key"), OperationName.REBUILD),
    (
        ("export", "exports/memory.zip", "--idempotency-key", "export-key"),
        OperationName.EXPORT,
    ),
    (
        ("import", "imports/memory.zip", "--idempotency-key", "import-key"),
        OperationName.IMPORT,
    ),
    (("explain", "mem_ALPHA"), OperationName.EXPLAIN),
    (("operation", "status", "op_sync"), ControlAction.OPERATION_STATUS),
)


@pytest.mark.parametrize(("arguments", "action"), CASES)
def test_cli_covers_every_public_and_control_action(
    arguments: tuple[str, ...], action: OperationName | ControlAction
) -> None:
    dispatcher = RecordingDispatcher()
    output = StringIO()

    exit_code = main((*BASE, *arguments), dispatcher=dispatcher, stdout=output)

    assert exit_code == 0
    assert dispatcher.requests[0].operation is action
    assert json.loads(output.getvalue())["operation"] == action.value


def test_cli_case_table_includes_all_sixteen_public_operations() -> None:
    public_actions = {action for _, action in CASES if isinstance(action, OperationName)}
    control_actions = {action for _, action in CASES if isinstance(action, ControlAction)}
    assert public_actions == set(OperationName)
    assert control_actions == set(ControlAction)


def test_recall_synthesis_requires_the_explicit_cli_flag() -> None:
    dispatcher = RecordingDispatcher()
    output = StringIO()

    assert (
        main(
            (*BASE, "recall", "source authority", "--synthesize"),
            dispatcher=dispatcher,
            stdout=output,
        )
        == 0
    )
    assert dispatcher.requests[0].payload["synthesize"] is True


def test_cli_emits_safe_structured_validation_errors_without_dispatch() -> None:
    dispatcher = RecordingDispatcher()
    output = StringIO()
    secret = "password=do-not-return"  # noqa: S105 - synthetic rejection fixture

    exit_code = main(
        (
            *BASE,
            "propose",
            "--proposal-json",
            json.dumps({"content": secret}),
            "--idempotency-key",
            "proposal-key",
            "--trace-id",
            TRACE_ID,
        ),
        dispatcher=dispatcher,
        stdout=output,
    )

    payload = json.loads(output.getvalue())
    assert exit_code == 2
    assert payload["error"]["category"] == ErrorCategory.SENSITIVITY_VIOLATION.value
    assert payload["error"]["trace_id"] == TRACE_ID
    assert "do-not-return" not in output.getvalue()
    assert not dispatcher.requests


def test_rebuild_activation_requires_and_carries_preview_operation_id() -> None:
    dispatcher = RecordingDispatcher()
    denied_output = StringIO()
    accepted_output = StringIO()
    digest = "a" * 64

    denied = main(
        (
            *BASE,
            "rebuild",
            "--activate",
            "--impact-digest",
            digest,
            "--idempotency-key",
            "rebuild-execute-missing-operation",
        ),
        dispatcher=dispatcher,
        stdout=denied_output,
    )
    accepted = main(
        (
            *BASE,
            "rebuild",
            "--activate",
            "--operation-id",
            "op_rebuild_preview",
            "--impact-digest",
            digest,
            "--idempotency-key",
            "rebuild-execute-with-operation",
        ),
        dispatcher=dispatcher,
        stdout=accepted_output,
    )

    assert denied == 2
    assert json.loads(denied_output.getvalue())["error"]["category"] == (
        ErrorCategory.SCHEMA_INVALID.value
    )
    assert accepted == 0
    assert dispatcher.requests[0].payload["operation_id"] == "op_rebuild_preview"


def test_cli_without_local_configuration_reports_not_initialized(tmp_path: Path) -> None:
    output = StringIO()

    exit_code = main(
        (*BASE, "--project-root", str(tmp_path), "health", "--trace-id", TRACE_ID),
        stdout=output,
    )

    payload = json.loads(output.getvalue())
    assert exit_code == 2
    assert payload["error"]["category"] == ErrorCategory.MEMORY_NOT_INITIALIZED.value
    assert payload["error"]["trace_id"] == TRACE_ID


def test_cli_unknown_dispatcher_error_is_redacted() -> None:
    output = StringIO()
    dispatcher = RecordingDispatcher(failure=RuntimeError("api_key=do-not-return"))

    exit_code = main(
        (*BASE, "health", "--trace-id", TRACE_ID),
        dispatcher=dispatcher,
        stdout=output,
    )

    assert exit_code == 2
    assert "do-not-return" not in output.getvalue()


def test_cli_long_operation_and_status_are_machine_readable() -> None:
    dispatcher = RecordingDispatcher()
    start_output = StringIO()
    status_output = StringIO()

    assert (
        main(
            (*BASE, "sync", "--dry-run", "--idempotency-key", "retry-key"),
            dispatcher=dispatcher,
            stdout=start_output,
        )
        == 0
    )
    assert (
        main(
            (*BASE, "operation", "status", "op_sync"),
            dispatcher=dispatcher,
            stdout=status_output,
        )
        == 0
    )

    start = json.loads(start_output.getvalue())
    status = json.loads(status_output.getvalue())
    assert start["operation_status"]["retry_safe"] is True
    assert start["operation_status"]["status_action"] == "memory.operations.status"
    assert status["result"]["state"] == "running"
    assert status["result"]["retry_safe"] is True


def test_help_is_local_and_lists_all_top_level_commands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        build_parser().parse_args(["--help"])

    help_text = capsys.readouterr().out
    assert stopped.value.code == 0
    for command in {
        "init",
        "sources",
        "health",
        "sync",
        "recall",
        "get",
        "graph",
        "propose",
        "approve",
        "supersede",
        "improve",
        "forget",
        "rebuild",
        "export",
        "import",
        "explain",
        "operation",
    }:
        assert command in help_text
