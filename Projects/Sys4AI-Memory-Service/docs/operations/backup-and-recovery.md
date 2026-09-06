# Backup and recovery

The durable recovery source is the canonical project, not a provider database
or memory package. Back up each asset according to its class.

## Asset classification

| Asset | Class | Recovery treatment |
|---|---|---|
| Registered project sources, profiles, schemas, registries, configuration, canonical permission documents, approvals, and accepted project changes | Canonical | Back up and restore through the normal project or repository controls. Verify identity, revision, and content hashes before rebuilding. |
| Exact index, provider database, cache, generated relations, active-generation pointer, local metrics, audit log, derived receipts, and staging | Derived | Useful for diagnostics or faster recovery, but disposable. Never restore one as authority over newer canonical sources. |
| Provider-neutral Sys4AI Memory Package or separately approved COGX artifact | Optional | Use only as a validated portability or acceleration artifact. It does not replace canonical source backup. |
| Credentials, user-home runtime identity, restricted cache, model weights, and any package containing protected material | Sensitive | Exclude from ordinary memory packages. Back up only under a separately approved secret/model policy with access control, encryption, rotation, and deletion rules. |

The machine-readable package repeats these classes in `backup-assets.json`; the
developer boundary is also summarized in
`src/sys4ai_memory/exchange/BACKUP.md`.

## Recovery order

1. Stop all memory-service writers. If a local model daemon is running, stop it
   unless the recovery procedure explicitly needs it.
2. Preserve the failed derived directory for diagnosis only when policy permits
   it. Do not copy secrets or restricted source content into a support bundle.
3. Restore canonical project files through their normal governed workflow.
4. Validate configuration, schemas, registries, profiles, canonical permission
   sources, and content hashes before opening provider state.
5. Run source discovery and review all include, exclude, reject, and unmatched
   counts.
6. Produce a full rebuild preview. Confirm project, dataset, source revisions,
   generated paths, previous generation, versions, model identifiers, and the
   impact digest.
7. Obtain fresh action-specific rebuild permission. Execute only the unchanged
   reviewed digest.
8. Validate exact-index and provider-neutral snapshot counts and checksums.
   Activate the new generation only after validation.
9. Check health and drift. Exercise representative exact, lexical, current,
   historical, and insufficiency queries.
10. Re-enable clients only after the active pointer, health, audit, and
    isolation checks agree.

Real Cognee recovery has not been exercised. The current rebuild tests use an
in-memory provider stage and disposable directories. Do not treat that test as
proof that a Cognee database can be restored.

The unified sync path has no transaction coordinator across exact-index and
provider writes. If one side fails after the other changes, stop writes, retain
sanitized failure evidence, use health/drift to identify the divergence, and
rebuild from canonical inputs. Do not declare the stores consistent from one
successful component receipt.

## Generation failure and rollback

`GenerationRebuilder` builds below a temporary candidate directory and writes
the active-generation pointer last. A failed or cancelled build records a
checkpoint and failure code without activating the candidate. The previous
generation remains available. A successful build records the previous
generation ID as its rollback pointer.

Recovery from a failed build:

1. Read the candidate `rebuild-receipt.json` and `checkpoint.json` as metadata.
2. Confirm the active pointer still names the prior valid generation.
3. Fix the source, adapter, configuration, model, provider, permission, or
   storage cause. Never edit a generated index or manifest by hand.
4. Create a new preview because changed inputs invalidate the old impact
   digest.
5. Resume through the operation tracker only when the failed/cancelled
   operation has a retry-safe checkpoint. Otherwise start a new idempotent
   rebuild operation.

There is no operator command that rewrites the pointer to an arbitrary older
generation. A rollback action must validate the generation manifest and use a
reviewed, atomic activation workflow. Manual pointer edits are unsupported.

## Drift recovery

Drift compares registered and indexed source IDs plus source, configuration,
profile, schema, adapter, provider, model, and generation fingerprints. A
`degraded` drift result means the service process may be live while its memory
is not ready for current-source claims.

