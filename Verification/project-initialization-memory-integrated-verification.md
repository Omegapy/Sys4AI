# Integrated verification

The final Memory Service wheel is version 0.1.0, SHA-256
`4970a7e5fd108eed9a1637069ddb7b11be023134a2cbe35648a9b96bf5ca104f`.
Its source-manifest SHA-256 is
`f2fa121c505d19516ea4d66dfa05f275e7e993ab6cbd96cd1cc80e31105ab1a1`.
The exact product's own Git marker, top-level and HEAD remain null; no parent
HEAD is substituted. Root installation metadata and all installed package
members match this artifact. The prior installation receipt is retained as
`control_records/memory/runtime-installation-0ba0ca67.json`; the current receipt
is `runtime-installation.json`. Replacing the development artifact after the
observed CLI correction did not change the root initialization receipt or data.

The final initializer helper SHA-256 is
`487b9c023fcabe3f19a36b7fca66759e8b95b50f17b82df67fd4323c9aeffe6a`.
All nine source/active package files match the current reviewed adoption manifest.

## Current executed checks

| Scope and actual environment | Result |
| --- | --- |
| Memory Service `make validate-memory`, existing product `.venv` through `uv run --frozen --no-sync` | Ruff passed; strict mypy passed for 114 source files; 594 tests passed, 5 opt-in tests skipped; release evidence 296 rows valid |
| Root `.venv`, all root tests | 28 passed, no runtime-import skips |
| Template's protected existing `.venv`, static seed tests | 7 passed |
| Source initializer, final wheel enabled | 17 passed in 114.249 seconds |
| Active initializer, final wheel enabled | 17 passed in 114.405 seconds |
| Both skill metadata files | Skill Creator validation passed; focused Ruff passed |
| Final root installed exact runtime after wheel replacement | Inventory exact recall passed in 1.006 seconds; canonical source hashes match |
| Installed resource and two-project native isolation opt-ins | 6 passed in 13.17 seconds with the preceding 0ba0ca67 artifact; every bootstrap/runtime/provider/package-resource member is byte-identical in the final wheel |
| Immutable build/installation checks | Original three tests passed; final source/active suites independently rebuilt the final wheel in separate fixture roots and matched its exact SHA-256 |
| Reviewed registration correction | 54 focused cases passed, including real subprocess success and sanitized permission denial; included in full 594-case suite |

The only changed wheel members between 0ba0ca67 and the final artifact are
`sys4ai_memory/source_registration.py` and the wheel's RECORD. Native isolation
evidence therefore still exercises the exact current provider/bootstrap bytes.
The five full-suite skips are two installed isolation cases, resource packaging,
an opt-in build case and local semantic inference. All required installed/build
behavior has separate evidence; semantic inference remains deliberately deferred.
The full suite emitted twelve upstream deprecation warnings.

## Corrections found through integration

- The rebuild fixture copied product registries without their schema/profile
  references. It now uses common consumer preparation; all ten rebuild tests pass.
- Source/active initializer test setup now handles both installation depths.
- FORWARD-001: permitted nested Projects destinations initially retained six
  incorrect relative guide links. The helper now rebases links to their original
  depot assets and records distinct source/destination hashes. Direct-child bytes,
  anchors and external links remain intact. The production template is unchanged.
- The reviewed-registration CLI correctly refused an ungranted principal but
  originally emitted an uncaught PermissionDeniedError. It now returns sanitized
  JSON with exit 2. Authorization and registry preservation are unchanged.

## Classified existing limits

The Director reran the unchanged producer Task contract: 16 tests, two failures
(`test_conditional_packages_match_impact_matrix` for Agent Task and
`test_required_sources_are_adopted_by_the_active_root`). Both assume equality
that the earlier separately authorized root-only Task intake policy intentionally
changed. The actual source and active Task packages remain at protected hashes.

The unchanged template role contract ran 50 tests with one failure:
`test_director_role_contains_every_required_operating_section` expects the exact
obsolete heading `## Task assessment and decomposition`. The protected template
ROLE remains unchanged; portable role-catalog behavior passes. No protected
guidance was rewritten to satisfy these old producer assumptions.

An unrelated existing multi-version `get --include-history` duplicate audit
target issue was reproduced independently of the new verifier. Current exact and
lexical retrieval plus explicit historical recall pass. The product release
ledger's unrelated deferred/unverified entries are not converted into release
claims by this plan.

No model download, semantic inference, host skill-discovery refresh, Git setup,
commit, push, remote creation, site publication or deployment is claimed.
Project creation is verified in disposable depots; the live root has its own
functional exact/lexical memory and the real template remains uninitialized.
Raw test output and independent forward-case evidence are retained under
`/private/tmp/sys4ai-*`; concise source-backed records live in this directory.
