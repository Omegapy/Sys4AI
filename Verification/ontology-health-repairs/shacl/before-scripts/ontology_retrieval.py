"""Deterministic vocabulary retrieval from canonical or explicitly frozen inputs."""
import copy
import re

from ontology_core import OntologyError, canonical_bytes, load_project, source_status


def project(value):
    return value if hasattr(value, "by_id") else load_project(value)


def limits(p, limit=None, max_bytes=None, hops=None):
    settings = p.config["retrieval"]
    result = {"limit": settings["default_limit"] if limit is None else limit,
              "max_bytes": settings["max_context_bytes"] if max_bytes is None else max_bytes,
              "hops": settings["default_hops"] if hops is None else hops}
    for key, low, high in (("limit", 1, min(100, settings["max_limit"])),
                           ("hops", 0, min(8, settings["max_hops"])),
                           ("max_bytes", 1024, min(32000, settings["max_context_bytes"]))):
        if type(result[key]) is not int or not low <= result[key] <= high:
            raise OntologyError("invalid_limit", f"{key} must be between {low} and {high}.")
    return result


def normalize(value):
    return " ".join(value.casefold().split())


def tokens(value):
    return set(re.findall(r"[\w]+", re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value).casefold()))


def query_text(query):
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise OntologyError("invalid_query", "Supply a nonempty query of at most 4096 characters.")
    return query.strip()


def match(record, query):
    q = normalize(query)
    if record["@id"] == query:
        return 0, 1, "stable_id"
    if normalize(record["label"]) == q:
        return 1, 1, "preferred_label"
    if q in [normalize(a) for a in record.get("aliases", [])]:
        return 2, 1, "alias"
    words = tokens(query)
    vocabulary = record["label"] + " " + " ".join(record.get("aliases", []))
    text = vocabulary + " " + record["definition"] + " " + record.get("scope_note", "")
    overlap = len(words & tokens(text))
    score = overlap * 10 + len(words & tokens(vocabulary)) * 5 + (20 if q in normalize(text) else 0)
    return (3, score, "lexical") if overlap else None


def ranked(p, query, *, kinds=None):
    query = query_text(query)
    results = []
    for record in p.records:
        if kinds is not None and record["kind"] not in kinds:
            continue
        reason = match(record, query)
        if reason:
            results.append((reason, record))
    results.sort(key=lambda item: (item[0][0], -item[0][1], item[1]["@id"]))
    return results


def explain(p, record, reason="selected", score=None):
    result = copy.deepcopy(record)
    result.update(source_type="ontology", match_reason=reason,
                  canonical_location=p.locations.get(record["@id"]),
                  module_version=next((m.get("version") for m in p.modules if m.get("id", m.get("module_id")) == record["module"]), None))
    bindings = [b for b in p.records if b["kind"] == "binding" and b["entity"] == record["@id"]]
    result["bindings"] = copy.deepcopy(bindings)
    sources = {canonical_bytes(s): s for b in [record, *bindings] for s in b.get("sources", [])}
    result["source_status"] = [source_status(p, sources[key]) for key in sorted(sources)]
    states = {s["status"] for s in result["source_status"]}
    result["freshness"] = "unavailable" if "unavailable" in states else "stale" if "stale" in states else "current"
    if score is not None:
        result["match_score"] = score
    result["relationships"] = [copy.deepcopy(r) for r in p.relations
                               if record["@id"] in (r["subject"], r["object"])]
    return result


def envelope(p, operation, query, results, bound, *, status="ok", truncated=False, **extra):
    context = p.context()
    # The full snapshot is reproducible by its digest; return exact versions for
    # the selected records rather than duplicating every unrelated source.
    compact = {k: copy.deepcopy(v) for k, v in context.items()
               if k in {"project_id", "profile_version", "generator_version", "snapshot_sha256", "config_sha256", "modules", "configuration"}}
    compact["config_sha256"] = context.get("inputs", {}).get("ontology.yaml")
    result = {"operation": operation, "query": query, "project_id": p.project_id,
              "status": status, "results": results[:bound["limit"]],
              "context": compact, "diagnostics": copy.deepcopy(p.diagnostics),
              "limits": bound, "truncation": {"truncated": truncated or len(results) > bound["limit"],
                 "available_results": len(results), "returned_results": min(len(results), bound["limit"])},
              "mutated": False,
              "authority": "Semantic source data; current user, project, role, skill and Task authority control action.", **extra}
    while len(canonical_bytes(result)) + 256 > bound["max_bytes"] and result["results"]:
        result["results"].pop()
        result["truncation"]["truncated"] = True
    if len(canonical_bytes(result)) + 256 > bound["max_bytes"]:
        result["diagnostics"] = [{"code": "diagnostics_truncated", "message": "Run health to inspect complete diagnostics."}]
        result["context"] = {k: v for k, v in compact.items() if k in {"project_id", "snapshot_sha256", "config_sha256"}}
        result["truncation"]["truncated"] = True
    if len(canonical_bytes(result)) > bound["max_bytes"]:
        raise OntologyError("context_too_large", "Response metadata exceeds the requested byte bound; use a larger bound.")
    result["truncation"]["returned_results"] = len(result["results"])
    return result


