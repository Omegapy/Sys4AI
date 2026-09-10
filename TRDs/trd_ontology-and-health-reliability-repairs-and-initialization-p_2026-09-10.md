---
schema_version: 2
trd_id: "TRD-20260910-F345F166"
title: "Ontology and health reliability repairs and initialization prevention"
slug: "ontology-and-health-reliability-repairs-and-initialization-p"
created_at: "2026-09-10T11:16:22-06:00"
updated_at: "2026-09-10T11:24:09-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 1 as the completed requirements baseline."
---

# Task Requirement Document: Ontology and health reliability repairs and initialization prevention

## Destination

Repair the ontology and health-diagnostic issues identified in the 2026-09-10 Sys4AI audit and prevent those failure classes from being silently introduced or reported as healthy by subsequent installations, project initialization, capability upgrades, or authorized runtime startup. The target is the current Sys4AI depot installation and its reusable source-to-Template delivery path.

## Captured user intent

U01: The user explicitly invoked to-trd, selected the full health report, and requested identification of the issues and why they happened, followed by requirements to fix them and prevent recurrence in new installations or system initiations. This document supplies that requirements baseline. Its approval does not execute the repairs.

The intended beneficiaries are the user and agents operating Sys4AI, health-command consumers, and projects receiving the reusable installation. System initiation covers the existing project creation/preparation/adoption/refresh/recovery routes and separately authorized runtime activation/startup. Prevention means correct setup, representative verification, and immediate truthful reporting of later invalidation; ordinary changes can make derived data stale, but that state must not be silently represented as operational readiness.

## Context and sources

