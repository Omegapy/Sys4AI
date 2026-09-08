---
name: manage-subagent-roles
description: Discover and return project sub-agent roles with their AGENTS.md and ROLE.md paths; use when the Project Director needs to list, select, create, validate, spawn, supervise, or collect results from role-based Codex sub-agents. Do not use this skill to install missing skills or to create separate user-visible tasks.
---

# Manage Sub-Agent Roles

Use the owning project's live `Roles/` pairs as its authoritative catalog.
`Roles/INDEX.md` is persisted navigation, never independent role authority.
The actual directory entry must be exactly `Roles`; a lowercase filesystem
alias or a second case-equivalent tree is not an active catalog.
The Project Director or the exact confirmed Task manager owns selection and
assignment. Ordinary children do not select their own project-level role or
write a role index.

## Establish the project root and mode

Resolve the owning project containing `SOUL.md`, `ROLE.md`, `AGENTS.md` and
`Roles/`. Read applicable local instructions. Run its installed helper with the
project Python environment; do not install a parser or dependency.

```text
.venv/bin/python .agents/skills/manage-subagent-roles/scripts/role_catalog.py --repo-root . list --format json
```

Inventory and validation are read-only. Selection adds a function-specific fit
decision. Creation is only for a demonstrated reusable role gap. Reindex or
legacy transition is an explicit mutation. Spawn and supervision use actual
native tools under the assignment's authority. Inventory alone creates no role,
index, manager, worker, Task or user-visible conversation.

## Inventory before other modes

Run fresh inventory before every selection, creation or assignment, including
manager bootstrap and each worker, solver, reviewer, senior and implementer.
Return each role's name, description, pair paths, content digests and validity;
return invalid bundles and index drift separately. Invalid roles are never
eligible. A stale or forged index cannot make a missing pair valid.

Use JSON for decisions and a concise Markdown table for a requested human
inventory. Legacy `sub-agent-roles/` is excluded from ordinary active discovery;
an absent active layout requires an explicit transition, never a fallback.

## Select by task fit

Define objective, required capabilities, read/write needs, expected output,
required Codex skills, tools, risk and stopping condition for this function.
Read both full files for plausible candidates. Compare capabilities, exclusions
and authority; verify actual skill/tool availability. A role capability is not
the same as a Codex skill dependency. Prefer the narrowest suitable valid role.
Return its pair paths and digests, alternatives, rationale and residual limits.

Distinguish a reusable responsibility gap from a missing skill, tool, dependency,
permission, native capability or work reserved for the Director. Only the first
case enters role creation. A manager requires explicit Task ownership and
nested-delegation capability; a general worker's title cannot supply it.

## Create a reusable role

Read [the role schema](references/role-schema.md). Define its enduring purpose,
descriptive name, selection boundary, capabilities, exclusions, required inputs,
outputs, method, skills, validation duties, authority and stopping conditions.
Respect the owning project's source/adoption boundary: reusable depot content
belongs in source collections; ordinary project roles remain project-local.

Use `create --help` and the existing helper to render a complete new pair and
publish its index. Never overwrite an existing target. Verify the returned pair,
index and fresh catalog before assignment. A committed valid bundle with a
pending index returns explicit recovery; run `reindex`, not creation again.
Creation-only requests stop after validation and do not spawn.

## Validate and repair navigation

```text
.venv/bin/python .agents/skills/manage-subagent-roles/scripts/role_catalog.py --repo-root . validate --format json
.venv/bin/python .agents/skills/manage-subagent-roles/scripts/role_catalog.py --repo-root . show ROLE_NAME --format json
.venv/bin/python .agents/skills/manage-subagent-roles/scripts/role_catalog.py --repo-root . reindex --format json
```

List/show/validate leave bytes unchanged and report missing/stale index content.
`reindex` regenerates deterministic relative links, hashes and invalid diagnostics
from the live pairs under the helper's mutation lock. Index failure cannot
promote an invalid bundle. Do not steal a lock, force an overwrite or treat a
lock file's age as proof of an active or abandoned writer.

For a legacy transition, read the schema, run `transition-preview --format json`,
review the exact old/new paths, digests and collisions, then use only the
authorized preview with `transition-apply --preview-file FILE --confirmed`.
Retain legacy pairs and historical references. If publication is interrupted,
inspect `Roles/.transition.json` and resume the exact reported recovery. A changed
source or customized destination blocks replay. Read-only routes never migrate.

