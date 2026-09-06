# Base memory profile

`profile.yaml` is the versioned `base@1` profile required by the public memory
contract. It declares only the common record types, relations, source adapters,
and deterministic capability requirements. It does not authorize a model,
network listener, durable write, retention period, export policy, or shared
backend.

The loader rejects unknown fields, duplicate definitions, missing parents,
inheritance cycles, incompatible API ranges, disabled required capabilities,
unsafe local references, and representation conflicts. A representation change
requires a rebuild or a versioned migration before activation.

An `IngestionSynchronizer` may bind synchronization to a loaded `ProfileSet`.
In that mode, each source must select a profile in the active set, its adapter
must be declared by that profile or an ancestor, and every emitted record type
must belong to the same profile lineage. The selected profile version is
written into normalized provenance. Missing profiles and undeclared runtime
material fail with `PROFILE_INCOMPATIBLE` before provider persistence.

Extensions use the same required fields and may also declare
`lexical_fields` on record types plus `retention_policies`,
`context_assembly_rules`, `reranking_rules`, and `instructions`. The existing
`retrieval_strategies` field is the query-strategy declaration. Write,
retrieval, retention, context, reranking, and instruction references carry an
`authority_tier`; an omitted tier defaults to `A7`.

The profile file cannot grant its own authority. A trusted caller supplies a
`ProfileSourceAuthority` to the loader from canonical registry or permission
state. The loader rejects any behavior reference whose tier is more privileged
than that external source grant, includes the grant in the profile-set
fingerprint, and applies the untrusted `A7` ceiling when no grant is supplied.
Evaluation references do not execute instructions and do not trigger a rebuild
when they are the only changed declaration.

A neutral temporary integration fixture proves the generic extension seam. The
tracked `software-engineering@1` extension is the approved product proof: its
adapter and record types sync and serve two agent identities through the
unchanged public API.
