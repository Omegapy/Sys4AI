# Storage and existing-account source assessment

7of9, read-only host work for TASK-20260910-7F1A11AE. These findings are from public rust-v0.153.4 source, bound in receipt.json. No installed credential, token, keychain item or auth file was read, copied or changed. No native runtime or model was launched.

## Findings

- `core/src/config/auth_keyring.rs::Config::auth_config` supplies the resolved Codex home to authentication. The audited configuration has no separate credential-root argument in this structure.
- `login/src/auth/storage.rs::get_auth_file` places file authentication under that root. Direct keyring lookup derives its key from the canonical root path, so a fresh root cannot be assumed to reuse the original login. The secrets backend also receives that root; its global scope label alone does not prove cross-root reuse. Do not switch credential backends or create credential symlinks as an unreviewed workaround.
- `rollout/src/recorder.rs::new_log_file` constructs recorded-history paths beneath the same Codex home, then the dated sessions directory and a runtime-generated thread/rollout filename. This is separate from the SQLite location supplied to the recorder.
- The preceding LocalThreadStore audit in curator-fork-storage-source-89xzdvb8 shows create_thread passes both codex_home and sqlite into RolloutConfig for the selected history mode. Paginated history is not evidence that dated rollout files disappear.
- The official configuration schema describes sqlite_home and log_dir as separate destinations. `history.persistence` governs the interactive history.jsonl file; it must not be represented as disabling all thread persistence. The tagged fork handler reads stored source state; ephemeral source viability remains an actual API prerequisite.

## Implication for a concrete scope

The inspected paths do not establish fully relocated runtime history plus transparent reuse of the existing account without changing or copying authentication material. That is a bounded finding about these code paths, not a claim that every other deployment route is impossible.

A scope may instead explicitly consider native-created, test-owned runtime records in the existing runtime's normal history location, with a separate test database/log directory where supported. This would preserve existing configuration and credentials and use the runtime's established login path. It is not equivalent to promising that every artifact stays inside the fixture. It needs an explicit host assessment before execution, exact native-ID/path ownership, verification of user-visible task behavior, and cleanup only of records created by that reviewed test. It must never alter unrelated sessions, indexes, credentials, home configuration or active project records. Native API metadata must identify actual owned paths; directory names or guessed filename patterns are insufficient authority.

Whether those bounded runtime side effects fit the existing verification authority is an authority/scope assessment for the host and manager, not a capability claim made by this note. No new user permission is automatically inferred as necessary merely because ordinary native runtime state is involved. If the accepted boundary requires every history file to remain inside the fixture and no supported account-reuse route satisfies it, retain that exact unmet gate and present a concrete alternative rather than copying credentials.

Current round-2 solver inputs remain unchanged. Any use of these additional sources in acceptance must be explicitly bound through the current review/synthesis process.
