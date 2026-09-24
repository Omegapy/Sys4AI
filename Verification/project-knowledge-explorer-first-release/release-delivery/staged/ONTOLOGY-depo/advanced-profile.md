# Advanced ontology profile v1

The second release retains `ontology.yaml`, compact record v1, vendored context,
and locked core module bytes. `ontology-advanced.yaml` is a separate strict JSON
subset of YAML. Unsupported versions or fields fail explicitly. The executable
reader is `ontology_advanced.load_advanced`; the schemas describe the same public
structure. The neutral configuration is
[`profiles/ontology-advanced-v1.json`](profiles/ontology-advanced-v1.json).

Profiles select standards, inference, semantic retrieval, guards, and the
legacy workbench configuration separately. The workbench service is retired;
its retained profile does not enable Explorer. A disabled or absent profile leaves core operations
available. A selected enabled profile with absent or incompatible dependencies
reports that state. Reading a profile, query, validation, inference, or document
does not install packages, prepare a model, start a service, or enable a profile.

Standards use the independently provisioned `.venv-ontology-standards` Python
3.12 environment. The exact wheel and transitive package hashes are in the
ontology skill's `requirements-standards.txt` and `profiles/standards-v1.json`.
The runtime is usable only with a current host certification covering actual
file/network denial, parser attempts, memory/time/cancellation termination,
bounded output, malformed IPC, and worker failure. Certification binds worker
code, installed package bytes, and the interpreter. It must be renewed after
those inputs change. This implementation certifies Darwin only.

Approved extension JSON belongs under `ONTOLOGY/extensions/`. The companion
selects each exact path and SHA256. Each extension has schema version 1, a unique
project ID, semantic version, project identity, and `axioms`, `annotations`, and
`negative_assertions` arrays. Each statement has a unique project ID, subject,
predicate, object, and exact selected source references. Optional `shapes`
select exact local Turtle files. Statements cannot redefine locked core IDs or
another project's semantics. An extension's exact selected canonical bytes are
the approved source; a draft or preview is identified separately and acquires
no publication permission.

An RDF term is an absolute IRI string or a literal object containing a string
`value` and either `datatype` or `language`. Annotation statements retain typed
and language-tagged values without adding fields to compact v1 records. Formal
equality and class/property declarations belong in `axioms`, never annotations.
The extension does not permit executable code or custom functions. Valid RDF
syntax supplies no trust or approval.

The optional `publication` binding has `enabled` and `binding`. Its binding
names a destination-local actor, the exact scopes `ontology-advanced.yaml` and
`ONTOLOGY/extensions`, and the current `SOUL.md`, `AGENTS.md`, and `ROLE.md`
digests. This grants no core, memory, Task, or external authority by itself.
Semantic publication may change selected extension bytes and their existing
companion locks only. Profile/authority changes use separately selected setup.

RDF projection maps compact instance types directly to `rdf:type`. A compact
`subtypeOf` relation maps explicitly to `rdfs:subClassOf`; other named
relationships retain their predicate identity. Concept records also identify
RDFS classes. Descriptive v1 metadata remains under the core `field:` namespace;
domain/range constraints are validated as authoring constraints, not silently
converted into additional OWL entailments.

The in-memory Dataset identifies `asserted`, `derived`, `inferred`, and
`external` graphs as `urn:sys4ai:ontology:graph:<project-id>:<kind>`. Selected
project modules/bindings and exact extensions supply the dataset. A link does
not load another project. Projection and queries do not write a persistent
alternative authoring graph. Context binds canonical inputs, selected sources,
module versions, companion/extension digests, profile and rule/shape versions.

Durable proposals remain under `ONTOLOGY/proposals/`; reviewed approvals and
publication/recovery records remain under `control_records/ontology/`. Derived
graphs, closures and indexes belong under `.sys4ai/ontology/`. Rebuilding a
derived product must not delete a proposal, receipt, canonical record, or memory
history. Runtime certification/worker capacity slots live in the selected
standards environment and are neither authored semantics nor authority.
