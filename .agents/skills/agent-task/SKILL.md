---
name: agent-task
description: Manage the project-local Task ledger for the root Project Director, including task creation, exact continuation, response recording, lifecycle transitions, validation, and recovery. Do not use as a general user task router or from a child-agent role.
---

# Agent Task

Use this internal workflow only when the root Project Director needs to inspect
or maintain the project-local Task ledger. It is not a second user-facing Task
router. A child agent must stop without changing `Tasks/` and return its evidence
to the Project Director.

## Establish authority and root

1. Confirm that the active agent is the root Project Director governed by the
   root `ROLE.md`.
2. Resolve the project root that contains the applicable `AGENTS.md`,
   `SOUL.md`, and `ROLE.md`.
3. Confine every ledger path to `<project-root>/Tasks/`. Stop at an ambiguous
   root, unsafe path, symlink escape, corrupt record, ambiguous selector,
   active writer, stale revision, prohibited transition, or missing authority.
4. Read the relevant sections of
   [the Task system contract](references/task-system-contract.md) before using a
   mutating mode or recovery procedure.

## Use the deterministic helper

Run the standard-library helper from the project root:

```bash
.venv/bin/python .agents/skills/agent-task/scripts/task_state.py \
  --project-root . <command> [options]
```

The read-only commands are `status`, `list`, `show`, `continue`, and
`validate`. They must not create directories, acquire persistent locks, update
timestamps, attach thread references, rebuild projections, or write Task
Responses. `rebuild-projections` changes generated views only.

The work-intake command is `intake`: it applies the 30-day inactivity policy,
then reuses a matching active Task or creates a new one from the supplied work
profile. An explicit `$task` work request authorizes intake without a separate
creation prompt. `--match-task SELECTOR` carries the Director's exact candidate
selection; automatic profile matching compares normalized name, description,
and definition of done. Read the contract before using this mutating route.

The canonical mutation commands are `intake`, `new`, `update`,
`record-response`, `pause`, `complete`, `close-old-task`, `cancel`, and `reopen`.
`reconcile` performs only the
explicit bounded repair described in its payload. Send long values as JSON on
standard input or in a one-use payload file; do not rely on fragile shell
quoting.

For every mutation of an existing task:

1. Run read-only validation and resolve exactly one task.
2. Read its canonical revision.
3. Supply that value with `--expected-revision`.
4. Let the helper acquire locks, reread and validate state, reject stale input,
   publish atomically, regenerate projections, and return a durable receipt.
5. Run validation after the mutation and inspect the returned paths.

Never edit `task.json`, `TASK.md`, `INDEX.md`, a Task Response, a lock, or a
transaction intent freehand. An old Task Response remains append-only during
ordinary work. Use a superseding response for corrections. Direct redaction is
limited to an explicitly authorized security or privacy recovery and must be
recorded as a correction.

## Record Director turns

Read the contract's payload and response sections before recording. Include
only observed work, concise verification evidence, the user-facing response
summary, truthful post-turn status, next step or required decision, current
blockers and questions, and relevant project-relative files. Never store
hidden reasoning, a full transcript, credentials, secrets, or large raw logs.

For completion, provide criterion-by-criterion evidence for the current
definition of done, set `next_step` to `null`, and use the exact conclusion
`Task completed. No next step required.` The helper must reject incomplete
completion evidence.

The successful response transaction order is response publication, canonical
JSON update, `TASK.md` regeneration, and `INDEX.md` regeneration. If the helper
returns a partial-transaction or projection warning, report the committed core
accurately and follow the explicit recovery route. Never retry blindly after an
orphan response, and never steal a lock automatically.

`close-old-task` is a separate terminal state for unfinished Tasks inactive for
at least 30 elapsed days, measured from `updated_at`. It preserves history,
uses `next_step: null`, and records why the Task was closed without claiming
its work is complete. Direct closure and intake both use the same locked age
and revision checks. Existing read-only routes never age or create Tasks.
Renewed work for completed, cancelled, or age-closed history goes through
intake to a new related Task; only an explicitly requested reopen can change
a completed record back to open.

For a multi-Task intake, inspect all closure and selection/creation receipts.
A partial result can contain committed changes; follow its recovery direction
before continuing instead of restarting the whole operation blindly.

## Interpret results

Use structured JSON for internal decisions. The helper's stable exit categories
are documented in the contract. Treat nonzero results as failures or recovery
states, not as successful mutations. A Task Response or index is a continuation
aid; current canonical state and live project artifacts still require direct
inspection before consequential work or a completion claim.

Task activation does not grant authority for deletion, dependency installation,
external communication, Git operations, publication, deployment, purchases, or
changes outside the project root.
