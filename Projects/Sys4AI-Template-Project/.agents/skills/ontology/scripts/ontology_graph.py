"""Bounded directional traversal with explicit edge classification and provenance."""
from collections import deque

from ontology_core import OntologyError
from ontology_retrieval import envelope, explain, limits, project, resolve_one


def edges(p, node, direction, predicates):
    if direction not in {"incoming", "outgoing", "both"}:
        raise OntologyError("invalid_direction", "Direction must be incoming, outgoing or both.")
    for r in p.relations:
        if predicates and r["predicate"] not in predicates:
            continue
        if direction in {"outgoing", "both"} and r["subject"] == node:
            yield r, r["object"], "outgoing"
        if direction in {"incoming", "both"} and r["object"] == node and r["subject"] != node:
            yield r, r["subject"], "incoming"


def selected_predicates(p, predicates):
    selected = set()
    for query in predicates or ():
        item = resolve_one(p, query)
        if item["kind"] != "predicate":
            raise OntologyError("invalid_predicate", "Traversal filters must resolve to relationship predicates.", record_id=item["@id"])
        selected.add(item["@id"])
    return selected


def neighbors(value, query, *, direction="both", predicates=(), hops=None, limit=None, max_bytes=None):
    p = project(value)
    bound = limits(p, limit, max_bytes, hops)
    start = resolve_one(p, query)["@id"]
    allowed = selected_predicates(p, predicates)
    queue, visited, seen_edges, found = deque([(start, 0)]), {start}, set(), []
    truncated = False
    # A visited-node budget bounds work even on dense graphs before serialization.
    visit_limit = min(100, p.config["retrieval"]["max_limit"])
    while queue:
        node, depth = queue.popleft()
        if depth >= bound["hops"]:
            continue
        for edge, target, orientation in edges(p, node, direction, allowed):
            if edge["@id"] in seen_edges:
                continue
            seen_edges.add(edge["@id"])
            item = explain(p, edge, "graph_traversal")
            item.pop("relationships", None)
            item.update(traversed_from=node, traversed_to=target, direction=orientation, hops=depth + 1,
                        target_label=p.by_id[target]["label"])
            found.append(item)
            if target not in visited:
                if len(visited) >= visit_limit:
                    truncated = True
                else:
                    visited.add(target)
                    queue.append((target, depth + 1))
            if len(found) > bound["limit"]:
                # One look-ahead edge distinguishes a complete boundary result.
                truncated = True
                queue.clear()
                break
    return envelope(p, "neighbors", query, found, bound, status="ok" if found else "no_match",
                    truncated=truncated, traversal={"start": start, "direction": direction,
                        "predicates": sorted(allowed), "visited_nodes": len(visited), "max_visited_nodes": visit_limit})


def path(value, source, target, *, direction="outgoing", predicates=(), hops=None, limit=None, max_bytes=None):
    p = project(value)
    bound = limits(p, limit, max_bytes, hops)
    start, end = resolve_one(p, source)["@id"], resolve_one(p, target)["@id"]
    allowed = selected_predicates(p, predicates)
    queue, visited = deque([(start, [])]), {start}
    found, truncated = None, False
    visit_limit = min(100, p.config["retrieval"]["max_limit"])
    while queue:
        node, steps = queue.popleft()
        if node == end:
            found = steps
            break
        if len(steps) >= bound["hops"]:
            continue
        for edge, nxt, orientation in edges(p, node, direction, allowed):
            if nxt in visited:
                continue
            if len(visited) >= visit_limit:
                truncated = True
                continue
            visited.add(nxt)
            queue.append((nxt, [*steps, (edge, node, nxt, orientation)]))
    results = []
    for edge, node, nxt, orientation in found or []:
        item = explain(p, edge, "graph_traversal")
        item.pop("relationships", None)
        item.update(traversed_from=node, traversed_to=nxt, direction=orientation)
        results.append(item)
    return envelope(p, "path", {"source": source, "target": target}, results, bound,
                    status="ok" if found is not None else "no_path", truncated=truncated,
                    traversal={"start": start, "end": end, "direction": direction,
                        "predicates": sorted(allowed), "visited_nodes": len(visited), "max_visited_nodes": visit_limit,
                        "within_hops": bound["hops"], "path_found": found is not None})
