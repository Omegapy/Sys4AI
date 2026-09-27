"""Resolved file identities and proof admission. A manifest is not OS proof."""
from contextlib import contextmanager
import hashlib
import copy
import os
from pathlib import Path
import stat
import unicodedata
import json
import sqlite3
import time
from urllib.parse import quote

from curator_policy import PolicyError, bounded, digest, exact, require, texts

CHANNELS = frozenset(('commandExecution', 'fileChange', 'dynamicToolCall', 'mcpToolCall',
    'collabAgentToolCall', 'webSearch', 'imageView', 'imageGeneration', 'permissionEscalation'))

HISTORY_METADATA_COLUMNS = {
    'thread_history_projection_state':('thread_id','next_rollout_byte_offset','next_rollout_ordinal'),
    'thread_turns':('thread_id','turn_id','rollout_ordinal','status','started_at','completed_at','duration_ms',
        'first_user_item_id','final_agent_item_id','rollout_byte_offset','rollout_end_ordinal','rollout_end_byte_offset'),
    'thread_items':('thread_id','turn_id','item_id','rollout_ordinal','created_at_ms','item_type','updated_at_ordinal'),
    'thread_realtime_items':('thread_id','item_id','rollout_ordinal','created_at_ms','item_type'),
}
HISTORY_METADATA_KEYS = {'thread_history_projection_state':('thread_id',),'thread_turns':('thread_id','turn_id'),
    'thread_items':('thread_id','turn_id','item_id'),'thread_realtime_items':('thread_id','item_id')}

AMBIENT_LIMITS={'ambient_review_batches':4,'new_external_ids_per_batch':2,'new_external_ids_total':8,
    'new_native_projects_total':4,'new_project_roots_total':8,'challenge_or_receipt_bytes':200000,
    'metadata_checkpoints_total':96,'project_metadata_rows':10000}
AMBIENT_THREAD_COLUMNS=('id','created_at','updated_at','archived','has_user_event','model_provider','model','reasoning_effort',
    'is_pinned','project_id','rollout_path','source','cwd','history_mode')
AMBIENT_PROJECT_COLUMNS=('id','position','created_at_ms','updated_at_ms')
AMBIENT_ROOT_COLUMNS=('project_id','position','path')


def canonical_root(path):
    p = Path(path)
    require(p.is_absolute(), 'root', 'Root must be absolute.')
    resolved = p.resolve(strict=True)
    require(resolved.is_dir(), 'root', 'Root must be a directory.')
    return resolved


@contextmanager
def parent_descriptor(root, relative):
    root = canonical_root(root); p = Path(relative)
    require(not p.is_absolute() and p.parts and '..' not in p.parts and str(p) == relative,
            'path', 'Expected normalized relative path.')
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in p.parts[:-1]:
            actual = os.listdir(descriptor)
            matches = [n for n in actual if unicodedata.normalize('NFC', n).casefold() == unicodedata.normalize('NFC', part).casefold()]
            require(matches == [part], 'alias', 'Directory spelling or normalization is ambiguous.')
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor); descriptor = child
        matches = [n for n in os.listdir(descriptor) if unicodedata.normalize('NFC', n).casefold() == unicodedata.normalize('NFC', p.name).casefold()]
        require(matches in ([], [p.name]), 'alias', 'File spelling or normalization is ambiguous.')
        yield descriptor, p.name
    finally:
        os.close(descriptor)


def file_snapshot(root, relative, max_bytes=25000000):
    with parent_descriptor(root, relative) as (parent, name):
        try:fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        except OSError as exc:
            raise PolicyError('file_open_held','File is unavailable or became an unsafe alias before its no-follow open.') from exc
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= max_bytes,
                    'unsafe_file', 'Expected bounded single-link regular file.')
            hasher = hashlib.sha256(); size = 0
            while True:
                data = os.read(fd, min(65536, max_bytes + 1 - size))
                if not data: break
                hasher.update(data); size += len(data)
                require(size <= max_bytes, 'file_limit', 'File grew beyond bound.')
            after = os.fstat(fd); current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns)
            require(identity(before) == identity(after) == identity(current), 'file_changed', 'File identity changed during read.')
            return {'path': relative, 'sha256': hasher.hexdigest(),
                    'device': after.st_dev, 'inode': after.st_ino, 'size': size, 'mode': stat.S_IMODE(after.st_mode)}
        finally:
            os.close(fd)


def source_manifest(root, paths):
    root = canonical_root(root); texts(paths)
    entries = [file_snapshot(root, name) for name in sorted(paths)]
    return {'schema_version': 1, 'root': str(root), 'device': root.stat().st_dev,
            'inode': root.stat().st_ino, 'files': entries}


NATIVE_HEADER_BYTES=131072


def read_native_header(stream,actor):
    """Read only one bounded first JSONL record from this already checked descriptor."""
    first=stream.readline(NATIVE_HEADER_BYTES+1)
    require(len(first)<=NATIVE_HEADER_BYTES and first.endswith(b'\n'),'native_storage_header',
            'Native header is incomplete or exceeds the first-record bound.')
    def pairs(values):
        result={}
        for key,value in values:
            require(key not in result,'native_storage_header','Duplicate native header key.');result[key]=value
        return result
    try:metadata=json.loads(first.decode('utf-8',errors='strict'),object_pairs_hook=pairs)
    except (ValueError,UnicodeError,RecursionError) as exc:raise PolicyError('native_storage_header','Native first record is not bounded UTF-8 JSON.') from exc
    require(type(metadata) is dict and metadata.get('type')=='session_meta' and type(metadata.get('payload')) is dict
            and metadata['payload'].get('id')==actor,'native_storage_unproven','Native header does not identify the admitted actor.')
    return {'header_sha256':hashlib.sha256(first).hexdigest(),'header_bytes':len(first),'hash_scope':'first_jsonl_record_including_newline'}


def native_header_snapshot(root,relative,actor,previous=None):
    """Bind header identity, never whole-log integrity, through one no-follow descriptor."""
    with parent_descriptor(root,relative) as (parent,name):
        try:descriptor=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
        except OSError as exc:raise PolicyError('native_storage_changed','Native log is unavailable or became an unsafe alias.') from exc
        with os.fdopen(descriptor,'rb') as stream:
            before=os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_nlink==1,'native_storage_changed','Native log must remain a regular single-link file.')
            header=read_native_header(stream,actor);after=os.fstat(stream.fileno());current=os.stat(name,dir_fd=parent,follow_symlinks=False)
            identity=lambda value:(value.st_dev,value.st_ino,value.st_uid,value.st_mode,value.st_nlink,value.st_size,value.st_mtime_ns)
            require(identity(before)==identity(after)==identity(current),'native_storage_changed','Native log changed during its bounded header read.')
    value={'device':after.st_dev,'inode':after.st_ino,'uid':after.st_uid,'mode':stat.S_IMODE(after.st_mode),
        'links':after.st_nlink,'size':after.st_size,'mtime_ns':after.st_mtime_ns,**header}
    if previous is not None:
        stable=lambda item:{key:value for key,value in item.items() if key not in ('size','mtime_ns')}
        require(stable(value)==stable(previous) and value['size']>=previous['size'] and value['mtime_ns']>=previous['mtime_ns'],
                'native_storage_changed','Previously admitted inode/header identity changed or log size regressed.')
    return value


def verify_manifest(manifest):
    exact(manifest, ('schema_version', 'root', 'device', 'inode', 'files'))
    require(manifest['schema_version'] == 1, 'manifest_version', 'Unsupported source manifest.')
    current = source_manifest(manifest['root'], [e['path'] for e in manifest['files']])
    require(current == manifest, 'trusted_source_changed', 'Frozen trusted source/import closure changed.')
    return current


def validate_profile(profile):
    bounded(profile)
    exact(profile, ('schema_version', 'name', 'read_roots', 'write_roots', 'denied_roots',
                    'executables', 'channels', 'network', 'config_sha256'))
    require(profile['schema_version'] == 1, 'profile_version', 'Unsupported profile.')
    for key in ('read_roots', 'write_roots', 'denied_roots', 'executables', 'network'): texts(profile[key])
    for key in ('read_roots', 'write_roots', 'denied_roots'):
        for raw in profile[key]:
            require(str(canonical_root(raw)) == raw, 'root_alias', 'Profile requires canonical resolved roots.')
    for candidate in profile['read_roots'] + profile['write_roots']:
        for protected in profile['denied_roots']:
            require(not Path(protected).is_relative_to(candidate) and not Path(candidate).is_relative_to(protected),
                    'profile_overlap', 'Allowed roots overlap protected roots.')
    exact(profile['channels'], CHANNELS)
    require(all(mode in ('disabled', 'broker', 'confined') for mode in profile['channels'].values()), 'channel', 'Unknown channel selection.')
    require(profile['channels']['permissionEscalation'] == 'disabled', 'escalation', 'Candidate escalation must be disabled.')
    for executable in profile['executables']:
        require(str(Path(executable).resolve(strict=True)) == executable, 'executable_alias', 'Use resolved executable and interpreter paths.')
        require(Path(executable).is_file() and os.access(executable, os.X_OK), 'executable', 'Missing selected executable.')
    return profile


