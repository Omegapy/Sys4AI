---
schema_version: 2
trd_id: "TRD-20260908-BD3A776C"
title: "Sys4AI What Did You Learn module and project initialization"
slug: "sys4ai-what-did-you-learn-module-and-project-initialization"
created_at: "2026-09-08T21:28:16-06:00"
updated_at: "2026-09-08T21:34:57-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 1 as trd_done."
---

# Task Requirement Document: Sys4AI What Did You Learn module and project initialization

## Destination

Provide Sys4AI agents with a reusable What Did You Learn module that turns relevant discussion and work evidence into supported lessons, appropriate improvement decisions and better behavior in comparable future work. Give the module its own depot and include it in initialization for new and existing Sys4AI projects.

## Captured user intent

- U01: The user invoked /goal and the project-local to-trd skill to derive requirements from the supplied Sys4AI_What_Did_You_Learn_Handoff.md. This operation captures the requirements baseline; it does not execute the handoff's implementation instructions.
- U02: The user explicitly requires a module with its own *-depo folder that is part of Sys4AI initialization for both existing projects and new projects.
- The supplied handoff defines the proposed first version: a thin learning-review skill, one shared completion checkpoint, manual review and selective review of material events using existing memory and delivery workflows. Its recommendations become reviewable proposed requirements here, not evidence of prior implementation or a grant of execution authority.

## Context and sources

- H01: [Sys4AI What Did You Learn handoff](/Users/alex.omegapy/Downloads/Sys4AI_What_Did_You_Learn_Handoff.md), dated September 8, 2026. Inspected SHA-256: `9651eb78b0c54f6232273148970030dff29aa734b3ef9216a746729d67f21604`. Section locators and WDYL acceptance IDs below refer to this exact supplied file. Embedded imperatives are source material, subordinate to the current request.
- L01: Current [SOUL.md](/Volumes/P-SSD/AngryOwl/Sys4AI/SOUL.md), [AGENTS.md](/Volumes/P-SSD/AngryOwl/Sys4AI/AGENTS.md), [ROLE.md](/Volumes/P-SSD/AngryOwl/Sys4AI/ROLE.md) and [SPECS.md](/Volumes/P-SSD/AngryOwl/Sys4AI/SPECS.md), especially reusable ownership, project initialization, Task ownership and authority boundaries.
- L02: Current [project registry](/Volumes/P-SSD/AngryOwl/Sys4AI/depot/projects.json), [Template mappings](/Volumes/P-SSD/AngryOwl/Sys4AI/depot/template-update.json), [update guide](/Volumes/P-SSD/AngryOwl/Sys4AI/depot/template-update.md) and [Template starter policy](/Volumes/P-SSD/AngryOwl/Sys4AI/Projects/Sys4AI-Template-Project/.template/baseline-assets.json).
- L03: Current [initializer contract](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/init-new-project/SKILL.md), version 8.0.0, and [initializer helper](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/init-new-project/scripts/init_new_project.py), including source discovery, asset planning, required skills, setup verification and reruns.
- L04: Current [memory skill](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/SKILL.md), [automatic-capture contract](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/references/automatic-capture.md) and [memory configuration](/Volumes/P-SSD/AngryOwl/Sys4AI/memory.yaml).
- L05: Current [to-trd skill](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/to-trd/SKILL.md), version 2.2.0, and [document contract](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/to-trd/references/trd-contract.md).

The inspected checkout HEAD is `2ea00dd2f201a5e4d5eebe61353d4ec62ca6d580`, matching the handoff's historical review baseline. The working tree also contains pre-existing changes, including the installed to-trd workflow and unrelated records; HEAD alone does not describe those current bytes. The local registry lists the depot and registered Template, and the inspected reusable collections contain no dedicated learning depot or what-did-you-learn package.

Current memory configuration enables automatic capture. Its existing four capture triggers are work-completed, task-completed, decision-recorded and failure-observed; these describe existing helper support, not guaranteed runtime event detection. The initializer uses governance-starter-v6, draws its assets from the Template, and preserves prior-edition receipts and project-owned packages. Ordinary reruns do not adopt a later Template edition, which makes REQ-023 necessary.

