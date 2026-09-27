import os,json,hashlib,base64,tarfile,stat,io,sys
from pathlib import Path
ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
M=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
S=Path('/private/tmp/explorer-contracts-implement-g3')
E=ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests/process-catalog-correction'
import os,stat,json,hashlib
from pathlib import Path
root=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
q=root/'Verification/project-knowledge-explorer-first-release/qualification-tests'
def read(base,rel):
    parts=Path(rel).parts
    assert parts and not Path(rel).is_absolute() and all(x not in ('.','..','') for x in parts)
    fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for x in parts[:-1]:
            nxt=os.open(x,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
        f=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            s=os.fstat(f);assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
            chunks=[]
            while b:=os.read(f,1048576):chunks.append(b)
            raw=b''.join(chunks)
            sig=lambda v:(v.st_dev,v.st_ino,v.st_mode,v.st_nlink,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
            assert sig(os.fstat(f))==sig(s) and sig(os.stat(parts[-1],dir_fd=fd,follow_symlinks=False))==sig(s)
            return raw
        finally:os.close(f)
    finally:os.close(fd)

def ref(p):
 b=read(p.parent,p.name);return {'path':str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
receipt=read(M,'host-dependency-runtime-receipt.json');assert hashlib.sha256(receipt).hexdigest()=='e377bb1b138589065fdfe133e94c437dc837623884080d007a664bf3ea692054'
r=json.loads(receipt);archive_by={a['name']:a for a in r['archives']}
lock=read(ROOT/'SKILLS-depo/ontology/explorer','package-lock.json')
assert hashlib.sha256(lock).hexdigest()=='c56e429ba8b70fe0e56ab5f879853f5267083eb7facbc0a6da36322b94afdbf9'
l=json.loads(lock);expected={};archives=[]
for package in r['installed_packages']:
 a=archive_by[package['name']];p=Path(a['archive']).resolve();raw=read(p.parent,p.name)
 assert len(raw)==a['archive_bytes'];integ='sha512-'+base64.b64encode(hashlib.sha512(raw).digest()).decode()
 assert integ==a['integrity']==l['packages']['node_modules/'+package['name']]['integrity']
 count=0
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf:
  seen=set()
  for member in tf.getmembers():
   parts=Path(member.name).parts;assert parts[0]=='package' and '..' not in parts
   if member.isdir():continue
   assert member.isfile() and member.name not in seen;seen.add(member.name)
   rel='node_modules/'+package['name']+'/'+str(Path(*parts[1:]))
   body=tf.extractfile(member).read();actual=read(S,rel);assert actual==body,rel
   assert rel not in expected;expected[rel]={'path':rel,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)};count+=1
 archives.append({**ref(p),'name':a['name'],'version':a['version'],'integrity':integ,'installed_files_equal':count})
actual_files=set();links=[]
for parent,dirs,files in os.walk(S/'node_modules',followlinks=False):
 for n in dirs:
  assert not (Path(parent)/n).is_symlink()
 for n in files:
  p=Path(parent)/n;rel=str(p.relative_to(S));s=p.lstat()
  if stat.S_ISLNK(s.st_mode):
   assert p.parent==S/'node_modules/.bin';target=p.resolve();assert target.is_relative_to(S/'node_modules')
   assert str(target.relative_to(S)) in expected
   links.append({'path':rel,'target':os.readlink(p),'resolved':str(target.relative_to(S))})
  else:actual_files.add(rel)
assert actual_files-set(expected)=={'node_modules/.package-lock.json'},sorted(actual_files-set(expected))
assert set(expected)<=actual_files
hidden=json.loads(read(S,'node_modules/.package-lock.json'))
assert hidden['lockfileVersion']==3
assert set(hidden['packages'])=={'node_modules/'+p['name'] for p in r['installed_packages']}
for name,data in hidden['packages'].items():
 for k in ('version','resolved','integrity'):assert data[k]==l['packages'][name][k]
assert {Path(x['path']).name for x in links}=={'nanoid','rolldown','tsc','vite'}
entries=sorted(expected.values(),key=lambda x:x['path']);parts=[]
for i in range(0,len(entries),400):
 p=E/('dependency-files-%02d.json'%(i//400));p.write_text(json.dumps({'root':str(S),'files':entries[i:i+400]},indent=2)+'\n');parts.append(ref(p))
tools=[]
for name in ('node','npm'):
 p=Path('/opt/homebrew/bin')/name;real=p.resolve();tools.append({'invocation':str(p),'resolved':ref(real)})
out={'producer':'/root/explorer_manager_g3/frontend_worker','status':'passed','scope':'Fresh read-only installed dependency/archive byte comparison; no dependency code, hooks or build executed by this check. Historical accepted host receipt supplies archive identity; exact current lock supplies SRI.','accepted_receipt':ref(M/'host-dependency-runtime-receipt.json'),'lock':ref(ROOT/'SKILLS-depo/ontology/explorer/package-lock.json'),'root':str(S),'installed_packages':len(archives),'installed_regular_files':len(entries),'archives':archives,'file_parts':parts,'bin_links':links,'hidden_install_lock':ref(S/'node_modules/.package-lock.json'),'tools':tools,'qualification':'Archive receipts are immutable artifact references; each later build must reverify all named live files, links, closure and tools before execution. This is dependency admission, not a production build or browser result.'}
p=E/'dependency-admission.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(ref(p)));print(json.dumps({'packages':len(archives),'files':len(entries),'parts':parts,'tools':tools},indent=2))
