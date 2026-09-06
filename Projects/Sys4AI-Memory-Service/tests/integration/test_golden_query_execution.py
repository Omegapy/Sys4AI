from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
    PermissionDeniedError,
)
from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    EvidenceState,
    MemoryScope,
    RecordStatus,
    RelationRecord,
    RetrievalMode,
    RetrievalResult,
    ScopeReference,
)
from sys4ai_memory.contracts.models import (
    MemoryRecord,
    RelationLifecycle,
    RelationSource,
    RelationValidation,
    RequesterIdentity,
    RetrievedRecord,
    TemporalMetadata,
)
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import IngestionBatchResult, normalize_many
from sys4ai_memory.providers import (
    InMemoryProviderConfig,
    ProviderContext,
    ProviderInitializationRequest,
    ProviderMutation,
    RememberRequest,
)
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.retrieval import RecallQuery, RetrievalEngine
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.sources import SourceDiscovery, load_source_registry
from tests.providers.helpers import policy

pytestmark = [pytest.mark.integration, pytest.mark.acceptance, pytest.mark.security]

PROJECT_ROOT = Path(__file__).parents[2]
GOLDEN_PATH = PROJECT_ROOT / "tests/golden_queries/queries.jsonl"
FIXTURE_ROOTS = {
    "fixture-alpha": PROJECT_ROOT / "tests/fixtures/projects/project_alpha",
    "fixture-beta": PROJECT_ROOT / "tests/fixtures/projects/project_beta",
}
NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)


def _load_cases() -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


CASES = _load_cases()
DETERMINISTIC_CASES = tuple(
    case for case in CASES if case.get("mode") in {"exact", "lexical"}
)
HYBRID_CASES = tuple(case for case in CASES if case.get("mode") == "hybrid")


def _normalize(project_id: str) -> IngestionBatchResult:
    fixture_root = FIXTURE_ROOTS[project_id]
    report = SourceDiscovery(
        project_root=fixture_root,
        project_id=project_id,
        entries=load_source_registry(fixture_root / "source_registry.csv"),
    ).discover()
    result = normalize_many(fixture_root, report.records, processed_at=NOW)
    assert not result.failures
    return result


def _write_permissions(root: Path, project_id: str, dataset_id: str) -> None:
    path = root / "control/permissions.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "revision": "golden-query-execution-1",
                "project_id": project_id,
                "dataset_id": dataset_id,
                "issued_at": NOW.isoformat().replace("+00:00", "Z"),
                "grants": [
                    {
                        "grant_id": "golden-query-reader",
                        "principal_id": "agent-golden-query",
                        "permissions": ["read"],
                        "operations": [],
                        "scopes": [
                            {
                                "level": "project",
                                "scope_id": project_id,
                                "parent_scopes": [],
                            }
                        ],
                        "target_prefixes": [],
                        "shared_project_ids": [],
                        "valid_until": None,
                    }
                ],
                "approval_policy": None,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _authorizer(root: Path, project_id: str, dataset_id: str) -> AuthorizationService:
    _write_permissions(root, project_id, dataset_id)
    return AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            ProjectBoundary(project_id, dataset_id, root),
            "control/permissions.json",
        )
    )


def _query(case: Mapping[str, object], *, suffix: str) -> RecallQuery:
    project_id = str(case["project_id"])
    mode = RetrievalMode(str(case["mode"]))
    outcomes = tuple(str(item) for item in case["required_policy_outcomes"])  # type: ignore[union-attr]
    at_time_raw = case.get("as_of")
    at_time = (
        datetime.fromisoformat(str(at_time_raw).replace("Z", "+00:00"))
        if at_time_raw is not None
        else None
    )
    requested_projects = tuple(
        str(item) for item in case.get("requested_project_ids", ())  # type: ignore[union-attr]
    )
    return RecallQuery(
        request_id=f"mrq_golden_{suffix}",
        trace_id=f"trace_golden_{suffix}",
        project_id=project_id,
        dataset_id=f"{project_id}-memory",
        requester=RequesterIdentity(
            principal_id="agent-golden-query",
            agent_type="test-agent",
            run_id=f"run-golden-{suffix}",
        ),
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=project_id),
        query=str(case["query"]),
        mode=mode,
        current_only=bool(case["current_only"]),
        at_time=at_time,
        requested_project_ids=requested_projects,
        explicit_cross_project=len(requested_projects) > 1,
        case_sensitive="case_sensitive_symbol_match" in outcomes,
        lexical_phrase=mode is RetrievalMode.LEXICAL,
    )


