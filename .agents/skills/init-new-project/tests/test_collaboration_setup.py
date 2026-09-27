"""Confined default installation, prior-receipt adoption and refusal checks."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from test_curator_setup import compose, fixture_directory, work_root


class CollaborationSetupTests(unittest.TestCase):
    def ready(self, h, destination, record):
        self.assertEqual(record['status'], 'completed')
        self.assertTrue(record['static_ready'])
        operation = record['module_adoptions'][-1]
        self.assertEqual(operation['module_id'], 'collaborate')
        self.assertEqual(operation['status'], 'completed')
        self.assertTrue(operation['capabilities']['enabled'])
        self.assertEqual(operation['capabilities']['runtime'], 'not-exercised')
        self.assertTrue(any(row['component'] == 'collaborate' and row['outcome'] == 'passed' for row in record['static_health']['components']))
        self.assertFalse((destination/'Evidence').exists())
        self.assertFalse((destination/'control_records/collaboration').exists())
        retained = work_root().parent / 'retained'
        retained.mkdir(exist_ok=True)
        (retained/(destination.name+'-receipt.json')).write_bytes(h.encoded(record))
        return operation

    def test_create_first_prepare_and_current_rerun(self):
        with fixture_directory('collaboration-defaults') as temp:
            root,h,_,_,_=compose(temp)
            created=root/'Projects/created'
            args=dict(mode='create',destination=created,project_id='created',project_name='Created',purpose='Default collaboration fixture')
            first=h.run_initialization(**args)
            operation=self.ready(h,created,first)
            saved=(created/h.RECORD).read_bytes()
            cli=subprocess.run([sys.executable,'-B',str(created/'.agents/skills/init-new-project/scripts/init_new_project.py'),'assess-collaboration','--destination',str(created)],capture_output=True,text=True,timeout=30)
            self.assertEqual(cli.returncode,0,cli.stderr+cli.stdout)
            self.assertTrue(json.loads(cli.stdout)['enabled'])
            self.assertEqual((created/h.RECORD).read_bytes(),saved)
            self.assertEqual(operation['packages'][h.COLLABORATION.ROOT]['decision'],'preserved-package')
            (created/'authored.txt').write_text('Keep this authored content.\n')
            repeated=h.run_initialization(**args)
            self.assertEqual(repeated['setup_contract'],first['setup_contract'])
            self.assertEqual(repeated['operation_id'],first['operation_id'])
            self.assertEqual(len(repeated['module_adoptions']),1)
            self.assertEqual(repeated['module_adoptions'][0]['operation_id'],operation['operation_id'])
            self.assertEqual((created/'authored.txt').read_text(),'Keep this authored content.\n')
            prepared=root/'Projects/prepared';prepared.mkdir();(prepared/'authored.txt').write_text('Existing work.\n')
            record=h.run_initialization(mode='prepare-existing',destination=prepared,project_id='prepared',project_name='Prepared',purpose='First existing preparation')
            self.ready(h,prepared,record)
            self.assertEqual((prepared/'authored.txt').read_text(),'Existing work.\n')

    def legacy(self, root,h):
        # Reconstructed supported v9 receipt, created by actual base-recovery
        # owner. It is synthetic preservation evidence, not historical/native.
        template=root/h.TEMPLATE;backup=root/'saved-template';shutil.copytree(template,backup)
        shutil.rmtree(template/h.COLLABORATION.ROOT)
        for name,(heading,marker) in h.COLLABORATION.GUIDANCE.items():
            path=template/name;text=path.read_text();start=text.index(heading+'\n');end=text.find('\n## ',start+len(heading));text=text[:start]+(text[end:] if end!=-1 else '')
            path.write_text(text)
        contract='governance-starter-v9';policy=json.loads((template/h.TEMPLATE_POLICY).read_text());policy['starter_files']=sorted(h.required_starters(contract));(template/h.TEMPLATE_POLICY).write_bytes(h.encoded(policy))
        dest=root/'Projects/legacy';identity=dict(schema_version=1,project_id='legacy',project_name='Legacy',purpose='Prior receipt fixture',relative_path='Projects/legacy')
        proposed,sources,original=h.source_snapshot(root,root/'SKILLS-depo/init-new-project',identity,contract=contract,destination=dest)
        for row in sources:
            name=row['destination'];row['adoption']='specialized' if name in h.SPECIALIZED_FILES and proposed[name]!=original.get(name) else 'adopted'
        record=dict(schema_version=1,setup_contract=contract,status='partial',mode='create',operation_id='project-setup-'+'a'*32,identity=identity,project_root=str(dest),sources=sources,
            owned_files={name:h.sha(raw) for name,raw in proposed.items()},preserved_files={},recovery_before={name:None for name in proposed},completed_stages=[],active_stage='assets',checks=[],created_at='2026-09-01T00:00:00+00:00',git_setup='separate',
            preserved_licenses={},preserved_memory={},preserved_learning={},preserved_ontology={})
        path=dest/h.RECORD;path.parent.mkdir(parents=True);h.validate_record(record,dest,identity);path.write_bytes(h.encoded(record))
        args=dict(mode='create',destination=dest,project_id='legacy',project_name='Legacy',purpose='Prior receipt fixture')
        completed=h._run_initialization_base(**args)
        self.assertEqual(completed['status'],'completed');self.assertFalse((dest/h.COLLABORATION.ROOT).exists())
        shutil.rmtree(template);backup.rename(template)
        return dest,completed,{**args,'mode':'prepare-existing'}

    def test_earlier_completed_receipt_adopts_preserves_and_resumes_partial(self):
        with fixture_directory('collaboration-prior') as temp:
            root,h,_,_,_=compose(temp);dest,base,args=self.legacy(root,h)
            protected={name:(dest/name).read_bytes() for name in ('AGENTS.md','ROLE.md','SOUL.md','memory.yaml','ontology.yaml','ontology-advanced.yaml','project.json')}
            original=(dest/h.RECORD).read_bytes()
            # Inject one local filesystem failure after a durable partial module
            # exists. Resume with identical ordinary request and exact sources.
            write=h.atomic_write
            def once(path,raw,expected=None,**kw):
                if str(path).endswith('/collaborate/SKILL.md'):
                    raise OSError('synthetic interrupted collaboration publication')
                return write(path,raw,expected,**kw)
            h.atomic_write=once
            with self.assertRaises(h.InitializationError):h.run_initialization(**args)
            h.atomic_write=write
            partial=json.loads((dest/h.RECORD).read_text());self.assertEqual(partial['status'],'completed');self.assertEqual(partial['module_adoptions'][-1]['status'],'partial')
            record=h.run_initialization(**args);op=self.ready(h,dest,record)
            self.assertEqual(op['packages'][h.COLLABORATION.ROOT]['decision'],'adopted')
            self.assertEqual({k:record.get(k) for k in h.BASE_IMMUTABLE},{k:base.get(k) for k in h.BASE_IMMUTABLE})
            self.assertEqual(protected,{name:(dest/name).read_bytes() for name in protected})
            prior=json.loads((dest/op['base_receipt']['path']).read_text())
            self.assertEqual({k:prior.get(k) for k in h.BASE_IMMUTABLE},{k:base.get(k) for k in h.BASE_IMMUTABLE})
            repeated=h.run_initialization(**args);self.assertEqual(repeated['module_adoptions'][0]['operation_id'],op['operation_id']);self.assertEqual(len(repeated['module_adoptions']),1)

    def test_conflict_and_unsupported_owner_refuse_without_overwrite(self):
        with fixture_directory('collaboration-refusal') as temp:
            root,h,_,_,_=compose(temp);dest,_,args=self.legacy(root,h)
            custom=dest/h.COLLABORATION.ROOT/'SKILL.md';custom.parent.mkdir(parents=True);custom.write_text('Project-owned incomplete collaboration.\n')
            before=custom.read_bytes()
            with self.assertRaisesRegex(h.InitializationError,'customized/incomplete'):h.run_initialization(**args)
            self.assertEqual(custom.read_bytes(),before);self.assertEqual(list(custom.parent.iterdir()),[custom])
            shutil.rmtree(custom.parent)
            owner=dest/'.agents/skills/agent-task/scripts/task_state.py';owner.write_bytes(owner.read_bytes()+b'\nraise RuntimeError("Must not execute")\n');before=owner.read_bytes()
            with self.assertRaisesRegex(h.InitializationError,'unsupported current Task owner'):h.run_initialization(**args)
            self.assertEqual(owner.read_bytes(),before);self.assertFalse(custom.parent.exists())


if __name__=='__main__':unittest.main()
