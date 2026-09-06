# {project_name}

{purpose}

Project ID: `{project_id}`. Workspace path: `{relative_path}`.

For project specifications, see [SPECS.md](./SPECS.md).

## Project guidance

Read [SOUL.md](./SOUL.md), [AGENTS.md](./AGENTS.md), and [ROLE.md](./ROLE.md)
before work. This project owns its copied guidance, six baseline skill packages,
and local sub-agent roles. Later depot changes do not update these files.

The [Task skill](./.agents/skills/task/SKILL.md) maintains durable work records.
Requirements and implementation plans remain separate from Task state.

## Agent roles

The [Project Director](./ROLE.md) uses the
[role management skill](./.agents/skills/manage-subagent-roles/SKILL.md) to inspect
the [local role bundles](./sub-agent-roles) before bounded delegation. The project
owns those role files and keeps task acceptance with its Director.

## Local memory

This project uses the `sys4ai-memory-service` Python package, maintained at
[Sys4AI-Memory-Service on GitHub](https://github.com/Omegapy/Sys4AI-Memory-Service).
The depot setup installs a locally built wheel into this project's own `.venv`.
Python imports `sys4ai_memory` there; this project's derived memory data stays
under `.sys4ai/memory/` and is excluded from Git.

After a GitHub clone, check the project's pinned dependency and local setup
instructions before using memory. Install the declared package with `pip` or
`uv pip`, then initialize, synchronize and verify memory for this environment.
A repository link, requirements file or copied receipt does not establish a
working installation. If the dependency or clone setup is missing, report that
gap; the current depot initializer does not generate those sharing components.
GitHub Pages, if provided, hosts documentation; the memory package runs locally.

For setup, readiness checks and activation decisions, follow the project-owned
[Memory control guide](./control_records/memory/README.md).
{manual_guide}
## Repository and publication

The depot registration records factual inventory. Git setup, remotes, publication
and deployment have their own separately authorized workflows.
