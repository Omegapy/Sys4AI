"""Final shipped Template and fresh disposable setup delivery checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import publish as p

os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['SYS4AI_CURATOR_TEST_SOURCE']=str(p.ROOT)
work=p.OUT/'fixtures-v2'
work.mkdir()
os.environ['SYS4AI_CURATOR_TEST_WORK']=str(work)
sys.path.insert(0,str(p.ROOT/'SKILLS-depo/init-new-project/tests'))
from test_curator_setup import compose, load

def ref(path):
    return {'path':path.relative_to(p.ROOT).as_posix(),'sha256':p.sha(path),'bytes':path.stat().st_size}

def local_inventory(root):
    return {f.relative_to(root).as_posix():p.sha(f) for f in root.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='.DS_Store'}

before=p.inventory(['Projects/Sys4AI-Template-Project'])
selected=['test_all_embedded_packages_are_complete_and_parseable',
          'test_complete_static_capability_inventory_includes_health_and_test_delivery',
          'test_curator_contract_is_complete_neutral_and_owner_bound',
          'test_starter_policy_has_no_product_runtime_bundle',
          'test_project_guidance_links_resolve']
command=[sys.executable,'-B','-m','unittest','-v',*('test_template_contract.TemplateContractTests.'+name for name in selected)]
result=subprocess.run(command,cwd=p.TEMPLATE/'tests',capture_output=True,env=os.environ)
(p.OUT/'v2-template-tests.stdout').write_bytes(result.stdout)
(p.OUT/'v2-template-tests.stderr').write_bytes(result.stderr)
p.save('v2-template-tests.json',{'command':command,'returncode':result.returncode,'selected_tests':selected,'summary':result.stderr.decode()[-2400:]})
assert result.returncode==0,result.stderr.decode()[-2400:]
assert before==p.inventory(['Projects/Sys4AI-Template-Project'])
print(json.dumps({'live_template_contract_tests':len(selected),'status':'passed'}),flush=True)

base=work/'shipped-package'
base.mkdir()
root,helper,updater,checked,applied=compose(base)
fixture_template=root/helper.TEMPLATE
final_check=updater.update(root,'check')
assert final_check['status']=='current'
p.save('v2-fixture-distribution.json',{'depot':str(root),'check':checked,'apply':applied,'final_check':final_check})
fixture_bindings=updater.load_state(root)['files']
p.save('v2-fixture-bindings.json',fixture_bindings)
fixture_inventory=local_inventory(fixture_template)
p.save('v2-fixture-template-inventory.json',fixture_inventory)

destination=root/'Projects/shipped-curator'
report=helper.run_initialization(mode='create',destination=destination,project_id='shipped-curator',project_name='Shipped Curator package',purpose='Disposable verification of the published Curator starter package.')
p.save('v2-fresh-result.json',report)
assert report['status']=='completed' and report['static_ready'] and report['setup_contract']=='governance-starter-v10'
receipt=destination/helper.RECORD
cfg=json.loads((destination/'curator.yaml').read_text())
assert cfg['project']['id']=='shipped-curator' and cfg['project']['coordination_root']==str(destination)
assert cfg['runtime'] is None and not cfg['schedule']['enabled'] and not cfg['autonomous_write']
assert not cfg['service_installed'] and not cfg['hook_installed'] and cfg['entitlements']==[]
assert not (destination/'control_records/curator').exists() and not (destination/'.sys4ai/curator').exists()
dest_before=local_inventory(destination)
assessment=helper._curator('assess',destination)
assert assessment['state']=='installed_inactive' and assessment['compatible'] and not assessment['runtime_observed'] and assessment['runtime']=='not-exercised'
assert dest_before==local_inventory(destination)
role_owner=load(destination/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py','shipped_publication_roles')
catalog=role_owner.build_catalog(destination)
assert not catalog.invalid_roles and catalog.index_status=='current'
p.save('v2-fresh-role-catalog.json',catalog.to_dict())
p.save('v2-fresh-project-inventory.json',dest_before)
capture=json.loads((destination/'memory.yaml').read_text())['integration']['automatic_capture']
assert capture is True
assert before==p.inventory(['Projects/Sys4AI-Template-Project'])
summary={'status':'passed','live_template_tests':len(selected),'fixture_managed_bindings':len(fixture_bindings),'fixture_template_file_count':len(fixture_inventory),'fresh_setup_receipt':ref(receipt),'setup_contract':report['setup_contract'],'static_ready':report['static_ready'],'curator_assessment':assessment,'fresh_role_index':'current','fresh_project_memory_capture':'on','assessment_preserved_files':True,'live_template_preserved_by_checks':True,'runtime':'not-exercised','real_product_adoption':False}
p.save('v2-shipped-package-result.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k!='curator_assessment'}),flush=True)
