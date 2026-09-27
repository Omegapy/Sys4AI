# Ontology and health-system reassessment

**Result: healthy for the assessed local capabilities and operations.** No unresolved health failure was found in this reassessment. The earlier SHACL timeout, stale memory integration, misleading aggregate health results, and broken installed test discovery are resolved in the current checked-out version.

Observed on 2026-09-10 at commit `b3d9e5ea28bd6679b7fca58f12ca4a59f417d4ae`. The working tree was clean before this audit. The approved baseline is `TRD-20260910-F345F166`, revision 2; its bytes remain unchanged. See [assessment context](assessment-context.json) for source identities and [the reassessment plan](PLAN.md) for scope.

## Before and after

| Earlier finding | Fresh observation | Disposition |
| --- | --- | --- |
| SHACL exhausted its 10-second budget | Full authored validation passed. Quiet-run worker time was **6.3997 seconds**, with **6.574 seconds total command time**. The operational-health run passed in **5.9252 worker seconds**. The limit remains 10 seconds and 512 MiB. | Resolved for the current graph and environment. |
| Memory backend projection and ontology associations were stale | Core generated products are current; memory static and operational health are ready. Actual hybrid retrieval succeeds without limitations, and mixed ontology retrieval reports current associations. | Resolved. |
| Historical memory evidence produced unsupported-claim errors | All four records validate. Original notes are superseded with historical proof retained; two active successors are explicitly historical context. Changed implementation versions produce informational applicability diagnostics. | Resolved without claiming old evidence verifies current code. |
| Health could say ready or exit zero despite selected failures | Current core, advanced, and memory summaries identify selected scope and assessment level. The live stopped-workbench control returned degraded/false and exit 1. All 66 identified regression fault controls passed. | Correct for the exercised conditions. |
| Direct installed ontology tests errored or skipped required coverage | The ordinary installed suite passed **183/183**, including all original 153 test obligations, with no verification-only root patch and no skips. | Resolved. |
| Recurrence through delivered setup needed verification | All 59 source/root adoption bindings and 312 managed Template files match. Nine focused initialization tests and 12 actual Template contract tests passed. | Current focused delivery checks pass; broader retained implementation evidence is distinguished below. |

The graph now contains **3,413 triples** across asserted, derived, and external authored graphs. Inferred conclusions are kept separate. SPARQL, the wiki-index-to-Artifact inference, canonical and current-authority lookup, graph traversal, capability discovery, semantic search, and wiki links all passed. Canonical validation passes all **34 competency checks** with **59 current source references**.

## Current health and diagnostic behavior

Ontology and advanced ontology report `aggregate: ready`, `ready: true` and no failed required components. Memory reports ready at both static and operational levels; its actual local backend probe and separate hybrid search pass. The semantic exact query ranks Task first, and the actual embedding query “recollections” ranks MemoryRecord first.

The complete advanced operational check exercised SPARQL, full SHACL, inference, semantic embedding, the guard validator, and the selected live workbench endpoint. Guard integrity covers the current declared action families and exact adapters. A read-only health check does not dispatch a production mutation; actual guarded mutation/recovery behavior is covered by disposable regression fixtures.

The audit-owned workbench served six assets and authenticated read-only state/record APIs correctly. Its endpoint passed current project, configuration, helper, and snapshot checks. After the service was stopped, the same endpoint was correctly reported as stopped and degraded with exit 1. This is an expected negative control, not an unresolved incident. The workbench remains an on-demand capability; this report does not claim it is continuously running. Session credentials stayed in memory.

Memory has **zero records claiming verified-current implementation support**. That is consistent with the repaired historical dispositions. The older observations remain historically supported, while current runtime confidence comes from this reassessment's actual operations. See [memory evidence summary](memory-evidence-summary.json), [memory validation](live/memory-validation.json), and [hybrid search](live/memory-hybrid-search.json).

## Fresh verification

| Suite | Passed | Failures/errors/skips |
| --- | ---: | --- |
| Ordinary installed ontology | 183 | 0 / 0 / 0 |
| Installed memory | 94 | 0 / 0 / 0 |
| Focused installed initializer readiness | 9 | 0 / 0 / 0 |
| Actual Template contracts | 12 | 0 / 0 / 0 |
| **Total** | **298** | **0 / 0 / 0** |

The 66 identified fault controls are included within these suites, not added to the total. The [regression report](regression/REPORT.md) and [structured summary](regression/summary.json) retain exact commands, runtime selections, identities, timing, raw logs, and preservation checks. Four nonfatal PyMuPDF/SWIG deprecation warnings remain visible in the memory log; they did not fail tests.

[Live command receipts](live-checks.json) retain 27 fresh command captures with raw stdout/stderr and actual exit codes. The only nonzero result is the intentional stopped-service control. Package integrity checks pass in the root, standards, ontology-semantic, and memory-pilot environments. [Root delivery verification](delivery-verification.json) and [Template verification](template-verification.json) confirm the current delivered bytes; the Template updater's read-only check reports current.

## Evidence scope and preservation

All **237 files** cited by the implementation's final acceptance record still match their recorded hashes. That record covers 30 requirements and 60 criteria. [Prior evidence verification](prior-evidence-verification.json) identifies these as retained historical runs, not new tests. [Requirement reassessment](REQUIREMENT-COVERAGE.md) maps the 30 requirements to fresh observations and any retained basis.

The full 119-case initializer run, detailed phase-level profiling, and the broad relocated/populated delivery matrix were not repeated wholesale. Their retained evidence is unchanged; current source/root/Template parity and focused initialization regressions were freshly checked. Visual browser rendering, always-on service uptime, live production mutation/recovery, dependency installation, new model downloads, other product adoption, and external deployment were outside this assessment.

The [protected-file comparison](preservation.json) shows all **6,649 files** retained their contents and modification times. The [runtime comparison](runtime-preservation.json) separately confirms **214 runtime files** unchanged, including current memory/ontology derived state and the selected certification. These sets may overlap and are not summed. [Git preservation](git-preservation.json) confirms no change outside this audit directory. The prior audit, repair evidence, TRD, canonical records, configuration, registry, source code, and existing environments were preserved.

Only this audit's scripts and evidence were added. The project memory completion checkpoint kept this inspection non-mutating and created no duplicate historical note. The assessment establishes the state of the selected local systems at the recorded versions and times; later source, configuration, evidence, or runtime changes require a new health check.
