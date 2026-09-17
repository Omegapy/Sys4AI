# Canonical Task orchestration

This contract extends the existing `task_state.py` and response transaction.
The Task ledger remains the only execution record. Native spawning and
messaging remain agent operations; no helper starts an agent or installs a
dependency. Exact event fields and implemented examples are checked against
the CLI before adoption.

## Storage and identities

New workflow Tasks use `orchestration_enabled: true` to select schema 2: the
schema-1 fields plus `orchestration`. Omitting the flag retains schema 1 for
legacy API compatibility; future execution workflow instructions always enable it. Historical
schema-1 records remain strictly readable with their historical semantics.
Read-only routes never upgrade them. Explicit selected-record upgrade previews
the current revision and digest, retains original bytes, and preserves identity
and responses. Unknown versions and unknown fields fail closed.

The orchestration object contains a version, execution ID, generation, stage,
bootstrap actor, designated manager assignment, current writer, inspected source
references, subtasks, assignments, artifact versions, candidates, reviews,
conflicts, syntheses, acceptances, implementation results, blockers and concise
events. A new unassigned record contains no invented native identity. Internal
subtasks and assignments are not additional top-level Tasks.

Each subtask baseline contains its objective, project context, requirement IDs,
criteria, dependencies, constraints, protected state, allowed actions, write
scope, one category and its rationale, and whether authorized implementation is
required. A content digest binds the material baseline. Dependencies resolve,
are acyclic, and complete before dependent dispatch. Categories are `generic`,
`complex` and `extra-complex`; decomposition is a separate decision.

Each assignment contains its function, subtask, exact role pair and digests,
fresh catalog/fit evidence, required capabilities, baseline, perspective,
permitted writes, stopping condition, runtime capability evidence, identity
guarantee, and eventual native receipt. Role names and native IDs are distinct.
Actual native IDs originate in tool receipts. Role pairs in `Roles/` determine
eligibility; their generated index is navigation. Historical role hashes retain
the originally inspected provenance even if the current role later changes.

The active directory is spelled exactly `Roles/`, including on case-insensitive
hosts. New reservations require that directory, its current catalog and the
matching capitalized pair paths. Structural validation retains earlier `roles/`
paths as immutable historical provenance; it neither renames stored references
nor treats them as a fresh selection. A role-path change is not a context-only
rebind: reconcile the prior owners and use the existing replacement protocol
for a newly loaded pair. Worker scopes cannot include the role root or its
index through trailing slashes, normalized path segments or case aliases.

## Writer and publication protocol

`task_state.py orchestrate SELECTOR --expected-revision N --payload-file FILE`
applies one typed event through the existing catalog/task locks and response
transaction. The payload includes event ID, actor, execution generation, kind
and kind-specific data, plus the normal concise response fields. Unknown keys,
unsafe paths, duplicate events, stale actors and stale revisions are rejected.

Bootstrap reserves one manager assignment before native launch. It records the
actual receipt before activating the manager. Activation transfers canonical
writer ownership to the manager and ends bootstrap write authority. Ordinary
response and lifecycle routes also check the designated writer and generation.
Workers, reviewers and seniors return evidence without writing canonical state
or promoting themselves through root guidance.

Native launch and file publication are separate transactions. An uncertain
launch retains the original reservation and blocks a blind second launch.
Reconcile that assignment against native status and known changes. Repeated
intake reconnects only a confirmed matching live execution. Actor/generation
checks enforce a cooperative protocol; they are not OS authentication,
filesystem isolation or cross-system exactly-once execution.

| Event family | Required gate and rejection case |
| --- | --- |
| Manager reservation, receipt, activation | Exactly one reservation and matching native receipt; reject duplicate owners, stale generations and uncertain relaunch. |
| Subtask definition or revision | Complete baseline, valid dependencies and category; reject cycles and reclassification that bypasses an unresolved gate. |
| Assignment reservation and receipt | Fresh valid role fit, native capability, exact settings and exclusive write scope; reject duplicate generic workers, shared reviewers or competing implementers. |
| Assignment reconciliation | Current native observation and known changes for the original ID; reject timestamp-only stopping and replacement of unresolved owners. |
| Candidate or generic result | Exact producer, current baseline and separate artifact version; reject missing solvers or wrong producers. |
| Review | Assigned reviewer, exact current candidate and baseline; reject self-review, shared reviewers, stale passes and unsupported outcomes. |
| Conflict | Exact inputs, shared explanation, evidence, recipients and targeted next change or bounded blocker; reject omitted originating solvers. |
| Synthesis | Distinct senior and every eligible current candidate; extra-complex requires every current reviewer pass. Reject mixed baselines, incomplete sets and unresolved core commitments. |
| Manager acceptance | Exact coherent current proposal returned to its manager; reject another actor or changed inputs. |
| Implementation result | One distinct dedicated implementer targeting the authorized accepted multi-solution proposal; reject proposal-only completion. |
| Subtask verification and execution finish | Manager artifact inspection, every criterion and integrated evidence; reject unresolved dependencies or ownership. |
| Stop and recovery | Stop dispatch, reconcile assignments, then revoke/replace or resume; reject blind replacement and silent setting changes. |

