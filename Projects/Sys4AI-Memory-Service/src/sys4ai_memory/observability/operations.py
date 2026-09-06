"""Retry-safe status, progress, cancellation, and checkpoint tracking."""

from __future__ import annotations

from datetime import datetime
from threading import RLock
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from sys4ai_memory.contracts import OperationName
from sys4ai_memory.contracts._base import Sha256, TraceId, UtcDateTime
from sys4ai_memory.security import require_secret_free
from sys4ai_memory.util import canonical_json_bytes, ensure_utc, sha256_bytes, stable_id, utc_now

from .models import MetadataCode, ObservabilityModel, OperationState
from .store import JsonlMetadataStore

LONG_RUNNING_OPERATIONS = frozenset(
    {
        OperationName.SYNC,
        OperationName.IMPROVE,
        OperationName.FORGET,
        OperationName.REBUILD,
        OperationName.EXPORT,
        OperationName.IMPORT,
    }
)


class OperationTransitionError(RuntimeError):
    """Requested operation status transition is not valid."""


class OperationProgress(ObservabilityModel):
    completed_units: Annotated[int, Field(ge=0)]
    total_units: Annotated[int, Field(ge=1)] | None = None
    unit: MetadataCode = "items"

    @model_validator(mode="after")
    def validate_progress(self) -> Self:
        if self.total_units is not None and self.completed_units > self.total_units:
            raise ValueError("operation progress cannot exceed total units")
        return self

    @property
    def fraction(self) -> float | None:
        if self.total_units is None:
            return None
        return self.completed_units / self.total_units


class OperationCheckpoint(ObservabilityModel):
    sequence: Annotated[int, Field(ge=1)]
    checkpoint_ref: MetadataCode
    checkpoint_fingerprint: Sha256
    created_at: UtcDateTime


class OperationStatus(ObservabilityModel):
    record_kind: Literal["operation_status"] = "operation_status"
    operation_id: MetadataCode
    project_id: MetadataCode
    operation: OperationName
    trace_id: TraceId
    state: OperationState
    retry_safe: bool
    idempotency_key_sha256: Sha256
    attempt: Annotated[int, Field(ge=1)]
    created_at: UtcDateTime
    updated_at: UtcDateTime
    started_at: UtcDateTime | None = None
    completed_at: UtcDateTime | None = None
    progress: OperationProgress
    checkpoint: OperationCheckpoint | None = None
    warning_codes: tuple[MetadataCode, ...] = ()
    error_code: MetadataCode | None = None

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        if self.operation not in LONG_RUNNING_OPERATIONS:
            raise ValueError("operation does not use long-running status tracking")
        if self.updated_at < self.created_at:
            raise ValueError("operation update cannot precede creation")
        if self.started_at is not None and self.started_at < self.created_at:
            raise ValueError("operation start cannot precede creation")
        terminal = {
            OperationState.CANCELLED,
            OperationState.SUCCEEDED,
            OperationState.FAILED,
        }
        if (self.state in terminal) != (self.completed_at is not None):
            raise ValueError("terminal operation state must have exactly one completion timestamp")
        if self.completed_at is not None and self.completed_at < self.updated_at:
            raise ValueError("completion timestamp cannot precede the latest update")
        if self.state is OperationState.FAILED and self.error_code is None:
            raise ValueError("failed operation status requires an error code")
        if self.state is not OperationState.FAILED and self.error_code is not None:
            raise ValueError("error code is valid only for failed operation status")
        if len(self.warning_codes) != len(set(self.warning_codes)):
            raise ValueError("operation warning codes must be unique")
        require_secret_free(self.model_dump(mode="json"), field_path="operation_status")
        return self


def _replace(status: OperationStatus, **updates: object) -> OperationStatus:
    payload = status.model_dump(mode="python")
    payload.update(updates)
    return OperationStatus.model_validate(payload)


