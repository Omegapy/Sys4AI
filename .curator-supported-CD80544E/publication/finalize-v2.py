"""Record exact final package bindings and bounded publication evidence."""
import json
import os
from pathlib import Path
import publish as p

def ref(path):
    return {'path':path.relative_to(p.ROOT).as_posix(),'sha256':p.sha(path),'bytes':path.stat().st_size}

def delta(before,after):
    return [{'path':k,'before_sha256':before.get(k),'sha256':after.get(k)}
            for k in sorted(before.keys()|after.keys()) if before.get(k)!=after.get(k)]

spec=p.ROOT/'Verification/project-curator-supported-release-v1/manager/publication-final-inventory-v2.json'
expected=json.loads(spec.read_text())
assert p.sha(spec)=='1dec5bc5091999954bde89c2747ac3edda6fe97eb828337155699229e5b5a7b2'
source_rows=[]
for row in expected['rows']:
    actual=p.sha(p.ROOT/row['path'])
    assert actual==row['expected_live_sha256'],row['path']
    source_rows.append({'path':row['path'],'before_sha256':row['live_before_sha256'],
                        'sha256':actual,'disposition':row['disposition'],
                        'changed':actual!=row['live_before_sha256']})
assert sum(r['changed'] for r in source_rows)==68
p.save('v2-final-sources.json',source_rows)

state_path=p.ROOT/'.sys4ai/template-update/state.json'
state=json.loads(state_path.read_text())
binding_rows=[]
for name,row in state['files'].items():
    dest=p.TEMPLATE/name
    assert p.sha(dest)==row['sha256'],name
    assert dest.stat().st_mode & 0o777 == row['mode'],name
    if row.get('generated'):
        for path,item in row['generated']['inputs'].items():
            assert p.sha(p.TEMPLATE/path)==item['sha256'],path
            assert p.sha(p.ROOT/item['source'])==item['sha256'],item['source']
    else:
        assert p.sha(p.ROOT/row['source'])==row['sha256'],row['source']
    binding_rows.append({'destination':name,**row})
p.save('v2-live-owned-bindings.json',binding_rows)

prepared_path=p.ROOT/'.curator-supported-CD80544E/setup_compatibility/alignment-v4/source-destination-inventory.json'
prepared=json.loads(prepared_path.read_text())
assert len(prepared)==387
assert all(p.sha(p.TEMPLATE/k)==v['sha256'] for k,v in prepared.items())
p.save('v2-prepared-binding-comparison.json',{'prepared_inventory':ref(prepared_path),'prepared_binding_count':387,'matching_live_destination_hashes':387,'full_live_owned_binding_count':len(binding_rows),'distinct_full_live_additional_bindings':len(binding_rows)-387})

full_inventory={}
for file in sorted(p.TEMPLATE.rglob('*')):
    name=file.relative_to(p.TEMPLATE).as_posix()
    if file.is_symlink():
        full_inventory[name]={'kind':'symlink','target':os.readlink(file)}
    elif file.is_file():
        full_inventory[name]={'sha256':p.sha(file),'mode':file.stat().st_mode & 0o777,'bytes':file.stat().st_size,'managed':name in state['files']}
p.save('v2-full-live-template-inventory.json',full_inventory)

before=json.loads((p.OUT/'before.json').read_text())
sources=p.inventory([f.name for f in p.ROOT.iterdir() if f.is_dir() and f.name.endswith('-depo')]+['tools','tests','depot'])
protected=p.inventory(['.agents/skills','Roles','SOUL.md','ROLE.md','AGENTS.md','SPECS.md','README.md','depot/projects.json'])
template=p.inventory(['Projects/Sys4AI-Template-Project'])
allowed={r['path'] for r in source_rows if r['changed']}
source_changes=delta(before['sources'],sources)
assert len(source_changes)==68 and {r['path'] for r in source_changes}==allowed
assert before['protected']==protected
template_changes=delta(before['template'],template)
applied=json.loads((p.OUT/'v2-apply.json').read_text())
assert applied['returncode']==0 and applied['result']['status']=='applied'
preview=applied['result']
expected_destinations={('Projects/Sys4AI-Template-Project/'+k) for field in ['additions','updates','deletions'] for k in preview[field]}
assert {r['path'] for r in template_changes}==expected_destinations
final=json.loads((p.OUT/'v2-final-check-after-completion.json').read_text())
assert final['returncode']==0 and final['result']['status']=='current'
assert all(final['result'][k]==[] for k in ['additions','adoptions','updates','deletions','conflicts'])
preservation={'status':'passed','net_source_changes':68,'unselected_source_differences':[],
              'protected_root_skill_role_governance_registry_files':len(protected),
              'protected_differences':[],'preserved_root_updater_sha256':p.sha(p.ROOT/'tools/template_update.py'),
              'template_checked_file_count':len(template),'template_changes':template_changes,
              'template_differences_outside_exact_owner_preview':[],
              'unmanaged_template_files_in_comparable_inventory_preserved':True,
              'full_final_template_inventory_includes_transient_files':True,
              'prior_template_comparison_excludes':['.DS_Store','__pycache__','*.pyc'],
              'real_product_files':'Independent root-host check pending; worker operated only on registered Template and its disposable fixture.',
              'owner_state':ref(state_path),
              'existing_watcher':'watcher.json advanced autonomously; no worker service or watcher-setting changes.'}
