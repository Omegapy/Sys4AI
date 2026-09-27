"""Queue-to-awareness/conversation data flow without connected Task activation."""
from pathlib import Path
import tempfile
import unittest
from test_retained_application import WORK,NOW,HASH,context,reference
from curator_events import make_event
from curator_queue import DeliveryQueue
from curator_awareness import inspect
from curator_notices import notice
from curator_handoff import select,retain_original,continue_original
from curator_policy import digest


class RetainedSchedulingTests(unittest.TestCase):
    def test_pending_correction_flows_to_exact_local_offer(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);ctx=context(root)
            event=make_event(ctx,'manual_correction','correction-1',{'request':reference('project')},created_at=NOW)
            queue=DeliveryQueue(root,ctx['project_id'],ctx['repository_id']);queue.enqueue(event)
            policy={'project':{'id':ctx['project_id'],'repository_id':ctx['repository_id'],'coordination_root':str(root)}}
            before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            aware=inspect(root,policy,affected_paths=['fixture-observation.json'])
            self.assertEqual(aware['notices'][0]['level'],'warning');self.assertFalse(aware['new_work'])
            row=aware['notices'][0]
            item={'id':row['id'],'paths':row['scope'],'state':row['level'],'impact':row['impact'],'action':row['action'],'meaningful':True,'routine_success':False}
            shown=notice(item,affected_paths=['fixture-observation.json']);self.assertEqual(shown['delivery'],'local');self.assertIsNone(shown['external_destination'])
            original=dict(objective='Continue authored report',constraints=['Preserve selected scope'],task_id='fixture-task',execution_id='fixture-execution',source_refs=[reference('project')],assumptions=[],authority_sha256=HASH)
            offer=dict(item_id=row['id'],operation_id='maintenance-1',source_sha256=digest(event),authority_sha256=HASH,expires_at='2026-09-12T13:00:00+00:00',original_work=original)
            selection=select('do it',[offer],now=NOW,current_sources={row['id']:digest(event)},current_authority=HASH)
            handoff=retain_original(original,selection)
            self.assertEqual(handoff['original'],original);self.assertFalse(selection['task_activation'])
            held=continue_original(handoff,maintenance_outcome='blocked',current_original=original,integrity_current=True,scope_current=True,authority_current=True)
            self.assertEqual(held['state'],'held');self.assertFalse(held['competing_execution'])
            self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertFalse((root/'Tasks').exists())


if __name__=='__main__':unittest.main()
