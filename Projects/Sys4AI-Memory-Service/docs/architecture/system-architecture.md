# System architecture and base contract

Status: accepted architecture contract  
Architecture version: 1.0  
Provider implementation status: not verified

This document maps PRD Sections 10 through 16 and 22 through 26 into the independent product root. The [ADR](../decisions/ADR-0001-memory-service-architecture.md) records why this architecture was selected. Public JSON schemas remain the machine-readable contract; this document defines responsibility and invariants.

## System context

```text
canonical project sources            registered external evidence
            |                                      |
            +---------- source registry -----------+
                               |
                    safe discovery and scanning
                               |
                       typed normalization
                               |
        +----------------------+----------------------+
        |                      |                      |
  exact/lexical         provider adapter       provenance ledger
  deterministic        Cognee 1.5.3 first       source revisions,
  retrieval            replaceable later       hashes, receipts
        |                      |                      |
        +----------------------+----------------------+
                               |
                    Sys4AI policy and ranking
          scope, permission, trust, lifecycle, evidence
                               |
              Python | HTTP | MCP | sys4ai-memory CLI
                               |
                       agents and operators
                               |
                     typed write proposals
                               |
                   governed canonical changes
```

The service is the only supported route to embedded provider files when concurrent access is possible. Public clients never depend on Cognee native objects, stores, or MCP methods.

## Information boundaries

| Category | Authority | Service treatment |
|---|---|---|
| Governance | Highest within its valid project scope | Index in an isolated authority namespace. Never create it from external retrieval or generated summaries. |
| Deterministic runtime state | Canonical for execution | Index for discovery only. Reread and validate the source before action. |
| Canonical project knowledge | Authoritative within its registered role | Preserve exact content and provenance; semantic representations remain derived. |
| Registered external evidence | Evidence only by default | Keep a distinct trust class and namespace; treat embedded instructions as data. |
| Agent-generated durable material | Non-authoritative until promoted | Require a typed proposal and write policy. |
| Episodic records | Evidence that an event occurred | Retain only under an approved policy; no retention duration is selected yet. |
| Session cache | No durable authority | Keep temporary; durable session persistence is disabled until policy approval. |
| Scratch data | None | Exclude from durable ingestion. |
| Audit log | Authoritative operational evidence | Append structured metadata; never execute text from a log. |
| Derived index | Never canonical | Keep disposable and rebuildable under `.sys4ai/memory/`. |

The binding rule is simple: memory may inform an action, but an action that depends on permission, Task state, approval, schema validity, or current control state must validate the canonical source at execution time.

## Component responsibilities

| Component | Owns | Must not own |
|---|---|---|
| Source registry and scanner | Explicit include/exclude rules, stable source identity, safe path resolution, source revisions, classification | Implicit repository-wide ingestion, secret values, or authority promotion |
| Typed normalization | Provider-neutral records, fragments, relation candidates, exact anchors | Canonical source meaning or unreviewed authority changes |
| Exact/lexical channel | Identifiers, paths, phrases, code symbols, structured fields, deterministic matches | Semantic authority, write policy, or current control-state decisions |
| Provider adapter | Mapping to Cognee, capability discovery, normalized provider errors, semantic/graph/temporal retrieval | Public agent contract, canonical truth, permission decisions, or direct durable promotion |
| Provenance ledger | Source identity, revision, content hash, extraction/config fingerprints, derivation links | Source content that must remain erased after privacy deletion |
| Policy engine | Scope, trust, authority, permission, lifecycle, sensitivity, write, and destructive-operation checks | Reviewer identity not present in canonical permission records |
| Evidence assembler | Provider-neutral result bundles, ranking/filter explanation, insufficiency results | Fluent unsupported answers or hidden source substitution |
| Optional answer synthesizer | Explicitly requested answers whose material claims cite records in the authorized evidence bundle | Default recall, uncited claims, independent retrieval, or model/profile selection |
| Public interfaces | Versioned Python, HTTP, MCP, and CLI operations | Provider-native parameters as required agent inputs |

## Source and format contract

No source enters durable project memory without a matching source-registry rule or an explicit one-time registration that creates such a rule. Exclusions take precedence over inclusions.

