"""Immutable memory inputs using the existing Task evidence contracts."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from memory_core import MemoryError, load_config, load_record, reject_sensitive
from memory_paths import safe_path, safe_read_bytes, relative_path, corpus_allowed
from memory_normalization import digest, normalize_document

MAX_BYTES = 250000
MAX_REFS = 200


def _require(condition, code, message):
    if not condition:
        raise MemoryError(code, message)


def _task(root, task_path):
    p = relative_path(task_path)
    _require(len(p.parts) == 3 and p.parts[0] == "Tasks" and p.name == "task.json", "invalid_task", "Supply the exact canonical Task path.")
    raw = safe_read_bytes(root, task_path)
    helper = safe_path(root, ".agents/skills/agent-task/scripts/task_state.py", must_exist=False)
    _require(helper.is_file(), "task_helper_unavailable", "The owning Agent Task helper is required for packet validation.")
    run = subprocess.run([sys.executable, str(helper), "--project-root", str(root), "show", p.parts[1]],
                         text=True, capture_output=True, timeout=30,
                         env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        value = json.loads(run.stdout)
    except ValueError:
        raise MemoryError("invalid_task", "Task helper did not return a valid inspection receipt.") from None
    _require(run.returncode == 0 and value.get("status") == "ok", "invalid_task", "The current Task does not pass its helper's read-only inspection.")
    _require(raw == safe_read_bytes(root, task_path), "task_changed", "Task changed during inspection.")
    return value["task"], digest(raw)


def _manager(root, task_path, execution_id, generation, actor):
    task, sha = _task(root, task_path)
    o = task.get("orchestration", {})
    manager = o.get("assignments", {}).get(o.get("manager_id"), {})
    _require(o.get("stage") == "active" and o.get("execution_id") == execution_id and o.get("generation") == generation
             and o.get("writer") == actor and manager.get("native_id") == actor
             and manager.get("role_reads") and manager.get("state") == "active",
             "publisher_not_current", "Only the confirmed current manager can freeze Task memory inputs.")
    return task, o, manager, sha


def _reference(root, ref):
    _require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "invalid_reference", "Evidence references have exactly path and sha256.")
    raw = safe_read_bytes(root, ref["path"], max_bytes=MAX_BYTES)
    _require(digest(raw) == ref["sha256"], "stale_packet", "A frozen input changed; manager reconciliation and input rebinding are required.")
    return raw


def _forbidden(o, task_path):
    """Current solver/reviewer/synthesis/proposal products cannot seed recall."""
    paths, hashes = set(), set()
    for aid, assignment in o["assignments"].items():
        if assignment["function"] == "manager":
            continue
        paths.update(assignment["fit"]["writes"])
        for artifact in o["artifacts"].values():
            if artifact.get("assignment_id") == aid:
                for key in ("source_path", "path"):
                    if artifact.get(key):
                        paths.add(artifact[key])
                if artifact.get("sha256"):
                    hashes.add(artifact["sha256"])
    paths.add(str(Path(task_path).parent / "artifacts/orchestration/work"))
    return paths, hashes


def _overlap(path, prefixes):
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def build_packet(root, *, task_path, execution_id, generation, actor, record_ids=None,
                 allowed_sources=(), query=None, max_records=20, max_bytes=200000, config=None,
                 subtask_id=None, revision_reason=None):
    """Build a value only. The manager explicitly publishes and registers it."""
    from memory_search import collect_documents, lexical_score
    config = config or load_config(root)
    task, o, manager, task_sha = _manager(root, task_path, execution_id, generation, actor)
    prior = [a for a in o["assignments"].values() if a["function"] == "solver"
             and (subtask_id is None or a["subtask_id"] == subtask_id)]
    if prior:
        _require(isinstance(revision_reason, str) and bool(revision_reason.strip())
                 and all(a["state"] in {"completed", "stopped", "failed", "revoked"} and a["observations"] for a in prior),
                 "packet_dispatch_started", "Freeze before initial solvers; revised packets need reconciled owners and an explicit material-change reason.")
    _require(type(max_records) is int and 0 <= max_records <= 100 and type(max_bytes) is int and 1024 <= max_bytes <= MAX_BYTES,
             "invalid_packet_limit", "Packet limits exceed the existing Task evidence bounds.")
    _require(isinstance(allowed_sources, (tuple, list)) and len(allowed_sources) <= MAX_REFS, "invalid_reference", "Too many explicit sources.")
    forbidden_paths, forbidden_hashes = _forbidden(o, task_path)
    documents, limitations = collect_documents(root, config)
    selected, refs, exclusions = [], {}, []
    wanted = set(record_ids) if record_ids is not None else None
    for doc in documents:
        if doc["kind"] != "memory":
            continue
        m = doc["metadata"]
        if wanted is not None and m["id"] not in wanted:
            continue
        if query and not any(lexical_score(s["text"], query) for s in doc["segments"]):
            continue
        ineligible = (m["origin"]["execution_id"] == execution_id or m["state"] != "active"
                      or doc["sha256"] in forbidden_hashes or _overlap(doc["path"], forbidden_paths)
                      or any(_overlap(s["path"], forbidden_paths) or s["sha256"] in forbidden_hashes for s in m["sources"]))
        if ineligible:
            exclusions.append({"id": m["id"], "reason": "current_execution_or_nonactive"})
            continue
        # Exact source versions are required in a frozen input, independent of recall rank.
        try:
            for source in m["sources"]:
                ref = {"path": source["path"], "sha256": source["sha256"]}
                _reference(root, ref)
                refs[ref["path"]] = ref
        except MemoryError:
            exclusions.append({"id": m["id"], "reason": "source_unavailable_or_changed"})
            continue
        selected.append(doc)
    selected.sort(key=lambda d: d["metadata"]["id"])
    selected = selected[:max_records]
    if wanted is not None:
        _require(wanted == {d["metadata"]["id"] for d in selected}, "ineligible_memory", "Some requested records are absent, stale, excluded or beyond the packet limit.")
    # Recompute references after selection so truncation does not grant extra sources.
    refs = {}
    for doc in selected:
        refs[doc["path"]] = {"path": doc["path"], "sha256": doc["sha256"]}
        for source in doc["metadata"]["sources"]:
            refs[source["path"]] = {"path": source["path"], "sha256": source["sha256"]}
    for ref in allowed_sources:
        _reference(root, ref)
        _require(corpus_allowed(ref["path"], config) and not _overlap(ref["path"], forbidden_paths)
                 and ref["sha256"] not in forbidden_hashes, "excluded_source", "Additional source is outside the permitted frozen corpus.")
        doc = normalize_document(root, ref["path"], config)
        reject_sensitive("\n".join(s["text"] for s in doc["segments"]))
        selected.append(doc)
        refs[ref["path"]] = ref
    _require(len(refs) <= MAX_REFS, "packet_too_large", "Packet references exceed the Task limit.")
    packet = {"schema_version": 1, "kind": "sys4ai-memory-context", "project_id": config["project"]["id"],
              "created_at": datetime.now(timezone.utc).isoformat(),
              "task": {"path": task_path, "id": task["task_id"], "execution_id": execution_id,
                       "generation": generation, "manager": actor, "inspected_sha256": task_sha,
                       "subtask_id": subtask_id, "revision_reason": revision_reason},
              "config_sha256": digest(safe_read_bytes(root, "memory.yaml")),
              "limits": {"max_records": max_records, "max_bytes": max_bytes},
              "documents": selected, "references": sorted(refs.values(), key=lambda r: r["path"]),
              "excluded": exclusions, "empty": not selected,
              "authority": "Frozen source data. Current Task, role and user authority remain controlling."}
    _require(len(packet_bytes(packet)) <= max_bytes, "packet_too_large", "Narrow the selected memories and explicit sources.")
    return packet


def packet_bytes(packet):
    return (json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def freeze_packet(root, packet, output, *, actor):
    config = load_config(root)
    t = packet["task"]
    _, _, manager, _ = _manager(root, t["path"], t["execution_id"], t["generation"], actor)
    validate_packet_value(root, config, packet)
    _require(_overlap(output, manager["fit"]["writes"]), "packet_scope", "Output is outside the manager's current write scope.")
    data = packet_bytes(packet)
    from memory_recovery import project_lock, atomic_replace
    with project_lock(root):
        _manager(root, t["path"], t["execution_id"], t["generation"], actor)
        validate_packet_value(root, config, packet)
        _require(not safe_path(root, output, must_exist=False).exists(), "packet_exists", "Frozen packet output already exists; use a new attributable version.")
        atomic_replace(root, output, data, None)
    return {"path": output, "sha256": digest(data)}


def validate_packet_value(root, config, packet):
    required = {"schema_version", "kind", "project_id", "created_at", "task", "config_sha256", "limits", "documents", "references", "excluded", "empty", "authority"}
    _require(isinstance(packet, dict) and set(packet) == required and packet["schema_version"] == 1
             and packet["kind"] == "sys4ai-memory-context" and packet["project_id"] == config["project"]["id"],
             "invalid_packet", "Packet identity or schema is invalid.")
    _require(isinstance(packet["documents"], list) and isinstance(packet["references"], list)
             and isinstance(packet["task"], dict) and set(packet["task"]) == {"path", "id", "execution_id", "generation", "manager", "inspected_sha256", "subtask_id", "revision_reason"}
             and isinstance(packet["limits"], dict) and set(packet["limits"]) == {"max_records", "max_bytes"},
             "invalid_packet", "Packet content shape is invalid.")
    _require(digest(safe_read_bytes(root, "memory.yaml")) == packet["config_sha256"], "stale_packet", "Memory configuration changed; review and rebind frozen inputs.")
    _require(len(packet_bytes(packet)) <= MAX_BYTES and len(packet["references"]) <= MAX_REFS,
             "packet_too_large", "Packet exceeds existing Task evidence limits.")
    refs = {}
    for ref in packet["references"]:
        _reference(root, ref)
        refs[ref["path"]] = ref["sha256"]
    for doc in packet["documents"]:
        _require(isinstance(doc, dict) and {"path", "sha256", "segments", "kind", "source_identity"} <= set(doc), "invalid_packet", "Packet document is incomplete.")
        _require(refs.get(doc["path"]) == doc["sha256"], "invalid_packet", "Packet document has no exact input reference.")
        if doc["kind"] == "memory":
            live = load_record(root, doc["path"], config)
            meta = live["metadata"]
            expected = [{"text": meta["title"] + "\n" + live["body"], "heading": meta["title"], "locator": live["path"]}]
            _require(meta == doc.get("metadata") and meta["state"] == "active"
                     and meta["origin"]["execution_id"] != packet["task"]["execution_id"]
                     and doc["source_identity"] == meta["id"] and doc["segments"] == expected,
                     "invalid_packet", "Curated packet content differs from eligible canonical memory.")
            for source in meta["sources"]:
                _require(refs.get(source["path"]) == source["sha256"], "invalid_packet", "A memory citation is outside the frozen references.")
        else:
            _require(doc["kind"] == "source", "invalid_packet", "Unsupported packet document kind.")
            live = normalize_document(root, doc["path"], config)
            _require(doc["segments"] == live["segments"] and doc["source_identity"] == live["source_identity"],
                     "invalid_packet", "Packet text differs from its cited source bytes.")
        reject_sensitive("\n".join(s["text"] for s in doc["segments"]))
    return packet


def load_packet(root, packet_ref, config=None):
    config = config or load_config(root)
    raw = _reference(root, packet_ref)
    try:
        packet = json.loads(raw)
    except ValueError:
        raise MemoryError("invalid_packet", "Packet is not valid JSON.") from None
    return validate_packet_value(root, config, packet)


def filter_documents(root, config, documents, packet_ref):
    packet = load_packet(root, packet_ref, config)
    allowed = {(d["path"], d["sha256"]) for d in packet["documents"]}
    return [d for d in documents if (d["path"], d["sha256"]) in allowed]


def validate_assignment(root, packet_ref, *, task_path, assignment_id):
    packet = load_packet(root, packet_ref)
    task, _ = _task(root, task_path)
    o = task.get("orchestration", {})
    t = packet["task"]
    _require(t["path"] == task_path and t["id"] == task["task_id"] and t["execution_id"] == o.get("execution_id")
             and t["generation"] == o.get("generation") and t["manager"] == o.get("writer") and o.get("stage") == "active",
             "stale_packet", "Packet belongs to a different or inactive Task execution.")
    a = o.get("assignments", {}).get(assignment_id, {})
    _require(a and packet_ref in a.get("context", []), "packet_not_bound", "Assignment does not contain this exact packet reference.")
    subtask = o["subtasks"][a["subtask_id"]]
    _require(packet_ref in subtask["baseline"]["inputs"] and a["baseline"] == subtask["digest"]
             and a["round"] == subtask["round"], "packet_not_bound", "Packet is outside the current subtask baseline.")
    return {"status": "bound", "assignment_id": assignment_id, "packet": packet_ref,
            "baseline": subtask["digest"], "round": subtask["round"], "mutated": False}


def search_packet(root, packet_ref, query, limit=None):
    from memory_search import rank_documents
    packet = load_packet(root, packet_ref)
    limit = 20 if limit is None else limit
    _require(type(limit) is int and 1 <= limit <= 200, "invalid_limit", "Packet result limit must be between 1 and 200.")
    results = rank_documents(packet["documents"], query, limit)
    return {"status": "ok" if results else "no_match" if packet["documents"] else "empty", "mode": "frozen-lexical",
            "project_id": packet["project_id"], "packet": packet_ref, "results": results,
            "mutated": False, "limitations": ["Only the exact frozen memory inputs are searched; changed inputs require manager reconciliation."]}


def assess_change(old_packet, new_packet, reason):
    _require(isinstance(reason, str) and bool(reason.strip()), "reason_required", "Record the materiality assessment reason.")
    old = {"documents": old_packet["documents"], "references": old_packet["references"], "config": old_packet["config_sha256"]}
    new = {"documents": new_packet["documents"], "references": new_packet["references"], "config": new_packet["config_sha256"]}
    material = old != new
    return {"material": material, "reason": reason, "mutated": False,
            "required_actions": ["Reconcile running owners", "Revise the canonical subtask baseline", "Rebind every affected assignment through assignment.inputs", "Repeat invalidated review, synthesis, acceptance and implementation gates"] if material else [],
            "task_events_replayed": False}
