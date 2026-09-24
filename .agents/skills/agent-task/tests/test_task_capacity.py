"""Project-local bounded Task capacity tests. Native fixtures are synthetic."""
import copy, hashlib, json, os
from pathlib import Path
import unittest
import test_orchestration_state as fixtures
task_state=fixtures.task_state
class CapacityProposalTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.OrchestrationTests(); self.f.setUp(); self.addCleanup(self.f.temp.cleanup)
    def pad(self,target):
        original=copy.deepcopy(self.f.state); stamp=original['created_at']
        def trial(n):
            d=copy.deepcopy(original)
            d['thread_refs']=[dict(thread_id=f'capacity-fixture-{i:05}',title='Synthetic capacity fixture '+'x'*350,first_seen_at=stamp,last_seen_at=stamp) for i in range(n)]
            return task_state.canonical_state(d)
        compact=lambda d:json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n'
        lo,hi=0,12000
        while lo<hi:
            mid=(lo+hi+1)//2
            if len(compact(trial(mid)).encode())<=target:lo=mid
            else:hi=mid-1
        d=trial(lo);remaining=target-len(compact(d).encode())
        for r in reversed(d['thread_refs']):
            n=min(remaining,500-len(r['title']));r['title']+='z'*n;remaining-=n
            if not remaining:break
        self.assertEqual(remaining,0)
        raw=task_state.task_json_text(d);self.assertEqual(len(raw.encode()),target)
        (self.f.folder/'task.json').write_text(raw);(self.f.folder/'TASK.md').write_text(task_state.render_task_markdown(d));task_state.write_index(self.f.root/'Tasks',[d]);self.f.state=d
        cp,result=self.f.run_cli('validate',d['task_id']);self.assertEqual(cp.returncode,0,result)
        return copy.deepcopy(d)
    def assert_error(self,code,fn):
        with self.assertRaises(task_state.TaskError) as got:fn()
        self.assertEqual(got.exception.code,code)
    def test_existing_compact_record_encoding_is_unchanged(self):
        before=self.pad(940_000)
        expected=(json.dumps(task_state.canonical_state(before),ensure_ascii=False,separators=(',',':'))+'\n').encode()
        self.assertGreater(len(task_state.json_text(before).encode()),1_000_000)
        self.assertEqual((self.f.folder/'task.json').read_bytes(),expected)
        self.assertEqual(task_state.task_json_text(task_state.canonical_state(before)).encode(),expected)
    def test_existing_pretty_boundary_and_utf8_preserved(self):
        v={'text':'é'*499991}
        while len(task_state.json_text(v).encode())<1_000_000:v['text']+='x'
        self.assertEqual(len(task_state.json_text(v).encode()),1_000_000)
        self.assertEqual(task_state.task_json_text(v),task_state.json_text(v))
        v['text']+='x'
        encoded=task_state.task_json_text(v)
        self.assertNotEqual(encoded,task_state.json_text(v));self.assertEqual(json.loads(encoded),v);self.assertIn('é',encoded)
    def test_new_exact_state_bound_and_refusal(self):
        v={'text':''};base=len((json.dumps(v,separators=(',',':'))+'\n').encode())
        v['text']='x'*(2_000_000-base)
        self.assertEqual(len(task_state.task_json_text(v).encode()),2_000_000)
        v['text']+='x';self.assert_error('ORCH_STATE_LIMIT',lambda:task_state.task_json_text(v))
    def test_payload_and_response_limits_unchanged(self):
        self.assertEqual(task_state.MAX_PAYLOAD_BYTES,1_000_000);self.assertEqual(task_state.MAX_RESPONSE_BYTES,250_000)
        self.assert_error('PAYLOAD_TOO_LARGE',lambda:task_state.parse_json_bytes(b' '*(1_000_001),'fixture'))
    def test_json_reader_refuses_above_new_bound(self):
        p=self.f.root/'oversized.json';p.write_bytes(b' '*(2_000_001))
        self.assert_error('JSON_TOO_LARGE',lambda:task_state.read_json_file(p,'fixture'))
    def test_intent_encoder_remains_bounded(self):
        self.assert_error('ORCH_INTENT_LIMIT',lambda:task_state.transaction_intent_text({'fixture':'x'*2_000_000}))
    def test_large_real_transaction_preserves_all_history(self):
        before=self.pad(1_200_000)
        self.f.event('subtask.define',dict(subtask_id='capacity_work',baseline=self.f.base()))
        after=self.f.state
        self.assertEqual(after['thread_refs'],before['thread_refs'])
        self.assertEqual(after['orchestration']['events'][:-1],before['orchestration']['events'])
        self.assertEqual(after['revision'],before['revision']+1)
        self.assertEqual(self.f.run_cli('validate',after['task_id'])[0].returncode,0)
    def test_large_fault_recovery_is_exact_and_idempotent(self):
        before=self.pad(1_200_000)
        result,_=self.f.event('subtask.define',dict(subtask_id='capacity_recover',baseline=self.f.base()),fault='after_state_publish',fail='TRANSACTION_INCOMPLETE')
        op=result['errors'][0]['operation_id'];intent=json.loads((self.f.root/'Tasks/.tmp'/f'{op}.json').read_text())
        expected=task_state.task_json_text(task_state.canonical_state(intent['planned_state'])).encode()
        self.assertEqual(intent['post_state_sha256'],hashlib.sha256(expected).hexdigest())
        payload=dict(repair_type='transaction',operation_id=op,actor=self.f.actor,execution_id=self.f.exec_id,generation=1)
        cp,repaired=self.f.run_cli('reconcile',before['task_id'],'--expected-revision',str(before['revision']),payload=payload)
        self.assertEqual(cp.returncode,0,repaired);self.assertEqual((self.f.folder/'task.json').read_bytes(),expected)
        after=json.loads(expected);self.assertEqual(after['thread_refs'],before['thread_refs']);self.assertEqual(after['orchestration']['events'][:-1],before['orchestration']['events'])
        cp,again=self.f.run_cli('reconcile',before['task_id'],'--expected-revision',str(before['revision']),payload=payload)
        self.assertEqual(cp.returncode,0,again);self.assertEqual(again['status'],'already_reconciled')
    def test_actual_oversized_state_rejected_without_staging(self):
        self.pad(1_999_000);before=self.f.tree_hash();b=self.f.base();b['objective']='x'*15000
        self.f.event('subtask.define',dict(subtask_id='capacity_too_large',baseline=b),fail='ORCH_STATE_LIMIT')
        self.assertEqual(self.f.tree_hash(),before)
    def test_actual_oversized_intent_cleans_only_own_temporary_files(self):
        self.f.define();self.f.assign('worker1','worker');self.pad(1_790_000)
        p=self.f.root/'output/input.txt';p.parent.mkdir(exist_ok=True);p.write_text('x'*249000)
        untouched=self.f.folder/'responses/.unrelated.txn';untouched.write_text('Retain this unrelated fixture file.\n')
        before=self.f.tree_hash()
        self.f.event('artifact.register',dict(artifact_id='too_large_intent',assignment_id='worker1',source_path='output/input.txt'),fail='ORCH_INTENT_LIMIT')
        self.assertEqual(self.f.tree_hash(),before);self.assertTrue(untouched.exists());self.assertEqual(list((self.f.root/'Tasks/.tmp').glob('*.json')),[])
if __name__=='__main__':unittest.main()
