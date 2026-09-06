# Sys4AI synchronization removal implementation plan

## Document control

| Field | Value |
| --- | --- |
| Status | Complete and verified |
| Authorized | 2026-08-29 user request |
| Requirements | `Requirements/sys4ai_synchronization_removal_requirements.md` |
| Project root | `/Volumes/P-SSD/AngryOwl/Sys4AI` |

## Outcome

Retire the complete Sys4AI synchronization capability. The finished workspace
will have no synchronization skill, copy engine, source-to-target manifest,
dependent test or operating process, or active instruction that expects shared
content to propagate. Reusable source collections and active project-local
copies will remain, but neither will automatically control the other.

## Baseline evidence

- No `.agents/skills/sys4ai-project-sync/` package exists.
- `tools/depot_sync.py` is the live Python copy engine.
- `depot/manifest.json` defines 14 source-to-target artifacts.
- `tests/test_depot_sync.py` directly tests the engine.
- `tests/test_repository_contract.py` loads the manifest and executes the
  engine.
- Root and template documentation and governance contain active
  synchronization instructions.
- The root and depot-source copies of `AGENTS.md` and `ROLE.md` are
  byte-identical before removal.
- The two files under `depot/contracts/` are byte-identical to the retained
  root implementation-plan copies.
- The baseline root test run contains 22 tests: the 11 engine unit tests pass,
  while the repository suite has three failures and two errors caused by stale
  path, TRD-state, removed-collection, and manifest assumptions.
- The initial worktree contains unrelated untracked implementation-plan, skill,
  TRD, and verification paths. They are protected.

## Decisions and boundaries

1. The phrase "synchronization skill" covers the underlying active copy system
   because the planned root skill wrapper was never installed.
2. Delete artifacts whose sole current purpose is synchronization.
3. Rewrite shared active documents that also carry independent project
   governance.
4. Preserve source catalogs and project-local copies as independent assets.
5. Preserve `depot/projects.json` as inventory only and correct its stale path.
6. Do not build a replacement updater, installer, copy script, or migration
   layer.
7. Do not commit, push, publish, deploy, or mutate the project Task ledger.

## Exact change map

### Delete

| Path | Reason | Requirement |
| --- | --- | --- |
| `tools/depot_sync.py` | Executable copy engine | REM-002 |
| `tools/__pycache__/depot_sync.cpython-312.pyc` | Ignored compiled engine remnant observed during final filename audit | REM-002 |
| `tests/test_depot_sync.py` | Tests only the removed engine | REM-004 |
| `tests/__pycache__/test_depot_sync.cpython-312.pyc` | Ignored compiled direct-test remnant observed during final filename audit | REM-004 |
| `depot/manifest.json` | Source-to-target authority map | REM-003 |
| `Requirements/sys4ai_skills_soul_sync_requirements.md` | Synchronization-only specification | REM-005 |
| `Implementation_Plans/sys4ai_skills_soul_sync_implementation_plan.md` | Synchronization-only plan | REM-005 |
| `Requirements/sys4ai_depot_requirements.md` | Active initial requirements embed synchronization as a core feature; replaced by the removal requirements | REM-005 |
| `Implementation_Plans/sys4ai_depot_implementation_plan.md` | Active initial plan embeds the removed engine and manifest; replaced by this plan | REM-005 |
| `Verification/sys4ai_depot_verification.md` | Verification record asserts the retired control plane | REM-005 |
| `depot/contracts/subagent_role_system_implementation_plan.md` | Exact duplicate used as a manifest source | REM-005 |
| `depot/contracts/task_system_implementation_plan.md` | Exact duplicate used as a manifest source | REM-005 |
| `AGENTS-depo/sys4ai-depot-AGENTS.md` | Exact root guidance duplicate retained only as the manifest source | REM-005 |
| `ROLES-depo/sys4ai-depot-ROLE.md` | Exact root role duplicate retained only as the manifest source | REM-005 |

Empty directories left by these deletions may be removed. Git history remains
the recovery source if the user later authorizes a new synchronization project.

### Rewrite or update

