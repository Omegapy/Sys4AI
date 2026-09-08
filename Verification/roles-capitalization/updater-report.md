# Template updater role-directory migration

RC-05 is implemented in the five source/pipeline files listed in
[updater-manifest.json](./updater-manifest.json). Live root and Template adoption
remain with the Director. This worker has reached targeted test and disposable
integration verification; it has not applied the live update.

The mapping, required assets and generated-index ownership now use `Roles/`.
Previous lowercase state and generated-index bindings remain readable. A complete
managed lowercase collection migrates as one recorded directory before ordinary
file publication; effective ownership keys are then changed to `Roles/`. No old
lowercase deletion can remove a newly written case alias. The source helper still
validates frozen role pairs and renders the current index in a disposable tree.

The transition binds the exact original raw state, every role-tree file, empty
directories and the original directory device/inode. It archives those original
bytes under the existing content-addressed role-layout history before either
rename hop. Customized managed bytes, partial mappings, aliases, distinct dual
trees, unexpected spelling, stale inputs, new destinations, replacement directory
identities and altered recovery records are rejected. The prior `sub-agent-roles/`
copy/archive/retirement workflow remains supported.

The Director's review found an empty-directory race in the first implementation's
`exists()` followed by `os.rename()`. The new regression reproduced that overwrite
before repair. Both hops now use exclusive native rename through Python's standard
library `ctypes`: `renamex_np(RENAME_EXCL)` on macOS and
`renameat2(RENAME_NOREPLACE)` where available on Linux. The competing empty
directory retains its inode and contents. Unsupported hosts fail closed. Original
passing observations, the failing regression and the pre-repair patch are retained.

## Observed verification

| Evidence | Observed result |
| --- | --- |
| [Final test receipts](./updater-test-results.json) | 47 updater and 12 watcher tests passed on default case-insensitive storage; one distinct-dual-tree test skipped because that filesystem cannot create it. |
| Same test receipts | All 59 tests passed on the Director's real case-sensitive APFS volume, with no skips. The receipt includes an actual case-sensitivity probe. |
| Rename and publication recovery tests | Recovery passed before the first hop, after either hop, during content publication, after state publication and before pending-record cleanup. Read-only check preserved pending state at each boundary. |
| Negative controls | Equal and unequal distinct case trees, wrong case, missing ownership, incomplete mappings, stale reviewed trees, hard-linked files, forged receipts, replaced directories, changed bytes and appearing empty destinations were rejected. |
| [Historical pending replay](./updater-compatibility.json) | Actual prior updater and role-helper bytes from commit `9e57eef474b6fbb3d45283dfd3e2c9bb3f038037` created a lowercase pending transaction. The current updater recovered it, applied the new source edition, migrated to exact `Roles/`, and returned current on repeat check. |
| [Failure before repair](./updater-exclusive-rename-regression-before.json) | The appearing-empty-destination regression failed before the exclusive rename repair and passed in both final filesystem suites. |
| [Artifact manifest](./updater-manifest.json) | Exact before/after hashes, required role-read hashes and a passing scoped whitespace check are retained. |

All fixtures were disposable and cleaned. No live root/Template updater state,
Task, TRD, managed plan, user configuration, Git index or external system was
modified by this worker. Linux's rename implementation was not exercised on this
macOS host. Recovery interruptions were controlled exceptions at real filesystem
operations; power loss was not induced.

## Director adoption commands

After all source helper, policy and guidance changes are integrated, with the
original watcher still stopped, run from the depot root:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/template_update.py check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/template_update.py apply
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/template_update.py check
```

Review the complete first result, especially `role_case_transition`, original
state SHA256, complete tree, intended additions/updates and absence of conflicts.
The first check returns exit 1 when the reviewed source edition needs publication.
After apply, inspect actual Template directory entries for exact `Roles` spelling,
validate its current catalog and initializer, and require the final check to be
current with no pending transaction. The root's separate helper adoption/rename
and watcher restoration remain Director-owned integration work. Any interrupted
Template operation resumes through ordinary `apply`; do not edit its state or
rename the recorded intermediate directory manually.
