# Ontology core interface, version 1

This is the shared implementation interface for PLAN-20260909-731308FD revision 4. All implementation files are staged until Director integration. Python requires only the standard library.

## Configuration and storage

`ontology.yaml` is strict JSON (the project's JSON subset of YAML). Its shape is:

```json
{
  "schema_version": 1,
  "project": {"id": "example", "name": "Example project", "purpose": "Selected project purpose.", "namespace": "urn:sys4ai:ontology:project:example:", "root": "."},
  "context": {"path": "ONTOLOGY/contexts/context-v1.jsonld", "sha256": "<64 lowercase hex>"},
  "modules": [{"id": "sys4ai-core", "version": "1.0.0", "path": "ONTOLOGY/modules/sys4ai-core/1.0.0", "sha256": "<file-set digest>"}],
  "project_files": ["ONTOLOGY/modules/project/project.jsonld"],
  "binding_files": ["ONTOLOGY/bindings/bindings.jsonld"],
  "competency_files": [],
  "source_allowlist": ["SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md", "depot/projects.json"],
  "retrieval": {"default_hops": 2, "max_hops": 8, "default_limit": 20, "max_limit": 100, "max_context_bytes": 32000},
  "publication": {"enabled": false, "binding": null}
}
```

Allowlist entries are exact relative file paths, never patterns or directory recursion. Vendored module manifest files are independently permitted source paths. The neutral starter has project ID, name, purpose and namespace null and publication disabled; ordinary operations reject it until initialization specializes it. Root `.` declares relocatable local identity; optional `expected_project_id` cross-checks callers. Existing project.json identity and any local registry root entry must agree. Bindings may use .json or .jsonld, always the exact graph profile. Optional competency_files selects exact project-local JSON files and participates in snapshots and publication.

Module manifest shape: `schema_version`, `module_id`, `version`, `files` (relative path -> SHA256), `record_files` (relative JSON-LD paths). Module lock is SHA256 of canonical JSON for the complete `files` map, including a separately configured trusted context hash in the map as `context-v1.jsonld` (the vendored module also holds an identical context copy). Manifest itself is separately included in the input snapshot. No extra module files are allowed.

Every canonical JSON-LD document has exactly `@context` and `@graph`. `@context` equals the configured local path string. Graph records have common fields `@id` (absolute stable URN), `@type` (nonempty array of absolute type URNs), `kind` (`concept`, `predicate`, `instance`, `relation`, or `binding`), `label`, `definition`, `lifecycle` (`draft`, `approved`, `deprecated`), `module`, `sources` (array of exact `{path, sha256, locator}`), and `fact_kind` (`asserted`, `derived`, `inferred`, `external`). Optional common fields: `aliases`, `scope_note`, `examples`, `non_examples`, `ambiguity_with`, `deprecation_reason`, `replacement`, `history`.

Predicate records add `domain` and `range` arrays of type URNs, `acyclic` boolean, `cardinality` (`min`, `max`, where max may be null), and `qualifiers` (name -> `{type: string|integer|number|boolean, required: boolean}`). Relation records add `subject`, `predicate`, `object` URNs and optional `qualifiers` map. Binding records add `entity` URN and `binding_type` (`artifact`, `skill`, `role`, `specification`, `registry`); their exact source is in `sources`, not an executable locator. All record keys are manifested in the profile contract. No arbitrary JSON-LD processing is supported.

## Shared Python API

`ontology_core.py` exports:

- `OntologyError(code, message, *, path=None, record_id=None)` with `.code`, `.message`, `.path`, `.record_id`, `.as_dict()`.
- `canonical_bytes(value) -> bytes` (sorted, indented UTF-8 JSON plus newline); `sha256(value: bytes|Path) -> str`; `read_json(path: Path) -> dict|list`; `safe_path(root: Path, relative: str, *, must_exist=True) -> Path` (rejects traversal and every symlink component).
- `load_project(root: str|Path, *, expected_project_id=None, validate=True) -> Project`. The loader never creates files. It rejects profile/path/module integrity failures. Semantic validation runs by default; `validate=False` permits examining invalid semantic data, while still enforcing safe parsing and import integrity. Source freshness failures become diagnostics and remain queryable as stale/unavailable; explicit builds/publication reject them.
- `Project` fields: `root: Path`, `config: dict`, `records: list[dict]` sorted by ID, `by_id: dict[str,dict]`, `relations: list[dict]`, `modules: list[dict]`, `locations: dict[str,str]`, `sources: list[dict]`, `diagnostics: list[dict]`, `snapshot: dict`.
- `Project.project_id`, `Project.namespace` properties. `Project.context()` returns deep-copied reproducibility context: project ID, profile/generator versions, exact configuration/canonical/context/module/helper/source hashes, and `snapshot_sha256`. No absolute temporary root or clock fields.
- `source_status(project, source: dict) -> dict`: original source plus `status` (`current`, `stale`, `unavailable`), `actual_sha256` or null, and bounded diagnostic. Project `.sources` is the deduplicated sorted list of these dictionaries.
- `assert_current(project) -> None`: rejects stale/unavailable sources and changed snapshot inputs.

`ontology_validate.py`: `validate_project(project, *, require_current=False) -> dict` with `valid`, `diagnostics`, and `context`; `validate_records(project) -> list[dict]`. Diagnostics always contain `code`, `message`, `path`, `record_id`, and `severity`, sorted deterministically.

`ontology_modules.py`: `module_digest(files: dict[str,str]) -> str`; `load_modules(root, config) -> tuple[records, modules, locations, inputs]` (locations maps ID to `file#/@graph/N`; inputs maps relative file path to digest).

`ontology_build.py`: `compile_project(project_or_root) -> dict`; `write_generated(project, outputs: dict[str,bytes], *, operation: str) -> dict`. Outputs are complete project-relative paths beneath `.sys4ai/ontology/` or `ONTOLOGY/WIKI/`; callers may import `write_generated` here. It validates inputs before writes, uses per-operation ownership manifests, refuses unknown/conflicting existing destinations, and preserves durable/canonical state. Return fields include `status`, `operation`, `outputs`, `context`.

`ontology_publication.py`: `preview(root, proposal: dict) -> dict`; `publish(root, proposal: dict, grant: dict, *, expected_preview_sha256: str, fail_at=None) -> dict`; `recover(root, operation_id: str, grant: dict, *, fail_at=None) -> dict`. Proposal shape and authority binding are defined in `ONTOLOGY-depo/publication-and-recovery.md`; CLI can accept strict JSON files and return these dict results unchanged.

Publication also explicitly compiles its changed canonical graph and records the projection result as required by TASK-010. A projection fault returns partial status with durable recovery. Standalone compile and build-wiki remain separate commands. Configured publication binding is `{actor_id, scope: ["ONTOLOGY/modules/project", "ONTOLOGY/bindings"], authority: [{path,sha256}]}`, with exactly the current SOUL.md, AGENTS.md and ROLE.md hashes. A proposal contains schema_version=1, operation_id beginning ONTOP-, operation=publish, reason, and changes with path/expected_sha256/content/sha256. Grants bind the proposal hash and preview hash, exact file scope and reviewed_records, actual normalized native roster, current identity/configuration and a maximum five-minute lifetime. See the publication contract for every field and manager Task context.

`ontology_lifecycle.py`: `transition(record: dict, state: str, *, reason: str, replacement=None) -> dict` returns a candidate only; `validate_transition(old_records, new_records) -> list[dict]` validates retained IDs and semantics history for publication.

`tests/support.py`: `make_project(path: Path, project_id="example") -> Path`, `core_id(local) -> str`, `project_id(local, identity="example") -> str`, `write_json(path,value)`, `read_json(path)`, `add_records(root, records, *, binding=False)`, `record(local, *, identity="example", kind="instance", type_name="Artifact", **overrides) -> dict`. Fixtures copy the neutral starter and specialize its ID; helper-generated records refer to fixture-local `SPECS.md`.

Query code should preserve all record fields, report `.sources` freshness and `.context()`, and filter approved defaults itself. It must not load generated graphs as authority. No core API invokes a skill, memory publisher, Task writer, network, or subprocess.
