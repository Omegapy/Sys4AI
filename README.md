# Sys4AI

Sys4AI is a local depot and multi-project workspace for building agentic AI
systems. It contains reusable skill, soul, agent-guidance, and role collections;
the active root Project Director environment; project planning and verification
records; and independent Sys4AI project working trees.

For project specifications, see [SPECS.md](./SPECS.md).

## Current state

The former synchronization capability was retired on 2026-08-29. The workspace
now provides an explicitly requested project initializer. It copies a reviewed
starter and records that one adoption; there is no background propagation.
A later change in a reusable collection does not change an active root or
child project, and a project change does not update a reusable collection.

The reusable `SKILLS-depo/` collection contains source packages that can be
reviewed for later project-local adoption. It is not an installation manager.
The project template is at `Projects/Sys4AI-Template-Project/`. The independent
Sys4AI Memory Service product is at `Projects/Sys4AI-Memory-Service/`. Both are
registered as workspace inventory, excluded from ordinary root-repository
tracking, and currently have no independent Git repository.

## Workspace layout

```text
Sys4AI/
  AGENTS.md                     root Project Director instructions
  SPECS.md                      root project specifications
  SOUL.md                       active root reasoning and quality guidance
  ROLE.md                       active root Project Director role
  .agents/skills/               active root skill installations
  SKILLS-depo/                  reusable skill source packages
  SOULS-depo/                   reusable soul source material
  AGENTS-depo/                  reusable agent-guidance source material
  ROLES-depo/                   reusable role source material
  SPECS-depo/                   reusable project specifications and .gitignore
  Projects/                     independent project working trees
  depot/
    projects.json               factual workspace project registry
    README.md                   registry contract
  Requirements/                current source-linked requirements
  Implementation_Plans/        current and independent implementation plans
  Verification/                current verification records
  Tasks/                        root project Task data
  tests/                        root repository contract tests
```

## Ownership model

Active root files and files inside each child project are project-local. Files
with the same name in a reusable collection are separate artifacts. Matching
content, prior equality, or workspace registration does not grant overwrite or
bulk-copy authority.

If a future request asks a project to adopt or refresh a reusable asset:

1. identify the exact reusable source and destination project;
2. read the destination project's local instructions;
3. compare the source with the current destination;
4. review the exact file and overwrite boundary;
5. make the authorized project-local change; and
6. run the destination project's relevant checks.

This is a normal scoped project change. No update happens automatically.

## Reusable collections

- `SKILLS-depo/` stores reusable Codex skill packages.
- `SOULS-depo/` stores reusable reasoning and quality guidance.
- `AGENTS-depo/` stores reusable project instruction sources.
- `ROLES-depo/` stores reusable Director and sub-agent role sources.
- For reusable project specifications, see [SPECS-depo/SPECS.md](./SPECS-depo/SPECS.md).

These collections can support a later explicit install, template update, or
project-specific edit. They do not control active copies. Root-specific
`AGENTS.md` and `ROLE.md` now exist only at the root; the redundant depot-source
copies were removed with the retired control plane.

## Project registry and repository boundaries

[`depot/projects.json`](./depot/projects.json) records known workspace projects,
their local paths, and observed repository and GitHub Pages state. Registration
does not create files, initialize Git, configure a remote, publish a site, or
give the parent authority over a child project's content.

The project container is [Projects](./Projects):

| Project | Local path | Repository | Remote |
| --- | --- | --- | --- |
| Sys4AI depot | `.` | Initialized on `main` | `git@github-omegapy:Omegapy/Sys4AI.git` |
| Sys4AI Template Project | `Projects/Sys4AI-Template-Project` | Not initialized | Not configured |
| Sys4AI Memory Service | `Projects/Sys4AI-Memory-Service` | Not initialized | Not configured |

Each child project can own its own Git history, remote, commits, pushes, and
deployment. The root repository ignores child working-tree files to avoid
double-tracking them. Repository creation, submodules, remotes, commits, pushes,
and deployment require separate explicit authority.

## Add a future Sys4AI project

