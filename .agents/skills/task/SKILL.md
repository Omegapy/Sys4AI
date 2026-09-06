---
name: task
description: Match explicit $task work to an active project Task or create one automatically, close Tasks inactive for 30 days, and maintain tracked work. Do not use for ordinary untracked questions or unrelated project work.
---

# Task

Use this skill only for the project-local Task workflow. The root agent remains
the Project Director. Do not spawn a replacement director or create a Codex
task, thread, or goal merely because this skill is active.

A project Task is a user-given job or problem assigned to the existing root
Project Director. It can be simple or complex. It is not a delegated subtask,
child-agent assignment, Codex conversation, native goal, managed TRD,
implementation plan, Git state, deployment, or release state.

## Activate the root Project Director

1. Resolve one exact project root containing the applicable root `AGENTS.md`,
   `SOUL.md`, and `ROLE.md`. Stop if the root is ambiguous, any required file is
   missing, or a candidate path escapes that root.
2. Read the complete root `ROLE.md` and apply its Project Director role before
   any Task mutation, classification, execution-pattern decision, role
   selection, or delegation. Also follow the root `AGENTS.md` and `SOUL.md`.
3. Confirm that the active root agent is that Project Director for the entire
   Task workflow. Reading the role specializes the existing root agent; it
   never spawns, substitutes, or delegates to a replacement Director.
4. Before every Task state operation, read the complete internal
   [Agent Task skill](../agent-task/SKILL.md). Use its helper and contract; do
   not construct paths or edit Task files freehand.

Task activation permits the requested project work and maintenance of its local
Task record. It does not authorize destructive actions, dependency installs,
external messages, commits, pushes, publication, deployment, or changes outside
the project root.

## Select the mode

Support work intake, `new`, `implement`, `continue`, `status`, `list`, `show`,
`update`, `pause`, `complete`, `close-old-task`, `cancel`, `reopen`, `validate`,
and an explicit recovery request. `implement` is a work request routed through
intake, not a separate helper command.

`Tasks/INDEX.md` is the generated catalog view. Use Agent Task `status` or
`list` to inspect current canonical records; a stale index cannot hide a Task.
Keep status, list, show, validate, startup awareness, and the helper's continue
operation read-only. A bare `$task` without an actionable objective can show the
catalog and ask what work the user wants; it must not invent a job.

For an explicit `$task` work request, including `$task implement <plan>`:

1. Infer a concise name, description, and observable definition of done from
   the user's actual objective and named artifacts. Use supplied values when
   available; do not ask the user to repeat information already present.
2. Inspect canonical candidates and compare their objective, deliverables,
   scope, and status. Planning and implementing the same artifact are
   different objectives. Similar words, recency, or the mere presence of an
   unrelated open Task are not a match.
3. If one active Task clearly matches, pass its exact selector through Agent
   Task `intake --match-task SELECTOR`. For deterministic identical profiles,
   `intake` can match the normalized name, description, and definition of done
   itself. Pass the actual work profile as the normal new-task JSON payload.
4. If no active Task matches, call `intake` to create a new Task automatically
   and proceed with authorized work. The explicit work request authorizes this
   bookkeeping; no separate new-task confirmation is needed.
5. When the matching history is completed, cancelled, or `close-old-task`, use
   a new related Task instead of presenting a reopen-or-new question. Preserve
   the historical record and use a parent link when its relation is established.
   Multiple historical matches do not block creation; omit an uncertain parent.
   An explicit `reopen` request remains available for completed Tasks.

Ask one focused question only when the objective is missing or multiple
plausible active Tasks cannot be distinguished from current evidence. An
invalid or ambiguous explicit selector must be resolved, not replaced with a
guess. A pure inspection request never creates a Task. Explicit `new` still
forces creation of a separate record.

Task routing must not add an approval gate to implementation the user already
authorized. Keep any actual unresolved scope, dependency, or action-specific
authority requirement separate from Task selection.

## Close inactive Tasks

Treat a month as 30 elapsed days without an update to the canonical Task.
During explicit work `intake`, close Tasks in `open`, `paused`, `awaiting_user`,
or `blocked` whose `updated_at` is at least 30 days old. Use the helper's
`close-old-task` transaction, which rechecks age, revision, and locks before
writing. A currently updated or locked record must not be closed from stale
information. This policy runs on intake, not a background schedule.

