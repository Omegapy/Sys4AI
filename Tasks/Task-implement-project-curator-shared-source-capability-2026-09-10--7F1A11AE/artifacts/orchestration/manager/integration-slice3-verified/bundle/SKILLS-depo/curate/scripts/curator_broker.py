"""Closed, authenticated dispatch to existing Task, memory and ontology owners."""
import base64
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import stat
from pathlib import Path
import threading

from curator_policy import PolicyError, canonical, digest, evaluate_operation, exact, inspect_policy, load_policy, require
from curator_classification import classify_target
from curator_confinement import VerificationAdmission, file_snapshot, parent_descriptor, proof_gate, verify_manifest
from curator_grants import GrantStore, validate_owner_state

TOOLS = frozenset(('policy.inspect', 'target.classify', 'artifact.submit', 'artifact.read',
    'task.create', 'task.event', 'task.response', 'memory.publish', 'memory.recover',
    'ontology.publish', 'ontology.recover', 'runtime.observe', 'runtime.message',
    'runtime.followup', 'runtime.interrupt', 'runtime.resume', 'runtime.delegate',
    'runtime.release', 'runtime.reconcile', 'role.acknowledge'))

# This source-bound map is never read from model arguments or project policy.
WIRE_TO_TOOL = {name.replace('.', '_'):name for name in TOOLS}

# Each exact owner field has its own native observation family. These aliases
# are executable source, never candidate-selected event/receipt conversions.
TASK_RECEIPTS = {
    'manager.reserve':{'bootstrap_receipt':('status',)},
    'manager.receipt':{'receipt':('creation',)},'assignment.receipt':{'receipt':('creation',)},
    'manager.activate':{'role_reads':('role_acknowledgement',)},'assignment.reads':{'role_reads':('role_acknowledgement',)},
    'assignment.inputs':{'receipt':('input_delivery',)},'conflict.deliver':{'receipt':('conflict_delivery',)},
    'assignment.observe':{'receipt':('status','interrupt','runtime_release')},
    'assignment.resume':{'receipt':('resume',)},
    'manager.reconnect':{'receipt':('status','resume'),'release_receipt':('runtime_release',),'role_reads':('role_acknowledgement',)},
    'manager.replace':{'observations':('reconciliation',)},
}


def native_tool_specs():
    result=[]
    for wire,logical in sorted(WIRE_TO_TOOL.items()):
        fields=({'reads':{'type':'object','additionalProperties':{'type':'string'}}} if logical=='role.acknowledge' else
            {} if logical=='policy.inspect' else ({'handle':{'type':'string'}} if logical=='artifact.read' else
            {'handle':{'type':'string'},'sha256':{'type':'string'},'content':{'type':'string'}} if logical=='artifact.submit' else
            {'operation_id':{'type':'string'},'payload_sha256':{'type':'string'},'payload':{'type':'object'}}))
        result.append({'type':'function','name':wire,'description':'Bounded Curator operation: '+logical,
            'inputSchema':{'type':'object','additionalProperties':False,'required':list(fields),'properties':fields}})
    return result


class Owners:
    """Modules are loaded from the complete protected manifest during trusted startup."""
    def __init__(self, root, task, memory, memory_recovery, ontology):
        self.root = Path(root).resolve(strict=True)
        self.task = task; self.memory = memory; self.memory_recovery = memory_recovery; self.ontology = ontology

    def dispatch(self, operation, payload, grant, grant_path, task_binding, actor):
        if operation == 'task.create':
            return self.task.command_new(self.root, self.root / 'Tasks', payload)
        if operation in ('task.event','task.response'):
            return self.task.response_transaction('orchestrate' if operation == 'task.event' else 'record-response',
                self.root, self.root / 'Tasks', task_binding['task_id'], task_binding['revision'], payload)
        if operation == 'memory.publish':
            return self.memory.publish(self.root, payload, grant_path, actor)
        if operation == 'memory.recover':
            return self.memory_recovery.recover(self.root, payload['journal_path'], grant_path, actor)
        if operation == 'ontology.publish':
            return self.ontology.publish(self.root, payload, grant, expected_preview_sha256=grant['preview_sha256'])
        if operation == 'ontology.recover':
            return self.ontology.recover(self.root, payload['operation_id'], grant)
        raise PolicyError('owner_route', 'Unsupported canonical owner route.')

    @staticmethod
    def outcome(operation, result):
        """A returned object is not evidence that its owning operation completed."""
        if not isinstance(result,dict): return 'unrecognized'
        state=result.get('state',result.get('status'))
        if result.get('recovery_required') is True or state in ('partial','blocked','recovery_required','created_with_warnings'):
            return 'partial'
        if state in ('error','failed','invalid','integrity_error'): return 'failed'
        if state in ('unavailable','unsupported'): return 'unavailable'
        if state in ('unchanged','skipped'): return 'unchanged'
        if operation.startswith('task.'):
            expected='created' if operation=='task.create' else 'recorded'
            return 'completed' if (result.get('status')==expected and result.get('mutated') is True
                and result.get('errors')==[] and result.get('recovery_required') is False) else 'unrecognized'
        if operation.startswith('memory.'):
            records=result.get('records')
            return 'completed' if (result.get('state')=='complete' and isinstance(records,list) and records
                and all(isinstance(item,dict) and item.get('state')=='committed' for item in records)
                and isinstance(result.get('journal_path'),str)) else 'unrecognized'
        if operation.startswith('ontology.'):
            files=result.get('files')
            return 'completed' if (result.get('status')=='complete' and isinstance(files,list) and files
                and all(isinstance(item,dict) and item.get('state')=='committed' for item in files)
                and isinstance(result.get('intent_sha256'),str)) else 'unrecognized'
        # Runtime response schemas are checked by the correlated native adapter.
        if operation=='runtime.observe': return 'observed' if isinstance(result.get('thread'),dict) else 'unrecognized'
        if operation=='runtime.interrupt': return 'requested' if result=={} else 'unrecognized'
        if operation=='runtime.message': return 'requested' if isinstance(result.get('turnId'),str) else 'unrecognized'
        if operation in ('runtime.followup','runtime.resume'):
            turn=result.get('turn')
            return 'requested' if isinstance(turn,dict) and turn.get('status')=='inProgress' else 'unrecognized'
        return 'unrecognized'


