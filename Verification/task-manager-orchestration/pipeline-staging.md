# Staged Template and initializer integration

The final staged component passes **93 checks**, including the actual copy-first role transition followed by preparation and rerun. Completed transitions are accepted with retained legacy content only when their strict receipt and current source, destination, helper, and index checks pass. The final durable [15-file manifest](./pipeline/component-manifest.json), [patch](./pipeline/implementation.patch), and [test results](./pipeline/test-results.json) supersede the earlier version below. Implementation remains in staging; live adoption is not performed by this component.

## Original 91-check snapshot (superseded)

The bounded component for PLAN-20260908-6E6F545E TASK-027 through TASK-030 is implemented and tested in staging. All 91 focused checks pass, the staged Template reports current, and actual initializer CLI runs created and prepared disposable projects successfully. Live source adoption and Template publication remain with the Project Director.

The staging root is `/Volumes/P-SSD/AngryOwl/Sys4AI/.sys4ai/task-manager-staging/pipeline/`. Its `checkout/` contains the files in repository-relative layout. All implementation writes stayed beneath that staging root; this report is the only other file written for this component.

## Reviewable delivery

- [Component manifest](./pipeline/before-transition-fix/component-manifest.json) names the exact 15 files, original and staged SHA-256 values, file modes, and patch digest. Every original hash matched the live file when the patch was prepared.
- [Implementation patch](./pipeline/before-transition-fix/implementation.patch) passed `git apply --check` against the live checkout. It was not applied there.
- [Frozen source manifest](./pipeline/before-transition-fix/source-manifest.json) records the 171 initially copied files. Copies of the original 15 component files are retained under `pipeline/baseline/`.
- [Context manifest](./pipeline/before-transition-fix/context-manifest.json) identifies 13 contextual copies, including the Project Director's workflow proposals and updated role/task tests. These files are excluded from this component's promotion patch. Their presence in the staged integration is not a publication claim.

The promotion set comprises the updater and mapping/guide; updater and watcher tests; the initializer helper, policy, receipt schema, README renderer, skill documentation, and three test files; and the reusable Template contract test. The watcher implementation is unchanged.

## Implemented behavior

The mapping places the generic and task-manager pairs in `roles/`. The updater reserves `roles/INDEX.md` for generated ownership. A static source mapping, including a case-equivalent path or a file/directory collision, cannot own that destination.

The updater loads the role validator from a frozen source snapshot and validates the intended role pairs in a disposable tree. Its generated index state entry binds the helper, SOUL, and role-file source digests. Exact index bytes are stored in the existing pending payload. Recovery recomputes the index from those frozen inputs before accepting the payload. Existing schema-1 ownership records remain readable, including the legacy role layout. Customized managed index/pair bytes remain conflicts, and an unmanaged active role directory blocks an update that would omit it from navigation.

A legacy mapped pair may retire only through its exact old-source-to-new-destination mapping. The preview includes its old path, active path, source, and old content hash. Before any retired bytes are removed, recovery material is retained under the updater's `role-layout-history/` control directory and bound in its pending record. The interruption fixture confirmed that both original pair files remain recoverable and that a repeated apply completes publication. Unrelated Template files and extra legacy content remain outside the deletion inventory.

New initialization uses receipt schema 1 with setup contract `governance-starter-v2`. It reads the schema-2 Template policy with `roles: roles`, requires valid generic and task-manager pairs, and verifies the Template index. The destination index is generated from the actual planned destination role content. Role validation uses disposable files; it does not add a role-catalog lock or transition receipt to a starter.

Existing `governance-starter-v1` receipts retain their legacy source-inventory and skipped-package rules. The tests exercised both partial recovery under the same old edition and a completed rerun after the Template changed to the new layout. Neither operation rewrote the saved role paths or adopted the new layout. A new prepare-existing request with a legacy role tree or an incompatible existing role helper stops before writes and identifies the need for explicit transition.

