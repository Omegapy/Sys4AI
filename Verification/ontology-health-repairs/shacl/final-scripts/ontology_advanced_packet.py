"""Version 2 Task packets: exact selected rules, proofs and captured retrieval inputs."""
import copy
import math
from pathlib import Path

from ontology_core import (CORE, canonical_bytes, exact, load_project, read_bytes,
                           read_json, require, safe_path, sha256)

GRAPHS = {"asserted", "derived", "inferred", "external"}


def _contracts():
    for parent in Path(__file__).resolve().parents:
        for relative in ("ONTOLOGY-depo", "reference-assets/ONTOLOGY-depo"):
            root = parent / relative
            if (root / "rules/finite-profile-v1.json").is_file():
                return root
    raise ValueError("The installed advanced rule contracts are missing.")


def _selected_extensions(project, cfg, identifiers):
    from ontology_advanced import load_extensions
    extensions, _, _ = load_extensions(project, cfg)
    all_ids = {row["id"] for ext in extensions for key in ("axioms", "annotations", "negative_assertions") for row in ext[key]}
    require(set(identifiers) <= all_ids, "unknown_assertion", "Select existing approved extension statement identities.")
    result = []
    for ext in extensions:
        value = copy.deepcopy(ext)
        for key in ("axioms", "annotations", "negative_assertions"):
            value[key] = [row for row in value[key] if row["id"] in identifiers]
        if any(value[key] for key in ("axioms", "annotations", "negative_assertions")):
            result.append(value)
    return result


def extend_packet(root, packet, *, graph_selection=("asserted",), goals=(), extension_ids=(), semantic_queries=()):
    from ontology_advanced import load_advanced
    from ontology_limits import limits
    from ontology_packet import MAX_BYTES, MAX_REFS, _manager, _forbidden, _overlap
    require(packet["schema_version"] == 1, "invalid_packet", "Extend an original version 1 selection exactly once.")
    require(isinstance(graph_selection, (tuple, list)) and graph_selection and
            len(set(graph_selection)) == len(graph_selection) and set(graph_selection) <= GRAPHS,
            "invalid_graph_selection", "Select distinct supported dataset graphs.")
    require(isinstance(extension_ids, (tuple, list)) and all(isinstance(i, str) for i in extension_ids),
            "invalid_selection", "Extension selection is an explicit list of statement IDs.")
    require(isinstance(semantic_queries, (tuple, list)) and len(semantic_queries) <= 10 and
            all(isinstance(q, str) and 0 < len(q) <= 4096 for q in semantic_queries),
            "invalid_selection", "Freeze at most ten exact semantic queries.")
    p = load_project(root)
    cfg = load_advanced(root, required=True)
    extensions = _selected_extensions(p, cfg, extension_ids)
    task = packet["task"]
    _, orchestration, _, task_sha = _manager(root, task["path"], task["execution_id"], task["generation"], task["manager"])
    require(task_sha == task["inspected_sha256"], "task_changed", "The manager's Task changed during advanced selection.")
    forbidden, forbidden_hashes = _forbidden(orchestration, task["path"])
    references = {}
    def bind(path, expected=None):
        require(not _overlap(path, forbidden), "excluded_source", "Worker-owned inputs cannot enter an initial solver packet.", path=path)
        data = read_bytes(safe_path(root, path))
        actual = sha256(data)
        require(actual not in forbidden_hashes and (expected is None or actual == expected),
                "stale_source", "Advanced packet source changed or belongs to a worker.", path=path)
        references[path] = {"path": path, "sha256": actual}
        return data
    bind("ontology-advanced.yaml")
    selected_ext_ids = {ext["id"] for ext in extensions}
    for ref in cfg["extensions"]:
        document = read_json(safe_path(root, ref["path"]))
        if document["id"] not in selected_ext_ids:
            continue
        bind(ref["path"], ref["sha256"])
        for shape in document.get("shapes", []):
            bind(shape["path"], shape["sha256"])
        for field in ("axioms", "annotations", "negative_assertions"):
            for row in document[field]:
                if row["id"] in extension_ids:
                    for source in row["sources"]:
                        require(source["path"] in p.config["source_allowlist"], "excluded_source", "Extension sources must belong to the selected project allowlist.")
                        bind(source["path"], source["sha256"])
    contracts = {}
    for relative in ("rules/finite-profile-v1.json", "shapes/ontology-v1.ttl"):
        raw = read_bytes(_contracts() / relative)
        contracts[relative] = {"sha256": sha256(raw), "text": raw.decode("utf-8")}
    inference = None
    if "inferred" in graph_selection or goals:
        from ontology_standards import infer
        inference = infer(root, goals=list(goals), premise_ids=[r["@id"] for r in packet["records"]] + list(extension_ids))
        require(inference.get("complete") and inference.get("status") in {"ok", "inconsistent"},
                "incomplete_reasoning", "Only completed scoped reasoning can be frozen; retain failures as separate evidence.")
    semantic = []
    if semantic_queries:
        from ontology_semantic import INDEX, MODEL_MANIFEST, capture_inputs
        selected = {r["@id"] for r in packet["records"]}
        for query in semantic_queries:
            captured = capture_inputs(p, query, selected)
            for path, digest in captured["documents"].items():
                require(path in {ref["path"] for ref in packet["references"]}, "excluded_source",
                        "Explicitly select indexed documentation as a frozen source before embedding it.", path=path)
                bind(path, digest)
            semantic.append({"query": query, "inputs": captured, "matches": _scores(captured),
                             "context": {"model_revision": captured["model"]["revision"], "index_sha256": captured["index_sha256"],
                                         "packages": captured["packages"]}, "excluded_results": "outside selected matrix"})
        bind(INDEX); bind(MODEL_MANIFEST)
    advanced = {"schema_version": 1, "graphs": list(graph_selection), "companion": cfg,
                "extension_ids": list(extension_ids), "extensions": extensions,
                "contracts": contracts, "references": sorted(references.values(), key=lambda r: r["path"]),
                "bounds": limits(cfg["limits"]), "goals": list(goals), "inference": inference,
                "semantic_queries": semantic,
                "authority": "Frozen semantic context; live guards and the current Task owner retain independent authority."}
    result = copy.deepcopy(packet)
    result.update(schema_version=2, advanced=advanced)
    require(len({r["path"] for r in [*packet["references"], *advanced["references"]]}) <= MAX_REFS and
            len(canonical_bytes(result)) <= min(MAX_BYTES, packet["limits"]["max_bytes"]),
            "packet_too_large", "Narrow the selected advanced facts, proofs, queries or sources to the existing Task packet bounds.")
    validate_advanced(root, result)
    return result


