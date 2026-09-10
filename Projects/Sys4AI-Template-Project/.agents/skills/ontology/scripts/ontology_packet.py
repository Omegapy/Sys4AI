"""Immutable selected ontology inputs using existing Task references and ownership."""
import copy
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

from ontology_core import (OntologyError, Project, canonical_bytes, load_config, load_project,
                           read_bytes, read_json, require, safe_path, sha256, source_status)
from ontology_retrieval import limits, ranked

MAX_BYTES = 250000
MAX_REFS = 200


def _task(root, task_path):
    path = PurePosixPath(task_path)
    require(len(path.parts) == 3 and path.parts[0] == "Tasks" and path.name == "task.json",
            "invalid_task", "Supply the exact canonical Tasks/<folder>/task.json path.")
    raw = read_bytes(safe_path(root, task_path), max_bytes=16_000_000)
    helper = safe_path(root, ".agents/skills/agent-task/scripts/task_state.py")
    try:
        run = subprocess.run([sys.executable, "-B", str(helper), "--project-root", str(root), "show", path.parts[1]],
                             capture_output=True, text=True, timeout=30,
                             env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    except (OSError, subprocess.TimeoutExpired) as error:
        raise OntologyError("task_helper_unavailable", "The current Task helper could not inspect ownership.") from error
    try:
        result = json.loads(run.stdout)
    except ValueError:
        raise OntologyError("invalid_task", "Task helper returned no valid inspection receipt.") from None
    require(run.returncode == 0 and result.get("status") == "ok", "invalid_task", "Task failed its owning helper's read-only inspection.")
    require(raw == read_bytes(safe_path(root, task_path), max_bytes=16_000_000), "task_changed", "Task changed during inspection.")
    return result["task"], sha256(raw)


def _manager(root, task_path, execution_id, generation, actor):
    task, digest = _task(root, task_path)
    o = task.get("orchestration", {})
    manager = o.get("assignments", {}).get(o.get("manager_id"), {})
    require(o.get("stage") == "active" and o.get("execution_id") == execution_id
            and type(generation) is int and o.get("generation") == generation
            and o.get("writer") == actor and manager.get("native_id") == actor
            and manager.get("state") == "active" and manager.get("role_reads"),
            "publisher_not_current", "Only the confirmed current manager can freeze ontology Task inputs.")
    return task, o, manager, digest


def _overlap(path, prefixes):
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def _forbidden(o, task_path):
    paths, digests = {str(PurePosixPath(task_path).parent / "artifacts/orchestration/work"), "ONTOLOGY/proposals"}, set()
    for aid, assignment in o["assignments"].items():
        if assignment["function"] == "manager":
            continue
        paths.update(assignment["fit"]["writes"])
        for artifact in o["artifacts"].values():
            if artifact.get("assignment_id") == aid:
                paths.update(p for p in (artifact.get("source_path"), artifact.get("path")) if p)
                if artifact.get("sha256"):
                    digests.add(artifact["sha256"])
    return paths, digests


def _reference(root, ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "invalid_reference", "Task references have exactly path and sha256.")
    raw = read_bytes(safe_path(root, ref["path"]), max_bytes=MAX_BYTES)
    require(sha256(raw) == ref["sha256"], "stale_packet", "A frozen reference changed; manager reassessment and input rebinding are required.", path=ref["path"])
    return raw


def build_packet(root, *, task_path, execution_id, generation, actor, concept_ids=None, query=None,
                 allowed_sources=(), max_records=100, max_bytes=MAX_BYTES, subtask_id=None, revision_reason=None,
                 advanced=False, graph_selection=("asserted",), inference_goals=(), extension_ids=(), semantic_queries=()):
    require(all(isinstance(v, str) and v for v in (task_path, execution_id, actor)), "invalid_task", "Task path, execution and actor must be nonempty strings.")
    require(concept_ids is None or isinstance(concept_ids, (list, tuple)) and all(isinstance(i, str) for i in concept_ids), "invalid_selection", "Select stable IDs using a list of strings.")
    p = load_project(root)
    task, o, manager, task_sha = _manager(p.root, task_path, execution_id, generation, actor)
    prior = [a for a in o["assignments"].values() if a["function"] == "solver" and
             (subtask_id is None or a["subtask_id"] == subtask_id)]
    if prior:
        require(isinstance(revision_reason, str) and bool(revision_reason.strip()) and
                all(a["state"] in {"completed", "stopped", "failed", "revoked"} and a["observations"] for a in prior),
                "packet_dispatch_started", "Freeze before solver dispatch; revised packets require reconciled owners and a reason.")
    require(type(max_records) is int and 0 <= max_records <= 100 and type(max_bytes) is int and 1024 <= max_bytes <= MAX_BYTES,
            "invalid_packet_limit", "Packet bounds exceed the current Task artifact limits.")
    require(concept_ids is not None or query is not None, "packet_selection_required", "Select concept IDs, a query, or an explicit empty ID list.")
    selected = set(concept_ids or [])
    if query:
        rows = ranked(p, query, kinds={"concept", "instance"})
        if rows:
            selected.update(r["@id"] for m, r in rows if m[:2] == rows[0][0][:2])
    require(selected <= set(p.by_id), "unknown_concept", "A selected stable identity is absent from the project ontology.")
    initial = set(selected)
    for relation in p.relations:
        if relation["subject"] in initial or relation["object"] in initial:
            selected.update((relation["@id"], relation["subject"], relation["predicate"], relation["object"]))
    for identity in list(selected):
        replacement = p.by_id[identity].get("replacement")
        if replacement:
            selected.add(replacement)
    for record in p.records:
        if record["kind"] == "binding" and record["entity"] in selected:
            selected.add(record["@id"])
    require(len(selected) <= max_records, "packet_too_large", "Selected context and immediate relationship endpoints exceed the record bound.")
    records = [copy.deepcopy(p.by_id[i]) for i in sorted(selected)]
    forbidden_paths, forbidden_hashes = _forbidden(o, task_path)
    refs = {}
    def add_reference(path, digest):
        require(not _overlap(path, forbidden_paths) and digest not in forbidden_hashes, "excluded_source", "Sibling candidate, review, synthesis or proposal sources cannot seed a packet.", path=path)
        ref = {"path": path, "sha256": digest}
        _reference(p.root, ref)
        refs[path] = ref
    add_reference("ontology.yaml", p.snapshot["inputs"]["ontology.yaml"])
    add_reference(p.config["context"]["path"], p.config["context"]["sha256"])
    for module in p.modules:
        add_reference(module["path"] + "/manifest.json", module["manifest_sha256"])
    sources = []
    source_keys = set()
    for record in records:
        owner = p.locations[record["@id"]].split("#", 1)[0]
        add_reference(owner, p.snapshot["inputs"][owner])
        for source in record["sources"]:
            status = source_status(p, source)
            require(status["status"] == "current", "stale_source", "Frozen definitions require current exact sources.", path=source["path"])
            add_reference(source["path"], source["sha256"])
            key = canonical_bytes(source)
            if key not in source_keys:
                sources.append(copy.deepcopy(source)); source_keys.add(key)
    require(isinstance(allowed_sources, (list, tuple)) and len(allowed_sources) <= MAX_REFS,
            "invalid_reference", "Explicit permitted sources exceed the reference limit.")
    documents = []
    for ref in allowed_sources:
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "invalid_reference", "Explicit permitted references have exactly path and sha256.")
        require(ref["path"] in p.config["source_allowlist"], "excluded_source", "Additional source is not in the exact ontology allowlist.", path=ref["path"])
        add_reference(ref["path"], ref["sha256"])
        documents.append({**ref, "text": _reference(p.root, ref).decode("utf-8")})
    require(len(refs) <= MAX_REFS, "packet_too_large", "Packet exceeds 200 exact Task references.")
    snapshot = copy.deepcopy(p.snapshot)
    snapshot["inputs"].update({ref["path"]: ref["sha256"] for ref in allowed_sources})
    packet = {"schema_version": 1, "kind": "sys4ai-ontology-context", "project_id": p.project_id,
              "task": {"path": task_path, "id": task["task_id"], "execution_id": execution_id,
                       "generation": generation, "manager": actor, "inspected_sha256": task_sha,
                       "subtask_id": subtask_id, "revision_reason": revision_reason},
              "selection": sorted(initial), "records": records,
              "locations": {r["@id"]: p.locations[r["@id"]] for r in records},
              "config": p.config, "modules": p.modules, "snapshot": snapshot,
              "sources": sorted(sources, key=lambda s: (s["path"], s["locator"])),
              "documents": sorted(documents, key=lambda d: d["path"]),
              "references": sorted(refs.values(), key=lambda r: r["path"]),
              "limits": {"max_records": max_records, "max_bytes": max_bytes}, "empty": not records,
              "authority": "Frozen semantic data. Current Task, role and user authority remain controlling."}
    require(len(canonical_bytes(packet)) <= max_bytes, "packet_too_large", "Narrow selected concepts and explicit sources to fit the Task artifact bound.")
    if advanced:
        from ontology_advanced_packet import extend_packet
        return extend_packet(root, packet, graph_selection=graph_selection, goals=inference_goals,
                             extension_ids=extension_ids, semantic_queries=semantic_queries)
    return packet


