from __future__ import annotations

from pathlib import Path

from pydantic import JsonValue

from tools.benchmark_local_runtime import run_benchmark


def _object(value: JsonValue) -> dict[str, JsonValue]:
    assert isinstance(value, dict)
    return value


def _integer(value: JsonValue) -> int:
    assert isinstance(value, int) and not isinstance(value, bool)
    return value


def _number(value: JsonValue) -> float:
    assert isinstance(value, int | float) and not isinstance(value, bool)
    return float(value)


def test_small_local_runtime_benchmark_reports_truthful_component_boundaries() -> None:
    project_root = Path(__file__).parents[2]
    tracked_configuration = project_root / "config/memory.toml"
    configuration_before = tracked_configuration.read_bytes()
    result = run_benchmark(
        fragments=200,
        batch_size=100,
        relations=200,
        relation_batch_size=100,
        recall_samples=4,
        startup_samples=4,
        sync_samples=4,
        warmups=1,
    )

    corpus = _object(result["corpus"])
    hybrid = _object(result["hybrid_recall"])
    startup = _object(result["guarded_startup"])
    sync = _object(result["incremental_sync"])
    capacity = _object(result["relation_capacity"])
    relation_latency = _object(capacity["batch_load_latency"])

    assert corpus["fragments"] == 200
    assert corpus["relations"] == 200
    assert corpus["indexed_records_before_sync"] == 202
    assert corpus["disposable_storage_removed_after_run"] is True
    assert hybrid["samples"] == 4
    assert _integer(hybrid["returned_records_total"]) >= 4
    assert hybrid["requirement_verified"] is False
    assert startup["samples"] == 4
    assert startup["requirement_verified"] is False
    assert sync["samples"] == 4
    assert sync["changed_sources_per_sample"] == 1
    assert sync["guarded_provider_path_measured"] is True
    assert sync["requirement_verified"] is False
    assert capacity["loaded_relations"] == 200
    assert capacity["full_relation_target_exercised"] is False
    assert capacity["included_in_hybrid_provider_recall"] is True
    assert capacity["relation_indexed_by_endpoint"] is True
    assert capacity["full_relation_scan_per_recall"] is False
    assert capacity["requirement_verified"] is False
    assert result["evidence_boundaries"]
    for measurement in (hybrid, startup, sync, relation_latency):
        assert _number(measurement["p50_ms"]) >= 0
        assert _number(measurement["p95_ms"]) >= 0
        assert _number(measurement["max_ms"]) >= 0
    assert tracked_configuration.read_bytes() == configuration_before
