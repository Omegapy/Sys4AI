# Rename the active role directory to `Roles/`

Status: completed. All ten requirements are verified; see the completion evidence below.

The user requests a plan and its implementation: rename `roles/` to `Roles/`
throughout the role processes, active Sys4AI root and designated Template.
This standalone plan follows that ordinary planning request; no managed-plan,
Task or TRD workflow is activated. The earlier orchestration records retain
their historical meaning and bytes.

## Inspected baseline and scope

The root is `/Volumes/P-SSD/AngryOwl/Sys4AI`, initially at Git commit
`9e57eef474b6fbb3d45283dfd3e2c9bb3f038037`. Both root and Template contain
lowercase `roles/`, two valid role pairs and a current generated index. Both
selected directories empirically use a case-insensitive filesystem. The
Template updater reports 81 managed destinations, 78 sources and no pending
change; its original watcher has a current successful check. The live Task
catalog has 21 terminal records and no nonterminal execution.

Reuse the existing Python 3.12 standard-library architecture. Change reusable
functionality in its depot source, propagate only through the checked Template
pipeline, and separately adopt the affected root copies. Preserve the earlier
root-role edits and unrelated To-TRD work. No other product adoption, dependency
installation, managed document rewrite, commit or push is included. Exact Git
path casing for the authorized directory rename is part of the implementation.

The pre-change inventory and preservation hashes are in
`Verification/roles-capitalization/baseline.json`.

## Requirements and observable acceptance

| ID | Requirement and acceptance evidence |
| --- | --- |
| RC-01 | The physical root and Template directories are spelled exactly `Roles`, with no separately active lowercase directory. Directory-entry inspection and Git path metadata prove spelling; case-insensitive `exists()` is insufficient. |
| RC-02 | Discovery, show, validation, role creation, index regeneration and legacy transition use `Roles/`. Actual CLI fixtures verify returned paths, valid pairs and deterministic relative navigation. Read-only operations never rename or repair. |
| RC-03 | The case-only transition preserves every pair and existing customization, refuses ambiguous dual trees or aliases, and has bounded stale-input/interruption recovery. Historical transition evidence remains attributable and valid without rewriting its original bytes. |
| RC-04 | New Task manager/worker assignments use the current `Roles/` catalog and pair paths. Worker write-scope protection covers the new role root/index. Existing historical lowercase provenance is not silently reclassified or rewritten; relevant compatibility and rejection fixtures prove the boundary. |
| RC-05 | Template mappings, required assets, generated role index, ownership state and update/recovery logic use the new case. Case-only migration safely handles physical aliases and distinct conflicting directories; repeat check/apply is current without recreating `roles/`. |
| RC-06 | The initializer creates usable `Roles/` starters and prepares selected existing projects without splitting a preserved role collection. Old setup contracts remain readable and are not silently converted; reruns and interrupted setup retain their edition and ownership. |
| RC-07 | Active skills, role/governance/specification documents, README examples, policy files and tests use the new paths. Remaining lowercase references are explicitly historical, legacy compatibility, or negative fixtures. Historical Tasks, TRDs, plans and evidence remain unchanged. |
| RC-08 | Root and Template receive the complete authorized adoption, including compatible helpers. Fresh catalogs validate both roles. A real native child explicitly reads its pair from `Roles/` and returns matching file digests. |
| RC-09 | All affected meaningful tests pass, including strict-case behavior and case-only recovery. Fresh disposable initializer/updater integration demonstrates the delivered Template works. Reports distinguish fixtures, actual native behavior, case-sensitive coverage and unexercised external use. |
| RC-10 | Final protected inventories, registry, Task state and prior edits remain unchanged. The original watcher is restored with a fresh successful check from its current PID, with no pending updater transaction or active validation worker. |

## Ordered work and ownership

1. Director: finish inventory, record the plan and baseline, then pause the
   original watcher for the coordinated source/mapping change. Dependencies: none.
2. Role-helper worker: implement exact-case catalog/creation/transition behavior,
   preservation and recovery tests in the source role package. Depends on 1.
3. Template-pipeline worker: implement safe case migration and generated-index
   ownership/recovery in the updater and its tests/mapping. Depends on 1; integrate
   against 2 before acceptance.
4. Initializer worker: implement the new starter edition and prior-edition
   compatibility, existing-project preservation, tests and package documentation.
   Depends on 1; coordinate helper interfaces with 2 and Template inputs with 3.
5. Director: update Task path validation/protection and active source guidance,
   integrate all source changes, and run focused suites. Depends on 2–4 for
   integrated checks; independent Task/document work may proceed earlier.
6. Director: inspect the complete updater preview, apply the Template migration,
   perform the exact root rename/adoption and regenerate its index. Record the
   Git case renames without staging unrelated edits. Depends on 5.
7. Director: exercise actual role CLI and native role reads, fresh and existing
   disposable setup, repeat updater/recovery checks, and affected source/root/
   Template suites. Resolve any demonstrated defect before proceeding. Depends on 6.
