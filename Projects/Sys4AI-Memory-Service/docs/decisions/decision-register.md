# Memory service decision register

Register version: 1.1  
Reviewed source date: 2026-09-03

This register separates approved product decisions from unresolved user-policy choices and technical evidence spikes. It covers every `MEM-DEC`, `MEM-OQ`, and plan `Q` identifier in the [canonical PRD](../../PRDs/Sys4AI_Memory_Service_PRD.md) and parent plan `PLAN-20260903-2DA243C0` revision 3.

Status meanings:

- `approved`: an identified authority has selected the stated outcome.
- `open`: the affected capability must remain unavailable or use the stated deny-safe behavior until an authorized decision is recorded.
- `evidence-spike`: no product selection has been made; a bounded technical comparison must return evidence before an authorized decision.

An implementation convenience, provider default, installed tool, or registry row cannot change a status in this file.

On 2026-09-03 the user explicitly approved `MEM-OQ-003` through
`MEM-OQ-011` exactly as proposed in Task Response 0012, including the local
model-cache fill and `age` installation/testing. Product Git initialization,
publication, deployment, and non-fixture destructive execution were explicitly
excluded from that authority and remain disabled.

## PRD product decisions

| ID | Status | Approved decision | Authority and evidence |
|---|---|---|---|
| `MEM-DEC-001` | approved | Git and registered canonical sources remain the long-term source of truth. | PRD Section 34; accepted by the user's approved architecture baseline on 2026-09-03. |
| `MEM-DEC-002` | approved | Derived memory databases are disposable and rebuildable. | PRD Section 34; accepted by the user's approved architecture baseline on 2026-09-03. |
| `MEM-DEC-003` | approved | The memory service is independent of individual agents. | PRD Section 34; accepted by the user's approved architecture baseline on 2026-09-03. |
| `MEM-DEC-004` | approved | Cognee is the initial provider behind a Sys4AI adapter. | PRD Section 34; user approved Cognee 1.5.3 as the replaceable first provider. |
| `MEM-DEC-005` | approved | The base product combines exact, lexical, semantic, graph, and temporal retrieval. | PRD Section 34; accepted by the user's approved architecture baseline on 2026-09-03. |
| `MEM-DEC-006` | approved | Governance, control state, project knowledge, external evidence, generated memory, and session data use separate authority and trust classes. | PRD Sections 10, 15, and 34; accepted by the user's approved architecture baseline. |
| `MEM-DEC-007` | approved | Deterministic runtime state is not owned by semantic memory. | PRD Sections 10 and 34; accepted by the user's approved architecture baseline. |
| `MEM-DEC-008` | approved | Durable agent writes are typed and policy controlled. | PRD Sections 22 and 34; accepted by the user's approved architecture baseline. |
| `MEM-DEC-009` | approved | External content cannot become governance without explicit promotion. | PRD Sections 15, 24, and 34; accepted by the user's approved architecture baseline. |
| `MEM-DEC-010` | approved | Provider-side improvement cannot change canonical authority. | PRD Sections 22, 23, and 34; accepted by the user's approved architecture baseline. |
| `MEM-DEC-011` | approved | Sys4AI defines its own provider-neutral export package; COGX is an additional provider export. | PRD Sections 23 and 34; ZIP/JSON/JSONL plus `age` X25519 was approved on 2026-09-03. |
| `MEM-DEC-012` | approved | Agent-specific functionality uses versioned memory profiles rather than core forks. | PRD Sections 16 and 34; accepted by the user's approved architecture baseline. |
| `MEM-DEC-013` | approved | Private chain-of-thought is not a memory requirement; store evidence, concise rationale, actions, and outcomes instead. | PRD Sections 6 and 34; accepted by the user's approved architecture baseline. |
| `MEM-DEC-014` | approved | General agents receive read and propose MCP operations by default; destructive tools are privileged. | PRD Sections 22, 24, and 34; accepted by the user's approved architecture baseline. |

## PRD open questions

