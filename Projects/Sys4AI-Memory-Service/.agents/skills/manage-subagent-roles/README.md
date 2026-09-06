# Manage sub-agent roles skill

This repository-local Codex skill lets the Project Director discover, validate,
select, create, and use reusable sub-agent roles stored in
`sub-agent-roles/`.

## Contents

- `SKILL.md` defines the role-management workflow.
- `agents/openai.yaml` contains Codex display and invocation metadata.
- `scripts/role_catalog.py` lists, validates, shows, and creates role bundles.
- `references/role-schema.md` defines the role-bundle format.
- `assets/role-bundle/` contains templates for new role bundles.
- `tests/test_role_catalog.py` verifies the catalog and project contracts.
- `README.md` explains the skill's purpose and contents.

## Project scope

Codex discovers this skill from
`.agents/skills/manage-subagent-roles/`. The root `ROLE.md` requires the
Project Director to use it before selecting, creating, or spawning a
role-based sub-agent.

The live `sub-agent-roles/` filesystem is the catalog. This skill does not
create a persistent role registry.

Codex does not recursively discover every nested `AGENTS.md`. Since role-based
children are spawned from the project root, the skill explicitly gives each
child its selected role's `AGENTS.md` and `ROLE.md` paths and requires both
files to be read before task work.

Every spawned role-based child must inherit the Project Director's exact model
and reasoning effort. Role selection changes instructions and task scope, not
the model configuration.
