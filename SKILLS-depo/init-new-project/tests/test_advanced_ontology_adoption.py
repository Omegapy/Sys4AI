"""Selected populated-v8 capability updates retain all authored ontology evidence."""
import json
from pathlib import Path
import shutil
import unittest

import test_initializer as fixture
import test_ontology_adoption as ontology_fixture


class AdvancedAdoptionTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def historical(self, edition=8):
        if edition != 8:
            return ontology_fixture.OntologyAdoptionTests.historical(self, edition)
        h=self.helper;template=self.root/h.TEMPLATE
        backup=Path(self.temporary.name)/"current-template";shutil.copytree(template,backup)
        for name in ("ontology-advanced.yaml","tools/template_update.py"):
            (template/name).unlink()
        contract="governance-starter-v8"
        policy=json.loads((template/h.TEMPLATE_POLICY).read_text());policy["starter_files"]=sorted(h.required_starters(contract));(template/h.TEMPLATE_POLICY).write_bytes(h.encoded(policy))
        identity={"schema_version":1,"project_id":"orchard","project_name":"Orchard","purpose":self.arguments["purpose"],"relative_path":"Projects/Orchard"}
        proposed,sources,original=h.source_snapshot(self.root,fixture.SOURCE_SKILL,identity,contract=contract)
        for source in sources:
            name=source["destination"];source["adoption"]="specialized" if name in h.SPECIALIZED_FILES and proposed[name]!=original.get(name) else "adopted"
        record={"schema_version":1,"setup_contract":contract,"status":"partial","mode":"create","operation_id":"project-setup-"+"8"*32,
                "identity":identity,"project_root":str(self.target),"sources":sources,"owned_files":{name:h.sha(raw) for name,raw in proposed.items()},"preserved_files":{},
                "preserved_licenses":{},"preserved_memory":{},"preserved_learning":{},"preserved_ontology":{},"recovery_before":{name:None for name in proposed},
                "completed_stages":[],"active_stage":"assets","checks":[],"created_at":"2026-09-09T00:00:00+00:00","git_setup":"separate"}
        receipt=self.target/h.RECORD;receipt.parent.mkdir(parents=True);receipt.write_bytes(h.encoded(record))
        first=self.run_setup();shutil.rmtree(template);backup.rename(template)
        return first

    def adopt(self):
        return self.run_setup(mode="prepare-existing",adopt_module="ontology-advanced")

    def assert_base(self, before, after):
        for key in self.helper.BASE_IMMUTABLE:
            self.assertEqual(before.get(key),after.get(key),key)

    def populate(self):
        h=self.helper;cfg_path=self.target/"ontology.yaml";config=json.loads(cfg_path.read_text())
        config["retrieval"]["default_limit"]=17;cfg_path.write_bytes(h.encoded(config))
        graph=self.target/config["project_files"][0];value=json.loads(graph.read_text())
        value["@graph"].append({"@id":"urn:sys4ai:ontology:project:orchard:owned","@type":["urn:sys4ai:ontology:core:Artifact"],"kind":"instance","label":"Owned meaning","definition":"Project-authored content stays unchanged.","lifecycle":"approved","module":"project","fact_kind":"asserted","sources":[{"path":"SPECS.md","sha256":h.sha((self.target/"SPECS.md").read_bytes()),"locator":"line:1"}]})
        graph.write_bytes(h.encoded(value))
        for name,content in (("ONTOLOGY/extensions/authored.json","Retained extension data.\n"),("control_records/ontology/proposals/owned.json","Retained proposal.\n"),("MEMORY/retained.md","Retained memory.\n")):
            path=self.target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
        memory=self.target/"memory.yaml";cfg=json.loads(memory.read_text());cfg["integration"]["automatic_capture"]=False;memory.write_bytes(h.encoded(cfg))

    def test_populated_v8_only_selected_upgrade_refreshes_verified_capability(self):
        obsolete=self.root/self.helper.TEMPLATE/".agents/skills/ontology/obsolete-owned-resource.txt"
        obsolete.write_text("An old receipt-owned capability resource.\n")
        first=self.historical();self.populate();obsolete.unlink()
        selected=self.root/self.helper.TEMPLATE/".agents/skills/ontology/README.md";selected.write_bytes(selected.read_bytes()+b"\nReviewed advanced release update.\n")
        before=fixture.manifest(self.target)
        repeated=self.run_setup();self.assert_base(first,repeated)
        self.assertFalse((self.target/"ontology-advanced.yaml").exists())
        after=self.adopt();self.assert_base(first,after)
        operation=after["module_adoptions"][-1]
        self.assertEqual(operation["module_id"],"ontology-advanced")
        self.assertFalse(operation["new_ontology"]);self.assertTrue(operation["new_advanced"])
        self.assertEqual(operation["packages"][".agents/skills/ontology"]["decision"],"refreshed-owned-package")
        self.assertFalse((self.target/".agents/skills/ontology/obsolete-owned-resource.txt").exists())
        self.assertTrue(operation["capabilities"]["installed"],operation["capabilities"])
        for name in before:
            if name.startswith(("ONTOLOGY/","control_records/ontology/","MEMORY/")) or name in {"ontology.yaml","memory.yaml","SOUL.md","AGENTS.md","ROLE.md","LICENSE","LICENSE-CODE","LICENSE-DOCS"}:
                self.assertEqual(before[name],fixture.manifest(self.target)[name],name)
        repeat=self.adopt();self.assertEqual(len(repeat["module_adoptions"]),1);self.assert_base(first,repeat)
        selected.write_bytes(selected.read_bytes()+b"\nNext selected capability update.\n")
        refreshed=self.adopt();self.assertEqual(len(refreshed["module_adoptions"]),2);self.assert_base(first,refreshed)

    def test_missing_and_customized_capability_refuse_before_any_write(self):
        self.historical()
        path=self.target/".agents/skills/ontology/scripts/ontology_wiki.py";raw=path.read_bytes()
        for missing in (True,False):
            if missing:path.unlink()
            else:path.write_bytes(raw+b"\n# Project-owned customization.\n")
            before=fixture.manifest(self.root)
            with self.assertRaises(self.helper.InitializationError):self.adopt()
            self.assertEqual(before,fixture.manifest(self.root))
            path.write_bytes(raw)

    def test_earlier_receipt_installs_explicit_baseline_prerequisite_in_same_operation(self):
        first=self.historical(7)
        after=self.adopt();self.assert_base(first,after)
        operation=after["module_adoptions"][-1]
        self.assertTrue(operation["new_ontology"])
        self.assertEqual(operation["prerequisites"],[{"module_id":"ontology","disposition":"install-neutral-baseline"}])
        self.assertTrue(operation["capabilities"]["installed"],operation["capabilities"])
        self.assertEqual(json.loads((self.target/"ontology.yaml").read_text())["project"]["id"],"orchard")
        self.assertNotIn("preserved_ontology",after)


if __name__ == "__main__":
    unittest.main()
