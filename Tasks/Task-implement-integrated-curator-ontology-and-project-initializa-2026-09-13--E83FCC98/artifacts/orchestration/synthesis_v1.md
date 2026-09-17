# Integrated implementation proposal

This synthesis preserves PLAN-20260913-64A6385B revision 1, all 23 tasks and all 34 acceptance clauses. The plan and its coverage remain normative; this proposal fixes implementation choices without changing scope or claiming performed implementation.

Exact inputs, verified unchanged:

- Baseline: `017e8affb9b545b845ee3a784c6db1fd4c295a977f8a14ceb1aacbc350efa2f1`.
- `plan.json`: `bc30f80e0a9d8cc40406149510e40520b33077607ab64190fc128f77bba0abd5`.
- `candidate_a_v1.md`: `83d3c3e7c3ff6c40313c5fe2712422525e8e45326717de34c4d90240945beb69`.
- `candidate_b_v1.md`: `732bc5c207957f8498716814964f0cd5219c1bbd4d1c706c1889b4146072c43d`.

## Decisions and candidate dispositions

Retain A's detailed ontology domains, paired-role provenance, source-current query distinctions, four-file grant boundary and original-predecessor recovery. Retain B's edition tables, schema-discriminated inventories, final role-index timing, generated-output provenance, complete setup routes and fault boundaries. Their shared authority and preservation requirements remain mandatory.

The naming difference is terminology: choose A's reserved `curator-` suffix family within `urn:sys4ai:ontology:project:<id>:`. Both colon and hyphen satisfy `ontology_core.ID_RE`; using one family avoids duplicate identities. Omit B's alternative `curator:` spelling.

The process-type alternatives are compatible scope choices. Select a `kind: instance` with core `Capability`, describing the coordination ability, plus a distinct installed `Skill` instance. Functions are Capability instances. Omit an additional process concept: core Capability already means a described ability, and `providesCapability` explicitly accepts Skill → Capability. Actual persisted owners are Role instances with paired sources; none is typed as a live TaskManager. No imported core or context changes are needed.

Use the plan's `ontology_integration.py` for the pure renderer and bounded integration implementation, with public wrappers in `ontology_publication.py`. A's separate `ontology_curator.py` name adds no required behavior. The candidates contain no evidence disagreement or irreconcilable exclusive commitment. Root publication uses the actual bound host `/root`, after the implementation worker stops and current overlap checks pass. Preserve the existing manager-scope validator exactly.

## Semantic and query contract

Store recipe, locators, competencies and digest manifest under `ONTOLOGY-depo/integrations/curator/1.0.0/`; distribute through existing reference mappings. The pure renderer receives reviewed recipe bytes, selected identity, finalized source bytes and canonical inventory. It returns three reserved files plus exact config additions. It performs no writes, destination-code execution or authority inference.

Use `curator-process`, `curator-skill`, `curator-function-<action>`, `curator-owner-<route>`, `curator-source-<key>`, `curator-scope-<key>` and deterministic relationship/binding suffixes. Reject cross-file collisions, duplicate records, unresolved/unsafe locators, identity mismatch and incomplete role pairs. Generic identity comes from project.json; the depot uses its existing registry/configuration identity.

Connect the Skill to every function with core `providesCapability`. Define local predicates: consumes/produces, Capability → Artifact; maintains, Capability → Artifact/Scope; coordinatesOwner, Capability → Skill/Role; triggeredBy, Capability → Artifact; requiresPrerequisite, Capability → Artifact/Scope/Authority. Set cardinality minimum 0, maximum null, because validation applies domains to unrelated existing records. Enforce mandatory Curator edges through competencies. Core `produces` cannot describe a Capability's output because its domain is Skill/Task. Artifact categories describe possible inputs/results, never invented receipts or Task instances.

Every function has direct current-source bindings and an observable competency covering its meaning, inputs, outputs, owner, scope and prerequisites. Include status, validate, scoped review, update, correct, exact retry/recovery, Task pause/resume, selected tick, session catch-up, log-register, log-list, log-summary and log-query. Keep session collection distinct from owner evaluation/dispatch. Route updates through their actual integration, memory, ontology or derived-product owner. Bind curate ACTIONS, commands, session maintenance, charter/configuration and applicable public owner contracts after all destination bytes settle.

