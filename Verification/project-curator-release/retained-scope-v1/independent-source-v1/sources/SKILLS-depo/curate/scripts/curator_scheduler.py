"""Deterministic scheduling decisions from selected policy and actual usage."""
from datetime import timedelta
from curator_policy import inspect_policy, moment, require


def due(policy, *, branch, now, pending_since=None, last_catch_up=None, last_dependency=None,
        usage, iterations, iteration_limit, runtime_current):
    current=moment(now);schedule=policy['schedule']
    empty={'state':'idle','dispatch':False,'reasons':[],'preserve_pending':True,'model_calls':0}
    if not schedule['enabled']:return empty
    if branch not in policy['branches'] or any(policy['project'][k] is None for k in ('id','repository_id','coordination_root')):
        return {**empty,'state':'held','reasons':['project_or_branch_unselected']}
    require(type(iterations) is int and type(iteration_limit) is int and 0<=iterations<=2147483647 and iteration_limit>=0,
            'iteration_bound','Select a finite iteration limit.')
    exhausted=iterations>=iteration_limit
    for key,bound in policy['bounds'].items():
        require(type(usage.get(key)) is int and usage[key]>=0,'usage','Actual usage counters are required.')
        # The caller already occupies its admitted slot. Equal concurrency is
        # allowed for work within that slot; acquiring another slot is separate.
        exhausted |= bound is None or (usage[key]>bound if key=='concurrent_agents' else usage[key]>=bound)
    if exhausted:return {**empty,'state':'pending','reasons':['budget_exhausted']}
    reasons=[]
    for key,previous,reason in [('debounce_seconds',pending_since,'pending_work'),('catch_up_seconds',last_catch_up,'catch_up'),
                                 ('dependency_cadence_seconds',last_dependency,'dependency_due')]:
        seconds=schedule[key]
        if seconds is None:return {**empty,'state':'held','reasons':['cadence_unselected']}
        if key=='debounce_seconds' and previous is None:continue
        if previous is None or current>=moment(previous)+timedelta(seconds=seconds):reasons.append(reason)
    if not reasons:return empty
    return {**empty,'state':'due' if runtime_current else 'unavailable','dispatch':bool(runtime_current),
            'reasons':reasons if runtime_current else [*reasons,'runtime_unavailable']}
