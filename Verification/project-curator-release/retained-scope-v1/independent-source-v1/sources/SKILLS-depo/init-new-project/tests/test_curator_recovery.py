"""Curator adoption uses the original setup transaction and preserves later edits."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_curator_setup import fixture_directory,load
from test_curator_adoption import historical_project,current_sources


class CuratorRecoveryTests(unittest.TestCase):
    def test_partial_exact_retry_changed_sources_and_later_edits(self):
        with fixture_directory('recovery') as temp:
            root,destination,base=historical_project(temp);helper=current_sources(root)
            args=dict(mode='prepare-existing',destination=destination,project_id='legacy',project_name='Legacy',purpose='Prior edition software',adopt_module='project-curator')
            original_write=helper.atomic_write;selected=destination/'.agents/skills/curate/README.md'
            def interrupted(path,raw,*values,**options):
                result=original_write(path,raw,*values,**options)
                if path==selected:raise OSError('fixture interruption after exact reviewed package write')
                return result
            with patch.object(helper,'atomic_write',side_effect=interrupted),self.assertRaises(helper.InitializationError):helper.run_initialization(**args)
            record_path=destination/helper.RECORD;partial=json.loads(record_path.read_text());operation=partial['module_adoptions'][-1]
            self.assertEqual(operation['status'],'partial');operation_id=operation['operation_id'];accepted=selected.read_bytes()
            self.assertEqual(helper.sha(accepted),operation['files']['.agents/skills/curate/README.md']['after'])
            (destination/'notes.md').write_text('Later unrelated human work must survive.\n')
            selected.write_text('Later human change to a selected target.\n');later=selected.read_bytes();receipt_before=record_path.read_bytes()
            with self.assertRaises(helper.InitializationError):helper.run_initialization(**args)
            self.assertEqual(selected.read_bytes(),later);self.assertEqual(record_path.read_bytes(),receipt_before)
            selected.write_bytes(accepted)
            unknown=destination/'.agents/skills/curate/human.py';unknown.write_text('authored = True\n')
            with self.assertRaises(helper.InitializationError):helper.run_initialization(**args)
            self.assertEqual(unknown.read_text(),'authored = True\n');unknown.unlink()
            source=root/'SKILLS-depo/curate/README.md';source_before=source.read_bytes();source.write_bytes(source_before+b'\nDifferent pending source edition.\n')
            updater=load(root/'tools/template_update.py','curator_recovery_updater');updater.update(root,'apply')
            with self.assertRaises(helper.InitializationError):helper.run_initialization(**args)
            self.assertEqual(selected.read_bytes(),accepted)
            source.write_bytes(source_before);updater.update(root,'apply')
            finished=helper.run_initialization(**args);final=finished['module_adoptions'][-1]
            self.assertEqual(final['operation_id'],operation_id);self.assertEqual(final['status'],'completed');self.assertEqual(finished['setup_contract'],base['setup_contract'])
            self.assertEqual((destination/'notes.md').read_text(),'Later unrelated human work must survive.\n')
            self.assertFalse(json.loads((destination/'memory.yaml').read_text())['integration']['automatic_capture'])
            self.assertEqual((destination/'LICENSE.custom').read_text(),'Existing project license retained.\n')
            self.assertEqual(len(finished['module_adoptions']),1)


if __name__=='__main__':unittest.main()