- U01: The current user request, quoted in substance in Captured user intent.
- S01: [Verification/system-health-2026-09-10/REPORT.md](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/REPORT.md), component results and findings 1-4. SHA-256: `3a0fab73de4401d31a31f141d97d668b1d295b76c48844d08236209a13b374b4`.
- S02: [Verification/system-health-2026-09-10/regression/REPORT.md](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/REPORT.md) and [Verification/system-health-2026-09-10/regression/summary.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/summary.json). These distinguish direct discovery (120 passes, 9 fixture setup errors, 24 skips) from successful follow-ups covering all 153 distinct ontology tests, 34 focused memory tests, and 19 meaningful diagnostic controls. Regression report SHA-256: `1b9373b409b46fe0150970e9e5be178e2a4dd92d2d7a948dafc52cc8247ebc97`.
- S03: [Verification/system-health-2026-09-10/live/memory-evidence-audit.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/live/memory-evidence-audit.json), [Verification/system-health-2026-09-10/live/memory-health.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/live/memory-health.json), and [Verification/system-health-2026-09-10/live/ontology-health.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/live/ontology-health.json). These identify the exact current historical-evidence and generated-state findings.
- S04: [.agents/skills/ontology/scripts/ontology.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/scripts/ontology.py), `health` and CLI exit mapping; [.agents/skills/ontology/scripts/ontology_advanced_cli.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/scripts/ontology_advanced_cli.py), `advanced-health`; [.agents/skills/memory/scripts/memory_core.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/scripts/memory_core.py), `health`; [.agents/skills/memory/scripts/memory.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/scripts/memory.py), CLI exit mapping. These establish the incomplete aggregate status behavior.
- S05: [.agents/skills/memory/scripts/memory_evidence.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/scripts/memory_evidence.py), `_verification` and `inspect_evidence`; [.agents/skills/memory/scripts/basic_memory_projection.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/scripts/basic_memory_projection.py), `verify_projection`; [.agents/skills/memory/scripts/basic_memory_adapter.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/scripts/basic_memory_adapter.py), certificate and health checks; [.agents/skills/ontology/scripts/ontology_memory.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/scripts/ontology_memory.py), memory retrieval and derived-link freshness. These establish evidence, projection, and safe-retrieval behavior.
- S06: [.agents/skills/ontology/scripts/ontology_shacl.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/scripts/ontology_shacl.py), shape generation and full validation; [.agents/skills/ontology/scripts/ontology_limits.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/scripts/ontology_limits.py), finite budgets; [Verification/system-health-2026-09-10/live/ontology-shacl-idle.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/live/ontology-shacl-idle.json), actual idle-worker retest. The current query budget is 10 seconds; the existing configurable ceiling is 60 seconds. Neither value is a new user-specified performance target.
- S07: [.agents/skills/ontology/tests/guard_support.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/tests/guard_support.py), `DEPOT` and fixture installation; [Verification/system-health-2026-09-10/regression/selected_guard_regression.py](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/selected_guard_regression.py), verification-only root correction; S02 documents corrected macOS temporary-path controls and explicit actual-model selection.
- S08: [.agents/skills/init-new-project/SKILL.md](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/init-new-project/SKILL.md) and [.agents/skills/init-new-project/scripts/init_new_project.py](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/init-new-project/scripts/init_new_project.py), ontology/advanced assessment, edition preservation, completed setup, and recovery. Static installation, disabled neutral profiles, and runtime not-exercised are deliberately distinct.
- S09: [AGENTS.md](/Volumes/P-SSD/AngryOwl/Sys4AI/AGENTS.md), [ROLE.md](/Volumes/P-SSD/AngryOwl/Sys4AI/ROLE.md), [SPECS.md](/Volumes/P-SSD/AngryOwl/Sys4AI/SPECS.md), [depot/template-update.md](/Volumes/P-SSD/AngryOwl/Sys4AI/depot/template-update.md), and [depot/template-update.json](/Volumes/P-SSD/AngryOwl/Sys4AI/depot/template-update.json). These establish source ownership, exact adoption, Template-only automatic distribution, preserved project content, local authority, and current runtime constraints.
- S10: [.agents/skills/ontology/references/commands.md](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/references/commands.md) and [.agents/skills/memory/references/automatic-capture.md](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/references/automatic-capture.md). These establish explicit maintenance operations, read-only health behavior, and the separation of publication, evidence, runtime, and preferences.
- S11: Fresh read-only inspection on 2026-09-10 found no drift in the audit's governing/source digest set or inspected diagnostic code. The memory projection manifest at [.sys4ai/memory/projection/manifest.json](/Volumes/P-SSD/AngryOwl/Sys4AI/.sys4ai/memory/projection/manifest.json) still contains README SHA-256 `8b5a2aa24dda664ab49fc123a71d46c2a07b429a17a9341d8197800c2d23adc1`; current [README.md](/Volumes/P-SSD/AngryOwl/Sys4AI/README.md) is `86ffbf111360e30547e950bc04a2d922389312834ea4b2fd38c6f4888aee62d9`. Both projected memory-record bytes still match their recorded hashes. The ontology link manifest snapshot `1d5f7f78e4f0eb4929f4dfae1ff11dc623e4690959652c9903c6f145f65b8c24` differs from the current audited snapshot `813899a2caf6449a21bc86642dbe271c12c2a30cb244c84b6fece8deddce85b3`; helper and canonical input versions changed after those links were built.

| Issue | Observed cause and certainty | Required correction and prevention |
| --- | --- | --- |
| F1: Live SHACL timeout | Confirmed: the real root does not finish within its 10-second worker budget, including with audit regression workers idle. The exact expensive phase is not established. Small fixture success did not predict root-scale completion. | REQ-001 through REQ-004, REQ-028, REQ-029. |
| F2: Misleading health summary | Confirmed by code and isolated controls: core status omits generated-state failures, memory status omits returned evidence/backend errors, advanced status has no aggregate failure mapping, and guard/workbench entries report selection rather than operational checks. | REQ-005 through REQ-011, REQ-021, REQ-024, REQ-025. |
| F3: Historical memory evidence loses current support | Confirmed: the old receipt is intact, but its memory_capture.py and init_new_project.py artifact hashes differ from current files. The validator checks those live paths; later code versions therefore invalidate current verification of the old claim. This does not establish corruption or falsity of the historical observation. | REQ-012 through REQ-014. |
| F4: Stale memory projection and ontology associations | Confirmed: README content differs from the memory projection; the ontology association snapshot predates changed ontology code and inputs. Existing read-only operations correctly refuse to repair or trust stale state. The audit does not establish who omitted maintenance or why. | REQ-015 through REQ-017, REQ-024, REQ-025. |
| F5: Installed tests fail or skip real coverage | Confirmed: fixed parents[3] root discovery resolves to .agents in the installed layout. Nine fixture setups fail and 23 guard tests miss an available backend; a separate semantic test needs its documented runtime selection. Verification-local root correction and explicit semantic selection exercise all affected cases successfully. | REQ-018 through REQ-021, REQ-028. |
| F6: Recurrence can escape a setup-only check | Observed coverage limit: initializer assessment intentionally checks static capability without runtime execution, and passing fixtures did not expose the live SHACL timeout or guarantee a working installed test command. This is not evidence that every new installation already fails. | REQ-022 through REQ-030. |

