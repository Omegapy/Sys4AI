# Installation and configuration

Read [memory readiness and activation](memory-readiness-and-activation.md) at
installation handoff and before activating an existing project. Installation,
exact/keyword verification and semantic/Cognee verification are separate
states. Tell the human and future agents which state this project has reached
and ask whether to activate semantic memory when that choice is undecided.
The default consumer is exact-only; inspect each existing project's actual
configuration and evidence instead of assuming that default still applies.

## Immutable consumer installation

Consumers use a versioned wheel built from this product, installed non-editably
in their own `.venv`. They never import the editable sibling checkout or copy
its runtime source. From this product root, with implementation/install authority:

```bash
.venv/bin/python tools/build_consumer_artifact.py build --project-root "$PWD"
```

The JSON result names an `artifact.json` under
`dist/consumer/<version>/<source-manifest-sha256>/`. That immutable directory contains the
wheel and hash-locked core/Cognee dependency exports. The receipt records the
source manifest, exact wheel member hashes, Python, uv, all build-tool versions,
the dependency lock digest, and the product's own Git HEAD when one exists.
Missing product Git metadata is recorded as null; an ancestor repository is
never used as its provenance. No artifact is uploaded or published.

The build installs only the hash-pinned `tools/build-requirements.lock` in a
temporary build environment, exports runtime requirements with `uv --locked`,
and uses a fixed `SOURCE_DATE_EPOCH`. Two builds of unchanged inputs must
produce identical wheel bytes. Source changes during the build stop receipt
publication. Updating build requirements is a separate reviewed tooling change;
ordinary builds never rewrite either lock.

Pass the returned receipt path and the real consumer root to the installer:

```bash
.venv/bin/python tools/build_consumer_artifact.py verify /absolute/path/artifact.json
.venv/bin/python tools/build_consumer_artifact.py install /absolute/path/artifact.json \
  --project-root /absolute/path/consumer --python "$PWD/.venv/bin/python"
```

It verifies artifact hashes before creating an environment, installs the locked
dependencies and exact wheel, then checks module origin, non-editable metadata
and every installed package member. The project-owned result is
`control_records/memory/runtime-installation.json`. An equivalent rerun verifies
the existing install; a different wheel requires a new adoption decision.
Existing unrelated environment packages are not removed. The default core
profile supports exact/lexical memory without loading Cognee or local models.
Use `--with-cognee` only when provider installation is part of the authorized
scope. Installation does not initialize memory or download models.

Preparation copies the portable `control_records/memory/README.md` handoff
from that wheel. Read it with the user after installation and follow its state
checks and activation choice. An updated source guide does not update an older
immutable wheel or overwrite documentation in an existing consumer. Build a
new artifact for future installations; review an explicit documentation
adoption for an existing project.

The explicit build/install test uses disposable source and consumer directories,
including a post-install source edit that must leave installed bytes unchanged:

```bash
SYS4AI_RUN_ARTIFACT_BUILD=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -q tests/test_consumer_artifact.py
```

## Supported local environment

The first release line uses Python 3.12 and `uv`. Install the exact locked
development and Cognee extras from the product root:

```bash
uv sync --locked --extra dev --extra cognee
uv run --frozen python --version
uv run --frozen python -c 'import importlib.metadata as m; print(m.version("cognee"))'
uv run --frozen python -c 'import importlib.metadata as m; print(m.version("fastembed"))'
```

The current checked environment reports Python 3.12, Cognee 1.5.3, and
FastEmbed 0.8.0. Installation proves dependency availability only. New projects
use one direct `init-memory` invocation after project preparation; root adoption
retains its separately reviewed `init preview` / `init apply` route. Both use
the same validation and initialization core, and receipts distinguish exact
readiness from provider/model activation.

