# Operations guide

This guide covers the current local Sys4AI Memory Service checkout. It is an
operator and developer reference, not an activation approval. The product's
configuration selects an approved local profile; consumer defaults are
exact-only. Neither configuration nor installation establishes live readiness.
Follow [memory readiness and activation](memory-readiness-and-activation.md) to
check this project's evidence, inform the human and next agent, and ask about
semantic/Cognee activation when the choice is undecided.

## Evidence labels used in these guides

| Label | Meaning |
|---|---|
| Contract implemented | A versioned model, adapter, or service boundary exists and passes applicable static or focused tests. |
| Fake/temp verified | Behavior ran against a fake or in-memory provider, ASGI test client, or disposable temporary directory. It did not touch live project memory. |
| Benchmark measured | A stated command ran on the documented machine and corpus, and its numeric result is retained. |
| Real-provider unverified | Cognee has not completed the named workflow with a real local store and approved model pair. |
| Decision pending | Product or security authority has not selected a required policy; the implementation must fail closed. |
| Not published | No package publication, product remote, listener, deployment, or hosted service was created. |

Do not shorten these labels to "working" or "production ready." A passing
contract test establishes less than a live provider workflow, and a model smoke
does not establish memory-service integration.

## Guide map

- [Memory readiness and activation](memory-readiness-and-activation.md) separates
  installation, exact/keyword readiness and verified semantic/Cognee operation,
  and covers the human decision and existing-project migration limitation.
- [Installation and configuration](installation-and-configuration.md) covers
  Python 3.12, locked extras, the no-cloud-key posture, configuration gates,
  local model state, and credential references.
- [Source and profile registration](source-and-profile-registration.md) covers
  exact source rows, default-deny discovery, `base@1`, extensions, and profile
  migration triggers.
- [Operator workflows](operator-workflows.md) covers initialization, source
  explanation and sync, retrieval, typed writes, lifecycle controls, rebuild,
  and package exchange.
- [Backup and recovery](backup-and-recovery.md) covers asset classes, recovery
  order, generation rollback, drift, privacy incidents, and package recovery.
- [Observability and troubleshooting](observability-and-troubleshooting.md)
  covers health, metrics, audit data, operation status, and common failures.
- [Developer guide](developer-guide.md) covers provider-neutral boundaries,
  single-writer composition, tests, and extension development.
- [Dependency upgrades](dependency-upgrades.md) defines the compatibility,
  migration, and rollback gate required before changing a dependency.

Security contracts remain under [the security directory](../security/). The
[decision register](../decisions/decision-register.md) is the source for current
approval status, and [the release evidence guide](../verification/README.md)
defines what counts as proof.

## Current operational stop conditions

Stop before activation when any of these conditions is true:

- `configuration_status` begins with `stage0-`;
- a value required for the requested capability begins with `pending-`;
- a required reviewed initialization, rebuild, import, or forget preview digest
  is missing or no longer matches current state; direct authorized bootstrap
  uses `init-memory` with internal preflight;
- current canonical permission cannot be read and validated;
- the request would cross a project, dataset, source, or derived-data boundary;
- the request requires a semantic capability but the local model pair and
  profile are not approved;
- a required export/encryption policy is unresolved for this project;
- a network listener or shared service would run without the required
  authentication and backend isolation; or
- a command would operate on canonical files outside the normal governed
  project workflow.

Current local artifacts are not a substitute for backups of canonical project
sources. See [backup and recovery](backup-and-recovery.md) before deleting or
rebuilding derived state.

## Known limits in this checkout

- `LocalMemoryRuntime` constructs the installed local command from canonical
  project files and composes `MemoryService`. Non-inspection operations need a
  matching initialization receipt and the required storage/provider state.
  There is no general installed command to migrate a fingerprint-bound
  exact-only initialization to changed semantic settings.
- The HTTP factory does not start a server, and the MCP adapter is not a running
  MCP server. There is no metrics or audit CLI command.
- `MemoryService` audits the public operations and initialization/status controls
  in focused tests. The separate `AdministrativeActionExecutor` also exercises
  every allowlisted source/profile/configuration/permission/telemetry change
  through fresh canonical authorization and audit capture. No live project
  control-plane change has been verified.
- Dispatcher tests cover the common guard with injected handlers and directly
  exercise built-in initialization preview/no-write, detailed health, and the
  source-to-exact-index/provider sync path. They do not directly exercise every
  other built-in operation integration.
- Exact/keyword bootstrap and retrieval have consumer evidence. The current
  project's receipt and source-backed queries still determine its readiness.
- One integrated offline acceptance fixture forces socket connection attempts
  to fail, then completes registered-source listing and sync, in-memory
  provider remember, hybrid recall, deterministic rebuild preview/activation,
  provider-neutral test export, and detailed health while preserving the
  canonical source bytes. This proves the core service has no mandatory cloud
  dependency at the conformance-provider level. It does not activate the
  tracked profile or replace the required real-Cognee validation.
- A retained synthetic local-runtime benchmark measures guarded hybrid recall,
  service-shell startup, one-source sync, 100,000 fragments, 100,000 relations,
  and peak process memory. A supplemental stress run loaded 1,000,000 relations
  and completed one endpoint-indexed hybrid recall. Both use the in-memory
  conformance provider; real Cognee, persistent provider startup, mixed
  concurrency, and sustained full-scale behavior remain unmeasured.
- The retained local model spike exercised the approved model pair and a
  bounded Cognee semantic run. That evidence does not establish current
  semantic, graph or temporal readiness for this checkout or a consumer.
  The explicit synthesis/citation boundary uses an injected model port.
- The decision register records approved local reviewer, retention, encrypted
  exchange and derived-profile choices. Shared backends and automatic feedback
  remain disabled; a consumer does not inherit product activation authority.
- Rebuild, exchange, lifecycle, security, and recovery tests use temporary or
  fake/in-memory state. Complete real-Cognee end-to-end recovery remains
  unverified.
- `MemoryService` serializes mutations inside one process. The installed local
  runtime also uses a project-local file lock for initialized storage; this
  does not establish a shared-service or network deployment.
- The interface suite currently emits upstream Starlette/httpx and AnyIO
  deprecation warnings. It passes, but the warnings should be reevaluated during
  the next dependency compatibility review.
- No project-local product Git repository, product remote, package publication,
  deployment, or hosted endpoint exists. The parent depot ignores this product
  directory.
