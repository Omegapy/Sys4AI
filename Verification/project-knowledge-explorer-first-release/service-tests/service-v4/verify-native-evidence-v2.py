"""Verify reviewed claim-specific native evidence; never execute a service or UI action."""
from pathlib import Path
import hashlib,json,os,stat
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
M=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
def raw(p):
 p=Path(p);fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in p.absolute().parts[1:-1]:
   n=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=n
  f=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
  try:
   a=os.fstat(f);assert stat.S_ISREG(a.st_mode) and a.st_nlink==1
   pieces=[]
   while b:=os.read(f,65536):pieces.append(b)
   value=b''.join(pieces);b=os.fstat(f);key=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
   assert key(a)==key(b);return value
  finally:os.close(f)
 finally:os.close(fd)
def digest(p):return hashlib.sha256(raw(p)).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':digest(p),'bytes':len(raw(p))}
def read(name):return json.loads(raw(OUT/('final-input-'+name)))
packet=M/'service-v4-final-native-input-packet.json';assert digest(packet)=='63885e493b251a1a166deaf5ebf57e57fecb6b72f4c0f108e8a00bde783e5d3e'
p=json.loads(raw(packet));assert len(p['references'])==258
for r in p['references']:
 b=raw(ROOT/r['path']);assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],r['path']
assert digest(ROOT/'Roles/project-sub-agent/AGENTS.md')=='7d064ae5d5954af65fc1a83b2ce1c69562d5c31f085e70ac92c3ad0bf2e7eec2'
assert digest(ROOT/'Roles/project-sub-agent/ROLE.md')=='4c3ac5415030ab770d9af7b73fc773da43d07b041889c77a8755974284c874e2'
copies=json.loads(raw(OUT/'final-input-copies.json'))['files'];assert len(copies)==16
for row in copies:
 assert raw(ROOT/row['source']['path'])==raw(ROOT/row['copy']['path'])
 assert digest(ROOT/row['copy']['path'])==row['source']['sha256']
