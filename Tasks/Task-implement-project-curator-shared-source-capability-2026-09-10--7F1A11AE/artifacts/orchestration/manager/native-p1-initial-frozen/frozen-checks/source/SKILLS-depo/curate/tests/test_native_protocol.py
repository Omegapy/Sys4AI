import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / 'scripts'))
sys.path.insert(0, str(PACKAGE.parent / 'agent-task/scripts'))
import orchestration_state as orch
from curator_runtime import RuntimeCoordinator
from curator_runtime_codex import shape
from curator_policy import PolicyError
native=orch.native


def observation(method, params, child=None, sequence=1):
    event={'method':method,'params':params}
    out={'schema_version':1,'backend':'codex-app-server-v2','session_id':'session-fixture',
        'sequence':sequence,'raw_sha256':hashlib.sha256(native.canonical(event)).hexdigest(),'event':event}
    if child is not None:out['child']=child
    return out


def launch(parent='parent-native', child='child-native'):
    return observation('item/completed',{'threadId':parent,'turnId':'turn-native','item':{
        'type':'collabAgentToolCall','id':'item-native','tool':'spawnAgent','status':'completed',
        'senderThreadId':parent,'receiverThreadIds':[child],'agentsStates':{child:{'status':'running'}}}},
        {'id':child,'parentThreadId':parent,'source':{'subAgent':{'thread_spawn':{
            'parent_thread_id':parent,'depth':1,'agent_path':None}}}})