The attachment's external research and runtime-hook references are background as supplied. They were not independently revalidated for this document; no current hook compatibility, live memory-backend health or implemented learning behavior is claimed.

## In scope

- A distinct reusable learning module with substantive assets in its own *-depo collection, a discoverable what-did-you-learn skill and one shared memory completion procedure.
- Explicit review, meaningful work and discussion checkpoints, evidence evaluation, memory publication under current grants, improvement disposition and later relevant recall and evaluation.
- Existing project and Task ownership, frozen solver inputs, privacy, non-mutating reads, capture opt-out, idempotency and recovery.
- Reusable source and Template integration, scoped active-depot adoption, new-project initialization, preparation of a selected existing project, and a supported module adoption route for a selected previously initialized project.
- Compatible dependency checks, preserved project customizations and memory history, destination-local setup provenance, and representative behavioral verification.

## Out of scope

- A second memory database or learned-record directory, second Task or setup ledger, new permanent learning manager, new mandatory agent team, or model-weight training.
- Per-message reflection, an inactivity scheduler, background consolidation, a transcript recorder, and a runtime-hook adapter in this first version. H01 explicitly places hooks and delayed processing after the core workflow; WDYL-H1 and WDYL-H2 therefore remain outside this baseline.
- Automatic propagation into unspecified projects, treating registry membership as adoption authority, overwriting customized project packages without scoped authorization, or moving one project's learned history into another project or the Template.
- Unnecessary schema or trigger extensions, backend provisioning, dependency installation, restoration of retired systems, service deployment, Git publication, external tickets or other external action.
- Implementation, project initialization, memory publication or downstream plan creation during this to-trd operation. Approval of this document establishes the requirements baseline only.

## Task requirements

### REQ-001 - Own a dedicated reusable module depot
- Requirement: Package What Did You Learn as a distinct Sys4AI module with its own top-level source collection whose name ends in -depo; a skill placed only inside SKILLS-depo is insufficient.
- Source: U02; H01 sections 1 and 8; L01 reusable-source ownership.
- Acceptance: The dedicated depot contains the module's substantive policy, review contract and lesson-body assets, with documented boundaries and dependencies; it is not an empty folder or a competing learned-record store.
- Acceptance: The reusable what-did-you-learn skill follows the existing SKILLS-depo package convention and references the module's canonical assets without maintaining conflicting copies of its policy.
- Depends on: None.

### REQ-002 - Use one learning and memory completion workflow
- Requirement: Provide a thin what-did-you-learn skill that identifies and evaluates lessons while the existing memory capability owns persistence, retrieval and lifecycle operations through one shared completion checkpoint.
- Source: U01; H01 sections 1, 5, 6.1 and 8.1; L04.
- Acceptance: A substantive completion invokes one coordinated learning review and publication path, even when both skills are installed.
- Acceptance: The module adds no second memory system, Task ledger, scheduler, permanent management role or mandatory review team.
- Depends on: REQ-001

### REQ-003 - Support explicit learning review
- Requirement: Respond to an explicit What did you learn request with a bounded evidence-based review of the relevant discussion or work, including an honest no-durable-lesson result when appropriate.
- Source: U01; H01 sections 4.1 and 5; WDYL-02.
- Acceptance: A manual review identifies supported lessons, applicability and limits, or explains that nothing durable was found.
- Acceptance: The review request alone does not authorize persistence or project changes; a requested save uses the established memory route only within applicable scope.
- Depends on: REQ-002

### REQ-004 - Review material work and discussion events
- Requirement: Evaluate learning at substantive work completion, tracked Task completion, settled substantive decisions, clear material user corrections, significant observed failures or violated constraints, and verified reusable successes.
- Source: U01; H01 sections 4.1, 4.2 and 14; L04.
- Acceptance: Completion review occurs after relevant verification and before the final handoff; Task review uses the timing and owner in REQ-018.
- Acceptance: Material corrections, failures, decisions and successes receive review when they could change future work; routine messages, isolated typos and temporary progress do not require a durable lesson.
- Acceptance: A reproduced defect or confirmed requirement can warrant action without recurrence; speculative generalization retains its uncertainty instead of relying on an invented numeric threshold.
- Depends on: REQ-002

