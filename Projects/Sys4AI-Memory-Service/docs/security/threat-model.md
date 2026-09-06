# Threat model and binding controls

Threat-model version: 1.0  
Status: Stage 0 control contract; focused fake/temp enforcement tests exist,
but real-provider, network, shared, production-export, and end-to-end evidence
is incomplete

## Scope and assets

This model covers source discovery, ingestion, provider mapping, retrieval, writes, control records, logs, rebuilds, deletion, exports, and local/shared interfaces. Protected assets include canonical sources, control state, permissions, credentials, restricted content, project isolation, provenance, current decisions, and the integrity of derived indexes.

Primary trust boundaries are the project root, registered external sources, client/service interface, Sys4AI/provider adapter, local generated-data root, model endpoint, control-record path, and any future shared-service tenant boundary.

## Required threats

| ID | PRD threat | Required prevention/detection | Binding controls | Current safe gate |
|---|---|---|---|---|
| `T-01` | Prompt injection contained in imported sources | Label imported content as data, isolate authority retrieval, preserve source provenance, and reread canonical instructions. | `C-01`, `C-02`, `C-03`, `C-13`, `C-14` | External sources are not registered by default. |
| `T-02` | Persistent memory poisoning | Bind trust/authority at write time, validate typed writes, stage promotion, preserve provenance, and detect contradiction/supersession. | `C-01` to `C-05`, `C-13`, `C-14` | Mutation is disabled in the Stage 0 configuration. |
| `T-03` | Unauthorized durable writes | Validate schemas and canonical permissions for every mutation; keep general agents read/propose only. | `C-04`, `C-05`, `C-11` | One human `local-owner` review is approved; canonical reread and no-self-approval remain mandatory, and destructive grants are absent. |
| `T-04` | Governance laundering, where untrusted content is summarized and later treated as trusted | Keep original authority, trust, and derivation on summaries and block authority inheritance. | `C-01`, `C-02`, `C-03`, `C-13`, `C-14` | `allow_authority_inheritance = false`. |
| `T-05` | Cross-project or cross-tenant data leakage | Resolve explicit project scope, check permissions, isolate datasets, and reject paths outside the allowed root. | `C-05`, `C-06`, `C-07` | Single-project and two-project deny behavior is fake/temp verified; shared deployment remains disabled. |
| `T-06` | Secret and credential ingestion | Exclude known secret paths, scan discovery/writes, prohibit secret values, minimize logs, and erase all copies after an incident. | `C-07`, `C-08`, `C-09`, `C-15` | Default-deny source discovery plus explicit secret exclusions. |
| `T-07` | Path traversal or arbitrary local file ingestion | Resolve paths under a trusted root, reject absolute/escaping/symlink paths, and ignore provider-native client paths. | `C-07`, `C-08` | Arbitrary local paths are disabled. |
| `T-08` | Malformed file attacks | Validate format/schema, enforce parser size/resource limits, isolate parser failures, and never activate partial output. | `C-04`, `C-07`, `C-08` | Registered adapters enforce size, nesting, encoding, and format limits in focused tests; live provider activation remains blocked. |
| `T-09` | Overbroad MCP tools | Publish read/propose operations separately from privileged destructive/admin operations and check canonical permissions. | `C-05`, `C-11` | Mutation and network listener are disabled. |
| `T-10` | Destructive forget or rebuild operations | Require scoped preview, authorization, generation safety, and non-sensitive receipts. | `C-05`, `C-10`, `C-15` | All destructive operations are privileged and disabled. |
| `T-11` | Supply-chain and provider-version changes | Pin versions, review advisories/licenses, run compatibility/migration checks, and retain rollback inputs. | `C-12` | Cognee is pinned to 1.5.3; no provider upgrade has completed the documented compatibility and migration procedure. |
| `T-12` | Stale or superseded knowledge presented as current | Filter by lifecycle/source revision, preserve supersession, and reread execution-critical canonical state. | `C-02`, `C-14` | Current-only is required unless history is explicit. |
| `T-13` | Model-extracted false relations | Mark model extraction, require provenance/confidence/validation, and prevent relation-based authority elevation. | `C-02`, `C-03`, `C-04`, `C-13` | Base relation meanings are registered with `implementation_status=not-implemented`; validation and ranking tests use fixture or in-memory relations, and no real provider graph is accepted. |
| `T-14` | Retrieval logs leaking sensitive content | Use structured metadata-only logs, redact before serialization, restrict access, and apply privacy erasure. | `C-09`, `C-15` | Telemetry is off; content logging is metadata-only. |
| `T-15` | Export packages leaking restricted material | Apply permission, classification, scanning, manifest, encryption, and deletion rules before package creation. | `C-05`, `C-08`, `C-09`, `C-15` | Export is disabled until format/encryption policy is approved. |

