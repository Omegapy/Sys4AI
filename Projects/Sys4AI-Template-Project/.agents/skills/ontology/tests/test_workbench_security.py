from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import tempfile
import unittest
import json

from support import CORE, canonical_bytes, read_json, sha256
from workbench_fixture import make_workbench_project, fixture_authority
from ontology_workbench import Workbench


class Client:
    def __init__(self, service):
        self.service=service
        self.csrf=""
        self.cookie=""

    def post(self, endpoint, body, **overrides):
        connection=HTTPConnection("127.0.0.1",self.service.server.server_port,timeout=30)
        headers={"Host":self.service.host_header,"Origin":self.service.origin,"Content-Type":"application/json", "X-Ontology-CSRF":self.csrf,"Cookie":self.cookie,**overrides}
        connection.request("POST","/api/"+endpoint,canonical_bytes(body),headers)
        response=connection.getresponse();data=json.loads(response.read());code=response.status
        cookie=response.getheader("Set-Cookie")
        if cookie:self.cookie=cookie.split(";")[0]
        connection.close()
        return code,data

    def connect(self):
        token=parse_qs(urlsplit(self.service.bootstrap_url()).fragment)["bootstrap"][0]
        code,result=self.post("session",{"bootstrap":token})
        assert code==200,(code,result)
        self.csrf=result["csrf"]
        return self


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=make_workbench_project(Path(self.temp.name)/"project")
        self.service=Workbench(self.root,fixture_authority(self.root)).start()
        self.client=Client(self.service).connect()

    def tearDown(self):
        self.service.close();self.temp.cleanup()

    def form(self, definition="A sourced browser-created concept."):
        return {"id":"urn:sys4ai:ontology:project:example:browser-concept","kind":"concept","label":"Browser concept",
                "definition":definition,"types":[CORE+"OntologyConcept"],"aliases":["browser alias"],
                "sources":[{"path":"SPECS.md","locator":"section:Specification"}],"reason":"Create an exact sourced concept through the real service."}

    def save(self, form=None, **args):
        path=read_json(self.root/"ontology.yaml")["project_files"][0]
        return self.client.post("draft",{"form":form or self.form(),"expected_target_sha256":sha256(self.root/path),**args})

    def test_origin_host_csrf_forged_authority_and_source_escape_are_rejected(self):
        before=sha256(self.root/"ontology.yaml")
        for overrides in ({"Origin":"https://hostile.example"},{"Host":"hostile.example"},{"X-Ontology-CSRF":"forged"}):
            self.assertEqual(self.client.post("state",{},**overrides)[0],403)
        self.assertEqual(self.client.post("state",{"actor_id":"/root"})[0],403)
        self.assertNotEqual(self.client.post("source",{"reference":{"path":"../../private","locator":"line:1"}})[0],200)
        (self.root/"escape.md").symlink_to(self.root/"SPECS.md")
        self.assertNotEqual(self.client.post("source",{"reference":{"path":"escape.md","locator":"line:1"}})[0],200)
        self.assertEqual(before,sha256(self.root/"ontology.yaml"))

    def test_browser_cookie_jar_isolates_ports_and_preserves_existing_tabs(self):
        second_tab = Client(self.service)
        second_tab.cookie = self.client.cookie
        second_tab.connect()
        self.assertEqual(second_tab.cookie, self.client.cookie)
        self.assertEqual(second_tab.csrf, self.client.csrf)
        reader = Workbench(self.root).start()
        try:
            other = Client(reader).connect()
            self.assertNotEqual(other.cookie.split("=",1)[0], self.client.cookie.split("=",1)[0])
            # A browser sends both host cookies to both local ports.
            shared = self.client.cookie + "; " + other.cookie
            self.client.cookie = second_tab.cookie = other.cookie = shared
            self.assertEqual(self.client.post("state",{})[0],200)
            self.assertEqual(second_tab.post("state",{})[0],200)
            code,state=other.post("state",{})
            self.assertEqual(code,200);self.assertFalse(state["authoring"])
            self.assertEqual(other.post("draft",{"form":self.form(),"expected_target_sha256":"0"*64})[0],403)
        finally:
            reader.close()

    def test_real_service_search_draft_invalid_validate_revise_review_publish_reopen(self):
        self.assertEqual(self.client.post("records",{"query":"sample"})[0],200)
        code,original=self.save(self.form(""));self.assertEqual(code,200,original)
        pid=original["head"]["proposal_id"]
        code,invalid=self.client.post("validate",{"id":pid,"revision":1});self.assertEqual(code,200,invalid)
        self.assertFalse(invalid["validation"]["eligible"])
        code,revised=self.save(proposal_id=pid,expected_revision=1);self.assertEqual(code,200,revised)
        code,valid=self.client.post("validate",{"id":pid,"revision":2});self.assertEqual(code,200,valid)
        self.assertTrue(valid["validation"]["eligible"],valid["validation"]["findings"])
        code,reviewed=self.client.post("decide",{"id":pid,"revision":2,"decision":"accept","reason":"Reviewed exact supported candidate.","validation_sha256":valid["head"]["validation_sha256"]});self.assertEqual(code,200,reviewed)
        code,result=self.client.post("publish",{"id":pid,"revision":2,"review_sha256":reviewed["head"]["review_sha256"]});self.assertEqual(code,200,result)
        self.assertEqual(result["status"],"published")
        self.assertTrue(all(row["matches_candidate"] for row in result["reopened"]))
        code,found=self.client.post("records",{"query":"browser alias"});self.assertEqual(code,200,found)
        self.assertEqual(found["records"][0]["label"],"Browser concept")

    def test_two_clients_stale_save_reject_and_reload_preserve_work(self):
        _,saved=self.save();pid=saved["head"]["proposal_id"]
        other=Client(self.service).connect()
        self.assertEqual(other.post("proposal",{"id":pid})[1]["revision"],saved["revision"])
        code,current=self.save(proposal_id=pid,expected_revision=1);self.assertEqual(code,200,current)
        path=read_json(self.root/"ontology.yaml")["project_files"][0]
        code,conflict=other.post("draft",{"form":self.form("A second client's pending text."),"expected_target_sha256":sha256(self.root/path),"proposal_id":pid,"expected_revision":1})
        self.assertEqual(code,409,conflict);self.assertTrue(conflict["draft_preserved"])
        code,rejected=self.client.post("decide",{"id":pid,"revision":2,"decision":"reject","reason":"Requires a different source."});self.assertEqual(code,200,rejected)
        self.assertEqual(other.post("proposal",{"id":pid})[1]["head"]["state"],"rejected")

    def test_core_protection_unsafe_text_and_browsing_only_session(self):
        form=self.form();form["id"]=CORE+"Artifact"
        self.assertNotEqual(self.save(form)[0],200)
        form=self.form();form["label"]='<img src=x onerror="alert(1)">'
        code,saved=self.save(form);self.assertEqual(code,200,saved)
        self.assertIn('<img',saved["revision"]["candidate"]["changes"][0]["content"])
        reader=Workbench(self.root).start()
        try:
            client=Client(reader).connect()
            self.assertEqual(client.post("state",{})[0],200)
            code,result=client.post("draft",{"form":self.form(),"expected_target_sha256":"0"*64})
            self.assertEqual(code,403,result)
        finally:reader.close()

    def test_composite_relation_draft_invalid_endpoint_and_deprecation_history(self):
        code,saved=self.save();self.assertEqual(code,200,saved)
        pid=saved["head"]["proposal_id"]
        relation=self.form();relation.update(id="urn:sys4ai:ontology:project:example:browser-relation",kind="relation",label="Browser relation",types=[CORE+"Relationship"],
            subject=self.form()["id"],predicate=CORE+"broader",object="urn:sys4ai:ontology:project:example:missing")
        code,value=self.save(relation,proposal_id=pid,expected_revision=1);self.assertEqual(code,200,value)
        _,invalid=self.client.post("validate",{"id":pid,"revision":2})
        self.assertFalse(invalid["validation"]["eligible"])
        self.assertIn("dangling_target",{f["code"] for f in invalid["validation"]["findings"]})
        relation["object"]="urn:sys4ai:ontology:project:example:related-artifact"
        code,value=self.save(relation,proposal_id=pid,expected_revision=2);self.assertEqual(code,200,value)
        _,valid=self.client.post("validate",{"id":pid,"revision":3})
        self.assertTrue(valid["validation"]["eligible"],valid["validation"]["findings"])
        canonical="urn:sys4ai:ontology:project:example:sample-artifact"
        _,inspected=self.client.post("inspect",{"id":canonical});original=inspected["record"]
        retired={"id":canonical,"kind":original["kind"],"label":original["label"],"definition":original["definition"],
                 "types":original["@type"],"aliases":original.get("aliases",[]),"sources":[{"path":"SPECS.md","locator":"section:Specification"}],
                 "reason":"Retain this historical identity and use the replacement.","lifecycle":"deprecated","replacement":"urn:sys4ai:ontology:project:example:related-artifact"}
        code,value=self.save(retired);self.assertEqual(code,200,value)
        content=json.loads(value["revision"]["candidate"]["changes"][0]["content"])
        row=next(r for r in content["@graph"] if r["@id"]==canonical)
        self.assertEqual(row["lifecycle"],"deprecated");self.assertTrue(row["history"])
        self.assertEqual(self.client.post("inspect",{"id":canonical})[1]["record"]["lifecycle"],"approved")


if __name__ == "__main__":
    unittest.main()
