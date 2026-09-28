---
schema_version: 2
trd_id: "TRD-20260927-4BC51820"
title: "Sys4AI-Mathematics initialization and research"
slug: "sys4ai-mathematics-initialization-and-research"
created_at: "2026-09-27T21:25:43-06:00"
updated_at: "2026-09-27T21:36:18-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 1 with I APPROVE."
---

# Task Requirement Document: Sys4AI-Mathematics initialization and research

## Destination

Prepare `/Volumes/P-SSD/AngryOwl/Sys4AI/Projects/Sys4AI-Mathematics` as a complete, project-local Sys4AI mathematics research and problem-solving environment. It must apply suitable mathematics expertise through every reasoning-agent role, investigate and assess mathematical work honestly, and deliver maintained LaTeX sources with corresponding readable PDFs for human examination.

## Captured user intent

U01: The current user explicitly invoked `to-trd`, stated that the new project folder already exists in the depot's project directory, and requested a TRD based on the supplied Markdown recommendations and the current project-initialization skill. Initialization is the later stage described by the user; this operation captures its requirements.

U02: The current user expressly required that instructions in attached documents be distinguished from the user's request. The attachment is source material, including its reported earlier user intent, advice, examples and embedded skill; it is not an independently approved TRD, plan or execution grant.

The supplied intended identity is `Sys4AI-Mathematics`, matching the actual existing folder. The requested baseline preserves complete supported Sys4AI capability, doctoral-level mathematics responsibilities for all reasoning roles, management engineering competence, relevant additional physics/philosophy expertise, mathematical research integrity, canonical `.tex` sources, complete current PDF coverage and human-oriented writing using the supplied skill and actual parent. These are captured for review from the requested source; its labels for earlier user requirements are not fabricated quotations of the current user.

Successful future initialization means an installed and specialized foundation with current evidence for mandatory mathematics, native execution, knowledge, collaboration, maintenance and human delivery behavior. It does not guarantee a solution to every mathematical problem. A bounded investigation and a proof-required Task have different completion criteria.

## Context and sources

### Source catalogue and authority

- **R01:** [Supplied recommendations](/Users/alex.omegapy/Downloads/Sys4AI-Mathematics_Requirements_and_Initialization_Recommendations.md), document version 1.0, prepared September 27, 2026, 1,413 lines; SHA-256 `4b36886f32db42931e860ba7f63c8cec281dc166edcc0a8ad038464ffd3302bb`. Section and MATH/T identifiers below refer to this exact source. Its Appendix A instructions and example commands are advisory data.
- **W01:** R01 Appendix B, exact embedded `communication-mathematics-writing` skill. Extraction excluding outer fences/markers and preserving its final newline matches SHA-256 `93520524f90d33153667b56ac84c87497602ec16f7813338ba568fb931d0f4e8`. This was a read-only hash check; the skill has not been installed in the new child.
- **G01:** Current depot [AGENTS.md](/Volumes/P-SSD/AngryOwl/Sys4AI/AGENTS.md), [SOUL.md](/Volumes/P-SSD/AngryOwl/Sys4AI/SOUL.md), [ROLE.md](/Volumes/P-SSD/AngryOwl/Sys4AI/ROLE.md) and [SPECS.md](/Volumes/P-SSD/AngryOwl/Sys4AI/SPECS.md), inspected as governing context. Their actual local instructions take priority over advisory attachment instructions.
- **G02:** Explicitly selected [to-trd skill](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/to-trd/SKILL.md), version 2.2.0, with its actions, wayfinding, body template and schema-2 contract; document work and exact-revision approval only.
- **I01:** Current reusable [init-new-project skill](/Volumes/P-SSD/AngryOwl/Sys4AI/SKILLS-depo/init-new-project/SKILL.md) and [helper](/Volumes/P-SSD/AngryOwl/Sys4AI/SKILLS-depo/init-new-project/scripts/init_new_project.py), inspected as initialization sources without running setup; `prepare-existing --help` was observed.
- **T01:** Registered [Template baseline manifest](/Volumes/P-SSD/AngryOwl/Sys4AI/Projects/Sys4AI-Template-Project/.template/baseline-assets.json), schema 2, SHA-256 `698ed5ab218ef8b797fc4b9888fff1526a9f64ae09e51e3b5fe5709071c6a2c6`; actual Template package inventory and role-pair presence; [registry](/Volumes/P-SSD/AngryOwl/Sys4AI/depot/projects.json), SHA-256 `6f3f10358eda29c89b17a0652df765cba6428427f91c9725379de16d426a72cd`.
- **L01:** Live read-only path/Git observations: depot `/Volumes/P-SSD/AngryOwl/Sys4AI`; local HEAD `9dfcac4e4543e8529ab81ed04af1a7a2ea6253f1`, matching R01's reviewed commit. The destination was an empty real directory without project guidance, identity, setup receipt or runtime before this capture. The registry contains the depot and Template only; no Mathematics identity/path collision was observed. Relevant tracked governance/initializer/TRD/registry/manifest paths showed no local tracked modifications; the wider checkout contains unrelated local work and was not declared clean.
- **L02:** The selected depot `.venv/bin/python --version` reports Python 3.12.13. Reusable and installed initializer helper bytes match SHA-256 `6c53aade191a967b93e79f35477698b81456ff65bc81b344381977ff1ad167d8`. Metadata is `13.0.0`, completion prose contains `governance-starter-v11`, the actual implementation sets `governance-starter-v12`, and SPECS contains a v13 Explorer description. These labels are not normalized into an invented receipt.
- **L03:** Read-only source/Template package comparison used the exclusion policy in [tools/template_update.py](/Volumes/P-SSD/AngryOwl/Sys4AI/tools/template_update.py), SHA-256 `d2f4a0ee14075672edec70c546ca4343c2fcf788cdd27defc746900b216aa723`. Every mapped file in all twelve packages matches its Template counterpart. The ontology's 28 additional source files are six generated `explorer/dist` files and 22 `tests/fixtures/explorer` files, both explicitly excluded from starter distribution; this explains the reported raw inventory difference without mixing packages.

R01's `U`, `C`, `D` and `O` labels are retained as its reported direct intent, inherited contract, design elaboration and optionality. Inclusion in this new draft is not a claim of previous approval. Pure design elaborations such as build provenance, the thin domain layer and integrated verification are proposed here for exact-document review because U01 requests a recommendations-derived TRD. Optional technology choices remain conditional. External documentation and historic release claims cited by R01 are not independently verified runtime/toolchain evidence in this capture.

