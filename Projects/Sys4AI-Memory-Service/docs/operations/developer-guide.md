# Developer guide

## Preserve the service boundary

Application code depends on provider-neutral contracts. The supported layering
is:

```text
Python / CLI / HTTP / MCP adapters
              |
 MemoryServiceDispatcher protocol
              |
         MemoryService
              |
 authorization, retrieval, policy, lifecycle, rebuild, exchange, observability
              |
          MemoryProvider
              |
       Cognee or in-memory adapter
```

Only `src/sys4ai_memory/providers/cognee.py` may import Cognee. Do not expose a
Cognee object, native result shape, local file path option, storage handle, or
native tool to a client. Provider calls carry explicit project, dataset,
principal, scope, trace, and current authorization data.

## Development setup

```bash
uv sync --locked --extra dev --extra cognee
uv run --frozen ruff check src tests tools
uv run --frozen mypy src tools
uv run --frozen pytest
uv run --frozen python tools/validate_release_evidence.py
```

Do not run the real provider, model daemon, network listener, or destructive
operation as part of the default suite. Real-provider tests must be explicit,
isolated, locally approved, and marked separately from fake/temp tests.

## Interface contracts

`MemoryClient`, the CLI parser, the FastAPI adapter, and `McpAdapter` all build
the same `DispatchRequest` and receive the same `DispatchSuccess` or stable
`ErrorEnvelope`. Mutating actions require an idempotency key. Read actions
reject one. Long-running success envelopes include an operation reference for
status polling.

`MemoryService` is the concrete synchronous dispatcher. Construction performs
no provider or storage initialization. It requires a loaded configuration,
`AuthorizationService`, `AuditRecorder`, and `VersionContext`; callers inject
`ServiceComponents`, `ProviderAuthorizationBridge`, `MetricsCollector`,
`OperationTracker`, or operation-specific `ServiceHandler` functions as
needed. Missing optional components fail closed with
`MEMORY_NOT_INITIALIZED`.

The Python client is synchronous at the public edge and requires an injected
dispatcher. The HTTP factory returns an ASGI application but does not bind a
socket. MCP is a framework-neutral catalog/call adapter; it is not a running MCP
server. The CLI accepts an injected `MemoryServiceDispatcher` for embedding but
does not construct `MemoryService`; without injection it returns
`MEMORY_NOT_INITIALIZED`. Keep adapter and dispatcher tests separate from proof
of a composed live service.

## Provider and concurrency rules

`MemoryProvider` is an asynchronous protocol for initialize, capabilities,
remember, recall, improve, forget, health, export, import, and migrate. The
in-memory implementation is a deterministic conformance provider. The Cognee
adapter is lazy, exact-version gated, local-path confined, no-cloud-fallback,
and authorization-bound before mutation.

The conformance provider builds normalized search text and token sets when a
record changes and indexes relation IDs by endpoint. Recall applies a minimum
query-coverage gate and expands only one relation hop, so generic project terms
cannot create evidence and relation traversal does not depend on insertion
order or scan every stored relation. These mechanics support deterministic
tests and benchmarks; they are not a production semantic model or graph store.

Provider-substitution acceptance uses the same `MemoryClient.recall` call and
provider-neutral evidence schema against the in-memory adapter and an injected
fake Cognee runtime. A static import check permits Cognee distribution imports
only inside `providers/cognee.py`. This proves the boundary and call-shape
interchangeability; it does not prove real Cognee recall quality.

The Cognee adapter also accepts a validated provider-neutral snapshot when it
is used as a distinct isolated import stage. It maps every eligible record and
typed relation through the same allowlisted representation as `remember`,
requires an unchanged preview digest and import authorization before invoking
the runtime, and returns exact imported IDs. The cross-adapter test uses the
fake runtime; real database-backed Cognee import remains unverified.

The focused [COGX compatibility probe](../verification/cogx-compatibility.md)
loads the real pinned Cognee 1.5.3 package and round-trips its native archive
types without a database, model, or network. Import hardening sets the local
Cognee paths and offline library switches before package load, including
LiteLLM's local model-cost map, then restores the host process environment.
Keep database-backed export/import and model-backed behavior as separate
disposable-runtime gates.

The local design requires one service process to own writes to an embedded
provider/index generation. Clients must never open those files directly.
`MemoryService` serializes mutating requests in one process and hashes
idempotency keys for replay/conflict checks. Long operations bind the request
fingerprint and checkpoint before execution, then resume a failed/cancelled
retry-safe attempt only for the same key and payload. In-process component
locks and private advisory file locks protect staging and metadata appends.
Two-phase forget and rebuild execution carries the stable operation ID returned
by preview plus its reviewed impact digest, while using a distinct idempotency
key for each exact preview or execution request.
These do not coordinate independently started service processes, and the
default service idempotency/proposal maps are process-local. A process bootstrap
and full single-writer operating workflow have not been verified. These
component controls do not make an embedded profile a secure shared deployment.
Shared use requires a centralized writer plus authenticated, backend-enforced
dataset isolation.

## Retrieval behavior

The planner classifies eleven query intents without a model. Exact/lexical
queries use `ExactIndex`; semantic/graph/temporal channels use a
provider-neutral provider. Authorization is checked before backend reads and
again before evidence assembly. Results are filtered by project, dataset,
scope, namespace, status, trust, authority, time, and current/history mode,
then ranked, deduplicated, and bounded.

