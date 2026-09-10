"""Explicit ontology-only embeddings; retrieval never installs, downloads or rebuilds."""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from ontology_core import (OntologyError, atomic_write, canonical_bytes, exact,
                           load_project, operation_lock, read_bytes, read_json,
                           require, safe_path, sha256, source_status)

VERSION = "1.0.0"
BASE = ".sys4ai/ontology/semantic"
MODEL_MANIFEST = BASE + "/model.json"
INDEX = BASE + "/index-v1.json"
ENVIRONMENT = ".venv-ontology-semantic"
PACKAGE = Path(__file__).resolve().parent.parent
MAX_ITEMS = 2000
MAX_TEXT = 8000


def specification():
    return read_json(PACKAGE / "profiles/semantic-v1.json")


def locked_versions():
    return dict(line.split()[0].split("==", 1) for line in (PACKAGE / "requirements-semantic.txt").read_text().splitlines()
                if line.strip() and not line.startswith("#"))


def backend_versions(root):
    """Read the selected environment metadata; never import optional packages on a health read."""
    versions = locked_versions()
    site = ENVIRONMENT + "/lib/python3.12/site-packages/"
    require(safe_path(root, ENVIRONMENT, must_exist=False).is_dir() and
            safe_path(root, ENVIRONMENT + "/pyvenv.cfg", must_exist=False).is_file(),
            "semantic_backend_unavailable", "Explicitly install the independent ontology semantic profile.")
    for name, version in versions.items():
        metadata = safe_path(root, site + name.replace("-", "_") + "-" + version + ".dist-info/METADATA")
        fields = read_bytes(metadata).decode("utf-8")
        require("\nVersion: " + version + "\n" in "\n" + fields, "semantic_version_mismatch", "Installed package differs from its lock: " + name)
    return versions


def profile(root):
    if not safe_path(root, "ontology-advanced.yaml", must_exist=False).exists():
        return {"enabled": False}, None
    from ontology_advanced import load_advanced
    advanced = load_advanced(root, required=False)
    if not advanced:
        return {"enabled": False}, None
    # Companion configuration is validated by its owner before consumption.
    cfg = dict(advanced.get("profiles", {}).get("semantic", {"enabled": False}))
    exact(cfg, ("enabled",), ("python", "model_manifest"))
    require(type(cfg["enabled"]) is bool, "invalid_semantic_profile", "Semantic enablement must be Boolean.")
    if cfg["enabled"]:
        cfg.setdefault("python", ENVIRONMENT + "/bin/python")
        cfg.setdefault("model_manifest", MODEL_MANIFEST)
        require(cfg.get("python") == ENVIRONMENT + "/bin/python" and cfg.get("model_manifest") == MODEL_MANIFEST,
                "invalid_semantic_profile", "Select the dedicated ontology semantic environment and model manifest.")
    return cfg, advanced


def setup_profile(root):
    """Separately selected package setup. This does not enable retrieval or prepare a model."""
    root = Path(root).resolve()
    target = safe_path(root, ENVIRONMENT, must_exist=False)
    lock = PACKAGE / "requirements-semantic.txt"
    require(lock.is_file(), "missing_profile_lock", "The selected semantic wheel lock is absent.")
    with operation_lock(root, BASE + "/setup.lock"):
        if not target.exists():
            subprocess.run([sys.executable, "-m", "venv", str(target)], check=True, timeout=120)
        require((target / "pyvenv.cfg").is_file(), "invalid_environment", "The selected path is not a virtual environment.")
        run = subprocess.run([str(target / "bin/python"), "-m", "pip", "install", "--require-hashes", "--only-binary=:all:",
                              "-r", str(lock)], capture_output=True, text=True, timeout=600)
        require(run.returncode == 0, "semantic_setup_failed", "Pinned semantic installation failed; inspect the explicit setup result.")
    return {"status": "installed", "profile": "ontology-semantic-v1", "environment": ENVIRONMENT,
            "requirements_sha256": sha256(lock), "model_prepared": False, "enabled_changed": False, "mutated": True}


