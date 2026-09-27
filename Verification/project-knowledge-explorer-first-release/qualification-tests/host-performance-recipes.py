"""Sequential supervised complete recipes and exact one-axis admission boundary."""
from pathlib import Path
import hashlib,json,os,signal,stat,subprocess,sys,tempfile,time
stage=Path(__file__).resolve().parent;manifest=json.loads((stage/'inputs.json').read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def verify():
    for item in manifest['files']:
        p=stage/item['path'];s=p.lstat()
        assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
    runtime=json.loads((stage/'test-browser-runtime.json').read_text());base=Path(runtime['root']);observed=set()
    assert not any(p.is_symlink() for p in [base,*base.parents])
    for p in base.rglob('*'):
        assert not p.is_symlink()
        if p.is_file():observed.add(str(p.relative_to(base)))
        else:assert p.is_dir()
    assert observed=={row['path'] for row in runtime['complete_files']} and len(observed)==20
    for row in [*runtime['complete_files'],runtime['registry']]:
        p=base/row['path'];assert not any(x.is_symlink() for x in [p,*p.parents]);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);h=hashlib.sha256()
        with os.fdopen(fd,'rb') as f:
            before=os.fstat(f.fileno());assert stat.S_ISREG(before.st_mode) and before.st_nlink==1
            while chunk:=f.read(1024*1024):h.update(chunk)
            after=os.fstat(f.fileno())
        signature=lambda st:(st.st_dev,st.st_ino,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
        assert signature(before)==signature(after)==signature(p.lstat())
        assert h.hexdigest()==row['sha256'] and before.st_size==row['bytes'] and ('mode' not in row or stat.S_IMODE(before.st_mode)==row['mode'])
verify();assert len(sys.argv)==1
control={};exec(compile((stage/'performance-control.py').read_bytes(),str(stage/'performance-control.py'),'exec'),control);summarize=control['summarize']
node='/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
base=Path(tempfile.mkdtemp(prefix='explorer-perfdata-',dir='/private/tmp'));results=[];number=0
python=sys.executable

def save(name,value):
 p=base/name;raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 p.chmod(0o600);return {'path':str(p),'sha256':sha(raw),'bytes':len(raw)}
def process_rows():
 p=subprocess.run(['/bin/ps','-axo','pid=,ppid=,rss=,lstart='],capture_output=True,text=True,timeout=2);assert p.returncode==0
 rows={}
 for line in p.stdout.splitlines():
  a=line.split(None,3)
  if len(a)==4 and all(x.isdigit() for x in a[:3]):rows[int(a[0])]=(int(a[1]),int(a[2])*1024,a[3])
 return rows
def tree(pid):
 rows=process_rows();found={pid};previous=set()
 while found!=previous:
  previous=found.copy();found|={k for k,v in rows.items() if v[0] in found}
 return {k:rows[k] for k in found if k in rows}
def fixture_inventory(root):
 files={};directories={}
 assert root.is_dir() and not root.is_symlink()
 for p in sorted(root.rglob('*')):
  st=p.lstat();relative=str(p.relative_to(root));assert not stat.S_ISLNK(st.st_mode)
  if stat.S_ISDIR(st.st_mode):directories[relative]=stat.S_IMODE(st.st_mode)
  else:
   assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
   fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
   with os.fdopen(fd,'rb') as f:
    begin=os.fstat(f.fileno());digest=sha(f.read());end=os.fstat(f.fileno())
   assert (begin.st_ino,begin.st_size,begin.st_mtime_ns)==(end.st_ino,end.st_size,end.st_mtime_ns)
   files[relative]={'sha256':digest,'bytes':end.st_size,'mtime_ns':end.st_mtime_ns,'mode':stat.S_IMODE(end.st_mode)}
 return {'files':files,'directories':directories}

def run(mode,scale,root,ids=None,relationships=None,canonical_file_bytes=None,canonical_path=None,trial=None):
 global number
 number+=1;label=str(number).zfill(3)+'-'+mode+'-'+root.name
 task={'base':str(base),'root':str(root),'mode':mode,'scale':scale,'ids':ids,'relationships':relationships,'canonical_file_bytes':canonical_file_bytes,'canonical_path':canonical_path,'trial':trial};job=save(label+'-job.json',task)
 timeout=180 if mode=='browser' else 120 if mode in ('canonical','canonical_boundary') else 90
 command=[node,str(stage/'compressed-runtime.cjs')] if mode=='compression' else [python,'-I','-B',str(stage/('performance-browser-case.py' if mode=='browser' else 'performance-case.py')),job['path']]
 before=fixture_inventory(root) if mode!='generate' else None
 before_ref=save(label+'-inventory-before.json',before) if before is not None else None
 started=time.monotonic();known={};peak=0;gaps=[];last=started;limit=None;controller_error=None
 cap=(1024 if mode=='browser' else 512)*1024**2
 p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','TMPDIR':'/private/tmp','PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
 try:
  while True:
   now=time.monotonic();gaps.append(now-last);last=now;rows=tree(p.pid)
   for pid,v in rows.items():known[pid]=v[2]
   peak=max(peak,max((v[1] for v in rows.values()),default=0))
   if now-started>timeout or peak>cap:
    limit='wall_deadline' if now-started>timeout else ('supervisor_1024_mib' if mode=='browser' else 'supervisor_512_mib');p.terminate()
    try:stdout,stderr=p.communicate(timeout=4)
    except subprocess.TimeoutExpired:p.kill();stdout,stderr=p.communicate(timeout=4)
    break
   try:stdout,stderr=p.communicate(timeout=.05);break
   except subprocess.TimeoutExpired:pass
 except BaseException as exc:
  controller_error=type(exc).__name__;p.terminate()
  try:stdout,stderr=p.communicate(timeout=4)
  except subprocess.TimeoutExpired:p.kill();stdout,stderr=p.communicate(timeout=4)
 # Only known owned child identities may be cleaned up, never an arbitrary PID.
 remaining={k:v for k,v in process_rows().items() if known.get(k)==v[2] and k!=p.pid};signals=[]
 for sig in (signal.SIGTERM,signal.SIGKILL):
  for pid,v in remaining.items():
   try:os.kill(pid,sig);signals.append(pid)
   except ProcessLookupError:pass
  end=time.monotonic()+2
  while remaining and time.monotonic()<end:
   time.sleep(.05);remaining={k:v for k,v in process_rows().items() if known.get(k)==v[2] and k!=p.pid}
 assert not remaining,'All known case descendants must be gone'
 first=[];valid_safe_report=False
 try:
  if mode=='browser':
   events=[json.loads(line) for line in stdout.splitlines() if line.strip()];first=[e for e in events if e.get('event')=='browser_first_readable'];final=[e for e in events if e.get('event')=='browser_result'];assert len(final)==1 and len(first)<=1 and len(events)==len(first)+1;report=final[0]
   if report['status']=='passed':assert len(first)==1
   if first:
    assert len(first)==1 and started<=first[0]['observed_monotonic']<=time.monotonic();report['cold_read']['child_spawn_to_first_readable_ms']=(first[0]['observed_monotonic']-started)*1000
    report['cold_read']['qualification']='Controller Popen start to child-observed first-readable Node event includes Python/import/stage/runtime/inventory/package/service/browser setup. Separate package boundary excludes earlier setup. Neither is public CLI command parsing or user browser-launch integration.'
   elif report['status']=='bounded_refusal':assert not first
  else:report=json.loads(stdout)
  assert isinstance(report,dict) and report.get('status') in ('generated','passed','failed','bounded_refusal','bounded_canonical_file_refusal')
  valid_safe_report=True
 except (ValueError,KeyError,AssertionError):report={'status':'failed','reason':'no_valid_safe_case_report'}
 if limit:
  interrupted=save(label+'-interrupted-safe-child.json',report) if valid_safe_report else None
  report={'status':'supervised_refusal' if mode=='canonical' else 'failed','reason':limit,'interrupted_report_status':report.get('status'),'interrupted_safe_child_report':interrupted}
 if stderr:report['status']='failed';report['raw_stderr_suppressed']=True
 if controller_error:report.update(status='failed',controller_exception_type=controller_error)
 if before is not None:
  after=fixture_inventory(root);after_ref=save(label+'-inventory-after.json',after)
  added={k:v for k,v in after['directories'].items() if k not in before['directories']}
  stable=before['files']==after['files'] and all(after['directories'].get(k)==v for k,v in before['directories'].items()) and all(k in ('.sys4ai','.sys4ai/ontology','.sys4ai/ontology/explorer') and v==0o700 for k,v in added.items())
  report.update(outer_protected_files_unchanged=stable,outer_protection={'before':before_ref,'after':after_ref,'added_startup_directories':added,'qualification':'All regular file bytes,mtime,modes preserved, including supervised or failed children. Original directory modes/presence preserved; only exact new0700 startup dirs allowed. No file exception.'})
  if not stable:report['status']='failed'

 report.update(supervisor={'elapsed_ms':(time.monotonic()-started)*1000,'process_exit_code':p.returncode,'limit':limit,'peak_individual_process_rss_bytes':peak,'max_sample_gap_seconds':max(gaps,default=0),'emergency_child_signals':len(signals),'wall_seconds':timeout,'individual_process_rss_ceiling_bytes':cap})
 result=save(label+'-result.json',report);results.append({'mode':mode,'scale':scale,'root':str(root),'result':result,'status':report['status']})
 control['validate_case'](mode,report,p.returncode)
 return report

def generated(name,scale,relationships=None,canonical_file_bytes=None):
 root=base/name;report=run('generate',scale,root,relationships=relationships,canonical_file_bytes=canonical_file_bytes)
 expected={'small':(50,100),'representative':(1000,5000),'stress':(5000,50000)}[scale];assert report['counts']['local_entries']==expected[0] and report['counts']['local_relations']==(relationships if relationships is not None else expected[1])
 return root,report

def hardware():
 values={}
 for key in ['machdep.cpu.brand_string','hw.memsize','hw.physicalcpu','hw.logicalcpu']:
  p=subprocess.run(['/usr/sbin/sysctl','-n',key],capture_output=True,text=True,timeout=5);assert p.returncode==0;values[key]=p.stdout.strip()
 p=subprocess.run(['/usr/bin/sw_vers','-productVersion'],capture_output=True,text=True,timeout=5);assert p.returncode==0;values['macos']=p.stdout.strip();values['python']=sys.version.split()[0]
 p=subprocess.run([node,'--version'],capture_output=True,text=True,timeout=5);assert p.returncode==0;values['node']=p.stdout.strip();return values

def service_summary(rows):
 successful=[r for r in rows if r['status']=='passed'];result={'attempts':len(rows),'statuses':[r['status'] for r in rows]}
 if successful:
  result['startup']=summarize([r['startup_ms'] for r in successful]);result['first_context']=summarize([r['cold_context_ms'] for r in successful]);result['warm_http']={mode:summarize([s['elapsed_ms'] for r in successful for s in r['warm_samples'][mode]]) for mode in ('search','entry_header','entry_definition','neighborhood')}
  result['qualification']='Each successful Service run retains20individual warm samples per operation; pooled n reflects all successful runs, with per-run samples retained in raw results. HTTP timings are not UI target substitutes.'
 return result

report={'status':'failed','reason':'not_finished'}
try:
 conditions=hardware();shapes={};supported=[]
 for scale in ('small','representative','stress'):
  root,fixture=generated(scale,scale);canonical=[run('canonical',scale,root) for _ in range(3)];service=[run('service',scale,root,ids=fixture['ids']) for _ in range(3)];admission=control['browser_admission'](service)
  shapes[scale]={'counts':fixture['counts'],'root':str(root),'canonical_outcomes':[r['status'] for r in canonical],'canonical_loaded_samples':summarize([r['elapsed_ms'] for r in canonical if r['status']=='passed']) if any(r['status']=='passed' for r in canonical) else None,'canonical_capacity_qualification':'Bulk counts are supported tested points or explicit supervised refusals, not a universal first unsupported record count. Separate canonical per-file byte boundary is measured below.','service':service_summary(service),'browser_admission':admission}
  if admission['eligible']:supported.append((scale,root,fixture))
 assert any(scale=='small' for scale,_,_ in supported),'Complete small recipe must be supported'
 # Distinct canonical loader per-file axis: unchanged complete small JSON value.
 canonical_boundary=[]
 for size in (2000000,2000001):
  root,fixture=generated('canonical-bytes-'+str(size),'small',canonical_file_bytes=size);padding=fixture['canonical_padding'];outcome=run('canonical_boundary','small',root,canonical_file_bytes=size,canonical_path=padding['path']);canonical_boundary.append({'bytes':size,'padding':padding,'complete_counts':fixture['counts'],'outcome':outcome['status'],'safe_code':outcome.get('safe_code')})
 assert [r['outcome'] for r in canonical_boundary]==['passed','bounded_canonical_file_refusal']
 # Separate Explorer snapshot/service relationship-count boundary on small recipe.
 low=100;high=5000;probes=[]
 root,fixture=generated('axis-'+str(high),'small',high);value=run('probe','small',root,ids=fixture['ids']);probes.append({'relationships':high,'counts':fixture['counts'],'status':value['status'],'safe_code':value.get('safe_code')});assert value['status']=='bounded_refusal'
 while high-low>1:
  n=(low+high)//2;root,fixture=generated('axis-'+str(n),'small',n);value=run('probe','small',root,ids=fixture['ids']);probes.append({'relationships':n,'counts':fixture['counts'],'status':value['status'],'safe_code':value.get('safe_code')})
  if value['status']=='passed':low=n
  else:high=n
 adjacent=[]
 for n in (low,high):
  root,fixture=generated('confirm-'+str(n),'small',n);value=run('probe','small',root,ids=fixture['ids']);adjacent.append({'relationships':n,'counts':fixture['counts'],'status':value['status'],'safe_code':value.get('safe_code')})
 assert adjacent[0]['status']=='passed' and adjacent[1]['status']=='bounded_refusal'
 # Admitted complete shapes only. Five processes/browser trials, no substitution.
 for scale,root,fixture in supported:
  profile=run('profile',scale,root,ids=fixture['ids']);browser=[run('browser',scale,root,ids=fixture['ids'],trial=i) for i in range(5)]
  shapes[scale]['source_validation_profile']={'status':profile['status'],'context_samples':len(profile['profiled_read_samples']),'immutable_snapshot_reused':profile['immutable_snapshot_reused'],'qualification':profile['qualification']};shapes[scale]['browser']=control['browser_summary'](browser)
 for scale,s in shapes.items():
  if not s['browser_admission']['eligible']:s['browser']={'status':'unavailable_actual_complete_recipe_refusal','qualification':'Not zero latency and not replaced by a smaller fixture. Exact Service outcomes are preserved.'}
 compression=run('compression','small',base/'small');assert len(compression['members'])==5
 report={'status':'passed','hardware':conditions,'shapes':shapes,'canonical_per_file_boundary':canonical_boundary,'service_relationship_axis_probes':probes,'service_adjacent_boundary_confirmation':adjacent,'compressed_runtime':compression,'result_files':results,'protocol':'Sequential complete recipes. Canonical loader120s/512MiB test supervision; browser case180s/1024MiB per-process test supervision. Production Service retains unchanged5s/256MiB worker/64MiB parent caps. No pruning/cap change. Fresh reader/process state; OS caches uncontrolled. Unexpected errors fail, never capacity refusals.','timing_qualification':'Five cold and focused Map samples per admitted complete shape; Map nearest-rank p95=max with limited tail inference.20warm search/entry/selection samples. Complete actual samples, target misses, counts, source-cost and raw/gzip/Brotli measurements remain separate. UI timing uses actual input event to exact identity/snapshot/definition/model and two animation frames. No public CLI launch claim.'}
except BaseException as exc:report={'status':'failed','reason':'recipe_measurement_failed','exception_type':type(exc).__name__,'result_files':results}
verify();report['stage_inputs_unchanged']=True;report['complete_headless_runtime_inventory_unchanged']=True;print(json.dumps(report,sort_keys=True));raise SystemExit(0 if report['status']=='passed' else 1)
