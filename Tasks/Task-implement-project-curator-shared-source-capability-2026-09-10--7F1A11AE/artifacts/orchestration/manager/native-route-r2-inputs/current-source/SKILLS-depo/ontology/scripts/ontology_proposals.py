"""Durable immutable candidates, evidence and decisions; never canonical authoring."""
from datetime import datetime, timezone
import copy
import re
import uuid

from ontology_core import (canonical_bytes, sha256, safe_path, read_json, read_bytes,
                           require, exact, digest, atomic_write, operation_lock,
                           load_project, OntologyError)
from ontology_publication import _root, check_proposal

STORE = "control_records/ontology/proposals/"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def identity(value):
    require(isinstance(value, str) and re.fullmatch(r"ONTPROP-[A-Za-z0-9-]{4,100}", value),
            "proposal_identity", "Select an exact ONTPROP proposal identity.")
    return value


def _folder(proposal_id):
    return STORE + identity(proposal_id) + "/"


def _sealed(value, key):
    result = copy.deepcopy(value)
    result[key] = sha256(canonical_bytes(result))
    return result


def _verify(value, key):
    checked = copy.deepcopy(value)
    expected = checked.pop(key, None)
    require(expected == sha256(canonical_bytes(checked)), "proposal_integrity",
            "Durable proposal evidence differs from its immutable digest.")
    return value


def _append(root, relative, value):
    data = canonical_bytes(value)
    require(len(data) <= 2_000_000, "proposal_size", "Proposal artifact exceeds two megabytes.")
    atomic_write(root, relative, data, None)


def _head(root, proposal_id):
    return _verify(read_json(safe_path(root, _folder(proposal_id) + "head.json")), "head_sha256")


def semantic_diff(root, candidate):
    """Field-level changes retain prior and candidate meanings, including removals."""
    changes = []
    for change in candidate["changes"]:
        source = safe_path(root, change["path"], must_exist=False)
        from ontology_core import decode_json
        if change["path"].endswith(".ttl"):
            changes.append({"path": change["path"], "id": None, "change": "shape",
                            "fields": {"turtle": {"before": read_bytes(source).decode() if source.exists() else None,
                                                   "after": change["content"]}}})
            continue
        before = read_json(source) if source.exists() else {}
        after = decode_json(change["content"].encode())
        if "@graph" in after:
            old = {r["@id"]: r for r in before.get("@graph", [])}
            new = {r["@id"]: r for r in after["@graph"]}
            for rid in sorted(old.keys() | new.keys()):
                if old.get(rid) == new.get(rid):
                    continue
                fields = {key: {"before": old.get(rid, {}).get(key), "after": new.get(rid, {}).get(key)}
                          for key in sorted(old.get(rid, {}).keys() | new.get(rid, {}).keys())
                          if old.get(rid, {}).get(key) != new.get(rid, {}).get(key)}
                changes.append({"path": change["path"], "id": rid,
                                "change": "add" if rid not in old else "remove" if rid not in new else "edit",
                                "fields": fields})
        elif before != after:
            changes.append({"path": change["path"], "id": None, "change": "document",
                            "fields": {"document": {"before": before, "after": after}}})
    return changes


def _evidence(project, evidence):
    require(isinstance(evidence, list) and len(evidence) <= 200, "proposal_evidence",
            "Select at most 200 exact source references.")
    from ontology_core import source_status
    for source in evidence:
        require(source_status(project, source)["status"] == "current", "source_not_current",
                "Proposal evidence must select current permitted source bytes.", path=source.get("path"))


