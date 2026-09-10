#!/usr/bin/env python3
"""Project-local ontology: read, validate, explicitly build, freeze or publish."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

from ontology_core import OntologyError, load_project, read_json, safe_path, sha256, require
from ontology_retrieval import human, read, search, term


def health(root):
    try:
        p = load_project(root, validate=False)
        from ontology_validate import validate_project
        validation = validate_project(p)
        projections = {}
        for operation in ("compile", "build-wiki", "link-memory"):
            path = f".sys4ai/ontology/manifests/{operation}.json"
            manifest = safe_path(p.root, path, must_exist=False)
            if not manifest.exists():
                projections[operation] = {"status": "missing", "explicit_operation": operation}
                continue
            try:
                value = read_json(manifest)
                require(isinstance(value, dict) and isinstance(value.get("outputs"), dict) and isinstance(value.get("context"), dict), "invalid_manifest", "Generated ownership manifest is malformed.", path=path)
                state = "current" if value["context"].get("snapshot_sha256") == p.context()["snapshot_sha256"] else "stale"
                for output, digest in value["outputs"].items():
                    require(isinstance(output, str) and output.startswith((".sys4ai/ontology/", "ONTOLOGY/WIKI/")) and isinstance(digest, str), "invalid_manifest", "Generated manifest contains an unsafe output reference.")
                    target = safe_path(p.root, output, must_exist=False)
                    if not target.exists() or sha256(target) != digest:
                        state = "stale"
                projections[operation] = {"status": state, "manifest": path, "explicit_operation": operation}
            except OntologyError as error:
                projections[operation] = {"status": "invalid", "error": error.as_dict()}
        return {"operation": "health", "status": "ready" if validation["valid"] and all(s["status"] == "current" for s in p.sources) else "degraded",
                "project_id": p.project_id, "configuration": "configured", "modules": "integrity_verified",
                "validation": validation, "sources": p.sources, "generated": projections,
                "project_extension": "empty" if not any(r["module"] == "project" for r in p.records) else "present",
                "context": p.context(), "mutated": False}
    except OntologyError as error:
        return {"operation": "health", "status": "invalid", "mutated": False, "error": error.as_dict()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--packet-file")
    parser.add_argument("--packet-sha256")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("health")
    commands.add_parser("validate")
    for operation in ("term", "search", "read", "capability", "knowledge", "neighbors", "path"):
        command = commands.add_parser(operation)
        command.add_argument("query")
        command.add_argument("--limit", type=int)
        command.add_argument("--max-bytes", type=int)
        if operation in {"neighbors", "path", "knowledge"}:
            command.add_argument("--hops", type=int)
            command.add_argument("--direction", choices=("incoming", "outgoing", "both"), default="outgoing" if operation == "path" else "both")
            command.add_argument("--predicate", action="append", default=[])
        if operation == "path":
            command.add_argument("target")
        if operation == "knowledge":
            command.add_argument("--intent", choices=("definition", "relationship", "capability", "current", "history", "mixed", "inference", "proposals"), default="mixed")
            command.add_argument("--advanced", action="store_true")
            command.add_argument("--memory-packet-file")
            command.add_argument("--memory-packet-sha256")
    commands.add_parser("compile")
    commands.add_parser("build-wiki")
    link = commands.add_parser("link-memory")
    link.add_argument("--record", action="append", default=[])
    link.add_argument("--concept", action="append", default=[])
    freeze = commands.add_parser("freeze-packet")
    freeze.add_argument("payload", help="JSON packet selection and exact current manager/execution inputs.")
    freeze.add_argument("--output", required=True)
    for operation in ("preview", "publish"):
        command = commands.add_parser(operation)
        command.add_argument("proposal")
        if operation == "publish":
            command.add_argument("--grant-file", required=True)
            command.add_argument("--expected-preview-sha256", required=True)
    recover = commands.add_parser("recover")
    recover.add_argument("operation_id")
    recover.add_argument("--grant-file", required=True)
    from ontology_advanced_cli import register, COMMANDS as ADVANCED_COMMANDS, READ_COMMANDS as ADVANCED_READS
    register(commands)
    args = parser.parse_args(argv)
    try:
        root = Path(args.project_root).absolute()
        require(root.is_dir() and root.resolve() == root and not root.is_symlink(), "invalid_root", "Select an explicit resolved project root.")
        require(bool(args.packet_file) == bool(args.packet_sha256), "packet_reference", "Frozen queries require both packet path and SHA256.")
        frozen = bool(args.packet_file)
        if frozen:
            require(args.command in {"term", "search", "read", "neighbors", "path", "capability", "knowledge"}, "frozen_operation", "Frozen packets support only selected query operations.")
            from ontology_packet import frozen_project
            p = frozen_project(root, {"path": args.packet_file, "sha256": args.packet_sha256})
        elif args.command in {"term", "search", "read", "neighbors", "path", "capability", "knowledge", "compile", "build-wiki", "link-memory"}:
            p = load_project(root)
        if args.command in ADVANCED_COMMANDS:
            from ontology_advanced_cli import dispatch
            result = dispatch(root, args)
        elif args.command == "health": result = health(root)
        elif args.command == "validate":
            from check_ontology import run_checks
            result = run_checks(root)
        elif args.command in {"term", "search"}:
            result = {"term": term, "search": search}[args.command](p, args.query, limit=args.limit, max_bytes=args.max_bytes)
        elif args.command == "read": result = read(p, args.query, max_bytes=args.max_bytes)
        elif args.command in {"neighbors", "path"}:
            from ontology_graph import neighbors, path
            kwargs = dict(hops=args.hops, direction=args.direction, predicates=args.predicate, limit=args.limit, max_bytes=args.max_bytes)
            result = neighbors(p, args.query, **kwargs) if args.command == "neighbors" else path(p, args.query, args.target, **kwargs)
        elif args.command == "capability":
            from ontology_knowledge import capability
            result = capability(p, args.query, limit=args.limit, max_bytes=args.max_bytes)
        elif args.command == "knowledge":
            from ontology_knowledge import knowledge
            require(bool(args.memory_packet_file) == bool(args.memory_packet_sha256), "packet_reference", "Frozen memory requires an exact path and SHA256.")
            memory_ref = {"path": args.memory_packet_file, "sha256": args.memory_packet_sha256} if args.memory_packet_file else None
            result = knowledge(p, args.query, intent=args.intent, hops=args.hops, direction=args.direction, predicates=args.predicate,
                               memory_packet=memory_ref, frozen_ontology=frozen, limit=args.limit, max_bytes=args.max_bytes, advanced=args.advanced)
        elif args.command == "compile":
            from ontology_build import compile_project
            result = compile_project(p)
        elif args.command == "build-wiki":
            from ontology_wiki import build_wiki
            result = build_wiki(p)
        elif args.command == "link-memory":
            from ontology_memory import link_memory
            result = link_memory(p, record_paths=args.record, concept_queries=args.concept)
        elif args.command == "freeze-packet":
            from ontology_packet import build_packet, freeze_packet
            payload = read_json(safe_path(root, args.payload))
            require(isinstance(payload, dict) and {"task_path", "execution_id", "generation", "actor"} <= set(payload)
                    <= {"task_path", "execution_id", "generation", "actor", "concept_ids", "query", "allowed_sources", "max_records", "max_bytes", "subtask_id", "revision_reason", "advanced", "graph_selection", "inference_goals", "extension_ids", "semantic_queries"},
                    "invalid_packet_request", "Packet request requires current Task manager inputs and supported selection fields.")
            packet = build_packet(root, **payload)
            result = freeze_packet(root, packet, args.output, actor=payload["actor"])
        elif args.command == "preview":
            from ontology_publication import preview
            result = preview(root, read_json(safe_path(root, args.proposal)))
        elif args.command == "publish":
            from ontology_publication import publish
            result = publish(root, read_json(safe_path(root, args.proposal)), read_json(safe_path(root, args.grant_file)), expected_preview_sha256=args.expected_preview_sha256)
        else:
            from ontology_publication import recover
            result = recover(root, args.operation_id, read_json(safe_path(root, args.grant_file)))
        print(human(result) if args.format == "text" else json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 1 if result.get("valid") is False or result.get("complete") is False or result.get("status") in {"invalid", "partial", "failed", "violation", "rejected"} else 0
    except OntologyError as error:
        read_only = args.command in {"health", "term", "search", "read", "neighbors", "path", "validate", "capability", "knowledge", "preview"} | ADVANCED_READS
        print(json.dumps({"status": "invalid", "error": error.as_dict(), "mutated": False if read_only else None}, sort_keys=True, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