## In scope

- The current root's ontology, memory integration, health commands, relevant test fixtures, and supported local runtime checks.
- Corrective requirements for the reusable ontology, memory, initializer, diagnostic/test assets and their documentation; distribution through the registered Template, with an exact separately reviewed root adoption manifest during future implementation.
- Prevention in new project creation, first preparation/manual Template copies, selected capability adoption/refresh, reruns, interruption recovery, and authorized profile activation/startup.
- Evidence lifecycle, generated-state freshness, accurate component/aggregate readiness, meaningful exit status, and reproducible tests at realistic root scale.

## Out of scope

- Executing repairs, installing dependencies, preparing models, starting a service, publishing records, or changing runtime settings during this document-only operation.
- Automatic upgrades or overwrites of other registered product projects, restoration of retired systems, a new background health service, cloud deployment, or Git publication.
- Replacing the existing Task/TRD/plan/receipt ownership systems or weakening source integrity, authorization, guarded dispatch, privacy, isolation, or finite resource limits.

## Task requirements

### REQ-001 - Establish the SHACL performance cause
- Requirement: Identify the measured cause of the root-scale SHACL timeout before accepting its corrective change.
- Source: U01; S01 finding 1; S06; F1.
- Acceptance: A repeatable diagnosis uses the full selected root graph and exact helper, profile, package, shape, and input versions, and reports time spent in the relevant preparation and validation phases.
- Acceptance: The diagnosis distinguishes observed cost from hypotheses and tests the selected remedy against that cost; an idle retest and small fixtures alone are not treated as a causal explanation.
- Depends on: None.

### REQ-002 - Complete full root-scale graph validation
- Requirement: Make the full valid current-root graph complete SHACL validation within a documented finite operating budget on the supported local environment.
- Source: U01; S01 and S06; F1.
- Acceptance: The actual repaired root and a representative populated installation complete with complete=true and a conformance result; the audited 2,268-triple baseline and its current successor are explicitly accounted for.
- Acceptance: The budget is reproducible and consistent with supported project limits. A budget change, if selected, has measured justification and retained safety ceilings; a larger timeout alone without full completion evidence does not satisfy this requirement.
- Depends on: REQ-001

### REQ-003 - Preserve graph-constraint meaning
- Requirement: Preserve all required graph constraints and source semantics while correcting SHACL performance.
- Source: U01; S06; S09 correctness and preservation rules.
- Acceptance: Known valid and deliberately invalid domain/range, cardinality, source, shape, and graph-selection cases retain the correct outcomes before and after the change.
- Acceptance: No empty graph, sample, skipped required shape, fabricated result, or weakened validator substitutes for the complete validation. Any optimization or cache is bound to exact relevant inputs and invalidated when they change.
- Depends on: REQ-001

### REQ-004 - Retain bounded failure and cancellation behavior
- Requirement: Keep timeout, cancellation, resource exhaustion, invalid input, backend failure, and nonconformance distinct from a completed healthy result.
- Source: U01; S01; S02 guard/deadline coverage; S06 finite budgets.
- Acceptance: Deliberate timeout/resource/cancellation controls produce non-complete structured outcomes, meaningful nonzero failure status, and terminated audit-owned workers without later guarded owner execution.
- Acceptance: Existing worker, memory, output, query, reasoning, and shared guard-deadline protections remain effective; runtime limits cannot be silently removed or expanded to make the assessment pass.
- Depends on: REQ-002, REQ-003

