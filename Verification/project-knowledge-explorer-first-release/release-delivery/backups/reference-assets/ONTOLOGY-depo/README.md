# Ontology Knowledge System

Version 1.0.0 provides a project-local vocabulary, typed relationships, exact local source bindings and deterministic retrieval. `modules/sys4ai-core/1.0.0` contains neutral reusable meanings. `starter/` contains a locked core, empty local extension and bindings, and unspecialized configuration. Specialize one selected project through the initializer before using it.

Canonical facts belong in `ONTOLOGY/modules/` and `ONTOLOGY/bindings/`; `ontology.yaml` selects their exact paths. [The profile](profile.md) describes every supported field. [State paths](state-paths.md) distinguish canonical inputs, generated products and durable accepted changes. [Publication and recovery](publication-and-recovery.md) describes exact review and current authority.

Use the installed ontology skill for `term Task`, `read` by stable ID, `capability`, typed `neighbors` and bounded `path`. `knowledge --intent current` checks selected current governing sources. Retrieval never executes a discovered skill or grants permission. `compile` and `build-wiki` are explicit generated writes. The wiki links definitions to exact canonical and source locations; edit canonical inputs through review rather than generated pages.

Each project imports the module version and complete file-set digest explicitly. A newer depot module never silently replaces a selected project version. Use distinct project URNs for extensions; shared core IDs cannot be redefined. Root-specific instances, publication grants, memory records, Task state and generated outputs do not belong in this collection.

The first release uses only Python 3.12's standard library. SPARQL, RDF conversion and standards validation, ontology embeddings, inference, graph databases, visual editing and execution interception are outside this release. Project memory remains a separate store and keeps its existing backend choices.
