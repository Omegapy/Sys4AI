# Repository fit and preservation boundary

Status: approved Stage 0 architecture record  
Decision date: 2026-09-03  
Authority: the user's approval of the Project Director's implementation boundary for `PLAN-20260903-2DA243C0`

This record maps the [Sys4AI Memory Service PRD](../../PRDs/Sys4AI_Memory_Service_PRD.md) into this product directory. It resolves repository placement and the package/tooling baseline. Later approved local-policy choices are recorded in the [decision register](../decisions/decision-register.md). This record does not initialize a Git repository, create a remote, publish a package, deploy a service, or authorize non-fixture destructive execution.

## Product identity

| Item | Approved mapping |
|---|---|
| Product root | The directory containing this file: `Projects/Sys4AI-Memory-Service/` in the Sys4AI depot workspace |
| Product relationship to the depot | Independent product project registered by the depot; registration is inventory, not copy, update, install, or publication authority |
| Python distribution | `sys4ai-memory-service` |
| Python import package | `sys4ai_memory` under `src/sys4ai_memory/` |
| Primary CLI entry point | `sys4ai-memory` |
| Other public channels | Provider-neutral Python, HTTP, and MCP contracts owned by this product |
| Supported first runtime | Python 3.12 |
| Dependency and lock manager | `uv`, `pyproject.toml`, and `uv.lock` |
| Initial semantic provider | Cognee 1.5.3 behind the Sys4AI provider adapter |
| Initial deployment direction | One local embedded process with no cloud key and no network listener enabled by default |
| Repository/remote state | Not established by this decision; no remote, publication, or deployment target is implied |

The CLI may expose the PRD operations as subcommands, but the names and request/response behavior come from the public schemas and implementation. Documentation examples do not authorize a compatibility alias such as `sys4ai memory` in another package.

## Canonical path ownership

| Path | Role | Canonical or derived | Stage 0 rule |
|---|---|---|---|
| `PRDs/` | Product requirements | Canonical | The copied PRD is the product requirement source. Changes require the normal governed review process. |
| `docs/architecture/` | Repository and architecture records | Canonical | Records product boundaries, invariants, and mappings. It cannot prove runtime behavior. |
| `docs/decisions/` | Architecture decisions and decision status | Canonical | Distinguishes approved decisions from open policy and evidence-spike questions. |
| `docs/security/` | Security contracts and operating rules | Canonical | Defines required controls. Runtime evidence is separate. |
| `config/` | Tracked configuration contract and safe defaults | Canonical configuration | Must contain no credential value. A safe default may keep capabilities disabled pending a decision. |
| `registries/` | Source, profile, and relation declarations | Canonical under their documented schemas | A registry row declares policy and identity; it is not proof that an adapter or relation is implemented. |
| `schemas/memory/` | Public validation contracts | Canonical | Schema versions govern records and operation envelopes. Generated schema projections must not be hand-edited. |
| `src/sys4ai_memory/` | Product implementation | Canonical implementation evidence | Agents and clients use Sys4AI contracts; they do not access Cognee storage or native shapes directly. |
| `control_records/memory/` | Durable proposals, approvals, receipts, migrations, incidents, and canonical permissions | Canonical only when schema-valid and created through the governed workflow | The local policy names one human `local-owner`, one approval, and no self-approval. |
| `tests/` | Contract, security, and behavior evidence | Canonical test source | Passing tests are evidence only for the behaviors they exercise. |
| `.sys4ai/memory/` | Provider data, exact indexes, caches, staging output, audit runtime logs, and exports | Derived and disposable | Must remain excluded from version control and must not be created until path, exclusion, and dry-run gates pass. |
| Model caches and downloaded weights | Local runtime assets | Derived | Keep outside tracked paths. Their provider and model identities require a separate approved profile. |

The canonical formats in this table are ordinary UTF-8 Markdown, CSV, JSON,
TOML, YAML, and Python sources. The portability acceptance test copies a
representative PRD, all three registries, and a public schema into a disposable
Git repository, commits them without transformation, reproduces every byte
through `git show`, locates a requirement with `grep`, and verifies a clean
working tree. This demonstrates Git/text readability without initializing Git
in the product directory or treating derived provider data as canonical.

Durable control records are project sources, not semantic-memory-owned state. Execution that depends on a permission, approval, Task status, validation result, or receipt must reread and validate the canonical record.

## Package and command boundary

The product owns one stable agent-facing namespace. Provider calls and provider-native MCP tools remain internal to the Cognee adapter.

```text
client or agent
    -> sys4ai-memory CLI / Sys4AI Python / HTTP / MCP contract
    -> scope, permission, write-policy, and evidence assembly
    -> exact/lexical channel + provider adapter + provenance ledger
    -> Cognee 1.5.3 or a future conforming provider
```

The package boundary must preserve these rules:

1. Public requests and responses use versioned Sys4AI schemas.
2. No public schema contains a Cognee-native object as a required field.
3. Stable Sys4AI IDs, project/dataset mapping, authority, trust, status, and provenance remain outside embeddings and survive a provider replacement.
4. All simultaneous clients use the service process. They do not write embedded databases directly.
5. Exact source content remains in canonical sources or provider-neutral records. A summary or embedding never replaces it.

## Depot and concurrent-work preservation

The surrounding Sys4AI root is a depot manager. This product decision does not grant permission to propagate files between the depot's reusable collections and this project. In particular:

- Do not overwrite `SKILLS-depo/`, `SOULS-depo/`, `AGENTS-depo/`, `ROLES-depo/`, sibling projects, parent Tasks, TRDs, implementation plans, or verification records.
- Do not replace this project's `AGENTS.md`, `SOUL.md`, `ROLE.md`, or copied local skills/roles merely because a reusable source has a matching name.
- Preserve unrelated working-tree changes. A later Git operation must inspect the current root and select exact paths.
- Project registration records factual identity only. It does not initialize Git, create a remote, install dependencies, publish, or deploy.
- Generated storage and exports must never be used as the only copy of durable knowledge.

## Stage 0 review boundary

This mapping is an approved architecture input. Stage 0 exit still requires the Project Director to inspect the integrated public schemas, configuration, registries, policy documents, source paths, and checks. Runtime behavior, provider compatibility, local model operation, authentication, and end-to-end recall are not established by this document.
