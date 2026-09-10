# Verification and competency checks

Run the combined standard-library entry point on the exact selected root:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python .agents/skills/ontology/scripts/check_ontology.py --project-root "$PWD"
```

The source equivalent is `SKILLS-depo/ontology/scripts/check_ontology.py` and
`SKILLS-depo/ontology/tests`. The command runs structural validation and
competency questions together, returns nonzero if either fails, and reports
exact configuration, module, canonical/source and helper versions. If unsafe or
unparseable inputs prevent a graph from loading, competency execution is
explicitly unavailable, never a passing empty check. There is no requirement for
hosted CI, an external service, an LLM or a new workflow provider.

Each selected module owns a manifest-declared `competency.json`. Project
extensions may add exact local files through `ontology.yaml`'s
`competency_files` array without changing the shared core. The suite schema is
`{"schema_version":1,"questions":[...]}`. A question has `id`, `intent`, `query`
and one or more observable expectations: `expected_ids`, `expected_terms`,
`expected_relations` (subject/predicate/object objects), `expected_sources`,
`expected_status` or `absent_ids`. Expectations compare actual query output;
an LLM opinion is not a pass condition. Query truncation fails a competency
question so absent evidence is not concealed by a context bound.

The initial suite covers core meanings and operational distinctions; selected
project questions test actual installed skill/role bindings and factual
registry relationships. Structural negative cases cover unsafe contexts/paths,
duplicate IDs, dangling targets, vocabulary ambiguity, metadata/provenance,
domain/range, cardinality and declared acyclicity. Query tests additionally
cover determinism, byte/timestamp preservation, graph bounds, stale sources,
generated link integrity, real memory interfaces and existing Task artifact
compatibility. Native agent dispatch remains a separate observed acceptance
step, distinct from synthetic deterministic fixtures.

## Advanced acceptance

The complete test suite now includes actual standards workers. Explicitly
prepare and certify the selected standards environment before running it:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" profile-setup standards --provision
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s .agents/skills/ontology/tests -v
```

The setup command installs only its pinned standards environment. Profile
enablement, semantic package/model preparation, index builds, and workbench
startup remain separately selected operations. The core checker above needs
none of them. A missing backend cannot count as a passing advanced acceptance.

`test_advanced_standards.py` groups actual worker confinement, RDF datasets,
PROV-O provenance, interchange, SPARQL, SHACL, finite rules, proof replay,
conflicts, cancellation, limits, and stale-input cases. `test_guarded_dispatch.py`
exercises every declared owning helper boundary, all eight action families, and
changes inside their existing locks. Its fixture native receipts are explicitly
synthetic. The guard setup requires exact installed adapter evidence separately
from a current real native authorizer.

`test_proposals.py`, `test_advanced_publication.py`, and
`test_generation_contract.py` group durable revisions, semantic impact,
finding-directed refinement, exact approval, rejection, and partial recovery.
`test_workbench_security.py` checks the real HTTP service, including shared
browser cookie isolation, conflicts, read-only sessions, and authority/source
boundaries. Actual browser operation and actual native generation are separate
release gates; an HTTP test or a prewritten candidate is not a substitute.

The explicit actual-model packet check copies an already prepared local semantic
runtime into a disposable test project. It does not download or enable one:

```text
SYS4AI_SEMANTIC_ACCEPTANCE_ROOT="$PWD" PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s .agents/skills/ontology/tests -p test_semantic_packet.py -v
```

That case registers identical captured vectors through the existing Task
artifact interface and checks that frozen queries invoke no live model.
`test_advanced_memory.py` exercises actual inference and the memory v1 reader in
an explicit advanced mixed query, retaining definitions, historical memory,
inferences, and proposals as separate source types. Tests preserve their host
process's module identities after switching into installed fixture packages.

Release evidence must bind current source/root/Template versions, actual backend
and native/browser observations, exact adoption and publication receipts, and
before/after protected state. Record supported-host and cooperative dispatch
limits explicitly. Core tests, selected installation, enabled profiles, valid
guards, actual execution, and unchanged canonical history prove different facts.
