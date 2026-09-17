# Local project coordination

`curator_workspace.Coordination` binds an explicit project, branch, canonical
coordination root and local common-Git directory identity. Linked worktrees can
share that identity while retaining different checkout snapshot identities.
Case and Unicode source-scope aliases use the same normalized owner key.
Registry aliases do not create additional owners. Independent clones and remote
ownership require a separately supported coordination adapter and remain held.

Task records stay in the selected canonical root. The actual Task helper validates
records before overlapping work proceeds. An active, paused or uncertain owner
retains its scope until the existing owner protocol reconciles it. Elapsed time
cannot establish stopping or transfer authority. Invalid canonical state holds
dependent work; unrelated paths remain independent.

`copy_candidate` copies only the exact selected source inventory into a new
candidate directory. It excludes Tasks, control records, Git metadata and derived
runtime state. It never stashes, resets, cleans, commits or modifies an index.

Local integration uses the pre-created protected
`control_records/curator/integration.lock`. The selected target checkout must own
its canonical ledger for this adapter. Cross-checkout candidates can supply
immutable source bytes; they cannot supply another writable Task ledger.

The lock serializes cooperating project operations. It is not an operating-system
lock on a human editor. Every write rechecks exact predecessor bytes and retains
its parent descriptor; unexpected later content is held for review. Operating
admission still requires the selected native confinement proof and current owner.
