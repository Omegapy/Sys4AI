---
schema_version: 2
trd_id: "TRD-20261003-5B3283BB"
title: "Sys4AI full operational project initialization"
slug: "sys4ai-full-operational-project-initialization"
created_at: "2026-10-03T18:34:17-06:00"
updated_at: "2026-10-03T20:24:04-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 1 requirements baseline in this chat."
---

# Task Requirement Document: Sys4AI full operational project initialization

## Destination

Improve the Sys4AI depot's initiation/initialization process so a new project, an existing project receiving Sys4AI, or a selected previously initialized project can finish with all supported Sys4AI features operational by default. Completion must establish compatible installed assets, required runtimes, useful project content and verified integrated use while preserving project-owned work.

## Captured user intent

- U01: The user requested a new depot-level requirements document using the detailed Æther Flow audit, the Mathematics initialization readiness handoff and `depot/system-guide.md`, covering initialization of both new and existing projects.
- U02: On October 3, 2026, after the alternatives and recommendation were presented, the user selected "**option 1: all supported Sys4AI features operational by default**." The recommendation retained existing project content and explicit opt-outs, reported blockers honestly, and kept retired features and unattended services off.
- This is requirements capture. The selected default is settled; approval of this exact saved TRD remains separate from that scope decision and from authorization to plan or implement it.

## Context and sources

The reports establish why the initialization contract needs to change. Æther Flow has substantial working core and browser behavior, but reports collaboration integrity and Lessons discovery defects, missing generated products and limited knowledge presentation. Mathematics reports corpus path failure, app-owner incompatibility, empty Home content, stale compilation, unreadable Explorer data and a collaboration mismatch. Both distinguish inactive optional runtimes and unverified Curator execution from proved software defects. Their earlier accepted setup scopes and completion records must retain those meanings.

The current initializer still selects `governance-starter-v14`. Its static assessment returns `runtime: not-exercised` and `provisioned: false`; the Project app assessor checks assets, identity and launcher mode without opening the app or checking populated Home content. U02 intentionally changes the target for future full initialization. It does not retroactively prove the old installer violated a different contract.

| Source | Locator and scope |
| --- | --- |
| S01 | [Æther Flow detailed audit](../Projects/Sys4AI-The-AEther-Flow/Verification/sys4ai-feature-audit-2026-10-03/REPORT.md), October 3, 2026; all 18 areas, F-01 through F-06, operational observations and verification limits. |
| S02 | [Mathematics readiness handoff](../Projects/Sys4AI-Mathematics/docs/sys4ai-initialization-readiness-handoff-2026-10-02.md), October 2, 2026; issues 1 through 10, preservation and diagnostic boundaries. |
| S03 | [System guide](../depot/system-guide.md), working-tree description dated October 2, 2026; feature inventory, skills, roles, setup routes, activation states and ownership. |
| S04 | [Reusable initializer contract](../SKILLS-depo/init-new-project/SKILL.md); source/destination rules, preservation, current shared-app edition, selected adoption and recovery. Historical edition paragraphs remain historical context. |
| S05 | [Template update guide](../depot/template-update.md) and [registry](../depot/projects.json); source-to-Template ownership and the actual registered depot/Template identities. |
| S06 | [Initializer implementation](../SKILLS-depo/init-new-project/scripts/init_new_project.py), `SETUP_CONTRACT` and setup routes; [static health](../SKILLS-depo/init-new-project/scripts/init_static_health.py), `assess`/`apply`; [Project app setup](../SKILLS-depo/init-new-project/scripts/init_project_app.py), `assess`. These were inspected as current implementation, not executed to initialize a project. |
| G01 | Depot [AGENTS.md](../AGENTS.md), [SOUL.md](../SOUL.md), [ROLE.md](../ROLE.md) and [SPECS.md](../SPECS.md); source ownership, authorization, preservation, native orchestration and proportionate verification. |

Inspected report/guide snapshots:

| Source | SHA-256 |
| --- | --- |
| S01 | `d0ae392a94196aafa70c2ee9d8b74200dd4b1f12566b63e08151848ec8366c1f` |
| S02 | `c0c23dc7a86aaf3e6c189ab420ffdecf4ff295d0f658def3af061bee94e25beb` |
| S03 | `ac8f9d9651dc1226d6b3a3935b00329328042392841d5eee2215a4937503ac64` |

The reports are dated source evidence, not a fresh reproduction of every child-project defect. Their linked historical TRDs, plans, native receipts and scientific results retain their own authority. This capture does not modify or supersede them.

For this baseline, **operational** means usable on demand with current evidence for the feature's supported behavior. It does not mean every service or agent runs continuously. **Populated** means useful content supported by this project's available sources, with legitimate empty states distinguished from missing setup. **Full** includes the previously optional supported memory backend/hybrid retrieval and four active ontology profiles, plus core generated products, reviewed Home/Explorer content and verified session maintenance. The retired authoring workbench, unattended operation and depot-only services are outside a child's runtime baseline.

Guide coverage is explicit:

| Guide area | Main requirements |
| --- | --- |
| 1. Governance and Director | REQ-005, REQ-015 |
| 2. Role catalog | REQ-016 |
| 3. Task ledger | REQ-017 |
| 4. Native orchestration | REQ-018 |
| 5. Shared collaboration | REQ-009, REQ-019 |
| 6. Managed requirements | REQ-017 |
| 7. Managed plans | REQ-017 |
| 8. Memory | REQ-020 through REQ-025 |
| 9. Learning review | REQ-023 |
| 10. Core ontology | REQ-026, REQ-027 |
| 11. Advanced ontology | REQ-028 through REQ-031 |
| 12. Curator | REQ-036, REQ-037 |
| 13. Project app | REQ-008, REQ-024, REQ-025, REQ-032, REQ-034, REQ-035 |
| 14. Knowledge Explorer | REQ-033, REQ-035 |
| 15. Initializer | REQ-001 through REQ-014, REQ-040 through REQ-044 |
| 16. Reusable sources and Template pipeline | REQ-007 |
| 17. Registry | REQ-038 |
| 18. Licensing | REQ-039 |