def prepare_model(root):
    """Download only the six reviewed immutable artifacts, verifying every byte before adoption."""
    root = Path(root).resolve()
    spec = specification()
    prefix = BASE + "/models/" + spec["revision"]
    with operation_lock(root, BASE + "/setup.lock"):
        for name, expected in spec["files"].items():
            require("/" not in name and name not in {".", ".."}, "invalid_model_file", "Model files must be the pinned flat inventory.")
            relative = prefix + "/" + name
            target = safe_path(root, relative, must_exist=False)
            if target.exists():
                require(sha256(read_bytes(target, max_bytes=100_000_000)) == expected["sha256"],
                        "model_conflict", "Existing model bytes differ from the selected immutable model.", path=relative)
                continue
            url = "https://huggingface.co/" + spec["repository"] + "/resolve/" + spec["revision"] + "/" + name
            with urllib.request.urlopen(url, timeout=120) as response:
                data = response.read(expected["size"] + 1)
            require(len(data) == expected["size"] and sha256(data) == expected["sha256"],
                    "model_hash_mismatch", "Downloaded model bytes failed the reviewed size/hash check.", path=relative)
            # The core writer deliberately limits ordinary records to 2 MB; model files use
            # exclusive creation, retained checked bytes and a separate 100 MB bound.
            target.parent.mkdir(parents=True, exist_ok=True)
            safe_path(root, relative, must_exist=False)
            with target.open("xb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            require(sha256(read_bytes(target, max_bytes=100_000_000)) == expected["sha256"],
                    "model_hash_mismatch", "Reopened model bytes differ.", path=relative)
        manifest = {"schema_version": 1, "profile_sha256": sha256(PACKAGE / "profiles/semantic-v1.json"),
                    "model": spec["model"], "repository": spec["repository"], "revision": spec["revision"],
                    "dimension": spec["dimension"], "directory": prefix, "files": spec["files"]}
        path = safe_path(root, MODEL_MANIFEST, must_exist=False)
        if path.exists():
            require(read_json(path) == manifest, "model_conflict", "A different model is already selected; use a reviewed profile upgrade.")
        else:
            atomic_write(root, MODEL_MANIFEST, canonical_bytes(manifest), None)
    return {"status": "prepared", "manifest": MODEL_MANIFEST, "sha256": sha256(canonical_bytes(manifest)),
            "model": spec["model"], "revision": spec["revision"], "enabled_changed": False, "mutated": True}


def model_context(root):
    spec = specification()
    manifest = read_json(safe_path(root, MODEL_MANIFEST))
    expected = {"schema_version": 1, "profile_sha256": sha256(PACKAGE / "profiles/semantic-v1.json"),
                "model": spec["model"], "repository": spec["repository"], "revision": spec["revision"],
                "dimension": spec["dimension"], "directory": BASE + "/models/" + spec["revision"], "files": spec["files"]}
    require(manifest == expected, "model_mismatch", "Prepared model does not match the selected semantic profile.")
    for name, expected_file in manifest["files"].items():
        data = read_bytes(safe_path(root, manifest["directory"] + "/" + name), max_bytes=100_000_000)
        require(len(data) == expected_file["size"] and sha256(data) == expected_file["sha256"],
                "model_mismatch", "Prepared model artifact changed.", path=name)
    return manifest


