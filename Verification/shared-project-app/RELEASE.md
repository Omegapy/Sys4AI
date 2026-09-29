# Shared Project app delivery

Implemented PLAN-20260929-F690CD02 revision 3 against TRD-20260928-92C32D18 revision 2. Home now opens independently of optional ontology, with reviewed project-owned explanations, Work, the existing Knowledge Explorer, lexical search, source previews, health and help in one local app.

## Delivered package

- Build: `b587accf1f6f44cebac189ce58051bc3e533fd059bc510573ff84c0cddf4853d`.
- Runtime manifest SHA-256: `6a9bd886559a0c6f1945429fa3afdee2f168044308950e07eeebf4c7bdce7b6f`.
- Reusable source: `SKILLS-depo/ontology/`, the app wire schema, selected initializer changes and Template guidance/mappings.
- Template: current through its owner updater, with neutral Home content and an executable launcher. The final v14 static starter inventory validates 554 files.
- Depot root: selected adoption plus a recorded 11-file layout/build correction. The combined final manifest covers 54 destinations, including retired chunks. Forty-seven pre-existing installed/source differences remain preserved.
- Existing guard remains enabled with coherent public guard-repair bindings. Existing installed-file modes were preserved; the new launcher is 0755.
- Existing Template watcher restored, running, ready and current. No real child project was adopted.

Double-click [Launch Project.command](../../Launch%20Project.command) in Finder. See [operations](../../.agents/skills/ontology/references/project-app-operations.md) for the actual launch, owned stop, selected adoption and recovery commands. [Project App Setup.html](../../Project%20App%20Setup.html) remains readable when the runtime is missing.

The user approved restoration of the existing locked build dependencies. `npm ci --ignore-scripts --no-audit --no-fund` ran only in a temporary build directory; the lock stayed unchanged and no dependency versions were upgraded. Strict TypeScript/Vite build and runtime publication passed. Launch itself installs or builds nothing.

## Verification and preservation

Highest verification: a reviewed production package delivered to source/Template/root, focused runtime and initializer fixtures, and an actual Finder/Chrome journey. [Focused results](focused-results.json) explains each check and rerun. [Browser observations](browser-smoke.md) distinguish the main journey from the final CSS correction; only `src/styles.css` changed among the 47 build inputs. The narrow overflow was fixed, the final alternate-project service check passed, and final Home/keyboard/text-enlargement checks passed.

[Final preservation](final-preservation.json) confirms all 9,866 protected baseline entries retain their hashes/modes, including Tasks, TRDs, plan records, memory, ontology, roles, registry, the protected Mathematics project and the two pre-existing tracked index edits. Four operation-owned guard receipts and two separately inspected session catch-up events are accounted for. App-owned private session files are transient and excluded from delivery; they must not be staged. The Git index was not changed.

[Final delivery](final-delivery.json) binds exact current bytes and modes. [Artifact traceability](artifact-traceability.json) maps every changed product artifact back to requirements and explains consolidated filenames. [Acceptance audit](acceptance-audit.json) preserves all 31 criteria and all 19 execution work items with evidence.

## Requirement evidence

