# Role publication review

Reviewed 2026-09-08 against PLAN-20260908-6E6F545E TASK-005 through TASK-008 and TRD REQ-018 through REQ-020 and REQ-033. The review covers the role helper and focused tests. It does not accept the complete plan or exercise root/Template adoption.

Four actionable gaps were reproduced. The highest verification level reached is runtime behavior observed in disposable fixtures. No source, installed skill, root role, Template, Task, plan, configuration, or external state was changed by this review.

Reviewed source:

- `SKILLS-depo/manage-subagent-roles/scripts/role_catalog.py`, SHA-256 `27d1d0e7761d7f9fabb6a2367edcf24c04b0379380604cc67c0d40db0be42400`.
- `SKILLS-depo/manage-subagent-roles/tests/test_role_catalog.py`, SHA-256 `e7c31535be17523fa4ee363fcd8460a7ea21acd6d3518743c7d077e84e983952`.

## Findings

### P1: Transition overwrites a destination created after its preflight check

Location: `role_catalog.py:1040-1044`, through `atomic_publish` at lines 566-577.

The transition reads a destination's digest and confirms it is absent. It then calls `atomic_publish`, which accepts any regular file and replaces it using `os.replace`. An editor or another process that creates the destination between those operations loses its content. The catalog lock serializes cooperating helper calls; it does not prevent that filesystem change. The transition returns success after this overwrite.

Reproduction used the existing `RoleCatalogTests` disposable legacy fixture. A wrapper around `atomic_publish` wrote `Concurrent project-owned content\n` to the destination `AGENTS.md` immediately before invoking the real publisher. This is the exact boundary after the preflight digest check. Observed output:

```json
{"status": "updated", "touched": ["roles/legacy-worker/AGENTS.md"], "customization_preserved": false}
```

The reviewed destination can only be absent or already byte-identical: identical content needs no write. Publish missing role files with an atomic fail-if-present operation, and preserve a newly appearing file for review. Keep replacement semantics for the separately governed index/receipt publication. Add a regression that inserts a differing destination at this boundary and verifies its bytes survive, the operation reports pending or blocked, and no successful completion receipt is written.

This violates TASK-006's concurrent-change protection and TASK-007/REQ-033's preservation and exact overwrite boundary. The existing test at `test_role_catalog.py:720-727` checks a stale catalog before publication; it does not exercise this interval.

### P2: Index validation can delete an already valid newly created pair

Location: `role_catalog.py:869-874`; the partial-publication handler at lines 885-891 is reached too late.

`_create_role` writes both canonical files, then calls `build_catalog`, which now also validates the index path. If the index is unsafe or unreadable, the generic creation rollback removes the new pair even when that pair is valid. The caller receives `CatalogError`, without the promised committed-bundle and index-recovery result.

Reproduction created a symlink at `roles/INDEX.md` pointing to a preserved fixture file, then called `create_role`. A wrapper inspected the new pair immediately before delegating to the unmodified cleanup function. Observed output:

```json
{"exception": "CatalogError", "target_exists": false, "cleanup": [{"valid_before_cleanup": true, "files_before_cleanup": ["AGENTS.md", "ROLE.md"]}], "preserved": "preserve"}
```

Check index safety before creation writes a target, and separate authoritative pair validation/commit from navigation publication failures. Once the pair is valid and committed, later index failures must retain it and return explicit recovery. Extend the focused test to fail during the catalog/index inspection after pair publication; the existing test at lines 595-605 only mocks the later `publish_index` call.

This is introduced by adding index validation to the catalog called inside the existing rollback region. It fails TASK-006 and REQ-020's valid-bundle preservation contract.

### P2: A root SOUL.md symlink outside the project leaves a role eligible

Location: `role_catalog.py:381-394`.

The validator resolves both the expected `SOUL.md` and the link target before comparing them. A root `SOUL.md` symlink pointing outside the project therefore compares equal and passes `is_file`. The new `checked_path` checks protect the paired files but do not check this instruction source.

Reproduction created a valid fixture pair, replaced root `SOUL.md` with a symlink to a regular file in a separate temporary directory, and rebuilt the catalog. Observed output:

```json
{"valid_roles": ["valid-worker"], "invalid": []}
```

Validate the unresolved required instruction-source path with the same alias policy, then confirm the target is a regular file confined to the project. Add a fixture for an external root-SOUL symlink. This is an existing validator gap carried into the new implementation, rather than a newly introduced regression; it leaves TASK-005 and REQ-018's required link/confinement invariant unmet.

### P2: Completed transition receipts accept inconsistent completion provenance

Location: `role_catalog.py:992-1002` and 1018-1024.

The current receipt validates that listed completed files are recognized, but a `status: completed` receipt need not list all its published files. Retained history validates its outer fields and preview but never validates its `completed` value. As a result, inconsistent or malformed provenance is accepted as a successful current transition.

Two probes started with a real successful transition and then changed only its receipt:

1. Replaced the current `completed` array with `[]`. Reapply returned `status: current`; the receipt still claimed `status: completed` with no completed files.
2. Appended a history entry with a valid preview and `status: completed`, but `completed: {"../not-a-file": "unreviewed"}`. Reapply returned `status: current` and retained that malformed history.

