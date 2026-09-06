# MEM-OQ-005 exact-index evidence spike

Status: approved and benchmark-verified  
Measured: 2026-09-03  
Candidate: embedded SQLite exact tables plus FTS5 lexical search

## Outcome

The implemented SQLite/FTS5 candidate passed the functional exact, lexical,
project-isolation, current/history, rollback, and hydration suites. On the
reference Apple-silicon Mac Studio with 96 GB memory, a disposable in-memory
100,000-fragment corpus plus 100 source-artifact records produced these
observed results using the checked-in benchmark command:

| Measure | Observed | PRD target |
|---|---:|---:|
| Build and normalization time | 31.749 s | No fixed target |
| Exact lookup p50, 200 samples | 136.638 ms | Informational |
| Exact lookup p95, 200 samples | 137.797 ms | <= 500 ms |
| Exact lookup maximum | 139.807 ms | Informational |
| Lexical phrase p95, 100 samples | 7.231 ms | Informational |
| Lexical phrase maximum | 40.464 ms | Informational |

The benchmark used the public JSONL normalization and `ExactIndex` write/query
paths. It ran with Python 3.12.11 and SQLite 3.49.1 on arm64 macOS. It did not
measure persistent-disk startup, concurrent mixed traffic, semantic recall, or
a real Cognee store. It created no product data files.

An independent fresh rerun during the traceability audit reproduced the result
on the same 100,000-fragment plus 100-source-artifact corpus: build and
normalization took 32.142 seconds; exact p50/p95/maximum were
137.858/139.579/142.909 milliseconds across 200 samples; and lexical
p50/p95/maximum were 6.948/7.292/41.007 milliseconds across 100 samples. Both
runs met the exact p95 target. The rerun used Python 3.12.11, SQLite 3.49.1,
and arm64 macOS, and likewise used a disposable in-memory database.

The first attempt exposed redundant per-record cleanup on new rows and was
stopped safely at 80,000 records after roughly 21 minutes. After removing that
unnecessary path and batching exact-term inserts, a fresh reproducible
100,000-fragment build and normalization pass completed in 31.749 seconds.
Focused ingestion/exact tests remained green.

Reproduction command:

```text
.venv/bin/python tools/benchmark_exact_index.py --fragments 100000 --batch-size 1000 --exact-samples 200
```

## Option assessment

| Option | Assessment |
|---|---|
| SQLite exact tables plus FTS5 | Meets deterministic exact/lexical, metadata, lifecycle, generation, rollback, and observed 100k p95 requirements. |
| Cognee/provider search alone | Cannot satisfy the independent exact-channel or no-LLM exact-only requirements and remains provider-coupled. |
| `rg` canonical search alone | Valuable for canonical verification and diagnostics, but it lacks typed lifecycle, provenance, ranking, generation, and service-index behavior. |
| Composed implementation | SQLite/FTS5 as the service index, followed by canonical-source reread for execution-critical results; `rg` remains an operator diagnostic fallback. |

## Decision

The approved composed implementation uses embedded SQLite exact tables and FTS5 as
the Stage 1 exact/lexical backend, while canonical source reread remains the
execution authority. Do not use Cognee as the exact backend and do not treat an
index hit as current permission or Task-state proof.

The user approved `MEM-OQ-005` / `Q-005` on 2026-09-03. This document remains
the technical evidence for that decision; `rg` is an operator diagnostic
fallback rather than an authority source.