def _matches_anchor(
    record: RetrievedRecord,
    anchor: Mapping[str, object],
    *,
    result_project_id: str,
) -> bool:
    anchor_project = anchor.get("project_id")
    if anchor_project is not None and str(anchor_project) != result_project_id:
        return False
    if anchor.get("source_id") is not None and record.source.source_id != anchor["source_id"]:
        return False
    if anchor.get("path") is not None and record.source.path != anchor["path"]:
        return False
    expected_locator = anchor.get("locator")
    if expected_locator is None:
        return True
    expected = str(expected_locator)
    if expected.casefold().startswith("literal phrase:"):
        phrase = expected.split(":", 1)[1].strip().casefold()
        return phrase in record.content.casefold()
    return record.source.locator.get("label") == expected


def _record(
    records: tuple[MemoryRecord, ...],
    source_id: str,
    locator: str,
) -> MemoryRecord:
    return next(
        record
        for record in records
        if record.source.source_id == source_id
        and record.source.locator.get("label") == locator
    )


def _relation(
    relation_id: str,
    relation_type: str,
    source: MemoryRecord,
    target: MemoryRecord,
    *,
    source_id: str,
    valid_from: datetime,
) -> RelationRecord:
    return RelationRecord(
        schema_version=SCHEMA_VERSION,
        api_version=API_VERSION,
        relation_id=relation_id,
        project_id="fixture-alpha",
        relation_type=relation_type,
        source_record_id=source.record_id,
        target_record_id=target.record_id,
        source=RelationSource(source_id=source_id, locator=dict(source.source.locator)),
        validation=RelationValidation(state="deterministic-fixture", confidence=None),
        temporal=TemporalMetadata(valid_from=valid_from, valid_to=None),
        lifecycle=RelationLifecycle(status=RecordStatus.ACTIVE),
    )


