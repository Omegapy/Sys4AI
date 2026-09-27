# Ontology proposals and local authoring

A candidate is durable unpublished work. Its exact semantic content, evidence,
generator attribution, uncertainty and review history live under
`control_records/ontology/proposals/ONTPROP-.../`. This directory is never a
graph cache. Rebuilding indexes, inference or wiki files cannot remove it.

## One shared proposal API

`ontology_proposals.save` writes an immutable numbered revision and an immutable
decision event. The current head changes through expected-revision checks and
the publication lock. Earlier revisions retain their bytes and review records.
Saving a revision invalidates the previous review. Two clients cannot silently
overwrite the same saved revision. A stale target or draft returns a conflict;
the browser retains entered text and the earlier saved draft remains available.

`open_proposal` and `list_proposals` are read-only. `decide` records distinct
accept, reject, discard, reopen and supersede outcomes. Accept means that the
candidate's exact validated content was reviewed. It does not supply publisher
authority or change canonical records. A superseded version cannot be published.
After a publication intent is accepted, that revision cannot be revised or
rejected; its exact operation owns completion or recovery.

`ontology_proposal_validation.validate_candidate` binds the current candidate,
canonical target, selected sources, helper versions and advanced configuration.
It checks the full proposed core, source freshness, lifecycle transitions,
competency questions and applicable real SHACL and finite inference backends.
Unavailable, unsupported, inconsistent and failed backends are separate failure
states. They never create eligible validation. Syntax or an LLM endorsement
alone cannot establish eligibility.

The report includes definition and relationship diffs, changed wiki previews,
before/after query results, competency improvements or regressions, and exact
findings. Preview checks do not publish canonical content or derived products.
Large displayed impact is bounded and explicitly marked truncated.

`publish_revision` needs an exact current review plus the version 2 ontology
grant described in [publication and recovery](publication-and-recovery.md).
It uses the existing publisher, reports the actual receipt, and reopens every
selected target to verify its post-hash. A partial result identifies committed
and pending files. Recovery reuses its accepted operation identity and a fresh
current grant. Creating a new operation to hide a partial commit is unsupported.

## Native generation and refinement

The [generation reference](../SKILLS-depo/ontology/references/proposal-generation.md)
defines `prepare` and `capture`. An immutable request freezes selected source
bytes, approved ontology context, target documents, runtime attribution and
the bounded objective. Source instructions remain quoted data. The generator
receives no publication authority, dependency-installation authority or new
service access.

Actual native receipt evidence is separate from parser fixtures. The parser
can check hashes and structure; it cannot authenticate fabricated local JSON.
The coordinating current owner must retain observed native tool evidence.
An initial run permits at most two finding-directed revisions. Every revision
names its observed findings and original source/version lineage. Repeated
unchanged failures or the attempt bound stop refinement with unresolved findings.

## RDF import staging

Completed local standards imports can enter `stage_rdf_import` with the exact
selected source reference and reason. The immutable `rdf-imports/ONTRDF-...json`
preserves the source bytes, full RDF quads including graph identity, parser
versions, diagnostics and semantic hash. It is always marked `approved: false`.

An explicitly selected existing extension target can receive a candidate only
when every imported statement is representable without conversion loss:
named project subjects, supported finite axiom predicates, named objects and
the project's asserted graph. Core/namespace conflicts, unknown graph classes,
blank nodes, literals and unsupported semantics remain staged and diagnosed.
The candidate preserves the original import, retains previous extension
statements, and changes only the selected extension and its companion lock.
Standards validation, review and publication remain separate required steps.

## Local workbench

Enable `profiles.workbench` explicitly in the selected advanced companion, then
start `ontology.py --project-root ROOT workbench --session-file
.sys4ai/ontology/workbench/SESSION.json`. A trusted local authority file may be
selected with `--authority-file`. It contains the exact `trusted_authority`
arguments: `actor_id`, `actor_kind`, normalized actual `native_receipt`,
`observed_at`, exact canonical-file `scope`, and optional confirmed `task`.
The current owner supplies this file; HTTP requests cannot supply these fields.
Without it the service permits browsing only.

The selected profile supports `enabled`, loopback `host: 127.0.0.1`, `port`
(0 chooses an available port), `session_seconds` from 60 to 3600, and
`max_request_bytes` from 1024 to 1000000. Basic browsing requires no remote
service or Node dependency. Advanced operations expose their real backend
readiness. Current native publication evidence lasts at most five minutes;
expired authority requires a fresh trusted observation, independently of the
browser session's lifetime.

Open the one-use bootstrap URL from the private runtime session file. Its token
is exchanged for a same-site HTTP-only session cookie and a CSRF token. The
fragment is removed from browser history after connection. Do not place the
session file or URL in evidence logs, canonical content, fixtures or Git.
Host and Origin checks reject cross-origin calls; CSP and text-only rendering
prevent labels, evidence and imported text from executing. Source navigation
opens only already selected evidence. The listener supports loopback only;
remote exposure needs a separate deployment and access policy.

Search supports ID, label and alias with module, kind, type, lifecycle and fact
filters. Both list buttons and graph nodes open definitions, directed relations
and source evidence. Imported assertions, project assertions, inferred facts
and proposals have readable labels. The inference view shows rule/premise
chains with source buttons and a bounded complete-result inspector.

The editor provides forms for concepts, instances, predicates and qualifier
properties, typed relations, cardinality/acyclic constraints and source
bindings. Imported IDs are protected. Deprecation retains historical meaning
and a distinct optional replacement; deleting or recycling approved identities
is rejected. All actions are available through labeled keyboard controls;
dragging and color interpretation are not required. Cancel preserves saved
drafts. Reject and discard preserve approved content. The review view retains
validation failures, exact diffs, history, actual partial receipts and canonical
reopen actions.

These checks are cooperative local process controls, not operating-system
identity authentication. Report actual browser and native evidence separately
from HTTP contract tests or screenshots.
