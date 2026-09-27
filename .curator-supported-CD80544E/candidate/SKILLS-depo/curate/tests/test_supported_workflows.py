"""Retained ordinary workflows; real local owners plus labelled supplied observations.

No native actor, publication grant or service readiness is synthesized here.
"""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import os

from test_retained_application import SOURCE,WORK,NOW,HASH,context,reference,outcome
from test_supported_application import files,create_task,task_state
from curator_policy import digest,PolicyError
from curator_events import make_event,commit_signal,catch_up_signal
from curator_queue import DeliveryQueue
from curator_preflight import preflight,coalesce
from curator_snapshots import recompute_obligations,empty_checkpoint,advance_checkpoint,current_stages
from curator_causality import obligations_for,stopping_decision
from curator_documentation import route,check_local_links
from curator_learning import disposition
from curator_maintenance import technical
from curator_knowledge import decision,semantic_rebind
from curator_products import plan,next_operation,observe
from curator_awareness import inspect as inspect_awareness
from curator_notices import notice
from curator_handoff import select,retain_original,continue_original
from curator_host_macos import assets,lifecycle,status,MacOSExecutor
from curator_metrics import operational_measures
from curator_git import LocalGit
from curator_workspace import Coordination,logical_identity,copy_candidate
from curator_integration import content_hash