Use the terminal status `close-old-task` and an append-only response recording
the inactivity evidence. Preserve the Task ID, definition of done, files, and
response history. Closing old work does not prove completion and must not mark
criteria as satisfied. A later work request receives a new related Task.
Explicit `close-old-task SELECTOR` uses the same 30-day gate.

Never run aging as a side effect of status, list, show, continue, validate,
startup awareness, or an ordinary unrelated prompt. If a multi-Task intake
partially commits, inspect its receipts and follow the stated recovery route
before retrying; do not repeat already recorded closures blindly.

## Run the workflow

For new work, derive or accept the task name, description, definition of done,
and an optional established parent-task reference. Use Agent Task `intake` to
reuse or create the record, or `new` when the user explicitly requests one.
For a continuation, load the selected task's canonical state, generated brief,
latest Task Response, and only the older records or live files needed for the
next decision. Live project artifacts override stale summaries.

## Record orchestration durably

Use the governed project Task record and append-only Task Responses as the
durable continuation record. Do not create a second orchestration ledger.
Record the selected workflow as direct, decomposed, or adversarial with its
concise rationale, then retain each event that applies:

- bounded subtask contracts, dependencies, and accountable owners;
- selected role names and role-file paths plus native child identifiers;
- candidate-to-reviewer mappings, review outcomes, revision requests,
  revision cycles, and repeated-review results;
- accepted synthesis, unresolved conflicts, and any recycled solution cycle;
- the single implementation owner, performed-work evidence, current blockers,
  and criterion-by-criterion completion evidence.

Place concise decisions and observed work in `work_completed`, validation in
`verification_evidence`, the current stage in `current_summary`, the next gate
in `next_step`, current impediments in `blockers` or `open_questions`, and
reviewable artifact paths in `relevant_files`. Use only the existing Agent Task
payload and contract unless a separately approved schema change is required.

Keep the project Task, delegated subtasks, child-agent state, managed TRDs,
implementation plans, Codex conversations, native goals, Git, deployment, and
release state distinct. Do not treat hidden reasoning, a full transcript,
stale memory, a child status, a review pass, or synthesis as canonical Task or
completion evidence.

Continue a solver, review, synthesis, or implementation cycle only when the
next cycle adds a material hypothesis, evidence item, or targeted revision.
When authority, capability, runtime capacity, repeated unchanged failure, or
irreducible conflict prevents meaningful progress, record the exact blocker or
bounded user decision and stop that cycle.

## Govern every delegated function

Before assigning any solver, reviewer, senior synthesizer, or implementer, use
the project-local [Manage Sub-Agent Roles skill](../manage-subagent-roles/SKILL.md)
to obtain a fresh valid filesystem-backed role catalog. Build a separate task
profile for the function containing its objective, required capabilities, read
and write needs, expected output, required Codex skills, required tools, risk,
and stopping condition. Select the narrowest valid existing role and preserve
the Project Director's selection decision. Do not reuse a stale catalog or let
a child select its own project-level role.

Each delegation must name the selected role and both role-file paths; require
the child to read root `SOUL.md` plus the selected `AGENTS.md` and `ROLE.md`;
and state one objective, necessary context, bounded scope, protected state,
deliverable, checks, evidence to return, authority limits, and stopping
condition. Require exact Project Director model and reasoning-effort
inheritance with no override.

Create and validate a role only after the fresh catalog proves that no valid
existing role fits and the missing responsibility is a reusable role-definition
gap. A missing Codex skill, tool, permission, dependency, native runtime
capability, or safe inheritance guarantee is not a role gap; stop with its
exact diagnostic instead of creating a substitute role or delegation.

## Generate independent adversarial candidates

Use the adversarial path only when substantial uncertainty or material
unknowns remain after the Director analyzes whether decomposition could reduce
them. Select at least two solvers, with a task-appropriate count unless a
feasible user instruction fixes the number, roles, or perspectives.

Create one common problem packet containing the bounded objective, governing
evidence, known assumptions and unknowns, allowed scope, protected state,
authority limits, expected candidate format, checks, and stopping condition.
Give that same packet to every solver while explicitly assigning each a
different suitable role or perspective through the fresh role-catalog workflow.

Keep candidate development independent: do not expose another solver's draft,
permit cross-solver convergence, or give two solvers conflicting write
ownership. Each solver returns a separately identified, reviewable candidate
artifact and evidence rather than editing the shared implementation. Record
the solver child identifier, role and perspective, candidate locator, and
outcome in the governed Task Response before review begins.

