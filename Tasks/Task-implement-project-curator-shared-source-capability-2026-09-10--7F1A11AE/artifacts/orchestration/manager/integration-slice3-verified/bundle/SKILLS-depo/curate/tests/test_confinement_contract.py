from pathlib import Path
import os
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


if __name__=='__main__':unittest.main()
