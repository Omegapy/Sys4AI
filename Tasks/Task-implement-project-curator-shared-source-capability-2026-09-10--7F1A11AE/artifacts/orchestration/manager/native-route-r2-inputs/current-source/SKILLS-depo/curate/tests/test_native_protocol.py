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

if __name__=='__main__':unittest.main()
