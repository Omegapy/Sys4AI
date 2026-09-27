"""Assemble final current evidence for manager review; all source inputs stay read-only."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).absolute().parent
NC = OUT.parent
S = ROOT / 'Verification/project-knowledge-explorer-first-release/service-tests/service-v4'
M = ROOT / 'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
spec = importlib.util.spec_from_file_location('readonly_audit', NC.parent / 'process-catalog-correction/final-v3/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

def write(name, obj):
    raw = (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(raw) <= 250000
    with (OUT / name).open('xb') as f:f.write(raw)

def ref(name):return a.ref(OUT / name)

def main():
    packet = a.load(M/'frontend-final-v4-input-packet.json')
    audit = a.load(OUT/'current-audit.json')
    native = a.load(OUT/'native-audit-raw.json')
    manifest = packet['runtime_manifest']
    service_checks = a.load(S/'current-checks.json')
    checks = copy.deepcopy(a.load(NC/'current-checks.json')['checks'])
    # Prior closure remains valid by exact unchanged source/stage comparison;
    # this finalization adds the fresh full current closure as a distinct check.
    for item in service_checks['checks']:
        if item['id'] == 'os_open_zoom':continue
        item = copy.deepcopy(item);item['id'] = 'service_v4_' + item['id'];checks.append(item)
    limits = [
        'This is the same owner final FRONTEND evidence package for independent manager acceptance. SERVICE V4 is accepted with all 14 criteria; qualification and full-release gates remain separate.',
        'Current production Headless Shell 151 checks prove 320 CSS-pixel behavior, narrow/wide transitions, exact identities, both themes and reduced motion. Native 200% observations cover only the listed controls/process/source/details subset on the current build, from the failed long attempt. Exact stable entity IDs were not recorded in that native subset; complete native Map/List usability at 200% is not claimed.',
        'The native long attempt remains failed for missing normal STOP before the 420-second inner deadline. Native Chrome zoom 90% to 200% to 90% was directly observed, but exact original window frame/origin/identity restoration remains false/unresolved. Positive zoom restoration is not frame restoration.',
        'The first short native attempt remains failed at 128.30 seconds under the unchanged 120-second STOP limit. The later successful short check stopped at 17.949551375 seconds and verified owned cleanup without any geometry or zoom actions. Its restoration is not applicable; it neither repeats the 200% walkthrough nor repairs the previous frame failure.',
        'Theme native keyboard selection remains unproved. Headless app and minimal native select made no change for the recorded sequence; the alternative also made no app selection change. This is a diagnostic, excluded from behavioral pass counts. No Theme-specific code was changed. Native Safari keyboard, actual VoiceOver speech and participant comprehension are not supplied.',
        'Dense captions can crowd in the 25-node/26-edge initial-fit Map. Exact List/canvas parity and selected/peripheral label behavior do not establish every association is unobscured or human comprehension. TASK-025 remains mandatory.',
        'Six focused unit groups use an explicit DOM double; 20 existing groups use mocked network/DOM. Catalog timer callback and passive-disconnect unit evidence are not real deadline or expiry timing. Prior real catalog timing remains historical and is not relabeled current.',
        'The 53 frontend browser groups and nine SERVICE V4 browser groups are reported groups across separate runs, including repeated bootstrap coverage, not counts of distinct requirements. Browser16 permits three exact disposable fixture paths to change, proving other-file preservation rather than every field in those three files.',
        'SERVICE V4 actual runner passed 28 cases, but its original wrapper receipt remains failed for an order-only validation assumption. Root adjudication and exact retained-case-set verification support the pass without a rerun. Initial browser driver failure and all native failures remain preserved.',
        'Operational worker RSS sampling permits transient overshoot; retained fault observations are not broad performance acceptance. Full 49 requirements, 36 acceptance tests, 33 tasks, eight phases and original qualification full 16 remain. No root/Template adoption, watcher restart, publication, retirement, participant/performance or main Task completion is claimed.'
    ]
    native_ui = native['claims']['native_ui_subset']
    lifecycle = native['claims']['no_change_lifecycle']
    checks.extend([
        {'id':'native_200_subset','status':'direct_partial_observation_from_failed_long_attempt','actual_executor':'/root','source':native_ui['source'],'failed_host_receipt':native_ui['failed_host_receipt'],'observations':native_ui['observations'],'zoom_percent':{'initial':90,'observed':200,'restored':90},'qualification':native_ui['qualification'],'historical_frame_restoration':native['historical_original_frame_restoration']},
        {'id':'native_no_change_lifecycle','status':'passed_separate_bounded_no_change_lifecycle','actual_executor':'/root','source':lifecycle['source'],'receipt':lifecycle['receipt'],'normal_stop_seconds':lifecycle['normal_stop_seconds'],'limit_seconds':120,'geometry_or_zoom_actions':False,'restoration':'not_applicable_to_this_no_action_check','qualification':'Owned clean readable OS-created context, normal STOP and cleanup only; does not repair the failed long attempt or prove a new 200% UI walkthrough.'},
        {'id':'accepted_service_v4','status':'accepted_by_manager_all14_with_stated_limits','receipt':a.ref(M/'service-package-acceptance-v4.json'),'delivery':a.ref(S/'delivery.json'),'criteria':a.ref(S/'criterion-evidence.json'),'criteria_count':14},
        {'id':'final_live_closure','status':'passed','receipt':ref('current-audit.json'),'runtime':ref('runtime-audit-raw.json'),'native_claim_reverification':ref('native-audit-raw.json'),'qualification':'Fresh frontend read-only exact input/source/build/dependency/stage/tool/inventory/full-runtime and native evidence checks. No service/browser/native UI/test/build rerun.'}
    ])
    write('current-checks.json',{'status':'current_evidence_bound_for_final_manager_review','build_id':packet['current_build_id'],'runtime_manifest':manifest,'frontend_unit_groups':{'focused':6,'existing':20},'frontend_browser_groups':53,'accepted_service_criteria':14,'service_cases':28,'service_browser_groups':9,'checks':checks,'limits':limits})
    native_sources = [a.ref(S/name) for name in ['native-partial-receipt.json','native-partial-observation.json','final-input-service-v4-native-attempt02-receipt.json','final-input-service-v4-native-attempt02-native-observation.json','final-input-service-v4-native-attempt02-adjudication.json','final-input-service-v4-short-attempt01-receipt.json','final-input-service-v4-short-attempt01-adjudication.json','final-input-service-v4-short-attempt02-receipt.json','final-input-service-v4-short-attempt02-root-native-observation.json','final-input-service-v4-native-claim-assessment.json','final-input-service-v4-native-no-geometry-guard-mapping.json']]
    write('native-qualification.json',{'status':'claim_specific_current_native_support_with_failed_history_retained','build_id':packet['current_build_id'],'actual_executor':'/root','manager_claim_mapping':a.ref(M/'service-v4-native-claim-assessment.json'),'fresh_readonly_verification':ref('native-audit-raw.json'),'sources':native_sources,'native_ui_subset':native_ui,'no_change_lifecycle':lifecycle,'historical_original_frame_restoration':native['historical_original_frame_restoration'],'native_viewport_at_200_percent':a.load(S/'final-input-service-v4-native-attempt02-native-observation.json')['window_and_viewport']['at_200_percent'],'not_claimed':native['not_claimed'],'qualification':'Native exact stable entity IDs were not recorded. Headless exact-ID evidence and native visible reading are separate, complementary observations; no invented native identity or full Map/List pass.'})
    criteria = copy.deepcopy(a.load(NC/'criterion-evidence.json')['criteria'])
    extra = {
        1:['service_v4_browser_late_session','service_v4_browser_late_context'],2:['service_v4_browser_basic'],3:['service_v4_browser_late_context'],4:['service_v4_service_http'],5:['native_200_subset'],
        12:['native_200_subset'],13:['native_200_subset'],23:['service_v4_browser_basic','service_v4_browser_late_session','service_v4_browser_late_context','service_v4_service_http'],25:['native_200_subset','native_no_change_lifecycle'],27:['service_v4_browser_basic'],28:['service_v4_browser_basic']
    }
    check_map = {x['id']:x for x in checks}
    for item in criteria:
        i = item['index']
        item['status'] = 'current_scoped_evidence_ready_for_manager_acceptance_with_stated_limits'
        item['acceptance_boundary'] = 'Accepted SERVICE V4 current dependency; manager FRONTEND acceptance and later qualification/full-release gates remain separate.'
        item['check_ids'] += extra.get(i,[]) + ['accepted_service_v4','final_live_closure']
        for ident in extra.get(i,[]) + ['accepted_service_v4','final_live_closure']:
            c = check_map[ident]
            item['direct_current_evidence'] += [c[k] for k in ['source','report','receipt','failed_host_receipt'] if k in c]
        item['direct_current_evidence'] = list({(x['path'],x['sha256']):x for x in item['direct_current_evidence']}.values())
        item['current_service_acceptance'] = a.ref(M/'service-package-acceptance-v4.json')
        if i == 12:
            item['explanation'] = 'Current actual headless entry/source tests preserve escaped text, heading focus, retained entry and exact source-trigger return, including a dismissed parent details region. The failed long native attempt directly observed current ordinary and process-step source reading at native 200%, with return to their triggers. Its STOP/frame failure remains disclosed; no native stable IDs or speech are invented.'
        if i == 13:
            item['explanation'] += ' Current native 200% observation adds visible ordered-process and numbered step-source reading, with the failed-attempt limitations preserved.'
        if i == 23:
            item['explanation'] += ' Accepted SERVICE V4 adds actual current absolute expiry/isolation, replay/resume and abort-insensitive late session/context checks; it does not turn the frontend passive modal unit into a separate real-expiry UI test.'
        if i == 25:
            item['status'] = 'current_320px_and_native200_reading_subset_supported_with_explicit_native_limits'
            item['explanation'] = 'Current actual 320 CSS-pixel production tests verify drawer/details keyboard behavior, both resize directions, source return, themes and reduced motion. Separate current native Chrome 90% to 200% to 90% observations verify the listed navigation, process/source reading and selected-details hide/reopen subset at 730 CSS-pixel inner width (723 document/client width). The long attempt remains failed for STOP and original frame restoration remains false/unresolved. Separate 17.9496-second no-change lifecycle proves shutdown/owned cleanup only, with restoration not applicable. Full native Map/List 200% usability, Safari and speech are unobserved.'
    assert [x['criterion'] for x in criteria] == packet['criteria'] and len(criteria) == 29
    write('criterion-evidence.json',{'assignment_id':'FRONTEND_WORKER_G3','baseline':packet['baseline'],'round':5,'criteria_count':29,'criteria_verbatim_and_original_order':True,'criteria':criteria,'current_checks':ref('current-checks.json'),'native_qualification':ref('native-qualification.json'),'limits':limits,'manager_acceptance_separate':True})

    old_context = a.load(NC/'current-context.json')
    write('current-context.json',{'assignment_id':'FRONTEND_WORKER_G3','native_id':'/root/explorer_manager_g3/frontend_worker','app_thread_id':'01a0c00b-e55b-74f1-b6dc-d83eb128e100','baseline':packet['baseline'],'round':5,'activation_reported_by_manager':'Task229 EV_FRONTEND_FINAL_V4_INPUTS, same original owner/settings; no helper replayed','packet':a.ref(M/'frontend-final-v4-input-packet.json'),'input_admission':ref('input-admission.json'),'original_context_refs':packet['original_context_preserved'],'authorized_evolutions':packet['authorized_input_evolution'],'current_dependency_verification':packet['current_dependency_verification'],'service_acceptance':a.ref(M/'service-package-acceptance-v4.json'),'prior_provisional_delivery':a.ref(NC/'delivery.json'),'original_plan':old_context['original_plan'],'remaining_original_plan_gates':old_context['remaining_original_plan_gates'],'all49_requirements_36_acceptance_tests_33_tasks_eight_phases_preserved':True,'qualification_full16_remains':True,'authority':packet['authority'],'write_scope':packet['write_scope'],'watcher':'Held by root; no action by this worker.','qualification':'Stopped pending owner rebind; no action by this worker.','limits':limits})
    history_refs = [a.ref(NC/'history-and-dispositions.json'),a.ref(NC/'final-verification-attempt-01.json'),ref('audit-attempt-01.json'),a.ref(S/'service-host-receipt.json'),a.ref(S/'service-host-adjudication.json'),a.ref(S/'service-adjudication-check.json'),a.ref(S/'evidence-inventory.json'),*native_sources]
    write('history-review.json',{'status':'preserved_and_scoped','references':history_refs,'frontend':'All original narrow failures/unexecuted stages and earlier frontend records remain exact; current 14–18 passes are unchanged, not rerun.','service':'Original service wrapper order failure remains failed despite actual 28-case runner pass and retained-output adjudication. Initial browser driver collision and native failures remain exact.','native':'Locked initial attempt supplied no actual zoom percentage. Long attempt supplied only listed native 200% observations and 90% zoom restoration, with no pre-deadline STOP and false/unresolved original frame. First short STOP at 128.30 seconds failed. Later 17.9496-second no-change lifecycle supplies shutdown/owned cleanup only.','current_verifier_failure':'audit.py attempted repository-root resolution of SERVICE output-manifest $.all_runtime_members. audit-attempt-01.json preserves the failure; audit-02.py requires exact equality with pinned manifest assets before resolving only that array at its live assets directory. Direct files remain repository-relative. No blanket path fallback.'})
    prior_visual = a.load(NC/'visual-qualification-current.json')
    write('visual-qualification.json',{'status':'unchanged_current_headless_images_and_new_claim_specific_native_observation','current_images':prior_visual['images'],'image_review':a.ref(NC/'visual-qualification-current.json'),'source_unchanged':ref('current-audit.json'),'native_observation':ref('native-qualification.json'),'dense_map_historical_image':prior_visual['historical_dense_map_image'],'qualification':'The five current narrow/session screenshots were actually viewed during the correction and still bind unchanged current product. No new screenshot/UI run is claimed. Dense map crowding and later human, Safari, speech and complete native Map/List usability remain explicit.'})
    frontend_files = a.load(NC/'output-manifest.json')['files']
    service_files = a.load(S/'output-manifest.json')['files']
    union = {x['path']:{k:x[k] for k in ['path','sha256','bytes']} for x in frontend_files + service_files}
    check_refs = list({(x['path'],x['sha256']):x for x in a.refs(checks)}.values())
    write('output-manifest.json',{'status':'direct_current_live_frontend_and_accepted_service_dependency_refs','build_id':packet['current_build_id'],'files':frontend_files,'accepted_service_dependency_files':service_files,'all_live_files':sorted(union.values(),key=lambda x:x['path']),'runtime_manifest':manifest,'all_runtime_members':audit['runtime_members'],'oversized_runtime_members':[x for x in audit['runtime_members'] if x['bytes']>250000],'oversized_policy':'Complete 434,861-byte vendor remains pinned by actual live manifest and repeated no-follow/single-link/hash/size audits; no truncation or substituted copy.','current_check_refs':check_refs,'product_tests_runtime_changed_this_finalization':False})
    result = {'status':'final_current_frontend_evidence_ready_for_manager_review','assignment_id':'FRONTEND_WORKER_G3','native_id':'/root/explorer_manager_g3/frontend_worker','baseline':packet['baseline'],'round':5,'build_id':packet['current_build_id'],'runtime_manifest':manifest,'criteria_count':29,'outcome':'All 29 original frontend criteria mapped to unchanged current narrow-layout correction and accepted SERVICE V4, with claim-specific native support and unresolved limitations retained.','changed_this_finalization':'Only new final-v4 evidence; product, tests, runtime and prior metadata remain unchanged.','checks_executed_now':'Read-only exact current input/build/dependency/stage/tool/inventory/preservation checks and unchanged full-runtime/native-evidence verifiers. No service, browser, native UI, test or build rerun.','existing_current_checks_admitted':{'frontend_unit_groups':26,'frontend_browser_groups':53,'service_criteria':14,'service_cases':28,'service_browser_groups':9},'native_evidence':'Direct listed 200% UI observations from failed long attempt; separate successful 17.9496-second no-change cleanup. Original frame restoration remains false/unresolved.','criteria':ref('criterion-evidence.json'),'checks':ref('current-checks.json'),'context':ref('current-context.json'),'audit':ref('current-audit.json'),'native_qualification':ref('native-qualification.json'),'history':ref('history-review.json'),'visual_qualification':ref('visual-qualification.json'),'limits':limits,'manager_acceptance_separate':True,'main_task_complete':False,'next_gate':'Stop writes for manager FRONTEND review/acceptance and same qualification owner current full16 input rebind; all original remaining plan gates stay required.'}
    write('result.json',result)
    handoff = f'''# Final current FRONTEND evidence

All 29 original TASK-012 through TASK-019 criteria remain verbatim and in order. This same-owner evidence-only finalization binds the current narrow navigation and dismissible phone details correction to accepted SERVICE V4. Build `{packet['current_build_id']}` and manifest `{manifest['sha256']}` are unchanged. Only new final-v4 metadata was written.

Current retained evidence includes 6 focused and 20 existing frontend unit groups, 53 actual frontend browser groups, all 14 accepted SERVICE criteria, 28 service cases and 9 service browser groups. Automated browser evidence uses the pinned Headless Shell 151.0.7922.34. Counts include repeated bootstrap groups and are not distinct-requirement counts. No test, build, listener, browser or native UI run was repeated here.

The fresh audit verifies all 349 packet references, 37 original context references, 8 exact admitted source/preimage evolutions, 28 authored build inputs, 1,001 live/staged dependency files, 4 dependency links, current stage/tool/check closure and all 5 live runtime members. The 434,861-byte vendor is fully hashed through the live manifest. Five recursively bound inventories verify 463 artifacts; 522 prior frontend and 93 SERVICE V4 files are preserved. Current live outputs and check receipts are directly enumerable in output-manifest.json and current-checks.json.

Native evidence is explicitly split. The failed long attempt directly observed native Chrome 90%→200%→90%, narrow navigation, process and numbered step-source reading, ordinary source reading with trigger return, and selected-details hide/reopen. At 200%, inner width was 730 CSS pixels and document/client width 723. Exact stable entity IDs were not recorded in this native subset, and complete native Map/List usability is not inferred. The attempt missed normal STOP before its 420-second deadline; exact original window frame/origin/identity restoration remains false/unresolved. Zoom restoration does not establish frame restoration.

The first short attempt still failed at 128.30 seconds under the unchanged 120-second limit. The separately successful short attempt sent normal STOP at 17.949551375 seconds and verified owned service/tab/window cleanup with six baseline tabs preserved. It made no geometry or zoom actions, so restoration is not applicable to that check. It supplies neither a new 200% walkthrough nor a repair of the earlier frame failure. native-qualification.json binds the exact root observations and failed/passed receipts separately.

Current 320 CSS-pixel, theme, reduced-motion, exact identity, keyboard List and renderer-failure checks remain distinct from native observations. The Theme headless no-change diagnostic is excluded from pass counts and does not establish an app defect or native keyboard success. Safari Theme keyboard behavior, actual VoiceOver speech and participant comprehension remain unobserved. Dense 25-node/26-edge initial-fit Map captions can crowd; exact parity does not establish every association is unobscured. Full native Map/List 200% and the planned human gate remain qualified.

Preserve the historical frontend failures and unexecuted preparations. SERVICE V4's actual 28-case runner passed, while its original wrapper remains failed for an order-only comparison, supported by exact retained-output adjudication without rerun. Initial service browser driver collision and all failed native attempts remain unchanged. This finalization's first audit path-base failure is preserved too: only the exact manifest-relative asset array receives its proven assets-directory base; direct current refs remain repository-relative.

Manager FRONTEND acceptance is separate. Next is the same qualification owner's full 16-criterion current input rebind and remaining original gates. All 49 requirements, 36 acceptance tests, 33 tasks and eight phases remain; performance, participant comprehension, adoption, cutover/rollback and final release are not claimed. Watcher stays held and qualification stays stopped until their owner gates. No Task, role, memory, Git, root, Template or publication changes occurred.

After delivery this worker stops all writes and waits for the manager's normal follow-up.
'''
    assert len(handoff.encode()) <= 250000
    with (OUT/'HANDOFF.md').open('x') as f:f.write(handoff)
    print(json.dumps({'status':'assembled_for_final_verification','result':ref('result.json'),'criteria':ref('criterion-evidence.json'),'checks':ref('current-checks.json'),'handoff':ref('HANDOFF.md')}))

if __name__ == '__main__':main()
