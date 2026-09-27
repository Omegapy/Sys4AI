"""Guarded SERVICE V4 final assembly; requires all current host receipts before any final pass."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent;OLD=OUT.parent
PACKET=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/service-v4-input-packet.json'
def read(name):return json.loads((OUT/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):
 p=Path(p);p=p if p.is_absolute() else OUT/p
 return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def run_audit(script,name,args=()):
 command=[str(ROOT/'.venv/bin/python'),'-I','-B',str(OUT/script),*args]
 done=subprocess.run(command,capture_output=True,text=True,timeout=30);assert done.returncode==0,done.stderr
 value=json.loads(done.stdout);save(name,{'command':command,'exit_code':0,'executor':'Same service worker, read-only final/current validation','script_sha256':sha(OUT/script),'result':value});return value
assert sha(PACKET)=='09496d697ce6ee3853ecce3adbfa7297a1f3962dc9144b43df09028db9a2e6dd'
packet=json.loads(PACKET.read_text());assert ('--final' in sys.argv)!=('--prepare' in sys.argv);final='--final' in sys.argv
suffix='final' if final else 'prepared'
assert not (OUT/'result.json').exists() and not (OUT/'delivery.json').exists()
if final and (OUT/'checkpoint.json').exists():
 checkpoint=read('checkpoint.json');assert sha(OUT/'checkpoint-inventory.json')==checkpoint['inventory']['sha256']
 for row in read('checkpoint-inventory.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
 save('checkpoint-preservation-final.json',{'status':'passed','checkpoint':ref('checkpoint.json'),'inventory':ref('checkpoint-inventory.json'),'prepared_files_unchanged':len(read('checkpoint-inventory.json')['files']),'qualification':'Prior native-pending checkpoint and all prepared/failure/partial evidence retain exact bytes; current final receipts are separate files.'})
if final:
 # A fixed passing observation-admission file is written only after this worker
 # inspects actual root native values/restoration/owned cleanup, never on timeout.
 native=read('native-check.json');assert native['status']=='passed'
 assert native['actual_browser_zoom_percent']==200 and native['restored_browser_zoom_percent']==native['initial_browser_zoom_percent']
 assert native['actual_os_created_tab'] and native['owned_cleanup_verified'] and not native['zoom_substitution_used']
 assert native['prior_window_bounds_restored'] and native['narrow_navigation_observed'] and native['selected_details_identity_preserved'] and native['process_source_reading_observed']
 for row in native['evidence']:assert sha(ROOT/row['path'])==row['sha256']
 audit=run_audit('audit-inputs.py','current-audit-final.json')
 run_audit('audit-live-runtime.py','live-runtime-final.json',['--expected-manifest',packet['runtime']['manifest']['sha256']])
else:
 audit=run_audit('audit-inputs.py','current-audit-prepared.json')
 run_audit('audit-live-runtime.py','live-runtime-prepared.json',['--expected-manifest',packet['runtime']['manifest']['sha256']])
for kind,version in [('batch','01'),('browser','01'),('browser','02'),('os-open','01')]:
 for row in read('stage-'+kind+'-'+version+'-inputs.json')['files']:
  source=ROOT/row['path'] if '/' in row['path'] else OUT/row['path']
  assert sha(source)==row['sha256'],str(source)
  staged=Path('/private/tmp/explorer-service-v4-'+kind+'-'+version)/row['path']
  assert sha(staged)==row['sha256'],str(staged)
run_audit('verify-tools.py','tool-admission-'+suffix+'.json',[str(OUT/'tool-pins.json'),sha(OUT/'tool-pins.json')])
service=read('service-host-output.json');sr=read('service-host-receipt.json')
assert service['status']=='passed' and service['tests_run']==28 and service['errors']==service['failures']==service['skips']==0
assert all(c['owned_children_reaped'] and c['observed_descendants_exited'] and not c['timed_out'] for c in service['cases'])
assert sr['exit_code']==0 and sr['stderr_bytes']==0 and not sr['remaining_owned_descendants'] and not sr['emergency_signals']
assert sr['status']=='failed' and sr['post_verification_errors']==[{'kind':'result_validation'}]
assert sr['stdout_sha256']==sha(OUT/'service-host-output.json') and sr['job']['sha256']==sha(OUT/'host-batch-01.json')
adjudication=read('service-host-adjudication.json');local_adjudication=read('service-adjudication-check.json')
assert adjudication['status']=='actual_runner_passed_host_order_assumption_false_negative'
assert local_adjudication['status']=='actual_service_pass_with_original_wrapper_order_failure_preserved'
assert local_adjudication['root_adjudication_sha256']==sha(OUT/'service-host-adjudication.json') and local_adjudication['receipt_sha256']==sha(OUT/'service-host-receipt.json') and local_adjudication['stdout_sha256']==sha(OUT/'service-host-output.json')
checks=[{'id':'service_http','status':'passed','executor':'Primary host /root under exact reviewed frozen-job protocol.','receipt':ref('service-host-receipt.json'),'report':ref('service-host-output.json'),'job':ref('host-batch-01.json'),'inputs':ref('stage-batch-01-inputs.json'),'original_wrapper_status':'failed','order_only_adjudication':ref('service-host-adjudication.json'),'independent_retained_output_check':ref('service-adjudication-check.json'),'qualification':'Actual runner passed; original wrapper failed only source-order versus unittest-order validation. Exact 28-case set adjudicated without rerun; failed receipt preserved.','tests_run':28,'failures':0,'errors':0,'skips':0,'case_ids':[c['case'] for c in service['cases']],'all_owned_cleanup_verified':True}]
for mode in ['basic','late_session','late_context']:
 name=mode.replace('_','-');report=read('browser-'+name+'-stdout.json');receipt=read('browser-'+name+'-receipt.json')
 assert report['status']=='passed' and report['owned_read_worker_reaped'] and report['observed_browser_descendants_exited'] and report['fixture_regular_files_unchanged'] and report['stage_inputs_unchanged']
 assert receipt['status']=='passed' and receipt['exit_code']==0 and receipt['stdout_sha256']==sha(OUT/('browser-'+name+'-stdout.json'))
 assert receipt['post_verification_errors']==[] and not receipt['remaining_owned_descendants'] and not receipt['emergency_signals'] and receipt['stderr_bytes']==0
 assert receipt['job']['sha256']==sha(OUT/('host-browser-'+mode+'-02.json'))
 assert report['browser_version']=='151.0.7922.34' and len(report['checks'])==(7 if mode=='basic' else 1)
 assert report['tool_admission_before']['status']=='passed' and report['tool_admission_after']['status']=='passed'
 checks.append({'id':'browser_'+mode,'status':'passed','executor':'Primary host /root, actual fully pinned Headless Shell151.0.7922.34, Playwright1.62.1 isolated context. No system-Chrome equivalence.','receipt':ref('browser-'+name+'-receipt.json'),'report':ref('browser-'+name+'-stdout.json'),'job':ref('host-browser-'+mode+'-02.json'),'inputs':ref('stage-browser-02-inputs.json'),'groups':len(report['checks']),'checks':report['checks'],'browser_version':report['browser_version'],'qualification':report['qualification']})
checks.append({'id':'os_open_zoom','status':'passed' if final else 'pending_native_observation','executor':'Primary host /root actual OS-created tab/native browser controls.','job':ref('host-os-open-01.json'),'inputs':ref('stage-os-open-01-inputs.json'),'evidence':native['evidence'] if final else [ref('native-partial-receipt.json'),ref('native-partial-observation.json'),ref('native-partial-stdout.jsonl')],'observation_admission':ref('native-check.json') if final else None,'qualification':'Public CLI subprocess is current V4 service batch01. OS-open uses the verified in-process command handler; direct Playwright navigation and native zoom are separately attributed. Native Map/List200percent is not inferred.'})
checks += [
 {'id':'browser_tools','status':'passed','receipt':ref('tool-admission-'+suffix+'.json'),'pins':ref('tool-pins.json'),'verifier':ref('verify-tools.py'),'selected_external_pins':28,'headless_runtime_members':20,'qualification':'Current explicit Headless Shell revision1234/version151.0.7922.34. All selected tools and exact runtime inventory checked at host pre/post and final assembly; no system app modification or Chrome154 equivalence.'},
 {'id':'live_runtime','status':'passed','receipt':ref('live-runtime-final.json' if final else 'live-runtime-prepared.json'),'script':ref('audit-live-runtime.py'),'runtime_members':5,'oversized_runtime_member_bytes':434861,'qualification':'Accepted helper validates actual current no-follow regular single-link bytes, full imports and identity. No new build/publish.'},
 {'id':'authored_build','status':'passed','receipt':ref('current-audit-final.json' if final else 'current-audit-prepared.json'),'script':ref('audit-inputs.py'),'build_receipt':audit['build_receipt'],'build_inputs_receipt':audit['build_inputs_receipt'],'source_members':audit['authored_source_record_members'],'source_digest':audit['authored_source_digest'],'build_id':audit['build_id'],'qualification':'Current correspondence to narrow-layout correction build03 executed by original frontend owner. Earlier V1/V2/V3 bundles are historical.'},
 {'id':'error_bounds','status':'passed','receipt':ref('current-audit-final.json' if final else 'current-audit-prepared.json'),'result':audit['fixed_errors']},
 {'id':'discovery','status':'passed','receipt':ref('current-audit-final.json' if final else 'current-audit-prepared.json'),'result':audit['discovery'],'qualification':'Only unchanged discovery predicate/constants executed; watcher remains held, no Template adoption.'},
 {'id':'local_health','status':'passed','receipt':ref('local-health.json'),'script':ref('check-health-local.py'),'qualification':'Current captured test/helper bytes, no listener, bounded owned read worker and unchanged fixture.'},
 {'id':'legacy_cli','status':'passed','receipt':ref('legacy-cli.json'),'script':ref('check-legacy-cli.py'),'qualification':'Three ordinary legacy reads; knowledge/metadata identical except asserted actual helper snapshot digest. No authoring mutation or retirement.'}]
checks_name='current-checks.json' if final else 'current-checks-prepared.json'
save(checks_name,{'status':'all_current_scoped_checks_passed' if final else 'native_pending_no_partial_acceptance','checks':checks,'actual_service_observations':[o for c in service['cases'] for o in c.get('observations',[])],'qualification':('Root supplied actual listener/browser/native execution.' if final else 'Root supplied actual listener/browser execution; native execution remains pending until its exact receipt.')+' Local static checks do not claim that runtime capability. Operational RSS sampling can overshoot; no broad release-performance or main-Task completion claim.'})
prior=json.loads((OLD/'criterion-evidence-v2.json').read_text());criteria=prior['criteria'];assert [c['criterion'] for c in criteria]==packet['criteria']
check_ids={c['id'] for c in checks}
for c in criteria:
 assert set(c['check_ids'])<=check_ids
 c['status']='current_v4_reverification_passed' if final else 'pending_native_evidence' if 'os_open_zoom' in c['check_ids'] else 'current_checks_supported_pending_full_service_gate'
criteria[4]['evidence_scope']='Actual current full UI clears fragments before network, copies safe route only, and rejects consumed token on same and separate new documents. Real delayed session/context responses cannot replace a newer connection; the corrected catalog finishes its current name reads before the comparison.'
criteria[10]['evidence_scope']='Actual current public CLI process is separately covered by V4 service batch01. Actual OS-created current reader tab and required narrow navigation, selected-detail identity controls, process/source reading, 200percent browser zoom, exact prior zoom/window restoration and owned cleanup must be supported by native-check.json. No prior-version or headless substitution.'
criteria_name='criterion-evidence.json' if final else 'criterion-evidence-prepared.json'
save(criteria_name,{'baseline':prior['baseline'],'criteria':criteria,'criterion_count':14,'original_verbatim_criteria_preserved':True,'additional_native_gate':{'status':'passed' if final else 'pending','check_id':'os_open_zoom','scope':'Corrected recorded-name Processes catalog plus vertical source/process/control reading at actual200percent browser zoom, exact prior-setting restoration. Native Map/List-at200percent requires separate direct observation.'},'acceptance_authority':'Manager only. No partial service acceptance, frontend acceptance or main-Task completion by this worker.'})
products=[{**r,'read_only_dependency':True} for r in packet['references'] if (r['path'].startswith('SKILLS-depo/ontology/') or r['path']=='ONTOLOGY-depo/schema/explorer-v1.json') and '/tests/' not in r['path'] and r['bytes']<=250000]
products += packet['owned_test_sources_now_readonly'];oversized=[{**r,'path':'SKILLS-depo/ontology/explorer/assets/'+r['path']} for r in packet['runtime']['all_members'] if r['bytes']>250000]
save('output-manifest.json' if final else 'output-manifest-prepared.json',{'status':'current_readonly_production_and_test_references','files':products,'runtime_manifest':packet['runtime']['manifest'],'all_runtime_members':packet['runtime']['all_members'],'oversized_runtime_members':oversized,'production_writes':False,'test_source_writes':False,'qualification':'Direct eligible refs remain enumerable. Oversized vendor member requires live full-manifest audit, not generic250000-byte evidence admission.'})
if not final:
 print(json.dumps({'status':'prepared_native_pending','service_cases':28,'browser_groups':9,'criteria':14,'final_passed_result_created':False}));raise SystemExit(0)
assert not (OUT/'result.json').exists(),'Finalize once after all receipts and evidence edits.'
save('result.json',{'result_id':'RES_SERVICE_PACKAGE_V4','assignment_id':packet['assignment_id'],'native_id':packet['native_id'],'app_thread_id':'01a0bfa4-7254-7891-aa1d-6d1f99934493','baseline':packet['baseline'],'round':1,'state':'delivered_for_manager_acceptance','criteria_count':14,'criteria':ref(criteria_name),'checks':ref(checks_name),'handoff':ref('HANDOFF-final.md'),'live_references':ref('output-manifest.json'),'scope':'All14 original service criteria against current corrected full UI plus current native zoom gate.','summary':'28 original current-package service cases,9 full-UI browser groups,current OS-open/native200percent zoom/restoration and read-only package/build/history/health/legacy audits passed.','remaining_within_assignment':[],'production_or_original_test_changes':False,'task_memory_watcher_root_template_git_writes':False,'later_gates':['Manager service acceptance and original frontend dependency refresh','Original qualification current inputs, Safari/VoiceOver, real human comprehension and native Map/List200percent where required','Full release performance/security/offline/adoption/preservation/cutover/rollback and main-Task completion']})
current_refs={}
def refs(value):
 if isinstance(value,dict):
  if 'path' in value and 'sha256' in value and value.get('bytes',0)<=250000:current_refs[value['path']]=value
  for v in value.values():refs(v)
 elif isinstance(value,list):
  for v in value:refs(v)
refs(checks)
refs([ref('native-check.json'),ref('service-adjudication-check.json')])
files=[]
for p in sorted(OUT.iterdir()):
 if not p.is_file() or p.name in ['delivery.json','evidence-inventory.json']:continue
 assert p.stat().st_size<=250000,p.name
 assert not re.search(rb'#bootstrap=[A-Za-z0-9_-]{43}(?:[^A-Za-z0-9_-]|$)',p.read_bytes()),p.name
 files.append(ref(p))
save('evidence-inventory.json',{'status':'bounded_complete_v4_inventory','files':files,'prior_v1_delivery':ref(OLD/'delivery.json'),'prior_v2_delivery':ref(OLD/'delivery-v2.json'),'prior_v1_inventory':ref(OLD/'evidence-inventory.json'),'prior_v2_inventory':ref(OLD/'evidence-inventory-v2.json'),'prior_v3_delivery':ref(OLD/'service-v3/delivery.json'),'prior_v3_inventory':ref(OLD/'service-v3/evidence-inventory.json'),'old_evidence_files_unchanged':{'v1':67,'v2':42,'v3':56},'largest_direct_evidence_bytes':max(r['bytes'] for r in files),'qualification':'Prior evidence and current failed wrapper/browser01 receipts remain history; only final current receipts and specific retained-output adjudication establish the scoped pass. No obsolete runtime copy substitutes for live bytes.'})
save('delivery.json',{'status':'delivered_for_manager_acceptance','assignment_id':packet['assignment_id'],'native_id':packet['native_id'],'baseline':packet['baseline'],'round':1,'result':ref('result.json'),'criteria':ref(criteria_name),'checks':ref(checks_name),'handoff':ref('HANDOFF-final.md'),'context':ref('current-context-final.json'),'input_admission':ref('input-admission.json'),'current_audit':ref('current-audit-final.json'),'live_runtime_audit':ref('live-runtime-final.json'),'output_manifest':ref('output-manifest.json'),'evidence_inventory':ref('evidence-inventory.json'),'live_outputs':products,'current_check_references':list(current_refs.values()),'oversized_runtime_members':oversized,'oversized_policy':'Current whole-package accepted-helper audit and full manifest required. No generic evidence cap change.','production_files_changed':False,'original_tests_changed':False,'main_task_complete':False})
print(json.dumps({'delivery':ref('delivery.json'),'result':ref('result.json'),'live_outputs':len(products),'current_check_refs':len(current_refs),'evidence_files':len(files)}))
