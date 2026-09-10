# Native context acceptance preparation

Prepared the disposable project at
`Verification/ontology-second-release/fixtures/native-context`. No Task ledger,
native manager, child launch, or native receipt was created.

The current source ontology package and contracts are copied with exact origins;
Task, Agent Task, role-management, communication and role pairs come from the
current installation. A final source refresh included the completed guard fixes.
The copied standards environment currently reports ready; actual SHACL validation
is conformant and scoped inference proves the baseline page is an Artifact.
Guards are disabled and memory is not adopted.

Start with [host bootstrap instructions](fixtures/native-context/preparation/HOST-PROTOCOL.md)
and the [valid new-Task payload](fixtures/native-context/preparation/task-new.json).
The host must create the empty fixture `Tasks` directory immediately before the
explicit helper `new` command; preparation leaves it absent. A read-only status
probe therefore returned the expected `TASKS_ROOT_NOT_FOUND`, `mutated: false`.

The three manager bootstrap templates retain null native observations until the
host supplies actual roster, capability/settings, launch and role-read evidence.
Use current revisions and the returned Task identity. After activation, only the
confirmed manager writes Task state. Its [protocol](fixtures/native-context/preparation/MANAGER-PROTOCOL.md)
requires two independent initial solvers, an unchanged original advanced packet,
a controlled later publication, explicit material reassessment and same-ID
input rebinding, then one distinct senior and canonical verification/completion.
The concrete late identity is deliberately not prepared in advance.

The [machine-readable preparation summary](native-context-preparation.json)
binds every reviewed input, protected initial hash, runtime fingerprint, and
[preflight result](fixtures/native-context/preparation/preflight-result.json).
The full origins manifest exceeds 250,000 bytes, so Task inputs should reference
the small [source summary](fixtures/native-context/preparation/source-summary.json)
that binds it. This preparation establishes fixture readiness, not native
orchestration acceptance or root installation.
