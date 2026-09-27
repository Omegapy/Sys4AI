"""Complete disposable Template/setup fixtures using the actual distribution owner."""
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

def source_root():
    raw=os.environ.get('SYS4AI_CURATOR_TEST_SOURCE')
    if not raw: raise RuntimeError('Set SYS4AI_CURATOR_TEST_SOURCE to the explicitly selected read-only depot source root.')
    root=Path(raw)
    if not root.is_absolute() or root.resolve()!=root or not (root/'SKILLS-depo/init-new-project/assets/baseline-assets.json').is_file():
        raise RuntimeError('Fixture source must be an exact real absolute depot source root with packaged starter assets.')
    return root


def work_root():
    raw=os.environ.get('SYS4AI_CURATOR_TEST_WORK')
    if not raw: raise RuntimeError('Set SYS4AI_CURATOR_TEST_WORK to an existing isolated fixture directory.')
    root=Path(raw)
    if not root.is_absolute() or root.resolve()!=root or not root.is_dir() or source_root()==root or source_root().is_relative_to(root):
        raise RuntimeError('Fixture work must be an existing isolated directory, never the source root or its ancestor.')
    return root


def fixture_directory(prefix='case'):
    return tempfile.TemporaryDirectory(dir=work_root(),prefix='curator-'+prefix+'-')


def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module


def compose(base, *, source=None):
    source=source_root() if source is None else Path(source)
    assert Path(base).resolve().is_relative_to(work_root()) and Path(base).resolve()!=work_root(), 'Fixture writes must stay inside their separately selected temporary child.'
    assert source.resolve()==source_root(), 'Only the explicitly selected read-only source root is permitted.'
    root=Path(base)/'Sys4AI';root.mkdir()
    ignore=shutil.ignore_patterns('__pycache__','.DS_Store','*.pyc')
    for collection in source.iterdir():
        if collection.is_dir() and collection.name.endswith('-depo'):shutil.copytree(collection,root/collection.name,ignore=ignore)
    (root/'depot').mkdir();(root/'tools').mkdir()
    for name in ('template-update.json','template-update.md','projects.json'):shutil.copyfile(source/'depot'/name,root/'depot'/name)
    registry=json.loads((root/'depot/projects.json').read_text());registry['projects']=[row for row in registry['projects'] if row['id'] in ('sys4ai-depot','sys4ai-template-project')]
    (root/'depot/projects.json').write_text(json.dumps(registry,indent=2)+'\n')
    shutil.copyfile(source/'SKILLS-depo/init-new-project/assets/template_update.py',root/'tools/template_update.py')
    for name in ('Implementation_Plans/subagent_role_system_implementation_plan.md','Implementation_Plans/task_system_implementation_plan.md','Tasks/INDEX.md'):
        destination=root/'Projects/Sys4AI-Template-Project'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/'Projects/Sys4AI-Template-Project'/name,destination)
    updater=load(root/'tools/template_update.py','curator_fixture_updater_'+str(abs(hash(str(root)))))
    checked=updater.update(root,'check');applied=updater.update(root,'apply')
    helper=load(root/'SKILLS-depo/init-new-project/scripts/init_new_project.py','curator_fixture_initializer_'+str(abs(hash(str(root)))))
    return root,helper,updater,checked,applied