### Inspected foundation inventory

The following counts cover policy-selected package files, not runtime tests. Each source/Template comparison was byte-equal after documented exclusions.

| Baseline skill | Mapped files compared | Intended preserved function |
| --- | ---: | --- |
| init-new-project | 38 | Template preparation, identity, factual registration, receipts and recovery. |
| task | 4 | Explicit execution, manager handoff, categories and acceptance. |
| agent-task | 14 | Canonical state, revisions, owner mutations and responses. |
| manage-subagent-roles | 8 | Live paired roles, fit, native capability and supervision. |
| communication | 2 | Human context, writing modes and source integrity. |
| to-trd | 16 | Requirement discovery and managed document lifecycle. |
| to-implementation-plan | 14 | Canonical plans and requirement/work/evidence traceability. |
| memory | 41 | Project-local evidence-backed recall and publication. |
| ontology | 179 | Meanings, source links, advanced interfaces and read-only Explorer. |
| what-did-you-learn | 7 | The single shared learning/memory completion review. |
| curate | 59 | Scoped existing-owner maintenance and session awareness. |
| collaborate | 21 | Governed boards, checkpoints, versioned exchange and independence. |

The Template's observed role pairs are `project-sub-agent`, `task-manager`, `curator-manager`, `documentation-curator`, `improvement-maintenance` and `knowledge-curator`. Presence was inspected; no role selection, dispatch or new role creation occurred. Starter inventory also contains the three licenses, neutral memory/ontology/advanced configuration, Curator/session configuration, protected ownership map, reference assets, inherited implementation guidance, updater helper and empty Task navigation. These are future adoption inputs, not claims that they exist in the child.

### Traceability and current evidence boundary

`MATH-001` through `MATH-042` map directly to `REQ-001` through `REQ-042`; individual source fields locate their elaborating sections. REQ-043 adds the live-source/adoption preflight and REQ-044 adds post-specialization authority reassessment from current contracts and R01 §11.4. R01 T01–T43 remain future verification scenarios, with overlap reusable and T40 conditional.

This capture performs requirements synthesis, source comparison, provenance checks and managed-document validation only. No initialization, project registration, dependency installation, document compilation, mathematical proof check, native research team, knowledge publication, Explorer launch, Git mutation or external release is claimed. The governing startup awareness checks do not activate a Mathematics Task or provide mathematics runtime evidence.

## In scope

- Supported preparation of the exact existing Mathematics folder, complete static foundation adoption and preservation of this TRD, source materials, local customizations and independent projects.
- Mathematics responsibilities for all reasoning roles, engineering responsibilities for management, appropriate additional expertise and the unchanged native category/settings/context/ownership contracts.
- Exact problem intake, genuine research, review, counterexamples, reproducible computation, claim/dependency records, change impact and honest stopping/continuation.
- The exact supplied writing extension and parent, appropriate manuscript profiles, canonical LaTeX sources, comprehensive current PDF delivery, provenance, layout review and authorized build confinement.
- Project-local memory, ontology and read-only Explorer; governed collaboration; the existing learning checkpoint and bounded Curator/session behavior; current post-specialization permissions.
- Integrated mandatory verification, varied bounded pilots, recoverable failures, usable documentation and truthful reporting of evidence/limitations.

The requirements define the future initialization outcome. They are not an implementation plan, an executable command sequence or authorization to execute that outcome during this capture.

## Out of scope

- Initializing or registering the child, launching execution/agents, installing dependencies or producing an implementation plan during this `to-trd` operation.
- Altering the depot's generic source collections, generic Template or other products; bulk propagation; copying private project history, credentials, runtime environments or another project's learned records.
- Git initialization/branches/commits/pushes/remotes, public repositories, websites, journal submission, external messages, purchases or external publication without their separately selected authority.
- Unrequested services, hooks, unattended AI/scheduling, automatic board wakeups, or universal activation of advanced ontology, semantic/backend, CAS/numerical or formal-checking runtimes.
- A replacement agent framework, competing Task/result scheduler, retired authoring workbench, guaranteed discovery, universal correctness certification, earned-degree claims, fixed manuscript/venue conventions or unverified accessibility/compliance labels.

Optional future runtime selections are not missing mandatory baseline requirements. Native, PDF, role, knowledge and collaboration integration needed for the stated outcome remain mandatory and cannot be deferred by calling them optional.

## Task requirements

### REQ-001 - Establish the Mathematics project identity
- Requirement: Initialize the existing selected folder as Sys4AI-Mathematics, a project for mathematical research and problem solving, with a consistent project-local identity and purpose.
- Source: U01; R01 §1.1 and MATH-001; I01 identity and destination contracts.
- Acceptance: project.json, README.md, SPECS.md, adopted configuration and the factual depot registry identify Sys4AI-Mathematics at Projects/Sys4AI-Mathematics; the derived ID sys4ai-mathematics remains collision-free at execution time.
- Acceptance: The purpose identifies human users who supply mathematical problems and inspect the resulting arguments and documents.
- Depends on: REQ-003

### REQ-002 - Account for the complete Sys4AI foundation
- Requirement: Adopt and account for all supported reusable Sys4AI capabilities and their required assets, dependencies, defaults and verification boundaries.
- Source: U01 requests a TRD based on the supplied recommendations; R01 MATH-002 and §§2.3–2.4; I01; T01.
- Acceptance: An inventory maps source to registered Template to child for all twelve baseline skill packages, governance, role pairs/navigation, local reference contracts, licenses, setup/recovery records, advanced ontology interfaces, the read-only Knowledge Explorer and applicable checks.
- Acceptance: Each capability has an explicit adopted, preserved, blocked or intentionally inactive runtime disposition; mandatory capability loss is reported as incomplete rather than hidden under an optional label.
- Acceptance: No depot history, credentials, caches, environments, learned records, retired systems or unrelated project content are imported as starter assets.
- Depends on: REQ-001

### REQ-003 - Use the supported Template preparation route
- Requirement: Prepare the selected child through the current reusable init-new-project helper and the registered Sys4AI Template, preserving depot, Template and product ownership.
- Source: U01 identifies an already-created folder; G01; I01; R01 MATH-003 and §§2.2, 13.
- Acceptance: Because this folder contains this managed TRD before setup, the selected route is prepare-existing; the existing TRD and its index remain intact.
- Acceptance: The helper uses the supported depot interpreter, explicit destination, project ID, name and purpose, and produces its actual control_records/project-setup.json receipt with asset, registration and verification outcomes.
- Acceptance: No arbitrary root copy, fabricated receipt edition, direct Template edit or incidental Git/remote/site creation substitutes for supported preparation.
- Depends on: REQ-043

