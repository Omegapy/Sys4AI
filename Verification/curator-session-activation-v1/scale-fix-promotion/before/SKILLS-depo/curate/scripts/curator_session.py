"""Session-only catch-up using current Git observations and the existing queue.

This entry creates delivery signals only. Its caller remains responsible for
real Task admission, exact owner operations and attributable delivery receipts.
"""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import shutil
import time

from curator_policy import PolicyError, decode, digest, exact, load_policy, require
from curator_integration import read_exact, content_hash

CONFIG = 'curator-session.yaml'
DEFAULTS = {'schema_version': 1, 'project_id': None, 'enabled': False,
            'mode': 'project-session', 'catch_up': 'on-start-and-return',
            'unattended_background_ai': False, 'notices': 'actionable',
            'bounds': {'model_calls': 2, 'work_seconds': 30, 'candidate_bytes': 1000000,
                       'concurrent_agents': 3}, 'iteration_limit': 1, 'event_limit': 50}


def validate(value, *, project_id=None):
    exact(value, tuple(DEFAULTS));exact(value['bounds'], tuple(DEFAULTS['bounds']))
    require(value['schema_version']==1 and type(value['enabled']) is bool,
            'session_policy', 'Select the supported session policy.')
    for key in ('mode','catch_up','unattended_background_ai','notices'):
        require(value[key]==DEFAULTS[key], 'session_policy', 'Unsupported session mode: '+key)
    require(value['project_id'] is None or type(value['project_id']) is str and value['project_id'],
            'session_project', 'Select a project identity.')
    require(not value['enabled'] or value['project_id'] is not None,
            'session_project', 'A neutral Template cannot activate session maintenance.')
    if project_id is not None:require(value['project_id']==project_id,'session_project','Session policy belongs to another project.')
    for key,limit in DEFAULTS['bounds'].items():
        require(type(value['bounds'][key]) is int and 0<=value['bounds'][key]<=limit,
                'session_budget', 'Session work requires finite bounds within the supported defaults.')
    for key in ('iteration_limit','event_limit'):
        require(type(value[key]) is int and 0<=value[key]<=DEFAULTS[key], 'session_budget', 'Invalid session iteration or event bound.')
    return value


def configuration(root):
    root=Path(root).resolve(strict=True)
    try:value=decode(read_exact(root,CONFIG))
    except FileNotFoundError:return {**deepcopy(DEFAULTS),'reason':'not_adopted'}
    validate(value)
    if value['project_id'] is not None:
        identity=decode(read_exact(root,'project.json'))
        validate(value,project_id=identity['project_id'])
    return value


