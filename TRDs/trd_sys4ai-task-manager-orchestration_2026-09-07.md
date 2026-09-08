---
schema_version: 2
trd_id: "TRD-20260907-ED998433"
title: "Sys4AI task-manager orchestration"
slug: "sys4ai-task-manager-orchestration"
created_at: "2026-09-07T23:47:10-06:00"
updated_at: "2026-09-07T23:50:25-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 1 as the completed requirements document."
---

# Task Requirement Document: Sys4AI task-manager orchestration

## Destination

Define a requirements baseline for Sys4AI's explicitly activated Task workflow to launch a real Project Director in task-manager mode and coordinate `generic`, `complex`, and `extra-complex` subtasks with persisted roles, exact model and reasoning identity, and verified integrated results. The target delivery spans reusable depot sources, the designated Template, and the active Sys4AI root.

## Captured user intent

- U01: The user invoked `/goal` and `$to-trd` with the supplied requirements-and-recommendations file. This authorizes capture of a project-local requirements document. The user explicitly directed the agent to distinguish instructions inside the file from the user's actual request.
- U02: In response to the exact scope question, the user answered `yes`: the TRD covers reusable depot sources, `Projects/Sys4AI-Template-Project/`, and the active Sys4AI root, with other product projects excluded. This answer settles the requirements scope; it does not approve an unseen TRD or authorize implementation or migration now.
- The supplied file describes a real native task manager, subtask-level category selection, one worker for generic work, independent solvers and senior fusion for complex work, one reviewer per solver for extra-complex work, conflict recycling, and a separate dedicated implementation worker for accepted multi-solution work when implementation is required and authorized.
- The resulting workflow must remain project-aware, preserve existing governed state and local specializations, and distinguish a completed proposal from performed implementation. Source-design recommendations are retained below with their actual proposal status.

## Context and sources

| Label | Source and relevance |
| --- | --- |
| U01 | Current user request to use `$to-trd` on the shared file and distinguish document instructions from request authority. |
| U02 | Current user's `yes` to the three named target destinations and exclusion of other product projects. |
| S01 | [Sys4AI_Task_Orchestration_Requirements_and_Recommendations.md](/Users/alex.omegapy/Downloads/Sys4AI_Task_Orchestration_Requirements_and_Recommendations.md), prepared September 7, 2026. Inspected SHA-256: `22df91ebb00fa088a072d8b06f743021fab062a0aa53cc1876eaa156c3551cbd`. Sections 1-3 define the workflow and TM-01 through TM-36; sections 4-12 elaborate behavior; sections 13-16 propose edits, phases, and evidence; section 17 registers its sources. |
| G01 | Current [root AGENTS.md](../AGENTS.md): depot identity, reusable-source and project ownership, explicit adoption, Task and TRD authority, preservation, and completion requirements. |
| G02 | Current [root ROLE.md](../ROLE.md): Director responsibility, existing orchestration, exact identity, ownership, progress, and evidence requirements. |
| G03 | Current [installed Task skill](../.agents/skills/task/SKILL.md) and [Agent Task skill](../.agents/skills/agent-task/SKILL.md): explicit intake, root-specific matching and 30-day aging, canonical helper and lifecycle rules. |
| G04 | Current [role-management skill](../.agents/skills/manage-subagent-roles/SKILL.md), [role schema](../.agents/skills/manage-subagent-roles/references/role-schema.md), and [role helper](../.agents/skills/manage-subagent-roles/scripts/role_catalog.py): fresh valid paired-file roles, current `sub-agent-roles` discovery, and current persistent-index prohibition. |
| G05 | Current [SPECS.md](../SPECS.md), [project registry](../depot/projects.json), and [Template mappings](../depot/template-update.json): Python standard-library helpers, exact depot and Template identities, and current source-to-Template role destinations. |
| G06 | Current [SOUL.md](../SOUL.md) and [to-trd skill](../.agents/skills/to-trd/SKILL.md): source fidelity, preservation, truthful verification, bounded persistence, document-only capture, and exact-revision approval. |

S01 is a handoff document, not an independently verified transcript of its earlier authoring conversation. Its `U`, `D`, and `P` labels mean reported user intent, derived requirement, and proposal respectively. REQ-001 through REQ-029 normalize its reported and derived outcomes. Retained governance constraints and the explicit scope answer supply the additional requirements. A proposal is not promoted merely because its source uses `must`; the disposition of every P-labeled item is recorded under Decisions.

S01 examined commit `947e0ea217eeb52369b33fd76d24079cea1d7e10`. The live checkout has that HEAD plus existing local changes, including the Director and installed/reusable to-trd files. Current inspected files govern the present operation. The current Task contract retains the calling root agent as Director, uses the older execution paths, and limits implementation ownership to the Director or senior; the current role system uses `sub-agent-roles/` and prohibits a persisted index. The requirements describe deliberate future changes to those contracts. They do not activate the proposed rules during this capture.