Each registration declares its project, location or pattern, format, canonicality, content role, authority tier, trust class, sensitivity, namespace, profile, adapter, schema where applicable, refresh mode, retention policy, owner, and write policy. Repository sources also carry a Git commit, blob hash, or explicit working-tree state in ingestion provenance. External sources carry their origin URI, retrieval time, content hash, and available license/retention metadata.

Generated HTML, PDF, wiki pages, summaries, indexes, provider records, and exports cannot outrank their canonical inputs. Secret files, provider databases, caches, build output, model assets, and temporary paths are excluded by default. The authoritative header and field rules are in the [registry contract](../../registries/README.md).

## Scope resolution

Every durable record has one primary scope and may name parent scopes.

| Scope | Meaning |
|---|---|
| `system` | The Sys4AI framework as a whole |
| `workspace` | One installation or organization |
| `project` | One target repository or project |
| `agent_type` | One class of agents |
| `agent_instance` | One configured agent instance |
| `task` | One bounded task or goal |
| `session` | Temporary session context |
| `user` | One authorized user's preferences under privacy policy |

Resolution rules:

1. A query supplies a project or executes in a context that resolves exactly one.
2. System governance may be inherited by a project.
3. Project records do not cross into another project without an explicit multi-project request and canonical grant.
4. Task and session queries may fall back to their project.
5. A lower scope may refine context but cannot override higher-authority governance.
6. Agent-instance content does not become shared project truth automatically.
7. Hidden global memory is prohibited.

## Authority, trust, lifecycle, and epistemic status

Authority and trust are separate fields. Authentication of an external source does not grant it authority.

| Tier | Name | Behavior |
|---|---|---|
| `A0` | System policy | Highest platform/host restrictions |
| `A1` | Approved Sys4AI governance | May direct behavior in valid scope |
| `A2` | Approved project control and decisions | May direct behavior in project scope when schema-valid and current |
| `A3` | Canonical project knowledge | Informs and constrains within its registered role |
| `A4` | Registered external evidence | Evidence only |
| `A5` | Agent-generated durable material | No authority until explicit promotion |
| `A6` | Session and scratch content | No durable authority |
| `A7` | Untrusted content | Never instruction authority |

Allowed trust classes are `system-controlled`, `human-approved`, `schema-validated`, `project-authored`, `externally-authenticated`, `external-unverified`, `agent-generated`, `model-extracted`, `user-supplied`, and `untrusted`.

Allowed lifecycle states are `proposed`, `staged`, `approved`, `active`, `superseded`, `rejected`, `invalidated`, `expired`, `withdrawn`, and `deleted`. Current-state recall excludes non-current states unless the query explicitly asks for history.

Allowed epistemic statuses are `source_statement`, `observation`, `claim`, `fact_candidate`, `verified_fact`, `hypothesis`, `inference`, `decision`, `procedure`, `preference`, `constraint`, `result`, `counterexample`, and `unknown`. Extraction by a model is not verification.

## Base type system

The base profile declares these core record types:

`SourceArtifact`, `SourceFragment`, `Entity`, `Statement`, `Requirement`, `Decision`, `Procedure`, `Event`, `Observation`, `Outcome`, `Feedback`, `Relation`, `Tombstone`, and `ExtensionRecord`.

The base relation vocabulary is:

`CONTAINS`, `DEFINES`, `DESCRIBES`, `IMPLEMENTS`, `VALIDATES`, `DEPENDS_ON`, `BLOCKS`, `ENABLES`, `DERIVED_FROM`, `GENERATED_FROM`, `CITES`, `SUPPORTS`, `CONTRADICTS`, `SUPERSEDES`, `INVALIDATES`, `APPLIES_TO`, `OWNED_BY`, `CREATED_BY`, `REVIEWED_BY`, `OBSERVED_DURING`, `RESULTED_IN`, `SIMILAR_TO`, `RELATED_TO`, `HAS_SOURCE`, `HAS_EVIDENCE`, `HAS_STATUS`, `USES`, and `PRODUCES`.

Every relation requires typed endpoints, scope compatibility, provenance, confidence or validation status, and a registered relation meaning. No relation raises the authority of either endpoint. A profile may add types and relations but cannot change a core meaning. A breaking semantic change requires a profile major version and migration.

