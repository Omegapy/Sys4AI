"""Versioned native observations and process-local owner call context.

Structural validation is not authentication. Only the protected broker transport
installs a live context, and its process must be outside candidate control.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import hashlib
import json
import re
import base64

_current = ContextVar('sys4ai_verified_native_call', default=None)


class NativeError(ValueError):
    pass


def need(condition, message):
    if not condition: raise NativeError(message)


def fields(value, required, optional=()):
    need(type(value) is dict and set(required) <= set(value) <= set(required) | set(optional), 'Unknown or missing native fields.')


def identity(value):
    need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', value), 'Expected actual App Server thread ID.')


def sha(value):
    need(type(value) is str and re.fullmatch('[a-f0-9]{64}', value), 'Expected native binding digest.')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def controller(value):
    fields(value, ('kind', 'charter', 'policy', 'project_id', 'repository_id', 'coordination_root'))
    need(value['kind'] == 'curator', 'Version 2 requires explicit Curator origin.')
    for key in ('charter', 'policy'):
        fields(value[key], ('path', 'sha256')); sha(value[key]['sha256'])
        need(type(value[key]['path']) is str and value[key]['path'], 'Missing source binding.')
    for key in ('project_id', 'repository_id', 'coordination_root'):
        need(type(value[key]) is str and value[key], 'Missing project identity.')


def protocol(value):
    if type(value) is dict and value.get('schema_version') == 2:
        fields(value, ('schema_version','backend','broker_run_id','lineage_kind',
                       'runtime_sha256','schema_sha256','source_sha256','profile_sha256'))
        need(type(value['schema_version']) is int and value['backend']=='codex-app-server-v2'
             and value['lineage_kind']=='thread-fork','Unsupported native protocol tuple.')
        identity(value['broker_run_id'])
        for key in ('runtime_sha256','schema_sha256','source_sha256','profile_sha256'):sha(value[key])
        return
    fields(value, ('schema_version', 'backend', 'session_id', 'runtime_sha256', 'schema_sha256', 'profile_sha256'))
    need(type(value['schema_version']) is int and value['schema_version'] == 1 and value['backend'] == 'codex-app-server-v2', 'Unsupported native protocol.')
    identity(value['session_id'])
    for key in ('runtime_sha256', 'schema_sha256', 'profile_sha256'): sha(value[key])


def protocol_key(value):
    if value is None:return None
    return value.get('broker_run_id') if value.get('schema_version')==2 else value.get('session_id')


def observation(value, *, launch=False, subject=None, parent=None, session=None, protocol_version=None):
    if protocol_version is not None:
        need(type(value) is dict and value.get('schema_version')==protocol_version,'Observation/native protocol tuple differs.')
    if type(value) is dict and value.get('schema_version') == 2:
        validate_observation_v2(value, expected_kind='creation' if launch else None,
                                subject=subject, source=parent, broker_run_id=session)
        if launch:return value['actor']['thread_id']
        return status_value_v2(value)
    fields(value, ('schema_version', 'backend', 'session_id', 'sequence', 'raw_sha256', 'event'), ('child',))
    need(type(value['schema_version']) is int and value['schema_version'] == 1 and value['backend'] == 'codex-app-server-v2', 'Unsupported observation version.')
    identity(value['session_id']); sha(value['raw_sha256'])
    need(session is None or session == value['session_id'], 'Observation belongs to a foreign session.')
    need(type(value['sequence']) is int and value['sequence'] > 0, 'Observation sequence is missing.')
    event = value['event']; fields(event, ('method', 'params'))
    need(hashlib.sha256(canonical(event)).hexdigest() == value['raw_sha256'], 'Observation digest differs.')
    params = event['params']
    if launch:
        need(event['method'] == 'item/completed', 'Launch requires a completed native item.')
        fields(params, ('threadId', 'turnId', 'item')); identity(params['threadId']); identity(params['turnId'])
        item = params['item']
        fields(item, ('type', 'id', 'tool', 'status', 'senderThreadId', 'receiverThreadIds', 'agentsStates'), ('model', 'prompt', 'reasoningEffort'))
        need(item['type'] == 'collabAgentToolCall' and item['tool'] == 'spawnAgent' and item['status'] == 'completed', 'Expected actual successful spawnAgent item.')
        need(type(item['receiverThreadIds']) is list and len(item['receiverThreadIds']) == 1, 'Spawn must identify one actual child.')
        child = item['receiverThreadIds'][0]; identity(child)
        need(item['senderThreadId'] == params['threadId'] and (parent is None or parent == params['threadId']), 'Native sender differs from reserved parent.')
        lineage = value.get('child'); fields(lineage, ('id', 'parentThreadId', 'source'))
        need(lineage['id'] == child and lineage['parentThreadId'] == item['senderThreadId'], 'Child lineage does not match actual spawn.')
        source = lineage['source']; fields(source, ('subAgent',)); fields(source['subAgent'], ('thread_spawn',))
        spawn = source['subAgent']['thread_spawn']; fields(spawn, ('parent_thread_id', 'depth'), ('agent_nickname', 'agent_role', 'agent_path'))
        need(spawn['parent_thread_id'] == item['senderThreadId'] and type(spawn['depth']) is int and spawn['depth'] > 0, 'Native source lineage differs.')
        return child
    need('child' not in value, 'Unexpected child payload in status observation.')
    if event['method'] == 'thread/status/changed':
        fields(params, ('threadId', 'status')); identity(params['threadId'])
        state = params['status']; need(type(state) is dict, 'Expected native status object.')
        fields(state, ('type',), ('activeFlags',))
        need(state['type'] in ('notLoaded', 'idle', 'systemError', 'active'), 'Unsupported native thread status.')
        if state['type'] == 'active':
            need(type(state.get('activeFlags')) is list, 'Active native flags missing.')
        return {'active':'running', 'idle':'idle', 'systemError':'failed', 'notLoaded':None}[state['type']] if params['threadId'] == subject else None
    if event['method'] == 'turn/completed':
        fields(params, ('threadId', 'turn')); identity(params['threadId'])
        turn = params['turn']; fields(turn, ('id', 'items', 'status', 'error'))
        need(turn['status'] in ('completed', 'interrupted', 'failed'), 'Turn is not terminal.')
        # Completed turn is idle, not a stopped native actor.
        return {'completed':'idle', 'interrupted':'interrupted', 'failed':'failed'}[turn['status']] if params['threadId'] == subject else None
    raise NativeError('Unsupported native status observation.')


@dataclass(frozen=True)
class VerifiedCallContext:
    session_id: str
    request_id: str | int
    call_id: str
    thread_id: str
    turn_id: str
    tool: str
    sequence: int
    raw_sha256: str
    _transport: object

    def __reduce__(self):
        raise TypeError('Live native contexts cannot be serialized.')

    def binding(self):
        return {'session_id': self.session_id, 'request_id': self.request_id, 'call_id': self.call_id,
                'thread_id': self.thread_id, 'turn_id': self.turn_id, 'tool': self.tool,
                'sequence': self.sequence, 'raw_sha256': self.raw_sha256}


class TransportAuthority:
    """Only instantiated by trusted transport startup, never exposed as a dynamic tool."""
    def __init__(self, session_id):
        identity(session_id); self.session_id = session_id; self._pending = {}; self._used = set()

    def capture(self, frame, sequence):
        fields(frame, ('id', 'method', 'params'))
        need(frame['method'] == 'item/tool/call', 'Only native dynamic calls carry caller identity.')
        p = frame['params']; fields(p, ('arguments', 'callId', 'threadId', 'turnId', 'tool'), ('namespace',))
        for key in ('callId', 'threadId', 'turnId'): identity(p[key])
        need(p.get('namespace') in (None, 'curator') and type(p['tool']) is str, 'Unknown tool namespace.')
        need(type(sequence) is int and sequence > 0 and type(frame['id']) in (int, str), 'Invalid transport locator.')
        key = (frame['id'], p['callId']); need(key not in self._used and key not in self._pending, 'Duplicate native request.')
        context = VerifiedCallContext(self.session_id, frame['id'], p['callId'], p['threadId'], p['turnId'], p['tool'], sequence, hashlib.sha256(canonical(frame)).hexdigest(), self)
        self._pending[key] = context
        return context

    @contextmanager
    def invoke(self, context):
        key = (context.request_id, context.call_id)
        need(context._transport is self and self._pending.get(key) is context, 'Caller context was not received on this live transport.')
        token = _current.set(context)
        try: yield context
        finally:
            _current.reset(token); del self._pending[key]; self._used.add(key)


def require_live(binding, actor, *, session=None, tool=None):
    current = _current.get()
    if type(current) is VerifiedCallContextV2:
        need(current.thread_id==actor and current.binding()==binding,'No current verified native-v2 caller.')
        current._transport.registry.require_current(current.actor)
        need((session is None or session==current.broker_run_id) and (tool is None or current.tool==tool),'Caller run/tool mismatch.')
        return current
    need(type(current) is VerifiedCallContext and current.thread_id == actor and current.binding() == binding, 'No current verified native caller.')
    need((session is None or current.session_id == session) and (tool is None or current.tool == tool), 'Caller session/tool mismatch.')
    return current


def validate_owner(grant, orchestration, owner):
    need(grant.get('actor_kind') == 'manager' and grant.get('controller_origin') == 'curator', 'Only current Curator manager can use native owner grants.')
    need(orchestration.get('version') == 2 and orchestration.get('controller_origin', {}).get('kind') == 'curator', 'Owner needs an explicit Curator Task v2.')
    fields(grant['broker_binding'], ('owner', 'call', 'protocol', 'charter', 'policy'))
    b = grant['broker_binding']; need(b['owner'] == owner, 'Independent owner grant mismatch.')
    need(b['protocol'] == orchestration['native_protocol'] and b['charter'] == orchestration['controller_origin']['charter'] and b['policy'] == orchestration['controller_origin']['policy'], 'Current owner provenance changed.')
    require_current(b['protocol'], grant['actor_id'], b['call'])


def require_current(selected_protocol, actor, binding=None):
    protocol(selected_protocol)
    current=_current.get()
    need(current is not None,'No current native caller.')
    if selected_protocol['schema_version']==1:
        need(type(current) is VerifiedCallContext,'Legacy protocol requires its original live-call tuple.')
        return require_live(binding or current.binding(),actor,session=selected_protocol['session_id'])
    need(type(current) is VerifiedCallContextV2 and current._transport.protocol==selected_protocol,
         'Fork protocol requires the exact current protocol/live-call tuple.')
    return require_live(binding or current.binding(),actor,session=selected_protocol['broker_run_id'])


def kernel_instance(value):
    fields(value,('pid','parent','group','uid','started','executable'))
    for key in ('pid','parent','group','uid'):
        need(type(value[key]) is int and value[key]>=0,'Invalid kernel process identity.')
    need(value['pid']>0 and value['group']>0,'Missing owned process identity.')
    need(type(value['started']) is list and len(value['started'])==2 and
         all(type(x) is int and x>=0 for x in value['started']),'Missing microsecond start identity.')
    need(type(value['executable']) is str and value['executable'].startswith('/'),'Kernel image must be absolute.')


def actor_binding(value):
    fields(value,('thread_id','session_id','connection_id','load_epoch','runtime_instance'))
    for key in ('thread_id','connection_id'):identity(value[key])
    if value['session_id'] is not None:identity(value['session_id'])
    need(type(value['load_epoch']) is int and value['load_epoch']>0,'Invalid loaded incarnation.')
    kernel_instance(value['runtime_instance'])


def wire_record(direction, sequence, raw):
    need(direction in ('sent','received') and type(sequence) is int and sequence>0,'Invalid frame direction/sequence.')
    need(type(raw) is bytes and len(raw)<=2000000,'Invalid bounded raw frame.')
    try:frame=json.loads(raw)
    except (ValueError,RecursionError) as exc:raise NativeError('Invalid raw frame JSON.') from exc
    need(type(frame) is dict,'Expected JSON-RPC frame.')
    return {'direction':direction,'sequence':sequence,'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'canonical_sha256':hashlib.sha256(canonical(frame)).hexdigest(),
            'raw_base64':base64.b64encode(raw).decode(),'frame':frame}


def validate_wire_record(value):
    fields(value,('direction','sequence','raw_sha256','canonical_sha256','raw_base64','frame'))
    need(type(value['raw_base64']) is str and len(value['raw_base64'])<=2700000,'Oversized raw frame.')
    try:raw=base64.b64decode(value['raw_base64'],validate=True)
    except ValueError as exc:raise NativeError('Invalid raw frame encoding.') from exc
    need(wire_record(value['direction'],value['sequence'],raw)==value,'Raw and parsed native frame bindings differ.')
    return value['frame']


def correlated_pair(records, method):
    pairs=[]
    for row in records:
        sent=row['frame']
        if row['direction']!='sent' or sent.get('method')!=method:continue
        fields(sent,('id','method','params'))
        need(type(sent['params']) is dict,'Native request params must be an object.')
        responses=[x for x in records if x['direction']=='received' and 'method' not in x['frame']
                   and x['frame'].get('id')==sent['id']]
        need(len(responses)==1,'Missing or ambiguous correlated native response.')
        response=responses[0];fields(response['frame'],('id','result'))
        need(type(response['frame']['result']) is dict,'Native operation result must be an object.')
        need(response['sequence']>row['sequence'],'Response precedes its request.')
        pairs.append((sent['params'],response['frame']['result']))
    need(len(pairs)==1,'Receipt has no unique expected native operation.')
    return pairs[0]


def native_metadata(value):
    fields(value,('id','sessionId','parentThreadId','forkedFromId','source','path','model','reasoningEffort','modelProvider'))
    identity(value['id'])
    for key in ('sessionId','parentThreadId','forkedFromId'):
        if value[key] is not None:identity(value[key])
    need(value['source'] is None or type(value['source']) in (str,dict),'Invalid actual native source metadata.')
    need(value['path'] is None or type(value['path']) is str,'Invalid native storage metadata.')
    for key in ('model','reasoningEffort','modelProvider'):need(type(value[key]) is str and value[key],'Missing configured native setting.')


RECEIPT_KINDS=frozenset(('creation','role_acknowledgement','status','input_delivery','conflict_delivery',
                        'interrupt','runtime_release','resume','reconciliation'))


def validate_observation_v2(value, *, expected_kind=None, subject=None, source=None, broker_run_id=None):
    fields(value,('schema_version','backend','broker_run_id','kind','actor','operation_id','reservation_id','frames','facts'))
    need(type(value['schema_version']) is int and value['schema_version']==2 and value['backend']=='codex-app-server-v2','Unsupported observation tuple.')
    identity(value['broker_run_id']);identity(value['operation_id']);identity(value['reservation_id']);actor_binding(value['actor'])
    need(broker_run_id is None or value['broker_run_id']==broker_run_id,'Foreign broker run.')
    need(expected_kind is None or value['kind']==expected_kind,'Wrong native receipt family.')
    need(type(value['kind']) is str and value['kind'] in RECEIPT_KINDS,'Unknown native receipt family.')
    actor=value['actor']['thread_id'];need(subject is None or subject==actor,'Receipt actor differs.')
    records=value['frames'];need(type(records) is list and 0<len(records)<=16,'Unbounded or missing frame locators.')
    for record in records:validate_wire_record(record)
    need(len({(r['direction'],r['sequence']) for r in records})==len(records),'Duplicate frame locator.')
    facts=value['facts'];kind=value['kind']
    if kind in ('creation','resume'):
        fields(facts,('source_thread_id','logical_parent_id','metadata','settings','history_cut'))
        identity(facts['source_thread_id']);identity(facts['logical_parent_id']);native_metadata(facts['metadata'])
        need(source is None or source==facts['source_thread_id'],'Reserved fork source differs.')
        params,result=correlated_pair(records,'thread/fork' if kind=='creation' else 'thread/resume')
        read_params,read_result=correlated_pair(records,'thread/read')
        need(read_params=={'threadId':actor,'includeTurns':False},'Independent metadata read differs.')
        need(not set(params)&{'path','history','effort','dynamicTools','allowProviderModelFallback'},'Unsupported creation/resume override.')
        expected_thread=facts['source_thread_id'] if kind=='creation' else actor
        need(params.get('threadId')==expected_thread,'Native creation/resume target differs.')
        if kind=='creation':need(actor!=facts['source_thread_id'],'Fork did not create a distinct native ID.')
        for observed in (result.get('thread'),read_result.get('thread')):
            need(type(observed) is dict,'Missing actual native thread metadata.')
            for key in ('id','sessionId','parentThreadId','forkedFromId','source','path','model','reasoningEffort','modelProvider'):
                need(key in observed and observed[key]==facts['metadata'][key],'Independent native metadata differs: '+key)
        need(facts['metadata']['id']==actor and facts['metadata']['sessionId']==value['actor']['session_id']
             and facts['metadata']['forkedFromId']==facts['source_thread_id'],'Actual fork provenance differs.')
        fields(facts['settings'],('model','reasoning_effort','provider','profile_id','cwd'))
        settings=facts['settings']
        need(result.get('model')==settings['model']==facts['metadata']['model']
             and result.get('reasoningEffort')==settings['reasoning_effort']==facts['metadata']['reasoningEffort']
             and result.get('modelProvider')==settings['provider']==facts['metadata']['modelProvider']
             and result.get('cwd')==settings['cwd'] and (result.get('activePermissionProfile') or {}).get('id')==settings['profile_id'],
             'Configured settings/profile do not match their actual response.')
        need(params.get('model')==settings['model'] and params.get('modelProvider')==settings['provider']
             and (params.get('config') or {}).get('model_reasoning_effort')==settings['reasoning_effort']
             and params.get('permissions')==settings['profile_id'] and params.get('cwd')==settings['cwd'],
             'Precreation settings differ from effective settings.')
        cut=facts['history_cut'];fields(cut,('mode','turn_id','history_sha256','input_sha256'))
        need(cut['mode'] in ('lastTurnId','beforeTurnId'),'Unknown history boundary.');identity(cut['turn_id'])
        sha(cut['history_sha256']);sha(cut['input_sha256'])
        if kind=='creation':need(params.get(cut['mode'])==cut['turn_id'] and not (set(params)&({'lastTurnId','beforeTurnId'}-{cut['mode']})), 'Fork history cut differs.')
    elif kind in ('input_delivery','conflict_delivery'):
        required=('recipient','turn_id','input_sha256','artifact_sha256s')
        fields(facts,required+(('origin_assignment_id','explanation_sha256') if kind=='conflict_delivery' else ()))
        need(facts['recipient']==actor,'Wrong delivery recipient.');identity(facts['turn_id']);sha(facts['input_sha256'])
        need(type(facts['artifact_sha256s']) is list,'Missing delivered input references.')
        for item in facts['artifact_sha256s']:sha(item)
        methods=[r['frame'].get('method') for r in records if r['direction']=='sent']
        need(len(methods)==1 and methods[0] in ('turn/start','turn/steer'),'Wrong delivery operation.')
        params,result=correlated_pair(records,methods[0])
        need(params.get('threadId')==actor and hashlib.sha256(canonical(params.get('input'))).hexdigest()==facts['input_sha256'],'Delivery input bytes differ.')
        returned=(result.get('turn') or {}).get('id') if methods[0]=='turn/start' else result.get('turnId')
        need(returned==facts['turn_id'],'Delivery acknowledgement has another turn.')
        text=canonical(params.get('input')).decode()
        need(all(h in text for h in facts['artifact_sha256s']),'Delivered message omits an exact input digest.')
        if kind=='conflict_delivery':
            identity(facts['origin_assignment_id']);sha(facts['explanation_sha256'])
            need(facts['explanation_sha256'] in facts['artifact_sha256s'],'Conflict explanation is outside the delivered input.')
    elif kind=='role_acknowledgement':
        fields(facts,('reads','call_id'));need(type(facts['reads']) is dict and facts['reads'],'Missing exact role/read acknowledgement.')
        for path,digest in facts['reads'].items():need(type(path) is str and path,'Missing read path.');sha(digest)
        calls=[r['frame'] for r in records if r['direction']=='received' and r['frame'].get('method')=='item/tool/call']
        need(len(calls)==1 and calls[0]['params']['threadId']==actor and calls[0]['params']['callId']==facts['call_id'],'Role callback actor/call differs.')
        need(type(calls[0]['params']['arguments']) is dict and calls[0]['params']['arguments'].get('reads')==facts['reads'],'Role acknowledgement differs from actual callback bytes.')
    elif kind=='status':
        fields(facts,('native_state',))
        need(facts['native_state'] in ('active','idle','notLoaded','systemError','completed','interrupted','failed'),'Unknown native status.')
        observed=[]
        for row in records:
            frame=row['frame'];params=frame.get('params',{})
            if row['direction']=='received' and params.get('threadId')==actor:
                if frame.get('method')=='thread/status/changed':observed.append(params['status']['type'])
                if frame.get('method')=='turn/completed':observed.append(params['turn']['status'])
        if not observed:
            params,result=correlated_pair(records,'thread/read');need(params.get('threadId')==actor,'Status read actor differs.')
            observed.append(result['thread']['status']['type'])
        need(facts['native_state'] in observed,'Status is not present in native evidence.')
    elif kind=='interrupt':
        fields(facts,('turn_id','acknowledged','observed_state'))
        params,result=correlated_pair(records,'turn/interrupt')
        need(params=={'threadId':actor,'turnId':facts['turn_id']} and facts['acknowledged'] is True,'Interrupt acknowledgement differs.')
        need(facts['observed_state'] in ('unknown','interrupted','completed','failed'),'Unknown stop observation.')
        if facts['observed_state']!='unknown':
            need(any(r['direction']=='received' and r['frame'].get('method')=='turn/completed'
                and r['frame']['params'].get('threadId')==actor and r['frame']['params']['turn'].get('id')==facts['turn_id']
                and r['frame']['params']['turn'].get('status')==facts['observed_state'] for r in records),'Interrupt result unobserved.')
    elif kind=='runtime_release':
        fields(facts,('admission_closed','owner_reconciled','local_runtime_absent','local_companion_absent','lease_released','provider_outcome','cleanup_sha256'))
        for key in ('admission_closed','owner_reconciled','local_runtime_absent','local_companion_absent','lease_released'):need(type(facts[key]) is bool,'Invalid release evidence flag.')
        sha(facts['cleanup_sha256']);need(facts['provider_outcome'] in ('unknown','completed','interrupted','failed'),'Invalid provider outcome.')
        need(not facts['lease_released'] or all(facts[k] for k in ('admission_closed','owner_reconciled','local_runtime_absent','local_companion_absent')),'Unreconciled local capacity release.')
    else:
        fields(facts,('assignments','owner_state'))
        need(type(facts['assignments']) is list and type(facts['owner_state']) is list,'Invalid reconciliation mapping.')
        seen=set()
        for item in facts['assignments']:
            fields(item,('assignment_id','observation'));identity(item['assignment_id']);need(item['assignment_id'] not in seen,'Duplicate reconciled assignment.');seen.add(item['assignment_id'])
            need(item['observation'].get('kind') in ('status','runtime_release','interrupt'),'Wrong per-assignment reconciliation kind.')
            validate_observation_v2(item['observation'],broker_run_id=value['broker_run_id'])
        for item in facts['owner_state']:fields(item,('path','sha256'));sha(item['sha256'])
    return value


def status_value_v2(value):
    kind=value['kind'];facts=value['facts']
    if kind=='status':return {'active':'running','completed':'idle','systemError':'failed','notLoaded':None}.get(facts['native_state'],facts['native_state'])
    if kind=='interrupt':return None if facts['observed_state']=='unknown' else ('idle' if facts['observed_state']=='completed' else facts['observed_state'])
    if kind=='runtime_release':return 'interrupted' if facts['lease_released'] else None
    raise NativeError('Receipt family cannot be substituted for status.')


class LoadedActorRegistry:
    """Trusted broker registry; candidates never receive this object."""
    def __init__(self, broker_run_id):
        identity(broker_run_id);self.broker_run_id=broker_run_id;self.current={};self.last_epoch={};self.quarantine=[]
    def bind(self, actor):
        actor_binding(actor);thread=actor['thread_id']
        need(thread not in self.current and actor['load_epoch']>self.last_epoch.get(thread,0),'Native ID already loaded or epoch reused.')
        need(all(x['connection_id']!=actor['connection_id'] for x in self.current.values()),'One connection cannot own multiple actors.')
        self.current[thread]=json.loads(canonical(actor));self.last_epoch[thread]=actor['load_epoch']
    def require_current(self, actor):
        actor_binding(actor);need(self.current.get(actor['thread_id'])==actor,'Native actor incarnation is not admitted.')
    def close_admission(self, actor):
        self.require_current(actor);del self.current[actor['thread_id']]


@dataclass(frozen=True)
class VerifiedCallContextV2:
    broker_run_id: str
    actor: dict
    request_id: str | int
    call_id: str
    turn_id: str
    tool: str
    locator: dict
    _transport: object
    @property
    def thread_id(self):return self.actor['thread_id']
    @property
    def session_id(self):return self.actor['session_id']
    @property
    def sequence(self):return self.locator['sequence']
    @property
    def raw_sha256(self):return self.locator['raw_sha256']
    def __reduce__(self):raise TypeError('Live native contexts cannot be serialized.')
    def binding(self):
        return {'schema_version':2,'broker_run_id':self.broker_run_id,'actor':json.loads(canonical(self.actor)),
                'request_id':self.request_id,'call_id':self.call_id,'turn_id':self.turn_id,'tool':self.tool,
                'locator':{k:self.locator[k] for k in ('direction','sequence','raw_sha256','canonical_sha256')}}


class TransportAuthorityV2:
    def __init__(self, selected_protocol, actor, registry):
        protocol(selected_protocol);need(selected_protocol['schema_version']==2,'Expected fork protocol.')
        registry.require_current(actor);need(registry.broker_run_id==selected_protocol['broker_run_id'],'Registry belongs to another broker run.')
        self.protocol=json.loads(canonical(selected_protocol));self.actor=json.loads(canonical(actor));self.registry=registry
        self.broker_run_id=selected_protocol['broker_run_id'];self.session_id=actor['session_id'];self._pending={};self._used=set()
    def capture(self, frame, sequence, raw=None):
        self.registry.require_current(self.actor);fields(frame,('id','method','params'))
        need(type(frame['id']) in (str,int) and (type(frame['id']) is int or 0<len(frame['id'])<=128),
             'Invalid native JSON-RPC request identity.')
        need(frame['method']=='item/tool/call','Only actual native tool calls carry caller authority.')
        p=frame['params'];fields(p,('arguments','callId','threadId','turnId','tool'),('namespace',))
        need(p['threadId']==self.actor['thread_id'],'Unadmitted native actor on owned connection.')
        for key in ('callId','turnId'):identity(p[key])
        need(p.get('namespace') in (None,'curator') and type(p['tool']) is str,'Unselected native tool namespace.')
        key=(frame['id'],p['callId']);need(key not in self._pending and key not in self._used,'Repeated native call.')
        locator=wire_record('received',sequence,raw if raw is not None else canonical(frame))
        need(locator['frame']==frame,'Captured frame differs from actual wire bytes.')
        context=VerifiedCallContextV2(self.broker_run_id,json.loads(canonical(self.actor)),frame['id'],p['callId'],p['turnId'],p['tool'],locator,self)
        self._pending[key]=context;return context
    @contextmanager
    def invoke(self, context):
        key=(context.request_id,context.call_id);self.registry.require_current(context.actor)
        need(context._transport is self and self._pending.get(key) is context,'Caller context was not received on this protected connection.')
        token=_current.set(context)
        try:yield context
        finally:_current.reset(token);self._pending.pop(key,None);self._used.add(key)
