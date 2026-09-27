"""Typed admission and complete-team bookkeeping, separate from runtime claims."""
from collections import deque
from dataclasses import dataclass, field
import copy
import os
import time
from curator_policy import PolicyError, digest, exact, require
from curator_policy import canonical
from curator_confinement import canonical_root, parent_descriptor

TEAMS = {
    'generic': ('worker',),
    'complex': ('solver_a', 'solver_b', 'senior', 'implementer'),
    'extra-complex': ('solver_a', 'solver_b', 'reviewer_a', 'reviewer_b', 'senior', 'implementer'),
}


@dataclass
class Actor:
    reservation: str
    parent: str
    function: str
    input_sha256: str
    profile_sha256: str
    native_id: str | None = None
    state: str = 'reserved'
    role_reads: dict | None = None
    effective: dict | None = None


class RuntimeCoordinator:
    """Reservations survive uncertainty. This class creates no native actors."""
    def __init__(self, adapter, model, effort, capacity):
        require(type(capacity) is int and capacity > 0, 'capacity', 'Observed positive capacity is required.')
        self.adapter = adapter; self.model = model; self.effort = effort
        self.capacity = capacity; self.actors = {}; self.pending = deque(); self.closed = False

    def reserve_team(self, category, parent, input_sha256, profiles, *, implementation=True):
        require(category in TEAMS and not self.closed, 'category', 'Unknown category or stopped admission.')
        team = tuple(k for k in TEAMS[category] if implementation or k != 'implementer')
        require(set(profiles) == set(team), 'team_profiles', 'Every required logical actor needs its own profile.')
        for function in team:
            key = parent + ':' + function
            require(key not in self.actors, 'reservation_duplicate', 'Existing reservation cannot be replaced.')
            self.actors[key] = Actor(key, parent, function, input_sha256, profiles[function])
            self.pending.append(key)
        return team

    def capacity_ready(self):
        # Readiness, an idle turn, or interruption does not prove the native
        # session released its capacity. Retain every bound session slot.
        active = sum(a.native_id is not None or a.state in ('reserved-launch', 'launch_uncertain') for a in self.actors.values())
        return not self.closed and active < self.capacity and bool(self.pending)

    def next_reservation(self):
        require(self.capacity_ready(), 'capacity', 'Queue retained; no available native slot.')
        key = self.pending.popleft(); self.actors[key].state = 'reserved-launch'; return self.actors[key]

    def record_launch(self, reservation, observation):
        actor = self.actors[reservation]
        require(actor.state in ('reserved-launch', 'launch_uncertain') and actor.native_id is None, 'launch_duplicate', 'Reservation already bound.')
        native_id = self.adapter.validate_launch(observation, actor.parent)
        require(native_id != actor.parent and all(a.native_id != native_id for a in self.actors.values()), 'native_duplicate', 'Native child is not distinct.')
        actor.native_id = native_id; actor.state = 'bootstrap'; return actor

    def ready(self, reservation, role_reads, effective, expected_roles):
        actor = self.actors[reservation]
        require(actor.state == 'bootstrap' and actor.native_id, 'bootstrap', 'Native bootstrap required.')
        require(role_reads == expected_roles, 'role_reads', 'Exact role acknowledgement differs.')
        require(effective.get('model') == self.model and effective.get('reasoningEffort') == self.effort
                and effective.get('profile_sha256') == actor.profile_sha256 and effective.get('observed') is True,
                'effective_settings', 'Actual effective settings/profile are not established.')
        require(effective.get('independent_input_sha256') == actor.input_sha256 and effective.get('channels_isolated') is True,
                'input_isolation', 'Whole-problem input/channel independence is unproven.')
        actor.role_reads = role_reads; actor.effective = effective; actor.state = 'ready'

    def release_work(self, reservation, text):
        actor = self.actors[reservation]
        require(not self.closed and actor.state == 'ready', 'work_held', 'Actor has not passed readiness.')
        result = self.adapter.followup(actor.native_id, text); actor.state = 'working'; return result

    def uncertain(self, reservation):
        actor = self.actors[reservation]
        require(actor.state == 'reserved-launch', 'reservation', 'No launch in progress.')
        actor.state = 'launch_uncertain'

    def stop(self):
        self.closed = True; results = {}
        for key, actor in self.actors.items():
            if actor.native_id and actor.state in ('working', 'bootstrap', 'ready'):
                actor.state = 'stop_requested'
                try:
                    observed = self.adapter.observe(actor.native_id)
                    native_state = observed['thread']['status']['type']
                    if native_state == 'active':
                        results[key] = {'state':'interrupt_requested', 'result':self.adapter.interrupt(actor.native_id)}
                    else:
                        actor.state = 'idle_unreconciled' if native_state == 'idle' else 'stop_uncertain'
                        results[key] = {'state':actor.state, 'observation':observed}
                except (PolicyError, OSError, KeyError) as exc:
                    actor.state = 'stop_uncertain'
                    results[key] = {'state':'stop_uncertain', 'code':getattr(exc,'code','observation_unavailable')}
        return results

    def reconcile(self, reservation, observation):
        actor = self.actors[reservation]
        state = self.adapter.validate_status(observation, actor.native_id)
        if state in ('interrupted', 'failed'):
            actor.state = 'stopped' if state == 'interrupted' else 'failed'
        elif state == 'idle':
            actor.state = 'idle'
        # Idle is not revocation or permission to replace the actor.
        return actor.state


