# Integration implementation proposal

Candidate for the complete baseline `017e8affb9b545b845ee3a784c6db1fd4c295a977f8a14ceb1aacbc350efa2f1`, implementing PLAN-20260913-64A6385B revision 1 (`bc30f80e0a9d8cc40406149510e40520b33077607ab64190fc128f77bba0abd5`). Perspective: initializer compatibility, exact recovery and complete route acceptance. The frozen memory packet is empty. This is inspected-source design evidence, not implementation or runtime evidence. No contradiction in the accepted implementation objective requires a user decision.

## Implement the selected edition without changing historical meanings

The source helper currently selects `governance-starter-v11`; its skill metadata already says 12.0.0, so distinguish package metadata from setup edition. Add `SESSION_CONTRACT = governance-starter-v11` before changing `SETUP_CONTRACT` to v12. Preserve explicit membership in every role, memory, capture, learning, ontology, advanced, licensing and Curator edition table. Otherwise changing the current constant silently removes v11 from historical validation. Keep Curator runtime/config `module_version: 1.0.0`.

In `init_curator.py`, preserve schema-1 operation validation and frozen fields. Introduce schema-2 only for integrated operations, with integration edition, exact recipe/renderer inventories, finalized source hashes, reserved output changes, source predecessor inventories, and optional linked ontology intent/receipt. Version `module_packages`, `module_frozen`, required source resources and stage validation together; never validate an old operation against new mandatory resources. Retain original archived receipt bytes and base immutable fields.

Normalize `curator` and `project-curator` aliases before selection. `--adopt-module curator` without an earlier adoption selects integration. A completed earlier adoption remains its recorded edition until `--refresh-module curator` is explicitly selected. Extend the existing refresh source-comparison branch, which currently handles only ontology/advanced, to compare the complete selected integration inventory. Same selection verifies once; changed explicitly selected inventory appends one operation. Pending operations always win over a new selection and require their original request.

## One renderer, typed functions and inspectable governing sources

Add the declarative recipe, competency data and digest manifest under `ONTOLOGY-depo/integrations/curator/1.0.0`. Distribution uses existing reference-collection mapping. Do not add a core import or populate neutral Template graphs.

The ontology-owned renderer accepts reviewed recipe bytes, selected identity, complete finalized source bytes and existing canonical records; it returns the three reserved output byte strings and additive configuration selections. It does not import destination Python, write, install or establish authority. Stable suffixes use a reserved `curator:` family within the destination namespace. Reject collisions across all existing selected files, repeated IDs, absent locators, mismatched project roots and incomplete role pairs before producing an eligible proposal.

Model the process as a local concept/instance, its functions as core `Capability`, and the installed curate workflow as `Skill` connected by `providesCapability`. Add explicitly typed local predicates for consumes, produces, maintains, coordinatesOwner and triggeredBy. Inputs, outputs and scopes reference typed artifacts; owner declarations reference actual role pairs or governing skill sources, never a native actor. Bind every function directly to its installed operational source, so `knowledge --intent current` can find it without fallback to general guidance.

The recipe's function matrix must cover status, validate, scoped review, update, correct, retry/recovery, pause, resume, tick, session catch-up and each log-register/list/summary/query route. Ground their inputs, outputs, owner routes, scope and prerequisites in `curate/ACTIONS.md`, `references/commands.md`, `references/session-maintenance.md` and the contract's existing-owner declarations. Updating and correcting distinguish integration, memory, ontology and derived-product owners. Session collection and owner dispatch are separate functions.

Extend capability output only enough to return those typed relationships and source context. Its current `availability=available` means source freshness; expose that basis explicitly and retain `executed=false`. Authorization, configuration, compatibility, runtime, pending delivery and completed outcome require separate evidence and must not become inferred booleans. Keep bounded ambiguity, stale/missing-source and unsupported-query behavior.

## Exact ontology transaction

Implement the named integration preview/publish/recover routes beside existing publication using the same ontology lock, intents, receipts, recovery storage and guard family. Add their exact dispatch entries and adapter declaration. Ordinary publish and its grant contract remain unchanged.

