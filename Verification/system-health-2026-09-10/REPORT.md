# Ontology and health diagnostics assessment

Observed on 2026-09-10 in `/Volumes/P-SSD/AngryOwl/Sys4AI`.

**Overall assessment: degraded.** The ontology's core queries and several advanced operations work. SHACL validation cannot finish within the current budget, memory has stale derived state and historical evidence, and the health summaries do not provide a reliable aggregate signal for automated monitoring.

The [test plan](PLAN.md) was written before test execution. “Health system” is interpreted as the installed health diagnostics; memory was checked as an ontology dependency. This directory contains the implemented audit scripts and current results, not a managed Task, TRD, or implementation-plan record.

## Current component results

| Component | Observed result | Evidence |
| --- | --- | --- |
| Core ontology | Ready for canonical lookup. Structural validation and all 34 competency checks pass; all 59 source references are current. | [Validation](live/ontology-validation.json), [health](live/ontology-health.json) |
| Lookup and relationships | Task definition, current-authority lookup, memory capability discovery, and two-hop graph traversal pass. | [Term](live/ontology-term.json), [authority](live/ontology-current.json), [capability](live/ontology-capability.json), [graph](live/ontology-neighbors.json) |
| Generated ontology | Compiled graph and wiki are current; wiki links pass. Memory associations are stale. | [Health](live/ontology-health.json), [wiki links](live/ontology-wiki-links.json) |
| Standards query | Actual local SPARQL succeeds and counts 2,268 asserted triples. Backend certification is current. | [SPARQL](live/ontology-sparql.json), [advanced health](live/ontology-advanced-health.json) |
| SHACL graph constraints | Incomplete: timeout at the configured 10-second worker limit, both during initial checks and with regression workers idle. | [Initial result](live/ontology-shacl.json), [idle retest](live/ontology-shacl-idle.json) |
| Inference | The wiki index is correctly inferred to be an Artifact, with a trusted derivation and no conflicts. | [Inference](live/ontology-inference.json) |
| Ontology semantic search | Current 94-record index. Exact “Task” ranks Task first; “recollections” uses the local semantic model and ranks MemoryRecord first. | [Exact search](live/ontology-semantic-exact.json), [paraphrase](live/ontology-semantic-paraphrase.json) |
| Guard integrity | All eight declared action families and 12 adapter bindings validate against current files. | [Binding verification](live/ontology-guard-bindings.json) |
| Workbench | Six HTTP assets and authenticated read-only state/record APIs pass on the actual root. The audit-owned service was stopped and no session credential was saved. | [HTTP/API check](live/ontology-workbench.json) |
| Memory | Two records are readable and lexical retrieval works. The enabled backend reports `projection_stale`; full record validation fails for one historical record. | [Health](live/memory-health.json), [validation](live/memory-validation.json), [search](live/memory-search.json) |
| Ontology-memory integration | Ontology rejects the historical record with unverified evidence instead of presenting it as trusted history. | [History query](live/ontology-memory-history.json) |
| Dependencies and distribution | `pip check` passes in root, standards, ontology-semantic, and memory-pilot environments. Template consistency is current; Task ledger is valid with no nonterminal Tasks. | [Command receipts](live-checks.json), [Template](live/template-consistency.json), [Task state](live/task-state.json) |

## Findings and next repairs

1. **SHACL cannot complete on the current root.** The two runs took 10.181 and 10.163 seconds including command overhead; each returned exit 1 and `complete: false`. The idle run rules out parallel regression work as a sufficient explanation. Structural checks passing does not establish SHACL conformance. Profile the constraint generation/validation cost on this graph before selecting a performance change or a reviewed project-budget adjustment.

2. **Memory needs an evidence review and explicit projection maintenance.** The receipt for `MEM-20260909-89C402A6` is unchanged, but its recorded versions of `memory_capture.py` and `init_new_project.py` differ from current code. This prevents current validation of its old verified claim; it does not prove that the historical claim was false. Review applicability using new evidence and the governed record lifecycle, then refresh the memory backend and ontology associations through their explicit maintenance operations. Merely replacing old hashes would not reverify the claim. See the [artifact-by-artifact comparison](live/memory-evidence-audit.json).

3. **A zero exit code or “ready” label is insufficient for a health monitor.** Core ontology readiness excludes generated projection state. Memory readiness excludes evidence errors and backend availability. Advanced health reports nested profile results, but its guard and workbench entries only describe selection and its CLI does not aggregate nested failure states. A monitor must inspect these fields and execute representative operations. The isolated diagnostic controls document the exact current behavior in the [regression report](regression/REPORT.md).

4. **The installed test suite has a fixture-root defect.** Direct discovery ran 153 tests: 120 passed, nine errored during fixture setup, and 24 were skipped. The fixture helper resolves its depot to `.agents` in the installed layout, leading to nonexistent `.agents/SKILLS-depo/...` paths and missed backend detection. The direct run remains a failed run. Supplemental tests use a verification-local correction; they do not repair the installed test entry point. See [regression evidence](regression/REPORT.md).

The supplemental guard run passed 32/32 tests with no skips or errors. The separately selected actual semantic packet test passed 1/1. Together with the direct run's 120 passes, all 153 distinct ontology tests were successfully exercised. Focused memory health/retrieval tests passed 34/34. This does not turn the original installed discovery command into a passing command or resolve the live SHACL and memory findings.

## Execution evidence and limits

[Live command receipts](live-checks.json) retain the exact arguments, timestamps, elapsed time, exit codes, and raw stdout/stderr for 27 commands. The [regression report](regression/REPORT.md) records direct and supplemental suite counts, skips, fault controls, and their limits. [Audit context](audit-context.json) binds governing files and the delegated test role to exact hashes.

Only audit artifacts and disposable test fixtures were authorized writes. Production repairs, dependency installation, model downloads, reindexing, ontology publication, product adoption, and Git publication were not performed. Guard mutation and recovery are fixture tests; no production write was dispatched as a test. Workbench evidence establishes local HTTP/API behavior, not visual browser rendering or production authoring. The workbench was started only for this check, so the result does not claim a continuously running service.

The [preservation comparison](preservation.json) checked 4,769 files: zero changed hashes, additions, removals, or modification-time changes. [Git comparison](git-preservation.json) confirms all 1,645 pre-existing status entries outside this audit directory are unchanged. [Evidence integrity](evidence-integrity.json) confirms the retained raw output matches the saved JSON for all 27 live command captures.

This is a local readiness assessment. The project memory completion checkpoint preserved inspection-only behavior despite automatic capture being enabled; it published no memory record. Current status findings and repair recommendations remain in this audit.

## Requirement coverage

| Requirement | Verification |
| --- | --- |
| H1: Actual installation health | Core/advanced/memory health, dependency checks, and source-version evidence establish current readiness and degradation. |
| H2: Ontology behavior | Live queries, inference, semantic retrieval, HTTP APIs, wiki links, and the explicit SHACL timeout establish the observed behavior. |
| H3: Diagnostics | Existing tests and isolated fault controls evaluate detection and misleading aggregate signals; fixture defects remain visible. |
| H4: Integrated assessment | The component table and findings reconcile reported readiness with actual operations and define concrete next repairs. |
| H5: Preservation | Pass: 4,769 files preserve bytes and modification times; all pre-existing Git status entries outside the audit are unchanged. |

Re-run selected live checks with the root Python interpreter and `audit.py LABEL ontology COMMAND ...` or `audit.py LABEL memory COMMAND ...`; use a new label to retain earlier evidence. `live_probes.py` supports `wiki`, `guards`, and `workbench`. Recheck the selected root and current instructions before any later run.
