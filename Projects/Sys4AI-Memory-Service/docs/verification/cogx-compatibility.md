# Cognee initialization and COGX compatibility probe

Date: 2026-09-03  
Python: 3.12.11  
Cognee: 1.5.3  
COGX archive version: 0.1

## Observed result

The pinned Cognee distribution passed the focused compatibility probe:

```bash
uv run --frozen pytest -q \
  tests/providers/test_cognee.py::test_pinned_distribution_provider_initialization_and_cogx_archive_are_compatible
```

The test loads the real installed Cognee package only after the adapter's
temporary hardened environment is active. Through the public provider
initialization boundary it creates Cognee's real 30-table relational SQLite
database and verifies representative Cognee tables plus confinement of the
database, data, system, cache, and log paths to a temporary project-derived
root. It then verifies the public export signature, writes two native COGX
entities and one native fact, reads the manifest and records back, and streams
the same archive through Cognee's `COGXArchiveSource`. The probe also verifies
omitted permissions, byte-independent typed record equality, no socket
connection attempts, and restoration of the host environment.

The adapter tests separately exercise the authorized, path-confined, two-phase
COGX export and import calls through the provider-neutral Sys4AI contract using
an injected deterministic runtime. Together these checks establish the first
real Cognee provider integration and prove that the adapter's COGX call shape
and Cognee 1.5.3 native archive API are compatible at this boundary.

## Compatibility corrections found by the probe

- Cognee 1.5.3 exposes data-root and system-root setters, but not a cache-root
  setter. The adapter now sets the cache root before import through
  `CACHE_ROOT_DIRECTORY` and calls only the two supported setters.
- Cognee validates an Ollama configuration as a complete model, endpoint, and
  key triple during import. The adapter supplies a temporary non-secret local
  placeholder; it is not persisted and Ollama does not authenticate it.
- LiteLLM otherwise attempts to refresh its model-cost map at import. The
  adapter temporarily sets `LITELLM_LOCAL_MODEL_COST_MAP=True`, and the test
  fails on any socket connection attempt.

## Deliberate boundary

This document is real-library, relational-database-initialization, and native-
archive compatibility evidence. The separate
[local-model spike](MEM-OQ-004-local-model-spike.md) now covers bounded real
graph/vector population, local LLM/embedding use, semantic recall, and stable
metadata rejoin. The [age package evidence](age-encrypted-package.md) covers
the approved provider-neutral encrypted format. Populated-dataset native COGX
export/import, provider storage migration, model-quality evaluation, full-scale
Cognee performance, and deployed-service operation remain outside these probes.
