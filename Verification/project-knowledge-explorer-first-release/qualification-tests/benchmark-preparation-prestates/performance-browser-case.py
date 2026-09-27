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


assert len(sys.argv)==2
import queue,threading
job_path=Path(sys.argv[1]);assert str(job_path).startswith('/private/tmp/explorer-perfdata-')
config=json.loads(job_path.read_text());root=Path(config['root']);assert root.parent==job_path.parent and root.name=='small' and root==root.resolve()
base=job_path.parent;report={'status':'failed','reason':'not_run'};package=None;service=None;thread=None;process=None;known={};lines=queue.Queue()
try:
    before=test_explorer_service.inventory(root);started=time.monotonic()
    launcher=test_explorer_service.compile_file('_browser_performance_launcher',scripts/'ontology_explorer.py');package,assets=launcher.prepare_package(scripts)
    service=package.modules['ontology_explorer'].Service(package,assets,root);service_ready_ms=(time.monotonic()-started)*1000
    thread=threading.Thread(target=service.serve);thread.start()
    metadata={'private_file':str(service.bootstrap_file),'origin':service.origin,'project_id':service.project,'project_name':'Explorer fixture '+service.project,'run_fault_observation':config['trial']==0}
    private=base/('browser-private-'+str(config['trial'])+'.json');private.write_text(json.dumps(metadata));private.chmod(0o600)
    process=subprocess.Popen(['/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node',str(stage/'performance-browser.cjs'),str(private)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','TMPDIR':'/private/tmp'})
    stderr_bytes=[]
    def consume_stdout():
        for line in process.stdout:lines.put((time.monotonic(),line))
    def consume_stderr():
        raw=process.stderr.read();stderr_bytes.append(len(raw.encode()))
    reader=threading.Thread(target=consume_stdout);errreader=threading.Thread(target=consume_stderr);reader.start();errreader.start();deadline=time.monotonic()+150;first=None
    while process.poll() is None:
        remember_descendants(process.pid,known)
        if time.monotonic()>=deadline:
            process.terminate()
            try:process.wait(5)
            except subprocess.TimeoutExpired:process.kill();process.wait(5)
            break
        time.sleep(.05)
    reader.join(5);errreader.join(5);assert not reader.is_alive() and not errreader.is_alive()
    while not lines.empty():
        observed,raw=lines.get();value=json.loads(raw)
        if value.get('event')=='first_readable':assert first is None;first={**value,'package_start_to_observed_first_readable_ms':(observed-started)*1000,'service_ready_ms':service_ready_ms}
        elif value.get('event')=='result':report=value
        else:raise ValueError('Unknown fixed browser event')
    assert first is not None;report['cold_read']=first
    signals,exited=cleanup_descendants(known);report.update(node_exit_code=process.returncode,raw_stderr_suppressed=bool(sum(stderr_bytes)),observed_browser_descendants_exited=exited,emergency_descendant_signals=signals)
    report['worker_peak_rss_bytes']=service.worker.peak;report['parent_peak_rss_bytes']=service.worker.parent_peak;report['rss_max_observation_gap_seconds']=service.worker.max_observation_gap;report['effective_policy']=service.policy
    if process.returncode or sum(stderr_bytes) or not exited or signals:report['status']='failed'
except BaseException as exc:report.update(status='failed',reason='browser_timing_driver_failed',exception_type=type(exc).__name__)
finally:
    if process and process.poll() is None:process.terminate();process.wait(5)
    if service:
        service.stopping=True
        if thread:thread.join(8)
        service.close();report['owned_worker_reaped']=service.worker.process is None
    if package:package.close()
    report['protected_files_unchanged']=before==test_explorer_service.inventory(root)
    if not report['protected_files_unchanged'] or not report.get('owned_worker_reaped'):report['status']='failed'
    verify();report['stage_inputs_unchanged']=True;report['complete_headless_runtime_inventory_unchanged']=True
print(json.dumps(report,sort_keys=True));raise SystemExit(0 if report['status']=='passed' else 1)