p.save('v2-preservation.json',preservation)

evidence_names=['before.json','source-copy.json','proposed-check.json','apply.json','after-check.json',
 'live-owner-stop-v1.json','root-tool-rollback-v1.json','v2-compatibility-check.json','v2-reviewed-preview.json',
 'v2-apply.json','v2-final-check.json','v2-final-check-after-completion.json','v2-template-tests.json',
 'v2-shipped-package-result.json','v2-fixture-distribution.json','v2-fixture-bindings.json',
 'v2-fixture-template-inventory.json','v2-fresh-role-catalog.json','v2-final-sources.json',
 'v2-live-owned-bindings.json','v2-prepared-binding-comparison.json','v2-full-live-template-inventory.json','v2-preservation.json',
 'publish.py','verify-v2.py','finalize-v2.py']
manifest={'schema_version':1,'assignment_id':'publication_worker_v1',
 'execution_id':'curator_supported_cd80544e','generation':2,
 'baseline_sha256':'cdc679ecfa198be9bf163ec30cf067bd041a47a6d37ab0a8288bd582d626519f',
 'status':'published_and_verified_with_preserved_root_owner','final_source_inventory':ref(spec),
 'selected_candidate_paths':89,'preserved_root_owner_paths':1,'net_source_copies':68,
 'root_owner_exception':expected['exception'],'template_owner_result':'applied',
 'template_final_check':'current','live_managed_bindings':len(binding_rows),
 'full_live_template_inventory_entries':len(full_inventory),'prepared_bindings_revalidated':387,
 'fresh_shipped_fixture_bindings':406,'fresh_shipped_fixture_files':409,
 'checks':{'live_template_contract_tests':5,'fresh_setup':'completed','setup_contract':'governance-starter-v10',
           'static_ready':True,'curator_state':'installed_inactive','fresh_memory_capture':'on',
           'protected_root_files':len(protected),'unselected_source_differences':0,'unexpected_template_differences':0},
 'changed_files':[row for row in source_rows if row['changed']],
 'evidence':[ref(p.OUT/name) for name in evidence_names],
 'raw_owner_output':[ref(file) for file in sorted(p.OUT.glob('*.stdout'))]+[ref(file) for file in sorted(p.OUT.glob('*.stderr'))],
 'known_history':['The initial candidate root updater apply failed its existing owner contract; exact prior root updater restoration is retained in the rollback receipt.',
                  'One premature read-only final check reported the still-running apply lock. The original apply completed and a later check returned current.'],
 'verification_limits':['Fresh setup demonstrates shipped static capability, with Curator runtime and schedules inactive.',
                       'Prior native integration used the narrow demo/staged-note workload; full installed-assets checkout exceeded the supported128-descriptor snapshot bound.',
                       'The optional memory backend remained disabled; no optional indexing readiness is claimed.',
                       'Ordinary Task schema2/orchestration1 behavior is the validated native mode; no v2 callback or standing service is claimed.',
                       'No real project adoption, runtime registration refresh, environment/account change, or external Git publication was performed.',
                       'Root host independently checks real product preservation after this worker stops.'],
 'writes_stopped':True}
ref_out=p.save('manifest-v2.json',manifest)
print(json.dumps({'manifest':ref_out,'status':manifest['status'],'net_sources':68,'managed_bindings':len(binding_rows),'full_inventory_entries':len(full_inventory),'prepared_bindings':387,'checks':manifest['checks']}),flush=True)