For an authorized rename of the previous lowercase `roles/` layout, run
`case-rename-preview --format json` and save the reviewed preview outside the
role tree. Use `case-rename-apply --preview-file FILE --confirmed` for that exact
project. The helper moves the unchanged tree through an exclusive temporary
name and records `.sys4ai/roles-case-rename.json`. Replay the same preview after
an interruption; changed bytes, identity, aliases or competing trees block
recovery. After completion, run `reindex` to publish current `Roles/` navigation.
The original `.transition.json` stays byte-identical. Its lowercase paths are
historical provenance; only a validated completed rename receipt resolves them
to current paths. This operation does not adopt other project assets or update
the Template mapping and ownership state; the depot update pipeline owns those.

## Build the delegation contract

Name the selected role and both canonical pair paths, root `SOUL.md`, one
objective, inspected inputs and current baseline, allowed reads/writes,
protected state, exact deliverable, checks, evidence, authority and stopping
condition. Include native identity/settings and context evidence separately.
Require the child to read SOUL, both role files and the complete contract before
work, then return their exact digests with its result.

Do not assume that Codex automatically loaded the role-specific nested
`AGENTS.md`. A role file outside the session's ancestor path must be explicitly
loaded. Root guidance does not promote ordinary children to manager or writer.

## Spawn through native Codex orchestration

Use available native `spawn_agent`, `send_message`, `followup_task`,
`list_agents`, `wait_agent` and `interrupt_agent` operations. Check actual
capability, delegation depth, instruction compatibility and current capacity
before corresponding dispatch. No shell-launched Codex process or separate
user-visible task or thread substitutes for a native child.

Every team member uses the manager's exact effective model and reasoning effort.
Record direct equality evidence or a verified runtime inheritance guarantee.
Omit the `model` and `reasoning_effort` spawn arguments when using verified
inheritance. Check effective `agents.default_subagent_model`,
`agents.default_subagent_reasoning_effort` and custom-agent settings without
exposing credentials or rewriting user configuration. Unverified settings or
a known mismatch blocks dispatch; seniority changes no setting.

Separate identity from context. `fork_turns: all` has a verified full-history
inheritance guarantee in the observed runtime, but solver forks qualify only
when the supplied history excludes sibling drafts. For queued initial solvers,
return only paths, hashes and status and defer candidate reads until all initial
solvers launch. Another context mode needs its own verified model/effort and
isolation guarantees. A prompt to ignore an inherited draft is insufficient.

Reserve the assignment through the Task helper before launch when orchestration
is active. Preserve the actual returned native ID and record the receipt before
activation/results. An uncertain launch keeps its original reservation for
reconciliation. Do not duplicate it. Queue within observed capacity, preserving
logical team counts, reviewer mappings and non-overlapping write ownership.
Do not authorize nested delegation unless the Director grants it for the bounded
assignment; the confirmed Task manager has only the nested authority handed off.

## Supervise and collect

Use the original native IDs for steering and follow-up. Wait for required
results; do not spawn a duplicate to avoid clarifying an active assignment.
Require outputs, paths, exact versions, checks, limitations and stopped-state
evidence. A completion message alone does not prove correct artifacts or capacity
release. Inspect material bytes and actual native status before acceptance.

On controlling user changes, stop dependent dispatch, request applicable native
interruption, inspect known edits and reconcile every owner before replacement
or a final stopped-state claim. Preserve uncertain owners explicitly. A manager
transfer or model-setting change must use the current Task generation and
recovery protocol. Do not infer stopping from age or roster absence alone.

For a completed/stopped instance receiving materially revised inputs, queue the
packet with `send_message` without waking it, record the helper's
`assignment.inputs` handoff and current scope/capacity checks, then wake it with
`followup_task`. Reconcile running owners first. An observed running status is
not a replacement for a required reservation or resume transition.

## Failure behavior

Report the exact missing role, capability, permission, native tool, inheritance
guarantee, independence condition or stale/conflicting state. Continue a cycle
only for a targeted revision, new evidence or hypothesis. Preserve artifacts,
mandatory criteria and required agent counts. Do not create roles to hide a
missing tool, silently change topology, or claim unobserved native behavior.
