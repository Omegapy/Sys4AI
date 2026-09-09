# Pinned Basic Memory pilot

This specification binds PLAN-20260908-5F47ADB2 TASK-004 and the isolated portions
of TASK-039/040/042. The current implementation request and the Director's bounded
delegation authorize this project-local provisioning. No global installation,
host MCP registration, hosted provider, or existing product adoption is included.

The frozen profile is `MEMORY-depo/profiles/basic-memory-v0.23.0.json`, SHA256
`c3d33e44260654427bfa32fdc6c346e78cb78e4fb64e0d45830fed0a148bcf17`.
The 165-package requirements lock has SHA256
`abffb537fe96fadc8f21a690b675a796445073cc1233ad69bad89f9c7df2004d`.
Both hashes were resolved and reviewed before installation. The runtime is Python
3.12 on macOS arm64 in `.venv-memory-pilot`; root `.venv` is preserved.
Two source-only legacy dependencies use separately frozen setuptools 80.9.0 and
wheel 0.45.1, with build isolation disabled. The Basic Memory dependency contract
requires the prerelease `fastmcp==4.0.0b1`; this is an explicit lock dependency.

Basic Memory 0.23.0 wheel SHA256 is
`196ac1ff9ace9df51f1131dcad4d4f1f7d3f65dd5fbfa08bb4819f5f2c486a5e`.
Primary metadata: [PyPI release](https://pypi.org/pypi/basic-memory/0.23.0/json),
[tagged source](https://github.com/basicmachines-co/basic-memory/tree/v0.23.0).
The package code identifies AGPL-3.0-or-later; its exact license is retained in
the downloaded wheel. This local pilot does not assess redistribution or hosted
service deployment obligations.

FastEmbed 0.8.0 maps `BAAI/bge-small-en-v1.5` to
`Qdrant/bge-small-en-v1.5-onnx-Q` revision
`52398278842ec682c6f32300af41344b1c0b0bb2`. The immutable ONNX weight SHA256 is
`51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431`.
The complete selected model files total 67,412,850 bytes (64.3 MiB). Every file's
URL, byte length, and hash is frozen. The conversion's [model card](https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q/blob/52398278842ec682c6f32300af41344b1c0b0bb2/README.md)
labels Apache-2.0, while the original BAAI card and FastEmbed registry label MIT.
This difference is recorded rather than flattened into one asserted license.
Installed package size and RSS are unknown until measured. No cloud payment is
needed for the selected local API; no paid API is used.

The adapter uses the exact release's `SQLiteSearchRepository`, `SearchIndexRow`,
and `FastEmbedEmbeddingProvider` APIs. Query mode maps `text` to vendor `fts`;
`vector` and `hybrid` keep their vendor meanings. An injected local provider loads
only the verified model directory using `specific_model_path` and
`local_files_only=True`. It disables automatic corrupt-cache repair.

Normal `ConfigManager`, CLI, MCP, server startup, sync, watch, and vendor writer
tools are never called by public inspection. Source inspection found that
ConfigManager creates/chmods directories, semantic search lazily executes schema
DDL, and the default embedding provider can download or purge model caches.
The fixed query subprocess uses `mode=ro&immutable=1`, `query_only=ON`, no inherited
API credentials, offline Hugging Face settings, and Python write/network checks.
Existing schema no-ops are permitted; attempted database writes must fail.
These application controls are not an operating-system sandbox.

Canonical `MEMORY/` and permitted sources supply metadata and result content.
Backend content is a disposable projection; backend metadata never flows back to
canonical records. `modified` maps directly from canonical `modified`; sources
without an authoritative timestamp use a neutral epoch, not filesystem recency.

Each fixture owns separate `.sys4ai/memory/projection`, `index`, `backend-config`,
`normalized`, `model-cache`, and durable `maintenance` paths. Reindex requires an
exact current grant and shared memory lock. It stages replacement products,
records hashes and effective controls, and retains recovery evidence on failure.
Unknown files block replacement. No inspection performs this operation.

The frozen query matrix covers exact identifiers, conceptual heat removal,
wrong projects, paths/aliases, draft/candidate sentinels, metadata preservation,
stale sources, frozen packets, attempted writer operations, interrupted rebuilds,
unknown state, and outage. Results must distinguish deterministic contracts,
real vendor observations, the isolated fixture, and the active root. Root
indexing waits for host adoption and all isolated safety gates. Any failed or
unexercised mandatory gate leaves persistent root semantic use disabled.