class NativeProtocolTests(unittest.TestCase):
    def test_native_ids_lineage_and_no_forged_legacy_receipts(self):
        self.assertEqual(native.observation(launch(),launch=True,parent='parent-native'),'child-native')
        for field in ('parentThreadId','id'):
            receipt=launch();receipt['child'][field]='foreign'
            with self.assertRaises(native.NativeError):native.observation(receipt,launch=True,parent='parent-native')
        with self.assertRaises(native.NativeError):native.observation(launch(),launch=True,session='foreign')
        with self.assertRaises(orch.OrchestrationError):orch.receipt(launch(),launch=True,version=1)
        with self.assertRaises(native.NativeError):orch.receipt({'tool':'collaboration.spawn_agent','result':{'task_name':'/root/a'}},launch=True,version=2)

    def test_completed_turn_is_idle_and_missing_roster_is_not_stop(self):
        receipt=observation('turn/completed',{'threadId':'child-native','turn':{
            'id':'turn-native','items':[],'status':'completed','error':None}})
        self.assertEqual(native.observation(receipt,subject='child-native'),'idle')
        self.assertIsNone(native.observation(receipt,subject='another-native'))

    def test_only_live_transport_context_can_authorize_owner(self):
        authority=native.TransportAuthority('session-fixture')
        frame={'id':1,'method':'item/tool/call','params':{'callId':'call1','threadId':'manager-native',
            'turnId':'turn1','tool':'memory.publish','arguments':{}}}
        context=authority.capture(frame,1)
        with self.assertRaises(native.NativeError):native.require_live(context.binding(),'manager-native')
        with authority.invoke(context):
            self.assertIs(native.require_live(context.binding(),'manager-native'),context)
            forged=dict(context.binding());forged['thread_id']='worker-native'
            with self.assertRaises(native.NativeError):native.require_live(forged,'worker-native')
        with self.assertRaises(native.NativeError):authority.capture(frame,2)
        with self.assertRaises(TypeError):context.__reduce__()

    def test_team_capacity_retains_all_required_slots_and_uncertainty(self):
        for category,count in [('generic',1),('complex',4),('extra-complex',6)]:
            from curator_runtime import TEAMS
            coordinator=RuntimeCoordinator(None,'model','high',1)
            coordinator.reserve_team(category,'controller','0'*64,{x:'1'*64 for x in TEAMS[category]})
            first=coordinator.next_reservation()
            self.assertEqual(len(coordinator.pending),count-1)
            coordinator.uncertain(first.reservation)
            self.assertFalse(coordinator.capacity_ready())
            self.assertEqual(first.state,'launch_uncertain')

    def test_requested_settings_cannot_mark_an_actor_ready(self):
        coordinator=RuntimeCoordinator(None,'model','high',1)
        coordinator.reserve_team('generic','controller','0'*64,{'worker':'1'*64})
        actor=coordinator.next_reservation();actor.native_id='child-native';actor.state='bootstrap'
        with self.assertRaises(PolicyError):coordinator.ready(actor.reservation,{},{
            'model':'model','reasoningEffort':'high','profile_sha256':'1'*64,'observed':False},{})

    def test_bound_ready_idle_or_interrupted_session_does_not_free_capacity(self):
        from curator_runtime import TEAMS
        coordinator=RuntimeCoordinator(None,'model','high',1)
        coordinator.reserve_team('complex','controller','0'*64,{x:'1'*64 for x in TEAMS['complex']})
        actor=coordinator.next_reservation();actor.native_id='child-native'
        pending=list(coordinator.pending)
        for state in ('ready','idle','idle_unreconciled','stopped','failed'):
            actor.state=state
            with self.subTest(state=state):
                self.assertFalse(coordinator.capacity_ready())
                with self.assertRaises(PolicyError):coordinator.next_reservation()
                self.assertEqual(list(coordinator.pending),pending)

    def test_wire_ref_and_union_validation_rejects_unknown_fields(self):
        definitions={'Value':{'type':'object','properties':{'id':{'type':'string'}},'required':['id']}}
        shape({'id':'actual'},{'allOf':[{'$ref':'#/definitions/Value'}]},definitions)
        with self.assertRaises(PolicyError):shape({'id':'actual','forged':True},{'$ref':'#/definitions/Value'},definitions)



    def test_stop_continues_past_idle_and_failed_observations(self):
        class Adapter:
            def __init__(self):self.interrupted=[]
            def observe(self,native_id):
                if native_id=='bad':raise PolicyError('offline','Unavailable native observer.')
                return {'thread':{'status':{'type':'idle' if native_id=='idle' else 'active'}}}
            def interrupt(self,native_id):self.interrupted.append(native_id);return {}
        adapter=Adapter();coordinator=RuntimeCoordinator(adapter,'model','high',4)
        from curator_runtime import Actor
        for name in ('idle','bad','active'):
            coordinator.actors[name]=Actor(name,'parent','worker','0'*64,'1'*64,native_id=name,state='ready')
        result=coordinator.stop()
        self.assertEqual(adapter.interrupted,['active'])
        self.assertEqual(result['idle']['state'],'idle_unreconciled')
        self.assertEqual(result['bad']['state'],'stop_uncertain')

    def test_child_override_is_rejected_before_profile_mutation(self):
        from curator_runtime_codex import CodexAdapter
        adapter=object.__new__(CodexAdapter);adapter.threads={'child':{}};adapter.bootstrap_profile='bootstrap'
        calls=[]
        def request(method,params):
            calls.append((method,params))
            return {'thread':{'model':'wrong-model','reasoningEffort':'high','canAcceptDirectInput':True}}
        adapter._request=request
        with self.assertRaises(PolicyError):adapter.select_child_profile('child','worker-profile','expected-model','high')
        self.assertEqual(calls,[('thread/read',{'threadId':'child','includeTurns':False})])

    def test_correlated_turn_response_retains_newer_terminal_observation(self):
        from curator_runtime_codex import CodexAdapter
        adapter=object.__new__(CodexAdapter);adapter.threads={'child':{}};adapter.turns={}
        active={'id':'turn1','status':'inProgress','items':[],'error':None}
        adapter._request=lambda method,params:{'turn':active}
        adapter.followup('child','Synthetic scope')
        self.assertEqual(adapter.turns['child'],active)
        terminal={**active,'status':'failed','error':{'message':'synthetic failure'}}
        adapter.turns['child']=terminal
        adapter.followup('child','Synthetic scope')
        self.assertEqual(adapter.turns['child'],terminal)

    def test_proof_error_metadata_never_retains_provider_text(self):
        path=PACKAGE.parents[1]/'Verification/project-curator-release/run-native-proof.py'
        spec=importlib.util.spec_from_file_location('proof_runner_fixture',path)
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        result=runner.safe_error({'message':'Model unsupported. PRIVATE-SENTINEL',
            'codexErrorInfo':{'httpConnectionFailed':{'httpStatusCode':400}},'additionalDetails':'PRIVATE-SENTINEL'})
        self.assertNotIn('PRIVATE-SENTINEL',json.dumps(result))
        self.assertIn('unsupported',result['categories'])
        self.assertEqual(result['codex_error_info']['httpConnectionFailed']['http_status_code'],400)
        packet={'root':'/synthetic','inputs':{'shared/'+name:'1'*64 for name in
            ('CURATOR.md','common-input.txt','SOUL.md','Roles/project-sub-agent/AGENTS.md','Roles/project-sub-agent/ROLE.md')}}
        a=runner.readiness_contract(packet,'solver_a');b=runner.readiness_contract(packet,'solver_b')
        self.assertEqual(a,b)
        self.assertEqual(len(a['reads']),4)
        self.assertEqual(len(runner.readiness_contract(packet,'controller')['reads']),2)
        final={'type':'agentMessage','id':'final1','phase':'final_answer','text':'Tool unavailable: api_key=PRIVATE-SENTINEL'}
        saved=runner.safe_item(final)
        self.assertIn('Tool unavailable',saved['final_diagnostic']['text'])
        self.assertNotIn('PRIVATE-SENTINEL',json.dumps(saved))
        for phase in ('commentary',None,'final'):
            self.assertNotIn('final_diagnostic',runner.safe_item({**final,'phase':phase}))
        self.assertEqual(runner.safe_item({**final,'phase':None})['phase'],'unknown')
        output=runner.safe_item({'type':'functionCallOutput','id':'call1','name':'synthetic_tool','namespace':None,
            'output':[{'type':'input_text','text':'unknown tool'},{'type':'encrypted_content','encrypted_content':'PRIVATE-REASONING'}]})
        self.assertEqual(output['diagnostics'][0]['text'],'unknown tool')
        self.assertNotIn('PRIVATE-REASONING',json.dumps(output))
        packet['stage']='tool-routing-diagnostic'
        self.assertEqual(len(runner.readiness_contract(packet,'controller')['reads']),1)

    def test_native_command_matcher_accepts_exact_observed_wrapper_only(self):
        import shlex
        path=PACKAGE.parents[1]/'Verification/project-curator-release/run-native-proof.py'
        spec=importlib.util.spec_from_file_location('proof_command_fixture',path)
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        expected=['/synthetic/python','-I','-B','/synthetic/read-probe.py','/synthetic/input file.txt']
        inner=shlex.join(expected);wrapped=shlex.join(['/bin/zsh','-c',inner])
        self.assertFalse(runner.exact_native_command(inner,expected))
        self.assertTrue(runner.exact_native_command(wrapped,expected))
        for value in (None,"'unterminated",inner+' extra',shlex.join(['/bin/zsh','-lc',inner]),
            shlex.join(['/bin/bash','-c',inner]),shlex.join(['/bin/zsh','-c',inner+'; extra']),
            shlex.join(['/bin/zsh','-c',inner+' $(extra)']),shlex.join(['/bin/zsh','-c',inner,'extra'])):
            with self.subTest(command=value):self.assertFalse(runner.exact_native_command(value,expected))

    def test_current_runtime_surface_closure_holds_enabled_and_unknown_routes(self):
        from curator_runtime_codex import CodexAdapter, DISABLED_FEATURES
        config={'features':{name:False for name in DISABLED_FEATURES},'mcp_servers':{},'web_search':'disabled',
            'browser_use':{'allow_history_access':False,'default_origin_policy':{
                name:'deny' for name in ('access','downloads','uploads','full_cdp_access')}},
            'computer_use':{'default_app_access':'deny'},
            'apps':{'_default':{'enabled':False,'destructive_enabled':False,'open_world_enabled':False}},
            'desktop':{'realtimeVoiceScreenContextEnabled':False,'keepRemoteControlAwakeWhilePluggedIn':False}}
        adapter=object.__new__(CodexAdapter);adapter.cwd='/synthetic'
        selected=copy.deepcopy(config);adapter._request=lambda method,params:{'config':selected}
        self.assertFalse(adapter.inspect_tool_configuration()['surfaces']['apps_enabled'])
        for surface,key,value in [('features','auth_elicitation',True),('features','shell_snapshot',True),
            ('browser_use','allow_history_access',True),('computer_use','default_app_access','allow'),
            ('desktop','realtimeVoiceScreenContextEnabled',True),('desktop','unknownToolRoute',True)]:
            selected=copy.deepcopy(config);selected[surface][key]=value
            with self.subTest(surface=surface,key=key),self.assertRaises(PolicyError):adapter.inspect_tool_configuration()
        selected=copy.deepcopy(config);selected['apps']['_default']['enabled']=True
        with self.assertRaises(PolicyError):adapter.inspect_tool_configuration()
        selected=copy.deepcopy(config);selected['features']['code_mode_host']=True
        with self.assertRaises(PolicyError):adapter.inspect_tool_configuration(code_mode_host=True)
        selected['features']['code_mode_host']={'enabled':True,'disable_in_process_fallback':True}
        self.assertTrue(adapter.inspect_tool_configuration(code_mode_host=True)['code_mode_host']['disable_in_process_fallback'])
        with self.assertRaises(PolicyError):adapter.inspect_tool_configuration()

    def test_companion_ownership_rejects_mismatched_parent_and_reused_pid(self):
        from curator_runtime_codex import CodexAdapter
        from types import SimpleNamespace
        import os
        root={'pid':5000,'parent':4000,'group':5000,'uid':os.getuid(),'started':[1,1],'executable':'/synthetic/codex'}
        child={'pid':5001,'parent':5000,'group':5001,'uid':os.getuid(),'started':[2,1],'executable':'/synthetic/codex-code-mode-host'}
        for mode in ('mismatched_parent','reused_pid'):
            adapter=object.__new__(CodexAdapter);adapter.process=SimpleNamespace(pid=5000,poll=lambda:None)
            adapter.companion={'path':'/synthetic/codex-code-mode-host','sha256':'1'*64};adapter._server_identity=root
            adapter._last_process_poll=0;adapter._owned_processes={};adapter.companion_observations={}
            adapter.companion_verified=False;adapter.companion_identity_uncertain=False
            adapter._process_snapshot=lambda:{5001:{'pid':5001,'parent':5000}}
            reads={}
            def kernel(pid):
                reads[pid]=reads.get(pid,0)+1
                if pid==5000:return copy.deepcopy(root)
                if pid!=5001:return None
                value=copy.deepcopy(child)
                if mode=='mismatched_parent':value['parent']=9999
                elif reads[pid]>1:value['started']=[9,9]
                return value
            adapter._kernel_identity=kernel
            adapter._observe_companion(force=True)
            self.assertEqual(adapter._owned_processes,{})
            self.assertEqual(adapter.companion_observations,{})
            self.assertFalse(adapter.companion_verified)
            self.assertTrue(adapter.companion_identity_uncertain)

    def test_final_companion_observation_failure_prevents_stop_success(self):
        from curator_runtime_codex import CodexAdapter
        from types import SimpleNamespace
        from unittest.mock import patch
        adapter=object.__new__(CodexAdapter)
        adapter.process=SimpleNamespace(pid=5000,poll=lambda:0,stdin=None,stdout=None,stderr=None)
        adapter.selector=SimpleNamespace(close=lambda:None)
        adapter.companion={'enabled':True};adapter.companion_verified=True
        adapter.companion_identity_uncertain=False
        adapter.companion_observations={5001:{'pid':5001,'group':5001,'started':[2,1]}}
        adapter._owned_processes={5001:{'pid':5001,'group':5001}}
        def unavailable(**kwargs):raise PolicyError('process_observation_unavailable','Synthetic failure')
        adapter._observe_companion=unavailable
        with patch('curator_runtime_codex.os.killpg',side_effect=ProcessLookupError),patch('curator_runtime_codex.os.kill',side_effect=ProcessLookupError):result=adapter.close()
        self.assertEqual(result['state'],'owned_process_group_stopped')
        self.assertEqual(result['companion_observation_error'],'process_observation_unavailable')
        self.assertEqual(result['companion']['state'],'uncertain')
        self.assertTrue(result['companion']['identity_uncertain'])
        self.assertEqual(result['companion']['groups'],[{'group':5001,'state':'stopped'}])

    def test_companion_moved_group_prevents_stop_success_without_new_signal(self):
        from curator_runtime_codex import CodexAdapter
        from types import SimpleNamespace
        from unittest.mock import patch
        import time
        adapter=object.__new__(CodexAdapter);adapter.process=SimpleNamespace(pid=5000)
        adapter.companion={'enabled':True};adapter.companion_verified=True
        adapter.companion_identity_uncertain=False
        old={'pid':5001,'group':5001,'started':[2,1],'uid':123,'executable':'/synthetic/codex-code-mode-host'}
        adapter.companion_observations={5001:old};adapter._owned_processes={5001:old}
        adapter._kernel_identity=lambda pid:{**old,'group':9000}
        with patch('curator_runtime_codex.os.killpg',side_effect=ProcessLookupError) as groups,patch('curator_runtime_codex.os.kill',return_value=None) as identities:
            result=adapter._close_companion(time.monotonic()+1)
        self.assertEqual(result['state'],'uncertain')
        self.assertEqual(result['identity_checks'][0]['code'],'original_helper_still_present')
        groups.assert_called_once_with(5001,0)
        identities.assert_called_once_with(5001,0)

    def test_failed_controller_turn_stops_before_dependent_launch_or_deadline(self):
        import contextlib
        import io
        import tempfile
        import time
        from unittest.mock import patch
        path=PACKAGE.parents[1]/'Verification/project-curator-release/run-native-proof.py'
        spec=importlib.util.spec_from_file_location('proof_stop_fixture',path)
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        class FailedTransport:
            def __init__(self,*args,**kwargs):
                self.events=[];self.raw_frames={};self.turns={};self.threads={};self.process=None
                self.method_counts={};self.request_counts={};self.starts=0
            def start(self):pass
            def inspect_tool_configuration(self,**kwargs):return {'fixture':True}
            def inspect_model(self,model,effort):return {'fixture':True}
            def start_controller(self,**kwargs):
                self.threads['controller']={}
                return {'thread':{'id':'controller'},'model':'model','reasoningEffort':'high','activePermissionProfile':{'id':'bootstrap'}}
            def followup(self,actor,text):
                self.starts+=1
                self.turns[actor]={'id':'turn1','status':'failed','items':[],
                    'error':{'message':'synthetic unsupported model','codexErrorInfo':'badRequest'}}
                return {'turn':self.turns[actor]}
            def pump(self,timeout):pass
            def begin_stop(self,deadline):pass
            def close(self,deadline):return {'state':'fixture_closed'}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'trusted').mkdir();(root/'trusted/canary').write_text('synthetic')
            packet={'root':str(root),'settings':{'model':'model','effort':'high'},
                'bounds':{'supervised_seconds':420,'io_wait_seconds':30,'host_turn_starts':5,
                    'artifact_bytes':20000,'expected_native_identities':3,'stop_grace_seconds':20},
                'sources':{str(PACKAGE/'scripts/curator_policy.py'):'unused_by_synthetic_transport'},
                'profiles':{'bootstrap':{'id':'bootstrap','override':'synthetic'}},'runtime':{'path':'synthetic'},
                'child_config':{'path':'synthetic'},'stage':'synthetic_transport_stop_test',
                'canaries':{'trusted/canary':runner.hash_file(root/'trusted/canary')}}
            started=time.monotonic()
            with patch('curator_runtime_codex.CodexAdapter',FailedTransport),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run_stage(packet),2)
            self.assertLess(time.monotonic()-started,2)
            report=json.loads((root/'native-feasibility-result.json').read_text())
            self.assertEqual(report['code'],'native_turn_failed')
            self.assertEqual(report['host_turn_starts'],1)
            self.assertEqual(report['identities'],{'controller':'controller'})
            self.assertTrue(report['canaries_unchanged'])
            # The same synthetic transport omits effective delegation evidence;
            # the reduced mode must stop before controller creation or any turn.
            (root/'native-feasibility-result.json').unlink()
            packet['stage']='tool-routing-diagnostic'
            with patch('curator_runtime_codex.CodexAdapter',FailedTransport),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run_stage(packet),2)
            report=json.loads((root/'native-feasibility-result.json').read_text())
            self.assertEqual(report['code'],'diagnostic_delegation_unproven')
            self.assertEqual(report['host_turn_starts'],0)
            self.assertEqual(report['identities'],{})

