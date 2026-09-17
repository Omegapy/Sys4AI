# Curator integration implementation proposal

Candidate for integration baseline `017e8affb9b545b845ee3a784c6db1fd4c295a977f8a14ceb1aacbc350efa2f1`, plan `PLAN-20260913-64A6385B` revision 1, SHA256 `bc30f80e0a9d8cc40406149510e40520b33077607ab64190fc128f77bba0abd5`. Perspective: ontology types, current sources, and owner publication integrity. Inspection only; no production code or canonical state changed. The supplied memory packet is empty. No sibling candidate was read.

## 1. Semantic contract and neutral recipe

Implement the plan's `ONTOLOGY-depo/integrations/curator/1.0.0/` recipe, locators, manifest, and competencies, mapped as reference assets. Keep core 1.0.0 and trusted context unchanged. Use a pure `ontology_curator.py` renderer accepting identity, reviewed recipe bytes, final selected source bytes, and the existing canonical inventory. It returns the three reserved outputs and exact required config additions. It must neither execute destination code nor read ambient identity, mutate files, mint authority, or use runtime evidence.

Use reserved `curator-` suffixes within the destination namespace: `curator-process`, `curator-skill`, `curator-function-<action>`, `curator-owner-<route>`, `curator-source-<key>`, `curator-scope-<key>`, and deterministic relation/binding IDs. The process can be a Capability describing coordination; its skill instance is a Skill. Functional capabilities use core Capability. Owner definitions are Role instances supported by actual paired role sources; public owner routes are Skill instances. Never type a persisted role definition as a currently running TaskManager. Require both role files in the locator map, and validate their presence and identity before rendering.

Use core `providesCapability` from the installed Curator Skill to every function. Core `produces` has domain Skill/Task, so do not apply it to Capability. Add destination predicates with explicit domains/ranges: consumes/produces (Capability → Artifact), maintains (Capability → Artifact/Scope), coordinatesOwner (Capability → Skill/Role), triggeredBy (Capability → Artifact), and requiresPrerequisite (Capability → Artifact/Scope/Authority). Give these predicates cardinality min 0/max null: the current validator applies cardinality to all matching domain instances, including unrelated existing capabilities. Enforce required Curator edges with its competency specification, not global minimum cardinalities. Use core `requiresAuthority`, `definedBy`, and `relatedTo` where their actual domains fit.

Each function has direct current-source references and these parallel contracts:

| Function | Input → output | Owner / prerequisite |
| --- | --- | --- |
| status, validate | selected policy → bounded diagnostics | curate policy reader; selected root |
| review | scoped source/metadata → findings | review route; selected scope/current source |
| update, correct | exact reviewed candidate → owner result | fixed integration, memory, ontology or derived-product route; that owner's grant |
| retry | original operation/journal → recovery result | original owner recovery pair; matching pre/post bytes |
| pause, resume | current Task binding → reconciled transition | agent-task; current manager and native stopping evidence |
| tick | selected work/budget observation → admitted dispatch/result | live application or supported Broker; current actor |
| session catch-up | changed input → retained delivery | collector first, subsequent current-owner evaluation; enabled session and remaining budget |
| log-register/list/summary/query | exact handle/filter → bounded result | registered log protocol; full logs preserved |

Source these statements primarily from installed `curate/ACTIONS.md`, `references/commands.md`, `references/session-maintenance.md`, corresponding public owner contracts, charter, current config, and role pairs. Model inputs, outputs, scope and prerequisites as declared artifact categories, never invented Task instances or receipts. Bind project identity through its actual existing identity source: generic project.json or depot root inventory/config. Do not require project.json at the depot root. Reject unresolved locators, duplicate IDs, reserved-path conflicts, unsafe source names, missing roles and unsupported functions before writing.

Keep recipe outputs compact. Existing `capability()` expands Skill/providesCapability and `explain()` already exposes relationships and bindings. Extend only capability response metadata needed to label declaration/source freshness separately from installed/configured/authorized/runtime state; avoid treating its current `availability: available` as operational availability. Stable per-function queries and source-current queries must work within 32,000 bytes. Use existing competency question format (`expected_ids`, `expected_relations`, `expected_sources`, `expected_terms`) and test overview truncation explicitly.

## 2. Exact integration owner transaction

Add `integration_preview`, `integration_publish`, and `integration_recover` public wrappers in `ontology_publication.py`; place their implementation in the dedicated integration module. Keeping wrappers in the current provider avoids an unnecessary new guard family. Legacy publish/check_proposal/authorize schemas remain exact and unchanged.

Define a separately named schema-1 `integrate-curator` proposal. Bind operation ID, reason, recipe edition/hash inventory, renderer/helper inventory, original config hash, protected authored inventory, exact selection, and four changes: ontology.yaml plus `ONTOLOGY/modules/project/curator.jsonld`, `ONTOLOGY/bindings/curator.jsonld`, `ONTOLOGY/modules/project/curator-competency.json`. Every change carries expected/content/post hash. New integration paths must be absent, or exactly owned by the selected previous completed integration receipt. Mere equality grants no refresh authority.