| ID | Status | Current answer or required evidence | Safe behavior before resolution | Authority or next decision gate |
|---|---|---|---|---|
| `MEM-OQ-001` | approved | Product root is `Projects/Sys4AI-Memory-Service/`; distribution is `sys4ai-memory-service`, import package is `sys4ai_memory`, and CLI is `sys4ai-memory`. | Work only within the registered independent product boundary. | User approved the Project Director's repository boundary on 2026-09-03; see [repository fit](../architecture/repository-fit.md). |
| `MEM-OQ-002` | approved | Python 3.12 and `uv` are canonical for the first release line. | Reject unsupported interpreter or unlocked production execution. | User approved the runtime bundle on 2026-09-03; see [runtime policy](../architecture/runtime-and-dependency-policy.md). |
| `MEM-OQ-003` | approved | Network exposure requires authentication. The supported single-user posture is in-process with no listener; loopback model daemons are separately bounded development dependencies, not an unauthenticated memory-service listener. | Keep the memory-service listener disabled in the local profile. Any future HTTP/MCP listener must use an approved authenticated profile. | User approval of Task Response 0012 on 2026-09-03. |
| `MEM-OQ-004` | approved | Use local Ollama `llama3.1:8b` plus FastEmbed `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions, with no remote or cloud fallback. | Models stay in ignored product-local cache paths; configuration load never starts or downloads either runtime. | User approval of Task Response 0012 plus the [local model and Cognee spike](../verification/MEM-OQ-004-local-model-spike.md). |
| `MEM-OQ-005` | approved | Use SQLite exact tables plus FTS5, require canonical reread for execution-critical use, and retain `rg` as an operator diagnostic fallback. | Exact storage remains derived and rebuildable; provider or diagnostic search cannot replace canonical text. | User approval of Task Response 0012 plus the [exact-index spike](../verification/MEM-OQ-005-exact-index-spike.md). |
| `MEM-OQ-006` | approved | Use one human `local-owner` reviewer, exactly one approval, no proposal self-approval, and the canonical mapping at `control_records/memory/permissions.json`. | General agents retain read/propose only. No delete, administer, or rebuild grant is present in the approved local mapping. | User approval of Task Response 0012; see the [control-record boundary](../../control_records/memory/README.md). |
| `MEM-OQ-007` | approved | Session retention is 72 hours and episodic retention is 365 days, with expiry purge and no silent extension. | TTL enforcement applies before durable persistence and expiry removes only the affected derived class. | User approval of Task Response 0012 and executable retention-policy tests. |
| `MEM-OQ-008` | approved | Use a deterministic provider-neutral ZIP containing JSON/JSONL, manifest, and checksums, wrapped in an `age` X25519 envelope whenever content is not public. | Secret-prohibited material remains excluded; identity files remain outside packages, source control, logs, and durable memory. | User approval of Task Response 0012 plus the [age exchange verification](../verification/age-encrypted-package.md). |
| `MEM-OQ-009` | approved | Approve no shared production backend for this release. Shared mode stays disabled until separate infrastructure, access-control, licensing, migration, and load evidence is authorized. | Embedded storage remains in-process and project-scoped; no deployment claim is made. | User approval of Task Response 0012 on 2026-09-03. |
| `MEM-OQ-010` | approved | Use `software-engineering@1` as the first derived-agent profile proof. | The extension adds types, relations, an adapter, policies, retrieval rules, and evaluation data without changing the base API. | User approval of Task Response 0012 and the tracked profile integration test. |
| `MEM-OQ-011` | approved | Accept explicit typed feedback only. Collect no automatic retrieval signals, telemetry export, or implicit feedback retention. | Automatic feedback remains denied by policy; explicit records retain evidence, actor, scope, authority, sensitivity, and retention metadata. | User approval of Task Response 0012 and executable feedback-policy tests. |

## Parent implementation-plan questions

| ID | Status | Current answer or required evidence | Safe behavior before resolution | Authority or next decision gate |
|---|---|---|---|---|
| `Q-001` | approved | The service lives in the newly registered independent product root `Projects/Sys4AI-Memory-Service/`, not in the depot manager root. | Do not propagate product files into reusable depot collections or sibling projects. | User approved the Project Director's boundary on 2026-09-03. |
| `Q-002` | approved | Python 3.12 and `uv` are canonical. | Use the locked product environment only. | User approved the Project Director's runtime bundle on 2026-09-03. |
| `Q-003` | approved | Network exposure is authenticated-only; the supported local memory-service posture is in-process with no listener. | Keep the tracked listener disabled. | Same authority as `MEM-OQ-003`. |
| `Q-004` | approved | The local profile is Ollama `llama3.1:8b` plus FastEmbed `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions. | Deny remote and cloud fallback; cache fill is explicit and rebuildable. | Same authority and evidence as `MEM-OQ-004`. |
| `Q-005` | approved | Exact retrieval uses SQLite tables plus FTS5, canonical reread, and an operator `rg` diagnostic fallback. | Keep canonical text authoritative. | Same authority and evidence as `MEM-OQ-005`. |
| `Q-006` | approved | The canonical local policy names one human `local-owner`, one approval, and no self-approval. | Reread canonical permission state for every decision. | Same authority as `MEM-OQ-006`. |
| `Q-007` | approved | Session and episodic retention are 72 hours and 365 days with expiry purge and no silent extension. | Enforce the configured maximum TTLs. | Same authority as `MEM-OQ-007`. |
| `Q-008` | approved | The portable format is deterministic ZIP JSON/JSONL with manifest/checksums and an `age` X25519 envelope for non-public content. | No unencrypted production fallback. | Same authority and evidence as `MEM-OQ-008`. |
| `Q-009` | approved | No shared production backend is selected for this release. | Keep shared mode disabled. | Same authority as `MEM-OQ-009`. |
| `Q-010` | approved | `software-engineering@1` is the first derived-agent proof profile. | Preserve the base API and authority semantics. | Same authority as `MEM-OQ-010`. |
| `Q-011` | approved | Feedback is explicit and typed only; no automatic signals are collected. | Automatic collection and telemetry export remain disabled. | Same authority as `MEM-OQ-011`. |
| `Q-012` | approved | Stage 1 begins with a local embedded no-cloud-key profile. It does not use provider API keys, Cognee API mode, or Cognee Cloud by default. | Use only the approved local model pair and deny outbound model fallback. | User approved the Project Director's implementation bundle on 2026-09-03. |

## Change rule

An approved decision changes only through a versioned decision record with authority, scope, compatibility impact, and migration effect. An open or evidence-spike item changes only after the named gate produces reviewable evidence and the authorized decision is recorded. The safe behavior remains binding until then.
