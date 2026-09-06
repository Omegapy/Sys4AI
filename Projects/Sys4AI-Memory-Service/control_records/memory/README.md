# Memory control-record boundary

Status: canonical path and local single-review policy approved

For the human and agent handoff, follow
[memory readiness and activation](../../docs/operations/memory-readiness-and-activation.md).
These control files and an installed package do not establish exact or semantic
readiness. Inspect this project's configuration, matching initialization
receipt and current workflow evidence. If semantic memory is disabled or
unverified, report that state and Cognee's observed activation state, then ask
whether to activate when the user has not already decided. Record the choice
and the next action in the normal project handoff; do not alter runtime success
receipts or repeat an unchanged decision during unrelated work.

`control_records/memory/` is the canonical root for durable memory-control evidence in this product. The current permission mapping is [permissions.json](permissions.json): one human `local-owner` reviewer, exactly one approval, and no proposal self-approval. The mapping grants no delete, administer, rebuild, or non-fixture destructive authority.

## Reserved record classes

| Relative path | Intended record class |
|---|---|
| `proposals/` | Typed write proposals and their validation/policy disposition |
| `approvals/` | Approval or rejection records that reference proposals and canonical permission evidence |
| `deletion_receipts/` | Scoped deletion and privacy-erasure receipts without erased content |
| `rebuild_receipts/` | Generation build, validation, activation, failure, and rollback evidence |
| `migrations/` | Versioned schema/profile/provider migration decisions and receipts |
| `incidents/` | Sanitized security, privacy, integrity, and availability incident records |

These child paths are reserved contract locations. Their absence means no record of that class exists; software must not create them merely by loading configuration.

## Review boundary

1. A proposal validates against its current public schema and records source, scope, type, target, trust, authority, sensitivity, provenance, and requested durability.
2. The write-policy engine returns reject, session-only, episodic, or stage. Session and episodic retention are bounded by the approved 72-hour and 365-day policy.
3. A staged proposal cannot approve itself. The service rereads a current canonical permission record for the exact reviewer, project, proposal type, target, and operation.
4. An approval/rejection record references the proposal digest, policy/schema versions, reviewer identity, canonical permission locator and revision, decision, rationale summary, evidence, and timestamp.
5. Approval does not directly mutate Cognee. Promotion uses the normal project workflow to create a reviewed canonical source change.
6. Synchronization begins from that canonical source and records the resulting source revision and generation.

`MEM-OQ-006` and plan `Q-006` are resolved for the local release by the canonical `permissions.json` document. A general agent is never an approver merely because it can create a proposal or retrieve an old approval. The service rereads that document for every authorization decision, and the staging layer independently denies an approving reviewer whose identity equals the proposal requester.

## Receipt rules

Receipts are schema-valid, append-only evidence of an observed operation. They include stable IDs, scope, sanitized actor/process identity, requested and effective operation, policy/permission/schema/configuration versions, source/record/generation identifiers, safe hashes, counts, timestamps, outcome, warnings, and previous/next generation where applicable.

Receipts exclude credentials, raw restricted content, erased content, provider request/response bodies, private chain-of-thought, and unbounded transcripts. A receipt cannot substitute for the current canonical permission or source record.

## Lifecycle and versioning

Record schemas use independent semantic versions. Optional additions may use a minor version; required-field or meaning changes require a major version and migration. Supersession preserves links and current/history distinction. Privacy deletion uses a tombstone or receipt that proves scope and outcome without retaining prohibited content.

Retention is 72 hours for session records and 365 days for episodic records, with expiry purge and no silent extension. Provider-neutral packages use deterministic ZIP JSON/JSONL members and an `age` X25519 envelope; unencrypted candidates remain disposable-test-only.
