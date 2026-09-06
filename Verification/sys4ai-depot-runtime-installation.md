# Exact root runtime installation

On 2026-09-05 the Director built and installed the latest frozen Memory Service
consumer in the actual Sys4AI root `.venv`. The immutable receipt is
`Projects/Sys4AI-Memory-Service/dist/consumer/0.1.0/9b94792bf169e43dcb4e4c1845aa4968b1656e5e181a8e4ee0e0027ff5cbe0ae/artifact.json`.

- Distribution: `sys4ai-memory-service` 0.1.0.
- Wheel: `sys4ai_memory_service-0.1.0-py3-none-any.whl`.
- Wheel SHA-256: `0ba0ca67e01b5baf0cea0a90647bf1f73da41e1154e2f044f0e0418d6c23ab40`.
- Source manifest SHA-256: `9b94792bf169e43dcb4e4c1845aa4968b1656e5e181a8e4ee0e0027ff5cbe0ae`.
- Product's own Git HEAD, marker and top-level: **null**. The product has no
  independent repository, as expressly accepted for this implementation. The
  parent Sys4AI HEAD is never substituted.
- Import origin:
  `/Volumes/P-SSD/AngryOwl/Sys4AI/.venv/lib/python3.12/site-packages/sys4ai_memory/__init__.py`.
- Installation: non-editable local wheel with a SHA-256 URL fragment; all wheel
  members and the exact locked core dependencies independently verified.
- Cognee imported by installation or boundary smoke: **false**. No root
  `.sys4ai` path existed after installation.

The canonical installation receipt is
`control_records/memory/runtime-installation.json`. It preserves the exact
artifact, source and installed metadata. The builder uses the existing locked
dependencies and pinned hatchling 1.32.0 build environment. No publication,
dependency unlock or Git operation occurred.

The installed adapter's safe configuration smoke checked root-local derived and
model-cache paths and rejected child-project/environment model-cache targets
without creating a directory or importing the native provider. The root
environment retains its unrelated existing packages.

The final source checks passed: Ruff, strict mypy (114 source files), **593
tests**, and release-evidence validation (296 rows). Five opt-in tests were
separately gated: two installed isolation cases, packaged resources, a build
reproducibility case and live semantic inference. Installed artifact/isolation
checks run separately for this plan; semantic inference stays deferred.
The initial rebuild-fixture failure was corrected by using the complete common
consumer preparation instead of copying incomplete product registries. All ten
rebuild tests and the full suite then passed. Twelve upstream deprecation
warnings do not change these observed results.
