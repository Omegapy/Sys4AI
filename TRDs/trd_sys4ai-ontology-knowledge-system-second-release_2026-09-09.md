---
schema_version: 2
trd_id: "TRD-20260909-5308DAE7"
title: "Sys4AI Ontology Knowledge System second release"
slug: "sys4ai-ontology-knowledge-system-second-release"
created_at: "2026-09-09T10:45:42-06:00"
updated_at: "2026-09-09T11:26:46-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the exact saved revision 1 and its SHA256 digest as the completed second-release requirements document."
---

# Task Requirement Document: Sys4AI Ontology Knowledge System second release

## Destination

Provide the second release of the Sys4AI Ontology Knowledge System: formal inference, AI-assisted ontology proposals, RDF/SPARQL interoperability, execution guardrails, and a usable visual ontology workbench. Extend the approved first-release foundation while retaining project-local ownership, source provenance, current operational authority, and separate memory/Task state.

## Captured user intent

- U01: The user explicitly invoked to-trd for a Sys4AI Ontology Knowledge System second release based on the first-release TRD and the shared recommendations file.
- U02: The preceding discussion identifies advanced reasoning, RDF/SPARQL, execution guardrails, and visual editing as the capabilities for this second release. The user requested a separate second-release requirements document following the first-release scope discussion.
- U03: After clarification of advanced reasoning, the user explicitly instructed: include both in the second-release TRD. Both means formal inference over approved ontology rules and AI-assisted proposals for new or revised ontology concepts, with supporting evidence and the existing publication approval process.
- All four capability areas are included deliverables. Optional backend installation or enablement is a project configuration choice; it does not make delivery of a named capability optional.
- This operation captures requirements only. The user's scope decision does not approve an unseen TRD revision or authorize planning, implementation, delegation, installation, migration, Git, publication, deployment, or external actions.

## Context and sources

The project root is /Volumes/P-SSD/AngryOwl/Sys4AI. Current inspection on 2026-09-09 found no installed ontology runtime, ONTOLOGY-depo/, ONTOLOGY/, ontology.yaml, or ontology skill. The approved first-release document is therefore a settled requirements source, not evidence that its implementation or integrated behavior already exists.

R01: [Research and Architecture Recommendations for an Ontology System in Sys4AI.md](</Users/alex.omegapy/Downloads/Research and Architecture Recommendations for an Ontology System in Sys4AI.md>). SHA256: `db0e5ac09d1c17fe326e9afbe73340e1ea3ad07da8c092e12a06701cb7cb3918`. Relevant locators are the semantic-web standards discussion; Ontology-grounded retrieval versus GraphRAG; the authoring/visualization reference; Semantic guardrails around tool calls; Optional RDF/SPARQL backend; the ONT-* recommendation table; and the Standards backend, Agent guardrails, and Advanced research delivery stages.

R02: [Sys4AI Ontology Knowledge System first release](../TRDs/trd_sys4ai-ontology-knowledge-system-first-release_2026-09-09.md), TRD-20260909-5D0F500E, schema 2, revision 3, status trd_done, 54 requirements. SHA256: `334f60fc310c7a5589eb3cde7ec1a267ec53210089f0c01262b03662ae9044a2`. Its Out of scope and Decisions identify the deferred capabilities; its requirements supply the foundation and preservation constraints. This capture does not modify R02.

Current governing sources:

| Source | Locator and use |
| --- | --- |
| P01 | [SOUL.md](../SOUL.md), [AGENTS.md](../AGENTS.md), [ROLE.md](../ROLE.md), and [SPECS.md](../SPECS.md): current authority, Python 3.12 core, source/depot ownership, exact approval, preservation, and truthful verification. |
| P02 | [memory.yaml](../memory.yaml), [memory record v1](../reference-assets/MEMORY-depo/schema/record-v1.json), and [publication/recovery contract](../reference-assets/MEMORY-depo/publication-and-recovery.md): independent memory state, fixed schema, corpus exclusions, scoped publication, and durable recovery evidence. |
| P03 | [Memory in an existing Task execution](../.agents/skills/memory/references/task-integration.md): existing artifact/input references, frozen sources, manager ownership, and material-change reassessment. |
| P04 | [Project registry](../depot/projects.json), [Template mappings](../depot/template-update.json), [initializer contract](../.agents/skills/init-new-project/SKILL.md), and [starter inventory](../.agents/skills/init-new-project/assets/baseline-assets.json): root/Template identity, explicit distribution/adoption, neutral configuration, and retained setup editions. |
| P05 | [to-trd skill](../.agents/skills/to-trd/SKILL.md) and [document contract](../.agents/skills/to-trd/references/trd-contract.md): helper-managed document lifecycle and approval of exact content. |

Primary technical references inspected for this capture:

