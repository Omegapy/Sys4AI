from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from sys4ai_memory.util import (
    PathBoundaryError,
    atomic_write_text,
    canonical_json_bytes,
    ensure_utc,
    redact_sensitive,
    resolve_within,
    sha256_bytes,
    sha256_file,
    stable_id,
)


def test_canonical_json_and_hashes_are_deterministic(tmp_path: Path) -> None:
    first = canonical_json_bytes({"b": 2, "a": "é"})
    second = canonical_json_bytes({"a": "é", "b": 2})
    assert first == second == b'{"a":"\xc3\xa9","b":2}\n'
    target = tmp_path / "record.json"
    target.write_bytes(first)
    assert sha256_file(target) == sha256_bytes(first)


def test_hash_rejects_symlink(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.write_text("source", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(source)
    with pytest.raises(ValueError, match="non-symlink"):
        sha256_file(link)


def test_stable_id_is_repeatable_and_namespaced() -> None:
    assert stable_id("record", "project", "path") == stable_id("record", "project", "path")
    assert stable_id("source", "project", "path") != stable_id("record", "project", "path")
    with pytest.raises(ValueError, match="nonblank"):
        stable_id("record", "")


def test_timestamp_requires_explicit_offset() -> None:
    value = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
    assert ensure_utc(value) == value
    offset = value.astimezone(timezone(timedelta(hours=-6)))
    assert ensure_utc(offset) == value
    with pytest.raises(ValueError, match="explicit UTC offset"):
        ensure_utc(datetime(2026, 9, 3, 12, 0))


def test_resolve_within_rejects_escape_absolute_and_symlink(tmp_path: Path) -> None:
    root = (tmp_path / "project").resolve()
    root.mkdir()
    source = root / "source.txt"
    source.write_text("content", encoding="utf-8")
    assert resolve_within(root, "source.txt") == source
    for unsafe in ("../outside", "/absolute"):
        with pytest.raises(PathBoundaryError):
            resolve_within(root, unsafe, must_exist=False)
    link = root / "linked"
    link.symlink_to(tmp_path)
    with pytest.raises(PathBoundaryError, match="symlink"):
        resolve_within(root, "linked/value", must_exist=False)


def test_atomic_write_replaces_content_and_sets_private_mode(tmp_path: Path) -> None:
    target = tmp_path / "receipt.json"
    atomic_write_text(target, json.dumps({"revision": 1}) + "\n")
    atomic_write_text(target, json.dumps({"revision": 2}) + "\n")
    assert json.loads(target.read_text(encoding="utf-8")) == {"revision": 2}
    assert target.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.glob(".receipt.json.*")) == []


def test_redaction_removes_sensitive_keys_headers_and_connection_passwords() -> None:
    opaque = "part" + "-not-a-real-secret"
    value = {
        "authorization": "Bearer " + opaque,
        "nested": {"password": opaque, "message": "connect postgresql://user:" + opaque + "@db/x"},
    }
    redacted = redact_sensitive(value)
    redacted_marker = "[REDACTED]"
    assert redacted["authorization"] == redacted_marker
    assert redacted["nested"]["password"] == redacted_marker
    assert opaque not in redacted["nested"]["message"]
