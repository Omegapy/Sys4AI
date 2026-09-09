# State ownership and maintenance

Canonical records live in `MEMORY/`; project configuration lives in
`memory.yaml`. Both are portable project-owned source files. Reusable contracts
are installed at `reference-assets/MEMORY-depo/` and are not learned memory.

| Project-relative path | Classification | Recovery rule |
| --- | --- | --- |
| `.sys4ai/memory/projection/` | Derived permitted corpus | Rebuild only listed products from current canonical sources. |
| `.sys4ai/memory/normalized/` | Derived source extraction | Each product binds a raw source digest and extractor version. Unknown files are preserved. |
| `.sys4ai/memory/index/` | Derived local backend database | Rebuild explicitly; stale or absent state makes public lookup fall back. |
| `.sys4ai/memory/model-cache/` | Reproducible pinned model artifacts | Provision only through the authorized local pilot; reads never download. |
| `.sys4ai/memory/backend-config/` | Durable local backend configuration and certification | Preserve and back up separately; it is not a disposable retrieval cache. |
| `.sys4ai/memory/maintenance/` | Durable memory transaction journals, receipts and locks | Reconcile accepted writes before cleanup. Never discard sole-copy accepted content. |

An ignore rule means local storage, not permission to delete. Reindex and cleanup
must validate the exact declared product manifest and reject unknown, changed or
durable content. A write requires the current scoped maintenance grant and lock.
The normalization library's `build_normalized` is an internal primitive called
only after that gate. Public search extracts current permitted sources into
process memory and reports stale saved products without modifying them.

Memory maintenance never touches `.sys4ai/template-update/`, role transition or
case-rename records, Task transactions, project setup receipts, unrelated caches,
other projects or canonical notes. Publication recovery operates only on its
exact attributable memory journal. A pending journal is not a retrieval source.

Sensitive-data correction needs an exact scoped grant, current versions and a
reason. Preserve history where appropriate, while removing sensitive originals
from affected recovery copies under that same explicit redaction scope. Do not
perform automatic record/schema migrations or retain credentials as audit evidence.
