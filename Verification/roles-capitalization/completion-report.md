# Roles directory capitalization complete

The active directory is now spelled exactly `Roles/` in both the Sys4AI root
and designated Template. Discovery, creation, validation, reindexing, Task
assignment checks, Template updates and project initialization use that path.
All ten requirements in the [implementation plan](../../Implementation_Plans/roles_capitalization_implementation_plan_2026-09-08.md)
are satisfied. The [final audit](final-audit.json) maps all 90 implementation
artifacts back to the requirements and records their original/current hashes.

The filesystem migration preserved each role pair and the original root
`.transition.json` bytes. Both directory moves use exclusive rename operations
through an intermediate name with exact identity, inventory and recovery
receipts. The Template transaction also preserves its prior ownership state.
Repeated root migration and Template apply return current without recreating
an active lowercase folder. Git records all 11 exact-case path renames.

Current role assignments require the actual capitalized directory and current
catalog. Historical lowercase provenance remains readable and retains its
original spelling. Worker write scopes reject aliases of the role root/index.
New initialization uses `governance-starter-v3`; existing v1/v2 editions retain
their original source/adoption evidence, with explicit case proof where needed.

| Check | Observed result |
| --- | --- |
| Root integrated suites | 330 run: 327 passed, 3 filesystem-specific skips |
| Template integrated suites | 190 run: 189 passed, 1 filesystem-specific skip |
| Case-sensitive source suites | All 181 role, initializer and updater/watcher tests passed without skips |
| Discriminating Task tests on case-sensitive APFS | All 4 passed |
| Real native role loading | Both selected roots have exact `Roles` entries; all six list/show/validate calls passed and 18 read/helper hashes were independently checked |
| Delivered Template setup | Four actual create/prepare/rerun calls passed on case-sensitive APFS; all 92 files in the existing-project fixture were preserved |
| Final preservation | All 27 protected inventories unchanged; original root-role edits and unrelated To-TRD work retained |
| Template and watcher | 82 managed destinations and 79 sources current; original plist unchanged, current watcher PID 86252 has a fresh successful check |

Counts overlap across source and installed copies and are not a unique-test
total. The skipped cases require distinct case-equivalent directories, which
were exercised successfully on a real case-sensitive APFS image. That temporary
image is now detached and removed. All validation workers have returned; the
native read worker was independently observed completed.

The audit found and corrected an updater race that could overwrite an empty
directory appearing between inspection and rename. Its failing regression and
passing exclusive-rename rechecks are retained. The integrated repository check
was updated to verify this adoption's receipt while preserving the earlier
immutable initializer evidence. Direct Template-copy validation also found a
retired metadata-only legacy directory; its Finder metadata was preserved in a
local backup and the dormant directory was removed from the Template. The
successful rerun proves fresh creation and manual-copy preparation with the
actual delivered Template. See [integration review](integration-review.md) and
[metadata preservation](empty-template-legacy-cleanup.json).

Highest verification: end-to-end local starter setup and actual native role
loading, with deterministic recovery and case-sensitive filesystem coverage.
Linux's exclusive-rename branch, actual power-loss recovery, a replay of the
full native Task-manager category scenario, and automatic discovery in a newly
opened Codex session were not exercised. No other product project was updated;
no dependency, commit, push, deployment or external publication was performed.
Only the necessary case renames are staged; implementation edits and prior
unrelated changes remain in the working tree.

Evidence: [role helper](role-helper-report.md),
[initializer](initializer-report.md), [updater](updater-report.md),
[integrated tests](integrated-tests.json),
[delivered starter](delivered-starter-validation.json),
[native read](native-role-read.json), and [final audit](final-audit.json).
