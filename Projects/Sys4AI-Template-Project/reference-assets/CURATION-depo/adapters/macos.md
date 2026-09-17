# macOS host adapter boundary

`curator_host_macos.assets` renders a deterministic per-checkout launchd plist
from explicitly selected root identity, interpreter, installed script, selection
file, log directory and cadence. It installs nothing and creates no hook.
`lifecycle` validates exact asset hash, independent service permission, current
root identity and prior owned installation before returning a reviewed host plan.
The executable `HostOwner` is the trusted-host owner for that lifecycle. Imports,
asset generation and distribution remain inactive.

The trusted host constructs `HostOwner()` and calls
`execute(action, selection, reviewed, operation_id=..., service_permission=True,
prior=...)`. `reviewed` binds the exact plist, installed script and scheduling
selection file hashes. This service-permission assertion must come from the
host's separately selected authority; it is not a cryptographic credential and
must never be copied from model arguments. No native candidate tool is added.
The executor uses fixed `/bin/launchctl print`, `bootstrap` and `bootout` commands
for the derived per-checkout label and its fixed user LaunchAgents path. It has
no arbitrary command interface.

Install requires an absent owned label/asset, including when an unowned asset
happens to contain identical bytes. Uninstall requires the exact completed
installation receipt. For relocation, `selection` identifies the newly reviewed
checkout and `prior` identifies the old root and completed operation. The new
asset/load is observed before the old label is unloaded and its exact asset
removed. Both root identities and source hashes are rechecked. Missing anchors
are never recreated, and unrelated launch agents or hooks are never selected.

An actual directory move is selected explicitly by adding
`relocated_receipt_sha256` to the prior root/operation reference. The old root
must be absent, the new root must retain the old device/inode identity, and the
exact old receipt must have moved with it into the new operation directory.
That receipt is read at this one selected location and remains byte-for-byte
historical evidence. Its old source/asset bindings are not relabeled as current;
the new reviewed source/selection hashes are checked independently. The old
launch agent is controlled only through its exact original label and asset
bytes. Changed receipts, an appearing old root, a different physical checkout
or a detached new volume hold the move without guessing another location.

Per-checkout locks and bounded receipts live under the selected existing root's
`control_records/curator/operations/`. Each file/service boundary is marked
started before its effect. A retry checks exact source/asset bytes and freshly
observed loaded state, then reconciles an already performed effect without
repeating it. Unknown replacements remain untouched. Completed receipt replay
checks the final state and writes nothing. No cleanup removes historical receipts.

`status` distinguishes idle, pending, unavailable, blocked and ready from fresh
volume, identity, owner, loaded-process and current-probe observations. Unknown
assets survive. An unavailable external volume retains pending state without
uninstalling or deleting records. Relocation invalidates the old checkout binding
and needs explicit revalidation. Distribution never calls launchctl, starts a
service, installs a hook, acquires a model or provisions a dependency.

`HostOwner.inspect` reopens source, receipt and asset bytes and obtains fresh
launchd/PID observations. Readiness additionally requires the trusted host's
actual current runtime probe; the default has no probe and remains unavailable
for pending work. The optional probe callback is a trusted-host integration seam,
not an authenticated claim by a candidate. Offline tests inject fake launchctl
jobs/PIDs and a synthetic probe while exercising real bounded filesystem and
journal operations in disposable directories. They are not native host evidence.

The standalone launchd tick still lacks its authenticated actor/session wake
bridge. Lifecycle completion therefore reports `standalone_ready: false`.
It does not establish standalone operation, and no actual host installation is
performed by source preparation. That bridge and the native install/probe/
uninstall/relocation gate remain explicitly required and unperformed.
