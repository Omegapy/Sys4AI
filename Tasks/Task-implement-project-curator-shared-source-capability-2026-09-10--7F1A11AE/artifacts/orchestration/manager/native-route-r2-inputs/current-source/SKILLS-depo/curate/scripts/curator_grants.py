"""Private exact-operation grants; no candidate-facing acceptance operation."""
import copy
from datetime import datetime, timedelta, timezone
import os
import stat
from pathlib import Path
import secrets
from curator_policy import MAX_BYTES, PERMISSIONS, bounded, canonical, decode, exact, moment, require, sha, text, texts

FIELDS = ('schema_version', 'issuer', 'prior_authority', 'nonce', 'issued_at', 'expires_at',
    'actor', 'call', 'controller', 'project', 'branch', 'policy_sha256', 'classification_sha256',
    'source_sha256', 'payload_sha256', 'operation', 'scope', 'task', 'owner', 'owner_state',
    'trusted_manifest_sha256', 'profile_sha256')


def relative(value):
    text(value)
    path=Path(value)
    require(not path.is_absolute() and str(path)==value and value not in ('.','')
            and '..' not in path.parts,'grant_path','Grant owner references require exact relative paths.')


def reference(value, nullable_hash=False):
    exact(value,('path','sha256'));relative(value['path'])
    if not (nullable_hash and value['sha256'] is None):sha(value['sha256'])


def validate_owner_state(value):
    bounded(value)
    exact(value,('schema_version','inputs','journal'))
    require(type(value['schema_version']) is int and value['schema_version']==1,'owner_state','Unknown owner state version.')
    require(type(value['inputs']) is list,'owner_state','Owner inputs must be an exact list.')
    seen=set()
    for entry in value['inputs']:
        reference(entry,True)
        require(entry['path'] not in seen,'owner_state','Repeated owner input path.')
        seen.add(entry['path'])
    if value['journal'] is not None:reference(value['journal'])
    return value


def validate_bindings(grant):
    bounded(grant)
    for key in ('issuer','prior_authority','actor','branch','operation','owner'):text(grant[key])
    call=grant['call']
    exact(call,('session_id','request_id','call_id','thread_id','turn_id','tool','sequence','raw_sha256'))
    for key in ('session_id','call_id','thread_id','turn_id','tool'):text(call[key])
    require(type(call['request_id']) in (str,int) and type(call['sequence']) is int and call['sequence']>0,
            'grant_call','Native request identity or observation sequence is malformed.')
    if isinstance(call['request_id'],str):text(call['request_id'])
    sha(call['raw_sha256'])
    require(call['thread_id']==grant['actor'] and call['tool']==grant['operation'].replace('.','_'),
            'grant_call','Authenticated wire call differs from logical operation or actor.')
    controller=grant['controller'];exact(controller,('kind','charter'))
    require(controller['kind'] in ('curator','director'),'grant_controller','An operating grant requires a selected controller.')
    reference(controller['charter'])
    project=grant['project'];exact(project,('id','repository_id','coordination_root'))
    for value in project.values():text(value)
    require(Path(project['coordination_root']).is_absolute(),'grant_project','Canonical project root must be absolute.')
    scope=grant['scope'];exact(scope,('class','project_id','repository_id','coordination_root','branch',
        'paths','tools','network','payload_sha256','cost','automatic'))
    require(type(scope['class']) is str and scope['class'] in PERMISSIONS,'grant_scope','Unknown operation permission.')
    for key in ('paths','tools','network'):texts(scope[key])
    for path in scope['paths']:relative(path)
    sha(scope['payload_sha256'])
    require(type(scope['automatic']) is bool,'grant_scope','Request origin must be a boolean.')
    exact(scope['cost'],('model_calls','work_seconds','candidate_bytes','concurrent_agents'))
    require(all(type(value) is int and 0<=value<=2147483647 for value in scope['cost'].values()),
            'grant_scope','Malformed finite operation budget.')
    require(scope['project_id']==project['id'] and scope['repository_id']==project['repository_id']
            and scope['coordination_root']==project['coordination_root'] and scope['branch']==grant['branch']
            and scope['payload_sha256']==grant['payload_sha256'],'grant_scope','Grant scope bindings disagree.')
    task=grant['task']
    if task is not None:
        exact(task,('path','sha256','task_id','execution_id','generation','assignment_id','revision'))
        relative(task['path']);sha(task['sha256'])
        for key in ('task_id','execution_id','assignment_id'):text(task[key])
        for key in ('generation','revision'):require(type(task[key]) is int and task[key]>0,'grant_task','Invalid current Task generation/revision.')
    else:require(grant['operation']=='task.create','grant_task','Only Task bootstrap has no current Task binding.')
    validate_owner_state(grant['owner_state'])


