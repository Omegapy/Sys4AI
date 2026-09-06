# Consumer package verification

The shared installed `prepare_project_memory` API and `python -m sys4ai_memory.bootstrap prepare` route create 27 canonical files plus ignore protections using importlib.resources. The resource set contains configuration, three registries, schemas, base and optional software-engineering profile reference closure, and consumer-owned permission records. Identity and owner are explicit inputs; the exact-only base profile defers semantic/provider activation.

The Director reviewed preparation validation, identity specialization, all-file conflict checks, reference validation in a disposable directory, exclusive creation and retry behavior. The independent package owner ran 30 bootstrap/packaging tests against the built wheel: all passed. The wheel-only subprocess loaded every generated reference, configuration and permission declaration and ran service health with no editable product import, no native Cognee import and no .sys4ai state. Ruff and strict mypy passed.

The immutable build workflow pins Hatchling 1.32.0 and its hash-locked build dependencies in a temporary environment. Runtime dependencies are exported from unchanged uv.lock using --locked. The artifact records every source/member digest, Python/backend/tool versions and unavailable independent Git metadata as null.

Two builds of the unchanged live source returned the same immutable artifact and byte-identical wheel; three artifact tests passed, including two disposable builds, exact non-editable installation, installed-member verification and a disposable source mutation that did not change installed bytes. No package was published. The installer preserves unrelated environment packages and records control_records/memory/runtime-installation.json.

Artifact receipt: `/Volumes/P-SSD/AngryOwl/Sys4AI/Projects/Sys4AI-Memory-Service/dist/consumer/0.1.0/093ca469f1c1ca7c3991e7894cea8075a01b1b2b39b9b104f926c9ccef2748b1/artifact.json`

Wheel SHA-256: `37bd904f5ad2bdda16b63e86f42cfca44e13f71c2cf6b92b1ca3dcf4c7cca7c7`

Source manifest SHA-256: `093ca469f1c1ca7c3991e7894cea8075a01b1b2b39b9b104f926c9ccef2748b1`
