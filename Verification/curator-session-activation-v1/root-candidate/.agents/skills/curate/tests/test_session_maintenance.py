"""Actual disposable Git/queue behavior; budget fixtures do not certify a live AI host."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

SOURCE=Path(os.environ['SYS4AI_CURATOR_TEST_SOURCE']).resolve(strict=True)
WORK=Path(os.environ['SYS4AI_CURATOR_TEST_WORK']).resolve(strict=True)
sys.path.insert(0,str(SOURCE/'SKILLS-depo/curate/scripts'))
from curator_session import collect, configuration, dispatch, effective_policy, DEFAULTS
from curator_policy import digest
from curator_queue import DeliveryQueue
from curator_integration import content_hash
from curator_git import LocalGit
NOW='2026-09-12T22:00:00+00:00'
GIT=str(Path(shutil.which('git')).resolve())


def setup(root, *, count=1):
    policy=json.loads((SOURCE/'CURATION-depo/starter/curator.yaml').read_text())
    policy['project'].update(id='session-fixture',coordination_root=str(root))
    (root/'curator.yaml').write_text(json.dumps(policy))
    session=deepcopy(DEFAULTS);session.update(project_id='session-fixture',enabled=True)
    (root/'curator-session.yaml').write_text(json.dumps(session))
    (root/'project.json').write_text(json.dumps({'schema_version':1,'project_id':'session-fixture'}))
    for n in range(count):(root/f'file-{n}.txt').write_text('Original ordinary text.\n')
    def git(*args):subprocess.run([GIT,'-C',str(root),*args],check=True,capture_output=True,timeout=20)
    git('init');git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Initial fixture')
    return session


def tree(root):return {p.relative_to(root).as_posix():content_hash(p.read_bytes()) for p in root.rglob('*') if p.is_file()}


class SessionMaintenanceTests(unittest.TestCase):
    def test_catch_up_reuse_consumption_return_and_opt_out(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);session=setup(root)
            from curator import metadata_status
            from curator_policy import load_policy
            before=tree(root);status=metadata_status(load_policy(root/'curator.yaml'))
            self.assertEqual(status['state'],'installed_session_enabled');self.assertTrue(status['session']['enabled'])
            self.assertIsNone(status['pending']);self.assertFalse(status['runtime_observed']);self.assertEqual(before,tree(root))
            first=collect(root,git_executable=GIT,now=NOW)
            self.assertEqual(first['state'],'pending_owner');self.assertFalse(first['runtime_observed']);self.assertEqual(first['model_calls'],0)
            self.assertEqual(first['transport_writes'],1);self.assertEqual(first['coverage'],'metadata_only')
            second=collect(root,git_executable=GIT,now=NOW)
            self.assertEqual(second['context'],first['context']);self.assertEqual(second['transport_writes'],0)
            self.assertEqual(first['pending'],second['pending'])
            q=DeliveryQueue(root,'session-fixture',first['context']['repository_id']);event=first['events'][0]
            # A fixture owner reference exercises the queue only, not a live AI operation.
            q.record_delivery(event['event_id'],None,receipt_id='fixture-completed',status='consumed',
                reference={'owner':'project','path':'file-0.txt','sha256':content_hash((root/'file-0.txt').read_bytes())},
                reason='Fixture source review completed',created_at=NOW)
            idle=collect(root,git_executable=GIT,now=NOW);self.assertEqual(idle['state'],'idle');self.assertFalse(idle['notify']);self.assertEqual(idle['transport_writes'],0)
            (root/'file-0.txt').write_text('First later edit.\n');changed=collect(root,git_executable=GIT,now=NOW)
            self.assertEqual(changed['pending'],1);self.assertNotEqual(idle['context'],changed['context'])
            (root/'file-0.txt').write_text('Second later edit, same dirty pathname.\n');again=collect(root,git_executable=GIT,now=NOW)
            self.assertNotEqual(again['context'],changed['context']);self.assertEqual(again['pending'],2)
            for name,sha in before.items():
                if name!='file-0.txt':self.assertEqual(sha,content_hash((root/name).read_bytes()),name)
            session['enabled']=False;(root/'curator-session.yaml').write_text(json.dumps(session));frozen=tree(root)
            disabled=collect(root,git_executable=GIT,now=NOW);self.assertEqual(disabled['state'],'disabled');self.assertEqual(frozen,tree(root));self.assertTrue(disabled['preserve_pending'])

    def test_large_layout_metadata_pages_keep_content_validation_pending(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);setup(root,count=160)
            observer=LocalGit(root,GIT,content_hash(Path(GIT).read_bytes()))
            from curator_policy import PolicyError
            with self.assertRaises(PolicyError) as failure:observer.snapshot()
            self.assertEqual(failure.exception.code,'git_descriptor_limit')
            for n in range(72):(root/f'file-{n}.txt').write_text('Ordinary updated document.\n')
            from curator import metadata_status
            from curator_policy import load_policy
            before=tree(root);status=metadata_status(load_policy(root/'curator.yaml'))
            self.assertEqual(status['state'],'installed_session_enabled');self.assertTrue(status['session']['enabled'])
            self.assertIsNone(status['pending']);self.assertFalse(status['runtime_observed']);self.assertEqual(before,tree(root))
            first=collect(root,git_executable=GIT,now=NOW)
            self.assertEqual(first['state'],'pending_owner');self.assertEqual(len(first['changed_paths']),50)
            self.assertEqual(first['changed_path_count'],235);self.assertTrue(first['source_validation_pending'])
            rows=list(first['changed_paths']);page=first
            while page['next_path_offset'] is not None:
                page=collect(root,git_executable=GIT,now=NOW,path_offset=page['next_path_offset'],expected_snapshot=first['context']['snapshot'])
                self.assertEqual(page['transport_writes'],0);self.assertEqual(first['context'],page['context']);rows+=page['changed_paths']
            self.assertEqual(len(rows),235);self.assertEqual(len({x['paths'][0]['path_b64'] for x in rows}),163)
            for name,sha in before.items():self.assertEqual(sha,content_hash((root/name).read_bytes()),name)

    def test_absent_repository_or_zero_budget_never_claims_runtime(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);session=setup(root);shutil.rmtree(root/'.git')
            result=collect(root,git_executable=GIT,now=NOW)
            self.assertEqual(result['state'],'pending');self.assertFalse(result['runtime_observed']);self.assertFalse((root/'control_records').exists())
            session['bounds']['work_seconds']=0;(root/'curator-session.yaml').write_text(json.dumps(session))
            self.assertEqual(collect(root,now=NOW)['reasons'],['budget_exhausted'])

    def test_dispatch_holds_unavailable_and_exhausted_before_owner_route(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);setup(root);ref=root/'file-0.txt'
            cost={'model_calls':1,'work_seconds':1,'candidate_bytes':1,'concurrent_agents':1}
            def reached(*args,**kwargs):raise RuntimeError('selected current-owner route reached')
            app=SimpleNamespace(policy_path=root/'curator.yaml',accepted={'selected':{'automatic':True,'operation':{'cost':cost}}},run=reached)
            obs=dict(policy_sha256=digest(effective_policy(root)),branch='main',observed_at=NOW,pending_since=NOW,last_catch_up=None,last_dependency=None,
                     usage={k:0 for k in cost},iterations=0,iteration_limit=1,runtime_current=False,
                     evidence=[{'root':str(root),'path':ref.name,'sha256':content_hash(ref.read_bytes())}])
            request={'operation_id':'selected'}
            result=dispatch(app,'update',request,root=root,actor='fixture-only',observation=obs,now=NOW)
            self.assertEqual(result['reasons'],['runtime_unavailable'])
            obs['runtime_current']=True;obs['usage']['model_calls']=2
            self.assertEqual(dispatch(app,'update',request,root=root,actor='fixture-only',observation=obs,now=NOW)['reasons'],['budget_exhausted'])
            obs['usage']['model_calls']=0
            with self.assertRaisesRegex(RuntimeError,'current-owner route reached'):dispatch(app,'update',request,root=root,actor='fixture-only',observation=obs,now=NOW)
            obs['iterations']=1
            self.assertEqual(dispatch(app,'update',request,root=root,actor='fixture-only',observation=obs,now=NOW)['reasons'],['budget_exhausted'])
            obs['iterations']=0;app.run=lambda *args,**kwargs:{'state':'held'}
            self.assertTrue(dispatch(app,'update',request,root=root,actor='fixture-only',observation=obs,now=NOW)['notify'])
            app.run=lambda *args,**kwargs:{'state':'completed'}
            self.assertFalse(dispatch(app,'update',request,root=root,actor='fixture-only',observation=obs,now=NOW)['notify'])


if __name__=='__main__':unittest.main()
