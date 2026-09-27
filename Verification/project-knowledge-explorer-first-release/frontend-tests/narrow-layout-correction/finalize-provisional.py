"""Final direct current checks and manifest-last provisional delivery. No product writes."""
import importlib.util
import json
from pathlib import Path

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).absolute().parent
APP = ROOT / 'SKILLS-depo/ontology/explorer'
spec = importlib.util.spec_from_file_location('readonly_audit', OUT.parent / 'process-catalog-correction/final-v3/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

def write(name, obj):
    raw = (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(raw) <= 250000
    with (OUT / name).open('xb') as f:
        f.write(raw)

def r(name):
    return a.ref(OUT / name)

def main():
    result = a.load(OUT / 'result.json')
    output = a.load(OUT / 'output-manifest.json')
    audit = a.load(OUT / 'current-audit.json')
    evolution = a.load(OUT / 'current-input-evolution.json')
    for row in evolution['unchanged_refs']:
        a.verify(row)
    for change in evolution['intentional_evolutions']:
        a.verify(change['preserved_preimage'])
        if change['current']:
            a.verify(change['current'])
        else:
            assert not (ROOT / change['previous_packet_ref']['path']).exists()
    for row in a.load(OUT / 'assembly-preservation.json')['references']:
        a.verify(row)
    before = a.load(OUT / 'preservation-before.json')
    assert before['prior_frontend_evidence'] == a.tree(OUT.parent, OUT)
    assert output['files'] == a.tree(APP)
    assert output['runtime_manifest'] == audit['runtime_manifest'] == result['runtime_manifest']
    for row in output['files'] + output['all_runtime_members'] + [output['runtime_manifest']]:
        a.verify(row)
    assert len(output['all_runtime_members']) == 5
    assert max(x['bytes'] for x in output['all_runtime_members']) == 434861
    for unit in audit['unit_closure']:
        a.verify(unit['receipt'])
        for row in unit['input_refs']:
            a.verify(row)
    for browser in audit['browser_closure']:
        for key in ('job', 'inputs', 'report', 'receipt', 'attribution'):
            a.verify(browser[key])
        job = json.loads(a.verify(browser['job']))
        for row in json.loads(a.verify(browser['inputs']))['files']:
            a.verify(row, Path(job['stage']))
            if row['path'].startswith(('SKILLS-depo/', 'ONTOLOGY-depo/')):
                a.verify(row)
        for tool in job['external_tools']:
            assert str(Path(tool['path']).resolve()) == tool['resolved']
            a.verify(dict(tool, path=tool['resolved']))
    criteria = a.load(OUT / 'criterion-evidence.json')
    packet = json.loads(a.verify(evolution['packet']))
    assert [c['criterion'] for c in criteria['criteria']] == packet['criteria']
    assert [c['index'] for c in criteria['criteria']] == list(range(1,30))
    checks = a.load(OUT / 'current-checks.json')
    check_ids = {c['id'] for c in checks['checks']}
    for item in criteria['criteria']:
        assert set(item['check_ids']) <= check_ids
        for row in item['implementation'] + item['direct_current_evidence'] + [item['current_runtime_manifest']]:
            a.verify(row)
    direct_documents = ['result.json','current-context.json','current-checks.json','native-safari-followup-prepared.json','implementation-review-current.json','visual-qualification-current.json']
    # Current document references only. Historical stages and preimages retain
    # their own bases in history/evolution; never reinterpret them as live bytes.
    for name in direct_documents:
        for row in a.refs(a.load(OUT / name)):
            a.verify(row)
    for row in a.tree(OUT):
        if Path(row['path']).suffix in ('.json','.md'):
            assert row['bytes'] <= 250000, row['path']
    write('final-verification.json', {
        'status': 'passed', 'executor': '/root/explorer_manager_g3/frontend_worker',
        'verifier': a.ref(Path(__file__)), 'current_audit': r('current-audit.json'),
        'criteria': r('criterion-evidence.json'), 'output_manifest': r('output-manifest.json'),
        'packet_current_unchanged': 225, 'packet_authorized_evolutions': 8,
        'criteria_count_exact_order_and_text': 29, 'unit_groups': {'focused':6,'existing':20},
        'browser_behavior_groups': 53, 'theme_diagnostic_excluded': True,
        'live_product_and_test_files': len(output['files']), 'runtime_members': 5,
        'full_largest_member_bytes': 434861, 'current_stage_tool_and_live_closure': True,
        'prior_frontend_evidence_files_unchanged': 319,
        'all_preexisting_correction_evidence_unchanged': True,
        'metadata_size_cap_bytes': 250000,
        'checks_performed_now': 'Read-only exact current hashes, regular single-link no-follow stable reads, direct criterion/check/source closure, stage/tool pins and preserved evidence. No test/build/browser rerun.',
        'manager_acceptance_separate': True,
        'remaining': 'SERVICE V4, final same-owner FRONTEND input rebind, native Safari/zoom/Theme and QUALIFICATION/full-plan remaining gates.'
    })
    inventory = a.tree(OUT)
    write('evidence-inventory.json', {'status':'complete_before_manifest_last_delivery','base':str(OUT),'files':inventory,'exclusions':['evidence-inventory.json (self)','delivery.json (written last)'],'qualification':'Every prior/current correction receipt, failed report, unexecuted job descriptor, script, preimage and copied clean image is preserved here. Historical stage bindings use their pinned stages. Runtime/preimage vendor bytes are independently full-hashed, not truncated.'})
    for row in inventory:
        a.verify(row)
    assert output['files'] == a.tree(APP)
    assert before['prior_frontend_evidence'] == a.tree(OUT.parent, OUT)
    delivery = {
        'assignment_id':'FRONTEND_WORKER_G3','native_id':'/root/explorer_manager_g3/frontend_worker',
        'baseline':result['baseline'],'round':4,
        'status':'provisional_current_correction_writes_stopped_pending_manager_review',
        'result':r('result.json'),'criteria':r('criterion-evidence.json'),'checks':r('current-checks.json'),
        'handoff':r('HANDOFF.md'),'input_context':r('current-context.json'),'input_admission':r('input-admission.json'),
        'input_evolution':r('current-input-evolution.json'),'output_manifest':r('output-manifest.json'),
        'current_audit':r('current-audit.json'),'final_verification':r('final-verification.json'),
        'evidence_inventory':r('evidence-inventory.json'),'history':r('history-and-dispositions.json'),
        'review':r('implementation-review-current.json'),'visual_qualification':r('visual-qualification-current.json'),
        'native_followup_prepared_only':r('native-safari-followup-prepared.json'),
        'live_outputs':output['files'],'all_runtime_members':output['all_runtime_members'],
        'runtime_manifest':output['runtime_manifest'],'build_id':output['build_id'],
        'criteria_count':29,'unit_groups':{'focused':6,'existing':20},'actual_browser_groups':53,
        'theme_keyboard_selection_success':False,'speech_observed':False,
        'current_native_zoom_exercised':False,
        'all_writes_stopped_after_this_delivery':True,'manager_acceptance_separate':True,
        'main_task_complete':False,
        'required_next_gate':'Manager provisional review/ownership reconciliation; same SERVICE owner current V4; same FRONTEND full29 refreshed final input binding; QUALIFICATION rebind and remaining original gates. Watcher remains held.'
    }
    write('delivery.json', delivery)
    # After delivery: read/print only. This script performs no subsequent writes.
    print(json.dumps({'status':'all_writes_stopped','delivery':r('delivery.json'),'result':r('result.json'),'criteria':r('criterion-evidence.json'),'handoff':r('HANDOFF.md'),'final_verification':r('final-verification.json'),'runtime_manifest':output['runtime_manifest']}))

if __name__ == '__main__':
    main()
