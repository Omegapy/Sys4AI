"""Intent routing keeps definitions, current authority and history distinguishable."""
from ontology_core import OntologyError, read_bytes, safe_path, sha256, source_status
from ontology_retrieval import envelope, explain, limits, project, query_text, ranked, term, tokens


def capability(value, query, *, limit=None, max_bytes=None):
    p = project(value)
    bound = limits(p, limit, max_bytes)
    rows = [(m, r) for m, r in ranked(p, query, kinds={"concept", "instance"})
            if any(t.rsplit(":", 1)[-1] in {"Skill", "Capability"} for t in r["@type"])]
    if rows and rows[0][0][0] < 3:
        rows = [(m, r) for m, r in rows if m[0] == rows[0][0][0]]
    selected = {}
    for match, record in rows[:bound["limit"]]:
        selected.setdefault(record["@id"], (match[2], record))
        related = set()
        for relation in p.relations:
            if relation["predicate"].rsplit(":", 1)[-1] == "providesCapability" and record["@id"] in (relation["subject"], relation["object"]):
                related.update((relation["subject"], relation["object"]))
        for identity in sorted(related):
            selected.setdefault(identity, ("capability_relation", p.by_id[identity]))
    results = []
    for identity, (reason, record) in selected.items():
        row = explain(p, record, reason)
        row["executed"] = False
        row["availability"] = "available" if row["freshness"] == "current" else row["freshness"]
        row["availability_basis"] = "declared_source_freshness"
        row["runtime_observed"] = False
        row["authorization"] = "not_assessed"
        row["constraints"] = [record.get("scope_note", "Current skill and project authority are required before execution.")]
        results.append(row)
    return envelope(p, "capability", query, results, bound, status="ok" if results else "no_match")


def _excerpt(text, locator, query, maximum=2000):
    lines = text.splitlines()
    if locator.startswith("line:"):
        try:
            start = max(0, int(locator[5:].split("-", 1)[0]) - 1)
        except ValueError:
            start = 0
    else:
        heading = locator.removeprefix("section:").strip().casefold()
        selected = [i for i, line in enumerate(lines) if line.lstrip("# ").strip().casefold() == heading]
        if selected:
            start = selected[0]
        else:
            words = tokens(query)
            start = max(range(len(lines)), key=lambda i: len(words & tokens(lines[i]))) if lines else 0
    segment = "\n".join(lines[start:])
    encoded = segment.encode("utf-8")
    return encoded[:maximum].decode("utf-8", errors="ignore"), start + 1, len(encoded) > maximum


def current_sources(value, query, *, limit=None, max_bytes=None):
    p = project(value)
    bound = limits(p, limit, max_bytes)
    query_text(query)
    rows = ranked(p, query, kinds={"concept", "instance"})[:3]
    selected_ids = {r["@id"] for _, r in rows}
    references = {}
    # Bindings to selected meanings take precedence over general root guidance.
    for r in p.records:
        if (r["kind"] == "binding" and r["entity"] in selected_ids) or r["@id"] in selected_ids:
            for s in r["sources"]:
                if s["path"] in p.config["source_allowlist"]:
                    references[(s["path"], s["locator"])] = s
    if not references:
        for source in p.sources:
            if source["path"] in {"AGENTS.md", "SOUL.md", "ROLE.md", "SPECS.md"}:
                references[(source["path"], source["locator"])] = {k: source[k] for k in ("path", "sha256", "locator")}
    results = []
    for (_, _), reference in sorted(references.items()):
        status = source_status(p, reference)
        row = {"source_type": "current_governance", "path": reference["path"], "locator": reference["locator"],
               "recorded_sha256": reference["sha256"], "sha256": status["actual_sha256"],
               "freshness": status["status"], "match_reason": "current_selected_governing_source",
               "discrepancy": "recorded_source_version_changed" if status["status"] == "stale" else "source_unavailable" if status["status"] == "unavailable" else None,
               "authority": "Current permitted source bytes control operational rules; ontology remains semantic context."}
        if status["status"] != "unavailable":
            raw = read_bytes(safe_path(p.root, reference["path"]))
            if sha256(raw) != status["actual_sha256"]:
                raise OntologyError("source_changed", "Current governing source changed during retrieval.", path=reference["path"])
            try:
                text = raw.decode("utf-8")
            except UnicodeError:
                raise OntologyError("invalid_source_encoding", "Current governing source is not UTF-8 text.", path=reference["path"]) from None
            excerpt, line, truncated = _excerpt(text, reference["locator"], query)
            row.update(excerpt=excerpt, excerpt_line=line, excerpt_truncated=truncated)
        results.append(row)
    return envelope(p, "current", query, results, bound, status="ok" if results else "no_current_source",
                    semantics="Current excerpts are authoritative source evidence; semantic contradictions need direct inspection.")


