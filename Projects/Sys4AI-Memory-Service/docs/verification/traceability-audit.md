# Release traceability audit

Audit date: 2026-09-03  
PRD: `SYS4AI-PRD-MEM-001` version 1.0  
Implementation plan: `PLAN-20260903-2DA243C0` revision 3

## Outcome

This audit reconciles every numbered PRD row with the current product files
and observed checks. It advances only rows directly supported by a current
artifact and an executable result. A `targeted_tests_passed` row can still be
limited to an in-memory provider, injected Cognee runtime, ASGI client, or
temporary directory. It does not mean the configured product is active or
production-ready.

The audited ledger has 296 rows. Its evidence levels are:

| Status | Rows |
|---|---:|
| `targeted_tests_passed` | 272 |
| `static_verified` | 12 |
| `runtime_verified` | 7 |
| `implemented_unverified` | 4 |
| `deferred` | 1 |

No row is classified as `broader_suite_passed` or `end_to_end_verified`.
The broader suite passed, but each row retains the narrower level that its
specific evidence establishes. Runtime rows include exact-index measurement,
real Cognee relational and semantic behavior, approved local-model evidence,
the encrypted `age` exchange, and the published capacity lower limit; none is
a deployed-service result.

This reconciliation applies the user's approval of `MEM-OQ-003` through
`MEM-OQ-011`, promotes only directly exercised behavior, and gives every
remaining limit an explicit disposition. No row remains `decision_pending` or
`not_implemented`.

## Source identity and managed-state boundary

| Source | Current identity |
|---|---|
| Canonical product PRD | `PRDs/Sys4AI_Memory_Service_PRD.md`, SHA-256 `37cba3ff2bf03bbcf1f1e4ad988b247bc43cbb53eec0d8ed5054e773a96cc20a` |
| Canonical plan record | `Implementation_Plans/Plan_sys4ai-memory-service-implementation_2026-09-03_2DA243C0/plan.json`, SHA-256 `ba394bc92f5cf2d75b9fbf0351d68b5ae94baf9843a69bcbdbf381c3e58aadff` |
| Plan state | `draft`, revision 3, validation `unresolved`, 29 tasks `planned`, 12 questions `open` |
| Product decision state | `docs/decisions/decision-register.md` records approved answers for `MEM-OQ-001` through `MEM-OQ-011` and the explicit external-action exclusions |
| Product runtime state | `config/memory.toml` selects the approved local capabilities while provider-on-load, network listening, shared mode, cloud fallback, and destructive execution remain disabled |

The PRD header still says `Proposed for review`, while the product decision
register records the user's later approval of the architecture baseline. The
managed plan has not been updated to reflect those later product decisions or
the implementation. This audit does not edit the PRD or plan and does not
reinterpret their lifecycle state.

## Status by PRD class

| Class | Total | Targeted | Static | Runtime | Implemented/unverified | Deferred |
|---|---:|---:|---:|---:|---:|---:|
| Principles | 15 | 15 | 0 | 0 | 0 | 0 |
| Primary goals | 12 | 12 | 0 | 0 | 0 | 0 |
| Functional requirements | 178 | 173 | 2 | 2 | 0 | 1 |
| Non-functional requirements | 28 | 19 | 3 | 2 | 4 | 0 |
| Acceptance criteria | 12 | 12 | 0 | 0 | 0 | 0 |
| Use cases | 12 | 12 | 0 | 0 | 0 | 0 |
| Product decisions | 14 | 14 | 0 | 0 | 0 | 0 |
| Open questions | 11 | 5 | 3 | 3 | 0 | 0 |
| Definition of done | 14 | 10 | 4 | 0 | 0 | 0 |

## Observed evidence bundles

Every positive ledger row points to one bundle below. Row lists are exact;
ranges are inclusive.

### TA-E01 repository fit

- Rows: `MEM-OQ-001`, `DOD-01`.
- Artifacts: `docs/architecture/repository-fit.md`, `depot/projects.json` in
  the parent workspace, and the approved path mapping in the decision register.
- Check: the two focused parent repository-contract tests for the registered
  path and truthful external state passed.
- Boundary: the product is registered but has no product-local Git repository,
  remote, publication, deployment, or hosted endpoint.

### TA-E02 runtime and dependency policy

- Rows: `MEM-FR-010`, `MEM-NFR-005`, `MEM-OQ-002`.
- Artifacts: `pyproject.toml`, `uv.lock`, `.python-version`, and
  `docs/architecture/runtime-and-dependency-policy.md`.
- Check: `uv lock --check` resolved 163 packages; the environment reported
  Python 3.12.11, package 0.1.0, and Cognee 1.5.3; `uv pip check` found all 157
  installed packages compatible.
- Boundary: dependency presence is not real-provider runtime evidence.

### TA-E03 public contracts

- Rows: `MEM-FR-036`, `MEM-FR-162`, `MEM-NFR-021`, `DOD-02`.
- Artifacts: `src/sys4ai_memory/contracts/` and `schemas/memory/`.
- Tests: `tests/contracts/test_contracts.py` and
  `tests/contracts/test_schemas.py`, including model/schema parity, versioned
  serialization, model-extraction provenance, permissions, and operation/tool
  catalogs.

### TA-E04 configuration and initialization

- Rows: `MEM-FR-005` and `MEM-FR-011` through `MEM-FR-018`.
- Artifacts: `config/memory.toml`, `src/sys4ai_memory/configuration/`, and
  `src/sys4ai_memory/initialization/`.
- Tests: `tests/configuration/test_configuration.py`,
  `tests/initialization/test_initialization.py`, and
  `tests/service/test_dispatcher.py::test_builtin_initialization_preview_reports_sources_without_writing`.
  The configuration tests represent local and remote LLM and embedding
  profiles, provider names, endpoints, dimensions, and credential references
  without activating any model.
- Boundary: preview and apply tests use temporary roots. No model profile is
  approved or active, and the tracked configuration cannot activate the
  provider.

### TA-E05 provider boundary

- Rows: `P-04`, `MEM-FR-002` through `MEM-FR-004`, `MEM-FR-009`,
  `MEM-FR-052` through `MEM-FR-055`, and `MEM-DEC-004`.
- Artifacts: `src/sys4ai_memory/providers/` and the provider-neutral service
  ports.
- Tests: `tests/providers/test_boundary.py`,
  `tests/providers/test_in_memory.py`, and
  `tests/providers/test_cognee.py::test_adapter_maps_only_declared_semantic_fields_and_normalizes_recall`,
  plus
  `tests/providers/test_cognee.py::test_pinned_distribution_provider_initialization_and_cogx_archive_are_compatible`.
