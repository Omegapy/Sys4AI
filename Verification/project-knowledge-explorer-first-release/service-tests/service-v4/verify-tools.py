"""Verify the reviewed external tool pins and entire test-only browser inventory."""
from pathlib import Path
import hashlib,json,os,stat

def digest(path):
    path=Path(path);fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in path.absolute().parts[1:-1]:
            nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
        member=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        try:
            before=os.fstat(member);assert stat.S_ISREG(before.st_mode) and before.st_nlink==1,'unsafe_tool'
            h=hashlib.sha256();count=0
            while data:=os.read(member,1048576):h.update(data);count+=len(data)
            after=os.fstat(member);signature=lambda s:(s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            assert signature(before)==signature(after) and count==before.st_size,'tool_changed'
            return h.hexdigest(),count,stat.S_IMODE(before.st_mode)
        finally:os.close(member)
    finally:os.close(fd)

def verify(pins_path,expected_sha256):
    pins_path=Path(pins_path);assert digest(pins_path)[0]==expected_sha256,'pins_changed';pins=json.loads(pins_path.read_text())
    for row in pins['external_tools']:
        p=Path(row['path']);resolved=p.resolve(strict=True);assert str(resolved)==row.get('resolved',str(p)),'tool_resolution_changed'
        h,size,mode=digest(resolved);assert h==row['sha256'] and size==row['bytes'],'tool_drift'
        if 'mode' in row:assert mode==row['mode'],'tool_mode_drift'
    runtime=pins['headless_runtime'];root=Path(runtime['root']);observed=[]
    for folder,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:assert not (Path(folder)/name).is_symlink(),'runtime_link'
        for name in files:
            p=Path(folder)/name;assert not p.is_symlink(),'runtime_link';observed.append(str(p.relative_to(root)))
    assert sorted(observed)==sorted(row['path'] for row in runtime['complete_files']),'runtime_inventory_changed'
    registry=json.loads(Path(runtime['registry']['path']).read_text());entry=next(x for x in registry['browsers'] if x['name']=='chromium-headless-shell')
    assert entry['revision']=='1234' and entry['browserVersion']=='151.0.7922.34','registry_mismatch'
    return {'external_tool_count':len(pins['external_tools']),'browser_runtime_members':len(observed),'browser_version':'151.0.7922.34','status':'passed'}

if __name__=='__main__':
    import sys
    print(json.dumps(verify(sys.argv[1],sys.argv[2]),sort_keys=True))
