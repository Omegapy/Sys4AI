# State ownership and lifetime

All paths below are relative to an adopting project's canonical coordination
root. Reusable source copies contain contracts and empty configuration only.
One logical project and selected branch resolve to one canonical coordination
root; candidate workspaces contain proposals and scoped source copies. They do
not receive competing writable Task ledgers. Unsupported multi-clone or
local/remote ownership is held rather than assumed safe under a local lock.

| Path | Owner and meaning | Lifetime and mutation route |
| --- | --- | --- |
| `CURATOR.md` | Selected Curator charter; protected governance | Durable project source; exact protected-change operation |
| `curator.yaml` | Selected identity, branches, bounds and policy references | Durable protected configuration; neutral until deliberately selected |
| `document-ownership.json` | File/section classes, canonical sources, generators and overrides | Durable protected governance; cannot reclassify itself |
| `reference-assets/CURATION-depo/` | Installed edition of reusable contracts | Exact selected setup adoption; no live records |
| `control_records/curator/events/` | Immutable delivery facts and correction requests | Durable transport; keep operation identity across retries |
| `control_records/curator/assessments/` | Immutable assessment and disposition facts | Durable evidence; references exact source and policy versions |
| `control_records/curator/operations/` | Curator coordination and exact owner-operation references | Durable delivery/recovery evidence; records real partial boundaries |
| `control_records/curator/cursors/` | Validated event positions and snapshot checkpoints | Durable small records; checked atomic replacement with recovery |
| `control_records/curator/notices/` | Selected offers, notice state and original-intent references | Durable while needed for exact selection and continuation |
| `.sys4ai/curator/` | Rebuildable caches and transient runtime observations | Disposable only through exact owned inventory; never sole-copy pending work |
| Trusted broker storage outside all candidate writable roots | Accepted policy, private grants, frozen owner code, native correlations | Protected independently of candidate code; no secrets in reusable assets or evidence |
| `Tasks/` and existing Task transaction paths | Task helper owns execution, generation, assignments, acceptance and completion | Current manager alone is logical writer after activation |
| `MEMORY/`, `memory.yaml`, existing memory publication and maintenance journals | Memory owner controls canonical notes, capture preference and derived products | Existing publication, lifecycle, recertification and exact recovery routes |
| `ONTOLOGY/`, ontology configuration, existing ontology journals | Ontology owner controls asserted knowledge, provenance, generated wiki and projections | Existing independent grants, publication and maintenance helpers |
| `Roles/` and generated `Roles/INDEX.md` | Role helper owns current role catalog | Fresh discovery and paired-file validation; retain legacy provenance |
| `control_records/project-setup.json` | Initializer owns setup editions and module adoption history | Existing checked setup/recovery protocol; preserve v1-v9 editions |
| `.sys4ai/template-update/` | Template updater owns mapping state and recovery | Existing updater only; Curator caches never consume or delete it |

Curator delivery fields have one owner and lifetime. `schema_version` identifies
their strict envelope; `event_id`, `operation_id` and `causal_parent` identify
durable delivery and effects. `project_id`, `repository_id`, canonical root,
selected branch and source snapshot bind applicability. Policy/source hashes,
assessment and disposition bind the recorded decision. Task IDs, execution
generations and publication receipt paths/hashes are references to their owners,
not copied execution state. Cursors bind the immutable delivery they advance.
Observed, assessed, canonically integrated and fully reconciled snapshots are
separate branch-bound checkpoints. Assessment alone advances neither integration
nor reconciliation.

Queue status describes delivery only: pending, delivered, held or consumed with
an attributable reference. It cannot declare a Task complete, manufacture a
publication receipt, or replace the Task owner's lifecycle. Status may join
current owner observations and must label their source and freshness. Metrics
are read-only derivations of these records; no separate metrics ledger owns
execution or creates work.

Ignore rules do not grant deletion permission. Restart and cache cleanup must
preserve pending manual corrections, grants, accepted content, partial owner
journals and later human edits. Recovery uses the same operation and exact
pre/post bytes; it does not erase history or claim cross-subsystem atomicity.
