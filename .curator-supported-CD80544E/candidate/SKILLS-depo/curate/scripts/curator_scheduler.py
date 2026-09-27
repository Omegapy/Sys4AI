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


def validate_observation(value, *, policy, now, cost):
    """Recheck a fresh host-selected view of existing usage and runtime evidence."""
    from curator_integration import read_exact,content_hash
    from curator_policy import digest,exact
    exact(value,('policy_sha256','branch','observed_at','pending_since','last_catch_up','last_dependency',
                 'usage','iterations','iteration_limit','runtime_current','evidence'))
    require(value['policy_sha256']==digest(policy),'policy_changed','Scheduling policy changed.')
    age=(moment(now)-moment(value['observed_at'])).total_seconds()
    require(0<=age<=60,'schedule_stale','Refresh the existing owner observations before another scheduling decision.')
    require(type(value['runtime_current']) is bool,'runtime_observation','Runtime availability must be explicitly observed.')
    require(type(value['evidence']) is list and 0<len(value['evidence'])<=100,
            'schedule_evidence','Select bounded existing usage and runtime evidence.')
    for item in value['evidence']:
        exact(item,('root','path','sha256'))
        require(content_hash(read_exact(item['root'],item['path']))==item['sha256'],
                'schedule_changed','Existing owner evidence changed; refresh the observation.')
    exact(value['usage'],tuple(policy['bounds']))
    exact(cost,tuple(policy['bounds']))
    for key,bound in policy['bounds'].items():
        used=value['usage'][key];reserved=cost[key]
        require(type(used) is int and used>=0 and type(reserved) is int and reserved>=0,
                'usage','Measured usage and selected reserved cost must be finite nonnegative counts.')
        require(bound is not None and (max(used,reserved) if key=='concurrent_agents' else used+reserved)<=bound,
                'budget_exhausted','Selected operation exceeds the remaining budget; pending work is retained.')
    return value
