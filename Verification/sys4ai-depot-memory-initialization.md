# Sys4AI depot initialization

The Director used the installed final wheel's `init preview`, reviewed its
identity, configuration fingerprint, private planned paths, source counts and
provider warning against the user's authorized root adoption, and applied that
exact digest through `init apply`. No additional approval was required because
the user had authorized this plan and current-folder execution.

Accepted impact digest:
`b5b34a4aeb1d1fcd8a7f4a8c8ecde5767df7d8e8d8d2c460101cc482842299d5`.
Configuration fingerprint:
`2f4b4de68a4abb009fa17352a8d4a625ed114c0025713767c142e391e6c417d0`.
The installed preview took 18.956 seconds; apply took 35.869 seconds and returned
success. The preview created no derived files. Its included count was 260;
its 354 non-included decisions also contain unmatched optional format rules,
so that number is not a count of physical excluded files.

The live receipt at `.sys4ai/memory/receipts/initialization.json` and the
metadata-only inspection in `sys4ai-depot-initialization.json` agree on
`sys4ai-depot`, `sys4ai-depot-memory`, reviewed mode and the accepted digest.
Exact index initialized: true. Provider initialized: false. Models activated:
false. All observed directories were mode 0700 and files mode 0600 under the
root-local memory boundary.

The installed reviewed and direct entry points share preflight and storage
code. The direct fixture tests separately prove no preview fields; only this
root-specific entry records an accepted digest. The root's Git metadata,
template `.git`/`.sys4ai` absence, Memory Service `.git` absence and user-wide
Cognee metadata all matched the just-before-adoption snapshot. No child or
user-wide runtime state was created. Functional source ingestion and retrieval
are the next separate verification step.