The integration proposal is a distinct version-1 `integrate-curator` contract. Its four-file boundary is `ontology.yaml` plus the three planned Curator files. Configuration comparison permits only deduplicated additions to project_files, binding_files, competency_files and the recipe-required source_allowlist. Preserve ordering of existing entries and every other value, especially identity, imports, retrieval and publication. Refresh changes only files with exact earlier integration receipt ownership; unowned equal bytes do not establish overwrite authority.

Factor configuration parsing/validation into an internal data-only function, then add a narrow internal loader accepting the validated candidate config and exact reserved overrides. Keep ordinary `load_project(_overrides=...)` restricted to currently selected canonical paths. This internal path validates the whole candidate graph, source freshness and transition rules without temporarily installing candidate configuration.

Use a separate integration grant validator calling existing native observation, Director binding, manager binding and overlap checks. Bind exact proposal, preview, config predecessor, governing/source/helper hashes, current actor, expiry and four-file changes. A Director grant explicitly authorizes this operation's bounded config delta; it does not expand the persistent core binding. A manager must actually possess every selected path. Preserve orchestration-version/native-protocol distinctions. Disabled publication blocks authored-ontology integration. No legacy publish grant conversion is valid.

Persist immutable intent before writes, retaining every preimage and expected postimage. Prefer records first, configuration last to reduce incomplete new selection; this is not cross-file atomicity. A refreshed selected graph can still be temporarily inconsistent, so reads must return truthful incomplete/invalid diagnostics without repair. Recovery reconstructs predecessor and candidate using saved bytes, accepts each target only in its exact pre/post state and checks unchanged non-target inputs and current authority. In particular, after configuration commits, recovery must accept its recorded postimage while still binding the original approved predecessor; blindly reusing legacy `authorize()` would compare the wrong config hash. Third-state edits, changed recipe/helper or owner generation refuse replay. Reopen the completed receipt and canonical bytes before linking setup success.

Acquire shared Template read lock, destination setup lock, then ontology publication lock whenever nested. Current base setup acquires Template before setup, while module adoption does the reverse; reconcile that ordering on the affected route. Release Template before registry mutation as base setup already does. Never acquire a setup or Template lock from inside ontology publication.

## Complete setup routes and recoverable holds

Finalize identity, governance changes, owner package bytes, Curator session choice and role index before rendering bindings. `asset_plan()` currently finalizes `Roles/INDEX.md` after `source_snapshot()`, so rendering only in the earlier snapshot is insufficient. Render against the final selected/preserved byte view; rerun must reproduce exactly the frozen outputs.

For absent/pristine ontology, use the existing setup owner transaction. Preserve neutral recipe/source hashes separately from generated destination hashes in version-discriminated receipt provenance. Account for generated outputs explicitly in bidirectional owned-file validation; do not invent Template source files containing destination facts. No ontology publication receipt or persistent grant is fabricated for this initial installation.

For compatible authored ontology, preserve the blanket package protection except the explicitly selected integration outputs/config delta. After required owner capability bytes settle, invoke the integration owner within the same setup/adoption workflow and link its immutable receipt. Accept explicit proposal/grant references for that owner call, and retain an exact authorization hold when absent or stale. The supported continuation is rerunning this selected setup with current owner inputs, not manual graph edits. A preflight can freeze final expected source bytes; native grants must be current when publication occurs.

Missing baseline ontology can be installed as a neutral prerequisite in schema-2 adoption. Custom/incomplete packages, contradictory identity, legacy role layout, reserved IDs or disabled required publication produce exact diagnostics. Session-off and capture-off are compatible retained choices; publication-off blocks an authored write, but does not prevent already installed read-only integration from being statically valid.

`init_static_health` must select assessment by saved base/operation edition. Earlier receipts must not acquire new semantic requirements or new package pins merely because the helper advanced. Integrated assessment uses reviewed source-side pure validation and never runs unknown destination code. It requires every expected capability, relationship, owner source, config selection and source digest. File installation or one Curator label fails. Required failure keeps partial verification/nonzero exit; preserved incompatibility remains explicitly degraded. Static success never certifies live execution.

## Verification and complete plan coverage

