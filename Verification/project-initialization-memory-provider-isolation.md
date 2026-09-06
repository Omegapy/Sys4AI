# Provider path confinement evidence

Configuration, provider contracts, and the lazy adapter now confine exact indexes, model caches, audit events, native data/system/cache/log directories and configured model frameworks below the selected project derived root. The adapter rechecks paths before import/use and rejects reuse with another project or dataset.

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/configuration tests/providers` in Memory Service: **57 passed, 1 skipped**. This isolated test process includes the real pinned Cognee initialization/database/archive compatibility test with network blocked; the skipped case requires a separately running model and semantic extraction. Focused Ruff checks passed. Fake import tests verify the environment before import, distinct project paths, caller environment restoration, symlink refusal and no user-home fallback.

The user-wide `.cognee` manifest exactly matches the pre-change baseline. `git check-ignore` confirms representative native log and model paths below the project `.sys4ai/memory` boundary are ignored. No live product provider directory was initialized.
