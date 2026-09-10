---
schema_version: 2
trd_id: "TRD-20260909-5D0F500E"
title: "Sys4AI Ontology Knowledge System first release"
slug: "sys4ai-ontology-knowledge-system-first-release"
created_at: "2026-09-09T09:21:44-06:00"
updated_at: "2026-09-09T10:10:54-06:00"
status: "trd_done"
revision: 3
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 2 and its exact SHA256 digest as the completed requirements document."
---

# Task Requirement Document: Sys4AI Ontology Knowledge System first release

## Destination

Provide a first release of a project-local Ontology Knowledge System for Sys4AI agents and human maintainers. It supplies explicit project meanings, typed relationships, source provenance, capability discovery, a generated knowledge wiki, and bounded integration with current memory and Task workflows.

## Captured user intent

- U01: The user invoked the project-local to-trd skill for the shared file, Research and Architecture Recommendations for an Ontology System in Sys4AI.md, and instructed that document content be distinguished from the user's request.
- U02: In the subsequent clarification, the user answered yes to a first-release TRD covering the ontology core, root and Template setup, retrieval, generated wiki, system bindings, and memory/Task integration, with advanced reasoning, RDF/SPARQL, execution guardrails, and visual editing left for later work.
- This capture produces a requirements document only. U02 settles the release scope; it does not approve an unseen TRD revision or authorize downstream planning, implementation, delegation, installation, Git, migration, publication, or external action.

## Context and sources

The established project root is /Volumes/P-SSD/AngryOwl/Sys4AI. Current inspection found no ONTOLOGY-depo/, ONTOLOGY/, ontology.yaml, or installed/source ontology skill in the depot, and no ontology starter in the registered Template. This is a new first-release baseline, not a resumption or restoration of an older ontology implementation.

The current depot has a separate project memory capability. memory.yaml uses project identity sys4ai-depot, retains its own corpus exclusions, and has an optional Basic Memory backend configured; configuration is not evidence of a successful live backend check. The memory record schema is version 1, rejects unsupported fields, and provides no automatic migration. The installed initializer currently uses governance-starter-v7 and preserves earlier receipt editions. Startup Task inspection was read-only and reported no nonterminal Tasks; this capture creates none.

R01: [Research and Architecture Recommendations for an Ontology System in Sys4AI.md](</Users/alex.omegapy/Downloads/Research and Architecture Recommendations for an Ontology System in Sys4AI.md>), supplied by the user. SHA256: `db0e5ac09d1c17fe326e9afbe73340e1ea3ad07da8c092e12a06701cb7cb3918`. Its named sections and ONT-* table identifiers are used as precise source locators. The 85 table rows are research recommendations, not independent action authority. U02 selects the release boundary used below.

R01 contains citation markers whose underlying external pages and attachments are not available as resolved citations in this file. This TRD attributes those statements to the supplied report and does not claim to have independently verified those external sources. Reported research percentages are not adopted as Sys4AI performance promises or acceptance targets.

Current project sources were inspected on 2026-09-09:

| Source | Locator and relevant constraint |
| --- | --- |
| P01 | [AGENTS.md](../AGENTS.md) and [ROLE.md](../ROLE.md): depot ownership, explicit adoption, current authority, Task separation, exact manager ownership, and role sources. |
| P02 | [SOUL.md](../SOUL.md) and [SPECS.md](../SPECS.md): source-first work, Python 3.12 standard-library core, preservation, verification, and validation. |
| P03 | [depot/projects.json](../depot/projects.json): factual inventory identifying sys4ai-depot and the registered Sys4AI Template Project. |
| P04 | [memory.yaml](../memory.yaml) and [record-v1.json](../reference-assets/MEMORY-depo/schema/record-v1.json): independent memory configuration, corpus boundaries, fixed record schema, and no automatic migration. |
| P05 | [Memory publication and recovery](../reference-assets/MEMORY-depo/publication-and-recovery.md): current scoped Director/manager grants, exact reviewed changes, source/version checks, durable receipts, and partial recovery. This supplies an authority pattern, not an ontology grant. |
| P06 | [Memory in an existing Task execution](../.agents/skills/memory/references/task-integration.md): existing Task artifact/input interfaces, immutable packet references, identical solver input, exclusion rules, and reassessment. |
| P07 | [Template mapping](../depot/template-update.json), [initializer contract](../.agents/skills/init-new-project/SKILL.md), and [starter inventory](../.agents/skills/init-new-project/assets/baseline-assets.json): existing distribution, neutral setup, prior-edition adoption, receipt provenance, and preservation rules. |
| P08 | [to-trd skill](../.agents/skills/to-trd/SKILL.md): requirements-only capture, helper-managed document state, and explicit approval of the exact saved revision. |

## In scope

- A deterministic, service-independent ontology core, explicit project configuration, stable identities, local source bindings, validation, lifecycle, and scoped canonical publication.
- Reusable contracts and core vocabulary in ONTOLOGY-depo/, an ontology skill in SKILLS-depo/ontology/, exact root adoption, and propagation into the registered Template through the existing updater.
- Neutral ontology capability for new projects, initializer specialization, and an explicit prior-edition adoption/upgrade route with preservation and receipt checks.
- Exact/alias/lexical retrieval, bounded typed graph traversal, capability lookup, source verification, agent-facing query routing, and a generated Markdown wiki.
- Current Skill, Role, Artifact, Specification, and registry bindings; derived memory links and query expansion; immutable ontology packets using current Task interfaces.
- Structural and competency checks plus observed interface/integration acceptance. Reusable core data covers Sys4AI vocabulary; selected root instances describe the depot.

## Out of scope

