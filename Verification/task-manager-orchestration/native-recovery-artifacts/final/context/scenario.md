# Bounded native stopping and recovery scenario

This is the authorized TASK-034 validation protocol for
PLAN-20260908-6E6F545E. It is a scenario definition, not observed evidence.
Run it only after the mixed-category scenario has completed. Use a separate
disposable project and one canonical test Task. Keep the live depot Task
history, user settings and other projects unchanged.

The test Task deliberately contains an unfinished deliverable criterion.
Its expected terminal lifecycle is cancellation, never successful delivery.
Successful validation of that cancellation is separate from Task completion.

1. The host reserves one manager, records its actual native spawn receipt and
   verified role-read readiness, and activates it. The manager becomes sole
   writer. On continuation, reconnect the exact native manager and execution
   using a fresh actual roster; duplicate manager reservation must fail.
2. The manager defines one generic bounded worker with a distinct writable
   marker directory and a stopping condition. Inspect a fresh role catalog,
   exact inherited settings and available capacity. Reserve before native spawn.
   The worker writes one small readiness marker and waits for control. It may
   not write canonical state or complete its deliberately unfinished deliverable.
3. Exercise a controlled delayed-receipt case: retain the actual spawn receipt
   in the test evidence but delay its canonical import. Mark the original
   reservation uncertain with an explicit test explanation. Reconcile that
   same native ID and import its real receipt; never launch a substitute.
   This proves recovery of a deliberately delayed receipt, not an actual
   network or native-service failure.
4. Request pause through the helper. Verify dependent dispatch is rejected and
   stop completion is rejected while worker ownership is unresolved. Request
   actual native interruption, inspect the returned status and marker bytes,
   and record the worker observation before finishing the stopped execution.
   Record the actual `pause` lifecycle through the same helper after stopping;
   preserve unfinished criteria and append-only history.
5. Exercise a requested-setting-change failure with a clearly labelled
   deterministic payload: resuming with different settings must require manager
   replacement. Do not change any real model, reasoning setting, spawn override,
   or user configuration. Report actual mid-run model switching as not exercised.
6. The first manager returns stopped-state evidence and performs no more writes.
   The host observes its actual completion and every started worker. A replacement
   attempt omitting an unresolved owner must fail in a deterministic fixture;
   the live replacement includes all actual observations and known file changes.
   Use the original bootstrap authority to revoke the prior generation and
   return writer ownership to the host.
7. Select and launch a distinct replacement manager from fresh role evidence.
   Record receipt, role reads and exact activation for the new generation.
   Reject a delayed old-generation operation through the public helper without
   changing canonical bytes. The new manager inspects the retained marker,
   histories and unfinished criterion, records the cancellation result, and
   cancels through the real lifecycle route. It must not label work delivered.
8. The host reopens the final canonical record, projections, marker and actual
   native roster. Account for every started instance, both generations and all
   observed changes. Retain concise receipts and hashes without raw transcripts.

All native agents inherit the exact model and reasoning effort through the
verified full-history runtime guarantee; no override arguments are used.
Literal identity telemetry remains unavailable and is not invented.
An unsupported or unsafe live failure case uses the existing deterministic
fixtures with explicit provenance. Unexpected helper defects stop dependent
testing for a bounded correction; no gate is bypassed to obtain a green result.
