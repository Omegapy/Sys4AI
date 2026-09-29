"""Apply the exact reviewed Project app manifest and public guard repair."""
from pathlib import Path
import json,hashlib,sys,os,tempfile,stat
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
encode=lambda x:(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
manifest=json.loads((OUT/'root-adoption-manifest.json').read_bytes())
preview=json.loads((OUT/'guard-repair-preview.json').read_bytes())
for row in manifest['files']:
 source=ROOT/row['source'] if row['source'] else None;target=ROOT/row['destination']
 if source and sha(source.read_bytes())!=row['source_sha256']:raise RuntimeError('reviewed source changed: '+row['source'])
 if (sha(target.read_bytes()) if target.exists() else None) not in {row['expected_destination_sha256'],row['source_sha256']}:
  raise RuntimeError('reviewed target changed: '+row['destination'])
now=datetime.now(timezone.utc);changes=preview['payload']['changes']
grant={'schema_version':1,'project_id':'sys4ai-depot','actor_id':'/root','actor_kind':'director','operation':'guard-repair','preview_sha256':preview['preview_sha256'],'config_sha256':sha((ROOT/'ontology.yaml').read_bytes()),'scope':[r['path'] for r in changes],'reviewed_records':[{k:r[k] for k in ('path','sha256','expected_sha256')} for r in changes],'native_receipt':json.loads((OUT/'native-adoption-observation.json').read_bytes()),'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=4)).isoformat(),'task':None}
(OUT/'guard-repair-grant.json').write_bytes(encode(grant))
sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
import ontology_guard_setup as guard
receipt=guard.apply(ROOT,preview=preview,grant=grant)
(OUT/'guard-repair-result.json').write_bytes(encode(receipt))
for row in manifest['files']:
 target=ROOT/row['destination'];current=target.read_bytes() if target.exists() else None
 if (sha(current) if current is not None else None)==row['source_sha256']:continue
 if (sha(current) if current is not None else None)!=row['expected_destination_sha256']:raise RuntimeError('destination changed before write')
 if row['source'] is None:
  target.unlink();continue
 source=ROOT/row['source'];raw=source.read_bytes()
 if sha(raw)!=row['source_sha256']:raise RuntimeError('source changed before write')
 target.parent.mkdir(parents=True,exist_ok=True)
 mode=stat.S_IMODE(target.stat().st_mode) if target.exists() else row['mode']
 fd,name=tempfile.mkstemp(prefix='.project-app-adoption-',dir=target.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno());os.fchmod(f.fileno(),mode)
  if (sha(target.read_bytes()) if target.exists() else None)!=row['expected_destination_sha256']:raise RuntimeError('destination changed during staging')
  if current is None:os.link(name,target,follow_symlinks=False)
  else:os.replace(name,target)
 finally:
  Path(name).unlink(missing_ok=True)
for row in manifest['files']:
 target=ROOT/row['destination']
 if (sha(target.read_bytes()) if target.exists() else None)!=row['source_sha256']:raise RuntimeError('postimage differs')
manifest.update(status='applied-verified',guard_receipt='Verification/shared-project-app/guard-repair-result.json',verified_at=datetime.now(timezone.utc).isoformat())
(OUT/'root-adoption.json').write_bytes(encode(manifest))
print(json.dumps({'status':manifest['status'],'files':len(manifest['files']),'guard_status':receipt.get('status')}))