def _premises(packet):
    from ontology_advanced import RDF, RDFS
    rows = []
    for r in packet["records"]:
        if r["lifecycle"] != "approved" or r["fact_kind"] != "asserted" or not r["sources"]:
            continue
        triples = [[r["@id"], RDF + "type", typ] for typ in r["@type"]]
        if r["kind"] == "relation":
            predicate = RDFS + "subClassOf" if r["predicate"] == CORE + "subtypeOf" else r["predicate"]
            triples.append([r["subject"], predicate, r["object"]])
        for triple in triples:
            rows.append({"id": r["@id"] + ":" + sha256(canonical_bytes(triple))[:16],
                         "triple": triple, "record_id": r["@id"], "sources": r["sources"], "approved": True})
    for extension in packet["advanced"]["extensions"]:
        for row in extension["axioms"]:
            rows.append({"id": row["id"], "triple": [row[key] for key in ("subject", "predicate", "object")],
                         "record_id": row["id"], "sources": row["sources"], "approved": True})
    return sorted(rows, key=lambda r: r["id"])


def _scores(captured):
    vector = captured["query_vector"]
    result = []
    for row in captured["matrix"]:
        candidate = row["vector"]
        denom = math.sqrt(sum(x*x for x in vector) * sum(x*x for x in candidate))
        score = sum(x*y for x, y in zip(vector, candidate))/denom if denom else 0.0
        if score >= captured["threshold"]:
            result.append({"id": row["id"], "score": round(score, 6)})
    return sorted(result, key=lambda row: (-row["score"], row["id"]))


