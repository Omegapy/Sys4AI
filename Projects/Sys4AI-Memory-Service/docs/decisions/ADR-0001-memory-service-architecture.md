# ADR-0001: Source-first provider-neutral memory service

Status: accepted  
Date: 2026-09-03  
Scope: base Sys4AI Memory Service architecture  
Authority: approved PRD decisions `MEM-DEC-001` through `MEM-DEC-014` and the user's approved implementation boundary

## Context

Sys4AI agents need durable project recall across sessions, but retrieved memory cannot replace Git, registered canonical sources, or deterministic control records. Semantic providers improve conceptual and relational retrieval, yet their data models, storage formats, and generated relations are not suitable as the public authority boundary.

The service also needs exact content, project isolation, typed durable writes, provenance, rebuildability, and future agent-specific extensions. Exposing Cognee directly would couple agents to one provider and could allow provider behavior to bypass Sys4AI authority and write controls.

## Decision

Build an independent local-first service with provider-neutral Sys4AI contracts. Canonical project sources flow through a source registry and typed normalization into three cooperating derived channels:

1. a deterministic exact and lexical index;
2. a Cognee 1.5.3 adapter for semantic, graph, relational, and temporal capabilities;
3. a provider-neutral provenance ledger.

The service applies scope, authority, trust, permission, lifecycle, ranking, and evidence-assembly rules before returning results or accepting writes. General agents receive read and propose operations by default. Approval, promotion, rebuild activation, import replacement, mass deletion, and privacy erasure remain privileged and require canonical permission checks plus impact previews where applicable.

The architecture adopts all fourteen PRD product decisions:

- canonical Git and registered sources remain authoritative;
- derived memory is disposable and rebuildable;
- the service is independent of individual agents and providers;
- Cognee is the replaceable first provider;
- retrieval combines exact, lexical, semantic, graph, and temporal channels;
- governance, control state, project knowledge, external evidence, generated memory, and session data retain distinct authority and trust classes;
- deterministic state remains canonically owned outside semantic memory;
- durable writes are typed and policy controlled;
- external or summarized content gains no governance authority without explicit promotion;
- provider improvement cannot change canonical authority;
- Sys4AI-native export is the primary portability contract and COGX is supplementary;
- versioned profiles extend the base product without core forks;
- private chain-of-thought is outside the memory contract; and
- destructive tools are not exposed to general agents by default.

## Boundary invariants

1. An execution-critical result must be reread and validated from its canonical source before action.
2. Every durable result identifies its project scope, record, source or labeled derivation, authority, trust, status, and retrieval evidence.
3. A provider record, embedding, summary, imported relation, or retrieval score cannot raise authority.
4. Public operation and record schemas do not require Cognee-native fields.
5. Provider storage, exact indexes, caches, logs, staging output, and exports under `.sys4ai/memory/` are disposable derived state.
6. Exact source text, identifiers, code, configuration, commands, and structured values are preserved outside semantic summaries.
7. Cross-project access is denied unless an explicit multi-project request and canonical authorization both allow it.
8. Direct client writes to embedded provider files are prohibited.

## Consequences

The service has more policy and provenance work than a direct Cognee integration. In return, agents retain a stable interface, canonical sources remain recoverable with ordinary tools, and provider replacement does not require rewriting every agent.

The architecture must maintain an exact retrieval implementation as well as the semantic provider. It must also version schemas, adapters, profiles, exports, and generations. Generated relations and provider-side improvement require explicit provenance and cannot silently modify authoritative meaning.

## Deferred decisions

This ADR established the decision gates; their current outcomes are recorded in
the [decision register](decision-register.md). The local release now uses
authenticated network exposure only, the approved local LLM/embedding pair,
SQLite/FTS5 plus canonical reread, bounded retention, `age`-encrypted exchange,
the software-engineering profile, and explicit typed feedback only. It selects
no shared production backend. Product deployment and non-fixture destructive
execution remain outside the current authority.

## Related records

- [Repository fit and preservation boundary](../architecture/repository-fit.md)
- [Runtime and dependency policy](../architecture/runtime-and-dependency-policy.md)
- [Configuration contract](../../config/README.md)
- [Threat model and binding controls](../security/threat-model.md)
- [Canonical PRD](../../PRDs/Sys4AI_Memory_Service_PRD.md)
