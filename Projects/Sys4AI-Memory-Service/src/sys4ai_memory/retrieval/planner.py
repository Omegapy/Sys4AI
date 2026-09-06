"""Deterministic query-intent classification and retrieval-channel planning."""

from __future__ import annotations

import re

from sys4ai_memory.contracts import RetrievalMode

from .models import QueryIntent, QueryPlan, RecallQuery

_IDENTIFIER = re.compile(
    r"(?<![A-Za-z0-9])(?:"
    r"(?:MEM-(?:FR|NFR)|REQ|TASK|PLAN|TRD|ADR|DEC|AC|UC)-[A-Za-z0-9-]+"
    r"|mem_[A-Za-z0-9_.:@-]+|src_[A-Za-z0-9_.:@-]+|rel_[A-Za-z0-9_.:@-]+"
    r")(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_PATH = re.compile(r"(?:^|\s)(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+(?:$|[\s?])")
_CODE_SYMBOL = re.compile(
    r"^(?:--[a-z][a-z0-9-]*|[A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]+|"
    r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+|[0-9a-f]{32,})$",
    re.I,
)
_COMMAND = re.compile(
    r"^(?:sys4ai-memory\s+\S+|uv run\s+\S+|python -m\s+\S+|"
    r"make\s+(?:validate|test|lint|typecheck|build|install|clean)[A-Za-z0-9_.:-]*)",
    re.I,
)

_INTENT_PATTERNS: tuple[tuple[QueryIntent, re.Pattern[str]], ...] = (
    (
        QueryIntent.HISTORICAL_QUERY,
        re.compile(
            r"\b(?:histor(?:y|ical)|previous|prior|formerly|as of|superseded|replaced)\b",
            re.I,
        ),
    ),
    (
        QueryIntent.DEPENDENCY_QUERY,
        re.compile(
            r"\b(?:depend(?:s|ed|ency|encies)?|blocked by|impact(?:ed|s)?|uses?|requires?)\b",
            re.I,
        ),
    ),
    (
        QueryIntent.PROVENANCE_QUERY,
        re.compile(
            r"\b(?:provenance|cite|citation|evidence|came from|origin(?:ated)?|source anchor)\b",
            re.I,
        ),
    ),
    (QueryIntent.REQUIREMENT_LOOKUP, re.compile(r"\brequirements?\b", re.I)),
    (
        QueryIntent.DECISION_LOOKUP,
        re.compile(r"\b(?:decisions?|adr|why was .* (?:chosen|selected)|rationale)\b", re.I),
    ),
    (
        QueryIntent.PROCEDURE_LOOKUP,
        re.compile(r"\b(?:how (?:do|to)|procedure|steps?|workflow|command)\b", re.I),
    ),
    (
        QueryIntent.SIMILAR_CASE_QUERY,
        re.compile(r"\b(?:similar|analogous|like this|related case|prior case)\b", re.I),
    ),
    (
        QueryIntent.CURRENT_STATE_QUERY,
        re.compile(r"\b(?:current|latest|active|right now|present status|status now)\b", re.I),
    ),
    (
        QueryIntent.SOURCE_LOOKUP,
        re.compile(
            r"\b(?:which file|what file|which source|what source|where is|file path|"
            r"source file|source contains|locator)\b",
            re.I,
        ),
    ),
)

_AUTO_CHANNELS: dict[QueryIntent, tuple[RetrievalMode, ...]] = {
    QueryIntent.EXACT_LOOKUP: (RetrievalMode.EXACT,),
    QueryIntent.SOURCE_LOOKUP: (RetrievalMode.EXACT, RetrievalMode.LEXICAL),
    QueryIntent.REQUIREMENT_LOOKUP: (
        RetrievalMode.EXACT,
        RetrievalMode.LEXICAL,
        RetrievalMode.SEMANTIC,
        RetrievalMode.GRAPH,
    ),
    QueryIntent.DECISION_LOOKUP: (
        RetrievalMode.EXACT,
        RetrievalMode.LEXICAL,
        RetrievalMode.SEMANTIC,
        RetrievalMode.GRAPH,
        RetrievalMode.TEMPORAL,
    ),
    QueryIntent.PROCEDURE_LOOKUP: (RetrievalMode.LEXICAL, RetrievalMode.SEMANTIC),
    QueryIntent.SEMANTIC_QUESTION: (RetrievalMode.LEXICAL, RetrievalMode.SEMANTIC),
    QueryIntent.DEPENDENCY_QUERY: (
        RetrievalMode.EXACT,
        RetrievalMode.LEXICAL,
        RetrievalMode.SEMANTIC,
        RetrievalMode.GRAPH,
    ),
    QueryIntent.PROVENANCE_QUERY: (
        RetrievalMode.EXACT,
        RetrievalMode.LEXICAL,
        RetrievalMode.GRAPH,
    ),
    QueryIntent.HISTORICAL_QUERY: (
        RetrievalMode.EXACT,
        RetrievalMode.LEXICAL,
        RetrievalMode.SEMANTIC,
        RetrievalMode.GRAPH,
        RetrievalMode.TEMPORAL,
    ),
    QueryIntent.SIMILAR_CASE_QUERY: (
        RetrievalMode.LEXICAL,
        RetrievalMode.SEMANTIC,
        RetrievalMode.GRAPH,
    ),
    QueryIntent.CURRENT_STATE_QUERY: (
        RetrievalMode.EXACT,
        RetrievalMode.LEXICAL,
        RetrievalMode.SEMANTIC,
        RetrievalMode.GRAPH,
        RetrievalMode.TEMPORAL,
    ),
}

_ALL_CHANNELS = (
    RetrievalMode.EXACT,
    RetrievalMode.LEXICAL,
    RetrievalMode.SEMANTIC,
    RetrievalMode.GRAPH,
    RetrievalMode.TEMPORAL,
)


def looks_like_exact_identifier(query: str) -> bool:
    """Return whether the query contains a stable identifier or explicit literal."""

    stripped = query.strip()
    return bool(
        _IDENTIFIER.search(stripped)
        or _PATH.search(stripped)
        or _CODE_SYMBOL.fullmatch(stripped)
        or _COMMAND.match(stripped)
        or (len(stripped) >= 2 and stripped[0] == stripped[-1] == "`")
    )


class QueryPlanner:
    """Route a recall request without using a model or mutable state."""

    def classify(self, query: str) -> QueryIntent:
        stripped = query.strip()
        for intent, pattern in _INTENT_PATTERNS:
            if pattern.search(stripped):
                return intent
        if looks_like_exact_identifier(stripped):
            return QueryIntent.EXACT_LOOKUP
        return QueryIntent.SEMANTIC_QUESTION

    def plan(self, request: RecallQuery) -> QueryPlan:
        intent = request.intent or self.classify(request.query)
        channels: tuple[RetrievalMode, ...]
        if request.mode is RetrievalMode.HYBRID:
            channels = _ALL_CHANNELS
        elif request.mode is not None:
            channels = (request.mode,)
        else:
            channels = _AUTO_CHANNELS[intent]

        if request.budget.max_relation_depth == 0 and RetrievalMode.GRAPH in channels:
            channels = tuple(channel for channel in channels if channel is not RetrievalMode.GRAPH)
            if not channels:
                raise ValueError("graph retrieval requires a positive relation-depth budget")

        historical_status = any(
            status.value not in {"active", "approved"} for status in request.status_filters
        )
        historical = (
            intent is QueryIntent.HISTORICAL_QUERY
            or request.at_time is not None
            or historical_status
        )
        current_only = request.current_only if request.current_only is not None else not historical
        if historical_status:
            current_only = False
        if request.at_time is not None and current_only:
            raise ValueError("historical at_time recall cannot use current_only=true")

        provider_channels = tuple(
            channel
            for channel in channels
            if channel in {RetrievalMode.SEMANTIC, RetrievalMode.GRAPH, RetrievalMode.TEMPORAL}
        )
        provider_mode: RetrievalMode | None
        if not provider_channels:
            provider_mode = None
        elif len(provider_channels) == 1:
            provider_mode = provider_channels[0]
        else:
            provider_mode = RetrievalMode.HYBRID

        result_mode = channels[0] if len(channels) == 1 else RetrievalMode.HYBRID
        governance_isolated = any(
            namespace.casefold().strip("/") == "governance"
            or namespace.casefold().strip("/").startswith("governance/")
            for namespace in request.namespaces
        )
        return QueryPlan(
            intent=intent,
            intent_overridden=request.intent is not None,
            channels=channels,
            result_mode=result_mode,
            provider_mode=provider_mode,
            current_only=current_only,
            governance_isolated=governance_isolated,
            explanations=(
                f"query_intent={intent.value}",
                "intent_source="
                + ("caller_override" if request.intent is not None else "deterministic_classifier"),
                "channels=" + ",".join(channel.value for channel in channels),
                f"current_only={str(current_only).lower()}",
                f"governance_isolated={str(governance_isolated).lower()}",
            ),
        )
