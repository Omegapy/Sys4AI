"""Explicit advanced CLI operations; core command startup stays standard-library only."""
import json
from pathlib import Path

from ontology_core import (atomic_write, canonical_bytes, exact, read_bytes,
                           read_json, require, safe_path, sha256)

READ_COMMANDS = {"advanced-health", "dataset", "sparql", "shacl", "infer", "semantic-search",
                 "proposal-list", "proposal-show", "generation-show"}
COMMANDS = READ_COMMANDS | {"profile-setup", "profile-configure", "prepare-model", "build-semantic-index",
                           "export-rdf", "import-rdf", "proposal-save", "proposal-validate", "proposal-decide", "proposal-publish",
                           "generation-prepare", "generation-capture", "guard-preview", "guard-apply", "guard-recover", "workbench"}


def register(commands):
    from ontology_health import arguments
    arguments(commands.add_parser("advanced-health"), advanced=True)
    setup = commands.add_parser("profile-setup")
    setup.add_argument("profile", choices=("standards", "semantic"))
    setup.add_argument("--provision", action="store_true", help="Explicitly install the selected hashed package lock.")
    config = commands.add_parser("profile-configure")
    config.add_argument("payload", help="Exact profile change, current config hash and current setup authority.")
    commands.add_parser("prepare-model")
    index = commands.add_parser("build-semantic-index")
    index.add_argument("--document", action="append", default=[])
    sem = commands.add_parser("semantic-search")
    sem.add_argument("query"); sem.add_argument("--limit", type=int); sem.add_argument("--max-bytes", type=int)
    for name in ("dataset", "sparql", "shacl"):
        parser = commands.add_parser(name)
        parser.add_argument("--graph", action="append")
        parser.add_argument("--limits-file")
        if name == "sparql":
            query = parser.add_mutually_exclusive_group(required=True)
            query.add_argument("--query"); query.add_argument("--query-file")
        if name == "shacl":
            parser.add_argument("--shapes", action="append", default=[])
    infer = commands.add_parser("infer")
    infer.add_argument("--goal", nargs=3, action="append", default=[])
    infer.add_argument("--premise-id", action="append")
    infer.add_argument("--expected-snapshot"); infer.add_argument("--limits-file")
    export = commands.add_parser("export-rdf")
    export.add_argument("--serialization", choices=("json-ld", "turtle", "xml"), required=True)
    export.add_argument("--graph"); export.add_argument("--output", required=True)
    export.add_argument("--expected-output-sha256")
    imp = commands.add_parser("import-rdf")
    imp.add_argument("input"); imp.add_argument("--serialization", choices=("json-ld", "turtle", "xml"), required=True)
    imp.add_argument("--manifest"); imp.add_argument("--reason", required=True)
    for name in ("proposal-save", "generation-prepare", "generation-capture", "guard-preview", "guard-apply", "guard-recover"):
        commands.add_parser(name).add_argument("payload")
    commands.add_parser("proposal-list")
    show = commands.add_parser("proposal-show"); show.add_argument("proposal_id"); show.add_argument("--revision", type=int)
    gen = commands.add_parser("generation-show"); gen.add_argument("request_id")
    val = commands.add_parser("proposal-validate"); val.add_argument("proposal_id"); val.add_argument("--revision", type=int, required=True)
    decision = commands.add_parser("proposal-decide")
    decision.add_argument("proposal_id"); decision.add_argument("decision", choices=("accept", "reject", "reopen", "supersede", "discard"))
    decision.add_argument("--revision", type=int, required=True); decision.add_argument("--reason", required=True)
    decision.add_argument("--validation-sha256"); decision.add_argument("--superseded-by")
    publish = commands.add_parser("proposal-publish")
    publish.add_argument("proposal_id"); publish.add_argument("--revision", type=int, required=True)
    publish.add_argument("--grant-file", required=True); publish.add_argument("--expected-review-sha256", required=True)
    commands.add_parser("workbench", help="Retired browser authoring command; use explore --open.")


def _json(root, path):
    return read_json(safe_path(root, path))


