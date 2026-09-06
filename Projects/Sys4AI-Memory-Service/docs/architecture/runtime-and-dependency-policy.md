# Runtime and dependency policy

Status: approved Stage 0 policy  
Policy version: 1.0  
Decision date: 2026-09-03

This policy freezes the initial runtime and dependency-management boundary for the Sys4AI Memory Service. It does not install dependencies or assert that a lockfile has been resolved on every supported platform.

## Approved baseline

| Concern | Policy |
|---|---|
| Python | Support Python 3.12 for the first release line. Keep `.python-version`, project metadata, CI, and operator documentation aligned. |
| Dependency manager | Use `uv` for resolution, locking, environment creation, and project commands. |
| Project metadata | Declare direct dependencies and supported Python in `pyproject.toml`. |
| Lock | Commit a complete `uv.lock` produced from the approved metadata. Install and test from the lock rather than an unbounded resolver result. |
| Semantic provider | Pin the first provider to `cognee==1.5.3`; do not use `latest` or a floating compatible range for runtime installation. |
| Provider boundary | Import Cognee only inside the provider adapter. Agent-facing code uses Sys4AI interfaces and schemas. |
| Default model posture | No cloud key. Use local Ollama `llama3.1:8b` and FastEmbed `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions; deny remote and cloud fallback. |
| Optional dependencies | Put non-core adapters and deployment integrations in explicit extras. Do not install cloud, scraping, or shared-backend extras by default. |

The Cognee 1.5.3 tagged metadata declares Python `>=3.10,<3.15` and Apache-2.0. Python 3.12 is inside that declared range. The tagged license file is Apache License 2.0. These upstream facts were inspected at:

- <https://raw.githubusercontent.com/topoteretes/cognee/v1.5.3/pyproject.toml>
- <https://raw.githubusercontent.com/topoteretes/cognee/v1.5.3/LICENSE>

This is a dependency-policy finding, not legal advice. Distribution must preserve applicable license and notice obligations for the locked dependency set.

## Lock and provenance rules

1. Resolve on an approved Python 3.12 interpreter.
2. Keep exact direct-provider pins in project metadata and the full transitive solution in `uv.lock`.
3. Record the Python version, target platform, lock digest, direct dependency versions, and provider adapter version in generation and validation receipts.
4. Do not hand-edit resolved versions in the lockfile.
5. Treat a lock refresh as a dependency change even when direct versions do not change.
6. Keep build, test, and runtime extras distinct. Production paths must not depend on test-only packages.
7. A dependency's presence in the lock does not authorize its network services, telemetry, credentials, or optional integrations.

## Upgrade gate

A Cognee or other security-relevant dependency upgrade requires all of the following before acceptance:

1. Review the tagged release notes, package metadata, license files, transitive dependency changes, and relevant security advisories.
2. Resolve a candidate lock on every supported platform profile that release evidence claims.
3. Run the provider contract smoke suite for capability discovery, remember, recall, improve-policy rejection, forget-policy rejection, health, and normalized errors.
4. Run storage migration checks against a copy of representative derived data. Never test an upgrade first against the only working provider database.
5. Run project isolation, exact-source preservation, source provenance, and no-cloud-key startup checks.
6. Verify that agent-facing schemas and call shapes did not change. A breaking change requires a public-contract migration rather than an adapter leak.
7. Record the decision, lock digest, checks, warnings, and rollback point in a reviewable receipt.

## Rollback policy

Canonical sources, registries, schemas, configuration, and provider-neutral exports are the recovery basis. Provider databases are not.

- Keep the last accepted lockfile and adapter version available through normal version history.
- Before a provider migration, create a provider-neutral export when export is authorized and its encryption policy has been approved. Until then, rely on canonical rebuild inputs, not an unapproved export.
- Build a new generation beside the active generation. Activate only after compatibility and integrity checks pass.
- If the candidate fails, retain the last valid generation, restore the accepted lock and adapter, and record the failed candidate without sensitive content.
- Never downgrade canonical schemas or silently reinterpret existing records to make a provider rollback succeed.

## Approved and deferred dependency decisions

The local model pair, SQLite/FTS5 exact backend, authenticated-network-only
posture, and `age` X25519 package envelope are approved in the
[decision register](../decisions/decision-register.md). No shared graph/vector
backend is approved for this release, so shared mode stays disabled. Product
Git, publication, deployment, model redistribution, and non-fixture destructive
execution remain outside this policy.
