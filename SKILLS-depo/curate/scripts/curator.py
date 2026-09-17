#!/usr/bin/env python3
"""Selected Curator status, review, guarded commands and summary-first log access."""
import argparse
import json
import os
from pathlib import Path
import secrets
import stat
from curator_confinement import parent_descriptor
from curator_logs import DEFAULTS,MAXIMA,LogService,register_log,_json
from curator_policy import PolicyError, decision, inspect_policy, load_policy, digest, exact, require, decode


def read_registry(path):
    path=Path(path).absolute()
    with parent_descriptor('/',str(path).lstrip('/')) as (parent,name):
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
        with os.fdopen(fd,'rb') as source:
            before=os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size>1000000:raise PolicyError('log_registry','Expected a bounded regular private registry.')
            raw=source.read(1000001);after=os.fstat(source.fileno());current=os.stat(name,dir_fd=parent,follow_symlinks=False)
            identity=lambda value:(value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns)
            if len(raw)>1000000 or identity(before)!=identity(after) or identity(after)!=identity(current):raise PolicyError('log_registry','Registry changed during read.')
    value=_json(raw.decode('utf-8'))
    if (type(value) is not dict or set(value)!={'schema_version','cursor_key','logs'} or value['schema_version']!=1
            or type(value['cursor_key']) is not str or len(value['cursor_key'])!=64 or type(value['logs']) is not dict):
        raise PolicyError('log_registry','Unknown registry schema.')
    return value


