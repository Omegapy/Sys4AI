"""Bounded, private, append-only storage for metadata observability records."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from threading import RLock
from typing import Any

from pydantic import BaseModel

from sys4ai_memory.security import redact_text
from sys4ai_memory.security.locks import exclusive_file_lock
from sys4ai_memory.util import PathBoundaryError, redact_sensitive, resolve_within


class MetadataStoreError(RuntimeError):
    """Metadata output was unsafe, corrupt, or outside its configured bound."""


def _redact_strings(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _redact_strings(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_strings(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_strings(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


class JsonlMetadataStore:
    """Append validated model payloads below one prevalidated derived root."""

    def __init__(
        self,
        derived_root: Path,
        relative_path: str,
        *,
        max_record_bytes: int = 64 * 1024,
        max_file_bytes: int = 16 * 1024 * 1024,
    ) -> None:
        if not derived_root.is_absolute() or derived_root.is_symlink() or not derived_root.is_dir():
            raise MetadataStoreError(
                "derived root must be an existing absolute non-symlink directory"
            )
        if max_record_bytes < 256 or max_file_bytes < max_record_bytes:
            raise ValueError("metadata store bounds are invalid")
        self._root = derived_root.resolve(strict=True)
        self._relative_path = relative_path
        self._max_record_bytes = max_record_bytes
        self._max_file_bytes = max_file_bytes
        self._thread_lock = RLock()
        self._resolve_target()
        self._resolve_lock()

    @property
    def path(self) -> Path:
        return self._resolve_target()

    def _resolve(self, candidate: str) -> Path:
        try:
            return resolve_within(self._root, candidate, must_exist=False)
        except PathBoundaryError as error:
            raise MetadataStoreError("metadata path escapes or crosses the derived root") from error

    def _resolve_target(self) -> Path:
        path = self._resolve(self._relative_path)
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise MetadataStoreError("metadata target must be a regular non-symlink file")
        return path

    def _resolve_lock(self) -> Path:
        path = self._resolve(f"{self._relative_path}.lock")
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise MetadataStoreError("metadata lock must be a regular non-symlink file")
        return path

    def _prepare_parent(self) -> None:
        target = self._resolve_target()
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(target.parent, 0o700)
        self._resolve_target()
        self._resolve_lock()

    def append(self, record: BaseModel) -> None:
        """Redact and append one complete JSON object without truncating prior data."""

        payload = record.model_dump(mode="json")
        redacted = _redact_strings(redact_sensitive(payload))
        serialized = (
            json.dumps(
                redacted,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        if len(serialized) > self._max_record_bytes:
            raise MetadataStoreError("metadata record exceeds its configured byte bound")

        with self._thread_lock:
            self._prepare_parent()
            path = self._resolve_target()
            lock_path = self._resolve_lock()
            with exclusive_file_lock(lock_path):
                flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                descriptor = os.open(path, flags, 0o600)
                try:
                    os.fchmod(descriptor, 0o600)
                    if os.fstat(descriptor).st_size + len(serialized) > self._max_file_bytes:
                        raise MetadataStoreError("metadata file reached its configured byte bound")
                    view = memoryview(serialized)
                    while view:
                        written = os.write(descriptor, view)
                        if written <= 0:
                            raise OSError("metadata append made no progress")
                        view = view[written:]
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)

    def read_payloads(self) -> tuple[dict[str, Any], ...]:
        """Read bounded JSON objects without following a replaced symlink."""

        with self._thread_lock:
            path = self._resolve_target()
            if not path.exists():
                return ()
            if path.stat().st_size > self._max_file_bytes:
                raise MetadataStoreError("metadata file exceeds its configured byte bound")
            lock_path = self._resolve_lock()
            payloads: list[dict[str, Any]] = []
            with exclusive_file_lock(lock_path):
                flags = os.O_RDONLY
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                descriptor = os.open(path, flags)
                try:
                    metadata = os.fstat(descriptor)
                    if not stat.S_ISREG(metadata.st_mode):
                        raise MetadataStoreError("metadata target must remain a regular file")
                    with os.fdopen(descriptor, "rb", closefd=False) as stream:
                        for line_number, line in enumerate(stream, start=1):
                            if len(line) > self._max_record_bytes:
                                raise MetadataStoreError(
                                    f"metadata line {line_number} exceeds its configured byte bound"
                                )
                            try:
                                payload = json.loads(line)
                            except json.JSONDecodeError as error:
                                raise MetadataStoreError(
                                    f"metadata line {line_number} is invalid JSON"
                                ) from error
                            if not isinstance(payload, dict):
                                raise MetadataStoreError(
                                    f"metadata line {line_number} must contain a JSON object"
                                )
                            payloads.append(payload)
                finally:
                    os.close(descriptor)
            return tuple(payloads)
