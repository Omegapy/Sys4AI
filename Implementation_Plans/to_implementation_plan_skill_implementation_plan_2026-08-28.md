# To Implementation Plan skill implementation plan

## Document control

| Field | Value |
| --- | --- |
| Plan status | Proposed and plan-level verified; implementation not started |
| Plan date | 2026-08-28 |
| Project root | `/Volumes/P-SSD/AngryOwl/Sys4AI` |
| Source TRD | `TRDs/trd_tracked-implementation-plan-skill_2026-08-28.md` |
| Source TRD ID | `TRD-20260828-D209CF52` |
| Source TRD revision | 1 |
| Source TRD state | `draft` |
| Source TRD SHA-256 | `9242337cbb7a176bee6f001d06448129b38545ce2f5a86516881d113a2cc254b` |
| Proposed skill name | `to-implementation-plan` |
| Proposed source package | `SKILLS-depo/to-implementation-plan/` |
| Plan verification report | `Verification/to_implementation_plan_skill_plan_verification_2026-08-28.md` |
| Implementation authority | Planning only. This document does not authorize skill creation, installation, synchronization, execution, Git actions, publication, or deployment. |

## 1. Executive intent

Implement a reusable, explicitly invoked Codex skill that converts an accessible
prompt, text, local file, Task Requirement Document (TRD), Product Requirements
Document (PRD), URL, or other readable source into a project-aware implementation
plan. Each plan must contain stable phases and tasks, durable state, explicit
dependencies, acceptance criteria, evidence, and bidirectional traceability.

The skill must solve two distinct problems:

1. Create an implementation plan that correctly represents the source intent and
   the live target project.
2. Maintain the plan as durable project state while authorized work progresses.

A generated plan is not proof that implementation occurred. Creating, approving,
or selecting a plan does not authorize the skill to modify the target project.
Execution begins only after a current user explicitly authorizes work against an
exact plan, and every external, destructive, publication, or deployment action
still requires its normal authority.

The initial implementation stops after creating and validating one self-contained
source package in `SKILLS-depo/to-implementation-plan/`. It does not register the
package in `depot/manifest.json`, synchronize it into `.agents/skills`, install it
globally, or publish it.

## 2. Scope and authority boundary

### 2.1 In scope for the later implementation

- Confirm the proposed skill name and initial behavior decisions.
- Use the current Codex `skill-creator` workflow to initialize the source package.
- Create a concise `SKILL.md` that routes among creation, inspection, revision,
  validation, progress tracking, lifecycle, and recovery operations.
- Create explicit-only UI metadata in `agents/openai.yaml`.
- Create the user-required `README.md` and the references, assets, scripts, and
  tests needed by the workflow.
- Implement a standard-library Python helper for deterministic plan identity,
  storage, validation, state changes, projection rendering, and recovery.
- Create durable plan records under a consumer project's `Implementation_Plans/`
  directory without disturbing pre-existing unmanaged plan files.
- Support source intake from prompts, pasted text, readable local files, TRDs,
  PRDs, and accessible URLs.
- Inspect the live project before proposing artifacts, dependencies, or tests.
- Extract requirements, intent, constraints, exclusions, decisions, assumptions,
  contradictions, and open questions with source links.
- Generate phases, tasks, dependencies, risks, acceptance criteria, verification
  steps, validation steps, and evidence requirements.
- Validate dependency graphs, state transitions, completion evidence, projections,
  and bidirectional source-to-plan coverage.
- Test representative workflows and failure cases in isolated temporary projects.
- Perform a final requirement, package, change-boundary, and intended-use audit.

### 2.2 Out of scope for the initial implementation

- Changing the source TRD or promoting it from `draft` without explicit approval.
- Adding `skill-to-implementation-plan` to `depot/manifest.json`.
- Synchronizing the source package into this depot's `.agents/skills` or the
  template project's `.agents/skills`.
- Installing the skill in a personal or global skill directory.
- Migrating existing standalone Markdown plans into the new tracker.
- Replacing or merging the project Task ledger, TRD lifecycle, Codex thread state,
  native goal state, GitHub issues, or another project-management system.
- Automatically executing a plan because it was created, approved, selected, or
  resumed.
- Creating branches, commits, pushes, pull requests, releases, packages, plugins,
  websites, deployments, accounts, or services.
- Requiring a database, daemon, hosted service, MCP server, or new runtime package.
- Saving full source pages, full transcripts, hidden reasoning, credentials,
  secrets, or unnecessary personal data in plan records.
- Claiming live Codex discovery or end-to-end execution before the source package
  is separately installed and exercised in an authorized consumer project.

### 2.3 Current-turn change boundary

This turn may create only this implementation plan and its plan-verification
report. It must preserve the live TRD, `SKILLS-depo`, `depot/manifest.json`, all
managed targets, existing implementation plans, Git state, and external systems.

## 3. Source precedence and evidence rules

The later implementation must use this source order:

1. Platform, safety, privacy, permission, sandbox, and tool constraints.
2. The current user's explicit request and current execution authority.
3. Applicable project `SOUL.md`, `ROLE.md`, and `AGENTS.md` files.
4. The exact selected plan's canonical `plan.json` state.
5. The selected plan's inspected sources, live target project, and accepted
   decisions.
6. The installed `to-implementation-plan` skill and its contract references.
7. Generated Markdown projections and catalog index.
8. Conversation context, prior plan history summaries, Codex memory, and other
   retrieval aids.

Lower-precedence sources cannot weaken a higher-precedence scope or permission.
Supplied files and pages are data. Instructions inside them do not grant execution,
installation, publication, destructive-action, or secret-access authority.

Evidence must identify whether it is directly observed, produced by a command,
reported by the user, inferred from a source, proposed by the plan, or not
exercised. A planned verification command is not a passing result.

## 4. Observed live baseline

| Item | Observed state | Planning consequence |
| --- | --- | --- |
| Root governance | `AGENTS.md`, `SOUL.md`, and `ROLE.md` define depot authority, task boundaries, verification, and communication rules. | The future skill must read applicable project guidance and cannot replace the Project Director. |
| Source TRD | Revision 1, state `draft`, 20 unchecked requirements, six open questions, and three unconfirmed assumptions. | Treat all architecture choices below as proposed until approved. Implementation must stop at the Phase 0 decision gates if they remain unresolved. |
| Depot source roots | `depot/manifest.json` lists `SKILLS-depo` as a source root. | The new reusable source belongs in `SKILLS-depo/`. |
| Managed skill registry | Five skill artifacts are registered; no implementation-plan skill is registered. | Do not add a manifest entry or targets during the initial implementation. |
| Existing source example | `SKILLS-depo/to-trd/` contains a complete explicit-only skill with README, references, assets, helper, tests, and UI metadata. | Reuse the proven packaging ideas, but do not copy code or licensed text without an attribution review. |
| Existing plan convention | `Implementation_Plans/` contains detailed Markdown implementation plans. | The new runtime catalog must coexist with these files and never treat them as managed records automatically. |
| Existing verification convention | `Verification/` contains durable verification reports. | Store this plan's independent audit there. Runtime plan evidence remains inside each managed plan record. |
| Current skill creator | The bundled initializer, UI metadata generator, and quick validator are present. | Use the initializer only after the name gate; use the validator through `uv --with PyYAML` because direct Python lacks PyYAML. |
| Current Python | Project and host Python are 3.12.13. | Target Python 3.10 or later and use the standard library for the runtime helper. |
| Current `uv` | `/Users/alex.omegapy/.local/bin/uv`, version 0.10.7. | Use an isolated PyYAML validation invocation; do not add PyYAML to this project solely for skill validation. |
| Official OpenAI guidance | A skill is a folder with required `SKILL.md`; scripts, references, assets, and `agents/openai.yaml` are optional. Explicit invocation remains available when `allow_implicit_invocation` is false. | Keep the package focused, use progressive disclosure, and set explicit-only policy because the user requested it. |
| Worktree | `TRDs/` is untracked; no other change was reported at plan start. | Preserve the user's TRD files and isolate future skill changes to the approved source package plus explicit verification artifacts. |

### 4.1 Planning sources

- Source requirements: `TRDs/trd_tracked-implementation-plan-skill_2026-08-28.md`.
- Depot authority: `depot/manifest.json` and `depot/projects.json`.
- Transferable skill precedent: `SKILLS-depo/to-trd/`.
- Detailed project-plan precedent:
  `Implementation_Plans/task_system_implementation_plan.md`.
- Current creator guidance:
  `/Users/alex.omegapy/.codex/skills/.system/skill-creator/SKILL.md` and
  `references/openai_yaml.md`.
