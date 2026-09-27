"""Focused aligned guidance/package, fresh setup and completed-rerun evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SOURCE = Path(os.environ['SYS4AI_CURATOR_TEST_SOURCE']).resolve(strict=True)
WORK = Path(os.environ['SYS4AI_CURATOR_TEST_WORK']).resolve(strict=True)
OUTPUT = WORK.parent
sys.path.insert(0, str(SOURCE/'SKILLS-depo/init-new-project/tests'))
from test_curator_setup import compose, load
from test_curator_adoption import historical_project, current_sources

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, data):
    (OUTPUT/name).write_text(json.dumps(data, indent=2)+'\n')


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}


def receipt_info(destination, helper):
    path = destination/helper.RECORD
    data = json.loads(path.read_text())
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size,
            'status': data['status'], 'setup_contract': data['setup_contract'],
            'static_ready': data['static_ready']}


base = WORK/'current-package'
base.mkdir()
root, helper, updater, checked, applied = compose(base)
template = root/helper.TEMPLATE
before = inventory(template)
final_check = updater.update(root, 'check')
assert final_check['status'] == 'current' and before == inventory(template)
save('distribution.json', {'depot': str(root), 'check': checked, 'apply': applied,
                           'final_check': final_check, 'check_preserved_bytes': True})
save('source-destination-inventory.json', updater.load_state(root)['files'])
save('template-final-inventory.json', before)
role_owner = load(template/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py', 'alignment_role_catalog')
catalog = role_owner.build_catalog(template)
assert not catalog.invalid_roles and catalog.index_status == 'current'
save('role-catalog.json', catalog.to_dict())
selected = ['test_all_embedded_packages_are_complete_and_parseable',
            'test_complete_static_capability_inventory_includes_health_and_test_delivery',
            'test_curator_contract_is_complete_neutral_and_owner_bound',
            'test_starter_policy_has_no_product_runtime_bundle',
            'test_project_guidance_links_resolve']
command = [sys.executable, '-B', '-m', 'unittest', '-v',
           *('test_template_contract.TemplateContractTests.'+name for name in selected)]
result = subprocess.run(command, cwd=template/'tests', capture_output=True)
(OUTPUT/'template-contract.stdout').write_bytes(result.stdout)
(OUTPUT/'template-contract.stderr').write_bytes(result.stderr)
save('template-contract-result.json', {'command': command, 'returncode': result.returncode,
                                      'tests': len(selected), 'summary': result.stderr.decode()[-2000:]})
assert result.returncode == 0, result.stderr.decode()[-2000:]
assert before == inventory(template)

destination = root/'Projects/current'
args = dict(mode='create', destination=destination, project_id='current',
            project_name='Current package', purpose='Ordinary current package fixture')
created = helper.run_initialization(**args)
assert created['status'] == 'completed' and created['static_ready']
assert created['setup_contract'] == 'governance-starter-v10'
save('fresh-receipt.json', created)
cfg = json.loads((destination/'curator.yaml').read_text())
assert cfg['runtime'] is None and not cfg['schedule']['enabled'] and not cfg['autonomous_write']
assert cfg['project']['id'] == 'current'
(destination/'notes.md').write_text('Later project-owned work.\n')
memory = destination/'memory.yaml'
config = json.loads(memory.read_text()); config['integration']['automatic_capture'] = False
memory.write_bytes(helper.encoded(config)); memory_before = memory.read_bytes()
repeated = helper.run_initialization(**args)
assert repeated['status'] == 'completed' and repeated['static_ready']
assert {k: created.get(k) for k in helper.BASE_IMMUTABLE} == {k: repeated.get(k) for k in helper.BASE_IMMUTABLE}
assert memory.read_bytes() == memory_before
assert (destination/'notes.md').read_text() == 'Later project-owned work.\n'
state_before = inventory(destination)
assessment = helper._curator('assess', destination)
assert assessment['state'] == 'installed_inactive' and assessment['compatible']
assert not assessment['runtime_observed'] and assessment['runtime'] == 'not-exercised'
assert state_before == inventory(destination)
save('completed-rerun.json', {'receipt': receipt_info(destination, helper),
                              'assessment': assessment, 'base_fields_preserved': True,
                              'capture_off_preserved': True, 'later_edits_preserved': True})

legacy_base = WORK/'prior-edition'
legacy_base.mkdir()
legacy_root, legacy, original = historical_project(legacy_base, edition=9)
current = current_sources(legacy_root)
protected = {name: (legacy/name).read_bytes() for name in ('memory.yaml', 'LICENSE.custom', 'notes.md')}
save('historical-v9-original-receipt.json', original)
prior = current.run_initialization(mode='prepare-existing', destination=legacy, project_id='legacy',
                                   project_name='Legacy', purpose='Prior edition software')
assert prior['status'] == 'completed' and prior['setup_contract'] == 'governance-starter-v9'
assert {k: original.get(k) for k in current.BASE_IMMUTABLE} == {k: prior.get(k) for k in current.BASE_IMMUTABLE}
assert protected == {name: (legacy/name).read_bytes() for name in protected}
assert not (legacy/'curator.yaml').exists()
save('historical-v9-rerun.json', {'receipt': receipt_info(legacy, current),
                                'base_fields_preserved': True, 'no_implicit_curator_adoption': True,
                                'capture_off_and_licensing_preserved': True,
                                'fixture_provenance': 'Reconstructed v9 inputs executed by current owner; not historical binaries.'})
save('result.json', {'status': 'passed', 'template_contract_tests': len(selected),
                     'fresh_current_setup': True, 'completed_current_rerun': True,
                     'completed_v9_rerun': True, 'static_runtime': 'not-exercised',
                     'fresh_project_receipt': receipt_info(destination, helper),
                     'prior_edition_receipt': receipt_info(legacy, current),
                     'live_source_or_template_changed': False})
print(json.dumps({'status': 'passed', 'template_contract_tests': len(selected),
                  'fresh_current_setup': True, 'completed_current_rerun': True,
                  'completed_v9_rerun': True}))