- The real-package probe invokes provider initialization with Cognee 1.5.3,
  creates and inspects its relational SQLite schema inside a temporary derived
  root, rejects every socket connection attempt, and restores the host
  environment. Other Cognee tests inject a fake runtime for deterministic
  adapter mapping and isolation.
- Boundary: this proves real relational provider initialization, not native
  semantic ingestion, graph/vector creation, recall, or recovery.

### TA-E06 source discovery and normalization

- Rows: `P-10`, `MEM-FR-019` through `MEM-FR-027`, `MEM-FR-029` through
  `MEM-FR-035`, `MEM-FR-037`, `MEM-FR-041`, `MEM-NFR-019`, and `DOD-04`.
- Artifacts: `registries/`, `profiles/base/profile.yaml`,
  `src/sys4ai_memory/sources/`, and `src/sys4ai_memory/ingestion/`.
- Tests: `tests/ingestion/test_registry_discovery.py`, including the real
  temporary-Git commit/blob/dirty-revision case, and
  `tests/ingestion/test_adapters.py`, including all nine base formats, exact
  bytes, stable IDs, natural locators, bounded chunks, a byte-oriented optional
  PDF fixture adapter, fail-closed missing-adapter behavior, and a hard
  per-source read bound.
- Boundary: the optional-adapter protocol is format-neutral, but the test uses
  only a synthetic PDF adapter. No production PDF, HTML, office, image, audio,
  or other domain adapter is installed by this evidence.

### TA-E07 exact index and synchronization

- Rows: `MEM-FR-008`, `MEM-FR-028`, `MEM-FR-038` through `MEM-FR-040`,
  `MEM-FR-042` through `MEM-FR-050`, `MEM-NFR-011`, and `UC-02`.
- Artifacts: `src/sys4ai_memory/exact_index/` and
  `src/sys4ai_memory/ingestion/synchronizer.py`.
- Tests: `tests/exact_index/test_sqlite_index.py`,
  `tests/ingestion/test_synchronization.py`, and
  `tests/service/test_dispatcher.py::test_builtin_sync_returns_revision_delta_checkpoint_generation_and_receipt`.
- The synchronization checks assign a new source revision to changed bytes,
  remove prior-revision active records, and verify the changed revision through
  an exact lookup after guarded synchronization.
- Boundary: SQLite/FTS5 is approved in the tracked configuration; canonical
  reread remains required for execution-critical results.

### TA-E08 retrieval and evidence assembly

- Rows: `P-08`, `P-13`, `G-05`, `MEM-FR-007`, `MEM-FR-056` through
  `MEM-FR-059`, `MEM-FR-061` through `MEM-FR-071`, `MEM-FR-074`,
  `MEM-FR-076` through `MEM-FR-078`, `MEM-NFR-026`, `MEM-NFR-027`,
  `AC-06`, `AC-08`, and `AC-12`.
- Artifacts: `src/sys4ai_memory/retrieval/` and the retrieval-result contract.
- Tests: `tests/retrieval/test_planner.py` and
  `tests/retrieval/test_engine.py`, including channel composition, double
  authorization, filters, provenance, ranking, budgets, project isolation,
  history, and insufficiency.
- Boundary: semantic/graph/temporal candidates use provider-neutral fixtures
  or the in-memory adapter; no real Cognee retrieval ran.

### TA-E09 authorization and trust isolation

- Rows: `P-09`, `P-12`, `MEM-FR-098`, `MEM-FR-163`, `MEM-FR-165` through
  `MEM-FR-168`, `MEM-FR-170`, `AC-04`, `MEM-DEC-006`, and `MEM-DEC-009`.
- Artifacts: `src/sys4ai_memory/authorization/` and
  `src/sys4ai_memory/security/`.
- Tests: `tests/authorization/test_permissions.py`,
  `tests/security/test_controls.py`, and
  `tests/service/test_provider_authorization.py`, including current canonical
  reread, action/scope binding, injection, laundering, secret rejection, and
  project/dataset isolation.

### TA-E10 typed writes, session data, and improvement

- Rows: `P-07`, `G-06`, `MEM-FR-079` through `MEM-FR-093`, `MEM-FR-097`,
  `MEM-FR-101` through `MEM-FR-110`, `UC-06`, `MEM-DEC-008`,
  `MEM-DEC-010`, and `MEM-DEC-013`.
- Artifacts: `src/sys4ai_memory/policies/` and the write-proposal contract.
- Tests: `tests/policies/test_write_policy.py`,
  `tests/policies/test_staging_and_review.py`, and
  `tests/policies/test_retention_and_feedback.py`, including authorized,
  dataset/profile-bounded failure-pattern consolidation and review suggestions
  for stale, duplicate, weakly supported, and frequently useful records.
- Boundary: one human `local-owner` and the 72-hour/365-day retention schedule
  are approved. Automatic feedback and destructive execution remain disabled.

### TA-E11 lifecycle and destructive controls

- Rows: `P-11`, `MEM-FR-111` through `MEM-FR-120`, and `UC-10`.
- Artifacts: `src/sys4ai_memory/lifecycle/`.
- Tests: `tests/lifecycle/test_state.py`,
  `tests/lifecycle/test_destructive.py`, and the service supersession
  preflight regression.
- Boundary: these tests use temporary/in-memory state. Provider-native forget,
  real backups, and external copies were not erased.

### TA-E12 generation rebuild

- Rows: `P-06`, `G-08`, `MEM-FR-121` through `MEM-FR-130`,
  `MEM-NFR-007`, `MEM-NFR-008`, `MEM-NFR-010`, `MEM-NFR-016`, `UC-08`,
  `MEM-DEC-002`, and `DOD-09`.
- Artifacts: `src/sys4ai_memory/rebuild/`.
- Tests: `tests/rebuild/test_generation_rebuild.py`, including deletion of all
  derived state, full/incremental rebuild, complete receipt fields, progress,
  cancellation, drift, failure preservation, atomic activation, registry and
  schema fingerprints, source revisions, and byte-for-byte snapshots proving
  that successful clean rebuilds do not change canonical fixture files.
- Boundary: the provider stage is in-memory; real Cognee rebuild and recovery
  remain unverified. The rebuild contract validates a supplied external
  manifest when external documents exist; this fixture has no external source.

### TA-E13 import and migration candidate

- Rows: `MEM-FR-136` through `MEM-FR-139` and `MEM-NFR-009`.
- Artifacts: `src/sys4ai_memory/exchange/`.
- Tests: `tests/exchange/test_memory_package.py` and
  `tests/exchange/test_validation_boundaries.py`, including tamper, checksum,
  scope, profile, trust, archive attack, provenance, canonical-overwrite, and
  migration-dry-run cases.
