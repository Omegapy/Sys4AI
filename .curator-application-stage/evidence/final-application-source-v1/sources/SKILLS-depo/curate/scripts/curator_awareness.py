"""Read existing delivery metadata before dependent Task intake or continuation."""
import os
from curator_policy import require
from curator_queue import DeliveryQueue
from curator_workspace import overlaps


def assess(items, *, affected_paths, owner_conflicts=(), infrastructure_current=True):
    require(type(items) is list and len(items)<=5000,'awareness_limit','Bounded existing metadata is required.')
    result={'state':'clear','notices':[],'model_calls':0,'task_writes':0,'new_work':False}
    for row in items:
        event=row['event'];paths=[ref['path'] for ref in event['sources']]
        if event['kind']=='manual_correction': paths.append(event['payload']['request']['path'])
        paths=list(dict.fromkeys(paths))
        if not paths or not overlaps(paths,affected_paths) or row['status']=='consumed':continue
        blocked=row['status'] in ('held','blocked')
        result['notices'].append({'id':event['event_id'],'scope':paths,'level':'blocker' if blocked else 'warning' if event['kind']=='manual_correction' else 'information',
            'impact':row.get('receipt',{}).get('reason') if row.get('receipt') else event['kind'].replace('_',' '),
            'action':'Reconcile this exact owner item before dependent work.' if blocked else 'Inspect the exact relevant item.'})
        if blocked:result['state']='blocked'
    conflicts=[x for x in owner_conflicts if overlaps(x['paths'],affected_paths)]
    if conflicts:result.update(state='blocked',owner_conflicts=conflicts)
    if not infrastructure_current and (result['notices'] or conflicts):result.update(state='blocked',infrastructure='unavailable')
    return result


def inspect(root, policy, *, affected_paths, owner_conflicts=(), infrastructure_current=True):
    project=policy['project']
    if not project['id'] or not project['repository_id']:return assess([],affected_paths=affected_paths)
    require(str(root)==project['coordination_root'],'coordination_root','Read awareness at the exact selected canonical root.')
    queue=DeliveryQueue(root,project['id'],project['repository_id'])
    with queue._directory(()) as descriptor:
        initialized=descriptor is not None and any(name in ('.delivery.lock','events','operations','cursors') for name in os.listdir(descriptor))
    rows=queue.status() if initialized else []
    return assess(rows,affected_paths=affected_paths,owner_conflicts=owner_conflicts,infrastructure_current=infrastructure_current)