### REQ-004 - Apply mathematics responsibilities to every reasoning role
- Requirement: Every eligible reasoning-agent role operates under doctoral-level mathematics responsibilities appropriate to its assignment.
- Source: R01 MATH-004 and §§1.3, 5.1; U01 requests the recommendations-derived baseline.
- Acceptance: Every eligible paired role, including general workers, managers, editors, implementers and Curator/maintenance roles, references and applies the common mathematics contract with role-specific duties.
- Acceptance: Assignments require explicit role/contract reads and assess definitions, assumptions, logical scope, counterexamples, supported deductions and human explanation appropriate to the work.
- Acceptance: AI role descriptions make no claim of earned academic credentials; deterministic compilers, indexes and validators are not assigned academic personas.
- Depends on: REQ-007

### REQ-005 - Provide relevant additional expertise
- Requirement: Make physics, philosophy of mathematics/science and other task-relevant expertise selectable in addition to the common mathematics baseline, including a combined mathematics/physics/philosophy profile.
- Source: R01 MATH-005 and §§5.2, 16.2; U01.
- Acceptance: A cross-disciplinary fixture selects the relevant combined or complementary expertise with a documented task-fit reason; a pure-mathematics fixture does not automatically launch unrelated specialists.
- Acceptance: Additional profiles specify responsibilities, required tools and limits; physics interpretation and philosophical reasoning do not replace mathematical proof.
- Acceptance: Profiles are reused or created only for actual enduring role gaps through the supported role workflow; the advisory catalogue does not become a permanently running team.
- Depends on: REQ-004, REQ-007

### REQ-006 - Specialize Director and Manager engineering responsibilities
- Requirement: The project-local Project Director and Task Manager combine mathematics responsibilities with systems engineering and appropriate software engineering.
- Source: R01 MATH-006 and §4.2; G01 ROLE.md; U01.
- Acceptance: Their contracts cover system ownership, interfaces, dependencies, reproducibility, tooling, integration and mathematical assessment.
- Acceptance: The host Director and activated native manager retain their separate identities and authority; no competing executive role or second canonical Task writer is introduced.
- Depends on: REQ-004

### REQ-007 - Preserve valid paired roles and real capability checks
- Requirement: Use the live filesystem-backed Roles/ catalogue and verify role fit, required skills, actual tools and permissions before assignment.
- Source: R01 MATH-007 and §5; G01 mandatory manage-subagent-roles workflow; T01.
- Acceptance: Every role-based selection, creation or assignment uses a fresh supported catalogue and reads both AGENTS.md and ROLE.md for the selected pair; generated navigation is not authority.
- Acceptance: Invalid or incomplete pairs are ineligible; missing tools, unsupported configuration or absent authority produce a named blocker rather than an invented role, identity or receipt.
- Acceptance: Both baseline pairs and all adopted Curator pairs remain accounted for; legacy provenance and protected project-owned roles are preserved.
- Depends on: REQ-001

### REQ-008 - Preserve native manager ownership and effective settings
- Requirement: Research execution uses real native manager handoff, exclusive canonical Task writing and the Director/manager's exact effective model and reasoning effort.
- Source: R01 MATH-008 and §§5.3, 12.2; G01 Task and delegation contracts.
- Acceptance: Reservation, actual native launch receipt and confirmed activation establish the manager before ownership transfers; the manager is distinct from the host and required logical children.
- Acceptance: Current actor, generation and revision checks protect Task mutation; the host relays steering after activation instead of competing for writes.
- Acceptance: Observed native capability, depth, capacity, topology, settings inheritance and context guarantees are recorded; unsupported inheritance blocks dispatch, and fabricated fixture IDs or shell-launched substitutes are not reported as native evidence.
- Depends on: REQ-006, REQ-007

### REQ-009 - Retain the category-specific team and review gates
- Requirement: Preserve the installed generic, complex and extra-complex orchestration contracts when organizing mathematical work.
- Source: R01 MATH-009 and §§5.4, 6.3–6.7; G01 ROLE.md category contracts.
- Acceptance: Generic work has one worker; complex work has at least two independent solvers and one distinct senior; extra-complex work also has one distinct reviewer per solver and every current required pass before synthesis.
- Acceptance: The required logical team is frozen and queued within observed capacity without removing members or adding unofficial category stages.
- Acceptance: Accepted complex/extra-complex changes use one distinct dedicated implementation child; generic implementation remains with its original worker. Exact candidates, baseline versions, review mappings, conflict rounds and manager acceptance remain attributable.
- Depends on: REQ-008

### REQ-010 - Preserve the exact mathematical problem and success boundary
- Requirement: Accept varied mathematical problems while preserving the original question, domain, assumptions, quantifiers, constraints, intended audience and requested outcome.
- Source: R01 MATH-010 and §6.1; U01.
- Acceptance: The versioned research baseline retains the original and interpreted formulations and defines whether success is proof, disproof, construction, exact value, approximation with stated error, algorithm, classification, explanation or bounded investigation.
- Acceptance: Consequential ambiguities are resolved from supplied facts or actual user answers; no easier claim or narrower outcome silently replaces the request.
- Acceptance: Modeling records distinguish the physical situation, mathematical model and question about that model; computational records distinguish exact, symbolic, approximate and empirical outcomes.
- Depends on: REQ-001

### REQ-011 - Expose the actual status of each mathematical claim
- Requirement: Distinguish supplied claims, conjectures, heuristics, proof sketches, incomplete arguments, complete candidate arguments, conditional results, numerical observations, counterexamples and checked results.
- Source: R01 MATH-011 and §7.1; W01 mathematical meaning and review boundaries.
- Acceptance: Material claims have evidence-supported status with separate source origin, argument, mathematical review, formal, editorial, build/layout, Task and distribution dimensions.
- Acceptance: An incomplete or conditional claim is visibly labeled near the affected statement in its human-readable PDF; a theorem environment or edited metadata cannot promote it to proved status.
- Acceptance: A counterexample verifies the exact assertion's hypotheses and failure of its conclusion; a bounded unsuccessful search does not imply nonexistence.
- Depends on: REQ-010

