"""Final evidence and full runtime gate; delivery is the last write."""
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).absolute().parent
NC = OUT.parent
FRONT = NC.parent
S = ROOT/'Verification/project-knowledge-explorer-first-release/service-tests/service-v4'
spec = importlib.util.spec_from_file_location('readonly_audit', FRONT/'process-catalog-correction/final-v3/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

def write(name,obj):
    raw = (json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode()
    assert len(raw) <= 250000
    with (OUT/name).open('xb') as f:f.write(raw)

def r(name):return a.ref(OUT/name)

def main():
    admission = a.load(OUT/'input-admission.json')
    packet = json.loads(a.verify(admission['packet']))
    for row in admission['references'] + admission['original_context_preserved'] + admission['roles']:a.verify(row)
    original = {x['live']['path']:x for x in a.load(NC/'input-admission.json')['preimages']}
    for x in admission['authorized_input_evolution']:
        previous = x['previous_packet_ref']
        assert previous == original[previous['path']]['live']
        assert x['preserved_preimage'] == original[previous['path']]['preimage']
        assert a.sha(a.verify(x['preserved_preimage'])) == previous['sha256']
        if x['current']:a.verify(x['current'])
        else:assert not (ROOT/previous['path']).exists()
    preservation = a.load(OUT/'preservation-prestate.json')
    previous_front = [x for part in preservation['frontend_parts'] for x in json.loads(a.verify(part))['files']]
    previous_service = [x for part in preservation['service_v4_parts'] for x in json.loads(a.verify(part))['files']]
    assert previous_front == a.tree(FRONT,OUT) and previous_service == a.tree(S)
    assert preservation['product_and_tests'] == a.tree(ROOT/'SKILLS-depo/ontology/explorer')
    closure = a.load(OUT/'inventory-closure.json')
    for row in closure['inventories']:a.verify(row)
    for part in closure['parts']:
        for row in json.loads(a.verify(part))['files']:a.verify(row)
    outputs = a.load(OUT/'output-manifest.json')
    for row in outputs['all_live_files'] + outputs['all_runtime_members'] + outputs['current_check_refs'] + [outputs['runtime_manifest']]:a.verify(row)
    criteria = a.load(OUT/'criterion-evidence.json')
    assert len(criteria['criteria']) == 29 and [x['index'] for x in criteria['criteria']] == list(range(1,30))
    assert [x['criterion'] for x in criteria['criteria']] == packet['criteria']
    check_ids = {x['id'] for x in a.load(OUT/'current-checks.json')['checks']}
    for x in criteria['criteria']:
        assert set(x['check_ids']) <= check_ids
        for row in x['implementation'] + x['direct_current_evidence'] + [x['current_runtime_manifest'],x['current_service_acceptance']]:a.verify(row)
    for name in ['result.json','current-checks.json','native-qualification.json','history-review.json','visual-qualification.json']:
        for row in a.refs(a.load(OUT/name)):a.verify(row)
    # The current-context historical evolution records were checked explicitly
    # above; only their exact original/preimage/current mapping is admissible.
    context = a.load(OUT/'current-context.json')
    assert context['authorized_evolutions'] == admission['authorized_input_evolution']
    for key,value in context.items():
        if key != 'authorized_evolutions':
            for row in a.refs(value):a.verify(row)
    native = a.load(OUT/'native-qualification.json')
    assert native['native_ui_subset']['status'] == 'direct_partial_observation_from_failed_attempt'
    assert native['historical_original_frame_restoration']['restored'] is False
    assert native['no_change_lifecycle']['restoration'] == 'not_applicable_to_this_no_action_check'
    assert native['no_change_lifecycle']['normal_stop_seconds'] == 17.949551375000738
    runtime_script = S/'audit-live-runtime.py'
    assert a.ref(runtime_script)['sha256'] == '254c07109033e34f69d59f718cb79c0e5777134196cfeed50832a1df2b48f515'
    command = [str(ROOT/'.venv/bin/python'),'-I','-B',str(runtime_script),'--expected-manifest',outputs['runtime_manifest']['sha256']]
    run = subprocess.run(command,capture_output=True,timeout=45)
    assert run.returncode == 0 and not run.stderr
    runtime = json.loads(run.stdout)
    assert runtime['status'] == 'passed' and runtime['members'] == outputs['all_runtime_members']
    assert len(runtime['members']) == 5 and max(x['bytes'] for x in runtime['members']) == 434861
    with (OUT/'runtime-final-raw.json').open('xb') as f:f.write(run.stdout)
    for row in a.tree(OUT):assert row['bytes'] <= 250000,row['path']
    write('final-verification.json',{'status':'passed','actual_executor':'/root/explorer_manager_g3/frontend_worker','verifier':a.ref(Path(__file__)),'input_refs':349,'original_context_refs':37,'exact_evolution_pairs':8,'criteria_exact_original_order':29,'current_live_refs':len(outputs['all_live_files']),'direct_current_check_refs':len(outputs['current_check_refs']),'frontend_files_preserved':522,'service_v4_files_preserved':93,'recursive_inventory_artifacts':463,'runtime_command':command,'runtime_exit_code':0,'runtime_report':r('runtime-final-raw.json'),'runtime_script':a.ref(runtime_script),'runtime_executor_qualification':'Fresh frontend read-only execution of unchanged accepted verifier; its raw static service-worker label is not actor attribution. No new build/test/service/browser/native execution.','runtime_members':outputs['all_runtime_members'],'metadata_cap_bytes':250000,'criteria':r('criterion-evidence.json'),'output_manifest':r('output-manifest.json'),'native_limits_verified':True,'preserved_audit_failure':r('audit-attempt-01.json'),'main_task_complete':False,'manager_acceptance_separate':True})
    files = a.tree(OUT)
    write('evidence-inventory.json',{'status':'complete_before_last_delivery','files':files,'excludes':['evidence-inventory.json self','delivery.json written last'],'qualification':'New final-v4 evidence only; every preceding frontend/service file preserved. Failed first audit and its exact successor remain separately pinned.'})
    for row in files:a.verify(row)
    assert previous_front == a.tree(FRONT,OUT) and previous_service == a.tree(S)
    assert preservation['product_and_tests'] == a.tree(ROOT/'SKILLS-depo/ontology/explorer')
    # Full member no-follow reads again immediately at the manifest-last gate.
    for row in outputs['all_runtime_members'] + [outputs['runtime_manifest']]:a.verify(row)
    delivery = {'status':'final_current_frontend_writes_stopped_pending_manager_acceptance','assignment_id':'FRONTEND_WORKER_G3','native_id':'/root/explorer_manager_g3/frontend_worker','baseline':packet['baseline'],'round':5,'result':r('result.json'),'criteria':r('criterion-evidence.json'),'checks':r('current-checks.json'),'handoff':r('HANDOFF.md'),'context':r('current-context.json'),'input_admission':r('input-admission.json'),'current_audit':r('current-audit.json'),'native_qualification':r('native-qualification.json'),'history':r('history-review.json'),'visual_qualification':r('visual-qualification.json'),'output_manifest':r('output-manifest.json'),'final_verification':r('final-verification.json'),'evidence_inventory':r('evidence-inventory.json'),'live_outputs':outputs['all_live_files'],'current_check_references':outputs['current_check_refs'],'runtime_manifest':outputs['runtime_manifest'],'all_runtime_members':outputs['all_runtime_members'],'build_id':packet['current_build_id'],'current_service_acceptance':context['service_acceptance'],'criteria_count':29,'frontend_unit_groups':26,'frontend_browser_groups':53,'service_criteria':14,'service_cases':28,'service_browser_groups':9,'native_support':'Listed current native 200% UI subset from failed long attempt, with 90% zoom restoration; separate passed 17.9496-second no-change lifecycle. Original frame restoration remains false/unresolved.','native_Map_List_200_complete':False,'native_Safari_Theme_keyboard_verified':False,'speech_observed':False,'product_tests_runtime_prior_evidence_changed':False,'all_writes_stopped_after_delivery':True,'manager_acceptance_separate':True,'main_task_complete':False,'next_gate':'Independent manager FRONTEND acceptance and same qualification owner full16 current input rebind; original remaining gates preserved. Watcher stays held.'}
    write('delivery.json',delivery)
    print(json.dumps({'status':'all_writes_stopped','delivery':r('delivery.json'),'result':r('result.json'),'criteria':r('criterion-evidence.json'),'checks':r('current-checks.json'),'handoff':r('HANDOFF.md'),'final_verification':r('final-verification.json'),'runtime_manifest':outputs['runtime_manifest']}))

if __name__ == '__main__':main()
