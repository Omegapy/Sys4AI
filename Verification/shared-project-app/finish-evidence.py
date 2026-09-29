"""Consolidate observed evidence without changing canonical plan/Task state."""
from pathlib import Path
import json
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
read = lambda name: json.loads((OUT / name).read_text())
def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')
now = datetime.now(timezone.utc).isoformat()
delivery = read('final-delivery.json')
assert delivery['status'] == 'verified'
assert read('final-preservation.json')['status'] == 'preserved'
build_id = delivery['build_id']

findings = {
1: ('One shared build serves the depot and alternate project; invalid optional ontology does not block alternate Home.', 'final-alternate-project.log final-delivery.json browser-smoke.md'),
2: ('Primary identity is root-bound; optional identity failure stays local.', 'reader-results.json final-alternate-project.log browser-smoke.md'),
3: ('Root purpose, scope and audience are reviewed; alternate content differs and missing sections remain gaps.', 'home-content-review.json reader-results.json browser-smoke.md'),
4: ('Start here resolves to the permitted README; destinations explain their reading purpose.', 'home-content-review.json browser-smoke.md'),
5: ('Permitted source handles open correct bounded text and reject arbitrary paths.', 'reader-results.json browser-smoke.md'),
6: ('Attention uses recorded issues/next steps, source status and observation time; partial coverage remains visible.', 'reader-results.json browser-smoke.md'),
7: ('Home and help copy were inspected against their sources; errors describe effect and next step.', 'home-content-review.json browser-smoke.md'),
8: ('Reviewed text and source digests are checked; drift flags review and revoked source permissions withhold content.', 'reader-results.json home-content-review.json'),
9: ('Common navigation, Back/Forward, source links, keyboard focus, narrow layout and 125% text were observed.', 'browser-smoke.md root-layout-adoption.json'),
10: ('Existing Knowledge views run within the common shell and retain source classifications.', 'transport-results.json final-package-service.log browser-smoke.md'),
11: ('Readable relationship lists and the map share directed/labeled data; unselected processes are explicit.', 'browser-smoke.md frontend-results.json'),
12: ('Memory retains historical finding, applicability, evidence and lifecycle under its existing owner/corpus.', 'reader-results.json browser-smoke.md'),
13: ('Canonical Task fields and latest public response metadata are projected; bounded plan history remains separate.', 'history-projection-results.json browser-smoke.md'),
14: ('TRD approval, plan state, static roles and runtime observations retain separate meanings.', 'history-projection-results.json reader-results.json browser-smoke.md'),
15: ('Source versions are current digests; unavailable history is labeled and copied references contain no bootstrap authority.', 'history-projection-results.json frontend-results.json browser-smoke.md'),
16: ('Bounded lexical search covers permitted owners and distinguishes partial/failed coverage from no matches.', 'reader-results.json final-package-service.log browser-smoke.md'),
17: ('Health projects existing static configuration and recorded notices with disabled/unavailable/not-checked distinctions.', 'reader-results.json browser-smoke.md'),
18: ('Installed skills and roles expose purpose/inputs/outputs/limits; help and copy controls describe actual effects.', 'reader-results.json frontend-results.json browser-smoke.md'),
19: ('Independent Home survives invalid optional knowledge; mandatory package/root failures have setup guidance.', 'reader-results.json transport-results.json final-alternate-project.log'),
20: ('Reading leaves governed baseline bytes and modes unchanged; only documented transient state changes.', 'final-preservation.json final-alternate-project.log browser-smoke.md'),
21: ('Fixed root/source selection, no-follow reads, exact owner bindings and excluded collaboration/child content retain boundaries.', 'reader-results.json transport-results.json final-alternate-project.log'),
22: ('Literal rendering, revoked/late result rejection and unchanged Host/Origin/CSRF checks pass.', 'frontend-results.json reader-results.json final-alternate-project.log'),
23: ('Prepared local package starts without builds, installers, depot service or optional backends; setup fallback is static.', 'final-alternate-project.log final-package-service.log browser-smoke.md'),
24: ('The actual macOS launcher resolves this root and opens/reopens Home; missing-runtime guidance is an independent HTML asset.', 'transport-results.json browser-smoke.md final-delivery.json'),
25: ('Session revocation, authenticated same-project reopen and owned stop are distinct and observed.', 'transport-results.json final-alternate-project.log browser-smoke.md'),
26: ('Neutral Template and v14 setup distribute the same reviewed package without depot records or runtime state.', 'final-package-initializer.log final-delivery.json template-check.json'),
27: ('Selected additive adoption preserves old editions/custom content, refuses modified packages and checks frozen recovery.', 'initializer-results.json final-package-initializer.log root-adoption.json root-layout-adoption.json final-preservation.json'),
28: ('Existing standalone Knowledge and CLI launch remain usable; app integration reuses existing read-only semantics.', 'transport-results.json final-package-service.log browser-smoke.md'),
29: ('Checks are reused across requirements; focused reruns address concrete integration/history/layout/package risks.', 'focused-results.json browser-smoke.md'),
30: ('No voice, dedicated screen-reader, compatibility matrix, benchmark, stress or native-agent validation campaign ran.', 'focused-results.json browser-smoke.md'),
31: ('Build, commands, exact destinations, requirement/artifact traceability and unexercised limits are documented.', 'final-delivery.json artifact-traceability.json final-preservation.json RELEASE.md'),
}

