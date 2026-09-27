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
    fields(value, ('schema_version', 'backend', 'session_id', 'runtime_sha256', 'schema_sha256', 'profile_sha256'))
    need(type(value['schema_version']) is int and value['schema_version'] == 1 and value['backend'] == 'codex-app-server-v2', 'Unsupported native protocol.')
    identity(value['session_id'])
    for key in ('runtime_sha256', 'schema_sha256', 'profile_sha256'): sha(value[key])


def observation(value, *, launch=False, subject=None, parent=None, session=None):
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
    need(type(current) is VerifiedCallContext and current.thread_id == actor and current.binding() == binding, 'No current verified native caller.')
    need((session is None or current.session_id == session) and (tool is None or current.tool == tool), 'Caller session/tool mismatch.')
    return current


def validate_owner(grant, orchestration, owner):
    need(grant.get('actor_kind') == 'manager' and grant.get('controller_origin') == 'curator', 'Only current Curator manager can use native owner grants.')
    need(orchestration.get('version') == 2 and orchestration.get('controller_origin', {}).get('kind') == 'curator', 'Owner needs an explicit Curator Task v2.')
    fields(grant['broker_binding'], ('owner', 'call', 'protocol', 'charter', 'policy'))
    b = grant['broker_binding']; need(b['owner'] == owner, 'Independent owner grant mismatch.')
    need(b['protocol'] == orchestration['native_protocol'] and b['charter'] == orchestration['controller_origin']['charter'] and b['policy'] == orchestration['controller_origin']['policy'], 'Current owner provenance changed.')
    require_live(b['call'], grant['actor_id'], session=b['protocol']['session_id'])
