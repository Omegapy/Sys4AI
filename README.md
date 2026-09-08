# Sys4AI

Sys4AI is a local depot and multi-project workspace for building agentic AI
systems. It contains reusable skill, soul, agent-guidance, and role collections;
the active root Project Director environment; project planning and verification
records; and independent Sys4AI project working trees.

For project specifications, see [SPECS.md](./SPECS.md).

## Current state

Reusable assets are maintained in the `*-depo` collections. The
[template update pipeline](./depot/template-update.md) automatically updates
`Projects/Sys4AI-Template-Project/` after source edits settle. Project creation
and clean existing-project preparation copy starter assets only from that
template. Active root installations and existing product projects keep their
own copies and receive updates only through a separately scoped adoption.

The reusable `SKILLS-depo/` collection is where skills are created, changed and
removed. Its valid packages are published into the template automatically.
The project template is at `Projects/Sys4AI-Template-Project/`. It is registered
as workspace inventory and tracked by this repository. It has no independent
Git repository. Other project working trees remain excluded from root tracking.

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

Active root files and files inside ordinary product projects are project-local.
The template has explicit source mappings in
[`depot/template-update.json`](./depot/template-update.json). Author mapped
template content in its source collection; the updater checks hashes before
replacing or deleting any managed template file.

If a future request asks a project to adopt or refresh a reusable asset:

1. identify the exact reusable source and destination project;
2. read the destination project's local instructions;
3. compare the source with the current destination;
4. review the exact file and overwrite boundary;
5. make the authorized project-local change; and
6. run the destination project's relevant checks.

This procedure applies to existing product projects and active root copies.
The template follows its automatic update mapping.

## Reusable collections

- `SKILLS-depo/` stores reusable Codex skill packages.
- `SOULS-depo/` stores reusable reasoning and quality guidance.
- `AGENTS-depo/` stores reusable project instruction sources.
- `ROLES-depo/` stores reusable Director and sub-agent role sources.
- For reusable project specifications, see [SPECS-depo/SPECS.md](./SPECS-depo/SPECS.md).

These collections own reusable changes and feed the template. Root-specific
`AGENTS.md` and `ROLE.md` now exist only at the root; the redundant depot-source
copies were removed with the retired control plane.

## Project registry and repository boundaries

[`depot/projects.json`](./depot/projects.json) records known workspace projects,
their local paths, and observed repository and GitHub Pages state. Registration
does not create files, initialize Git, configure a remote, publish a site, or
give the parent authority over a child project's content.

The project container is [Projects](./Projects):

| Project | Local path | Own repository | Own remote |
| --- | --- | --- | --- |
| Sys4AI depot | `.` | Initialized on `main` | `git@github-omegapy:Omegapy/Sys4AI.git` |
| Sys4AI Template Project | `Projects/Sys4AI-Template-Project` | Not initialized | Not configured |

The parent tracks the Template's source files. Local ignore rules protect
environments, credentials, caches, and generated artifacts. Other child working
trees remain excluded. GitHub Pages and deployment are separate actions.

## Add a future Sys4AI project

Use the active [init-new-project skill](./.agents/skills/init-new-project/SKILL.md)
with the destination, unique stable ID, name, and product purpose. Both routes
support projects beneath this depot's `Projects/` container.

```bash
.venv/bin/python .agents/skills/init-new-project/scripts/init_new_project.py create \
  --destination /Volumes/P-SSD/AngryOwl/Sys4AI/Projects/Example-Project \
  --project-id example-project --project-name 'Example Project' \
  --purpose 'Describe the actual product and its users.'
```

The helper copies the registered Template's selected starter files, complete
skill and role packages, reference assets, and `SOUL.md`. It specializes project
identity and records factual registration. All seven governance and setup
skills are required; additional complete packages are discovered automatically.

Use `prepare-existing` for a manual copy or a customized existing project.
It adopts missing assets and preserves project-owned content and identity.
Equivalent reruns verify the retained setup without duplicate registration.
The project-owned `control_records/project-setup.json` receipt records source
hashes, asset adoption, registration, and verification; interrupted operations
resume through the helper's checked same-request flow.

Project runtime dependencies, environment creation, Git configuration, and
publication are separate work. Starter copying excludes environments, secrets,
caches, and repository metadata. Existing products receive no automatic refresh.

## Agent roles

The root [AGENTS.md](./AGENTS.md), [SOUL.md](./SOUL.md), and
[ROLE.md](./ROLE.md) define the Sys4AI Depot Project Director. Active role definitions live as paired files under [roles](./roles);
[roles/INDEX.md](./roles/INDEX.md) provides generated navigation. Legacy
`sub-agent-roles/` retains transition provenance and historical references.

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

The retained helpers and tests use the Python standard library. Initializer
checks use disposable depot fixtures. Local checks do not establish publication,
deployment, or behavior in an independently customized product.

## Task-manager execution

Explicit Task work uses the installed [Task skill](./.agents/skills/task/SKILL.md).
The host reserves one real native manager and transfers canonical writer
ownership after its actual receipt and activation. Generic work uses one worker;
complex work uses independent solvers and a distinct senior; extra-complex work
adds one reviewer per solver. Current review, proposal acceptance, dedicated
implementation when needed, and direct integration evidence govern completion.

The [orchestration contract](./.agents/skills/agent-task/references/orchestration-contract.md)
documents actual helper payloads, version and recovery gates. Root automatic
work intake and 30-day inactivity closure remain local policies. Historical
Tasks retain their original schema and meaning until an explicitly selected
upgrade. Native goals, plans, TRDs and Task state remain separate.