- The optional standards backend, RDFLib/pySHACL installation, SPARQL, Turtle/RDF/XML exports, SHACL shapes, and standards-grade PROV-O export are later work. The local compact JSON-LD authoring profile and source provenance remain included. R01: ONT-PROV-03, ONT-VAL-06, ONT-RET-07, ONT-NFR-02; U02.
- A new ontology embedding/vector backend is deferred; first-release ontology retrieval is exact, alias, lexical, and graph-based. Existing project memory backend choices remain intact. R01: ONT-RET-03; U02.
- A static interactive graph viewer, visual ontology editor, and Ontology-Playground-style interface are deferred. The generated Markdown wiki and its navigation are included. R01: ONT-WIKI-05; U02.
- Semantic pre-execution gates, tool-call interception, and action-loop guardrails are deferred. ActionType remains a modeled concept, and the prohibition on ontology granting execution authority remains required. R01: ONT-AGENT-04, ONT-AGENT-05; U02.
- There is no agent-provided SPARQL endpoint in this release, so SPARQL federation and local-file query access are not exposed. Any later backend must address this source security requirement under its own scope. R01: ONT-SEC-04; U02.
- Full OWL reasoning, graph databases, dynamic ontology extraction/refinement, GraphRAG experiments, autonomous semantic publication, and agent training are deferred under U02.
- Memory schema v2, adding ontology_refs to current memory records, merging memory and ontology stores, changing the current memory corpus, or activating/replacing a memory backend are excluded.
- Root-wide recursive ingestion, child-project domain import, automatic adoption by existing products, bulk rewriting of skills/roles, and restoration of retired ontology or Memory Service components are excluded. The release supports selected future adoption without performing a real product rollout.
- Hosted services, hosted CI provisioning, Git/GitHub activity, website publication, dependency installation, deployment, and downstream plan/Task execution are not authorized by this document-capture operation. Remote execution/publication requires its separate authority; acceptance is runnable locally.

## Task requirements

### REQ-001 - Keep ontology project-local

- Requirement: Provide a project-local Ontology Knowledge System whose canonical semantics and mutation lifecycle remain separate from memory, Task state, role state, and skill runtime state.
- Source: R01: ONT-ARCH-01, ONT-MEM-01; Executive recommendation. U02: selected first-release scope.
- Acceptance: Ontology operations identify their own canonical store and change boundary; creating, retrieving, or publishing ontology content does not create or activate a Task, alter role ownership, or merge canonical stores.
- Depends on: None.

### REQ-002 - Resolve one explicit project identity and root

- Requirement: Require an explicit resolved project root and project-local ontology.yaml containing project identity, namespace, selected modules, retrieval settings, and publication configuration.
- Source: R01: ONT-ARCH-02, ONT-SEC-01; Proposed Sys4AI ontology design.
- Acceptance: Operations reject unresolved, mismatched, or unspecialized project identity; path resolution prevents traversal or symlink escape into sibling projects or unselected filesystem locations.
- Acceptance: Two projects with the same labels retain separate identities and lookup results.
- Depends on: REQ-001

### REQ-003 - Preserve child-project independence

- Requirement: Limit root ontology lookup to its own approved content and explicit local bindings; factual registry entries may describe child projects without importing their internal vocabularies or granting access or write authority.
- Source: R01: ONT-ARCH-05, ONT-ARCH-06. P01: project identity and reusable-asset boundaries. P03: factual project registry.
- Acceptance: A root query does not open a child project's ontology solely because it is under Projects/ or registered; child ontology changes do not silently change root results.
- Acceptance: Registry-derived representations identify their registry source and do not authorize writes to the represented project.
- Depends on: REQ-002

### REQ-004 - Use one canonical authoring representation

- Requirement: Store ontology entities in a documented compact JSON-LD profile under ONTOLOGY/modules/, explicit canonical binding records under ONTOLOGY/bindings/, and configuration in ontology.yaml; keep these distinct from generated representations.
- Source: R01: ONT-ARCH-03; Canonical versus generated data; Canonical representation. P02: standard-library helper constraint.
- Acceptance: The supported JSON-LD profile and local context define record keys and their meanings; ordinary canonical parsing uses Python 3.12 standard-library JSON support.
- Acceptance: Wiki pages, graph files, indexes, exports, and external tools are not alternative editable sources of canonical ontology facts.
- Acceptance: ontology.yaml follows the project's documented JSON subset of YAML without introducing a core parser dependency.
- Depends on: REQ-002

### REQ-005 - Keep JSON-LD context resolution local

- Requirement: Use trusted, versioned, vendored JSON-LD contexts and reject arbitrary remote contexts or context paths outside the selected project's permitted local files.
- Source: R01: ONT-SEC-03; Optional RDF/SPARQL backend.
- Acceptance: A record containing an HTTP context, an untrusted context, or an escaping file reference is rejected without network access or reading the target.
- Acceptance: Core parsing does not advertise support for unrestricted JSON-LD processing; unsupported profile features receive an explicit diagnostic.
- Depends on: REQ-004

### REQ-006 - Make generated knowledge reproducible

- Requirement: Keep compiled graphs, retrieval indexes, backlinks, caches, and memory-link projections under .sys4ai/ontology/, and generated Markdown pages under ONTOLOGY/WIKI/; rebuild them deterministically from identified canonical inputs.
- Source: R01: ONT-ARCH-03, ONT-ARCH-04, ONT-NFR-03, ONT-NFR-04; Canonical versus generated data.
- Source: P05: publication receipts and maintenance recovery are durable accepted work.
- Acceptance: Two builds from identical ontology, configuration, referenced input bytes, module versions, and generator version produce byte-equivalent generated output.
- Acceptance: Removing a generated projection loses no canonical knowledge; an explicit rebuild restores it and reports its input versions and digests.
- Acceptance: compile and build-wiki modify only their declared generated destinations; failed input validation does not publish an apparently successful build or overwrite unrelated files.
- Acceptance: Approval records, publication receipts, and accepted recovery state are durable records and are not classified or deleted as rebuildable projections.
- Depends on: REQ-004, REQ-005

### REQ-007 - Provide a reusable Sys4AI core module

