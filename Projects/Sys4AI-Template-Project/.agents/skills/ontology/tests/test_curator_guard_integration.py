"""Actual selected local standards backend verifies the new owner guard routes."""
import importlib,unittest,tempfile
from test_curator_integration import fixture,integration_grant
from support import *
from guard_support import install_adapters,fixture_selection,preserve_imports

@unittest.skipUnless(standards_available(),'Select an existing certified standards runtime')
class CuratorGuardIntegrationTests(unittest.TestCase):
    def test_guarded_preview_publish_and_recovery(self):
        preserve_imports(self)
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=fixture(Path(temporary.name)/'project');install_adapters(root)
        shutil.copytree(standards_environment(),root/'.venv-ontology-standards',symlinks=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in list(sys.modules):
            if name.startswith('ontology_'):del sys.modules[name]
        sys.path.insert(0,str(root/'.agents/skills/ontology/scripts'))
        fixture_selection(root)
        owner=importlib.import_module('ontology_publication')
        pre=owner.integration_preview(root,{'schema_version':1,'operation_id':'ONTOP-guarded-curator','reason':'Actual disposable guard integration.'})
        grant=integration_grant(root,pre)
        partial=owner.integration_publish(root,pre['proposal'],grant,expected_preview_sha256=pre['preview_sha256'],fail_at='after_commit:4')
        self.assertEqual(partial['status'],'partial');self.assertEqual(partial['ontology_guard']['semantic_status'],'conformant')
        completed=owner.integration_recover(root,pre['proposal']['operation_id'],grant)
        self.assertEqual(completed['status'],'complete');self.assertTrue(completed['ontology_guard']['lock_rechecked'])
        again=owner.integration_recover(root,pre['proposal']['operation_id'],grant)
        self.assertEqual(completed['intent_sha256'],again['intent_sha256'])
        before={name:(root/name).read_bytes() for name in ('ontology.yaml','ONTOLOGY/modules/project/curator.jsonld','ONTOLOGY/bindings/curator.jsonld','ONTOLOGY/modules/project/curator-competency.json')}
        contract=json.loads((root/'reference-assets/ONTOLOGY-depo/actions/contracts-v1.json').read_text())
        action=next(r for r in contract['actions'] if r['family']=='ontology' and r['operation']=='integration_preview')
        action['target_type']='memory-owned-artifact'
        fixture_selection(root,contract=contract)
        error_class=importlib.import_module('ontology_core').OntologyError
        with self.assertRaises(error_class) as rejected:
            owner.integration_preview(root,{'schema_version':1,'operation_id':'ONTOP-guard-negative','reason':'Reject mismatched selected request semantics.'})
        self.assertEqual(rejected.exception.code,'guard_violation')
        self.assertEqual(before,{name:(root/name).read_bytes() for name in before})