class ProtectedArchiveTests(unittest.TestCase):
    def fixture(self):
        import time
        from curator_runtime_codex import ForkCodexAdapter
        a=object.__new__(ForkCodexAdapter);a.native=native;a.actor_binding={'thread_id':'archive-native'}
        a.deadline_seconds=10;a.absolute_deadline=time.monotonic()+10;a.wire_records=[];a.history_reads=[]
        turns=[{'id':'turn-one','items':[{'type':'userMessage','text':'synthetic whole problem'}]},
            {'id':'turn-two','items':[{'type':'agentMessage','text':'synthetic private full item '*300}]}]
        pages=[]
        for index,turn in enumerate(turns):
            params={'threadId':'archive-native','itemsView':'full','sortDirection':'asc','limit':1}
            if index:params['cursor']='cursor-two'
            result={'data':[turn],'nextCursor':None if index else 'cursor-two'}
            rows=[]
            for direction,frame in [('sent',{'id':index+1,'method':'thread/turns/list','params':params}),('received',{'id':index+1,'result':result})]:
                row=native.wire_record(direction,len(a.wire_records)+1,native.canonical(frame)+b'\n');a.wire_records.append(row);rows.append(row)
            pages.append({'request':params,'frames':[{key:row[key] for key in ('direction','sequence','raw_sha256','canonical_sha256')} for row in rows]})
        frame={'id':1,'method':'item/tool/call','params':{'threadId':'archive-native','turnId':'turn-two','callId':'artifact-call',
            'tool':'artifact_submit','arguments':{'content':'synthetic'}}}
        a.wire_records.append(native.wire_record('received',5,native.canonical(frame)+b'\n'))
        a.history_reads=[{'thread_id':'archive-native','pages':pages,'sha256':hashlib.sha256(native.canonical(turns)).hexdigest(),
            'turns':2,'complete':True}]
        return a

    def test_complete_raw_pages_and_callbacks_reconstruct_from_bounded_shards(self):
        import tempfile
        a=self.fixture()
        with tempfile.TemporaryDirectory() as root:
            selected=a.archive_evidence(root,max_bytes=200000,shard_bytes=1024)
            checked=a.verify_evidence_archive(selected,max_bytes=200000)
            self.assertEqual(checked['records'],5);self.assertEqual(checked['complete_history_reads'],1)
            self.assertFalse(checked['raw_bodies_returned'])
            shards=list(Path(root).glob('*.part'));self.assertGreater(len(shards),2)
            self.assertTrue(all(p.stat().st_size<=1024 for p in shards))
            shards[0].write_bytes(shards[0].read_bytes()+b'x')
            with self.assertRaises(PolicyError):a.verify_evidence_archive(selected,max_bytes=200000)

    def test_missing_page_frame_and_archive_bound_do_not_produce_replayable_success(self):
        import tempfile
        a=self.fixture();a.wire_records.pop(1)
        with tempfile.TemporaryDirectory() as root:
            selected=a.archive_evidence(root,max_bytes=200000,shard_bytes=1024)
            with self.assertRaises(PolicyError):a.verify_evidence_archive(selected,max_bytes=200000)
        a=self.fixture()
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(PolicyError):a.archive_evidence(root,max_bytes=1000,shard_bytes=1024)
            self.assertFalse((Path(root)/'index.json').exists())


