# Exact root owner handoff

These files are prepared and have not been applied. The actual bound host
`/root` performs the root phase after the implementation assignment stops and
current write ownership is reconciled. No native roster or grant is fabricated
in these artifacts. Re-run prepare_root_handoff.py only after checking any
changed predecessor and while the source scope is no longer being edited.

1. Review source-adoption-manifest.json and every exact pre/post hash. The five
   changed existing ontology helpers and commands.md have no unrelated source
   delta from their original installed counterparts. The new integration helper
   is additive. The root initializer, Task intake/helper, authority helper,
   governing trio, core and memory are excluded. The publication contract uses a
   root-local proposal adding only this integration section. CURATOR.proposed.md
   preserves the depot identity and supported current-owner routing; it does not
   invent project.json or claim the prepared-project selection artifact works.
2. Before replacing guarded helpers, import the currently installed
   ontology_guard_setup.py and call `preview_repair(root, **selection)` using
   guard-repair-selection.json. Persist and review its exact returned preview.
   The proposed bundle retains enabled enforcement, all eight action families,
   shapes and the 128 MiB guard bound. Obtain a current real native roster and
   construct the existing schema-1 guard-repair grant, binding preview_sha256,
   project_id, current ontology.yaml SHA, actor `/root`, actor_kind `director`,
   observed_at/expires_at within five minutes, task null, exact scope and each
   reviewed pre/post record. Call the existing `apply(root, preview, grant)`.
   Do not directly copy the rows marked ontology-guard-repair before that owner
   transaction. Reopen its immutable receipt and all selected postimages.
3. Apply only the remaining exact-local-source-adoption rows using expected
   predecessor hashes and atomic writes. Reopen those bytes. Recertify the
   existing root standards runtime with the installed command
   `ontology.py --project-root ROOT profile-setup standards`; do not provision
   or change profiles. This is required because ontology_core.py is part of
   the standards worker fingerprint. Check current backend and guard health.
4. Run the installed public `integration-preview` with integration-selection.json.
   Its output contains the exact proposal and preview hash. Save the proposal
   separately for the CLI. The root graph and current sources are validated
   before any writes. Any existing binding that would be stale after the four
   target changes is an exact protected-binding hold.
5. Use a fresh real native observation to construct an integration grant with
   schema_version 1, grant_id beginning ONTIGRANT-, operation integrate-curator,
   project_id sys4ai-depot, actor_id /root, actor_kind director, task null,
   observed_at/expires_at at most five minutes apart, and native_receipt from
   actual collaboration.list_agents. Copy payload_sha256 and preview_sha256
   from the preview; copy config_sha256 from ontology.yaml's original expected
   predecessor, scope in exact TARGETS order, reviewed_records from each
   proposal path/expected_sha256/sha256, resources and sources from proposal,
   and helpers from preview.before.helpers. No persistent scope is widened.
6. Run `integration-publish PROPOSAL --grant-file GRANT
   --expected-preview-sha256 DIGEST`. On interruption renew current authority
   for the original preview and config predecessor, then use
   `integration-recover OPERATION_ID --grant-file GRANT`. Reopen the immutable
   owner receipt and run check_ontology.py to check all fourteen functions.

The distinct public owner APIs are in ontology_publication.py. All CLI file
arguments are confined project-relative paths. Guard repair has an existing
Python `preview_repair` API; `guard-preview` in the older CLI is enablement only
and must not be substituted. Current native identity, overlap, governing-hash,
publication-enabled and bound canonical scope gates remain mandatory.

Continue root compile/wiki/semantic/link maintenance and the live session,
pending obligations, historical Task, memory retrieval and temporary workbench
checks through their existing owners. This implementation has not performed
those root actions and makes no root runtime or end-to-end completion claim.
