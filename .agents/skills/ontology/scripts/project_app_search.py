"""Ephemeral typed lexical aggregation within each source owner's scope."""
from __future__ import annotations

import re
from project_app_sources import AppError, plain, read_bytes
from project_app_work import catalog
from project_app_knowledge import configured, memory


def search(reader, query):
    if not isinstance(query, str) or not query.strip() or len(query) > 300:
        raise AppError("invalid_request")
    terms = set(re.findall(r"\w+", query.casefold()))
    if not terms:
        raise AppError("invalid_request")
    def matches(text):
        return all(term in text.casefold() for term in terms)
    items, coverage = [], []
    try:
        docs = reader.documents(reader.config())
        failed = False
        for row in docs:
            if row["status"] != "ready":
                failed = True
                continue
            text = read_bytes(reader.root, row["path"]).decode("utf-8")
            if matches(row["title"] + "\n" + row["path"] + "\n" + text):
                positions = [text.casefold().find(term) for term in terms if term in text.casefold()]
                start = max(0, min(positions, default=0) - 80)
                items.append({"id": row["path"], "owner": "documents", "type": "document", "title": row["title"], "excerpt": plain(text[start:start+700], 700), "source": row})
        coverage.append({"owner": "documents", "status": "partial" if failed else "ready"})
    except (AppError, UnicodeError):
        coverage.append({"owner": "documents", "status": "unavailable"})
    work = catalog(reader)
    coverage.extend({"owner": row["owner"], "status": row["status"]} for row in work["owners"])
    for row in work["items"]:
        if matches("\n".join(str(row.get(k, "")) for k in ("id", "title", "summary", "status", "next_step"))):
            items.append({**row, "owner": row["type"], "excerpt": row["summary"]})
    try:
        result = memory(reader, {"query": query, "include_documents": True})
        items.extend(result.get("items", []))
        coverage.append({"owner": "memory", "status": result["status"]})
    except AppError:
        coverage.append({"owner": "memory", "status": "unavailable"})
    if configured(reader, "knowledge") == "configured" and callable(getattr(reader, "knowledge_search", None)):
        try:
            result = reader.knowledge_search(query)
            if result.get("status") not in ("ok", "partial", "ready", "ambiguous", "truncated", "incomplete", "no_match"):
                raise AppError("knowledge_unavailable")
            for row in result.get("data", {}).get("items", [])[:15]:
                entry = row.get("entry", row)
                if row.get("kind") == "detail_required":
                    continue
                items.append({"id": entry["id"], "owner": "knowledge", "type": "knowledge", "title": plain(entry.get("label", entry["id"]), 180),
                              "excerpt": plain(entry.get("definition_excerpt", entry.get("definition", entry.get("summary", ""))), 700), "knowledge_id": entry["id"],
                              "fact_kind": entry.get("fact_kind"), "lifecycle": entry.get("lifecycle"), "source": None})
            coverage.append({"owner": "knowledge", "status": "ready" if result.get("coverage", {}).get("complete") else "partial"})
        except (AppError, ValueError, KeyError, TypeError):
            coverage.append({"owner": "knowledge", "status": "unavailable"})
    else:
        coverage.append({"owner": "knowledge", "status": "unavailable"})
    items = sorted(items, key=lambda row: (row["type"], row["title"].casefold(), row["id"]))
    partial = any(row["status"] != "ready" for row in coverage) or len(items) > 50
    return {"status": "partial" if partial else "ready", "query": query, "items": items[:50], "coverage": coverage,
            "guidance": "No matches in the supported returned pages." if not items else "Lexical matches from supported owners. Coverage lists unavailable or partial modules."}
