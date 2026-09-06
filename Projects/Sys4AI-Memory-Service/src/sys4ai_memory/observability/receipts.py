"""Deterministic validation receipts that never execute recorded commands."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sys4ai_memory.util import canonical_json_bytes, ensure_utc, sha256_bytes

from .models import (
    DirtyState,
    EvidenceLocator,
    ValidationReceipt,
    VersionContext,
)
from .store import JsonlMetadataStore


def build_validation_receipt(
    *,
    command_id: str,
    command: tuple[str, ...],
    exit_status: int,
    recorded_at: datetime,
    source_revision: str | None,
    dirty_state: DirtyState,
    versions: VersionContext,
    evidence: tuple[EvidenceLocator, ...],
    dirty_state_fingerprint: str | None = None,
    warning_codes: tuple[str, ...] = (),
) -> ValidationReceipt:
    """Validate supplied result metadata and derive a stable receipt identity.

    This function records an already-observed command result. It does not import
    a process API, invoke a shell, or execute any command token.
    """

    candidate = ValidationReceipt.model_construct(
        record_kind="validation_receipt",
        schema_version="1.0",
        api_version="1.0",
        receipt_id="vrc_" + "0" * 64,
        command_id=command_id,
        command=command,
        exit_status=exit_status,
        recorded_at=ensure_utc(recorded_at),
        source_revision=source_revision,
        dirty_state=dirty_state,
        dirty_state_fingerprint=dirty_state_fingerprint,
        versions=versions,
        warning_codes=warning_codes,
        evidence=evidence,
    )
    receipt_id = "vrc_" + sha256_bytes(canonical_json_bytes(candidate.digest_payload()))
    payload = candidate.model_dump(mode="python")
    payload["receipt_id"] = receipt_id
    return ValidationReceipt.model_validate(payload)


class ValidationReceiptRecorder:
    """Append validated receipts to a caller-selected local metadata store."""

    def __init__(self, store: JsonlMetadataStore) -> None:
        self._store = store

    def record(self, receipt: ValidationReceipt) -> None:
        self._store.append(receipt)


def validation_receipt_schema() -> dict[str, Any]:
    """Return the checked-in validation receipt's JSON Schema contract."""

    schema = ValidationReceipt.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "validation-receipt.schema.json"
    return schema
