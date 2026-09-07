# {project_name}

{purpose}

Project ID: `{project_id}`. Workspace path: `{relative_path}`.

For project specifications, see [SPECS.md](./SPECS.md).

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
the [local role bundles](./sub-agent-roles) before bounded delegation. The project
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