### REQ-005 - Report health for an explicit scope
- Requirement: Give ontology, advanced-ontology, and memory health entry points a truthful aggregate assessment for an explicit project, capability selection, and assessment level.
- Source: U01; S01 finding 3; S04; F2.
- Acceptance: The primary human and machine summaries identify the assessed scope and report degradation or failure when a required selected component is stale, invalid, unavailable, incomplete, or unverified.
- Acceptance: Canonical lookup readiness remains separately visible. Optional never-built projections and intentionally disabled profiles are explicitly not selected or not exercised, rather than falsely ready or silently treated as failures of an otherwise valid neutral starter.
- Depends on: None.

### REQ-006 - Align diagnostic exit status with aggregate health
- Requirement: Make health-command exit status consistent with the reported aggregate result and document the compatibility behavior for callers.
- Source: U01; S02 fault controls; S04 CLI mappings; F2.
- Acceptance: For a valid explicit health request, zero means its required assessed scope passes; selected-component failure, stale required state, unavailable prerequisites, or incomplete required assessment produces nonzero even when nested in profiles or backend details.
- Acceptance: Missing requested systems, malformed requests, and invalid roots remain distinguishable. Optional disabled capabilities are labeled and do not become false errors. Existing JSON consumers receive a documented migration/compatibility contract without losing component detail.
- Depends on: REQ-005

### REQ-007 - Separate capability from observed runtime readiness
- Requirement: Distinguish installed files, valid configuration, enabled profiles, current certification, generated-state freshness, and successful observed behavior throughout health and setup results.
- Source: U01; S01; S04; S08.
- Acceptance: A selected but unprovisioned backend, stale certification, or unexercised runtime cannot be presented as operationally ready.
- Acceptance: Results identify observation time and relevant input versions; changes invalidate affected readiness evidence. Completed starter setup can coexist with explicitly unselected runtime profiles without implying runtime execution.
- Depends on: REQ-005

### REQ-008 - Identify actionable failure causes
- Requirement: Return bounded, source-specific diagnostics that explain an unhealthy result and identify the appropriate next operation.
- Source: U01; S03 through S05; F2 through F4.
- Acceptance: Diagnostics distinguish absent, stale, invalid, unsupported historical evidence, backend unavailable, timeout, and intentionally disabled states, and identify the affected component and safe source locator.
- Acceptance: For nested evidence drift, show the changed artifact inside the receipt, not only the unchanged receipt path; include expected/current version information where safe. Suggested repair steps do not execute automatically or expose credentials.
- Depends on: REQ-005

### REQ-009 - Verify guard readiness from current bindings
- Requirement: Assess enabled guard readiness against its actual current bootstrap, engine, contract, adapters, required action-family coverage, and backend prerequisites.
- Source: U01; S01 guard integrity; S02 incomplete-guard controls; S04 and S09.
- Acceptance: Missing, incomplete, changed, or mismatched bindings and unavailable required backends make the selected guard assessment non-ready; enabled=true and a fixed coverage string are insufficient.
- Acceptance: All currently declared action families are checked. Integrity/certification and actual dispatch coverage remain distinct, and production writes are not dispatched as health tests.
- Depends on: REQ-005, REQ-007, REQ-008

### REQ-010 - Report real workbench service state
- Requirement: Report the selected workbench capability and actual service state separately, without a placeholder running value.
- Source: U01; S01 workbench API evidence; S02 and S04.
- Acceptance: A running-service assertion requires a bounded response from the selected loopback service with matching project identity and a safe read-only operation; stopped, unreachable, wrong-project, and not-assessed states are explicit.
- Acceptance: On-demand capability does not become an always-on service requirement. Health inspection starts no service, and any separately authorized probe cleans up its own process and keeps session credentials out of evidence and reusable assets.
- Depends on: REQ-005, REQ-007, REQ-008