Config must equal the predecessor except additive, duplicate-free selections in project_files/binding_files/competency_files and the exact recipe-needed source_allowlist. Preserve all previous ordering and values; append new selections deterministically. Do not alter project identity, context, imports, retrieval, publication binding/scope/enabled, or advanced profiles. Finalize candidate config before computing any source hash that could depend on it; preferably cite governing/config inputs already outside this four-file transaction to avoid self-referential hashes.

Refactor pure config validation from disk acquisition internally. A narrow integration-only candidate loader validates the candidate config together with graph bytes; ordinary `load_project(_overrides=...)` still rejects config and unselected paths. Candidate validation includes the complete authored graph, collisions, lifecycle and current sources. Preview must not stage files or repair products. Reject stale unrelated source bindings rather than hiding them through replacement config.

A distinct exact integration grant binds contract/version, project, actor/kind, operation, payload/preview/config predecessor hashes, governing references, all four exact changed paths and pre/post hashes, native receipt, observation/expiry, and current Task binding when applicable. Reuse `validate_native_observation`, `validate_director_binding`, `validate_manager_binding` and overlapping-manager inspection without weakening them. The grant explicitly authorizes the restricted config addition; never translate a legacy publish grant into this grant. Publication-disabled authored installations remain held. Manager orchestration-version rules retain their existing protected-native requirements.

The execution manager reports that its reservation owns manager artifacts only. Therefore eventual root canonical publication must be invoked by the actual `/root` Director with its current bound hashes and real fresh roster, after verifying no overlapping owner. The implementer prepares exact bytes; it cannot claim to be the publisher. Do not widen the manager validator to work around this division.

Use the existing ontology publication lock, immutable intent/receipt/recovery directories, canonical encoding, safe-path/atomic-write primitives, and bounded intent size. Retain all original preimages. Write graph/binding/competency first and config last, then compile and write completion receipt. This minimizes incomplete selections but does not promise atomicity across files: refresh can expose mixed pre/post content. Readers must report a partial integration when its exact current intent is incomplete; they must not repair it.

Recovery reconstructs original config and graph context from the immutable intent. It accepts only original pre/post hashes, the original recipe/helpers/selection, current owner grant, unchanged external sources/protected inventory, and the exact original payload/preview. Grant config hash refers to the retained predecessor; separately require the actual config to be its recognized pre/post state. A completed receipt only verifies current bytes and never overwrites later edits. Guard rechecks must recognize the same original pre/post transition rather than rejecting the transaction's own config replacement or accepting unrelated drift.

Register the three operations in the existing ontology action contract, declared adapters and `_direct_facts`; classify ontology.yaml as an ontology target only for this validated restricted operation. Guard ownership alone supplies no grant. Enabled guards remain enabled; refresh exact bound adapter/contract/bootstrap evidence through supported repair and recertify affected standards inputs. Retain the 128 MiB bound.

## 3. Initializer, adoption and recovery

Implement governance-starter-v12 with integration edition `curator-ontology-1.0.0`; retain Curator runtime/config 1.0.0. Update all membership tables, complete resource inventories, trusted static pins, baseline assets and version-discriminated receipt schema together. Existing v1-v11 base provenance and schema-1 module validators retain their meanings. Root installed initializer v9 remains untouched.

Create/pristine first preparation renders only after final destination identity, governance, role index and owner-source bytes settle. Include the three outputs/config in the existing setup manifest, with neutral source hashes separate from rendered destination hashes. Initial absent/pristine ontology uses setup authority and records no live publication. Nonempty custom ontology never enters that shortcut.

For authored first preparation and historical adoption, add a schema-2 project-curator module operation containing integration edition, exact recipe/source/target inventories, protected inputs, and linked ontology operation/receipt. Adopt compatible packages only under existing whole-package rules. Missing baseline ontology may be an explicitly recorded neutral prerequisite; partial/custom prerequisites cause a named hold. Add `--refresh-module curator` and project-curator alias. Ordinary completed adoption verifies its historical selection; explicit refresh selects current source inventory and archives prior receipt bytes. Preserve the original base receipt fields and history.

Provide a trusted caller owner callback and an optional exact grant-file CLI input for authored publication. The initializer itself prepares/persists the exact preview, invokes the selected owner API, and links/reopens its receipt; unavailable authority returns a resumable held operation with preview and required owner action. A fresh grant may resume the original frozen operation. Never require manual graph/config editing, invent an actor, persist a grant as standing authority, or report setup completion before owner completion and semantic readiness.

Use lock order Template shared read → destination setup → ontology publication. Release ontology publication before factual registry locking. Never call setup from the ontology publisher. New v2 paths must avoid the existing module route's inverse setup→Template acquisition. Persist checkpoints inside existing setup history: assets, ontology integration pending/complete, receipt linkage, registration where applicable, verification. Every retry checks original request/source inventory, protected identity/preferences, recognized pre/post targets and owner generation. Expired grants require renewal, never expiry reset.

