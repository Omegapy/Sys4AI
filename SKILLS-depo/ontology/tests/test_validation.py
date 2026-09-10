from pathlib import Path
import tempfile
import unittest
from support import *
from ontology_core import load_project, OntologyError
from ontology_validate import validate_project


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=make_project(Path(self.temp.name)/"project")

    def diagnostics(self,records):
        target=self.root/"ONTOLOGY/modules/project/project.jsonld"
        value=read_json(target);value["@graph"]=records;write_json(target,value)
        return validate_project(load_project(self.root,validate=False))["diagnostics"]

    def test_required_metadata_and_provenance(self):
        r=record("missing");r.pop("definition");r["sources"]=[]
        codes={d["code"] for d in self.diagnostics([r])}
        self.assertTrue({"missing_metadata","missing_provenance"} <= codes)

    def test_ambiguity_requires_all_candidates_and_distinctions(self):
        a,b=record("a",label="Same"),record("b",aliases=["Same"])
        self.assertTrue(any(d["code"]=="label_ambiguity" for d in self.diagnostics([a,b])))
        a.update(ambiguity_with=[b["@id"]],scope_note="First meaning")
        b.update(ambiguity_with=[a["@id"]],scope_note="Second meaning")
        self.assertEqual(self.diagnostics([a,b]),[])

    def test_dangling_and_typed_endpoints(self):
        edge=record("edge",kind="relation",type_name="Relationship",subject=core_id("Project"),predicate=core_id("providesCapability"),object=core_id("Task"))
        codes={d["code"] for d in self.diagnostics([edge])}
        self.assertTrue({"domain_violation","range_violation"}<=codes)
        edge["object"]=project_id("missing")
        self.assertIn("dangling_target",{d["code"] for d in self.diagnostics([edge])})

    def test_cardinality_and_qualifier_schema_are_executable(self):
        pred=record("predicate",kind="predicate",type_name="RelationshipType",domain=[core_id("Artifact")],range=[core_id("Artifact")],acyclic=False,cardinality={"min":0,"max":1},qualifiers={"weight":{"type":"number","required":True}})
        a,b,c=record("a"),record("b"),record("c")
        edges=[record("edge"+str(i),kind="relation",type_name="Relationship",subject=a["@id"],predicate=pred["@id"],object=target["@id"],qualifiers={"weight":"bad"}) for i,target in enumerate([b,c])]
        codes={d["code"] for d in self.diagnostics([pred,a,b,c,*edges])}
        self.assertTrue({"cardinality_violation","qualifier_type"} <= codes)
        edges[0]["qualifiers"]={"weight":0.5}
        self.assertEqual(self.diagnostics([pred,a,b,edges[0]]),[])

    def test_only_declared_acyclic_relations_reject_cycles(self):
        a=record("a",kind="concept",type_name="OntologyConcept");b=record("b",kind="concept",type_name="OntologyConcept")
        edges=[record("edge"+str(i),kind="relation",type_name="Relationship",subject=s["@id"],predicate=core_id("subtypeOf"),object=o["@id"]) for i,(s,o) in enumerate([(a,b),(b,a)])]
        self.assertIn("acyclic_violation",{d["code"] for d in self.diagnostics([a,b,*edges])})
        for edge in edges:edge["predicate"]=core_id("relatedTo")
        self.assertEqual(self.diagnostics([a,b,*edges]),[])

    def test_diagnostics_are_stable_with_reordered_record_input(self):
        a,b=record("a",label="Same"),record("b",label="Same")
        first=self.diagnostics([a,b]);second=self.diagnostics([b,a])
        self.assertEqual([(d['code'],d['record_id']) for d in first],[(d['code'],d['record_id']) for d in second])


if __name__ == "__main__": unittest.main()