The retrieval engine returns evidence only. If no candidate survives, it
returns `evidence_state=insufficient` with no synthesized answer. The service
may call an injected `EvidenceSynthesisPort` only when `RecallInput.synthesize`
is true and the semantic/model configuration gate passes. It validates that
canonical authorization remains current immediately before and after the port
call, that the result identity and model profile match the request, and that
every material claim cites an exact record/source anchor from the authorized
evidence bundle.
Governance and external-evidence namespaces cannot be mixed in one request,
and generated or external text cannot enter the governance authority lane.

Use `RetrievalEngine.recall_with_trace()` in service integrations. It returns
the result plus actual channel candidate counts, filtering, ranking,
deduplication, budget, selected-source, and omission metadata. A custom
`ServiceHandler` for recall must provide its own validated `RecallTrace` in the
`PortResult`; do not reconstruct channel counts from final rows.

Use `RetrievalEngine.graph_paths_with_trace()` for the current structured graph
surface. It returns one-hop paths only, and each path retains the complete typed
relation metadata. A relation is omitted unless both endpoints survived the
ordinary evidence filters and budget.

## Write and lifecycle behavior

The write policy requires type, scope, evidence, status, trust, sensitivity,
authority, target, idempotency, current canonical permission, and secret-free
content. It returns a policy action such as session-only, stage-for-review,
derived commit, episodic commit, or reject.

`ProposalStager` writes a human-readable proposal, patch, and review material
under a confined staging root. `ReviewerAuthorizationGate` rereads the
canonical permission document and requires the named human or higher-policy
automation reviewer. `CanonicalPromotionPlanner` rereads both reviewer policy
and target content, then returns a normal governed change request.
`CanonicalPromotionCoordinator` can execute that request only through an
injected governed-repository port and a matching canonical-source sync port. It
rolls back and resynchronizes the original bytes on a recoverable downstream
failure. The public service emits success only after commit and matching source
synchronization; a failure after canonical bytes were replaced is compensated
before a stable error is returned. A failed compensation is surfaced as a
recovery-required failure and never as success. No coordinator is composed
automatically.

Lifecycle state is explicit and historical. Built-in supersession requires two
active records in one project/dataset plus both a `LifecycleCatalog` and a
`LifecycleIndexPort`. It validates the catalog first, atomically changes the
SQLite current/history projection, applies the same timestamp and links to the
catalog, and rejects divergent results. `RetrievalEngine` treats that
deterministic lifecycle projection as authoritative over stale provider
candidate status, so ordinary hybrid recall excludes the prior record while a
historical query can retain it. This does not mutate a provider-native store;
source-first rebuild remains the recovery path. Destructive operations use
preview, fresh action-specific permission, digest recheck, bounded paths, and
a sanitized receipt. Canonical deletion first produces a governed change
request and remains fail-closed unless an injected canonical executor completes
the exact preview through the normal atomic project workflow. The service then
checks the completed resource IDs and verifies that every local canonical
target was removed before it transitions lifecycle state or returns a receipt.

The current built-in dispatcher has explicit integration limits. Sync has no
transaction coordinator across exact-index and provider writes. Approval uses
an in-process proposal/artifact lookup. Forget does not invoke provider-native
forget. Rebuild requests deterministic full mode and does not forward the CLI
generation label. Export/import require an injected `PortableExchangePort`,
and initialization apply creates derived directories and a receipt but leaves
`provider_initialized=false`. Preserve these limits until an integrated design
and tests replace them.

## Profile development

Start with `profiles/base/profile.yaml` and the public
`schemas/memory/memory-profile.schema.json`. An extension may add names; it
cannot silently redefine a base type, relation, adapter, or policy. Load the
base and extensions as one deterministic set and validate them against
`registries/memory_profile_registry.csv`.

Pass that validated set to `IngestionSynchronizer.profile_set` when extension
sources are active. Synchronization selects each source's exact loaded profile
version, permits only adapters declared in its inheritance chain, and rejects
adapter output whose record type belongs outside that chain. The failure is
reported as `PROFILE_INCOMPATIBLE` and no document from that source reaches an
index or provider.

A change to record types, relations, adapters, write policies, retrieval
strategies, or compatibility is a representation change. Use
`assess_representation_change`; require a migration or full rebuild before
activation. The current migration registry plans version paths and emits a
dry-run impact digest. It does not transform bytes itself.

Checked-in public schema projections are guarded by model-to-file parity tests.
Runtime indexes and provider snapshots are generated under a checksum-bound
generation manifest; drift verification detects modification, deletion, or
symlink substitution. Regenerate either class from its source rather than
editing the projection or derived artifact.

The neutral temporary fixture still tests the generic extension seam. The
tracked `software-engineering@1` profile is the approved product proof and is
also exercised through public sync and recall for two agent identities without
changing the operation catalog.

## Verification boundaries

Use focused suites while developing:

```bash
uv run --frozen pytest -q tests/contracts tests/configuration tests/profiles
uv run --frozen pytest -q tests/ingestion tests/exact_index tests/retrieval
uv run --frozen pytest -q tests/providers tests/service tests/interfaces
uv run --frozen pytest -q tests/policies tests/lifecycle tests/security
uv run --frozen pytest -q tests/rebuild tests/exchange tests/observability
```

Then run the broader commands shown above. Classify every result correctly:
schema/static, focused test, broader suite, measured benchmark, real runtime,
or end-to-end. Do not advance the release evidence ledger merely because a
file exists or a child task reported success. Current dispatcher tests verify
the common guard across every action plus built-in initialization
preview/no-write, detailed health, and source-to-SQLite/in-memory-provider sync
paths. They do not directly exercise every other built-in subsystem
integration.
