import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import curator_policy as policy


class PolicyTests(unittest.TestCase):
    def setUp(self):
        here = Path(__file__).resolve()
        candidates = [p / 'CURATION-depo/starter/curator.yaml' for p in here.parents]
        self.policy = policy.load_policy(next(p for p in candidates if p.exists()))

    def test_neutral_and_specialization_do_not_authorize(self):
        self.assertEqual(policy.inspect_policy(self.policy)['state'], 'installed_inactive')
        self.policy['capabilities'] = ['maintain documentation']
        self.assertFalse(policy.evaluate_operation(self.policy, None, {}, {})['allowed'])
        self.assertEqual(self.policy['entitlements'], [])

    def test_strict_parser_and_counts(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1.2}', b'{"a":"\\u0001"}'):
            with self.assertRaises(policy.PolicyError): policy.decode(raw)
        for key, value in [('schema_version', True), ('unexpected', None), ('bounds', {'model_calls': True})]:
            selected = copy.deepcopy(self.policy); selected[key] = value
            with self.assertRaises(policy.PolicyError): policy.validate_policy(selected)

    def test_cli_is_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / 'curator.yaml'
            source.write_text(json.dumps(self.policy)); before = source.read_bytes()
            for cmd in ('status', 'validate'):
                result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve().parents[1] / 'scripts/curator.py'), cmd, '--policy', str(source)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(json.loads(result.stdout)['allowed'])
            self.assertEqual(list(root.iterdir()), [source]); self.assertEqual(source.read_bytes(), before)

    def test_permission_registry_is_independent(self):
        self.assertEqual(len(policy.PERMISSIONS), 22)
        self.assertTrue({'commit','push','merge','memory.publish','ontology.publish','adoption','runtime.install'} <= policy.PERMISSIONS)



    def selected(self, permission='analysis'):
        selected = copy.deepcopy(self.policy)
        selected.update(project={'id':'p','repository_id':'r','coordination_root':'/selected'},
            branches=['main'], controller={'kind':'curator','charter':{'path':'CURATOR.md','sha256':'1'*64}},
            runtime={'backend':'codex-app-server-v2','executable':'/runtime','sha256':'2'*64,
                'schema_sha256':'3'*64,'profile_sha256':'4'*64,'model':'selected','effort':'high'},
            accepted_policy={'id':'policy','edition':'1','sha256':'5'*64,'expires_at':'2099-01-01T00:00:00Z'},
            entitlements=[{'id':'entitlement','sha256':'6'*64}],
            bounds={'model_calls':1,'work_seconds':60,'candidate_bytes':1000,'concurrent_agents':1})
        entitlement={'id':'entitlement','sha256':'6'*64,'policy_sha256':'5'*64,
            'project_id':'p','repository_id':'r','coordination_root':'/selected','branches':['main'],
            'permissions':[permission],'paths':['docs'],'tools':[],'network':[],'expires_at':'2099-01-01T00:00:00Z'}
        operation={'class':permission,'project_id':'p','repository_id':'r','coordination_root':'/selected',
            'branch':'main','paths':['docs/file.md'],'tools':[],'network':[],'payload_sha256':'7'*64,
            'cost':dict(selected['bounds']),'automatic':False}
        observation={'root_available':True,'runtime_available':True,'proof_current':True,
            'supported_bounds':dict(selected['bounds']),'policy_sha256':policy.digest(selected),'now':'2026-09-11T00:00:00Z'}
        return selected,entitlement,operation,observation

    def test_each_selected_permission_requires_its_own_prior_entitlement(self):
        for permission in policy.PERMISSIONS:
            args = self.selected(permission)
            self.assertTrue(policy.evaluate_operation(*args)['allowed'], permission)
            args[1]['permissions']=[]
            self.assertEqual(policy.evaluate_operation(*args)['code'], 'permission_denied')

    def test_selected_malformed_stale_and_unsupported_values(self):
        for value in ({}, [], None, True, 'shell'):
            args=self.selected();args[2]['class']=value
            self.assertEqual(policy.evaluate_operation(*args)['code'],'permission_unknown')
        for target,key,value,code in [(2,'branch','other','branch_mismatch'),
            (3,'root_available',False,'runtime_unavailable'),(3,'proof_current',False,'runtime_proof_required'),
            (1,'expires_at','2000-01-01T00:00:00Z','entitlement_expired')]:
            args=self.selected();args[target][key]=value
            self.assertEqual(policy.evaluate_operation(*args)['code'],code)
        args=self.selected();args[2]['cost']['model_calls']=True
        self.assertEqual(policy.evaluate_operation(*args)['code'],'bounds_exhausted')

    def test_automatic_capture_and_explicit_corrections_are_separate(self):
        args=self.selected('memory.publish');args[0]['autonomous_write']=True
        args[3]['policy_sha256']=policy.digest(args[0]);args[2]['automatic']=True
        args[3]['automatic_capture']=False
        self.assertEqual(policy.evaluate_operation(*args)['code'],'capture_disabled')
        args[2]['automatic']=False
        self.assertTrue(policy.evaluate_operation(*args)['allowed'])

    def test_deep_json_is_a_bounded_error(self):
        with self.assertRaises(policy.PolicyError):
            policy.decode(b'['*10000+b'0'+b']'*10000)

if __name__ == '__main__': unittest.main()
