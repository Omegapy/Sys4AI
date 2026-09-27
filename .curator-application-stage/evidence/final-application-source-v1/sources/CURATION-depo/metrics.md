# Bounded operational measures

`curator_metrics.metrics` retains its existing read-only delivery, outcome and
current-checkpoint counts. `operational_measures` adds the measures below from
one explicitly selected evidence set. Neither function reads a live service,
schedules work, calls a model, writes a Task/knowledge record or owns a ledger.
An exact repeated input reference is deduplicated; conflicting projections of
one reference are rejected. These are counts over supplied records, not inferred
global totals or rates over an unspecified period.

| Measure | Meaning and source boundary |
| --- | --- |
| Unresolved staleness | Observed branch checkpoints lacking current reconciliation. Conflicting or unobserved checkpoints are reported separately. |
| Duplicate signals | Distinct delivery IDs for the same causal event. Repeated reading of the same ID is not duplicate work. |
| Repeated output/failure | Consecutive nonconflicting owner attempts with the same input and output/finding. Conflicting outcome keys remain separate. |
| Observed reversal | An attributed, time-ordered target-byte chain returning to a prior hash. Broken links or ambiguous equal timestamps break the chain. Different outcome hashes alone do not prove reversal. |
| Protected-write violation | An attributed actual changed-byte effect on a protected target with explicitly denied authority. Denied unchanged attempts are separate; an unattributed later human edit is not charged to the owner. |
| Dependency exposure | An advisory with assessed installed-version applicability. A newer release, missing advisory or unknown applicability remains unassessed. |
| Reconciliation delay | Each exact observed start-to-reconciliation interval in milliseconds. Missing timestamps are unknown. Summed attempt elapsed times are not wall-clock reconciliation delay. |
| Inactivity model use | Actual idle observation counters. Missing counters are unknown, not zero; calculator calls/writes themselves are zero. |

Optional observation families are ephemeral projections of existing owner/audit
receipts, dependency assessments and runtime/preflight observations. Each value
retains its exact owner reference. The caller must select one coherent scope and
verify the original source bytes and field meanings before supplying these views;
the calculator does not authenticate an audit conclusion or mint authority.
A missing family returns null measures and an explicit missing-family list.
A supplied empty family represents zero only within that selected evidence set.

Known-count scenarios must bind their source hashes, exact observed intervals,
input/output versions and fixture limitations. Synthetic audit examples establish
calculation semantics, not a live protected-write failure or a real vulnerability.
Actual idle preflight counters can establish zero work for that inspected call.
No benefit baseline or service target is invented. Edit volume is not success
and these measures never authorize continuing unnecessary work. TASK049 final
acceptance remains with the manager after the required integrated validation gate.