The registry currently identifies the Sys4AI depot and designated Template. Registration remains factual inventory. Source-register web references and native-runtime claims in S01 were not independently revalidated as part of this document capture. No native manager, worker, reviewer, senior, implementation run, or target-system acceptance test was executed here. Those evidence needs belong to the future delivery requirements, not the TRD approval gate.

## In scope

- The required Task intake, real manager topology, engineering context, subtask decomposition and category behaviors, role selection and persistence, identity guarantees, current-version review and synthesis, conditional implementation, durable state ownership, safe stopping, and integrated verification described by this baseline.
- Reusable common contracts and support in the appropriate depot collections; the explicit Template mapping and initialization paths; and a reviewed adoption into the active Sys4AI root preserving its depot and intake specializations.
- Preservation of existing role and Task provenance through any separately authorized transition, without fixing a particular schema number or migration command before planning.
- For the present capture operation, one new canonical root TRD and its helper-generated `TRDs/INDEX.md` entry. The older orchestration TRD and other Task, plan, and TRD records retain their identities and content.

## Out of scope

- Implementing these requirements, preparing a downstream implementation plan, launching or testing a native agent team, creating roles or Tasks, or migrating existing records during this to-trd operation.
- Adoption into other ordinary product projects; bulk synchronization or overwrite authority derived from registration, matching filenames, historical equality, or shared directory ancestry.
- Git commits, pushes, branches, PRs, publication, deployment, external messages, installations, service provisioning, credentials, or user-configuration changes without their own authority.
- Automatic execution on TRD or plan approval; merged lifecycle state across documents, Tasks, native goals, conversations, Git, or releases; automatic background aging or monitoring.
- A replacement orchestration platform, mandatory memory/ontology service, a larger model for senior roles, fixed product-domain assumptions, forced consensus, or completion claims based only on changed instructions or child reports.

## Task requirements

### REQ-001 - One authorized intake route

- Requirement: The explicitly activated Task entry point shall accept a prompt, a supplied file, or an authorized handoff from another skill and route equivalent objectives through the same task-management workflow.
- Source: S01 TM-01 and sections 5.1-5.3; U01.
- Acceptance: Equivalent prompt, file, and skill inputs retain the same objective, deliverables, acceptance criteria, constraints, source references, project root, and action-authority boundary.
- Acceptance: An upstream handoff retains any supplied document or plan ID and its inspected revision or digest. Merely opening or approving a document does not start execution.
- Depends on: None.

### REQ-002 - Launch a real task manager

- Requirement: Task execution shall launch a real native Project Director agent in task-manager mode, or reconnect the confirmed designated manager for the same live Task execution.
- Source: S01 TM-02, TM-23 and sections 1.1, 4.1-4.2; this is a target change to G02 and G03.
- Acceptance: A native runtime receipt identifies the manager as an agent instance distinct from the calling host; relabeling the host does not satisfy the requirement.
- Acceptance: The calling host relays user input and results after handoff without concurrently performing the same manager responsibilities. Repeated intake for the same live execution does not create a competing manager.
- Depends on: REQ-001

### REQ-003 - Retain Director and systems-engineering responsibilities

- Requirement: The task manager shall apply the owning project's Project Director responsibilities and establish the engineering context needed to direct the requested work.
- Source: S01 TM-03 and section 4.3; G01-G02.
- Acceptance: Before decomposition, its inspectable context identifies the owning project, relevant architecture and interfaces, state ownership, dependencies, constraints, protected behavior, change impact, risks, and verification needs.
- Acceptance: The applicable local guidance and relevant project artifacts support that context. The manager retains scope, role selection, coordination, acceptance, integration, and final verification responsibility.
- Depends on: REQ-002

### REQ-004 - Decompose into bounded coordinated subtasks

- Requirement: The manager shall decompose the main objective into bounded, traceable subtasks and coordinate them according to their actual dependencies.
- Source: S01 TM-04 and sections 6.1, 12.3.
- Acceptance: Each executable subtask identifies its objective, requirement links, inputs, dependencies, deliverable, accountable assignment, allowed reads and writes, protected scope, acceptance criteria, and stopping condition.
- Acceptance: Missing dependency targets and dependency cycles prevent dependent execution. A small objective may use one generic subtask; mixed-category tasks retain main-task integration checks.
- Depends on: REQ-003

### REQ-005 - Classify every executable subtask

- Requirement: Each executable subtask shall have exactly one category: `generic`, `complex`, or `extra-complex`, selected with a concise task-specific rationale.
- Source: S01 TM-05 and sections 6.2-6.3.
- Acceptance: No runnable subtask is uncategorized or substitutes `direct`, `decomposed`, or `adversarial` for the required category. Decomposition and category selection remain separate decisions.
- Acceptance: Reclassification records the changed evidence and applicable gates. It cannot silently bypass failed review, reduce a required team because of capacity, or split an inseparable decision solely to evade review.
- Depends on: REQ-004

### REQ-006 - Execute generic work with one worker

