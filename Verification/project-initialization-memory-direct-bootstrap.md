# Direct bootstrap verification

The installed `sys4ai-memory init-memory` command and `MemoryClient.initialize` now use the shared initialization preflight/storage core. The existing root `init preview` and digest-bound `init apply` routes share that core. Direct receipts contain no preview object or impact digest.

The new LocalMemoryRuntime loads project-local configuration, complete registry/profile declarations and canonical permissions, then persists exact indexing and synchronization state across command processes. Exact-only consumers use base@1 and report provider/model activation as deferred.

The delegated focused suite passed **89 tests** across initialization, interfaces, CLI, service and local runtime; the Director inspected service/runtime code and independently exercised an immutable installed wheel. The rebuilt wheel passed `tests/test_local_runtime.py::test_real_cli_initializes_and_reopens_exact_state_across_processes` using `SYS4AI_MEMORY_TEST_EXECUTABLE=/private/tmp/sys4ai-intermediate-consumer-venv/bin/sys4ai-memory`: direct init, sync, exact recall, then repeat sync.

Failure injection covers directory creation, SQLite, provider callback and receipt publication. No success receipt is published on failure; incomplete initialization is retryable. Rebinding an initialized directory, changing its configuration or using a malformed receipt fails before reopening its state. Side-effect-free validation covers authorization, identity, secrets, exclusions and path boundaries.

This intermediate wheel verifies the executable; the later governed artifact build will record locked dependencies and final source provenance.

Intermediate wheel SHA-256: `31fa9f85028a881e8d01d002bd5bf07d2742941f73bd5e79d2c27ea69caca59d`.
