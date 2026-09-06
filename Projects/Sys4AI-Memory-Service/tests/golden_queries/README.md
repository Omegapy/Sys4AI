# Golden query contract

`queries.jsonl` defines retrieval expectations; the file alone is not observed
evidence. Each line is an independent JSON object with a stable query ID, one
required query class, an explicit project scope, expected source anchors,
policy outcomes, and forbidden anchors where applicable.

Evaluation must resolve each expected path beneath the declared fixture project, enforce project permission before retrieval and evidence assembly, and compare stable locators rather than generated wording. `no_answer` succeeds only with a structured insufficient-evidence outcome. `supersession` checks current and historical status explicitly. `project_isolation` must fail closed when cross-project authority is absent.

`tests/integration/test_golden_query_execution.py` validates all declared
anchors against normalized fixture records and executes all ten cases through
the provider-neutral retrieval engine. Exact and lexical cases use SQLite
directly. Hybrid cases combine SQLite with the deterministic in-memory
conformance provider and source-anchored fixture relations. The test verifies
the common `RetrievalResult` contract, five-channel traces, expected and
forbidden anchors, temporal filters, relation provenance, structured
insufficiency, and cross-project denial.

This is focused conformance evidence. The in-memory semantic score uses
normalized token coverage, and fixture relations are deterministic test
projections. The suite does not exercise embeddings, an LLM, provider-derived
graph extraction, or a real Cognee database.