ui=read('service-v4-native-attempt02-native-observation.json');failed=read('service-v4-native-attempt02-receipt.json')
assert ui['actor']=='/root' and failed['actor']=='/root' and failed['status']=='failed' and not failed['stop_requested']
assert ui['native_chrome_zoom']=={'initial_percent':90,'test_percent':200,'final_percent':90,'each_observed_in_native_chrome_accessibility_ui':True}
assert ui['actual_os_dispatch'] and ui['clean_overview_route_and_bootstrap_fragment_absence_observed']
assert ui['window_and_viewport']['exact_original_bounds_restored'] is False
assert ui['window_and_viewport']['at_200_percent']['narrow_media_query_matches'] and len(ui['direct_ui_observations'])==5
assert ui['driver_receipt']['sha256']==digest(OUT/'final-input-service-v4-native-attempt02-receipt.json')
assert failed['stdout_sha256']==digest(OUT/'final-input-service-v4-native-attempt02-stdout.jsonl')
assert failed['job']['sha256']==digest(OUT/'host-os-open-01.json')
short=read('service-v4-short-attempt02-receipt.json');observation=read('service-v4-short-attempt02-root-native-observation.json')
job=read('service-v4-native-no-geometry-job-v2.json');release=read('service-v4-native-no-geometry-release-v2.json')
assert short['actor']=='/root' and observation['actor']=='/root' and short['status']=='driver_clean'
assert short['stop_requested'] and short['before_120_seconds'] and 0<short['stop_elapsed_seconds']<=job['normal_stop_latest_seconds']==120
assert short['stop_elapsed_seconds']==17.949551375000738 and short['elapsed_seconds']<job['timeout_seconds']==180
assert short['exit_code']==0 and short['stderr_bytes']==0 and not short['outer_timed_out'] and not short['emergency_signals'] and not short['remaining_owned_descendants'] and not short['post_verification_errors'] and not short['problems']
assert short['cleanup']=={'context_observed':True,'exit_code':0,'fixture_regular_files_unchanged':True,'owned_worker_reaped':True,'stage_inputs_unchanged':True}
assert short['admitted_files']==109 and short['live_file_count']==107 and short['external_tool_count']==2
assert short['job']['sha256']==digest(OUT/'final-input-service-v4-native-no-geometry-job-v2.json')
assert short['release_sha256']==digest(OUT/'final-input-service-v4-native-no-geometry-release-v2.json')
assert short['manifest_sha256']==digest(OUT/'stage-os-open-01-inputs.json')
assert short['stdout_sha256']==digest(OUT/'final-input-service-v4-short-attempt02-stdout.jsonl')
assert observation['host_receipt_sha256']==digest(OUT/'final-input-service-v4-short-attempt02-receipt.json')
assert observation['owned_blank_tab_id']=='1492113092' and observation['owned_test_tab_id']=='1492113093' and len(set(observation['baseline_browser_tab_ids']))==6
assert len(observation['observations'])==8
assert 'both owned tab IDs absent and all six baseline tab IDs present' in observation['observations'][5]
assert 'no Project Knowledge Explorer window' in observation['observations'][6]
assert observation['observations'][7]=='No geometry, zoom, preference, display, tile or window size actions were taken in this retry.'
first=read('service-v4-short-attempt01-receipt.json');first_adjudication=read('service-v4-short-attempt01-adjudication.json')
assert first_adjudication['status']=='failed_short_protocol_timing_gate_preserved' and first['stop_elapsed_seconds']>120
assert first['stdout_sha256']==digest(OUT/'final-input-service-v4-short-attempt01-stdout.jsonl')
assessment=read('service-v4-native-claim-assessment.json');mapping=read('service-v4-native-no-geometry-guard-mapping.json')
assert assessment['current_build_id']=='c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a'
assert mapping['original_full14_criteria_unchanged'] and mapping['original_full29_frontend_criteria_unchanged']
assert assessment['supported']['new_check_geometry_or_zoom_actions'] is False
print(json.dumps({'status':'supported_claim_union_with_historical_failure_retained','executor_attribution':'Primary host /root actual execution and native UI; manager reviewed claim mapping; same service worker verifies exact retained bytes only.','supplement':ref(packet),'all_supplement_refs_verified':258,'original_current_refs_verified':181,'checkpoint_files_preserved':58,'exact_copies_verified':16,'evidence':[row['copy'] for row in copies],'mapping':ref(OUT/'final-input-service-v4-native-no-geometry-guard-mapping.json'),'claims':{'native_ui_subset':{'status':'direct_partial_observation_from_failed_attempt','source':ref(OUT/'final-input-service-v4-native-attempt02-native-observation.json'),'failed_host_receipt':ref(OUT/'final-input-service-v4-native-attempt02-receipt.json'),'initial_zoom_percent':90,'observed_zoom_percent':200,'restored_zoom_percent':90,'actual_created_tab':ui['exact_created_tab_id'],'observations':ui['direct_ui_observations'],'qualification':'Exact stable entity IDs were not recorded in native subset; no full native Map/List usability claim.'},'no_change_lifecycle':{'status':'passed_reviewed_bounded_lifecycle','source':ref(OUT/'final-input-service-v4-short-attempt02-root-native-observation.json'),'receipt':ref(OUT/'final-input-service-v4-short-attempt02-receipt.json'),'normal_stop_seconds':short['stop_elapsed_seconds'],'limit_seconds':120,'all_owned_cleanup_verified':True,'baseline_tabs_preserved':6,'geometry_or_zoom_actions':False,'restoration':'not_applicable_to_this_no_action_check'}},'historical_original_frame_restoration':{'status':'false_unresolved','restored':False,'qualification':'Missing original frame/origin/identity and uncertain later interrupted resize are not repaired by the later no-change lifecycle. Original long receipt remains failed.'},'failed_short_attempt_preserved':ref(OUT/'final-input-service-v4-short-attempt01-adjudication.json'),'not_claimed':['A single fully passing native200percent walkthrough with exact original-frame restoration','New200percent observation in the short lifecycle','Full native Map/List usability','Safari Theme keyboard selection','VoiceOver speech','Participant comprehension','Manager service/frontend acceptance'],'new_test_or_ui_execution':False},indent=2))
