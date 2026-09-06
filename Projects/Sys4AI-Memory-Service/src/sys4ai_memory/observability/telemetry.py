"""Metadata-only OpenTelemetry Protocol JSON trace projection."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from pydantic import JsonValue, TypeAdapter

from sys4ai_memory.util import canonical_json_bytes, sha256_bytes

from .models import OperationAuditRecord

_JSON_OBJECT = TypeAdapter(dict[str, JsonValue])
_TRACE_ID = re.compile(r"^[0-9a-f]{32}$")


@runtime_checkable
class OpenTelemetryTraceExporter(Protocol):
    """Caller-injected sink for one OTLP/JSON `TracesData` envelope."""

    def export(self, trace: Mapping[str, JsonValue]) -> None: ...


def _identifier(value: str, *, length: int) -> str:
    normalized = value.casefold()
    if length == 32 and _TRACE_ID.fullmatch(normalized) and set(normalized) != {"0"}:
        return normalized
    return sha256_bytes(value.encode("utf-8"))[:length]


def _unix_nanoseconds(value: datetime) -> str:
    timestamp = value.astimezone(UTC)
    delta = timestamp - datetime(1970, 1, 1, tzinfo=UTC)
    seconds = delta.days * 86_400 + delta.seconds
    return str(seconds * 1_000_000_000 + delta.microseconds * 1_000)


def _attribute(key: str, value: str | bool | int) -> dict[str, JsonValue]:
    if isinstance(value, bool):
        encoded: dict[str, JsonValue] = {"boolValue": value}
    elif isinstance(value, int):
        encoded = {"intValue": str(value)}
    else:
        encoded = {"stringValue": value}
    return {"key": key, "value": encoded}


def operation_audit_to_otlp_json(record: OperationAuditRecord) -> dict[str, JsonValue]:
    """Project one validated audit record into an OTLP JSON traces envelope."""

    trace_id = _identifier(record.trace_id, length=32)
    span_id = _identifier(
        sha256_bytes(
            canonical_json_bytes(
                {
                    "event_id": record.event_id,
                    "operation": record.operation.value,
                    "outcome": record.outcome_code,
                }
            )
        ),
        length=16,
    )
    observed = _unix_nanoseconds(record.occurred_at)
    status_code = (
        1
        if record.outcome_code in {"succeeded", "idempotent_replay"}
        else 2
        if record.outcome_code in {"denied", "failed"}
        else 0
    )
    attributes = tuple(
        sorted(
            (
                _attribute("sys4ai.actor.id_sha256", sha256_bytes(record.actor_id.encode())),
                _attribute(
                    "sys4ai.dataset.id_sha256",
                    sha256_bytes(record.dataset_id.encode()),
                ),
                _attribute("sys4ai.operation", record.operation.value),
                _attribute("sys4ai.outcome", record.outcome_code),
                _attribute("sys4ai.policy.allowed", record.policy_allowed),
                _attribute("sys4ai.policy.reason", record.policy_reason_code),
                _attribute(
                    "sys4ai.project.id_sha256",
                    sha256_bytes(record.project_id.encode()),
                ),
                _attribute("sys4ai.target.count", len(record.target_ids)),
                _attribute("sys4ai.warning.count", len(record.warning_codes)),
            ),
            key=lambda item: str(item["key"]),
        )
    )
    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        _attribute("service.name", "sys4ai-memory-service"),
                        _attribute("service.version", record.api_version),
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {
                            "name": "sys4ai_memory.observability",
                            "version": record.schema_version,
                        },
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": span_id,
                                "name": record.operation.value,
                                "kind": 1,
                                "startTimeUnixNano": observed,
                                "endTimeUnixNano": observed,
                                "attributes": list(attributes),
                                "droppedAttributesCount": 0,
                                "status": {"code": status_code},
                            }
                        ],
                    }
                ],
            }
        ]
    }
    return _JSON_OBJECT.validate_python(payload)
