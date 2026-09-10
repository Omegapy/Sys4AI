"""Explicit configuration authority and recovery; no backend installation."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import tempfile
import unittest
from support import make_project,bind_director,write_json
from ontology_core import read_json,sha256,OntologyError
from ontology_profiles import configure_profile,preview_profile,health


class ProfileConfiguration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='ontology-profile-setup-');self.root=make_project(Path(self.tmp.name)/'project');bind_director(self.root)
        write_json(self.root/'ontology-advanced.yaml',{'schema_version':1,'profiles':{'standards':{'enabled':False},'guards':{'enabled':False}},'extensions':[],'limits':{}})
    def tearDown(self):self.tmp.cleanup()
    def authority(self,profile,enabled,expected):
        now=datetime.now(timezone.utc)
        return {'schema_version':1,'operation_id':'ONTPROFILE-test-0001','operation':'configure-profile','project_id':'example','profile':profile,'enabled':enabled,'expected_config_sha256':expected,'actor_id':'/root','actor_kind':'director','native_receipt':{'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':'/root','agent_status':'running'}]}},'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=2)).isoformat()}
    def test_selected_enable_and_replay(self):
        expected=sha256(self.root/'ontology-advanced.yaml');grant=self.authority('standards',True,expected)
        result=configure_profile(self.root,'standards',True,expected,grant)
        self.assertEqual(result['status'],'configured');self.assertFalse(result['provisioned']);self.assertFalse((self.root/'.venv-ontology-standards').exists())
        cfg=read_json(self.root/'ontology-advanced.yaml');self.assertFalse(cfg['profiles']['guards']['enabled']);self.assertTrue(cfg['profiles']['standards']['enabled'])
        self.assertTrue(configure_profile(self.root,'standards',True,expected,grant)['replayed'])
        self.assertEqual(health(self.root)['status'],'backend_unavailable')
    def test_wrong_or_expired_authority_preserves_config(self):
        expected=sha256(self.root/'ontology-advanced.yaml');grant=self.authority('standards',True,expected);grant['actor_id']='/ordinary-child'
        with self.assertRaises(OntologyError):configure_profile(self.root,'standards',True,expected,grant)
        self.assertEqual(sha256(self.root/'ontology-advanced.yaml'),expected)
    def test_incomplete_enabled_guard_fails_closed(self):
        cfg=read_json(self.root/'ontology-advanced.yaml');cfg['profiles']['guards']['enabled']=True;write_json(self.root/'ontology-advanced.yaml',cfg)
        expected=sha256(self.root/'ontology-advanced.yaml');grant=self.authority('standards',True,expected)
        with self.assertRaises(OntologyError) as error:configure_profile(self.root,'standards',True,expected,grant)
        self.assertEqual(error.exception.code,'guard_schema');self.assertEqual(sha256(self.root/'ontology-advanced.yaml'),expected)
    def test_partial_receipt_recovery(self):
        expected=sha256(self.root/'ontology-advanced.yaml');grant=self.authority('standards',True,expected)
        result=configure_profile(self.root,'standards',True,expected,grant)
        (self.root/result['receipt_path']).unlink()
        recovered=configure_profile(self.root,'standards',True,expected,grant)
        self.assertEqual(recovered['status'],'configured');self.assertTrue((self.root/recovered['receipt_path']).exists())


if __name__=='__main__':unittest.main()
