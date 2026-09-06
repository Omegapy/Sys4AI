# Memory configuration contract

Contract version: 1.0  
Default file: `config/memory.toml`

The tracked configuration declares provider-neutral Sys4AI behavior. Provider-specific keys remain under the provider section and must be translated by the adapter. They do not become public agent fields.

The committed configuration selects the approved local embedded, no-cloud-key
profile. Exact, semantic, typed-write, bounded-retention, and encrypted-package
policy is resolved, but loading remains side-effect free because provider
initialization is a separate explicit operation. The memory-service network
listener, shared backend, provider-native export, cloud fallback, and
non-fixture destructive execution remain disabled.

Configuration parsing, strict unknown-key rejection, path confinement,
cross-field invariants, capability gates, deterministic fingerprinting, and
initialization preview/apply boundaries are implemented and focused-test
verified. The tests use temporary directories. They do not activate this
checkout or initialize Cognee.

For installation handoff and current project state, use
[memory readiness and activation](../docs/operations/memory-readiness-and-activation.md).
New consumers default to `semantic_enabled = false`; this product configuration
selects semantic capabilities. Neither setting proves backend or model
readiness. Report the actual state to the human and next agent and ask whether
to activate only when their decision is not already settled.

## Loading and validation

1. Locate the project root from an explicit operator path or a trusted service context. Do not infer it from an arbitrary client path.
2. Load `config/memory.toml` as UTF-8 TOML and reject duplicate or unknown keys when `strict_config = true`.
3. Validate types, enumerated values, version compatibility, path rules, and cross-field invariants before loading a provider.
4. Resolve tracked relative paths against `memory.project_root`; resolve symlinks and confirm the result remains inside the allowed root.
5. Load registries and public schemas before source discovery.
6. Run exclusion, secret-scan, and discovery dry-run checks before creating `.sys4ai/memory/` or initializing Cognee.
7. Require an explicit activation action. Loading configuration alone must not create storage, bind a socket, download a model, contact a remote host, or run ingestion.

The service must fail closed when configuration is missing, malformed or
unsupported, or a setting required for the requested capability is unresolved.
Pending semantic profiles do not block the prepared exact-only capability. It
must not substitute a provider or library default that could contact a remote
service.

## Field semantics

### File and base memory fields

| Field | Meaning and validation |
|---|---|
| `config_version` | Version of this TOML contract. Reject unsupported major versions. |
| `configuration_status` | Human-readable lifecycle state. The tracked value records an approved local profile whose provider is not initialized by configuration load. |
| `memory.enabled` | Master capability flag. It does not initialize a provider or bind a listener. |
| `memory.api_version` | Required public API major/minor contract. It must be compatible with installed schemas. |
| `memory.project_id` | Stable project identifier used for scope and dataset mapping. It is not a display name. |
| `memory.project_root` | Trusted root for relative-path resolution. The default is the directory above `config/`. |
| `memory.default_memory_profile` | Exact registered profile identifier. It must resolve to one active compatible row. |
| `memory.deployment_profile` | Selected deployment posture. It is separate from a memory extension profile. |
| `memory.local_data_dir` | Derived-data root. It must be inside the project root and excluded from version control and ingestion. |
| `memory.read_only` | Blocks all mutation operations when true, including proposal persistence. |
| `memory.strict_config` | Requires unknown-key rejection and strict type/enumeration validation. |

### Service and provider fields

| Field | Meaning and validation |
|---|---|
| `memory.service.transport` | `in_process` means no HTTP/MCP socket is implied. A network transport requires a separate approved posture. |
| `memory.service.network_listener_enabled` | Controls socket binding. `false` is binding even when a host is present. |
| `memory.service.bind_host` | Allowed listener address if a future profile enables one. A non-loopback address requires shared-profile approval. |
| `memory.service.authentication_posture` | Any future network exposure is authenticated-only; the tracked local service uses no listener. |
| `memory.service.single_writer` | Requires all embedded-store writes to flow through one service process. |
| `memory.provider.name` | Adapter-selected provider. Clients cannot use this value to bypass Sys4AI contracts. |
| `memory.provider.version_constraint` | Exact supported provider version. The runtime must compare the installed version before initialization. |
| `memory.provider.mode` | Provider operating mode. `standalone` does not authorize provider API or cloud mode. |
| `memory.provider.initialize_on_load` | When false, parsing configuration cannot initialize provider storage. |
| `memory.provider.allow_native_client_access` | When false, public clients cannot receive native provider handles or storage paths. |
| `memory.provider.outbound_network` | `local-only` permits the explicit loopback Ollama dependency and denies remote/model fallback. |
| `memory.provider.cognee.dataset` | Stable local dataset mapping for this project. It does not authorize cross-project access. |
| `memory.provider.cognee.backend_access_control_posture` | Backend access control is disabled only for the in-process single-user profile; it is not a network no-auth approval. |
| `memory.provider.cognee.accept_local_file_path` | Rejects provider-level arbitrary client file paths when false. Sources enter through the Sys4AI registry/scanner. |

