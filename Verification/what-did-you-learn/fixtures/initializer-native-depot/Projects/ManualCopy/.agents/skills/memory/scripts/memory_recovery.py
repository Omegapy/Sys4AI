"""Memory-only atomic replacement, durable intent, and exact idempotent recovery."""
from __future__ import annotations

import base64
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import uuid

from memory_paths import MemoryError, require, project_root, relative_path, safe_path, safe_read_bytes
from memory_core import decode_json_yaml, exact, sha256, json_bytes, load_config

JOURNAL_ROOT = ".sys4ai/memory/maintenance/transactions"
LOCK_PATH = ".sys4ai/memory/maintenance/memory.lock"


def _parent_fd(root, rel):
    root = project_root(root)
    parts = relative_path(rel).parts
    safe_path(root, rel, must_exist=False, kind="any")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=descriptor)
                os.fsync(descriptor)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor, parts[-1]
    except OSError as exc:
        os.close(descriptor)
        raise MemoryError("unsafe_write", "Cannot open confined output directory.") from exc


def _current_digest(root, rel):
    path = safe_path(root, rel, must_exist=False)
    return sha256(safe_read_bytes(root, rel)) if path.exists() else None


@contextmanager
def project_lock(root):
    parent, name = _parent_fd(root, LOCK_PATH)
    lock_fd = None
    try:
        lock_fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        require(os.fstat(lock_fd).st_nlink == 1, "unsafe_lock", "Memory lock must not be hard linked.")
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise MemoryError("memory_locked", "A current memory operation owns the project lock.") from exc
        yield
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
        os.close(parent)


def atomic_replace(root, rel, data, expected_sha256, *, before_replace=None):
    require(isinstance(data, bytes), "invalid_write", "Atomic writes require exact bytes.")
    root = project_root(root)
    require(_current_digest(root, rel) == expected_sha256, "record_conflict", "Current bytes differ from the expected version.", {"path": rel})
    parent, name = _parent_fd(root, rel)
    temporary = ".memory-" + uuid.uuid4().hex + ".tmp"
    temp_fd = None
    try:
        temp_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(temp_fd, "wb", closefd=False) as stream:
            stream.write(data); stream.flush(); os.fsync(temp_fd)
        if before_replace:
            before_replace()
        actual_parent = safe_path(root, rel, must_exist=False).parent.stat()
        opened_parent = os.fstat(parent)
        require((actual_parent.st_dev, actual_parent.st_ino) == (opened_parent.st_dev, opened_parent.st_ino), "directory_changed", "Output directory changed during publication.")
        require(_current_digest(root, rel) == expected_sha256, "record_conflict", "A concurrent or human edit changed the target before replacement.", {"path": rel})
        os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)
        require(_current_digest(root, rel) == sha256(data), "post_write_conflict", "Target changed immediately after publication.", {"path": rel})
    finally:
        if temp_fd is not None:
            os.close(temp_fd)
        try:
            os.unlink(temporary, dir_fd=parent)
        except FileNotFoundError:
            pass
        os.close(parent)
    return sha256(data)


def _fault(callback, boundary):
    if callback:
        callback(boundary)


def journal_status(root, journal):
    results = []
    for change in journal["payload"]["changes"]:
        current = _current_digest(root, change["path"])
        if current == change["reviewed_record_sha256"]:
            state = "committed"
        elif current == change["expected_sha256"]:
            state = "pending"
        else:
            state = "conflict"
        results.append({"path": change["path"], "state": state, "sha256": current})
    return results


def _read_journal(root, rel):
    journal = decode_json_yaml(safe_read_bytes(root, rel, max_bytes=16_000_000))
    exact(journal, ("schema_version", "operation_id", "payload_sha256", "payload", "grant", "actor_id", "state", "originals", "redacted_paths", "redaction_sha256", "receipt"))
    require(journal["schema_version"] == 1 and journal["state"] in {"prepared", "complete"}, "invalid_journal", "Unsupported memory journal version or state.")
    require(isinstance(journal["payload"], dict), "invalid_journal", "Journal payload is absent.")
    if journal["redacted_paths"]:
        require(journal["state"] == "complete" and sha256(json_bytes(journal["payload"])) == journal["redaction_sha256"],
                "journal_changed", "Completed redacted history has an invalid sanitized payload digest.")
        for change in journal["payload"]["changes"]:
            if change["path"] in journal["redacted_paths"]:
                require(change["content"] is None, "redaction_incomplete", "Redacted record content remains in a historical payload.")
        for original in journal["originals"]:
            if original["path"] in journal["redacted_paths"]:
                require(original["content_base64"] is None, "redaction_incomplete", "Redacted original remains in history.")
    else:
        require(journal["redaction_sha256"] is None and sha256(json_bytes(journal["payload"])) == journal["payload_sha256"], "journal_changed", "Accepted journal payload no longer matches its reviewed digest.")
    require(journal["operation_id"] == journal["payload"]["operation_id"] and rel == JOURNAL_ROOT + "/" + journal["operation_id"] + ".json", "journal_identity", "Journal identity or path is inconsistent.")
    return journal


