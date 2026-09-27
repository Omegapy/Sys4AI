"""Admit the explicit round-two current inputs without rewriting historical receipts."""
from pathlib import Path
import hashlib,json,os,stat,time
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
PACKET=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/qualification-current-v3-input-packet.json'
EXPECTED='bf9b52bccd01ada39a2510500c3ec20eed7608365fc5393211060d1a38debcc7'
def read(p):
    assert not any(x.is_symlink() for x in [p,*p.parents]),str(p)
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno());assert stat.S_ISREG(a.st_mode) and a.st_nlink==1,str(p)
        raw=f.read();b=os.fstat(f.fileno())
    c=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns)==(c.st_ino,c.st_size,c.st_mtime_ns,c.st_ctime_ns),str(p)
    return raw
def ref(p):
    raw=read(p);return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def check(r):
    actual=ref(ROOT/r['path']);assert actual['sha256']==r['sha256'] and ('bytes' not in r or actual['bytes']==r['bytes']),r['path'];return actual
def admit():
    raw=read(PACKET);assert hashlib.sha256(raw).hexdigest()==EXPECTED
    d=json.loads(raw);assert d['round']==2 and len(d['criteria'])==16 and len(d['references'])==220
    rows=[check(r) for r in d['references']];contexts=[check(r) for r in d['previous_context']]
    baseline=json.loads(read(ROOT/d['previous_context'][0]['path']));assert baseline['criteria']==d['criteria'] and baseline['writes']==d['write_scope']
    current={r['path']:r for r in rows}
    for e in d['authorized_source_runtime_evolution']:
        if e['current'] is None:assert not (ROOT/e['previous']['path']).exists(),e['previous']['path']
        else:assert current[e['current']['path']]==e['current']
    assert len(d['authorized_source_runtime_evolution'])==7
    build=d['current_build'];check(build['manifest']);assetroot=ROOT/Path(build['manifest']['path']).parent
    manifest=json.loads(read(assetroot/'manifest.json'));assert manifest['build_id']==build['build_id']
    members=[]
    for r in build['all_members']:
        a=ref(assetroot/r['path']);assert a['sha256']==r['sha256'] and a['bytes']==r['bytes'];members.append(a)
    observed=set()
    for p in assetroot.rglob('*'):
        assert not p.is_symlink(),str(p)
        if p.is_file():observed.add(str(p.relative_to(assetroot)))
    assert observed=={'manifest.json'}|{r['path'] for r in build['all_members']}
    roles=[ref(ROOT/n) for n in ['SOUL.md','Roles/project-sub-agent/AGENTS.md','Roles/project-sub-agent/ROLE.md']]
    check(d['prior_owned_work_checkpoint'])
    return {'status':'passed','observed_unix':time.time(),'native_id':d['native_id'],'baseline':d['baseline'],'round':2,'activation':'Manager supplied EV_QUALIFICATION_CURRENT_V3_INPUTS committed 205 to 206; no worker state operations.','packet':ref(PACKET),'role_reads':roles,'references':rows,'context_references':contexts,'criteria_count':16,'authorized_evolutions':d['authorized_source_runtime_evolution'],'current_build_id':build['build_id'],'runtime_members':members,'runtime_inventory_exact':True,'historical_checkpoint':d['prior_owned_work_checkpoint'],'protected_read_window_started':False}
if __name__=='__main__':
    result=admit();p=OUT/'input-admission-current-v3.json'
    with p.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(ref(p)))
