# Native-discovered input-handoff repair

The live mixed-category test found an internal error when a rejected coding
solver received a correction while depending on an already accepted analysis.
`assignment.inputs` temporarily removed the solver's assignment before checking
dependencies. The analysis freshness check scans candidate provenance, including
the coding candidate, and dereferenced that temporarily missing assignment.

The failed operation did not publish canonical state or a transaction intent.
The disposable Task remained valid at revision 59. Its failed event UUID and an
independently saved pre-command checksum were unavailable; the evidence does not
invent either. The observed revision-59 checksum, exact input payload, original
error, traceback and old helper are retained in this directory. No worker was
woken while the gate was unresolved.

The repair leaves the original assignment available until reservation checks
succeed. It excludes only that same assignment object from its own slot/write
ownership check. Other Task owners, native identity, role reads, generation,
packet digests, scope, candidate history and dependency acceptance remain checked.
The public CLI and persisted schema are unchanged.

The new regression reproduces the original `KeyError: coding_a` on the old
helper and passes on the repair. A second regression confirms another active
writer still blocks a rebind without changing canonical bytes. The independent
review replays the preserved native payload in memory and checks seven adjacent
rejection gates. It reports no actionable findings; it publishes no returned
state or native action.

| Observed check | Result |
| --- | --- |
| Original mixed-category rebind regression before repair | Failed as expected, reproducing the native error |
| Focused rebind CLI tests after repair | 3 passed |
| Repaired source Agent Task suite | 89 passed |
| Repaired installed root Agent Task suite | 108 passed |
| Repaired delivered Template Agent Task suite | 89 passed |
| Repository/updater/watcher contract suite | 73 passed |
| Independent current-payload replay and adjacent controls | Passed; no native Task mutation |

The exact [adoption manifest](adoption-manifest.json) records two package files
in each selected destination: designated Template, active root, paused native
fixture, and the disposable source/Template used for starter testing. The
checked updater reported exactly two Template updates and no other changes.
It now reports all 81 managed destinations current. The original watcher plist
was retained and restored; its new PID has a fresh successful check. The
source, root and Template manifests retain links to their pre-repair versions.

The host-provided validation wrapper also now writes new catalog snapshots in
the manager's declared `coordination/` scope. Earlier context snapshots remain
intact. This harness correction changes no problem baseline or queued packet.

The original manager subsequently confirmed the unchanged revision-59 state,
reconnected, committed the same solver's corrected inputs at revision 61, then
woke it and recorded its actual running state at revision 64. The queued native
handle briefly reported `pending_init`; its raw status was retained, counted
conservatively for capacity and never relabelled as stopped or completed.
The final native category audit retains the resulting version/review sequence.

The earlier 295-test root and 175-test Template reports remain historical
snapshots. With the two added tests, the current checked compositions are 297
root tests and 177 Template tests. Unchanged suites retain their original
receipts; affected Task suites and repository checks were rerun as listed above.

Evidence: [test results](test-results.json), [independent review](independent-review.md),
[original payload replay](original-payload-after.json), and
[original native defect](rebind-defect-report.json). This repair does not claim
that the entire native scenario has completed; its remaining review, conflict,
implementation and integration gates are recorded separately.
