"""Metadata-only operation audit capture with explicit local telemetry control."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sys4ai_memory.authorization import AuthorizationDecision
from sys4ai_memory.configuration import LoadedConfiguration
from sys4ai_memory.contracts import OperationName
from sys4ai_memory.security import AuditSink
from sys4ai_memory.util import ensure_utc, stable_id, utc_now

from .models import (
    AdministrativeOperation,
    AuditedOperation,
    CountMetric,
    OperationAuditRecord,
    RecallTrace,
    VersionContext,
)
from .store import JsonlMetadataStore
from .telemetry import OpenTelemetryTraceExporter, operation_audit_to_otlp_json


@dataclass(frozen=True, slots=True)
class TelemetryControl:
    """Current implementation permits explicit local capture and no export."""

    local_capture_enabled: bool = False
    telemetry_export_enabled: bool = False
    content_logging: str = "metadata_only"

    @classmethod
    def from_configuration(
        cls,
        loaded: LoadedConfiguration,
        *,
        enable_local_capture: bool = False,
    ) -> TelemetryControl:
        settings = loaded.configuration.memory.observability
        control = cls(
            local_capture_enabled=enable_local_capture,
            telemetry_export_enabled=settings.telemetry_export,
            content_logging=settings.content_logging,
        )
        control.validate()
        return control

    def validate(self) -> None:
        if self.content_logging not in {"metadata_only", "disabled"}:
            raise ValueError("observability capture supports metadata_only or disabled logging")
        if self.local_capture_enabled and self.content_logging == "disabled":
            raise ValueError("disabled content logging cannot enable local capture")


def configured_audit_store(
    loaded: LoadedConfiguration,
    *,
    derived_root: Path,
    max_record_bytes: int = 64 * 1024,
    max_file_bytes: int = 16 * 1024 * 1024,
) -> JsonlMetadataStore:
    """Bind the configured audit path to the initialized derived root."""

    expected_root = loaded.resolved_paths["local_data"]
    if derived_root.is_symlink() or derived_root.resolve(strict=True) != expected_root.resolve():
        raise ValueError("derived root does not match the loaded memory configuration")
    configured_path = loaded.resolved_paths["audit_log"]
    try:
        relative_path = configured_path.relative_to(expected_root)
    except ValueError as error:
        raise ValueError("configured audit log is outside the derived memory root") from error
    return JsonlMetadataStore(
        derived_root,
        relative_path.as_posix(),
        max_record_bytes=max_record_bytes,
        max_file_bytes=max_file_bytes,
    )


class AuditRecorder:
    """Record each public or control-plane operation through the security audit sink."""

    def __init__(
        self,
        security_sink: AuditSink,
        *,
        telemetry: TelemetryControl | None = None,
        local_store: JsonlMetadataStore | None = None,
        trace_exporter: OpenTelemetryTraceExporter | None = None,
    ) -> None:
        self._security_sink = security_sink
        self._telemetry = telemetry or TelemetryControl()
        self._telemetry.validate()
        if self._telemetry.local_capture_enabled and local_store is None:
            raise ValueError("enabled local telemetry requires a metadata store")
        if self._telemetry.telemetry_export_enabled and trace_exporter is None:
            raise ValueError("enabled telemetry export requires a trace exporter")
        if not self._telemetry.telemetry_export_enabled and trace_exporter is not None:
            raise ValueError("a trace exporter requires telemetry export to be enabled")
        self._local_store = local_store
        self._trace_exporter = trace_exporter

    def capture(
        self,
        *,
        decision: AuthorizationDecision,
        actor_id: str,
        policy_decision_ref: str,
        outcome_code: str,
        trace_id: str,
        versions: VersionContext,
        occurred_at: datetime | None = None,
        target_ids: tuple[str, ...] = (),
        counts: tuple[CountMetric, ...] = (),
        decision_reason_codes: tuple[str, ...] = (),
        warning_codes: tuple[str, ...] = (),
        recall: RecallTrace | None = None,
        event_id: str | None = None,
    ) -> OperationAuditRecord:
        """Validate, project, and optionally persist one metadata record."""

        operation: AuditedOperation
        try:
            operation = OperationName(decision.operation)
        except ValueError:
            operation = AdministrativeOperation(decision.operation)
        timestamp = ensure_utc(occurred_at or utc_now())
        resolved_event_id = event_id or (
            "evt_"
            + stable_id(
                "operation-audit",
                decision.project_id,
                operation.value,
                trace_id,
                timestamp.isoformat(),
                "|".join(target_ids) or "no-target",
            ).replace("-", "")
        )
        record = OperationAuditRecord(
            event_id=resolved_event_id,
            occurred_at=timestamp,
            actor_id=actor_id,
            effective_principal_id=decision.principal_id,
            project_id=decision.project_id,
            dataset_id=decision.dataset_id,
            operation=operation,
            target_ids=target_ids,
            policy_allowed=decision.allowed,
            policy_reason_code=decision.reason_code,
            decision_reason_codes=decision_reason_codes,
            policy_decision_ref=policy_decision_ref,
            permission_revision=decision.permission_revision,
            canonical_policy_sha256=decision.canonical_sha256,
            grant_id=decision.grant_id,
            outcome_code=outcome_code,
            trace_id=trace_id,
            versions=versions,
            counts=counts,
            warning_codes=warning_codes,
            recall=recall,
        )
        self._security_sink.record(record.to_security_event())
        if self._telemetry.local_capture_enabled:
            assert self._local_store is not None
            self._local_store.append(record)
        if self._telemetry.telemetry_export_enabled:
            assert self._trace_exporter is not None
            self._trace_exporter.export(operation_audit_to_otlp_json(record))
        return record