save('focused-results.json', {
    'observed_at': now, 'status': 'passed', 'final_build_id': build_id,
    'checks': [
        {'receipt': 'history-projection-results.json', 'level': 'six focused reader tests and actual canonical-owner reads', 'reason': 'Novel bounded owner/provenance/access behavior and a discovered history projection gap.'},
        {'receipt': 'transport-results.json', 'level': 'three novel service cases and one affected shared-Knowledge recheck', 'reason': 'New app routes, ownership handshake, session revocation and stop.'},
        {'receipt': 'frontend-results.json', 'level': 'focused frontend checks', 'reason': 'New session/client/rendering integration.'},
        {'receipt': 'final-package-service.log', 'level': 'one combined test, 11.620 seconds', 'reason': 'Validate produced package for retained standalone reader, embedded Knowledge/search and real CLI launch/reopen/stop.'},
        {'receipt': 'final-package-initializer.log', 'level': 'one combined fixture, 37.244 seconds', 'reason': 'Validate reviewed package through create/prepare/adopt/customization/refusal/interruption/recovery boundaries.'},
        {'receipt': 'final-alternate-project.log', 'level': 'one combined test, 4.190 seconds', 'reason': 'Bind alternate project content and optional failure/security behavior to the final post-layout package.'},
        {'receipt': 'production-build.json', 'level': 'strict TypeScript, production Vite build and runtime publisher', 'reason': 'Required runtime delivery; repeated only for observed narrow overflow correction.'},
        {'receipt': 'browser-smoke.md', 'level': 'actual macOS Finder/Chrome observation', 'reason': 'Changed integrated user flow and observed layout defect.'},
        {'receipt': 'final-delivery.json', 'level': 'exact source/asset/mode/Template/static comparison', 'reason': 'Selected adoption and preservation boundary.'},
    ],
    'evidence_reuse': 'The last build-input difference is only src/styles.css. Existing reader/frontend/transport logic evidence and initializer transaction evidence remain applicable. Final static inventory and one alternate-project service fixture validate the resulting package; the main browser journey was not rerun wholesale.',
    'excluded_campaigns': ['historical Explorer release matrix', 'voice or speech', 'dedicated screen-reader testing', 'full WCAG certification', 'broad browser/platform compatibility', 'benchmarks or stress', 'native-agent validation pilots', 'unselected real-project adoption'],
})

old = read('build-results.json')
if old['build_id'] != build_id:
    save('build-results-before-layout.json', old)
    old.update(build_id=build_id, manifest_sha256=delivery['manifest_sha256'], source_inputs_verified=47,
        correction='Observed narrow result-row overflow; only src/styles.css changed among the 47 build inputs.',
        evidence='production-build.json and root-layout-adoption.json')
    save('build-results.json', old)

