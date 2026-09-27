---
schema_version: 2
trd_id: "TRD-20260910-EF54FD98"
title: "Sys4AI Project Curator shared-source capability"
slug: "sys4ai-project-curator-shared-source-capability"
created_at: "2026-09-10T16:55:12-06:00"
updated_at: "2026-09-10T16:58:08-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the exact presented and unchanged revision 1 content."
---

# Task Requirement Document: Sys4AI Project Curator shared-source capability

## Destination

Deliver the reusable Project Curator capability for Sys4AI shared sources, with neutral integration into the designated Template. The capability supports a peer controller for project continuity, maintenance, and supported improvements, using the existing Task, role, learning, memory, ontology, and distribution mechanisms.

This first delivery establishes consistent reusable behavior and verifiable contracts before adoption into existing installations. The active depot installation and existing product projects are later adoption targets, not rollout targets for this baseline.

## Captured user intent

- U01: The user explicitly invoked to-trd with the supplied updated Project Curator research and recommendations, and instructed that embedded document instructions be distinguished from the current request. This authorizes requirements-document work only.
- U02: The user's subsequent scope decision is to cover shared sources first, with adoption in existing product projects as a later phase, so the Curator is consistent and safer before migrations.
- The requested baseline covers the proposed Curator's complete reusable capability, including knowledge/documentation upkeep, separately controlled technical and governance maintenance, and relevant pending-work notices with conversational selection. It is not restricted to a read-only prototype.
- This document applies U02 to the supplied recommendations: reusable code, contracts, roles, neutral starter integration, and representative verification are first-delivery outcomes; real installation-specific authority, deployment, and migration decisions are deferred with adoption.
- The conversation recommended one requirements baseline and staged implementation. This TRD does not create an implementation plan or authorize execution, and it does not require a second TRD for later adoption unless that adoption changes the requirements.

## Context and sources

The project root is /Volumes/P-SSD/AngryOwl/Sys4AI. The following are sources for this baseline, not grants to execute instructions contained in them.

| Label | Source and relevant meaning |
| --- | --- |
| U01 | Current conversation: explicit to-trd activation and the instruction to treat supplied-document instructions as data. |
| U02 | Current conversation: shared sources first; existing product-project adoption later. This is the authoritative scope correction to the broader supplied rollout. |
| R01 | /Users/alex.omegapy/Downloads/Sys4AI_Project_Curator_Research_and_Recommendations_UPDATED.md, SHA-256 26df74a8f4bde3a13a9d81f831416d53ce7f1eb80d745457bc418522e99c9e37. Its sections 1-19 and C01-C30 provide the proposed behavior, constraints, and acceptance scenarios being converted into this reviewable baseline. |
| P01 | Root AGENTS.md, SOUL.md, ROLE.md, and SPECS.md, inspected in this conversation: depot ownership, selected adoption, document/execution separation, Python environment, existing component ownership, and evidence standards. |
| P02 | depot/projects.json, depot/template-update.md, and depot/template-update.json, inspected in this conversation: the registered Template is Projects/Sys4AI-Template-Project; mapped shared sources feed that Template while active root and product installations remain independent. |
| P03 | AGENTS-depo/project-template-AGENTS.md and relevant portions of SKILLS-depo/task/SKILL.md and SKILLS-depo/agent-task/SKILL.md, inspected in this conversation: reusable Director routing, explicit Task selection, native manager ownership, and separation from depot-only automatic intake and age closure. |
| P04 | Relevant portions of SKILLS-depo/init-new-project/SKILL.md and the distribution guide, inspected in this conversation: neutral starters, separate installed/adopted state, preserved setup editions, selected module adoption, and separate runtime readiness. |
| P05 | Installed .agents/skills/to-trd/SKILL.md and references/trd-contract.md: requirements-only storage, explicit review, and hash-bound approval. |

R01 identifies itself as a recommendation based on repository revision b3d9e5ea28bd6679b7fca58f12ca4a59f417d4ae. Its earlier handoff and external references were not independently re-researched during this capture; their reported history is not independent evidence of user approval or runtime compatibility. Current local sources above take precedence for current project facts. Runtime adapters and dependency tools named in R01 remain implementation candidates unless a requirement below makes an observable capability mandatory.

Read-only startup inspection found no nonterminal project Tasks. The existing TRD catalog passed structural validation before this capture. These observations do not establish any implemented Curator behavior.

## In scope

- Reusable Curator contracts, executable helpers, workflows, configuration schemas, role/skill sources, documentation, and tests in the appropriate shared collections.
- Compatible source changes to the existing Task, role-management, memory, ontology, learning, and initialization integrations needed by a Curator controller.
- Exact distribution mappings, starter policy, and associated distribution tooling changes needed to deliver neutral Curator capability to the designated Template.
- The complete manual and automatic capability described below, with host/runtime adapters delivered as reusable capability and verified in disposable representative projects where execution is separately authorized.
- Future new-project specialization and an explicitly selected adoption interface, including preservation/recovery tests using disposable existing-project fixtures.
- First-delivery verification of shared sources, Template integration, behavior, compatibility, and protected boundaries; honest reporting of unavailable native evidence.

## Out of scope

