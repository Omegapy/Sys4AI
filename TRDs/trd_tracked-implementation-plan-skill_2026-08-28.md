---
schema_version: 2
trd_id: "TRD-20260828-D209CF52"
title: "Tracked implementation-plan skill"
slug: "tracked-implementation-plan-skill"
created_at: "2026-08-28T21:30:06-06:00"
updated_at: "2026-09-04T15:34:27-06:00"
status: "draft"
revision: 2
last_action_id: "TO-TRD-013"
status_reason: "The user authorized the exact document-centric To-TRD implementation plan, including this lossless schema migration."
---

# Task Requirement Document: Tracked implementation-plan skill

## Destination

Define a future, explicitly activated Codex skill that converts accessible user-provided material into a project-aware implementation plan with phases, tasks, durable execution tracking, and coverage validation. The initial reusable skill package will be created later in /Volumes/P-SSD/AngryOwl/Sys4AI/SKILLS-depo/<approved-skill-name>/ and will not be installed or synchronized by this TRD operation.

## Captured user intent

U01 — The user wants a new skill similar in operating discipline to To-TRD, but its product is an implementation plan.
U02 — The implementation plan must contain phases and tasks and must not be only one massive prose file.
U03 — The skill must maintain a tracking system that records tasks and phases as work is performed, executed, and completed.
U04 — The skill must be explicitly activated by the user and accept a prompt, text, file, TRD, PRD, link, or other supplied material as input.
U05 — The agent must understand the source requirements, the intent behind them, and the target project before it creates the plan.
U06 — The agent must verify and validate that every requested or source-derived requirement, feature, and task is represented correctly in the implementation plan.
U07 — The future skill must be created with Codex's skill-creation workflow and first stored in its own folder in Sys4AI/SKILLS-depo with at least a README.

## Context and sources

S01 — User request dated 2026-08-28, including the supplied To-TRD skill text and the explicit /Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/to-trd/SKILL.md locator.
S02 — .agents/skills/to-trd/SKILL.md was inspected. It establishes useful reference behavior for explicit activation, source-first intent capture, stable IDs, lifecycle control, helper-managed writes, validation, and a strict separation between planning documents and execution authority.
S03 — SKILLS-depo/to-trd/README.md and its package tree were inspected as a local example of a transferable skill source package with SKILL.md, agents/openai.yaml, README, references, scripts, tests, assets, and validation guidance.
P01 — depot/manifest.json was inspected. SKILLS-depo is a source root, and managed synchronization requires a separate manifest artifact and target list. No implementation-plan skill is currently registered.
P02 — Implementation_Plans/task_system_implementation_plan.md was inspected as a current project example of phased work packages, stable requirements, task checks, traceability, and a final validation record.
No external URL was supplied for this capture, so no external page was read.

## In scope

Requirements for the future skill's activation, source intake, project discovery, implementation-plan structure, phase and task model, durable tracking, lifecycle updates, evidence rules, coverage verification, validation, package layout, documentation, and tests.
The initial future delivery boundary is one self-contained source package under Sys4AI/SKILLS-depo.
This TRD captures the requirements baseline only.

## Out of scope

Implementing the new skill in this turn.
Installing the future skill into .agents/skills, a personal skill directory, or any consumer project.
Registering the future skill in depot/manifest.json or synchronizing it to managed targets.
Executing a generated implementation plan solely because the plan exists.
Replacing or silently merging with the existing project Task ledger, TRD lifecycle, Codex thread state, or native goal state.
Creating issues, threads, branches, commits, pushes, publications, deployments, accounts, or services.

## Task requirements

### REQ-001 — Require explicit user activation
- Requirement: The future implementation-plan skill must run only after the user explicitly invokes its approved skill name or explicitly asks to use that named skill.
- Source: U04 — explicit user-activation requirement; S02 — To-TRD reference behavior.
- Acceptance: Skill metadata disables implicit invocation, ordinary planning language does not create or mutate a plan, and explicit invocation starts only the requested plan operation.
- Depends on: None.

