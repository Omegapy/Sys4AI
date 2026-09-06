# Observability and troubleshooting

Observability data is metadata-only derived state. It helps diagnose behavior
but never grants permission, changes a decision, or becomes the sole canonical
receipt for an approved action.

## Health

The composite health contract reports three top-level states:

- liveness: whether the service process can answer;
- readiness: the worst state across required dependencies; and
- drift: whether canonical inputs and the active generation still agree.

When a `HealthAggregator` is composed, its `CompositeHealth` report contains
exactly these six components:

1. provider connectivity;
2. exact index;
3. source registry;
4. schema compatibility;
5. storage access; and
6. source/index drift.

`healthy`, `degraded`, and `unavailable` are distinct. A process can be live but
not ready. In particular, the Cognee liveness probe can confirm that version
1.5.3 is installed without importing or initializing Cognee. Readiness remains
degraded while the provider is not initialized. The adapter deliberately does
not call a writeful native Cognee health routine.

Health aggregation and drift detection are contract implemented and covered
by focused tests. They are not yet verified against a real Cognee store or an
accepted active generation.

`MemoryService` always reports configuration state and whether provider,
exact-index, and retrieval components were composed. `--detailed` adds the
metric snapshot. The six-component `health` object is present only when a
`HealthAggregator` was injected; absence is composition state, not a healthy
dependency result.

## Metrics

`MetricsCollector` records fixed, content-free dimensions for:

- ingestion successes, failures, and lag;
- recall latency by retrieval channel;
- sufficient and insufficient evidence counts;
- returned sources and explicitly selected results;
- source/index drift;
- approval and rejection rate;
- operation and provider errors;
- duplicate active records;
- storage bytes by memory class;
- rebuild progress, warnings, completion/failure, and duration; and
- expired-entry cleanup lag.

It does not accept query text, result passages, source content, or dynamic
content-derived labels. `MemoryService` exposes the metadata-only snapshot in
the result of detailed health. The collector has no separate CLI, HTTP, or MCP
metrics operation, and its default state is process-local.

