# {project_name}

{purpose}

Project ID: `{project_id}`. Workspace path: `{relative_path}`.

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

## Project app

Open **Launch Project.command** in Finder to read this project's Home, Work,
Project knowledge, Health and setup, and Tools and help. Search and source
previews stay within the selected project's permitted information.

Closing a tab leaves the reading session active. **Close reading session**
revokes that session; **Stop app** stops this project's owned reader service.
Opening the launcher again reuses a compatible service or starts a fresh one.
If a prerequisite is missing, the launcher opens **Project App Setup.html**.

Home explanations live in `project-app.json`. A project owner reviews the text
and its source references; changed sources show a review notice. Empty starter
content is labeled until reviewed. See the
[Project app operations](./.agents/skills/ontology/references/project-app-operations.md)
for build, selected adoption and recovery instructions.
