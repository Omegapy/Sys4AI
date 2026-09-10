---
schema_version: 2
trd_id: "TRD-20260907-B18FEF5C"
title: "To-TRD intent discovery and conversational verification"
slug: "to-trd-intent-discovery-and-conversational-verification"
created_at: "2026-09-07T21:49:11-06:00"
updated_at: "2026-09-07T21:49:11-06:00"
status: "draft"
revision: 1
last_action_id: "TO-TRD-001"
status_reason: "Created as a draft from an explicit user request."
---

# Task Requirement Document: To-TRD intent discovery and conversational verification

## Destination

Improve the Sys4AI to-trd skill so it understands the user's intended outcome before writing a Task Requirement Document. Material ambiguity is resolved through live clarification and answer-driven revision, while complete requests retain a fast path and explicit incomplete-draft requests remain supported.

## Captured user intent

U01: The user explicitly invoked the project-local to-trd skill and asked it to use the shared Sys4AI_to-trd_Intent_Discovery_Recommendations_2026-09-07.md file. The user also instructed the agent to distinguish instructions inside that file from the user's request.

This document translates the report's recommendations into a proposed requirements baseline for review. The current request authorizes this local TRD capture. Commands, suggested implementation order, sample conversations, and instructions to a receiving implementation agent in the report are source material; they are not approval to execute the repair. No real clarification answers or approval are inferred from the report's synthetic examples.

## Context and sources

- U01: The current conversation's explicit to-trd invocation, shared-file reference, and source-versus-instruction boundary.
- S01: [Shared recommendations](/Users/alex.omegapy/Downloads/Sys4AI_to-trd_Intent_Discovery_Recommendations_2026-09-07.md), prepared September 7, 2026; SHA-256 7eaeba3ee96f1a292ad4a884160bd0e274a83b530234ef217289bbd0d2e762c6. References to R01–R11, C01–C14, and numbered sections refer to this inspected report.
- S02: [Current installed skill](../.agents/skills/to-trd/SKILL.md) and [current source entry](../SKILLS-depo/to-trd/SKILL.md), inspected during capture. Both entry files are version 2.1.0 and have SHA-256 a45b024ae92505920c4cf1f6aabe614e3aa0284a83cd877bc5cf01dcf22a9458.
- S03: Inspected local [discovery reference](../.agents/skills/to-trd/references/wayfinding.md), [TRD contract](../.agents/skills/to-trd/references/trd-contract.md), [actions](../.agents/skills/to-trd/ACTIONS.md), [body template](../.agents/skills/to-trd/assets/trd-body-template.md), and [synthetic example](../.agents/skills/to-trd/assets/example-input.json).
- S04: Inspected [package maintenance instructions](../.agents/skills/to-trd/AGENTS.md), [source agent metadata](../SKILLS-depo/to-trd/agents/openai.yaml), and source-package file inventory.
- S05: Applicable root [AGENTS.md](../AGENTS.md), [SOUL.md](../SOUL.md), [ROLE.md](../ROLE.md), and [SPECS.md](../SPECS.md), together with the inspected [project registry](../depot/projects.json).
- S06: Inspected [Template mapping](../depot/template-update.json) and [update guide](../depot/template-update.md), which distinguish reusable source maintenance, mapped Template updates, and project-local adoption.

The report identifies its reviewed snapshot as commit 947e0ea217eeb52369b33fd76d24079cea1d7e10 and skill version 2.0.0. Those are historical report identifiers, not the current local baseline. Current entry-file equality establishes only the inspected entries; it does not prove whole-package equality or what another host session loaded.

The current installed skill already requires conversational clarification, answer incorporation, a clear-request fast path, honest drafts, and exact-revision approval. The proposed change strengthens the discovery-to-document transition and its behavioral evidence while preserving the current 2.1.0 completion workflow. The report supplies no reproduced failing transcript or live execution evidence; this capture does not diagnose a proven failure mechanism. Its external links and upstream observations are report provenance, not claims of a fresh upstream audit.

## In scope

- Requirements for the reusable discovery behavior and its package documentation, metadata, examples, compatibility constraints, and verification.
- SKILLS-depo/to-trd/ as the future source-maintenance target, with the existing mapped Template workflow preserved.
- The report's R01–R11 recommendations and C01–C14 conversational acceptance cases, including actual-host verification criteria for a separately authorized implementation.
- A local managed TRD and its generated index under this capture request.

## Out of scope

