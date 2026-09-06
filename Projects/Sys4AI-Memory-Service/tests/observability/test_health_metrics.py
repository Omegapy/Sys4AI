from __future__ import annotations

from datetime import datetime

import pytest

from sys4ai_memory.contracts import OperationName, RetrievalMode
from sys4ai_memory.exact_index import IndexHealth
from sys4ai_memory.observability import (
    REQUIRED_COMPONENTS,
    HealthAggregator,
    HealthComponentName,
    HealthCount,
    HealthProbe,
    HealthState,
    MetricsCollector,
    OperationState,
    detect_source_index_drift,
    drift_health_component,
    exact_index_health_component,
    metadata_health_probe,
    provider_health_component,
)
from sys4ai_memory.providers import (
    ProviderHealth,
    ProviderHealthProbe,
    ProviderHealthState,
    ProviderName,
)


def _probe(
    name: str,
    state: HealthState,
    detail: str,
    observed_at: datetime,
    *,
    counts: tuple[HealthCount, ...] = (),
) -> HealthProbe:
    return metadata_health_probe(
        name=name,
        probe=lambda: (state, detail, counts, None),
        clock=lambda: observed_at,
    )


def test_composite_health_reports_degraded_readiness_and_drift(
    observed_at: datetime,
) -> None:
    probes = [
        _probe(name, HealthState.HEALTHY, "ready", observed_at)
        for name in sorted(REQUIRED_COMPONENTS)
        if name not in {HealthComponentName.PROVIDER_CONNECTIVITY, HealthComponentName.DRIFT}
    ]
    probes.extend(
        (
            _probe(
                HealthComponentName.PROVIDER_CONNECTIVITY,
                HealthState.DEGRADED,
                "provider_degraded",
                observed_at,
            ),
            _probe(
                HealthComponentName.DRIFT,
                HealthState.DEGRADED,
                "source_index_drift",
                observed_at,
                counts=(HealthCount(name="drift_count", value=2),),
            ),
        )
    )
    report = HealthAggregator(probes).check(
        project_id="project-alpha",
        checked_at=observed_at,
    )

    assert report.liveness is HealthState.HEALTHY
    assert report.readiness is HealthState.DEGRADED
    assert report.drift is HealthState.DEGRADED
    assert {component.name for component in report.components} == REQUIRED_COMPONENTS
    drift = next(
        component for component in report.components if component.name == HealthComponentName.DRIFT
    )
    assert drift.counts[0].value == 2


def test_health_requires_each_component_exactly_once(observed_at: datetime) -> None:
    probes = [
        _probe(name, HealthState.HEALTHY, "ready", observed_at)
        for name in sorted(REQUIRED_COMPONENTS - {HealthComponentName.DRIFT})
    ]
    with pytest.raises(ValueError, match="each required component"):
        HealthAggregator(probes).check(project_id="project-alpha", checked_at=observed_at)
    with pytest.raises(ValueError, match="unknown health component"):
        _probe("unknown_component", HealthState.HEALTHY, "ready", observed_at)


def test_exact_index_adapter_reports_generation_and_counts(observed_at: datetime) -> None:
    component = exact_index_health_component(
        IndexHealth(
            schema_version="1.0",
            fts5_available=True,
            active_generation_id=None,
            current_source_count=7,
            current_record_count=21,
        ),
        checked_at=observed_at,
    )
    assert component.name == HealthComponentName.EXACT_INDEX
    assert component.state is HealthState.DEGRADED
    assert component.detail_code == "generation_missing"
    assert {item.name: item.value for item in component.counts} == {
        "source_count": 7,
        "record_count": 21,
    }

    unavailable = exact_index_health_component(
        IndexHealth(
            schema_version="1.0",
            fts5_available=False,
            active_generation_id=None,
            current_source_count=0,
            current_record_count=0,
        ),
        checked_at=observed_at,
    )
    assert unavailable.state is HealthState.UNAVAILABLE

    ready = exact_index_health_component(
        IndexHealth(
            schema_version="1.0",
            fts5_available=True,
            active_generation_id="gen_ready",
            current_source_count=1,
            current_record_count=1,
        ),
        checked_at=observed_at,
    )
    assert ready.state is HealthState.HEALTHY


def test_provider_health_adapter_preserves_provider_state(observed_at: datetime) -> None:
    component = provider_health_component(
        ProviderHealth(
            provider_name=ProviderName.IN_MEMORY,
            provider_version="1.0.0",
            project_id="project-alpha",
            dataset_id="project-alpha-memory",
            probe=ProviderHealthProbe.READINESS,
            state=ProviderHealthState.UNAVAILABLE,
            checked_at=observed_at,
            initialized=False,
            components=(),
            trace_id="trace_health",
        )
    )
    assert component.name == HealthComponentName.PROVIDER_CONNECTIVITY
    assert component.state is HealthState.UNAVAILABLE
    assert component.detail_code == "provider_unavailable"


