# Source and profile registration

Runtime discovery never edits a registry. Source and profile registration is a
normal reviewed project change to tracked canonical files.

The installed `sys4ai_memory.source_registration` administrative module applies
one reviewed, project-owned source rule through `AdministrativeActionExecutor`
and `memory.sources.register`. That existing boundary rereads the canonical
action-specific `administer` grant and records the outcome. Registration remains
outside the public memory API. Profile installation still uses the reviewed
`memory.profile.install` callback boundary described below.

## Apply reviewed future-folder data

This route requires an already initialized local exact index and a matching
initialization receipt. It writes its audit events to the existing project-local
audit path. It never initializes `.sys4ai/memory`, a provider, models, or a
network listener. The named principal needs the explicit `memory.sources.register`
grant for `registries/memory_source_registry.csv`; a general `administer` grant
without that operation is insufficient. Consumer preparation supplies this
bounded grant only with its explicit source-registration option.

Record the review in an existing project-local file, for example
`Verification/future-source-review.md`. Save the reviewed source metadata as
`Verification/future-source.json`:

```json
{
  "project_id": "example-project",
  "dataset_id": "example-project-memory",
  "source_id": "src_future_design_notes",
  "path": "DesignNotes",
  "file_pattern": "*.md",
  "recursive": true,
  "format": "markdown",
  "ingestion_adapter": "markdown",
  "namespace": "project:design-notes",
  "canonicality": "canonical",
  "content_role": "project-knowledge",
  "authority_tier": "A3",
  "trust_class": "project-authored",
  "sensitivity": "internal",
  "retention_policy": "canonical",
  "write_policy": "deny",
  "owner": "project-owner",
  "relevance": "Reviewed design notes for this project",
  "profile_id": "base@1",
  "chunking_profile": "heading-blocks@1",
  "refresh_mode": "content-hash"
}
```

The folder must already exist and contain at least one eligible source of the
declared format. The filename pattern matches one segment; `recursive: true`
adds explicit `**` recursion. For one exact file, use its relative path and omit
`file_pattern` and `recursive`. The base profile must declare the selected
format/adapter pair. This route does not install optional adapters or change
profiles. Source registration cannot assign A0/A1 authority or system-controlled
trust, grant canonical writes, or remove an exclusion.

From the consumer project, inspect the current registry hash and use that exact
reviewed value in the command:

```bash
shasum -a 256 registries/memory_source_registry.csv
.venv/bin/python -m sys4ai_memory.source_registration \
  --project-root "$PWD" \
  --principal-id project-owner \
  --reviewed-source-json Verification/future-source.json \
  --review-reference Verification/future-source-review.md \
  --expected-registry-sha256 CURRENT_REVIEWED_SHA256
```

The Python entry point is:

```python
from sys4ai_memory.source_registration import register_reviewed_source

receipt = register_reviewed_source(
    project_root,
    principal_id,
    reviewed_source,
    review_reference="Verification/future-source-review.md",
    expected_registry_sha256=current_reviewed_hash,
)
```

The operation acquires the existing runtime lock and rereads canonical
configuration, source registry and permissions. It uses the existing
`SourceDiscovery` matcher and exclusion precedence to prove the specific
admission, then atomically appends one CSV row while retaining all previous
bytes. It rereads authorization and canonical inputs immediately before the
replacement. Duplicate IDs with different metadata, overlapping include rules,
stale hashes, malformed metadata, symlinks, traversal and independently owned
nested Git folders are rejected. Child projects, derived state, environments,
caches, models, secrets, staging, temporary files and raw logs are ineligible.
An excluded file inside an otherwise eligible folder remains excluded.

The returned receipt binds the reviewed metadata and review-file hashes to the
registry hashes before and after, actual admitted paths, change status, audit
outcome and trace ID. Audits contain hashes and source identifiers, never source
content. An equivalent repeat with the current registry hash returns `unchanged`
and does not duplicate or rewrite the row. A second eligible folder uses the
same data route without a Memory Service code change. Unregistered paths remain
denied and synchronization remains a separate operation.

An audit failure before the callback prevents the registry mutation. A failure
to persist the final audit event after atomic replacement returns an error,
never a success receipt. Inspect the current registry after an I/O error before
retrying with its fresh reviewed hash. Registration does not promise a
transaction spanning both the canonical CSV and the audit log.

Focused checks use disposable initialized exact-only projects:

```bash
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 .venv/bin/python -m pytest \
  -p no:cacheprovider -q tests/observability/test_administrative_executor.py \
  tests/observability/test_source_registration.py
```

## Register an exact source

1. Place the source inside the project root or obtain separate approval for an
   external URI. Do not register an arbitrary client-supplied local path.
2. Check the path against `.gitignore`, derived-data exclusions, secret-path
   patterns, file type, size, symlinks, and the intended sensitivity class.
3. Add one row to `registries/memory_source_registry.csv` using the exact
   documented header order. Use a stable `src_` identifier.
