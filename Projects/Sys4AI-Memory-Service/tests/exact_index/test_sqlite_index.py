from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.contracts import RecordStatus, SourceRecord
from sys4ai_memory.exact_index import ExactIndex, IndexGeneration
from sys4ai_memory.ingestion import normalize_bytes, normalize_many
from sys4ai_memory.sources import SourceDiscovery, load_source_registry

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURES = PROJECT_ROOT / "tests/fixtures/projects"
PROCESSED_AT = datetime(2026, 9, 3, 12, tzinfo=UTC)


def _documents(project_name: str, project_id: str):
    root = FIXTURES / project_name
    report = SourceDiscovery(
        project_root=root,
        project_id=project_id,
        entries=load_source_registry(root / "source_registry.csv"),
    ).discover()
    batch = normalize_many(root, report.records, processed_at=PROCESSED_AT)
    assert not batch.failures
    return report, batch.documents


def _replace_hash(source: SourceRecord, raw: bytes) -> SourceRecord:
    values = source.to_json_dict()
    values["content_sha256"] = hashlib.sha256(raw).hexdigest()
    values["working_tree_state"] = "modified"
    return SourceRecord.model_validate(values)


def test_fts5_feature_and_golden_exact_lexical_cases_are_project_scoped() -> None:
    _, alpha = _documents("project_alpha", "fixture-alpha")
    _, beta = _documents("project_beta", "fixture-beta")
    with ExactIndex(":memory:") as index:
        for document in (*alpha, *beta):
            index.upsert_document(document)

        assert index.fts5_available
        requirement = index.query_exact(
            project_id="fixture-alpha", query="REQ-ALPHA-042"
        )
        assert requirement
        assert requirement[0].source.source_id == "src_alpha-requirements"
        assert requirement[0].source.path == "docs/requirements.md"
        assert requirement[0].source.locator["label"] == (
            "heading: Requirement REQ-ALPHA-042"
        )
        assert requirement[0].scores.exact == 1.0
        assert requirement[0].scores.final == 1.0

        symbol = index.query_exact(
            project_id="fixture-beta", query="resolve_beta_route"
        )
        assert symbol
        assert symbol[0].source.source_id == "src_beta-code"
        assert symbol[0].source.locator["label"] == "symbol: resolve_beta_route"
        source_revision = symbol[0].source.locator["source_revision"]
        assert isinstance(source_revision, str)
        assert symbol[0].source.path is not None
        hydrated = index.resolve_record(
            project_id="fixture-beta",
            record_id=symbol[0].record_id,
            source_revision=source_revision,
            source_path=symbol[0].source.path,
        )
        assert hydrated is not None
        assert hydrated.record_id == symbol[0].record_id
        assert hydrated.namespace == "code/fixture-beta"
        assert (
            index.resolve_record(
                project_id="fixture-alpha",
                record_id=symbol[0].record_id,
                source_revision=source_revision,
                source_path=symbol[0].source.path,
            )
            is None
        )
        assert not index.query_exact(
            project_id="fixture-beta", query="RESOLVE_BETA_ROUTE", case_sensitive=True
        )
        assert index.query_exact(
            project_id="fixture-beta", query="RESOLVE_BETA_ROUTE", case_sensitive=False
        )

        phrase = index.query_lexical(
            project_id="fixture-alpha",
            query="amber horizon calibration",
            phrase=True,
        )
        assert phrase
        assert phrase[0].source.source_id == "src_alpha-notes"
        assert phrase[0].source.locator["label"] == (
            "literal phrase: amber horizon calibration"
        )
        assert not index.query_exact(project_id="fixture-beta", query="REQ-ALPHA-042")


