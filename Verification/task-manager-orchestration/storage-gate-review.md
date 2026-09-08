# Focused Task storage gate review

Two material completion bypasses were reproduced on 2026-09-08. Both were sent
to the component owner and Project Director. The component owner confirmed the
causes and is implementing fixes. This report records the failing snapshot; it
does not assert that subsequent source edits retain either defect.

The review used the approved plan `PLAN-20260908-6E6F545E`, the source Agent Task
helper, its orchestration tests and contract, and disposable CLI fixtures. It
focused on current evidence and completion behavior under REQ-025, REQ-027 and
REQ-030. It did not repeat the owner's pending cross-reference, conflict-round,
frozen-slot or pre-activation reconnect findings. It is not a complete audit of
all orchestration requirements.

## Reviewed snapshot and method

Snapshot directory:
`/private/var/folders/2k/jj9s1zzs5sxdb_7g557y533c0000gn/T/sys4ai-storage-gate-review-rijyrqhe`

| File | SHA-256 |
| --- | --- |
| `SKILLS-depo/agent-task/scripts/task_state.py` | `6a3113756121282503573d25121f47d5db8bb181410e4c88cc5a6526ed14811c` |
| `SKILLS-depo/agent-task/scripts/orchestration_state.py` | `5047efa0173d4417f6064af5db8b3893ff9d313da39c97445c0fca2d83d48633` |
| Snapshot `results.json` | `64a8b5260f47b74c162cbfbef34372d278e8b52537ee83662a964a3ce2f0fbc2` |
| Snapshot `reproduce.py` | `146934ac115723db3a5c1a556282e5a570edbe36a1828f543654cd16e68ee1b9` |

All state transitions ran through the public CLI in fresh disposable projects.
The fixtures supplied explicitly synthetic native receipts. There were no live
native launches, live Task mutations, or project adoption operations in this
review. The snapshot contains both source packages, the reproduction script,
machine-readable results, and preserved copies of the two final fixture trees.
Line references below refer to these exact snapshot bytes.

## Finding 1: changed dependency delivery leaves dependent work current

Location: `SKILLS-depo/agent-task/scripts/orchestration_state.py:394-395` and
`430-440`.

The current-dependency comparison runs only when `dependency_versions` is
nonempty. The sole assignment to that map is inside extra-complex reviewer
selection. A generic dependent assignment therefore keeps an empty map after
dispatch and verification; a new upstream delivery cannot invalidate it.

Observed sequence:

1. Deliver and verify generic `subtask1` as `upstream_result1`.
2. Define generic `subtask2` with dependency `subtask1` and an explicit input
   reference to the immutable `upstream_v1` artifact. Deliver and verify
   `downstream_result1` against that first interface.
3. Record and verify `upstream_result2`, whose artifact contains an incompatible
   interface. The downstream record is unchanged and still has
   `dependency_versions: {}`.
4. `execution.finish` succeeds, and `complete` returns exit 0 with canonical
   status `completed` for fixture Task `TASK-20260908-D03DB0F3`.

This violates REQ-025's required invalidation after a material input change and
REQ-027's dependency integration check. The source contract also promises that
a required-input change invalidates dependent acceptance and implementation.

Smallest fix: bind the exact current dependency verification versions at the
common assignment/input-binding boundary for every category, before work
begins. Current-result and completion checks must reject a missing or changed
binding for a dispatched dependent. A changed dependency must require current
dependent work and verification; simply filling an empty map during completion
would bless work performed against the old input. Add this two-subtask CLI
sequence as a regression.

## Finding 2: changed live delivery can complete from an old artifact copy

Location: `SKILLS-depo/agent-task/scripts/orchestration_state.py:736`,
`738-748`, and `835-844`.

`result.record` checks live `changes` and `checks` references once.
`subtask.verify` and `verified_current` later check the immutable copied artifact
and result identity, but do not rehash the result's live delivery references.
This permits an old copied result to establish completion after the actual
project output has changed.

Observed sequence:

1. A generic worker writes and registers `output/deliverable.txt` containing
   `correct delivered bytes`.
2. `result.record` explicitly binds that live path in `changes` with digest
   `36608eef5cd0af2d029cd264766d6a7df2d3ab3ff8b32cc4e1c81f3322cd23f1`.