4. Set exactly one of `path_or_uri` or `path_pattern`. A direct source should
   use `source_kind=file`; a pattern should use `path_rule`.
5. Select the exact format, canonicality, content role, authority tier, trust
   class, sensitivity, namespace, profile, adapter, chunking profile, refresh
   mode, owner, and write policy. These fields are policy, not comments.
6. Keep `include_flag=true` only for an intentional include. Add a separate
   `exclusion_rule` with `include_flag=false` and `format=any` for a denial.
   Exclusion wins over inclusion.
7. Validate the complete registry bundle and run discovery before sync.

The source registry format is specified in [the registry contract](../../registries/README.md).
With `default_include = false`, an unmatched path is excluded. Discovery also
rejects absolute paths, traversal, symlinks, non-regular files, generated and
cache paths, Git-ignored paths, unsupported formats, oversized sources, and
secret-like content. External entries are declarations only; discovery never
fetches their URI. Their bytes and retrieval metadata must come from a separate
approved acquisition workflow.

The operations guides are currently registered as project knowledge by
`src_MEM-OPS-001`. Downloaded model manifests and blobs under `models/**` are
explicitly denied by `src_EXCLUDE-MODELS-001`; the local model smoke cannot
enter memory through a broad source pattern.

Focused validation:

```bash
uv run --frozen pytest -q tests/ingestion/test_registry_discovery.py
uv run --frozen pytest -q tests/ingestion/test_adapters.py
```

The first command validates registry references and default-deny discovery.
The second checks deterministic normalization for the registered adapter
families. Tests use tracked fixtures or temporary project roots; they do not
sync this project's live derived store.

Non-base formats use an explicit caller-supplied `OptionalSourceAdapter`.
The adapter must have a unique versioned ID, semantic version, and exact set of
formats, and it returns provider-neutral `OptionalAdapterUnit` values. It
cannot replace a base adapter. Discovery, project confinement, maximum byte
size, source hashing, and secret scanning run before extraction; ingestion
retains the exact bytes and source locator, bounds extracted text, and records
the supplied adapter version. A declared PDF, HTML, DOCX, XLSX, PPTX, image,
audio, or domain format fails closed when its exact adapter is absent. No
parser dependency is installed or selected implicitly.

## Explain before synchronizing

Source explanation is read-only and does not read file content. It reports the
matching registry rule and a stable disposition/reason such as
`registered_include`, `registered_exclusion`, `default_deny_unmatched`,
`unsafe_path`, `symlink_not_allowed`, or `secret_path`.

Full discovery reads only candidates that survive path and policy checks, then
performs the configured secret scan. Review every included, excluded, rejected,
and unmatched count before initialization or sync. A surprising include is a
stop condition.

Incremental synchronization compares source manifests and reports additions,
changes, moves, deletions, unchanged sources, failures, and checkpoint resumes.
A move retains identity only when the previous and current content hash match
uniquely. One source failure does not authorize skipping it silently; inspect
the source, adapter, stage, error category, and recovery action before resuming.

## Register a profile

The tracked base definition is `profiles/base/profile.yaml`; its projection is
the `base@1` row in `registries/memory_profile_registry.csv`. To develop an
extension:

1. Create a versioned YAML or JSON profile inside the project root.
2. Set a unique profile ID, exact version, `extends`, compatible memory API
   range, and every required capability.
3. Declare only the record types, relations, adapters, index fields, write and
   retention policies, retrieval/query strategies, context assembly,
   reranking, instructions, and evaluations owned by that extension. Do not
   redefine a base item.
4. Keep every repository reference normalized, relative, present, and inside
   the project root.
5. Add the matching registry row. The current CSV projection represents one
   parent in `extends_profile_id`; do not claim a multi-parent projection that
   the registry cannot express.
6. Load all selected profiles together, validate their registry projection,
   and compare them with the prior active set.
7. If record types, relations, adapters, write policy, retrieval strategy, or
   compatibility changes, require a versioned migration or a rebuild before
   activation.

Focused profile validation:

```bash
uv run --frozen pytest -q tests/profiles/test_profile_loader.py
```

The loader orders the base first, then extensions deterministically. It rejects
duplicate YAML keys, missing parents, inheritance cycles, detached profiles,
disabled required capabilities, API incompatibility, conflicting owned names,
unsafe references, registry mismatches, and any behavior reference that
exceeds the externally supplied source-authority ceiling.

## Current profile state

The `base@1` definition and loader are implemented and test-verified.
`software-engineering@1` is the approved first extension: it adds code, test,
build-target, and failure-pattern types; four relation declarations; the
`software-python-ast@1` adapter; write/retrieval/retention rules; and an
evaluation case. A public integration test syncs those records and serves two
agent identities without changing the operation catalog. Profile-specific
instructions still cannot raise source authority, change the public API, or
enable a missing provider capability.

All base relation meanings are registered. Relation validation and bounded
graph-ranking tests use supplied fixture or in-memory relations; a real Cognee
spike populated one typed relation, but the Sys4AI relation contract remains the
authority over provider-native graph semantics.