def validate_packet_value(root, packet):
    if isinstance(packet, dict) and packet.get("schema_version") == 2:
        from ontology_advanced_packet import validate_advanced
        return validate_advanced(root, packet)
    required = {"schema_version", "kind", "project_id", "task", "selection", "records", "locations", "config", "modules", "snapshot", "sources", "documents", "references", "limits", "empty", "authority"}
    require(isinstance(packet, dict) and set(packet) == required and packet["schema_version"] == 1 and packet["kind"] == "sys4ai-ontology-context", "invalid_packet", "Packet schema or kind is invalid.")
    require(isinstance(packet["task"], dict) and set(packet["task"]) == {"path", "id", "execution_id", "generation", "manager", "inspected_sha256", "subtask_id", "revision_reason"}
            and isinstance(packet["selection"], list) and isinstance(packet["locations"], dict)
            and isinstance(packet["sources"], list) and isinstance(packet["documents"], list)
            and isinstance(packet["modules"], list) and isinstance(packet["snapshot"], dict)
            and isinstance(packet["limits"], dict) and set(packet["limits"]) == {"max_records", "max_bytes"}, "invalid_packet", "Frozen packet fields are malformed.")
    require(all(isinstance(packet["task"][k], str) and packet["task"][k] for k in ("path", "id", "execution_id", "manager", "inspected_sha256"))
            and type(packet["task"]["generation"]) is int and all(isinstance(i, str) for i in packet["selection"])
            and all(isinstance(v, str) for v in packet["locations"].values()), "invalid_packet", "Frozen Task identity and record locations must be exact strings.")
    require(type(packet["limits"]["max_records"]) is int and 0 <= packet["limits"]["max_records"] <= 100
            and type(packet["limits"]["max_bytes"]) is int and 1024 <= packet["limits"]["max_bytes"] <= MAX_BYTES,
            "invalid_packet_limit", "Frozen packet limits are invalid.")
    require(len(canonical_bytes(packet)) <= packet["limits"]["max_bytes"] and isinstance(packet["references"], list) and len(packet["references"]) <= MAX_REFS,
            "packet_too_large", "Packet exceeds existing Task evidence limits.")
    config = load_config(Path(root), packet["project_id"])
    permitted_refs = {"ontology.yaml", config["context"]["path"], *config["source_allowlist"], *config["project_files"], *config["binding_files"]}
    for selected in config["modules"]:
        manifest_path = selected["path"] + "/manifest.json"
        manifest = read_json(safe_path(root, manifest_path))
        require(isinstance(manifest, dict) and isinstance(manifest.get("files"), dict), "invalid_packet", "Selected module manifest is malformed.")
        permitted_refs.add(manifest_path)
        permitted_refs.update(selected["path"] + "/" + name for name in manifest["files"])
    refs = {}
    for ref in packet["references"]:
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"} and isinstance(ref["path"], str) and isinstance(ref["sha256"], str) and ref["path"] in permitted_refs,
                "excluded_source", "Frozen input is outside explicitly permitted canonical and source paths.")
        raw = _reference(root, ref)
        require(ref["path"] not in refs, "invalid_packet", "Duplicate frozen source reference.")
        refs[ref["path"]] = raw
    require("ontology.yaml" in refs and json.loads(refs["ontology.yaml"]) == packet["config"], "invalid_packet", "Packet configuration differs from exact frozen source bytes.")
    require(config == packet["config"], "stale_packet", "Project configuration changed; manager input rebinding is required.")
    require(packet["project_id"] == config["project"]["id"] and isinstance(packet["records"], list), "invalid_packet", "Packet project identity is invalid.")
    require(len(packet["records"]) <= packet["limits"]["max_records"] and all(isinstance(r, dict) and {"@id", "sources"} <= set(r) and isinstance(r["@id"], str) and isinstance(r["sources"], list) for r in packet["records"]), "invalid_packet", "Frozen record selection is malformed or exceeds limits.")
    require(packet["empty"] == (not packet["records"]) and set(packet["selection"]) <= {r["@id"] for r in packet["records"]}, "invalid_packet", "Frozen empty flag or initial selection is inconsistent.")
    canonical_owners = set(config["project_files"] + config["binding_files"])
    require(len(packet["modules"]) == len(config["modules"]), "invalid_packet", "Frozen module selection differs from configuration.")
    for module, selected in zip(packet["modules"], config["modules"]):
        require(isinstance(module, dict) and all(module.get(k) == selected[k] for k in ("id", "version", "path", "sha256")), "invalid_packet", "Frozen module identity differs from its selected lock.")
        manifest_path = module["path"] + "/manifest.json"
        require(manifest_path in refs and sha256(refs[manifest_path]) == module.get("manifest_sha256"), "invalid_packet", "Frozen module manifest is not bound.")
        manifest = json.loads(refs[manifest_path])
        require(module.get("files") == manifest["files"], "invalid_packet", "Frozen module file versions differ from its manifest.")
        canonical_owners.update(module["path"] + "/" + name for name in manifest["record_files"])
    require(set(packet["locations"]) == {r["@id"] for r in packet["records"]} and len(packet["locations"]) == len(packet["records"]), "invalid_packet", "Frozen record locations or identities are incomplete.")
    for record in packet["records"]:
        owner, _, pointer = packet["locations"][record["@id"]].partition("#")
        require(owner in refs and owner in canonical_owners, "invalid_packet", "Frozen definition has no permitted exact canonical owner reference.")
        try:
            current = json.loads(refs[owner])
            for part in pointer.strip("/").split("/"):
                current = current[int(part)] if isinstance(current, list) else current[part]
        except (ValueError, KeyError, IndexError, TypeError):
            raise OntologyError("invalid_packet", "Frozen canonical record locator is invalid.") from None
        require(current == record, "invalid_packet", "Frozen record text differs from its exact canonical source.")
        for source in record["sources"]:
            require(source["path"] in refs and sha256(refs[source["path"]]) == source["sha256"], "invalid_packet", "Frozen definition citation is outside its exact permitted sources.")
    for document in packet["documents"]:
        require(isinstance(document, dict) and set(document) == {"path", "sha256", "text"}, "invalid_packet", "Malformed frozen source document.")
        require(document["path"] in config["source_allowlist"] and document["path"] in refs and
                sha256(refs[document["path"]]) == document["sha256"] and refs[document["path"]].decode("utf-8") == document["text"],
                "invalid_packet", "Frozen current-source text differs from permitted exact bytes.")
    expected_sources = {canonical_bytes(s) for record in packet["records"] for s in record["sources"]}
    require({canonical_bytes(s) for s in packet["sources"]} == expected_sources, "invalid_packet", "Frozen source metadata differs from selected record citations.")
    require(isinstance(packet["snapshot"].get("inputs"), dict) and all(packet["snapshot"]["inputs"].get(ref["path"]) == ref["sha256"] for ref in packet["references"]),
            "invalid_packet", "Frozen snapshot versions differ from exact references.")
    actual_helpers = {f.name: sha256(f) for f in sorted(Path(__file__).parent.glob("ontology*.py")) if not f.is_symlink()}
    require(packet["snapshot"].get("helpers") == actual_helpers, "stale_packet", "Ontology helper versions changed; rebind frozen inputs.")
    return packet


