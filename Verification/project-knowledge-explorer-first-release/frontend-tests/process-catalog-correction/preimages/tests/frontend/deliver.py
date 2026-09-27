"""Bind a stopped provisional frontend candidate to exact current evidence."""
from pathlib import Path
import hashlib,json,stat
ROOT=Path(__file__).resolve().parents[5]
BASE=ROOT/'SKILLS-depo/ontology/explorer'
E=ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests'
TASK=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620'
BASELINE='d548997fff1e19b519c26586ca35e96bde3220cef8f5db2ecd1ebfb44c5ae79c'
def ref(p):
 p=p if p.is_absolute() else ROOT/p
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
 data=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
def write(name,value):
 raw=json.dumps(value,indent=2,ensure_ascii=False)+'\n';assert len(raw.encode())<=250000
 (E/name).write_text(raw);return ref(E/name)
manifest=json.loads((BASE/'assets/manifest.json').read_text())
build=json.loads((E/'build-19.json').read_text());assert build['status']=='passed' and build['manifest']==manifest
build_inputs=json.loads((E/'build-inputs-19.json').read_text())
for row in build_inputs['inputs']['record']['files']:
 relative=row['path']
 source=(ROOT/'ONTOLOGY-depo/schema/explorer-v1.json' if relative.startswith('$schema/') else ROOT/'SKILLS-depo/ontology/scripts/ontology_explorer_assets.py' if relative.startswith('$tooling/') else BASE/relative)
 assert ref(source)['sha256']==row['sha256'],relative
unit=json.loads((E/'unit-12.json').read_text());assert unit['exit_code']==0
for r in unit['inputs']+unit['test_inputs']:assert ref(ROOT/r['path'])['sha256']==r['sha256']
unit_report=json.loads(unit['stdout']);assert unit_report['status']=='passed'
audit=json.loads((E/'current-audit.json').read_text());assert audit['status']=='passed' and audit['build_id']==manifest['build_id']
for r in audit['current_source_files']+audit['runtime_manifest_and_members']+audit['initial_context_files']:assert ref(ROOT/r['path'])==r
current={18:'visual',19:'neutral',20:'advanced',21:'bounds'}
checks=[]
for number,kind in current.items():
 report=json.loads((E/f'browser-{number:02}-host-output.json').read_text());receipt=json.loads((E/f'browser-{number:02}-host-executor-receipt.json').read_text());inputs=json.loads((E/f'stage-browser-{number:02}-inputs.json').read_text())
 assert report['status']=='passed' and receipt['exit_code']==0 and report['stage_inputs_unchanged'] and report['owned_read_worker_reaped'] and report['observed_browser_descendants_exited']
 assert report['csp_violations']==[] and report['page_errors']==0 and report['nonlocal_requests']==0
 assert receipt['stdout_sha256']==ref(E/f'browser-{number:02}-host-output.json')['sha256']
 assert receipt['manifest_sha256']==ref(E/f'stage-browser-{number:02}-inputs.json')['sha256']
 for r in inputs['files']:
  if r['path'].startswith('SKILLS-depo/ontology/') or r['path'].startswith('ONTOLOGY-depo/'):
   assert ref(ROOT/r['path'])==r,r['path']
 checks.append({'id':kind,'status':'passed','executor':'Primary host /root under the manager-reviewed frozen disposable execution protocol; not child listener/browser execution.','report':ref(E/f'browser-{number:02}-host-output.json'),'receipt':ref(E/f'browser-{number:02}-host-executor-receipt.json'),'inputs':ref(E/f'stage-browser-{number:02}-inputs.json'),'job':ref(E/f'host-browser-job-{number:02}.json'),'checks':[r['name'] for r in report['checks']],'current_runtime_files_match':True,'qualification':report['qualification']})
