"""Assemble new final evidence from admitted immutable checks, without reruns."""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
P = a.load(a.PACKET)
old = a.load(a.F / 'criterion-evidence-final.json')
current = a.load(a.E / 'current-checks.json')
service = a.load(a.S / 'current-checks.json')
audit = a.load(a.OUT / 'current-audit.json')
manifest = audit['live_manifest']
limits = [
    'Native Chrome zoom was 90% to 200% and restored to the actual original 90%. Current controls, corrected process catalog, ordered process reading and both source paths were observed. Native Map/List usability at 200% was not exercised.',
    'The separate current advanced03 check covers 320 CSS pixels, dark theme and reduced motion; neutral05 covers light/system/reset. Earlier 200% text sizing is not native browser zoom.',
    'Dense inner map captions can still crowd in the 25-node/26-edge initial-fit view. Exact model/List parity and selected/peripheral label handling do not establish human comprehension or every association being unobscured. TASK-025 remains mandatory.',
    'Safari, VoiceOver, real-human usability, release-wide performance/security/accessibility qualification, adoption, retirement, rollback and final release are not established by this frontend package.',
    'The 20 unit groups use actual compiled modules with mocked network/DOM; their deadline callback is mocked. Catalog07 uses a real authenticated response held by declared abort-insensitive instrumentation. Its 10,915 ms observation is first catalog request to Retry visible, including subsequent finite headers after the unmodified 10,000 ms timer, not a timer callback timestamp.',
    'Catalog07 checks the final parsed fixture equals exactly the original with only process14 label changed. Advanced03 permits exactly three declared fixture paths; that is path-level preservation, not the stronger catalog whole-document assertion.',
]
checks = current['checks'] + [dict(c, id='service_v3_' + c['id']) for c in service['checks']]
checks += [
    {'id': 'final_live_closure', 'status': 'passed', 'receipt': a.ref(a.OUT / 'current-audit.json'), 'runtime': a.ref(a.OUT / 'live-runtime-raw.json'), 'service_inputs': a.ref(a.OUT / 'service-input-closure.json'), 'qualification': 'Fresh read-only byte, confinement, complete package and current input closure checks. No new test, build, listener or browser run.'},
    {'id': 'accepted_service_v3', 'status': 'accepted_by_manager', 'receipt': a.ref(a.M / 'service-package-acceptance-v3.json'), 'criteria': a.ref(a.S / 'criterion-evidence.json'), 'delivery': a.ref(a.S / 'delivery.json'), 'criteria_count': 14},
    {'id': 'accepted_foundations', 'status': 'accepted_dependency_unchanged', 'delivery': a.ref(a.ROOT / 'Verification/project-knowledge-explorer-first-release/client-foundations-tests/delivery.json'), 'receipt': a.ref(a.M / 'client-foundations-acceptance.json'), 'qualification': 'Accepted pure decoder/state/model/routes/preferences dependency; current source digests checked. No new foundation execution claimed.'},
]
a.write('current-checks.json', {'status': 'current_frontend_evidence_ready_for_manager_acceptance', 'build_id': audit['build_id'], 'runtime_manifest': manifest, 'actual_browser_groups': 50, 'unit_groups': 20, 'rerun_policy': 'Existing exact current checks reused after complete admitted input and runtime closure; only read-only audits executed this finalization.', 'checks': checks, 'limits': limits})