def freeze_packet(root, packet, output, *, actor):
    validate_packet_value(root, packet)
    t = packet["task"]
    _, _, manager, task_sha = _manager(root, t["path"], t["execution_id"], t["generation"], actor)
    require(task_sha == t["inspected_sha256"], "task_changed", "Task changed after packet selection; rebuild before freezing.")
    require(t["manager"] == actor and _overlap(output, manager["fit"]["writes"]), "packet_scope", "Packet output is outside its confirmed manager's write scope.")
    require(output not in {r["path"] for r in packet["references"]} and output.endswith(".json"), "packet_scope", "Use a new JSON artifact path, never a canonical input.")
    target = safe_path(root, output, must_exist=False)
    require(not target.exists(), "packet_exists", "Frozen packets are immutable; select a new versioned artifact path.")
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_path(root, output, must_exist=False)
    data = canonical_bytes(packet)
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise OntologyError("packet_exists", "Frozen packet output already exists.") from None
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
    except OSError:
        target.unlink()
        raise
    return {"path": output, "sha256": sha256(data)}


def load_packet(root, packet_ref):
    try:
        value = json.loads(_reference(root, packet_ref))
    except ValueError:
        raise OntologyError("invalid_packet", "Frozen ontology packet is not valid JSON.") from None
    return validate_packet_value(root, value)


