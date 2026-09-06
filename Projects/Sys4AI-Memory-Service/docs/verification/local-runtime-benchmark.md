# Local runtime performance benchmark

Status: component measurements complete; real-profile limits explicitly bounded  
Measured: 2026-09-04  
Benchmark: `sys4ai-local-runtime-synthetic-v1`

## Outcome

The benchmark measured local components with synthetic, non-sensitive data in
disposable storage. Every maintained 20-sample p95 was below its numeric PRD
threshold. A separate one-sample stress run also loaded the full
100,000-fragment and 1,000,000-relation target and exercised indexed one-hop
hybrid recall.

After the model decision, a bounded real-profile run added a two-record,
one-relation Cognee lower limit: initialization 1.657 seconds, semantic remember
11.132 seconds, and recall 0.049 seconds. That small run verifies the profile
path but does not turn the component scale measurements into a real Cognee
scale claim. `MEM-NFR-013` through `MEM-NFR-015` therefore remain implemented
but unverified at complete-profile scale. `MEM-NFR-017` is runtime-verified
under its explicit measured-lower-limit alternative.

| Requirement | Measured path | Samples | p50 | p95 | Maximum | Numeric target | Result boundary |
|---|---|---:|---:|---:|---:|---:|---|
| `MEM-NFR-013` | Guarded in-process hybrid recall over 100,000 fragments and 100,000 relations | 20 | 1,326.892 ms | 2,291.999 ms | 2,337.205 ms | p95 <= 3,000 ms | Measured path was within target; real Cognee hybrid recall was not measured. |
| `MEM-NFR-014` | Configuration load, existing SQLite open/health, service construction, and authorized health | 20 | 49.539 ms | 49.869 ms | 50.032 ms | startup <= 15,000 ms | Measured path was within target; no process bootstrap or provider database was started. |
| `MEM-NFR-015` | One changed 120-byte text source through guarded dispatch, discovery, normalization, SQLite update, and in-memory provider write | 20 | 266.282 ms | 274.593 ms | 276.829 ms | p95 <= 10,000 ms | Measured path was within target; real Cognee synchronization was not measured. |
| `MEM-NFR-017` | Load 100,000 deterministic relations into the in-memory conformance provider in 10 batches | 10 batches | 171.182 ms | 1,045.781 ms | 1,045.781 ms | 1,000,000 relations or a measured lower limit | The maintained run publishes a 100,000-relation component lower limit; the supplemental stress run reaches the full numeric count. |

The maintained relation batches completed in 3.246 seconds total. Hybrid
recall used an endpoint relation index and did not scan every stored relation.
Corpus normalization, SQLite indexing, provider search-index construction, and
in-memory provider loading took 58.649 seconds; that build time is not part of
the recall latency samples.

## Environment and corpus

| Property | Observed value |
|---|---|
| Measurement timestamp | `2026-09-04T02:44:22.003808Z` |
| Workstation | Apple-silicon Mac Studio, 96 GB physical memory |
| Platform | macOS 26.6.2, arm64 |
| Logical CPUs | 28 |
| Python | 3.12.11 |
| SQLite | 3.49.1 with FTS5 |
| Peak benchmark-process resident set | 2,142.672 MB |
| Exact database files | 1,312,642,792 bytes in the disposable root |
| Fragment corpus | 100,000 JSONL rows plus 100 source-artifact records |
| Provider corpus | Same normalized records in `InMemoryProvider` |
| Relation corpus | 100,000 deterministic `REFERENCES` relations |
| Timed source change | One synthetic text file, at most 120 bytes |
| Corpus recipe SHA-256 | `6c1775f1ba10962cde3d328246d5a168369663ca7ee3564980b10e87a537f9e6` |

The benchmark used a deterministic stride across the fragment IDs. It used
three warmup calls before the hybrid-recall, startup, and incremental-sync
latency series. The p95 is the nearest-rank value after sorting the recorded
wall-clock samples. Temporary configuration, permission, source, SQLite, and
provider state was removed when the command finished.

## Reproduction

Run from the product root with the locked environment:

```text
uv run --frozen python tools/benchmark_local_runtime.py \
  --fragments 100000 \
  --batch-size 1000 \
  --relations 100000 \
  --relation-batch-size 10000 \
  --recall-samples 20 \
  --startup-samples 20 \
  --sync-samples 20 \
  --warmups 3
```

The command writes its result as JSON to standard output. It does not retain a
database or result file. The focused smoke test uses a smaller corpus:

```text
uv run --frozen pytest -q tests/benchmark/test_local_runtime_benchmark.py
```

The full-count supplemental stress command was:

