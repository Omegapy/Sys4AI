# Scheduling and notices

The starter has no selected project or branch, active schedule, external
notification destination, service or hook. Preparation specializes destination
identity only. Selected cadence has finite work/model/candidate/concurrency
budgets and an iteration limit. The due calculation retains pending work when
limits are reached or the current runtime is unavailable.

`Application.tick(action, request, actor=actual_actor, observation=view, now=time)`
uses one explicit host-selected view of existing usage and runtime evidence.
An existing Broker host can supply its actual `context` callback instead.
The view binds the current policy, branch, observed time, cadence timestamps,
usage, iterations and exact source-record references. Before dispatch it reopens
those references, checks their bytes, requires an observation at most 60 seconds
old and verifies that the selected operation fits the remaining budget. The host
must derive this view from its current owners and refresh it after operation
results; the application does not infer measured usage from a requested budget.
No separate scheduler ledger is created.

Both manual and scheduled requests use `Application.run` and the same current
Task and operation owners. An inactive tick reads no runtime evidence and performs
no owner operation. Standalone `tick --selection ...` is a due-status preview;
it does not start an actor or persistent schedule. Missing native session support
remains unavailable rather than being synthesized from selection files.

The read-only scheduler supplies no Task or publication lifecycle authority.
Operation retries retain their exact owner identity and journal. The resulting
owner outcome remains distinct from observed scheduling readiness, actual
integration and fully reconciled products.

Meaningful scoped changes, failures, conflicts and required actions produce a
concise item, impact and next action. Routine success and unchanged notices stay
quiet. A digest/channel is optional selected configuration. No check sends an
external message.

Per-checkout macOS assets and status use [the host adapter](adapters/macos.md).
Fresh runtime and process observations are needed for ready. A loaded job or old
successful log alone is insufficient. Detached volumes preserve pending work.
Relocation rechecks selected identity and current ownership.
