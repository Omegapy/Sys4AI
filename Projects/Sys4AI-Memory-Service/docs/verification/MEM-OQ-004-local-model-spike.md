# MEM-OQ-004 local-model evidence spike

Status: approved local profile runtime-verified  
Measured: 2026-09-03  
Profile: Ollama 0.33.2 `llama3.1:8b` plus FastEmbed
`sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions

## Outcome

The approved LLM and embedding artifacts were placed in product-local ignored
model directories and exercised without cloud fallback. The original LLM smoke
returned exactly `LOCAL_OK`. A later offline FastEmbed run produced one finite
384-dimensional vector, and a bounded real Cognee 1.5.3 integration run stored
semantic and relational representations and recalled a public Sys4AI record
through the provider-neutral adapter.

| Measure | Observed |
|---|---:|
| LLM | `llama3.1:8b` |
| Ollama model ID | `46e0c10c039e` |
| Reported LLM size | 4.9 GB |
| Architecture / quantization | Llama 8.0B / Q4_K_M |
| Context length | 131,072 tokens |
| Cold LLM request total | 2.573 s |
| Model load | 2.343 s |
| Prompt evaluation | 20 tokens in 0.207 s |
| Generation | 3 tokens in 0.021 s, about 94.3 tokens/s |
| FastEmbed cache | `models/fastembed`, 12 files, about 87 MB |
| Embedding result | one finite vector, 384 dimensions, offline socket denial active |
| Cognee initialization | 1.657 s |
| Cognee remember | 11.132 s for two records and one typed relation |
| Cognee recall | 0.049 s; returned `mem_BETA` with one evidence candidate |

The server was started with:

- `OLLAMA_HOST=127.0.0.1:11434`;
- `OLLAMA_NO_CLOUD=1`;
- `OLLAMA_NOHISTORY=1`; and
- `OLLAMA_MODELS=<product-root>/models/ollama`.

The integrated run also used `HF_HUB_OFFLINE=1`,
`TRANSFORMERS_OFFLINE=1`, disabled Cognee telemetry/tracing/caching, and
observed only `127.0.0.1`, `::1`, or `localhost` connections to the explicitly
allowed Ollama port. No non-loopback connection attempt occurred. Cognee stored
Sys4AI external metadata in its project-confined relational database; the
adapter rejoined a CHUNKS result by stable data/document ID so public callers
retained the typed record and source anchor after the provider call.

The repeatable opt-in check is:

```bash
SYS4AI_RUN_LOCAL_COGNEE=1 uv run --frozen pytest -q \
  tests/providers/test_cognee.py::test_approved_local_cognee_profile_creates_and_recalls_real_representations
```

It requires the approved Ollama model on loopback, queries the real graph for
non-empty nodes and edges, rejects every non-loopback socket destination, and
removes its product-local disposable provider root. The final run passed in
17.41 seconds with upstream deprecation warnings only. The daemon was then
stopped; an independent port check found no TCP listener on 11434.

## Security observation

The Ollama runtime does not authenticate its local HTTP API, and the underlying
local runner emitted a broad-CORS/no-key warning. The approved posture therefore
keeps the memory service in-process with no listener, binds any bounded model
daemon to loopback only, and requires authenticated exposure for any future
networked memory-service profile.

On the first attempted daemon startup, Ollama created its normal private-key
file outside the product at `~/.ollama/id_ed25519`. The Project Director stopped
that first daemon before any model pull or inference, did not inspect, copy, or
delete the key, and repeated the spike with cloud disabled. This external side
effect remains visible to the operator; it is not product evidence or a
credential approved for service use.

## Scope and remaining evidence

This evidence establishes the approved local model pairing, offline embedding
cache, real Cognee semantic remember/recall, stable metadata rejoin, and creation
of native relational/graph representations on the reference machine. It does
not establish:

- sustained throughput, concurrency, long-context behavior, or memory limits;
- license acceptance for distribution or redistribution; or
- a networked or shared production deployment.

Model downloads remain excluded from source registration and Git. Configuration
load is side-effect free and never starts Ollama, Cognee, or a download.
Semantic, graph, and temporal capability is approved only for the configured
local profile after explicit initialization; no cloud fallback is allowed.

## Decision

The user approved `llama3.1:8b` with FastEmbed
`sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions on 2026-09-03. This
document records technical evidence; the authority and exact exclusions remain
in the decision register. Model redistribution, product Git, publication, and
deployment are not authorized by this decision.