```text
uv run --frozen python tools/benchmark_local_runtime.py \
  --fragments 100000 \
  --batch-size 1000 \
  --relations 1000000 \
  --relation-batch-size 25000 \
  --recall-samples 1 \
  --startup-samples 1 \
  --sync-samples 1 \
  --warmups 0
```

That run completed at `2026-09-04T02:42:09.766516Z` with recipe SHA-256
`ba5bf82ed7d57f662320c5c7c201a3baa8c06e7359147f99339ba143d42f0482`.
It loaded 1,000,000 relations in 38.399 seconds, used 5,618.219 MB peak
resident memory, and completed its single indexed hybrid recall in 1,354.589
ms. A single sample is capacity evidence, not a p95 measurement.

## Measurement boundaries

### Hybrid recall

The timed path begins at `MemoryService.dispatch`. It includes canonical
permission-file reads, configuration gates, audit and metrics capture,
`RetrievalEngine.recall_with_trace`, SQLite exact and lexical lookup, and
in-memory provider semantic, graph, and temporal scoring. Provider search text
and normalized token sets are built on mutation, and graph expansion uses an
endpoint index with a one-hop bound. The trace confirmed all five planned
channels for every sample.

`InMemoryProvider` implements deterministic token-overlap and relation
behavior for conformance tests. It is not Cognee, does not run an embedding or
LLM, and does not establish semantic quality. The result is useful local
orchestration evidence for `MEM-NFR-013`, but it is not a service-level
guarantee or real-provider scale acceptance evidence.

### Guarded startup

Each timed sample reloads and validates a disposable active benchmark
configuration, constructs canonical authorization, opens and checks the
existing 100,100-record SQLite database, constructs an exact-only retrieval
engine and `MemoryService`, and completes an authorized health call. The timer
stops before database close.

The maintained run does not measure an executable process bootstrap, listener, Cognee
import or initialization, provider database reopen, model connection, or
readiness of a complete approved local profile. Operating-system filesystem
caches were warm after three warmups. `MEM-NFR-014` remains unverified until
that complete startup path is measured repeatedly, despite the separate
1.657-second small-corpus Cognee initialization.

### Incremental synchronization

Each sample changes exactly one small source before timing. The timed path
starts at `MemoryService.dispatch` and covers canonical authorization,
configuration gates, source discovery, secret scanning, normalization,
deterministic record revision assignment, manifest and checkpoint comparison,
the transactional SQLite update, in-memory provider write, audit, operation
tracking, and receipt generation. An exact lookup after each sample verifies
the new revision.

The 100,000-fragment and 100,000-relation corpus was already loaded when these
samples ran. This is integrated local service evidence, but the provider was
the in-memory conformance implementation. No Cognee database or embedding model
participated in these 20 samples, so `MEM-NFR-015` remains unverified; the
separate real remember sample exceeded 10 seconds and is not a complete
incremental-sync measurement.

### Capacity

The maintained run demonstrates 100,000 normalized fragments in both the
temporary SQLite exact index and the in-memory conformance provider plus
100,000 endpoint-indexed relations. The supplemental stress run demonstrates
the same fragment count and the full 1,000,000-relation numeric target, with a
single successful indexed hybrid recall. Neither scale run measures a
persistent Cognee graph database, provider recovery, or concurrent clients.
The published real-profile lower limit is two records and one relation; the
100,000/1,000,000 result remains conformance-provider capacity evidence.

## Strict limitations

- The benchmark creates a temporary active configuration solely to exercise
  guarded code paths. It does not modify tracked configuration or resolve a
  product decision.
- No Ollama process, model, Cognee runtime, network listener, remote endpoint,
  credential, tracked canonical source, or product memory directory was opened
  or changed. The in-memory conformance provider is an in-process test object.
- Measurements come from one local run without CPU affinity, thermal control,
  background-load isolation, or an independent rerun. They are reproducible
  measurements, not production guarantees.
- Hybrid samples use deterministic token and relation fixtures. They do not
  measure embedding quality, graph extraction, model latency, or real Cognee
  storage behavior.
- The startup result is a service-shell and exact-database measurement, not a
  deployable local-service startup measurement.
- The sync result uses the in-memory conformance provider rather than Cognee.
  The full-count capacity result is a one-sample stress run, not a sustained
  service or persistent-provider measurement.
- At the time of this benchmark, the release ledger and tracked decisions were
  not changed. The later decision/evidence reconciliation supersedes that
  historical ledger statement without changing the measurements.

The existing [exact-index evidence spike](MEM-OQ-005-exact-index-spike.md)
retains the independent 100,000-fragment exact-lookup measurement. The
[local-model evidence spike](MEM-OQ-004-local-model-spike.md) remains the
separate real-profile evidence; no model was started for this synthetic scale
benchmark.