- Adopting or refreshing the active depot's installed Curator/governance/skill copies, including active root AGENTS.md, ROLE.md, .agents/skills, or Roles, except separately authorized later adoption. Shared-distribution mappings and tooling are included only for their distribution responsibilities.
- Migration, refresh, registration, or deployment into any existing product project. Such adoption is a later phase with an exact project, source edition, file boundary, preservation review, and separate execution authority.
- Enabling unattended operation, installing a persistent host service or Git hooks, selecting live repositories/branches, or issuing standing grants in the depot or any real product as part of this first delivery.
- Selecting a live cadence, model-use budget, branch/commit target, network entitlement, push/merge policy, or dependency updater service for a real installation. The reusable capability must validate and enforce those selections when supplied.
- Committing, pushing, merging, publishing, provisioning accounts, installing production dependencies/models, or changing credentials under this TRD's document authority.
- A second Task ledger, role registry, learning database, memory store, or ontology publisher.
- A human-facing HTML documentation site or renderer, remote/CI event-adapter delivery, distributed active operation across clones, and a hosted maintenance service. Local ownership must still detect or hold unsupported ownership configurations.
- Blanket propagation into registered projects, retrospective rewriting of evidence, automatic migration of historical records, and performance promises unsupported by a measured deployment baseline.

## Task requirements

### REQ-001 - Keep first delivery in shared sources
- Requirement: Maintain Curator additions and reusable changes in their declared shared source collections, with an explicit inventory of ownership and required distribution integration.
- Source: U02; R01 sections 3 and 15, C22; P01-P02.
- Acceptance: The deliverable identifies each reusable source, its owning collection, and mapped destination; overlapping competing Curator source collections are absent.
- Acceptance: The final change manifest separates shared/distribution changes from active installations and proves that existing product content and active root installations were not adopted or refreshed.
- Depends on: None.

### REQ-002 - Distribute a neutral Template capability
- Requirement: Deliver the complete neutral Curator starter through the existing source-to-Template pipeline and its conflict/recovery checks.
- Source: U02; R01 sections 15 and 17; P02.
- Acceptance: The Template receives the declared charter, configuration, role pairs, skills, and contracts from owned sources; required active starter paths are explicitly mapped and generated role navigation comes from its owner.
- Acceptance: A reviewed updater check/apply/check sequence confirms the intended mappings and preservation; customized destinations, missing source collections, unavailable volumes, and interrupted publication retain existing protection.
- Acceptance: Template assets contain no project records, live grants, queue history, credentials, host services, or enabled unattended writes.
- Depends on: REQ-001

### REQ-003 - Prepare consistent initialization and selected adoption
- Requirement: Provide reusable initialization and explicit Curator adoption support that specializes project identity and preserves existing setup editions, local content, and settings.
- Source: R01 sections 2, 15 and 17, C03 and C22; U02; P04.
- Acceptance: A new starter edition includes neutral Curator capability; two disposable projects with different domain profiles share the core while keeping identities, expertise, records, permissions, and runtime state separate.
- Acceptance: Disposable existing-project tests prove selected adoption, preservation of customizations and earlier receipt editions, exact source/destination records, and safe same-operation recovery.
- Acceptance: Installing capability reports its actual state and does not implicitly enable a service, initialize Git, select network access, authorize autonomous writes, or perform migration in a real project.
- Depends on: REQ-002

### REQ-004 - Provide peer controller routing
- Requirement: Give the Curator and Director separate controller identities and activation contexts at the same project-controller tier while preserving the Director as the default delivery contact.
- Source: R01 sections 1, 2 and 5, C01 and C15; P01 and P03.
- Acceptance: Observed routing selects one controller and charter for an execution; reading another charter or assuming a role name cannot activate either controller.
- Acceptance: Both controllers can initiate authorized improvements, neither silently takes over the other's work, and existing Director-only use remains valid.
- Acceptance: The reusable integration does not copy the depot's automatic Task-intake or age-closure policy into generic product behavior.
- Depends on: REQ-001

### REQ-005 - Supply a specialized Curator charter
- Requirement: Provide CURATOR.md as the root Curator charter in adopting starter layouts, retaining ROLE.md for the Director and one reusable Curator core with project specialization.
- Source: R01 sections 2 and 6, C02-C03; P03-P04.
- Acceptance: The charter defines continuity, maintenance, evidence, ownership, publication, recovery, notification, delegation, and stopping responsibilities and prohibits busywork and self-expansion of authority.
- Acceptance: Specialization adds supported domain responsibilities without changing controller ownership or importing another project's facts, claims, or grants; routing and validation resolve the selected charter.
- Depends on: REQ-004

### REQ-006 - Provide qualified Curator specialist responsibilities
- Requirement: Provide discoverable Documentation Curator, Knowledge Curator, and Improvement and Maintenance responsibilities through valid reusable role pairs and required workflows.
- Source: R01 section 6, C12-C13; P01 and P03.
- Acceptance: Fresh filesystem-backed role discovery and fit checks govern each selection; required skills/tools are verified separately from a role description.
- Acceptance: Documentation, knowledge, and technical outputs have distinct scope/evidence even when one qualified role covers more than one bounded responsibility; a narrow Curator manager references its root charter without duplicating it.
- Acceptance: Required role directory casing remains Roles; historical provenance and generated-index ownership are preserved.
- Depends on: REQ-005