### REQ-012 - Review mathematics independently of administrative and presentation success
- Requirement: Assess mathematical arguments and dependencies independently of editorial quality, agent agreement, compilation, ontology validation and Task administration.
- Source: R01 MATH-012 and §§6.4–6.6; W01 proof writing.
- Acceptance: Review findings identify exact checked statements, assumptions, dependencies, scope and defects, including unsupported implications or missing hypotheses.
- Acceptance: Mandatory defects return to the producer and the required current review; optional prose improvements stop once criteria pass.
- Acceptance: Neither votes, fluent prose, a passing build, a graph type nor a Task approval establishes mathematical validity; unresolved objections retain attributable dispositions and remain blocking when the acceptance contract requires their resolution.
- Depends on: REQ-011, REQ-013

### REQ-013 - Preserve supported sources and evidence
- Requirement: Keep precise source attribution and check the applicability of cited mathematical results, while retaining reproducible evidence for claims actually made.
- Source: R01 MATH-013 and §§6.4, 9.5; W01 citations and source integrity.
- Acceptance: Each external dependency identifies its source/version/locator and relevant assumptions, or an explicit access or verification limit; citations and execution observations are not invented.
- Acceptance: Bibliography entries alone do not certify support. Fabricated locators, inaccessible references and a real reference attached to an unsupported claim are flagged.
- Acceptance: Authorship, novelty/priority, acknowledgments, funding, contributions, declarations and publication acceptance are stated only from actual supplied or verified facts.
- Depends on: REQ-010

### REQ-014 - Keep mathematical research in editable LaTeX sources
- Requirement: Maintain canonical mathematical research exposition and arguments in UTF-8 LaTeX .tex sources with their required non-secret dependencies.
- Source: R01 MATH-014 and §§8.1, 11.1; W01 LaTeX mechanics.
- Acceptance: Problem formulations, candidate notes, proofs, mathematical review notes, partial results, counterexamples and manuscripts use declared .tex sources with stable labels and semantic environments.
- Acceptance: Native code/data, .bib references and supporting macros/classes remain linked in their appropriate formats; typesetting transforms the declared sources directly without rewriting the argument through another authoring format.
- Acceptance: Accepted assembly preserves the exact originating candidate/version; a build does not mutate a reviewed candidate or create two independently editable canonical statements.
- Depends on: REQ-001

### REQ-015 - Provide complete current PDF coverage
- Requirement: Every retained research document and mathematical artifact submitted for review or handoff has a current corresponding readable PDF, including drafts and incomplete work.
- Source: R01 MATH-015 and §8.2; U01.
- Acceptance: A coverage manifest accounts for standalone notes, draft proofs, review notes and assembled manuscripts; independently retained or handed-off fragments have a suitable wrapper PDF with necessary notation and context.
- Acceptance: Build gates run at saved research checkpoints and candidate/review/final handoffs. A retained version that fails to build is visibly blocked; an older output cannot satisfy its current-source requirement.
- Acceptance: Shared infrastructure, vendor files and generated temporary sources have explicit classifications; substantive research is not relabeled as macros or excluded through broad ignore rules to hide missing PDFs.
- Depends on: REQ-014

### REQ-016 - Bind builds and PDFs to exact inputs
- Requirement: Maintain version-bound artifact and build evidence linking each expected PDF to its complete source/dependency set and declared build environment.
- Source: R01 MATH-016, a proposed design elaboration for this draft; §§8.3–8.4; U01 requests use of the recommendations.
- Acceptance: The manifest records document identity/kind/audience/owner, entrypoint and included fragments, figures/macros/classes/bibliography hashes, expected output, actual PDF hash, toolchain/configuration versions, command arguments, observed exit, diagnostics, time, page count and review references.
- Acceptance: Declared dependencies are reconciled with observed build dependencies; a changed include, macro or bibliography marks affected PDFs stale.
- Acceptance: A failed build retains sources and diagnostics, preserves a previous good PDF as historical/stale and does not publish a partial replacement as current; retries follow diagnosed corrections within the selected budget.
- Depends on: REQ-014

### REQ-017 - Verify readable PDF delivery
- Requirement: Accept PDFs only with suitable mathematical layout, legibility and human-reading evidence in addition to successful compilation.
- Source: R01 MATH-017 and §§8.4–8.5; W01.
- Acceptance: Every page of initialization fixtures and the accepted initialization delivery set is rendered and inspected for readable text, symbols, equations, matrices, alignment, figures, delimiters, theorem identification and page boundaries.
- Acceptance: Undefined labels, unresolved citations, missing glyphs and materially clipped equations fail the delivery gate. Other warnings are judged by their actual effect.
- Acceptance: Later large-document review declares its coverage honestly; sampling is not reported as all-page review. Searchable/selectable text and meaningful metadata are used where supported, without unverified accessibility, PDF/A or tagged-PDF claims.
- Acceptance: A handoff includes the current PDF, exact editable source/dependency bundle and concise build/verification record.
- Depends on: REQ-015, REQ-016

### REQ-018 - Adopt the supplied mathematics-writing skill and its parent
- Requirement: Install the exact supplied communication-mathematics-writing skill as a project-local extension and apply it with the actual shared communication parent.
- Source: R01 MATH-018 and §9.1; W01 verified Appendix B source; I01 package preservation.
- Acceptance: The installed supplied text has SHA-256 93520524f90d33153667b56ac84c87497602ec16f7813338ba568fb931d0f4e8 and retained source provenance; outer appendix fences/markers are excluded and the final newline is preserved.
- Acceptance: Its location and discovery follow the child's actual skill configuration. Relevant assignment packets explicitly require both skills and observed representative outputs demonstrate their application.
- Acceptance: The supplied skill is not silently rewritten, shortened or installed into the generic depot, Template or unrelated projects; absent parent capability is reported explicitly.
- Depends on: REQ-001

### REQ-019 - Explain mathematical work for human readers
- Requirement: Produce academically precise mathematical documents with enough context for the selected human audience to reconstruct the problem, result and argument.
- Source: R01 MATH-019 and §§6.1, 9.3; W01 reader context; U01.
- Acceptance: Each document identifies its audience/prerequisites and supplies appropriate orientation, definitions, stable notation, assumptions, results, justified reasoning and limitations without requiring internal agent history.
- Acceptance: Abstracts and informal explanations match the formal claim's strength. Intuition and examples remain distinct from proof; unexplained formula collections and generic significance claims do not satisfy delivery.
- Acceptance: Necessary technical vocabulary and repetition are preserved; agent-management details appear in the reading output only when they help the reader interpret evidence or reliability.
- Depends on: REQ-014, REQ-018