- Boundary: unencrypted packages remain disposable test candidates. The
  approved ZIP/age export and public service path are runtime-verified in
  `age-encrypted-package.md`; database-backed COGX execution remains separate.

### TA-E14 profiles

- Rows: `P-14`, `G-11`, `MEM-FR-141` through `MEM-FR-150`, and
  `MEM-DEC-012`.
- Artifacts: `profiles/base/profile.yaml` and
  `src/sys4ai_memory/profiles/`.
- Tests: `tests/profiles/test_profile_loader.py`, including deterministic
  extension loading, conflicts, capability/API compatibility, confined
  references, registry parity, record/index/query/policy/evaluation declarations,
  context assembly and reranking references, externally bounded instruction
  authority, and rebuild-required representation changes.
- Boundary: the generic extension cases remain temporary fixtures. The tracked
  software-engineering profile and its public integration test are recorded
  separately in TA-E43.

### TA-E15 public interfaces

- Rows: `G-09`, `MEM-FR-151` through `MEM-FR-154`, `MEM-FR-156` through
  `MEM-FR-159`, and `MEM-DEC-014`.
- Artifacts: `src/sys4ai_memory/interfaces/` and
  `src/sys4ai_memory/cli.py`.
- Tests: `tests/interfaces/`, `tests/cli/test_cli.py`, and
  `tests/integration/test_service_interfaces.py`.
- Boundary: Python, ASGI, CLI, and MCP reach one guarded in-process dispatcher
  for the integration case, but no process bootstrap, listener, or deployed
  MCP server exists.

### TA-E16 observability contracts

- Rows: `MEM-FR-171` through `MEM-FR-173`, `MEM-FR-176`, `MEM-FR-178`, and
  `MEM-NFR-028`.
- Artifacts: `src/sys4ai_memory/observability/`.
- Tests: `tests/observability/`, including every public operation and
  administrative operation, authorized callback execution, denial and failure
  outcomes, audit fields, redaction, bounded private JSONL storage,
  health/drift aggregation, metrics, operation status, and validation receipts.
- Boundary: no outbound telemetry, live audit store, or retention/rotation
  workflow was enabled. Administrative callbacks use disposable fixture state,
  not tracked registries or configuration.

### TA-E17 exact-index benchmark

- Row: `MEM-NFR-012`.
- Artifact: `docs/verification/MEM-OQ-005-exact-index-spike.md`.
- Fresh audit rerun: 100,000 fragments plus 100 source-artifact records;
  32.142 seconds build/normalization; exact p50/p95/max
  137.858/139.579/142.909 ms over 200 samples; lexical p50/p95/max
  6.948/7.292/41.007 ms over 100 samples; target met.
- Environment: Python 3.12.11, SQLite 3.49.1, arm64 macOS 26.6.2; disposable
  in-memory database.
- Boundary: no hybrid, persistent-startup, mixed-concurrency, relation-scale,
  memory-use, or Cognee measurement.

### TA-E18 cross-feature validation

- Rows: `MEM-NFR-022`, `DOD-11`.
- Artifacts: explicit provider/source/profile/ranker interfaces and the
  security-sensitive implementation modules.
- Checks: final `make validate-memory` passed Ruff, strict mypy over 105 source
  files, all 463 tests, and the updated ledger validator. Dedicated
  `make validate-memory-security` passed 164 tests,
  `make validate-memory-integration` passed 39 tests,
  `make validate-memory-provider` passed 28 tests, and the minimum-risk gate
  passed seven tests. The full run reported two upstream TestClient
  deprecations and ten upstream Pydantic deprecations exposed by the real
  Cognee import.
- Boundary: a broad passing suite does not promote unrelated rows and does not
  supply real-provider or end-to-end evidence.

### TA-E19 operator documentation

- Rows: `MEM-FR-140`, `MEM-NFR-023`, `DOD-13`, `DOD-14`.
- Artifacts: `README.md`, `config/README.md`, `docs/operations/`,
  `docs/security/`, `src/sys4ai_memory/exchange/BACKUP.md`, and
  `docs/verification/README.md`.
- Check: a read-only audit of 29 files found all 12 required operation,
  security, backup, and limitation topics and resolved 88 local links. The
  backup guide names the tested `backup-assets.json` member.
- Boundary: documentation explains the current interfaces and stop conditions;
  it is not proof that a documented live workflow ran.

### TA-E20 unified service

- Rows: `G-10`, `MEM-FR-001`, `MEM-FR-100`, `MEM-FR-155`,
  `MEM-FR-160`, `MEM-FR-161`, `MEM-FR-174`, `MEM-FR-175`, `MEM-NFR-020`,
  and `MEM-DEC-003`.
- Artifacts: `src/sys4ai_memory/service/dispatcher.py`, service ports/models,
  and `RetrievalEngine.recall_with_trace()`.
- Tests: `tests/service/test_dispatcher.py` and
  `tests/integration/test_service_interfaces.py`, including all 16 public
  operations plus three controls through one guard, fresh canonical
  authorization, project/dataset binding, read-only blocking, process-local
  mutation serialization under 16 concurrent requests, idempotent retry,
  built-in initialization and sync, exact per-channel recall trace, detailed
  health metrics, safe errors, and four-interface in-process dispatch.
- Boundary: built-in operation integrations are not all directly tested;
  serialization is process-local; the standalone CLI does not construct the
  service; no listener or deployment exists.

### TA-E21 canonical promotion and rejection

- Rows: `MEM-FR-094` through `MEM-FR-096`, `AC-05`, and `UC-05`.
- Artifacts: `src/sys4ai_memory/policies/staging.py`,
  `src/sys4ai_memory/policies/promotion.py`, and the guarded service approval
  path.
- Tests: `tests/policies/test_write_policy.py`,
  `tests/policies/test_staging_and_review.py`,
  `tests/policies/test_promotion_coordinator.py`, and
  `tests/integration/test_promotion_flow.py`. They cover typed write
  classification, untyped rejection, fresh reviewer authority, repository
  change/review references, canonical commit followed by source
  synchronization, no contradictory memory write, rollback/reconciliation on
  failed synchronization, public success only after matching sync evidence,
  and policy-bounded or zero-metadata rejection disposal.
- Boundary: repository and synchronizer ports use disposable test
  implementations. The tracked reviewer policy is unresolved, no product Git
  repository exists, and no real project change was promoted.

### TA-E22 structured graph paths

- Rows: `MEM-FR-060` and `UC-04`.
- Artifacts: `src/sys4ai_memory/retrieval/` and the unified service graph
  handler.