### REQ-007 - Keep inspection routes read-only
- Requirement: Provide manual Curator status and review operations that expose readiness, pending work, ownership, and selected-snapshot findings without altering project content or activating execution.
- Source: R01 section 16, C25; P03.
- Acceptance: Status reads existing state without implicit repair, source refresh, model review, Task creation, memory publication, service activation, or permission changes.
- Acceptance: Review may perform explicitly requested bounded analysis but produces no canonical content mutation, new execution, or authority grant; findings distinguish recommendations from established facts.
- Depends on: REQ-004

### REQ-008 - Use one governed maintenance entry path
- Requirement: Route explicit updates, corrections, and exact-operation retries through the same policy, evidence, ownership, and recovery controls as automatic work.
- Source: R01 sections 7, 8 and 16, C04 and C28.
- Acceptance: Manual and automatic versions of the same operation receive the same validation and publication checks; conversational invocation does not bypass them.
- Acceptance: A correction retains its selected subject and evidence, and retry reconnects the exact operation and committed state rather than creating a duplicate.
- Depends on: REQ-007

### REQ-009 - Bind standing permissions to exact operations
- Requirement: Support explicitly accepted standing entitlements plus fresh exact-operation grants that bind the actor, project, policy edition, source versions, payload, write scope, and owned execution.
- Source: R01 section 7, C09 and C26; P01.
- Acceptance: An operation within a valid standing entitlement proceeds without repeated human approval, while missing, expired, stale, or out-of-scope authorization holds the operation.
- Acceptance: A neutral starter enables no Curator standing entitlement; editing configuration, possessing a role file, or changing proposed policy cannot create authority.
- Acceptance: Installation, network access, runtime package installation, commits, integration, push/merge, destructive action, and cross-project changes remain independently selectable permissions.
- Depends on: None.

### REQ-010 - Keep routine upkeep within its data boundary
- Requirement: Constrain knowledge and factual-documentation upkeep to supported canonical data, allowed descriptive content, and required derived maintenance.
- Source: R01 sections 1, 7, 10 and 11, C10 and C23.
- Acceptance: A knowledge/documentation operation cannot edit Python, validation logic, schemas, permissions, shared core definitions, operating instructions, or governance controls.
- Acceptance: A rejected data proposal remains rejected or held; it cannot fix its own rejection by changing its validator or reclassifying a protected file.
- Depends on: REQ-009

### REQ-011 - Support bounded technical maintenance
- Requirement: Permit technical maintenance of code, dependencies, and non-governance skill implementation within explicitly selected classes, paths, tools, budgets, and integration targets.
- Source: R01 sections 7 and 13, C11 and C13.
- Acceptance: A supported defect or compatibility need can become an isolated repair with a bounded definition of done, preserved interfaces, applicable regression evidence, and reversible integration.
- Acceptance: Speculative refactoring and unselected classes remain outside the operation; a suspected cause can enter bounded investigation without being treated as a proven repair.
- Depends on: REQ-009

### REQ-012 - Protect governance improvements
- Requirement: Provide a separate governance-change path for instructions, controller charters, role policies, skill operating contracts, and authorization-related configuration.
- Source: R01 sections 7 and 14, C11 and C26.
- Acceptance: Either controller can develop a scoped governance improvement, but publication requires the protected-change authority and independent verification valid before that operation.
- Acceptance: Authority expansion, disabling checks, or permission changes require a separate explicit grant; a patch cannot authorize itself or change its approving enforcement process.
- Acceptance: An accepted governance change reconciles affected actors and deliberately updates bindings under separate authority; the new policy becomes effective at a new execution boundary and stale grants remain rejected.
- Depends on: REQ-009

### REQ-013 - Preserve schemas and bind Curator provenance
- Requirement: Represent Curator origin, selected charter, standing-policy edition, and execution inputs through compatible validated interfaces or explicit versioned extensions where necessary.
- Source: R01 section 5; P01 and P03.
- Acceptance: Strict existing records reject unknown fields; historical Task, memory, ontology, and setup semantics remain intact and are not rewritten to manufacture Curator provenance.
- Acceptance: Existing manager publication routes validate the Curator execution's actual authority inputs; neither a forged Director identity nor the manager label alone is accepted.
- Acceptance: Required schema extensions and any explicit conversion route retain provenance and do not silently migrate old records.
- Depends on: REQ-004, REQ-009

### REQ-014 - Retain one canonical execution owner
- Requirement: Use the existing Task ledger and real manager reservation, launch receipt, activation, version, writer, and completion gates for mutating Curator work.
- Source: R01 sections 5 and 9, C16 and C25; P03.
- Acceptance: A Curator bootstrap transfers canonical Task writing to one confirmed native manager; the bootstrap host and ordinary workers cannot remain competing writers.
- Acceptance: After acceptance into a Task, that Task owns execution/completion state; queue and assessment records reference it and cannot supply conflicting lifecycle status.
- Acceptance: Read-only inspection and unchanged/no-op events do not create Tasks; Curator intake is explicitly selected without broadening unrelated Task activation.
- Depends on: REQ-008, REQ-013

