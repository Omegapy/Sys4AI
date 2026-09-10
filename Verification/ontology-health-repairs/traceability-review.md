# Acceptance mapping review

All **30 requirements**, **60 original acceptance criteria verbatim**, **36 planned tasks**, and **54 adoption source/destination artifacts** are mapped. **No criterion receives final acceptance**; this is a draft for the host.

The JSON retains the exact approved criterion text, canonical task actions/criteria/dependencies, actual source hashes, evidence-file hashes, and existing test IDs. AST-derived test IDs are coverage links, not new executions. Source/fixture results do not establish actual root or delivered-runtime readiness.

TRD revision 2: `cfb3ef5cebdec871e2c44118f6f7888d93c156a6ce1463b6ba3511625a9c5fa0`. Plan revision 1: `1569553faaebb27904e6b5282fd8bff39948cfce79079ecde0807a9290439705`. Current 54-file manifest: `e7d0dffd2a23e8b89835de56dbb5788dcdd4e52fa2feba99f2ab13a23cca8425`. 8 current source hashes differ from that manifest; exact versions are recorded in manifest_source_drift and refresh is pending.

## Observed evidence

- Full authored SHACL payload: **3,413 triples** (2,268 asserted +1,129 derived +16 external), conformant in **5.8784 seconds** within unchanged 10-second budget. All 191 targets and 2,346 expanded property constraints are equivalent;15 semantic controls per version pass. The earlier asserted+derived-only violation is preserved separately and resolved by the later full-authored replay.
- Memory source suite: **89 passes**, zero skips/failures/errors. All five original historical artifact versions, the unchanged receipt and six matching logs are retained. Exact companion/supersession candidates validate in a disposable fixture; no live disposition is inferred.
- Discovery: six controls and eight nested ordinary unittest runs (72 tests) across source, installed, Template-named and deep-space layouts. Required skip/setup error/missing identity gates reject; declared optional-unselected skips remain allowed.
- Source ontology focused evidence includes six health controls, four independent health regressions, nine link/query controls, workbench security and corrected publication results. Complete selected source/installed coverage remains a separate gate.
- Initializer: six recorded static controls, three selected preservation controls and two ontology-adoption controls pass. The newest relocation case and complete final initializer suite require completed current evidence.
- Explicit Template precheck/apply and delivered Template contract suite exit 0. Final coherent-set postcheck/parity and preservation remain required.

## Pending execution and verification

- **PEND-MANIFEST-REFRESH — PENDING:** Re-freeze current source changes and refresh exact reviewed adoption manifest; 8 source hashes drifted from the observed 54-file manifest.
- **PEND-SOURCE-ONTOLOGY — PENDING:** Complete selected current-source 182-identity standards+semantic gate, including original 153 identities. No partial result or skipped selected profile counts as success.
- **PEND-SOURCE-INITIALIZER — PENDING:** Complete current frozen initializer full suite, including newest relocated-copy control. Earlier incomplete/aborted logs remain incomplete.
- **PEND-TEMPLATE-FINAL — PENDING:** Final post-apply check, exact source/Template parity and preservation after last relevant write.
- **PEND-ROOT-ADOPTION — PENDING:** Execute exact 54-artifact adoption through required guard repair; retain final runtime/guard bindings and post-hashes.
- **PEND-HISTORICAL-DISPOSITION — PENDING:** Publish reviewed companion only in already granted Verification/project-memory/evidence and exact two-record supersession; reinspect provenance and live helper result.
- **PEND-ROOT-MAINTENANCE — PENDING:** After final inputs settle, granted memory reindex and ontology links/wiki/semantic refresh, selected actual backend query/health and dependency closure.
- **PEND-DELIVERED-MATRIX — PENDING:** Final coherent delivered fresh/manual/deep/relocated/populated/earlier-adoption/customized/capture-off/rerun/interruption matrix and actual selected runtime.
- **PEND-LIVE-CLOSURE — PENDING:** Re-run originalF 1-F6 checks against final root; prove full current conformance, selected runtime/guards/service, preservation and final host acceptance.

## Implementation gaps and evidence limits

No confirmed uncovered implementation requirement was identified by this bounded mapping. Remaining items are explicit final operations or verification gates, not assumed missing code. This does not replace integrated review or required suites. Equivalent existing evidence is distinguished from missing planned report filenames in the JSON.

The original control_records/memory plan target label cannot widen current root authority. The historical companion uses already granted Verification/project-memory/evidence; canonical memory and maintenance retain existing owner helpers/journals.

The canonical plan remains unchanged. Manifests, previews, equal source bytes, installed runtime directories and historical receipts are not final adoption or current operational acceptance. Earlier failed publication, partial initializer and limited-scope SHACL evidence remains separately labeled.

## Reverse adoption map