def save(root, candidate, *, proposal_id=None, expected_revision=None, rationale,
         evidence=(), uncertainty=(), generator=None, source_packet=None, addressed_findings=()):
    root = _root(root)
    check_proposal(root, candidate)
    project = load_project(root, validate=False)
    require(isinstance(rationale, str) and 0 < len(rationale.strip()) <= 4000,
            "proposal_rationale", "Provide a bounded explanation of the semantic change.")
    require(isinstance(uncertainty, (list, tuple)) and len(uncertainty) <= 100
            and all(isinstance(x, str) and 0 < len(x) <= 2000 for x in uncertainty),
            "proposal_uncertainty", "Uncertainty must be a bounded list of explicit statements.")
    require(isinstance(addressed_findings, (list, tuple)) and all(isinstance(x, str) for x in addressed_findings),
            "proposal_findings", "Addressed findings must name exact finding identities.")
    require(generator is None or isinstance(generator, dict), "proposal_generator", "Generator attribution is an object or explicitly unavailable.")
    require(source_packet is None or isinstance(source_packet, dict), "proposal_packet", "Source packet attribution is an object or explicitly unavailable.")
    evidence = list(evidence)
    _evidence(project, evidence)
    # A stale target may be retained in a candidate for repair, but never reviewed or published.
    proposal_id = identity(proposal_id or "ONTPROP-" + uuid.uuid4().hex)
    folder = _folder(proposal_id)
    with operation_lock(root, "control_records/ontology/publication.lock"), operation_lock(root, STORE + "store.lock"):
        path = safe_path(root, folder + "head.json", must_exist=False)
        previous = _head(root, proposal_id) if path.exists() else None
        require(expected_revision == (previous["revision"] if previous else None),
                "draft_conflict", "A newer saved revision exists. Your entered draft is unchanged; reopen and compare it.")
        require(not previous or previous["state"] not in {"published", "partial"}, "proposal_closed",
                "A published or partially committed operation must be reopened or recovered, not revised.")
        revision = previous["revision"] + 1 if previous else 1
        parent = open_proposal(root, proposal_id)["revision"] if previous else None
        if parent:
            accepted = "control_records/ontology/intents/" + parent["candidate"]["operation_id"] + ".json"
            require(not safe_path(root, accepted, must_exist=False).exists(), "proposal_closed", "This candidate has an accepted publication intent; recover or reopen its canonical result.")
        record = _sealed({"schema_version": 1, "proposal_id": proposal_id,
                          "project_id": project.project_id, "revision": revision,
                          "parent_sha256": parent["revision_sha256"] if parent else None,
                          "created_at": utc_now(), "candidate": copy.deepcopy(candidate),
                          "candidate_sha256": sha256(canonical_bytes(candidate)),
                          "base_context": project.context(), "rationale": rationale,
                          "evidence": evidence, "uncertainty": list(uncertainty),
                          "generator": copy.deepcopy(generator), "source_packet": copy.deepcopy(source_packet),
                          "addressed_findings": list(addressed_findings),
                          "semantic_diff": semantic_diff(root, candidate)}, "revision_sha256")
        _append(root, folder + f"revisions/{revision:06d}.json", record)
        event_number = previous["event"] + 1 if previous else 1
        event = _sealed({"schema_version": 1, "proposal_id": proposal_id, "event": event_number,
                         "revision": revision, "revision_sha256": record["revision_sha256"],
                         "decision": "revise" if previous else "save", "at": utc_now(),
                         "supersedes": parent["revision_sha256"] if parent else None,
                         "details": {"approval_invalidated": bool(previous)}}, "event_sha256")
        _append(root, folder + f"events/{event_number:06d}.json", event)
        head = _sealed({"schema_version": 1, "proposal_id": proposal_id, "revision": revision,
                        "revision_sha256": record["revision_sha256"], "event": event_number,
                        "state": "draft", "validation_sha256": None, "review_sha256": None}, "head_sha256")
        atomic_write(root, folder + "head.json", canonical_bytes(head), sha256(path) if path.exists() else None)
    return open_proposal(root, proposal_id)


