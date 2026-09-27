"""Final current read-only checks, followed by new bounded stopped delivery."""
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
packet = a.load(a.PACKET)
for row in packet['references'] + packet['original_context_preserved']:
    a.verify(row)
before = a.load(a.OUT / 'preservation-prestate.json')
assert before['prior_frontend_files'] == a.tree(a.F, a.OUT)
assert before['product_and_tests'] == a.tree(a.ROOT / 'SKILLS-depo/ontology/explorer')
criterion = a.load(a.OUT / 'criterion-evidence.json')
assert [r['criterion'] for r in criterion['criteria']] == packet['criteria']
assert [r['index'] for r in criterion['criteria']] == list(range(1, 30))
assert criterion['round'] == 3 and criterion['baseline'] == packet['baseline']
checked = set()
for name in ('current-audit.json', 'service-input-closure.json', 'output-manifest.json', 'current-checks.json', 'criterion-evidence.json', 'result.json', 'visual-qualification.json'):
    for row in a.refs(a.load(a.OUT / name)):
        a.verify(row)
        checked.add((row['path'], row['sha256']))
counts = {}
for check in a.load(a.E / 'current-checks.json')['checks'][:5]:
    report = json.loads(a.verify(check['report']))
    assert report['status'] == 'passed'
    assert len(report['checks']) == check['groups']
    assert all(c['status'] == 'passed' for c in report['checks'])
    counts[check['id']] = len(report['checks'])
unit = a.load(a.E / 'unit-01.json')
unit_report = json.loads(unit['stdout'])
assert unit['exit_code'] == 0 and unit_report['status'] == 'passed'
assert len(unit_report['checks']) == 20 and all(c['status'] == 'passed' for c in unit_report['checks'])
assert sum(counts.values()) == 50
native = a.load(a.S / 'native-check.json')
assert native['initial_browser_zoom_percent'] == native['restored_browser_zoom_percent'] == 90
assert native['actual_browser_zoom_percent'] == 200 and not native['zoom_substitution_used']
assert native['corrected_process_catalog_observed'] and native['ordered_process_and_both_sources_observed']
audit = a.load(a.OUT / 'current-audit.json')
run = subprocess.run(audit['runtime_command'], capture_output=True, timeout=45)
assert run.returncode == 0 and not run.stderr
assert run.stdout == a.read(a.OUT / 'live-runtime-raw.json')
assert before['prior_frontend_files'] == a.tree(a.F, a.OUT)
assert before['product_and_tests'] == a.tree(a.ROOT / 'SKILLS-depo/ontology/explorer')
for row in packet['references']:
    a.verify(row)
assert all(p.stat().st_size <= 250000 for p in a.OUT.iterdir() if p.is_file())
a.write('final-verification.json', {'status': 'passed', 'executor': packet['native_id'], 'verification_code': a.ref(Path(__file__)), 'packet_refs_reverified': 196, 'original_context_reverified': 37, 'all_prior_frontend_files_unchanged': len(before['prior_frontend_files']), 'all_product_and_test_files_unchanged': len(before['product_and_tests']), 'current_direct_refs_reverified': len(checked), 'criteria_verbatim_and_ordered': 29, 'unit_groups': 20, 'browser_groups': counts, 'browser_groups_total': 50, 'native_zoom': [90, 200, 90], 'fresh_runtime_gate': {'exit_code': run.returncode, 'report_bytes_identical': True, 'report': a.ref(a.OUT / 'live-runtime-raw.json'), 'members': 5, 'vendor_bytes': 434861}, 'all_metadata_bounded': True, 'new_product_test_build_or_browser_execution': False, 'qualification': 'Final read-only scope/byte/evidence/runtime verification. Prior explicitly historical audit failures and source evolution remain preserved; full Task acceptance is separate.'})
inventory = a.tree(a.OUT)
a.write('evidence-inventory.json', {'status': 'complete_new_final_v3_evidence_inventory', 'files': inventory, 'excludes': ['evidence-inventory.json self-reference', 'delivery.json final binding'], 'every_file_maximum_bytes': 250000, 'old_frontend_inventory': a.ref(a.OUT / 'preservation-prestate.json'), 'qualification': 'All files are newly authored under the sole final-v3 write directory; no old record overwritten.'})
delivery = {'assignment_id': packet['assignment_id'], 'native_id': packet['native_id'], 'baseline': packet['baseline'], 'round': 3, 'status': 'final_current_delivery_writes_stopped_pending_manager_acceptance', 'result': a.ref(a.OUT / 'result.json'), 'criteria': a.ref(a.OUT / 'criterion-evidence.json'), 'checks': a.ref(a.OUT / 'current-checks.json'), 'handoff': a.ref(a.OUT / 'HANDOFF.md'), 'input_context': a.ref(a.OUT / 'current-context.json'), 'input_admission': a.ref(a.OUT / 'input-admission.json'), 'output_manifest': a.ref(a.OUT / 'output-manifest.json'), 'current_audit': a.ref(a.OUT / 'current-audit.json'), 'service_input_closure': a.ref(a.OUT / 'service-input-closure.json'), 'final_verification': a.ref(a.OUT / 'final-verification.json'), 'evidence_inventory': a.ref(a.OUT / 'evidence-inventory.json'), 'visual_qualification': a.ref(a.OUT / 'visual-qualification.json'), 'live_outputs': [a.ref(a.ROOT / r['path']) for r in a.load(a.E / 'delivery.json')['live_outputs']], 'all_runtime_members': audit['runtime_members'], 'runtime_manifest': audit['live_manifest'], 'build_id': audit['build_id'], 'current_dependency': a.ref(a.M / 'service-package-acceptance-v3.json'), 'criteria_count': 29, 'unit_groups': 20, 'actual_browser_groups': 50, 'native_zoom': 'Actual current 90% to 200% to original 90%; controls/catalog/process/source only, not Map/List.', 'product_test_assets_changed_this_finalization': False, 'all_writes_stopped_after_this_delivery': True, 'manager_acceptance_separate': True, 'main_task_complete': False, 'required_next_gate': 'Independent manager FRONTEND acceptance and original qualification-owner dependency reconciliation; preserve TASK-020 through TASK-033, full49REQ/36AT release gates and watcher hold.'}
a.write('delivery.json', delivery)
for row in a.refs(delivery):
    a.verify(row)
for row in a.load(a.OUT / 'evidence-inventory.json')['files']:
    a.verify(row)
assert before['prior_frontend_files'] == a.tree(a.F, a.OUT)
assert before['product_and_tests'] == a.tree(a.ROOT / 'SKILLS-depo/ontology/explorer')
print(json.dumps({'status': 'all_writes_stopped', 'delivery': a.ref(a.OUT / 'delivery.json'), 'result': delivery['result'], 'criteria': delivery['criteria'], 'checks': delivery['checks'], 'final_verification': delivery['final_verification'], 'new_files': len(list(a.OUT.iterdir()))}))