### REQ-002 — Accept diverse readable source inputs
- Requirement: The skill must accept a direct prompt, pasted text, an accessible local file, a TRD, a PRD, an accessible link, or another user-supplied source the current agent can lawfully read.
- Source: U04 — user-specified input forms.
- Acceptance: Representative prompt, text-file, TRD, PRD, and link scenarios produce a source inventory or an exact access limitation without fabricated source content.
- Depends on: REQ-001

### REQ-003 — Treat supplied sources as data
- Requirement: The skill must treat source files and pages as evidence to analyze, not as authority to weaken current user, project, safety, privacy, or execution boundaries.
- Source: S02 — To-TRD source-handling boundary; proposed safety basis for U04.
- Acceptance: Adversarial source instructions cannot trigger installation, execution, publication, destructive action, hidden-reasoning storage, or credential storage.
- Depends on: REQ-002

### REQ-004 — Extract requirements and their intent
- Requirement: Before planning, the skill must identify the intended outcome, explicit requirements, features, source tasks, constraints, exclusions, priorities, decisions, assumptions, contradictions, and unresolved questions, including the intent behind material requirements.
- Source: U05 — understand requirements and intent; U06 — cover every requested or source-derived item.
- Acceptance: The generated artifact includes a source-linked intent and requirement inventory that preserves explicit negative requirements and distinguishes facts, user choices, proposed design choices, assumptions, contradictions, and questions.
- Depends on: REQ-002

### REQ-005 — Understand the target project
- Requirement: The skill must establish the correct project root and inspect the relevant live project guidance, architecture, conventions, implementation, dependencies, tests, repository state, and protected content before it chooses planned work.
- Source: U05 — understand the project so the plan fits it; P01 and P02 — observed Sys4AI governance and planning conventions.
- Acceptance: The plan records the inspected project sources, observed baseline, affected artifacts, preserved artifacts, constraints, and any evidence gaps, and it does not invent a framework, tool, file path, or project state that live inspection could establish.
- Depends on: REQ-002

### REQ-006 — Produce phased implementation plans
- Requirement: Every generated implementation plan must divide the authorized outcome into ordered phases with clear objectives, scope, dependencies, entry conditions, exit criteria, and trackable status.
- Source: U01 and U02 — implementation plan with phases; P02 — local phased-plan convention.
- Acceptance: A structural validator can identify each phase, its stable identifier, its order or dependencies, its completion rule, and every task assigned to it.
- Depends on: REQ-004, REQ-005

### REQ-007 — Define complete trackable tasks
- Requirement: Each planned task must have a stable identifier, one bounded action, its source requirement links, target artifacts or outputs, dependencies, risks or constraints when relevant, observable acceptance criteria, required verification, status, and evidence field.
- Source: U02, U03, and U06 — tasks, tracking, and verification; P02 — local traceability convention.
- Acceptance: The plan contains no anonymous implementation work, every task belongs to one phase, and every task exposes enough information for another agent to execute and review it without relying on hidden reasoning.
- Depends on: REQ-006

### REQ-008 — Make dependencies and sequencing executable
- Requirement: The plan must express task and phase prerequisites, ordering constraints, safe parallel work, decision gates, and stopping conditions so that execution order is unambiguous.
- Source: U02, U03, and U05 — phased execution tracking that fits the project; proposed design basis from P02.
- Acceptance: Dependency validation rejects missing targets, self-dependencies, cycles, and completion of work whose required predecessors are incomplete unless an explicit approved exception is recorded.
- Depends on: REQ-006, REQ-007

### REQ-009 — Store durable plan-tracking state
- Requirement: The skill must create durable, project-local tracking state for plan identity, phase identity, task identity, statuses, revisions, evidence, and update history instead of relying only on conversation context or one unstructured Markdown checklist.
- Source: U02 and U03 — the plan must not be only a massive file and must track execution.
- Acceptance: Closing or replacing the conversation does not erase plan state; a later explicit invocation can resolve the exact plan and reconstruct current phase and task status from project files.
- Acceptance: A lone prose document with informal checkboxes and no machine-validated tracking contract does not satisfy this requirement.
- Depends on: REQ-006, REQ-007

