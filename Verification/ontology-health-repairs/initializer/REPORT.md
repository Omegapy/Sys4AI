# Initializer static readiness and prevention

Bounded implementation for PLAN-20260910-2C3A0863 TASK-019, TASK-020, TASK-022 and the assigned reusable-source portions of TASK-023/TASK-028. The host owns integrated release acceptance, actual root adoption, canonical plan state and runtime checks.

## Result contract

The initializer now reports a versioned `static_health` assessment, `static_ready`, `aggregate` and `ready`. The assessment identifies the destination, selected setup edition or module, observation time, inspector digest, source-inventory digest, component input-inventory digests, required/preserved outcomes and precise diagnostic paths. It explicitly reports `runtime: not-exercised`, `provisioned: false` and `unknown_target_code_executed: false`. Known hash-pinned configuration, learning and role-index inspectors are identified separately.

An adopted or explicitly selected capability that fails a required static check stops in the existing verification stage. Assets and registration that already completed remain recorded; the receipt stays partial, reports the failed capability and retains the exact recovery request. The CLI returns 2. Correcting the cause and repeating the exact operation resumes its existing receipt and source versions.

A preserved custom capability gap may retain completed base assets and registration, with `preserved-unverified`, `static_ready: false`, `aggregate: degraded`, and CLI exit 1. This retains the base receipt required for later governed module adoption. It makes no healthy-installation claim. CLI exit 0 requires the selected static assessment to pass. Explicit capture-off and disabled publication choices are retained.

## Implemented checks

The current neutral starter is checked against `assets/static-capability-v1.json`, pinned by the executing initializer. Its 211 required paths include ontology, memory and initializer packages, shipped tests, the ontology health helper and acceptance runner, local contracts and four exact standards/semantic requirement-profile locks. The final inventory digest is `7c63b052c086a09697ca43514dd91f90e56183bdd62e93152fe298d12d7f32a5`. Missing required files, malformed Python/JSON, changed locks, invalid identity/imports, and invalid or stale enabled local publication bindings prevent an adopted capability from passing.

The first setup snapshot freezes actual source/adoption identities as before. Ordinary reruns assess current bytes against that receipt's edition and source inventory. Completed module-adoption inventories are overlaid by package and destination for current assessment, removing superseded resources without rewriting the original base or operation records. This closes the observed case where a later-adopted ontology test could become syntactically invalid while an older base receipt falsely reported a passing empty ontology inventory.

Pure memory configuration inspection requires the current reviewed `memory_core.py` hash `48592604ac950e32e4c80aab24edd2e90d26d09df1b6af912dcad24bbc490a54` and unchanged `memory_paths.py`. The previously reviewed core hash `a41175553ec3e4d81b7cede8cc26b81676eddb4a7a697db6c1a47aab5929d874` remains allowed only for assessment of a preserved configuration edition; new Template sources require the current pin. Function-local runtime imports are not invoked by static configuration validation.

The previously unrestricted role-inspector `exec` now checks exact known helper bytes before execution. It accepts current `Roles` hash `b649dc368d9b4f2d8eec032aaf2ae28e08ff493bbaf07d20ef21a55a52fd0cb2` and the exact reviewed root-name variants for `roles` and `sub-agent-roles`. Unknown copied role helpers are retained and rejected before code execution. Legacy edition names and original receipt hashes remain unchanged.

The receipt JSON schema retains the original three ordered completed setup checks and permits additional typed static outcomes. Selected module operations can retain their scoped `static_health` without a new ledger or a base setup-edition upgrade. Skill metadata is 11.1.0; the setup contract remains `governance-starter-v9`, receipt schema version 1.

## Verification record

Final full-suite verification passed: 119 tests ran, 118 passed, one platform-dependent test skipped, and there were no failures or errors. The ordinary command was `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/init-new-project/tests -v`. Unittest measured 780.567 seconds; the capturing runner measured 780.693 seconds and returned exit 0. `final-suite.receipt.json` retains the exact command, cwd, test identities/outcomes, logs and source binding. It confirms zero source changes during the run. `source-freeze.json` SHA256 is `ef09cc12214a3048262f5c3a7e49298fec5965f5cf0c1cf4ec360573f40c28ad`.

Focused evidence already retained:

- `static-readiness.*.log`: initial six controls passed, including fresh/manual/deep paths, required adopted-test failure and exact recovery, preserved capability gaps, disabled choices, unknown ontology code inspection and v8 retention. The final suite additionally includes relocated receipt-replay rejection, later-adoption rerun coverage and the role-inspector sentinel control.
- `selected-boundaries.*.log`: three controls passed for incomplete selected memory refresh, preservation and missing required test/health resources. Selected failure expectations changed; the original preservation assertions remain.
- `ontology-adoption-boundaries.*.log`: two controls passed for unavailable selected ontology adoption/refresh, which now remains partial rather than claiming completed capability.
- `adoption-rerun-regression.*.log`: three controls passed for later module source assessment, retired package-resource handling, v6 learning refresh and populated-v8 advanced adoption.
- `role-trust-and-binding.*.log`: 13 tests ran, 12 passed and one platform-dependent case skipped. The unknown role helper sentinel did not execute; current/v1/v2 variants and role-case recovery passed. Capture-off remained preserved while stale enabled ontology bindings correctly prevented readiness.
- `../installations/template-static-contract.receipt.json`: the changed Template inventory contract test passed in a disposable source-composed Template using its actual copied initializer and resource list. The live Template was not written by this worker.

The first broad run's `full-suite.*.log` is retained as diagnostic evidence. It overlapped memory-inspector source changes and reported the expected pin mismatch plus legacy assertions that accepted unavailable explicitly selected capability. Interrupted runs are retained under `interrupted-before-*`; their receipts explicitly record interruption and changed source versions and do not count as final acceptance. `diagnostic-before-final-freeze.*` retains the settling run with the two subsequently corrected test assertions. The final frozen run supersedes those diagnostic runs for acceptance; their original logs remain available.

## Preservation and limits

All durable source edits are confined to `SKILLS-depo/init-new-project/**` and the assigned `SPECS-depo/template-tests/test_template_contract.py`. `changed-paths.json` records exact baseline/current hashes; `source-freeze.json` binds the final source set used by validation. Evidence is confined to this directory and the assigned `../installations/` directory. No installed `.agents`, actual Template, root configuration/registry, canonical Task/plan, project memory, root runtime, Git or external publication was written by this worker. Disposable setup tests use their own registrations and receipts.

The case-sensitive dual-directory control requires a case-sensitive filesystem and is explicitly skipped on this host's case-insensitive test volume. No disk image or filesystem was created to replace that missing platform condition. Final delivered installation checks, actual selected runtime behavior, root adoption and end-to-end release closure remain host integration work. Static readiness does not certify a backend/model, validate live guard operation, start a workbench, or establish semantic runtime conformance.

The bounded stopping condition is satisfied. Highest verification reached is level 5 for observed setup CLI and filesystem behavior in disposable projects, supported by the complete relevant initializer suite. Final installed delivery and actual root/runtime acceptance are not claimed here. No subagents were created by this worker and no workers from these verification runs remain active.