- Executing the captured repair, generating a downstream implementation plan, creating or changing a project Task, launching agents or separate tasks, installing dependencies, Git activity, publication, deployment, and external actions under this request.
- A schema revision, renamed skill, new lifecycle states or CLI operations, interview database, second discovery system, mandatory questionnaire, and compulsory upstream skill installation.
- Active-root or ordinary product-project adoption without separate exact authorization; the existing mapped Template mechanism is preserved.
- Rewriting, migrating, retiring, deleting, or otherwise altering existing TRDs as a side effect of skill maintenance.
- Changes to unrelated governance, Task, memory, registry, or project workflows.

## Task requirements

### REQ-001 — Make understanding intent the entry-point responsibility
- Requirement: The to-trd entry point and agent metadata must describe intent discovery as the primary responsibility and TRD writing as the synthesis of understood intent, within the existing project role.
- Source: S01 §1 and R01; S02.
- Acceptance: SKILL.md and agents/openai.yaml consistently describe inspecting the request, resolving material ambiguity, and deriving requirements before document approval.
- Acceptance: The package retains the name to-trd, Task Requirement Document terminology, TRP as an alias, and explicit invocation without introducing a new agent identity or mandatory subagent.
- Depends on: None.

### REQ-002 — Use an explicit readiness check before ordinary synthesis
- Requirement: Ordinary synthesis must proceed only when applicable material requirement areas are understood from the request, inspected facts, actual user answers, or explicit delegation.
- Source: S01 R03; S02 and S03.
- Acceptance: The check considers outcome, beneficiary and use, current state and change, scope and exclusions, inputs and outputs and behavior, constraints and authority, observable success, and consequential edge cases.
- Acceptance: A gap is material when alternative answers change the required outcome, scope, interface, constraints, acceptance, or action authority; a bounded implementation choice does not become a requirement gap.
- Acceptance: A fully specified request takes the fast path without a compulsory questionnaire, numeric readiness score, or repeated confirmation; the ability to invent a plausible document does not establish readiness.
- Depends on: None.

### REQ-003 — Separate discoverable facts from user-owned decisions
- Requirement: Discovery must inspect relevant available sources for factual gaps and use the conversation for unresolved desired behavior, priorities, tradeoffs, and authority.
- Source: S01 R04 and R07; S03.
- Acceptance: A fixture establishing the current format is inspected without asking the user to restate it; that fact is not treated as approval to preserve the format in a redesign.
- Acceptance: Source facts, user intent, design proposals, explicit delegation, assumptions, and contradictions remain distinguishable; unavailable evidence is reported without invented research or a required new plugin.
- Depends on: None.

### REQ-004 — Pause after asking for a material user decision
- Requirement: When a material intake decision belongs to the user, the agent must ask one focused question with its consequence and wait for the actual answer before dependent synthesis or writing.
- Source: S01 R02 and §6 proposed control flow; S03.
- Acceptance: An ambiguous first capture produces a live clarification question and ends the response without a TRD write or a presented completed baseline in that turn.
- Acceptance: Silence, elapsed time, a preselected recommendation, a tool result, and an unrelated reply do not settle the decision or authorize a write.
- Acceptance: Discovery resumes from the actual answer or an explicit user instruction changing the requested mode, subject to higher-priority host instructions.
- Depends on: None.

### REQ-005 — Sequence clarification by consequence and dependency
- Requirement: The interview must adapt one material question at a time to settled prerequisites and the latest answer, preserving only the decisions that the user actually resolves.
- Source: S01 R04 and cases C03–C04.
- Acceptance: The agent surveys the major requirement areas, addresses outcome and scope first when unresolved, and selects a useful answerable question without imposing a fixed interview length.
- Acceptance: A dependent question is asked only after its prerequisite is settled and only if it remains relevant.
- Acceptance: A partial answer or ambiguous agreement resolves only its clear portion; the remaining material distinction receives a focused follow-up without repeating settled questions.
- Depends on: None.

### REQ-006 — Propagate answers and changed intent into the requirements
- Requirement: Each material clarification must update all affected intent, scope, constraints, decisions, requirements, and acceptance criteria before further discovery or synthesis.
- Source: S01 R04 and R07–R08; cases C02 and C09; S03.
- Acceptance: A clarification specifying one project and no sharing appears in scope and the relevant requirement and acceptance, with contradictory cross-project behavior removed.
- Acceptance: A changed answer invalidates dependent assumptions and obsolete interview branches; recording the answer only in Decisions while leaving affected behavior vague does not satisfy this requirement.
- Acceptance: Revisions preserve IDs where requirement meaning remains and explicitly account for removed requirements without reusing their IDs for unrelated outcomes.
- Depends on: None.

