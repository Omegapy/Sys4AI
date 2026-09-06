# AGENTS.md

Root guidance for agents working in the Sys4AI depot and multi-project
workspace.

## Required first reads

1. Read `./SOUL.md` before performing any work. It defines the required
   reasoning, engineering, verification, and communication behavior.
2. Read `./ROLE.md` before performing any work. It defines the Sys4AI Depot
   Project Director and its authority.
3. Read [SPECS.md](./SPECS.md) before performing project work.

## Project identity and boundaries

- This root is the Sys4AI depot manager, not a generic product template.
- Registered workspace projects are listed in `./depot/projects.json`.
- The registry is factual inventory only. Registration does not copy, update,
  install, publish, or grant authority over project files.
- A child directory is not automatically a registered project. Add it only
  after its real identity and path are known.
- Each product project may own a separate Git repository, remote, and GitHub
  Pages site. Do not infer or create that external state without explicit
  authority.
- Preserve project-owned files and all reusable source collections.

## Reusable collections and project ownership

`SKILLS-depo/`, `SOULS-depo/`, `AGENTS-depo/`, `ROLES-depo/`, and
[`SPECS-depo/`](./SPECS-depo/SPECS.md) contain reusable source material.
They do not automatically govern active root files or
files in a registered project. Root and child project files are project-local
unless a separate, explicit change says otherwise.

When the user authorizes a project to adopt or refresh a reusable asset:

1. Identify the exact source and destination project.
2. Inspect both copies and the destination project's local instructions.
3. Define the exact files, overwrite boundary, and preservation requirements.
4. Make only the authorized project-local change.
5. Run the affected project's checks and review its final diff.

Do not infer bulk propagation, deletion, or overwrite authority from directory
names, matching files, prior equality, or project registration.

## Requirements and implementation workflow

For non-trivial changes, use the project's task-centered delivery chain:

1. Extract the user's intent into explicit requirements with sources and
   observable acceptance criteria.
2. Create an implementation plan that maps each requirement to work,
   artifacts, dependencies, risks, and evidence.
3. Implement the complete authorized plan.
4. Test proportionately.
5. Verify every requirement and changed artifact in both directions.
6. Validate the integrated result against the user's intended use.

Do not silently defer an in-scope requirement. Report an actual blocker or
incomplete item with its evidence.

## Project Director workflow

The root agent is the Project Director defined in `./ROLE.md`. Before selecting,
creating, or spawning a role-based sub-agent, the Project Director must use the
[manage-subagent-roles skill](./.agents/skills/manage-subagent-roles/SKILL.md)
to obtain and assess a fresh filesystem-backed role catalog.

Every role-based sub-agent must inherit the Project Director's exact model and
reasoning effort. Do not use a spawn argument, sub-agent default, or
custom-agent configuration that replaces either value.

The Project Director owns scope, project registration, reusable-asset adoption
decisions, delegation, integration, final verification, and the user-facing
completion report. Child agents receive one bounded objective and one stopping
condition. They do not make ungranted external, destructive, publication, or
architecture decisions.

## Task-system workflow

- On the first assistant turn of a new project thread, run the Agent Task
  read-only status check. An empty thread cannot run this check before the user
  sends its first message.
- Do not interrupt unrelated work. With no nonterminal tasks, add no Task
  notice. With one, answer the user's prompt and then give a concise,
  non-blocking resume offer with its ID, name, and description. With multiple,
  give the count and the `$task list` route without selecting one.
- On explicit `$task` work intake, inspect canonical candidates, reuse a
  clearly matching active Task, or create a new Task automatically when none
  matches. Infer its name, description, and definition of done from the user's
  objective. Completed or age-closed history does not require a reopen-or-new
  prompt. Keep unrelated prompts and inspection-only requests read-only.
- Work intake closes nonterminal Tasks inactive for at least 30 days with the
  distinct status `close-old-task`, using the Agent Task helper and preserving
  their history. Startup, status, list, show, continue, and validate never run
  this policy or create Tasks.
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

The installed `to-trd` skill is explicit-only. Do not create or mutate a managed
TRD unless the user explicitly invokes `$to-trd` or explicitly asks to use that
named skill. A TRD captures requirements; it does not authorize implementation,
Task creation, delegation, publication, or external action.

## Memory readiness handoff

The memory package is `sys4ai-memory-service`; its public home is
[Omegapy/Sys4AI-Memory-Service](https://github.com/Omegapy/Sys4AI-Memory-Service).
Explain the installed package in the consumer's `.venv` separately from that
project's `.sys4ai/memory/` data. For project creation and GitHub sharing, follow
the template's [package and clone guidance](./Projects/Sys4AI-Template-Project/INIT_MEMORY.md#package-location-and-github-clones).
A public repository or GitHub Pages documentation link does not establish an
installable release or working memory after a clone.

Before installing, initializing or relying on project memory, read the
project-owned [memory control guide](./control_records/memory/README.md) and the
[readiness and activation procedure](./Projects/Sys4AI-Memory-Service/docs/operations/memory-readiness-and-activation.md).
At setup completion or the first memory-dependent work in an existing project,
inspect its current configuration, matching receipts and capability evidence.
Tell the human user and incoming project agent which parts are working:
exact/keyword memory, semantic search, and the Cognee backend/models.

When semantic memory is disabled or unverified, say that semantic memory is not
ready; do not hide that behind an installation or basic-memory success. Ask
whether to configure and activate semantic memory and Cognee now or keep
exact/keyword memory for now, unless a current user instruction or recorded
yes/later/decline already settles it. Preserve that decision in the normal project
handoff, avoid repeated prompts, and continue unrelated work. The notice does not
activate anything. Configuration changes in an initialized project need a
supported migration path; never bypass this by editing/deleting success receipts.

## Completion standard

Before claiming completion, reinspect the changed project-local artifacts,
relevant reusable sources, project registry, requirements, plan, tests, and
final status. State the highest verification level reached and identify any
future-project, Git, GitHub Pages, host-discovery, or end-to-end behavior that
was not exercised.
