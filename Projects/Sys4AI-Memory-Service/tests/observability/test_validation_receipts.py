from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from pydantic import ValidationError

from sys4ai_memory.observability import (
    DirtyState,
    EvidenceLocator,
    EvidenceLocatorKind,
    JsonlMetadataStore,
    ValidationReceipt,
    ValidationReceiptRecorder,
    VersionContext,
    build_validation_receipt,
    validation_receipt_schema,
)


def _build(observed_at: datetime, versions: VersionContext) -> ValidationReceipt:
    return build_validation_receipt(
        command_id="validate_observability",
        command=("uv", "run", "--frozen", "pytest", "-q", "tests/observability"),
        exit_status=0,
        recorded_at=observed_at,
        source_revision="abc123def456",
        dirty_state=DirtyState.DIRTY,
        dirty_state_fingerprint="f" * 64,
        versions=versions,
        warning_codes=("working_tree_dirty",),
        evidence=(
            EvidenceLocator(
                kind=EvidenceLocatorKind.TEST,
                reference="tests/observability/test_validation_receipts.py",
                line=1,
                content_sha256="1" * 64,
            ),
            EvidenceLocator(
                kind=EvidenceLocatorKind.REQUIREMENT,
                reference="MEM-FR-172",
            ),
        ),
    )


def test_validation_receipt_is_deterministic_and_does_not_execute_command(
    monkeypatch: pytest.MonkeyPatch,
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    def unexpected_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise AssertionError("receipt construction must not execute a command")

    monkeypatch.setattr(subprocess, "run", unexpected_run)
    first = _build(observed_at, versions)
    second = _build(observed_at, versions)

    assert first == second
    assert first.receipt_id.startswith("vrc_")
    assert len(first.receipt_id) == 68
    assert first.command[0] == "uv"
    assert first.exit_status == 0
    assert first.recorded_at == observed_at
    assert first.source_revision == "abc123def456"
    assert first.dirty_state is DirtyState.DIRTY
    assert first.versions.provider_version == "1.0.0"
    assert first.evidence[0].reference.startswith("tests/observability/")


def test_validation_receipt_rejects_tampering(
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    receipt = _build(observed_at, versions)
    payload = receipt.model_dump(mode="python")
    payload["exit_status"] = 1
    with pytest.raises(ValidationError, match="receipt ID"):
        ValidationReceipt.model_validate(payload)


def test_validation_receipt_records_metadata_only(
    tmp_path: Path,
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    receipt = _build(observed_at, versions)
    store = JsonlMetadataStore(tmp_path.resolve(), "validation/receipts.jsonl")
    ValidationReceiptRecorder(store).record(receipt)

    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert payload["receipt_id"] == receipt.receipt_id
    assert payload["command"] == [
        "uv",
        "run",
        "--frozen",
        "pytest",
        "-q",
        "tests/observability",
    ]
    assert set(payload) == {
        "record_kind",
        "schema_version",
        "api_version",
        "receipt_id",
        "command_id",
        "command",
        "exit_status",
        "recorded_at",
        "source_revision",
        "dirty_state",
        "dirty_state_fingerprint",
        "versions",
        "warning_codes",
        "evidence",
    }
    assert "stdout" not in payload
    assert "stderr" not in payload
    assert "content" not in payload


def test_checked_in_validation_receipt_schema_matches_and_accepts_receipt(
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    schema_path = (
        Path(__file__).parents[2] / "schemas" / "memory" / ("validation-receipt.schema.json")
    )
    checked_in = json.loads(schema_path.read_text(encoding="utf-8"))
    expected = validation_receipt_schema()
    assert checked_in == expected
    Draft202012Validator.check_schema(checked_in)
    Draft202012Validator(checked_in).validate(_build(observed_at, versions).model_dump(mode="json"))


def test_validation_receipt_rejects_unsafe_evidence_and_command_tokens(
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    with pytest.raises(ValidationError):
        EvidenceLocator(kind=EvidenceLocatorKind.ARTIFACT, reference="../outside")
    with pytest.raises(ValidationError):
        build_validation_receipt(
            command_id="unsafe",
            command=("python", "-c", "print('raw project content')"),
            exit_status=0,
            recorded_at=observed_at,
            source_revision=None,
            dirty_state=DirtyState.UNKNOWN,
            versions=versions,
            evidence=(
                EvidenceLocator(kind=EvidenceLocatorKind.REQUIREMENT, reference="MEM-FR-172"),
            ),
        )


def test_dirty_state_requires_exactly_one_dirty_fingerprint(
    observed_at: datetime,
    versions: VersionContext,
) -> None:
    with pytest.raises(ValidationError, match="requires a fingerprint"):
        build_validation_receipt(
            command_id="validate_observability",
            command=("pytest",),
            exit_status=0,
            recorded_at=observed_at,
            source_revision="abc123",
            dirty_state=DirtyState.DIRTY,
            versions=versions,
            evidence=(
                EvidenceLocator(kind=EvidenceLocatorKind.REQUIREMENT, reference="MEM-FR-172"),
            ),
        )
