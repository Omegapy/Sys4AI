"""Root-only compatibility fixtures; never copied into generic policy."""
import datetime as dt
import unittest
from unittest import mock
import test_orchestration_state as fixtures


class RootOrchestrationIntakeTests(unittest.TestCase):
    def setUp(self):
        self.h = fixtures.OrchestrationTests(); self.h.setUp()
    def tearDown(self): self.h.tearDown()
    def raw(self):
        h=self.h
        return {k:h.state[k] for k in ('name','description','definition_of_done')} | {'orchestration_enabled':True}
    def future(self):return (dt.datetime.fromisoformat(self.h.state['updated_at'])+dt.timedelta(days=31)).isoformat()
    def test_old_live_match_is_blocked_before_successor_or_any_closure(self):
        h=self.h;before=h.tree_hash()
        with mock.patch.object(fixtures.task_state,'now_local',return_value=self.future()):
            with self.assertRaises(fixtures.task_state.TaskError) as caught:
                fixtures.task_state.command_intake(h.root,h.root/'Tasks',self.raw())
        self.assertEqual(caught.exception.code,'ORCH_AGE_OWNERS');self.assertEqual(before,h.tree_hash())
    def test_reconciled_age_closure_keeps_distinct_status_and_new_execution_unassigned(self):
        h=self.h
        h.event('manager.replace',{'reason':'Explicit controlled recovery before age closure','user_authorized':True,'observations':[{'assignment_id':'manager1','receipt':h.roster('/root/manager1','completed'),'changes':h.context}]},actor='/root');h.generation=2;h.actor='/root'
        raw=self.raw()|{'intake_actor':{'native_id':'/root','receipt':h.roster('/root','running')}}
        with mock.patch.object(fixtures.task_state,'now_local',return_value=self.future()):
            result=fixtures.task_state.command_intake(h.root,h.root/'Tasks',raw)
        old=h.read_state(h.folder);self.assertEqual(old['status'],'close-old-task');self.assertIsNone(old['next_step']);self.assertEqual(len(result['closed_tasks']),1)
        self.assertNotEqual(result['task_id'],old['task_id']);self.assertEqual(result['task']['parent_task_id'],old['task_id']);self.assertIsNone(result['task']['orchestration']['execution_id'])
        response=(h.folder/old['last_response']['path']).read_text();self.assertIn('Completion was not verified.',response)
    def test_matching_live_execution_and_read_only_routes_do_not_create_or_age(self):
        h=self.h;before=h.tree_hash();result=fixtures.task_state.command_intake(h.root,h.root/'Tasks',self.raw());self.assertEqual(result['status'],'matched');self.assertEqual(before,h.tree_hash())
        with mock.patch.object(fixtures.task_state,'now_local',return_value=self.future()):
            result=fixtures.task_state.command_status(h.root,h.root/'Tasks',3)
        self.assertEqual(result['integrity'],'valid');self.assertEqual(before,h.tree_hash())

    def test_unassigned_old_schema2_uses_native_intake_receipt_without_inventing_owner(self):
        h=self.h;root=h.root/'unassigned-project';root.mkdir();(root/'Tasks').mkdir()
        for name in ('SOUL.md','AGENTS.md','ROLE.md'):(root/name).write_text('# Disposable fixture\n')
        (root/'Tasks/INDEX.md').write_text(fixtures.task_state.render_index_markdown([], '2026-09-08T00:00:00+00:00'))
        cp,result=h.run_cli('new',root=root,payload={'name':'Unassigned old work','description':'Old enabled record before manager reservation.','definition_of_done':['Work performed.'],'orchestration_enabled':True});self.assertEqual(cp.returncode,0,result)
        folder=__import__('pathlib').Path(result['task_folder']);old=h.read_state(folder)
        future=(dt.datetime.fromisoformat(old['updated_at'])+dt.timedelta(days=31)).isoformat()
        raw={k:old[k] for k in ('name','description','definition_of_done')}|{'orchestration_enabled':True,'intake_actor':{'native_id':'/root','receipt':h.roster('/root','running')}}
        with mock.patch.object(fixtures.task_state,'now_local',return_value=future):
            result=fixtures.task_state.command_intake(root,root/'Tasks',raw)
        closed=h.read_state(folder);self.assertEqual(closed['status'],'close-old-task');self.assertEqual(closed['orchestration'],fixtures.task_state.orch.empty());self.assertEqual(len(result['closed_tasks']),1)
        self.assertIsNone(result['task']['orchestration']['writer']);self.assertIsNone(result['task']['orchestration']['execution_id'])
