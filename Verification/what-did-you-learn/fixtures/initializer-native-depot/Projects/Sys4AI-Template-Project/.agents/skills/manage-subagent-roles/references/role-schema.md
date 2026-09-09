# Sub-Agent Role Bundle Schema

Read this reference when creating a role, validating a role, or diagnosing why
a role is ineligible. The role system is a project-owned convention modeled on
Codex skill discovery. Codex does not natively discover arbitrary `ROLE.md`
files.

## Canonical layout

Each immediate role directory under `Roles/` is one reusable definition:

```text
Roles/
|-- INDEX.md
`-- descriptive-role-name/
    |-- AGENTS.md
    `-- ROLE.md
```

The two files are the canonical role bundle. `INDEX.md` is a deterministic
navigation view of validated pairs, with project-relative links, content
digests and invalid-role diagnostics. It is never role authority. Do not add a
competing registry, database, CSV or native custom-agent TOML configuration.
Legacy `sub-agent-roles/` remains recoverable provenance and is inspected only
for explicit transition or diagnostics, never as an automatic active fallback.

The `reindex`, `transition-preview` and confirmed `transition-apply`
routes extend the existing helper. Reindex reports unchanged/current output or
the exact publication failure. Creation reports a committed valid bundle
separately from an index still needing publication. Recovery completes that
publication without recreating or deleting the bundle. Transition previews bind
the exact old/new pair hashes; differing destinations or stale previews block
copy-first apply. Preserve legacy content and historical references. No
read-only route reindexes, creates, migrates or repairs.

The role root's actual directory entry must be exactly `Roles`. All other
case-equivalent names and dual trees are rejected, including on case-insensitive
filesystems. `roles/` is the previous edition, not an active fallback.

## Case-only rename and provenance

`case-rename-preview --format json` inspects the previous lowercase tree without
writing. Its version 1 preview binds the exact project root, `source: roles`,
`destination: Roles`, deterministic temporary name, source device/inode,
complete relative directory/file inventory and `preview_sha256`. Every file
has its SHA-256, including custom content, `INDEX.md` and `.transition.json`.
Symlinks, hard links, unexpected entry types and competing case aliases block.
A pending legacy copy-first transition must finish using its original helper
before the directory can be renamed.

Save the preview outside the role tree. An authorized
`case-rename-apply --preview-file FILE --confirmed --format json` writes a
version 1 receipt at `.sys4ai/roles-case-rename.json`, then moves the same directory
through two exclusive no-overwrite renames. Its `preview` retains the reviewed
input and `status` is `pending` or `completed`. The macOS implementation uses
`renamex_np(RENAME_EXCL)`; Linux uses `renameat2(RENAME_NOREPLACE)` when supplied
by the host C library. Unsupported exclusive rename capability fails explicitly.
No nonexclusive fallback overwrites a competing empty directory.

An interruption before or after either hop returns exit 3 with the same-preview
recovery command. Pending recovery requires the exact original inventory and
directory identity at exactly one source, temporary or destination path. It
never deletes a competing tree or restores stale bytes. A completed replay
verifies the same exact `Roles` directory identity and leaves later authorized
file edits intact. Run `reindex` separately after the rename; the physical
operation preserves the old index bytes and does not claim current navigation.

`validate_case_rename_receipt(value, root)` requires completed, exact current
physical spelling and retained directory identity. It returns `status`,
`directory_identity`, `source_files` (old project-relative paths to original
hashes) and `destination_paths` (old paths to current `Roles/` paths). This is
historical provenance; current consumers must inspect current file hashes.
`validate_transition_receipt` accepts internally valid prior lowercase
destinations without rewriting them. `transition_destination_paths(value,
root)` resolves those destinations only through the completed rename proof and
requires every historical file to have belonged to its inventory. Active
`transition-preview` and `transition-apply` accept only current `Roles/` targets.
Case receipts and prior transition evidence are controls, not starter assets or
role definitions. Template migration also requires its own checked mapping and
managed-ownership transaction through the depot updater.

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
`assets/role-bundle/ROLE.md.template`, validates both files, reserves a new role
directory with a fail-if-present operation, and publishes its index. It removes
only its own invalid incomplete pair on creation failure. A valid committed
pair survives an index failure; exit 3 reports `bundle_committed: true` and
`recovery: reindex`. Never repeat creation of that existing role.

Mutations use the standard-library POSIX advisory lock at
`.sys4ai/role-catalog.lock`. Its retained regular file avoids unlink/reacquire
races; only the held OS lock indicates an active writer. Read-only routes do
not create it or publish any files. Unsafe symlink or hard-link targets fail.

`transition-preview --format json` returns exact pairs, source/destination
digests, conflicts and `preview_sha256`. Save the reviewed JSON outside the
role tree. `transition-apply --preview-file FILE --confirmed --format json`
rereads those preconditions, keeps all legacy files, records publication in
`Roles/.transition.json`, then validates and indexes the active pairs. A partial
receipt resumes only with the same reviewed preview; current source or
destination changes block recovery. Successful repeated apply is a no-op.
Index, lock and transition receipts are not role definitions or starter data.

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

Every role-based child uses the Project Director's exact model and reasoning
effort. The selected role changes the child's instructions and bounded objective
only. Record directly observed equality or an effective runtime inheritance
guarantee; a role title or requested setting is not observed equality.

For a runtime that guarantees inheritance with `fork_turns: all`, omit the
`model` and `reasoning_effort` arguments. Check effective custom-agent files,
`agents.default_subagent_model` and `agents.default_subagent_reasoning_effort`
without exposing secrets. Do not use a configuration that replaces the parent's
values. Model/effort inheritance and context independence are separate checks.
Initial solver history must exclude sibling candidate content, including queued
dispatch. Keep returns to paths, hashes and status until every initial solver
has launched; another context mode requires its own verified guarantees.

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

For a tracked execution, the host reserves and launches a real manager, records
its native receipt, and activates its exact assignment through the Task helper.
That manager alone owns canonical writes after handoff. An ordinary child is not
promoted by reading root guidance. Role definitions, logical function slots,
native instances, result producers and the canonical writer remain distinct.
Re-read the catalog and assess the function-specific fit before each assignment.
Reservation precedes launch; an uncertain outcome is reconciled against the
original reservation before any replacement. Follow the Task contract's current
generation, artifact, stopping and recovery gates.
