"""Freeze only the corrected test-driver binding; preserve original browser01 bytes."""
from pathlib import Path
import hashlib,json,os,stat
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):
 p=Path(p);fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in p.absolute().parts[1:-1]:
   nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
  f=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
  try:
   before=os.fstat(f);assert stat.S_ISREG(before.st_mode) and before.st_nlink==1
   data=[]
   while piece:=os.read(f,65536):data.append(piece)
   raw=b''.join(data);after=os.fstat(f)
   assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
   return raw
  finally:os.close(f)
 finally:os.close(fd)
old=Path('/private/tmp/explorer-service-v4-browser-01');raw=read(old/'inputs.json')
assert sha(raw)=='f03787eb51dc7cdd9f0a11fd239ef1f602967c38c0eb5e0284d5da44a8687760'
rows=json.loads(raw)['files'];captured={}
for row in rows:
 data=read(old/row['path']);assert sha(data)==row['sha256'] and len(data)==row['bytes']
 live=(ROOT/row['path']) if (ROOT/row['path']).is_file() else (OUT/row['path'])
 assert read(live)==data,row['path'];captured[row['path']]=data
assert len(captured)==112
captured.pop('host-playwright-driver.py');captured['host-playwright-driver-v2.py']=read(OUT/'host-playwright-driver-v2.py')
assert sha(captured['host-playwright-driver-v2.py'])=='7f8be6f60942d9f60687d569c68b7af48d19a8322265e9735c0925d8e0296937'
new=Path('/private/tmp/explorer-service-v4-browser-02');new.mkdir()
newrows=[]
for name,data in sorted(captured.items()):
 p=new/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);newrows.append({'path':name,'sha256':sha(data),'bytes':len(data)})
raw=(json.dumps({'files':newrows},indent=2)+'\n').encode();(new/'inputs.json').write_bytes(raw);(OUT/'stage-browser-02-inputs.json').write_bytes(raw)
reports=[]
for mode in ('basic','late_session','late_context'):
 oldjob=OUT/f'host-browser-{mode}-01.json';job=json.loads(read(oldjob));job['stage']=str(new);job['command'][3]=str(new/'host-playwright-driver-v2.py');job['manifest']={'path':str(new/'inputs.json'),'sha256':sha(raw)}
 job['supersedes_test_driver_only']={'path':str(oldjob.relative_to(ROOT)),'sha256':sha(read(oldjob)),'reason':'Correct manifest hash map overwritten by owned descendant tracking; all product, test assertions, browser JavaScript and tool pins unchanged.'}
 q=OUT/f'host-browser-{mode}-02.json';assert not q.exists();q.write_text(json.dumps(job,indent=2)+'\n');reports.append({'path':str(q.relative_to(ROOT)),'sha256':sha(read(q))})
print(json.dumps({'status':'frozen','stage':str(new),'manifest_sha256':sha(raw),'inputs_count':112,'only_change':'host-playwright-driver.py replaced by separately versioned host-playwright-driver-v2.py; original stage unchanged','jobs':reports},indent=2))
