from __future__ import annotations

import pytest

from sys4ai_memory.contracts import MemoryScope, RetrievalMode, ScopeReference
from sys4ai_memory.contracts.models import RequesterIdentity
from sys4ai_memory.retrieval import ContextBudget, QueryIntent, QueryPlanner, RecallQuery


def _query(text: str, **updates: object) -> RecallQuery:
    values: dict[str, object] = {
        "request_id": "mrq_planner",
        "trace_id": "trace_planner",
        "project_id": "project-alpha",
        "dataset_id": "dataset-alpha",
        "requester": RequesterIdentity(
            principal_id="agent-alpha",
            agent_type="test-agent",
            run_id="run-planner",
        ),
        "scope": ScopeReference(level=MemoryScope.PROJECT, scope_id="project-alpha"),
        "query": text,
    }
    values.update(updates)
    return RecallQuery.model_validate(values)


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("REQ-ALPHA-042", QueryIntent.EXACT_LOOKUP),
        ("Where is the file path for the relay?", QueryIntent.SOURCE_LOOKUP),
        ("Which requirement governs relay completion?", QueryIntent.REQUIREMENT_LOOKUP),
        ("What decision selected the provider?", QueryIntent.DECISION_LOOKUP),
        ("How to rebuild the index?", QueryIntent.PROCEDURE_LOOKUP),
        ("Explain provider neutrality", QueryIntent.SEMANTIC_QUESTION),
        ("What does COMP-ALPHA depend on?", QueryIntent.DEPENDENCY_QUERY),
        ("What evidence came from the source anchor?", QueryIntent.PROVENANCE_QUERY),
        ("What was the prior routing state?", QueryIntent.HISTORICAL_QUERY),
        ("Find a similar case for this failure", QueryIntent.SIMILAR_CASE_QUERY),
        ("What is the current active state?", QueryIntent.CURRENT_STATE_QUERY),
    ),
)
def test_classifier_covers_every_prd_query_intent(text: str, expected: QueryIntent) -> None:
    assert QueryPlanner().classify(text) is expected


def test_explicit_intent_override_is_inspectable() -> None:
    plan = QueryPlanner().plan(_query("REQ-ALPHA-042", intent=QueryIntent.PROCEDURE_LOOKUP))

    assert plan.intent is QueryIntent.PROCEDURE_LOOKUP
    assert plan.intent_overridden
    assert "intent_source=caller_override" in plan.explanations


def test_code_symbol_routes_to_exact_without_a_model() -> None:
    plan = QueryPlanner().plan(_query("resolve_beta_route"))

    assert plan.intent is QueryIntent.EXACT_LOOKUP
    assert plan.channels == (RetrievalMode.EXACT,)

    command_plan = QueryPlanner().plan(_query("sys4ai-memory recall --project alpha"))
    assert command_plan.intent is QueryIntent.EXACT_LOOKUP
    assert command_plan.channels == (RetrievalMode.EXACT,)


@pytest.mark.parametrize(
    ("mode", "channels"),
    (
        (RetrievalMode.EXACT, (RetrievalMode.EXACT,)),
        (RetrievalMode.LEXICAL, (RetrievalMode.LEXICAL,)),
        (RetrievalMode.SEMANTIC, (RetrievalMode.SEMANTIC,)),
        (RetrievalMode.GRAPH, (RetrievalMode.GRAPH,)),
        (RetrievalMode.TEMPORAL, (RetrievalMode.TEMPORAL,)),
        (
            RetrievalMode.HYBRID,
            (
                RetrievalMode.EXACT,
                RetrievalMode.LEXICAL,
                RetrievalMode.SEMANTIC,
                RetrievalMode.GRAPH,
                RetrievalMode.TEMPORAL,
            ),
        ),
    ),
)
def test_explicit_mode_plans_each_channel_and_hybrid(
    mode: RetrievalMode, channels: tuple[RetrievalMode, ...]
) -> None:
    plan = QueryPlanner().plan(_query("Explain the relay", mode=mode))

    assert plan.channels == channels
    assert plan.result_mode is mode


def test_historical_intent_defaults_to_history_and_graph_depth_is_hard_bounded() -> None:
    historical = QueryPlanner().plan(_query("Show prior decisions"))
    assert not historical.current_only
    assert RetrievalMode.TEMPORAL in historical.channels

    no_graph = QueryPlanner().plan(
        _query(
            "Which requirement governs the relay?",
            budget=ContextBudget(max_relation_depth=0),
        )
    )
    assert RetrievalMode.GRAPH not in no_graph.channels

    with pytest.raises(ValueError, match="positive relation-depth"):
        QueryPlanner().plan(
            _query(
                "Show dependencies",
                mode=RetrievalMode.GRAPH,
                budget=ContextBudget(max_relation_depth=0),
            )
        )


def test_governance_and_external_namespaces_require_separate_requests() -> None:
    with pytest.raises(ValueError, match="separate recall requests"):
        _query(
            "Compare policy and vendor text",
            namespaces=("governance", "evidence/external"),
        )