The current structured graph surface returns only one-hop paths. Both endpoints
must survive the normal evidence filters and budget, and each path retains its
typed relation source, validation/confidence, temporal interval, and lifecycle
state. Deeper traversal requires a future versioned contract rather than an
implicit unbounded provider query.

## Write and lifecycle contract

```text
proposed
  -> rejected                 schema or policy failure
  -> session-only            temporary policy, when approved
  -> episodic committed      low-risk event, when approved
  -> staged -> rejected      reviewer rejects
            -> approved      canonically authorized reviewer approves
               -> canonical write -> synchronized -> active
                                                   -> superseded
                                                   -> invalidated
                                                   -> expired
                                                   -> deleted
```

Default behavior by target:

| Target | Default behavior |
|---|---|
| Session context | Temporary only; durable persistence stays off until retention policy is approved |
| Episodic event | Disabled for durable storage until retention and task policy are approved |
| Observation | Stage; an approved future policy may permit bounded episodic commit |
| Feedback | Explicit typed proposal; it cannot change authority |
| Project fact candidate or Decision | Stage for review |
| Requirement, governance, or permission | Human/canonical approval required; a general agent cannot approve |
| Canonical code or configuration | Use the normal implementation and review workflow, not direct provider mutation |
| External evidence | Register as evidence, never instruction |
| Secret or credential | Reject and alert without logging the value |

A promoted proposal becomes a normal project change, such as a patch, schema-valid control record, registry update, or reviewed source document. The service then synchronizes from that canonical source. It never keeps a higher-priority provider-only copy.

## Cognee mapping

| Sys4AI concept | Adapter mapping |
|---|---|
| Project boundary | One Cognee dataset or an equally strong isolated mapping under the deployment profile |
| Provider-neutral record | DataPoint, DataItem, document fragment, or custom mapped structure |
| Semantic fields | Explicit embeddable/index fields; never secrets or raw credentials |
| Relation | Provider graph edge plus Sys4AI relation metadata |
| Provenance | Provider relational metadata plus the Sys4AI provenance ledger |
| Durable ingest | `remember` or a controlled lower-level pipeline |
| Read | `recall` by default or lower-level search for an explicit mode |
| Improve | Provider improvement only inside Sys4AI derived-data policy |
| Delete | Provider forget/delete only after Sys4AI lifecycle authorization |
| Provider export | COGX as a supplementary export |

The adapter preserves stable Sys4AI IDs, project mapping, source metadata, authority, trust, status, and exact-content references outside embeddings. It returns Sys4AI evidence bundles, normalizes errors, reports health/capabilities, and records provider/configuration fingerprints.

## Configuration and deployment gates

The tracked [configuration contract](../../config/README.md) selects the approved
local embedded no-cloud-key profile while keeping the provider inactive during
load. Configuration never contains a credential value and does not allow Cognee
or a model library to select a remote default silently.

The first profile uses local embedded relational, vector, and graph storage
through one process, SQLite/FTS5 exact retrieval with canonical reread, Ollama
`llama3.1:8b`, and 384-dimensional FastEmbed MiniLM embeddings. Session and
episodic persistence is TTL-bound, provider-neutral export uses an `age`
envelope, and feedback is explicit and typed only. Network listening, shared
deployment, cloud fallback, and non-fixture destructive execution remain
disabled.

## Version and migration rules

- Version the public API, record schemas, profile schemas, export package, provider adapter, and memory generation independently.
- A minor version may add optional fields without changing existing meaning.
- A required field or semantic change requires a major version and migration.
- Provider upgrades require the compatibility and rollback checks in the [runtime policy](runtime-and-dependency-policy.md).
- Each generation records source, schema, profile, adapter, model, configuration, and lock fingerprints.
- Existing material is classified before ingestion. Unknown-origin material is `untrusted`; agent strings without provenance are `agent-generated` and `proposed` or episodic; imported relations are `model-extracted` or `imported-unverified` until validated.
- Imported existence never grants governance authority.

## Binding principle and goal traceability

