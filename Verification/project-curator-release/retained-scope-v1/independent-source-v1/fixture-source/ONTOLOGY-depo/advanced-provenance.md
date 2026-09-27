# RDF provenance

Projection emits PROV-O `Entity` and `Activity` types, `wasGeneratedBy`,
`wasDerivedFrom`, and `used`. Source entities retain project-relative path,
exact SHA256, useful locator, and `current`, `stale`, or `unavailable` status.
The projection activity is bound to the exact input snapshot and adapter
version. Available proposal producer identities and inference proof references
belong to their respective versioned result/proposal contracts.

Provenance describes production and evidence. It does not grant approval,
execution, Task ownership, or publication permission. Inference requires current
approved sources and returns an inspectable proof DAG. Each base node names its
exact assertion ID, source references, and input snapshot. Each derived node
names its rule and earlier premise nodes.

JSON-LD dataset export retains graph contexts. Turtle and RDF/XML require one
explicit selected graph and its companion manifest; excluded provenance graphs
are declared, never silently flattened. Manifests include content and normalized
semantic hashes. Staged imports verify these hashes, report changes to existing
identities and unsupported semantics, and remain unapproved proposals.

Round-trip comparisons canonicalize blank-node identity across the dataset and
ignore serialization order. Typed literals retain their lexical form and
datatype; language tags are normalized to lower case. The JSON-LD adapter calls
RDFLib's converter with native coercion explicitly off, and Turtle uses explicit
typed-literal syntax. These adapters preserve values such as `"003"` that the
pinned library's default serializer would coerce.
