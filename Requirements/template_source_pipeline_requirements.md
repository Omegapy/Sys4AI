# Template source pipeline requirements

Source: the user's 2026-09-05 request in this conversation to separate reusable
asset maintenance from project initialization and automatically update the
template after depot additions, modifications, and deletions.

| ID | Requirement | Observable acceptance |
| --- | --- | --- |
| TSP-001 | Reusable skills and guidance are authored in their `*-depo` source collections. | Root guidance identifies source ownership and the template update route. |
| TSP-002 | Both initializer routes obtain every starter asset from the registered template. | Tests give template and depot different bytes, remove source collections, and prove template bytes win; asset receipts cite only template paths. |
| TSP-003 | New template skills and role bundles are discovered without a fixed six-package copy list. | Added packages are copied; removed optional packages are absent; required governance remains validated. |
| TSP-004 | Additions, modifications and deletions in source collections update only the template. | Engine fixtures exercise all operations; existing product projects and active root assets remain unchanged. |
| TSP-005 | Explicit mappings preserve the template's active file layout and specialized guidance. | Reviewed template guidance is first retained in source files; mapped outputs have matching hashes. Other reusable documents are available under `reference-assets/`. |
| TSP-006 | Automatic updates work after filesystem edits, without requiring a commit or a running Codex task. | A local macOS launch agent observes a harmless live source addition, modification and removal and updates the template after edits settle. |
| TSP-007 | Updates protect unrelated files and reject unsafe or incomplete input. | Tests cover symlinks, invalid skill content, missing source collections, destination customization, source drift and interrupted writes. No force-overwrite mode exists. |
| TSP-008 | Initialization and automatic updates cannot consume or publish an inconsistent template snapshot. | Shared/exclusive locking and source-recheck tests pass; a second unchanged update writes nothing. |
| TSP-009 | Preserve project identity, manual-copy conflicts, customized files and rerun behavior. | Initializer checks pass in isolated standard-library fixtures; the Template remains a neutral starter. |
| TSP-010 | Ship clear control, status and recovery instructions with current evidence. | Local check/apply and watcher status/stop commands work; final review maps every requirement to files and observed checks. |

Project runtime and dependency setup are separate from starter asset delivery.
The 2026-09-07 cleanup supersedes the earlier runtime-adoption requirement while
preserving this pipeline's source ownership, update, and project-isolation
requirements. Historical Task and managed document records remain separate.
