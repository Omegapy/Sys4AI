# Memory readiness and activation

Installing memory does not establish semantic readiness. Exact memory finds
identifiers and keywords; semantic memory finds related meaning through the
Cognee backend and configured models. A project can have working exact memory
while semantic memory is disabled and Cognee has not been activated.

The packaged consumer default is `semantic_enabled = false`, with pending model
profiles. Each new or existing project owns its configuration. Inspect that
project's files before reporting its state: the Memory Service development
configuration, for example, selects semantic capabilities, while its test and
model-spike evidence does not initialize every consumer or this checkout.

## Establish the state for this project

At installation handoff, when taking over memory work in an existing project,
and before relying on semantic retrieval, check the following evidence. During
unrelated work, keep any first-use notice brief and non-blocking; do not run
activation or repeatedly prompt about an unchanged choice.

| Evidence | What it establishes |
|---|---|
| Installed package metadata and `control_records/memory/runtime-installation.json`, when present | The selected runtime was installed. This does not prove storage, provider, or model readiness. An older/custom installation without this receipt needs its own provenance check. |
| `config/memory.toml`, loaded by this project's installed `load_configuration` | Current project and dataset identity, configuration fingerprint, semantic flag, selected models, approved local paths and capability gates. Invalid or missing configuration means readiness is unknown. |
| `.sys4ai/memory/receipts/initialization.json`, under the configured local data directory | Historical initialization evidence. Compare project ID, dataset ID and configuration fingerprint with the current configuration. A missing, malformed or mismatched receipt does not establish current readiness. |
| `exact_index_initialized`, the configured index and current source-backed exact/lexical checks | Exact storage and tested retrieval, respectively. A storage receipt alone does not prove that sources were synchronized or that a query works. |
| `provider_initialized` and current Cognee-backed workflow evidence | `false` in a matching receipt means the initializer did not activate Cognee. `true` records successful initialization at that time; it does not prove that the current backend and models work. |
| Approved model profiles plus a successful real semantic sync/recall in this project | Semantic readiness for the tested configuration and corpus. The result must show actual provider participation, valid source references and isolation from another project. An exact fallback, cached answer or fixture in a different project is insufficient. |

The current initializer writes `models_activated = false` in its receipt; it
does not issue a model-readiness certificate. Do not change that field by hand.
Retain later model and semantic verification separately with the configuration
fingerprint, package/model versions, project/dataset, observed result and date.
Recheck after a material configuration, model, provider or environment change.

Inspect configuration and receipt metadata without loading Cognee, starting a
daemon or downloading models. The packaged
[consumer handoff](../../src/sys4ai_memory/package_data/consumer_v1/control_records/memory/README.md)
contains a portable, read-only inspection command. Its output is evidence to
interpret, not an activation result. CLI `health` can describe configured
capabilities without exercising the provider; it is not semantic verification.

## Tell the human and the next agent

Use a short, project-specific handoff. For a verified default exact installation:

> Exact/keyword memory is working in this project. Semantic memory is disabled
> and is not ready; the Cognee backend has not been activated. Meaning-based
> retrieval remains unavailable until configuration, activation and verification.

If only installation or preparation succeeded, replace the first sentence with
"Memory is installed/prepared; exact retrieval has not been verified yet."
If the flag is true but evidence is absent or stale, say "Semantic memory is
configured, but its readiness and the current Cognee backend state are
unverified." Do not claim that every existing project's backend is inactive.

If the user's current instructions or a recorded decision do not already settle
activation, ask:

> Would you like me to configure and activate semantic memory and the Cognee
> backend for this project now, or keep exact/keyword memory for now?

Record the answer in the project's normal handoff or work record, with the
observed state, evidence references, scope and next action. Give later agents
the same record. Do not manufacture a success receipt or a Task merely to
record this choice.

- **Yes:** honor that authority and proceed through the applicable path below.
  Resolve only missing model, resource or migration decisions; do not ask for
  the same authorization again.