def pending_transactions(root):
    path = safe_path(root, JOURNAL_ROOT, must_exist=False, kind="dir")
    if not path.exists():
        return []
    pending = []
    for entry in sorted(path.iterdir()):
        require(entry.name.endswith(".json"), "unclassified_journal", "Unclassified durable maintenance content requires inspection.")
        rel = entry.relative_to(root).as_posix()
        journal = _read_journal(root, rel)
        if journal["state"] != "complete":
            pending.append({"path": rel, "operation_id": journal["operation_id"], "records": journal_status(root, journal)})
    return pending


def _scrub_history(root, paths, current_journal):
    """Scoped privacy redaction removes managed journal copies, retaining hashes."""
    for entry in sorted(safe_path(root, JOURNAL_ROOT, kind="dir").iterdir()):
        rel = entry.relative_to(root).as_posix()
        if rel == current_journal:
            continue
        journal = _read_journal(root, rel)
        involved = {change["path"] for change in journal["payload"]["changes"]} & set(paths)
        if involved:
            require(journal["state"] == "complete", "pending_redaction_history", "Resolve earlier accepted writes before redacting their historical copies.")
            expected = _current_digest(root, rel)
            journal["redacted_paths"] = sorted(set(journal["redacted_paths"]) | involved)
            for change in journal["payload"]["changes"]:
                if change["path"] in involved:
                    change["content"] = None
            for original in journal["originals"]:
                if original["path"] in involved:
                    original["content_base64"] = None
            journal["redaction_sha256"] = sha256(json_bytes(journal["payload"]))
            atomic_replace(root, rel, json_bytes(journal), expected)


def _finish(root, journal, rel, fault, recheck):
    conflicts = [r for r in journal_status(root, journal) if r["state"] == "conflict"]
    require(not conflicts, "recovery_conflict", "Recovery found human or unrelated changes; no automatic overwrite.", {"records": conflicts})
    for index, change in enumerate(journal["payload"]["changes"]):
        if _current_digest(root, change["path"]) == change["reviewed_record_sha256"]:
            continue
        _fault(fault, "before_record_" + str(index))
        def before_replace():
            _fault(fault, "before_replace_" + str(index))
            recheck()
        atomic_replace(root, change["path"], change["content"].encode("utf-8"), change["expected_sha256"],
                       before_replace=before_replace)
        _fault(fault, "after_record_" + str(index))
    _fault(fault, "before_receipt")
    recheck()
    if journal["payload"]["operation"] == "redact":
        _scrub_history(root, [c["path"] for c in journal["payload"]["changes"]], rel)
        _fault(fault, "after_redaction_history")
    receipt = {"operation_id": journal["operation_id"], "operation": journal["payload"]["operation"],
               "state": "complete", "reason": journal["payload"]["reason"], "records": journal_status(root, journal),
               "journal_path": rel, "task_events_replayed": False}
    expected = _current_digest(root, rel)
    journal.update(state="complete", receipt=receipt)
    atomic_replace(root, rel, json_bytes(journal), expected)
    _fault(fault, "after_receipt")
    return receipt


