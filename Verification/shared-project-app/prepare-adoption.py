"""Prepare exact package and guard adoption manifests without publishing them."""
from pathlib import Path
import ast,json,hashlib,stat,os,sys,importlib.util,shutil
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
encode=lambda x:(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
spec=importlib.util.spec_from_file_location('app_template_update',ROOT/'tools/template_update.py')
u=importlib.util.module_from_spec(spec);sys.modules[spec.name]=u;spec.loader.exec_module(u)
rows=[];preserved_differences=[]
for package in ['ontology','init-new-project']:
 src=ROOT/'SKILLS-depo'/package
 before=json.loads((OUT/'manifests'/('installed-'+('ontology' if package=='ontology' else 'initializer')+'-before.json')).read_text())
 source_before=json.loads((OUT/'manifests'/('source-'+('ontology' if package=='ontology' else 'initializer')+'-before.json')).read_text())
 for directory,dirs,files in os.walk(src):
  dirs[:]=[n for n in dirs if not u.excluded(str((Path(directory)/n).relative_to(ROOT)))]
  for n in files:
   source=Path(directory)/n;logical=str(source.relative_to(ROOT))
   if u.excluded(logical):continue
   target=ROOT/'.agents/skills'/package/source.relative_to(src);dest=str(target.relative_to(ROOT))
   raw=source.read_bytes();present=target.read_bytes() if target.exists() else None
   expected=before.get(dest,{}).get('sha256')
   if (sha(present) if present is not None else None)!=expected:raise RuntimeError('destination changed since baseline: '+dest)
   if present!=raw and source_before.get(logical,{}).get('sha256')==sha(raw):
    preserved_differences.append(dest)
    continue
   if present!=raw:
    rows.append({'source':logical,'destination':dest,'source_sha256':sha(raw),'expected_destination_sha256':expected,'mode':stat.S_IMODE(source.stat().st_mode)})
 # Runtime publisher may retire only old manifest-owned assets; preserve extras.
 if package=='ontology':
  old=json.loads((ROOT/'.agents/skills/ontology/explorer/assets/manifest.json').read_text())
  new=json.loads((src/'explorer/assets/manifest.json').read_text())
  for name in {v['path'] for v in old['assets']}-{v['path'] for v in new['assets']}:
   dest='.agents/skills/ontology/explorer/assets/'+name;target=ROOT/dest
   expected=before[dest]['sha256']
   if sha(target.read_bytes())!=expected:raise RuntimeError('obsolete asset customized')
   rows.append({'source':None,'destination':dest,'source_sha256':None,'expected_destination_sha256':expected,'mode':stat.S_IMODE(target.stat().st_mode)})
for source,dest in [('ONTOLOGY-depo/schema/project-app-v1.json','reference-assets/ONTOLOGY-depo/schema/project-app-v1.json'),('Verification/shared-project-app/root-project-app.json','project-app.json'),('SKILLS-depo/ontology/assets/project-app/Launch Project.command','Launch Project.command'),('SKILLS-depo/ontology/assets/project-app/Project App Setup.html','Project App Setup.html')]:
 s=ROOT/source;t=ROOT/dest
 if t.exists():raise RuntimeError('new root adoption destination already exists: '+dest)
 rows.append({'source':source,'destination':dest,'source_sha256':sha(s.read_bytes()),'expected_destination_sha256':None,'mode':0o755 if dest=='Launch Project.command' else 0o644})
for row in rows:
 target=ROOT/row['destination']
 if target.exists():
  p=OUT/'preimages'/row['destination'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,p)
(OUT/'root-adoption-manifest.json').write_bytes(encode({'status':'reviewed-exact-manifest','plan_id':'PLAN-20260929-F690CD02','revision':3,'files':rows,'preserved_preexisting_source_installed_differences':preserved_differences}))
sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
import ontology_guard_setup as guard
cfg=json.loads((ROOT/'ontology-advanced.yaml').read_text());profile=cfg['profiles']['guards']
adapters=json.loads((ROOT/profile['adapters']['path']).read_text());bootstrap=json.loads((ROOT/profile['bootstrap']['path']).read_text())
operation='ONTGUARD-project-app-20260929';changes=[]
def change(path,value):
 raw=value.encode() if isinstance(value,str) else encode(value);p=ROOT/path
 changes.append({'path':path,'expected_sha256':sha(p.read_bytes()) if p.exists() else None,'sha256':sha(raw),'content':raw.decode()})
main='.agents/skills/init-new-project/scripts/init_new_project.py'
change(main,(ROOT/'SKILLS-depo/init-new-project/scripts/init_new_project.py').read_text())
for entry in adapters['families']['setup']:
 if entry['path']==main:entry['sha256']=changes[0]['sha256']
adapter_path='control_records/ontology/guard-bootstrap/'+operation+'-adapters.json';change(adapter_path,adapters)
binding={'path':adapter_path,'sha256':sha(encode(adapters))}
bootstrap.update(operation_id=operation,adapters=binding,repair_basis='Exact Project app initializer adoption; preserves all-family guard semantics, backend profiles and prior evidence. Current focused delivery checks are distinct from historical guard qualification.')
bootstrap_path='control_records/ontology/guard-bootstrap/'+operation+'-bootstrap.json';change(bootstrap_path,bootstrap)
cfg['profiles']['guards'].update(adapters=binding,bootstrap={'path':bootstrap_path,'sha256':sha(encode(bootstrap))});change('ontology-advanced.yaml',cfg)
preview=guard.preview_repair(ROOT,operation_id=operation,changes=changes)
(OUT/'guard-repair-preview.json').write_bytes(encode(preview))
print(json.dumps({'adoption_files':len(rows),'guard_preview':preview['preview_sha256'],'guard_changes':[r['path'] for r in changes]}))
