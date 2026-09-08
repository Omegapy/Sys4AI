# Native stopping and recovery validation

The controlled recovery scenario passed. The disposable Task
`TASK-20260908-A8B65949` ends **cancelled** at revision 23, generation 2,
with execution stage `stopped`. Its deliberately unfinished delivery criterion
is unchanged. No delivery exists and no successful verification is claimed.

The root independently rehashed all 162 final indexed files and the handoff
references, validated the actual canonical record without mutation, checked
86 protected files and 19 prior responses, and compared generation-1 events.
It read the cancellation Response and observed the actual final roster:

| Native instance | Final observed state | Canonical attribution |
| --- | --- | --- |
| `/root/recovery_manager` | completed | Generation 1 manager revoked during transfer |
| `/root/recovery_manager/marker_worker` | interrupted | Original worker retained, then revoked during transfer |
| `/root/recovery_replacement` | completed | Generation 2 manager and final writer |

Actual operations cover same-ID manager reconnection, one worker launch,
interruption from running to interrupted, stopped-state recording, pause,
prior-owner reconciliation, distinct manager replacement, role-read activation
and the real cancelled lifecycle. The final canonical manager assignment retains
its writer attribution; the separate native observation establishes completion
of its turn.

Six negative controls passed without canonical mutation: duplicate manager,
dispatch after pause, lifecycle pause before stop, stop before ownership
observation, different-settings resume, and a stale generation operation.
Existing deterministic suites separately cover omitted or unresolved owners.

The delayed receipt was deliberately withheld from canonical import while its
real native return was retained. It was reconciled to the same original worker,
never relaunched. Stale-generation and different-settings payloads were controlled
cases. They do not prove an organic network failure or actual model switching.
Literal model/effort telemetry is unavailable; every real spawn used the verified
full-history inheritance guarantee without overrides. No user configuration
was rewritten.

The first host replacement payload used the native basename instead of the
canonical logical assignment ID. The helper rejected it without mutation.
The host corrected the mapping from canonical state. Its original evidence
is retained; it was an input error, not a helper defect.

[Root receipts](native-recovery-receipts.json) record current hashes, validation,
controls and native accounting. [The evidence manifest](native-recovery-artifact-manifest.json)
retains 164 final files. The earlier generation-1 snapshot preserves its original
canonical and helper-log boundary. These snapshots are evidence, not duplicate
Task ledgers; the original disposable project remains authoritative.

Highest verification: runtime behavior observed for native recovery controls
and the expected cancelled fixture lifecycle. All three started recovery
instances are accounted for. No unconfirmed activity or unmet scenario criterion
remains. The separate mixed-category test establishes completed delivery.