class SupportedWorkflowsTests(unittest.TestCase):
    def test_read_only_document_ownership_and_preflight_routes(self):
        ownership=json.loads((SOURCE/'CURATION-depo/starter/document-ownership.json').read_text())
        samples={'AGENTS.md':b'Project instructions\n','README.md':b'Ordinary factual guide\n',
                 'ONTOLOGY/WIKI/index.md':b'Generated view\n','Tasks/task/responses/response.md':b'Historical observed result\n'}
        routes={}
        for path,raw in samples.items():
            entry=next(x for x in ownership['entries'] if x['path']==path or (x['pattern'] and path.startswith(x['path'].split('*')[0])))
            mapped=deepcopy(entry);mapped.update(path=path,pattern=False,sha256=content_hash(raw))
            selected={'schema_version':1,'entries':[mapped]};identity=dict(id=entry['id'],path=path,sha256=content_hash(raw))
            result=route(selected,identity,[[0,len(raw)]],{path:raw},dict(kind='content',old_path=path,new_path=path,semantic_review=None))
            routes[path]=result['route']
            if entry['class']=='historical':self.assertTrue(result['preserve_original'])
            if entry['class']=='generated':self.assertFalse(result['edit_generated_output'])
            if path=='README.md':
                for kind in ['rename','interface']:
                    review=dict(source_sha256=identity['sha256'],applicable=True)
                    changed=route(selected,identity,[[0,len(raw)]],{path:raw},dict(kind=kind,old_path=path,new_path='Guide.md',semantic_review=review))
                    self.assertEqual(changed['change_kind'],kind)
                for paths,state in [(['unrelated/*'],'idle'),(['README.md'],'ready')]:
                    found=preflight(context(WORK),deltas=[dict(identity=identity,ranges=[[0,len(raw)]])],ownership=selected,snapshot={path:raw},relevant_paths=paths,now=NOW)
                    self.assertEqual(found['state'],state);self.assertTrue(all(v==0 for v in found['counters'].values()))
        self.assertEqual(routes,{'AGENTS.md':'protected.review','README.md':'project.documentation','ONTOLOGY/WIKI/index.md':'ontology.wiki','Tasks/task/responses/response.md':'task.response-correction'})
        missing=route({'schema_version':1,'entries':[]},dict(id='unknown',path='unknown.md',sha256=HASH),[[0,1]],{'unknown.md':b'x'},dict(kind='content',old_path='unknown.md',new_path='unknown.md',semantic_review=None))
        self.assertNotEqual(missing['state'],'proposed')
        ignored=preflight(context(WORK),deltas=[dict(identity=dict(id='cache',path='control_records/curator/cache.json',sha256=HASH),ranges=[[0,1]])],ownership={'schema_version':1,'entries':[]},snapshot={},relevant_paths=['*'],now=NOW)
        self.assertEqual(ignored['state'],'idle')

    def test_actual_role_link_casing_in_disposable_document(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);(root/'Roles/curator').mkdir(parents=True);(root/'Roles/curator/ROLE.md').write_text('Fixture role\n')
            (root/'README.md').write_text('[Role](roles/curator/ROLE.md)\n[Missing](missing.md)\n[External](https://example.invalid/)\n')
            before=files(root);found=check_local_links(root,['README.md'])
            self.assertEqual({x['code'] for x in found['findings']},{'path_casing','missing_link'});self.assertEqual(before,files(root))
            self.assertEqual(found['findings'][0]['actual_path'],'Roles/curator/ROLE.md')
            (root/'README.md').write_text('[Role](Roles/curator/ROLE.md)\n')
            self.assertEqual(check_local_links(root,['README.md'])['state'],'current')

    def test_queue_notices_and_exact_conversational_continuation(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);ctx=context(root);queue=DeliveryQueue(root,ctx['project_id'],ctx['repository_id'])
            policy={'project':{k:ctx[k] for k in ['project_id','repository_id','coordination_root']}};policy['project']['id']=policy['project'].pop('project_id')
            correction=make_event(ctx,'manual_correction','correction',{'request':reference('project')},created_at=NOW)
            queue.enqueue(correction)
            for scope,level in [(['unrelated.txt'],None),(['fixture-observation.json'],'warning')]:
                before=files(root);value=inspect_awareness(root,policy,affected_paths=scope)
                self.assertEqual([n['level'] for n in value['notices']],[] if level is None else [level]);self.assertEqual(before,files(root))
            queue.record_delivery(correction['event_id'],None,receipt_id='held',status='held',reason='Existing owner must complete current work',created_at=NOW)
            value=inspect_awareness(root,policy,affected_paths=['fixture-observation.json']);self.assertEqual(value['state'],'blocked')
            self.assertEqual(value['notices'][0]['level'],'blocker')
            item=dict(id='item',paths=['guide.md'],state='information',impact='Guide meaning changed',action='Inspect guide',meaningful=True,routine_success=False)
            for level in ['information','warning','blocker']:
                row={**item,'state':level};self.assertEqual(notice(row,affected_paths=['guide.md'])['level'],level)
                self.assertIsNone(notice(row,affected_paths=['guide.md'],previous_sha256=digest(row)))
            self.assertIsNone(notice({**item,'routine_success':True},affected_paths=['guide.md']))
            self.assertIsNone(notice(item,affected_paths=['unrelated.txt']))
            self.assertEqual(notice(item,affected_paths=['guide.md'],digest_selected=True)['delivery'],'selected_digest')
            original=dict(objective='Continue original authored report',constraints=['Preserve sources'],task_id=None,execution_id=None,source_refs=[reference('project')],assumptions=['Source current'],authority_sha256=HASH)
            offer=dict(item_id='item',operation_id='maintenance',source_sha256=HASH,authority_sha256=HASH,expires_at='2026-09-13T12:00:00Z',original_work=original)
            for utterance in ['do it','do the task','do so']:
                chosen=select(utterance,[offer],now=NOW,current_sources={'item':HASH},current_authority=HASH)
                self.assertEqual(chosen['state'],'selected');self.assertFalse(chosen['task_activation'])
            self.assertEqual(select('do it',[offer,offer],now=NOW,current_sources={'item':HASH},current_authority=HASH)['state'],'selection_required')
            self.assertEqual(select('do it',[offer],now=NOW,current_sources={'item':'b'*64},current_authority=HASH)['state'],'stale_offer')
            self.assertEqual(select('What is this?',[offer],now=NOW,current_sources={'item':HASH},current_authority=HASH)['state'],'read_only')
            saved=retain_original(original,chosen);kwargs=dict(current_original=original,integrity_current=True,scope_current=True,authority_current=True)
            self.assertEqual(continue_original(saved,maintenance_outcome='completed',**kwargs)['state'],'continuation_ready')
            self.assertEqual(continue_original(saved,maintenance_outcome='blocked',**kwargs)['state'],'held')
            self.assertEqual(continue_original(saved,maintenance_outcome='blocked',maintenance_required=False,**kwargs)['state'],'continuation_ready')
            self.assertEqual(continue_original(saved,maintenance_outcome='completed',**{**kwargs,'current_original':{**original,'assumptions':['Changed source']}})['state'],'held')
            self.assertEqual(continue_original(saved,maintenance_outcome='completed',**{**kwargs,'authority_current':False})['state'],'held')

    def test_learning_disposition_investigation_and_exact_scope(self):
        review=dict(completion_id='review',objective='Fix selected parser',artifact='code/parser.py',source_sha256=HASH,mode='automatic',durable=True,supported=True,cause_established=False,already_repaired=False,remaining_obligations=[])
        value=disposition(review,capture=False);self.assertFalse(value['persist']);self.assertEqual(value['route'],'bounded_investigation')
        self.assertFalse(disposition({**review,'mode':'review'},capture=True)['persist'])
        self.assertTrue(disposition({**review,'mode':'explicit'},capture=False,explicit_save=True)['persist'])
        self.assertEqual(disposition({**review,'already_repaired':True,'remaining_obligations':['documentation']},capture=True)['route'],'remaining_obligations')
        terminal={k:review[k] for k in ['objective','artifact','source_sha256']};terminal.update(state='completed',owner='prior-owner')
        self.assertNotEqual(disposition(review,capture=True,active_work=[terminal])['route'],'current_owner')
        self.assertEqual(disposition(review,capture=True,consumed=[value['completion_identity']])['state'],'unchanged')
        finding=dict(class_='defect',paths=['code/parser.py'],tools=['python-syntax'],cause_established=False,evidence=[reference()],definition_of_done=['Selected parser output verified']);finding['class']=finding.pop('class_')
        accepted=dict(target_sha256=HASH,finding_sha256=digest(finding),cost={'work_seconds':1})
        kwargs=dict(selected_classes=['defect'],selected_paths=['code/*'],selected_tools=['python-syntax'],remaining={'work_seconds':2})
        result=technical(finding,accepted,current_target=HASH,**kwargs);self.assertEqual(result['route'],'bounded_investigation')
        with self.assertRaises(PolicyError):technical(finding,accepted,current_target='b'*64,**kwargs)
        with self.assertRaises(PolicyError):technical(finding,accepted,current_target=HASH,**{**kwargs,'selected_classes':[]})
        with self.assertRaises(PolicyError):technical(finding,accepted,current_target=HASH,**{**kwargs,'remaining':{'work_seconds':0}})
        self.assertEqual(value['benefit'],'unobserved')

    def test_product_recheck_and_unsupported_meaning_stay_pending(self):
        source={'path':'source.md','sha256':HASH}
        finding=dict(memory=True,ontology=True,supported=False,conflicting=False,new_knowledge=True,stale_products=[],sources=[source])
        self.assertEqual(decision(finding)['state'],'held')
        self.assertEqual(decision({**finding,'supported':True,'conflicting':True})['decision'],'neither')
        old={'meaning':'Original'};new={'meaning':'Changed'}
        with self.assertRaises(PolicyError):semantic_rebind(old,new,dict(before_sha256=digest(old),after_sha256=digest(new),meaning_preserved=False,applicability='Meaning changed',evidence=[source]))
        products=[dict(id='compile',route='ontology.compile',required=True,enabled=True,present=False,current=False,input_sha256=HASH,dependencies=[])]
        value=plan(products,HASH)
        with self.assertRaises(PolicyError):next_operation(value,current_snapshot='b'*64,inputs={'compile':HASH})
        with self.assertRaises(PolicyError):next_operation(value,current_snapshot=HASH,inputs={'compile':'b'*64})
        result=observe(value,'compile',input_sha256=HASH,receipt={'path':'owner.json','sha256':HASH},outcome='failed')
        self.assertEqual(result['state'],'pending')
        disabled=plan([{**products[0],'enabled':False}],HASH);self.assertEqual(next_operation(disabled,current_snapshot=HASH,inputs={'compile':HASH})['reason'],'required_product_disabled')

    def test_portable_host_assets_status_and_detached_input(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);executor=MacOSExecutor(home=root);identity=executor.identity(root)
            selection=dict(project_id='fixture',root=str(root),root_identity=identity,python=str(Path(sys.executable).absolute()),script=str(root/'curator.py'),selection_path=str(root/'selection.json'),log_directory=str(root/'logs'),cadence_seconds=60)
            before=files(root);asset=assets(selection);plist=plistlib.loads(asset['bytes']);self.assertFalse(plist['RunAtLoad']);self.assertFalse(asset['installed']);self.assertFalse(asset['hook'])
            base=dict(selected=True,pending=True,volume_available=True,identity_current=True,loaded=True,process_current=True,probe_current=True,owner_current=True)
            for changes,expected in [({},'ready'),({'selected':False},'pending'),({'selected':False,'pending':False},'idle'),({'volume_available':False},'unavailable'),({'identity_current':False},'blocked'),({'process_current':False},'unavailable'),({'probe_current':False},'unavailable')]:
                self.assertEqual(status(**{**base,**changes})['state'],expected)
            missing=lifecycle('uninstall',selection,asset_sha256=asset['sha256'],source_available=False,operation_id='fixture-operation')
            self.assertFalse(missing['deletion']);self.assertTrue(missing['preserve_pending']);self.assertEqual(missing['actions'],[])
            with self.assertRaises(PolicyError):lifecycle('install',selection,asset_sha256=asset['sha256'],observed_identity=identity,operation_id='fixture-operation')
            moved={**selection,'root_identity':[identity[0],identity[1]+1]}
            with self.assertRaises(PolicyError):lifecycle('relocate',moved,asset_sha256=asset['sha256'],observed_identity=identity,operation_id='fixture-operation')
            self.assertEqual(before,files(root))

    def test_known_operational_counts_and_time_attribution(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);target=root/'guide.md';values=[b'First\n',b'Second\n',b'First\n'];transitions=[]
            target.write_bytes(values[0]);started=datetime.now(timezone.utc).isoformat()
            for index,content in enumerate(values[1:]):
                before=content_hash(target.read_bytes());target.write_bytes(content);at=datetime.now(timezone.utc).isoformat()
                transitions.append(dict(reference=reference(),value=dict(operation_id='op-'+str(index),path='guide.md',before_sha256=before,after_sha256=content_hash(content),observed_at=at,protected=False,authorized=True,effect_attributed=True)))
            ended=datetime.now(timezone.utc).isoformat();ctx=context(root)
            event=commit_signal(ctx,'1'*40,created_at=NOW);duplicate=commit_signal(ctx,'1'*40,created_at='2026-09-12T12:00:01Z')
            idle=preflight(ctx,ownership={'schema_version':1,'entries':[]},snapshot={},relevant_paths=[],now=NOW)
            receipt_root=WORK/'metric-sources-v3';receipt_root.mkdir(exist_ok=True)
            def retain(name,value):
                data=json.dumps(value,sort_keys=True).encode();path=receipt_root/(name+'.json');path.write_bytes(data)
                return dict(reference=dict(owner='project',path='metric-sources-v3/'+path.name,sha256=content_hash(data)),value=value)
            transitions=[retain('transition-'+str(i),row['value']) for i,row in enumerate(transitions)]
            observations=dict(transitions=transitions,reconciliation=[retain('reconciliation',dict(operation_id='cycle',started_at=started,reconciled_at=ended))],runtime=[retain('runtime',dict(state=idle['state'],counters=idle['counters']))])
            checkpoint=advance_checkpoint(empty_checkpoint(ctx),'observed',ctx);key=digest('effect')
            before=files(root);measures=operational_measures([event,duplicate],[outcome(key,1),outcome(key,2)],[checkpoint],observations=observations)
            self.assertEqual(measures['observed_reversals'],1);self.assertEqual(measures['duplicate_signals'],1);self.assertEqual(measures['unchanged_repeated_failures'],1)
            self.assertEqual(measures['unresolved_staleness'],1);self.assertEqual(measures['idle_model_calls'],0)
            elapsed=int((datetime.fromisoformat(ended)-datetime.fromisoformat(started)).total_seconds()*1000)
            self.assertEqual(measures['reconciliation_delay_ms'][0]['milliseconds'],elapsed)
            self.assertIn('dependencies',measures['missing_observation_families']);self.assertIsNone(measures['benefit_baseline']);self.assertEqual(before,files(root))
            (WORK/'metric-measures-v3.json').write_text(json.dumps({'observations':observations,'measures':measures,'timing_scope':'Actual two local fixture file transitions; not a deployed service interval.'},indent=2)+'\n')

    def test_actual_rewritten_history_missed_events_and_worktrees(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            workspace=Path(raw);root=workspace/'repo';root.mkdir();executable=Path(shutil.which('git')).resolve()
            env={'PATH':'/usr/bin:/bin','HOME':str(workspace),'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1',
                 'GIT_AUTHOR_NAME':'Fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'Fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'}
            def command(*args):return subprocess.run([str(executable),'-C',str(root),*args],env=env,capture_output=True,check=True).stdout.decode().strip()
            command('init','-b','main');(root/'source.txt').write_text('original\n');(root/'gone.txt').write_text('delete me\n')
            (root/'.gitignore').write_text('Tasks/\ncontrol_records/\n');command('add','.');command('commit','-m','fixture base')
            git=LocalGit(root,executable,content_hash(executable.read_bytes()));base=git.head()['commit']
            def checkpoint():return dict(commit=git.head()['commit'],context={**context(root),'branch':git.head()['branch'],'snapshot':digest(git.snapshot())})
            command('checkout','-b','feature');(root/'feature.txt').write_text('feature\n');command('add','feature.txt');command('commit','-m','fixture feature');before_rebase=checkpoint()
            command('checkout','main');(root/'main.txt').write_text('main\n');command('add','main.txt');command('commit','-m','fixture main')
            command('checkout','feature');command('rebase','main');after_rebase=checkpoint()
            self.assertFalse(git.is_ancestor(before_rebase['commit'],after_rebase['commit']))
            rebase=recompute_obligations(before_rebase,after_rebase,ancestor=False,changes=git.changes(before_rebase['commit'],after_rebase['commit']))
            self.assertIn('rewritten_history',{r['kind'] for r in rebase['obligations']})
            command('checkout','main');command('merge','--squash','feature');command('commit','-m','fixture squash');squashed=checkpoint()
            self.assertFalse(git.is_ancestor(after_rebase['commit'],squashed['commit']))
            command('mv','source.txt','renamed.txt');command('rm','gone.txt');command('commit','-m','fixture rename and deletion');renamed=checkpoint()
            changes=git.changes(squashed['commit'],renamed['commit']);kinds={r['kind'] for r in recompute_obligations(squashed,renamed,ancestor=True,changes=changes)['obligations']}
            self.assertTrue({'rename','deletion','source_changed'}<=kinds)
            ctx=renamed['context'];queue=DeliveryQueue(root,ctx['project_id'],ctx['repository_id'])
            caught=catch_up_signal(ctx,base,renamed['commit'],created_at=NOW);signal=commit_signal(ctx,renamed['commit'],created_at=NOW)
            for event in [signal,caught,signal]:queue.enqueue(event)
            reopened=DeliveryQueue(root,ctx['project_id'],ctx['repository_id']);events=[v['event'] for v in reopened.status()]
            self.assertEqual(len(events),2);self.assertEqual(coalesce(events),coalesce(list(reversed(events))))
            command('branch','pointer',renamed['commit']);command('checkout','pointer');before_force=checkpoint();command('checkout','main');command('branch','-f','pointer',base);command('checkout','pointer');after_force=checkpoint()
            self.assertFalse(git.is_ancestor(before_force['commit'],after_force['commit']))
            self.assertIn('rewritten_history',{x['kind'] for x in recompute_obligations(before_force,after_force,ancestor=False)['obligations']})
            command('checkout','main');linked=workspace/'linked';command('worktree','add','-b','worktree',str(linked))
            other=LocalGit(linked,executable,content_hash(executable.read_bytes()))
            coordination=Coordination(checkout=other,coordination=git,task_owner=task_state,selection=dict(project_id=ctx['project_id'],branch=other.head()['branch'],common=logical_identity(git),coordination_root=str(root)))
            self.assertEqual(coordination.owners(['renamed.txt'])['state'],'clear');self.assertFalse((linked/'Tasks').exists())
            folder,state=create_task(root);(folder/'task.json').write_text('{"schema_version":99}\n')
            self.assertEqual(coordination.owners(['renamed.txt'])['state'],'held')
            independent=workspace/'independent';independent.mkdir()
            subprocess.run([str(executable),'-C',str(independent),'init','-b','main'],env=env,check=True,capture_output=True)
            (independent/'README.md').write_text('independent\n');subprocess.run([str(executable),'-C',str(independent),'add','.'],env=env,check=True,capture_output=True);subprocess.run([str(executable),'-C',str(independent),'commit','-m','fixture independent'],env=env,check=True,capture_output=True)
            separate=LocalGit(independent,executable,content_hash(executable.read_bytes()))
            with self.assertRaises(PolicyError):Coordination(checkout=separate,coordination=git,task_owner=task_state,selection=dict(project_id=ctx['project_id'],branch=separate.head()['branch'],common=logical_identity(git),coordination_root=str(root)))
            (WORK/'git-observations-v3.json').write_text(json.dumps(dict(rebase=rebase,renamed_changes=changes,events=events,force_before=before_force,force_after=after_force),indent=2)+'\n')

    def test_durable_append_and_cursor_interruption_recovery(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);ctx=context(root);queue=DeliveryQueue(root,ctx['project_id'],ctx['repository_id'])
            event=make_event(ctx,'manual_correction','correction',{'request':reference('project')},created_at=NOW)
            actual_replace=os.replace
            def fail_append(src,dst,**kwargs):raise OSError('ordinary interrupted append')
            with patch('curator_queue.os.replace',side_effect=fail_append):
                with self.assertRaises(OSError):queue.enqueue(event)
            reopened=DeliveryQueue(root,ctx['project_id'],ctx['repository_id']);self.assertEqual(reopened.status(),[])
            reopened.enqueue(event)
            def fail_pointer(src,dst,**kwargs):
                if dst=='current.json':raise OSError('ordinary interrupted cursor pointer')
                return actual_replace(src,dst,**kwargs)
            with patch('curator_queue.os.replace',side_effect=fail_pointer):
                with self.assertRaises(OSError):reopened.advance_cursor('consumer','main',None,event['event_id'])
            restarted=DeliveryQueue(root,ctx['project_id'],ctx['repository_id']);before=restarted.cursor('consumer','main')
            self.assertTrue(before['recovery_pending']);self.assertEqual(before['record']['revision'],1)
            recovered=restarted.advance_cursor('consumer','main',None,event['event_id'])
            self.assertEqual(recovered,before['record']);self.assertFalse(restarted.cursor('consumer','main')['recovery_pending'])
            self.assertEqual(len(restarted.status()),1)
            cached=root/'.sys4ai/curator';cached.mkdir(parents=True);(cached/'cache.json').write_text('{}');shutil.rmtree(cached)
            self.assertEqual(restarted.status()[0]['event'],event)
            with self.assertRaises(PolicyError):restarted.enqueue({**event,'schema_version':99})


if __name__=='__main__':unittest.main()
