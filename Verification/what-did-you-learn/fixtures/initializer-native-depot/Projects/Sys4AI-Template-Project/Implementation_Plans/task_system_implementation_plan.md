# Project-local Task system implementation plan

## Document control

- **Status:** Proposed implementation plan
- **Plan date:** 2026-08-27
- **Target project:** Generic Template Project
- **Project root:** `/Volumes/P-SSD/Template-Project`
- **Planned system name:** Task system
- **Planned user-facing skill:** Task
- **Planned internal skill:** Agent Task
- **Implementation authority:** This document authorizes planning only. It does
  not authorize implementation, task creation, skill creation, configuration
  changes, commits, publication, or deployment.
- **Primary purpose:** Define every artifact, rule, lifecycle transition,
  failure behavior, verification activity, and acceptance criterion needed to
  implement a project-local Task system that the Project Director can continue
  across independent Codex threads.

## 1. Executive intent

The project must implement a durable Task system in which a user explicitly
invokes a local **Task** skill to start, continue, inspect, pause, complete, or
cancel project work. The existing root agent remains the Project Director. The
Task skill does not spawn a second director and does not create a new Codex
thread. It activates a controlled task-management workflow in the current
Project Director thread.

The Project Director will use a separate local **Agent Task** skill to perform
deterministic task-state operations. Task identity and lifecycle state will be
stored under the project root in `Tasks/`. Each task will have a stable task
identifier, a folder whose name contains `Task`, the task name, and the creation
date, a machine-readable state file, a human-readable task brief, and an
append-only sequence of Markdown Task Response records.

The architecture must solve five distinct problems:

1. Explicit user activation without accidental implicit task creation.
2. Unambiguous selection between a new task and continuation of an existing
   task.
3. Durable project-local state that survives a closed, compacted, or replaced
   conversation thread.
4. A complete Task Response record for every final Project Director turn that
   belongs to the task.
5. Safe recovery from ambiguous names, stale summaries, concurrent updates,
   partial writes, missing files, and corrupt state.

The task is the durable object. A Codex thread is only an interaction channel
that may be associated with the task. Neither the most recent thread nor the
most recently updated task automatically determines the user's current intent.

## 2. Scope boundary

### 2.1 In scope for the later implementation

- Create the project-local user-facing `task` skill.
- Create the project-local internal `agent-task` skill.
- Configure both skills with accurate Codex metadata and invocation policy.
- Create the root `Tasks/` directory and its generated human-facing index.
- Define and implement the canonical task-state schema.
- Define and implement the `TASK.md` human-readable projection.
- Define and implement the timestamped Task Response Markdown format.
- Implement deterministic task creation, resolution, continuation, response
  recording, state transition, listing, validation, and index regeneration.
- Add first-turn task awareness to the root project guidance.
- Integrate task ownership into the existing Project Director role.
- Keep ordinary non-task conversation and ordinary project work available.
- Support more than one nonterminal task without treating one global pointer
  as authoritative.
- Support explicit parent-child relationships between related tasks.
- Protect task writes with locks, expected revisions, safe path handling, and
  atomic file replacement.
- Detect and report partial or corrupt state without guessing.
- Add focused unit, contract, behavioral, and cross-thread tests.
- Update project documentation with user commands and operating rules.
- Perform a final bidirectional requirement audit.

### 2.2 Out of scope for the initial implementation

- Global or personal skills under `~/.agents`, `~/.codex`, or another user
  directory.
- A remote task-management service.
- A hosted database, server, daemon, background process, or MCP server.
- Automatic plugin installation.
- A dependency on Codex-generated memories as authoritative task state.
- Treating native `/goal` state as the cross-thread Task registry.
- Automatically creating, forking, moving, renaming, pinning, or archiving a
  user-visible Codex thread.
- Spawning another Project Director.
- Allowing sub-agents to own or mutate the canonical Task ledger directly.
- Storing hidden reasoning, complete transcripts, credentials, secrets, or
  large raw logs in Task Response files.
- Fuzzy automatic selection among ambiguous task names.
- A full Temporal-style workflow engine, event database, or distributed lock
  service.
- Task analytics, time billing, performance scores, dashboards, or remote
  notifications.
- A migration of unrelated existing project files.
- Git initialization, commit, push, publication, or deployment.

### 2.3 Explicit current-turn boundary

This implementation plan is the only project artifact to be created in the
current goal. The skills, scripts, schemas, templates, `Tasks/` directory,
tests, and project-guidance changes described below belong to a later,
explicitly authorized implementation task.

## 3. Observed project baseline

The later implementation must recheck this baseline before editing because the
project may change after this plan is approved.

| Item | Observed state on 2026-08-27 | Implementation consequence |
| --- | --- | --- |
| Root `AGENTS.md` | Exists and requires `SOUL.md` and `ROLE.md` first reads | Add only the narrow Task-awareness and Task-routing integration. |
| Root `SOUL.md` | Exists and requires the communication skill | Preserve it unless a later approved requirement directly requires a change. |
| Root `ROLE.md` | Exists and defines the Project Director | Add only Task-system ownership that is not already expressed. |
| Root `README.md` | Exists and documents the template and role system | Add Task-system usage without rewriting unrelated setup guidance. |
| `Implementation_Plans/` | Exists with a detailed implementation-plan convention | Store this plan in that directory. |
| `.agents/skills/communication/` | Exists | Reuse it; do not duplicate it. |
| `.agents/skills/manage-subagent-roles/` | Exists with scripts and tests | Preserve it and define how delegated results return to the Director. |
| `.agents/skills/task/` | Absent | Create it only during the later implementation. |
| `.agents/skills/agent-task/` | Absent | Create it only during the later implementation. |
| `Tasks/` | Absent | Create it only during the later implementation. |
| Project Python | `.venv/bin/python`, Python 3.12.13 | Use the project interpreter for Task helper tests. |
| Skill validator dependency | Project `.venv` lacks PyYAML | Use the observed `uv --with PyYAML` validation wrapper; do not install PyYAML globally or add it to the project solely for validation. |
| Git repository | Not detected at the project root | Do not use Git history as the only drift check or claim staged, committed, or pushed state. |
| `.gitignore` | Does not ignore `Tasks/` | Keep durable Task records visible; ignore only ephemeral lock and temporary-write paths if those paths are created. |

## 4. Authority and source precedence

The later implementation and every Task invocation must use this precedence:

1. Platform, safety, permission, sandbox, and tool constraints.
2. The user's current explicit instructions and approved Task objective.
3. Root `SOUL.md`.
4. Root `ROLE.md` for the Project Director.
5. Root `AGENTS.md`.
6. The user-facing `task` skill.
7. The internal `agent-task` skill and its schema reference.
8. Canonical live task state under `Tasks/`.
9. The current thread transcript and task-associated Task Response records.
10. Codex memory, generated indexes, and other retrieval aids.

Lower-precedence sources can add context but cannot weaken authority,
permissions, protected scope, or current live evidence. A Task Response is a
continuation record. It does not prove that an artifact still exists or that a
reported check remains current. The Project Director must inspect live
artifacts when they affect the next action or completion claim.

## 5. Compatibility and research basis

### 5.1 Official Codex behaviors used

The design relies on these current documented behaviors:

- Repository-local skills are discovered under `.agents/skills/`.
- A skill contains a required `SKILL.md` with `name` and `description`.
- Skills use progressive disclosure.
- `agents/openai.yaml` can set `policy.allow_implicit_invocation: false`,
  preserving explicit `$skill-name` invocation while disabling implicit
  invocation.
- Codex reads applicable `AGENTS.md` guidance at the start of a run.
- Local projects give related chats access to the same project files and
  durable project instructions, while each chat retains its own transcript.
- Codex memories are a helpful recall layer and can update later or be skipped;
  required project rules belong in `AGENTS.md` or checked-in documentation.
- Native `/goal` is useful for long-running work in the same chat or session,
  but it is not a replacement for the project-local cross-thread Task ledger.

Official sources:

- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Projects and chats](https://learn.chatgpt.com/docs/projects)
- [Memories](https://learn.chatgpt.com/docs/customization/memories)
- [Long-running work](https://learn.chatgpt.com/docs/long-running-work)

### 5.2 Agent Skills format constraints

The implementation must follow the open Agent Skills naming and structure
rules. Skill names and their folder names will be lowercase and hyphenated,
even though the user-facing display names are title-cased.

Reference:

- [Agent Skills specification](https://agentskills.io/specification)

### 5.3 Local continuation patterns consulted

The following local sources informed the persistence and handoff design but are
not runtime dependencies of this Task system:

- `/Volumes/P-SSD/AngryOwl/The-AEther-Flow/.codex/skills/continue-research/SKILL.md`
- `/Volumes/P-SSD/AngryOwl/The-AEther-Flow/scripts/research_control/continue_research.py`
- `/Volumes/P-SSD/AngryOwl/The-AEther-Flow/research_control/handoffs/README.md`
- `/Volumes/P-SSD/AngryOwl/Sys4AI-dev/development/bootstrap-agent/skills/context-window-and-handoff-manager/SKILL.md`

The reusable principles are tracked state, separate machine and human views,
bounded continuation, current-state verification, and memory as navigation.
The scientific AgentJob, decision-record, claim-promotion, checkpoint, and
relay machinery must not be copied into this generic system.

## 6. Terms

| Term | Meaning |
| --- | --- |
| Task | A durable project objective with one stable task identifier and one task folder. |
| Task system | The two skills, state helper, project guidance, task files, response history, and validation behavior defined by this plan. |
| Task skill | The explicit-only user-facing `task` skill that interprets user intent and routes the Project Director. |
| Agent Task skill | The internal `agent-task` skill that defines deterministic state operations for the Project Director. |
| Project Director | The root agent governed by root `ROLE.md`; the owner of task framing, execution coordination, response logging, and completion. |
| Task folder | One immediate child of `Tasks/` whose name includes `Task`, the task slug, the creation date, and a stable short identifier. |
| Task state | Canonical machine-readable state in a task folder's `task.json`. |
| Task brief | The human-readable `TASK.md` projection of the task objective and current state. |
| Task Response | One timestamped Markdown record summarizing one final Project Director turn associated with a task. |
| Nonterminal task | A task in `open`, `paused`, `awaiting_user`, or `blocked` state. |
| Terminal task | A task in `completed` or `cancelled` state. |
| Continuation | Further work toward the same durable objective in the same task folder. |
| Related new task | A different deliverable linked to an earlier task with `parent_task_id`. |
| Thread reference | Optional metadata identifying a Codex thread when the runtime exposes a stable identifier; it never defines task identity. |
| Generated projection | A human-readable file derived from canonical task state and safe to regenerate. |
| Revision | A monotonic integer used to reject stale concurrent updates. |
| Response sequence | A monotonic per-task integer used to order Task Response files. |

## 7. Complete requirement catalog

### 7.1 Architecture, authority, and locality requirements

- **ARC-001:** Implement the Task system entirely inside the project root.
- **ARC-002:** Create no global or personal Task skill, state, task folder,
  configuration, or registry.
- **ARC-003:** Treat the durable task, not a conversation thread, as the
  primary continuation object.
- **ARC-004:** Keep the existing root agent as the Project Director when the
  Task skill activates.
- **ARC-005:** Do not spawn another Project Director or create a user-visible
  Codex thread merely because the user creates a Task-system task.
- **ARC-006:** Use the flow `user -> task skill -> Project Director -> agent-task
  skill -> deterministic helper -> Tasks/ state`.
- **ARC-007:** Store authoritative task identity and lifecycle state in project
  files, not in Codex memory, thread titles, or generated summaries.
- **ARC-008:** Permit native `/goal` to coexist with a task only as an optional
  same-thread execution aid; never use it as the Task registry.
- **ARC-009:** Keep generated indexes and memories as navigation aids whose
  claims must be checked against canonical task state and live artifacts.
- **ARC-010:** Preserve the existing Project Director, sub-agent role system,
  communication skill, and unrelated project behavior.

### 7.2 User-facing Task skill requirements

- **USR-001:** Create `.agents/skills/task/` with a valid `SKILL.md`.
- **USR-002:** Use the machine name `task` and the user-facing display name
  `Task`.
- **USR-003:** Configure `policy.allow_implicit_invocation: false` in
  `task/agents/openai.yaml`.
- **USR-004:** Require explicit `$task` invocation to create a new tracked task;
  permit continuation of an existing task after the user explicitly selects it
  by ID/name or confirms a first-turn resume offer.
- **USR-005:** Support user intents for `new`, `continue`, `status`, `list`,
  `update`, `pause`, `complete`, `cancel`, and explicit `reopen`.
- **USR-006:** Accept a task name, description, definition of done, and optional
  parent-task reference when supplied by the user.
- **USR-007:** Request only missing information that materially affects task
  identity, scope, selection, or completion criteria.
- **USR-008:** When `$task` has no explicit mode, inspect current nonterminal
  tasks before asking whether the user wants a new task or a continuation.
- **USR-009:** Keep status and list operations read-only.
- **USR-010:** Never mutate task state merely because an ordinary prompt uses
  words such as "task," "work," "next," or "continue" outside explicit Task
  activation or the cross-thread continuation rules.
- **USR-011:** Route state operations through the Agent Task contract instead
  of constructing task paths or JSON freehand.
- **USR-012:** If invoked outside an unambiguous project root or by an agent
  that does not own Project Director authority, stop and report the boundary.

### 7.3 Internal Agent Task skill requirements

- **AGT-001:** Create `.agents/skills/agent-task/` with a valid `SKILL.md`.
- **AGT-002:** Use the machine name `agent-task` and the display name
  `Agent Task`.
- **AGT-003:** Define Agent Task as a Project Director workflow, not a second
  user-facing entry point.
- **AGT-004:** Configure Agent Task so it cannot be selected implicitly for
  unrelated prompts.
- **AGT-005:** Require Agent Task to establish the project root and confine all
  task-state paths to `<project-root>/Tasks/`.
- **AGT-006:** Provide deterministic operations for `status`, `list`, `new`,
  `continue`, `update`, `record-response`, `pause`, `complete`, `cancel`, and
  `validate`.
- **AGT-007:** Provide an explicit repair or index-regeneration operation that
  never silently changes canonical task meaning.
- **AGT-008:** Put detailed schemas, lifecycle rules, and recovery procedures in
  a focused reference linked from `SKILL.md`.
- **AGT-009:** Put reusable `TASK.md`, Task Response, and `INDEX.md` structures
  in assets when the helper renders those assets directly.
- **AGT-010:** Implement repeated filename, state-transition, and validation
  logic in a standard-library-only Python helper.
- **AGT-011:** Return structured JSON for internal decisions and concise
  Markdown or text for human-facing status.
- **AGT-012:** Fail closed when task identity, state, path safety, revision,
  lifecycle, or response history cannot be established.

### 7.4 Storage, identity, and naming requirements

- **STO-001:** Create the root directory `Tasks/`, with an uppercase `T` and
  plural `s`.
- **STO-002:** Create `Tasks/INDEX.md` as a generated human-readable task
  catalog.
- **STO-003:** Store each task in exactly one immediate child directory of
  `Tasks/`.
- **STO-004:** Use the folder pattern
  `Task-<task-slug>-<YYYY-MM-DD>--<short-id>`.
- **STO-005:** Ensure the folder name contains the word `Task`, a safe form of
  the task name, and the local creation date.
- **STO-006:** Allocate a stable ID such as `TASK-YYYYMMDD-XXXXXXXX`; the ID,
  not the mutable display name, is the durable identity.
- **STO-007:** Prevent collisions for two tasks with the same name and creation
  date by including a unique short identifier.
- **STO-008:** Preserve the user's original task name in canonical state and
  the task brief.
- **STO-009:** Generate a safe slug with deterministic Unicode normalization,
  ASCII alphanumeric retention, hyphen collapse, length bounding, and a safe
  fallback when no characters remain.
- **STO-010:** Never automatically rename a task folder when the display name
  changes.
- **STO-011:** Create `task.json`, `TASK.md`, and `responses/` inside every task
  folder.
- **STO-012:** Store all Task Response files only under the owning task's
  `responses/` directory.
- **STO-013:** Use local host time with an explicit UTC offset for recorded
  timestamps; do not hardcode a daylight-saving abbreviation.
- **STO-014:** Use filename-safe timestamps while keeping the full ISO 8601
  timestamp in Markdown titles and structured state.

### 7.5 Canonical state and Task Response requirements

- **STA-001:** Make `task.json` authoritative for machine-readable identity and
  lifecycle state.
- **STA-002:** Include `schema_version`, `task_id`, `name`, `original_name`,
  `slug`, `folder_name`, `description`, `definition_of_done`, `created_at`,
  `updated_at`, `status`, `parent_task_id`, `revision`, `response_count`,
  `last_response`, `current_summary`, `next_step`, `blockers`,
  `open_questions`, and optional `thread_refs` in the state contract.
- **STA-003:** Make `TASK.md` a generated human-readable projection of the
  objective, scope, definition of done, current status, current summary,
  blockers, open questions, and next step.
- **STA-004:** Treat `INDEX.md` as a generated catalog, never as authority over
  a task's `task.json`.
- **STA-005:** List task ID, name, status, creation time, update time, parent,
  latest response, and next step in `INDEX.md`.
- **STA-006:** Create one Task Response for each final Project Director turn
  that performs, decides, changes, or substantively explains work for a
  selected task. Exclude pure read-only `status`/`list` queries and automatic
  first-turn resume notices.
- **STA-007:** Do not create Task Response files for transient commentary,
  progress updates, tool output, or internal reasoning.
- **STA-008:** Name response files
  `Task-Response-<sequence>-<filename-safe-timestamp>.md`.
- **STA-009:** Use the H1 title `Task Response - <full ISO timestamp>` or the
  typographically equivalent visible title with the same information.
- **STA-010:** Include task name, task ID, response ID, timestamp, task
  description, work completed, verification evidence, user-facing response
  summary, status after the response, next step or required decision,
  blockers/open questions, and relevant files in every Task Response.
- **STA-011:** When the task is complete, record the explicit conclusion
  `Task completed. No next step required.` unless a more specific approved
  closing statement is required.
- **STA-012:** Keep Task Responses append-only during ordinary operation;
  record corrections in a new response with `supersedes_response_id`.
- **STA-013:** Permit direct alteration of an old response only for an
  explicitly authorized security, privacy, or secret-removal correction, and
  record that correction.
- **STA-014:** Never store hidden chain-of-thought, credentials, access tokens,
  private keys, passwords, unnecessary personal data, full transcripts, or
  large raw logs in Task files.

### 7.6 Lifecycle and task-resolution requirements

- **LIF-001:** Support the statuses `open`, `paused`, `awaiting_user`,
  `blocked`, `completed`, and `cancelled`.
- **LIF-002:** Treat `open`, `paused`, `awaiting_user`, and `blocked` as
  nonterminal.
- **LIF-003:** Treat `completed` and `cancelled` as terminal.
- **LIF-004:** Create a new task only from explicit new-task intent or an
  explicit decision after ambiguity is presented.
- **LIF-005:** Continue work toward the same objective in the same task folder.
- **LIF-006:** Create a new related task for a materially different deliverable
  and link it through `parent_task_id`.
- **LIF-007:** Validate that a non-null parent exists and reject parent cycles.
- **LIF-008:** Never infer that the most recently updated task is the task the
  user intends; use recency only to order candidates.
- **LIF-009:** Resolve an exact task ID before considering a name.
- **LIF-010:** Accept an exact unique name or unique safe ID prefix; report
  ambiguity instead of using fuzzy selection.
- **LIF-011:** With no nonterminal tasks, ask for the information needed to
  define a new task when `$task` is invoked without a mode.
- **LIF-012:** With exactly one nonterminal task, show its ID, name, and concise
  description before asking whether to continue it or create a new task.
- **LIF-013:** With multiple nonterminal tasks, show the most recently updated
  candidates with stable IDs and request an explicit selection or new-task
  decision.
- **LIF-014:** Never reopen a terminal task automatically; require an explicit
  user decision to reopen a completed task, and prefer a new related task for a
  new deliverable or a cancelled predecessor.

### 7.7 Cross-thread awareness and memory requirements

- **CTX-001:** Add a concise root `AGENTS.md` rule that performs a read-only
  Task status check on the first assistant turn of a new project thread.
- **CTX-002:** Do not claim that the agent can prompt the user before the user
  sends the first message in an empty thread.
- **CTX-003:** When no nonterminal tasks exist, add no Task notice to an
  ordinary first response.
- **CTX-004:** When exactly one nonterminal task exists, provide a concise,
  non-blocking resume offer with task ID, name, and description unless the user
  has already invoked `$task` or clearly selected that task.
- **CTX-005:** When multiple nonterminal tasks exist, provide a concise count
  and candidate route rather than silently choosing one.
- **CTX-006:** Answer unrelated user questions normally and perform no task
  mutation merely because a Task exists.
- **CTX-007:** Treat explicit continuation language such as `continue`,
  `resume`, or `pick up` as a reason to inspect candidates, not as proof of one
  task's identity.
- **CTX-008:** On continuation, load the selected task's canonical state,
  `TASK.md`, latest Task Response, and only the older responses or referenced
  files needed for the next decision.
- **CTX-009:** Verify material task claims against live project artifacts
  before acting or claiming completion.
- **CTX-010:** Keep thread IDs or titles optional; continuation must work when
  the runtime exposes no stable current-thread identifier.
- **CTX-011:** Use Codex memory only to help locate context and never as the
  sole authority for task identity, status, scope, completion, or next action.
- **CTX-012:** Keep native goal state and Task-system state separate and report
  any mismatch rather than silently merging them.

### 7.8 Reliability, concurrency, recovery, and security requirements

- **REL-001:** Perform state mutations through one deterministic helper rather
  than freehand edits by the Project Director.
- **REL-002:** Acquire an atomic directory-based lock before a task mutation;
  use a separate root/index lock for task creation and index regeneration when
  needed.
- **REL-003:** Record lock ownership metadata sufficient to diagnose a
  collision without storing secrets.
- **REL-004:** Never steal or delete an apparently stale lock automatically;
  require inspection and an explicit recovery action.
- **REL-005:** Require the caller's expected revision and reject the update if
  canonical state advanced after it was read.
- **REL-006:** Increment `revision` and `response_count` monotonically.
- **REL-007:** Write replacement content to a temporary file in the same
  directory and publish it with an atomic replace operation.
- **REL-008:** For a response transaction, publish the new Task Response,
  update `task.json`, regenerate `TASK.md`, and regenerate `INDEX.md` in that
  recoverable order.
- **REL-009:** Treat `INDEX.md` and `TASK.md` as regenerable projections so a
  projection-write failure cannot change canonical task meaning.
- **REL-010:** Detect orphan responses, missing response targets, sequence
  gaps, malformed JSON, schema mismatches, folder/ID mismatches, invalid parent
  references, latest-response/status mismatches, projection drift, and unsafe
  links.
- **REL-011:** Stop mutation and return exact diagnostics when integrity cannot
  be proved.
- **REL-012:** Provide an explicit validation and reconciliation route; never
  silently invent missing work summaries or status transitions.
- **REL-013:** Reject absolute paths, `..` traversal, control characters,
  hidden task targets, symlink escapes, and paths outside the project `Tasks/`
  root.
- **REL-014:** If durable response recording fails, disclose the failure and do
  not tell the user that the Task record was successfully updated.

### 7.9 Project Director and sub-agent integration requirements

- **DIR-001:** Make the Project Director responsible for Task classification,
  task selection, scope, definition of done, state transition approval,
  response summaries, and final completion claims.
- **DIR-002:** Require the Project Director to use Agent Task before mutating
  task state.
- **DIR-003:** Require the Project Director to record one Task Response before
  delivering each substantive task-work or task-decision final response, with
  the documented read-only query and startup-notice exceptions.
- **DIR-004:** Record what was actually completed and verified; do not promote
  plans, intent, a child-agent report, or unobserved behavior to completion.
- **DIR-005:** Use `awaiting_user` when a user decision is required and
  `blocked` only when progress cannot continue under current authority or
  available state.
- **DIR-006:** Mark `completed` only when the task definition of done has been
  checked against current evidence.
- **DIR-007:** Keep Project Director completion reporting consistent with the
  existing `ROLE.md` verification and validation duties.
- **DIR-008:** Permit role-based sub-agents to perform bounded task work only
  through the existing `manage-subagent-roles` workflow.
- **DIR-009:** Prevent child agents from creating task folders, changing
  canonical task status, or writing final Task Responses; they return evidence
  to the Project Director, who integrates and records it.
- **DIR-010:** Do not infer authority for destructive actions, external writes,
  commits, pushes, publication, deployment, or dependency installation from
  Task activation.

### 7.10 Documentation and verification requirements

- **VER-001:** Update root `AGENTS.md` with the smallest complete first-turn
  awareness and Task-routing contract.
- **VER-002:** Update root `ROLE.md` only where Task-system ownership is not
  already covered by general Project Director duties.
- **VER-003:** Update root `README.md` with Task commands, new-versus-continue
  behavior, storage structure, response logging, and cross-thread use.
- **VER-004:** Update `.gitignore` only for generated lock or temporary paths;
  do not ignore the durable `Tasks/` ledger as a whole.
- **VER-005:** Validate both new skills with the bundled skill validator.
- **VER-006:** Use the observed command
  `/Users/alex.omegapy/.local/bin/uv run --with PyYAML -- python
  /Users/alex.omegapy/.codex/skills/.system/skill-creator/scripts/quick_validate.py
  <skill-path>` unless current state supplies a simpler working validator.
- **VER-007:** Add focused standard-library tests for the state helper and
  schema.
- **VER-008:** Test explicit-only invocation metadata and discriminating skill
  descriptions.
- **VER-009:** Test task creation, same-name collision handling, safe slugging,
  required folder contents, and index generation.
- **VER-010:** Test every allowed and prohibited lifecycle transition,
  including terminal-task continuation behavior.
- **VER-011:** Test exact, prefix, name, ambiguous, absent, and corrupt task
  resolution.
- **VER-012:** Test Task Response sequence, filename, title, required sections,
  completion statement, supersession, and secret/log exclusion guidance.
- **VER-013:** Test read-only status/list behavior and prove that an unrelated
  prompt path causes no Task mutation.
- **VER-014:** Test revision conflicts, lock conflicts, partial transactions,
  orphan responses, projection drift, path traversal, and symlink escape.
- **VER-015:** Perform a manual cross-thread scenario that creates a task in
  one thread, opens a new thread, presents the resume offer, selects the task,
  validates live state, continues it, and creates the next Task Response.
- **VER-016:** Inspect the final tree and prove that all Task-system skills,
  state, scripts, tests, and templates remain project-local and that no global
  files, user-visible Codex tasks, commits, or pushes were created.

## 8. Immutable initial design decisions

Unless the user explicitly revises this plan before implementation, the first
implementation will use these decisions:

1. The system has two skills, `task` and `agent-task`.
2. The Task skill is explicit-only. New task creation requires `$task`; an
   existing task can continue after the user explicitly selects it or confirms
   a resume offer.
3. The Agent Task skill is internal to the Project Director and is not an
   alternate user entry point.
4. The system uses project files and a Python standard-library helper, not a
   database or remote service.
5. `task.json` is canonical machine state.
6. `TASK.md` and `INDEX.md` are generated human-readable projections.
7. Task Responses are append-only records of final Director turns.
8. Multiple nonterminal tasks are allowed.
9. No single global `current_task` pointer is authoritative.
10. Recency orders suggestions but never proves user intent.
11. Thread references are optional metadata.
12. The default new-thread behavior is a read-only check and a non-blocking
    resume offer, not a forced task-selection question for unrelated prompts.
13. Canonical writes use locks, expected revisions, temporary files, and
    atomic replace operations.
14. Child agents return evidence to the Project Director and do not mutate the
    Task ledger.
15. The implementation does not create or manage native Codex goals or
    user-visible threads automatically.

## 9. Proposed file architecture

The later implementation should produce this structure:

~~~text
Template-Project/
|-- AGENTS.md
|-- SOUL.md
|-- ROLE.md
|-- README.md
|-- .gitignore
|-- Tasks/
|   `-- INDEX.md
|-- .agents/
|   `-- skills/
|       |-- task/
|       |   |-- SKILL.md
|       |   `-- agents/
|       |       `-- openai.yaml
|       `-- agent-task/
|           |-- SKILL.md
|           |-- agents/
|           |   `-- openai.yaml
|           |-- references/
|           |   `-- task-system-contract.md
|           |-- scripts/
|           |   `-- task_state.py
|           |-- assets/
|           |   |-- TASK.md.template
|           |   |-- Task-Response.md.template
|           |   `-- INDEX.md.template
|           `-- tests/
|               `-- test_task_state.py
`-- Implementation_Plans/
    |-- subagent_role_system_implementation_plan.md
    `-- task_system_implementation_plan.md
~~~

After the user creates tasks, the runtime structure will expand as follows:

~~~text
Tasks/
|-- INDEX.md
|-- .locks/                                  Ephemeral and ignored
|-- .tmp/                                    Ephemeral and ignored
|-- Task-create-task-system-2026-08-27--A1B2C3D4/
|   |-- task.json
|   |-- TASK.md
|   `-- responses/
|       |-- Task-Response-0001-2026-08-27T14-35-22-06-00.md
|       `-- Task-Response-0002-2026-08-27T16-08-03-06-00.md
`-- Task-another-objective-2026-08-28--E5F6A7B8/
    |-- task.json
    |-- TASK.md
    `-- responses/
~~~

Do not add skill-specific README files, changelogs, examples, icons,
dependencies, or placeholder directories unless a concrete later requirement
justifies them. The `assets/` files are required only if `task_state.py`
actually renders them. If the implementation safely holds short templates in
code and tests prove the exact output, omit unused asset files and update this
plan's file inventory before implementation approval.

## 10. Skill specifications

### 10.1 User-facing Task skill

The Task skill must be a concise intent router. It must not duplicate the full
task schema or implement file mutation in prose.

Required frontmatter shape:

```yaml
---
name: task
description: Start, continue, inspect, update, pause, complete, or cancel a project-local tracked task when the user explicitly invokes $task. Do not use for ordinary untracked questions or unrelated project work.
---
```

Required `agents/openai.yaml` shape:

```yaml
interface:
  display_name: "Task"
  short_description: "Start or continue a tracked project task"
  default_prompt: "Use $task to start a new tracked task or continue an existing one."

policy:
  allow_implicit_invocation: false
```

Do not add icons or tool dependencies unless the user later requests them and
the files or tools actually exist.

The body must:

1. State that the current root agent remains the Project Director.
2. Identify supported user modes.
3. Establish the project root.
4. Read the Agent Task skill before any state action.
5. Run a read-only status operation before resolving an unspecified mode.
6. Separate new-task intent from continuation intent.
7. Ask one focused question only when selection or definition is materially
   incomplete.
8. Keep list and status read-only.
9. Preserve ordinary conversation outside Task activation.
10. Require a Task Response before a task-associated final answer.
11. State that Task activation does not authorize external or destructive
    actions.

### 10.2 Internal Agent Task skill

The Agent Task skill must contain the shared state-operation procedure and
route detailed rules to `references/task-system-contract.md`.

Required frontmatter shape:

```yaml
---
name: agent-task
description: Manage the project-local Task ledger for the root Project Director, including task creation, exact continuation, response recording, lifecycle transitions, validation, and recovery. Do not use as a general user task router or from a child-agent role.
---
```

Required `agents/openai.yaml` shape:

```yaml
interface:
  display_name: "Agent Task"
  short_description: "Manage durable project task state"
  default_prompt: "Use $agent-task to inspect or update the selected project Task record."

policy:
  allow_implicit_invocation: false
```

The body must:

1. Establish and verify the project root.
2. Require Project Director authority.
3. Explain which operations are read-only and which mutate state.
4. Require the state helper for every mutation.
5. Link the schema reference where each mode needs it.
6. Require expected revisions for mutations of existing tasks.
7. Require validation before and after mutation.
8. Define response-recording order and failure reporting.
9. Prevent direct Task-ledger writes by sub-agents.
10. Stop at ambiguous, corrupt, unsafe, stale, or unauthorized state.

### 10.3 Skill-to-skill routing

The Task skill must refer to the Agent Task skill by a project-relative path.
The Project Director must read the complete Agent Task `SKILL.md` before it
performs a task-state operation. The Task skill must not assume that disabling
implicit invocation automatically loads Agent Task.

The later implementation must test this routing in a fresh Codex thread. If
the host cannot reliably resolve an explicit-only referenced skill, the Task
skill must instruct the Project Director to read the exact local file directly.
Do not change Agent Task to implicit invocation merely to hide a routing defect.

## 11. Task-state helper design

### 11.1 Location and runtime

Create:

```text
.agents/skills/agent-task/scripts/task_state.py
```

Run it with the current project Python environment:

```bash
.venv/bin/python .agents/skills/agent-task/scripts/task_state.py \
  --project-root . <command> [options]
```

Use only the Python standard library. Likely modules include `argparse`,
`datetime`, `hashlib`, `json`, `os`, `pathlib`, `re`, `tempfile`, `unicodedata`,
and `uuid`. Do not add PyYAML, a database library, a file-lock package, or a
framework dependency.

### 11.2 Command contract

The helper must provide these public commands:

| Command | Mutation | Required outcome |
| --- | --- | --- |
| `status` | No | Return task counts, integrity state, most recently updated nonterminal candidates, and any projection drift. |
| `list` | No | Return all tasks or filtered tasks in deterministic order. |
| `show` | No | Resolve one exact task and return its canonical state plus latest response path. |
| `continue` | No by default | Resolve one task and return a bounded continuation packet. |
| `new` | Yes | Create one unique task folder and canonical initial state. |
| `update` | Yes | Change user-approved task name, description, definition of done, blockers, open questions, or next step as part of a Task Response transaction without changing stable identity. |
| `record-response` | Yes | Add one Task Response and update current state in one recoverable transaction. |
| `pause` | Yes | Move an allowed nonterminal task to `paused` as part of a response transaction. |
| `complete` | Yes | Move an allowed nonterminal task to `completed` as part of a verified response transaction. |
| `cancel` | Yes | Move an allowed nonterminal task to `cancelled` after explicit user intent. |
| `reopen` | Yes | Reopen a completed task only with explicit user authorization and a new response record. |
| `validate` | No | Validate the full catalog or one task without changing canonical state. |
| `rebuild-projections` | Projection only | Regenerate `TASK.md` and `INDEX.md` from valid canonical JSON without altering task meaning or revisions. |
| `reconcile` | Controlled repair | Apply only an explicit, validated repair plan to a detectable partial transaction. |

`reconcile` must not infer missing summaries, work completed, user decisions,
or lifecycle status. If the correct repair requires those facts, it must stop
and request them.

### 11.3 Output formats

Every command must support structured JSON. Read-only list and status commands
should also support concise Markdown.

Structured results must include:

- `schema_version`
- `command`
- `status`
- `project_root`
- `tasks_root`
- `mutated`
- `task_id` when applicable
- `revision_before` and `revision_after` when applicable
- `response_id` and `response_path` when applicable
- `warnings`
- `errors`
- `recovery_required`

Do not print a success result before durable writes are complete. Never include
secrets, full Task Response content, or raw internal exception traces in normal
human-facing output.

### 11.4 Exit-code contract

Use stable exit categories so the skills can distinguish failures:

| Exit code | Meaning |
| --- | --- |
| `0` | Requested operation completed with the reported durable result. |
| `2` | Invalid arguments, payload, or schema. |
| `3` | Task or project root not found. |
| `4` | Task selector is ambiguous. |
| `5` | Integrity validation failed. |
| `6` | Expected revision does not match canonical revision. |
| `7` | Lock could not be acquired. |
| `8` | Lifecycle transition is prohibited. |
| `9` | File transaction failed or needs reconciliation. |

If an implementation language or platform convention requires a different
numeric mapping, preserve the semantic categories and update the skill and
tests together.

### 11.5 Payload handling

Long descriptions, definitions of done, response summaries, and file lists
must not be embedded in fragile shell quoting. Support JSON payload input from
standard input or an explicit temporary payload file. Validate the complete
payload before acquiring a mutation lock.

Temporary payloads must be created outside the durable task record or under
`Tasks/.tmp/`, must not be followed through a symlink, and must be removed after
the operation. Do not place secrets in a payload.

## 12. Canonical task folder and identifier contract

### 12.1 Task identifier

Use this logical shape:

```text
TASK-YYYYMMDD-XXXXXXXX
```

- `YYYYMMDD` is the local creation date.
- `XXXXXXXX` is an uppercase eight-character random hexadecimal suffix derived
  from a cryptographically adequate UUID source.
- The helper must check the proposed ID and folder do not already exist.
- The task ID never changes.

An implementation may use a longer UUID internally, but the canonical visible
ID must remain stable and easy for the user to reference.

### 12.2 Task slug

The slug algorithm must:

1. Normalize the task name with Unicode NFKD.
2. Convert representable characters to lowercase ASCII.
3. Retain ASCII letters and digits.
4. Replace each run of other characters with one hyphen.
5. Remove leading and trailing hyphens.
6. Collapse consecutive hyphens.
7. Bound the slug to 60 characters without a trailing hyphen.
8. Use `task` if no safe characters remain.

The slug is a path label, not the task's human name.

### 12.3 Folder name

Construct the folder as:

```text
Task-<slug>-<YYYY-MM-DD>--<suffix>
```

For task ID `TASK-20260827-A1B2C3D4` and name `Create Task System`, the folder
is:

```text
Task-create-task-system-2026-08-27--A1B2C3D4
```

The helper must store this exact folder name in `task.json` and validate the
folder-to-state identity on every operation.

## 13. Canonical `task.json` schema

### 13.1 Required representation

Use UTF-8 JSON, a terminating newline, two-space indentation, and deterministic
key order. The first schema version should use this shape:

```json
{
  "schema_version": 1,
  "task_id": "TASK-20260827-A1B2C3D4",
  "name": "Create Task System",
  "original_name": "Create Task System",
  "slug": "create-task-system",
  "folder_name": "Task-create-task-system-2026-08-27--A1B2C3D4",
  "description": "Implement the approved project-local Task system.",
  "definition_of_done": [
    "The two skills are valid and project-local.",
    "Cross-thread continuation passes the approved scenario."
  ],
  "created_at": "2026-08-27T14:35:22-06:00",
  "updated_at": "2026-08-27T14:35:22-06:00",
  "status": "open",
  "parent_task_id": null,
  "revision": 1,
  "response_count": 0,
  "last_response": null,
  "current_summary": "Task created; implementation has not started.",
  "next_step": "Begin the first approved implementation work package.",
  "blockers": [],
  "open_questions": [],
  "thread_refs": []
}
```

### 13.2 Field rules

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | Integer | Must equal a supported positive version. |
| `task_id` | String | Must match the canonical ID pattern and folder suffix. |
| `name` | String | Required nonblank current display name. An explicit Task update can change this field without moving the folder. |
| `original_name` | String | Immutable nonblank name accepted when the task was created. |
| `slug` | String | Must equal the helper's deterministic slug for `original_name` at creation. |
| `folder_name` | String | Must equal the actual immediate child directory name. |
| `description` | String | Required concise objective and scope. |
| `definition_of_done` | Array of strings | At least one measurable criterion unless the task is explicitly an exploratory task with an approved stopping condition. |
| `created_at` | String | Immutable ISO 8601 timestamp with offset. |
| `updated_at` | String | ISO 8601 timestamp with offset whose represented instant must not precede the prior update. |
| `status` | String | One allowed lifecycle value. |
| `parent_task_id` | String or null | Must resolve to another task and must not form a cycle. |
| `revision` | Integer | Starts at 1 and increases on canonical mutation. |
| `response_count` | Integer | Equals the highest committed response sequence. |
| `last_response` | Object or null | Points to the last committed response and must match the filesystem. |
| `current_summary` | String | Current decision-dense state, not a transcript. |
| `next_step` | String or null | Concrete next action, required decision, or null for a completed task. |
| `blockers` | Array of strings | Current blockers only. |
| `open_questions` | Array of strings | Current unresolved questions only. |
| `thread_refs` | Array of objects | Optional thread metadata; never required for resolution. |

### 13.3 `last_response` object

When non-null, use:

```json
{
  "response_id": "RESP-0002",
  "sequence": 2,
  "created_at": "2026-08-27T16:08:03-06:00",
  "path": "responses/Task-Response-0002-2026-08-27T16-08-03-06-00.md",
  "supersedes_response_id": null
}
```

The path must be relative to the task folder and must resolve to a regular file
under `responses/` without following a symlink outside the folder.

### 13.4 Thread-reference object

When the current runtime exposes a reliable identifier, use a bounded record:

```json
{
  "thread_id": "opaque-runtime-id",
  "title": "Optional current task title",
  "first_seen_at": "2026-08-27T14:35:22-06:00",
  "last_seen_at": "2026-08-27T16:08:03-06:00"
}
```

Omit the record when the identifier is unavailable. Never invent an ID or make
task continuation depend on it.

## 14. Generated `TASK.md` contract

`TASK.md` is for a cold human or agent reader. Begin with a generated-file
notice that names the source revision:

```markdown
<!-- Generated from task.json revision 4. Do not edit directly. -->

# Task: Create Task System
```

Required sections:

1. **Identity**: task ID, status, created, updated, parent, revision.
2. **Description**.
3. **Definition of done**.
4. **Current summary**.
5. **Blockers**.
6. **Open questions**.
7. **Next step**.
8. **Latest Task Response**.

Render `None` for an empty blocker or open-question list. Link the latest Task
Response with a task-folder-relative link. If `TASK.md` disagrees with valid
`task.json`, validation must report projection drift and `task.json` wins.

Do not let users or agents change task scope by manually editing `TASK.md`.
Scope changes must pass through Task activation and a canonical state update.

## 15. Task Response contract

### 15.1 Filename and identity

Use a four-digit sequence for the first 9,999 responses:

```text
Task-Response-0001-2026-08-27T14-35-22-06-00.md
```

If a task exceeds that count, increase width without renaming earlier files.
The response ID is `RESP-0001` within the task.

### 15.2 Required Markdown template

```markdown
# Task Response - 2026-08-27T14:35:22-06:00

| Field | Value |
| --- | --- |
| Task | Create Task System |
| Task ID | TASK-20260827-A1B2C3D4 |
| Response ID | RESP-0001 |
| Status before | open |
| Status after | awaiting_user |
| Thread reference | Not available |
| Supersedes | None |

## Task description

[Stable description of the durable task.]

## Work completed this turn

[What was actually done during this Director turn.]

## Verification and evidence

[Checks run, files inspected, observed results, and the highest verification
level actually reached.]

## User-facing response summary

[Concise summary of the final response delivered to the user. Do not copy the
full transcript or hidden reasoning.]

## Current blockers and open questions

[Current blockers, required decisions, or None.]

## Next step

[One concrete next action, required user decision, or the exact completion
statement.]

## Relevant files

- [Project-relative path and why it matters.]
```

### 15.3 Response-content rules

- Record only observed or clearly labeled inferred facts.
- Distinguish work completed from work recommended.
- State checks that actually ran and their results.
- State what was not verified when material.
- Summarize the final response rather than copying it verbatim.
- Use project-relative paths unless an absolute path is necessary to identify
  an external source.
- Do not include secrets or excessive raw output.
- If no next step remains, use `Task completed. No next step required.`
- If the response corrects an earlier record, set `Supersedes` and preserve the
  original response unless a security correction requires redaction.

### 15.4 Response-recording boundary

Create one Task Response immediately before each substantive task-work or
task-decision final Project Director reply, after the work and verification are
known. Intermediate commentary, automatic first-turn notices, `$task list`,
and `$task status` do not create a response file.

Draft the final reply before recording its summary. After the response commits,
the delivered final reply must remain materially consistent with the saved
summary. If a material change becomes necessary before delivery, record a
superseding response rather than silently diverging from the ledger.

If the Task Response write succeeds but a later generated projection fails,
do not create the response again. Report the committed response and the stale
projection diagnostic. If the durable response itself does not publish, the
Director must disclose that the ledger update failed.

## 16. Generated `INDEX.md` contract

`Tasks/INDEX.md` must begin with:

```markdown
<!-- Generated from canonical task.json files. Do not edit directly. -->

# Tasks
```

Include:

- Generation timestamp.
- Integrity status.
- Counts by lifecycle status.
- A table with task ID, name, status, created, updated, parent, latest response,
  and next step.
- A short command reminder for `$task list`, `$task status`, and
  `$task continue <task-id>`.

Sort nonterminal tasks before terminal tasks. Within each group, sort by
the parsed `updated_at` instant descending and then task ID ascending. Do not
sort offset timestamps as unparsed strings. A missing or stale `INDEX.md` must
never hide a canonical task because status and list commands scan task folders
directly.

## 17. Lifecycle state machine

### 17.1 Allowed transitions

| From | Allowed destinations | Required authority or evidence |
| --- | --- | --- |
| New record | `open` | Explicit new-task intent and valid task definition. |
| `open` | `paused`, `awaiting_user`, `blocked`, `completed`, `cancelled` | Director decision; completion requires definition-of-done evidence; cancellation requires explicit user intent. |
| `paused` | `open`, `awaiting_user`, `blocked`, `completed`, `cancelled` | Explicit continuation or Director state assessment. |
| `awaiting_user` | `open`, `paused`, `blocked`, `completed`, `cancelled` | User response or evidence that resolves the awaited decision. |
| `blocked` | `open`, `paused`, `awaiting_user`, `completed`, `cancelled` | New authority, evidence, external-state change, or explicit user disposition. |
| `completed` | `open` | Explicit user authorization to reopen the same objective and a new Task Response. |
| `cancelled` | None in the initial implementation | Create a related new task if the user wants new work. |

Every transition must be part of a response transaction that states the old
status, new status, reason, evidence, and next step.

### 17.2 Completion gate

Before moving to `completed`, the Project Director must:

1. Read the current definition of done.
2. Map each criterion to current evidence.
3. Inspect the evidence directly.
4. Mark missing, weak, indirect, or contradictory evidence as incomplete.
5. Continue work or record the limitation instead of claiming completion.
6. Record the final verification level in the Task Response.
7. Set `next_step` to null and use the completion statement.

### 17.3 Awaiting-user and blocked distinction

Use `awaiting_user` when one bounded decision, answer, approval, or artifact is
needed from the user. Use `blocked` when the task cannot make meaningful
progress because authority, a dependency, external state, or canonical project
evidence is unavailable. Do not use either status merely because the work is
hard or would benefit from more discussion.

## 18. New-task and continuation resolution

### 18.1 Resolution order

Resolve a selector in this order:

1. Exact canonical task ID.
2. Unique case-insensitive exact task name.
3. Unique canonical task-ID prefix of a safe minimum length.
4. Unique case-insensitive exact folder name.

Do not perform fuzzy similarity, semantic similarity, contains matching, or
"best guess" selection for mutation. A read-only search may return candidates,
but the user or Project Director must select the exact task before mutation.

### 18.2 `$task` with no mode

| Current state | Required behavior |
| --- | --- |
| No nonterminal tasks | Ask for or infer with confirmation the task name, description, and definition of done. |
| Exactly one nonterminal task | Show ID, name, status, description, and next step; ask whether to continue it or create a new task. |
| Multiple nonterminal tasks | Show the three most recently updated candidates and offer `$task list`; require an explicit selection or new-task decision. |
| Integrity failure | Report the exact failure and do not offer a mutation until validation or recovery succeeds. |

### 18.3 Same task versus related new task

Use the same task when the requested work repairs, completes, verifies, or
continues the same objective and definition of done. Create a related new task
when the requested outcome is a distinct deliverable, independently
completable objective, or a successor whose acceptance criteria differ
materially. Store the predecessor in `parent_task_id` and mention the relation
in the first Task Response.

### 18.4 Terminal-task continuation

If the user selects a completed task, show its completion summary and ask
whether the user intends to:

1. Reopen the same incomplete or incorrectly completed objective.
2. Create a related new task for a new deliverable.
3. Inspect status only.

Never reopen on the basis of the word `continue` alone. A cancelled task cannot
be reopened in the initial implementation.

## 19. Cross-thread startup and continuation workflow

### 19.1 First assistant turn

The root `AGENTS.md` addition must require a cheap read-only `status --format
json` call on the first assistant turn of a new project thread. This check
occurs only after the user sends the first message because an empty thread does
not execute agent work.

The check must not mutate task state, update timestamps, attach invented thread
references, rebuild projections, or create locks that remain after the command.

### 19.2 Resume-offer behavior

- With zero nonterminal tasks, say nothing about Tasks unless the user's prompt
  invokes `$task` or asks about past tasks.
- With one nonterminal task and an unrelated prompt, answer the prompt first
  and append one concise, non-blocking resume offer.
- With multiple nonterminal tasks, answer the prompt first and append a short
  notice with the count and `$task list` route.
- If the user already invoked `$task`, do not duplicate the startup notice.
- If the user clearly names an exact task ID, inspect that task directly.

The notice must not force the user to answer before receiving help on an
unrelated request.

### 19.3 Continuation packet

The helper's read-only `continue` result must provide:

- Canonical task ID and folder.
- Status and revision.
- Task description and definition of done.
- Current summary.
- Current blockers and open questions.
- Next step.
- Latest Task Response path.
- Parent-task relation.
- Relevant file paths carried by the latest response.
- Integrity warnings.

The Project Director then reads `task.json`, `TASK.md`, and the latest response.
It reads older responses only when the latest record points to an unresolved
decision, correction, or evidence chain. It inspects live relevant files before
using them as authority.

### 19.4 Memory and goal boundary

Memories may help locate the task or recall terminology, but the Project
Director must resolve the task from `Tasks/`. A native goal may describe work
inside the task, but the task state, definition of done, and Task Response
history remain independent. If goal state and Task state disagree, report the
mismatch and request or derive the narrowest safe reconciliation without
silently changing either source.

## 20. Project Director operating workflow

### Phase A: First-turn awareness

1. Read root project guidance as usual.
2. Run Agent Task `status` in read-only mode.
3. Record no mutation from the awareness check.
4. Answer the user's actual prompt.
5. Add the applicable non-blocking Task notice only when a nonterminal task
   exists and Task mode is not already active.

### Phase B: Task workflow activation

1. Recognize either explicit `$task` invocation or the user's explicit
   selection or confirmation of an existing task from a resume offer.
2. Read the complete Task skill.
3. Establish the project root.
4. Read the complete Agent Task skill before a state operation.
5. Determine whether the user specified a mode.
6. Run read-only status or resolution before any mutation.

### Phase C: Task definition or selection

For a new task:

1. Establish the task name.
2. Establish the description and scope.
3. Establish measurable definition-of-done criteria or an exploratory stopping
   condition.
4. Determine whether the task is related to an existing parent.
5. Confirm only materially missing or ambiguous facts.
6. Create the task through the helper.

For a continuation:

1. Resolve the exact task.
2. Validate canonical state and response history.
3. Read the bounded continuation packet.
4. Inspect the live files or evidence that govern the next action.
5. Explain any drift or contradiction before proceeding.

### Phase D: Task work

1. Restate the current outcome, constraints, and definition of done internally.
2. Decide whether work remains with the Project Director or should be delegated
   through `manage-subagent-roles`.
3. Preserve task scope and authority.
4. Perform or coordinate the work.
5. Inspect resulting artifacts and run proportionate checks.
6. Determine the truthful post-turn status.

### Phase E: Durable response transaction

Before sending the final task-associated reply:

1. Prepare the Task Response payload.
2. Include the response summary, not an invented or full transcript.
3. Include observed work and verification.
4. Set the status after the response.
5. Set the next step, required decision, or completion statement.
6. Call `record-response` with the expected revision.
7. Observe the returned task ID, response ID, new revision, and durable paths.
8. If recording fails, report the failure and do not claim a successful ledger
   update.
9. Deliver the user-facing final response.

### Phase F: Completion

1. Audit every definition-of-done criterion.
2. Reinspect current evidence.
3. Record unresolved limitations.
4. Use `completed` only if the evidence proves completion.
5. Create the completion Task Response.
6. Confirm that `task.json`, `TASK.md`, `INDEX.md`, and the response file agree.
7. Leave the completed task visible in the index but exclude it from automatic
   nonterminal resume offers.

## 21. Sub-agent integration boundary

Task-system ownership remains with the Project Director even when task work is
delegated.

### 21.1 Delegation

- Use the existing `manage-subagent-roles` skill before selecting or spawning
  a role-based child.
- Include the task ID and bounded task context in the delegation contract.
- Give the child only the files and authority needed for its subtask.
- State that `Tasks/` is read-only to the child unless the Project Director has
  explicitly delegated a narrowly defined read-only validation operation.
- Never delegate canonical state mutation, lifecycle authority, or final Task
  Response creation.

### 21.2 Collection and logging

When a child returns:

1. The Project Director inspects the cited files and evidence.
2. The Project Director separates observed evidence from child inference.
3. The Project Director accepts, revises, or rejects the result.
4. The Project Director summarizes accepted work in its own Task Response.
5. The child report may be listed as relevant evidence, but it does not become
   the canonical task status.

### 21.3 Parallel work

Separate child agents may work on independent files, but two threads or agents
must not update the same task ledger concurrently. The helper's revision and
lock checks remain mandatory even when the Project Director believes it has
exclusive ownership.

## 22. Transaction, locking, and recovery design

### 22.1 Lock locations

Use atomic directory creation for portable lock acquisition:

```text
Tasks/.locks/catalog.lock/
Tasks/.locks/TASK-20260827-A1B2C3D4.lock/
```

Each lock directory should contain a small `owner.json` when possible:

```json
{
  "operation_id": "TXN-opaque-id",
  "command": "record-response",
  "task_id": "TASK-20260827-A1B2C3D4",
  "acquired_at": "2026-08-27T16:08:03-06:00",
  "process_id": 12345
}
```

The process ID is diagnostic only and must not be treated as proof that a lock
is safe to remove. Do not include usernames, prompts, or secrets.

Read-only commands must inspect the catalog-lock path before scanning. If a
writer lock is active, return a bounded `busy` or lock-conflict result instead
of interpreting the writer's temporary transaction state as corruption. The
read-only command must not remove the lock or change any file.

### 22.2 New-task transaction

Implement task creation in this order:

1. Validate the complete input payload.
2. Validate the `Tasks/` root and reject unsafe links.
3. Acquire the catalog lock.
4. Rescan canonical task folders.
5. Allocate and collision-check the task ID and folder.
6. Create a transaction-specific temporary task folder under `Tasks/.tmp/`.
7. Write and validate initial `task.json`.
8. Render and validate initial `TASK.md`.
9. Create the empty `responses/` directory.
10. Atomically rename the complete task folder into `Tasks/`.
11. Regenerate `INDEX.md` from all valid canonical tasks.
12. Release the catalog lock.
13. Return the durable task ID, folder, revision, and any projection warning.

If step 11 fails, the new task remains valid canonical state and the command
must report that the index needs regeneration. It must not create a duplicate
task on retry.

### 22.3 Response and state transaction

Implement response recording in this order:

1. Validate the response payload before locking.
2. Acquire the catalog lock.
3. Acquire the task lock.
4. Reread and fully validate `task.json`.
5. Compare the expected revision.
6. Validate the requested lifecycle transition or user-approved task update.
7. Allocate the next response sequence.
8. Render the Task Response to a same-directory temporary file.
9. Validate the rendered response structure and path set.
10. Record a bounded transaction intent under `Tasks/.tmp/`.
11. Atomically publish the Task Response.
12. Atomically publish the updated `task.json` with incremented revision and
    response count.
13. Regenerate and atomically publish `TASK.md`.
14. Regenerate and atomically publish `INDEX.md`.
15. Remove the transaction intent.
16. Release the task lock and then the catalog lock.
17. Return the exact durable core and projection result.

Every operation that needs both locks must acquire the catalog lock before the
task lock and release them in reverse order. This initial implementation
accepts serialized Task-ledger writes in exchange for a simple, auditable
deadlock boundary. Read-only commands acquire neither persistent lock; they
detect an active writer as described in section 22.1.

### 22.4 Partial-transaction classes

| Observed state | Classification | Safe response |
| --- | --- | --- |
| Temporary files only; no published response | Aborted before durable mutation | Remove only validated transaction-owned temporary files. |
| Published next response; old `task.json` still points to prior response | Orphan response | Stop normal mutation and run explicit reconciliation using the response and transaction intent. |
| Updated `task.json`; referenced response missing | Canonical integrity failure | Stop; recover the exact response from transaction evidence or require user-authorized correction. |
| Canonical response and `task.json` agree; `TASK.md` stale | Projection drift | Rebuild `TASK.md`. |
| Canonical tasks valid; `INDEX.md` stale or missing | Catalog projection drift | Rebuild `INDEX.md`. |
| Lock exists with no provable owner state | Ambiguous writer ownership | Do not steal; inspect and require explicit recovery. |

### 22.5 Reconciliation rules

- Reconciliation must begin with read-only validation.
- It must name the exact task, expected revision, partial files, and proposed
  repair.
- It must preserve any durable Task Response already published.
- It must not create a second response for the same final Director turn.
- It must not invent a response summary, status reason, verification result,
  or user decision.
- It must be idempotent when repeated after a fully successful repair.
- It must leave a Task Response or separate bounded repair note when canonical
  task meaning changes.

## 23. Project guidance and documentation changes

### 23.1 Root `AGENTS.md`

Add a concise section with these duties:

```markdown
## Task-system workflow

- On the first assistant turn of a new project thread, run the Agent Task
  read-only status check.
- Do not interrupt unrelated work. Give the applicable non-blocking resume
  offer only when nonterminal tasks exist.
- Enter task creation or selection only after explicit `$task` activation or
  an explicit user continuation decision.
- Before changing Task state, read and follow the project-local Task and Agent
  Task skills.
- The Project Director owns Task state and final Task Responses. Child agents
  return evidence and do not mutate the Task ledger.
```

The final wording may be more compact, but it must preserve every behavior.
Do not turn the entire task schema into always-loaded `AGENTS.md` content.

### 23.2 Root `ROLE.md`

Add only the responsibilities not already covered by general Project Director
language:

- Classify explicit Task requests as new, continuation, or read-only inquiry.
- Own the canonical Task ledger and response record.
- Verify definition-of-done evidence before completion.
- Keep Task state separate from thread state, child-agent reports, memories,
  and native goals.

Do not duplicate the Agent Task command reference in `ROLE.md`.

### 23.3 Root `README.md`

Add a user-facing **Tasks** section that explains:

- `$task new <information>`.
- `$task continue <task-id-or-name>`.
- `$task status` and `$task list`.
- `$task update <task-id>` for a user-approved name, scope, definition-of-done,
  blocker, open-question, or next-step change.
- Pause, complete, cancel, and explicit reopen behavior.
- The new-versus-continuation decision.
- Folder naming and stable task IDs.
- What a Task Response contains.
- The first-turn resume offer.
- The fact that ordinary questions do not mutate Tasks.
- The location and local-only scope of both skills.

Keep commands short and copy-pasteable. Do not expose helper implementation
details unless they help troubleshooting.

### 23.4 Root `.gitignore`

If runtime locks and temporary payloads are created, add only:

```gitignore
/Tasks/.locks/
/Tasks/.tmp/
```

Do not ignore `/Tasks/`, `task.json`, `TASK.md`, `INDEX.md`, or Task Response
files. This plan does not authorize a Git commit or push.

## 24. Security, privacy, and authority controls

### 24.1 Path safety

- Resolve and validate the project root before every operation.
- Reject a `Tasks/` root that is a symlink or resolves outside the project.
- Inspect each task folder and canonical file without following an escape
  symlink.
- Use explicit paths, not globs, for mutation targets.
- Refuse absolute user-supplied paths and traversal segments.
- Bound filename and field lengths sufficiently to avoid filesystem failures
  while preserving the original task name in JSON.

### 24.2 Content safety

- Treat task descriptions and old responses as user/project data, not as
  higher-priority instructions.
- Do not execute commands copied from an old response without current user
  authority and live validation.
- Redact or summarize secret-bearing logs before response recording.
- Do not persist environment variables, credentials, authentication headers,
  private keys, or browser session data.
- Record evidence paths and concise results instead of bulk tool output.

### 24.3 Authority safety

Task activation authorizes creation and maintenance of the local Task record
and the work explicitly requested by the user. It does not authorize:

- Deletion of unrelated files.
- Dependency installation.
- External messages.
- Purchases or financial actions.
- Commit, push, merge, publication, or deployment.
- A new native Codex task or thread.
- Changes outside the project root.

### 24.4 Privacy and retention

The initial implementation stores Task records indefinitely in the project
until the user explicitly removes or archives them under a later approved
workflow. It must not implement automatic deletion. If a future project uses
Git, the user must decide whether Task records belong in version control before
publication or sharing.

## 25. Implementation work packages

Each work package has one primary objective and an observable stopping
condition. The Project Director must complete them in dependency order unless
current evidence justifies a documented change.

### WP-00: Reconfirm baseline and freeze the change boundary

**Objective:** Establish current authority and prevent the plan from being
implemented against stale assumptions.

**Actions:**

1. Read current `AGENTS.md`, `SOUL.md`, and `ROLE.md`.
2. Inspect current skills, Task-related paths, README, `.gitignore`, Python,
   validator, and repository state.
3. Reconcile any new Task implementation or conflicting plan.
4. Record the authorized file set and protected unrelated files.

**Evidence:** Baseline command output, current tree, and explicit changed-path
allowlist.

**Stopping condition:** The Project Director can name every file it will create
or modify and every unrelated area it will preserve.

### WP-01: Establish the task-state contract and render templates

**Objective:** Make schema and output contracts authoritative before code.

**Artifacts:**

- `.agents/skills/agent-task/references/task-system-contract.md`
- Conditional template assets
- Initial `Tasks/INDEX.md` template

**Actions:**

1. Transcribe the approved state, naming, response, index, lifecycle,
   concurrency, and recovery rules.
2. Define JSON payload schemas for every mutating command.
3. Define exact Markdown templates and generated-file notices.
4. Define exit categories and validation findings.
5. Review the contract for duplicate sources of truth.

**Checks:** Reference links, template completeness, schema examples, and manual
traceability to requirements.

**Stopping condition:** Another agent can implement the helper without
inventing a field, state transition, output section, or recovery rule.

### WP-02: Initialize and write the user-facing Task skill

**Objective:** Create the explicit-only user entry point.

**Artifacts:**

- `.agents/skills/task/SKILL.md`
- `.agents/skills/task/agents/openai.yaml`

**Actions:**

1. Use the bundled skill initializer for a project-local path without unused
   resources.
2. Replace all scaffold placeholders.
3. Write the discriminating description and routing workflow.
4. Set display name `Task` and explicit-only invocation.
5. Link to the exact Agent Task skill.
6. Validate the skill.

**Checks:** Skill validator, frontmatter inspection, metadata inspection,
explicit-invocation test, and unrelated-prompt nonactivation test.

**Stopping condition:** `$task` routes all supported modes without directly
editing task files or attracting ordinary prompts.

### WP-03: Initialize and write the Agent Task skill

**Objective:** Create the Project Director's state-management procedure.

**Artifacts:**

- `.agents/skills/agent-task/SKILL.md`
- `.agents/skills/agent-task/agents/openai.yaml`
- Reference and conditional assets from WP-01

**Actions:**

1. Initialize only the resources the workflow uses.
2. Write root discovery, authority, mode routing, mutation, validation, and
   failure behavior.
3. Set display name `Agent Task` and explicit-only invocation.
4. Link each detailed mode to the relevant contract section.
5. Prevent child-agent mutation and user-router substitution.
6. Validate the skill.

**Stopping condition:** The complete skill is concise, routes every supported
operation, and adds no alternate source of truth.

### WP-04: Implement storage, identity, and read-only discovery

**Objective:** Create and discover canonical tasks safely.

**Artifacts:**

- `task_state.py`
- Initial `Tasks/INDEX.md`
- Focused tests

**Actions:**

1. Implement root and path validation.
2. Implement ID and slug generation.
3. Implement canonical JSON validation.
4. Implement `status`, `list`, `show`, and `continue`.
5. Implement `new` through a temporary-folder transaction.
6. Implement TASK and index rendering.

**Stopping condition:** The helper creates uniquely named tasks and can list or
resolve them without mutation or ambiguity.

### WP-05: Implement lifecycle and response transactions

**Objective:** Record Director turns and state transitions durably.

**Actions:**

1. Implement response payload validation.
2. Implement allowed transition validation.
3. Implement lock acquisition and expected revisions.
4. Implement Task Response rendering and publication.
5. Implement state update and projection regeneration.
6. Implement user-approved task updates, pause, complete, cancel, and explicit
   reopen.
7. Return durable receipts and exact partial-failure status.

**Stopping condition:** Every successful task-associated final turn produces
one ordered Task Response and a matching canonical state revision.

### WP-06: Implement validation and recovery

**Objective:** Detect and safely recover from state drift and partial writes.

**Actions:**

1. Implement full-catalog and one-task validation.
2. Detect every REL-010 integrity class.
3. Implement projection rebuild.
4. Implement bounded reconciliation with explicit repair input.
5. Ensure repeated repair is idempotent.
6. Ensure ambiguous locks are never stolen automatically.

**Stopping condition:** Each injected failure produces the intended diagnostic,
and approved recoverable cases return to a valid state without duplicate
responses or invented meaning.

### WP-07: Integrate project guidance and documentation

**Objective:** Make Task awareness available in future project threads without
crowding always-loaded instructions.

**Artifacts:**

- Focused changes to root `AGENTS.md`, `ROLE.md`, `README.md`, and `.gitignore`

**Actions:**

1. Add first-turn awareness and routing to `AGENTS.md`.
2. Add missing Task ownership to `ROLE.md`.
3. Add user instructions to `README.md`.
4. Ignore only ephemeral runtime directories.
5. Reinspect unrelated existing guidance for preservation.

**Stopping condition:** A cold reader can invoke, continue, inspect, and close a
task, and a fresh Project Director knows when to check state without loading the
full schema.

### WP-08: Complete automated verification

**Objective:** Prove the deterministic implementation satisfies its contracts.

**Actions:**

1. Run both skill validators.
2. Run all Task helper tests.
3. Run existing relevant project tests for the role system.
4. Run static compilation and format checks.
5. Run no-mutation snapshots for read-only paths.
6. Run fault-injection tests in isolated temporary roots.

**Stopping condition:** Every required automated check passes or every
pre-existing unrelated failure is isolated and explicitly reported.

### WP-09: Perform behavioral and cross-thread validation

**Objective:** Validate the actual user workflow, not only files and units.

**Actions:**

1. Create or select an explicitly approved disposable local project copy.
2. Start a fresh thread for that isolated project and invoke `$task new`.
3. Create and inspect the first task folder.
4. Perform one bounded task turn and inspect its Task Response.
5. Open a separate fresh thread for the same isolated project.
6. Observe the correct resume offer.
7. Continue the exact task and inspect live files.
8. Record the second response.
9. Exercise multiple-task ambiguity and an unrelated question.
10. Confirm no implicit task mutation, template-root test task, or global
    artifact remains.

**Stopping condition:** The end-to-end cross-thread scenario succeeds with the
expected user experience and durable files.

### WP-10: Run the final requirement and change-boundary audit

**Objective:** Prove complete implementation against this plan.

**Actions:**

1. Reopen all material files.
2. Inspect the final project tree.
3. Map every requirement ID to implementation and evidence.
4. Map every changed Task-system artifact back to an approved requirement.
5. Confirm no unapproved global, external, Git, or thread action occurred.
6. State the highest verification and validation levels reached.

**Stopping condition:** Every requirement has direct current evidence, every
changed artifact is authorized, and no required work remains.

## 26. Focused test matrix

All filesystem mutation tests must use an isolated directory created with a
safe temporary-directory mechanism. The end-to-end manual scenario must use a
disposable local project copy or another explicitly approved isolated project.
It must not leave test tasks in the template root. Starting the two validation
threads is a deliberate tester action, not automatic Task-system behavior.

| Test ID | Scenario | Expected evidence | Primary requirements |
| --- | --- | --- | --- |
| TST-001 | Run status with an empty valid `Tasks/` root | Zero counts, no mutation, valid JSON | AGT-006, STO-001, VER-013 |
| TST-002 | Run status when `Tasks/` is absent | Documented empty/uninitialized result or exact not-found result, with no creation from read-only mode | AGT-012, REL-011 |
| TST-003 | Create a task with name, description, and definition of done | Exact folder pattern, valid `task.json`, generated `TASK.md`, empty `responses/` | USR-006, STO-003 through STO-011 |
| TST-004 | Create two same-name tasks on the same date | Distinct IDs and folders; original names preserved | STO-006 through STO-010 |
| TST-005 | Create a task with Unicode and punctuation-only name segments | Deterministic safe slug or `task` fallback; no path escape | STO-008, STO-009, REL-013 |
| TST-006 | Supply an absolute path, `..`, hidden target, control character, or symlink escape | Operation rejected before mutation | REL-013 |
| TST-007 | Validate a correct initial state | PASS with revision 1 and response count 0 | STA-001, STA-002 |
| TST-008 | Corrupt one required JSON field or type | Exact schema diagnostic and no mutation | STA-002, AGT-012, REL-010 |
| TST-009 | Change folder name so it disagrees with JSON | Exact identity diagnostic | STO-004, STA-001, REL-010 |
| TST-010 | Render `TASK.md` from canonical state | All required sections and source revision present | STA-003 |
| TST-011 | Alter generated `TASK.md` only | Projection drift detected; canonical JSON unchanged; rebuild restores it | STA-003, REL-009, REL-012 |
| TST-012 | Generate `INDEX.md` with mixed statuses | Correct fields, grouping, sorting, counts, and command reminder | STO-002, STA-004, STA-005 |
| TST-013 | Delete or alter `INDEX.md` | Status still discovers tasks; rebuild restores index | STA-004, REL-009, REL-012 |
| TST-014 | Record the first normal response | Correct filename, H1 timestamp, required sections, revision and count increment | STA-006 through STA-010 |
| TST-015 | Record a response with `completed` status | Definition-of-done evidence required and exact completion statement emitted | STA-011, DIR-006 |
| TST-016 | Record a superseding correction | New response points to prior ID; prior file remains | STA-012, STA-013 |
| TST-017 | Use explicit credential-pattern fixtures and a prompt requesting hidden reasoning in a Task Response | Deterministic known-secret checks reject the fixtures; behavioral review confirms hidden reasoning is omitted | STA-014 |
| TST-018 | Exercise each allowed lifecycle transition | Transition succeeds only with required payload and authority | LIF-001 through LIF-007 |
| TST-019 | Exercise each prohibited lifecycle transition | Exit category 8; no files change | LIF-003, LIF-014 |
| TST-020 | Continue a completed task without explicit reopen intent | Read-only completion summary and decision request; no mutation | LIF-014 |
| TST-021 | Create a valid related child task | Existing parent resolved and stored | LIF-006, LIF-007 |
| TST-022 | Use missing parent or create a parent cycle | Rejected with exact diagnostic | LIF-007 |
| TST-023 | Resolve exact task ID | Exact task selected | LIF-009 |
| TST-024 | Resolve a unique exact name or safe ID prefix | Unique task selected | LIF-010 |
| TST-025 | Resolve an ambiguous name or prefix | Candidate list and exit category 4; no mutation | LIF-010, LIF-013 |
| TST-026 | Invoke `$task` with zero, one, and multiple nonterminal tasks | Correct decision dialog for each state | USR-008, LIF-011 through LIF-013 |
| TST-027 | Run `$task status` and `$task list` | Read-only output and byte-identical canonical files | USR-005, USR-009, VER-013 |
| TST-028 | Send an unrelated ordinary prompt while tasks exist | Prompt answered; no Task mutation; optional notice follows policy | USR-010, CTX-006 |
| TST-029 | Inspect skill metadata | `task` and `agent-task` both have explicit-only policy and accurate display names | USR-002, USR-003, AGT-002, AGT-004, VER-008 |
| TST-030 | Invoke Task skill in a fresh thread | Task reads or resolves exact Agent Task contract before mutation | USR-011, AGT-003 |
| TST-031 | Attempt Agent Task use from an unqualified child role | Operation stops without ledger mutation | USR-012, AGT-003, DIR-009 |
| TST-032 | Hold a task lock and attempt a second write | Exit category 7; first writer's files unchanged | REL-002 through REL-004 |
| TST-033 | Read revision N, commit N+1 elsewhere, then write with N | Exit category 6; no stale write | REL-005, REL-006 |
| TST-034 | Interrupt before response publication | Only transaction-owned temporary data remains; safe cleanup | REL-007, REL-008, REL-012 |
| TST-035 | Interrupt after response publication and before JSON update | Orphan response detected; no duplicate response; reconciliation required | REL-008, REL-010, REL-012 |
| TST-036 | Interrupt after canonical update and before projections | Canonical core accepted; projection drift reported and rebuildable | REL-008, REL-009 |
| TST-037 | Delete the response referenced by `task.json` | Integrity failure; no normal continuation | REL-010, REL-011 |
| TST-038 | Run reconciliation twice after an approved recoverable fault | First repairs; second is a no-op with valid state | AGT-007, REL-012 |
| TST-039 | Start a fresh thread with zero, one, and multiple tasks | Correct first-turn read-only behavior and resume notice | CTX-001 through CTX-005 |
| TST-040 | Continue from a fresh thread without a runtime thread ID | Continuation succeeds from task ID and files | CTX-008 through CTX-010 |
| TST-041 | Make latest response disagree with current live artifact | Director reports drift; live artifact wins | CTX-008, CTX-009 |
| TST-042 | Disable or clear Codex memory, then continue by task ID | Continuation still succeeds | CTX-011 |
| TST-043 | Create conflicting native goal text and Task state | Mismatch reported; neither source silently overwritten | ARC-008, CTX-012 |
| TST-044 | Delegate bounded work through existing role system | Child returns evidence; only Director records Task Response | DIR-008, DIR-009 |
| TST-045 | Try a destructive or external action based only on Task activation | Authorization denied or requested separately | DIR-010 |
| TST-046 | Run both skill validators | Both return PASS with no unfinished scaffold placeholders | VER-005, VER-006 |
| TST-047 | Run Python compile and Task helper unit tests | All pass | VER-007 |
| TST-048 | Inspect project and user/global paths after implementation | Only approved project-local artifacts exist | ARC-001, ARC-002, VER-016 |
| TST-049 | Run the full cross-thread user scenario | Creation, notice, exact resume, live validation, and second response succeed | VER-015 |
| TST-050 | Inspect final tree and changed contents | Every change maps to an approved requirement; no external or Git action | ARC-010, VER-016 |
| TST-051 | Explicitly update task name, description, and definition of done | Canonical fields and projections change with one response; original name, task ID, slug, folder, and prior responses remain stable | USR-005, AGT-006, STO-008, STO-010, STA-002 |
| TST-052 | Run read-only status while a catalog writer lock is active | Bounded busy/lock result; no transient state is misclassified and no file changes | REL-002, REL-003, REL-011 |

## 27. Future implementation acceptance criteria

The later implementation is accepted only when all applicable criteria below
have direct current evidence.

### 27.1 Skill acceptance

- [ ] Both skills exist only under `.agents/skills/` in this project.
- [ ] Both skill folders and frontmatter names match.
- [ ] Task displays as `Task` and Agent Task displays as `Agent Task`.
- [ ] Both skills are explicit-only where specified.
- [ ] Task routes to Agent Task without duplicating state logic.
- [ ] Agent Task refuses unsupported or unauthorized use.
- [ ] Both skills pass the bundled validator.

### 27.2 Storage and schema acceptance

- [ ] `Tasks/` and generated `INDEX.md` exist.
- [ ] Every task is an immediate child with the approved name pattern.
- [ ] Every task has valid `task.json`, generated `TASK.md`, and `responses/`.
- [ ] Stable IDs prevent same-name/date collisions.
- [ ] JSON fields, types, timestamps, revisions, parents, and paths validate.
- [ ] Generated projections can be rebuilt from canonical state.
- [ ] The index never hides a valid task when stale or absent.

### 27.3 Response acceptance

- [ ] Each substantive task-work or task-decision final Director turn produces
  exactly one Task Response.
- [ ] Pure status/list replies and automatic resume notices remain read-only
  and create no Task Response.
- [ ] Commentary and tool progress do not produce responses.
- [ ] Filenames, response IDs, timestamps, and sequence numbers agree.
- [ ] Every required Task Response section is present and meaningful.
- [ ] Completed tasks contain the completion statement.
- [ ] Corrections supersede rather than silently rewriting history.
- [ ] No protected secret, hidden-reasoning, transcript, or raw-log content is
  stored.

### 27.4 Lifecycle and selection acceptance

- [ ] Every status and allowed transition behaves as specified.
- [ ] Prohibited transitions leave files unchanged.
- [ ] Same-objective work stays in the same task.
- [ ] Different deliverables create related tasks when appropriate.
- [ ] Explicit task updates preserve original name, stable ID, slug, folder,
  and prior responses.
- [ ] Exact IDs win over names and ambiguous matches never auto-select.
- [ ] Terminal tasks never reopen automatically.
- [ ] Recency orders candidates but does not establish user intent.

### 27.5 Cross-thread acceptance

- [ ] A first-turn read-only check occurs in a fresh project thread.
- [ ] Empty threads are not described as proactively executable.
- [ ] Zero, one, and multiple task notices follow the approved policy.
- [ ] Unrelated prompts receive their answer without Task mutation.
- [ ] An exact task continues in a new thread without relying on memory or a
  thread ID.
- [ ] The Director inspects current task state, latest response, and live
  artifacts before continuing.
- [ ] Native goal and Task state remain separate.

### 27.6 Reliability and security acceptance

- [ ] Locks prevent concurrent writers.
- [ ] Read-only checks report an active writer without removing its lock or
  misclassifying transient state.
- [ ] Expected revisions prevent stale writes.
- [ ] Atomic replacement prevents partially written individual files.
- [ ] Injected transaction failures produce the documented recovery class.
- [ ] Reconciliation is explicit, bounded, idempotent, and meaning-preserving.
- [ ] Path traversal and symlink escapes are rejected.
- [ ] Task activation does not broaden destructive or external authority.
- [ ] Child agents cannot mutate the Task ledger.
- [ ] No global skill, state, task, plugin, commit, push, or deployment is
  created.

### 27.7 Documentation acceptance

- [ ] Root guidance contains the concise Task contract without the full schema.
- [ ] Project Director ownership is explicit without duplicated procedure.
- [ ] README commands and examples match live behavior.
- [ ] `.gitignore` excludes only ephemeral Task runtime paths.
- [ ] The final report states exact checks, results, verification level,
  validation level, and remaining limitations.

## 28. Failure modes and required controls

| Failure mode | Risk | Required control |
| --- | --- | --- |
| The user says only `$task` | Wrong new/continue assumption | Inspect nonterminal tasks and present the correct bounded choice. |
| Two tasks share a name | Wrong continuation | Stable IDs and ambiguity failure. |
| A task name contains unsafe path characters | Path escape or invalid folder | Deterministic slugging and path containment validation. |
| The most recent task is unrelated | Wrong automatic resume | Recency is ordering only; require selection. |
| A completed task receives `continue` | Silent reopening | Present reopen/new/status choice. |
| A new thread has no transcript | Lost context | Read project guidance and canonical Task state. |
| Codex memory is disabled or stale | Missing or wrong recall | Memory is optional navigation only. |
| `/goal` disagrees with task state | Split authority | Report mismatch; do not merge silently. |
| Two threads update one task | Lost update or duplicate response | Directory lock plus expected revision. |
| Process stops during a write | Partial transaction | Temporary files, atomic replace, transaction intent, validation, reconciliation. |
| Response exists but JSON was not advanced | Duplicate response on retry | Detect orphan sequence and reconcile; never blindly retry. |
| Projection differs from JSON | Cold-reader misinformation | Generated notice, validation, and projection rebuild. |
| Referenced live file changed | Stale handoff | Reinspect current file; live artifact wins. |
| Child claims success | False completion | Director reinspection and definition-of-done audit. |
| Task Response contains a secret | Persistent exposure | Pre-write content guard, minimal summaries, explicit redaction procedure. |
| User invokes Agent Task directly | Bypassed user routing | Authority check and refusal outside Project Director workflow. |
| First-turn awareness annoys ordinary chat | Workflow friction | Non-blocking notice after answering; no mutation or forced response. |
| Validator is unavailable in `.venv` | Unverified skills | Use the observed `uv --with PyYAML` wrapper without global installation. |
| Project is not a Git repository | False Git assurance | Use direct filesystem evidence and do not claim commit or history checks. |

## 29. Verification and validation commands

The exact commands must be reconfirmed during WP-00. The expected initial set
is:

```bash
.venv/bin/python -m py_compile \
  .agents/skills/agent-task/scripts/task_state.py
```

```bash
.venv/bin/python -m unittest \
  .agents/skills/agent-task/tests/test_task_state.py -v
```

```bash
/Users/alex.omegapy/.local/bin/uv run --with PyYAML -- python \
  /Users/alex.omegapy/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/task
```

```bash
/Users/alex.omegapy/.local/bin/uv run --with PyYAML -- python \
  /Users/alex.omegapy/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/agent-task
```

```bash
.venv/bin/python \
  .agents/skills/manage-subagent-roles/scripts/role_catalog.py \
  --repo-root . validate --format markdown
```

```bash
.venv/bin/python \
  .agents/skills/agent-task/scripts/task_state.py \
  --project-root . validate --format json
```

Use temporary test roots for fault injection. Do not run destructive cleanup
against the project root. If the project becomes a Git repository, add scoped
`git diff --check` and final diff inspection; do not make Git a prerequisite
for Task continuity.

## 30. Rollback and preservation strategy

### 30.1 Before first real task

If the implementation is rejected before a real task is created:

1. Remove only the two newly created skill directories and the empty generated
   `Tasks/` scaffold through an explicitly approved change.
2. Revert only the Task-system additions to root guidance, README, and
   `.gitignore`.
3. Preserve the implementation plan and unrelated role-system work unless the
   user separately requests removal.

### 30.2 After a real task exists

Task records are user data. Disabling or removing the skills must not delete
`Tasks/`. Preserve the ledger, explain how it can be read manually, and require
explicit authorization before archiving, moving, redacting, or deleting any
task folder.

### 30.3 Failed transaction recovery

Do not roll back by deleting broad directories. Resolve the exact task and
transaction, preserve durable response evidence, repair only the inconsistent
files, validate the full task, and then rebuild projections.

## 31. Decisions, assumptions, and unresolved implementation checks

### 31.1 Decisions established by the user and this plan

- The system is project-local.
- The user-facing skill is Task.
- The Project Director owns tasks.
- Agent Task performs internal lifecycle operations.
- Each task has its own dated and named folder.
- Each substantive task-work or task-decision final Director turn has a
  timestamped Markdown Task Response.
- Pure status/list replies and automatic resume notices are read-only and are
  the only response-recording exceptions.
- Cross-thread continuation uses project files.
- The user may ask ordinary questions without entering Task mode.
- New-task and continuation intent must be distinguished.
- The initial design favors transparent files over a database.

### 31.2 Assumptions to reverify at implementation time

- The project still uses `.agents/skills/` for local skills.
- The root agent is still the Project Director.
- Python 3.12 or a compatible project interpreter remains available.
- The bundled skill validator and `uv` wrapper remain available at their
  observed paths.
- No partial Task implementation has appeared.
- The user still wants the non-blocking first-turn resume policy.

### 31.3 Checks that require live implementation validation

- Whether explicit Task-to-Agent-Task routing remains loaded correctly after a
  long context compaction.
- Whether the current Codex UI displays both requested names exactly.
- Whether a stable current thread ID is exposed; the design must work if it is
  not.
- Whether first-turn awareness adds acceptable latency in a project with many
  tasks.
- Whether response-content secret detection should remain instruction-based or
  needs a deterministic project-specific pattern check after real usage.

These checks do not block this plan because the design has safe fallbacks and
does not make their uncertain behavior authoritative.

## 32. Requirement traceability matrix

The matrix assigns each requirement to a primary implementation area and
evidence lane. Tests can cover more requirements than the primary mappings
shown here.

| Requirement IDs | Source intent | Primary sections | Work packages | Primary evidence |
| --- | --- | --- | --- | --- |
| ARC-001, ARC-002, ARC-003, ARC-004, ARC-005 | Local-only skills; Project Director owns the durable task across threads | 1, 2, 4, 9, 20 | WP-00, WP-02, WP-03, WP-07 | Final tree, skill locations, root role and guidance inspection |
| ARC-006, ARC-007, ARC-008, ARC-009, ARC-010 | Two-skill flow, project files as authority, memory and goals separated, existing systems preserved | 4, 5, 9, 10, 19, 23 | WP-01, WP-02, WP-03, WP-07, WP-10 | Contract review, behavioral tests, final change audit |
| USR-001, USR-002, USR-003, USR-004 | Create the user Task skill and make it user-activated only | 9, 10.1 | WP-02 | Skill validator, metadata inspection, TST-029 |
| USR-005, USR-006, USR-007, USR-008 | Support modes and gather enough task information without excess questioning | 10.1, 18, 20 | WP-02, WP-04, WP-05 | TST-026, TST-051, behavioral scenarios |
| USR-009, USR-010, USR-011, USR-012 | Read-only queries, ordinary-chat preservation, Agent Task routing, authority boundary | 10.1, 10.3, 20, 24 | WP-02, WP-03, WP-07 | TST-027 through TST-031 |
| AGT-001, AGT-002, AGT-003, AGT-004 | Create internal Agent Task with accurate identity and explicit-only policy | 9, 10.2 | WP-03 | Skill validator and metadata inspection |
| AGT-005, AGT-006, AGT-007, AGT-008 | Root confinement, complete command set, repair route, progressive reference | 10.2, 11, 22 | WP-01, WP-03, WP-04, WP-06 | CLI contract tests, reference inspection, TST-038, TST-051 |
| AGT-009, AGT-010, AGT-011, AGT-012 | Templates, deterministic helper, structured output, failure-closed behavior | 9, 11, 13 through 16, 22 | WP-01, WP-03 through WP-06 | Unit tests, output-schema tests, fault injection |
| STO-001, STO-002, STO-003, STO-004, STO-005 | Root Tasks folder and one named, dated folder per task | 9, 12, 16 | WP-01, WP-04 | TST-003, TST-012 |
| STO-006, STO-007, STO-008, STO-009, STO-010 | Stable unique identity, original name, safe slug, stable folder | 12, 13 | WP-01, WP-04 | TST-004 through TST-006, TST-051 |
| STO-011, STO-012, STO-013, STO-014 | Required task files, response location, offset timestamp, safe filename | 9, 12 through 15 | WP-01, WP-04, WP-05 | Tree inspection, TST-003, TST-014 |
| STA-001, STA-002, STA-003, STA-004, STA-005 | Canonical JSON and generated human views | 13, 14, 16 | WP-01, WP-04, WP-06 | Schema validation, TST-007 through TST-013, TST-051 |
| STA-006, STA-007, STA-008, STA-009, STA-010 | One correctly identified and complete Task Response per substantive task-work or decision turn, with read-only exceptions | 15, 20 | WP-01, WP-05 | TST-014, TST-027, behavioral turn audit |
| STA-011, STA-012, STA-013, STA-014 | Completion statement, append-only corrections, authorized redaction, content privacy | 15, 24 | WP-01, WP-05, WP-06 | TST-015 through TST-017 |
| LIF-001, LIF-002, LIF-003, LIF-004, LIF-005 | Status set, terminal boundary, explicit creation, same-objective continuation | 17, 18, 20 | WP-01, WP-04, WP-05 | TST-018 through TST-020 |
| LIF-006, LIF-007, LIF-008, LIF-009, LIF-010 | Related tasks, parent integrity, recency boundary, exact resolution, ambiguity | 13, 18 | WP-04, WP-05 | TST-021 through TST-025 |
| LIF-011, LIF-012, LIF-013, LIF-014 | Zero/one/many selection flow and terminal-task decision | 18 | WP-02, WP-04, WP-05 | TST-020, TST-026 |
| CTX-001, CTX-002, CTX-003, CTX-004 | First-turn check and zero/one task notice behavior | 19, 23.1 | WP-07, WP-09 | TST-039 |
| CTX-005, CTX-006, CTX-007, CTX-008 | Multiple-task notice, unrelated prompts, continuation language, bounded load | 18, 19 | WP-02, WP-07, WP-09 | TST-028, TST-039, TST-040 |
| CTX-009, CTX-010, CTX-011, CTX-012 | Live-artifact authority, optional thread IDs, memory independence, goal separation | 4, 19 | WP-03, WP-07, WP-09 | TST-040 through TST-043 |
| REL-001, REL-002, REL-003, REL-004 | Helper-only mutation and safe lock ownership | 11, 22 | WP-04 through WP-06 | TST-032, TST-052 |
| REL-005, REL-006, REL-007, REL-008 | Expected revisions, monotonic counters, atomic writes, ordered transactions | 13, 15, 22 | WP-04, WP-05 | TST-033 through TST-036 |
| REL-009, REL-010, REL-011, REL-012 | Regenerable projections, integrity findings, failure-closed behavior, explicit recovery | 14, 16, 22 | WP-06 | TST-011, TST-013, TST-035 through TST-038 |
| REL-013, REL-014 | Path containment and honest response-recording failure | 22, 24 | WP-04 through WP-06 | TST-006, fault-injection receipt checks |
| DIR-001, DIR-002, DIR-003, DIR-004, DIR-005 | Director owns classification, Agent Task use, response recording, truthful state, waiting/blocking | 20, 21 | WP-02, WP-03, WP-05, WP-07 | Behavioral workflow and Task Response inspection |
| DIR-006, DIR-007, DIR-008, DIR-009, DIR-010 | Completion evidence, role consistency, bounded delegation, child boundary, unchanged authority | 17, 20, 21, 24 | WP-05, WP-07, WP-09 | TST-015, TST-044, TST-045 |
| VER-001, VER-002, VER-003, VER-004 | Root guidance, role, README, and ephemeral ignores | 23 | WP-07 | Source comparison and final file inspection |
| VER-005, VER-006, VER-007, VER-008 | Skill validators, helper tests, and invocation-policy tests | 10, 26, 29 | WP-02, WP-03, WP-08 | TST-029, TST-046, TST-047 |
| VER-009, VER-010, VER-011, VER-012 | Creation, lifecycle, resolution, and response test coverage | 26 | WP-08 | TST-003 through TST-026 |
| VER-013, VER-014, VER-015, VER-016 | No-mutation, fault/security tests, cross-thread validation, local-only final audit | 26, 27, 29 | WP-08 through WP-10 | TST-027 through TST-052 |

## 33. Bidirectional traceability verification procedure

Before implementation begins and again before it is accepted:

1. Extract every requirement ID from section 7.
2. Confirm each ID is unique in the requirement catalog.
3. Extract every requirement ID from section 32.
4. Compare the two sets and require no missing or extra IDs.
5. Confirm each requirement maps to at least one plan section, work package, and
   evidence lane.
6. Confirm each planned artifact maps back to one or more requirement IDs.
7. Confirm each test maps to the behavior it can actually prove.
8. Treat a test name, green result, or validator as insufficient when its scope
   does not cover the mapped requirement.
9. Reinspect current files and runtime results rather than accepting the plan's
   prediction as evidence.
10. Record gaps as incomplete work and continue until none remain.

The plan-level audit may use a read-only script to compare requirement tokens.
The future implementation should add a maintained traceability check only if it
provides ongoing value; do not add a permanent script solely to count headings.

## 34. Definition of done for the future implementation

The Task system is complete only when:

1. Every requirement in section 7 has direct current evidence.
2. Both project-local skills are valid and behaviorally tested.
3. The Task helper implements every approved command and failure category.
4. The canonical schema, folder naming, generated projections, and response
   format match this plan.
5. All lifecycle, resolution, concurrency, recovery, security, and no-mutation
   tests pass.
6. A real fresh-thread continuation scenario passes end to end.
7. The Project Director records Task Responses accurately and child agents do
   not own the ledger.
8. Ordinary prompts remain usable without Task mutation.
9. Current project guidance and documentation match runtime behavior.
10. No global, external, destructive, Git, deployment, or user-visible thread
    action occurred without separate authority.
11. The final tree and all Task-system changes have been reinspected.
12. Remaining limitations are stated and do not contradict a required
    acceptance criterion.

Passing unit tests alone does not satisfy this definition. The cross-thread
user workflow and current-state completion audit are mandatory.

## 35. Logical implementation order

Execute the later implementation in this dependency order:

```text
WP-00 baseline and authority
  -> WP-01 schema, templates, and contracts
    -> WP-02 user-facing Task skill
    -> WP-03 internal Agent Task skill
      -> WP-04 storage, identity, and read-only discovery
        -> WP-05 lifecycle and response transactions
          -> WP-06 validation and recovery
            -> WP-07 guidance and documentation integration
              -> WP-08 automated verification
                -> WP-09 cross-thread behavioral validation
                  -> WP-10 final bidirectional audit
```

WP-02 and WP-03 can be drafted independently after WP-01, but integration and
behavioral tests must wait until both exist. Do not start root guidance changes
before the actual command paths and behavior are stable enough to document.

## 36. Plan-level completion standard

This planning task is complete only when the following plan-level claims are
verified against the actual Markdown file:

- The plan exists in the approved project implementation-plan directory.
- The plan explicitly preserves the current-turn planning-only boundary.
- Every requirement from the approved research recommendation appears in the
  requirement catalog.
- Every requirement catalog ID appears in the traceability matrix and no extra
  matrix ID exists.
- Every named future artifact has a specification or work-package owner.
- Every user command, lifecycle status, state field, Task Response section,
  cross-thread rule, failure class, and security boundary appears in the plan.
- The plan includes automated checks and a real cross-thread validation.
- Markdown code fences are balanced and no placeholder markers remain.
- The created plan is reopened after validation.
- No Task-system implementation artifact was created during planning.

## 37. Plan validation record

### 37.1 Automated structural audit

- **Requirement catalog:** PASS. The catalog contains 128 unique requirement
  IDs.
- **Traceability parity:** PASS. The traceability matrix contains the same 128
  unique requirement IDs, with no missing, extra, or duplicate ID.
- **Test catalog:** PASS. The plan contains 52 sequential test IDs from
  `TST-001` through `TST-052`.
- **Work packages:** PASS. The plan contains 11 sequential work packages from
  `WP-00` through `WP-10`.
- **Numbered sections:** PASS. Sections are complete and sequential through
  this validation record.
- **Markdown structure:** PASS. Backtick and tilde code fences are balanced.
- **Whitespace:** PASS. No trailing whitespace was found.
- **Scaffold markers:** PASS. No `TODO`, `TBD`, `REPLACE_ME`, or equivalent
  unfinished scaffold marker was found. Metavariables inside documented
  filename and command templates are intentional contracts.

### 37.2 Requirement-intent audit

The plan was checked for every material requirement from the approved research
recommendation:

- Two local skills with distinct user and Director responsibilities.
- Explicit user control of new task creation.
- Existing Project Director ownership rather than a spawned replacement.
- Root `Tasks/` storage and one named, dated folder per task.
- Stable task IDs and support for same-name tasks.
- New-task, continuation, related-task, update, terminal, and ambiguity rules.
- Canonical JSON, human task brief, generated index, and timestamped Markdown
  Task Responses.
- Required Task Response description, work, evidence, summary, status, next
  step, blocker, completion, and file context.
- Cross-thread first-turn awareness without blocking unrelated conversation.
- Memory, thread, goal, and generated-index non-authority boundaries.
- Live-artifact reinspection before continuation and completion claims.
- Locks, revisions, atomic writes, partial-transaction classification, and
  explicit reconciliation.
- Project guidance, documentation, security, rollback, automated tests, manual
  cross-thread validation, and final bidirectional audit.

Result: **PASS**. No material approved requirement was found without a plan
location, work-package owner, and evidence lane.

### 37.3 Current-state and scope audit

- The final plan was reopened in full after creation and reviewed by section.
- `Tasks/` remains absent.
- `.agents/skills/task/` remains absent.
- `.agents/skills/agent-task/` remains absent.
- No global Task skill or state was created.
- No Git repository was detected, and no commit or push was attempted.
- The only authorized Task-system artifact created by this planning goal is
  `Implementation_Plans/task_system_implementation_plan.md`.

### 37.4 Verification and validation level

- **Highest verification level reached for this plan:** Static checks passed.
- **Plan validation reached:** Requirement-by-requirement design validation
  against the user objective, the approved research recommendation, current
  project guidance, observed project state, and current official Codex skill
  documentation.
- **Deliberate limitation:** No Task-system runtime behavior is claimed because
  implementation is outside this planning goal.
