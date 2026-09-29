"""Bounded source references for the Project app; never a filesystem browser."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat


class AppError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def plain(value, limit=2000):
    if not isinstance(value, str):
        return ""
    if re.search(r"(?is)<(?:analysis|think|thinking)>|private chain.of.thought|hidden reasoning|(?:api[_ -]?key|password|secret)\s*[:=]\s*\S+", value):
        return "Content withheld."
    return "".join(c for c in value if c in "\n\t" or ord(c) >= 32)[:limit]


def relative(value):
    if not isinstance(value, str) or not value or len(value) > 500 or "\\" in value:
        raise AppError("source_unavailable")
    parts = PurePosixPath(value).parts
    if value.startswith("/") or any(p in ("", ".", "..") for p in parts) or str(PurePosixPath(value)) != value:
        raise AppError("source_unavailable")
    return parts


def read_bytes(root, path, limit=262144):
    """Open each path component by descriptor with no symlink following."""
    parts = relative(path)
    fd = None
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        child = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        os.close(fd)
        fd = child
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
            raise AppError("source_unavailable")
        chunks, size = [], 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise AppError("source_unavailable")
        after = os.fstat(fd)
        if after.st_nlink != 1 or (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise AppError("source_changed")
        return b"".join(chunks)
    except OSError:
        raise AppError("source_unavailable") from None
    finally:
        if fd is not None:
            os.close(fd)


def json_bytes(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise AppError("invalid_content") from None


def document_allowed(path):
    try:
        parts = relative(path)
    except AppError:
        return False
    denied = {"projects", "tasks", "trds", "implementation_plans", "roles", "memory", "node_modules", "control_records", "verification"}
    if any(p.startswith(".") or p.casefold() in denied or p.casefold().endswith("-depo") or p.casefold() in {"secrets", "credentials"} for p in parts):
        return False
    return Path(path).suffix.lower() in {".md", ".txt", ".rst"} and not re.search(r"(?i)(secret|credential|private|password)", path)


def source(reader, source_id):
    record = reader.handles.get(source_id)
    if record is None:
        raise AppError("source_unavailable")
    if record["owner"] == "documents":
        config = reader.config()
        docs = {row["path"]: row for row in config["documents"]}
        path = record["path"]
        if path not in docs or not document_allowed(path):
            raise AppError("source_unavailable")
        raw = read_bytes(reader.root, path)
        text = raw.decode("utf-8")
        return {"status": "ready", "title": plain(docs[path]["title"], 160), "path": path,
                "sha256": sha(raw), "text": plain(text, 24000), "truncated": len(text) > 24000,
                "freshness": "current" if sha(raw) == record.get("sha256") else "changed"}
    if record["owner"] in ("task", "trd", "plan"):
        from project_app_work import detail
        item = detail(reader, record["id"])["item"]
        text = json.dumps(item, ensure_ascii=False, indent=2)
        return {"status": "ready", "title": item["title"], "path": item["source"].get("path") or "Not recorded",
                "sha256": item["source"].get("sha256"), "text": text[:24000],
                "truncated": len(text) > 24000, "freshness": "current"}
    if record["owner"] == "memory":
        from project_app_knowledge import memory_source
        return memory_source(reader, record)
    if record["owner"] == "work-artifact":
        from project_app_work import task_document
        raw = task_document(reader, record["task_id"], record["path"])
        text = raw.decode("utf-8")
        return {"status": "ready", "title": record["path"], "path": record["path"], "sha256": sha(raw),
                "text": plain(text, 24000), "truncated": len(text) > 24000,
                "freshness": "current" if sha(raw) == record.get("sha256") else "changed"}
    raise AppError("source_unavailable")
