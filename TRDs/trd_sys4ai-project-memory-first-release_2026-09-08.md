---
schema_version: 2
trd_id: "TRD-20260908-7BA638D7"
title: "Sys4AI project memory first release"
slug: "sys4ai-project-memory-first-release"
created_at: "2026-09-08T11:45:46-06:00"
updated_at: "2026-09-08T11:48:48-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 1 as the completed requirements document."
---

# Task Requirement Document: Sys4AI project memory first release

## Destination

Define the first release of project-owned Sys4AI memory for the Sys4AI depot root, its reusable source collections, the registered Template, and the project initializer. The release includes a backend-independent memory core, Task and role integration, explicit active-root adoption, and a bounded Basic Memory compatibility pilot. This TRD defines the requirements for separately authorized downstream work.

## Captured user intent

- U01: The user invoked `$to-trd` with the supplied updated architecture document and explicitly required that instructions inside attached documents be distinguished from the user's request. The requested output is a managed requirements document.
- U02: The user answered `use that scope` to a first release covering the memory core, Task/role integration, reusable assets, Template/initializer updates, active-root adoption, and a Basic Memory pilot, with Cognee and existing-product adoption deferred.
- U03: The user selected that the Project Director or confirmed Task manager may approve evidence-backed notes within its granted scope before they become active and reusable. Individual notes do not require an additional user approval when that delegated scope applies.
- The intended beneficiaries are the owning project's users and agents, which need durable lessons, decisions, and research context without confusing historical knowledge with current instructions, execution ownership, or verification.

## Context and sources