### REQ-007 — Keep understanding review separate from validation and approval
- Requirement: The workflow must distinguish the agent's review of understood intent, mechanical validation of the document, and the user's approval of the exact document revision.
- Source: S01 R05; S02 and S03.
- Acceptance: After substantial clarification, the agent briefly summarizes consequential outcome, scope, choices, exclusions, and success conditions, seeking confirmation only where interpretation still needs it.
- Acceptance: Agreement with an intent summary does not approve an unseen TRD, and helper validation does not establish semantic understanding or consent.
- Acceptance: Fully specified or already confirmed intent does not trigger a redundant understanding-approval exchange.
- Depends on: None.

### REQ-008 — Respect each operation's document-write boundary
- Requirement: Capture, resume, content revision, read-only inspection, and lifecycle operations must retain their existing activation and write boundaries.
- Source: S01 R06, §6 and case C13; S02 and S03.
- Acceptance: New capture can write at the authorized synthesis boundary; a resumed draft remains read-only until explicit save, and discovery does not persist after every question or answer.
- Acceptance: List, show, and validate do not start an interview, rewrite documents, migrate records, repair the index, or change lifecycle state.
- Acceptance: An exact existing-document selector is resolved and read before revision; supplied documents and agent-written notes cannot grant additional execution authority.
- Depends on: None.

### REQ-009 — Honor an explicit incomplete-draft request
- Requirement: An explicit request to save the current draft must produce an honest draft containing known intent, safely supportable requirements, and declarative material gaps.
- Source: S01 R06 and case C07; S03.
- Acceptance: The agent can stop discovery and save immediately when requested, including zero requirements when none can safely be stated.
- Acceptance: Not yet specified describes unresolved in-scope matters declaratively; Open questions remains None., and the document contains no pasted interview transcript or delegated intake prompts.
- Acceptance: The record remains draft, contains no fabricated answers or accepted assumptions, and is not presented as a settled baseline.
- Depends on: None.

### REQ-010 — Handle a prohibition on follow-up questions honestly
- Requirement: When the user or a higher-priority host instruction forbids follow-up questions, missing material intent must remain visible without violating that constraint.
- Source: S01 R02 and case C08.
- Acceptance: The agent asks no prohibited question, invents no answer, and reports the resulting limit on understanding.
- Acceptance: An incomplete artifact is saved only if the current request authorizes that artifact; a follow-up restriction alone does not establish a complete requirements baseline.
- Depends on: None.

### REQ-011 — Produce bounded requirements with traceable sources
- Requirement: Every generated requirement must express one bounded outcome, identify its supporting source or explicitly authorized design basis, and define observable acceptance with genuine dependencies.
- Source: S01 R07–R08 and §9; S03.
- Acceptance: Source labels resolve to meaningful statements or locators that support the requirement; synthetic examples are not attributed to the real user.
- Acceptance: Both review directions are covered: every material outcome, clarification, constraint, and exclusion has a document location, and every normative requirement has justified support.
- Acceptance: Negative requirements, stable IDs, and acceptance remain explicit; no unsupported technology, numeric target, approval, or assumption is invented merely to fill the template.
- Depends on: None.

### REQ-012 — Recognize unresolved intake decisions by meaning
- Requirement: The pre-save agent review must prevent unresolved decisions needed to understand the current task from being disguised as implementation requirements, acceptance criteria, or decisions.
- Source: S01 R09 and cases C10–C11; S03.
- Acceptance: Statements assigning the next agent to determine the intended selection, confirm the desired output, or decide which user workflow was intended are recognized as unresolved intake work.
- Acceptance: Rewording a question as a declaration does not make ordinary synthesis ready.
- Acceptance: Legitimate deliverable behavior that asks its future user a question, requested research questions, quoted labels, and URL query strings are not rejected merely for containing question language or punctuation.
- Depends on: None.

### REQ-013 — Align the package guidance and interaction examples
- Requirement: The source package must provide one consistent discovery procedure across its entry file, references, metadata, template, example, and maintenance documentation.
- Source: S01 §6; S04.
- Acceptance: SKILL.md contains the critical readiness, pause, and answer-propagation rules; references/wayfinding.md supplies the detailed procedure without a contradictory competing flow.
- Acceptance: New references/interaction-examples.md covers the clear fast path, ambiguous request with a real pause, answer-driven follow-up, and requested incomplete draft, and is linked from the discovery reference and package index.
- Acceptance: The template preserves its contract without becoming an interview checklist; the valid synthetic example adds a clarification source that changes an actual requirement and acceptance, with affected fixtures aligned.
- Acceptance: README.md, INDEX.md, AGENTS.md, ACTIONS.md, and references/trd-contract.md accurately describe the same operations, write boundaries, verification limits, and source-maintenance paths.
- Depends on: None.

