---
schema_version: 2
trd_id: "TRD-20260902-C2F3AF2B"
title: "Task-triggered Project Director orchestration"
slug: "task-triggered-project-director-orchestration"
created_at: "2026-09-02T09:54:52-06:00"
updated_at: "2026-09-04T15:34:26-06:00"
status: "draft"
revision: 7
last_action_id: "TO-TRD-013"
status_reason: "The user authorized the exact document-centric To-TRD implementation plan, including this lossless schema migration."
---

# Task Requirement Document: Task-triggered Project Director orchestration

## Destination

Define requirements for a future source-only revision of reusable Sys4AI assets. The required source targets are SKILLS-depo/task/ and ROLES-depo/project-director-ROLE.md. SKILLS-depo/agent-task/ and SKILLS-depo/manage-subagent-roles/ are candidate targets whose need for change must be established by requirement-to-artifact impact analysis. After later adoption into a consumer project, explicit Task-skill activation must cause the existing root agent to operate as the Project Director defined by that consumer project root ROLE.md and must support the complete proportional orchestration workflow described below. The active Sys4AI root ROLE.md and installed .agents/skills/ copies are reference-only and must remain unchanged by the future source implementation.

## Captured user intent

U01 - The user reports that invoking the Task skill does not reliably trigger the Project Director role and requires the Task workflow to use the Project Director definition stored in the project-root ROLE.md.
U02 - A task is a user-given job or problem assigned to the Project Director; it may be simple or complex.
U03 - The Project Director manages tasks, judges their complexity, and decides whether a complex task should be split into smaller subtasks.
U04 - Subtasks are assigned to sub-agents whose roles match the work.
U05 - The Director should select suitable existing project roles and may create and store a reusable role when no existing role fits the task or subtask.
U06 - A complex task with substantial uncertainty or unknowns may need multiple adversarial solution agents with different roles or perspectives instead of decomposition.
U07 - The Director decides how many solution agents are appropriate unless the user specifies the orchestration.
U08 - When the Director decides candidate solutions need review, each solution agent receives a reviewer; a failed review returns the solution to its originating agent for revision.
U09 - After all candidate solutions pass review, a senior sub-agent fuses them into one solution; irreconcilable conflicts are explained and returned to all solution agents for another solution cycle.
U10 - The process must culminate in the actual task being performed and verified, but the user explicitly left open whether the senior synthesis agent or the Project Director should own final implementation.
U11 - When the user specifies sub-agent types, counts, roles, or reviewer use, the Project Director follows those instructions within applicable authority and runtime constraints.
U12 - The user explicitly invoked To-TRD and used "TRP" to request this requirements artifact.
U13 - The reusable Task skill package in SKILLS-depo/task/ is a definite future implementation target.
U14 - The reusable Agent Task and Manage Sub-Agent Roles packages in SKILLS-depo/agent-task/ and SKILLS-depo/manage-subagent-roles/ are possible implementation targets; future impact analysis must determine which changes are actually required.
U15 - The reusable Project Director role must be changed in ROLES-depo/project-director-ROLE.md rather than in the active root ROLE.md.
U16 - The active Sys4AI project is not an implementation target for this work; the user will adopt the reusable depot changes into the project later.

## Context and sources

S01 - User-supplied goal objective at /Users/alex.omegapy/.codex/attachments/e46fed61-0f2b-4d14-a36d-77840df9a92a/goal-objective.md, read on 2026-09-02.
P01 - AGENTS.md establishes that the root agent is the Project Director, requires the live role-management workflow before role-based delegation, assigns final integration and verification to the Director, and keeps Task, TRD, native-goal, and other state systems separate.
P02 - ROLE.md currently defines the Project Director's project-level authority, task assessment, decomposition, role selection or creation, delegation contracts, supervision, integration, evidence review, and completion reporting.
P03 - .agents/skills/task/SKILL.md currently says the root agent remains the Project Director and must not spawn a replacement Director, but it does not define the requested adversarial solver-reviewer-synthesis lifecycle.
P04 - .agents/skills/agent-task/SKILL.md and its task-system contract define helper-managed Task state, Director-only lifecycle mutations, append-only Task Responses, and evidence-gated completion.
P05 - SOUL.md requires evidence-based classification, bounded delegation, meaningful retry hypotheses, reorientation instead of repeated failure, direct verification, and truthful blocker reporting.
P06 - .agents/skills/to-trd/SKILL.md defines TRP as an alias for TRD and limits this operation to requirements capture rather than implementation.
S02 - User clarification dated 2026-09-02 that future implementation belongs only in reusable SKILLS-depo and ROLES-depo sources, with active project adoption deferred.
P07 - Live inventory confirmed SKILLS-depo/task/, SKILLS-depo/agent-task/, SKILLS-depo/manage-subagent-roles/, and ROLES-depo/project-director-ROLE.md as the exact reusable source assets named by the clarification.
P08 - Current comparison found the three reusable skill package sources equivalent to their installed .agents/skills/ counterparts when generated __pycache__ files are excluded; ROLES-depo/project-director-ROLE.md is the generic reusable role and differs from the active Sys4AI root ROLE.md.
No external research was needed because this document specifies project-local behavior from the user's statement and inspected project contracts.