### REQ-020 - Protect mathematical meaning during editorial work
- Requirement: Writing, editing and formatting preserve protected mathematical semantics and the authorized change boundary.
- Source: R01 MATH-020 and §9.2; W01 task modes and mathematical meaning.
- Acceptance: Comparison before and after edits checks objects, domains, quantifier order, hypotheses, inequalities, scope, regularity, constant dependence, asymptotics, implication direction and conclusions.
- Acceptance: Draft, rewrite, light edit, proofread, fill-only, structural edit and mathematical review retain their distinct permissions; an editorial worker returns a discovered proof gap to its research owner.
- Acceptance: A substantive mathematical repair has its own authorized evidence and affected review; it is not silently classified as copyediting or hidden by a rhetorical transition.
- Depends on: REQ-018

### REQ-021 - Use content-appropriate manuscript profiles
- Requirement: Support suitable pure, applied/modeling, numerical/computational, survey/expository and short-note structures without one compulsory paper template.
- Source: R01 MATH-021 and §9.4; W01 profiles, LaTeX mechanics and venue safeguards.
- Acceptance: Representative short and computational documents use structures suited to their content and preserve existing manuscript conventions within authorized changes.
- Acceptance: No universal IMRaD structure, document class, abstract length, conclusion, citation style, classification code or AI disclosure is imposed.
- Acceptance: When venue preparation is separately selected, current venue requirements and actual author/AI use are verified; unavailable rules and unsupported declarations remain explicit, and preparation does not authorize submission.
- Depends on: REQ-018

### REQ-022 - Maintain stable statements, notation and proof dependencies
- Requirement: Keep compact stable result, notation, dependency, bibliography and related-paper references tied to the authoritative mathematical sources.
- Source: R01 MATH-022 and §§7.2–7.3; W01 multi-paper project mode.
- Acceptance: Material results have stable identifiers, owning document, exact .tex label/source hash, assumption and proof locators, dependencies, source/review references and supersession or retraction; registers link instead of duplicating editable claims.
- Acceptance: Cross-paper checks identify shared notation, contributions, prior results, references and inaccessible dependencies within the authorized scope; related manuscripts have substantive contribution boundaries.
- Acceptance: Missing prerequisites and circular proof support are exposed. Legitimate conceptual ontology cycles are not confused with circular mathematical justification.
- Depends on: REQ-014

### REQ-023 - Use evidence-backed project-local memory
- Requirement: Maintain isolated mathematics project memory through the existing memory owner with exact evidence, provenance, applicability and claim status.
- Source: R01 MATH-023 and §10.2; I01 neutral memory and capture contracts; G01.
- Acceptance: New memory starts empty of depot/other-project learned records. Published research history links exact sources/PDFs, current status, reviewed evidence and conditions of applicability.
- Acceptance: Ordinary children propose records; current authorized owners publish through supported grants and recovery. Unreviewed or rejected proofs cannot become established shared recall.
- Acceptance: Superseded/retracted claims remain distinguishable from current knowledge; failed approaches have precise bounded reasons. Optional backend failure is distinguished from canonical local-record failure.
- Acceptance: The actual automatic-capture choice is reported after setup with the supported opt-out; explicit off preferences and project-local configuration remain preserved.
- Depends on: REQ-002, REQ-044

### REQ-024 - Use a separate mathematics ontology and read-only Explorer
- Requirement: Extend the supported project-local ontology with mathematical meanings and sourced relationships while preserving locked core semantics and its separate owner.
- Source: R01 MATH-024 and §10.3; I01 ontology/advanced capabilities; G01 SPECS.md.
- Acceptance: Scoped definitions and relationships for the research workflow use permitted schema/vocabulary mechanisms and exact source/status references, with current publication grants and protected core imports.
- Acceptance: Queries and the actual selected-project read-only Knowledge Explorer expose relevant definitions, processes, relationships and associated mathematical artifacts without publishing canonical changes.
- Acceptance: Graph membership, inference or validation does not certify a proof; memory, Tasks and mathematical evidence remain separate.
- Acceptance: Advanced RDF/SPARQL, SHACL, finite inference, semantic and guard interfaces are inventoried. Unselected profiles remain inactive, and the retired authoring workbench is not reintroduced.
- Depends on: REQ-002, REQ-044

### REQ-025 - Use governed version-specific collaboration
- Requirement: Integrate the existing collaboration provider under the manager's registered policy, exact inputs, namespaces and participant grants.
- Source: R01 MATH-025 and §10.4; I01 default collaboration contract; G01.
- Acceptance: Participants observe the four checkpoints before starting/resuming, relying on shared interfaces, revising candidates and final handoff.
- Acceptance: Posts, bounded help, objections and notices identify exact artifacts/versions and retain distinct post, reported-reading and recipient-observed notification receipts.
- Acceptance: All material objections reach the responsible senior/manager with attributable resolved, limited, deferred or blocking dispositions; discussion neither changes Task authority nor publishes knowledge.
- Acceptance: Actual owner input binding precedes wake/resume after a material change; a post or empty send response is not proof that an idle agent resumed or understood the change.
- Depends on: REQ-008

### REQ-026 - Protect independent first passes and frozen inputs
- Requirement: Preserve solver and reviewer independence with identical frozen problem inputs and phase-specific access restrictions.
- Source: R01 MATH-026 and §§6.2–6.3, 10.4; G01 independent-context contract.
- Acceptance: Initial solvers receive the same complete versioned problem/criteria and approved memory/ontology packet, appropriate distinct perspectives and separate candidate namespaces.
- Acceptance: Sibling drafts cannot enter initial context through shared files, boards, memory, live retrieval or queued full-history forks; first reviewer assessments retain their required seals.
- Acceptance: Context-isolation evidence is checked separately from model inheritance and cooperative filesystem checks. If independence cannot be established, dispatch is blocked rather than certified by a prompt to ignore inherited material.
- Depends on: REQ-009, REQ-025

