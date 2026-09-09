"""Fixed, local Basic Memory queries over a verified disposable projection.

No vendor CLI, MCP tool, server startup, project discovery, sync, or publication
is exposed. The SQLite and Python checks are application controls, not an OS
sandbox. Every public result is reconstructed from current canonical documents.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import stat
from pathlib import Path
import subprocess
import sys
import time

from basic_memory_projection import canonical_json, digest, verify_projection
from memory_paths import MemoryError, project_root, require, safe_path, safe_read_bytes

PROFILE = "basic-memory-v0.23.0"
VERSION = "0.23.0"
OPERATIONS = ("search", "health")
MODES = ("text", "vector", "hybrid")


def _limitations(error):
    code = getattr(error, "code", "backend_unavailable")
    if code == "file_absent":
        return [code, "A required backend profile, certificate, projection, or index file is absent; explicit setup or reindex is required."]
    if isinstance(error, FileNotFoundError):
        return ["backend_model_absent", "A pinned local model artifact is absent; reads do not download or repair it."]
    return [code]


def _config(root, supplied):
    from memory_core import load_config
    current = load_config(root)
    require(supplied is None or supplied == current, "backend_config_changed", "Use the current project configuration.")
    return current


def load_profile(root, config):
    raw = safe_read_bytes(root, config["contract_root"] + "/profiles/" + PROFILE + ".json")
    value = json.loads(raw)
    require(value.get("profile_id") == PROFILE and value.get("backend_version") == VERSION,
            "backend_profile", "Unsupported Basic Memory profile.")
    require(value.get("query_contract", {}).get("operations") == list(OPERATIONS),
            "backend_operations", "Backend writer operations are prohibited.")
    return value, digest(raw)


def _file_digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _model_directory(root, config, profile):
    model = profile["model"]
    rel = config["state"]["model_cache"] + "/" + model["revision"]
    directory = safe_path(root, rel, kind="dir")
    for artifact in model["files"]:
        # Tokenizer artifact names contain "tokens" but are immutable model data,
        # not candidate source/credential paths. Only the pinned direct children
        # of the already confined model directory enter this narrow exception.
        require(Path(artifact["path"]).name == artifact["path"], "backend_model_path", "Model artifact must be a direct child.")
        target = directory / artifact["path"]
        info = target.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                "backend_model_path", "Model artifacts must be regular, unlinked files.")
        require(target.stat().st_size == artifact["bytes"] and _file_digest(target) == artifact["sha256"],
                "backend_model_changed", "Pinned local model artifact is missing or changed.")
    require({p.name for p in directory.iterdir()} == {a["path"] for a in model["files"]},
            "backend_model_changed", "Unclassified model files are present.")
    return directory


def _read_certificate(root, config, *, documents=None):
    from memory_maintenance import pending_reindexes
    require(not pending_reindexes(root, config), "maintenance_pending", "Backend rebuild recovery is pending.")
    profile, profile_sha = load_profile(root, config)
    rel = config["state"]["backend_config"] + "/certification.json"
    certificate = json.loads(safe_read_bytes(root, rel))
    require(certificate.get("schema_version") == 1 and certificate.get("project_id") == config["project"]["id"]
            and certificate.get("project_root") == str(root), "backend_project", "Backend certificate belongs to another project.")
    require(certificate.get("profile_sha256") == profile_sha, "backend_profile_changed", "Pinned backend profile changed.")
    require(certificate.get("adapter_sha256") == _file_digest(Path(__file__)),
            "backend_adapter_changed", "Query implementation changed after backend certification.")
    require(certificate.get("config_sha256") == digest(safe_read_bytes(root, "memory.yaml")),
            "backend_config_changed", "Backend certificate configuration is stale.")
    require(certificate.get("backend_config_sha256") == digest(safe_read_bytes(root, config["state"]["backend_config"] + "/config.json")),
            "backend_config_changed", "Effective backend configuration changed.")
    projection = verify_projection(root, config, current_documents=documents)
    require(certificate.get("projection_sha256") == digest(safe_read_bytes(root, config["state"]["projection"] + "/manifest.json")),
            "backend_projection_changed", "Backend certificate projection changed.")
    db = safe_path(root, config["state"]["index"] + "/basic-memory.db")
    require(_file_digest(db) == certificate.get("database_sha256"), "backend_database_changed", "Backend database is stale or changed.")
    index = safe_path(root, config["state"]["index"], kind="dir")
    require({p.name for p in index.iterdir()} == {"basic-memory.db", "manifest.json"},
            "unclassified_index", "Unclassified or active database products prevent read-only queries.")
    manifest = json.loads(safe_read_bytes(root, config["state"]["index"] + "/manifest.json"))
    require(manifest == {"classification": "rebuildable-index", "files": {"basic-memory.db": certificate["database_sha256"]}},
            "backend_index_manifest", "Index ownership manifest changed.")
    _model_directory(root, config, profile)
    return profile, certificate, projection


def health(root, config=None):
    """Inspect existing state only. Never import or start the vendor runtime."""
    root = project_root(root)
    try:
        config = _config(root, config)
        if not config["backend"]["enabled"] or not config["backend"]["semantic_enabled"]:
            return {"available": False, "mode": "lexical", "limitations": ["backend_disabled"]}
        profile, certificate, projection = _read_certificate(root, config)
        return {"available": True, "mode": "prebuilt-profile", "profile": profile["profile_id"],
                "documents": len(projection["entries"]), "limitations": ["runtime_not_started_by_health"]}
    except (MemoryError, OSError, ValueError, KeyError, TypeError) as exc:
        return {"available": False, "mode": "lexical", "limitations": _limitations(exc)}


def _runtime_python(root):
    try:
        if importlib.metadata.version("basic-memory") == VERSION:
            return sys.executable
    except importlib.metadata.PackageNotFoundError:
        pass
    executable = root / ".venv-memory-pilot/bin/python"
    require(executable.is_file(), "backend_runtime_absent", "Pinned local pilot runtime is not installed.")
    return str(executable)


def _worker_environment(root, config):
    # Do not inherit API keys, backend overrides, cloud routing, Python startup
    # customization, or a caller's Hugging Face configuration.
    env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "SYSTEMROOT", "TMPDIR") if key in os.environ}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "HF_HUB_OFFLINE": "1",
                "HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false",
                "BASIC_MEMORY_CONFIG_DIR": str(root / config["state"]["backend_config"]),
                "BASIC_MEMORY_MCP_PROJECT": config["project"]["id"], "BASIC_MEMORY_AUTO_UPDATE": "false",
                "BASIC_MEMORY_ENSURE_FRONTMATTER_ON_SYNC": "false"})
    return env


def run_worker(root, config, request, *, build=False):
    """Fixed program and JSON input only; callers cannot supply commands/tools."""
    started = time.perf_counter()
    proc = subprocess.run([_runtime_python(root), "-B", str(Path(__file__).resolve()),
                           "--build-worker" if build else "--query-worker"],
                          input=canonical_json(request), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=root, env=_worker_environment(root, config), timeout=180 if build else 60,
                          check=False)
    require(len(proc.stdout) <= 2_000_000, "backend_output_limit", "Backend response exceeded the result limit.")
    try:
        value = json.loads(proc.stdout)
    except (ValueError, UnicodeError) as exc:
        raise MemoryError("backend_failed", "Backend did not return a valid fixed-operation result.",
                          {"returncode": proc.returncode, "stderr_tail": proc.stderr.decode(errors="replace")[-1500:]}) from exc
    require(proc.returncode == 0 and value.get("ok") is True, value.get("error", "backend_failed"),
            "Pinned backend operation failed.", {"error_detail": value.get("detail"), "returncode": proc.returncode})
    value["subprocess_seconds"] = round(time.perf_counter() - started, 6)
    return value


def query(root, query, config=None, *, mode="hybrid", limit=20, packet=None, pilot=False):
    root = project_root(root)
    require(mode in MODES and isinstance(query, str) and 0 < len(query.strip()) <= 4096 and
            isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= 200 and type(pilot) is bool,
            "backend_query", "Expected a bounded text query and supported retrieval mode.")
    try:
        config = _config(root, config)
        if not pilot and (not config["backend"]["enabled"] or not config["backend"]["semantic_enabled"]):
            return {"available": False, "mode": "lexical", "results": [], "limitations": ["backend_disabled"]}
        from memory_search import collect_documents
        documents, limitations = collect_documents(root, config, historical=False)
        profile, certificate, projection = _read_certificate(root, config, documents=documents)
        if packet is not None:
            from memory_packet import filter_documents
            documents = filter_documents(root, config, documents, packet)
        request = {"root": str(root), "operation": "search", "query": query.strip(), "mode": mode,
                   "limit": limit, "profile_sha256": certificate["profile_sha256"]}
        response = run_worker(root, config, request)
        # Ranking cannot confer scope, lifecycle, metadata, body, or title authority.
        current = {(d["kind"], d["path"]): d for d in documents}
        allowed = {e["projection_path"]: e for e in projection["entries"]}
        results, seen = [], set()
        for row in response["results"]:
            entry = allowed.get(row.get("projection_path"))
            if entry is None or row.get("project_id") != 1:
                continue
            document = current.get((entry["kind"], entry["path"]))
            if document is None or digest(safe_read_bytes(root, entry["path"])) != entry["sha256"]:
                continue
            key = (entry["kind"], entry["source_identity"])
            if key in seen:
                continue
            seen.add(key)
            results.append({"path": entry["path"], "sha256": entry["sha256"], "kind": entry["kind"],
                            "source_identity": entry["source_identity"], "score": row.get("score"),
                            "retrieval_mode": mode})
        return {"available": True, "mode": mode, "results": results[:limit], "limitations": limitations,
                "runtime": {k: v for k, v in response.items() if k not in {"results", "ok"}}}
    except (MemoryError, OSError, ValueError, KeyError, TypeError, ImportError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "mode": "lexical", "results": [],
                "limitations": _limitations(exc)}


def _audit_guard(write_root=None):
    """Deny network and Python-level writes beyond an optional staging directory."""
    write_root = Path(write_root).resolve() if write_root else None

    def may_write(value):
        if isinstance(value, int):
            return False
        try:
            target = Path(value).absolute()
        except (TypeError, ValueError):
            return False
        return write_root is not None and (target == write_root or write_root in target.parents)

    def audit(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.bind", "socket.sendto", "subprocess.Popen", "os.system"}:
            raise PermissionError("backend_network_or_process_denied:" + event)
        if event == "open":
            filename, mode, flags = args
            if (flags or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                if not may_write(filename):
                    raise PermissionError("backend_write_denied:open")
        elif event in {"os.remove", "os.rename", "os.rmdir", "os.chmod", "os.chown", "os.truncate", "os.link", "os.symlink", "os.utime"}:
            if not may_write(args[0]) or (event in {"os.rename", "os.link", "os.symlink"} and not may_write(args[1])):
                raise PermissionError("backend_write_denied:" + event)
        elif event == "os.mkdir" and not Path(args[0]).is_dir() and not may_write(args[0]):
            raise PermissionError("backend_write_denied:mkdir")
    sys.addaudithook(audit)


async def vendor_operation(root, config, profile, request, *, build=False):
    """The only vendor integration. Imports occur solely inside the worker."""
    from datetime import datetime
    import resource
    from sqlalchemy import event, text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from basic_memory.config_models import BasicMemoryConfig
    from basic_memory.repository.fastembed_provider import FastEmbedEmbeddingProvider
    from basic_memory.repository.sqlite_search_repository import SQLiteSearchRepository
    from basic_memory.schemas.search import SearchItemType, SearchRetrievalMode
    from loguru import logger
    logger.remove()
    local_model = _model_directory(root, config, profile)

    class LocalPinnedProvider(FastEmbedEmbeddingProvider):
        def _create_model(self):
            from fastembed import TextEmbedding
            return TextEmbedding(model_name=profile["model"]["fastembed_name"],
                                 specific_model_path=str(local_model), local_files_only=True,
                                 cache_dir=str(local_model), threads=2, enable_cpu_mem_arena=False)

        def _purge_model_subdirs(self, subdirs):
            raise PermissionError("Automatic model cache repair is prohibited.")

    provider = LocalPinnedProvider(model_name=profile["model"]["name"], dimensions=384,
                                  cache_dir=str(local_model), threads=2, parallel=1)
    projection_dir = root / config["state"]["projection"]
    settings = BasicMemoryConfig(**profile["controls"], default_project=config["project"]["id"],
                                 projects={config["project"]["id"]: {"path": str(projection_dir), "mode": "local"}},
                                 semantic_embedding_cache_dir=str(local_model), project_root=str(projection_dir))
    if build:
        db_path = safe_path(root, request["database"], must_exist=False)
        require(not db_path.exists(), "backend_stage_exists", "Refusing to overwrite a staged database.")
        engine = create_async_engine("sqlite+aiosqlite:///" + str(db_path))
    else:
        db_path = safe_path(root, config["state"]["index"] + "/basic-memory.db")
        engine = create_async_engine("sqlite+aiosqlite:///file:" + str(db_path) + "?mode=ro&immutable=1&uri=true")
        @event.listens_for(engine.sync_engine, "connect")
        def readonly(connection, record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA query_only=ON")
            cursor.close()
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    repository = SQLiteSearchRepository(session_maker, project_id=1, app_config=settings,
                                        embedding_provider=provider)
    started = time.perf_counter()
    try:
        if build:
            from basic_memory.models import Base, Entity, Project
            from basic_memory.repository.search_index_row import SearchIndexRow
            manifest = request["projection_manifest"]
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            async with session_maker() as session:
                session.add(Project(id=1, name=config["project"]["id"], path=str(projection_dir)))
                await session.commit()
            await repository.init_search_index()
            for number, entry in enumerate(manifest["entries"], start=1):
                projected = safe_read_bytes(root, request["projection_stage"] + "/" + entry["projection_path"])
                require(digest(projected) == entry["projection_sha256"], "projection_changed", "Staged projection changed.")
                content = projected.decode().split("\n---\n", 1)[1].strip()
                created, modified = datetime.fromisoformat(entry["created"]), datetime.fromisoformat(entry["modified"])
                async with session_maker() as session:
                    session.add(Entity(id=number, project_id=1, title=entry["title"], note_type="note",
                                       entity_metadata={"sys4ai_metadata": entry["metadata"]},
                                       content_type="text/markdown", permalink=entry["permalink"],
                                       file_path=entry["projection_path"], checksum=entry["projection_sha256"],
                                       created_at=created, updated_at=modified))
                    await session.commit()
                await repository.index_item(SearchIndexRow(project_id=1, id=number, type="entity",
                                           entity_id=number,
                                           file_path=entry["projection_path"], title=entry["title"],
                                           permalink=entry["permalink"], metadata={"sys4ai_metadata": entry["metadata"]},
                                           created_at=created, updated_at=modified,
                                           content_stems=content, content_snippet=content))
                await repository.sync_entity_vectors(number)
            async with session_maker() as session:
                counts = (await session.execute(text("SELECT COUNT(*), COUNT(DISTINCT entity_id) FROM search_vector_chunks WHERE project_id=1 AND embedding_status='ready'"))).one()
            require(counts[1] == len(manifest["entries"]), "backend_vector_coverage", "Not every projected document has ready semantic vectors.")
            result = {"indexed_documents": len(manifest["entries"]), "ready_vector_chunks": counts[0], "vector_entities": counts[1]}
        else:
            async with session_maker() as session:
                projects = (await session.execute(text("SELECT id,name,path FROM project"))).all()
                require(len(projects) == 1 and tuple(projects[0]) == (1, config["project"]["id"], str(projection_dir)),
                        "backend_project", "Vendor database project binding is invalid.")
                counts = (await session.execute(text("SELECT COUNT(*), COUNT(DISTINCT entity_id) FROM search_vector_chunks WHERE project_id=1 AND embedding_status='ready'"))).one()
                entity_count = (await session.execute(text("SELECT COUNT(*) FROM entity WHERE project_id=1"))).scalar()
                require(counts[1] == entity_count, "backend_vector_coverage", "Semantic coverage is incomplete; reindex requires explicit maintenance.")
            mode = SearchRetrievalMode.FTS if request["mode"] == "text" else SearchRetrievalMode(request["mode"])
            rows = await repository.search(search_text=request["query"], retrieval_mode=mode,
                                           search_item_types=[SearchItemType.ENTITY], limit=request["limit"])
            result = {"results": [{"projection_path": row.file_path, "project_id": row.project_id,
                                    "score": row.score} for row in rows], "mode": request["mode"],
                      "ready_vector_chunks": counts[0], "vector_entities": counts[1]}
        result.update({"ok": True, "vendor_seconds": round(time.perf_counter() - started, 6),
                       "max_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                       "effective_controls": {k: getattr(settings, k) for k in profile["controls"]},
                       "package_version": VERSION, "model_revision": profile["model"]["revision"]})
        return result
    finally:
        await engine.dispose()


def _main():
    import asyncio
    try:
        require(sys.argv[1:] in [["--query-worker"], ["--build-worker"]], "backend_operation", "Unsupported backend operation.")
        build = sys.argv[1] == "--build-worker"
        raw = sys.stdin.buffer.read(4_000_001)
        require(len(raw) <= 4_000_000, "backend_request_limit", "Backend request exceeds limit.")
        request = json.loads(raw)
        root = project_root(request["root"])
        config = _config(root, None)
        profile, sha = load_profile(root, config)
        require(request["profile_sha256"] == sha, "backend_profile_changed", "Backend profile changed.")
        for package in profile["dependency_lock"]:
            require(importlib.metadata.version(package["name"]) == package["version"],
                    "backend_dependency_changed", "Pinned runtime package version changed.")
        if build:
            from memory_maintenance import verify_build_request
            write_root = verify_build_request(root, config, request)
        else:
            require(request.get("operation") == "search" and request.get("mode") in MODES
                    and isinstance(request.get("query"), str) and 0 < len(request["query"]) <= 4096
                    and isinstance(request.get("limit"), int) and not isinstance(request["limit"], bool) and 1 <= request["limit"] <= 200,
                    "backend_operation", "Only fixed bounded search is permitted.")
            _read_certificate(root, config)
            write_root = None
        _audit_guard(write_root)
        value = asyncio.run(vendor_operation(root, config, profile, request, build=build))
        print(json.dumps(value, default=str))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": getattr(exc, "code", type(exc).__name__), "detail": str(exc)[:1600]}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