3. After the result is recorded, replace the live file with
   `corrupted delivered bytes after recorded check`. Its digest becomes
   `be023e1086d8dd1f25c017e63824665b79c9edbf938b1de8a6bccca439c90a44`.
   Leave the immutable Task artifact copy unchanged.
4. `subtask.verify`, `execution.finish`, and `complete` all succeed. The final
   command returns exit 0 and canonical status `completed` for fixture Task
   `TASK-20260908-DF9D0B56`.

This violates REQ-025's exact-current-version boundary and REQ-027's requirement
for current direct evidence of the delivered work. It allows the canonical
lifecycle to express completion on stale evidence under REQ-030.

Smallest fix: centralize current-result validation and rehash the referenced
live changes/checks when verifying a subtask, consuming its result, and
completing the Task. Recheck the stored inspection references used by current
acceptances and verifications as part of those same freshness boundaries.
Retain old result and evidence records as history. Add the live-file mutation
sequence as a regression separate from immutable candidate mutation tests.

## Controls and verification limit

Two existing focused tests ran against the same snapshot and passed:

- `test_generic_delivered_work_and_completion`: 1 test, exit 0.
- `test_byte_edit_invalidates_accepted_synthesis`: 1 test, exit 0. This confirms
  the existing immutable-candidate mutation gate works in the fixture; Finding
  2 concerns the separately referenced live output.

The highest level reached is deterministic CLI behavior observed in disposable
projects, including the two erroneous completed lifecycle states. These results
are not native execution or end-to-end project delivery evidence. The source
owner must run the new rejection regressions after correction, and the Project
Director owns integration and acceptance. No source or installed package was
edited by this reviewer. The bounded review stopping condition was reached.

## Superseding verification: 2026-09-08 02:43:51 -06:00

Both original findings are resolved for the independently replayed scenarios
on the source snapshot below. The original failure evidence above is retained.
The final source hashes were reread after the checks and matched this snapshot.

Snapshot directory:
`/private/var/folders/2k/jj9s1zzs5sxdb_7g557y533c0000gn/T/sys4ai-storage-gate-recheck-h678shtd`

| File | SHA-256 |
| --- | --- |
| `SKILLS-depo/agent-task/scripts/task_state.py` | `3306a6e8eb9c4c14828605a0b00c97a081aa8a7ae4359f756948939c665a295e` |
| `SKILLS-depo/agent-task/scripts/orchestration_state.py` | `b1b1cf480f7a1077c6e017ea073a9adcf59b4efc456a09b37b74206df51e7cf6` |
| Snapshot `results.json` | `168c667fc9906482a91c66303f371682724062310fc9e670d46d7c1225f41aab` |
| Snapshot `reproduce.py` | `dc991e8ff278de5064312998ac67c7a81f7569b0f7242b51980c5ed070a8a1b6` |

The independent recheck rebuilt fresh disposable projects and replayed the
original public CLI event sequences. It also ran each sequence without its
invalidating change as a positive control. The script exited 0 after checking
all four expected outcomes.

| Scenario | Observed result |
| --- | --- |
| Change upstream delivery after dependent verification | The generic dependent now stores the exact `subtask1` verification digest. `execution.finish` rejects with `ORCH_DEPENDENCY_CHANGED`; direct `complete` rejects with `ORCH_COMPLETION` and exit 2. The Task stays `open`. |
| Preserve the verified upstream delivery | Dependent verification, execution finish and completion succeed; `complete` exits 0 and the Task becomes `completed`. |
| Change live delivery bytes after result registration | `subtask.verify` rejects with `ORCH_EVIDENCE_CHANGED`; execution finish and direct completion reject with `ORCH_COMPLETION`. `complete` exits 2 and the Task stays `open`. |
| Preserve the recorded live delivery bytes | Subtask verification, execution finish and completion succeed; `complete` exits 0 and the Task becomes `completed`. |

For each invalidated scenario, the canonical `task.json` hash remained exactly
unchanged across the rejected verification/completion attempts. The snapshot
stores the complete receipts and the four preserved fixture trees. Its
`reproduce.py` accepts the snapshot directory as its first argument to repeat
the same source version.

The recheck was restricted to these two findings and their positive controls.
No source, installed package, live Task, plan or TRD state was edited. These are
deterministic CLI fixture results with synthetic native receipts; the review
makes no native execution claim. The final bounded verification stopping
condition was reached.
