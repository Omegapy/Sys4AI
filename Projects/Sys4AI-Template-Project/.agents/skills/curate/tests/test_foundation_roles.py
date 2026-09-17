from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import json

PACKAGE = Path(__file__).resolve().parents[1]
DEPOT = PACKAGE.parent.parent


class RoleTests(unittest.TestCase):
    def test_real_catalog_validates_exact_new_role_pairs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'SOUL.md').write_text('# Disposable role validation\n')
            (root/'Roles').mkdir()
            names=('curator-manager','documentation-curator','knowledge-curator','improvement-maintenance')
            for name in names:
                (root/'Roles'/name).mkdir()
                for kind in ('AGENTS','ROLE'):
                    shutil.copy2(DEPOT/'ROLES-depo'/f'{name}-{kind}.md',root/'Roles'/name/f'{kind}.md')
            helper=PACKAGE.parent/'manage-subagent-roles/scripts/role_catalog.py'
            result=subprocess.run([sys.executable,'-B',str(helper),'--repo-root',str(root),'list','--format','json'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads(result.stdout)
            self.assertEqual(data['role_root'],'Roles')
            self.assertEqual(len(data['valid_roles']),4)

    def test_default_controller_and_inactive_charter(self):
        director=(DEPOT/'ROLES-depo/project-director-ROLE.md').read_text()
        charter=(DEPOT/'ROLES-depo/project-curator-CURATOR.md').read_text()
        self.assertIn('Project Director remains the default',director)
        self.assertIn('Installation and reading this file are inactive',charter)
        for name in ('documentation-curator','knowledge-curator','improvement-maintenance'):
            role=(DEPOT/'ROLES-depo'/f'{name}-ROLE.md').read_text()
            self.assertIn('Do not publish Task, memory or ontology state',role)
            self.assertIn('Stopping condition',role)


if __name__=='__main__':unittest.main()
