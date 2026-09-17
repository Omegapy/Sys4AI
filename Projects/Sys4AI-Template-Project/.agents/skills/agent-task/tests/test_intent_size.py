"""Bounded intent encoding; synthetic native fixtures are not runtime proof."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import test_orchestration_state as fixture_module
task_state = fixture_module.task_state


class IntentSizeTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture_module.OrchestrationTests()
        self.f.setUp()
        self.addCleanup(self.f.temp.cleanup)

    def pad(self, target=982000, compact=False):
        # Build only a disposable valid metadata fixture. History and response
        # records remain exactly as produced by the real helper bootstrap.
        state = copy.deepcopy(self.f.state)
        stamp = state['created_at']
        def candidate(count):
            trial = copy.deepcopy(state)
            trial['thread_refs'] = [dict(thread_id=f'fixture-{i:05}', title='Synthetic metadata ' + 'x'*180,
                first_seen_at=stamp, last_seen_at=stamp) for i in range(count)]
            return task_state.canonical_state(trial)
        encode = (lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))+"\n") if compact else task_state.json_text
        low, high = 0, 6000
        while low < high:
            mid = (low+high+1)//2
            if len(encode(candidate(mid)).encode()) <= target: low = mid
            else: high = mid-1
        state = candidate(low)
        (self.f.folder/'task.json').write_text(task_state.task_json_text(state))
        (self.f.folder/'TASK.md').write_text(task_state.render_task_markdown(state))
        task_state.write_index(self.f.root/'Tasks', [state])
        self.f.state = state
        cp, result = self.f.run_cli('validate', state['task_id'])
        self.assertEqual(cp.returncode, 0, result)
        self.assertGreater((self.f.folder/'task.json').stat().st_size, target-500)
        return copy.deepcopy(state)

    def repair(self, result, expected_revision):
        operation = result['errors'][0]['operation_id']
        cp, repaired = self.f.run_cli('reconcile', self.f.state['task_id'], '--expected-revision', str(expected_revision),
            payload=dict(repair_type='transaction',operation_id=operation,actor=self.f.actor,execution_id=self.f.exec_id,generation=1))
        return cp, repaired

    def test_near_cap_schema2_artifact_response_and_recovery(self):
        before = self.pad()
        raw_before = (self.f.folder/'task.json').read_bytes()
        result, _ = self.f.event('subtask.define', dict(subtask_id='bounded',baseline=self.f.base()),
            fault='after_response_publish',fail='TRANSACTION_INCOMPLETE')
        path = self.f.root/'Tasks/.tmp'/f"{result['errors'][0]['operation_id']}.json"
        raw = path.read_bytes(); intent = json.loads(raw)
        self.assertGreater(len(task_state.json_text(intent).encode()), task_state.MAX_JSON_BYTES)
        self.assertLessEqual(len(raw), task_state.MAX_JSON_BYTES)
        self.assertEqual((self.f.folder/'task.json').read_bytes(),raw_before)
        self.assertEqual(intent['post_state_sha256'],hashlib.sha256(task_state.json_text(intent['planned_state']).encode()).hexdigest())
        cp, repaired = self.repair(result,before['revision']);self.assertEqual(cp.returncode,0,repaired)
        after = json.loads((self.f.folder/'task.json').read_text())
        self.assertEqual(after['thread_refs'],before['thread_refs'])
        self.assertEqual(after['orchestration']['events'][:-1],before['orchestration']['events'])
        self.assertEqual((self.f.folder/'task.json').read_text(),task_state.json_text(task_state.canonical_state(after)))
        self.assertEqual(after['revision'],before['revision']+1)
        self.assertTrue((self.f.folder/intent['artifacts'][0]['path']).is_file())
        cp, repeated = self.repair(result,before['revision']);self.assertEqual(cp.returncode,0,repeated)
        self.assertEqual(repeated['status'],'already_reconciled')
        print(json.dumps(dict(case='near_cap',before=len(raw_before),canonical_after=(self.f.folder/'task.json').stat().st_size,
            compact_intent=len(raw),pretty_intent=len(task_state.json_text(intent).encode()))))

    def test_old_pretty_intent_still_recovers(self):
        before = self.f.state['revision']
        result,_=self.f.event('subtask.define',dict(subtask_id='legacy',baseline=self.f.base()),fault='after_response_publish',fail='TRANSACTION_INCOMPLETE')
        path=self.f.root/'Tasks/.tmp'/f"{result['errors'][0]['operation_id']}.json"
        intent=json.loads(path.read_text());path.write_text(task_state.json_text(intent))
        cp,repaired=self.repair(result,before);self.assertEqual(cp.returncode,0,repaired)
        self.assertEqual((self.f.folder/'task.json').read_text(),task_state.json_text(task_state.canonical_state(intent['planned_state'])))

    def test_changed_post_state_recovery_is_denied(self):
        before=self.pad()
        result,_=self.f.event('subtask.define',dict(subtask_id='changed',baseline=self.f.base()),fault='after_state_publish',fail='TRANSACTION_INCOMPLETE')
        state=json.loads((self.f.folder/'task.json').read_text());state['current_summary']='A later independently changed fixture value.'
        altered=task_state.json_text(task_state.canonical_state(state));(self.f.folder/'task.json').write_text(altered)
        cp,repaired=self.repair(result,before['revision']);self.assertNotEqual(cp.returncode,0)
        self.assertEqual(repaired['errors'][0]['code'],'ORCH_RECOVERY_STATE_HASH')
        self.assertEqual((self.f.folder/'task.json').read_text(),altered)

    def test_canonical_cap_still_rejects_before_any_staging(self):
        self.pad(target=999500, compact=True);before=self.f.tree_hash();baseline=self.f.base();baseline['objective']='x'*15000
        self.f.event('subtask.define',dict(subtask_id='too_big',baseline=baseline),fail='ORCH_STATE_LIMIT')
        self.assertEqual(self.f.tree_hash(),before)
        self.assertEqual(task_state.MAX_JSON_BYTES,1000000)

    def test_compact_intent_cap_rejects_and_removes_only_own_unpublished_temp(self):
        self.f.define();self.f.assign('worker1','worker');self.pad()
        raw=self.f.root/'output/input.txt';raw.parent.mkdir(exist_ok=True);raw.write_text('x'*249000)
        preserved=self.f.folder/'responses/.unrelated.txn';preserved.write_text('Unrelated retained fixture temp.\n')
        before=self.f.tree_hash()
        self.f.event('artifact.register',dict(artifact_id='oversized',assignment_id='worker1',source_path='output/input.txt'),fail='ORCH_INTENT_LIMIT')
        self.assertEqual(self.f.tree_hash(),before)
        self.assertTrue(preserved.exists())
        self.assertEqual(list((self.f.root/'Tasks/.tmp').glob('*.json')),[])


if __name__ == '__main__': unittest.main()