## In scope

Requirements for a future source-only implementation in SKILLS-depo/task/ and ROLES-depo/project-director-ROLE.md.
Requirement-to-artifact impact analysis for SKILLS-depo/agent-task/ and SKILLS-depo/manage-subagent-roles/, followed by changes only where the behavioral contract requires them.
Requirements for the future relationship among the reusable Project Director role, Task skill, Agent Task workflow, role-management workflow, and native sub-agent orchestration after later project adoption.
Requirements for task definition, complexity and uncertainty assessment, simple-task handling, decomposition, role matching and role creation, adversarial candidate solutions, per-solution review, revision, senior synthesis, conflict recycling, implementation ownership, completion verification, user overrides, and truthful stopping conditions.
Source-package structural, focused workflow, cross-package, and scenario checks plus protected-active-copy verification.
This operation revises the requirements baseline only.

## Out of scope

Implementing the reusable skill or role changes in this TRD revision.
Modifying the active root ROLE.md, AGENTS.md, or any installed package under .agents/skills/.
Installing, synchronizing, copying, or otherwise adopting depot changes into the Sys4AI root, the project template, or any registered project; the user will perform or authorize that separately later.
Restoring, modifying, or replacing the currently deleted ROLES-depo/sys4ai-depot-ROLE.md or changing unrelated reusable assets.
Spawning solver, reviewer, senior, or implementation sub-agents to perform the future workflow during requirements capture.
Selecting a fixed number of solvers or reviewers for every task.
Creating a reusable role when an existing valid role already fits or when the gap is a missing tool, skill, permission, or external capability rather than a role gap.
Changing model or reasoning-effort inheritance, runtime concurrency limits, platform permissions, or higher-priority safety and authorization rules.
Treating Task activation, Task creation, TRD creation, a native goal, a child-agent result, or a synthesized solution as proof that the actual user job is complete.
Committing, pushing, publishing, deploying, sending external messages, installing dependencies, or performing destructive actions.

## Task requirements

### REQ-001 - Activate the root Project Director
- Requirement: Explicit Task-skill activation must cause the existing root agent to read and apply the Project Director role defined by the ROLE.md at the established project root for the entire Task workflow.
- Source: U01 - required role activation and exact root role source; P01 and P03 - current root-agent and no-replacement contracts.
- Acceptance: A representative Task invocation resolves the established project root, identifies its ROLE.md as the governing Project Director role, applies that role before any Task mutation or delegation decision, and does not spawn or substitute a second Director.
- Depends on: None.

### REQ-002 - Define a task consistently
- Requirement: The Project Director and Task workflow must define a task as a user-given job or problem assigned to the Project Director that may range from simple to complex.
- Source: U02 - user-provided Task definition.
- Acceptance: The authoritative role and Task contracts use one compatible definition and do not confuse a project Task with a subtask, Codex conversation, native goal, TRD, implementation plan, or child-agent assignment.
- Depends on: REQ-001

### REQ-003 - Define Director task-management ownership
- Requirement: The root Project Director role must explicitly own task intake, scope and authority analysis, complexity assessment, decomposition decisions, orchestration choice, role selection, supervision, synthesis acceptance, implementation ownership decisions, final verification, and user-facing completion claims.
- Source: U03 and U10 - Director task-management and end-to-end responsibility; P01 and P02 - current project-level authority.
- Acceptance: ROLES-depo/project-director-ROLE.md and the reusable Task workflow in SKILLS-depo/task/ assign every listed decision to the Project Director, keep Task-ledger mutations with the Director, and prevent child agents from claiming project-level completion or expanding authority.
- Depends on: REQ-001, REQ-002