def dispatch(root, args):
    name = args.command
    if name == "advanced-health":
        from ontology_health import advanced_health
        return advanced_health(root, scope=args.scope, level=args.level, required=args.require, workbench_url=args.workbench_url)
    if name == "profile-setup":
        if args.profile == "semantic":
            from ontology_semantic import setup_profile, health
            return setup_profile(root) if args.provision else health(root)
        from ontology_profiles import setup_profile
        return setup_profile(root, "standards", provision=args.provision)
    if name == "profile-configure":
        from ontology_profiles import configure_profile
        value = _json(root, args.payload)
        exact(value, ("profile", "enabled", "expected_config_sha256", "authority"))
        return configure_profile(root, **value)
    if name == "prepare-model":
        from ontology_semantic import prepare_model
        return prepare_model(root)
    if name == "build-semantic-index":
        from ontology_semantic import build_index
        return build_index(root, documents=args.document)
    if name == "semantic-search":
        from ontology_semantic import search
        return search(root, args.query, limit=args.limit, max_bytes=args.max_bytes)
    if name in {"dataset", "sparql", "shacl", "infer", "export-rdf", "import-rdf"}:
        import ontology_standards as standards
        limits = _json(root, args.limits_file) if getattr(args, "limits_file", None) else None
        if name == "dataset": return standards.dataset(root, graphs=args.graph, limits=limits)
        if name == "sparql":
            query = args.query if args.query is not None else read_bytes(safe_path(root, args.query_file)).decode("utf-8")
            return standards.query(root, query, graphs=args.graph, limits=limits)
        if name == "shacl":
            shapes = [read_bytes(safe_path(root, path)).decode("utf-8") for path in args.shapes]
            return standards.validate(root, graphs=args.graph, shapes=shapes, limits=limits)
        if name == "infer":
            return standards.infer(root, goals=args.goal, premise_ids=args.premise_id, expected_snapshot=args.expected_snapshot, limits=limits)
        if name == "import-rdf":
            from ontology_proposals import stage_rdf_import
            data = read_bytes(safe_path(root, args.input))
            staged = standards.stage_import(root, data.decode("utf-8"), args.serialization,
                                            manifest=_json(root, args.manifest) if args.manifest else None)
            if not staged.get("complete"): return staged
            return stage_rdf_import(root, staged, {"path": args.input, "sha256": sha256(data), "locator": "line:1"}, args.reason)
        result = standards.export(root, args.serialization, selected_graph=args.graph)
        if not result.get("complete"): return result
        require(args.output.startswith((".sys4ai/ontology/exports/", "exports/")), "export_scope", "Use an explicitly selected export directory, never canonical ontology paths.")
        target = safe_path(root, args.output, must_exist=False)
        require((sha256(target) if target.exists() else None) == args.expected_output_sha256,
                "export_conflict", "Export overwrite requires the exact current destination hash.")
        manifest_path = args.output + ".manifest.json"
        require(not safe_path(root, manifest_path, must_exist=False).exists(), "export_conflict", "Select a new export with a new companion manifest.")
        result["manifest"].update(context=result["context"])
        atomic_write(root, manifest_path, canonical_bytes(result["manifest"]), None)
        try:
            atomic_write(root, args.output, result["content"].encode("utf-8"), args.expected_output_sha256)
        except Exception:
            return {"status": "partial", "mutated": True, "manifest": manifest_path,
                    "diagnostic": "The manifest was written but the selected export was not confirmed. Inspect both paths; do not replay blindly."}
        return {"status": "exported", "output": args.output, "sha256": sha256(target), "manifest": manifest_path,
                "manifest_sha256": sha256(safe_path(root, manifest_path)), "mutated": True}
    if name.startswith("proposal-"):
        import ontology_proposals as proposals
        if name == "proposal-list": return {"status": "ok", "proposals": proposals.list_proposals(root), "mutated": False}
        if name == "proposal-show": return proposals.open_proposal(root, args.proposal_id, revision=args.revision)
        if name == "proposal-save":
            data = _json(root, args.payload)
            exact(data, ("candidate", "rationale"), ("proposal_id", "expected_revision", "evidence", "uncertainty", "generator", "source_packet", "addressed_findings"))
            return proposals.save(root, **data)
        if name == "proposal-validate":
            from ontology_proposal_validation import validate_candidate
            return validate_candidate(root, args.proposal_id, expected_revision=args.revision)
        if name == "proposal-publish":
            from ontology_proposal_validation import publish_revision
            return publish_revision(root, args.proposal_id, _json(root, args.grant_file), expected_revision=args.revision,
                                    expected_review_sha256=args.expected_review_sha256)
        return proposals.decide(root, args.proposal_id, expected_revision=args.revision, decision=args.decision,
                                reason=args.reason, validation_sha256=args.validation_sha256, superseded_by=args.superseded_by)
    if name.startswith("generation-"):
        import ontology_generation as generation
        if name == "generation-show": return generation.read_request(root, args.request_id)
        data = _json(root, args.payload)
        if name == "generation-prepare":
            exact(data, ("sources", "context_ids", "instruction", "runtime"),
                  ("request_id", "previous_request", "findings", "proposal_id"))
            return generation.prepare(root, **data)
        exact(data, ("request_id", "result", "native_receipt"))
        return generation.capture(root, **data)
    if name.startswith("guard-"):
        import ontology_guard_setup as guards
        data = _json(root, args.payload)
        if name == "guard-preview":
            exact(data, ("operation_id", "contract", "repair", "verification"))
            return guards.preview_enablement(root, **data)
        if name == "guard-apply":
            exact(data, ("preview", "grant")); return guards.apply(root, **data)
        exact(data, ("operation_id", "grant")); return guards.recover(root, **data)
    if name == "workbench":
        require(False, "workbench_retired",
                "The browser workbench is retired. Use explore --open for the read-only Explorer; use trusted proposal commands for authoring.")
    require(False, "unsupported_operation", "Unknown advanced operation.")