def frozen_project(root, packet_ref):
    value = load_packet(root, packet_ref)
    records = copy.deepcopy(value["records"])
    p = Project(Path(root), copy.deepcopy(value["config"]), records, {r["@id"]: r for r in records},
                [r for r in records if r["kind"] == "relation"], copy.deepcopy(value["modules"]),
                copy.deepcopy(value["locations"]), snapshot=copy.deepcopy(value["snapshot"]))
    p.sources = [source_status(p, s) for s in value["sources"]]
    p.frozen_packet = value
    p.frozen_reference = packet_ref
    return p


def search_packet(root, packet_ref, query, *, limit=None, max_bytes=None):
    from ontology_retrieval import search
    result = search(frozen_project(root, packet_ref), query, limit=limit, max_bytes=max_bytes)
    result.update(mode="frozen-ontology", packet=packet_ref)
    return result


def frozen_current_sources(p, query, *, limit=None, max_bytes=None):
    from ontology_knowledge import _excerpt
    from ontology_retrieval import envelope
    results = []
    for doc in p.frozen_packet["documents"]:
        excerpt, line, truncated = _excerpt(doc["text"], "", query)
        results.append({"source_type": "current_governance", "path": doc["path"], "sha256": doc["sha256"],
                        "freshness": "current_frozen_version", "excerpt": excerpt, "excerpt_line": line,
                        "excerpt_truncated": truncated, "match_reason": "explicit_frozen_source",
                        "authority": "Exact permitted frozen source; changed versions require manager reassessment."})
    return envelope(p, "current", query, results, limits(p, limit, max_bytes), status="ok" if results else "no_permitted_frozen_source")


