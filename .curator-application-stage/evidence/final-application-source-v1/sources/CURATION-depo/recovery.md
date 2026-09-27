# Exact operation recovery

Recover the original operation through its existing owner. Never delete a pending
journal, invent an original request, recreate a grant from a summary, or restore
old bytes over later human edits.

The Broker has closed recovery pairs:

| Original operation | Recovery operation | Owning journal |
| --- | --- | --- |
| `memory.publish` | `memory.recover` | Existing memory transaction journal |
| `ontology.publish` | `ontology.recover` | Existing ontology intent and recovery records |
| `integration.apply` | `integration.recover` | `control_records/curator/integration/<operation-id>.json` |

The private Curator record keeps the original operation ID, grant, nonce and
payload digest. `GrantStore.resume_recovery` validates a fresh recovery grant
without changing the actual tool name, callback identity, payload or scope. Its
`recovery_of` record links the original operation and grant; earlier recovery
grants remain in `recovery_history`. Record-size limits retain their existing
bounds. Reaching a limit holds the operation without dropping history.

The trusted accepted request selects the original payload digest and the exact
owner journal. The recovery grant retains the owner, project, branch, actor,
canonical Task identity, execution generation and assignment. The current
transport and canonical owner authenticate a fresh load incarnation. An old
callback cannot act through a resumed instance. Unknown recovery pairs, changed
original payloads, another owner or an absent partial operation are rejected
before owner dispatch.

Owner grants remain separate from the Broker grant. Memory recovery receives an
independently selected memory grant for `recover` and the original memory payload;
ontology receives its exact original reviewed publication/preview grant. Their
existing helpers check source, canonical pre/post bytes, lock-time state and
history. The Broker examines the nested owner result, retains the raw outcome and
records completion only for a recognized committed result.

An integration retry binds the same accepted candidate, paths, source inputs,
review digest, execution, branch, commit, tree and index bytes. The journal keeps
bounded exact predecessor bytes for repeated actual edit classification and records each committed
boundary. Recovery accepts only each original before or selected after digest;
unknown content remains visible and stops recovery. The Broker derives actual changed-byte coverage from each original predecessor
and candidate. Declared ranges cannot hide other edits, and insertions at section
boundaries include both neighbors. Protected or mixed edits require their own
authority. Final validation rechecks selected owner checks, exact Git version and
exact integrated bytes. Commit, push and merge are
separate owner actions, absent from the local integration adapter.

A consumed exact request can return its existing receipt only while the current
post-state and trusted bindings still match. It does not repeat canonical writes.
A different request cannot use the completed operation ID to create new work.
Legacy `resume_original` retains its same-operation behavior and validation.

The executable tests use real disposable owner helpers and synthetic transport
frames. They establish recovery behavior under those conditions, not native
runtime confinement, process stopping or end-to-end project readiness.

## Memory product restoration

The closed `memory.reindex` to `memory.reindex_recover` pair uses the actual
`memory_maintenance` owner. The Broker operation ID and the owner-generated
32-character maintenance UUID are separate identities. Recovery selects the
exact pending owner UUID and original `expected_payload_sha256`; the memory
owner grant still authorizes `reindex` against that original owner payload.

A successful restoration returns the owner's `aborted` status. The Broker records
`owner_aborted`, consumes the original private operation and exposes
`products_ready: false` with a separate `memory.reindex` obligation. Exact receipt
replay performs no second restoration. It cannot describe restored old products
as a completed rebuild. A committed rebuild whose required readiness remains
pending likewise retains `owner_reconciled_pending` and its remaining obligation.

Integration checks the complete committed journal and owner-result shapes before
issuing a private grant. This includes predecessor bytes, committed file states,
selected check results and the final snapshot. SHA fields have fixed widths;
the longer possible dirty boolean is reserved. The same bound is checked again
inside the owner before its first target replacement. Both existing 2,000,000-byte
file limits remain unchanged; an oversized zero-effect request creates no grant
or original journal.

## Application pause and resume

Trusted bootstrap selects `application_controls=True` and pins the entire current
application helper package. Legacy Broker construction retains its prior defaults.
The application controller persists its pause state in the selected private Broker
directory before requesting interruption through the actual native pool. It keeps
the controller and current canonical manager available for reconciliation.

Interruption acknowledgment is a request, not stopped-process evidence. Missing
or failed interruption results remain uncertain. New work and pre-pause work
selections are held. Original recovery, bounded evidence return and current owner
observations remain available; existing Task stop/reconnect events retain their
own canonical helper and authenticated callback route.

Resume validates the exact pause operation and current Task owner before grant
issuance, then rechecks immediately before changing the control record. Every
selected child needs its native pool's exact release evidence. Unresolved private
owner operations, a quarantined/closed pool or an expired work deadline hold the
resume. Old work operation IDs remain revoked afterward; a fresh accepted work
selection is required. Task lifecycle and original-work prerequisite checks are
separate from reopening Curator dispatch.
