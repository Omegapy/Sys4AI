# Optional standards and inference API

All functions accept an explicit project root. Core Python imports none of the
optional packages. The public module `ontology_standards.py` supervises the
actual selected backend in an OS-confined subprocess.

```python
health(root)
dataset(root, graphs=["asserted", "derived"])
query(root, "SELECT ?s WHERE {?s ?p ?o} LIMIT 10", graphs=["asserted"])
validate(root, graphs=["asserted", "derived"])
infer(root, goals=[[subject_iri, predicate_iri, object_iri]], premise_ids=None)
infer_diagnostic(root, goals=[], premise_ids=None)
export(root, "json-ld")
export(root, "json-ld", include_inferred=True)
export(root, "turtle", selected_graph="asserted")
stage_import(root, text, "turtle", manifest=context_manifest)
freshness(root, previous_result)
```

`validate` also accepts exact Turtle `shapes` and explicit `triples` for guarded
action validation. It runs pySHACL with inference, JS, imports, and advanced
executable extensions disabled. Reports distinguish `conformant`, `violation`,
unsupported features, and processing failure. The authoring path combines
manifested shapes and exact per-record endpoint/cardinality constraints with
core validation. Generated NodeShapes group only identical complete constraint
sets and retain every original targetNode. Inferred graphs cannot supply missing approval or provenance.

Generated membership lists use deterministic named RDF cells with identical
ordered suffixes shared within one call. Every member and list order remains
intact; meta-SHACL still validates their first/rest structure. Named cells avoid
repeated rendering of anonymous list tails in intermediate validator reports.

`query` supports SELECT, ASK, CONSTRUCT, and DESCRIBE. It parses SPARQL, resolves
prefixes, rejects Update and SERVICE, and restricts FROM/FROM NAMED to already
selected local graph IDs. Parsed dataset clauses are removed before execution
against a constructed in-memory selection, preventing retrieval. The default
graph is the union of explicitly selected scopes. DESCRIBE uses RDFLib's concise
bounded description including reachable blank-node objects. Unordered SELECT
bindings and graph results are normalized. Explicit ORDER BY order is retained;
ties follow SPARQL's unspecified ordering. RAND, NOW, UUID, STRUUID, BNODE, and
unselected custom functions are outside the repeatable query profile.

Results include `status`, `complete`, exact `context`, backend `versions`, and
worker measurements. Partial results are explicit non-success states. Optional
`limits` can lower the project budgets; a `threading.Event` passed as `cancel`
can cancel an active worker. `expected_snapshot` rejects old approved input.
Preview `overrides` accepts exact bytes for selected core/extension files and
their companion locks; the result is marked `context.preview = true`.

`export` returns content plus a context/provenance manifest. The owning CLI must
select a destination and overwrite expectation explicitly. `stage_import`
returns attributed, unapproved proposal data; the owning proposal workflow
persists and reviews it. Neither function writes canonical files.
Selecting the inferred graph, or explicitly setting `include_inferred=True`,
runs complete trusted inference and includes its PROV-O proof links. Disabled
inference or an incomplete/conflicting closure fails that selection explicitly.

Explicit setup uses
`ontology_profiles.setup_profile(root, "standards", provision=True)` to install
the complete wheel-hash lock in the independent environment and execute host
certification. `provision=False` only certifies an existing selected runtime.
Reads never invoke setup. `preview_profile` prepares an exact enable/disable
change. `configure_profile` requires current native destination-local Director
authority, exact selected config hash/profile/value, and no overlapping manager.
It preserves all other profiles and publication binding. An enabled guard
requires the owning guard repair workflow instead of this direct setup path.
Profile setup retains an exact pre/post intent and completion receipt; a retry
reopens those bytes and requires current authority before completing a partial
receipt. A disabled or absent companion reports runtime presence separately
from dependency readiness and enablement.

Primary backend references: [RDFLib source](https://github.com/RDFLib/rdflib),
[pySHACL](https://github.com/RDFLib/pySHACL), and
[OWL-RL](https://github.com/RDFLib/OWL-RL). The locked versions and actual runtime
receipts determine delivered behavior.

`infer_diagnostic` computes the same complete selected closure, negative assertions
and conflicts as `infer` inside the same confined worker and unchanged budgets.
Its explicit schema-1 diagnostic returns counts and canonical SHA-256 digests for
selected premises, negatives, inferred triples, proofs, conflicts and provenance.
It retains completeness, trust, failures and bounded goal classifications.
`reasoning_scope` is `full_selected_closure` only without a premise subset;
otherwise it is `selected_premise_closure`. `proof_detail` is always
`counts_and_digests_only`. It delivers no full proof arrays. Digest counts on an
incomplete result describe only that incomplete result; unavailable evidence is
null. The operational health inference probe selects this diagnostic explicitly
and reports that full proof delivery was not exercised. Default full `infer`,
publication, knowledge retrieval and frozen proof replay retain their full proof
contract and truthful `output_limit` when full detail exceeds the response budget.
For proof detail call `infer` with exact premise/record IDs and goals; that query
proves only its selected premise scope, not the complete project closure.
