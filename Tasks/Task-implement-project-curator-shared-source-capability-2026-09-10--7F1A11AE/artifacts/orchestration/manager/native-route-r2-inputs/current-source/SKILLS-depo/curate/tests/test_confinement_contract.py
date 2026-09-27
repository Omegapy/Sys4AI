from pathlib import Path
import os
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from curator_confinement import file_snapshot, source_manifest, verify_manifest, proof_gate, CHANNELS
from curator_policy import PolicyError


class ConfinementTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'file').write_bytes(b'fixed')

    def test_frozen_source_change_and_replacement_are_rejected(self):
        manifest=source_manifest(self.root,['file'])
        self.assertEqual(verify_manifest(manifest),manifest)
        (self.root/'file').write_bytes(b'changed')
        with self.assertRaises(PolicyError):verify_manifest(manifest)

    def test_symlink_hardlink_directory_alias_and_case_are_rejected(self):
        (self.root/'link').symlink_to(self.root/'file')
        with self.assertRaises((PolicyError,OSError)):file_snapshot(self.root,'link')
        os.link(self.root/'file',self.root/'hard')
        with self.assertRaises(PolicyError):file_snapshot(self.root,'hard')
        with self.assertRaises((PolicyError,OSError)):file_snapshot(self.root,'FILE')
        with self.assertRaises(PolicyError):file_snapshot(self.root,'../outside')

    def test_os_evidence_is_not_inferred_from_manifest(self):
        manifest=source_manifest(self.root,['file'])
        (self.root/'candidate').mkdir();(self.root/'private').mkdir()
        profile={'schema_version':1,'name':'fixture','read_roots':[],
            'write_roots':[str(self.root/'candidate')],'denied_roots':[str(self.root/'private')],
            'executables':[],'channels':{k:'disabled' for k in CHANNELS},'network':[],'config_sha256':'0'*64}
        with self.assertRaises(PolicyError):proof_gate(profile,manifest,{},{
            'state':'not_run','profile_sha256':'0'*64,'manifest_sha256':'0'*64,
            'runtime':{},'channels':{k:'observed_disabled' for k in CHANNELS},'cases':{}})



    def test_fifo_cannot_block_snapshot_before_type_check(self):
        import subprocess
        os.mkfifo(self.root/'fifo')
        code="import sys;sys.path.insert(0,sys.argv[1]);from curator_confinement import file_snapshot;from curator_policy import PolicyError;\ntry:file_snapshot(sys.argv[2],'fifo')\nexcept PolicyError:sys.exit(3)"
        result=subprocess.run([sys.executable,'-B','-c',code,str(Path(__file__).resolve().parents[1]/'scripts'),str(self.root)],
                              capture_output=True,text=True,timeout=3)
        self.assertEqual(result.returncode,3,result.stderr)

if __name__=='__main__':unittest.main()