## In scope

- The shared initialization workflow, relevant reusable owner-package corrections, checked Template distribution and exact adoption of affected initializer assets into the active depot.
- New creation, first existing-project preparation, selected upgrade of an initialized project, and the compatible assessment/rerun/recovery paths.
- Required local Sys4AI runtime preparation and enablement; destination identity and authority bindings; project-specific content; current knowledge products; focused consumer-boundary regression checks and integrated operational qualification.
- Preservation of custom content, explicit choices, independent histories and local policy; useful diagnostics and accurate operational handoff.

## Out of scope

- Implementing this TRD, creating a downstream plan or Task, spawning agents, installing runtimes or changing code/configuration during this document-capture operation.
- Automatically repairing or upgrading Æther Flow, Mathematics or any other registered product. They are evidence sources; each actual destination adoption needs its own selected scope. Mathematics' paused research Task remains protected.
- Solving product/scientific problems, claiming new scientific results, comprehensive ontology modeling of every source, or fabricating lessons to fill an empty store.
- Reviving the retired browser authoring workbench; enabling unattended AI, standing autonomous writes, schedules, services, hooks, external notifications or idle-agent wakeups by default.
- Git creation/commit/push, remotes, GitHub Pages, deployment, purchases, credential collection, relicensing, bulk propagation, automatic product watchers or copying project history/runtime into the Template.
- A promise of universal platform portability, performance targets, a fixed model choice or an exhaustive historical testing campaign unsupported by the supplied sources.

## Task requirements

### REQ-001 - Make full operational initialization the default

- Requirement: New-project creation, first preparation of an existing project, and a selected upgrade of an initialized project shall target all supported Sys4AI features as operational by default.
- Source: U01; U02; S01, assessment dimensions and recommended follow-up; S02, Finding; S03, initialization routes.
- Acceptance: A normal new initialization request includes the supported memory backend and hybrid retrieval, ontology standards, inference, semantic retrieval and guards, generated knowledge products, populated readers, collaboration and session maintenance in its required outcome.
- Acceptance: Asset copying or passing static checks alone cannot complete a full initialization request; any unmet required operational criterion leaves that request incomplete with a named reason.
- Acceptance: A selected existing-project upgrade adds a new attributable operation without changing the historical meaning of its original installation.
- Depends on: None.

### REQ-002 - Account for every supported feature

- Requirement: Initialization shall use a versioned capability inventory that gives every applicable feature an owner, prerequisites, default activation, content needs and observable operational acceptance.
- Source: U02; S03, all 18 feature areas and What must a new system implement; S01, All 18 feature areas.
- Acceptance: The initial inventory accounts for all 18 guide areas, including the twelve system skills and applicable role packages, and distinguishes destination features from depot-only responsibilities.
- Acceptance: Supported advanced targets include standards, inference, semantic retrieval and guards; the retired browser authoring workbench is explicitly excluded.
- Acceptance: Each feature has an explicit disposition; neither absence from a narrow health command nor a newly added shared package silently removes an obligation.
- Depends on: REQ-001

### REQ-003 - Respect explicit reduced scope and existing opt-outs

- Requirement: Initialization shall retain an explicit user-selected reduction or current opt-out while distinguishing it from an inherited disabled default or an earlier deferment.
- Source: U02, acceptance of the recommended full default; S03, clean defaults and preserved preferences; S04, preservation rules; G01.
- Acceptance: An inherited backend/profile-off default does not exclude that supported feature from a newly selected full initialization.
- Acceptance: An explicit capture-off, session-off or other protected user choice is preserved unless the current request supersedes it; the receipt identifies the choice and its effect on the full target.
- Acceptance: A deliberately reduced setup is clearly labeled with its actual coverage and is never presented as all supported features operational.
- Depends on: REQ-001, REQ-002

### REQ-004 - Inspect the exact destination before changing it

- Requirement: Each initialization shall establish the real destination, stable identity, purpose, intended workflows, available source set, project instructions, existing setup/runtime state and preservation boundary before mutation.
- Source: S03, new and existing project routes; S04, Scope and ownership; S02, issues 1 and 3; G01.
- Acceptance: Preflight uses supplied intent and inspected project sources to establish purpose and expected use, then inspects identity, governance, complete package inventories, licensing, corpus directory spellings, receipts, relevant configurations and existing Task ownership.
- Acceptance: Identity collisions, unsafe paths, unsupported legacy layouts, active conflicting writers and incomplete transactions produce specific diagnostics before conflicting writes.
- Acceptance: The existing beneath-Projects boundary and registered Template selection remain enforced; the depot, Template and another registered project cannot be mistaken for the target.
- Depends on: REQ-002

### REQ-005 - Keep operational setup within its actual authority

- Requirement: Full initialization shall perform the necessary local setup and qualification through their existing owners within current authorization, without treating feature enablement as unrestricted execution or publication authority.
- Source: U01; U02; G01; S03, activation distinctions; S04, owner/adoption and runtime boundaries.
- Acceptance: An authorized full setup can carry out its required local dependency/model preparation, configuration, knowledge preparation and verification without treating every supported feature as a separate optional selection.
- Acceptance: Task execution, canonical knowledge writes and guarded actions still satisfy their current owner, scope, grant and version checks; missing authority is an exact resumable blocker.
- Acceptance: Read-only requests do not provision or repair anything, and initialization does not imply Git creation/publication, deployment, credential use, external notifications or standing autonomous writes.
- Depends on: REQ-001, REQ-004

