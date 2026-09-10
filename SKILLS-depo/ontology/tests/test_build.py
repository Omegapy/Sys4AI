from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from support import *
from ontology_core import load_project, OntologyError
from ontology_build import compile_project, write_generated
import ontology_build


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=make_project(Path(self.temp.name)/"project")

    def test_rebuild_byte_equivalence_and_recovery_after_deleted_projection(self):
        first=compile_project(self.root)
        before={p:(self.root/p).read_bytes() for p in first["outputs"]}
        second=compile_project(self.root)
        self.assertEqual(first,second)
        for p in before:(self.root/p).unlink()
        compile_project(self.root)
        self.assertEqual(before,{p:(self.root/p).read_bytes() for p in before})

    def test_conflicting_and_unknown_generated_files_are_preserved(self):
        result=compile_project(self.root)
        target=self.root/next(iter(result["outputs"]))
        target.write_text("User edited content")
        with self.assertRaises(OntologyError):compile_project(self.root)
        self.assertEqual(target.read_text(),"User edited content")
        with self.assertRaises(OntologyError):write_generated(load_project(self.root),{"SPECS.md":b"bad"},operation="bad")

    def test_stale_source_blocks_build_before_output(self):
        add_records(self.root,[record("bound-artifact")]);(self.root/"SPECS.md").write_text("Changed")
        with self.assertRaises(OntologyError):compile_project(self.root)
        self.assertFalse((self.root/".sys4ai").exists())

    def test_write_failure_rolls_back_prior_outputs_without_success_manifest(self):
        p=load_project(self.root)
        original=ontology_build.atomic_write
        calls=[]
        def fail(root,path,data,expected):
            calls.append(path)
            if path.endswith("two.json"):raise OSError("Injected output write failure")
            return original(root,path,data,expected)
        with patch.object(ontology_build,"atomic_write",side_effect=fail):
            with self.assertRaises(OSError):write_generated(p,{".sys4ai/ontology/one.json":b"one",".sys4ai/ontology/two.json":b"two"},operation="failure")
        self.assertFalse((self.root/".sys4ai/ontology/one.json").exists())
        self.assertFalse((self.root/".sys4ai/ontology/manifests/failure.json").exists())


if __name__ == "__main__": unittest.main()
