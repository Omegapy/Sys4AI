---
schema_version: 2
trd_id: "TRD-20260913-8BACF221"
title: "Scalable verification and Task storage"
slug: "scalable-verification-and-task-storage"
created_at: "2026-09-13T12:54:42-06:00"
updated_at: "2026-09-13T12:54:42-06:00"
status: "draft"
revision: 1
last_action_id: "TO-TRD-001"
status_reason: "Created as a draft from an explicit user request."
---

# Task Requirement Document: Scalable verification and Task storage

## Destination

Make Sys4AI verification scale with the dependencies of the current operation while preserving growing Task history as usable, verifiable evidence. Routine work must retain complete relevant integrity checks without repeatedly scanning unrelated historical artifacts.

## Captured user intent

U01: The user requested a new tracked Task using To-TRD to capture the supplied scalability recommendations as a separate requirements document. The purpose is to remove the growth limitation exposed by the former 64 MiB guard inventory ceiling and address the underlying repeated scanning, catalog validation and write serialization costs.

U02: The user selected immediate verification of every dependency of the current operation, verification of historical evidence against its expected hash when accessed, and separate full archive audits. This accepts potentially later detection of damage to unrelated historical evidence.

U03: This requirements capture is separate from the existing integration-planning Task. The request authorizes this document workflow; it does not approve the unseen document or authorize a downstream implementation plan, implementation, installation, migration, Git activity or external action.

## Context and sources

- U01 and U03: [Captured request](../Tasks/Task-capture-scalable-verification-and-task-storage-requirements-2026-09-13--64DDD6CF/artifacts/orchestration/bootstrap/request.json). The exact user-supplied attachment was retained as [S01, scalability recommendations](../Tasks/Task-capture-scalable-verification-and-task-storage-requirements-2026-09-13--64DDD6CF/artifacts/orchestration/bootstrap/user-supplied-recommendations.md), SHA-256 `17c0c319bfe16af36722f216cabf123e72277000e3adceda5c1a933342f76353`.
- U02: [Recorded user integrity choice](../Tasks/Task-capture-scalable-verification-and-task-storage-requirements-2026-09-13--64DDD6CF/artifacts/orchestration/manager/user-integrity-choice.json), SHA-256 `3e1a7ff89a69e2bddc0b10d93e051622edaba324a22b576c7b4479f792c89fd4`. The affirmative answer selected the behavior stated in Captured user intent; it did not approve a document revision.
- S02: Installed [guard engine](../.agents/skills/ontology/scripts/ontology_guards.py), particularly constants, `_snapshot`, `_context` and `Decision._recheck`. Inspection for this capture found a 128 MiB byte bound, a 10,000-entry bound, whole-file reads before the accumulated byte check, and the complete `Tasks/` tree in shared context. These are current inspected implementation facts, not desired long-term capacity targets.
- S03: Installed [Task helper](../.agents/skills/agent-task/scripts/task_state.py), `scan_catalog` and `response_transaction`, validates catalog relationships and serializes cooperating mutations through catalog and Task locks. Installed [TRD](../.agents/skills/to-trd/scripts/trd.py), [plan](../.agents/skills/to-implementation-plan/scripts/plan_state.py) and [memory recovery](../.agents/skills/memory/scripts/memory_recovery.py) adapters also enter the shared guard.
- S04: [AGENTS.md](../AGENTS.md) and [SPECS.md](../SPECS.md) define project ownership, reusable-source adoption, canonical records, local Python 3.12 tooling and authority boundaries. The installed [To-TRD contract](../.agents/skills/to-trd/references/trd-contract.md) separates document approval from downstream work.
- S05: The prior [capacity-repair report](../Verification/guard-capacity-20260913/REPORT.md) records the separately authorized increase to 128 MiB and its verification limits. The installed [Curator scanner](../.agents/skills/curate/scripts/curator_git.py), `changed_metadata`, supplies an existing bounded-streaming example; adopting that implementation is not required.

S01's research snapshot reported 63.95 MiB of base guard context, 63.53 MiB in Task folders, 60.04 MiB in one cancelled Task, 1.74 MiB across 26 canonical Task records, and 13.97 MiB of duplicate artifact content. Its 0.286–0.295-second measurements covered complete Task snapshots, not complete transactions or cold-disk benchmarks. These are values from the supplied September 13, 2026 report; this capture did not repeat those measurements.

