"""Versioned SERVICE V4 finalization under reviewed claim mapping; preserve original guard."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent;OLD=OUT.parent
PACKET=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/service-v4-input-packet.json'
def read(name):return json.loads((OUT/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):
 p=Path(p);p=p if p.is_absolute() else OUT/p
 return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
def save(name,value):
 data=json.dumps(value,indent=2)+'\n';target=OUT/name
 assert not target.exists() or target.read_text()==data,'Refuse changed overwrite: '+name
 target.write_text(data) if not target.exists() else None
def run_audit(script,name,args=()):
 command=[str(ROOT/'.venv/bin/python'),'-I','-B',str(OUT/script),*args]
 done=subprocess.run(command,capture_output=True,text=True,timeout=30);assert done.returncode==0,done.stderr
 value=json.loads(done.stdout);save(name,{'command':command,'exit_code':0,'executor':'Same service worker, read-only final/current validation','script_sha256':sha(OUT/script),'result':value});return value
assert sha(PACKET)=='09496d697ce6ee3853ecce3adbfa7297a1f3962dc9144b43df09028db9a2e6dd'
packet=json.loads(PACKET.read_text());assert sys.argv[1:]==['--final'];final=True
SUPPLEMENT=PACKET.with_name('service-v4-final-native-input-packet.json')
assert sha(SUPPLEMENT)=='63885e493b251a1a166deaf5ebf57e57fecb6b72f4c0f108e8a00bde783e5d3e'
assert json.loads(SUPPLEMENT.read_text())['criteria']==packet['criteria']
suffix='final' if final else 'prepared'
assert not (OUT/'result.json').exists() and not (OUT/'delivery.json').exists()
if final and (OUT/'checkpoint.json').exists():
 checkpoint=read('checkpoint.json');assert sha(OUT/'checkpoint-inventory.json')==checkpoint['inventory']['sha256']
 for row in read('checkpoint-inventory.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
 save('checkpoint-preservation-final.json',{'status':'passed','checkpoint':ref('checkpoint.json'),'inventory':ref('checkpoint-inventory.json'),'prepared_files_unchanged':len(read('checkpoint-inventory.json')['files']),'qualification':'All58 prior native-pending checkpoint files and the original immutable assembler remain exact; new versioned guard/assembler implements explicitly reviewed no-geometry mapping without pretending prior_window_bounds_restored.'})
if final:
 native=run_audit('verify-native-evidence-v2.py','native-check-v2.json')
 assert native['status']=='supported_claim_union_with_historical_failure_retained'
 assert native['historical_original_frame_restoration']['restored'] is False
 assert native['claims']['no_change_lifecycle']['restoration']=='not_applicable_to_this_no_action_check'
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
checks.append({'id':'os_open_zoom','status':'supported_claim_union_with_historical_failure_retained','executor':'Primary host /root native UI and execution; manager-reviewed claim mapping.','job':ref('host-os-open-01.json'),'no_geometry_job':ref('final-input-service-v4-native-no-geometry-job-v2.json'),'inputs':ref('stage-os-open-01-inputs.json'),'evidence':native['evidence'],'observation_admission':ref('native-check-v2.json'),'guard':ref('verify-native-evidence-v2.py'),'claims':native['claims'],'historical_original_frame_restoration':native['historical_original_frame_restoration'],'qualification':'Current public CLI is independently covered by service batch01. Failed long native02 supplies only exact listed200percent/90percent UI observations. Passed short02 supplies normalSTOP/owned cleanup with no geometry/zoom actions. The old frame remains unresolved; no single full native walkthrough or complete Map/List usability is claimed.'})
checks += [
 {'id':'browser_tools','status':'passed','receipt':ref('tool-admission-'+suffix+'.json'),'pins':ref('tool-pins.json'),'verifier':ref('verify-tools.py'),'selected_external_pins':28,'headless_runtime_members':20,'qualification':'Current explicit Headless Shell revision1234/version151.0.7922.34. All selected tools and exact runtime inventory checked at host pre/post and final assembly; no system app modification or Chrome154 equivalence.'},
 {'id':'live_runtime','status':'passed','receipt':ref('live-runtime-final.json' if final else 'live-runtime-prepared.json'),'script':ref('audit-live-runtime.py'),'runtime_members':5,'oversized_runtime_member_bytes':434861,'qualification':'Accepted helper validates actual current no-follow regular single-link bytes, full imports and identity. No new build/publish.'},
 {'id':'authored_build','status':'passed','receipt':ref('current-audit-final.json' if final else 'current-audit-prepared.json'),'script':ref('audit-inputs.py'),'build_receipt':audit['build_receipt'],'build_inputs_receipt':audit['build_inputs_receipt'],'source_members':audit['authored_source_record_members'],'source_digest':audit['authored_source_digest'],'build_id':audit['build_id'],'qualification':'Current correspondence to narrow-layout correction build03 executed by original frontend owner. Earlier V1/V2/V3 bundles are historical.'},
 {'id':'error_bounds','status':'passed','receipt':ref('current-audit-final.json' if final else 'current-audit-prepared.json'),'result':audit['fixed_errors']},
 {'id':'discovery','status':'passed','receipt':ref('current-audit-final.json' if final else 'current-audit-prepared.json'),'result':audit['discovery'],'qualification':'Only unchanged discovery predicate/constants executed; watcher remains held, no Template adoption.'},
 {'id':'local_health','status':'passed','receipt':ref('local-health.json'),'script':ref('check-health-local.py'),'qualification':'Current captured test/helper bytes, no listener, bounded owned read worker and unchanged fixture.'},
 {'id':'legacy_cli','status':'passed','receipt':ref('legacy-cli.json'),'script':ref('check-legacy-cli.py'),'qualification':'Three ordinary legacy reads; knowledge/metadata identical except asserted actual helper snapshot digest. No authoring mutation or retirement.'}]
checks_name='current-checks.json' if final else 'current-checks-prepared.json'
save(checks_name,{'status':'all_current_scoped_claims_supported_with_historical_native_failure','checks':checks,'actual_service_observations':[o for c in service['cases'] for o in c.get('observations',[])],'qualification':('Root supplied actual listener/browser/native evidence. Native claim support combines a failed long UI attempt and a separately passed no-change lifecycle; exact old frame restoration remains false/unresolved.' if final else 'Root supplied actual listener/browser execution; native execution remains pending until its exact receipt.')+' Local static checks do not claim that runtime capability. Operational RSS sampling can overshoot; no broad release-performance or main-Task completion claim.'})
prior=json.loads((OLD/'criterion-evidence-v2.json').read_text());criteria=prior['criteria'];assert [c['criterion'] for c in criteria]==packet['criteria']
check_ids={c['id'] for c in checks}
for c in criteria:
 assert set(c['check_ids'])<=check_ids
 c['status']='current_v4_supported_for_manager_review';c['historical_native_limitation']=native['historical_original_frame_restoration'] if 'os_open_zoom' in c['check_ids'] else None
criteria[4]['evidence_scope']='Actual current full UI clears fragments before network, copies safe route only, and rejects consumed token on same and separate new documents. Real delayed session/context responses cannot replace a newer connection; the corrected catalog finishes its current name reads before the comparison.'
criteria[10]['evidence_scope']='Actual public CLI launch is current V4 service batch01. Exact current native200percent UI and90percent zoom restoration observations are retained from failed long native02. Separate short02 proves clean OS-created context, normalSTOP17.9496seconds and owned cleanup without geometry/zoom actions. Exact old window restoration remains false/unresolved; no passed-old-attempt claim or headless substitution.'
criteria_name='criterion-evidence.json' if final else 'criterion-evidence-prepared.json'
save(criteria_name,{'baseline':prior['baseline'],'criteria':criteria,'criterion_count':14,'original_verbatim_criteria_preserved':True,'additional_native_gate':{'status':'supported_claim_union_with_historical_failure_retained','check_id':'os_open_zoom','scope':'Exact listed current controls/process/source/details observations and200-to90percent zoom from failed long02; separate bounded no-change lifecycle supports normalSTOP and owned cleanup. Old frame restoration false/unresolved; no complete nativeMap/List claim.','mapping':ref('final-input-service-v4-native-no-geometry-guard-mapping.json')},'acceptance_authority':'Manager only. No partial service acceptance, frontend acceptance or main-Task completion by this worker.'})
products=[{**r,'read_only_dependency':True} for r in packet['references'] if (r['path'].startswith('SKILLS-depo/ontology/') or r['path']=='ONTOLOGY-depo/schema/explorer-v1.json') and '/tests/' not in r['path'] and r['bytes']<=250000]
products += packet['owned_test_sources_now_readonly'];oversized=[{**r,'path':'SKILLS-depo/ontology/explorer/assets/'+r['path']} for r in packet['runtime']['all_members'] if r['bytes']>250000]
save('output-manifest.json' if final else 'output-manifest-prepared.json',{'status':'current_readonly_production_and_test_references','files':products,'runtime_manifest':packet['runtime']['manifest'],'all_runtime_members':packet['runtime']['all_members'],'oversized_runtime_members':oversized,'production_writes':False,'test_source_writes':False,'qualification':'Direct eligible refs remain enumerable. Oversized vendor member requires live full-manifest audit, not generic250000-byte evidence admission.'})
if not final:
 print(json.dumps({'status':'prepared_native_pending','service_cases':28,'browser_groups':9,'criteria':14,'final_passed_result_created':False}));raise SystemExit(0)
assert not (OUT/'result.json').exists(),'Finalize once after all receipts and evidence edits.'
save('result.json',{'result_id':'RES_SERVICE_PACKAGE_V4','assignment_id':packet['assignment_id'],'native_id':packet['native_id'],'app_thread_id':'01a0bfa4-7254-7891-aa1d-6d1f99934493','baseline':packet['baseline'],'round':1,'state':'delivered_for_manager_acceptance','criteria_count':14,'criteria':ref(criteria_name),'checks':ref(checks_name),'handoff':ref('HANDOFF-final.md'),'live_references':ref('output-manifest.json'),'scope':'All14 unchanged service criteria against current full UI with reviewed claim-specific native evidence and historical failure limitations.','summary':'28 service cases and9 full-UI browser groups pass. Current native200percent UI subset comes from a failed long attempt; a separate no-change lifecycle passes normalSTOP/owned cleanup. Current package/build/source/history/tool audits match.','native_claim_status':'supported_claim_union_with_historical_failure_retained','historical_unresolved':native['historical_original_frame_restoration'],'native_not_claimed':native['not_claimed'],'final_input_packet':ref(SUPPLEMENT),'remaining_within_assignment':[],'production_or_original_test_changes':False,'task_memory_watcher_root_template_git_writes':False,'later_gates':['Manager service acceptance and original frontend dependency refresh','Original qualification current inputs, Safari/VoiceOver, real human comprehension and native Map/List200percent where required','Full release performance/security/offline/adoption/preservation/cutover/rollback and main-Task completion']})
current_refs={}
def refs(value):
 if isinstance(value,dict):
  if 'path' in value and 'sha256' in value and value.get('bytes',0)<=250000:current_refs[value['path']]=value
  for v in value.values():refs(v)
 elif isinstance(value,list):
  for v in value:refs(v)
refs(checks)
refs([ref('native-check-v2.json'),ref('verify-native-evidence-v2.py'),ref('service-adjudication-check.json'),ref('checkpoint-preservation-final.json'),ref(SUPPLEMENT)])
files=[]
for p in sorted(OUT.iterdir()):
 if not p.is_file() or p.name in ['delivery.json','evidence-inventory.json']:continue
 assert p.stat().st_size<=250000,p.name
 assert not re.search(rb'#bootstrap=[A-Za-z0-9_-]{43}(?:[^A-Za-z0-9_-]|$)',p.read_bytes()),p.name
 files.append(ref(p))
save('evidence-inventory.json',{'status':'bounded_complete_v4_inventory','files':files,'prior_v1_delivery':ref(OLD/'delivery.json'),'prior_v2_delivery':ref(OLD/'delivery-v2.json'),'prior_v1_inventory':ref(OLD/'evidence-inventory.json'),'prior_v2_inventory':ref(OLD/'evidence-inventory-v2.json'),'prior_v3_delivery':ref(OLD/'service-v3/delivery.json'),'prior_v3_inventory':ref(OLD/'service-v3/evidence-inventory.json'),'old_evidence_files_unchanged':{'v1':67,'v2':42,'v3':56},'largest_direct_evidence_bytes':max(r['bytes'] for r in files),'qualification':'Prior evidence and current failed wrapper/browser01 receipts remain history; only final current receipts and specific retained-output adjudication establish the scoped pass. No obsolete runtime copy substitutes for live bytes.'})
save('delivery.json',{'status':'delivered_for_manager_acceptance','assignment_id':packet['assignment_id'],'native_id':packet['native_id'],'baseline':packet['baseline'],'round':1,'result':ref('result.json'),'criteria':ref(criteria_name),'checks':ref(checks_name),'handoff':ref('HANDOFF-final.md'),'context':ref('current-context-final.json'),'input_admission':ref('input-admission.json'),'final_input_packet':ref(SUPPLEMENT),'checkpoint_preservation':ref('checkpoint-preservation-final.json'),'native_claim_mapping':ref('native-check-v2.json'),'historical_unresolved':native['historical_original_frame_restoration'],'current_audit':ref('current-audit-final.json'),'live_runtime_audit':ref('live-runtime-final.json'),'output_manifest':ref('output-manifest.json'),'evidence_inventory':ref('evidence-inventory.json'),'live_outputs':products,'current_check_references':list(current_refs.values()),'oversized_runtime_members':oversized,'oversized_policy':'Current whole-package accepted-helper audit and full manifest required. No generic evidence cap change.','production_files_changed':False,'original_tests_changed':False,'main_task_complete':False})
print(json.dumps({'delivery':ref('delivery.json'),'result':ref('result.json'),'live_outputs':len(products),'current_check_refs':len(current_refs),'evidence_files':len(files)}))