### Retrieval and model fields

| Field | Meaning and validation |
|---|---|
| `memory.exact_index.enabled` | Enables the approved deterministic exact/lexical backend. |
| `memory.exact_index.provider` | SQLite exact tables plus FTS5, canonical reread, and operator `rg` diagnostic fallback. |
| `memory.exact_index.path` | Derived index path inside `memory.local_data_dir`. |
| `memory.models.semantic_enabled` | Enables semantic/model operations only when both model profiles are selected and locally available. |
| `memory.models.llm_profile` | Approved local Ollama `llama3.1:8b` profile ID. |
| `memory.models.embedding_profile` | Approved FastEmbed `sentence-transformers/all-MiniLM-L6-v2` profile ID at 384 dimensions. |
| `memory.models.model_cache_dir` | Rebuildable model caches below `memory.local_data_dir`, normally `.sys4ai/memory/models`. |
| `memory.models.allow_remote` | Permits a remote model endpoint only in an approved profile. |
| `memory.models.allow_cloud_fallback` | When false, missing local capability fails rather than selecting a cloud default. |
| `memory.models.profiles` | Optional typed catalog of local or remote LLM and embedding profiles. Each entry binds a profile ID, capability, locality, provider, model, endpoint where applicable, embedding dimensions, and a credential reference rather than a secret value. |

Local catalog entries reject credential references and non-loopback endpoints.
Remote catalog entries require HTTPS and a reference using the
`environment:`, `keychain:`, or `managed-secret:` scheme; embedded URL
credentials are rejected. Catalog presence alone does not approve a profile,
enable semantic behavior, resolve a credential, or change the public memory
API. The tracked configuration declares only the approved local LLM and
embedding entries; neither entry starts or downloads a model during load.

The ignored product-local model caches completed bounded LLM, offline embedding,
and real Cognee semantic/metadata-round-trip checks. Cache presence is still
not provider-initialization authority. See
[the local-model evidence spike](../docs/verification/MEM-OQ-004-local-model-spike.md).

### Registry, source, and control fields

| Field | Meaning and validation |
|---|---|
| `memory.registries.sources` | Canonical source-registry path. |
| `memory.registries.profiles` | Canonical memory-profile registry path. |
| `memory.registries.relations` | Canonical relation registry path. |
| `memory.sources.respect_gitignore` | Adds applicable Git ignore rules to, but never weakens, registry exclusions. |
| `memory.sources.default_include` | When false, unmatched paths are excluded. |
| `memory.sources.require_registered_rule` | Requires an explicit registry rule for every durable source. |
| `memory.sources.require_discovery_dry_run` | Requires a reviewed discovery result before ingestion or storage initialization. |
| `memory.control_records.root` | Canonical root for schema-valid memory proposals, approvals, receipts, migrations, and incidents. |
| `memory.control_records.approval_policy_status` | Approved local single-review policy ID. |
| `memory.control_records.reviewer_principal_id` | Canonical human reviewer identity, `local-owner`. |
| `memory.control_records.approvals_required` | Exactly one approval. |
| `memory.control_records.self_approval_allowed` | Must remain false. |
| `memory.control_records.deny_unresolved_approval` | Makes a missing or unresolved reviewer rule a denial. |

### Permission and security fields

| Field | Meaning and validation |
|---|---|
| `memory.permissions.general_operations` | Maximum default operation names for a general agent. The current master/read-only gates still apply. |
| `memory.permissions.privileged_operations` | Operation names that require a canonical permission check and action-specific authorization. |
| `memory.permissions.mutation_enabled` | Global mutation gate. `false` blocks proposal and destructive mutation. |
| `memory.permissions.require_canonical_permission` | Requires current validated permission records; semantic memory cannot authorize an operation. |
| `memory.security.secret_scan` | Requires configured secret detection during discovery and writes. |
| `memory.security.external_content_is_authority` | Must remain false under the approved architecture. |
| `memory.security.allow_authority_inheritance` | Must remain false; summaries and relations do not raise authority. |
| `memory.security.safe_path_mode` | `project-allowlist` permits only registered paths that resolve inside an allowed project root. |
| `memory.security.allow_arbitrary_local_paths` | Must remain false for server-facing client requests. |
| `memory.security.require_dry_run_for_destructive` | Requires a non-mutating plan before any destructive request. |
| `memory.security.require_impact_preview` | Requires counts, scope, affected identifiers/hashes, and warnings before authorization. |
| `memory.security.destructive_execution_enabled` | Independent execution gate; false keeps non-fixture destructive operations unavailable. |

### Policy and deliberately disabled profile fields

