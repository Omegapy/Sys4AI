---
schema_version: 2
trd_id: "TRD-20260904-2D10A556"
title: "Sys4AI Project Initialization and Memory System Adoption"
slug: "sys4ai-project-initialization-and-memory-system-adoption"
created_at: "2026-09-04T09:04:37-06:00"
updated_at: "2026-09-04T15:34:26-06:00"
status: "trd_done"
revision: 11
last_action_id: "TO-TRD-013"
status_reason: "The user authorized the exact document-centric To-TRD implementation plan, including this lossless schema migration."
---

# Task Requirement Document: Sys4AI Project Initialization and Memory System Adoption

## Destination

Establish a governed hybrid initialization architecture for the Sys4AI depot root and future Sys4AI product projects. The root uses a canonical `init-new-project` skill, `Projects/Sys4AI-Template-Project/` remains the static project seed and documented manual fallback, and every real project can receive its own project-bound Memory System without creating memory state in the template.

## Captured user intent

U01 — The user wants the Cognee-backed capability referred to as the “Memory System” and wants it enabled for the main Sys4AI depot project.
U02 — The user wants a root `init-new-project` skill that creates new projects using governed assets from the depot and initializes their Memory System.
U03 — The reusable adoption inputs must include both `SKILLS-depo/` and `SOULS-depo/`.
U04 — The exact template is `Projects/Sys4AI-Template-Project/`; it must not contain initialized Memory System state, but it must tell an agent how to initialize memory after a real project is created from it.
U05 — The user approved the recommended hybrid architecture: the root skill is the canonical orchestrator, the template is its static seed and manual fallback, and both paths use the same Memory System initialization procedure.
U06 — Memory data and logs must be isolated per project rather than stored as an account-wide or user-wide memory/log collection.
U07 — Each project must initially receive the Memory Service runtime as an immutable locally built package installed into that project’s own environment.
U08 — Every new project must automatically receive the six current baseline workflow skills and `SOULS-depo/SOUL.md`; future additional skill or soul packages remain opt-in.
U09 — New-project Memory System initialization must not create a non-mutating Memory System preview, preview digest, or preview-approval pause.
U10 — The canonical `init-new-project` workflow must initialize project-local memory automatically in the same authorized run after internal validation; a manually copied template must use one separate direct `init-memory` invocation.
U11 — Version 1 of `init-new-project` must support only real projects created beneath the registered Sys4AI `Projects/` directory; out-of-depot project creation is unsupported.
U12 — The `sys4ai-depot` Memory System must include the approved tiered root-owned source set and support other relevant root-owned folders added in the future.
U13 — Every future relevant root-owned folder must receive explicit reviewed source registration before any of its content is ingested; automatic folder ingestion is prohibited.

## Context and sources

S01 — `README.md` states that the retired synchronization capability no longer provides a copy engine or automatic propagation, that reusable collections are not installation managers, and that project-local adoption requires exact source, destination, overwrite, and verification boundaries.
S02 — `depot/projects.json` identifies the main project as `sys4ai-depot`, identifies `Projects/Sys4AI-Template-Project/` as the registered template, and identifies the Memory Service as an independent product.
S03 — `Projects/Sys4AI-Template-Project/README.md`, `AGENTS.md`, `ROLE.md`, and `SOUL.md` establish the template as a generic governed starter with project-local Task, TRD, planning, role, and communication assets.
S04 — Live inspection on 2026-09-04 found no Memory System configuration or state in the template and found `.venv`, `.ruff_cache`, `.DS_Store`, and generated cache artifacts that must not be copied into a new project.
S05 — `SOULS-depo/SOUL.md`, the active root `SOUL.md`, and the template `SOUL.md` currently have the same SHA-256, but the depot ownership contract says equality does not create automatic propagation authority.
S06 — `Projects/Sys4AI-Memory-Service/README.md`, `config/memory.toml`, and `src/sys4ai_memory/initialization/service.py` define a provider-neutral, project-confined Memory System with explicit preview, digest-bound apply, private derived directories, and no initialization on configuration load.
S07 — `TASK-20260904-08E13458` governs this requirements-definition work and prohibits implementation, installation, Git, publication, deployment, and destructive actions during TRD capture.
S08 — The current Memory Service initialization primitive uses preview and digest-bound apply; U09 deliberately requires a different no-preview bootstrap behavior for newly created projects while retaining fail-closed internal validation.
S09 — Live root inventory found active governance files, depot control records, Requirements, TRDs, Implementation Plans, Verification, Tasks, active skills, reusable SKILLS/SOULS/AGENTS/ROLES collections, and root tests; the existing Memory Service registry supports separate namespaces, authority classes, and explicit exclusions.