- Requirement: A generic subtask shall use one active accountable execution sub-agent that performs the bounded work, including any implementation already required and authorized.
- Source: S01 TM-06 and section 8.1.
- Acceptance: One worker returns its deliverables, actual changes, proportionate checks, evidence, and limitations to the manager. The category adds no solver panel, reviewer agent, senior synthesizer, or separate implementation child.
- Acceptance: Targeted corrections return to the responsible worker. Replacement after failure records revocation of the previous ownership before assigning a replacement; the manager directly verifies the result.
- Depends on: REQ-005, REQ-019, REQ-021

### REQ-007 - Develop independent solutions for multi-solution work

- Requirement: Complex and extra-complex subtasks shall use at least two distinct solver agents addressing the same complete bounded problem from related but meaningfully different role perspectives.
- Source: S01 TM-07, sections 1, 7.1, 8.2-8.4 and 10.2.
- Acceptance: All planned solvers receive the same versioned problem baseline and success criteria, with documented role differences. Two is a minimum, not a fixed required team size.
- Acceptance: Initial candidate development excludes sibling drafts, including for queued solvers. Separate candidate artifacts identify each contribution; competing solvers do not implement conflicting production changes in the shared worktree.
- Acceptance: A missing required candidate blocks collection. A runtime that cannot preserve the required independence reports the limitation instead of claiming independent development.
- Depends on: REQ-005, REQ-019, REQ-021

### REQ-008 - Assign a distinct senior synthesizer

- Requirement: Every multi-solution subtask shall send its eligible candidate set to one distinct senior sub-agent with suitable domain and synthesis competence.
- Source: S01 TM-08 and sections 8.2-8.3.
- Acceptance: The senior is a distinct runtime instance from the manager and solvers; for extra-complex work it is also distinct from the assigned reviewers.
- Acceptance: The senior receives every required current candidate, relevant evidence, limitations, and applicable review findings. Complex work has no mandatory per-candidate reviewer stage; extra-complex eligibility follows REQ-014.
- Depends on: REQ-007, REQ-019, REQ-021

### REQ-009 - Fuse compatible contributions into a coherent solution

- Requirement: The senior shall integrate compatible candidate contributions into one coherent proposal with traceable treatment of material differences.
- Source: S01 TM-09 and sections 9.3, 9.5.
- Acceptance: The proposal identifies its current source candidates, retained contributions, justified omissions, resolved differences, assumptions, interfaces, requirement coverage, residual risks, and verification approach.
- Acceptance: The result contains no unresolved mutually exclusive core commitments. Concatenation, majority vote, an unexplained preferred candidate, or an unsupported endorsement does not satisfy fusion.
- Depends on: REQ-008, REQ-026

### REQ-010 - Return unresolved opposition with a shared explanation

- Requirement: When candidate commitments cannot coherently coexist, the senior shall identify the conflict and the manager shall return the same shared explanation to all originating solvers.
- Source: S01 TM-10 and sections 8.2, 9.3-9.4.
- Acceptance: The conflict identifies the synthesis round, common problem baseline, candidate versions, incompatible claims, affected requirements, supporting evidence, and required resolution.
- Acceptance: All solver assignments receive the same shared explanation; any role-specific action notes are separate. An opposing core commitment is not discarded merely to declare a winner.
- Depends on: REQ-008, REQ-026

### REQ-011 - Repeat solution and synthesis cycles with current evidence

- Requirement: The solver-senior cycle shall repeat when a targeted revision or new evidence can resolve an identified conflict.
- Source: S01 TM-11 and sections 9.4, 9.6; G02-G03 progress rules.
- Acceptance: Affected originating solvers return materially revised candidates or resolving evidence. An unaffected solver may return a versioned revalidation explaining compatibility.
- Acceptance: The next synthesis uses a consistent current candidate set and problem baseline. Repeated unchanged failure or exhausted authorized resources produces an honest non-complete state, never forced acceptance.
- Depends on: REQ-010, REQ-025, REQ-031

### REQ-012 - Assign one distinct reviewer to every extra-complex solver

- Requirement: Every extra-complex solver shall have its own independently assigned reviewer agent.
- Source: S01 TM-12 and section 8.3.
- Acceptance: The solver-to-reviewer mapping is one-to-one. Self-review and a single reviewer instance shared among solvers are rejected.
- Acceptance: Reviewer role definitions may be reused when suitable, while reviewer runtime instances remain distinct. The assigned reviewer evaluates its own solver's current candidate against the common criteria.
- Depends on: REQ-007, REQ-019, REQ-021

### REQ-013 - Revise rejected candidates through their reviewers

- Requirement: An extra-complex reviewer shall return evidenced, actionable findings to its assigned solver and review the resulting current candidate again when correction is needed.
- Source: S01 TM-13 and sections 8.3, 9.2.
- Acceptance: A rejection identifies failed criteria, evidence, and required changes, distinguishing mandatory defects from optional improvements.
- Acceptance: The originating solver returns a new candidate version and a response to findings. A rejected candidate cannot become passed through a manager override or without current review of the revision.
- Acceptance: The same reviewer assignment continues while its runtime session remains available; any necessary replacement preserves the mapping and review history.
- Depends on: REQ-012, REQ-025

