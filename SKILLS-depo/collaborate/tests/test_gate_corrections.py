"""Three targeted V3 boundaries; deterministic fixtures, never native pilot proof."""
from pathlib import Path
import io
import json
from contextlib import redirect_stdout
import unittest

from test_collaboration_acceptance import fixture, message, tree, cli_main
from collaboration_store import CollaborationError, encoded, publish
from collaboration_read import TYPES
from collaboration_delivery import pending
from collaboration_decisions import assess
from collaboration_task import OWNER_PROFILE, task_module


class GateCorrections(unittest.TestCase):
    def test_closed_native_delivery_including_manager(self):
        f=fixture('extra-complex');self.addCleanup(f.tearDown)
        author=f.board('solver1')
        substantive=author.post({**message(author,op='secret_clock_rule',recipients=['manager1']),'title':'private-content initial conclusion'})
        operational=author.post(message(author,op='notice1',visibility='operational',recipients=['manager1']))
        initial=pending(author,'manager1')
        self.assertNotIn('private-content',encoded(initial).decode());self.assertNotIn('secret_clock_rule',encoded(initial).decode())
        self.assertEqual([x['message_id'] for x in initial['requests']],[operational['message_id']])
        self.assertEqual(initial['remaining'],0)  # No restricted-content count is exposed.
        for aid in ['solver1','solver2']:f.candidate(aid,'candidate'+aid[-1])
        for aid in ['reviewer1','reviewer2']:f.assign(aid,aid)
        self.assertNotIn(substantive['message_id'],{x['message_id'] for x in pending(f.board('solver1'),'manager1')['requests']})
        f.review('reviewer1','candidate1','review1')
        self.assertNotIn(substantive['message_id'],{x['message_id'] for x in pending(f.board('solver1'),'manager1')['requests']})
        f.review('reviewer2','candidate2','review2')
        released=pending(f.board('solver1'),'manager1')
        self.assertIn(substantive['message_id'],{x['message_id'] for x in released['requests']})
        self.assertFalse(released['wake'])

    def test_every_material_type_and_explicit_legacy_targetless_disposition(self):
        f=fixture('extra-complex');self.addCleanup(f.tearDown)
        for aid in ['solver1','solver2']:f.candidate(aid,'candidate'+aid[-1])
        for aid in ['reviewer1','reviewer2']:f.assign(aid,aid);f.review(aid,'candidate'+aid[-1],'review'+aid[-1])
        f.assign('senior1','senior');f.synthesis(['candidate1','candidate2'],['review1','review2'])
        author=f.board('solver1');ids=[]
        for i,kind in enumerate(TYPES):
            result=author.post(message(author,op='material'+str(i),kind=kind,target=f.ev,material=True,recipients=['solver2']))
            ids.append(result['message_id'])
        harmless=author.post(message(author,op='harmless1',material=False,body='A speculative optional question, outside current mandatory criteria.'))
        owner=f.board();initial=assess(owner,'subtask1',[])
        self.assertEqual({x['message_id'] for x in initial['pending']},set(ids));self.assertNotIn(harmless['message_id'],{x['message_id'] for x in initial['pending']})
        for i,mid in enumerate(ids):f.board('solver2').receipt('answered'+str(i),mid,'answered')
        self.assertEqual(len(assess(owner,'subtask1',[])['pending']),len(TYPES))
        decisions=[dict(message_id=mid,target=f.ev,disposition='rejected',owner='manager1',decision_kind='acceptance',decision_id='accept_synthesis1',evidence=[f.ev],reason='Current canonical decision and inspected assigned source dispose this exact current concern.') for mid in ids]
        self.assertTrue(assess(owner,'subtask1',decisions)['eligible'])
        # Newly authored material communication needs a concrete version target.
        with self.assertRaises(CollaborationError):author.post(message(author,op='newtargetless',kind='question',material=True))
        # Valid prior v1 note/question semantics are preserved without silent omission.
        legacy={**author.c.binding(),**message(author,op='legacy1',kind='note',material=True),'message_id':'solver1.legacy1'}
        publish(f.root,author.c.namespace+'/messages/legacy1.json',legacy)
        pending_legacy=assess(owner,'subtask1',decisions)
        self.assertFalse(pending_legacy['eligible']);self.assertEqual(pending_legacy['pending'][0]['target'],None)
        legacy_decision=dict(message_id='solver1.legacy1',target=None,disposition='rejected',owner='manager1',decision_kind='acceptance',decision_id='accept_synthesis1',evidence=[f.ev],reason='Legacy untargeted concern was inspected against the current criterion-complete canonical decision; no affected criterion established.')
        self.assertTrue(assess(owner,'subtask1',decisions+[legacy_decision])['eligible'])

    def test_actual_provider_unknown_absent_and_cached_change_fail_before_execution(self):
        f=fixture();self.addCleanup(f.tearDown);board=f.board('worker1')
        self.assertEqual(Path(board.c.owner.__file__),f.root/'.agents/skills/agent-task/scripts/task_state.py')
        self.assertIs(task_module(f.root),board.c.owner)
        path=f.root/'.agents/skills/agent-task/scripts/task_state.py';saved=path.read_bytes()
        marker=f.root/'executed-untrusted-code'
        path.write_text("from pathlib import Path\nPath("+repr(str(marker))+").write_text('unsafe')\n")
        before=tree(f.root)
        for call in [lambda:f.board(),board.query]:
            with self.assertRaises(CollaborationError) as exc:call()
            self.assertEqual(exc.exception.code,'COLLAB_OWNER_UNSUPPORTED')
        self.assertFalse(marker.exists());self.assertEqual(before,tree(f.root))
        path.unlink()
        with self.assertRaises(CollaborationError) as exc:f.board()
        self.assertEqual(exc.exception.code,'COLLAB_OWNER_UNSUPPORTED');self.assertFalse(marker.exists())
        path.write_bytes(saved);self.assertIs(task_module(f.root),board.c.owner)
        # A changed dependency is rejected before a cached owner can be reused.
        dep=f.root/'.agents/skills/agent-task/scripts/orchestration_state.py';original=dep.read_bytes();dep.write_bytes(original+b'\n# changed installed provider\n')
        with self.assertRaises(CollaborationError) as exc:board.query()
        self.assertEqual(exc.exception.code,'COLLAB_OWNER_UNSUPPORTED');dep.write_bytes(original)
        self.assertTrue(f.board().c.eligibility('subtask1')['category']=='generic')


    def test_recipient_observed_receipt_v2_is_distinct_from_reading_and_empty_api_results(self):
        f=fixture();self.addCleanup(f.tearDown)
        sender=f.board('worker1');result=sender.post(message(sender,op='notice_to_two'))
        mid=result['message_id'];recipient=f.board()
        # Empty/null actual API result is equally weak; no future notified receipt.
        for i,value in enumerate((None,{},[],'')):
            with self.assertRaises(CollaborationError):
                sender.receipt('empty'+str(i),mid,'notified','manager1','Actual API return contained no confirmation.',{'tool':'collaboration.send_message','native_id':recipient.c.actor,'result':value})
        # Historical v1 empty-return records remain exact attributed data.
        legacy={**sender.c.binding(),'operation_id':'legacy_empty','message_id':mid,'message_sha256':result['source']['sha256'],'recipient':'manager1','state':'notified','evidence':'Synthetic historical empty API return, not notification confirmation.','native_receipt':{'tool':'collaboration.send_message','native_id':recipient.c.actor,'result':{}}}
        legacy_ref=publish(f.root,sender.c.namespace+'/receipts/legacy_empty.json',legacy)
        old_bytes=(f.root/legacy_ref['path']).read_bytes()
        old=next(x for x in recipient.receipts(recipient.messages()) if x['receipt']['operation_id']=='legacy_empty')
        self.assertEqual(old['receipt']['state'],'notified');self.assertEqual(old['receipt']['native_receipt']['result'],{})
        self.assertFalse(old['notification_confirmation']['confirmed'])
        self.assertIn(mid,{x['message_id'] for x in pending(sender,'manager1')['requests']})
        # Only the addressed active recipient can assert its own mailbox observation.
        with self.assertRaises(CollaborationError):sender.receipt('forged_observation',mid,'notified','manager1','Pretended recipient observation.',receipt_version=2)
        with self.assertRaises(CollaborationError):recipient.receipt('blank_observation',mid,'notified',evidence='',receipt_version=2)
        with self.assertRaises(CollaborationError):recipient.receipt('fake_api',mid,'notified',evidence='Mailbox observed.',native_receipt={'tool':'collaboration.send_message','native_id':recipient.c.actor,'result':{'invented':True}},receipt_version=2)
        with self.assertRaises(CollaborationError):recipient.receipt('unknown_version',mid,'notified',evidence='Mailbox observed.',receipt_version=3)
        evidence='Synthetic deterministic recipient assertion: the exact immutable ID/hash was observed in its native mailbox notice; no real tool call is claimed.'
        observed=recipient.receipt('observed_notice',mid,'notified',evidence=evidence,receipt_version=2)
        self.assertEqual(observed,recipient.receipt('observed_notice',mid,'notified',evidence=evidence,receipt_version=2))
        with self.assertRaises(CollaborationError):recipient.receipt('observed_notice',mid,'notified',evidence=evidence+' Conflicting retry.',receipt_version=2)
        raw=json.loads((f.root/observed['path']).read_text())['payload']
        self.assertEqual(raw['version'],2);self.assertIsNone(raw['native_receipt']);self.assertEqual(raw['message_sha256'],result['source']['sha256'])
        self.assertNotIn(mid,{x['message_id'] for x in pending(sender,'manager1')['requests']})
        self.assertIn(mid,{x['message_id'] for x in pending(sender,'worker1')['requests']})
        unread=recipient.query(unread=True);self.assertIn(mid,{x['message']['message_id'] for x in unread['items']});self.assertFalse(unread['items'][0]['reported_reading'])
        current=next(x for x in recipient.receipts(recipient.messages()) if x['receipt']['version']==2)
        self.assertTrue(current['notification_confirmation']['confirmed']);self.assertFalse(current['notification_confirmation']['reported_reading'])
        recipient.receipt('reported_reading',mid,'acknowledged')
        self.assertNotIn(mid,{x['message']['message_id'] for x in recipient.query(unread=True)['items']})
        self.assertTrue(recipient.query()['items'][0]['reported_reading'])
        self.assertEqual(old_bytes,(f.root/legacy_ref['path']).read_bytes())


if __name__=='__main__':unittest.main()