## In scope

- Enable a distinct project-bound Memory System instance for the Sys4AI depot root.
- Define the root `init-new-project` skill and its reusable source/adoption relationship.
- Use the exact registered template as the static seed for canonical and manual project creation.
- Adopt explicitly selected reusable skills and soul guidance from `SKILLS-depo/` and `SOULS-depo/`.
- Provide one reusable Memory System initialization procedure and a project-local `INIT_MEMORY.md` guide.
- Specialize project identity, register factual inventory, protect derived paths, and verify initialization outcomes.
- Keep project creation and Memory System initialization safe, internally validated, reproducible, and project-isolated.
- Limit version 1 project creation to real child projects beneath the registered Sys4AI `Projects/` directory.
- Register the approved tiered root-owned source set for `sys4ai-depot` memory and support admission of other relevant root-owned folders added later.

## Out of scope

- Initializing a Memory System, model cache, Cognee database, or runtime log inside `Projects/Sys4AI-Template-Project/`.
- Account-wide or user-wide memory, provider databases, audit logs, or Cognee file logs.
- Non-mutating Memory System preview artifacts, preview digests, and preview-approval pauses for newly created projects.
- Editable sibling-path Memory Service dependencies and copied consumer-local Memory Service source trees.
- Creating or initializing projects outside the registered Sys4AI depot workspace in version 1.
- Restoring the retired synchronization engine or adding automatic propagation from reusable collections into existing projects.
- Git repository initialization, remote configuration, commits, pushes, package publication, GitHub Pages, or deployment.
- Shared production Memory Service mode, cloud fallback, credential acquisition, and non-fixture destructive operations.
- Treating this TRD or its Task as implementation authority.

## Task requirements

### REQ-001 — Use the hybrid creation architecture
- Requirement: Use a hybrid architecture in which the root `init-new-project` skill is the canonical project-creation orchestrator and the exact template is both its static seed and a documented manual fallback.
- Source: U05 — the user explicitly approved the recommended hybrid architecture.
- Acceptance: The implemented canonical and manual workflows both start from `Projects/Sys4AI-Template-Project/` and converge on the same required project identity, governed assets, Memory System procedure, and verification outcomes.
- Depends on: None.

### REQ-002 — Provide the root project-initialization skill
- Requirement: Provide a reusable `init-new-project` skill source under `SKILLS-depo/` and a separately adopted active copy for the Sys4AI root Project Director.
- Source: U02, U03 — the user requested a root initialization skill using governed depot assets.
- Acceptance: Both skill packages exist at their approved source and active paths, have a documented source-to-destination relationship, pass their package checks, and do not claim automatic synchronization after adoption.
- Depends on: REQ-001

### REQ-003 — Use the exact registered template
- Requirement: Use `Projects/Sys4AI-Template-Project/` as the only template seed selected by this architecture.
- Source: U04 — the user identified the exact template project.
- Acceptance: The root workflow resolves that exact registered path, verifies that it is still identified as `kind: project-template`, and rejects an ambiguous, missing, or substituted template path.
- Depends on: REQ-001

### REQ-004 — Copy only the clean project skeleton
- Requirement: Create a new project from an explicit allowlist of template-owned starter artifacts and exclude virtual environments, caches, operating-system metadata, generated bytecode, template runtime state, and other non-source files.
- Source: S04 — live template inspection found transient artifacts that an unfiltered copy could carry.
- Acceptance: A created project contains the approved starter inventory and does not contain `.venv`, `.ruff_cache`, `.DS_Store`, `__pycache__`, `.sys4ai/memory`, provider databases, model caches, or template-generated runtime state.
- Depends on: REQ-003

### REQ-005 — Specialize the new project identity
- Requirement: Replace template identity with a user-supplied project name, unique stable project ID, real root path, and product-specific README context before treating the destination as a real project.
- Source: U02 and S03 — the initializer creates real projects from a generic template.
- Acceptance: The resulting README and governed configuration contain the approved project identity, no active artifact identifies the product as “Sys4AI Template Project,” and the stable ID is unique in the registry.
- Depends on: REQ-004

### REQ-006 — Register only factual project inventory
- Requirement: Add the new project to `depot/projects.json` only after its directory and identity exist, recording only observed repository and publication state.
- Source: S01 and S02 — registration is factual inventory and grants no external-action authority.
- Acceptance: The registry contains one schema-valid entry with the approved stable ID and real root-relative path, and it does not invent a repository, remote, publication, or deployment state.
- Depends on: REQ-005

