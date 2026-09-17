from pathlib import Path
import os
import hashlib
import stat
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from curator_confinement import file_snapshot, source_manifest, verify_manifest, proof_gate, CHANNELS
from curator_policy import PolicyError
import json
import sqlite3
import time
from datetime import datetime,timedelta,timezone
from curator_policy import digest
from curator_confinement import NativeStorageAdmission


class ConfinementTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'file').write_bytes(b'fixed')

    def test_frozen_source_change_and_replacement_are_rejected(self):
        manifest=source_manifest(self.root,['file'])
        self.assertEqual(verify_manifest(manifest),manifest)
        (self.root/'file').write_bytes(b'changed')
        with self.assertRaises(PolicyError):verify_manifest(manifest)

    def test_symlink_hardlink_directory_alias_and_case_are_rejected(self):
        (self.root/'link').symlink_to(self.root/'file')
        with self.assertRaises((PolicyError,OSError)):file_snapshot(self.root,'link')
        os.link(self.root/'file',self.root/'hard')
        with self.assertRaises(PolicyError):file_snapshot(self.root,'hard')
        with self.assertRaises((PolicyError,OSError)):file_snapshot(self.root,'FILE')
        with self.assertRaises(PolicyError):file_snapshot(self.root,'../outside')

    def test_os_evidence_is_not_inferred_from_manifest(self):
        manifest=source_manifest(self.root,['file'])
        (self.root/'candidate').mkdir();(self.root/'private').mkdir()
        profile={'schema_version':1,'name':'fixture','read_roots':[],
            'write_roots':[str(self.root/'candidate')],'denied_roots':[str(self.root/'private')],
            'executables':[],'channels':{k:'disabled' for k in CHANNELS},'network':[],'config_sha256':'0'*64}
        with self.assertRaises(PolicyError):proof_gate(profile,manifest,{},{
            'state':'not_run','profile_sha256':'0'*64,'manifest_sha256':'0'*64,
            'runtime':{},'channels':{k:'observed_disabled' for k in CHANNELS},'cases':{}})



    def test_fifo_cannot_block_snapshot_before_type_check(self):
        import subprocess
        os.mkfifo(self.root/'fifo')
        code="import sys;sys.path.insert(0,sys.argv[1]);from curator_confinement import file_snapshot;from curator_policy import PolicyError;\ntry:file_snapshot(sys.argv[2],'fifo')\nexcept PolicyError:sys.exit(3)"
        result=subprocess.run([sys.executable,'-B','-c',code,str(Path(__file__).resolve().parents[1]/'scripts'),str(self.root)],
                              capture_output=True,text=True,timeout=3)
        self.assertEqual(result.returncode,3,result.stderr)

