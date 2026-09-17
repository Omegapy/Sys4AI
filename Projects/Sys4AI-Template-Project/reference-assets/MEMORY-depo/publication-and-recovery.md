# Publication and recovery contract

The caller supplies a reviewed operation payload and a separate short-lived
project grant. Neither a role title, native actor string, note, Task completion,
nor user-supplied grant text alone establishes authority. The helper compares
the grant with current project configuration, governance files and, when
applicable, the installed canonical Task and role interfaces.

## Reviewed operation

The JSON payload has `operation_id`, `operation`, `reason`, and `changes`.
An operation ID is a stable `MEMOP-` identifier. Each change has an exact
relative `path`, nullable `expected_sha256`, exact reviewed Markdown `content`,
and `reviewed_record_sha256`. The payload digest is SHA256 of UTF-8 JSON
serialized with sorted keys, two-space indentation, `ensure_ascii=False`,
and one trailing newline. `memory_core.json_bytes` supplies this representation.
The record digest always covers the actual raw Markdown bytes.

`publish` activates one new or existing draft. It cannot silently edit an
active note. `supersede` publishes one successor and marks its named active
predecessors superseded. Every link and reason must agree. `retract` retains
the original body and states the reason. `redact` requires explicit privacy
authority, preserves stable identity and chronology, records the precise
reason, and removes corresponding managed historical copies where necessary.
Automatic schema/profile migrations are unsupported.

## Grant and current ownership

The grant has `schema_version: 1`, `grant_id`, `project_id`, `actor_id`,
`actor_kind`, `operation`, `payload_sha256`, `config_sha256`, `scope`,
`native_receipt`, `observed_at`, `expires_at`, `task`, `reviewed_records`, and
`privacy_redaction`. Each reviewed record binds `path`, `sha256`, and nullable
`expected_sha256`. Scope is a list of exact path prefixes; wildcards are not
permission expansion. Native status uses the actual normalized result of
`collaboration.list_agents`, naming the caller as `running`. Grants last no
more than five minutes and cannot precede their observed native evidence.

A Director's current `memory.yaml` binding names its native actor, bounded
scope, and actual `SOUL.md`, `AGENTS.md`, `ROLE.md` path/digest pairs. Those
governing bytes must still match. Empty starters contain no publisher binding.
An unreconciled Task manager with overlapping assigned writes blocks a
competing Director publication, including paused or uncertain ownership.

A manager grant binds the current canonical Task path/digest, Task ID,
execution ID, generation and manager assignment ID. The installed Task helper
validates the record read-only. Its current writer, active stage, real native
launch receipt, role reads and fresh role catalog must agree. The assigned
`fit.writes` must contain every requested write. Activation alone does not
grant arbitrary memory scope. A stale generation, child actor, missing role
pair, changed Task or scope mismatch fails before canonical publication.

These are cooperative process/tool checks, not cryptographic authentication
or an OS sandbox. They cannot prove the provenance of a forged local receipt.
The Director must save actual tool evidence and must not expose alternate
backend write tools as a route around canonical controls.

## Commit boundaries

Writers share a nonblocking POSIX advisory lock at
`.sys4ai/memory/maintenance/memory.lock`. The lock is never deleted to break
an active owner. Validation precedes a journaled change; under the lock it is
repeated against current config, source versions and expected record bytes.

An accepted intent is durably written to
`.sys4ai/memory/maintenance/transactions/<operation-id>.json`. It retains the
payload digest, exact accepted post-content, original bytes/digests for
ordinary correction, reason and publisher attribution. Privacy redaction
does not persist the sensitive original. This journal is durable accepted
work and is never treated as a rebuildable index.

Each record is written to a temporary sibling, flushed, compared again with
the expected current version, atomically replaced and followed by directory
fsync and a post-write digest check. All directories are opened without
following symlinks; inode and path checks run at the replacement boundary.
Human editors should coordinate through the same lock. An unrelated process
that ignores it can race a filesystem rename; this implementation reports
observed pre/post conflicts and does not claim an OS-level compare-and-swap.