- Requirement: Maintain a small versioned sys4ai-core module of meaningful Sys4AI concepts and relationships, with reusable contracts and starter assets in ONTOLOGY-depo/ and the executable ontology skill in SKILLS-depo/ontology/.
- Source: R01: ONT-MOD-01; Core ontology versus project ontology; first root concepts in Delivery roadmap. P01: reusable-source ownership.
- Acceptance: The core covers Project, ProjectTemplate, Artifact, Source, Specification, Requirement, Task, TRD, ImplementationPlan, Verification, Evidence, Agent, Role, Skill, Capability, ActionType, MemoryRecord, Lesson, Decision, OntologyConcept, Authority, and Scope, plus terms needed by the competency questions.
- Acceptance: Concepts model meaning, capability, and relationships; a filesystem location is represented as an artifact binding rather than substituted for the concept.
- Acceptance: Product-domain vocabulary and root-specific instances are absent from the reusable core.
- Depends on: REQ-004

### REQ-008 - Lock imported modules

- Requirement: Bind each imported core module to an explicit version and content digest, and retain those import identities in validation, build, retrieval, and packet context.
- Source: R01: ONT-MOD-03, ONT-NFR-04; Core ontology versus project ontology.
- Acceptance: Missing modules or a digest/version mismatch produce a precise diagnostic and cannot be treated as a valid current import.
- Acceptance: A newer depot module does not silently replace a project's selected imported version.
- Depends on: REQ-007

### REQ-009 - Allow project extensions without redefining core identities

- Requirement: Keep project and domain modules local, reuse existing concepts or aliases when appropriate, and require a distinct stable identity for genuinely different semantics instead of silently redefining an imported core ID.
- Source: R01: ONT-MOD-02, ONT-MOD-04; extend-first policy.
- Acceptance: A project-local subtype or distinct concept can extend the selected core; an attempted incompatible redefinition of a core ID is rejected.
- Acceptance: Project extensions remain local and do not automatically modify sys4ai-core or another project's ontology.
- Depends on: REQ-008

### REQ-010 - Keep semantic identities stable

- Requirement: Assign a stable absolute identifier to every modeled class, concept, relationship type, property, capability, action type, and selected project instance; separate semantic identity from labels and file paths.
- Source: R01: ONT-ID-01, ONT-ID-02; Canonical representation.
- Acceptance: Moving a bound artifact or changing a display label preserves the entity ID and existing references.
- Acceptance: Imported core identities remain stable across projects; project-specific identities are unambiguous across project namespaces.
- Acceptance: An identifier is not recycled for a different meaning.
- Depends on: REQ-004, REQ-009

### REQ-011 - Make concepts understandable and searchable

- Requirement: Require approved concepts to carry a preferred label, definition, lifecycle state, module ownership, and source reference, and support aliases, scope notes, examples, non-examples, and broader, narrower, or related relationships where useful.
- Source: R01: ONT-VOC-01, ONT-VOC-02, ONT-VOC-04, ONT-VAL-03; semantic validation examples.
- Acceptance: An approved concept with missing required metadata is invalid; a concept with supported optional explanatory fields retains them through reading and wiki generation.
- Acceptance: Aliases resolve to the underlying stable identity rather than creating accidental duplicate concepts.
- Depends on: REQ-010

### REQ-012 - Represent overloaded terminology explicitly

- Requirement: Model and return explicit distinctions between a Sys4AI Task, a TRD, an implementation plan, a native goal, and a Codex task or conversation; preserve the governing distinction between verification and validation.
- Source: R01: ONT-VOC-03, ONT-AGENT-01; Task vocabulary example. P01: ROLE.md Task activation and ownership. P02: SOUL.md Verification discipline and Validation discipline.
- Acceptance: term Task and term TRD return distinct definitions, stable IDs, relevant distinctions, and current source references.
- Acceptance: Agent-facing answers do not equate document approval with Task activation or implementation completion, or verification with validation.
- Depends on: REQ-011

### REQ-013 - Separate types from concrete instances

- Requirement: Represent ontology types and schemas separately from selected project instances, including concrete skills, roles, artifacts, and projects.
- Source: R01: ONT-GRAPH-04; ontology/component distinction and system binding examples.
- Acceptance: The type Skill is distinguishable from the installed memory skill instance and the SKILL.md artifact that describes it; type and instance queries preserve that distinction.
- Depends on: REQ-010

### REQ-014 - Provide typed directional relationships

- Requirement: Define relationships with stable predicates, direction, permitted source and target types, and supported cardinality constraints or qualifiers where the modeled semantics require them.
- Source: R01: ONT-GRAPH-01, ONT-GRAPH-02, ONT-GRAPH-03; Relationships matter more than a large class hierarchy.
- Acceptance: A relationship has a registered predicate and typed endpoints; incoming and outgoing directions remain distinguishable.
- Acceptance: Configured cardinality and qualifiers survive read/build operations, and invalid endpoint types or cardinalities fail validation.
- Depends on: REQ-013

### REQ-015 - Distinguish assertions from derived knowledge

- Requirement: Preserve the classification and provenance of asserted, derived, inferred, and external or cross-system facts without treating a generated association as an approved canonical assertion.
- Source: R01: ONT-GRAPH-05; Canonical versus generated data. U02: advanced reasoning deferred.
- Acceptance: Retrieval, graph projections, and wiki output identify the kind and source of each included fact.
- Acceptance: Representing an inferred-fact category does not enable an inference engine or allow derived memory links to redefine canonical concepts.
- Depends on: REQ-014

### REQ-016 - Use explicit source bindings

- Requirement: Maintain an ontology-specific allowlist of selected source bindings to project governance, specifications, installed skills, exact role pairs, artifacts, and factual registry metadata without broadening the memory corpus.
- Source: R01: Sys4AI fit and the architectural boundary with memory; System bindings delivery stage; ONT-SEC-02. P04: memory.yaml corpus exclusions. P01: current role sources.
- Acceptance: Bindings may point to selected SOUL.md, AGENTS.md, ROLE.md, SPECS.md, .agents/skills/, Roles/, and depot/projects.json content within the established project policy.
- Acceptance: Unselected child content, credentials, secrets, private runtime data, environments, and caches are excluded; tests show that traversal and symlink references cannot bypass the binding policy.
- Acceptance: Ontology binding setup leaves memory corpus configuration and exclusion rules unchanged.
- Depends on: REQ-002, REQ-013

