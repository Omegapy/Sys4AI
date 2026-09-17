from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;HANDOFF=OUT/'root-handoff';HANDOFF.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
rows=[]
for old in json.loads((OUT/'preimages.json').read_text()):
 src=ROOT/old['source'];name=old['source'].replace('SKILLS-depo/ontology/','.agents/skills/ontology/');dst=ROOT/name
 assert sha(dst)==old['root_sha256']
 rows.append({'source':old['source'],'path':name,'expected_sha256':sha(dst),'sha256':sha(src),'bytes':src.stat().st_size,'operation':'exact-local-source-adoption','compatibility':'Exact root predecessor equals retained source preimage; only reviewed correction delta.'})
cfg=json.loads((ROOT/'ontology-advanced.yaml').read_text());guards=cfg['profiles']['guards'];adapters=json.loads((ROOT/guards['adapters']['path']).read_text())
bound={r['path'] for family in adapters['families'].values() for r in family}
assert not ({r['path'] for r in rows}&bound)
save(HANDOFF/'source-adoption-manifest.json',{'schema_version':2,'status':'prepared_not_applied','files':rows,'no_guard_adapter_changes':True,'root_initializer':'preserve current v9 package; reusable v12 pin files are not root adoption targets','recertification_required':True})
save(HANDOFF/'guard-repair-selection.json',{'schema_version':1,'status':'not_required','reason':'None of the six selected targets is a bound owning adapter, guard engine, guard setup helper, action contract or configuration. Existing adapter/bootstrap bindings remain exact. Re-certify the existing standards worker after the two fingerprinted helper changes.','changed_bound_adapters':[],'current_guards':guards,'current_advanced_config_sha256':sha(ROOT/'ontology-advanced.yaml'),'limits':cfg['limits']})
# Verify the exact current inventory delta and its single helper pin change.
before=json.loads((OUT/'preimages/SKILLS-depo/init-new-project/assets/static-capability-v1.json').read_text());after=json.loads((ROOT/'SKILLS-depo/init-new-project/assets/static-capability-v1.json').read_text())
changes=json.loads((OUT/'inventory-pin-delta.json').read_text())
for row in changes:before[row['group']][row['path']]=row['after']
assert before==after
old=(OUT/'preimages/SKILLS-depo/init-new-project/scripts/init_static_health.py').read_text();new=(ROOT/'SKILLS-depo/init-new-project/scripts/init_static_health.py').read_text()
assert re.sub(r'^INVENTORY_SHA256 = "[a-f0-9]+"','INVENTORY_SHA256 = "PIN"',old,flags=re.M)==re.sub(r'^INVENTORY_SHA256 = "[a-f0-9]+"','INVENTORY_SHA256 = "PIN"',new,flags=re.M)
# Check neutral Template selections and exact corrected files.
template=ROOT/'Projects/Sys4AI-Template-Project';oc=json.loads((template/'ontology.yaml').read_text());cc=json.loads((template/'curator.yaml').read_text());sc=json.loads((template/'curator-session.yaml').read_text())
assert all(oc['project'][k] is None for k in ('id','name','namespace','purpose')) and oc['publication']=={'enabled':False,'binding':None}
assert all(v is None for v in cc['project'].values()) and not sc['enabled'] and sc['project_id'] is None
assert not (template/'project.json').exists()
assert all(not json.loads((template/p).read_text())['@graph'] for p in oc['project_files']+oc['binding_files'])
all_sources=[r['source'] for r in rows]+['SKILLS-depo/init-new-project/assets/static-capability-v1.json','SKILLS-depo/init-new-project/scripts/init_static_health.py']+['SKILLS-depo/ontology/tests/'+n for n in ('test_inference_diagnostic.py','test_shacl_grouping.py','test_named_shacl_lists.py')]
assert all(sha(ROOT/p)==sha(template/p.replace('SKILLS-depo/','.agents/skills/')) for p in all_sources)
save(OUT/'template-neutrality-final.json',{'status':'neutral','exact_corrected_source_files':all_sources,'project_identity':oc['project'],'curator_identity':cc['project'],'session_enabled':sc['enabled'],'project_record_absent':True,'project_and_binding_graphs_empty':True,'current_inventory_only_delta_verified':True})
# The complete corrected runtime helpers used in actual confined root tests match source.
observed=json.loads((OUT/'root-copy-shacl-final.json').read_text())['context']['helpers']
assert all(observed[Path(r['source']).name]==r['sha256'] for r in rows if '/scripts/' in r['source'])
original=json.loads((OUT.parent/'source-freeze-manifest.json').read_text())
found=[]
def walk(v):
 if isinstance(v,dict):
  if v.get('path')=='SKILLS-depo/init-new-project/assets/static-capability-v11.json':found.append(v)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(original)
assert len(found)==1 and sha(ROOT/found[0]['path'])==found[0]['sha256']
save(OUT/'preservation-final.json',{'root_targets_unchanged':[{k:r[k] for k in ('path','expected_sha256')} for r in rows],'runtime_helpers_match_actual_test':True,'historical_v11_unchanged':found[0],'v1_result_sha256':sha(OUT.parent/'result.md'),'v1_freeze_sha256':sha(OUT.parent/'source-freeze-manifest.json')})
print('6 exact root targets; 11 corrected source files; neutral current Template; historical and root targets preserved')