| Source | Reference and bounded use |
| --- | --- |
| W01 | [W3C OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/), especially the OWL 2 RL discussion: reasoning profiles have explicit expressive and conformance boundaries. No particular engine or claim of unrestricted OWL support is inferred. |
| W02 | [W3C SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/), query forms, datasets, and security considerations: read-query result forms and dataset selection. |
| W03 | [W3C SHACL](https://www.w3.org/TR/shacl/), validation reports: graph conformance and validation-result structure. |
| W04 | [RDFLib security considerations](https://rdflib.readthedocs.io/en/latest/security_considerations/): parsers and queries can access indirectly referenced file/network resources, requiring actual access restrictions. |
| W05 | [W3C RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/), sections 4 and 4.1: graph/dataset separation and semantic comparison. |
| W06 | [W3C PROV-O](https://www.w3.org/TR/prov-o/), starting-point classes/properties: entities, activities, agents, and derivation attribution. |
| W07 | [RDFLib loading and saving RDF](https://rdflib.readthedocs.io/en/latest/intro_to_parsing/): supported serialization mechanisms; graph and dataset preservation must be checked for the selected format. |
| W08 | [pySHACL project documentation](https://github.com/RDFLib/pySHACL), errors and inference/rules: validation failure is distinct from a conforming or nonconforming data graph; enabled extensions require explicit handling. |

R01 contains unresolved citation markers for other pages, attachments, and studies. Those are attributed to the supplied report; this capture does not claim to have verified its entire bibliography. Reported research performance percentages are not adopted as Sys4AI acceptance targets. The W references verify selected technical constraints and do not establish user preferences, installation authority, or product completion.

## In scope

- Formal inference over approved, versioned rules, with explainable derived facts, explicit logical outcomes, resource limits, and freshness checks.
- AI-assisted generation and refinement of source-backed ontology proposals, with validation, impact review, rejection/revision, and exact approved publication.
- RDF dataset projection, local JSON-LD/Turtle/RDF/XML interchange, provenance export, read-only SPARQL, SHACL validation, and actual file/network access controls.
- Optional ontology semantic/vector retrieval and a reproducible graph-assisted retrieval/reasoning comparison, preserving exact-match priority and separate memory indexes.
- Semantic action contracts and guards on supported consequential Sys4AI dispatch paths, followed by current authorization, execution, and verification.
- A local browser workbench for exploration, real draft editing, proposal review, inference/query inspection, validation, conflict handling, and governed publication.
- Advanced frozen Task context, unchanged memory boundaries, reusable source delivery, root integration, neutral Template support, and explicit existing-project adoption.
- Real standards, reasoning, AI-generation, action-dispatch, browser, and integrated acceptance, with current versions and actual evidence.

## Out of scope

- Autonomous publication or rewriting of canonical ontology from model suggestions, inferred permissions, or extracted graphs. Reviewed proposal generation and refinement are included.
- Merging memory with ontology, automatically migrating memory or Task schemas, changing memory corpus/capture/backend choices, cross-project recursive ingestion, or automatic product-project adoption.
- Training a new model or self-modifying agent runtime. Proposal generation uses a permitted agent/model runtime; the model/provider and deployment mechanism remain constrained implementation choices.
- Mandatory deployment of a hosted graph database, public website, remote editor, or global host-wide tool interceptor. The included local capabilities and guarded Sys4AI interfaces must still be fully delivered and tested.
- Implementation, implementation-plan creation, Task execution, dependency/model installation, Git activity, service provisioning, migration, publication, or deployment during this requirements-capture operation.

## Task requirements

### REQ-001 - Deliver all second-release capabilities

- Requirement: Deliver advanced reasoning with both formal inference and AI-assisted ontology proposals, RDF/SPARQL interoperability, execution guardrails, and visual editing as required second-release capabilities on the approved first-release foundation.
- Source: U01: second-release to-trd objective. U02: the four deferred capability areas. U03: explicit instruction to include both reasoning modes. R02: Out of scope and D01.
- Acceptance: The release inventory and acceptance evidence contain functioning deliverables for all four areas and both reasoning modes; a roadmap, design, mockup, or disconnected prototype does not replace any required capability.
- Acceptance: Optional installation or activation of a backend means a configurable delivered feature, not permission to omit its implementation or acceptance.
- Depends on: None.

### REQ-002 - Preserve the first-release foundation

- Requirement: Retain the first release's canonical ownership, stable identities, module locks, project isolation, publication authority, deterministic core, and independent memory/Task state while adding versioned extension contracts.
- Source: R02: REQ-001 through REQ-024, REQ-035, REQ-039 through REQ-048. P01: ownership and preservation.
- Acceptance: Existing valid records and core commands remain compatible; added semantic profiles and fields have explicit versions and capabilities, and unsupported older readers fail clearly rather than misinterpret them.
- Acceptance: No automatic memory or Task schema migration, concept-ID recycling, core-ID redefinition, or child-project adoption occurs.
- Acceptance: Acceptance of integration requires evidence that the applicable first-release foundation works; the first TRD's trd_done status alone does not prove implementation.
- Depends on: REQ-001

### REQ-003 - Isolate and explicitly provision optional backends

- Requirement: Package pinned, compatible optional standards, inference, and semantic-retrieval profiles separately from the Python 3.12 standard-library core, with explicit project-local enablement and readiness checks.
- Source: R01: ONT-NFR-01, ONT-NFR-02, ONT-RET-03; Optional RDF/SPARQL backend. R02: REQ-029, REQ-048. P01: SPECS.md.
- Acceptance: Core lookup, validation, and wiki generation operate with all advanced profiles absent or disabled; enabled advanced operations report missing or incompatible dependencies without claiming success.
- Acceptance: Installation, model preparation, service startup, and profile upgrades occur only through separately selected setup operations; a query or document approval performs none of them.
- Acceptance: Profiles report their exact runtime/package/model versions and input compatibility; RDFLib and pySHACL remain the report-derived standards-backend basis, with exact versions selected and tested during planning.
- Depends on: REQ-002

### REQ-004 - Restrict untrusted ontology input

- Requirement: Constrain RDF parsers, reasoners, SHACL processors, imports, and query execution to explicitly permitted project resources and trusted vendored contexts, with unauthorized file and network access blocked.
- Source: R01: ONT-SEC-01 through ONT-SEC-04; Optional RDF/SPARQL backend. R02: REQ-005, REQ-016. W04: indirect resource access in RDFLib.
- Acceptance: Remote JSON-LD contexts, unselected OWL imports, escaping paths, symlinks, external XML resources, and federated query targets cannot cause unauthorized reads or network requests.
- Acceptance: Uploaded ontology content cannot enable executable extensions, plugins, JavaScript, Python code, or custom query functions; supported extensions are explicitly registered project capabilities.
- Acceptance: Tests observe prohibited access attempts being blocked, rather than relying only on a denylist of literal strings or a documentation warning.
- Depends on: REQ-003

### REQ-005 - Provide an RDF dataset projection

- Requirement: Project canonical ontology data into RDF while preserving stable identifiers, literal types/languages, relationships, module identity, and the separation of asserted, derived, inferred, and external facts.
- Source: R01: ONT-GRAPH-05; Canonical versus generated data; Optional RDF/SPARQL backend. R02: REQ-006, REQ-015. W05: graph and dataset distinctions.
- Acceptance: The adapter exposes separately identifiable graph contexts for the included fact classes and records exact canonical inputs, module versions, configuration, and adapter version.
- Acceptance: Materializing or querying the RDF projection does not make it an alternative authoring store or change canonical ontology bytes.
- Acceptance: Only selected, permitted project modules and bindings enter the dataset; a cross-system link does not import another project's graph automatically.
- Depends on: REQ-002, REQ-004

### REQ-006 - Import and export without silent semantic loss

- Requirement: Support selected local JSON-LD, Turtle, and RDF/XML interchange, with explicit preservation of dataset context and provenance when a graph-only format cannot carry the complete dataset.
- Source: R01: Standards backend delivery stage; standards-grade import/export. R02: canonical representation and provenance constraints. W05, W07: RDF graph/dataset formats.
- Acceptance: Export followed by staged re-import preserves the supported identities, typed values, relations, and graph membership; semantic equivalence accounts for serialization order and blank-node renaming.
- Acceptance: A graph-only export identifies its selected graph and supplies a companion context/provenance manifest or explicitly rejects an unsupported lossless export; it never silently flattens distinct fact classes.
- Acceptance: Imported data is validated and staged as an attributed proposal, with namespace conflicts and unsupported constructs reported before any canonical publication.
- Acceptance: Export destinations and overwrite behavior are explicit; imports cannot overwrite canonical content or grant trust merely because their syntax is valid.
- Depends on: REQ-005

### REQ-007 - Expose standards-compatible provenance

- Requirement: Provide PROV-O-compatible provenance for source assertions, import/export activities, inference results, and AI-generated proposals while retaining exact local source locators and hashes.
- Source: R01: ONT-PROV-03 and provenance discussion. R02: REQ-017. W06: entities, activities, agents, and derivation relationships.
- Acceptance: A result can be traced to the exact source entity and the activity that produced it; available producer attribution and derivation links survive export.
- Acceptance: Provenance identifies evidence and production history, not execution permission or approval of a proposal.
- Acceptance: Changed or missing evidence is visible as stale or unavailable rather than represented as verified current provenance.
- Depends on: REQ-005

### REQ-008 - Provide read-only SPARQL queries

- Requirement: Expose SPARQL 1.1 SELECT, ASK, CONSTRUCT, and DESCRIBE over the selected local dataset through an agent/CLI interface and the visual workbench.
- Source: R01: ONT-RET-07; Standards backend stage. U02: RDF/SPARQL. W02: query forms.
- Acceptance: Representative queries return tabular bindings, a Boolean answer, or a result graph as appropriate, with project/dataset identity, versions, and whether asserted or inferred graphs were selected.
- Acceptance: Named-graph selection is explicit; graph-producing queries return results without inserting them into canonical or persistent stores.
- Acceptance: Supported DESCRIBE behavior, result ordering, and nondeterministic expressions are documented; repeatability checks use a defined deterministic query/result profile.
- Depends on: REQ-005, REQ-007

### REQ-009 - Prevent query mutation and uncontrolled expansion

- Requirement: Reject SPARQL updates and unauthorized resource resolution, and enforce configured query time, memory, traversal, result-count, and output-size limits.
- Source: R01: ONT-SEC-04, ONT-RET-06; read-only SPARQL recommendation. R02: REQ-025, REQ-027. W02, W04.
- Acceptance: Update operations and SERVICE federation are rejected; FROM and FROM NAMED can select only already permitted local dataset graphs and cannot trigger retrieval of external resources.
- Acceptance: Malformed, prohibited, cancelled, or resource-limited queries return distinct diagnostics; partial results are not labeled complete.
- Acceptance: Query execution changes no canonical or generated persistent state, and cannot silently install a backend or refresh an index.
- Depends on: REQ-008, REQ-004

### REQ-010 - Validate graph constraints with SHACL

- Requirement: Maintain SHACL shapes for the supported ontology constraints and run standards-grade validation through the optional standards backend, separately from inference and operational authorization.
- Source: R01: ONT-VAL-06; semantic-web standards and pySHACL recommendation. R02: REQ-024. W03, W08: validation reports and failures.
- Acceptance: Shapes cover required definitions/provenance, identity references, relation endpoint types, and configured cardinalities; overlap with core checks yields compatible results.
- Acceptance: Reports distinguish conformance, violations, and inability to complete validation, and identify the affected entity, path, shape, severity, and useful diagnostic.
- Acceptance: Invalid shapes, unsupported features, missing backends, and processing errors cannot become a passing validation or an execution authorization.
- Acceptance: Validation identifies its graph scope and whether inference was applied; inferred triples cannot supply missing approval/provenance or bypass the core authoring checks.
- Depends on: REQ-005, REQ-004

### REQ-011 - Derive facts from approved ontology rules

- Requirement: Provide formal inference over approved, versioned ontology definitions and rules, supporting class/type propagation and declared property semantics including equivalence, inverse, transitive, and symmetric relationships.
- Source: U03: include formal inference. R01: selected OWL semantics and advanced reasoning. R02: typed relations and fact classification. W01: explicit reasoning profiles.
- Acceptance: Approved rules and example facts yield the expected additional types or relationships, including a generated wiki page being recognized as an Artifact through its declared type hierarchy.
- Acceptance: The supported reasoning profile and its limits are explicit; required competency cases determine profile adequacy, and unsupported axioms are reported rather than silently ignored.
- Acceptance: Draft proposals and merely similar labels do not enter the approved reasoning premises; identity equivalence requires an approved semantic assertion.
- Depends on: REQ-010, REQ-007

### REQ-012 - Explain and separate inferred results

- Requirement: Keep inferred facts in an identifiable derived projection and return an inspectable derivation linking each reported conclusion to approved premises, rules, and exact input versions.
- Source: U03: formal inference with sources and rules. R01: ONT-GRAPH-05, ONT-PROV-01/02. R02: REQ-015, REQ-017.
- Acceptance: An agent and a human can distinguish authored assertions, inferred conclusions, and AI suggestions and inspect the premise/rule chain for a selected inferred result.
- Acceptance: Rebuilding or discarding inference results changes no canonical assertion or historical memory; accepting a proposed semantic change still requires publication.
- Acceptance: A reasoning pass never grants Task, role, tool, or publication authority.
- Depends on: REQ-011

### REQ-013 - Report uncertainty and contradiction accurately

- Requirement: Distinguish an entailed conclusion, a contradicted or inconsistent case, an unproven conclusion, and a reasoning failure according to the declared semantics.
- Source: U03: reasoning over approved rules. R01: formal semantics and deterministic guardrails. P01: evidence and uncertainty discipline.
- Acceptance: An absent relationship is not automatically treated as false or as a permission denial/approval unless an explicit applicable constraint defines that interpretation.
- Acceptance: Inconsistent approved premises produce an actionable conflict report; unrelated conclusions are not presented as trustworthy merely because the engine completed.
- Acceptance: Validation and authorization decisions use their own explicit rules rather than treating incomplete inference as proof of compliance.
- Depends on: REQ-011, REQ-012

### REQ-014 - Bound and reproduce reasoning runs

- Requirement: Apply explicit resource limits and version tracking to reasoning, invalidate stale conclusions when their premises change, and make derivation results reproducible for fixed approved inputs and a fixed engine/profile.
- Source: R01: ONT-NFR-03/04; bounded graph reasoning. R02: REQ-006, REQ-017, REQ-040.
- Acceptance: Limit exhaustion, cancellation, unsupported semantics, and stale input return clear non-success states; no incomplete closure is silently labeled complete.
- Acceptance: Identical pinned inputs produce equivalent conclusions and stable normalized evidence; changing a premise invalidates dependent results.
- Acceptance: Live recomputation does not replace the ontology packet already frozen for an active solver round.
- Depends on: REQ-013

### REQ-015 - Generate ontology proposals from permitted evidence

- Requirement: Provide an AI-assisted workflow that uses selected project sources, approved ontology context, and permitted feedback to propose new concepts, definitions, relationships, mappings, or corrections.
- Source: U03: include AI-assisted ontology proposals. R01: Ontology-grounded retrieval versus GraphRAG, including the proposal/refinement recommendation.
- Acceptance: An authorized agent/model run produces a concrete structured proposal from an identified source packet, with supporting references, rationale, affected identities, and explicit uncertainty.
- Acceptance: Instructions embedded in sources remain data; generated content cannot expand read/write scope, invoke actions, or approve itself.
- Acceptance: Generation uses an explicitly permitted runtime and source scope; it does not silently provision a model, request credentials, or send project data to a new service.
- Depends on: REQ-002, REQ-007

### REQ-016 - Keep proposals attributable and reviewable

- Requirement: Give each proposal a durable identity and version, record its source/context hashes and available generator configuration, and track the proposed semantic changes separately from approved ontology content.
- Source: U03: reviewed AI-assisted proposals. R01: ONT-LIFE-05 and normal publication authority. R02: REQ-019 through REQ-021.
- Acceptance: A proposal displays its evidence, semantic diff, generator attribution, current review state, and any superseding revision; unsupported claims are visible.
- Acceptance: Revising or regenerating a proposal preserves its earlier review history and invalidates approvals tied to obsolete content.
- Acceptance: AI generation need not be byte-deterministic; review, validation, and publication bind the exact captured candidate bytes.
- Depends on: REQ-015

### REQ-017 - Validate proposals before publication

- Requirement: Validate proposed records and their impact on the selected ontology using core checks, applicable SHACL shapes, reasoning consistency checks, and competency questions before they are eligible for approval.
- Source: U03: existing approval process for proposals. R01: proposal evaluation against competency questions and tests; ONT-LIFE-05, ONT-VAL-06.
- Acceptance: Candidate checks run without publishing the proposal or contaminating approved retrieval; reports identify regressions, conflicts, unsupported semantics, and source freshness.
- Acceptance: A candidate cannot become eligible merely because an LLM endorses it or because it passes syntax validation.
- Acceptance: Reviewers can inspect the affected definitions, relations, generated wiki/query results, and downstream semantic effects before accepting exact content.
- Depends on: REQ-016, REQ-010, REQ-013

### REQ-018 - Publish only approved exact proposals

- Requirement: Publish a validated proposal only through the existing scoped ontology publication workflow under the current authorized Director or confirmed Task manager, preserving stable IDs and lifecycle history.
- Source: U03: proposals require the existing approval process. R02: REQ-019 through REQ-021. P01: current authority and writer ownership.
- Acceptance: Approval binds the exact current proposal and target hashes; stale evidence, changed targets, missing grants, or conflicting ownership prevent publication.
- Acceptance: Accept, reject, revise, and supersede have distinct recorded outcomes; rejecting or discarding a proposal changes no approved ontology.
- Acceptance: An approved edit becomes canonical only when its actual publication receipt and reopened target bytes establish success; partial failure reports its real committed boundary.
- Depends on: REQ-017

### REQ-019 - Refine proposals using observed feedback

- Requirement: Allow bounded iterative refinement of ontology proposals using validation failures, competency results, and authorized reviewer feedback without autonomous canonical rewriting.
- Source: U03: include AI-assisted improvements. R01: advanced extraction/refinement and feedback discussion. P01: bounded iteration and stopping discipline.
- Acceptance: A revised proposal addresses named findings and retains source/version lineage; unchanged failures or exhausted limits stop with unresolved findings.
- Acceptance: Evaluation shows whether the candidate improves the relevant competency behavior and reports regressions or lack of benefit without requiring a predetermined improvement percentage.
- Acceptance: Training or self-modification of the agent is not required to perform this proposal-refinement workflow.
- Depends on: REQ-018

### REQ-020 - Add optional ontology semantic retrieval

- Requirement: Deliver a configurable semantic/vector fallback over permitted ontology definitions and documentation, isolated from the memory index and subordinate to stable-ID, exact-label, alias, and explicit graph resolution.
- Source: R01: ONT-RET-03; Ontology-grounded retrieval versus GraphRAG. R02: deferred ontology embedding/vector backend and REQ-026, REQ-028.
- Acceptance: With the profile enabled, an otherwise missed paraphrase can return a sourced ontology concept labeled as a semantic match; it does not displace an exact identity match.
- Acceptance: Model/index/input versions and stale-index status are visible; absence of the profile preserves first-release lexical and graph retrieval.
- Acceptance: Embedding similarity does not establish semantic equivalence, approve a new concept, or access sources excluded from the selected project or frozen packet.
- Depends on: REQ-003, REQ-002

### REQ-021 - Evaluate graph-assisted reasoning and retrieval

- Requirement: Provide a reproducible comparison of advanced semantic/graph-assisted retrieval and proposal reasoning against the first-release retrieval baseline using project competency cases and known evidence.
- Source: R01: GraphRAG distinction, ontology-grounded retrieval research, and Advanced research stage. R02: REQ-050 through REQ-052.
- Acceptance: The comparison records the dataset, ontology/configuration/model versions, expected facts and sources, retrieval correctness, attribution, resource use, and observed failures.
- Acceptance: An automatically extracted graph remains exploratory or proposed knowledge; it is not promoted to normative project vocabulary by the evaluation.
- Acceptance: The report's published study percentages are not treated as guaranteed Sys4AI outcomes; useful negative or neutral results remain valid evidence.
- Depends on: REQ-019, REQ-020

### REQ-022 - Define semantic contracts for governed actions

- Requirement: Model consequential Sys4AI action types with stable identities, target and input types, valid semantic state transitions, required capabilities, governing-source references, and the project dispatch paths where guards apply.
- Source: U02: execution guardrails. R01: ONT-AGENT-04, ONT-AGENT-05; Semantic guardrails around tool calls. R02: capability and role bindings.
- Acceptance: Coverage includes applicable ontology and memory publication, Task lifecycle/ownership operations, TRD/plan lifecycle operations, role/asset changes, and project setup/adoption through their supported project interfaces.
- Acceptance: Every covered operation resolves to a current action contract and dispatch binding; missing, stale, and unsupported bindings are reported explicitly.
- Acceptance: Action contracts describe semantic validity and capability; current user/role/Task authority still determines whether the actor may act.
- Depends on: REQ-002, REQ-007

### REQ-023 - Enforce guards in the execution path

- Requirement: Integrate semantic guard evaluation into the supported project action dispatch paths so enabled guards run after input/schema checks and before current authorization checks, execution, and result verification.
- Source: U02: execution guardrails. R01: prescribed action-loop sequence and ONT-AGENT-05.
- Acceptance: A semantically invalid covered request reaches no underlying mutation helper; a valid request proceeds only after the existing authorization checks succeed.
- Acceptance: Guarding is demonstrated through actual dispatch adapters, not only an independently callable validator that callers may accidentally omit.
- Acceptance: Coverage diagnostics distinguish guarded project paths from direct host/third-party paths outside the integration; the system makes no unsupported claim of intercepting every native tool or shell command.
- Depends on: REQ-022, REQ-010, REQ-013

### REQ-024 - Fail closed when an enabled guard cannot validate

- Requirement: Reject a covered consequential action when its enabled semantic guard finds invalid inputs, ambiguous targets, incompatible states, missing evidence, unsupported rules, stale bindings, or an unavailable/failed validation backend.
- Source: R01: ONT-AGENT-05; deterministic semantic validation before execution. P01: preserve authority, evidence, and truthful failure.
- Acceptance: Each failure returns its action identity, failing condition, relevant source/version, and an actionable diagnostic without invoking the requested side effect.
- Acceptance: A timeout, unknown result, or backend failure cannot be converted to a pass, and retry does not silently disable the guard.
- Acceptance: An explicitly disabled guard profile is reported as disabled; existing authorization checks remain active and no disabled path is advertised as semantically protected.
- Depends on: REQ-023

### REQ-025 - Bind a guard decision to the exact operation

- Requirement: Bind each semantic decision to the exact action, arguments, target state, ontology/rule/source versions, and current authority context, and revalidate or reject when material inputs change before execution.
- Source: R01: source-version evidence and semantic action sequence. R02: REQ-017, REQ-019, REQ-041. P01: exact-version and ownership gates.
- Acceptance: Changing arguments, a target revision, an ontology rule, governing source, manager generation, or approval scope invalidates the old decision.
- Acceptance: Tests exercise a change between preview/check and dispatch; a stale pass cannot authorize the new operation.
- Acceptance: The integration respects existing helper transactions and locks, reports real consistency limits, and does not fabricate a cross-system atomicity guarantee.
- Depends on: REQ-024

### REQ-026 - Record guard outcomes and verify effects

- Requirement: Return linked evidence for semantic checks, operational authorization, actual execution, and post-action verification while preserving their separate meanings.
- Source: R01: semantic guardrail execution stack. R02: REQ-018, REQ-054. P01: observed results and exact receipts.
- Acceptance: A successful record identifies the checked request, decision versions, authoritative authorization outcome, actual helper receipt, and verified target result.
- Acceptance: Semantic success without authorization or execution is reported only as semantic success; errors and partial mutations retain their true status.
- Acceptance: Logs and durable receipts contain bounded operational evidence without credentials, unnecessary personal data, hidden reasoning, or full transcripts.
- Depends on: REQ-025

### REQ-027 - Provide a local ontology workbench

- Requirement: Deliver a browser-usable local visual workbench for selecting one project, searching concepts, exploring bounded typed graphs, inspecting definitions and provenance, and accessing the included advanced capabilities.
- Source: U02: visual editing. R01: Ontology Playground authoring/visualization reference and ONT-WIKI-05.
- Acceptance: A user can find a concept by ID, label, or alias; inspect incoming/outgoing relations; filter by module, type, lifecycle, or fact classification; and navigate to its source evidence.
- Acceptance: Approved assertions, inferred facts, imported material, and AI proposals remain visually distinguishable, with a readable list/inspector alternative to the graph.
- Acceptance: The workbench reports the selected project and current readiness accurately and does not require a hosted website or remote service for basic browsing.
- Depends on: REQ-008, REQ-012, REQ-016

### REQ-028 - Support real visual authoring

- Requirement: Allow users to create and edit draft concepts, definitions, aliases, properties, typed relationships, constraints, and source bindings through forms and graph interactions backed by the canonical ontology contract.
- Source: U02: visual editing. R01: authoring/visualization reference and Advanced research visual-editor stage. R02: canonical ownership and lifecycle rules.
- Acceptance: An author can add a concept and relationship, edit their supported fields, validate the draft, and inspect the resulting semantic diff without hand-editing JSON.
- Acceptance: Imported locked core content is protected; project extensions and distinct replacement identities follow existing rules rather than silently redefining an imported ID.
- Acceptance: Deprecation/replacement preserves historical IDs, while unsupported destructive changes are rejected or routed through their separately authorized lifecycle.
- Depends on: REQ-027, REQ-002

### REQ-029 - Connect visual review to governed publication

- Requirement: Expose draft save, validation, AI proposal review, exact diff/impact preview, rejection/revision, and authorized publication in the workbench through the same guarded project mutation interfaces.
- Source: U02: visual editing and execution guardrails. U03: reviewed AI proposals. R02: REQ-019 through REQ-021.
- Acceptance: A user can inspect an AI proposal's evidence and validation results, revise or reject it, and publish only when the actual current project authority permits the exact operation.
- Acceptance: Draft saving, successful validation, and clicking a review control do not themselves approve or publish canonical semantics.
- Acceptance: After publication, the workbench reopens the canonical result and shows its real status and receipt; it does not declare success from a queued request alone.
- Depends on: REQ-028, REQ-018, REQ-026

### REQ-030 - Preserve edits during conflicts and failures

- Requirement: Detect concurrent edits and stale reviews in the workbench and preserve unpublished user work through validation, publication, or backend failures.
- Source: R02: REQ-019, REQ-047; exact expected versions and preservation. P01: data integrity.
- Acceptance: Two clients editing the same target cannot silently overwrite each other; a stale save or publish reports the conflict and retains the draft for review.
- Acceptance: Cancel, discard, and failed validation leave approved content unchanged; a partial publication shows exactly what committed and what remains unresolved.
- Acceptance: Reloading or reopening a saved draft preserves its identity, content, evidence, and review state.
- Depends on: REQ-029

### REQ-031 - Make workbench actions understandable and accessible

- Requirement: Provide readable labels, keyboard-operable forms and review actions, visible focus, clear errors, and a non-graph route to inspect and edit supported ontology records.
- Source: U02: usable visual editing. R01: human-readable ontology authoring and inspector references. P01: fit for intended use and accessibility.
- Acceptance: A user can complete search, draft editing, validation, diff review, and the permitted publication/rejection flow without relying on graph dragging or color alone.
- Acceptance: Field errors identify what failed and preserve entered content; loading, unavailable profiles, stale results, and partial failures have distinct visible states.
- Acceptance: The main flow explains concepts and review consequences without exposing unnecessary implementation details.
- Depends on: REQ-030

### REQ-032 - Protect local editor and query endpoints

- Requirement: Keep the workbench project-scoped and local by default, validate the actual current actor and operation scope for mutations, and prevent untrusted ontology text or browser requests from bypassing publication controls.
- Source: R01: project-local architecture and ONT-SEC-01/02. R02: publication and source boundaries. P01: privacy, authorization, and data integrity.
- Acceptance: The default listener is restricted to the local machine; remotely exposing it requires a separate selected deployment and access policy.
- Acceptance: Forged actor fields, stale review tokens, unauthorized browser origins/requests, escaping file paths, and executable content in labels/imports do not cause unauthorized reads, writes, or script execution.
- Acceptance: Browser controls use the same guarded publication/validation interfaces as other supported clients and retain their exact target/version checks.
- Depends on: REQ-029, REQ-004, REQ-025

### REQ-033 - Freeze advanced ontology context

- Requirement: Extend ontology packet content to include selected asserted and inferred facts, derivations, approved rule/shape/profile versions, graph selection, provenance, and semantic-retrieval inputs where used, through existing Task artifact references.
- Source: R02: REQ-039 through REQ-041. R01: ONT-TASK-01/02/04. P03: existing frozen-input contract.
- Acceptance: The current manager freezes exact packet bytes before dispatch and supplies identical references to every independent initial solver, including queued solvers.
- Acceptance: Further queries cannot add live facts, new AI proposals, new embeddings/documents, changed rules, or sibling/current-execution candidate material outside the permitted frozen inputs.
- Acceptance: The packet uses existing path/SHA256 interfaces and size limits; selection/truncation is explicit and no new Task schema field or ownership route is introduced.
- Depends on: REQ-014, REQ-020, REQ-002

### REQ-034 - Reassess material advanced-context changes

- Requirement: Apply the existing manager-controlled reassessment and revised-input workflow when ontology rules, inferred conclusions, accepted proposals, or source evidence materially affect active work or a pending action.
- Source: R02: REQ-040/041. P03: versioned inputs, reconciliation, and review invalidation.
- Acceptance: A newly published concept or rule does not silently enter active solver context; the manager assesses its effect and repeats the existing affected input/review/acceptance gates when material.
- Acceptance: Execution guards check current approved action context and reject an action based on stale inputs without rewriting the solver's frozen packet.
- Acceptance: Ontology integration neither replaces the current Task manager nor changes required team composition, role authority, or lifecycle status.
- Depends on: REQ-033, REQ-025

### REQ-035 - Preserve memory history and retrieval scope

- Requirement: Keep advanced ontology reasoning, proposals, indexes, and visual editing separate from canonical memory, preserving memory v1, current corpus exclusions, backend/capture preferences, and frozen-memory rules.
- Source: R02: REQ-035 through REQ-038. R01: ONT-MEM-01 through ONT-MEM-06. P02, P03.
- Acceptance: Ontology inference, proposal publication, visual editing, and RDF import/export do not rewrite existing memory records or add unsupported fields.
- Acceptance: Advanced mixed queries retain the identities and source types of definitions, inferences, proposals, and historical evidence and cannot upgrade memory into operational authority.
- Acceptance: Memory-side mutations occur only through their own authorized operations; new semantic links remain derived and versioned.
- Depends on: REQ-018, REQ-033

### REQ-036 - Deliver reusable sources and root integration

- Requirement: Maintain the second-release contracts, profiles, rules/shapes, skill/interface code, workbench assets, and tests in the appropriate reusable depot sources, then adopt their exact selected versions into the Sys4AI root.
- Source: U01: Sys4AI second release based on the first-release system. R02: REQ-042/043. P01, P04: source ownership and exact adoption.
- Acceptance: The root installation exposes and verifies all four capability areas against current root bindings, with exact versions and readiness for the selected profiles.
- Acceptance: Reusable assets contain no root project instances, proposal history, credentials, generated indexes, or runtime state.
- Acceptance: Adoption preserves unrelated local files and existing approvals/authority; any needed governance-binding refresh is exact, scoped, and verified rather than inferred from file similarity.
- Depends on: REQ-034, REQ-035, REQ-032

### REQ-037 - Extend neutral setup and selected upgrades

- Requirement: Distribute second-release capability through the existing Template updater and initializer, with neutral advanced profiles and explicit adoption/upgrade for existing projects.
- Source: R02: REQ-042 through REQ-047. P04: Template and prior-edition adoption contracts.
- Acceptance: New/first-prepared projects receive their own identity, locked core/extension versions, and empty project data; backend/model activation and publication authority are destination-local and accurately reported.
- Acceptance: Existing projects and prior receipt editions retain their content, configuration, imports, licenses, memory choices, and provenance until an exact adoption/upgrade is selected.
- Acceptance: Customized or incompatible packages are preserved and diagnosed; upgrades and recovery use current expected versions and the existing receipt model, with no bulk product propagation.
- Depends on: REQ-036

### REQ-038 - Document operational contracts and durable state

- Requirement: Document the supported reasoning/query profiles, proposal and visual workflows, guarded action coverage, source/authority rules, configuration, setup, recovery, and the distinction between durable records and rebuildable products.
- Source: R01: ontology skill/contracts and generated/canonical separation. R02: REQ-006, REQ-049. P01: documentation and evidence discipline.
- Acceptance: A maintainer can enable an authorized profile, run inference/SPARQL/SHACL, generate and review a proposal, visually edit a draft, and understand a rejected action using the delivered instructions.
- Acceptance: Captured drafts/proposals, approvals, and publication/recovery receipts remain durable; rebuilding graphs or indexes cannot delete that accepted work.
- Acceptance: Documentation and health output distinguish implemented, installed, enabled, validated, guarded, and unexercised capabilities, and report limitations without advertising unsupported behavior.
- Depends on: REQ-037

### REQ-039 - Verify standards interoperability and access controls

- Requirement: Exercise the actual selected RDF/SPARQL/SHACL backend with positive and negative cases that prove the supported contract and security boundaries.
- Source: R01: ONT-RET-07, ONT-VAL-06, ONT-SEC-03/04; standards backend stage. W02 through W08: inspected standards/backend constraints.
- Acceptance: Tests cover graph/dataset round trips, typed/language-tagged literals, source/provenance retention, all supported query forms, shape conformance, violations, and validation failure.
- Acceptance: Tests observe rejection of SPARQL updates, SERVICE, remote contexts/imports, external XML resources, escaping paths, untrusted executable extensions, and resource-limit violations.
- Acceptance: Actual results identify dependency/profile/input versions; successful core-only tests or mocked backend outputs cannot prove this requirement.
- Depends on: REQ-009, REQ-010, REQ-006

### REQ-040 - Verify actual formal inference

- Requirement: Run executable competency cases through the real reasoning interface to verify required entailments, explanations, contradiction handling, resource limits, and invalidation.
- Source: U03: formal inference. R01: ONT-EVAL-01 through ONT-EVAL-03. R02: competency and observed-interface acceptance.
- Acceptance: Cases show a correct inferred type and property relationship with inspectable premises/rules, an unproven conclusion that remains unproven, and an inconsistent or unsupported case that does not pass as valid.
- Acceptance: Changing an approved premise invalidates its dependent result; a bounded/cancelled run reports incomplete reasoning accurately.
- Acceptance: Captured outputs prove engine behavior and versioned evidence rather than relying on an LLM's prose explanation of what the engine should do.
- Depends on: REQ-014, REQ-039

### REQ-041 - Verify AI generation and governed acceptance

- Requirement: Demonstrate the actual AI-assisted source-to-proposal workflow, validation/refinement, and accept/reject paths using representative permitted project inputs.
- Source: U03: AI-assisted proposals with evidence and existing approval. R01: extraction/refinement and competency evaluation.
- Acceptance: An actual authorized model/agent run generates a sourced candidate; a supported change can be reviewed and published through the normal gate, while unsupported or conflicting content remains unapproved.
- Acceptance: Evaluation includes changed evidence, stale approval, attempted instruction injection, and a revision responding to a concrete validation finding.
- Acceptance: Prewritten candidates or parser tests alone do not establish proposal-generation capability; missing runtime evidence remains explicitly unverified.
- Depends on: REQ-019, REQ-021

### REQ-042 - Verify guarded dispatch and failure behavior

- Requirement: Exercise every delivered action-family adapter through its actual guarded dispatch path, with representative valid, invalid, unauthorized, stale, ambiguous, and backend-failure cases.
- Source: U02: execution guardrails. R01: ONT-AGENT-04/05 and action-loop sequence. R02: integrated evidence standard.
- Acceptance: The coverage report maps each supported action family and dispatch path to observed tests; negative cases prove that the underlying side effect was not invoked.
- Acceptance: At least one valid authorized action reaches its owning helper and its result is reopened; semantic success without authority is rejected.
- Acceptance: Input changes between preview and execution invalidate the earlier pass, and execution/partial failure receipts retain truthful status.
- Acceptance: Any uncovered host or direct bypass path is disclosed as outside observed coverage rather than described as protected.
- Depends on: REQ-026, REQ-039

### REQ-043 - Verify real browser editing workflows

- Requirement: Validate the delivered local workbench through actual browser interactions with the real project service and canonical publication interfaces.
- Source: U02: visual editing. R01: authoring/visualization reference. R02: actual-interface acceptance.
- Acceptance: A browser session searches and inspects a concept, explores a relation/derivation, edits a draft, observes a validation error, reviews a diff, publishes an authorized change, and reopens its canonical result.
- Acceptance: Separate cases verify rejected/unauthorized publication, concurrent-edit conflict, draft preservation, keyboard operation, and readable non-graph access.
- Acceptance: A static screenshot, mockup, or frontend-only fixture does not establish end-to-end editing or publication.
- Depends on: REQ-031, REQ-032, REQ-042

### REQ-044 - Validate second-release integration and preservation

- Requirement: Verify the combined release in the root and representative isolated project destinations, including enabled/disabled profiles, advanced frozen Task inputs, memory boundaries, Template distribution, and existing-project adoption.
- Source: U01 through U03. R02: REQ-052 through REQ-054. P01 through P04: integrated validation and preservation.
- Acceptance: The combined flow resolves a concept, derives a fact with provenance, uses advanced retrieval where selected, generates and reviews a proposal, and applies an authorized visual change through a semantic guard.
- Acceptance: Representative independent solver assignments receive the same advanced packet digest; post-dispatch ontology changes follow reassessment without silent context replacement.
- Acceptance: Before/after checks prove canonical memory preservation, project isolation, no unintended product adoption, and continued core operation with advanced profiles disabled.
- Acceptance: Release acceptance supplies current evidence for each required capability and interface; unavailable prerequisites or unexercised integration remain incomplete rather than being replaced by a smaller demonstration.
- Depends on: REQ-038, REQ-040, REQ-041, REQ-043, REQ-037, REQ-035

## Decisions

- D01: U03 settles the only reasoning-scope distinction raised during this capture: both formal inference and AI-assisted ontology proposals are included. RDF/SPARQL, execution guardrails, and visual editing remain required second-release outcomes. No named capability has been replaced by documentation-only work.
- D02: R02 remains the approved first-release source with its original scope. This TRD adds later capabilities and their compatibility constraints; it does not retroactively claim that R02 includes them or that the first release has been implemented. Cross-TRD prerequisites are stated through R02 references; Depends on fields below the requirements refer only to IDs in this new document.
- D03: The supported formal reasoning profile and engine are implementation choices constrained by required entailments, accurate unproven/conflict behavior, derivation evidence, and competency tests. A planner may not drop those behaviors to fit a convenient library. Unsupported expressivity must be reported; this TRD does not claim conformance to every OWL language variant.
- D04: RDFLib and pySHACL are the report-derived standards-backend basis. Exact versions, isolated environment layout, resource-limit values, model/provider selection, graph storage implementation, and query/result normalization belong to implementation planning within the stated compatibility, privacy, and access constraints. No new service or credential is selected by this document.
- D05: Graph-only formats cannot be assumed to preserve all dataset context. The required interoperability boundary is semantic preservation through a supported dataset representation, selected-graph export with adequate manifest/provenance, or explicit rejection of unsupported lossless conversion. Canonical ontology remains the authoring source.
- D06: Formal inference runs on approved premises and produces derived facts. AI output is a candidate requiring validation and approval. Generation may vary between runs; exact captured proposal bytes, source/model context, subsequent validation, and publication remain attributable and reviewable. Deterministic projection/reasoning checks apply to fixed pinned inputs, not an unrecorded stochastic generation.
- D07: Execution guardrails apply to the supported governed Sys4AI operation families and their actual dispatch adapters. They are enforced when enabled and cannot turn semantic validity into operational authority. Direct host/third-party paths outside those adapters require truthful coverage reporting; adding a universal host interception system is not implied by the local report.
- D08: Visual editing means functional draft authoring and governed publication through a local browser workbench. Frontend framework, graph-rendering library, backend transport, exact screen layout, and trusted-session implementation remain planning choices. A viewer or mockup alone does not satisfy the editing requirement.
- D09: Optional means separately installed/enabled at the project level. Each advanced feature must be delivered and verified in its enabled configuration, while its absence/disabled state preserves the core. Template starters remain neutral; existing projects retain their choices until selected adoption.
- D10: The first-release deferrals map into this document as follows: ONT-PROV-03 to REQ-007; ONT-VAL-06 to REQ-010; ONT-RET-03 to REQ-020; ONT-RET-07 to REQ-008/009; ONT-WIKI-05 to REQ-027 through REQ-032; ONT-AGENT-04 and ONT-AGENT-05 to REQ-022 through REQ-026; ONT-SEC-04 to REQ-004/009; and ONT-NFR-02 to REQ-003. Formal inference and AI-assisted extraction/refinement are captured in REQ-011 through REQ-019, with their observed acceptance in REQ-040/041.
- D11: Missing implementation details, backend provisioning, or a finished first-release runtime do not prevent completing this requirements baseline. They do prevent an unsupported claim that second-release implementation or acceptance has already occurred. Implementation begins only under its separate activation and authority, with current prerequisites reinspected.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
