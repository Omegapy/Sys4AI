# Typed action guards

The enabled `sys4ai-actions-v1` contract checks the supported ontology, memory,
Task, TRD, plan, role, Template, and setup dispatch paths. It retains stable
action IDs and schema version 1. Unknown rule names, lifecycle vocabularies,
input types, provider paths, and generic or unknown capability references fail
closed. `contracts-v1.json` and `action-shapes-v1.ttl` are exact selected inputs.

Each public adapter runs its current structural readers first. The guard then
reads the selected target and builds observed facts. Task records come from the
Task catalog; TRDs and plans come from their owning selectors; memory records
come from their parser and configuration; ontology proposals are checked against
the actual current and proposed graphs. Role catalogs, setup receipts, Template
collection state, and profile configuration supply their respective facts.
Caller-supplied `_semantic_state` is rejected. An independently called validator
cannot invent an observation packet for a different owning interface.

The guard classifies actual selected paths against the current canonical stores
and configured ontology files. It checks requested input identity and exact
versions, memory record transitions, Task and document lifecycle edges, selected
Task orchestration generation and assignment identities, plan update targets,
and setup receipt state where applicable. These checks do not execute mutation
callbacks or issue an authorization grant. The owner's complete candidate,
authorization, transaction, and post-write verification checks remain active.

Concrete capabilities are resolved from the exact installed provider's actual
`ONTOLOGY_GUARDED_ACTIONS` declaration. For example, the Task helper provides
`TaskLifecycleManagement`, while the memory helpers provide `MemoryMaintenance`.
The action contract states its required capability; a mismatch with the actual
provider fails SHACL validation. A generic `core:Capability` cannot stand in for
an observed provider. Capability availability does not identify an authorized
actor. The three current destination-local governance files must also exist,
contain text, and remain at the checked hashes.

Before a version-2 ontology action can be conformant, its complete proposed
extension, shape, and companion bytes pass the selected standards checks and
finite inference checks. Formal assertions require an explicitly enabled
inference profile. A missing profile, unsupported rule, or inconsistent candidate
fails the action without enabling anything. Selected project shapes are checked
against their complete authoring data alongside the action facts.

The shared SHACL shape requires actual input, target, capability, and governance
facts. A bounded selected-action shape applies the declared input/target type,
concrete capability, positive target revision, stable identity format, and
permitted lifecycle edges. Validation must return a complete conformant result.
Violation, unsupported rules, missing evidence, unavailable backend, timeout,
and unknown results do not invoke the underlying continuation. Diagnostics name
the action and the selected contract and governing versions. Owning interfaces
that retain only exception text still receive a bounded action, condition,
contract path/hash, backend status, and safe finding identifiers. Raw arguments
and RDF values are not included in that text; structured details remain separate.

One monotonic deadline covers the complete semantic decision, with a maximum
of five seconds or the lower selected `guard_seconds` value. Candidate RDF
projection, selected-shape validation, formal inference, and action SHACL share
the same cancellation object and remaining worker limits. The existing worker
supervisor cancels running processes at expiry; no late result can dispatch the
owner. Synchronous filesystem preparation is checked at phase boundaries, so
this is an enforced evaluation budget, not a real-time OS scheduling guarantee.
Execution receipts state the selected budget and observed evaluation duration.
Exact hashed previews retain the stable budget and omit measured elapsed time.

The complete core record validator checks record types, references, cardinality,
and lifecycle before candidate graph validation. Guards reuse the exact candidate
RDF graph for selected project SHACL and action shapes. They do not regenerate
equivalent per-record SHACL constraints during this bounded decision. The normal
owning publication validation, including its complete graph checks, remains
independent and unchanged.

The decision binds original arguments, observed facts, target snapshots, current
ontology and rule inputs, and current governance/Task/role context. Owning lock
checkpoints reject changed arguments or state. Receipts keep semantic conformance,
current owner authorization, actual helper result, and reopened effects distinct.
Existing exact pre/post recovery remains supported, including an already-written
accepted memory or ontology operation. A pass is not reusable for another call.
An accepted v2 intent can identify an extension or shape at its retained pre/post
version while the companion update is still pending. The guard validates the
complete proposed state, retains the actual current target snapshot, and accepts
its own newly written intent only after the owning lock checkpoint. Unrecognized
bytes or a changed accepted intent remain a conflict.

Guard setup and repair use a separate `GuardSetupRequest` shape and their exact
native setup grant. A selected old guard can install the typed contract through
the existing immutable repair manifest because its binding and schema-version
interfaces remain compatible. Repair retains its accepted old rules while
writing exact reviewed files, writes the companion last, and reopens the new
enabled bindings. Use a fresh helper process after repair. Ordinary guard paths
must not disable the profile or silently adopt changed code.

The delivered adapters target the canonical managed stores and the registered
Template/setup routes. Direct filesystem writes, arbitrary mutation callbacks
outside those interfaces, native host tools, and third-party applications remain
outside interception. The guards provide no cross-system atomicity or filesystem
sandbox. Test-generated native grants are fixture evidence only.
