# Backup and exchange boundary

The Sys4AI Memory Package is a provider-neutral, derived-data exchange candidate. It does
not replace a backup of registered canonical project sources.

| Asset | Class | In candidate package | Handling |
|---|---|---:|---|
| Registered project sources and control records | Canonical | No | Back up and restore through normal repository and project controls. |
| Provider-neutral records, relations, source metadata, status, and provenance | Derived | Yes | Rebuildable from canonical sources; validate all checksums before use. |
| Exact index, provider databases, and COGX artifacts | Optional | No | Rebuild or use a separately approved provider-native backup. |
| Credentials, secret fixtures, restricted caches, and model weights | Sensitive | No | Keep outside packages and manage under separately approved controls. |

`MEM-OQ-008` and `Q-008` remain unresolved. There is no approved production archive or
encryption selection. The current code denies normal export and import. It permits an
unencrypted directory or ZIP candidate only when policy and the caller both mark the
operation as disposable-test-only and the destination is inside an explicit disposable root.
The public service can exercise that exception only through
`DisposableMemoryPackageExchange`, which is confined to an isolated in-memory provider and
always reports `production_ready=false`. Its active and staging providers must be distinct.
Import activation validates the provider result against the exact requested snapshot before
publishing a receipt, active-import pointer, or provider-reference swap.

COGX remains supplementary and provider-owned. The base exchange code can describe a gated
delegation but does not read or write a provider-native database.

## Recovery order

1. Restore and validate canonical project sources and control records through
   the normal project workflow.
2. Validate configuration, schemas, registries, profiles, permission sources,
   source revisions, and content hashes.
3. Run discovery and review every included, excluded, rejected, and unmatched
   source.
4. Rebuild into a new derived generation, validate exact/provider-neutral
   counts and checksums, and activate the pointer last.
5. Check health and source/index drift before clients resume.

Do not restore an older provider database over newer canonical sources. Failed
or cancelled generation builds must leave the prior active generation
available. Manual edits to indexes, provider stores, manifests, or the active
pointer are unsupported.

The current package and rebuild tests use disposable paths and an in-memory or
fake provider. Real Cognee backup, restore, database-backed COGX export/import,
and privacy erasure have not been verified. The real pinned library's archive
writer, reader, and source passed the isolated compatibility probe. See
`docs/operations/backup-and-recovery.md` for the operator procedure.