@dataclass
class ForkLease:
    reservation: str
    generation: int
    parent: str | None
    function: str
    profile: str
    reads: dict
    history_cut: dict | None
    state: str = 'queued'
    actor: dict | None = None
    creation: dict | None = None
    adapter: object = None
    epoch: int = 0
    observations: list = field(default_factory=list)
    release_request: dict | None = None
    readiness: dict | None = None
    required_reads: dict = field(default_factory=dict)


class ForkRuntimePool:
    """Protected local leases around real per-actor native adapters.

    The canonical Task owner remains the assignment authority. This ledger
    records runtime intent before I/O and never promotes an idle native turn
    into released process capacity. Constructor callbacks are trusted code.
    """
    def __init__(self, *, native, protocol, registry, adapter_factory, directory,
                 capacity, generation, deadline, owner_reconciler):
        native.protocol(protocol)
        require(protocol['schema_version']==2 and registry.broker_run_id==protocol['broker_run_id'],
                'pool_protocol','The explicit fork protocol and current registry must agree.')
        require(type(capacity) is int and capacity>0 and type(generation) is int and generation>0,
                'pool_capacity','Positive protected capacity and generation are required.')
        require(type(deadline) in (int,float) and deadline>time.monotonic(), 'pool_deadline','A finite future work deadline is required.')
        self.native=native;self.protocol=copy.deepcopy(protocol);self.registry=registry
        self.factory=adapter_factory;self.directory=canonical_root(directory);self.capacity=capacity
        self.generation=generation;self.deadline=deadline;self.owner_reconciler=owner_reconciler
        self.leases={};self.handles={};self.queue=deque();self.closed=False;self.sequence=0
        self.host_releases={};self.controller=None
        self._journal('pool.created',{'protocol':self.protocol,'capacity':capacity,'generation':generation})

    def _journal(self,kind,data):
        self.sequence+=1
        value={'sequence':self.sequence,'kind':kind,'generation':self.generation,'data':data}
        name=str(self.sequence).zfill(8)+'.json'
        try:
            with parent_descriptor(self.directory,name) as (parent,leaf):
                fd=os.open(leaf,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
                with os.fdopen(fd,'wb') as stream:stream.write(canonical(value));stream.flush();os.fsync(stream.fileno())
                os.fsync(parent)
        except Exception:
            self.closed=True
            raise
        return digest(value)

    def _work(self):
        require(not self.closed and time.monotonic()<self.deadline,'pool_held','Pool admission is closed or its work deadline expired.')
        require(not self.registry.quarantine and not any(x.adapter and x.adapter.quarantine for x in self.leases.values()),
                'pool_quarantine','Unexpected native identity holds every new admission.')

    def occupied(self):
        return sum(x.state not in ('queued','released') for x in self.leases.values())

    def _lease(self,reservation):
        require(type(reservation) is str and reservation in self.leases,'reservation','Unknown protected reservation.')
        return self.leases[reservation]

    def _loaded(self,reservation):
        value=self._lease(reservation)
        require(value.actor is not None and value.state in ('bootstrap','ready','working'), 'lease_held','No admitted loaded incarnation.')
        self.registry.require_current(value.actor)
        return value

    def for_actor(self,actor):
        matches=[lease for lease in self.leases.values() if lease.actor and lease.actor['thread_id']==actor]
        require(len(matches)==1,'actor_reservation','Native identity has no unique protected reservation.')
        return matches[0]

    @staticmethod
    def cut_history(history,cut):
        require(history.get('complete') is True and type(history.get('turns')) is list,'history_unproven','Complete source pages are required.')
        matches=[i for i,turn in enumerate(history['turns']) if turn.get('id')==cut['turn_id']]
        require(len(matches)==1 and cut['mode'] in ('lastTurnId','beforeTurnId'),'history_cut','The exact native history boundary is unavailable.')
        end=matches[0]+(1 if cut['mode']=='lastTurnId' else 0)
        turns=history['turns'][:end]
        require(digest(turns)==cut['history_sha256'],'source_history_changed','Native history prefix differs from the accepted whole-problem cut.')
        return turns

    def attach_controller(self,reservation,adapter,profile,reads):
        self._work();require(not self.leases and adapter.actor_binding is not None,'controller_binding','Controller must be the first actual admitted actor.')
        require(adapter.native is self.native and adapter.registry is self.registry and adapter.selected_protocol==self.protocol,
                'pool_protocol','Controller uses another native authority.')
        self.registry.require_current(adapter.actor_binding)
        value=ForkLease(reservation,self.generation,None,'controller',profile,copy.deepcopy(reads),None,
            state='bootstrap',actor=copy.deepcopy(adapter.actor_binding),adapter=adapter,epoch=adapter.load_epoch)
        self._journal('controller.attached',{'reservation':reservation,'actor':value.actor,'profile':profile})
        self.leases[reservation]=value;self.controller=reservation;adapter.after_response=self.acknowledge_callback
        return value

    def reserve(self,assignment,parent,profile,history_cut,reads):
        self._work();aid=assignment['assignment_id'];self.native.identity(aid)
        require(aid not in self.leases and assignment['generation']==self.generation and assignment['native_id'] is None
                and assignment['state']=='reserved','reservation','Only a fresh current canonical reservation can be queued.')
        self._loaded(parent)
        self.native.fields(history_cut,('mode','turn_id','history_sha256','input_sha256'))
        require(type(reads) is dict and reads and type(profile) is str and profile,'reservation','Protected profile and exact bootstrap inputs are required.')
        for key,value in reads.items():require(type(key) is str and key,'role_reads','Missing read path.');self.native.sha(value)
        self._journal('reservation.queued',{'assignment_id':aid,'assignment_sha256':digest(assignment),
            'parent':parent,'profile':profile,'history_cut':history_cut,'reads':reads})
        self.leases[aid]=ForkLease(aid,self.generation,parent,assignment['function'],profile,copy.deepcopy(reads),copy.deepcopy(history_cut))
        context_paths={ref['path'] for ref in assignment.get('context',[])}
        self.leases[aid].required_reads={path:sha256 for path,sha256 in reads.items() if path not in context_paths}
        self.queue.append(aid)
        return aid

    def _remember(self,lease,receipt):
        exact(receipt,('handle','value'));value=receipt['value']
        self.native.validate_observation_v2(value,subject=lease.actor['thread_id'],broker_run_id=self.protocol['broker_run_id'])
        require(value['actor']==lease.actor and value['reservation_id']==lease.reservation,
                'receipt_binding','Observation belongs to another reservation or incarnation.')
        require(receipt['handle'] not in self.handles,'receipt_duplicate','Observation handle already exists.')
        # The adapter also checks actual protected wire membership on creation.
        observed=lease.adapter.load_observation(receipt['handle'],value['kind'],actor=lease.actor['thread_id'])
        require(observed==value,'receipt_binding','Adapter observation body differs.')
        self._journal('observation.recorded',{'handle':receipt['handle'],'value':value})
        self.handles[receipt['handle']]={'value':copy.deepcopy(value),'generation':self.generation}
        lease.observations.append(receipt['handle'])
        return {'handle':receipt['handle'],'kind':value['kind'],'actor':value['actor']['thread_id'],'load_epoch':value['actor']['load_epoch']}

    def resolve(self,handle,kinds,*,reservation,actor,epoch,operation_id):
        require(type(handle) is str and handle in self.handles,'observation_unavailable','Unknown protected observation handle.')
        row=self.handles[handle];value=row['value'];lease=self._lease(reservation)
        require(row['generation']==self.generation and value['kind'] in kinds and value['reservation_id']==reservation
                and value['actor']['thread_id']==actor and value['actor']['load_epoch']==epoch and value['operation_id']==operation_id,
                'observation_scope','Receipt family, actor, source operation, generation or incarnation differs.')
        self.native.validate_observation_v2(value,broker_run_id=self.protocol['broker_run_id'])
        if value['kind']=='runtime_release':
            # A newly resumed canonical manager must still be able to submit
            # the exact old release during its explicit reconnect transaction.
            require(handle in lease.observations and value['facts']['lease_released'],'release_unproven','Local release remains unconfirmed.')
        else:
            require(lease.actor is not None and value['actor']==lease.actor,'observation_stale','Only this reservation\'s current incarnation is eligible.')
            self.registry.require_current(value['actor'])
        return copy.deepcopy(value)

    def launch(self,reservation,operation_id):
        self._work();lease=self._lease(reservation)
        require(lease.state=='queued' and self.occupied()<self.capacity,'pool_capacity','The complete reservation queue is retained until local capacity is available.')
        parent=self._loaded(lease.parent)
        settings=parent.adapter.configured_settings()
        history=self.cut_history(parent.adapter.full_history(),lease.history_cut)
        lease.state='creating';lease.epoch+=1
        self._journal('creation.pending',{'reservation':reservation,'operation_id':operation_id,'epoch':lease.epoch,
            'settings':settings,'history_cut':lease.history_cut,'source':parent.actor})
        try:
            adapter=self.factory(reservation,lease.epoch,lease.profile);lease.adapter=adapter
            require(adapter.native is self.native and adapter.registry is self.registry and adapter.selected_protocol==self.protocol,
                    'pool_protocol','Factory returned another protocol/context registry.')
            adapter.after_response=self.acknowledge_callback;adapter.start();adapter.verify_prelaunch(settings['model'],settings['reasoning_effort'],settings['provider'])
            result=adapter.fork_reserved(parent_settings=settings,source_thread_id=parent.actor['thread_id'],
                history_cut=lease.history_cut,profile=lease.profile,logical_parent_id=parent.actor['thread_id'],operation_id=operation_id,reservation_id=reservation)
            lease.actor=copy.deepcopy(adapter.actor_binding)
            require(all(other is lease or other.actor is None or other.actor['thread_id']!=lease.actor['thread_id'] for other in self.leases.values()),
                    'native_duplicate','A different reservation already owns this permanent native ID.')
            inherited=adapter.full_history()
            require(inherited['complete'] and inherited['turns']==history, 'fork_history_mismatch','Complete inherited history differs; bootstrap remains held.')
            lease.creation=copy.deepcopy(result['observation']['value']);lease.state='bootstrap';self.queue.remove(reservation)
            return self._remember(lease,result['observation'])
        except Exception:
            lease.state='uncertain';self.closed=True
            self._journal('creation.uncertain',{'reservation':reservation,'operation_id':operation_id,'actor':lease.actor})
            raise

    def role_acknowledgement(self,context,reservation,operation_id,reads):
        lease=self._loaded(reservation)
        require(context.actor==lease.actor and reads==lease.reads,'role_reads','The actual actor must acknowledge its exact protected role, charter and input bytes.')
        observed=self._remember(lease,lease.adapter.role_receipt(context,operation_id,reservation,reads))
        lease.readiness=observed;lease.state='ready';return observed

    def bind_owner_inputs(self,assignment,charter):
        lease=self._loaded(assignment['assignment_id'])
        require(assignment['generation']==self.generation and assignment['native_id']==lease.actor['thread_id'],
                'input_owner','Input binding must come from the current canonical assignment.')
        reads=copy.deepcopy(lease.required_reads)
        reads.update({ref['path']:ref['sha256'] for ref in assignment['context']})
        reads.update({assignment['role']['agents_path']:assignment['role']['agents_sha256'],
            assignment['role']['role_path']:assignment['role']['role_sha256'],charter['path']:charter['sha256']})
        self._journal('inputs.rebound',{'reservation':lease.reservation,'actor':lease.actor,'reads':reads,'assignment_sha256':digest(assignment)})
        lease.reads=reads;lease.readiness=None;lease.state='bootstrap'

    def observe(self,reservation,operation_id,selection=None):
        lease=self._lease(reservation)
        if selection is not None:
            exact(selection,('kind','source_operation','epoch'))
            require(type(selection['kind']) is str and selection['kind'] in self.native.RECEIPT_KINDS,
                    'observation_kind','Unknown typed observation family.')
            matches=[(handle,self.handles[handle]['value']) for handle in lease.observations
                if self.handles[handle]['value']['kind']==selection['kind'] and self.handles[handle]['value']['operation_id']==selection['source_operation']
                and self.handles[handle]['value']['actor']['load_epoch']==selection['epoch']]
            require(len(matches)==1,'observation_unavailable','No unique completed observation matches the protected selection.')
            handle,value=matches[0]
            self.resolve(handle,(selection['kind'],),reservation=reservation,actor=value['actor']['thread_id'],
                epoch=selection['epoch'],operation_id=selection['source_operation'])
            return {'handle':handle,'kind':value['kind'],'actor':value['actor']['thread_id'],'load_epoch':value['actor']['load_epoch']}
        if lease.state=='released':
            values=[(handle,self.handles[handle]['value']) for handle in lease.observations
                if self.handles[handle]['value']['kind']=='runtime_release' and self.handles[handle]['value']['actor']==lease.actor]
            require(len(values)==1,'release_unproven','No exact completed release descriptor is available.')
            handle,value=values[0]
            return {'handle':handle,'kind':'runtime_release','actor':lease.actor['thread_id'],'load_epoch':lease.actor['load_epoch']}
        lease=self._loaded(reservation)
        return self._remember(lease,lease.adapter.status_receipt(operation_id,reservation))

    def deliver(self,reservation,operation_id,text,artifacts,*,conflict=None,steer=False):
        self._work();lease=self._loaded(reservation)
        require(lease.readiness is not None,'work_held','Work requires an acknowledged current input set.')
        result=self._remember(lease,lease.adapter.delivery_receipt(text,operation_id,reservation,artifacts,conflict=conflict,steer=steer))
        lease.state='working';return result

    def interrupt(self,reservation,operation_id):
        lease=self._loaded(reservation)
        return self._remember(lease,lease.adapter.interrupt_receipt(operation_id,reservation))

    def request_release(self,context,reservation,operation_id):
        lease=self._loaded(reservation)
        require(reservation!=self.controller,'controller_release_denied','Ordinary manager tools cannot release the controller.')
        self.native.require_current(self.protocol,context.thread_id,context.binding())
        require(lease.release_request is None,'release_pending','Release is already pending; do not retry its callback.')
        request={'operation_id':operation_id,'call':context.binding(),'acknowledged':False,'host':False}
        self._journal('release.pending',{'reservation':reservation,**request})
        lease.release_request=request;lease.state='release_pending';lease.adapter.close_actor_admission()
        return {'state':'release_pending','reservation':reservation,'operation_id':operation_id}

    def authorize_controller_release(self,operation_id,*,actor,generation,handoff_sha256):
        """Trusted host lifecycle entry point; deliberately absent from tool aliases."""
        self.native.sha(handoff_sha256);lease=self._loaded(self.controller)
        require(actor==lease.actor and generation==self.generation and operation_id not in self.host_releases,
                'host_lifecycle_scope','Host release must bind the current controller incarnation and handoff.')
        self.host_releases[operation_id]={'actor':copy.deepcopy(actor),'handoff_sha256':handoff_sha256}
        self._journal('host.release.authorized',{'operation_id':operation_id,**self.host_releases[operation_id]})

    def release_controller(self,operation_id):
        lease=self._loaded(self.controller);selected=self.host_releases.pop(operation_id,None)
        require(selected is not None and selected['actor']==lease.actor,'host_lifecycle_scope','No unused exact host controller-release operation.')
        lease.release_request={'operation_id':operation_id,'call':None,'acknowledged':True,'host':True}
        self._journal('release.pending',{'reservation':lease.reservation,**lease.release_request})
        lease.state='release_pending';lease.adapter.close_actor_admission()

    def acknowledge_callback(self,context):
        # The adapter invokes this only after the actual response bytes are sent.
        for lease in self.leases.values():
            request=lease.release_request
            if request and not request['host'] and request['call']==context.binding():
                self._journal('release.callback_acknowledged',{'reservation':lease.reservation,'call':context.binding()})
                request['acknowledged']=True

    def drain_releases(self,deadline):
        """Called outside native callbacks; stop every requested lease despite failures."""
        results={}
        for lease in self.leases.values():
            if lease.state!='release_pending' or not lease.release_request['acknowledged']:continue
            operation_id=lease.release_request['operation_id'];owner=None;cleanup=None;error=None
            interruption=None
            turn=getattr(lease.adapter,'turns',{}).get(lease.actor['thread_id'])
            if turn is not None and turn.get('status')=='inProgress':
                try:
                    lease.adapter.begin_stop(deadline);lease.adapter.interrupt(lease.actor['thread_id'])
                    interruption={'turn_id':turn['id'],'state':'acknowledged'}
                except Exception as exc:
                    interruption={'turn_id':turn['id'],'state':'uncertain','code':getattr(exc,'code',type(exc).__name__)}
            try:
                require(time.monotonic()<deadline,'stop_deadline','No shared cleanup time remains.')
                owner=self.owner_reconciler(copy.deepcopy(lease.actor),deadline)
                exact(owner,('state','actor','inputs','journals'))
                require(owner['state']=='reconciled' and owner['actor']==lease.actor,'owner_unreconciled','Write-owning operations remain uncertain.')
                for ref in [*owner['inputs'],*owner['journals']]:
                    exact(ref,('path','sha256'));self.native.sha(ref['sha256'])
            except Exception as exc:error=getattr(exc,'code',type(exc).__name__)
            try:
                lease.adapter.begin_stop(deadline);cleanup=lease.adapter.close(deadline)
            except Exception as exc:error=error or getattr(exc,'code',type(exc).__name__)
            runtime=type(cleanup) is dict and cleanup.get('state')=='owned_process_group_stopped'
            companion=type(cleanup) is dict and cleanup.get('companion',{}).get('state')=='owned_companion_stopped'
            released=error is None and runtime and companion and time.monotonic()<=deadline
            lease.state='released' if released else 'uncertain'
            if not released:self.closed=True
            evidence={'owner':owner,'cleanup':cleanup,'error':error,'interruption':interruption}
            self._journal('release.observed',{'reservation':lease.reservation,'actor':lease.actor,'released':released,**evidence})
            if released:
                terminal=[r for r in lease.adapter.wire_records if r['direction']=='received' and r['frame'].get('method')=='turn/completed'
                    and r['frame'].get('params',{}).get('threadId')==lease.actor['thread_id']]
                frames=terminal[-1:] or lease.creation['frames'][-2:] if lease.creation else terminal[-1:]
                outcome=terminal[-1]['frame']['params']['turn']['status'] if terminal else 'unknown'
                if outcome not in ('completed','interrupted','failed'):outcome='unknown'
                receipt=lease.adapter.typed_receipt('runtime_release',operation_id,lease.reservation,frames,
                    {'admission_closed':True,'owner_reconciled':True,'local_runtime_absent':True,'local_companion_absent':True,
                     'lease_released':True,'provider_outcome':outcome,'cleanup_sha256':digest(cleanup)})
                results[lease.reservation]=self._remember(lease,receipt)
            else:results[lease.reservation]={'state':'uncertain','error':error,'runtime_absent':runtime,'companion_absent':companion}
        return results

    def resume(self,reservation,operation_id):
        self._work();lease=self._lease(reservation)
        require(lease.state=='released' and lease.creation is not None and self.occupied()<self.capacity,
                'resume_held','Same-ID resume requires confirmed old release and available local capacity.')
        stored=lease.creation['facts'];settings={k:stored['settings'][k] for k in ('model','reasoning_effort','provider')}
        previous=copy.deepcopy(lease.actor);lease.state='creating';lease.epoch+=1;lease.readiness=None
        self._journal('resume.pending',{'reservation':reservation,'operation_id':operation_id,'prior_actor':previous,'epoch':lease.epoch})
        try:
            adapter=self.factory(reservation,lease.epoch,lease.profile);lease.adapter=adapter
            require(adapter.native is self.native and adapter.registry is self.registry and adapter.selected_protocol==self.protocol,
                    'pool_protocol','Resume factory returned another native authority.')
            adapter.after_response=self.acknowledge_callback;adapter.start();adapter.verify_prelaunch(settings['model'],settings['reasoning_effort'],settings['provider'])
            result=adapter.resume_owned(stored_actor={'thread_id':previous['thread_id'],**{k:stored[k] for k in ('source_thread_id','logical_parent_id','history_cut')}},
                settings=settings,profile=lease.profile,operation_id=operation_id,reservation_id=reservation)
            lease.actor=copy.deepcopy(adapter.actor_binding)
            require(lease.actor['thread_id']==previous['thread_id'] and lease.actor['connection_id']!=previous['connection_id']
                    and lease.actor['load_epoch']>previous['load_epoch'],'resume_binding','Resume did not produce a fresh load of the exact permanent ID.')
            lease.state='bootstrap';lease.release_request=None
            return self._remember(lease,result['observation'])
        except Exception:
            lease.state='uncertain';self.closed=True;self._journal('resume.uncertain',{'reservation':reservation,'prior_actor':previous})
            raise
