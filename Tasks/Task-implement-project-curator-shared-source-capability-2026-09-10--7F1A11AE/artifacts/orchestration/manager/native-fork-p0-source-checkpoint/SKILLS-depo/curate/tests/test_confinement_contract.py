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
        self.columns=('id','created_at','updated_at','archived','has_user_event','model_provider','model','reasoning_effort','is_pinned','project_id','rollout_path','source')
        self.row={'id':'host-native','created_at':1,'updated_at':2,'archived':0,'has_user_event':0,'model_provider':'openai',
            'model':'gpt-6-astra','reasoning_effort':'xhigh','is_pinned':0,'project_id':None,'rollout_path':str(self.log),'source':'synthetic'}
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE TABLE backfill_state (id INTEGER,status TEXT)');db.execute("INSERT INTO backfill_state VALUES (1,'complete')")
            db.execute('CREATE TABLE threads ('+','.join(name+(' TEXT' if name in ('id','model_provider','model','reasoning_effort','project_id','rollout_path','source') else ' INTEGER') for name in self.columns)+')')
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


if __name__=='__main__':unittest.main()