audit = read('acceptance-audit.json')
trace = read('artifact-traceability.json')
audit.update(observed_at=now, purpose='Final execution acceptance against approved criteria. This evidence does not mutate canonical plan or Task state.', status='verified', build_id=build_id)
audit['available_evidence'] = sorted({f for _, files in findings.values() for f in files.split()})
for row in audit['requirements']:
    n = int(row['requirement_id'][4:])
    finding, files = findings[n]
    row.update(completion='verified', finding=finding, evidence=files.split(), remaining_gates=[],
        delivered_artifacts=[p['path'] for p in trace['product_artifacts'] if row['requirement_id'] in p['requirement_ids']])
plan = json.loads((ROOT / 'Implementation_Plans/Plan_shared-project-app-homepage-and-knowledge-integration_2026-09-29_F690CD02/plan.json').read_text())
task_evidence = {
1: ['BASELINE.md', 'final-preservation.json'], 2: ['home-content-review.json', 'reader-results.json'],
3: ['transport-results.json', 'final-alternate-project.log'], 4: ['history-projection-results.json'],
5: ['reader-results.json', 'final-package-service.log', 'browser-smoke.md'], 6: ['reader-results.json', 'browser-smoke.md'],
7: ['reader-results.json', 'browser-smoke.md'], 8: ['frontend-results.json', 'browser-smoke.md'],
9: ['home-content-review.json', 'browser-smoke.md'], 10: ['history-projection-results.json', 'browser-smoke.md'],
11: ['transport-results.json', 'browser-smoke.md'], 12: ['transport-results.json', 'browser-smoke.md'],
13: ['production-build.json', 'final-delivery.json'], 14: ['template-check.json', 'final-delivery.json'],
15: ['final-package-initializer.log', 'initializer-results.json'], 16: ['root-adoption.json', 'root-layout-adoption.json', 'final-delivery.json'],
17: ['focused-results.json'], 18: ['browser-smoke.md'], 19: ['RELEASE.md', 'artifact-traceability.json', 'final-preservation.json'],
}
audit['execution_task_results'] = [{'task_id': t['task_id'], 'title': t['title'], 'requirement_ids': t['requirement_ids'],
    'acceptance_criteria': t['acceptance_criteria'], 'completion': 'verified', 'evidence': task_evidence[int(t['task_id'][5:])]} for t in plan['tasks']]
audit['canonical_state'] = {'plan_status': plan['status'], 'plan_revision': plan['revision'], 'mutation': 'none', 'task_execution': 'Native goal with bounded implementation workers; no canonical Task activation.'}
save('acceptance-audit.json', audit)

