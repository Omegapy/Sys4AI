"""Behavioral CLI fixtures. Synthetic native receipts are not native evidence."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import test_task_state as legacy
task_state = legacy.task_state
SKILL_ROOT = legacy.SKILL_ROOT


class OrchestrationTests(unittest.TestCase):
    run_cli = legacy.TaskStateTests.run_cli
    response_payload = legacy.TaskStateTests.response_payload
    read_state = legacy.TaskStateTests.read_state
    tree_hash = legacy.TaskStateTests.tree_hash
    maxDiff = None

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name).resolve() / 'project'; self.root.mkdir()
        for name in ('AGENTS.md', 'ROLE.md', 'SOUL.md'): (self.root / name).write_text('# Fixture guidance\n')
        (self.root / 'Tasks').mkdir(); (self.root / 'Tasks/INDEX.md').write_text(task_state.render_index_markdown([], '2026-09-08T00:00:00+00:00'))
        source = SKILL_ROOT.parent / 'manage-subagent-roles'
        shutil.copytree(source, self.root / '.agents/skills/manage-subagent-roles', ignore=shutil.ignore_patterns('__pycache__'))
        role_dir = self.root / 'roles/fixture-role'; role_dir.mkdir(parents=True)
        (role_dir / 'AGENTS.md').write_bytes((source / 'assets/role-bundle/AGENTS.md.template').read_bytes())
        headings = ['Purpose','Suitable tasks','Capabilities','Tasks outside the role','Required Codex skills','Expected inputs','Expected outputs','Working method','Validation responsibilities','Authority limits','Escalation and stopping conditions','Result-reporting contract']
        (role_dir / 'ROLE.md').write_text('---\nname: fixture-role\ndescription: Bounded deterministic test role only.\n---\n\n# Fixture role\n\n' + '\n\n'.join('## '+h+'\n\nUse only the explicit bounded test contract; do not take project authority.' for h in headings)+'\n')
        helper = self.root / '.agents/skills/manage-subagent-roles/scripts/role_catalog.py'
        cp = subprocess.run([sys.executable, str(helper), '--repo-root', str(self.root), 'reindex'], capture_output=True,text=True); self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
        cp = subprocess.run([sys.executable,str(helper),'--repo-root',str(self.root),'list','--format','json'],capture_output=True,text=True); self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
        (self.root / 'catalog.json').write_text(cp.stdout)
        (self.root / 'evidence.txt').write_text('Synthetic deterministic fixture evidence; no actual native execution is claimed.\n')
        self.ev = self.ref('evidence.txt'); self.context = [self.ev]
        self.role = {'name':'fixture-role','agents_path':'roles/fixture-role/AGENTS.md','role_path':'roles/fixture-role/ROLE.md','agents_sha256':self.ref('roles/fixture-role/AGENTS.md')['sha256'],'role_sha256':self.ref('roles/fixture-role/ROLE.md')['sha256'],'catalog':self.ref('catalog.json')}
        self.settings = {'mode':'verified_inheritance','model':None,'effort':None,'evidence':self.context}
        self.runtime = {'tools':['spawn_agent','list_agents','send_message','followup_task','interrupt_agent'],'depth':2,'available_slots':2,'evidence':self.context}
        cp, result = self.run_cli('new',payload={'name':'Orchestration fixture','description':'Deliver the bounded fixture.','definition_of_done':['Delivered and inspected.'],'orchestration_enabled':True})
        self.assertEqual(cp.returncode,0,result); self.folder=Path(result['task_folder']);self.state=self.read_state(self.folder);self.seq=0;self.actor='/root';self.exec_id='execution1';self.generation=1
        self.event('manager.reserve',self.manager_data('manager1'))
        self.event('manager.receipt',{'assignment_id':'manager1','receipt':self.launch('/root/manager1')})
        self.event('manager.activate',{'assignment_id':'manager1','role_reads':self.reads()});self.actor='/root/manager1'

    def tearDown(self): self.temp.cleanup()
    def ref(self, raw): return {'path':raw,'sha256':hashlib.sha256((self.root/raw).read_bytes()).hexdigest()}
    def launch(self,nid):return {'tool':'collaboration.spawn_agent','result':{'task_name':nid}}
    def roster(self,nid,status):return {'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':nid,'agent_status':status}]}}
    def reads(self):return {'agents_sha256':self.role['agents_sha256'],'role_sha256':self.role['role_sha256'],'evidence':'Fixture reports explicit pair read.'}
    def fit(self,writes):return {'objective':'Bounded fixture','capabilities':['focused verification'],'reads':['evidence.txt'],'writes':writes,'deliverable':'Evidence artifact','tools':['native collaboration'],'skills':[],'authority':'Only fixture writes','risk':'Disposable fixture','stop':'Return the artifact','rationale':'This test role fits focused checks.'}
    def manager_data(self,aid):return {'assignment_id':aid,'role':self.role,'fit':self.fit([]),'runtime':self.runtime,'settings':self.settings,'context':self.context,'source_refs':self.context,'authority':'Explicit fixture work','bootstrap_receipt':self.roster('/root','running')}
    def event(self,kind,data,*,fail=None,actor=None,fault=None,event_id=None,generation=None):
        self.seq+=1
        event={'event_id':event_id or f'event{self.seq}','actor':actor or self.actor,'execution_id':self.exec_id,'generation':self.generation if generation is None else generation,'kind':kind,'data':data}
        cp,res=self.run_cli('orchestrate',self.state['task_id'],'--expected-revision',str(self.state['revision']),payload={'event':event,'response':self.response_payload(self.state)},fault=fault)
        self.state=self.read_state(self.folder)
        if fail:self.assertNotEqual(cp.returncode,0,res);self.assertEqual(res['errors'][0]['code'],fail,res)
        else:self.assertEqual(cp.returncode,0,res)
        return res,event
    def base(self,category='generic',implementation=True,dependencies=None):
        if category=='generic': slots=[{'slot':'worker','function':'worker','perspective':'execute','solver_slot':None}]
        else:
            slots=[{'slot':'solver1','function':'solver','perspective':'direct','solver_slot':None},{'slot':'solver2','function':'solver','perspective':'inverse','solver_slot':None},{'slot':'senior','function':'senior','perspective':'fusion','solver_slot':None}]
            if category=='extra-complex':slots += [{'slot':'reviewer1','function':'reviewer','perspective':'review direct','solver_slot':'solver1'},{'slot':'reviewer2','function':'reviewer','perspective':'review inverse','solver_slot':'solver2'}]
            if implementation:slots += [{'slot':'implementer','function':'implementer','perspective':'implement accepted proposal','solver_slot':None}]
        return {'objective':'Deliver bounded result','requirements':['REQ-fixture'],'inputs':self.context,'dependencies':dependencies or [],'criteria':['Subtask done.'],'category':category,'rationale':'Fixture exercises the chosen workflow.','reads':['evidence.txt'],'writes':['output'],'protected':['evidence.txt'],'authority':'Fixture only','implementation_required':implementation,'deliverable':'Result and evidence','stop':'Return result','slots':slots}
    def define(self,category='generic',implementation=True,sid='subtask1',dependencies=None):
        b=self.base(category,implementation,dependencies);self.event('subtask.define',{'subtask_id':sid,'baseline':b});return b
    def assignment_data(self,aid,slot,sid='subtask1'):
        o=self.state['orchestration'];st=o['subtasks'][sid]
        slot_record=next(x for x in st['baseline']['slots'] if x['slot']==slot);function=slot_record['function']
        writes=['output'] if function in ('worker','implementer') else [str(self.folder.relative_to(self.root)/'artifacts/orchestration/work'/aid)]
        context=self.context+[{'path':str(self.folder.relative_to(self.root)/'artifacts/orchestration'/('baseline_'+st['digest']+'.json')),'sha256':st['digest']}]
        current=[c for c in o['candidates'].values() if o['assignments'][c['assignment_id']]['subtask_id']==sid and c['baseline']==st['digest'] and c['round']==st['round'] and not any(n['supersedes']==c['candidate_id'] for n in o['candidates'].values())]
        artifacts=[]
        if function=='reviewer':artifacts=[c['artifact_id'] for c in current if o['assignments'][c['assignment_id']]['slot']==slot_record['solver_slot']]
        if function=='senior':
            artifacts=[c['artifact_id'] for c in current]
            artifacts += [review['findings'] for review in o['reviews'].values() if review['candidate_id'] in {c['candidate_id'] for c in current} and review['outcome']=='passed' and review['round']==st['round']]
        if function=='implementer':
            accepted=[e['data']['acceptance_id'] for e in o['events'] if e['kind']=='acceptance.record']
            if accepted:artifacts=[o['syntheses'][o['acceptances'][accepted[-1]]['synthesis_id']]['artifact_id']]
        artifacts += [o['conflicts'][cid]['explanation'] for cid in st['active_conflicts']]
        for ar in artifacts:context.append({'path':str(self.folder.relative_to(self.root)/o['artifacts'][ar]['path']),'sha256':o['artifacts'][ar]['sha256']})
        return {'assignment_id':aid,'subtask_id':sid,'slot':slot,'role':self.role,'fit':self.fit(writes),'runtime':self.runtime,'settings':self.settings,'context':context}
    def rebind(self,aid):
        a=self.state['orchestration']['assignments'][aid];d=self.assignment_data(aid,a['slot'],a['subtask_id']);st=self.state['orchestration']['subtasks'][a['subtask_id']]
        if a['baseline']==st['digest'] and a['round']==st['round'] and a['context']==d['context']:return
        self.event('assignment.inputs',{'assignment_id':aid,'role':d['role'],'fit':d['fit'],'runtime':d['runtime'],'context':d['context'],'receipt':{'tool':'collaboration.followup_task','native_id':a['native_id'],'artifact_sha256s':sorted({r['sha256'] for r in d['context']}),'evidence':'Fixture input handoff retains the exact native identity and every current digest.'},'reason':'Current candidate or baseline requires this explicit input handoff.'})
    def assign(self,aid,slot,sid='subtask1'):
        self.event('assignment.reserve',self.assignment_data(aid,slot,sid));self.event('assignment.receipt',{'assignment_id':aid,'receipt':self.launch('/root/manager1/'+aid)});self.event('assignment.reads',{'assignment_id':aid,'role_reads':self.reads()})
    def artifact(self,aid,artifact_id,content='fixture artifact'):
        a=self.state['orchestration']['assignments'][aid];raw=a['fit']['writes'][0]+'/'+artifact_id+'.txt';p=self.root/raw;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
        self.event('artifact.register',{'artifact_id':artifact_id,'assignment_id':aid,'source_path':raw});return artifact_id
    def candidate(self,aid,cid,*,supersedes=None,revalidation=None):
        self.rebind(aid)
        ar=self.artifact(aid,'artifact_'+cid,cid);s=self.state['orchestration']['subtasks']['subtask1']
        self.event('candidate.record',{'candidate_id':cid,'assignment_id':aid,'artifact_id':ar,'baseline':s['digest'],'round':s['round'],'supersedes':supersedes,'findings':'Addressed requested changes.' if supersedes else None,'revalidation':revalidation});return cid
    def observe(self,aid,status='completed'):
        self.event('assignment.observe',{'assignment_id':aid,'receipt':self.roster(self.state['orchestration']['assignments'][aid]['native_id'],status),'changes':self.context})
    def review(self,aid,cid,rid,outcome='passed'):
        self.rebind(aid)
        ar=self.artifact(aid,'artifact_'+rid,rid);s=self.state['orchestration']['subtasks']['subtask1']
        self.event('review.record',{'review_id':rid,'assignment_id':aid,'candidate_id':cid,'baseline':s['digest'],'round':s['round'],'outcome':outcome,'findings':ar})
    def synthesis(self,cids,rids=(),synid='synthesis1'):
        self.rebind('senior1')
        self.artifact('senior1','artifact_'+synid,'Coherent synthesis');s=self.state['orchestration']['subtasks']['subtask1']
        d={'synthesis_id':synid,'assignment_id':'senior1','candidate_ids':cids,'review_ids':list(rids),'baseline':s['digest'],'round':s['round'],'artifact_id':'artifact_'+synid,'resolved_conflicts':list(s['active_conflicts']),'dispositions':{'retained':['All compatible contributions'],'omitted':[],'differences':{x:'No unresolved differences.' for x in ['complementary','terminology','scope','evidence','exclusive']},'assumptions':['Consistent'],'interfaces':['Compatible'],'requirements':['REQ-fixture'],'risks':[],'verification':['Inspect result'],'unresolved':[]}}
        self.event('synthesis.record',d);self.event('acceptance.record',{'acceptance_id':'accept_'+synid,'synthesis_id':synid,'inspection':self.context});return d
    def result(self,aid,ar,acceptance=None):
        s=self.state['orchestration']['subtasks']['subtask1']
        d={'result_id':'result1','assignment_id':aid,'baseline':s['digest'],'round':s['round'],'acceptance_id':acceptance,'artifact_ids':[ar],'changes':self.context,'checks':self.context,'limitations':[]}
        self.event('result.record',d)
    def verify(self,result='result1',acceptance=None,artifacts=None):
        s=self.state['orchestration']['subtasks']['subtask1']; self.event('subtask.verify',{'subtask_id':'subtask1','baseline':s['digest'],'round':s['round'],'result_id':result,'acceptance_id':acceptance,'artifacts':artifacts or ['deliverable'],'criteria':[{'criterion':'Subtask done.','evidence':'Direct fixture inspection.'}],'inspection':self.context})

    def test_legacy_and_v2_read_only_and_strict_keys(self):
        before=self.tree_hash();cp,res=self.run_cli('validate');self.assertEqual(cp.returncode,0,res);self.assertEqual(before,self.tree_hash())
        for malformed in [True,3,'2']:
            state=copy.deepcopy(self.state);state['schema_version']=malformed
            self.assertTrue(task_state.validate_state_shape(state,self.folder,task_state.json_text(state)))
        state=copy.deepcopy(self.state);state['orchestration']['typo']=1;self.assertTrue(task_state.validate_state_shape(state,self.folder,task_state.json_text(state)))
    def test_writer_generation_and_indirect_completion(self):
        self.event('block',{'reason':'test','next_step':'resolve'},actor='/root',fail='ORCH_WRITER')
        self.event('block',{'reason':'test','next_step':'resolve'},generation=0,fail='ORCH_STALE_GENERATION')
        body=self.response_payload(self.state,completion=True);body.update(actor=self.actor,execution_id=self.exec_id,generation=1)
        cp,res=self.run_cli('record-response',self.state['task_id'],'--expected-revision',str(self.state['revision']),payload=body);self.assertEqual(res['errors'][0]['code'],'ORCH_COMPLETION')
        cp,res=self.run_cli('rebuild-projections',self.state['task_id']);self.assertEqual(res['errors'][0]['code'],'ORCH_STALE_GENERATION')
    def test_duplicate_manager_and_reconnect(self):
        self.event('manager.reserve',self.manager_data('other'),fail='ORCH_DUPLICATE_MANAGER')
        self.event('manager.reconnect',{'assignment_id':'manager1','receipt':self.roster(self.actor,'running')})
        self.event('manager.reconnect',{'assignment_id':'manager1','receipt':self.roster(self.actor,'completed')},fail='ORCH_MANAGER_NOT_LIVE')
    def test_native_role_and_settings_substitution(self):
        self.define();d=self.assignment_data('worker1','worker');d['role']=copy.deepcopy(self.role);d['role']['role_sha256']='0'*64
        self.event('assignment.reserve',d,fail='ORCH_ROLE_CHANGED')
        d=self.assignment_data('worker1','worker');d['settings']=copy.deepcopy(self.settings);d['settings']['mode']='unverified';self.event('assignment.reserve',d,fail='ORCH_SETTINGS')
        self.event('assignment.reserve',self.assignment_data('worker1','worker'))
        self.event('assignment.receipt',{'assignment_id':'worker1','receipt':self.launch('fixture-role')},fail='ORCH_NATIVE_ID')
        self.event('assignment.uncertain',{'assignment_id':'worker1','reason':'Native response lost.'})
        self.event('assignment.reserve',self.assignment_data('worker2','worker'),fail='ORCH_SLOT_OWNER')
    def test_counts_dependencies_and_scope(self):
        b=self.base('complex');b['slots']=[b['slots'][0]];self.event('subtask.define',{'subtask_id':'bad','baseline':b},fail='ORCH_TEAM')
        b=self.base(dependencies=['missing']);self.event('subtask.define',{'subtask_id':'bad','baseline':b},fail='ORCH_DEPENDENCY')
        self.define();self.define(sid='subtask2',dependencies=['subtask1'])
        d=self.assignment_data('worker2','worker','subtask2');self.event('assignment.reserve',d,fail='ORCH_DEPENDENCY_PENDING')
        b=self.base(dependencies=['subtask2']);self.event('subtask.revise',{'subtask_id':'subtask1','baseline':b,'reason':'cycle'},fail='ORCH_DEPENDENCY_CYCLE')
        self.assign('worker1','worker');self.define(sid='subtask3');self.event('assignment.reserve',self.assignment_data('worker3','worker','subtask3'),fail='ORCH_WRITE_OVERLAP')
    def test_generic_delivered_work_and_completion(self):
        self.define();self.assign('worker1','worker');self.artifact('worker1','deliverable');self.result('worker1','deliverable');self.observe('worker1');self.verify()
        self.event('execution.finish',{'outcome':'delivered','criteria':[{'criterion':'Delivered and inspected.','evidence':'Integration fixture passed.'}],'inspection':self.context})
        body=self.response_payload(self.state,completion=True);body.update(actor=self.actor,execution_id=self.exec_id,generation=1)
        cp,res=self.run_cli('complete',self.state['task_id'],'--expected-revision',str(self.state['revision']),payload=body);self.assertEqual(cp.returncode,0,res)
    def test_complex_accepted_analysis(self):
        self.define('complex',False);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.candidate('solver2','candidate2');self.assign('senior1','senior');self.synthesis(['candidate1','candidate2'])
        for a in ['solver1','solver2','senior1']:self.observe(a)
        self.verify(result=None,acceptance='accept_synthesis1',artifacts=['artifact_synthesis1'])
    def test_missing_required_candidate_blocks_senior(self):
        self.define('complex',False);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.event('assignment.reserve',self.assignment_data('senior1','senior'),fail='ORCH_REQUIRED_CANDIDATE')
    def test_extra_complex_rejection_revision_and_current_pass(self):
        self.define('extra-complex',False)
        for x in ['solver1','solver2']:self.assign(x,x)
        self.candidate('solver1','candidate1');self.candidate('solver2','candidate2')
        for x in ['reviewer1','reviewer2']:self.assign(x,x)
        self.review('reviewer1','candidate1','review1','rejected');self.review('reviewer2','candidate2','review2')
        self.event('assignment.reserve',self.assignment_data('senior1','senior'),fail='ORCH_REVIEW_GATE')
        self.candidate('solver1','candidate1v2',supersedes='candidate1');self.review('reviewer1','candidate1v2','review1v2');self.assign('senior1','senior');self.synthesis(['candidate1v2','candidate2'],['review1v2','review2'])
    def test_byte_edit_invalidates_accepted_synthesis(self):
        self.define('complex',False);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.candidate('solver2','candidate2');self.assign('senior1','senior');self.synthesis(['candidate1','candidate2'])
        p=self.folder/self.state['orchestration']['artifacts']['artifact_candidate1']['path'];p.write_text('edited under same filename')
        self.event('acceptance.record',{'acceptance_id':'bad','synthesis_id':'synthesis1','inspection':self.context},fail='ORCH_ARTIFACT_CHANGED')
    def test_stop_blocks_dispatch_and_requires_observation(self):
        self.define();self.assign('worker1','worker');self.event('stop.request',{'reason':'Pause requested','action':'pause'})
        self.event('stop.finish',{'reason':'done'},fail='ORCH_STOP_UNCONFIRMED')
        self.event('assignment.observe',{'assignment_id':'worker1','receipt':self.roster('/root/notworker','completed'),'changes':[]},fail='ORCH_NATIVE_UNCONFIRMED')
        self.observe('worker1','interrupted');self.event('stop.finish',{'reason':'Confirmed stopped'})
        self.event('assignment.reserve',self.assignment_data('worker2','worker'),fail='ORCH_DISPATCH_STOPPED')
    def test_replay_and_stale_revision(self):
        self.define();before=self.state['revision'];res,event=self.event('block',{'reason':'A specific evidence gap','next_step':'Obtain it'})
        self.event('block',event['data'],event_id=event['event_id'],fail='ORCH_DUPLICATE_EVENT')
        cp,res=self.run_cli('record-response',self.state['task_id'],'--expected-revision',str(before),payload=self.response_payload(self.state));self.assertEqual(res['errors'][0]['code'],'REVISION_CONFLICT')
    def test_artifact_partial_publication_recovery(self):
        self.define();self.assign('worker1','worker');raw='output/result.txt';(self.root/'output').mkdir();(self.root/raw).write_text('result')
        res,event=self.event('artifact.register',{'artifact_id':'result','assignment_id':'worker1','source_path':raw},fault='after_artifact_publish',fail='TRANSACTION_INCOMPLETE')
        err=res['errors'][0];details=err.get('details',{})
        operation=err.get('operation_id') or res.get('operation_id');self.assertTrue(operation,res)
        cp,out=self.run_cli('reconcile',self.state['task_id'],'--expected-revision',str(self.state['revision']),payload={'repair_type':'transaction','operation_id':operation,'actor':self.actor,'execution_id':self.exec_id,'generation':1});self.assertEqual(cp.returncode,0,out)
        self.state=self.read_state(self.folder);self.assertIn('result',self.state['orchestration']['artifacts'])
        self.event('artifact.register',event['data'],event_id=event['event_id'],fail='ORCH_DUPLICATE_EVENT')


    def test_common_packet_and_queued_independence_gate(self):
        self.define('complex',False)
        d=self.assignment_data('solver1','solver1');d['context']=self.context
        self.event('assignment.reserve',d,fail='ORCH_COMMON_PACKET')
        self.assign('solver1','solver1')
        a=self.state['orchestration']['assignments']['solver1'];raw=a['fit']['writes'][0]+'/early.txt';p=self.root/raw;p.parent.mkdir(parents=True);p.write_text('early result')
        self.event('artifact.register',{'artifact_id':'early','assignment_id':'solver1','source_path':raw},fail='ORCH_INDEPENDENT_DISPATCH')
    def test_bootstrap_recovery_replacement_rejects_unconfirmed_and_old_generation(self):
        self.define();self.assign('worker1','worker')
        d={'reason':'User authorized stopped-manager replacement.','user_authorized':True,'observations':[{'assignment_id':'manager1','receipt':self.roster('/root/manager1','completed'),'changes':self.context}]}
        self.event('manager.replace',d,actor='/root',fail='ORCH_RECOVERY_OWNER')
        d['observations'].append({'assignment_id':'worker1','receipt':self.roster('/root/manager1/worker1','interrupted'),'changes':self.context})
        self.event('manager.replace',d,actor='/root');self.generation=2;self.actor='/root'
        self.event('manager.reserve',self.manager_data('manager2'))
        self.event('manager.receipt',{'assignment_id':'manager2','receipt':self.launch('/root/manager2')})
        self.event('manager.activate',{'assignment_id':'manager2','role_reads':self.reads()});self.actor='/root/manager2'
        self.event('block',{'reason':'late old result','next_step':'reject'},generation=1,actor='/root/manager1',fail='ORCH_STALE_GENERATION')
    def test_task_and_subtask_baseline_changes_invalidate_current_results(self):
        self.define();self.assign('worker1','worker');self.artifact('worker1','deliverable');self.result('worker1','deliverable');self.observe('worker1');self.verify()
        body=self.response_payload(self.state,updates={'definition_of_done':['Revised current criterion.']});body.update(actor=self.actor,execution_id=self.exec_id,generation=1)
        cp,res=self.run_cli('update',self.state['task_id'],'--expected-revision',str(self.state['revision']),payload=body);self.assertEqual(cp.returncode,0,res);self.state=self.read_state(self.folder)
        d={'outcome':'delivered','criteria':[{'criterion':'Revised current criterion.','evidence':'claim'}],'inspection':self.context}
        self.event('execution.finish',d,fail='ORCH_TASK_BASELINE')
        b=self.base();b['criteria']=['Changed subtask criterion.'];self.event('subtask.revise',{'subtask_id':'subtask1','baseline':b,'reason':'Task requirement changed.'})
        st=self.state['orchestration']['subtasks']['subtask1'];self.event('subtask.verify',{'subtask_id':'subtask1','baseline':st['digest'],'round':st['round'],'result_id':'result1','acceptance_id':None,'artifacts':['deliverable'],'criteria':[{'criterion':'Changed subtask criterion.','evidence':'claim'}],'inspection':self.context},fail='ORCH_RESULT_BASELINE')
    def test_conflict_delivery_and_re_review_gate(self):
        self.define('extra-complex',False)
        for x in ['solver1','solver2']:self.assign(x,x)
        self.candidate('solver1','candidate1');self.candidate('solver2','candidate2')
        for x in ['reviewer1','reviewer2']:self.assign(x,x)
        self.review('reviewer1','candidate1','review1');self.review('reviewer2','candidate2','review2');self.assign('senior1','senior')
        self.artifact('senior1','conflictbytes','One exact shared conflict explanation');st=self.state['orchestration']['subtasks']['subtask1']
        self.event('conflict.record',{'conflict_id':'conflict1','assignment_id':'senior1','candidate_ids':['candidate1','candidate2'],'baseline':st['digest'],'round':st['round'],'explanation':'conflictbytes','progress':'Targeted opposing interface correction.'})
        for slot in ['solver1','solver2']:
            self.event('conflict.deliver',{'conflict_id':'conflict1','solver_slot':slot,'receipt':{'native_id':'/root/manager1/'+slot,'explanation_sha256':self.state['orchestration']['artifacts']['conflictbytes']['sha256'],'evidence':'Native message acknowledged the exact explanation.'}})
        self.rebind('solver1');self.rebind('solver2')
        self.candidate('solver1','candidate1v2',supersedes='candidate1');self.candidate('solver2','candidate2v2',supersedes='candidate2',revalidation='Unaffected solution revalidated under shared conflict.')
        self.review('reviewer1','candidate1v2','review1v2')
        st=self.state['orchestration']['subtasks']['subtask1'];d={'conflict_id':'retry','assignment_id':'senior1','candidate_ids':['candidate1v2','candidate2v2'],'baseline':st['digest'],'round':st['round'],'explanation':'conflictbytes','progress':'Another targeted correction.'}
        self.event('assignment.inputs',{'assignment_id':'senior1','role':self.role,'fit':self.fit(self.state['orchestration']['assignments']['senior1']['fit']['writes']),'runtime':self.runtime,'context':self.assignment_data('senior1','senior')['context'],'receipt':{'tool':'collaboration.followup_task','native_id':'/root/manager1/senior1','artifact_sha256s':sorted({r['sha256'] for r in self.assignment_data('senior1','senior')['context']}),'evidence':'Try current input packet.'},'reason':'Retry synthesis input'},fail='ORCH_REVIEW_GATE')
        self.review('reviewer2','candidate2v2','review2v2');self.synthesis(['candidate1v2','candidate2v2'],['review1v2','review2v2'])
    def test_dedicated_implementation_binds_exact_acceptance(self):
        self.define('complex',True);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.candidate('solver2','candidate2');self.assign('senior1','senior');self.synthesis(['candidate1','candidate2']);self.assign('implementer1','implementer');self.artifact('implementer1','deliverable');self.result('implementer1','deliverable','accept_synthesis1')
        for aid in ['solver1','solver2','senior1','implementer1']:self.observe(aid)
        self.verify()
    def test_legacy_upgrade_retains_bytes_and_read_only_preview(self):
        cp,r=self.run_cli('new',payload={'name':'Legacy fixture','description':'Preserved legacy objective.','definition_of_done':['Legacy criterion.']});self.assertEqual(cp.returncode,0,r);folder=Path(r['task_folder']);state=self.read_state(folder);original=(folder/'task.json').read_bytes()
        before=self.tree_hash();cp,preview=self.run_cli('upgrade-preview',state['task_id']);self.assertEqual(cp.returncode,0,preview);self.assertEqual(before,self.tree_hash())
        body=self.response_payload(state,authorized=True);body['legacy_sha256']=preview['sha256']
        cp,r=self.run_cli('upgrade-orchestration',state['task_id'],'--expected-revision','1',payload=body);self.assertEqual(cp.returncode,0,r);after=self.read_state(folder);self.assertEqual(after['schema_version'],2);self.assertEqual(after['task_id'],state['task_id']);self.assertIsNone(after['orchestration']['execution_id']);self.assertEqual((folder/'artifacts/orchestration'/('legacy-v1-'+preview['sha256']+'.json')).read_bytes(),original)
    def test_post_commit_recovery_rejects_same_revision_changed_state(self):
        res,event=self.event('block',{'reason':'Known bounded blocker','next_step':'Obtain evidence'},fault='after_state_publish',fail='TRANSACTION_INCOMPLETE')
        operation=res['errors'][0]['operation_id'];intent=json.loads((self.root/'Tasks/.tmp'/f'{operation}.json').read_text());state=self.read_state(self.folder);state['current_summary']='Different bytes at the same revision.';(self.folder/'task.json').write_text(task_state.json_text(task_state.canonical_state(state)))
        cp,r=self.run_cli('reconcile',self.state['task_id'],'--expected-revision',str(intent['expected_revision']),payload={'repair_type':'transaction','operation_id':operation,'actor':self.actor,'execution_id':self.exec_id,'generation':1});self.assertEqual(r['errors'][0]['code'],'ORCH_RECOVERY_STATE_HASH')
    def test_reopen_retains_prior_execution_history(self):
        self.define();self.assign('worker1','worker');self.artifact('worker1','deliverable');self.result('worker1','deliverable');self.observe('worker1');self.verify();self.event('execution.finish',{'outcome':'delivered','criteria':[{'criterion':'Delivered and inspected.','evidence':'Done'}],'inspection':self.context})
        body=self.response_payload(self.state,completion=True);body.update(actor=self.actor,execution_id=self.exec_id,generation=1);cp,r=self.run_cli('complete',self.state['task_id'],'--expected-revision',str(self.state['revision']),payload=body);self.assertEqual(cp.returncode,0,r);self.state=self.read_state(self.folder)
        body=self.response_payload(self.state,authorized=True);body.update(actor='/root',execution_id=self.exec_id,generation=1,reconciliation=[{'assignment_id':'manager1','receipt':self.roster('/root/manager1','completed'),'changes':self.context}])
        cp,r=self.run_cli('reopen',self.state['task_id'],'--expected-revision',str(self.state['revision']),payload=body);self.assertEqual(cp.returncode,0,r);self.state=self.read_state(self.folder);self.exec_id='execution2';self.actor='/root';self.event('manager.reserve',self.manager_data('manager2'));self.assertEqual(self.state['orchestration']['history'][0]['execution_id'],'execution1')


    def test_reclassified_completed_generic_worker_cannot_bypass_new_team(self):
        self.define();self.assign('worker1','worker');self.artifact('worker1','deliverable');self.observe('worker1')
        self.event('subtask.revise',{'subtask_id':'subtask1','baseline':self.base('complex',True),'reason':'Material uncertainty now requires independent solutions.'})
        st=self.state['orchestration']['subtasks']['subtask1'];d={'result_id':'bypass','assignment_id':'worker1','acceptance_id':None,'baseline':st['digest'],'round':st['round'],'artifact_ids':['deliverable'],'changes':self.context,'checks':self.context,'limitations':[]}
        self.event('result.record',d,fail='ORCH_ASSIGNMENT_BASELINE')
        a=self.state['orchestration']['assignments']['worker1'];self.event('assignment.inputs',{'assignment_id':'worker1','role':self.role,'fit':a['fit'],'runtime':self.runtime,'context':self.context,'receipt':{'tool':'collaboration.followup_task','native_id':a['native_id'],'artifact_sha256s':[self.ev['sha256']],'evidence':'Attempt to retain incompatible worker.'},'reason':'Attempt incompatible rebind'},fail='ORCH_ASSIGNMENT_BASELINE')
    def test_reviewer_and_senior_dispatch_require_exact_candidate_inputs(self):
        self.define('extra-complex',False);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.candidate('solver2','candidate2')
        d=self.assignment_data('reviewer1','reviewer1');d['context']=d['context'][:2];self.event('assignment.reserve',d,fail='ORCH_INPUT_PACKET')
        for aid in ['reviewer1','reviewer2']:self.assign(aid,aid)
        self.review('reviewer1','candidate1','review1');self.review('reviewer2','candidate2','review2')
        d=self.assignment_data('senior1','senior');d['context']=d['context'][:2];self.event('assignment.reserve',d,fail='ORCH_INPUT_PACKET')
    def test_changed_review_findings_invalidates_accepted_synthesis(self):
        self.define('extra-complex',False);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.candidate('solver2','candidate2')
        for aid in ['reviewer1','reviewer2']:self.assign(aid,aid)
        self.review('reviewer1','candidate1','review1');self.review('reviewer2','candidate2','review2');self.assign('senior1','senior');self.synthesis(['candidate1','candidate2'],['review1','review2'])
        (self.folder/self.state['orchestration']['artifacts']['artifact_review1']['path']).write_text('Changed reviewed evidence.')
        self.event('acceptance.record',{'acceptance_id':'tampered','synthesis_id':'synthesis1','inspection':self.context},fail='ORCH_ARTIFACT_CHANGED')
    def test_implementer_context_and_reserved_acceptance_are_exact(self):
        self.define('complex',True);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.candidate('solver2','candidate2');self.assign('senior1','senior');self.synthesis(['candidate1','candidate2'])
        d=self.assignment_data('implementer1','implementer');d['context']=d['context'][:2];self.event('assignment.reserve',d,fail='ORCH_INPUT_PACKET')
        self.assign('implementer1','implementer');self.assertEqual(self.state['orchestration']['assignments']['implementer1']['acceptance_id'],'accept_synthesis1');self.artifact('implementer1','deliverable');self.observe('implementer1');self.synthesis(['candidate1','candidate2'],synid='synthesis2')
        st=self.state['orchestration']['subtasks']['subtask1'];d={'result_id':'wrong_target','assignment_id':'implementer1','acceptance_id':'accept_synthesis2','baseline':st['digest'],'round':st['round'],'artifact_ids':['deliverable'],'changes':self.context,'checks':self.context,'limitations':[]}
        self.event('result.record',d,fail='ORCH_STALE_ACCEPTANCE')
    def test_compatible_baseline_rebind_preserves_native_identity(self):
        self.define();self.assign('worker1','worker');self.observe('worker1');b=self.base();b['criteria']=['Changed criterion.'];self.event('subtask.revise',{'subtask_id':'subtask1','baseline':b,'reason':'User clarified the same bounded generic work.'})
        self.rebind('worker1');a=self.state['orchestration']['assignments']['worker1'];self.assertEqual(a['native_id'],'/root/manager1/worker1');self.assertEqual(a['baseline'],self.state['orchestration']['subtasks']['subtask1']['digest']);self.assertEqual(a['round'],2)
    def test_rejected_solver_rebind_retains_provenance_while_checking_analysis_dependency(self):
        self.define('complex',False);self.assign('solver1','solver1');self.assign('solver2','solver2')
        self.candidate('solver1','candidate1');self.candidate('solver2','candidate2');self.assign('senior1','senior');self.synthesis(['candidate1','candidate2'])
        for aid in ['solver1','solver2','senior1']:self.observe(aid)
        self.verify(result=None,acceptance='accept_synthesis1',artifacts=['artifact_synthesis1'])
        self.define('extra-complex',False,sid='coding',dependencies=['subtask1'])
        for aid,slot in [('coding_a','solver1'),('coding_b','solver2')]:self.assign(aid,slot,'coding')
        st=self.state['orchestration']['subtasks']['coding']
        for aid in ['coding_a','coding_b']:
            ar=self.artifact(aid,aid+'_v1','Current coding candidate')
            self.event('candidate.record',{'candidate_id':aid+'_c1','assignment_id':aid,'artifact_id':ar,'baseline':st['digest'],'round':st['round'],'supersedes':None,'findings':None,'revalidation':None})
        self.assign('coding_reviewer_a','reviewer1','coding')
        findings=self.artifact('coding_reviewer_a','coding_rejection','A required validation boundary is missing.')
        self.event('review.record',{'review_id':'coding_review1','assignment_id':'coding_reviewer_a','candidate_id':'coding_a_c1','baseline':st['digest'],'round':st['round'],'outcome':'rejected','findings':findings})
        for aid in ['coding_a','coding_b','coding_reviewer_a']:self.observe(aid)
        before=copy.deepcopy(self.state['orchestration']);d=self.assignment_data('coding_a','solver1','coding')
        for ar in ['coding_a_v1',findings]:
            artifact=before['artifacts'][ar]
            d['context'].append({'path':str(self.folder.relative_to(self.root)/artifact['path']),'sha256':artifact['sha256']})
        self.event('assignment.inputs',{'assignment_id':'coding_a','role':d['role'],'fit':d['fit'],'runtime':d['runtime'],'context':d['context'],'receipt':{'tool':'collaboration.send_message','native_id':before['assignments']['coding_a']['native_id'],'artifact_sha256s':sorted({r['sha256'] for r in d['context']}),'evidence':'Synthetic queued correction packet; no native wake is performed by this fixture.'},'reason':'Correct the rejected current candidate while preserving the accepted analysis dependency.'})
        after=self.state['orchestration'];a=after['assignments']['coding_a']
        for key in ['native_id','native_receipt','role_reads','observations']:self.assertEqual(a[key],before['assignments']['coding_a'][key])
        self.assertEqual(a['state'],'active');self.assertEqual(a['context'],d['context'])
        for key in ['candidates','reviews','acceptances','syntheses']:self.assertEqual(after[key],before[key])
        self.assertEqual(after['subtasks']['subtask1'],before['subtasks']['subtask1'])
        self.assertEqual(after['subtasks']['coding']['dependency_versions'],before['subtasks']['coding']['dependency_versions'])
        cp,result=self.run_cli('validate');self.assertEqual(cp.returncode,0,result)

    def test_input_rebind_does_not_skip_another_active_write_owner(self):
        self.define();self.assign('worker1','worker');self.observe('worker1')
        self.define(sid='subtask2');self.assign('worker2','worker','subtask2')
        d=self.assignment_data('worker1','worker');before=self.tree_hash()
        self.event('assignment.inputs',{'assignment_id':'worker1','role':d['role'],'fit':d['fit'],'runtime':d['runtime'],'context':d['context'],'receipt':{'tool':'collaboration.send_message','native_id':'/root/manager1/worker1','artifact_sha256s':sorted({r['sha256'] for r in d['context']}),'evidence':'Synthetic queued input; another worker now owns the output scope.'},'reason':'Attempt to resume the original worker with newly supplied inputs.'},fail='ORCH_WRITE_OVERLAP')
        self.assertEqual(before,self.tree_hash())
    def test_new_result_invalidates_prior_direct_verification(self):
        self.define();self.assign('worker1','worker');self.artifact('worker1','deliverable');self.result('worker1','deliverable');self.observe('worker1');self.verify();self.artifact('worker1','deliverable2','A revised deliverable')
        st=self.state['orchestration']['subtasks']['subtask1'];self.event('result.record',{'result_id':'another_result','assignment_id':'worker1','acceptance_id':None,'baseline':st['digest'],'round':st['round'],'artifact_ids':['deliverable2'],'changes':self.context,'checks':self.context,'limitations':[]})
        self.event('execution.finish',{'outcome':'delivered','criteria':[{'criterion':'Delivered and inspected.','evidence':'Claim previous verification still counts.'}],'inspection':self.context},fail='ORCH_VERIFICATION_STALE')


    def test_structural_reference_corruption_is_rejected_read_only(self):
        self.define('extra-complex',True);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.candidate('solver2','candidate2')
        for aid in ['reviewer1','reviewer2']:self.assign(aid,aid)
        self.review('reviewer1','candidate1','review1');self.review('reviewer2','candidate2','review2');self.assign('senior1','senior');self.synthesis(['candidate1','candidate2'],['review1','review2']);self.assign('implementer1','implementer');self.artifact('implementer1','deliverable');self.result('implementer1','deliverable','accept_synthesis1')
        original=(self.folder/'task.json').read_bytes()
        mutations=[('artifacts','deliverable','assignment_id','missing'),('candidates','candidate1','artifact_id','missing'),('candidates','candidate1','supersedes','missing'),('candidates','candidate1','candidate_id','wrong'),('reviews','review1','review_id','wrong'),('syntheses','synthesis1','candidate_ids',['missing']),('syntheses','synthesis1','review_ids',['missing']),('syntheses','synthesis1','artifact_id','missing'),('syntheses','synthesis1','synthesis_id','wrong'),('acceptances','accept_synthesis1','acceptance_id','wrong'),('results','result1','artifact_ids',['missing']),('results','result1','result_id','wrong')]
        for collection,rid,key,value in mutations:
            with self.subTest(collection=collection,key=key):
                bad=json.loads(original);bad['orchestration'][collection][rid][key]=value;(self.folder/'task.json').write_text(task_state.json_text(task_state.canonical_state(bad)));before=self.tree_hash()
                for command in ('validate','show'):
                    cp,res=self.run_cli(command,self.state['task_id']);self.assertNotEqual(cp.returncode,0,res);self.assertIn('ORCH_REFERENCE',json.dumps(res))
                self.assertEqual(before,self.tree_hash());(self.folder/'task.json').write_bytes(original)
    def test_pre_activation_host_roster_is_not_manager_reconnection(self):
        cp,r=self.run_cli('new',payload={'name':'Preactivation','description':'Probe exact manager identity','definition_of_done':['Confirmed manager.'],'orchestration_enabled':True});self.assertEqual(cp.returncode,0,r)
        self.folder=Path(r['task_folder']);self.state=self.read_state(self.folder);self.exec_id='preactivation';self.actor='/root';self.event('manager.reserve',self.manager_data('manager2'))
        d={'assignment_id':'manager2','receipt':self.roster('/root','running')};self.event('manager.reconnect',d,fail='ORCH_MANAGER_NOT_LIVE')
        self.event('manager.receipt',{'assignment_id':'manager2','receipt':self.launch('/root/manager2')});self.event('manager.reconnect',d,fail='ORCH_MANAGER_NOT_LIVE')
    def test_conflict_survives_material_revision_and_requires_all_original_deliveries(self):
        self.define('complex',False);self.assign('solver1','solver1');self.assign('solver2','solver2');self.candidate('solver1','candidate1');self.candidate('solver2','candidate2');self.assign('senior1','senior');self.artifact('senior1','explanation','Resolve opposite interface commitments');st=self.state['orchestration']['subtasks']['subtask1']
        self.event('conflict.record',{'conflict_id':'conflict1','assignment_id':'senior1','candidate_ids':['candidate1','candidate2'],'baseline':st['digest'],'round':st['round'],'explanation':'explanation','progress':'User steering will settle the contradictory interface.'})
        for aid in ['solver1','solver2','senior1']:self.observe(aid)
        b=self.base('complex',False);b['criteria']=['Raise ValueError under approved strict validation.'];self.event('subtask.revise',{'subtask_id':'subtask1','baseline':b,'reason':'Authorized shared strict-validation steering.'});self.assertEqual(self.state['orchestration']['subtasks']['subtask1']['active_conflicts'],['conflict1'])
        self.rebind('solver1');self.rebind('solver2');self.artifact('solver1','revision','Revised strict validation');st=self.state['orchestration']['subtasks']['subtask1']
        d={'candidate_id':'revised','assignment_id':'solver1','artifact_id':'revision','baseline':st['digest'],'round':st['round'],'supersedes':'candidate1','findings':'Resolved interface as instructed.','revalidation':None}
        self.event('candidate.record',d,fail='ORCH_CONFLICT_DELIVERY')
        for slot in ['solver1','solver2']:
            self.event('conflict.deliver',{'conflict_id':'conflict1','solver_slot':slot,'receipt':{'native_id':'/root/manager1/'+slot,'explanation_sha256':self.state['orchestration']['artifacts']['explanation']['sha256'],'evidence':'Same original explanation and revised common baseline delivered.'}})
        self.event('candidate.record',d)
    def test_same_category_cannot_drop_a_frozen_solver_after_candidates(self):
        b=self.base('complex',False);b['slots'].append({'slot':'solver3','function':'solver','perspective':'boundary','solver_slot':None});self.event('subtask.define',{'subtask_id':'subtask1','baseline':b})
        for aid in ['solver1','solver2','solver3']:self.assign(aid,aid)
        self.candidate('solver1','candidate1')
        for aid in ['solver1','solver2','solver3']:self.observe(aid)
        self.event('subtask.revise',{'subtask_id':'subtask1','baseline':self.base('complex',False),'reason':'Attempt to omit the queued third contribution.'},fail='ORCH_RECLASSIFICATION')
    def test_live_delivery_changed_after_result_blocks_verification(self):
        self.define();self.assign('worker1','worker');self.artifact('worker1','deliverable','Original delivered bytes');st=self.state['orchestration']['subtasks']['subtask1'];self.event('result.record',{'result_id':'result1','assignment_id':'worker1','acceptance_id':None,'baseline':st['digest'],'round':st['round'],'artifact_ids':['deliverable'],'changes':[self.ref('output/deliverable.txt')],'checks':self.context,'limitations':[]});self.observe('worker1');(self.root/'output/deliverable.txt').write_text('Changed live production bytes.')
        d={'subtask_id':'subtask1','baseline':st['digest'],'round':st['round'],'result_id':'result1','acceptance_id':None,'artifacts':['deliverable'],'criteria':[{'criterion':'Subtask done.','evidence':'Invalid stale claim.'}],'inspection':self.context};self.event('subtask.verify',d,fail='ORCH_EVIDENCE_CHANGED')
    def test_changed_upstream_delivery_invalidates_generic_dependent(self):
        def result(aid,sid,rid,artifact):
            st=self.state['orchestration']['subtasks'][sid];self.event('result.record',{'result_id':rid,'assignment_id':aid,'acceptance_id':None,'baseline':st['digest'],'round':st['round'],'artifact_ids':[artifact],'changes':self.context,'checks':self.context,'limitations':[]})
        def verify(sid,rid,artifact):
            st=self.state['orchestration']['subtasks'][sid];self.event('subtask.verify',{'subtask_id':sid,'baseline':st['digest'],'round':st['round'],'result_id':rid,'acceptance_id':None,'artifacts':[artifact],'criteria':[{'criterion':'Subtask done.','evidence':'Current direct check.'}],'inspection':self.context})
        self.define();self.assign('worker1','worker');self.artifact('worker1','upstream1');result('worker1','subtask1','result_upstream1','upstream1');self.observe('worker1');verify('subtask1','result_upstream1','upstream1')
        self.define(sid='subtask2',dependencies=['subtask1']);self.assign('worker2','worker','subtask2');self.artifact('worker2','downstream');result('worker2','subtask2','result_downstream','downstream');self.observe('worker2');verify('subtask2','result_downstream','downstream');self.assertTrue(self.state['orchestration']['subtasks']['subtask2']['dependency_versions'])
        self.artifact('worker1','upstream2');result('worker1','subtask1','result_upstream2','upstream2');verify('subtask1','result_upstream2','upstream2')
        self.event('execution.finish',{'outcome':'delivered','criteria':[{'criterion':'Delivered and inspected.','evidence':'Stale downstream integration claim.'}],'inspection':self.context},fail='ORCH_DEPENDENCY_CHANGED')


    def test_observation_cannot_restore_revoked_or_unresumed_ownership(self):
        self.define();self.assign('worker1','worker');self.observe('worker1')
        observation={'assignment_id':'worker1','receipt':self.roster('/root/manager1/worker1','running'),'changes':self.context}
        self.event('assignment.observe',observation,fail='ORCH_RESUME_REQUIRED')
        self.event('assignment.resume',{'assignment_id':'worker1','runtime':self.runtime,'reason':'Actual same-ID follow-up is ready.'});self.event('assignment.observe',observation);self.observe('worker1')
        self.event('assignment.revoke',{'assignment_id':'worker1','reason':'Observed completion and replacement.'});self.assign('worker2','worker');before=self.tree_hash()
        self.event('assignment.observe',observation,fail='ORCH_REVOKED');self.assertEqual(before,self.tree_hash())
        self.event('assignment.uncertain',{'assignment_id':'worker1','reason':'Late activity cannot undo revocation.'},fail='ORCH_REVOKED')

    def test_unassigned_projection_recovery_uses_bounded_bootstrap_receipt(self):
        cp,r=self.run_cli('new',payload={'name':'Unassigned recovery','description':'Recover generated views only.','definition_of_done':['View is usable.'],'orchestration_enabled':True});self.assertEqual(cp.returncode,0,r);folder=Path(r['task_folder']);state=self.read_state(folder);canonical=(folder/'task.json').read_bytes()
        (self.root/'Tasks/INDEX.md').write_text('Projection publication was interrupted.');(folder/'TASK.md').write_text('Projection incomplete.')
        (self.root/'bootstrap-roster.json').write_text(json.dumps(self.roster('/root','running')))
        cp,r=self.run_cli('rebuild-projections',state['task_id'],'--actor','/root','--generation','0','--bootstrap-receipt','bootstrap-roster.json');self.assertEqual(cp.returncode,0,r);self.assertEqual((folder/'task.json').read_bytes(),canonical);self.assertIsNone(self.read_state(folder)['orchestration']['writer'])
        cp,r=self.run_cli('rebuild-projections',self.state['task_id'],'--actor','/root','--execution-id',self.exec_id,'--generation','1','--bootstrap-receipt','bootstrap-roster.json');self.assertEqual(r['errors'][0]['code'],'ORCH_WRITER')


if __name__ == '__main__': unittest.main()
