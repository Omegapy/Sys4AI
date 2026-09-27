from pathlib import Path
import sys,json,hashlib,copy,shutil
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
import ontology_guard_setup as guard
from ontology_core import canonical_bytes
sha=lambda raw:hashlib.sha256(raw).hexdigest()
MAIN='.agents/skills/init-new-project/scripts/init_new_project.py'
manifest=json.loads((OUT/'initializer/root-initializer-adoption-manifest.json').read_text())
def save(name,v): (OUT/name).write_bytes(canonical_bytes(v))
def prepare():
 for row in manifest['files']:
  source=Path(row['source']);dest=Path(row['destination'])
  assert sha(source.read_bytes())==row['source_sha256'],source
  assert (sha(dest.read_bytes()) if dest.exists() else None)==row['expected_destination_sha256'],dest
 for p in (ROOT/'.agents/skills/init-new-project').rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:
   dest=OUT/'root-retained'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 cfg=json.loads((ROOT/'ontology-advanced.yaml').read_bytes());profile=cfg['profiles']['guards'];adapters=json.loads((ROOT/profile['adapters']['path']).read_bytes());bootstrap=json.loads((ROOT/profile['bootstrap']['path']).read_bytes())
 op='ONTGUARD-collaboration-initializer-20260927';changes=[]
 def change(path,content):
  raw=content.encode() if isinstance(content,str) else canonical_bytes(content);p=ROOT/path
  changes.append(dict(path=path,expected_sha256=sha(p.read_bytes()) if p.exists() else None,sha256=sha(raw),content=raw.decode()))
 change(MAIN,(ROOT/'SKILLS-depo/init-new-project/scripts/init_new_project.py').read_text())
 for row in adapters['families']['setup']:
  if row['path']==MAIN: row['sha256']=sha((ROOT/'SKILLS-depo/init-new-project/scripts/init_new_project.py').read_bytes())
 adapter_path='control_records/ontology/guard-bootstrap/'+op+'-adapters.json';change(adapter_path,adapters)
 binding={'path':adapter_path,'sha256':sha(canonical_bytes(adapters))}
 bootstrap.update(operation_id=op,adapters=binding,repair_basis='Exact current Source initializer adoption required for automatic complete collaboration setup. Existing all-family declarations, engine, contracts, backends, governance and prior verification remain retained; prior campaign is historical, no new full guard certification is claimed.')
 bootstrap_path='control_records/ontology/guard-bootstrap/'+op+'-bootstrap.json';change(bootstrap_path,bootstrap)
 cfg['profiles']['guards'].update(adapters=binding,bootstrap={'path':bootstrap_path,'sha256':sha(canonical_bytes(bootstrap))});change('ontology-advanced.yaml',cfg)
 save('guard-repair-input.json',dict(operation_id=op,changes=changes))
 preview=guard.preview_repair(ROOT,operation_id=op,changes=changes);save('guard-repair-preview.json',preview)
 print(json.dumps({'status':'reviewed-preview','files':len(manifest['files']),'guard_changes':[r['path'] for r in changes],'preview_sha256':preview['preview_sha256']}))
def apply():
 preview=json.loads((OUT/'guard-repair-preview.json').read_bytes());grant=json.loads((OUT/'guard-repair-grant.json').read_bytes())
 result=guard.apply(ROOT,preview=preview,grant=grant);save('guard-repair-result.json',result)
 for row in manifest['files']:
  source=Path(row['source']);dest=Path(row['destination']);assert sha(source.read_bytes())==row['source_sha256']
  if dest.relative_to(ROOT).as_posix()!=MAIN:
   assert (sha(dest.read_bytes()) if dest.exists() else None)==row['expected_destination_sha256'],dest
   dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
  assert sha(dest.read_bytes())==row['source_sha256']
 final=copy.deepcopy(manifest);final['status']='applied-verified';final['guard_receipt']='Verification/collaboration-enablement-20260927/guard-repair-result.json';save('root-initializer-adoption.json',final)
 print(json.dumps({'status':final['status'],'files':len(final['files']),'guard_status':result.get('status')}))
if __name__=='__main__': {'prepare':prepare,'apply':apply}[sys.argv[1]]()