### REQ-005 - Wait for settled meaning and preserve pending evidence
- Requirement: Use resolved-topic checkpoints during long discussions and preserve permitted pending evidence at planned handoff, interruption or context-compaction boundaries without prematurely treating unresolved discussion as accepted intent.
- Source: U01; H01 sections 4.3 and 9; WDYL-08.
- Acceptance: An unfinished correction or clarification remains unsettled; silence and a quiet period do not establish acceptance.
- Acceptance: A known handoff or compaction checkpoint preserves only concise, authorized evidence or draft findings and does not start an expansive improvement exercise.
- Acceptance: The workflow does not depend on every final-turn hook executing; unavailable interruption detection is reported as a limit.
- Depends on: REQ-004

### REQ-006 - Keep ordinary inspection non-mutating
- Requirement: Keep ordinary status, list, lookup and inspection-only requests read-only throughout the learning integration.
- Source: U01; H01 section 4.4; WDYL-01; L04.
- Acceptance: Representative read-only operations leave memory records and indexes, Task state, project artifacts and configuration unchanged.
- Acceptance: Reading a source or inspecting setup readiness does not install a backend, activate a Task or run a hidden learning persistence path.
- Depends on: REQ-002

### REQ-007 - Honor capture settings and user opt-out
- Requirement: Use the existing automatic_capture setting to control automatic persistence, preserve an existing off preference, and retain explicit review and authorized save behavior when automatic capture is off.
- Source: U01; H01 section 4.4; WDYL-06; L03 and L04.
- Acceptance: With automatic capture off, material events cause no automatic persistence under either the memory or learning skill name.
- Acceptance: An explicit review remains available, and an explicitly requested save still satisfies normal evidence and publication checks.
- Acceptance: A new compatible installation follows the existing default-on setup policy and reports the actual setting; setup and adoption preserve an existing opt-out.
- Depends on: REQ-006

### REQ-008 - Establish project and evidence boundaries
- Requirement: Establish the real owning project, responsible Director or confirmed Task manager, relevant work unit, current configuration, applicable authority and exact relevant sources before evaluating a candidate lesson.
- Source: U01; H01 section 5 steps 1 and 2; L01 and L04.
- Acceptance: A review distinguishes the expected result, actual observation and proposed explanation using inspected artifacts.
- Acceptance: Ordinary work retains null Task and execution origins; directory names and role names do not manufacture project ownership or native identities.
- Depends on: REQ-002

### REQ-009 - Support claims with attributable evidence
- Requirement: Give each proposed lesson evidence appropriate to its claim, with real source versions and locators, and distinguish accepted decisions, verified outcomes, observed failures and unverified causal explanations.
- Source: U01; H01 section 5 steps 2 and 5; WDYL-07, WDYL-08 and WDYL-15; L04.
- Acceptance: An observed failing test is not presented as proof of its suspected cause; confidence does not upgrade a hypothesis into a verified fact.
- Acceptance: When discussion is the only evidence and capture is authorized, a concise attributed local decision or evidence record satisfies the current memory contract; a conversation reference alone is not treated as sufficient.
- Acceptance: Missing hashes, source locators, publication receipts and Task origins are never fabricated; unsupported candidates remain unpublished or appropriately limited.
- Depends on: REQ-008

### REQ-010 - Select useful lessons and resolve duplicates or conflicts
- Requirement: Accept only useful, supported and applicable findings after comparing them with current authoritative sources and accepted project memory, including duplicate and contradiction handling.
- Source: U01; H01 section 5 steps 3 and 4; WDYL-03, WDYL-05 and WDYL-09.
- Acceptance: A completed review may save nothing; it rejects trivial, temporary, redundant and unsupported candidates without manufacturing a lesson.
- Acceptance: Additional evidence for an existing lesson is distinguished from a new lesson; contradictory evidence uses the supported review, supersession or retraction lifecycle and retains history.
- Acceptance: The lesson states how a future agent should perform similar work differently and under which conditions; a single success is not generalized into universal reliability.
- Depends on: REQ-009

