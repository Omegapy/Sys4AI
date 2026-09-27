"""Disposable pool/owner-boundary tests. Synthetic transport is not native proof."""
import copy
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from curator_runtime import ForkRuntimePool
from curator_runtime_codex import ForkCodexAdapter
from curator_policy import PolicyError,digest
from test_native_protocol import ForkProtocolTests,native


class SyntheticAdapter:
    typed_receipt=ForkCodexAdapter.typed_receipt
    load_observation=ForkCodexAdapter.load_observation
    close_actor_admission=ForkCodexAdapter.close_actor_admission
    role_receipt=ForkCodexAdapter.role_receipt

    def __init__(self,pool,reservation,epoch,profile):
        self.native=native;self.registry=pool.registry;self.selected_protocol=pool.protocol
        self.reservation=reservation;self.load_epoch=epoch;self.profile=profile;self.quarantine=[]
        self.actor_binding=None;self.closed_admission=False;self.cleanup_observation=None
        self.observation_handles={};self.wire_records=[];self.history=[{'id':'source-turn','items':[{'type':'userMessage','content':'whole problem'}]}]
        self.cleanup={'state':'owned_process_group_stopped','companion':{'state':'owned_companion_stopped'}}
        self.effects=[]

    def bind(self,actor):
        self.actor_binding={'thread_id':actor,'session_id':'shared-session','connection_id':self.reservation+'-epoch-'+str(self.load_epoch),
            'load_epoch':self.load_epoch,'runtime_instance':{'pid':100+self.load_epoch,'parent':1,'group':100+self.load_epoch,
                'uid':501,'started':[100,self.load_epoch],'executable':'/synthetic/codex'}}
        self.registry.bind(self.actor_binding);self.authority=native.TransportAuthorityV2(self.selected_protocol,self.actor_binding,self.registry)

    def wire(self,direction,frame):
        row=native.wire_record(direction,len(self.wire_records)+1,native.canonical(frame)+b'\n');self.wire_records.append(row);return row

    def start(self):self.effects.append('start')
    def verify_prelaunch(self,*settings):self.effects.append(('closure',settings))
    def configured_settings(self):return {'model':'gpt-6-astra','reasoning_effort':'xhigh','provider':'openai'}
    def full_history(self):return {'complete':True,'turns':copy.deepcopy(self.history),'sha256':digest(self.history)}
    def begin_stop(self,deadline):self.effects.append('begin_stop')
    def close(self,deadline):
        self.effects.append('close');self.close_actor_admission();self.cleanup_observation=copy.deepcopy(self.cleanup);return self.cleanup_observation

    def create(self,kind,actor,source,logical,cut,operation_id,reservation_id):
        self.bind(actor);settings={**self.configured_settings(),'profile_id':self.profile,'cwd':'/synthetic'}
        metadata={'id':actor,'sessionId':'shared-session','parentThreadId':None,'forkedFromId':source,'source':'vscode',
            'path':'/synthetic/'+actor+'.jsonl','model':'gpt-6-astra','reasoningEffort':'xhigh','modelProvider':'openai'}
        params={'threadId':source if kind=='creation' else actor,'model':'gpt-6-astra','modelProvider':'openai',
            'config':{'model_reasoning_effort':'xhigh'},'permissions':self.profile,'cwd':'/synthetic'}
        if kind=='creation':params[cut['mode']]=cut['turn_id']
        result={'thread':metadata,'model':'gpt-6-astra','modelProvider':'openai','reasoningEffort':'xhigh','cwd':'/synthetic','activePermissionProfile':{'id':self.profile}}
        frames=[self.wire('sent',{'id':1,'method':'thread/fork' if kind=='creation' else 'thread/resume','params':params}),
            self.wire('received',{'id':1,'result':result}),self.wire('sent',{'id':2,'method':'thread/read','params':{'threadId':actor,'includeTurns':False}}),
            self.wire('received',{'id':2,'result':{'thread':metadata}})]
        observation=self.typed_receipt(kind,operation_id,reservation_id,frames,
            {'source_thread_id':source,'logical_parent_id':logical,'metadata':metadata,'settings':settings,'history_cut':cut})
        return {'thread_id':actor,'response':result,'observation':observation}

    def fork_reserved(self,**kwargs):
        return self.create('creation',self.reservation+'-native',kwargs['source_thread_id'],kwargs['logical_parent_id'],
            kwargs['history_cut'],kwargs['operation_id'],kwargs['reservation_id'])
    def resume_owned(self,**kwargs):
        stored=kwargs['stored_actor'];return self.create('resume',stored['thread_id'],stored['source_thread_id'],stored['logical_parent_id'],
            stored['history_cut'],kwargs['operation_id'],kwargs['reservation_id'])
    def status_receipt(self,operation_id,reservation_id):
        frame=self.wire('received',{'method':'turn/completed','params':{'threadId':self.actor_binding['thread_id'],'turn':{'id':'done-turn','status':'completed'}}})
        return self.typed_receipt('status',operation_id,reservation_id,[frame],{'native_state':'completed'})


class ForkPoolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        fixture=ForkProtocolTests();fixture.setUp();self.protocol=fixture.protocol
        self.registry=native.LoadedActorRegistry(self.protocol['broker_run_id']);self.adapters=[]
        self.pool=ForkRuntimePool(native=native,protocol=self.protocol,registry=self.registry,adapter_factory=self.factory,
            directory=self.temp.name,capacity=3,generation=1,deadline=time.monotonic()+30,owner_reconciler=self.reconcile)
        self.controller=self.factory('controller',1,'profile');self.controller.bind('controller-native')
        self.pool.attach_controller('controller',self.controller,'profile',{'charter':'1'*64})
        self.cut={'mode':'lastTurnId','turn_id':'source-turn','history_sha256':digest(self.controller.history),'input_sha256':'2'*64}
    def factory(self,*args):
        adapter=SyntheticAdapter(self.pool,*args);self.adapters.append(adapter);return adapter
    def reconcile(self,actor,deadline):return {'state':'reconciled','actor':actor,'inputs':[],'journals':[]}
    def worker(self,name):
        self.pool.reserve({'assignment_id':name,'generation':1,'native_id':None,'state':'reserved','function':'worker'},
            'controller','profile',self.cut,{'charter':'1'*64});return self.pool.launch(name,'launch-'+name)
    def context(self,tool='runtime_release',adapter=None):
        adapter=adapter or self.controller
        frame={'id':10+len(adapter.wire_records),'method':'item/tool/call','params':{'threadId':adapter.actor_binding['thread_id'],
            'turnId':'active-turn','callId':'call-'+str(len(adapter.wire_records)),'tool':tool,'arguments':{'reads':{'charter':'1'*64}}}}
        row=adapter.wire('received',frame);return adapter.authority.capture(frame,row['sequence'],native.canonical(frame)+b'\n')
    def release(self,name):
        context=self.context()
        with self.controller.authority.invoke(context):self.pool.request_release(context,name,'release-'+name)
        self.pool.acknowledge_callback(context)
        return self.pool.drain_releases(time.monotonic()+2)

    def test_completed_turn_retains_capacity_and_ack_precedes_actual_release(self):
        self.worker('a');self.worker('b');a=self.pool.leases['a'];self.pool.observe('a','observe-a')
        self.assertEqual(self.pool.occupied(),3)
        self.pool.reserve({'assignment_id':'c','generation':1,'native_id':None,'state':'reserved','function':'worker'},'controller','profile',self.cut,{'charter':'1'*64})
        with self.assertRaises(PolicyError):self.pool.launch('c','launch-c')
        context=self.context()
        with self.controller.authority.invoke(context):self.pool.request_release(context,'a','release-a')
        self.assertEqual(self.pool.drain_releases(time.monotonic()+2),{});self.assertNotIn('close',a.adapter.effects)
        self.assertEqual(self.pool.occupied(),3)
        self.pool.acknowledge_callback(context);result=self.pool.drain_releases(time.monotonic()+2)
        self.assertEqual(result['a']['kind'],'runtime_release');self.assertEqual(self.pool.occupied(),2)
        self.assertEqual(self.pool.leases['b'].state,'bootstrap');self.pool.launch('c','launch-c')
        self.assertEqual(self.pool.occupied(),3)

    def test_same_id_resume_has_new_epoch_and_requires_fresh_role_ack(self):
        created=self.worker('a');lease=self.pool.leases['a'];original=copy.deepcopy(lease.creation)
        old=copy.deepcopy(lease.actor);self.release('a');result=self.pool.resume('a','resume-a')
        self.assertEqual(lease.actor['thread_id'],old['thread_id']);self.assertEqual(result['load_epoch'],2)
        self.assertEqual(lease.creation,original);self.assertIsNone(lease.readiness)
        with self.assertRaises(PolicyError):self.pool.deliver('a','work','text',[])
        with self.assertRaises(PolicyError):self.pool.resolve(created['handle'],('creation',),reservation='a',actor=old['thread_id'],epoch=1,operation_id='launch-a')
        context=self.context('role_acknowledge',lease.adapter)
        with lease.adapter.authority.invoke(context):self.pool.role_acknowledgement(context,'a','reads-a',{'charter':'1'*64})
        self.assertEqual(lease.state,'ready')

    def test_uncertain_helper_stop_holds_capacity_but_other_requested_children_stop(self):
        self.worker('a');self.worker('b');self.pool.leases['a'].adapter.cleanup['companion']={'state':'uncertain'}
        for name in ('a','b'):
            context=self.context()
            with self.controller.authority.invoke(context):self.pool.request_release(context,name,'release-'+name)
            self.pool.acknowledge_callback(context)
        result=self.pool.drain_releases(time.monotonic()+2)
        self.assertEqual(result['a']['state'],'uncertain');self.assertEqual(self.pool.leases['b'].state,'released')
        self.assertEqual(self.pool.occupied(),2);self.assertTrue(self.pool.closed)
        with self.assertRaises(PolicyError):self.pool.resume('b','retry-b')

    def test_ordinary_tool_cannot_release_controller_and_host_operation_is_exact_one_use(self):
        context=self.context()
        with self.controller.authority.invoke(context),self.assertRaises(PolicyError):self.pool.request_release(context,'controller','release-controller')
        with self.assertRaises(PolicyError):self.pool.release_controller('host-release')
        self.pool.observe('controller','observe-controller')
        self.pool.authorize_controller_release('host-release',actor=self.controller.actor_binding,generation=1,handoff_sha256='3'*64)
        self.pool.release_controller('host-release');self.pool.drain_releases(time.monotonic()+2)
        self.assertEqual(self.pool.leases['controller'].state,'released')
        with self.assertRaises(PolicyError):self.pool.release_controller('host-release')

    def test_launch_uncertainty_is_durable_and_cannot_be_retried_as_a_second_actor(self):
        def failing(*args):raise PolicyError('synthetic_start_failure','No real native launch occurred.')
        self.pool.factory=failing
        self.pool.reserve({'assignment_id':'a','generation':1,'native_id':None,'state':'reserved','function':'worker'},'controller','profile',self.cut,{'charter':'1'*64})
        with self.assertRaises(PolicyError):self.pool.launch('a','launch-a')
        self.assertEqual(self.pool.occupied(),2);self.assertEqual(self.pool.leases['a'].state,'uncertain')
        with self.assertRaises(PolicyError):self.pool.launch('a','launch-again')
        journal=''.join(path.read_text() for path in sorted(Path(self.temp.name).glob('*.json')))
        self.assertIn('creation.pending',journal);self.assertIn('creation.uncertain',journal)

    def test_role_builder_rejects_a_different_authentic_tool(self):
        self.worker('a');lease=self.pool.leases['a'];context=self.context('artifact_submit',lease.adapter)
        with lease.adapter.authority.invoke(context),self.assertRaises(PolicyError):
            self.pool.role_acknowledgement(context,'a','read-a',{'charter':'1'*64})
        self.assertIsNone(lease.readiness)

    def test_both_native_cut_modes_preserve_prefix_while_parent_controls_advance(self):
        common=copy.deepcopy(self.controller.history)
        self.controller.history.extend([{'id':'private-control','items':[{'type':'agentMessage','text':'manager control'}]},
            {'id':'later-candidate','items':[{'type':'agentMessage','text':'private candidate'}]}])
        retained=copy.deepcopy(self.controller.history)
        for mode,turn_id in (('beforeTurnId','private-control'),('lastTurnId','source-turn')):
            cut={**self.cut,'mode':mode,'turn_id':turn_id}
            with self.subTest(mode=mode):
                self.assertEqual(self.pool.cut_history(self.controller.full_history(),cut),common)
                self.cut=cut
                receipt=self.worker('a' if mode=='beforeTurnId' else 'b')
                self.assertEqual(receipt['kind'],'creation')
                self.assertEqual(self.controller.history,retained)
        for bad in ('absent-turn','private-control'):
            history=self.controller.full_history()
            if bad=='private-control':history['turns'].append(copy.deepcopy(history['turns'][1]))
            with self.subTest(boundary=bad),self.assertRaises(PolicyError):
                self.pool.cut_history(history,{**self.cut,'mode':'beforeTurnId','turn_id':bad})
