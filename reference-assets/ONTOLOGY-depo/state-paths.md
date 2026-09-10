# Ontology state paths

| Class | Selected paths | Ownership and rebuild rule |
| --- | --- | --- |
| Canonical | `ontology.yaml`, selected files under `ONTOLOGY/modules/` and `ONTOLOGY/bindings/` | Configuration selects identity, imports and sources. Canonical facts change only through scoped review; imported core files remain locked. |
| Generated | `.sys4ai/ontology/compiled/`, `manifests/`, `links/` and other declared projection paths | Explicit operations rebuild these from current identified inputs. Each operation owns an exact output-hash manifest. Unknown or edited destinations cause conflicts. |
| Generated wiki | `ONTOLOGY/WIKI/` | Explicit `build-wiki` creates Markdown navigation and provenance; pages never become canonical input. |
| Durable accepted intent | `control_records/ontology/intents/<operation-id>.json` | Immutable exact reviewed payload, prior bytes, publisher identity and input context; not a cache. |
| Durable completion receipt | `control_records/ontology/receipts/<operation-id>.json` | Immutable report of actual committed files and projection result. Replay must still match actual current canonical hashes. |
| Durable recovery | `control_records/ontology/recovery/<operation-id>.json` | Bounded progress and conflict information for the original accepted operation. An exact current grant is required to recover. |
| Writer locks | `control_records/ontology/publication.lock`, `.sys4ai/ontology/build.lock` | Nonblocking POSIX advisory locks are held only during the operation. Never delete a lock to override an active writer. |

Removing generated output loses no canonical knowledge, accepted intent or publication receipt. Rebuild only through an explicit operation. There is no broad cleanup, root-wide ingestion, hidden repair on reads, runtime/service setup or automatic project propagation. Obsolete managed projections are preserved unless their exact removal is separately selected; unknown files are always preserved.

Memory, learning, Task records, role pairs and their own recovery state remain separate. Ontology publication and recovery modify none of them. Immutable Task packets are ontology-owned outputs at the exact granted packet path; the existing Task helper registers their external path/SHA256 references without a schema change.

## Advanced capability paths

The companion `ontology-advanced.yaml` selects versioned optional profiles and
exact approved files beneath `ONTOLOGY/extensions/`. It leaves the compact v1
configuration and locked imported core identities intact. Rules and shapes are
capability contracts; profile selection and current action authority are separate.

Saved drafts, immutable candidate revisions, review history, and staged RDF
imports belong under `ONTOLOGY/proposals/`. Immutable native generation requests
and captured results belong under `control_records/ontology/generation/`.
Accepted publication, exact repair, profile setup and guard bootstrap evidence
remain in `control_records/ontology/`. None are projection caches.

The independent environments `.venv-ontology-standards/` and
`.venv-ontology-semantic/` contain explicitly provisioned packages. The standards
environment also holds host certification and bounded worker-capacity slots.
Ontology model artifacts and their exact manifest live under
`.sys4ai/ontology/semantic/`; only an explicit build replaces `index-v1.json`.
Reads neither download a model nor refresh an index. Workbench session files
belong only in `.sys4ai/ontology/workbench/` with private filesystem permissions;
session credentials do not belong in saved operational evidence.

Advanced Task packets retain the existing 250,000-byte and 200-reference bounds
and exact manager-owned artifact paths. Version 2 includes selected contracts,
proofs and semantic query vectors/matrices. Live changes require reassessment;
neither a query nor a guard rewrites a solver's frozen packet.