`operation_audit_to_otlp_json()` projects a validated audit record into an
OpenTelemetry Protocol (OTLP) JSON `TracesData` envelope. It uses lowercase
32-hex trace IDs, 16-hex span IDs, numeric span/status enums, lower-camel-case
field names, and decimal-string nanosecond timestamps as required by the
[OTLP JSON encoding](https://opentelemetry.io/docs/specs/otlp/) and
[OpenTelemetry trace context](https://opentelemetry.io/docs/specs/otel/trace/api/).
The span contains fixed metadata attributes only. Actor, principal, project,
dataset, and non-W3C internal trace identifiers are hashed; query text, source
content, target IDs, credentials, and headers are absent.

`AuditRecorder` sends that envelope only when
`TelemetryControl.telemetry_export_enabled=true` and the embedding process
injects an `OpenTelemetryTraceExporter`. An enabled gate without an exporter,
or an exporter supplied while the gate is disabled, is rejected at
construction. The product implements no endpoint, transport, header parsing,
retry loop, or background sender. The tracked local profile keeps
`telemetry_export = false`, so ordinary operation performs no export.

## Audit records

Every public operation and the allowlisted control-plane actions can produce an
`OperationAuditRecord` with actor, effective principal, project/dataset,
operation, stable target IDs, policy decision, current permission revision and
hash, result code, trace ID, version context, counts, warnings, and a
content-free recall trace.

The control-plane allowlist is initialization preview/apply, operation status,
source registration, profile installation, configuration change, permission
change, and telemetry change. An unknown administrative operation fails
validation. `AdministrativeActionExecutor` is the local control-plane boundary:
it rereads current canonical, action-specific permission before invoking a
reviewed callback and records `denied`, `failed`, or `succeeded` after the
attempt. It does not expose a network endpoint or make a change by itself.
`MemoryService` wraps all 16 public operations and initialization
preview/apply/status with authorization, success/failure, and denial audit
capture in focused tests. Its built-in recall calls
`RetrievalEngine.recall_with_trace()` and returns/audits actual selected
channels, per-channel candidate counts, filter stages, ranking/dedup/budget
stages, returned source IDs, and omissions. A custom recall handler must supply
its own validated `RecallTrace`.

Source/profile registration and other control-plane changes remain outside the
three dispatcher controls. Focused tests execute every allowlisted action
through the authorized executor, including a real source-registry fixture
write, a denial after canonical permission changes, and a failed callback. No
live project control-plane change or deployed service has been verified.

The default configured location is `.sys4ai/memory/audit/events.jsonl`. Local
capture is opt-in at runtime even when this path is configured. The append-only
store uses private file permissions, an advisory lock, path confinement,
record/file size bounds, structured redaction, and complete-line writes.

Do not record raw queries, source passages, proposal bodies, prompts, model
responses, credentials, headers, environment values, provider payloads, or
stack locals. See [logging and redaction](../security/logging-and-redaction.md).

## Long-running operation status

Sync, improve, forget, rebuild, export, and import use the long-running status
contract. Status records include the operation ID, state, trace ID,
idempotency-key hash, attempt, progress, timestamps, checkpoint fingerprint,
warning codes, and error code. The raw idempotency key is not retained.

Allowed states are `pending`, `running`, `cancel_requested`, `cancelled`,
`succeeded`, and `failed`. Progress cannot move backward. A failed or cancelled
operation can resume only when it is marked retry-safe and has a checkpoint.
Reusing an idempotency key for a different project or operation fails closed.

The status tracker supports an optional local JSON Lines store and reloads its
latest records. It does not run work by itself; the service dispatcher owns the
actual operation and checkpoint integration.

The current dispatcher executes each long operation synchronously and records
one total unit. It binds a hashed request fingerprint and checkpoint before the
handler. A failed or cancelled retry-safe operation automatically resumes when
the same key and payload are submitted again; changed reuse conflicts, and a
successful result later replays without duplicate work. Interfaces expose
status lookup only, not explicit cancel or resume, and do not stream
intermediate progress.

## Validation receipts

`build_validation_receipt` records metadata for a command that already ran. It
does not execute the command. A receipt binds the command tokens, exit status,
time, source revision or non-versioned state, configuration/provider/profile
fingerprints, warnings, and evidence locators into a deterministic receipt ID.

Do not claim a receipt proves more than its command observed. The product has
no project-local repository and the parent depot ignores this directory, so a
truthful product receipt uses `not_versioned` rather than inventing a product
Git revision.

## Troubleshooting

| Symptom or error | Meaning | Safe response |
|---|---|---|
| `MEMORY_NOT_INITIALIZED` | The CLI has no injected `MemoryService`, a required optional component is absent, or the safe configuration remains inactive. | Confirm the dispatcher/bootstrap and exact component composition. Review configuration and decisions; do not flip gates just to clear the error. |
| `configuration is Stage 0 only` | A requested capability is not available from the committed profile. | Produce the required decision and evidence, then use a reviewed activation profile. |
| `canonical_permission_unavailable` or `no_matching_current_grant` | Current canonical authorization is missing, invalid, stale, or does not cover the operation/scope/target. | Repair the canonical control record through the governed workflow. Never authorize from remembered prose. |
| `project_dataset_mismatch` | Request identity does not match the service boundary. | Correct the explicit project/dataset pair; do not remap a provider store silently. |
| Source is excluded or unmatched | Registry, hard exclusion, Git ignore, path, type, size, or secret policy denied discovery. | Use source explanation, inspect the reason code, and make a reviewed registry change only if the source is safe and intended. |
| Source normalization failed | The adapter rejected syntax, size, nesting, encoding, or the exact index transaction. | Inspect the sanitized source/adapter/stage/category/recovery metadata; fix the source or adapter and resume its checkpoint. |
| `evidence_state="insufficient"` | No visible result survived authorization, lifecycle, scope, namespace, trust, ranking, and context limits. | Treat it as no answer. Inspect filters and source registration; do not synthesize unsupported content. |
| Provider degraded | Cognee is uninitialized, incompatible, or native readiness is unavailable. | Keep exact-only diagnostics available if authorized. Do not enable a cloud fallback. |
| Stale impact digest | Configuration, permission, source, target, or package state changed after preview. | Discard the old preview and generate a new one. |
| Concurrent or idempotency conflict | Another writer or a different request owns the key/path. | Inspect current status and fingerprints. Retry only with the same logical payload or create a new operation key. |
| Rebuild failed or cancelled | Candidate generation was not activated. | Confirm the prior active pointer, read the candidate receipt/checkpoint, correct the cause, then re-preview. |
| Export/import denied | Production archive/encryption policy is unresolved or path/scope checks failed. | Keep production exchange disabled. Use the test-only API only inside a disposable test root. |
| Audit store reached its bound | The configured metadata file exceeded its safe limit. | Stop capture, preserve evidence under approved controls, then apply a documented rotation/retention policy. Do not truncate a live record. |

Focused checks:

```bash
uv run --frozen pytest -q tests/observability
uv run --frozen pytest -q tests/security
```

These checks use in-memory state or temporary paths. They do not create a live
audit file for this checkout and do not test outbound telemetry.