## Artifacts, review and implementation

Bounded regular evidence files live in the selected Task's
`artifacts/orchestration/`. Register unique version IDs and SHA-256 digests;
preserve prior versions and reject traversal, symlinks, collisions and duplicate
IDs. Artifact copies and receipts are evidence, not a second ledger. Solver
candidates have separate writable paths.

Reread referenced bytes before accepting results. A byte edit, material baseline
revision or required-input change invalidates dependent reviews, synthesis,
acceptance and implementation targets. Retain old records as history. A current
candidate and any required re-review establish eligibility again. A matching
name or path never preserves a pass by itself.

Generic work has exactly one worker, including authorized implementation;
corrections return to that worker. Multi-solution work has at least two distinct
solvers with the same complete baseline and different suitable perspectives,
then one distinct senior. Extra-complex work has one independent reviewer per
solver. Every required current candidate needs its assigned reviewer pass.
Complex work adds no mandatory reviewer stage.

Return the same versioned synthesis-conflict explanation to all originating
solvers. Revised or explicitly revalidated candidates retain solver attribution.
Extra-complex candidates return through their reviewers before further fusion.
The senior records retained contributions, justified omissions, assumptions,
interfaces and dispositions for complementary contributions, terminology,
scope alternatives, evidence disagreements and mutually exclusive commitments.
Contradictory requirements need a bounded user decision. Voting, concatenation
or hidden discarded opposition cannot establish a coherent solution. Only the
manager accepts the returned proposal.

For accepted multi-solution work requiring authorized changes, exactly one
dedicated implementation child performs them. It differs from manager,
solvers, reviewers and senior. Analysis-only work finishes at the accepted
deliverable; generic work retains its own worker. Manager verification checks
actual outputs, interfaces, main-Task criteria and integration before completion.

## Native settings, context and capacity

Before dispatch, check current native APIs and applicable instructions. Record
observed exact model/effort equality or a verified effective inheritance
guarantee. Prompt assertions and unverified aliases are insufficient. Seniority
does not change settings; no user-configuration rewrite supplies an exception.

Context independence is a separate gate. A full-history fork is eligible only
when its supplied history excludes sibling candidate drafts. The verified
queued protocol returns only paths, hashes and status and defers candidate reads
until every initial solver has been dispatched. Another isolation mechanism
needs its own supported runtime guarantee. Shared-filesystem instructions do
not constitute a security sandbox.

Use observed capacity, with no product concurrency constant. Queue logical
assignments while retaining all required distinct agents and gates. Count
reserved, active and uncertain owners and serialize overlapping writes.
Completion messages alone do not prove capacity release: observe native status
and accepted new dispatch. The prerequisite probe observed this reuse and
same-ID follow-up without an explicit close API.

## Stop, recovery and compatibility

Pause, cancel, replacement and setting changes stop new dependent dispatch.
Request native interruption, inspect actual statuses and known edits, and retain
unconfirmed ownership as a blocker. Timestamps never prove stopping. Revoke an
old manager only after required team reconciliation. Replacement begins a new
generation and rejects delayed results from the former one.

Continue loops only for a targeted revision, material new evidence or a new
hypothesis. Unchanged failure, irreducible conflict, unavailable capability and
exhausted resources produce a non-complete blocker. Resource pressure cannot
remove required agents, lower criteria or auto-pass review. Optional improvements
stop after mandatory criteria are met.

Keep strict validation, lock order, revision checks, append-only responses,
transaction intents and partial-publication recovery. After a committed write,
repair only pending projections; never blindly replay the event. An upgrade
retains original bytes and stable identity without inventing active agents.

Root automatic intake and 30-day `close-old-task` policy remain separate from
generic source/Template policy. Root age closure reconciles known managers and
unresolved write owners first. Read-only routes and unrelated prompts never
create, age, dispatch, migrate, reindex or repair.

## Verification boundary

