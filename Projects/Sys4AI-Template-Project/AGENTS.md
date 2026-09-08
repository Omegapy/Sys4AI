# AGENTS.md

Root project guidance for agents working in a project created from the Sys4AI
template.

## Required first reads

1. Read `./SOUL.md` before performing any work. It defines the required
   reasoning, engineering, and communication behavior for the agent.
2. Read `./ROLE.md` before performing any work. It defines the agent's active
   role.
3. Read [SPECS.md](./SPECS.md) before performing project work.

## Project identity

Read the project README and local requirements before assuming the product,
domain, repository state, runtime, or publication target. This template supplies
agent governance and workflow components; it does not supply a product identity.

## Requirements and implementation workflow

For non-trivial changes, extract explicit requirements from user intent, create
a traceable implementation plan, implement the complete authorized scope, and
verify every requirement against current evidence. Keep requirements, plans,
Task state, TRD state, and native goal state distinct.

## Project Director workflow

The host is the Project Director defined in `./ROLE.md`. Explicit Task execution
uses a distinct native manager with a bounded bootstrap handoff. Before selecting,
creating, or spawning any role-based agent, the responsible Director must use the
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
- Bootstrap reserves one manager before launch and records its actual native
  receipt before activation. Activation transfers the sole canonical writer to
  that exact manager and ends bootstrap writes. The host relays user steering.
- The confirmed manager owns Task state, definition-of-done verification,
  integration and final Task Responses. Ordinary workers, solvers, reviewers,
  seniors and implementers return evidence without ledger or role-index writes.
- Each executable subtask is generic, complex or extra-complex. Follow the
  installed Task skill for required distinct agents, current-version review,
  senior return, conditional implementation and native stopping/recovery.
- Active role pairs are in `Roles/`; `Roles/INDEX.md` is generated navigation.
  Fresh paired-file validity and function-specific fit govern each assignment.
  Reading root guidance does not promote an ordinary child to manager.
- Keep Task state separate from conversation threads, Codex memory, managed
  TRDs, and native goal state. Report any mismatch and do not silently merge or
  overwrite these sources.

## TRD workflow boundary

The installed `to-trd` skill remains explicit-only. It captures requirements
when the user invokes it; it does not authorize implementation or create Task
state.
