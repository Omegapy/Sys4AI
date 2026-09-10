# Root and Template To-TRD adoption

Verified 2026-09-08T05:12:05.819966+00:00 under the user's explicit request to update the root project and `Projects/Sys4AI-Template-Project`. The requested `to-trp` name was interpreted as the existing `to-trd` skill, which documents TRP as an alias. No separate package was renamed or introduced.

Both installations now match **to-trd 2.2.0** from `SKILLS-depo/to-trd`, with all **16 resource hashes identical**.

| Destination | Action | Validation |
| --- | --- | --- |
| Root `.agents/skills/to-trd` | Updated 11 files and added both interaction resources after confirming no local drift from its recorded 2.1.0 baseline. | 46/46 tests passed in 6.74 seconds. |
| Template `.agents/skills/to-trd` | Already matched 2.2.0; the checked mapping required no write. | 46/46 tests passed in 6.758 seconds. |

AST parsing and compilation into temporary output passed for both installed helpers and test modules. The suites exercise each installation's own metadata, local links, examples, helper, lifecycle, compatibility and safe-write contracts. Root TRD validation is canonical-valid and read-only. The Template updater reports current with no pending work, conflict or recovery. Diff whitespace checks passed.

The helper, attribution and license needed no replacement. Project TRDs, Tasks, managed and unmanaged plans, root governance, registry and Template mapping retain their pre-adoption hashes. No source-package edits, product-project propagation, dependency installation, watcher control, Git mutation or publication occurred. Prior replaced root files were retained in a disposable backup.

This separately authorized adoption supersedes the root-preservation boundary of the earlier source-implementation turn. Its historical baseline and report remain accurate for that earlier operation. Canonical plan/TRD/Task states were not changed.

Highest verification: installed-package suites and filesystem parity. Fresh-host discovery and manual C01–C14 conversations remain unexercised; adoption does not supply that behavioral evidence.

Evidence: [inspection and exact manifest](adoption-inspection.json), [final results](adoption-results.json), [root tests](root-adoption-tests.txt), [Template tests](template-adoption-tests.txt), [mapping check](adoption-template-check.json), [read-only TRD validation](adoption-trd-validation.json).
