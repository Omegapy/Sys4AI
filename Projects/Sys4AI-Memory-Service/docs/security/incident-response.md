# Security incident response

This procedure covers suspected credential exposure, secret ingestion, memory
poisoning, cross-project disclosure, path escape, unauthorized write, unsafe
export, and destructive-operation error. Preserve evidence without copying the
protected content into a Task, log, receipt, chat, or support bundle.

## Contain

1. Stop the memory-service writer and any local model/provider process involved
   in the event. Keep the network listener disabled.
2. Disable the affected profile or credential reference. Do not print or test a
   suspected credential on a command line.
3. Block sync, improvement, promotion, export, import, rebuild activation, and
   destructive execution for the affected project/dataset.
4. Preserve non-sensitive event IDs, trace IDs, source/record IDs, timestamps,
   policy revision, configuration/profile/provider fingerprints, and affected
   storage classes. Do not preserve raw queries or matching secret text.

## Assess scope

Check each possible copy under project control:

- canonical sources and control records;
- source registry, staging, proposal/review artifacts, and rebuild inputs;
- exact index, provider store, graph/vector data, cache, and active/failed
  generations;
- audit and operation-status files;
- provider-neutral packages, COGX artifacts, authorized backups, and temporary
  exports; and
- model/runtime files when the provider may have persisted input.

Identify the source of authority for removal. A memory permission does not by
itself authorize editing or deleting a canonical project file.

## Credential exposure

1. Revoke the credential at its issuer. Deleting a local reference is not
   issuer-side revocation.
2. Review provider access and audit records for the credential's scope and
   validity window.
3. Create a replacement with the narrowest approved scope only if the
   integration remains authorized.
4. Update the external keychain or secret-store reference without recording
   the value. Restart the narrow provider process so it cannot retain the old
   value.
5. Scan all classes above. If prohibited content reached memory, continue with
   privacy erasure.

Ollama's user-home identity file is sensitive runtime material. It is not a
memory-service credential and must not be copied into the repository or
derived memory. If it is implicated, rotate or remove it only through an
approved Ollama-specific recovery procedure after stopping the daemon.

## Privacy erasure or secret ingestion

1. Correct or remove the canonical source through its governed workflow.
2. Create a non-mutating privacy-erasure impact preview covering provider,
   exact index, cache, staging, audit, export, backup, rebuild-input, and
   canonical-source locations.
3. Obtain current action-specific delete permission. If canonical files are in
   scope, obtain the separate canonical project authority and executor.
4. Execute only the unchanged preview digest. Reject execution if content,
   paths, permissions, or scope changed.
5. Rebuild from sanitized canonical inputs into a new generation.
6. Search the allowed locations again and verify that a future rebuild cannot
   reintroduce the content.
7. Retain only a sanitized receipt with identifiers, safe path hashes, policy
   revision, outcome, and times. Do not retain the erased value or a reversible
   derivative.

The destructive lifecycle is fake/temp verified only. Real provider, export,
and backup erasure remains unverified and requires an environment-specific
procedure before production use.

## Poisoning, authority, or isolation incident

Quarantine the affected source or generated record without raising its
authority. Revalidate the current canonical permission and governance sources,
then inspect provenance, trust, content origin, namespace, lifecycle, and
relation validation. Do not promote a corrective summary as governance.

For cross-project exposure, disable the shared/query path, preserve sanitized
project/dataset/record IDs, verify the one-to-one dataset mapping and canonical
grants, erase unauthorized derived copies, rebuild both affected boundaries as
needed, and run two-project deny tests before reopening access.

## Restore and close

Restore through [the backup and recovery procedure](../operations/backup-and-recovery.md).
Before reopening service, require clean configuration/profile/schema checks,
source discovery, permission validation, generation checksums, health/drift,
representative retrieval, secret/redaction tests, and the affected isolation or
destructive tests.

The incident record should state what was observed, containment time, affected
IDs/classes, canonical actions, provider/issuer actions, verification evidence,
remaining uncertainty, and who authorized restoration. It must also state what
was not tested. Never claim full erasure for an external backup, provider, or
issuer that was not directly checked.
