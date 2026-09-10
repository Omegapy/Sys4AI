"""Deterministic rebuildable projections with explicit ownership and no ingestion."""
from pathlib import Path
import re
from ontology_core import (load_project, canonical_bytes, sha256, safe_path, read_bytes,
                           read_json, require, OntologyError, atomic_write, operation_lock, assert_current)
from ontology_validate import validate_project


def write_generated(project, outputs, *, operation):
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,49}", operation), "invalid_operation", "Expected a bounded generated operation name.")
    result = validate_project(project, require_current=True)
    require(result["valid"], "invalid_graph", "Generated publication requires valid current canonical inputs.")
    require(isinstance(outputs, dict) and len(outputs) <= 10000, "invalid_outputs", "Expected a bounded generated output mapping.")
    ownership_path = f".sys4ai/ontology/manifests/{operation}.json"
    for path, data in outputs.items():
        safe_path(project.root, path, must_exist=False)
        require(path.startswith((".sys4ai/ontology/", "ONTOLOGY/WIKI/")) and not path.startswith(".sys4ai/ontology/manifests/") and not path.endswith(".lock") and isinstance(data, bytes), "generated_scope", "Output is outside the declared rebuildable destinations.", path=path)
    manifest_file = safe_path(project.root, ownership_path, must_exist=False)
    old = read_json(manifest_file) if manifest_file.exists() else {"outputs": {}}
    require(isinstance(old, dict) and isinstance(old.get("outputs"), dict), "invalid_manifest", "Existing generated ownership manifest is invalid.")
    hashes = {path: sha256(data) for path, data in sorted(outputs.items())}
    manifest = {"schema_version": 1, "operation": operation, "outputs": hashes, "context": project.context()}
    writes = {**outputs, ownership_path: canonical_bytes(manifest)}
    previous = {}
    for path in writes:
        target = safe_path(project.root, path, must_exist=False)
        data = read_bytes(target) if target.exists() else None
        if data is not None and path != ownership_path:
            require(path in old["outputs"] and sha256(data) == old["outputs"][path], "generated_conflict", "Existing output is unknown or edited; preserve it and resolve the conflict.", path=path)
        previous[path] = data
    # Obsolete managed outputs are retained; no directory cleanup can remove user files.
    committed = []
    with operation_lock(project.root, ".sys4ai/ontology/build.lock"):
        assert_current(project)
        try:
            for path, data in writes.items():
                expected = sha256(previous[path]) if previous[path] is not None else None
                atomic_write(project.root, path, data, expected)
                committed.append(path)
        except (OSError, OntologyError) as exc:
            conflicts = []
            for path in reversed(committed):
                try:
                    target = safe_path(project.root, path)
                    require(sha256(target) == sha256(writes[path]), "rollback_conflict", "Concurrent changes block rollback.", path=path)
                    if previous[path] is None: target.unlink()
                    else: atomic_write(project.root, path, previous[path], sha256(writes[path]))
                except (OSError, OntologyError): conflicts.append(path)
            if conflicts:
                raise OntologyError("partial_build", "Generated rollback encountered changed files: " + ", ".join(conflicts)) from exc
            raise
    return {"status": "complete", "operation": operation, "outputs": hashes, "manifest": {"path": ownership_path, "sha256": sha256(writes[ownership_path])}, "context": project.context()}


def compile_project(project_or_root):
    project = project_or_root if hasattr(project_or_root, "records") else load_project(project_or_root)
    graph = {"schema_version": 1, "generated": True, "records": project.records, "context": project.context()}
    index = {"schema_version": 1, "generated": True, "entries": [{"id": r["@id"], "label": r.get("label"), "aliases": r.get("aliases", []), "kind": r["kind"], "lifecycle": r.get("lifecycle"), "fact_kind": r.get("fact_kind"), "canonical": project.locations[r["@id"]]} for r in project.records], "context": project.context()}
    return write_generated(project, {".sys4ai/ontology/compiled/graph.json": canonical_bytes(graph), ".sys4ai/ontology/compiled/index.json": canonical_bytes(index)}, operation="compile")
