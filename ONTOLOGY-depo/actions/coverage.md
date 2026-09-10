# Guarded action coverage

The action contract is `contracts-v1.json`. It gives each supported action a
stable identity, typed input and target, capability reference, governing-source
references and exact owning helper/symbol. It defines 43 normal routes and one
optional project-local Task intake route. The optional route does not install
depot intake policy in a generic project.

| Family | Owning public boundaries |
| --- | --- |
| Ontology | `ontology_publication.preview`, `publish`, `recover`; the accepted commit continuation retains its original lock and pre/post checks. |
| Memory | `memory_recovery.transact` and `recover`; publication aliases delegate there. Saved proposals, capture/settings, reindex and reindex recovery have their own adapters. |
| Task | Creation, response/lifecycle/orchestration, projection rebuild, reconciliation, transaction recovery, redaction recovery and exact lock repair. A local `command_intake` must declare its additional adapter when present. |
| TRD | `Store.create`, `update`, `set_status`, `migrate`, `reindex`. |
| Plan | Create, baseline/phase/task/evidence/lifecycle changes, the shared mutation continuation, projection rebuild, index rebuild and reconciliation. |
| Role | Role creation, transition, case rename, index rebuild and index publication. |
| Template | `template_update.update` apply and `recover`, including recovery reached before a fresh update preflight. The read-only check route remains read-only. |
| Setup | `run_initialization`, `run_module_adoption`, and `ontology_profiles.configure_profile`; their existing locks, exact configuration selection and current authority remain authoritative. |

The portable wrappers first bind the real function signature and project root.
Only exact path fields are inspected as files. Inline content, byte/base64
envelopes and maps keyed by filenames remain data; malformed explicit paths
produce bounded diagnostics without echoing the supplied value.
They perform the owner's available structural checks, normalize the exact
request and evaluate its selected semantic contract through the actual
constrained SHACL worker. Task, TRD and plan lifecycle checks add current typed
state and identity facts without authorizing the transition. Existing source,
evidence, approval, native actor, manager generation, scope, transaction and
post-write checks still run in their original owners.

Every enabled decision binds normalized arguments, target bytes, ontology and
extension inputs, rules, the three root governing files, current Task and role
content, explicit authority/source files and all declared adapter digests.
The immutable bootstrap also binds the guard engine and repair helper. A cached
guard from another project or a changed loaded engine fails closed. The owning
lock callbacks recheck the decision. Replacement callbacks retain all other
sources while the owner checks selected targets against its accepted pre/post
hashes. There is no cross-helper or operating-system atomicity claim.

No companion or an explicitly disabled guard profile preserves ordinary
standalone behavior without importing the ontology runtime. Enabled checks
reject invalid or ambiguous contracts, unsupported actions, stale code or
context, missing backends, worker failures, limits and unknown results. They
never turn a failed check into a disabled profile. Semantic evidence is returned
under `ontology_guard` alongside the owner's original receipt. A returned
semantic pass, the owner's authorization, its execution result and its
post-verification remain distinct claims; an immutable owner receipt is not
rewritten to insert guard metadata.

`coverage_manifest` audits current installed declarations and hashes. Guard
enablement additionally requires the actual-backend family matrix, reopened
positive results and evidence matching the current owning and guard code.
Registration alone is insufficient. The tests in the ontology package call
real installed fixture helpers, use the actual selected standards environment,
exercise all six required family cases, mutate governing context at original
lock callbacks, and exercise pending transaction and projection recovery.
Their native receipts and fixture bootstrap are explicitly synthetic; they do
not establish real root actor authority or consumer adoption.

Direct host, shell and third-party writes are outside this integration. Calling
private filesystem primitives or a Python wrapper's private implementation
outside its public owning transaction is also outside supported dispatch.
Editor races that ignore cooperative locks remain observable conflicts, not
prevented operating-system writes. Role case behavior retains the owning
helper's platform checks; unexecuted filesystem-specific tests remain labeled.

## Explicit bootstrap and repair

`ontology_guard_setup.preview_enablement` is read-only. It verifies the full
current adapter inventory, exact action/repair bindings and actual dispatch
evidence before returning a reviewed manifest. `apply` requires the separate
current setup grant. It reuses the existing ontology native/time/Director/Task
checks, checks the exact manifest and overlapping manager scopes, and writes
through the existing ontology publication lock and atomic writer. It does not
broaden semantic publication grants.

The selected companion change is last. Immutable accepted setup intents,
bootstrap/adapter bindings and completion receipts live under
`control_records/ontology/guard-bootstrap/`. `preview_repair` freezes the exact
pre/post contents and retained semantic rules. `recover` uses the accepted
intent with current authority. Every selected file must still have one of its
accepted hashes. Unknown bytes and unavailable validation block recovery and
remain preserved. Ordinary guarded calls stay blocked while an interrupted
upgrade has stale bindings. Repair cannot disable the guard or provision a
backend. Backend restoration uses separately authorized provisioning.

Other profile changes use `ontology_profiles.configure_profile` and its existing
exact native Director grant. Its enabled-guard adapter checks semantics before
that authorizer and again under the original publication lock. It changes only
the selected optional profile's enabled flag and retains the existing intent and
receipt recovery. Guard repair cannot change backend, publication, import or
limit configuration. Enabled guards require the standards profile; the profile
owner rejects disabling that dependency. Reprovisioning a missing standards
environment remains a separate explicitly selected operation.

The setup grant contains exactly `schema_version: 1`, `operation` (`guard-setup`
or `guard-repair`), `preview_sha256`, `actor_id`, `actor_kind`, `observed_at`,
`expires_at`, `native_receipt`, `scope`, `reviewed_records`, `task`, `project_id`
and `config_sha256` (current core ontology configuration). Scope lists every
selected file in payload order; reviewed records repeat each path and its
expected/post hashes. The native observation format and five-minute maximum
are the existing ontology authority contract. A manager additionally needs the
exact current Task binding and assigned writes. These are cooperative local
checks, not authentication of a fabricated native receipt.