class ForkProtocolTests(unittest.TestCase):
    def setUp(self):
        self.protocol={'schema_version':2,'backend':'codex-app-server-v2','broker_run_id':'synthetic-run',
            'lineage_kind':'thread-fork',**{k:'1'*64 for k in ('runtime_sha256','schema_sha256','source_sha256','profile_sha256')}}
        self.actor={'thread_id':'child-native','session_id':'shared-native-session','connection_id':'connection-one','load_epoch':1,
            'runtime_instance':{'pid':5000,'parent':4000,'group':5000,'uid':501,'started':[123,456],'executable':'/synthetic/codex'}}
        self.registry=native.LoadedActorRegistry('synthetic-run');self.registry.bind(self.actor)
        self.authority=native.TransportAuthorityV2(self.protocol,self.actor,self.registry)

    def record(self,direction,sequence,frame):return native.wire_record(direction,sequence,native.canonical(frame)+b'\n')

    def callback(self,identifier=1):
        return {'id':identifier,'method':'item/tool/call','params':{'arguments':{},'callId':'actual-call',
            'threadId':'child-native','turnId':'native-turn','tool':'artifact_submit'}}

    def status(self):
        return {'schema_version':2,'backend':'codex-app-server-v2','broker_run_id':'synthetic-run','kind':'status',
            'actor':copy.deepcopy(self.actor),'operation_id':'observe-one','reservation_id':'reserved-child',
            'frames':[self.record('received',1,{'method':'thread/status/changed','params':{'threadId':'child-native','status':{'type':'idle'}}})],
            'facts':{'native_state':'idle'}}

    def creation(self):
        settings={'model':'gpt-6-astra','reasoning_effort':'xhigh','provider':'openai','profile_id':'child-profile','cwd':'/synthetic/child'}
        metadata={'id':'child-native','sessionId':'shared-native-session','parentThreadId':None,'forkedFromId':'source-native',
            'source':'appServer','path':'/synthetic/native.jsonl','model':'gpt-6-astra','reasoningEffort':'xhigh','modelProvider':'openai'}
        params={'threadId':'source-native','lastTurnId':'cut-turn','model':'gpt-6-astra','modelProvider':'openai',
            'config':{'model_reasoning_effort':'xhigh'},'permissions':'child-profile','cwd':'/synthetic/child'}
        result={'thread':metadata,'model':'gpt-6-astra','reasoningEffort':'xhigh','modelProvider':'openai','cwd':'/synthetic/child',
            'activePermissionProfile':{'id':'child-profile'}}
        value=self.status();value.update(kind='creation',frames=[
            self.record('sent',1,{'id':1,'method':'thread/fork','params':params}),self.record('received',2,{'id':1,'result':result}),
            self.record('sent',3,{'id':2,'method':'thread/read','params':{'threadId':'child-native','includeTurns':False}}),
            self.record('received',4,{'id':2,'result':{'thread':metadata}})],
            facts={'source_thread_id':'source-native','logical_parent_id':'manager-native','metadata':metadata,'settings':settings,
                'history_cut':{'mode':'lastTurnId','turn_id':'cut-turn','history_sha256':'2'*64,'input_sha256':'3'*64}})
        return value

    def test_malformed_v2_discriminator_and_rpc_id_are_bounded(self):
        for malformed in ({},[],None,True):
            value=self.status();value['kind']=malformed
            with self.subTest(kind=malformed),self.assertRaises(native.NativeError):native.validate_observation_v2(value)
            with self.subTest(request_id=malformed),self.assertRaises(native.NativeError):self.authority.capture(self.callback(malformed),1)
        self.assertEqual(self.authority._pending,{})

    def test_malformed_nested_native_wire_objects_are_bounded(self):
        for malformed in ('malformed',[],None,True):
            value=self.creation();frame=copy.deepcopy(value['frames'][1]['frame'])
            frame['result']['activePermissionProfile']=malformed;value['frames'][1]=self.record('received',2,frame)
            with self.subTest(profile=malformed),self.assertRaises(native.NativeError):native.validate_observation_v2(value)
            value=self.status();frame=copy.deepcopy(value['frames'][0]['frame']);frame['params']=malformed
            value['frames'][0]=self.record('received',1,frame)
            with self.subTest(params=malformed),self.assertRaises(native.NativeError):native.validate_observation_v2(value)
        value=self.status();value['facts']['native_state']={}
        with self.assertRaises(native.NativeError):native.validate_observation_v2(value)

    def test_fork_preserves_null_agent_parent_and_shared_session_but_checks_actual_lineage(self):
        value=self.creation()
        self.assertEqual(native.observation(value,launch=True,parent='source-native',session='synthetic-run'),'child-native')
        self.assertIsNone(value['facts']['metadata']['parentThreadId'])
        for key,replacement in [('forkedFromId','another-source'),('reasoningEffort','low')]:
            altered=copy.deepcopy(value);altered['facts']['metadata'][key]=replacement
            with self.subTest(key=key),self.assertRaises(native.NativeError):native.validate_observation_v2(altered)
        altered=copy.deepcopy(value);altered['frames'][2]['direction']='received'
        with self.assertRaises(native.NativeError):native.validate_observation_v2(altered)
        altered=copy.deepcopy(value);frame=copy.deepcopy(altered['frames'][3]['frame'])
        frame['result']['thread']['modelProvider']='foreign-provider'
        altered['frames'][3]=self.record('received',4,frame)
        with self.assertRaises(native.NativeError):native.validate_observation_v2(altered)

    def test_actual_raw_frame_and_canonical_digest_have_distinct_meaning(self):
        frame=self.callback();raw=json.dumps(frame,indent=2).encode()+b'\n'
        context=self.authority.capture(frame,3,raw)
        self.assertNotEqual(context.binding()['locator']['raw_sha256'],context.binding()['locator']['canonical_sha256'])
        with self.authority.invoke(context):self.assertIs(native.require_current(self.protocol,'child-native'),context)
        value=self.status();value['frames'][0]['raw_sha256']='0'*64
        with self.assertRaises(native.NativeError):native.validate_observation_v2(value)

    def test_resume_epoch_does_not_revive_old_context_or_foreign_actor(self):
        context=self.authority.capture(self.callback(),1)
        self.registry.close_admission(self.actor)
        resumed=copy.deepcopy(self.actor);resumed.update(load_epoch=2,connection_id='connection-two')
        self.registry.bind(resumed)
        with self.assertRaises(native.NativeError):
            with self.authority.invoke(context):pass
        other=native.TransportAuthorityV2(self.protocol,resumed,self.registry)
        frame=self.callback(2);frame['params']['threadId']='foreign-native'
        with self.assertRaises(native.NativeError):other.capture(frame,1)
        valid=other.capture(self.callback(2),2)
        with other.invoke(valid):
            self.assertEqual(native.require_current(self.protocol,'child-native').actor['load_epoch'],2)
            with self.assertRaises(native.NativeError):native.require_live(context.binding(),'child-native')
        with self.assertRaises(native.NativeError):self.registry.bind(resumed)

    def test_status_cannot_substitute_for_creation_or_local_capacity_release(self):
        value=self.status()
        self.assertEqual(native.observation(value,subject='child-native',session='synthetic-run'),'idle')
        with self.assertRaises(native.NativeError):native.validate_observation_v2(value,expected_kind='runtime_release')
        with self.assertRaises(native.NativeError):native.observation(value,launch=True)

    def test_client_rpc_and_server_callback_can_share_id_without_collision(self):
        from curator_runtime_codex import CodexAdapter,ForkCodexAdapter
        from unittest.mock import patch
        adapter=object.__new__(ForkCodexAdapter);adapter.closed_admission=False;adapter.wire_sequence=0
        adapter.wire_records=[];adapter.native=native;adapter.request_id=1
        params={'threadId':'child-native','includeTurns':False};result={'thread':{'id':'child-native'}}
        def actual_records(method,request):
            adapter.wire_records.extend([self.record('sent',1,{'id':1,'method':method,'params':request}),
                self.record('received',2,self.callback(1)),self.record('received',3,{'id':1,'result':result})])
            return result
        with patch.object(CodexAdapter,'_request',side_effect=actual_records):
            self.assertEqual(adapter._request('thread/read',params),result)
        self.assertEqual(len(adapter.last_rpc['records']),2)
        self.assertEqual(adapter.wire_records[1]['frame']['method'],'item/tool/call')


