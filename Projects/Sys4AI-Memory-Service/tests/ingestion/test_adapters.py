from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.contracts import ErrorCategory, SourceRecord
from sys4ai_memory.ingestion import (
    IngestionFailure,
    IngestionSynchronizer,
    OptionalAdapterUnit,
    SoftwareEngineeringPythonAdapter,
    available_adapters,
    normalize_bytes,
    normalize_many,
    normalize_source,
)
from sys4ai_memory.sources import SourceDiscovery, load_source_registry

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE_ROOT = PROJECT_ROOT / "tests/fixtures/projects/project_alpha"
PROCESSED_AT = datetime(2026, 9, 3, 12, tzinfo=UTC)


class FixturePdfAdapter:
    adapter_id = "fixture-pdf"
    adapter_version = "1.2.0"
    formats = frozenset({"pdf"})

    def units(
        self,
        raw_bytes: bytes,
        source: SourceRecord,
    ) -> tuple[OptionalAdapterUnit, ...]:
        assert raw_bytes.startswith(b"%PDF-")
        return (
            OptionalAdapterUnit(
                title="PDF page 1",
                exact="Extracted optional-adapter text.",
                locator={"label": "page: 1", "page": 1},
                structured={"unit_kind": "pdf_page", "source_id": source.source_id},
            ),
        )


def _with_hash(source: SourceRecord, digest: str) -> SourceRecord:
    values = source.to_json_dict()
    values["content_sha256"] = digest
    return SourceRecord.model_validate(values)


def _fixture_documents():
    entries = load_source_registry(FIXTURE_ROOT / "source_registry.csv")
    report = SourceDiscovery(
        project_root=FIXTURE_ROOT,
        project_id="fixture-alpha",
        entries=entries,
    ).discover()
    batch = normalize_many(FIXTURE_ROOT, report.records, processed_at=PROCESSED_AT)
    assert not batch.failures
    return {document.source.source_id: document for document in batch.documents}


def test_all_nine_base_formats_normalize_to_public_records_with_exact_bytes() -> None:
    documents = _fixture_documents()
    formats = {document.source.format for document in documents.values()}

    assert formats == {
        "markdown",
        "yaml",
        "csv",
        "toml",
        "json",
        "jsonl",
        "json_schema",
        "text",
        "python",
    }
    assert set(available_adapters()) >= {
        "markdown",
        "yaml",
        "csv",
        "toml",
        "json",
        "jsonl",
        "json_schema",
        "text",
        "python",
        "source_code",
    }
    for document in documents.values():
        path = FIXTURE_ROOT / document.source.path_or_uri
        assert document.raw_bytes == path.read_bytes()
        assert document.source.content_sha256 == hashlib.sha256(document.raw_bytes).hexdigest()
        assert document.records[0].content.exact == document.raw_bytes.decode("utf-8")
        assert document.records[0].record_type == "SourceArtifact"
        for record in document.records:
            assert record.source.source_id == document.source.source_id
            assert record.source.content_sha256 == document.source.content_sha256
            assert record.source.locator
            assert record.processing.adapter_version == "1.0.0"
            assert record.processing.profile_id == "base@1"
            assert record.processing.processed_at == PROCESSED_AT
            assert record.processing.model_extracted_fields == ()
            assert record.processing.model_id is None
            assert record.processing.prompt_fingerprint is None
            assert record.processing.deterministic_fields
            assert record.content.structured["_sys4ai"] == {
                "extractor_version": "1.0.0",
                "profile_version": "1.0.0",
                "extraction": "deterministic",
            }


def test_format_aware_units_preserve_required_natural_locators() -> None:
    documents = _fixture_documents()
    labels = {
        source_id: {str(record.source.locator.get("label")) for record in document.records}
        for source_id, document in documents.items()
    }

    assert "heading: Requirement REQ-ALPHA-042" in labels["src_alpha-requirements"]
    assert "key: completion_authority" in labels["src_alpha-task"]
    assert "row: component_id=COMP-ALPHA-RELAY" in labels["src_alpha-components"]
    assert "section: memory.exact_index" in labels["src_alpha-config"]
    assert "json-pointer: /decisions/0" in labels["src_alpha-decisions"]
    assert "event_id: EVT-ALPHA-001" in labels["src_alpha-events"]
    assert "schema key: /properties/route_label" in labels["src_alpha-schema"]
    assert "paragraph: 1" in labels["src_alpha-notes"]
    assert "symbol: resolve_alpha_route" in labels["src_alpha-code"]