### REQ-007 — Install the baseline skills from SKILLS-depo
- Requirement: Automatically install the complete `agent-task`, `communication`, `manage-subagent-roles`, `task`, `to-implementation-plan`, and `to-trd` packages from `SKILLS-depo/` into every new project’s recognized local skill directory, while keeping all future additional skill packages opt-in.
- Source: U03 and U08 — the user requires `SKILLS-depo/` and approved the six-skill default baseline with future additions opt-in.
- Acceptance: A new project contains complete validated copies of exactly the six baseline packages from their reviewed source versions, and no additional or future skill package is installed without explicit selection.
- Depends on: REQ-002, REQ-005

### REQ-008 — Install the baseline soul from SOULS-depo
- Requirement: Automatically install `SOULS-depo/SOUL.md` as the new project’s local `SOUL.md`, while keeping any future additional or alternative soul package opt-in.
- Source: U03 and U08 — the user requires `SOULS-depo/` and approved its current `SOUL.md` as the default baseline.
- Acceptance: The new project’s `SOUL.md` is a verified project-local copy of the reviewed `SOULS-depo/SOUL.md` source, no additional or alternative soul is installed without explicit selection, and later source changes do not silently alter the project copy.
- Depends on: REQ-005

### REQ-009 — Preserve project ownership after creation
- Requirement: Treat every created project’s instructions, skills, soul, configuration, registries, control records, documentation, and memory state as project-owned after initialization.
- Source: S01 and U05 — the hybrid architecture retains the depot’s explicit adoption model.
- Acceptance: Documentation and behavior state that no reusable-source change propagates automatically and that every later refresh requires a new exact project-local adoption decision and verification.
- Depends on: REQ-006, REQ-007, REQ-008

### REQ-010 — Provide one Memory System initialization procedure
- Requirement: Provide one canonical project-bound Memory System initialization procedure that can be invoked by the root `init-new-project` skill, by the Sys4AI root adoption workflow, and by an agent working from a manually copied template.
- Source: U01, U02, U04, and U05 — all approved entry paths must use one Memory System procedure.
- Acceptance: All three entry paths resolve the same configuration, path-isolation, validation, and verification contracts without duplicating executable initialization logic, while entry-specific authorization behavior follows the applicable requirements.
- Depends on: REQ-001

### REQ-011 — Include a manual Memory System guide in the template
- Requirement: Add a project-local `INIT_MEMORY.md` to the exact template and link it prominently from the template README so the instructions remain available after a manual copy.
- Source: U04 and U05 — the template must remain a usable manual fallback and explain Memory System initialization.
- Acceptance: The template README has a valid relative link to `INIT_MEMORY.md`, the guide clearly states that the template itself is not initialized, and a copied project agent can identify the canonical initialization procedure and required approvals from the local files.
- Depends on: REQ-003, REQ-010

### REQ-012 — Keep the template uninitialized
- Requirement: Keep `Projects/Sys4AI-Template-Project/` free of Memory System configuration specialized to a real project and free of derived memory, provider databases, runtime logs, model caches, and initialization receipts.
- Source: U04 — the user explicitly excludes Memory System initialization in the template.
- Acceptance: Template validation confirms that no `.sys4ai/memory` state, Cognee database, project-specific memory identity, runtime log, model cache, or initialization receipt exists after documentation and skill changes.
- Depends on: REQ-003, REQ-011

### REQ-013 — Enable project-bound memory for the Sys4AI depot
- Requirement: Initialize the main Sys4AI depot as its own Memory System project using stable identity `sys4ai-depot` and root-local configuration and derived storage.
- Source: U01 and S02 — the user requires Memory System enablement for the registered main project.
- Acceptance: The depot has reviewed project-specific configuration, a digest-bound initialization receipt, and derived storage beneath `/Volumes/P-SSD/AngryOwl/Sys4AI/.sys4ai/memory/` without borrowing the Memory Service product’s dataset or storage.
- Depends on: REQ-010

### REQ-014 — Keep depot memory out of child projects
- Requirement: Scope the Sys4AI depot’s Memory System to root-owned canonical material and exclude independent child-project working trees and their derived state by default.
- Source: U06, S01, and S02 — root and child projects have separate ownership and require project-bound memory.
- Acceptance: Root source discovery and recall tests show that content beneath independent child-project roots is absent unless a separately authorized cross-project request and canonical grant explicitly permits it.
- Depends on: REQ-013