lines = [
'# Shared Project app delivery', '',
'Implemented PLAN-20260929-F690CD02 revision 3 against TRD-20260928-92C32D18 revision 2. Home now opens independently of optional ontology, with reviewed project-owned explanations, Work, the existing Knowledge Explorer, lexical search, source previews, health and help in one local app.', '',
'## Delivered package', '',
f'- Build: `{build_id}`.',
f'- Runtime manifest SHA-256: `{delivery["manifest_sha256"]}`.',
'- Reusable source: `SKILLS-depo/ontology/`, the app wire schema, selected initializer changes and Template guidance/mappings.',
'- Template: current through its owner updater, with neutral Home content and an executable launcher. The final v14 static starter inventory validates 554 files.',
'- Depot root: selected adoption plus a recorded 11-file layout/build correction. The combined final manifest covers 54 destinations, including retired chunks. Forty-seven pre-existing installed/source differences remain preserved.',
'- Existing guard remains enabled with coherent public guard-repair bindings. Existing installed-file modes were preserved; the new launcher is 0755.',
'- Existing Template watcher restored, running, ready and current. No real child project was adopted.', '',
'Double-click [Launch Project.command](../../Launch%20Project.command) in Finder. See [operations](../../.agents/skills/ontology/references/project-app-operations.md) for the actual launch, owned stop, selected adoption and recovery commands. [Project App Setup.html](../../Project%20App%20Setup.html) remains readable when the runtime is missing.', '',
'The user approved restoration of the existing locked build dependencies. `npm ci --ignore-scripts --no-audit --no-fund` ran only in a temporary build directory; the lock stayed unchanged and no dependency versions were upgraded. Strict TypeScript/Vite build and runtime publication passed. Launch itself installs or builds nothing.', '',
'## Verification and preservation', '',
'Highest verification: a reviewed production package delivered to source/Template/root, focused runtime and initializer fixtures, and an actual Finder/Chrome journey. [Focused results](focused-results.json) explains each check and rerun. [Browser observations](browser-smoke.md) distinguish the main journey from the final CSS correction; only `src/styles.css` changed among the 47 build inputs. The narrow overflow was fixed, the final alternate-project service check passed, and final Home/keyboard/text-enlargement checks passed.', '',
'[Final preservation](final-preservation.json) confirms all 9,866 protected baseline entries retain their hashes/modes, including Tasks, TRDs, plan records, memory, ontology, roles, registry, the protected Mathematics project and the two pre-existing tracked index edits. Four operation-owned guard receipts and two separately inspected session catch-up events are accounted for. App-owned private session files are transient and excluded from delivery; they must not be staged. The Git index was not changed.', '',
'[Final delivery](final-delivery.json) binds exact current bytes and modes. [Artifact traceability](artifact-traceability.json) maps every changed product artifact back to requirements and explains consolidated filenames. [Acceptance audit](acceptance-audit.json) preserves all 31 criteria and all 19 execution work items with evidence.', '',
'## Requirement evidence', '',
'| Requirement | Delivered behavior and evidence |',
'| --- | --- |',
]
for n, (finding, files) in findings.items():
    refs = ', '.join(f'[{f}]({f})' for f in files.split())
    lines.append(f'| REQ-{n:03d} | {finding} {refs} |')
lines += ['', '## Boundaries', '',
'The native goal implementation and canonical managed records remain separate. The plan record is still `ready`, revision 3, and its tasks remain in their pre-execution tracked states because no explicit plan-management operation was invoked. This report supplies implementation evidence without rewriting approval/history. Existing unrelated awaiting-user Tasks were not activated or repaired.', '',
'New-project creation, first preparation and selected existing-project adoption were exercised in disposable fixtures. No other real product was updated. No Git commit/push, deployment or external publication occurred. Standalone Explorer compatibility was checked through the focused service/CLI fixture; the older full-release qualification was not rerun. No voice/audio, screen-reader certification, broad compatibility, benchmark, stress or native-agent validation campaign ran.', '',
'The root ontology has no selected processes, and an existing SPECS binding is stale; the app reports those source conditions accurately. Memory and Work can report partial coverage under their owner limits. Browsing repairs none of them. The final owned reader remains open for use; its Stop app control affects only that reader.', '',
]
(OUT / 'RELEASE.md').write_text('\n'.join(lines))

progress = OUT / 'PROGRESS.md'
original = progress.read_text()
if not original.startswith('# Project app implementation — completed'):
    (OUT / 'PROGRESS-before-approval.md').write_text(original)
progress.write_text(f'''# Project app implementation — completed

The user approved exact locked dependency restoration. The strict production build, runtime publication, Template update and selected root adoption are complete. Final build: `{build_id}`.

The integrated browser journey passed after correcting one narrow-layout overflow. Focused owner, frontend, transport and initializer checks passed. Final static/source comparisons and all 9,866 protected-entry comparisons passed. The original Template watcher is restored, running and current; the final Home is open.

[RELEASE.md](RELEASE.md) is the current delivery record. [acceptance-audit.json](acceptance-audit.json) maps all 31 criteria and 19 execution work items to evidence. Canonical plan/TRD/Task state remains unchanged. No real child-project adoption or Git publication was performed.

The earlier missing-toolchain blocker and its consecutive-turn audit are retained in [PROGRESS-before-approval.md](PROGRESS-before-approval.md) as historical evidence. They no longer describe current execution status.
''')
for f in audit['available_evidence']:
    assert (OUT / f).is_file(), f
print(json.dumps({'requirements': len(audit['requirements']), 'tasks': len(audit['execution_task_results']), 'status': audit['status'], 'build_id': build_id}))