| ID | Architecture enforcement |
|---|---|
| `P-01` | Source registry, canonical path roles, and promotion back to reviewed source |
| `P-02` | Canonical reread for execution-critical control state |
| `P-03` | Stable Python, HTTP, MCP, and CLI contracts independent of one agent |
| `P-04` | Provider adapter and provider-neutral schemas/export |
| `P-05` | Local embedded profile with no required cloud service |
| `P-06` | Disposable generated paths and generation-based rebuild inputs |
| `P-07` | Typed proposal schemas, write-policy matrix, and review records |
| `P-08` | Evidence bundles with source, trust, authority, status, and ranking details |
| `P-09` | Isolated authority namespaces and no authority inheritance |
| `P-10` | Exact/lexical channel and canonical exact-source preservation |
| `P-11` | Supersession, invalidation, expiration, tombstones, and receipts |
| `P-12` | Canonical permission envelopes and privileged destructive operations |
| `P-13` | Required project/dataset, role, and durability scope |
| `P-14` | Versioned profile registry and `ExtensionRecord` contract |
| `P-15` | Focused contract, security, rebuild, isolation, and retrieval evidence |
| `G-01` | Project-scoped durable records rebuilt across sessions |
| `G-02` | Agent-independent interfaces and storage ownership |
| `G-03` | Canonical path ownership and revalidation |
| `G-04` | Exact, lexical, semantic, relational, and temporal channels |
| `G-05` | Provenance and trust on every durable result |
| `G-06` | Typed, staged, reviewable, auditable writes |
| `G-07` | No-cloud-key local profile |
| `G-08` | Source/profile/schema/configuration-driven rebuild |
| `G-09` | Versioned Python, HTTP, CLI, and MCP contracts |
| `G-10` | One embedded writer, project isolation, and explicit cross-project grants |
| `G-11` | Profile registry and non-breaking extension rule |
| `G-12` | Sys4AI-native export plus supplementary COGX |

## Stage boundaries

| Stage | Contract boundary |
|---|---|
| 0 | Repository fit, architecture, public schemas, registries, trust/authority policy, configuration, and security controls |
| 1 | Local read-only service, provider adapter, exact channel, base adapters, sync/recall/get/explain/health, and provenance |
| 2 | Typed writes, staging, approval, supersession, expiration, and delete-derived |
| 3 | Generation rebuild, receipts, provider-neutral import/export, COGX where supported, and drift detection |
| 4 | Authentication, dataset isolation, role/permission mapping, concurrency controls, and shared service |
| 5 | Profile SDK, example profile, migrations, and profile-specific golden queries |
| 6 | Explicitly approved feedback, auditable provider improvement, stale/duplicate suggestions, and non-destructive consolidation |

Later-stage behavior is not implemented merely because its contract is described here.

## Architecture risk register

| PRD risk | Required mitigation and gate |
|---|---|
| Cognee API or storage changes | Exact pin, adapter isolation, contract tests, provider-neutral records/export, migration review |
| Repository layout differs from assumptions | Approved [repository-fit mapping](repository-fit.md) and exact path review |
| Semantic retrieval sounds correct but misses exact source | Independent exact channel, evidence bundle, canonical validation |
| Generic schema becomes too vague | Small required core plus typed profile extensions |
| Core schema becomes too specialized | Domain types remain in versioned profiles |
| Memory duplicates runtime state | Binding state boundary and canonical reread |
| Automatic improve changes meaning | Derived-only improvement, receipts, and no authority mutation |
| Imported content poisons memory | Trust classes, isolated authority, write-time provenance, and staging |
| Embedded stores receive concurrent direct writes | One service process and no client file access |
| Secret files are ingested | Explicit exclusions, secret scanning, prohibited sensitivity class |
| Rebuild is non-reproducible due to LLM extraction | Model/configuration fingerprints, deterministic parsing, and generation comparison |
| Provider export is incomplete | Sys4AI-native export is the primary portability contract |
| Too much session data becomes permanent | Persistence disabled until retention policy; typed promotion only; no transcript dump |
| Excessive testing slows development | Contract-risk suite and focused validation targets |
| Overbroad MCP surface enables destructive action | Read/propose default and privileged destructive operations |
| Stale records outrank current decisions | Status filtering, supersession, source revision, and freshness rules |

Security threats and the fifteen binding controls are maintained in the [threat model](../security/threat-model.md).
