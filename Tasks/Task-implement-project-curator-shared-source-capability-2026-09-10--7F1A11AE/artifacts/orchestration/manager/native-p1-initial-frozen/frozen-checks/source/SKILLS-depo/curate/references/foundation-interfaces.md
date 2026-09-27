# Foundation interfaces

`load_policy(path)` reads at most 250,000 bytes. `validate_policy(document)` checks
the strict version 1 structure. `inspect_policy(document)` reports missing
operating selections. These paths are pure reads and create no runtime state.

`evaluate_operation(policy, accepted_entitlement, operation, observation)` checks
the exact selected operation using observations supplied by the trusted caller.
It cannot verify an issuer by parsing candidate data. Only the protected broker
may supply the previously accepted entitlement. Omitted permission classes deny;
specialized capability descriptions confer no entitlement. Null bounds mean
unselected and zero permits no work. Automatic memory capture requires its own
current opt-in; explicit correction authority is evaluated independently.

Protected canonical mutations remain owned by the existing Task, memory and
ontology helpers. No CLI command in this edition publishes canonical state.

## Implemented owner and broker interfaces

The broker exposes a closed tool union: policy inspection, target classification,
assignment-scoped artifact submit/read, Task create/event/response, independent
memory and ontology publish/recover, and fixed controls for already bound native
actors. The public CLI continues to expose only pure status and validation.
Missing operating proof holds canonical work. No arbitrary command, executable,
import, environment or protocol proxy is a candidate operation.

`Broker.dispatch_verified` accepts only the live context installed by its
protected native transport. Accepted operations, automatic/explicit request
origin, owner grants, source closure and profiles are private bootstrap inputs.
Candidate arguments cannot select them. Every target's actual class, owner and
route must match the independently accepted permission. Existing helper owners
perform canonical writes and their lock-time rechecks. The broker retains
private exact grants, original owner results and delivery states; it does not
replace owner journals or claim cross-owner atomicity.

`VerificationAdmission` is a distinct trusted-only first-proof route. Its exact
host-reviewed digest binds a newly created synthetic root, root identity/marker,
source manifest, runtime, profile, tools and expiry. Candidate requests and
project configuration cannot select it. It never establishes production readiness.

File inspection uses directory descriptors, no-follow/nonblocking opens and
regular-file/link/inode checks. Permission profiles and hashes are input
contracts, not OS proof. The full enabled-channel and native category proof must
remain current before operating admission.
