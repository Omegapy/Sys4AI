"""Explicit, authorized rebuilding of classified memory retrieval products."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import uuid

from basic_memory_projection import canonical_json, digest, render_projection
from memory_paths import MemoryError, corpus_allowed, project_root, require, safe_path, safe_read_bytes

TERMINAL = {"complete", "aborted"}


def _files(root, relative):
    directory = safe_path(root, relative, must_exist=False, kind="dir")
    if not directory.exists():
        return {}
    result = {}
    for candidate in sorted(directory.rglob("*")):
        rel = candidate.relative_to(root).as_posix()
        safe_path(root, rel, kind="any")
        if candidate.is_file():
            result[candidate.relative_to(directory).as_posix()] = digest(safe_read_bytes(root, rel))
    return result


def _classified(root, config):
    """Unknown state is never silently deleted, replaced, or adopted."""
    result = {}
    for kind in ("projection", "index", "normalized", "backend_config"):
        rel = config["state"][kind]
        current = _files(root, rel)
        directory = safe_path(root, rel, must_exist=False, kind="dir")
        require(not directory.exists() or not any(p.is_dir() for p in directory.iterdir()),
                "unclassified_state", "Unexpected nested state directories cannot be replaced.")
        if current and kind == "projection":
            require("manifest.json" in current, "unclassified_state", "Projection ownership manifest is absent.")
            manifest = json.loads(safe_read_bytes(root, rel + "/manifest.json"))
            expected = {e["projection_path"]: e["projection_sha256"] for e in manifest.get("entries", [])}
            require(manifest.get("classification") == "rebuildable-projection" and
                    {k: v for k, v in current.items() if k != "manifest.json"} == expected,
                    "unclassified_state", "Projection contains unknown or modified content.")
        elif current and kind == "index":
            require("manifest.json" in current, "unclassified_state", "Index ownership manifest is absent.")
            manifest = json.loads(safe_read_bytes(root, rel + "/manifest.json"))
            require(manifest.get("classification") == "rebuildable-index" and
                    {k: v for k, v in current.items() if k != "manifest.json"} == manifest.get("files"),
                    "unclassified_state", "Index contains unknown or modified content.")
        elif current and kind == "normalized":
            owned = {}
            receipts = safe_path(root, config["state"]["maintenance"], must_exist=False, kind="dir")
            if receipts.exists():
                for receipt in receipts.glob("backend-*.json"):
                    journal = json.loads(safe_read_bytes(root, receipt.relative_to(root).as_posix()))
                    if journal.get("operation") == "reindex" and journal.get("status") == "complete":
                        for product in journal.get("normalization", {}).get("products", []):
                            owned.setdefault(product["path"], set()).add(product["sha256"])
            for name in current:
                require(Path(name).name == name and name.endswith(".json"), "unclassified_state", "Unknown normalization artifact.")
                product = json.loads(safe_read_bytes(root, rel + "/" + name))
                require(set(product) == {"schema_version", "normalization_version", "document"} and
                        product["schema_version"] == 1 and product["document"].get("kind") == "source",
                        "unclassified_state", "Sole-copy or unclassified normalization content cannot be replaced.")
                doc = product["document"]
                require({"path", "sha256", "source_identity", "extractor", "segments", "kind", "format", "limitations"} <= set(doc)
                        and isinstance(doc["path"], str) and corpus_allowed(doc["path"], config)
                        and name == digest(doc["path"].encode()) + ".json"
                        and isinstance(doc["sha256"], str) and re.fullmatch("[a-f0-9]{64}", doc["sha256"])
                        and isinstance(doc["extractor"], str) and doc["extractor"]
                        and isinstance(doc["source_identity"], str) and doc["source_identity"]
                        and isinstance(doc["segments"], list)
                        and all(isinstance(s, dict) and {"text", "locator", "heading"} <= set(s) for s in doc["segments"])
                        and current[name] in owned.get(rel + "/" + name, set()),
                        "unclassified_state", "Normalization lacks exact path, provenance or completed maintenance ownership.")
        elif kind == "backend_config":
            require(set(current) <= {"config.json", "certification.json"}, "unclassified_state", "Unknown durable backend configuration must be preserved.")
            if "config.json" in current:
                value = json.loads(safe_read_bytes(root, rel + "/config.json"))
                require(set(value) == {"profile_id", "profile_sha256", "project_id", "project_path", "controls", "routing", "mcp_registered"}
                        and value["profile_id"] == "basic-memory-v0.23.0"
                        and value["project_id"] == config["project"]["id"]
                        and value["project_path"] == config["state"]["projection"]
                        and value["routing"] == "local" and value["mcp_registered"] is False,
                        "unclassified_state", "Backend configuration is not an attributable local profile.")
        result[kind] = current
    return result


def pending_reindexes(root, config):
    directory = safe_path(root, config["state"]["maintenance"], must_exist=False, kind="dir")
    if not directory.exists():
        return []
    pending = []
    for candidate in sorted(directory.glob("backend-*.json")):
        journal = json.loads(safe_read_bytes(root, candidate.relative_to(root).as_posix()))
        require(journal.get("operation") == "reindex" and journal.get("schema_version") == 1,
                "maintenance_journal", "Unknown backend maintenance journal.")
        if journal.get("status") not in TERMINAL:
            pending.append(journal)
    return pending


def reindex_payload(root, config=None):
    """Return the concrete request to bind into a reindex grant; read-only."""
    from memory_core import load_config
    from memory_search import collect_documents
    from basic_memory_adapter import load_profile
    root = project_root(root)
    current = load_config(root)
    require(config is None or config == current, "config_changed", "Use current memory configuration.")
    config = current
    profile, profile_sha = load_profile(root, config)
    documents, limitations = collect_documents(root, config)
    files, manifest = render_projection(root, config, documents)
    payload = {"schema_version": 1, "operation": "reindex", "project_id": config["project"]["id"],
               "config_sha256": digest(safe_read_bytes(root, "memory.yaml")), "profile_sha256": profile_sha,
               "projection_manifest": manifest,
               "before": _classified(root, config),
               "paths": [config["state"][k] for k in ("projection", "index", "normalized", "backend_config", "maintenance")],
               "limitations": limitations}
    return payload


def _write(root, relative, data):
    from memory_recovery import atomic_replace
    path = safe_path(root, relative, must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    prior = digest(safe_read_bytes(root, relative)) if path.exists() else None
    atomic_replace(root, relative, data, prior)


def verify_build_request(root, config, request):
    """Worker repeats the actual authority and exact staging checks."""
    from memory_publish import authorize
    payload = request.get("payload")
    require(isinstance(payload, dict) and payload.get("operation") == "reindex", "maintenance_request", "Missing concrete reindex request.")
    authorize(root, config, request["grant_file"], "reindex", digest(canonical_json(payload)),
              request["actor"], paths=payload["paths"])
    operation_id = request["operation_id"]
    require(len(operation_id) == 32 and all(c in "0123456789abcdef" for c in operation_id),
            "maintenance_operation", "Invalid maintenance identity.")
    staging = config["state"]["maintenance"] + "/backend-" + operation_id
    require(request["database"] == staging + "/index/basic-memory.db" and
            request["projection_stage"] == staging + "/projection" and
            request["projection_manifest"] == payload["projection_manifest"],
            "maintenance_scope", "Worker may write only its approved backend staging directory.")
    require(payload["config_sha256"] == digest(safe_read_bytes(root, "memory.yaml")),
            "config_changed", "Configuration changed after maintenance approval.")
    for entry in payload["projection_manifest"]["entries"]:
        require(digest(safe_read_bytes(root, entry["path"])) == entry["sha256"],
                "source_changed", "Canonical source changed after maintenance approval.")
    return safe_path(root, staging, kind="dir")


def reindex(root, *, grant_file, actor, expected_payload_sha256, config=None):
    from memory_core import load_config
    from memory_publish import authorize
    from memory_recovery import project_lock
    from memory_search import collect_documents
    from memory_normalization import build_normalized
    from basic_memory_adapter import load_profile, run_worker, _model_directory, _file_digest
    root = project_root(root)
    current = load_config(root)
    require(config is None or config == current, "config_changed", "Use current memory configuration.")
    config = current
    payload = reindex_payload(root, config)
    require(digest(canonical_json(payload)) == expected_payload_sha256,
            "maintenance_request_changed", "Reindex input differs from the reviewed payload.")
    authorize(root, config, grant_file, "reindex", expected_payload_sha256, actor, paths=payload["paths"])
    profile, profile_sha = load_profile(root, config)
    _model_directory(root, config, profile)
    with project_lock(root):
        require(not pending_reindexes(root, config), "maintenance_pending", "An earlier rebuild requires explicit recovery.")
        require(reindex_payload(root, config) == payload, "maintenance_request_changed", "Reindex input changed while acquiring ownership.")
        operation_id = uuid.uuid4().hex
        stage = config["state"]["maintenance"] + "/backend-" + operation_id
        journal_rel = stage + ".json"
        journal = {"schema_version": 1, "operation": "reindex", "operation_id": operation_id,
                   "project_id": config["project"]["id"], "status": "preparing", "payload": payload,
                   "payload_sha256": expected_payload_sha256, "actor": actor, "effects": []}
        _write(root, journal_rel, canonical_json(journal))
        try:
            documents, limitations = collect_documents(root, config)
            files, manifest = render_projection(root, config, documents)
            require(manifest == payload["projection_manifest"], "source_changed", "Projection inputs changed.")
            for name, raw in files.items():
                _write(root, stage + "/projection/" + name, raw)
            _write(root, stage + "/projection/manifest.json", canonical_json(manifest))
            safe_path(root, stage + "/index", must_exist=False, kind="dir").mkdir(parents=True, exist_ok=False)
            journal["status"] = "building"
            _write(root, journal_rel, canonical_json(journal))
            request = {"root": str(root), "operation": "reindex", "operation_id": operation_id,
                       "profile_sha256": profile_sha, "payload": payload, "grant_file": grant_file, "actor": actor,
                       "projection_manifest": manifest, "projection_stage": stage + "/projection",
                       "database": stage + "/index/basic-memory.db"}
            result = run_worker(root, config, request, build=True)
            db_hash = _file_digest(safe_path(root, request["database"]))
            _write(root, stage + "/index/manifest.json", canonical_json({"classification": "rebuildable-index", "files": {"basic-memory.db": db_hash}}))
            require(reindex_payload(root, config) == payload, "source_changed", "Canonical or existing derived state changed while indexing.")
            journal.update(status="publishing", runtime=result, after={"projection": _files(root, stage + "/projection"),
                                                                         "index": _files(root, stage + "/index")})
            _write(root, journal_rel, canonical_json(journal))
            for kind in ("projection", "index"):
                target = safe_path(root, config["state"][kind], must_exist=False, kind="dir")
                backup = safe_path(root, stage + "/previous-" + kind, must_exist=False, kind="dir")
                if target.exists():
                    os.rename(target, backup)
                os.rename(safe_path(root, stage + "/" + kind, kind="dir"), target)
                journal["effects"].append("replaced_" + kind)
                _write(root, journal_rel, canonical_json(journal))
            settings = {"profile_id": profile["profile_id"], "profile_sha256": profile_sha,
                        "project_id": config["project"]["id"], "project_path": config["state"]["projection"],
                        "controls": profile["controls"], "routing": "local", "mcp_registered": False}
            _write(root, config["state"]["backend_config"] + "/config.json", canonical_json(settings))
            certificate = {"schema_version": 1, "project_id": config["project"]["id"], "project_root": str(root),
                           "profile_sha256": profile_sha, "config_sha256": payload["config_sha256"],
                           "backend_config_sha256": digest(canonical_json(settings)),
                           "projection_sha256": digest(canonical_json(manifest)), "database_sha256": db_hash,
                           "adapter_sha256": _file_digest(Path(__file__).with_name("basic_memory_adapter.py")),
                           "operation_id": operation_id, "certification": "prebuilt-state-only; global compatibility remains a separate pilot decision"}
            _write(root, config["state"]["backend_config"] + "/certification.json", canonical_json(certificate))
            journal["normalization"] = build_normalized(root, config)
            journal.update(status="complete", limitations=limitations)
            _write(root, journal_rel, canonical_json(journal))
            return {"status": "reindexed", "operation_id": operation_id, "journal": journal_rel,
                    "projection_documents": len(manifest["entries"]), "runtime": result, "limitations": limitations}
        except Exception as exc:
            journal.update(status="failed", error={"code": getattr(exc, "code", type(exc).__name__), "message": str(exc)[:1200]})
            _write(root, journal_rel, canonical_json(journal))
            raise


def recover_reindex(root, operation_id, *, grant_file, actor):
    """Abort a pre-publication rebuild, or restore exact prior derived products.

    Partial products and the original failure receipt remain attributable. No
    canonical memory is replayed or deleted and no Task state is changed.
    """
    from memory_core import load_config
    from memory_publish import authorize
    from memory_recovery import project_lock
    root = project_root(root)
    config = load_config(root)
    require(len(operation_id) == 32 and all(c in "0123456789abcdef" for c in operation_id),
            "maintenance_operation", "Invalid maintenance identity.")
    stage = config["state"]["maintenance"] + "/backend-" + operation_id
    rel = stage + ".json"
    journal = json.loads(safe_read_bytes(root, rel))
    require(journal.get("operation_id") == operation_id and journal.get("status") not in TERMINAL,
            "maintenance_operation", "Only a pending exact rebuild can be recovered.")
    authorize(root, config, grant_file, "reindex", journal["payload_sha256"], actor, paths=journal["payload"]["paths"])
    with project_lock(root):
        for kind in ("projection", "index"):
            before = journal["payload"]["before"][kind]
            target_rel = config["state"][kind]
            backup_rel = stage + "/previous-" + kind
            backup = safe_path(root, backup_rel, must_exist=False, kind="dir")
            target = safe_path(root, target_rel, must_exist=False, kind="dir")
            actual = _files(root, target_rel)
            if actual == before and not backup.exists():
                continue
            require(actual == journal.get("after", {}).get(kind) or not target.exists(),
                    "recovery_conflict", "Changed derived state blocks exact recovery.")
            if target.exists():
                os.rename(target, safe_path(root, stage + "/aborted-" + kind, must_exist=False, kind="dir"))
            if before:
                require(backup.exists() and _files(root, backup_rel) == before,
                        "recovery_conflict", "Prior derived products are not intact.")
                os.rename(backup, target)
        # Any certificate from a partial publication may now reference aborted
        # products. Public reads fail closed until a separately authorized rebuild.
        journal["status"] = "aborted"
        journal["recovery_actor"] = actor
        _write(root, rel, canonical_json(journal))
        return {"status": "aborted", "operation_id": operation_id, "journal": rel}


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
    return MemoryError(code, message, details)

ONTOLOGY_GUARDED_ACTIONS = ['reindex', 'recover_reindex']
reindex = _ontology_guard_adapter(reindex, 'memory', 'root', ['MEMORY'])
recover_reindex = _ontology_guard_adapter(recover_reindex, 'memory', 'root', ['MEMORY'])
