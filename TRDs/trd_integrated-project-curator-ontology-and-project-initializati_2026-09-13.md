---
schema_version: 2
trd_id: "TRD-20260913-C85981B3"
title: "Integrated Project Curator, ontology and project initialization"
slug: "integrated-project-curator-ontology-and-project-initializati"
created_at: "2026-09-13T08:52:09-06:00"
updated_at: "2026-09-13T09:02:47-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "User explicitly approved the unchanged presented TRD revision during the current voice conversation."
---

# Task Requirement Document: Integrated Project Curator, ontology and project initialization

## Destination

Make Project Curator an integral, usable part of the Sys4AI depot root and of each selected project's ontology. Supply the same complete capability through the neutral Template and supported new-project, existing-project preparation and selected adoption workflows, while resolving the remaining findings in the root health report.

## Captured user intent

U01 — The user requests a new Task Requirement Document based on the supplied root health report. The missing ontology integration must cover Curator process functionality in the root and Template, and must be included when Sys4AI initializes a new or existing project.

U02 — Curator must be integrated with the project itself and with its ontology. Successful supported setup must deliver both together, including selected adoption for previously initialized projects. An installed package or a capability name without the corresponding functions and relationships does not meet that outcome.

The present work captures requirements for review. It does not perform the repairs or grant authority to implement them. The previously rejected and deleted TRD is not a source or an approved baseline.

## Context and sources

All file locators below are relative to the Sys4AI depot root. Exact inspected source hashes are recorded in the [source manifest](../Verification/curator-ontology-integration-trd-20260913-v1/source-manifest.json) and [integration observation](../Verification/curator-ontology-integration-trd-20260913-v1/integration-observation.json).

- U01–U02: Current user request, captured in [request.md](../Verification/curator-ontology-integration-trd-20260913-v1/request.md).
- H01: [Root system health report](../Verification/root-health-followup-trd-20260912-v1/REPORT.md), an exact retained copy of the supplied September 12 report. It records absent Curator ontology discovery, pending owner maintenance, an old staged Task response, and an unverified on-demand workbench. Memory retrieval and ontology core/backend probes passed at that check.
- G01: Root [AGENTS.md](../AGENTS.md), [ROLE.md](../ROLE.md) and [SPECS.md](../SPECS.md), covering project ownership, reusable sources, current canonical writers, publication boundaries and preservation.
- C01: Installed [Curator skill](../.agents/skills/curate/SKILL.md), [action inventory](../.agents/skills/curate/ACTIONS.md) and [session maintenance contract](../.agents/skills/curate/references/session-maintenance.md), covering functions, collection, owner dispatch and bounded session behavior.
- O01: Installed [ontology skill](../.agents/skills/ontology/SKILL.md) and [command reference](../.agents/skills/ontology/references/commands.md), covering typed discovery, source provenance, projection maintenance, publication and workbench boundaries.
- I01: Reusable [initializer skill](../SKILLS-depo/init-new-project/SKILL.md), its `scripts/init_new_project.py`, `scripts/init_curator.py` and `assets/baseline-assets.json`, covering creation, first preparation, selected module adoption, specialization, preservation and setup evidence.
- T01: [Template update guide](../depot/template-update.md), [mapping](../depot/template-update.json), [project registry](../depot/projects.json) and the registered Template's `AGENTS.md`, `ROLE.md`, `curator-session.yaml` and `ontology.yaml`, covering source distribution and neutral starter state.
- D01: [Integration observation](../Verification/curator-ontology-integration-trd-20260913-v1/integration-observation.json), binding inspected initializer and ontology starter bytes. The reusable and Template project/binding graphs are empty; the inspected Curator adoption path specializes Curator configuration while protecting the existing ontology tree.

The report's two pending signals, 42,406 changed-path metadata records and old Task revision are dated observations. They are not current counts, proof of maintenance failures, or authority to alter records. A missing workbench endpoint at that check did not establish a failed service.

## In scope

- Requirements for coherent Curator project operation and functional ontology representation in the active depot root.
- Reusable Curator and ontology assets, mapped Template distribution, and initializer behavior needed to supply the same integration to selected destinations.
- New-project creation, first-time preparation of existing projects, and supported selected adoption for previously initialized projects, including installations that already contain Curator but lack its ontology integration.
- Preservation, compatibility, recovery and observable completion behavior across those routes.
- Owner disposition of the reported pending maintenance, investigation of the staged Task response and lifecycle ownership, on-demand workbench verification, and fresh integrated health evidence.

## Out of scope

