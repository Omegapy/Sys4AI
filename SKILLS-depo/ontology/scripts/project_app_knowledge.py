"""Lazy Knowledge capability and search-first permitted memory reading."""
from __future__ import annotations

from project_app_sources import AppError, json_bytes, plain, read_bytes
from project_app_work import compatibility, owner_read


def configured(reader, owner):
    path = "ontology.yaml" if owner == "knowledge" else "memory.yaml"
    try:
        value = json_bytes(read_bytes(reader.root, path, 65536))
    except AppError:
        return "unavailable"
    if not isinstance(value, dict) or value.get("project", {}).get("id") != reader.project_id or value.get("project", {}).get("root") != ".":
        return "incompatible"
    if value.get("enabled") is False:
        return "disabled"
    return "configured"


def knowledge(reader, params):
    state = configured(reader, "knowledge")
    return {"status": "ready" if state == "configured" else "disabled" if state == "disabled" else "unavailable",
            "availability": state, "guidance": "Open Project knowledge to read terms, documented processes, the relationship list and map through the existing Explorer reader.",
            "reading": "Existing Explorer semantics and source permissions apply.", "runtime": "Not checked until Project knowledge is opened."}


def memory(reader, params):
    state = configured(reader, "memory")
    if state != "configured":
        return {"status": "disabled" if state == "disabled" else "unavailable", "items": [], "guidance": "Lessons and decisions needs a compatible project memory configuration."}
    compatibility(reader, "memory")
    if params.get("source_id"):
        record = reader.handles.get(params["source_id"])
        if record is None or record["owner"] != "memory":
            raise AppError("source_unavailable")
        result = memory_source(reader, record)
        return {"status": result["status"], "items": [], "item": result}
    query = params.get("query", "")
    if not query:
        return {"status": "ready", "items": [], "guidance": "Search a topic or decision to find permitted saved findings. This view does not list the entire memory corpus."}
    value = owner_read(reader, "memory", "search", query)
    items = []
    for row in value.get("results", [])[:15]:
        # This view is specifically saved findings. Document hits remain part of
        # unified lexical search through the same owner, never a widened corpus.
        if row.get("kind") != "memory" and not params.get("include_documents"):
            continue
        path = row.get("path")
        if not isinstance(path, str):
            continue
        title = plain(row.get("heading", row.get("record_id", path)), 180)
        ref = reader.reference("memory", path, title, path=path, sha256=row.get("sha256"), status="ready", query=query, kind=row.get("kind"))
        items.append({"id": plain(row.get("record_id", row.get("source_identity", path)), 300), "type": "memory" if row.get("kind") == "memory" else "document",
                      "owner": "memory", "title": title, "excerpt": plain(row.get("excerpt", ""), 1500),
                      "status": plain(row.get("state", "current"), 80), "claim": plain(row.get("claim", {}).get("summary", ""), 1500) if isinstance(row.get("claim"), dict) else plain(row.get("claim", ""), 1500),
                      "verified_current": row.get("verified_current") is True, "source": ref})
    return {"status": "partial" if value.get("limitations") else "ready", "items": items,
            "coverage": "Bounded lexical results from the memory owner's permitted corpus.",
            "guidance": "No matching saved findings in the returned page." if not items else "Saved findings are historical evidence; inspect applicability and current sources before acting.",
            "issues": ["memory_coverage_limited"] if value.get("limitations") else []}


def memory_source(reader, record):
    if configured(reader, "memory") != "configured":
        raise AppError("source_unavailable")
    result = owner_read(reader, "memory", "search", record["query"])
    match = next((r for r in result.get("results", []) if r.get("path") == record["path"]), None)
    if match is None:
        raise AppError("source_unavailable")
    if match.get("kind") != "memory":
        return {"status": "partial", "title": plain(match.get("heading", record["path"]), 180), "path": record["path"],
                "sha256": match.get("sha256"), "text": plain(match.get("excerpt", ""), 1500), "truncated": True,
                "guidance": "The memory owner supports a bounded excerpt for this document, not a full source read."}
    value = owner_read(reader, "memory", "read", record["path"])
    meta = value.get("metadata", {})
    if meta.get("project_id") != reader.project_id or meta.get("state") != "active" or value.get("sha256") != match.get("sha256"):
        raise AppError("source_unavailable")
    public = {key: plain(meta.get(key, ""), 2000) for key in ("id", "title", "type", "state", "confidence", "created", "modified")}
    public["claim"] = {key: plain(meta.get("claim", {}).get(key, ""), 2000) for key in ("level", "summary")}
    public["applicability"] = [plain(x, 1000) for x in meta.get("applicability", [])[:10] if isinstance(x, str)]
    public["limitations"] = [plain(x, 1000) for x in meta.get("limitations", [])[:10] if isinstance(x, str)]
    public["lifecycle"] = {k: plain(v, 1000) if isinstance(v, str) else v if v is None else [plain(x, 100) for x in v[:20] if isinstance(x, str)] if isinstance(v, list) else "Not recorded" for k, v in meta.get("lifecycle", {}).items() if k in ("supersedes", "superseded_by", "reason", "changed_at")}
    evidence = {"verified_current": value.get("evidence", {}).get("verified_current") is True,
                "sources": [{k: plain(row[k], 1000) for k in ("path", "sha256", "locator", "relationship") if isinstance(row.get(k), str)} for row in meta.get("sources", [])[:15] if isinstance(row, dict)]}
    body = value.get("body", "")
    return {"status": "ready", "title": plain(meta.get("title", ""), 180), "path": record["path"], "sha256": value.get("sha256"),
            "text": plain(body, 20000), "truncated": len(body) > 20000, "metadata": public, "evidence": evidence}
