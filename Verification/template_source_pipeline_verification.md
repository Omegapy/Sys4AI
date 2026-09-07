# Template source pipeline verification

Historical verification record. The 2026-09-07 cleanup retired the Memory Service
and ontology integration referenced below. Those paths and command results
describe the earlier revision; they are not current setup instructions.

Verified on 2026-09-05 in `/Volumes/P-SSD/AngryOwl/Sys4AI`.

The initializer uses only the registered template for starter assets. The
template is maintained from the reusable source collections through the new
update engine and a running macOS user launch agent. Current source, template
and active initializer package bytes agree.

## Requirement acceptance

| Requirement | Result and direct evidence |
| --- | --- |
| TSP-001 | Passed. Root AGENTS, ROLE and README identify `*-depo` as reusable authoring locations. Template-specific guidance was preserved in AGENTS-depo and SPECS-depo sources before adoption. |
| TSP-002 | Passed. `test_template_assets_and_renderer_win_over_reusable_depot_editions` and `test_installed_helper_works_when_all_reusable_collections_are_missing` exercise both routes; receipts cite template paths exclusively. |
| TSP-003 | Passed. Dynamic skill/role/reference adoption and optional-package deletion tests pass. Required governance dependency failures are rejected. The live template contains seven complete skill packages. |
| TSP-004 | Passed. Engine add/edit/delete cases pass. Live source addition, modification and deletion propagated through launchd without manual apply calls. Existing product files and other active root skills have no diff. |
| TSP-005 | Passed. The exact mapping produces 73 template destinations from 71 source files; every mapped source/destination byte sequence and receipt hash matched during final inspection. |
| TSP-006 | Passed. `org.sys4ai.template-update.a58847325820` is loaded and running, with a recent successful check. The user approved macOS removable-volume access for Python. See [live evidence](./template-watch-live-check.json). |
| TSP-007 | Passed. Tests reject customized targets, invalid skills/JSON/Python, unsafe links, special files, traversal, collisions and missing collections. Unmanaged files are preserved. Independent review findings about stale status and log symlinks were fixed and regression-tested. |
| TSP-008 | Passed. Shared initializer locks block updates; updater locks block initialization. Source file-set drift and interruption-recovery tests pass. A current `check` reports no changes, and no-op apply preserves timestamps in fixtures. |
| TSP-009 | Passed. All 26 initializer unit tests and the installed-wheel end-to-end test passed. The latter exercised creation, manual preparation plus exact recall, isolation, equivalent reruns and recovery in disposable depots. The live template remains uninitialized. |
| TSP-010 | Passed. Check/apply and watcher install/status/uninstall/reinstall work; the guide documents recovery, mapping and clone setup. Uninstall removed the service and plist, reinstall became ready, and managed template state remained byte-identical. Source/active/template validation and final diff checks pass. Logout/reboot were not performed. |

## Checks run

| Command or inspection | Observed result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -q` | 57 tests passed, including 19 update-engine and 10 watcher tests. |
| `.venv/bin/python -m unittest discover -s SKILLS-depo/init-new-project/tests -p test_initializer.py -v` | 26 tests passed. |
| `.venv/bin/python -m unittest discover -s Projects/Sys4AI-Template-Project/tests -q` | 7 tests passed. |
| Initializer `test_end_to_end.py` with a verified current consumer artifact | 1 installed-wheel integration test passed in 130.062 seconds. |
| Skill Creator `quick_validate.py` on source, active and template initializer | All three valid. |
| Agent Task read-only validation | All 15 Tasks valid; no warning or mutation. |
| `tools/template_update.py check` | Current; 73 managed destinations, no addition, update, deletion or conflict. |
| `tools/template_watch.py status` | Loaded, running, fresh successful check, `ready: true`. |
| Mapped-file hashes and initializer three-way comparison | Passed. |
| Registry, root SOUL and historical orchestration TRD/plan comparison with Git HEAD | Byte-identical. |
| `git diff --check` and Memory Service child Git status | Clean checks; no Memory Service source change. |

The first installed-wheel attempt identified an older artifact whose recorded
README no longer matched the producer's current documentation. The supported
builder produced a new local artifact at
`Projects/Sys4AI-Memory-Service/dist/consumer/0.1.0/c553b32ce99da88c7c1b7a491cdbeeab6659a3266c65a84f6588180f500b62f2/artifact.json`.
The integration test then passed without changing an old receipt. Runtime
installations and generated projects were confined to disposable fixtures.

The first launch attempt failed because macOS would not let `xpcproxy` create
log files on the removable volume. Launch logs now use the user's standard
`Library/Logs/Sys4AI/` location. Python's subsequent removable-volume prompt
was explicitly approved by the user, after which the live file lifecycle
passed: addition 6.61 seconds, modification 4.32 seconds, deletion 4.82 seconds.
The probe was removed from source and template.

## Review and boundaries

The Project Director independently inspected the initializer's template lookup,
asset selection, receipt origins, locking, manual preservation and recovery,
and the updater's mapping, ownership checks, atomic writes and recovery logic.
A separate reviewer reproduced and reported two watcher defects; both were
corrected before the final live check. Live lifecycle verification also exposed
asynchronous launchd unloading. Stop now waits for actual unload, and readiness
requires a fresh successful receipt from the current process. Regression tests
and live uninstall/reinstall passed after these corrections.

An independent forward-test used the actual helper to create Field Notes and
prepare Field Notes Manual in a temporary depot. Both adopted a newly added
three-file optional skill and three-file role bundle. All 78 asset records per
project matched source/destination hashes and cited the template exclusively,
even after all temporary `*-depo` collections were removed. The manual copy's
notes and extra local skill resource were preserved byte-for-byte. The template
was unchanged. This check intentionally stopped before runtime installation;
the separately passing installed-wheel test covers that stage.

Highest verification: installed-runtime end-to-end behavior in disposable
depots, plus observed source-to-template updates through the real host launch
agent. Login startup and recovery after a physical drive reconnect are
configured but were not exercised by logging out, rebooting or disconnecting
the user's drive. The updater validates syntax and required files; it does
not run every package's tests after every edit.

The earlier Task closure is preserved as an unrelated pre-existing change.
No new Task, managed TRD or native goal was created. The registry, root SOUL,
historical plans, Memory Service source and existing product projects remain
unchanged. The active initializer received the explicit requested adoption;
other active root skill installations remain independent. Git publication,
semantic model activation and product-memory refresh were not performed.