### REQ-004 - Classify task complexity and uncertainty
- Requirement: Before choosing an execution pattern, the Project Director must assess task complexity, uncertainty, unknowns, decomposability, dependency structure, risk, review need, and evidence needed for completion.
- Source: U03, U06, and U08 - complexity, uncertainty, decomposition, and review decisions; P02 and P05 - current assessment and evidence discipline.
- Acceptance: Representative simple, decomposable-complex, and uncertain-nondecomposable scenarios produce an explicit workflow classification with a concise evidence-based rationale and no invented numeric threshold.
- Depends on: REQ-003

### REQ-005 - Handle simple tasks without unnecessary delegation
- Requirement: The Project Director may perform a simple, low-risk task directly when decomposition, adversarial solution development, or delegated review would not add material value.
- Source: U02 and U03 - tasks may be easy or simple and the Director decides complexity; P02 - delegation must add material value.
- Acceptance: A representative simple task stays with the Director, incurs no unnecessary child-agent workflow, and still receives proportionate verification before completion.
- Depends on: REQ-004

### REQ-006 - Decompose suitable complex tasks
- Requirement: When a complex task can be made safer or easier by decomposition, the Project Director must split it into bounded subtasks with clear dependencies, ownership, deliverables, allowed scope, protected state, checks, and stopping conditions.
- Source: U03 and U04 - break complex problems into subproblems and assign them; P02 - current delegation-contract requirements.
- Acceptance: A representative decomposable task produces complete subtask contracts, identifies ordering and safe parallel work, prevents conflicting write ownership, and preserves Director-level decisions for the Director.
- Depends on: REQ-004

### REQ-007 - Select suitable existing roles
- Requirement: Before delegating a subtask or orchestration function, the Project Director must inspect the live project role catalog and select the narrowest valid existing role whose capabilities and authority fit the work.
- Source: U04 and U05 - use existing project sub-agent roles when they fit; P01 and P02 - mandatory live role-catalog workflow.
- Acceptance: Each delegated solver, reviewer, synthesizer, or implementer has a documented task profile, selected role, role-file paths, fit rationale, authority limits, and stopping condition based on a fresh valid catalog.
- Depends on: REQ-004

### REQ-008 - Create a reusable role only for a real role gap
- Requirement: If no valid existing role fits and the missing responsibility is reusable, the Project Director may create, store, validate, and then select a new role in the project's approved role catalog; a missing skill, tool, permission, or external dependency must be reported rather than disguised as a role.
- Source: U05 - create and save a role when no existing role matches; P01 and P02 - reusable-role creation and capability boundaries.
- Acceptance: A no-fit scenario either yields a new non-overwriting role bundle that passes the live catalog validator before use or yields an exact capability or authority blocker, while an existing-fit scenario creates no duplicate role.
- Depends on: REQ-007

### REQ-009 - Run an adversarial multi-solution path for uncertain tasks
- Requirement: When a complex task has substantial uncertainty or unknowns and decomposition would not adequately reduce them, the Project Director may assign the same bounded problem to two or more independent solution agents using deliberately different suitable roles or perspectives.
- Source: U06 and U07 - adversarial agents with different roles and a Director-selected count.
- Acceptance: A representative uncertain task records why the adversarial path was chosen, gives every solver the same objective and governing evidence, distinguishes their roles or perspectives, preserves independent candidate solutions, and uses a task-appropriate count rather than a fixed global number.
- Depends on: REQ-004, REQ-007

### REQ-010 - Honor explicit user orchestration
- Requirement: The Project Director must follow explicit user instructions about sub-agent use, counts, roles, perspectives, reviewer use, or review omission unless a higher-priority authority, safety, capability, or runtime constraint prevents it.
- Source: U11 - user-specified orchestration takes precedence over Director defaults.
- Acceptance: Scenario checks show feasible user-specified orchestration is preserved exactly, while an infeasible or unauthorized instruction causes a specific disclosed conflict and no silent substitution.
- Depends on: REQ-004

### REQ-011 - Assign one reviewer to each candidate solution
- Requirement: When the Project Director determines that an adversarial solution workflow requires formal review, each candidate solution must be assigned to its own reviewer role before synthesis.
- Source: U08 - one reviewer for each solution agent when review is required.
- Acceptance: The orchestration record contains a one-to-one solver-output-to-reviewer mapping with no unreviewed candidate entering synthesis and no reviewer silently acting as the final Project Director.
- Depends on: REQ-007, REQ-009

