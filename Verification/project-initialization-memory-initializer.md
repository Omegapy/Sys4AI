# Project initializer verification

The Director reran the complete source package suite on 2026-09-05: **16 tests
passed in 112.272 seconds**, including the installed-wheel end-to-end cases.
Command: `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 TMPDIR=/private/tmp
SYS4AI_INITIALIZER_ARTIFACT=<verified artifact.json> .venv/bin/python -m unittest
discover -s SKILLS-depo/init-new-project/tests -v`.
The full output is `/private/tmp/sys4ai-initializer-director-final-tests.txt`.
The tested helper SHA-256 is
`b3eb40afa4e3d551725cd528c99f35efb77b5c345a8764fcb40a477f728bb149`.
Skill Creator metadata validation and Ruff passed. Relative package links resolve.

The exact wheel used here has SHA-256
`37bd904f5ad2bdda16b63e86f42cfca44e13f71c2cf6b92b1ca3dcf4c7cca7c7`.
The disposable depots reconstruct the recorded source from that immutable wheel;
their source provenance is independently checked. A later integration run will
use the final runtime artifact after reviewed-registration and reread corrections.

## Behavior verified

| Plan work | Direct observations |
| --- | --- |
| TASK-007 | Nine-file complete source skill; installed location pins the depot and three exact registered identities. Standard-library helper delegates memory preparation and operations to the installed wheel. No Git mutation, publication, credential or provider activation route. Source and active adoption are separate. |
| TASK-008 | Table-driven forbidden destination, traversal, symlink, hardlink, occupied path and source-substitution tests compare unchanged manifests. The exact static starter allowlist excludes environments, caches, Git directories/gitfiles, history, models, derived state and unknown files. |
| TASK-009 | Supplied ID/name/purpose specialize README, project.json and canonical memory identity before registration. Invalid/reserved/duplicate identities fail before mutation. Created active files have the real product identity. |
| TASK-010 | Registry schema, duplicate and stale-state tests, atomic failure injection and equivalent rerun pass. Exact child Git markers are required before read-only Git observation; ancestor discovery is never a child HEAD. Manual preparation shares the same registration function. The live registry and live Projects inventory were unchanged. |
| TASK-011 | Exactly six complete source packages and the baseline soul are adopted with source/destination hashes. Source additions during copying cause drift refusal. Later source edits do not refresh owned copies. No optional seventh package is copied. Portable adopted-package checks passed as detailed below. |
| TASK-012 | Installed subprocesses prepare canonical configuration, initialize directly once, sync and recall exact project content without source PYTHONPATH. Schema-validated receipts record actual immutable wheel/version/origin, project/dataset, asset digests, checks and deferred model activation. The memory receipt has no preview fields. Failure before initialized state is recorded as partial, never successful. |
| TASK-013 | Creation, manual preparation, equivalent no-op rerun, duplicate/conflicting identity/path, stale registry, installation and bootstrap failure recovery all pass in owned disposable depots. Completed reruns validate dataset and configuration fingerprint, installed bytes and database identity; mismatches stop without mutation. |

Related scenarios are consolidated in `tests/test_initializer.py` and
`tests/test_end_to_end.py`, with the seed/asset contract in
`assets/baseline-assets.json`. These replace the plan's illustrative per-feature
test filenames without omitting their cases. The implementation includes one
shared copy/identity/registry/install/preparation flow for both routes.

## Adopted package validation

In a real generated consumer: Agent Task 52/52, portable role catalog 40/40,
managed-plan helper 50/50 and To-TRD 42/42 tests passed. Communication and Task
metadata and complete byte manifests passed. The Task orchestration tests are
producer-depot checks that require depot collections and historical verification
records; copying those into a consumer would violate its six-package boundary.

Two unchanged producer Task assertions fail at the real depot (16 tests, two
failures): `test_conditional_packages_match_impact_matrix` and
`test_required_sources_are_adopted_by_the_active_root`. They assume equality
between source and active Task packages, while the separately authorized
30-day intake policy already changed only the active root before this plan's
baseline. One unchanged template role assertion fails (50 tests, one failure):
`test_director_role_contains_every_required_operating_section` expects the exact
heading `## Task assessment and decomposition`. The template ROLE and all six
source and preexisting active packages retain their protected baseline hashes.
These are classified existing contract mismatches, not waived functional checks.

Evidence details and before/after input comparisons are in
`/private/tmp/sys4ai-initializer-evidence/`. This verification did not initialize
the template, create a live product, change Git metadata, publish, download a
model or exercise semantic inference.