### REQ-011 - Keep inspection non-mutating
- Requirement: Preserve the non-mutating contract of ordinary health, validation, lookup, and static setup assessment.
- Source: U01; S02 read preservation; S08 through S10.
- Acceptance: Checks neither repair canonical records or projections nor initialize databases, install packages, download models, recertify runtimes, toggle settings, or start persistent services.
- Acceptance: Negative controls compare relevant bytes and persistent timestamps before and after reads. Any separately selected bounded runtime probe is identified as such, uses existing authorized local resources, and reports its actual execution and cleanup.
- Depends on: REQ-005, REQ-007

### REQ-012 - Reconcile the existing unsupported memory claim
- Requirement: Give MEM-20260909-89C402A6 an evidence-backed governed disposition appropriate to its historical observation and present applicability.
- Source: U01; S01 finding 2; S03 and S05; F3.
- Acceptance: Review the intact historical receipt and the changed memory_capture.py and init_new_project.py versions, retaining their original bytes, identities, and provenance.
- Acceptance: Any renewed current claim is supported by actual current verification and the appropriate existing publication/supersession route. Missing historical proof remains explicit; rewriting old hashes, deleting diagnostics, or asserting the historical observation was false is not a repair.
- Depends on: None.

### REQ-013 - Separate historical support from current applicability
- Requirement: Distinguish integrity of historical verification evidence from whether a historical claim applies to current implementation versions.
- Source: U01; S03 and S05; F3.
- Acceptance: Where exact immutable evidence supports an older observation, later workspace changes do not by themselves assert that the observation is false or its record corrupt; current applicability is separately marked stale, changed, or unverified.
- Acceptance: Unavailable or altered historical evidence remains diagnosed. Unsupported or inapplicable evidence cannot be promoted into trusted current-authority or verified-current results. Existing records retain their provenance and receive an explicit compatibility treatment.
- Depends on: REQ-012

### REQ-014 - Retain reproducible evidence for new claims
- Requirement: Make new and renewed verified memory claims refer to durable evidence for the exact observed artifact versions, with an explicit applicability boundary.
- Source: U01; S05 current live-path verification mechanism; F3.
- Acceptance: A controlled later code/source update preserves the reproducibility of the earlier historical observation while invalidating only its unsupported current applicability.
- Acceptance: Only permitted selected evidence is retained within governed publication/evidence paths and existing privacy and resource bounds. A digest without accessible supporting evidence is not treated as proof; no synthetic success receipt or blind hash refresh is accepted.
- Depends on: REQ-013

### REQ-015 - Expose generated-state invalidation
- Requirement: Detect and report when memory projections/index certification or ontology associations no longer match their canonical sources and relevant runtime/configuration inputs.
- Source: U01; S03, S05, S10 and S11; F4.
- Acceptance: Changed README/document content, memory lifecycle/content, ontology definitions/helpers, profile configuration, or model/index inputs invalidate each affected derived product according to its declared dependency set.
- Acceptance: Previously generated required products that are missing, modified, or stale cannot contribute a healthy/current assertion; supported lexical fallback remains available with its actual limitations, without trusting stale associations.
- Depends on: REQ-005, REQ-008

### REQ-016 - Restore current derived integration state
- Requirement: Repair the current selected memory backend projection/index and ontology-memory associations after the evidence disposition and source versions are settled.
- Source: U01; S01 finding 2; S03, S05 and S11; F4.
- Acceptance: Use the existing authorized maintenance/reindex/link operations against final selected inputs, preserving canonical records, capture preferences, backend selection, and unrelated project content.
- Acceptance: Memory and ontology health show current required derived state; actual selected backend retrieval and ontology historical integration succeed or exclude records according to their documented governed disposition. A directory, enabled flag, or build receipt alone does not establish runtime readiness.
- Depends on: REQ-012, REQ-013, REQ-015