### REQ-015 - Preserve teams and independent evidence
- Requirement: Retain the established generic, complex, and extra-complex team rules, exact inherited model/reasoning settings, independent solver contexts, and version-bound review and acceptance.
- Source: R01 sections 5, 6 and 8; P01 and P03.
- Acceptance: Generic work has one execution worker; complex work retains independent full-problem solvers and a distinct senior; extra-complex work additionally retains distinct reviewer coverage and current passes.
- Acceptance: Native observations prove launch identity, required topology, settings inheritance, and context isolation; capacity constraints queue required work without reducing the team or changing settings.
- Acceptance: Material input/candidate changes invalidate affected evidence; implementation targets the accepted current proposal through the existing distinct-worker rules.
- Depends on: REQ-006, REQ-014

### REQ-016 - Collect relevant local events
- Requirement: Provide reusable inputs for human/agent commits, merge/history/branch transitions, accepted-work completion, manual requests, startup/catch-up, due dependency checks, and deterministic stale-data findings.
- Source: R01 section 8, C04-C05, C20 and C27.
- Acceptance: Human and agent commits receive equivalent evidence-based eligibility; authorship cannot grant permission or exclude required follow-through.
- Acceptance: Hooks record bounded delivery identifiers and signal transport without inference, repository-wide analysis, installation, content edits, commits, or pushes, and preserve existing hook-manager configuration.
- Acceptance: Selected input adapters recover missed events and retain pending work when the runtime is unavailable; no real hook or persistent service is installed merely by distributing the capability.
- Depends on: REQ-002

### REQ-017 - Keep delivery durable without duplicating execution state
- Requirement: Maintain durable event transport with retry, cursors, causality, snapshot identity, and references to canonical executions and publication receipts.
- Source: R01 sections 5, 9 and 15, C20 and C28.
- Acceptance: Queue records identify the project/repository, branch, source snapshot, event/operation identity, causal parent, policy/source hashes, disposition, and Task/receipt references where applicable.
- Acceptance: Pending manual corrections survive restart and are not lost through cache cleanup; Git catch-up reconstructs missed repository events.
- Acceptance: Assessment and transport records preserve their own meaning while canonical Task and publication journals remain authoritative for execution and actual writes.
- Depends on: REQ-014, REQ-016

### REQ-018 - Avoid unnecessary inference and content churn
- Requirement: Run inexpensive deterministic preflight before automatic model invocation and permit a correct no-change outcome.
- Source: R01 sections 1 and 8, C06-C08.
- Acceptance: Preflight verifies project identity, selected branch, trusted policy, event/snapshot integrity, pending recovery, active owners, and affected path classes, and coalesces related events.
- Acceptance: No relevant delta, no due external check, and no relevant pending work results in zero model calls and no content rewrite, Task, memory note, or ontology assertion.
- Acceptance: An irrelevant commit can finish with a transport disposition; unknown file classes or changed dependencies are examined conservatively, while cache/generated/control timestamps alone do not cause full semantic reanalysis.
- Depends on: REQ-009, REQ-016, REQ-017

### REQ-019 - Track snapshot-specific reconciliation
- Requirement: Keep separate observed, assessed, canonically integrated, and fully reconciled checkpoints for each selected project and branch.
- Source: R01 section 9, C06, C18 and C20.
- Acceptance: Rename, interface change, rebase, squash, force update, deletion, and branch switch cases use actual snapshots and ancestry to reassess affected obligations.
- Acceptance: Knowledge and derivatives remain bound to the approved branch snapshot; feature-branch content cannot silently become another branch's current knowledge.
- Acceptance: A commit observed or assessed cannot advance full reconciliation while integration, required products, ownership, or recovery remains unresolved.
- Depends on: REQ-017

### REQ-020 - Prevent duplicates and self-trigger loops
- Requirement: Recognize repeated deliveries and already satisfied work using operation identity, hashes, versions, and causal provenance without suppressing all Curator-originated changes.
- Source: R01 section 9, C15 and C20.
- Acceptance: Duplicate, retried, and out-of-order events cause one logical maintenance outcome and do not duplicate Tasks, lessons, or canonical assertions.
- Acceptance: A Curator code repair receives necessary documentation/knowledge follow-through; its derivative-only follow-up does not restart the satisfied repair.
- Acceptance: Unchanged output/failure and configured iteration or resource limits stop further expansion while retaining the unresolved finding.
- Depends on: REQ-018, REQ-019

### REQ-021 - Prove native runtime capability
- Requirement: Provide a runtime adapter whose supported modes are established by actual activation, delegation, supervision, identity, stopping, and publication observations.
- Source: R01 section 8 and section 17 stage 2, C25.
- Acceptance: Disposable runtime verification demonstrates top-level Curator activation, confirmed manager handoff, required native children, inherited settings, context isolation, supervision, and real publication identity observations.
- Acceptance: Process lists, role names, fixture receipts, and shell-launched substitutes do not masquerade as native agent receipts; a different observation format requires a validated versioned adapter.
- Acceptance: Missing native capability produces a named blocked mode and preserves queued work. Read-only fallback remains available but cannot count as full autonomous-delivery verification.
- Depends on: REQ-013, REQ-014, REQ-015