### REQ-014 - Require all current review passes before extra-complex synthesis

- Requirement: Extra-complex synthesis shall begin only after every required current candidate has a valid pass from its assigned reviewer for the current problem baseline.
- Source: S01 TM-14 and section 8.3.
- Acceptance: Any missing, rejected, blocked, or stale review prevents synthesis. A pass on an earlier version does not admit a changed candidate.
- Acceptance: The synthesis input set corresponds exactly to the eligible reviewed versions.
- Depends on: REQ-012, REQ-013, REQ-025

### REQ-015 - Reapply review after extra-complex synthesis conflicts

- Requirement: An extra-complex synthesis conflict shall return through the originating solver-reviewer process before another synthesis attempt.
- Source: S01 TM-15 and sections 8.3, 9.4.
- Acceptance: The shared conflict reaches all solvers; revised or revalidated current candidates receive their associated reviewers' current attestations under the updated context.
- Acceptance: No conflict revision bypasses REQ-014 or retains a pass invalidated by a material baseline change.
- Depends on: REQ-010, REQ-013, REQ-014

### REQ-016 - Return synthesis to the manager for acceptance

- Requirement: The senior shall return the fused solution and its evidence to the task manager, which alone decides acceptance against the subtask and project criteria.
- Source: S01 TM-16 and sections 1.1, 8.2, 9.5.
- Acceptance: The manager records acceptance of the exact current proposal, requests a bounded correction, or records a specific blocker.
- Acceptance: The senior cannot authorize implementation, change the user's scope, or close the Task. There is no additional senior layer implied by wording in the source handoff.
- Depends on: REQ-008, REQ-025, REQ-026

### REQ-017 - Use one dedicated implementation child when required

- Requirement: When an accepted complex or extra-complex solution requires performed implementation and that work is authorized, the manager shall assign exactly one dedicated implementation sub-agent to that solution.
- Source: S01 TM-17 and sections 1.1, 8.5.
- Acceptance: The implementation instance is distinct from the manager, solvers, reviewers, and senior, with one active owner for the accepted solution and an exact scope, protected state, checks, evidence, and stopping condition.
- Acceptance: An analysis or recommendation objective that is already satisfied by the accepted deliverable creates no unnecessary implementation child; a coding objective is not complete on a design alone.
- Acceptance: A material design defect returns to the manager for a bounded decision or reopened solution cycle. The implementer does not silently replace the accepted design; changed acceptance binds to the revised solution.
- Depends on: REQ-016, REQ-021, REQ-032

### REQ-018 - Persist project-local roles and an accurate index

- Requirement: Active role definitions shall reside in the owning project's root `roles/` directory with a persisted `roles/INDEX.md`, while the paired `AGENTS.md` and `ROLE.md` files remain authoritative role definitions.
- Source: S01 TM-18 and sections 7.1-7.3; G04 for preserved bundle constraints. Index-generation mechanics remain proposal P02.
- Acceptance: The index resolves to current valid role bundles and exposes relevant invalid-role diagnostics. A missing, stale, or misleading entry cannot make a missing or invalid bundle eligible.
- Acceptance: The existing paired-file format, valid role metadata and links, safe names, path confinement, and overwrite protections remain supported. New installations discover active roles under `roles/`, with any legacy lookup limited to explicit transition or diagnostics.
- Depends on: None.

### REQ-019 - Select a suitable existing role before creating one

- Requirement: The manager shall use a fresh filesystem-backed role catalog and a function-specific fit assessment before every role-based assignment, selecting the narrowest suitable valid existing definition when one fits.
- Source: S01 TM-19 and section 7.4; G01-G02 and G04.
- Acceptance: Manager, generic worker, solver, reviewer, senior, and implementer selection records identify the objective, domain capabilities, reads and writes, deliverable, tools and skills, authority, risk, stopping condition, selected role, both file paths, inspected revision or digests, and fit rationale.
- Acceptance: Role content is read and applied by the assigned agent. An unsuitable or invalid role is not accepted solely because it exists; a tool, permission, dependency, or runtime gap is reported separately from a role gap.
- Depends on: REQ-018

### REQ-020 - Create and persist roles for demonstrated gaps

- Requirement: When no suitable valid role definition exists and the gap is a reusable role responsibility, the manager shall create and persist a fitting definition within the owning project's authorized role scope and update its index before assignment.
- Source: S01 TM-20 and section 7.4; G01-G02 reusable-source and adoption boundaries.
- Acceptance: Fresh inventory and fit evidence precede creation. The new paired-file bundle validates, appears accurately in the index, and is available for later tasks before an agent uses it.
- Acceptance: Creation preserves unrelated files and reusable-source ownership. It does not invent unavailable capabilities, duplicate a suitable role, or treat a missing tool or permission as a role-definition gap.
- Acceptance: A partial publication identifies the committed bundle and remaining index recovery without duplicate creation or deletion of valid work.
- Depends on: REQ-018, REQ-019

