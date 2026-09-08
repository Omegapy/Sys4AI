# Active-root adoption verification

The exact 37-file [manifest](root-adoption-manifest.json) was applied with a
[journal](root-adoption-journal.json). The root-bound role transition first copied
the legacy pair and recorded its exact receipt. The approved source definitions
were then adopted and the role helper published the final index under its lock.
All manifested final hashes, both retained legacy files and the completed
transition receipt were reopened and verified. The receipt describes the initial
copy-first transition; the later authorized definition changes are separately
attributed by the adoption manifest. Historical references were not rewritten.

All 295 installed/root tests pass:

| Suite | Tests |
| --- | ---: |
| Repository, updater and watcher | 73 |
| Installed Agent Task and root intake | 106 |
| Installed role catalog/contracts | 66 |
| Installed Task workflow | 14 |
| Installed initializer | 36 |

[Commands, logs and hashes](root-checks/results.json) retain the observed results.
Actual role validation reports both current valid pairs and generated index.
Task validation reports all 21 canonical historical records valid; startup/status
reports zero nonterminal Tasks. These read-only calls create no Task, age no
history and launch no manager. The 106-test suite includes the original root
intake/aging behavior and new ownership/unassigned maintenance controls.

The root preserves its depot governance and pre-existing ROLE edits. Common
behavior matches the reusable sources; automatic intake and 30-day closure stay
root-local. Their current native receipt fields are documented in the installed
contract. The old initializer adoption receipt remains historical; this goal's
manifest records the newly adopted package instead of rewriting that receipt.

All 42 protected baseline entries pass the post-adoption
[preservation comparison](root-preservation.json), including the live registry,
Task/TRD/plan history, To-TRD work, SOUL sources and Electronics project. The
Template was already checked current and its original watcher restored.
No Git publication or other product adoption was performed.

Highest level: installed root behavior and destination integration checks.
Native category/recovery scenarios remain the next required gate.

## Superseding native-discovered repair

The later same-ID input-handoff correction, exact destinations, preserved prior
versions and current rerun results are recorded in [the repair report](rebind-repair/report.md).
This earlier adoption snapshot remains attributable to its original hashes and checks.
