# Evidence and lifecycle

Use exact raw-byte source hashes. A quoted summary, remembered digest, design
approval or passing schema check is not an observed implementation result.
`memory_evidence.assess_evidence` separates historical support, current
applicability, retained durability and verified-current qualification. The legacy
`inspect_evidence` interface still returns a diagnostic list without changing the
record. `validate_publication_evidence` rejects any
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
have an actually observed command/action, timestamp and exact artifact versions.
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


## Durable verified claims and compatibility

Record schema v1 is unchanged. A new or renewed `verified_outcome` publication
uses receipt schema v1 with explicit `"applicability": "current"` and adds a
`retained_path` to every artifact reference. That path names a distinct retained
copy beneath `Verification/` or `control_records/memory/evidence/`, whose exact
bytes match the original artifact's `sha256`. The receipt itself remains bound
by its source path and raw-byte digest. The receipt's limitations describe the
scope of the actual check; successful structural validation cannot substitute for
observing the command and judging the evidence.

The owning workflow retains only selected, reviewed, permitted bytes under its
existing evidence write scope. The reader never creates an archive or refreshes
a hash. Symlink, hardlink, alias, secret-path, privacy, source-size and project
boundary checks continue to apply. A receipt has at most 200 artifacts and at
most 16 MB of retained artifact bytes. Text retention passes the existing privacy
filter; PDF bytes retain the existing extraction/review limitation.

A matching current file can support a legacy receipt, but legacy receipt readers
report `durable: false` unless exact retained copies are referenced. Changed live
bytes without accessible matching retained evidence remain historical-unsupported
and current-changed/unverified. Changed live bytes with intact retained proof
remain historically supported and current-changed. Missing or tampered selected
archives remain diagnosed even when live bytes happen to match. The assessment
reports each affected artifact path and safe expected/current digests. It never
asserts that later changes make the old observation false.

New verified publication requires current live versions as well as retained proof.
An explicitly historical receipt cannot establish `verified_current` or silently
renew an active verified claim. Historical-only disposition uses the existing
`historical_context` successor and supersession route: preserve the predecessor's
body, original claim, receipt/hash provenance and reason. `historical_context`
asserts context from exact cited sources; it does not claim current verification.
Superseded/retracted records remain inspectable with their diagnostics and are
excluded from default active recall. Their obsolete execution inputs do not
require today's health to reproduce yesterday's implementation.

Existing performed-work/failure/cancellation records and publication remain
compatible and report retained durability truthfully. A fresh verified claim must
meet the stronger durable-evidence gate. Retrieval exposes `verified_current`
explicitly; diagnostics continue to exclude unqualified records from trusted
frozen packets and ontology association construction.

An unchanged legacy receipt can gain a reviewed historical proof locator without
editing its original bytes. The optional companion is exactly
`Verification/project-memory/evidence/verification-<receipt-sha256>.json`:

```json
{
  "schema_version": 1,
  "receipt": {"path": "Verification/original.json", "sha256": "actual original receipt digest"},
  "applicability": "historical",
  "artifacts": [{"path": "docs/original.md", "sha256": "actual observed artifact digest", "retained_path": "Verification/retained/original.md"}]
}
```

The example digest strings are descriptive placeholders, not usable evidence.
The companion must preserve the original receipt path/hash and every artifact
path/hash in order, with no added or omitted artifact. Its JSON is bounded to
250,000 bytes; retained bytes use the existing 200-artifact/16 MB limits. The
owning Director reviews and retains exact evidence within current scope; the
reader neither creates the companion nor upgrades it into an execution receipt.
Historical applicability is mandatory. Missing companions retain legacy behavior;
malformed, mismatched, missing-archive or tampered-archive companions fail closed.

When exact historical proof is intact, changed/missing live versions and explicit
historical applicability are informational diagnostics (`severity: info`). They
still exclude the claim from verified-current publication and strict current
frozen packets. A historical-only consumer may accept supported evidence with
informational diagnostics, while preserving the detail and its lack of current
operational authority. Warning/error diagnostics remain evidence failures for
both historical and current trusted consumers. `historical_context` is context
from exact cited sources (`historical_support: context_only`); it is never a
verified-current claim. Derived consumers bind the full evidence assessment,
including companion and retained/current version references, in their input set.

Verification citations are inspected before direct source citations regardless of
their list order. A changed or absent direct `kind: source` citation can retain
historical support only through a qualified verification artifact with the exact
same path and expected digest. The reader reopens the permitted retained bytes,
checks their hash and privacy constraints, and verifies the original source
locator against those bytes. It retains an informational `current_source_changed`
diagnostic and cannot qualify the result as verified-current. Missing, altered or
mismatched proof and invalid historical locators still fail. Accepted-design
claims cannot borrow incompatible execution proof to bypass their own evidence.

The `validate` command rejects warning/error or unclassified diagnostics while
retaining informational applicability details. Its `verified_current_records`
count separately reports current verified outcomes; `valid: true` for qualified
history is not a claim that those historical observations apply to current code.