### REQ-021 - Preserve exact model and reasoning identity

- Requirement: Every team agent shall use the task manager's exact effective AI model identity and reasoning level; role seniority shall not change either value.
- Source: S01 TM-21 and section 10; G01-G02 and G04 parity requirements.
- Acceptance: Runtime-provided evidence or a named verified runtime inheritance guarantee establishes parity for each assignment. Prompt assertions and unverified aliases alone are insufficient.
- Acceptance: The workflow distinguishes direct observed identity matches, verified inheritance-contract evidence, and unverified settings. Known mismatches or insufficient guarantees prevent compliant dispatch.
- Acceptance: Model identity and context provision are checked separately. A user-requested mid-run model or reasoning change reconciles the active team before further assignments under the new identity; no automatic downgrade or user-configuration rewrite supplies an exception.
- Depends on: None.

### REQ-022 - Adapt to the owning project

- Requirement: The common workflow shall adapt to different projects and task domains by loading applicable local instructions, constraints, interfaces, and appropriate role definitions.
- Source: S01 TM-22 and sections 4.3, 5.2, 13-14; G01-G02 and G05.
- Acceptance: Common orchestration does not hard-code a product domain or copy depot-only registration authority into ordinary product Directors.
- Acceptance: A clean temporary project created from the designated Template receives usable current starter contracts and roles without copied live Task history, coordinator assignments, native agent IDs, or execution state.
- Depends on: None.

### REQ-023 - Maintain one manager and one canonical writer

- Requirement: Each Task execution shall have exactly one designated active manager and one authoritative canonical Task-state writer, with a bounded bootstrap-to-manager handoff.
- Source: S01 TM-23 and sections 4.1-4.2, 11.5; G03 canonical-state protection.
- Acceptance: Duplicate intake, stale manager results, competing writers, and replacement attempts cannot create competing accepted ownership or duplicate work. Live matching execution identity is checked before reconnection.
- Acceptance: The host's bootstrap write authority ends at handoff. Ordinary workers, reviewers, and seniors do not mutate canonical Task state, final Task Responses, or role indexes or promote themselves to manager by reading root guidance.
- Acceptance: Replacement reconciles outstanding agents and explicitly revokes the previous assignment. A claimed actor field or role prose is not described as operating-system authentication or filesystem isolation.
- Depends on: REQ-002

### REQ-024 - Keep orchestration identities and provenance distinct

- Requirement: Roles, runtime agent instances, Task executions, subtasks, problem baselines, candidates, reviews, conflicts, synthesis outputs, and implementation assignments shall be separately attributable through stable identities and current references.
- Source: S01 TM-24 and sections 9.1, 11.2-11.5.
- Acceptance: Each accepted artifact or result resolves to its Task, subtask, responsible runtime instance, selected role revision, input baseline, and artifact version or digest as applicable.
- Acceptance: Actual native IDs originate in tool receipts. Role names, subtask IDs, conversation IDs, placeholders, or child success text cannot substitute for runtime identity or completed work.
- Acceptance: Duplicate, stale, or out-of-order results are identifiable and cannot repeat an already accepted transition; historical results retain their attribution.
- Depends on: None.

### REQ-025 - Bind reviews and acceptance to exact current versions

- Requirement: Reviews, synthesis eligibility, manager acceptance, and implementation targets shall bind to the exact candidate artifacts and material problem baseline they evaluated.
- Source: S01 TM-25 and sections 6.3, 8.5, 9.4, 11.3-11.5.
- Acceptance: A change to candidate bytes invalidates a dependent pass even if its filename and title remain unchanged.
- Acceptance: A material input, requirement, or problem-baseline change invalidates dependent review or acceptance until current evidence establishes eligibility again; stale records remain history.
- Acceptance: A synthesis uses a mutually consistent current candidate set, and implementation identifies the exact manager-accepted current solution.
- Depends on: REQ-024

### REQ-026 - Distinguish reconcilable differences from contradictions

- Requirement: The synthesis process shall classify and resolve material differences without accepting unresolved contradictory requirements or core commitments.
- Source: S01 TM-26 and section 9.3.
- Acceptance: Complementary contributions, terminology differences, scope alternatives, evidence disagreements, and mutually exclusive commitments receive an explicit evidence-based disposition.
- Acceptance: A coherent result has consistent assumptions, compatible interfaces, non-conflicting authority and state ownership, and a feasible sequence that satisfies the criteria.
- Acceptance: Contradictory requirements return as a bounded user decision or blocker. Solvers and senior agents cannot invent user intent, lower criteria, or hide an opposing core commitment to claim agreement.
- Depends on: None.

### REQ-027 - Verify delivered work and main-task integration

