# Exact operation recovery

Pause belongs to the selected canonical Task. `RecoveryController` reads it with
`task_state.validate_task_folder`; it creates no pause journal and cannot stop an
actor by changing a local flag. The existing Task `stop.request`, `stop.finish`,
`execution.resume` and lifecycle response operations retain their current checks.
A paused Task preserves pending delivery and original publication journals.
Current native interruption and reconciliation operations retain their existing
owner. Requested interruption is not confirmed stopping. Status reports the
canonical Task stage and keeps that distinction explicit.

`Application` uses fixed public memory/ontology correction and recovery owners
with exact reviewed arguments, or the existing Broker dispatcher when selected.
It passes the original owner request and returns the actual owner result. The application does not edit or re-create an owner journal, rename an
operation, or claim that a partial result is complete.

Local integration uses the existing `IntegrationOwner.execute` public API with
its current canonical Task binding. Recovery retains the same candidate identity,
original operation, selected predecessor and candidate bytes. A later human edit
holds recovery. The owner checks its selected source snapshot, dirty index,
current scope owner and required integrated validation at the actual write
boundaries. The original journal remains available after a partial operation.
No stash, reset, clean, commit, merge or push is performed by this adapter.

Memory product restoration uses `memory_maintenance.recover_reindex` and its
original owner operation. An aborted restoration does not prove current products;
required subsequent rebuilds remain pending. Ontology compile and wiki operations
use their existing public owners. Disabled optional products remain disabled.

The host supplies explicit policy, selected operation metadata,
canonical Task folder, and any exact candidate/product owner arguments. These are
embedding inputs, not authority obtained from a selection JSON file. A standalone
CLI selection remains a held preview. Connected native operation and project
readiness require their own observed evidence.

For Task transitions, the caller rechecks current writer, revision, execution and
generation while allowing the specific existing owner to validate pause/resume or
recovery from its documented current state. Task event and response calls target
only the selected canonical Task. Exact Task transaction recovery uses the public
`command_reconcile` transaction route with its original operation identity.