def test_exact_hash_path_schema_key_and_lexical_prefix_field_queries() -> None:
    _, documents = _documents("project_alpha", "fixture-alpha")
    by_source = {item.source.source_id: item for item in documents}
    with ExactIndex(":memory:") as index:
        for document in documents:
            index.upsert_document(document)

        path_matches = index.query_exact(
            project_id="fixture-alpha",
            query="docs/requirements.md",
            field="path",
        )
        assert path_matches
        assert all(item.source.path == "docs/requirements.md" for item in path_matches)

        schema_matches = index.query_exact(
            project_id="fixture-alpha", query="route_label", field="schema_key"
        )
        assert schema_matches
        assert schema_matches[0].source.locator["label"] == (
            "schema key: /properties/route_label"
        )

        digest = by_source["src_alpha-code"].source.content_sha256
        assert digest is not None
        hash_matches = index.query_exact(
            project_id="fixture-alpha", query=digest, field="hash"
        )
        assert hash_matches
        assert all(item.source.source_id == "src_alpha-code" for item in hash_matches)

        prefix_matches = index.query_lexical(
            project_id="fixture-alpha", query="calib", prefix=True, field="content"
        )
        assert prefix_matches
        assert prefix_matches[0].source.source_id == "src_alpha-notes"
        field_matches = index.query_lexical(
            project_id="fixture-alpha", query="requirements", field="path"
        )
        assert field_matches
        assert all(item.source.path == "docs/requirements.md" for item in field_matches)


def test_upsert_is_idempotent_and_changed_source_rolls_back_as_one_transaction() -> None:
    _, documents = _documents("project_alpha", "fixture-alpha")
    notes = next(item for item in documents if item.source.source_id == "src_alpha-notes")
    with ExactIndex(":memory:") as index:
        first = index.upsert_document(notes)
        count = index.health("fixture-alpha").current_record_count
        second = index.upsert_document(notes)

        assert first.action == "added"
        assert second.action == "unchanged"
        assert second.records_written == 0
        assert index.health("fixture-alpha").current_record_count == count

        changed_raw = notes.raw_bytes + b"New rollback-only marker.\n"
        changed_source = _replace_hash(notes.source, changed_raw)
        changed = normalize_bytes(
            changed_source,
            changed_raw,
            processed_at=datetime(2026, 9, 4, 12, tzinfo=UTC),
        )

        def fail_after_deactivate(stage: str, _: int) -> None:
            if stage == "after_deactivate":
                raise RuntimeError("injected transaction failure")

        with pytest.raises(RuntimeError, match="injected transaction failure"):
            index.upsert_document(changed, fault_hook=fail_after_deactivate)

        assert index.query_lexical(
            project_id="fixture-alpha", query="amber horizon calibration", phrase=True
        )
        assert not index.query_exact(
            project_id="fixture-alpha", query="rollback-only"
        )
        history = index.source_history("fixture-alpha", notes.source.source_id)
        assert len(history) == 1
        assert history[0]["is_current"] == 1

        index.upsert_document(changed)
        revisions = index.query_lexical(
            project_id="fixture-alpha",
            query="amber horizon calibration",
            phrase=True,
            current_only=False,
        )
        prior = next(item for item in revisions if item.lifecycle.status is RecordStatus.SUPERSEDED)
        source_revision = prior.source.locator["source_revision"]
        assert isinstance(source_revision, str)
        assert prior.source.path is not None
        hydrated = index.resolve_record(
            project_id="fixture-alpha",
            record_id=prior.record_id,
            source_revision=source_revision,
            source_path=prior.source.path,
        )
        assert hydrated is not None
        assert hydrated.lifecycle.status is RecordStatus.SUPERSEDED
        assert hydrated.lifecycle.valid_to is not None


def test_current_and_historical_status_are_kept_separate() -> None:
    _, documents = _documents("project_alpha", "fixture-alpha")
    with ExactIndex(":memory:") as index:
        for document in documents:
            index.upsert_document(document)

        current = index.query_exact(
            project_id="fixture-alpha", query="DEC-ALPHA-001"
        )
        historical = index.query_exact(
            project_id="fixture-alpha",
            query="DEC-ALPHA-001",
            current_only=False,
        )

        assert not any(
            item.source.source_id == "src_alpha-decisions"
            and item.source.locator.get("json_pointer") == "/decisions/0"
            for item in current
        )
        assert any(
            item.source.source_id == "src_alpha-decisions"
            and item.source.locator.get("json_pointer") == "/decisions/0"
            and item.lifecycle.status is RecordStatus.SUPERSEDED
            for item in historical
        )