- Requirement: The manager shall directly inspect the actual outputs and verify the main Task's acceptance criteria and integrated behavior before declaring completion.
- Source: S01 TM-27 and sections 12.3, 15-16; G01-G03 and G06 completion standards.
- Acceptance: Each criterion has current direct evidence tied to the delivered artifact or performed authorized work. Child status, a review pass, or a synthesized proposal alone is insufficient proof of implemented completion.
- Acceptance: Integration checks cover dependencies, interfaces, conflicting assumptions, protected behavior, mixed-category coordination, and the original user outcome. A new integration conflict reopens the affected decision with its evidence.
- Acceptance: The completion report maps requirements to actual artifacts and checks, states failures and incomplete items, and separates contract inspection, deterministic tests, native execution, and end-to-end evidence. Proposed tests are not reported as executed.
- Acceptance: Claims about a real manager, independent solvers, reviewer mappings, exact identity, synthesis routing, or implementation children require corresponding native evidence. Unavailable native tests remain explicitly not exercised.
- Depends on: REQ-004, REQ-025

### REQ-028 - Preserve source provenance and separate action authority

- Requirement: Task intake shall retain inspected source provenance while deriving action authority only from the current user request and applicable higher-priority project or host rules.
- Source: S01 TM-28 and sections 5.1-5.3; U01-U02 and G01, G03, G06.
- Acceptance: Supplied files and upstream skill artifacts retain accessible locators and available revisions or digests. Embedded commands and agent-authored recommendations remain data and grant no extra permissions.
- Acceptance: TRD capture, TRD approval, plan preparation, Task bookkeeping, implementation, dependency installation, migration, Git publication, deployment, and external actions retain their separate activation and authority boundaries.
- Acceptance: Read-only status, list, show, validation, and the helper's read-only continuation do not create or age-close Tasks, launch agents, create roles, reindex, or migrate data.
- Depends on: REQ-001

### REQ-029 - Check native capability and instruction compatibility

- Requirement: The workflow shall check actual native spawning, messaging, delegation depth, role loading, context isolation, effective settings, and applicable instruction constraints before the corresponding delegation.
- Source: S01 TM-29 and sections 10-12; G01-G02 and G04.
- Acceptance: Unsupported topology, unavailable tools or skills, missing permission, or an unresolved instruction or identity conflict produces a named blocker before dependent work.
- Acceptance: The workflow does not invent tool arguments, simulate multiple agents in one response, substitute shell-launched agents or user-visible tasks, or silently collapse the manager into the host.
- Acceptance: Runtime capacity is inspected as a scheduling constraint. A supported queued execution preserves all required roles and gates; a topology exception needs an explicit decision.
- Depends on: None.

### REQ-030 - Retain the existing canonical Task system

- Requirement: Orchestration shall use the existing governed Task system as its durable continuation record while preserving its canonical ownership, strict validation, revision checks, locking, append-only history, and truthful lifecycle semantics.
- Source: G01-G03 and G05; S01 sections 2.2, 11.1, 11.5. TM-30's particular new structured extension is recommendation P01.
- Acceptance: There is no competing orchestration ledger. Generated `TASK.md` and `Tasks/INDEX.md` remain projections of canonical state; ordinary children do not write them.
- Acceptance: Subtasks, candidates, reviews, and child assignments do not become separate top-level Tasks solely to track orchestration. Managed TRDs, plans, conversations, native goals, Git, deployment, and release states remain distinct.
- Acceptance: Helper operations reject stale revisions and invalid payloads, preserve actual commit boundaries, and report partial publication with exact recovery. No fabricated cross-system atomicity or exactly-once native-launch guarantee is claimed.
- Acceptance: Durable records contain concise decisions and necessary evidence, not hidden reasoning, full transcripts, credentials, secrets, or large raw logs.
- Depends on: None.

### REQ-031 - Continue loops only with meaningful progress

- Requirement: Review, conflict, synthesis, and implementation loops shall continue only when the next cycle offers a targeted change, material new evidence, or a new hypothesis within available authorized resources.
- Source: G02 progress gate and G06 persistence rules; S01 TM-32 and section 9.6. Numeric checkpoints remain recommendation P03.
- Acceptance: Repeated unchanged failure, irreducible conflict, missing capability or authority, and exhausted resources preserve current artifacts and produce an explicit non-complete blocker or required decision.
- Acceptance: Resource pressure does not auto-pass a candidate, remove a required solver or reviewer, lower acceptance criteria, or change model or reasoning settings.
- Acceptance: Optional improvements do not extend review indefinitely after mandatory criteria are met.
- Depends on: None.

### REQ-032 - Respect runtime capacity and write ownership

- Requirement: Parallel assignments shall fit the actual native runtime capacity and have non-overlapping authorized write ownership; conflicting writes shall be serialized.
- Source: G01-G02 parallel-work rules; S01 TM-33 and sections 8.4-8.5.
- Acceptance: No two active assignments own the same accepted solution implementation or overlapping write scope. Solver candidates have distinct protected artifact ownership.
- Acceptance: Queued execution retains the required logical agent instances, role distinctions, candidate independence, review gates, and exact identity. No fixed concurrency number or simultaneous full-team launch is required.
- Depends on: None.

### REQ-033 - Preserve existing roles and Task history during transition