def collect(root, *, git_executable=None, now=None, path_offset=0, expected_snapshot=None):
    """Gather bounded current observations and retain a missed-session signal.

    No AI process is inferred from this command. A completed delivery requires
    the existing queue owner's separate exact canonical-operation receipt.
    """
    root=Path(root).resolve(strict=True);session=configuration(root)
    result={'state':'disabled','enabled':session['enabled'],'mode':'project-session',
            'runtime_observed':False,'model_calls':0,'canonical_writes':0,
            'transport_writes':0,'preserve_pending':True,'notify':False,
            'bounds':session['bounds'],'iteration_limit':session['iteration_limit'],
            'unattended_background_ai':False,'reasons':[]}
    if not session['enabled']:return result
    if not session['iteration_limit'] or not session['event_limit'] or not session['bounds']['work_seconds']:
        return {**result,'state':'pending','reasons':['budget_exhausted']}
    started=time.monotonic();now=now or datetime.now(timezone.utc).isoformat()
    policy=load_policy(root/'curator.yaml')
    require(policy['project']['id']==session['project_id'] and policy['project']['coordination_root']==str(root),
            'session_project', 'Curator policy must select this exact prepared project.')
    try:
        from curator_git import LocalGit
        from curator_queue import DeliveryQueue
        from curator_events import make_event, CONTEXT_FIELDS
        from curator_preflight import preflight
        selected=git_executable or shutil.which('git')
        require(selected is not None,'git_unavailable','No installed local Git observer is available.')
        executable=Path(selected).resolve(strict=True)
        git=LocalGit(root,executable,content_hash(executable.read_bytes()),
                     max_bytes=session['bounds']['candidate_bytes'],max_seconds=min(5,session['bounds']['work_seconds']))
        # Startup needs changed-path metadata. Full content observation remains
        # the exact operation owner's work and keeps its existing snapshot bounds.
        observed=git.changed_metadata()
        require(policy['project']['repository_id'] in (None,observed['repository_id']),
                'session_repository','The selected repository identity differs from the observed repository.')
        queue=DeliveryQueue(root,session['project_id'],observed['repository_id'])
        # A newly adopted package may have owner records but no delivery queue.
        with queue._directory(()) as descriptor:
            import os
            initialized=descriptor is not None and any(name in ('.delivery.lock','events','operations','cursors') for name in os.listdir(descriptor))
        rows=queue.status() if initialized else []
        context={key:observed[key] for key in ('repository_id','branch','snapshot','source_sha256')}
        context.update(project_id=session['project_id'],coordination_root=str(root),policy_sha256=digest(policy))
        matching=[row for row in rows if all(row['event'][key]==context[key] for key in CONTEXT_FIELDS)
                  and row['event']['kind']=='catch_up']
        old=[row for row in rows if row['event']['kind'] in ('catch_up','commit') and row['event']['branch']==context['branch']]
        previous=(matching[0]['event']['payload']['previous_commit'] if matching else
                  max(old,key=lambda row:row['event']['created_at'])['event']['payload']['commit'] if old else None)
        committed=[];commit_gap=None
        if previous!=observed['commit']:
            try:committed=git.changes(previous,observed['commit'])
            except PolicyError as error:commit_gap=error.code
        changed_paths=[*committed,*observed['changes']]
        require(type(path_offset) is int and 0<=path_offset<=len(changed_paths), 'session_page', 'Select an existing changed-path page.')
        require(not path_offset or expected_snapshot==observed['snapshot'], 'session_page_changed', 'Refresh changed paths after the observation changes.')
        require(time.monotonic()-started<=session['bounds']['work_seconds'],
                'session_time_budget','Catch-up exceeded its time budget; pending work is retained.')
        if not matching:
            event=make_event(context,'catch_up','session-'+digest(context),
                             {'previous_commit':previous,'commit':observed['commit']},created_at=now)
            added=queue.enqueue(event);result['transport_writes']=int(added['created'])
            rows.append({'event':event,'sha256':digest(event),'status':'pending','receipt':None})
        pending=[row for row in rows if row['status']!='consumed']
        selected_rows=sorted(pending,key=lambda row:(row['event']['created_at'],row['event']['event_id']))[:session['event_limit']]
        current=[row['event'] for row in selected_rows if all(row['event'][key]==context[key] for key in CONTEXT_FIELDS)]
        triage=preflight(context,events=current,ownership={'schema_version':1,'entries':[]},snapshot={},
                         relevant_paths=[],now=now,pending=bool(pending),runtime_available=False)
        held=any(row['status']=='held' for row in selected_rows)
        return {**result,'state':'pending_owner' if pending else 'idle','reasons':triage['reasons'],
                'context':context,'observation':{key:value for key,value in observed.items() if key!='changes'},
                'changed_paths':changed_paths[path_offset:path_offset+session['event_limit']],
                'remaining_changed_paths':max(0,len(changed_paths)-path_offset-session['event_limit']),
                'path_offset':path_offset,'next_path_offset':path_offset+session['event_limit'] if path_offset+session['event_limit']<len(changed_paths) else None,
                'coverage':'metadata_only','committed_delta_gap':commit_gap,
                'changed_path_count':len(changed_paths),
                'source_validation_pending':bool(pending),
                'pending':len(pending),'notify':bool(held or commit_gap),
                'events':[{'event_id':row['event']['event_id'],'status':row['status'],'kind':row['event']['kind'],
                           'sha256':row['sha256']} for row in selected_rows],
                'remaining_events':len(pending)-len(selected_rows),'triage':triage,
                'next_action':'Use the live project owner to assess this snapshot, select eligible maintenance and record its exact owner receipt.' if pending else None}
    except (PolicyError,OSError) as error:
        return {**result,'state':'pending','reasons':[getattr(error,'code','source_unavailable')],
                'catch_up_complete':False,'notify':True,
                'next_action':'The current project owner must resolve the bounded observation gap before claiming catch-up.'}


def effective_policy(root):
    """Session budgets do not enable or edit the separate unattended scheduler."""
    session=configuration(root);policy=load_policy(Path(root)/'curator.yaml')
    require(session['enabled'],'session_disabled','Project-session maintenance is disabled.')
    policy=deepcopy(policy);policy['bounds']=deepcopy(session['bounds'])
    return policy


def dispatch(application, action, request, *, root, actor, observation, now):
    """One admitted live-owner operation, with fresh current-owner usage evidence."""
    from curator_scheduler import validate_observation
    root=Path(root).resolve(strict=True);session=configuration(root)
    if not session['enabled']:return {'state':'disabled','preserve_pending':True,'notify':False}
    require(Path(application.policy_path).resolve()==root/'curator.yaml','session_project','Application policy belongs to another project.')
    selected=application.accepted.get(request['operation_id'])
    require(selected is not None and selected['automatic'],'session_selection','Select one admitted automatic owner operation.')
    policy=effective_policy(root)
    try:
        view=validate_observation(observation,policy=policy,now=now,cost=selected['operation']['cost'])
        if not view['runtime_current']:
            return {'state':'pending','reasons':['runtime_unavailable'],'preserve_pending':True,'notify':False}
        require(type(view['iterations']) is int and type(view['iteration_limit']) is int
                and 0<=view['iterations']<min(view['iteration_limit'],session['iteration_limit']),
                'budget_exhausted','This session checkpoint has exhausted its operation budget.')
    except PolicyError as error:
        if error.code=='budget_exhausted':return {'state':'pending','reasons':[error.code],'preserve_pending':True,'notify':False}
        raise
    outcome=application.run(action,request,actor=actor,origin='automatic')
    actionable=isinstance(outcome,dict) and any(outcome.get(key) in ('held','blocked','failed','conflict') for key in ('state','status'))
    return {'state':'dispatched','outcome':outcome,'runtime_observed':True,
            'preserve_pending':True,'notify':actionable,
            'receipt_required':'The live owner records delivery consumption only after its attributable completed outcome.'}
