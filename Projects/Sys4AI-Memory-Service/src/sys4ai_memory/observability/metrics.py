"""Thread-safe operational metrics with fixed metadata-only dimensions."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import Literal

from pydantic import Field, model_validator

from sys4ai_memory.contracts import OperationName, RetrievalMode
from sys4ai_memory.contracts._base import UtcDateTime
from sys4ai_memory.security import require_secret_free
from sys4ai_memory.util import ensure_utc, utc_now

from .models import MetadataCode, ObservabilityModel, OperationState


class IngestionMetrics(ObservabilityModel):
    success_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)
    lag_seconds: float = Field(ge=0)


class RecallLatencyMetric(ObservabilityModel):
    channel: RetrievalMode
    count: int = Field(ge=0)
    average_ms: float = Field(ge=0)
    maximum_ms: float = Field(ge=0)


class RecallQualityMetrics(ObservabilityModel):
    sufficient_count: int = Field(ge=0)
    insufficient_count: int = Field(ge=0)
    returned_source_count: int = Field(ge=0)
    selected_result_count: int = Field(ge=0)


class ApprovalMetrics(ObservabilityModel):
    approved_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    approval_rate: float | None = Field(default=None, ge=0, le=1)

    @property
    def decision_count(self) -> int:
        return self.approved_count + self.rejected_count

    @model_validator(mode="after")
    def validate_rate(self) -> ApprovalMetrics:
        expected = None if self.decision_count == 0 else self.approved_count / self.decision_count
        if self.approval_rate != expected:
            raise ValueError("approval rate must match the recorded decision counts")
        return self


class OperationFailureMetric(ObservabilityModel):
    operation: OperationName
    count: int = Field(ge=0)


class StorageMetric(ObservabilityModel):
    memory_class: MetadataCode
    bytes_used: int = Field(ge=0)


class RebuildMetrics(ObservabilityModel):
    state: OperationState
    completed_units: int = Field(ge=0)
    total_units: int | None = Field(default=None, ge=1)
    warning_count: int = Field(ge=0)
    completed_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)
    latest_duration_ms: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_progress(self) -> RebuildMetrics:
        if self.total_units is not None and self.completed_units > self.total_units:
            raise ValueError("rebuild progress cannot exceed total units")
        return self


class MetricSnapshot(ObservabilityModel):
    record_kind: Literal["metric_snapshot"] = "metric_snapshot"
    project_id: MetadataCode
    captured_at: UtcDateTime
    ingestion: IngestionMetrics
    recall_latency: tuple[RecallLatencyMetric, ...]
    recall_quality: RecallQualityMetrics
    source_index_drift_count: int = Field(ge=0)
    approvals: ApprovalMetrics
    failures: tuple[OperationFailureMetric, ...]
    provider_error_count: int = Field(ge=0)
    duplicate_active_record_count: int = Field(ge=0)
    storage: tuple[StorageMetric, ...]
    rebuild: RebuildMetrics
    expiration_cleanup_lag_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_metadata_only(self) -> MetricSnapshot:
        require_secret_free(self.model_dump(mode="json"), field_path="metric_snapshot")
        return self


@dataclass(slots=True)
class _LatencyAccumulator:
    count: int = 0
    total_ms: float = 0.0
    maximum_ms: float = 0.0

    def add(self, latency_ms: float) -> None:
        self.count += 1
        self.total_ms += latency_ms
        self.maximum_ms = max(self.maximum_ms, latency_ms)


class MetricsCollector:
    """Collect fixed operational counters without labels derived from content."""

    def __init__(self, project_id: str) -> None:
        self._project_id = project_id
        self._lock = RLock()
        self._ingestion_success = 0
        self._ingestion_failure = 0
        self._ingestion_lag_seconds = 0.0
        self._latencies: dict[RetrievalMode, _LatencyAccumulator] = defaultdict(_LatencyAccumulator)
        self._sufficient = 0
        self._insufficient = 0
        self._returned_sources = 0
        self._selected_results = 0
        self._drift_count = 0
        self._approved = 0
        self._rejected = 0
        self._failures: dict[OperationName, int] = defaultdict(int)
        self._provider_errors = 0
        self._duplicate_records = 0
        self._storage: dict[str, int] = {}
        self._rebuild_state = OperationState.PENDING
        self._rebuild_completed_units = 0
        self._rebuild_total_units: int | None = None
        self._rebuild_warnings = 0
        self._rebuild_completed_count = 0
        self._rebuild_failure_count = 0
        self._rebuild_duration_ms: float | None = None
        self._expiration_lag_seconds = 0.0

    def record_ingestion(self, *, succeeded: int, failed: int, lag_seconds: float) -> None:
        if succeeded < 0 or failed < 0 or lag_seconds < 0:
            raise ValueError("ingestion metrics must be non-negative")
        with self._lock:
            self._ingestion_success += succeeded
            self._ingestion_failure += failed
            self._ingestion_lag_seconds = lag_seconds

    def record_recall(
        self,
        *,
        channel: RetrievalMode,
        latency_ms: float,
        sufficient: bool,
        returned_source_count: int,
        selected_result_count: int = 0,
    ) -> None:
        if latency_ms < 0 or returned_source_count < 0 or selected_result_count < 0:
            raise ValueError("recall metrics must be non-negative")
        if selected_result_count > returned_source_count:
            raise ValueError("selected results cannot exceed returned sources")
        with self._lock:
            self._latencies[channel].add(latency_ms)
            if sufficient:
                self._sufficient += 1
            else:
                self._insufficient += 1
            self._returned_sources += returned_source_count
            self._selected_results += selected_result_count

    def set_drift_count(self, count: int) -> None:
        if count < 0:
            raise ValueError("drift count must be non-negative")
        with self._lock:
            self._drift_count = count

    def record_approval(self, *, approved: bool) -> None:
        with self._lock:
            if approved:
                self._approved += 1
            else:
                self._rejected += 1

    def record_failure(
        self,
        operation: OperationName,
        *,
        count: int = 1,
        provider_error: bool = False,
    ) -> None:
        if count < 1:
            raise ValueError("failure count must be positive")
        with self._lock:
            self._failures[operation] += count
            if provider_error:
                self._provider_errors += count

    def set_duplicate_active_record_count(self, count: int) -> None:
        if count < 0:
            raise ValueError("duplicate record count must be non-negative")
        with self._lock:
            self._duplicate_records = count

    def set_storage_size(self, memory_class: str, bytes_used: int) -> None:
        if bytes_used < 0:
            raise ValueError("storage size must be non-negative")
        StorageMetric(memory_class=memory_class, bytes_used=bytes_used)
        with self._lock:
            self._storage[memory_class] = bytes_used

    def record_rebuild_progress(
        self,
        *,
        completed_units: int,
        total_units: int | None,
        warning_count: int,
        state: OperationState,
        completed: bool = False,
        failed: bool = False,
        duration_ms: float | None = None,
    ) -> None:
        if completed_units < 0 or warning_count < 0:
            raise ValueError("rebuild metrics must be non-negative")
        if total_units is not None and (total_units < 1 or completed_units > total_units):
            raise ValueError("rebuild total must bound completed units")
        if duration_ms is not None and duration_ms < 0:
            raise ValueError("rebuild duration must be non-negative")
        if completed and failed:
            raise ValueError("one rebuild cannot be both completed and failed")
        with self._lock:
            self._rebuild_completed_units = completed_units
            self._rebuild_total_units = total_units
            self._rebuild_warnings = warning_count
            self._rebuild_state = state
            self._rebuild_duration_ms = duration_ms
            if completed:
                self._rebuild_completed_count += 1
            if failed:
                self._rebuild_failure_count += 1

    def set_expiration_cleanup_lag(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("expiration cleanup lag must be non-negative")
        with self._lock:
            self._expiration_lag_seconds = seconds

    def snapshot(self, *, captured_at: datetime | None = None) -> MetricSnapshot:
        with self._lock:
            latencies = tuple(
                RecallLatencyMetric(
                    channel=channel,
                    count=value.count,
                    average_ms=value.total_ms / value.count,
                    maximum_ms=value.maximum_ms,
                )
                for channel, value in sorted(
                    self._latencies.items(), key=lambda item: item[0].value
                )
                if value.count
            )
            failures = tuple(
                OperationFailureMetric(operation=operation, count=count)
                for operation, count in sorted(
                    self._failures.items(), key=lambda item: item[0].value
                )
            )
            storage = tuple(
                StorageMetric(memory_class=name, bytes_used=value)
                for name, value in sorted(self._storage.items())
            )
            return MetricSnapshot(
                project_id=self._project_id,
                captured_at=ensure_utc(captured_at or utc_now()),
                ingestion=IngestionMetrics(
                    success_count=self._ingestion_success,
                    failure_count=self._ingestion_failure,
                    lag_seconds=self._ingestion_lag_seconds,
                ),
                recall_latency=latencies,
                recall_quality=RecallQualityMetrics(
                    sufficient_count=self._sufficient,
                    insufficient_count=self._insufficient,
                    returned_source_count=self._returned_sources,
                    selected_result_count=self._selected_results,
                ),
                source_index_drift_count=self._drift_count,
                approvals=ApprovalMetrics(
                    approved_count=self._approved,
                    rejected_count=self._rejected,
                    approval_rate=(
                        None
                        if self._approved + self._rejected == 0
                        else self._approved / (self._approved + self._rejected)
                    ),
                ),
                failures=failures,
                provider_error_count=self._provider_errors,
                duplicate_active_record_count=self._duplicate_records,
                storage=storage,
                rebuild=RebuildMetrics(
                    state=self._rebuild_state,
                    completed_units=self._rebuild_completed_units,
                    total_units=self._rebuild_total_units,
                    warning_count=self._rebuild_warnings,
                    completed_count=self._rebuild_completed_count,
                    failure_count=self._rebuild_failure_count,
                    latest_duration_ms=self._rebuild_duration_ms,
                ),
                expiration_cleanup_lag_seconds=self._expiration_lag_seconds,
            )