def transact(root, payload, grant_file, actor, *, fault=None):
    from memory_publish import authorize, validate_payload
    root = project_root(root); config = load_config(root)
    digest_value = sha256(json_bytes(payload))
    paths = [change["path"] for change in payload["changes"]]
    grant = authorize(root, config, grant_file, payload["operation"], digest_value, actor, paths=paths)
    # Validate the operation ID before it becomes a filesystem component.
    import re
    require(isinstance(payload.get("operation_id"), str) and re.fullmatch(r"MEMOP-[A-Za-z0-9-]{4,100}", payload["operation_id"]), "invalid_operation", "Malformed operation identity.")
    rel = JOURNAL_ROOT + "/" + payload["operation_id"] + ".json"
    def recheck():
        current_grant = authorize(root, config, grant_file, payload["operation"], digest_value, actor, paths=paths)
        from memory_evidence import validate_publication_evidence
        from memory_core import parse_record
        for change in payload["changes"]:
            record = parse_record(change["content"])
            if record["metadata"]["state"] == "active":
                validate_publication_evidence(root, record, config)
        return current_grant
    with project_lock(root):
        authorize(root, config, grant_file, payload["operation"], digest_value, actor, paths=paths)
        exists = safe_path(root, rel, must_exist=False).exists()
        if exists:
            journal = _read_journal(root, rel)
            require(journal["payload_sha256"] == digest_value, "operation_conflict", "Operation ID already refers to different reviewed bytes.")
            if journal["state"] == "complete":
                if journal["redacted_paths"]:
                    raise MemoryError("history_redacted", "Completed operation history was explicitly redacted; it cannot be replayed.")
                require(all(r["state"] == "committed" for r in journal_status(root, journal)), "post_completion_changed", "Records changed after this operation; historical receipt cannot overwrite them.")
                return journal["receipt"]
            validate_payload(root, config, payload, grant, recovering=True)
        else:
            require(not pending_transactions(root), "recovery_required", "Resolve accepted pending memory operations before a new publication.")
            validate_payload(root, config, payload, grant)
            originals = []
            for change in payload["changes"]:
                content = None
                if change["expected_sha256"] is not None and payload["operation"] != "redact":
                    content = base64.b64encode(safe_read_bytes(root, change["path"], max_bytes=250000)).decode("ascii")
                originals.append({"path": change["path"], "sha256": change["expected_sha256"], "content_base64": content})
            journal = {"schema_version": 1, "operation_id": payload["operation_id"], "payload_sha256": digest_value,
                       "payload": payload, "grant": {"path": str(grant_file), "sha256": grant["_sha256"]},
                       "actor_id": actor, "state": "prepared", "originals": originals, "redacted_paths": [], "redaction_sha256": None, "receipt": None}
            _fault(fault, "before_journal")
            atomic_replace(root, rel, json_bytes(journal), None)
        try:
            if not exists:
                _fault(fault, "after_journal")
            return _finish(root, journal, rel, fault, recheck)
        except (MemoryError, OSError) as exc:
            raise MemoryError("publication_interrupted", "Publication did not finish; recover the exact accepted operation.",
                              {"operation_id": payload["operation_id"], "journal_path": rel, "records": journal_status(root, journal),
                               "cause": exc.code if isinstance(exc, MemoryError) else type(exc).__name__}) from exc


def recover(root, journal_path, grant_file, actor, *, fault=None):
    from memory_publish import authorize, validate_payload
    root = project_root(root); config = load_config(root)
    require(str(journal_path).startswith(JOURNAL_ROOT + "/"), "recovery_scope", "Recovery accepts only a memory transaction journal.")
    journal = _read_journal(root, str(journal_path))
    require(not journal["redacted_paths"], "history_redacted", "Redacted completed history cannot be replayed.")
    paths = [change["path"] for change in journal["payload"]["changes"]]
    grant = authorize(root, config, grant_file, "recover", journal["payload_sha256"], actor, paths=paths)
    def recheck():
        authorize(root, config, grant_file, "recover", journal["payload_sha256"], actor, paths=paths)
        from memory_evidence import validate_publication_evidence
        from memory_core import parse_record
        for change in journal["payload"]["changes"]:
            record = parse_record(change["content"])
            if record["metadata"]["state"] == "active":
                validate_publication_evidence(root, record, config)
    with project_lock(root):
        authorize(root, config, grant_file, "recover", journal["payload_sha256"], actor, paths=paths)
        fresh = _read_journal(root, str(journal_path))
        require(fresh["payload_sha256"] == journal["payload_sha256"], "journal_changed", "Journal changed before recovery acquired its lock.")
        journal = fresh
        if journal["state"] == "complete":
            require(all(r["state"] == "committed" for r in journal_status(root, journal)), "post_completion_changed", "Completed publication has subsequent changes; recovery will not overwrite history.")
            return journal["receipt"]
        validate_payload(root, config, journal["payload"], grant, recovering=True)
        return _finish(root, journal, str(journal_path), fault, recheck)