- Official OpenAI documentation:
  [Build skills](https://learn.chatgpt.com/docs/build-skills).

The later implementer must reopen these sources and recheck Git and filesystem
state before editing. This baseline is evidence for planning, not a permanent
claim about the repository.

## 5. Proposed decisions and human gates

The source TRD is still a draft. The following choices make this plan concrete,
but they are proposed design decisions rather than recorded user approvals.

| Gate | Proposed decision | Reason | Required action before implementation |
| --- | --- | --- | --- |
| GATE-001 | Name the skill and folder `to-implementation-plan`; display name `To Implementation Plan`. | It is action-oriented, under 64 characters, and parallels `to-trd`. | Confirm or replace the exact name before running the initializer. |
| GATE-002 | Store managed runtime plans under `<project-root>/Implementation_Plans/`. | It matches the live project convention and remains project-local. | Confirm the default; an explicit per-invocation plans root may override it. |
| GATE-003 | Use one managed directory per plan with canonical JSON and split Markdown projections. | It provides durable machine state without one large unstructured Markdown file. | Confirm the storage shape before schema implementation. |
| GATE-004 | V1 creates, maintains, validates, and tracks plans. It does not automatically execute tasks. | It preserves authority while still recording progress from separately authorized work. | Confirm whether later execution orchestration belongs in V1 or a future scope. |
| GATE-005 | Use task states `planned`, `in_progress`, `blocked`, `paused`, `completed`, and `skipped`; derive phase state from task state. | It covers the required work progression while preventing phase/task drift. | Confirm state names and skipped-task policy. |
| GATE-006 | Record URL locators, access times, extracted facts, and optional content hashes; do not save full page snapshots by default. | It limits privacy, copyright, and storage risk. | Confirm whether explicitly authorized snapshots are needed in V1. |
| GATE-007 | Do not migrate unmanaged Markdown plans automatically. | The current directory already contains project-owned plans with unknown contracts. | Confirm that migration is outside V1. |

If a gate remains unresolved when implementation begins, Phase 0 records the
question and stops before creating or modifying the proposed skill folder.

## 6. Terms

| Term | Meaning |
| --- | --- |
| Plan catalog | The managed plan directories plus generated `Implementation_Plans/INDEX.md`. |
| Managed plan | A directory created or explicitly adopted by this skill and containing valid canonical `plan.json`. |
| Unmanaged plan | Any pre-existing file or directory not carrying the skill's canonical identity. It remains untouched. |
| Plan ID | Stable identifier `PLAN-YYYYMMDD-XXXXXXXX`. |
| Source item | A prompt, text block, file, TRD, PRD, URL, or other accessible input recorded with provenance. |
| Requirement | A bounded source-derived outcome with acceptance criteria and source links. |
| Phase | An ordered group of tasks with entry conditions, exit criteria, dependencies, and derived status. |
| Task | A bounded action with stable identity, artifacts, dependencies, acceptance, verification, status, and evidence. |
| Coverage edge | A recorded relationship from a source item to a requirement and from a requirement to one or more tasks or an explicit disposition. |
| Evidence | A concise, reviewable record supporting a task or requirement state. |
| Projection | Human-readable Markdown generated from canonical state. |
| Plan readiness | Structural and intent coverage is complete, material questions are settled, and the user approved the baseline. |
| Plan completion | Every required task and acceptance criterion has current evidence, with any skip explicitly authorized. |

## 7. Proposed source-package architecture

```text
SKILLS-depo/
  to-implementation-plan/
    SKILL.md
    README.md
    ACTIONS.md
    INDEX.md
    agents/
      openai.yaml
    assets/
      example-input.json
      plan-overview-template.md
      phase-template.md
      traceability-template.md
    references/
      intent-and-project-discovery.md
      plan-contract.md
      lifecycle-and-recovery.md
    scripts/
      plan_state.py
    tests/
      test_plan_state.py
```

Conditional files:

- Add `ATTRIBUTION.md` and an applicable license copy only if implementation
  reuses protected code or text rather than independently implementing the
  documented behavior.
- Add a second focused test module only if the first module becomes difficult to
  navigate; do not create placeholder files or empty resource directories.
- Do not add icons, a changelog, a plugin manifest, root guidance, or dependencies
  unless a later approved requirement needs them.

Proposed `agents/openai.yaml` interface:

```yaml
interface:
  display_name: "To Implementation Plan"
  short_description: "Create and track implementation plans"
  default_prompt: "Use $to-implementation-plan to turn this source into a tracked project implementation plan."
policy:
  allow_implicit_invocation: false
```

The metadata has no hard MCP dependency. The agent uses the tools available in
the current host and reports when a local file, URL, or format cannot be read.

## 8. Proposed runtime plan-catalog architecture

```text
<project-root>/
  Implementation_Plans/
    INDEX.md
    Plan_<safe-slug>_<YYYY-MM-DD>_<SHORTID>/
      plan.json
      PLAN.md
      TRACEABILITY.md
      phases/
        PHASE-001_<safe-slug>.md
        PHASE-002_<safe-slug>.md
```

### 8.1 Authority

- `plan.json` is the only canonical state for one plan.
- `PLAN.md`, `TRACEABILITY.md`, phase files, and the catalog `INDEX.md` are
  deterministic projections.
- Missing or stale projections do not erase canonical state.
- A malformed canonical record stops mutation; the helper must not skip it and
  produce an incomplete catalog.
- Read-only operations never repair projections or initialize a catalog.
- `reindex` and `rebuild-projections` are explicit repair operations.
- Existing Markdown plan files and unknown directories remain unmanaged.

### 8.2 Identity and paths

- Plan IDs use `PLAN-YYYYMMDD-XXXXXXXX`, with an uppercase UUID-derived suffix.
- Phase IDs use `PHASE-001` style identifiers scoped to a plan.
- Task IDs use `TASK-001` style identifiers scoped to a plan.
- Source IDs use `SRC-001`; preserve an external source identifier in a separate
  field instead of changing the local ID contract.
- Requirement IDs preserve valid supplied IDs when unique. Generated IDs use
  `REQ-001` style identifiers and never recycle an old meaning.
- Filenames use normalized, bounded ASCII slugs. Display titles preserve the
  user's text.
- The explicit project root is resolved once. Managed paths must remain beneath
  it and must not traverse symlinks, `..`, hidden selector paths, or separators
  embedded in IDs.
- Exact selection accepts the full plan ID, exact managed directory name, or a
  unique case-insensitive complete title. It does not select by recency, partial
  title, substring, or fuzzy match.

### 8.3 Write and recovery model

- Creation uses a short-lived catalog lock.
- Existing-plan updates use a per-plan lock plus the current revision and SHA-256
  of `plan.json`.
- The helper rereads state after locking and rejects stale input.
- Canonical JSON is written to a same-directory temporary file, flushed, and
  atomically replaced before projections are regenerated.
- A canonical commit followed by projection failure returns a partial-success
  receipt and an explicit rebuild route. It must not repeat the canonical update.
- Lock ownership is never inferred safe from age alone. Recovery requires a
  separate explicit instruction, active-writer checks, exact lock inspection,
  canonical validation, and bounded removal of only the abandoned lock.
- The helper must never delete managed plans during normal operations. Retirement
  and cancellation preserve records.

## 9. Canonical `plan.json` contract

The implementation must define a versioned schema with these top-level fields:

| Field | Purpose and rule |
| --- | --- |
| `schema_version` | Positive integer; starts at 1. |
| `plan_id` | Stable ID matching creation date and managed directory suffix. |
| `title` | Nonblank human display title. |
| `slug` | Stable safe slug used by the directory name. |
| `created_at`, `updated_at` | Offset-aware timestamps; creation is immutable and update time never moves backward. |
| `status` | One supported plan lifecycle state. |
| `revision` | Positive integer; starts at 1 and advances only on a real canonical change. |
| `status_reason` | Concise reason for the current plan state. |
| `project` | Root hint, inspected guidance, baseline facts, constraints, and preserved paths. |
| `objective` | Intended outcome and user value. |
| `scope` | In-scope outcomes, explicit exclusions, and execution-authority boundary. |
| `sources` | Provenance records for prompts, files, TRDs, PRDs, URLs, and other inputs. |
| `requirements` | Stable requirements, intent, sources, acceptance criteria, disposition, and evidence state. |
| `decisions` | User-approved decisions and labeled proposed decisions. |
| `open_questions` | Material unresolved baseline questions and their prerequisites. |
| `assumptions` | Accepted or unconfirmed assumptions with basis. |
| `phases` | Stable phase records, task membership, dependencies, gates, and derived status. |
| `tasks` | Stable task records with work, outputs, dependencies, criteria, status, and evidence. |
| `coverage` | Source-to-requirement and requirement-to-task mappings plus explicit dispositions. |
| `validation` | Last structural and coverage result, findings, and checked revision. |
| `history` | Concise revision entries; no full transcripts or hidden reasoning. |

### 9.1 Source record

Each source record contains `source_id`, kind, locator or local description,
display title, access time, optional digest, facts used, access limitations, and
whether content was supplied by the user or inspected by the agent. Prompt text
is summarized to the minimum needed for continuity. A URL record does not imply
the page was accessible; it must state the observed result.

### 9.2 Requirement record

Each requirement contains a stable ID, title, one bounded outcome, intent,
source IDs, acceptance criteria, dependencies when real, explicit negative
requirements when applicable, status or disposition, and evidence references.
Requirements may be removed only through an explicit disposition; their IDs are
not reused.

### 9.3 Phase record

Each phase contains a stable ID, title, objective, scope, dependency phase IDs,
entry conditions, exit criteria, task IDs, risks, and derived status. The helper
recomputes status after each task update and rejects stored phase/task drift.

### 9.4 Task record

Each task contains a stable ID, phase ID, title, one bounded action, requirement
IDs, source or design basis, target artifacts or outputs, dependencies, safe
parallel group when applicable, relevant risks, acceptance criteria, verification
steps, status, blocker or pause reason, evidence entries, and completion time.
No task may exist without a requirement or labeled design-quality basis.

### 9.5 Evidence record

Evidence contains an ID, timestamp, evidence type, concise description, locator
or command, observed result, verification level, and source of the observation.
It must distinguish planned checks, agent-observed results, and user reports.
It must not contain credentials, hidden reasoning, full transcripts, or large
raw logs.

### 9.6 History record

History entries contain revision, timestamp, action ID, affected plan/phase/task
IDs, status before and after, concise summary, and authority basis. The history is
a continuation aid, not a substitute for live project inspection.

## 10. Lifecycle and readiness contract

### 10.1 Plan states

| State | Meaning | Allowed next states |
| --- | --- | --- |
| `draft` | Sources, requirements, design, or plan structure remain unsettled. | `ready`, `retired`, `cancelled` |
| `ready` | Coverage and structure pass, material questions are settled, and the user approved this exact baseline. | `draft`, `in_progress`, `retired`, `cancelled` |
| `in_progress` | The user explicitly authorized execution of the exact ready plan and work has begun. | `paused`, `blocked`, `completed`, `cancelled`, `draft` after material scope change |
| `paused` | Work intentionally stopped without an external blocker. | `in_progress`, `cancelled`, `draft` after material scope change |
| `blocked` | Work cannot proceed because a named condition is unmet. | `in_progress`, `cancelled`, `draft` after material scope change |
| `completed` | All completion gates passed against current evidence. | `in_progress` after explicit reopen, `retired` |
| `retired` | Plan retained but no longer active. | `draft` after explicit restore |
| `cancelled` | Work intentionally ended incomplete and is retained. | `draft` only after explicit restoration and scope review |

### 10.2 Task states

| State | Meaning | Allowed next states |
| --- | --- | --- |
| `planned` | Task is defined and not started. | `in_progress`, `blocked`, `skipped` |
| `in_progress` | Authorized work is currently being performed. | `paused`, `blocked`, `completed` |
| `paused` | Work stopped intentionally. | `in_progress`, `blocked`, `skipped` |
| `blocked` | A named unmet condition prevents work. | `in_progress`, `paused`, `skipped` |
| `completed` | Acceptance and evidence gates passed. | `in_progress` after explicit reopen |
| `skipped` | The current user explicitly approved a reasoned exception. | `planned` after explicit restoration |

### 10.3 Derived phase states

- `planned`: all required tasks are `planned`.
- `in_progress`: at least one task has started or completed and required work
  remains executable.
- `blocked`: required unfinished work has no currently executable path because of
  recorded blockers.
- `paused`: all active unfinished work is paused by an explicit instruction.
- `completed`: every required task is `completed`, or a task is `skipped` under an
  explicit accepted exception that also disposes its requirement coverage.

### 10.4 Readiness gate

A draft may become ready only when:

1. The project root and relevant live guidance were inspected.
2. At least one source and one requirement exist.
3. Material contradictions are resolved or explicitly dispositioned.
4. Open questions and unconfirmed assumptions that affect scope are empty.
5. At least one phase and one task exist.
6. Every phase and task satisfies its field contract.
7. All dependencies exist, are acyclic, and respect phase order.
8. Every source requirement maps to work or an explicit disposition.
9. Every task has a requirement or labeled design basis.
10. The validation report has no unresolved error-level findings.
11. The current user approved this exact plan revision.

### 10.5 Execution gate

Moving `ready` to `in_progress` requires a current explicit instruction that
identifies the exact plan. This authorizes only the work and normal local actions
already in the approved plan. It does not authorize deletion, dependency
installation, publication, deployment, external communication, financial action,
or another separately governed action unless the instruction also grants it.

### 10.6 Completion gate

A plan may become completed only when:

1. Every required task is completed or covered by an explicitly approved skip.
2. Every task acceptance criterion has current, meaningful evidence.
3. Phase rollups are consistent with task state.
4. Every requirement acceptance criterion is satisfied or dispositioned.
5. Forward and reverse traceability both pass.
6. The final project state and protected files were reinspected.
7. Planned tests are reported as passed, failed, blocked, or not exercised.
8. The completion summary states the highest verification level actually reached.
9. The current user explicitly authorizes the completion transition.

## 11. Helper operations and action IDs

| Action ID | Agent operation | Helper route | Mutation |
| --- | --- | --- | --- |
| `TO-IP-001` | Create a draft plan | `create --input FILE|-` | New canonical plan and projections |
| `TO-IP-002` | Show or resume exact plan | `show SELECTOR` | None |
| `TO-IP-003` | List plans | `list [--status STATE]` | None |
| `TO-IP-004` | Revise plan baseline | `update SELECTOR --expect-revision N --expect-sha256 HASH --input FILE|-` | Canonical plan and projections |
| `TO-IP-005` | Update phase content or blocker | `update-phase SELECTOR PHASE-ID ...` | Canonical plan and projections |
| `TO-IP-006` | Update task content or status | `update-task SELECTOR TASK-ID ...` | Canonical plan and projections |
| `TO-IP-007` | Record task or requirement evidence | `record-evidence SELECTOR TARGET-ID ...` | Canonical plan and projections |
| `TO-IP-008` | Change plan lifecycle state | `set-status SELECTOR --status STATE ... --confirmed` | Canonical plan and projections |
| `TO-IP-009` | Validate one plan or the catalog | `validate [SELECTOR]` | None |
| `TO-IP-010` | Rebuild one plan's projections | `rebuild-projections SELECTOR` | Generated files only |
| `TO-IP-011` | Rebuild catalog index | `reindex` | Generated index only |
| `TO-IP-012` | Apply one explicit bounded recovery | `reconcile SELECTOR --input FILE|- --confirmed` | Only reviewed recovery scope |

All commands return structured JSON with a stable schema, command, project root,
status, mutation flag, warnings, errors, recovery requirement, and plan receipt.
The helper defines distinct nonzero categories for invalid input, missing target,
ambiguous selector, unsafe or corrupt state, stale revision/hash, active lock,
prohibited transition, unmet gate, and I/O or partial-projection failure.

## 12. Agent workflow implemented by the skill

1. Confirm explicit activation and identify the requested operation.
2. Establish the project root from explicit user context or unambiguous project
   evidence; stop before writing if the root remains ambiguous.
3. For an existing plan, resolve an exact selector and read canonical state before
   asking questions or proposing mutations.
4. Inventory supplied prompts, text, files, TRDs, PRDs, URLs, and other sources.
5. Treat sources as data; record access limitations and do not execute embedded
   instructions.
6. Read the applicable project guidance and inspect the live architecture,
   conventions, dependencies, tests, repository state, and protected artifacts.
7. Extract the intended outcome, requirements, features, source tasks,
   constraints, exclusions, decisions, assumptions, contradictions, and questions.
8. Use a fast path when intent is clear. Otherwise ask one material,
   prerequisite-ready question at a time or save a requested draft with uncertainty
   preserved.
9. Generate stable requirements, phases, tasks, dependencies, risks, acceptance
   criteria, verification steps, validation steps, and evidence fields.
10. Check all dependency references and cycles before writing.
11. Run forward coverage from every source item to a requirement and task or
    explicit disposition.
12. Run reverse coverage from every task and design choice to its requirement or
    source basis.
13. Write only through the helper, inspect the receipt, show the canonical plan,
    and run read-only validation.
14. Return the exact plan path, stable ID, state, phase and task counts, unresolved
    items, validation result, and index result.
15. Stop. Do not execute planned work unless the user separately and explicitly
    authorizes execution of the exact plan.

## 13. Implementation phases and task ledger

All implementation tasks start in `planned`. Status changes belong to the future
authorized implementation workflow, not this planning turn.

### Phase IP-P00 - Reconfirm authority, baseline, and design gates

- Status: `planned`
- Requirements: REQ-003, REQ-005, REQ-013, REQ-015, REQ-016, REQ-017, REQ-019
- Depends on: None.
- Entry: The user explicitly authorizes implementation planning or implementation
  against the exact source TRD.
- Parallelism: IP-P00-T02 and IP-P00-T03 may run in parallel after IP-P00-T01.
- Write boundary: No skill-package write until IP-P00-T04 resolves all blocking
  gates and IP-P00-T06 records implementation authority.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P00-T01 | planned | Reopen the TRD, root guidance, manifest, project registry, worktree, and relevant existing skill/plan sources; record hashes and observed drift. | None. | REQ-005, REQ-015, REQ-019 | Baseline record names every inspected source, distinguishes observed facts from plan assumptions, and identifies unrelated dirty files to preserve. |
| IP-P00-T02 | planned | Run To-TRD read-only show/validate for `TRD-20260828-D209CF52`; compare the live requirement set with this plan. | IP-P00-T01 | REQ-004, REQ-014, REQ-016 | Canonical TRD is structurally valid or the exact defect blocks implementation; requirement additions, removals, or state changes are reported before work. |
| IP-P00-T03 | planned | Recheck official OpenAI skill guidance, current `skill-creator`, initializer, metadata generator, quick validator, Python, and `uv`. | IP-P00-T01 | REQ-017, REQ-018, REQ-020 | Commands and package assumptions are current; unavailable tools or changed contracts are reflected in a revised plan before scaffolding. |
| IP-P00-T04 | planned | Present GATE-001 through GATE-007 and record the user's exact decisions without treating plan proposals as approval. | IP-P00-T02, IP-P00-T03 | REQ-001, REQ-009, REQ-010, REQ-012, REQ-016, REQ-017 | Exact name, storage, lifecycle, execution scope, URL retention, and migration decisions are settled or implementation stops. |
| IP-P00-T05 | planned | Freeze the approved initial package, runtime catalog, source, consumer, external-action, and Git boundaries. | IP-P00-T04 | REQ-003, REQ-013, REQ-019 | A written boundary permits only the source package and named verification artifacts; manifest, `.agents/skills`, consumers, and external systems remain protected. |
| IP-P00-T06 | planned | Record the current user's implementation authorization, approved TRD/plan revisions, evidence expectations, and stop condition. | IP-P00-T05 | REQ-011, REQ-015, REQ-019 | Authority identifies exact revisions and scope; absent authority stops before IP-P01-T01. |

Exit: All material decisions are approved, the live baseline agrees with the plan
or the plan is revised, and implementation authority is explicit.

### Phase IP-P01 - Initialize the self-contained source package

- Status: `planned`
- Requirements: REQ-001, REQ-017, REQ-018, REQ-019
- Depends on: IP-P00
- Entry: GATE-001 and the package boundary are approved; the target folder does
  not exist.
- Parallelism: After initialization, frontmatter, UI metadata, and README work may
  proceed with distinct file ownership.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P01-T01 | planned | Use the bundled `skill-creator` initializer with the approved name, `SKILLS-depo` path, and only required `scripts,references,assets` resources. | IP-P00-T06 | REQ-017, REQ-018, REQ-019 | One new approved skill directory exists; no existing directory is overwritten and no consumer or manifest path changes. |
| IP-P01-T02 | planned | Inspect the scaffold, remove unfinished examples, and establish the approved package inventory without adding speculative files. | IP-P01-T01 | REQ-017, REQ-018 | Required directories exist, all placeholders have an owner or are removed, and no empty or unrelated resource remains. |
| IP-P01-T03 | planned | Write proposed `SKILL.md` frontmatter with exact name and a discriminating explicit-only description. | IP-P01-T01 | REQ-001, REQ-017, REQ-018 | Name is hyphen-case and under 64 characters; description states creation/tracking scope and excludes ordinary planning requests. |
| IP-P01-T04 | planned | Generate or narrowly update `agents/openai.yaml` with consistent interface text, explicit default prompt, and `allow_implicit_invocation: false`. | IP-P01-T01, IP-P01-T03 | REQ-001, REQ-017, REQ-018 | UI strings meet current constraints, default prompt names `$to-implementation-plan`, and no unneeded dependency or icon field exists. |
| IP-P01-T05 | planned | Create a concise README foundation and package index because the user explicitly requires a transferable documented folder. | IP-P01-T01 | REQ-017, REQ-019, REQ-020 | README states source-only staging and package index lists only real files; later phases fill operating details. |
| IP-P01-T06 | planned | Run the quick validator through isolated `uv --with PyYAML`; record the scaffold baseline before behavior is added. | IP-P01-T02, IP-P01-T03, IP-P01-T04, IP-P01-T05 | REQ-018, REQ-020 | Validator passes or the exact scaffold defect is corrected; PyYAML is not installed into the project. |

Exit: The approved source folder exists, contains no unfinished scaffold content,
passes baseline validation, and remains unregistered and uninstalled.

### Phase IP-P02 - Specify identity, schema, lifecycle, and projections

- Status: `planned`
- Requirements: REQ-002 through REQ-016
- Depends on: IP-P01
- Entry: Package scaffold and name are stable.
- Parallelism: Schema records may be drafted in parallel, but one owner integrates
  `plan-contract.md` and resolves field conflicts before helper code begins.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P02-T01 | planned | Define source precedence, explicit activation, project-root resolution, authority, and state-system separation in `references/plan-contract.md`. | IP-P01-T06 | REQ-001, REQ-003, REQ-005, REQ-013 | Contract has one authority order, source-as-data rule, exact root rule, and no implicit authority from plan or source content. |
| IP-P02-T02 | planned | Define plan, source, requirement, phase, task, evidence, action, and history identifiers plus safe naming and selector rules. | IP-P02-T01 | REQ-006, REQ-007, REQ-009, REQ-012 | IDs are stable and unique; collision, Unicode, punctuation-only, ambiguous, and unsafe selector behavior is deterministic. |
| IP-P02-T03 | planned | Specify all top-level `plan.json` fields, types, invariants, versioning, revision, timestamps, and status-reason rules. | IP-P02-T02 | REQ-009, REQ-010, REQ-012 | Schema is complete, machine-validatable, backward-version aware, and contains no hidden or duplicate authority field. |
| IP-P02-T04 | planned | Specify source and requirement records, provenance, intent, negative requirements, contradictions, assumptions, questions, dispositions, and source digests. | IP-P02-T03 | REQ-002, REQ-003, REQ-004, REQ-014, REQ-016 | Every material input can be represented without storing unnecessary source content; missing access and unconfirmed choices remain visible. |
| IP-P02-T05 | planned | Specify phase, task, evidence, and history records, including task-to-phase ownership, output fields, acceptance, verification, blocker reasons, and evidence levels. | IP-P02-T03 | REQ-006, REQ-007, REQ-009, REQ-011 | Each task is independently executable and reviewable; evidence distinguishes planned, observed, user-reported, and not-exercised results. |
| IP-P02-T06 | planned | Specify plan/task transitions, derived phase rollups, readiness, execution, skip, completion, reopen, retirement, and cancellation gates. | IP-P02-T04, IP-P02-T05 | REQ-010, REQ-011, REQ-012, REQ-016 | All states and legal transitions are enumerated; invalid transitions, unsupported completion, and material scope changes fail closed. |
| IP-P02-T07 | planned | Specify dependency graph and bidirectional coverage algorithms, explicit dispositions, orphan detection, cycle detection, and readiness severity levels. | IP-P02-T04, IP-P02-T05 | REQ-008, REQ-014, REQ-015 | Missing/self/cyclic dependencies, uncovered requirements, silent exclusions, and orphan tasks produce deterministic blocking findings. |
| IP-P02-T08 | planned | Specify deterministic `PLAN.md`, per-phase Markdown, `TRACEABILITY.md`, and catalog `INDEX.md` templates and sorting rules. | IP-P02-T03, IP-P02-T05, IP-P02-T07 | REQ-006, REQ-007, REQ-009, REQ-014 | Projections contain identity, status, tasks, evidence summaries, and coverage without becoming canonical or one monolithic prose file. |
| IP-P02-T09 | planned | Specify size bounds, UTF-8 handling, privacy/secret rules, version rejection, unmanaged-plan coexistence, no-migration policy, and future migration extension points. | IP-P02-T01, IP-P02-T03, IP-P02-T04 | REQ-003, REQ-009, REQ-013, REQ-015, REQ-019 | Bounds have documented bases; unknown versions and unmanaged files are preserved; sensitive content is rejected before write. |

Exit: One internally consistent contract defines every runtime record, projection,
transition, gate, failure class, and authority boundary needed by the helper and
skill instructions.

### Phase IP-P03 - Implement helper foundation and read-only operations

- Status: `planned`
- Requirements: REQ-005, REQ-008, REQ-009, REQ-012, REQ-014, REQ-015
- Depends on: IP-P02
- Entry: Contract fields and operations are frozen for V1.
- Parallelism: Renderer work may proceed beside parser/selector work after the
  shared data model exists; one helper owner integrates the file.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P03-T01 | planned | Create the standard-library `scripts/plan_state.py` CLI skeleton, global arguments, command router, JSON result envelope, and main error boundary. | IP-P02-T09 | REQ-009, REQ-012, REQ-015 | Each documented command is routable, stdout contains machine JSON, diagnostics avoid secrets, and unsupported arguments cause no write. |
| IP-P03-T02 | planned | Implement explicit root resolution, catalog confinement, managed-directory recognition, regular-file checks, symlink escape rejection, and safe temporary paths. | IP-P03-T01 | REQ-003, REQ-005, REQ-009, REQ-013 | Absolute, parent, hidden, separator, symlink, and out-of-root attempts fail before mutation; unmanaged files remain untouched. |
| IP-P03-T03 | planned | Implement duplicate-key-safe JSON loading and full schema, identifier, timestamp, lifecycle, requirement, phase, task, evidence, history, and coverage validation. | IP-P03-T01, IP-P03-T02 | REQ-007, REQ-008, REQ-009, REQ-010, REQ-014, REQ-015 | Valid fixtures pass; wrong types, missing fields, duplicate IDs, bad references, and cycles yield exact findings. |
| IP-P03-T04 | planned | Implement catalog discovery and exact ID, directory, and complete-title selection with stable ambiguity diagnostics. | IP-P03-T02, IP-P03-T03 | REQ-009, REQ-012 | Exact targets resolve; partial/fuzzy/ambiguous selectors cause no mutation and return candidates without choosing one. |
| IP-P03-T05 | planned | Implement deterministic renderers for overview, per-phase files, traceability, and index, including escaping and stable sort order. | IP-P03-T03 | REQ-006, REQ-007, REQ-009, REQ-014 | Repeated renders are byte-identical for unchanged canonical state; stale or altered projections are detected. |
| IP-P03-T06 | planned | Implement `show`, `list`, and `validate` as strictly read-only operations that detect active locks, canonical corruption, projection drift, coverage gaps, and unmanaged content safely. | IP-P03-T04, IP-P03-T05 | REQ-012, REQ-014, REQ-015 | Byte comparisons prove no read-only mutation; catalog validation never skips malformed managed plans or claims unmanaged plans. |
| IP-P03-T07 | planned | Finalize stable receipts, warning/error categories, exit codes, validation severities, and no-op representation. | IP-P03-T06 | REQ-012, REQ-015 | Tests can distinguish success, no-op, invalid input, not found, ambiguity, corruption, stale state, lock, gate failure, and partial I/O. |

Exit: All read-only operations and deterministic projections work from valid
fixtures, reject corrupt/unsafe state, and produce no filesystem mutation.

### Phase IP-P04 - Implement safe mutations, evidence, and recovery

- Status: `planned`
- Requirements: REQ-008 through REQ-015
- Depends on: IP-P03
- Entry: Read-only discovery and validation are passing.
- Parallelism: Mutation handlers may be developed against separate fixtures, but
  locking and transaction code have one owner and are integrated before tests.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P04-T01 | planned | Implement draft plan creation, collision-safe identity, initial history, canonical write, projections, and catalog index under a catalog lock. | IP-P03-T07 | REQ-006, REQ-007, REQ-009, REQ-012 | Creation never overwrites a collision, starts in draft, returns a complete receipt, and reports partial projection failure accurately. |
| IP-P04-T02 | planned | Implement baseline `update` with expected revision/hash, stable IDs, requirement dispositions, material-scope detection, and ready/in-progress return-to-draft behavior. | IP-P04-T01 | REQ-004, REQ-009, REQ-010, REQ-012, REQ-016 | Stale updates fail; material changes cannot remain falsely ready; removed requirements retain explicit disposition and identity history. |
| IP-P04-T03 | planned | Implement `update-phase` for approved phase content, dependencies, gates, risks, and blockers while keeping status derived. | IP-P04-T02 | REQ-006, REQ-008, REQ-010, REQ-012 | Phase edits preserve task ownership, reject cycles, recompute rollups, and cannot set a contradictory manual completion state. |
| IP-P04-T04 | planned | Implement `update-task` for content, status, blocker/pause reasons, dependencies, outputs, checks, and explicit reopen/skip rules. | IP-P04-T02 | REQ-007, REQ-008, REQ-010, REQ-012 | Invalid transitions and predecessor violations fail; completed/skipped tasks require the correct authority and preserve prior evidence/history. |
| IP-P04-T05 | planned | Implement `record-evidence` for task and requirement targets with evidence typing, concise content validation, locators, verification level, and secret guard. | IP-P04-T04 | REQ-003, REQ-007, REQ-011, REQ-012 | Meaningless markers and known credential patterns are rejected; user reports are labeled; evidence can be resolved from every checked item. |
| IP-P04-T06 | planned | Implement `set-status` with readiness, execution, pause, block, completion, reopen, retirement, cancellation, confirmation, and exact-revision gates. | IP-P04-T03, IP-P04-T04, IP-P04-T05 | REQ-010, REQ-011, REQ-012, REQ-014, REQ-015 | Every allowed transition succeeds only when its gate passes; prohibited transitions leave files byte-identical. |
| IP-P04-T07 | planned | Implement per-plan locks, catalog lock ordering, double stale checks, same-directory temporary writes, flush/replace behavior, and deterministic no-ops. | IP-P04-T01, IP-P04-T02 | REQ-009, REQ-010, REQ-012, REQ-015 | Concurrent writers serialize, stale clients cannot overwrite, no-op updates do not advance revision, and no deadlock order exists. |
| IP-P04-T08 | planned | Implement projection/index publication after canonical commit plus partial-success receipts and explicit `rebuild-projections` and `reindex`. | IP-P04-T06, IP-P04-T07 | REQ-009, REQ-012, REQ-015 | Canonical success is not misreported as failure; repair changes projections only and is idempotent. |
| IP-P04-T09 | planned | Implement bounded `reconcile`, abandoned-lock diagnostics, orphan-temp detection, corrupt-state refusal, and documented recovery stop conditions. | IP-P04-T07, IP-P04-T08 | REQ-003, REQ-009, REQ-012, REQ-015 | Recovery requires explicit reviewed input, never steals a live lock, never guesses missing intent/evidence, and leaves a validation receipt. |

Exit: All canonical mutations are revision-safe, evidence-gated, atomic at the
canonical boundary, recoverable within the documented limits, and fully covered
by transaction fixtures.

### Phase IP-P05 - Write skill instructions, references, and README

- Status: `planned`
- Requirements: REQ-001 through REQ-003, REQ-012, REQ-013, REQ-016 through REQ-020
- Depends on: IP-P02
- Entry: Contracts are stable enough to describe accurately.
- Parallelism: May run beside IP-P03 and IP-P04 with file ownership limited to
  documentation and metadata; synchronize command names after helper integration.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P05-T01 | planned | Write concise `SKILL.md` purpose, explicit activation boundary, operation routing, shared workflow, authority limits, and stop condition using progressive disclosure. | IP-P02-T09 | REQ-001, REQ-003, REQ-012, REQ-013, REQ-016 | Entrypoint contains only shared decisions; every conditional reference is linked where it becomes relevant; ordinary planning text does not trigger it. |
| IP-P05-T02 | planned | Write `ACTIONS.md` with user operations, helper routes, write sets, confirmations, and action IDs. | IP-P05-T01 | REQ-001, REQ-010, REQ-012 | Every operation maps to one implemented route; read-only and mutating actions are visibly distinct. |
| IP-P05-T03 | planned | Complete `references/plan-contract.md` with schema, selectors, storage, result, error, rendering, locking, recovery, and compatibility rules. | IP-P02-T09, IP-P03-T07, IP-P04-T09 | REQ-007 through REQ-015 | Reference matches actual helper behavior and contains no planned command that does not exist. |
| IP-P05-T04 | planned | Write `references/intent-and-project-discovery.md` for source intake, provenance, project inspection, intent extraction, clarification, and pre-write coverage review. | IP-P02-T04 | REQ-002 through REQ-005, REQ-014 through REQ-016 | Each supported input has a route; facts, user choices, proposals, assumptions, contradictions, and access gaps remain separate. |
| IP-P05-T05 | planned | Write `references/lifecycle-and-recovery.md` for state meanings, authority, evidence, safe updates, locks, partial failures, and explicit recovery. | IP-P02-T06, IP-P04-T09 | REQ-009 through REQ-013, REQ-015 | Lifecycle tables and recovery steps agree with code and never manufacture consent or delete a plan. |
| IP-P05-T06 | planned | Complete `README.md` with context, package tree, requirements, source-only staging, installation, explicit usage, input examples, generated layout, states, commands, validation, recovery, and evidence limitations. | IP-P05-T02, IP-P05-T03, IP-P05-T04, IP-P05-T05 | REQ-017, REQ-019, REQ-020 | A new reader can install later and use the skill without project history; README does not claim current installation or live Codex testing. |
| IP-P05-T07 | planned | Finalize `INDEX.md`, cross-links, metadata consistency, terminology, and attribution/license decision; remove duplicate guidance. | IP-P05-T01, IP-P05-T06 | REQ-017, REQ-018, REQ-020 | Every package file is listed and reachable; copied material is licensed/attributed or replaced with original text; one term names each concept. |

Exit: Instructions and documentation match the implemented contract, preserve
explicit authority, and satisfy the user-required transferable README package.

### Phase IP-P06 - Implement source intake, project discovery, and plan synthesis

- Status: `planned`
- Requirements: REQ-002 through REQ-008, REQ-014 through REQ-016
- Depends on: IP-P03, IP-P05
- Entry: Helper input contract and agent workflow references are stable.
- Parallelism: Input adapters can be exercised independently; one integration pass
  owns normalized source and requirement semantics.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P06-T01 | planned | Implement prompt and pasted-text normalization into source records without storing an unnecessary full transcript. | IP-P03-T03, IP-P05-T04 | REQ-002, REQ-003, REQ-004 | Direct requests retain vocabulary, intent, constraints, and source attribution; private or irrelevant text is omitted. |
| IP-P06-T02 | planned | Implement accessible local-file intake with exact path, regular-file checks, format-aware reading through available tools, digest when practical, and explicit unsupported-format results. | IP-P06-T01 | REQ-002, REQ-003 | Readable fixtures produce provenance; symlinks/unsafe paths fail; unreadable formats are reported without fabricated extraction. |
| IP-P06-T03 | planned | Implement TRD intake that preserves TRD ID, revision, state, requirement IDs, acceptance, decisions, open questions, assumptions, and exclusions. | IP-P06-T02 | REQ-002, REQ-004, REQ-014, REQ-016 | The current 20-requirement TRD produces 20 traceable requirement records and retains its draft limitations. |
| IP-P06-T04 | planned | Implement PRD intake for headings, requirements, features, user stories, acceptance, constraints, exclusions, and unresolved content without assuming one universal PRD schema. | IP-P06-T02 | REQ-002, REQ-004, REQ-014, REQ-016 | Structured and free-form PRD fixtures preserve every material item or record an explicit ambiguity. |
| IP-P06-T05 | planned | Implement URL intake through available browsing tools with canonical locator, title, access time, extracted facts, optional digest, citation, and exact inaccessible-page limitation. | IP-P06-T01 | REQ-002, REQ-003, REQ-014 | Accessible fixture is cited; inaccessible, authenticated, dynamic, or unsupported content is not fabricated or silently omitted. |
| IP-P06-T06 | planned | Normalize mixed sources, detect duplicates/contradictions, label source authority, and defend against embedded execution or permission instructions. | IP-P06-T01, IP-P06-T02, IP-P06-T03, IP-P06-T04, IP-P06-T05 | REQ-003, REQ-004, REQ-014 | Duplicate facts remain traceable, contradictions remain visible, and source content cannot change agent authority. |
| IP-P06-T07 | planned | Implement target-project establishment and bounded inspection of guidance, architecture, dependencies, tests, repository state, conventions, and protected files. | IP-P06-T06 | REQ-005, REQ-013, REQ-015 | The plan baseline cites live files and observations, does not guess project technology, and asks for root choice only when materially ambiguous. |
| IP-P06-T08 | planned | Implement intent extraction and uncertainty handling with fast path, one material question at a time, draft-now behavior, explicit decisions, and accepted/unconfirmed assumptions. | IP-P06-T06, IP-P06-T07 | REQ-004, REQ-016 | Clear requests proceed directly; material unknowns block readiness but do not block saving an honest draft. |
| IP-P06-T09 | planned | Implement phase/task synthesis, dependency ordering, safe parallel groups, acceptance/evidence design, forward and reverse coverage, validation, helper payload generation, and post-write inspection. | IP-P06-T08, IP-P03-T06 | REQ-006, REQ-007, REQ-008, REQ-014, REQ-015 | Generated plan passes schema, acyclic dependency, complete coverage, no-orphan, and project-fit checks before it can become ready. |

Exit: Every supported input route produces a truthful normalized source set and a
project-aware draft plan, or an exact limitation without invented content.

### Phase IP-P07 - Build automated contract and fault tests

- Status: `planned`
- Requirements: REQ-001 through REQ-015, REQ-017 through REQ-020
- Depends on: IP-P04, IP-P06
- Entry: Helper and synthesis workflow are feature-complete for V1.
- Parallelism: Test groups may be authored independently with isolated temporary
  projects; shared fixtures have one owner.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P07-T01 | planned | Add package, frontmatter, UI metadata, explicit-invocation, resource-link, and unfinished-placeholder tests. | IP-P01-T06, IP-P05-T07 | REQ-001, REQ-017, REQ-018, REQ-020 | Metadata and package tests detect wrong names, implicit policy, missing files, broken links, and scaffold residue. |
| IP-P07-T02 | planned | Add identity, naming, collision, timestamp, revision, schema-version, JSON type, duplicate-key, and size-bound tests. | IP-P03-T03, IP-P04-T01 | REQ-007, REQ-009, REQ-010 | Valid state passes; each invalid representation fails before mutation with an exact category. |
| IP-P07-T03 | planned | Add root, traversal, hidden path, symlink, unsafe selector, exact selection, ambiguity, unmanaged-file, and corrupt-catalog tests. | IP-P03-T02, IP-P03-T04 | REQ-003, REQ-009, REQ-012, REQ-013 | Unsafe paths and ambiguity never mutate; unmanaged project plans remain byte-identical. |
| IP-P07-T04 | planned | Add missing dependency, self-reference, cycle, phase-order, missing membership, duplicate ID, uncovered requirement, silent exclusion, and orphan-task tests. | IP-P03-T03, IP-P02-T07 | REQ-006, REQ-007, REQ-008, REQ-014, REQ-015 | Every graph and coverage fault is detected and blocks readiness. |
| IP-P07-T05 | planned | Add every allowed/prohibited plan and task transition, phase-rollup, readiness, execution, skip, completion, reopen, material-scope, and evidence gate test. | IP-P04-T03, IP-P04-T04, IP-P04-T05, IP-P04-T06 | REQ-010, REQ-011, REQ-012, REQ-015 | State table is exhaustively exercised; invalid changes leave canonical and projection files unchanged. |
| IP-P07-T06 | planned | Add stale revision/hash, concurrent lock, lock order, interrupted-write, canonical/projection partial failure, no-op, and atomic replacement tests. | IP-P04-T07, IP-P04-T08 | REQ-009, REQ-010, REQ-012, REQ-015 | Stale and concurrent writes cannot overwrite; committed canonical state and repair routes are reported truthfully. |
| IP-P07-T07 | planned | Add read-only byte-parity, projection drift, reindex, rebuild, explicit reconcile, abandoned lock, orphan temp, and repeat-recovery tests. | IP-P03-T06, IP-P04-T08, IP-P04-T09 | REQ-009, REQ-012, REQ-015 | Read-only commands write nothing; repairs are bounded and idempotent; corruption is not guessed away. |
| IP-P07-T08 | planned | Add known-secret, hidden-reasoning, oversized-log, adversarial-source, unauthorized-execution, and cross-state-system isolation tests. | IP-P04-T05, IP-P06-T06 | REQ-003, REQ-011, REQ-013, REQ-019 | Sensitive and authority-escalating input is rejected or safely summarized; no Task/TRD/goal/manifest state changes. |
| IP-P07-T09 | planned | Add deterministic overview, per-phase, traceability, index sorting/escaping, missing projection, and round-trip tests. | IP-P03-T05, IP-P04-T08 | REQ-006, REQ-007, REQ-009, REQ-014 | Repeated render is byte-identical and projections represent all canonical phases, tasks, status, and coverage. |

Exit: Focused unit and contract tests cover every state, operation, graph rule,
security boundary, transaction class, and projection invariant.

### Phase IP-P08 - Run representative behavioral workflows

- Status: `planned`
- Requirements: REQ-002, REQ-004 through REQ-016, REQ-020
- Depends on: IP-P06, IP-P07
- Entry: Automated contract suite passes.
- Parallelism: Scenarios use separate temporary project roots and may run in
  parallel if they do not share a skill-package checkout.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P08-T01 | planned | Create a plan from one clear direct prompt and verify fast-path intent, phases, tasks, coverage, draft receipt, and split projections. | IP-P07-T09 | REQ-002, REQ-004, REQ-006, REQ-007, REQ-014, REQ-015 | Scenario yields one valid draft with no invented project fact and complete prompt-to-task coverage. |
| IP-P08-T02 | planned | Create plans from pasted text and a local file; compare provenance, digest, requirements, exclusions, and unsupported-file behavior. | IP-P08-T01 | REQ-002, REQ-003, REQ-004 | Both readable inputs preserve intent; unsafe or unsupported file input returns an exact limitation and no partial plan. |
| IP-P08-T03 | planned | Create a plan from a copy of the 20-requirement source TRD in a temporary project. | IP-P08-T01 | REQ-002, REQ-004, REQ-014, REQ-016, REQ-020 | All 20 IDs and acceptance criteria map to tasks or explicit dispositions; draft questions remain blockers; no requirement is silently marked complete. |
| IP-P08-T04 | planned | Create plans from structured and narrative PRD fixtures with features, user stories, negative requirements, and contradictions. | IP-P08-T01 | REQ-002, REQ-004, REQ-014, REQ-016, REQ-020 | Material PRD content is preserved and contradictions remain visible until a user decision. |
| IP-P08-T05 | planned | Exercise an accessible controlled URL fixture and inaccessible/authenticated URL cases without saving full pages by default. | IP-P08-T01 | REQ-002, REQ-003, REQ-014, REQ-020 | Locator, access result, citations, and extracted facts are truthful; inaccessible content causes no fabricated requirement. |
| IP-P08-T06 | planned | Exercise one-question clarification, draft-now save, approval-to-ready, material revision back to draft, and unconfirmed-assumption gate. | IP-P08-T01 | REQ-010, REQ-012, REQ-016 | Conversation behavior is concise; user decisions are recorded exactly; lifecycle follows the contract. |
| IP-P08-T07 | planned | Resume an exact plan in a fresh context, record progress/evidence, pause/block/reopen work, and reach completion only after all gates pass. | IP-P08-T06 | REQ-009, REQ-010, REQ-011, REQ-012, REQ-013 | Durable files provide continuity without transcript/memory authority; task, phase, requirement, and plan states agree. |
| IP-P08-T08 | planned | Exercise ordinary non-invoked planning language, ambiguous selector, unauthorized execute request, stale state, corrupt state, and another state system reporting conflicting status. | IP-P08-T07 | REQ-001, REQ-003, REQ-012, REQ-013, REQ-015 | Skill does not trigger implicitly, choose ambiguously, expand authority, overwrite stale/corrupt state, or merge conflicting ledgers. |

Exit: Representative user journeys succeed in isolated projects and all negative
scenarios fail closed with usable diagnostics.

### Phase IP-P09 - Validate and package the source-only delivery

- Status: `planned`
- Requirements: REQ-017 through REQ-020 and all package-facing acceptance criteria
- Depends on: IP-P07, IP-P08
- Entry: Contract and behavioral tests pass.
- Parallelism: Static documentation and filesystem audits may run beside isolated
  smoke checks; final change-set review is sequential.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P09-T01 | planned | Compile the helper and tests with the supported Python baseline and check for generated bytecode outside ignored temporary locations. | IP-P07-T09 | REQ-017, REQ-020 | Compilation passes and no `__pycache__` or `.pyc` remains in the delivery. |
| IP-P09-T02 | planned | Run the complete focused `unittest` suite in a clean temporary environment and save the high-level result. | IP-P09-T01 | REQ-020 | All tests pass with exact count; failures are fixed rather than skipped or weakened. |
| IP-P09-T03 | planned | Run the current skill-creator quick validator through isolated `uv --with PyYAML`. | IP-P09-T02 | REQ-018, REQ-020 | Validator reports valid skill; project dependencies and global Python remain unchanged. |
| IP-P09-T04 | planned | Check Markdown structure, links, code fences, YAML consistency, terminology, trailing whitespace, duplicate guidance, and unresolved placeholders. | IP-P05-T07, IP-P09-T03 | REQ-017, REQ-020 | All internal references resolve and no TODO/template residue, malformed Markdown, or metadata mismatch remains. |
| IP-P09-T05 | planned | Copy only the completed source package to an isolated temporary project's `.agents/skills/`, run helper smoke operations there, and remove the temporary project. | IP-P09-T02, IP-P09-T04 | REQ-017, REQ-019, REQ-020 | Package is self-contained and runnable after copy; this is not claimed as live Codex discovery or host end-to-end execution. |
| IP-P09-T06 | planned | Audit the complete working-tree change set, manifest, managed targets, consumer projects, personal/global skills, Git index, and generated junk. | IP-P09-T05 | REQ-019 | Only the approved source package and explicit planning/verification artifacts changed; nothing is staged, installed, synchronized, committed, or published. |
| IP-P09-T07 | planned | Reopen every package file and verification result; reconcile README, INDEX, action table, contract, helper help, tests, and actual tree. | IP-P09-T06 | REQ-017, REQ-018, REQ-020 | File inventory and documented commands match the delivered package byte-for-byte at handoff. |

Exit: The transferable source package passes structural, automated, behavioral,
documentation, portability, and scope checks without installation or publication.

### Phase IP-P10 - Perform final bidirectional audit and handoff

- Status: `planned`
- Requirements: REQ-001 through REQ-020
- Depends on: IP-P09
- Entry: All prior phases meet their exit criteria.
- Parallelism: Coverage calculations may be independent, but one final Director
  review integrates and accepts the evidence.

| Task | Status | Action and output | Depends on | Requirements | Acceptance and verification |
| --- | --- | --- | --- | --- | --- |
| IP-P10-T01 | planned | Run forward traceability from each live TRD requirement and acceptance criterion to implemented artifacts, tests, and current evidence. | IP-P09-T07 | REQ-001 through REQ-020 | All 20 requirements have direct evidence or are reported incomplete; no matrix-only claim substitutes for artifact inspection. |
| IP-P10-T02 | planned | Run reverse traceability from every changed file, behavior, command, schema field, test, phase, and task to an approved requirement or necessary quality basis. | IP-P10-T01 | REQ-014, REQ-015, REQ-019 | No orphan feature, file, dependency, action, or out-of-scope change remains. |
| IP-P10-T03 | planned | Recheck every acceptance criterion, test scenario, lifecycle transition, failure mode, recovery path, and documentation promise against current outputs. | IP-P10-T02 | REQ-011, REQ-015, REQ-020 | Passed, failed, blocked, partial, and not-exercised evidence is separated; no planned check is reported as run. |
| IP-P10-T04 | planned | Reinspect the live project, protected content, manifest, targets, worktree, and source-package tree after all checks. | IP-P10-T03 | REQ-005, REQ-013, REQ-019 | Preserved files and state remain intact; final scope equals authorized scope. |
| IP-P10-T05 | planned | Review security, privacy, authority, stale-write, recovery, migration, compatibility, and maintenance risks; record residual limits. | IP-P10-T04 | REQ-003, REQ-009, REQ-010, REQ-012, REQ-013, REQ-015 | Every material risk has a control, owner/decision, evidence, and honest residual status. |
| IP-P10-T06 | planned | Publish the implementation verification report inside `Verification/` with hashes, commands, counts, coverage, failures, limitations, and highest verification level. | IP-P10-T05 | REQ-011, REQ-014, REQ-015, REQ-020 | Report is reproducible, matches current files, and distinguishes package validation from installed/live behavior. |
| IP-P10-T07 | planned | Deliver the exact source path, file inventory, requirement result, test result, limitations, and one separately authorized next step; stop before registration, installation, Git, or publication. | IP-P10-T06 | REQ-017, REQ-018, REQ-019, REQ-020 | User receives a complete evidence-backed handoff and no unrequested downstream action occurs. |

Exit: Every requirement and every implemented change is accounted for in both
directions, the source-only package is validated, and all limits are explicit.

## 14. Phase dependency and progress summary

| Phase | Status | Depends on | Task count | Required output |
| --- | --- | --- | ---: | --- |
| IP-P00 | planned | None | 6 | Approved gates, frozen boundary, implementation authority |
| IP-P01 | planned | IP-P00 | 6 | Valid source-package scaffold |
| IP-P02 | planned | IP-P01 | 9 | Complete runtime and storage contract |
| IP-P03 | planned | IP-P02 | 7 | Read-only helper and deterministic projections |
| IP-P04 | planned | IP-P03 | 9 | Safe mutations, lifecycle, evidence, and recovery |
| IP-P05 | planned | IP-P02 | 7 | Skill instructions, references, README, and metadata |
| IP-P06 | planned | IP-P03, IP-P05 | 9 | Source intake, project discovery, and synthesis workflow |
| IP-P07 | planned | IP-P04, IP-P06 | 9 | Automated contract and fault suite |
| IP-P08 | planned | IP-P06, IP-P07 | 8 | Representative behavioral validation |
| IP-P09 | planned | IP-P07, IP-P08 | 7 | Validated portable source package and scope audit |
| IP-P10 | planned | IP-P09 | 7 | Final bidirectional audit and handoff |

Total implementation phases: 11. Total implementation tasks: 84. Completed
implementation tasks at plan creation: 0.

## 15. Detailed verification and test matrix

All tests use temporary project roots unless a row explicitly identifies a
read-only inspection of the live source package. Tests must not install the
skill, alter the manifest, or mutate a consumer project.

| Test | Scenario | Expected result | Requirements |
| --- | --- | --- | --- |
| TST-001 | Validate `SKILL.md` frontmatter and name. | Valid hyphen-case name, required fields, no unknown fields or placeholder. | REQ-017, REQ-018 |
| TST-002 | Inspect `agents/openai.yaml`. | UI values match the skill and `allow_implicit_invocation` is false. | REQ-001, REQ-017, REQ-018 |
| TST-003 | Send ordinary planning text without explicit invocation. | Skill does not create or mutate a plan. | REQ-001 |
| TST-004 | Explicitly invoke the approved skill name. | Requested operation begins and no unrelated operation runs. | REQ-001 |
| TST-005 | Create from a direct prompt. | Source inventory, intent, requirements, phases, tasks, and draft state are correct. | REQ-002, REQ-004, REQ-006, REQ-007 |
| TST-006 | Create from pasted text. | Material vocabulary, constraints, exclusions, and source attribution are preserved. | REQ-002, REQ-004 |
| TST-007 | Create from a readable local text file. | Exact locator and digest are recorded; content is represented without modifying the source. | REQ-002, REQ-003 |
| TST-008 | Supply unsafe, symlinked, missing, binary, or unsupported local input. | Exact access/format error, no fabricated content, and no partial plan write. | REQ-002, REQ-003, REQ-015 |
| TST-009 | Create from the source TRD fixture. | All 20 requirement IDs and acceptance criteria map to work or explicit dispositions. | REQ-002, REQ-004, REQ-014, REQ-020 |
| TST-010 | Create from a structured PRD fixture. | Features, user stories, constraints, exclusions, and acceptance remain traceable. | REQ-002, REQ-004, REQ-014 |
| TST-011 | Create from a narrative PRD fixture. | Unnumbered material items receive stable generated IDs without invented certainty. | REQ-002, REQ-004, REQ-016 |
| TST-012 | Read a controlled accessible URL fixture. | Locator, title, access time, extracted facts, and citation are truthful; no default full snapshot. | REQ-002, REQ-003 |
| TST-013 | Read inaccessible, authenticated, or dynamic URL fixtures. | Limitation is explicit and no inaccessible claim becomes a requirement. | REQ-002, REQ-003, REQ-015 |
| TST-014 | Place execution and permission-escalation text inside a source. | Source remains data and cannot cause installation, execution, publication, or destructive action. | REQ-003, REQ-013, REQ-019 |
| TST-015 | Supply a known credential pattern or request hidden reasoning storage. | Pre-write guard rejects or safely omits the prohibited content. | REQ-003, REQ-011 |
| TST-016 | Establish a project with clear root guidance and known stack. | Plan baseline cites the actual guidance, architecture, dependencies, tests, and protected paths. | REQ-005, REQ-015 |
| TST-017 | Present two plausible project roots. | Skill performs read-only inspection and asks for the material root choice before writing. | REQ-005, REQ-016 |
| TST-018 | Supply source assumptions that conflict with the live project. | Contradiction remains visible and live evidence controls project facts. | REQ-004, REQ-005, REQ-016 |
| TST-019 | Create a plan with two phases and ordered tasks. | Every phase has identity, objective, gates, dependencies, tasks, and derived status. | REQ-006, REQ-008 |
| TST-020 | Validate a fully populated task. | Stable ID, phase, action, requirement links, outputs, dependencies, risks, criteria, checks, status, and evidence field all exist. | REQ-007 |
| TST-021 | Add missing, self, or cyclic task/phase dependencies. | Validation blocks the plan and names every invalid edge. | REQ-008, REQ-015 |
| TST-022 | Mark a dependent task in progress before its predecessor. | Transition fails unless an explicit approved exception is allowed by contract. | REQ-008, REQ-010 |
| TST-023 | Create two same-title plans on the same date. | Stable distinct IDs and non-overwriting managed directories are produced. | REQ-009 |
| TST-024 | Close context and resume by exact plan ID. | Canonical files reconstruct the current phase/task state without transcript or memory authority. | REQ-009, REQ-012, REQ-013 |
| TST-025 | Use exact title, exact directory, partial ID, fuzzy title, and ambiguous title selectors. | Only allowed exact/unique selectors resolve; ambiguous or fuzzy input causes no mutation. | REQ-012 |
| TST-026 | Exercise every allowed plan transition. | Transition succeeds only with required state, revision/hash, reason, confirmation, and gate evidence. | REQ-010, REQ-012 |
| TST-027 | Exercise every prohibited plan transition. | Stable error category and byte-identical canonical/projection files. | REQ-010, REQ-012 |
| TST-028 | Exercise every allowed and prohibited task transition. | Task state follows the contract and phase rollup remains consistent. | REQ-010, REQ-011 |
| TST-029 | Complete a task without acceptance evidence. | Completion is rejected and the exact missing evidence is reported. | REQ-011 |
| TST-030 | Complete all tasks in a phase. | Phase becomes completed only when all required tasks pass or have approved skips. | REQ-010, REQ-011 |
| TST-031 | Skip a required task without current explicit approval. | Skip and plan completion are rejected. | REQ-010, REQ-011 |
| TST-032 | Revise material scope in ready or in-progress state. | Plan returns to draft and requires renewed coverage and approval. | REQ-010, REQ-012, REQ-016 |
| TST-033 | Run `list`, `show`, and `validate` on valid state. | Useful output and byte-identical files. | REQ-012 |
| TST-034 | Hold the catalog or plan lock during another write. | Second writer returns busy; first writer's state is unchanged. | REQ-009, REQ-012 |
| TST-035 | Read revision N, commit N+1, then submit N. | Stale update is rejected without overwrite. | REQ-009, REQ-010, REQ-012 |
| TST-036 | Interrupt before canonical replacement. | No canonical change; only transaction-owned temporary residue is diagnosable. | REQ-009, REQ-015 |
| TST-037 | Fail after canonical replacement but before projections/index. | Receipt reports canonical commit and projection failure; rebuild route repairs without repeating mutation. | REQ-009, REQ-012, REQ-015 |
| TST-038 | Alter or delete generated projections. | Validation detects drift; explicit rebuild restores them from canonical state. | REQ-009, REQ-012 |
| TST-039 | Corrupt canonical JSON or use an unknown schema version. | Catalog mutation stops; no record is skipped or guessed. | REQ-009, REQ-015 |
| TST-040 | Run explicit recovery twice on an approved recoverable fault. | First call repairs only the reviewed scope; second call is a valid no-op. | REQ-012, REQ-015 |
| TST-041 | Omit one source requirement from all tasks. | Forward coverage blocks readiness and names the missing requirement. | REQ-014, REQ-015 |
| TST-042 | Add a task with no requirement or design basis. | Reverse coverage reports an orphan task and blocks readiness. | REQ-014, REQ-015 |
| TST-043 | Remove a requirement and reuse its ID for another meaning. | Validation rejects ID reuse; explicit disposition is required. | REQ-004, REQ-014 |
| TST-044 | Leave a material open question or unconfirmed assumption. | Draft may save, but ready transition fails with exact unresolved items. | REQ-016 |
| TST-045 | Run Task/TRD/goal state with conflicting status. | Plan reports the mismatch and mutates no other state system. | REQ-013 |
| TST-046 | Render overview, phase files, traceability, and index twice. | Outputs are deterministic, split, complete, and byte-identical. | REQ-006, REQ-007, REQ-009, REQ-014 |
| TST-047 | Inspect an existing `Implementation_Plans/` containing unmanaged Markdown. | Existing files remain unchanged and absent from the managed catalog unless explicitly adopted later. | REQ-009, REQ-013, REQ-019 |
| TST-048 | Run package link, metadata, template, and README checks. | All referenced resources exist and documented operations match the helper. | REQ-017, REQ-018, REQ-020 |
| TST-049 | Copy package to an isolated temporary project and run create/show/validate/update/evidence/rebuild. | Package works without files outside its folder or project dependency installation. | REQ-017, REQ-020 |
| TST-050 | Inspect final worktree, manifest, targets, personal/global skill roots, Git index, and remotes. | Only authorized source/verification files changed; no install, registration, staging, commit, push, or publication occurred. | REQ-019 |

## 16. Failure modes and required controls

| Failure mode | Consequence | Required control |
| --- | --- | --- |
| Implicit activation | Unrequested plan writes | Explicit-only metadata plus SKILL routing and negative prompt test. |
| Wrong project root | Plan targets unrelated artifacts | Explicit root, guidance inspection, confinement checks, and ambiguity stop. |
| Source prompt injection | Permission or scope escalation | Treat sources as data and keep authority outside source content. |
| Unreadable input treated as read | Fabricated requirements | Record exact access limitation and stop or save an honest draft. |
| Stale project baseline | Wrong architecture or commands | Reinspect live files before plan creation, implementation, and completion. |
| One huge prose plan | Unreliable tracking and poor continuation | Canonical JSON plus overview, phase, traceability, and index projections. |
| Duplicate or recycled IDs | Broken history and coverage | Immutable stable IDs, collision checks, and explicit dispositions. |
| Dependency cycle | Non-executable plan | Full graph validation before ready and after every dependency change. |
| Manual phase/task status drift | False progress or completion | Derive phase status from task state and validate every rollup. |
| Completion without evidence | Unsupported success claim | Acceptance-level evidence gate and explicit completion confirmation. |
| Stale concurrent write | Lost progress | Revision/hash preconditions, per-plan locks, and double check after lock. |
| Canonical/projection partial failure | Confusing state | Canonical-first receipt, drift warning, and explicit idempotent rebuild. |
| Lock stolen while writer is active | Corruption | Never infer stale from age/PID alone; require reviewed recovery authority. |
| Existing Markdown plan treated as managed | Project-owned content corruption | Recognize only valid managed directories and preserve all unmanaged content. |
| Plan state merged with Task/TRD/goal state | Contradictory authority | Separate identifiers, APIs, files, and completion claims; report mismatches. |
| Secret or raw transcript stored | Privacy and security exposure | Minimal summaries, secret guard, size bounds, and explicit content rules. |
| Package uses files outside its folder | Non-portable delivery | Package inventory, isolated copy smoke test, and path audit. |
| Validator passes but behavior is wrong | False confidence | Contract tests, representative scenarios, forward/reverse audit, and manual intended-use review. |
| Source package is silently installed or registered | Scope violation | Final manifest/target/skill-root/Git audit and source-only stop condition. |

## 17. Risk register

| Risk | Likelihood | Impact | Mitigation | Residual validation |
| --- | --- | --- | --- | --- |
| Draft TRD decisions change after implementation begins | Medium | High | Phase 0 gates and hash/revision check; material changes return work to planning. | Compare live TRD and plan before every phase boundary. |
| `to-implementation-plan` is not the desired name | Medium | Medium | Treat as proposed and block initializer until confirmed. | Check folder, frontmatter, metadata, docs, and tests use one approved name. |
| Runtime schema becomes too complex | Medium | High | Standard-library JSON, one canonical file, deterministic projections, no database. | Review field necessity and remove speculative fields before code. |
| Canonical JSON becomes large | Medium | Medium | Split human projections, bound source/log content, store concise evidence/history. | Exercise a representative large plan and record file size/runtime without inventing a target. |
| URL behavior differs across hosts | High | Medium | Agent-level tool use, capability detection, exact limitations, no hard MCP dependency. | Test controlled accessible and inaccessible cases; state host limits. |
| PRD formats vary widely | High | Medium | Format-tolerant extraction plus source-linked ambiguity, not one rigid PRD parser. | Run structured and narrative fixtures. |
| Generated phase files drift | Medium | Medium | Canonical-only authority, deterministic rendering, drift detection, rebuild. | Byte-parity render and repair tests. |
| Existing plans conflict with generated index | Medium | High | Managed-directory recognition and preservation of unmanaged files. | Fixture containing all current Markdown plans. |
| Evidence is plausible but false | Medium | High | Label evidence source and require direct inspection for agent claims. | Manual sample review and negative evidence fixtures. |
| Partial filesystem transaction | Low | High | Lock, expected revision/hash, canonical-first atomic replacement, precise receipt. | Inject failures at transaction boundaries. |
| Skill instructions duplicate reference contracts | Medium | Medium | Progressive disclosure and one owner for each rule. | Duplication and link audit. |
| Future Codex skill format changes | Medium | Medium | Recheck official docs and current skill-creator before implementation. | Run current initializer and quick validator at delivery time. |
| Over-testing consumes time without adding confidence | Medium | Medium | Focus tests on observable contracts, failure modes, and user workflows. | Review each test's unique failure signal; remove duplicates. |
| Independent forward-testing is unavailable or unauthorized | Medium | Low | Use isolated same-agent scenarios; mark independent agent review not exercised. | Report the exact validation level without overstating. |

## 18. Planned verification commands

Paths and names below become runnable only after the source package exists. The
implementation must recheck tool paths rather than copying these commands blindly.

```bash
.venv/bin/python -m py_compile \
  SKILLS-depo/to-implementation-plan/scripts/plan_state.py \
  SKILLS-depo/to-implementation-plan/tests/test_plan_state.py

.venv/bin/python -m unittest discover \
  -s SKILLS-depo/to-implementation-plan/tests -v

/Users/alex.omegapy/.local/bin/uv run --with PyYAML -- python \
  /Users/alex.omegapy/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  SKILLS-depo/to-implementation-plan

.venv/bin/python SKILLS-depo/to-implementation-plan/scripts/plan_state.py \
  --project-root /absolute/disposable/project validate

git diff --check

git status --short
```

Additional final checks:

- Confirm no `__pycache__`, `.pyc`, `.DS_Store`, lock, or temporary file exists
  inside the delivery.
- Scan every new package and verification file directly for trailing whitespace,
  because untracked files are not covered by ordinary `git diff --check`.
- Confirm every Markdown link and every `SKILL.md` reference resolves.
- Compare `README.md`, `ACTIONS.md`, helper `--help`, and implemented subcommands.
- Compare package files before and after isolated-copy testing.
- Inspect `depot/manifest.json`, both managed target skill roots, personal/global
  skill roots, Git index, and remote state without mutating them.
- Reopen the source TRD, all 20 requirements, every package file, test output, and
  final verification report before claiming completion.

## 19. Requirement-to-work traceability matrix

| Requirement | Primary implementation work | Planned tests | Completion evidence |
| --- | --- | --- | --- |
| REQ-001 | IP-P01-T03, IP-P01-T04, IP-P05-T01, IP-P05-T02 | TST-002 through TST-004 | Frontmatter/metadata inspection and explicit/ordinary prompt behavior. |
| REQ-002 | IP-P02-T04, IP-P05-T04, IP-P06-T01 through IP-P06-T05 | TST-005 through TST-013 | Source records and representative prompt/file/TRD/PRD/URL artifacts. |
| REQ-003 | IP-P02-T01, IP-P02-T09, IP-P04-T05, IP-P06-T06 | TST-008, TST-013 through TST-015 | Adversarial-source, unsafe-path, secret, and no-execution results. |
| REQ-004 | IP-P02-T04, IP-P06-T01, IP-P06-T03, IP-P06-T04, IP-P06-T06, IP-P06-T08 | TST-005 through TST-011, TST-018 | Source-linked requirement/intent inventory with decisions and uncertainty separated. |
| REQ-005 | IP-P00-T01, IP-P02-T01, IP-P06-T07 | TST-016 through TST-018 | Live baseline citations, project-root decision, and no invented stack/path. |
| REQ-006 | IP-P02-T05, IP-P02-T08, IP-P06-T09 | TST-019, TST-046 | Valid phase records and split phase projections. |
| REQ-007 | IP-P02-T05, IP-P06-T09 | TST-020, TST-046 | Every task contains the complete task contract and belongs to one phase. |
| REQ-008 | IP-P02-T07, IP-P03-T03, IP-P04-T03, IP-P04-T04, IP-P06-T09 | TST-019, TST-021, TST-022 | Acyclic dependency report, order enforcement, and parallel-group review. |
| REQ-009 | IP-P02-T03, IP-P02-T05, IP-P02-T08, IP-P03 through IP-P04 | TST-023, TST-024, TST-034 through TST-040, TST-046, TST-047 | Canonical plan, revisions, history, projections, locks, and recovery receipts. |
| REQ-010 | IP-P02-T06, IP-P04-T03, IP-P04-T04, IP-P04-T06 | TST-026 through TST-032 | Complete transition matrix, rejection evidence, and consistent rollups. |
| REQ-011 | IP-P02-T05, IP-P04-T05, IP-P04-T06 | TST-029 through TST-031 | Evidence-gated task, phase, requirement, and plan completion. |
| REQ-012 | IP-P03-T04, IP-P03-T06, IP-P04-T02 through IP-P04-T09, IP-P05-T02 | TST-024 through TST-040 | Exact continuation, update, lifecycle, read-only, and recovery command receipts. |
| REQ-013 | IP-P02-T01, IP-P02-T09, IP-P05-T01, IP-P06-T07 | TST-014, TST-024, TST-045, TST-047, TST-050 | No Task/TRD/goal/manifest mutation and explicit mismatch reporting. |
| REQ-014 | IP-P02-T07, IP-P02-T08, IP-P03-T03, IP-P06-T09 | TST-009 through TST-011, TST-041 through TST-043, TST-046 | Zero missing source requirements and zero orphan tasks in coverage reports. |
| REQ-015 | IP-P02-T07, IP-P03-T03, IP-P03-T06, IP-P06-T07, IP-P06-T09 | TST-013, TST-016 through TST-018, TST-021, TST-039 through TST-044 | Validation separates pass/fail/unresolved/not-exercised and blocks false readiness. |
| REQ-016 | IP-P00-T04, IP-P02-T04, IP-P05-T04, IP-P06-T08 | TST-011, TST-017, TST-018, TST-032, TST-044 | Fast path, one-question flow, draft-now behavior, and readiness blocker evidence. |
| REQ-017 | IP-P01, IP-P05-T06, IP-P05-T07, IP-P09 | TST-001, TST-002, TST-048 through TST-050 | Complete self-contained `SKILLS-depo/to-implementation-plan/` tree and README. |
| REQ-018 | IP-P00-T03, IP-P01-T01, IP-P01-T06, IP-P09-T03 | TST-001, TST-002, TST-048 | Recorded skill-creator use and current quick-validator pass. |
| REQ-019 | IP-P00-T05, IP-P01-T01, IP-P09-T05 through IP-P09-T07, IP-P10-T04 | TST-014, TST-045, TST-047, TST-049, TST-050 | Diff/status audit proves source-only delivery and no registration/install/external action. |
| REQ-020 | IP-P05-T06, IP-P07, IP-P08, IP-P09, IP-P10-T03, IP-P10-T06 | TST-001 through TST-050 | README, full test output, behavioral records, package validation, and final report. |

## 20. Bidirectional verification procedure

### 20.1 Forward audit

1. Parse all requirement IDs and acceptance lines from the live source TRD.
2. Confirm each requirement appears in at least one implementation task row.
3. Confirm each requirement appears in the traceability matrix exactly once as a
   primary row.
4. Confirm each requirement maps to at least one observable test or inspection.
5. Confirm each acceptance criterion maps to a planned artifact or observed
   behavior, not only a document statement.
6. Confirm exclusions and decisions map to scope controls or negative tests.
7. Report missing work, tests, evidence, or decisions as blocking gaps.

### 20.2 Reverse audit

1. Enumerate every phase, task, proposed file, schema field group, command,
   lifecycle state, test, and external dependency.
2. Trace each item to a source requirement or a necessary quality basis that
   supports one or more requirements.
3. Reject orphan features, speculative files, duplicate state systems,
   unnecessary dependencies, and unrequested installation/publication work.
4. Confirm all task dependencies resolve and the combined graph is acyclic.
5. Confirm no phase or task is silently deferred outside the definition of done.

### 20.3 Final evidence audit

1. Reopen current artifacts rather than trusting prior receipts or summaries.
2. Recompute file hashes and coverage counts.
3. Compare planned commands with commands actually run.
4. Record pre-existing failures separately from implementation regressions.
5. State the highest verification level actually reached and name end-to-end
   behavior that was not exercised.

## 21. Rollback, recovery, and preservation strategy

### 21.1 Before registration or installation

The source package is additive and unregistered. If implementation must be
abandoned, preserve the reviewed source and verification evidence or move the
exact new folder to an authorized archive. Do not delete it without an explicit
user instruction. No consumer rollback is needed because consumers were not
changed.

### 21.2 During helper development

- Run mutation tests only in temporary project roots.
- Keep fixtures inside temporary directories and remove them after the test.
- Never point fault-injection tests at this live Sys4AI checkout.
- Preserve unrelated dirty files and recheck the exact change set after each
  phase.
- If a write spreads beyond the approved source folder, stop, inspect, and
  restore only with explicit authority.

### 21.3 After later registration or installation

Registration and installation require a separate plan and authorization. That
later plan must identify every target, review drift, preserve target-only files,
apply through depot synchronization, test consumers, and provide a reversible
rollback. This initial plan does not define or authorize those writes.

## 22. Definition of done for the future implementation

The future implementation is complete only when all statements below are true:

- GATE-001 through GATE-007 have recorded user decisions.
- `SKILLS-depo/to-implementation-plan/` contains the complete approved package.
- `SKILL.md` is explicit-only, concise, discriminating, and routes every operation.
- `README.md` explains context, package, installation, use, inputs, outputs,
  tracking, lifecycle, validation, evidence, recovery, and source-only scope.
- `agents/openai.yaml` matches the skill and passes current validation.
- `plan_state.py` implements every documented command and error category.
- Canonical state, projections, identity, selectors, schema, dependencies,
  lifecycle, evidence, locks, atomic writes, recovery, and unmanaged-plan safety
  conform to the contract.
- Prompt, text, file, TRD, PRD, and URL workflows have representative evidence.
- Every supported state and transition has a passing positive or negative test.
- Every source requirement maps to work or an explicit authorized disposition.
- Every task, file, command, schema group, and test traces to an approved basis.
- All focused tests, compile checks, skill validation, links, and package smoke
  checks pass.
- No unfinished placeholder, secret, transcript, cache, temporary file, stale
  lock, or generated junk remains in the delivery.
- `depot/manifest.json`, `.agents/skills`, consumer projects, personal/global
  skills, Git index, remotes, and external systems remain unchanged.
- The verification report states hashes, commands, counts, coverage, failures,
  limitations, and the highest verification level reached.
- The source package was not represented as installed or live-tested in Codex.

## 23. Plan-level validation record

This section records validation of this implementation plan, not implementation
of the future skill.

| Check | Planned result field |
| --- | --- |
| Source TRD identity and hash | Rechecked against current file before final report. |
| Requirement count | 20 unique requirements expected. |
| Phase count | 11 unique phases expected. |
| Task count | 84 unique implementation tasks expected. |
| Forward requirement coverage | Every REQ-001 through REQ-020 must appear in task work and the traceability matrix. |
| Reverse task coverage | Every task must cite at least one REQ identifier. |
| Task dependency validity | Every dependency must exist and the graph must be acyclic. |
| Phase dependency validity | Every dependency must exist and the graph must be acyclic. |
| Test coverage | TST-001 through TST-050 expected, each linked to requirements. |
| Placeholder and Markdown checks | No unfinished template markers, malformed fences, or trailing whitespace. |
| Change boundary | Only the new plan and its verification report may be added this turn. |
| Implementation status | 0 of 84 tasks completed; skill package does not yet exist. |

The executed results and plan hash belong in the separate verification report so
this plan does not attempt to contain its own final digest.

## 24. Logical next step

The next step is a human decision on GATE-001 through GATE-007, beginning with
the exact skill name. Only after those decisions and a separate implementation
authorization may Phase IP-P00 change from `planned` and begin.