### REQ-006 - Provide a reproducible usable runtime

- Requirement: Initialization shall establish and record a supported local runtime and the dependency/model resources needed by every required capability, including the actual execution contexts used by isolated readers.
- Source: U02; S01, inactive advanced capabilities, Lessons extraction and Installation; S02, issues 2 and 8; S03, runtime boundaries; G01, SPECS.md.
- Acceptance: The receipt identifies the working interpreter, reviewed dependency specifications, selected model artifacts and relevant runtime paths; existing compatible resources may be reused after verification.
- Acceptance: Required packages, models and indexes are prepared and exercised through their owner routes; unavailable downloads, unsupported confinement, missing native tools or insufficient host resources remain named blockers rather than causing silent feature disablement.
- Acceptance: Direct helpers, isolated app owners and the launcher each use a verified compatible context; a target-local virtual environment is not required merely to satisfy a directory convention.
- Depends on: REQ-002, REQ-004, REQ-005

### REQ-007 - Distribute a coherent reusable release

- Requirement: Initializer improvements and affected shared packages shall be authored in their owning reusable collections, distributed through the checked Template pipeline, and adopted into the active depot only within an exact reviewed file boundary.
- Source: G01; S03, reusable collections and feature delivery; S04; S05.
- Acceptance: The source packages, inventories, dependency contracts, starter mappings and compatibility declarations agree for the selected release, and the registered Template update check passes.
- Acceptance: The Template remains neutral, without destination identities, grants, learned records, live Tasks, models, environments or generated project knowledge; full operational defaults are applied at destination setup.
- Acceptance: The active depot's documented initializer route uses the reviewed adopted release without replacing its separate Task policy; no ordinary product project is refreshed by the Template update.
- Depends on: REQ-002

### REQ-008 - Admit compatible app owner variants as a whole

- Requirement: Initialization shall establish reviewed compatibility between the Project app and the complete installed Task, role, memory, TRD and plan owner dependencies for each supported project variant.
- Source: S02, issue 3; S01, functioning app and preserved local adaptations; S04, whole-package preservation.
- Acceptance: Both the generic Template/child variant and the supported depot variant are checked against their own reviewed executing bytes; a depot-only manifest cannot reject an otherwise supported clean child installation.
- Acceptance: Work and Lessons owner admission succeeds with the actual dependency closure, including Task/role dependencies needed by memory admission.
- Acceptance: Unknown or changed code fails closed with exact mismatches; updating expected hashes without code review, disabling checks or copying the depot's Task policy over a child does not satisfy acceptance.
- Depends on: REQ-004, REQ-007

### REQ-009 - Keep collaboration integrity layers coherent

- Requirement: Collaboration installation and subsequent authorized adapter changes shall maintain a coherent complete package inventory, trusted owner-profile declaration and exact owner-file bindings.
- Source: S01, F-01; S02, issue 7; S04, Default collaboration activation.
- Acceptance: Both the adapter inventory digest and the trusted owner-profile declaration agree with the reviewed installed variant, and all declared owner-file pins pass.
- Acceptance: A supported clean setup and reviewed local adapter update both pass installed collaboration health with enabled and ready outcomes.
- Acceptance: Conflicts remain visible and preserve reviewed local behavior such as Task-capacity support; neither a single checksum edit nor blind restoration of old code counts as repair.
- Depends on: REQ-007, REQ-008

### REQ-010 - Offer a governed path for customized installations

- Requirement: Existing projects with customized or incomplete packages shall receive an exact compatibility/adoption decision that preserves their work and permits a separately reviewed supported repair.
- Source: U01; S01, Installation and F-01; S02, issue 3 and Requested Sys4AI follow-up; S04.
- Acceptance: Preflight identifies the affected whole packages, executing dependencies, local adaptations, proposed source/target changes and preserved files.
- Acceptance: An incompatible preserved package prevents the relevant full-readiness claim and produces a bounded repair/adoption route; it is not overwritten or silently merged.
- Acceptance: An authorized repaired variant receives renewed owner and setup evidence, while unrelated configuration, scientific sources and historical receipts retain their original content.
- Depends on: REQ-004, REQ-007, REQ-008, REQ-009

### REQ-011 - Preserve project work and independent state

- Requirement: Initialization and qualification shall preserve project-owned content, local policy, active ownership and canonical history outside the exact authorized change set.
- Source: U01; G01; S01, preservation and retained native evidence; S02, Scope and evidence limits; S04.
- Acceptance: Before/after review confirms preservation of existing identity, custom governance, product/research files, Tasks, TRDs, plans, role provenance, memory records, ontology assertions, repository state and licensing except for exact authorized changes.
- Acceptance: An active or paused research Task is neither resumed nor replaced for setup; completed Tasks and plans retain their prior scope and status.
- Acceptance: Qualification content is clearly attributable and isolated where possible; no copied depot lessons, fabricated project results or sample production Tasks are used to make a new project appear populated.
- Depends on: REQ-004, REQ-005, REQ-010

### REQ-012 - Resume setup without losing provenance

- Requirement: Operational initialization shall extend the existing setup receipt and recovery model with attributable stage results, preserving historical editions and exact in-progress requests.
- Source: S03, module adoption and receipts; S04, Completion and receipts and Reruns and recovery; G01.
- Acceptance: Each operation records source versions, adopted/preserved/refreshed assets, current observations, runtime/content/qualification outcomes, failed stage and exact next recovery gate without rewriting original adoption hashes.
- Acceptance: An equivalent completed rerun adds no duplicate identity or adoption and preserves later user edits; a selected new full upgrade is a distinct operation rather than a relabeled historical receipt.
- Acceptance: Interruption resumes recognized pre/post states against frozen inputs; changed sources, conflicting target edits or live locks stop replay without deleting recovery evidence or repeating non-idempotent owner actions.
- Depends on: REQ-004, REQ-005, REQ-010, REQ-011

