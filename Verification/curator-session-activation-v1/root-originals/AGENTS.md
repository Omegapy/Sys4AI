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

`SKILLS-depo/`, `SOULS-depo/`, `AGENTS-depo/`, `ROLES-depo/`, `LICENSES-depo/`, and
[`SPECS-depo/`](./SPECS-depo/SPECS.md) contain reusable source material.
They do not automatically govern active root files or ordinary product
projects. Reusable additions, modifications and deletions belong in these
source collections. The explicit template update pipeline is the exception:
[`depot/template-update.json`](./depot/template-update.json) maps these sources
into `Projects/Sys4AI-Template-Project/`, and the local filesystem watcher keeps
that template current. Follow [the update guide](./depot/template-update.md).
Edit mapped content in its source collection, then check the template update.
Create and prepare product projects using only that template's starter assets.
Active root and product-project copies remain project-local.

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

The host is the Sys4AI Depot Project Director defined in `./ROLE.md`. Explicit
Task execution hands control to a real native manager only after its reservation,
actual launch receipt and confirmed activation. That manager acts as Project
Director for the assigned execution and becomes its sole canonical writer. The
host relays user steering and results. Ordinary children receive one bounded
objective and stopping condition; reading root guidance does not promote them.

Before every role-based selection, creation or assignment, the responsible
Director must use the [manage-subagent-roles skill](./.agents/skills/manage-subagent-roles/SKILL.md)
to obtain and assess a fresh filesystem-backed catalog. Active roles are paired
files under `Roles/`; `Roles/INDEX.md` is navigation only. Preserve legacy role
provenance and use explicit preview/apply for transition.

Every role-based child inherits the exact effective model and reasoning effort
of the Director. Omit overrides under a verified inheritance guarantee and
separately verify solver context independence. Queue within observed capacity
without reducing required teams. Children receive no ungranted external,
destructive, publication, installation or architecture authority.

The host retains workspace registration and reusable-asset adoption decisions.
Within its assigned Task, the confirmed manager owns decomposition, category and
role selection, delegation, acceptance, integration, final verification and the
canonical Task Response. Follow the installed Task skill's generic, complex and
extra-complex team, version, stopping and recovery gates.

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
- The host owns bounded bootstrap until manager activation. The confirmed
  manager then owns Task state, definition-of-done verification and final Task
  Responses. Ordinary children return evidence without ledger or role-index writes.
- Reconcile known managers and write-owning workers before any age-based matching
  exclusion, closure, pause, cancellation, replacement or settings change.
- Keep Task state separate from conversation threads, Codex memory, managed
  TRDs, and native goal state. Report any mismatch and do not silently merge or
  overwrite these sources.

## TRD workflow boundary

The installed `to-trd` skill is explicit-only. Do not create or mutate a managed
TRD unless the user explicitly invokes `$to-trd` or explicitly asks to use that
named skill. A TRD captures requirements; it does not authorize implementation,
Task creation, delegation, publication, or external action.

## Completion standard

Before claiming completion, reinspect the changed project-local artifacts,
relevant reusable sources, project registry, requirements, plan, tests, and
final status. State the highest verification level reached and identify any
future-project, Git, GitHub Pages, host-discovery, or end-to-end behavior that
was not exercised.

## Project memory

The [memory skill](./.agents/skills/memory/SKILL.md) provides project-owned
Markdown recall and evidence retrieval when configured. Current instructions,
canonical Tasks, exact role pairs and direct sources retain authority. Memory
lookup is read-only and creates or activates no Task. Follow its
[Task integration contract](./.agents/skills/memory/references/task-integration.md)
for identical frozen solver packets, scoped publication and material changes.
Keep learned records in this project's `MEMORY/`; starter setup copies only
empty capability and never another project's records or runtime.

When project memory is configured with `integration.automatic_capture: true`,
perform the memory skill's [automatic completion checkpoint](./.agents/skills/memory/references/automatic-capture.md)
before the final handoff of substantive work. Capture useful new evidence-backed
findings within current scope without a user reminder. Skip trivial or read-only
requests and duplicate findings. Respect an explicit opt-out and preserve the
existing publication, privacy, Task ownership and frozen-input checks.