### REQ-014 — Preserve schema, storage, and historical compatibility
- Requirement: The discovery repair must preserve schema 2, the current helper API and operation IDs, project-local storage, and the existing compatibility and safe-write contracts.
- Source: S01 §6 and §9; S02–S04.
- Acceptance: The schema headings, requirement fields, frontmatter, draft/trd_done/retired states, canonical Markdown records, generated index, immutable identities, and hash-checked helper writes remain compatible.
- Acceptance: New and content-updated TRDs keep Open questions as None.; existing read and explicit-migration behavior for historical questions and evidence is preserved.
- Acceptance: No new schema field, status, CLI subcommand, persisted interview database, or second canonical store is introduced merely to record discovery.
- Acceptance: Existing TRDs are not silently rewritten, renamed, migrated, retired, or deleted as a side effect of package maintenance.
- Depends on: None.

### REQ-015 — Preserve exact-revision approval and current diagnostics
- Requirement: Document completion must retain the current 2.1.0 approval workflow and truthful structural completion diagnostics.
- Source: S01 R05 and §9; S02 and S03; U01.
- Acceptance: New records remain draft until the user explicitly approves the presented unchanged revision; the agent uses the current hash, reason, and confirmation, then reads back trd_done.
- Acceptance: Approval requires at least one valid requirement, empty unresolved sections, and no unconfirmed assumptions; approval-bearing content changes return an approved document to draft.
- Acceptance: completion.content_ready, blockers, and next_action remain derived from the actual gate and are described as structural diagnostics, without semantic-understanding claims or keyword exemptions.
- Acceptance: A normal settled capture presents the document and asks for approval only when missing; a draft-only request or read-only inquiry does not initiate that exchange.
- Acceptance: Document approval grants no planning, implementation, migration, installation, Git, publication, deployment, or external-action authority.
- Depends on: None.

### REQ-016 — Verify the source helper and changed contracts
- Requirement: Mechanical verification of a reusable package change must exercise the source copy being changed and retain existing helper regressions.
- Source: S01 R10 and §7 source-package checks; S04 and S06.
- Acceptance: Maintenance commands target SKILLS-depo/to-trd/tests and SKILLS-depo/to-trd/scripts/trd.py using the repository's existing Python environment.
- Acceptance: Changed contracts, example fixtures, or optional diagnostics receive proportionate focused checks; unchanged installed-copy tests do not stand in for verification of changed source files.
- Acceptance: Storage and syntax results are reported accurately, with generated caches kept out of deliverables; prepared document-body tests are not called live interviews.
- Depends on: None.

### REQ-017 — Define the complete conversational acceptance set
- Requirement: New tests/interaction-scenarios.md must define the report's C01–C14 cases with synthetic inputs, expected visible behavior, and prohibited writes where applicable.
- Source: S01 R10 and its C01–C14 table.
- Acceptance: C01 requires an ambiguous first-turn question and real pause with no write; C02 requires the actual answer to change isolation requirements and acceptance.
- Acceptance: C03 covers prerequisite-dependent questioning; C04 covers partial answers and ambiguous agreement without invented consent.
- Acceptance: C05 covers inspection of a source-resolvable fact; C06 covers a fully specified fast path that writes only within authority and remains draft until approval.
- Acceptance: C07 covers an explicitly requested incomplete draft, including zero requirements; C08 covers missing intent when questions are prohibited.
- Acceptance: C09 covers changed intent, affected acceptance, stable IDs, and accounted removals; C10 detects unresolved intake work hidden in declarative wording.
- Acceptance: C11 preserves legitimate question content in the intended deliverable; C12 separates intent agreement from exact-document approval and implementation authority.
- Acceptance: C13 verifies read-only operations; C14 verifies the deliberately selected candidate package and its resources in a fresh target-host session.
- Depends on: None.

### REQ-018 — Verify the discovery behavior in actual conversations
- Requirement: Behavioral verification must exercise the candidate skill with sequences of user messages and distinguish executed interaction evidence from static checks.
- Source: S01 R10, §7 and §9.
- Acceptance: At minimum, the actual target host exercises an ambiguous first turn, answer-driven revision, the clear fast path, an explicit incomplete draft, and exact-document approval.
- Acceptance: The ambiguous case is repeated with differently worded requests, and a critical ambiguous case is exercised in a fresh session loading the deliberately selected candidate entry and resources.
- Acceptance: Tests use disposable project roots and synthetic facts; evidence records the loaded skill path, version and hashes, relevant host instructions, available model configuration, minimal visible exchanges, write calls, and final artifact.
- Acceptance: Manual host exercises or an available conversation evaluator are acceptable, with the actual mode and unexecuted cases identified; synthetic test answers are never treated as real user approval.
- Acceptance: Evidence excludes hidden reasoning, credentials, unrelated conversations, and unnecessary raw logs.
- Depends on: None.

