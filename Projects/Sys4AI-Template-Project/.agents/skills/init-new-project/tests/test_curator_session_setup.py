"""Current setup/session defaults and earlier receipt preservation."""
import json
from pathlib import Path
import unittest
from test_integrated_setup import grant_for
from test_curator_setup import compose, fixture_directory


class CuratorSessionSetupTests(unittest.TestCase):
    def test_current_install_enables_session_and_preserves_opt_out(self):
        with fixture_directory('session-setup') as temp:
            root,h,updater,_,_=compose(temp)
            template=root/h.TEMPLATE
            neutral=json.loads((template/'curator-session.yaml').read_text())
            self.assertIsNone(neutral['project_id']);self.assertFalse(neutral['enabled'])
            dest=root/'Projects/active'
            args=dict(mode='create',destination=dest,project_id='active',project_name='Active',purpose='Session maintenance fixture')
            result=h.run_initialization(**args)
            self.assertEqual(result['setup_contract'],'governance-starter-v12');self.assertEqual(result['status'],'completed')
            session=json.loads((dest/'curator-session.yaml').read_text());self.assertTrue(session['enabled']);self.assertEqual(session['project_id'],'active')
            self.assertFalse(session['unattended_background_ai']);self.assertEqual(h._curator('assess',dest)['state'],'installed_session_enabled')
            cfg=json.loads((dest/'curator.yaml').read_text());self.assertFalse(cfg['schedule']['enabled']);self.assertIsNone(cfg['runtime']);self.assertFalse(cfg['autonomous_write'])
            self.assertFalse((dest/'control_records/curator').exists())
            original_receipt=(dest/h.RECORD).read_bytes();result=h.run_initialization(**args)
            self.assertEqual(result['setup_contract'],'governance-starter-v12')
            session['enabled']=False;(dest/'curator-session.yaml').write_text(json.dumps(session,indent=2)+'\n');before=(dest/'curator-session.yaml').read_bytes()
            with self.assertRaises(h.InitializationError):h.run_initialization(**args)
            result=h.run_initialization(**args,integration_grant_file=grant_for)
            self.assertEqual((dest/'curator-session.yaml').read_bytes(),before)
            self.assertEqual(h._curator('assess',dest)['state'],'installed_inactive')
            self.assertEqual(json.loads(original_receipt)['operation_id'],result['operation_id'])

    def test_first_preparation_neutral_copy_is_enabled(self):
        import shutil
        with fixture_directory('session-prepare') as temp:
            root,h,_,_,_=compose(temp);dest=root/'Projects/prepared'
            shutil.copytree(root/h.TEMPLATE,dest,ignore=shutil.ignore_patterns('.template','__pycache__'))
            (dest/'authored.txt').write_text('Preserved project content\n')
            result=h.run_initialization(mode='prepare-existing',destination=dest,project_id='prepared',project_name='Prepared',purpose='First preparation session fixture')
            self.assertEqual(result['status'],'completed');self.assertTrue(json.loads((dest/'curator-session.yaml').read_text())['enabled'])
            self.assertEqual((dest/'authored.txt').read_text(),'Preserved project content\n')

    def test_v10_receipt_does_not_acquire_session_on_recovery_or_rerun(self):
        with fixture_directory('session-v10') as temp:
            root,h,_,_,_=compose(temp);template=root/h.TEMPLATE
            original_policy=(template/h.TEMPLATE_POLICY).read_bytes()
            contract='governance-starter-v10';policy=json.loads(original_policy)
            policy['starter_files']=sorted(h.required_starters(contract));(template/h.TEMPLATE_POLICY).write_bytes(h.encoded(policy))
            dest=root/'Projects/legacy';identity={'schema_version':1,'project_id':'legacy','project_name':'Legacy','purpose':'Preserved v10 fixture','relative_path':'Projects/legacy'}
            proposed,sources,original=h.source_snapshot(root,root/'SKILLS-depo/init-new-project',identity,contract=contract,destination=dest)
            self.assertNotIn('curator-session.yaml',proposed)
            for row in sources:row['adoption']='specialized' if row['destination'] in h.SPECIALIZED_FILES and proposed[row['destination']]!=original.get(row['destination']) else 'adopted'
            record=dict(schema_version=1,setup_contract=contract,status='partial',mode='create',operation_id='project-setup-'+'a'*32,
                        identity=identity,project_root=str(dest),sources=sources,owned_files={n:h.sha(raw) for n,raw in proposed.items()},preserved_files={},
                        recovery_before={n:None for n in proposed},completed_stages=[],active_stage='assets',checks=[],created_at='2026-09-09T00:00:00+00:00',git_setup='separate',
                        preserved_licenses={},preserved_memory={},preserved_learning={},preserved_ontology={})
            receipt=dest/h.RECORD;receipt.parent.mkdir(parents=True);h.validate_record(record,dest,identity);receipt.write_bytes(h.encoded(record))
            args=dict(mode='create',destination=dest,project_id='legacy',project_name='Legacy',purpose='Preserved v10 fixture')
            for _ in range(2):
                result=h.run_initialization(**args);self.assertEqual(result['status'],'completed');self.assertEqual(result['setup_contract'],contract)
                self.assertFalse((dest/'curator-session.yaml').exists());self.assertEqual(h._curator('assess',dest)['state'],'installed_inactive')
            (template/h.TEMPLATE_POLICY).write_bytes(original_policy)
            adopted=h.run_initialization(**{**args,'mode':'prepare-existing'},adopt_module='curator',refresh_module=['curator'],integration_grant_file=grant_for)
            self.assertEqual(adopted['setup_contract'],contract);self.assertEqual(adopted['module_adoptions'][-1]['status'],'completed')
            self.assertTrue(h._integration('assess',dest)['compatible'])
            from test_integrated_setup import IntegratedSetupTests
            self.h=h
            IntegratedSetupTests.retain(self,'earlier-curator-without-semantics',dest)


if __name__=='__main__':unittest.main()
