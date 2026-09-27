"""Read-only derived measures; no metric ledger, scheduling or lifecycle authority."""
from collections import Counter

from curator_causality import reduce_outcomes
from curator_preflight import coalesce
from curator_snapshots import current_stages
from curator_policy import require


def metrics(events, outcomes, checkpoints=()):
    require(type(events) is list and len(events) <= 5000 and len(checkpoints) <= 500,
            'metric_limit', 'Metrics inputs exceed bounded observation limits.')
    logical = coalesce(events); reduced = reduce_outcomes(outcomes)
    observed = assessed = integrated = reconciled = 0
    for checkpoint in checkpoints:
        current = current_stages(checkpoint)
        observed += current['observed']
        for stage in ('assessed', 'integrated', 'reconciled'):
            count = current[stage]
            if stage == 'assessed': assessed += count
            elif stage == 'integrated': integrated += count
            else: reconciled += count
    return {'source': 'supplied immutable delivery and owner-observation records',
            'delivery_records': len({event['event_id'] for event in events}),
            'logical_events': len(logical), 'event_types': dict(sorted(Counter(e['kind'] for e in logical).items())),
            'logical_outcomes': len(reduced), 'satisfied_effects': sum(v['state'] == 'satisfied' for v in reduced.values()),
            'held_effects': sum(v['state'] == 'held' for v in reduced.values()),
            'pending_effects': sum(v['state'] == 'pending' for v in reduced.values()),
            'observed_branches': observed, 'assessed_current': assessed,
            'integrated_current': integrated, 'reconciled_current': reconciled}


