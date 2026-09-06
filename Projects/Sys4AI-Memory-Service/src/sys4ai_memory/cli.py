"""Structured command-line adapter for the Sys4AI Memory Service."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import IO, NoReturn

from pydantic import JsonValue, ValidationError

from sys4ai_memory.contracts import (
    ErrorCategory,
    MemoryScope,
    OperationName,
    RetrievalMode,
    ScopeReference,
)
from sys4ai_memory.interfaces.common import (
    invoke_dispatcher,
    project_authorization,
    safe_trace_id,
)
from sys4ai_memory.interfaces.dispatcher import (
    MemoryServiceDispatcher,
    error_envelope,
)
from sys4ai_memory.interfaces.models import (
    ControlAction,
    DispatchResponse,
    DispatchSuccess,
    InterfaceAction,
    InterfaceIdentity,
    InterfaceKind,
)


class CliParseError(ValueError):
    """Command syntax was invalid; details are intentionally not retained."""


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise CliParseError("invalid command line")


def _json_object(value: str) -> dict[str, JsonValue]:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise argparse.ArgumentTypeError("expected a JSON object") from error
    if not isinstance(parsed, dict) or any(not isinstance(key, str) for key in parsed):
        raise argparse.ArgumentTypeError("expected a JSON object")
    return parsed


def _add_idempotency(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--idempotency-key", required=True)


def _add_request_ids(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--request-id")
    parser.add_argument("--trace-id")


def build_parser() -> argparse.ArgumentParser:
    parser = SafeArgumentParser(
        prog="sys4ai-memory",
        description="Dispatch Sys4AI memory operations as structured JSON.",
    )
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--principal-id", required=True)
    parser.add_argument("--agent-type", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--configuration-path", default="config/memory.toml")
    parser.add_argument(
        "--scope-level",
        choices=[item.value for item in MemoryScope],
        default="project",
    )
    parser.add_argument("--scope-id")
    parser.add_argument("--query-project-id", action="append", dest="query_project_ids")
    parser.add_argument("--explicit-cross-project", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=SafeArgumentParser)

    init_direct = commands.add_parser(
        "init-memory", help="Initialize project memory directly after internal validation."
    )
    init_direct.add_argument("--configuration-path", default=argparse.SUPPRESS)
    _add_idempotency(init_direct)
    _add_request_ids(init_direct)
    init_direct.set_defaults(_action=ControlAction.INITIALIZE_DIRECT)

    init_parser = commands.add_parser("init", help="Preview or apply memory initialization.")
    init_actions = init_parser.add_subparsers(
        dest="init_action", required=True, parser_class=SafeArgumentParser
    )
    init_preview = init_actions.add_parser("preview", help="Preview initialization without writes.")
    init_preview.add_argument("--configuration-path", default=argparse.SUPPRESS)
    _add_request_ids(init_preview)
    init_preview.set_defaults(_action=ControlAction.INITIALIZE_PREVIEW)
    init_apply = init_actions.add_parser("apply", help="Apply an exact reviewed preview.")
    init_apply.add_argument("--configuration-path", default=argparse.SUPPRESS)
    init_apply.add_argument("--impact-digest", required=True)
    _add_idempotency(init_apply)
    _add_request_ids(init_apply)
    init_apply.set_defaults(_action=ControlAction.INITIALIZE_APPLY)

    sources_parser = commands.add_parser("sources", help="Inspect the registered source set.")
    source_actions = sources_parser.add_subparsers(
        dest="sources_action", required=True, parser_class=SafeArgumentParser
    )
    sources_list = source_actions.add_parser("list", help="List visible registered sources.")
    sources_list.add_argument("--include-excluded", action="store_true")
    _add_request_ids(sources_list)
    sources_list.set_defaults(_action=OperationName.SOURCES_LIST)
    sources_explain = source_actions.add_parser("explain", help="Explain source inclusion policy.")
    sources_explain.add_argument("target")
    _add_request_ids(sources_explain)
    sources_explain.set_defaults(_action=OperationName.SOURCES_EXPLAIN)

    health = commands.add_parser("health", help="Inspect service and dependency health.")
    health.add_argument("--detailed", action="store_true")
    _add_request_ids(health)
    health.set_defaults(_action=OperationName.HEALTH)

    sync = commands.add_parser("sync", help="Synchronize registered sources.")
    sync.add_argument("--source-id", action="append", dest="source_ids")
    sync.add_argument("--full", action="store_true")
    sync.add_argument("--dry-run", action="store_true")
    _add_idempotency(sync)
    _add_request_ids(sync)
    sync.set_defaults(_action=OperationName.SYNC)

    recall = commands.add_parser("recall", help="Retrieve a source-backed evidence bundle.")
    recall.add_argument("query")
    recall.add_argument("--mode", choices=[item.value for item in RetrievalMode], default="hybrid")
    recall.add_argument("--limit", type=int, default=10)
    recall.add_argument("--namespace", action="append", dest="namespaces")
    recall.add_argument("--include-history", action="store_true")
    recall.add_argument(
        "--synthesize",
        action="store_true",
        help="Explicitly request cited answer synthesis from an injected model port.",
    )
    _add_request_ids(recall)
    recall.set_defaults(_action=OperationName.RECALL)

    get = commands.add_parser("get", help="Retrieve one record by stable ID.")
    get.add_argument("record_id")
    get.add_argument("--include-history", action="store_true")
    _add_request_ids(get)
    get.set_defaults(_action=OperationName.GET)

    graph = commands.add_parser("graph", help="Inspect authorized typed relations.")
    graph.add_argument("record_id")
    graph.add_argument("--relation-type", action="append", dest="relation_types")
    _add_request_ids(graph)
    graph.set_defaults(_action=OperationName.GRAPH)

    propose = commands.add_parser("propose", help="Stage a typed memory write proposal.")
    propose.add_argument("--proposal-json", required=True, type=_json_object)
    _add_idempotency(propose)
    _add_request_ids(propose)
    propose.set_defaults(_action=OperationName.PROPOSE)

    approve = commands.add_parser("approve", help="Approve or reject a staged proposal.")
    approve.add_argument("proposal_id")
    approve.add_argument("--decision", choices=["approve", "reject"], required=True)
    approve.add_argument("--reason", required=True)
    _add_idempotency(approve)
    _add_request_ids(approve)
    approve.set_defaults(_action=OperationName.APPROVE)

    supersede = commands.add_parser("supersede", help="Link a replacement record.")
    supersede.add_argument("record_id")
    supersede.add_argument("replacement_record_id")
    supersede.add_argument("--reason", required=True)
    _add_idempotency(supersede)
    _add_request_ids(supersede)
    supersede.set_defaults(_action=OperationName.SUPERSEDE)

    improve = commands.add_parser("improve", help="Apply derived-memory feedback.")
    improve.add_argument("--feedback-json", required=True, type=_json_object)
    improve.add_argument("--record-id")
    _add_idempotency(improve)
    _add_request_ids(improve)
    improve.set_defaults(_action=OperationName.IMPROVE)

    forget = commands.add_parser("forget", help="Preview or execute a lifecycle action.")
    forget.add_argument("--record-id", action="append", dest="record_ids", required=True)
    forget.add_argument(
        "--action",
        choices=["expire", "withdraw", "delete-derived", "delete-source", "privacy-erase"],
        required=True,
    )
    forget.add_argument("--reason", required=True)
    forget.add_argument("--execute", action="store_true")
    forget.add_argument("--operation-id")
    forget.add_argument("--impact-digest")
    _add_idempotency(forget)
    _add_request_ids(forget)
    forget.set_defaults(_action=OperationName.FORGET)

    rebuild = commands.add_parser("rebuild", help="Preview or activate a derived-memory rebuild.")
    rebuild.add_argument("--activate", action="store_true")
    rebuild.add_argument("--generation-label")
    rebuild.add_argument("--operation-id")
    rebuild.add_argument("--impact-digest")
    _add_idempotency(rebuild)
    _add_request_ids(rebuild)
    rebuild.set_defaults(_action=OperationName.REBUILD)

    export = commands.add_parser("export", help="Create a portable memory package.")
    export.add_argument("output_path")
    export.add_argument("--format", choices=["sys4ai", "cogx"], default="sys4ai")
    export.add_argument("--include-sensitive", action="store_true")
    _add_idempotency(export)
    _add_request_ids(export)
    export.set_defaults(_action=OperationName.EXPORT)

    import_parser = commands.add_parser("import", help="Validate or activate a memory package.")
    import_parser.add_argument("package_path")
    import_parser.add_argument("--activate", action="store_true")
    import_parser.add_argument("--expected-sha256")
    import_parser.add_argument("--impact-digest")
    _add_idempotency(import_parser)
    _add_request_ids(import_parser)
    import_parser.set_defaults(_action=OperationName.IMPORT)

    explain = commands.add_parser("explain", help="Explain record provenance and ranking.")
    explain.add_argument("record_id")
    _add_request_ids(explain)
    explain.set_defaults(_action=OperationName.EXPLAIN)

    operation = commands.add_parser("operation", help="Inspect long-running operation state.")
    operation_actions = operation.add_subparsers(
        dest="operation_action", required=True, parser_class=SafeArgumentParser
    )
    operation_status = operation_actions.add_parser("status", help="Get retry-safe status.")
    operation_status.add_argument("operation_id")
    _add_request_ids(operation_status)
    operation_status.set_defaults(_action=ControlAction.OPERATION_STATUS)
    return parser


def _payload(args: argparse.Namespace) -> dict[str, JsonValue]:
    action: InterfaceAction = args._action
    if action in {ControlAction.INITIALIZE_PREVIEW, ControlAction.INITIALIZE_DIRECT}:
        return {"configuration_path": args.configuration_path}
    if action is ControlAction.INITIALIZE_APPLY:
        return {
            "configuration_path": args.configuration_path,
            "impact_digest": args.impact_digest,
        }
    if action is ControlAction.OPERATION_STATUS:
        return {"operation_id": args.operation_id}
    if action is OperationName.HEALTH:
        return {"detailed": args.detailed}
    if action is OperationName.SOURCES_LIST:
        return {"include_excluded": args.include_excluded}
    if action is OperationName.SOURCES_EXPLAIN:
        return {"target": args.target}
    if action is OperationName.SYNC:
        return {
            "source_ids": args.source_ids or [],
            "full": args.full,
            "dry_run": args.dry_run,
        }
    if action is OperationName.RECALL:
        return {
            "query": args.query,
            "mode": args.mode,
            "limit": args.limit,
            "namespaces": args.namespaces or [],
            "current_only": not args.include_history,
            "synthesize": args.synthesize,
        }
    if action is OperationName.GET:
        return {"record_id": args.record_id, "include_history": args.include_history}
    if action is OperationName.GRAPH:
        return {
            "record_id": args.record_id,
            "max_depth": 1,
            "relation_types": args.relation_types or [],
        }
    if action is OperationName.PROPOSE:
        return {"proposal": args.proposal_json}
    if action is OperationName.APPROVE:
        return {
            "proposal_id": args.proposal_id,
            "decision": args.decision,
            "reason": args.reason,
        }
    if action is OperationName.SUPERSEDE:
        return {
            "record_id": args.record_id,
            "replacement_record_id": args.replacement_record_id,
            "reason": args.reason,
        }
    if action is OperationName.IMPROVE:
        return {"record_id": args.record_id, "feedback": args.feedback_json}
    if action is OperationName.FORGET:
        return {
            "record_ids": args.record_ids,
            "action": args.action,
            "reason": args.reason,
            "execute": args.execute,
            "operation_id": args.operation_id,
            "impact_digest": args.impact_digest,
        }
    if action is OperationName.REBUILD:
        return {
            "preview_only": not args.activate,
            "generation_label": args.generation_label,
            "operation_id": args.operation_id,
            "impact_digest": args.impact_digest,
        }
    if action is OperationName.EXPORT:
        return {
            "output_path": args.output_path,
            "format": args.format,
            "include_sensitive": args.include_sensitive,
        }
    if action is OperationName.IMPORT:
        return {
            "package_path": args.package_path,
            "activate": args.activate,
            "expected_sha256": args.expected_sha256,
            "impact_digest": args.impact_digest,
        }
    if action is OperationName.EXPLAIN:
        return {"record_id": args.record_id}
    raise CliParseError("unsupported command")


def _trace_from_argv(argv: Sequence[str]) -> str:
    for index, value in enumerate(argv[:-1]):
        if value == "--trace-id":
            return safe_trace_id(argv[index + 1])
    return safe_trace_id(None)


def _emit(response: DispatchResponse, output: IO[str]) -> None:
    output.write(
        json.dumps(
            response.model_dump(mode="json", exclude_none=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    dispatcher: MemoryServiceDispatcher | None = None,
    stdout: IO[str] | None = None,
) -> int:
    """Parse one command, dispatch once, and emit exactly one JSON envelope."""

    arguments = tuple(sys.argv[1:] if argv is None else argv)
    output = stdout or sys.stdout
    try:
        args = build_parser().parse_args(arguments)
    except CliParseError:
        response: DispatchResponse = error_envelope(
            _trace_from_argv(arguments), ErrorCategory.SCHEMA_INVALID
        )
        _emit(response, output)
        return 2
    try:
        identity = InterfaceIdentity(
            principal_id=args.principal_id,
            agent_type=args.agent_type,
            run_id=args.run_id,
        )
        scope = ScopeReference(
            level=MemoryScope(args.scope_level),
            scope_id=args.scope_id or args.project_id,
        )
        authorization = project_authorization(
            identity,
            project_id=args.project_id,
            dataset_id=args.dataset_id,
            scope=scope,
            query_project_ids=tuple(args.query_project_ids or (args.project_id,)),
            explicit_cross_project=args.explicit_cross_project,
        )
        payload = _payload(args)
    except (CliParseError, ValidationError, ValueError, TypeError):
        response = error_envelope(
            safe_trace_id(getattr(args, "trace_id", None)),
            ErrorCategory.SCHEMA_INVALID,
        )
        _emit(response, output)
        return 2
    if dispatcher is None:
        from sys4ai_memory.runtime import LocalMemoryRuntime

        dispatcher = LocalMemoryRuntime(
            project_root=Path(args.project_root).absolute(),
            configuration_path=args.configuration_path,
        )
    response = invoke_dispatcher(
        dispatcher,
        operation=args._action,
        authorization=authorization,
        interface=InterfaceKind.CLI,
        client_id="sys4ai-cli",
        purpose=f"CLI {args._action.value}",
        payload=payload,
        idempotency_key=getattr(args, "idempotency_key", None),
        request_id=getattr(args, "request_id", None),
        trace_id=getattr(args, "trace_id", None),
    )
    _emit(response, output)
    return 0 if isinstance(response, DispatchSuccess) else 2


if __name__ == "__main__":
    raise SystemExit(main())
