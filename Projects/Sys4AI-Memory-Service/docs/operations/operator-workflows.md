# Operator workflows

Before using these operations, follow
[memory readiness and activation](memory-readiness-and-activation.md). Give the
human and next agent the observed exact, semantic and Cognee state, and ask
about activation only when that decision is not already settled. An initialized
exact-only consumer needs a supported configuration migration before semantic
settings change; the current runtime has no general installed command for that
transition.

## Interface availability

The Python, CLI, HTTP, and MCP adapters use the provider-neutral
`MemoryServiceDispatcher` protocol. `MemoryService` is the concrete unified
dispatcher. It performs fresh canonical authorization, project/dataset and
configuration gates, process-local mutation serialization, hashed idempotency,
long-operation status, audit capture, metrics, and safe error normalization
for the public operations and initialization/status controls. Its built-ins route to
explicitly injected components; a missing component fails with
`MEMORY_NOT_INITIALIZED` rather than selecting a fallback.

The installed `sys4ai-memory` command uses `LocalMemoryRuntime` to construct
`MemoryService` from canonical project configuration, permissions and registries.
Operations that use initialized memory require a matching receipt and storage;
missing or incompatible state returns `MEMORY_NOT_INITIALIZED`. It does not
start a persistent network service. The HTTP factory creates an ASGI
application but does not start a listener. `McpAdapter` is a framework-neutral tool adapter, not a running MCP
server. Do not describe these surfaces as a deployed service.

Focused integration tests inject one `MemoryService` and route Python, HTTP,
CLI, and MCP health and recall calls through the same canonical authorization
and audit boundary while confirming that the ASGI application opened no
listener. A separate substitution case sends one unchanged Python-client recall
through in-memory and injected fake-Cognee providers. That is local test
evidence, not a process bootstrap, real Cognee run, or deployment.

Safe interface inspection:

```bash
uv run --frozen sys4ai-memory --help
uv run --frozen sys4ai-memory init --help
uv run --frozen sys4ai-memory sources --help
uv run --frozen sys4ai-memory recall --help
uv run --frozen sys4ai-memory operation --help
```

Every normal CLI request requires these global identity fields before its
command:

```text
sys4ai-memory \
  --project-id sys4ai-memory-service \
  --dataset-id sys4ai-memory-service \
  --principal-id <canonical-principal-id> \
  --agent-type <registered-agent-type> \
  --run-id <current-run-id> \
  <command>
```

These identifiers are claims used to resolve current canonical permission;
they do not grant permission by themselves. Cross-project requests must repeat
`--query-project-id` for every project and set `--explicit-cross-project`.

## Initialize safely

The reviewed workflow is preview, review, then an authorized apply. New-project
and manual consumer bootstrap also provide `init-memory` as a direct authorized
route with the same internal source, path, configuration and permission checks:

```text
<identity flags> init preview --configuration-path config/memory.toml
<identity flags> init apply \
  --configuration-path config/memory.toml \
  --impact-digest <reviewed-sha256> \
  --idempotency-key <operation-key>
```

Preview is non-mutating. It reports project/root, provider and pinned version,
deployment profile, configuration fingerprint, source counts, planned private
directories, security posture, warnings, and an impact digest. Apply rereads
configuration, recomputes the digest and identity, requires explicit
authorization and the exact capability gate, creates only the previewed
derived directories with private permissions, and writes a sanitized receipt.
The installed runtime can initialize Cognee when semantic configuration and
canonical permission enable the provider. The exact-only default initializes
exact storage without activating Cognee or models. A receipt records that
outcome; model and semantic retrieval readiness require their own verification.

Although preview is non-mutating, `MemoryService` requires a current
action-specific `administer` grant for both initialization controls. Operation
status requires `read`; the other public operations use the permission in the
public operation catalog.