def operational_measures(events, outcomes, checkpoints=(), *, observations=None):
    """Derive measures from one caller-selected evidence set, without owner writes.

    Optional families are ephemeral views of existing owner/audit observations.
    References are retained; this calculator does not authenticate their claims.
    Missing families are unknown, while an explicitly supplied empty set is zero
    within that selected set. There is no implicit global or time-window claim.
    """
    from curator_events import reference
    from curator_policy import bounded, digest, exact, moment, sha
    observations={} if observations is None else observations
    require(type(observations) is dict and set(observations)<={'transitions','dependencies','reconciliation','runtime'},
            'metric_observations','Select only known read-only observation families.')
    sources={}
    def family(name):
        raw=observations.get(name)
        if raw is None:return None
        require(type(raw) is list and len(raw)<=5000,'metric_limit','Owner observation family exceeds its bound.')
        unique={}
        for row in raw:
            bounded(row);exact(row,('reference','value'));reference(row['reference'])
            require(type(row['value']) is dict,'metric_observation','Expected a bounded owner observation view.')
            fields={'transitions':('operation_id','path','observed_at'),'dependencies':('dependency_id',),
                    'reconciliation':('operation_id',),'runtime':()}[name]
            key=digest([row['reference'],[row['value'].get(field) for field in fields]])
            require(key not in unique or unique[key]==row,'metric_conflict','One exact source reference has conflicting projected values.')
            unique[key]=row
        sources[name]=[row['reference'] for _,row in sorted(unique.items())]
        return [row['value'] for _,row in sorted(unique.items())]
    def count(value):
        require(type(value) is int and 0<=value<=2**53-1,'metric_count','Expected a measured finite nonnegative count.')
        return value
    base=metrics(events,outcomes,checkpoints)
    unique_events={event['event_id']:event for event in events}
    reduced=reduce_outcomes(outcomes);repeated_failures=repeated_outputs=0
    for item in reduced.values():
        if item['conflict']:continue
        for before,after in zip(item['attempts'],item['attempts'][1:]):
            if before['input_sha256']!=after['input_sha256']:continue
            if before['status']!='satisfied' and after['status']!='satisfied' and before['finding_sha256']==after['finding_sha256']:repeated_failures+=1
            if before['output_sha256'] is not None and before['output_sha256']==after['output_sha256']:repeated_outputs+=1
    groups={}
    for checkpoint in checkpoints:
        current_stages(checkpoint)
        key=tuple(checkpoint[k] for k in ('project_id','repository_id','coordination_root','branch'))
        groups.setdefault(key,{})[digest(checkpoint)]=checkpoint
    stale=unknown_branches=0
    for variants in groups.values():
        if len(variants)!=1:unknown_branches+=1;continue
        current=current_stages(next(iter(variants.values())))
        if not current['observed']:unknown_branches+=1
        elif not current['reconciled']:stale+=1
    transitions=family('transitions');violations=denied_unchanged=reversals=broken_chains=None
    if transitions is not None:
        violations=denied_unchanged=reversals=broken_chains=0;by_path={}
        for row in transitions:
            exact(row,('operation_id','path','before_sha256','after_sha256','observed_at','protected','authorized','effect_attributed'))
            require(type(row['operation_id']) is str and row['operation_id'] and type(row['path']) is str and row['path'], 'metric_identity','Observed transition needs exact operation and target identity.')
            for key in ('before_sha256','after_sha256'):
                if row[key] is not None:sha(row[key])
            moment(row['observed_at'])
            require(type(row['protected']) is bool and type(row['effect_attributed']) is bool and (row['authorized'] is None or type(row['authorized']) is bool),
                    'metric_attribution','Audit attribution/authority must be explicit, with unknown authority represented by null.')
            changed=row['before_sha256']!=row['after_sha256']
            violations+=bool(changed and row['protected'] and row['authorized'] is False and row['effect_attributed'])
            denied_unchanged+=bool(not changed and row['authorized'] is False)
            if changed and row['effect_attributed']:by_path.setdefault(row['path'],[]).append(row)
        for rows in by_path.values():
            ordered=sorted(rows,key=lambda row:(moment(row['observed_at']),row['operation_id']))
            seen=[];last=None;last_at=None
            for row in ordered:
                at=moment(row['observed_at'])
                if last_at is not None and (last!=row['before_sha256'] or at==last_at):
                    broken_chains+=1;seen=[]
                if not seen:seen=[row['before_sha256']]
                if row['after_sha256'] in seen:reversals+=1
                seen.append(row['after_sha256']);last=row['after_sha256'];last_at=at
    dependencies=family('dependencies');exposed=unassessed=None
    if dependencies is not None:
        exposed=unassessed=0
        for row in dependencies:
            exact(row,('dependency_id','evidence_kind','installed_affected'))
            require(type(row['dependency_id']) is str and row['dependency_id'] and row['evidence_kind'] in ('security_advisory','release','unavailable')
                    and (row['installed_affected'] is None or type(row['installed_affected']) is bool),'metric_dependency','Dependency exposure needs attributed advisory applicability, not release recency.')
            if row['evidence_kind']=='security_advisory' and row['installed_affected'] is not None:exposed+=row['installed_affected']
            else:unassessed+=1
    reconciliation=family('reconciliation');delays=None;delay_unknown=None
    if reconciliation is not None:
        delays=[];delay_unknown=0;operations=set()
        for row in reconciliation:
            exact(row,('operation_id','started_at','reconciled_at'))
            require(type(row['operation_id']) is str and row['operation_id'] not in operations,'metric_identity','Reconciliation must supply one exact observed operation interval.')
            operations.add(row['operation_id'])
            if row['started_at'] is None or row['reconciled_at'] is None:delay_unknown+=1;continue
            start,end=moment(row['started_at']),moment(row['reconciled_at']);require(end>=start,'metric_time','Reconciliation cannot precede observed start.')
            delays.append({'operation_id':row['operation_id'],'milliseconds':int((end-start).total_seconds()*1000)})
    runtime=family('runtime');idle_calls=task_writes=knowledge_writes=None
    if runtime is not None:
        idle_calls=task_writes=knowledge_writes=0
        for row in runtime:
            exact(row,('state','counters'));require(row['state'] in ('idle','pending','unavailable','held','active'),'metric_runtime','Use an existing observed runtime/preflight state.')
            counters=row['counters'];require(type(counters) is dict and {'model_calls','task_writes','knowledge_writes'}<=counters.keys(),'metric_runtime','Exact observed call/write counters are required.')
            if row['state']=='idle':idle_calls+=count(counters['model_calls'])
            else:count(counters['model_calls'])
            task_writes+=count(counters['task_writes']);knowledge_writes+=count(counters['knowledge_writes'])
    return {'scope':'caller-selected immutable evidence set; not a global or assumed time-window total',
            'unresolved_staleness':stale,'unknown_checkpoint_branches':unknown_branches,
            'duplicate_signals':len(unique_events)-base['logical_events'],'repeated_attempt_outputs':repeated_outputs,
            'unchanged_repeated_failures':repeated_failures,'conflicting_outcome_keys':sum(row['conflict'] for row in reduced.values()),
            'observed_reversals':reversals,'broken_or_ambiguous_transition_chains':broken_chains,
            'attributed_protected_write_violations':violations,'denied_unchanged_attempts':denied_unchanged,
            'confirmed_dependency_exposure':exposed,'dependency_exposure_unassessed':unassessed,
            'reconciliation_delay_ms':delays,'reconciliation_intervals_unknown':delay_unknown,
            'idle_model_calls':idle_calls,'observed_task_writes':task_writes,'observed_knowledge_writes':knowledge_writes,
            'missing_observation_families':[name for name in ('transitions','dependencies','reconciliation','runtime') if observations.get(name) is None],
            'source_references':sources,'calculator_model_calls':0,'calculator_writes':0,'benefit_baseline':None}
