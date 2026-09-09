# Project memory release assessment

Implementation and verification are complete under the user’s updated instruction: “so do not used sub-agent and finish testing.” The remaining tests were run directly in the host. No additional sub-agents were launched or used. The original live-agent scenarios that could not finish remain explicitly unexercised; they are not represented as passed. [Verification authority](host-testing-scope.json).

The active root and registered Template contain the complete project-memory capability: portable canonical Markdown records, bounded source retrieval, scoped publication and recovery, immutable Task input packets, and the pinned local Basic Memory 0.23.0 adapter. Root hybrid retrieval is enabled. The Template contains only an empty starter with its backend disabled; initializer edition `governance-starter-v5` specializes new projects while preserving older receipts and existing content.

| Verification suite | Run | Passed | Skipped |
| --- | ---: | ---: | ---: |
| host-source-memory | 61 | 61 | 0 |
| host-installed-memory | 61 | 61 | 0 |
| host-template-memory | 61 | 61 | 0 |
| host-installed-task | 111 | 111 | 0 |
| installed-initializer | 63 | 62 | 1 |
| source-role | 76 | 75 | 1 |
| final-root | 88 | 87 | 1 |
| final-template-contract | 9 | 9 | 0 |

The memory suite now contains 61 tests, including two new integration tests, and passes in all three locations. All 111 installed Task tests passed in the direct host run. Suite counts overlap across installations and are distinct from the 59 requirements. Existing platform-dependent skips remain visible in their logs.

The new integration tests exercise actual Task and memory helper code in disposable projects with explicitly synthetic native receipts. A changed candidate invalidates its old reviewer pass. Publishing a material supersession invalidates old frozen recall without changing Task files; unreconciled fixture owners block packet replacement. A revised baseline invalidates old acceptance, requires both current mapped reviews, preserves assignment identities, and binds a distinct fixture implementer to the new accepted proposal. Optional publication failure and idempotent recovery after terminal Task completion preserve all Task bytes and modification times. No live native message, interruption, review, or implementation is claimed by these tests. [Host test results](host-testing-results.json).

Actual backend evidence remains separate: the isolated and root pilots passed project isolation, exact and conceptual retrieval, metadata preservation, guarded write rejection, classified rebuilds, interruption recovery and outage fallback. Current root health is ready and direct host lookup uses hybrid retrieval. Earlier fresh-context native recall found the actual root record and reopened its matching source evidence; its 287-entry inspection snapshot was unchanged. [Backend decision](backend-compatibility-decision.json), [root checks](root-backend-enablement-results.json), [current health](host-root-health.json), and [fresh-context evidence](end-to-end-results.json).

Earlier native generic capture/publication and two independent complex solvers completed. The reserved senior was never launched because of repeated native thread-limit rejections. The user then selected direct testing without further sub-agents. The original disposable native Task remains at its historical blocked revision 37; its canonical ledger and actual receipts were preserved rather than rewritten as successful live execution. Remaining live complex/extra-complex/material-change runs are excluded by the updated instruction. Production Task team requirements and ownership guards were not changed. [Historical native handoff](native-project/Verification/manager/native-handoff.json).

Preservation checked 5,062 existing files: 4,976 are unchanged and 86 have reviewed implementation changes. All 3,964 protected files are unchanged, including historical Task/TRD/plan records, registry, licenses, To-TRD and Electronics. The real root Task ledger retains 21 terminal Tasks. The complete memory package has 36 matching files in source, root and Template. The Template updater is current and its watcher has a fresh successful check from its current PID. [Preservation](final-preservation.json) and [adoption chain](root-adoption-current.json).

The managed plan remains revision 1, draft, at SHA256 `6cd29af3938797c9bb15c7d699f416d50b43e26d7a8103b99afd0c01679a58c6`; its approved TRD retains revision 2. Their lifecycle records were not mutated. Git HEAD is unchanged. No existing product adoption, Git publication, host MCP registration, cloud routing, deployment, GitHub Pages update or other host/platform was exercised. Retired Memory Service/ontology systems and Cognee remain outside scope.

The [evidence index](evidence-index.json) assesses all 59 requirements and 50 plan tasks, with 1,245 changed/new source and verification artifacts mapped to requirements. Rows marked ‘Local tests; live runs excluded’ retain the user-directed method change and the actual limits of the evidence.