Fixtures cover ownership, schemas, version invalidation, category paths and
interrupted publication. Negative controls show a gate's observable effect.
Native receipts separately establish topology, role reads, settings, context
and controls. Reports distinguish inspection, deterministic tests, runtime
observations and end-to-end delivery. Keep concise decisions and evidence;
exclude credentials, hidden reasoning and full transcripts.

## Implemented CLI and exact payloads

Run the installed helper with its owning project root. Source tests also run
directly from `SKILLS-depo/agent-task/tests`. All event keys below are required;
nullable fields must be explicit `null`. Unknown keys fail validation. IDs are
stable bounded strings matching `[A-Za-z][A-Za-z0-9_-]{0,95}`. Native IDs are
separate canonical tool paths, such as `/root/task_manager/solver_a`.

```sh
python .agents/skills/agent-task/scripts/task_state.py --help
python .agents/skills/agent-task/scripts/task_state.py --project-root /absolute/project new --payload-file new.json
python .agents/skills/agent-task/scripts/task_state.py --project-root /absolute/project orchestrate TASK_ID --expected-revision 1 --payload-file reserve.json
python .agents/skills/agent-task/scripts/task_state.py --project-root /absolute/project upgrade-preview TASK_ID
python .agents/skills/agent-task/scripts/task_state.py --project-root /absolute/project upgrade-orchestration TASK_ID --expected-revision REVISION --payload-file upgrade.json
```

The exact new-record payload can be:

```json
{"name":"Bounded delivery","description":"Deliver the authorized fixture.","definition_of_done":["Output inspected."],"orchestration_enabled":true}
```

Every `orchestrate` payload is `{ "event": EVENT, "response": RESPONSE }`.
`EVENT` has exactly `event_id`, `actor`, `execution_id`, `generation`, `kind`,
and `data`. The reservation chooses the first execution ID and generation 1.
Subsequent calls retain that binding and read the latest canonical revision.
`RESPONSE` uses the existing eight required response fields; it does not carry
an independent actor or secretly change lifecycle state. Ordinary schema-2
response/lifecycle commands add `actor`, `execution_id`, and `generation` to
the normal response payload. They receive the same writer and completion gates.
A `status_after` field cannot bypass them.

| Event kind | Exact `data` fields |
| --- | --- |
| `manager.reserve` | `assignment_id`, `role`, `fit`, `runtime`, `settings`, `context`, `source_refs`, `authority`, `bootstrap_receipt` |
| `manager.receipt` | `assignment_id`, `receipt` |
| `manager.activate` | `assignment_id`, `role_reads` |
| `manager.reconnect` | `assignment_id`, `receipt` |
| `subtask.define` | `subtask_id`, `baseline` |
| `subtask.revise` | `subtask_id`, `baseline`, `reason` |
| `assignment.reserve` | `assignment_id`, `subtask_id`, `slot`, `role`, `fit`, `runtime`, `settings`, `context` |
| `assignment.receipt` | `assignment_id`, `receipt` |
| `assignment.reads` | `assignment_id`, `role_reads` |
| `assignment.inputs` | `assignment_id`, `role`, `fit`, `runtime`, `context`, `receipt`, `reason` |
| `assignment.observe` | `assignment_id`, `receipt`, `changes` |
| `assignment.uncertain` | `assignment_id`, `reason` |
| `assignment.revoke` | `assignment_id`, `reason` |
| `assignment.resume` | `assignment_id`, `runtime`, `reason` |
| `artifact.register` | `artifact_id`, `assignment_id`, `source_path` |
| `candidate.record` | `candidate_id`, `assignment_id`, `artifact_id`, `baseline`, `round`, `supersedes`, `findings`, `revalidation` |
| `review.record` | `review_id`, `assignment_id`, `candidate_id`, `baseline`, `round`, `outcome`, `findings` |
| `conflict.record` | `conflict_id`, `assignment_id`, `candidate_ids`, `baseline`, `round`, `explanation`, `progress` |
| `conflict.deliver` | `conflict_id`, `solver_slot`, `receipt` |
| `synthesis.record` | `synthesis_id`, `assignment_id`, `candidate_ids`, `review_ids`, `baseline`, `round`, `artifact_id`, `dispositions`, `resolved_conflicts` |
| `acceptance.record` | `acceptance_id`, `synthesis_id`, `inspection` |
| `result.record` | `result_id`, `assignment_id`, `acceptance_id`, `baseline`, `round`, `artifact_ids`, `changes`, `checks`, `limitations` |
| `subtask.verify` | `subtask_id`, `baseline`, `round`, `result_id`, `acceptance_id`, `artifacts`, `criteria`, `inspection` |
| `stop.request` | `reason`, `action` |
| `stop.finish` | `reason` |
| `execution.resume` | `settings`, `reason` |
| `manager.replace` | `reason`, `user_authorized`, `observations` |
| `execution.finish` | `outcome`, `criteria`, `inspection` |
| `block` | `reason`, `next_step` |