### REQ-022 - Provide an inactive portable scheduling capability
- Requirement: Supply platform-independent scheduling policy and a separate macOS per-checkout host adapter with explicit installation, readiness, relocation, and unavailable-volume behavior.
- Source: R01 section 8 and section 16 operating choices, C08 and C25; U02.
- Acceptance: The reusable policy validates selected project/branch sets, debounce, catch-up and dependency cadences, bounded model/work budgets, operation entitlements, notifications, and runtime compatibility before activation.
- Acceptance: Neutral configuration has no live project/branch selection, installed service, active schedule, or autonomous-write entitlement; required operating selections are reported as missing rather than guessed.
- Acceptance: Disposable adapter checks distinguish idle, pending, unavailable, blocked, and ready; detached input cannot imply deletion, relocation preserves identity checks, and the existing Template watcher remains independent.
- Depends on: REQ-016, REQ-018, REQ-021

### REQ-023 - Coordinate concurrent owners and isolated integration
- Requirement: Preserve one canonical coordination location and publication owner per logical project/branch while executing scoped changes in an isolated workspace.
- Source: R01 sections 8 and 14, C16 and C22.
- Acceptance: Concurrent worktrees do not create competing writable Task ledgers; overlapping Director/Curator scopes wait or reconcile through their current owners, including paused or uncertain owners.
- Acceptance: Dirty user working trees, staged content, unrelated files, and later human edits survive; no automatic stash, reset, clean, or blind integration is used to gain access.
- Acceptance: Target changes invalidate affected passes and require source/target revalidation before serialized integration; unsupported multi-clone or local/remote ownership is held rather than treated as protected by a local lock.
- Depends on: REQ-014, REQ-019

### REQ-024 - Use owned memory and ontology publication
- Requirement: Make separate evidence-based decisions for memory, ontology, and derived-only maintenance and use their existing lifecycle and publication helpers.
- Source: R01 sections 3 and 11, C04, C07 and C17.
- Acceptance: A change may justify neither, either, or both kinds of canonical knowledge; a commit or passed validator alone cannot establish truth or acceptance.
- Acceptance: Confirmed Curator managers publish through authorized existing routes with exact proposal, source, grant, and operation checks; ordinary children return proposals and never directly rewrite canonical records.
- Acceptance: A stale derivative alone triggers its owning maintenance operation without fabricating a new memory lesson or ontology assertion.
- Depends on: REQ-010, REQ-013, REQ-014

### REQ-025 - Preserve knowledge history and identity
- Requirement: Retain source provenance, applicability, uncertainty, temporal meaning, and replacement relationships when knowledge changes.
- Source: R01 section 11, C17 and C19.
- Acceptance: Manual correction and automatic upkeep use appropriate supersession, retraction, deprecation, or replacement while preserving the earlier record's meaning and stable identity relationships.
- Acceptance: Source rebinding verifies that the semantics still apply and cannot merely substitute a hash to bypass rejection.
- Acceptance: Authored, inferred, externally sourced, and derived material remain distinguishable; historical evidence is not retroactively rewritten to claim new results.
- Depends on: REQ-024

### REQ-026 - Respect memory capture choices
- Requirement: Preserve automatic-capture preferences and existing persistence ownership across learning and Curator integrations.
- Source: R01 sections 11 and 12, C14.
- Acceptance: Capture off prevents equivalent automatic persistence through a renamed Curator path; independently authorized explicit corrections remain possible.
- Acceptance: A distinct entitlement that changes an earlier preference requires deliberate selection and disclosure; starter distribution and ordinary setup reruns cannot silently override an existing choice.
- Acceptance: A bare learning question remains review-only and cannot itself authorize saving, repair execution, service activation, or permission changes.
- Depends on: REQ-009, REQ-024

### REQ-027 - Reconcile all selected dependent products
- Requirement: Complete required dependent maintenance in source-aware order and distinguish canonical publication from full readiness.
- Source: R01 sections 9 and 11, C18 and C28.
- Acceptance: Canonical changes and historical disposition precede any separately authorized recertification and required memory projections, ontology compilation/wiki, semantic products, and derived associations.
- Acceptance: Final checks bind the selected products to their actual input versions and recheck the source snapshot after documentation or integration changes.
- Acceptance: A failed required rebuild remains pending even when a note or assertion was saved; disabled optional profiles are not installed or activated to make status appear current.
- Depends on: REQ-019, REQ-024, REQ-025

### REQ-028 - Hold unsupported semantic changes
- Requirement: Keep conflicting, uncertain, or unsupported semantic changes out of approved canonical content until adequate evidence and required authority exist.
- Source: R01 sections 9 and 11, C19 and C26.
- Acceptance: A held proposal states the exact evidence gap or decision needed, affected source versions, and the bounded correction/review route.
- Acceptance: Structural, SHACL, relationship, or schema conformance is reported separately from factual truth; an inference cannot silently become an approved authored assertion.
- Acceptance: Unresolved meaning is not repaired by broad speculative edits, erased history, or weakened validators.
- Depends on: REQ-024, REQ-025

### REQ-029 - Classify documentation by purpose and ownership
- Requirement: Provide a project-owned classification and dependency map for governance, descriptive documentation, canonical knowledge, generated views, historical evidence, and mixed/unknown material.
- Source: R01 section 10, C12 and C23-C24.
- Acceptance: AGENTS.md, a README, a generated wiki page, and a completed Task response receive different update routes independent of their extension.
- Acceptance: Explicit section/file ownership and overrides take precedence over broad defaults; mixed or unknown content uses the stricter applicable boundary or holds ambiguous edits.
- Acceptance: The map retains canonical sources, generators, protected sections, stable content identity, and affected interfaces without reclassifying its own controls as routine editable prose.
- Depends on: REQ-010, REQ-012