### REQ-017 - Trace definitions to exact source versions

- Requirement: Attach source-of-truth references to approved project-specific definitions and bindings, including local path, SHA256 digest, and a useful section or other locator; expose source freshness.
- Source: R01: ONT-PROV-01, ONT-PROV-02, ONT-NFR-04; provenance discussion. P01: exact evidence discipline.
- Acceptance: A reviewer can resolve a returned definition to its recorded local source version and locator.
- Acceptance: Changed, missing, or inaccessible source bytes are reported as stale or unavailable and cannot be presented as freshly verified current authority.
- Acceptance: Validation and build results expose source/configuration/module/helper versions and hashes sufficient to reproduce their reported result.
- Depends on: REQ-016, REQ-011

### REQ-018 - Keep meaning separate from permission

- Requirement: Treat ontology as semantic context and capability discovery while current user instructions and governing project, skill, role, and Task contracts continue to control operational authorization.
- Source: R01: ONT-AUTH-01, ONT-AUTH-02, ONT-AUTH-03, ONT-SKILL-04; authorization boundary in ONT-AGENT-05. P01: ROLE.md Authority and non-authority.
- Acceptance: Resolving a capability, reading an action type, or validating an ontology does not invoke a skill or grant Task, role, tool, write, publication, or execution authority.
- Acceptance: When a retrieved definition conflicts with current governing sources, the response identifies the discrepancy and uses those sources for operational rules.
- Acceptance: ActionType may be described as vocabulary; installing execution interception or semantic pre-execution gates is excluded from this release.
- Depends on: REQ-017

### REQ-019 - Require scoped approval for canonical ontology changes

- Requirement: Permit agent publication of canonical ontology changes only through explicit ontology mutation operations with reviewed content, exact expected versions, and current project-local publication authority held by the Director or the confirmed Task manager within its granted scope.
- Source: R01: ONT-LIFE-04; same kind of explicit publication authority as governed Sys4AI assets. P01: Director and confirmed-manager ownership. P05: current memory publication authority pattern.
- Acceptance: The writer supplies the exact reviewed change, reason, expected current digest, and applicable authority; stale content, missing authority, an ordinary child actor, or conflicting manager ownership prevents publication.
- Acceptance: An authorized operation records what actually committed, preserves unrelated bytes, and exposes an exact receipt and bounded recovery result if publication is partial.
- Acceptance: Ontology uses its own publication path and authority scope; possession of a memory publication grant alone does not authorize ontology writes.
- Depends on: REQ-018

### REQ-020 - Preserve lifecycle and deprecated references

- Requirement: Give ontology entities explicit draft, approved, and deprecated states; retain deprecated identifiers and reasons, identify replacements when they exist, and require renewed scoped review when approved semantics change.
- Source: R01: ONT-LIFE-01, ONT-LIFE-02, ONT-LIFE-03. P01: version-bound approval discipline.
- Acceptance: A deprecated ID remains resolvable with its deprecation reason and replacement when present; old references retain their historical meaning.
- Acceptance: A changed definition cannot claim approval of the old bytes, and replacing a concept does not recycle its ID or silently rewrite history.
- Depends on: REQ-019, REQ-010

### REQ-021 - Keep agent suggestions provisional

- Requirement: Keep agent-generated ontology suggestions provisional until deterministic validation and acceptance by the current authorized owner; memory capture must not automatically publish or redefine ontology semantics.
- Source: R01: ONT-LIFE-05, ONT-MEM-02; OaK future-work discussion.
- Acceptance: A suggestion or captured memory remains a proposal and cannot appear as an approved canonical definition without the required publication operation.
- Acceptance: Rejected proposals and ambiguous extracted links do not silently change approved lookup results.
- Depends on: REQ-020

### REQ-022 - Validate identities and references

- Requirement: Reject duplicate stable IDs and dangling targets across the complete selected module and binding set.
- Source: R01: ONT-VAL-01.
- Acceptance: Negative examples with a duplicate ID or unresolved relationship target fail with the offending ID and record location; equivalent valid examples pass.
- Depends on: REQ-008, REQ-014, REQ-016

### REQ-023 - Validate vocabulary ambiguity

- Requirement: Detect preferred-label and alias collisions; permit explicitly modeled ambiguity while preventing silent selection of one conflicting concept.
- Source: R01: ONT-VAL-02.
- Acceptance: An unmodeled collision fails validation; an explicitly modeled collision returns the candidate IDs and their distinctions rather than claiming an exact unambiguous resolution.
- Depends on: REQ-011

### REQ-024 - Validate semantic constraints deterministically

- Requirement: Enforce required concept metadata, valid lifecycle and module ownership, required source references, relation domain/range, configured cardinality, and acyclicity of relationships declared acyclic.
- Source: R01: ONT-VAL-03, ONT-VAL-04, ONT-VAL-05, ONT-VAL-07.
- Acceptance: Focused invalid examples for each configured constraint fail with actionable diagnostics; strict-specialization cycles fail while a cycle in a relation not declared acyclic is not rejected solely for being a cycle.
- Acceptance: Validation is deterministic and runs locally without an LLM, graph service, or optional standards backend.
- Depends on: REQ-022, REQ-023, REQ-020, REQ-017

### REQ-025 - Provide non-mutating ontology operations

- Requirement: Expose health, term, search, read, neighbors, path, and validate through the project-local ontology skill with an explicit project root, without changing canonical or generated state.
- Source: R01: ONT-RET-01; minimal command interface and read-only behavior in Delivery roadmap.
- Acceptance: Running each read operation preserves canonical files, generated files, configuration, and persistent timestamps, including when generated state is missing or stale.
- Acceptance: Ordinary reads do not create directories, rebuild indexes on disk, install dependencies, start services, create Tasks, or publish proposals.
- Depends on: REQ-002, REQ-024

### REQ-026 - Resolve identifiers and vocabulary deterministically

