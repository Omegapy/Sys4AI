# Template source pipeline implementation plan

This ordinary implementation plan carries the user's current authorized scope.
It does not create a managed TRD or reopen the completed orchestration Task.
Requirements: [template source pipeline](../Requirements/template_source_pipeline_requirements.md).

| Work | Requirements | Artifacts and dependency | Evidence |
| --- | --- | --- | --- |
| Retain specialized template guidance as reusable sources and define mappings. | TSP-001, TSP-004, TSP-005 | `AGENTS-depo/project-template-AGENTS.md`, template-specific files in `SPECS-depo/`, `depot/template-update.json`; precedes first template update. | Source-to-template hash comparison. |
| Make initialization read only the template's policy, renderer, skills, roles, soul and bounded references. | TSP-002, TSP-003, TSP-008, TSP-009 | `SKILLS-depo/init-new-project/`; adopt into the active initializer after verification. | Focused standard-library unit and isolated project-setup fixtures. |
| Implement deterministic update/check operations with scoped ownership and recovery. | TSP-004, TSP-005, TSP-007, TSP-008 | `tools/template_update.py`, `tests/test_template_update.py`; uses explicit mapping and local state. | Add/edit/delete, conflict, exclusion, concurrency and recovery fixtures. |
| Add and enable the macOS filesystem watcher. | TSP-006, TSP-007, TSP-010 | `tools/template_watch.py`, local launch agent, local status; requires verified engine. | Watcher tests and live source-file lifecycle observed through launchd. |
| Update guidance and affected repository/template contracts. | TSP-001, TSP-003, TSP-005, TSP-010 | Root/depot/project documentation and affected tests. | Link checks, package validation and relevant suites. |
| Integrate, inspect preservation boundaries and document verification. | All | `Verification/template_source_pipeline_verification.md`. | Current hashes, read-only update check, runtime evidence, final diff. |

The Project Director owns the design, mapping decisions, host activation and
integration. The bounded initializer implementation and update engine can be
developed independently. No child changes the Task ledger, registry, template,
active installation or host service.

Risk controls: a quiet period avoids copying files mid-save; structural
validation and source rechecks reject incomplete inputs; managed hashes prevent
overwriting customized template files; only previously managed removed files
can be deleted; a shared template lock separates updates from initialization.
Existing product projects remain independent. A missing external volume is an
unavailable source, never evidence to remove destination files.

Status: implemented and verified. The installed macOS watcher propagated a
live source addition, edit and deletion after the user approved Python's
removable-volume permission. See the [verification record](../Verification/template_source_pipeline_verification.md)
for evidence and remaining verification limits.