Use the active [init-new-project skill](./.agents/skills/init-new-project/SKILL.md)
with the destination, unique stable ID, name, product purpose and memory owner.
Version 1 supports real projects beneath this depot's `Projects/` container.
For example, after the user selects those values, the canonical command is:

```bash
.venv/bin/python .agents/skills/init-new-project/scripts/init_new_project.py create \
  --destination /Volumes/P-SSD/AngryOwl/Sys4AI/Projects/Example-Project \
  --project-id example-project --project-name 'Example Project' \
  --purpose 'Describe the actual product and its users.' --principal-id example-owner
```

One execution copies the registered template's static starter, specializes its
identity, adopts exactly six complete skill packages from `SKILLS-depo/` and
`SOULS-depo/SOUL.md`, records factual inventory, installs an immutable Memory
Service wheel into the final project's own `.venv`, and initializes local memory
directly. It checks exact retrieval before reporting completion. Semantic
provider and model activation are reported separately and remain deferred.
The initializer skill itself and future optional packages are not added to the
six-package consumer baseline.

For a clean manual copy, follow the template's
[INIT_MEMORY.md](./Projects/Sys4AI-Template-Project/INIT_MEMORY.md).
The same helper's `prepare-existing` route refreshes the six reviewed depot
packages, preserves unrelated files, registers inventory and installs the exact
runtime. It returns one direct `init-memory` command. The template itself stays
uninitialized. Neither route copies `.git`, environments, caches or memory
databases, and neither configures Git or publication.

Each result records immutable source/package hashes and project-owned outputs.
An equivalent rerun verifies them without refreshing assets or repeating memory
initialization. A conflict or interrupted stage gives bounded recovery evidence;
later asset refreshes remain separately scoped project work.

## Sys4AI depot memory

For project memory specifications, see [SPECS.md](./SPECS.md#project-memory).
For setup, readiness checks and activation decisions, follow the
[project memory control guide](./control_records/memory/README.md).

## Agent roles

The root [AGENTS.md](./AGENTS.md), [SOUL.md](./SOUL.md), and
[ROLE.md](./ROLE.md) define the Sys4AI Depot Project Director. Reusable
sub-agent roles live in [sub-agent-roles](./sub-agent-roles).

Before role-based delegation, the Project Director uses the root
[manage-subagent-roles skill](./.agents/skills/manage-subagent-roles/SKILL.md)
to inspect the current filesystem-backed role catalog. Child agents return
bounded evidence; the Director owns scope, integration, and completion.

## Tasks and TRDs

The project-local Task system stores durable work records in [Tasks](./Tasks).
It activates only through explicit `$task` intent. A Task is separate from a
Codex task, native goal, or Task Requirement Document (TRD).

The [To-TRD skill](./.agents/skills/to-trd/SKILL.md) creates a managed TRD only
when the user explicitly invokes `$to-trd` or asks to use that named skill. A
TRD captures requirements; it does not authorize implementation or create Task
state.

## Removal records

The current requirements and implementation plan are:

- [synchronization removal requirements](./Requirements/sys4ai_synchronization_removal_requirements.md);
- [synchronization removal implementation plan](./Implementation_Plans/sys4ai_synchronization_removal_implementation_plan.md); and
- [synchronization removal verification](./Verification/sys4ai_synchronization_removal_verification.md).

The independent role-system and Task-system implementation contracts remain in
`Implementation_Plans/`. Git history retains the earlier control-plane sources
if the user later authorizes a new project to reconsider the capability.

## Checks

Run the root repository and independent skill checks with:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s .agents/skills/init-new-project/tests -v
.venv/bin/python -m unittest discover -s .agents/skills/agent-task/tests -v
.venv/bin/python -m unittest discover -s .agents/skills/manage-subagent-roles/tests -v
.venv/bin/python -m unittest discover -s .agents/skills/to-trd/tests -v
```

Installed-wheel initializer scenarios are opt-in via the exact
`SYS4AI_INITIALIZER_ARTIFACT` receipt, as described in the skill README. They
exercise disposable projects. Local checks and fixture creation do not establish
GitHub Pages, publication, deployment or semantic model readiness.