def proof_gate(profile, manifest, runtime_binding, proof):
    """Admission consumes trusted release evidence; candidate-supplied booleans are insufficient."""
    validate_profile(profile); verify_manifest(manifest)
    exact(proof, ('state', 'profile_sha256', 'manifest_sha256', 'runtime', 'channels', 'cases'))
    require(proof['state'] == 'passed' and proof['profile_sha256'] == digest(profile)
            and proof['manifest_sha256'] == digest(manifest) and proof['runtime'] == runtime_binding,
            'enforcement_unproven', 'No current source-bound native confinement proof.')
    exact(proof['channels'], CHANNELS)
    require(all(v in ('observed_denied', 'observed_confined', 'observed_disabled', 'observed_broker') for v in proof['channels'].values()),
            'channel_unproven', 'Every enabled channel requires direct evidence.')
    require(set(proof['cases']) >= {'NP-007','NP-010','NP-011','NP-012'} and
            all(v == 'passed' for v in proof['cases'].values()), 'enforcement_unproven', 'Required native adversarial cases are not passed.')
    return True

class VerificationAdmission:
    """Trusted-only first-proof admission; never a production readiness receipt."""
    def __init__(self, packet, reviewed_sha256):
        from curator_policy import moment
        from datetime import datetime, timezone
        exact(packet, ('schema_version','scope_id','root','device','inode','marker_sha256',
                       'manifest_sha256','profile_sha256','runtime','tools','expires_at','synthetic_only'))
        require(packet['schema_version'] == 1 and packet['synthetic_only'] is True,
                'verification_scope', 'Only a newly created synthetic proof scope is eligible.')
        require(digest(packet) == reviewed_sha256, 'verification_review', 'Host review does not bind this exact scope.')
        require(datetime.now(timezone.utc) < moment(packet['expires_at']), 'verification_expired', 'Proof scope expired.')
        self.packet = dict(packet); self.reviewed_sha256 = reviewed_sha256

    def check(self, root, profile, manifest, runtime, tool):
        from curator_policy import moment
        from datetime import datetime, timezone
        packet = self.packet
        require(digest(packet) == self.reviewed_sha256 and datetime.now(timezone.utc) < moment(packet['expires_at']),
                'verification_expired', 'Exact reviewed scope is stale or changed.')
        selected = canonical_root(root)
        require(str(selected) == packet['root'] and selected.stat().st_dev == packet['device']
                and selected.stat().st_ino == packet['inode'], 'verification_root', 'Disposable scope identity changed.')
        marker = file_snapshot(selected,'.curator-disposable-proof.json')
        require(marker['sha256'] == packet['marker_sha256'], 'verification_root', 'Disposable proof marker changed.')
        require(digest(manifest) == packet['manifest_sha256'] and digest(profile) == packet['profile_sha256']
                and runtime == packet['runtime'] and tool in packet['tools'], 'verification_scope', 'Runtime, source, profile or tool exceeds reviewed proof scope.')
        validate_profile(profile); verify_manifest(manifest)
        return True


