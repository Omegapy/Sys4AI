# Explorer release preparation: rollback correction

This handoff supplements `HANDOFF.md` and the unchanged first `checkpoint.json`.
Use `rollback-manifest-v2.json` for rollback instructions. The two proposed guard
adapter/bootstrap records become durable history when accepted. Preserve them
and all related intents and receipts. Rollback publishes successor bindings
through the guard owner; it does not delete or overwrite accepted records.

The 15 source proposals, 52 selected root entries, four-file guard repair and
separate workbench profile proposal are unchanged. The static Template manifest
contains 504 files: 78 creates and 14 replacements, with no observed customized
conflicts or unrelated pending changes. These are source-inspection counts, not
an executed owner preview or test result.

Only this handoff, `rollback-manifest-v2.json` and `checkpoint-02.json` were added.
Every first-checkpoint file remains byte-identical. No source, installation,
configuration, watcher, canonical state or historical record was changed; no
apply, test, build or launch ran. Current native/time grants remain deferred to
the actual authorized owner operation. Original PLAN1 is not fully verified.

Writes are stopped for manager review. Exact host adoption authority and owner
admission/application remain pending. Keep the watcher held.