Only after every accepted post-hash is present does the journal receive its
durable complete receipt. Failures report the actual committed, pending, or
conflicting records. A crash before journal creation leaves no accepted
intent. A crash after it leaves recoverable exact accepted work. A crash after
record replacement but before the receipt is resolved from current hashes.
Pending canonical transactions suspend shared recall so partial supersession
cannot become an unqualified current conclusion.

## Retry, correction and recovery

Retry the same operation ID with the same payload. A different payload under
that identity is a conflict. Committed records are recognized by their exact
post-hash and are not written again. A completed receipt is returned only
while its actual records still match; later human edits cannot be overwritten
by replaying historical acceptance.

`recover` requires a new current grant for the original exact payload digest.
It accepts only its memory transaction journal and rechecks current authority,
evidence and scope. Unknown bytes, a changed journal, stale publisher or active
lock blocks recovery. Recovery never reads memory as Task instructions, writes
a Task/role index, replays an event, reopens terminal work, or relaunches agents.

Privacy redaction is scoped to selected canonical records and their managed
transaction copies, with a durable hash/reason receipt. It does not search or
purge unrelated source files, Git history, external backups, or other projects.
No retention rule requires keeping credentials. If history was explicitly
redacted, it cannot later be replayed to restore the removed content.

The record/config helper and transaction tests establish deterministic local
behavior. Vendor backend, actual native ownership and complete project delivery
need their own observed integration evidence.


## Evidence retention and current readiness

New `verified_outcome` claims require an actually observed receipt with explicit
current applicability, exact live artifact versions and reviewed retained bytes
under the governed evidence paths. Record schema v1 remains unchanged; the
receipt's optional per-artifact `retained_path` extends its existing format.
Retaining an archive is a separately scoped evidence write, not an implicit
publication side effect. Reads never rewrite receipts, refresh hashes or create
archives. Existing legacy receipts remain readable with explicit durability and
historical/current applicability limitations. Missing or tampered historical
proof cannot become a verified-current result. See the adopted memory skill's
`references/evidence-and-lifecycle.md` for the exact compatible reader contract.

Canonical transaction completion and current derived readiness have distinct
meanings. Publication/capture return the original exact commit receipt plus a
read-only `current_readiness` observation. A new record, lifecycle change or
configuration change can invalidate a selected projection/index. The result
reports the precise pending component and owning maintenance route; no publication
grant silently authorizes reindex, recertification, ontology associations or a
runtime operation. Exact retries preserve canonical idempotence and reevaluate
current readiness. A prior receipt retains historical provenance after its inputs
change and cannot be reused as current operational success.

For unchanged legacy receipts, a reviewed historical-only proof companion may be
retained at `Verification/project-memory/evidence/verification-<receipt-sha256>.json`.
It binds the exact original receipt path/hash and the unchanged ordered artifact
path/hash list to permitted retained copies. It provides a proof locator, not a
new execution receipt or current claim. The original record, receipt and canonical
transaction journal retain their original bytes until an explicitly reviewed
ordinary lifecycle operation changes the record's lifecycle fields. The original
claim, evidence identities and predecessor body remain preserved by supersession.

## Native Curator grant version 2

Grant v1, record/config v1 and existing journals retain their meanings. Grant v2
adds `controller_origin: curator` and a strict `broker_binding` for the memory
owner, actual live call, selected native protocol, charter and policy. The actor
is the current confirmed manager of a version-2 Curator execution. It is never
relabeled Director. Current Task bytes, generation, role reads, assigned paths,
source evidence, privacy, exact payload and the five-minute freshness limit
remain independently checked under the existing owner transactions.

A serialized call or ordinary CLI invocation cannot authorize v2 publication.
The actual protected transport must install its process-local caller context
for every owner check, including recovery. Grants retain their original raw
file digests and journal references. Recovery uses the original owner operation
and preserves later edits. Automatic capture preferences remain unchanged;
Curator's broker derives automatic versus explicit origin from trusted accepted
run metadata, and explicit correction authority is independently selected.