8. Director: inspect all requirements and changed artifacts in both directions,
   check preservation, restore/observe the watcher, update this plan and write
   the final evidence-bound report. Depends on 7.

Workers receive the current `project-sub-agent` pair under a fresh catalog,
one bounded objective and disjoint source ownership. They inherit the exact
Director model/effort without overrides, do not alter live Task/plan ledgers,
and return their own evidence. The Director owns integration and acceptance.

## Risks and controls

- Case-insensitive lookup can hide an unchanged on-disk or Git spelling. Inspect
  directory entries explicitly and use a controlled intermediate rename.
- A delete/add updater sequence can delete its own newly written alias. Treat
  the case rename as an explicit recoverable path operation before ordinary
  content publication; test interruption and distinct-tree conflicts.
- Saved receipts contain earlier paths and hashes. Keep their original edition
  and evidence, with explicit transition provenance; never relabel old history
  as a current native assignment or edit an old canonical ledger for convenience.
- Half-adopted helpers or a running watcher can mix editions. Pause the verified
  watcher during source integration; apply only a fully reviewed update and
  require repeat current checks before restoration.
- Broad text replacement can corrupt JSON field names, role slugs, unrelated
  projects or historical requirements. Change active path values and examples
  within the reviewed scope, then classify every remaining active-path match.

## Verification and completion evidence

Use the source role, Task/orchestration, initializer and updater/watcher suites,
root/Template contract suites, actual role CLI commands and disposable setup
flows. Add focused tests only for casing, receipt/edition compatibility,
preservation and recovery behavior not already covered. Do not count synthetic
native receipts as actual role loading. A final path/requirement/artifact map,
test receipts, native read receipt and preservation comparison will be retained
under `Verification/roles-capitalization/`.

Completion requires every RC criterion above to have sufficient observed
evidence, exact `Roles/` spelling in both selected projects and Git metadata,
current validated Template/root behavior, unchanged protected state, and a
restored healthy watcher. An unresolved item remains incomplete rather than
being reduced to a documentation-only or compatibility-alias result.

## Completion evidence

All eight work steps are complete. The final audit covers 90 implementation artifacts: 76 updates, 11 case renames and three added test copies. Every artifact maps back to an RC requirement.

| Requirement | Result | Evidence |
| --- | --- | --- |
| RC-01 | passed | Actual root and Template directory entries are exactly Roles; the Git index records all 11 case renames and has no tracked lowercase active path. |
| RC-02 | passed | Current root/Template catalogs and six native list/show/validate CLI calls pass. Source role tests cover create, reindex and legacy transition under the exact capitalized directory on both filesystem modes. |
| RC-03 | passed | Both two-hop transitions and repeat-current results were observed. The root original tree bytes survived before explicit reindex; .transition.json is unchanged. Source tests cover stale previews, aliases, distinct trees, appearing empty destinations and interrupted receipt/rename recovery with original identity. |
| RC-04 | passed | The 111 root and 92 Template Agent Task tests pass; new reservations require actual Roles and exact catalog paths. Dedicated tests preserve lowercase history structurally and reject old live paths plus role-root/index write aliases; four discriminating tests pass on case-sensitive APFS. |
| RC-05 | passed | Reviewed Template migration moved five managed role paths, retained recoverable state and generated its new index. Repeat apply/check is current at 82 managed files/79 sources. The 59 updater/watcher tests pass on strict-case APFS including six recovery boundaries and the repaired exclusive-rename race. |
| RC-06 | passed | Initializer v3 creates Roles starters. Earlier v1/v2 receipt editions and proof-bound renamed-v2 reruns retain provenance in 46 strict-case tests. Four actual calls using the unchanged delivered Template created/repeated a fresh project and prepared/repeated an existing project, preserving all 92 pre-existing files. |
| RC-07 | passed | The changed active helpers, source guidance, policy values, installed root and Template documents/tests use Roles. Remaining lowercase path literals are bounded prior-edition history, explicit migration inputs, casefold comparison or negative fixtures. Protected historical Tasks, TRDs, plans and evidence remain byte-identical. |
| RC-08 | passed | 21 root package/guidance files were adopted separately, with exact source hashes and root-specific policies preserved. Both roles validate in root and Template. Native child /root/roles_case_native_read opened the capitalized pair and passed all six installed CLI calls; root rehashed its 18 read/helper references and observed its completion. |
| RC-09 | passed | All applicable integrated checks pass; case-sensitive source suites exercise cases impossible on the host filesystem. The actual delivered Template setup and native role-loading checks pass. Historical manifest and /var fixture-path failures retain their explanations; no check was weakened to pass. |
| RC-10 | passed | All 27 protected inventories match their baseline, including registry, historical ledgers, prior plans/evidence, unrelated To-TRD packages and Electronics. The original watcher plist is unchanged and its current PID has a fresh successful check. The temporary test image is detached/removed and workers are accounted for. |

The canonical evidence for this standalone plan is [final-audit.json](../Verification/roles-capitalization/final-audit.json); the [completion report](../Verification/roles-capitalization/completion-report.md) records observed scope, checks and limits. Existing managed plan, Task and TRD ledgers are preserved.
