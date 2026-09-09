# Project Director and Sub-Agent Role System Implementation Plan

## Document control

- **Status:** Proposed implementation plan
- **Plan date:** 2026-08-27
- **Target project:** Generic Template Project
- **Project root:** `/Volumes/P-SSD/Template-Project`
- **Implementation authority:** This document authorizes planning only. It does not authorize implementation.
- **Primary purpose:** Define a generic, reusable Project Director role, a discoverable sub-agent role system, and a project-local Codex skill that lists, selects, creates, and spawns suitable sub-agents.

## 1. Executive intent

The template must establish a project-management architecture in which the main
agent acts as the **Project Director**. The Project Director owns task analysis,
decomposition, delegation, coordination, review, integration, verification, and
the final project-level response. Sub-agents perform bounded project work under
roles selected by the Project Director.

The architecture must include:

1. A generic root-level `ROLE.md` for the Project Director.
2. A root-level `sub-agent-roles/` directory containing one directory per
   reusable sub-agent role.
3. Exactly one role-specific `AGENTS.md` and one role-specific `ROLE.md` in
   every valid sub-agent role directory.
4. A generic initial role whose visible Markdown title is exactly
   **Sub-Agent Project Role**.
5. A project-local Codex skill that treats the role directories as a live role
   catalog.
6. A discovery-first workflow that returns every existing valid role with the
   paths to its `AGENTS.md` and `ROLE.md` files.
7. A fit check that prevents the Project Director from assigning a role that
   lacks the capability or required Codex skill for the delegated task.
8. A role-creation workflow used only when no existing valid role fits.
9. Native Codex sub-agent spawning, supervision, and result collection after a
   suitable role is selected or created.

The role catalog will be filesystem-backed. This version will not add a
separate registry, database, manifest, or persistent usage tracker.

## 2. Scope boundary for this plan

### 2.1 In scope for the later implementation

- Create and populate the root `ROLE.md`.
- Update the root `AGENTS.md` only where needed to connect the Project
  Director role and the role-management skill.
- Create `sub-agent-roles/`.
- Create the initial `project-sub-agent/` role bundle.
- Create a repository-local `manage-subagent-roles` skill.
- Define role metadata, role discovery, validation, fit assessment, creation,
  spawning, supervision, and completion behavior.
- Add proportionate deterministic validation and behavioral checks.
- Document the compatibility boundary between project-defined roles and native
  Codex features.

### 2.2 Out of scope for the later initial implementation

- A central role registry file, database, CSV, or persistent index.
- Role usage history, performance scoring, or audit analytics.
- Automatic plugin installation.
- Automatic installation of a missing Codex skill.
- A remote service or external role catalog.
- Global user-level skills or global user-level custom agents.
- Creating a new role for every task when an existing role is suitable.
- Unbounded nested delegation by sub-agents.
- Replacing the native Codex sub-agent runtime with shell-launched Codex
  processes.
- Committing, publishing, or deploying the implementation.
- Creating domain-specific roles beyond the one requested generic seed role.

### 2.3 Explicit current-turn boundary

This plan is the only artifact to be created in the current task. The root
role, sub-agent role files, skill, scripts, and tests described below must be
created only in a later implementation task.

## 3. Observed project baseline

The implementation must start from the observed project state, not from an
assumed repository layout.

| Item | Observed state | Consequence |
| --- | --- | --- |
| Root `AGENTS.md` | Exists | Preserve it and make only the smallest required integration edit. |
| Root `SOUL.md` | Exists | It remains the shared behavioral source for the director and all sub-agents. |
| Root `ROLE.md` | Missing | The implementation must create it. |
| Root `README.md` | Exists | Add role-system documentation only if needed; do not recast unrelated Python setup text. |
| `sub-agent-roles/` | Missing | The implementation must create it. |
| Repository-local role-management skill | Missing | The implementation must create it. |
| Python environment | `.venv` exists | Use it for any Python validation helpers. |
| Git repository | Not currently detected | Do not claim staged, committed, or tracked status unless that state changes and is verified. |
| Communication skill referenced by `SOUL.md` | Referenced path is currently missing | Do not silently invent or replace that unrelated skill in this implementation. |

## 4. Authority and source precedence

The later implementation must use this precedence:

1. Platform, safety, permission, and tool constraints.
2. The user's approved implementation request.
3. Root `SOUL.md`.
4. Root `ROLE.md` for the Project Director.
5. Root `AGENTS.md`.
6. The selected sub-agent role's `AGENTS.md` and `ROLE.md`.
7. The role-management skill and its supporting schema.
8. The bounded delegation prompt for the current task.

A lower source can specialize a higher source but must not silently contradict
or weaken it.

## 5. Codex compatibility basis

The design must align with current official Codex conventions while clearly
labeling the project-defined extension.

### 5.1 Official behaviors used

- Codex skills use progressive disclosure: name and description are available
  for discovery, and the full `SKILL.md` is loaded when selected.
- A skill requires a folder containing `SKILL.md` with `name` and
  `description` frontmatter.
- Repository-local Codex skills are discovered under `.agents/skills/`.
- Codex discovers `AGENTS.md` instructions by walking from the project root
  toward the current working directory.
- Current Codex clients can spawn sub-agents after a direct request or
  applicable project or skill instruction.
- Native sub-agent orchestration includes spawning, steering, waiting for
  results, interruption, and consolidation.
- Project-scoped native custom-agent TOML files can exist in `.codex/agents/`,
  but they are a separate native configuration mechanism.

Official sources:

- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

### 5.2 Project-defined extension

Codex does not natively advertise arbitrary `ROLE.md` files as a role catalog.
Therefore:

- `sub-agent-roles/` will be a project-owned convention.
- YAML frontmatter in each role's `ROLE.md` will be a project-owned discovery
  schema modeled on Codex skill metadata.
- The `manage-subagent-roles` skill will perform role discovery and validation.
- The skill will explicitly direct a spawned sub-agent to read the selected
  role bundle.
- The implementation must not claim that Codex automatically discovers or
  activates these role bundles without the skill workflow.

### 5.3 Initial decision about native custom-agent TOML files

The first implementation will not require one `.codex/agents/name.toml` file
per role. Requiring a third canonical file would duplicate role metadata and
create a synchronization problem that the user did not request.

The canonical role bundle will remain:

1. `AGENTS.md`
2. `ROLE.md`

If a later role requires native per-agent model, reasoning, sandbox, MCP, or
skill configuration, a later plan may add a generated TOML adapter. The role
bundle must remain the source of truth if that extension is approved.

## 6. Terms

| Term | Meaning |
| --- | --- |
| Project Director | The main agent governed by the root `ROLE.md`. |
| Sub-agent | A native Codex child agent spawned for one bounded delegated objective. |
| Role bundle | One immediate child directory of `sub-agent-roles/` containing both `AGENTS.md` and `ROLE.md`. |
| Role metadata | The required name and description frontmatter at the top of a role's `ROLE.md`. |
| Role catalog | The live set of role bundles discovered from the filesystem on the current invocation. |
| Valid role | A role bundle that passes structure, metadata, link, naming, and content validation. |
| Suitable role | A valid role whose capabilities, boundaries, and available Codex skills fit a delegated task. |
| Required Codex skill | A discoverable Codex skill that the delegated task or role explicitly requires. |
| Capability | A kind of work the role is authorized and designed to perform. |
| Delegation contract | The bounded task prompt supplied to a spawned sub-agent. |
| Role creation | Creation of a new reusable role bundle because no existing valid role is suitable. |

