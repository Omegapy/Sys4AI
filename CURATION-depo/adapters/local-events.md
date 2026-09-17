# Local delivery and snapshot interfaces

These standard-library modules provide inactive deterministic capability for
TASK-014 through TASK-018. Distribution creates no hook, scheduler, service,
Task, model session or knowledge record. A selected runtime must pass the
separate policy, owner and confinement gates before using these interfaces.
The Python functions are callable interfaces; no CLI or runtime route is added
by this package. PHASE-004 integrated acceptance remains behind PHASE-003.

## Events and durable transport

`curator_events.make_event(context, kind, operation_id, payload, created_at=...)`
constructs the strict version 1 envelope. Context binds the project, repository,
canonical coordination root, selected branch, snapshot, policy hash and source
hash. Retain the original operation ID across retries and follow-through.
`causal_parent` records the originating event when a later delivery is caused by
it. Human and agent commits use the same `commit_signal` interface; author names
and commit messages are not execution instructions or acceptance evidence.

| Kind | Bounded payload | Meaning |
| --- | --- | --- |
| `manual_correction` | `request` owner/path/SHA256 reference | Preserve the exact requested correction. |
| `commit` | Complete `commit` object ID | Candidate signal; relevant delta screening is still required. |
| `accepted_work` | Existing `completion` reference and `effect` | Owner-reported accepted work; independently verify that reference before consequential use. |
| `catch_up` | `previous_commit` or null, and current `commit` | Missed-hook endpoints; compute bounded local differences and ancestry. |
| `dependency_due` | Selected `check_id` and `due_at` | A due check can be recorded without a commit. |
| `stale_product` | `product_id`, existing `owner`, `input_sha256` | Route an existing product to owner maintenance. |

`catch_up_signal` returns no event when endpoints match. Hook integration, if
later selected, supplies bounded IDs to transport and exits. It must preserve
existing hook managers and cannot analyze the repository, invoke a model, edit
content or publish Git state. No hook installer is included here.

An event is at most 32,768 UTF-8 bytes, with at most 50 source references.
Opaque IDs use at most 128 ASCII characters; branches use at most 1,024 UTF-8
bytes; evidence paths use at most 2,048 UTF-8 bytes. References contain only an
owner, relative path and SHA256. Raw requests, commands and credentials are not
embedded in the envelope. The corresponding JSON schema documents structure;
Python also checks byte limits, canonical paths and timezone-bearing timestamps.

`DeliveryQueue(root, project_id, repository_id)` binds an existing canonical
local root. It writes only these selected transport paths:

- `control_records/curator/events/<event_id>.json`: immutable envelopes.
- `control_records/curator/operations/deliveries/<event_id>/<revision>.json`:
  immutable delivery receipts.
- `control_records/curator/cursors/delivery-<consumer_branch_digest>/`:
  immutable cursor revisions and an atomically replaced `current.json` pointer.
- `control_records/curator/.delivery.lock`: cooperative local writer lock.

`enqueue` accepts an exact duplicate and rejects changed bytes under the same
ID. `record_delivery` uses the expected prior receipt digest and immutable
receipt ID; an exact retry returns the original receipt. Statuses are `pending`,
`delivered`, `held` and `consumed`. Consumed deliveries need an attributable owner
reference and cannot be reopened. A receipt does not declare a Task complete or
manufacture a canonical publication outcome.

`advance_cursor(consumer, branch, expected_sha256, event_id)` binds a committed
event and writes its revision before its pointer. `cursor` reconstructs the
validated journal and reports `recovery_pending` after an interrupted pointer
replacement. Retrying the same operation repairs the pointer. A stale request,
missing revision, changed record or branch mismatch fails closed. Cursors never
hide pending corrections from `status`.

Publication writes and fsyncs a private temporary file, atomically replaces the
selected destination under the lock, then fsyncs its directory. Unpublished
`.pending-*` files do not count as events and are not deleted by read-only status.
Event and journal scans hold above 5,000 records; each stored record is bounded
at 40,000 bytes. Corrupt or unknown records hold instead of being silently
skipped. Reads reject symlinked directories and special or multiply linked
records. Busy transport returns a retryable `transport_busy` error.

Status and cursor reads create nothing. Cache cleanup under `.sys4ai/curator/`
cannot erase these durable records. This local protocol assumes a selected
cooperative owner; it does not establish hostile-process confinement, distributed
locking, cross-owner atomicity or cross-system exactly-once execution. Unsupported
multi-clone ownership remains held by the runtime owner.

## Local Git observations

`LocalGit(root, executable, executable_sha256)` uses a selected absolute local
Git executable and exact repository top-level root. `head`, `is_ancestor`,
`changes` and `snapshot` read local state. Object IDs must be complete; all
arguments are passed directly without a shell. Git pathname outputs are
NUL-delimited and retained as `path_b64`, including tabs, newlines and non-UTF-8
path bytes. Repository identity binds the selected root and common Git directory
paths plus their device/inode identities. Relocation needs revalidation.

The reader excludes inherited Git configuration overrides and global/system
configuration; disables optional writes, lazy fetching, network protocols,
maintenance, hooks and fsmonitor; requests no external diff or text conversion;
and uses only metadata, committed-tree and pathname-listing Git commands.
Worktree contents are hashed as raw bytes by Python, so clean/smudge/process
filters cannot execute, including filters configured after construction. It never installs a hook,
changes configuration, fetches, commits, resets, checks out, stages or pushes.
Local repository configuration is still untrusted input. Runtime confinement
and exclusive ownership remain necessary against concurrent hostile changes.