Use the drift report to identify the changed input. Revalidate the canonical
source directly, then run incremental sync or a full rebuild as policy
requires. Never mark drift clear by changing the expected fingerprint in a
generated manifest.

Drift also hashes the active generation manifest, SQLite exact index, and
provider-neutral snapshot against the checksums published at activation. A
manual edit, replacement, deletion, or symlink substitution is reported as
generation drift. Recover by rebuilding from canonical inputs; do not repair a
generated file or its expected checksum by hand.

## Provider-neutral package recovery

The exporter and validator implement the approved deterministic ZIP JSON/JSONL
package inside an `age` X25519 envelope. The encrypted path builds the plaintext
ZIP in memory and writes only ciphertext. Unencrypted packages remain available
solely as disposable test candidates.

A candidate package is inspectable with standard JSON and JSON Lines tools. It
contains a manifest, filtered source metadata, typed records, relations,
origin provenance, profile versions, record statuses, backup classifications,
and checksums. It excludes secret-prohibited material and records excluded
sensitivity counts.

Import validation checks the closed member set, paths, sizes, compression
ratio, checksums, schemas, project/dataset scope, profile versions, trust and
sensitivity allowlists, source anchors, relation endpoints, provenance, and
canonical-source collisions before staging. Activation requires a fresh
canonical `administer` decision bound to the exact preview digest plus a
separate provider mutation authorization. Provider responses must repeat the
expected identity, scope, execution state, impact, and exact imported IDs; a
mismatch leaves the filesystem activation pointer unwritten. Imported data is
placed under derived storage and cannot overwrite a canonical source.

`MemoryPackageExchange` returns `production_ready=true` only for the approved
ZIP/age policy and an explicit public recipient. The retained
`DisposableMemoryPackageExchange` name is a test-policy compatibility surface
that returns `production_ready=false`. Import activation still requires a
distinct inactive provider generation and fresh `administer` authorization; no
such grant exists in the tracked local permissions. Current runtime evidence
covers encrypted export/decryption and disposable import activation, not a
non-fixture recovery cutover.

## COGX boundary

COGX is optional, supplementary, and provider-owned. `plan_cogx_delegation`
can describe an import/export delegation only when the adapter capability and
policy both approve it. The provider-neutral package code does not read or
write Cognee-native databases. The pinned Cognee 1.5.3 native archive writer,
reader, and `COGXArchiveSource` passed the isolated
[compatibility probe](../verification/cogx-compatibility.md), but no populated
Cognee database was exported or imported.

Separately, the generic provider-neutral importer is fake/temp verified from
an in-memory snapshot into an isolated Cognee adapter using its injected test
runtime. This proves that the Sys4AI package is not tied to the originating
provider database. It complements the native archive probe but does not
establish real Cognee storage, model, database-backed export/import, or
migration behavior.

## Privacy or credential incident recovery

A privacy erase must cover active provider state, exact index, cache, staging,
logs, authorized exports/backups under project control, and future rebuild
inputs. Canonical-source effects use the normal governed project workflow; the
memory service cannot silently delete the source file. An embedding application
may supply a governed canonical executor only for the exact previewed impact;
the service verifies completion before returning a receipt. After removal,
rebuild from sanitized inputs and verify that the prohibited content cannot
reappear.

The current `MemoryService` forget route performs the governed
filesystem/lifecycle operation and explicitly reports
`provider_forget_executed=false`. Until provider, package, audit, backup, and
rebuild-input erasure are coordinated and verified, it is not a complete
privacy-erasure workflow.

For a credential incident, disable the affected profile, stop the provider
process, revoke the credential at its issuer, rotate the external reference,
scan canonical and derived locations, apply privacy erasure where required,
and restart only after clean validation. Deleting a local reference is not
proof of issuer-side revocation. See [incident response](../security/incident-response.md).