- Tests: `tests/retrieval/test_engine.py::test_structured_graph_query_returns_bounded_typed_paths`,
  `tests/retrieval/test_engine.py::test_structured_graph_query_rejects_cross_project_relation`,
  and
  `tests/service/test_dispatcher.py::test_builtin_graph_returns_typed_one_hop_path_and_retrieval_trace`.
  They cover one-hop direction, relation-type and depth bounds, typed source,
  validation, confidence, temporal and lifecycle evidence, double
  authorization, trace metadata, and cross-project relation rejection.
- Boundary: paths use a static or in-memory provider and stop at one hop. No
  real Cognee graph, multi-hop traversal, or open-ended graph query ran.

### TA-E23 opt-in cited synthesis

- Rows: `MEM-FR-072` and `MEM-FR-073`.
- Artifacts: the optional `EvidenceSynthesisPort`, strict synthesis models, the
  unified recall handler, and the explicit CLI `--synthesize` flag.
- Tests: `tests/service/test_dispatcher.py::test_recall_synthesis_is_explicit_and_rejects_uncited_evidence`
  and `tests/cli/test_cli.py::test_recall_synthesis_requires_the_explicit_cli_flag`.
  They cover retrieval-only default behavior, explicit opt-in, an
  evidence-only provider request, a citation for every declared material
  claim, exact record/source-anchor reconciliation, rejected out-of-bundle
  citations, canonical authorization immediately before and after the injected
  call, denial after mid-call permission revocation, and no synthesis call on
  insufficient evidence.
- Boundary: the synthesis port uses a deterministic fake. The tracked semantic
  gate remains closed, and no LLM, embedding, Cognee runtime, or generated
  answer quality was exercised.

### TA-E24 canonical control and provider-failure boundaries

- Rows: `MEM-FR-006`, `MEM-FR-075`, `MEM-NFR-006`, and `AC-02`.
- Artifacts: the unified service authorization and synchronization paths,
  canonical permission loader, and provider-safe error boundary.
- Tests:
  `tests/integration/test_failure_boundaries.py::test_provider_outage_cannot_modify_or_remove_canonical_source`
  and
  `tests/integration/test_failure_boundaries.py::test_remembered_control_copy_cannot_authorize_a_mutation`.
  They inject a provider outage after reading a canonical fixture and compare
  its bytes and existence after failure. A separate case returns a remembered
  permission claim, changes the canonical permission file to read-only, then
  verifies that the proposed mutation is denied before its handler runs.
- Boundary: the provider is an in-memory failure fixture and the canonical
  files are temporary. This is direct failure/control-boundary evidence, not a
  real Cognee outage or deployed recovery exercise.

### TA-E25 public disposable package round trip

- Rows: `MEM-FR-131` through `MEM-FR-134`, `AC-10`, `AC-11`, and `DOD-10`.
- Artifacts: `src/sys4ai_memory/exchange/`,
  `src/sys4ai_memory/service/exchange.py`, the unified service import/export
  handlers, and the Python client.
- Tests: `tests/exchange/test_memory_package.py`,
  `tests/exchange/test_validation_boundaries.py`,
  `tests/integration/test_exchange_flow.py`, the runtime-generated secret and
  audit-redaction cases in `tests/security/test_controls.py` and
  `tests/observability/test_audit_store.py`. The public integration exports a
  provider-neutral ZIP through `MemoryClient`, inspects it with
  the standard `zipfile` reader, copies it into a clean project, previews and
  activates it through a separately authorized target service, checks the
  imported records and relation, and proves the target canonical bytes did not
  change. Package tests cover all declared members, checksums, policy filtering,
  secret rejection, hostile inputs, provenance, and result reconciliation.
- Determinism is separately proven by the package-component test that exports
  identical fixed snapshots to byte-identical ZIPs. The public provider export
  stamps its live snapshot time and is not itself a determinism assertion.
- Boundary: `DisposableMemoryPackageExchange` accepts only isolated in-memory
  providers and reports `production_ready=false`. The unencrypted package is a
  test-only policy exception. Production archive/encryption, COGX, real Cognee,
  alternate-provider compatibility, publication, and deployment remain
  unverified. The adapter swaps only its own exchange-provider reference; it
  does not replace `ServiceComponents.provider` or a retrieval engine provider,
  so this public disposable path alone does not establish service-wide provider
  migration. TA-E30 separately proves provider-neutral transfer into a
  different adapter through the generic isolated import boundary.

### TA-E26 agent, provider, governance, and MCP boundaries

- Rows: `P-03`, `AC-07`, `DOD-03`, `DOD-06`, and `DOD-07`.
- Artifacts: provider-neutral interfaces, `MemoryProvider`, the lazy provider
  registry and Cognee adapter, retrieval authority filters, and the MCP mode
  catalog.
- Tests:
  `tests/integration/test_service_interfaces.py::test_four_interfaces_recall_the_same_service_owned_evidence`
  sends the same recall identity, query, and payload through Python, HTTP, CLI,
  and MCP and compares the normalized evidence from one service-owned provider.
  `tests/integration/test_provider_substitution.py` runs one unchanged
  `MemoryClient.recall` call against the in-memory and injected fake-Cognee
  adapters, comparing schema, record, content, source, and identity while
  proving that the real Cognee distribution was not loaded.
  `tests/providers/test_boundary.py` rejects direct Cognee imports outside the
  dedicated adapter. Governance isolation is covered by the prompt-injection,
  summary-laundering, namespace-separation, external-instruction, and canonical
  control-reread cases. `tests/interfaces/test_mcp.py` proves that default MCP
  can dispatch read/propose work, exposes no destructive tool, and denies a
  hidden destructive call before authorization or dispatch.
- Boundary: the Cognee runtime is injected and deterministic, provider data is
  temporary or in memory, HTTP is in-process ASGI, and no listener, real model,
  live Cognee store, different agent framework, or future runtime was started.
  This proves current contract interchangeability, not real-provider quality or
  deployed multi-runtime compatibility.

### TA-E27 source-first rebuild acceptance

- Rows: `P-01`, `G-03`, `AC-01`, and `MEM-DEC-001`.
- Artifacts: canonical source registry and fixture files, initialization
  preview/apply, deterministic ingestion, SQLite exact generation, isolated
  provider generation, rebuild receipts, manifests, snapshots, and atomic
  activation pointer.
- Test:
  `tests/rebuild/test_generation_rebuild.py::test_clean_full_rebuild_restores_exact_and_provider_generations`
  explicitly initializes a temporary project, ingests its registered canonical
  sources, creates and validates an initial exact/provider generation, deletes
  the entire `.sys4ai/memory/` tree, regenerates a typed source-anchored
  relation from the same normalized canonical inputs, rebuilds, and reconciles
  the complete record IDs, relation IDs, source IDs, source revisions, and
  exact requirement lookup. Byte snapshots prove every canonical fixture file
  remains unchanged. The approved canonical-source decision and recoverable
  promotion tests in TA-E21 cover the opposite direction: memory can affect a
  canonical source only through the governed project-write workflow.
