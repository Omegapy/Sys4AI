# Sub-Agent Role Bundle Schema

Read this reference when creating a role, validating a role, or diagnosing why
a role is ineligible. The role system is a project-owned convention modeled on
Codex skill discovery. Codex does not natively discover arbitrary `ROLE.md`
files.

## Canonical layout

Each immediate child of `sub-agent-roles/` is one reusable role:

```text
sub-agent-roles/
`-- descriptive-role-name/
    |-- AGENTS.md
    `-- ROLE.md
```

The two files are the canonical role bundle. Do not add a registry, database,
CSV, generated index, or native custom-agent TOML file for the initial system.

## Directory and role name

- Use lowercase ASCII letters, digits, and single hyphens.
- Begin and end with a letter or digit.
- Keep the slug under 64 characters.
- Make the name describe an enduring responsibility.
- Do not use a hidden name, absolute path, path separator, traversal segment,
  transient ticket identifier, or opaque ordinal such as `agent-1`.
- The `ROLE.md` metadata name must equal the directory name.
- Role names must be unique across the live catalog.

The enforced pattern is:

```text
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

## ROLE.md discovery metadata

Put a flat YAML frontmatter block at the first line:

```markdown
---
name: descriptive-role-name
description: State when this role fits and an important boundary that prevents misrouting.
---
```

Only `name` and `description` are permitted in this initial schema.

- Both values are single-line, non-empty strings.
- The description must identify when to use the role.
- The description must include a meaningful boundary such as `not`, `only`,
  `unless`, `outside`, or an equivalent `when` condition.
- Detailed capabilities and constraints belong in the Markdown body, not the
  discovery metadata.

## Required ROLE.md body

Use one human-readable H1 followed by every exact H2:

1. `## Purpose`
2. `## Suitable tasks`
3. `## Capabilities`
4. `## Tasks outside the role`
5. `## Required Codex skills`
6. `## Expected inputs`
7. `## Expected outputs`
8. `## Working method`
9. `## Validation responsibilities`
10. `## Authority limits`
11. `## Escalation and stopping conditions`
12. `## Result-reporting contract`

Each section must contain substantive content. Do not leave scaffold markers,
empty lists, or TODO text.

The `Required Codex skills` section can state that no skill is required. If it
names a skill, the Project Director must verify that the skill is available to
the spawned child. Declaring a skill does not install or grant it.

## Required AGENTS.md contract

The role-specific `AGENTS.md` must:

- Use the visible H1 `Sub-Agent Instructions`.
- Include `## Required first reads`.
- Link to root `SOUL.md` with the exact relative target `../../SOUL.md`.
- Link to local `ROLE.md` with the exact relative target `./ROLE.md`.
- Require reading both sources and the delegation contract before work.
- Include `## Delegated-work rules`.
- Limit work to the delegated objective and scope.
- Preserve protected content and authority limits.
- Require evidence and checks in the result.
- Require the child to stop at the delegated stopping condition.
- Require the exact model and reasoning effort inherited from the Project
  Director and prohibit overrides.
- Prohibit nested sub-agents unless the Project Director explicitly grants
  that authority.

Both links must resolve to regular files inside the project.

Codex does not recursively load every descendant `AGENTS.md`. A nested role
file is automatically discovered only when it is on the path from the project
root to the session's current working directory. Role-based children spawned
from the project root must therefore be told explicitly to read their selected
role's `AGENTS.md` and `ROLE.md` before task work.

## Creation input contract

The catalog helper's `create` command requires:

- Role name.
- Human-readable title.
- Selection description.
- Purpose.
- At least one suitable task.
- At least one capability.
- At least one task outside the role.
- At least one expected input.
- At least one expected output.
- At least one working-method step.
- At least one validation duty.
- At least one authority limit.
- At least one escalation condition.
- Zero or more required Codex skills.

Example command shape:

```bash
.venv/bin/python .agents/skills/manage-subagent-roles/scripts/role_catalog.py \
  --repo-root . create documentation-reviewer \
  --title "Documentation Reviewer Role" \
  --description "Use for source-grounded documentation review, not for implementation changes." \
  --purpose "Review project documentation against its authoritative sources." \
  --suitable-task "Review documentation against supplied sources." \
  --capability "Source-grounded documentation review." \
  --outside-task "Application-code implementation." \
  --expected-input "The document and its authoritative sources." \
  --expected-output "Findings with exact file references." \
  --working-method "Compare each material claim with its source." \
  --validation-duty "Verify every reported finding against the current file." \
  --authority-limit "Do not edit files unless the delegation contract authorizes it." \
  --escalation-condition "Stop when an authoritative source is missing." \
  --format json
```

The helper renders `assets/role-bundle/AGENTS.md.template` and
`assets/role-bundle/ROLE.md.template`, creates both files in a temporary
directory under the role root, reserves the final directory with a
fail-if-present operation, moves both completed files into it, validates the
live catalog, and removes only its own incomplete output if creation fails.

## Catalog states

A **valid role** has:

- A safe descriptive directory name.
- Exactly one regular `AGENTS.md`.
- Exactly one regular `ROLE.md`.
- Valid matching metadata.
- Every required role section.
- Both required resolving links.
- No duplicate metadata name.

An **invalid role** remains visible in inventory diagnostics but cannot be
selected, shown as valid, created over, or spawned.

## Fit assessment

The Project Director creates a task profile with objective, capabilities,
read/write needs, expected output, required skills, tools, risk, and stopping
condition. The Project Director then:

1. Excludes invalid bundles.
2. Reads full files for plausible candidates.
3. Compares capabilities and explicit exclusions.
4. Verifies required Codex skills and tools in the current environment.
5. Checks authority and scope compatibility.
6. Prefers the narrowest suitable role.
7. Returns the selected role, both paths, alternatives, rationale, and
   limitations.

If no role fits, classify the gap before acting. Create a role only for a
reusable role-definition gap. A missing skill, tool, dependency, permission,
or native runtime capability is a blocker, not a reason to invent a role.

## Model and reasoning identity

Every role-based child is a model-and-reasoning copy of the Project Director.
The selected role changes the child's instructions and bounded objective only.

For a runtime with `spawn_agent`, set `fork_turns` to `all` and omit the
`model` and `reasoning_effort` arguments. Do not use a custom-agent file or an
effective `agents.default_subagent_model` or
`agents.default_subagent_reasoning_effort` setting that replaces the parent's
values.

Check the effective project and user configuration before spawning. If the
runtime cannot guarantee that both values match the Project Director exactly,
the role is not spawnable in that runtime. Report the conflict. Do not silently
use a different model, lower or raise reasoning effort, or change user-level
configuration.

## Activation contract

The role catalog is not automatic Codex role discovery. Activation occurs only
when the Project Director:

1. Runs fresh inventory.
2. Selects or creates and validates a suitable role.
3. Builds a bounded delegation contract.
4. Explicitly tells the native child to read root `SOUL.md`, role
   `AGENTS.md`, and role `ROLE.md`.
5. Confirms exact parent model and reasoning inheritance.
6. Uses native Codex sub-agent orchestration without model or reasoning
   overrides.
7. Reviews and verifies the returned result.