## 7. Requirement catalog

### 7.1 Project Director requirements

- **DIR-001:** Create `/ROLE.md` in the project root.
- **DIR-002:** Use the visible title **Project Director Role** in root
  `ROLE.md`.
- **DIR-003:** Keep the Project Director role generic so repositories created
  from the template can specialize it later.
- **DIR-004:** Define the Project Director as the primary project coordinator,
  not as a domain-specific worker.
- **DIR-005:** Require the Project Director to inspect the task, project
  guidance, current state, risks, and available roles before delegation.
- **DIR-006:** Require the Project Director to decide whether a task must be
  decomposed and which parts can run independently.
- **DIR-007:** Require substantive delegable project work to be assigned to
  suitable sub-agents.
- **DIR-008:** Allow the Project Director to perform director-level work such
  as scoping, decisions, coordination, conflict resolution, integration, and
  final verification.
- **DIR-009:** Prevent the Project Director from delegating merely to create
  activity when delegation adds no value or the runtime does not permit it.
- **DIR-010:** Require the Project Director to invoke the
  `manage-subagent-roles` skill before selecting, creating, or spawning a
  role-based sub-agent.
- **DIR-011:** Require the Project Director to use the skill's returned live
  catalog rather than relying on remembered role names.
- **DIR-012:** Require the Project Director to retain accountability for
  delegated scope, permissions, output review, integration, verification, and
  the final response.
- **DIR-013:** Require one bounded objective and one explicit stopping
  condition per delegated sub-agent.
- **DIR-014:** Require non-overlapping write ownership when multiple sub-agents
  run in parallel.
- **DIR-015:** Require the Project Director to wait for required results,
  inspect them, resolve conflicts, and reject unsupported conclusions.
- **DIR-016:** Prohibit the Project Director from treating a sub-agent's
  completion message as proof that the project state is correct.
- **DIR-017:** Require direct reinspection or proportionate validation of
  material delegated changes before final acceptance.
- **DIR-018:** Require the Project Director to report when no suitable role,
  required Codex skill, tool, permission, or concurrency slot is available.

### 7.2 Role directory and bundle requirements

- **ROL-001:** Create the root directory `/sub-agent-roles/`.
- **ROL-002:** Store each sub-agent role in its own immediate child directory.
- **ROL-003:** Use a lowercase, hyphen-separated, descriptive child-directory
  name that indicates what the role does.
- **ROL-004:** Do not use opaque names such as `agent-1` or `role-a`.
- **ROL-005:** Require exactly one `AGENTS.md` and exactly one `ROLE.md` at
  the root of each valid role directory.
- **ROL-006:** Treat the two-file pair as the minimum canonical role bundle.
- **ROL-007:** Require each role-specific `AGENTS.md` to contain a relative
  Markdown link to the root `SOUL.md`.
- **ROL-008:** Require each role-specific `AGENTS.md` to contain a relative
  Markdown link to its sibling `ROLE.md`.
- **ROL-009:** Require the role-specific `AGENTS.md` to instruct the sub-agent
  to read both linked files before performing delegated work.
- **ROL-010:** Require the role-specific `AGENTS.md` to enforce delegated
  scope, evidence reporting, authority limits, and the stopping condition.
- **ROL-011:** Require the role-specific `ROLE.md` to define purpose,
  capabilities, boundaries, expected inputs, expected outputs, validation
  duties, and escalation conditions.
- **ROL-012:** Require role folders to be reusable project roles, not one-off
  task records.
- **ROL-013:** Prevent a role creation operation from overwriting or merging
  into an existing role directory.
- **ROL-014:** Detect duplicate role names even when they occur in different
  folders.
- **ROL-015:** Treat incomplete, malformed, or duplicate role bundles as
  invalid and ineligible for spawning.

### 7.3 Generic initial role requirements

- **GEN-001:** Create the initial role directory
  `/sub-agent-roles/project-sub-agent/`.
- **GEN-002:** Create
  `/sub-agent-roles/project-sub-agent/AGENTS.md`.
- **GEN-003:** Create
  `/sub-agent-roles/project-sub-agent/ROLE.md`.
- **GEN-004:** Use the exact visible H1 title **Sub-Agent Project Role** inside
  the generic role's `ROLE.md`.
- **GEN-005:** Keep the filename `ROLE.md`; do not use the visible title as
  the filename.
- **GEN-006:** Define the initial role as a general-purpose worker for bounded
  project analysis, implementation, documentation, and verification.
- **GEN-007:** Keep the initial role generic and reusable rather than embedding
  assumptions about a particular language, framework, company, or domain.
- **GEN-008:** Require the generic sub-agent to follow the root `SOUL.md`, its
  role, and the delegation contract.
- **GEN-009:** Prevent the generic role from making Project Director decisions
  or expanding its own authority.
- **GEN-010:** Prevent the generic role from creating nested sub-agents unless
  the Project Director explicitly delegates that authority.

### 7.4 Role metadata and discovery requirements

- **MET-001:** Put YAML frontmatter at the top of every role-specific
  `ROLE.md`.
- **MET-002:** Require the frontmatter fields `name` and `description`,
  matching the minimum discovery pattern used by Codex skills.
- **MET-003:** Require `name` to equal the role directory slug.
- **MET-004:** Require `description` to state when the role should be used and
  include enough boundary language to prevent obvious misrouting.
- **MET-005:** Keep detailed capabilities and constraints in the Markdown body
  so only concise discovery metadata must be read during initial inventory.
- **MET-006:** Scan the live filesystem on every inventory request.
- **MET-007:** Do not require a generated registry, role index, database, or
  tracking file in the first implementation.
- **MET-008:** Inspect every immediate child directory of
  `sub-agent-roles/`, including incomplete directories, so diagnostics are
  not hidden.
- **MET-009:** Return valid and invalid entries separately.
- **MET-010:** For every valid entry, return role name, description, role
  folder, `AGENTS.md` path, `ROLE.md` path, and validity state.
- **MET-011:** For every invalid entry, return the folder, missing or malformed
  item, and corrective diagnostic.
- **MET-012:** Use repository-relative paths in normal output and resolved
  paths during validation.
- **MET-013:** Sort returned entries deterministically by role name and then
  folder path.
- **MET-014:** Support structured JSON output for deterministic use and a
  concise Markdown table for human-facing use.
- **MET-015:** Never silently omit an invalid role that appears to be intended
  as a role bundle.

### 7.5 Role fit and selection requirements

- **FIT-001:** Convert the delegated task into a small task profile containing
  objective, required capabilities, read/write needs, expected output,
  required Codex skills, tool needs, risk, and stopping condition.