# Exact individual check names and direct report/receipt references remain in
# current-checks.json. These rows explain each criterion's evidence disposition.
mapping = [
 ('unit catalog07 advanced03 service_v3_browser_late_session service_v3_browser_late_context accepted_foundations', 'State/request generations reject obsolete entry, catalog, session and context replies even when abort is ignored. Catalog headers have an independent finite allowlist and cannot change selection/history/entry state.'),
 ('unit advanced03 service_v3_browser_basic accepted_foundations', 'Exact route hydration, synchronous fragment erasure and safe history are checked; ordinary new-tab entry resumes authentication and copied links exclude bootstrap/session data.'),
 ('advanced03', 'Actual selection creates one history item while the camera stays fixed. Snapshot conflict retains the old view; atomic refresh updates retained graph identities and resets incompatible category/cursor/expansion state.'),
 ('unit catalog07 advanced03', 'ReadClient owns all fetch paths, including separately cancelled finite catalog reads. Screens and renderer emit intentions. Current keyboard, navigation and late-reply flows use that shared owner.'),
 ('advanced03 neutral05', 'Bootstrap exposes Overview, Terms, Processes and Map with visible search and no initial canvas. Neutral empty-local data retains reading navigation rather than management counters.'),
 ('advanced03 neutral05', 'Validated context supplies purpose and starting IDs; the neutral fixture explains imported vocabulary, offers Terms/categories/search and truthfully reports no configured process catalog.'),
 ('keyboard01 unit', 'Actual keyboard typing, Escape, submit and result-to-entry work without shortcuts. Unit generation/Arrow endpoint regressions preserve query and reject dismissed or obsolete suggestions.'),
 ('advanced03 unit catalog07', 'Two Alignment results retain exact identities, recorded excerpts and filter controls. Duplicate autocomplete and configured-process labels remain distinguishable by exact ID; non-starting process names are read from headers.'),
 ('neutral05 bounds04 unit', 'Empty search retains query/clear action; bounded continuation preserves the unconsumed page and offers deliberate narrowed/reset progress. Shared content-budget refusal is not admitted as success.'),
 ('advanced03 catalog07', 'Exact definition, aliases, scope, examples and non-examples, historical replacement/authority warnings and changed source freshness are observed. Definition spans three pages/66,023 UTF-8 bytes; catalog full-name access reads 15,011 exact bytes after preview disclosure.'),
 ('advanced03 unit', 'Map/List and entry retain exact direction/member IDs/qualifiers and sources. Two qualifier pages preserve 44,066 UTF-8 bytes; unsafe numeric qualifiers are not rounded while endpoint strings are projected losslessly.'),
 ('keyboard01 advanced03 service_v3_os_open_zoom', 'Source opens with heading focus, escaped exact text, retained entry and exact trigger return. Current native 200% observations cover ordinary source and process-step source with visible vertical reading and focus return.'),
 ('advanced03 unit catalog07 service_v3_os_open_zoom', 'Documented process fields and order resolve exact canonical/direct-binding support, including an owner found through a later field. Bounded discovery preserves incomplete continuation. Current catalog resolves recorded non-starting names and the native run reads recorded ordered steps and their source.'),
 ('advanced03', 'The actual unordered-process flow asserts the complete required sentence verbatim, without converting recorded relationships into an execution sequence.'),
 ('advanced03 build', 'Process pages render only recorded supported fields/order and execute no process. Source/import and locked build correspondence retain the single Cytoscape dependency and read-only architecture.'),
 ('advanced03 accepted_foundations', 'Actual DOM/canvas comparison retains canonical node/relation IDs, endpoints, direction, qualifiers, sources, classification, warnings and returned scope; normalized model and refusal metadata remain current.'),
 ('keyboard01 advanced03 bounds04', 'With renderer import blocked, keyboard List selection, source reading, More connections, Focus here and useful return remain operational. Canvas loss/layout refusal retain the same readable List model.'),
 ('advanced03', 'Exact current Map/List semantic parity and selection/scope survive route switching, copied explicit focus/selection, filter history and same-ID refreshed content.'),
 ('advanced03', 'Map loads lazily from an exact selected ID or picker and bounded neighborhood. Selecting updates entry details and exactly one history item without a camera/focus change.'),
 ('keyboard01 advanced03 bounds04', 'Keyboard Focus here replaces scope; More connections appends bounded scope. High-degree continuation stops at the tighter display budget and rereads unconsumed data after reset. Renderer keeps surviving positions and prunes removed positions; layout deadline retains List.'),
 ('advanced03 bounds04', 'Production canvas/List agree on parallel relation IDs, self-loop, canonical direction, unsafe qualifiers and relation-as-endpoint identities; retargeted retained edges update actual endpoints. Current unchanged renderer uses bounded preset positions, visible unusual-kind markers and peripheral/selected labels. Dense-fit comprehension remains qualified.'),
 ('advanced03 build', 'Renderer consumes normalized model only. Authored controls retain the exact required guidance, clear legend and deliberate focus/expansion actions; renderer has no source or ontology fetch path.'),
 ('catalog07 advanced03 bounds04 service_v3_browser_late_session service_v3_browser_late_context', 'Session/snapshot/route races retain useful recorded views and reject mixed or late responses; refresh uses new context and lower limits. Import failure, canvas loss and bounded layout refusal preserve List/source actions.'),
 ('neutral05 bounds04', 'The accepted Reader proves the ActionType returned view complete and empty before the exact absence sentence is asserted. High-degree/local budget/incomplete paths retain their limit disclosure and continuation rather than claiming absence.'),
 ('advanced03 neutral05 service_v3_os_open_zoom', 'Separate current 320 CSS-pixel/dark/reduced-motion and light/system/reset checks complement actual native Chrome 90% to 200% to 90% controls/catalog/ordered-process/source reading. Native Map/List at 200% remains unexercised; no CSS zoom substitution.'),
 ('advanced03', 'Repeated Back/Forward restores selection, same-focus filter scope and useful map context; focused-search Back cancels pending preview and restores query. Node selection pushes once; camera motion does not push history.'),
 ('advanced03 service_v3_browser_basic', 'Terms/Map and copied relation-subject routes preserve exact focus/selection identities, including a relation used as a genuine endpoint. Normal new-tab entry resumes an authenticated session and copied routes are secret-free.'),
 ('neutral05 advanced03 unit catalog07', 'Light/dark/system/reset affect presentation only, with preference-only storage. Theme updates preserve catalog in-flight identity and focused links; source bodies and ontology content are not stored in browser databases.'),
 ('advanced03 keyboard01 bounds04', 'Current exact Map/List relation IDs, endpoints, direction, qualifiers, source descriptors, warnings, filters, selection and scope are compared in production Chrome. Blocked import, canvas loss and layout refusal all retain useful keyboard List actions and entry/source reading.'),
]
assert len(mapping) == 29 and [r['criterion'] for r in old['criteria']] == P['criteria']
byid = {c['id']: c for c in checks}
criteria = []
for index, (ids, explanation) in enumerate(mapping, 1):
    previous = old['criteria'][index - 1]
    implementations = [a.ref(a.ROOT / r['path']) for r in previous['implementation']]
    if index in (1, 4, 8, 10, 13, 15, 23, 25, 28):
        r = a.ref(a.ROOT / 'SKILLS-depo/ontology/explorer/src/processes.ts')
        if r not in implementations:
            implementations.append(r)
    check_ids = ids.split() + ['accepted_service_v3', 'final_live_closure']
    direct = {}
    for cid in check_ids:
        assert cid in byid
        for r in a.refs(byid[cid]):
            # Reports, receipts, inputs and current code all remain directly bound.
            direct[(r['path'], r['sha256'])] = r
    criteria.append({'index': index, 'task': previous['task'], 'criterion': P['criteria'][index - 1], 'status': 'verified_with_stated_scope_limits_for_manager_review', 'explanation': explanation, 'check_ids': check_ids, 'implementation': implementations, 'direct_evidence': list(direct.values()), 'qualification': limits[2] if index == 21 else limits[0] + ' ' + limits[1] if index == 25 else 'Observed scope is bounded by the referenced receipts; full release and later original gates are separate.'})
