"""Attributable source normalization; cache writes require explicit maintenance."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from memory_core import MemoryError, load_config
from memory_paths import corpus_allowed, safe_path, safe_read_bytes

VERSION = "normalization-1"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _markdown(text, path, sha256):
    headings = list(re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", text))
    starts = [(0, "Document")]
    starts.extend((h.start(), h.group(1)) for h in headings if h.start())
    if headings and headings[0].start() == 0:
        starts[0] = (0, headings[0].group(1))
    segments = []
    for i, (start, heading) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        line = text.count("\n", 0, start) + 1
        raw = text[start:end]
        if raw.strip():
            segments.append({"text": raw, "locator": f"{path}:{line}", "heading": heading, "line": line})
    return {"kind": "source", "path": path, "sha256": sha256, "source_identity": path,
            "format": "md", "extractor": "markdown-headings-1", "segments": segments, "limitations": []}


def source_identity(root, path, config):
    """Group only an explicitly documented, currently evidenced relationship."""
    selected = []
    for group in config["corpus"]["source_groups"]:
        if path not in group["paths"]:
            continue
        if not all(corpus_allowed(p, config) for p in group["paths"]):
            raise MemoryError("invalid_source_group", "Source group includes an excluded path.")
        evidence = group["evidence"]
        if not corpus_allowed(evidence["path"], config):
            raise MemoryError("invalid_source_group", "Relationship evidence must be an allowed source.")
        if digest(safe_read_bytes(root, evidence["path"])) != evidence["sha256"]:
            raise MemoryError("stale_source_group", "Relationship evidence changed; review the grouping before rebuilding.")
        for rel in group["paths"]:
            safe_path(root, rel)
        selected.append(group["id"])
    if len(selected) > 1:
        raise MemoryError("invalid_source_group", "A source belongs to more than one evidence group.")
    return selected[0] if selected else path


def normalize_document(root, path, config=None):
    config = config or load_config(root)
    path = str(path)
    if not corpus_allowed(path, config):
        raise MemoryError("excluded_source", "Source is outside the permitted corpus.")
    data = safe_read_bytes(root, path)
    sha = digest(data)
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        from memory_normalize_pdf import normalize
        doc = normalize(data, path, sha)
    else:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise MemoryError("unsupported_encoding", "Text source must be UTF-8.") from None
        if suffix == ".tex":
            from memory_normalize_tex import normalize
        elif suffix in {".html", ".htm"}:
            from memory_normalize_html import normalize
        elif suffix in {".md", ".markdown"}:
            normalize = _markdown
        else:
            raise MemoryError("unsupported_format", "Source format is not supported.")
        doc = normalize(text, path, sha)
    doc["source_identity"] = source_identity(root, path, config)
    return doc


def _cache_path(config, path):
    key = digest(path.encode("utf-8"))
    return f"{config['state']['normalized']}/{key}.json"


def cache_diagnostic(root, config, path, source_sha256, extractor=None):
    """Observe cache freshness without creating or modifying files."""
    rel = _cache_path(config, path)
    target = safe_path(root, rel, must_exist=False)
    if not target.exists():
        return None
    try:
        cached = json.loads(safe_read_bytes(root, rel))
        if (cached.get("normalization_version") != VERSION or cached.get("document", {}).get("sha256") != source_sha256
                or (extractor is not None and cached.get("document", {}).get("extractor") != extractor)):
            return "Stored normalization is stale; this result was extracted from the current source without updating the cache."
    except (ValueError, TypeError):
        return "Stored normalization is invalid; current source extraction was used without cache repair."
    return None


def build_normalized(root, config, output_dir=None):
    """Caller must hold the memory maintenance lock and validate its exact grant.

    Publish only our classified source products; never remove unknown files.
    """
    from memory_search import collect_documents
    root = Path(root)
    expected = config["state"]["normalized"]
    if output_dir is not None and str(output_dir) != expected:
        raise MemoryError("unsafe_maintenance", "Normalization output differs from the declared state path.")
    docs, limitations = collect_documents(root, config)
    target = safe_path(root, expected, must_exist=False, kind="dir")
    target.mkdir(parents=True, exist_ok=True)
    safe_path(root, expected, kind="dir")
    products = []
    for doc in docs:
        if doc["kind"] != "source":
            continue
        if digest(safe_read_bytes(root, doc["path"])) != doc["sha256"]:
            raise MemoryError("source_changed", "Source changed during normalization; retry after inspection.")
        rel = _cache_path(config, doc["path"])
        payload = {"schema_version": 1, "normalization_version": VERSION, "document": doc}
        data = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        destination = safe_path(root, rel, must_exist=False)
        with tempfile.NamedTemporaryFile(dir=target, delete=False, prefix=".normalize-", suffix=".tmp") as tmp:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
            temporary = tmp.name
        try:
            safe_path(root, rel, must_exist=False)
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        products.append({"path": rel, "sha256": digest(data), "source_path": doc["path"], "source_sha256": doc["sha256"]})
    return {"status": "normalized", "products": products, "limitations": limitations}
