"""Build in disposable staging; transfer exact owned runtime assets manifest-last."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[5]
SOURCE=ROOT/'SKILLS-depo/ontology/explorer'
EVIDENCE=ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests'
DEPS=Path('/private/tmp/explorer-contracts-implement-g3/node_modules')
# Validate the authored input tree before copying. Tooling dependency links
# are treated separately below and never confer permission on product inputs.
def regular_nofollow(file):
 import stat
 file=file.absolute();fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in file.parts[1:-1]:
   nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
  handle=os.open(file.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
  try:
   st=os.fstat(handle);assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
   with os.fdopen(os.dup(handle),'rb') as stream:raw=stream.read(8388609)
   assert len(raw)==st.st_size and len(raw)<=8388608
   return raw
  finally:os.close(handle)
 finally:os.close(fd)
for folder in [SOURCE/'src',SOURCE/'scripts']:
 for member in folder.rglob('*'):
  if member.is_dir():assert not member.is_symlink()
  else:regular_nofollow(member)
for name in ['index.html','package.json','package-lock.json','THIRD_PARTY_NOTICES.md','BUILD.md','vite.config.ts','tsconfig.json']:
 regular_nofollow(SOURCE/name)
STAGE=Path(tempfile.mkdtemp(prefix='explorer-frontend-build-',dir='/private/tmp'))
work=STAGE/'SKILLS-depo/ontology/explorer';work.mkdir(parents=True)
for name in ['src','scripts']:shutil.copytree(SOURCE/name,work/name)
for name in ['index.html','package.json','package-lock.json','THIRD_PARTY_NOTICES.md','BUILD.md','vite.config.ts','tsconfig.json']:shutil.copy2(SOURCE/name,work/name)
(work.parent/'scripts').mkdir(exist_ok=True)
shutil.copy2(ROOT/'SKILLS-depo/ontology/scripts/ontology_explorer_assets.py',work.parent/'scripts/ontology_explorer_assets.py')
schema=STAGE/'ONTOLOGY-depo/schema';schema.mkdir(parents=True);shutil.copy2(ROOT/'ONTOLOGY-depo/schema/explorer-v1.json',schema/'explorer-v1.json')
for link in DEPS.rglob('*'):
 if link.is_symlink():assert link.resolve().is_relative_to(DEPS.resolve())
shutil.copytree(DEPS,work/'node_modules',symlinks=True)
def inv(folder):return [(str(p.relative_to(folder)),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(folder.rglob('*')) if p.is_file()]
assert inv(DEPS)==inv(work/'node_modules')
checks=[]
env=dict(os.environ,EXPLORER_PYTHON=str(ROOT/'.venv/bin/python'))
for command in [['npm','run','build'],['npm','run','package:runtime']]:
 result=subprocess.run(command,cwd=work,env=env,capture_output=True,text=True);checks.append({'command':command,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
 if result.returncode:break
sequence=len(list(EVIDENCE.glob('build-[0-9][0-9].json')))+1
receipt={'stage':str(STAGE),'checks':checks,'status':'passed' if all(x['exit_code']==0 for x in checks) and len(checks)==2 else 'failed'}
if receipt['status']=='passed':
 generated=json.loads((work/'assets/manifest.json').read_text())
 record=json.loads((work/'dist/.explorer-build.json').read_text())
 for row in record['inputs']['record']['files']:
  relative=row['path']
  source=(ROOT/'ONTOLOGY-depo/schema/explorer-v1.json' if relative.startswith('$schema/') else ROOT/'SKILLS-depo/ontology/scripts/ontology_explorer_assets.py' if relative.startswith('$tooling/') else SOURCE/relative)
  assert hashlib.sha256(regular_nofollow(source)).hexdigest()==row['sha256'],'live build source changed'
 publisher=regular_nofollow(SOURCE/'scripts/package-runtime.mjs')
 assert hashlib.sha256(publisher).hexdigest()=='7346ed8159e14f3457a2d6315fe40ceda0fbc7af2082efd9b605ff1cc1ae3147'
 body=publisher.decode().split('const PUBLISH_PYTHON = String.raw`',1)[1].split('`;',1)[0]
 helper=ROOT/'SKILLS-depo/ontology/scripts/ontology_explorer_assets.py'
 payload={'stage':str(work/'assets'),'destination':str(SOURCE/'assets'),'helper':str(helper),'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'schema':record['inputs']['schema_sha256'],'old_manifest_sha256':hashlib.sha256(regular_nofollow(SOURCE/'assets/manifest.json')).hexdigest()}
 publication=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B','-c',body],input=json.dumps(payload),capture_output=True,text=True,timeout=30)
 checks.append({'command':['reviewed publisher fixed Python body','source asset transfer'],'exit_code':publication.returncode,'stdout':publication.stdout,'stderr':publication.stderr})
 if publication.returncode:receipt['status']='failed'
 else:
  shutil.copy2(work/'dist/.explorer-build.json',EVIDENCE/f'build-inputs-{sequence:02}.json')
  receipt['manifest']=generated
(EVIDENCE/f'build-{sequence:02}.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'stage':str(STAGE),'receipt':str(EVIDENCE/f'build-{sequence:02}.json'),'checks':checks if receipt['status']=='failed' else [{'command':x['command'],'exit_code':x['exit_code']} for x in checks]},indent=2))
raise SystemExit(0 if receipt['status']=='passed' else 1)
