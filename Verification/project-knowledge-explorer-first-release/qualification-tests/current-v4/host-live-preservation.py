"""Frozen disposable test executor: outputs evidence, edits no project files."""
import hashlib,importlib.abc,importlib.util,io,json,os,signal,stat,subprocess,sys,time,types,unittest
from pathlib import Path
stage=Path(__file__).resolve().parent
manifest=json.loads((stage/'inputs.json').read_text())
def verify():
    for item in manifest['files']:
        p=stage/item['path'];s=p.lstat()
        assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
verify();sys.dont_write_bytecode=True
scripts=stage/'SKILLS-depo/ontology/scripts';tests=stage/'SKILLS-depo/ontology/tests'
known={row['path']:row['sha256'] for row in manifest['files']}
class Source(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    def find_spec(self,name,path=None,target=None):
        p=(scripts/name).with_suffix('.py') if name.startswith('ontology') else (tests/name).with_suffix('.py')
        if p.is_file() and str(p.relative_to(stage)) in known:return importlib.util.spec_from_file_location(name,p,loader=self)
        return None
    def create_module(self,spec):return None
    def exec_module(self,module):
        p=Path(module.__spec__.origin);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==known[str(p.relative_to(stage))]
        module.__file__=str(p);exec(compile(raw,str(p),'exec',dont_inherit=True),module.__dict__)
sys.meta_path.insert(0,Source())
import test_explorer_service

def process_snapshot():
    observed=subprocess.run(['/bin/ps','-axo','pid=,ppid=,lstart='],capture_output=True,text=True,timeout=2)
    rows={}
    for line in observed.stdout.splitlines():
        parts=line.split(None,2)
        if len(parts)==3 and parts[0].isdigit() and parts[1].isdigit():rows[int(parts[0])]=(int(parts[1]),parts[2])
    return rows

def remember_descendants(pid,known):
    rows=process_snapshot();front={pid};seen=set()
    while front:
        found={child for child,(parent,stamp) in rows.items() if parent in front and child not in seen}
        seen.update(found)
        for child in found:known[child]=rows[child][1]
        front=found

def cleanup_descendants(known):
    count=0
    for sig,wait in ((signal.SIGTERM,2),(signal.SIGKILL,2)):
        rows=process_snapshot()
        alive=[pid for pid,stamp in known.items() if pid in rows and rows[pid][1]==stamp]
        if not alive:return count,True
        for pid in alive:
            try:os.kill(pid,sig);count+=1
            except ProcessLookupError:pass
        end=time.monotonic()+wait
        while time.monotonic()<end:
            rows=process_snapshot()
            if not any(pid in rows and rows[pid][1]==known[pid] for pid in alive):return count,True
            time.sleep(.05)
    rows=process_snapshot()
    return count,not any(pid in rows and rows[pid][1]==stamp for pid,stamp in known.items())


assert len(sys.argv)==1
import tempfile,threading
TARGET=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
base=Path(tempfile.mkdtemp(prefix='explorer-live-preservation-',dir='/private/tmp'))
def dump(name,value):
    p=base/name;raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    with p.open('xb') as f:f.write(raw)
    p.chmod(0o600);return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def inventory_receipt(label,value):
    rows=value.pop('rows');parts=[dump(label+'-'+str(i//450).zfill(3)+'.json',rows[i:i+450]) for i in range(0,len(rows),450)]
    return dump(label+'.json',{**value,'count':len(rows),'parts':parts}),{r['path']:r for r in rows}
code=(stage/'protected-inventory.py').read_bytes();module=types.ModuleType('protected_inventory');exec(compile(code,str(stage/'protected-inventory.py'),'exec'),module.__dict__)
launcher=test_explorer_service.compile_file('_live_preservation_launcher',scripts/'ontology_explorer.py');package,assets=launcher.prepare_package(scripts)
service=None;thread=None;process=None;report={'status':'failed','reason':'not_run'};known={};before_rows=None
try:
    project=package.modules['ontology_core'].load_project(TARGET,validate=False)
    before_ref,before_rows=inventory_receipt('before',module.capture(TARGET,package.modules['ontology_core']))
    service=package.modules['ontology_explorer'].Service(package,assets,TARGET);thread=threading.Thread(target=service.serve);thread.start()
    startup_ref,startup_rows=inventory_receipt('startup',module.capture(TARGET,package.modules['ontology_core']))
    exact_files=[str(p.relative_to(TARGET)) for p in (service.bootstrap_file,service.identity_file)];exact_dirs=service.private.created_directories[:]
    startup_changes=[k for k in sorted(set(before_rows)|set(startup_rows)) if before_rows.get(k)!=startup_rows.get(k)]
    assert set(startup_changes)==set(exact_files)|set(exact_dirs),'Only exact startup creations'
    assert all(startup_rows[k]['mode']==0o600 for k in exact_files) and all(startup_rows[k]['mode']==0o700 for k in exact_dirs)
    metadata={'private_file':str(service.bootstrap_file),'origin':service.origin,'project_id':service.project,'project_name':project.config['project']['name'],'preference_key':'sys4ai-explorer:v1:'+service.root_scope+':'+service.project+':'+project.config['project']['namespace']}
    job=base/'private-job.json';job.write_text(json.dumps(metadata));job.chmod(0o600)
    process=subprocess.Popen(['/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node',str(stage/'live-preservation-browser.cjs'),str(job)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','TMPDIR':'/private/tmp'})
    deadline=time.monotonic()+120
    while True:
        remember_descendants(process.pid,known)
        try:stdout,stderr=process.communicate(timeout=.25);break
        except subprocess.TimeoutExpired:
            if time.monotonic()<deadline:continue
            process.terminate()
            try:stdout,stderr=process.communicate(timeout=10)
            except subprocess.TimeoutExpired:process.kill();stdout,stderr=process.communicate(timeout=3)
            break
    try:report=json.loads(stdout)
    except ValueError:report={'status':'failed','reason':'no_safe_browser_report'}
    report['node_exit_code']=process.returncode;report['raw_stderr_suppressed']=bool(stderr)
    signals,exited=cleanup_descendants(known);report['observed_browser_descendants_exited']=exited;report['emergency_descendant_signals']=signals
    if not exited or process.returncode!=0:report['status']='failed'
    report['protected_before']=before_ref;report['protected_startup']=startup_ref;report['exact_startup_files']=exact_files;report['exact_startup_directories']=exact_dirs;report['startup_only_exact_creations']=True
except BaseException as exc:
    report.update(status='failed',reason='live_preservation_driver_failed',exception_type=type(exc).__name__)
finally:
    if process and process.poll() is None:process.terminate();process.wait(10)
    if service:
        service.stopping=True
        if thread:thread.join(8)
        service.close();report['owned_read_worker_reaped']=service.worker.process is None
    if before_rows is not None:
        after_ref,after_rows=inventory_receipt('after',module.capture(TARGET,package.modules['ontology_core']))
        changes=[{'path':k,'before':before_rows.get(k),'after':after_rows.get(k)} for k in sorted(set(before_rows)|set(after_rows)) if before_rows.get(k)!=after_rows.get(k)]
        allowed=set(service.private.created_directories if service and service.private else [])
        unexpected=[r for r in changes if not (r['path'] in allowed and r['before'] is None and r['after']=={'path':r['path'],'kind':'directory','mode':0o700})]
        report['protected_after']=after_ref;report['protected_changes']=changes;report['unexpected_changes']=unexpected;report['complete_protected_comparison_passed']=not unexpected
        if unexpected:report['status']='failed'
    verify();report['stage_inputs_unchanged']=True;package.close();print(json.dumps(report,sort_keys=True))
raise SystemExit(0 if report['status']=='passed' and report.get('owned_read_worker_reaped') and report.get('complete_protected_comparison_passed') else 1)