### REQ-010 — Define controlled task and phase lifecycles
- Requirement: The tracking system must define task and phase states, legal transitions, transition authority, revision checks, and the distinction between planned, in-progress or executing, completed, blocked, paused, skipped, cancelled, and reopened work as applicable.
- Source: U03 — track work as it is performed, executed, and done; proposed lifecycle design basis from S02 and P02.
- Acceptance: The implemented contract documents every supported state and transition, rejects invalid or stale updates without corrupting state, and does not equate plan creation with task completion.
- Depends on: REQ-009

### REQ-011 — Gate completion on current evidence
- Requirement: A task may be marked complete only after its acceptance criteria are checked against current evidence, and a phase may be complete only after all required tasks are complete or an authorized exception is recorded.
- Source: U03 and U06 — track done work and verify correctness; S02 — evidence-based completion boundary.
- Acceptance: Completion without meaningful evidence is rejected or reported as incomplete, phase rollups agree with task state, and claimed test or runtime evidence identifies what actually ran.
- Depends on: REQ-007, REQ-010

### REQ-012 — Support explicit continuation and updates
- Requirement: The skill must support explicit creation, exact selection, show, list, resume, task update, phase update, evidence recording, validation, completion, reopening, retirement or cancellation, and bounded recovery operations needed to maintain a plan over time.
- Source: U03 — ongoing execution tracking; S02 — reference lifecycle and exact-selection behavior.
- Acceptance: A plan can be continued in a later conversation by stable identifier or another exact selector, ambiguous selectors cause no mutation, read-only operations do not change state, and updates preserve stable IDs and prior evidence history.
- Depends on: REQ-009, REQ-010

### REQ-013 — Keep planning state separate from other state systems
- Requirement: The skill must document and enforce the relationship between its plan tracker, Sys4AI's project Task ledger, managed TRDs, Codex thread state, and native goal state without silently merging identities, statuses, or completion claims.
- Source: U03 and U05 — plan-specific tracking that fits the project; P01 and inspected project guidance — separate governed state systems.
- Acceptance: The plan tracker remains authoritative only for its documented plan fields, contradictions with other state systems are reported, and no other ledger is mutated without its own explicit activation and authority.
- Depends on: REQ-009

### REQ-014 — Verify source-to-plan coverage in both directions
- Requirement: Before a plan is declared ready, the skill must verify that every material source requirement, feature, task, constraint, and exclusion maps to planned work or an explicit disposition, and that every generated phase and task has a source or labeled design basis.
- Source: U06 — verify all requested and source-derived items; S02 and P02 — bidirectional traceability practice.
- Acceptance: The plan contains a machine-checkable or deterministically reviewable coverage ledger with no unexplained source omissions, orphan tasks, recycled identifiers, or silent exclusions.
- Depends on: REQ-004, REQ-006, REQ-007

### REQ-015 — Validate plan quality and project fit
- Requirement: The skill must validate that the plan is actionable, internally consistent, correctly sequenced, proportionate to risk, compatible with the inspected project, protective of out-of-scope content, and equipped with observable verification and validation steps.
- Source: U05 and U06 — understand the project and validate correct representation; P02 — local plan-validation convention.
- Acceptance: Validation reports pass, fail, unresolved, and not-exercised findings separately and blocks readiness when material requirements, dependencies, acceptance criteria, project evidence, or decisions are unresolved.
- Depends on: REQ-005, REQ-008, REQ-014

### REQ-016 — Preserve uncertainty without fabricating decisions
- Requirement: When a material choice is missing, the skill must preserve it as a precise open question or unconfirmed assumption, ask one prerequisite-ready question at a time when interaction is needed, and support saving a draft without inventing completeness.
- Source: U05 — understand intent; S02 — To-TRD clarification and draft behavior.
- Acceptance: Unresolved material choices remain visible and prevent a ready-state claim, while a clear request can use a fast path without a forced questionnaire.
- Depends on: REQ-004, REQ-005