### REQ-013 - Report readiness at the level actually verified

- Requirement: Initialization shall report installation, enablement, authorization, content population, runtime operation and evidence freshness separately and derive full completion from all required outcomes.
- Source: S01, assessment dimensions and final follow-up; S02, issue 10; S03, verification semantics; S06.
- Acceptance: A feature reports passed, blocked, failed, unverified, deliberately excluded or not applicable with its reason, evidence scope and observation date; empty legitimate content is explained separately.
- Acceptance: A response-level ready status, static_ready value, configured flag or successful asset transaction cannot override an incompatible owner, failing query, missing required product or unverified runtime.
- Acceptance: The full-initialization result is unsuccessful/incomplete while any required applicable acceptance remains unmet, even when an underlying base installation transaction is complete.
- Depends on: REQ-001, REQ-002, REQ-003, REQ-012

### REQ-014 - Invalidate only evidence affected by change

- Requirement: Readiness shall be tied to exact relevant package, configuration, content, model/index and host inputs, and material changes shall invalidate affected operational claims.
- Source: S01, retained evidence and post-installation collaboration drift; S02, issues 3, 5 and 10; S04, rerun assessment; G01, proportionate verification.
- Acceptance: Changed adapter, owner, source, configuration or runtime inputs identify the affected checks and dependent products instead of inheriting a historical green result.
- Acceptance: Unchanged exact-version evidence may be reused with its original scope and limitations; current destination and host integration checks remain explicit.
- Acceptance: Validation follows the affected dependencies and supports an explicit full assessment without requiring a whole-depot or unrelated historical archive scan before every bounded operation.
- Depends on: REQ-012, REQ-013

### REQ-015 - Install usable destination governance

- Requirement: Initialized projects shall have coherent destination-specific governance and technical guidance that explains the full operational default and retains the project's actual authority boundaries.
- Source: S03, governance feature and initialization assets; S04, identity specialization; G01.
- Acceptance: The effective SOUL, AGENTS, ROLE, SPECS and project entry documentation identify the destination and describe required workflows and runtime usage consistently.
- Acceptance: Custom guidance is preserved or changed only within the reviewed boundary; required capabilities that conflict with preserved guidance are reported for resolution.
- Acceptance: Generic child guidance retains its intended Task intake policy and does not acquire the depot's matching/age-closure policy by copying.
- Depends on: REQ-004, REQ-007, REQ-011

### REQ-016 - Supply and validate the required role catalog

- Requirement: Initialization shall make the role pairs needed by supported Sys4AI workflows discoverable and valid through the role owner.
- Source: S03, Role catalog and six active roles; S01, working role inventory; S02, role validation; S04, role layouts.
- Acceptance: The actual paired AGENTS.md and ROLE.md files validate, their dependencies exist and generated navigation matches the destination paths.
- Acceptance: Project-specific roles and provenance are preserved; legacy/case-conflicting collections use the separate reviewed role transition rather than a second silently created collection.
- Acceptance: Installed roles are reported as available definitions, with no claim that their agents are running.
- Depends on: REQ-007, REQ-011, REQ-015

### REQ-017 - Qualify Task, requirements and plan owners

- Requirement: Initialized projects shall support their managed Task, TRD and implementation-plan workflows through compatible canonical owners while preserving each workflow's independent lifecycle.
- Source: S03, feature areas 3, 6 and 7; S01, validated canonical work; S02, working direct owners and app mismatch; G01.
- Acceptance: Owner validation/read operations succeed against the actual project state and current projections, including a legitimately empty new-project ledger or catalog.
- Acceptance: Bounded release qualification demonstrates each changed create/update/validation path through its helper; ordinary project setup does not invent work items or approve unseen documents.
- Acceptance: Document approval, plan readiness, Task execution and product completion remain distinct; app projections agree with canonical owner reads.
- Depends on: REQ-008, REQ-011, REQ-015, REQ-016

### REQ-018 - Establish real native orchestration capability

- Requirement: Full operational readiness shall include current native-host admission and evidence that the installed Task orchestration can execute its governed manager and child workflows.
- Source: U02; S03, native orchestration and category teams; S01, Native execution; S02, later native evidence; G01.
- Acceptance: Host preflight observes actual native tools and capacity, exact effective model/reasoning inheritance and the required context-independence guarantees; role files or a stored native ID are insufficient.
- Acceptance: A bounded authorized execution, or exact applicable retained qualification plus current destination admission, supports manager reservation, real launch receipt, activation, delegation and final owner verification.
- Acceptance: Generic, complex and extra-complex category gates retain their required distinct participants and review/synthesis rules; missing authority or host support blocks the claim without simulated receipts or a reduced team.
- Depends on: REQ-005, REQ-006, REQ-016, REQ-017

### REQ-019 - Verify collaboration through a governed exchange

- Requirement: Collaboration shall work with the installed Task owner during an authorized native workflow, beyond passing installation health.
- Source: S01, F-01 and receipt distinctions; S02, issue 7; S03, Shared agent collaboration; G01.
- Acceptance: Qualification uses a real current manager policy, native assignment bindings, scoped participant grants and the required read checkpoints.
- Acceptance: A permitted post, addressed notification observation, exact-version reading receipt and owner snapshot/disposition are verified; uncertain delivery is not reported as acknowledged reading.
- Acceptance: Independent initial candidates and first reviews remain sealed, and material messages trigger current owner assessment and required input/version revalidation before dependent work.
- Depends on: REQ-009, REQ-018