class OperationTracker:
    """Maintain current status and append every transition for recovery inspection."""

    def __init__(self, store: JsonlMetadataStore | None = None) -> None:
        self._store = store
        self._lock = RLock()
        self._statuses: dict[str, OperationStatus] = {}
        self._idempotency: dict[str, str] = {}
        if store is not None:
            for payload in store.read_payloads():
                if payload.get("record_kind") != "operation_status":
                    continue
                status = OperationStatus.model_validate(payload)
                self._statuses[status.operation_id] = status
                self._idempotency[status.idempotency_key_sha256] = status.operation_id

    @staticmethod
    def idempotency_fingerprint(value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency key must not be blank")
        encoded = value.encode("utf-8")
        if len(encoded) > 4096:
            raise ValueError("idempotency key exceeds its byte bound")
        return sha256_bytes(encoded)

    def _persist(self, status: OperationStatus) -> OperationStatus:
        if self._store is not None:
            self._store.append(status)
        self._statuses[status.operation_id] = status
        self._idempotency[status.idempotency_key_sha256] = status.operation_id
        return status

    def create(
        self,
        *,
        project_id: str,
        operation: OperationName,
        trace_id: str,
        idempotency_key: str,
        total_units: int | None = None,
        retry_safe: bool = True,
        created_at: datetime | None = None,
    ) -> OperationStatus:
        if operation not in LONG_RUNNING_OPERATIONS:
            raise ValueError("operation does not use long-running status tracking")
        key_hash = self.idempotency_fingerprint(idempotency_key)
        with self._lock:
            existing_id = self._idempotency.get(key_hash)
            if existing_id is not None:
                existing = self._statuses[existing_id]
                if existing.project_id != project_id or existing.operation is not operation:
                    raise OperationTransitionError(
                        "idempotency key is already bound to another project or operation"
                    )
                return existing
            timestamp = ensure_utc(created_at or utc_now())
            operation_id = "op_" + stable_id(
                "long-running-operation", project_id, operation.value, key_hash
            ).replace("-", "")
            return self._persist(
                OperationStatus(
                    operation_id=operation_id,
                    project_id=project_id,
                    operation=operation,
                    trace_id=trace_id,
                    state=OperationState.PENDING,
                    retry_safe=retry_safe,
                    idempotency_key_sha256=key_hash,
                    attempt=1,
                    created_at=timestamp,
                    updated_at=timestamp,
                    progress=OperationProgress(completed_units=0, total_units=total_units),
                )
            )

    def get(self, operation_id: str) -> OperationStatus:
        with self._lock:
            try:
                return self._statuses[operation_id]
            except KeyError as error:
                raise KeyError("operation status not found") from error

    def start(self, operation_id: str, *, at: datetime | None = None) -> OperationStatus:
        with self._lock:
            status = self.get(operation_id)
            if status.state is not OperationState.PENDING:
                raise OperationTransitionError("only a pending operation can start")
            timestamp = ensure_utc(at or utc_now())
            return self._persist(
                _replace(
                    status,
                    state=OperationState.RUNNING,
                    started_at=timestamp,
                    updated_at=timestamp,
                )
            )

    def update_progress(
        self,
        operation_id: str,
        *,
        completed_units: int,
        total_units: int | None = None,
        at: datetime | None = None,
    ) -> OperationStatus:
        with self._lock:
            status = self.get(operation_id)
            if status.state not in {OperationState.RUNNING, OperationState.CANCEL_REQUESTED}:
                raise OperationTransitionError("progress requires a running operation")
            resolved_total = total_units if total_units is not None else status.progress.total_units
            progress = OperationProgress(
                completed_units=completed_units,
                total_units=resolved_total,
                unit=status.progress.unit,
            )
            if completed_units < status.progress.completed_units:
                raise OperationTransitionError("operation progress cannot move backwards")
            timestamp = ensure_utc(at or utc_now())
            return self._persist(_replace(status, progress=progress, updated_at=timestamp))

    def checkpoint(
        self,
        operation_id: str,
        *,
        checkpoint_ref: str,
        checkpoint_metadata: dict[str, object],
        at: datetime | None = None,
    ) -> OperationStatus:
        with self._lock:
            status = self.get(operation_id)
            if status.state not in {OperationState.RUNNING, OperationState.CANCEL_REQUESTED}:
                raise OperationTransitionError("checkpoint requires a running operation")
            timestamp = ensure_utc(at or utc_now())
            sequence = 1 if status.checkpoint is None else status.checkpoint.sequence + 1
            serialized_metadata = canonical_json_bytes(checkpoint_metadata)
            if len(serialized_metadata) > 64 * 1024:
                raise ValueError("checkpoint metadata exceeds its byte bound")
            checkpoint = OperationCheckpoint(
                sequence=sequence,
                checkpoint_ref=checkpoint_ref,
                checkpoint_fingerprint=sha256_bytes(serialized_metadata),
                created_at=timestamp,
            )
            return self._persist(_replace(status, checkpoint=checkpoint, updated_at=timestamp))

    def request_cancel(self, operation_id: str, *, at: datetime | None = None) -> OperationStatus:
        with self._lock:
            status = self.get(operation_id)
            timestamp = ensure_utc(at or utc_now())
            if status.state is OperationState.PENDING:
                return self._persist(
                    _replace(
                        status,
                        state=OperationState.CANCELLED,
                        updated_at=timestamp,
                        completed_at=timestamp,
                    )
                )
            if status.state is OperationState.CANCEL_REQUESTED:
                return status
            if status.state is not OperationState.RUNNING:
                raise OperationTransitionError("only pending or running operations can cancel")
            return self._persist(
                _replace(status, state=OperationState.CANCEL_REQUESTED, updated_at=timestamp)
            )

    def acknowledge_cancel(
        self, operation_id: str, *, at: datetime | None = None
    ) -> OperationStatus:
        with self._lock:
            status = self.get(operation_id)
            if status.state is not OperationState.CANCEL_REQUESTED:
                raise OperationTransitionError("cancellation was not requested")
            timestamp = ensure_utc(at or utc_now())
            return self._persist(
                _replace(
                    status,
                    state=OperationState.CANCELLED,
                    updated_at=timestamp,
                    completed_at=timestamp,
                )
            )

    def succeed(self, operation_id: str, *, at: datetime | None = None) -> OperationStatus:
        with self._lock:
            status = self.get(operation_id)
            if status.state is not OperationState.RUNNING:
                raise OperationTransitionError("only a running operation can succeed")
            if (
                status.progress.total_units is not None
                and status.progress.completed_units != status.progress.total_units
            ):
                raise OperationTransitionError("known operation progress must be complete")
            timestamp = ensure_utc(at or utc_now())
            return self._persist(
                _replace(
                    status,
                    state=OperationState.SUCCEEDED,
                    updated_at=timestamp,
                    completed_at=timestamp,
                )
            )

    def fail(
        self,
        operation_id: str,
        *,
        error_code: str,
        warning_codes: tuple[str, ...] = (),
        at: datetime | None = None,
    ) -> OperationStatus:
        with self._lock:
            status = self.get(operation_id)
            if status.state not in {OperationState.RUNNING, OperationState.CANCEL_REQUESTED}:
                raise OperationTransitionError("only an active operation can fail")
            timestamp = ensure_utc(at or utc_now())
            return self._persist(
                _replace(
                    status,
                    state=OperationState.FAILED,
                    error_code=error_code,
                    warning_codes=warning_codes,
                    updated_at=timestamp,
                    completed_at=timestamp,
                )
            )

    def resume(self, operation_id: str, *, at: datetime | None = None) -> OperationStatus:
        with self._lock:
            status = self.get(operation_id)
            if status.state not in {OperationState.FAILED, OperationState.CANCELLED}:
                raise OperationTransitionError("only a failed or cancelled operation can resume")
            if not status.retry_safe or status.checkpoint is None:
                raise OperationTransitionError("operation has no retry-safe checkpoint")
            timestamp = ensure_utc(at or utc_now())
            return self._persist(
                _replace(
                    status,
                    state=OperationState.RUNNING,
                    attempt=status.attempt + 1,
                    started_at=timestamp,
                    updated_at=timestamp,
                    completed_at=None,
                    error_code=None,
                )
            )