def test_source_index_drift_detection_compares_ids_and_fingerprints(
    observed_at: datetime,
) -> None:
    report = detect_source_index_drift(
        registered_source_ids=("src_alpha", "src_beta"),
        indexed_source_ids=("src_alpha", "src_unexpected"),
        stale_source_ids=("src_alpha",),
        expected_configuration_fingerprint="a" * 64,
        active_configuration_fingerprint="b" * 64,
        expected_profile_fingerprint="c" * 64,
        active_profile_fingerprint="c" * 64,
        expected_provider_fingerprint="d" * 64,
        active_provider_fingerprint="d" * 64,
    )
    assert report.drift_count == 4
    assert report.state is HealthState.DEGRADED
    assert set(report.reason_codes) == {
        "missing_index_sources",
        "unexpected_index_sources",
        "stale_source_revisions",
        "configuration_fingerprint_mismatch",
    }
    component = drift_health_component(report, checked_at=observed_at)
    assert component.state is HealthState.DEGRADED
    assert component.detail_code == "source_index_drift"
    assert {item.name: item.value for item in component.counts}["drift_count"] == 4

    clear = detect_source_index_drift(
        registered_source_ids=("src_alpha",),
        indexed_source_ids=("src_alpha",),
        expected_configuration_fingerprint="a" * 64,
        active_configuration_fingerprint="a" * 64,
        expected_profile_fingerprint="b" * 64,
        active_profile_fingerprint="b" * 64,
        expected_provider_fingerprint="c" * 64,
        active_provider_fingerprint="c" * 64,
    )
    assert clear.drift_count == 0
    assert drift_health_component(clear, checked_at=observed_at).state is HealthState.HEALTHY


def test_drift_detection_rejects_unknown_stale_ids_and_invalid_fingerprints() -> None:
    shared = {
        "expected_configuration_fingerprint": "a" * 64,
        "active_configuration_fingerprint": "a" * 64,
        "expected_profile_fingerprint": "b" * 64,
        "active_profile_fingerprint": "b" * 64,
        "expected_provider_fingerprint": "c" * 64,
        "active_provider_fingerprint": "c" * 64,
    }
    with pytest.raises(ValueError, match="belong"):
        detect_source_index_drift(
            registered_source_ids=("src_alpha",),
            indexed_source_ids=("src_alpha",),
            stale_source_ids=("src_other",),
            **shared,
        )
    with pytest.raises(ValueError, match="SHA-256"):
        detect_source_index_drift(
            registered_source_ids=("src_alpha",),
            indexed_source_ids=("src_alpha",),
            expected_configuration_fingerprint="invalid",
            active_configuration_fingerprint="a" * 64,
            expected_profile_fingerprint="b" * 64,
            active_profile_fingerprint="b" * 64,
            expected_provider_fingerprint="c" * 64,
            active_provider_fingerprint="c" * 64,
        )


def test_metrics_snapshot_covers_operational_measurements(observed_at: datetime) -> None:
    collector = MetricsCollector("project-alpha")
    collector.record_ingestion(succeeded=9, failed=1, lag_seconds=2.5)
    collector.record_recall(
        channel=RetrievalMode.EXACT,
        latency_ms=10.0,
        sufficient=True,
        returned_source_count=2,
        selected_result_count=1,
    )
    collector.record_recall(
        channel=RetrievalMode.EXACT,
        latency_ms=30.0,
        sufficient=False,
        returned_source_count=0,
    )
    collector.set_drift_count(3)
    collector.record_approval(approved=True)
    collector.record_approval(approved=False)
    collector.record_failure(OperationName.RECALL, provider_error=True)
    collector.set_duplicate_active_record_count(2)
    collector.set_storage_size("episodic", 4096)
    collector.record_rebuild_progress(
        completed_units=4,
        total_units=10,
        warning_count=2,
        state=OperationState.FAILED,
        failed=True,
        duration_ms=1250.0,
    )
    collector.set_expiration_cleanup_lag(90.0)

    snapshot = collector.snapshot(captured_at=observed_at)

    assert snapshot.ingestion.success_count == 9
    assert snapshot.ingestion.failure_count == 1
    assert snapshot.ingestion.lag_seconds == 2.5
    assert snapshot.recall_latency[0].average_ms == 20.0
    assert snapshot.recall_latency[0].maximum_ms == 30.0
    assert snapshot.recall_quality.sufficient_count == 1
    assert snapshot.recall_quality.insufficient_count == 1
    assert snapshot.source_index_drift_count == 3
    assert snapshot.approvals.approval_rate == 0.5
    assert snapshot.failures[0].operation is OperationName.RECALL
    assert snapshot.provider_error_count == 1
    assert snapshot.duplicate_active_record_count == 2
    assert snapshot.storage[0].bytes_used == 4096
    assert snapshot.rebuild.failure_count == 1
    assert snapshot.rebuild.warning_count == 2
    assert snapshot.expiration_cleanup_lag_seconds == 90.0
    serialized = snapshot.model_dump_json()
    for prohibited in ("query", "content", "credential", "token"):
        assert prohibited not in serialized.casefold()


def test_metrics_reject_negative_or_unbounded_inputs() -> None:
    collector = MetricsCollector("project-alpha")
    with pytest.raises(ValueError, match="non-negative"):
        collector.record_ingestion(succeeded=-1, failed=0, lag_seconds=0)
    with pytest.raises(ValueError, match="cannot exceed"):
        collector.record_recall(
            channel=RetrievalMode.HYBRID,
            latency_ms=1,
            sufficient=True,
            returned_source_count=1,
            selected_result_count=2,
        )
    with pytest.raises(ValueError, match="bound"):
        collector.record_rebuild_progress(
            completed_units=2,
            total_units=1,
            warning_count=0,
            state=OperationState.FAILED,
        )
    with pytest.raises(ValueError, match="positive"):
        collector.record_failure(OperationName.RECALL, count=0)
    with pytest.raises(ValueError, match="non-negative"):
        collector.set_drift_count(-1)
    with pytest.raises(ValueError, match="non-negative"):
        collector.set_duplicate_active_record_count(-1)
    with pytest.raises(ValueError, match="non-negative"):
        collector.set_storage_size("episodic", -1)
    with pytest.raises(ValueError, match="non-negative"):
        collector.set_expiration_cleanup_lag(-1)
    assert collector.snapshot().approvals.approval_rate is None
