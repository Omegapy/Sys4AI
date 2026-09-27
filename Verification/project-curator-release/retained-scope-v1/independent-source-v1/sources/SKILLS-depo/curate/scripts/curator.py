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
    return result


class Application:
    """One protected route for manual and automatic native callers.

    The host constructs the actual Broker and pins its complete application
    package. A file or CLI argument never becomes a native context or issuer.
    """
    ROUTES={'update':{'integration.apply','memory.publish','ontology.publish','memory.reindex','ontology.compile','ontology.wiki'},
            'correct':{'integration.apply','memory.publish','ontology.publish'},
            'retry':{'integration.recover','memory.recover','ontology.recover','memory.reindex_recover'},
            'pause':{'control.pause'},'resume':{'control.resume'},'review':{'target.classify'}}

    def handoff(self, utterance, offers, *, original, now, current_sources, current_authority):
        from curator_handoff import select, retain_original
        selected = select(utterance, offers, now=now, current_sources=current_sources, current_authority=current_authority)
        if selected['state'] != 'selected': return selected
        return {**selected, 'handoff': retain_original(original, selected)}

    def __init__(self, broker):
        from curator_broker import Broker
        require(type(broker) is Broker and broker.control is not None,'application_unavailable','Select the protected application Broker with control enabled.')
        broker._verify_owner_closure();self.broker=broker

    def status(self, *, affected_paths=()):
        result=metadata_status(load_policy(self.broker.policy_path),affected_paths=affected_paths)
        control=self.broker.control.read()
        if control is not None:
            result['paused']=control['paused'];result['pause_operation_id']=control['operation_id']
        return result

    def review(self, *, affected_paths, request=None, context=None, origin='manual'):
        require(affected_paths and len(affected_paths)<=500,'review_scope','Select the bounded review scope.')
        if request is not None:
            require(context is not None,'review_context','Operational review requires its actual authenticated callback.')
            exact(request['payload'],('analysis','paths'))
            require(request['payload']['analysis']=='source-ownership' and request['payload']['paths']==list(affected_paths),
                    'review_scope','Review must match the exact selected analysis and source paths.')
            selected=self.broker.accepted.get(request['operation_id'])
            require(selected is not None and selected['operation']['class']=='analysis','analysis_permission','Explicit analysis requires the selected analysis permission.')
            return self.run('review',request,context=context,origin=origin)
        result=self.status(affected_paths=affected_paths)
        return {**result,'review':'existing_metadata','scope':list(affected_paths),'analysis_performed':False,'model_calls':0,'canonical_writes':0}

    def run(self, action, request, *, context, origin='manual'):
        require(action in self.ROUTES and origin in ('manual','automatic'),'application_route','Select a fixed application command and origin.')
        exact(request,('operation_id','payload_sha256','payload'))
        selected=self.broker.accepted.get(request['operation_id'])
        require(selected is not None and selected['tool'] in self.ROUTES[action], 'operation_unaccepted','The exact operation is not selected for this command.')
        require(selected['automatic']==(origin=='automatic'),'origin','Manual/automatic origin is protected run metadata.')
        if action=='correct' and selected['tool']=='memory.publish':
            require(request['payload'].get('operation') in ('supersede','retract','redact'),'correction_selection','Select the exact existing memory lifecycle correction.')
        return self.broker.dispatch_verified(context,request)

    def tick(self, action, request, *, context):
        """Dispatch one previously selected automatic owner operation.

        This is an embedding entry point inside the authenticated native callback,
        not a service bootstrap. Cadence comes from protected accepted metadata;
        prior issued costs come from the existing private operation records.
        """
        from datetime import datetime,timezone
        from curator_scheduler import due
        from curator_grants import FIELDS,validate_grant
        from curator_confinement import file_snapshot
        from curator_integration import read_exact,content_hash
        require(action in ('update','correct','retry'),'scheduled_route',
                'Select an owner operation with durable exact-operation reconciliation.')
        exact(request,('operation_id','payload_sha256','payload'))
        broker=self.broker
        with broker._lock:
            selected=broker.accepted.get(request['operation_id'])
            require(selected is not None and selected['automatic'] is True and selected['tool'] in self.ROUTES[action],
                    'scheduled_operation','Select the exact automatic owner operation.')
            require(broker.pool is not None,'runtime_unavailable','The authenticated application requires its current native pool.')
            broker.native.require_current(broker.pool.protocol,context.thread_id,context.binding())
            require(selected['actor']==context.thread_id and context.tool==selected['tool'].replace('.','_')
                    and digest(request['payload'])==request['payload_sha256']==selected['payload_sha256'],
                    'operation_changed','Scheduled caller, route or selected payload differs.')
            broker._verify_owner_closure()
            broker.control.gate(selected['tool'],request)
            policy=load_policy(broker.policy_path)
            schedule=selected.get('schedule')
            exact(schedule,('policy_sha256','pending_since','last_catch_up','last_dependency','iteration_limit'))
            require(schedule['policy_sha256']==digest(policy),'policy_changed','Selected scheduling policy changed.')
            binding=selected['task']
            require(binding is not None,'schedule_owner','A scheduled operation requires its existing execution owner.')
            existing=broker.grants.inspect(request['operation_id'])
            if existing is not None and existing['state']=='consumed':
                # Receipt replay does not spend a new cadence/iteration. The
                # Broker still rechecks the exact actor, proof and post-state.
                return {'state':'replayed','dispatch':False,'preserve_pending':True,
                        'result':self.run(action,request,context=context,origin='automatic')}
            usage={key:0 for key in policy['bounds']};iterations=0;size=0;seen=set();records={};other={};owner_files={}
            files=list(broker.grants.directory.glob('*.json'))
            require(len(files)<=5000,'schedule_accounting','Private operation accounting exceeds its bounded scan.')
            for path in files:
                size+=path.lstat().st_size
                require(size<=8000000,'schedule_accounting','Private operation accounting exceeds its byte bound.')
                info=file_snapshot(broker.grants.directory,path.name,2000000)
                if path.name==broker.control.path:
                    require(digest(broker.control.read())==info['sha256'],'schedule_accounting','Current pause-control owner state changed during accounting.')
                    continue
                # Grants keep their original 250 KB cap. Owner results already
                # support 2 MB and are matched by exact recorded nonce below;
                # their payload is never parsed as a selection or charged twice.
                raw=read_exact(broker.grants.directory,path.name) if info['size']<=250000 else None
                require(raw is None or content_hash(raw)==info['sha256'],'schedule_accounting','Private record changed during accounting.')
                try:record=json.loads(raw) if raw is not None else None
                except (ValueError,UnicodeError,RecursionError) as error:
                    raise PolicyError('schedule_accounting','Private record is not its bounded owner JSON.') from error
                if type(record) is not dict or 'grant' not in record:
                    other[path.name]=info;continue
                record=decode(raw)  # Strict existing grant decoder; no owner-result scalar limits.
                broker.grants._path(path.stem)
                require(digest(record)==info['sha256'],'schedule_accounting','Private grant record changed during accounting.')
                require({'state','grant','receipt','post_state'}<=record.keys()
                        and record.keys()<={'state','grant','receipt','post_state','recovery_grant','recovery_history','recovery_of'},
                        'schedule_accounting','Unknown private grant record fields.')
                require(record.get('state') in ('issued','dispatching','owner-partial','consumed'),
                        'schedule_accounting','Unknown private operation state.')
                grants=[record['grant'],*record.get('recovery_history',[])]
                if 'recovery_grant' in record:grants.append(record['recovery_grant'])
                records[path.name]=record
                for grant in grants:
                    expected={key:grant[key] for key in FIELDS if key not in ('schema_version','nonce','issued_at','expires_at')}
                    validate_grant(grant,expected,datetime.fromisoformat(grant['issued_at'].replace('Z','+00:00')))
                    require(grant['nonce'] not in seen,'schedule_accounting','A grant nonce appears in multiple private operations.')
                    seen.add(grant['nonce'])
                    owner_files[path.stem+'-owner-'+grant['nonce']+'.json']=(record,grant)
                    if grant['issuer']!=broker.grants.issuer or grant['project']!=policy['project'] or grant['branch']!=selected['operation']['branch']:continue
                    task=grant['task']
                    if task is None or any(task[key]!=binding[key] for key in ('path','task_id','execution_id','generation')):continue
                    iterations+=1
                    for key in usage:
                        if key!='concurrent_agents':usage[key]+=grant['scope']['cost'][key]
            require(not records.keys() & owner_files.keys(),'schedule_accounting','Operation and owner-result namespaces collide.')
            for name,info in other.items():
                require(name in owner_files,'schedule_accounting','Unowned private record cannot be ignored by scheduling.')
                record,grant=owner_files[name]
                if record['state']=='consumed' and grant==record.get('recovery_grant',record['grant']):
                    require(info['sha256']==record['receipt']['result_sha256'],'schedule_accounting','Consumed owner result differs from its exact receipt.')
            for name,record in records.items():
                if record['state']=='consumed':
                    owner_name=Path(name).stem+'-owner-'+record.get('recovery_grant',record['grant'])['nonce']+'.json'
                    require(owner_name in other,'schedule_accounting','Consumed operation is missing its exact owner result.')
            usage['concurrent_agents']=broker.pool.occupied()
            common=dict(branch=selected['operation']['branch'],now=datetime.now(timezone.utc).isoformat(),
                usage=usage,iterations=iterations,iteration_limit=schedule['iteration_limit'],
                **{key:schedule[key] for key in ('pending_since','last_catch_up','last_dependency')})
            planned=due(policy,**common,runtime_current=True)
            if not planned['dispatch']:return {**planned,'usage':usage,'iterations':iterations}
            cost=selected['operation']['cost']
            if any((max(usage[key],cost[key]) if key=='concurrent_agents' else usage[key]+cost[key])>bound
                   for key,bound in policy['bounds'].items()):
                return {**planned,'state':'pending','dispatch':False,'reasons':['budget_exhausted'],
                        'usage':usage,'iterations':iterations}
            try:
                broker.pool._work();lease=broker.pool._loaded(broker.pool.for_actor(context.thread_id).reservation)
                require(lease.actor==context.actor,'runtime_unavailable','Current callback and pool incarnation differ.')
            except PolicyError as error:
                return {**planned,'state':'unavailable','dispatch':False,'reasons':[error.code],
                        'usage':usage,'iterations':iterations}
            result=self.run(action,request,context=context,origin='automatic')
            return {**planned,'state':'dispatched','result':result,'usage_before':usage,'iterations_before':iterations,
                    'runtime':{'reservation':lease.reservation,'actor':context.thread_id,'load_epoch':lease.epoch,
                               'authenticated_call_sha256':digest(context.binding())}}


def operation_preview(args):
    value=read_selection(args.selection)
    exact(value,('schema_version','policy_sha256','operation_id','tool','payload_sha256','payload'))
    require(value['schema_version']==1 and value['policy_sha256']==digest(load_policy(args.policy)), 'selection_changed','Policy or selection edition changed.')
    require(value['tool'] in Application.ROUTES[args.command] and value['payload_sha256']==digest(value['payload']),
            'selection_changed','Command or exact selected payload differs.')
    # A standalone shell has no authenticated callback. The same Application.run
    # route admits this selection only when the existing native transport calls it.
    return {'state':'held','code':'authenticated_application_required','operation_id':value['operation_id'],
            'tool':value['tool'],'policy_sha256':value['policy_sha256'],'model_calls':0,'canonical_writes':0,
            'next_action':'Use this exact selection through the current Task manager and protected native application.'}


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
        if args.command=='tick':result=tick_preview(args)
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