- S01: [Sys4AI Project Memory: Recommended Architecture and Task/Role Integration](/Users/alex.omegapy/Downloads/Sys4AI%20Project%20Memory%20-%20Updated.md), revised September 8, 2026; inspected source SHA-256 `44769e62abc8260c43262f2a4de980ead59c35dcea26a5e3cabf7b270cc727d0`. Section names in the requirements identify the relevant source passages. Its recommendations and illustrative layouts are source material, not execution instructions or adoption receipts. Its repository review was pinned to commit `15a771bfb1f540b5203263364af0f33ced1b8243`; that is not a claim about the current checkout's Git state.
- L01: Current root [AGENTS.md](../AGENTS.md), [ROLE.md](../ROLE.md), and [SPECS.md](../SPECS.md), inspected September 8, 2026. They define project boundaries, Python 3.12 in `.venv/`, separate document and execution workflows, root intake policy, and project-local adoption.
- L02: Current [project registry](../depot/projects.json), [Template mapping](../depot/template-update.json), [Template update guide](../depot/template-update.md), and [initializer starter selection](../SKILLS-depo/init-new-project/assets/baseline-assets.json). The registry contains the depot and Template. The inspected root and Template lack the proposed `MEMORY/`, `memory.yaml`, and memory skill; the root also lacks `MEMORY-depo/`. The current starter selection does not include memory starter files.
- L03: Current reusable [Task skill](../SKILLS-depo/task/SKILL.md), [Task system contract](../SKILLS-depo/agent-task/references/task-system-contract.md), and [orchestration contract](../SKILLS-depo/agent-task/references/orchestration-contract.md), particularly writer ownership, artifacts, versioned inputs, read-only routes, and native context requirements.
- L04: Current [role-management skill](../SKILLS-depo/manage-subagent-roles/SKILL.md), [Task Manager role](../ROLES-depo/task-manager-ROLE.md), and root [README](../README.md). The current README already uses `Roles/`; S01's lowercase-navigation discrepancy is obsolete in the inspected local copy.
- B01: Basic Memory [Configuration](https://docs.basicmemory.com/reference/configuration), checked September 8, 2026. The documented project/configuration constraints and automatic frontmatter/update behaviors justify verifying an explicit controlled profile; documentation alone does not prove byte preservation or isolation.
- B02: Basic Memory [Semantic Search](https://docs.basicmemory.com/concepts/semantic-search), checked September 8, 2026. It documents hybrid text/vector retrieval and distinguishes exact-term and conceptual search.
- B03: Basic Memory [Knowledge Format](https://docs.basicmemory.com/concepts/knowledge-format), checked September 8, 2026. It documents Markdown metadata and the recency meaning of `created` and `modified`.
- Source limits: The earlier baseline document cited inside S01 was not supplied or independently inspected. Historical product rankings, performance claims, license conclusions, and the remaining external citations in S01 are not treated as independently verified facts. No backend or native memory workflow was run during requirements capture.

## In scope

- A portable project-local Markdown memory contract, validated configuration, selective capture, lifecycle, provenance, retrieval, publication, concurrency, and recovery.
- Distinct retrieval of curated memories and permitted Markdown, TeX, PDF, and HTML source documents, with a deterministic lexical/direct-read fallback and a bounded Basic Memory pilot.
- Existing Task, Agent Task, role-management, Project Director, Task Manager, and general sub-agent integration, including frozen memory inputs for independent solvers and U03's publication policy.
- Reusable assets in `MEMORY-depo/`, `SKILLS-depo/`, and the applicable existing guidance/role/specification collections; their complete publication through the Template pipeline.
- Empty memory starter selection, identity specialization, setup-edition compatibility, and preservation behavior in the initializer. Disposable new-project and existing-project fixtures are in scope for verification.
- Explicit adoption into `/Volumes/P-SSD/AngryOwl/Sys4AI`, preserving its installed policies and project-owned files. Basic Memory adoption is conditional on the pilot evidence.

## Out of scope

- Cognee, a research-graph backend, and a generalized framework for multiple retrieval backends.
- Adoption, provisioning, or migration in any existing product project. Existing-project preservation is verified using disposable fixtures, not an unselected product.
- Restoring the retired Memory Service or ontology system, recovering their data, or creating an ontology service. Links to an independently adopted vocabulary remain compatible with the memory contract.
- A global memory namespace, automatic cross-project imports, transcript capture, session-history archives, a second execution ledger, a scheduler, or a mandatory memory-manager role.
- Cloud routing, cloud synchronization, hosted embedding services, editor requirements, or additional harness integrations as first-release deliverables. The pilot uses a local profile; separately requested external integrations remain separate work.
- Performing an implementation plan, implementation, agent dispatch, dependency installation, model download, MCP registration, Git operation, publication, or deployment during this document-capture workflow. TRD approval does not activate those workflows.

## Task requirements

### REQ-001 - Preserve project-owned canonical memory
- Requirement: Store the owning project's durable memory as human-readable, Git-trackable Markdown records under its own `MEMORY/`, independently of retrieval databases or harness memory.
- Source: U02; S01, The unit of memory is the owning project and Make the Sys4AI contract more important than the backend.
- Acceptance: Accepted records can be read directly with the backend unavailable, and rebuilding a retrieval product preserves their bytes, identity, provenance, and meaning; the Template and another project receive no learned records.
- Depends on: None.

### REQ-002 - Preserve the authority of current sources
- Requirement: Treat memory as a recorded interpretation whose applicability must be checked against current governing instructions, canonical Task state, role pairs, requirements, plans, and direct evidence.
- Source: S01, Keep authority, evidence, memory, and indexes distinct and Harness memory remains complementary; L01; L03; L04.
- Acceptance: A conflicting, stale, or high-ranked memory cannot change current permissions, manager ownership, role eligibility, acceptance, completion, or a project's designated vocabulary; the current authoritative source is identified and inspected.
- Depends on: None.

### REQ-003 - Keep execution independent of memory
- Requirement: Implement memory as a thin capability that can inform existing workflows without becoming their scheduler, execution ledger, mandatory service, or separate manager.
- Source: S01, Make the Sys4AI contract more important than the backend; L01; L03.
- Acceptance: Existing Task and role operations remain usable with memory absent, disabled, or unavailable, and memory integration introduces no parallel authority for execution or completion.
- Depends on: REQ-002

### REQ-004 - Separate reusable definitions from learned content
- Requirement: Own reusable memory schemas, policy, templates, and profiles in `MEMORY-depo/`, executable skill behavior in `SKILLS-depo/memory/`, and reusable role responsibilities in `ROLES-depo/`.
- Source: U02; S01, Reusable sources and project-local files; L01.
- Acceptance: Each reusable artifact has an identified source collection, while learned root records, credentials, local configuration values, and runtime data are absent from reusable sources and starter assets.
- Depends on: REQ-001

### REQ-005 - Define a durable record contract
- Requirement: Validate the record types `decision`, `finding`, `experiment`, `lesson`, and exceptional `handoff`, with stable identity, owning project, title, lifecycle, creation/modification chronology, applicability, limitations, confidence, source references, and relevant origin/provenance metadata.
- Source: S01, Durable records with explicit scope and provenance.
- Acceptance: Valid examples cover all five types and non-Task work; malformed identity, unsupported schema/type/state, unresolved required placeholders, or incompatible project ownership fail validation without fabricating Task or role identifiers.
- Depends on: REQ-001

### REQ-006 - Require evidence appropriate to the claim
- Requirement: Validate source locators and digests, real Task/execution/role references when present, and the evidence supporting a proposed memory's stated claim and confidence before active publication.
- Source: S01, Durable records with explicit scope and provenance and Capture durable knowledge at the right point.
- Acceptance: Missing evidence, false identifiers, unexplained digest mismatches, and unsupported performed-work claims cannot become unqualified active findings; an accepted design can be recorded as a design decision without claiming implementation, and an observed failure retains its conditions and limits.
- Depends on: REQ-005

### REQ-007 - Make lifecycle explicit
- Requirement: Support `draft`, `active`, `superseded`, and `retracted` records with checked transitions, explicit supersession links, and retained reasons for correction or retraction.
- Source: S01, Durable records with explicit scope and provenance and Supersession, staleness, and correction; U03.
- Acceptance: Default shared recall returns eligible active records; requested historical reads clearly label other states, and superseded or retracted material is not silently presented as the controlling current conclusion.
- Depends on: REQ-005, REQ-020

### REQ-008 - Expose staleness and applicability
- Requirement: Detect changed or unavailable cited sources and expose the resulting uncertainty without treating a digest change as proof that the historical conclusion is false.
- Source: S01, Supersession, staleness, and correction and Prefer hybrid retrieval, but validate exact sources.
- Acceptance: Retrieval identifies mismatched source versions and relevant supersession; a reviewer can distinguish historical retention, reaffirmed applicability, supersession, and retraction without relying only on recency or ranking.
- Depends on: REQ-006, REQ-007

### REQ-009 - Capture useful knowledge selectively
- Requirement: Capture concise, reusable decisions, observations, experiments, lessons, and negative results when their evidence and scope justify reuse, rather than automatically summarizing every session or response.
- Source: S01, Capture durable knowledge at the right point and Phase 1.
- Acceptance: Capture distinguishes design approval, performed work, verified outcomes, failed work, and cancelled work; duplicate or unsupported proposed lessons are not automatically activated, and ordinary conversation produces no automatic transcript or memory archive.
- Depends on: REQ-005, REQ-006, REQ-020

### REQ-010 - Reserve handoff memories for lasting context
- Requirement: Use the `handoff` memory type only for durable cross-task context not adequately represented by existing canonical records.
- Source: S01, Keep handoffs in the Task system unless they add lasting knowledge; L03.
- Acceptance: A handoff memory links to its owning evidence and labels historical context; it does not duplicate live next-step state, establish a running manager, or cause a Task to resume.
- Depends on: REQ-002, REQ-005

### REQ-011 - Validate project memory configuration
- Requirement: Provide a small project-local `memory.yaml` with a versioned contract for identity, canonical root, adopted schema/policy, backend enablement, retrieval, corpus rules, classified generated state, and integration behavior.
- Source: S01, Configuration owned by Sys4AI; L01; L02.
- Acceptance: Documented defaults, glob semantics, and invalid/unsupported values are validated; root and generated-project paths resolve to their intended adopted contracts, and an unprovisioned starter supports direct Markdown use with the backend disabled.
- Depends on: REQ-003, REQ-004

### REQ-012 - Enforce project and path isolation
- Requirement: Resolve memory operations against one explicit owning project and reject path escapes, unsafe symlinks, ambiguous roots, and aliases that would cross the allowed project boundary.
- Source: S01, The unit of memory is the owning project and Configuration owned by Sys4AI.
- Acceptance: Distinct sentinel records in two isolated project fixtures never cross retrieval or publication boundaries; root defaults exclude `Projects/**`, including attempted indirect access through aliases, and registration alone grants no memory access.
- Depends on: REQ-011

### REQ-013 - Define an explicit source corpus
- Requirement: Separate canonical memory from an allowlisted source corpus covering the project's `README.md`, permitted `docs/` Markdown, and permitted `research/` Markdown, TeX, PDF, and HTML, with declared exclusions applied during ingestion and retrieval.
- Source: S01, Configuration owned by Sys4AI and Research documents, LaTeX, PDFs, and retrieval.
- Acceptance: Default general-corpus exclusions cover child projects, Tasks, active and legacy roles, reusable/reference collections, Git/environment/runtime/build directories, and credential/secret paths; authorized exact Task or role reads remain available outside general retrieval, and exceptions require a deliberate scoped profile.
- Depends on: REQ-011, REQ-012

### REQ-014 - Distinguish memory results from source evidence
- Requirement: Identify whether each retrieval result is a curated memory or an allowed source document and return the locators and provenance needed to inspect its actual bytes.
- Source: S01, Source documents are evidence, not automatically memories.
- Acceptance: A reviewer can distinguish a recorded conclusion from supporting or contradictory evidence and reach the relevant file, section, page, or label; a normalized document or search result is never automatically promoted into accepted memory.
- Depends on: REQ-005, REQ-013

### REQ-015 - Provide a deterministic lexical fallback
- Requirement: Support direct reads and deterministic lexical retrieval for exact identifiers, paths, error codes, and equation labels when a semantic backend is disabled, unavailable, or inappropriate for a read-only operation.
- Source: S01, Retained alternatives and human interfaces, Prefer hybrid retrieval, but validate exact sources, and Phase 1.
- Acceptance: Exact-term fixture queries return the expected permitted source with usable locators; empty and no-match cases are explicit, and degraded results disclose lexical/direct-read coverage without claiming semantic retrieval or silently creating an index.
- Depends on: REQ-012, REQ-014

### REQ-016 - Evaluate combined exact and conceptual retrieval
- Requirement: Include Basic Memory hybrid retrieval in the pilot so conceptual queries can complement exact-term lookup while retaining lifecycle, project, provenance, and version constraints.
- Source: U02; S01, Basic Memory remains the preferred first backend and Prefer hybrid retrieval, but validate exact sources; B02.
- Acceptance: The pilot records results for representative exact and conceptual queries against known relevant records, distinguishes actual retrieval modes, and reports missed or misleading results without treating ranking as evidence of truth.
- Depends on: REQ-008, REQ-014, REQ-050

### REQ-017 - Preserve strict read-only behavior
- Requirement: Keep memory `search`, `read`, `validate`, and `health` non-mutating, including when configuration or backend state is missing or stale.
- Source: S01, Task activation must not become a memory side effect and Phase 1; L03.
- Acceptance: Read-only checks leave governed file bytes and modification timestamps unchanged and do not initialize databases, synchronize files, repair indexes, install packages, download models, or enable cloud routing; a permitted direct-read fallback or an explicit limitation is returned instead.
- Depends on: REQ-011, REQ-015

### REQ-018 - Separate inspection from maintenance operations
- Requirement: Expose documented operations for `search`, `read`, `propose`, `publish`, `supersede`, `retract`, `validate`, `reindex`, and `health`, with each operation's write boundary and required scope explicit.
- Source: S01, Phase 1 and Publication, concurrency, and recovery.
- Acceptance: The interface distinguishes read-only inspection, bounded proposal output, canonical publication, derived-index rebuilding, and recovery; no read operation silently performs a maintenance operation, and mutations without their required scope are rejected.
- Depends on: REQ-017, REQ-020

### REQ-019 - Keep secrets and source instructions out of authority
- Requirement: Exclude credentials, unnecessary personal data, hidden reasoning, full transcripts, and unauthorized project content from records and retrieval products, and treat retrieved instructions as source data.
- Source: U01; S01, Configuration owned by Sys4AI, Supersession, staleness, and correction, and Prefer hybrid retrieval, but validate exact sources; L01.
- Acceptance: Sensitive fixture content is excluded at ingestion, retrieval, and publication boundaries, and an instruction embedded in a note or source cannot expand permissions or trigger an external action.
- Depends on: REQ-012, REQ-013

### REQ-020 - Apply the agreed publication authority
- Requirement: Allow the owning Project Director or confirmed Task manager to approve and activate evidence-backed notes within its explicitly granted memory scope, without an additional per-note user approval.
- Source: U03; S01, Add memory responsibilities to existing roles and Publication, concurrency, and recovery; L01; L03.
- Acceptance: Publication checks the actual publisher, current project/execution ownership where applicable, granted memory scope, reviewed content, evidence, and expected record version; out-of-scope, stale, or unconfirmed publishers fail, and a host cannot compete with an activated manager's assigned scope.
- Depends on: REQ-006

### REQ-021 - Keep child outputs as proposals
- Requirement: Have workers, solvers, reviewers, seniors, and implementers return proposed findings through their authorized result artifacts rather than publishing shared active memories.
- Source: S01, Add memory responsibilities to existing roles and Capture durable knowledge at the right point; L03; L04.
- Acceptance: A child's useful proposed note is inspectable by its authorized Director or manager, but it does not become shared recall or confer canonical Task, role-index, or unrestricted memory write rights before approved publication.
- Depends on: REQ-020

### REQ-022 - Prevent alternate backend publication routes
- Requirement: Keep canonical memory publication under the Sys4AI helper and prevent ordinary backend tools from providing an unrestricted alternate writer to solvers or other unauthorized actors.
- Source: S01, Basic Memory remains the preferred first backend and Publication, concurrency, and recovery.
- Acceptance: Indexing and retrieval preserve canonical note, Task, and role bytes; either a verified non-mutating canonical read profile or a derived projection is used, and actual exposed tools are checked for canonical write bypasses.
- Depends on: REQ-017, REQ-020, REQ-021

### REQ-023 - Publish single-record changes without lost updates
- Requirement: Validate single-record changes before atomic publication, serialize conflicting writes with a project-local memory lock, and require the expected prior digest for an existing record.
- Source: S01, Publication, concurrency, and recovery.
- Acceptance: Concurrent or stale writes produce a reported conflict with no lost update; a human edit is detected before replacement, unrelated notes remain intact, and a failed pre-publication check leaves canonical content unchanged.
- Depends on: REQ-005, REQ-020

### REQ-024 - Recover multi-record lifecycle changes accurately
- Requirement: Make supersession and other multi-record memory changes recoverable, using a bounded transaction or deterministic append-first representation with attributable idempotent retries.
- Source: S01, Publication, concurrency, and recovery.
- Acceptance: Interruption at each publication boundary yields a report of the actual committed state; recovery preserves identities and history without duplicate records, lost reasons, silent half-supersession, or an unsupported claim of full success.
- Depends on: REQ-007, REQ-023

### REQ-025 - Keep Task and memory publication boundaries separate
- Requirement: Reference actual memory publication results through permitted Task evidence/response mechanisms without replaying execution or manufacturing Task acceptance to repair a note.
- Source: S01, Publication, concurrency, and recovery; L03.
- Acceptance: A failed required memory deliverable remains an unmet criterion; failure of optional later capture is reported separately, and retry never reopens a terminal Task, relaunches agents, or repeats an already committed Task event merely to repair memory.
- Depends on: REQ-003, REQ-024, REQ-035

### REQ-026 - Classify rebuildable state and recovery data
- Requirement: Separate declared rebuildable retrieval and normalization products under `.sys4ai/memory/` from backend configuration, accepted writes awaiting materialization, and durable memory-maintenance recovery information.
- Source: S01, Keep rebuildable data separate from recovery information.
- Acceptance: Rebuilding or deleting only declared retrieval products loses no accepted memory and touches neither Template-update nor role-transition recovery; cleanup rejects unclassified or sole-copy durable content, and recovery receipts are excluded from semantic recall.
- Depends on: REQ-001, REQ-024

### REQ-027 - Preserve TeX as research evidence
- Requirement: Treat permitted TeX as a first-class source and retain section structure, raw equations, theorem/lemma/proof environments, labels, references, bibliography keys, and useful source locators during normalization.
- Source: S01, Treat TeX as a first-class research source.
- Acceptance: Representative mathematical fixtures retain their original expressions and identifiers in retrievable evidence without an LLM rewriting equations; matched material can be traced to the source section or label.
- Depends on: REQ-013, REQ-014

### REQ-028 - Preserve PDF provenance and extraction limits
- Requirement: Normalize permitted PDFs with source path/digest, page boundaries, available metadata, and extracted text while exposing uncertain or unsupported extraction.
- Source: S01, Normalize PDFs and HTML into a rebuildable layer; L01.
- Acceptance: Retrieved text identifies its source page and version; difficult equations, tables, scans, or layouts are flagged for a supported richer extraction or visual check instead of becoming unqualified accepted findings.
- Depends on: REQ-013, REQ-014, REQ-026

### REQ-029 - Preserve useful HTML structure
- Requirement: Normalize permitted HTML with its source location, version, and relevant headings while removing navigation and presentation material from the retrieval representation.
- Source: S01, Normalize PDFs and HTML into a rebuildable layer.
- Acceptance: Representative HTML queries return substantive source content with locators rather than navigation noise, and normalization leaves the original source bytes unchanged.
- Depends on: REQ-013, REQ-014, REQ-026

### REQ-030 - Keep derived representations attributable
- Requirement: Bind normalization products to source digests, regenerate them deliberately after source changes, and group a TeX source with its generated PDF under one source identity when their relationship is known.
- Source: S01, Treat TeX as a first-class research source and Normalize PDFs and HTML into a rebuildable layer.
- Acceptance: Stale extractions are detectable and rebuildable, and duplicate TeX/PDF representations do not dominate retrieval as independent evidence; unrelated documents are not merged by filename similarity alone.
- Depends on: REQ-026, REQ-027, REQ-028, REQ-029

### REQ-031 - Freeze shared memory before independent solvers
- Requirement: Before the first initial solver starts, have the confirmed manager select eligible previously accepted memories and provide every initial solver with the same bounded, versioned memory context packet.
- Source: S01, Freeze memory context before independent solver work; L03.
- Acceptance: The packet records selected note IDs and exact digests, relevant evidence digests, inclusion limits, and its own digest through existing Task evidence mechanisms; every solver, including queued solvers, receives that packet, with an explicit empty packet permitted when no memory is relevant.
- Depends on: REQ-008, REQ-020, REQ-035

### REQ-032 - Prevent sibling information leakage
- Requirement: Exclude current-execution candidate drafts, reviewer comments, synthesis drafts, and proposed memories from independent solvers' shared recall, indirect corpus copies, and inherited context.
- Source: S01, Freeze memory context before independent solver work; L03.
- Acceptance: A planted sibling draft is absent from another initial solver's direct, indexed, and inherited inputs; contaminated full-history forks are rejected or replaced through a supported isolation mechanism rather than declared independent by an instruction to ignore the draft.
- Depends on: REQ-013, REQ-021, REQ-031

### REQ-033 - Bound additional retrieval during independent work
- Requirement: Keep any further solver retrieval within the frozen memory baseline and assignment's permitted sources until an authorized material input change is applied.
- Source: S01, Freeze memory context before independent solver work and Material memory changes are material input changes.
- Acceptance: A newly published or edited note cannot silently change one solver's supplied memory or expose a sibling solution; additional allowed evidence remains attributable to the assignment and its current input version.
- Depends on: REQ-031, REQ-032

### REQ-034 - Apply material memory changes through existing gates
- Requirement: Route material changes in memory evidence through the existing baseline, conflict, reconciliation, and assignment-input procedures before affected work continues.
- Source: S01, Material memory changes are material input changes; L03.
- Acceptance: A changed material conclusion invalidates affected reviews, synthesis, acceptance, and implementation targets; running writers are reconciled before rebinding, while an immaterial edit receives an explicit materiality assessment without an automatic execution restart.
- Depends on: REQ-008, REQ-033, REQ-035

### REQ-035 - Use existing Task interfaces and preserve history
- Requirement: Attach memory context and results through the current inspected-source, versioned input, registered artifact, and normal response-file reference mechanisms, without extending the Task schema for this release.
- Source: S01, Reuse existing evidence fields; do not invent a Task schema; L03.
- Acceptance: Memory evidence satisfies the helper's actual path/ownership contracts; unsupported fields such as `memory_state` or invented promotion events remain rejected, and historical schema-1 Tasks stay readable and byte-preserved without implicit upgrades.
- Depends on: REQ-003

### REQ-036 - Preserve fresh role discovery
- Requirement: Obtain current role eligibility through the existing fresh filesystem-backed catalog and exact active `Roles/` pairs before each role-based selection or assignment.
- Source: S01, Keep authority, evidence, memory, and indexes distinct and Add memory responsibilities to existing roles; L03; L04.
- Acceptance: Remembered role names, historical hashes, or a stale role index cannot qualify a missing or invalid pair; stored role provenance remains historical and does not replace current pair reads.
- Depends on: REQ-002

### REQ-037 - Preserve real manager ownership and stopping evidence
- Requirement: Preserve the existing reservation, native launch receipt, role-read, activation, sole-writer, generation, stopping, and reconciliation gates when memory is used.
- Source: S01, Harness memory remains complementary, Use the existing execution chain, and Add memory responsibilities to existing roles; L01; L03.
- Acceptance: A restored session, remembered manager, or note cannot activate, replace, resume, or prove the stopping of a native owner; the host and confirmed manager retain their current separate responsibilities.
- Depends on: REQ-002, REQ-020

### REQ-038 - Preserve category teams and effective settings
- Requirement: Add memory responsibilities without changing the required `generic`, `complex`, and `extra-complex` teams, independent identities, review gates, or effective model and reasoning-effort requirements.
- Source: S01, Use the existing execution chain and Add memory responsibilities to existing roles; L03; L04.
- Acceptance: Generic memory capture adds no reviewer/senior/extra implementer, complex work adds no mandatory per-candidate review stage, extra-complex work retains every required current review, and remembered preferences cannot alter settings or shrink teams.
- Depends on: REQ-003, REQ-031, REQ-036, REQ-037

### REQ-039 - Keep memory free of Task lifecycle side effects
- Requirement: Preserve the owning project's installed Task activation/selection policy and its read-only startup/status/list/show/continue/validate behavior when memory is integrated.
- Source: S01, Task activation must not become a memory side effect; L01; L03.
- Acceptance: Memory lookup creates, resumes, closes, or upgrades no Task and changes no role/index; root intake and 30-day closure policy remain distinct from generic Template policy, and read-only Task routes omit any backend operation that would mutate state.
- Depends on: REQ-017, REQ-035, REQ-036

### REQ-040 - Deliver a complete reusable memory package
- Requirement: Provide the memory skill, helper, references, policy/schema support, examples, operating guidance, and proportionate tests as complete reusable assets with clear installation and invocation boundaries.
- Source: U02; S01, Reusable sources and project-local files, Phase 1, and Phase 3.
- Acceptance: The published package can be inspected and validated as a complete capability; examples are clearly non-active, documentation explains lookup/proposal/publication/maintenance flows and limits, and no optional editor or harness-specific memory becomes required canonical storage.
- Depends on: REQ-004, REQ-018

### REQ-041 - Integrate existing guidance and role responsibilities
- Requirement: Add bounded memory guidance to reusable Task, Agent Task, role-management, Project Director, Task Manager, and applicable general sub-agent assets, referencing their existing execution contracts.
- Source: U02; S01, Add memory responsibilities to existing roles and Phases 2-3; L01; L03; L04.
- Acceptance: Guidance identifies when to inspect current sources and memory, freeze context, return proposals, and publish within granted scope; it preserves role/function/native identity distinctions and introduces no duplicate execution protocol or mandatory memory role.
- Depends on: REQ-020, REQ-021, REQ-031, REQ-036, REQ-038, REQ-039, REQ-040

### REQ-042 - Publish through the actual Template pipeline
- Requirement: Add explicit Template mappings for active memory starter files and publish complete memory assets through the existing source-to-Template update process.
- Source: U02; S01, Phase 3; L02.
- Acceptance: Starter README/config reach their intended active destinations, contract assets and the complete memory skill reach their mapped destinations, and checked add/change/removal scenarios preserve ownership and report customized-target conflicts instead of overwriting them.
- Depends on: REQ-004, REQ-040, REQ-041

### REQ-043 - Keep Template memory empty
- Requirement: Give the Template an empty memory capability consisting of the selected starter README/config and reusable contract assets, without learned records or specialized root identity/runtime paths.
- Source: S01, Reusable sources and project-local files and Phase 3; L02.
- Acceptance: The Template contains `MEMORY/README.md`, an unspecialized `memory.yaml`, and the complete published capability; creating optional record directories does not require populating examples or copying a root memory tree.
- Depends on: REQ-011, REQ-042

### REQ-044 - Initialize a distinct new-project capability
- Requirement: Extend the initializer's explicit starter selection and identity/path specialization so a new project receives only its own empty memory capability from the Template.
- Source: U02; S01, Configuration owned by Sys4AI and Phase 3; L02.
- Acceptance: A disposable created project has a distinct stable project identity, correct adopted contract/config paths, and no learned root/other-project records or inherited absolute backend directories; missing memory starter selection is detected by verification.
- Depends on: REQ-012, REQ-043

### REQ-045 - Preserve existing memory and prior setup editions
- Requirement: Preserve existing-project memory/configuration and the original semantics of older setup receipts during preparation and equivalent reruns.
- Source: S01, Phase 3; L01; L02; U02, existing-product adoption is deferred.
- Acceptance: Disposable existing-project fixtures retain their memory and configuration bytes, customization, and older receipt behavior; a rerun does not silently adopt a new memory edition, overwrite records, or become a migration of an actual product.
- Depends on: REQ-043, REQ-044

### REQ-046 - Record memory starter adoption factually
- Requirement: Define the necessary setup-edition and receipt changes so newly authorized memory starter adoption records its actual source assets, specialization, preservation, and verification without implying runtime provisioning or expanded registry authority.
- Source: S01, Phase 3; L01; L02.
- Acceptance: New-edition fixture receipts distinguish copied, specialized, and preserved assets; interrupted setup follows the checked same-request recovery flow, earlier editions retain their requirements, and registration does not enable cross-project memory access or backend installation.
- Depends on: REQ-044, REQ-045

### REQ-047 - Document ownership, dependencies, and exact paths
- Requirement: Update applicable reusable guidance, specifications, navigation, and ignore rules to describe memory ownership, configuration, dependency provisioning, and classified runtime paths while preserving project-specific content.
- Source: S01, Phase 3 and Repository discrepancy to resolve during adoption; L01; L02; L04.
- Acceptance: New active role references use `Roles/`, historical lowercase provenance is retained, dependency/configuration guidance agrees with the selected implementation, and ignore/cleanup rules cannot hide canonical memory or classify unrelated recovery state as disposable.
- Depends on: REQ-026, REQ-040, REQ-041

### REQ-048 - Adopt the reviewed capability into the active root
- Requirement: Adopt the first-release capability into `/Volumes/P-SSD/AngryOwl/Sys4AI` through an explicit reviewed source/destination file set and preservation boundary after reusable sources and the Template are verified.
- Source: U02; S01, Phase 5; L01; L02.
- Acceptance: The root has its own memory records/configuration and the intended active skill/guidance integration; its local intake policies and unrelated files are preserved, and no existing product is changed or declared adopted through source publication alone.
- Depends on: REQ-041, REQ-042, REQ-047

### REQ-049 - Keep dependency ownership explicit
- Requirement: Preserve the root's specified Python environment and the standard-library independence of Task/role helpers while declaring any memory configuration, extraction, or retrieval dependencies in their actual owning runtime.
- Source: S01, Configuration owned by Sys4AI, Normalize PDFs and HTML into a rebuildable layer, and Phase 1; L01.
- Acceptance: The chosen YAML strategy is either an explicitly declared parser or a documented constrained representation; PDF/backend availability is checked per environment, and importing or using Task/role inspection does not acquire an undeclared memory dependency.
- Depends on: REQ-003, REQ-011, REQ-028

### REQ-050 - Define a controlled Basic Memory profile
- Requirement: Pilot a pinned Basic Memory version with explicit local project/configuration binding, no automatic frontmatter rewriting or updating, and an adapter that preserves Sys4AI canonical publication controls.
- Source: U02; S01, Basic Memory remains the preferred first backend and Phase 4; B01.
- Acceptance: Effective configuration verifies the selected version's equivalents of `BASIC_MEMORY_CONFIG_DIR`, `BASIC_MEMORY_MCP_PROJECT`, `ensure_frontmatter_on_sync=false`, and `auto_update=false`; canonical hashes remain unchanged through indexing/search, and settings are not represented as an OS sandbox.
- Depends on: REQ-011, REQ-012, REQ-022, REQ-049

### REQ-051 - Preserve metadata across the adapter
- Requirement: Map Sys4AI record metadata into the selected Basic Memory representation without losing custom provenance, lifecycle, identity, or creation/modification chronology.
- Source: S01, Durable records with explicit scope and provenance; B03.
- Acceptance: Round-trip or projection checks retain the authoritative record meaning and exact canonical bytes; `modified` is mapped intentionally so competing timestamp fields or backend-generated metadata do not silently change recency or approval semantics.
- Depends on: REQ-005, REQ-007, REQ-050

### REQ-052 - Exercise the backend compatibility pilot
- Requirement: Run the selected Basic Memory profile against representative isolated fixtures and the bounded active-root adoption context, recording actual backend behavior for isolation, preservation, retrieval, publication controls, rebuilds, and outage behavior.
- Source: U02; S01, Phase 4 and Acceptance checks for the implementation.
- Acceptance: Evidence includes cross-project sentinels, source/note hashes before and after indexing/search, exact/conceptual queries, attempted writer bypasses, declared-cache rebuilds, and backend-disabled/unavailable fallback; any failed or unexercised check is reported explicitly rather than inferred from vendor documentation.
- Depends on: REQ-012, REQ-015, REQ-016, REQ-022, REQ-026, REQ-048, REQ-050, REQ-051

### REQ-053 - Make backend enablement conditional on evidence
- Requirement: Conclude the pilot with an attributable compatibility decision and enable root semantic use only when all mandatory isolation, preservation, publication-control, and operational checks pass.
- Source: S01, Basic Memory remains the preferred first backend and Phase 4; U02.
- Acceptance: A passing decision references the tested version/configuration and actual results; a failing or incomplete pilot leaves semantic enablement off, preserves lexical/direct-read operation, and reports the remaining incompatibility without claiming successful backend adoption or substituting another backend.
- Depends on: REQ-052

### REQ-054 - Separate runtime provisioning from reads and setup
- Requirement: Make backend installation, model provisioning, MCP registration, and runtime activation explicit downstream actions, while new-project setup and ordinary reads remain usable without them.
- Source: S01, Configuration owned by Sys4AI and Phase 4; L01; U02.
- Acceptance: The local pilot records the authorized runtime/configuration it actually uses; starter creation and reads trigger no package/model download, external provider request, or cloud synchronization, and backend outage does not trigger automatic provisioning.
- Depends on: REQ-017, REQ-044, REQ-049, REQ-050

### REQ-055 - Review the selected backend's operational fit
- Requirement: Before committing to backend adoption, assess the selected version's license, integration method, model requirements, local resource use, and any cost implications using current evidence.
- Source: S01, Retained alternatives and human interfaces and Phase 4.
- Acceptance: The pilot report names the selected versions and operating prerequisites, separates observed resource behavior from estimates, and records any adoption constraint; historical pricing, rankings, and performance claims are not treated as current guarantees.
- Depends on: REQ-049, REQ-050

### REQ-056 - Verify deterministic contracts and preservation
- Requirement: Verify the new memory contracts and affected root, reusable-skill, Template, and initializer behavior with proportionate deterministic tests and before/after preservation checks.
- Source: S01, Acceptance checks for the implementation; L01; L03.
- Acceptance: Coverage includes record validation/staleness, unauthorized and conflicting writes, interrupted publication/retry, cache safety, read-only timestamps, empty initialization, existing-fixture preservation, legacy Task rejection/compatibility, category integrity, and Template conflict handling; every failure remains visible.
- Depends on: REQ-006, REQ-008, REQ-017, REQ-023, REQ-024, REQ-025, REQ-026, REQ-035, REQ-038, REQ-042, REQ-044, REQ-045, REQ-046

### REQ-057 - Verify native and integrated memory use
- Requirement: Exercise actual native Task/role memory integration and representative end-to-end capture/retrieval in the adopted root, using disposable inputs where needed to preserve project knowledge.
- Source: S01, Freeze memory context before independent solver work, Phase 5, and Acceptance checks for the implementation; L03.
- Acceptance: Actual receipts establish manager activation/ownership, required role reads, supplied packet versions, solver-context isolation, and stopping; a supported fresh context can retrieve an approved project note with its evidence, and deterministic tests are not substituted for native or backend observations.
- Depends on: REQ-020, REQ-031, REQ-032, REQ-034, REQ-036, REQ-037, REQ-038, REQ-039, REQ-048, REQ-052, REQ-056

### REQ-058 - Preserve history during correction and migration
- Requirement: Require explicit scoped authority, inspected current versions, preserved originals where appropriate, and recoverable changes for sensitive-data redaction or any necessary memory-record migration; ordinary adoption must not migrate or delete intellectual history automatically.
- Source: S01, Supersession, staleness, and correction and Phase 5; L01.
- Acceptance: A schema/profile change or setup rerun does not silently overwrite existing notes; an authorized correction records its reason and actual change boundary, and retention policy does not force continued storage of credentials or unnecessary personal data.
- Depends on: REQ-007, REQ-019, REQ-024, REQ-045

### REQ-059 - Report release evidence at its actual level
- Requirement: Provide a final requirement-by-requirement release assessment distinguishing source inspection, structural checks, deterministic tests, backend observations, native observations, and end-to-end results.
- Source: S01, Acceptance checks for the implementation; L01; L03.
- Acceptance: Each requirement and changed artifact has current evidence or an explicit unmet/unexercised result, the pilot decision and active-root adoption status are distinct, and no claim is made that existing products, Git publication, deployment, or untested future environments were exercised.
- Depends on: REQ-048, REQ-053, REQ-054, REQ-055, REQ-056, REQ-057, REQ-058

## Decisions

- D01: U02 fixes the first-release scope. Reusable sources, the registered Template, initializer behavior, the active root, and a Basic Memory pilot are included. Cognee and actual existing-product adoption are excluded. Disposable project fixtures verify isolation and preservation without expanding product adoption.
- D02: U03 delegates active-note approval to the Project Director or confirmed Task manager only within its granted scope. Approval is bound to reviewed content and current authority; manager activation alone grants no arbitrary memory write scope. This policy is an outcome to implement after separately authorized adoption, not authority for this TRD workflow to publish memories.
- D03: S01 makes backend adoption conditional on compatibility evidence. Completing a documented pilot evaluation and successfully enabling the backend are distinct outcomes. A negative or incomplete result keeps semantic use disabled; it does not reduce required checks or authorize Cognee as a substitute.
- D04: The local Basic Memory pilot and isolated fixtures fit U02's root-only adoption boundary and S01's project-local first release. Exact disposable paths, the staged pilot arrangement, pinned backend/model versions, parser, extraction libraries, adapter APIs, transaction representation, and adopted root contract location are implementation choices. Planning must satisfy the requirements above and cannot introduce cloud routing, cross-project scope, ungranted publication authority, or hidden dependencies.
- D05: S01's YAML, record IDs, directory examples, and proposed operation names describe a contract direction rather than existing helper payloads. Required behaviors, file ownership, named record types/states, project-local `MEMORY/` and `memory.yaml`, complete capability distribution, and the specified control boundaries are retained. Internal schema field spellings and package layout can be chosen consistently during planning without inventing current Task fields or changing the existing Task schema.
- D06: The live README already uses the correct `Roles/` spelling. No obsolete lowercase-navigation repair is required; current active references and historical provenance remain protected by REQ-047.
- D07: S01's acceptance examples are future release criteria, not tests run during its review or this TRD capture. Numerical performance targets and unverified product rankings are not added. Pilot fixture/query selection and operational measurements belong to planning within the specified pass/fail boundaries.
- D08: This capture changes only the managed TRD and its generated index. Its `trd_done` state will require approval of the exact presented revision and will establish document completion only.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