def _embed(root, texts, *, query=False, timeout=60):
    require(isinstance(texts, list) and 0 < len(texts) <= MAX_ITEMS and
            all(isinstance(t, str) and len(t) <= MAX_TEXT for t in texts),
            "embedding_limit", "Embedding text exceeds the bounded ontology corpus.")
    model = model_context(root)
    executable = Path(root) / ENVIRONMENT / "bin/python"
    # Venv Python is normally a symlink to the selected base interpreter. Its parent
    # environment is confined; arbitrary executables cannot be selected in configuration.
    safe_path(root, ENVIRONMENT)
    require((Path(root) / ENVIRONMENT / "pyvenv.cfg").is_file() and executable.is_file(),
            "semantic_backend_unavailable", "Explicitly install the ontology semantic profile first.")
    worker = PACKAGE / "scripts/ontology_semantic_worker.py"
    payload = {"texts": texts, "query": query, "model_directory": str(safe_path(root, model["directory"])),
               "model": model["model"], "dimension": model["dimension"], "packages": backend_versions(root)}
    env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "LANG") if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
               TOKENIZERS_PARALLELISM="false", HF_HUB_DISABLE_TELEMETRY="1")
    try:
        run = subprocess.run([str(executable), "-B", "-I", str(worker)], input=json.dumps(payload),
                             capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired as exc:
        raise OntologyError("semantic_timeout", "The bounded offline embedding run timed out; no index was replaced.") from exc
    try:
        result = json.loads(run.stdout)
    except (ValueError, UnicodeError) as exc:
        raise OntologyError("semantic_backend_failed", "The offline embedding worker returned no valid result.") from exc
    require(run.returncode == 0 and result.get("status") == "ok", "semantic_backend_failed",
            result.get("diagnostic", "The offline model failed."))
    require(result.get("packages") == payload["packages"] and result.get("python", "").startswith("3.12."),
            "semantic_version_mismatch", "The semantic runtime differs from its Python and complete package lock.")
    vectors = result.get("vectors")
    require(isinstance(vectors, list) and len(vectors) == len(texts) and
            all(isinstance(v, list) and len(v) == model["dimension"] and
                all(isinstance(x, (int, float)) and math.isfinite(x) for x in v) for v in vectors),
            "invalid_embedding_result", "The worker returned malformed vectors.")
    return vectors, {"model": model, "packages": result["packages"], "python": result["python"], "worker_sha256": sha256(worker),
                     "requirements_sha256": sha256(PACKAGE / "requirements-semantic.txt"),
                     "truncated_inputs": result["truncated_inputs"], "offline": True}


def _corpus(p, documents=()):
    require(isinstance(documents, (list, tuple)) and len(set(documents)) == len(documents),
            "invalid_semantic_sources", "Select distinct allowed documentation paths.")
    require(set(documents) <= set(p.config["source_allowlist"]), "excluded_source", "Semantic documents must be explicitly permitted ontology sources.")
    texts = {path: read_bytes(safe_path(p.root, path)).decode("utf-8") for path in documents}
    rows = []
    for r in sorted(p.records, key=lambda value: value["@id"]):
        if r["kind"] not in {"concept", "instance", "predicate"} or r["lifecycle"] != "approved" or r["fact_kind"] != "asserted":
            continue
        require(all(source_status(p, s)["status"] == "current" for s in r["sources"]),
                "stale_source", "Semantic builds require current approved source evidence.", record_id=r["@id"])
        parts = [r["label"], *r.get("aliases", []), r["definition"], r.get("scope_note", "")]
        parts.extend(texts[s["path"]] for s in r["sources"] if s["path"] in texts)
        text = "\n".join(parts)
        rows.append({"id": r["@id"], "text": text[:MAX_TEXT], "text_truncated": len(text) > MAX_TEXT,
                     "record_sha256": sha256(canonical_bytes(r)), "sources": copy.deepcopy(r["sources"])})
    require(rows and len(rows) <= MAX_ITEMS, "embedding_limit", "Select a nonempty corpus of at most 2,000 approved definitions.")
    return rows, {path: sha256(text.encode()) for path, text in texts.items()}


def build_index(root, *, documents=()):
    cfg, _ = profile(root)
    require(cfg["enabled"], "semantic_disabled", "Explicitly enable the prepared semantic profile before building.")
    p = load_project(root)
    rows, selected_docs = _corpus(p, documents)
    before = p.context()
    started = time.monotonic()
    vectors, runtime = _embed(p.root, [row["text"] for row in rows], timeout=120)
    value = {"schema_version": 1, "kind": "ontology-semantic-index", "version": VERSION,
             "project_id": p.project_id, "context": before,
             "companion_sha256": sha256(safe_path(root, "ontology-advanced.yaml")),
             "documents": selected_docs, "rows": rows, "vectors": vectors, "runtime": runtime,
             "semantics": "Similarity is a retrieval hint, never equivalence, approval or authority."}
    require(len(canonical_bytes(value)) <= 16_000_000, "embedding_limit", "The index exceeds 16 MB.")
    with operation_lock(root, BASE + "/index.lock"):
        require(load_project(root).context() == before and all(sha256(safe_path(root, path)) == digest for path, digest in selected_docs.items()),
                "source_changed", "Inputs changed while embedding; build again from the new reviewed state.")
        target = safe_path(root, INDEX, must_exist=False)
        # Keep the same exclusive expected-byte core transaction for bounded indexes.
        require(len(canonical_bytes(value)) <= 2_000_000, "embedding_limit", "Narrow this initial matrix to the 2 MB atomic-index bound.")
        atomic_write(root, INDEX, canonical_bytes(value), sha256(target) if target.exists() else None)
    return {"status": "built", "path": INDEX, "sha256": sha256(canonical_bytes(value)), "records": len(rows),
            "runtime": runtime, "elapsed_seconds": time.monotonic() - started, "mutated": True}


def load_index(p):
    value = read_json(safe_path(p.root, INDEX))
    require(value.get("schema_version") == 1 and value.get("kind") == "ontology-semantic-index" and
            value.get("project_id") == p.project_id, "invalid_semantic_index", "The semantic index has an unsupported identity or version.")
    require(value.get("context") == p.context() and value.get("companion_sha256") == sha256(safe_path(p.root, "ontology-advanced.yaml")),
            "stale_semantic_index", "Ontology/profile inputs changed; explicitly rebuild the semantic index.")
    require(all(sha256(safe_path(p.root, path)) == digest for path, digest in value.get("documents", {}).items()),
            "stale_semantic_index", "Selected documentation changed; explicitly rebuild the semantic index.")
    require(value.get("runtime", {}).get("model") == model_context(p.root) and
            value["runtime"].get("worker_sha256") == sha256(PACKAGE / "scripts/ontology_semantic_worker.py") and
            value["runtime"].get("requirements_sha256") == sha256(PACKAGE / "requirements-semantic.txt") and
            value["runtime"].get("packages") == backend_versions(p.root),
            "model_mismatch", "The index's model or runtime worker changed.")
    expected_rows, _ = _corpus(p, tuple(value["documents"]))
    require(value.get("rows") == expected_rows and isinstance(value.get("vectors"), list) and
            len(value["vectors"]) == len(expected_rows), "invalid_semantic_index", "The indexed corpus differs from the exact permitted definitions.")
    dim = value["runtime"]["model"]["dimension"]
    require(all(isinstance(v, list) and len(v) == dim and all(type(x) in (float, int) and math.isfinite(x) for x in v)
                for v in value["vectors"]), "invalid_semantic_index", "Malformed vector matrix.")
    return value


def health(root):
    try:
        cfg, _ = profile(root)
        if not cfg["enabled"]:
            return {"status": "disabled", "implemented": True, "mutated": False}
        p = load_project(root)
        value = load_index(p)
        return {"status": "ready", "implemented": True, "enabled": True, "index": INDEX,
                "index_sha256": sha256(safe_path(root, INDEX)), "records": len(value["rows"]),
                "model": value["runtime"]["model"], "mutated": False}
    except OntologyError as exc:
        return {"status": "unavailable", "implemented": True, "diagnostic": exc.as_dict(), "mutated": False}


def capture_inputs(p, query, identifiers):
    """Explicit packet input selection; subsequent frozen reads use this matrix only."""
    from ontology_retrieval import query_text
    require(not hasattr(p, "frozen_packet"), "frozen_semantic_scope", "A frozen reader cannot expand semantic inputs.")
    query = query_text(query)
    cfg, _ = profile(p.root)
    require(cfg["enabled"], "semantic_disabled", "Enable the prepared semantic profile before selecting packet inputs.")
    index = load_index(p)
    selected = set(identifiers)
    require(selected <= set(p.by_id), "unknown_concept", "Semantic packet selection requires current approved IDs.")
    vectors, runtime = _embed(p.root, [query], query=True)
    require(runtime["packages"] == index["runtime"]["packages"], "semantic_version_mismatch", "The model runtime changed after index build.")
    return {"query_vector": vectors[0], "matrix": [{"id": row["id"], "vector": vector, "text": row["text"],
              "record_sha256": row["record_sha256"], "sources": row["sources"]}
              for row, vector in zip(index["rows"], index["vectors"]) if row["id"] in selected],
            "model": runtime["model"], "packages": runtime["packages"], "documents": index["documents"],
            "index_sha256": sha256(safe_path(p.root, INDEX)), "threshold": 0.45}


def search(value, query, *, limit=None, max_bytes=None, kinds=None):
    from ontology_retrieval import envelope, explain, limits, project, query_text, ranked
    p = project(value)
    query = query_text(query)
    bound = limits(p, limit, max_bytes)
    lexical = ranked(p, query, kinds=kinds or {"concept", "instance", "predicate"})
    if lexical and lexical[0][0][0] < 3:
        return envelope(p, "semantic-search", query, [explain(p, r, m[2], m[1]) for m, r in lexical], bound,
                        semantic={"status": "exact_resolution_precedes_semantic", "used": False})
    require(not hasattr(p, "frozen_packet"), "frozen_semantic_scope", "Frozen context requires frozen semantic inputs; live embedding/index reads are forbidden.")
    cfg, _ = profile(p.root)
    if not cfg["enabled"]:
        return envelope(p, "semantic-search", query, [explain(p, r, m[2], m[1]) for m, r in lexical], bound,
                        status="ok" if lexical else "no_match", semantic={"status": "disabled", "used": False})
    index = load_index(p)
    vectors, runtime = _embed(p.root, [query], query=True)
    require(runtime["packages"] == index["runtime"]["packages"], "semantic_version_mismatch", "The embedding runtime changed since index build.")
    q = vectors[0]
    scored = []
    for row, vector in zip(index["rows"], index["vectors"]):
        if kinds and p.by_id[row["id"]]["kind"] not in kinds:
            continue
        denom = math.sqrt(sum(x*x for x in q) * sum(x*x for x in vector))
        score = sum(x*y for x, y in zip(q, vector))/denom if denom else 0.0
        if score >= 0.45:
            scored.append((score, row["id"]))
    scored.sort(key=lambda x: (-x[0], x[1]))
    results = [explain(p, p.by_id[i], "semantic_similarity", round(score, 6)) for score, i in scored]
    for row in results:
        row["semantic_uncertainty"] = "Similarity suggests relevance; it establishes neither equivalence nor authority."
    return envelope(p, "semantic-search", query, results, bound, status="ok" if results else "no_match",
                    semantic={"status": "current", "used": True, "index_sha256": sha256(safe_path(p.root, INDEX)),
                              "model_revision": runtime["model"]["revision"], "packages": runtime["packages"],
                              "threshold": 0.45, "offline": True})