def open_proposal(root, proposal_id, *, revision=None):
    root = _root(root)
    head = _head(root, proposal_id)
    selected = head["revision"] if revision is None else revision
    require(type(selected) is int and 1 <= selected <= head["revision"], "proposal_revision",
            "Select an existing proposal revision.")
    folder = _folder(proposal_id)
    record = _verify(read_json(safe_path(root, folder + f"revisions/{selected:06d}.json")), "revision_sha256")
    require(record["revision"] == selected and record["proposal_id"] == proposal_id,
            "proposal_integrity", "Candidate identity differs from its durable location.")
    if selected == head["revision"]:
        require(record["revision_sha256"] == head["revision_sha256"], "proposal_integrity", "Current revision differs from head.")
    events = [_verify(read_json(safe_path(root, folder + f"events/{n:06d}.json")), "event_sha256")
              for n in range(1, head["event"] + 1)]
    result = {"head": head, "revision": record, "events": events,
              "superseded": selected != head["revision"], "validation": None, "review": None}
    for key in ("validation", "review"):
        value = head[key + "_sha256"]
        if value and selected == head["revision"]:
            result[key] = _verify(read_json(safe_path(root, folder + key + "s/" + value + ".json")), key + "_sha256")
    return result


def list_proposals(root):
    root = _root(root)
    folder = safe_path(root, STORE.rstrip("/"), must_exist=False)
    if not folder.exists():
        return []
    rows = []
    for path in sorted(folder.iterdir()):
        if path.name.startswith("ONTPROP-"):
            safe_path(root, STORE + path.name)
            rows.append(_head(root, path.name))
    return rows


def _event(root, proposal_id, expected_revision, decision, details, *, validation=None, review=None):
    root = _root(root)
    with operation_lock(root, "control_records/ontology/publication.lock"), operation_lock(root, STORE + "store.lock"):
        head = _head(root, proposal_id)
        require(head["revision"] == expected_revision, "draft_conflict", "Current candidate changed after this view.")
        folder = _folder(proposal_id)
        if decision not in {"published", "partial"}:
            candidate = open_proposal(root, proposal_id)["revision"]["candidate"]
            require(not safe_path(root, "control_records/ontology/intents/" + candidate["operation_id"] + ".json", must_exist=False).exists(),
                    "proposal_closed", "An accepted publication intent owns this revision; preserve it for exact recovery.")
        if review is not None:
            require(review["validation_sha256"] == head["validation_sha256"] and review["revision_sha256"] == head["revision_sha256"],
                    "stale_validation", "Validation changed while accepting the review. Reopen its latest exact report.")
        old_hash = sha256(safe_path(root, folder + "head.json"))
        event_number = head["event"] + 1
        event = _sealed({"schema_version": 1, "proposal_id": proposal_id, "event": event_number,
                         "revision": head["revision"], "revision_sha256": head["revision_sha256"],
                         "decision": decision, "at": utc_now(), "details": copy.deepcopy(details)}, "event_sha256")
        _append(root, folder + f"events/{event_number:06d}.json", event)
        head.pop("head_sha256")
        head.update(event=event_number)
        if validation is not None:
            data = _sealed(validation, "validation_sha256")
            relative = folder + "validations/" + data["validation_sha256"] + ".json"
            if not safe_path(root, relative, must_exist=False).exists():
                _append(root, relative, data)
            head.update(validation_sha256=data["validation_sha256"], review_sha256=None, state="validated" if data["eligible"] else "invalid")
        elif review is not None:
            data = _sealed(review, "review_sha256")
            _append(root, folder + "reviews/" + data["review_sha256"] + ".json", data)
            head.update(review_sha256=data["review_sha256"], state="reviewed")
        elif decision in {"reject", "discard", "supersede", "reopen", "published", "partial"}:
            head.update(state={"reject": "rejected", "discard": "discarded", "supersede": "superseded",
                               "reopen": "draft"}.get(decision, decision))
            if decision not in {"published", "partial"}:
                head["review_sha256"] = None
        head = _sealed(head, "head_sha256")
        atomic_write(root, folder + "head.json", canonical_bytes(head), old_hash)
    return open_proposal(root, proposal_id)