An evidence reference has exactly `path` (project-relative) and `sha256`
(lowercase 64-digit digest). Evidence files are regular, bounded to 250,000
bytes, and cannot traverse symlinks. A role is exactly `name`, `agents_path`,
`role_path`, `agents_sha256`, `role_sha256`, and `catalog`; the last is an
evidence reference to the current complete catalog JSON. The live paired role
and current index must agree with that catalog at dispatch. A role-read receipt
has exactly `agents_sha256`, `role_sha256`, and concise `evidence` text.

A fit has exactly `objective`, `capabilities`, `reads`, `writes`, `deliverable`,
`tools`, `skills`, `authority`, `risk`, `stop`, and `rationale`. Capabilities,
paths, tools, and skills are arrays of strings. Settings have exactly `mode`,
`model`, `effort`, and `evidence`: `observed_equal` needs concrete equal strings;
`verified_inheritance` uses explicit null model/effort with current evidence of
the effective inheritance guarantee. Neither mode accepts a prompt's unsupported
identity assertion. Runtime has exactly `tools`, `depth`, `available_slots`, and
`evidence`; the required native names are `spawn_agent`, `list_agents`,
`send_message`, `followup_task`, and `interrupt_agent`. Runtime observations
must justify nesting and a currently available launch slot.

Native receipt normalization preserves the tool and actual returned identity:

```json
{"tool":"collaboration.spawn_agent","result":{"task_name":"/root/task_manager/solver_a"}}
```

```json
{"tool":"collaboration.list_agents","result":{"agents":[{"agent_name":"/root/task_manager/solver_a","agent_status":"completed"}]}}
```

Roster status may also preserve a native `{ "completed": "bounded result" }`
object. Store concise evidence; do not embed transcripts. A same-ID input
handoff has exactly `tool` (`collaboration.send_message` or
`collaboration.followup_task`), `native_id`, `artifact_sha256s`, and `evidence`.
It records the actual sent digest set and recipient, never a fabricated launch.
A `conflict.deliver` receipt instead has exactly `native_id`,
`explanation_sha256`, and `evidence`; its digest binds the identical shared
explanation sent to the originating solver.
Replacement/reopening observations are arrays of `assignment_id`, `receipt`,
and `changes` evidence-reference arrays.

A baseline has exactly `objective`, `requirements`, `inputs`, `dependencies`,
`criteria`, `category`, `rationale`, `reads`, `writes`, `protected`, `authority`,
`implementation_required`, `deliverable`, `stop`, and `slots`. Requirements,
dependencies, criteria, and path lists are string arrays; inputs are evidence
references. A slot has `slot`, `function`, `perspective`, and `solver_slot`;
only a reviewer has a non-null solver slot. Definition/revision publishes the
canonical compact baseline JSON at
`artifacts/orchestration/baseline_<sha256>.json`. Include its exact project-relative
reference in every assigned context. Solver/reviewer/senior writes are confined
to their own `artifacts/orchestration/work/<assignment_id>/`; generic workers
and implementers use only the baseline's authorized project write scope.

Reservation binds assignment baseline, round, slot, and, for implementation,
the exact current acceptance ID. It binds current dependency verification for
every category. Reviewer context includes its assigned current candidate;
senior context includes all current candidates and required passing findings;
implementer context includes the exact accepted proposal. Missing inputs fail
before dispatch. Use `assignment.inputs` after actual same-ID messaging to
rebind compatible existing assignments to a changed baseline or input packet.
Fresh role fit, runtime, unchanged role identity, and every exact current digest
are required. Incompatible function slots require a reconciled new assignment.

For a material same-ID input change, first observe the assignment completed or
stopped. Queue the exact packet with `collaboration.send_message`, which does
not wake an idle agent. Record `assignment.inputs` to validate and bind the
current context, scope, and capacity; only then use `collaboration.followup_task`
to wake it. Stop and reconcile active workers before changing their material
inputs. An unchanged-input continuation uses `assignment.resume` before waking
the same native instance. Observing activity cannot undo revocation or bypass
resume checks, and a still-running stop request remains a stop request.