- Requirement: Support stable-ID, exact preferred-label, alias, and lexical lookup over the selected project ontology, with deterministic match priority and stable results for identical inputs.
- Source: R01: ONT-RET-02, ONT-AGENT-01; Retrieval and wiki stage. U02: advanced capabilities deferred.
- Acceptance: Stable-ID and exact-label lookup precede alias and general lexical matches; approved exact matches are not displaced by looser matches.
- Acceptance: An unknown term reports no match; an ambiguous term returns explicit alternatives with IDs and distinctions.
- Acceptance: Retrieval works without embeddings or an external semantic service.
- Depends on: REQ-025, REQ-023

### REQ-027 - Bound graph-based context expansion

- Requirement: Provide incoming and outgoing neighbors, typed relationship lookup, and path traversal with configured maximum hops and bounded result/context size.
- Source: R01: ONT-RET-06, ONT-AGENT-03; Optional RDF/SPARQL backend core operations; path acceptance scenario.
- Acceptance: neighbors Task returns typed relationships from the selected graph; path Task MemoryRecord returns a meaningful path within limits or explicitly reports none.
- Acceptance: A cyclic or densely connected example terminates within the configured limits and identifies any truncation; relation direction and allowed predicates are preserved.
- Acceptance: No fixed performance target or arbitrary hop count is implied; supported limits and defaults are documented.
- Depends on: REQ-026, REQ-014

### REQ-028 - Return explainable ontology results

- Requirement: Return stable ID, label, definition, lifecycle status, module/version context, relevant relationships, provenance, source freshness, and the reason each result matched.
- Source: R01: ONT-RET-04, ONT-RET-05, ONT-NFR-04.
- Acceptance: A human or agent can distinguish ID, preferred-label, alias, lexical, or graph-traversal matches and identify their source versions.
- Acceptance: Draft and deprecated results are explicitly labeled and cannot be mistaken for currently approved definitions.
- Acceptance: Machine-readable output and concise human-facing rendering convey the same result identity and evidence.
- Depends on: REQ-026, REQ-027, REQ-017

### REQ-029 - Report readiness without hidden repair

- Requirement: Report configuration, selected module integrity, validation state, source freshness, and generated-state readiness through health and relevant query diagnostics without mutating or silently repairing the system.
- Source: R01: ONT-RET-01, ONT-NFR-04; health interface and source verification. P02: distinguish configuration from runtime readiness.
- Acceptance: Missing configuration, invalid modules, missing projections, stale source hashes, and an empty project extension produce specific diagnostics.
- Acceptance: Valid empty project extensions can use the imported core; stale generated data is not presented as a verified current answer.
- Acceptance: Any suggested compile or repair remains a separate explicit operation.
- Depends on: REQ-025, REQ-008, REQ-017

### REQ-030 - Generate readable concept pages

- Requirement: Generate the Markdown knowledge wiki from canonical ontology records, including stable identifiers, labels and aliases, definitions, distinctions, relationships, status, source-of-truth references, and backlinks.
- Source: R01: ONT-WIKI-01, ONT-WIKI-02, ONT-WIKI-03; Knowledge wiki.
- Acceptance: A generated Task page explains its distinction from TRD and links to related concepts and recorded governing sources.
- Acceptance: Pages identify themselves as generated, preserve source/classification information, and direct canonical edits to their owning records.
- Acceptance: A wiki rebuild never imports hand-edited page content as canonical ontology.
- Depends on: REQ-006, REQ-028

### REQ-031 - Make the wiki navigable

- Requirement: Generate concept, relationship, module, and capability/skill indexes with working links and backlinks between the generated pages.
- Source: R01: ONT-WIKI-04; Knowledge wiki navigation examples.
- Acceptance: A reader can start at the wiki index, find Task or a memory capability, follow a relationship, and reach its source reference.
- Acceptance: Repeated builds have stable filenames and links; validation detects broken generated internal links.
- Depends on: REQ-030

### REQ-032 - Bind skills to capabilities

- Requirement: Represent installed skills, their capabilities, implemented operations, and source artifacts through explicit ONTOLOGY/bindings/skills.json records rather than requiring ontology metadata changes in every skill package.
- Source: R01: ONT-SKILL-01, ONT-SKILL-02, ONT-SKILL-03; Skill-system integration.
- Acceptance: Capability-to-skill and skill-to-capability queries resolve project memory retrieval and TRD creation to their installed skill sources.
- Acceptance: The to-trd binding accurately states that creating a TRD does not create a Task.
- Acceptance: Missing or changed skill sources are reported as unavailable or stale; capability discovery invokes no skill.
- Depends on: REQ-016, REQ-028, REQ-018

### REQ-033 - Bind roles and governance artifacts to their meanings

- Requirement: Represent the selected project's roles, artifacts, specifications, and governance relationships using explicit bindings to current project-local sources.
- Source: R01: System bindings stage; Integration with memory, skills, tasks, and agent execution. P01: active role pairs and manager ownership.
- Acceptance: Queries identify the artifacts defining a role using its actual AGENTS.md and ROLE.md pair, rather than treating Roles/INDEX.md as authority.
- Acceptance: The graph distinguishes the host Director from a confirmed Task manager and an ordinary child; ontology lookup neither assigns a role nor changes canonical role or Task state.
- Acceptance: Bindings represent selected relevant metadata without requiring a rewrite of every role, skill, or specification file.
- Depends on: REQ-016, REQ-013, REQ-018

### REQ-034 - Route knowledge queries by intent

- Requirement: Provide a lightweight agent-facing knowledge-routing contract that distinguishes definitions, aliases, relationships, capabilities, current operational rules, historical decisions or lessons, and mixed semantic/historical queries.
- Source: R01: ONT-AGENT-02; Unified knowledge routing; query intent table.
- Acceptance: Definition and vocabulary queries use ontology and its source references; relationships use the bounded graph; historical questions use memory.
- Acceptance: Current-authority queries read the current governing sources first; mixed queries resolve ontology terminology, retrieve memory evidence, and verify current sources when an answer concerns current behavior.
- Acceptance: A capability request returns its skill and constraints without executing the operation.
- Depends on: REQ-028, REQ-032, REQ-033

### REQ-035 - Preserve canonical memory and its retrieval policy