### REQ-012 - Return failed reviews for targeted revision
- Requirement: A reviewer that does not accept a candidate solution must return a clear failure explanation and actionable revision requests to the originating solution agent, after which the revised solution must be reviewed again.
- Source: U08 - failed solutions return to their agents for modification.
- Acceptance: A failing review scenario preserves the original candidate and review outcome, sends the findings to the correct solver, produces a materially revised candidate, and records the subsequent review result without treating rejection as completion.
- Depends on: REQ-011

### REQ-013 - Fuse reviewed solutions through a senior agent
- Requirement: After all required candidate reviews pass, the Project Director must assign a distinct senior synthesis agent to combine all accepted solutions and review findings into one coherent proposed solution.
- Source: U09 - senior sub-agent fuses all reviewed solutions.
- Acceptance: The senior synthesis receives every accepted candidate and material review finding, preserves compatible contributions, explains how differences were resolved, and returns one integrated proposal to the Project Director.
- Depends on: REQ-007, REQ-012

### REQ-014 - Recycle irreconcilable conflicts
- Requirement: If the senior synthesis agent cannot reconcile genuine conflicts among candidate solutions, it must identify the exact conflicts and send the same conflict explanation back to every affected solution agent for another solution-and-review cycle.
- Source: U09 - conflicts that prevent fusion return with an explanation to all solution agents and restart the process.
- Acceptance: A conflict scenario produces a shared conflict record, targeted revised candidates from every affected solver, repeated required reviews, and another synthesis attempt; no conflicting choice is silently discarded or presented as fused.
- Depends on: REQ-013

### REQ-015 - Assign final implementation ownership explicitly
- Requirement: After the Project Director accepts a fused solution, the workflow must name exactly one accountable owner for performing or implementing the final solution under the Director's scope and authority controls.
- Source: U10 - actual implementation is required, while ownership between the senior agent and Director remains unresolved.
- Acceptance: The authoritative workflow records whether the senior synthesis agent or the Project Director owns implementation before execution begins, and no candidate, review pass, or synthesis artifact is mislabeled as implementation.
- Depends on: REQ-013

### REQ-016 - Verify the user's actual task before completion
- Requirement: The Project Director must mark the project Task complete only after the final solution has been performed, implemented, or delivered as authorized and every definition-of-done criterion has current direct evidence.
- Source: U10 - the system must end with the actual task done; P01, P02, P04, and P05 - Director-owned evidence-gated completion.
- Acceptance: Completion scenarios contain criterion-by-criterion evidence inspected by the Director, reject child-agent completion messages as sole proof, distinguish unexercised external or runtime behavior, and produce one truthful final Task Response.
- Depends on: REQ-015

### REQ-017 - Preserve an auditable orchestration record
- Requirement: The Task workflow must durably record the workflow classification, decomposition or adversarial decision, delegated roles and child identifiers, reviewer mappings and outcomes, revision cycles, synthesis result, implementation owner, blockers, and completion evidence needed for continuation and audit.
- Source: U03 through U10 - the Director must manage the complete multi-stage process; P04 - durable canonical Task state and Task Responses.
- Acceptance: A later Project Director can reconstruct the current workflow state from governed project records without hidden reasoning, a full transcript, stale memory, or inference from child-agent status alone.
- Depends on: REQ-003

### REQ-018 - Preserve authority and state boundaries
- Requirement: The redesigned workflow must keep the project Task ledger, subtask contracts, child-agent state, managed TRDs, implementation plans, Codex conversations, and native goals distinct, and it must not expand permission for destructive, external, installation, Git, publication, or deployment actions.
- Source: P01 through P06 - current project state and authority boundaries; U11 - user instructions remain subject to applicable constraints.
- Acceptance: Contract and scenario checks show each state system has one documented authority, contradictions are reported rather than merged, and Task or role activation alone performs no separately governed external or destructive action.
- Depends on: REQ-003

### REQ-019 - Stop or escalate when iteration cannot progress
- Requirement: Solver revision, review, and fusion cycles must continue only when each cycle has a material new hypothesis, evidence item, or targeted change; missing authority, unavailable capability, runtime limits, repeated unchanged failure, or irreducible conflict must become a truthful blocker or user decision instead of an infinite loop or false completion.
- Source: U09 and U10 - repeat toward fusion and actual completion; P05 - persistence, reorientation, and truthful blocking rules.
- Acceptance: A no-progress or unavailable-capability scenario stops without fabricating fusion or completion, records the exact blocker and smallest needed decision or state change, and can resume from the durable Task record.
- Depends on: REQ-012, REQ-014, REQ-018