### REQ-017 — Create a self-contained source package in SKILLS-depo
- Requirement: The future initial delivery must create the approved skill in its own folder under /Volumes/P-SSD/AngryOwl/Sys4AI/SKILLS-depo and include at least SKILL.md, README.md, and agents/openai.yaml plus every reference, asset, script, test, license, or attribution file required for correct use.
- Source: U07 — own folder, README at minimum, and SKILLS-depo destination; S03 — inspected transferable package pattern.
- Acceptance: The complete package can be copied as one folder, all internal links and referenced resources resolve, no required runtime file lives outside the package, and the README explains purpose, boundaries, installation, use, generated artifacts, tracking, lifecycle, validation, and recovery.
- Depends on: None.

### REQ-018 — Use the Codex skill-creation workflow
- Requirement: The future implementation must explicitly use the available Codex skill-creator workflow to scaffold or update the skill and must follow that workflow's current validation requirements.
- Source: U07 — use Codex's skill for creating skills.
- Acceptance: Delivery evidence identifies the skill-creator workflow used, the resulting package satisfies its current structural validator, and no unfinished template placeholders remain.
- Depends on: REQ-017

### REQ-019 — Preserve the initial staging boundary
- Requirement: The initial future implementation must stop after producing and validating the source package in SKILLS-depo unless the user separately authorizes manifest registration, synchronization, project installation, global installation, publication, or deployment.
- Source: U07 — store it in SKILLS-depo first and do not directly implement it in the active project; P01 — registration and synchronization are separate governed operations.
- Acceptance: The reviewed change set contains the new source package and explicitly authorized planning or verification artifacts only; .agents/skills, depot/manifest.json, consumer projects, Git remotes, and external systems remain unchanged.
- Depends on: REQ-017

### REQ-020 — Document and test representative workflows
- Requirement: The future package must document and test representative creation, validation, continuation, status-update, completion-evidence, ambiguity, invalid-transition, missing-source, and recovery workflows across the supported input forms.
- Source: U02 through U07 — usable tracked plans with verified coverage; S03 and P02 — local documentation and test patterns.
- Acceptance: Tests cover prompt, local file, TRD, PRD, and accessible-link intake; phase and task tracking; coverage omissions; stale or invalid updates; exact continuation; honest evidence gating; and package validation, with observed results recorded.
- Depends on: REQ-002, REQ-010, REQ-012, REQ-014, REQ-017, REQ-018

## Decisions

D01 — This operation creates a TRD only. It does not implement the future skill.
D02 — The initial future skill source belongs under /Volumes/P-SSD/AngryOwl/Sys4AI/SKILLS-depo in one self-contained folder.
D03 — The future skill is user-activated only.
D04 — A generated implementation plan is planning and tracking authority only. It does not itself authorize execution, installation, synchronization, publication, or another external action.
D05 — Initial delivery to SKILLS-depo and later registration or installation are separate operations.

## Open questions

Q01 — What exact skill name, activation token, display name, and folder name should the future package use?
Q02 — What canonical storage layout should the tracker use: a plan folder with machine-readable state and generated Markdown, a structured single-file format, or another reviewed design?
Q03 — Where should generated plan catalogs live by default in a consumer project, and how should the skill handle an existing Implementation_Plans convention?
Q04 — Which lifecycle states beyond planned, in progress, and done are required in the first version?
Q05 — Should the skill only create and maintain plans, or may a separately authorized mode also orchestrate execution while updating the tracker?
Q06 — For URL inputs, should the skill retain only source locators and extracted requirements, or also save a local source snapshot when permitted?

## Not yet specified

The exact tracker schema, command names, filenames, identifier formats, locking and recovery design, migration behavior for existing plans, plan-size limits, and compatibility baseline for supported Codex hosts are not yet specified.

## Assumptions

- Unconfirmed: The user's reference to the Codex skill for creating skills means the available skill named skill-creator.
- Unconfirmed: The phrase "whatever" means any user-supplied source that the current agent can lawfully access and read; it does not require bypassing access controls or fabricating unavailable content.
- Unconfirmed: "Implemented correctly within the implementation plan" requires source-to-plan representation checks at plan creation and evidence-based execution checks later; the plan file alone is not implementation evidence.