### REQ-027 - Retain scoped learning and Curator maintenance
- Requirement: Preserve the single learning/memory completion checkpoint and bounded Curator session maintenance through the existing owners.
- Source: R01 MATH-027 and §10.5; I01 Curator/session/learning contracts; G01.
- Acceptance: Enabled capture evaluates useful/no-durable-lesson outcomes once; capture-off and current publication restrictions are respected without duplicate learning storage or pipelines.
- Acceptance: Curator checks and relevant maintenance proposals use current scoped owners, preserve original user work and active Task ownership, and keep pending work when runtime or budget is unavailable.
- Acceptance: Lessons and maintenance observations do not authorize unsolicited role/skill/governance changes or proof rewrites; setup/session behavior starts no unrequested unattended AI, service, hook or external notification.
- Depends on: REQ-002, REQ-044

### REQ-028 - Retain native governance and owner formats
- Requirement: Keep Sys4AI's canonical governance, Task, role, memory, ontology, plan, setup and operational formats intact while using LaTeX/PDF for mathematics.
- Source: R01 MATH-028 and §§4.1, 11.1; G01; I01.
- Acceptance: Helper-owned JSON, Markdown, JSON-LD and JSON-compatible YAML contracts, paired roles and generated projections retain their existing owners and schemas.
- Acceptance: Task summaries and board messages are not converted into competing LaTeX state; retained mathematical arguments in operational notes instead link to their research .tex/PDF artifact.
- Acceptance: No domain manifest mutates canonical owner records or treats a generated index as authority.
- Depends on: REQ-003

### REQ-029 - Make computational findings reproducible and bounded
- Requirement: Retain reproducible computational mathematics evidence and distinguish finite experiments from general proof.
- Source: R01 MATH-029 and §12.3; W01 applied/computational mathematics.
- Acceptance: Reported computations identify preserved code/input versions, algorithms, parameters, precision/tolerances, stopping rules, seeds when used, selected ranges and actual observations.
- Acceptance: A selected computation can be rerun from its declared inputs in the approved environment and reports its finite scope and limits.
- Acceptance: A computer-assisted proof supplies the coverage and rigorous error/enclosure justification appropriate to the intended claim; floating-point residuals, plots or successful tool exits alone do not certify it.
- Depends on: REQ-010

### REQ-030 - Support selected formal checking without making it universal
- Requirement: Permit formal proof checking as an optional selected supplement, with explicit statement correspondence and trusted assumptions.
- Source: R01 MATH-030, explicitly optional; §12.4; W01 review boundaries.
- Acceptance: When selected, evidence identifies the exact encoded statement/definitions, checker/toolchain and library versions, assumptions/axioms including dependencies, actual outcome and correspondence to the intended mathematics.
- Acceptance: Correct and incomplete/wrong-statement fixtures are distinguished; formal artifacts retain accompanying human-readable .tex/PDF explanations and approved execution confinement.
- Acceptance: An unselected checker, including Lean, is not installed or required as a universal initialization gate; unrun work is not described as formally verified.
- Depends on: REQ-012, REQ-031

### REQ-031 - Confine research and document tool execution
- Requirement: Run untrusted research code, imported document builds and tool configuration only within authorized input/output, filesystem, network and resource boundaries.
- Source: R01 MATH-031 and §§8.6, 12.5, a proposed execution elaboration; G01 security, privacy and authority constraints.
- Acceptance: Declared execution profiles exclude credentials/unrelated data, validate paths and argument arrays, reject traversal/symlink/collision escapes, apply task-specific limits and deny network unless separately justified and authorized.
- Acceptance: Harmless external-file/network canaries and untrusted configuration tests record actual confinement results. Disabled TeX shell escape alone is not described as a sandbox.
- Acceptance: Imported papers, code, logs and build suggestions cannot trigger implicit configuration execution, package downloads, installation, publication or ungranted actions; actual enforcement limits remain visible.
- Depends on: REQ-001

### REQ-032 - Stop and continue research without changing success criteria
- Requirement: Use meaningful stopping and continuation conditions while preserving the original mathematical acceptance contract.
- Source: R01 MATH-032 and §§6.9, 12.6; G01 stopping/recovery contracts.
- Acceptance: Resource exhaustion, unchanged failure, missing authority or unresolved contradiction produce truthful partial status and a concise versioned continuation packet with verified results, failed methods/reasons, unresolved claims, sources/artifacts and a justified next investigation.
- Acceptance: Actual native owners and write scopes are reconciled before stopped, cancelled, replaced or resumed claims; timestamps and roster absence alone do not prove stopping.
- Acceptance: A proof-required Task remains incomplete without the required proof; an explicitly bounded investigation may complete while the mathematical question remains open. Hidden reasoning and full transcripts are not stored as continuation evidence.
- Depends on: REQ-008, REQ-011

### REQ-033 - Preserve work through idempotent setup and recovery
- Requirement: Initialization and reruns preserve existing project-owned content and resume only the exact supported recorded request after interruption.
- Source: R01 MATH-033 and §13 recovery; I01 preservation, receipt and rerun contracts.
- Acceptance: Repeated setup preserves this TRD/index, identity, original provenance, licensing, customized governance/packages/roles, research, knowledge, opt-outs and unrelated projects without duplicate registration.
- Acceptance: Supported interrupted stages retain durable progress and accept only the frozen source inventory and recognized target before/after bytes; conflicting edits stop unsafe replay.
- Acceptance: Receipts, historical editions and custom packages are not deleted, relabeled, partially merged or fabricated to bypass an error; partial/degraded results retain their exact committed boundary.
- Depends on: REQ-003

### REQ-034 - Report capability evidence at its actual level
- Requirement: Distinguish installed, configured, dependency-available, authorized, statically valid and runtime-tested capability states.
- Source: R01 MATH-034 and §§12.1–12.2, 14.1; I01 static-health semantics.
- Acceptance: The capability report identifies exact input revisions/environment, check procedure, artifacts and passed, failed, blocked, partial or not-exercised outcome for each required component.
- Acceptance: Deterministic fixtures, actual native observations and end-to-end deliveries are labeled separately; static health and installed-but-disabled optional profiles do not imply operating services.
- Acceptance: A mandatory unexercised gate limits completion explicitly. Earlier release statements and a pre-specialization receipt do not certify the new child's current runtime.
- Depends on: REQ-002