- **Later:** preserve the current usable configuration and record the deferred
  action. Revisit when the user resumes it or the agreed condition occurs.
- **Decline:** retain exact/keyword memory and record that choice. Do not keep
  asking during unrelated work.
- **No answer:** leave activation undecided and continue independent work.
  Silence is not authorization.

## Carry out an authorized activation

First identify the exact project root, dataset, caller, installed artifact and
existing initialization state. Read the project's prior decisions. Provider
installation, model selection/cache fill, local process startup and a migration
must fit the authorized scope. Documentation changes alone authorize none of
those actions. Git and publication remain separate.

1. Check the current installation and intended model profiles. The local runtime
   supports its configured Cognee adapter with local model profiles; do not
   promise an arbitrary provider, remote fallback or synthesis capability.
   Use the [installation procedure](installation-and-configuration.md) for any
   required locked provider dependencies. Respect an existing immutable
   installation receipt; a different artifact or installation profile needs
   the corresponding adoption procedure.
2. Review source exclusions, canonical permission for the requested operations,
   project/dataset identity, model resources and project-private storage paths.
   Keep caches and provider state under the configured `.sys4ai/memory/` tree.
   A model approval or model cache in the producer project is not consumer
   activation evidence. Stage the proposed settings before disturbing a
   working initialized project.
3. Choose the correct initialization or migration path below. Stop with a
   precise pending action if the current runtime cannot carry it out safely.
4. After successful authorized initialization, synchronize reviewed sources and
   test exact retrieval and real semantic recall on a small, known corpus.
   Verify cited canonical sources, actual provider results, no foreign-project
   records, local paths and no unintended remote fallback. Keep a failure or
   degraded fallback visible. Graph, temporal and synthesis capabilities need
   their own checks if requested.
5. Update the normal handoff with what actually passed, any remaining gap and
   the user's activation decision. Claim semantic readiness only for the
   configuration and capabilities that were exercised.

### A project without initialized memory

Configure and validate its approved model profiles and optional dependencies
before first initialization. If a partial or unfamiliar derived store exists,
inspect it and use an appropriate recovery plan instead of treating it as clean.
Use the installed `sys4ai-memory` command with this project's global identity
flags (`--project-root`, `--project-id`, `--dataset-id`, `--principal-id`,
`--agent-type`, `--run-id`). The reviewed route is `init preview`, followed by
`init apply --impact-digest <current-reviewed-digest> --idempotency-key <key>`
under its current action-specific permission. The direct `init-memory` route
exists for an already authorized project bootstrap and performs the same
internal preflight. Provider-enabled initialization can activate Cognee; it is
not a read-only readiness check. Neither route proves semantic retrieval until
the subsequent real workflow succeeds.

### A project already initialized with exact memory

The current installed runtime binds initialization and sync receipts to a
configuration fingerprint. Changing `semantic_enabled`, model profiles or other
fingerprinted settings makes the previous receipt incompatible; rerunning
`init-memory` or `init apply` does not migrate that receipt. There is currently
no general installed command that upgrades an initialized exact-only consumer
to semantic memory while managing that configuration transition.

After a yes decision, prepare the desired configuration and a bounded migration
or reinitialization proposal that preserves canonical sources and the current
working state. Report that runtime gap before changing the live configuration.
The next action is to provide and validate that supported migration path under
the user's activation scope, then perform it and verify the backend. Do not
invent an `activate` command, edit/delete success receipts, wipe the memory
directory or silently turn off existing exact memory to bypass the guard.

## Delivery and existing projects

Newly built consumer artifacts carry the portable handoff in
`control_records/memory/README.md`; template instructions and the initializing
agent must make it discoverable to the human and future agents. Updating these
source docs does not rewrite an older wheel, a previous consumer installation
or another project's local instructions. For an existing project, review and
adopt the relevant documentation within that project's authorized boundary,
then inspect its own state and honor its existing activation choice.
