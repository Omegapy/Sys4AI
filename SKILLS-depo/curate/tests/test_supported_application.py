"""Ordinary supported-owner behavior in disposable local projects.

These checks exercise real public Task, Git, integration and log owners.
They do not establish an operating native session or deployment readiness.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from test_retained_application import SOURCE,WORK,NOW,HASH
sys.path.insert(0,str(SOURCE/'SKILLS-depo/agent-task/scripts'))
import task_state
from curator import Application
from curator_recovery import RecoveryController
from curator_policy import digest,PolicyError,load_policy
from curator_logs import LogService,register_log
from curator_scheduler import validate_observation,due
from curator_git import LocalGit
from curator_workspace import Coordination,logical_identity
from curator_integration import IntegrationOwner,content_hash


def response(summary):
    return dict(work_completed=[summary],verification_evidence=['Ordinary disposable owner observation'],
                user_response_summary=summary,current_summary=summary,next_step='Continue selected fixture',
                blockers=[],open_questions=[],relevant_files=[])


def create_task(root):
    (root/'Tasks').mkdir()
    task_state.command_new(root,root/'Tasks',dict(name='Ordinary retained workflow',
        description='Exercise existing Task lifecycle in a disposable layout.',definition_of_done=['Owner result observed']))
    folder=next((root/'Tasks').glob('Task-*'))
    return folder,task_state.validate_task_folder(folder)[0]


def files(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


class SupportedApplicationTests(unittest.TestCase):
    def test_real_task_pause_restart_and_read_only_application_status(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);folder,state=create_task(root)
            policy=root/'curator.yaml';shutil.copyfile(SOURCE/'CURATION-depo/starter/curator.yaml',policy)
            app=Application(None,policy_path=policy,accepted_operations={},task_owner=task_state,task_folder=folder)
            before=files(root);self.assertFalse(app.status()['paused']);self.assertEqual(before,files(root))
            task_state.response_transaction('pause',root,root/'Tasks',state['task_id'],state['revision'],response('Pause selected work'))
            state=task_state.validate_task_folder(folder)[0];current=RecoveryController(task_state,folder)
            self.assertTrue(current.read()['paused']);self.assertFalse(current.read()['stopping_confirmed'])
            with self.assertRaisesRegex(PolicyError,'holds new operations'):current.gate('update','integration.apply',{'payload':{}})
            before=files(root);current.gate('retry','integration.recover',{'payload':{}});self.assertEqual(before,files(root))
            payload=response('Resume selected work');payload['status_after']='open'
            task_state.response_transaction('record-response',root,root/'Tasks',state['task_id'],state['revision'],payload)
            self.assertFalse(app.status()['paused']);self.assertEqual(task_state.validate_task_folder(folder)[0]['response_count'],2)

    def test_large_log_outgoing_context_and_bounded_followup_query(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);folder,_=create_task(root)
            policy=root/'curator.yaml';shutil.copyfile(SOURCE/'CURATION-depo/starter/curator.yaml',policy)
            path=root/'worker.log';path.write_text('info: ordinary progress '+('x'*190)+'\n'*1)
            with path.open('a') as out:
                for i in range(15000):out.write('info: progress '+str(i)+' '+('x'*190)+'\n')
                out.write('ERROR: renderer stalled after final pass\n')
            self.assertGreater(path.stat().st_size,2000000)
            service=LogService({'worker':register_log(root,'worker.log',format='text')},cursor_key=b'a'*32)
            app=Application(None,policy_path=policy,accepted_operations={},task_owner=task_state,task_folder=folder,log_service=service)
            before=files(root);outgoing=app.log_context('worker');encoded=json.dumps(outgoing).encode()
            self.assertLess(len(encoded),34000);self.assertIn('renderer',encoded.decode())
            self.assertIn('tool_output',outgoing['query']['projections'])
            result=service.query('worker',{'mode':'search','literal':'renderer','projection':'tool_output'})
            self.assertIn('renderer',json.dumps(result));self.assertLess(len(json.dumps(result).encode()),32000)
            self.assertEqual(before,files(root))

    def test_fresh_scheduler_evidence_and_remaining_budget(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);source=root/'usage.json';source.write_text('{"used":1}')
            policy=load_policy(SOURCE/'CURATION-depo/starter/curator.yaml')
            policy['project']=dict(id='fixture',repository_id='fixture',coordination_root=str(root));policy['branches']=['main']
            policy['schedule']=dict(enabled=True,debounce_seconds=1,catch_up_seconds=10,dependency_cadence_seconds=10)
            policy['bounds']=dict(model_calls=5,work_seconds=50,candidate_bytes=5000,concurrent_agents=2)
            obs=dict(policy_sha256=digest(policy),branch='main',observed_at=NOW,pending_since=None,last_catch_up=None,last_dependency=None,
                usage=dict(model_calls=1,work_seconds=5,candidate_bytes=50,concurrent_agents=1),iterations=1,iteration_limit=4,runtime_current=False,
                evidence=[dict(root=str(root),path='usage.json',sha256=content_hash(source.read_bytes()))])
            cost=dict(model_calls=1,work_seconds=5,candidate_bytes=50,concurrent_agents=1)
            before=files(root);view=validate_observation(obs,policy=policy,now=NOW,cost=cost)
            value=due(policy,branch=view['branch'],now=NOW,usage=view['usage'],iterations=view['iterations'],iteration_limit=view['iteration_limit'],runtime_current=False)
            self.assertEqual(value['state'],'unavailable');self.assertTrue(value['preserve_pending']);self.assertEqual(before,files(root))
            with self.assertRaises(PolicyError):validate_observation(obs,policy=policy,now=NOW,cost={**cost,'model_calls':5})
            source.write_text('{"used":2}')
            with self.assertRaises(PolicyError):validate_observation(obs,policy=policy,now=NOW,cost=cost)

    def test_actual_git_rename_branch_history_and_read_only_snapshot(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);git=shutil.which('git')
            def command(*args):
                return subprocess.run([git,'-C',str(root),*args],check=True,capture_output=True,
                    env={'PATH':'/usr/bin:/bin','HOME':str(root),'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1',
                         'GIT_AUTHOR_NAME':'Fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'Fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'}).stdout.decode().strip()
            command('init','-b','main');(root/'old.txt').write_text('baseline\n');command('add','old.txt');command('commit','-m','fixture baseline')
            executable=Path(git).resolve();owner=LocalGit(root,executable,content_hash(executable.read_bytes()))
            first=owner.head()['commit'];command('mv','old.txt','new.txt');command('commit','-m','fixture rename')
            current=owner.head()['commit'];self.assertTrue(owner.is_ancestor(first,current))
            changes=owner.changes(first,current);self.assertEqual(changes[0]['status'],'R100')
            command('checkout','-b','feature');(root/'new.txt').write_text('feature\n');command('add','new.txt');command('commit','-m','fixture feature')
            feature=owner.head();command('checkout','main');self.assertNotEqual(owner.head()['branch'],feature['branch'])
            self.assertFalse(owner.is_ancestor(feature['commit'],owner.head()['commit']))
            (root/'unrelated.txt').write_text('human draft\n');(root/'new.txt').write_text('staged human edit\n');command('add','new.txt')
            before=files(root);snapshot=owner.snapshot();self.assertTrue(snapshot['dirty']);self.assertEqual(before,files(root))

    def test_real_integration_partial_retry_preserves_later_edits(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            workspace=Path(raw);root=workspace/'checkout';root.mkdir();candidate=workspace/'candidate';candidate.mkdir()
            executable=Path(shutil.which('git')).resolve()
            def command(*args):
                return subprocess.run([str(executable),'-C',str(root),*args],check=True,capture_output=True,
                    env={'PATH':'/usr/bin:/bin','HOME':str(workspace),'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1',
                         'GIT_AUTHOR_NAME':'Fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'Fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'}).stdout
            (root/'.gitignore').write_text('control_records/\nTasks/\n')
            (root/'source.txt').write_text('Reviewed requirement\n')
            (root/'parser.py').write_text('value = 1\n');(candidate/'parser.py').write_text('value = 2\n')
            (root/'guide.md').write_text('Version one\n');(candidate/'guide.md').write_text('Version two\n')
            command('init','-b','main');command('add','.');command('commit','-m','fixture baseline')
            (root/'unrelated.txt').write_text('human draft\n');command('add','unrelated.txt')
            control=root/'control_records/curator';(control/'integration').mkdir(parents=True);(control/'integration.lock').touch()
            git=LocalGit(root,executable,content_hash(executable.read_bytes()))
            coordination=Coordination(checkout=git,coordination=git,task_owner=task_state,
                selection=dict(project_id='fixture',branch=git.head()['branch'],common=logical_identity(git),coordination_root=str(root)))
            selected=dict(operation_id='fixture-operation',candidate_root=str(candidate),
                source_refs=[dict(path='source.txt',sha256=content_hash((root/'source.txt').read_bytes()))],
                files=[dict(path=name,before_sha256=content_hash((root/name).read_bytes()),after_sha256=content_hash((candidate/name).read_bytes())) for name in ['parser.py','guide.md']],
                snapshot=git.snapshot(),checks=[dict(owner='python-syntax',path='parser.py')],
                permissions=dict(local_integration=True,commit=False,push=False,merge=False),review_sha256=HASH)
            owner=IntegrationOwner(coordination,{'fixture-operation':selected})
            binding=dict(task_id='disposable-owner-observation',revision=1,execution_id='fixture-execution',generation=1)
            original_index=(root/'.git/index').read_bytes()
            def interrupt(stage):
                if stage=='after_replace_0':raise RuntimeError('ordinary interrupted file publication')
            with self.assertRaisesRegex(RuntimeError,'interrupted'):
                owner.execute({'candidate_id':'fixture-operation'},actor='fixture-owner',task_binding=binding,fault=interrupt)
            journal=control/'integration/fixture-operation.json';self.assertEqual(json.loads(journal.read_text())['state'],'pending')
            (root/'parser.py').write_text('value = 99  # later human edit\n')
            with self.assertRaises(PolicyError):
                owner.execute(dict(candidate_id='fixture-operation',original_operation_id='fixture-operation'),actor='fixture-owner',task_binding=binding,recovering=True)
            self.assertIn('later human edit',(root/'parser.py').read_text())
            # The fixture author explicitly restores its selected candidate to
            # exercise the original retry. The owner never restores this edit.
            (root/'parser.py').write_bytes((candidate/'parser.py').read_bytes())
            result=owner.execute(dict(candidate_id='fixture-operation',original_operation_id='fixture-operation'),actor='fixture-owner',task_binding=binding,recovering=True)
            self.assertEqual(result['state'],'complete');self.assertEqual(result['operation_id'],'fixture-operation')
            self.assertEqual((root/'guide.md').read_bytes(),(candidate/'guide.md').read_bytes());self.assertEqual(original_index,(root/'.git/index').read_bytes())
            self.assertEqual((root/'unrelated.txt').read_text(),'human draft\n')


if __name__=='__main__':unittest.main()