| Root destination | Source | Tasks | Delivery |
| --- | --- | --- | --- |
| `.agents/skills/ontology/README.md` | `SKILLS-depo/ontology/README.md` | TASK-002, TASK-023 | PENDING final adoption/parity |
| `.agents/skills/ontology/references/commands.md` | `SKILLS-depo/ontology/references/commands.md` | TASK-002, TASK-023 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology.py` | `SKILLS-depo/ontology/scripts/ontology.py` | TASK-012, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_advanced_cli.py` | `SKILLS-depo/ontology/scripts/ontology_advanced_cli.py` | TASK-014, TASK-015, TASK-021 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_health.py` | `SKILLS-depo/ontology/scripts/ontology_health.py` | TASK-012, TASK-014, TASK-015, TASK-017, TASK-018, TASK-021 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_memory.py` | `SKILLS-depo/ontology/scripts/ontology_memory.py` | TASK-010, TASK-016, TASK-017, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_profiles.py` | `SKILLS-depo/ontology/scripts/ontology_profiles.py` | TASK-014, TASK-017, TASK-021, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_publication.py` | `SKILLS-depo/ontology/scripts/ontology_publication.py` | TASK-017, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_retrieval.py` | `SKILLS-depo/ontology/scripts/ontology_retrieval.py` | TASK-012, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_shacl.py` | `SKILLS-depo/ontology/scripts/ontology_shacl.py` | TASK-005, TASK-006, TASK-007 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_standards.py` | `SKILLS-depo/ontology/scripts/ontology_standards.py` | TASK-006, TASK-007, TASK-021 | PENDING final adoption/parity |
| `.agents/skills/ontology/scripts/ontology_workbench.py` | `SKILLS-depo/ontology/scripts/ontology_workbench.py` | TASK-015, TASK-018, TASK-021 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/acceptance_runner.py` | `SKILLS-depo/ontology/tests/acceptance_runner.py` | TASK-004, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/advanced_support.py` | `SKILLS-depo/ontology/tests/advanced_support.py` | TASK-003 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/guard_support.py` | `SKILLS-depo/ontology/tests/guard_support.py` | TASK-003 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/support.py` | `SKILLS-depo/ontology/tests/support.py` | TASK-003 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_acceptance_coverage.py` | `SKILLS-depo/ontology/tests/test_acceptance_coverage.py` | TASK-004, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_action_semantics.py` | `SKILLS-depo/ontology/tests/test_action_semantics.py` | TASK-003, TASK-008, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_fixture_discovery.py` | `SKILLS-depo/ontology/tests/test_fixture_discovery.py` | TASK-003 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_guard_deadline.py` | `SKILLS-depo/ontology/tests/test_guard_deadline.py` | TASK-003, TASK-008, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_guard_profiles.py` | `SKILLS-depo/ontology/tests/test_guard_profiles.py` | TASK-003, TASK-014, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_guard_recovery.py` | `SKILLS-depo/ontology/tests/test_guard_recovery.py` | TASK-003, TASK-018, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_guarded_dispatch.py` | `SKILLS-depo/ontology/tests/test_guarded_dispatch.py` | TASK-003, TASK-014, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_health_contract.py` | `SKILLS-depo/ontology/tests/test_health_contract.py` | TASK-012, TASK-014, TASK-015, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_health_review_regressions.py` | `SKILLS-depo/ontology/tests/test_health_review_regressions.py` | TASK-012, TASK-014, TASK-015, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_publication.py` | `SKILLS-depo/ontology/tests/test_publication.py` | TASK-017, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_query_memory.py` | `SKILLS-depo/ontology/tests/test_query_memory.py` | TASK-010, TASK-016, TASK-017, TASK-018 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_semantic_packet.py` | `SKILLS-depo/ontology/tests/test_semantic_packet.py` | TASK-003, TASK-004 | PENDING final adoption/parity |
| `.agents/skills/ontology/tests/test_shacl_lists.py` | `SKILLS-depo/ontology/tests/test_shacl_lists.py` | TASK-006, TASK-007 | PENDING final adoption/parity |
| `.agents/skills/memory/references/basic-memory-pilot.md` | `SKILLS-depo/memory/references/basic-memory-pilot.md` | TASK-013, TASK-016, TASK-021, TASK-023 | PENDING final adoption/parity |
| `.agents/skills/memory/references/evidence-and-lifecycle.md` | `SKILLS-depo/memory/references/evidence-and-lifecycle.md` | TASK-010, TASK-011, TASK-023 | PENDING final adoption/parity |
| `.agents/skills/memory/references/operations.md` | `SKILLS-depo/memory/references/operations.md` | TASK-002, TASK-013, TASK-017, TASK-021, TASK-023 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/basic_memory_adapter.py` | `SKILLS-depo/memory/scripts/basic_memory_adapter.py` | TASK-013, TASK-016, TASK-021 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/basic_memory_projection.py` | `SKILLS-depo/memory/scripts/basic_memory_projection.py` | TASK-016 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/memory.py` | `SKILLS-depo/memory/scripts/memory.py` | TASK-013 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/memory_capture.py` | `SKILLS-depo/memory/scripts/memory_capture.py` | TASK-011, TASK-017 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/memory_core.py` | `SKILLS-depo/memory/scripts/memory_core.py` | TASK-013 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/memory_evidence.py` | `SKILLS-depo/memory/scripts/memory_evidence.py` | TASK-010, TASK-011 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/memory_maintenance.py` | `SKILLS-depo/memory/scripts/memory_maintenance.py` | TASK-017, TASK-021, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/memory_publish.py` | `SKILLS-depo/memory/scripts/memory_publish.py` | TASK-011, TASK-017 | PENDING final adoption/parity |
| `.agents/skills/memory/scripts/memory_search.py` | `SKILLS-depo/memory/scripts/memory_search.py` | TASK-010, TASK-013 | PENDING final adoption/parity |
| `.agents/skills/memory/tests/test_health_evidence.py` | `SKILLS-depo/memory/tests/test_health_evidence.py` | TASK-010, TASK-011, TASK-013, TASK-016, TASK-017, TASK-018, TASK-021, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/memory/tests/test_learning_integration.py` | `SKILLS-depo/memory/tests/test_learning_integration.py` | TASK-011, TASK-017 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/README.md` | `SKILLS-depo/init-new-project/README.md` | TASK-019, TASK-023 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/SKILL.md` | `SKILLS-depo/init-new-project/SKILL.md` | TASK-019, TASK-023 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/assets/initialization-receipt.schema.json` | `SKILLS-depo/init-new-project/assets/initialization-receipt.schema.json` | TASK-019, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/assets/static-capability-v1.json` | `SKILLS-depo/init-new-project/assets/static-capability-v1.json` | TASK-019, TASK-020 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/scripts/init_new_project.py` | `SKILLS-depo/init-new-project/scripts/init_new_project.py` | TASK-019, TASK-020, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/scripts/init_ontology_advanced.py` | `SKILLS-depo/init-new-project/scripts/init_ontology_advanced.py` | TASK-019, TASK-020, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/scripts/init_static_health.py` | `SKILLS-depo/init-new-project/scripts/init_static_health.py` | TASK-019, TASK-020 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/tests/test_learning_adoption.py` | `SKILLS-depo/init-new-project/tests/test_learning_adoption.py` | TASK-019, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/tests/test_ontology_adoption.py` | `SKILLS-depo/init-new-project/tests/test_ontology_adoption.py` | TASK-019, TASK-022 | PENDING final adoption/parity |
| `.agents/skills/init-new-project/tests/test_static_readiness.py` | `SKILLS-depo/init-new-project/tests/test_static_readiness.py` | TASK-019, TASK-020, TASK-022 | PENDING final adoption/parity |
| `reference-assets/MEMORY-depo/publication-and-recovery.md` | `MEMORY-depo/publication-and-recovery.md` | TASK-010, TASK-011, TASK-017, TASK-023 | PENDING final adoption/parity |

## Mapping validation

Exact 30/60/36/54 cardinalities, criterion equality with both TRD and canonical plan, source hashes with explicit drift findings, reverse coverage, source-parsed test IDs and evidence-file existence were checked. Only the two assigned mapping files were written. This assignment ran no test suite, grant, canonical mutation, installation or publication.

The host must refresh evidence states after in-flight suites and final root/delivered operations finish. File hashes intentionally describe this observation; an in-progress log may change afterward.

## Pending additions after the 54-file manifest

The host added a measured RDF dataset canonicalization correction and two corresponding regression IDs, plus the documented health-exit expectation adjustment. The current required ontology inventory contains **182 identities** (the original 153 remain obligations). These changes are mapped as pending additions in the JSON and need manifest regeneration and the complete selected suite. No passing outcome is inferred from source presence.

- `SKILLS-depo/ontology/scripts/ontology_rdf.py` → `.agents/skills/ontology/scripts/ontology_rdf.py`: TASK-006, TASK-007; PENDING manifest and final verification.
- `SKILLS-depo/ontology/tests/test_rdf_canonicalization.py` → `.agents/skills/ontology/tests/test_rdf_canonicalization.py`: TASK-006, TASK-007, TASK-018; PENDING manifest and final verification.
- `SKILLS-depo/ontology/tests/test_query_retrieval.py` → `.agents/skills/ontology/tests/test_query_retrieval.py`: TASK-012, TASK-018; PENDING manifest and final verification.
