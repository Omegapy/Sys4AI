import base64
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import types
import unittest

PACKAGE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PACKAGE/'scripts'))
sys.path.insert(0,str(PACKAGE.parent/'agent-task/tests'))
sys.path.insert(0,str(PACKAGE.parent/'memory/scripts'))
sys.path.insert(0,str(PACKAGE.parent/'ontology/scripts'))
import memory_publish
import memory_recovery
import ontology_publication
from test_orchestration_state import NativeOrchestrationFixture
import test_foundation_policy as policy_fixture
from curator_policy import PolicyError, digest, load_policy
from curator_confinement import CHANNELS, VerificationAdmission, file_snapshot, source_manifest
from curator_grants import FIELDS, GrantStore, validate_grant
from curator_broker import Broker, Owners, TOOLS, WIRE_TO_TOOL, native_tool_specs


class GrantTests(unittest.TestCase):
    def bindings(self):
        helper=policy_fixture.PolicyTests();helper.setUp()
        policy,_,operation,_=helper.selected('governance')
        bindings={k:'bound' for k in FIELDS if k not in ('schema_version','nonce','issued_at','expires_at')}
        for key in bindings:
            if key.endswith('sha256'):bindings[key]='1'*64
        operation['payload_sha256']=bindings['payload_sha256']
        bindings.update(issuer='issuer',prior_authority='accepted',actor='controller-native',task=None,
            call={'session_id':'session-native','request_id':1,'call_id':'call-native','thread_id':'controller-native',
                'turn_id':'turn-native','tool':'task_create','sequence':1,'raw_sha256':'1'*64},
            controller=policy['controller'],project=policy['project'],branch='main',operation='task.create',
            scope=operation,owner='task',owner_state={'schema_version':1,'inputs':[],'journal':None})
        return bindings

    def test_all_bindings_replay_and_original_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            store=GrantStore(td,'issuer')
            bindings=self.bindings()
            grant=store.issue('operation1',bindings)
            for key in bindings:
                changed=copy.deepcopy(bindings);changed[key]='different'
                with self.assertRaises(PolicyError):validate_grant(grant,changed)
            store.begin('operation1',bindings);store.uncertain('operation1')
            with self.assertRaises(PolicyError):store.begin('operation1',bindings)
            fresh=store.resume_original('operation1',bindings)
            self.assertNotEqual(grant['nonce'],fresh['nonce'])
            store.finish('operation1',{'owner':'actual fixture'}, {'file':'1'*64})
            with self.assertRaises(PolicyError):store.begin('operation1',bindings)
            self.assertEqual(store.inspect('operation1')['state'],'consumed')

    def test_nested_grant_structures_and_wire_binding_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            bindings=self.bindings();grant=GrantStore(td,'issuer').issue('operation1',bindings)
            for field,value in [('owner_state',{}),('call',{}),('project',[]),('controller',{}),('scope',{})]:
                bad=copy.deepcopy(grant);bad[field]=value
                with self.subTest(field=field),self.assertRaises(PolicyError):validate_grant(bad,bindings)
            for field,value in [('sequence',True),('thread_id','other'),('tool','task_response')]:
                bad=copy.deepcopy(grant);bad['call'][field]=value
                with self.subTest(field=field),self.assertRaises(PolicyError):validate_grant(bad,bindings)
            bad=copy.deepcopy(grant);bad['nonce']='z'*64
            with self.assertRaises(PolicyError):validate_grant(bad,bindings)

    def test_oversized_private_record_fails_before_creating_a_grant(self):
        with tempfile.TemporaryDirectory() as td:
            bindings=self.bindings();bindings['scope']['network']=[str(i)+'x'*1000 for i in range(300)]
            with self.assertRaises(PolicyError) as exc:GrantStore(td,'issuer').issue('operation1',bindings)
            self.assertEqual(exc.exception.code,'grant_size')
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_explicit_live_call_v2_schema_preserves_legacy_and_rejects_mixed_shapes(self):
        import json
        from curator_runtime_codex import shape
        schema=json.loads((PACKAGE.parents[1]/'CURATION-depo/schema/grant-v1.json').read_text())['properties']['call']
        bindings=self.bindings();shape(bindings['call'],schema,{})
        legacy=copy.deepcopy(bindings['call'])
        bindings['call']={'schema_version':2,'broker_run_id':'synthetic-run','request_id':1,'call_id':'native-call',
            'turn_id':'native-turn','tool':'task_create','actor':{'thread_id':'controller-native','session_id':'native-session',
                'connection_id':'one-connection','load_epoch':1,'runtime_instance':{'pid':123,'parent':12,'group':123,
                    'uid':501,'started':[1,123],'executable':'/synthetic/codex'}},
            'locator':{'direction':'received','sequence':3,'raw_sha256':'1'*64,'canonical_sha256':'2'*64}}
        shape(bindings['call'],schema,{})
        with tempfile.TemporaryDirectory() as td:
            store=GrantStore(td,'issuer');grant=store.issue('native-v2',bindings)
            self.assertEqual(validate_grant(grant,bindings)['call']['actor']['load_epoch'],1)
        invalid=[{**legacy,'schema_version':2},{**bindings['call'],'schema_version':99},
                 {**bindings['call'],'thread_id':'controller-native'}]
        altered=copy.deepcopy(bindings['call']);altered['actor']['load_epoch']=True;invalid.append(altered)
        altered=copy.deepcopy(bindings['call']);altered['locator']['direction']='sent';invalid.append(altered)
        for call in invalid:
            with self.subTest(call=call),self.assertRaises(PolicyError):shape(call,schema,{})
            with tempfile.TemporaryDirectory() as td:
                bad={**bindings,'call':call}
                with self.assertRaises(PolicyError):GrantStore(td,'issuer').issue('bad',bad)
                self.assertEqual(list(Path(td).iterdir()),[])