## Fifteen binding controls

| ID | PRD control | Required implementation behavior | Minimum evidence before release |
|---|---|---|---|
| `C-01` | Authority isolation | Governance retrieval uses a separate namespace/filter from evidence retrieval. | Injection and laundering tests show external/generated records cannot enter the governance result set. |
| `C-02` | Write-time provenance | Bind source, derivation, trust, authority, status, scope, actor/process, and timestamps at creation. | Valid/invalid schema fixtures plus immutable provenance checks. |
| `C-03` | No authority inheritance through summaries | Derived summaries retain their own lower authority and a `DERIVED_FROM` link. | A laundering fixture stays non-authoritative after summarization/re-ingestion. |
| `C-04` | Schema validation | Validate control records and proposals before use; reject malformed/unknown-major inputs. | Representative valid and invalid fixtures for each public schema. |
| `C-05` | Permission envelope | Resolve and validate current canonical permission for every operation. | General-agent denial and administrator-scoped allow/deny cases. |
| `C-06` | Dataset isolation | Shared profiles use authentication and supported isolated storage boundaries. | Two-project and two-tenant read/write isolation tests before shared release. |
| `C-07` | Safe local paths | Accept only registered, normalized, allowed-root paths; reject arbitrary client paths. | Traversal, absolute path, symlink escape, and out-of-root tests. |
| `C-08` | Secret scanning | Scan discovery, writes, imports, and exports; reject or quarantine without logging values. | Known secret fixtures are excluded/rejected with redacted results. |
| `C-09` | Sensitive logging controls | Use allowlisted structured metadata and hashes where safe; omit raw content by default. | Log-capture tests contain no fixture secret or restricted content. |
| `C-10` | Dry-run destructive actions | Preview exact scope and impact before deletion, mass forget, import replacement, or rebuild activation. | Preview is non-mutating; execution requires matching current scope and authorization. |
| `C-11` | Read-only agent mode | Expose read/propose separately; omit privileged tools for general agents. | MCP/tool inventory and authorization tests. |
| `C-12` | Provider hardening | Pin provider/dependencies and review advisories, compatibility, migrations, and rollback. | Lock evidence, version check, provider smoke suite, and upgrade receipt. |
| `C-13` | External-source labeling | Imported content remains data and preserves external trust/authority labels. | Imported instruction fixture cannot alter policy or gain governance status. |
| `C-14` | Canonical revalidation | Reread current canonical permission/control sources before execution-critical action. | Stale indexed permission/decision fixtures are rejected after source change. |
| `C-15` | Deletion semantics | Erase content from all relevant active/derived/export copies while receipts retain identifiers/hashes only when safe. | Privacy-erasure coverage with no prohibited content in receipt or rebuild inputs. |

## Acceptance and residual risk

No Stage 0 document alone is enforcement evidence. Current focused tests provide
contract, fake-provider, ASGI, or temporary-path evidence for many controls;
the [release evidence ledger](../verification/README.md) remains the acceptance
record. A bounded real Cognee semantic path, approved model pair, encrypted
export, and TTL policy now have direct evidence. Full-scale Cognee recovery, a
live authenticated network service, shared isolation, and a concrete durable
persistence adapter remain unavailable or unverified; automatic feedback is
deliberately prohibited. Local-only execution reduces network exposure but does not remove poisoning, secret
ingestion, path, parser, local-user, or supply-chain risk.

Related contracts:

- [Secret lifecycle](secret-lifecycle.md)
- [Logging and redaction](logging-and-redaction.md)
- [Safe paths and destructive operations](safe-paths-and-destructive-operations.md)
- [Deployment profiles](deployment-profiles.md)
- [Control-record boundary](../../control_records/memory/README.md)
