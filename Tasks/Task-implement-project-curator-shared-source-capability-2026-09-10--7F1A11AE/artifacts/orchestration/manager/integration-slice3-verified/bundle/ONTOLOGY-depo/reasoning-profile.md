# Finite reasoning profile v1

This release provides deterministic forward rules for named classes,
subproperties, class/property equivalence, inverse properties, declared
symmetric/transitive properties, and approved named-individual equality. The
exact rule table is [`rules/finite-profile-v1.json`](rules/finite-profile-v1.json).
It is a selected finite subset, not a claim of full OWL 2 RL conformance.

Only approved asserted v1 records with current exact sources and approved
selected extension axioms enter the premises. Drafts, similar labels, annotation
text, inferred records, and external facts do not supply approved premises.
Selected premise IDs restrict both positive and explicit negative assertions.
Locked core identity is retained; extensions cannot redefine core semantics.

An instance typed as a project `GeneratedWikiPage` becomes an `Artifact` when
an approved compact `subtypeOf` declaration supplies that hierarchy. The
conclusion identifies the exact type assertion, hierarchy assertion, and
`cax-sco` rule. The original assertions remain unchanged.

Disjoint types/properties, explicit negative assertions, and equality that
conflicts with `differentFrom` produce actionable conflict reports. A complete
but inconsistent run marks all conclusions untrusted. Absent facts remain
`unproven`; an explicitly negated queried fact is `contradicted`. Unsupported
axioms, blank-node class expressions, and equality over class/property objects
fail explicitly. No inference result supplies operational authorization.

Each proof node has a stable hash identity, its conclusion triple, the rule ID,
and references to earlier proof nodes. Base nodes also retain approval, assertion
and record IDs, source hashes/locators, and the input snapshot. First derivations
are deterministic. `ontology_derivations.for_conclusion` selects an exact proof
chain; `verify` checks DAG structure. Frozen consumers can replay
`ontology_reasoning.infer` on their frozen base premises and negative assertions
to validate rule semantics without reading live sources or starting a backend.

Rounds, derived triples, proof nodes, time, resident memory, output, and
cancellation are bounded. A limit returns incomplete status and cannot be used
as complete closure. Fixed input and rule versions produce equivalent facts and
normalized proofs. `ontology_standards.freshness` compares current exact inputs
with an earlier result; any change invalidates that result. Live inference never
replaces a frozen solver packet.

The pinned OWL-RL engine is a differential oracle for supported positive cases.
Its extra axiomatic/datatype conclusions are not imported as unexplained trusted
facts. Runtime acceptance checks compare the finite engine's inferred positive
triples to actual OWL-RL closure.