| Path | Planned change | Requirement |
| --- | --- | --- |
| `README.md` | Describe the post-removal workspace, independent catalogs and installations, registry, and current verification | GOV-002, REG-001, VER-001 |
| `AGENTS.md` | Remove manifest and managed-copy duties while retaining Director, role, Task, TRD, and delivery rules | GOV-001 |
| `ROLE.md` | Replace synchronization governance with workspace-registry and reusable-catalog governance | GOV-001, GOV-002 |
| `depot/README.md` | Document `projects.json` as inventory only | GOV-002, REG-001 |
| `depot/projects.json` | Correct the template path, remove `managed`, and record registry-only semantics | REG-001 |
| `AGENTS-depo/project-template-AGENTS.md` | Remove parent-manifest instructions from reusable template guidance | TMP-001 |
| `Projects/Sys4AI-Template-Project/AGENTS.md` | Apply the same project-local ownership guidance in the current ignored template | TMP-001 |
| `Projects/Sys4AI-Template-Project/README.md` | Remove sync setup and managed-file claims; document explicit one-time component selection | TMP-001 |
| `Projects/README.md` | Describe registered independent project working trees without synchronization terminology | REG-001 |
| `tests/test_repository_contract.py` | Replace manifest/engine assertions with retirement, preservation, registry, governance, link, and traceability checks | REM-004, VER-001, VER-002 |
| `Verification/sys4ai_synchronization_removal_verification.md` | Record baseline, exact changes, command evidence, requirement matrix, and limitations | VER-003 |

### Preserve

- `SKILLS-depo/**` and `.agents/skills/**`;
- `SOULS-depo/SOUL.md` and active `SOUL.md` copies;
- reusable template and sub-agent role assets under `AGENTS-depo/`,
  `ROLES-depo/`, and `sub-agent-roles/` that are not on the deletion list;
- retained root `Implementation_Plans/subagent_role_system_implementation_plan.md`
  and `Implementation_Plans/task_system_implementation_plan.md`;
- `Tasks/**`, `TRDs/**`, and the ignored template's local project data;
- `.gitignore`, repository configuration, Git history, index, and remotes; and
- every unrelated pre-existing untracked file.

## Work packages

### WP-01 - Freeze baseline and write the plan

1. Read root and template instructions.
2. Record Task-ledger, Git, filesystem, manifest, registry, reference, and test
   evidence.
3. Create the source-linked removal requirements and this exact plan.

Stop condition: The deletion, rewrite, and preservation sets are explicit
before the first destructive edit.

### WP-02 - Remove the executable control plane

1. Delete the engine, manifest, direct unit suite, synchronization-only
   requirements and plan, initial synchronization-dependent project records,
   duplicate contract sources, and redundant root governance sources.
2. Confirm that no installed sync wrapper exists.
3. Remove empty directories created only by the retired files.

Stop condition: No synchronization command, configuration, test, or source-only
duplicate remains callable or project-active.

### WP-03 - Establish post-removal workspace governance

1. Rewrite root `AGENTS.md` and `ROLE.md` around factual registration,
   project-local ownership, and reusable catalogs.
2. Rewrite the root and depot READMEs.
3. Convert `depot/projects.json` to a registry-only schema and correct the
   template path.
4. Update `Projects/README.md`.

Stop condition: Root governance has no synchronization authority or procedure,
and the retained registry matches live paths.

### WP-04 - Detach the template project

1. Update the reusable template `AGENTS.md` source.
2. Update the ignored template's active `AGENTS.md` and README.
3. Preserve all installed template skills, SOUL, role, contracts, Task data,
   environment, and product-neutral purpose.

Stop condition: The template remains usable and contains no parent manifest or
apply dependency.

### WP-05 - Replace repository checks

1. Rewrite `tests/test_repository_contract.py` to assert the post-removal
   contract.
2. Test exact retirement-path absence.
3. Test registry truth, retained capabilities, governance, template neutrality,
   Markdown links, state-system separation, and removal-plan traceability.

Stop condition: The repository suite tests what should exist after removal and
never imports or executes the removed engine.

### WP-06 - Verify, audit, and close

1. Run the repository suite.
2. Run the independent root Task, role-catalog, and To-TRD suites.
3. Run the same independent suites in the ignored template when practical.
4. Search active surfaces for stale commands, manifest references, and sync
   authority.
5. Inspect `git diff --check`, the exact diff, root status, and ignored-template
   changes.
6. Produce the verification record and update this plan's status and evidence.
7. Audit requirements to evidence and changed artifacts to authorization.