### REQ-030 - Maintain source-backed descriptive documentation
- Requirement: Detect documentation affected by selected changes and update factual descriptions through the declared documentation or generator owner.
- Source: R01 sections 3 and 10, C06 and C12.
- Acceptance: Review covers affected commands, path casing, links, prerequisites, diagrams, examples, interfaces, and status claims, combining deterministic checks with semantic source comparison.
- Acceptance: Generated outputs are rebuilt through their owner; historical reports preserve earlier meaning and receive successors or annotations instead of false retrospective claims.
- Acceptance: Representative rename, changed-interface, and policy-change fixtures produce appropriate distinct outcomes, including the reported role-link casing example without requiring a live-root README repair.
- Depends on: REQ-029

### REQ-031 - Connect learning to supported improvements
- Requirement: Consume the existing learning/completion disposition once and connect unresolved findings to appropriately owned repair or investigation and later observed outcomes.
- Source: R01 section 12, C14-C15.
- Acceptance: A finding can be traced through review, allowed persistence, disposition, authorized repair/investigation, validation, and any later observed outcome without duplicate lessons or Tasks.
- Acceptance: Matching considers objective, artifact, and source version; an active owner's work is coordinated through that owner and terminal work is not reopened merely to create Curator activity.
- Acceptance: Already repaired work receives only its remaining obligations; suspected causes receive bounded investigation, and later benefit remains unobserved until real evidence exists.
- Depends on: REQ-014, REQ-020, REQ-026

### REQ-032 - Assess external dependency changes
- Requirement: Provide due dependency/advisory assessment that can identify relevant candidates while repository content is unchanged.
- Source: R01 sections 8 and 13, C11 and C27.
- Acceptance: The inventory covers declared/locked dependencies, selected optional backends and models, external tools, workflow actions, skill editions, and relevant compatibility constraints.
- Acceptance: Candidates use authoritative release/security information and distinguish security issues, ordinary releases, and deliberately retained compatible pins; newest does not automatically mean acceptable.
- Acceptance: A due external check can create a bounded finding without continuous AI scanning; competing updater services do not manage the same manifests and network/source access follows selected permissions.
- Depends on: REQ-009, REQ-016, REQ-018

### REQ-033 - Validate and isolate dependency changes
- Requirement: Process selected dependency candidates through isolated declaration/lock changes, compatibility checks, and appropriate behavioral verification.
- Source: R01 section 13, C11, C13 and C28.
- Acceptance: Declaration updates, runtime installation, new package sources, and starting services are separately authorized; failed candidates leave live environments and unrelated content intact.
- Acceptance: Major versions, backend swaps, storage/schema changes, and certification implications take the higher-risk path; patch-version labels cannot replace regression checks.
- Acceptance: Checks include a clean candidate environment when dependencies change and any required recertification or derived maintenance before claiming integrated readiness.
- Depends on: REQ-011, REQ-023, REQ-027, REQ-032

### REQ-034 - Keep routine notifications quiet
- Requirement: Report Curator outcomes according to their material impact and suppress routine successful or irrelevant maintenance chatter.
- Source: R01 sections 8 and 16, C21 and C29.
- Acceptance: Idle checks, irrelevant backlog, and routine successful upkeep stay quiet; significant changes, failures, conflicts, and required user actions are visible with concise impact and next action.
- Acceptance: Information, warning, and blocking are distinguishable: information does not interrupt execution, warnings permit safe continuation, and blockers prevent conflicting or invalid execution.
- Acceptance: An optional selected digest or notification channel remains configuration; no external message destination or periodic status flood is enabled by the starter.
- Depends on: None.

### REQ-035 - Check relevant pending work at intake and resume
- Requirement: Add a lightweight read-only Curator-awareness check when project Task work starts or resumes, using existing queue/Task metadata and affected scope.
- Source: R01 section 16 task-start awareness, C29.
- Acceptance: No relevant item produces no interruption and no model review merely to find notices; unrelated work proceeds normally.
- Acceptance: A relevant notice identifies the exact item, affected component, impact level, and available action; warnings offer prior maintenance only when useful.
- Acceptance: Active writer conflict, known-invalid required governance/infrastructure, or failed integrity gates block dependent execution until reconciliation or an explicitly supported safe alternative exists.
- Depends on: REQ-007, REQ-017, REQ-023, REQ-034

### REQ-036 - Resolve clear conversational Curator selection
- Requirement: Accept natural-language selection of one exact Curator item just surfaced with an explicit offer to execute it.
- Source: R01 section 16 natural-language handoff, C30.
- Acceptance: When one item was clearly offered, replies such as do it or do the task select that item and enter the normal Task, ownership, role, authority, and verification pipeline.
- Acceptance: If multiple items are eligible, the offer is no longer applicable, or the phrase could refer to the original work, the system asks the smallest disambiguating question instead of guessing.
- Acceptance: Explicit Curator commands remain available but are not mandatory for an unambiguous conversational selection; read-only questions do not imply execution consent.
- Depends on: REQ-008, REQ-014, REQ-035