### REQ-035 - Keep document, execution, claim and publication lifecycles separate
- Requirement: Maintain the distinct lifecycles and canonical owners of TRDs, plans, Tasks, mathematical claims, knowledge publication, build delivery and external release.
- Source: R01 MATH-035 and §§4.1, 7.1, 15; G01; G02.
- Acceptance: TRD approval completes only the requirements revision; plan readiness, Task completion, claim review, current PDF delivery and distribution each require their own actual criteria and authority.
- Acceptance: Result/build registers reference canonical Tasks without scheduling, assigning or independently changing their state; mathematical review is not conflated with build or editorial status.
- Acceptance: Recovery repairs only the owning system's recorded operation without replaying an unrelated event, promoting a claim or silently opening a new execution.
- Depends on: REQ-003

### REQ-036 - Keep the mathematics layer small and project-local
- Requirement: Implement mathematics-specific research records, policies, writing integration and build/validation functionality as a thin project-local extension of existing supported owners.
- Source: R01 MATH-036, a proposed design elaboration for review; §§4.3, 7.2, 11.2–11.5; U01.
- Acceptance: Domain records have validated identities, path roots, required references, authorized writers and exact update rules without adding unsupported Task/memory/ontology schema fields.
- Acceptance: Existing assignment/candidate/reviewer/senior namespaces remain protected; accepted shared research assembly has explicit ownership and links to exact source evidence.
- Acceptance: No second scheduler, ledger, autonomous messaging service or required vector database is introduced. An optional mathematics-research skill and the illustrative directory tree are not mandatory independent subsystems.
- Depends on: REQ-028

### REQ-037 - Invalidate evidence after material changes
- Requirement: Assess change impact and invalidate affected mathematical reviews, dependencies, knowledge references and PDFs when their material inputs change.
- Source: R01 MATH-037 and §§7.3, 11.4; W01 semantic/cross-paper checks; G01 version gates.
- Acceptance: Changes to claims, assumptions, definitions, proof dependencies, meaningful macros or input context identify affected results, reviews, synthesis/acceptance, manuscript sections, knowledge records and outputs.
- Acceptance: Historical evidence remains attributable but cannot count as a current pass; owner baselines and required rechecks bind the new exact versions.
- Acceptance: Representation-only changes receive proportionate rebuild/layout or semantic checks according to actual impact; neither all style edits nor all whitespace edits are automatically classified as mathematical changes.
- Depends on: REQ-022, REQ-035

### REQ-038 - Verify the integrated Mathematics workflow
- Requirement: Demonstrate the required initialization and research integration with proportionate positive, negative, recovery, native and human-delivery evidence.
- Source: R01 MATH-038, a proposed verification elaboration; §§13–14, including T01–T43; U01.
- Acceptance: A requirement-to-evidence matrix covers every mandatory requirement and all materially distinct risks represented by T01–T43; overlapping checks may share evidence and T40 applies only if formal checking is selected.
- Acceptance: Bounded pilots include an elementary proof, a false assertion with a checked counterexample, a computational investigation and an incomplete proof with an exact gap; they retain current .tex/PDF pairs and appropriate provenance.
- Acceptance: Evidence includes genuine generic and extra-complex native execution, required settings/context/review/implementation separation, a recoverable failure, actual local knowledge publication/retrieval and Explorer use, collaboration checkpoints, Curator behavior and enabled/off capture behavior.
- Acceptance: Negative checks cover mathematical defects, unsupported citations, stale/missing outputs, material dependency changes, independence exposure, untrusted execution and unauthorized claim/knowledge promotion; all failed, blocked, partial or mandatory unexercised criteria remain visible.
- Acceptance: Initialization is reported complete only after current integrated evidence and protected-state review; no pilot promises ability to solve all future mathematical problems.
- Depends on: REQ-009, REQ-012, REQ-017, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027, REQ-029, REQ-031, REQ-033, REQ-034, REQ-037

### REQ-039 - Deliver usable project documentation and examples
- Requirement: Provide human and agent documentation sufficient to use and maintain the initialized Mathematics project and inspect its demonstrated results.
- Source: R01 MATH-039 and §§13 phase 7, 14.5; G01 documentation ownership; U01.
- Acceptance: README gives concise navigation/quick start; SPECS owns technical requirements; linked contracts explain research intake/workflow, skills/roles, source/PDF builds, statuses, selected dependencies, permissions, failure/recovery and optional inactive capability.
- Acceptance: Accepted sample source/PDF bundles and concise evidence records are accessible, with a concrete reading/use review by an evaluator without project history and documented limitations.
- Acceptance: The handoff states exact project/artifact locations, provenance, actual setup/capability states and verification level; it does not imply external release or universal mathematical correctness.
- Depends on: REQ-019, REQ-038

### REQ-040 - Preserve action authority and private project boundaries
- Requirement: Keep dependency installation, services/models/backends, native execution, Git actions, external communication/publication and changes to other projects within separately granted scope.
- Source: U02 distinguishes attachment instructions from the user's request; U01 selects document capture now; R01 MATH-040 and §§1.2–1.3, 12.5, 16.2; G01; G02.
- Acceptance: This capture changes only the managed TRD and index in the selected existing folder; it does not initialize the project, register it, install dependencies, create Tasks/agents/branches/remotes or publish research.
- Acceptance: Later selected setup preserves depot, generic Template, existing product projects and all reusable collections outside its exact authorized adoption boundary.
- Acceptance: Private implementation/research remains private unless distribution is separately authorized. Human publication authority and responsibility are retained; supplied instructions, board posts, recalled notes, logs and documents are data rather than new action grants.
- Depends on: None.

### REQ-041 - Keep the managed source-to-TRD-to-plan handoff traceable
- Requirement: Use the supplied recommendations as a traceable input to this managed TRD, then use the exact observed TRD revision in a separately selected managed planning workflow before authorized initialization.
- Source: U01 explicitly invokes to-trd and describes later initialization; R01 MATH-041 and §15; G02.
- Acceptance: MATH-001 through MATH-042 map one-to-one to REQ-001 through REQ-042, with additional current-contract requirements identified separately; direct, inherited, derived and conditional bases remain distinguishable.
- Acceptance: The TRD helper supplies canonical identity/frontmatter, draft state and generated index; exact-revision approval and future plan state remain truthful.
- Acceptance: A later plan uses its canonical helper/plan.json and requirement/work/evidence traceability under separate activation; no document approval or advisory sequence automatically executes initialization.
- Depends on: REQ-040

