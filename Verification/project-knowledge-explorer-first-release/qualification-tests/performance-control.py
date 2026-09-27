"""Pure benchmark result accounting; imports no fixture, Explorer or browser code."""
import math, statistics

def summarize(values, target_ms=None):
    assert values and all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in values)
    ordered=sorted(values);n=len(values);p95=ordered[math.ceil(.95*n)-1]
    result={'n':n,'median_ms':statistics.median(values),'p95_ms':p95,'max_ms':max(values),'p95_method':'nearest rank ceil(.95*n), no interpolation','tail_qualification':'n<20: nearest-rank p95 is the sample maximum; limited tail inference' if n<20 else 'Observed sample percentile; no population-confidence claim'}
    if target_ms is not None:result.update(proposed_target_ms=target_ms,target_is_proposed=True,p95_exceeds_target=p95>target_ms,miss_sample_indices=[i for i,x in enumerate(values) if x>target_ms])
    return result

def validate_case(mode, report, exit_code):
    status=report.get('status')
    allowed={'generate':{'generated'},'canonical':{'passed','supervised_refusal'},'canonical_boundary':{'passed','bounded_canonical_file_refusal'},'service':{'passed','bounded_refusal'},'probe':{'passed','bounded_refusal'},'profile':{'passed'},'browser':{'passed','bounded_refusal'},'compression':{'passed'}}
    assert mode in allowed and status in allowed[mode]
    if status=='supervised_refusal':
        assert mode=='canonical' and report['supervisor']['limit'] in ('wall_deadline','supervisor_512_mib') and exit_code!=0
    else:assert exit_code==0
    if status=='bounded_refusal':assert report.get('safe_code') in ('resource_limit','deadline_exceeded')
    if status=='bounded_canonical_file_refusal':assert report.get('safe_code')=='input_too_large' and report.get('canonical_file_bytes')==2000001 and report.get('exact_selected_path_refused') is True
    if mode in ('canonical','canonical_boundary','service','probe','profile','browser') and status!='supervised_refusal':assert report.get('protected_files_unchanged') is True
    if mode in ('service','probe','browser') and status in ('passed','bounded_refusal'):assert report.get('owned_worker_reaped') is True
    if report.get('supervisor'):
        assert report['supervisor']['emergency_child_signals']==0
        if mode!='generate':assert report.get('outer_protected_files_unchanged') is True
    return status

def browser_admission(service_results):
    assert len(service_results)==3
    for r in service_results:assert r['status'] in ('passed','bounded_refusal')
    return {'eligible':all(r['status']=='passed' for r in service_results),'observed_statuses':[r['status'] for r in service_results],'qualification':'Five browser trials only for complete recipes admitted in all three actual Service runs. Any refusal/mixed admission remains recorded, not replaced by a reduced recipe.'}

def browser_summary(reports):
    passed=[r for r in reports if r['status']=='passed'];result={'attempts':len(reports),'completed':len(passed),'outcomes':[r['status'] for r in reports]}
    if not passed:return {**result,'status':'unavailable_actual_startup_refusal'}
    expected={'search':4,'entry':4,'map':1,'selection':4};targets={'search':200,'entry':250,'map':1500,'selection':100}
    for r in passed:
        for mode,n in expected.items():assert sum(m['mode']==mode for m in r['metrics'])==n
    result['cold_first_read']=summarize([r['cold_read']['child_spawn_to_first_readable_ms'] for r in passed],2000)
    result['cold_boundaries']={key:summarize([r['cold_read'][key] for r in passed]) for key in ('package_start_to_observed_first_readable_ms','service_ready_ms','node_to_first_readable_ms','browser_launch_ms','navigation_to_first_readable_ms')}
    result['warm']={mode:summarize([m['elapsed_ms'] for r in passed for m in r['metrics'] if m['mode']==mode],targets[mode]) for mode in expected}
    result['status']='complete_five_trials' if len(passed)==len(reports)==5 else 'partial_actual_startup_refusal'
    result['map_actual_counts']=[{k:m[k] for k in ('actual_nodes','actual_edges','relationship_rows','requested_nodes','requested_edges','response_bytes','coverage')} for r in passed for m in r['metrics'] if m['mode']=='map']
    return result
