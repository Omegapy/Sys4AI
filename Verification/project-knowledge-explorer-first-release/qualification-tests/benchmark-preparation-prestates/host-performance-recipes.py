"""Sequential supervised complete recipes and exact one-axis admission boundary."""
from pathlib import Path
import hashlib,json,os,signal,stat,subprocess,sys,tempfile,time
stage=Path(__file__).resolve().parent;manifest=json.loads((stage/'inputs.json').read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def verify():
 for row in manifest['files']:
  p=stage/row['path'];st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
verify();assert len(sys.argv)==1
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
def run(mode,scale,root,ids=None,relationships=None):
 global number
 number+=1;label=str(number).zfill(3)+'-'+mode+'-'+root.name
 task={'base':str(base),'root':str(root),'mode':mode,'scale':scale,'ids':ids,'relationships':relationships};job=save(label+'-job.json',task)
 started=time.monotonic();timeout=120 if mode=='canonical' else 90;known={};peak=0;gaps=[];last=started;limit=None
 p=subprocess.Popen([python,'-I','-B',str(stage/'performance-case.py'),job['path']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
 while True:
  now=time.monotonic();gaps.append(now-last);last=now;rows=tree(p.pid)
  for pid,v in rows.items():known[pid]=v[2]
  peak=max(peak,max((v[1] for v in rows.values()),default=0))
  if now-started>timeout or peak>512*1024**2:
   limit='wall_deadline' if now-started>timeout else 'supervisor_512_mib';p.terminate()
   try:stdout,stderr=p.communicate(timeout=4)
   except subprocess.TimeoutExpired:p.kill();stdout,stderr=p.communicate(timeout=4)
   break
  try:stdout,stderr=p.communicate(timeout=.05);break
  except subprocess.TimeoutExpired:pass
 # Clean only retained child identities if normal test cleanup failed.
 remaining={k:v for k,v in process_rows().items() if known.get(k)==v[2] and k!=p.pid};signals=[]
 for pid,v in remaining.items():
  if pid!=p.pid and known.get(pid)==v[2]:
   try:os.kill(pid,signal.SIGTERM);signals.append(pid)
   except ProcessLookupError:pass
 if signals:time.sleep(.1)
 remaining={k:v for k,v in process_rows().items() if known.get(k)==v[2] and k!=p.pid}
 for pid,v in remaining.items():
  if pid!=p.pid and known.get(pid)==v[2]:
   try:os.kill(pid,signal.SIGKILL)
   except ProcessLookupError:pass
 cleanup_deadline=time.monotonic()+2
 while True:
  remaining={k:v for k,v in process_rows().items() if known.get(k)==v[2] and k!=p.pid}
  if not remaining or time.monotonic()>=cleanup_deadline:break
  time.sleep(.05)
 assert not remaining,'All known case descendants must be gone'
 try:report=json.loads(stdout)
 except ValueError:report={'status':'supervised_refusal' if limit else 'failed','reason':limit or 'no_safe_case_report'}
 assert not stderr,'Case stderr must be absent'
 report.update(supervisor={'elapsed_ms':(time.monotonic()-started)*1000,'process_exit_code':p.returncode,'limit':limit,'peak_individual_process_rss_bytes':peak,'max_sample_gap_seconds':max(gaps,default=0),'emergency_child_signals':len(signals)})
 result=save(label+'-result.json',report);results.append({'mode':mode,'scale':scale,'root':str(root),'result':result,'status':report['status']})
 return report

def generated(name,scale,relationships=None):
 root=base/name;report=run('generate',scale,root,relationships=relationships);assert report['status']=='generated';return root,report

def hardware():
 values={}
 for key in ['machdep.cpu.brand_string','hw.memsize','hw.physicalcpu','hw.logicalcpu']:
  p=subprocess.run(['/usr/sbin/sysctl','-n',key],capture_output=True,text=True,timeout=5);assert p.returncode==0;values[key]=p.stdout.strip()
 p=subprocess.run(['/usr/bin/sw_vers','-productVersion'],capture_output=True,text=True,timeout=5);assert p.returncode==0;values['macos']=p.stdout.strip();values['python']=sys.version.split()[0];return values
report={'status':'failed','reason':'not_finished'}
try:
 conditions=hardware();shapes={}
 for scale in ('small','representative','stress'):
  root,fixture=generated(scale,scale);shapes[scale]={'counts':fixture['counts'],'root':str(root),'canonical':[],'service':[]}
  for _ in range(3):shapes[scale]['canonical'].append(run('canonical',scale,root))
  for _ in range(3):shapes[scale]['service'].append(run('service',scale,root,ids=fixture['ids']))
  assert all(r['status'] in ('passed','supervised_refusal') for r in shapes[scale]['canonical'])
  assert all(r['status'] in ('passed','bounded_refusal') for r in shapes[scale]['service'])
  if scale=='small':small=(root,fixture)
 assert all(r['status']=='passed' for r in shapes['small']['service']),'Small complete recipe must be supported'
 low=100;high=5000;probes=[]
 root,fixture=generated('axis-'+str(high),'small',high);value=run('probe','small',root,ids=fixture['ids']);probes.append({'relationships':high,'counts':fixture['counts'],'status':value['status'],'safe_code':value.get('safe_code')});assert value['status']=='bounded_refusal'
 while high-low>1:
  n=(low+high)//2;root,fixture=generated('axis-'+str(n),'small',n);value=run('probe','small',root,ids=fixture['ids']);probes.append({'relationships':n,'counts':fixture['counts'],'status':value['status'],'safe_code':value.get('safe_code')})
  assert value['status'] in ('passed','bounded_refusal')
  if value['status']=='passed':low=n
  else:high=n
 adjacent=[]
 for n in (low,high):
  root,fixture=generated('confirm-'+str(n),'small',n);value=run('probe','small',root,ids=fixture['ids']);adjacent.append({'relationships':n,'counts':fixture['counts'],'status':value['status'],'safe_code':value.get('safe_code')})
 assert adjacent[0]['status']=='passed' and adjacent[1]['status']=='bounded_refusal'
 profile=run('profile','small',small[0],ids=small[1]['ids']);assert profile['status']=='passed'
 summary={scale:{'counts':s['counts'],'canonical_statuses':[r['status'] for r in s['canonical']],'service_statuses':[r['status'] for r in s['service']]} for scale,s in shapes.items()}
 report={'status':'passed','hardware':conditions,'shapes':summary,'threshold_probes':probes,'adjacent_boundary_confirmation':adjacent,'result_files':results,'protocol':'Sequential owned cases only. Canonical loader has explicit120s/512MiB test supervision; production Service retains its own5s/256MiB worker/64MiB parent bounds. Complete recipes never pruned; each case runs fresh. Reader/process state is cold; OS filesystem caches are uncontrolled and are not claimed cold. Every unexpected canonical OntologyError fails the job, retaining its safe enum. Individual case files retain every timing and outcome.','timing_qualification':'Service startup/HTTP timing only; actual browser timings are a separate job. Canonical loader and instrumented source-cost profile are distinct measures. Peak RSS sampling can miss transients; sample gaps are retained.'}
except BaseException as exc:report={'status':'failed','reason':'recipe_measurement_failed','exception_type':type(exc).__name__,'result_files':results}
verify();report['stage_inputs_unchanged']=True;print(json.dumps(report,sort_keys=True));raise SystemExit(0 if report['status']=='passed' else 1)