An initialization receipt records storage initialization; it does not prove
successful synchronization, retrieval or model readiness. In particular,
`models_activated = false` is written by the current initializer even when a
provider initializer ran. Current semantic readiness needs real project-local
workflow evidence. For an already initialized exact-only consumer, changing
the semantic flag or model configuration invalidates the bound fingerprint.
There is no general installed upgrade command for this transition; follow the
[existing-project migration boundary](memory-readiness-and-activation.md#a-project-already-initialized-with-exact-memory)
before changing a working configuration.

Use `uv sync --locked`, not an unlocked sync, for reproducible installation.
Use `uv run --frozen` for normal checks. A deliberate dependency upgrade follows
[the upgrade procedure](dependency-upgrades.md) and may update `uv.lock` only
after compatibility and migration review.

Provider-neutral encryption also requires the external `age` CLI. The current
reference Mac uses Homebrew `age` v1.3.2:

```bash
brew install age
age --version
age-keygen --version
```

Do not place an identity file in this project or pass private key material as a
command argument. The service invokes `age` with a public recipient and reads a
separately managed identity only for an explicitly authorized import.

## Approved local model evidence

The retained product spike used Ollama 0.33.2 and an ignored product-local
`models/ollama/` cache with `llama3.1:8b`, Q4_K_M, and a 4.92 GB model layer.
Its ignored `models/fastembed/` cache held
`sentence-transformers/all-MiniLM-L6-v2`. A bounded loopback-only LLM smoke
returned `LOCAL_OK`, an offline embedding produced 384 finite dimensions, and
a real Cognee 1.5.3 semantic remember/recall run preserved Sys4AI metadata.
The exact environment and measurements are retained in
[the local-model evidence spike](../verification/MEM-OQ-004-local-model-spike.md).

These are historical measurements, not proof that a current project has those
models available or activated. The current runtime confines consumer model
caches to the configured `.sys4ai/memory/models/` tree; do not copy a producer's
state or infer readiness from its older cache directories.

The pair is approved for explicit local initialization only. Configuration load
does not start Ollama, initialize Cognee, or fill either cache. Do not start a
daemon or pull another model as an implicit configuration step, and never allow
a missing local model to trigger remote fallback.

The first Ollama startup reported creating its user-home identity file at
`~/.ollama/id_ed25519`. This file is outside the repository. Its contents were
not inspected, copied, or deleted. Treat it as sensitive local runtime material
and manage it through the credential lifecycle, not through Git or memory.
The source registry also explicitly excludes `models/**` from discovery.

Read-only state checks are:

```bash
ollama --version
brew services list | rg '^ollama\s'
```

`ollama list` requires a running local daemon. Do not start the daemon merely to
make that command succeed. The product-local manifest can be inspected without
a daemon at `models/ollama/manifests/registry.ollama.ai/library/llama3.1/8b`.

## Tracked approved local configuration

The complete field contract is in [the configuration reference](../../config/README.md).
The current `config/memory.toml` has these binding effects:

- `memory.enabled = true` exposes approved local capabilities without provider-on-load behavior;
- `memory.read_only = false` and `mutation_enabled = true` allow policy-controlled typed writes;
- `transport = "in_process"` and `network_listener_enabled = false` block a
  network listener;
- Cognee is pinned to `==1.5.3`, is not initialized on load, and may not expose
  a native client;
- provider access is local-only and cloud fallback is denied;
- exact retrieval uses SQLite/FTS5 plus canonical reread;
- semantic retrieval is configured for the approved local model pair, and
  needs provider activation plus current workflow verification before use;
- reviewer, retention, encrypted export, derived-profile, and explicit-feedback
  policy is resolved;
- shared mode, automatic feedback, provider-native export, and destructive
  execution remain disabled; and
- audit content is metadata-only with outbound telemetry disabled.

Loading this file may validate and fingerprint configuration. It must not
create `.sys4ai/memory/`, load Cognee, start Ollama, bind a socket, or contact a
remote endpoint.

## Configuration validation

Run the focused configuration and initialization tests without applying an
initialization:

```bash
uv run --frozen pytest -q tests/configuration tests/initialization
```

These tests use temporary directories. They check unknown-key rejection,
cross-field gates, confined non-symlink paths, deterministic preview digests,
and digest-bound apply behavior. They do not activate this checkout.

This product's reviewed activation route requires source discovery review and
a digest-bound initialization preview. Authorized consumer bootstrap also has
the direct `init-memory` route with the same internal preflight.
Do not edit the tracked profile to bypass the shared, network, cloud,
provider-native, or destructive gates. Record the approved decision identifiers,
configuration fingerprint, selected profiles, provider/model identifiers, path
review, and permission source in the governed activation record.

## Credential references, never values

The approved local direction requires no cloud or provider credential. If a
future profile requires one, tracked configuration may contain only a
non-secret reference such as an OS-keychain item name or a managed-secret
identifier. The value stays outside Git and is resolved at runtime only after
configuration, scope, and permission validation.

Do not put a credential value, reversible encoding, authorization header,
cookie, private key, recovery code, or credential-bearing connection string in
any of these locations:

- `config/memory.toml`, profiles, registries, schemas, documentation, or source
  files;
- shell command arguments, Tasks, plans, fixtures, logs, traces, receipts, or
  support bundles;
- memory records, provider databases, embeddings, graph properties, staging,
  exports, or backups.

Environment injection is temporary process exposure, not storage. It requires
an approved profile and documented risk. Rotation, revocation, and incident
steps are in [secret lifecycle](../security/secret-lifecycle.md) and
[incident response](../security/incident-response.md).

## Local and shared deployment

The current mode is an approved single-user in-process profile and is not a
secure shared configuration. In-process use still requires source, path,
secret, authority, permission, logging, and destructive-operation controls.

Do not start an HTTP or MCP listener from the current profile. The HTTP module
builds an ASGI application but deliberately does not call a server runner.
`LocalMemoryRuntime` composes the installed command-line service from canonical
project files, while `MemoryService` remains the provider-neutral dispatcher.
The installed local command does not start a network service.
Loopback no-auth mode is explicitly test-only. A shared deployment requires an
authenticated identity, canonical permission mapping, TLS, backend access
control, dataset isolation, centralized single-writer mutation, secret
lifecycle, and isolation/recovery evidence. See [deployment profiles](../security/deployment-profiles.md).
