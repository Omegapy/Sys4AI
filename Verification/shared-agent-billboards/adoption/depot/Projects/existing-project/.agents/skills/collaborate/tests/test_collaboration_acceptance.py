"""Exactly four deterministic bundles. Synthetic receipts are NEVER native proof."""
from __future__ import annotations
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shutil
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPT_ROOT=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPT_ROOT))
sys.path.insert(0,str(SCRIPT_ROOT.parents[1]/'agent-task/tests'))
import test_orchestration_state as existing
from collaboration_store import CollaborationError, encoded, publish, record, digest
from collaboration_task import Context
from collaboration_read import Board, TYPES
from collaboration_delivery import pending
from collaboration_views import rebuild_view, render
from collaboration_decisions import snapshot, assess
from collaborate import main as cli_main
import io
from contextlib import redirect_stdout
from types import SimpleNamespace


def fixture(category='generic'):
    # Local subclass avoids discovering/rerunning the unaffected existing suite.
    class F(existing.OrchestrationTests):
        def fit(self,writes):
            fit=super().fit(writes)
            fit['reads']=['evidence.txt',str(self.folder.relative_to(self.root)/'artifacts/orchestration'),'Evidence/'+self.state['task_id']]
            return fit
        def manager_data(self,aid):
            data=super().manager_data(aid)
            data['fit']=self.fit([str(self.folder.relative_to(self.root)/'artifacts/orchestration/manager')])
            return data
        def base(self,*args,**kwargs):
            b=super().base(*args,**kwargs)
            b['reads']=self.fit([])['reads']
            if b['category']=='generic': b['writes']=['Evidence/'+self.state['task_id']+'/work/worker1']
            return b
        def assignment_data(self,aid,slot,sid='subtask1'):
            data=super().assignment_data(aid,slot,sid)
            if slot=='worker':data['fit']['writes']=['Evidence/'+self.state['task_id']+'/work/'+aid]
            return data
        def board(self,aid='manager1',**overrides):
            a=self.state['orchestration']['assignments'][aid]
            values=dict(root=self.root,task_path=str(self.folder.relative_to(self.root)/'task.json'),assignment=aid,actor=a['native_id'],execution=self.exec_id,generation=self.generation,policy=self.policy_ref)
            values.update(overrides);return Board(Context(**values))
    f=F(methodName='runTest');f.setUp()
    # Deterministic fixture explicitly installs exact current source owner bytes.
    owner_source=SCRIPT_ROOT.parents[1]/'agent-task/scripts'
    owner_target=f.root/'.agents/skills/agent-task/scripts';owner_target.mkdir(parents=True)
    for name in ('task_state.py','orchestration_state.py','native_observations.py'):
        shutil.copyfile(owner_source/name,owner_target/name)
    people=['manager1','worker1'] if category=='generic' else ['manager1','solver1','solver2','reviewer1','reviewer2','senior1']
    participants={aid:{'namespace':str(f.folder.relative_to(f.root)/'artifacts/orchestration'/('manager' if aid=='manager1' else 'work/'+aid)/'collaboration'),'subtask_id':None if aid=='manager1' else 'subtask1'} for aid in people}
    if category=='generic':participants['worker1']['namespace']='Evidence/'+f.state['task_id']+'/work/worker1/collaboration'
    policy={'version':1,'project':str(f.root),'task':f.state['task_id'],'execution':f.exec_id,'generation':1,'manager':'manager1','participants':participants,'subtasks':{'subtask1':{'phase':'integration' if category=='generic' else 'independent','audience':people,'independent_first_pass':category!='generic','reviewer_first_pass':category=='extra-complex','exchange_stop':'Stop after one precise evidence challenge and response, or unchanged findings.'}},'bounds':{'record_bytes':65536,'output_bytes':32768,'page_items':20},'topology':'common-store-cooperative'}
    source=str(f.folder.relative_to(f.root)/'artifacts/orchestration/manager/policy.json')
    (f.root/source).parent.mkdir(parents=True,exist_ok=True);(f.root/source).write_bytes(encoded(policy))
    f.event('artifact.register',{'artifact_id':'policy1','assignment_id':'manager1','source_path':source})
    ar=f.state['orchestration']['artifacts']['policy1'];f.policy_ref={'path':str(f.folder.relative_to(f.root)/ar['path']),'sha256':ar['sha256']};f.context=f.context+[f.policy_ref]
    f.define(category,False if category!='generic' else True)
    if category=='generic':f.assign('worker1','worker')
    else:
        for aid in ['solver1','solver2']:f.assign(aid,aid)
    return f