def _fixture_relations(records: tuple[MemoryRecord, ...]) -> tuple[RelationRecord, ...]:
    relay = _record(
        records,
        "src_alpha-components",
        "row: component_id=COMP-ALPHA-RELAY",
    )
    exact_index = _record(
        records,
        "src_alpha-components",
        "row: component_id=COMP-ALPHA-INDEX",
    )
    completion_authority = _record(
        records,
        "src_alpha-task",
        "key: completion_authority",
    )
    runtime_boundary = _record(
        records,
        "src_alpha-requirements",
        "heading: Runtime state boundary",
    )
    event = _record(records, "src_alpha-events", "event_id: EVT-ALPHA-001")
    historical_decision = _record(
        records,
        "src_alpha-decisions",
        "json-pointer: /decisions/0",
    )
    return (
        _relation(
            "rel_ALPHA_RELAY_DEPENDS_ON_INDEX",
            "DEPENDS_ON",
            relay,
            exact_index,
            source_id="src_alpha-components",
            valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        _relation(
            "rel_ALPHA_CONTROL_VALIDATES_RUNTIME",
            "VALIDATES",
            completion_authority,
            runtime_boundary,
            source_id="src_alpha-task",
            valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        _relation(
            "rel_ALPHA_EVENT_OBSERVED_DURING_DECISION",
            "OBSERVED_DURING",
            event,
            historical_decision,
            source_id="src_alpha-events",
            valid_from=datetime(2026, 6, 15, 12, tzinfo=UTC),
        ),
    )


async def _seed_provider(
    normalized: IngestionBatchResult,
) -> InMemoryProvider:
    provider = InMemoryProvider(
        InMemoryProviderConfig(
            project_id="fixture-alpha",
            dataset_id="fixture-alpha-memory",
        )
    )
    context = ProviderContext(
        project_id="fixture-alpha",
        dataset_id="fixture-alpha-memory",
        principal_id="agent-golden-query",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id="fixture-alpha"),
        trace_id="trace_golden_provider_setup",
    )
    records = tuple(
        record for document in normalized.documents for record in document.records
    )
    await provider.initialize(
        ProviderInitializationRequest(
            context=context,
            configuration_fingerprint="a" * 64,
            dry_run=False,
            authorization=policy(ProviderMutation.INITIALIZE, context),
        )
    )
    await provider.remember(
        RememberRequest(
            context=context,
            request_id="mrq_golden_provider_seed",
            idempotency_key="golden-provider-seed",
            records=records,
            relations=_fixture_relations(records),
            sources=tuple(document.source for document in normalized.documents),
            authorization=policy(ProviderMutation.REMEMBER, context),
        )
    )
    return provider


def test_golden_query_contract_resolves_every_declared_source_anchor() -> None:
    identifiers = [str(case["query_id"]) for case in CASES]
    assert len(CASES) == 10
    assert len(identifiers) == len(set(identifiers))
    assert {str(case["query_class"]) for case in CASES} == {
        "exact",
        "lexical",
        "conceptual",
        "dependency",
        "temporal",
        "no_answer",
        "supersession",
        "project_isolation",
    }

    normalized = {project_id: _normalize(project_id) for project_id in FIXTURE_ROOTS}
    records_by_project = {
        project_id: tuple(
            record for document in result.documents for record in document.records
        )
        for project_id, result in normalized.items()
    }
    for case in CASES:
        case_project = str(case["project_id"])
        expected = case["expected_source_anchors"]
        forbidden = case["forbidden_source_anchors"]
        assert isinstance(expected, list)
        assert isinstance(forbidden, list)
        for raw_anchor in (*expected, *forbidden):
            assert isinstance(raw_anchor, dict)
            anchor_project = str(raw_anchor.get("project_id", case_project))
            source_id = raw_anchor.get("source_id")
            source_path = raw_anchor.get("path")
            candidates = records_by_project[anchor_project]
            assert any(
                (source_id is None or record.source.source_id == source_id)
                and (source_path is None or record.source.path == source_path)
                for record in candidates
            ), (case["query_id"], raw_anchor)
            locator = raw_anchor.get("locator")
            if locator is None:
                continue
            locator_text = str(locator)
            if locator_text.casefold().startswith("literal phrase:"):
                phrase = locator_text.split(":", 1)[1].strip().casefold()
                assert any(
                    record.source.source_id == source_id
                    and phrase in record.content.exact.casefold()
                    for record in candidates
                ), (case["query_id"], raw_anchor)
            else:
                assert any(
                    record.source.source_id == source_id
                    and record.source.locator.get("label") == locator_text
                    for record in candidates
                ), (case["query_id"], raw_anchor)


@pytest.mark.parametrize(
    "case",
    DETERMINISTIC_CASES,
    ids=lambda case: str(case["query_id"]),
)
@pytest.mark.asyncio
async def test_exact_and_lexical_golden_queries_execute_against_normalized_sources(
    case: dict[str, object],
    tmp_path: Path,
) -> None:
    project_id = str(case["project_id"])
    dataset_id = f"{project_id}-memory"
    normalized = _normalize(project_id)
    authorizer = _authorizer(tmp_path.resolve(), project_id, dataset_id)
    mode = RetrievalMode(str(case["mode"]))

    with ExactIndex(":memory:") as index:
        for document in normalized.documents:
            index.upsert_document(document)
        engine = RetrievalEngine(
            project_id=project_id,
            dataset_id=dataset_id,
            authorizer=authorizer,
            exact_backend=index,
            clock=lambda: NOW,
        )
        result, trace = await engine.recall_with_trace(
            _query(case, suffix=str(case["query_id"]).lower().replace("-", "_"))
        )

    assert result.evidence_state.value == case["expected_evidence_state"]
    assert RetrievalResult.model_validate(result.to_json_dict()) == result
    assert trace.selected_channels == (mode,)
    assert result.filters_applied.permission
    expected = case["expected_source_anchors"]
    forbidden = case["forbidden_source_anchors"]
    assert isinstance(expected, list)
    assert isinstance(forbidden, list)
    for anchor in expected:
        assert isinstance(anchor, dict)
        assert any(
            _matches_anchor(record, anchor, result_project_id=result.project_id)
            for record in result.results
        ), (case["query_id"], anchor)
    for anchor in forbidden:
        assert isinstance(anchor, dict)
        assert not any(
            _matches_anchor(record, anchor, result_project_id=result.project_id)
            for record in result.results
        ), (case["query_id"], anchor)
    assert all(record.source.locator.get("source_revision") for record in result.results)
    if mode is RetrievalMode.EXACT:
        assert result.results[0].scores.exact == 1.0
    else:
        assert result.results[0].scores.lexical > 0.0


@pytest.mark.parametrize(
    "case",
    HYBRID_CASES,
    ids=lambda case: str(case["query_id"]),
)
@pytest.mark.asyncio
async def test_hybrid_golden_queries_execute_with_scoped_provider_evidence(
    case: dict[str, object],
    tmp_path: Path,
) -> None:
    normalized = _normalize("fixture-alpha")
    provider = await _seed_provider(normalized)
    authorizer = _authorizer(
        tmp_path.resolve(),
        "fixture-alpha",
        "fixture-alpha-memory",
    )
    suffix = str(case["query_id"]).lower().replace("-", "_")
    query = _query(case, suffix=suffix)

    with ExactIndex(":memory:") as index:
        for document in normalized.documents:
            index.upsert_document(document)
        engine = RetrievalEngine(
            project_id="fixture-alpha",
            dataset_id="fixture-alpha-memory",
            authorizer=authorizer,
            exact_backend=index,
            provider=provider,
            clock=lambda: NOW,
        )
        if case["expected_evidence_state"] == "denied":
            assert case.get("expected_error_category") == "PERMISSION_DENIED"
            with pytest.raises(PermissionDeniedError):
                await engine.recall_with_trace(query)
            return
        result, trace = await engine.recall_with_trace(query)

    assert result.evidence_state.value == case["expected_evidence_state"]
    assert RetrievalResult.model_validate(result.to_json_dict()) == result
    assert trace.selected_channels == (
        RetrievalMode.EXACT,
        RetrievalMode.LEXICAL,
        RetrievalMode.SEMANTIC,
        RetrievalMode.GRAPH,
        RetrievalMode.TEMPORAL,
    )
    assert result.filters_applied.permission
    expected = case["expected_source_anchors"]
    forbidden = case["forbidden_source_anchors"]
    assert isinstance(expected, list)
    assert isinstance(forbidden, list)
    for anchor in expected:
        assert isinstance(anchor, dict)
        assert any(
            _matches_anchor(record, anchor, result_project_id=result.project_id)
            for record in result.results
        ), (case["query_id"], anchor)
    for anchor in forbidden:
        assert isinstance(anchor, dict)
        assert not any(
            _matches_anchor(record, anchor, result_project_id=result.project_id)
            for record in result.results
        ), (case["query_id"], anchor)

    outcomes = set(str(item) for item in case["required_policy_outcomes"])  # type: ignore[union-attr]
    if "historical_mode_applied" in outcomes:
        assert not result.filters_applied.current_only
        assert result.filters_applied.time_constraints["at_time"] == (
            "2026-06-15T12:00:00Z"
        )
        assert all(
            record.scores.temporal > 0.0
            for anchor in expected
            for record in result.results
            if isinstance(anchor, dict)
            and _matches_anchor(record, anchor, result_project_id=result.project_id)
        )
    if "current_status_filter_applied" in outcomes:
        assert all(
            record.lifecycle.status in {RecordStatus.ACTIVE, RecordStatus.APPROVED}
            for record in result.results
        )
    if "typed_dependency_relation_returned" in outcomes:
        assert any(
            "graph_relation=rel_ALPHA_RELAY_DEPENDS_ON_INDEX"
            in record.selection_reason
            for record in result.results
        )
        assert any(
            "graph_relation_source=src_alpha-components" in record.selection_reason
            for record in result.results
        )
    if case["query_class"] == "conceptual":
        expected_records = tuple(
            record
            for anchor in expected
            for record in result.results
            if isinstance(anchor, dict)
            and _matches_anchor(record, anchor, result_project_id=result.project_id)
        )
        assert expected_records
        assert any(record.scores.semantic > 0.0 for record in expected_records)
        assert any(record.scores.graph > 0.0 for record in expected_records)
    if result.evidence_state is EvidenceState.INSUFFICIENT:
        assert case.get("expected_error_category") == "INSUFFICIENT_EVIDENCE"
        assert result.results == ()


@pytest.mark.asyncio
async def test_normalized_event_occurrence_time_controls_temporal_recall(
    tmp_path: Path,
) -> None:
    project_id = "fixture-alpha"
    dataset_id = "fixture-alpha-memory"
    normalized = _normalize(project_id)
    event_document = next(
        document
        for document in normalized.documents
        if document.source.source_id == "src_alpha-events"
    )
    event = next(record for record in event_document.records if record.title == "EVT-ALPHA-001")
    occurred_at = datetime(2026, 6, 15, 12, tzinfo=UTC)
    assert event.record_type == "Event"
    assert event.lifecycle.valid_from == occurred_at

    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=project_id, dataset_id=dataset_id)
    )
    context = ProviderContext(
        project_id=project_id,
        dataset_id=dataset_id,
        principal_id="agent-golden-query",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=project_id),
        trace_id="trace_golden_temporal_setup",
    )
    await provider.initialize(
        ProviderInitializationRequest(
            context=context,
            configuration_fingerprint="a" * 64,
            dry_run=False,
            authorization=policy(ProviderMutation.INITIALIZE, context),
        )
    )
    await provider.remember(
        RememberRequest(
            context=context,
            request_id="mrq_golden_temporal_seed",
            idempotency_key="golden-temporal-seed",
            records=(event,),
            sources=(event_document.source,),
            authorization=policy(ProviderMutation.REMEMBER, context),
        )
    )
    engine = RetrievalEngine(
        project_id=project_id,
        dataset_id=dataset_id,
        authorizer=_authorizer(tmp_path.resolve(), project_id, dataset_id),
        provider=provider,
        clock=lambda: NOW,
    )

    before = RecallQuery(
        request_id="mrq_golden_temporal_before",
        trace_id="trace_golden_temporal_before",
        project_id=project_id,
        dataset_id=dataset_id,
        requester=RequesterIdentity(
            principal_id="agent-golden-query",
            agent_type="test-agent",
            run_id="run-golden-temporal-before",
        ),
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=project_id),
        query="EVT-ALPHA-001",
        mode=RetrievalMode.TEMPORAL,
        current_only=False,
        at_time=occurred_at - timedelta(seconds=1),
    )
    at_occurrence = before.model_copy(
        update={
            "request_id": "mrq_golden_temporal_at",
            "trace_id": "trace_golden_temporal_at",
            "at_time": occurred_at,
        }
    )
    absent = await engine.recall(before)
    present, trace = await engine.recall_with_trace(at_occurrence)

    assert absent.evidence_state is EvidenceState.INSUFFICIENT
    assert absent.results == ()
    assert present.evidence_state is EvidenceState.SUFFICIENT
    assert RetrievalResult.model_validate(present.to_json_dict()) == present
    assert [record.record_id for record in present.results] == [event.record_id]
    assert present.results[0].source.source_id == "src_alpha-events"
    assert present.results[0].source.locator["label"] == "event_id: EVT-ALPHA-001"
    assert trace.selected_channels == (RetrievalMode.TEMPORAL,)
