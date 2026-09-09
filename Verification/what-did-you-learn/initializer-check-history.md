# Initializer check history

This worker ran isolated fixtures only. No live project initializer, Template updater,
package installer, backend, registry mutation, or Git publication was invoked.

- Baseline: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/init-new-project/tests` ran 69 tests in 106.566 seconds: OK, one skip for a case-insensitive real filesystem.
- Initial memory regression check: 8 tests in 19.577 seconds: OK.
- Initial learning edition check: 5 tests in 6.252 seconds: OK.
- First adoption check: 6 tests in 20.465 seconds, one error. The completed-rerun fixture removed the registered Template directory itself, causing the existing factual registry validation to reject the missing project. The fixture now changes the Template policy while preserving its registered directory, verifying that completed reruns do not read current starter inputs.
- First combined learning check: 12 tests in 29.156 seconds, one assertion failure. The added RuntimeError guard wrapped an existing InitializationError and hid its precise inventory diagnostic. The loader now preserves InitializationError unchanged.
- Corrected combined learning check: 13 tests in 30.971 seconds: OK. Includes no-execution sentinel checks for unknown destination and Template inspectors, and preserved narrower Director scope.
- First full v7 run: 85 tests in 164.809 seconds: 82 passed, two test failures, one known filesystem skip. The old latest-edition capture test expected unchanged governing bytes, whereas approved v7 first binding appends the minimal missing completion link. It now verifies that exact appended content and its final local authority hash. The generic partial-adoption test expected its conflict only inside the write stage; v7 rejects changed first-binding governance during frozen-proposal preflight. It now verifies the earlier diagnostic and unchanged pending receipt. Explicit earlier-edition cases retain their original expectations.

Later final check outputs are recorded separately under `initializer-*` in this directory.
- Corrected full run before final scalar guards: 86 tests in 167.607 seconds: OK, one known filesystem skip.
- Focused final scalar/provenance checks: 17 learning tests in 48.677 seconds: OK. Raw output is `initializer-learning-final.log`. This includes JSON true/list/dict/unknown-field refusals before mutation, exact selected type-collision refusal, and the bare-adopt/refresh/bare-repeat sequence.
- Final review also removed empty-directory ownership inference: an unowned empty dependency directory is preserved even with explicit refresh selection. The final full suite includes that additional regression case.