### REQ-020 - Place required changes in reusable depots
- Requirement: The future implementation must change the canonical reusable Task skill package in SKILLS-depo/task/ and the generic Project Director role source at ROLES-depo/project-director-ROLE.md rather than their active project copies.
- Source: U13 and U15 - definite source targets; S02 and P07 - clarified and observed depot locations.
- Acceptance: The implementation change set contains requirement-linked changes in both required reusable targets and contains no corresponding change in the active root ROLE.md or .agents/skills/task/.
- Depends on: None.

### REQ-021 - Determine conditional skill-package impact
- Requirement: Before implementation, map every orchestration requirement to SKILLS-depo/agent-task/ and SKILLS-depo/manage-subagent-roles/ and modify either package only when a specific contract, helper, schema, template, metadata, documentation, or test change is required.
- Source: U14 - Agent Task and Manage Sub-Agent Roles are probable but not confirmed change targets; P07 and P08 - observed packages and current source-to-active parity.
- Acceptance: A requirement-to-artifact impact matrix gives a changed or unchanged disposition with evidence for each named package and file, and no speculative or duplicate edit is made merely because the package participates in the workflow.
- Depends on: REQ-020

### REQ-022 - Preserve active project copies for later adoption
- Requirement: The future source implementation must leave the active Sys4AI root ROLE.md, AGENTS.md, .agents/skills/task/, .agents/skills/agent-task/, .agents/skills/manage-subagent-roles/, project template, registered projects, and unrelated depot assets unchanged.
- Source: U15 and U16 - role and skill work belongs in the depots and active project adoption is deferred; S02 and P08 - clarified boundary and observed baselines.
- Acceptance: Pre-change and post-change scoped hashes and repository status prove every protected active path is unchanged, no install or synchronization operation ran, and the existing deletion of ROLES-depo/sys4ai-depot-ROLE.md was neither restored nor modified.
- Depends on: REQ-020

### REQ-023 - Validate source-only deliverables
- Requirement: The future implementation must validate every changed reusable skill package and the reusable Project Director role as source artifacts, including cross-package references and representative direct, decomposed, adversarial, review-revision, fusion-conflict, user-override, completion, and failure workflows.
- Source: U13 through U16 - reusable source delivery boundary; P01, P02, P05, P07, and P08 - project verification discipline and observed asset layout.
- Acceptance: All affected source-package structural validators and focused tests pass, cross-package checks cover every changed contract, the reusable role passes its applicable review, scoped diff checks pass, no new generated residue remains, and protected active-copy hashes remain unchanged.
- Depends on: REQ-020, REQ-021, REQ-022

## Decisions

D01 - "TRP" is treated as the To-TRD skill's documented alias for a Task Requirement Document, so this operation creates one managed TRD rather than a separate artifact type. Source: U12 and P06.
D02 - "Trigger the Project Director" means the existing root agent must load and apply the exact project-root ROLE.md; it does not mean spawning a replacement Director. Source: U01, P01, and P03.
D03 - The future workflow has three proportional paths: direct Director execution for simple work, decomposition for separable complex work, and adversarial multi-solution work for complex uncertainty that decomposition does not resolve. Source: U02, U03, U06, and P02.
D04 - Reviewer assignment is conditional on the Director or user selecting formal review; when selected, the one-reviewer-per-candidate rule applies. Source: U08.
D05 - This document remains draft because final implementation ownership is unresolved and no implementation is authorized by TRD creation. Source: U10 and P06.
D06 - Future implementation is source-only: SKILLS-depo/task/ and ROLES-depo/project-director-ROLE.md are required targets. Source: U13, U15, S02, and P07.
D07 - SKILLS-depo/agent-task/ and SKILLS-depo/manage-subagent-roles/ are impact-analysis candidates, not automatic edit targets. Source: U14, P07, and P08.
D08 - Active root and installed copies remain unchanged until a later, separately authorized adoption step. Source: U16, S02, and P08.

## Open questions

Q01 - After a fused solution is accepted, should the default implementation owner be the senior synthesis agent, the Project Director, or should the Project Director choose case by case based on the task? Source: U10.

## Not yet specified

None.

## Assumptions

None.