def search(value, query, *, limit=None, max_bytes=None, kinds=None, semantic=True):
    p = project(value)
    bound = limits(p, limit, max_bytes)
    rows = ranked(p, query, kinds=kinds or {"concept", "instance", "predicate"})
    results = [explain(p, r, m[2], m[1]) for m, r in rows]
    if semantic and getattr(p, "frozen_packet", {}).get("schema_version") == 2:
        from ontology_advanced_packet import frozen_search
        frozen = frozen_search(p, query, limit=limit, max_bytes=max_bytes)
        if frozen is not None:
            return frozen
    if semantic and not hasattr(p, "frozen_packet") and (not rows or rows[0][0][0] == 3):
        from ontology_semantic import profile, search as semantic_search
        try:
            cfg, _ = profile(p.root)
            if cfg["enabled"]:
                return semantic_search(p, query, limit=limit, max_bytes=max_bytes, kinds=kinds)
        except OntologyError as error:
            return envelope(p, "search", query, results, bound, status="ok" if rows else "no_match",
                            semantic={"status": "unavailable", "used": False, "diagnostic": error.as_dict()})
    return envelope(p, "search", query, results, bound, status="ok" if rows else "no_match")


def term(value, query, *, limit=None, max_bytes=None):
    p = project(value)
    bound = limits(p, limit, max_bytes)
    rows = ranked(p, query, kinds={"concept", "instance", "predicate"})
    if rows:
        best = rows[0][0][:2]
        rows = [(m, r) for m, r in rows if m[:2] == best]
    if not rows or rows[0][0][0] == 3:
        result = search(p, query, limit=limit, max_bytes=max_bytes)
        if result.get("semantic", {}).get("used"):
            result["operation"] = "term"
            result["status"] = "semantic_candidates" if result["results"] else "no_match"
            return result
    results = [explain(p, r, m[2], m[1]) for m, r in rows]
    return envelope(p, "term", query, results, bound,
                    status="ambiguous" if len(rows) > 1 else "ok" if rows else "no_match")


def read(value, identifier, *, max_bytes=None):
    p = project(value)
    query_text(identifier)
    rows = [explain(p, p.by_id[identifier], "stable_id")] if identifier in p.by_id else []
    return envelope(p, "read", identifier, rows, limits(p, 1, max_bytes), status="ok" if rows else "no_match")


def resolve_one(p, query):
    rows = ranked(p, query, kinds={"concept", "instance", "predicate"})
    if not rows:
        raise OntologyError("no_match", f"No ontology match for {query!r}.")
    best = [r for m, r in rows if m[:2] == rows[0][0][:2]]
    if len(best) != 1:
        raise OntologyError("ambiguous_term", "Ambiguous vocabulary; use a stable ID: " + ", ".join(r["@id"] for r in best))
    return best[0]


def human(result):
    lines = [f"{result.get('project_id', 'unresolved')}: {result.get('operation', 'ontology')} ({result.get('status', 'checked')})"]
    for r in result.get("results", []):
        lines.append(f"{r.get('label', r.get('record_id', r.get('path', 'evidence')))} [{r.get('@id', r.get('record_id', r.get('path', '')))}] "
                     f"({r.get('lifecycle', r.get('source_type', 'evidence'))}; {r.get('match_reason', 'selected')}; {r.get('freshness', 'see source')})")
        lines.append(r.get("definition", r.get("excerpt", "")))
        if r.get("scope_note"):
            lines.append(r["scope_note"])
        for s in r.get("source_status", r.get("sources", [])):
            lines.append(f"  Source: {s['path']} [{s['sha256']}] {s.get('locator', '')} ({s.get('status', 'recorded')})")
        for edge in r.get("relationships", []):
            lines.append(f"  {edge['subject']} --{edge['predicate']}--> {edge['object']} [{edge['fact_kind']}]")
        if r.get("kind") == "relation":
            lines.append(f"  {r['subject']} --{r['predicate']}--> {r['object']} [{r['fact_kind']}; {r.get('direction', 'canonical direction')}]")
        if r.get("sha256") and r.get("path"):
            lines.append(f"  Source: {r['path']} [{r['sha256']}] {r.get('locator', '')}")
        if r.get("discrepancy"):
            lines.append(f"  Discrepancy: {r['discrepancy']}; recorded source SHA256 {r.get('recorded_sha256')}")
        if r.get("replacement"):
            lines.append(f"  Replacement: {r['replacement']}; {r.get('deprecation_reason', '')}")
    if result.get("truncation", {}).get("truncated"):
        lines.append("Results were truncated at the declared bounds.")
    if result.get("memory"):
        lines.append("Historical evidence: " + result["memory"]["status"] + " (" + result["memory"].get("mode", "unavailable") + ")")
        lines.extend(result["memory"].get("limitations", []))
    if result.get("context", {}).get("snapshot_sha256"):
        lines.append("Input snapshot: " + result["context"]["snapshot_sha256"])
    if result.get("generated"):
        lines.extend(operation + ": " + value["status"] for operation, value in result["generated"].items())
    if result.get("structural"):
        lines.append("Structural validation: " + ("passed" if result["structural"]["valid"] else "failed"))
        lines.append("Competency validation: " + ("passed" if result["competency"]["valid"] else "failed"))
    return "\n".join(lines)
