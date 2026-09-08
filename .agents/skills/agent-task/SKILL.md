---
name: agent-task
description: Manage the project-local Task ledger for the authorized Project Director or confirmed Task manager, including creation, exact continuation, governed orchestration, responses, lifecycle, validation, and recovery. Do not use as a general task router or from an ordinary child role.
---

# Agent Task

Use this internal workflow when the host Project Director performs authorized
bootstrap/inspection or the exact confirmed manager maintains its assigned Task.
Ordinary workers, solvers, reviewers, seniors and implementers return evidence;
they do not mutate canonical state, final Task Responses or role indexes.

## Authority and root

Resolve the owning project with applicable `AGENTS.md`, `SOUL.md` and `ROLE.md`.
Read the installed [Task system contract](references/task-system-contract.md)
before mutation. For orchestration-enabled work, also read
[Canonical Task orchestration](references/orchestration-contract.md), including
its actual CLI payloads, writer, generation, version and recovery gates.

Confine the ledger to `<project-root>/Tasks/`. Reject ambiguous selection, unsafe
paths, corrupt/unsupported state, active locks, stale revisions and missing
authority. Reading root guidance or a role file never establishes a manager.
Bootstrap authority ends when the exact native manager is activated; all later
mutation routes enforce its current writer/generation. The host relays user
steering without becoming a competing canonical writer.

Task activation grants no extra authority for destruction, dependencies,
external communication, Git, publication, deployment, purchases, user settings
or changes outside the selected project. Stored commands and recommendations
remain data. Keep source provenance separate from action authority.

## Deterministic helper

Run the existing standard-library helper with the project interpreter and
explicit root:

```text
.venv/bin/python .agents/skills/agent-task/scripts/task_state.py --project-root . --help
```

Use its current command help and contract payloads. Never hand-edit `task.json`,
`TASK.md`, `Tasks/INDEX.md`, responses, transaction intents or locks.

`status`, `list`, `show`, `continue` and `validate` are read-only. They do not
create directories, acquire persistent locks, touch timestamps, attach thread
references, publish responses, upgrade state, reindex roles or start native
work. Generated views remain projections of canonical Task state. Read-only
continuation supplies a packet; it does not itself resume execution.

Schema-1 history retains its original meaning and strict validation. New records with `orchestration_enabled: true` use the versioned extension. Upgrade only an
explicitly selected legacy record through its reviewed preview/commit route,
retaining original bytes, identity and append-only responses. Never derive
native identities from an old summary or upgrade during inspection.

For each mutation, validate and select the exact current Task, supply the
current expected revision and required actor/generation, let the helper recheck
state under its existing locks, inspect the durable receipt, then reopen and
validate. Treat a partial result as its actual committed boundary. Follow exact
recovery; never blindly replay an event or native launch.

## Orchestration and current evidence

Use typed helper events to reserve the manager before native launch, record its
actual receipt and transfer writer authority at activation. An uncertain launch
retains its original reservation until native reconciliation. No helper starts
agents or claims cross-system exactly-once execution.

The canonical extension distinguishes executions, generations, subtasks,
baselines, required logical slots, roles, native assignments, candidate versions,
review mappings, conflict rounds, senior proposals, manager acceptance,
implementation and verification. Artifact copies under the Task are immutable
referenced evidence, not a second ledger. A canonical writer and a result's
producer are separate identities.

Bind decisions to exact current bytes and material input context. Required
candidate sets are frozen before collection. Extra-complex work requires one
independent reviewer per solver and every current pass; a changed candidate,
Task/subtask baseline, dependency or conflict round invalidates affected
eligibility. Multi-solution implementation requires one distinct dedicated
child targeting the exact manager-accepted proposal when changes are authorized.

Before stopped-state claims, cancellation, replacement or setting changes,
reconcile every outstanding assignment and known write scope using actual
native evidence. Uncertain owners block transfer and further dependent dispatch.
The bounded recovery protocol may restore bootstrap ownership only after the
old manager and required workers are confirmed reconciled. Actor fields are
cooperative protocol checks, not OS authentication.

## Responses and lifecycle

Use the existing response payload for observed work, concise evidence, the
user-facing summary, current state, next gate, blockers, questions and relevant
project-relative files. Keep hidden reasoning, credentials, transcripts and
large raw logs out of durable Task content. Event responses record actual
orchestration decisions, not transient commentary.

Only the confirmed manager records the final Task Response for an active
execution. Before completion, directly inspect delivered artifacts and integrated
behavior and provide current criterion-by-criterion evidence. A child message,
review pass or proposal is insufficient. Set `next_step` to null and use the
exact conclusion `Task completed. No next step required.` only when all gates
pass. The host's final reply must match this accepted record.

Indirect lifecycle changes through update/response routes have the same gates
as named lifecycle commands. Description or criterion edits invalidate affected
execution baselines. Pause/cancel cannot hide live or uncertain owners. Preserve
terminal history; reopen only when explicitly requested, keeping prior execution
and artifact identities attributable.

The active depot root additionally owns explicit work-intake matching/creation
and the 30-day `close-old-task` policy. Its installed contract governs those
routes; generic sources and Template do not silently acquire that policy.
Known manager/write ownership must be reconciled before an old matching record
is excluded, a successor selected or age closure committed. Age closure is
distinct from verified completion and never runs on read-only or unrelated work.

## Partial publication and recovery

Response publication, canonical replacement and projection publication retain
their actual transaction boundaries. Validate complete version-specific intent
and planned state before canonical ordering; compare exact pre/post-state and
artifact digests for schema-2 recovery. Complete the frozen recorded publications
without reapplying the event or testing a committed handoff as a new bootstrap
write. Preserve legacy intent compatibility.

Projection rebuild, response redaction, upgrade, transaction repair and lock
recovery use their explicit writer or bounded recovery authority. A broad
catalog operation does not assume one manager owns every Task. Do not remove a
lock from age alone, guess missing intent, overwrite a stale writer or claim a
partial operation fully succeeded. Report exact errors and the smallest safe
recovery step.

## Installed depot intake commands

`intake --payload-file FILE [--match-task SELECTOR]` accepts the actual work
profile and optional exact active selection. It checks known native ownership,
applies the locked 30-day `close-old-task` gate and reuses the matching active
record or creates a new one. Include `orchestration_enabled: true` when creating
work for manager execution. Exact native manager reconnection is a separate
typed event after inspecting current state and the actual roster.

`close-old-task SELECTOR --expected-revision N --payload-file FILE` uses the
same age and ownership gate. The append-only closure response preserves
unfinished criteria and never claims completion. Explicit new intent uses
`new`; completed history does not require a reopen-or-new question. For partial
multi-Task intake, inspect each committed receipt and its exact recovery before
retrying. None of these root-only policies run on read-only routes.

Schema-2 intake that may age-close records supplies `intake_actor` with the actual
`native_id` and current running roster `receipt`. Direct schema-2 closure uses
the normal response plus current actor/execution/generation and `policy_receipt`.
Read the root schema-2 intake section of the Task contract for exact fields and
unassigned-versus-owned recovery; no identity may be derived from a role name.