An existing current `roles/` collection is preserved as a whole. Missing source roles are recorded as skipped, and a missing index is generated for the retained destination pairs. An existing differing index requires explicit reindex. This policy preserves customized and incomplete role packages; index diagnostics do not make an invalid role eligible. A preserved collection that lacks a manager does not silently receive one during preparation.

The README renderer now links to `roles/` and its index. Starter scanning excludes role-transition receipts and runtime control state. Current and legacy receipt validation reject mixed layouts and unsupported contract shapes.

## Verification

All commands used the root Python 3.12 environment and `PYTHONDONTWRITEBYTECODE=1`, with the staged checkout as the working directory. The [test result record](./pipeline/before-transition-fix/test-results.json) binds each retained log by SHA-256.

| Suite | Tests | Result | Log |
| --- | ---: | --- | --- |
| Template updater | 38 | Passed | [updater-tests.log](./pipeline/before-transition-fix/updater-tests.log) |
| Filesystem watcher | 11 | Passed | [watcher-tests.log](./pipeline/before-transition-fix/watcher-tests.log) |
| Initializer and CLI recovery | 34 | Passed | [initializer-tests.log](./pipeline/before-transition-fix/initializer-tests.log) |
| Staged Template contract | 8 | Passed | [template-tests.log](./pipeline/before-transition-fix/template-tests.log) |

The tests retain existing preservation, confinement, lock, source-drift, pending-recovery, registration, and identity checks. Added cases cover generated index provenance and tampering, invalid role definitions, reserved index paths, unmanaged destination roles, legacy pair retirement with interruption, watcher source/destination boundaries, old receipt recovery, incompatible helper editions, and customized current roles. The initializer CLI test uses isolated Python with network and arbitrary command execution rejected; its permitted subprocess activity is read-only Git observation.

## Template preview and project evidence

The final [source-to-Template preview](./pipeline/before-transition-fix/source-to-template-preview.json) uses the staged component plus the declared workflow context against a copy of the unchanged live Template/state baseline. It reports 8 additions, 29 updates, 2 deletions, and no conflicts. The two deletions are the exact old generic role paths listed with their retained hashes. This is a combined integration preview; it is not a claim that all 29 updates belong to this component alone.

The simulated apply used only `pipeline/checkout/Projects/Sys4AI-Template-Project/`. Its [final result](./pipeline/before-transition-fix/final-template-result.json) reports current with 81 managed files and no pending recovery. The old pair recovery record remains in the staging checkout's updater control directory. The separate `pipeline/review-depot/` retains the original Template baseline and was used for the combined read-only preview.

Actual CLI evidence and file manifests are retained in [starter-project-evidence.json](./pipeline/before-transition-fix/starter-project-evidence.json), [fresh-project-manifest.json](./pipeline/before-transition-fix/fresh-project-manifest.json), and [prepared-project-manifest.json](./pipeline/before-transition-fix/prepared-project-manifest.json):

- `checkout/Projects/Pipeline-Fresh/` has valid generic and task-manager pairs and a current index. Its read-only Task status reports a valid empty catalog with zero Tasks and no projection drift. No live Task record, `.sys4ai` directory, or role-transition receipt was copied.
- `checkout/Projects/Pipeline-Prepared/` retains its customized README, historical role-path text, and modified generic role bytes. Its destination index is current. The pre-existing role collection remains generic-only, with the source manager explicitly skipped under the preservation policy.
- Both projects passed actual role-helper validation and repeated initializer CLI runs. Their identities remained unchanged. Read-only role and Task checks preserved file bytes.

Highest verification reached: end-to-end initializer behavior observed in disposable staged projects. This does not establish native manager activation, live root adoption, live Template publication, or host watcher readiness.

## Preserved boundaries and handoff