def knowledge(value, query, *, intent="mixed", limit=None, max_bytes=None, hops=None,
              direction="both", predicates=(), memory_packet=None, frozen_ontology=False, advanced=False):
    p = project(value)
    frozen_ontology = frozen_ontology or hasattr(p, "frozen_packet")
    if intent == "definition":
        result = term(p, query, limit=limit, max_bytes=max_bytes)
    elif intent == "relationship":
        from ontology_graph import neighbors
        result = neighbors(p, query, hops=hops, direction=direction, predicates=predicates, limit=limit, max_bytes=max_bytes)
    elif intent == "capability":
        result = capability(p, query, limit=limit, max_bytes=max_bytes)
    elif intent == "inference":
        result = inference_knowledge(p, query, limit=limit, max_bytes=max_bytes)
    elif intent == "proposals":
        result = proposal_knowledge(p, query, limit=limit, max_bytes=max_bytes)
    elif intent == "current":
        if frozen_ontology:
            from ontology_packet import frozen_current_sources
            result = frozen_current_sources(p, query, limit=limit, max_bytes=max_bytes)
        else:
            result = current_sources(p, query, limit=limit, max_bytes=max_bytes)
    elif intent in {"history", "mixed"}:
        from ontology_memory import read_links, search_memory
        bound = limits(p, limit, max_bytes)
        # Current sources are read before combining operational and historical evidence.
        if intent == "mixed":
            if frozen_ontology:
                from ontology_packet import frozen_current_sources
                current = frozen_current_sources(p, query, limit=limit, max_bytes=max_bytes)
            else:
                current = current_sources(p, query, limit=limit, max_bytes=max_bytes)
        else:
            current = {"results": []}
        history = search_memory(p, query, limit=limit, packet=memory_packet, frozen_ontology=frozen_ontology)
        definitions = term(p, query, limit=limit, max_bytes=max_bytes) if intent == "mixed" else {"results": []}
        try:
            associations = read_links(p) if intent == "mixed" and not frozen_ontology else {"status": "not_read", "results": []}
        except OntologyError as error:
            associations = {"status": "invalid", "results": [], "diagnostic": error.as_dict()}
        ids = {r["@id"] for r in definitions["results"]}
        links = [{**r, "source_type": "derived_association", "freshness": associations["status"],
                  "path": associations["path"], "sha256": associations["sha256"], "match_reason": "existing_memory_concept_sidecar"}
                 for r in associations["results"] if ids.intersection(r["concept_ids"])]
        results = [*definitions["results"], *current["results"], *history["results"], *links]
        if advanced and intent == "mixed":
            inferred = inference_knowledge(p, query, limit=limit, max_bytes=max_bytes)
            results.extend(inferred["results"])
            suggestions = proposal_knowledge(p, query, limit=limit, max_bytes=max_bytes)
            results.extend(suggestions["results"])
        result = envelope(p, "knowledge", query, results, bound, status="ok" if results else history["status"],
                          memory={k: v for k, v in history.items() if k != "results"},
                          associations_status=associations["status"], associations_diagnostic=associations.get("diagnostic"))
    else:
        raise OntologyError("invalid_intent", "Supported intents: definition, relationship, capability, current, history, mixed, inference, proposals.")
    result["intent"] = intent
    return result


def inference_knowledge(value, query, *, limit=None, max_bytes=None):
    p = project(value)
    query = query_text(query)
    bound = limits(p, limit, max_bytes)
    if hasattr(p, "frozen_packet"):
        proof = p.frozen_packet.get("advanced", {}).get("inference")
        if proof is None:
            return envelope(p, "inference", query, [], bound, status="no_permitted_frozen_inference")
    else:
        from ontology_standards import infer
        proof = infer(p.root)
    if not proof.get("complete"):
        return envelope(p, "inference", query, [], bound, status=proof.get("status", "unavailable"),
                        inference={"complete": False, "diagnostics": proof.get("diagnostics", [])})
    identities = {r["@id"] for _, r in ranked(p, query, kinds={"concept", "instance", "predicate"})[:bound["limit"]]}
    rows = []
    from ontology_derivations import for_conclusion
    for triple in proof.get("inferred", []):
        if query not in triple and not identities.intersection(x for x in triple if isinstance(x, str)):
            continue
        chain = for_conclusion(proof["proofs"], triple)
        rows.append({"source_type": "ontology_inference", "fact_kind": "inferred", "triple": triple,
                     "label": " → ".join(triple), "definition": "A conclusion from the selected approved premises and finite rules.",
                     "trusted": proof["trusted"], "proof": chain, "profile": proof["profile"],
                     "freshness": "current_frozen_version" if hasattr(p, "frozen_packet") else "current",
                     "input_snapshot_sha256": proof["context"]["snapshot_sha256"], "authority": False})
    return envelope(p, "inference", query, rows, bound, status=proof["status"],
                    inference={"complete": True, "trusted": proof["trusted"], "conflicts": proof.get("conflicts", [])})


def proposal_knowledge(value, query, *, limit=None, max_bytes=None):
    p = project(value)
    bound = limits(p, limit, max_bytes)
    query = query_text(query)
    if hasattr(p, "frozen_packet"):
        return envelope(p, "proposals", query, [], bound, status="proposals_excluded_from_frozen_context")
    from ontology_proposals import list_proposals, open_proposal
    rows = []
    for head in list_proposals(p.root):
        proposal = open_proposal(p.root, head["proposal_id"])
        revision = proposal["revision"]
        if not tokens(query).intersection(tokens(str(revision.get("candidate", {})) + " " + revision.get("rationale", ""))):
            continue
        rows.append({"source_type": "ontology_proposal", "fact_kind": "proposed", "label": head["proposal_id"],
                     "definition": revision.get("rationale", "Saved draft awaiting separate review."), "review_state": head["state"],
                     "proposal_id": head["proposal_id"], "revision": head["revision"],
                     "revision_sha256": head["revision_sha256"], "authority": False})
    return envelope(p, "proposals", query, rows, bound, status="ok" if rows else "no_match")
