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

## Browser entry and retained local helpers

Use the installed ontology skill's `explore --open` command for the read-only
Project Knowledge Explorer. Authoring uses the trusted proposal, validation,
review, publication and recovery commands described above. The old `workbench`
command returns `workbench_retired` and rejects former authority/session options.

`TrustedAuthority`, `trusted_authority` and `draft_form` retain their local helper
interfaces for trusted callers. They confer no browser access. Historical setup
receipts and six exact workbench assets remain compatibility resources; the
current package has no authoring HTTP implementation. Old session credentials
are not migrated. Review the installed `references/explorer-operations.md` for
normal launch, configuration and code/assets/configuration rollback boundaries.