### REQ-011 - Use the existing lesson schema and helper interface
- Requirement: Store accepted lessons in the owning project's MEMORY directory through the current memory record contract and helper, with learning-specific explanation in the Markdown body.
- Source: U01; H01 sections 6.1, 6.2 and 8.2; WDYL-16; L04.
- Acceptance: A lesson body covers observation, evidence, lesson and applicability, limitations, improvement disposition, and validation or follow-up references.
- Acceptance: Records use valid current fields, claim levels and lifecycle states; helper calls use supported commands and trigger values with their actual meanings.
- Acceptance: Finer event distinctions use supported body or evidence content; no unsupported event value, frontmatter field or second implementation-progress state machine is introduced.
- Depends on: REQ-010

### REQ-012 - Keep publication with the authorized owner
- Requirement: Publish only owner-reviewed exact record bytes within the current scoped memory grant, using the existing memory helper and its required identity and version checks.
- Source: U01; H01 section 5 step 6 and sections 7.1 and 7.2; WDYL-04 and WDYL-10; L04.
- Acceptance: Children return proposals through their assigned result artifacts; those proposals enter no shared active recall until the responsible owner reviews and publishes them.
- Acceptance: The Director or confirmed manager verifies the publication receipt and resulting canonical record before reporting a save.
- Acceptance: Publication within an existing grant does not require redundant per-note approval; rejected publication is not bypassed by rewriting grants, authority hashes or configuration.
- Depends on: REQ-011

### REQ-013 - Recover publication without duplicate or false completion
- Requirement: Retain the existing retry and recovery semantics and distinguish optional capture failure from failure of a required memory deliverable.
- Source: U01; H01 section 5 step 6 and section 7.3; WDYL-05 and WDYL-19; L04.
- Acceptance: Retries reuse the existing operation identity where required and do not create duplicate active records after repeated delivery or a partial publication.
- Acceptance: The result reports the exact observed failure or committed boundary; it never reports an unsaved proposal as saved.
- Acceptance: Optional capture failure does not falsely invalidate accepted work; required publication remains incomplete on failure, and memory recovery neither reopens terminal Tasks nor replays committed Task events.
- Depends on: REQ-012

### REQ-014 - Give every accepted lesson an improvement disposition
- Requirement: Decide whether an accepted lesson needs contextual recall only, a targeted artifact improvement, or further investigation.
- Source: U01; H01 section 4.5 and section 5 step 7.
- Acceptance: A targeted proposal names the exact owning project and artifact, intended behavior, reason, preservation boundary and observable validation criteria.
- Acceptance: An unsupported cause or benefit produces a bounded investigation disposition rather than an asserted fix.
- Acceptance: Accumulated lessons can be reviewed at an existing milestone or an explicitly requested retrospective without an independent scheduler or a mandatory exercise after every small event.
- Depends on: REQ-010

### REQ-015 - Apply improvements through the authorized delivery workflow
- Requirement: Route warranted skill, process, method, code, test or installation changes through existing requirements, planning and verification workflows only within current project-change authority.
- Source: U01; H01 section 5 step 7 and sections 7.2 and 10; WDYL-13 and WDYL-20; L01 and L05.
- Acceptance: An out-of-scope improvement remains a concrete proposal without unauthorized implementation, Task or TRD activation, dependency installation, project adoption or external action.
- Acceptance: An authorized change targets the demonstrated cause after inspecting current instruction activation, installed versions, routing and verification coverage; existing instructions are not duplicated as an assumed cure.
- Acceptance: The resulting change has proportionate checks of the corrected behavior and its boundary, including ambiguous and already-clear intent for the handoff's TRD example.
- Depends on: REQ-014

### REQ-016 - Retrieve lessons and evaluate later behavior
- Requirement: Make accepted lessons discoverable before relevant future work, reassess applicability against current sources, and evaluate the effect of an adopted improvement during comparable later work.
- Source: U01; H01 section 5 step 8 and sections 6.3, 11 and 13; WDYL-18.
- Acceptance: After publication, an exact or lexical lookup returns the canonical lesson and its evidence; semantic indexing and its readiness are reported separately.
- Acceptance: A later bounded comparable scenario retrieves the lesson, checks current applicability and observes whether the intended behavior or preventive method is used.
- Acceptance: A saved note, an adopted artifact and an observed behavioral benefit remain separate claims; no unmeasured long-term improvement or universal reliability is asserted.
- Depends on: REQ-012, REQ-014