def validate_grant(grant, expected, now=None):
    exact(grant, FIELDS)
    validate_bindings(grant)
    require(type(grant['schema_version']) is int and grant['schema_version'] == 1, 'grant_version', 'Unsupported Curator grant.')
    sha(grant['nonce'])
    current = now or datetime.now(timezone.utc)
    issued, expires = moment(grant['issued_at']), moment(grant['expires_at'])
    require(issued <= current <= expires and 0 < (expires - issued).total_seconds() <= 300, 'grant_expired', 'Grant is stale or expired.')
    for key in ('policy_sha256', 'classification_sha256', 'source_sha256', 'payload_sha256', 'trusted_manifest_sha256', 'profile_sha256'): sha(grant[key])
    require(set(expected) == set(FIELDS) - {'schema_version', 'nonce', 'issued_at', 'expires_at'}, 'grant_bindings', 'Exact expected grant bindings are required.')
    require(all(grant[key] == value for key, value in expected.items()), 'grant_changed', 'Exact actor/source/payload/owner binding differs.')
    return grant


class GrantStore:
    """Trusted broker-only store in an already selected protected directory."""
    def __init__(self, directory, issuer):
        self.directory = Path(directory).resolve(strict=True)
        require(self.directory.is_dir(), 'grant_store', 'Private store is unavailable.')
        self.issuer = issuer

    def _path(self, operation_id):
        require(type(operation_id) is str and operation_id and len(operation_id) <= 96
                and all(c.isascii() and (c.isalnum() or c in '-_') for c in operation_id), 'operation_id', 'Invalid operation ID.')
        p = self.directory / (operation_id + '.json')
        require(not p.is_symlink(), 'grant_store', 'Grant store symlink is forbidden.')
        return p

    def _write(self, operation_id, document, *, new=False):
        data=canonical(document)
        require(len(data)<=MAX_BYTES,'grant_size','Private operation record exceeds its bounded decoder size.')
        target = self._path(operation_id)
        if new:
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as out: out.write(data); out.flush(); os.fsync(out.fileno())
        else:
            temporary = self.directory / ('.' + secrets.token_hex(16))
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                with os.fdopen(fd, 'wb') as out: out.write(data); out.flush(); os.fsync(out.fileno())
                os.replace(temporary, target)
            finally: temporary.unlink(missing_ok=True)
        descriptor = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)

    def inspect(self, operation_id):
        p = self._path(operation_id)
        if not p.exists(): return None
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as src:
            require(stat.S_ISREG(os.fstat(src.fileno()).st_mode) and os.fstat(src.fileno()).st_nlink == 1, 'grant_store', 'Private store hardlink is forbidden.')
            return decode(src.read(250001))

    def issue(self, operation_id, bindings, now=None):
        require(bindings.get('issuer') == self.issuer, 'issuer', 'Unknown protected issuer.')
        now = now or datetime.now(timezone.utc)
        grant = {**copy.deepcopy(bindings), 'schema_version': 1, 'nonce': secrets.token_hex(32),
                 'issued_at': now.isoformat(), 'expires_at': (now + timedelta(seconds=300)).isoformat()}
        validate_grant(grant, bindings, now)
        self._write(operation_id, {'state':'issued', 'grant':grant, 'receipt':None, 'post_state':None}, new=True)
        return grant

    def begin(self, operation_id, bindings):
        record = self.inspect(operation_id)
        require(record is not None and record['state'] == 'issued', 'grant_replay', 'Operation is consumed or awaits exact owner reconciliation.')
        validate_grant(record['grant'], bindings)
        record['state'] = 'dispatching'; self._write(operation_id, record)
        return record['grant']

    def finish(self, operation_id, receipt, post_state):
        record = self.inspect(operation_id)
        require(record and record['state'] == 'dispatching', 'grant_state', 'No dispatched grant.')
        record.update(state='consumed', receipt=receipt, post_state=post_state)
        self._write(operation_id, record)

    def resume_original(self, operation_id, bindings, now=None):
        record = self.inspect(operation_id)
        require(record and record['state'] in ('dispatching', 'owner-partial'), 'grant_state', 'No original uncertain owner operation.')
        original = record['grant']
        require(all(original[k] == bindings[k] for k in ('payload_sha256','operation','project','branch','owner')),
                'recovery_changed', 'Recovery must retain the original exact owner payload and project.')
        if original['task'] is not None:
            require(all(original['task'][k] == bindings['task'][k] for k in ('task_id','execution_id','generation','assignment_id')),
                    'recovery_changed', 'Recovery cannot silently change its execution owner.')
        now = now or datetime.now(timezone.utc)
        fresh = {**copy.deepcopy(bindings), 'schema_version':1, 'nonce':secrets.token_hex(32),
                 'issued_at':now.isoformat(), 'expires_at':(now + timedelta(seconds=300)).isoformat()}
        validate_grant(fresh, bindings, now)
        record['recovery_grant'] = fresh; record['state'] = 'dispatching'
        self._write(operation_id, record)
        return fresh

    def uncertain(self, operation_id):
        record = self.inspect(operation_id)
        require(record and record['state'] == 'dispatching', 'grant_state', 'No dispatched grant.')
        record['state'] = 'owner-partial'; self._write(operation_id, record)

    def reconciled(self, operation_id, bindings, receipt, post_state):
        record = self.inspect(operation_id)
        require(record and record['state'] in ('dispatching', 'owner-partial'), 'grant_state', 'Only original uncertain operation can reconcile.')
        require(all(record['grant'][k] == bindings[k] for k in ('payload_sha256','operation','project','branch','owner','task')), 'recovery_changed', 'Recovery must retain the exact original operation.')
        record.update(state='consumed', receipt=receipt, post_state=post_state); self._write(operation_id, record)