The tracked product configuration selects an approved local profile, while
fresh consumers select an exact-only default. Inspect the actual project's
state and permissions; do not weaken gates to make an example succeed. A
configuration change on an initialized project invalidates its bound receipt.
Neither direct initialization nor reviewed apply migrates that receipt; use
the [existing-project guidance](memory-readiness-and-activation.md#a-project-already-initialized-with-exact-memory).

## Inspect and synchronize sources

```text
<identity flags> sources list --include-excluded
<identity flags> sources explain docs/security/threat-model.md
<identity flags> sync --dry-run --idempotency-key <operation-key>
<identity flags> sync --source-id src_MEM-SEC-001 --idempotency-key <operation-key>
```

List and explain are read-only. Explain evaluates a registered path without
reading its content. Sync discovers current registered sources, normalizes each
with its declared adapter, compares manifests, and updates only derived state.
A dry run currently returns included/excluded/failure counts. An executing
`MemoryService` response returns document and record counts, sanitized failure
metadata, skipped source IDs, a stable generation ID, added/changed/moved/
deleted/unchanged/failed/resumed delta counts, manifest and source revisions,
checkpoint metadata, a deterministic receipt digest, provider result when
present, and long-operation status.

Sync requires this project's initialized state and canonical permission.
Exact consumer synchronization has installed-runtime evidence; semantic sync
also needs the configured and initialized provider. Fixture results or a
producer model spike do not prove that this project's live Cognee-backed sync
has run. The unified built-in has no
cross-store transaction coordinator. A provider failure after an exact-index
write requires drift detection and rebuild/recovery.

## Retrieve evidence

```text
<identity flags> recall "MEM-FR-140" --mode exact --limit 5
<identity flags> recall "How are backup assets classified?" --mode lexical --limit 10
<identity flags> get mem_example --include-history
<identity flags> graph mem_example --relation-type CITES
<identity flags> explain mem_example
```

`recall` returns a retrieval-only evidence bundle by default, with request/trace IDs,
mode, evidence state, source anchors, authority/trust/lifecycle metadata,
channel scores, selection reasons, applied filters, and omitted count. It does
not invoke answer synthesis unless the caller adds `--synthesize`. The unified
built-in also returns an auditable trace
with selected channels, actual per-channel candidate counts, filter stages,
ranking/dedup/budget stages, returned source IDs, and omissions. If nothing
survives permission, project/dataset,
scope, namespace, lifecycle, time, trust, authority, ranking, and context
limits, the result is `evidence_state="insufficient"` with an empty result set.
Treat this as insufficient evidence, not as permission to guess.

Explicit synthesis requires both an enabled semantic/model configuration and
an injected `EvidenceSynthesisPort`. The port receives only the already
authorized evidence bundle after another fresh canonical permission check; the
permission is checked again before the result is released. Its response is
rejected unless every declared material claim has at least one record/source
anchor that exactly matches a returned evidence record. Empty evidence
produces `insufficient_evidence` without calling the synthesizer. No concrete
LLM synthesis port is composed in this checkout, and the tracked profile keeps
the capability disabled.

```text
<identity flags> recall "Summarize the approved decision" \
  --mode hybrid \
  --synthesize
```

`get` retrieves one stable record and can include history. `graph` is hard
bounded to one relation hop in the current public contract. It returns the
ordinary filtered evidence bundle plus paths anchored at the requested record;
each path carries direction and the complete typed relation, including source,
validation/confidence, temporal interval, and lifecycle state. Relations with
an unselected endpoint, a foreign project, a disallowed type, or an inactive
time/lifecycle state are not returned. `explain` reports provenance, status,
authority, and ranking information. Execution-critical control results still
require a direct reread of the current canonical source.

For an operator-only diagnostic fallback, use a fixed-string search against the
specific registered canonical path, then open and review that source directly:

```bash
rg -n --fixed-strings -- '<exact identifier or phrase>' '<registered path>'
```

This command is not a service index, permission source, or proof that a Task or
runtime state is current.

The SQLite/FTS5 exact/lexical path passed a 100,000-fragment benchmark. A bounded
real Cognee run with the approved local model pair created semantic and graph
representations and returned one source-anchored public record through the
provider-neutral adapter. Structured multi-hop path behavior and explicit cited
synthesis remain fixture-verified; no model-generated answer is accepted as
runtime or governance evidence.

## Propose, review, and promote a write

The CLI accepts a complete typed proposal JSON object:

```text
<identity flags> propose \
  --proposal-json '<schema-valid non-sensitive proposal object>' \
  --idempotency-key <operation-key>
<reviewer identity flags> approve mwp_example \
  --decision approve \
  --reason "Reviewed against current canonical sources" \
  --idempotency-key <operation-key>
```

Do not place secret values in a CLI JSON argument. For real use, construct the
typed request in a trusted process so sensitive shell history is not created.
The payload must name type, scope, evidence, status, trust, sensitivity,
authority, target, and idempotency. The write matrix may keep a session-only
record, commit an authorized derived record, or stage a human-readable
proposal and patch. Canonical/governance targets always stage for review.

Approval rereads the canonical permission document and requires a named human
reviewer or an authorized automation identity with a higher-system policy
reference. Promotion planning rereads the reviewer policy and canonical target.
When the embedding application supplies a `CanonicalPromotionCoordinator`, an
approved artifact can be applied through a recoverable project-repository port;
the coordinator then requires a matching synchronization receipt before it
returns a `promotion_receipt`. A write or sync failure restores the original
canonical bytes and resynchronizes the restored source before the public API
returns a stable error. If compensation itself fails, the attempt is marked
recovery-required and cannot produce a success receipt. Without that explicit
port, the service returns only a governed `promotion_request` and does not
modify the target file.

Rejection never writes the canonical target. Pending proposal content is
purged unless an approved retention policy explicitly permits retaining only
review metadata. The temporary-path integration tests cover successful
promotion, matching sync evidence, rejection disposal, rollback, idempotency,
permission drift, and failure immediately after canonical replacement; they do
not authorize a change to this checkout.

The tracked policy names one human `local-owner`, requires one approval, and
forbids proposal self-approval. Staging/review/promotion components are
fixture-verified, but no product-repository write port or Git authority exists.
`MemoryService` keeps the
proposal-to-artifact lookup in process memory; restart-safe approval lookup has
not been verified.

## Session, episodic, and improvement data

Session records are temporary, non-authoritative, session-scoped, and
time-to-live bounded. Episodic records store concise rationale, evidence and
input/output references, actions, tools, and outcome; they do not store private
chain-of-thought. Durable persistence uses the approved 72-hour session and
365-day episodic TTL limits. A supplied persistence port must enforce expiry
purge and cannot silently extend them.

Automatic feedback is disabled by decision. Explicit feedback must be typed,
evidence-backed, scoped to the target project/profile, secret-free, and
authorized for derived writes. Reweighting or consolidation cannot increase a
record's authority or trust. Conflicting records stay separate.

```text
<identity flags> improve \
  --record-id mem_example \
  --feedback-json '<typed non-sensitive feedback object>' \
  --idempotency-key <operation-key>
```

The command is available only to a principal with the current action-specific
derived-write grant; the tracked `local-owner` mapping includes that grant.

## Supersession and forgetting

```text
<identity flags> supersede mem_old mem_replacement \
  --reason "Replacement is current" \
  --idempotency-key <operation-key>
<privileged identity flags> forget \
  --record-id mem_old \
  --action delete-derived \
  --reason "Approved derived-data removal" \
  --idempotency-key <operation-key>
```

Supersession requires two active records in the same project/dataset and a
composed lifecycle catalog plus deterministic lifecycle index. The service
updates the SQLite current/history projection and catalog with one effective
timestamp. Normal exact, lexical, or hybrid recall then excludes the
superseded record—even if a provider returns a stale active candidate—while
historical recall can retain it with lifecycle metadata. The response field
`deterministic_index_updated=true` confirms that projection change; it is not
evidence that provider-native storage was rewritten.

Forget actions are `expire`, `withdraw`, `delete-derived`, `delete-source`, and
`privacy-erase`. The first forget request is a preview even though the CLI
syntax does not contain a `--preview` flag. Execution adds both `--execute` and
the exact preview-returned `--operation-id` and `--impact-digest`, using a new
idempotency key for the execution request, with current action-specific delete
permission.

`delete-source` first returns a separate governed project-change request. Its
execution remains denied unless the embedding application supplies a governed
canonical executor for that exact preview; successful execution verifies the
completed resource IDs and local target removal before returning a receipt.
Privacy erasure must cover all derived/export/backup copies under project
control and uses the same executor boundary for canonical effects. Current
forget behavior is fake/temp verified only; no live product data was deleted.
The unified dispatcher currently reports
`provider_forget_executed=false`; it does not coordinate provider-native forget
with filesystem/lifecycle deletion. Do not claim full privacy erasure through
that dispatcher until every declared storage class is integrated and checked.

## Rebuild, generation, rollback, and drift

```text
<privileged identity flags> rebuild \
  --generation-label candidate-1 \
  --idempotency-key <operation-key>
<privileged identity flags> rebuild \
  --activate \
  --generation-label candidate-1 \
  --operation-id <preview-operation-id> \
  --impact-digest <reviewed-sha256> \
  --idempotency-key <execution-key>
```

Without `--activate`, rebuild produces a non-mutating preview. Activation
requires current action-specific rebuild permission plus the unchanged
preview operation ID and digest. Preview and activation use distinct
idempotency keys; an idempotency key still identifies one exact request.
The rebuilder discovers and normalizes canonical sources, builds an isolated
exact/provider generation, checks counts and checksums, writes manifests and a
receipt, moves the candidate into the generations directory, and updates the
active pointer last. Failure or cancellation leaves the prior generation
active and records a checkpoint.

Use `operation status` for the returned operation ID:

```text
<identity flags> operation status op_example
```

The current service runs each interface-dispatched long operation synchronously
and reports one total unit. It binds a hashed request fingerprint and checkpoint
before work. A failed or cancelled retry-safe operation automatically resumes
on the same idempotency key and identical payload; changed reuse conflicts, and
a later successful retry replays without repeating work. The public interfaces
expose status lookup, not an explicit cancel or resume action, and they do not
stream intermediate progress.

Drift is part of health rather than a separate CLI command. A degraded drift
component requires source/config/profile/schema/adapter/provider/model or
generation reconciliation before current-state claims. Rebuild is fake/temp
verified with an in-memory provider, not real Cognee.

The current dispatcher always asks its rebuild port for deterministic full
mode. The CLI accepts `--generation-label`, but the built-in does not forward
that label. Incremental mode and operator-selected generation labels are not
available through this dispatch path.

## Export, import, and COGX

```text
<privileged identity flags> export exports/candidate \
  --format sys4ai \
  --idempotency-key <operation-key>
<privileged identity flags> import exports/candidate \
  --expected-sha256 <package-sha256> \
  --idempotency-key <operation-key>
```

The provider-neutral package implementation currently permits only an
unencrypted disposable-test-only candidate inside an explicit temporary root.
The CLI service path does not expose a flag that can authorize that developer
test exception. Production export/import remains denied until archive and
encryption policy is approved.

The unified service uses an optional `PortableExchangePort`; no standalone
exchange composition is installed by the CLI. A missing port fails closed.
`DisposableMemoryPackageExchange` is the only concrete composition in this
checkout. It accepts only the in-memory conformance provider, an explicit
test-only policy, and an export root confined to the project boundary. The
integration suite exercises export, ZIP inspection, import preview, and import
activation through `MemoryClient` and the unified authorization/audit path. It
returns `production_ready=false` on every result and must not be installed as a
production exchange port. Import requires a distinct inactive in-memory
staging provider; the adapter changes its active provider reference only after
the staged result and filesystem activation validate successfully. That swap
is local to the exchange adapter; it does not rebind an injected retrieval,
synchronization, or general `ServiceComponents.provider`. The test therefore
does not prove service-wide provider migration or lock-in prevention.

Import validation is non-activating. Activation adds `--activate` and the
reviewed `--impact-digest`, and requires distinct current `memory.import` and
`memory.import.activate` authorization checks. It stages and activates derived
data without overwriting canonical sources. Provider preview and execution
results are reconciled against the exact provider, request, trace, scope,
format, impact digest, and record/relation IDs before any filesystem activation
receipt or pointer is written.

`--format cogx` names the optional provider-owned format, but COGX is disabled
unless the adapter and policy explicitly approve it. The real Cognee 1.5.3
native archive API passed an isolated writer/reader/source
[compatibility probe](../verification/cogx-compatibility.md); no populated
Cognee database export/import or production exchange ran. See
[backup and recovery](backup-and-recovery.md) for the asset and restore
boundaries.

## HTTP and MCP inventory

HTTP exposes POST-only routes below `/v1/projects/{project_id}` for health,
source list/explain, sync, recall, get, graph, propose/approve, supersede,
improve, forget, rebuild, export/import, explain, and operation status. Every
request carries dataset, scope, query-project set, client/purpose, request and
trace IDs, idempotency key when required, and the typed operation payload.
Authentication is mandatory except in explicit loopback test mode.

MCP default mode exposes exactly six tools:

- `sys4ai_memory_health`
- `sys4ai_memory_recall`
- `sys4ai_memory_get`
- `sys4ai_memory_graph`
- `sys4ai_memory_propose`
- `sys4ai_memory_explain`

Read-only mode omits propose. Administrative mode also inventories approve,
improve, forget, rebuild, export, and import, but each call still needs its own
authorization. Destructive tools are never default-enabled. There is no
separate metrics or audit CLI/MCP operation in the current interface contract.
Detailed health exposes a metadata-only metric snapshot when calls reach a
configured `MemoryService`; audit remains an internal cross-cutting behavior.
