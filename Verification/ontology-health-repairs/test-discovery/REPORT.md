# Fixture discovery and selected coverage controls

Bounded implementation of PLAN-20260910-2C3A0863 TASK-003 and TASK-004. The host owns integrated acceptance and canonical plan state. This report records focused fixture and coverage verification; selected standards and semantic runtime acceptance remain with the host after the source set settles.

## Implemented behavior

Ontology support now resolves the package's actual source or installed owner by its named layout. It validates that owner's delivered ontology contracts and never searches ancestor projects. Disposable neutral fixture data is composed from the selected local module, context, and advanced-profile contract, with the module file-set digest checked by the existing module helper. Temporary fixture roots are resolved before calling production helpers. Existing production path/symlink/hardlink/FIFO checks are unchanged and their loading tests pass.

Guard fixtures copy the selected delivery's helpers and contracts. Initializer and Template-update test factories are depot-only inputs: a root that lacks those factories must explicitly select `SYS4AI_TEST_DEPOT_ROOT`. This selector supplies factory code for disposable depots, not a fallback helper/contract installation. The legacy explicit `SYS4AI_GUARD_INSTALLED_ROOT` adapter selector remains supported. Guard module reload/cleanup isolation remains in place.

`SYS4AI_STANDARDS_PYTHON` selects an existing certified `venv/bin/python`; otherwise only the exact package owner's `.venv-ontology-standards` is considered. The interpreter executable symlink is not resolved out of its virtual environment. An invalid explicit selection fails; an absent unselected optional backend produces an explicit skip. `SYS4AI_SEMANTIC_ACCEPTANCE_ROOT` continues to select an existing local semantic environment/model and now validates its required files. No selection provisions packages, downloads a model, certifies a runtime, or mutates the selected owner.

The reusable `tests/acceptance_runner.py` records exact command, cwd, selected owner, test directory, Python, runtime selectors, standards certificate digest, inventory digest, discovered identities, per-identity outcomes, unittest exit, final gate exit, logs, and timing. Class/module setup events are attributed to their unexecuted discovered methods. Missing identities, duplicate discovery, incomplete results, failures/errors, unexpected successes, expected failures, selected/required skips, and unapproved skip reasons block acceptance. New unclassified tests are required. Only a declared unselected optional profile with an explicitly allowed reason may skip, with the receipt stating that its behavior was not exercised.

## Inventory and original audit

`../required-test-inventory.json` retains the original 153 identities and each original outcome from `Verification/system-health-2026-09-10/regression/summary.json`, with its digest and command. Original discovery remains 120 passes, nine guard setup errors, 23 guard skips, one semantic skip, exit 1. The audit files were not edited. At this handoff the inventory has 175 identities, including the host's six health-contract tests and the SHACL worker's four declared tests. New test additions do not erase baseline obligations.

## Observed verification

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/ontology/tests -p test_fixture_discovery.py -v`: six controls passed in 37.683 seconds. Eight nested ordinary unittest commands ran 72 tests: nine loading and nine guard-engine tests in each source, installed-root, Template-named, and deep initialized-project layout. All eight processes returned zero. `layout-controls.stdout.log` records every exact command/root, stdout, and stderr; `layout-controls.stderr.log` records the outer results. These test all nine originally errored guard identities without a monkeypatch or audit wrapper.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/ontology/tests -p test_acceptance_coverage.py -v`: six controls passed. Cases include required skips, optional class-level skips, unapproved reasons, setup errors, missing/duplicate identities, and failed subtests. Raw logs are `coverage-controls.*.log`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python Verification/ontology-health-repairs/test-discovery/gate_injection_checks.py`: actual CLI processes returned required skip = 1, setup error = 1, missing identity = 1, and approved unselected optional skip = 0. Individual `injected-*.receipt.json` files retain two expected identities, logs, exact runtime selections, and diagnostics; `gate-injection-summary.json` records their comparison with expected exits.
- The ordinary source `test_loading.py` route passed all nine tests after the fixture change. AST syntax inspection passed all 12 changed/new reusable Python files. Required instruction digests were rechecked unchanged in `instruction-digests.json`.

## Selected runtime route for integration

Use the ordinary installed unittest command for development, or the following shipped identity gate for complete release evidence. Both support explicit existing runtime selection; neither installs one. Use absolute, already resolved paths for selected roots:

```sh
SYS4AI_STANDARDS_PYTHON="/selected/certified/venv/bin/python" \
SYS4AI_SEMANTIC_ACCEPTANCE_ROOT="/selected/semantic/project" \
SYS4AI_TEST_DEPOT_ROOT="/selected/depot" \
PYTHONDONTWRITEBYTECODE=1 /selected/python \
  /selected/project/.agents/skills/ontology/tests/acceptance_runner.py \
  --inventory /selected/required-test-inventory.json \
  --receipt /selected/output/ontology-acceptance.json \
  --select standards --select semantic
```

The runner derives its test owner from the selected package, or accepts an explicit `--tests-dir`. For an unselected optional profile, omit its `--select` and runtime selector. A standards runtime already present in the exact selected owner may still execute its tests; actual outcomes remain reported. Always use `--select standards` when standards coverage is an acceptance requirement. The host will exercise the original 23 skipped real guard cases and actual semantic packet test after source integration.

## Files and authority

`changed-paths.json` is the exact source/inventory manifest with current and baseline SHA256. Authorized initial source writes were `guard_support.py`, `support.py`, `advanced_support.py`, and `test_semantic_packet.py`; new files are `acceptance_runner.py`, `test_acceptance_coverage.py`, and `test_fixture_discovery.py`. The host explicitly extended authority to `test_guarded_dispatch.py`, `test_guard_recovery.py`, `test_guard_profiles.py`, `test_guard_deadline.py`, and `test_action_semantics.py` only for shared runtime availability and helper/factory path calls. Their test assertions were preserved. Evidence writes are confined to this directory and `../required-test-inventory.json`.

No installed `.agents`, Template, root runtime/configuration, registry, canonical Task/plan, project memory, or original audit files were written by this worker. No nested delegation occurred. External runtime/factory bytes are selected inputs, not shipped starter content. Fresh configured-project creation and final delivered full-suite checks remain later integration evidence. The bounded stopping condition is satisfied; highest verification here is targeted tests plus observed acceptance-CLI and ordinary unittest subprocess behavior in disposable layouts.
