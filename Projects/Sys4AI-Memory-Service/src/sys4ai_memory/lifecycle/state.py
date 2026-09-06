"""Non-destructive record transitions with current and historical views."""

from __future__ import annotations

from datetime import datetime
from threading import RLock
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from sys4ai_memory.contracts import AuthorityTier, RecordStatus, Sensitivity, TrustClass
from sys4ai_memory.util import ensure_utc, utc_now


class LifecycleStateError(RuntimeError):
    """A requested lifecycle transition is invalid or ambiguous."""


class LifecycleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    record_id: str
    project_id: str
    dataset_id: str
    status: RecordStatus
    authority_tier: AuthorityTier
    trust_class: TrustClass
    sensitivity: Sensitivity
    canonical: bool
    source_ids: tuple[str, ...]
    valid_from: datetime
    valid_to: datetime | None = None
    supersedes: tuple[str, ...] = ()
    superseded_by: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_record(self) -> Self:
        start = ensure_utc(self.valid_from)
        end = None if self.valid_to is None else ensure_utc(self.valid_to)
        if end is not None and end < start:
            raise ValueError("valid_to cannot precede valid_from")
        if self.record_id in {*self.supersedes, *self.superseded_by}:
            raise ValueError("a record cannot supersede itself")
        if len(set(self.supersedes)) != len(self.supersedes):
            raise ValueError("supersedes must not contain duplicates")
        if len(set(self.superseded_by)) != len(self.superseded_by):
            raise ValueError("superseded_by must not contain duplicates")
        return self


_TRANSITIONS: dict[RecordStatus, frozenset[RecordStatus]] = {
    RecordStatus.PROPOSED: frozenset({RecordStatus.STAGED, RecordStatus.REJECTED}),
    RecordStatus.STAGED: frozenset(
        {RecordStatus.APPROVED, RecordStatus.REJECTED, RecordStatus.WITHDRAWN}
    ),
    RecordStatus.APPROVED: frozenset({RecordStatus.ACTIVE, RecordStatus.WITHDRAWN}),
    RecordStatus.ACTIVE: frozenset(
        {
            RecordStatus.SUPERSEDED,
            RecordStatus.INVALIDATED,
            RecordStatus.EXPIRED,
            RecordStatus.WITHDRAWN,
            RecordStatus.DELETED,
        }
    ),
    RecordStatus.SUPERSEDED: frozenset({RecordStatus.DELETED}),
    RecordStatus.REJECTED: frozenset({RecordStatus.DELETED}),
    RecordStatus.INVALIDATED: frozenset({RecordStatus.DELETED}),
    RecordStatus.EXPIRED: frozenset({RecordStatus.DELETED}),
    RecordStatus.WITHDRAWN: frozenset({RecordStatus.DELETED}),
    RecordStatus.DELETED: frozenset(),
}