### REQ-017 - Close maintenance dependencies during authorized changes
- Requirement: Ensure authorized publication, capability refresh, maintenance, and runtime-startup workflows account for every invalidated required derived product before claiming operational completion.
- Source: U01 recurrence prevention; S08 through S11; F4 and F6.
- Acceptance: Dependency-aware verification evaluates final versions after writes. Within the operation's granted maintenance scope, required refreshes complete in dependency order and are rechecked.
- Acceptance: If maintenance is outside the granted scope, unavailable, or interrupted, completion reports the precise pending/stale state and recovery action. Read-only calls never provide implicit maintenance authority; no hidden background daemon is introduced.
- Depends on: REQ-007, REQ-011, REQ-015, REQ-016

### REQ-018 - Resolve fixture roots for every supported layout
- Requirement: Make shipped test support resolve its actual source, installed project, or Template context without fixed directory-depth assumptions.
- Source: U01; S02 and S07; F5.
- Acceptance: The same documented test entry points locate correct installed helpers, contracts, and explicitly selected local runtimes from source collections, root installation, Template, and a newly initialized project at different depths and with spaces in paths.
- Acceptance: macOS temporary fixture roots are resolved before use. No test-only monkeypatch is needed, and production symlink/alias safety rules are not weakened to accommodate fixtures.
- Depends on: None.

### REQ-019 - Make direct installed regression reproducible
- Requirement: Make the normal documented installed ontology test command run correctly using supported runtime discovery and explicit optional acceptance selection.
- Source: U01; S02 direct failure and follow-up evidence; S07; F5.
- Acceptance: All baseline ontology test identities, including the nine errored and 23 skipped guard cases, succeed when their actual local prerequisites are selected; the actual semantic acceptance test runs through its documented selection.
- Acceptance: Root and initialized-project execution require no audit-directory wrapper or hidden import patch. Tests do not provision dependencies or download models implicitly; unavailable optional prerequisites are reported explicitly.
- Depends on: REQ-018

### REQ-020 - Reject missing required test coverage
- Requirement: Make release and installation verification distinguish passes, failures, errors, expected optional skips, and unexpected skipped required coverage.
- Source: U01; S02; F5 and F6.
- Acceptance: Verification retains exact commands, runtime selections, counts, test identities, and exit status; an errored/skipped direct run cannot be relabeled as passed by adding unrelated successful runs.
- Acceptance: Expected disabled-profile skips are permitted only outside the selected acceptance scope. A selected/provisioned acceptance profile with missing or unexpectedly skipped required tests blocks its release-readiness claim.
- Depends on: REQ-007, REQ-019

### REQ-021 - Regress the health reporting faults
- Requirement: Add or retain meaningful controls for each diagnostic failure class from the audit, checking both detailed results and aggregate/exit behavior.
- Source: U01; S02 nineteen meaningful controls; S04 through S07.
- Acceptance: Controls cover healthy baselines; absent/invalid configuration; missing/stale/invalid projections; changed sources/evidence; missing backend; stale certification/index; incomplete guard selection; stopped/wrong-project service; timeout/cancellation; and intentionally disabled profiles.
- Acceptance: Each control demonstrates the intended injected cause, preserves read-only fixture state, and checks primary summary, details, and CLI result. Path-precondition failures and synthetic vectors are explicitly separated from configuration and actual-model evidence.
- Depends on: REQ-004, REQ-005, REQ-006, REQ-008, REQ-009, REQ-010, REQ-011, REQ-018

### REQ-022 - Distribute fixes from their reusable owners
- Requirement: Author reusable corrective changes in their owning depot collections and deliver the reviewed compatible set through the explicit Template update pipeline.
- Source: U01 future-installation prevention; S09; F6.
- Acceptance: The selected ontology, memory, initializer, test, and contract/documentation changes exist in the appropriate SKILLS-depo and other owned source collections, with reviewed package/contract versions and complete mappings.
- Acceptance: Template check/apply/check, relevant parity checks, and a separately exact-scoped root adoption establish the actual delivered file set. Root-only patches or direct edits to generated Template copies do not satisfy distribution.
- Depends on: None.

