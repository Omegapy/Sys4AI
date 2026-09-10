# Ontology and health diagnostic regression assessment

H3 completed on 2026-09-10 for `/Volumes/P-SSD/AngryOwl/Sys4AI`. All 153 distinct ontology tests were successfully exercised across direct discovery and two bounded follow-ups. The 34 focused memory tests passed. The unmodified installed discovery remains broken by a fixture-path defect. Detailed health diagnostics detect the tested faults, but top-level readiness and process exit status do not summarize whole-system health.

## Results

| Check | Run | Passed | Errors | Skipped | Exit | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ontology-discovery | 153 | 120 | 9 | 24 | 1 | 175.475 |
| selected-guard-regression | 32 | 32 | 0 | 0 | 0 | 248.318 |
| semantic-packet-acceptance | 1 | 1 | 0 | 0 | 0 | 9.082 |
| memory-health-focused | 34 | 34 | 0 | 0 | 0 | 0.614 |

There were no assertion failures. Every suite has raw `.stdout.log` and `.stderr.log` files plus a `.receipt.json` with its exact command, environment overrides, working directory, timestamps, duration, and actual exit status. [summary.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/summary.json) contains every test ID, outcome, original error/skip, instruction digest, and limitation.

The direct command was `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s .agents/skills/ontology/tests -v`. Its nine errors occur during `GuardEngineTests` fixture setup. Twenty-three guard tests skip backend checks; one actual-model semantic test skips because its acceptance root was not selected. Raw details remain in [ontology-discovery.stderr.log](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/ontology-discovery.stderr.log).

The installed `tests/guard_support.py` sets `DEPOT` to `Path(__file__).resolve().parents[3]`, which resolves to `.agents` in the installed layout. It then looks for `.agents/SKILLS-depo/ontology` and `.agents/.venv-ontology-standards`. The supplemental [selected_guard_regression.py](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/selected_guard_regression.py) corrects that variable only in its verification process, before test-class imports. `SYS4AI_GUARD_INSTALLED_ROOT` selects the installed helpers and contracts for disposable fixtures. All nine errored and 23 skipped guard cases then passed. No source file was repaired.

The semantic follow-up used `SYS4AI_SEMANTIC_ACCEPTANCE_ROOT` to select the existing local runtime/model, copied into a disposable fixture. It passed actual embedding, frozen packet retrieval without a live model call, forged-score rejection, and changed-index rejection. Nothing was downloaded.

## Health diagnostic findings

- **Exit 0 is not an aggregate health pass.** Ontology source staleness yields `degraded` with exit 0. Missing advanced backends and stale certification appear inside `profiles`, while `advanced-health` has no aggregate status and returns 0. Memory health remains `ready`, exit 0, with `evidence_changed` and `claim_unsupported` diagnostics. The paired ontology and memory `validate` commands return `valid: false`, exit 1, for their stale-source cases.
- **Canonical readiness and generated readiness are separate.** A missing projection, changed compiled output, or invalid generated manifest leaves core health `ready`, exit 0, while `generated` correctly reports `missing`, `stale`, or `invalid`. This matches the contract's separation of canonical reads and explicit projections; it does not show that projections are current.
- **Guard and workbench entries describe selection.** A profile with `guards.enabled: true` but missing required guard bindings still reports enabled plus a constant coverage description. The direct read-only guard checker rejects the same configuration with `guard_schema`. Workbench health returns the placeholder `running: "inspect the selected service"`, including when no service was started. These fields do not establish operational readiness.

Implementations inspected: ontology `ontology.py:13-43,152`, `ontology_advanced_cli.py:76-86`, `ontology_profiles.py:47-74`, `ontology_semantic.py:247-259`, and memory `memory_core.py:326-345`, `memory.py:101`, `basic_memory_adapter.py:113-125`. The command contract describes separate generated readiness; memory operations explicitly use certificate inspection without starting the vendor runtime. Standards readiness checks existing certification and exact package/helper fingerprints. Live operation results remain necessary.

Stale memory support means a historical claim needs applicability review. It does not establish record corruption or that the original observation was false. The parent owns the exact live-root evidence audit.

## Fault controls

All 22 read invocations preserved fixture file bytes and mtimes. Nineteen provide meaningful configuration/diagnostic controls. Three initial controls hit macOS `/var/...` alias rejection before configuration inspection; their original logs are preserved. [configuration_fault_probes.py](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/configuration_fault_probes.py) repeated only those cases using resolved `/private/var/...` roots.

| Fault | Detailed result | Exit |
| --- | --- | ---: |
| Missing/invalid ontology configuration | `invalid`, `missing_file` / `invalid_json` | 1 |
| Missing/stale/invalid generated products | Core `ready`; nested state detects fault | 0 |
| Changed ontology source | `degraded`; paired validator `valid: false` | 0; validator 1 |
| Enabled missing advanced backends | Nested `backend_unavailable` / `unavailable` | 0 |
| Changed standards certification | Nested `incompatible_certification` | 0 |
| Changed semantic index inputs | Nested `unavailable`, `stale_semantic_index` | 0 |
| Incomplete enabled guard | Health says enabled; checker `guard_schema` | 0; checker 1 |
| Changed memory evidence | `ready`; `evidence_changed`, `claim_unsupported` | 0; validator 1 |
| Enabled missing memory backend | `ready`; backend unavailable, lexical limitation | 0 |
| Missing memory contract | `invalid`, `file_absent` | 1 |
| Missing memory configuration | `absent`, unavailable backend | 0 |

Current compiled-output and standards-certificate controls passed before their fixture bytes were changed. Full control results and receipts are in [fault-probes.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/fault-probes.json) and [configuration-fault-probes.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/configuration-fault-probes.json). Each control has separate raw logs. The semantic stale-index control uses synthetic vectors to isolate freshness detection before model access; actual-model acceptance passed separately.

Existing coverage also passed actual SHACL conformance/violation cases, fail-closed guard/backend controls, all eight action families and owning-helper locks, recovery and deadlines, source/path safety, projection tampering, and read preservation. Small fixture graphs do not establish that live-root SHACL finishes within its selected budget. The parent reports that live result separately.

## Preservation and stopping condition

Only this regression evidence directory was changed durably. Temporary fixtures were cleaned up. No production source repair, installation, download, recertification, root build/index refresh, canonical publication, or Git mutation occurred. The parent owns and has reported a successful full protected-state comparison. Actual guard native receipts remain synthetic fixture data; HTTP tests do not establish a user browser workflow or native authorization.

Required role digests matched the assignment on initial read and recheck. [inspected-source-digests.json](/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/system-health-2026-09-10/regression/inspected-source-digests.json) records the full hashes, including SOUL, both role files, and the assigned plan. The supplied role catalog fingerprint was `ba245e8ebbde2fd020f851d21343d5348b3763692a37468cab019642775b3545`. No nested delegation occurred.

Highest local verification: relevant broader regression coverage plus runtime behavior in disposable fixtures, including real standards workers, semantic model execution, and loopback HTTP. All suite processes have exited. The H3 stopping condition is reached; no further tests or source repairs are underway. Follow-up candidates are a fixture root-discovery repair and an explicit aggregate monitoring result that preserves component details while surfacing selected-component failures.