Each Git command has a selected limit of 1,000,000 output bytes and 10 seconds by
default; allowed ranges are 1,024–8,000,000 bytes and 1–60 seconds. Captured stdout
and stderr share the byte bound. All raw worktree contents share one additional byte
bound, with at most 500 path entries, 32 path components and 128 retained
descriptors. These limits fail closed when reached. Oversized results hold; they are not truncated and called complete.
Snapshots bind HEAD, committed tree, index metadata, raw tracked/untracked file
hashes and executable modes. The reader computes Git blob identities directly
without content filters. Newline conversion can therefore conservatively report
a raw-byte delta that Git porcelain would normalize. `source_sha256` binds the
committed tree, raw worktree digest, `index_sha256` and
`index_identity_sha256`. The index hashes bind its complete raw bytes and exact
file identity through retained no-follow descriptors. An index-only content,
flag or file replacement changes snapshot and source identity even when HEAD,
worktree bytes, normalized stage listings and dirty status are unchanged. This
includes intent-to-add versus staged empty files. Index refreshes can invalidate
a snapshot; deterministic relevance screening still governs further work.
Index bytes have a separate selected byte bound, and split-index dependencies
are explicitly held until a bounded dependency adapter is selected. Repeated HEAD/index/tree/pathname checks
and descriptor-relative no-follow reads detect changes during observation.
Directory and file identities stay bound throughout hashing; final revalidation
also runs after content descriptors close while parent descriptors remain open.
Snapshot reads are observations, not atomic locks against later source changes.
An integration owner must reobserve and compare the exact snapshot before use.

Detached HEAD, unavailable/replaced roots, missing Git objects, unsupported
submodules or symlinks, unsafe files or exceeded bounds hold. An
unavailable external volume is never interpreted as deletion. Disposable Git
fixtures exercise rebase, squash, force update, branch switch, rename, deletion
and configured-execution canaries; these tests do not modify real repositories.

## Checkpoints, preflight and causality

`empty_checkpoint`, `advance_checkpoint` and `recompute_obligations` are pure
functions. The selected owner persists their results through its checked cursor
or operation route; this package creates no competing checkpoint writer.
Observed, assessed, integrated and reconciled records remain separate on one
branch. Every later stage needs its exact predecessor record hash and current observed
context. A record includes `predecessor_sha256`, which is null only for the
observed stage. `current_stages` checks the complete predecessor chain. Changing
an upstream obligation or evidence record makes retained successors historical,
even with unchanged source context; metrics count only a complete current chain.
An exact unchanged transition remains idempotent. Unbound earlier staged record
editions fail closed rather than acquiring fabricated predecessor evidence. Required obligations cannot disappear between stages. Reconciliation
requires all integrated obligations to be explicitly satisfied. Evidence paths
are supplied owner observations, not independently verified publication proofs.
Feature-branch checkpoints cannot become another branch's current knowledge.

Git ancestry and changed paths distinguish forward history, rewritten history,
branch switches, rename/copy, deletion and content change obligations. A rebase,
squash or force update can preserve content while invalidating ancestry evidence.
A new observation retains historical assessed/integrated/reconciled records but
makes their old context visibly stale. Assessment alone advances neither
integration nor reconciliation.

`preflight` first checks project/policy/branch/source identity, owner availability
and recovery state, then screens known cache/control churn, relevant paths,
existing ownership classification, selected due checks and pending work.
Each preflight accepts at most 5,000 events, 500 deltas/due checks/path patterns,
and 500 source files totaling 8,000,000 bytes. Unknown or mixed classes hold. Commit/catch-up signals alone do not trigger
assessment without relevant changes or other pending/due work. Stale product
signals route to the existing memory or ontology maintenance owner. `ready` is a
screening result and grants no authority. No function here invokes a model,
creates a Task, publishes knowledge or rewrites project content; returned counters
are zero and describe this deterministic invocation only.

`coalesce` produces stable results for duplicate and reordered deliveries.
`obligation_key` uses the original operation, project/repository/root/branch,
policy, canonical source hash and obligation type. The observation snapshot stays
in the event but is excluded from this key so a derivative-only snapshot change
does not create a second obligation for unchanged canonical sources.
`obligations_for` retains documentation and knowledge assessment after an
accepted repair. Accepted knowledge can require derivative follow-through;
completed derivative work creates no further obligation. These signals never
assert that knowledge publication is warranted.

`reduce_outcomes` accepts attributable owner observations, deduplicates attempts,
and holds conflicting same-attempt or satisfied-output claims. Multiple input
hashes under one key also hold; an earlier satisfied input cannot supply a
current output for a different input. Exact duplicate observations collapse,
while every distinct conflicting observation and unresolved finding is retained
in stable order. Mixed input versions require explicit owner reconciliation;
the reducer does not infer which version is current. Finite selected
attempt/time/byte limits and repeated unchanged failures or outputs stop further
expansion; unresolved finding hashes remain in the stopping result. A new
canonical source hash gives a distinct applicability key. No outcome reducer
executes an owner operation or promises exactly-once external publication.

`metrics` derives bounded event, outcome and current-checkpoint counts from
supplied records. It has no mutable metric ledger, implicit refresh, lifecycle
ownership or ability to create work. Source freshness is the caller's supplied
observation boundary.