def test_jsonl_event_identity_and_occurrence_time_are_preserved() -> None:
    events = tuple(
        record
        for record in _fixture_documents()["src_alpha-events"].records
        if record.record_type != "SourceArtifact"
    )

    assert [record.record_type for record in events] == ["Event", "Event"]
    assert [record.title for record in events] == ["EVT-ALPHA-001", "EVT-ALPHA-002"]
    assert [record.lifecycle.valid_from for record in events] == [
        datetime(2026, 6, 15, 12, tzinfo=UTC),
        datetime(2026, 7, 2, 12, tzinfo=UTC),
    ]


def test_record_ids_are_stable_when_only_processing_time_changes() -> None:
    entries = load_source_registry(FIXTURE_ROOT / "source_registry.csv")
    report = SourceDiscovery(
        project_root=FIXTURE_ROOT,
        project_id="fixture-alpha",
        entries=entries,
    ).discover()
    source = next(item for item in report.records if item.source_id == "src_alpha-code")

    first = normalize_source(FIXTURE_ROOT, source, processed_at=PROCESSED_AT)
    second = normalize_source(
        FIXTURE_ROOT,
        source,
        processed_at=datetime(2026, 9, 4, 12, tzinfo=UTC),
    )

    assert tuple(item.record_id for item in first.records) == tuple(
        item.record_id for item in second.records
    )


def test_python_symbols_are_qualified_unique_and_stable_across_line_moves() -> None:
    documents = _fixture_documents()
    template = documents["src_alpha-code"].source
    first_raw = (
        b"class Alpha:\n"
        b"    project_id: str\n\n"
        b"class Beta:\n"
        b"    project_id: str\n"
    )
    moved_raw = b"# inserted comment\n" + first_raw
    first = normalize_bytes(
        _with_hash(template, hashlib.sha256(first_raw).hexdigest()),
        first_raw,
        processed_at=PROCESSED_AT,
    )
    moved = normalize_bytes(
        _with_hash(template, hashlib.sha256(moved_raw).hexdigest()),
        moved_raw,
        processed_at=PROCESSED_AT,
    )

    first_by_label = {
        str(record.source.locator["label"]): record.record_id for record in first.records
    }
    moved_by_label = {
        str(record.source.locator["label"]): record.record_id for record in moved.records
    }
    assert "symbol: Alpha.project_id" in first_by_label
    assert "symbol: Beta.project_id" in first_by_label
    assert len(first_by_label) == len(first.records)
    assert first_by_label["symbol: Alpha.project_id"] == moved_by_label[
        "symbol: Alpha.project_id"
    ]


def test_oversized_natural_units_split_into_bounded_deterministic_parts() -> None:
    documents = _fixture_documents()
    template = documents["src_alpha-notes"].source
    raw = ("one two three four five six seven eight nine ten\n" * 4).encode()
    source = _with_hash(template, hashlib.sha256(raw).hexdigest())

    first = normalize_bytes(source, raw, processed_at=PROCESSED_AT, max_chunk_chars=24)
    second = normalize_bytes(source, raw, processed_at=PROCESSED_AT, max_chunk_chars=24)
    fragments = [item for item in first.records if item.record_type != "SourceArtifact"]

    assert fragments
    assert all(len(item.content.exact) <= 24 for item in fragments)
    assert any("[part " in str(item.source.locator["label"]) for item in fragments)
    assert tuple(item.record_id for item in first.records) == tuple(
        item.record_id for item in second.records
    )


def test_repository_ingestion_enforces_a_hard_source_memory_bound(tmp_path: Path) -> None:
    documents = _fixture_documents()
    template = documents["src_alpha-notes"].source
    raw = b"bounded-ingestion-fixture\n" * 32
    root = tmp_path.resolve()
    source_path = root / "large.txt"
    source_path.write_bytes(raw)
    source = _with_hash(template, hashlib.sha256(raw).hexdigest()).model_copy(
        update={"path_or_uri": "large.txt"},
    )

    with pytest.raises(IngestionFailure) as captured:
        normalize_source(
            root,
            source,
            processed_at=PROCESSED_AT,
            max_file_bytes=128,
        )

    assert captured.value.stage == "source_read"
    assert captured.value.category is ErrorCategory.INGESTION_FAILED
    assert captured.value.message == "source exceeds the configured byte limit"
    assert raw.decode() not in captured.value.message


