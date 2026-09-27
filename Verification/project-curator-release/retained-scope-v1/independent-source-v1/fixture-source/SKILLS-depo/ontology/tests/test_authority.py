from pathlib import Path
import tempfile
import unittest
import copy
from support import *
from ontology_core import load_project, OntologyError
from ontology_authority import authorize
from ontology_publication import publish


class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=make_project(Path(self.temp.name)/"project");bind_director(self.root)
        self.proposal=proposal(self.root,[record("fixture")]);self.grant=grant(self.root,self.proposal)

    def test_current_director_is_authorized_without_creating_other_state(self):
        before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        authorize(load_project(self.root),self.grant,self.proposal,self.grant["preview_sha256"])
        self.assertEqual(before,{p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_child_wrong_project_memory_grant_and_overbroad_scope_fail(self):
        changes=[("actor_kind","child"),("project_id","other"),("grant_id","MEMGRANT-1234"),("scope",["ONTOLOGY"]),("payload_sha256","0"*64),("actor_id","/root/child")]
        for key,value in changes:
            candidate=copy.deepcopy(self.grant);candidate[key]=value
            with self.subTest(key=key):
                with self.assertRaises(OntologyError):authorize(load_project(self.root),candidate,self.proposal,self.grant["preview_sha256"])

    def test_stale_authority_and_expired_native_evidence_fail(self):
        candidate=copy.deepcopy(self.grant);candidate["expires_at"]="2000-01-01T00:00:00Z"
        with self.assertRaises(OntologyError):authorize(load_project(self.root),candidate,self.proposal,candidate["preview_sha256"])
        (self.root/"ROLE.md").write_text("Changed current governance")
        with self.assertRaises(OntologyError) as error:authorize(load_project(self.root),self.grant,self.proposal,self.grant["preview_sha256"])
        self.assertEqual(error.exception.code,"authority_changed")

    def test_unverified_active_manager_blocks_instead_of_trusting_raw_json(self):
        write_json(self.root/"Tasks/example/task.json",{"orchestration":{"manager_id":"m1","stage":"active","assignments":{"m1":{"state":"active","fit":{"writes":["ONTOLOGY/modules/project"]}}}}})
        with self.assertRaises(OntologyError):authorize(load_project(self.root),self.grant,self.proposal,self.grant["preview_sha256"])

    def test_stale_manager_task_digest_is_rejected(self):
        candidate=copy.deepcopy(self.grant);candidate["actor_kind"]="manager"
        task_path="Tasks/example/task.json";write_json(self.root/task_path,{"task_id":"example"})
        candidate["task"]={"path":task_path,"sha256":"0"*64,"task_id":"example","execution_id":"execution","generation":1,"assignment_id":"manager"}
        with self.assertRaises(OntologyError) as error:authorize(load_project(self.root),candidate,self.proposal,candidate["preview_sha256"])
        self.assertEqual(error.exception.code,"task_changed")


class ConfirmedManagerAuthorityTests(unittest.TestCase):
    """Actual installed Task state validator, explicitly synthetic native receipts."""
    def setUp(self):
        sys.path.insert(0, str(PACKAGE.parent / "agent-task/tests"))
        import test_orchestration_state as task_fixture
        self.driver = task_fixture.OrchestrationTests(methodName="test_legacy_and_v2_read_only_and_strict_keys")
        original = self.driver.manager_data
        def manager_data(aid):
            data = original(aid)
            data["fit"]["writes"] = ["ONTOLOGY/modules/project", "control_records/ontology"]
            return data
        self.driver.manager_data = manager_data
        self.driver.setUp()
        self.addCleanup(self.driver.tearDown)
        self.root = make_project(self.driver.root)
        shutil.copytree(PACKAGE.parent / "agent-task", self.root / ".agents/skills/agent-task", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        bind_director(self.root)
        self.proposal = proposal(self.root, [record("manager-published")])
        self.grant = grant(self.root, self.proposal, actor=self.driver.actor)
        d = self.driver
        relative = str(d.folder.relative_to(self.root) / "task.json")
        self.grant.update(actor_kind="manager", task={"path":relative, "sha256":sha256(self.root / relative), "task_id":d.state["task_id"], "execution_id":d.exec_id, "generation":d.generation, "assignment_id":"manager1"})

    def test_confirmed_manager_publishes_with_current_exact_task_scope(self):
        before = (self.root / self.grant["task"]["path"]).read_bytes()
        result = publish(self.root, self.proposal, self.grant, expected_preview_sha256=self.grant["preview_sha256"])
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["publisher"]["actor_kind"], "manager")
        self.assertEqual(before, (self.root / self.grant["task"]["path"]).read_bytes())

    def test_changed_generation_and_overlapping_director_fail(self):
        changed = copy.deepcopy(self.grant); changed["task"]["generation"] += 1
        with self.assertRaises(OntologyError) as error: authorize(load_project(self.root), changed, self.proposal, changed["preview_sha256"])
        self.assertEqual(error.exception.code, "manager_unconfirmed")
        director = grant(self.root, self.proposal)
        with self.assertRaises(OntologyError) as error: authorize(load_project(self.root), director, self.proposal, director["preview_sha256"])
        self.assertEqual(error.exception.code, "manager_owns_scope")


if __name__ == "__main__":unittest.main()

class NativeOntologyFixture:
    """Existing ontology owner and Task helper with synthetic native call frames."""
    def __init__(self,protocol_version=1):
        sys.path.insert(0,str(PACKAGE.parent/'agent-task/tests'))
        from test_orchestration_state import NativeOrchestrationFixture
        self.driver=NativeOrchestrationFixture(writes=['ONTOLOGY','control_records/ontology','ontology-advanced.yaml'],protocol_version=protocol_version)
        self.root=make_project(self.driver.root);bind_director(self.root)
        self.proposal=proposal(self.root,[record('native-published')])

    def authority(self,context,profile='core-v1'):
        value=grant(self.root,self.proposal,actor=self.driver.actor)
        value.update(schema_version=3,owner_profile=profile,actor_kind='manager',controller_origin='curator',
            native_receipt=self.driver.roster(self.driver.actor),task=self.driver.binding(),
            broker_binding=self.driver.owner_binding(context,'ontology'))
        return value

    def close(self):self.driver.close()


class NativeOntologyAuthorityTests(unittest.TestCase):
    def test_v3_core_current_manager_publishes_with_exact_profile(self):
        fixture=NativeOntologyFixture();self.addCleanup(fixture.close)
        context=fixture.driver.context('ontology.publish');value=fixture.authority(context)
        with fixture.driver.authority.invoke(context):
            result=publish(fixture.root,fixture.proposal,value,expected_preview_sha256=value['preview_sha256'])
        self.assertEqual(result['status'],'complete')
        self.assertEqual(value['schema_version'],3)

    def test_v3_without_live_context_wrong_owner_profile_or_actor_fails(self):
        fixture=NativeOntologyFixture();self.addCleanup(fixture.close)
        context=fixture.driver.context('ontology.publish');value=fixture.authority(context)
        with self.assertRaises(OntologyError):
            publish(fixture.root,fixture.proposal,value,expected_preview_sha256=value['preview_sha256'])
        with fixture.driver.authority.invoke(context):
            for key,bad in [('actor_kind','director'),('owner_profile','unknown'),('unknown',True)]:
                candidate=copy.deepcopy(value);candidate[key]=bad
                with self.assertRaises(OntologyError):
                    publish(fixture.root,fixture.proposal,candidate,expected_preview_sha256=candidate['preview_sha256'])


class ForkOntologyAuthorityTests(unittest.TestCase):
    def test_old_or_unconfirmed_manager_epoch_cannot_publish_and_reconnected_v3_owner_can(self):
        fixture=NativeOntologyFixture(protocol_version=2);self.addCleanup(fixture.close);driver=fixture.driver
        old=driver.context('ontology_publish');old_authority=driver.authority
        released=driver.release_receipt('native-manager');resumed=driver.resume_receipt('native-manager')
        with self.assertRaises(driver.native.NativeError):
            with old_authority.invoke(old):pass
        context=driver.context('ontology_publish');value=fixture.authority(context)
        with driver.authority.invoke(context),self.assertRaises(OntologyError):
            publish(fixture.root,fixture.proposal,value,expected_preview_sha256=value['preview_sha256'])
        driver.event('manager.reconnect',{'assignment_id':'native-manager','receipt':resumed,'release_receipt':released,
            'role_reads':driver.role_acknowledgement('native-manager')})
        context=driver.context('ontology_publish');value=fixture.authority(context)
        with driver.authority.invoke(context):result=publish(fixture.root,fixture.proposal,value,expected_preview_sha256=value['preview_sha256'])
        self.assertEqual(result['status'],'complete');self.assertEqual(value['schema_version'],3)
        self.assertEqual(value['broker_binding']['call']['actor']['load_epoch'],2)
