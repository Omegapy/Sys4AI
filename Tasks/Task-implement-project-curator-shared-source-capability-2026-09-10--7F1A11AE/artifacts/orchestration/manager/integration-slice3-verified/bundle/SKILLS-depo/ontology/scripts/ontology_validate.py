"""Deterministic executable constraints for the compact ontology profile."""
import unicodedata
from ontology_core import CORE, OntologyError, exact, require, assert_current


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def validate_records(project):
    findings = []
    by_id = project.by_id

    def add(code, message, record):
        findings.append({"code": code, "message": message, "record_id": record.get("@id"), "path": project.locations.get(record.get("@id")), "severity": "error"})

    def check(condition, code, message, record):
        if not condition: add(code, message, record)
        return bool(condition)

    labels = {}
    for record in project.records:
        rid, kind = record["@id"], record["kind"]
        state = record.get("lifecycle")
        check(state in {"draft", "approved", "deprecated"}, "invalid_lifecycle", "Lifecycle must be draft, approved or deprecated.", record)
        check(record.get("fact_kind") in {"asserted", "derived", "inferred", "external"}, "invalid_fact_kind", "Every fact must retain its classification.", record)
        types = record.get("@type")
        valid_types = check(isinstance(types, list) and bool(types) and all(isinstance(v, str) for v in types) and len(types) == len(set(types)), "invalid_types", "@type must list distinct stable type IDs.", record)
        if valid_types:
            for target in types:
                check(target in by_id and by_id[target]["kind"] == "concept", "invalid_type", "Type is not a selected ontology concept: " + target, record)
        if state in {"approved", "deprecated"}:
            for key in ("label", "definition", "module"):
                check(isinstance(record.get(key), str) and bool(record[key].strip()), "missing_metadata", "Approved records require " + key + ".", record)
            check(bool(record.get("sources")), "missing_provenance", "Approved records require an exact local source reference.", record)
        for key in ("aliases", "examples", "non_examples", "ambiguity_with"):
            if key in record:
                check(isinstance(record[key], list) and all(isinstance(v, str) and v.strip() for v in record[key]), "invalid_metadata", key + " must be a string array.", record)
        if "scope_note" in record:
            check(isinstance(record["scope_note"], str) and record["scope_note"].strip(), "invalid_metadata", "Scope note must explain a distinction.", record)
        if isinstance(record.get("label"), str) and state != "draft" and kind != "relation":
            terms = [record["label"]] + (record.get("aliases", []) if isinstance(record.get("aliases", []), list) else [])
            for term in terms:
                if isinstance(term, str): labels.setdefault(normalized(term), set()).add(rid)
        for target in record.get("ambiguity_with", []) if isinstance(record.get("ambiguity_with", []), list) else []:
            check(target in by_id and target != rid, "dangling_target", "Ambiguity must name another selected identity.", record)
        if state == "deprecated":
            check(isinstance(record.get("deprecation_reason"), str) and bool(record["deprecation_reason"].strip()), "deprecation_reason", "Deprecated IDs require a reason.", record)
        elif "deprecation_reason" in record or "replacement" in record:
            add("invalid_deprecation", "Only deprecated records carry deprecation metadata.", record)
        if record.get("replacement") is not None:
            check(record["replacement"] in by_id and record["replacement"] != rid, "dangling_replacement", "Replacement must name a distinct selected identity.", record)
        if "history" in record:
            valid_history = check(isinstance(record["history"], list), "invalid_history", "History must be a list of retained semantic revisions.", record)
            if valid_history:
                for entry in record["history"]:
                    check(isinstance(entry, dict) and set(entry) == {"sha256", "definition", "lifecycle", "reason"} and all(isinstance(v, str) and v for v in entry.values()), "invalid_history", "Each history entry needs previous sha256, definition, lifecycle and reason.", record)
        if kind == "predicate":
            for field in ("domain", "range"):
                values = record.get(field)
                valid = check(isinstance(values, list) and bool(values) and all(isinstance(v, str) for v in values), "invalid_predicate", "Predicate requires explicit permitted " + field + " types.", record)
                if valid:
                    for target in values:
                        check(target in by_id and by_id[target]["kind"] == "concept", "invalid_predicate_type", "Predicate type is not a selected concept.", record)
            check(type(record.get("acyclic")) is bool, "invalid_predicate", "Predicate must explicitly declare acyclicity.", record)
            c = record.get("cardinality")
            check(isinstance(c, dict) and set(c) == {"min", "max"} and type(c["min"]) is int and c["min"] >= 0 and (c["max"] is None or type(c["max"]) is int and c["max"] >= c["min"]), "invalid_cardinality", "Cardinality requires nonnegative min and compatible max (or null).", record)
            qualifiers = record.get("qualifiers")
            if check(isinstance(qualifiers, dict), "invalid_qualifiers", "Predicate qualifier schema must be an object.", record):
                for name, spec in qualifiers.items():
                    check(isinstance(name, str) and bool(name) and isinstance(spec, dict) and set(spec) == {"type", "required"} and isinstance(spec["type"], str) and spec["type"] in {"string", "integer", "number", "boolean"} and type(spec["required"]) is bool, "invalid_qualifiers", "Unsupported qualifier schema.", record)
        elif kind == "binding":
            check(record.get("entity") in by_id, "dangling_target", "Binding target is absent.", record)
            check(record.get("binding_type") in {"artifact", "skill", "role", "specification", "registry"}, "invalid_binding", "Unsupported binding type.", record)
            if record.get("binding_type") == "role":
                paths = {r["path"] for r in record.get("sources", [])}
                check(paths == {"AGENTS.md", "ROLE.md"} or len(paths) == 2 and any(p.endswith("/AGENTS.md") and p[:-9]+"ROLE.md" in paths for p in paths), "role_pair", "Role bindings require both exact AGENTS.md and ROLE.md sources in one directory.", record)

    for label, ids in sorted(labels.items()):
        if len(ids) > 1:
            for rid in sorted(ids):
                rec = by_id[rid]
                check(ids - {rid} <= set(rec.get("ambiguity_with", [])) and bool(rec.get("scope_note")), "label_ambiguity", "Unmodeled label/alias collision for " + repr(label) + "; add explicit candidate distinctions.", rec)

    # Type membership includes explicit local subtype declarations, with a bounded fixed point.
    parent_types = {}
    for edge in project.relations:
        if edge.get("predicate") == CORE + "subtypeOf":
            parent_types.setdefault(edge.get("subject"), set()).add(edge.get("object"))

    def types_of(record):
        result = set(record.get("@type", [])) if isinstance(record.get("@type"), list) else set()
        if record["kind"] == "concept": result.add(record["@id"])
        queue = list(result)
        while queue:
            typ = queue.pop()
            for parent in parent_types.get(typ, ()):
                if parent not in result:
                    result.add(parent); queue.append(parent)
        return result

    edges_by_predicate = {}
    for edge in project.relations:
        ends = []
        for key in ("subject", "predicate", "object"):
            target = edge.get(key)
            if check(isinstance(target, str) and target in by_id, "dangling_target", "Relationship " + key + " is absent from the selected graph.", edge):
                ends.append(by_id[target])
        if len(ends) != 3: continue
        subject, predicate, obj = ends
        if not check(predicate["kind"] == "predicate", "invalid_relation_type", "Relationship predicate is not a registered predicate.", edge): continue
        check(bool(types_of(subject) & set(predicate.get("domain", []))), "domain_violation", "Relationship source type is outside the predicate domain.", edge)
        check(bool(types_of(obj) & set(predicate.get("range", []))), "range_violation", "Relationship target type is outside the predicate range.", edge)
        values, spec = edge.get("qualifiers", {}), predicate.get("qualifiers", {})
        if check(isinstance(values, dict), "invalid_qualifiers", "Relationship qualifiers must be an object.", edge) and isinstance(spec, dict):
            check(set(values) <= set(spec), "invalid_qualifiers", "Relationship contains undeclared qualifiers.", edge)
            for key, rule in spec.items():
                if not isinstance(rule, dict) or not isinstance(rule.get("type"), str): continue
                check(not rule.get("required") or key in values, "required_qualifier", "Required relationship qualifier is absent: " + key, edge)
                if key in values:
                    value = values[key]
                    valid = {"string": isinstance(value, str), "integer": type(value) is int, "number": type(value) in (int, float), "boolean": type(value) is bool}.get(rule["type"], False)
                    check(valid, "qualifier_type", "Relationship qualifier has an invalid type: " + key, edge)
        edges_by_predicate.setdefault(predicate["@id"], []).append(edge)

    for predicate in (r for r in project.records if r["kind"] == "predicate"):
        edges = edges_by_predicate.get(predicate["@id"], [])
        cardinality = predicate.get("cardinality", {})
        if isinstance(cardinality, dict) and type(cardinality.get("min")) is int and (cardinality.get("max") is None or type(cardinality.get("max")) is int):
            for subject in project.records:
                if not types_of(subject) & set(predicate.get("domain", [])): continue
                count = sum(e["subject"] == subject["@id"] for e in edges)
                check(cardinality["min"] <= count and (cardinality.get("max") is None or count <= cardinality["max"]), "cardinality_violation", "Outgoing relation count violates " + predicate["@id"] + ".", subject)
        if predicate.get("acyclic") is True:
            graph = {}
            for edge in edges: graph.setdefault(edge["subject"], set()).add(edge["object"])
            indegree = {v: 0 for a, targets in graph.items() for v in [a, *targets]}
            for targets in graph.values():
                for target in targets: indegree[target] += 1
            ready = sorted(v for v, n in indegree.items() if n == 0)
            visited = 0
            while ready:
                current = ready.pop(); visited += 1
                for target in sorted(graph.get(current, ())):
                    indegree[target] -= 1
                    if indegree[target] == 0: ready.append(target)
            check(visited == len(indegree), "acyclic_violation", "Declared acyclic relationship contains a cycle.", predicate)
    return sorted(findings, key=lambda d: (d["code"], d["record_id"] or "", d["path"] or "", d["message"]))


def validate_project(project, *, require_current=False):
    if not hasattr(project, "records"):
        from ontology_core import load_project
        project = load_project(project, validate=False)
    diagnostics = list(project.diagnostics)
    if require_current:
        try: assert_current(project)
        except OntologyError as exc: diagnostics.append(exc.as_dict())
    return {"valid": not any(d["severity"] == "error" for d in diagnostics), "diagnostics": diagnostics, "context": project.context()}