Static readiness must validate neutral resource closure separately from destination integration. Selected v12/integrated setup fails for missing graph selection, any missing function/edge/source binding, identity mismatch or unknown incompatible code. Parse only reviewed source interfaces; never execute arbitrary destination Python. Disabled compatible choices remain disabled; authorization and runtime stay false/not-exercised in static results. Preserve degraded base preparation behavior where existing custom capability prevents integrated success, with nonzero result and exact diagnosis.

## 4. Integration and evidence sequence

Plan tasks 001–002 freeze current manifests/owner selection and accept this exact contract. Tasks 003–005 implement semantics/transaction/query controls; 006–011 implement editioned setup and stage fault recovery. Tasks 012–013 distribute only through checked Template update and exercise actual disposable create, authored first preparation, pristine manual copy, prior setup without Curator, prior Curator without semantics, and already-integrated refresh. Keep neutral graphs empty, identity null, publication unbound, session disabled, no runtime/history. Prove original-edition ordinary reruns, disabled settings, custom conflicts, legacy-role refusal and duplicate-free retry.

For tasks 014–016, adopt an exact minimal root helper/resource manifest. Existing root graph binds ontology SKILL.md, SPECS.md, AGENTS.md and ROLE.md: preserve those bytes when unnecessary changes would create unrelated stale bindings outside the three reserved files. The present CURATOR.md incorrectly assumes project.json and describes installation as wholly inactive; correct that charter narrowly to name depot identity fallback and enabled bounded session collection. Existing root AGENTS already carries the session checkpoint. If another bound governing source truly must change, return the precise required rebind scope to the manager rather than silently widening publication. Publish with current Director evidence, then refresh compile/wiki/memory links and affected selected certifications after final source bytes settle.

Tasks 017–021 need actual evidence: one enabled bounded session checkpoint with separate collection/admission/dispatch/completed-owner receipt; current pending-delivery disposition; historical cancelled Task staged-artifact hash, transaction and native-owner reconciliation; actual on-demand workbench navigation and safe shutdown with token excluded; current bounded memory retrieval and ontology health. Pending or historical work may remain preserved with exact owner/blocker/next action where the plan permits it. Dispatch never consumes delivery. No fictitious Task or service is needed to manufacture native evidence.

For 022–023, map all 34 clauses to current evidence and owner, distinguish fixtures/static/actual owner/browser/end-to-end setup, compare protected inventories after the final change, and record every unexercised limit. Guard/publication fixtures must cover both Director and confirmed manager, stale/disabled/overlapping owners, forbidden config edits, every four-file/projection/receipt fault, changed source/target/selection, symlink/hardlink and repeated recovery. Query tests hash files/timestamps before and after reads. No Git publication, unselected child adoption, dependencies or background service are implied.

No contradiction in the accepted plan requires redesign. Implementation must preserve the exact current-owner split and source-freshness boundaries described above.

## Inspected source bindings

| Source | SHA256 |
| --- | --- |
| SOUL.md | 3aa4841fa9f2dc177beabaebd341368d797d224cce3bb18b3fd494f34fa473b2 |
| Roles/project-sub-agent/AGENTS.md | 7d064ae5d5954af65fc1a83b2ce1c69562d5c31f085e70ac92c3ad0bf2e7eec2 |
| Roles/project-sub-agent/ROLE.md | 4c3ac5415030ab770d9af7b73fc773da43d07b041889c77a8755974284c874e2 |
| SKILLS-depo/ontology/scripts/ontology_core.py | 15336a6fbb542cb8abccf6db8cd4227fc846758f60868ef9e3782580ea18be1d |
| SKILLS-depo/ontology/scripts/ontology_publication.py | e9d8a2520807a4598a11890ddc9e6d470eeaa6611d6e67f6847aed3220a4b936 |
| SKILLS-depo/ontology/scripts/ontology_authority.py | c5eda42e85d5b3d02d2950e958c59ee52dfa58837580b19146a3b9f7adee289a |
| SKILLS-depo/ontology/scripts/ontology_guards.py | a9213263d5163877596a7c4ece9b67db418bf8886ae0f785b101bebaaccfab7d |
| SKILLS-depo/ontology/scripts/ontology_knowledge.py | feb9d2c2e5f7570db49d3d07c3961ee2f38c1ee629f3a135915ea003645c0d55 |
| SKILLS-depo/init-new-project/scripts/init_curator.py | ad1480038d09ceea4d5eaaea75d64667f3691e54f70233e503aa37c843e0adfc |
| SKILLS-depo/init-new-project/scripts/init_new_project.py | 7801def2e6585e4f9f42cb0b5c129c52dd343456c4e2ec37f744fb7e2194b100 |
| .agents/skills/curate/ACTIONS.md | 3ae676c3f350e92ab25ab8a02776f11b946ecea3ba9785b882ffae8ef3e97dc5 |
| .agents/skills/curate/references/session-maintenance.md | c06a23c871c7c388e7d7f7c5939f282c134ef248442566a9d2aa3c39efb7055c |