### REQ-020 - Match memory corpus access to real paths

- Requirement: Initialization shall reconcile permitted memory corpus discovery with the destination's canonical directory entries and source policy without weakening confinement.
- Source: S02, issue 1; S01, preserved corpus-access and temporary-path corrections; S04, path safety.
- Acceptance: A project using Research rather than research can complete an ordinary allowed corpus search and affected packet preparation using its actual safe paths.
- Acceptance: Case-insensitive lookup, Unicode aliases, symbolic links, canonical temporary paths and true path conflicts are handled according to the existing safety contract; permissive alias bypass is not accepted.
- Acceptance: Authorized source coverage is reported against actual files, and excluded/private/out-of-project content remains excluded.
- Depends on: REQ-004, REQ-006, REQ-011

### REQ-021 - Verify normal memory retrieval and Task packets

- Requirement: Core memory readiness shall require useful exact and lexical retrieval over permitted project sources and correct preparation of selected frozen Task input packets.
- Source: S01, Memory and learning; S02, issue 1; S03, Project memory and Task integration.
- Acceptance: A normal keyword query over the destination corpus succeeds and returns supported findings/documents; an exact record read alone cannot substitute for the corpus query.
- Acceptance: Packet preparation succeeds on the selected safe sources, records their exact versions and confines retrieval to the configured bounds.
- Acceptance: When used for independent initial solvers, the selected frozen packet bytes are identical and do not permit live sibling information to contaminate the baseline.
- Depends on: REQ-018, REQ-020

### REQ-022 - Enable and qualify the memory backend and hybrid retrieval

- Requirement: Full initialization shall provision or reuse the supported memory backend and semantic resources, enable the intended hybrid retrieval path and demonstrate their operation.
- Source: U02; S02, issue 2; S01, inactive memory services; S03, Project memory.
- Acceptance: The supported backend, projection, embedding/model resources and semantic index are available, destination-bound and current under the memory owner's reviewed configuration.
- Acceptance: A representative hybrid query exercises the selected runtime and returns attributable results with source freshness and scope information; lexical-only success does not satisfy this criterion.
- Acceptance: Missing or stale backend/model/index resources are reported at that layer, with no fallback represented as a successful hybrid qualification.
- Depends on: REQ-005, REQ-006, REQ-020, REQ-021

### REQ-023 - Make capture and learning usable under local authority

- Requirement: Memory automatic capture and learning review shall share a working destination-local completion route, with capture enabled by default and supported explicit opt-outs preserved.
- Source: U02; S01, real memory publication/supersession evidence; S03, Project memory and Learning review; S04, bindings and preserved preferences.
- Acceptance: Current destination governance hashes, required contracts, compatible owners and applicable publication scope admit the shared completion checkpoint.
- Acceptance: A useful evidence-backed finding can be published, retrieved and later superseded through the owner in bounded qualification; duplicate or unsupported findings are declined and a no-finding outcome is valid.
- Acceptance: New projects inherit capability and preferences, never another project's lessons, transcripts or runtime state; learning creates no second store or unattended loop.
- Depends on: REQ-003, REQ-005, REQ-011, REQ-021

### REQ-024 - Keep saved findings discoverable in Lessons

- Requirement: The Project app's Lessons query shall retain access to matching permitted memory findings when document hits occupy an earlier result page.
- Source: S01, F-02; S02, issue 3.
- Acceptance: A query with a matching active saved finding beyond fifteen preceding document hits still exposes that finding through correct selection or bounded continuation.
- Acceptance: Selection and continuation are correct at the upstream owner query as well as the display layer; moving only the client-side slice is insufficient.
- Acceptance: Exact finding reads retain lifecycle, applicability, evidence and source-currentness information without relaxing corpus permissions.
- Depends on: REQ-008, REQ-021, REQ-023

### REQ-025 - Qualify extraction in the actual reader context

- Requirement: Required source extraction and search coverage shall be assessed in the same execution context used by each reader and shall expose precise unsupported or partial coverage.
- Source: S01, F-02 and browser source/PDF limits; S02, memory and app integration; S03, permitted source readers.
- Acceptance: A runtime dependency available to a direct helper is not assumed available to an isolated app owner; selected Markdown, TeX, PDF or other supported source routes are checked where they execute.
- Acceptance: Source delivery, body extraction, search indexing and saved-finding availability have distinct results; extraction caveats do not hide otherwise valid notes.
- Acceptance: Where required coverage cannot operate, the affected criterion remains incomplete with the exact limitation; no unsupported format capability is invented.
- Depends on: REQ-006, REQ-008, REQ-020, REQ-024

### REQ-026 - Populate useful source-backed project knowledge

- Requirement: Initialization shall create or preserve reviewed project ontology content that represents the project's known purpose, principal artifacts, important concepts and supported relationships at the scope established by its actual sources.
- Source: U02; S01, F-04; S02, issues 5 and 6; S03, Core ontology.
- Acceptance: The destination knowledge identifies relevant project artifacts and workflows, and maps the declared initial content scope to current permitted sources rather than counting shared Sys4AI terms as domain coverage.
- Acceptance: For an existing project, principal document families and their supported assumptions, outcomes and dependencies are represented to the agreed source-backed scope; unavailable evidence is a visible gap rather than an invented assertion.
- Acceptance: For a genuinely new project, the stated purpose and known structure supply honest starter knowledge; absent research results are not fabricated and no arbitrary minimum term count determines readiness.
- Depends on: REQ-004, REQ-005, REQ-011

