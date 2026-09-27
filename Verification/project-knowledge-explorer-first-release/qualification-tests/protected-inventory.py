"""Exact protected inventory for a coordinated live read window; no writes here."""
from pathlib import Path
import hashlib,os,stat
TREES=['ONTOLOGY','MEMORY','control_records','.sys4ai','.agents','Roles','Projects/Sys4AI-Template-Project','SKILLS-depo/ontology/scripts','SKILLS-depo/ontology/explorer','ONTOLOGY-depo']
SINGLES=['ontology.yaml','ontology-advanced.yaml','ontology-explorer.yaml','ontology-semantic.yaml','ontology-standards.yaml','project.json','memory.yaml','document-ownership.json','depot/projects.json','depot/template-update.json','SOUL.md','ROLE.md','SPECS.md','AGENTS.md','task-settings.yaml','CURATOR.md','curator.yaml','curator-session.yaml']
def capture(root,core):
    root=Path(root);project=core.load_project(root,validate=False)
    registered=sorted({s['path'] for r in project.records for s in r.get('sources',[])})
    singles=set(SINGLES)|set(registered)|set(project.snapshot['inputs'])|{p.name for p in root.iterdir() if p.is_file() and p.suffix in ('.yaml','.yml','.json','.toml')}
    paths={root/name for name in singles}
    for name in TREES:
        p=root/name;paths.add(p)
        if p.is_dir() and not p.is_symlink():
            for parent,dirs,files in os.walk(p,followlinks=False):paths.update(Path(parent)/x for x in dirs+files)
    rows=[]
    for p in sorted(paths):
        rel=str(p.relative_to(root));assert '..' not in Path(rel).parts
        try:st=p.lstat()
        except FileNotFoundError:rows.append({'path':rel,'kind':'absent'});continue
        r={'path':rel,'mode':stat.S_IMODE(st.st_mode)}
        if stat.S_ISDIR(st.st_mode):r['kind']='directory'
        elif stat.S_ISLNK(st.st_mode):r.update(kind='symlink',target=os.readlink(p),mtime_ns=st.st_mtime_ns)
        elif stat.S_ISREG(st.st_mode):
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);h=hashlib.sha256()
            with os.fdopen(fd,'rb') as f:
                a=os.fstat(f.fileno())
                while b:=f.read(1024*1024):h.update(b)
                end=os.fstat(f.fileno())
            signature=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            assert signature(st)==signature(a)==signature(end)==signature(p.lstat()),rel
            r.update(kind='file',bytes=st.st_size,sha256=h.hexdigest(),mtime_ns=st.st_mtime_ns,nlink=st.st_nlink)
        else:r.update(kind='special',mtime_ns=st.st_mtime_ns)
        rows.append(r)
    return {'registered_source_paths':registered,'canonical_record_count':len(project.records),'registered_input_paths':sorted(project.snapshot['inputs']),'trees':TREES,'singles':sorted(singles),'rows':rows,'timing_policy':'Compare file bytes,size,mode,mtime and link count; directory existence/mode. Directory mtime is omitted because exact authorized per-instance startup files change parent directory timestamps. No broad path exemption.'}