class LifecycleCatalog:
    """Thread-safe metadata catalog that never discards lifecycle history."""

    def __init__(self) -> None:
        self._records: dict[str, LifecycleRecord] = {}
        self._lock = RLock()

    def add(self, record: LifecycleRecord) -> LifecycleRecord:
        with self._lock:
            existing = self._records.get(record.record_id)
            if existing is not None and existing != record:
                raise LifecycleStateError("record ID already exists with different metadata")
            self._records[record.record_id] = record
            return record

    def get(self, record_id: str) -> LifecycleRecord:
        with self._lock:
            try:
                return self._records[record_id]
            except KeyError as error:
                raise LifecycleStateError("record does not exist") from error

    def transition(
        self,
        record_id: str,
        status: RecordStatus,
        *,
        at: datetime | None = None,
    ) -> LifecycleRecord:
        with self._lock:
            current = self.get(record_id)
            if status is current.status:
                return current
            if status not in _TRANSITIONS[current.status]:
                raise LifecycleStateError(
                    f"invalid lifecycle transition: {current.status.value} -> {status.value}"
                )
            effective_at = ensure_utc(at or utc_now())
            updated = LifecycleRecord.model_validate(
                {
                    **current.model_dump(),
                    "status": status,
                    "valid_to": None if status is RecordStatus.ACTIVE else effective_at,
                }
            )
            self._records[record_id] = updated
            return updated

    def transition_many(
        self,
        record_ids: tuple[str, ...],
        status: RecordStatus,
        *,
        at: datetime | None = None,
    ) -> tuple[LifecycleRecord, ...]:
        """Validate every transition before publishing the batch."""

        effective_at = ensure_utc(at or utc_now())
        with self._lock:
            current = tuple(self.get(record_id) for record_id in record_ids)
            self._validate_transition_set(current, status)
            updated = tuple(
                record
                if status is record.status
                else LifecycleRecord.model_validate(
                    {
                        **record.model_dump(),
                        "status": status,
                        "valid_to": None if status is RecordStatus.ACTIVE else effective_at,
                    }
                )
                for record in current
            )
            self._records.update({record.record_id: record for record in updated})
            return updated

    def validate_transition_many(
        self,
        record_ids: tuple[str, ...],
        status: RecordStatus,
    ) -> None:
        """Fail before external effects if any member of a batch cannot transition."""

        with self._lock:
            current = tuple(self.get(record_id) for record_id in record_ids)
            self._validate_transition_set(current, status)

    @staticmethod
    def _validate_transition_set(
        records: tuple[LifecycleRecord, ...],
        status: RecordStatus,
    ) -> None:
        for record in records:
            if status is record.status:
                continue
            if status not in _TRANSITIONS[record.status]:
                raise LifecycleStateError(
                    f"invalid lifecycle transition: {record.status.value} -> {status.value}"
                )

    def supersede(
        self,
        prior_record_id: str,
        replacement_record_id: str,
        *,
        at: datetime | None = None,
    ) -> tuple[LifecycleRecord, LifecycleRecord]:
        with self._lock:
            prior = self.get(prior_record_id)
            replacement = self.get(replacement_record_id)
            if (
                prior.status is RecordStatus.SUPERSEDED
                and replacement_record_id in prior.superseded_by
            ):
                return prior, replacement
            self._validate_supersession_pair(prior, replacement)
            effective_at = ensure_utc(at or utc_now())
            prior_updated = LifecycleRecord.model_validate(
                {
                    **prior.model_dump(),
                    "status": RecordStatus.SUPERSEDED,
                    "valid_to": effective_at,
                    "superseded_by": tuple(sorted({*prior.superseded_by, replacement_record_id})),
                }
            )
            replacement_updated = LifecycleRecord.model_validate(
                {
                    **replacement.model_dump(),
                    "supersedes": tuple(sorted({*replacement.supersedes, prior_record_id})),
                }
            )
            self._records[prior_record_id] = prior_updated
            self._records[replacement_record_id] = replacement_updated
            return prior_updated, replacement_updated

    def validate_supersession(
        self,
        prior_record_id: str,
        replacement_record_id: str,
    ) -> None:
        """Validate a supersession before a coordinated index mutation."""

        with self._lock:
            prior = self.get(prior_record_id)
            replacement = self.get(replacement_record_id)
            if (
                prior.status is RecordStatus.SUPERSEDED
                and replacement_record_id in prior.superseded_by
            ):
                return
            self._validate_supersession_pair(prior, replacement)

    @staticmethod
    def _validate_supersession_pair(
        prior: LifecycleRecord,
        replacement: LifecycleRecord,
    ) -> None:
        if (
            prior.project_id != replacement.project_id
            or prior.dataset_id != replacement.dataset_id
        ):
            raise LifecycleStateError("supersession cannot cross project or dataset boundaries")
        if (
            prior.status is not RecordStatus.ACTIVE
            or replacement.status is not RecordStatus.ACTIVE
        ):
            raise LifecycleStateError("supersession requires two active records")

    def invalidate(self, record_id: str, *, at: datetime | None = None) -> LifecycleRecord:
        return self.transition(record_id, RecordStatus.INVALIDATED, at=at)

    def expire(self, record_id: str, *, at: datetime | None = None) -> LifecycleRecord:
        return self.transition(record_id, RecordStatus.EXPIRED, at=at)

    def withdraw(self, record_id: str, *, at: datetime | None = None) -> LifecycleRecord:
        return self.transition(record_id, RecordStatus.WITHDRAWN, at=at)

    def mark_deleted(self, record_id: str, *, at: datetime | None = None) -> LifecycleRecord:
        return self.transition(record_id, RecordStatus.DELETED, at=at)

    def expire_due(self, *, now: datetime | None = None) -> tuple[str, ...]:
        effective_now = ensure_utc(now or utc_now())
        with self._lock:
            due = tuple(
                sorted(
                    record_id
                    for record_id, record in self._records.items()
                    if record.status is RecordStatus.ACTIVE
                    and record.valid_to is not None
                    and record.valid_to <= effective_now
                )
            )
            for record_id in due:
                self.transition(record_id, RecordStatus.EXPIRED, at=effective_now)
            return due

    def query(
        self,
        *,
        project_id: str,
        dataset_id: str,
        historical: bool = False,
    ) -> tuple[LifecycleRecord, ...]:
        with self._lock:
            records = (
                record
                for record in self._records.values()
                if record.project_id == project_id and record.dataset_id == dataset_id
            )
            if not historical:
                records = (record for record in records if record.status is RecordStatus.ACTIVE)
            return tuple(sorted(records, key=lambda record: record.record_id))