def store_validation(root, proposal_id, expected_revision, report):
    current = open_proposal(root, proposal_id)
    require(report["revision_sha256"] == current["revision"]["revision_sha256"], "stale_validation",
            "Validation names another candidate revision.")
    return _event(root, proposal_id, expected_revision, "validate", {"eligible": report["eligible"]}, validation=report)


def decide(root, proposal_id, *, expected_revision, decision, reason, validation_sha256=None, superseded_by=None):
    require(decision in {"accept", "reject", "discard", "supersede", "reopen"}, "proposal_decision", "Unsupported proposal decision.")
    require(isinstance(reason, str) and 0 < len(reason.strip()) <= 4000, "proposal_reason", "Explain this review decision.")
    current = open_proposal(root, proposal_id)
    require(current["head"]["revision"] == expected_revision, "draft_conflict", "A newer candidate superseded this view.")
    require(current["head"]["state"] not in {"published", "partial"}, "proposal_closed", "Committed operations use exact recovery and canonical reopen.")
    if decision == "accept":
        validation = current["validation"]
        require(validation and validation["eligible"] and validation["validation_sha256"] == validation_sha256,
                "validation_required", "Exact eligible validation is required before review acceptance.")
        from ontology_proposal_validation import assert_review_current
        assert_review_current(root, current)
        review = {"schema_version": 1, "proposal_id": proposal_id, "revision": expected_revision,
                  "revision_sha256": current["revision"]["revision_sha256"],
                  "validation_sha256": validation_sha256, "preview_sha256": validation["preview"]["preview_sha256"],
                  "candidate_sha256": current["revision"]["candidate_sha256"],
                  "target_snapshot": validation["target_snapshot"], "at": utc_now(), "reason": reason,
                  "meaning": "Reviewed candidate only; current publisher authorization and actual receipt remain required."}
        return _event(root, proposal_id, expected_revision, decision, {"reason": reason}, review=review)
    if decision == "supersede":
        identity(superseded_by)
        require(superseded_by != proposal_id, "proposal_identity", "A proposal cannot supersede itself.")
        open_proposal(root, superseded_by)
    return _event(root, proposal_id, expected_revision, decision, {"reason": reason, "superseded_by": superseded_by})