- Requirement: Integrate ontology with the current project memory capability while preserving memory schema v1, existing record bytes and historical meaning, publication lifecycle, corpus boundaries, and backend configuration.
- Source: R01: ONT-MEM-01, ONT-MEM-02, ONT-MEM-03; Memory integration without merging stores. P04: memory schema and configuration.
- Acceptance: Ontology publication and linking leave existing memory records byte-identical and valid under the current schema; no ontology_refs field is inserted.
- Acceptance: Memory publication or automatic capture leaves canonical ontology unchanged.
- Acceptance: Ontology setup does not broaden the memory corpus, activate a new memory backend, migrate memory, or alter its existing capture setting.
- Depends on: REQ-019, REQ-021

### REQ-036 - Build derived memory-to-concept links

- Requirement: Store initial associations from memory record identities to stable ontology concept IDs in a rebuildable sidecar under .sys4ai/ontology/links/, with the exact record and ontology versions used and a distinguishable derived-association status.
- Source: R01: ONT-MEM-04, ONT-GRAPH-05, ONT-NFR-04; .sys4ai/ontology/links/memory-records.json example.
- Acceptance: Explicit link generation creates associations only for the selected project's accessible records and resolvable concepts; memory records remain unchanged.
- Acceptance: Ambiguous or unmatched associations are identified rather than published as canonical facts.
- Acceptance: After a source record or ontology version changes, stale associations are detected; explicit rebuilding reproduces current links and does not reuse stale links as verified evidence.
- Depends on: REQ-035, REQ-006, REQ-015

### REQ-037 - Use ontology to improve memory query selection

- Requirement: Allow resolved concepts, aliases, and bounded related concepts to expand or constrain memory queries while preserving the memory system's current source access, lifecycle, evidence, and frozen-input restrictions.
- Source: R01: ONT-MEM-05, ONT-AGENT-03; query expansion example. P06: frozen memory search and permitted sources.
- Acceptance: A query about prior Task manager failures resolves TaskManager-related terminology and retrieves relevant existing historical memory through the supported memory interface.
- Acceptance: Expansion cannot bring excluded sources, another project's records, stale evidence, or new live records into a frozen solver context.
- Acceptance: The response identifies no matching historical evidence or unavailable memory when applicable, without inventing records or provisioning a backend.
- Depends on: REQ-034, REQ-036

### REQ-038 - Keep mixed knowledge evidence distinguishable

- Requirement: Keep ontology definitions, derived associations, historical memory, and current governing-source excerpts distinguishable in combined query responses.
- Source: R01: ONT-MEM-06; Unified knowledge routing and grounded context packet.
- Acceptance: A mixed response identifies each source type, exact concept or record identity, source version, and relevant evidence.
- Acceptance: Historical memory is not upgraded to operational authority by a concept link, and an ontology match is not presented as proof that a historical event occurred.
- Depends on: REQ-037, REQ-018

### REQ-039 - Freeze ontology context as existing Task inputs

- Requirement: Provide immutable ontology context packets containing selected concept IDs, definitions, aliases, relationships, constraint and source references, selected module/configuration versions, and exact source hashes, bound by the existing Task artifact path and SHA256 reference.
- Source: R01: ONT-TASK-01; Task integration and frozen ontology context. P06: existing artifact.register, baseline.inputs, and assignment context contract.
- Acceptance: The current confirmed manager can freeze an explicit selected or empty packet within its granted output scope and register it through existing Task artifact/input mechanisms.
- Acceptance: The complete packet digest is held in its external artifact reference; the packet does not need a self-referential hash.
- Acceptance: Packets obey the current Task reference and artifact limits, exclude sibling drafts and prohibited sources, and introduce no Task schema field or activation route.
- Depends on: REQ-028, REQ-018

### REQ-040 - Keep independent solver inputs identical

- Requirement: Supply the same selected ontology packet and exact digest to every independent initial solver in a round, including queued solvers; prevent later live ontology changes from silently entering their frozen context.
- Source: R01: ONT-TASK-02; identical frozen ontology packet requirement. P06: independent context and frozen source restrictions.
- Acceptance: Each initial assignment references identical ontology packet bytes and permitted source versions.
- Acceptance: Publishing new ontology content after dispatch leaves the packet unchanged; a changed referenced file is detected and not silently substituted.
- Acceptance: Further ontology retrieval for that round is limited to its frozen content and explicitly permitted exact sources.
- Depends on: REQ-039

### REQ-041 - Use existing Task ownership and reassessment

- Requirement: Keep Task activation, writer ownership, category teams, role selection, and state separate from ontology integration; assess material ontology changes through the existing manager-controlled revised-input workflow.
- Source: R01: ONT-TASK-03, ONT-TASK-04. P01: Task authority. P06: material changes and receipt linkage.
- Acceptance: Ontology operations create, resume, complete, or upgrade no Task and do not alter its required team or writer.
- Acceptance: A change affecting current solver meaning is assessed by the confirmed manager and reaches affected workers only through the existing versioned input, reconciliation, review, and acceptance gates.
- Acceptance: An immaterial change retains its reason without requiring an automatic restart.
- Depends on: REQ-040

### REQ-042 - Distribute reusable ontology through the existing Template pipeline

- Requirement: Extend the existing depot mappings and initializer starter inventory to publish reusable ontology contracts, core modules, the ontology skill, and neutral starter configuration into the registered Sys4AI Template Project.
- Source: R01: ONT-TPL-03; template mapping examples. P01: reusable collections. P07: current template mapping and initializer assets.
- Acceptance: Authoritative additions originate in ONTOLOGY-depo/, SKILLS-depo/ontology/, and the affected existing reusable source collections; the Template receives them through tools/template_update.py.
- Acceptance: The update check reports the exact mapped additions and any conflicts before application; affected source/Template contracts validate after application.
- Acceptance: Only the registered Template is automatically updated; unrelated project-local installations remain unchanged.
- Depends on: REQ-007

### REQ-043 - Adopt the first release in the Sys4AI depot root

