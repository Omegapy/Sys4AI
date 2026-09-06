# Sys4AI Memory Service

Sys4AI Memory Service provides project memory for Sys4AI agents.

Public source repository:
[Omegapy/Sys4AI-Memory-Service](https://github.com/Omegapy/Sys4AI-Memory-Service).

For project specifications, see [SPECS.md](./SPECS.md).

## Current status

Installation and capability configuration do not establish readiness in a
particular project. New consumers default to exact/keyword memory with semantic
memory disabled and Cognee activation deferred. This development checkout's
semantic-enabled configuration and bounded tests do not prove an initialized
live project. Agents and humans should use
[memory readiness and activation](docs/operations/memory-readiness-and-activation.md)
to check the actual state, receive an explicit handoff and choose whether to
activate semantic memory. Existing decisions remain in force.

This checkout implements the versioned contracts and core modules described by
parent plan `PLAN-20260903-2DA243C0`. It is not a production deployment.

| State | Current evidence boundary |
|---|---|
| Contract implemented | Schemas, registries, configuration, adapters, exact index, provider boundary, retrieval, bounded graph paths, opt-in cited synthesis, write/lifecycle policy, rebuild, exchange, observability, interfaces, and the unified `MemoryService` dispatcher exist in this checkout. |
| Integrated behavior verified | Provider, profile, policy, lifecycle, promotion, rebuild, exchange, security, administrative control-plane, and interface tests use confined fixtures. The approved `software-engineering@1` extension syncs typed Python AST records and serves two agents through the unchanged public API. The public export path creates and validates an `age`-encrypted provider-neutral package containing restricted fixture data without writing the plaintext ZIP to disk. |
| Benchmark measured | The SQLite/FTS5 exact-index candidate met the exact lookup target on a synthetic 100,000-fragment corpus. The maintained local-runtime run measured guarded hybrid recall, service-shell startup, one-source sync, 100,000 fragments, and 100,000 in-memory relations. A supplemental stress run loaded 1,000,000 relations and completed one endpoint-indexed hybrid recall in 1,354.589 ms using 5,618.219 MB peak resident memory. A separate real Cognee run proves the small-corpus profile path; complete-profile scale/startup/sync requirements remain unverified. See [the exact-index spike](docs/verification/MEM-OQ-005-exact-index-spike.md) and [the local-runtime benchmark](docs/verification/local-runtime-benchmark.md). |
| Real Cognee bounded run verified | Cognee 1.5.3 created project-confined relational and graph representations, remembered two typed records and one relation, and returned a public record through a stable metadata rejoin. Populated-dataset rebuild, native COGX migration, sustained load, and production recovery remain separate evidence gaps. |
| Local model checks recorded | Bounded model, cache, and semantic checks are recorded in [the local-model evidence spike](docs/verification/MEM-OQ-004-local-model-spike.md). |
| Network disabled | The tracked profile uses in-process transport and does not bind a listener. `MemoryService` has no deployment bootstrap, and the HTTP adapter constructs an application but never starts a server. |
| Source repository | This product has its own Git repository and public origin at `Omegapy/Sys4AI-Memory-Service`. Source installation is supported by `pyproject.toml`; package-index releases, GitHub Pages and a hosted service are separate from source publication. |

A module, passing unit test, installed dependency, or benchmark does not grant
authority for further action.

## Install the Python package

The package requires Python 3.12. Clone the source, create a local environment
and install the core package:

```bash
git clone https://github.com/Omegapy/Sys4AI-Memory-Service.git
cd Sys4AI-Memory-Service
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/sys4ai-memory --help
```

With `uv`, the equivalent environment and installation steps are
`uv venv --python 3.12` and `uv pip install .`.

For a consuming project, install into that project's own environment and pin
the dependency to a tested full Git commit. Pip supports the requirement form
`sys4ai-memory-service @ git+https://github.com/Omegapy/Sys4AI-Memory-Service.git@COMMIT_SHA`,
with `COMMIT_SHA` replaced by the actual revision. Keep the project's resolved
dependencies in its own lockfile when reproducible installation is required.
The package imports as `sys4ai_memory` and provides the `sys4ai-memory` command.

Installation supplies the software. Each consumer still needs its own
configuration, permissions, source registration and memory initialization;
follow [installation and configuration](docs/operations/installation-and-configuration.md)
and [memory readiness](docs/operations/memory-readiness-and-activation.md).
The core installation does not activate Cognee or download models. The Sys4AI
template's portable clone bootstrap remains separate work.

## Install the locked environment

From the product root:

```bash
uv sync --locked --extra dev --extra cognee
uv run --frozen python --version
uv run --frozen python -c 'import importlib.metadata as m; print(m.version("cognee"))'
```

The version commands report the selected runtime and installed provider.
`--locked` prevents dependency resolution from changing `uv.lock`;
`--frozen` prevents a run command from changing it.

Installation alone does not start Ollama, initialize Cognee, or bind a network
listener. Model-cache fill and provider initialization remain explicit operator
actions documented in [installation and configuration](docs/operations/installation-and-configuration.md).

## Safe first checks

These commands read tracked files and run local tests. They do not initialize a
provider, start a listener, download a model, or create canonical records.

```bash
uv run --frozen pytest -q tests/configuration tests/contracts tests/profiles
uv run --frozen pytest -q tests/ingestion tests/exact_index
uv run --frozen python tools/validate_release_evidence.py
```

For initialization preview and apply, follow
[installation and configuration](docs/operations/installation-and-configuration.md).

## Documentation

- [Operations guide](docs/operations/README.md)
- [Installation and configuration](docs/operations/installation-and-configuration.md)
- [Memory readiness and activation](docs/operations/memory-readiness-and-activation.md)
- [Source and profile registration](docs/operations/source-and-profile-registration.md)
- [Operator workflows](docs/operations/operator-workflows.md)
- [Backup and recovery](docs/operations/backup-and-recovery.md)
- [Observability and troubleshooting](docs/operations/observability-and-troubleshooting.md)
- [Developer guide](docs/operations/developer-guide.md)
- [Dependency upgrades](docs/operations/dependency-upgrades.md)
- [Deployment profiles](docs/security/deployment-profiles.md)
- [Security incident response](docs/security/incident-response.md)
- [Configuration contract](config/README.md)
- [Release evidence rules](docs/verification/README.md)

Project direction is defined in [ROLE.md](ROLE.md). Reusable bounded roles live
under [sub-agent-roles](sub-agent-roles), and the Project Director must use the
local [role-management skill](.agents/skills/manage-subagent-roles/SKILL.md)
before selecting a role-based child.
