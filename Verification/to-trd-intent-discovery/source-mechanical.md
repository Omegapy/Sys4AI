# Revised source verification

Final candidate: [complete manifest](candidate-manifest.json), version 2.2.0, resource-manifest digest `4d33823d68edb18e5696cd27d6e25a3229115404a23c9b7ec52636decbdf5d55`. This manifest hashes a sorted JSON map of all 16 relative resource paths and SHA-256 values; it is not a Git commit or host-loading claim.

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/to-trd/tests -v`: **46/46 passed**, 6.452 seconds. [Output](source-test-output.txt).
- Baseline and final helper/test modules passed AST parsing and compilation into disposable output directories. No source bytecode artifacts were generated.
- `test_skill_package_contract` verifies resource presence, all local Markdown links, explicit-only metadata, naming, source helper standard-library imports, and unchanged upstream license identity. `test_template_and_example` validates heading order, JSON/body shape, stable IDs, real dependency and U03 propagation into selection and acceptance.
- `test_clarification_questions_stay_out_of_new_writes` retains rejection of persisted prompts, historical read compatibility and managed-update behavior; each fixture replacement asserts one target, and the saved record asserts intent, scope, U04 source, requirement and acceptance propagation. `test_material_updates_reopen_document_review` still asserts its changes are not no-ops. Other migration, lifecycle, diagnostics, hash, lock, atomicity, no-op, read-only, and privacy regressions remain present and pass.
- SKILL, README, INDEX and maintenance guidance all identify 2.2.0. Schema 2, all eight helper commands and operation IDs remain unchanged. The protected helper, ATTRIBUTION and MIT bytes match baseline hashes. [Exact execution diff](source-changes.patch).
- The external `skill-creator/scripts/quick_validate.py` was attempted with the project Python and existing bundled Python; both stop before validation with `ModuleNotFoundError: No module named 'yaml'`. The default Python also lacks PyYAML. No dependency was installed or validator weakened. The package's own metadata/link tests passed, but the external YAML validator is **not reported passed**.

These are structural and helper results. They do not establish a real pause, meaningful user-answer incorporation by an agent, or fresh-host loading. All manual cases remain [unexercised](host-results.md).