## Review and revise candidates

Formal review is conditional. Use it when the user requests it or the Project
Director finds that independent review adds material value. Once selected,
create one reviewer assignment for every candidate through a fresh role-catalog
selection. Record an exact one-to-one candidate, solver, reviewer child, role,
criteria, and outcome mapping. A reviewer evaluates only its assigned candidate
in that cycle, remains independent from its solver, and never assumes Project
Director ownership.

Classify each result as passed or rejected with evidence. Do not send an
unreviewed or rejected candidate to synthesis. For a rejection, preserve the
candidate and review record, send the clear failure explanation and actionable
revision requests to the originating solver child, and require a separately
identified materially revised candidate. Preserve solver identity and route
the revision through review again before changing its outcome to passed.

If a purported revision adds no targeted change, evidence, or material
hypothesis, do not start another identical review cycle. Record the repeated
unchanged failure and the exact capability, authority, evidence, or user
decision blocker under the stopping contract.

## Synthesize accepted candidates

Begin synthesis only after every candidate required to receive formal review
has a recorded pass. Through a fresh role-catalog selection, assign a distinct
senior synthesis agent that is not the Project Director and does not take
Director authority. Give it every accepted candidate and every material review
finding, including compatible contributions, differences, assumptions,
evidence, and residual risks.

Require one coherent integrated proposal that preserves compatible
contributions, identifies its source candidates, and explains how each material
difference was resolved. Return the proposal and its evidence to the Project
Director for acceptance; synthesis alone neither authorizes implementation nor
proves the Task complete.

If genuine conflicts prevent fusion, require one exact shared conflict record
that identifies every affected candidate, incompatible claim, governing
evidence, and required resolution. Send the same conflict explanation to every
affected originating solver. Each solver returns an independently and
materially revised candidate, every required review repeats, and only then may
another synthesis attempt begin. Record the shared conflict, recipients,
revisions, reviews, and synthesis outcome in the Task Response.

When another cycle cannot add a material hypothesis, evidence item, or targeted
change, use the truthful stopping path and record the irreducible conflict,
missing authority or capability, or bounded user decision instead of silently
choosing a candidate.

## Assign implementation and verify completion

After the Project Director accepts the direct, decomposed, or synthesized
solution, the Director chooses the implementation owner case by case based on
the Task. The owner is either the Project Director or, when its validated role,
capabilities, scope, and action-specific authority fit, the senior synthesis
agent. Record exactly one accountable implementation owner before execution
begins; reject a missing or multiple-owner state.

Before implementation, record the owner, approved solution, allowed files and
scope, protected state, required action-specific authority, dependencies,
checks, evidence, and stopping condition. A Task record, candidate, review
pass, accepted synthesis, or child completion message is a proposal or status,
not performed implementation. Do not broaden authority for installation,
destruction, external messages, Git operations, publication, or deployment.

After the authorized solution is performed, the Project Director must reopen
the live artifacts and current canonical Task, inspect the actual integrated
result, run proportionate checks, and verify every definition-of-done criterion
with current direct evidence. Reject incomplete evidence and a child report as
sole proof. State any consumer adoption, native child execution, external
action, deployment, or other behavior that was not exercised.

Only the Project Director may record exactly one truthful final Task Response
and invoke Agent Task completion. Do not mark the Task complete until the
authorized work was performed or delivered and every definition-of-done
criterion is proven.

The Project Director owns task classification, scope, state transitions,
verification, and completion claims. Role-based child agents may return bounded
work evidence through the existing role workflow, but they cannot create task
folders, mutate canonical Task state, or write final Task Responses.

Before each final Project Director reply that performs, decides, changes, or
substantively explains selected-task work, record exactly one Task Response
through Agent Task using the current expected revision. Do not record transient
commentary, tool output, internal reasoning, an automatic resume notice, or a
pure `status` or `list` reply. Draft the response summary first and keep the
delivered reply materially consistent with the durable record.

If durable recording fails, disclose the failure and do not claim that the
Task ledger was updated. Mark a task completed only after every definition-of-
done criterion has current direct evidence.

Outside explicit Task activation or an explicit continuation decision, answer
ordinary prompts normally and do not mutate Task state merely because a prompt
uses words such as "task," "work," "next," or "continue."