class PreuserStorageAndDiagnosticTests(unittest.TestCase):
    def test_rpc_error_retains_correlated_safe_diagnostics_before_discard(self):
        from curator_runtime_codex import ForkCodexAdapter
        from unittest.mock import patch
        a=object.__new__(ForkCodexAdapter)
        a.closed_admission=False;a.wire_sequence=0;a.wire_records=[];a.native=native
        a.method_schemas=ForkCodexAdapter.METHOD_SCHEMAS;a.stopping=False;a.request_id=0
        a.request_counts={};a.pending_methods={};a.responses={};a.rpc_errors=[];a.manifest={}
        a._remaining=lambda:1;a._validate=lambda name,value:None
        error={'code':-32600,'message':'thread selected-id is not materialized yet; includeTurns is unavailable before first user message','data':{'token':'PRIVATE-SENTINEL'}}
        def send(frame):
            reply={'id':frame['id'],'error':error}
            a.responses[frame['id']]=reply
            a.wire_sequence+=1
            a.wire_records.append(native.wire_record('received',a.wire_sequence,native.canonical(reply)+b'\n'))
        a._send=send
        with patch('curator_runtime_codex.verify_manifest'):
            for message in (error['message'],'PRIVATE-SENTINEL password=secret /private/account'):
                error['message']=message
                with self.assertRaises(PolicyError):a._request('thread/read',{'threadId':'selected-id','includeTurns':True})
        self.assertEqual(a.responses,{})
        self.assertEqual(a.rpc_errors[0]['category'],'pre_user_history_unavailable')
        self.assertEqual(a.rpc_errors[0]['locator']['direction'],'received')
        self.assertEqual([row['request_id'] for row in a.rpc_errors],[1,2])
        self.assertTrue(all(row['method']=='thread/read' and row['rpc_code']==-32600 for row in a.rpc_errors))
        self.assertNotIn('PRIVATE-SENTINEL',json.dumps(a.rpc_errors))
        self.assertNotIn('/private/account',json.dumps(a.rpc_errors))

    def test_preuser_storage_uses_returned_path_then_independent_metadata_only(self):
        from curator_runtime_codex import ForkCodexAdapter
        from types import SimpleNamespace
        a=object.__new__(ForkCodexAdapter);a.actor_binding={'thread_id':'seed-native'}
        initial={'id':'seed-native','sessionId':'seed-native','parentThreadId':None,'forkedFromId':None,
            'source':'vscode','path':'/synthetic/owned.jsonl','model':'gpt-6-astra','reasoningEffort':'xhigh','modelProvider':'openai'}
        a.threads={'seed-native':initial};a.last_rpc={'records':[]};steps=[]
        def bind(actor,thread):steps.append(('bind',actor,thread['path']));return {'path':thread['path']}
        def request(method,params):steps.append((method,params));return {'thread':dict(initial)}
        a.storage_admission=SimpleNamespace(bind_storage=bind,require_owned=lambda actor:steps.append(('owned',actor)))
        a._request=request
        result=a.observe_preuser_storage()
        self.assertEqual(steps[0],('bind','seed-native','/synthetic/owned.jsonl'))
        self.assertEqual(steps[1],('thread/read',{'threadId':'seed-native','includeTurns':False}))
        self.assertFalse(result['include_turns'])
        a._request=lambda method,params:{'thread':{**initial,'modelProvider':'foreign-provider'}}
        with self.assertRaises(PolicyError):a.observe_preuser_storage()

    def test_effective_instruction_sources_are_exact_and_hash_only(self):
        import tempfile
        from curator_runtime_codex import ForkCodexAdapter
        from curator_confinement import file_snapshot
        with tempfile.TemporaryDirectory() as td:
            path=Path(td).resolve()/'AGENTS.md';path.write_text('Synthetic instruction source.\n')
            info=file_snapshot('/',str(path).lstrip('/'));a=object.__new__(ForkCodexAdapter)
            a.instruction_sources=[{'path':str(path),**{key:info[key] for key in ('sha256','device','inode','size','mode')}}]
            result=a.verify_instruction_sources({'instructionSources':[str(path)]})
            self.assertFalse(result['contents_copied']);self.assertNotIn('Synthetic instruction',json.dumps(result))
            for selected in (None,[],[str(path),'/unselected/AGENTS.md']):
                with self.assertRaises(PolicyError):a.verify_instruction_sources({'instructionSources':selected})
            path.write_text('Changed instruction source.\n')
            with self.assertRaises(PolicyError):a.verify_instruction_sources({'instructionSources':[str(path)]})

    def test_preuser_partial_error_requires_exact_actor_request_code_and_owned_header(self):
        from curator_runtime_codex import ForkCodexAdapter,NativeRPCError,safe_rpc_error
        actor='seed-native';params={'threadId':actor,'includeTurns':True}
        frame={'id':7,'error':{'code':-32600,'message':f'thread {actor} is not materialized yet; includeTurns is unavailable before first user message','data':None}}
        locator={'direction':'received','sequence':12,'raw_sha256':'a'*64,'canonical_sha256':'b'*64}
        valid=NativeRPCError('thread/read',params,7,frame,locator)
        self.assertEqual(valid.preuser_actor,actor)
        cases=[('thread/fork',params,7,frame,locator),('thread/read',{**params,'includeTurns':False},7,frame,locator),
            ('thread/read',params,8,frame,locator),('thread/read',params,7,{**frame,'id':8},locator),
            ('thread/read',params,7,frame,{**locator,'direction':'sent'})]
        for change in ({'code':-32603},{'message':frame['error']['message'].replace(actor,'another-actor')},{'data':{'unselected':'value'}}):
            cases.append(('thread/read',params,7,{'id':7,'error':{**frame['error'],**change}},locator))
        for args in cases:
            with self.subTest(args=args):self.assertIsNone(NativeRPCError(*args).preuser_actor)
        a=object.__new__(ForkCodexAdapter);a.actor_binding={'thread_id':actor};a.request_id=7;a.turns={}
        from types import SimpleNamespace
        a.storage_admission=SimpleNamespace(observe_index_metadata=lambda selected:{'state':'absent','actor':selected,'metadata':None})
        a.rpc_errors=[safe_rpc_error('thread/read',7,frame,locator)];calls=[]
        def persist(operation,reservation):calls.append((operation,reservation));raise valid
        a.persist_history=persist
        a.observe_preuser_storage=lambda:{'ownership':{'path':'/synthetic/owned.jsonl'},'frames':[{'sequence':14}]}
        result=a.materialize_preuser_storage('persist-once','seed')
        self.assertEqual(calls,[('persist-once','seed')]);self.assertTrue(result['partial_persistence'])
        self.assertEqual(result['materialization']['response_locator']['sequence'],12)
        self.assertEqual(result['frames'][0]['sequence'],14)
        def missing_header():raise PolicyError('native_storage_unproven','Missing actual owned header.')
        a.observe_preuser_storage=missing_header
        with self.assertRaises(PolicyError):a.materialize_preuser_storage('separate-synthetic-case','seed')

    def test_absent_row_exception_does_not_admit_present_or_postuser_history(self):
        from curator_runtime_codex import ForkCodexAdapter,NativeRPCError,safe_rpc_error
        from types import SimpleNamespace
        actor='seed-native';params={'threadId':actor,'includeTurns':True}
        frame={'id':7,'error':{'code':-32601,'message':'list_turns is not supported yet'}}
        locator={'direction':'received','sequence':12,'raw_sha256':'a'*64,'canonical_sha256':'b'*64}
        error=NativeRPCError('thread/read',params,7,frame,locator)
        self.assertEqual(error.preuser_actor,actor);self.assertTrue(error.requires_absent_row)
        self.assertIsNone(NativeRPCError('thread/read',params,7,{'id':7,'error':{**frame['error'],'message':'other is not supported yet'}},locator).preuser_actor)
        a=object.__new__(ForkCodexAdapter);a.actor_binding={'thread_id':actor};a.request_id=7;a.turns={}
        a.rpc_errors=[safe_rpc_error('thread/read',7,frame,locator)]
        def persist(operation,reservation):raise error
        a.persist_history=persist;a.observe_preuser_storage=lambda:{'ownership':{'path':'/synthetic/owned'}}
        absent={'state':'absent','actor':actor,'metadata':None}
        a.storage_admission=SimpleNamespace(observe_index_metadata=lambda selected:absent)
        self.assertEqual(a.materialize_preuser_storage('op','seed')['index_metadata'],absent)
        for observation in ({'state':'present','actor':actor,'metadata':{'history_mode':'paginated'}},
                            {'state':'present','actor':actor,'metadata':{'history_mode':'legacy'}},
                            {'state':'absent','actor':'another-actor','metadata':None}):
            a.storage_admission.observe_index_metadata=lambda selected,value=observation:value
            with self.assertRaises(PolicyError):a.materialize_preuser_storage('op','seed')
        a.storage_admission.observe_index_metadata=lambda selected:absent
        a.turns={actor:{'id':'observed-user-turn'}}
        with self.assertRaises(PolicyError) as blocked:a.materialize_preuser_storage('op','seed')
        self.assertEqual(blocked.exception.code,'preuser_only')

    def test_owned_runtime_startup_disables_history_writers_without_enabling_transcript(self):
        from curator_runtime_codex import DISABLED_FEATURES
        path=PACKAGE.parents[1]/'Verification/project-curator-release/run-native-proof.py'
        spec=importlib.util.spec_from_file_location('p0_storage_controls_fixture',path)
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        packet={'stage':'native-fork-p0','profiles':{},'child_config':{'path':'/synthetic/role.toml'}}
        selected=runner.runtime_overrides(packet)
        for name in ('background_paginated_rollout_migration','local_thread_store_compression','local_thread_store_shared_compression'):
            self.assertIn(name,DISABLED_FEATURES);self.assertIn('features.'+name+'=false',selected)
        self.assertIn('features.transcript_v2=false',selected);self.assertIn('features.sqlite=true',selected)


class LocalEnvironmentTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from curator_runtime_codex import ForkCodexAdapter
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'home/.codex').mkdir(parents=True);(self.root/'shared').mkdir()
        self.a=object.__new__(ForkCodexAdapter);self.a.cwd=str(self.root/'shared');self.a._local_verified=False
        self.a.environment={'HOME':str(self.root/'home'),'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','LANG':'en_US.UTF-8',
            'TMPDIR':str(self.root),'PYTHONDONTWRITEBYTECODE':'1'}
        self.a.local_environment={'id':'local','cwd':self.a.cwd,'runtime_workspace_roots':[],
            'shell':{'name':'zsh','path':'/bin/zsh'},'configuration_path':str(self.root/'home/.codex/environments.toml'),'configuration_state':'absent'}
        self.calls=[];self.status={'status':'ready'}
        self.info={'shell':{'name':'zsh','path':'/bin/zsh'},'cwd':Path(self.a.cwd).as_uri()}
        def request(method,params):
            self.calls.append((method,params));self.a.last_rpc={'records':[{'method':method,'params':params}]}
            return self.status if method=='environment/status' else self.info
        self.a._request=request

    def test_local_metadata_is_required_before_allocation_and_unknown_routes_hold(self):
        result=self.a.inspect_local_environment();self.assertTrue(self.a._local_verified)
        self.assertEqual(self.calls,[('environment/status',{'environmentId':'local'}),('environment/info',{'environmentId':'local'})])
        self.assertEqual(len(result['frames']),2)
        for status in ('pending','disconnected','unknown'):
            self.status={'status':status}
            with self.subTest(status=status),self.assertRaises(PolicyError):self.a.inspect_local_environment()
            self.assertFalse(self.a._local_verified)
        self.status={'status':'ready'};self.info['cwd']='file:///unselected'
        with self.assertRaises(PolicyError):self.a.inspect_local_environment()
        self.info['cwd']=Path(self.a.cwd).as_uri();self.info['shell']={'name':'bash','path':'/bin/bash'}
        with self.assertRaises(PolicyError):self.a.inspect_local_environment()

    def test_absent_configuration_and_minimal_environment_gate_precede_start(self):
        from curator_runtime_codex import CodexAdapter
        from unittest.mock import patch
        self.a.verify_local_configuration()
        config=Path(self.a.local_environment['configuration_path']);config.write_text('PRIVATE-CONFIG-CONTENTS')
        with patch.object(CodexAdapter,'start') as start,self.assertRaises(PolicyError):self.a.start()
        start.assert_not_called();config.unlink();config.symlink_to(self.root/'missing')
        with self.assertRaises(PolicyError):self.a.verify_local_configuration()
        config.unlink();self.a.environment['CODEX_EXEC_SERVER_URL']='unselected'
        with self.assertRaises(PolicyError):self.a.verify_local_configuration()
        del self.a.environment['CODEX_EXEC_SERVER_URL'];self.a.local_environment['id']='remote'
        with self.assertRaises(PolicyError):self.a.inspect_local_environment()

    def test_seed_and_each_turn_select_only_exact_local_environment(self):
        self.a.inspect_local_environment();self.calls=[];self.a.threads={'seed-native':{}};self.a.turns={}
        self.a._begin_creation=lambda *args:None;self.a._bind_response=lambda *args,**kwargs:'seed-native'
        def request(method,params):
            self.calls.append((method,params));self.a.last_rpc={'records':[]}
            return {'thread':{'id':'seed-native'}} if method=='thread/start' else {'turn':{'id':'turn1','status':'inProgress'}}
        self.a._request=request
        self.a.start_seed(settings={'model':'gpt-6-astra','reasoning_effort':'xhigh','provider':'openai'},profile='read-only',dynamic_tools=[],instructions='Synthetic',operation_id='seed-op',reservation_id='seed')
        self.a.followup('seed-native','Synthetic input')
        for method,params in self.calls:
            self.assertEqual(params['environments'],[{'environmentId':'local','cwd':self.a.cwd,'runtimeWorkspaceRoots':[]}])
            self.assertEqual(params['cwd'],self.a.cwd);self.assertEqual(params['runtimeWorkspaceRoots'],[])
        self.assertEqual(self.calls[0][1]['permissions'],'read-only')

    def test_transient_group_permission_errors_only_repeat_read_only_probes(self):
        from curator_runtime_codex import CodexAdapter
        from types import SimpleNamespace
        from unittest.mock import patch
        import time
        a=object.__new__(CodexAdapter);a.process=SimpleNamespace(pid=5000,poll=lambda:0,stdin=None,stdout=None,stderr=None)
        a.selector=SimpleNamespace(close=lambda:None);a.companion=None;a._observe_companion=lambda **kwargs:None
        count=0
        def transient(group,sig):
            nonlocal count
            self.assertEqual((group,sig),(5000,0));count+=1
            if count==1:raise PermissionError
            raise ProcessLookupError
        with patch('curator_runtime_codex.os.killpg',side_effect=transient):result=a.close(deadline=time.monotonic()+1)
        self.assertEqual(result['state'],'owned_process_group_stopped');self.assertEqual(result['observation_permission_errors'],1)
        with patch('curator_runtime_codex.os.killpg',side_effect=PermissionError) as probe:
            result=a.close(deadline=time.monotonic()+.02)
        self.assertEqual(result['state'],'uncertain');self.assertEqual(result['code'],'group_status_unavailable')
        self.assertTrue(all(call.args==(5000,0) for call in probe.call_args_list))