- Requirement: The transition to the revised role layout and any necessary Task storage changes shall preserve existing role provenance, stable Task identities, historical meaning, append-only responses, and unrelated work.
- Source: G01-G03 and G06 preservation and migration authority; S01 TM-34, sections 7.5, 11.1 and 14.
- Acceptance: Existing valid roles remain recoverable and attributable after transition, with unchanged content retained where semantics are unchanged. Historical path references and completed records are not rewritten to simulate new behavior.
- Acceptance: Conflicting old and new role destinations are identified before overwrite. Read-only inspection does not migrate; any migration write requires explicit authority and exact reviewed scope.
- Acceptance: Unsupported record versions or interrupted transitions fail safely with a documented recovery route. No old summary is used to invent live manager or child identities.
- Depends on: None.

### REQ-034 - Deliver to the confirmed Sys4AI destinations

- Requirement: The target change shall cover reusable depot sources, the designated `Projects/Sys4AI-Template-Project/`, and the active Sys4AI depot root, while excluding adoption into other product projects.
- Source: U02 explicit destination-scope answer; G01 and G05; S01 TM-35 and sections 13-14.
- Acceptance: Reusable additions, modifications, and deletions originate in the appropriate `SKILLS-depo/`, `ROLES-depo/`, `AGENTS-depo/`, `SOULS-depo/`, or `SPECS-depo/` source collection as applicable. The explicit mappings and checked update workflow produce the designated Template.
- Acceptance: The active root receives a separately reviewed local adoption that reconciles the changed manager, taxonomy, role path, state-writer, and implementation-owner contracts while preserving its depot responsibilities and unrelated edits.
- Acceptance: Template mappings and initialization produce the new role layout and current common workflow in a temporary new project, with destination-appropriate role-index validation.
- Acceptance: Each selected destination has relevant checks and preservation evidence. Registration does not authorize propagation into any other project; the registry remains factual and unselected project files remain untouched.
- Depends on: REQ-018, REQ-022

### REQ-035 - Account for outstanding agents when work stops or transfers

- Requirement: Pausing, cancellation, failure recovery, manager replacement, and model-setting changes shall account for outstanding native assignments and their write ownership before dependent dispatch or a final stopped-state claim.
- Source: G02 supervision, ownership and stopping rules; G06 authority and truthful reporting; S01 TM-36 and sections 4.2, 10.3, 12.1-12.2. Detailed recovery protocol remains recommendation P07.
- Acceptance: New dispatch stops when the controlling action requires it; applicable interruption is requested, actual runtime status and known changes are reconciled, and any uncontained or unconfirmed worker is reported explicitly.
- Acceptance: A stopped or cancelled execution is not labeled completed. An old timestamp or expired observation alone does not prove that a manager or worker has stopped.
- Acceptance: Replacement does not duplicate a still-active owner. Native launch or receipt uncertainty is reconciled against the original assignment before retrying.
- Depends on: REQ-023, REQ-032

### REQ-036 - Preserve intentional intake and lifecycle policies

- Requirement: Adopting the common orchestration contract shall preserve the active root's existing explicit Task activation, matching and creation behavior, 30-day intake-triggered inactivity policy, and distinct `close-old-task` meaning.
- Source: G01 and G03; S01 sections 2.1 F12, 5.2 and 12.2; U02 preservation boundary.
- Acceptance: Explicit work intake reuses a clearly matching active Task or creates one as the established root contract specifies. Completed history does not become a substitute for a new objective.
- Acceptance: Read-only and unrelated requests do not run aging or create Tasks. Eligible age closure remains distinct from completion and preserves unfinished criteria and history.
- Acceptance: Known active manager or unresolved write-owning worker state is reconciled before inactivity closure. No scheduled background process is added, and intentional source/template versus root intake differences remain documented.
- Depends on: REQ-028, REQ-030, REQ-035

### REQ-037 - Extend the existing helper architecture proportionately

- Requirement: The target shall extend the existing Task and role system using the project's Python standard-library helper architecture and native agent workflow, preserving their separate responsibilities.
- Source: S01 decision summary and sections 11.1, 13, 16; G05 dependency specifications.
- Acceptance: Deterministic storage and validation stay within the existing helper architecture; actual agent spawning and messaging use available native agent tools through the agent or skill workflow.
- Acceptance: The change does not introduce a replacement general-purpose agent framework, database or queue service, mandatory memory or ontology backend, new model provider, or production dependency solely to implement orchestration.
- Acceptance: Proposed module names, CLI operations, packet fields, and schema numbers are checked against the live implementation and documented through separately authorized planning; illustrative payloads are never treated as already-supported APIs.
- Depends on: REQ-030

## Decisions

D01: The user's scope answer selects reusable depot sources, the designated Template, and the active root as target destinations, while excluding other product projects. REQ-034 and every scope statement use this answer. Document approval remains separate from actual source edits, Template adoption, root adoption, migration, execution, or publication.

D02: The source's topology distinctions are preserved. A spawned manager is a real native instance; the senior returns to that manager; generic work uses its own worker for authorized implementation; complex and extra-complex work use a distinct implementation child only when performed changes are needed. A small main task may contain one generic subtask. At least two solvers are required for either multi-solution category, without fixing the team to two or requiring simultaneous execution.