### REQ-015 — Confine each project’s memory and logs
- Requirement: Place each real project’s exact index, Cognee data/system/cache directories, Memory System audit output, receipts, exports, and Cognee file logs beneath that project’s approved local derived-data boundary.
- Source: U06 and S06 — the user requires project-separated memory and logs, and the Memory Service supports confined paths.
- Acceptance: Two independently initialized projects resolve all listed state to different roots beneath their respective projects, and neither creates or uses `~/.cognee/logs` or another account-wide memory/log directory.
- Depends on: REQ-010

### REQ-016 — Use unique project and dataset identities
- Requirement: Give every initialized project a unique project ID, unique Cognee dataset identity, and a project-scoped runtime boundary rather than multiplexing unrelated projects through one unguarded in-process Cognee instance.
- Source: U06 and S06 — project isolation requires identity and runtime separation in addition to path separation.
- Acceptance: Cross-project requests fail closed, each initialized runtime reports the expected project and dataset, and a two-project test finds no record, graph relation, cache entry, or provider handle crossing the boundary.
- Depends on: REQ-005, REQ-015

### REQ-017 — Protect paths and sources before initialization
- Requirement: Install and verify project-local ignore, discovery, secret-exclusion, and safe-path rules before creating any Memory System derived directory or invoking Cognee.
- Source: S01, S04, and S06 — derived storage is disposable and must be protected before initialization.
- Acceptance: A non-mutating preflight proves that `.sys4ai/memory`, model caches, provider paths, credentials, environments, and excluded transient files cannot enter canonical source discovery or version control before initialization apply is offered.
- Depends on: REQ-005, REQ-010

### REQ-018 — Initialize new-project memory directly without preview
- Requirement: Make the canonical `init-new-project` workflow initialize project-local Memory System state automatically in the same authorized run after internal validation, and make the manual-template path use one separate direct `init-memory` invocation, without a preview or preview digest in either path.
- Source: U09 and U10 — the user prohibited previews and approved same-run initialization for the canonical path with one direct invocation for the manual path.
- Acceptance: The canonical path produces initialized project-local Memory System state in its single authorized run; the manual path produces the equivalent state after one explicit `init-memory` invocation; neither path generates, stores, displays, or requests approval of a preview or preview digest; and required identity, path, configuration, secret, and isolation checks fail closed before writes.
- Depends on: REQ-010, REQ-017

### REQ-019 — Make canonical and manual creation converge safely
- Requirement: Ensure that the root-skill path and the documented manual-template path are repeatable, detect existing destinations and identities, and stop without overwriting unrelated files or duplicating registry entries.
- Source: U05 and S01 — both hybrid entry paths must preserve project ownership and existing work.
- Acceptance: Tests cover a new empty destination, an equivalent rerun, a conflicting nonempty destination, an existing registry ID/path, and a manual-template project; equivalent state is reported without duplication and conflicts stop before mutation.
- Depends on: REQ-006, REQ-009, REQ-010, REQ-018

### REQ-020 — Verify every initialized project
- Requirement: Produce a bounded initialization result that verifies template specialization, adopted skills and soul guidance, registry accuracy, Memory System path isolation, provider/configuration identity, ignored derived state, and project-local tests.
- Source: S01 and U05 — the hybrid workflow requires project-local verification rather than a copy claim.
- Acceptance: A created project has a reviewable result or receipt listing actual source versions, destination paths, project and dataset IDs, checks run, pass/fail outcomes, and any deliberately deferred provider/model activation without recording secrets.
- Depends on: REQ-007, REQ-008, REQ-016, REQ-018, REQ-019

### REQ-021 — Record the Memory Service runtime source
- Requirement: Build an immutable local package artifact from the Sys4AI Memory Service product and install that exact artifact into each consumer project’s own environment while keeping runtime implementation separate from project-local configuration and derived memory.
- Source: U07 — the user selected immutable local-package delivery as the required initial method; S06 establishes the Memory Service as an independent product.
- Acceptance: The package artifact has a recorded version and SHA-256 digest, the consumer environment installs and loads that exact artifact without an editable sibling-path dependency or copied source tree, and later edits in the Memory Service checkout do not change the installed consumer runtime.
- Depends on: REQ-010, REQ-015

### REQ-022 — Confine version 1 project creation to the Sys4AI workspace
- Requirement: Allow version 1 of `init-new-project` to create only real child projects whose resolved destination is beneath `/Volumes/P-SSD/AngryOwl/Sys4AI/Projects/`, and reject out-of-depot destinations.
- Source: U11 — the user approved the recommended version 1 workspace boundary.
- Acceptance: A valid new destination beneath the registered `Projects/` container is accepted; the depot root, the template’s own path, existing unrelated paths, symlink escapes, traversal attempts, and destinations outside the depot are rejected before any filesystem or registry mutation.
- Depends on: REQ-001, REQ-003