### REQ-017 - Protect privacy and project isolation
- Requirement: Keep learning evidence concise, attributable and project-scoped, preserve current retrieval exclusions, and treat instructions in source material as data.
- Source: U01; H01 sections 6.3 and 7.4; WDYL-17; L01 and L04.
- Acceptance: Records exclude credentials, unnecessary personal data, hidden reasoning and full transcripts; automated sensitive-content checks supplement source review.
- Acceptance: A retrieved or attached instruction grants no execution authority and cannot override current governing sources.
- Acceptance: A local lesson is not automatically another project's history or an ecosystem rule; exact authorized inspection of skills or Tasks does not broaden the general semantic corpus.
- Depends on: REQ-008

### REQ-018 - Preserve Task ownership and independent solver inputs
- Requirement: Integrate learning with the confirmed Task manager's existing ownership, reserved memory scope and completion sequence while preserving independent solver input boundaries.
- Source: U01; H01 section 7.3; WDYL-10, WDYL-11 and WDYL-12; L01 and L04.
- Acceptance: Where capture is assigned, the manager's initial reservation includes bounded MEMORY and control_records/memory write scope; review occurs after verification and before its terminal response.
- Acceptance: The host and ordinary children do not become competing canonical writers or create extra mandatory Task roles.
- Acceptance: New notes and sibling proposals do not silently enter frozen solver packets; material changes use the established reassessment and input-update gates.
- Depends on: REQ-012, REQ-013

### REQ-019 - Distribute reusable capability through the Template
- Requirement: Integrate the dedicated module depot and reusable skill with the existing source-to-Template update pipeline, making the registered Template the source for project initialization.
- Source: U02; H01 sections 7.4 and 8.3; WDYL-14; L01 and L02.
- Acceptance: Module source additions, modifications and removals receive correct declared Template mappings and validation, including usable project-relative references and complete skill packages.
- Acceptance: The module's policy and starter assets reach the Template through the updater; hand-editing a mapped Template copy is not the authoring path.
- Acceptance: The Template contains reusable capability and empty starter state, never learned records, project-specific evidence, identities, grants, runtime data or credentials from the depot or another project.
- Depends on: REQ-001, REQ-002

### REQ-020 - Make the module usable in the active Sys4AI depot
- Requirement: Include scoped adoption into the active Sys4AI depot's local skills and applicable governance so the owning system can use the same learning module it distributes.
- Source: U01 and U02; H01 section 8.3 identifies active-root integration; L01.
- Acceptance: The active root's adopted module assets, skill and shared completion references match their declared reusable versions or explicitly preserved local adaptations.
- Acceptance: Adoption names exact source and destination files, verifies the final local result and preserves unrelated root edits, Tasks, memory records and registry metadata.
- Acceptance: Template currency alone is not reported as active-root adoption or working learning behavior.
- Depends on: REQ-019

### REQ-021 - Include the module in new-project initialization
- Requirement: Include the complete learning capability and its required memory integration by default in Sys4AI's create initialization route for a selected new project.
- Source: U02 explicitly requires initialization of new projects; L02 and L03.
- Acceptance: A newly initialized project receives the module's usable skill, contracts and required governance references entirely from the registered Template, with destination-local paths and identity.
- Acceptance: The initialized agent can find the manual learning workflow and the shared completion procedure without referring back to depot-owned runtime paths.
- Acceptance: A missing required module starter or incompatible dependency is diagnosed rather than reported as successful complete module setup.
- Depends on: REQ-019

### REQ-022 - Include the module when preparing an existing project
- Requirement: Include the learning module in prepare-existing initialization for a selected existing project or manual Template copy while preserving project-owned content.
- Source: U02 explicitly requires initialization of existing projects; L01 and L03.
- Acceptance: A selected project with no prior Sys4AI receipt receives missing compatible module assets and working project-local references during preparation.
- Acceptance: Customized README, specifications, skills, roles, Tasks, code, licensing, configuration, memory records and independent repository state remain preserved within the established package boundaries.
- Acceptance: A customized module or dependency package is assessed as a whole; incompatible or missing internal resources do not trigger silent edition mixing, overwrite or a false readiness claim.
- Depends on: REQ-019