### REQ-023 - Keep new starters neutral and self-contained
- Requirement: Ensure reusable starters contain complete repaired capability and local contracts without project history, host runtime, generated data, or enabled optional profiles.
- Source: U01; S08 and S09; F6.
- Acceptance: A new Template-derived project has its own specialized identity and permitted authority bindings, empty project memory and neutral ontology extensions, and the intended disabled optional profiles.
- Acceptance: No source project records, stale projections, model files, virtual environments, runtime certifications, guard bootstraps, session credentials, or machine-specific fixture paths are copied. Static capability readiness and runtime not-exercised remain truthful.
- Depends on: REQ-007, REQ-018, REQ-022

### REQ-024 - Check readiness at project initialization boundaries
- Requirement: Make create, first preparation, manual Template-copy preparation, and selected capability adoption/refresh verify and report the health level they can actually establish.
- Source: U01; S08; F6.
- Acceptance: Trusted static inspection validates the complete selected capability, locks, contracts, identity, bindings, and fixture/package availability before claiming starter setup is valid, without executing unknown copied project code.
- Acceptance: Failed required setup checks prevent a successful-ready assertion and identify the actual partial boundary. Optional runtime remains explicitly unselected/not-exercised unless separately authorized and tested; successful copying cannot mask a selected unavailable capability.
- Depends on: REQ-005, REQ-007, REQ-008, REQ-011, REQ-022, REQ-023

### REQ-025 - Verify authorized runtime initiation
- Requirement: Require separately authorized profile activation, service startup, and operational refresh to verify selected dependencies and representative operations before claiming runtime readiness.
- Source: U01 system initiation prevention; S01, S08 and S10; F1, F2, F4 and F6.
- Acceptance: The selected operation checks current configuration, runtime/model/certification, guard bindings, and required derived state against final versions, then runs bounded relevant behavior probes.
- Acceptance: A stale, missing, timed-out, wrong-project, or failed required component prevents an operational-ready claim and preserves a precise failure/recovery result. This does not grant dependency installation, service startup, or repairs to ordinary health reads.
- Depends on: REQ-002, REQ-004, REQ-007, REQ-009, REQ-010, REQ-011, REQ-017, REQ-024

### REQ-026 - Preserve existing project ownership and editions
- Requirement: Keep existing project upgrades explicit and preserve customized assets, authored data, original setup editions, and operation-specific authority.
- Source: U01 scoped future-installation correction; S08 and S09.
- Acceptance: Other registered product projects are not automatically changed. A selected existing installation uses exact source/destination inventories and the established adoption/refresh boundary, retaining earlier receipt provenance.
- Acceptance: Customized or incomplete packages, ontology definitions/imports, memory history/preferences, Tasks, roles, governance, licenses, proposals, and unrelated edits are preserved or produce an explicit conflict; registration, equal filenames, or matching old content grants no overwrite authority.
- Depends on: REQ-022

### REQ-027 - Preserve rerun and recovery correctness
- Requirement: Make repeated and interrupted setup, refresh, maintenance, and runtime-initiation operations retain their exact intent and truthful health status.
- Source: U01 recurrence prevention; S08 through S10; F6.
- Acceptance: Equivalent reruns create no duplicate registrations, records, or side effects and do not silently adopt a newer edition or toggle existing choices.
- Acceptance: Interrupted operations resume only the same authorized selection with matching source/target preconditions; changed inputs, conflicting edits, or unknown ownership block replay. A prior ready receipt is not reused as current health after its dependencies change.
- Depends on: REQ-017, REQ-024, REQ-025, REQ-026

### REQ-028 - Verify fresh and preserved installation scenarios
- Requirement: Exercise the repaired delivery path in new and existing-project fixtures that represent the supported initialization and activation states.
- Source: U01; S02; S08 and S09; F5 and F6.
- Acceptance: Acceptance covers a fresh project, first preparation/manual copy, relocated/deeper installed test layout, populated root-scale ontology, selected earlier-edition adoption/refresh, preserved customized/disabled/capture-off configuration, equivalent rerun, and interrupted recovery.
- Acceptance: An unprovisioned neutral starter is checked without installs; a separately selected already prepared runtime exercises the advanced profiles and standard test entry point. Actual capability/runtime results are distinguished from static file checks, fixtures, and skipped work.
- Depends on: REQ-019, REQ-020, REQ-021, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027