def log_command(args):
    path=Path(args.registry).absolute()
    try:registry=read_registry(path)
    except FileNotFoundError:
        if args.command!='log-register':raise
        registry={'schema_version':1,'cursor_key':secrets.token_hex(32),'logs':{}}
    service=LogService(registry['logs'],cursor_key=bytes.fromhex(registry['cursor_key']))
    if args.command=='log-register':
        handle=args.handle or 'log-'+secrets.token_hex(12)
        if handle in registry['logs']:raise PolicyError('log_registered','Existing handles cannot be rebound; explicitly select a new handle.')
        registry['logs'][handle]=register_log(args.root,args.path,actor=args.actor,format=args.format)
        LogService(registry['logs'],cursor_key=bytes.fromhex(registry['cursor_key']))
        raw=json.dumps(registry,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
        if len(raw)>1000000:raise PolicyError('log_registry','Registry exceeds its 1000000-byte bound.')
        with parent_descriptor('/',str(path).lstrip('/')) as (parent,name):
            temp='.'+name+'.'+secrets.token_hex(8)
            fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            try:
                with os.fdopen(fd,'wb') as target:target.write(raw);target.flush();os.fsync(target.fileno())
                os.replace(temp,name,src_dir_fd=parent,dst_dir_fd=parent)
            finally:
                try:os.unlink(temp,dir_fd=parent)
                except FileNotFoundError:pass
        return {'state':'registered','handle':handle,'format':args.format,'hash_scope':registry['logs'][handle]['identity'].get('hash_scope','stat_identity_only')}
    if args.command=='log-list':return service.discover()
    options={key:getattr(args,key) for key in (*DEFAULTS,'cursor') if getattr(args,key,None) is not None}
    if args.command=='log-summary':return service.summary(args.handle,options=options)
    options.update({key:getattr(args,key) for key in ('mode','literal','start_line','lines','projection') if getattr(args,key,None) is not None})
    return service.query(args.handle,options)



def read_selection(path):
    """Bounded operation data only; selection files cannot carry caller authority."""
    path=Path(path).absolute()
    with parent_descriptor('/',str(path).lstrip('/')) as (parent,name):
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
        with os.fdopen(fd,'rb') as source:
            before=os.fstat(source.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=250000,
                    'selection_file','Select a bounded regular operation file.')
            raw=source.read(250001);after=os.fstat(source.fileno());current=os.stat(name,dir_fd=parent,follow_symlinks=False)
            identity=lambda v:(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
            require(identity(before)==identity(after)==identity(current),'selection_changed','Operation selection changed during read.')
    return decode(raw)


def metadata_status(policy, *, affected_paths=()):
    from curator_queue import DeliveryQueue
    from curator_awareness import assess
    result=inspect_policy(policy);project=policy['project'];items=[]
    if all(project.values()):
        queue=DeliveryQueue(project['coordination_root'],project['id'],project['repository_id'])
        with queue._directory(()) as descriptor:
            initialized=descriptor is not None and any(name in ('.delivery.lock','events','operations','cursors') for name in os.listdir(descriptor))
        if initialized: items=queue.status()
    result.update(pending=sum(row['status']!='consumed' for row in items),
                  awareness=assess(items,affected_paths=list(affected_paths)),
                  model_calls=0,canonical_writes=0,runtime_observed=False)
    if project['id'] and project['coordination_root']:
        from curator_session import configuration
        session=configuration(project['coordination_root'])
        require(session['project_id'] in (None,project['id']),'session_project','Session status belongs to another project.')
        result['session']={'enabled':session['enabled'],'mode':'project-session',
                           'unattended_background_ai':False,'bounds':session['bounds']}
        if session['enabled']:
            result.update(unattended_state=result['state'],state='installed_session_enabled')
            if not project['repository_id']:
                result['pending']=None
                result['pending_assessment']='Run session-start to observe the current repository delivery queue.'
    return result


def validate_controller_selection(project_root, selection, *, catalog_owner):
    """Validate one read-only provenance artifact for ordinary Curator intake."""
    from curator_integration import read_exact,content_hash
    from curator_policy import validate_policy
    root=Path(project_root).resolve(strict=True)
    exact(selection,('schema_version','controller','project_id','project','charter','policy','role'))
    require(type(selection['schema_version']) is int and selection['schema_version']==1
            and selection['controller']=='curator','controller_selection','Select the known Curator provenance schema.')
    exact(selection['role'],('name','agents','role'))
    refs=[selection[k] for k in ('project','charter','policy')]+[selection['role'][k] for k in ('agents','role')]
    contents={}
    for ref in refs:
        exact(ref,('path','sha256'));raw=read_exact(root,ref['path'])
        require(content_hash(raw)==ref['sha256'],'selection_source_changed','A selected controller source changed.')
        contents[ref['path']]=raw
    require(selection['project']['path']=='project.json' and selection['charter']['path']=='CURATOR.md'
            and selection['policy']['path']=='curator.yaml','controller_selection','Select the project-owned identity, charter and policy paths.')
    project=decode(contents['project.json']);policy=validate_policy(decode(contents['curator.yaml']))
    require(project.get('schema_version')==1 and project.get('project_id')==selection['project_id']==policy['project']['id']
            and policy['project']['coordination_root']==str(root),'controller_project','Controller selection must bind this exact prepared project.')
    require(policy['controller']['kind'] in (None,'curator') and policy['controller']['charter'] in (None,'CURATOR.md'),
            'controller_conflict','The current policy selects a different controller or charter.')
    catalog=catalog_owner.build_catalog(root)
    role=catalog_owner.find_valid_role(catalog,selection['role']['name'])
    require(role is not None and selection['role']['agents']=={'path':role.agents_file,'sha256':role.agents_sha256}
            and selection['role']['role']=={'path':role.role_file,'sha256':role.role_sha256},
            'controller_role_changed','The selected role pair must match the fresh filesystem catalog.')
    for ref in refs:
        require(content_hash(read_exact(root,ref['path']))==ref['sha256'],'selection_source_changed',
                'A controller source changed before validation completed.')
    return {'state':'validated','selection_sha256':digest(selection),'controller':'curator','project_id':selection['project_id'],
            'source_refs':refs,'role_catalog_fingerprint':catalog.fingerprint,
            'task_mode':{'task_schema_version':2,'orchestration_version':1},
            'task_creation':False,'manager_activation':False,'canonical_writes':0,'model_calls':0}


def review_selected_sources(owner, arguments, payload):
    """Bounded current source classifications through the existing read-only owner."""
    from curator_integration import read_exact,content_hash
    exact(arguments,('root','ownership','targets'));exact(payload,('analysis','paths'))
    require(payload['analysis']=='source-ownership' and type(payload['paths']) is list
            and 0<len(payload['paths'])<=50 and len(set(payload['paths']))==len(payload['paths']),
            'review_scope','Select one bounded source-ownership review.')
    require(type(arguments['targets']) is list and [v['identity']['path'] for v in arguments['targets']]==payload['paths'],
            'review_scope','Owner targets must match the exact requested path order.')
    snapshot={};total=0
    for target in arguments['targets']:
        exact(target,('identity','ranges'));identity=target['identity'];raw=read_exact(arguments['root'],identity['path'])
        total+=len(raw);require(total<=8000000,'review_scope','Selected review exceeds the byte bound.')
        require(content_hash(raw)==identity['sha256'],'source_changed','The selected review source changed.')
        snapshot[identity['path']]=raw
    results=[owner.classify_target(arguments['ownership'],target['identity'],target['ranges'],snapshot)
             for target in arguments['targets']]
    for path,raw in snapshot.items():
        require(content_hash(read_exact(arguments['root'],path))==content_hash(raw),
                'source_changed','A selected source changed before review completed.')
    return {'state':'reviewed' if all(v['state']=='classified' for v in results) else 'held',
            'analysis':'source-ownership','results':results,'model_calls':0,'canonical_writes':0,
            'sources':[{'path':path,'sha256':content_hash(raw)} for path,raw in snapshot.items()]}


class Application:
    """Coordinate selected operations through their existing public owners.

    The embedding host supplies the same immutable operation selections used by
    its Broker, a policy path and the canonical Task owner. Selection files are
    previews only. No application-owned execution or pause ledger is created.
    """
    ROUTES={'update':{'integration.apply','memory.publish','ontology.publish','memory.reindex','ontology.compile','ontology.wiki','task.event','task.response'},
            'correct':{'integration.apply','memory.publish','ontology.publish','task.response'},
            'retry':{'integration.recover','memory.recover','ontology.recover','memory.reindex_recover','task.recover'},
            'pause':{'task.event','runtime.interrupt','runtime.reconcile','task.response'},
            'resume':{'task.event','runtime.resume','task.response'},'review':{'target.classify'}}
    BROKER_ROUTES={'memory.publish','memory.recover','ontology.publish','ontology.recover',
                   'task.event','task.response','runtime.interrupt','runtime.reconcile','runtime.resume','target.classify'}

    DIRECT_ROUTES={'task.event':('task_state','response_transaction'),
                   'task.response':('task_state','response_transaction'),
                   'task.recover':('task_state','command_reconcile'),
                   'memory.publish':('memory_publish','publish'),
                   'memory.recover':('memory_recovery','recover'),
                   'ontology.publish':('ontology_publication','publish'),
                   'ontology.recover':('ontology_publication','recover'),
                   'target.classify':('curator_classification','classify_target')}

    def __init__(self, broker, *, policy_path, accepted_operations, task_owner, task_folder,
                 integration_owner=None, product_owners=None, product_arguments=None, log_service=None,
                 operation_owners=None, operation_arguments=None):
        from copy import deepcopy
        from curator_broker import Broker
        from curator_recovery import RecoveryController
        require(broker is None or type(broker) is Broker, 'application_unavailable', 'Select the existing operation Broker.')
        require(type(accepted_operations) is dict, 'application_selection', 'Select exact host operation metadata.')
        self.broker=broker;self.policy_path=Path(policy_path)
        self.accepted=deepcopy(accepted_operations)
        self.task=RecoveryController(task_owner,task_folder)
        self.integration=integration_owner;self.products=deepcopy(product_arguments or {})
        self.product_owners=dict(product_owners or {});self.logs=log_service
        self.operation_owners=dict(operation_owners or {})
        self.operation_arguments=deepcopy(operation_arguments or {})

    def handoff(self, utterance, offers, *, original, now, current_sources, current_authority):
        from curator_handoff import select, retain_original
        selected=select(utterance,offers,now=now,current_sources=current_sources,current_authority=current_authority)
        if selected['state']!='selected':return selected
        return {**selected,'handoff':retain_original(original,selected)}

    def status(self, *, affected_paths=()):
        result=metadata_status(load_policy(self.policy_path),affected_paths=affected_paths)
        owner=self.task.read()
        return {**result,'task':owner,'paused':owner['paused'],
                'stopping_confirmed':owner['stopping_confirmed']}

    def review(self, *, affected_paths, request=None, context=None, actor=None, origin='manual'):
        require(affected_paths and len(affected_paths)<=50,'review_scope','Select at most 50 review paths.')
        if request is not None:
            require(context is not None or actor is not None,'review_context','Operational review requires its actual selected owner.')
            exact(request['payload'],('analysis','paths'))
            require(request['payload']['analysis']=='source-ownership' and request['payload']['paths']==list(affected_paths),
                    'review_scope','Review must match the exact analysis and selected paths.')
            return self.run('review',request,context=context,actor=actor,origin=origin)
        return {**self.status(affected_paths=affected_paths),'review':'existing_metadata',
                'scope':list(affected_paths),'analysis_performed':False,'model_calls':0,'canonical_writes':0}

    def run(self, action, request, *, context=None, actor=None, origin='manual'):
        require(action in self.ROUTES and origin in ('manual','automatic'),'application_route','Select a fixed command and origin.')
        exact(request,('operation_id','payload_sha256','payload'))
        selected=self.accepted.get(request['operation_id'])
        require(selected is not None and selected['tool'] in self.ROUTES[action],
                'operation_unaccepted','The exact operation is not selected for this command.')
        require(selected['automatic']==(origin=='automatic'),'origin','The operation origin must match its host selection.')
        require(request['payload_sha256']==digest(request['payload'])==selected['payload_sha256'],
                'operation_changed','The exact selected operation payload changed.')
        tool=selected['tool']
        arguments=self.operation_arguments.get(request['operation_id'])
        self.task.gate(action,tool,request,owner_command=arguments.get('command') if arguments is not None else None)
        if action=='correct' and tool=='memory.publish':
            require(request['payload'].get('operation') in ('supersede','retract','redact'),
                    'correction_selection','Select the exact existing memory correction.')
        if tool in self.BROKER_ROUTES and arguments is None:
            require(self.broker is not None and context is not None,'operation_owner_unavailable',
                    'Select the existing Broker callback or exact direct public-owner arguments.')
            require(actor is None or actor==context.thread_id,'operation_actor','The actual callback and selected actor differ.')
            return self.broker.dispatch_verified(context,request)
        actual_actor=actor if actor is not None else getattr(context,'thread_id',None)
        require(type(actual_actor) is str and actual_actor,'operation_actor','The embedding host must supply its actual current actor.')
        binding=self.task.binding(selected['task_binding'],actor=actual_actor,allow_inactive=action in ('pause','resume','retry','review'))
        if arguments is not None:
            return self._direct_owner(tool,request,selected,arguments,binding,actual_actor)
        if tool in ('integration.apply','integration.recover'):
            from curator_integration import IntegrationOwner
            require(type(self.integration) is IntegrationOwner,'integration_unavailable','Select the existing integration owner.')
            require(request['payload']['candidate_id']==request['operation_id'],
                    'operation_changed','Integration must retain the original selected operation.')
            return self.integration.execute(request['payload'],actor=actual_actor,task_binding=binding,
                                            recovering=tool=='integration.recover')
        arguments=self.products.get(request['operation_id'])
        require(arguments is not None,'product_owner_unavailable','Select reviewed arguments for the existing product owner.')
        require(digest(arguments)==selected['owner_arguments_sha256'],'product_selection','Selected owner arguments changed.')
        from types import ModuleType
        module_name,function_name={
            'memory.reindex':('memory_maintenance','reindex'),
            'memory.reindex_recover':('memory_maintenance','recover_reindex'),
            'ontology.compile':('ontology_build','compile_project'),
            'ontology.wiki':('ontology_wiki','build_wiki')}[tool]
        owner=self.product_owners.get(module_name)
        require(isinstance(owner,ModuleType) and owner.__name__==module_name,
                'product_owner_unavailable','Select the actual public product helper module.')
        return getattr(owner,function_name)(**arguments)

    def _direct_owner(self, tool, request, selected, arguments, binding, actor):
        """Fixed public calls only; the actual owner retains its full validation."""
        from copy import deepcopy
        from types import ModuleType
        require(tool in self.DIRECT_ROUTES,'operation_owner_unavailable','No direct public owner is mapped for this operation.')
        require(digest(arguments)==selected['owner_arguments_sha256'],'operation_arguments_changed',
                'The exact reviewed owner arguments changed.')
        module_name,function_name=self.DIRECT_ROUTES[tool]
        owner=self.task.owner if module_name=='task_state' else self.operation_owners.get(module_name)
        require(isinstance(owner,ModuleType) and owner.__name__==module_name,
                'operation_owner_unavailable','Select the actual existing public owner module.')
        args=deepcopy(arguments)
        if tool.startswith('task.'):
            root=self.task.folder.parent.parent.resolve();tasks_root=self.task.folder.parent.resolve()
            require(Path(args['project_root']).resolve()==root and Path(args['tasks_root']).resolve()==tasks_root
                    and args['selector']==binding['task_id'] and args['expected_revision']==binding['revision'],
                    'task_selection','The Task operation must target this exact current canonical Task and root.')
            require(args['raw_payload']==request['payload'],'operation_payload','The selected Task payload differs.')
            if tool=='task.event':
                require(args.get('command')=='orchestrate','task_operation','Use the existing orchestration transaction.')
                event=args['raw_payload']['event']
                require(event['actor']==actor and all(event[key]==binding[key] for key in ('execution_id','generation')),
                        'task_selection','Task event actor and execution must match the current selected writer.')
            elif tool=='task.response':
                require(args.get('command') in ('record-response','pause'),'task_operation','Use the selected existing response or pause transaction.')
                require(args['raw_payload'].get('actor')==actor and all(args['raw_payload'].get(key)==binding[key] for key in ('execution_id','generation')),
                        'task_selection','Task response actor and execution must match the current selected writer.')
            else:
                require(args['raw_payload'].get('repair_type')=='transaction','task_operation','Retry only the exact existing Task transaction.')
        if tool in ('memory.publish','memory.recover'):
            require(args.get('actor')==actor,'operation_actor','Memory owner arguments must name the actual selected actor.')
        if tool=='memory.publish':
            require(args.get('payload')==request['payload'],'operation_payload','The exact memory owner payload differs.')
        if tool in ('ontology.publish','ontology.recover'):
            require(args.get('grant',{}).get('actor_id')==actor,'operation_actor','Ontology owner arguments must name the actual selected actor.')
        if tool=='ontology.publish':
            require(args.get('proposal')==request['payload'],'operation_payload','The exact ontology owner proposal differs.')
        if tool=='target.classify':return review_selected_sources(owner,args,request['payload'])
        # JSON selections retain path strings for their exact digest. Convert only
        # the fixed public helper path parameters after that comparison.
        for key in ('root','project_root','tasks_root','grant_file','journal_path'):
            if key in args:args[key]=Path(args[key])
        return getattr(owner,function_name)(**args)

    def tick(self, action, request, *, context=None, actor=None, observation, now):
        """Use fresh selected owner evidence, then the ordinary operation route.

        Observations are supplied by the embedding host, never by model tool
        arguments. They are exact views of existing owner records, not a second
        scheduler ledger. Missing or changed evidence preserves pending work.
        """
        from curator_scheduler import due, validate_observation
        policy=load_policy(self.policy_path)
        if not policy['schedule']['enabled']:
            return due(policy,branch='',now=now,usage={},iterations=0,iteration_limit=0,runtime_current=False)
        selected=self.accepted.get(request['operation_id'])
        require(selected is not None and selected['automatic'],'schedule_selection','Select an automatic operation.')
        view=validate_observation(observation,policy=policy,now=now,cost=selected['operation']['cost'])
        decision=due(policy,branch=view['branch'],now=now,pending_since=view['pending_since'],
                     last_catch_up=view['last_catch_up'],last_dependency=view['last_dependency'],
                     usage=view['usage'],iterations=view['iterations'],iteration_limit=view['iteration_limit'],
                     runtime_current=view['runtime_current'])
        if not decision['dispatch']:return decision
        return {'schedule':decision,'outcome':self.run(action,request,context=context,actor=actor,origin='automatic')}

    def log_context(self, handle, *, options=None):
        """The outgoing agent context contains a bounded summary and query route."""
        require(self.logs is not None,'logs_unavailable','Select the existing log service.')
        summary=self.logs.summary(handle,options=options)
        return {'log_summary':summary,'log_handle':handle,
                'query':{'tool':'log.query','handle':handle,'modes':['search','excerpt'],'projections':['events','tool_output'],
                         'projection_guidance':'Use events for event metadata; use tool_output for details in ordinary text logs.'},
                'instruction':'Use the summary first. Query this handle for matching events or a bounded excerpt when more evidence is needed.'}


def operation_preview(args):
    value=read_selection(args.selection)
    exact(value,('schema_version','policy_sha256','operation_id','tool','payload_sha256','payload'))
    require(value['schema_version']==1 and value['policy_sha256']==digest(load_policy(args.policy)), 'selection_changed','Policy or selection edition changed.')
    require(value['tool'] in Application.ROUTES[args.command] and value['payload_sha256']==digest(value['payload']),
            'selection_changed','Command or exact selected payload differs.')
    # A standalone file does not select an actual Task owner or its arguments.
    # The embedding host invokes Application.run with its current owner context.
    return {'state':'held','code':'authenticated_application_required','operation_id':value['operation_id'],
            'tool':value['tool'],'policy_sha256':value['policy_sha256'],'model_calls':0,'canonical_writes':0,
            'next_action':'Use this exact selection through the current Task manager and selected public owners.'}


def tick_preview(args):
    from curator_scheduler import due
    from datetime import datetime,timezone
    selected=read_selection(args.selection)
    exact(selected,('schema_version','policy','branch','pending_since','last_catch_up','last_dependency','usage','iterations','iteration_limit'))
    exact(selected['policy'],('path','sha256'))
    require(selected['schema_version']==1,'selection_version','Unknown scheduling selection.')
    policy=load_policy(selected['policy']['path'])
    require(digest(policy)==selected['policy']['sha256'],'policy_changed','Scheduling policy changed.')
    return due(policy,branch=selected['branch'],now=datetime.now(timezone.utc).isoformat(),pending_since=selected['pending_since'],
        last_catch_up=selected['last_catch_up'],last_dependency=selected['last_dependency'],usage=selected['usage'],
        iterations=selected['iterations'],iteration_limit=selected['iteration_limit'],runtime_current=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('status','validate','review'):
        command=commands.add_parser(name);command.add_argument('--policy',required=True)
        if name=='review':command.add_argument('--scope',action='append',required=True)
    for name in (name for name in Application.ROUTES if name!='review'):
        command=commands.add_parser(name);command.add_argument('--policy',required=True);command.add_argument('--selection',required=True)
    commands.add_parser('tick').add_argument('--selection',required=True)
    session=commands.add_parser('session-start');session.add_argument('--project-root',required=True);session.add_argument('--git-executable');session.add_argument('--path-offset',type=int,default=0);session.add_argument('--snapshot')
    register=commands.add_parser('log-register');register.add_argument('--registry',required=True)
    register.add_argument('--root',required=True);register.add_argument('--path',required=True)
    register.add_argument('--actor');register.add_argument('--format',choices=('native-jsonl','text'),default='native-jsonl');register.add_argument('--handle')
    commands.add_parser('log-list').add_argument('--registry',required=True)
    for name in ('log-summary','log-query'):
        command=commands.add_parser(name);command.add_argument('--registry',required=True);command.add_argument('--handle',required=True);command.add_argument('--cursor')
        for key in DEFAULTS:command.add_argument('--'+key.replace('_','-'),type=int,help='Default '+str(DEFAULTS[key])+', maximum '+str(MAXIMA[key]))
        if name=='log-query':
            command.add_argument('--mode',choices=('search','excerpt'),default='search');command.add_argument('--literal')
            command.add_argument('--start-line',type=int);command.add_argument('--lines',type=int);command.add_argument('--projection',choices=('events','tool_output'))
    args = parser.parse_args()
    try:
        if args.command.startswith('log-'):
            result=log_command(args)
            print(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False));return 0
        if args.command=='session-start':
            from curator_session import collect
            result=collect(args.project_root,git_executable=args.git_executable,path_offset=args.path_offset,expected_snapshot=args.snapshot)
        elif args.command=='tick':result=tick_preview(args)
        elif args.command in Application.ROUTES and args.command!='review':result=operation_preview(args)
        elif args.command in ('status','review'):result=metadata_status(load_policy(args.policy),affected_paths=getattr(args,'scope',()))
        else:result=inspect_policy(load_policy(args.policy))
        if args.command=='review':result.update(review='existing_metadata',analysis_performed=False)
        result['valid'] = True
    except (PolicyError, OSError,ValueError,UnicodeError) as exc:
        result = decision('unavailable' if isinstance(exc, OSError) or getattr(exc, 'code', '').endswith('_unavailable') else 'blocked', getattr(exc, 'code', 'read_failed'))
        result['valid'] = False
    print(json.dumps(result, indent=2))
    return 0 if result['valid'] and result.get('state') not in ('held','blocked','unavailable') else 2


if __name__ == '__main__':
    raise SystemExit(main())
