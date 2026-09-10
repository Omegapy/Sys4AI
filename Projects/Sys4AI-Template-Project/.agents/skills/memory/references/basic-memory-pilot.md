# Basic Memory integration boundary

The optional backend is fixed by
`reference-assets/MEMORY-depo/profiles/basic-memory-v0.23.0.json` and the separate
`requirements-backend-pilot.txt`. The profile is specific to Python 3.12 on macOS
arm64. Another platform needs its own reviewed complete artifact resolution.
Ordinary reads and project setup never install those requirements or a model.

`basic_memory_adapter.query(root, query, config=None, mode="hybrid", limit=20,
packet=None)` starts only the fixed local query worker. Supported modes are
`text`, `vector`, and `hybrid`. `health(root, config=None, level="static")` reads existing state
without importing vendor packages. Explicit `level="operational"` additionally
runs the fixed bounded hybrid-read worker and rechecks final versions. Missing, changed, disabled, unprovisioned,
uncertified, or pending-recovery state returns a lexical limitation. Canonical
read and validation stay with the standard-library memory helper.

The backend's actual `fts` mode is reported publicly as `text`. Vendor hybrid
ranking is evidence of relevance only. Returned path, source identity, lifecycle,
metadata, title and body come from currently permitted canonical documents.
Additional solver retrieval is filtered through the exact frozen packet.

The internal `pilot=True` query keyword is reserved for a specifically scoped
compatibility evaluation. It leaves persistent enablement unchanged and retains
every certificate, version, project, model, read-only, and network check. The
ordinary memory search command does not expose it. Enabling persistent flags
changes the configuration digest; perform a new authorized reindex and then
repeat the enabled-root query before claiming enabled behavior.

The only public backend operations are search and health. Vendor `write_note`,
edit/delete/project/config/cloud tools and arbitrary commands are inaccessible
through this interface. ConfigManager and normal vendor startup are not used.
The subprocess binds one project to one derived projection and one immutable
read-only SQLite file; it loads a pinned local model and denies network and
Python-level filesystem writes. These checks are not an OS sandbox.

`memory_maintenance.reindex_payload(root)` returns the concrete versioned request
for review. `reindex(root, grant_file=..., actor=..., expected_payload_sha256=...)`
requires a current grant over that payload and all affected state paths. Its
worker rechecks authority and can write only its assigned staging directory.
The shared canonical memory lock prevents concurrent publication. Normalized
products, projection and index are rebuildable. Configuration and unresolved
maintenance journals are durable; they cannot be treated as caches.

`recover_reindex(root, operation_id, grant_file=..., actor=...)` aborts a failed
pre-publication build or restores exact prior derived products after interrupted
publication. It retains failure artifacts and rejects changed or unknown state.
This operation does not replay canonical publication or Task transitions.

A prebuilt certificate records exact configuration, projection, database,
adapter and profile hashes. It is distinct from the full compatibility decision.
Root semantic enablement is authorized only after all mandatory actual pilot
checks pass. Deterministic tests and a small fixture do not establish root or
future-host readiness. A failed pilot keeps lexical/direct retrieval available.


Projection manifests record the exact producer implementations for identity,
normalization, text extraction and eligibility. They verify the complete current
permitted document set, including additions, content changes and memory lifecycle
changes. Legacy manifests lacking producer hashes are explicitly stale and require
a reviewed reindex; a read never adds those hashes. Index manifests bind database
bytes, and certificates bind project/root, configuration, backend settings,
projection, database, adapter and profile; the profile pins local model artifacts.
Changes outside the declared corpus and producer set do not fabricate dependencies.
