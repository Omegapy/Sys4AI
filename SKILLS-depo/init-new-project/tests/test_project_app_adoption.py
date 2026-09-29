"""One disposable delivery journey covers changed app setup and preservation."""
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from test_initializer import fixture_depot, load_helper


class ProjectAppAdoption(unittest.TestCase):
    def test_create_prepare_and_selected_recovery_preserve_content(self):
        with tempfile.TemporaryDirectory(prefix='sys4ai-app-delivery-') as temp:
            depot = fixture_depot(Path(temp))
            h = load_helper(depot / 'SKILLS-depo/init-new-project')
            destination = depot / 'Projects/Example'
            args = dict(mode='create',destination=destination,project_id='example',project_name='Example',purpose='Read a distinct synthetic project')
            template_entry=depot/h.TEMPLATE/'Launch Project.command'
            template_entry.chmod(0o644)
            with self.assertRaises(h.InitializationError):h.run_initialization(**args)
            template_entry.chmod(0o755)
            created = h.run_initialization(**args)
            self.assertEqual(created['setup_contract'],'governance-starter-v14')
            self.assertEqual(json.loads((destination/'project-app.json').read_text())['project_id'],'example')
            self.assertEqual(stat.S_IMODE((destination/'Launch Project.command').stat().st_mode),0o755)
            self.assertFalse((destination/'.sys4ai/project-app').exists())
            # A reconstructed earlier completed receipt demonstrates additive
            # adoption; it is labeled fixture evidence, never historical execution.
            record_path=destination/h.RECORD
            prior=json.loads(record_path.read_text());prior['setup_contract']=h.INTEGRATED_CONTRACT
            for name in h.PROJECT_APP.STARTERS:
                prior['owned_files'].pop(name,None)
                prior['sources']=[row for row in prior['sources'] if row['destination']!=name]
                (destination/name).unlink()
            # Drop the fixture's later collaboration operation before reconstructing
            # its base; installed collaboration remains unchanged source data.
            prior.pop('module_adoptions',None);prior.pop('history',None)
            record_path.write_bytes(h.encoded(prior))
            base=record_path.read_bytes()
            custom=b'Original project guidance stays intact.\n';(destination/'custom-notes.txt').write_bytes(custom)
            selected={**args,'mode':'prepare-existing','adopt_module':'project-app'}
            package_file=destination/h.PROJECT_APP.ROOT/'scripts/project_app_core.py'
            package_before=package_file.read_bytes()
            package_file.write_bytes(package_before+b'\n# Fixture-owned customization\n')
            with self.assertRaises(h.InitializationError):h.run_initialization(**selected)
            self.assertEqual(package_file.read_bytes(),package_before+b'\n# Fixture-owned customization\n')
            package_file.write_bytes(package_before)
            original_write=h.atomic_write
            failed=False
            def fail_once(target,data,expected,**kwargs):
                nonlocal failed
                if target.name=='Launch Project.command' and not failed:
                    failed=True
                    raise OSError('injected launcher publication interruption')
                return original_write(target,data,expected,**kwargs)
            with patch.object(h,'atomic_write',side_effect=fail_once):
                with self.assertRaises(h.InitializationError):h.run_initialization(**selected)
            pending=json.loads(record_path.read_text())
            self.assertEqual(pending['module_adoptions'][-1]['status'],'partial')
            template_launcher=depot/h.TEMPLATE/'Launch Project.command'
            launcher_source=template_launcher.read_bytes()
            template_launcher.write_bytes(launcher_source+b'\n# Changed after the frozen request\n')
            with self.assertRaises(h.InitializationError):h.run_initialization(**selected)
            template_launcher.write_bytes(launcher_source)
            completed=h.run_initialization(**selected)
            self.assertEqual(completed['setup_contract'],h.INTEGRATED_CONTRACT)
            op=completed['module_adoptions'][-1]
            self.assertEqual(op['status'],'completed')
            self.assertEqual(stat.S_IMODE((destination/'Launch Project.command').stat().st_mode),0o755)
            self.assertEqual((destination/'custom-notes.txt').read_bytes(),custom)
            self.assertEqual((destination/op['base_receipt']['path']).read_bytes(),base)
            cfg=json.loads((destination/'project-app.json').read_text())
            cfg['documents']=[{'title':'Local overview','path':'README.md'}]
            (destination/'project-app.json').write_text(json.dumps(cfg)+'\n')
            personalized=(destination/'project-app.json').read_bytes()
            h.run_initialization(**selected)
            self.assertEqual((destination/'project-app.json').read_bytes(),personalized)
            # First preparation preserves existing user prose and launcher bytes.
            prepared=depot/'Projects/Prepared';prepared.mkdir()
            (prepared/'project-app.json').write_bytes(personalized.replace(b'example',b'prepared'))
            record=h.run_initialization(mode='prepare-existing',destination=prepared,project_id='prepared',project_name='Prepared',purpose='Preserved first preparation')
            self.assertIn('project-app.json',record['preserved_files'])
            self.assertEqual(stat.S_IMODE((prepared/'Launch Project.command').stat().st_mode),0o755)
            self.assertFalse((prepared/'.sys4ai/project-app').exists())
            with self.assertRaises(h.InitializationError):
                h.run_initialization(**{**selected,'destination':depot})

if __name__=='__main__':unittest.main()
