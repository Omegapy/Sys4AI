# Basic Memory isolated operating evidence

The tested isolated profile passes its compatibility checks. This is the worker's
fixture result; the Director owns the active-root pilot and enablement decision.
The result is bound to profile SHA256
`c3d33e44260654427bfa32fdc6c346e78cb78e4fb64e0d45830fed0a148bcf17`
and adapter SHA256
`1f0a625bd6a3462bb6074caa9c0d291df315ccb0e42c7554f971a2c8ac9d3482`.
The [assessment](backend-isolated-assessment.json) contains the exact evidence
hashes and requirement/task boundary.

Basic Memory 0.23.0 uses Python 3.12.13 in `.venv-memory-pilot`. All 165 runtime
package artifacts and two source-build tools were pinned before installation.
`pip check` passed. The lock deliberately includes vendor-required prerelease
FastMCP 4.0.0b1. Root `.venv` retains pip 26.0 and PyMuPDF 1.28.2; no backend
package was installed there. PDF extraction was tested in that root interpreter,
with vendor execution in the separate pilot interpreter.

The local FastEmbed 0.8.0 model is `bge-small-en-v1.5`, backed by Qdrant's quantized
ONNX revision `52398278842ec682c6f32300af41344b1c0b0bb2`. All model files are
verified by SHA256 and length. The model has 384 dimensions; the selected runtime
uses two embedding threads and one process. No paid provider, cloud route, or
host-wide MCP server was used or registered.

The [Basic Memory release metadata](https://pypi.org/pypi/basic-memory/0.23.0/json)
and bundled license identify AGPL-3.0-or-later. The original BAAI model card and
FastEmbed registry identify MIT, while the pinned Qdrant conversion
[model card](https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q/blob/52398278842ec682c6f32300af41344b1c0b0bb2/README.md)
identifies Apache-2.0. The profile retains these separate observations. This local
use review does not evaluate redistribution or hosted-service obligations.

| Observed quantity | Result |
| --- | --- |
| Host | Apple M3 Ultra, 28 physical/logical cores, 96 GiB memory |
| Installed pilot regular-file bytes | 468,134,480 |
| Downloaded package artifacts including build tools | 98,896,039 bytes |
| Selected model artifacts | 67,412,850 bytes |
| Two main fixture corpora | 9 documents and 9 ready vector rows each |
| PDF fixture corpus | 10 documents |
| Main fixture index subprocess times | 1.320 and 1.259 seconds |
| Query subprocess time, 20 actual queries | 0.635–0.892 seconds; mean 0.787 seconds |
| Maximum query-worker RSS | 354,942,976 bytes |
| Maximum index-worker RSS | 351,518,720 bytes |

Timing uses monotonic `perf_counter`; peak RSS uses macOS
`getrusage(RUSAGE_SELF).ru_maxrss`. Each query starts a fresh constrained process.
Repeated runs benefit from the filesystem cache; an OS-cold disk run and a
persistent warm worker were not tested. The subprocess timings exclude parent
normalization and integrity checks. Final main/PDF/special-path fixture starts
ran concurrently. These are small-corpus observations, not throughput guarantees.
Disk figures sum regular file lengths and exclude filesystem allocation overhead.
The [resource record](backend-resources.json) preserves the measurement details.

The actual backend returned the expected source for exact identifiers and
conceptual heat-removal queries. Hybrid search can also return weakly related
local memories when an identifier is absent. Exact text retrieval remains the
appropriate no-match check, and ranking does not establish truth. PDF results
retain their source hash and page locator. TeX and HTML extraction limitations
remain visible. All five canonical record types retain exact metadata and ISO
chronology in the projection and vendor `sys4ai_metadata`. Vendor ORM timestamp
columns use local wall time; public meaning and applicability use canonical data.

Twenty fault inspections preserved all inspected file bytes and modification
times. Cases covered wrong project/configuration, unsafe aliases, altered profile
and projection, retraction, stale sources, missing index/model, disabled backend,
writer and canonical-target attempts, and frozen input changes. A broader actual
index containing a new note and a sibling source copy could not expand the
source-only frozen packet. A real vendor process was terminated after staged
database creation; explicit recovery retained canonical files and restored
hybrid lookup. A directory containing `?`, space and `#` was indexed and queried
at the exact declared path, with no truncated outside database created.

The adapter uses fixed repository calls, an explicit project binding, immutable
read-only SQLite connections, verified local models, and Python network/write
checks. Normal vendor startup, automatic updates, frontmatter synchronization,
formatting, watchers, model repair and unrestricted writer tools are absent from
the query interface. These application controls are not an OS sandbox.

The source-only packet fixture does not prove native solver independence or
manager activation. The Director tightened curated packet eligibility while
final evidence was being recorded; the exact before/after shared-module hashes
and the unaffected source-only path are recorded in
[preservation evidence](backend-preservation.json). The owned backend source
files stayed fixed during the final runtime checks.

Active-root measurements and native end-to-end evidence remain with the Director.
Root semantic flags must remain conditional on those gates. Enabling flags changes
the configuration digest and requires a new authorized certificate/reindex before
claiming enabled behavior. No existing-product, other-platform, future-host,
Git/publication or deployment behavior is claimed here.