a.write('criterion-evidence.json', {'assignment_id': P['assignment_id'], 'baseline': P['baseline'], 'round': 3, 'criteria_count': 29, 'criteria_verbatim_and_original_order': True, 'criteria': criteria, 'current_checks': a.ref(a.OUT / 'current-checks.json'), 'limits': limits, 'manager_acceptance_separate': True})

prestate = a.load(a.OUT / 'preservation-prestate.json')
a.write('output-manifest.json', {'status': 'current_readonly_authored_test_and_runtime_references', 'build_id': audit['build_id'], 'files': prestate['product_and_tests'], 'current_check_refs': [a.ref(a.OUT / n) for n in ('current-audit.json', 'service-input-closure.json', 'current-checks.json', 'live-runtime-raw.json')], 'runtime_manifest': manifest, 'all_runtime_members': audit['runtime_members'], 'oversized_runtime_members': [r for r in audit['runtime_members'] if r['bytes'] > 250000], 'oversized_policy': 'All-member no-follow stable regular/single-link/hash/size validation through the accepted helper. No generic evidence-size limit or chunk change.', 'product_or_test_writes_this_finalization': False})
plan_path = a.ROOT / 'Implementation_Plans/Plan_project-knowledge-explorer-full-first-release_2026-09-20_9B9964BA/plan.json'
plan = a.load(plan_path)
remaining = [{'task_id': t['task_id'], 'title': t['title']} for t in plan['tasks'] if int(t['task_id'].split('-')[-1]) >= 20]
a.write('current-context.json', {'assignment_id': P['assignment_id'], 'native_id': P['native_id'], 'baseline': P['baseline'], 'round': 3, 'canonical_activation_reported_by_manager': 'EV_FRONTEND_FINAL_V3_INPUTS 199 to 200; same owner activated; no helper event replayed', 'packet': a.ref(a.PACKET), 'input_admission': a.ref(a.OUT / 'input-admission.json'), 'original_37_context_refs': P['original_context_preserved'], 'seven_authorized_evolutions': P['authorized_input_evolution'], 'current_service_dependency': P['current_dependency_verification'], 'prior_correction_delivery': a.ref(a.E / 'delivery.json'), 'original_plan': a.ref(plan_path), 'remaining_original_plan_gates': remaining, 'all_49_requirements_and_36_acceptance_tests_remain': True, 'watcher': 'Held by root; no restart or Template propagation by this worker.', 'qualification': 'Stopped pending manager-controlled current dependency reconciliation; this worker does not resume it.', 'authority': P['authority']})
a.write('result.json', {'status': 'final_current_frontend_evidence_ready_for_manager_acceptance', 'assignment_id': P['assignment_id'], 'native_id': P['native_id'], 'baseline': P['baseline'], 'round': 3, 'build_id': audit['build_id'], 'runtime_manifest': manifest, 'criteria_count': 29, 'outcome': 'Full frontend TASK-012 through TASK-019 evidence finalized against accepted SERVICE V3 and the unchanged current process-catalog correction. Recorded non-starting process names, stable focus, bounded independent header reads and truthful deadline/retry/races remain backed by current checks.', 'changed_this_finalization': 'Only new final-v3 evidence/scripts; product/tests/assets/dependencies and all prior metadata unchanged.', 'checks_executed_now': 'No-follow current input/build/dependency/stage/member/preservation audits and accepted full runtime verifier; no test/build/browser rerun.', 'existing_current_checks_admitted': {'unit_groups': 20, 'browser_groups': 50, 'service_criteria': 14, 'native_zoom': 'Actual Chrome 90% to 200% to original 90%, current controls/catalog/process/source paths'}, 'highest_observed_verification': 'Actual production browser and native reading behavior supplied by attributed primary-host receipts; this worker freshly verified their unchanged current closure.', 'criteria': a.ref(a.OUT / 'criterion-evidence.json'), 'checks': a.ref(a.OUT / 'current-checks.json'), 'context': a.ref(a.OUT / 'current-context.json'), 'audit': a.ref(a.OUT / 'current-audit.json'), 'historical_failures': [a.ref(a.E / 'history.json'), a.ref(a.OUT / 'audit-attempt-01.json'), a.ref(a.OUT / 'audit-attempt-02.json')], 'limits': limits, 'new_product_blocker_found': False, 'main_task_complete': False, 'next_gate': 'Manager independently verifies and accepts current FRONTEND; reconcile same qualification owner to current dependency packet. Preserve remaining original plan gates and watcher hold.'})
handoff = '''Final current frontend evidence is ready for independent manager review. The unchanged baseline has all 29 original criteria in their original order, now bound to accepted SERVICE V3 and build 09b4571b34594b39e9d19be3320f334bf7d608a333e0d06902dfda0a361259b8. The manifest remains c59422dc85017405ff9c92e335a459f770e649a2a59507d7dc7b7f449d04ae4a.

Only this new final-v3 directory was written. The implementation, tests, assets, dependency pins, previous deliveries, failed receipts, preimages and pause checkpoint remain unchanged. The correction reads every finite configured process ID through the shared client, preserves exact IDs and recorded names, discloses truncated names with full entry access, updates stable links in place, and keeps meaningful keyboard focus during bounded retry. Catalog requests have independent cancellation and route/session/snapshot correlation.

current-checks.json binds 20 compiled-module unit groups and 50 actual Chrome browser groups (4 keyboard, 7 catalog, 28 advanced, 4 bounds, 7 neutral). No unchanged test/build/browser job was rerun for this finalization. current-audit.json and service-input-closure.json revalidate exact current source/runtime, frozen browser inputs and service V3 stages. All 28 build inputs and 1,001 dependency files match live and staged bytes, including the four reviewed internal tool links. The accepted runtime helper freshly checks all five actual files, including the 434,861-byte vendor member, complete imports, lock/notices/schema/build identity, no-follow confinement and stable manifest. Do not rely on a generic evidence-reference cap to validate the vendor file.

SERVICE V3's accepted 14 criteria and current native observation are explicitly bound. The host observed actual native Chrome controls at the original 90%, increased to 200%, read the corrected catalog, recorded ordered steps, step source and ordinary source with heading/trigger focus, then restored the actual original 90% before closing the owned tab. The current 320 CSS-pixel, dark/reduced-motion, light/system/reset checks are separate. Native Map/List at 200% was not exercised. Historical 200% text sizing must not be described as native zoom.

Catalog07's observed 10,915 ms interval runs from first catalog call to Retry becoming visible; it includes finite subsequent headers after the unchanged 10,000 ms production timer. The test holds a real authenticated response and deliberately ignores AbortSignal. It proves truthful failure/retry and late rejection, not the exact callback firing time. The unit timer is mocked. Catalog07's final parsed fixture allows only process14 label to change; advanced03 preserves all files except three declared fixture paths and has the narrower path-level assertion.

The historical initial catalog06 selector failure, keyboard wrapper expectation failure, neutral Chrome postcheck failure and initial compilation failure remain preserved. The finalization audit also preserved two diagnostic failures: unrestricted recursion mistakenly treated qualification checkpoint01's old production-browser.cjs assertion as current, and a second attempt applied the repository base to asset-relative member paths. Checkpoint02's actual owned_files binding matches live bytes. Current inventories and stage bases are verified without weakening any current source binding; no product edit resulted.

Dense inner Map labels can still crowd at initial fit with 25 nodes and 26 edges. Current exact Map/List parity and bounded rendering do not prove every association unobscured or human comprehension. Preserve this limitation for TASK-025. Safari, VoiceOver, native Map/List at 200%, human validation and later qualification/adoption/cutover/rollback/release work remain mandatory as applicable in the unchanged plan. This is not main Task completion or publication authority.

For review, begin with delivery.json, criterion-evidence.json and current-checks.json, then inspect direct exact receipts and current-audit.json. Recheck the full manifest at acceptance and any later affected gate. Manager acceptance and qualification-owner rebind remain separate. The watcher remains root-held; this worker does not resume it or qualification. After the final delivery write and read-only validation, all worker writes stop.
'''
with (a.OUT / 'HANDOFF.md').open('x') as f:
    f.write(handoff)
print(json.dumps({'status': 'assembled', 'criteria': len(criteria), 'remaining_plan_tasks': len(remaining), 'largest_criterion_map_bytes': (a.OUT / 'criterion-evidence.json').stat().st_size}))
