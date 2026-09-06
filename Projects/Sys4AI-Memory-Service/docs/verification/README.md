# Release evidence ledger

`release_evidence_ledger.csv` is the requirement-to-evidence control table for the first production-capable release. It contains one row for every numbered release source in `PRDs/Sys4AI_Memory_Service_PRD.md`: 15 principles, 12 primary goals, 178 functional requirements, 28 non-functional requirements, 12 acceptance criteria, 12 use cases, 14 product decisions, 11 open questions, and 14 definition-of-done items. The expected total is 296 rows.

The ledger was initialized conservatively with every implementation-bearing row
at `not_implemented`, every open-question row at `decision_pending`, and empty
`current_evidence`. That is historical initialization state, not a promise that
the current CSV still has those counts. Current counts and locators come from
the checked-in ledger and its latest validated traceability audit.

The ledger must not be bulk-promoted from file existence or delegated reports.
Each advanced row requires a reviewed result and exact evidence locator. A
planned check is not evidence, a source fixture is not a passing test, and a
generated report is not proof of runtime behavior.

The [minimum contractual-risk suite](minimum-risk-suite.md) selects one test
node for each cross-cutting risk in `P-15`. Use it as the fast minimum gate,
not as a substitute for the broader checks mapped by the ledger.

The [Cognee initialization and COGX compatibility probe](cogx-compatibility.md)
and [local-model spike](MEM-OQ-004-local-model-spike.md) record the real Cognee
1.5.3 relational, semantic, metadata-rejoin, and archive-API boundaries. The
[age exchange verification](age-encrypted-package.md) records the approved
provider-neutral encrypted-package path separately from deployment.

## Columns

- `item_id`: unique PRD identifier. Section 38 entries use `DOD-01` through `DOD-14`.
- `item_class`: `principle`, `goal`, `functional_requirement`, `nonfunctional_requirement`, `acceptance_criterion`, `use_case`, `decision`, `open_question`, or `definition_of_done`.
- `source_document`: repository-relative authoritative source path.
- `source_locator`: section-qualified, snapshot-specific line locator in the PRD.
- `priority`: PRD priority when one is stated; otherwise `binding`, `primary`, `acceptance`, `use_case`, `decision`, `question`, or `release_gate`.
- `requirement_or_outcome`: exact source wording or a whitespace-normalized, lossless acceptance outcome.
- `plan_tasks`: implementation-plan task IDs that own or verify the outcome.
- `implementation_expectation`: expected module or artifact set. It does not assert that the artifact exists.
- `planned_verification`: the check that could provide current evidence once run against the implementation.
- `status`: current evidence state.
- `current_evidence`: exact artifact, receipt, test, or runtime locator. It remains empty until observed.

## Evidence rules

Only an observed result can advance a row. Record the narrowest truthful state and include an exact locator. Static structure can support a static claim, targeted tests can support the behavior they exercise, and end-to-end acceptance requires the complete user-relevant workflow. Do not infer implementation from a plan, fixture, dependency lock, generated schema, child-agent report, or absence of a detected error.

When the PRD changes, update the wording and line locators from the new authoritative revision, rerun continuity and uniqueness checks, and retain evidence only when it still proves the revised requirement. Open questions remain `decision_pending` until an approved decision exists; they do not become passed because an implementation chose a default.

Use these evidence levels consistently:

| Level | What it can establish |
|---|---|
| Inspected or generated | The artifact exists and appears structurally relevant. It does not prove behavior. |
| Static validation | Schema, formatting, typing, import, link, or registry structure passed. |
| Focused test | The named behavior passed against its test inputs. State whether it used a fake/in-memory provider or temporary path. |
| Broader suite | The integrated local test set passed; it still does not prove a real provider or deployed service unless those were part of the run. |
| Measured benchmark | A numeric result was observed on the named machine and corpus. It proves only the measured path. |
| Real runtime | A provider/model/storage/interface behavior was directly observed with its versions, configuration, and isolation recorded. |
| End-to-end acceptance | The complete user workflow and acceptance criterion ran with all required boundaries and postconditions checked. |

Current special boundaries:

- SQLite/FTS5 exact lookup is benchmark-measured on the documented synthetic
  100,000-fragment corpus. A separate local-runtime benchmark measures guarded
  hybrid recall, service-shell startup, incremental sync, and 100,000 in-memory
  relations. A supplemental one-sample stress run loaded the full 1,000,000
  relations and exercised endpoint-indexed hybrid recall. These results do not
  cover real Cognee, full process/provider startup, mixed concurrency, or
  sustained full-scale operation.
- Cognee behavior tests use an injected runtime except for the focused
  real-package initialization/COGX probe and bounded local semantic run. Real
  relational initialization, graph/vector population, semantic recall, and
  stable metadata rejoin are verified on a small disposable corpus. Rebuild,
  populated-dataset COGX migration, recovery, and full-scale real-provider
  performance remain unverified.
- The approved local model profile is loopback Ollama `llama3.1:8b` plus
  offline FastEmbed `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions.
  Model-cache presence does not initialize a provider or authorize deployment.
- Policy, lifecycle, exchange, rebuild, security, interface, and observability
  tests use in-memory state, ASGI clients, or disposable temporary paths unless
  an evidence locator says otherwise.
- The neutral temporary extension still proves the generic seam. The approved
  tracked `software-engineering@1` profile separately adds four types, four
  relations, a Python AST adapter, policies/rules, and an evaluation case; its
  records are recalled by two agent identities through the unchanged client.
- Encrypted exchange tests use temporary age identities, verify deterministic
  inner ZIP bytes and non-public record round-trip, reject a wrong identity,
  and persist no test key in the product.
- No project-local product Git revision, product remote, publication,
  deployment, or hosted endpoint exists. The parent depot ignores this product
  directory.

## Fixture relationship

`tests/fixtures/` supplies deterministic source, security, lifecycle, and
isolation inputs. `tests/golden_queries/queries.jsonl` supplies expected
anchors and policy outcomes; neither input is evidence by itself. The focused
golden-query integration test now executes all ten cases against normalized
fixtures, SQLite, canonical test permissions, and the in-memory conformance
provider. That evidence remains separate from real Cognee, model quality, and
deployed-service acceptance.

## Validation commands

The ledger validator checks the 296 expected rows, IDs, source locators, allowed
states, and evidence-locator rule:

```bash
uv run --frozen python tools/validate_release_evidence.py
```

Project checks are:

```bash
uv run --frozen ruff check src tests tools
uv run --frozen mypy src tools
uv run --frozen pytest
```

Running these commands does not update the ledger automatically. Record a
result only after reviewing its scope, environment, output, changed state, and
relationship to the exact requirement. Operational interpretation is in the
[operations guide](../operations/README.md).
