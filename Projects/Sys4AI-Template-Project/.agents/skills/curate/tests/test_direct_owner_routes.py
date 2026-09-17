"""Current public-owner signatures and actual bounded source review.

Actual manager-bound mutation is performed by the manager, not synthesized by
this ordinary worker's checks.
"""
import inspect
import json
import shutil
from pathlib import Path
import sys
import tempfile
import unittest
from test_retained_application import SOURCE,WORK
from test_supported_application import files
sys.path.insert(0,str(SOURCE/'SKILLS-depo/memory/scripts'))
import task_state
import memory_publish
import memory_recovery
import ontology_publication
import curator_classification
from curator import review_selected_sources,validate_controller_selection
from curator_integration import content_hash
from curator_policy import PolicyError


class DirectOwnerRoutesTests(unittest.TestCase):
    def test_current_public_mutation_signatures_accept_fixed_keyword_names(self):
        root=str(WORK)
        cases=[
            (task_state.response_transaction,dict(command='orchestrate',project_root=root,tasks_root=root,selector='selected-task',expected_revision=1,raw_payload={})),
            (task_state.response_transaction,dict(command='record-response',project_root=root,tasks_root=root,selector='selected-task',expected_revision=1,raw_payload={})),
            (task_state.command_reconcile,dict(project_root=root,tasks_root=root,selector='selected-task',expected_revision=1,raw_payload={})),
            (memory_publish.publish,dict(root=root,payload={},grant_file='selected-owner-record',actor='selected-actor')),
            (memory_recovery.recover,dict(root=root,journal_path='selected-journal',grant_file='selected-owner-record',actor='selected-actor')),
            (ontology_publication.publish,dict(root=root,proposal={},grant={},expected_preview_sha256='a'*64)),
            (ontology_publication.recover,dict(root=root,operation_id='selected-original-operation',grant={})),
        ]
        for owner,arguments in cases:
            with self.subTest(owner=owner.__module__+'.'+owner.__name__):
                inspect.signature(owner).bind(**arguments)

    def test_bounded_review_uses_actual_owner_and_rechecks_source_bytes(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);path=root/'README.md';path.write_text('Selected factual documentation\n');content=path.read_bytes();sha=content_hash(content)
            entry=dict(id='readme',path='README.md',pattern=False,sha256=sha,class_='documentation',owner='project',generator=None,sources=[],sections=[],interfaces=[]);entry['class']=entry.pop('class_')
            arguments=dict(root=str(root),ownership={'schema_version':1,'entries':[entry]},targets=[dict(identity=dict(id='readme',path='README.md',sha256=sha),ranges=[[0,len(content)]])])
            payload=dict(analysis='source-ownership',paths=['README.md']);before=files(root)
            result=review_selected_sources(curator_classification,arguments,payload)
            self.assertEqual(result['state'],'reviewed');self.assertEqual(result['results'][0]['route'],'project.documentation')
            self.assertEqual(result['canonical_writes'],0);self.assertEqual(result['model_calls'],0);self.assertEqual(before,files(root))
            path.write_text('Later factual documentation\n');changed=files(root)
            with self.assertRaises(PolicyError):review_selected_sources(curator_classification,arguments,payload)
            self.assertEqual(changed,files(root))

    def test_versioned_controller_selection_reads_current_role_and_project(self):
        sys.path.insert(0,str(SOURCE/'SKILLS-depo/manage-subagent-roles/scripts'))
        import role_catalog
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);role=root/'Roles/curator-manager';role.mkdir(parents=True)
            for name in ['AGENTS.md','ROLE.md']:shutil.copyfile(SOURCE/('ROLES-depo/curator-manager-'+name),role/name)
            shutil.copyfile(SOURCE/'ROLES-depo/project-curator-CURATOR.md',root/'CURATOR.md')
            (root/'SOUL.md').write_text('Disposable project guidance for read-only selection validation.\n')
            shutil.copyfile(SOURCE/'ROLES-depo/project-director-ROLE.md',root/'ROLE.md')
            (root/'project.json').write_text(json.dumps(dict(schema_version=1,project_id='fixture',project_name='Fixture',purpose='Validate selected provenance',relative_path='Projects/fixture')))
            policy=json.loads((SOURCE/'CURATION-depo/starter/curator.yaml').read_text());policy['project']['id']='fixture';policy['project']['coordination_root']=str(root)
            (root/'curator.yaml').write_text(json.dumps(policy))
            def ref(name):return dict(path=name,sha256=content_hash((root/name).read_bytes()))
            selection=dict(schema_version=1,controller='curator',project_id='fixture',project=ref('project.json'),charter=ref('CURATOR.md'),policy=ref('curator.yaml'),role=dict(name='curator-manager',agents=ref('Roles/curator-manager/AGENTS.md'),role=ref('Roles/curator-manager/ROLE.md')))
            before=files(root);result=validate_controller_selection(root,selection,catalog_owner=role_catalog)
            self.assertEqual(result['state'],'validated');self.assertEqual(result['task_mode'],dict(task_schema_version=2,orchestration_version=1))
            self.assertFalse(result['task_creation']);self.assertFalse(result['manager_activation']);self.assertEqual(result['canonical_writes'],0);self.assertEqual(before,files(root))
            with self.assertRaises(PolicyError):validate_controller_selection(root,{**selection,'unexpected':'field'},catalog_owner=role_catalog)
            (root/'CURATOR.md').write_text('Changed selected charter\n')
            with self.assertRaises(PolicyError):validate_controller_selection(root,selection,catalog_owner=role_catalog)


if __name__=='__main__':unittest.main()
