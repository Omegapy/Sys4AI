"""Evidence-only current audit; no service, browser, test, or build execution."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).absolute().parent
NC = OUT.parent
FRONT = NC.parent
SERVICE = ROOT / 'Verification/project-knowledge-explorer-first-release/service-tests/service-v4'
APP = ROOT / 'SKILLS-depo/ontology/explorer'
M = ROOT / 'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
PACKET = M / 'frontend-final-v4-input-packet.json'
PACKET_SHA = '9fd9eae983f68fe06258ede0f10b559871f351ae2cd4d8e429abbe5c30289b79'
spec = importlib.util.spec_from_file_location('readonly_audit', FRONT / 'process-catalog-correction/final-v3/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

def write(name, obj):
    raw = (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(raw) <= 250000
    with (OUT / name).open('xb') as f:
        f.write(raw)

def parts(stem, rows):
    refs = []
    for start in range(0, len(rows), 300):
        name = f'{stem}-{start // 300:02}.json'
        write(name, {'files': rows[start:start + 300]})
        refs.append(a.ref(OUT / name))
    return refs

def stage_check(job_ref):
    job = json.loads(a.verify(job_ref))
    rows = json.loads(a.verify(job['manifest']))['files']
    live = []
    for row in rows:
        a.verify(row, Path(job['stage']))
        if row['path'].startswith(('SKILLS-depo/', 'ONTOLOGY-depo/')):
            a.verify(row)
            live.append(row)
    for tool in job.get('external_tools', []):
        assert str(Path(tool['path']).resolve()) == tool['resolved']
        a.verify(dict(tool, path=tool['resolved']))
    return {'job': job_ref, 'manifest': job['manifest'], 'stage': job['stage'], 'stage_files': len(rows), 'live_files': len(live), 'external_tools': len(job.get('external_tools', []))}

def main():
    packet = json.loads(a.verify({'path': str(PACKET), 'sha256': PACKET_SHA}))
    assert len(packet['references']) == 349 and len(packet['original_context_preserved']) == 37
    assert len(packet['criteria']) == 29 and len(packet['authorized_input_evolution']) == 8
    for row in packet['references'] + packet['original_context_preserved']:
        a.verify(row)
    baseline = M.parent / ('baseline_' + packet['baseline'] + '.json')
    assert a.ref(baseline)['sha256'] == packet['baseline']
    assert a.load(baseline)['criteria'] == packet['criteria']
    initial = a.load(NC / 'input-admission.json')
    original_pairs = {r['live']['path']: r for r in initial['preimages']}
    for change in packet['authorized_input_evolution']:
        p = change['previous_packet_ref']['path']
        assert change['previous_packet_ref'] == original_pairs[p]['live']
        assert change['preserved_preimage'] == original_pairs[p]['preimage']
        a.verify(change['preserved_preimage'])
        if change['current']:
            a.verify(change['current'])
        else:
            assert not (ROOT / p).exists() and p.startswith('SKILLS-depo/ontology/explorer/assets/')
    roles = [a.ref(ROOT / p) for p in ['SOUL.md','Roles/project-sub-agent/AGENTS.md','Roles/project-sub-agent/ROLE.md']]
    previous_frontend = a.tree(FRONT, OUT)
    previous_service = a.tree(SERVICE)
    product = a.tree(APP)

    # Recursively verify enumerated evidence inventories, including predecessor
    # inventories. Arbitrary historical report contents are not live bindings.
    queue = [a.ref(NC / 'evidence-inventory.json'), a.ref(SERVICE / 'evidence-inventory.json')]
    inventories, evidence = {}, {}
    while queue:
        row = queue.pop()
        key = (row['path'], row['sha256'])
        if key in inventories:
            continue
        doc = json.loads(a.verify(row))
        inventories[key] = row
        for item in doc['files']:
            a.verify(item)
            evidence[(item['path'],item['sha256'])] = item
            if Path(item['path']).name.startswith('evidence-inventory') and item['path'].endswith('.json'):
                queue.append(item)
        for name, item in doc.items():
            if name.startswith('prior_') and isinstance(item,dict) and 'path' in item and 'sha256' in item:
                a.verify(item)
                evidence[(item['path'],item['sha256'])] = item
                if 'inventory' in name:
                    queue.append(item)
    # Direct current delivery/outputs/checks refs are checked without following
    # previous-source tuples embedded in history or historical stage manifests.
    service_delivery = a.load(SERVICE / 'delivery.json')
    for row in service_delivery['live_outputs'] + service_delivery['current_check_references']:
        a.verify(row)
    service_output = a.load(SERVICE / 'output-manifest.json')
    for row in service_output['files'] + service_output['all_runtime_members'] + [service_output['runtime_manifest']]:
        a.verify(row)
    assert a.load(NC / 'output-manifest.json')['files'] == product
    units = []
    for name, count in [('unit-06.json',6),('unit-07.json',20)]:
        record = a.load(NC / name)
        for row in record['inputs'] + record['test_inputs']:
            a.verify(row)
        report = json.loads(record['stdout'])
        assert record['exit_code'] == 0 and not record['stderr'] and report['status'] == 'passed'
        assert len(report['checks']) == count and all(x['status'] == 'passed' for x in report['checks'])
        units.append({'receipt':a.ref(NC / name),'groups':count,'current_inputs':record['inputs'] + record['test_inputs'],'qualification':report['qualification']})
    stages = []
    for number,count in [(14,1),(15,13),(16,28),(17,4),(18,7)]:
        stages.append(stage_check(a.ref(NC / f'host-browser-job-{number:02}.json')))
        record = a.load(NC / f'host-{number:02}/receipt.json')
        report_ref = a.ref(NC / f'host-{number:02}/stdout.json')
        report = json.loads(a.verify(report_ref))
        assert record['status'] == report['status'] == 'passed' and record['exit_code'] == 0
        assert record['stdout_sha256'] == report_ref['sha256'] and len(report['checks']) == count
        assert not record['post_verification_errors'] and not record['remaining_owned_descendants']
        assert not record['stderr_bytes'] and not report['page_errors'] and not report['nonlocal_requests'] and not report['csp_violations']
    sc = a.load(SERVICE / 'current-checks.json')['checks']
    service_cases = a.load(SERVICE / 'service-host-output.json')
    service_receipt = a.load(SERVICE / 'service-host-receipt.json')
    service_http = next(x for x in sc if x['id'] == 'service_http')
    assert service_cases['status'] == 'passed' and service_cases['tests_run'] == 28
    assert not service_cases['failures'] and not service_cases['errors'] and not service_cases['skips']
    assert len({x['case'] for x in service_cases['cases']}) == 28
    assert {x['case'] for x in service_cases['cases']} == set(service_http['case_ids'])
    assert service_receipt['status'] == 'failed' and service_receipt['exit_code'] == 0
    assert service_receipt['post_verification_errors'] == [{'kind':'result_validation'}]
    assert service_receipt['stdout_sha256'] == a.ref(SERVICE / 'service-host-output.json')['sha256']
    for row in service_cases['cases']:
        assert row['status'] == 'passed' and row['exit_code'] == 0 and row['inputs_unchanged']
        assert row['owned_children_reaped'] and row['observed_descendants_exited'] and not row['timed_out']
    for c in sc:
        if c['id'] in ('service_http','browser_basic','browser_late_session','browser_late_context'):
            stages.append(stage_check(c['job']))
        if c['id'].startswith('browser_') and 'groups' in c:
            receipt = json.loads(a.verify(c['receipt']))
            report = json.loads(a.verify(c['report']))
            assert receipt['status'] == report['status'] == 'passed' and receipt['exit_code'] == 0
            assert receipt['stdout_sha256'] == c['report']['sha256'] and len(report['checks']) == c['groups']
            assert not receipt['post_verification_errors'] and not receipt['remaining_owned_descendants']
    assert sum(c.get('groups',0) for c in sc if c['id'].startswith('browser_')) == 9
    stages.append(stage_check(a.ref(SERVICE / 'host-os-open-01.json')))
    stages.append(stage_check(a.ref(SERVICE / 'final-input-service-v4-native-no-geometry-job-v2.json')))

    stage = Path(a.load(NC / 'build-03.json')['stage'])
    staged_app = stage / 'SKILLS-depo/ontology/explorer'
    sources = []
    for row in a.load(NC / 'build-inputs-03.json')['inputs']['record']['files']:
        p = row['path']
        rel = 'ONTOLOGY-depo/schema/' + Path(p).name if p.startswith('$schema/') else 'SKILLS-depo/ontology/scripts/' + Path(p).name if p.startswith('$tooling/') else 'SKILLS-depo/ontology/explorer/' + p
        actual = dict(row,path=rel)
        assert a.verify(actual) == a.verify(actual,stage)
        sources.append(actual)
    assert len(sources) == 28
    assert {str(p.relative_to(APP)) for p in (APP/'src').rglob('*') if p.is_file()} == {row['path'].split('/explorer/')[1] for row in sources if '/explorer/src/' in row['path']}
    deps = a.load(NC / 'build01-dependency-admission.json')
    depfiles = [r for part in deps['file_parts'] for r in json.loads(a.verify(part))['files']]
    assert len(depfiles) == 1001
    base = Path(deps['root'])
    for row in depfiles:
        assert a.verify(row,base) == a.verify(row,staged_app)
    for root in (base,staged_app):
        files,links = set(),{}
        for parent,dirs,names in os.walk(root/'node_modules',followlinks=False):
            assert all(not (Path(parent)/d).is_symlink() for d in dirs)
            for name in names:
                p = Path(parent)/name
                rel = str(p.relative_to(root))
                if p.is_symlink():links[rel] = os.readlink(p)
                else:files.add(rel)
        assert files == {r['path'] for r in depfiles} | {'node_modules/.package-lock.json'}
        assert links == {r['path']:r['target'] for r in deps['bin_links']}
        for r in deps['bin_links']:
            assert str((root/r['path']).resolve().relative_to(root)) == r['resolved']
    assert a.verify(deps['hidden_install_lock']) == a.read(staged_app/'node_modules/.package-lock.json')
    for tool in deps['tools']:
        assert str(Path(tool['invocation']).resolve()) == tool['resolved']['path']
        a.verify(tool['resolved'])

    # Reviewed helpers below only inspect bytes and print JSON. Their static
    # actor text does not change the actual executor of this fresh audit.
    helper_results = {}
    for name,script,args in [('runtime','audit-live-runtime.py',['--expected-manifest',packet['runtime_manifest']['sha256']]),('native','verify-native-evidence-v2.py',[])]:
        script_path = SERVICE/script
        expected = next(r for r in packet['references'] if r['path'] == str(script_path.relative_to(ROOT)))
        a.verify(expected)
        command = [str(ROOT/'.venv/bin/python'),'-I','-B',str(script_path),*args]
        run = subprocess.run(command,capture_output=True,timeout=45)
        assert run.returncode == 0 and not run.stderr
        value = json.loads(run.stdout)
        with (OUT / f'{name}-audit-raw.json').open('xb') as f:f.write(run.stdout)
        helper_results[name] = {'command':command,'exit_code':run.returncode,'script':expected,'report':a.ref(OUT/f'{name}-audit-raw.json'),'executor':'/root/explorer_manager_g3/frontend_worker','qualification':'Fresh read-only execution of unchanged accepted verifier. Static raw service-worker text is not executor attribution; no new listener/browser/native/test execution.'}
    runtime = a.load(OUT/'runtime-audit-raw.json')
    assert runtime['status'] == 'passed' and len(runtime['members']) == 5
    assert runtime['build_id'] == packet['current_build_id']
    assert a.read(APP/'assets/manifest.json') == a.read(staged_app/'assets/manifest.json')
    native = a.load(OUT/'native-audit-raw.json')
    assert native['historical_original_frame_restoration']['restored'] is False
    assert native['claims']['no_change_lifecycle']['normal_stop_seconds'] == 17.949551375000738
    for row in packet['references'] + packet['original_context_preserved']:a.verify(row)
    assert previous_frontend == a.tree(FRONT,OUT) and previous_service == a.tree(SERVICE) and product == a.tree(APP)
    write('input-admission.json',{'status':'passed','packet':a.ref(PACKET),'references':packet['references'],'original_context_preserved':packet['original_context_preserved'],'authorized_input_evolution':packet['authorized_input_evolution'],'roles':roles,'write_scope':packet['write_scope'],'baseline':packet['baseline'],'round':5})
    evidence_rows = sorted(evidence.values(),key=lambda r:(r['path'],r['sha256']))
    write('inventory-closure.json',{'status':'passed','inventories':list(inventories.values()),'recursive_evidence_files':len(evidence_rows),'parts':parts('inventory-closure',evidence_rows),'interpretation':'Inventory members are pinned artifact bytes. Historical embedded source assertions are not current bindings; only eight exact admitted evolution/preimage pairs resolve old source identities. Stage-relative members are checked at each explicit job stage.'})
    write('preservation-prestate.json',{'status':'captured_and_rechecked','frontend_files':len(previous_frontend),'frontend_parts':parts('preserved-frontend',previous_frontend),'service_v4_files':len(previous_service),'service_v4_parts':parts('preserved-service',previous_service),'product_and_tests':product})
    write('current-audit.json',{'status':'passed','executor':'/root/explorer_manager_g3/frontend_worker','script':a.ref(Path(__file__)),'read_helper':a.ref(Path(spec.origin)),'packet_refs':349,'original_context_refs':37,'authorized_evolutions':8,'criteria_verbatim':29,'unit_closure':units,'unit_groups':26,'frontend_browser_groups':53,'service_cases':28,'service_original_wrapper_status':'failed_order_assumption_only_adjudicated','service_browser_groups':9,'stage_closure':stages,'authored_build_inputs':sources,'source_inventory_exact':True,'build_stage':str(stage),'dependencies_live_and_staged':1001,'dependency_links':4,'runtime_manifest':packet['runtime_manifest'],'build_id':runtime['build_id'],'runtime_members':runtime['members'],'fresh_readonly_helper_results':helper_results,'inventory_closure':a.ref(OUT/'inventory-closure.json'),'preservation':a.ref(OUT/'preservation-prestate.json'),'no_product_test_runtime_or_previous_metadata_writes':True})
    print(json.dumps({'status':'passed','packet_refs':349,'inventory_files':len(evidence_rows),'inventories':len(inventories),'prior_frontend_files':len(previous_frontend),'service_v4_files':len(previous_service),'unit_groups':26,'frontend_browser_groups':53,'service_cases':28,'service_browser_groups':9,'runtime_members':5,'build_inputs':28,'dependency_files':1001}))

if __name__ == '__main__':main()