### REQ-023 - Support adoption by previously initialized projects
- Requirement: Provide a supported, explicitly selected module adoption or refresh path within existing-project initialization for projects whose earlier setup receipts predate the learning module.
- Source: U02; L03 explicitly preserves earlier editions and does not upgrade them on equivalent rerun.
- Acceptance: A representative previously initialized project can acquire the module through a documented scoped operation; merely reporting its old setup complete does not satisfy module adoption.
- Acceptance: Ordinary equivalent reruns keep their original contract and history; module adoption records its new scope and provenance without relabeling or deleting the earlier receipt.
- Acceptance: Customizations, user opt-out and learned records are preserved; incompatible packages receive a precise scoped adoption requirement rather than an automatic bulk upgrade.
- Acceptance: No unspecified product project is updated merely because it is registered, adjacent, or uses similar files.
- Depends on: REQ-022

### REQ-024 - Verify compatible dependencies without provisioning a runtime
- Requirement: Check that an adopted learning module has compatible installed memory, governance and initialization interfaces, and report actual capability separately from runtime or backend readiness.
- Source: U01 and U02; H01 sections 2, 8.2, 9 and 11; L03 and L04.
- Acceptance: Preparation verifies module assets, resolvable local references, valid configuration and supported helper interfaces; a preserved incompatible installation is identified accurately.
- Acceptance: Setup, review and readiness inspection do not install packages, download models, initialize a backend service, add runtime hooks or create external infrastructure.
- Acceptance: The learning workflow remains usable through explicit and instruction-based checkpoints without a hook adapter or semantic backend; any narrower readiness limitation is stated.
- Depends on: REQ-021, REQ-022, REQ-023

### REQ-025 - Preserve destination-local memory settings and authority
- Requirement: During initialization or adoption, retain existing memory and capture preferences and bind any newly installed memory capability only to its owning destination under the established setup authority contract.
- Source: U02; H01 sections 4.4, 6 and 7; L03 and L04.
- Acceptance: A new project receives empty learned state and destination-local identity and authority; it receives no source project's notes, grants, operation journal or runtime.
- Acceptance: An existing project's memory records and configuration, including automatic capture off, remain intact; unchanged compatible memory is reused.
- Acceptance: Setup reports the verified capture setting and any preserved incompatibility, follows the current opt-out notice, and does not treat a true flag alone as successful publication readiness.
- Depends on: REQ-007, REQ-024

### REQ-026 - Record and recover module initialization accurately
- Requirement: Extend existing setup provenance and recovery mechanisms to account for learning-module adoption, preservation and verification without introducing a competing setup ledger.
- Source: U02; L03 completion, receipts, reruns and recovery; H01 sections 11 and 13.
- Acceptance: Setup evidence identifies source version or hashes, exact destination assets, adopted versus preserved or skipped content, checks and actual module readiness.
- Acceptance: Equivalent completed reruns create no duplicate registration or unintended asset upgrade and preserve normal project edits.
- Acceptance: Interrupted adoption resumes through checked existing recovery principles; changed inputs or conflicting destination edits are reported without deleting history or overwriting project content.
- Depends on: REQ-021, REQ-022, REQ-023

### REQ-027 - Verify the integrated learning and initialization behavior
- Requirement: Verify the module against the handoff's core acceptance scenarios and representative new-project, existing-project and prior-edition adoption cases with evidence appropriate to each behavior.
- Source: U01 and U02; H01 sections 11 and 12; L01.
- Acceptance: Coverage accounts for WDYL-01 through WDYL-20 using the mapping in Decisions, including no useful lesson, duplicate, opt-out, uncertain cause, unauthorized save, frozen solver inputs and optional publication failure.
- Acceptance: A bounded authorized learning scenario exercises review, publication, canonical receipt inspection, retrieval and improvement disposition; an in-scope improvement is tested when the scenario calls for one.
- Acceptance: Initialization checks cover a new project, a customized existing project, a prior setup receipt, capture off, incompatible preserved dependencies, rerun and interrupted adoption.
- Acceptance: Verification distinguishes static checks, helper fixtures, actual agent behavior, backend retrieval and later comparable use; an unexercised required behavior remains explicit and is not marked passed.
- Depends on: REQ-013, REQ-015, REQ-016, REQ-018, REQ-020, REQ-024, REQ-025, REQ-026

