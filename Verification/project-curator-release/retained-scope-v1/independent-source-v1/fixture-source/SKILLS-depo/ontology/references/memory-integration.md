# Memory integration

Ontology owns this adapter; it changes no memory schema, configuration, record,
capture setting, corpus, publisher or backend choice. The adapter locates the
selected project's installed `.agents/skills/memory/scripts/` package and calls
its actual `memory_core.load_config`, `load_record`, `load_records` and
`memory_search.search` public interfaces in a separate Python import process.
Frozen searches use the existing `memory_packet.search_packet` route through
`memory_search.search(packet=...)`. No alternate memory store is constructed.

Memory and ontology project IDs must agree. Ontology requests deterministic
lexical memory retrieval and explicitly reports that mode; it does not start or
certify an optional backend. An absent package or configuration, identity
mismatch, rejected memory evidence or failed memory inspection returns an
unavailable limitation while independent ontology results remain usable.
Frozen packet failures are errors and cannot become live fallback searches.

Query expansion retains the original query, then up to eight total queries
from resolved approved concept labels, aliases and one-hop related vocabulary.
The installed memory interface controls corpus access and lifecycle. Only active
memory records with no unresolved evidence diagnostics become historical
results. Drafts, excluded child content and stale/unqualified evidence do not
become verified history. No matching eligible record returns
`no_matching_historical_evidence`. Returned record IDs, note/source hashes,
limits, match routes and limitations remain visible.

`link-memory` is an explicit derived build. Repeated `--record` paths select
exact canonical memory records; with none, the installed memory interface lists
accessible active records. Repeated `--concept` arguments request associations;
with none, the builder detects exact labels/aliases mentioned in each record.
Unambiguous matches receive `derived_association`, overloaded labels receive
`ambiguous` with candidate IDs, and unknown associations receive `unmatched`.
This never changes a canonical concept or inserts an `ontology_refs` field in
memory-v1 records.

The deterministic sidecar at `.sys4ai/ontology/links/memory-records.json` retains
record/source versions, ontology snapshot, association status and provenance.
Readers check both its ownership digest and current record/ontology versions.
Changed or hand-edited inputs make the sidecar stale; stale associations are
not returned as current evidence. Only another explicit build can refresh them.
Memory publication and ontology publication remain separate granted operations.
Existing memory recovery and Task frozen-input restrictions remain controlling.