D03: Root governance remains in force for this document-only operation. A future implementation must reconcile the old root-only coordinator, execution categories, role-index prohibition, full-transcript guidance where it conflicts with candidate independence, and Director/senior implementation-owner restriction across the selected active contracts. Reading this TRD does not itself make any of those replacements effective.

D04: The source's proposed mechanisms are constrained planning choices, not missing user intent. A later separately activated planning workflow can choose exact schema versions, CLI names, internal APIs, module boundaries, packet fields, artifact layout, locking and recovery mechanisms, and capability-check implementation within the requirements. No such choice can change required topology, identity, authority, acceptance, preservation, or target scope.

| Proposal | Source item and retained recommendation | Binding boundary and disposition |
| --- | --- | --- |
| P01 | TM-30; sections 11 and 13: add a versioned structured orchestration extension, immutable referenced artifacts, typed internal events, and deterministic transition validation through the existing Task helper. | The existing one-ledger and helper protections are required by REQ-030 and REQ-037; identity and current-version behavior are required by REQ-023 through REQ-025. The exact new schema, event kinds, packet shapes, storage layout, and module/command names are recommendations for planning. The illustrative schema number `2` is not reserved or assumed available. |
| P02 | TM-31; section 7.3: generate `roles/INDEX.md` deterministically from validated bundles, report drift, and provide explicit reindex and partial-publication recovery. | Accurate persisted navigation, authoritative role bundles, fresh validation, and safe creation are required by REQ-018 through REQ-020. Generation, fingerprint shape, lock strategy, and Template-index publication mechanics remain recommended implementation choices. The index cannot become a competing role-definition authority. |
| P03 | TM-32; section 9.6: establish resource checkpoints, with three revision or synthesis attempts suggested as an initial checkpoint. | Meaningful progress and truthful stopping already follow G02/G06 and REQ-031. The numeric checkpoint is a proposal, not a fixed retry limit, automatic failure threshold, or permission to lower criteria. |
| P04 | TM-33; sections 8.4-8.5: queue the logical team within live capacity and serialize shared implementation. | REQ-032 retains required non-overlapping writes and observed capacity. Serializing all implementation across otherwise independent subtasks and reusing an already dedicated implementer for later compatible assignments are optional scheduling choices; the distinct-agent and one-owner rules remain mandatory. |
| P05 | TM-34; sections 7.5 and 14: use previewable migration, reviewed recovery copies, old-to-new role mapping, and checked state upgrades. | Preservation, explicit migration authority, and safe failure are required by REQ-033. Exact migration commands, archive or mapping layout, and schema-upgrade mechanics remain proposals. Existing historical records are not edited during capture. |
| P06 | TM-35; sections 13-14: propagate through sources, Template generation, initialization, and selected installed copies. | U02 explicitly settles the destination selection in REQ-034. The source's file-by-file edit map and implementation phases are recommendations, not an approved implementation plan or overwrite manifest. Only affected files in the confirmed destinations may enter later scoped adoption. |
| P07 | TM-36; sections 4.2, 10.3 and 12: account for live assignments on pause, cancellation, recovery, and replacement. | REQ-023, REQ-035, and REQ-036 preserve the required one-owner, authority, truthful-stopping, and intake boundaries. Epoch names, receipt publication sequence, actor fields, and exact recovery transitions remain implementation recommendations. Shared-filesystem protocol checks are not represented as a malicious-process security boundary. |

D05: Suggested role names such as `task-manager`, `systems-solution-designer`, `failure-analysis-solver`, `solution-reviewer`, `senior-solution-synthesizer`, and `solution-implementer` are examples. The baseline requires suitable persisted definitions and distinct assignment functions, not immediate creation of that named roster. A valid base role may support distinct documented solver specializations when its real capabilities and authority fit; cosmetic agent naming does not supply different perspectives.

D06: Native support and model/context inheritance are future verification obligations. They do not block completion of a requirements document whose required behavior is settled. An implementation that cannot establish the specified topology, independence, or identity must report the exact unmet requirement and evidence; it may not silently substitute an easier workflow. No fixed model identifier or hidden runtime assumption is accepted here.

D07: S01 AT-01 through AT-53 are proposed acceptance scenarios. They inform the observable criteria above and remain planned evidence. Later delivery can choose the smallest adequate checks, but contract inspection and deterministic fixtures cannot substantiate unobserved native or end-to-end behavior. Requirement coverage must work in both directions, without changing historical records or weakening tests simply to obtain a pass.

The source-requirement trace is direct: TM-01 through TM-29 correspond to REQ-001 through REQ-029. P01-P07 account for TM-30 through TM-36. REQ-030 through REQ-033 and REQ-035 through REQ-037 preserve identified live governance constraints and their necessary application to the new workflow; REQ-034 implements the explicit scope clarification. This baseline contains no approval of S01's exact implementation design.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