Use one structural validator for current and historical receipt entries. Require every completed reference to be a unique destination in its own preview, and require exact destination coverage for completed status. Historical validation should check internal provenance consistency without requiring historical destination bytes to remain live indefinitely. The tests at `test_role_catalog.py:729-740` cover unsupported top-level versions and null previews, but not these internally inconsistent completed states.

This is a receipt-validation gap under TASK-007 and REQ-033. The probes did not cause path traversal or mutate a file named by the malformed history; the defect is accepting corrupted completion evidence as valid provenance.

## Reproduction method and checks

All probes used the root `.venv/bin/python`, `PYTHONDONTWRITEBYTECODE=1`, the source helper imported through the existing test module, `RoleCatalogTests.setUp()`/`tearDown()`, and temporary directories. Fixture roots were normalized with `.resolve()` before instrumentation to account for macOS `/var` aliases. Publication probes used `unittest.mock.patch.object` only to insert a deterministic failure or concurrent filesystem event, then invoked the original helper operation. No production function was replaced with a simulated outcome.

Focused command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover \
  -s SKILLS-depo/manage-subagent-roles/tests -p test_role_catalog.py \
  -k RoleCatalogTests -q
```

Observed: 52 tests passed, exit 0. This independently confirms the existing focused suite while the additional probes expose the gaps above.

Running the same discovery without `-k RoleCatalogTests` also ran all 52 behavioral tests successfully, but `ImplementationContractTests.setUpClass` failed before its tests. Its `PROJECT_ROOT = ...parents[4]` resolves to `/Volumes/P-SSD/AngryOwl` in the reusable source layout, so it attempted to read `/Volumes/P-SSD/AngryOwl/Implementation_Plans/subagent_role_system_implementation_plan.md`. This is a source-placement/test-harness limitation, not evidence of a role-helper regression or a passing broader suite.

Only this report was written. The bounded review is complete; fixes, regression tests, integration, and plan acceptance remain with the Project Director.

## Superseding recheck after four fixes

The Project Director requested a bounded recheck of the four findings and adjacent publication/rollback behavior. This section supersedes their unresolved status above while preserving the original evidence. The recheck reviewed source SHA-256 `b63c30795df5e863f583c8f0c01ba00443c3915b3f2f7faef0d8a85b73fb6dc0` and test SHA-256 `f43fdf0f5a9038d0971077be78d79ea7f491a82f4cbe1b2680389bd66695d161` on 2026-09-08.

All four original reproductions now pass:

- A file inserted at the transition publication boundary survives. Apply reports pending, and the receipt remains pending.
- An already unsafe index is rejected before `_create_role` is entered. The new pair is never created. The added regression also verifies that an index becoming unsafe after pair publication leaves the valid pair intact with recovery reported.
- A root `SOUL.md` symlink to an external regular file yields no eligible role and one invalid-role diagnostic.
- A completed receipt with empty destination coverage and a historical entry with a malformed `completed` object are both rejected without changing the receipt.

The same focused unittest command above passed all 56 `RoleCatalogTests` with exit 0. The original failure probes were rerun separately against the revised helper, with keyword forwarding adapted to the new `atomic_publish(..., replace=...)` signature. No broader suite or adoption workflow was run in this recheck.

### Remaining P2: Rollback deletes a concurrently replaced file with identical bytes

Location in the rechecked source: `role_catalog.py:841-846` and 888-900.

Creation now records only filenames successfully linked by the helper, and cleanup verifies the target directory identity. It still identifies each file by its filename and content. If another process replaces a linked file with a new regular file containing the same bytes, cleanup deletes that replacement after a later publication conflict. A directory identity check cannot establish ownership of a replaced child file.

The adjacent probe used the existing creation fixture and wrapped the second `os.link` call. At that boundary it atomically replaced the already published `AGENTS.md` with identical bytes under a different inode, then created `ROLE.md` using the pending source bytes. Direct pair validation returned valid before the real second link raised `FileExistsError`. Cleanup then removed the replacement `AGENTS.md`, leaving the concurrently completed pair incomplete. Observed output:

```json
{"new_inode": true, "valid_concurrent_pair": true, "exception": "FileExistsError", "agents_survives": false, "role_survives": true}
```

Record each successfully linked file's device/inode identity and restrict cleanup to that identity as well as its expected content. Preserve a replaced file even when the bytes happen to match. A focused regression should exercise this replacement before the second-link conflict and verify both files in the concurrent valid pair survive.

The original four findings are resolved for their reproduced cases. This single adjacent preservation gap remains. Highest verification reached: runtime behavior observed in disposable fixtures. Only this superseding report section was written; the recheck stopping condition has been reached.

## Director correction of the adjacent rollback finding

Rollback now records each linked file's device/inode from its source before publication and removes only that exact inode with matching expected bytes. The new regression atomically replaces AGENTS.md with identical bytes and a different inode while the second link collides; both valid concurrent files survive. The full focused suite now passes 57 tests. All original reviewer findings and the adjacent reproduction are addressed. Current helper SHA-256: `5f4ad425c096a3de82bec18e67d0773291d65a70734cfd9bd87ed37dcea21d66`.