Extend capability output only as necessary. Label availability's source-freshness basis and `executed: false`; keep declared, installed, configured, compatible, authorized, runtime-observed, pending and completed states distinct. Preserve bounded ambiguity, unsupported-query, stale/missing-source and truncation diagnostics within 32,000 bytes. Queries never repair products.

## Four-file owner transaction

Provide `integration_preview(root, selection)`, `integration_publish(root, proposal, grant, expected_preview_sha256)` and `integration_recover(root, operation_id, grant)`, with explicit CLI routes and existing-family guard adapters.

The separately named schema-1 `integrate-curator` contract changes only `ontology.yaml`, `ONTOLOGY/modules/project/curator.jsonld`, `ONTOLOGY/bindings/curator.jsonld` and `ONTOLOGY/modules/project/curator-competency.json`. Permit deterministic deduplicated additions to project_files, binding_files, competency_files and recipe-required source_allowlist only. Preserve existing order and all identity, imports, retrieval, profiles and publication values. Refresh requires exact earlier completed integration receipt ownership; equal unowned bytes do not grant overwrite authority.

Factor data-only config validation into a narrow internal candidate loader. Validate the complete authored graph and current sources in memory. Ordinary load_project overrides and legacy publication/grants keep their exact boundaries. Avoid self-referential source hashes inside the four-file change.

The distinct integration grant binds actor, current native observation/expiry, governing hashes, proposal/preview, original config hash, recipe/helper/source inventories, operation identity and all exact pre/post targets. Reuse current Director, manager, overlap and native validators. Disabled authored publication remains a hold. Never translate a legacy grant or enlarge persistent binding scope. Guard ownership supplies no authority; preserve enabled enforcement and the 128 MiB bound.

Persist immutable intent and all preimages before replacing graph, bindings, competencies, then config. Compile and write the completion receipt through existing owner storage. Cross-file atomicity is not promised; reads diagnose incomplete/invalid intermediate selection without repairing it. Recovery reconstructs original and candidate contexts from saved bytes, accepts only exact pre/post targets and unchanged protected inputs/helpers/selection, and requires current authority. Its grant binds the approved predecessor even when live config is the recognized postimage. Third-state edits refuse replay. Completed receipts verify current bytes without overwriting later edits.

Use lock order Template shared read → destination setup → ontology publication. Reconcile the existing module route's inverse order. Release Template before registry mutation; never acquire setup/Template locks inside ontology publication.

## Editioned setup and adoption

Implement governance-starter-v12 and curator-ontology-1.0.0; retain Curator module_version 1.0.0. Name historical session v11 explicitly before changing the current constant. Preserve v1-v11 membership in every applicable role, licensing, memory, capture, learning, ontology, advanced and Curator table. Update resource inventories, trusted pins, baseline assets, operation validators and receipt schema together. Schema-1 operations retain their frozen resources; integrated operations use schema 2. Preserve archived receipts and original base provenance.

Render create/pristine preparation after identity, governance, session choice, owner packages and Roles/INDEX.md are finalized. Record neutral source hashes separately from generated destination hashes and account for generated files bidirectionally. Absent/pristine ontology uses the existing setup transaction and claims no live publication or persistent grant.

Compatible authored preparation/adoption preserves whole packages outside exact selected integration changes. The initializer prepares the exact preview, invokes its trusted owner callback or supplied exact proposal/grant CLI references, links and reopens the immutable owner receipt, then verifies semantics. Missing/stale authority creates a resumable hold; continuation is the same selected setup request with current owner inputs, never manual graph edits.

Normalize curator/project-curator aliases. First adoption selects integration; an earlier completed adoption stays its recorded edition until explicit `--refresh-module curator`. Compare the complete selected inventory; unchanged selection verifies, changed explicit selection appends one operation. Pending work requires its original selection. Missing baseline ontology may be a recorded neutral prerequisite. Custom/incomplete packages, identity/path collisions and legacy role conflicts remain preserved diagnostic holds.

Static assessment follows the saved base/operation edition, uses reviewed pure parsing without unknown destination Python, and requires resource closure, identity, graph selection, every function/edge/binding and current source digest. Missing semantic integration cannot pass on file installation. Preserve session-off/capture-off; publication-off prevents authored writes but does not invalidate compatible installed reads. Required failure remains partial/nonzero; preserved incompatibility remains explicitly degraded. Static success never certifies execution.

## Coverage, verification and delivery