- **FIT-002:** Exclude invalid role bundles before semantic matching.
- **FIT-003:** Compare the task profile against each candidate role's
  description, capabilities, boundaries, and required-skills section.
- **FIT-004:** Treat a role as unsuitable when it lacks a required capability.
- **FIT-005:** Treat a role as unsuitable when the delegated task requires a
  Codex skill that is unavailable to the spawned agent.
- **FIT-006:** Distinguish a role capability from a Codex `SKILL.md`
  dependency; they are related but not interchangeable.
- **FIT-007:** Prefer the narrowest suitable role over a broad role when both
  fit.
- **FIT-008:** Return the selected role, alternatives considered, fit
  rationale, and any residual limitation.
- **FIT-009:** Do not force the generic role onto specialized work merely
  because it is the only valid role.
- **FIT-010:** If no role fits because only the role definition is missing,
  enter the role-creation workflow.
- **FIT-011:** If no role fits because a required Codex skill, tool,
  permission, or external dependency is unavailable, report that blocker;
  creating a new role must not pretend to provide the missing capability.

### 7.6 Local skill requirements

- **SKL-001:** Create the repository-local skill at
  `/.agents/skills/manage-subagent-roles/`.
- **SKL-002:** Name the skill `manage-subagent-roles`.
- **SKL-003:** Create the required
  `/.agents/skills/manage-subagent-roles/SKILL.md`.
- **SKL-004:** Give `SKILL.md` valid YAML frontmatter with required
  `name` and `description` fields.
- **SKL-005:** Front-load the description with the skill's primary purpose:
  discover and return existing sub-agent roles with their `AGENTS.md` and
  `ROLE.md` paths.
- **SKL-006:** Include selection, role creation, spawning, supervision, and
  result collection as secondary supported modes.
- **SKL-007:** Keep automatic discovery enabled while also requiring the
  Project Director to invoke the skill explicitly for role-based delegation.
- **SKL-008:** Use progressive disclosure: short routing in `SKILL.md` and
  detailed role schema in a supporting reference.
- **SKL-009:** Create `references/role-schema.md` for the canonical bundle
  schema, metadata, validation rules, and examples.
- **SKL-010:** Create a deterministic, standard-library-only role catalog
  helper under `scripts/`.
- **SKL-011:** Use the existing project Python environment to run the helper.
- **SKL-012:** Avoid adding a third-party parser dependency solely for the
  two-field frontmatter schema.
- **SKL-013:** Create role bundle templates under `assets/` only if the final
  creation workflow uses them.
- **SKL-014:** Do not add a skill-specific README, changelog, or unrelated
  support files.
- **SKL-015:** Provide explicit modes for inventory, selection, creation,
  spawning, and validation.
- **SKL-016:** Make inventory the first operation for selection, creation, or
  spawning.
- **SKL-017:** If invoked only to list roles, return the catalog and do not
  create or spawn anything.
- **SKL-018:** If invoked to create a role, validate and return the new role
  but do not spawn it unless the director's task also requires spawning.
- **SKL-019:** If invoked to spawn, require a valid suitable role and a bounded
  delegation contract first.
- **SKL-020:** Use native Codex sub-agent tools rather than shelling out to a
  second Codex process.

### 7.7 Role creation requirements

- **CRT-001:** Create a new role only after a fresh inventory and fit check
  finds no suitable existing role.
- **CRT-002:** Derive a descriptive lowercase hyphenated role name from the
  enduring responsibility, not from a transient task identifier.
- **CRT-003:** Define the role's purpose, positive capabilities, exclusions,
  required inputs, output contract, validation duties, required Codex skills,
  escalation conditions, and authority boundary before creating files.
- **CRT-004:** Create the new role directory and both required files as one
  logical operation.
- **CRT-005:** Populate `ROLE.md` frontmatter with a unique matching name and
  discriminating description.
- **CRT-006:** Put a human-readable role title in the body of `ROLE.md`.
- **CRT-007:** Populate the new `AGENTS.md` with links to root `SOUL.md` and
  local `ROLE.md`.
- **CRT-008:** Use relative links that resolve from the role directory.
- **CRT-009:** Fail closed if the target directory or either file already
  exists.
- **CRT-010:** Reject path traversal, absolute output paths, empty names,
  hidden directory names, and names that do not match the slug policy.
- **CRT-011:** Validate the new bundle immediately after creation.
- **CRT-012:** Re-run inventory and return the new valid role before it can be
  selected or spawned.
- **CRT-013:** Do not create a separate catalog or tracking entry.
- **CRT-014:** Do not install a missing skill or plugin as an implicit part of
  role creation.

### 7.8 Native spawning and supervision requirements

- **SPN-001:** Use Codex's native sub-agent orchestration tools.
- **SPN-002:** Give every spawned agent one concrete bounded subtask.
- **SPN-003:** Include the selected role name and repository-relative bundle
  paths in the spawn prompt.
- **SPN-004:** Explicitly instruct the child to read root `SOUL.md`, the
  selected role's `AGENTS.md`, and the selected role's `ROLE.md` before task
  work.
- **SPN-005:** Include objective, context, inputs, allowed scope, protected
  files or behavior, expected deliverable, required checks, authority limits,
  evidence requirements, and stopping condition in the delegation contract.
- **SPN-006:** Require every role-based child to inherit the Project
  Director's exact model and reasoning effort by setting `fork_turns` to
  `all` and omitting model and reasoning overrides.
- **SPN-007:** Respect the current runtime's concurrency limit; do not encode a
  machine-specific fixed limit in the template.
- **SPN-008:** Parallelize only independent work with non-overlapping write
  ownership.
- **SPN-009:** Use follow-up or steering operations for material clarification
  instead of spawning duplicate agents for the same unresolved objective.
- **SPN-010:** Wait for all sub-agent results required by the task before
  integration.
- **SPN-011:** Interrupt a sub-agent only for a clear scope, safety,
  duplication, or invalid-assumption reason.
- **SPN-012:** Require each sub-agent result to identify work completed,
  evidence, files changed, checks run, failures, uncertainty, and unresolved
  items.
- **SPN-013:** Require the Project Director to review actual artifacts and
  current state after sub-agent completion.
- **SPN-014:** Prevent sub-agents from silently authorizing external,
  destructive, publishing, dependency-installation, or architecture-changing
  actions.
- **SPN-015:** Do not use user-visible separate Codex tasks as a substitute for
  child sub-agents.
- **SPN-016:** Before spawning, confirm that effective user defaults, project
  defaults, and custom-agent configuration cannot replace the inherited model
  or reasoning effort. If exact inheritance cannot be guaranteed, fail closed
  without spawning or modifying user-level configuration.

### 7.9 Verification and documentation requirements

- **VER-001:** Validate the root role, role bundles, skill, and links
  independently.
- **VER-002:** Validate the skill with the bundled skill validator.
- **VER-003:** Validate catalog behavior with focused standard-library tests.
- **VER-004:** Test empty, valid, incomplete, malformed, duplicate, and
  traversal-like role cases.
- **VER-005:** Test that the generic role is returned with both required paths.
- **VER-006:** Test that invalid roles are reported but cannot be selected.
- **VER-007:** Test that creation refuses an existing target.
- **VER-008:** Test that generated relative links resolve to the intended
  files.