class NativeStorageTests(unittest.TestCase):
    """Real disposable SQLite/file metadata; no native runtime or transcript read."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();home=self.root/'established';history=home/'sessions';history.mkdir(parents=True)
        (self.root/'trusted/native-storage').mkdir(parents=True)
        self.log=history/'concurrent.jsonl';self.log.write_bytes(b'x'*100)
        self.other=history/'unlisted.jsonl';self.other.write_bytes(b'private-content-not-read')
        self.database=home/'state_5.sqlite'
        self.columns=('id','created_at','updated_at','archived','has_user_event','model_provider','model','reasoning_effort','is_pinned','project_id','rollout_path','source','history_mode','cwd')
        self.row={'id':'host-native','created_at':1,'updated_at':2,'archived':0,'has_user_event':0,'model_provider':'openai',
            'model':'gpt-6-astra','reasoning_effort':'xhigh','is_pinned':0,'project_id':None,'rollout_path':str(self.log),'source':'synthetic','history_mode':'paginated','cwd':str(self.root)}
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE TABLE backfill_state (id INTEGER,status TEXT)');db.execute("INSERT INTO backfill_state VALUES (1,'complete')")
            db.execute('CREATE TABLE threads ('+','.join(name+(' TEXT' if name in ('id','model_provider','model','reasoning_effort','project_id','rollout_path','source','history_mode','cwd') else ' INTEGER') for name in self.columns)+')')
            db.execute('INSERT INTO threads VALUES ('+','.join('?' for _ in self.columns)+')',[self.row[k] for k in self.columns])
            for table in ('projects','project_roots','thread_sections','external_agent_config_imports','remote_control_enrollments'):
                db.execute('CREATE TABLE '+table+' (id INTEGER)')
        info=self.log.stat();concurrent={'execution_role':'host','index_metadata':self.row,'native_parent_id':None,
            'log_identity':{'path':str(self.log),'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,
                'mode':info.st_mode&0o777,'links':info.st_nlink,'size':info.st_size,'mtime_ns':info.st_mtime_ns}}
        receipt=self.root/'concurrent.json';receipt.write_text(json.dumps({'kind':'host_active_execution_native_metadata','rows':[concurrent]}))
        reference={'path':str(receipt),'sha256':file_snapshot(self.root,'concurrent.json')['sha256']}
        identity=lambda path:{'device':path.stat().st_dev,'inode':path.stat().st_ino}
        storage={'schema_version':1,'kind':'EstablishedRuntimeOwnedRecords','runtime_home':str(home),'sqlite_home':str(home),
            'database_path':str(self.database),'history_root':str(history),'database_identity':identity(self.database),
            'history_identity':identity(history),'metadata_file_bound':100,'metadata_row_bound':100,
            'operations':{'seed-create':{'kind':'seed','reservation_id':'seed','source_reservation':None}},
            'visibility_reviews':{'seed':'trusted/native-storage/seed-review.json'},'backfill_receipt':reference,
            'backfill_source_receipt':reference,'schema_receipt':reference,'concurrent_receipt':reference,'concurrent_threads':[concurrent]}
        self.packet={'root':str(self.root),'expires_at':(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),'storage':storage}
        self.admission=NativeStorageAdmission(self.packet,digest(self.packet),deadline=time.monotonic()+10)

    def test_concurrent_growth_is_attributed_and_unlisted_changes_still_hold(self):
        self.admission.freeze_preservation()
        self.log.write_bytes(b'x'*110)
        with sqlite3.connect(self.database) as db:db.execute('UPDATE threads SET updated_at=3 WHERE id=?',('host-native',))
        result=self.admission.check_preservation()
        self.assertEqual(result['state'],'unchanged_unlisted_metadata')
        self.assertEqual(result['concurrent_progress']['host-native']['size_observed'],110)
        self.other.write_bytes(b'changed-unlisted-content')
        with self.assertRaises(PolicyError):self.admission.check_preservation()

    def test_concurrent_size_cannot_regress_below_actual_frozen_baseline(self):
        self.log.write_bytes(b'x'*200);self.admission.freeze_preservation()
        self.log.write_bytes(b'x'*150)
        with self.assertRaises(PolicyError) as error:self.admission.check_preservation()
        self.assertEqual(error.exception.code,'native_concurrent_identity_changed')

    def test_backfill_or_stable_settings_change_blocks_without_index_mutation(self):
        self.admission.freeze_preservation()
        with sqlite3.connect(self.database) as db:db.execute("UPDATE threads SET model='other-model'")
        with self.assertRaises(PolicyError):self.admission.check_preservation()
        with sqlite3.connect(self.database) as db:
            db.execute("UPDATE threads SET model='gpt-6-astra'");db.execute("UPDATE backfill_state SET status='pending'")
        with self.assertRaises(PolicyError) as error:self.admission.inspect_backfill()
        self.assertEqual(error.exception.code,'native_backfill_unproven')
        with sqlite3.connect(self.database) as db:self.assertEqual(db.execute('SELECT status FROM backfill_state').fetchone()[0],'pending')

    def test_allocation_is_single_attempt_and_visibility_failure_is_not_pending(self):
        self.admission.freeze_preservation();self.admission.begin_operation('seed','seed-create','seed')
        with self.assertRaises(PolicyError):self.admission.begin_operation('seed','seed-create','seed')
        with self.assertRaises(PolicyError) as pending:self.admission.require_visibility_review('seed')
        self.assertEqual(pending.exception.code,'native_visibility_pending')
        path=self.root/'trusted/native-storage/seed-review.json'
        path.write_text(json.dumps({'schema_version':1,'scope_sha256':digest(self.packet),'native_ids':[],'state':'failed','observer':'host'}))
        with self.assertRaises(PolicyError) as failed:self.admission.require_visibility_review('seed')
        self.assertEqual(failed.exception.code,'native_visibility_unproven')

    def test_final_storage_mismatch_or_unavailable_observation_vetoes_pass(self):
        import importlib.util
        path=Path(__file__).resolve().parents[3]/'Verification/project-curator-release/run-native-proof.py'
        spec=importlib.util.spec_from_file_location('p0_final_storage_fixture',path)
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        self.admission.freeze_preservation();self.admission.check_preservation()
        self.other.write_bytes(b'changed-after-pre-stop-check')
        result={'state':'passed_p0_only','storage':{}}
        runner.finalize_p0_storage(result,self.admission)
        self.assertEqual(result['code'],'final_native_storage_unproven')
        self.assertEqual(result['storage']['final_preservation']['code'],'native_storage_preservation_unproven')
        self.admission.deadline=time.monotonic()-1
        result={'state':'passed_p0_only','storage':{}}
        runner.finalize_p0_storage(result,self.admission)
        self.assertEqual(result['state'],'blocked')
        self.assertEqual(result['storage']['final_preservation']['code'],'native_deadline')

    def test_owned_index_absence_and_postuser_metadata_require_exact_selected_row(self):
        from curator_runtime_codex import ForkCodexAdapter
        self.admission.freeze_preservation();self.admission.begin_operation('seed','seed-create','seed')
        path=Path(self.packet['storage']['history_root'])/'owned-seed.jsonl'
        path.write_text(json.dumps({'type':'session_meta','payload':{'id':'seed-native'}})+'\n')
        thread={'id':'seed-native','path':str(path),'modelProvider':'openai','model':'gpt-6-astra','reasoningEffort':'xhigh'}
        self.admission.register_native('seed-create','seed',thread);self.admission.bind_storage('seed-native',thread)
        self.assertEqual(self.admission.observe_index_metadata('seed-native')['state'],'absent')
        a=object.__new__(ForkCodexAdapter);a.actor_binding={'thread_id':'seed-native'};a.threads={'seed-native':thread}
        a.storage_admission=self.admission;a.cwd=str(self.root)
        with self.assertRaises(PolicyError):a.require_paginated_metadata()
        row={**self.row,'id':'seed-native','rollout_path':str(path)}
        with sqlite3.connect(self.database) as db:
            db.execute('INSERT INTO threads VALUES ('+','.join('?' for _ in self.columns)+')',[row[k] for k in self.columns])
        self.assertEqual(a.require_paginated_metadata()['metadata']['history_mode'],'paginated')
        for field,value in (('history_mode','legacy'),('model_provider','foreign-provider'),('rollout_path',str(self.other))):
            with sqlite3.connect(self.database) as db:db.execute('UPDATE threads SET '+field+'=? WHERE id=?',(value,'seed-native'))
            with self.subTest(field=field),self.assertRaises(PolicyError):a.require_paginated_metadata()
            with sqlite3.connect(self.database) as db:db.execute('UPDATE threads SET '+field+'=? WHERE id=?',(row[field],'seed-native'))
        before=self.database.read_bytes();self.admission.observe_index_metadata('seed-native');self.assertEqual(self.database.read_bytes(),before)

    def test_large_owned_log_uses_header_only_and_keeps_prior_inode_and_header(self):
        from unittest.mock import patch
        self.admission.freeze_preservation();self.admission.begin_operation('seed','seed-create','seed')
        path=Path(self.packet['storage']['history_root'])/'large-owned.jsonl'
        header=json.dumps({'type':'session_meta','payload':{'id':'seed-native'}}).encode()+b'\n'
        path.write_bytes(header+b'x'*3000000)
        thread={'id':'seed-native','path':str(path)};self.admission.register_native('seed-create','seed',thread)
        with patch('curator_confinement.file_snapshot',side_effect=AssertionError('Whole-log hashing is not header identity')):
            first=self.admission.bind_storage('seed-native',thread)
        self.assertEqual(first['header_sha256'],hashlib.sha256(header).hexdigest());self.assertNotIn('sha256',first)
        self.assertEqual(first['hash_scope'],'first_jsonl_record_including_newline');self.assertEqual(first['path'],str(path))
        self.assertEqual(first['size'],len(header)+3000000)
        with path.open('ab') as stream:stream.write(b'appended')
        grown=self.admission.bind_storage('seed-native',thread);self.assertEqual(grown['header_sha256'],first['header_sha256'])
        retained=dict(self.admission.path_identities['seed-native']);replacement=path.with_suffix('.replacement')
        replacement.write_bytes(path.read_bytes());os.replace(replacement,path)
        with self.assertRaises(PolicyError):self.admission.bind_storage('seed-native',thread)
        self.assertEqual(self.admission.path_identities['seed-native'],retained)

    def test_header_encoding_actor_growth_race_and_special_paths_fail_closed(self):
        from curator_confinement import native_header_snapshot,NATIVE_HEADER_BYTES
        from unittest.mock import patch
        path=self.root/'header.jsonl';value={'type':'session_meta','payload':{'id':'actor'}}
        header=json.dumps(value).encode()+b'\n';path.write_bytes(header)
        initial=native_header_snapshot(self.root,path.name,'actor')
        for encoding in ('utf-32-be','utf-16-be'):
            path.write_bytes((json.dumps(value)+'\n').encode(encoding))
            with self.assertRaises(PolicyError):native_header_snapshot(self.root,path.name,'actor')
        path.write_bytes(header)
        with self.assertRaises(PolicyError):native_header_snapshot(self.root,path.name,'wrong-actor')
        changed=json.dumps({'type':'session_meta','payload':{'id':'actor'},'changed':True}).encode()+b'\n';path.write_bytes(changed)
        with self.assertRaises(PolicyError):native_header_snapshot(self.root,path.name,'actor',initial)
        path.write_bytes(b'x'*(NATIVE_HEADER_BYTES+1)+b'\n')
        with self.assertRaises(PolicyError):native_header_snapshot(self.root,path.name,'actor')
        path.write_bytes(header);import curator_confinement as module;read=module.read_native_header
        def append_during(stream,actor):
            result=read(stream,actor)
            with path.open('ab') as target:target.write(b'growth')
            return result
        with patch.object(module,'read_native_header',side_effect=append_during),self.assertRaises(PolicyError):native_header_snapshot(self.root,path.name,'actor')
        link=self.root/'hardlink';os.link(path,link)
        with self.assertRaises(PolicyError):native_header_snapshot(self.root,path.name,'actor')
        link.unlink();link.symlink_to(path)
        with self.assertRaises(PolicyError):native_header_snapshot(self.root,link.name,'actor')
        fifo=self.root/'fifo';os.mkfifo(fifo)
        with patch.object(module,'read_native_header',side_effect=AssertionError('Never read special files')),self.assertRaises(PolicyError):native_header_snapshot(self.root,fifo.name,'actor')


class HistoryIndexTests(unittest.TestCase):
    """Real synthetic SQL metadata snapshots; body columns are never selected."""
    def setUp(self):
        from curator_confinement import HISTORY_METADATA_COLUMNS,HISTORY_METADATA_KEYS
        self.fixture=NativeStorageTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root;self.database=self.fixture.database.parent/'thread_history_1.sqlite'
        self.columns=HISTORY_METADATA_COLUMNS
        text={'thread_id','turn_id','item_id','status','first_user_item_id','final_agent_item_id','item_type'}
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE TABLE _sqlx_migrations (version INTEGER PRIMARY KEY,description TEXT,installed_on TEXT,success INTEGER,checksum BLOB,execution_time INTEGER)')
            db.execute("INSERT INTO _sqlx_migrations VALUES (1,'synthetic','now',1,x'01',1)")
            for table,columns in self.columns.items():
                body=',error_json TEXT' if table=='thread_turns' else ',item_json TEXT' if table in ('thread_items','thread_realtime_items') else ''
                db.execute('CREATE TABLE '+table+' ('+','.join(c+(' TEXT' if c in text else ' INTEGER') for c in columns)+body+',PRIMARY KEY('+','.join(HISTORY_METADATA_KEYS[table])+'))')
                for actor in ('host-native','unlisted-native'):
                    row=self.row(table,actor);db.execute('INSERT INTO '+table+' ('+','.join(columns)+') VALUES ('+','.join('?' for _ in columns)+')',[row[k] for k in columns])
            db.execute("INSERT INTO thread_history_projection_state VALUES ('prior-seed',100,1)")
            schema=[list(row) for row in db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name')]
        info=self.database.stat();self.packet=self.fixture.packet
        self.packet['storage']['history_index']={'schema_version':1,'path':str(self.database),
            'identity':{'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,'mode':info.st_mode&0o777,'links':info.st_nlink},
            'schema_sha256':digest(schema),'migrations_sha256':digest([(1,'synthetic','now',1,'01',1)]),'metadata_row_bound':350000,'scan_seconds':15,
            'columns':{k:list(v) for k,v in self.columns.items()},'receipts':[]}
        self.a=NativeStorageAdmission(self.packet,digest(self.packet),deadline=time.monotonic()+30)

    def row(self,table,actor):
        values={'thread_id':actor,'turn_id':'turn1','item_id':'item1','rollout_ordinal':2,'created_at_ms':100,
            'item_type':'functionCall','updated_at_ordinal':2,'status':'inProgress','started_at':1,'completed_at':None,
            'duration_ms':None,'first_user_item_id':'first1','final_agent_item_id':None,'rollout_byte_offset':0,
            'rollout_end_ordinal':None,'rollout_end_byte_offset':None,'next_rollout_byte_offset':100,'next_rollout_ordinal':10}
        return {k:values[k] for k in self.columns[table]}

    def execute(self,sql,args=()):
        with sqlite3.connect(self.database) as db:db.execute(sql,args)

    def test_unlisted_update_insert_delete_schema_and_migration_changes_hold(self):
        self.a.freeze_preservation()
        changes=[("UPDATE thread_items SET updated_at_ordinal=3 WHERE thread_id='unlisted-native'", "UPDATE thread_items SET updated_at_ordinal=2 WHERE thread_id='unlisted-native'"),
            ("INSERT INTO thread_history_projection_state VALUES ('unexpected',0,0)","DELETE FROM thread_history_projection_state WHERE thread_id='unexpected'"),
            ("DELETE FROM thread_history_projection_state WHERE thread_id='prior-seed'","INSERT INTO thread_history_projection_state VALUES ('prior-seed',100,1)"),
            ("CREATE INDEX extra_index ON thread_items(item_type)","DROP INDEX extra_index"),
            ("UPDATE _sqlx_migrations SET success=0","UPDATE _sqlx_migrations SET success=1")]
        for change,restore in changes:
            self.execute(change)
            with self.subTest(change=change),self.assertRaises(PolicyError):self.a.check_preservation()
            self.execute(restore)
        self.assertEqual(self.a.check_preservation()['state'],'unchanged_unlisted_metadata')

    def test_concurrent_append_progress_and_later_regression_or_deletion_hold(self):
        self.a.freeze_preservation()
        self.execute("UPDATE thread_history_projection_state SET next_rollout_byte_offset=110,next_rollout_ordinal=11 WHERE thread_id='host-native'")
        self.execute("UPDATE thread_items SET updated_at_ordinal=5 WHERE thread_id='host-native'")
        self.execute("UPDATE thread_turns SET status='completed',completed_at=2,duration_ms=1000,final_agent_item_id='final1',rollout_end_ordinal=10,rollout_end_byte_offset=110 WHERE thread_id='host-native'")
        row=self.row('thread_items','host-native');row.update(item_id='item2',rollout_ordinal=6,updated_at_ordinal=6)
        columns=self.columns['thread_items'];self.execute('INSERT INTO thread_items ('+','.join(columns)+') VALUES ('+','.join('?' for _ in columns)+')',[row[k] for k in columns])
        result=self.a.check_preservation();self.assertEqual(result['history_index']['concurrent_progress']['thread_items']['observed_rows'],2)
        self.execute("UPDATE thread_history_projection_state SET next_rollout_byte_offset=105 WHERE thread_id='host-native'")
        with self.assertRaises(PolicyError):self.a.check_preservation()
        self.execute("UPDATE thread_history_projection_state SET next_rollout_byte_offset=110 WHERE thread_id='host-native'")
        self.execute("UPDATE thread_items SET item_type='changed-stable-type' WHERE thread_id='host-native' AND item_id='item1'")
        with self.assertRaises(PolicyError):self.a.check_preservation()
        self.execute("UPDATE thread_items SET item_type='functionCall' WHERE thread_id='host-native' AND item_id='item1'")
        self.execute("DELETE FROM thread_items WHERE thread_id='host-native' AND item_id='item2'")
        with self.assertRaises(PolicyError):self.a.check_preservation()

    def test_owned_projection_is_attributed_but_old_seed_remains_protected(self):
        self.a.freeze_preservation();self.a.begin_operation('seed','seed-create','seed')
        path=Path(self.packet['storage']['history_root'])/'new-owned.jsonl';path.write_text(json.dumps({'type':'session_meta','payload':{'id':'new-owned'}})+'\n')
        thread={'id':'new-owned','path':str(path)};self.a.register_native('seed-create','seed',thread);self.a.bind_storage('new-owned',thread)
        self.execute("INSERT INTO thread_history_projection_state VALUES ('new-owned',1038,1)")
        result=self.a.check_preservation()['history_index']['owned']['thread_history_projection_state']['new-owned']
        self.assertEqual(result['count'],1);self.assertEqual(result['projection']['next_rollout_byte_offset'],1038)
        self.execute("UPDATE thread_history_projection_state SET next_rollout_ordinal=2 WHERE thread_id='prior-seed'")
        with self.assertRaises(PolicyError):self.a.check_preservation()

    def test_explicit_metadata_queries_never_read_item_or_error_bodies(self):
        from unittest.mock import patch
        original=sqlite3.connect
        def guarded(*args,**kwargs):
            db=original(*args,**kwargs)
            def authorize(action,first,second,database,origin):
                if action==sqlite3.SQLITE_READ and second in ('item_json','error_json'):return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            db.set_authorizer(authorize);return db
        self.execute("UPDATE thread_items SET item_json='PRIVATE-BODY'")
        self.execute("UPDATE thread_turns SET error_json='PRIVATE-ERROR'")
        with patch('curator_confinement.sqlite3.connect',side_effect=guarded):
            self.a.freeze_preservation();result=self.a.check_preservation()
        self.assertNotIn('PRIVATE-',json.dumps(result));self.assertNotIn('PRIVATE-',json.dumps(self.a.history_baseline))

    def test_identity_scaled_row_bound_and_final_timeout_hold(self):
        import importlib.util
        self.a.freeze_preservation();identity=self.a.history_index['identity'];original=identity['inode'];identity['inode']+=1
        with self.assertRaises(PolicyError):self.a.check_preservation()
        identity['inode']=original
        self.a.history_index['metadata_row_bound']=1
        with self.assertRaises(PolicyError) as bounded:self.a.check_preservation()
        self.assertEqual(bounded.exception.code,'native_history_row_bound')
        self.a.history_index['metadata_row_bound']=350000
        path=Path(__file__).resolve().parents[3]/'Verification/project-curator-release/run-native-proof.py'
        spec=importlib.util.spec_from_file_location('history_final_deadline_fixture',path);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        self.a.deadline=time.monotonic()-1;report={'state':'passed_p0_only','storage':{}}
        runner.finalize_p0_storage(report,self.a);self.assertEqual(report['state'],'blocked')
        # State-index/JSONL checks succeed, then the final history phase loses
        # its remaining stop budget. Earlier observations cannot stand for it.
        from unittest.mock import patch
        self.a.deadline=time.monotonic()+10;scan=self.a._history_index_snapshot
        def expire_at_history():
            self.a.deadline=time.monotonic()-1
            return scan()
        report={'state':'passed_p0_only','storage':{}}
        with patch.object(self.a,'_history_index_snapshot',side_effect=expire_at_history):
            runner.finalize_p0_storage(report,self.a)
        self.assertEqual(report['code'],'final_native_storage_unproven')
        self.assertEqual(report['storage']['final_preservation']['state'],'unproven')


class AmbientMetadataTests(unittest.TestCase):
    """Actual disposable SQL/lstat accounting; host decisions are synthetic fixtures."""
    def fixture(self,*,freeze=True,observation_protocol=1):
        import copy
        from types import SimpleNamespace
        from curator_confinement import AMBIENT_LIMITS
        history=HistoryIndexTests();history.setUp();self.addCleanup(history.doCleanups)
        old=history.fixture;proof=tempfile.TemporaryDirectory();self.addCleanup(proof.cleanup)
        root=Path(proof.name).resolve();(root/'trusted/native-storage').mkdir(parents=True)
        cwd=old.root/'baseline-project';cwd.mkdir()
        with sqlite3.connect(old.database) as db:
            db.execute('DROP TABLE projects');db.execute('DROP TABLE project_roots')
            db.execute('CREATE TABLE projects (id TEXT PRIMARY KEY,position INTEGER,created_at_ms INTEGER,updated_at_ms INTEGER,name TEXT)')
            db.execute('CREATE TABLE project_roots (project_id TEXT,position INTEGER,path TEXT)')
            db.execute("INSERT INTO projects VALUES ('baseline-project',0,1,1,'EXCLUDED-NAME')")
            db.execute('INSERT INTO project_roots VALUES (?,?,?)',('baseline-project',0,str(cwd)))
        packet=copy.deepcopy(history.packet);packet['root']=str(root);packet['stage']='native-fork-p1'
        packet['seed_selection']={'retained_prior_native_ids':['prior-proof']}
        packet['storage']['ambient_review']={'schema_version':1,'kind':'AmbientMetadataReview','limits':dict(AMBIENT_LIMITS),
            'observer':'host','protected_roots':[str(root)]}
        if observation_protocol!=1:packet['storage']['ambient_review']['observation_protocol']=observation_protocol
        a=NativeStorageAdmission(packet,digest(packet),deadline=time.monotonic()+30)
        if freeze:a.freeze_preservation()
        return SimpleNamespace(a=a,h=history,f=old,root=root,cwd=cwd)

    def external(self,x,aid,number=1,new_project=True):
        cwd=x.f.root/('external-'+aid) if new_project else x.cwd
        if not cwd.exists():cwd.mkdir()
        log=Path(x.a.selected['history_root'])/(aid+'.jsonl');log.write_bytes(b'x'*100)
        row={**x.f.row,'id':aid,'created_at':number+2,'updated_at':number+2,'rollout_path':str(log),'cwd':str(cwd),'project_id':None}
        with sqlite3.connect(x.f.database) as db:
            db.execute('INSERT INTO threads ('+','.join(x.f.columns)+') VALUES ('+','.join('?' for _ in x.f.columns)+')',[row[key] for key in x.f.columns])
            if new_project:
                db.execute('INSERT INTO projects VALUES (?,?,?,?,?)',('project-'+aid,number,number,number,'EXCLUDED-'+aid))
                db.execute('INSERT INTO project_roots VALUES (?,?,?)',('project-'+aid,0,str(cwd)))
        x.h.execute('INSERT INTO thread_history_projection_state VALUES (?,?,?)',(aid,100,1))
        return log

    def witness(self,x,**updates):
        return {'admission_closed':True,'actors':[],'pending_callbacks':0,'pending_requests':0,'pending_owner_operations':0,
            'pending_releases':0,'proof_native_ids':sorted(x.a.known),'operation_ledger_sha256':digest(x.a.pending),**updates}

    def challenge(self,x,**updates):
        with self.assertRaises(PolicyError) as caught:x.a.check_preservation(quiescence=lambda:self.witness(x,**updates))
        self.assertEqual(caught.exception.code,'ambient_review_required');self.assertFalse(x.a.ambient.open)
        return x.a.ambient.challenge['value']

    def decision(self,x,mutate=None):
        from curator_confinement import AmbientMetadataReview
        c=x.a.ambient.challenge['value'];observations=[]
        for aid,row in c['additions']['threads'].items():
            project=next(root['project_id'] for root in x.a.ambient.challenge['snapshot']['roots'].values() if root['path']==row['cwd'])
            log=c['additions']['logs'][row['rollout_path']]
            observations.append({'native_id':aid,'app':{'source':'codex_app.list_threads','record_id':'actual-app-observation-fixture',
                'task_id':'app-'+aid,'native_id':aid,'project_id':'different-app-project-'+project},
                'native':{'source':'readonly_selected_metadata','record_id':'actual-native-observation-fixture','native_id':aid,'project_id':project,
                    'thread_stable_sha256':digest(AmbientMetadataReview._stable_thread(row)),'log_stable_sha256':digest(AmbientMetadataReview._stable_log(log)),
                    'history_challenge_sha256':digest({table:{key:value for key,value in rows.items() if value['thread_id']==aid}
                        for table,rows in c['additions']['history'].items()})}})
        value={'schema_version':1,'kind':'AmbientMetadataDecision','observer':'host','decision':'accept',
            **{key:c[key] for key in ('scope_sha256','baseline_sha256','previous_receipt_sha256','batch','native_ids')},
            'challenge_sha256':digest(c),'additions_sha256':digest(c['additions']),'observations':observations}
        if mutate:mutate(value)
        with x.a.ambient.decision_path().open('x') as out:json.dump(value,out)
        return value

    def test_immutable_baseline_and_exact_external_adoption(self):
        x=self.fixture();before={p.name:p.read_bytes() for p in x.a.state_root.glob('*before.json')}
        self.external(x,'external-one');challenge=self.challenge(x);self.assertEqual(challenge['native_ids'],['external-one'])
        with self.assertRaises(PolicyError):x.a.assert_admission()
        self.decision(x);accepted=x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        self.assertEqual(accepted['state'],'ambient_delta_accepted');self.assertFalse(accepted['proof_membership_changed'])
        self.assertEqual(x.a.known,{});self.assertEqual(x.a.slots,{})
        self.assertEqual({p.name:p.read_bytes() for p in x.a.state_root.glob('*before.json')},before)
        self.assertEqual(x.a.check_preservation()['ambient_receipts'],1)

    def test_two_ordered_batches_replay_and_monotonic_external_progress(self):
        x=self.fixture();logs=[]
        for number,aid in enumerate(('external-one','external-two'),1):
            logs.append(self.external(x,aid,number));self.challenge(x);decision=self.decision(x)
            self.assertIsNone(x.a.ambient.challenge['value']['additions']['threads'][aid]['project_id'])
            self.assertNotEqual(decision['observations'][0]['app']['project_id'],decision['observations'][0]['native']['project_id'])
            x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        logs[0].write_bytes(b'x'*150)
        with sqlite3.connect(x.f.database) as db:db.execute("UPDATE threads SET updated_at=10 WHERE id='external-one'")
        x.h.execute("UPDATE thread_history_projection_state SET next_rollout_byte_offset=150,next_rollout_ordinal=2 WHERE thread_id='external-one'")
        self.assertEqual(x.a.check_preservation()['ambient_receipts'],2)
        expected,last=x.a.ambient._replay();self.assertTrue({'external-one','external-two'}<=set(expected['threads']))
        self.assertEqual(last,x.a.ambient.chain[-1]['file']['sha256'])
        self.assertEqual(len(expected['history']['external']['thread_history_projection_state']),2)

    def test_baseline_changes_aliases_special_files_and_unselected_projects_fail_closed(self):
        changes=('old-thread','old-log','archive','old-project','root-change','unknown-schema','unselected-project','hardlink','symlink','fifo','old-file-substitution')
        for kind in changes:
            x=self.fixture();log=self.external(x,'external-one')
            if kind=='old-thread':
                with sqlite3.connect(x.f.database) as db:db.execute("UPDATE threads SET model='foreign' WHERE id='host-native'")
            elif kind=='old-log':x.f.other.write_bytes(b'changed')
            elif kind=='archive':
                with sqlite3.connect(x.f.database) as db:db.execute("UPDATE threads SET archived=1 WHERE id='host-native'")
            elif kind=='old-project':
                with sqlite3.connect(x.f.database) as db:db.execute("UPDATE projects SET updated_at_ms=2 WHERE id='baseline-project'")
            elif kind=='root-change':
                with sqlite3.connect(x.f.database) as db:db.execute("UPDATE project_roots SET position=9 WHERE project_id='baseline-project'")
            elif kind=='unknown-schema':
                with sqlite3.connect(x.f.database) as db:db.execute('ALTER TABLE projects ADD COLUMN unknown TEXT')
            elif kind=='unselected-project':
                with sqlite3.connect(x.f.database) as db:db.execute("INSERT INTO projects VALUES ('unselected',9,9,9,'hidden')")
            elif kind=='hardlink':os.link(log,log.with_name('alias.jsonl'))
            elif kind=='symlink':log.with_name('alias.jsonl').symlink_to(log)
            elif kind=='fifo':os.mkfifo(log.with_name('fifo.jsonl'))
            else:
                with sqlite3.connect(x.f.database) as db:db.execute("UPDATE threads SET rollout_path=? WHERE id='external-one'",(str(x.f.other),))
            with self.subTest(kind=kind),self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))
            self.assertIsNone(x.a.ambient.challenge);self.assertFalse(x.a.ambient.open)

    def test_wrong_stale_duplicate_and_incomplete_host_decisions_cannot_adopt(self):
        mutations=[lambda v:v.update(scope_sha256='wrong'),lambda v:v.update(baseline_sha256='wrong'),
            lambda v:v.update(previous_receipt_sha256='wrong'),lambda v:v.update(challenge_sha256='wrong'),
            lambda v:v.update(native_ids=['other']),lambda v:v.update(observations=[]),lambda v:v.update(unselected=True),
            lambda v:v.update(batch=2)]
        for index,mutate in enumerate(mutations):
            x=self.fixture();self.external(x,'external-one');self.challenge(x);self.decision(x,mutate)
            with self.subTest(case=index),self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
            self.assertEqual(x.a.ambient.chain,[]);self.assertFalse(x.a.ambient.open)
        x=self.fixture();self.external(x,'external-one');self.challenge(x);self.decision(x);x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))

    def test_nonquiescent_or_proof_owned_candidates_never_get_a_resumable_hold(self):
        for key in ('pending_callbacks','pending_requests','pending_owner_operations','pending_releases'):
            x=self.fixture();self.external(x,'external-one')
            with self.subTest(key=key),self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x,**{key:1}))
            self.assertIsNone(x.a.ambient.challenge)
        x=self.fixture();self.external(x,'external-one')
        with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x,proof_native_ids=['external-one']))
        x=self.fixture();self.external(x,'prior-proof')
        with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))
        x=self.fixture();self.external(x,'external-one')
        with sqlite3.connect(x.f.database) as db:db.execute("UPDATE threads SET cwd=? WHERE id='external-one'",(str(x.root),))
        with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))

    def test_reopen_rejects_additional_change_and_uses_current_challenge_high_water(self):
        x=self.fixture();self.external(x,'external-one');self.challenge(x);self.decision(x);self.external(x,'external-two',2)
        with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        x=self.fixture();log=self.external(x,'external-one');self.challenge(x);self.decision(x)
        log.write_bytes(b'x'*200);x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        log.write_bytes(b'x'*150)
        with self.assertRaises(PolicyError):x.a.check_preservation()

    def test_absent_rejected_exhausted_and_final_review_states_remain_closed(self):
        x=self.fixture();self.external(x,'external-one');self.challenge(x)
        with self.assertRaises(PolicyError) as missing:x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        self.assertEqual(missing.exception.code,'ambient_receipt_pending')
        self.decision(x,lambda value:value.update(decision='reject'))
        with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        x=self.fixture();self.external(x,'external-one')
        with self.assertRaises(PolicyError):x.a.check_preservation(final=True)
        self.assertIsNone(x.a.ambient.challenge);self.assertFalse(x.a.ambient.open)
        x=self.fixture();x.a.ambient.checkpoints=96
        with self.assertRaises(PolicyError):x.a.check_preservation()
        x=self.fixture();x.a.deadline=time.monotonic()-1
        with self.assertRaises(PolicyError):x.a.check_preservation()
        x=self.fixture()
        for number in range(4):
            for suffix in ('a','b'):self.external(x,'external-'+str(number)+suffix,number+1,new_project=False)
            self.challenge(x);self.decision(x);x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        self.external(x,'ninth-external',5,new_project=False)
        with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))


class AmbientPartialInitializationTests(unittest.TestCase):
    def test_each_partial_boundary_is_typed_closed_without_final_file_changes(self):
        from unittest.mock import patch
        from contextlib import ExitStack
        import curator_confinement as module
        for boundary in ('storage_snapshot','storage_save','history_snapshot','history_save','ambient_snapshot','legacy_compare','ambient_save','baseline_binding'):
            with self.subTest(boundary=boundary):
                case=AmbientMetadataTests();self.addCleanup(case.doCleanups);x=case.fixture(freeze=False);a=x.a;review=a.ambient
                primary=PolicyError('injected_initialization_failure','Selected partial-boundary fixture.')
                save=a._save;snapshot=review._snapshot;binding=module.file_snapshot
                def save_at(name,value):
                    if name=={'storage_save':'preservation-before.json','history_save':'history-index-before.json','ambient_save':'ambient-before.json'}.get(boundary):raise primary
                    return save(name,value)
                def snapshot_at():
                    value=snapshot()
                    if boundary=='legacy_compare':x.f.other.write_bytes(b'Unlisted metadata changed during ambient freeze')
                    return value
                def binding_at(root,relative,*args):
                    if boundary=='baseline_binding' and Path(root)==a.state_root:raise primary
                    return binding(root,relative,*args)
                with ExitStack() as stack:
                    stack.enter_context(patch.object(a,'_save',side_effect=save_at));stack.enter_context(patch.object(module,'file_snapshot',side_effect=binding_at))
                    stack.enter_context(patch.object(review,'_snapshot',side_effect=primary if boundary=='ambient_snapshot' else snapshot_at))
                    if boundary=='storage_snapshot':stack.enter_context(patch.object(a,'preservation_snapshot',side_effect=primary))
                    if boundary=='history_snapshot':stack.enter_context(patch.object(a,'_history_index_snapshot',side_effect=primary))
                    with self.assertRaises(PolicyError) as caught:a.freeze_preservation()
                self.assertEqual(caught.exception.code,'native_storage_preservation_unproven' if boundary=='legacy_compare' else primary.code)
                before={str(p.relative_to(a.state_root)):p.read_bytes() for p in a.state_root.rglob('*') if p.is_file()}
                self.assertFalse(review.initialized);self.assertFalse(review.open)
                with self.assertRaises(PolicyError) as final:a.check_preservation(final=True)
                self.assertEqual(final.exception.code,'ambient_initialization_incomplete')
                with self.assertRaises(PolicyError):a.assert_admission()
                self.assertEqual(before,{str(p.relative_to(a.state_root)):p.read_bytes() for p in a.state_root.rglob('*') if p.is_file()})


class AmbientChildObservationTests(unittest.TestCase):
    fixture=AmbientMetadataTests.fixture
    external=AmbientMetadataTests.external
    challenge=AmbientMetadataTests.challenge
    witness=AmbientMetadataTests.witness
    PARENT='10000000-0000-4000-8000-000000000001'
    CHILD='10000000-0000-4000-8000-000000000002'
    OTHER='10000000-0000-4000-8000-000000000003'

    def edge(self,parent=None,**extra):
        return json.dumps({'subagent':{'thread_spawn':{'parent_thread_id':parent or self.PARENT,'depth':1,
            'agent_path':'/root/worker1','agent_nickname':'Synthetic','agent_role':None,**extra}}})

    def child(self,x,source=None):
        self.external(x,self.CHILD,new_project=False)
        with sqlite3.connect(x.f.database) as db:db.execute('UPDATE threads SET source=? WHERE id=?',(source if source is not None else self.edge(),self.CHILD))

    def initial_parent(self,x):
        log=self.external(x,self.PARENT,new_project=False)
        with sqlite3.connect(x.f.database) as db:
            row=dict(zip(x.f.columns,db.execute('SELECT '+','.join(x.f.columns)+' FROM threads WHERE id=?',(self.PARENT,)).fetchone()))
        info=log.stat();identity={'path':str(log),'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,'mode':stat.S_IMODE(info.st_mode),
            'links':info.st_nlink,'size':info.st_size,'mtime_ns':info.st_mtime_ns}
        binding={'execution_role':'unrelated_external_metadata_observation','index_metadata':row,'log_identity':identity,'native_parent_id':None}
        x.a.concurrent[self.PARENT]=binding;x.a.concurrent_paths[str(log)]=binding

    def v2_decision(self,x,*,direct_ids=(),mutate=None):
        from curator_confinement import AmbientMetadataReview
        c=x.a.ambient.challenge['value'];snapshot=x.a.ambient.challenge['snapshot']
        def app(aid):return {'source':'codex_app.list_threads','record_id':'fresh-app-fixture-'+str(c['batch']),
            'task_id':'app-'+aid,'native_id':aid,'project_id':'separate-app-project','challenge_sha256':digest(c)}
        def metadata(aid,history):
            row=snapshot['threads'][aid];log=snapshot['logs'][row['rollout_path']]
            project=next(root['project_id'] for root in snapshot['roots'].values() if root['path']==row['cwd'])
            value={'source':'readonly_selected_metadata','record_id':'fresh-native-fixture-'+str(c['batch']),
                'native_id':aid,'project_id':project,'thread_stable_sha256':digest(AmbientMetadataReview._stable_thread(row)),
                'log_stable_sha256':digest(AmbientMetadataReview._stable_log(log)),'challenge_sha256':digest(c)}
            if history:value['history_challenge_sha256']=digest({table:{key:row for key,row in rows.items() if row['thread_id']==aid} for table,rows in c['additions']['history'].items()})
            return value
        observations=[]
        for aid in c['native_ids']:
            if aid in direct_ids:observations.append({'kind':'direct_task','native_id':aid,'app':app(aid),'native':metadata(aid,True)})
            else:observations.append({'kind':'direct_child','child_native_id':aid,'parent_native_id':self.PARENT,
                'app_parent':app(self.PARENT),'child':metadata(aid,True),'parent':metadata(self.PARENT,False),
                'source_sha256':hashlib.sha256(snapshot['threads'][aid]['source'].encode()).hexdigest()})
        value={'schema_version':1,'observation_protocol':2,'kind':'AmbientMetadataDecision','observer':'host','decision':'accept',
            **{key:c[key] for key in ('scope_sha256','baseline_sha256','previous_receipt_sha256','batch','native_ids')},
            'challenge_sha256':digest(c),'additions_sha256':digest(c['additions']),'observations':observations}
        if mutate:mutate(value)
        x.a.ambient.decision_path().write_text(json.dumps(value));return value

    def ready_child(self,source=None):
        x=self.fixture(freeze=False,observation_protocol=2);self.initial_parent(x);x.a.freeze_preservation()
        self.child(x,source);self.challenge(x);return x

    def test_exact_child_initial_prior_and_same_batch_parent_routes_replay_with_fixed_counts(self):
        for route in ('initial','prior','same_batch'):
            with self.subTest(route=route):
                x=self.fixture(freeze=False,observation_protocol=2)
                if route=='initial':self.initial_parent(x)
                x.a.freeze_preservation()
                if route!='initial':self.external(x,self.PARENT,new_project=False)
                if route=='prior':
                    self.challenge(x);self.v2_decision(x,direct_ids=(self.PARENT,));x.a.ambient.adopt(quiescence=lambda:self.witness(x))
                self.child(x);self.challenge(x);decision=self.v2_decision(x,direct_ids=(self.PARENT,) if route=='same_batch' else ())
                child=next(row for row in decision['observations'] if row['kind']=='direct_child')
                self.assertEqual(child['app_parent']['native_id'],self.PARENT);self.assertNotIn('app',child)
                self.assertIsNone(x.a.ambient.challenge['snapshot']['threads'][self.CHILD]['project_id'])
                result=x.a.ambient.adopt(quiescence=lambda:self.witness(x));self.assertFalse(result['proof_membership_changed'])
                self.assertEqual(len(result['external_native_ids']),2 if route=='same_batch' else 1)
                self.assertEqual(x.a.check_preservation()['ambient_receipts'],2 if route=='prior' else 1)

    def test_missing_app_parent_wrong_swapped_and_malformed_source_edges_reject(self):
        sources={'unsupported':'{"fork":{}}','malformed':'[','duplicate':'{"subagent":{},"subagent":{}}',
            'extra':self.edge(extra=True),'ancestry':self.edge(self.OTHER,depth=2),'spoof_label':self.edge('/root/worker1',agent_path=self.PARENT)}
        for case in ('missing_app','wrong_parent','swapped_child',*sources):
            with self.subTest(case=case):
                x=self.ready_child(sources.get(case))
                def change(value):
                    row=value['observations'][0]
                    if case=='missing_app':row['app_parent']=None
                    if case=='wrong_parent':row['parent_native_id']=self.OTHER
                    if case=='swapped_child':row['child_native_id']=self.PARENT
                self.v2_decision(x,mutate=change)
                with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
                self.assertFalse(x.a.ambient.open);self.assertEqual(x.a.ambient.chain,[])

    def test_global_own_proof_retained_uuid_exclusions_apply_to_both_roles(self):
        for role in ('parent','child'):
            for kind in ('host','manager','implementer','proof','retained'):
                with self.subTest(role=role,kind=kind):
                    x=self.ready_child();aid=self.PARENT if role=='parent' else self.CHILD
                    if kind=='retained':x.a.packet['seed_selection']['retained_prior_native_ids'].append(aid)
                    elif kind=='proof':x.a.known[aid]='fixture-proof'
                    else:x.a.concurrent[aid]={**x.a.concurrent[self.PARENT],'execution_role':kind}
                    self.v2_decision(x)
                    with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
                    self.assertFalse(x.a.ambient.open)

    def test_mixed_versions_unknown_fields_and_changed_initial_associations_hold(self):
        for case in ('version','mixed','unknown','stale_app','stale_metadata','archived','cwd','root','parent_field'):
            with self.subTest(case=case):
                x=self.ready_child()
                def change(value):
                    if case=='version':value['observation_protocol']=1
                    if case=='mixed':value['observations'][0]={'native_id':self.CHILD,'app':{},'native':{}}
                    if case=='unknown':value['observations'][0]['child_app_visible']=True
                    if case=='stale_app':value['observations'][0]['app_parent']['challenge_sha256']='a'*64
                    if case=='stale_metadata':value['observations'][0]['parent']['challenge_sha256']='a'*64
                self.v2_decision(x,mutate=change)
                with sqlite3.connect(x.f.database) as db:
                    if case=='archived':db.execute('UPDATE threads SET archived=1 WHERE id=?',(self.PARENT,))
                    if case=='cwd':db.execute('UPDATE threads SET cwd=? WHERE id=?',(str(x.root),self.PARENT))
                    if case=='root':db.execute('UPDATE project_roots SET path=?',(str(x.root),))
                    if case=='parent_field':db.execute('UPDATE threads SET model=? WHERE id=?',('other-model',self.PARENT))
                with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))

    def test_fresh_extra_identity_source_change_deadline_and_budget_still_hold(self):
        for case in ('extra','source','deadline','budget'):
            with self.subTest(case=case):
                x=self.ready_child();self.v2_decision(x)
                if case=='extra':self.external(x,self.OTHER,new_project=False)
                if case=='source':
                    with sqlite3.connect(x.f.database) as db:db.execute('UPDATE threads SET source=? WHERE id=?',('{}',self.CHILD))
                if case=='deadline':x.a.deadline=time.monotonic()-1
                if case=='budget':x.a.ambient.checkpoints=96
                with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
                self.assertFalse(x.a.ambient.open)


class ProjectlessMetadataTests(unittest.TestCase):
    fixture=AmbientMetadataTests.fixture
    external=AmbientMetadataTests.external
    challenge=AmbientMetadataTests.challenge
    witness=AmbientMetadataTests.witness
    initial_parent=AmbientChildObservationTests.initial_parent
    child=AmbientChildObservationTests.child
    edge=AmbientChildObservationTests.edge
    PARENT=AmbientChildObservationTests.PARENT
    CHILD=AmbientChildObservationTests.CHILD
    OTHER=AmbientChildObservationTests.OTHER

    def setup_case(self,*,protocol=3,projectless=True,parent=False,freeze=True):
        x=self.fixture(freeze=False,observation_protocol=protocol)
        if projectless:
            with sqlite3.connect(x.f.database) as db:db.execute('DELETE FROM project_roots');db.execute('DELETE FROM projects')
        if parent:self.initial_parent(x)
        if freeze:x.a.freeze_preservation()
        return x

    def decision(self,x,*,direct_ids=(),mutate=None):
        from curator_confinement import AmbientMetadataReview
        c=x.a.ambient.challenge['value'];snapshot=x.a.ambient.challenge['snapshot']
        def binding(aid):
            row=snapshot['threads'][aid];roots=[root for root in snapshot['roots'].values() if root['path']==row['cwd']]
            return roots[0]['project_id'] if roots else None,{'kind':'linked' if roots else 'projectless','exact_cwd_roots_sha256':digest(roots)}
        def app(aid):return {'source':'codex_app.list_threads','record_id':'current-app-fixture','task_id':'app-'+aid,'native_id':aid,
            'project_id':'different-app-project' if binding(aid)[0] is not None else None,'challenge_sha256':digest(c)}
        def metadata(aid,history):
            row=snapshot['threads'][aid];log=snapshot['logs'][row['rollout_path']];project,selected=binding(aid)
            value={'source':'readonly_selected_metadata','record_id':'current-native-fixture','native_id':aid,'project_id':project,
                'thread_stable_sha256':digest(AmbientMetadataReview._stable_thread(row)),'log_stable_sha256':digest(AmbientMetadataReview._stable_log(log)),
                'challenge_sha256':digest(c),'project_binding':selected}
            if history:value['history_challenge_sha256']=digest({table:{key:row for key,row in rows.items() if row['thread_id']==aid} for table,rows in c['additions']['history'].items()})
            return value
        observations=[]
        for aid in c['native_ids']:
            if aid in direct_ids:observations.append({'kind':'direct_task','native_id':aid,'app':app(aid),'native':metadata(aid,True)})
            else:observations.append({'kind':'direct_child','child_native_id':aid,'parent_native_id':self.PARENT,'app_parent':app(self.PARENT),
                'child':metadata(aid,True),'parent':metadata(self.PARENT,False),'source_sha256':hashlib.sha256(snapshot['threads'][aid]['source'].encode()).hexdigest()})
        value={'schema_version':1,'observation_protocol':3,'kind':'AmbientMetadataDecision','observer':'host','decision':'accept',
            **{key:c[key] for key in ('scope_sha256','baseline_sha256','previous_receipt_sha256','batch','native_ids')},
            'challenge_sha256':digest(c),'additions_sha256':digest(c['additions']),'observations':observations}
        if mutate:mutate(value)
        x.a.ambient.decision_path().write_text(json.dumps(value));return value

    def direct(self,**kwargs):
        x=self.setup_case(**kwargs);self.external(x,self.CHILD,new_project=False);self.challenge(x);return x

    def add_root(self,x):
        with sqlite3.connect(x.f.database) as db:
            db.execute('INSERT INTO projects VALUES (?,?,?,?,?)',('new-project',1,1,1,'EXCLUDED-NAME'))
            db.execute('INSERT INTO project_roots VALUES (?,?,?)',('new-project',0,str(x.cwd)))

    def test_p0_legacy_default_and_protocol2_keep_linked_requirement(self):
        for protocol in (1,2):
            x=self.setup_case(protocol=protocol);self.external(x,self.CHILD,new_project=False)
            with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))
            x=self.direct(protocol=protocol,projectless=False)
            if protocol==1:AmbientMetadataTests.decision(self,x)
            else:AmbientChildObservationTests.v2_decision(self,x,direct_ids=(self.CHILD,))
            self.assertEqual(x.a.ambient.adopt(quiescence=lambda:self.witness(x))['state'],'ambient_delta_accepted')

    def test_p1_direct_projectless_adopts_and_replays_with_immutable_baseline(self):
        x=self.direct();before={p.name:p.read_bytes() for p in x.a.state_root.glob('*before.json')};decision=self.decision(x,direct_ids=(self.CHILD,))
        record=decision['observations'][0];self.assertIsNone(record['app']['project_id']);self.assertIsNone(record['native']['project_id'])
        self.assertEqual(record['native']['project_binding'],{'kind':'projectless','exact_cwd_roots_sha256':digest([])})
        self.assertEqual(x.a.ambient.challenge['value']['additions']['projects'],{});self.assertEqual(x.a.ambient.challenge['value']['additions']['roots'],{})
        result=x.a.ambient.adopt(quiescence=lambda:self.witness(x));self.assertFalse(result['proof_membership_changed'])
        self.assertEqual(x.a.check_preservation()['ambient_receipts'],1);self.assertEqual(x.a.known,{})
        self.assertEqual(before,{p.name:p.read_bytes() for p in x.a.state_root.glob('*before.json')})

    def test_p2_direct_child_has_separate_parent_app_and_equal_projectless_binding(self):
        x=self.setup_case(parent=True);self.child(x);self.challenge(x);decision=self.decision(x)
        observed=decision['observations'][0];self.assertEqual(observed['app_parent']['native_id'],self.PARENT);self.assertNotIn('app',observed)
        self.assertIsNone(observed['app_parent']['project_id']);self.assertEqual(observed['child']['project_binding'],observed['parent']['project_binding'])
        self.assertEqual(len(x.a.ambient.challenge['value']['native_ids']),1)
        self.assertEqual(x.a.ambient.adopt(quiescence=lambda:self.witness(x))['external_native_ids'],[self.CHILD]);self.assertEqual(x.a.check_preservation()['ambient_receipts'],1)

    def test_p3_missing_unavailable_or_contradictory_project_evidence_rejects(self):
        for case in ('native_nonnull','missing_native','missing_binding','wrong_empty_digest','unknown_class','app_nonnull','missing_app'):
            with self.subTest(case=case):
                x=self.direct()
                def change(value):
                    observation=value['observations'][0];record=observation['native']
                    if case=='native_nonnull':record['project_id']='not-null'
                    if case=='missing_native':record.pop('project_id')
                    if case=='missing_binding':record.pop('project_binding')
                    if case=='wrong_empty_digest':record['project_binding']['exact_cwd_roots_sha256']=digest({})
                    if case=='unknown_class':record['project_binding']['kind']='unknown'
                    if case=='app_nonnull':observation['app']['project_id']='not-null'
                    if case=='missing_app':observation['app'].pop('project_id')
                self.decision(x,direct_ids=(self.CHILD,),mutate=change)
                with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
                self.assertFalse(x.a.ambient.open)
        x=self.setup_case();self.external(x,self.CHILD,new_project=False)
        with sqlite3.connect(x.f.database) as db:db.execute('UPDATE threads SET project_id=? WHERE id=?',('non-null-with-no-root',self.CHILD))
        with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))
        with self.assertRaises(PolicyError):x.a.ambient._project_binding({'cwd':str(x.cwd),'project_id':None},{'roots':None,'projects':{}})

    def test_p4_linked_positive_and_changed_root_source_alias_or_exclusion_rejects(self):
        x=self.direct(projectless=False);self.decision(x,direct_ids=(self.CHILD,));self.assertEqual(x.a.ambient.adopt(quiescence=lambda:self.witness(x))['state'],'ambient_delta_accepted')
        for case in ('duplicate_root','deleted_root','deleted_project','source','cwd','alias','own','current','retained','protected'):
            with self.subTest(case=case):
                x=self.direct(projectless=False);self.decision(x,direct_ids=(self.CHILD,))
                with sqlite3.connect(x.f.database) as db:
                    if case=='duplicate_root':db.execute('INSERT INTO project_roots VALUES (?,?,?)',('baseline-project',1,str(x.cwd)))
                    if case=='deleted_root':db.execute('DELETE FROM project_roots')
                    if case=='deleted_project':db.execute('DELETE FROM projects')
                    if case=='source':db.execute('UPDATE threads SET source=? WHERE id=?',('{}',self.CHILD))
                    if case=='cwd':db.execute('UPDATE threads SET cwd=? WHERE id=?',(str(x.f.root),self.CHILD))
                    if case=='protected':db.execute('UPDATE threads SET cwd=? WHERE id=?',(str(x.root),self.CHILD))
                if case=='alias':(x.f.root/'alias').symlink_to(x.cwd,target_is_directory=True)
                if case=='alias':
                    with sqlite3.connect(x.f.database) as db:db.execute('UPDATE threads SET cwd=? WHERE id=?',(str(x.f.root/'alias'),self.CHILD))
                if case=='own':x.a.concurrent[self.CHILD]={'execution_role':'host'}
                if case=='current':x.a.known[self.CHILD]='proof-fixture'
                if case=='retained':x.a.packet['seed_selection']['retained_prior_native_ids'].append(self.CHILD)
                with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))

    def test_p5_fresh_or_later_associations_cannot_reclassify_existing_projectless_rows(self):
        for moment in ('after_challenge','after_adoption','initial_parent_new_child','accepted_parent_new_child','native_project_change'):
            with self.subTest(moment=moment):
                if moment=='initial_parent_new_child':
                    x=self.setup_case(parent=True);self.child(x);self.add_root(x)
                    with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))
                    continue
                if moment=='accepted_parent_new_child':
                    x=self.setup_case();self.external(x,self.PARENT,new_project=False);self.challenge(x);self.decision(x,direct_ids=(self.PARENT,))
                    x.a.ambient.adopt(quiescence=lambda:self.witness(x));self.child(x);self.add_root(x)
                    with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))
                    continue
                x=self.direct();self.decision(x,direct_ids=(self.CHILD,))
                if moment=='after_adoption':x.a.ambient.adopt(quiescence=lambda:self.witness(x))
                if moment=='native_project_change':
                    with sqlite3.connect(x.f.database) as db:db.execute('UPDATE threads SET project_id=? WHERE id=?',('new-project',self.CHILD))
                else:self.add_root(x)
                with self.assertRaises(PolicyError):
                    if moment=='after_adoption':x.a.check_preservation(final=True)
                    else:x.a.ambient.adopt(quiescence=lambda:self.witness(x))
                self.assertFalse(x.a.ambient.open)
        # Unlisted old history remains byte-stable, but is not an opted-in external parent.
        x=self.setup_case(freeze=False);self.external(x,self.OTHER,new_project=False);x.a.freeze_preservation()
        self.external(x,self.CHILD,new_project=False);self.add_root(x);self.challenge(x);self.decision(x,direct_ids=(self.CHILD,))
        self.assertEqual(x.a.ambient.adopt(quiescence=lambda:self.witness(x))['state'],'ambient_delta_accepted')
        self.assertEqual(x.a.check_preservation()['ambient_receipts'],1)

    def test_p6_versions_receipt_bindings_limits_and_nonquiescence_stay_closed(self):
        for key in ('observation_protocol','scope_sha256','baseline_sha256','challenge_sha256','previous_receipt_sha256','unknown'):
            with self.subTest(key=key):
                x=self.direct()
                def change(value):value[key]=2 if key=='observation_protocol' else 'invalid'
                self.decision(x,direct_ids=(self.CHILD,),mutate=change)
                with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        x=self.direct();self.decision(x,direct_ids=(self.CHILD,));x.a.ambient.checkpoints=96
        with self.assertRaises(PolicyError):x.a.ambient.adopt(quiescence=lambda:self.witness(x))
        x=self.setup_case()
        for aid in (self.PARENT,self.CHILD,self.OTHER):self.external(x,aid,new_project=False)
        with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x))
        x=self.setup_case();self.external(x,self.CHILD,new_project=False)
        with self.assertRaises(PolicyError):x.a.check_preservation(quiescence=lambda:self.witness(x,pending_callbacks=1))


if __name__=='__main__':unittest.main()