class CuratorSetupTests(unittest.TestCase):
    def test_first_preparation_specializes_manual_template_copy(self):
        with fixture_directory('manual') as temp:
            root,helper,_,_,_=compose(temp)
            destination=root/'Projects/manual'
            shutil.copytree(root/helper.TEMPLATE,destination,ignore=shutil.ignore_patterns('.template','__pycache__'))
            # A selected first preparation can add whole missing Curator pairs
            # while the actual role owner regenerates its exact prior index.
            for role in helper.CURATOR.ROLES: shutil.rmtree(destination/'Roles'/role)
            prior_roles={p.relative_to(destination).as_posix():p.read_bytes() for p in (destination/'Roles').rglob('*') if p.is_file() and p.name!='INDEX.md'}
            (destination/'Roles/INDEX.md').write_bytes(helper.planned_role_index(destination,{},{}))
            (destination/'authored.txt').write_text('Keep this manual project content.\n')
            report=helper.run_initialization(mode='prepare-existing',destination=destination,project_id='manual',project_name='Manual',purpose='First selected preparation')
            self.assertEqual(report['status'],'completed');self.assertTrue(report['static_ready'])
            cfg=json.loads((destination/'curator.yaml').read_text());self.assertEqual(cfg['project']['id'],'manual');self.assertEqual(cfg['project']['coordination_root'],str(destination))
            self.assertFalse(cfg['autonomous_write']);self.assertIsNone(cfg['runtime']);self.assertEqual(cfg['entitlements'],[])
            self.assertEqual((destination/'authored.txt').read_text(),'Keep this manual project content.\n')
            self.assertEqual(prior_roles,{name:(destination/name).read_bytes() for name in prior_roles})
            self.assertTrue(all((destination/'Roles'/role/'ROLE.md').is_file() for role in helper.CURATOR.ROLES))
            before={p.relative_to(destination).as_posix():p.read_bytes() for p in destination.rglob('*') if p.is_file()}
            command=[sys.executable,'-B',str(root/'SKILLS-depo/init-new-project/scripts/init_new_project.py'),'assess-curator','--destination',str(destination)]
            assessed_cli=subprocess.run(command,capture_output=True,text=True,check=False,timeout=20)
            self.assertEqual(assessed_cli.returncode,0,assessed_cli.stderr)
            self.assertEqual(json.loads(assessed_cli.stdout)['state'],'installed_session_enabled')
            self.assertEqual(before,{p.relative_to(destination).as_posix():p.read_bytes() for p in destination.rglob('*') if p.is_file()})
            source=destination/'.agents/skills/curate/scripts/curator.py';prior=source.read_bytes()
            source.write_bytes(prior+b'\nraise RuntimeError("Unknown customized project Python must not execute")\n')
            assessed=helper._curator('assess',destination)
            self.assertTrue(assessed['installed']);self.assertFalse(assessed['compatible']);self.assertEqual(assessed['inspector_execution'],'none')
            self.assertEqual(source.read_bytes(),prior+b'\nraise RuntimeError("Unknown customized project Python must not execute")\n')

    def test_two_domains_neutral_complete_and_isolated(self):
        with fixture_directory('setup') as temp:
            root,helper,updater,_,_=compose(temp)
            first=root/'Projects/software';second=root/'Projects/teaching'
            for destination,description in ((first,'A software build project'),(second,'A teaching curriculum')):
                record=helper.run_initialization(mode='create',destination=destination,project_id=destination.name,project_name=destination.name.title(),purpose=description)
                self.assertEqual(record['setup_contract'],'governance-starter-v12');self.assertEqual(record['status'],'completed');self.assertTrue(record['static_ready'])
                config=json.loads((destination/'curator.yaml').read_text());self.assertEqual(config['project']['id'],destination.name);self.assertEqual(config['project']['coordination_root'],str(destination))
                self.assertIsNone(config['project']['repository_id']);self.assertFalse(config['schedule']['enabled']);self.assertEqual(config['entitlements'],[]);self.assertFalse(config['service_installed']);self.assertFalse(config['hook_installed']);self.assertIsNone(config['runtime'])
                self.assertFalse((destination/'control_records/curator').exists());self.assertFalse((destination/'.sys4ai/curator').exists())
                self.assertTrue((destination/'Roles/curator-manager/ROLE.md').is_file());self.assertIn('curator-manager',(destination/'Roles/INDEX.md').read_text())
                self.assertTrue(json.loads((destination/'memory.yaml').read_text())['integration']['automatic_capture'])
                self.assertEqual(helper._curator('assess',destination)['state'],'installed_session_enabled')
            self.assertNotEqual((first/'project.json').read_bytes(),(second/'project.json').read_bytes())
            self.assertEqual((first/'CURATOR.md').read_bytes(),(second/'CURATOR.md').read_bytes())
            self.assertNotEqual((first/'ontology.yaml').read_bytes(),(second/'ontology.yaml').read_bytes())


if __name__=='__main__':unittest.main()
