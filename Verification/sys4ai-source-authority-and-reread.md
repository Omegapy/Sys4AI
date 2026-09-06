# Root source authority and current-source verification

On 2026-09-05 the Director ran the six root memory configuration/registry
unittests with the actual Memory Service environment: **6/6 passed**, without
creating live root derived state. The fixture matrix covers all 16 REQ-023
categories, their A1/A2/A3/A5 authority and distinct namespaces, plus child,
unregistered/no-Git child, derived, environment, cache, secret, model, lock,
temporary and raw-log exclusions. A new root folder remains unmatched.

The relevant Memory Service suite passed **41 tests in 26.35 seconds**:
`tests/test_local_runtime.py`, `tests/integration/test_control_authority.py`,
`tests/authorization/test_permissions.py`, and
`tests/ingestion/test_registry_discovery.py`, using `pytest -p no:cacheprovider -q`.
All mutable work occurs in disposable fixtures. No live root ingestion or
provider initialization occurs in these focused root registry tests.

The runtime now rereads each current exact/lexical returned source before
delivery, checking canonical registry eligibility, project/source/rule identity,
current content hash, authority, trust, namespace, sensitivity and profile.
Changed, deleted, restricted or excluded current sources fail closed. Explicit
historical recall stays historical. Current canonical permission revocation
overrules remembered permission content, and reusable/evidential content cannot
grant control authority. Foreign canonical project IDs and unsafe storage paths
still refuse reads.

Initialized exact reads avoid a repeated whole-depot discovery scan; they retain
canonical configuration, receipt, permission, registry and path validation and
perform bounded reread of returned sources. Mutations and provider activation
retain full preflight. This matters for the root's 243-source reviewed baseline,
where a full discovery took about 19 seconds. An anchored segment matcher also
keeps `tests/**` from incorrectly classifying nested reusable-package tests as
root tests. All source patterns remain relative to the project root.

The registered root corpus and its 16-category coverage are documented in
`sys4ai-depot-source-registry.md` and `sys4ai-depot-source-discovery.json`.
TASK-020's 69-case admission/authorization check supplements this coverage.

The child's investigation also reproduced an existing unrelated multi-version
`get --include-history` duplicate-audit-target failure with the new verifier
disabled. That route is not used for current-state validation here. Explicit
historical recall and the required current exact/lexical path pass. No semantic
model inference is claimed.