Performing implementation, repairs, Template updates, ontology publication, Task recovery or actual child-project adoption during this document capture. Document approval does not authorize those actions. Bulk updates to registered projects, restoration of the rejected TRD, replacement of historical setup receipts, new background AI, unattended scheduling, service or hook installation, dependency/model provisioning, Git activity, publication and deployment are outside this request's execution authority.

## Task requirements

### REQ-001 — Integrate Curator into the root project
- Requirement: The active Sys4AI depot root shall expose one coherent project-local Curator process through its governance, charter, configuration, owner entry points and ontology, using the root's actual project identity and current operating policy.
- Source: U01–U02; H01 missing ontology integration; G01 project identity and ownership; C01 application and session contracts.
- Acceptance: Root project guidance and ontology discovery identify the same Curator process, its configured project root and its supported owner routes; a bounded representative maintenance operation reaches the applicable current owner and produces attributable evidence under that owner's rules.
- Acceptance: File presence, policy validity or ontology label discovery alone cannot establish completion of root process integration.
- Depends on: REQ-002, REQ-003, REQ-009

### REQ-002 — Represent Curator functionality in the ontology
- Requirement: The ontology shall represent the supported Curator process and its meaningful functions, including policy inspection, scoped review, owner-routed update and correction, exact retry/recovery, Task pause/resume, selected dispatch, session catch-up and bounded log access.
- Source: U01–U02; C01 action inventory and session contract; O01 typed capability discovery.
- Acceptance: Ontology queries can identify what each represented function does, its inputs and outputs, responsible owner, affected scope and prerequisites, with references to the installed governing source; unsupported operations are not presented as available.
- Acceptance: The representation distinguishes Curator coordination from the canonical Task, memory, ontology and integration operations it coordinates. A name-only Curator capability entry fails acceptance.
- Depends on: None.

### REQ-003 — Make relationships and current sources discoverable
- Requirement: Curator ontology knowledge shall connect the process to project identity, governing skills and roles, Task lifecycle/current ownership, memory, ontology and maintenance obligations, with typed relationships and inspectable source provenance.
- Source: U01–U02; C01 fixed owner routes; O01 current-authority retrieval and source-version contracts; G01 canonical ownership boundaries.
- Acceptance: Bounded capability, relationship and current-authority queries answer what Curator maintains, which owner controls a selected action, what triggers evaluation, and which source governs the result; outputs identify the exact source/version context and preserve ambiguity, missing-source and stale-source diagnostics.
- Acceptance: Capability declaration, installation, configuration, authorization, compatibility, runtime observation, pending work and completed owner outcomes remain distinguishable. A historical ontology statement or memory record cannot replace a current owner/authority check.
- Acceptance: Relevant generated ontology indexes, wiki and memory links remain consistent with the selected canonical Curator knowledge through their existing explicit maintenance operations; retrieval itself performs no repair or canonical write.
- Depends on: REQ-002

### REQ-004 — Deliver complete neutral capability through the Template
- Requirement: Reusable source collections and the registered Sys4AI Template shall contain the complete Curator project and ontology capability needed for destination specialization through the supported initializer.
- Source: U01–U02; G01 reusable-asset ownership; T01 Template distribution and neutral configuration; D01 current empty starter graphs.
- Acceptance: The reviewed source-to-Template inventory accounts for the functional ontology content, bindings or specialization inputs, owner interfaces and project-session assets required by REQ-002 and REQ-003; source and Template checks detect omitted or incompatible integration resources.
- Acceptance: The Template retains neutral project identity, unbound publication authority and disabled session operation. It contains no root-specific live owner, maintenance backlog, learned record, project-instance claim or runtime evidence, while still supplying the complete reusable integration.
- Acceptance: Reusable changes originate in their owning source collections and reach only the registered Template through its checked update pipeline; root adoption and selected destination adoption remain distinct operations.
- Depends on: REQ-002, REQ-003

### REQ-005 — Complete both integrations during new-project creation
- Requirement: Supported Sys4AI new-project creation shall deliver Curator project wiring and its functional ontology integration together as part of the same successful initialization workflow.
- Source: U01–U02; I01 create route, destination specialization and starter assessment; T01 Template as the sole starter source.
- Acceptance: A representative new project created from the reviewed Template has destination-consistent Curator and ontology identity, source bindings, local owner routes and the discoverable functions/relationships in REQ-002 and REQ-003, without a separate manual ontology-integration step.
- Acceptance: The resulting project has session maintenance enabled by the selected installation policy, subject to an explicit destination opt-out; its neutral runtime and service choices are preserved. Setup evidence distinguishes static readiness from a separately observed live session.
- Depends on: REQ-004, REQ-008, REQ-009