Stop condition: All requirements have current evidence, checks pass, protected
assets remain, and limitations are explicit.

## Risk controls

| Risk | Control |
| --- | --- |
| Useful skills are mistaken for synchronization dependencies | Preserve source packages and active installations; inventory them before and after |
| Root instructions still require a deleted manifest | Rewrite both `AGENTS.md` and `ROLE.md`; add repository assertions and stale-reference search |
| The ignored template silently retains obsolete instructions | Inspect and patch it directly; report that it is outside the root Git diff |
| Historical tests are made green by deleting valid coverage | Remove only engine-specific tests; replace repository expectations and run all independent skill suites |
| Unrelated current work is altered | Compare final status with the frozen initial untracked set; do not stage or publish |
| A future reconsideration becomes harder | Preserve reusable assets and Git history; do not create a dormant replacement framework |

## Requirement-to-work traceability

| Requirement | Work packages | Primary evidence |
| --- | --- | --- |
| REM-001 | WP-02, WP-06 | Package/path search and repository contract |
| REM-002 | WP-02, WP-06 | Engine absence and stale-command search |
| REM-003 | WP-02, WP-03, WP-06 | Manifest absence and governance search |
| REM-004 | WP-02, WP-05, WP-06 | Direct-suite absence and passing repository suite |
| REM-005 | WP-02, WP-06 | Exact retirement list and Git diff |
| GOV-001 | WP-03, WP-05, WP-06 | Root governance assertions and inspection |
| GOV-002 | WP-03, WP-05, WP-06 | README and catalog-preservation checks |
| REG-001 | WP-03, WP-05, WP-06 | Registry schema/path tests |
| TMP-001 | WP-04, WP-05, WP-06 | Template content and focused suite evidence |
| PRS-001 | WP-02 through WP-06 | Before/after inventories and independent tests |
| PRS-002 | WP-01, WP-06 | Initial/final Git status and no external action |
| VER-001 | WP-05, WP-06 | Active-surface stale-reference search |
| VER-002 | WP-05, WP-06 | Observed suite outputs |
| VER-003 | WP-01, WP-06 | Final forward and reverse traceability audit |

## Implementation status

| Work package | Status | Evidence |
| --- | --- | --- |
| WP-01 | Complete | Live inventory, baseline tests, removal requirements, and this plan |
| WP-02 | Complete | All 14 deletion-table paths are absent; the uninstalled wrapper path is also absent |
| WP-03 | Complete | Root governance, README files, and registry use project-local ownership and inventory-only semantics |
| WP-04 | Complete | Reusable and active template guidance is detached; the template suites pass |
| WP-05 | Complete | The 11-test post-removal repository contract passes |
| WP-06 | Complete | Structural checks, 242 focused capability tests, diff review, Task-state recheck, and bidirectional audit pass |

## Final evidence

- All 12 tracked deletion-table files and two ignored compiled remnants are
  absent, and the wrapper path that was already absent at baseline remains
  absent.
- The post-removal repository contract passes 11 tests.
- Root Agent Task, role-catalog, and To-TRD suites pass 52, 50, and 19 tests.
- The same template suites pass 52, 50, and 19 tests. The six focused runs total
  242 passing tests.
- The five preserved source, root, and template skill trees match byte-for-byte
  when ignored cache files and `.DS_Store` are excluded.
- Registry JSON validation passes; both registered paths exist; the recorded
  root remote matches `git remote get-url origin`; the template has no `.git`.
- Active root and template guidance has no stale engine, manifest, wrapper, or
  propagation reference.
- The Task ledger remains valid and empty with `mutated: false`.
- `git diff --check` passes, no file is staged, and the unrelated pre-existing
  untracked package, TRD, plan, and verification records remain.
- Full evidence and limitations are recorded in
  `Verification/sys4ai_synchronization_removal_verification.md`.

## Completion gate

- [x] Every path in the deletion table is absent.
- [x] Root and template active guidance contain no synchronization operation.
- [x] Reusable skills, active installations, SOUL files, role bundles, Task
  data, TRDs, and the template remain.
- [x] The registry is factual and cannot grant copying authority.
- [x] Repository and independent skill tests pass.
- [x] No unrelated file is changed or staged.
- [x] The verification record supplies complete forward and reverse evidence.