| Requirement | Delivered behavior and evidence |
| --- | --- |
| REQ-001 | One shared build serves the depot and alternate project; invalid optional ontology does not block alternate Home. [final-alternate-project.log](final-alternate-project.log), [final-delivery.json](final-delivery.json), [browser-smoke.md](browser-smoke.md) |
| REQ-002 | Primary identity is root-bound; optional identity failure stays local. [reader-results.json](reader-results.json), [final-alternate-project.log](final-alternate-project.log), [browser-smoke.md](browser-smoke.md) |
| REQ-003 | Root purpose, scope and audience are reviewed; alternate content differs and missing sections remain gaps. [home-content-review.json](home-content-review.json), [reader-results.json](reader-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-004 | Start here resolves to the permitted README; destinations explain their reading purpose. [home-content-review.json](home-content-review.json), [browser-smoke.md](browser-smoke.md) |
| REQ-005 | Permitted source handles open correct bounded text and reject arbitrary paths. [reader-results.json](reader-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-006 | Attention uses recorded issues/next steps, source status and observation time; partial coverage remains visible. [reader-results.json](reader-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-007 | Home and help copy were inspected against their sources; errors describe effect and next step. [home-content-review.json](home-content-review.json), [browser-smoke.md](browser-smoke.md) |
| REQ-008 | Reviewed text and source digests are checked; drift flags review and revoked source permissions withhold content. [reader-results.json](reader-results.json), [home-content-review.json](home-content-review.json) |
| REQ-009 | Common navigation, Back/Forward, source links, keyboard focus, narrow layout and 125% text were observed. [browser-smoke.md](browser-smoke.md), [root-layout-adoption.json](root-layout-adoption.json) |
| REQ-010 | Existing Knowledge views run within the common shell and retain source classifications. [transport-results.json](transport-results.json), [final-package-service.log](final-package-service.log), [browser-smoke.md](browser-smoke.md) |
| REQ-011 | Readable relationship lists and the map share directed/labeled data; unselected processes are explicit. [browser-smoke.md](browser-smoke.md), [frontend-results.json](frontend-results.json) |
| REQ-012 | Memory retains historical finding, applicability, evidence and lifecycle under its existing owner/corpus. [reader-results.json](reader-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-013 | Canonical Task fields and latest public response metadata are projected; bounded plan history remains separate. [history-projection-results.json](history-projection-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-014 | TRD approval, plan state, static roles and runtime observations retain separate meanings. [history-projection-results.json](history-projection-results.json), [reader-results.json](reader-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-015 | Source versions are current digests; unavailable history is labeled and copied references contain no bootstrap authority. [history-projection-results.json](history-projection-results.json), [frontend-results.json](frontend-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-016 | Bounded lexical search covers permitted owners and distinguishes partial/failed coverage from no matches. [reader-results.json](reader-results.json), [final-package-service.log](final-package-service.log), [browser-smoke.md](browser-smoke.md) |
| REQ-017 | Health projects existing static configuration and recorded notices with disabled/unavailable/not-checked distinctions. [reader-results.json](reader-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-018 | Installed skills and roles expose purpose/inputs/outputs/limits; help and copy controls describe actual effects. [reader-results.json](reader-results.json), [frontend-results.json](frontend-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-019 | Independent Home survives invalid optional knowledge; mandatory package/root failures have setup guidance. [reader-results.json](reader-results.json), [transport-results.json](transport-results.json), [final-alternate-project.log](final-alternate-project.log) |
| REQ-020 | Reading leaves governed baseline bytes and modes unchanged; only documented transient state changes. [final-preservation.json](final-preservation.json), [final-alternate-project.log](final-alternate-project.log), [browser-smoke.md](browser-smoke.md) |
| REQ-021 | Fixed root/source selection, no-follow reads, exact owner bindings and excluded collaboration/child content retain boundaries. [reader-results.json](reader-results.json), [transport-results.json](transport-results.json), [final-alternate-project.log](final-alternate-project.log) |
| REQ-022 | Literal rendering, revoked/late result rejection and unchanged Host/Origin/CSRF checks pass. [frontend-results.json](frontend-results.json), [reader-results.json](reader-results.json), [final-alternate-project.log](final-alternate-project.log) |
| REQ-023 | Prepared local package starts without builds, installers, depot service or optional backends; setup fallback is static. [final-alternate-project.log](final-alternate-project.log), [final-package-service.log](final-package-service.log), [browser-smoke.md](browser-smoke.md) |
| REQ-024 | The actual macOS launcher resolves this root and opens/reopens Home; missing-runtime guidance is an independent HTML asset. [transport-results.json](transport-results.json), [browser-smoke.md](browser-smoke.md), [final-delivery.json](final-delivery.json) |
| REQ-025 | Session revocation, authenticated same-project reopen and owned stop are distinct and observed. [transport-results.json](transport-results.json), [final-alternate-project.log](final-alternate-project.log), [browser-smoke.md](browser-smoke.md) |
| REQ-026 | Neutral Template and v14 setup distribute the same reviewed package without depot records or runtime state. [final-package-initializer.log](final-package-initializer.log), [final-delivery.json](final-delivery.json), [template-check.json](template-check.json) |
| REQ-027 | Selected additive adoption preserves old editions/custom content, refuses modified packages and checks frozen recovery. [initializer-results.json](initializer-results.json), [final-package-initializer.log](final-package-initializer.log), [root-adoption.json](root-adoption.json), [root-layout-adoption.json](root-layout-adoption.json), [final-preservation.json](final-preservation.json) |
| REQ-028 | Existing standalone Knowledge and CLI launch remain usable; app integration reuses existing read-only semantics. [transport-results.json](transport-results.json), [final-package-service.log](final-package-service.log), [browser-smoke.md](browser-smoke.md) |
| REQ-029 | Checks are reused across requirements; focused reruns address concrete integration/history/layout/package risks. [focused-results.json](focused-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-030 | No voice, dedicated screen-reader, compatibility matrix, benchmark, stress or native-agent validation campaign ran. [focused-results.json](focused-results.json), [browser-smoke.md](browser-smoke.md) |
| REQ-031 | Build, commands, exact destinations, requirement/artifact traceability and unexercised limits are documented. [final-delivery.json](final-delivery.json), [artifact-traceability.json](artifact-traceability.json), [final-preservation.json](final-preservation.json), [RELEASE.md](RELEASE.md) |

## Boundaries

The native goal implementation and canonical managed records remain separate. The plan record is still `ready`, revision 3, and its tasks remain in their pre-execution tracked states because no explicit plan-management operation was invoked. This report supplies implementation evidence without rewriting approval/history. Existing unrelated awaiting-user Tasks were not activated or repaired.

New-project creation, first preparation and selected existing-project adoption were exercised in disposable fixtures. No other real product was updated. No Git commit/push, deployment or external publication occurred. Standalone Explorer compatibility was checked through the focused service/CLI fixture; the older full-release qualification was not rerun. No voice/audio, screen-reader certification, broad compatibility, benchmark, stress or native-agent validation campaign ran.

The root ontology has no selected processes, and an existing SPECS binding is stale; the app reports those source conditions accurately. Memory and Work can report partial coverage under their owner limits. Browsing repairs none of them. The final owned reader remains open for use; its Stop app control affects only that reader.
