from __future__ import annotations

import json
import re
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import BaseModel, JsonValue, ValidationError

from sys4ai_memory.authorization import AuthorizationDecision
from sys4ai_memory.configuration import LoadedConfiguration, load_configuration
from sys4ai_memory.contracts import OperationName, Permission, RetrievalMode
from sys4ai_memory.observability import (
    AdministrativeOperation,
    AuditRecorder,
    CountMetric,
    JsonlMetadataStore,
    MetadataStoreError,
    RecallChannelCount,
    RecallFilterTrace,
    RecallRankingTrace,
    RecallTrace,
    TelemetryControl,
    VersionContext,
    configured_audit_store,
)
from sys4ai_memory.security import InMemoryAuditSink, SecretDetectedError

SECURITY_FIXTURE = (
    Path(__file__).parents[1] / "fixtures" / "security" / ("prompt_injection_untrusted.md")
)


class _RecordingTraceExporter:
    def __init__(self) -> None:
        self.traces: list[dict[str, JsonValue]] = []

    def export(self, trace: Mapping[str, JsonValue]) -> None:
        self.traces.append(dict(trace))


def _decision(operation: OperationName) -> AuthorizationDecision:
    return AuthorizationDecision(
        allowed=True,
        reason_code="allowed",
        principal_id="agent-runtime",
        project_id="project-alpha",
        dataset_id="project-alpha-memory",
        operation=operation.value,
        permission=Permission.READ,
        permission_revision="permissions-v1",
        canonical_sha256="e" * 64,
        grant_id="grant-runtime",
    )


def _administrative_decision(operation: AdministrativeOperation) -> AuthorizationDecision:
    return AuthorizationDecision(
        allowed=True,
        reason_code="allowed",
        principal_id="project-director",
        project_id="project-alpha",
        dataset_id="project-alpha-memory",
        operation=operation.value,
        permission=Permission.ADMINISTER,
        permission_revision="permissions-v1",
        canonical_sha256="e" * 64,
        grant_id="grant-administrator",
    )


def _recall_trace() -> RecallTrace:
    return RecallTrace(
        selected_channels=(RetrievalMode.EXACT, RetrievalMode.SEMANTIC),
        candidates=(
            RecallChannelCount(channel=RetrievalMode.EXACT, candidate_count=4),
            RecallChannelCount(channel=RetrievalMode.SEMANTIC, candidate_count=8),
        ),
        filters=(
            RecallFilterTrace(
                filter_code="scope_filter",
                examined_count=12,
                excluded_count=3,
                reason_codes=("outside_scope",),
            ),
        ),
        ranking_stages=(
            RecallRankingTrace(stage_code="weighted_rank", input_count=9, output_count=3),
        ),
        returned_source_ids=("src_alpha", "src_beta"),
        omitted_result_count=6,
    )


