"""Static activation and exact depot owner compatibility; no native pilot claims."""
import copy
import json
from pathlib import Path
import shutil
import unittest
from test_collaboration_acceptance import fixture, message
from collaboration_task import OWNER_PROFILES, task_module
from collaboration_install import assess_project, owner_profiles
from collaboration_store import CollaborationError

DEPOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parents[1]

class Installation(unittest.TestCase):
    def test_depot_v1_read_owner_and_scoped_exchange(self):
        f=fixture();self.addCleanup(f.tearDown)
        for name in OWNER_PROFILES['depot-v1']['files']:
            shutil.copyfile(DEPOT/name, f.root/name)
        owner=task_module(f.root)
        self.assertEqual(owner._collaboration_profile,'depot-v1')
        self.assertFalse(hasattr(owner.orch,'versioned'))
        b=f.board('worker1');before=(f.folder/'task.json').read_bytes()
        post=b.post(message(b,op='depot_notice'))
        self.assertEqual(f.board().query()['items'][0]['message']['message_id'],post['message_id'])
        f.board().receipt('depot_read',post['message_id'],'acknowledged')
        self.assertEqual(f.board().query(unread=True)['returned'],0)
        self.assertEqual(before,(f.folder/'task.json').read_bytes())
        bad=copy.deepcopy(f.state);bad['orchestration']['version']=2
        (f.folder/'task.json').write_text(json.dumps(bad))
        with self.assertRaises(CollaborationError): f.board()

    def test_known_profile_complete_review_inventory_and_preservation(self):
        f=fixture();self.addCleanup(f.tearDown)
        package=f.root/'.agents/skills/collaborate'
        shutil.copytree(SOURCE, package, ignore=shutil.ignore_patterns('__pycache__'))
        for name,marker in [('.agents/skills/task/SKILL.md','<!-- sys4ai:collaboration-default-v1 -->'),('.agents/skills/agent-task/SKILL.md','<!-- sys4ai:collaboration-owner-gates-v1 -->')]:
            p=f.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(marker)
        import hashlib
        inventory={p.relative_to(f.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in package.rglob('*') if p.is_file()}
        self.assertTrue(assess_project(f.root,expected_inventory=inventory)['enabled'])
        self.assertFalse(assess_project(f.root)['enabled'])
        receipt=f.root/'control_records/collaboration-installation.json';receipt.parent.mkdir()
        receipt.write_text(json.dumps(dict(schema_version=1,project_root=str(f.root),status='completed',package_inventory=inventory)))
        self.assertTrue(assess_project(f.root)['enabled'])
        p=package/'scripts/collaboration_task.py';old=p.read_bytes();p.write_bytes(old+b'\n# local customization\n')
        current=p.read_bytes()
        result=assess_project(f.root)
        self.assertFalse(result['enabled']);self.assertIn('COLLAB_PACKAGE_VERSION',[d['code'] for d in result['diagnostics']]);self.assertEqual(p.read_bytes(),current)
        fake="OWNER_PROFILES = {'custom': {'files': {'.agents/skills/task/custom.py':'"+'0'*64+"'}, 'versions':[1]}}"
        with self.assertRaises(ValueError):owner_profiles(fake.encode())
