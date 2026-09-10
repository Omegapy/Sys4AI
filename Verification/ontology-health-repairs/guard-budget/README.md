# Five-second guard decision repair

The original required v2 guard case exhausted its shared five-second deadline
after its final backend returned conformance. The measured decision took
5.0187 seconds. The dataset worker alone consumed 3.2675 seconds; all eight
preparations together consumed 0.2058 seconds, and four complete package
fingerprints consumed 0.1397 seconds.

A confined worker measurement located the cost in `ontology_rdf.quad_rows`:
normalizing 1,629 quads took 2.9176 seconds although none contained an RDF blank
node. The original algorithm created temporary blank nodes for every quad and
canonicalized those invented identities. Direct encoding and stable sorting
of URI/literal terms took 0.02085 seconds and returned exactly the same quads
and semantic hash.

The small source change uses that direct path only when the entire dataset has
no blank nodes. The original blank-node branch remains byte-identical, including
its shared identity handling across named graphs. No cache, deadline increase,
guard semantic change, test relaxation or skipped safety check was introduced.

The repaired decision takes 2.1771 seconds in the final profile and 2.1551 seconds
in the unchanged required deadline test. All four existing deadline tests pass,
including actual cancellation and rejection of a late conformant result before
owner invocation. The isolated original failure case also passes unchanged.

- [Result and exact source hashes](result.json)
- [Complete original phase profile](baseline-profile.json)
- [Complete repaired phase profile](after-profile.json)
- [Exact dataset worker comparison](dataset-comparison.json)
- [Six original/repaired RDF identity controls](rdf-equivalence.json)
- [Two shipped RDF regression tests](rdf-tests.log)
- [All four unchanged deadline tests](deadline-suite.log)
- [Observed deadlines and owner exclusion](deadline-evidence.json)
- [Revalidated source runtime certificate](source-runtime-certification.json)
- [Minimal source diff](source-change.diff)

The earlier source runtime certificate is retained by its canonical SHA256
under the disposable runtime's existing certification history. Its new
certificate binds the final RDF helper. No active root runtime or installation
was changed by this assignment.

The scripts in this directory recreate disposable fixture inputs and retain
finite worker supervision. `profile_guard.py after-profile.json` measures the
current source decision; `profile_dataset.py` compares the frozen original RDF
helper against the direct serialization candidate. `compare_rdf.py` checks
ground, blank-node, reordered, empty and named-graph inputs through both actual
workers. Select the explicitly certified source runtime using
`SYS4AI_STANDARDS_PYTHON` from `result.json` before running them.
