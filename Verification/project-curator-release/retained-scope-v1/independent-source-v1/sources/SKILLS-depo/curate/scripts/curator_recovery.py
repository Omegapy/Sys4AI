"""Trusted pause control over the existing native pool and owner operation store."""
from copy import deepcopy
from pathlib import Path
import json
from curator_integration import read_exact, replace_exact, content_hash
from curator_policy import canonical, exact, require

READ_OR_RECOVERY = {'policy.inspect','target.classify','artifact.read','artifact.submit','log.summary','log.query',
    'runtime.observe','runtime.interrupt','runtime.release','runtime.reconcile','memory.recover','ontology.recover',
    'integration.recover','memory.reindex_recover','control.pause','control.resume','task.response'}
OWNER_EVENTS = {'assignment.observe','assignment.uncertain','assignment.revoke','manager.reconnect','manager.replace','stop.request','stop.finish','execution.resume'}


class RecoveryController:
    """Opt-in protected application control; legacy Broker defaults remain intact."""
    def __init__(self, broker):
        self.broker=broker;self.directory=broker.grants.directory
        require(self.directory.is_relative_to(broker.owners.root),'control_scope','Application control storage must belong to its selected project.')
        self.path='.pause-control.json'
        self.relative=(self.directory/self.path).relative_to(broker.owners.root).as_posix()

    def read(self):
        raw=read_exact(self.directory,self.path,missing=True)
        if raw is None:return None
        record=json.loads(raw)
        exact(record,('schema_version','paused','actor','execution_id','generation','operation_id','reason','reservations','requests','revoked_operations','history'))
        require(record['schema_version']==1 and type(record['paused']) is bool,'control_state','Unknown pause state.')
        return record

    def gate(self, tool, request):
        record=self.read()
        if record is None:return
        operation_id=request.get('operation_id') if type(request) is dict else None
        require(operation_id not in record['revoked_operations'],'operation_revoked','A pre-pause work selection cannot issue a future grant.')
        if not record['paused']:return
        owner_event=tool=='task.event' and request.get('payload',{}).get('kind') in OWNER_EVENTS
        require(tool in READ_OR_RECOVERY or owner_event,'execution_paused','New work is held while the current owners reconcile pause.')

    def preflight(self, accepted, *, tool, payload, context, state, operation_id):
        current=content_hash(read_exact(self.directory,self.path,missing=True))
        require({'path':self.relative,'sha256':current} in accepted['owner_state']['inputs'],
                'control_predecessor','The accepted control operation must bind its exact prior durable state.')
        require(any(self.relative==p or self.relative.startswith(p.rstrip('/')+'/') for p in accepted['operation']['paths']),
                'control_scope','Pause metadata is outside the selected control scope.')
        record = self.read()
        if tool == 'control.resume':
            self._resume_ready(record, payload, actor=context.thread_id, state=state, operation_id=operation_id)
        else:
            require(record is None or not record['paused'], 'already_paused', 'The original pause must be reconciled first.')


    def apply(self, tool, payload, *, context, accepted, state, operation_id):
        pool=self.broker.pool;require(pool is not None,'runtime_unavailable','Application pause requires the selected real native pool.')
        current=self.read();raw=read_exact(self.directory,self.path,missing=True)
        actor=context.thread_id;execution=state['orchestration']['execution_id'];generation=state['orchestration']['generation']
        if tool=='control.pause':
            exact(payload,('reason',));require(type(payload['reason']) is str and 0<len(payload['reason'])<=2000,'pause_reason','Supply a bounded pause reason.')
            require(current is None or not current['paused'],'already_paused','Reconcile the existing pause operation instead of creating another.')
            manager_reservation = pool.for_actor(actor).reservation
            reservations=sorted(name for name,lease in pool.leases.items() if name not in (pool.controller,manager_reservation) and lease.state!='released')
            require(sorted(accepted['runtime_reservations'])==reservations,'pause_scope','Pause must account for every unresolved actor in this selected execution.')
            revoked=sorted(set((current or {}).get('revoked_operations',[])) |
                {key for key,value in self.broker.accepted.items() if value['tool'] not in READ_OR_RECOVERY})
            record={'schema_version':1,'paused':True,'actor':actor,'execution_id':execution,'generation':generation,'operation_id':operation_id,
                'reason':payload['reason'],'reservations':reservations,'requests':[],'revoked_operations':revoked,
                'history':[] if current is None else [*current['history'],{k:v for k,v in current.items() if k!='history'}]}
            # Admission closes durably before interruption I/O. Interrupt receipts
            # remain requests; only the native owner's release proves stopping.
            replace_exact(self.directory,self.path,canonical(record),content_hash(raw))
            for index,name in enumerate(reservations):
                lease=pool.leases[name]
                if lease.state=='queued':row={'reservation':name,'state':'not_started'}
                else:
                    try:
                        handle=pool.interrupt(name,operation_id+'-interrupt-'+str(index))
                        row={'reservation':name,'state':'interrupt_requested','observation':handle}
                    except Exception as error:
                        row={'reservation':name,'state':'uncertain','code':getattr(error,'code',type(error).__name__)}
                record['requests'].append(row)
                old=read_exact(self.directory,self.path);replace_exact(self.directory,self.path,canonical(record),content_hash(old))
            return {'state':'paused','journal_path':self.relative,'requests':record['requests'],'stopping_confirmed':False}
        self._resume_ready(current, payload, actor=actor, state=state, operation_id=operation_id)
        current['history'].append({k:deepcopy(v) for k,v in current.items() if k!='history'})
        current['paused']=False;current['operation_id']=operation_id
        replace_exact(self.directory,self.path,canonical(current),content_hash(raw))
        return {'state':'resumed','journal_path':self.relative,'new_work_requires_fresh_operations':True,'revoked_operations':current['revoked_operations']}

    def _resume_ready(self, current, payload, *, actor, state, operation_id):
        pool=self.broker.pool;require(pool is not None, 'runtime_unavailable', 'Selected native pool is unavailable.')
        execution=state['orchestration']['execution_id'];generation=state['orchestration']['generation']
        exact(payload,('pause_operation_id',))
        require(current is not None and current['paused'] and current['operation_id']==payload['pause_operation_id']
                and current['actor']==actor and current['execution_id']==execution and current['generation']==generation,
                'resume_owner','Resume must reconcile this exact pause and current execution owner.')
        for name in current['reservations']:
            lease=pool.leases[name]
            if lease.state=='queued':continue
            require(lease.state=='released','owner_uncertain','A requested interruption is not a confirmed native release.')
            values=[pool.handles[h]['value'] for h in lease.observations if pool.handles[h]['value']['kind']=='runtime_release'
                    and pool.handles[h]['value']['actor']==lease.actor]
            require(len(values)==1 and values[0]['facts']['lease_released'],'owner_uncertain','Exact runtime release evidence is required.')
            value=values[0];handle=next(h for h in lease.observations if pool.handles[h]['value']==value)
            pool.resolve(handle,('runtime_release',),reservation=name,actor=value['actor']['thread_id'],epoch=value['actor']['load_epoch'],operation_id=value['operation_id'])
        import re
        names = sorted(p.name for p in self.directory.iterdir())
        require(len(names) <= 5000, 'control_inventory', 'Private owner operation inventory exceeds its bound.')
        for name in names:
            if name.startswith('.') or re.fullmatch(r'[A-Za-z0-9_-]+-owner-[a-f0-9]{64}\.json', name): continue
            require(name.endswith('.json'), 'control_inventory', 'Unclassified private owner state must be reconciled.')
            key = name[:-5]; record=self.broker.grants.inspect(key)
            require(type(record) is dict and {'state','grant','receipt','post_state'} <= record.keys(),
                    'control_inventory', 'Unknown private owner record remains held.')
            require(key==operation_id or record['state']=='consumed','owner_partial','Original owner operations still need exact recovery.')
        pool._work()  # Never reopen a closed/quarantined/expired native pool.
