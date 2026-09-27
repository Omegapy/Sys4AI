"""Read current qualification inputs; write only bounded worker evidence."""
from pathlib import Path
import hashlib,json,os,stat,sys,time
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
PACKET=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/qualification-execution-packet.json'
TREES=['ONTOLOGY','MEMORY','control_records','.sys4ai','.agents','Roles','Projects/Sys4AI-Template-Project','SKILLS-depo/ontology/scripts','SKILLS-depo/ontology/explorer','ONTOLOGY-depo']
SINGLES=['ontology.yaml','ontology-advanced.yaml','ontology-explorer.yaml','ontology-semantic.yaml','ontology-standards.yaml','project.json','memory.yaml','document-ownership.json','depot/projects.json','depot/template-update.json','SOUL.md','ROLE.md','SPECS.md','AGENTS.md','task-settings.yaml','CURATOR.md','curator.yaml','curator-session.yaml']
def write(name,obj):
    raw=(json.dumps(obj,sort_keys=True,indent=2)+'\n').encode();p=OUT/name
    with p.open('xb') as f:f.write(raw)
    return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def admit():
    raw=PACKET.read_bytes();assert hashlib.sha256(raw).hexdigest()=='5ce550a4c29312f83a83071e65abb6055ba4add09d8b39c9e2d8c0cba0910b14'
    rows=json.loads(raw)['references']
    for r in rows:
        p=ROOT/r['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
        assert not any(x.is_symlink() for x in [p,*p.parents]);b=p.read_bytes()
        assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],r['path']
    return {'packet':str(PACKET.relative_to(ROOT)),'packet_sha256':hashlib.sha256(raw).hexdigest(),'references':rows,'status':'passed','observed_unix':time.time()}
def snapshot():
    rows=[]
    def inspect(p):
        s=p.lstat();v={'path':str(p.relative_to(ROOT)),'mode':stat.S_IMODE(s.st_mode),'mtime_ns':s.st_mtime_ns,'nlink':s.st_nlink}
        if stat.S_ISLNK(s.st_mode):v.update(kind='symlink',target=os.readlink(p))
        elif stat.S_ISREG(s.st_mode):
            h=hashlib.sha256()
            with p.open('rb') as f:
                while b:=f.read(1024*1024):h.update(b)
            end=p.lstat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(end.st_size,end.st_mtime_ns,end.st_ino),str(p)
            v.update(kind='file',bytes=s.st_size,sha256=h.hexdigest())
        elif stat.S_ISDIR(s.st_mode):v={'path':v['path'],'kind':'directory','mode':v['mode']}
        else:v.update(kind='special')
        rows.append(v)
    singles=set(SINGLES)|{p.name for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.yaml','.yml','.json','.toml')}
    for name in sorted(singles):
        p=ROOT/name
        if p.exists() or p.is_symlink():inspect(p)
        else:rows.append({'path':name,'kind':'absent'})
    for tree in TREES:
        p=ROOT/tree
        if not p.exists():rows.append({'path':tree,'kind':'absent'});continue
        inspect(p)
        for parent,dirs,files in os.walk(p,followlinks=False):
            for name in sorted(dirs+files):inspect(Path(parent)/name)
    return sorted(rows,key=lambda r:r['path'])
if __name__=='__main__':
    name=sys.argv[1];assert name in ('before','before-supplemental','before-browser','after-security','after-browser','after-final')
    admission=write('input-admission-'+name+'.json',admit());rows=snapshot();parts=[]
    for start in range(0,len(rows),450):parts.append(write('protected-'+name+'-'+str(start//450).zfill(3)+'.json',rows[start:start+450]))
    result={'status':'captured','admission':admission,'parts':parts,'count':len(rows),'trees':TREES,'single_files':SINGLES,'additional_single_file_rule':'Every current root-level yaml,yml,json,toml configuration file is also inventoried. Explicit absent optional configuration paths remain represented.','excluded_paths':[],
      'timing_policy':'File mtime, byte digest, size and mode are compared. Directory mode and existence are compared; directory mtime changes naturally when explicit per-instance runtime files are created and removed.',
      'support_repair':'Fresh capture after approved active Task 2 MB policy and exact guard repair; no support change is classified as a browser-read exception.','captured_unix':time.time()}
    print(json.dumps(write('protected-'+name+'.json',result)))