### REQ-027 - Produce and verify all required core knowledge products

- Requirement: Full initialization shall leave core ontology validation, compilation, generated wiki and ontology-to-memory association products current and usable.
- Source: U02; S01, F-03; S02, issue 5; S03, Core ontology.
- Acceptance: Required-product health explicitly includes compile, build-wiki and link-memory, and verifies their input hashes and freshness rather than relying on the narrower default health selection.
- Acceptance: A representative generated page and each applicable tested association can be followed to their current sources through the relevant owner/read route.
- Acceptance: A new project with no legitimate saved findings may have an explicitly verified empty association result; a missing or unbuilt product is not equivalent to that valid empty state.
- Depends on: REQ-021, REQ-023, REQ-026

### REQ-028 - Enable supported ontology standards operations

- Requirement: Full initialization shall enable and qualify the supported RDF/SPARQL and SHACL standards profile through its reviewed local runtime.
- Source: U02; S01, advanced capability inventory; S02, issue 8; G01, SPECS.md advanced ontology contract.
- Acceptance: Required pinned dependencies, destination configuration and actual host confinement pass the owner's checks.
- Acceptance: Representative supported read-only query and validation operations succeed over current project inputs, with asserted, inferred, derived and external graph boundaries retained.
- Acceptance: Unsupported query or standards semantics remain explicitly unsupported, and no claim of unrestricted RDF/OWL support follows from enabling the profile.
- Depends on: REQ-005, REQ-006, REQ-026, REQ-027

### REQ-029 - Enable and verify finite inference

- Requirement: Full initialization shall make the supported finite ontology inference profile usable without promoting derived conclusions into authored or scientifically established facts.
- Source: U02; S01, advanced capability inventory; S02, issue 8; G01, SPECS.md finite-rule boundary.
- Acceptance: A supported rule case produces the expected source-attributable derived conclusion in the inference context.
- Acceptance: Changing relevant source inputs makes affected inferred output stale until rebuilt; asserted and inferred records remain distinguishable.
- Acceptance: The supported finite rule profile and its limits are stated; passing inference is not evidence that a project's scientific claims are true.
- Depends on: REQ-028

### REQ-030 - Enable ontology semantic retrieval

- Requirement: Full initialization shall make the supported ontology semantic retrieval profile operational with exact model, package and index provenance.
- Source: U02; S01, advanced capability inventory; S02, issue 8; G01, SPECS.md semantic boundaries.
- Acceptance: The selected local model/runtime is prepared, the index reflects current permitted inputs and a representative semantic query succeeds.
- Acceptance: Results retain source identity and freshness; similarity does not grant truth, equivalence, approval or execution authority.
- Acceptance: Model, package or input changes invalidate the affected qualification and indexes through the owner.
- Depends on: REQ-006, REQ-014, REQ-026, REQ-027

### REQ-031 - Activate supported guards without bypassing ownership

- Requirement: Full initialization shall enable supported ontology guards with current bindings for the declared guarded action families while retaining every canonical owner's independent authorization checks.
- Source: U02; S01, inactive guards; S02, issue 8; S03, supported advanced features; S04, guarded adoption.
- Acceptance: Guard qualification covers the declared ontology, memory, Task, TRD, plan, role, Template and setup routes as applicable to the owning root.
- Acceptance: A bounded permitted action and a denied stale/out-of-scope action demonstrate actual interception through supported dispatch, with the relevant owner still enforcing its own grant.
- Acceptance: Package/configuration changes refresh bindings only through the reviewed route; direct filesystem edits and unintegrated tools are not represented as covered, and the retired browser workbench remains off.
- Depends on: REQ-005, REQ-007, REQ-008, REQ-014, REQ-028

### REQ-032 - Complete and review the project Home

- Requirement: Initialization shall supply a useful reviewed Home page with destination-specific purpose, scope, audience, source documents and a Start here entry.
- Source: S02, issue 4; S01, working Home; S03, Project app and owner content responsibility; U02.
- Acceptance: Required Home explanations are nonempty, factual and tied to permitted sources with current text/source review bindings.
- Acceptance: Selected entry documents and Start here resolve to the intended project; absent work is shown honestly when the project's Task ledger is empty or completed.
- Acceptance: Existing reviewed prose is preserved or revised only within the authorized content boundary, and the actual browser Home is observed with the correct project identity.
- Depends on: REQ-005, REQ-008, REQ-011, REQ-015, REQ-026

### REQ-033 - Make Explorer navigation useful and readable

- Requirement: Initialization shall provide working standalone and embedded knowledge reading with meaningful project starting entries and process descriptions.
- Source: S01, F-04 and browser observations; S02, issue 6; S03, Knowledge Explorer.
- Acceptance: Explorer health and actual browser reading succeed for selected project data; configured availability or valid packaged assets alone cannot satisfy this requirement.
- Acceptance: Overview starts, Terms, Processes, relationship lists, source access and Map navigation expose reviewed relevant content and correct identity.
- Acceptance: A valid empty domain state is explained with known project/process entry points; a failing snapshot path is diagnosed separately from canonical validation or stale compilation.
- Depends on: REQ-008, REQ-026, REQ-027, REQ-032

### REQ-034 - Verify the integrated Project app

- Requirement: The Project app shall present consistent canonical Work, Lessons, knowledge, search, source previews, Health and Help results for the initialized project.
- Source: S01, Home and browser functionality; S02, issues 3, 6 and 10; S03, Project app.
- Acceptance: Work agrees with Task/TRD/plan owners; Lessons includes matching findings; live integrated search includes the supported document and knowledge sources.
- Acceptance: Permitted text and binary delivery routes are checked for representative selected sources, and reported coverage limits distinguish source bytes from extraction and visual rendering.
- Acceptance: Health exposes the operational readiness dimensions and blockers, while Help lists actual installed skills/roles and supported use; the browser grants no authoring or execution authority.
- Depends on: REQ-013, REQ-017, REQ-024, REQ-025, REQ-033