| Requirement | Outcome | Assessment | Primary evidence |
| --- | --- | --- | --- |
| REQ-001 | Preserve project-owned canonical memory | Verified in recorded scope | [root-validation.json](root-validation.json); [end-to-end-results.json](end-to-end-results.json) |
| REQ-002 | Preserve the authority of current sources | Verified in recorded scope | [root-validation.json](root-validation.json); [end-to-end-results.json](end-to-end-results.json) |
| REQ-003 | Keep execution independent of memory | Verified in recorded scope | [root-validation.json](root-validation.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-004 | Separate reusable definitions from learned content | Verified in recorded scope | [core-results.json](core-results.json); [final-template-contract-results.json](final-template-contract-results.json) |
| REQ-005 | Define a durable record contract | Verified in recorded scope | [core-results.json](core-results.json) |
| REQ-006 | Require evidence appropriate to the claim | Verified in recorded scope | [end-to-end-results.json](end-to-end-results.json); [core-results.json](core-results.json) |
| REQ-007 | Make lifecycle explicit | Verified in recorded scope | [backend-isolated-assessment.json](backend-isolated-assessment.json); [retrieval-results.json](retrieval-results.json) |
| REQ-008 | Expose staleness and applicability | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-009 | Capture useful knowledge selectively | Verified in recorded scope | [end-to-end-results.json](end-to-end-results.json); [core-results.json](core-results.json) |
| REQ-010 | Reserve handoff memories for lasting context | Verified in recorded scope | [core-results.json](core-results.json) |
| REQ-011 | Validate project memory configuration | Verified in recorded scope | [root-validation.json](root-validation.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-012 | Enforce project and path isolation | Verified in recorded scope | [root-validation.json](root-validation.json); [backend-root-results.json](backend-root-results.json) |
| REQ-013 | Define an explicit source corpus | Verified in recorded scope | [backend-isolated-assessment.json](backend-isolated-assessment.json); [retrieval-results.json](retrieval-results.json) |
| REQ-014 | Distinguish memory results from source evidence | Verified in recorded scope | [end-to-end-results.json](end-to-end-results.json); [backend-root-results.json](backend-root-results.json) |
| REQ-015 | Provide a deterministic lexical fallback | Verified in recorded scope | [root-validation.json](root-validation.json); [end-to-end-results.json](end-to-end-results.json) |
| REQ-016 | Evaluate combined exact and conceptual retrieval | Verified in recorded scope | [backend-root-results.json](backend-root-results.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-017 | Preserve strict read-only behavior | Verified in recorded scope | [root-validation.json](root-validation.json); [end-to-end-results.json](end-to-end-results.json) |
| REQ-018 | Separate inspection from maintenance operations | Verified in recorded scope | [backend-isolated-assessment.json](backend-isolated-assessment.json); [core-results.json](core-results.json) |
| REQ-019 | Keep secrets and source instructions out of authority | Verified in recorded scope | [backend-root-results.json](backend-root-results.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-020 | Apply the agreed publication authority | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-021 | Keep child outputs as proposals | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-022 | Prevent alternate backend publication routes | Verified in recorded scope | [end-to-end-results.json](end-to-end-results.json); [backend-root-results.json](backend-root-results.json) |
| REQ-023 | Publish single-record changes without lost updates | Verified in recorded scope | [core-results.json](core-results.json) |
| REQ-024 | Recover multi-record lifecycle changes accurately | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-025 | Keep Task and memory publication boundaries separate | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-026 | Classify rebuildable state and recovery data | Verified in recorded scope | [backend-root-results.json](backend-root-results.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-027 | Preserve TeX as research evidence | Verified in recorded scope | [retrieval-results.json](retrieval-results.json) |
| REQ-028 | Preserve PDF provenance and extraction limits | Verified in recorded scope | [retrieval-results.json](retrieval-results.json) |
| REQ-029 | Preserve useful HTML structure | Verified in recorded scope | [retrieval-results.json](retrieval-results.json) |
| REQ-030 | Keep derived representations attributable | Verified in recorded scope | [backend-isolated-assessment.json](backend-isolated-assessment.json); [retrieval-results.json](retrieval-results.json) |
| REQ-031 | Freeze shared memory before independent solvers | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-032 | Prevent sibling information leakage | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-033 | Bound additional retrieval during independent work | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-034 | Apply material memory changes through existing gates | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-035 | Use existing Task interfaces and preserve history | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-036 | Preserve fresh role discovery | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-037 | Preserve real manager ownership and stopping evidence | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-038 | Preserve category teams and effective settings | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-039 | Keep memory free of Task lifecycle side effects | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-040 | Deliver a complete reusable memory package | Verified in recorded scope | [core-results.json](core-results.json); [final-template-contract-results.json](final-template-contract-results.json) |
| REQ-041 | Integrate existing guidance and role responsibilities | Verified in recorded scope | [final-template-contract-results.json](final-template-contract-results.json) |
| REQ-042 | Publish through the actual Template pipeline | Verified in recorded scope | [final-template-contract-results.json](final-template-contract-results.json) |
| REQ-043 | Keep Template memory empty | Verified in recorded scope | [root-validation.json](root-validation.json); [initializer-results.json](initializer-results.json) |
| REQ-044 | Initialize a distinct new-project capability | Verified in recorded scope | [root-validation.json](root-validation.json); [initializer-results.json](initializer-results.json) |
| REQ-045 | Preserve existing memory and prior setup editions | Verified in recorded scope | [root-validation.json](root-validation.json); [initializer-results.json](initializer-results.json) |
| REQ-046 | Record memory starter adoption factually | Verified in recorded scope | [root-validation.json](root-validation.json); [initializer-results.json](initializer-results.json) |
| REQ-047 | Document ownership, dependencies, and exact paths | Verified in recorded scope | [root-validation.json](root-validation.json); [final-template-contract-results.json](final-template-contract-results.json) |
| REQ-048 | Adopt the reviewed capability into the active root | Verified in recorded scope | [root-validation.json](root-validation.json); [end-to-end-results.json](end-to-end-results.json) |
| REQ-049 | Keep dependency ownership explicit | Verified in recorded scope | [root-validation.json](root-validation.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-050 | Define a controlled Basic Memory profile | Verified in recorded scope | [backend-root-results.json](backend-root-results.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-051 | Preserve metadata across the adapter | Verified in recorded scope | [backend-root-results.json](backend-root-results.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-052 | Exercise the backend compatibility pilot | Verified in recorded scope | [end-to-end-results.json](end-to-end-results.json); [backend-root-results.json](backend-root-results.json) |
| REQ-053 | Make backend enablement conditional on evidence | Verified in recorded scope | [end-to-end-results.json](end-to-end-results.json) |
| REQ-054 | Separate runtime provisioning from reads and setup | Verified in recorded scope | [backend-isolated-assessment.json](backend-isolated-assessment.json); [retrieval-results.json](retrieval-results.json) |
| REQ-055 | Review the selected backend's operational fit | Verified in recorded scope | [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-056 | Verify deterministic contracts and preservation | Verified in recorded scope | [root-validation.json](root-validation.json); [backend-isolated-assessment.json](backend-isolated-assessment.json) |
| REQ-057 | Verify native and integrated memory use | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-058 | Preserve history during correction and migration | Local tests; live runs excluded | [host-testing-scope.json](host-testing-scope.json); [host-testing-results.json](host-testing-results.json) |
| REQ-059 | Report release evidence at its actual level | Verified in recorded scope | [acceptance-matrix.md](acceptance-matrix.md); [authority-and-adoption.md](authority-and-adoption.md) |

Current required checks pass in [final validation](final-validation.json). Backend prerequisites, selected licenses, package/model sizes and measured limits are retained in the [isolated operating report](backend-operational-fit.md) and [root operating report](backend-root-operating-fit.md). Results apply to the inspected host, versions and bounded corpora. Large/scanned research corpora and other platforms were not established.

The planned `tests/fixtures/research` directory contains the exact reusable TeX and HTML samples. Tests load these samples from each installed package and generate the PDF fixture in a temporary project. State-path contracts are published in the reusable collection and installed references. Publication controls are a cooperative workflow and guarded adapter, not an OS security sandbox.