### REQ-019 — Keep reusable maintenance within the source-to-Template boundary
- Requirement: The reusable repair must be authored in SKILLS-depo/to-trd/ and follow the existing checked mapping into the registered Sys4AI Template.
- Source: S01 R11 and §8; S05 and S06.
- Acceptance: Before future implementation, the current package, applicable guidance, mappings, and destination state are reinspected instead of relying on the report's reviewed snapshot.
- Acceptance: Mapped Template updates use the existing template-update workflow and are checked against the source; no direct edit to a mapped Template copy or automatic product-project propagation is inferred.
- Acceptance: Verification reports the actual check result and any conflict or recovery state; watcher installation, running status, and host readiness are not inferred from a mapping or matching version.
- Depends on: None.

### REQ-020 — Preserve project-local installations and unrelated state
- Requirement: Active root and ordinary product-project installations must remain project-local, with any later adoption limited to separately authorized exact destinations and overwrite boundaries.
- Source: U01; S01 R11 and §8; S05.
- Acceptance: An installed-copy refresh, if separately authorized, inspects source and destination guidance and content, preserves local changes, defines the exact file set, and verifies the resulting package.
- Acceptance: No bulk child-project refresh, global install, root-governance change to force invocation, or unrelated Task, memory, registry, or TRD mutation accompanies the repair.
- Acceptance: Disposable evaluation of the candidate and the mapped Template path are distinguished from adoption into the active root or product projects; source verification alone is not reported as installed-host verification.
- Depends on: None.

### REQ-021 — Keep the adaptation self-contained and preserve provenance
- Requirement: The revised package must remain a lightweight self-contained adaptation with accurate attribution and versioning.
- Source: S01 §3, §6, §8 and §9; S02 and S04.
- Acceptance: The package retains Matt Pocock's Wayfinder attribution and MIT notice, adds provenance only for newly adapted material actually inspected, and does not present unverified upstream claims as current facts.
- Acceptance: The repair does not require an upstream Wayfinder or companion-skill installation, tickets, research branches, mandatory agents, or one-ticket-per-session machinery.
- Acceptance: The package version increment follows repository practice while document schema 2 remains unchanged.
- Depends on: None.

### REQ-022 — Report the actual verification and adoption level
- Requirement: The final report for a separately authorized implementation must identify the delivered changes and the highest verification level actually supported by evidence.
- Source: S01 §7–§9; S05.
- Acceptance: The report names changed files, the source revision, helper checks and their results, conversational cases actually executed, fresh-host evidence, and separately authorized installed-copy changes.
- Acceptance: It distinguishes static checks, helper tests, live interaction behavior, host integration, and unexercised behavior, including any remaining failure or limitation.
- Acceptance: It does not claim that the original behavioral problem is fixed solely because instructions were rewritten, versions match, or Python tests pass.
- Depends on: None.

## Decisions

- D01: This is a new capture under U01, not a revision of an existing TRD or execution of the attached handoff. The report's proposals supply the baseline for document review; approval has not yet been given.
- D02: The current inspected 2.1.0 entry and its completion contract govern compatibility. The report's 2.0.0 snapshot is retained as historical context rather than used to remove later behavior.
- D03: Detailed wording, a repository-consistent package version increment, and the choice of a manual host exercise or an already available evaluator remain implementation choices within the specified behavior and evidence requirements. They do not require a new schema, new dependency, or unresolved requirements entry.
- D04: Supplemental semantic linting is optional under S01 R09. A helper rewrite is not required; any chosen diagnostic must preserve strict writes and be tested without claiming to establish consent or comprehension.
- D05: Source authoring and mapped Template maintenance follow existing project governance. No installed-root or product-project refresh is included by implication, and actual-host testing must preserve that adoption boundary.
- D06: Understanding review, document validation, document approval, and authority to implement remain distinct. This document's acceptance criteria specify future required behavior; they are not claims that that behavior was exercised during capture.
- D07: No cross-requirement dependency is imposed merely to encode implementation order. The report's suggested sequencing remains planning input outside this TRD's operation.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