def test_parse_and_hash_failures_are_structured_without_source_content() -> None:
    documents = _fixture_documents()
    template = documents["src_alpha-decisions"].source
    invalid = b'{"decision_id": '
    invalid_source = _with_hash(template, hashlib.sha256(invalid).hexdigest())

    with pytest.raises(IngestionFailure) as captured:
        normalize_bytes(invalid_source, invalid, processed_at=PROCESSED_AT)
    error = captured.value
    assert error.source_id == template.source_id
    assert error.adapter == "json"
    assert error.stage == "parse"
    assert error.category is ErrorCategory.INGESTION_FAILED
    assert invalid.decode() not in error.message
    assert error.recovery_action

    with pytest.raises(IngestionFailure) as drift:
        normalize_bytes(template, b"different", processed_at=PROCESSED_AT)
    assert drift.value.category is ErrorCategory.INDEX_DRIFT
    assert drift.value.stage == "integrity_check"


def test_explicit_optional_binary_adapter_preserves_bytes_and_provenance(
    tmp_path: Path,
) -> None:
    raw = b"%PDF-1.7\n\xff\x00fixture-binary\n"
    digest = hashlib.sha256(raw).hexdigest()
    template = next(
        entry
        for entry in load_source_registry(FIXTURE_ROOT / "source_registry.csv")
        if entry.source_id == "src_alpha-notes"
    )
    entry = replace(
        template,
        source_id="src_optional-pdf",
        path_or_uri="evidence.pdf",
        format="pdf",
        ingestion_adapter="fixture-pdf",
        chunking_profile="page@1",
        registry_path=None,
        row_number=None,
    )
    root = tmp_path.resolve()
    (root / "evidence.pdf").write_bytes(raw)
    report = SourceDiscovery(
        project_root=root,
        project_id="fixture-alpha",
        entries=(entry,),
    ).discover()
    source = report.records[0]
    assert source.content_sha256 == digest

    result = IngestionSynchronizer(
        project_root=root,
        optional_adapters=(FixturePdfAdapter(),),
    ).synchronize(report, processed_at=PROCESSED_AT)

    assert not result.failures
    document = result.documents[0]
    assert document.raw_bytes == raw
    assert document.adapter_id == "fixture-pdf"
    assert document.adapter_version == "1.2.0"
    assert len(document.records) == 2
    artifact, page = document.records
    assert artifact.record_type == "SourceArtifact"
    assert digest in artifact.content.exact
    assert page.title == "PDF page 1"
    assert page.content.exact == "Extracted optional-adapter text."
    assert page.source.locator == {"label": "page: 1", "page": 1}
    assert page.processing.parsed_by == "sys4ai_memory.ingestion.fixture-pdf"
    assert page.processing.adapter_version == "1.2.0"
    assert "fixture-pdf" in available_adapters((FixturePdfAdapter(),))


def test_software_engineering_adapter_classifies_deterministic_python_symbols() -> None:
    raw = b'''BUILD_TARGET = "wheel"

class ParserError(Exception):
    pass

def parse(value: str) -> str:
    return value

def test_parse() -> None:
    assert parse("ok") == "ok"
'''
    documents = _fixture_documents()
    values = documents["src_alpha-code"].source.to_json_dict()
    values.update(
        {
            "source_id": "src_software-profile",
            "path_or_uri": "src/example.py",
            "profile_id": "software-engineering@1",
            "ingestion_adapter": "software-python-ast@1",
            "content_sha256": hashlib.sha256(raw).hexdigest(),
        }
    )
    source = SourceRecord.model_validate(values)

    document = normalize_bytes(
        source,
        raw,
        processed_at=PROCESSED_AT,
        profile_version="1.0.0",
        optional_adapters=(SoftwareEngineeringPythonAdapter(),),
    )

    typed = document.records[1:]
    assert {record.record_type for record in typed} == {
        "BuildTarget",
        "CodeSymbol",
        "FailurePattern",
        "TestCase",
    }
    assert all(
        record.profile_type == f"software-engineering@1:{record.record_type}"
        for record in typed
    )
    assert all(record.processing.adapter_version == "1.0.0" for record in typed)


def test_optional_format_fails_closed_without_its_exact_adapter() -> None:
    raw = b"%PDF-1.7\n\xff\x00fixture-binary\n"
    documents = _fixture_documents()
    values = documents["src_alpha-notes"].source.to_json_dict()
    values.update(
        {
            "source_id": "src_optional-missing",
            "path_or_uri": "missing.pdf",
            "format": "pdf",
            "ingestion_adapter": "missing-pdf-adapter",
            "content_sha256": hashlib.sha256(raw).hexdigest(),
        }
    )
    source = SourceRecord.model_validate(values)

    with pytest.raises(IngestionFailure) as caught:
        normalize_bytes(source, raw, processed_at=PROCESSED_AT)

    assert caught.value.stage == "adapter_selection"
    assert caught.value.category is ErrorCategory.INGESTION_FAILED
    assert raw.decode("latin-1") not in caught.value.message