class BrokerTests(unittest.TestCase):
    def setUp(self):
        helper=policy_fixture.PolicyTests();helper.setUp()
        selected,entitlement,operation,observed=helper.selected('governance')
        def policy_factory(root):
            selected['project'].update(id='fixture',repository_id='fixture',coordination_root=str(root))
            return selected
        self.fixture=NativeOrchestrationFixture(writes=['Tasks'],policy_factory=policy_factory,
            protocol_version=getattr(self,'protocol_version',1))
        self.addCleanup(self.fixture.close)
        self.root=self.fixture.root
        for name in ('candidate','private','outputs'):(self.root/name).mkdir()
        (self.root/'.curator-disposable-proof.json').write_text('Synthetic broker test only.\n')
        self.owners=Owners(self.root,self.fixture.helper,memory_publish,memory_recovery,ontology_publication)
        directories={Path(m.__file__).resolve().parent for m in
            (self.owners.task,self.owners.memory,self.owners.memory_recovery,self.owners.ontology)}
        paths={p.resolve() for d in directories for p in d.glob('*.py')}
        paths.update(p.resolve() for p in (self.root/'.agents/skills').rglob('*.py'))
        self.manifest=source_manifest('/',[str(p).removeprefix('/') for p in sorted(paths)])
        self.profile={'schema_version':1,'name':'fixture','read_roots':[],
            'write_roots':[str(self.root/'candidate')],'denied_roots':[str(self.root/'private')],
            'executables':[],'channels':{k:'disabled' for k in CHANNELS},'network':[],'config_sha256':'0'*64}
        packet={'schema_version':1,'scope_id':'synthetic-broker-test','root':str(self.root),
            'device':self.root.stat().st_dev,'inode':self.root.stat().st_ino,
            'marker_sha256':file_snapshot(self.root,'.curator-disposable-proof.json')['sha256'],
            'manifest_sha256':digest(self.manifest),'profile_sha256':digest(self.profile),'runtime':{},
            'tools':sorted(TOOLS),'expires_at':(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),'synthetic_only':True}
        self.admission=VerificationAdmission(packet,digest(packet))
        policy=load_policy(self.root/'curator.yaml')
        entitlement.update(project_id='fixture',repository_id='fixture',coordination_root=str(self.root),paths=['Tasks'])
        operation.update(project_id='fixture',repository_id='fixture',coordination_root=str(self.root),paths=['Tasks'])
        observed['policy_sha256']=digest(policy)
        task=self.fixture.binding();task['revision']=self.fixture.state['revision']
        self.payload=self.fixture.driver.response_payload(self.fixture.state)
        operation['payload_sha256']=digest(self.payload)
        self.accepted={'tool':'task.response','actor':self.fixture.actor,'payload_sha256':digest(self.payload),
            'operation':operation,'automatic':False,'observation':observed,'entitlement':entitlement,
            'task':task,'targets':[],'sources':[],'owner':'task',
            'owner_state':{'schema_version':1,'inputs':[],'journal':None},
            'post_paths':[task['path']],'bootstrap_actor':'controller-native'}
        adapter=types.SimpleNamespace(native=self.fixture.native,authority=self.fixture.authority)
        self.broker=Broker(owners=self.owners,adapter=adapter,policy_path=self.root/'curator.yaml',
            ownership_map={'schema_version':1,'entries':[]},manifest=self.manifest,profile=self.profile,
            runtime_binding={},enforcement_proof=None,private_directory=self.root/'private',issuer='fixture',
            accepted_operations={'response1':self.accepted},verification_admission=self.admission,
            artifacts={'output1':{'producer':'worker-native','readers':['manager-native'],'root':str(self.root/'outputs'),
                'path':'candidate.txt','sha256':None,'max_bytes':1000}})

    def request(self):
        return {'operation_id':'response1','payload_sha256':digest(self.payload),'payload':self.payload}

    def dispatch(self,tool,request,actor=None):
        wire=next((name for name,logical in WIRE_TO_TOOL.items() if logical==tool),tool)
        context=self.fixture.context(wire,actor)
        with self.fixture.authority.invoke(context):return self.broker.dispatch_verified(context,request)

    def test_actual_task_owner_call_and_exact_success_receipt_retry(self):
        result=self.dispatch('task.response',self.request())
        self.assertEqual(result['state'],'owner_completed')
        state=self.fixture.helper.validate_task_folder(self.fixture.folder)[0]
        self.assertEqual(state['revision'],self.fixture.state['revision']+1)
        self.assertEqual(result,self.dispatch('task.response',self.request()))
        self.assertTrue(list((self.root/'private').glob('*-owner-*.json')))
        grant=self.broker.grants.inspect('response1')['grant']
        self.assertEqual(grant['call']['tool'],'task_response')
        self.assertEqual(grant['operation'],'task.response')

    def test_source_bound_wire_names_cannot_be_selected_by_model_arguments(self):
        specs=native_tool_specs()
        self.assertEqual({spec['name'] for spec in specs},set(WIRE_TO_TOOL))
        self.assertEqual(len(WIRE_TO_TOOL),len(TOOLS))
        self.assertTrue(all(spec['type']=='function' and '.' not in spec['name'] for spec in specs))
        context=self.fixture.context('task.response')
        with self.fixture.authority.invoke(context),self.assertRaises(PolicyError):
            self.broker.dispatch_verified(context,self.request())
        request=self.request();request['logical_tool']='task.response'
        with self.assertRaises(PolicyError):self.dispatch('task.response',request)

    def test_owner_failure_unavailable_unchanged_and_unknown_returns_are_not_consumed(self):
        from unittest.mock import patch
        cases=[({'status':'failed'},'failed'),({'status':'unavailable'},'unavailable'),
            ({'status':'unchanged'},'unchanged'),({'status':'created_with_warnings','recovery_required':True},'partial'),
            ({'status':'recorded','mutated':False,'errors':[],'recovery_required':False},'unrecognized'),
            ({'status':'recorded','mutated':True,'errors':['failure'],'recovery_required':False},'unrecognized')]
        for index,(result,expected) in enumerate(cases):
            operation_id='response'+str(index+10)
            self.broker.accepted[operation_id]=copy.deepcopy(self.accepted)
            request=self.request();request['operation_id']=operation_id
            with self.subTest(result=result),patch.object(self.owners,'dispatch',return_value=result):
                receipt=self.dispatch('task.response',request)
                self.assertEqual(receipt['state'],'owner_'+expected)
                self.assertEqual(self.broker.grants.inspect(operation_id)['state'],'owner-partial')

    def test_knowledge_owner_contracts_require_committed_records(self):
        memory={'state':'complete','records':[{'state':'committed'}],'journal_path':'control_records/memory/operation.json'}
        ontology={'status':'complete','files':[{'state':'committed'}],'intent_sha256':'1'*64}
        self.assertEqual(Owners.outcome('memory.publish',memory),'completed')
        self.assertEqual(Owners.outcome('ontology.publish',ontology),'completed')
        self.assertEqual(Owners.outcome('ontology.publish',memory),'unrecognized')
        self.assertEqual(Owners.outcome('memory.publish',ontology),'unrecognized')
        for operation,value,key in [('memory.publish',memory,'records'),('ontology.publish',ontology,'files')]:
            value[key][0]['state']='pending'
            self.assertEqual(Owners.outcome(operation,value),'unrecognized')

    def test_current_owner_state_and_journal_are_reopened_before_grant_issue(self):
        path='owner-state.json';(self.root/path).write_text('original')
        accepted=self.broker.accepted['response1']
        accepted['owner_state']={'schema_version':1,'inputs':[{'path':path,'sha256':file_snapshot(self.root,path)['sha256']}],'journal':None}
        (self.root/path).write_text('changed')
        with self.assertRaises(PolicyError) as exc:self.dispatch('task.response',self.request())
        self.assertEqual(exc.exception.code,'owner_state_changed')
        self.assertIsNone(self.broker.grants.inspect('response1'))
        accepted['owner_state']={'schema_version':1,'inputs':[],'journal':{'path':path,'sha256':'0'*64}}
        with self.assertRaises(PolicyError) as exc:self.dispatch('task.response',self.request())
        self.assertEqual(exc.exception.code,'owner_state_changed')
        accepted['owner_state']={'schema_version':1,'inputs':[{'path':'absent.json','sha256':None}],'journal':None}
        (self.root/'absent.json').symlink_to(self.root/'missing.json')
        with self.assertRaises(PolicyError):self.dispatch('task.response',self.request())

    def test_actual_owner_post_state_preserves_a_later_response_edit(self):
        self.dispatch('task.response',self.request())
        record=self.broker.grants.inspect('response1')
        response=next(path for path in record['post_state'] if '/responses/' in path)
        changed=(self.root/response).read_text()+'\nLater human edit.\n'
        (self.root/response).write_text(changed)
        with self.assertRaises(PolicyError) as exc:self.dispatch('task.response',self.request())
        self.assertEqual(exc.exception.code,'operation_changed')
        self.assertEqual((self.root/response).read_text(),changed)

    def test_absence_post_state_does_not_hide_a_broken_symlink(self):
        self.assertEqual(self.broker._post_state(['missing.json']),{'missing.json':None})
        (self.root/'missing.json').symlink_to(self.root/'nowhere.json')
        with self.assertRaises(PolicyError):self.broker._post_state(['missing.json'])

    def test_candidate_actor_automatic_profile_and_raw_protocol_fields_fail(self):
        for field in ('actor','automatic','profile','shell','method','grant'):
            request=self.request();request[field]=True
            with self.assertRaises(PolicyError):self.dispatch('task.response',request)
        with self.assertRaises(PolicyError):self.dispatch('process/spawn',{})
        with self.assertRaises(PolicyError):self.dispatch('task.response',self.request(),'worker-native')

    def test_production_gate_stays_closed_without_native_proof(self):
        self.broker.verification_admission=None
        with self.assertRaises(PolicyError):self.dispatch('task.response',self.request())

    def test_assignment_artifact_transfer_excludes_siblings(self):
        content=b'synthetic solver output'
        import hashlib
        value={'handle':'output1','sha256':hashlib.sha256(content).hexdigest(),'content':base64.b64encode(content).decode()}
        self.dispatch('artifact.submit',value,'worker-native')
        with self.assertRaises(PolicyError):self.dispatch('artifact.read',{'handle':'output1'},'sibling-native')
        result=self.dispatch('artifact.read',{'handle':'output1'},'manager-native')
        self.assertEqual(base64.b64decode(result['content']),content)
        with self.assertRaises(PolicyError):self.dispatch('artifact.submit',value,'worker-native')

    def test_automatic_origin_is_fixed_by_the_trusted_run(self):
        self.broker.accepted['response1']['automatic']=True
        with self.assertRaises(PolicyError) as exc:self.dispatch('task.response',self.request())
        self.assertEqual(exc.exception.code,'automatic_disabled')



    def test_actual_class_owner_and_route_control_admission(self):
        import hashlib
        path='AGENTS.md';raw=(self.root/path).read_bytes();source=hashlib.sha256(raw).hexdigest()
        self.broker.ownership_map={'schema_version':1,'entries':[{'id':'instructions','path':path,
            'pattern':False,'sha256':source,'class':'documentation','owner':'project','generator':None,
            'sources':[],'sections':[],'interfaces':[]}]}
        accepted=self.broker.accepted['response1']
        accepted.update(tool='target.classify',owner='project',routes=['project.governance'],
            targets=[{'identity':{'id':'instructions','path':path,'sha256':source},'ranges':[[0,len(raw)]]}])
        for permission in ('documentation','technical'):
            accepted['operation']['class']=permission;accepted['entitlement']['permissions']=[permission]
            with self.assertRaises(PolicyError) as exc:self.dispatch('target.classify',self.request())
            self.assertEqual(exc.exception.code,'classification_permission')
        accepted['operation']['class']='governance';accepted['entitlement']['permissions']=['governance']
        accepted['routes']=['project.documentation']
        with self.assertRaises(PolicyError) as exc:self.dispatch('target.classify',self.request())
        self.assertEqual(exc.exception.code,'classification_route')