### REQ-028 - Document use and report verified outcomes
- Requirement: Document module ownership, manual and automatic behavior, initialization and adoption routes, dependencies, preservation rules and the evidence required for truthful completion.
- Source: U01 and U02; H01 sections 8, 11, 12 and 13; L01 through L04.
- Acceptance: A user can locate the dedicated module depot and follow the documented route for new setup, first preparation and previously initialized-project adoption.
- Acceptance: The implementation handoff identifies changed source, Template and active-project paths, actual acceptance results, publication and retrieval results, adoption status and remaining limitations.
- Acceptance: Instruction-based checkpoints, any future runtime-enforced events and unsupported detection are labeled accurately; optional hook checks WDYL-H1 and WDYL-H2 are not reported passed when hooks are excluded.
- Depends on: REQ-027

## Decisions

1. **The direct module requirement extends the handoff.** H01 proposes a package under SKILLS-depo. U02 additionally requires a substantive dedicated *-depo collection. REQ-001 retains the existing skill-discovery convention while giving the module its own policy and asset ownership.
2. **Naming and internal arrangement remain bounded implementation choices.** `LEARNING-depo/` is a proposed collection name, not a fixed user-specified spelling. Planning may select its exact name and file layout while retaining a distinct top-level *-depo folder, one canonical module policy, usable project-local assets and the what-did-you-learn entry point. The installer edition number, internal APIs and exact checked adoption mechanism can also be chosen within REQ-019 through REQ-026.
3. **Existing projects include projects already initialized.** U02 requires both new and existing-project initialization. Because L03 preserves earlier editions on ordinary reruns, a complete solution must support both first preparation and explicit module adoption for earlier receipts. This requires a capability and a representative verification scenario; it does not select or authorize modification of an unspecified production project.
4. **First-version reliability is based on the existing agent workflow.** H01 sections 1, 9 and 11 explicitly defer runtime hooks and background processing. Core review, publication, retrieval and initialization must work without them. Describing a completion instruction as a guaranteed runtime hook would misstate the result.
5. **Current memory behavior remains authoritative.** The module reuses supported record, trigger, publication and lifecycle contracts. Finer event meaning belongs in valid evidence and body content. A new event enum or schema is not an intake requirement merely because several trigger occasions are described.
6. **Behavioral improvement requires separate evidence.** Record generation, successful memory publication, adopted changes and observed later behavior are distinct outcomes. REQ-016 and REQ-027 require a bounded comparable-use check without inventing a quantitative benefit or a long-term reliability target.
7. **Authority remains operation-specific.** The supplied recommendations and this baseline do not activate project execution. Once implementation or selected-project adoption is separately authorized, existing scope and helper checks govern it; no redundant approval is needed for actions already covered.

Core handoff acceptance coverage:

| Handoff checks | Requirement coverage |
| --- | --- |
| WDYL-01, WDYL-02, WDYL-03 | REQ-006, REQ-003, REQ-010 |
| WDYL-04, WDYL-05, WDYL-06 | REQ-012, REQ-010 and REQ-013, REQ-007 |
| WDYL-07, WDYL-08, WDYL-09 | REQ-009, REQ-005 and REQ-009, REQ-010 |
| WDYL-10, WDYL-11, WDYL-12 | REQ-012 and REQ-018, REQ-018, REQ-018 |
| WDYL-13, WDYL-14, WDYL-15 | REQ-015, REQ-019 through REQ-023, REQ-009 |
| WDYL-16, WDYL-17, WDYL-18 | REQ-011, REQ-017, REQ-016 |
| WDYL-19, WDYL-20 | REQ-013, REQ-015 and REQ-027 |
| WDYL-H1, WDYL-H2 | Excluded optional hook adapter; no passing result asserted. |
| U02 dedicated module and initialization additions | REQ-001, REQ-019 through REQ-026, REQ-027 |

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