### REQ-042 - Investigate open and difficult problems honestly
- Requirement: Support meaningful research attempts on conjectures and difficult or historically open problems without guaranteed discovery claims.
- Source: R01 MATH-042 and §§1.1, 6.9; U01.
- Acceptance: The framework can retain tested approaches, supported partial/conditional results, verified counterexamples and precise remaining obstacles rather than refuse solely because a problem is historically open.
- Acceptance: The original success boundary remains visible, with appropriate methods, resource/stopping decisions and readable partial outputs; progress is not fabricated or called a complete solution when the required outcome is unestablished.
- Depends on: REQ-010, REQ-011, REQ-032

### REQ-043 - Verify the live source and adoption baseline
- Requirement: Establish and preserve a current compatible depot, initializer and registered Template baseline before project preparation, including all material version and package differences.
- Source: U01 asks that current initialization needs inform the TRD; I01; T01; R01 §§2.1, 2.5, 13 phase 0; L01–L03.
- Acceptance: The preflight records the actual commit, relevant local modifications, helper/manifest/package hashes, registered Template, destination identity/path/content and preservation boundaries without overwriting existing work.
- Acceptance: Initializer metadata, receipt prose, implementation constants and other documentation labels are recorded as distinct facts; the executed supported helper determines the actual receipt edition.
- Acceptance: Source/Template comparisons use the documented distribution policy. The observed ontology generated-dist/Explorer-fixture exclusions are distinguished from required capability loss; unexplained incompatibility blocks affected adoption instead of prompting an unauthorized Template repair.
- Depends on: None.

### REQ-044 - Refresh publication authority after project specialization
- Requirement: Reassess and, where necessary, reestablish governance-bound memory/ontology publication authority after final project-local mathematics specialization through supported current owner operations.
- Source: R01 §11.4 and T33; I01 destination-local hash bindings; G01 source/adoption boundaries.
- Acceptance: Current assessments bind the final applicable AGENTS.md, SOUL.md and ROLE.md bytes with the exact permitted operations and destination-local scopes, including applicable advanced/Curator integration permissions.
- Acceptance: A changed bound governance file rejects stale authority; supported rebinding produces its own reviewed current owner evidence while original setup receipts and archived provenance remain intact.
- Acceptance: Missing grants or absent supported rebinding capability are explicit integration blockers; hand-edited receipt hashes, disabled guards or copied authority from another project do not satisfy readiness.
- Depends on: REQ-004, REQ-006, REQ-018

## Decisions

- **Document operation and project root:** U01 authorizes a new managed requirements capture. The unique existing `Sys4AI-Mathematics` directory and R01 identity establish its actual root; the helper is invoked with that explicit root. No Mathematics Task is created and no setup is executed.
- **Derived identity:** `sys4ai-mathematics` follows R01's recommendation and the observed collision-free registry. REQ-001/REQ-043 require the identity and collision check to remain valid when future setup is selected; this choice does not register or overwrite anything now.
- **Nonempty folder and preservation:** This project-local TRD makes the folder nonempty. The supported later route is `prepare-existing`, preserving the TRD/index and any content added before setup. R01's advisory preference for depot-held planning when a child does not exist does not override this user's already-existing selected folder; no empty-destination `create` claim is made.
- **Full-feature meaning:** All supported static capabilities and their required integration/evidence are accounted for. Installation, enablement, current permission and observed runtime remain separate. Optional backends, advanced profiles, numerical packages and formal tools are enabled only when selected; this does not exempt mandatory native research, PDF delivery, knowledge/Explorer, collaboration or maintenance evidence.
- **Design elaborations in this draft:** R01's D recommendations are incorporated as supported proposed outcomes/acceptance where they preserve the requested integrity, provenance, complete outputs or integration. They are not described as earlier approved user preferences. The compact representation and existing-owner boundary in REQ-036 preserve flexibility without authorizing a second framework.
- **Bounded choices left to planning:** The engine/build profile, package pins, class/bibliography conventions, wrapper mechanics, compact domain schema/internal APIs, exact additional directory/helper names and task-specific numeric resource limits are implementation choices under the captured constraints. R01's latexmk/LuaLaTeX proposal is a candidate; compatible supported tooling can satisfy the same complete source/PDF, reproducibility and security criteria. No engine installation, library, fixed budget or permanent concurrency number is mandated by an example.
- **Host document behavior:** Separately selected standalone LaTeX creation/editing in this Codex environment uses its built-in source editor and compiler by default under host instructions. That does not require installing a TeX plugin/runtime and does not itself qualify the future project's multi-file build pipeline; tooling must fit the actually selected document scope.
- **Conditional formal verification:** REQ-030 and R01 T40 apply only when formal checking is selected. Lean is an example, not an already chosen dependency or prerequisite for ordinary initialization; trusted assumptions and intended-statement correspondence remain required for any formal claim.
- **Expertise and topology:** Mathematics is the common reasoning-agent baseline. Physics/philosophy/other expertise is selected for fit rather than universally deployed. Shared role references and the actual required category team are preserved; the advisory role list is a profile catalogue, not a standing launch instruction.
- **Audience and writing:** Academic precision with concise orientation and explicit prerequisites is the baseline drawn from R01/W01. Specific research Tasks refine audience and scope. The supplied skill, existing parent and manuscript conventions control authorized editing; there is no default venue, paper-count target, disclosure or forced conclusion.
- **Research and PDF status:** A partial or incomplete mathematical result still needs its retained/handoff PDF. Missing/stale/failed outputs block current delivery without promoting mathematical status. A readable output can complete a bounded documentation/investigation objective only when that is its actual acceptance contract.
- **Publication bindings:** Mathematics edits to bound governance can invalidate setup-time permissions. REQ-044 requires supported current owner reassessment/rebinding and separate evidence; receipt history and guards are preserved. A missing owner operation or grant is an execution blocker rather than permission to edit hashes by hand.
- **Version and inventory observations:** The observed metadata/prose/helper/SPECS labels remain version-specific source facts. Required source-to-Template files matched after actual documented exclusions; that static comparison is not a runtime test or permission to refresh assets. Future preflight rechecks changed sources instead of treating this snapshot as permanent.
- **Verification detail:** R01 §13 is advisory future dependency guidance, not a generated plan. R01 T01–T43 are source-backed scenario coverage; a future authorized plan selects proportionate checks, shares overlapping evidence and records all mandatory remaining failures/limits. No future check is marked performed in this TRD.
- **Approval and next-stage boundary:** This revision starts in `draft`; structural eligibility does not establish user approval. Only approval of the exact presented unchanged revision allows the helper to mark `trd_done`. A later managed plan and initialization require their separate user selection; no downstream state changes follow automatically.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