- Requirement: Provide the root's active ontology skill, project-local configuration, adopted core contracts, approved initial project definitions, and system bindings for the selected Sys4AI depot scope.
- Source: U02: explicitly included root setup. R01: active root installation and ONTOLOGY/ structure. P01: exact reusable-asset adoption boundaries. P03: sys4ai-depot identity.
- Acceptance: The installed root commands resolve project sys4ai-depot and answer the initial competency questions using current root sources.
- Acceptance: Root adoption records the selected source versions and exact changed artifacts, and preserves existing memory, learning, Task, role, licensing, and independent project state.
- Acceptance: The operation does not restore an old ontology or Memory Service runtime or inherit authority from historical records.
- Depends on: REQ-042, REQ-034, REQ-041

### REQ-044 - Keep the Template neutral

- Requirement: Supply the Template with neutral ontology.yaml, an empty project/domain ontology, locked reusable core contracts, and the ontology skill, without copying root-specific definitions, instances, publication bindings, learned records, or runtime products.
- Source: R01: ONT-TPL-01; Core ontology versus project ontology; initializer copy exclusions.
- Acceptance: A Template content inventory contains the reusable capability and core module but no sys4ai-depot instance data, root actor binding, memory links, generated graph/index/cache/wiki build state, or project-private source references.
- Acceptance: An empty project extension is distinguished from missing required capability.
- Depends on: REQ-042, REQ-008

### REQ-045 - Specialize ontology during new-project setup

- Requirement: Extend new-project creation and first preparation through the existing initializer to specialize ontology project ID, name, purpose, namespace, core-module selection, and destination-local Director publication binding.
- Source: R01: ONT-TPL-02; initializer specialization list. P07: current initializer preservation and receipt contracts.
- Acceptance: Disposable create and first-prepare runs produce distinct project identities/namespaces and exact destination-local authority references without root project data.
- Acceptance: Setup receipts distinguish copied assets, specialized configuration, preserved content, and actual capability readiness.
- Acceptance: Initialization installs no external ontology service, RDF backend, embedding model, or product runtime.
- Depends on: REQ-044, REQ-019

### REQ-046 - Support explicit adoption by existing projects

- Requirement: Provide an explicitly selected ontology adoption or upgrade route for an exact existing project, including projects whose completed setup receipt predates ontology, while preserving the original setup edition and provenance.
- Source: R01: ONT-TPL-04; explicit adoption/upgrade policy. P07: prior-edition module adoption and preserved receipt semantics.
- Acceptance: An ordinary rerun of an earlier completed setup neither adds ontology nor relabels the project's base setup edition.
- Acceptance: A selected adoption records source/destination identity, exact module and file versions, overwrite boundaries, preserved content, and current readiness through the existing receipt/recovery model.
- Acceptance: No real existing product project receives ontology solely because this release is installed in the depot or Template.
- Depends on: REQ-045

### REQ-047 - Preserve project-owned content during adoption

- Requirement: Preserve customized ontology and existing memory, learning, skills, roles, Tasks, licenses, configuration choices, and other project-owned content during setup or selected adoption; permit refresh only within the exact authorized file and overwrite boundary.
- Source: R01: ONT-TPL-04; Existing project adoption acceptance scenario. P01: reusable adoption rules. P07: whole-package preservation and recovery.
- Acceptance: A destination containing a customized, incomplete, or incompatible ontology package is preserved and receives precise diagnostics rather than a partial merge or false ready claim.
- Acceptance: Existing memory backend/capture settings, historical records, licenses, and bound governance remain unchanged unless the user separately selects the exact applicable change.
- Acceptance: Interrupted adoption resumes only its same recorded request and expected bytes; changed inputs or conflicting edits prevent unsafe replay.
- Depends on: REQ-046

### REQ-048 - Keep the first-release core service-independent

- Requirement: Run core parsing, deterministic validation, exact/alias/lexical lookup, bounded traversal, wiki generation, and source verification with Python 3.12 standard-library helpers and no external service.
- Source: R01: ONT-NFR-01, ONT-VAL-07; standard-library core and optional RDF backend separation. P02: Python environment.
- Acceptance: The ontology core acceptance checks pass with no graph database, RDFLib, pySHACL, LLM, vector index, or network service available.
- Acceptance: Ontology lookup remains usable when the optional memory backend is unavailable; mixed queries report the memory limitation while retaining valid ontology results.
- Acceptance: Ordinary reads and project setup do not install or initialize optional dependencies.
- Depends on: REQ-025, REQ-030

### REQ-049 - Document authoring, retrieval, and integration

- Requirement: Provide project and reusable documentation for canonical ownership, module extension, identity/lifecycle rules, source bindings, publication authority, supported read/build commands, wiki navigation, memory links, Task packets, and initialization/adoption.
- Source: R01: proposed ONTOLOGY-depo README/policy/contract, ontology skill references, and minimal command interface. P01: documentation ownership.
- Acceptance: A reader can resolve Task, inspect a capability, follow provenance, build the wiki explicitly, and identify the required authority for a proposed canonical edit using documented examples.
- Acceptance: Documentation distinguishes semantic retrieval from execution, generated files from authoring files, setup from operational readiness, and document approval from implementation authority.
- Acceptance: Unimplemented later features are labeled out of scope rather than advertised as available.
- Depends on: REQ-043, REQ-047, REQ-048

### REQ-050 - Specify executable competency questions

- Requirement: Maintain module-owned competency questions with expected semantic results and supporting sources, covering the initial Sys4AI use cases and distinctions.
- Source: R01: ONT-EVAL-01; competency question table. P02: verification/validation distinction.
- Acceptance: The initial checks cover Project and Task meaning; Task versus TRD; project memory and its authority limits; memory-retrieval capability; Task management; role source artifacts; verification versus validation; Template derivation; child-project authority; memory-publication relations; deprecated replacements; and definition provenance.
- Acceptance: Each question has an observable expected concept, relationship, distinction, source, or explicit no-result outcome; success is not defined as an LLM declaring its own answer correct.
- Acceptance: Project extensions can add competency questions without changing the shared core vocabulary.
- Depends on: REQ-012, REQ-034, REQ-049