def message(board,op='post1',kind='note',visibility='findings',target=None,recipients=None,material=False,body='Concise uncertain operational observation.'):
    post = dict(operation_id=op,thread_id='thread1',reply_to=None,supersedes=None,subtask='subtask1',type=kind,title='Bounded contribution '+op,body=body,phase=board.phase('subtask1'),visibility=visibility,recipients=recipients or list(board.c.policy['subtasks']['subtask1']['audience']),requested_response='Answer this question within existing scope, then stop.',urgency='blocker' if kind=='blocker' else 'routine',targets=[] if target is None else [target],evidence=[],limitations=['Deterministic fixture; no native or comprehension proof.'],material=material)
    if visibility=='operational' and board.c.policy['subtasks']['subtask1']['independent_first_pass']:
        post.update(operation_id='notice1',thread_id='operations',title='Source unavailable',body='Operational notice; ask the current manager for the permitted clarification.',requested_response='Manager: assess the exact frozen source or tool issue at the next active checkpoint.',limitations=[],material=False)
    return post


def tree(root):
    return {str(p.relative_to(root)):digest(p.read_bytes()) for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


class AcceptanceBundles(unittest.TestCase):
    def denied(self,call,root=None):
        before=tree(root) if root else None
        with self.assertRaises(CollaborationError) as caught:call()
        self.assertNotIn('private-content',str(caught.exception))
        if root:self.assertEqual(before,tree(root))

    def test_D1_publication_retry_crash(self):
        f=fixture();self.addCleanup(f.tearDown)
        def write(i):
            b=f.board('worker1' if i%2 else 'manager1');return b.post(message(b,op='parallel'+str(i)))
        with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(write,range(16)))
        self.assertEqual(len({x['message_id'] for x in results}),16)
        for result in results:record(f.root,result['source']['path'])
        b=f.board('worker1');post=message(b,op='retry1');first=b.post(post)
        self.assertEqual(first,b.post(post));self.denied(lambda:b.post({**post,'body':'Conflicting payload.'}),f.root)
        original=(f.root/first['source']['path']).read_bytes()
        self.denied(lambda:publish(f.root,first['source']['path'],{'collision':True}),f.root)
        self.assertEqual(original,(f.root/first['source']['path']).read_bytes())
        with patch('collaboration_read.publish',side_effect=lambda *args,**kwargs:(publish(*args,**kwargs),(_ for _ in ()).throw(RuntimeError('Injected after durable publication before notification')))[1]):
            with self.assertRaises(RuntimeError):b.post(message(b,op='crash1'))
        recovered=f.board('worker1');requests=pending(recovered,'manager1')
        self.assertIn('worker1.crash1',{r['message_id'] for r in requests['requests']})
        self.assertFalse(requests['wake']);self.assertFalse(requests['persistence_is_delivery'])
        receipt={'tool':'collaboration.send_message','native_id':f.actor,'result':{'fixture':'synthetic successful native receipt only'}}
        r=recovered.receipt('delivery1','worker1.crash1','notified','manager1','Synthetic deterministic receipt.',receipt)
        self.assertEqual(r,recovered.receipt('delivery1','worker1.crash1','notified','manager1','Synthetic deterministic receipt.',receipt))
        self.assertNotIn('worker1.crash1',{r['message_id'] for r in pending(recovered,'manager1')['requests']})
        tmp=f.root/recovered.c.namespace/'messages/.pending-incomplete';tmp.write_bytes(b'{')
        self.assertEqual(len(recovered.messages()),18)
        corrupt=f.root/recovered.c.namespace/'messages/corrupt.json';corrupt.write_bytes(b'{"payload":{"private-content":true},"sha256":"wrong"}')
        self.denied(recovered.messages)

    def test_D2_scope_privacy_release_and_read_boundaries(self):
        f=fixture('extra-complex');self.addCleanup(f.tearDown)
        b=f.board('solver1');sealed=b.post(message(b,op='sealed1',kind='finding',visibility='findings',body='private-content independent conclusion'))
        notice=b.post(message(b,op='notice1',visibility='operational'))
        peer=f.board('solver2');before=tree(f.root)
        for route in [lambda:peer.query(),lambda:peer.query(search='private-content'),lambda:peer.query(unread=True),lambda:render(peer),lambda:pending(b,'solver2')]:
            value=route();self.assertNotIn('private-content',value.decode() if isinstance(value,bytes) else encoded(value).decode())
        self.denied(lambda:peer.find(sealed['message_id']))
        self.denied(lambda:peer.linked(sealed['message_id'],f.ev))
        self.assertEqual(before,tree(f.root))
        peer.receipt('private-content-receipt',notice['message_id'],'acknowledged',evidence='private-content candidate conclusion in receipt')
        for value in [b.query(),b.receipts(b.messages()),render(b),pending(peer,'solver1')]:
            self.assertNotIn('private-content-receipt',value.decode() if isinstance(value,bytes) else encoded(value).decode())
            if not isinstance(value,bytes):
                self.assertNotIn('private-content candidate conclusion in receipt',encoded(value).decode())
        self.assertEqual(peer.query(unread=True)['returned'],0)
        f.candidate('solver1','candidate1');f.candidate('solver2','candidate2')
        peer=f.board('solver2');self.assertEqual([x['message']['message_id'] for x in peer.query(unread=True)['items']],[sealed['message_id']])
        manager=f.board();self.assertIn(sealed['message_id'],{x['message']['message_id'] for x in manager.query(unread=True)['items']})
        for aid in ['reviewer1','reviewer2']:f.assign(aid,aid)
        reviewer=f.board('reviewer2');self.assertNotIn('private-content',encoded(reviewer.query()).decode())
        reviewer1=f.board('reviewer1');verdict=reviewer1.post(message(reviewer1,op='verdict1',kind='finding',visibility='verdict',body='private-content reviewer verdict'))
        self.assertNotIn(verdict['message_id'],{x['message']['message_id'] for x in reviewer.query()['items']})
        f.review('reviewer1','candidate1','review1');f.review('reviewer2','candidate2','review2')
        self.assertIn(verdict['message_id'],{x['message']['message_id'] for x in f.board('reviewer2').query()['items']})
        fresh=f.board('solver2');before=tree(f.root)
        fresh.query();fresh.query(search='Bounded');fresh.query(unread=True);fresh.messages();self.assertEqual(before,tree(f.root))
        rebuilt=rebuild_view(fresh);after=tree(f.root);self.assertEqual(set(after)-set(before),{rebuilt['path']});self.assertTrue(all(after[k]==v for k,v in before.items()))
        for override in [{'generation':0},{'actor':'/root/forged'},{'assignment':'manager1','actor':'/root/manager1/solver2'},{'root':f.root/'other'},{'task_path':'../task.json'}]:
            self.denied(lambda ov=override:f.board('solver2',**ov),f.root)
        for content in [{'title':'private-content sk-proj-abcdefghijklmnopqrst'},{'body':'private-content\x01'},{'body':'x'*70000},{'visibility':'operational','type':'finding'},{'visibility':'operational','title':'private-content'},{'visibility':'operational','operation_id':'private-content'},{'visibility':'operational','limitations':['private-content']}]:
            self.denied(lambda x=content:fresh.post({**message(fresh,op='invalid1'),**x}),f.root)
        self.denied(lambda:fresh.post({**message(fresh),'recipients':['unassigned']}),f.root)
        self.denied(lambda:fresh.post({**message(fresh),'targets':[{'path':'../outside','sha256':'0'*64}]}),f.root)
        outside=f.root/'private-content';outside.write_text('private-content')
        self.denied(lambda:fresh.post({**message(fresh),'targets':[{'path':'private-content','sha256':digest(outside.read_bytes())}]}),f.root)
        own=f.root/fresh.c.namespace/'receipts';own.mkdir(parents=True,exist_ok=True);(own/'symlink.json').symlink_to(outside)
        self.denied(lambda:fresh.receipt('symlink',notice['message_id'],'acknowledged'),f.root)
        (own/'symlink.json').unlink()  # Disposable negative fixture, not a retention route.
        # Forged policy producer and unbound policy bytes cannot grant themselves scope.
        wrong=copy.deepcopy(fresh.c.policy_ref);wrong['sha256']='0'*64;self.denied(lambda:f.board('solver2',policy=wrong),f.root)
        argv=['--project-root',str(f.root),'--task-path',str(f.folder.relative_to(f.root)/'task.json'),'--assignment','solver2','--actor',fresh.c.actor,'--execution',f.exec_id,'--generation','1','--policy-path',fresh.c.policy_ref['path'],'--policy-sha256',fresh.c.policy_ref['sha256'],'post','--payload-file','private-content']
        with redirect_stdout(io.StringIO()) as output: self.assertEqual(cli_main(argv),2)
        self.assertEqual(json.loads(output.getvalue()),{'error':'COLLAB_SCOPE'})
        # An older owner lacking the versioned API fails constant preflight,
        # without falling back or touching Task/receipt/assignment state.
        unsupported=SimpleNamespace(validate_state_shape=fresh.c.owner.validate_state_shape,orch=SimpleNamespace(**{key:value for key,value in vars(fresh.c.orch).items() if key!='versioned'}))
        before=tree(f.root)
        with patch('collaboration_task.task_module',return_value=unsupported):
            with redirect_stdout(io.StringIO()) as output:self.assertEqual(cli_main(argv[:-3]+['validate']),2)
            self.assertEqual(json.loads(output.getvalue()),{'error':'COLLAB_OWNER_UNSUPPORTED'})
        self.assertEqual(before,tree(f.root))
        self.assertTrue(f.board('solver2').c.first_review('reviewer2'))
        saved=(f.folder/'task.json').read_bytes();bad=copy.deepcopy(f.state);bad['orchestration']['assignments']['solver2']['role_reads']['role_sha256']='0'*64
        (f.folder/'task.json').write_text(json.dumps(bad));self.denied(lambda:f.board('solver2'));(f.folder/'task.json').write_bytes(saved)
        damaged=f.root/fresh.c.namespace/'receipts/corrupt.json';damaged.write_bytes(b'{"payload":{},"sha256":"invalid"}')
        validate_args=argv[:-3]+['validate']
        with redirect_stdout(io.StringIO()) as output:self.assertEqual(cli_main(validate_args),2)
        self.assertEqual(json.loads(output.getvalue()),{'error':'COLLAB_HASH'})
        damaged.unlink()  # Disposable corruption fixture only.
        cached=fresh;f.event('block',{'reason':'Synthetic canonical state change.','next_step':'Reopen exact current context.'})
        self.denied(lambda:cached.post(message(cached,op='late1')),f.root);self.denied(cached.query,f.root)
        # Late generation files stay historical and do not affect current unread state.
        now=f.board('solver2');ns=now.c.namespace+'/messages/old1.json';old={**message(now,op='old1'),**now.c.binding(),'message_id':'solver2.old1','generation':0}
        publish(f.root,ns,old);self.assertNotIn('solver2.old1',{x['message']['message_id'] for x in now.query()['items']})

    def test_D3_task_gates_snapshots_material_objections(self):
        f=fixture('extra-complex');self.addCleanup(f.tearDown)
        for aid in ['solver1','solver2']:f.candidate(aid,'candidate'+aid[-1])
        for aid in ['reviewer1','reviewer2']:f.assign(aid,aid);f.review(aid,'candidate'+aid[-1],'review'+aid[-1])
        f.assign('senior1','senior');f.synthesis(['candidate1','candidate2'],['review1','review2'])
        owner=f.board();self.assertEqual(owner.c.eligibility('subtask1')['category'],'extra-complex')
        ar=f.state['orchestration']['artifacts']['artifact_candidate1'];target={'path':str(f.folder.relative_to(f.root)/ar['path']),'sha256':ar['sha256']}
        peer=f.board('solver1');challenge=peer.post(message(peer,op='challenge1',kind='challenge',visibility='findings',target=target,material=True,recipients=['solver2']))
        # Owner can assess material peer-targeted objections within its canonical scope.
        owner=f.board();self.assertFalse(assess(owner,'subtask1',[])['eligible'])
        f.board('solver2').receipt('answered1',challenge['message_id'],'answered')
        self.assertFalse(assess(owner,'subtask1',[])['eligible'])
        a={'message_id':challenge['message_id'],'target':target,'disposition':'rejected','owner':'manager1','decision_kind':'acceptance','decision_id':'accept_synthesis1','evidence':[f.ev],'reason':'Exact canonical inspection supports the current bounded conclusion; objection disposition retained.'}
        self.denied(lambda:assess(owner,'subtask1',[{**a,'decision_id':'invented'}]),f.root)
        self.assertTrue(assess(owner,'subtask1',[a])['eligible']);self.assertFalse(assess(owner,'subtask1',[{**a,'disposition':'deferred'}])['eligible'])
        canonical=(f.folder/'task.json').read_bytes();snap=snapshot(owner,'snapshot1',[challenge['message_id']],[a]);self.assertEqual(canonical,(f.folder/'task.json').read_bytes());p,_=record(f.root,snap['path'],250000);self.assertFalse(p['conversation_copied']);self.assertEqual(p['selected'][0]['source'],challenge['source'])
        self.denied(lambda:snapshot(peer,'forbidden',[]),f.root)
        # Required input artifact edit invalidates current context and canonical gates.
        old_candidate=(f.root/target['path']).read_bytes();(f.root/target['path']).write_text('Changed immutable candidate in negative fixture.')
        self.denied(lambda:f.board().c.eligibility('subtask1'))
        (f.root/target['path']).write_bytes(old_candidate)
        # Genuine version revision leaves original synthesis/acceptance history intact.
        f.candidate('solver1','candidate1v2',supersedes='candidate1')
        self.denied(lambda:f.board().c.eligibility('subtask1'))
        # Its preserved old first review does not release the superseding
        # candidate; an exact current assigned re-review opens that gate again.
        old_first_review=f.board().c.o['reviews']['review1'].copy()
        self.assertFalse(f.board().c.first_review('reviewer1'))
        f.review('reviewer1','candidate1v2','review1v2')
        self.assertTrue(f.board().c.first_review('reviewer1'))
        self.assertEqual(f.board().c.o['reviews']['review1'],old_first_review)
        f.synthesis(['candidate1v2','candidate2'],['review1v2','review2'],synid='synthesis2')
        current=f.board();self.assertEqual(current.c.eligibility('subtask1')['candidates'],['candidate1v2','candidate2'])
        self.assertIn('accept_synthesis1',current.c.o['acceptances']);self.assertIn('synthesis1',current.c.o['syntheses'])
        self.denied(lambda:assess(current,'subtask1',[a]))
        # Strict historical/source contracts remain unknown-field/version closed.
        bad=copy.deepcopy(f.state);bad['orchestration']['unexpected']=True
        self.assertTrue(f.board().c.owner.validate_state_shape(bad,f.folder,json.dumps(bad)))
        before=tree(f.root);f.board().c.owner.orch.empty();self.assertEqual(before,tree(f.root))

    def test_D4_vocabulary_filters_corrections_bounds_handling(self):
        f=fixture();self.addCleanup(f.tearDown);b=f.board('worker1');target=f.ev
        posts=[]
        for i,kind in enumerate(TYPES):
            posts.append(b.post(message(b,op='vocab'+str(i),kind=kind,visibility='findings' if kind in ('finding','challenge','proposal') else 'operational',target=target,material=kind in ('finding','challenge','blocker','change-notice'))))
        reader=f.board();self.assertEqual(reader.query()['total'],len(TYPES))
        for field,value in [('subtask','subtask1'),('thread','thread1'),('participant','worker1'),('artifact',target['path']),('phase','integration')]:self.assertEqual(reader.query(**{field:value})['total'],len(TYPES))
        for kind in TYPES:self.assertEqual(reader.query(type=kind)['total'],1)
        self.assertEqual(reader.query(search='Bounded')['total'],len(TYPES))
        original=posts[0];before=(f.root/original['source']['path']).read_bytes()
        reply=b.post({**message(b,op='reply1'),'reply_to':original['message_id']})
        correction=b.post({**message(b,op='correction1'),'supersedes':original['message_id']})
        self.assertEqual(before,(f.root/original['source']['path']).read_bytes());self.assertEqual(reader.find(reply['message_id'])['message']['reply_to'],original['message_id']);self.assertEqual(reader.find(correction['message_id'])['message']['supersedes'],original['message_id'])
        self.denied(lambda:b.post({**message(b,op='badreply'),'reply_to':'worker1.missing'}),f.root)
        result=reader.query(items=2);self.assertEqual(result['returned'],2);self.assertEqual(result['remaining'],8);self.assertLessEqual(len(encoded(result)),32768)
        mid=posts[1]['message_id'];reader.receipt('defer1',mid,'deferred');self.assertFalse(reader.find(mid)['message'].get('reported_reading',False))
        item=next(x for x in reader.query()['items'] if x['message']['message_id']==mid);self.assertFalse(item['reported_reading']);self.assertNotIn(mid,{x['message']['message_id'] for x in reader.query(unread=True)['items']})
        reader.receipt('ack1',mid,'acknowledged');item=next(x for x in reader.query()['items'] if x['message']['message_id']==mid);self.assertTrue(item['reported_reading'])
        reader.receipt('handled1',mid,'handled');reader.receipt('answered1',mid,'answered')
        b.receipt('attempt1',mid,'delivery-attempt','manager1');b.receipt('failed1',mid,'failed','manager1');b.receipt('uncertain1',mid,'uncertain','manager1')
        self.assertIn(mid,{x['message_id'] for x in pending(b,'manager1')['requests']})
        linked=reader.linked(posts[2]['message_id'],target);self.assertEqual(linked['source'],target)
        self.assertTrue(all(x['receipt']['state'] in ('deferred','acknowledged','handled','answered','delivery-attempt','failed','uncertain') for x in reader.receipts(reader.messages())))


if __name__=='__main__':unittest.main()