S01 cited [Bazel Skyframe](https://bazel.build/reference/skyframe), [Git objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects), [Bazel caching](https://bazel.build/remote/caching), [Git race handling](https://git-scm.com/docs/racy-git), [Watchman recovery](https://facebook.github.io/watchman/docs/troubleshooting) and [SQLite isolation](https://www.sqlite.org/isolation.html). They remain background research references supplied with the report, not independently refreshed sources in this capture or mandates to adopt those projects.

## In scope

- Operation dependency selection, integrity checks, resource accounting, repeated validation and storage growth for the installed shared guard and the Task, implementation-plan, TRD, memory and ontology workflows that use it.
- Immediate verification of current dependencies; historical evidence retention and verified access; a separate complete archive-integrity audit.
- Correct reuse of derived information, safe cooperation between independent Tasks, and representative evidence of scalability and preserved safeguards.
- Requirements applicable to reusable capability work while retaining separate authority for the registered Template, active root adoption and ordinary product projects.

## Out of scope

- Performing the captured changes, creating a downstream implementation plan, choosing or installing a database or service, migrating stored records, changing the guard ceiling, or changing locks during this document Task.
- Modifying the independent integration-planning Task, its approved source TRD or its plan artifacts.
- Deleting or expiring historical evidence to reduce inventory size; weakening ownership, approval, integrity, path-safety or recovery checks to obtain performance gains.
- Automatic adoption into existing product projects, unattended scheduling of audits, cloud or distributed storage, and Git or external publication.
- A new fixed capacity or latency service-level target. Such implementation budgets require representative evidence and must satisfy the behavioral acceptance below.

## Task requirements

### REQ-001 — Derive the complete operation dependencies
- Requirement: Each affected owning helper shall identify the complete reads, writes and governing constraints needed for its operation, so the shared guard can verify that scope without relying on a caller-supplied omission list.
- Source: U01; S01 recommendation 2; S02 shared context; S03 owning helpers.
- Acceptance: The dependency description covers selected canonical state, requested targets, referenced evidence, current governing rules and relevant cross-record constraints for representative Task, plan, TRD, memory and ontology mutations.
- Acceptance: Omitting or changing a dependency in caller input cannot cause an operation to proceed without the corresponding owning-helper check; newly relevant relationships invalidate the prior dependency decision.
- Depends on: None.

### REQ-002 — Keep authorization and freshness live
- Requirement: Routine operations shall immediately verify every current dependency and preserve exact authorization, owner and generation, revision, content and target checks through the owning transaction's commit boundary.
- Source: U02; S01 recommendations 2 and 4; S02 `_recheck`; S03 transaction checks; S04 authority boundaries.
- Acceptance: A changed relevant input, stale owner or generation, stale revision, unauthorized target, changed rule or changed operation argument blocks stale execution or requires a fresh valid decision before mutation.
- Acceptance: Derived metadata, cached decisions and semantic conformance cannot substitute for current action authority or erase an existing path, symlink, integrity or recovery rejection.
- Depends on: REQ-001

### REQ-003 — Decouple routine verification from unrelated history
- Requirement: Increasing historical artifact bytes or entries outside an operation's complete dependency set shall not increase that operation's historical content hashing or require enumeration of the growing unrelated artifact tree.
- Source: U01 and U02; S01 central recommendation and recommendation 5.
- Acceptance: With the active operation, complete dependency set and relevant shared catalog facts held fixed, adding unrelated historical files leaves the set and byte count of historical content read for routine verification unchanged.
- Acceptance: The same comparison does not fail solely because unrelated retained history exceeds the old 64 MiB or current 128 MiB inventory ceiling; operation-specific resource limits still apply to relevant work.
- Depends on: REQ-001, REQ-002

### REQ-004 — Preserve and verify historical evidence on access
- Requirement: Historical evidence shall retain its identity, provenance and expected content hash, and its bytes shall be verified against that hash before the evidence is consumed by an operation.
- Source: U02; S01 recommendation 3; S04 history and evidence preservation.
- Acceptance: Existing referenced evidence remains resolvable with its recorded identity and expected hash; missing or altered referenced content is reported and cannot be accepted as the expected evidence.
- Acceptance: A changed unrelated historical file need not block a routine operation that does not consume it; consuming that file detects the mismatch. No manifest or retained hash alone is represented as proof of its current mutable bytes.
- Depends on: REQ-001, REQ-002

### REQ-005 — Provide a separate complete archive audit
- Requirement: A separately invoked audit shall verify retained historical evidence against its expected inventory and hashes, and clearly distinguish a complete integrity result from an incomplete, interrupted or failed audit.
- Source: U02; S01 recommendation 3 and its explicit integrity tradeoff.
- Acceptance: The audit identifies expected items that are missing or hash-mismatched and accounts for files outside the expected inventory without silently declaring them verified.
- Acceptance: An audit that cannot examine its full declared archive scope reports that scope and remaining coverage; it does not report a complete pass. The result states that unrelated damage may have arisen or been discovered between audits.
- Depends on: REQ-004

### REQ-006 — Bound verification resources during work
- Requirement: Verification shall enforce distinct, inspectable resource budgets during traversal and content reading, with operation input size, retained buffers, verification work or time, and total retained history treated as separate quantities.
- Source: U01; S01 recommendation 1; S02 `_snapshot`; S05 bounded-streaming example.
- Acceptance: Large-file and large-directory cases stop at the applicable budget without first retaining the full file or full recursive listing; any bounded read or traversal overhead is documented and measured.
- Acceptance: A limit result names the exhausted resource and observed consumption and cannot become a successful verification. A partially committed owning operation retains its explicit recovery status and receipt semantics.
- Depends on: REQ-001, REQ-002

### REQ-007 — Expose useful scalability diagnostics
- Requirement: Verification and transaction diagnostics shall expose the work needed to explain capacity failures, repeated processing and contention without disclosing file contents or credentials.
- Source: U01; S01 recommendations 1 and 5; S04 privacy and evidence constraints.
- Acceptance: Representative operation evidence reports bytes read or hashed, entries examined, elapsed verification and complete-operation time, peak memory, and lock wait or hold duration, identifying where each measurement comes from.
- Acceptance: Limit failures identify major contributors within a bounded diagnostic output. When derived reuse is present, diagnostics distinguish reused results from fresh verification rather than presenting reused data as newly read content.
- Depends on: REQ-006

### REQ-008 — Make incremental reuse correct and recoverable
- Requirement: Reused content hashes and parsed metadata shall remain tied to their verified inputs, and any derived index shall be rebuildable without replacing canonical JSON or Markdown as the source of truth.
- Source: U01; S01 recommendation 4; S04 canonical-state constraints.
- Acceptance: Relevant input changes invalidate affected reuse; same-size rapid edits, uncertain filesystem notifications and lost watcher events cannot make stale evidence valid solely because timestamps or notifications appear unchanged.
- Acceptance: Missing, corrupt or stale derived data invokes safe rebuilding, existing authoritative reads or an explicit failure. It neither loses canonical history nor approves an operation using an unverified substitute.
- Depends on: REQ-001, REQ-002, REQ-004

### REQ-009 — Preserve safe concurrent Task work
- Requirement: Independent Tasks shall retain separate ownership and artifacts while shared transactions protect the actual uniqueness, relationship, ownership and recovery constraints they require.
- Source: U03; S01 recommendations 2 and 5; S03 catalog invariants and locking; S04 manager ownership.
- Acceptance: Concurrent operations on unrelated Tasks complete or report a retryable conflict without lost updates, mixed ownership or interference with another Task's approved sources and artifacts.
- Acceptance: Operations with a genuine shared dependency detect conflicts and revalidate current state before retrying; interrupted writes retain their documented recovery route. Serialized shared bookkeeping remains permitted when required for correctness.
- Depends on: REQ-001, REQ-002, REQ-008

### REQ-010 — Preserve canonical contracts and adoption boundaries
- Requirement: Scalability changes shall preserve canonical record identities, document states, history, evidence references, Task ownership and helper recovery semantics, together with existing project-local and reusable-source ownership boundaries.
- Source: U03; S01 recommendations 3 and 4; S04 project governance and storage contracts.
- Acceptance: Existing valid Task, plan and TRD records and referenced evidence remain readable with unchanged meanings; generated indexes and optional derived storage do not grant approval, change authoritative state or silently migrate records.
- Acceptance: Shared-guard changes retain the existing protected coverage of role, Template and setup actions as well as the five affected workflow families. Reusable changes, registered Template updates, root adoption and existing-product adoption have separately identified file and authority boundaries.
- Depends on: None.

### REQ-011 — Verify scalability and safeguards together
- Requirement: Acceptance evidence shall compare representative complete operations as unrelated history grows and demonstrate preserved integrity, concurrency and recovery behavior alongside resource measurements.
- Source: U01 and U02; S01 recommendation 5 and its measurement limitations; S04 verification standard.
- Acceptance: Evidence includes many small files, a few large files, duplicate evidence, concurrent unrelated Tasks, relevant content changes and interrupted transactions, with recorded workload sizes, environment and measurement conditions.
- Acceptance: Fixed-dependency comparisons satisfy REQ-003 and report complete-operation latency, bytes hashed, peak memory and lock duration. Relevant tampering, stale authority, unauthorized targets and recovery failures still reject correctly, while historical access and audit cases satisfy the user-selected detection timing.
- Acceptance: The report distinguishes inspected contracts, deterministic fixtures and observed native or end-to-end behavior. It does not infer a scalability result from snapshot timings or a raised ceiling alone.
- Depends on: REQ-003, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010

## Decisions

- Integrity timing is settled by U02. Immediate verification covers the current operation's complete dependencies. Historical evidence is verified when consumed; separate archive audits may discover unrelated damage later. This changes the timing of unrelated archive detection, not the validity required for evidence being used now.
- S01's order of work remains a planning proposal: improve bounded reading and diagnostics, establish complete operation dependencies, then consider historical manifests and incremental indexing. Any narrower locking follows explicit shared-invariant analysis and representative evidence.
- Numeric capacities, chunk sizes, time budgets, manifest layout, content-addressed storage, deduplication, cache invalidation mechanisms, database choice and lock granularity remain implementation choices within these requirements. The reported 128 MiB setting is existing relief, not a final scalability target. SQLite is an optional proposal and introduces no installation authority.
- Scalability acceptance uses fixed-operation and fixed-dependency comparisons against growing unrelated history. This supplies an observable outcome without inventing a latency target or selecting a database. Relevant dependency growth and complete archive audits still consume real verification work.
- The initial canonical JSON and Markdown formats, identities and approval meanings remain authoritative. A future migration or dependency installation requires its own explicit authority; a document approval does not supply it.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
