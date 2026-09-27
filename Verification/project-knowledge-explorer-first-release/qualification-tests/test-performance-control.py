"""Explicitly synthetic result-accounting checks; no real fixture/browser/codec work."""
from pathlib import Path
import copy, hashlib, json
Q=Path(__file__).resolve().parent
scope={};exec(compile((Q/'performance-control.py').read_bytes(),str(Q/'performance-control.py'),'exec'),scope)
checks=[]
def check(name,fn):fn();checks.append(name)
def must(value):assert value
def rejected(fn):
 try:fn()
 except (AssertionError,KeyError,ValueError):return
 raise AssertionError('Invalid synthetic result was accepted')
check('five_sample_p95_is_max_with_limit',lambda:must(scope['summarize']([1,2,3,4,5],3)=={'n':5,'median_ms':3,'p95_ms':5,'max_ms':5,'p95_method':'nearest rank ceil(.95*n), no interpolation','tail_qualification':'n<20: nearest-rank p95 is the sample maximum; limited tail inference','proposed_target_ms':3,'target_is_proposed':True,'p95_exceeds_target':True,'miss_sample_indices':[3,4]}))
check('twenty_sample_nearest_rank_is_19',lambda:must(scope['summarize'](list(range(1,21)))['p95_ms']==19))
for label,values in [('empty',[]),('nan',[float('nan')]),('infinite',[float('inf')]),('negative',[-1]),('boolean',[True])]:check('reject_'+label,lambda values=values:rejected(lambda:scope['summarize'](values)))
check('admit_only_three_passes',lambda:must(scope['browser_admission']([{'status':'passed'}]*3)['eligible']))
check('mixed_admission_unavailable',lambda:must(not scope['browser_admission']([{'status':'passed'},{'status':'bounded_refusal'},{'status':'passed'}])['eligible']))
check('failed_case_not_admission',lambda:rejected(lambda:scope['browser_admission']([{'status':'passed'},{'status':'failed'},{'status':'passed'}])))
base={'status':'passed','protected_files_unchanged':True,'outer_protected_files_unchanged':True,'owned_worker_reaped':True,'supervisor':{'limit':None,'emergency_child_signals':0}}
check('ordinary_service_protected',lambda:must(scope['validate_case']('service',base,0)=='passed'))
for field in ['protected_files_unchanged','outer_protected_files_unchanged','owned_worker_reaped']:
 bad={**base,field:False};check('reject_'+field,lambda bad=bad:rejected(lambda:scope['validate_case']('service',bad,0)))
refusal={**base,'status':'bounded_refusal','safe_code':'resource_limit'}
check('exact_service_resource_refusal',lambda:must(scope['validate_case']('service',refusal,0)=='bounded_refusal'))
check('invalid_source_is_not_capacity',lambda:rejected(lambda:scope['validate_case']('service',{**refusal,'safe_code':'source_unavailable'},0)))
supervised={'status':'supervised_refusal','outer_protected_files_unchanged':True,'supervisor':{'limit':'wall_deadline','emergency_child_signals':0}}
check('canonical_supervised_refusal_preserved',lambda:must(scope['validate_case']('canonical',supervised,-15)=='supervised_refusal'))
check('killed_child_preservation_not_exempt',lambda:rejected(lambda:scope['validate_case']('canonical',{**supervised,'outer_protected_files_unchanged':False},-15)))
check('supervision_not_service_refusal',lambda:rejected(lambda:scope['validate_case']('service',supervised,-15)))
boundary={**base,'status':'bounded_canonical_file_refusal','safe_code':'input_too_large','canonical_file_bytes':2000001,'exact_selected_path_refused':True}
check('canonical_exact_byte_path_refusal',lambda:must(scope['validate_case']('canonical_boundary',boundary,0)=='bounded_canonical_file_refusal'))
check('canonical_wrong_path_rejected',lambda:rejected(lambda:scope['validate_case']('canonical_boundary',{**boundary,'exact_selected_path_refused':False},0)))
metrics=[]
for mode,n in [('search',4),('entry',4),('map',1),('selection',4)]:
 for i in range(n):metrics.append({'mode':mode,'elapsed_ms':i+1,'actual_nodes':5,'actual_edges':7,'relationship_rows':7,'requested_nodes':25,'requested_edges':50,'response_bytes':123,'coverage':{'synthetic':True}})
cold={k:1 for k in ['child_spawn_to_first_readable_ms','package_start_to_observed_first_readable_ms','service_ready_ms','node_to_first_readable_ms','browser_launch_ms','navigation_to_first_readable_ms']}
rows=[{'status':'passed','cold_read':cold,'metrics':metrics} for _ in range(5)];summary=scope['browser_summary'](rows)
check('exact_5_cold_5_map_20_other_counts',lambda:must(summary['cold_first_read']['n']==5 and {k:v['n'] for k,v in summary['warm'].items()}=={'search':20,'entry':20,'map':5,'selection':20}))
check('map_small_sample_warning_retained',lambda:must(summary['warm']['map']['p95_ms']==summary['warm']['map']['max_ms'] and 'limited tail inference' in summary['warm']['map']['tail_qualification']))
bad=copy.deepcopy(rows);bad[0]['metrics'].pop();check('incomplete_sample_group_rejected',lambda:rejected(lambda:scope['browser_summary'](bad)))
check('browser_refusal_not_zero_latency',lambda:must('warm' not in scope['browser_summary']([{'status':'bounded_refusal'}]*5)))
print(json.dumps({'status':'passed','qualification':'Synthetic deterministic result data only. No Explorer, browser, fixture generation, compression measurement or real timing sample was executed. Not AT36 evidence.','control_sha256':hashlib.sha256((Q/'performance-control.py').read_bytes()).hexdigest(),'checks':checks,'check_count':len(checks)},indent=2))
