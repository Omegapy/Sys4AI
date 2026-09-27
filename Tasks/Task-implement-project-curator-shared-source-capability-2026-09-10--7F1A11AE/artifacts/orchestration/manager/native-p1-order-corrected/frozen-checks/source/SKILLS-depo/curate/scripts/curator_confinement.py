"""Resolved file identities and proof admission. A manifest is not OS proof."""
from contextlib import contextmanager
import hashlib
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
            *(('history_index',) if 'history_index' in selected else ())))
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
        self.pending={};self.known={};self.slots={};self.paths={};self.path_identities={};self.baseline=None
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

    def _history_index_snapshot(self):
        self._time();self._validate_roots();selected=self.history_index
        deadline=min(self.deadline,time.monotonic()+selected['scan_seconds'])
        connection=sqlite3.connect('file:'+quote(selected['path'])+'?mode=ro',uri=True,timeout=min(2,max(.001,deadline-time.monotonic())))
        started=time.monotonic();total=0;unlisted={};concurrent={};owned={}
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
                hasher=hashlib.sha256();count=0;concurrent[table]={};owned[table]={}
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
                    elif actor in self.concurrent:
                        key=digest([value[k] for k in HISTORY_METADATA_KEYS[table]])
                        require(key not in concurrent[table],'native_history_identity','Repeated concurrent history row identity.')
                        concurrent[table][key]=value
                    else:hasher.update(raw);count+=1
                unlisted[table]={'count':count,'metadata_sha256':hasher.hexdigest()}
                for entry in owned[table].values():entry['metadata_sha256']=entry.pop('_hasher').hexdigest()
            check()
            return {'unlisted':unlisted,'concurrent':concurrent,'owned':owned,'total_rows':total,
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
        return {'sha256':digest(self.baseline),'history_files':len(self.baseline['history_file_metadata']),
                'thread_metadata_rows':len(self.baseline['threads']),
                'history_index_sha256':digest(self.history_baseline) if self.history_baseline is not None else None}

    def check_preservation(self):
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
        self._time();path=self.state_root/name
        with path.open('xb') as out:out.write(canonical(value));out.flush();os.fsync(out.fileno())

    def begin_operation(self,kind,operation_id,reservation_id,source_thread_id=None):
        self._time();require(self.baseline is not None,'native_storage_scope','Freeze preservation before any allocation.')
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
        snapshot=file_snapshot(self.selected['history_root'],relative,2000000)
        with parent_descriptor(self.selected['history_root'],relative) as (parent,name):
            descriptor=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
            with os.fdopen(descriptor,'rb') as source:
                info=os.fstat(source.fileno())
                require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=2000000
                        and (info.st_dev,info.st_ino)==(snapshot['device'],snapshot['inode']),
                        'native_storage_changed','Stored native identity changed before its header read.')
                first=source.readline(2000001)
        try:metadata=json.loads(first)
        except (ValueError,RecursionError) as exc:raise PolicyError('native_storage_unproven','Stored native metadata is not a recognized bounded record.') from exc
        require(type(metadata) is dict and metadata.get('type')=='session_meta' and type(metadata.get('payload')) is dict and metadata['payload'].get('id')==actor,
                'native_storage_unproven','Returned storage does not identify the actual allocated native actor.')
        require(actor not in self.paths or self.paths[actor]==supplied,'native_storage_changed','Known native storage path changed.')
        self.paths[actor]=supplied
        self.path_identities[actor]={'device':snapshot['device'],'inode':snapshot['inode']}
        return {'actor':actor,'path':supplied,**snapshot}

    def require_owned(self,actor):
        require(actor in self.paths,'native_storage_unproven','Native storage ownership has not passed.')
        info=Path(self.paths[actor]).lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and
                {'device':info.st_dev,'inode':info.st_ino}==self.path_identities[actor],
                'native_storage_changed','Allocated native storage identity changed.')
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
