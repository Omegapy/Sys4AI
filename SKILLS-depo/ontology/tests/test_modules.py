from pathlib import Path
import tempfile
import unittest
from support import *
from ontology_core import load_project, OntologyError


class ModuleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = make_project(Path(self.temp.name)/"project")

    def test_changed_missing_and_extra_module_files_fail(self):
        module = self.root/"ONTOLOGY/modules/sys4ai-core/1.0.0"
        original = (module/"core.jsonld").read_bytes()
        (module/"core.jsonld").write_bytes(original+b" ")
        with self.assertRaises(OntologyError): load_project(self.root)
        (module/"core.jsonld").write_bytes(original)
        (module/"extra.json").write_text("{}")
        with self.assertRaises(OntologyError): load_project(self.root)
        (module/"extra.json").unlink(); (module/"core.jsonld").unlink()
        with self.assertRaises(OntologyError): load_project(self.root)

    def test_wrong_version_and_lock_fail(self):
        for field, value in (("version", "9.0.0"), ("sha256", "0"*64)):
            config = read_json(self.root/"ontology.yaml")
            original = dict(config["modules"][0]); config["modules"][0][field]=value
            write_json(self.root/"ontology.yaml", config)
            with self.assertRaises(OntologyError): load_project(self.root)
            config["modules"][0]=original; write_json(self.root/"ontology.yaml",config)

    def test_core_redefinition_duplicate_and_foreign_namespace_fail(self):
        target = self.root/"ONTOLOGY/modules/project/project.jsonld"
        value = read_json(target)
        for records in ([{**record("bad"), "@id":core_id("Task")}], [record("same"),record("same")], [record("foreign", identity="other")]):
            value["@graph"]=records; write_json(target,value)
            with self.assertRaises(OntologyError): load_project(self.root)

    def test_local_subtype_and_label_move_keep_identity(self):
        extension = record("local-type",kind="concept",type_name="OntologyConcept")
        edge = record("subtype",kind="relation",type_name="Relationship",subject=extension["@id"],predicate=core_id("subtypeOf"),object=core_id("Artifact"))
        add_records(self.root,[extension,edge])
        before = load_project(self.root)
        target = self.root/"ONTOLOGY/modules/project/project.jsonld"
        value=read_json(target); value["@graph"][0]["label"]="Renamed type";write_json(target,value)
        after=load_project(self.root)
        self.assertEqual(set(before.by_id),set(after.by_id))
        self.assertEqual(after.by_id[edge["@id"]]["subject"],extension["@id"])


if __name__ == "__main__": unittest.main()