### REQ-029 - Reverify every live audit finding
- Requirement: Demonstrate that the original live-root issues are resolved and healthy behaviors remain intact after the integrated corrective change.
- Source: U01; S01 through S03 and S11.
- Acceptance: Re-run the relevant original live checks and corrected diagnostics against final root versions: full SHACL, core/competency queries, SPARQL, inference, semantic retrieval, memory evidence/applicability, required projection/association freshness, guard integrity, and an authorized read-only workbench service probe.
- Acceptance: The evidence maps each F1-F6 finding and every requirement to a result or explicit unresolved blocker, preserves original failed evidence, and confirms protected files/identities outside the exact approved change set. Unit success alone cannot close a live failure.
- Depends on: REQ-002, REQ-003, REQ-004, REQ-009, REQ-010, REQ-012, REQ-013, REQ-014, REQ-016, REQ-020, REQ-021, REQ-025, REQ-028

### REQ-030 - Document operation and compatibility outcomes
- Requirement: Deliver with the corrected local capability a consistent operator/agent contract for health interpretation, prerequisites, explicit maintenance, installation, and recovery.
- Source: U01; S01 recommended repairs; S08 through S10; F2 and F6.
- Acceptance: Source, installed, and Template documentation agree on assessed scope, aggregate status and exit meanings, optional-profile treatment, historical applicability, supported runtime/test selection, and safe repair commands.
- Acceptance: Completion reports distinguish requirements approval, starter installation, runtime readiness, tested repair, and external publication. Compatible versions and any caller-visible schema/CLI transition are stated; no unsupported future-installation or continuous-service guarantee is inferred from a single successful run.
- Depends on: REQ-006, REQ-007, REQ-008, REQ-017, REQ-019, REQ-022, REQ-024, REQ-025, REQ-027, REQ-029

## Decisions

- D01: U01 and the selected report establish the scope without a further intake questionnaire. The required outcomes cover all audit findings and recurrence through the existing delivery and initiation routes; they do not authorize the repair implementation in this TRD operation.
- D02: The SHACL cost bottleneck is a technical diagnosis to be established under REQ-001, not an unresolved user outcome or an assumed cause. Algorithm, caching, phase instrumentation, and any justified finite budget adjustment remain constrained implementation choices. Full semantic coverage, completed root-scale validation, and resource protection are fixed acceptance requirements.
- D03: Health is scoped. Healthy canonical lookup, a valid neutral starter, enabled capability, currently running service, and verified operational readiness are different claims. Existing on-demand workbench behavior and optional disabled profiles remain supported; no always-on service is introduced.
- D04: The health repairs must preserve detailed failure information while adding a trustworthy primary aggregate and exit contract. Exact field names and a compatible versioning/migration mechanism belong to implementation design; silent selected-component failure is not an acceptable alternative.
- D05: Historical observation integrity and current applicability are separate. The existing record's disposition requires evidence and the existing governed lifecycle; neither automatic hash replacement nor unconditional promotion of old history is permitted. The exact durable evidence representation is an implementation choice within current ownership, compatibility, privacy, and resource constraints.
- D06: Required derived-state maintenance belongs to explicit authorized mutation/setup/refresh/startup scope. If that scope is absent, the system reports a pending dependency truthfully. Read-only queries and checks remain non-mutating. This prevents hidden degradation without adding an implicit background service or broader authority.
- D07: Reusable fixes originate in depot sources and the registered Template; current-root adoption is separately manifested during future implementation. Other existing product projects remain individually selected, preserving original editions and customizations.
- D08: The issue table provides forward coverage from the requested fixes to requirements; every requirement cites U01 plus inspected source evidence or the existing preservation/authority contract. The fresh-installation and integrated-root criteria provide observable prevention and closure without pretending that all future faults are impossible.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