- **VER-009:** Test that listing alone causes no project mutation.
- **VER-010:** Test the no-fit path and the unavailable-required-skill path as
  distinct outcomes.
- **VER-011:** Perform one read-only native sub-agent smoke test after static
  and focused tests pass.
- **VER-012:** In the smoke test, require the child to report the three
  instruction sources it read and return a bounded result.
- **VER-013:** Inspect the final project tree and all changed file contents.
- **VER-014:** Verify that no role registry or tracking file was added.
- **VER-015:** Review the final change boundary for unrelated edits.
- **VER-016:** State the highest verification level actually achieved and any
  unverified runtime behavior.

## 8. Proposed file architecture

~~~text
Template-Project/
|-- AGENTS.md
|-- SOUL.md
|-- ROLE.md
|-- README.md
|-- sub-agent-roles/
|   `-- project-sub-agent/
|       |-- AGENTS.md
|       `-- ROLE.md
|-- .agents/
|   `-- skills/
|       `-- manage-subagent-roles/
|           |-- SKILL.md
|           |-- agents/
|           |   `-- openai.yaml
|           |-- references/
|           |   `-- role-schema.md
|           |-- scripts/
|           |   `-- role_catalog.py
|           |-- assets/
|           |   `-- role-bundle/
|           |       |-- AGENTS.md.template
|           |       `-- ROLE.md.template
|           `-- tests/
|               `-- test_role_catalog.py
`-- Implementation_Plans/
    `-- subagent_role_system_implementation_plan.md
~~~

The `assets/` directory is conditional. Keep it only if creation reads the
templates directly. If the final skill can create the two files clearly and
reliably without templates, omit `assets/` and its files.

The `agents/openai.yaml` file is optional Codex skill UI metadata. If created
by the official initializer, keep only accurate display metadata and the
default implicit-invocation policy. Do not add unsupported dependencies.

## 9. Canonical file specifications

### 9.1 Root ROLE.md

The root file must contain these sections:

1. **Project Director Role**
2. **Purpose**
3. **Primary responsibilities**
4. **Authority and non-authority**
5. **Task assessment and decomposition**
6. **Mandatory role-management skill workflow**
7. **Role selection and role creation**
8. **Delegation contract**
9. **Model and reasoning identity**
10. **Parallel-work ownership**
11. **Supervision and steering**
12. **Review and integration**
13. **Verification and validation**
14. **Escalation and stopping conditions**
15. **Completion report**

The mandatory skill section must name `manage-subagent-roles` and state that
the Project Director must use it to obtain a fresh role catalog before
role-based delegation.

The role must keep a clean responsibility split:

- **Project Director owns:** intent, decomposition, role choice, task
  boundaries, permissions, coordination, integration decisions, final
  verification, and final reporting.
- **Sub-agent owns:** the bounded delegated objective, evidence collection,
  authorized edits, focused checks, and a structured result.

### 9.2 Root AGENTS.md integration

The current root `AGENTS.md` already requires reading `SOUL.md` and `ROLE.md`.
The implementation should:

- Preserve those required first reads.
- Correct only wording needed for clarity.
- Add a short director/delegation instruction only if root `ROLE.md` alone is
  not reliably sufficient.
- Link the Project Director to the local role-management skill if a direct
  link improves discoverability.
- Avoid duplicating the entire director workflow in `AGENTS.md`.

### 9.3 Role-specific AGENTS.md

Every role-specific `AGENTS.md` must use a structure equivalent to:

~~~markdown
# Sub-Agent Instructions

## Required first reads

1. Read the [project soul](../../SOUL.md).
2. Read this sub-agent's [role definition](./ROLE.md).

## Delegated-work rules

- Work only on the objective and paths assigned by the Project Director.
- Follow the authority and stopping condition in the delegation contract.
- Report evidence, checks, uncertainty, and unresolved items.
- Do not create nested sub-agents unless the Project Director explicitly
  authorizes it.
~~~

The final wording may be refined, but both relative links and both read
requirements are invariant.

Codex does not recursively load every descendant `AGENTS.md`. It automatically
discovers a nested `AGENTS.md` only when that file is on the path from the
project root to the session's current working directory. Because role-based
children are spawned from the project root, their delegation prompts must
explicitly require reading the selected role's `AGENTS.md` and `ROLE.md`.

### 9.4 Role-specific ROLE.md

Every role-specific `ROLE.md` must begin with:

~~~markdown
---
name: descriptive-role-slug
description: State when this role should be selected and its important boundary.
---
~~~

The body must contain:

1. Human-readable H1 role title.
2. Purpose.
3. Suitable tasks.
4. Capabilities.
5. Tasks outside the role.
6. Required Codex skills, if any.
7. Expected inputs.
8. Expected outputs.
9. Working method.
10. Validation responsibilities.
11. Authority limits.
12. Escalation and stopping conditions.
13. Result-reporting contract.

### 9.5 Initial generic ROLE.md

The initial role must use:

~~~markdown
---
name: project-sub-agent
description: General-purpose sub-agent for bounded project analysis, implementation, documentation, and verification when no narrower specialized role is required.
---

# Sub-Agent Project Role
~~~

The title is exact. The remainder must remain generic and project-neutral.

## 10. Role metadata and progressive disclosure model

The role system will mirror the useful discovery behavior of Codex skills
without claiming native role support.

### Stage 1: Inventory

Read only:

- Role directory name.
- `ROLE.md` name.
- `ROLE.md` description.
- Presence of `AGENTS.md`.
- Presence of `ROLE.md`.

This is enough to return the catalog cheaply.

### Stage 2: Fit assessment

For candidates whose descriptions plausibly match, read the full:

- `ROLE.md`
- `AGENTS.md`

Compare capabilities, exclusions, required skills, output contract, and
authority limits against the delegated task profile.

### Stage 3: Activation

After selection:

- Include the role name and file paths in the delegation contract.
- Instruct the child to read root `SOUL.md` and both role files.
- Spawn through native Codex sub-agent orchestration.

## 11. Role catalog output contract

### 11.1 Human-facing output

The default inventory output must be a concise table:

| Role | Description | Folder | AGENTS.md | ROLE.md | State |
| --- | --- | --- | --- | --- | --- |
| project-sub-agent | General-purpose bounded project work | sub-agent-roles/project-sub-agent | sub-agent-roles/project-sub-agent/AGENTS.md | sub-agent-roles/project-sub-agent/ROLE.md | valid |

Invalid entries must appear in a separate diagnostics table.

### 11.2 Structured output

The helper must support JSON with an object equivalent to:

~~~json
{
  "schema_version": 1,
  "role_root": "sub-agent-roles",
  "valid_roles": [
    {
      "name": "project-sub-agent",
      "description": "General-purpose sub-agent for bounded project work.",
      "folder": "sub-agent-roles/project-sub-agent",
      "agents_file": "sub-agent-roles/project-sub-agent/AGENTS.md",
      "role_file": "sub-agent-roles/project-sub-agent/ROLE.md",
      "valid": true,
      "diagnostics": []
    }
  ],
  "invalid_roles": []
}
~~~

The JSON is an invocation result, not a persistent registry file.

## 12. Role catalog helper design

Create one cohesive standard-library script:

`.agents/skills/manage-subagent-roles/scripts/role_catalog.py`

### 12.1 Required commands

- **list:** Return valid and invalid role bundles.
- **validate:** Exit nonzero if any intended role bundle is invalid.
- **show NAME:** Return the selected role's metadata and canonical paths.

Role creation remains a skill workflow using templates and normal project file
editing. Do not place native sub-agent tool calls inside the Python script;
native tools are available to the Codex agent, not to the filesystem helper.

### 12.2 Discovery algorithm

1. Resolve the repository root supplied by the skill.
2. Resolve `sub-agent-roles/` beneath that root.
3. Refuse a role root that escapes the repository.
4. Enumerate immediate child directories only.
5. For each child, check for `AGENTS.md` and `ROLE.md`.
6. Read only the bounded frontmatter region from `ROLE.md`.
7. Parse the flat required fields `name` and `description`.
8. Verify name-to-directory equality.
9. Verify no duplicate role name exists.
10. Verify required relative links exist in `AGENTS.md` and resolve.
11. Add valid entries to `valid_roles`.
12. Add incomplete or malformed entries to `invalid_roles` with diagnostics.
13. Sort deterministically.
14. Print Markdown or JSON.
15. Perform no writes in **list**, **validate**, or **show** modes.

### 12.3 Parser boundary

The metadata schema is deliberately flat and small. The helper should parse
only:

- Opening and closing frontmatter delimiters.
- One-line `name`.
- One-line `description`.

The helper must reject multiline, duplicate, empty, or unsupported required
fields instead of attempting to become a general YAML parser. This avoids a
new dependency and keeps validation deterministic. Codex still receives valid
YAML frontmatter.

## 13. Skill behavior

### 13.1 Proposed skill description

The `SKILL.md` description should be equivalent to:

> Discover and return project sub-agent roles with their AGENTS.md and ROLE.md
> paths; use when the Project Director needs to select, create, validate, or
> spawn a role-based Codex sub-agent.

This wording front-loads the primary list-and-return behavior.

### 13.2 Inventory mode

1. Identify the project root.
2. Run the role catalog helper in list mode.
3. Return valid roles and invalid diagnostics.
4. Stop if the caller requested only inventory.
5. Do not modify files or spawn agents.

### 13.3 Selection mode

1. Run inventory first.
2. Build the bounded task profile.
3. Read full files only for plausible candidates.
4. Check capabilities, boundaries, required skills, and tool availability.
5. Return:
   - selected role;
   - both file paths;
   - fit rationale;
   - alternatives rejected;
   - missing capability or skill, if any.
6. If no role fits, route to creation or return a blocker.

### 13.4 Creation mode

1. Run inventory and fit assessment.
2. Confirm the gap is a reusable role gap, not a missing tool, skill, plugin,
   permission, or one-off task detail.
3. Define a descriptive role slug and role contract.
4. Check that the target does not exist.
5. Create the role directory.
6. Create `AGENTS.md` and `ROLE.md` from the canonical schema.
7. Populate all required content; do not leave TODO placeholders.
8. Validate the new bundle.
9. Re-run inventory.
10. Return the created role and both canonical paths.
11. Spawn only if spawning was part of the director's original workflow.

### 13.5 Spawn mode

1. Run inventory.
2. Select or create a suitable role.
3. Build the delegation contract.
4. Use the native spawn operation.
5. Track the returned child identifier.
6. Supervise, steer, wait, or interrupt through native operations as needed.
7. Collect the child's structured result.
8. Reinspect material artifacts.
9. Integrate or reject the result.
10. Report project-level completion only after director verification.

### 13.6 Failure behavior

The skill must fail closed for:

- Missing `sub-agent-roles/` when a list or selection is requested after
  implementation should have created it.
- Invalid role pair.
- Duplicate role name.
- Role metadata mismatch.
- Broken required link.
- Existing role-creation target.
- No suitable role.
- Missing required Codex skill.
- Missing native sub-agent capability.
- Permission or concurrency limitation.

The failure must state the exact condition and the smallest corrective action.

## 14. Delegation contract

Every spawned sub-agent prompt must include:

| Field | Required content |
| --- | --- |
| Role | Selected role name. |
| Model | Exact model currently used by the Project Director. |
| Reasoning effort | Exact reasoning effort currently used by the Project Director. |
| Instruction sources | Root `SOUL.md`, selected `AGENTS.md`, selected `ROLE.md`. |
| Objective | One concrete outcome. |
| Context | Only facts needed for the objective. |
| Inputs | Files, data, commands, or evidence sources to inspect. |
| Allowed scope | Files, systems, and actions the child may use. |
| Protected scope | Files, behavior, decisions, or external actions it must not change. |
| Deliverable | Exact output expected by the director. |
| Checks | Focused verification the child must perform. |
| Evidence | Paths, command outcomes, and uncertainty to report. |
| Authority | What the child may decide and what remains with the director. |
| Stop condition | The condition that ends the subtask. |

Example shape:

~~~text
Act as the project-sub-agent role for one bounded objective.

Spawn with `fork_turns` set to `all`. Do not pass `model` or
`reasoning_effort`; inherit both exact values from the Project Director.

Before working, read:
1. SOUL.md
2. sub-agent-roles/project-sub-agent/AGENTS.md
3. sub-agent-roles/project-sub-agent/ROLE.md

Objective: ...
Allowed scope: ...
Protected scope: ...
Deliverable: ...
Required checks: ...
Authority limits: ...
Stop when: ...

Return a concise result with evidence, files changed, checks run, failures,
uncertainty, and unresolved items.
~~~

## 15. Project Director operating workflow

### Phase A: Intake

1. Read project guidance.
2. Restate the requested outcome.
3. Identify constraints, protected content, permissions, and success criteria.
4. Inspect current project state.

### Phase B: Decomposition

1. Separate director-level decisions from executable subtasks.
2. Identify dependencies between subtasks.
3. Mark subtasks as independent or ordered.
4. Assign exclusive write ownership for parallel subtasks.

### Phase C: Role discovery

1. Invoke `manage-subagent-roles`.
2. Obtain a fresh role catalog.
3. Review invalid-role diagnostics.
4. Build a task profile for each delegable subtask.

### Phase D: Role selection or creation

1. Match each task profile to valid roles.
2. Reject roles missing required capabilities or skills.
3. Select the narrowest suitable role.
4. If no role fits, distinguish:
   - reusable role gap;
   - missing Codex skill;
   - missing tool;
   - permission gap;
   - task that should remain with the director.
5. Create a role only for a reusable role gap.
6. Validate and relist the role before selection.

### Phase E: Delegation

1. Build one delegation contract per child.
2. Spawn through native Codex tools.
3. Preserve returned child identifiers.
4. Avoid parallel write collisions.

### Phase F: Supervision

1. Monitor material progress without duplicating the child's work.
2. Send follow-up guidance when facts or scope change.
3. Interrupt only when continuation is unsafe, invalid, or duplicative.
4. Wait for all results required for integration.

### Phase G: Review and integration

1. Read each child's result.
2. Inspect claimed changed files and current project state.
3. Compare output to the delegation contract.
4. Resolve conflicts using evidence and project authority.
5. Run proportionate integration checks.
6. Accept, revise, or reject each result.

### Phase H: Final response

1. State what the project accomplished.
2. Distinguish director work from delegated work only when useful.
3. State actual checks and results.
4. State limitations and unresolved blockers.
5. Do not claim completion from child status alone.

## 16. Implementation work packages

### WP-00: Reconfirm baseline and authority

**Objective:** Ensure the later implementation begins from current files and
approved authority.

Actions:

1. Re-read root `AGENTS.md`, `SOUL.md`, and this plan.
2. Confirm whether `ROLE.md`, `sub-agent-roles/`, or the target skill have
   appeared since planning.
3. Inspect Git state if the directory has become a repository.
4. Stop on conflicting user changes rather than overwriting them.
5. Record the exact planned change boundary.

Exit criteria:

- Current state is known.
- No overlapping user change is at risk.
- Implementation authority is explicit.

### WP-01: Establish the role schema

**Objective:** Freeze the minimal role-bundle contract before generating files.

Actions:

1. Define folder slug rules.
2. Define flat name and description frontmatter.
3. Define required Markdown body sections.
4. Define required `AGENTS.md` links and delegated-work rules.
5. Define catalog JSON and Markdown output.
6. Define invalid-bundle diagnostics.
7. Write `references/role-schema.md`.

Exit criteria:

- The schema covers discovery, fit, creation, validation, and activation.
- No registry or third-party dependency is required.

### WP-02: Create the Project Director role

**Objective:** Add the generic root role that manages the project and
sub-agents.

Actions:

1. Create root `ROLE.md`.
2. Add the exact director purpose and responsibility split.
3. Require `manage-subagent-roles` before role-based delegation.
4. Define decomposition, concurrency, supervision, review, and completion
   behavior.
5. Update root `AGENTS.md` only if needed for reliable integration.

Exit criteria:

- Root `AGENTS.md` required reads resolve.
- The director role is generic.
- The director must use the role-management skill.
- Director accountability remains explicit.

### WP-03: Create the role root and generic seed role

**Objective:** Add the minimum valid role catalog.

Actions:

1. Create `sub-agent-roles/`.
2. Create `sub-agent-roles/project-sub-agent/`.
3. Create its `AGENTS.md` with both required links.
4. Create its `ROLE.md` with valid metadata.
5. Use the exact title **Sub-Agent Project Role**.
6. Define generic capabilities and strict authority limits.

Exit criteria:

- Both files exist.
- Both links resolve.
- The title is exact.
- The role is project-neutral.

### WP-04: Initialize the local skill

**Objective:** Create a Codex-discoverable repository skill.

Actions:

1. Create `.agents/skills/manage-subagent-roles/` using the skill initializer
   when practical.
2. Create `SKILL.md` with discriminating metadata.
3. Make role listing and path return the primary workflow.
4. Add selection, creation, spawning, and validation modes.
5. Add `agents/openai.yaml` only with accurate UI metadata.
6. Add only supporting directories used by the final workflow.

Exit criteria:

- Codex skill validation passes.
- The description correctly triggers role-catalog and delegation work.
- No unrelated skill resources exist.

### WP-05: Implement deterministic discovery and validation

**Objective:** Make role inventory reproducible and safe.

Actions:

1. Implement `scripts/role_catalog.py`.
2. Add list, validate, and show commands.
3. Implement bounded flat-frontmatter parsing.
4. Implement pair, name, duplicate, and link checks.
5. Add Markdown and JSON output.
6. Guarantee read-only behavior for all three commands.

Exit criteria:

- Valid roles are returned with both file paths.
- Invalid roles are diagnosed.
- Output ordering is deterministic.
- Listing performs no writes.

### WP-06: Implement role creation

**Objective:** Let the Project Director create a reusable role when none fits.

Actions:

1. Define the no-fit decision gate in `SKILL.md`.
2. Add and use templates only if they reduce duplication.
3. Enforce descriptive slug and collision rules.
4. Create both files with complete content.
5. Validate and relist immediately.
6. Return the new role and both paths.
7. Keep creation separate from spawning unless both are required.

Exit criteria:

- Creation cannot overwrite.
- Creation produces a valid pair.
- No registry is added.
- Missing tools or skills are not disguised as new roles.

### WP-07: Implement native spawning and supervision

**Objective:** Connect selected role bundles to Codex native sub-agent
orchestration.

Actions:

1. Define the delegation-contract template.
2. Require explicit instruction-source reads in every spawn prompt.
3. Require `fork_turns: all` and prohibit model and reasoning override values.
4. Check effective user, project, and custom-agent configuration for model or
   reasoning overrides; fail closed if exact inheritance is not guaranteed.
5. Use the runtime's native spawn operation.
6. Record child identifiers.
7. Define follow-up, waiting, interruption, and consolidation behavior.
8. Define concurrency and write-ownership rules.
9. Require director reinspection and integration checks.

Exit criteria:

- No shell-launched Codex child process is used.
- The child receives one bounded objective.
- Role files are explicitly loaded.
- The child uses the Project Director's exact model and reasoning effort.
- The director reviews the result before acceptance.

### WP-08: Add focused tests

**Objective:** Verify structure and behavior in proportion to risk.

Actions:

1. Add standard-library tests for catalog discovery and validation.
2. Use temporary fixture directories.
3. Test valid, invalid, duplicate, malformed, and no-role cases.
4. Test output path accuracy and deterministic ordering.
5. Test no-write behavior.
6. Test role-creation guard conditions at the skill workflow level.

Exit criteria:

- Focused tests pass.
- Tests do not depend on external services.
- Tests do not modify the live role catalog.

### WP-09: Run integration verification

**Objective:** Confirm the complete intended workflow.

Actions:

1. Run skill quick validation.
2. Run catalog validation.
3. Run focused tests.
4. Check every required Markdown link.
5. Confirm Codex sees the repository-local skill.
6. Run one read-only generic-role spawn smoke test.
7. Require the child to identify its three instruction sources.
8. Inspect the final tree and changed content.
9. Confirm no tracking registry was created.
10. Complete requirement traceability.

Exit criteria:

- All applicable acceptance checks pass.
- Any environment-limited check is reported accurately.
- No unrelated project content changed.

## 17. Focused test matrix

| Test ID | Fixture or action | Expected result |
| --- | --- | --- |
| T-001 | Empty `sub-agent-roles/` | Valid empty catalog; no mutation. |
| T-002 | One complete role bundle | One valid role with both paths. |
| T-003 | Missing `AGENTS.md` | Invalid diagnostic; not eligible. |
| T-004 | Missing `ROLE.md` | Invalid diagnostic; not eligible. |
| T-005 | Missing frontmatter | Invalid diagnostic. |
| T-006 | Empty name | Invalid diagnostic. |
| T-007 | Empty description | Invalid diagnostic. |
| T-008 | Name does not equal folder slug | Invalid diagnostic. |
| T-009 | Duplicate role names | Both conflicting locations reported; neither silently preferred. |
| T-010 | Broken root `SOUL.md` link | Invalid diagnostic. |
| T-011 | Broken local `ROLE.md` link | Invalid diagnostic. |
| T-012 | Multiple valid roles | Deterministic name/path ordering. |
| T-013 | Markdown output | Required columns and canonical paths returned. |
| T-014 | JSON output | Valid schema version and fields returned. |
| T-015 | Inventory filesystem snapshot before and after | No writes. |
| T-016 | Create descriptive new role | Both complete files created and validated. |
| T-017 | Create existing role | Fails without changing either file. |
| T-018 | Create traversal-like slug | Rejected. |
| T-019 | Existing suitable role | Selected; no new role created. |
| T-020 | No suitable role, reusable capability gap | Creation workflow proposed or executed according to caller authority. |
| T-021 | Required Codex skill unavailable | Blocker returned; no false-fit role created. |
| T-022 | Listing-only invocation | Catalog returned; no spawn. |
| T-023 | Creation-only invocation | New role returned; no spawn. |
| T-024 | Spawn invocation | Valid role and delegation contract required before native spawn. |
| T-025 | Generic role smoke test | Child confirms it read root `SOUL.md`, local `AGENTS.md`, and local `ROLE.md`. |
| T-026 | Child result review | Director reinspects claimed state before acceptance. |
| T-027 | Model and reasoning inheritance | Spawn contract uses `fork_turns: all`, omits model and reasoning overrides, and fails closed if another configuration layer can replace either value. |

## 18. Acceptance criteria

The later implementation is complete only when all applicable criteria pass:

1. Root `ROLE.md` exists and defines a generic Project Director.
2. The Project Director is responsible for project handling, task decisions,
   delegation, coordination, review, integration, and final verification.
3. Root `ROLE.md` requires use of `manage-subagent-roles` before role-based
   sub-agent creation or spawning.
4. `sub-agent-roles/` exists.
5. The generic `project-sub-agent/` bundle exists.
6. The generic role contains exactly one `AGENTS.md` and one `ROLE.md`.
7. The generic role's visible H1 is exactly **Sub-Agent Project Role**.
8. Its `AGENTS.md` links to root `SOUL.md` and local `ROLE.md`.
9. Its `ROLE.md` contains valid name and description metadata.
10. The skill is stored in the official repository-local skill location.
11. The skill's primary behavior returns existing roles and both canonical
    file paths.
12. The skill diagnoses incomplete and malformed roles.
13. The skill evaluates capability and required-skill fit.
14. The skill creates a new descriptive role bundle only when no existing role
    fits and the gap is actually a role gap.
15. The skill validates and relists a new role before spawning.
16. The skill uses native Codex sub-agent orchestration.
17. The spawned child is instructed to read all three governing sources.
18. The Project Director waits for, reviews, and verifies required results.
19. Listing does not mutate the project.
20. No separate role registry or tracking database exists.
21. Focused structural and catalog tests pass.
22. Skill validation passes.
23. One read-only native spawn smoke test passes, or its exact environment
    limitation is reported.
24. The final change review finds no unrelated edits.
25. Every requirement in this plan has implementation or verification
    evidence.
26. Every role-based child uses the Project Director's exact model and
    reasoning effort; no spawn argument, sub-agent default, or custom-agent
    configuration replaces either value.

## 19. Failure modes and controls

| Failure mode | Control |
| --- | --- |
| Director remembers a stale role list | Inventory must run for each selection workflow. |
| Role folder has only one required file | Catalog marks it invalid and ineligible. |
| Role metadata and folder disagree | Validation fails closed. |
| Two roles share a name | Both are reported as conflicts; no silent winner. |
| Generic role is used for specialized work | Fit check evaluates capabilities and boundaries. |
| Missing Codex skill is confused with a missing role | Fit workflow classifies skill availability separately. |
| Role creation overwrites user work | Existing target causes immediate failure. |
| New role is named after a one-off ticket | Naming policy requires an enduring descriptive responsibility. |
| Nested `AGENTS.md` is not auto-loaded for a root-CWD child | Spawn prompt explicitly requires reading the selected role files. |
| Child changes files owned by another child | Director assigns exclusive write ownership. |
| Child result is accepted without evidence | Director must inspect artifacts and rerun proportionate checks. |
| Too many agents are spawned | Respect current runtime concurrency and task value. |
| Script tries to spawn agents | Keep filesystem helpers separate from native orchestration. |
| A role registry becomes stale | No persistent registry in this version. |
| Skill creates roles during a listing request | Invocation modes enforce read-only inventory. |
| Role creation pretends to supply a missing tool | Creation gate distinguishes capability, skill, tool, and permission gaps. |
| Template becomes tied to current machine paths | Store repository-relative paths and resolve them at runtime. |
| Child receives a different model or reasoning effort | Use `fork_turns: all`, omit both overrides, reject custom-agent or default settings that replace inherited values, and fail closed when exact inheritance cannot be guaranteed. |

## 20. Security, permission, and change controls

- Role discovery is read-only.
- Role creation writes only beneath `sub-agent-roles/`.
- Skill creation writes only beneath its repository-local skill directory.
- The implementation must not use unresolved paths to create files.
- The role helper must reject path escape.
- The director must preserve user changes and dirty worktrees.
- Sub-agents inherit the active runtime permission boundary unless the platform
  explicitly supports and authorizes a narrower override.
- Neither a role definition nor a delegation contract can grant authority that
  the user, platform, or parent does not have.
- Do not change user-level Codex configuration to force model inheritance.
  Stop if the runtime cannot guarantee an exact match safely.
- External writes, publication, dependency installation, destructive actions,
  and credential use remain separately authorized actions.

## 21. Rollback strategy

The architecture is designed to be reversible.

If the implementation must be rolled back:

1. Remove only the new root `ROLE.md` if it did not replace user content.
2. Revert only the role-system additions to root `AGENTS.md`.
3. Remove only `sub-agent-roles/` entries created by the implementation.
4. Remove only `.agents/skills/manage-subagent-roles/`.
5. Remove only focused role-system tests.
6. Preserve this plan unless the user explicitly asks to remove it.
7. Preserve unrelated project files and all user-created roles added after the
   implementation.

If Git is available later, use scoped version-control operations. Do not use a
broad destructive reset.

## 22. Decisions and assumptions

### 22.1 Decisions

- **D-001:** The root director file will be named `ROLE.md`.
- **D-002:** The sub-agent role root will be named `sub-agent-roles/`.
- **D-003:** The initial child directory will be `project-sub-agent/`.
- **D-004:** The exact generic role title will be **Sub-Agent Project Role**.
- **D-005:** Each role bundle has two canonical files: `AGENTS.md` and
  `ROLE.md`.
- **D-006:** `ROLE.md` uses name and description frontmatter to mirror Codex
  skill discovery metadata.
- **D-007:** The repository-local skill will use the current official path
  `.agents/skills/manage-subagent-roles/`.
- **D-008:** The role catalog is discovered live and is not stored.
- **D-009:** The role helper is read-only and standard-library-only.
- **D-010:** Native Codex tools handle spawning; Python scripts do not.
- **D-011:** A native custom-agent TOML adapter is deferred until a concrete
  per-agent configuration need exists.
- **D-012:** The implementation will seed one generic role and no speculative
  domain roles.
- **D-013:** Every role-based child is a model-and-reasoning copy of the
  Project Director. Role selection changes instructions and task scope only.

### 22.2 Assumptions

- The user's repeated reference to the root source file means the existing
  root `SOUL.md`.
- The phrase “skill required” can mean either task capability or an actual
  Codex skill. The implementation will model and check both separately.
- The Project Director should delegate substantive bounded work but may retain
  inherently director-level work and should not spawn agents without value or
  runtime support.
- “Not for now, just forget that” means no separate role tracking system in
  the first version. Live filesystem discovery still provides the requested
  role lookup.
- A new role should represent a reusable responsibility, not a single task
  instance.

## 23. Requirement-to-intent traceability

| User intent | Formal requirements | Planned artifacts or workflow | Verification |
| --- | --- | --- | --- |
| Create a generic root ROLE.md | DIR-001 through DIR-004 | Root `ROLE.md` | Acceptance 1-2; content inspection |
| Main role is Project Director | DIR-002, DIR-004, DIR-008 | Root role title and purpose | Root-role review |
| Director handles the project | DIR-005 through DIR-008, DIR-012 | Director operating workflow | Delegation scenario review |
| Director handles and creates sub-agents | DIR-006, DIR-007, DIR-010; SPN-001 through SPN-005 | Skill selection and native spawn modes | T-024, T-025 |
| Director decides how to handle tasks | DIR-005, DIR-006, FIT-001 | Intake and decomposition phases | Scenario review |
| Tasks are given to fitting sub-agents | DIR-007; FIT-001 through FIT-009 | Role fit workflow | T-019, T-024 |
| Director must use the skill | DIR-010, DIR-011; SKL-007 | Root `ROLE.md` and skill invocation | Root-role and behavioral inspection |
| Create a sub-agent role folder | ROL-001, ROL-002 | `sub-agent-roles/` | Tree inspection |
| One descriptive folder per sub-agent role | ROL-002 through ROL-004 | `sub-agent-roles/name/` | Naming tests |
| Each role has its own agent MD | ROL-005, ROL-006 | Role-specific `AGENTS.md` | T-002 through T-004 |
| Each role has its own role MD | ROL-005, ROL-006 | Role-specific `ROLE.md` | T-002 through T-004 |
| Agent MD points to root source MD | ROL-007, ROL-009 | Link to `../../SOUL.md` | T-010 |
| Agent MD points to local role MD | ROL-008, ROL-009 | Link to `./ROLE.md` | T-011 |
| Initial role is generic | GEN-006 through GEN-009 | Generic role body | Content inspection |
| Title is “Sub-Agent Project Role,” not filename | GEN-004, GEN-005 | H1 in `ROLE.md` | Exact-title check |
| Create a local skill | SKL-001 through SKL-004 | `.agents/skills/manage-subagent-roles/` | Skill validator |
| Match Codex skill-style metadata | MET-001 through MET-005 | `ROLE.md` frontmatter and progressive disclosure | Metadata tests |
| Main skill purpose is to return existing roles and both files | MET-006 through MET-015; SKL-005 | Inventory output contract | T-002, T-013, T-014 |
| Find already-created roles | MET-006, MET-008, SKL-016 | Live catalog scan | T-001 through T-012 |
| Do not use a role lacking required capability or skill | FIT-003 through FIT-006 | Fit assessment | T-019, T-021 |
| Create a role when none fits | FIT-010; CRT-001 through CRT-012 | Creation mode | T-016, T-020 |
| New folder indicates what the agent is | ROL-003, ROL-004; CRT-002 | Descriptive slug policy | T-018 and naming checks |
| Create both files for a new role | CRT-004 through CRT-008 | Role creation workflow | T-016 |
| Use Codex spawning processes | SKL-020; SPN-001 through SPN-013 | Native orchestration workflow | T-024 through T-026 |
| Children use the director's exact model and reasoning effort | SPN-006, SPN-016 | Full-history native spawn with no model or reasoning override | T-027 |
| Do not build role tracking now | MET-007; CRT-013; VER-014 | Live filesystem source of truth | Acceptance 20; final tree inspection |
| Make the design generic for a template | DIR-003; GEN-007; D-012 | Generic root and seed role | Content inspection |
| Produce a detailed implementation plan only | Scope 2.3 | This file | Final artifact inspection |
| Create Implementation_Plans folder and place plan there | Current task output | `Implementation_Plans/subagent_role_system_implementation_plan.md` | Path and file check |
| Verify every requirement and intent is in the plan | Entire catalog and this matrix | Requirement catalog plus traceability | Bidirectional traceability review |

## 24. Bidirectional traceability verification procedure

Before implementation approval:

1. Read the user's request sentence by sentence.
2. Map every distinct intent to at least one formal requirement.
3. Confirm every formal requirement maps to:
   - an artifact or workflow;
   - a work package;
   - an acceptance criterion or test.
4. Confirm no planned artifact lacks a requirement.
5. Confirm no requirement silently adds an unrelated product feature.
6. Confirm deferred tracking is listed as a non-goal.
7. Confirm the exact generic role title appears in the plan.
8. Confirm both required role files and both required links appear in the plan.
9. Confirm discovery is the skill's primary purpose.
10. Confirm native spawning is separate from filesystem helper scripts.
11. Confirm role suitability checks both capability and Codex-skill
    availability.
12. Confirm the no-fit role-creation path does not overwrite existing roles.
13. Confirm every spawn path preserves the exact parent model and reasoning
    effort and rejects every override layer.

## 25. Definition of done for the future implementation

The future implementation is done only when:

- All required artifacts exist.
- All path and title invariants are exact.
- All valid roles are discoverable.
- Invalid roles are visible but ineligible.
- The Project Director uses the local skill.
- The skill returns role names and both canonical file paths.
- Role matching rejects capability and skill mismatches.
- The no-fit workflow can create a complete reusable role safely.
- Native Codex sub-agent spawning uses the selected role bundle.
- Every role-based child inherits the Project Director's exact model and
  reasoning effort.
- The director supervises, reviews, and verifies delegated work.
- Focused tests and skill validation pass.
- The final tree contains no separate role registry or tracking store.
- Requirement-to-implementation evidence covers every requirement.
- The final report distinguishes observed verification from any untested
  runtime behavior.

## 26. Logical implementation order

Implement in this dependency order:

1. WP-00 baseline and authority.
2. WP-01 role schema.
3. WP-02 Project Director role.
4. WP-03 generic role bundle.
5. WP-04 local skill scaffold.
6. WP-05 catalog helper.
7. WP-06 role creation workflow.
8. WP-07 native spawning workflow.
9. WP-08 focused tests.
10. WP-09 integration verification and final traceability.

Do not begin a dependent work package until its predecessor's exit criteria
are satisfied.
