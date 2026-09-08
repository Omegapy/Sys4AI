# Initializer role-directory capitalization

RC-06 is implemented in the reusable `SKILLS-depo/init-new-project/` package.
New setup uses helper version 5.0.0, setup contract `governance-starter-v3`, and
exact `Roles/` directory entries. The initializer does not migrate a selected
project's role collection; that operation remains an explicit role-helper
preview/apply followed by reviewed helper adoption and reindexing.

The exact changed-file hashes, original hashes, role-read receipts and test-log
hashes are in [initializer-results.json](initializer-results.json). Only this
source package and `initializer-*` evidence were written by this worker.

## Behavior and evidence

| Acceptance area | Observed result |
| --- | --- |
| New project creation and manual-copy preparation | Actual isolated Python CLI runs created the two role pairs and index under exactly `Roles/`, retained project identity and registry behavior, and completed reruns. |
| Existing current collections | Existing pairs, custom files and missing resources stay project-owned as one collection. Preparation generates an absent index from actual pairs and refuses an incompatible existing index. It does not add a missing task-manager pair into an existing role collection. |
| Wrong-case or conflicting collections | Preparation refused lowercase `roles`, uppercase `ROLES`, and genuinely distinct `Roles` plus `roles` trees before mutation. The dual-tree case ran on real case-sensitive APFS. A current starter policy with a lowercase physical Template tree was also rejected. |
| Current-edition interruption | An interrupted role-index publication retained the v3 edition. A wrong-case retry was refused without mutation; restoring the recorded physical spelling allowed the original operation to finish. |
| Prior setup editions | v1 legacy-role and v2 lowercase-role partial setup and completed reruns retained their original contract, source paths, source hashes and adoption maps. A partial v2 asset stage could not adopt a later Template edition. |
| Proven v2 case rename | A completed role-helper rename let the v2 receipt verify current files under actual `Roles/` paths. The separate proof digest was recorded without relabeling the original source or adoption maps. Later authorized role edits and explicit reindexing remained compatible. |
| Invalid case proof | Missing, pending, wrong-root or changed recorded proof refused reruns before mutation. |
| Post-assets recovery | A v2 setup interrupted after its asset stage resumed registration and verification after the completed explicit case rename, retaining the original v2 source inventory. |
| Retained copy-first provenance | An actual disposable legacy-to-lowercase transition followed by an actual case rename permitted new v3 preparation and rerun. The original `.transition.json` bytes and retained legacy pair hashes stayed unchanged; the existing current collection was preserved whole. |

## Checks

The original 36 initializer tests passed after the implementation changes.
The expanded suite then ran on both filesystem modes. One final copy-first
integration test was added and run separately on each mode; no production code
changed between the expanded suite and that final test.

| Filesystem | Distinct tests | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Case-sensitive APFS fixture | 46 | 46 | 0 | 0 |
| Case-insensitive APFS under `/private/tmp` | 46 | 45 | 0 | 1 |

The sole skip is the genuinely distinct dual-directory case, which passed on
case-sensitive APFS. Logs retain the separate 45-test suite and one-test run:

- [Case-sensitive suite](initializer-tests-case-sensitive.log)
- [Case-insensitive suite](initializer-tests-case-insensitive.log)
- [Case-sensitive copy-first integration](initializer-copy-first-case-sensitive.log)
- [Case-insensitive copy-first integration](initializer-copy-first-case-insensitive.log)

Python AST checks and JSON parsing passed for all seven source resources of
those types. The scoped Git whitespace check passed. Tests used the existing
Python 3.12 interpreter and standard library; isolated CLI subprocesses allowed
only read-only Git observations. Fixtures honored the supplied `TMPDIR` and
cleaned their disposable project contents.

The earlier-edition fixtures model their actual policy, path and receipt
contract. Their role helper is configured to its former lowercase root inside
the fixture. They are compatibility fixtures, not modified live historical
projects. Runtime locks and transition receipts remain excluded from starter
copies.

## Integration boundary

This worker did not update the live root installation, live Template, updater
state, registry, watcher, Task/TRD records or historical plans, and did not stage,
commit or publish Git changes. The Director owns live adoption and final
integrated validation. The highest level here is successful local CLI workflows
and broader initializer-suite verification on both filesystem modes; future
product use and external publication were not exercised.