class ForkBrokerTests(unittest.TestCase):
    """Actual disposable Task owner and GrantStore, synthetic protected transport."""
    protocol_version=2
    request=BrokerTests.request
    dispatch=BrokerTests.dispatch

    def setUp(self):
        import time
        from curator_runtime import ForkRuntimePool,ForkLease
        from curator_runtime_codex import ForkCodexAdapter
        BrokerTests.setUp(self)
        f=self.fixture;(self.root/'pool').mkdir()
        def no_launch(*args):raise AssertionError('This deterministic owner test must not launch native actors.')
        self.pool=ForkRuntimePool(native=f.native,protocol=f.protocol,registry=f.registry,adapter_factory=no_launch,
            directory=self.root/'pool',capacity=3,generation=1,deadline=time.monotonic()+30,
            owner_reconciler=self.broker.reconcile_actor_operations)
        assignment=f.state['orchestration']['assignments']['native-manager']
        self.adapter=types.SimpleNamespace(native=f.native,registry=f.registry,selected_protocol=f.protocol,
            actor_binding=copy.deepcopy(f.actors[f.actor]),authority=f.authority,wire_records=[],observation_handles={},
            closed_admission=False,cleanup_observation=None,quarantine=[])
        for name in ('load_observation','typed_receipt','role_receipt'):
            setattr(self.adapter,name,types.MethodType(getattr(ForkCodexAdapter,name),self.adapter))
        self.pool.leases['native-manager']=ForkLease('native-manager',1,'controller','manager','profile',{},None,
            state='ready',actor=copy.deepcopy(f.actors[f.actor]),adapter=self.adapter,epoch=1,creation=assignment['native_receipt'])
        self.broker.pool=self.pool

    def store(self,value):
        handle='observation-'+digest(value)
        self.adapter.wire_records.extend(value['frames']);self.adapter.observation_handles[handle]=value
        return self.pool._remember(self.pool.leases['native-manager'],{'handle':handle,'value':value})['handle']

    def event(self,kind,data,bindings):
        self.payload={'kind':kind,'data':data,'response':self.fixture.driver.response_payload(self.fixture.state)}
        accepted=self.broker.accepted['response1']
        accepted.update(tool='task.event',payload_sha256=digest(self.payload),receipt_bindings=bindings)
        accepted['operation']['payload_sha256']=digest(self.payload)

    def test_actual_v2_broker_owner_grant_preserves_authenticated_actor_and_rejects_cross_epoch_replay(self):
        result=self.dispatch('task.response',self.request());self.assertEqual(result['state'],'owner_completed')
        grant=self.broker.grants.inspect('response1')['grant']
        self.assertEqual(grant['call']['schema_version'],2)
        self.assertEqual(grant['call']['actor'],self.fixture.actors[self.fixture.actor])
        self.assertEqual(grant['call']['tool'],'task_response')
        self.assertEqual(self.dispatch('task.response',self.request()),result)
        self.fixture.bind_actor(self.fixture.actor,2)
        with self.assertRaises(PolicyError) as exc:self.dispatch('task.response',self.request())
        self.assertEqual(exc.exception.code,'grant_epoch')

    def test_unregistered_callback_namespace_is_rejected_before_task_mutation(self):
        before=(self.fixture.folder/'task.json').read_bytes();f=self.fixture
        frame={'id':701,'method':'item/tool/call','params':{'threadId':f.actor,'turnId':'turn-namespace','callId':'call-namespace',
            'namespace':'curator','tool':'task_response','arguments':self.request()}}
        with self.assertRaises(f.native.NativeError):f.authority.capture(frame,701,f.native.canonical(frame)+b'\n')
        self.assertEqual((f.folder/'task.json').read_bytes(),before);self.assertIsNone(self.broker.grants.inspect('response1'))

    def test_actual_task_event_receives_only_the_closed_typed_status_handle(self):
        value=self.fixture.roster(self.fixture.actor);handle=self.store(value)
        selected={'reservation':'native-manager','actor':self.fixture.actor,'epoch':1,'operation_id':value['operation_id']}
        self.event('assignment.observe',{'assignment_id':'native-manager','receipt_handle':handle,'changes':[]},{'receipt':selected})
        result=self.dispatch('task.event',self.request());self.assertEqual(result['state'],'owner_completed')
        state=self.fixture.helper.validate_task_folder(self.fixture.folder)[0]
        self.assertEqual(state['orchestration']['assignments']['native-manager']['observations'][-1]['receipt'],value)
        self.assertEqual(self.broker.grants.inspect('response1')['grant']['call']['tool'],'task_event')

    def test_raw_sequences_wrong_family_and_foreign_source_operation_leave_task_unchanged(self):
        value=self.fixture.roster(self.fixture.actor);handle=self.store(value)
        selected={'reservation':'native-manager','actor':self.fixture.actor,'epoch':1,'operation_id':value['operation_id']}
        before=(self.fixture.folder/'task.json').read_bytes()
        cases=[('assignment.observe',{'assignment_id':'native-manager','receipt_sequence':1,'changes':[]},selected),
            ('assignment.reads',{'assignment_id':'native-manager','role_reads_handle':handle},selected),
            ('assignment.observe',{'assignment_id':'native-manager','receipt_handle':handle,'changes':[]},{**selected,'operation_id':'foreign-source'})]
        for index,(kind,data,binding) in enumerate(cases):
            key='role_reads' if kind=='assignment.reads' else 'receipt'
            self.event(kind,data,{key:binding});operation_id='negative'+str(index)
            self.broker.accepted[operation_id]=copy.deepcopy(self.broker.accepted['response1'])
            request=self.request();request['operation_id']=operation_id
            with self.subTest(kind=kind),self.assertRaises(PolicyError):self.dispatch('task.event',request)
            self.assertEqual((self.fixture.folder/'task.json').read_bytes(),before)

    def test_sequential_actual_owner_mutations_reconcile_only_through_their_verified_chain(self):
        import time
        first=self.dispatch('task.response',self.request())
        self.fixture.binding();task=self.fixture.binding();task['revision']=self.fixture.state['revision']
        self.payload=self.fixture.driver.response_payload(self.fixture.state)
        second=copy.deepcopy(self.broker.accepted['response1']);second.update(task=task,payload_sha256=digest(self.payload))
        second['operation']['payload_sha256']=digest(self.payload);self.broker.accepted['response2']=second
        request=self.request();request['operation_id']='response2'
        self.assertEqual(self.dispatch('task.response',request)['state'],'owner_completed')
        actor=self.fixture.actors[self.fixture.actor]
        result=self.broker.reconcile_actor_operations(actor,time.monotonic()+2)
        self.assertEqual(result['state'],'reconciled')
        # Ordering the protected selections differently cannot alter the chain.
        self.broker.accepted=dict(reversed(list(self.broker.accepted.items())))
        self.assertEqual(self.broker.reconcile_actor_operations(actor,time.monotonic()+2),result)
        with self.assertRaises(PolicyError):self.broker.reconcile_actor_operations({**actor,'load_epoch':2},time.monotonic()+2)
        saved=self.broker.accepted.pop('response2')
        with self.assertRaises(PolicyError):self.broker.reconcile_actor_operations(actor,time.monotonic()+2)
        self.broker.accepted['response2']=saved
        path=self.fixture.folder/'task.json';path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaises(PolicyError):self.broker.reconcile_actor_operations(actor,time.monotonic()+2)

    def test_runtime_observation_handle_returns_to_caller_and_drives_actual_task_event(self):
        value=self.fixture.roster(self.fixture.actor)
        def status(operation_id,reservation_id):
            observed=copy.deepcopy(value);observed['operation_id']=operation_id
            handle='observation-'+digest(observed);self.adapter.wire_records.extend(observed['frames']);self.adapter.observation_handles[handle]=observed
            return {'handle':handle,'value':observed}
        self.adapter.status_receipt=status
        payload={'reservation':'native-manager'};accepted=copy.deepcopy(self.broker.accepted['response1'])
        accepted.update(tool='runtime.observe',owner='runtime',payload_sha256=digest(payload),runtime_reservations=['native-manager'],post_paths=[])
        accepted['operation']['payload_sha256']=digest(payload);self.broker.accepted['observe-manager']=accepted
        result=self.dispatch('runtime.observe',{'operation_id':'observe-manager','payload_sha256':digest(payload),'payload':payload})
        self.assertEqual(set(result['runtime']),{'handle','kind','actor','load_epoch'})
        handle=result['runtime']['handle'];self.assertEqual(result['runtime']['kind'],'status')
        self.event('assignment.observe',{'assignment_id':'native-manager','receipt_handle':handle,'changes':[]},
            {'receipt':{'reservation':'native-manager','actor':self.fixture.actor,'epoch':1,'operation_id':'observe-manager'}})
        self.assertEqual(self.dispatch('task.event',self.request())['state'],'owner_completed')

    def test_task_creation_returns_only_safe_identity_and_revision_for_the_next_native_call(self):
        f=self.fixture
        payload={'name':'Second disposable native task','description':'Check public creation metadata.',
            'definition_of_done':['Observed bounded Task identity.'],'orchestration_enabled':True,'orchestration_version':2,
            'controller_origin':f.origin,'native_protocol':f.protocol}
        selected=copy.deepcopy(self.broker.accepted['response1']);selected.update(tool='task.create',task=None,bootstrap_actor=f.actor,
            payload_sha256=digest(payload),post_paths=[])
        selected['operation']['payload_sha256']=digest(payload);self.broker.accepted['create-task']=selected
        result=self.dispatch('task.create',{'operation_id':'create-task','payload_sha256':digest(payload),'payload':payload})
        self.assertEqual(set(result['task']),{'task_id','path','revision'});self.assertEqual(result['task']['revision'],1)
        state=self.fixture.helper.validate_task_folder((self.root/result['task']['path']).parent)[0]
        self.assertEqual(state['task_id'],result['task']['task_id'])

    def test_async_release_completion_is_observed_through_broker_without_changing_original_receipt(self):
        import time
        from curator_runtime import ForkLease
        from curator_runtime_codex import ForkCodexAdapter
        f=self.fixture;f.event('subtask.define',{'subtask_id':'subtask1','baseline':f.driver.base()})
        f.driver.state=f.state;f.driver.folder=f.folder
        data=f.driver.assignment_data('worker-case','worker');data['runtime']=copy.deepcopy(f.state['orchestration']['assignments']['native-manager']['runtime'])
        f.event('assignment.reserve',data);created=f.launch(f.actor,'worker-native','worker-case')
        f.event('assignment.receipt',{'assignment_id':'worker-case','receipt':created})
        f.event('assignment.reads',{'assignment_id':'worker-case','role_reads':f.role_acknowledgement('worker-case')})
        task=f.binding();task['revision']=f.state['revision']
        worker=types.SimpleNamespace(native=f.native,registry=f.registry,selected_protocol=f.protocol,actor_binding=copy.deepcopy(f.actors['worker-native']),
            wire_records=copy.deepcopy(created['frames']),observation_handles={},closed_admission=False,cleanup_observation=None,quarantine=[],begin_stop=lambda deadline:None)
        for name in ('close_actor_admission','typed_receipt','load_observation'):
            setattr(worker,name,types.MethodType(getattr(ForkCodexAdapter,name),worker))
        def close(deadline):
            worker.close_actor_admission();worker.cleanup_observation={'state':'owned_process_group_stopped','companion':{'state':'owned_companion_stopped'}}
            return worker.cleanup_observation
        worker.close=close
        self.pool.leases['worker-case']=ForkLease('worker-case',1,'native-manager','worker','profile',{},None,
            state='ready',actor=copy.deepcopy(worker.actor_binding),adapter=worker,epoch=1,creation=created)
        payload={'reservation':'worker-case'}
        for name,tool in [('release-worker','runtime.release'),('observe-release','runtime.observe')]:
            selected=copy.deepcopy(self.broker.accepted['response1']);selected.update(tool=tool,owner='runtime',task=task,
                payload_sha256=digest(payload),post_paths=[],runtime_reservations=['worker-case'])
            selected['operation']['payload_sha256']=digest(payload);self.broker.accepted[name]=selected
        request={'operation_id':'release-worker','payload_sha256':digest(payload),'payload':payload}
        context=f.context('runtime_release')
        with f.authority.invoke(context):original=self.broker.dispatch_verified(context,request)
        self.assertEqual(original['runtime']['state'],'release_pending')
        self.assertEqual(self.pool.drain_releases(time.monotonic()+2),{})
        self.pool.acknowledge_callback(context);self.pool.drain_releases(time.monotonic()+2)
        self.assertEqual(self.dispatch('runtime.release',request),original)
        observed=self.dispatch('runtime.observe',{**request,'operation_id':'observe-release'})
        self.assertEqual(observed['runtime']['kind'],'runtime_release')
        self.broker.accepted['response1']['task']=task
        self.event('assignment.observe',{'assignment_id':'worker-case','receipt_handle':observed['runtime']['handle'],'changes':[]},
            {'receipt':{'reservation':'worker-case','actor':'worker-native','epoch':1,'operation_id':'release-worker'}})
        self.assertEqual(self.dispatch('task.event',self.request())['state'],'owner_completed')


if __name__=='__main__':unittest.main()