### REQ-037 - Preserve and resume the original request
- Requirement: Retain the user's original work intent and its authority while an intervening Curator item is handled.
- Source: R01 section 16 natural-language handoff, C30.
- Acceptance: The original objective, constraints, and existing Task selection remain recoverable without a competing execution or fabricated new authorization.
- Acceptance: After a truthful terminal or blocked Curator outcome, the original request is reassessed and continues when prior authority, relevant assumptions, and required integrity gates still permit it.
- Acceptance: A Curator change that alters original requirements, scope, or safe execution conditions triggers focused re-evaluation before continuation; a remaining blocker is not bypassed.
- Depends on: REQ-019, REQ-023, REQ-036

### REQ-038 - Support truthful pause and exact recovery
- Requirement: Provide explicit pause/resume and recovery behavior that preserves actors, operation identities, journals, and partial results.
- Source: R01 sections 9, 14 and 16, C25 and C28.
- Acceptance: Emergency pause stops new dispatch, requests actual interruption, reconciles active/uncertain actors and partial writes, and revokes future grants according to the owning protocol.
- Acceptance: Status distinguishes queued, launched, confirmed, held/blocked, stopped, partially published, integrated, and fully reconciled observations without inventing new competing Task terminal states.
- Acceptance: Retry/resume follows exact recorded operations and current ownership; timeout or timestamp age alone cannot establish stopping, grant takeover, or justify destructive rollback.
- Acceptance: Recovery preserves later human edits and history; cross-subsystem operations report their real partial-commit boundaries rather than claiming nonexistent atomicity.
- Depends on: REQ-014, REQ-017, REQ-021, REQ-023, REQ-027

### REQ-039 - Enforce the trust boundary for unattended work
- Requirement: Keep untrusted content and proposed changes outside the trusted process that approves their authority and publication.
- Source: R01 sections 7 and 14, C26.
- Acceptance: Diffs, commit/branch text, notes, retrieved documents, and release information remain data and cannot create shell execution, permission changes, or authority escalation.
- Acceptance: Unattended mutating modes require an enforced boundary beyond cooperative role text and an isolated worktree; the candidate cannot rewrite its own approval mechanism or effective policy.
- Acceptance: Credentials stay out of source control, prompts, records, receipts, logs, and fixtures; execution/install tooling uses only selected filesystem/network access.
- Acceptance: Negative cases prove a malicious branch name, diff, policy patch, or note cannot approve itself or bypass protected publication.
- Depends on: REQ-009, REQ-012, REQ-021, REQ-023

### REQ-040 - Report complete reconciliation from current evidence
- Requirement: Declare a maintenance batch fully reconciled only when every required integrated outcome and dependency is verified at the final source snapshot.
- Source: R01 section 9 final completion predicate, C18 and C25.
- Acceptance: The predicate includes actually integrated canonical changes, valid authority/receipts, applicable checks on the integrated result, current required derivatives, no unresolved owner/partial publication/recovery, and a final source recheck.
- Acceptance: A source change after a candidate pass invalidates affected evidence; observed, proposed, tested, integrated, and fully reconciled remain distinct claims.
- Acceptance: Readiness/status reads do not repair or install components to satisfy the predicate.
- Depends on: REQ-019, REQ-023, REQ-027, REQ-028, REQ-038

### REQ-041 - Verify the complete reusable capability
- Requirement: Provide traceable deterministic, behavioral, native, and integrated verification for the shared-source release and its Template distribution.
- Source: R01 sections 17-18, C01-C30; U02; P01-P04.
- Acceptance: Verification maps each requirement to concrete source artifacts and checks, covering no-op/inactivity, irrelevant and renamed inputs, duplicate/missed/out-of-order events, rewritten history, corrections, opt-out, already-fixed lessons, and stale derivatives.
- Acceptance: Failure coverage includes overlapping or uncertain owners, dirty worktrees, malicious content, stale grants, failed dependencies, partial publication, pause/recovery, unavailable drives/runtime, and source changes after passing checks.
- Acceptance: Conversational cases cover unrelated/relevant pending work, each notification level, clear and ambiguous selection, and original-intent continuation after assumptions change.
- Acceptance: Shared sources and mapped Template behavior pass compatibility and preservation checks in disposable projects; native runtime/ownership claims require real observations. Missing required runtime proof remains an explicit incomplete item, not a passing fixture substituted for delivery.
- Acceptance: Final evidence distinguishes source capability, Template distribution, disposable adoption/runtime checks, unperformed root/product adoption, and later operational benefit; no production rollout is claimed.
- Depends on: REQ-001, REQ-002, REQ-003, REQ-015, REQ-021, REQ-030, REQ-031, REQ-033, REQ-037, REQ-039, REQ-040, REQ-042

### REQ-042 - Measure useful maintenance outcomes
- Requirement: Expose bounded operational evidence that allows later deployments to assess maintenance benefit and resource use without using edit volume as success.
- Source: R01 section 18 operational outcomes, C08 and C25.
- Acceptance: Observable metrics include unresolved staleness, duplicate findings, repair reversals, protected-write violations, dependency exposure, reconciliation delay, repeated failures, and inactivity model use.
- Acceptance: The reusable release verifies metric meaning and collection on representative scenarios; live service targets and benefit baselines require later measured deployment and are not invented here.
- Acceptance: Metrics do not themselves create knowledge records, goals, Tasks, or permission to continue unnecessary work.
- Depends on: REQ-018, REQ-020, REQ-034, REQ-040