| Field | Meaning and validation |
|---|---|
| `memory.retention.policy_status` | Approved 72-hour session and 365-day episodic policy. |
| `memory.retention.session_ttl_hours` | Maximum session lifetime: 72 hours. |
| `memory.retention.episodic_ttl_days` | Maximum episodic lifetime: 365 days. |
| `memory.retention.session_persistence` | Allows a supplied persistence port only with TTL enforcement and expiry purge. |
| `memory.retention.episodic_persistence` | Allows a supplied persistence port only with TTL enforcement and expiry purge. |
| `memory.export.enabled` | Master provider-neutral export gate. |
| `memory.export.format_status` | Approved provider-neutral ZIP JSON/JSONL contract. |
| `memory.export.container` | Deterministic `zip` inner container. |
| `memory.export.encryption_required` | Requires the approved encryption policy before a package containing non-public content can be produced. |
| `memory.export.encryption` | `age-x25519`. |
| `memory.export.recipient_reference_required` | Requires an explicit public age recipient; no private identity is stored here. |
| `memory.export.provider_native_export_enabled` | Separate gate for supplementary COGX/provider export. |
| `memory.shared.enabled` | Shared-service deployment gate. |
| `memory.shared.backend_status` | Records that no production shared backend is approved for this release. |
| `memory.shared.authentication_required` | Binding shared-profile requirement. |
| `memory.shared.dataset_isolation_required` | Binding shared-profile requirement. |
| `memory.feedback.automatic_collection` | Must remain false under the approved policy. |
| `memory.feedback.explicit_typed_only` | Requires actor-, evidence-, scope-, authority-, sensitivity-, and retention-aware feedback records. |
| `memory.feedback.policy_status` | Approved explicit-typed-only policy. |
| `memory.observability.local_audit_log` | Derived local structured audit-log path. It is not a canonical approval record. |
| `memory.observability.content_logging` | `metadata_only` permits identifiers, classes, hashes, outcomes, and timings, not raw source/query/result content. |
| `memory.observability.telemetry_export` | Outbound telemetry gate. It stays false in the approved local profile. |

## Cross-field invariants

- `memory.enabled = false` overrides every lower capability flag; the tracked local profile is enabled without provider-on-load behavior.
- `memory.read_only = true` or `memory.permissions.mutation_enabled = false` rejects every mutating operation.
- A network listener requires a non-pending authentication posture. Non-loopback binding also requires an approved shared profile.
- Semantic operation requires non-pending local model profiles. `allow_remote = false` and `allow_cloud_fallback = false` prohibit remote substitution.
- Exact retrieval requires a non-pending exact-index provider.
- Approval or promotion requires a non-pending canonical approval policy and a current permission record.
- Durable session or episodic storage requires an approved retention policy.
- Export requires an approved format/encryption policy; shared deployment requires approved backends and access-control evidence.
- Automatic feedback is prohibited by the approved explicit-typed-only policy.
- `destructive_execution_enabled = false` blocks forget execution even when mutation support is otherwise enabled.
- Provider initialization requires an accepted version, safe derived path, source exclusions, secret scan, and discovery dry run.

## Credential references and overrides

The committed configuration contains no credential value or credential reference because the first profile requires none. A later credentialed profile may refer to an operating-system keychain item or managed-secret name from an operator-owned configuration outside version control. The service resolves that reference at runtime and passes the value only to the narrow provider process that needs it.

Do not place a password, token, API key, cookie, private key, recovery code, connection string containing a secret, or their encoded/encrypted copies in this file, a CLI argument, Task record, fixture, log, receipt, export manifest, or derived memory. Environment variables may carry an injected value only when process exposure is accepted and documented; they are not a persistence mechanism.

## Activation checklist

An operator still must run source/path/exclusion review. Reviewed initialization
requires an accepted preview; an authorized consumer bootstrap may use direct
`init-memory` with the same internal preflight. Enabling a
network listener, shared backend, provider-native exchange, cloud fallback, or
destructive execution requires a separate approved profile and evidence. Record
only the sanitized configuration fingerprint and decision identifiers; never
record resolved secret material.

Changing semantic/model settings changes the configuration fingerprint. An
existing initialization or sync receipt then becomes incompatible. The current
installed runtime has no general command to migrate an initialized exact-only
consumer to this changed configuration. Preserve the live working settings
while preparing the approved migration path; do not edit/delete receipts or
assume that changing the boolean and rerunning initialization completes it.

See also:

- [Decision register](../docs/decisions/decision-register.md)
- [Deployment profiles](../docs/security/deployment-profiles.md)
- [Secret lifecycle](../docs/security/secret-lifecycle.md)
- [Safe paths and destructive operations](../docs/security/safe-paths-and-destructive-operations.md)
- [Installation and configuration](../docs/operations/installation-and-configuration.md)
- [Operator workflows](../docs/operations/operator-workflows.md)

Read-only validation from the product root:

```bash
uv run --frozen pytest -q tests/configuration tests/initialization
```

The installed local CLI uses `LocalMemoryRuntime` to construct `MemoryService`
from canonical project files. Operations requiring initialized storage still
return `MEMORY_NOT_INITIALIZED` for absent or mismatched initialization state;
that is not a reason to bypass the configuration guards. Provider dependencies
are activated only by operations that require them. See the interface boundary
in the
[operator workflows](../docs/operations/operator-workflows.md).
