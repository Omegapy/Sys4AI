"""Deterministic project retrieval with optional guarded semantic ranking."""
import re
from pathlib import Path

from memory_core import MemoryError, load_config, load_records
from memory_paths import iter_corpus, safe_read_bytes
from memory_normalization import normalize_document, cache_diagnostic, digest


def collect_documents(root, config=None, historical=False):
    """Return current permitted bytes; this function never builds an index."""
    from memory_core import reject_sensitive
    config = config or load_config(root)
    documents, limitations = [], []
    for record in load_records(root, config=config, historical=historical):
        meta = record["metadata"]
        doc = {"kind": "memory", "path": record["path"], "sha256": record["sha256"],
               "source_identity": meta["id"], "metadata": meta,
               "segments": [{"text": meta["title"] + "\n" + record["body"],
                             "heading": meta["title"], "locator": record["path"]}],
               "limitations": meta["limitations"], "diagnostics": record["diagnostics"], "evidence": record["evidence"]}
        reject_sensitive(record["body"])
        documents.append(doc)
    for source in iter_corpus(root, config):
        rel = Path(source).relative_to(Path(root)).as_posix() if Path(source).is_absolute() else str(source)
        try:
            doc = normalize_document(root, rel, config)
            # Screen the complete source representation before exposing excerpts.
            reject_sensitive("\n".join(s["text"] for s in doc["segments"]))
            stale = cache_diagnostic(root, config, rel, doc["sha256"], doc.get("extractor"))
            if stale:
                doc["limitations"].append(stale)
            documents.append(doc)
            limitations.extend(f"{rel}: {item}" for item in doc["limitations"])
        except MemoryError as error:
            limitations.append(f"Source excluded or unavailable ({error.code}).")
    return documents, sorted(set(limitations))


def lexical_score(text, query):
    text, query = text.casefold(), query.casefold()
    terms = sorted(set(re.findall(r"[\w]+(?:[./:_-][\w]+)*", query)))
    if not terms:
        return 0
    phrase = text.count(query)
    hits = sum(min(text.count(term), 20) for term in terms)
    coverage = sum(term in text for term in terms)
    return phrase * 100 + coverage * 10 + hits


def _excerpt(text, query, length=700):
    needle = query.casefold()
    pos = text.casefold().find(needle)
    if pos < 0:
        terms = re.findall(r"\w+", needle)
        found = [text.casefold().find(t) for t in terms if t in text.casefold()]
        pos = min(found) if found else 0
    start = max(0, pos - 100)
    return ("…" if start else "") + text[start:start + length] + ("…" if len(text) > start + length else "")


def rank_documents(documents, query, limit, ranking=None):
    """One result per known evidence identity, retaining all representation paths."""
    ranked = []
    use_backend = ranking is not None
    ranking = {} if ranking is None else ranking
    for doc in documents:
        segments = doc["segments"]
        if not segments:
            continue
        best = max(segments, key=lambda s: lexical_score(s["text"], query))
        score = lexical_score(best["text"] + "\n" + doc["path"], query)
        semantic = ranking.get((doc["path"], doc["sha256"]))
        if semantic is not None:
            score = semantic
        elif use_backend:
            continue
        if score <= 0 and semantic is None:
            continue
        result = {"kind": doc["kind"], "path": doc["path"], "sha256": doc["sha256"],
                  "source_identity": doc["source_identity"], "locator": best["locator"],
                  "heading": best["heading"], "excerpt": _excerpt(best["text"], query),
                  "score": score, "limitations": list(doc["limitations"]),
                  "diagnostics": doc.get("diagnostics", []),
                  "authority": "Source data; inspect current governing sources before acting."}
        for field in ("labels", "references", "bibliography_keys", "environments", "page", "line"):
            if field in best:
                result[field] = best[field]
        if doc["kind"] == "memory":
            result.update({"record_id": doc["metadata"]["id"], "state": doc["metadata"]["state"],
                           "sources": doc["metadata"]["sources"], "claim": doc["metadata"]["claim"],
                           "confidence": doc["metadata"]["confidence"], "evidence": doc.get("evidence"),
                           "verified_current": doc.get("evidence", {}).get("verified_current", False)})
        ranked.append(result)
    ranked.sort(key=lambda r: (-r["score"], r["source_identity"], r["path"], r["locator"]))
    unique = {}
    for result in ranked:
        identity = result["source_identity"]
        if identity not in unique:
            result["representations"] = []
            unique[identity] = result
        unique[identity]["representations"].append({"path": result["path"], "sha256": result["sha256"], "locator": result["locator"]})
    return list(unique.values())[:limit]


def search(root, query, config=None, historical=False, packet=None, limit=None, mode="auto"):
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise MemoryError("invalid_query", "Supply a nonempty query of at most 4096 characters.")
    if mode not in {"auto", "lexical", "hybrid"}:
        raise MemoryError("invalid_mode", "Supported modes are auto, lexical and hybrid.")
    if packet is not None:
        from memory_packet import search_packet
        return search_packet(root, packet, query, limit=limit)
    config = config or load_config(root, optional=True)
    if config is None:
        return {"status": "unconfigured", "mode": "lexical", "mutated": False,
                "results": [], "limitations": ["No project memory configuration; inspect permitted source files directly."]}
    if mode == "auto":
        mode = config["retrieval"]["mode"]
    limit = config["retrieval"]["max_results"] if limit is None else limit
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 200:
        raise MemoryError("invalid_limit", "Result limit must be between 1 and 200.")
    docs, limitations = collect_documents(root, config, historical=historical)
    ranking = None
    actual_mode = "lexical"
    if mode != "lexical" and not historical:
        if config["backend"]["enabled"] and config["backend"]["semantic_enabled"]:
            from basic_memory_adapter import query as backend_query
            response = backend_query(root, query, config, mode="hybrid", limit=limit, packet=None)
            limitations.extend(response.get("limitations", []))
            if response.get("available"):
                # Recheck every locator/digest against current allowed canonical bytes.
                current = {(d["path"], d["sha256"]): d for d in docs}
                ranking = {(r["path"], r["sha256"]): r["score"] for r in response.get("results", [])
                           if (r.get("path"), r.get("sha256")) in current}
                actual_mode = response["mode"]
            else:
                limitations.append("Semantic backend unavailable or uncertified; using lexical retrieval without maintenance.")
        else:
            limitations.append("Semantic backend disabled; results use deterministic lexical retrieval.")
    # Fail if a source changed while ranking, rather than returning a stale version as current.
    current_docs = []
    for doc in docs:
        if digest(safe_read_bytes(root, doc["path"])) == doc["sha256"]:
            current_docs.append(doc)
        else:
            limitations.append("A source changed during retrieval and was excluded; inspect it again.")
    docs = current_docs
    results = rank_documents(docs, query, limit, ranking=ranking)
    return {"status": "ok" if results else "no_match" if docs else "empty", "mode": actual_mode,
            "mutated": False, "project_id": config["project"]["id"], "results": results,
            "limitations": sorted(set(limitations)), "historical": historical}
