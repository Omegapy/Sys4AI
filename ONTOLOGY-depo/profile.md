# Local ontology profile 1.0.0

This is a deliberately bounded compact JSON-LD authoring profile, parsed with Python 3.12 standard-library JSON. It is not a general JSON-LD processor. Unknown keys, duplicate JSON keys, non-finite numbers, nested or remote contexts, unsupported kinds and escaping paths are errors. Configuration uses strict UTF-8 JSON as the documented JSON subset of YAML.

## Configuration

`ontology.yaml` contains `schema_version: 1`; `project` with `id`, `name`, `purpose`, `namespace` and `root`; `context` with exact `path` and `sha256`; locked `modules`; exact `project_files`, `binding_files`, optional `competency_files`; `source_allowlist`; `retrieval`; and `publication`. Project `root` is `.`. A specialized ID uses lowercase letters, numbers and hyphens. Its namespace is `urn:sys4ai:ontology:project:<project-id>:`. If present, current `project.json` or the root entry in `depot/projects.json` must agree. The neutral starter leaves ID, name, purpose and namespace null and disables publication.

The trusted context is `ONTOLOGY/contexts/context-v1.jsonld`. Its exact content must match the installed profile constant and configured SHA256. Each imported module manifests an identical context copy. The context maps profile properties to stable `urn:sys4ai:ontology:core:field:<name>` property identities. `@id` and `@type` retain their JSON-LD identity meanings. Contexts are read locally and no context URL is fetched.

An import has `id`, `version`, `path` and `sha256`. Its `manifest.json` has `schema_version`, `module_id`, `version`, `files` and `record_files`. `files` maps every module-relative file except the manifest itself to its SHA256. The locked module digest hashes canonical JSON of this complete map. An extra, missing or changed file fails integrity checks. The manifest's own digest is included separately in every input snapshot, avoiding self-hash cycles. `record_files` lists only manifested JSON-LD graph files.

Selected extension paths are under `ONTOLOGY/modules/project/` and end in `.jsonld`; binding paths are under `ONTOLOGY/bindings/` and end in `.json` or `.jsonld`. Competency paths are explicit `.json` files under `ONTOLOGY/modules/project/`. Nothing recursively discovers child projects or new canonical files.

The source allowlist selects exact project-relative regular files. It never uses wildcards. Approved vendored module files are also permitted local sources. Child projects, memory records, Tasks, private runtime, environment/cache directories, hidden credentials and generated wiki pages cannot be source bindings. Symlinks, hardlink aliases, FIFOs, traversal and absolute file references fail before content is returned.

Retrieval defaults are two hops, twenty results and 32000 UTF-8 context bytes. Configured bounds must retain maximum eight hops, one hundred results and 32000 bytes, with at least 1024 context bytes. CLI operations report truncation and stable ID tie breaks.

## Records

Every graph document has exactly `@context` (the configured local context path) and `@graph` (a record array). Record property inventory is machine-readable in `contract.json` and `schema/record-v1.json`. Executable semantic validation is in `ontology_validate.py`.

| Common field | Meaning |
| --- | --- |
| `@id` | Stable absolute URN. Shared meanings use `urn:sys4ai:ontology:core:<local-id>`; project entities use their selected namespace. IDs are never recycled. |
| `@type` | A nonempty array of selected concept type IDs. `kind` separately distinguishes a class or concept from a concrete instance. |
| `kind` | `concept`, `predicate`, `instance`, `relation` or `binding`. |
| `label`, `definition` | Preferred human label and explicit meaning. Both are mandatory for approved/deprecated records. |
| `lifecycle` | `draft`, `approved` or `deprecated`. Draft suggestions do not enter approved lookup silently. |
| `module` | Owning module, `sys4ai-core` for imported records or `project` for local records. |
| `sources` | Exact references `{path, sha256, locator}`; required for approved/deprecated records. |
| `fact_kind` | `asserted`, `derived`, `inferred` or `external`. A classification does not enable an inference engine or promote derived links to canonical assertions. |
| `aliases` | Alternative strings resolving to this stable ID. |
| `scope_note` | Human explanation of scope or a distinction from another meaning. |
| `examples`, `non_examples` | Optional explanatory string arrays. |
| `ambiguity_with` | Other stable IDs sharing an explicitly ambiguous label or alias. Every affected candidate must name all peers and supply a scope note. |
| `deprecation_reason`, `replacement` | Reason and optional distinct replacement ID. Only deprecated records use these fields. |
| `history` | Retained previous reviewed meanings, with `sha256`, `definition`, `lifecycle` and `reason`. The hash covers the complete prior canonical record serialization. |

Predicates add `domain` and `range` arrays of selected concept type IDs; `acyclic` boolean; `cardinality` with nonnegative `min` and compatible `max` or null; and `qualifiers` mapping names to `{type, required}`. Supported qualifier types are string, integer, number and boolean. Cardinality counts outgoing edges for each matching source. Type membership follows explicit `subtypeOf` declarations. A concept can participate in type-level relationships through its own semantic ID; its `kind: concept` remains distinct from an instance.

Relations add `subject`, `predicate` and `object` stable IDs and an optional `qualifiers` object conforming to the predicate schema. Direction is preserved. Only predicates declaring acyclicity reject cycles. All endpoints, types, replacements and ambiguity references must resolve in the selected graph.

Bindings add `entity` (the described stable ID) and `binding_type` (`artifact`, `skill`, `role`, `specification` or `registry`). Sources carry actual exact file references. Role bindings require both AGENTS.md and ROLE.md in one directory. A registry binding describes factual inventory and grants no access to a child's ontology.

## Provenance and deterministic versions

Source locators are `section:<literal heading or text>`, `line:<n>`/`lines:<start>-<end>`, or `json:<JSON pointer>`. The locator must resolve in current matching bytes. A changed hash yields `stale`; a missing or inaccessible source yields `unavailable`. Retrieval keeps these statuses explicit. It cannot present stale ontology text as current governing authority.

Input snapshots include the project ID, profile/generator versions, exact configuration/context/module/canonical/source file hashes, module manifest hashes and ontology helper hashes. They contain no clock or temporary absolute root path. Sorted UTF-8 JSON, two-space indentation and one trailing newline define deterministic serialization.

Approved semantic edits need new exact scoped review and retained previous meaning, or a draft transition followed by later approval. A deprecated ID keeps its original meaning and lifecycle; use a new identity for replacement. Label/path changes preserve stable identity. Publication checks the complete proposed graph and never rewrites an imported core ID.
