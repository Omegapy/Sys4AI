"""Real disposable owner transactions; synthetic roles are not native proof."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import test_orchestration_state as fixtures

task_state = fixtures.task_state


class TaskEncodingTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.OrchestrationTests()
        self.f.setUp()
        self.addCleanup(self.f.temp.cleanup)

    def pad(self, target=999000, compact=False):
        original = copy.deepcopy(self.f.state)
        stamp = original['created_at']
        def trial(count):
            state = copy.deepcopy(original)
            state['thread_refs'] = [dict(thread_id=f'fixture-{i:05}',
                title='Synthetic Unicode α ' + 'x'*180,
                first_seen_at=stamp, last_seen_at=stamp) for i in range(count)]
            return task_state.canonical_state(state)
        def encode(state):
            if compact:
                return json.dumps(state, ensure_ascii=False, separators=(',', ':'))+'\n'
            return task_state.json_text(state)
        lo, hi = 0, 6000
        while lo < hi:
            mid = (lo+hi+1)//2
            if len(encode(trial(mid)).encode('utf-8')) <= target: lo = mid
            else: hi = mid-1
        state = trial(lo)
        remaining = target-len(encode(state).encode('utf-8'))
        for ref in reversed(state['thread_refs']):
            count = min(remaining, 500-len(ref['title']))
            ref['title'] += 'z'*count
            remaining -= count
            if not remaining: break
        self.assertEqual(remaining, 0)
        raw = task_state.task_json_text(state)
        self.assertEqual(len(raw.encode('utf-8')), target)
        (self.f.folder/'task.json').write_text(raw)
        (self.f.folder/'TASK.md').write_text(task_state.render_task_markdown(state))
        task_state.write_index(self.f.root/'Tasks', [state])
        self.f.state = state
        cp, result = self.f.run_cli('validate', state['task_id'])
        self.assertEqual(cp.returncode, 0, result)
        return copy.deepcopy(state)

    def repair(self, result, revision):
        operation = result['errors'][0]['operation_id']
        return self.f.run_cli('reconcile', self.f.state['task_id'],
            '--expected-revision', str(revision), payload=dict(
                repair_type='transaction', operation_id=operation,
                actor=self.f.actor, execution_id=self.f.exec_id, generation=1))

    def assert_compact(self, before, after):
        raw = (self.f.folder/'task.json').read_bytes()
        self.assertGreater(len(task_state.json_text(after).encode('utf-8')), 1000000)
        self.assertLessEqual(len(raw), 1000000)
        self.assertEqual(raw, task_state.task_json_text(task_state.canonical_state(after)).encode('utf-8'))
        self.assertEqual(after['thread_refs'], before['thread_refs'])
        self.assertEqual(json.loads(raw), after)
        self.assertIn('α'.encode('utf-8'), raw)
        self.assertNotIn(b'\\u03b1', raw)

    def test_small_state_and_exact_utf8_threshold(self):
        state = self.f.state
        self.assertEqual(task_state.task_json_text(state), task_state.json_text(state))
        value = {'text': 'é'*499991}
        pretty = task_state.json_text(value)
        while len(pretty.encode('utf-8')) < 1000000:
            value['text'] += 'x'; pretty = task_state.json_text(value)
        self.assertEqual(len(pretty.encode('utf-8')), 1000000)
        self.assertEqual(task_state.task_json_text(value), pretty)
        value['text'] += 'x'
        self.assertNotEqual(task_state.task_json_text(value), task_state.json_text(value))
        self.assertEqual(json.loads(task_state.task_json_text(value)), value)
        value['text'] += 'x'*100
        with self.assertRaises(task_state.TaskError) as caught:
            task_state.task_json_text(value)
        self.assertEqual(caught.exception.code, 'ORCH_STATE_LIMIT')

    def test_actual_pretty_to_compact_transaction_and_next_transaction(self):
        before = self.pad()
        before_raw = (self.f.folder/'task.json').read_bytes()
        self.f.event('subtask.define', dict(subtask_id='crossing', baseline=self.f.base()))
        after = copy.deepcopy(self.f.state)
        self.assert_compact(before, after)
        self.assertEqual(after['orchestration']['events'][:-1], before['orchestration']['events'])
        self.assertEqual(after['revision'], before['revision']+1)
        self.f.event('subtask.define', dict(subtask_id='next', baseline=self.f.base()))
        self.assert_compact(after, self.f.state)
        self.assertEqual(self.f.state['orchestration']['events'][:-1], after['orchestration']['events'])
        self.assertEqual(self.f.run_cli('validate', self.f.state['task_id'])[0].returncode, 0)
        print(json.dumps(dict(case='boundary', before=len(before_raw),
            pretty_after=len(task_state.json_text(after).encode('utf-8')),
            compact_after=len(task_state.task_json_text(after).encode('utf-8')))))

    def test_boundary_fault_recovery_preserves_exact_post_digest_and_retry(self):
        for fault in ['after_artifact_publish', 'after_response_publish', 'after_state_publish']:
            with self.subTest(fault=fault):
                if fault != 'after_artifact_publish': self.setUp()
                before = self.pad()
                raw_before = (self.f.folder/'task.json').read_bytes()
                result, _ = self.f.event('subtask.define', dict(subtask_id='recover', baseline=self.f.base()),
                    fault=fault, fail='TRANSACTION_INCOMPLETE')
                p = self.f.root/'Tasks/.tmp'/f"{result['errors'][0]['operation_id']}.json"
                intent = json.loads(p.read_bytes())
                expected = task_state.task_json_text(task_state.canonical_state(intent['planned_state'])).encode('utf-8')
                self.assertEqual(intent['pre_state_sha256'], hashlib.sha256(raw_before).hexdigest())
                self.assertEqual(intent['post_state_sha256'], hashlib.sha256(expected).hexdigest())
                self.assertNotEqual(intent['post_state_sha256'], hashlib.sha256(task_state.json_text(intent['planned_state']).encode()).hexdigest())
                cp, repaired = self.repair(result, before['revision'])
                self.assertEqual(cp.returncode, 0, repaired)
                self.assertEqual((self.f.folder/'task.json').read_bytes(), expected)
                self.assert_compact(before, json.loads(expected))
                self.assertTrue((self.f.folder/intent['artifacts'][0]['path']).is_file())
                cp, repeated = self.repair(result, before['revision'])
                self.assertEqual(cp.returncode, 0, repeated)
                self.assertEqual(repeated['status'], 'already_reconciled')
                self.assertEqual((self.f.folder/'task.json').read_bytes(), expected)

    def test_compact_post_state_tamper_is_rejected(self):
        before = self.pad()
        result, _ = self.f.event('subtask.define', dict(subtask_id='tamper', baseline=self.f.base()),
            fault='after_state_publish', fail='TRANSACTION_INCOMPLETE')
        altered = self.f.read_state(self.f.folder)
        altered['current_summary'] = 'Later distinct fixture edit.'
        raw = task_state.task_json_text(task_state.canonical_state(altered))
        (self.f.folder/'task.json').write_text(raw)
        cp, recovered = self.repair(result, before['revision'])
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(recovered['errors'][0]['code'], 'ORCH_RECOVERY_STATE_HASH')
        self.assertEqual((self.f.folder/'task.json').read_text(), raw)

    def test_true_compact_over_limit_is_rejected_without_staging(self):
        self.pad(999500, compact=True)
        before = self.f.tree_hash()
        baseline = self.f.base(); baseline['objective'] = 'x'*15000
        self.f.event('subtask.define', dict(subtask_id='too_big', baseline=baseline), fail='ORCH_STATE_LIMIT')
        self.assertEqual(self.f.tree_hash(), before)
        self.assertEqual(task_state.MAX_JSON_BYTES, 1000000)

    def test_actual_compact_to_pretty_update_and_recovery(self):
        before = self.pad(995000)
        payload = self.f.response_payload(before)
        payload.update(current_summary='x'*10000, actor=self.f.actor,
            execution_id=self.f.exec_id, generation=1)
        cp, result = self.f.run_cli('record-response', before['task_id'],
            '--expected-revision', str(before['revision']), payload=payload)
        self.assertEqual(cp.returncode, 0, result)
        large = self.f.read_state(self.f.folder)
        self.assert_compact(before, large)
        self.f.state = large
        compact_raw = (self.f.folder/'task.json').read_bytes()
        payload = self.f.response_payload(large)
        payload.update(current_summary=before['current_summary'], actor=self.f.actor,
            execution_id=self.f.exec_id, generation=1)
        cp, result = self.f.run_cli('record-response', large['task_id'],
            '--expected-revision', str(large['revision']), payload=payload,
            fault='after_state_publish')
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(result['errors'][0]['code'], 'TRANSACTION_INCOMPLETE', result)
        p = self.f.root/'Tasks/.tmp'/f"{result['errors'][0]['operation_id']}.json"
        intent = json.loads(p.read_bytes())
        planned = task_state.canonical_state(intent['planned_state'])
        pretty = task_state.json_text(planned).encode('utf-8')
        self.assertLessEqual(len(pretty), 1000000)
        self.assertEqual(intent['pre_state_sha256'], hashlib.sha256(compact_raw).hexdigest())
        self.assertEqual(intent['post_state_sha256'], hashlib.sha256(pretty).hexdigest())
        self.assertEqual((self.f.folder/'task.json').read_bytes(), pretty)
        cp, recovered = self.repair(result, large['revision'])
        self.assertEqual(cp.returncode, 0, recovered)
        self.assertEqual((self.f.folder/'task.json').read_bytes(), pretty)
        self.assertEqual(planned['orchestration'], before['orchestration'])
        self.assertEqual(planned['thread_refs'], before['thread_refs'])
        cp, repeated = self.repair(result, large['revision'])
        self.assertEqual(cp.returncode, 0, repeated)
        self.assertEqual(repeated['status'], 'already_reconciled')
        self.assertEqual(self.f.run_cli('validate', large['task_id'])[0].returncode, 0)

    def test_unselected_small_compact_encoding_is_rejected_read_only(self):
        p = self.f.folder/'task.json'
        p.write_text(json.dumps(self.f.state, ensure_ascii=False, separators=(',', ':'))+'\n')
        before = self.f.tree_hash()
        cp, result = self.f.run_cli('validate', self.f.state['task_id'])
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn('CANONICAL_JSON_FORMAT', json.dumps(result))
        self.assertEqual(self.f.tree_hash(), before)

    def test_large_initial_creation_uses_selected_encoding(self):
        state = self.pad()
        refs = copy.deepcopy(state['thread_refs'])
        refs += [dict(refs[-1], thread_id=f'new-{i}') for i in range(80)]
        cp, created = self.f.run_cli('new', payload=dict(name='Large initial fixture',
            description='Synthetic bounded metadata only.', definition_of_done=['Fixture inspected.'], thread_refs=refs))
        self.assertEqual(cp.returncode, 0, created)
        path = Path(created['task_folder'])/'task.json'; after = json.loads(path.read_bytes())
        self.assertEqual(after['thread_refs'], refs)
        self.assertGreater(len(task_state.json_text(after).encode('utf-8')), 1000000)
        self.assertEqual(path.read_text(), task_state.task_json_text(task_state.canonical_state(after)))
        self.assertEqual(self.f.run_cli('validate', after['task_id'])[0].returncode, 0)

    def test_redaction_crosses_boundary_and_recovers_both_sides_of_state_write(self):
        for fault in ['after_redaction_correction_publish', 'after_redaction_state_publish']:
            with self.subTest(fault=fault):
                if fault != 'after_redaction_correction_publish': self.setUp()
                before = self.pad(999999)
                correction = self.f.response_payload(before)
                for key in ['current_summary', 'next_step', 'blockers', 'open_questions']:
                    correction[key] = before[key]
                payload = dict(repair_type='redact-response', response_id='RESP-0001',
                    redactions=['Completed one bounded and observed work unit.'],
                    reason='Remove this exact synthetic private phrase.', correction_response=correction,
                    user_authorized=True, actor=self.f.actor, execution_id=self.f.exec_id, generation=1)
                cp, result = self.f.run_cli('reconcile', before['task_id'], '--expected-revision', str(before['revision']),
                    payload=payload, fault=fault)
                self.assertNotEqual(cp.returncode, 0)
                self.assertEqual(result['errors'][0]['code'], 'REDACTION_TRANSACTION_INCOMPLETE', result)
                p = self.f.root/'Tasks/.tmp'/f"{result['errors'][0]['operation_id']}.json"
                intent = json.loads(p.read_bytes())
                expected = task_state.task_json_text(intent['planned_state']).encode('utf-8')
                self.assertEqual(intent['post_state_sha256'], hashlib.sha256(expected).hexdigest())
                cp, repaired = self.repair(result, before['revision']); self.assertEqual(cp.returncode, 0, repaired)
                after = self.f.read_state(self.f.folder); self.assert_compact(before, after)
                self.assertEqual(after['orchestration'], before['orchestration'])
                self.assertNotIn(payload['redactions'][0], (self.f.folder/intent['old_response_path']).read_text())
                cp, repeated = self.repair(result, before['revision']); self.assertEqual(cp.returncode, 0, repeated)
                self.assertEqual(repeated['status'], 'already_reconciled')
                self.assertEqual((self.f.folder/'task.json').read_bytes(), expected)


if __name__ == '__main__': unittest.main()