checks.extend([{'id':'unit','status':'passed','receipt':ref(E/'unit-12.json'),'checks':[r['name'] for r in unit_report['checks']],'qualification':unit_report['qualification']},{'id':'build','status':'passed','receipt':ref(E/'build-19.json'),'inputs':ref(E/'build-inputs-19.json')},{'id':'audit','status':'passed','receipt':ref(E/'current-audit.json')},{'id':'visual_review','status':'qualified','receipt':ref(E/'visual-review.json')}])
checks_ref=write('current-checks.json',{'status':'provisional_current_frontend_checks_passed_with_visual_qualification','build_id':manifest['build_id'],'checks':checks,'mandatory_next_gate':'Same service owner must reverify current shared main/index/assets, followed by refreshed frontend dependency baseline and same-worker rebind.'})
# Verbatim criteria are copied without rewriting from the frozen assignment preparation.
prior=json.loads((E/'criterion-evidence-pending.json').read_text())
assignments={1:['unit','advanced','audit'],2:['unit','advanced','audit'],3:['advanced','unit'],4:['audit'],5:['visual','neutral'],6:['neutral','visual'],7:['visual','unit'],8:['advanced','visual','neutral'],9:['neutral','bounds','advanced'],10:['advanced'],11:['advanced','bounds'],12:['advanced','visual'],13:['advanced','unit'],14:['advanced','neutral'],15:['advanced','audit','visual_review'],16:['advanced','bounds','audit'],17:['advanced','bounds'],18:['advanced','bounds'],19:['advanced','visual'],20:['bounds','advanced','audit'],21:['advanced','visual','visual_review'],22:['audit','visual_review'],23:['advanced','unit','bounds'],24:['neutral','bounds'],25:['advanced','visual','neutral','visual_review'],26:['advanced','unit'],27:['advanced','unit'],28:['advanced','neutral','audit'],29:['advanced','bounds']}
source_groups={
'TASK-012':['api.ts','app.ts'], 'TASK-013':['app.ts','overview.ts','styles.css'], 'TASK-014':['search.ts','api.ts','app.ts'], 'TASK-015':['entry.ts','sources.ts','feedback.ts'], 'TASK-016':['processes.ts','sources.ts','api.ts'], 'TASK-017':['map/list.ts','map/controller.ts','app.ts'], 'TASK-018':['map/renderer.ts','map/controller.ts','app.ts'], 'TASK-019':['app.ts','api.ts','sources.ts','styles.css','map/list.ts','map/renderer.ts']}
criteria=[]
for row in prior['criteria']:
 r={k:row[k] for k in ['index','task','criterion']};r['status']='verified within provisional frontend scope; manager acceptance and shared-service rebind pending';r['check_ids']=assignments[r['index']];r['current_checks']=checks_ref;r['implementation']=[ref(BASE/'src'/name) for name in source_groups[r['task']]]
 if r['index']==25:r['status']='provisional:320CSSpixel and200percent text reflow verified; actual browser zoom remains required and unexercised, scheduled with current service V2/native check before final frontend acceptance'
 if r['index'] in [21,25]:r['qualification']='Actual synthetic Chrome views and measured labels/reflow, not VoiceOver or human comprehension. Dense inner Map labels can still crowd; no claim that every association is unobscured. Preserve the full-canvas evidence for the separately planned human comprehension gate.'
 criteria.append(r)