def stage_rdf_import(root, staged, source_reference, reason, target_extension=None):
    """Retain all imported quads; convert only the exactly representable axiom subset."""
    root = _root(root)
    project = load_project(root)
    require(isinstance(staged, dict) and staged.get("status") == "staged" and staged.get("complete") is True
            and staged.get("proposal_kind") == "rdf-import" and staged.get("approved") is False,
            "rdf_import_incomplete", "Only a completed attributed standards import can enter durable staging.")
    _evidence(project, [source_reference])
    source = read_bytes(safe_path(root, source_reference["path"]), max_bytes=500000)
    require(sha256(source) == staged.get("content_sha256") and sha256(canonical_bytes(staged.get("quads"))) == staged.get("semantic_sha256"),
            "rdf_import_changed", "Staged content/semantic hashes differ from the selected exact source.")
    require(isinstance(reason, str) and 0 < len(reason.strip()) <= 4000, "proposal_reason", "Explain the selected RDF import.")
    import_id = "ONTRDF-" + uuid.uuid4().hex
    findings = copy.deepcopy(staged.get("diagnostics", []))
    if staged.get("unsupported_constructs"):
        findings.append({"code": "rdf_unsupported_semantics", "message": "The parser identified constructs outside the supported semantic profile."})
    from ontology_advanced import AXIOMS, load_advanced, term
    from ontology_rdf import graph_ids
    rows = staged["quads"]
    expected_graph = graph_ids(project.project_id)["asserted"]
    for index, quad in enumerate(rows):
        require(isinstance(quad, list) and len(quad) == 4, "rdf_import_shape", "Each imported quad must retain its four RDF terms.")
        s,p,o,g = quad
        for value in quad:
            term(value, blank=True)
        if not all(isinstance(value, str) for value in quad):
            findings.append({"code": "rdf_staged_term", "message": "Blank nodes and literals retain exact RDF terms in staging; no v1/core coercion is allowed.", "quad": index})
        elif not s.startswith(project.namespace) or p not in AXIOMS or g != expected_graph:
            findings.append({"code": "rdf_staged_scope", "message": "Only selected project-subject finite axioms in this project's asserted graph can become an extension candidate.", "quad": index})
    candidate, proposal = None, None
    if target_extension is not None:
        cfg = load_advanced(root, required=True)
        require(target_extension in {r["path"] for r in cfg["extensions"]}, "extension_scope", "Select an already locked project extension target.")
        if not findings:
            updated = read_json(safe_path(root, target_extension))
            known = {tuple(r[k] for k in ("subject", "predicate", "object")) for r in updated["axioms"] if isinstance(r["object"], str)}
            for quad in rows:
                triple = tuple(quad[:3])
                if triple not in known:
                    updated["axioms"].append({"id": project.namespace + "import-" + sha256(canonical_bytes(quad))[:24],
                                              "subject": quad[0], "predicate": quad[1], "object": quad[2], "sources": [source_reference]})
                    known.add(triple)
            parts = updated["version"].split(".")
            updated["version"] = ".".join(parts[:2] + [str(int(parts[2]) + 1)])
            extension_bytes = canonical_bytes(updated)
            cfg["extensions"] = [{**r, "sha256": sha256(extension_bytes)} if r["path"] == target_extension else r for r in cfg["extensions"]]
            candidate = {"schema_version": 2, "operation_id": "ONTOP-rdf-" + uuid.uuid4().hex,
                         "operation": "publish", "reason": reason,
                         "changes": [{"path": path, "expected_sha256": sha256(safe_path(root, path)),
                                      "content": raw.decode(), "sha256": sha256(raw)}
                                     for path,raw in ((target_extension, extension_bytes), ("ontology-advanced.yaml", canonical_bytes(cfg)))]}
            proposal = save(root, candidate, rationale=reason, evidence=[source_reference], uncertainty=[],
                            generator={"kind": "rdf_import", "import_id": import_id, "semantic_sha256": staged["semantic_sha256"], "runtime_invoked": False})
    artifact = _sealed({"schema_version": 1, "import_id": import_id, "project_id": project.project_id,
                        "created_at": utc_now(), "source": source_reference, "source_content": source.decode("utf-8"),
                        "reason": reason, "staged": copy.deepcopy(staged), "diagnostics": findings,
                        "approved": False, "target_extension": target_extension,
                        "proposal_id": proposal["head"]["proposal_id"] if proposal else None,
                        "disposition": "candidate_created" if proposal else "staged_only"}, "import_sha256")
    relative = STORE + "rdf-imports/" + import_id + ".json"
    _append(root, relative, artifact)
    return {"status": artifact["disposition"], "approved": False, "import": artifact,
            "path": relative, "proposal": proposal}


def read_rdf_import(root, import_id):
    require(isinstance(import_id, str) and re.fullmatch(r"ONTRDF-[a-f0-9]{32}", import_id), "rdf_import_identity", "Select an exact ONTRDF identity.")
    return _verify(read_json(safe_path(_root(root), STORE + "rdf-imports/" + import_id + ".json")), "import_sha256")


def list_rdf_imports(root):
    folder = safe_path(_root(root), STORE + "rdf-imports", must_exist=False)
    if not folder.exists():
        return []
    return [read_rdf_import(root, path.stem) for path in sorted(folder.iterdir()) if path.name.startswith("ONTRDF-") and path.suffix == ".json"]