All planned initial solver receipts must exist before candidate import. For a
revised round, rebind every required solver before importing its candidate.
Conflict obligations survive further material baseline revisions; explain and
deliver every active conflict to all originating solvers, then include those
explanations in their contexts. An unresolved cycle cannot shrink or reclassify
its frozen team. `resolved_conflicts` covers the full active set. Extra-complex
revisions and explicit revalidation receive their assigned current review again.

Synthesis `dispositions` has exactly `retained`, `omitted`, `differences`,
`assumptions`, `interfaces`, `requirements`, `risks`, `verification`, and
`unresolved`. All except differences are string arrays. Differences has exactly
`complementary`, `terminology`, `scope`, `evidence`, and `exclusive`, each with
an explicit disposition. Unresolved commitments prevent acceptance.
Criterion evidence is an array of `{ "criterion": "exact current criterion",
"evidence": "concise direct check" }`, covering each criterion once. Inspection,
changes, and checks are evidence-reference arrays. Artifact IDs refer to immutable
registered versions. Rechecking verification also checks current live changed
files and check receipts; copying an output into an artifact cannot conceal a
later edit to the delivered file. Dependency changes invalidate dependent current
evidence, including generic results.

`execution.finish` records delivered integration only after all subtask gates;
it does not replace the explicit `complete` response and its definition-of-done
evidence. Both recheck current bytes and bindings. Reopening preserves the old
execution and its events; a later reservation archives it in `history` and starts
a new execution. The old manager cannot write into the next generation.

## Unassigned maintenance and committed recovery

An enabled record starts without an execution, writer, or bootstrap. Before
reservation, selected projection/lock/redaction maintenance needs `actor`,
`execution_id: null`, `generation: 0`, and a current native running
`bootstrap_receipt`. It grants no execution ownership. For selected projection
repair the corresponding CLI is:

```sh
python .agents/skills/agent-task/scripts/task_state.py --project-root /absolute/project rebuild-projections TASK_ID --actor /root --generation 0 --bootstrap-receipt bootstrap-roster.json
```

The receipt argument is a project-relative JSON file. After reservation, this
exception ends: only the designated writer with the exact current binding may
repair the selected Task. Blanket repair cannot silently mutate owned records.
Read-only routes perform no repairs. Root-only aging of an unassigned record
uses its separate current intake-host receipt and preserves unset ownership.

Frozen schema-2 transaction intents include exact pre/post canonical digests,
writer/generation/event binding, immutable artifact bytes, and response metadata.
If no publication committed, recovery aborts the orphan intent; otherwise it
finishes the exact existing transaction without replaying the event. Original
handoff actors may finish their own already-frozen publication after ownership
transfers. An unrelated canonical byte edit blocks recovery even at an unchanged
revision. Redaction and lock removal also enforce current ownership; historical
responses remain append-only except the existing explicitly authorized redaction
transaction. Recovery evidence does not authorize arbitrary new work.

Explicit upgrade requires the normal response fields plus `user_authorized`,
`status_reason`, and the preview's `legacy_sha256`. The original schema-1 bytes
are retained under `artifacts/orchestration/legacy-v1-<sha256>.json`. No read,
intake inspection, or catalog rebuild upgrades historical records automatically.

## Optional memory artifacts

The installed memory capability uses the evidence contracts above without
extending this schema. A confirmed manager registers a bounded immutable memory
packet, includes its exact reference in baseline inputs and every initial solver
context, and preserves it for queued dispatch. The memory-side assignment check
validates those bindings. Current-execution drafts and proposals are excluded.
Changed material memory follows existing reconciliation, baseline revision,
conflict and assignment-input gates. A publication receipt is normal evidence;
memory recovery cannot manufacture acceptance or replay committed Task events.
See the [memory integration contract](../../memory/references/task-integration.md)
for packet selection, limits and retrieval behavior.

## Explicit Curator version 2

New Task creation can select `orchestration_enabled: true` and
`orchestration_version: 2` together with exact `controller_origin` and
`native_protocol` bindings. Default creation and every historical record retain
their existing versions. The selected Curator origin binds charter, policy and
canonical project identity; the native protocol binds backend, session, runtime,
schema and profile hashes. Unknown fields and incompatible selections fail.

Version 2 records actual App Server IDs and versioned observations. Completed
spawn items must agree with observed child parent/source lineage. A completed
turn means idle, not permanent shutdown. The sole manager reservation, role and
charter acknowledgements, writer transfer, category teams, current reviews,
recovery and exact artifact rules remain mandatory. Version 2 writes require a
current protected broker context; serialized evidence is insufficient. This is
a logical owner check whose security depends on independently proven process
confinement. No migration, Task creation or activation occurs during inspection.