class Broker:
    """All constructor data is trusted deployment state, never native tool arguments."""
    def __init__(self, *, owners, adapter, policy_path, ownership_map, manifest, profile,
                 runtime_binding, enforcement_proof, private_directory, issuer, accepted_operations,
                 artifacts=None, verification_admission=None, runtime_pool=None):
        self.owners = owners; self.adapter = adapter; self.policy_path = Path(policy_path)
        self.ownership_map = copy.deepcopy(ownership_map); self.manifest = copy.deepcopy(manifest)
        self.profile = copy.deepcopy(profile); self.runtime_binding = copy.deepcopy(runtime_binding)
        self.enforcement_proof = copy.deepcopy(enforcement_proof)
        self.grants = GrantStore(private_directory, issuer)
        self.accepted = copy.deepcopy(accepted_operations); self.artifacts = copy.deepcopy(artifacts or {})
        self._lock = threading.RLock()
        require(verification_admission is None or type(verification_admission) is VerificationAdmission, 'verification_admission', 'Only trusted bootstrap may supply proof admission.')
        self.verification_admission = verification_admission
        self.native = owners.task.orch.native
        self.pool=runtime_pool
        if self.pool is not None:
            require(self.pool.native is self.native,'owner_context','Pool and every installed owner must share the exact native context.')
        require(adapter.native is self.native, 'owner_context', 'Transport and installed owner must share the exact native context.')
        listed = {str(Path(manifest['root']) / e['path']) for e in manifest['files']}
        for module in (owners.task, owners.memory, owners.memory_recovery, owners.ontology):
            require(str(Path(module.__file__).resolve()) in listed, 'owner_unpinned', 'Owner executable is absent from frozen import closure.')

    def _verify_owner_closure(self):
        verify_manifest(self.manifest)
        listed = {str(Path(self.manifest['root']) / e['path']) for e in self.manifest['files']}
        directories = {Path(module.__file__).resolve().parent for module in
                       (self.owners.task, self.owners.memory, self.owners.memory_recovery, self.owners.ontology)}
        installed = self.owners.root / '.agents/skills'
        required = {str(p.resolve()) for directory in directories for p in directory.glob('*.py')}
        if installed.exists(): required.update(str(p.resolve()) for p in installed.rglob('*.py'))
        require(required <= listed, 'owner_closure_changed', 'A trusted owner or dynamically installed helper is absent from the complete frozen import closure.')

    def _task(self, accepted, actor):
        binding = accepted['task']
        if binding is None:
            require(accepted['tool'] == 'task.create' and accepted['bootstrap_actor'] == actor, 'writer', 'Only selected bootstrap may create the Task.')
            return None
        root = self.owners.root
        require(file_snapshot(root, binding['path'], 2000000)['sha256'] == binding['sha256'], 'task_changed', 'Canonical Task changed after operation selection.')
        state, errors, _ = self.owners.task.validate_task_folder((root / binding['path']).parent)
        require(not errors and state['task_id'] == binding['task_id'] and state['revision'] == binding['revision'], 'task_changed', 'Owner Task validation or revision differs.')
        orch = state['orchestration']
        require(orch['version'] == 2 and orch['execution_id'] == binding['execution_id']
                and orch['generation'] == binding['generation'] and orch['writer'] == actor,
                'writer', 'Caller is not the current canonical writer.')
        if accepted['tool'].startswith(('memory.','ontology.')):
            assignment = orch['assignments'][orch['manager_id']]
            require(orch['stage'] == 'active' and assignment['native_id'] == actor and assignment['function'] == 'manager'
                    and assignment['role_reads'] and assignment['state'] == 'active', 'manager', 'Knowledge publication requires the current activated manager.')
        return state

    def _post_state(self, paths):
        result={}
        for path in paths:
            with parent_descriptor(self.owners.root,path) as (parent,name):
                try:os.stat(name,dir_fd=parent,follow_symlinks=False)
                except FileNotFoundError:result[path]=None;continue
            result[path]=file_snapshot(self.owners.root,path,2000000)['sha256']
        return result

    def _owner_post_paths(self, tool, result, accepted):
        paths=set(accepted['post_paths'])
        if accepted['task'] is not None:paths.add(accepted['task']['path'])
        def add(value, absolute=False):
            require(type(value) is str,'owner_receipt','Owning helper omitted a canonical result path.')
            path=Path(value)
            if absolute:
                try:path=path.relative_to(self.owners.root)
                except ValueError as exc:raise PolicyError('owner_receipt','Owning result escapes its canonical project.') from exc
            paths.add(path.as_posix())
        if tool=='task.create':
            add(str(Path(result['task_folder'])/'task.json'),True)
        elif tool in ('task.event','task.response'):
            add(accepted['task']['path']);add(result['response_path'],True)
        elif tool.startswith('memory.'):
            for record in result['records']:add(record['path'])
            add(result['journal_path'])
        elif tool.startswith('ontology.'):
            for record in result['files']:add(record['path'])
            add('control_records/ontology/receipts/'+result['operation_id']+'.json')
        return sorted(paths)

    def _verify_owner_state(self, value):
        validate_owner_state(value)
        for ref in [*value['inputs'],*([value['journal']] if value['journal'] is not None else [])]:
            with parent_descriptor(self.owners.root,ref['path']) as (parent,name):
                try:os.stat(name,dir_fd=parent,follow_symlinks=False)
                except FileNotFoundError:
                    require(ref['sha256'] is None,'owner_state_changed','An expected owner input is absent.')
                    continue
            require(ref['sha256'] is not None and file_snapshot(self.owners.root,ref['path'],2000000)['sha256']==ref['sha256'],
                    'owner_state_changed','Current owner input or journal differs from the accepted operation.')

    def _artifact(self, context, request, tool):
        exact(request, ('handle','sha256','content') if tool == 'artifact.submit' else ('handle',))
        require(type(request['handle']) is str and request['handle'] in self.artifacts, 'artifact_unknown', 'Unknown assigned opaque artifact.')
        selected = self.artifacts[request['handle']]
        if tool == 'artifact.read':
            require(context.thread_id in selected['readers'], 'artifact_forbidden', 'Artifact is not in this assignment released input set.')
            info = file_snapshot(selected['root'], selected['path'], selected['max_bytes'])
            require(info['sha256'] == selected['sha256'], 'artifact_changed', 'Released input bytes changed.')
            with parent_descriptor(selected['root'], selected['path']) as (parent, name):
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                with os.fdopen(fd,'rb') as stream:
                    info = os.fstat(stream.fileno())
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'artifact_type', 'Artifact became a special or linked file.')
                    content = stream.read(selected['max_bytes'] + 1)
            require(hashlib.sha256(content).hexdigest() == selected['sha256'], 'artifact_changed', 'Artifact changed during transfer.')
            return {'handle':request['handle'],'sha256':selected['sha256'],'content':base64.b64encode(content).decode()}
        require(context.thread_id == selected['producer'] and selected['sha256'] is None, 'artifact_forbidden', 'Actor does not own this immutable output slot.')
        require(type(request['content']) is str and len(request['content']) <= 2 * selected['max_bytes'], 'artifact_size', 'Artifact exceeds byte limit.')
        try: content = base64.b64decode(request['content'], validate=True)
        except ValueError as exc: raise PolicyError('artifact_encoding', 'Artifact must be base64 bytes.') from exc
        require(len(content) <= selected['max_bytes'] and hashlib.sha256(content).hexdigest() == request['sha256'], 'artifact_digest', 'Artifact size/digest differs.')
        with parent_descriptor(selected['root'], selected['path']) as (parent, name):
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            with os.fdopen(fd,'wb') as stream: stream.write(content); stream.flush(); os.fsync(stream.fileno())
            os.fsync(parent)
        selected['sha256'] = request['sha256']
        return {'handle':request['handle'],'sha256':selected['sha256'],'bytes':len(content)}

    def _owner_grant(self, accepted, context, state, payload):
        owner = accepted['owner']; now = datetime.now(timezone.utc)
        binding = state['orchestration']
        supplied = copy.deepcopy(accepted['owner_grant'])
        if binding['native_protocol']['schema_version']==2:
            require(self.pool is not None and 'native_receipt' not in supplied,'native_arguments','Version2 owner grants require a protected status handle.')
            selected=accepted['owner_native_binding'];exact(selected,('handle','reservation','actor','epoch','operation_id'))
            supplied['native_receipt']=self.pool.resolve(selected['handle'],('status',),
                **{key:selected[key] for key in ('reservation','actor','epoch','operation_id')})
        expected_version = 2 if owner == 'memory' else 3
        require(supplied['schema_version'] == expected_version and supplied['actor_kind'] == 'manager',
                'owner_grant', 'Current independent owner grant version required.')
        supplied.update(actor_id=context.thread_id, controller_origin='curator',
            observed_at=now.isoformat(), expires_at=(now + timedelta(seconds=300)).isoformat(),
            broker_binding={'owner':owner,'call':context.binding(),'protocol':binding['native_protocol'],
                'charter':binding['controller_origin']['charter'],'policy':binding['controller_origin']['policy']})
        supplied['task'] = {k:accepted['task'][k] for k in ('path','sha256','task_id','execution_id','generation','assignment_id')}
        # The accepted owner envelope independently binds exact scope, reviewed records,
        # configuration, lifecycle and preview. Existing owners recheck all of them.
        relative = accepted['owner_grant_path']
        require(relative.startswith('control_records/curator/private-grants/'), 'owner_grant_path', 'Private owner grants require selected protected storage.')
        with parent_descriptor(self.owners.root, relative) as (parent, name):
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            with os.fdopen(fd,'wb') as stream: stream.write(canonical(supplied)); stream.flush(); os.fsync(stream.fileno())
            os.fsync(parent)
        return supplied, relative

    def _task_receipts(self,kind,data,accepted):
        require(type(kind) is str and type(data) is dict,'native_arguments','Expected a typed owner event.')
        fields=TASK_RECEIPTS.get(kind,{})
        bindings=accepted.get('receipt_bindings',{})
        require(type(bindings) is dict and set(bindings)==set(fields),'native_arguments','Protected receipt bindings must match the closed owner field map.')
        require(not any(key.endswith('_sequence') for key in data),'native_arguments','Native sequence numbers are not candidate authority.')
        for key,kinds in fields.items():
            ref=key+'_handle'
            require(key not in data and ref in data,'native_arguments','Candidate must supply the selected opaque handle, never a native observation body.')
            selected=bindings[key];handle=data.pop(ref)
            if selected is None:
                require(kind=='manager.reconnect' and key in ('role_reads','release_receipt') and handle is None,
                        'native_arguments','Only explicit status reconnection permits absent optional receipts.')
                data[key]=None;continue
            exact(selected,('reservation','actor','epoch','operation_id'))
            data[key]=self.pool.resolve(handle,kinds,**selected)

    def _runtime(self,tool,context,payload,accepted,state,operation_id):
        if tool=='runtime.reconcile':
            exact(payload,('receipts',));require(type(payload['receipts']) is dict,'reconciliation','Expected exact assignment handles.')
            selections=accepted['runtime_receipts']
            require(set(payload['receipts'])==set(selections),'reconciliation','Reconciliation must cover the exact selected assignments.')
            assignments=[]
            for aid,selected in selections.items():
                exact(selected,('reservation','actor','epoch','operation_id'))
                require(aid==selected['reservation'] and aid in state['orchestration']['assignments'],
                        'reconciliation','Receipt does not name a canonical assignment.')
                value=self.pool.resolve(payload['receipts'][aid],('runtime_release',),**selected)
                assignments.append({'assignment_id':aid,'observation':value})
            lease=self.pool.for_actor(context.thread_id)
            frames=[row for row in lease.adapter.wire_records if row['direction']=='received' and row['sequence']==context.sequence]
            owner_state=accepted['owner_state']['inputs']
            require(all(ref['sha256'] is not None for ref in owner_state),'reconciliation','Reconciliation requires observed owner file digests.')
            receipt=lease.adapter.typed_receipt('reconciliation',operation_id,lease.reservation,frames,
                {'assignments':assignments,'owner_state':owner_state})
            return self.pool._remember(lease,receipt)
        delivery=tool in ('runtime.message','runtime.followup')
        exact(payload,('reservation','text') if delivery else ('reservation',))
        reservation=payload['reservation']
        require(type(reservation) is str and reservation in accepted['runtime_reservations'],
                'runtime_scope','Reservation is outside the exact accepted lifecycle scope.')
        assignment=state['orchestration']['assignments'].get(reservation)
        if tool=='runtime.delegate':
            require(assignment is not None and assignment['generation']==state['orchestration']['generation'],
                    'runtime_scope','Delegation requires its current canonical reservation.')
            selected=accepted['runtime_selection'];exact(selected,('parent','profile','history_cut','reads'))
            if reservation not in self.pool.leases:self.pool.reserve(assignment,**selected)
            return self.pool.launch(reservation,operation_id)
        lease=self.pool._lease(reservation)
        require(assignment is not None or reservation==self.pool.controller,'runtime_scope','No current canonical assignment or selected controller.')
        if assignment is not None:
            require(assignment['generation']==self.pool.generation and assignment['native_id']==lease.actor['thread_id'],
                    'runtime_scope','Canonical native identity or assignment generation differs.')
        if tool=='runtime.observe':return self.pool.observe(reservation,operation_id)
        if tool=='runtime.interrupt':return self.pool.interrupt(reservation,operation_id)
        if tool=='runtime.release':return self.pool.request_release(context,reservation,operation_id)
        if tool=='runtime.resume':return self.pool.resume(reservation,operation_id)
        require(delivery,'runtime_route','Unsupported protected runtime route.')
        selected=accepted['runtime_delivery'];exact(selected,('artifact_sha256s','conflict'))
        return self.pool.deliver(reservation,operation_id,payload['text'],selected['artifact_sha256s'],
            conflict=selected['conflict'],steer=tool=='runtime.message')

    def reconcile_actor_operations(self,actor,deadline):
        """Read actual selected owner records before a local lease can be released."""
        import time
        from curator_grants import validate_bindings
        require(self.pool is not None and self.pool.for_actor(actor['thread_id']).actor==actor,
                'owner_epoch','Reconciliation must name the exact current local incarnation.')
        inputs={};journals={};records=[];owned=[]
        with self._lock:
            for operation_id,accepted in self.accepted.items():
                require(time.monotonic()<deadline,'stop_deadline','Owner reconciliation exceeded the shared stop bound.')
                record=self.grants.inspect(operation_id)
                if record is None:continue
                grant=record.get('recovery_grant',record['grant']);validate_bindings(grant);call=grant['call']
                require(call.get('schema_version')==2 and call['broker_run_id']==self.pool.protocol['broker_run_id']
                        and grant['issuer']==self.grants.issuer and grant['actor']==accepted['actor'],
                        'owner_chain_binding','Owner lineage contains an unselected native call or issuer.')
                mine=call['actor']==actor
                if mine:require(record['state']=='consumed','owner_unreconciled','An actual owner grant remains issued, dispatching or partial.')
                if record['state']!='consumed':continue
                post=record['post_state']
                require(type(post) is dict,'owner_chain_binding','Consumed owner post-state is missing.')
                name=operation_id+'-owner-'+grant['nonce']+'.json'
                info=file_snapshot(self.grants.directory,name,2000000)
                with parent_descriptor(self.grants.directory,name) as (parent,leaf):
                    fd=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
                    with os.fdopen(fd,'rb') as source:
                        current=os.fstat(source.fileno())
                        require(stat.S_ISREG(current.st_mode) and current.st_nlink==1,'owner_result_type','Owner result became a special or linked file.')
                        raw=source.read(2000001)
                require(len(raw)<=2000000 and hashlib.sha256(raw).hexdigest()==info['sha256'],'owner_result_changed','Stored owner result changed during reconciliation.')
                result=json.loads(raw)
                require(digest(result)==record['receipt']['result_sha256'],'owner_result_changed','Consumed receipt does not bind its actual owner result.')
                before={ref['path']:ref['sha256'] for ref in grant['owner_state']['inputs']}
                task=grant['task'];revision=None
                if task is not None:
                    require(task['generation']==self.pool.generation,'owner_chain_generation','Owner effect belongs to another generation.')
                    before[task['path']]=task['sha256']
                    if grant['operation'] in ('task.event','task.response'):
                        require(result.get('task_id')==task['task_id'] and result.get('revision_before')==task['revision']
                                and result.get('revision_after')==task['revision']+1,
                                'owner_revision_chain','Actual Task owner revision receipt differs from the accepted predecessor.')
                        revision=result['revision_after']
                row={'operation':operation_id,'before':before,'post':post,'task':task,'revision':revision}
                records.append(row)
                if mine:owned.append(row)
                journal=grant['owner_state']['journal']
                if mine and journal is not None:journals[journal['path']]=journal['sha256']
            # Follow only authenticated before/after edges. Collection order and
            # timestamps cannot make a historical post-state current.
            for original in owned:
                for path,start in original['post'].items():
                    value=start;used={original['operation']};revision=original['revision'] if original['task'] and original['task']['path']==path else None
                    while True:
                        require(time.monotonic()<deadline,'stop_deadline','Owner lineage scan exceeded the shared stop bound.')
                        successors=[row for row in records if row['operation'] not in used and path in row['before'] and row['before'][path]==value
                            and path in row['post'] and row['post'][path]!=value]
                        require(len(successors)<=1,'owner_chain_ambiguous','Multiple owner operations claim the same predecessor state.')
                        if not successors:break
                        following=successors[0]
                        if revision is not None:
                            require(following['task'] is not None and following['task']['path']==path and following['task']['revision']==revision,
                                    'owner_revision_chain','Task revision lineage has a missing or foreign link.')
                        revision=following['revision'];used.add(following['operation']);value=following['post'][path]
                    require(path not in inputs or inputs[path]==value,'owner_chain_ambiguous','Historical effects do not resolve to one terminal owner state.')
                    inputs[path]=value
            require(inputs==self._post_state(inputs),'owner_state_changed','A missing operation link or unexplained later edit prevents owner reconciliation.')
            for path,expected in journals.items():
                current=inputs.get(path,expected)
                require(file_snapshot(self.owners.root,path,2000000)['sha256']==current,'owner_journal_changed','Owner journal is not accounted for by the operation chain.')
                journals[path]=current
        return {'state':'reconciled','actor':copy.deepcopy(actor),
            'inputs':[{'path':path,'sha256':value} for path,value in sorted(inputs.items()) if value is not None],
            'journals':[{'path':path,'sha256':value} for path,value in sorted(journals.items())]}

    def dispatch_verified(self, context, request):
        if self.pool is not None:
            self.native.require_current(self.pool.protocol,context.thread_id,context.binding())
        else:self.native.require_live(context.binding(), context.thread_id, session=self.adapter.authority.session_id, tool=context.tool)
        tool = WIRE_TO_TOOL.get(context.tool)
        require(tool is not None, 'tool_denied', 'Only source-bound native tool names are dispatched; no raw protocol or model-selected alias exists.')
        with self._lock:
            self._verify_owner_closure()
            policy = load_policy(self.policy_path)
            if tool == 'policy.inspect':
                exact(request, ()); return inspect_policy(policy)
            if tool.startswith('artifact.'): return self._artifact(context, request, tool)
            if tool=='role.acknowledge':
                exact(request,('reads',));require(self.pool is not None,'pool_required','Typed role acknowledgement requires the fork runtime pool.')
                lease=self.pool.for_actor(context.thread_id)
                return self.pool.role_acknowledgement(context,lease.reservation,'role-'+lease.reservation+'-'+str(lease.epoch),request['reads'])
            exact(request, ('operation_id','payload_sha256','payload'))
            require(type(request['operation_id']) is str and request['operation_id'] in self.accepted,
                    'operation_unaccepted', 'No applicable previously accepted operation.')
            accepted = self.accepted[request['operation_id']]
            require(accepted['tool'] == tool and accepted['actor'] == context.thread_id
                    and digest(request['payload']) == request['payload_sha256'] == accepted['payload_sha256'],
                    'operation_changed', 'Actual caller, route or accepted payload differs.')
            if self.verification_admission is None:
                proof_gate(self.profile, self.manifest, self.runtime_binding, self.enforcement_proof)
            else:
                self.verification_admission.check(self.owners.root, self.profile, self.manifest, self.runtime_binding, tool)
            operation = copy.deepcopy(accepted['operation'])
            # Automatic/explicit origin belongs to protected accepted-run metadata.
            require(type(accepted['automatic']) is bool, 'origin', 'Accepted run origin is missing.')
            operation['automatic'] = accepted['automatic']
            observation = copy.deepcopy(accepted['observation']); observation['now'] = datetime.now(timezone.utc).isoformat()
            observation['policy_sha256'] = digest(policy)
            if operation['class'] == 'memory.publish':
                config = self.owners.memory.load_config(self.owners.root)
                observation['automatic_capture'] = config['integration']['automatic_capture']
            decision = evaluate_operation(policy, accepted['entitlement'], operation, observation, verification=self.verification_admission is not None)
            require(decision['allowed'], decision['code'], 'Operation does not satisfy prior accepted authority.')
            existing = self.grants.inspect(request['operation_id'])
            if existing is not None and existing['state'] == 'consumed':
                if self.pool is not None:
                    require(existing['grant']['call'].get('schema_version')==2 and existing['grant']['call']['actor']==context.actor,
                            'grant_epoch','Receipt replay cannot cross a native load incarnation.')
                require(existing['grant']['actor'] == context.thread_id and existing['grant']['payload_sha256'] == request['payload_sha256']
                        and existing['grant']['policy_sha256'] == digest(policy)
                        and existing['grant']['trusted_manifest_sha256'] == digest(self.manifest)
                        and existing['grant']['profile_sha256']==digest(self.profile)
                        and existing['grant']['scope']==operation and existing['grant']['owner']==accepted['owner'],
                        'grant_replay', 'Retry actor, payload, scope or trusted binding differs.')
                require(accepted['task'] is None or accepted['task']['path'] in existing['post_state'], 'post_state', 'Retry must bind the canonical Task post-state.')
                require(existing['post_state'] == self._post_state(existing['post_state']), 'operation_changed', 'Later edits prevent original receipt replay.')
                return existing['receipt']
            if tool.startswith('memory.'):
                require(operation['class'] == 'memory.publish' and accepted['owner'] == 'memory', 'owner_permission', 'Memory publication requires its independent permission.')
            if tool.startswith('ontology.'):
                require(operation['class'] == 'ontology.publish' and accepted['owner'] == 'ontology', 'owner_permission', 'Ontology publication requires its independent permission.')
            if tool.startswith('task.'):
                require(operation['class'] == 'governance' and accepted['owner'] == 'task', 'owner_permission', 'Task mutation requires its owning governance permission.')
            if tool.startswith('runtime.'):
                require(operation['class']=='governance' and accepted['owner']=='runtime','owner_permission','Native lifecycle operations require their independent governance permission.')
            state = self._task(accepted, context.thread_id)
            classification = []
            for target in accepted['targets']:
                root = self.owners.root
                path = target['identity']['path']
                info = file_snapshot(root, path, 2000000)
                require(info['sha256'] == target['identity']['sha256'], 'source_changed', 'Target changed.')
                with parent_descriptor(root, path) as (parent, name):
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                    with os.fdopen(fd, 'rb') as stream:
                        current = os.fstat(stream.fileno())
                        require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1 and current.st_ino == info['inode'] and current.st_dev == info['device'], 'source_changed', 'Source identity changed before classification read.')
                        raw = stream.read(2000001)
                require(len(raw) <= 2000000 and hashlib.sha256(raw).hexdigest() == info['sha256'], 'source_changed', 'Source changed before classification.')
                classified = classify_target(self.ownership_map, target['identity'], target['ranges'], {path:raw})
                require(classified['state'] == 'classified', classified['code'], 'Unsafe target ownership.')
                required_class = {'documentation':'documentation', 'data':'documentation', 'technical':'technical',
                                  'governance':'governance', 'generated':'ontology.publish', 'historical':'governance'}[classified['class']]
                if classified['owner'] in ('memory','ontology') and classified['class'] != 'governance':
                    required_class = classified['owner'] + '.publish'
                require(operation['class'] == required_class, 'classification_permission', 'Accepted operation permission does not match actual target class.')
                require(classified['owner'] == accepted['owner'] and classified['route'] in accepted['routes'],
                        'classification_route', 'Exact target owner or update route is not independently authorized.')
                classification.append(classified)
            if tool == 'target.classify': return classification
            self._verify_owner_state(accepted['owner_state'])
            payload = copy.deepcopy(request['payload'])
            bindings = {'issuer':self.grants.issuer, 'prior_authority':accepted['entitlement']['id'],
                'actor':context.thread_id, 'call':context.binding(), 'controller':policy['controller'],
                'project':policy['project'], 'branch':operation['branch'], 'policy_sha256':digest(policy),
                'classification_sha256':digest(classification), 'source_sha256':digest(accepted['sources']),
                'payload_sha256':request['payload_sha256'], 'operation':tool,
                'scope':operation, 'task':accepted['task'], 'owner':accepted['owner'],
                'owner_state':accepted['owner_state'], 'trusted_manifest_sha256':digest(self.manifest),
                'profile_sha256':digest(self.profile)}
            for ref in accepted['sources']:
                require(file_snapshot(self.owners.root, ref['path'], 2000000)['sha256'] == ref['sha256'], 'source_changed', 'Frozen source changed.')
            existing = self.grants.inspect(request['operation_id'])
            recovering = tool in ('memory.recover','ontology.recover')
            if recovering:
                require(existing is not None and accepted['original_payload_sha256'] == existing['grant']['payload_sha256'], 'recovery_original', 'Fresh recovery must name the original exact owner payload.')
                bindings['payload_sha256'] = accepted['original_payload_sha256']
                bindings['operation'] = existing['grant']['operation']
                self.grants.resume_original(request['operation_id'], bindings)
            else:
                if existing is not None:
                    require(existing['state'] == 'consumed' and existing['grant']['payload_sha256'] == request['payload_sha256']
                            and existing['post_state'] == self._post_state(existing['post_state']), 'operation_pending', 'Original owner operation requires exact reconciliation.')
                    return existing['receipt']
                self.grants.issue(request['operation_id'], bindings)
                self.grants.begin(request['operation_id'], bindings)
            try:
                grant = None; grant_path = None
                if accepted['owner'] in ('memory','ontology'):
                    grant, grant_path = self._owner_grant(accepted, context, state, payload)
                if tool == 'task.event':
                    # Receipt-bearing fields come from live adapter observations only.
                    exact(payload, ('kind','data','response'))
                    data = payload['data']
                    if self.pool is not None:self._task_receipts(payload['kind'],data,accepted)
                    for key in (() if self.pool is not None else ('receipt','bootstrap_receipt')):
                        require(key not in data, 'native_arguments', 'Candidate cannot supply native receipt bodies.')
                        ref = key + '_sequence'
                        if ref in data:
                            seq = data.pop(ref); native_frame = self.adapter.raw_frames[seq]['frame']
                            item = native_frame.get('params', {}).get('item', {})
                            child = item['receiverThreadIds'][0] if item.get('tool') == 'spawnAgent' and len(item.get('receiverThreadIds', [])) == 1 else None
                            data[key] = self.adapter.receipt(seq, child=child)
                    event = {'event_id':request['operation_id'], 'actor':context.thread_id,
                        'execution_id':accepted['task']['execution_id'], 'generation':accepted['task']['generation'],
                        'kind':payload['kind'],'data':data}
                    response = payload['response']
                    require(not set(response) & {'actor','execution_id','generation'}, 'actor_arguments', 'Response identity is transport-owned.')
                    response.update(actor=context.thread_id, execution_id=accepted['task']['execution_id'], generation=accepted['task']['generation'])
                    payload = {'event':event, 'response':response}
                if tool == 'task.response':
                    require(not set(payload) & {'actor','execution_id','generation'}, 'actor_arguments', 'Identity comes from the live native envelope.')
                    payload.update(actor=context.thread_id, execution_id=accepted['task']['execution_id'], generation=accepted['task']['generation'])
                if tool.startswith('runtime.'):
                    if self.pool is not None:result=self._runtime(tool,context,payload,accepted,state,request['operation_id'])
                    else:
                        require(tool in ('runtime.observe','runtime.interrupt','runtime.message','runtime.followup'),
                                'runtime_version','Actual resume/delegation/release requires the explicit fork protocol.')
                        exact(payload, ('thread_id',) if tool in ('runtime.observe','runtime.interrupt') else ('thread_id','text'))
                        require(payload['thread_id'] in accepted['actors'], 'runtime_scope', 'Actor is outside assigned control scope.')
                        if tool == 'runtime.observe': result = self.adapter.observe(payload['thread_id'])
                        elif tool == 'runtime.interrupt': result = self.adapter.interrupt(payload['thread_id'])
                        elif tool == 'runtime.message': result = self.adapter.message(payload['thread_id'], payload['text'])
                        else: result = self.adapter.followup(payload['thread_id'], payload['text'])
                else:
                    result = self.owners.dispatch(tool, payload, grant, grant_path, accepted['task'], context.thread_id)
                result_path = self.grants.directory / (request['operation_id'] + '-owner-' + self.grants.inspect(request['operation_id']).get('recovery_grant', self.grants.inspect(request['operation_id'])['grant'])['nonce'] + '.json')
                fd = os.open(result_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(canonical(result)); stream.flush(); os.fsync(stream.fileno())
                outcome=('requested' if self.pool is not None and tool.startswith('runtime.') and
                    (result.get('kind') in self.native.RECEIPT_KINDS or result.get('state')=='release_pending') else self.owners.outcome(tool,result))
                receipt = {'operation_id':request['operation_id'], 'owner':accepted['owner'],
                           'result_sha256':digest(result), 'state':'owner_'+outcome}
                if tool.startswith('task.') and outcome=='completed':
                    path=(Path(result['task_folder'])/'task.json').relative_to(self.owners.root).as_posix() if tool=='task.create' else accepted['task']['path']
                    receipt['task']={'task_id':result['task_id'],'path':path,'revision':result['revision_after']}
                if self.pool is not None and tool.startswith('runtime.') and outcome=='requested':
                    if result.get('state')=='release_pending':
                        exact(result,('state','reservation','operation_id'))
                    else:
                        exact(result,('handle','kind','actor','load_epoch'))
                        require(type(result['handle']) is str and result['handle'] in self.pool.handles,
                                'runtime_result','Runtime did not return its protected typed observation handle.')
                    receipt['runtime']=copy.deepcopy(result)
                if outcome not in ('completed','observed','requested'):
                    self.grants.uncertain(request['operation_id'])
                    return receipt
                self.grants.finish(request['operation_id'], receipt, self._post_state(self._owner_post_paths(tool,result,accepted)))
                return receipt
            except Exception:
                # An owner may have written before returning an error; preserve the
                # original operation and journal, and never claim rollback or retry.
                self.grants.uncertain(request['operation_id'])
                raise
