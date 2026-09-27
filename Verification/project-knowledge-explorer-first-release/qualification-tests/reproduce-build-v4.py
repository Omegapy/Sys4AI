"""Reproduce accepted build bytes in one fresh owned workspace only."""
from pathlib import Path
import base64,hashlib,json,os,stat,subprocess,sys,tarfile,io,time
ROOT=Path(__file__).resolve().parents[3];Q=Path(__file__).resolve().parent
M=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
NUMBER=sys.argv[2];assert len(NUMBER)==2 and NUMBER.isdigit()
STAGE=Path('/private/tmp/explorer-qualification-build-'+NUMBER);APP=STAGE/'SKILLS-depo/ontology/explorer'
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
def source_inputs(copy=False):
    old=json.loads(bound(ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests/narrow-layout-correction/build-inputs-03.json','d1141a712a83dd136573cd230436c99896af6dd4d0625657bf89d1eb74840ecd'))
    authored={'index.html','package.json','package-lock.json','THIRD_PARTY_NOTICES.md','BUILD.md','vite.config.ts','tsconfig.json','scripts/package-runtime.mjs','$schema/explorer-v1.json','$tooling/ontology_explorer_assets.py'}
    source_root=ROOT/'SKILLS-depo/ontology/explorer'
    for p in (source_root/'src').rglob('*'):
        assert not p.is_symlink(),str(p)
        if p.is_dir():continue
        assert p.suffix in ('.ts','.css','.html','.json') and not any(x.startswith('.') for x in p.relative_to(source_root).parts)
        authored.add(str(p.relative_to(source_root)))
    assert authored=={x['path'] for x in old['inputs']['record']['files']},'Complete current authored source inventory'
    rows=[]
    for row in old['inputs']['record']['files']:
        relative=row['path']
        if relative.startswith('$schema/'):rel=Path('ONTOLOGY-depo/schema')/Path(relative).name
        elif relative.startswith('$tooling/'):rel=Path('SKILLS-depo/ontology/scripts')/Path(relative).name
        else:rel=Path('SKILLS-depo/ontology/explorer')/relative
        b,mode=read(ROOT,rel);assert sha(b)==row['sha256'] and len(b)==row['bytes']
        if copy:p=STAGE/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);p.chmod(mode)
        else:assert read(STAGE,rel)[0]==b,rel
        rows.append({'path':str(rel),'sha256':sha(b),'bytes':len(b)})
    return rows
mode=sys.argv[1];assert mode in ('prepare','run')
if mode=='prepare':
    STAGE.mkdir();(STAGE/'npm-user.conf').write_text('');(STAGE/'npm-global.conf').write_text('');sources=source_inputs(copy=True);dependencies=dependency_inputs(copy=True)
    write(Q/('build-preparation-'+NUMBER+'.json'),{'status':'prepared_not_built','stage':str(STAGE),'sources':sources,'dependency_validation':dependencies})
    print(json.dumps({'status':'prepared_not_built','stage':str(STAGE),'source_files':len(sources),'dependency_files':dependencies['files']}));raise SystemExit(0)
gate=json.loads((Q.parent/'security-results.json').read_text());assert gate['status']=='passed' and gate['build_id']=='c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a' and set(gate['acceptance_scenarios'])=={'AT-24','AT-25','AT-26','AT-27'}
before=source_inputs();dependencies=dependency_inputs();checks=[]
env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','LANG':'en_US.UTF-8','EXPLORER_PYTHON':str(ROOT/'.venv/bin/python'),'EXPLORER_SCHEMA':str(STAGE/'ONTOLOGY-depo/schema/explorer-v1.json'),
     'npm_config_userconfig':str(STAGE/'npm-user.conf'),'npm_config_globalconfig':str(STAGE/'npm-global.conf'),'npm_config_cache':str(STAGE/'npm-cache'),'npm_config_audit':'false','npm_config_fund':'false'}
for script in ('build','package:runtime'):
    start=time.monotonic();p=subprocess.run(['/opt/homebrew/bin/npm','run',script],cwd=APP,env=env,capture_output=True,text=True,timeout=120)
    checks.append({'command':['/opt/homebrew/bin/npm','run',script],'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start,'stdout':p.stdout[-20000:],'stderr':p.stderr[-10000:]})
    if p.returncode:write(Q/('build-execution-'+NUMBER+'-failure.json'),{'status':'failed','checks':checks,'stage':str(STAGE)});raise SystemExit(1)
live=ROOT/'SKILLS-depo/ontology/explorer/assets';manifest=read(live,'manifest.json')[0];built=read(APP/'assets','manifest.json')[0];assert manifest==built
assets=json.loads(manifest)['assets'];outputs=[]
for row in assets:
    a=read(live,row['path'])[0];b=read(APP/'assets',row['path'])[0];assert a==b and sha(b)==row['sha256'] and len(b)==row['bytes'];outputs.append(row)
assert before==source_inputs();dependency_inputs()
build_record=json.loads((APP/'dist/.explorer-build.json').read_text())
write(Q/('build-inputs-reproduced-'+NUMBER+'.json'),build_record)
result={'status':'passed','executor':'See actual execution receipt; isolated disposable-stage build only','stage':str(STAGE),'checks':checks,'dependency_validation':dependencies,'source_inputs':before,'outputs':outputs,'runtime_manifest_sha256':sha(manifest),'build_id':json.loads(manifest)['build_id'],'all_runtime_bytes_equal':True,'source_and_shared_dependency_inputs_unchanged':True,'complete_current_source_inventory_equal':True,'shared_and_staged_dependency_file_and_link_closures_equal':True,'build_environment':env,'environment_policy':'Exact listed environment only; no inherited NODE_OPTIONS,NODE_PATH,npm preload/script configuration. Distinct empty user/global config files. Cache and outputs stay in owned stage.','publication_scope':'Only owned stage assets; no production/installed/source package writes.'}
write(Q/'current-v4'/'production-build-candidate.json',result);print(json.dumps({'status':'passed','build_id':result['build_id'],'runtime_members':len(outputs),'all_runtime_bytes_equal':True}))
