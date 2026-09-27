"""Read-only current product/context audit; writes only its bounded receipt."""
from pathlib import Path
import hashlib,json,os,stat,subprocess
ROOT=Path(__file__).resolve().parents[5]
BASE=ROOT/'SKILLS-depo/ontology/explorer'
E=ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests'
def read(file):
 file=file.absolute();parent=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in file.parts[1:-1]:
   child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent);os.close(parent);parent=child
  fd=os.open(file.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
  try:
   meta=os.fstat(fd);assert stat.S_ISREG(meta.st_mode) and meta.st_nlink==1
   with os.fdopen(os.dup(fd),'rb') as stream:data=stream.read(8388609)
   assert len(data)==meta.st_size and len(data)<=8388608
   return data
  finally:os.close(fd)
 finally:os.close(parent)
def record(path):
 data=read(path);return {'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
initial=json.loads(read(E/'initial-context.json'));context=[]
for expected in initial['context']:
 actual=record(ROOT/expected['path']);assert actual==expected,expected['path'];context.append(actual)
manifest=json.loads(read(BASE/'assets/manifest.json'));members=[record(BASE/'assets/manifest.json')]
for row in manifest['assets']:
 actual=record(BASE/'assets'/row['path']);assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'];members.append(actual)
assert {str(p.relative_to(BASE/'assets')) for p in (BASE/'assets').rglob('*') if p.is_file()}=={'manifest.json'}|{x['path'] for x in manifest['assets']}
for folder in [BASE/'src',BASE/'assets',BASE/'tests/frontend']:
 for p in folder.rglob('*'):
  if p.is_dir():assert not p.is_symlink()
  else:read(p)
sources=[record(BASE/'index.html')]+[record(p) for p in sorted((BASE/'src').rglob('*')) if p.is_file()]
fetch_owners=[str(p.relative_to(BASE)) for p in (BASE/'src').rglob('*.ts') if 'fetch(' in read(p).decode()]
assert fetch_owners==['src/api.ts'],fetch_owners
for p in (BASE/'src').rglob('*.ts'):
 if p.name=='contracts.ts':continue
 text=read(p).decode();assert '.innerHTML' not in text and 'eval(' not in text and 'new Function' not in text,str(p)
check=subprocess.run(['git','diff','--check','--','SKILLS-depo/ontology/explorer','Verification/project-knowledge-explorer-first-release/frontend-tests'],cwd=ROOT,capture_output=True,text=True)
assert check.returncode==0,check.stdout+check.stderr
receipt={'status':'passed','qualification':'Current no-follow regular single-link/hash/size audit and targeted source inspection. Does not replace browser, service, assistive-technology or human checks.','initial_context_files':context,'current_source_files':sources,'runtime_manifest_and_members':members,'build_id':manifest['build_id'],'checks':['37 unchanged frozen bound inputs','exact runtime closed inventory and member hashes/sizes','all source/runtime/frontend-test files regular single-link with no-follow parent reads','only api.ts owns fetch','no innerHTML/eval/dynamic function in authored consuming UI','scoped git diff --check'],'runtime_member_document_cap':'The434861-byte pinned Cytoscape runtime is a product asset governed by its manifest and8MiB package limit; evidence documents remain<=250000bytes.'}
raw=json.dumps(receipt,indent=2)+'\n';assert len(raw.encode())<=250000
(E/'current-audit.json').write_text(raw)
print(json.dumps({'status':'passed','source_files':len(sources),'runtime_files':len(members),'bound_context_files':len(context),'build_id':manifest['build_id']}))
