# Deployment profile rules

Status: local profile approved; shared and credentialed profiles disabled

Evidence boundary: deployment posture, project/dataset mapping, loopback test
mode, and fail-closed shared gates are implemented and exercised with temporary
or ASGI test contexts. No live memory-service listener or shared backend has
been deployed.

## Local embedded no-cloud-key profile

`local-embedded-no-cloud-key@1` is the first approved deployment profile. Its
tracked configuration exposes local capabilities only after explicit provider
initialization and never binds a memory-service listener on load.

- Run one local service process for all clients that may touch embedded stores.
- Use Cognee 1.5.3 only through the Sys4AI adapter.
- Keep canonical sources in the project and derived data under `.sys4ai/memory/`.
- Do not bind a network listener. Any future network exposure requires authentication.
- Permit only the explicit loopback Ollama dependency; deny remote models and cloud fallback.
- Use the approved local LLM/embedding pair after explicit provider initialization.
- Use SQLite exact tables plus FTS5 and canonical reread.
- Permit typed mutations under current canonical permission and review policy while keeping destructive execution disabled.
- Do not let clients open SQLite, vector, graph, or provider files directly.

Local-only does not mean trusted input. Source, path, secret, authority, permission, logging, and destructive-operation controls still apply.

Ollama 0.33.2 and the ignored product-local `llama3.1:8b` Q4_K_M model are
paired with the ignored FastEmbed MiniLM cache. Offline embedding and a bounded
real Cognee semantic/metadata round trip passed. Model artifacts still do not
initialize this deployment profile. See
[the local-model evidence spike](../verification/MEM-OQ-004-local-model-spike.md).

## Future authenticated network profile

A loopback or non-loopback HTTP/MCP listener requires an authenticated profile
that defines process/user boundary, listener address, credentials, origin/client
restrictions, and operator warnings. The approved local profile does not supply
that deployment bootstrap and cannot be reclassified as no-auth network mode.

## Future shared profile

Shared deployment is disabled. It requires, at minimum:

- authenticated client identity and canonical role/permission mapping;
- supported dataset or tenant isolation for relational, vector, graph, cache, and logs;
- a single centralized write path with concurrency and idempotency controls;
- TLS and approved secret lifecycle;
- approved graph/vector backends and their license, capacity, backup, restore, migration, and access-control evidence;
- cross-project deny tests and incident/audit procedures; and
- no change to agent-facing Sys4AI contracts.

An embedded backend that lacks the required isolation cannot be reclassified as shared by configuration alone.

The local multi-agent acceptance fixture exercises the service-level contract
without enabling this profile: two separately authorized principals recall the
same project-scoped evidence through one `MemoryService`, concurrent proposals
enter the single mutation lock one at a time, and a foreign project/dataset
request is denied before provider access. This proves the `UC-11` service
behavior, but it does not establish backend authentication, a shared datastore,
TLS, listener deployment, or production multi-user readiness.

The HTTP adapter requires an authenticator unless a caller explicitly selects
the test-only loopback no-auth posture. That test posture rejects non-loopback
clients and is prohibited in shared mode. The adapter constructs an ASGI
application only; it does not bind or run a listener.

## Future credentialed or remote-model profile

No such profile is approved. It requires an explicit provider/model decision, data-class rules, endpoint and region, least-privilege credential reference, egress/telemetry policy, retention terms, failure/fallback behavior, redaction tests, and revocation procedure. It cannot silently replace the no-cloud-key profile when a local model is missing.

## Deliberately disabled capabilities

The [decision register](../decisions/decision-register.md) approves bounded
retention, encrypted export, and the software-engineering proof profile. It
deliberately selects no shared production backend and no automatic feedback.
Product deployment and non-fixture destructive execution remain unapproved.
