"""Reproduce accepted build bytes in one fresh owned workspace only."""
from pathlib import Path
import base64,hashlib,json,os,stat,subprocess,sys,tarfile,io,time
ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI');Q=Path(__file__).resolve().parent
M=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
NUMBER='01'
STAGE=Path(json.loads((Q/'build-01.json').read_text())['stage']);APP=STAGE/'SKILLS-depo/ontology/explorer'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(base,relative):
    parts=Path(relative).parts;assert parts and not Path(relative).is_absolute() and all(p not in ('..','.','') for p in parts)
    fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
        f=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        try:
            st=os.fstat(f);assert stat.S_ISREG(st.st_mode) and st.st_nlink==1;chunks=[]
            while b:=os.read(f,1024*1024):chunks.append(b)
            signature=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            assert signature(st)==signature(os.fstat(f))==signature(os.stat(parts[-1],dir_fd=fd,follow_symlinks=False))
            return b''.join(chunks),stat.S_IMODE(st.st_mode)
        finally:os.close(f)
    finally:os.close(fd)
def bound(path,digest):
    b,_=read(path.parent,path.name);assert sha(b)==digest,str(path);return b
def write(p,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def dependency_inputs(copy=False):
    admission=json.loads(bound(M/'qualification-dependency-admission.json','2a59ce84637e601cc4d835c6b8cf51d34930f3af483e1e995008f645677b805c'))
    base=Path(admission['root']);expected={}
    for part in admission['file_parts']:
        obj=json.loads(bound(ROOT/part['path'],part['sha256']));assert obj['root']==str(base)
        for row in obj['files']:assert row['path'] not in expected;expected[row['path']]=row
    assert len(expected)==1001
    for archive in admission['archives']:
        p=Path(archive['path']);b=bound(p,archive['sha256']);assert 'sha512-'+base64.b64encode(hashlib.sha512(b).digest()).decode()==archive['integrity']
        with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as tar:
            for item in tar.getmembers():
                if item.isdir():continue
                assert item.isfile() and Path(item.name).parts[0]=='package' and '..' not in Path(item.name).parts
                rel='node_modules/'+archive['name']+'/'+str(Path(*Path(item.name).parts[1:]));content=tar.extractfile(item).read();assert sha(content)==expected[rel]['sha256']
    for rel,row in expected.items():
        b,mode=read(base,rel);assert sha(b)==row['sha256'] and len(b)==row['bytes']
        if copy:
            p=APP/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);p.chmod(mode)
        else:assert read(APP,rel)[0]==b,rel
    hidden=admission['hidden_install_lock'];b=bound(Path(hidden['path']),hidden['sha256'])
    if copy:(APP/'node_modules/.package-lock.json').write_bytes(b)
    else:assert read(APP,'node_modules/.package-lock.json')[0]==b
    actual=set();observed_links={};links={x['path']:x for x in admission['bin_links']}
    for parent,dirs,files in os.walk(base/'node_modules',followlinks=False):
        assert all(not (Path(parent)/d).is_symlink() for d in dirs)
        for name in files:
            p=Path(parent)/name;rel=str(p.relative_to(base))
            if p.is_symlink():
                assert rel in links and os.readlink(p)==links[rel]['target'] and str(p.resolve().relative_to(base))==links[rel]['resolved']
                observed_links[rel]=os.readlink(p)
            else:actual.add(rel)
    assert actual==set(expected)|{'node_modules/.package-lock.json'}
    assert observed_links=={k:v['target'] for k,v in links.items()}
    if copy:
        for row in links.values():p=APP/row['path'];p.parent.mkdir(exist_ok=True);p.symlink_to(row['target'])
    else:
        for row in links.values():assert os.readlink(APP/row['path'])==row['target'] and str((APP/row['path']).resolve().relative_to(APP))==row['resolved']
        staged_files=set();staged_links={}
        for parent,dirs,names in os.walk(APP/'node_modules',followlinks=False):
            assert all(not (Path(parent)/name).is_symlink() for name in dirs)
            for name in names:
                p=Path(parent)/name;rel=str(p.relative_to(APP))
                if p.is_symlink():staged_links[rel]=os.readlink(p)
                else:staged_files.add(rel)
        assert staged_files==set(expected)|{'node_modules/.package-lock.json'}
        assert staged_links=={k:v['target'] for k,v in links.items()}
    tools=[]
    for row in admission['tools']:
        invoke=Path(row['invocation']);assert str(invoke.resolve())==row['resolved']['path'];bound(invoke.resolve(),row['resolved']['sha256'])
        r=subprocess.run([str(invoke),'--version'],capture_output=True,text=True,timeout=10,env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','npm_config_userconfig':str(STAGE/'npm-user.conf'),'npm_config_globalconfig':str(STAGE/'npm-global.conf')})
        assert r.returncode==0;tools.append({'invocation':str(invoke),'version':r.stdout.strip(),'resolved':row['resolved']})
    assert [x['version'] for x in tools]==['v25.9.0','11.12.1']
    return {'files':1001,'packages':19,'archives_sri_verified':19,'bin_links':list(links.values()),'tools':tools,'tree_closure_equal':True}

deps=dependency_inputs();record=json.loads((Q/'build-inputs-01.json').read_text());sources=[]
for row in record['inputs']['record']['files']:
 relative=row['path']
 rel=Path('ONTOLOGY-depo/schema')/Path(relative).name if relative.startswith('$schema/') else Path('SKILLS-depo/ontology/scripts')/Path(relative).name if relative.startswith('$tooling/') else Path('SKILLS-depo/ontology/explorer')/relative
 live=read(ROOT,rel)[0];staged=read(STAGE,rel)[0];assert live==staged and sha(live)==row['sha256'] and len(live)==row['bytes'];sources.append({'path':str(rel),'sha256':sha(live),'bytes':len(live)})
source_root=ROOT/'SKILLS-depo/ontology/explorer';authored={'index.html','package.json','package-lock.json','THIRD_PARTY_NOTICES.md','BUILD.md','vite.config.ts','tsconfig.json','scripts/package-runtime.mjs','$schema/explorer-v1.json','$tooling/ontology_explorer_assets.py'}
for p in (source_root/'src').rglob('*'):
 assert not p.is_symlink()
 if p.is_file():authored.add(str(p.relative_to(source_root)))
assert authored=={row['path'] for row in record['inputs']['record']['files']}
manifest=read(source_root/'assets','manifest.json')[0];assert manifest==read(APP/'assets','manifest.json')[0]
run=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(ROOT/'Verification/project-knowledge-explorer-first-release/service-tests/audit-live-runtime-v2.py'),'--expected-manifest',sha(manifest)],capture_output=True,text=True,timeout=30);assert run.returncode==0 and not run.stderr
runtime=json.loads(run.stdout);assert runtime['status']=='passed'
result={'status':'passed','executor':'Same frontend worker read-only post-build audit','dependency_closure':deps,'authored_build_inputs':sources,'source_inventory_exact':True,'staged_and_live_runtime_manifest_equal':True,'runtime_manifest_sha256':sha(manifest),'build_id':json.loads(manifest)['build_id'],'accepted_runtime_verifier_result':runtime,'runtime_executor_qualification':'Fresh frontend execution of unchanged accepted service audit script; original nested executor label is its static historical label. No browser claim.','stage':str(STAGE)}
write(Q/'post-build-audit-01.json',result);print(json.dumps({'status':'passed','dependency_files':deps['files'],'authored_build_members':len(sources),'runtime_members':len(runtime['members']),'manifest_sha256':sha(manifest)}))