def validate_assignment(root, packet_ref, *, task_path, assignment_id):
    packet = load_packet(root, packet_ref)
    task, _ = _task(root, task_path)
    o, t = task.get("orchestration", {}), packet["task"]
    require(t["path"] == task_path and t["id"] == task["task_id"] and t["execution_id"] == o.get("execution_id") and
            t["generation"] == o.get("generation") and t["manager"] == o.get("writer") and o.get("stage") == "active", "stale_packet", "Packet belongs to a different or inactive Task execution.")
    prefix = str(PurePosixPath(task_path).parent)
    registered = [a for a in o["artifacts"].values() if prefix + "/" + a["path"] == packet_ref["path"] and a["sha256"] == packet_ref["sha256"]]
    require(registered and all(a["assignment_id"] == o["manager_id"] for a in registered), "packet_unregistered", "Packet must be the current manager's registered immutable Task artifact.")
    assignment = o["assignments"].get(assignment_id, {})
    require(assignment and packet_ref in assignment.get("context", []), "packet_not_bound", "Assignment lacks the exact frozen packet reference.")
    subtask = o["subtasks"][assignment["subtask_id"]]
    require(packet_ref in subtask["baseline"]["inputs"] and assignment["baseline"] == subtask["digest"] and assignment["round"] == subtask["round"], "packet_not_bound", "Packet is outside the current subtask baseline and round.")
    for peer in o["assignments"].values():
        if peer["function"] == "solver" and peer["subtask_id"] == assignment["subtask_id"] and peer["round"] == assignment["round"]:
            require(packet_ref in peer["context"], "unequal_solver_packet", "Initial solver contexts do not share the same ontology packet reference.")
    return {"status": "bound", "assignment_id": assignment_id, "packet": packet_ref, "baseline": subtask["digest"], "round": subtask["round"], "mutated": False}


def assess_change(old_packet, new_packet, reason):
    require(isinstance(reason, str) and bool(reason.strip()), "reason_required", "Record the manager's materiality assessment reason.")
    old = {r["@id"]: r for r in old_packet["records"]}
    new = {r["@id"]: r for r in new_packet["records"]}
    affected = sorted(i for i in set(old) | set(new) if old.get(i) != new.get(i))
    advanced_changed = old_packet.get("advanced") != new_packet.get("advanced")
    material = bool(affected) or advanced_changed or any(old_packet[k] != new_packet[k] for k in ("references", "config", "documents"))
    return {"material": material, "reason": reason, "affected_meanings": affected, "mutated": False, "task_events_replayed": False,
            "advanced_context_changed": advanced_changed,
            "required_actions": ["Reconcile affected running owners", "Revise the canonical subtask baseline", "Send exact revised input references using native send_message", "Commit assignment.inputs with the actual native message receipt", "Continue through followup_task", "Repeat affected review, synthesis, acceptance and implementation checks"] if material else []}