### REQ-006 — Complete both integrations during first existing-project preparation
- Requirement: First-time Sys4AI preparation of a selected existing project shall supply the same integrated Curator process and ontology functionality while preserving the destination's established identity, authored content and explicit configuration choices.
- Source: U01–U02; I01 prepare-existing route, manual Template-copy specialization and whole-package preservation; G01 destination ownership.
- Acceptance: Representative first preparation of an existing project and of an unspecialized Template copy yields the functional project and ontology integration required by REQ-002 and REQ-003, specialized to that destination, without a further manual ontology step.
- Acceptance: Existing customizations and opt-outs remain intact. When preserved content prevents compatible integration, the workflow identifies the exact blocked capability and required selected reconciliation instead of reporting healthy integrated setup.
- Depends on: REQ-004, REQ-008, REQ-009

### REQ-007 — Support selected adoption by previously initialized projects
- Requirement: Sys4AI shall provide a supported explicitly selected adoption or refresh route that completes Curator project and ontology integration for previously initialized projects, including those with an earlier Curator installation that lacks ontology integration.
- Source: U01–U02; I01 selected module adoption and historical setup contracts; G01 exact source/destination adoption boundaries.
- Acceptance: Representative prior initialized destinations can receive both parts of the integration through one supported selected workflow, with no separately omitted manual ontology-integration step; unavailable prerequisites or protected conflicts produce exact diagnostics and no false success.
- Acceptance: Original setup editions, source inventories and receipts remain unchanged historical evidence. New adoption evidence identifies the selected integration edition and current destination state separately, using the existing setup receipt/history mechanism.
- Acceptance: An ordinary rerun verifies its recorded edition without silently acquiring the new integration. Unselected registered projects remain untouched; an existing disabled setting remains disabled.
- Depends on: REQ-004, REQ-008, REQ-009

### REQ-008 — Preserve project data and recover exact setup operations
- Requirement: Integration setup and adoption shall preserve authored ontology and memory, Task history, project identity, licensing, custom packages, unrelated roles and explicit opt-outs, with exact change boundaries and recoverable operations.
- Source: G01 preservation and adoption rules; I01 ownership inventories, package conflicts, receipt provenance and same-request recovery; D01 authored ontology protection.
- Acceptance: Before/after comparison accounts for every intended integration addition or selected change and proves preservation of unrelated project-owned material. Compatible pre-existing knowledge remains usable without wholesale graph or package replacement.
- Acceptance: Customized, incompatible, partial or concurrently changed inputs produce attributable conflict or partial-operation evidence. Exact unchanged reruns resume or verify without duplicate capabilities, bindings or registrations; changed sources or destination edits cannot be replayed as an earlier approved operation.
- Acceptance: Existing session-disabled, capture-off and disabled publication choices survive preparation, adoption and reruns. No existing-project or ontology overwrite authority is inferred from file equality, directory location or registry membership.
- Depends on: None.

### REQ-009 — Preserve session triggers and canonical owner authority
- Requirement: Curator project behavior and ontology representation shall consistently describe bounded session-start/return collection, subsequent current-owner evaluation and separately authorized execution, preserving the configured session-only operating mode.
- Source: C01 session maintenance and action contracts; O01 separate ontology operations and publication grants; G01 sole canonical writer and Task activation boundaries.
- Acceptance: A representative enabled session records changed-input catch-up and routes eligible work through the applicable current owner within the configured bounds. Collection, admission, dispatch and completed owner outcomes are reported separately; unavailable owners or exhausted budgets retain pending work.
- Acceptance: Session checks and ontology queries do not create an unattended AI service, start a scheduler, invent a native actor, create a second canonical writer or acquire publication authority. Ontology discovery and saved memory do not themselves trigger canonical ontology updates.
- Acceptance: Existing disabled session choices remain effective, and operation-specific authority, exact source checks and current Task lifecycle gates remain enforced for manual and session-origin work.
- Depends on: None.

### REQ-010 — Resolve the reported pending owner maintenance
- Requirement: The root's pending Curator catch-up obligations identified by the health report shall receive current-owner disposition based on fresh bounded evidence and current source/ownership checks.
- Source: H01 pending owner work; C01 delivery retention and completed-outcome consumption; G01 current Task reuse and ownership.
- Acceptance: Each still-relevant reported obligation is traced to its current delivery and owning workflow, then either completed with an attributable canonical owner receipt or retained with a specific blocker, owner and next eligible action. Already completed or superseded items retain their supporting history.
- Acceptance: A delivery is consumed only after its completed owner outcome. Metadata row counts and partial path pages are not represented as failure counts, full source validation or completed maintenance; source drift requires a fresh observation.
- Depends on: REQ-009

