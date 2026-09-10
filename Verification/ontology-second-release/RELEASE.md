# Ontology knowledge system: second release

Implementation for `PLAN-20260909-4B15BB49`, revision 2, is complete in the
Sys4AI depot and its registered Template. The [requirement audit](requirement-audit.json)
maps all 44 requirements and 135 acceptance criteria to the delivered artifacts
and observed evidence. The [final status](final-status.json) binds the
[file manifest](final-manifest.json), including the exact root adoption chain.
Both independent guard findings are resolved in the
[final review](guard-correction-review.json).

The release adds a confined RDF/SPARQL/SHACL backend, finite formal inference
with source and rule explanations, native-agent proposal generation and exact
review/publication, independent optional ontology embeddings, action guards,
and a local browser workbench. The locked first-release core remains version
1.0.0; advanced capability is version 2.0.0. Initializer version 11 supplies the
neutral `governance-starter-v9` edition and explicit prior-edition adoption.

The selected standards environment uses RDFLib 7.6.0, pySHACL 0.40.1, and
owlrl 7.6.2, with exact package and worker hashes. The semantic environment
uses FastEmbed 0.8.0 and the separately prepared BAAI/bge-small-en-v1.5 ONNX
model at revision `52398278842ec682c6f32300af41344b1c0b0bb2`.
Core lookup, validation, and wiki generation need neither environment.

| Capability | Observed evidence |
| --- | --- |
| Standards and confinement | [Actual worker, query, graph, shape, and access-control results](standards-acceptance.json) |
| Formal inference | [Rules, premises, property inference, contradiction, and limits](reasoning-acceptance.json); [final installed root inference](root-inference-final.json) |
| Native proposal generation | [Two actual native runs, finding-directed revision, stale rejection, and reopened publication](generation-acceptance.json) |
| Semantic retrieval | [Root comparison](root-retrieval-comparison-final.json); [actual-model frozen-packet verification](semantic-packet-acceptance.json) |
| Action guards | [48 passing cases across eight helper families and 44 installed public boundaries](dispatch-acceptance.json); [shared deadline and cancellation](guard-deadline-acceptance.json) |
| Browser authoring | [Actual browser editing, validation, conflict, review, publication, and reopening](browser-acceptance.json); [final guard publication](browser-guard-correction-acceptance.json); [root browser inspection](root-browser-acceptance.json) |
| Native solver context | [Actual manager, independent solvers, materiality assessment, same-ID rebinds, and senior acceptance](native-context-evidence.json) |
| Destination setup | [New, first-prepared, populated, customized, and interrupted destination cases](destination-matrix.json) |
| Preservation | [Exact protected-file audit](preservation-audit.json) |
| Distribution | [300 managed Template files and 203 inspected root package files](template-distribution.json) |
| Integrated result | [Generation, retrieval, inference, authoring, solver context, and installed destinations](integrated-acceptance.json) |

The [final test summary](verification-summary.json) records 153 ontology tests:
152 passed, and the opt-in actual-model test was skipped in that suite and
passed separately using the installed model. All 17 repository checks, 11
Template contract checks, 10 installed initializer destination cases, and four
root intake policy checks passed. The original initializer suite passed 109
of 110 cases, with one simultaneous case-equivalent-directory fixture skipped
on this filesystem. Earlier failed or interrupted logs retain their original
outcomes and versions.

The corrected guards inspect actual typed inputs, targets, lifecycle state,
capabilities and current source bindings before invoking the owning helper.
All backend phases share one deadline and cancellation signal. The final
browser edit was reviewed, published and reopened with the corrected engine;
its publication receipt records a 0.5039-second guard evaluation within the
five-second budget. Repeated unchanged previews retain an identical digest.

On the six-case installed-root retrieval comparison, lexical retrieval found
the expected answer in the first five results for three cases; semantic
retrieval did so for five. Both returned the expected first result for three
cases. The report retains false positives and neutral results. These observed
results establish neither general accuracy nor semantic equivalence.

Run the core check from the depot with:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -S .agents/skills/ontology/scripts/check_ontology.py --project-root .
```

[The installed command reference](../../.agents/skills/ontology/references/commands.md)
describes profile selection, explicit provisioning, inference, SPARQL, SHACL,
proposal capture and review, semantic index builds, and the loopback workbench.
[The verification contract](../../.agents/skills/ontology/references/verification.md)
distinguishes fixture tests from actual native and browser acceptance.
The workbench requires a current trusted native authority observation for an
authoring session. A browsing session grants no publication authority.

The verified worker confinement is Darwin-specific. The finite rule profile
does not claim full OWL 2 RL coverage. Native-agent filesystem scope is
cooperative; the acceptance report discloses the initial solver's style-file
read exception. Guards cover the declared project helper interfaces, with
their existing transactions and authorizers, and do not intercept arbitrary
shell commands or third-party tools. No cross-system atomicity is claimed.

The registered Template remains neutral and contains no depot ontology
instances, generated proposals, indexes, or prepared models. No ordinary
product project was adopted. Git commits, pushes, PRs, hosted deployment, and
non-Darwin certification were not part of this local implementation.

All 4,612 protected baseline files remain byte-for-byte unchanged, including
the locked core and existing canonical memory and Task history. Ignored old
runtime trees have unchanged-timestamp corroboration; no missing baseline
content hashes are claimed. The Template watcher is ready with a fresh
successful check from its current PID. The temporary acceptance workbench
services and tabs were closed after verification; profile enablement does
not imply that a server is left running.

Canonical plan/TRD status and root Task history remain unchanged. The evidence
in this directory records implementation and acceptance independently of those
lifecycle records. The [completion learning checkpoint](completion-checkpoint.json)
retains implemented lessons in tests while preserving existing canonical memory.