assert len(criteria)==29
criteria_ref=write('criterion-evidence.json',{'assignment':'FRONTEND_WORKER_G3','baseline':BASELINE,'criteria':criteria,'criterion25_remaining':'Actual browser zoom must still be directly exercised before final frontend acceptance; current200percent text sizing is not that proof.','later_scope':'TASK020-033 and full49requirement/36acceptance-test release verification are not claimed complete.'})
context_ref=write('current-context.json',{'assignment':'FRONTEND_WORKER_G3','baseline':BASELINE,'round':1,'bound_inputs':audit['initial_context_files'],'all37_hashes_unchanged':True,'integration_handoff':ref(TASK/'artifacts/orchestration/manager/frontend-integration-handoff.json'),'shared_dependency_status':'Accepted SERVICE_PACKAGE V1 remains an immutable historical dependency. Frontend has intentionally replaced live main.ts/index.html/assets; V1 shared-file verification is stale and cannot authorize final acceptance. Stop frontend writes, reverify same service owner, revise unchanged FRONTEND baseline input versions, then rebind this same frontend owner.'})
owned_names=['main.ts','api.ts','app.ts','overview.ts','search.ts','entry.ts','sources.ts','processes.ts','feedback.ts','styles.css']
owned=[ref(BASE/'index.html')]+[ref(BASE/'src'/name) for name in owned_names]+[ref(p) for p in sorted((BASE/'src/map').rglob('*')) if p.is_file()]
test_files=[ref(p) for p in sorted((BASE/'tests/frontend').rglob('*')) if p.is_file()]
output_ref=write('output-manifest.json',{'build_id':manifest['build_id'],'authored_product':owned,'frontend_test_helpers':test_files,'runtime_package_manifest':ref(BASE/'assets/manifest.json'),'runtime_member_verification':ref(E/'current-audit.json'),'runtime_boundary':'Every live runtime member is enumerated with exact hash/size by assets/manifest.json and recursively checked as a regular single-link no-follow file. The pinned434861-byte Cytoscape chunk is a product runtime asset within8MiB; it is not submitted as a250000-byte evidence document.','shared_files_requiring_SERVICE_V2':['SKILLS-depo/ontology/explorer/src/main.ts','SKILLS-depo/ontology/explorer/index.html','SKILLS-depo/ontology/explorer/assets/']})
result_ref=write('result.json',{'assignment_id':'FRONTEND_WORKER_G3','native_id':'/root/explorer_manager_g3/frontend_worker','app_thread_id':'01a0c00b-e55b-74f1-b6dc-d83eb128e100','baseline':BASELINE,'round':1,'status':'provisional_delivery_stopped_for_shared_service_reverification','outcome':'Full TASK012-019 reading frontend implemented;29exact criteria mapped to current build/unit/browser/audit evidence with explicit visual qualification.','build_id':manifest['build_id'],'criteria':criteria_ref,'checks':checks_ref,'outputs':output_ref,'context':context_ref,'boundaries':['No canonical Task, role, memory, schema, contract, dependency pin, pure-state/model/route/preferences, Python reader/service, active root installation, Template, canonical knowledge or workbench edit.','No publication or deployment.','Actual headless Chrome production checks, no OS browser-dispatch, native assistive-technology, human participant or general release-performance claim.'],'remaining_gates':['Manager reviews stopped provisional package.','Same service owner rebinds and verifies live shared package/session/bootstrap behavior as SERVICE V2.','Manager refreshes unchanged FRONTEND baseline dependency versions and rebinds this same worker for final current verification.','Actual browser zoom for criterion25 remains unexercised; manager schedules the required current native/service V2 check before final frontend acceptance.','TASK020-033 remain separately required.'],'visual_qualification':'Selected/adjacent predicate captions retain12CSSpixels at crowdedfit/zoom; exact25node26edge fullcanvas preserves some dense inner text crowding. All semantics/actions remain in List. Human comprehension remains a planned later gate.','main_task_complete':False})
# Inventory excludes the two self-referential manifests and binds all preserved history.
inventory=write('evidence-inventory.json',{'qualification':'Current evidence is identified by current-checks.json. Earlier failures/passes and unexecuted03 are retained as exact historical observations.','files':[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name not in ['delivery.json','evidence-inventory.json']]})
for p in E.rglob('*'):
 if p.is_file():assert p.stat().st_size<=250000,p
write('delivery.json',{'assignment_id':'FRONTEND_WORKER_G3','native_id':'/root/explorer_manager_g3/frontend_worker','baseline':BASELINE,'round':1,'status':'provisional_delivery_stopped_for_shared_service_reverification','result':result_ref,'criteria':criteria_ref,'checks':checks_ref,'handoff':ref(E/'HANDOFF.md'),'input_context':context_ref,'output_manifest':output_ref,'live_outputs':owned+[ref(BASE/'assets/manifest.json')],'evidence_inventory':inventory,'main_task_complete':False,'scope':'All29 original TASK012-019 criteria; mandatory SERVICE V2 current shared-file verification then FRONTEND input rebind remain. Dense Map label qualification remains for later human comprehension.'})
print(json.dumps({'status':'provisional_delivery_ready','delivery':ref(E/'delivery.json'),'criteria':len(criteria),'build_id':manifest['build_id']}))