Every clause below retains its exact plan wording and acceptance strength. Implement the following complete evidence sequence; clause ranges denote every numbered acceptance criterion within that requirement.

| Requirement clauses | Plan tasks and required evidence |
| --- | --- |
| REQ-001.1–2 | 001–002, 014–015, 017: exact root identity/wiring and attributable current-owner operation. |
| REQ-002.1–2 | 003–005, 012–015: complete function queries, owners, contracts and coordination distinction. |
| REQ-003.1–3 | 003–005, 008, 016, 021: typed queries, distinct readiness, current projections/links. |
| REQ-004.1–3 | 003, 006–007, 009–010, 012: source closure and Template check/apply/check; empty neutral graphs, null identity, unbound authority, disabled session. |
| REQ-005.1–2 | 004, 006–007, 010–011, 013: actual disposable create and reopened destination queries/receipt. |
| REQ-006.1–2 | 004, 006–008, 010–011, 013: actual first preparation, authored ontology and manual Template copy; preservation/conflict controls. |
| REQ-007.1–3 | 004, 006, 009–011, 013: prior setup without Curator, earlier Curator without semantics, integrated refresh and ordinary historical reruns. |
| REQ-008.1–3 | 001, 004, 006–016, 019, 021: exact inventories, opt-outs, receipt ownership, fault/recovery controls. |
| REQ-009.1–3 | 005, 007–009, 011, 013–015, 017–018: actual bounded collection/admission/dispatch/result; no invented actors, services or second writer. |
| REQ-010.1–2 | 018: fresh disposition for every relevant dated delivery; consume only completed owner outcomes. |
| REQ-011.1–2 | 019: cancelled TASK-20260910-7F1A11AE artifact/hash, transaction, status and native-owner reconciliation; supported disposition or precise preserved blocker. |
| REQ-012.1–2 | 020: actual temporary workbench read/navigation and safe shutdown; exclude token/private fragment. |
| REQ-013.1–2 | 014, 016, 021: actual bounded memory retrieval and current ontology/backend health; independent data/settings preserved. |
| REQ-014.1–3 | 010, 012–013, 016–023: all route results, final scope/hash/owner audit and truthful verification levels. |

Test both Director and confirmed-manager grants, stale/disabled/overlapping authority, forbidden config changes, each intent/target/projection/owner-receipt/setup-link/registration/verification fault, changed inputs, symlink/hardlink aliases and twice-repeated recovery without duplicates. Hash read targets and timestamps to establish nonmutation. Classify reconstructed historical fixtures separately from actual CLI routes.

For root adoption, manifest minimal helper/resources and necessary CURATOR.md corrections for depot identity and enabled bounded session collection. Preserve root initializer v9, Task intake and unnecessarily unchanged bound guidance. A required additional governing-source rebind returns to the manager with exact scope. Repair affected guards and selected certifications through their supported routes after final source bytes; refresh compile/wiki/semantic/memory-link products in their actual dependency order. The manager reports these products already stale, while canonical validity and standards/inference/guard probes pass: preserve that baseline distinction and obtain final fresh evidence.

## Assumptions, risks and stopping

The current authority permits only the selected local implementation, neutral Template distribution, exact root adoption, disposable validation and temporary workbench observation. No unselected products, dependency installation, Git publication, external messages or unattended service. Existing independent memory ownership remains a pending capture boundary until reconciled. Source drift, unavailable owner capability, stale grants and interrupted cross-file state remain explicit holds, never lowered acceptance criteria.

Unresolved synthesis conflicts: **empty**. Implementation and runtime checks remain to be performed by their assigned owners.

Inspection verification: all eight delegation context hashes matched; all 321 preservation-baseline hashes matched. Core 1.0.0 type definitions and validator domains/cardinality directly support the selected representation. Core SHA256: `b9b3bb90f8db47110588c02c99c8b4bedab62c1b4be9f533572aa3a6362e4f43`. Paired-role reads: AGENTS `7d064ae5d5954af65fc1a83b2ce1c69562d5c31f085e70ac92c3ad0bf2e7eec2`; ROLE `4c3ac5415030ab770d9af7b73fc773da43d07b041889c77a8755974284c874e2`; SOUL `3aa4841fa9f2dc177beabaebd341368d797d224cce3bb18b3fd494f34fa473b2`. The frozen memory packet is empty. Only this result artifact was written. Synthesis stopping condition reached.