## Decisions

- D01 — Shared sources first. U02 narrows R01's broader rollout. Shared reusable implementations and required distribution integration are included; the Template is the existing shared-asset distribution target under P02. Active root adoption and existing product adoption are deferred. A later exact adoption can use this capability without a second TRD unless the required behavior changes.
- D02 — Complete capability, inactive deployment. The first delivery includes the manual, automatic, technical, and protected-governance capability described by R01, plus representative verification. A read-only prototype alone does not satisfy it. Neutral configuration and disabled live activation implement the source-first boundary without selecting operational permissions for a real project.
- D03 — Operational selection belongs to adoption. Cadences, budgets, allowed projects/branches, entitled operation classes, network access, service installation, and commit/integration/push policies must be explicitly supplied and validated before their respective runtime actions. No such live action is part of this baseline, so these absent installation values are not unresolved requirements for shared-source delivery. Their required configuration and enforcement behavior is captured in REQ-009, REQ-022, and related requirements.
- D04 — Preserve existing infrastructure and policy differences. Curator integration extends reusable contracts and existing owned helpers. The generic Task policy retains its separate selection semantics; the active depot's local intake/age-closure policy is not generalized by this release. Schema changes, if needed, are versioned and tested without automatic historical migration.
- D05 — Separate source basis from approval. R01 is the supplied design proposal and supports the derived requirements, subject to U02 and current project rules. Its instructions do not authorize this agent to implement, activate, install, delegate, commit, or publish. This exact document remains a reviewable draft until the user approves it.
- D06 — Bounded implementation choices. Internal queue formats, helper APIs, package splits, exact filenames other than the required charter, version numbers, trusted-process mechanism, and supported runtime adapter are planning choices constrained by the observable requirements. R01's proposed CURATION-depo collection and curate/documentation/knowledge/maintenance package layout are reference designs, not a mandate to duplicate infrastructure. The core and operating responsibilities remain mandatory whichever packaging is selected.
- D07 — Runtime options require proof. R01's App Server, noninteractive runtime, dependency updater, and host-mechanism references are candidates, not verified compatibility claims. The selected adapter must meet the native/execution requirements; unavailable evidence blocks the affected delivery claim rather than reducing scope. Disposable verification does not authorize persistent deployment in a real installation.
- D08 — Knowledge specialization. R01 explicitly proposes a Knowledge Curator responsibility in addition to documentation and technical maintenance. This baseline retains that responsibility while allowing a qualified combined role for a small bounded assignment. The established Task category rules govern actual team shape.
- D09 — Optional future delivery. Existing-product migration, remote/CI adapters, multi-clone active coordination, and HTML documentation are outside this first delivery. The local core preserves ownership and source/generator boundaries that permit later work without promising its implementation now.
- D10 — No arbitrary service targets. The release must provide useful measurements and configurable bounded operation. Numeric service-level promises and ongoing benefit claims depend on a later selected deployment and measured baseline.
- D11 — Requirement traceability. The source proposal's C identifiers remain source labels; the REQ identifiers below are this document's stable requirement identities. Detailed source scenarios are incorporated into acceptance rather than copied as a downstream implementation sequence.

| R01 source requirement | TRD coverage |
| --- | --- |
| C01 | REQ-004, REQ-014 |
| C02 | REQ-005 |
| C03 | REQ-002, REQ-003, REQ-005 |
| C04 | REQ-008, REQ-024, REQ-025 |
| C05 | REQ-016 |
| C06 | REQ-018, REQ-019, REQ-029, REQ-030 |
| C07 | REQ-018, REQ-024 |
| C08 | REQ-018, REQ-022, REQ-042 |
| C09 | REQ-009 |
| C10 | REQ-010 |
| C11 | REQ-011, REQ-012, REQ-032, REQ-033 |
| C12 | REQ-006, REQ-029, REQ-030 |
| C13 | REQ-006, REQ-011, REQ-033 |
| C14 | REQ-026, REQ-031 |
| C15 | REQ-004, REQ-020, REQ-031 |
| C16 | REQ-014, REQ-023 |
| C17 | REQ-024, REQ-025 |
| C18 | REQ-019, REQ-027, REQ-040 |
| C19 | REQ-025, REQ-028 |
| C20 | REQ-016, REQ-017, REQ-019, REQ-020 |
| C21 | REQ-034 |
| C22 | REQ-001, REQ-002, REQ-003, REQ-023 |
| C23 | REQ-010, REQ-029 |
| C24 | REQ-029; HTML exclusion in Out of scope and D09 |
| C25 | REQ-007, REQ-014, REQ-021, REQ-022, REQ-038, REQ-040, REQ-042 |
| C26 | REQ-009, REQ-010, REQ-012, REQ-028, REQ-039 |
| C27 | REQ-016, REQ-032 |
| C28 | REQ-008, REQ-017, REQ-027, REQ-033, REQ-038 |
| C29 | REQ-034, REQ-035 |
| C30 | REQ-036, REQ-037 |

REQ-013 captures the versioned provenance integration in R01 section 5; REQ-015 captures its team and runtime safeguards; REQ-041 provides integrated verification across the source requirements. No source requirement is removed without the explicit rollout or future-feature exclusions above.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