- Boundary: initialization and rebuild use temporary paths, SQLite, and
  isolated in-memory provider generations. Relation regeneration is a
  deterministic fixture transform, not real Cognee extraction. This is
  targeted source-authority evidence, not a production recovery run.

### TA-E28 public lifecycle and deterministic-control execution

- Rows: `MEM-DEC-007` and `DOD-08`.
- Artifacts: typed write/review/promotion policy, lifecycle catalog,
  destructive lifecycle service, public interface models, Python client, and
  unified dispatcher.
- Tests: `tests/integration/test_promotion_flow.py` covers typed proposal,
  review, recoverable canonical promotion with matching synchronization, and
  rejection disposal. `tests/integration/test_lifecycle_flow.py` runs public
  supersession followed by non-mutating delete preview and separately
  idempotent execution using the preview-returned operation ID and exact impact
  digest; it verifies history links, deletion receipt, lifecycle transition,
  audit outcomes, and file removal. The broader lifecycle/policy suites cover
  every allowed and denied transition, self-approval denial, rollback,
  canonical non-overwrite, changed-impact denial, and privacy/canonical change
  routing. TA-E24 and TA-E26 prove that remembered or generated content cannot
  provide execution authority; current canonical control is reread instead.
- Boundary: all repositories, sources, providers, and deleted content are
  disposable fixtures. Provider-native forget and real product canonical
  changes did not run. The complete general-agent versus administrator
  destructive matrix is recorded separately in TA-E43.

### TA-E29 generated-artifact integrity

- Row: `MEM-NFR-024`.
- Artifacts: public schema generation/parity code, generation manifests,
  checksum-bound exact indexes and provider snapshots, drift reporting, and the
  rebuild/operations guidance.
- Tests: `tests/contracts/test_schemas.py::test_checked_in_schema_matches_model`
  detects a hand edit to a checked-in schema projection.
  `tests/rebuild/test_generation_rebuild.py::test_drift_detects_generated_artifact_hand_edits`
  modifies the active SQLite index and provider snapshot independently and
  requires explicit generation drift against the activation-time checksums.
  Manifest and active-pointer tamper tests cover the surrounding metadata.
- Boundary: detection is tested on temporary generations. No generated
  documentation artifact is checked in beyond schema projections; runtime
  recovery remains regeneration from canonical inputs, not in-place repair.

### TA-E30 cross-adapter provider-neutral migration

- Rows: `MEM-NFR-003` and `UC-12`.
- Artifacts: Sys4AI Memory Package validation/import, the generic isolated
  provider stage, and Cognee adapter support for provider-neutral snapshots.
- Test:
  `tests/exchange/test_memory_package.py::test_provider_neutral_package_rebuilds_an_isolated_cognee_adapter`
  exports an in-memory provider snapshot, validates and stages its standard
  JSON/JSONL package, imports its complete allowed record/relation set into a
  distinct Cognee adapter through the ordinary allowlisted semantic mapping,
  and recalls both records and their typed relation. The test verifies package
  IDs, canonical byte preservation, provider-result reconciliation, and that
  the real Cognee distribution never loaded.
- Boundary: Cognee is represented by the injected deterministic runtime and
  the destination is an isolated disposable generation. This proves the
  cross-adapter contract and prevents dependence on the original provider
  database; it does not prove real Cognee quality, COGX, service-wide hot-swap,
  production encryption, or deployed migration.

### TA-E31 persistent exact memory across agent sessions

- Row: `G-01`.
- Artifacts: deterministic ingestion, on-disk SQLite exact index, reopened
  `ExactIndex`, fresh `MemoryService`, retrieval engine, and Python client.
- Test:
  `tests/integration/test_session_persistence.py::test_fresh_agent_session_recalls_existing_source_anchored_index`
  builds an index from a registered canonical Markdown source, closes the
  builder, recalls through one service/client run, closes that index handle,
  then opens a new index handle and a fresh service/client with a different run
  identity. Both sessions return the same stable record; the second retains the
  exact canonical source ID, path, and content.
- Boundary: this proves local exact-index persistence across in-process agent
  sessions and service composition restart. The tracked exact backend remains
  unapproved and disabled, and no persistent Cognee semantic/graph state or OS
  process restart was exercised.

### TA-E32 canonical control, reconnect, and correction flows

- Rows: `P-02`, `UC-01`, and `UC-07`.
- Artifacts: canonical authorization, registered-source ingestion, persisted
  SQLite exact/lexical index, provider-neutral retrieval, lifecycle catalog,
  deterministic lifecycle projection, and the public Python client.
- Tests:
  `tests/integration/test_control_authority.py::test_canonical_control_reread_overrules_remembered_permission_copy`
  first recalls a stale provider-held permission claim, then changes only the
  canonical permission record and verifies the guarded supersession is denied
  before its handler runs;
  `tests/integration/test_project_reconnect.py::test_new_agent_session_recalls_complete_current_project_context`
  opens a fresh service/client session over a reopened on-disk index and
  returns current governance, decision, requirement, architecture, and
  verified-outcome records with exact source IDs, paths, hashes, and locators;
  and
  `tests/integration/test_lifecycle_flow.py::test_public_supersession_and_two_phase_deletion_share_governed_lifecycle`
  uses public supersession to update both lifecycle catalog and deterministic
  index, then proves hybrid current recall filters a stale provider copy while
  historical recall retains the linked superseded record. The focused exact
  index test separately verifies transactional current/history projection and
  hydrated supersession links.
- Boundary: all three cases use temporary canonical fixtures and local test
  components. The provider candidate in the correction case is injected, the
  product provider is not initialized by configuration load, and no provider-native lifecycle
  store, real Cognee process, network listener, or canonical product file was
  mutated.

### TA-E33 one-service multi-agent isolation and serialization

- Row: `UC-11`.
- Artifacts: canonical permission-envelope loader, fixed project/dataset
  `MemoryService` boundary, provider-neutral retrieval, public Python clients,
  audit events, idempotency handling, and the service mutation lock.
- Test:
  `tests/integration/test_multi_agent_service.py::test_two_agents_share_scoped_evidence_and_service_serializes_writes`
  grants two distinct principals through the same canonical permission file,
  verifies both receive the same source-anchored project evidence, dispatches
  their proposals concurrently and observes a maximum of one active write,
  then submits a foreign project/dataset recall and verifies denial before a
  third provider request.
