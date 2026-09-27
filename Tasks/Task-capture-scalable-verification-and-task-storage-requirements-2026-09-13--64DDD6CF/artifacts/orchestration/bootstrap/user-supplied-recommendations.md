**My recommendation is to make verification scale with the operation’s dependencies, while allowing the project’s history to grow independently.** Increasing the byte limit is useful relief, but repeated whole-history scans are the underlying problem.

The active installation now uses **128 MiB**, and I verified that its engine matches the configured bootstrap hashes. That changed since my first answer.

I examined the guard, Task transactions, existing capacity tests, and Curator’s scanning code, then researched comparable approaches in Bazel, Git, Watchman, and SQLite.

The current project measurements are revealing:

| Observation | Measured result |
|---|---:|
| Base guard context | 63.95 MiB |
| Content in Task folders | 63.53 MiB |
| One cancelled Task’s share | 60.04 MiB — 94.5% |
| All 26 canonical `task.json` files combined | 1.74 MiB |
| Duplicate artifact content | 13.97 MiB — about 23% |
| One complete Task snapshot | 0.286–0.295 seconds |

Those timings are repeated local snapshot measurements, not complete transaction timings or cold-disk benchmarks.

The guard includes the entire Task tree in its context and rereads it for target and freshness checks. Separately, the Task helper validates the whole catalog and takes a catalog-wide writer lock. Thus, there are **three scaling issues: bytes scanned, repeated validation, and serialized writes**. Simply raising `MAX_BYTES` addresses only the first ceiling. Sources: [guard context](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/scripts/ontology_guards.py:400), [catalog scanning](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/agent-task/scripts/task_state.py:1257), [transaction locking](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/agent-task/scripts/task_state.py:2042).

I recommend the following order.

1. **Keep 128 MiB as immediate relief, and improve how limits work.**

   The current scanner reads each entire file before checking the accumulated byte limit, and builds a sorted recursive listing before enforcing the entry limit. Therefore, these limits do not reliably bound peak memory or enumeration work.

   Change it to hash files in chunks, enforce budgets during traversal and reading, and report bytes scanned, file count, elapsed time, and the largest contributors. Separate limits for request size, memory buffers, verification time, and retained storage. A project archive should not inherit the same limit as an individual operation.

   I would benchmark larger settings before choosing 256 MiB or 1 GiB. The existing 10,000-entry ceiling and five-second decision budget would still need consideration. [Current scanner](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/ontology/scripts/ontology_guards.py:255).

2. **Make each operation declare its complete read and write dependencies. This is the highest-value change.**

   For a planning artifact registration, verify the selected Task, referenced evidence, governing rules, current owner/generation, and relevant cross-Task constraints. Preserve catalog-wide checks where the operation actually needs uniqueness, parent relationships, or shared ownership.

   The owning helper should determine these dependencies; a caller should not be allowed to omit inconvenient files.

   Bazel tackles the analogous problem by recording dependencies and invalidating only affected computations. Its documentation specifically warns that undeclared reads produce incorrect incremental results. That is the central lesson for this guard: **reduce scope by proving dependencies, not by skipping arbitrary directories**. [Bazel Skyframe](https://bazel.build/reference/skyframe).

   Apply this across Task, plan, TRD, memory, and ontology operations. Changing only the Task adapter would leave the shared context scan in place.

3. **Separate active verification from historical evidence storage.**

   Preserve historical artifacts, but represent sealed evidence with manifests containing paths, sizes, and content hashes. Verify referenced content when it is consumed, and provide a separate complete archive-integrity audit.

   Git stores content-addressed objects and trees; Bazel separates action metadata from content-addressed file storage. Those patterns fit the project’s existing SHA-256 evidence references. Deduplication could also recover roughly 14 MiB in the current artifact collection, although that alone is a secondary improvement. [Git objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects), [Bazel caching](https://bazel.build/remote/caching).

   **There is an explicit tradeoff:** an old manifest cannot prove that arbitrary mutable files remain unchanged. Immediate detection of every out-of-band edit throughout the archive requires rereading it or a trustworthy storage/change-tracking mechanism. Separating archive audits from transaction checks changes when unrelated historical damage is detected; that should be a deliberate contract decision.

4. **Add incremental indexing carefully, after dependencies are explicit.**

   Reuse verified content hashes and parsed metadata when their inputs remain valid. Keep current authorization, ownership, revisions, and commit-time checks live.

   File timestamps and watcher notifications are useful hints, but insufficient proof by themselves. Git documents same-size, rapid-edit races; Watchman must rescan after losing filesystem events, including on macOS. [Git’s race handling](https://git-scm.com/docs/racy-git), [Watchman recovery](https://facebook.github.io/watchman/docs/troubleshooting).

   A rebuildable SQLite index is a reasonable later option if catalog scanning remains expensive. Initially, preserve canonical JSON/Markdown and make index failure recoverable through existing readers. SQLite provides transactional snapshots, but still permits only one writer at a time; adopting it alone would not solve write concurrency. [SQLite isolation](https://www.sqlite.org/isolation.html).

5. **Prove scalability with representative workloads before changing lock scope.**

   Test growing archives independently from active work: many small files, a few large files, duplicate evidence, concurrent unrelated Tasks, and interrupted transactions. Measure complete-operation latency, bytes hashed, peak memory, and lock duration.

   The acceptance target should be: **adding unrelated historical evidence does not materially increase a small operation’s verification work**, while relevant content changes, stale ownership, unauthorized targets, and recovery failures still block correctly.

I would implement streaming and diagnostics first, then operation-specific dependencies, then historical manifests and indexing. Narrower locking should come last, after shared catalog invariants are explicit. The project already has a useful bounded-streaming pattern in [Curator’s metadata scanner](/Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/curate/scripts/curator_git.py:98).

This was research and read-only measurement; I made no implementation changes. The proposed performance gains still require representative end-to-end testing.