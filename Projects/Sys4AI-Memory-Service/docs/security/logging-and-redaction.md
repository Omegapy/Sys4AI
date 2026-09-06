# Logging and redaction policy

Status: binding security contract; metadata models and temporary-path storage
are implemented and focused-test verified, but live operational capture and
rotation are not configured

The default audit log is local derived state at `.sys4ai/memory/audit/events.jsonl`. Canonical approvals and operation receipts belong under `control_records/memory/`; a runtime log is never permission or approval evidence by itself.

The configuration loader confines the exact index, audit output, and model
caches below the project's local derived-data boundary. The Cognee adapter
sets data, system, cache, and file-log paths before importing the provider.
FastEmbed, Hugging Face, Transformers, and Torch client caches use the configured
project-local model-cache root, normally `.sys4ai/memory/models`. The adapter
restores the caller's environment afterward and rejects reuse of an initialized
runtime for another project or dataset. Separate projects use separate runtime
processes; a loopback model endpoint remains an independently managed service.

## Default event content

Use an allowlisted structured event schema. A routine event may contain timestamp, event ID, operation, sanitized actor/process ID, project/dataset ID, record/source IDs, sensitivity class, policy decision, status, duration, counts, version/configuration fingerprints, safe content hashes, and warning/error codes.

Do not log raw queries, retrieved passages, source text, proposal bodies, prompts, model responses, file contents, credentials, authorization headers, cookies, environment values, stack-frame locals, or full provider request/response bodies by default.

## Redaction rules

1. Redact structured fields before formatting or serialization; do not rely on a later text scrubber alone.
2. Use key-name, value-pattern, and data-class rules. Replace a rejected value with a constant marker and rule ID, not a revealing prefix/suffix.
3. Do not hash secrets or low-entropy personal values with an ordinary digest. Use an approved keyed correlation token when correlation is necessary, or omit the value.
4. Content hashes are permitted for non-secret source integrity. Restrict access when a hash could expose a small or predictable value set.
5. Sanitize exception messages from providers and parsers before returning or logging them.
6. Keep telemetry export off in the local profile. A future exporter requires explicit destination, fields, transport, retention, and credential approval.

## Access, retention, and erasure

Limit local log access to the service operator and process. Rotate safely, but do not select a retention duration until the retention policy is approved. Until then, activation must define an operator-managed bounded local policy or keep durable logging disabled.

Privacy erasure removes prohibited content from every log copy under project control. A retained receipt may identify the event and outcome without preserving erased content. Logs must never be the only source of a required canonical receipt.

## Current implementation boundary

`AuditRecorder`, `OperationAuditRecord`, `RecallTrace`, `MetricsCollector`, and
`JsonlMetadataStore` implement the local metadata-only boundary. Tests cover
allowlisted fields, principal/policy evidence, query-free recall traces,
pre-serialization redaction, private complete-line concurrent appends, path
and symlink rejection, and byte bounds using in-memory or temporary stores.
The recorder accepts every public operation plus the explicit initialization,
operation-status, source/profile registration, configuration, permission, and
telemetry control actions; unknown administrative names fail closed.

`MemoryService` wraps all public operations and initialization
preview/apply/status with audit capture in focused tests. The remaining
control-plane actions must call the recorder from their governed workflows.
Built-in recall records actual selected channels, per-channel candidate counts,
filter stages, ranking/dedup/budget stages, returned source IDs, and omissions.

Local capture is disabled unless the embedding service explicitly enables it
and supplies the configured derived-root store. Telemetry export is rejected.
No production retention or rotation duration is approved, so operators must
not enable an unbounded durable log.