### REQ-035 - Qualify launch, session safety and shutdown

- Requirement: Initialization shall verify the supported launcher and reader lifecycle on the selected host without installing an unattended service.
- Source: S01, launcher and session lifecycle observations; S02, installed launcher without browser qualification; S03, reader launch and runtime boundaries.
- Acceptance: The real supported launcher uses the verified runtime, opens the intended destination and serves its packaged assets; executable permissions are correct where required.
- Acceptance: Loopback scope, permitted-source access, session revocation and the existing Host/Origin/session/CSRF controls remain enforced.
- Acceptance: Qualification-owned sessions/services are closed or stopped with verified cleanup; an already running unrelated service is preserved, and on-demand readiness does not require permanent background execution.
- Depends on: REQ-005, REQ-006, REQ-032, REQ-033, REQ-034

### REQ-036 - Complete an admitted Curator session operation

- Requirement: Full initialization shall qualify the enabled active-session Curator route from observation through an eligible current owner operation and exact completion receipt.
- Source: S01, F-05; S02, issue 9; S03, Project Curator; S04, session installation.
- Acceptance: Session start/return observes a bounded change, the live authorized owner admits a genuinely needed operation within the configured session budget, and the exact owner receipt supports its result.
- Acceptance: Only the completed attributable delivery is consumed; unavailable owners, exhausted budgets and unhandled events remain pending with explicit status.
- Acceptance: If the real destination has no eligible maintenance, a clearly separated representative qualification exercises the same installed route without fabricated production work; observation alone is never called completed maintenance.
- Depends on: REQ-005, REQ-006, REQ-011, REQ-014, REQ-018, REQ-023, REQ-027

### REQ-037 - Preserve maintenance ownership and propagation rules

- Requirement: Curator and later setup maintenance shall route changes through their current canonical owners and preserve dependent source/review bindings and protected project work.
- Source: S01, F-05 and F-06; S02, issues 9 and 10; S03, Curator and ownership; G01.
- Acceptance: Document ownership protects scientific/product sources, active Task state and user-authored records; setup does not manufacture a Task or reopen completed work solely to clear a queue.
- Acceptance: A legitimate documentation, package or knowledge update identifies affected Home, memory, ontology and guard evidence and refreshes it through the corresponding owners.
- Acceptance: Session maintenance remains bounded live-session work; unattended schedules, services, hooks, external notifications and standing autonomous writes remain unselected.
- Depends on: REQ-011, REQ-014, REQ-031, REQ-036

### REQ-038 - Keep factual registration accurate

- Requirement: Initialization shall maintain exactly one truthful registry entry for the selected project without treating registration as runtime or external-state authority.
- Source: S03, Workspace registry; S01, Installation, provenance, registry and licensing; S04; G01.
- Acceptance: The real stable ID, canonical relative path and project kind agree with local identity; reruns do not add duplicates or claim an unregistered directory.
- Acceptance: Existing repository/remote/Pages information is retained or updated from permitted actual observations, with unverified remote/deployment state identified.
- Acceptance: No repository, remote, branch, Pages site or deployment is created solely because the project is registered.
- Depends on: REQ-004, REQ-011, REQ-012

### REQ-039 - Preserve the complete existing licensing system

- Requirement: Initialization shall preserve a destination's existing licensing as a whole and adopt the Template license trio only when the existing licensing rules permit it.
- Source: S03, Licensing; S01, verified license preservation; S04, licensing detection; G01.
- Acceptance: Preflight and the receipt distinguish adopted license files from preserved project licensing, including intentionally absent companion files.
- Acceptance: Existing licensing text and recorded provenance remain intact; missing companions are not silently combined with a different license system.
- Acceptance: A clean eligible project receives the reviewed LICENSE, LICENSE-CODE and LICENSE-DOCS assets with source provenance; initialization makes no relicensing or legal-compliance claim.
- Depends on: REQ-004, REQ-007, REQ-011, REQ-012

### REQ-040 - Keep initialization guidance consistent with the actual release

- Requirement: Mutable system and project guidance shall describe the new full operational default, supported routes, prerequisites, exclusions and current evidence without erasing historical records.
- Source: U01, explicit system-guide examination; U02; S01, F-06; S02, issue 10; S03, historical edition note; S04, multiple edition descriptions.
- Acceptance: The initializer entry, relevant SPECS/README guidance, depot/system-guide.md, Template guidance and setup handoff agree on the executing release and the meaning of full completion.
- Acceptance: Historical receipt editions and immutable closeouts retain their scope; superseded instructions are clearly labeled rather than presented as current defaults.
- Acceptance: Commands and recovery guidance identify how to create, first-prepare, upgrade, assess and resume one project, including runtime/content obligations and explicit exclusions.
- Depends on: REQ-001, REQ-002, REQ-007, REQ-012, REQ-013, REQ-037

### REQ-041 - Prevent recurrence of the reported integration defects

- Requirement: The shared initialization release shall include proportionate checks that detect the failure classes found in the supplied reports at their actual consumer boundaries.
- Source: S01, F-01 through F-06; S02, issues 1 through 10; G01, testing and verification discipline.
- Acceptance: Focused checks cover corpus case/path handling, whole app-owner compatibility, both collaboration integrity layers, saved-finding pagination, blank Home, unreadable Explorer inputs, stale/missing knowledge products and misreported Curator/runtime readiness.
- Acceptance: The Lessons case includes a matching finding beyond fifteen preceding document hits; direct-helper success cannot substitute for the app-owner context.
- Acceptance: Tests use controlled inputs and the smallest evidence set that detects the failures; unrelated scientific work, broad historical audits and a superseded testing campaign are not prerequisites.
- Depends on: REQ-008, REQ-009, REQ-013, REQ-020, REQ-024, REQ-025, REQ-027, REQ-032, REQ-033, REQ-036