def test_supersession_atomically_reindexes_current_and_historical_views() -> None:
    _, documents = _documents("project_alpha", "fixture-alpha")
    changed_at = datetime(2026, 9, 3, 18, tzinfo=UTC)
    with ExactIndex(":memory:") as index:
        for document in documents:
            index.upsert_document(document)
        prior = index.query_exact(
            project_id="fixture-alpha",
            query="REQ-ALPHA-042",
        )[0]
        replacement = index.query_exact(
            project_id="fixture-alpha",
            query="control/task.yaml",
        )[0]

        indexed_prior, indexed_replacement = index.supersede_records(
            project_id="fixture-alpha",
            prior_record_id=prior.record_id,
            replacement_record_id=replacement.record_id,
            at=changed_at,
        )

        assert indexed_prior.lifecycle.status is RecordStatus.SUPERSEDED
        assert indexed_prior.lifecycle.valid_to == changed_at
        assert indexed_prior.lifecycle.superseded_by == (replacement.record_id,)
        assert indexed_replacement.lifecycle.supersedes == (prior.record_id,)
        assert not any(
            item.record_id == prior.record_id
            for item in index.query_exact(
                project_id="fixture-alpha",
                query="REQ-ALPHA-042",
            )
        )
        historical = index.query_exact(
            project_id="fixture-alpha",
            query="REQ-ALPHA-042",
            current_only=False,
        )
        historical_prior = next(item for item in historical if item.record_id == prior.record_id)
        assert historical_prior.lifecycle.status is RecordStatus.SUPERSEDED
        source_revision = historical_prior.source.locator["source_revision"]
        assert isinstance(source_revision, str)
        assert historical_prior.source.path is not None
        hydrated_prior = index.resolve_record(
            project_id="fixture-alpha",
            record_id=prior.record_id,
            source_revision=source_revision,
            source_path=historical_prior.source.path,
        )
        assert hydrated_prior is not None
        assert hydrated_prior.lifecycle.superseded_by == (replacement.record_id,)


def test_rebuild_activates_atomically_and_failed_candidate_keeps_previous_generation() -> None:
    _, documents = _documents("project_alpha", "fixture-alpha")
    with ExactIndex(":memory:") as index:
        for document in documents:
            index.upsert_document(document)
        previous = index.health("fixture-alpha")
        generation = IndexGeneration.create(
            project_id="fixture-alpha",
            configuration_fingerprint="b" * 64,
            profile_versions={"base@1": "1.0.0"},
            adapter_versions={"base": "1.0.0"},
            created_at=datetime(2026, 9, 5, tzinfo=UTC),
            identity="rebuild-test",
        )

        def fail_candidate(stage: str, index_value: int) -> None:
            if stage == "after_source" and index_value == 0:
                raise RuntimeError("injected rebuild failure")

        with pytest.raises(RuntimeError, match="injected rebuild failure"):
            index.rebuild(generation, documents, fault_hook=fail_candidate)

        after_failure = index.health("fixture-alpha")
        assert after_failure.active_generation_id == previous.active_generation_id
        assert after_failure.current_record_count == previous.current_record_count
        assert index.query_exact(project_id="fixture-alpha", query="REQ-ALPHA-042")

        rebuilt = index.rebuild(generation, documents)
        assert rebuilt.sources_written == len(documents)
        assert index.health("fixture-alpha").active_generation_id == generation.generation_id
        assert index.query_exact(project_id="fixture-alpha", query="REQ-ALPHA-042")


def test_exclusion_explanations_store_metadata_only() -> None:
    report, _ = _documents("project_alpha", "fixture-alpha")
    enriched = SourceDiscovery(
        project_root=report.project_root,
        project_id=report.project_id,
        entries=load_source_registry(report.project_root / "source_registry.csv"),
    ).discover(candidate_paths=("unregistered.md",))
    with ExactIndex(":memory:") as index:
        index.record_discovery_report(enriched)
        explanation = index.explain_source_exclusion(
            "fixture-alpha", "unregistered.md"
        )

        assert explanation is not None
        assert explanation.disposition == "unmatched"
        assert explanation.reason == "default_deny_unmatched"
        assert explanation.rule_ids == ()