class P1EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=PACKAGE.parents[1]/'Verification/project-curator-release/run-native-proof.py'
        spec=importlib.util.spec_from_file_location('p1_evidence_fixture',path);cls.runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.runner)

    def test_engine_digest_vectors_and_common_key_program_do_not_emit_hidden_values(self):
        import shutil,subprocess
        executable=shutil.which('node');self.assertIsNotNone(executable,'Existing JavaScript engine required for bounded digest verification.')
        values=['','abc','a'*55,'a'*56,'a'*64,'a'*1000,'0'*64,'{"case":"load"}']
        source=self.runner.P1_SHA256+'\nconsole.log(JSON.stringify('+json.dumps(values)+'.map(sha256)));'
        result=subprocess.run([executable,'--input-type=module'],input=source.encode(),capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr.decode());self.assertEqual(json.loads(result.stdout),[hashlib.sha256(value.encode()).hexdigest() for value in values])
        for slot in ('solver_a','solver_b'):
            program=self.runner.p1_helper_program('store',slot)
            self.assertIn('key="curator-p1-private-v1"',program);self.assertNotIn('marker:',program)
            prefix='const saved=new Map();globalThis.store=(k,v)=>saved.set(k,v);globalThis.load=k=>saved.get(k);globalThis.text=v=>console.log(JSON.stringify(v));\n'
            result=subprocess.run([executable,'--input-type=module'],input=(prefix+program).encode(),capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr.decode());observed=json.loads(result.stdout)
            self.assertEqual(set(observed),{'case','slot','direct'});self.assertEqual(set(observed['direct']),{'state','sha256'})
            self.assertRegex(observed['direct']['sha256'],'^[a-f0-9]{64}$')

    def test_owned_cell_raw_turn_and_epoch_associations_reject_relabeling_or_extra_stores(self):
        import tempfile,time
        fixture=ForkProtocolTests();fixture.setUp();actor=fixture.actor
        program='text({value:"synthetic"});\n';turn='actual-turn'
        records=[{'type':'session_meta','payload':{'id':actor['thread_id']}},
            {'type':'event_msg','payload':{'type':'task_started','turn_id':turn}},
            {'type':'response_item','payload':{'type':'custom_tool_call','name':'exec','call_id':'cell-one','input':program}},
            {'type':'response_item','payload':{'type':'custom_tool_call_output','call_id':'cell-one','output':[{'type':'input_text','text':'{"value":"synthetic"}'}]}}]
        frames=[fixture.record('sent',1,{'id':1,'method':'turn/start','params':{'threadId':actor['thread_id'],'input':[]}}),
            fixture.record('received',2,{'id':1,'result':{'turn':{'id':turn,'status':'inProgress'}}})]
        receipt={'actor':actor,'frames':frames}
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'owned.jsonl';path.write_bytes(b''.join(native.canonical(row)+b'\n' for row in records))
            cells=self.runner.p1_owned_cells(path,actor['thread_id'],max_bytes=100000,deadline=time.monotonic()+1)
            cells[0]['actor_binding']=copy.deepcopy(actor)
            self.assertEqual(self.runner.p1_check_cells(cells,turn,[program],turn_receipt=receipt,native=native),cells)
            changed=copy.deepcopy(cells);changed[0]['turn_id']='fabricated-turn'
            with self.assertRaises(ValueError):self.runner.p1_check_cells(changed,'fabricated-turn',[program])
            changed=copy.deepcopy(cells);changed[0]['actor_binding']['load_epoch']=2
            with self.assertRaises(ValueError):self.runner.p1_check_cells(changed,turn,[program],turn_receipt=receipt,native=native)
            changed=copy.deepcopy(cells);changed[0]['program']='store("curator-p1-private-v1","forged");'+program
            with self.assertRaises(ValueError):self.runner.p1_check_cells(changed,turn,[changed[0]['program']],turn_receipt=receipt,native=native)
            with self.assertRaises(ValueError):self.runner.p1_check_cells(cells+copy.deepcopy(cells),turn,[program],turn_receipt=receipt,native=native)

    def test_selected_instruction_reader_delivers_text_and_matching_hashes(self):
        import tempfile,subprocess
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'role.txt').write_text('Complete selected role instructions.\n')
            (root/'contract.json').write_text(json.dumps({'Roles/role/ROLE.md':'role.txt'}))
            result=subprocess.run([sys.executable,'-I','-B','-c',self.runner.P1_READ,str(root),'contract.json'],capture_output=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr.decode());value=json.loads(result.stdout)
            self.assertEqual(value['contents'],{'Roles/role/ROLE.md':'Complete selected role instructions.\n'})
            self.assertEqual(value['reads'],{'Roles/role/ROLE.md':hashlib.sha256((root/'role.txt').read_bytes()).hexdigest()})


if __name__=='__main__':unittest.main()
