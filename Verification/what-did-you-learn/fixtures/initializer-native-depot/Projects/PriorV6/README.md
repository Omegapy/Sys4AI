# Native Prior V6

Observe installed initialization and local learning capability.

Project ID: `native-prior-v6`. Workspace path: `Projects/PriorV6`.

For project specifications, see [SPECS.md](./SPECS.md).

## Licensing

Review this project's root license notices before reusing its material. Setup
adopts the Template's `LICENSE`, `LICENSE-CODE` (Apache 2.0), and `LICENSE-DOCS`
(CC BY 4.0) when no existing license markers are present. An existing licensing
system is preserved as a whole. The setup receipt records which files were
adopted, preserved, or skipped; it does not replace the project's license terms.

## Project guidance

Read [SOUL.md](./SOUL.md), [AGENTS.md](./AGENTS.md), and [ROLE.md](./ROLE.md)
before work. This project owns the guidance, skill packages, and local sub-agent
roles copied from the template. Later template or depot changes require a
separate adoption into this project.

The [Task skill](./.agents/skills/task/SKILL.md) maintains durable work records.
Requirements and implementation plans remain separate from Task state.

## Agent roles

The [Project Director](./ROLE.md) uses the
[role management skill](./.agents/skills/manage-subagent-roles/SKILL.md) to inspect
the [local role bundles](./Roles) and [role index](./Roles/INDEX.md) before bounded delegation. The project
owns those role files and keeps task acceptance with its Director.

## Project setup

The setup receipt is `control_records/project-setup.json`. It records the
Template source hashes, adopted and preserved files, project identity and
factual registration. Later runs verify current files and registration while
preserving project edits. The project owns its environment and dependencies;
add them only when its actual work requires them.

## Repository and publication

The depot registration records factual inventory. Git setup, remotes, publication
and deployment have their own separately authorized workflows.

## Project memory

The [memory skill](./.agents/skills/memory/SKILL.md) uses this project's
[memory directory](./MEMORY/README.md) and [configuration](./memory.yaml).
New projects start with no learned records and the backend disabled. Current
instructions, Task state, roles and source evidence retain authority over recalled
conclusions. Lookup does not initialize a backend or create a Task. The setup
receipt records preserved existing memory separately; later runtime provisioning
and canonical publication require their own current project scope.

Automatic memory capture defaults on for a new installation. The agent records
useful evidence-backed findings at substantive work completion. Ask to turn it
off; current configuration in `memory.yaml` determines the actual preference.