- Boundary: this is an in-process temporary-fixture acceptance case. It proves
  the single-service multi-agent behavior and fixed service boundary, not the
  deferred shared deployment profile, backend access control, TLS, a network
  listener, or a production graph/vector store.

### TA-E34 dependency-upgrade review gate

- Row: `MEM-NFR-025`.
- Artifacts: `tools/validate_dependency_upgrade.py` and
  `docs/operations/dependency-upgrades.md`.
- Tests: `tests/verification/test_dependency_upgrade_gate.py` verifies that a
  complete accepted review is bound to the exact baseline and candidate lock
  bytes, both macOS and Linux results, all 14 named compatibility checks, a
  Cognee migration dry run that preserves the prior generation, verified
  rollback, and a timezone-aware reviewer decision. Negative cases prove that
  missing checks/platforms, skipped Cognee migration, unverified rollback,
  lock tampering, and secret-like review content fail closed without echoing
  the generated value.
- Boundary: this implements and tests the mandatory review gate. It does not
  claim that a newer Cognee release, candidate lock, Linux environment, real
  provider migration, or dependency upgrade was executed or accepted in this
  checkout.

### TA-E35 canonical Git and text portability

- Row: `MEM-NFR-002`.
- Artifacts: canonical PRD, CSV registries, JSON Schema, and the repository-fit
  path/authority contract.
- Test:
  `tests/integration/test_canonical_text_portability.py::test_canonical_memory_is_round_trip_readable_by_git_and_text_tools`
  copies representative canonical files into a disposable Git repository,
  commits them without transformation, reproduces every file byte-for-byte
  through `git show`, locates `MEM-FR-001` with ordinary `grep`, and confirms
  the working tree remains clean.
- Boundary: this proves canonical-format readability with Git and text tools.
  It does not create a product repository, commit product files, prove a
  remote/published history, or classify the derived provider database as
  canonical memory.

### TA-E36 offline core service workflow

- Rows: `P-05`, `G-07`, and `MEM-NFR-001`.
- Artifacts: registered Markdown ingestion, SQLite exact/lexical index,
  in-memory conformance provider, provider-neutral retrieval, deterministic
  generation rebuild, disposable provider-neutral export, unified service,
  public Python client, authorization, audit, and operation tracking.
- Test:
  `tests/integration/test_offline_core_workflow.py::test_core_service_workflow_completes_with_all_network_access_denied`
  replaces both socket connection entry points with a fail-fast function, then
  completes source administration, sync/provider remember, hybrid recall,
  rebuild preview and activation, export, and detailed health. It verifies the
  exported artifact, active rebuild receipt, source anchor, zero failed audit
  events, and byte-for-byte canonical-source preservation.
- Boundary: this directly proves that the core provider-neutral service path
  has no mandatory cloud dependency. It uses a temporary active test
  configuration, in-memory conformance provider, disposable unencrypted test
  export, and local in-process interface. Separate checks cover the tracked
  approved configuration, bounded real Cognee path, and encrypted service
  export; listener and deployment evidence remain outside this test.

### TA-E37 minimum contractual-risk gate

- Row: `P-15`.
- Artifacts: Make target `validate-memory-minimum-risk`,
  `docs/verification/minimum-risk-suite.md`, and the release evidence ledger.
- Check: `make validate-memory-minimum-risk` executed seven unique maintained
  test nodes and all seven passed. The nodes have one primary risk each:
  authority separation, provenance, isolation, data integrity,
  rebuildability, deletion, and retrieval correctness. The gate reuses the
  maintained acceptance tests instead of copying their setup or assertions.
- Boundary: this is the deliberately small cross-cutting risk gate. It does
  not replace the broader schema, provider, security, migration, benchmark,
  real-runtime, or end-to-end checks required by their own release rows.

### TA-E38 opt-in OpenTelemetry-compatible trace projection

- Row: `MEM-FR-177`.
- Artifacts: `src/sys4ai_memory/observability/telemetry.py`, explicit exporter
  injection in `AuditRecorder`, and the observability operator contract.
- Test:
  `tests/observability/test_audit_store.py::test_explicit_telemetry_export_emits_metadata_only_otlp_json`
  enables export only with an injected recording exporter and verifies an
  OTLP/JSON `TracesData` envelope with lowercase 32/16-hex trace/span IDs,
  integer enum values, decimal-string nanosecond timestamps, lower-camel-case
  fields, and metadata-only attributes. It also verifies that raw actor,
  principal, internal trace ID, and source-content markers are absent. The
  default-off test rejects a missing exporter and rejects an exporter while
  the gate is disabled.
- Boundary: this is a transport-neutral compatibility projection. No
  OpenTelemetry SDK, collector endpoint, header, credential, retry worker,
  background sender, network connection, or telemetry export was configured;
  the tracked setting remains false.

### TA-E39 shared-backend transition without an agent-contract change

- Row: `MEM-NFR-018`.
- Artifacts: stable `MemoryClient`, public request/result contracts,
  `MemoryProvider` protocol, provider-neutral retrieval engine, service
  composition ports, canonical authorization, and fixed project/dataset
  boundaries.
- Checks:
  `tests/integration/test_provider_substitution.py::test_same_public_recall_shape_survives_provider_substitution`
  runs one unchanged client recall against the embedded in-memory adapter and
  an isolated injected Cognee adapter and compares their provider-neutral
  result; TA-E33 separately proves two authenticated principals can share one
  service with serialized writes and cross-project denial.
- Boundary: this proves the architecture and agent contract can survive a
  backend transition. It does not select, authenticate, benchmark, deploy, or
  approve a production shared graph/vector backend; `MEM-OQ-009` deliberately
  selects no such backend for this release, so shared mode remains disabled.

### TA-E40 provider-neutral package plus native COGX compatibility

- Rows: `G-12`, `MEM-FR-135`, and `MEM-DEC-011`.
- Artifacts: provider-neutral Sys4AI Memory Package implementation, the
  policy-gated Cognee export/import adapter, pinned Cognee 1.5.3, and
  `docs/verification/cogx-compatibility.md`.
- Checks:
  `tests/exchange/test_memory_package.py::test_provider_neutral_package_rebuilds_an_isolated_cognee_adapter`
  proves the standard-tool-inspectable Sys4AI package crosses provider
  boundaries; `tests/providers/test_cognee.py::test_authorized_privileged_calls_use_scoped_fake_runtime`
  exercises the adapter's authorized, confined COGX export and two-phase
  import calls; and
  `tests/providers/test_cognee.py::test_pinned_distribution_provider_initialization_and_cogx_archive_are_compatible`
  loads the real installed Cognee package, initializes and inspects its
  project-confined relational SQLite schema, verifies its export signature,
  round-trips two native entities and one fact through COGX 0.1, and streams
  the archive through `COGXArchiveSource` with all socket access denied. The
  real-package probe also verifies project-confined data/system/cache/log
  paths, omitted permissions, and complete host-environment restoration.