The live depot registry SHA-256 remained `6f3f10358eda29c89b17a0652df765cba6428427f91c9725379de16d426a72cd` during the retained project runs. Only disposable registries were mutated. The original 135-requirement role plan still matches the Project Director's baseline hash, `6eba8a8b538804a6ef5403d3133f725d35b16fa7e545d89c3ba9851691cfa8a7`. No historical plan, Task record, user configuration, live watcher, installed root skill, or unselected product project was changed by this component.

The Project Director can review the manifest and patch, reconcile the frozen contextual files with accepted source integration, and run a fresh live updater preview before any separately controlled adoption. No live publication command or canonical Task/plan mutation was performed here. The bounded staging objective and stopping condition are satisfied.

## Final recheck after transition integration fix

This section supersedes the earlier legacy-directory blocker and 91-check result. Root review correctly identified that a copy-first transition intentionally retains `sub-agent-roles/`. The initializer now accepts that retained directory when the explicit completed transition evidence validates; it does not infer completion from directory presence.

Preparation uses the role validator from the frozen Template source snapshot to check the strict transition receipt and its completed destination coverage. It verifies the receipt's project binding, the retained legacy fingerprint and bytes, active destination hashes, valid current role pairs, and a current index. It also inspects the installed role helper's active-layout and transition-function contract. This occurs during read-only preflight before starter publication. Legacy-only projects, both layouts without a receipt, pending or corrupt receipts, changed retained source bytes, and active-role collisions remain blocked.

The two added tests exercise the real role transition helper followed by initialization and rerun, plus five rejected evidence cases with byte-preservation assertions. The final results are:

| Suite | Tests | Result |
| --- | ---: | --- |
| Template updater | 38 | Passed |
| Filesystem watcher | 11 | Passed |
| Initializer and CLI recovery | 36 | Passed |
| Staged Template contract | 8 | Passed |
| Total | 93 | Passed |

The [final test record](./pipeline/test-results.json) binds the four durable logs: [updater](./pipeline/updater-tests.log), [watcher](./pipeline/watcher-tests.log), [initializer](./pipeline/initializer-tests.log), and [Template](./pipeline/template-tests.log). The final [patch](./pipeline/implementation.patch) still covers 15 files, has SHA-256 `fb281ec8acabe72332db71d0fabac52aa4aab8453395ce0ed2631b437a673599`, and passed `git apply --check` against the unchanged component baselines. The [manifest](./pipeline/component-manifest.json) records every before/after file hash.

An additional retained CLI workflow is captured in [transition-prepare-evidence.json](./pipeline/transition-prepare-evidence.json) and its [project manifest](./pipeline/transitioned-project-manifest.json). It ran `transition-preview`, confirmed `transition-apply`, `prepare-existing`, a repeated preparation, and the destination role validator against `checkout/Projects/Pipeline-Transitioned/`. Preparation and rerun completed under `governance-starter-v2`; the legacy bytes and completed transition receipt remained byte-identical, and the active role index was current. An injected pending receipt was first rejected without changing project bytes, then the original completed receipt was restored for the successful run.

The final [combined preview](./pipeline/source-to-template-preview.json) remains conflict-free with 8 additions, 29 updates, and 2 exact legacy role deletions. The [staged Template result](./pipeline/final-template-result.json) reports current. [Fresh/prepared project evidence](./pipeline/starter-project-evidence.json), the [frozen input manifest](./pipeline/source-manifest.json), and [context manifest](./pipeline/context-manifest.json) are also retained durably. Earlier evidence is explicitly archived under `pipeline/before-transition-fix/`.

All implementation remains beneath `.sys4ai/task-manager-staging/pipeline/`. Per the Project Director's follow-up, the durable patch, manifests, previews, test logs, and project evidence are additionally stored under `Verification/task-manager-orchestration/pipeline/`, so cleanup of the staging checkout does not erase the handoff record. The live registry and original historical role-plan hashes were rechecked and still match the values above. No live adoption, registry write, watcher operation, or canonical Task/plan mutation was performed. The final bounded staging objective is complete.
