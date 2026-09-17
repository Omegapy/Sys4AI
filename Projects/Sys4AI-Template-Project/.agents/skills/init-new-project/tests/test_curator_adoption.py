"""Reconstructed edition fixtures and exact Curator adoption through actual owners."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from test_integrated_setup import grant_for
from test_curator_setup import source_root,work_root,fixture_directory,compose,load


def current_sources(root):
    """The current Template was restored after historical fixture preparation."""
    assert root.resolve().is_relative_to(work_root())
    return load(root/'SKILLS-depo/init-new-project/scripts/init_new_project.py','curator_current_initializer_'+str(abs(hash(str(root)))))


def historical_project(base, edition=9):
    """Reconstruct supported edition inputs, then let the actual owner recover.

    These are reconstructed fixture bytes, not original historical binaries.
    Every reconstructed role helper must equal its existing exact approved pin.
    No completed receipt is relabeled and no role transition is performed.
    """
    root,h,_,_,_=compose(base);template=root/h.TEMPLATE;backup=Path(base)/'current-template'
    shutil.copytree(template,backup)
    for name in ('CURATOR.md','curator.yaml','document-ownership.json','.agents/skills/curate','reference-assets/CURATION-depo'):
        path=template/name
        if path.is_dir():shutil.rmtree(path)
        elif path.exists():path.unlink()
    for role in h.CURATOR.ROLES:shutil.rmtree(template/'Roles'/role)
    # The same fixed removals used by the existing packaged historical tests;
    # no import of a helper that discovers an unrelated live depot is needed.
    absent=[]
    if edition<9:absent += ['ontology-advanced.yaml','tools/template_update.py']
    if edition<8:absent += ['.agents/skills/ontology','reference-assets/ONTOLOGY-depo','ONTOLOGY','ontology.yaml']
    if edition<7:absent += ['.agents/skills/what-did-you-learn','reference-assets/LEARNING-depo']
    if edition<5:absent += ['.agents/skills/memory','reference-assets/MEMORY-depo','MEMORY','memory.yaml']
    for name in absent:
        path=template/name
        if path.is_dir():shutil.rmtree(path)
        elif path.exists():path.unlink()
    if edition==5:
        cfg=json.loads((template/'memory.yaml').read_text());cfg['integration']['automatic_capture']=False;(template/'memory.yaml').write_bytes(h.encoded(cfg))
    contract='governance-starter-v'+str(edition);role_root=h.ROLE_ROOTS[contract]
    if role_root!='Roles':
        (template/'Roles').rename(template/'fixture-role-hop');(template/'fixture-role-hop').rename(template/role_root)
        script=template/h.ROLE_HELPER
        reconstructed=script.read_text().replace('ROLE_ROOT_NAME = "Roles"','ROLE_ROOT_NAME = "'+role_root+'"').encode()
        assert h.sha(reconstructed)==h.ROLE_INSPECTOR_SHA256[role_root], 'Historical helper reconstruction must match the exact pre-existing approved pin.'
        script.write_bytes(reconstructed)
    if edition==1:
        shutil.rmtree(template/role_root/'task-manager');(template/role_root/'INDEX.md').unlink()
    else:
        files={'SOUL.md':(template/'SOUL.md').read_bytes(),h.ROLE_HELPER:(template/h.ROLE_HELPER).read_bytes()}
        files.update({role_root+'/'+name:raw for name,raw in h.tree_files(template/role_root).items() if name!='INDEX.md'})
        (template/role_root/'INDEX.md').write_bytes(h.role_index_bytes(files,required=True,contract=contract))
    policy=json.loads((template/h.TEMPLATE_POLICY).read_text());policy.update(roles=role_root,starter_files=sorted(h.required_starters(contract)));(template/h.TEMPLATE_POLICY).write_bytes(h.encoded(policy))
    destination=root/'Projects/legacy';identity={'schema_version':1,'project_id':'legacy','project_name':'Legacy','purpose':'Prior edition software','relative_path':'Projects/legacy'}
    proposed,sources,original=h.source_snapshot(root,root/'SKILLS-depo/init-new-project',identity,contract=contract)
    for row in sources:
        name=row['destination'];row['adoption']='specialized' if contract in h.MEMORY_CONTRACTS and name in h.SPECIALIZED_FILES and proposed[name]!=original.get(name) else 'adopted'
    record={'schema_version':1,'setup_contract':contract,'status':'partial','mode':'create','operation_id':'project-setup-'+format(edition,'x')*32,
            'identity':identity,'project_root':str(destination),'sources':sources,'owned_files':{name:h.sha(raw) for name,raw in proposed.items()},'preserved_files':{},
            'recovery_before':{name:None for name in proposed},'completed_stages':[],'active_stage':'assets','checks':[],'created_at':'2026-09-09T00:00:00+00:00','git_setup':'separate'}
    for field,contracts in [('preserved_licenses',h.LICENSE_CONTRACTS),('preserved_memory',h.MEMORY_CONTRACTS),('preserved_learning',h.LEARNING_CONTRACTS),('preserved_ontology',h.ONTOLOGY_CONTRACTS)]:
        if contract in contracts:record[field]={}
    receipt=destination/h.RECORD;receipt.parent.mkdir(parents=True);h.validate_record(record,destination,identity);receipt.write_bytes(h.encoded(record))
    record=h.run_initialization(mode='create',destination=destination,project_id='legacy',project_name='Legacy',purpose='Prior edition software')
    assert record['setup_contract']==contract and record['status']=='completed'
    shutil.rmtree(template);backup.rename(template)
    (destination/'LICENSE.custom').write_text('Existing project license retained.\n');(destination/'notes.md').write_text('Unrelated authored work.\n')
    if (destination/'memory.yaml').exists():
        cfg=json.loads((destination/'memory.yaml').read_text());cfg['integration']['automatic_capture']=False;(destination/'memory.yaml').write_bytes(h.encoded(cfg))
    return root,destination,record


class CuratorAdoptionTests(unittest.TestCase):
    def test_customized_partial_and_unowned_packages_preserve_exact_bytes(self):
        with fixture_directory('preservation') as temp:
            root,destination,_=historical_project(temp);helper=current_sources(root)
            args=dict(mode='prepare-existing',destination=destination,project_id='legacy',project_name='Legacy',purpose='Prior edition software',adopt_module='curator',integration_grant_file=grant_for)
            snapshot=lambda:{p.relative_to(destination).as_posix():p.read_bytes() for p in destination.rglob('*') if p.is_file()}
            owner=destination/'.agents/skills/memory/SKILL.md';original=owner.read_bytes()
            for state in ('customized','partial'):
                with self.subTest(state=state):
                    if state=='customized':owner.write_bytes(original+b'\nProject-owned customization.\n')
                    else:owner.unlink()
                    before=snapshot()
                    with self.assertRaises(helper.InitializationError):helper.run_initialization(**args)
                    self.assertEqual(snapshot(),before)
                    owner.write_bytes(original)
            unowned=destination/'.agents/skills/curate/README.md';unowned.parent.mkdir(parents=True);unowned.write_text('Unowned project package.\n')
            before=snapshot()
            with self.assertRaises(helper.InitializationError):helper.run_initialization(**args)
            self.assertEqual(snapshot(),before)
            shutil.rmtree(unowned.parent)
            (destination/'CURATOR.md').write_text('# Legacy maintenance charter\nKeep project-specific responsibilities.\n')
            (destination/'document-ownership.json').write_text(json.dumps({'schema_version':1,'entries':[]})+'\n')
            protected={name:(destination/name).read_bytes() for name in ('CURATOR.md','document-ownership.json','memory.yaml','LICENSE.custom','notes.md')}
            prior_receipt=(destination/helper.RECORD).read_bytes()
            adopted=helper.run_initialization(**args);operation=adopted['module_adoptions'][-1]
            self.assertEqual(operation['status'],'completed')
            self.assertEqual(protected,{name:(destination/name).read_bytes() for name in protected})
            self.assertEqual((destination/operation['base_receipt']['path']).read_bytes(),prior_receipt)
            self.assertEqual(operation['base_receipt']['sha256'],helper.sha(prior_receipt))
            self.assertNotIn('CURATOR.md',operation['files']);self.assertNotIn('document-ownership.json',operation['files'])

    def test_v1_through_v9_preserve_original_receipts_and_role_prerequisites(self):
        for edition in range(1,10):
            with self.subTest(edition=edition),fixture_directory('edition-'+str(edition)) as temp:
                root,destination,first=historical_project(temp,edition);h=current_sources(root)
                args=dict(mode='prepare-existing',destination=destination,project_id='legacy',project_name='Legacy',purpose='Prior edition software')
                repeated=h.run_initialization(**args)
                expected={key:first.get(key) for key in h.BASE_IMMUTABLE}
                self.assertEqual({key:repeated.get(key) for key in h.BASE_IMMUTABLE},expected)
                snapshot=lambda:{p.relative_to(destination).as_posix():p.read_bytes() for p in destination.rglob('*') if p.is_file()}
                before=snapshot()
                if edition in (1,2):
                    with self.assertRaises(h.InitializationError):h.run_initialization(**args,adopt_module='curator',integration_grant_file=grant_for)
                    self.assertEqual(snapshot(),before)
                    self.assertFalse((destination/'Roles').exists() if edition==1 else 'Roles' in {p.name for p in destination.iterdir()})
                else:
                    adopted=h.run_initialization(**args,adopt_module='curator',integration_grant_file=grant_for)
                    self.assertEqual({key:adopted.get(key) for key in h.BASE_IMMUTABLE},expected)
                    self.assertEqual(adopted['module_adoptions'][-1]['status'],'completed')
                    self.assertEqual((destination/'LICENSE.custom').read_bytes(),before['LICENSE.custom'])
                    if 'memory.yaml' in before:self.assertEqual((destination/'memory.yaml').read_bytes(),before['memory.yaml'])
                self.assertEqual(json.loads((destination/h.RECORD).read_text())['setup_contract'],'governance-starter-v'+str(edition))

    def test_selected_adoption_preserves_base_preferences_and_completed_rerun(self):
        with fixture_directory('adoption') as temp:
            root,destination,before=historical_project(temp);helper=current_sources(root)
            original={key:before.get(key) for key in helper.BASE_IMMUTABLE}
            protected={name:(destination/name).read_bytes() for name in ('memory.yaml','ontology-advanced.yaml','project.json','LICENSE.custom','notes.md')}
            args=dict(mode='prepare-existing',destination=destination,project_id='legacy',project_name='Legacy',purpose='Prior edition software')
            ordinary=helper.run_initialization(**args);self.assertEqual(ordinary['setup_contract'],'governance-starter-v9');self.assertFalse((destination/'curator.yaml').exists())
            adopted=helper.run_initialization(**args,adopt_module='curator',integration_grant_file=grant_for)
            self.assertEqual({key:adopted.get(key) for key in helper.BASE_IMMUTABLE},original)
            self.assertEqual(protected,{name:(destination/name).read_bytes() for name in protected})
            operation=adopted['module_adoptions'][-1];self.assertEqual(operation['status'],'completed');self.assertEqual(operation['module_id'],'project-curator')
            self.assertFalse(operation['capabilities']['authorized']);self.assertFalse(operation['capabilities']['runtime_observed'])
            # A source successor cannot silently refresh the completed adoption.
            source=root/'SKILLS-depo/curate/README.md';source.write_text(source.read_text()+'\nNew source edition, not selected for adoption.\n')
            updater=load(root/'tools/template_update.py','curator_rerun_updater');updater.update(root,'apply')
            old_bytes=(destination/'.agents/skills/curate/README.md').read_bytes()
            rerun=helper.run_initialization(**args,adopt_module='curator',integration_grant_file=grant_for)
            self.assertEqual(len(rerun['module_adoptions']),1);self.assertEqual(rerun['module_adoptions'][0]['operation_id'],operation['operation_id'])
            self.assertEqual((destination/'.agents/skills/curate/README.md').read_bytes(),old_bytes)
            self.assertEqual(rerun['module_adoptions'][0]['rerun'],'verified-current-module-without-refresh')


if __name__=='__main__':unittest.main()