class NativeStorageAdmission:
    """Exact host-reviewed runtime-owned records; no credential or index writer."""
    def __init__(self,packet,reviewed_sha256,*,deadline):
        from datetime import datetime,timezone
        from curator_policy import moment
        require(digest(packet)==reviewed_sha256 and datetime.now(timezone.utc)<moment(packet['expires_at']),
                'native_storage_scope','Current exact host-reviewed allocation packet is required.')
        selected=packet['storage'];exact(selected,('schema_version','kind','runtime_home','sqlite_home','database_path',
            'history_root','database_identity','history_identity','operations','metadata_file_bound','metadata_row_bound',
            'visibility_reviews','backfill_receipt','backfill_source_receipt','schema_receipt','concurrent_receipt','concurrent_threads',
            *(('history_index',) if 'history_index' in selected else ()),*(('ambient_review',) if 'ambient_review' in selected else ())))
        require(packet.get('stage') not in ('native-fork-p0','native-fork-p1') or 'history_index' in selected,
                'native_history_index_unselected','Native fork proof requires its explicitly selected established history index.')
        require(selected['schema_version']==1 and selected['kind']=='EstablishedRuntimeOwnedRecords',
                'native_storage_scope','No isolated-home or silent established-home fallback is admitted.')
        require(selected['runtime_home']==selected['sqlite_home'] and
                str(canonical_root(selected['runtime_home']))==selected['runtime_home'],
                'native_storage_scope','Runtime/account/index roots must be the explicitly selected established roots.')
        self.packet=packet;self.scope_sha256=reviewed_sha256;self.selected=selected;self.deadline=deadline
        self.root=canonical_root(packet['root']);self.state_root=self.root/'trusted/native-storage'
        require(self.state_root.is_dir(),'native_storage_scope','Prepared private allocation state is missing.')
        self.pending={};self.known={};self.slots={};self.paths={};self.path_identities={};self.baseline=None;self.runtime_inventory={}
        self.concurrent={};self.concurrent_paths={};self.concurrent_progress={}
        self.history_index=selected.get('history_index');self.history_baseline=None;self.history_progress=None
        if self.history_index is not None:
            h=self.history_index
            exact(h,('schema_version','path','identity','schema_sha256','migrations_sha256','metadata_row_bound','scan_seconds','columns','receipts'))
            require(h['schema_version']==1 and h['metadata_row_bound']==350000 and h['scan_seconds']==15
                    and h['columns']=={k:list(v) for k,v in HISTORY_METADATA_COLUMNS.items()}
                    and Path(h['path']).parent==Path(selected['runtime_home']),
                    'native_history_index_scope','Select only the existing history index and exact metadata limits/columns.')
        receipt=selected['concurrent_receipt']
        require(file_snapshot('/',receipt['path'].lstrip('/'))['sha256']==receipt['sha256'],
                'native_concurrency_scope','Concurrent execution metadata receipt changed.')
        approved=json.loads(Path(receipt['path']).read_text())
        require(approved.get('kind')=='host_active_execution_native_metadata' and approved.get('rows')==selected['concurrent_threads'],
                'native_concurrency_scope','Concurrent identities are not the exact host-bound set.')
        for row in selected['concurrent_threads']:
            exact(row,('execution_role','index_metadata','log_identity','native_parent_id'))
            actor=row['index_metadata']['id'];path=row['log_identity']['path']
            require(actor not in self.concurrent and path not in self.concurrent_paths
                    and row['index_metadata']['rollout_path']==path,'native_concurrency_scope','Duplicate or inconsistent concurrent identity.')
            self.concurrent[actor]=row;self.concurrent_paths[path]=row
        self._validate_roots();self.inspect_backfill()
        self.ambient=AmbientMetadataReview(self,selected['ambient_review']) if 'ambient_review' in selected else None

    def assert_admission(self):
        self._time()
        if self.ambient is not None:self.ambient.assert_admission()

    def record_runtime_inventory(self,binding):
        self.assert_admission()
        exact(binding,('thread_id','session_id','connection_id','load_epoch','runtime_instance'))
        require(type(binding['thread_id']) is str and binding['thread_id'] in self.known and type(binding['connection_id']) is str and binding['connection_id']
                and type(binding['load_epoch']) is int and binding['load_epoch']>0,'ambient_runtime_inventory','Runtime binding is not an admitted proof identity.')
        key=binding['connection_id'];old=self.runtime_inventory.get(key)
        require(old is None or old==binding,'ambient_runtime_inventory','An owned runtime incarnation changed identity.')
        if old is None:
            epochs=[row['load_epoch'] for row in self.runtime_inventory.values() if row['thread_id']==binding['thread_id']]
            require(binding['load_epoch']==max(epochs,default=0)+1,'ambient_runtime_inventory','Runtime incarnation sequence differs.')
            self.runtime_inventory[key]=copy.deepcopy(binding)

    def _time(self):require(time.monotonic()<self.deadline,'native_deadline','Native storage operation exceeded its absolute bound.')

    def _validate_roots(self):
        for path_key,identity_key,directory in (('database_path','database_identity',False),('history_root','history_identity',True)):
            path=Path(self.selected[path_key]);info=path.lstat();expected=self.selected[identity_key]
            require(not path.is_symlink() and (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
                    and {'device':info.st_dev,'inode':info.st_ino}==expected,
                    'native_storage_changed','Selected established storage identity changed.')
        require(Path(self.selected['database_path']).parent==Path(self.selected['sqlite_home'])
                and Path(self.selected['history_root']).is_relative_to(self.selected['runtime_home']),
                'native_storage_scope','Database or history root is outside its exact selected runtime root.')
        if self.history_index is not None:
            info=Path(self.history_index['path']).lstat()
            current={'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,'mode':stat.S_IMODE(info.st_mode),'links':info.st_nlink}
            require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and current==self.history_index['identity'],
                    'native_history_index_changed','Selected history database identity changed.')

    def _history_index_snapshot(self,external_ids=()):
        self._time();self._validate_roots();selected=self.history_index
        deadline=min(self.deadline,time.monotonic()+selected['scan_seconds'])
        connection=sqlite3.connect('file:'+quote(selected['path'])+'?mode=ro',uri=True,timeout=min(2,max(.001,deadline-time.monotonic())))
        started=time.monotonic();total=0;unlisted={};concurrent={};owned={};external={}
        def check():require(time.monotonic()<deadline,'native_history_deadline','History metadata snapshot exceeded its selected deadline.')
        try:
            connection.execute('PRAGMA query_only=ON');connection.set_progress_handler(lambda:int(time.monotonic()>=deadline),1000)
            connection.execute('BEGIN')
            schema=[list(row) for row in connection.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name')]
            require(digest(schema)==selected['schema_sha256'],'native_history_schema_changed','History index schema differs from its inspected selection.')
            migrations=connection.execute('SELECT version,description,installed_on,success,hex(checksum),execution_time FROM _sqlx_migrations ORDER BY version').fetchmany(1001)
            require(len(migrations)<=1000,'native_history_migrations','Unbounded history migration metadata.')
            require(digest(migrations)==selected['migrations_sha256'],'native_history_migrations_changed','History migration metadata differs from its complete inspected selection.')
            for table,columns in HISTORY_METADATA_COLUMNS.items():
                hasher=hashlib.sha256();count=0;concurrent[table]={};owned[table]={};external[table]={}
                order=','.join(HISTORY_METADATA_KEYS[table])
                cursor=connection.execute('SELECT '+','.join(columns)+' FROM '+table+' ORDER BY '+order)
                for row in cursor:
                    total+=1
                    if total%256==0:check()
                    require(total<=selected['metadata_row_bound'],'native_history_row_bound','History metadata exceeds the separate 350000-row scope.')
                    require(all(value is None or type(value) is int or (type(value) is str and len(value)<=1024) for value in row),
                            'native_history_metadata','Unexpected or oversized metadata scalar.')
                    value=dict(zip(columns,row));actor=value['thread_id']
                    raw=json.dumps(row,separators=(',',':'),ensure_ascii=False).encode()+b'\n'
                    if actor in self.known:
                        entry=owned[table].setdefault(actor,{'count':0,'_hasher':hashlib.sha256()});entry['count']+=1;entry['_hasher'].update(raw)
                        if table=='thread_history_projection_state':entry['projection']=value
                    elif actor in external_ids:
                        key=digest([value[k] for k in HISTORY_METADATA_KEYS[table]])
                        require(key not in external[table],'native_history_identity','Repeated external history metadata key.')
                        external[table][key]=value
                    elif actor in self.concurrent:
                        key=digest([value[k] for k in HISTORY_METADATA_KEYS[table]])
                        require(key not in concurrent[table],'native_history_identity','Repeated concurrent history row identity.')
                        concurrent[table][key]=value
                    else:hasher.update(raw);count+=1
                unlisted[table]={'count':count,'metadata_sha256':hasher.hexdigest()}
                for entry in owned[table].values():entry['metadata_sha256']=entry.pop('_hasher').hexdigest()
            check()
            return {'unlisted':unlisted,'concurrent':concurrent,'owned':owned,**({'external':external} if external_ids else {}),'total_rows':total,
                'schema_sha256':digest(schema),'migrations_sha256':digest(migrations),'seconds':time.monotonic()-started,
                'level':'explicit metadata columns only; item_json/error_json and whole database never read or hashed'}
        except sqlite3.OperationalError as exc:
            raise PolicyError('native_history_observation_unavailable','History metadata snapshot unavailable or interrupted.') from exc
        finally:connection.close()

    @staticmethod
    def _check_concurrent_history(before,after):
        for table,old_rows in before.items():
            new_rows=after[table]
            require(set(old_rows)<=set(new_rows),'native_history_concurrent_deleted','A previously observed concurrent row disappeared.')
            maxima={}
            for row in old_rows.values():
                if 'rollout_ordinal' in row:maxima[row['thread_id']]=max(maxima.get(row['thread_id'],-1),row['rollout_ordinal'])
            for key,row in new_rows.items():
                old=old_rows.get(key)
                if old is None:
                    require('rollout_ordinal' not in row or row['rollout_ordinal']>maxima.get(row['thread_id'],-1),
                            'native_history_concurrent_insert','Concurrent rows must append beyond the frozen ordinal boundary.')
                    continue
                growing=({'next_rollout_byte_offset','next_rollout_ordinal'} if table=='thread_history_projection_state' else
                         {'updated_at_ordinal'} if table=='thread_items' else
                         {'completed_at','duration_ms','rollout_end_ordinal','rollout_end_byte_offset'} if table=='thread_turns' and old['status']=='inProgress' else set())
                fillable={'final_agent_item_id'} if table=='thread_turns' and old['status']=='inProgress' else set()
                for field,value in old.items():
                    current=row[field]
                    if field in growing:
                        require((value is None and (current is None or type(current) is int and current>=0)) or
                                (type(value) is int and type(current) is int and current>=value),
                                'native_history_concurrent_regression','Concurrent metadata progress regressed.')
                    elif field in fillable:
                        require(current==value or (value is None and type(current) is str),
                                'native_history_concurrent_identity','Concurrent completion identity changed.')
                    elif field=='status' and table=='thread_turns' and value=='inProgress':
                        require(current in ('inProgress','completed','interrupted','failed'),
                                'native_history_concurrent_status','Unsupported concurrent turn transition.')
                    else:require(current==value,'native_history_concurrent_identity','Stable concurrent metadata changed.')

    @contextmanager
    def _database(self):
        self._time();self._validate_roots()
        connection=sqlite3.connect('file:'+quote(self.selected['database_path'])+'?mode=ro',uri=True,
            timeout=min(2,max(0.001,self.deadline-time.monotonic())))
        try:
            connection.execute('PRAGMA query_only=ON')
            connection.set_progress_handler(lambda:int(time.monotonic()>=self.deadline),1000)
            yield connection
        finally:connection.close()

    def inspect_backfill(self):
        with self._database() as connection:
            rows=connection.execute('SELECT id,status FROM backfill_state').fetchall()
        require(rows==[(1,'complete')],'native_backfill_unproven','Established index backfill is not already complete; no marker is forged.')
        return {'connection_mode':'read-only; query_only=ON','backfill_state':'complete'}

    def _history_metadata(self):
        root=Path(self.selected['history_root']);result={};count=0
        for directory,dirs,files in os.walk(root,followlinks=False):
            self._time()
            for name in (*dirs,*files):
                path=Path(directory)/name;info=path.lstat()
                require(not stat.S_ISLNK(info.st_mode),'native_history_alias','Unproved history-root alias.')
                if stat.S_ISDIR(info.st_mode):continue
                require(stat.S_ISREG(info.st_mode),'native_history_type','Unproved special file in history scope.')
                count+=1;require(count<=self.selected['metadata_file_bound'],'native_metadata_bound','History metadata inventory exceeds scope.')
                if str(path) in self.paths.values():continue
                key=digest(str(path.relative_to(root)))
                if str(path) in self.concurrent_paths:
                    row=self.concurrent_paths[str(path)];prior=row['log_identity']
                    frozen=(self.baseline or {}).get('concurrent_progress',{}).get(row['index_metadata']['id'],{})
                    current={'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,'mode':stat.S_IMODE(info.st_mode),'links':info.st_nlink}
                    require(all(current[k]==prior[k] for k in current) and info.st_size>=max(prior['size'],frozen.get('size_observed',0))
                            and info.st_mtime_ns>=max(prior['mtime_ns'],frozen.get('mtime_observed',0)),
                            'native_concurrent_identity_changed','Concurrent log identity changed or regressed outside its exact scope.')
                    result[key]=['provenance-bound-concurrent',*current.values()]
                    self.concurrent_progress[row['index_metadata']['id']].update(size_before=prior['size'],size_observed=info.st_size,
                        mtime_before=prior['mtime_ns'],mtime_observed=info.st_mtime_ns)
                else:result[key]=[info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns]
        return result

    def preservation_snapshot(self):
        self.inspect_backfill()
        self.concurrent_progress={}
        with self._database() as connection:
            for actor,binding in self.concurrent.items():
                expected=binding['index_metadata'];columns=list(expected)
                require(all(k.replace('_','').isalnum() for k in columns),'native_concurrency_scope','Unsupported metadata selector.')
                row=connection.execute('SELECT '+','.join(columns)+' FROM threads WHERE id=?',(actor,)).fetchone()
                require(row is not None,'native_concurrent_identity_changed','Bound concurrent index identity disappeared.')
                current=dict(zip(columns,row))
                frozen=(self.baseline or {}).get('concurrent_progress',{}).get(actor,{})
                require(all(current[k]==expected[k] for k in columns if k!='updated_at')
                        and current['updated_at']>=max(expected['updated_at'],frozen.get('updated_at_observed',0)),
                        'native_concurrent_identity_changed','Concurrent identity/settings changed outside the exact progress scope.')
                self.concurrent_progress[actor]={'execution_role':binding['execution_role'],
                    'updated_at_before':expected['updated_at'],'updated_at_observed':current['updated_at']}
            columns='id,created_at,updated_at,archived,has_user_event,model_provider,model,reasoning_effort,is_pinned,project_id'
            rows=connection.execute('SELECT '+columns+' FROM threads ORDER BY id LIMIT ?',
                                    (self.selected['metadata_row_bound']+1,)).fetchall()
            require(len(rows)<=self.selected['metadata_row_bound'],'native_metadata_bound','Index metadata inventory exceeds scope.')
            threads={digest(row[0]):digest([*row[:2],None,*row[3:]] if row[0] in self.concurrent else list(row)) for row in rows if row[0] not in self.known}
            counts={name:connection.execute('SELECT COUNT(*) FROM '+name).fetchone()[0]
                    for name in ('projects','project_roots','thread_sections','external_agent_config_imports','remote_control_enrollments')}
            schema=[list(row) for row in connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name")]
        history=self._history_metadata()
        return {'threads':threads,'unselected_table_counts':counts,'schema_sha256':digest(schema),
                'history_file_metadata':history,'concurrent_progress':dict(self.concurrent_progress),
                'level':'metadata-only; no unrelated credential or transcript contents inspected'}

    def freeze_preservation(self):
        require(self.baseline is None,'native_storage_scope','Preservation baseline is immutable.')
        self.baseline=self.preservation_snapshot();self._save('preservation-before.json',self.baseline)
        if self.history_index is not None:
            self.history_baseline=self._history_index_snapshot();self._save('history-index-before.json',self.history_baseline)
            self.history_progress=self.history_baseline['concurrent']
        if self.ambient is not None:self.ambient.freeze()
        return {'sha256':digest(self.baseline),'history_files':len(self.baseline['history_file_metadata']),
                'thread_metadata_rows':len(self.baseline['threads']),
                'history_index_sha256':digest(self.history_baseline) if self.history_baseline is not None else None}

    def check_preservation(self,*,quiescence=None,final=False):
        if self.ambient is not None:return self.ambient.check(quiescence=quiescence,final=final)
        return self._legacy_check_preservation()

    def _legacy_check_preservation(self):
        require(self.baseline is not None,'native_storage_scope','No preservation baseline.')
        current=self.preservation_snapshot()
        stable=lambda value:{k:v for k,v in value.items() if k!='concurrent_progress'}
        require(stable(current)==stable(self.baseline),'native_storage_preservation_unproven','Unlisted metadata changed; preserve evidence and hold further work.')
        result={'state':'unchanged_unlisted_metadata','sha256':digest(stable(current)),
                'concurrent_progress':current['concurrent_progress'],'level':current['level']}
        if self.history_index is not None:
            require(self.history_baseline is not None,'native_history_baseline','History index baseline is unavailable.')
            history=self._history_index_snapshot()
            for key in ('unlisted','schema_sha256','migrations_sha256'):
                require(history[key]==self.history_baseline[key],'native_history_preservation_unproven','Unlisted history metadata or schema/migrations changed.')
            self._check_concurrent_history(self.history_progress,history['concurrent'])
            self.history_progress=history['concurrent']
            result['history_index']={k:v for k,v in history.items() if k!='concurrent'}
            result['history_index']['concurrent_progress']={table:{'frozen_rows':len(self.history_baseline['concurrent'][table]),
                'observed_rows':len(rows),'metadata_sha256':digest(rows)} for table,rows in history['concurrent'].items()}
        self._time();return result

    def _save(self,name,value):
        from curator_policy import canonical
        self._time()
        with parent_descriptor(self.state_root,name) as (parent,leaf):
            fd=os.open(leaf,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            with os.fdopen(fd,'wb') as out:out.write(canonical(value));out.flush();os.fsync(out.fileno())

    def begin_operation(self,kind,operation_id,reservation_id,source_thread_id=None):
        self.assert_admission();require(self.baseline is not None,'native_storage_scope','Freeze preservation before any allocation.')
        require(type(operation_id) is str and operation_id in self.selected['operations'],
                'native_storage_scope','No exact native allocation operation was reviewed.')
        operation=self.selected['operations'][operation_id]
        exact(operation,('kind','reservation_id','source_reservation'))
        require(operation['kind']==kind and operation['reservation_id']==reservation_id and operation_id not in self.pending,
                'native_creation_pending','Repeated or mismatched allocation; reconcile the original attempt.')
        expected=self.slots.get(operation['source_reservation']) if operation['source_reservation'] else None
        require(source_thread_id==expected,'native_storage_scope','Native source differs from the reviewed reserved source.')
        value={'kind':kind,'operation_id':operation_id,'reservation_id':reservation_id,'source_thread_id':source_thread_id,
               'state':'pending','scope_sha256':self.scope_sha256}
        self._save(operation_id+'.json',value);self.pending[operation_id]=value

    def register_native(self,operation_id,reservation_id,thread):
        pending=self.pending.get(operation_id)
        require(pending is not None and pending['reservation_id']==reservation_id,'native_creation_unreserved','Native result lacks its committed pending reservation.')
        actor=thread.get('id');require(type(actor) is str and actor,'native_identity_unproven','Native creation returned no ID.')
        if pending['kind']=='resume':require(self.slots.get(reservation_id)==actor,'native_resume_mismatch','Resume replaced the stored identity.')
        else:require(actor not in self.known and actor not in self.packet.get('seed_selection',{}).get('retained_prior_native_ids',[])
                     and reservation_id not in self.slots,'native_creation_duplicate','Native creation reused an identity or reservation.')
        self.slots[reservation_id]=actor;self.known[actor]={'reservation_id':reservation_id,'operation_id':operation_id}
        self._save(operation_id+'-native.json',{'id':actor,'sessionId':thread.get('sessionId'),
            'parentThreadId':thread.get('parentThreadId'),'forkedFromId':thread.get('forkedFromId'),'path':thread.get('path')})

    def bind_storage(self,actor,thread):
        require(actor in self.known and thread.get('id')==actor,'native_storage_unreserved','Storage observation is not an allocated native ID.')
        supplied=thread.get('path')
        require(type(supplied) is str and supplied,'native_storage_unproven','Actual native response has no stored path.')
        path=Path(supplied)
        require(path.is_absolute() and str(path.resolve(strict=True))==supplied and path.is_relative_to(self.selected['history_root']),
                'native_storage_unproven','Native returned path is outside the reviewed history allocation root or is aliased.')
        relative=str(path.relative_to(self.selected['history_root']))
        require(actor in self.paths or digest(relative) not in self.baseline['history_file_metadata'],
                'native_storage_unowned','A new native ID points to pre-existing history.')
        require(actor not in self.paths or self.paths[actor]==supplied,'native_storage_changed','Known native storage path changed.')
        snapshot=native_header_snapshot(self.selected['history_root'],relative,actor,self.path_identities.get(actor))
        self.paths[actor]=supplied
        self.path_identities[actor]=snapshot
        return {'actor':actor,'path':supplied,**snapshot}

    def require_owned(self,actor):
        require(actor in self.paths,'native_storage_unproven','Native storage ownership has not passed.')
        relative=str(Path(self.paths[actor]).relative_to(self.selected['history_root']))
        self.path_identities[actor]=native_header_snapshot(self.selected['history_root'],relative,actor,self.path_identities[actor])
        self._time();return self.paths[actor]

    def observe_index_metadata(self,actor):
        """Inspect only the exact allocated identity, without transcript fields."""
        owned_path=self.require_owned(actor)
        columns=('id','rollout_path','model_provider','model','reasoning_effort','history_mode','cwd')
        with self._database() as connection:
            row=connection.execute('SELECT '+','.join(columns)+' FROM threads WHERE id=?',(actor,)).fetchone()
        metadata=dict(zip(columns,row)) if row is not None else None
        require(metadata is None or (metadata['id']==actor and metadata['rollout_path']==owned_path),
                'native_index_identity_mismatch','Selected index row points to another native identity or stored path.')
        return {'state':'absent' if metadata is None else 'present','actor':actor,'metadata':metadata,
                'database_identity':dict(self.selected['database_identity']),'query_only':True}

    def require_visibility_review(self,stage):
        self._time();require(stage in self.selected['visibility_reviews'],'native_visibility_unproven','No scoped visibility checkpoint.')
        path=self.root/self.selected['visibility_reviews'][stage]
        require(path.exists(),'native_visibility_pending','Host storage/visibility observation is not available yet.')
        require(path.is_file() and not path.is_symlink(),'native_visibility_unproven','Host visibility receipt is an unsafe file.')
        from curator_policy import decode
        review=decode(path.read_bytes());exact(review,('schema_version','scope_sha256','native_ids','state','observer'))
        require(review['schema_version']==1 and review['scope_sha256']==self.scope_sha256 and review['state']=='passed'
                and review['observer']=='host' and sorted(review['native_ids'])==sorted(self.known),
                'native_visibility_unproven','Host review does not bind the actual allocated IDs and this exact scope.')
        return review


class AmbientMetadataReview:
    """P1-only host accounting of exact external additions, never actor authority."""
    def __init__(self,storage,selection):
        exact(selection,('schema_version','kind','limits','observer','protected_roots',*(('observation_protocol',) if 'observation_protocol' in selection else ())))
        self.observation_protocol=selection.get('observation_protocol',1)
        require(type(self.observation_protocol) is int and self.observation_protocol in (1,2,3),
                'ambient_observation_version','Unsupported selected observation protocol.')
        require(storage.packet.get('stage')=='native-fork-p1' and selection['schema_version']==1
                and selection['kind']=='AmbientMetadataReview' and selection['limits']==AMBIENT_LIMITS
                and selection['observer']=='host' and selection['protected_roots']==[str(storage.root)],
                'ambient_selection','Only the exact opt-in P1 metadata review scope is supported.')
        self.storage=storage;self.selection=copy.deepcopy(selection);self.open=False;self.challenge=None
        self.base=None;self.progress=None;self.chain=[];self.checkpoints=0;self.baseline_refs={};self.failed=False;self.initialized=False
        self.directory=storage.state_root/'ambient';self.directory.mkdir(mode=0o700)

    def assert_admission(self):
        self.storage._time();require(self.initialized and self.open and not self.failed and self.challenge is None,'ambient_admission_closed',
            'Metadata review holds every new model, allocation and owner operation.')

    def _write(self,name,value):
        from curator_policy import canonical
        raw=canonical(value)
        require(len(raw)<=AMBIENT_LIMITS['challenge_or_receipt_bytes'],'ambient_bytes','Ambient evidence exceeds its explicit byte bound.')
        self.storage._save('ambient/'+name,value)
        return file_snapshot(self.storage.state_root,'ambient/'+name,AMBIENT_LIMITS['challenge_or_receipt_bytes'])

    def _read(self,name):
        from curator_policy import decode
        with parent_descriptor(self.storage.state_root,'ambient/'+name) as (parent,leaf):
            try:fd=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
            except FileNotFoundError:raise PolicyError('ambient_receipt_pending','The exact protected host decision has not arrived.')
            except OSError as exc:raise PolicyError('ambient_receipt_unsafe','Unsafe host decision path.') from exc
            with os.fdopen(fd,'rb') as stream:
                before=os.fstat(stream.fileno())
                require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=200000,
                        'ambient_receipt_unsafe','Host decision must be a bounded exclusive regular file.')
                raw=stream.read(200001);after=os.fstat(stream.fileno());current=os.stat(leaf,dir_fd=parent,follow_symlinks=False)
                identity=lambda info:(info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns)
                require(len(raw)<=200000 and identity(before)==identity(after)==identity(current),
                        'ambient_receipt_changed','Host decision changed during its bounded read.')
        return decode(raw),{'device':before.st_dev,'inode':before.st_ino,'sha256':hashlib.sha256(raw).hexdigest(),
                            'size':len(raw),'mode':stat.S_IMODE(before.st_mode)}

    def _snapshot(self):
        s=self.storage;s._time();self.checkpoints+=1
        require(self.checkpoints<=96,'ambient_checkpoints','Metadata checkpoint budget exhausted.')
        s.inspect_backfill()
        with s._database() as db:
            db.execute('BEGIN')
            def rows(table,columns,bound):
                values=db.execute('SELECT '+','.join(columns)+' FROM '+table+' ORDER BY '+','.join(columns)).fetchmany(bound+1)
                require(len(values)<=bound,'ambient_rows','Selected metadata inventory exceeds its row bound.')
                require(all(value is None or type(value) is int or type(value) is str and len(value)<=4096 for row in values for value in row),
                        'ambient_metadata','Unexpected metadata scalar or oversized field.')
                return [dict(zip(columns,row)) for row in values]
            threads={row['id']:row for row in rows('threads',AMBIENT_THREAD_COLUMNS,s.selected['metadata_row_bound']) if row['id'] not in s.known}
            projects={row['id']:row for row in rows('projects',AMBIENT_PROJECT_COLUMNS,10000)}
            roots={digest(row):row for row in rows('project_roots',AMBIENT_ROOT_COLUMNS,10000)}
            counts={table:db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in
                ('projects','project_roots','thread_sections','external_agent_config_imports','remote_control_enrollments')}
            require(counts['projects']==len(projects) and counts['project_roots']==len(roots),'ambient_counts','Metadata row identities do not explain table counts.')
            schema=[list(row) for row in db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name')]
        logs={};history=Path(s.selected['history_root'])
        for directory,dirs,files in os.walk(history,followlinks=False):
            s._time()
            for name in (*dirs,*files):
                path=Path(directory)/name;info=path.lstat()
                require(not stat.S_ISLNK(info.st_mode),'ambient_alias','History aliases are never ambient additions.')
                if stat.S_ISDIR(info.st_mode):continue
                require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'ambient_file_type','History requires ordinary single-link files.')
                if str(path) in s.paths.values():continue
                logs[str(path)]={'path':str(path),'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,
                    'mode':stat.S_IMODE(info.st_mode),'links':info.st_nlink,'size':info.st_size,'mtime_ns':info.st_mtime_ns}
                require(len(logs)<=s.selected['metadata_file_bound'],'ambient_files','History inventory exceeds its file bound.')
        ids=set(threads)-(set(self.base['threads']) if self.base else set(threads))
        h=s._history_index_snapshot(ids) if s.history_index is not None else None
        if h is not None:h.setdefault('external',{table:{} for table in HISTORY_METADATA_COLUMNS})
        return {'threads':threads,'logs':logs,'projects':projects,'roots':roots,'counts':counts,'schema_sha256':digest(schema),'history':h}

    def freeze(self):
        self.base=self._snapshot();self.storage._legacy_check_preservation()
        self.storage._save('ambient-before.json',self.base)
        for name in ('preservation-before.json','history-index-before.json','ambient-before.json'):
            path=self.storage.state_root/name
            if path.exists():self.baseline_refs[name]=file_snapshot(self.storage.state_root,name)
        self.baseline_sha256=digest({name:ref['sha256'] for name,ref in self.baseline_refs.items()})
        self.progress=copy.deepcopy(self.base);self.initialized=True;self.open=True

    @staticmethod
    def _stable_thread(row):return {key:value for key,value in row.items() if key!='updated_at'}
    @staticmethod
    def _stable_log(row):return {key:value for key,value in row.items() if key not in ('size','mtime_ns')}

    def _replay(self):
        for name,ref in self.baseline_refs.items():
            require(file_snapshot(self.storage.state_root,name)==ref,'ambient_baseline_changed','Immutable initial baseline changed.')
        expected=copy.deepcopy(self.base);previous=None
        for number,entry in enumerate(self.chain,1):
            body=entry['body'];ref=entry['file']
            require(file_snapshot(self.storage.state_root,ref['path'])==ref and digest(body)==ref['sha256']
                    and body['batch']==number and body['previous_receipt_sha256']==previous
                    and body['challenge']['baseline_sha256']==self.baseline_sha256,
                    'ambient_chain','Ordered immutable ambient delta chain differs.')
            _,host_identity=self._read('decision-'+str(number).zfill(4)+'.json')
            require(host_identity==body['host_identity'],'ambient_chain','An accepted host decision was replaced.')
            for name in ('threads','logs','projects','roots'):
                additions=body['challenge']['additions'][name]
                require(not set(expected[name])&set(additions),'ambient_chain','An ambient delta overwrites an existing identity.')
                expected[name].update(copy.deepcopy(additions))
            if expected['history'] is not None:
                target=expected['history'].setdefault('external',{table:{} for table in HISTORY_METADATA_COLUMNS})
                for table,rows in (body['challenge']['additions']['history'] or {}).items():
                    require(not set(target[table])&set(rows),'ambient_chain','Ambient history row identity is duplicated.')
                    target[table].update(copy.deepcopy(rows))
            previous=ref['sha256']
        return expected,previous

    def _compare(self,expected,current,growing):
        s=self.storage
        require(current['schema_sha256']==expected['schema_sha256'],'ambient_schema','Selected native schema changed.')
        for name in ('threads','logs','projects','roots'):
            require(set(expected[name])<=set(current[name]),'ambient_removal','Previously recorded metadata disappeared.')
            for key,old in expected[name].items():
                new=current[name][key]
                if name=='threads' and key in growing:
                    require(self._stable_thread(old)==self._stable_thread(new) and type(new['updated_at']) is int
                            and new['updated_at']>=old['updated_at'],'ambient_progress','External thread identity changed or progress regressed.')
                elif name=='logs' and any(row['rollout_path']==key for aid,row in expected['threads'].items() if aid in growing):
                    require(self._stable_log(old)==self._stable_log(new) and new['size']>=old['size'] and new['mtime_ns']>=old['mtime_ns'],
                            'ambient_progress','External log identity changed or progress regressed.')
                else:require(new==old,'ambient_existing_changed','Existing selected metadata changed.')
        if self.observation_protocol==3:
            tracked={aid for aid,value in s.concurrent.items() if value['execution_role']=='unrelated_external_metadata_observation'}
            tracked.update(aid for entry in self.chain for aid in entry['body']['challenge']['native_ids'])
            for aid in tracked:
                row=expected['threads'][aid]
                before=[root for root in expected['roots'].values() if root['path']==row['cwd']]
                after=[root for root in current['roots'].values() if root['path']==row['cwd']]
                require(before==after,'ambient_project_reclassification','Already accounted external cwd associations cannot be reclassified by a later delta.')
        for name in ('thread_sections','external_agent_config_imports','remote_control_enrollments'):
            require(current['counts'][name]==expected['counts'][name],'ambient_unselected_table','Unselected table count changed.')
        if current['history'] is not None:
            for key in ('unlisted','schema_sha256','migrations_sha256'):
                require(current['history'][key]==self.base['history'][key],'ambient_history_changed','Unexplained history metadata changed.')
            s._check_concurrent_history(expected['history']['concurrent'],current['history']['concurrent'])
            before=expected['history'].get('external',{table:{} for table in HISTORY_METADATA_COLUMNS})
            after={table:{key:row for key,row in current['history']['external'][table].items() if row['thread_id'] in growing} for table in HISTORY_METADATA_COLUMNS}
            s._check_concurrent_history(before,after)

    @staticmethod
    def quiescent(value,inventory=None):
        exact(value,('admission_closed','actors','pending_callbacks','pending_requests','pending_owner_operations','pending_releases','proof_native_ids','operation_ledger_sha256'))
        require(value['admission_closed'] is True and all(type(value[key]) is int and value[key]==0 for key in
            ('pending_callbacks','pending_requests','pending_owner_operations','pending_releases')),'ambient_not_quiescent','Pending native/callback/owner/release work cannot enter a review hold.')
        require(type(value['actors']) is list and type(value['proof_native_ids']) is list
                and all(type(aid) is str and aid for aid in value['proof_native_ids']),'ambient_not_quiescent','Missing complete owned actor inventory.')
        inventory=inventory or {};seen=set()
        for actor in value['actors']:
            exact(actor,('native_id','connection_id','load_epoch','state','evidence_sha256','binding_sha256'))
            require(type(actor['connection_id']) is str and type(actor['native_id']) is str,
                    'ambient_not_quiescent','Malformed runtime identity in quiescence evidence.')
            bound=inventory.get(actor['connection_id'])
            require(actor['state'] in ('completed','failed','interrupted','no_turn_idle','released')
                    and actor['native_id'] in value['proof_native_ids'] and actor['connection_id'] not in seen
                    and bound is not None and actor['native_id']==bound['thread_id'] and actor['load_epoch']==bound['load_epoch']
                    and actor['binding_sha256']==digest(bound)
                    and type(actor['evidence_sha256']) is str and len(actor['evidence_sha256'])==64,
                    'ambient_not_quiescent','Every owned actor needs a unique observed terminal or released identity.')
            seen.add(actor['connection_id'])
        require(seen==set(inventory) and len(value['proof_native_ids'])==len(set(value['proof_native_ids']))
                and set(value['proof_native_ids'])=={actor['native_id'] for actor in value['actors']},
                'ambient_not_quiescent','Quiescence must cover every exact owned runtime incarnation, including released epochs.')
        return value

    def _additions(self,expected,current,proof_ids):
        s=self.storage;new={name:{key:value for key,value in current[name].items() if key not in expected[name]} for name in ('threads','logs','projects','roots')}
        ids=set(new['threads']);all_external=set(current['threads'])-set(self.base['threads'])
        excluded=set(s.known)|set(s.concurrent)|set(proof_ids)|set(s.packet.get('seed_selection',{}).get('retained_prior_native_ids',[]))
        require(0<len(ids)<=2 and len(all_external)<=8 and not ids&excluded,'ambient_external_scope','Only bounded new independently external identities may be reviewed.')
        require(len(new['logs'])==len(ids) and set(new['logs'])=={row['rollout_path'] for row in new['threads'].values()},
                'ambient_log_attribution','Every new log must be attributed to exactly one new external thread.')
        require(len(current['projects'])-len(self.base['projects'])<=4 and len(current['roots'])-len(self.base['roots'])<=8,
                'ambient_project_bound','Ambient native project/root addition limit reached.')
        cwd_paths=set()
        for aid,row in new['threads'].items():
            exact(row,AMBIENT_THREAD_COLUMNS);require(type(aid) is str and 0<len(aid)<=300 and row['id']==aid and row['archived']==0
                and type(row['rollout_path']) is str and type(row['cwd']) is str,'ambient_external_scope','Archived, malformed or mismatched external identity.')
            path=Path(row['rollout_path']);cwd=Path(row['cwd'])
            require(path.is_absolute() and str(path.resolve(strict=True))==str(path) and path.is_relative_to(s.selected['history_root'])
                    and cwd.is_absolute() and str(canonical_root(cwd))==str(cwd)
                    and not any(cwd.is_relative_to(root) or path.is_relative_to(root) for root in self.selection['protected_roots']),
                    'ambient_external_path','External metadata cannot claim protected proof paths or aliases.')
            with parent_descriptor('/',str(path).lstrip('/')):pass
            with parent_descriptor('/',str(cwd).lstrip('/')):pass
            cwd_paths.add(str(cwd))
            if self.observation_protocol==3:self._project_binding(row,current)
            else:
                roots=[root for root in current['roots'].values() if root['path']==str(cwd)]
                require(len(roots)==1 and roots[0]['project_id'] in current['projects']
                        and row['project_id'] in (None,roots[0]['project_id']),'ambient_project_identity','No unique exact native project-root association.')
        for row in new['projects'].values():
            exact(row,AMBIENT_PROJECT_COLUMNS)
            require(type(row['id']) is str and row['id'] and all(type(row[key]) is int and row[key]>=0 for key in AMBIENT_PROJECT_COLUMNS[1:]),
                    'ambient_project_metadata','Unsupported native project metadata values.')
            require(any(root['project_id']==row['id'] and root['path'] in cwd_paths for root in new['roots'].values()),
                    'ambient_project_unselected','New native project is unrelated to the reviewed external tasks.')
        for row in new['roots'].values():
            exact(row,AMBIENT_ROOT_COLUMNS)
            require(type(row['position']) is int and row['position']>=0 and row['path'] in cwd_paths and row['project_id'] in current['projects'],
                    'ambient_project_unselected','Unselected project-root addition.')
        new['history']={table:{key:row for key,row in current['history']['external'][table].items() if row['thread_id'] in ids}
            for table in HISTORY_METADATA_COLUMNS} if current['history'] is not None else None
        return new

    def check(self,*,quiescence=None,final=False):
        try:return self._check(quiescence=quiescence,final=final)
        except PolicyError as exc:
            self.open=False
            if final or exc.code not in ('ambient_review_required','ambient_receipt_pending'):self.failed=True
            raise

    def _check(self,*,quiescence=None,final=False):
        self.open=False;s=self.storage;s._time()
        require(self.initialized,'ambient_initialization_incomplete','Immutable ambient baseline capture did not complete; preservation is unproven.')
        require(not self.failed,'ambient_failed','A rejected accounting run cannot reopen admission.')
        require(self.challenge is None,'ambient_receipt_pending','The pending exact host decision must be resolved first.')
        expected,previous=self._replay();current=self._snapshot()
        growing=set(s.concurrent)|(set(expected['threads'])-set(self.base['threads']))
        self._compare(self.progress,current,growing)
        changed=any(set(current[name])!=set(expected[name]) for name in ('threads','logs','projects','roots'))
        if not changed:
            self.progress=current;self.open=True
            return {'state':'unchanged_unlisted_metadata','initial_baseline_sha256':self.baseline_sha256,
                'ambient_receipts':len(self.chain),'last_receipt_sha256':previous,'checkpoints':self.checkpoints,
                'sha256':digest(current),'level':'exact selected metadata; baseline plus ordered host-reviewed additions'}
        require(not final and len(self.chain)<4,'ambient_final_or_batch_bound','Unknown final changes or exhausted review batches cannot be accepted.')
        witness=self.quiescent(quiescence() if callable(quiescence) else quiescence,s.runtime_inventory)
        require(witness['operation_ledger_sha256']==digest(s.pending) and set(s.known)<=set(witness['proof_native_ids']),
                'ambient_not_quiescent','Quiescence does not cover the current proof allocation ledger.')
        additions=self._additions(expected,current,witness['proof_native_ids'])
        challenge={'schema_version':1,'kind':'AmbientMetadataChallenge','scope_sha256':s.scope_sha256,
            'baseline_sha256':self.baseline_sha256,'previous_receipt_sha256':previous,'batch':len(self.chain)+1,
            'checkpoint':self.checkpoints,'native_ids':sorted(additions['threads']),'additions':additions,'quiescence':witness}
        if self.observation_protocol in (2,3):challenge['observation_protocol']=self.observation_protocol
        ref=self._write('challenge-'+str(challenge['batch']).zfill(4)+'.json',challenge)
        self.challenge={'value':challenge,'file':ref,'snapshot':current}
        raise PolicyError('ambient_review_required','New exact external metadata awaits a protected host decision with admission closed.')

    def decision_path(self):
        require(self.challenge is not None,'ambient_no_challenge','No current ambient challenge.')
        return self.directory/('decision-'+str(self.challenge['value']['batch']).zfill(4)+'.json')

    def adopt(self,*,quiescence):
        try:return self._adopt(quiescence=quiescence)
        except PolicyError as exc:
            self.open=False
            if exc.code!='ambient_receipt_pending':self.failed=True
            raise

    def _adopt(self,*,quiescence):
        require(not self.failed,'ambient_failed','A rejected accounting run cannot adopt another receipt.')
        require(not self.open and self.challenge is not None,'ambient_no_challenge','No closed pending ambient review.')
        s=self.storage;s._time();challenge=self.challenge['value'];current_ref=self.challenge['file']
        decision,identity=self._read(self.decision_path().name)
        require(file_snapshot(s.state_root,current_ref['path'],200000)==current_ref,'ambient_challenge_changed','The immutable challenge was replaced.')
        expected,previous=self._replay()
        exact(decision,('schema_version','kind','observer','decision','scope_sha256','baseline_sha256','previous_receipt_sha256',
            'batch','challenge_sha256','native_ids','additions_sha256','observations',*(('observation_protocol',) if self.observation_protocol in (2,3) else ())))
        require(decision.get('observation_protocol',1)==self.observation_protocol,'ambient_observation_version','Decision observation protocol differs from the selected scope.')
        require(decision['schema_version']==1 and decision['kind']=='AmbientMetadataDecision' and decision['observer']=='host'
                and all(decision[key]==challenge[key] for key in ('scope_sha256','baseline_sha256','previous_receipt_sha256','batch','native_ids'))
                and decision['previous_receipt_sha256']==previous and decision['challenge_sha256']==current_ref['sha256']
                and decision['additions_sha256']==digest(challenge['additions']),'ambient_decision_binding','Host decision does not bind the exact current ordered challenge.')
        require(decision['decision']=='accept','ambient_review_rejected','Host did not accept this exact external metadata delta.')
        observations=decision['observations'];require(type(observations) is list and len(observations)==len(challenge['native_ids']),
            'ambient_independent_observation','Every external ID needs independent app and native metadata observations.')
        if self.observation_protocol in (2,3):self._observations_v2(observations,challenge)
        seen=set()
        for observed in observations if self.observation_protocol==1 else ():
            exact(observed,('native_id','app','native'))
            aid=observed['native_id'];require(aid in challenge['native_ids'] and aid not in seen,'ambient_independent_observation','Missing or repeated external observation.');seen.add(aid)
            app=observed['app'];record=observed['native'];exact(app,('source','record_id','task_id','native_id','project_id'))
            exact(record,('source','record_id','native_id','project_id','thread_stable_sha256','log_stable_sha256','history_challenge_sha256'))
            row=challenge['additions']['threads'][aid];log=challenge['additions']['logs'][row['rollout_path']]
            roots=[root for root in self.challenge['snapshot']['roots'].values() if root['path']==row['cwd']]
            require(app['source']=='codex_app.list_threads' and record['source']=='readonly_selected_metadata' and app['native_id']==record['native_id']==aid
                    and all(type(value) is str and 0<len(value)<=300 for value in (app['record_id'],app['task_id'],record['record_id']))
                    and (app['project_id'] is None or type(app['project_id']) is str and 0<len(app['project_id'])<=300)
                    and record['project_id']==roots[0]['project_id'] and record['thread_stable_sha256']==digest(self._stable_thread(row))
                    and record['log_stable_sha256']==digest(self._stable_log(log))
                    and record['history_challenge_sha256']==digest({table:{key:value for key,value in rows.items() if value['thread_id']==aid}
                        for table,rows in (challenge['additions']['history'] or {}).items()}),
                    'ambient_independent_observation','Independent app/native sources do not establish this exact external metadata selection.')
        witness=self.quiescent(quiescence() if callable(quiescence) else quiescence,s.runtime_inventory)
        require(witness['operation_ledger_sha256']==digest(s.pending) and set(s.known)<=set(witness['proof_native_ids']),
                'ambient_not_quiescent','Proof ownership changed during the review hold.')
        current=self._snapshot();all_growing=set(s.concurrent)|(set(current['threads'])-set(self.base['threads']))
        self._compare(self.challenge['snapshot'],current,all_growing)
        require(all(set(current[name])==set(self.challenge['snapshot'][name]) for name in ('threads','logs','projects','roots')),
                'ambient_additional_change','Additional unlisted metadata appeared before adoption.')
        _,current_identity=self._read(self.decision_path().name)
        require(current_identity==identity,'ambient_receipt_changed','Host decision changed before delta publication.')
        body={'schema_version':1,'batch':challenge['batch'],'previous_receipt_sha256':previous,'challenge':challenge,
            'host_decision':decision,'host_identity':identity,'adopted_metadata_sha256':digest(current)}
        ref=self._write('accepted-'+str(challenge['batch']).zfill(4)+'.json',body)
        self.chain.append({'body':body,'file':ref});self.progress=current;self.challenge=None;self.open=True
        return {'state':'ambient_delta_accepted','batch':body['batch'],'receipt_sha256':ref['sha256'],
            'external_native_ids':decision['native_ids'],'proof_membership_changed':False,'writer_causation_proven':False}

    @staticmethod
    def _native_uuid(value):
        import uuid
        require(type(value) is str,'ambient_external_identity','Expected a canonical native UUID.')
        try:valid=str(uuid.UUID(value))==value
        except ValueError:valid=False
        require(valid,'ambient_external_identity','Expected a canonical native UUID.')
        return value

    def _project_binding(self,row,snapshot):
        require(type(snapshot.get('roots')) is dict and type(snapshot.get('projects')) is dict and 'project_id' in row,
                'ambient_project_unavailable','Complete selected project/root metadata and explicit native project ID are required.')
        roots=[root for root in snapshot['roots'].values() if root['path']==row['cwd']]
        if self.observation_protocol==3 and roots==[]:
            require(row['project_id'] is None,'ambient_project_identity','A projectless native identity must explicitly have null project ID.')
            return None,{'kind':'projectless','exact_cwd_roots_sha256':digest([])}
        require(len(roots)==1 and roots[0]['project_id'] in snapshot['projects'] and row['project_id'] in (None,roots[0]['project_id']),
                'ambient_project_identity','No unique exact native project-root association.')
        return roots[0]['project_id'],{'kind':'linked','exact_cwd_roots_sha256':digest(roots)}

    def _external_identity(self,aid,snapshot):
        self._native_uuid(aid);s=self.storage
        excluded=set(s.known)|set(s.packet.get('seed_selection',{}).get('retained_prior_native_ids',[]))
        excluded|={key for key,value in s.concurrent.items() if value['execution_role']!='unrelated_external_metadata_observation'}
        require(aid not in excluded and aid in snapshot['threads'],'ambient_external_identity','Own, proof, retained or unavailable identities cannot be external parent or child.')
        row=snapshot['threads'][aid];log=snapshot['logs'].get(row['rollout_path']);cwd=Path(row['cwd'])
        require(row['archived']==0 and cwd.is_absolute() and str(cwd.resolve(strict=True))==str(cwd) and log is not None,
                'ambient_external_identity','External identity is archived, relocated, aliased or missing its log.')
        protected=[Path(path) for path in self.selection['protected_roots']]
        require(not any(cwd.is_relative_to(path) or Path(log['path']).is_relative_to(path) for path in protected)
                and log['path'] not in s.paths.values(),'ambient_external_identity','Protected proof paths are not external metadata.')
        if self.observation_protocol==3:
            project,_=self._project_binding(row,snapshot);return row,log,project
        roots=[root for root in snapshot['roots'].values() if root['path']==str(cwd)]
        require(len(roots)==1 and roots[0]['project_id'] in snapshot['projects']
                and row['project_id'] in (None,roots[0]['project_id']),'ambient_external_identity','External identity has no unique selected local project-root association.')
        return row,log,roots[0]['project_id']

    def _app_observation(self,app,aid):
        exact(app,('source','record_id','task_id','native_id','project_id','challenge_sha256'))
        require(app['source']=='codex_app.list_threads' and app['native_id']==aid
                and all(type(app[key]) is str and 0<len(app[key])<=300 for key in ('record_id','task_id'))
                and (app['project_id'] is None or type(app['project_id']) is str and 0<len(app['project_id'])<=300)
                and app['challenge_sha256']==digest(self.challenge['value']),
                'ambient_independent_observation','The exact external identity needs an independent current app observation.')

    def _metadata_observation(self,record,aid,snapshot,history=None):
        keys=('source','record_id','native_id','project_id','thread_stable_sha256','log_stable_sha256','challenge_sha256')
        exact(record,(*keys,*(('history_challenge_sha256',) if history is not None else ()),
            *(('project_binding',) if self.observation_protocol==3 else ())))
        row,log,project=self._external_identity(aid,snapshot)
        if self.observation_protocol==3:
            exact(record['project_binding'],('kind','exact_cwd_roots_sha256'))
            require(record['project_binding']==self._project_binding(row,snapshot)[1],
                    'ambient_project_binding','The explicit project class and exact cwd root evidence do not match.')
        require(record['source']=='readonly_selected_metadata' and record['native_id']==aid
                and type(record['record_id']) is str and 0<len(record['record_id'])<=300 and record['project_id']==project
                and record['thread_stable_sha256']==digest(self._stable_thread(row))
                and record['log_stable_sha256']==digest(self._stable_log(log))
                and record['challenge_sha256']==digest(self.challenge['value']),
                'ambient_independent_observation','Independent metadata does not bind the exact external identity.')
        if history is not None:
            require(record['history_challenge_sha256']==digest({table:{key:value for key,value in rows.items() if value['thread_id']==aid}
                for table,rows in history.items()}),'ambient_independent_observation','Child/task history metadata differs from the exact challenge.')
        return row

    def _observations_v2(self,observations,challenge):
        from curator_policy import decode
        snapshot=self.challenge['snapshot'];history=challenge['additions']['history'] or {};seen=set();direct={}
        for observed in observations:
            require(type(observed) is dict and type(observed.get('kind')) is str and observed['kind'] in ('direct_task','direct_child'),
                    'ambient_observation_kind','Select exactly one closed direct-task or direct-child observation.')
            fields=('kind','native_id','app','native') if observed['kind']=='direct_task' else (
                'kind','child_native_id','parent_native_id','app_parent','child','parent','source_sha256')
            exact(observed,fields);aid=self._native_uuid(observed['native_id'] if observed['kind']=='direct_task' else observed['child_native_id'])
            require(aid in challenge['native_ids'] and aid not in seen,'ambient_independent_observation','Missing, swapped or duplicate added identity.')
            seen.add(aid)
            if observed['kind']=='direct_task':
                self._app_observation(observed['app'],aid);self._metadata_observation(observed['native'],aid,snapshot,history)
                if self.observation_protocol==3 and observed['native']['project_binding']['kind']=='projectless':
                    require(observed['app']['project_id'] is None,'ambient_project_binding','Projectless native and independently observed app project IDs must both be null.')
                direct[aid]=observed
        require(seen==set(challenge['native_ids']),'ambient_independent_observation','Each added identity requires its own observation.')
        eligible={aid for aid,row in self.storage.concurrent.items() if row['execution_role']=='unrelated_external_metadata_observation'}|set(direct)
        for entry in self.chain:
            eligible.update(row['native_id'] for row in entry['body']['host_decision']['observations'] if row.get('kind','direct_task')=='direct_task')
        for observed in observations:
            if observed['kind']!='direct_child':continue
            child=self._native_uuid(observed['child_native_id']);parent=self._native_uuid(observed['parent_native_id'])
            require(parent!=child and parent in eligible,'ambient_external_parent','The direct parent is not an explicitly reviewed external task.')
            self._app_observation(observed['app_parent'],parent)
            child_row=self._metadata_observation(observed['child'],child,snapshot,history)
            parent_row=self._metadata_observation(observed['parent'],parent,snapshot)
            require(child_row['cwd']==parent_row['cwd'],'ambient_external_parent','Child and parent local project roots differ.')
            if self.observation_protocol==3:
                require(observed['child']['project_binding']==observed['parent']['project_binding'],
                        'ambient_project_binding','Child and parent must have the same exact project class and cwd roots.')
                if observed['parent']['project_binding']['kind']=='projectless':
                    require(observed['app_parent']['project_id'] is None,'ambient_project_binding','Projectless parent app observation must explicitly have null project ID.')
            source=child_row['source'];require(type(source) is str,'ambient_source_edge','Unsupported stored source variant.')
            value=decode(source.encode());exact(value,('subagent',));exact(value['subagent'],('thread_spawn',));edge=value['subagent']['thread_spawn']
            exact(edge,('parent_thread_id','depth','agent_path','agent_nickname','agent_role'))
            require(self._native_uuid(edge['parent_thread_id'])==parent and type(edge['depth']) is int and edge['depth']>0
                    and all(edge[key] is None or type(edge[key]) is str for key in ('agent_path','agent_nickname','agent_role'))
                    and observed['source_sha256']==hashlib.sha256(source.encode()).hexdigest(),
                    'ambient_source_edge','The exact stored one-hop child-to-parent edge is not established.')