def test_every_public_operation_is_audited_with_effective_policy_context(
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    sink = InMemoryAuditSink()
    recorder = AuditRecorder(sink)

    records = [
        recorder.capture(
            decision=_decision(operation),
            actor_id="agent-caller",
            policy_decision_ref="control_records/memory/permissions",
            outcome_code="succeeded",
            trace_id=f"trace_{index}",
            versions=versions,
            occurred_at=observed_at,
            target_ids=(f"target_{index}",),
            counts=(CountMetric(name="affected_count", value=index),),
            recall=_recall_trace() if operation is OperationName.RECALL else None,
        )
        for index, operation in enumerate(OperationName)
    ]

    assert {record.operation for record in records} == set(OperationName)
    assert all(record.effective_principal_id == "agent-runtime" for record in records)
    assert all(
        record.policy_decision_ref == "control_records/memory/permissions" for record in records
    )
    assert len(sink.events()) == len(OperationName) == 16
    recall = next(record for record in records if record.operation is OperationName.RECALL)
    assert recall.recall is not None
    assert recall.recall.returned_source_ids == ("src_alpha", "src_beta")
    assert "query" not in recall.model_dump(mode="json")


def test_initialization_registration_and_administrative_changes_are_auditable(
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    sink = InMemoryAuditSink()
    recorder = AuditRecorder(sink)

    records = [
        recorder.capture(
            decision=_administrative_decision(operation),
            actor_id="project-director",
            policy_decision_ref="control_records/memory/permissions",
            outcome_code="succeeded",
            trace_id=f"trace_admin_{index}",
            versions=versions,
            occurred_at=observed_at,
        )
        for index, operation in enumerate(AdministrativeOperation)
    ]

    assert {record.operation for record in records} == set(AdministrativeOperation)
    assert {event.operation for event in sink.events()} == {
        operation.value for operation in AdministrativeOperation
    }

    invalid = _administrative_decision(AdministrativeOperation.PERMISSION_CHANGE).model_copy(
        update={"operation": "memory.unknown.change"}
    )
    with pytest.raises(ValueError):
        recorder.capture(
            decision=invalid,
            actor_id="project-director",
            policy_decision_ref="control_records/memory/permissions",
            outcome_code="rejected",
            trace_id="trace_admin_unknown",
            versions=versions,
            occurred_at=observed_at,
        )


def test_failed_or_denied_recall_can_be_audited_without_backend_trace(
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    recorder = AuditRecorder(InMemoryAuditSink())
    failed = recorder.capture(
        decision=_decision(OperationName.RECALL),
        actor_id="agent-caller",
        policy_decision_ref="control_records/memory/permissions",
        outcome_code="failed",
        trace_id="trace_recall_failed",
        versions=versions,
        occurred_at=observed_at,
    )
    denied_decision = _decision(OperationName.RECALL).model_copy(
        update={
            "allowed": False,
            "reason_code": "no_matching_current_grant",
            "permission_revision": None,
            "canonical_sha256": None,
            "grant_id": None,
        }
    )
    denied = recorder.capture(
        decision=denied_decision,
        actor_id="agent-caller",
        policy_decision_ref="control_records/memory/permissions",
        outcome_code="denied",
        trace_id="trace_recall_denied",
        versions=versions,
        occurred_at=observed_at,
    )

    assert failed.recall is None
    assert denied.recall is None


def test_telemetry_is_default_off_and_requires_explicit_local_store(
    tmp_path: Path,
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    store = JsonlMetadataStore(tmp_path.resolve(), "audit/events.jsonl")
    sink = InMemoryAuditSink()
    recorder = AuditRecorder(sink, local_store=store)
    recorder.capture(
        decision=_decision(OperationName.HEALTH),
        actor_id="agent-caller",
        policy_decision_ref="control_records/memory/permissions",
        outcome_code="succeeded",
        trace_id="trace_health",
        versions=versions,
        occurred_at=observed_at,
    )
    assert not store.path.exists()
    with pytest.raises(ValueError, match="requires a metadata store"):
        AuditRecorder(
            sink,
            telemetry=TelemetryControl(local_capture_enabled=True),
        )
    with pytest.raises(ValueError, match="requires a trace exporter"):
        AuditRecorder(
            sink,
            telemetry=TelemetryControl(telemetry_export_enabled=True),
        )
    with pytest.raises(ValueError, match="requires telemetry export"):
        AuditRecorder(sink, trace_exporter=_RecordingTraceExporter())
    TelemetryControl(content_logging="disabled").validate()
    with pytest.raises(ValueError, match="cannot enable local capture"):
        TelemetryControl(local_capture_enabled=True, content_logging="disabled").validate()


def test_explicit_telemetry_export_emits_metadata_only_otlp_json(
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    exporter = _RecordingTraceExporter()
    recorder = AuditRecorder(
        InMemoryAuditSink(),
        telemetry=TelemetryControl(telemetry_export_enabled=True),
        trace_exporter=exporter,
    )

    recorder.capture(
        decision=_decision(OperationName.HEALTH),
        actor_id="agent-caller",
        policy_decision_ref="control_records/memory/permissions",
        outcome_code="succeeded",
        trace_id="trace_health_export",
        versions=versions,
        occurred_at=observed_at,
        target_ids=("target-health",),
    )

    assert len(exporter.traces) == 1
    payload = exporter.traces[0]
    resource_span = payload["resourceSpans"][0]  # type: ignore[index]
    span = resource_span["scopeSpans"][0]["spans"][0]  # type: ignore[index]
    assert re.fullmatch(r"[0-9a-f]{32}", span["traceId"])  # type: ignore[arg-type, index]
    assert re.fullmatch(r"[0-9a-f]{16}", span["spanId"])  # type: ignore[arg-type, index]
    assert span["kind"] == 1  # type: ignore[index]
    assert span["startTimeUnixNano"] == span["endTimeUnixNano"]  # type: ignore[index]
    assert isinstance(span["startTimeUnixNano"], str)  # type: ignore[index]
    assert span["status"] == {"code": 1}  # type: ignore[index]
    serialized = json.dumps(payload, sort_keys=True)
    assert "agent-caller" not in serialized
    assert "agent-runtime" not in serialized
    assert "trace_health_export" not in serialized
    assert "source content" not in serialized


def test_audit_store_binds_to_loaded_configuration(tmp_path: Path) -> None:
    project_root = Path(__file__).parents[2]
    loaded = load_configuration(
        project_root / "config" / "memory.toml",
        trusted_project_root=project_root,
    )
    derived = (tmp_path / ".sys4ai" / "memory").resolve()
    derived.mkdir(parents=True)
    temporary_loaded = LoadedConfiguration(
        configuration=loaded.configuration,
        project_root=tmp_path.resolve(),
        configuration_path=tmp_path / "memory.toml",
        resolved_paths={
            "local_data": derived,
            "audit_log": derived / "audit" / "events.jsonl",
        },
        fingerprint=loaded.fingerprint,
    )

    control = TelemetryControl.from_configuration(
        temporary_loaded,
        enable_local_capture=True,
    )
    store = configured_audit_store(temporary_loaded, derived_root=derived)
    assert control.local_capture_enabled
    assert not control.telemetry_export_enabled
    assert store.path == derived / "audit" / "events.jsonl"

    wrong_root = (tmp_path / "wrong").resolve()
    wrong_root.mkdir()
    with pytest.raises(ValueError, match="does not match"):
        configured_audit_store(temporary_loaded, derived_root=wrong_root)


def test_enabled_local_audit_contains_only_allowlisted_metadata(
    tmp_path: Path,
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    store = JsonlMetadataStore(tmp_path.resolve(), "audit/events.jsonl")
    recorder = AuditRecorder(
        InMemoryAuditSink(),
        telemetry=TelemetryControl(local_capture_enabled=True),
        local_store=store,
    )
    record = recorder.capture(
        decision=_decision(OperationName.RECALL),
        actor_id="agent-caller",
        policy_decision_ref="control_records/memory/permissions",
        outcome_code="succeeded",
        trace_id="trace_recall",
        versions=versions,
        occurred_at=observed_at,
        decision_reason_codes=("scope_allowed", "authority_allowed"),
        recall=_recall_trace(),
    )

    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert payload == record.model_dump(mode="json")
    assert set(payload["recall"]) == {
        "selected_channels",
        "candidates",
        "filters",
        "ranking_stages",
        "returned_source_ids",
        "omitted_result_count",
    }
    assert "content" not in store.path.read_text(encoding="utf-8").casefold()
    assert payload["decision_reason_codes"] == ["scope_allowed", "authority_allowed"]


def test_recall_trace_requires_complete_unique_stage_metadata() -> None:
    with pytest.raises(ValidationError, match="cover every selected channel"):
        RecallTrace(
            selected_channels=(RetrievalMode.EXACT, RetrievalMode.SEMANTIC),
            candidates=(RecallChannelCount(channel=RetrievalMode.EXACT, candidate_count=1),),
            filters=(),
            ranking_stages=(),
            returned_source_ids=(),
        )
    with pytest.raises(ValidationError, match="cannot exceed"):
        RecallFilterTrace(
            filter_code="scope_filter",
            examined_count=1,
            excluded_count=2,
        )
    with pytest.raises(ValidationError, match="cannot exceed"):
        RecallRankingTrace(stage_code="rank", input_count=1, output_count=2)


def test_secret_and_restricted_content_never_reach_audit_storage(
    tmp_path: Path,
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    restricted = SECURITY_FIXTURE.read_text(encoding="utf-8")
    secret = "sk-" + "runtimegenerated123456"
    store = JsonlMetadataStore(tmp_path.resolve(), "audit/events.jsonl")
    recorder = AuditRecorder(
        InMemoryAuditSink(),
        telemetry=TelemetryControl(local_capture_enabled=True),
        local_store=store,
    )
    for unsafe_actor in (secret, restricted):
        with pytest.raises((ValidationError, SecretDetectedError)):
            recorder.capture(
                decision=_decision(OperationName.HEALTH),
                actor_id=unsafe_actor,
                policy_decision_ref="control_records/memory/permissions",
                outcome_code="rejected",
                trace_id="trace_unsafe",
                versions=versions,
                occurred_at=observed_at,
            )
    assert not store.path.exists()


class _SensitiveMetadata(BaseModel):
    record_kind: str = "test_metadata"
    authorization: str
    message: str


def test_store_applies_last_line_secret_redaction(tmp_path: Path) -> None:
    secret = "runtime.generated." + "token.value"
    store = JsonlMetadataStore(tmp_path.resolve(), "audit/events.jsonl")
    store.append(
        _SensitiveMetadata(
            authorization="Bearer " + secret,
            message="connect postgresql://user:" + secret + "@localhost/db",
        )
    )
    serialized = store.path.read_text(encoding="utf-8")
    assert secret not in serialized
    assert serialized.count("[REDACTED]") == 2


class _SequenceRecord(BaseModel):
    record_kind: str = "test_sequence"
    sequence: int


def test_concurrent_jsonl_appends_remain_complete_and_private(tmp_path: Path) -> None:
    store = JsonlMetadataStore(tmp_path.resolve(), "traces/events.jsonl")
    with ThreadPoolExecutor(max_workers=8) as executor:
        tuple(executor.map(lambda index: store.append(_SequenceRecord(sequence=index)), range(80)))

    payloads = store.read_payloads()
    assert len(payloads) == 80
    assert {payload["sequence"] for payload in payloads} == set(range(80))
    assert store.path.stat().st_mode & 0o777 == 0o600


def test_metadata_store_rejects_escape_and_symlink_paths(tmp_path: Path) -> None:
    root = (tmp_path / "derived").resolve()
    root.mkdir()
    with pytest.raises(MetadataStoreError, match="escapes or crosses"):
        JsonlMetadataStore(root, "../outside.jsonl")
    root_link = tmp_path / "derived-link"
    root_link.symlink_to(root, target_is_directory=True)
    with pytest.raises(MetadataStoreError, match="derived root"):
        JsonlMetadataStore(root_link, "events.jsonl")

    linked = root / "linked"
    linked.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(MetadataStoreError, match="escapes or crosses"):
        JsonlMetadataStore(root, "linked/events.jsonl")

    store = JsonlMetadataStore(root, "events.jsonl")
    target = tmp_path / "outside.jsonl"
    target.write_text("", encoding="utf-8")
    store.path.symlink_to(target)
    with pytest.raises(MetadataStoreError, match="escapes or crosses"):
        store.append(_SequenceRecord(sequence=1))


def test_metadata_store_enforces_record_and_file_bounds(tmp_path: Path) -> None:
    store = JsonlMetadataStore(
        tmp_path.resolve(),
        "events.jsonl",
        max_record_bytes=256,
        max_file_bytes=300,
    )
    store.append(_SequenceRecord(sequence=1))
    with pytest.raises(MetadataStoreError, match="file reached"):
        for index in range(20):
            store.append(_SequenceRecord(sequence=index + 2))
