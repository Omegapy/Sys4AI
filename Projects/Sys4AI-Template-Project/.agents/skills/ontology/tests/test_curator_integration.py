"""Integration semantics, exact pre/post recovery and authority boundary fixtures."""
from support import *
import tempfile
import unittest
from ontology_integration import *
from ontology_publication import integration_preview,integration_publish,integration_recover
from check_ontology import run_checks


def fixture(path):
    root=make_project(path);context=fixture_context();depot=context['root']
    recipe=context['contracts']/'integrations/curator/1.0.0'
    shutil.copytree(recipe,root/RECIPE_ROOT)
    for name in source_paths(resources(root)):
        if name in ('SOUL.md','AGENTS.md','ROLE.md'):continue
        src=(context['skills']/name.removeprefix('.agents/skills/') if name.startswith('.agents/skills/') else
             depot/'Projects/Sys4AI-Template-Project'/name)
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
    cfg=read_json(root/'curator.yaml');cfg['project'].update(id='example',coordination_root=str(root));write_json(root/'curator.yaml',cfg)
    session=read_json(root/'curator-session.yaml');session.update(project_id='example');write_json(root/'curator-session.yaml',session)
    bind_director(root);return root


def integration_grant(root,pre):
    now=datetime.now(timezone.utc);prop=pre['proposal'];cfg=read_json(root/'ontology.yaml')
    return {'schema_version':1,'grant_id':'ONTIGRANT-fixture','operation':'integrate-curator','project_id':cfg['project']['id'],
        'actor_id':cfg['publication']['binding']['actor_id'],'actor_kind':'director','native_receipt':{'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':cfg['publication']['binding']['actor_id'],'agent_status':'running'}]}},
        'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=5)).isoformat(),'task':None,
        'payload_sha256':pre['payload_sha256'],'preview_sha256':pre['preview_sha256'],'config_sha256':sha256(root/'ontology.yaml'),
        'scope':list(TARGETS),'reviewed_records':[{k:c[k] for k in ('path','expected_sha256','sha256')} for c in prop['changes']],
        'resources':prop['resources'],'sources':prop['sources'],'helpers':pre['before']['helpers']}


class CuratorIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=fixture(Path(self.temp.name)/'project')
        self.pre=integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-curator-test','reason':'Test exact Curator integration.'})
        self.grant=integration_grant(self.root,self.pre)
    def publish(self,fault=None):
        return integration_publish(self.root,self.pre['proposal'],self.grant,expected_preview_sha256=self.pre['preview_sha256'],fail_at=fault)
    def test_complete_semantics_and_read_nonmutation(self):
        result=self.publish();self.assertEqual(result['status'],'complete')
        checks=run_checks(self.root)
        self.assertTrue(checks['valid'],[r for r in checks['competency']['results'] if not r['valid']])
        prior={p:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        run_checks(self.root)
        self.assertEqual(prior,{p:(p.read_bytes(),p.stat().st_mtime_ns) for p in prior})
    def test_each_commit_boundary_recovery_and_idempotence(self):
        for fault in ('before_commit',*[f'after_commit:{n}' for n in range(1,5)],'projection','receipt'):
            with self.subTest(fault=fault):
                root=fixture(Path(self.temp.name)/fault.replace(':','-'))
                pre=integration_preview(root,{'schema_version':1,'operation_id':'ONTOP-curator-recovery','reason':'Recover exact original config.'});g=integration_grant(root,pre)
                self.assertEqual(integration_publish(root,pre['proposal'],g,expected_preview_sha256=pre['preview_sha256'],fail_at=fault)['status'],'partial')
                one=integration_recover(root,pre['proposal']['operation_id'],g)
                two=integration_recover(root,pre['proposal']['operation_id'],g)
                self.assertEqual(one,two);self.assertEqual(one['status'],'complete')
    def test_pre_intent_failure_and_hardlink_target_are_rejected(self):
        with self.assertRaises(OntologyError):self.publish('before_intent')
        self.assertFalse((self.root/'control_records/ontology/integrations/intents').exists())
        target=self.root/GRAPH;target.parent.mkdir(parents=True,exist_ok=True)
        source=self.root/'linked-target.txt';source.write_text(self.pre['proposal']['changes'][0]['content'])
        os.link(source,target)
        with self.assertRaises(OntologyError) as error:integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-hardlink-test','reason':'Reject hardlink target aliases.'})
        self.assertEqual(error.exception.code,'unsafe_file')
    def test_existing_config_binding_is_held_before_mutation(self):
        cfg=read_json(self.root/'ontology.yaml');cfg['source_allowlist'].append('ontology.yaml');write_json(self.root/'ontology.yaml',cfg)
        authored=record('config-bound',sources=[{'path':'ontology.yaml','sha256':sha256(self.root/'ontology.yaml'),'locator':'json:/project'}])
        add_records(self.root,[authored]);before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaises(OntologyError) as error:integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-config-binding','reason':'Preserve an authored config binding.'})
        self.assertEqual(error.exception.code,'integration_protected_binding')
        self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_partial_or_malformed_setup_provenance_is_not_ownership(self):
        for c in self.pre['proposal']['changes']:
            path=self.root/c['path'];path.parent.mkdir(parents=True,exist_ok=True);path.write_text(c['content'])
        value={'schema_version':1,'setup_contract':'governance-starter-v12','status':'partial','project_root':str(self.root),'completed_stages':['assets','registration','verification'],
               'curator_integration':{'edition':EDITION,'mode':'setup-generated','status':'completed','files':{c['path']:c['sha256'] for c in self.pre['proposal']['changes']}},
               'owned_files':{c['path']:c['sha256'] for c in self.pre['proposal']['changes']},'generated_files':{c['path']:{'sha256':c['sha256']} for c in self.pre['proposal']['changes'][:-1]}}
        for status in ('partial','completed'):
            value['status']=status;write_json(self.root/'control_records/project-setup.json',value)
            with self.assertRaises(OntologyError) as error:integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-invalid-setup','reason':'Reject partial or malformed owner proof.'})
            self.assertEqual(error.exception.code,'integration_unowned')
    def test_config_scope_and_unowned_collision(self):
        prop=copy.deepcopy(self.pre['proposal']);c=prop['changes'][-1];cfg=decode_json(c['content'].encode());cfg['retrieval']['max_limit']=99;c['content']=canonical_bytes(cfg).decode();c['sha256']=sha256(c['content'].encode())
        with self.assertRaises(OntologyError):check_proposal(self.root,prop)
        target=self.root/GRAPH;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(self.pre['proposal']['changes'][0]['content'])
        with self.assertRaises(OntologyError):integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-collision-test','reason':'Unowned equal bytes.'})
    def test_expired_grant_and_disabled_publication_are_rejected(self):
        expired=copy.deepcopy(self.grant);expired['expires_at']='2000-01-01T00:00:00Z'
        with self.assertRaises(OntologyError) as error:
            integration_publish(self.root,self.pre['proposal'],expired,expected_preview_sha256=self.pre['preview_sha256'])
        self.assertEqual(error.exception.code,'grant_expired')
        cfg=read_json(self.root/'ontology.yaml');cfg['publication']['enabled']=False;write_json(self.root/'ontology.yaml',cfg)
        pre=integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-disabled-test','reason':'Respect publication off.'});g=integration_grant(self.root,pre)
        with self.assertRaises(OntologyError) as error:
            integration_publish(self.root,pre['proposal'],g,expected_preview_sha256=pre['preview_sha256'])
        self.assertEqual(error.exception.code,'publication_disabled')
    def test_narrow_director_scope_and_identity_role_conflicts(self):
        cfg=read_json(self.root/'ontology.yaml');cfg['publication']['binding']['scope']=['ONTOLOGY/modules/project'];write_json(self.root/'ontology.yaml',cfg)
        pre=integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-scope-test','reason':'Respect bound canonical scope.'});g=integration_grant(self.root,pre)
        with self.assertRaises(OntologyError) as error:integration_publish(self.root,pre['proposal'],g,expected_preview_sha256=pre['preview_sha256'])
        self.assertEqual(error.exception.code,'director_scope')
        raw=(self.root/'curator-session.yaml').read_bytes();session=decode_json(raw);session['project_id']='another';write_json(self.root/'curator-session.yaml',session)
        with self.assertRaises(OntologyError) as error:integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-identity-test','reason':'Reject mixed identities.'})
        self.assertEqual(error.exception.code,'identity_mismatch');(self.root/'curator-session.yaml').write_bytes(raw)
        role=self.root/'Roles/curator-manager/ROLE.md';role.write_text(role.read_text().replace('name: curator-manager','name: another-role'))
        with self.assertRaises(OntologyError) as error:integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-role-test','reason':'Reject role identity mismatch.'})
        self.assertEqual(error.exception.code,'role_pair')
    def test_source_and_alias_changes_refuse_recovery(self):
        self.publish('after_commit:1')
        source=self.root/'CURATOR.md';prior=source.read_bytes();source.write_bytes(prior+b' ')
        with self.assertRaises(OntologyError) as error:integration_recover(self.root,self.pre['proposal']['operation_id'],self.grant)
        self.assertEqual(error.exception.code,'integration_input_changed');source.write_bytes(prior)
        target=self.root/BINDINGS;target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(self.root/GRAPH)
        with self.assertRaises(OntologyError) as error:integration_recover(self.root,self.pre['proposal']['operation_id'],self.grant)
        self.assertEqual(error.exception.code,'unsafe_symlink')
    def test_stale_grant_disabled_publication_third_state(self):
        wrong=copy.deepcopy(self.grant);wrong['operation']='publish'
        with self.assertRaises(OntologyError):integration_publish(self.root,self.pre['proposal'],wrong,expected_preview_sha256=self.pre['preview_sha256'])
        self.assertEqual(self.publish('after_commit:1')['status'],'partial')
        path=self.root/GRAPH;path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(OntologyError):integration_recover(self.root,self.pre['proposal']['operation_id'],self.grant)

if __name__=='__main__':unittest.main()

class CuratorManagerAuthorityTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0,str(PACKAGE.parent/'agent-task/tests'))
        import test_orchestration_state as task_fixture
        self.driver=task_fixture.OrchestrationTests(methodName='test_legacy_and_v2_read_only_and_strict_keys')
        original=self.driver.manager_data
        def selected(aid):
            import subprocess
            fixture(self.driver.root)
            helper=self.driver.root/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'
            subprocess.run([sys.executable,str(helper),'--repo-root',str(self.driver.root),'reindex'],check=True,capture_output=True)
            catalog=subprocess.run([sys.executable,str(helper),'--repo-root',str(self.driver.root),'list','--format','json'],check=True,capture_output=True)
            (self.driver.root/'catalog.json').write_bytes(catalog.stdout)
            self.driver.role['catalog']=self.driver.ref('catalog.json')
            data=original(aid);data['fit']['writes']=['ONTOLOGY','ontology.yaml','control_records/ontology'];return data
        self.driver.manager_data=selected;self.driver.setUp();self.addCleanup(self.driver.tearDown)
        self.root=self.driver.root
        shutil.copytree(PACKAGE.parent/'agent-task',self.root/'.agents/skills/agent-task',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
        import subprocess
        checked=subprocess.run([sys.executable,str(self.root/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'),'--repo-root',str(self.root),'reindex'],capture_output=True,text=True)
        self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
        self.pre=integration_preview(self.root,{'schema_version':1,'operation_id':'ONTOP-manager-integration','reason':'Verify confirmed manager scope with synthetic native evidence.'})
        self.grant=integration_grant(self.root,self.pre);d=self.driver
        relative=(d.folder.relative_to(self.root)/'task.json').as_posix()
        self.grant.update(actor_kind='manager',actor_id=d.actor,native_receipt=d.roster(d.actor,'running'),task={'path':relative,'sha256':sha256(self.root/relative),'task_id':d.state['task_id'],'execution_id':d.exec_id,'generation':d.generation,'assignment_id':'manager1'})
    def test_current_manager_and_overlapping_director(self):
        direct=integration_grant(self.root,self.pre)
        with self.assertRaises(OntologyError) as error:integration_publish(self.root,self.pre['proposal'],direct,expected_preview_sha256=self.pre['preview_sha256'])
        self.assertEqual(error.exception.code,'manager_owns_scope')
        result=integration_publish(self.root,self.pre['proposal'],self.grant,expected_preview_sha256=self.pre['preview_sha256'])
        self.assertEqual(result['status'],'complete');self.assertEqual(result['publisher']['actor_kind'],'manager')
    def test_stale_manager_generation(self):
        self.grant['task']['generation']+=1
        with self.assertRaises(OntologyError) as error:integration_publish(self.root,self.pre['proposal'],self.grant,expected_preview_sha256=self.pre['preview_sha256'])
        self.assertEqual(error.exception.code,'manager_unconfirmed')


class IntegrationNativeVersionGate(unittest.TestCase):
    def test_unsupported_native_protocol_cannot_use_legacy_grant(self):
        from unittest.mock import patch
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=fixture(Path(temporary.name)/'project')
        pre=integration_preview(root,{'schema_version':1,'operation_id':'ONTOP-native-gate','reason':'Verify explicit unsupported native version hold.'})
        value=integration_grant(root,pre);value.update(actor_kind='manager',task={'path':'Tasks/fixture/task.json'})
        with patch('ontology_authority.validate_manager_binding'),patch('ontology_authority.read_task',return_value=({'orchestration':{'version':2}},None)):
            with self.assertRaises(OntologyError) as error:authorize(load_project(root),value,pre['proposal'],pre)
        self.assertEqual(error.exception.code,'grant_version')
