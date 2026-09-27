"""Freeze current read-only inputs into uniquely owned V3 host stages."""
from pathlib import Path
import hashlib,json,os,stat
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
PACKET=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/service-v3-input-packet.json'
def raw(p):
 p=Path(p);fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in p.absolute().parts[1:-1]:
   nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
  member=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
  try:
   before=os.fstat(member);assert stat.S_ISREG(before.st_mode) and before.st_nlink==1
   pieces=[]
   while piece:=os.read(member,65536):pieces.append(piece)
   value=b''.join(pieces);after=os.fstat(member);key=lambda s:(s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
   assert key(before)==key(after) and len(value)==before.st_size;return value
  finally:os.close(member)
 finally:os.close(fd)
def sha(v):return hashlib.sha256(v).hexdigest()
def ref(p):v=raw(p);return {'path':str(p),'sha256':sha(v),'bytes':len(v)}
def save(name,value):
 p=OUT/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(ROOT)),'sha256':sha(raw(p)),**value}))
packet=raw(PACKET);assert sha(packet)=='d94f72539c3b7c2c8e826a6639c9d51ed88038130e20a5515fac014785e65ab0'
d=json.loads(packet)
for row in d['references']:
 v=raw(ROOT/row['path']);assert sha(v)==row['sha256'] and len(v)==row['bytes'],row['path']
paths=list((ROOT/'SKILLS-depo/ontology/scripts').glob('ontology*.py'))
paths += [ROOT/'SKILLS-depo/ontology/tests'/n for n in ['test_explorer_service.py','test_explorer_sessions.py','test_explorer_health.py','support.py','explorer_support.py']]
paths += [p for p in (ROOT/'ONTOLOGY-depo').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [ROOT/'SKILLS-depo/ontology/explorer'/n for n in ['package.json','package-lock.json','THIRD_PARTY_NOTICES.md','BUILD.md']]
paths += [p for p in (ROOT/'SKILLS-depo/ontology/explorer/assets').rglob('*') if p.is_file()]
contents={str(p.relative_to(ROOT)):raw(p) for p in sorted(set(paths))}
def stage(kind,names):
 target=Path('/private/tmp/explorer-service-v3-'+kind+'-01');target.mkdir();items=[]
 for name,value in {**contents,**{n:raw(OUT/n) for n in names}}.items():
  q=target/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(value);items.append({'path':name,'sha256':sha(value),'bytes':len(value)})
 items.sort(key=lambda x:x['path']);m=json.dumps({'files':items},indent=2)+'\n';(target/'inputs.json').write_text(m);(OUT/('stage-'+kind+'-01-inputs.json')).write_text(m)
 return target,{'path':str(target/'inputs.json'),'sha256':sha(m.encode())},len(items)
service,m,count=stage('batch',['host-runner.py'])
save('host-batch-01.json',{'command':[str(ROOT/'.venv/bin/python'),'-I','-B',str(service/'host-runner.py')],'stage':str(service),'manifest':m,'inputs_count':count,'timeout_seconds':300,'intended_writes':['Only independent disposable explorer-http-* fixture trees/private runtime and case-owned processes. No source or old evidence writes.'],'cleanup':'Existing bounded per-case runner closes/reaps owned children and observes exact descendant identities; fixed resource ceilings remain.','scope':'All28 original service/session/health/public CLI/installed layout/provenance/resource cases against current V3 bundle.','credential_boundary':'Memory and exact private runtime files only; no bootstrap URL/body/CSRF in command arguments or output.'})
browser,m,count=stage('browser',['host-runner.py','host-playwright-driver.py','browser-bootstrap.cjs'])
external=[ref(Path(p)) for p in ['/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node','/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']]
for mode in ['basic','late_session','late_context']:
 save('host-browser-'+mode+'-01.json',{'command':[str(ROOT/'.venv/bin/python'),'-I','-B',str(browser/'host-playwright-driver.py'),mode],'stage':str(browser),'manifest':m,'inputs_count':count,'external_test_tools':external,'timeout_seconds':100,'intended_writes':['Independent disposable explorer-http-* fixture/private runtime and fresh Playwright Chrome profile only.'],'cleanup':'Close context/browser, stop/reap reader and recorded browser descendants, audit unchanged fixture/stage/tools.','credential_boundary':'No private URL/CSRF/body/raw exception output, trace/HAR or screenshots. Delayed real response lives only in browser memory. Clipboard capture does not change OS clipboard.','scope':'Current full UI bootstrap/resume/copy-link/close/replays and abort-insensitive late session/context modes. Race comparison waits for recorded catalog names to finish current reads; no fake response substitution.','same_product_inputs_as':'host-batch-01.json'})
osstage,m,count=stage('os-open',['host-runner.py','host-browser-driver.py'])
save('host-os-open-01.json',{'command':[str(ROOT/'.venv/bin/python'),'-I','-B',str(osstage/'host-browser-driver.py')],'stage':str(osstage),'manifest':m,'inputs_count':count,'external_test_tools':external,'timeout_seconds':360,'intended_writes':['One disposable fixture/private runtime/reader; ordinary OS default browser opens one tab with existing settings.'],'credential_boundary':'Wait for browser_ready and inspect only the actual created tab after positive fragment removal. No replacement tab, credential URL output, raw error or private-body output.','inspection':['Observe exact initial native browser zoom. Set and positively observe actual200percent browser zoom, without CSS/page-scale/viewport substitution.','Inspect labeled controls and corrected Processes catalog: recorded process names with exact IDs retained. Open Fixture ordered inspection by its displayed recorded name, inspect vertical process reading and numbered steps, open a step source and verify wrapped source text, heading focus, visible exact-trigger return. Also inspect the ordinary Alignment source drawer.','Restore and positively observe the exact original browser zoom before closing only this created tab. Record native Map/List200percent only if actually observed; not required or inferred here.','Stop the exact owned driver with normal SIGTERM, then await browser_cleanup/exit and created-tab absence. Driver lifetime is300seconds, outer job360seconds.'],'cleanup':'Normal exact-driver stop or its bounded lifetime closes listener/private files and reaps reader; exact fixture/stage/tools postchecks. Restore original zoom and close only actual created test tab.','attribution':'Actual OS default-browser dispatch through verified in-process command(... explore --open). Public CLI subprocess proof is the current V3 service batch01; direct Playwright runs remain separate.','scope':'Current native zoom and corrected catalog/source/process reading only. No Safari, VoiceOver, human comprehension, native Map/List-at200percent, release-performance or final Task acceptance.'})
for row in d['references']:
 v=raw(ROOT/row['path']);assert sha(v)==row['sha256'] and len(v)==row['bytes']
