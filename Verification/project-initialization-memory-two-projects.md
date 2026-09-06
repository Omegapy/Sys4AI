# Two-project bootstrap and provider verification

Two opt-in tests passed with `uv run --frozen --no-sync python -m pytest -q -p no:cacheprovider tests/integration/test_consumer_bootstrap_isolation.py` and the reviewed immutable artifact. The core wheel and its locked dependencies were installed independently into disposable alpha/beta project environments. Each installed process prepared its canonical files, directly initialized memory, synchronized its own marker, recalled one own match and zero foreign matches, and rejected crossed project/dataset context. Direct outputs contain no preview object or impact digest. Invalid storage configuration failed without committed derived state.

Two separate controlled Cognee 1.5.3 adapter processes initialized distinct relational stores. The Director independently compared final inode manifests: disjoint. Native data, logs and configured model roots remain beneath each 0700 memory ancestor; native SQLite leaves are 0644 and native directories 0755, while core exact/receipt/audit files are 0600. Effective private ancestor confinement was verified. No model files, allowed network operations or outside-root writes occurred. Each process blocked urllib3's import-time IPv6 capability bind; this was not an allowed network action.

The five-entry user-wide Cognee metadata snapshot remained unchanged, as did the Director's original protected baseline. No live template, product or root memory was initialized. Semantic ingestion and model inference were not part of these exact/bootstrap/storage tests. Ruff passed.

Full disposable evidence: `/private/tmp/sys4ai-consumer-isolation-20260905-02/consumer-isolation0/consumer-isolation-evidence.json`.
