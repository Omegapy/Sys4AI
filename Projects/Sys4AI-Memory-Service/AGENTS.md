# AGENTS.md

Root project guidance for agents working on the Sys4AI Memory Service.

## Required first reads

1. Read `./SOUL.md` before performing any work. It defines the required
   reasoning, engineering, and communication behavior for the agent.
2. Read `./ROLE.md` before performing any work. It defines the agent's active
   role.
3. Read [SPECS.md](./SPECS.md) before performing project work.
4. For memory installation, adoption, readiness or semantic use, read
   [memory readiness and activation](docs/operations/memory-readiness-and-activation.md).
   Inspect this project's current configuration and matching receipts before
   reporting readiness. Distinguish installed runtime, verified exact/keyword
   memory and verified semantic/Cognee operation. If semantic readiness is
   missing, give the human the guide's concise notice and activation choice,
   unless an existing decision already settles it. Keep startup awareness
   non-blocking and do not repeat an unchanged choice during unrelated work.

## Project identity

Read the approved PRD under `PRDs/` and the current implementation evidence
before changing contracts, storage, policy, or provider behavior.

All files in this product are project-local. Reusable
material in a parent Sys4AI workspace does not automatically govern or update
the project. Adopting or refreshing a reusable asset requires an explicit exact
source, destination, overwrite boundary, and project-local verification.

Do not place credentials in the repository, Task records, logs, fixtures,
exports, or derived memory. Do not initialize provider storage until exclusions,
path boundaries, and a dry-run have passed. Destructive operations require an
impact preview, explicit scope, authorization, and a non-sensitive receipt.

## Requirements and implementation workflow

For non-trivial changes, extract explicit requirements from user intent, create
a traceable implementation plan, implement the complete authorized scope, and
verify every requirement against current evidence. Keep requirements, plans,
Task state, TRD state, and native goal state distinct.

## Project Director workflow

The root agent is the Project Director defined in `./ROLE.md`. Before selecting,
creating, or spawning a role-based sub-agent, the Project Director must use the
[manage-subagent-roles skill](./.agents/skills/manage-subagent-roles/SKILL.md)
to obtain and assess the current role catalog.

Every role-based sub-agent must inherit the Project Director's exact model and
reasoning effort. Do not use a spawn argument, sub-agent default, or
custom-agent configuration that replaces either value.

## Task-system workflow

- On the first assistant turn of a new project thread, run the Agent Task
  read-only status check. An empty thread cannot run this check before the user
  sends its first message.
- Do not interrupt unrelated work. With no nonterminal tasks, add no Task
  notice. With one, answer the user's prompt and then give a concise,
  non-blocking resume offer with its ID, name, and description. With multiple,
  give the count and the `$task list` route without selecting one.
- Enter task creation or selection only after explicit `$task` activation or
  an explicit user continuation decision. Continuation language triggers a
  candidate check; it does not prove task identity.
- Before a Task state operation, read and follow the project-local
  [Task skill](./.agents/skills/task/SKILL.md) and
  [Agent Task skill](./.agents/skills/agent-task/SKILL.md). Use the Agent Task
  helper for every mutation; status, list, startup awareness, and unrelated
  prompts remain read-only.
- The Project Director owns Task state, definition-of-done verification, and
  final Task Responses. Child agents return evidence and do not mutate the Task
  ledger.
- Keep Task state separate from conversation threads, Codex memory, managed
  TRDs, and native goal state. Report any mismatch and do not silently merge or
  overwrite these sources.

## TRD workflow boundary

The installed `to-trd` skill remains explicit-only. It captures requirements
when the user invokes it; it does not authorize implementation or create Task
state.