### REQ-051 - Run structural and competency checks together

- Requirement: Provide one repeatable automated validation entry point that executes structural validation and competency questions together and can be invoked by CI.
- Source: R01: ONT-EVAL-02; initial acceptance suite. P02: proportionate testing and verification.
- Acceptance: The local automated run executes both groups, fails if either fails, and reports exact input versions and results.
- Acceptance: Negative cases cover duplicate IDs, dangling targets, label ambiguity, missing approved metadata/provenance, invalid relation types/cardinality, acyclic-relation violations, unsafe source paths, and remote JSON-LD contexts.
- Acceptance: CI invocation is documented and connected to any applicable existing pipeline; hosted CI provisioning or remote publication is not required to run these checks locally.
- Depends on: REQ-050, REQ-024, REQ-005

### REQ-052 - Verify actual agent-facing retrieval

- Requirement: Accept the first release using actual calls through the installed ontology and knowledge-routing interfaces, in addition to structural tests.
- Source: R01: ONT-EVAL-03; first-release acceptance scenarios.
- Acceptance: An agent resolves Task and TRD with the intended distinctions, finds the memory capability for a relevant lexical query, traverses Task relationships, and receives a meaningful bounded path or explicit no-path result.
- Acceptance: Deprecated lookup identifies its replacement where present; a current-governance query reads governing sources; a mixed prior-failure query returns real memory evidence or accurately reports none.
- Acceptance: Recorded outputs identify the project, source versions, query route, and result evidence; a valid schema alone is not sufficient acceptance.
- Depends on: REQ-051, REQ-038

### REQ-053 - Verify Template and initializer behavior

- Requirement: Verify the release through the actual Template update and initializer helpers using isolated representative project destinations.
- Source: R01: new-project initialization and existing-project adoption acceptance scenarios. P07: current setup/adoption interfaces.
- Acceptance: Create and first preparation yield neutral but specialized ontology capability; an older completed receipt acquires ontology only through the selected adoption route.
- Acceptance: Customized content, prior setup editions, memory preferences, licensing, and project-local data survive reruns and adoption.
- Acceptance: Root queries remain isolated from the representative child projects, and reusable changes do not propagate into them automatically.
- Depends on: REQ-047, REQ-051, REQ-003

### REQ-054 - Verify memory and Task integration boundaries

- Requirement: Verify sidecar linking, mixed retrieval, and frozen ontology input behavior through the current memory and Task integration interfaces without weakening their existing authority or consistency gates.
- Source: R01: memory publication, ontology publication, memory-v1 record, mixed-query, solver-dispatch, and post-dispatch-change acceptance scenarios. P06: existing frozen-input workflow.
- Acceptance: Before/after digests show that ontology publication/linking preserves canonical memory and memory publication preserves canonical ontology.
- Acceptance: A representative Task input/assignment flow registers and delivers the same packet digest to the independent solver contexts; a subsequent ontology change cannot enter those frozen contexts silently.
- Acceptance: Read operations leave canonical and generated state unchanged; unauthorized publication is rejected even when ontology validation succeeds.
- Acceptance: Evidence distinguishes deterministic tests from directly observed agent/Task integration and does not claim unexercised runtime behavior.
- Depends on: REQ-052, REQ-041, REQ-036

## Decisions

- D01: U02 selects the report's first five delivery areas as one first-release baseline. The optional standards backend, execution guardrails, advanced research, and visual editing remain later work. Retaining an ActionType concept or fact classification does not enable those later systems.
- D02: The report's compact JSON-LD proposal is used as the canonical representation for this baseline, within a documented local profile. This is a source-derived design basis submitted for review, not a claim that the user separately mandated every serialization detail. Basic parsing remains standard-library compatible; standards-grade conversion and validation are deferred.
- D03: Stable identifiers, locked imports, typed relationships, evidence, query behavior, and authority are requirements. Exact namespace spelling beyond absolute/stable/project-separated identity, record partitioning, internal Python module layout, ranking tie-break implementation, command argument design, traversal defaults, and concrete publication/recovery storage layout belong to later implementation planning within those constraints. They are not unresolved user-intent decisions.
- D04: The report uses both ONTOLOGY/ and .sys4ai/ontology/ in its layout. The approved-baseline proposal keeps canonical entities/bindings under ONTOLOGY/, configuration in ontology.yaml, the generated Markdown exception under ONTOLOGY/WIKI/, and other derived state under .sys4ai/ontology/. Durable approval/transaction receipts must be classified separately from rebuildable outputs; the memory recovery contract supplies that preservation constraint.
- D05: Source-derived Should recommendations that directly support the selected scope are included where stated: explanatory vocabulary, required cardinality/qualifiers, bounded traversal, wiki indexes, capability queries, memory expansion and source-type separation, and Task reassessment. This does not pull the explicitly deferred optional backends or execution systems into the release.
- D06: Ontology meanings do not replace current operational sources. The report's question about what Verification validates is normalized to the actual SOUL.md distinction: verification checks conformance; validation checks fitness for the intended use. Competency checks must preserve both meanings.
- D07: Source snapshots describe the current inputs for this TRD. A later authorized implementation must inspect then-current governance and integrations before changing them. This is a source freshness obligation, not a request for a downstream agent to choose the present release scope.
- D08: Root setup and Template support are selected in U02. Existing-product deployment is excluded; its explicitly selected adoption capability is included. Initializer edition numbering and exact module-adoption CLI syntax remain implementation choices, while preservation of previous editions, selected identity, exact receipts, and project-owned state is required.
- D09: CI means repeatable automated structural and competency checks with a documented CI entry point and wiring to any existing applicable pipeline. No new hosted service or remote publication is implied. Local execution of that entry point and observed agent-facing integration are required; live external infrastructure is outside this release's acceptance boundary.
- D10: The 54 REQ blocks and exclusions account for all 85 R01 recommendation rows. ONT-AGENT-05 is split deliberately: its no-authorization rule is included, while enabled pre-execution validation is deferred. ONT-SEC-04 is satisfied for this scope by not exposing SPARQL; a future backend must retain its security requirement.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
