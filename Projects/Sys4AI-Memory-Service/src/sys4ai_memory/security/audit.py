"""Allowlisted, metadata-only audit events and sinks."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from threading import RLock
from typing import Protocol

from sys4ai_memory.util import ensure_utc

from .errors import PolicyDisabledError
from .isolation import ProjectBoundary
from .locks import exclusive_file_lock
from .secrets import require_secret_free


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """A content-free security and policy decision record."""

    event_id: str
    occurred_at: datetime
    principal_id: str
    project_id: str
    dataset_id: str
    operation: str
    target_ids: tuple[str, ...]
    policy_decision: str
    outcome: str
    trace_id: str
    policy_id: str
    permission_revision: str | None
    counts: tuple[tuple[str, int], ...] = ()
    warning_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_utc(self.occurred_at)
        require_secret_free(
            {
                "event_id": self.event_id,
                "principal_id": self.principal_id,
                "project_id": self.project_id,
                "dataset_id": self.dataset_id,
                "operation": self.operation,
                "target_ids": self.target_ids,
                "policy_decision": self.policy_decision,
                "outcome": self.outcome,
                "trace_id": self.trace_id,
                "policy_id": self.policy_id,
                "permission_revision": self.permission_revision,
                "warning_codes": self.warning_codes,
            },
            field_path="audit",
        )
        if any(value < 0 for _, value in self.counts):
            raise ValueError("audit counts must be non-negative")

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["occurred_at"] = ensure_utc(self.occurred_at).isoformat().replace("+00:00", "Z")
        payload["target_ids"] = list(self.target_ids)
        payload["counts"] = dict(self.counts)
        payload["warning_codes"] = list(self.warning_codes)
        return payload


class AuditSink(Protocol):
    def record(self, event: AuditEvent) -> None: ...


class InMemoryAuditSink:
    """A non-durable sink suitable while retention remains unresolved."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = RLock()

    def record(self, event: AuditEvent) -> None:
        with self._lock:
            self._events.append(event)

    def events(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return tuple(self._events)


class JsonlAuditSink:
    """A serialized local sink available only with an approved retention policy."""

    def __init__(
        self,
        boundary: ProjectBoundary,
        relative_path: str,
        *,
        retention_policy_id: str | None,
    ) -> None:
        if retention_policy_id is None or not retention_policy_id.strip():
            raise PolicyDisabledError("durable audit logging requires an approved retention policy")
        boundary.resolve_path(relative_path, must_exist=False)
        boundary.resolve_path(f"{relative_path}.lock", must_exist=False)
        self._boundary = boundary
        self._relative_path = relative_path

    def record(self, event: AuditEvent) -> None:
        serialized = json.dumps(event.to_json_dict(), sort_keys=True, separators=(",", ":")) + "\n"
        path = self._boundary.resolve_path(self._relative_path, must_exist=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        path = self._boundary.resolve_path(self._relative_path, must_exist=False)
        lock_path = self._boundary.resolve_path(
            f"{self._relative_path}.lock",
            must_exist=False,
        )
        with exclusive_file_lock(lock_path):
            descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                os.fchmod(descriptor, 0o600)
                content = serialized.encode("utf-8")
                written = os.write(descriptor, content)
                if written != len(content):
                    raise OSError("audit event append was incomplete")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
