---
name: manage-subagent-roles
description: Discover and return project sub-agent roles with their AGENTS.md and ROLE.md paths; use when the Project Director needs to list, select, create, validate, spawn, supervise, or collect results from role-based Codex sub-agents. Do not use this skill to install missing skills or to create separate user-visible tasks.
---

# Manage Sub-Agent Roles

Use the live `sub-agent-roles/` filesystem as the role catalog. Never rely on a
remembered role list and never create a persistent registry.

## Establish the project root

Use the nearest ancestor that contains `SOUL.md`, `ROLE.md`, `AGENTS.md`, and
`sub-agent-roles/`. Stop with the exact missing path if that root is not
unambiguous.

Run the helper with the project's Python environment. From the template root:

```bash
.venv/bin/python .agents/skills/manage-subagent-roles/scripts/role_catalog.py --repo-root . list --format json
```

On another platform, use that checkout's active project-environment Python.
Do not install a parser or another dependency for this workflow.

## Choose the requested mode

- **Inventory:** Return the current valid roles and invalid-role diagnostics.
- **Selection:** Inventory first, then choose the narrowest suitable valid
  role for a bounded task.
- **Creation:** Inventory and assess fit first; create a reusable role only
  when no existing valid role fits and the gap is a role gap.
- **Validation:** Validate structure, metadata, links, names, and role
  contracts.
- **Spawn:** Select or create a valid role, build a delegation contract, and
  use native Codex sub-agent tools.
- **Supervision and collection:** Steer, wait for, interrupt when necessary,
  collect, and review native child-agent results.

If the request is inventory only, return the catalog and stop without creating
or spawning anything. If it is creation only, validate and return the role and
stop without spawning.

## Inventory before other modes

Always run a fresh catalog inventory before selection, creation, or spawning.
Use JSON for internal decisions and a Markdown table for a human-facing list.

The result must return, for each valid role:

- Name.
- Description.
- Role folder.
- `AGENTS.md` path.
- `ROLE.md` path.
- Validity state.

Return invalid intended role folders separately with every diagnostic. Invalid
roles are never eligible for selection or spawning.

## Select by task fit

Build a task profile with:

- Objective.
- Required capabilities.
- Read and write needs.
- Expected output.
- Required Codex skills.
- Tool needs.
- Risk.
- Stopping condition.

Read the full `ROLE.md` and `AGENTS.md` only for plausible candidates. Compare
the profile with each candidate's purpose, suitable tasks, capabilities, tasks
outside the role, required Codex skills, and authority limits.

Exclude roles that lack a capability, required skill, tool, or authority. A
role capability is not the same as a Codex skill dependency. Check required
skills against the skills actually available to the current child-agent
environment; do not infer availability from a role declaration.

Prefer the narrowest suitable role. Return the selected role, both canonical
paths, alternatives considered, fit rationale, and residual limitations. Do
not force the general role onto specialized work merely because it is the
only valid role.

If no role fits, distinguish:

1. A reusable role-definition gap.
2. A missing Codex skill.
3. A missing tool or dependency.
4. Missing permission.
5. Work that should remain with the Project Director.

Only the first case enters role creation.

## Create a reusable role

Before creation, read
[the role schema](references/role-schema.md). Define the enduring
responsibility, descriptive slug, title, selection boundary, capabilities,
exclusions, required inputs, expected outputs, working method, validation
duties, required skills, authority limits, and escalation conditions.

Use the helper's `create` command. It renders the canonical templates,
rejects unsafe or existing targets, installs both role files as one logical
operation, validates the result, reruns inventory, and returns the new role.
Run `create --help` for the accepted fields.

Do not leave placeholders. Do not create a role for a transient ticket or task
identifier. Do not overwrite an existing path. Do not create a registry entry.
Do not install a missing skill, tool, plugin, or dependency.

## Validate a catalog or role

Use:

```bash
.venv/bin/python .agents/skills/manage-subagent-roles/scripts/role_catalog.py --repo-root . validate --format markdown
.venv/bin/python .agents/skills/manage-subagent-roles/scripts/role_catalog.py --repo-root . show ROLE_NAME --format json
```

Validation fails closed for an absent role root, an incomplete pair, malformed
metadata, a name mismatch, a duplicate name, a broken required link, an
incomplete role contract, an unsafe path, or an invalid creation target.

## Build the delegation contract

Before spawning, specify:

1. Selected role name and repository-relative `AGENTS.md` and `ROLE.md` paths.
2. Root `SOUL.md` as the shared behavioral source.
3. One concrete objective.
4. Necessary context and inputs.
5. Allowed scope.
6. Protected files, behavior, decisions, and external actions.
7. Exact deliverable.
8. Required checks.
9. Evidence to return.
10. Authority limits.
11. Explicit stopping condition.
12. Exact Project Director model inheritance with no override.
13. Exact Project Director reasoning-effort inheritance with no override.

The spawn prompt must instruct the child to read, before task work:

1. Root `SOUL.md`.
2. The selected role's `AGENTS.md`.
3. The selected role's `ROLE.md`.
4. The complete delegation contract.

Do not assume that Codex automatically loaded the role-specific nested
`AGENTS.md`. Codex discovers a nested `AGENTS.md` automatically only when that
file is on the path from the project root to the session's current working
directory. A child spawned from the project root must receive the selected
role-file paths and explicit read instructions in its delegation prompt.

## Spawn through native Codex orchestration

Use the native sub-agent operations available in the current Codex runtime,
such as `spawn_agent`, `list_agents`, `send_message` or `followup_task`,
`wait_agent`, and `interrupt_agent`.

- Give each child one bounded objective.
- Preserve the returned child identifier.
- Set `fork_turns` to `all`.
- Omit the `model` and `reasoning_effort` spawn arguments. The child must
  inherit the exact model and reasoning effort used by the Project Director.
- Do not select a custom-agent file that sets `model` or
  `model_reasoning_effort`.
- Do not use `agents.default_subagent_model` or
  `agents.default_subagent_reasoning_effort` for role-based children.
- Before spawning, check whether effective user or project configuration can
  override either inherited value. If the runtime cannot guarantee exact
  inheritance, stop and report the conflict without changing user
  configuration.
- Respect the runtime's current concurrency limit.
- Run parallel children only for independent work with non-overlapping write
  ownership.
- Do not shell out to another Codex process.
- Do not create a user-visible task or thread as a substitute for a child
  agent.
- Do not authorize nested delegation unless the Project Director explicitly
  requires it.

## Supervise and collect

Steer an existing child when material context or scope changes. Do not spawn a
duplicate agent to avoid clarification. Interrupt only for a clear safety,
scope, duplication, or invalid-assumption reason.

Wait for every result required for integration. Require each child to return:

- Outcome.
- Evidence and paths.
- Files changed.
- Checks run and observed results.
- Failures or uncertainty.
- Unresolved items.
- Whether the stopping condition was reached.

The Project Director must inspect material artifacts and current project state,
resolve conflicts, and run proportionate checks before accepting a result.
A child completion message is not proof of project completion.

## Failure behavior

Fail closed and report the smallest corrective action when:

- No valid suitable role exists.
- A required skill, tool, permission, dependency, or concurrency slot is
  unavailable.
- Role files are incomplete or contradictory.
- Creation would overwrite or escape the role root.
- Native sub-agent orchestration is unavailable.
- The child's model or reasoning effort would differ from the Project
  Director's current settings.
- The requested action exceeds current authority.
