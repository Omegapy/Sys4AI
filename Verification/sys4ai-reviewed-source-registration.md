# Reviewed future-source registration

Director inspection and independent execution on 2026-09-05 verified the new
`sys4ai_memory.source_registration` administrative route. The combined focused
command passed **69 tests in 7.68 seconds**:

```text
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 .venv/bin/python -m pytest
  -p no:cacheprovider -q tests/observability/test_administrative_executor.py
  tests/observability/test_source_registration.py
  tests/ingestion/test_registry_discovery.py
```

The route reuses the existing `AdministrativeActionExecutor` unchanged. It
requires initialized exact memory and a current canonical action-specific
`memory.sources.register` grant, rereads permission immediately before
publication, and uses the same runtime lock as memory operations. The request
contains project/dataset, stable source ID, path/pattern, adapter/format, owner,
relevance, namespace, canonicality, authority, trust, sensitivity, retention,
write policy and chunking metadata. A local review reference and exact reviewed
registry SHA-256 bind the decision to current canonical inputs.

Disposable fixtures prove an unknown folder is unmatched before registration,
eligible content becomes discoverable afterward, a second folder needs only new
reviewed data, and existing exclusions continue to override admission. Original
CSV rows remain byte-identical; equivalent reruns add nothing. Concurrent stale
requests, conflicting IDs, revoked or general-only grants, foreign identity,
unsupported adapters, symlinks, nested Git projects and prohibited child,
derived, cache, environment, model, secret, temporary and raw-log paths refuse
publication. Wrong-principal requests do not reach candidate content discovery.

The Director inspected the full production module and test coverage. Ruff and
strict mypy passed in the child's isolated check. The module SHA-256 at this
inspection is `d578c2a2f5db7a54d849ad243cb730bf2646ea48ee09c7a0fe9eda0a404f3746`.
Operator instructions are in the Memory Service's
`docs/operations/source-and-profile-registration.md`. No live root folder was
admitted, no exclusion weakened, and no provider/model/network action occurred.
The route is included in the next immutable wheel; installed integration is a
separate later check.
