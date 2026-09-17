"""Large status streams and existing depot identity, without live queue writes."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from test_session_maintenance import SOURCE, WORK, GIT, NOW, setup
from curator_git import LocalGit
from curator_integration import content_hash
from curator_policy import PolicyError
from curator_session import collect, configuration


class RootScaleMetadataTests(unittest.TestCase):
    def test_large_status_stream_retains_pages_and_checks_late_changes(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);setup(root)
            folder=root/'ordinary-documents';folder.mkdir()
            for n in range(5205):(folder/f'note-{n:05d}.txt').write_text('Ordinary fixture text.\n')
            observer=LocalGit(root,GIT,content_hash(Path(GIT).read_bytes()),max_bytes=16384,max_seconds=5)
            index_before=content_hash((root/'.git/index').read_bytes())
            first=observer.changed_metadata();last=observer.changed_metadata(offset=5200)
            self.assertEqual(first['change_count'],5205);self.assertEqual(len(first['changes']),50)
            self.assertGreater(first['scanned_bytes'],observer.max_bytes);self.assertEqual(first['retained_byte_limit'],16384)
            self.assertEqual(len(last['changes']),5);self.assertIsNone(last['next_offset'])
            self.assertEqual(first['snapshot'],last['snapshot']);self.assertEqual(last['remaining_changes'],0)
            (folder/'note-05204.txt').write_text('Changed beyond the first page.\n')
            changed=observer.changed_metadata();self.assertNotEqual(first['snapshot'],changed['snapshot'])
            self.assertEqual(index_before,content_hash((root/'.git/index').read_bytes()))
            queued=collect(root,git_executable=GIT,now=NOW)
            self.assertEqual(queued['state'],'pending_owner');self.assertEqual(len(queued['changed_paths']),50)
            self.assertGreater(queued['remaining_changed_paths'],5000);self.assertFalse(queued['runtime_observed'])

    def test_depot_policy_identity_without_generic_project_file(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);session=setup(root);(root/'project.json').unlink()
            self.assertEqual(configuration(root),session)
            result=collect(root,git_executable=GIT,now=NOW)
            self.assertEqual(result['state'],'pending_owner');self.assertEqual(result['context']['project_id'],'session-fixture')
            (root/'project.json').write_text(json.dumps({'project_id':'different-project'}))
            with self.assertRaises(PolicyError):configuration(root)
            (root/'project.json').unlink()
            policy=json.loads((root/'curator.yaml').read_text());policy['project']['coordination_root']=str(root/'other')
            (root/'curator.yaml').write_text(json.dumps(policy))
            with self.assertRaises(PolicyError):configuration(root)


if __name__=='__main__':unittest.main()