- Boundary: this proves the separate provider-neutral and provider-native
  portability mechanisms and the pinned relational initialization plus native
  archive/API compatibility. It does not initialize or populate Cognee's
  graph/vector stores, invoke a model, call `cognee.export` on a populated
  dataset, import that dataset with
  `cognee.remember`, run a provider-storage migration, or approve production
  archive/encryption policy.

### TA-E41 maintained five-channel golden-query execution

- Rows: `G-04`, `AC-03`, `UC-03`, `MEM-DEC-005`, and `DOD-05`.
- Artifacts: all ten cases in `tests/golden_queries/queries.jsonl`, normalized
  Alpha/Beta project fixtures, the SQLite exact/lexical index, provider-neutral
  retrieval engine, canonical test authorization, deterministic in-memory
  conformance provider, and `tests/integration/test_golden_query_execution.py`.
- Checks: the focused integration file passed 12 tests. One contract test
  resolves every expected and forbidden source anchor against normalized
  records. Three parameterized cases execute the exact and lexical golden
  queries directly through SQLite. Seven parameterized cases execute the
  conceptual, dependency, temporal, no-answer, supersession, and isolation
  cases through one hybrid engine; the unauthorized cross-project case is
  denied. Every successful result round-trips through the public
  `RetrievalResult` contract, and every hybrid trace selects exact, lexical,
  semantic, graph, and temporal channels. The conceptual case returns both
  declared canonical anchors with semantic and graph signals; the dependency
  case retains its typed relation and source; the historical case returns its
  declared event and decision at the requested time; and the no-answer case
  returns structured insufficiency with no records.
- Corrections: JSONL event identity now takes precedence over a linked
  `decision_id`, and `occurred_at` becomes the event validity start. The
  conformance provider now normalizes compound tokens, word forms, dates, and
  timestamps and rejects weak query coverage, preventing generic project words
  from producing false evidence.
- Boundary: semantic scoring is deterministic normalized-token coverage, and
  the three typed relations are fixture projections anchored to normalized
  source records. This is provider-neutral contract and evidence-selection
  acceptance, not embedding quality, provider-derived graph extraction, real
  Cognee database behavior, an approved local model profile, or a deployed
  service result.

### TA-E42 public write atomicity at the governed promotion boundary

- Row: `MEM-FR-099`.
- Artifacts: the guarded public approval path, proposal staging and reviewer
  gate, `CanonicalPromotionCoordinator`, and its injected governed-repository
  and canonical-source synchronization ports.
- Checks: `tests/integration/test_promotion_flow.py` now proves that the public
  service returns success only after a canonical commit and matching source
  synchronization. Its failure case injects an exception immediately after
  the repository port replaces the canonical bytes, then observes rollback,
  rollback-source synchronization, restoration of the original bytes, a
  stable `WRITE_REJECTED` public error, preserved staged proposal, and failed
  audit outcome with no success receipt. The component promotion suite also
  covers concurrent idempotent success, failed or mismatched promotion sync,
  reviewer/target drift after prepare, rollback failure as
  `recovery_required`, and replay/conflict handling.
- Boundary: repository and synchronization ports operate only on a disposable
  temporary fixture. The evidence establishes the public result and
  compensation contract, including explicit recovery-required behavior when
  rollback cannot restore atomic state. It does not install a reviewer policy,
  create a product Git repository, exercise a real review workflow, mutate a
  non-fixture canonical source, or prove cross-process transactions.

### TA-E43 destructive-operation authorization and execution matrix

- Row: `AC-09`.
- Artifacts: the public operation and input contracts, canonical permission
  loader, unified dispatcher, Python client, destructive lifecycle service,
  rebuild service port, disposable import service, and default MCP tool
  catalog.
- Checks:
  `tests/integration/test_destructive_controls.py::test_general_agent_cannot_invoke_destructive_operations`
  makes separate public calls for mass forget, delete-source, rebuild
  activation, and import replacement from a read/propose-only principal. All
  four are denied by the common authorization boundary before a component can
  run. The same file executes a two-record mass-forget preview and deletion and
  a canonical-source preview and deletion as the privileged fixture identity,
  checks unchanged-preview digests, lifecycle transitions, removed paths, and
  non-sensitive receipts, and routes canonical removal only through an
  injected governed executor. The component lifecycle suite proves the default
  no-executor path fails closed and rejects an executor that reports completion
  while leaving a previewed local target present; it also rejects a
  delete-source scope containing no canonical source.
  `tests/service/test_two_phase_operations.py` performs privileged rebuild
  preview and activation with one operation identity and reviewed digest.
  `tests/integration/test_exchange_flow.py::test_public_disposable_export_preview_and_import_round_trip`
  performs privileged import preview and isolated replacement activation with
  a receipt. The default MCP suite separately confirms that general agents do
  not receive destructive tools.
- Boundary: all mutable paths are disposable temporary fixtures. Rebuild uses
  an injected deterministic port, canonical deletion uses a test governed
  executor, and import replacement uses distinct in-memory providers plus the
  explicit unencrypted disposable-package policy. No product repository,
  provider-native forget, real backup/export erasure, production identity,
  shared service, or non-fixture destructive operation was exercised.

### TA-E44 generic derived-agent runtime reuse

- Row: `G-02`.
- Artifacts: the versioned base and extension profile loader, canonical profile
  registry contract, profile-bound `IngestionSynchronizer`, optional adapter
  seam, provider-neutral records, unified service, in-memory conformance
  provider, and public Python client.
- Checks:
  `tests/integration/test_derived_profile_runtime.py::test_temporary_extension_syncs_and_serves_two_agents_without_api_change`
  builds and registry-validates a neutral extension over `base@1`, declares one
  custom adapter and `DomainFact` record type, synchronizes its canonical
  temporary source through the public service, and confirms the selected
  extension version in normalized provenance. Two distinct authorized agent
  identities then use the same unchanged `MemoryClient.recall` call and receive
  the same source-anchored extension record. The operation catalog is unchanged.
  Three negative cases reject a missing source profile, an undeclared adapter,
  and adapter output with an undeclared record type as
  `PROFILE_INCOMPATIBLE` before provider persistence. The existing profile
  suite retains deterministic ordering, compatibility, conflict, authority,
  reference-confinement, and representation-change coverage.
- Boundary: this original test uses disposable extension material and proves
  the generic seam. TA-E43 separately verifies the approved tracked
  `software-engineering@1` profile, its adapter/types, and the unchanged public
  operation catalog.