### REQ-011 — Reconcile the staged Task response through its owner
- Requirement: The reported staged response under the cancelled historical Curator Task shall be investigated through the Task owner, with any lifecycle or native-write-ownership mismatch reconciled before a supported recovery or cleanup disposition.
- Source: H01 old Task transaction warning; G01 Task ownership, lifecycle reconciliation and history preservation; installed Task and Agent Task contracts listed in the source manifest.
- Acceptance: The investigation identifies the exact current staged artifact, related transaction evidence, canonical Task revision/status and known write-owning assignments. It records whether the artifact is recoverable, already represented or requires a specific owner action without inferring safety from age, cancellation or roster absence alone.
- Acceptance: Any authorized disposition uses the supported exact Task operation, preserves response history and unrelated work, and is followed by rereading the canonical Task state and running validation. If the evidence or authority is insufficient, the artifact remains preserved with a precise blocker; no Task is falsely completed or silently reopened.
- Depends on: None.

### REQ-012 — Verify the selected on-demand ontology workbench
- Requirement: The root health follow-up shall establish actual local browser behavior for the selected on-demand ontology workbench and report its operating state accurately without requiring an always-on service.
- Source: H01 advanced ontology workbench evidence gap; O01 selected profile, private session and workbench service boundaries.
- Acceptance: A separately authorized on-demand verification opens the selected local workbench and exercises a representative read/navigation flow against the intended root. It records the observed result and safe lifecycle disposition while protecting the private session token.
- Acceptance: Health evidence distinguishes not running, not assessed, observed operational and failed behavior. An absent endpoint alone is not classified as a failed service, and read/navigation evidence does not imply guarded writes or canonical publication passed.
- Depends on: None.

### REQ-013 — Preserve healthy memory and ontology behavior
- Requirement: The integration and report follow-up shall preserve the working root memory retrieval, ontology core/backend behavior and their independent data, configuration and authority boundaries.
- Source: H01 passed memory retrieval and ontology diagnostics; O01 memory/ontology separation; G01 protected project state.
- Acceptance: Fresh applicable health checks and a bounded actual memory retrieval demonstrate no integration regression against the previously working behavior, including canonical validity, relevant source freshness, projections and memory links.
- Acceptance: Existing authored facts, accepted memory records, capture settings and locked imports retain their meaning and provenance. Unrelated backends, schemas, runtimes and publication grants are not changed to make the integration appear healthy.
- Depends on: None.

### REQ-014 — Report integration success with inspectable evidence
- Requirement: Final integration reporting shall cover root, reusable sources, neutral Template and each supported initialization/adoption route, relating every requirement and health finding to current evidence and explicit limits.
- Source: U01–U02; H01 verification limits; G01 completion standard; I01 separate installed/configured/authorized/compatible/runtime-observed assessment.
- Acceptance: Evidence demonstrates functional ontology queries and coherent project wiring in the root and representative new, first-prepared and prior-initialized destinations; Template evidence proves neutral reusable completeness. Each route rejects file-install-only or missing-ontology success.
- Acceptance: The report separates static contract checks, fixture checks, actual owner execution, browser observation and end-to-end setup behavior. It identifies any remaining blocker or unexercised behavior without describing the associated requirement as satisfied.
- Acceptance: Current hashes, source/destination scope, receipts and final state support the reported result. The dated health report remains preserved, and no fixture or configured flag is substituted for a live observation.
- Depends on: REQ-001, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013

## Decisions

- The expanded user request defines functional integration across the root, Template and all supported selected setup routes. It supersedes the narrower rejected capture without restoring that document or treating it as authority.
- The Template stays neutral while supplying complete reusable Curator semantics and the inputs needed for destination binding. Root-specific facts and runtime evidence belong to their owning project. This follows the existing Template contract and the user's requirement for reusable integration.
- The current initializer's neutral-graph checks and authored-ontology preservation explain why the required outcome needs coordinated reusable and initializer support. Ontology term identifiers, module packaging/versioning, specialization mechanics, exact compatible adoption/refresh interface and the appropriate future setup edition remain implementation-planning choices within the stated functional and preservation constraints. They are not missing user requirements.
- Existing-project coverage includes first preparation and explicitly selected adoption or refresh for earlier initialized projects. Ordinary reruns retain historical editions and explicit opt-outs; registration grants no bulk update authority.
- The report identifies evidence gaps and pending obligations, not proved backend failures. Fresh owner-led diagnosis determines the supported repair or disposition without inventing a defect or forcing an always-on service.
- This requirements capture grants no repair, service-start or adoption execution authority. A future implementation or verification request must carry the applicable action scope; exact document approval establishes the requirements baseline only.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
