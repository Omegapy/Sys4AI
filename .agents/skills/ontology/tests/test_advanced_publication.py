import copy
from pathlib import Path
import tempfile
import unittest

from support import bind_director, record, add_records, write_json, grant, project_id, CORE
from advanced_support import make_advanced, extension, statement
from ontology_core import OntologyError, canonical_bytes, sha256, read_json
from ontology_advanced import RDF, RDFS
from ontology_publication import preview, publish, recover
from ontology_proposals import save, stage_rdf_import, read_rdf_import
from ontology_proposal_validation import validate_candidate


class AdvancedPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=make_advanced(Path(self.temp.name)/"project")
        bind_director(self.root)
        add_records(self.root,[record("LocalClass",kind="concept",type_name="OntologyConcept"),record("OtherClass",kind="concept",type_name="OntologyConcept")])
        extension(self.root)
        config=read_json(self.root/"ontology-advanced.yaml")
        config["publication"]={"enabled":True,"binding":{"actor_id":"/root","scope":["ontology-advanced.yaml","ONTOLOGY/extensions"],
            "authority":[{"path":name,"sha256":sha256(self.root/name)} for name in ("SOUL.md","AGENTS.md","ROLE.md")]}}
        write_json(self.root/"ontology-advanced.yaml",config)

    def tearDown(self):
        self.temp.cleanup()

    def candidate(self):
        path="ONTOLOGY/extensions/semantics.json"
        value=read_json(self.root/path);value["version"]="1.0.1"
        value["axioms"].append(statement(self.root,"local-subclass",project_id("LocalClass"),RDFS+"subClassOf",project_id("OtherClass")))
        raw=canonical_bytes(value)
        config=read_json(self.root/"ontology-advanced.yaml");config["extensions"][0]["sha256"]=sha256(raw)
        return {"schema_version":2,"operation_id":"ONTOP-advanced-local-0001","operation":"publish","reason":"Add an explicitly sourced local subtype axiom.",
                "changes":[{"path":relative,"expected_sha256":sha256(self.root/relative),"content":data.decode(),"sha256":sha256(data)}
                           for relative,data in ((path,raw),("ontology-advanced.yaml",canonical_bytes(config)))]}

    def authority(self,candidate):
        value=grant(self.root,candidate)
        value.update(schema_version=2,advanced_config_sha256=sha256(self.root/"ontology-advanced.yaml"),proposal_review=None)
        return value

    def test_actual_standards_and_consistency_validate_isolated_candidate(self):
        candidate=self.candidate();before=sha256(self.root/"ONTOLOGY/extensions/semantics.json")
        value=save(self.root,candidate,rationale=candidate["reason"],evidence=record("x")["sources"])
        checked=validate_candidate(self.root,value["head"]["proposal_id"],expected_revision=1)
        self.assertEqual(checked["validation"]["standards"]["status"],"conformant",checked["validation"]["standards"])
        self.assertEqual(checked["validation"]["inference"]["status"],"ok",checked["validation"]["inference"])
        self.assertTrue(checked["validation"]["eligible"],checked["validation"]["findings"])
        self.assertEqual(before,sha256(self.root/"ONTOLOGY/extensions/semantics.json"))

    def test_v1_grant_cannot_publish_extension_and_exact_v2_partial_recovery(self):
        candidate=self.candidate();pre=preview(self.root,candidate)
        old_grant=grant(self.root,candidate)
        with self.assertRaisesRegex(OntologyError,"v2 grant"):
            publish(self.root,candidate,old_grant,expected_preview_sha256=pre["preview_sha256"])
        authority=self.authority(candidate)
        partial=publish(self.root,candidate,authority,expected_preview_sha256=pre["preview_sha256"],fail_at="after_commit:1")
        self.assertEqual(partial["status"],"partial")
        completed=recover(self.root,candidate["operation_id"],authority)
        self.assertEqual(completed["status"],"complete")
        self.assertEqual(read_json(self.root/"ONTOLOGY/extensions/semantics.json")["version"],"1.0.1")

    def test_profile_or_authority_changes_are_outside_semantic_publication(self):
        candidate=self.candidate();change=candidate["changes"][1]
        config=read_json(self.root/"ontology-advanced.yaml");config["profiles"]["standards"]["enabled"]=False
        change["content"]=canonical_bytes(config).decode();change["sha256"]=sha256(change["content"].encode())
        with self.assertRaisesRegex(OntologyError,"extension locks only"):
            preview(self.root,candidate)
        candidate=self.candidate();authority=self.authority(candidate);pre=preview(self.root,candidate)
        (self.root/"ROLE.md").write_text("Changed current Director authority.\n")
        with self.assertRaises(OntologyError):
            publish(self.root,candidate,authority,expected_preview_sha256=pre["preview_sha256"])

    def test_rdf_import_retains_full_quads_and_only_converts_lossless_axioms(self):
        from ontology_standards import stage_import
        graph="urn:sys4ai:ontology:graph:example:asserted"
        source="docs/import.jsonld"
        content=[{"@id":graph,"@graph":[{"@id":project_id("ImportedClass"),RDFS+"subClassOf":[{"@id":project_id("OtherClass")}]}]}]
        write_json(self.root/source,content)
        config=read_json(self.root/"ontology.yaml");config["source_allowlist"].append(source);write_json(self.root/"ontology.yaml",config)
        raw=(self.root/source).read_text();ref={"path":source,"sha256":sha256(raw.encode()),"locator":"line:1"}
        staged=stage_import(self.root,raw,"json-ld")
        self.assertEqual(staged["status"],"staged",staged)
        result=stage_rdf_import(self.root,staged,ref,"Review a selected local subtype import.","ONTOLOGY/extensions/semantics.json")
        self.assertEqual(result["status"],"candidate_created",result["import"]["diagnostics"])
        self.assertEqual(read_rdf_import(self.root,result["import"]["import_id"])["staged"]["quads"],staged["quads"])
        content[0]["@graph"][0][RDFS+"label"]=[{"@value":"uncoerced text","@language":"en"}]
        write_json(self.root/source,content);raw=(self.root/source).read_text();ref["sha256"]=sha256(raw.encode())
        staged=stage_import(self.root,raw,"json-ld")
        result=stage_rdf_import(self.root,staged,ref,"Retain unsupported core literals as RDF draft data.","ONTOLOGY/extensions/semantics.json")
        self.assertEqual(result["status"],"staged_only")
        self.assertIsNone(result["proposal"])
        self.assertFalse(result["approved"])


if __name__=="__main__":
    unittest.main()