### REQ-042 - Validate complete new and existing initialization journeys

- Requirement: The improved release shall demonstrate integrated full initialization for new, first-prepared and previously initialized project scenarios, including preservation and recoverable failure.
- Source: U01; U02; S01, future-project qualification limits; S02, reusable-package follow-up; S04, three setup cases; G01.
- Acceptance: Representative isolated projects exercise a new destination, a content-bearing existing destination and an older receipt receiving a selected upgrade, using the reviewed source-to-Template distribution.
- Acceptance: Each successful journey reaches the full required feature outcome across actual owners, selected runtimes, useful content, browser reading, native/collaboration qualification and Curator; mocks or static fixture passes alone are not end-to-end evidence.
- Acceptance: Representative interruption, changed-input, incompatible custom-package, explicit opt-out and unavailable-runtime cases preserve state and report the correct limited outcome; host/platform coverage is stated rather than inferred.
- Depends on: REQ-006, REQ-007, REQ-010, REQ-012, REQ-017, REQ-018, REQ-019, REQ-022, REQ-023, REQ-027, REQ-028, REQ-029, REQ-030, REQ-031, REQ-034, REQ-035, REQ-036, REQ-038, REQ-039, REQ-041

### REQ-043 - Deliver a source-traceable operational handoff

- Requirement: Every completed initialization shall provide a concise current handoff that maps the selected feature baseline to its actual outcome, evidence, limitations and supported next use.
- Source: S01, assessment matrix and evidence limits; S02, issue 10; S03, verification section; U02.
- Acceptance: The handoff identifies the destination, setup/base and adoption versions, requested full baseline, explicit exceptions, runtime locations, content coverage and feature-level evidence with current input versions.
- Acceptance: It states which checks were static, directly executed, observed in a browser/native runtime or reused from exact retained evidence; any required blocked/unverified item prevents an all-features-operational claim.
- Acceptance: The operational record agrees with canonical setup, Task/TRD/plan and owner receipts, gives usable launch/recovery guidance and preserves a reviewable before/after change boundary.
- Depends on: REQ-013, REQ-014, REQ-040, REQ-042

### REQ-044 - Keep assessments read-only

- Requirement: Status and assessment routes shall remain safe read-only observations even though initialization now has a full operational default.
- Source: S03, assessment and verification routes; S04, pure inspectors; S06; G01.
- Acceptance: An assessment reports current installation, configuration, owner compatibility and qualification freshness without copying assets, enabling profiles, installing dependencies, generating knowledge or creating Tasks.
- Acceptance: Unknown/customized target code is not executed merely to label the operation static or read-only; execution requires the supported trusted owner route.
- Acceptance: Assessment identifies an exact required repair or qualification step without silently performing it, upgrading an older receipt or rebuilding stale navigation.
- Depends on: REQ-004, REQ-013, REQ-014

## Decisions

- D01 — Settled by U02: full operational setup is the default outcome. The old static-only/optional-runtime default described by S03/S04 is a current-state observation that the new implementation must change. A supported required feature is not silently made optional because setup is difficult.
- D02 — Preserve authority and project ownership: full setup covers necessary Sys4AI preparation within the selected operation. Existing canonical owner gates remain binding; missing scope or runtime support produces a precise incomplete result. This document grants no execution authority.
- D03 — Existing project choices: inherited disabled starter values and historical deferment are distinct from an explicit current opt-out. The former do not narrow a newly selected full target. The latter is preserved and reported unless superseded by the current destination request; an exception does not become an all-features-operational claim.
- D04 — Source ownership: shared fixes belong in their reusable owners and reach projects through checked distribution/adoption. Differences from the Template can be legitimate reviewed local adaptations. The two evidence projects are not repair targets of this capture.
- D05 — Bounded implementation choices: exact command spelling, stage layout, compatible receipt extensions, package/module decomposition, supported local environment layout and reviewed model/dependency versions belong to implementation planning. They must satisfy this baseline, current owner contracts, reproducibility and preservation; these are not unresolved user requirements.
- D06 — Qualification scope: focused regression checks and representative integrated journeys establish the required behavior. Current applicable exact-version evidence may be reused, but stale/static evidence cannot substitute for a missing runtime or destination integration. No arbitrary content count, performance percentage or broad campaign is required.
- D07 — Legitimate empty states: a new project can have no active Tasks, learned findings or research results. Initialization must still provide usable project explanations, supported source-backed knowledge, correctly built empty products where appropriate and working capability verified with clearly separated qualification data.
- D08 — Completion layers: historical asset transactions may remain completed while a new full operational request is incomplete. Setup, runtime qualification, document approval, Task execution and publication retain distinct states.
- D09 — Source finding coverage: S01 F-01 maps to REQ-009/REQ-019; F-02 to REQ-024/REQ-025; F-03 to REQ-027; F-04 to REQ-026/REQ-033; F-05 to REQ-036/REQ-037; F-06 to REQ-014/REQ-040/REQ-043. S02 issues 1–10 map respectively to REQ-020/REQ-021, REQ-022, REQ-008/REQ-034, REQ-032, REQ-027, REQ-033, REQ-009/REQ-019, REQ-028 through REQ-031, REQ-036/REQ-037, and REQ-013/REQ-040/REQ-043. Cross-cutting verification is REQ-041/REQ-042.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