## Measured component evidence without requirement promotion

`docs/verification/local-runtime-benchmark.md` records the maintained synthetic
scale run for `MEM-NFR-013`, `MEM-NFR-014`, `MEM-NFR-015`, and `MEM-NFR-017`.
The separate real-profile spike adds a two-record/one-relation Cognee lower
limit. The scale and real-provider evidence are not conflated: three latency
rows remain `implemented_unverified`, while the capacity row uses its explicit
published-lower-limit alternative.

## Decision-bundle verification

### TA-E42 - approved local policy and fail-closed exclusions

- The decision register records the user's exact approval of `MEM-OQ-003`
  through `MEM-OQ-011` and the product Git/deployment/destructive exclusions.
- Typed configuration loads the approved model, exact index, reviewer,
  retention, exchange, shared-disabled, and feedback policies without creating
  derived state.
- The canonical permission document names one human `local-owner`, requires one
  approval, forbids self-approval, leaves general agents at read/propose, and
  grants no delete, administer, or rebuild permission.
- Configuration and policy tests verify that exact, semantic, approval,
  retention, export, and explicit feedback are ready while network, shared, and
  destructive execution remain blocked.

### TA-E43 - software-engineering derived profile

- `software-engineering@1` extends `base@1` with four types, four relations, the
  `software-python-ast@1` adapter, write/retrieval/retention references, and an
  evaluation case.
- The tracked profile and registry projections validate together. An
  integration test synchronizes all four derived types, serves the same
  source-anchored result to two agent identities, and proves the public
  operation catalog is unchanged.

### TA-LIMIT-01 - sensitive namespace storage profile

`MEM-FR-169` is deliberately deferred. Restricted records are rejected by the
current Cognee adapter unless an approved isolated storage profile exists, and
non-public portable packages use age encryption. A separate per-namespace
at-rest key/storage profile is not selected for this no-shared-backend release.

### TA-LINUX-GAP - Linux runtime evidence

`MEM-NFR-004` is implemented in portable Python/package metadata but remains
unverified on Linux. No Docker, Podman, Colima, Lima, remote Linux host, or
authorized download-backed substitute was available in this operation. macOS
runtime evidence must not be relabeled as Linux execution.

## Remaining evidence limits

No ledger row remains `decision_pending` or `not_implemented`. Four rows are
truthfully `implemented_unverified`: Linux execution and the complete-profile
100,000-fragment hybrid, startup, and incremental-sync measurements. One
optional row, `MEM-FR-169`, is deferred as described above. Populated-dataset
native COGX migration, non-fixture destructive execution, product Git,
publication, and deployment were not authorized and are not release claims.

## Plan reconciliation

The current product contains substantial implementation for every phase, but
the canonical plan still records all 29 tasks as `planned`. This audit does not
change managed plan state. In particular:

- `TASK-001` and `TASK-002` have approved product decisions; the unchanged
  managed plan still records its historical open questions.
- `TASK-006` has a concrete guarded dispatcher and real temporary Cognee
  relational/semantic initialization, but no standalone deployed interface.
- `TASK-007`, `TASK-013`, and `TASK-014` have real small-corpus Cognee/model
  execution plus provider-neutral golden tests; scale evidence remains bounded.
- `TASK-016` has a guarded, publicly atomic canonical promotion and
  source-resync path under disposable repository/synchronizer test ports. The
  product has the approved local reviewer policy but no authorized
  product-repository write port.
- `TASK-018` and `TASK-028` now pass the complete public destructive-control
  acceptance matrix against disposable components, including governed
  canonical deletion. Provider-native and non-fixture destructive execution
  remain outside the evidence boundary.
- `TASK-020` has runtime-verified deterministic ZIP/age exchange and native
  COGX archive compatibility; database-backed COGX migration remains outside
  the accepted evidence.
- `TASK-022` and `TASK-023` have local authorization/isolation controls; the
  approved release decision deliberately selects no shared production backend.
- `TASK-025` has both the generic extension framework and the approved
  software-engineering profile proof through two-agent public recall.
- `TASK-027` has exact/lexical and synthetic local component benchmarks, not
  real-provider service-level measurements. `TASK-028` has component and
  in-process integration evidence, not the complete acceptance suite.
- `TASK-029` has a current row-by-row audit with explicit evidence levels and
  limitations rather than an unsupported deployment claim.

## Preservation and operational state

- The PRD and plan digests above remained unchanged during the audit.
- The tracked configuration selects approved local capability but never
  initializes a provider during load. Real Cognee runs used disposable roots
  below `.sys4ai/memory/` and removed them; the product derived root is absent.
- The Ollama daemon was stopped after the authorized local-model checks, and an
  independent port check found no listener on 11434. The ignored product-local
  Ollama and FastEmbed caches remain rebuildable derived state. The user-home Ollama
  identity file created by its first startup was not inspected, copied, or
  deleted.
- One source-inspection subprocess imported Cognee without the adapter's
  hardened environment and created a 1,407-byte user-home Cognee log. No project
  record or model request was supplied to that process; the log was not read or
  deleted because external cleanup was not authorized.
- No project-local Git repository, product remote, commit, push, publication,
  deployment, network listener, or hosted endpoint was created.

## Post-ledger validation

- `uv run --frozen python tools/validate_release_evidence.py`: valid, 296
  rows, with 272 `targeted_tests_passed`, 12 `static_verified`, seven
  `runtime_verified`, four `implemented_unverified`, and one `deferred`.
- `make validate-memory`: Ruff passed; strict mypy reported no issues in 107
  source files; 475 tests passed and the opt-in live Cognee test skipped after
  daemon shutdown, with upstream TestClient/Cognee deprecation warnings; the
  final ledger validator returned the same valid distribution.
- Opt-in real local profile: one test passed in 17.41 seconds, creating and
  reading real graph nodes/edges and recalling source-backed metadata with zero
  non-loopback socket attempts.
- The package/exchange suite exercised `age` and `age-keygen` v1.3.2 with
  temporary identities; the public encrypted export and wrong-identity denial
  passed.
- `uv run --frozen pytest -q tests/verification/test_release_evidence.py`:
  three passed after its current-count assertion was aligned to this audit.
- `make validate-memory-minimum-risk`: seven passed.
- Maintained-document audit: 36 Markdown files and 94 repository-local links,
  with zero missing targets.
- `uv lock --check`: the unchanged lock resolved 163 packages.
- `uv pip check`: all 157 installed packages compatible.
- From the parent depot root, the repository-contract suite passed all 11
  tests, including the registered product path and truthful external-state
  assertions.
