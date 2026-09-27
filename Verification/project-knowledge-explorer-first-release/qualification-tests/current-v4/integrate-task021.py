"""Read exact receipts and assemble scoped TASK021 evidence; run no product code."""
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
V = ROOT / 'Verification/project-knowledge-explorer-first-release'
Q = V / 'qualification-tests'
O = Q / 'current-v4'
M = ROOT / 'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
BUILD = 'c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a'
MANIFEST = 'b27225ad7b3d57277cb962f4cebbff0b778563a327ec4b0dce0cfa324cdbcb37'


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'file admission'
        chunks = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(fd)
        assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'unstable read'
        return b''.join(chunks)
    finally:
        os.close(fd)


def ref(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    data = read(path)
    return {'path': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def check(expected, path=None):
    actual = ref(path or expected['path'])
    assert actual['sha256'] == expected['sha256'], 'digest mismatch: ' + actual['path']
    assert 'bytes' not in expected or actual['bytes'] == expected['bytes'], 'size mismatch'
    return actual


def load(path):
    return json.loads(read(path))


def save(path, data):
    data = (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(data) <= 250000, 'evidence cap'
    path = Path(path)
    assert path.is_relative_to(Q) or path in [V / 'browser-results.json', V / 'offline-csp-results.json']
    path.write_bytes(data)
    return ref(path)


packet = load(M / 'qualification-current-v4-input-packet.json')
assert ref(M / 'qualification-current-v4-input-packet.json')['sha256'] == 'd7d53a2a07893182f45410c345f4a948f92df4c04a5ad75fecc27539aa3db75d'
for name in ['browser-results.json', 'offline-csp-results.json']:
    assert read(V / name) == read(O / 'prestates' / name), 'summary prestate changed'

# Every referenced original and captured member is checked again. Current mapped
# sources are separately checked; accepted stage-only test drivers remain explicit.
stage_audits = []


def audit_stage(job_path, receipt_path, inputs_path=None):
    job, receipt = load(job_path), load(receipt_path)
    manifest = check(job['manifest'])
    if inputs_path:
        assert read(inputs_path) == read(manifest['path']), 'manifest copy mismatch'
    members = load(manifest['path'])['files']
    original = Path(job.get('stage', job.get('staging_root')))
    captured = Path(receipt['execution_stage'])
    assert len(members) == job['inputs_count']
    mapped, stage_only = [], []
    for item in members:
        check(item, original / item['path'])
        check(item, captured / item['path'])
        live = Path(job.get('source_mapping', {}).get(item['path'], ROOT / item['path']))
        if live.exists():
            mapped.append(check(item, live))
        else:
            stage_only.append(item)
    for stage in [original, captured]:
        actual = set()
        for base, dirs, files in os.walk(stage, followlinks=False):
            assert not any((Path(base) / x).is_symlink() for x in dirs + files), 'stage symlink'
            actual.update(str((Path(base) / x).relative_to(stage)) for x in files)
        assert actual == {i['path'] for i in members} | {'inputs.json'}, 'stage inventory mismatch'
    stage_audits.append({'job': ref(job_path), 'receipt': ref(receipt_path), 'manifest': manifest, 'member_count': len(members), 'current_mapped_members': len(mapped), 'stage_only_members': stage_only, 'original_and_captured_members_exact': True, 'current_mapped_members_exact': True})


new_runs = [
    ('actual-production-07', '/private/tmp/explorer-task021-host-1uukw8zs', 'd0e4879d385b09112ac2b3c4f595c3bab0b6dc3d783d2f72732e5b6a625c5e83', '8e74f5f23ca8736255d246903cc257ab7e9370b13e40ec5a8f447b2fd7e26aec'),
    ('actual-production-07-confirmation', '/private/tmp/explorer-task021-host-q4buqkx5', 'e24f8a1d6c3d4e46e0bc0da2453a8739205afa520c2e061e883832cc4713e92e', 'deee4ba22598420c99a95f61ba00c56d32123928261080f4b8288af1c05ce6e5'),
]
for name, source, receipt_hash, raw_hash in new_runs:
    source, target = Path(source), O / name
    check({'path': str(source / 'receipt.json'), 'sha256': receipt_hash})
    check({'path': str(source / 'stdout.json'), 'sha256': raw_hash})
    receipt, raw = load(source / 'receipt.json'), load(source / 'stdout.json')
    assert receipt['status'] == raw['status'] == 'passed'
    assert receipt['stdout_sha256'] == raw_hash and receipt['exit_code'] == 0
    assert receipt['post_verification_errors'] == receipt['emergency_signals'] == []
    assert receipt['observed_descendants_exited'] and receipt['stderr_bytes'] == 0 and not receipt['timed_out']
    assert len(raw['checks']) == 9 and all(x['status'] == 'passed' for x in raw['checks'])
    assert raw['browser_version'] == '151.0.7922.34' and raw['async_failures'] == []
    audit_stage(source / 'reviewed-job.json', source / 'receipt.json')
    target.mkdir(exist_ok=True)
    names = ['host-wrapper.py', 'reviewed-release.json', 'reviewed-job.json', 'stdout.json', 'admission.json', 'receipt.json']
    if (source / 'reviewed-confirmation-release.json').exists():
        names.append('reviewed-confirmation-release.json')
    for member in names:
        data = read(source / member)
        if (target / member).exists():
            assert read(target / member) == data, 'preserved root copy'
        else:
            (target / member).write_bytes(data)
    save(target / 'attribution.json', {'status': 'passed', 'actual_executor': '/root', 'root_source': str(source), 'worker_action': 'Copied exact public host bundle and independently checked original/captured/current-mapped stage bytes; no test rerun.', 'references': [ref(target / n) for n in names], 'build_id': BUILD, 'observed_groups': raw['checks'], 'qualification': 'Nine actual current scenarios passed. Production06 remains failed with unknown cause; two diagnostic07 passes are not evidence of a diagnosed fix or universal reliability.'})

sources, raw_reports = {}, {}


def source(key, directory):
    directory = Path(directory)
    sources[key] = {k: ref(directory / filename) for k, filename in [('raw', 'stdout.json'), ('receipt', 'receipt.json'), ('job', 'reviewed-job.json'), ('attribution', 'attribution.json')]}
    raw_reports[key] = load(directory / 'stdout.json')
    assert raw_reports[key]['status'] == 'passed'


for key, name in [('P', 'actual-production-07'), ('P2', 'actual-production-07-confirmation'), ('KEY', 'actual-keyboard-04'), ('EXP', 'actual-lifecycle-06-expiry'), ('STOP', 'actual-lifecycle-06-stop'), ('TIME', 'actual-lifecycle-06-deadline')]:
    source(key, O / name)
    if key not in ['P', 'P2']:
        audit_stage(O / name / 'reviewed-job.json', O / name / 'receipt.json')

frontend_path = V / 'frontend-tests/narrow-layout-correction/final-v4/current-checks.json'
frontend = load(frontend_path)
frontend_checks = [c for c in frontend['checks'] if c['id'].startswith('browser')]
assert sum(c['groups'] for c in frontend_checks) == 53
evidence = {}


def refs_in(obj):
    if isinstance(obj, dict):
        if 'path' in obj and 'sha256' in obj:
            yield obj
        for value in obj.values():
            yield from refs_in(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from refs_in(value)


def bind_refs(obj):
    for item in refs_in(obj):
        evidence[item['path']] = check(item)


for c in frontend_checks:
    bind_refs(c)
    key = 'F' + c['id'].removeprefix('browser')
    sources[key] = {k: c[v] for k, v in [('raw', 'report'), ('receipt', 'receipt'), ('job', 'job'), ('inputs', 'inputs'), ('attribution', 'attribution')]}
    sources[key]['fixture_scope'] = c.get('fixture_scope', c['qualification'])
    raw_reports[key] = load(c['report']['path'])
    assert raw_reports[key]['status'] == 'passed'
    assert len(raw_reports[key]['checks']) == c['groups'] and all(x['status'] == 'passed' for x in raw_reports[key]['checks'])
    audit_stage(c['job']['path'], c['receipt']['path'], c['inputs']['path'])

service_path = V / 'service-tests/service-v4/current-checks.json'
service = load(service_path)
service_checks = [c for c in service['checks'] if c['id'] in ['service_http', 'browser_basic', 'browser_late_session', 'browser_late_context']]
for c in service_checks:
    bind_refs(c)
    key = 'S_' + c['id']
    sources[key] = dict(c)
    sources[key]['raw'] = c['report']
    raw_reports[key] = load(c['report']['path'])
    assert raw_reports[key]['status'] == 'passed'
    audit_stage(c['job']['path'], c['receipt']['path'], c['inputs']['path'])
http = raw_reports['S_service_http']
assert http['tests_run'] == 28 and http['failures'] == http['errors'] == http['skips'] == 0
assert all(c['status'] == 'passed' for c in http['cases'])
assert sum(c.get('groups', 0) for c in service_checks) == 9

# Existing per-scenario claims are mapped by exact check name to current reports,
# never by the historical group index or an old bundle's passing status.
old = load(O / 'prestates/browser-results.json')
progress = load(O / 'progress.json')
acceptance = {x['id']: x['exact_acceptance'] for x in progress['individual36_acceptance_progress']}
replacement = {'F20': 'F16', 'F19': 'F18', 'F21': 'F17'}
scenarios = {}


def observation(key, name):
    matches = [(i, c) for i, c in enumerate(raw_reports[key]['checks']) if c['name'] == name]
    assert len(matches) == 1, 'exact current group missing'
    index, c = matches[0]
    assert c['status'] == 'passed'
    return {'source': key, 'locator': f'checks[{index}]', 'name': name, 'status': c['status']}


for at, row in old['scenarios'].items():
    observations = []
    for item in row['observations']:
        key = replacement.get(item['source'], item['source'])
        observations.append(observation(key, item['name']))
        if key == 'P':
            observations.append(observation('P2', item['name']))
    scenarios[at] = {'status': 'observed_current_production_phase_evidence', 'exact_acceptance': acceptance[at], 'observations': observations}
assert set(scenarios) == {f'AT-{i:02}' for i in [*range(1, 24), 28, 29, 32, 34]}
for at, names in {
    'AT-10': ['details_presentation_retains_actual_renderer_camera_and_returned_ids'],
    'AT-11': ['phone_details_keyboard_dismiss_reopen_preserves_scope_selection_history_and_list_nodes'],
    'AT-19': ['source_close_reexposes_exact_trigger_after_parent_details_dismissal'],
    'AT-22': ['delayed_entry_response_does_not_reopen_dismissed_details_or_steal_focus'],
    'AT-29': ['320px_native_drawer_keyboard_open_close_hidden_navigation_and_persistent_search', 'keyboard_destination_closes_drawer_and_restores_reading_focus', 'phone_details_keyboard_dismiss_reopen_preserves_scope_selection_history_and_list_nodes'],
    'AT-34': ['failed_renderer_keeps_phone_list_focus_expand_and_details_reopen'],
}.items():
    for name in names:
        scenarios[at]['observations'].append(observation('F15', name))
scenarios['AT-23']['observations'].append(observation('F14', 'narrow_close_session_preserves_visible_focus_and_exposes_closed_status'))
scenarios['AT-29']['qualification'] = 'TASK021 establishes actual keyboard reachability, visible focus and browser DOM/live-region feedback. Actual Safari/VoiceOver utterances and final global AT29 closure remain pending in TASK022; DOM or AX text is not observed speech.'

failed_dir = O / 'actual-production-06-failed'
failed = load(failed_dir / 'stdout.json')
assert failed['status'] == 'failed' and len(failed['checks']) == 1
discrepancy = save(O / 'production-discrepancy.json', {
    'status': 'unexplained_original_failure_with_two_current_diagnostic_passes',
    'build_id': BUILD,
    'failed_run': {k: ref(failed_dir / p) for k, p in [('receipt', 'receipt.json'), ('raw', 'stdout.json'), ('attribution', 'attribution.json')]},
    'failed_observation': {'phase': failed.get('phase'), 'reason': failed.get('reason'), 'completed_groups': 1, 'successful_search_responses': 20, 'type_frame_query_repetition_page_and_operation': 'not captured by original generic error handler'},
    'passing_runs': [sources['P'], sources['P2']],
    'reviewed_driver': ref(O / 'production-browser-diagnostic.cjs'),
    'original_driver': ref(O / 'production-browser.cjs'),
    'assessment': 'No concrete deterministic cause is established. Original06 failed before the first deterministic-search group completed. Diagnostic07 retained queries, fixture, assertion semantics, product and runtime pins, and added safe operation diagnostics and outstanding-promise rejection handling. Both separately authorized fresh-fixture runs passed all nine groups. Instrumentation and timing differ, so these passes do not explain or prove a fix for06.',
    'limits': ['Original06 failure and all raw bytes remain preserved.', 'No raw exception type/frame or exact failed page/action can be reconstructed.', 'No product defect, resolved defect or universal reliability is asserted.', 'No further repetition was run or requested.']})

for item in [ref(frontend_path), ref(service_path), ref(V / 'production-build.json'), ref(O / 'runtime-audit.json'), ref(O / 'build04-execution-receipt.json'), ref(M / 'frontend-acceptance-final-v4.json'), ref(M / 'service-package-acceptance-v4.json'), ref(M / 'qualification-current-v4-TASK020-acceptance.json')]:
    evidence[item['path']] = check(item)
bind_refs(sources)
bind_refs(discrepancy)
manifest = load(ROOT / 'SKILLS-depo/ontology/explorer/assets/manifest.json')
assert ref(ROOT / 'SKILLS-depo/ontology/explorer/assets/manifest.json')['sha256'] == MANIFEST

closure = save(O / 'task021-current-evidence-closure.json', {'status': 'passed', 'observed_unix': time.time(), 'build_id': BUILD, 'runtime_manifest_sha256': MANIFEST, 'stage_audits': stage_audits, 'evidence': list(evidence.values()), 'reuse_basis': 'Exact executed current V4 production inputs and original/captured stages freshly compared by stable no-follow single-link reads. Current live mappings checked separately. Stage-only drivers listed explicitly; no historical build substitution, no suite rerun.', 'qualification': 'Host execution/tool pre-post checks remain attributed to root. This assembly rechecks stage/evidence/source correspondence and does not claim a new browser/native run.'})

browser = save(V / 'browser-results.json', {'status': 'production_phase_evidence_complete_pending_manager_acceptance', 'plan_task': 'TASK-021', 'criterion_number': 3, 'exact_criterion': packet['criteria'][2], 'build_id': BUILD, 'runtime_manifest_sha256': MANIFEST, 'scenarios': scenarios, 'sources': sources, 'production_build': ref(V / 'production-build.json'), 'current_runtime_audit': ref(O / 'runtime-audit.json'), 'reused_current_input_closure': closure, 'frontend_current_groups': 53, 'service_current_cases': 28, 'service_current_browser_groups': 9, 'complete_scenario_count': len(scenarios), 'production_discrepancy': discrepancy, 'preserved_prestate': ref(O / 'prestates/browser-results.json'), 'highest_verification': 'Actual current production browser workflows in explicitly pinned Headless Shell151.0.7922.34; five frontend runs, two diagnostic production runs, keyboard and lifecycle, plus accepted current service evidence.', 'proof_boundaries': ['All actual listener/browser execution is attributed to root; reproducible build04 was executed by this worker.', 'Accepted frontend fixture mutations are limited to each recorded test scope; this is not whole live-depot nonmutation.', 'AT29 browser-layer keyboard/live-region evidence supports entering TASK022; actual speech and complete accessibility remain pending.', 'Production06 remains an unexplained failure; two diagnostic07 passes are separately retained.', 'Service runner passed all28 cases; its original wrapper order-only failure and exact adjudication remain preserved.', 'No native Safari/VoiceOver, participant comprehension, performance or final TASK023 preservation pass is implied.']})

selected_cases = ['test_explorer_service.PackageRaceTests.test_missing_assets_and_invalid_configuration', 'test_explorer_health.HealthTests.test_missing_bundle_health_facts_and_legacy_help', 'test_explorer_health.HealthTests.test_cli_launch_and_no_optional_imports', 'test_explorer_health.InstalledLayoutTests.test_installed_package_serves_and_cli_health_reads_real_root_contracts', 'test_explorer_service.ServiceTests.test_success_all_operations_and_safe_assets']
service_observations = []
for name in selected_cases:
    found = [(i, c) for i, c in enumerate(http['cases']) if c['case'] == name]
    assert len(found) == 1 and found[0][1]['status'] == 'passed'
    service_observations.append({'source': 'S_service_http', 'locator': f'cases[{found[0][0]}]', 'case': name, 'status': 'passed'})
offline_runs = []
for key in ['P', 'P2']:
    raw = raw_reports[key]
    assert raw['optional_paths_absent'] and not raw['publication_enabled']
    assert raw['nonlocal_requests'] == raw['page_errors'] == 0 and raw['csp_violations'] == []
    assert raw['generated_files_unchanged'] and raw['generated_absences_preserved'] and raw['fixture_regular_files_unchanged']
    offline_runs.append({'source': sources[key], 'fixture_identity': raw['fixture_identity'], 'network': {'external_requests': raw['nonlocal_requests'], 'csp_violations': raw['csp_violations'], 'page_errors': raw['page_errors'], 'server': 'Dedicated Python Service; Node is browser-test tooling only, not a serving/dev process.'}, 'optional_services_absent': raw['optional_paths_absent'], 'publication_enabled': raw['publication_enabled'], 'generated_products': raw['generated_state'], 'generated_files_unchanged': True, 'generated_absences_preserved': True, 'fixture_regular_files_unchanged': True})
offline = save(V / 'offline-csp-results.json', {'status': 'production_phase_evidence_complete_pending_manager_acceptance', 'plan_task': 'TASK-021', 'criterion_number': 4, 'exact_criterion': packet['criteria'][3], 'build_id': BUILD, 'runtime_manifest_sha256': MANIFEST, 'production_build': ref(V / 'production-build.json'), 'actual_offline_browser_runs': offline_runs, 'service_evidence': sources['S_service_http'], 'service_observations': service_observations, 'security_and_csp': ref(V / 'security-results.json'), 'current_input_closure': closure, 'production_discrepancy': discrepancy, 'preserved_prestate': ref(O / 'prestates/offline-csp-results.json'), 'qualification': 'Actual installed-layout and missing-assets checks use current SERVICE V4; missing assets fail package preparation before browser UI exists. In both production07 fixtures actual wiki owner setup preceded read baseline, retaining its real221-member manifest then changing listed INDEX.md and removing listed concepts.md. Reads neither generated nor required those products. Complete selected live-depot nonmutation remains TASK023.'})

progress['phases']['TASK021'] = 'current_27_scenario_and_offline_evidence_complete_pending_manager_acceptance'
progress['phases']['TASK024'] = 'benchmark05_current_refreeze_reviewed_unexecuted_dependency_gate'
for row in progress['original16criteria'][2:4]:
    row['status'] = 'current_phase_evidence_complete_pending_manager_acceptance'
    row['gate'] = 'manager_TASK021_acceptance_before_TASK022_execution'
for row in progress['individual36_acceptance_progress']:
    if row['id'] in scenarios:
        row['status'] = 'observed_current_production_phase_evidence'
        row['evidence'] = [browser]
        row['qualification'] = scenarios[row['id']].get('qualification', 'Current TASK021 scope only; final full qualification and later gates remain.')
save(O / 'progress.json', progress)
print(json.dumps({'browser_results': browser, 'offline_csp': offline, 'discrepancy': discrepancy, 'closure': closure, 'stage_audits': len(stage_audits), 'stage_member_checks': sum(x['member_count'] for x in stage_audits), 'evidence_count': len(evidence), 'scenario_rows': len(scenarios), 'observations': sum(len(x['observations']) for x in scenarios.values())}, indent=2))