### REQ-023 — Register the tiered sys4ai-depot source set
- Requirement: Register the root `AGENTS.md`, `SOUL.md`, `ROLE.md`, and `README.md`; `depot/`; `Requirements/`; `TRDs/`; `Implementation_Plans/`; `Verification/`; `Tasks/`; `.agents/skills/`; `SKILLS-depo/`; `SOULS-depo/`; `AGENTS-depo/`; `ROLES-depo/`; and `tests/` as the initial `sys4ai-depot` Memory System source set with distinct namespaces and authority classifications.
- Source: U12 — the user approved the recommended tiered root-owned source set; S09 confirms the current categories.
- Acceptance: The root source registry covers every named source, distinguishes active root authority from reusable depot material and evidential records, preserves canonical-file reread for execution-critical state, and excludes every independent child project and all derived, environment, cache, model, secret, temporary, and raw-log paths.
- Depends on: REQ-013, REQ-014, REQ-017

### REQ-024 — Register future relevant root-owned folders explicitly
- Requirement: Allow other relevant root-owned source folders to enter `sys4ai-depot` memory only after an explicit reviewed source registration, without requiring Memory Service source-code changes or weakening existing exclusions; prohibit automatic folder ingestion.
- Source: U12 and U13 — the user requires future-folder support and selected explicit reviewed registration rather than automatic discovery.
- Acceptance: A representative eligible future root-owned folder enters memory only after a reviewed registration records its owner, relevance, path, format, namespace, canonicality, authority, trust, sensitivity, retention, and write policy; the same unregistered folder is not ingested; and child-project, derived, cache, environment, secret, temporary, and raw-log folders remain excluded.
- Depends on: REQ-023

## Decisions

- D-001 — Use “Memory System” as the user-facing name for the Cognee-backed, provider-neutral Sys4AI capability. Basis: U01.
- D-002 — Adopt the hybrid project-creation architecture. Basis: U05.
- D-003 — Use `Projects/Sys4AI-Template-Project/` as the static seed, not as the actor that performs initialization. Basis: U04 and U05.
- D-004 — Keep the root `init-new-project` skill as the canonical orchestrator while retaining a documented manual-template route. Basis: U02 and U05.
- D-005 — Include both `SKILLS-depo/` and `SOULS-depo/` as governed project-adoption sources. Basis: U03.
- D-006 — Keep the template free of initialized Memory System state. Basis: U04.
- D-007 — Give the Sys4AI depot and every child project separate Memory System identity, storage, logs, and runtime scope. Basis: U01 and U06.
- D-008 — Preserve explicit adoption and prohibit automatic synchronization from reusable collections after project creation. Basis: S01 and the approved hybrid architecture.
- D-009 — Use an immutable locally built Memory Service package installed into each project’s own environment as the initial runtime delivery method; prohibit editable sibling-path dependencies and copied consumer-local runtime source. Basis: U07.
- D-010 — Install the six current baseline workflow skills and `SOULS-depo/SOUL.md` automatically in every new project; keep every future additional skill or soul package opt-in. Basis: U08.
- D-011 — Do not create a non-mutating Memory System preview, preview digest, or preview-approval pause for newly created projects; retain internal fail-closed validation. Basis: U09.
- D-012 — Initialize project-local memory automatically during the canonical `init-new-project` run; require one separate direct `init-memory` invocation after a manual template copy. Basis: U10.
- D-013 — Limit version 1 of `init-new-project` to real child projects beneath the registered Sys4AI `Projects/` directory and reject out-of-depot destinations. Basis: U11.
- D-014 — Use the approved tiered root-owned source set for the initial `sys4ai-depot` Memory System, with separate namespaces and authority classes and complete child/derived/secret exclusions. Basis: U12.
- D-015 — Support other relevant root-owned folders added in the future without requiring Memory Service code changes. Basis: U12.
- D-016 — Require explicit reviewed source registration before ingesting any future root-owned folder and prohibit automatic folder ingestion. Basis: U13.

## Open questions

None.

## Not yet specified

None.

## Assumptions

- Accepted: “Coiny” refers to Cognee and “Six AI” refers to Sys4AI, based on the surrounding conversation and named local paths.
- Accepted: `sys4ai-depot` is the stable identity of the main root project, based on `depot/projects.json`.
- Accepted: Template files become independently project-owned after creation and do not retain an automatic update relationship with reusable depot sources, based on the root ownership contract and the approved hybrid model.
