# Safe paths and destructive operations

Status: binding security contract; path, preview, lifecycle, and temporary-file
behavior are focused-test verified, but real provider/export/backup erasure is
not verified

## Path resolution

All source and derived paths start from a trusted operator-resolved project root. For each candidate path, the service must:

1. reject a client-supplied absolute path unless a separately approved external-source registration names it;
2. normalize separators and dot segments;
3. resolve existing parent directories and symlinks;
4. confirm the resolved path remains inside the registered allowed root;
5. match exactly one effective registry decision, with exclusion taking precedence;
6. apply Git ignore rules in addition to, never instead of, registry exclusions;
7. reject device files, sockets, provider stores, caches, temporary paths, secret patterns, and unsupported formats;
8. enforce adapter size, nesting, decompression, and processing limits; and
9. return a redacted reason code for every exclusion or rejection.

Provider-native local-file options do not bypass this resolver. Server-facing clients submit a registered source ID, not an arbitrary filesystem path. A path accepted before a rename or symlink change is resolved again before read.

## Two-phase destructive protocol

Mass forget, delete-source, privacy erase, import replacement, and rebuild activation use a preview followed by a separately authorized execution.

The preview is non-mutating and includes operation, project/dataset, selection rule, record/source counts, sensitivity classes, affected generation/export locations, canonical-source effects, blocked items, warnings, policy/permission revision, and a digest of the resolved impact set. It must not include sensitive content.

Execution must reread canonical permissions and current state, recompute the impact set, and compare it with the preview digest. A change requires a new preview. The request must carry exact action-specific authorization; role names or semantic-memory claims are insufficient. Completion writes a non-sensitive receipt and verifies the intended copies were removed or the new generation was activated.

| Operation | Required additional rule |
|---|---|
| Mass forget | Never delete canonical sources; list every dataset/generation affected. |
| Delete-source | Distinguish source deregistration, derived-record deletion, and deletion of a canonical file. The last action uses the normal project workflow and separate authority. |
| Privacy erase | Reach provider stores, exact index, cache, staging, logs, authorized exports/backups under project control, and future rebuild inputs. Receipts cannot retain the erased content. |
| Import replacement | Validate package, scope, versions, signatures/checksums, sensitivity, and a rollback generation before activation. |
| Rebuild activation | Build beside the active generation; activate atomically only after integrity and compatibility checks. Failure preserves the last valid generation. |

## Authority boundary

The control-record root and local reviewer policy are fixed in
`control_records/memory/permissions.json`. The document names one human
`local-owner`, but grants no delete, administer, or rebuild permission. Preview
code remains testable; tracked configuration independently disables destructive
execution, so non-fixture execution is denied.

## Current implementation boundary

Source discovery rejects traversal, absolute paths, symlinks, non-regular
files, hard exclusions, Git-ignored files, unsupported or oversized content,
and secret-like content. The destructive lifecycle recomputes hashes and
current permission before deleting a file inside an explicit deletable root.
Its tests use disposable temporary directories only.

`delete-source` first returns a governed canonical change requirement and never
deletes a canonical file through its ordinary filesystem path. Execution is
denied unless the embedding application supplies a governed canonical executor
for the exact previewed set. The service verifies the executor's completed IDs
and confirms that every local previewed canonical path is absent before it
returns a deletion receipt. The executor is responsible for the normal atomic
project workflow and rollback. Privacy erasure uses the same boundary for
canonical effects. No production identity or repository implementation is yet
authorized as that executor, and no real Cognee store, exported archive, or
external backup has been erased in validation.
The unified dispatcher currently reports `provider_forget_executed=false`, so
its filesystem/lifecycle receipt must not be interpreted as complete erasure
across provider and package copies.
