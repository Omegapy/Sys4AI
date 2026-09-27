#!/usr/bin/env python3
"""Public memory CLI: explicit roots and lazy operation dispatch."""
from __future__ import annotations

import argparse
import json
import sys
sys.dont_write_bytecode = True

from memory_paths import MemoryError, require, project_root, safe_read_bytes
from memory_core import decode_json_yaml, health, load_config, load_record, load_records, parse_record, validate_record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    health_command = commands.add_parser("health")
    health_command.add_argument("--scope", choices=("canonical", "selected"), default="selected")
    health_command.add_argument("--level", choices=("static", "operational"), default="static")
    health_command.add_argument("--require", action="append", default=[])
    health_command.add_argument("--format", choices=("json", "text"), default="json")
    commands.add_parser("capture-status")
    setting = commands.add_parser("set-capture")
    setting.add_argument("setting", choices=("on", "off"))
    setting.add_argument("--expected-config-sha256", required=True)
    capture = commands.add_parser("capture")
    capture.add_argument("payload")
    capture.add_argument("--trigger", required=True)
    capture.add_argument("--grant-file", required=True)
    capture.add_argument("--actor", required=True)
    validate = commands.add_parser("validate"); validate.add_argument("path", nargs="?")
    read = commands.add_parser("read"); read.add_argument("path")
    search = commands.add_parser("search"); search.add_argument("query")
    search.add_argument("--historical", action="store_true"); search.add_argument("--limit", type=int)
    search.add_argument("--mode", choices=("auto", "lexical", "hybrid"), default="auto")
    search.add_argument("--packet-file"); search.add_argument("--packet-sha256")
    proposal = commands.add_parser("propose")
    proposal.add_argument("input", help="Project-relative Markdown draft record with JSON-compatible YAML frontmatter (not a JSON wrapper).")
    proposal.add_argument("--output"); proposal.add_argument("--grant-file", "--grant", dest="grant_file")
    proposal.add_argument("--actor")
    for operation in ("publish", "supersede", "retract", "redact"):
        command = commands.add_parser(operation); command.add_argument("payload")
        command.add_argument("--grant-file", "--grant", dest="grant_file", required=True)
        command.add_argument("--actor", required=True)
    recover = commands.add_parser("recover"); recover.add_argument("journal")
    recover.add_argument("--grant-file", "--grant", dest="grant_file", required=True); recover.add_argument("--actor", required=True)
    commands.add_parser("reindex-payload")
    rebuild = commands.add_parser("reindex")
    rebuild.add_argument("--grant-file", "--grant", dest="grant_file", required=True); rebuild.add_argument("--actor", required=True)
    rebuild.add_argument("--expected-payload-sha256", required=True)
    backend_recover = commands.add_parser("backend-recover")
    backend_recover.add_argument("--operation-id", required=True)
    backend_recover.add_argument("--grant-file", "--grant", dest="grant_file", required=True)
    backend_recover.add_argument("--actor", required=True)
    args = parser.parse_args(argv)
    try:
        root = project_root(args.project_root)
        if args.command == "health":
            result = health(root, scope=args.scope, level=args.level, required=args.require)
        elif args.command == "capture-status":
            from memory_capture import capture_status
            result = capture_status(root)
        elif args.command == "set-capture":
            from memory_capture import set_capture
            result = set_capture(root, args.setting == "on", args.expected_config_sha256)
        elif args.command == "capture":
            from memory_capture import capture
            payload = decode_json_yaml(safe_read_bytes(root, args.payload, max_bytes=16_000_000))
            result = capture(root, payload, args.grant_file, args.actor, trigger=args.trigger)
        elif args.command == "read":
            result = load_record(root, args.path)
        elif args.command == "validate":
            config = load_config(root)
            records = [load_record(root, args.path, config)] if args.path else load_records(root, config, historical=True)
            diagnostics = [d for record in records for d in record["diagnostics"]]
            result = {"valid": not any(d.get("severity") != "info" for d in diagnostics),
                      "records": len(records), "diagnostics": diagnostics,
                      "verified_current_records": sum(record["evidence"]["verified_current"] for record in records),
                      "read_only": True}
        elif args.command == "search":
            require(bool(args.packet_file) == bool(args.packet_sha256), "packet_reference", "Frozen packet lookup requires both exact path and reviewed SHA256.")
            from memory_search import search as find
            packet = {"path": args.packet_file, "sha256": args.packet_sha256} if args.packet_file else None
            result = find(root, args.query, historical=args.historical, packet=packet, limit=args.limit, mode=args.mode)
        elif args.command == "propose":
            from memory_publish import propose
            record = parse_record(safe_read_bytes(root, args.input, max_bytes=250000))
            result = propose(root, record, output=args.output, grant_file=args.grant_file, actor=args.actor)
        elif args.command in {"publish", "supersede", "retract", "redact"}:
            from memory_publish import publish
            payload = decode_json_yaml(safe_read_bytes(root, args.payload, max_bytes=16_000_000))
            require(payload.get("operation") == args.command, "operation_mismatch", "CLI operation differs from the reviewed payload.")
            result = publish(root, payload, args.grant_file, args.actor)
        elif args.command == "recover":
            from memory_recovery import recover as repair
            result = repair(root, args.journal, args.grant_file, args.actor)
        elif args.command == "reindex-payload":
            from memory_maintenance import reindex_payload
            result = reindex_payload(root)
        elif args.command == "reindex":
            from memory_maintenance import reindex
            result = reindex(root, grant_file=args.grant_file, actor=args.actor, expected_payload_sha256=args.expected_payload_sha256)
        else:
            from memory_maintenance import recover_reindex
            result = recover_reindex(root, args.operation_id, grant_file=args.grant_file, actor=args.actor)
        if args.command == "health":
            from memory_core import health_exit
            if args.format == "text":
                print(f"Memory health: {result['aggregate']} ({args.scope}/{args.level})")
                for name, component in result.get("components", {}).items():
                    print(f"  {name}: {component['status']}")
                for diagnostic in result.get("diagnostics", []):
                    print("  " + json.dumps(diagnostic, sort_keys=True))
                if result.get("error"):
                    print("  " + json.dumps(result["error"], sort_keys=True))
            else:
                print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
            return health_exit(result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 1 if (isinstance(result, dict) and (result.get("valid") is False or result.get("ready") is False or result.get("status") == "invalid")) else 0
    except MemoryError as exc:
        print(json.dumps({"ok": False, "error": exc.as_dict()}, sort_keys=True, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