| Plan work | Required performed evidence |
| --- | --- |
| TASK-001–002 | Reopen frozen scope/preservation manifest; create exact function and transaction matrix. |
| TASK-003–005 | Two-identity deterministic renderer, complete typed competencies, collision/locator/ambiguity/stale-source controls, legacy publication compatibility and read nonmutation. |
| TASK-006–011 | Versioned receipt tests; complete create, first-empty and authored preparation, manual Template copy, missing-baseline adoption, old Curator refresh and integrated refresh. Validate old v1–v11 receipts, v1/v2 transition refusal, opt-outs and source-change refusal. |
| TASK-012–013 | Template check/apply/check and neutral inventory; actual disposable CLI routes with reopened receipts and each destination's full query matrix. Classify reconstructed historical fixtures accurately. |
| TASK-014–016 | Exact root capability manifest, affected guard recertification, root-owner integration receipt, explicit compile/wiki/memory-link maintenance and current health. Preserve active root initializer v9 and Task intake. |
| TASK-017–018 | Actual root session changed-input collection, admission, dispatch and one attributable owner result; consume only completed deliveries. Record each dated pending obligation's current disposition or precise owner blocker. |
| TASK-019–021 | Historical Task owner investigation without inferred cleanup; authorized temporary browser read/navigation with safe shutdown/token handling; fresh memory search and ontology/selected backend health. |
| TASK-022–023 | All 14 requirements and 34 clauses mapped to exact current evidence and verification level; final protected inventory and truthful report. Frozen plan revision remains unchanged per manager handoff. |

Fault injection must cover intent, each canonical/config replacement, owner receipt, setup receipt linkage, registration and verification. Retry twice without duplicate records/registrations; reject source/target/identity/opt-out changes, unknown files, symlink/hardlink aliases and overlapping writers. Do not weaken guards or refresh historical inventories to pass.

Root authority may be performed by the live bound host Director only after current overlap checks and observed worker stopping, as the manager clarified. Existing validators remain controlling. Manager-provided fresh observations identify already-stale compile/wiki/memory links and the preserved historical staged response; treat these as baseline findings, not introduced regressions or cleanup permission. Final evidence must refresh after the last source change. Memory capture with unresolved independent ownership remains pending, without overlapping writes.

## Inspected source versions

SHA256 values for principal implementation inputs:

- `SKILLS-depo/init-new-project/scripts/init_new_project.py`: `7801def2e6585e4f9f42cb0b5c129c52dd343456c4e2ec37f744fb7e2194b100`
- `SKILLS-depo/init-new-project/scripts/init_curator.py`: `ad1480038d09ceea4d5eaaea75d64667f3691e54f70233e503aa37c843e0adfc`
- `SKILLS-depo/init-new-project/scripts/init_static_health.py`: `4a975e000e72ea52b995b7d027655e615613cfba593146ea8573ad2a688b2eb9`
- `SKILLS-depo/ontology/scripts/ontology_publication.py`: `e9d8a2520807a4598a11890ddc9e6d470eeaa6611d6e67f6847aed3220a4b936`
- `SKILLS-depo/ontology/scripts/ontology_authority.py`: `c5eda42e85d5b3d02d2950e958c59ee52dfa58837580b19146a3b9f7adee289a`
- `SKILLS-depo/ontology/scripts/ontology_core.py`: `15336a6fbb542cb8abccf6db8cd4227fc846758f60868ef9e3782580ea18be1d`
- `SKILLS-depo/ontology/scripts/ontology_knowledge.py`: `feb9d2c2e5f7570db49d3d07c3961ee2f38c1ee629f3a135915ea003645c0d55`

Paired-role reads: `Roles/project-sub-agent/AGENTS.md` SHA256 `7d064ae5d5954af65fc1a83b2ce1c69562d5c31f085e70ac92c3ad0bf2e7eec2`; `Roles/project-sub-agent/ROLE.md` SHA256 `4c3ac5415030ab770d9af7b73fc773da43d07b041889c77a8755974284c874e2`. SOUL SHA256 `3aa4841fa9f2dc177beabaebd341368d797d224cce3bb18b3fd494f34fa473b2`.

Only this candidate artifact was written. No production mutation, test execution, owner action, browser session or publication was performed by this solver. Stop condition reached.
