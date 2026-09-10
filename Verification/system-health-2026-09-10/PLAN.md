# Ontology and health diagnostics test plan

Date: 2026-09-10. Project: `/Volumes/P-SSD/AngryOwl/Sys4AI`.

The user requested a plan, execution of that plan, and an evidence-backed health assessment. This is an ordinary test plan under the active native goal. It does not activate a managed Task, TRD, or implementation-plan record.

## Scope and success criteria

The current installed ontology has compact core, standards, inference, semantic, guard, and workbench profiles. “Health system” is interpreted as the installed health diagnostics; memory health is included as an ontology dependency. There is no separately identified health service in the inspected implementation. The user was offered clarification during inspection; a material correction will revise this scope before dependent checks.

| Requirement | Acceptance criterion | Work and evidence |
| --- | --- | --- |
| H1: Establish actual installation health | Record current configuration, source freshness, generated state, selected profiles, backend readiness, and dependency integrity; retain failures as findings. | Baseline manifests; live core/advanced/memory health; package checks. |
| H2: Exercise ontology behavior | Execute representative vocabulary, graph, capability, current-authority, RDF query, SHACL, inference, and semantic retrieval operations. Compare results with current authored meaning and declared contracts. | Timestamped command logs, exit codes, structured observations, wiki link check. |
| H3: Test health diagnostics | Existing regression tests and isolated fault controls detect missing/invalid configuration, changed source or output, unavailable backend, and stale certification/index where covered. Identify misleading summaries or exit codes separately. | Installed ontology regression suite; focused memory health tests; diagnostic coverage report and any additional isolated probes. |
| H4: Verify integrated health | Inspect the complete status tree, compare health summaries with actual operations, and distinguish enabled, ready, degraded, unavailable, and unexercised behavior. | Final report with severity, evidence, reproducible commands, and repair recommendations. |
| H5: Preserve project state | All canonical ontology/memory records, configurations, shared source assets, installed code, registry, Task state, and pre-existing edits retain their baseline bytes. | Before/after SHA-256 manifests and final Git comparison. |

## Execution order and ownership

1. Director saves the baseline and this plan before running tests. Inspect existing tests and use the root Python 3.12 environment plus already provisioned ontology environments.
2. One `project-sub-agent` runs the installed regression suite and evaluates diagnostic fault coverage in disposable fixtures. Its only durable write scope is `Verification/system-health-2026-09-10/regression/`. The Director runs live read operations and owns the plan, live evidence, and final report.
3. Run core health/validation and representative retrieval. Inspect generated wiki links without rebuilding. Run advanced health, real SPARQL/SHACL/inference, exact and paraphrased semantic searches, and memory health/validation/retrieval.
4. Exercise workbench health using an existing safe read interface or a short-lived local read-only service if necessary. Retain only sanitized status evidence; private session tokens stay outside reports. Guard checks are read-only on the real root; mutation/recovery behavior is tested only in disposable fixtures.
5. Reconcile observed failures with diagnostic claims. Targeted follow-ups must test a new hypothesis. Missing prerequisites are reported; the audit does not install packages, download models, repair indexes, recertify runtimes, publish records, or change settings to turn a failure green.
6. Reopen logs and artifacts, compare protected bytes and Git state, map every requirement to evidence, and report the health of the systems at the observed time. A completed assessment may find unhealthy components; it does not imply repairs were performed.

## Constraints and stopping condition

Keep test writes confined to this verification directory and disposable temporary fixtures. Preserve unrelated working-tree changes and existing product projects. Existing tests may start bounded fixture-local workers or loopback services and must clean them up. No Git publication, product adoption, or host configuration change is included. External service availability and future-project deployment are outside this local assessment.

Stop after the planned checks and evidence review establish the current health or precise limitations for each selected component. Do not broaden to repairs without an evidence-supported need and appropriate scope. Save the final assessment in `REPORT.md` with command/result receipts alongside it.
