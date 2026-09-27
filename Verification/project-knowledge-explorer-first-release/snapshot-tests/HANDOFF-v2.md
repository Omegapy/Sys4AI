# Snapshot correction handoff v2

The API and integration boundaries in HANDOFF.md remain unchanged. The current source and tests are bound by delivery-v2.json and run-06.json. Version 1 source/test bytes are retained in source-v1.py.txt and tests-v1.py.txt; version 1 delivery, result and every earlier run record remain unchanged as historical evidence.

The corrected snapshot preflight validates untrusted container shapes before accessing nested configuration, module manifests, graph documents, source arrays, project identity and local registry observations. Complete semantic validation still runs through the unchanged canonical loader. No blanket AttributeError catch was introduced.

The current 40-test suite passes. Three added tests cover 41 malformed-container cases, including the exact manifest-array regression. Each case requires the exact private store.error_type, fixed canonical_invalid message, and retention of the prior current view. The current live-root snapshot check loads 412 records and 181 relationships across 34 source paths, reuses its immutable cache, and preserves selected bytes and modification times across cached reads.

This remains scoped TASK-004 evidence. Full reader semantics, production bootstrap/package/worker handshake, supervisor deadline/RSS controls, HTTP/session/assets, browser and final preservation gates retain the boundaries recorded in HANDOFF.md and result-v2.json.
