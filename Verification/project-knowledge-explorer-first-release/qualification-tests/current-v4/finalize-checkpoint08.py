"""Finalize scoped current evidence and an explicit stopped same-owner checkpoint."""
import hashlib
import json
import os
from pathlib import Path
import stat
import time

O = Path(__file__).resolve().parent
Q, V, ROOT = O.parent, O.parent.parent, O.parents[3]
M = ROOT / 'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
BUILD = 'c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a'
NATIVE = '/root/explorer_manager_g3/qualification_worker'


def read(p):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        a = os.fstat(fd)
        assert stat.S_ISREG(a.st_mode) and a.st_nlink == 1
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read()
        z = os.fstat(fd)
        assert (a.st_dev, a.st_ino, a.st_size, a.st_mtime_ns, a.st_ctime_ns) == (z.st_dev, z.st_ino, z.st_size, z.st_mtime_ns, z.st_ctime_ns)
        return data
    finally:
        os.close(fd)


def ref(p):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    data = read(p)
    return {'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def load(p):
    return json.loads(read(p))


def verify(row):
    actual = ref(row['path'])
    assert actual == row, 'reference mismatch: ' + row['path']
    return actual


def save(p, obj):
    data = (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(data) <= 250000
    p.write_bytes(data)
    return ref(p)


packet_path = M / 'qualification-current-v4-input-packet.json'
packet = load(packet_path)
assert ref(packet_path)['sha256'] == 'd7d53a2a07893182f45410c345f4a948f92df4c04a5ad75fecc27539aa3db75d'
for name in ['accessibility-results.json', 'manual-keyboard-voiceover.md']:
    assert read(V / name) == read(O / 'prestates' / name)
native_path = V / 'frontend-tests/narrow-layout-correction/final-v4/native-qualification.json'
native = load(native_path)
for item in native['sources']:
    verify(item)
verify(native['manager_claim_mapping'])
verify(native['fresh_readonly_verification'])
adjudication = load(O / 'accessibility-adjudication.json')
for item in adjudication['state_evidence']:
    verify(item)
scanner = load(O / 'actual-accessibility-16/observation-summary.json')
geometry = load(O / 'actual-geometry-04/stdout.json')
expiry = load(O / 'actual-expiry-accessibility-02/stdout.json')
assert scanner['scans_count'] == 70 and scanner['violation_nodes'] == 0 and scanner['incomplete_nodes'] == 336
assert expiry['status'] == 'passed' and expiry['incomplete_nodes'] == 0 and len(expiry['scans']) == 2

remaining = [
    'Actual current Safari Theme control and native AT continuation need a permitted launch/observation method; Theme01 is prepared but unreleased.',
    'Direct osascript requires a specific user request under current CUA instructions. Alternatively, a user-operated private launch needs its own reviewed protocol. Existing broad approval does not settle either method.',
    'The proposed tokenless credential endpoint is not authorized or implemented: local-client race and pre-capture clean-route proof remain unresolved.',
    'Actual contemporaneous heard VoiceOver words/captions and focused native flow observations remain unobserved; DOM/AX text, approved actions and headless results are not spoken output.',
    'Current native Chrome200% reading subset is partial, with exact stable IDs unrecorded and old frame restoration false/unresolved. The17.9496-second no-change lifecycle does not repair it.',
    'Windows browser/AT combination was not exercised.',
    'TASK023 live03 must wait for TASK022 completion and coordinated manager/root no-write window with watcher held; no protected live comparison has started.',
    'TASK024 complete benchmark05 remains prepared/reviewed but unexecuted until TASK023.',
    'TASK025 requires an actual participant and contemporaneous own-word answers, timing, help and errors after original dependencies. Availability is unanswered; no participant result exists.',
    'All49 requirements,36 scenarios,33 tasks,eight phases and later TASK026–033 remain unchanged.'
]
a11y = {
    'status': 'current_automated_and_scoped_manual_findings_complete_native_AT_incomplete',
    'plan_task': 'TASK-022', 'build_id': BUILD,
    'runtime_manifest_sha256': 'b27225ad7b3d57277cb962f4cebbff0b778563a327ec4b0dce0cfa324cdbcb37',
    'criteria': [{'number': i + 1, 'exact_criterion': packet['criteria'][i], 'status': 'supported_qualified_reporting' if i == 6 else 'not_complete_native_evidence_required'} for i in [4, 5, 6]],
    'actual_versions': {'current_automated_browser': 'Chrome Headless Shell151.0.7922.34/revision1234', 'scanner': 'axe-core4.13.0', 'current_native_subset': 'Root-attributed system Chrome partial, separately bound below; not Safari or speech.', 'historical_native': 'Prior Safari/VoiceOver versions and actions remain in exact preserved V3 reports; not a current V4 spoken-flow execution.', 'windows_AT': 'not_exercised'},
    'scanner': {'attribution': ref(O / 'actual-accessibility-16/attribution.json'), 'stdout_lossless_index': ref(O / 'actual-accessibility-16/stdout-index.json'), 'all_raw_index': ref(O / 'actual-accessibility-16/raw-shard-index.json'), 'summary': ref(O / 'actual-accessibility-16/observation-summary.json'), 'states': 70, 'violations': 0, 'incomplete_nodes': 336, 'sub24px_candidates': 454, 'coverage': 'All original54 plus16 new dialog/details/source-parent state/theme combinations.'},
    'expiry': {'attribution': ref(O / 'actual-expiry-accessibility-02/attribution.json'), 'raw': ref(O / 'actual-expiry-accessibility-02/stdout.json'), 'original_failed_wrapper': ref(O / 'actual-expiry-accessibility-02/receipt.json'), 'root_adjudication': ref(O / 'actual-expiry-accessibility-02/root-adjudication.json'), 'states': 2, 'actual_wait_ms': expiry['real_wait_ms'], 'configured_seconds': 60, 'clock_modified': False, 'violations': 0, 'incomplete_nodes': 0, 'qualification': 'One actual passing child run; original wrapper failed on two absent summary fields, separately adjudicated without rerun.'},
    'geometry': {'attribution': ref(O / 'actual-geometry-04/attribution.json'), 'raw_index': ref(O / 'actual-geometry-04/raw-shard-index.json'), 'states': 46, 'coverage': 'All original30 plus16 current narrow states.', 'label_activation': 'Four trusted draft-label clicks: enable/restore once per theme; other labels individually measured for association and hit area.'},
    'visual': {'attribution': ref(O / 'actual-visual-04/attribution.json'), 'raw_index': ref(O / 'actual-visual-04/raw-shard-index.json'), 'root_review': ref(O / 'actual-visual-04/root-visual-observation.json'), 'views': 8, 'qualification': 'Current both-theme wide first sentence,320px first sentence/summary and dismissed-parent source text. Viewport evidence only; no old-bundle pixels.'},
    'individual_findings': ref(O / 'accessibility-adjudication.json'),
    'finding_disposition_counts': adjudication['counts'],
    'modal_focus': {'actual_trace': ref(O / 'actual-accessibility-16/observation-summary.json'), 'departures_per_theme': 1, 'returns_per_theme': 1, 'qualification': 'BODY/document.hasFocus=false departure while modal stays open; next Tab returns to visible modalcontrol. No background-control focus observed. Browser-chrome destination is an interpretation, not direct observation.'},
    'keyboard_and_DOM_live_regions': ref(V / 'browser-results.json'),
    'current_native_partial': {'source': ref(native_path), 'subset': native['native_ui_subset'], 'viewport': native['native_viewport_at_200_percent'], 'separate_no_change_lifecycle': native['no_change_lifecycle'], 'unresolved_original_frame': native['historical_original_frame_restoration']},
    'preserved_failures': [ref(O / name / 'attribution.json') for name in ['actual-accessibility-14-failed', 'actual-accessibility-15-failed']],
    'preserved_prestate': ref(O / 'prestates/accessibility-results.json'),
    'remaining': remaining, 'no_WCAG_compliance_claim': True,
    'highest_verification': 'Current production headless scanner/keyboard/geometry plus scoped actual pixel review; limited root-attributed native Chrome reading subset. Actual current Safari/VoiceOver qualification remains incomplete.'
}
a11y_ref = save(V / 'accessibility-results.json', a11y)
manual = '''# Current keyboard and assistive-technology evidence

Current build: `c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a`. TASK022 remains incomplete. Complete former reports are preserved in `qualification-tests/current-v4/prestates/`; old V3 pixels, Safari actions and words are not promoted to this build.

Root executed the current Headless Shell151.0.7922.34 keyboard04 production flow: four groups and14 real key traversals covering search, exact entry/source return, renderer-independent List selection/expansion/focus, and process-step source return. Actual DOM status updates include “entries returned”, “Selected FixtureTaskManager.” and “Returned connections updated.” These are observed live-region contents, not heard announcements. See `browser-results.json` for exact raw locations and current frontend/service evidence.

Scanner16 completed70 states with zero violations;336 incomplete contrast nodes and454 rectangle candidates were retained and individually mapped to current geometry04. The46 geometry states retain the original30 plus16 modal/details states. Measured spacing supports188 standalone anchors;14 associated label regions meet the measured square/hit-area checks;252 original rectangle candidates are inactive controls, including six retained0×0 closed-details rows. Actual trusted activation was four draft-label clicks, not14 separate label activations. All328 arrow color chains and eight overlap cases have exact scoped evidence in `qualification-tests/current-v4/accessibility-adjudication.json`. VISUAL04 supplies eight current scrolled images; both-theme first sentences,320px summaries and source excerpts are legible in those viewports. This is not whole-page or WCAG certification.

The corrected modal test records one document-focus departure and return per theme: BODY with document.hasFocus=false while the modal remains open, followed by Tab returning inside. Actual document controls outside the modal still fail. Original scanner14/15 failures remain unchanged. The two expired-state scans passed after real60-second expiry; an independent root adjudication preserves the wrapper's absent-summary-field failure without rerunning the browser.

Current native Chrome evidence from the frontend/service owners is a limited subset from a failed long attempt: zoom90→200→90, measured innerWidth730/clientWidth723/scrollWidth723, modal/process/source reading and selected-details hide/reopen. Exact stable entity IDs were not recorded. Original frame restoration is false/unresolved. A separate17.9496-second no-change cleanup pass preserved six baseline tabs; it neither repeats200% reading nor repairs that frame failure. These exact distinctions remain in `accessibility-results.json`.

Actual current Safari Theme selection and VoiceOver words remain unobserved. Historical Safari/VoiceOver activation, AX names, screenshots and approvals do not supply utterances. Windows/browser/AT was not exercised. Native focus, narrow/reflow and ordinary/reduced-motion continuation must retain actual methods and restoration limits; the current headless evidence is not a substitute.

The minimal method handoff is either an explicit user request authorizing AppleScript only for the disposable Safari document, followed by exact manager/root release, or a newly reviewed user-operated private-launch protocol. Prepared Theme01 remains unreleased under the current CUA-only boundary. No tokenless credential endpoint was implemented: its local-client race and safe pre-capture route observation are unresolved. No token may appear in CUA arguments, logs or general clipboard capture.

Once a permitted current session is ready, an actual listener must report contemporaneous VoiceOver words for the required actions, with action, heard wording, time/help and failures kept distinct. The existing `qualification-tests/voiceover-utterance-checklist.md` remains unfilled. Later participant comprehension requires the person's own explanations and observed completion/errors under the original protocol. Availability is unanswered; no simulated speech, prompted answer or approval counts as evidence.

TASK023 live preservation, TASK024 benchmark05 and TASK025 participant execution remain gated. The watcher remains root-held. No native, live-read or benchmark job is active at this checkpoint.
'''
(V / 'manual-keyboard-voiceover.md').write_text(manual)
manual_ref = ref(V / 'manual-keyboard-voiceover.md')
progress = load(O / 'progress.json')
progress['status'] = 'stopped_checkpoint08_current_native_human_method_gates'
progress['phases']['TASK022'] = 'current_scanner72_geometry46_visual8_findings_adjudicated_native_AT_incomplete'
progress['current_TASK022_evidence'] += [ref(O / name / 'attribution.json') for name in ['actual-accessibility-16', 'actual-geometry-04', 'actual-visual-04']]
for c in progress['original16criteria']:
    if c['number'] in [5, 6]:
        c.update(status='not_complete_actual_current_native_AT_required', evidence=[a11y_ref, manual_ref])
    elif c['number'] == 7:
        c.update(status='supported_current_qualified_reporting', evidence=[a11y_ref, ref(O / 'accessibility-adjudication.json')], gate='No whole TASK022 or WCAG acceptance; native criteria5/6 remain.')
for row in progress['individual36_acceptance_progress']:
    if row['id'] in ['AT-29', 'AT-30']:
        row.update(status='partial_current_browser_native_subset_full_native_AT_pending', evidence=[ref(V / 'browser-results.json'), a11y_ref], qualification='Actual current speech/full native observations remain incomplete; no headless-to-native substitution.')
progress['remaining'] = remaining
save(O / 'progress.json', progress)

# Audit the full admitted closure. Only explicitly authorized current summaries
# may differ, and every original byte is retained in a named prestate.
admission = load(O / 'admission.json')
prestates = {x['original']['path']: x for x in admission['report_and_test_prestates']}
changed = {str((V / n).relative_to(ROOT)) for n in ['security-results.json', 'production-build.json', 'browser-results.json', 'offline-csp-results.json', 'accessibility-results.json', 'manual-keyboard-voiceover.md']}
comparisons, evolved = [], []
for expected in packet['references']:
    actual = ref(expected['path'])
    if actual != expected:
        assert expected['path'] in changed
        prestate = prestates[expected['path']]
        assert expected == prestate['original']
        verify(prestate['preserved'])
        evolved.append({'original': expected, 'preserved_prestate': prestate['preserved'], 'current': actual, 'authority': 'Explicit current V4 summary evolution in unchanged owned evidence scope.'})
    else:
        comparisons.append(actual)
old_owned, old_changed = 0, []
for part in packet['preserved_owned_inventory_parts']:
    verify(part)
    for expected in load(part['path'])['files']:
        actual = ref(expected['path'])
        if actual != expected:
            assert expected['path'] in changed
            preserved = prestates[expected['path']]['preserved']
            assert preserved['sha256'] == expected['sha256'] and preserved['bytes'] == expected['bytes']
            verify(preserved)
            old_changed.append({'original': expected, 'current': actual, 'preserved_prestate': preserved})
        old_owned += 1
assert old_owned == 826 and len(packet['references']) == 386
closure_ref = save(Q / 'input-closure-checkpoint-08.json', {'status': 'current386_refs_and826_history_files_verified_with_exact_authorized_summary_evolution', 'observed_unix': time.time(), 'packet': ref(packet_path), 'unchanged_current_references': comparisons, 'authorized_current_reference_evolutions': evolved, 'preserved_owner_file_count': old_owned, 'authorized_owned_evolutions': old_changed, 'product_evolution_admission': ref(O / 'admission.json'), 'current_phase_closure': ref(O / 'task021-current-evidence-closure.json'), 'qualification': 'No original frozen stage/checkpoint/raw evidence or product input changed. Exactly named summaries evolve with preserved preimages; this is byte provenance, not TASK023 live nonmutation.'})
supported = [1, 2, 3, 4, 7]
result_ref = save(Q / 'result-current-v4-checkpoint-08.json', {'status': 'incomplete_current_qualification_stopped_at_native_human_method_gate', 'native_id': NATIVE, 'assignment_id': 'QUALIFICATION_WORKER_G3', 'baseline': packet['baseline'], 'round': 3, 'build_id': BUILD, 'all16_original_criteria': progress['original16criteria'], 'supported_current_criteria': supported, 'not_complete_criteria': [x for x in range(1, 17) if x not in supported], 'individual36_acceptance_progress': progress['individual36_acceptance_progress'], 'phase_state': progress['phases'], 'current_reports': [ref(V / n) for n in ['security-results.json', 'production-build.json', 'browser-results.json', 'offline-csp-results.json', 'accessibility-results.json', 'manual-keyboard-voiceover.md']], 'adjudication': ref(O / 'accessibility-adjudication.json'), 'current_input_closure': closure_ref, 'remaining': remaining, 'authority': 'Worker evidence conclusion only; no final manager/full-task acceptance, pause or blocked status mutation.', 'actual_executor': 'Root ran all listener/browser/native observations; worker ran released build04, scoped static/synthetic controls and evidence/source/pixel review.'})
jobs = [ref(Q / n) for n in ['host-native-theme-01.json', 'host-live-preservation-03.json', 'host-performance-recipes-05.json']]
delivery_ref = save(Q / 'delivery-current-v4-checkpoint-08.json', {'status': 'partial_current_evidence_ready_with_exact_continuation_gates', 'native_id': NATIVE, 'result': result_ref, 'input_closure': closure_ref, 'current_adjudication': ref(O / 'accessibility-adjudication.json'), 'prepared_unexecuted_resume_jobs': jobs, 'native_protocol': ref(O / 'native-theme-protocol-01.md'), 'native_method_assessment': ref(O / 'native-handoff-feasibility-01.md'), 'voiceover_checklist_unfilled': ref(Q / 'voiceover-utterance-checklist.md'), 'participant_protocol_unexecuted': ref(Q / 'participant-protocol-v3.md'), 'minimal_user_handoff': 'Specific user request for disposable-document AppleScript, or a newly reviewed user-operated private launch; then actual contemporaneous heard VoiceOver words. Later actual participant own-word answers remain required. Parent availability question has no answer.', 'preserved_prestate_admission': ref(O / 'admission.json'), 'remaining': remaining})

# Include every file in this owner's exact scope, then bound the inventory.
paths = set()
for name in packet['write_scope']:
    p = ROOT / name
    if p.is_dir():
        for base, dirs, files in os.walk(p, followlinks=False):
            assert not any((Path(base) / n).is_symlink() for n in dirs + files)
            paths.update(Path(base) / n for n in files)
    elif p.exists():
        paths.add(p)
owned = [ref(p) for p in sorted(paths)]
parts = []
for start in range(0, len(owned), 300):
    parts.append(save(Q / f'checkpoint08-owned-inventory-part-{start // 300 + 1:02}.json', {'status': 'exact_settled_owned_files', 'part': start // 300 + 1, 'files': owned[start:start + 300]}))
checkpoint_ref = save(Q / 'same-owner-checkpoint-08.json', {'status': 'all_qualification_work_and_writes_stopped', 'observed_unix': time.time(), 'native_id': NATIVE, 'assignment_id': 'QUALIFICATION_WORKER_G3', 'baseline': packet['baseline'], 'round': 3, 'packet': ref(packet_path), 'previous_checkpoint': ref(Q / 'same-owner-checkpoint-07.json'), 'result': result_ref, 'delivery': delivery_ref, 'current_input_closure': closure_ref, 'roles_read': admission['roles'], 'owned_file_count': len(owned), 'owned_inventory_parts': parts, 'inventory_boundary': 'Every existing file in exact owner scope at capture; excludes these newly created inventory parts and this self-referential final checkpoint. Parts and checkpoint are separately hash-bound.', 'original_criteria_count': 16, 'supported_current_criteria': supported, 'not_complete_criteria': [x for x in range(1, 17) if x not in supported], 'prepared_unexecuted_resume_jobs': jobs, 'remaining': remaining, 'native_method': 'Theme01 held/unreleased; tokenless alternative not implemented; root/user method and actual words required.', 'nonmutation_window_started': False, 'benchmark_executed': False, 'participant_observed': False, 'windows_AT_exercised': False, 'watcher': 'Root-held; unchanged by worker.', 'no_active_worker_owned_host_processes': True, 'canonical_state_mutation': False, 'continuation': 'Same owner/native/settings/full original scope. Manager must bind current inputs and explicitly wake before further writes. This checkpoint is not a Task pause, blocked status or full completion.'})
for row in [checkpoint_ref, delivery_ref, result_ref, closure_ref, a11y_ref, manual_ref, *parts]:
    verify(row)
print(json.dumps({'checkpoint': checkpoint_ref, 'delivery': delivery_ref, 'result': result_ref, 'closure': closure_ref, 'accessibility': a11y_ref, 'manual': manual_ref, 'owned_files': len(owned), 'inventory_parts': len(parts), 'packet_unchanged': len(comparisons), 'packet_authorized_evolved': len(evolved), 'preserved826_authorized_evolved': len(old_changed), 'supported_criteria': supported, 'all_writes_stopped_after_this_command': True}, indent=2))