def validate_advanced(root, packet):
    from ontology_advanced import load_advanced
    from ontology_limits import limits
    from ontology_packet import MAX_BYTES, MAX_REFS, validate_packet_value
    require(isinstance(packet, dict) and packet.get("schema_version") == 2 and isinstance(packet.get("advanced"), dict),
            "invalid_advanced_packet", "An advanced packet has an explicit version 2 wrapper.")
    base = {k: copy.deepcopy(v) for k, v in packet.items() if k != "advanced"}
    base["schema_version"] = 1
    validate_packet_value(root, base)
    advanced = packet["advanced"]
    exact(advanced, ("schema_version", "graphs", "companion", "extension_ids", "extensions", "contracts", "references",
                     "bounds", "goals", "inference", "semantic_queries", "authority"))
    require(advanced["schema_version"] == 1 and isinstance(advanced["graphs"], list) and advanced["graphs"] and
            set(advanced["graphs"]) <= GRAPHS, "invalid_advanced_packet", "Unsupported frozen graph selection.")
    current_cfg = load_advanced(root, required=True)
    require(advanced["companion"] == current_cfg and advanced["bounds"] == limits(current_cfg["limits"]),
            "stale_packet", "Advanced configuration changed; the manager must assess and rebind inputs.")
    p = load_project(root)
    expected_extensions = _selected_extensions(p, current_cfg, advanced["extension_ids"])
    require(advanced["extensions"] == expected_extensions, "stale_packet", "Selected extension evidence changed.")
    permitted = {"ontology-advanced.yaml", ".sys4ai/ontology/semantic/index-v1.json", ".sys4ai/ontology/semantic/model.json",
                 *p.config["source_allowlist"], *(r["path"] for r in current_cfg["extensions"])}
    permitted.update(ref["path"] for ext in expected_extensions for ref in ext.get("shapes", []))
    require(isinstance(advanced["references"], list), "invalid_advanced_packet", "Advanced references must be explicit.")
    for ref in advanced["references"]:
        exact(ref, ("path", "sha256"))
        require(ref["path"] in permitted and sha256(read_bytes(safe_path(root, ref["path"]))) == ref["sha256"],
                "stale_packet", "An exact frozen advanced input changed or escaped its selection.", path=ref["path"])
    required_refs = {"ontology-advanced.yaml"}
    selected_exts = {ext["id"] for ext in expected_extensions}
    for ref in current_cfg["extensions"]:
        if read_json(safe_path(root, ref["path"]))["id"] in selected_exts:
            required_refs.add(ref["path"])
    required_refs.update(ref["path"] for ext in expected_extensions for ref in ext.get("shapes", []))
    required_refs.update(source["path"] for ext in expected_extensions for key in ("axioms", "annotations", "negative_assertions")
                         for statement in ext[key] for source in statement["sources"])
    if advanced["semantic_queries"]:
        required_refs.update({".sys4ai/ontology/semantic/index-v1.json", ".sys4ai/ontology/semantic/model.json"})
    require(required_refs <= {ref["path"] for ref in advanced["references"]}, "invalid_advanced_packet", "Advanced frozen evidence references are incomplete.")
    require(len({ref["path"] for ref in [*base["references"], *advanced["references"]]}) <= MAX_REFS and
            len(canonical_bytes(packet)) <= min(MAX_BYTES, base["limits"]["max_bytes"]), "packet_too_large", "Advanced packet exceeds existing Task evidence bounds.")
    require(set(advanced["contracts"]) == {"rules/finite-profile-v1.json", "shapes/ontology-v1.ttl"},
            "invalid_advanced_packet", "Freeze the selected supported rule and shape contracts.")
    for relative, contract in advanced["contracts"].items():
        raw = read_bytes(_contracts() / relative)
        require(contract == {"sha256": sha256(raw), "text": raw.decode("utf-8")},
                "stale_packet", "Frozen rules/shapes differ from the installed selected profile.")
    result = advanced["inference"]
    if result is not None:
        from ontology_reasoning import infer
        require(isinstance(result, dict) and result.get("complete") is True and isinstance(result.get("context"), dict),
                "invalid_advanced_packet", "Frozen inference must have complete engine evidence and exact context.")
        negatives = [row for ext in expected_extensions for row in ext["negative_assertions"]]
        replay = infer(_premises(packet), negatives, advanced["goals"], result["context"], advanced["bounds"])
        for key in ("status", "complete", "trusted", "profile", "rules", "inferred", "proofs", "conflicts", "conclusions"):
            require(result.get(key) == replay.get(key), "invalid_derivation", "Frozen derivation does not follow from the exact selected premises and rules.")
    selected = {r["@id"] for r in packet["records"]}
    require(isinstance(advanced["semantic_queries"], list) and len(advanced["semantic_queries"]) <= 10,
            "invalid_advanced_packet", "Frozen semantic queries exceed their bound.")
    for query in advanced["semantic_queries"]:
        exact(query, ("query", "inputs", "matches", "context", "excluded_results"))
        require(isinstance(query["query"], str) and 0 < len(query["query"]) <= 4096 and
                all(set(row) == {"id", "score"} and row["id"] in selected and type(row["score"]) in (float, int)
                    and -1 <= row["score"] <= 1 for row in query["matches"]),
                "excluded_source", "Captured semantic matches cannot add definitions outside the frozen selection.")
        captured = query["inputs"]
        exact(captured, ("query_vector", "matrix", "model", "packages", "documents", "index_sha256", "threshold"))
        dimension = captured["model"]["dimension"]
        require(type(dimension) is int and dimension == 384 and captured["threshold"] == 0.45 and
                isinstance(captured["matrix"], list) and len(captured["matrix"]) <= len(selected),
                "invalid_advanced_packet", "Captured model/matrix dimensions exceed the selected profile.")
        for vector in [captured["query_vector"], *(row["vector"] for row in captured["matrix"])]:
            require(isinstance(vector, list) and len(vector) == dimension and
                    all(type(x) in (int, float) and math.isfinite(x) for x in vector),
                    "invalid_advanced_packet", "Captured embedding is not a finite selected-model vector.")
        index = read_json(safe_path(root, ".sys4ai/ontology/semantic/index-v1.json"))
        require(captured["model"] == index["runtime"]["model"] and captured["packages"] == index["runtime"]["packages"]
                and captured["documents"] == index["documents"] and captured["index_sha256"] == sha256(safe_path(root, ".sys4ai/ontology/semantic/index-v1.json")),
                "invalid_advanced_packet", "Captured semantic model/index versions differ from the exact frozen inputs.")
        require(set(captured["documents"]) <= {ref["path"] for ref in base["references"]},
                "excluded_source", "Captured documentation lies outside the original permitted packet sources.")
        indexed = {row["id"]: (row, vector) for row, vector in zip(index["rows"], index["vectors"])}
        for row in captured["matrix"]:
            exact(row, ("id", "vector", "text", "record_sha256", "sources"))
            require(row["id"] in selected and row["id"] in indexed, "excluded_source", "Vector identity lies outside the frozen record selection.")
            original, vector = indexed[row["id"]]
            require(row == {"id": original["id"], "vector": vector, "text": original["text"],
                            "record_sha256": original["record_sha256"], "sources": original["sources"]},
                    "invalid_advanced_packet", "Captured matrix differs from the referenced exact source index.")
        require(query["matches"] == _scores(captured), "invalid_advanced_packet", "Captured semantic scores do not follow from the frozen matrix.")
    return packet


def frozen_search(p, query, *, limit=None, max_bytes=None):
    from ontology_retrieval import envelope, explain, limits, normalize, ranked
    bound = limits(p, limit, max_bytes)
    lexical = ranked(p, query, kinds={"concept", "instance", "predicate"})
    if lexical and lexical[0][0][0] < 3:
        return None
    rows = p.frozen_packet.get("advanced", {}).get("semantic_queries", [])
    saved = next((row for row in rows if normalize(row["query"]) == normalize(query)), None)
    if saved is None:
        return None
    results = [explain(p, p.by_id[row["id"]], "frozen_semantic_similarity", row["score"]) for row in saved["matches"]]
    return envelope(p, "search", query, results, bound, status="ok" if results else "no_match",
                    semantic={"status": "frozen", "used": True, "context": saved["context"], "live_embeddings_read": False,
                              "excluded_results": saved["excluded_results"]})
