# Evidence and lifecycle

Use exact raw-byte source hashes. A quoted summary, remembered digest, design
approval or passing schema check is not an observed implementation result.
`memory_evidence.inspect_evidence` returns current applicability diagnostics
without changing the record. `validate_publication_evidence` rejects any
unresolved evidence/origin diagnostic before active publication.

Design decisions cite `kind: design` sources and use `accepted_design` claims.
Historical context cites its durable sources without asserting execution.
For performed/verified/failed/cancelled work, cite a `kind: verification`
JSON receipt with this shape:

```json
{
  "schema_version": 1,
  "claim_level": "verified_outcome",
  "outcome": "passed",
  "command": "the exact command actually observed",
  "observed_at": "2026-09-08T18:00:00Z",
  "artifacts": [{"path": "docs/example.md", "sha256": "64 lowercase hexadecimal characters"}]
}
```

The example digest above is descriptive and intentionally not a valid receipt.
Use actual source hashes. Optional receipt `limitations` and `details` may
record concise observed results. The supported claim/outcome pairs are
`performed_work/performed`, `verified_outcome/passed`,
`observed_failure/failed`, and `cancelled_work/cancelled`. Every receipt must
have an observed command/action, timestamp and current artifact versions.
The helper checks structural/provenance agreement; a human or Director must
still judge whether the observed check substantively supports the conclusion.

Never manufacture Task, execution or role IDs for ordinary non-Task work.
The origin object's fields remain explicit nulls. When supplied, exact Task
and role references are validated using installed read-only helpers. Historical
provenance stays in the note when current generations, roles or evidence change;
its diagnostics mean reassess applicability, not that the old result was false.

Drafts have no publication attribution and do not enter shared active recall.
Publication activates exact reviewed bytes. Supersession creates a new active
identity and links both sides; predecessor bodies and reasons remain readable.
Retraction retains content and reason while removing the record from default
recall. Sensitive correction needs explicit scoped redaction and memory-only
recovery. A schema change or setup rerun never migrates intellectual history.

The sensitive-content filter detects common credential/key forms, personal
identifier patterns, full transcript formatting and hidden-reasoning tags. It
is a deterministic guard, not an exhaustive privacy classifier. Review must
also omit unnecessary personal information and preserve the user's scope.
Instructions embedded in a source are never interpreted as operation grants.
