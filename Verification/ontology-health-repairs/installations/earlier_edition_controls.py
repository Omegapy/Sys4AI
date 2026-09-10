"""Delivered CLI recovery from a documented, reconstructed earlier-edition fixture."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone
from prepare_static import (REAL,OUT,ACTUAL_TEMPLATE,FIXTURES,TEMPLATE_REL,SKILL_REL,sha,tree,digest_tree,load_helper,run_cli,args,write_json)

source_before=tree(ACTUAL_TEMPLATE)
registry_before=(REAL/'depot/projects.json').read_bytes()
spec=importlib.util.spec_from_file_location('earlier_factory',REAL/'SKILLS-depo/init-new-project/tests/test_initializer.py')
factory=importlib.util.module_from_spec(spec);sys.modules[spec.name]=factory;spec.loader.exec_module(factory)
depot=factory.fixture_depot(FIXTURES/'earlier edition delivery')
template=depot/TEMPLATE_REL;shutil.rmtree(template);shutil.copytree(ACTUAL_TEMPLATE,template,symlinks=True)
assert tree(template)==source_before
h=load_helper(template/SKILL_REL);script=template/SKILL_REL/'scripts/init_new_project.py'
target=depot/'Projects/Earlier Edition'
identity={'schema_version':1,'project_id':'delivery-earlier','project_name':'Earlier Edition',
          'purpose':'Verify delivered governance capability in an isolated acceptance fixture.','relative_path':'Projects/Earlier Edition'}
# Match the delivered test_advanced_ontology_adoption.historical(edition=8)
# construction; this is fixture state, never an assertion of a prior real setup.
backup={name:(template/name).read_bytes() for name in ('ontology-advanced.yaml','tools/template_update.py',h.TEMPLATE_POLICY)}
(template/'ontology-advanced.yaml').unlink();(template/'tools/template_update.py').unlink()
policy=json.loads(backup[h.TEMPLATE_POLICY]);policy['starter_files']=sorted(h.required_starters('governance-starter-v8'));(template/h.TEMPLATE_POLICY).write_bytes(h.encoded(policy))
proposed,sources,original=h.source_snapshot(depot,template/SKILL_REL,identity,contract='governance-starter-v8')
for source in sources:
 name=source['destination'];source['adoption']='specialized' if name in h.SPECIALIZED_FILES and proposed[name]!=original.get(name) else 'adopted'
record={'schema_version':1,'setup_contract':'governance-starter-v8','status':'partial','mode':'create','operation_id':'project-setup-'+'8'*32,
        'identity':identity,'project_root':str(target),'sources':sources,'owned_files':{n:h.sha(raw) for n,raw in proposed.items()},'preserved_files':{},
        'preserved_licenses':{},'preserved_memory':{},'preserved_learning':{},'preserved_ontology':{},'recovery_before':{n:None for n in proposed},
        'completed_stages':[],'active_stage':'assets','checks':[],'created_at':datetime.now(timezone.utc).isoformat(),'git_setup':'separate'}
receipt=target/h.RECORD;receipt.parent.mkdir(parents=True);receipt.write_bytes(h.encoded(record))
write_json(OUT/'earlier-fixture-provenance.json',{'method':'Reconstructed partial v8 state using the actual delivered helper source_snapshot and delivered historical fixture recipe.',
 'recipe_source':'Projects/Sys4AI-Template-Project/.agents/skills/init-new-project/tests/test_advanced_ontology_adoption.py',
 'recipe_sha256':sha((ACTUAL_TEMPLATE/'.agents/skills/init-new-project/tests/test_advanced_ontology_adoption.py').read_bytes()),
 'no_actual_historical_operation_claim':True,'original_actual_template_sha256':digest_tree(source_before),'seeded_fixture_receipt_sha256':sha(receipt.read_bytes()),
 'fixture_depot':str(depot),'project':str(target),'contract':'governance-starter-v8'})
command=args('create',target,'delivery-earlier','Earlier Edition')
# Changed selected Template bytes must refuse exact pending replay.
soul=template/'SOUL.md';soul_original=soul.read_bytes();soul.write_bytes(soul_original+b'\nControlled later fixture source change.\n')
before=tree(target,mtimes=True)
changed,_=run_cli('earlier-source-conflict',script,command,depot,expected=2)
assert tree(target,mtimes=True)==before
soul.write_bytes(soul_original)
# Unknown project-owned bytes cannot be overwritten to complete pending setup.
conflict=target/'AGENTS.md';conflict.write_text('Concurrent fixture-owned governance; preserve exact bytes.\n')
conflict_raw=conflict.read_bytes();before_receipt=receipt.read_bytes()
conflicting,_=run_cli('earlier-target-conflict',script,command,depot,expected=2)
assert conflict.read_bytes()==conflict_raw
# Remove only this fixture-injected unknown file to restore its documented absence.
conflict.unlink()
first,_=run_cli('earlier-exact-recovery',script,command,depot)
assert first['setup_contract']=='governance-starter-v8' and first['sources']==sources
assert first['operation_id']==record['operation_id'] and not (target/'ontology-advanced.yaml').exists()
first_immutable={k:first.get(k) for k in h.BASE_IMMUTABLE}
# Restore the complete final delivered Template byte-for-byte before adoption.
for name,raw in backup.items():
 p=template/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
assert tree(template)==source_before
repeated,_=run_cli('earlier-ordinary-rerun',script,command,depot)
assert {k:repeated.get(k) for k in h.BASE_IMMUTABLE}==first_immutable
assert not (target/'ontology-advanced.yaml').exists()
# Preserve explicit existing choices when advanced capability is later selected.
memory=target/'memory.yaml';cfg=json.loads(memory.read_text());cfg['integration']['automatic_capture']=False;memory.write_bytes(h.encoded(cfg))
protected={n:(target/n).read_bytes() for n in ('memory.yaml','ontology.yaml','SOUL.md','AGENTS.md','ROLE.md','LICENSE','LICENSE-CODE','LICENSE-DOCS')}
adopt_args=args('prepare-existing',target,'delivery-earlier','Earlier Edition')+['--adopt-module','ontology-advanced']
adopted,_=run_cli('earlier-selected-advanced-adoption',script,adopt_args,depot)
assert {k:adopted.get(k) for k in h.BASE_IMMUTABLE}==first_immutable
assert all((target/n).read_bytes()==raw for n,raw in protected.items())
operation=adopted['module_adoptions'][-1]
assert operation['module_id']=='ontology-advanced' and operation['status']=='completed'
assert operation['capabilities']['installed'] is True
assert not any(v['enabled'] for v in json.loads((target/'ontology-advanced.yaml').read_text())['profiles'].values())
reg=(depot/'depot/projects.json').read_bytes()
retry,_=run_cli('earlier-selected-adoption-rerun',script,adopt_args,depot)
assert len(retry['module_adoptions'])==len(adopted['module_adoptions'])==1
assert retry['module_adoptions'][0]['operation_id']==operation['operation_id']
assert (depot/'depot/projects.json').read_bytes()==reg
assert all((target/n).read_bytes()==raw for n,raw in protected.items())
assert tree(ACTUAL_TEMPLATE)==source_before
assert (REAL/'depot/projects.json').read_bytes()==registry_before
summary={'scenario':'reconstructed-v8-delivered-cli-recovery-and-selected-adoption','status':'passed','fixture_depot':str(depot),'project_root':str(target),
 'construction':'documented existing delivered earlier-edition fixture recipe; no claim of a real historical setup',
 'source_conflict':{'exit':2,'destination_bytes_mtimes_preserved':True},'target_conflict':{'exit':2,'unknown_bytes_preserved':True},
 'exact_recovery':{'exit':0,'same_operation':True,'same_sources':True,'setup_contract':'governance-starter-v8'},
 'ordinary_rerun':{'exit':0,'base_immutable_fields_preserved':True,'no_implicit_advanced_adoption':True},
 'selected_adoption':{'exit':0,'base_contract_preserved':True,'base_immutable_fields_preserved':True,'protected_files_preserved':{n:sha(raw) for n,raw in protected.items()},
                      'new_advanced':operation['new_advanced'],'capability':operation['capabilities'],'module_operation_id':operation['operation_id']},
 'selected_rerun':{'exit':0,'module_operations':1,'no_duplicate_registration':True,'same_module_operation':True},
 'runtime':'not-exercised','actual_template_unchanged':True,'real_registry_unchanged':True,
 'commands':['commands/'+n+'/receipt.json' for n in ('earlier-source-conflict','earlier-target-conflict','earlier-exact-recovery','earlier-ordinary-rerun','earlier-selected-advanced-adoption','earlier-selected-adoption-rerun')]}
write_json(OUT/'earlier-edition-result.json',summary)
matrix=json.loads((OUT/'recovery-matrix.json').read_text());matrix['status']='static_delivered_recovery_matrix_complete_runtime_unexercised';matrix['cases'].append(summary);matrix.pop('earlier_edition_and_asset_conflicts',None);write_json(OUT/'recovery-matrix.json',matrix)
print(json.dumps({'status':'earlier-edition-controls-passed','project':str(target),'operation_id':operation['operation_id']}),flush=True)
