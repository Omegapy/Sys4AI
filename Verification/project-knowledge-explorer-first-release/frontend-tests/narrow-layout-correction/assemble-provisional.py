"""Assemble the bounded provisional evidence, never mutate product or old records."""
import importlib.util
import json
from pathlib import Path

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).absolute().parent
APP = ROOT / 'SKILLS-depo/ontology/explorer'
PRIOR = OUT.parent / 'process-catalog-correction/final-v3'
M = ROOT / 'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
spec = importlib.util.spec_from_file_location('readonly_audit', PRIOR / 'audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

def write(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(raw) <= 250000
    with (OUT / name).open('xb') as f:
        f.write(raw)

def r(name):
    return a.ref(OUT / name)

def main():
    existing = a.tree(OUT)
    audit = a.load(OUT / 'current-audit.json')
    packet = a.load(M / 'frontend-narrow-repair-v4-input-packet-02.json')
    old_criteria = a.load(PRIOR / 'criterion-evidence.json')['criteria']
    baseline = M.parent / ('baseline_' + packet['baseline'] + '.json')
    assert a.ref(baseline)['sha256'] == packet['baseline']
    assert packet['criteria'] == a.load(baseline)['criteria'] == [c['criterion'] for c in old_criteria]
    manifest, build_id = audit['runtime_manifest'], audit['build_id']
    limits = [
        'Provisional corrected frontend only. Current SERVICE V4 verification, same-owner full29 FRONTEND input rebind/finalization and QUALIFICATION rebind remain mandatory before acceptance.',
        'Current headless151 runs prove 320 CSS-pixel behavior, wide/narrow transitions, both themes and reduced motion. Actual native substantial browser zoom on this changed build has not been exercised. Earlier native90 to200 to90 source/process/catalog observations belong to the prior build; native Map/List at200 remains unexercised. Text scaling is not native browser zoom.',
        'Theme Home/ArrowDown/Enter/Tab and alternate Space/ArrowUp/Enter/Tab in headless151 left Dark with zero change events. A minimal native select also made no change for the original sequence. This is separate observed diagnostic evidence, not keyboard-selection success, not an app-specific defect, and not Safari proof. No Theme-specific production change was made.',
        'Actual Safari keyboard behavior and VoiceOver/speech remain unobserved for this correction. DOM roles/focus and keyboard browser checks do not prove spoken output or full WCAG acceptance.',
        'Dense inner captions can crowd in the25-node/26-edge initial-fit Map. Exact List/canvas semantics and selected/peripheral label treatment do not establish every association is unobscured or human comprehension. Planned TASK-025 remains mandatory.',
        'Six focused unit groups exercise compiled UI methods with an explicit DOM double;20 existing groups use mocked network/DOM. The catalog deadline unit invokes a mocked timer callback. Earlier real catalog10s instrumentation remains historical:10,915ms was first request to Retry visible including subsequent headers, not a timer firing timestamp.',
        'The passive terminal-state modal regression is a mocked state-transition unit check; current browser14 exercises an actual explicit session close. Real expiry timing remains qualification work.',
        'Browser16 allows exactly three disposable fixture paths to change; it proves preservation of other paths, not every field within those three files. Other current browser fixtures remain unchanged.',
        'The53 browser groups are reported groups across five runs, including repeated bootstrap checks. They are not53 distinct requirements. No TASK023/024/025, root adoption, Template propagation, workbench retirement, publication or main Task completion is claimed.'
    ]
    checks = []
    for row in audit['unit_closure']:
        report = json.loads(a.load(ROOT / row['receipt']['path'])['stdout'])
        checks.append({**row, 'status': 'passed_current_compiled_input_closure', 'check_names': [x['name'] for x in report['checks']]})
    for row in audit['browser_closure']:
        report = a.load(ROOT / row['report']['path'])
        checks.append({**row, 'status': 'passed_current_production_bytes', 'actual_executor': '/root', 'browser': report['browser'], 'check_names': [x['name'] for x in report['checks']], 'qualification': report.get('qualification'), 'fixture_scope': a.load(ROOT / row['attribution']['path'])['fixture_qualification']})
    checks.extend([
        {'id': 'build03', 'status': 'passed', 'receipt': r('build-03.json'), 'inputs': r('build-inputs-03.json'), 'dependency_admission': r('build01-dependency-admission.json'), 'post_build_audit': r('post-build-audit-03.json'), 'qualification': 'Strict typecheck/build, accepted runtime packaging and manifest-last governed source-asset transfer. Toolchain/pins unchanged.'},
        {'id': 'current_closure', 'status': 'passed', 'receipt': r('current-audit.json'), 'runtime': r('live-runtime-current-raw.json'), 'evolution': r('current-input-evolution.json'), 'preservation': r('preservation-current.json'), 'qualification': 'Fresh no-follow single-link stable descriptor/hash/size audit of direct current inputs; no new browser/build/test execution during evidence assembly.'}
    ])
    foundation = next(x for x in a.load(PRIOR / 'current-checks.json')['checks'] if x['id'] == 'accepted_foundations')
    a.verify(foundation['receipt']);a.verify(foundation['delivery'])
    checks.append(foundation)
    write('current-checks.json', {'status': 'current_checks_bound_for_provisional_review', 'build_id': build_id, 'runtime_manifest': manifest, 'unit_groups': {'focused': 6, 'existing': 20}, 'actual_browser_groups': 53, 'actual_browser_runs': 5, 'theme_diagnostic_excluded': True, 'checks': checks, 'limits': limits})

    # Complete the preserved failure03 copy without changing its original report.
    folder = OUT / 'host-03'
    receipt = a.load(folder / 'receipt.json')
    images = []
    for row in receipt['images']:
        dest = folder / Path(row['path']).name
        with dest.open('xb') as f:
            f.write(a.verify(row))
        images.append({'original': row, 'copy': a.ref(dest)})
    write('host-03/attribution.json', {'actual_executor': '/root', 'original_receipt': {'path': '/private/tmp/explorer-narrow-v4-host-edi2zktz/receipt.json', 'sha256': a.ref(folder / 'receipt.json')['sha256']}, 'receipt': a.ref(folder / 'receipt.json'), 'report': a.ref(folder / 'stdout.json'), 'status': 'failed_historical', 'images': images, 'diagnosis': 'Five earlier groups passed. Source action could target a disabled pending entry because the old readiness selector matched retained content; no source HTTP was observed. Successor strict current-entry and active-enabled-target waits resolved this test setup gap. No production source-reading change was made to satisfy this failure.'})
    historical = []
    executed = {2: ('failed', 'Immediate wide resize assertion preceded responsive readiness; settled same Theme-node focus subsequently passed.'), 3: ('failed', 'Old pending/retained-entry selector and unchecked disabled control could send Enter to heading; successor requires actual admitted current entry and target.'), 5: ('failed', 'First ten behaviors passed. Assumed native key sequence result was not observed; successor records actual value/events and separates unresolved Theme diagnostic.'), 8: ('failed', 'First ten behaviors passed. Same-fragment navigation did not guarantee a fresh renderer request; successor forces a new document and asserts actual import abort.'), 9: ('passed_historical_build02', 'All13 narrow groups passed; Theme no-selection observation remained separate. Product changed afterward for actual session-close defect.'), 13: ('failed_product_defect', 'Actual close left modal open, BODY focus without visible box, closed status outside modal/inert. Corrected in build03; current14 passes actual visible status focus.')}
    skipped = {1: 'No external tool pins; preserved before root execution.', 4: 'Current-entry and resize readiness guards still incomplete; never released.', 6: 'Theme diagnostic preparation superseded before release.', 7: 'Native popup intermediate value overconstraint removed in successor before release.', 10: 'Broad build02 preparation superseded by actual session-close correction; never executed.', 11: 'Bounds build02 preparation superseded; never executed.', 12: 'Neutral build02 preparation superseded; never executed.'}
    for number in range(1, 19):
        job = a.load(OUT / f'host-browser-job-{number:02}.json')
        pinned = a.verify(job['manifest'])
        assert pinned == a.read(OUT / f'stage-browser-{number:02}-inputs.json')
        rows = json.loads(pinned)['files']
        for row in rows:
            a.verify(row, Path(job['stage']))
        item = {'job_number': number, 'job': r(f'host-browser-job-{number:02}.json'), 'inputs': r(f'stage-browser-{number:02}-inputs.json'), 'stage': job['stage'], 'stage_file_count': len(rows), 'scope_of_verification': 'Pinned stage-relative paths verified against this exact stage; historical stage paths are not current-live source bindings.'}
        if number in executed:
            item.update(status=executed[number][0], disposition=executed[number][1], report=r(f'host-{number:02}/stdout.json'), receipt=r(f'host-{number:02}/receipt.json'), attribution=r(f'host-{number:02}/attribution.json'))
        elif number in skipped:
            item.update(status='prepared_unexecuted', disposition=skipped[number])
        else:
            item.update(status='passed_current_build03', report=r(f'host-{number:02}/stdout.json'), receipt=r(f'host-{number:02}/receipt.json'), attribution=r(f'host-{number:02}/attribution.json'))
        historical.append(item)
    write('history-and-dispositions.json', {'status': 'preserved', 'jobs': historical, 'prior_builds': [r('build-01.json'), r('build-02.json')], 'prior_units': [r(f'unit-{n:02}.json') for n in range(1, 6)], 'root_wrapper_preexecution_observation': 'Manager reported one earlier literal wrapper admission failure before driver execution. No driver/raw run was produced and no execution is counted for it.', 'earlier_frontend_history': a.ref(PRIOR / 'history-review.json') if (PRIOR / 'history-review.json').exists() else a.ref(PRIOR / 'result.json'), 'preserved_prior_inventory': r('preservation-before.json'), 'meaning': 'All earlier319 frontend evidence files are unchanged; old passes/failures and unexecuted preparations retain their original scope. No historical product-level result is relabeled current.'})

    write('native-safari-followup-prepared.json', {
        'status': 'prepared_only_not_executed', 'owner': 'Manager-reviewed primary host native Safari follow-up', 'build_id': build_id, 'runtime_manifest': manifest,
        'inputs': [r('current-audit.json'), r('host-15/stdout.json'), r('host-14/stdout.json'), a.ref(APP / 'src/app.ts'), a.ref(APP / 'src/sources.ts'), a.ref(APP / 'src/styles.css'), r('fixture.py')],
        'purpose': 'Short native check of the new drawer/details integration and unresolved exact Theme key/value discrepancy. No new native harness or launcher is introduced.',
        'gate': 'Manager must reconcile stopped provisional delivery, refresh current SERVICE V4/full frontend dependency binding, and review the exact native session/fixture/tool prechecks before execution. Use its existing authorized isolated native Safari OS-open protocol with current runtime, never stale V3 assets or system Chrome.',
        'bounds': {'maximum_active_seconds': 360, 'maximum_clean_content_screenshots': 4, 'maximum_safe_report_bytes': 250000, 'no_unbounded_retries': True},
        'preconditions': ['Record actual Safari version, original window/zoom and Theme; fresh isolated exact approved synthetic fixture only.', 'Verify all current authored/runtime pins, exact selected fixture IDs and clean fragment before any content capture. Keep private launch/bootstrap URL in memory; no token, cookie, URL, raw navigation error, trace/HAR or browser-chrome screenshot.', 'Do not assume a320CSS viewport from physical pixels or a narrow window. Record actual viewport and only assert widths actually reached; use genuine browser zoom for any zoom assertion.'],
        'observations': [
            'Keyboard-open navigation from visible toggle; record labeled modal, focus on visible Close navigation, Escape/Close return, and Tab destination activation closing drawer into visible reading focus. Expand/scroll Help, close and reopen to confirm Close control is visible.',
            'With actual Theme control focused, widen/narrow and record whether same control or deliberate visible fallback owns focus. Do not infer completion from a resize request alone.',
            'In Map/List at narrow layout, keyboard dismiss/reopen selected details. Verify selected stable ID, safe route, returned scope and List remain intact. Read source, hide parent details, close source and verify exact trigger is re-exposed visibly. Map/List native200percent remains a separately required observation unless actually reached and checked.',
            'Focus native Theme; record initial value/appearance and exact Home, ArrowDown, Enter sequence, then separately record Tab commit. Record visible menu behavior, every actual key, final value and resolved appearance. If unchanged, allow only one bounded native menu selection attempt from a known recorded value with its actual keys. A programmatic option/value/AX selection is not native keyboard proof; unchanged minimal-control behavior is diagnostic only.',
            'Close reading session from navigation; record modal closed, visible meaningful focus and readable closed status. This establishes visual focus/status only, not speech.'
        ],
        'stop_and_cleanup': ['Stop on a reproducible product defect and return exact safe observations; do not silently patch or weaken a test.', 'Restore exact original Theme, zoom and window where modified; close only owned page/session/service/fixture/profile, record owned-process cleanup and verify scoped fixture/tool/runtime preservation. Leave watcher held and qualification stopped until their owner gates.'],
        'not_claimed': ['Actual execution of this packet', 'Safari success', 'Theme native keyboard selection', 'VoiceOver or spoken announcements', 'Human comprehension', 'Full WCAG or release acceptance', 'TASK023/024/025 execution']
    })

    check_map = {c['id']: c for c in checks}
    ids = [
        ['existing_unit','browser16'], ['existing_unit','browser16','browser15'], ['browser16','focused_unit','browser15'], ['existing_unit','build03'],
        ['browser16','browser18','browser15'], ['browser18','browser16'], ['existing_unit','browser16','browser15'], ['existing_unit','browser16'], ['existing_unit','browser18','browser17'],
        ['browser16'], ['browser16','existing_unit'], ['browser16','browser15','focused_unit'], ['existing_unit','browser16'], ['browser16'], ['build03','browser16'],
        ['browser16','browser17'], ['browser15','browser16','browser17'], ['browser15','browser16'], ['browser16','browser15'], ['browser15','browser17'], ['browser16','browser17'], ['build03','browser16'],
        ['existing_unit','browser14','browser15','browser16','browser17','focused_unit'], ['browser18','browser17'], ['browser15','browser16','browser18','focused_unit'], ['browser16','browser15'], ['browser16'], ['browser15','browser16','browser18','existing_unit'], ['browser15','browser16','browser17']
    ]
    explanations = [
        'Pure foundations are unchanged; current20 units cover abort-insensitive response/session/discovery/catalog identity races. Current production refresh and retained-context flows pass; details dismissal retains state/model/history and late entry responses do not reopen it.',
        'Current exact route hydration/fragment erasure unit checks and production new-tab/copy-route flows pass. Current narrow jobs positively assert fragment removal before capture. No new route/history/storage field was added.',
        'Actual selection creates one history item and retains camera; current snapshot conflict/atomic refresh update retained IDs and remove obsolete category scope. Details presentation creates no history/model/state transition.',
        'ReadClient remains the single fetch owner; unchanged finite independent catalog and source discovery admission is covered by current20 unit groups. New drawer/details methods perform presentation and emit existing intentions only.',
        'Current authenticated first screen exposes Overview, Terms, Processes and Map with persistent labeled search and no initial canvas. Narrow navigation is an actual labeled keyboard-operable native dialog, with reading content outside it.',
        'Current normal and neutral fixtures use recorded project purpose/starting IDs. Neutral Overview explains imported vocabulary and retains categories/search; no local process catalog is invented.',
        'Current unit regressions cover autocomplete generations, initial ArrowUp/Down, Escape and duplicate identity labels. Current production explicit search and actual keyboard drawer/search navigation pass; query is preserved.',
        'Current production search preserves two exact Alignment identities with recorded display content. Current20 units cover exact duplicate autocomplete/catalog IDs, recorded non-starting names, truthful label truncation/full-entry access and stable focused links.',
        'Current empty search retains query/clear actions. High-degree continuation stops at tighter display limits and rereads unconsumed pages; shared-content refusal is rejected. No totals or exhaustive absence are invented.',
        'Current browser16 verifies exact definition/aliases/scope/examples/non-examples, historical replacement and independent authority warning; long definition preserves66023UTF8bytes over3pages. Changed source freshness remains distinct. Earlier15011byte full-catalog-name browser proof is historical; unchanged catalog/entry code and current unit closure are explicit.',
        'Current production List/canvas and entry assertions inspect exact member IDs, direction, qualifiers and descriptors. Long qualifiers preserve44066UTF8bytes over2pages; current lossless endpoint unit checks reject gaps/duplicates and avoid unsafe-number rounding.',
        'Current browser16 verifies exact escaped source reading and heading focus. Browser15 hides parent Map details while source remains open, then source close re-exposes and visibly focuses the exact original trigger. No current native200percent reading claim is made.',
        'Current ordered process/direct binding and later-field-owner discovery flows preserve exact selected support. Current units cover bounded source discovery windows and independent recorded-name catalog admission. No unsupported field or ordering is manufactured.',
        'Current production unordered-process check asserts the complete required sentence verbatim.',
        'Process pages remain read-only renderers of recorded fields/order. Current source/toolchain correspondence preserves the single existing graph library; no execution, extra dependency, protocol or authoring was added.',
        'Current actual DOM/canvas comparison verifies exact nodes/relations, endpoints, direction, qualifiers, sources, classifications, warnings, filters and returned scope. Budget/incomplete metadata stays distinct from completeness.',
        'Current browser15 positively blocks one renderer import in a fresh document. Keyboard More connections appends exact returned scope, then different Focus here replaces it; List entry/source/details remain usable. Current canvas-loss/layout-refusal cases retain List.',
        'Current selection/scope/history/filter and copied explicit focus/selection flows pass. Dismiss/reopen retains exact List DOM nodes and current renderer/camera/returned identities.',
        'Map remains lazy, starts from exact focus or visible picker and bounded one-step data. Selection updates details without moving camera; ID-less Map after failed entry now ignores a detached retained heading and focuses visible Choose a focus.',
        'Current keyboard Focus here replaces scope and More connections appends it. High-degree continuation respects tighter service/display limits; injected layout deadline retains List. Existing renderer positions and ceiling policy are unchanged.',
        'Current production parity covers exact parallel IDs, self-loop, direction, qualifiers, genuine relation-as-endpoint identity and retained-edge retargeting. The unchanged preset renderer preserves semantic data; dense-fit label crowding remains a stated human-comprehension qualification.',
        'Renderer source remains unchanged and consumes model/intentions without fetch. Current authored legend retains the exact guidance and visible focus/expand controls; generated runtime is bound to this source.',
        'Current production conflict/refresh, blocked import, canvas loss and layout refusal retain coherent reading and useful evidence/List. Actual narrow session close exposes visible focused status; passive disconnect and later-route focus ownership have focused unit coverage. Actual expiry timing is not claimed.',
        'Current neutral job verifies complete empty ActionType scope before the exact absence message. Current bounded/high-degree paths disclose refusal/incomplete state and continuation separately.',
        'Current actual320CSSpx drawer, details dismiss/reopen, both resize directions, source-trigger return, light/dark and reduced-motion checks pass. Native substantial browser zoom and Safari behavior on this changed build remain pending the prepared follow-up/current integration gates; previous native90to200to90 and text-sizing results are historical and are not substituted.',
        'Current repeated Back/Forward restores same-focus filter/selection context and cancels pending focused-search preview. Node selection pushes once; camera changes do not spam history. Presentation-only details dismissal leaves history intact.',
        'Current Terms/Map and copied relation-subject route checks preserve exact identity, including relation-kind focus endpoints. Authenticated ordinary new-tab entry succeeds; copied routes contain no credential material.',
        'Current storage checks and neutral light/system/reset plus dark/reduced-motion flow show presentation-only preferences and no persisted knowledge/source bodies. Native Theme keyboard selection did not change in the separate headless diagnostic; no success or app defect is inferred.',
        'Current production exact Map/List IDs, direction, qualifiers, sources, warnings, filters, selection and scope comparisons pass. Fresh blocked-renderer, lost-canvas and refused-layout runs preserve substantive keyboard List entry/evidence/focus/expand actions and phone details access.'
    ]
    criteria = []
    for index, old in enumerate(old_criteria, 1):
        selected = ids[index - 1] + ['current_closure']
        direct = []
        for ident in selected:
            c = check_map[ident]
            direct.extend(c[k] for k in ('report','receipt') if k in c)
        direct = list({(v['path'],v['sha256']):v for v in direct}.values())
        criteria.append({'index': index, 'task': old['task'], 'criterion': packet['criteria'][index - 1], 'status': 'narrow_behavior_verified_native_zoom_and_Safari_followup_pending' if index == 25 else 'current_implementation_and_scoped_evidence_ready_pending_integration_gates', 'explanation': explanations[index - 1], 'check_ids': selected, 'implementation': [a.ref(ROOT / row['path']) for row in old['implementation']], 'direct_current_evidence': direct, 'current_runtime_manifest': manifest, 'acceptance_boundary': 'Provisional only; SERVICE V4 and final FRONTEND/QUALIFICATION gates remain.'})
    write('criterion-evidence.json', {'assignment_id': 'FRONTEND_WORKER_G3', 'baseline': packet['baseline'], 'round': 4, 'criteria_count': 29, 'criteria_verbatim_and_original_order': True, 'criteria': criteria, 'current_checks': r('current-checks.json'), 'limits': limits, 'manager_acceptance_separate': True})
    prior_context = a.load(PRIOR / 'current-context.json')
    write('current-context.json', {'assignment_id': 'FRONTEND_WORKER_G3', 'native_id': '/root/explorer_manager_g3/frontend_worker', 'app_thread_id': '01a0c00b-e55b-74f1-b6dc-d83eb128e100', 'baseline': packet['baseline'], 'round': 4, 'canonical_activation_reported_by_manager': 'Task217 EV_FRONTEND_NARROW_REPAIR_V4_INPUTS_02; same owner/settings activated; no helper replayed', 'packet': a.ref(M / 'frontend-narrow-repair-v4-input-packet-02.json'), 'input_admission': r('input-admission.json'), 'current_evolution': r('current-input-evolution.json'), 'original_baseline': a.ref(baseline), 'original_plan': prior_context['original_plan'], 'original_context_reference_record': a.ref(PRIOR / 'current-context.json'), 'prior_dependency_service_v3': {'status': 'previously_accepted_shared_runtime_now_changed_requires_v4', 'acceptance': a.ref(M / 'service-package-acceptance-v3.json')}, 'required_current_sequence': ['Manager provisional review and ownership reconciliation', 'Same original SERVICE owner current V4 package/session/bootstrap/native verification', 'Same FRONTEND owner full29 final input rebind and evidence-only finalization', 'QUALIFICATION current-dependency rebind and remaining original gates'], 'remaining_original_plan_gates': prior_context['remaining_original_plan_gates'], 'all49_requirements_36_acceptance_tests_33_tasks_eight_phases_preserved': True, 'watcher': 'Held/quiesced by root; this worker has no restoration authority. No Template propagation.', 'qualification': 'Stopped; no resume by this worker.', 'write_scope': packet['write_scope'], 'authority': packet['authority'], 'limits': limits})
    preservation = a.load(OUT / 'preservation-current.json')
    write('implementation-review-current.json', {'status': 'current_build03_reviewed_with_actual_focused_and_regression_evidence', 'changes': [x for x in preservation['product_changes'] if not x['path'].startswith('SKILLS-depo/ontology/explorer/assets/')], 'diff': r('authored-changes-current.patch'), 'behavior': ['Native navigation dialog below760CSSpx moves the existing navigation/Theme/help nodes, preserves visible focus through close/Escape/route/resize, and keeps project/search in header.', 'Phone selected details dismiss/reopen is local presentation only; normalized model, reading state, exact List nodes, camera, returned scope and history remain intact.', 'Source return callback re-exposes exact connected trigger; detached retained entry headings cannot intercept new Map picker focus.', 'Observed session-close modal defect is fixed by closing navigation before asynchronous close and focusing readable status without stealing later route/focus intent. Passive terminal notification closes navigation before hiding its focused session control.'], 'review_disposition': 'Only three authored UI files plus one new focused test and generated runtime changed. No API/foundation/service/schema/dependency/toolchain/Theme key-handler change.', 'current_tests': [r('unit-06.json'), r('unit-07.json'), r('current-checks.json')], 'actual_failure_and_resolution': [r('host-13/attribution.json'), r('host-14/attribution.json')], 'limits': limits})
    images = []
    for n in (14,15):
        images.extend(x['copy'] for x in a.load(OUT / f'host-{n:02}/attribution.json')['images'])
    write('visual-qualification-current.json', {'status': 'five_current_clean_content_PNGs_actually_viewed_by_frontend_worker', 'images': images, 'observations': ['Current closed-session PNG shows modal dismissed and the focused readable status below sticky header.', 'Closed narrow Overview keeps project/search/Open navigation compact and allocates remaining width to reading.', 'Navigation PNG shows Close navigation focus, vertical destinations and reachable native Theme/help content.', 'Light/dark selected-detail PNGs show Close selected details, readable focused entry heading and recorded fields below sticky header.'], 'qualification': 'These bounded images do not show every route, full graph association, long process/source at native200percent, Safari, spoken output or participant comprehension. Dense-map historical qualification remains.', 'historical_dense_map_image': a.ref(OUT.parent / 'screenshots-current/full-canvas.png'), 'native_followup': r('native-safari-followup-prepared.json')})
    write('output-manifest.json', {'status': 'current_direct_live_authored_test_runtime_refs', 'build_id': build_id, 'files': preservation['current_product_and_tests'], 'changed_product_files': preservation['product_changes'], 'runtime_manifest': manifest, 'all_runtime_members': audit['runtime_members'], 'oversized_runtime_members': [x for x in audit['runtime_members'] if x['bytes'] > 250000], 'oversized_policy': '434861-byte vendor is a runtime member, not a bounded evidence document. Its complete bytes are pinned by live manifest and checked no-follow/single-link/hash/size at every current gate; it is not truncated.', 'current_check_refs': [r('current-checks.json'),r('current-audit.json'),r('build-03.json'),r('unit-06.json'),r('unit-07.json')]})
    result = {'status': 'provisional_current_correction_ready_for_manager_review', 'assignment_id': 'FRONTEND_WORKER_G3', 'native_id': '/root/explorer_manager_g3/frontend_worker', 'baseline': packet['baseline'], 'round': 4, 'build_id': build_id, 'runtime_manifest': manifest, 'criteria_count': 29, 'outcome': 'The original narrow-navigation and dismissible phone Map-details gaps are implemented and current focused/regression checks pass. A new modal session-close defect found in actual browser13 is corrected and passes current browser14.', 'changed': 'Three UI files, one new frontend test and generated runtime; new evidence only in narrow-layout-correction.', 'unit_groups': {'focused': 6, 'existing': 20}, 'actual_browser_groups': 53, 'actual_browser_runs': 5, 'theme_observation_not_a_pass': True, 'highest_observed_verification': 'Primary-host actual pinned headless151 production execution, current source/runtime/stage/tool closure, and five reviewed clean content PNGs. This worker did not run a browser/listener.', 'criteria': r('criterion-evidence.json'), 'checks': r('current-checks.json'), 'context': r('current-context.json'), 'audit': r('current-audit.json'), 'history': r('history-and-dispositions.json'), 'review': r('implementation-review-current.json'), 'visual': r('visual-qualification-current.json'), 'native_followup': r('native-safari-followup-prepared.json'), 'limits': limits, 'main_task_complete': False, 'manager_acceptance_separate': True, 'next_gate': 'Stop writes; manager review, SERVICE V4 current shared-runtime verification, same-owner FRONTEND full29 final rebind, then QUALIFICATION current dependencies/remaining gates.'}
    write('result.json', result)
    handoff = f'''# Provisional narrow-layout correction

The two original REQ036 gaps now have a native narrow navigation drawer and dismissible/reopenable phone Map details. Details presentation preserves exact selection, List nodes, model, returned scope, camera and history. Source close re-exposes its exact trigger. The actual session-close modal defect discovered during this work is also fixed: navigation closes and the readable closed status receives visible focus. Passive terminal notification has a focused state-transition unit regression.

Current build: `{build_id}`. Runtime manifest SHA256: `{manifest['sha256']}`. Product remains in the reusable source collection; there was no active-root installation, Template propagation, Git publication or watcher change.

Current evidence consists of6 focused compiled-UI unit groups,20 existing compiled frontend groups, strict build/typecheck and53 reported actual headless151 behavior groups across five primary-host runs:14 session(1),15 narrow(13),16 advanced(28),17 bounds/recovery(4),18 neutral(7). Shared bootstrap checks repeat across runs. All current jobs have clean stage/tool/source/cleanup/CSP/error checks. Browser16 changes exactly three declared disposable fixture paths; the other four fixtures are unchanged. The complete current manifest includes the434861-byte vendor member.

`current-audit.json` binds28 build inputs,1001 live/staged dependency files and4 links, all5 runtime members, current unit/browser closures and preservation of all319 prior frontend evidence files. `current-input-evolution.json` records225 unchanged packet references and8 explicitly authorized source/runtime evolutions. `output-manifest.json` binds every current explorer product/test file. All29 baseline criteria remain verbatim and in original order in `criterion-evidence.json`.

The Theme native-key diagnostic is excluded from pass counts. Home/Down/Enter/Tab and Space/Up/Enter/Tab left Dark with no change events in headless151; the original sequence also made no change in a minimal native select. No Theme-specific product patch was justified. `native-safari-followup-prepared.json` provides a short bounded manager/host follow-up, prepared only and not executed.

Current320CSSpx, light/dark/system and reduced-motion evidence does not substitute for native substantial browser zoom. Prior90→200→90 process/catalog/source observations are historical after these app/runtime changes; native Map/List200 remains unexercised. Actual Safari, VoiceOver/speech and human comprehension are not claimed. Dense25-node/26-edge Map captions can still crowd; TASK025 remains mandatory. Passive disconnect unit evidence is not actual expiry timing. The five current PNGs cover narrow controls/details/status, not all release visuals.

Keep every old failure and preparation. Jobs01/04/06/07/10–12 were unexecuted. Actual02/03/05/08 failed with documented test readiness/keyboard/setup causes;09 passed on the prior build. Actual13 exposed the real close-session defect;14 is its current passing regression. `history-and-dispositions.json` preserves the exact reports, stages and distinctions. No historical stage-relative reference is treated as a current-live binding.

Next: manager reviews the stopped provisional package and reconciles ownership; the same SERVICE owner verifies current shared assets/session/bootstrap as V4; the same FRONTEND owner receives the refreshed full29 final binding; QUALIFICATION then receives current dependencies. Original TASK020–033 gates, all49 requirements and36 acceptance tests remain. Do not restart the held watcher or resume qualification from this handoff. No new Task, owner, model/effort, schema, dependency or public route/storage format was introduced.

After the final delivery write, this worker stops all writes and awaits the manager's normal follow-up. This is not main Task or TASK022 acceptance.
'''
    raw = handoff.encode();assert len(raw) <= 250000
    with (OUT / 'HANDOFF.md').open('xb') as f:
        f.write(raw)
    for row in existing:
        a.verify(row)
    write('assembly-preservation.json', {'status': 'passed', 'preexisting_correction_evidence_count': len(existing), 'references': existing, 'all_preexisting_correction_evidence_unchanged': True, 'assembler': a.ref(Path(__file__))})
    print(json.dumps({'status': 'assembled_pending_final_verification_and_delivery', 'criteria': r('criterion-evidence.json'), 'result': r('result.json'), 'native_followup': r('native-safari-followup-prepared.json')}))

if __name__ == '__main__':
    main()
