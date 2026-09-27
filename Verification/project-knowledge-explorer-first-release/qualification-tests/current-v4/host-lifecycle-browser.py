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


assert len(sys.argv)==2 and sys.argv[1] in ('expiry','stop','entry_deadline')
mode=sys.argv[1];blocked_worker=None
h=test_explorer_service.Harness(identity='explorer-alpha',limits={'session_seconds':60})
def directories():return {str(p.relative_to(h.root)):stat.S_IMODE(p.stat().st_mode) for p in h.root.rglob('*') if p.is_dir() and not p.is_symlink()}
before=h.before;before_dirs=directories();h.start()
startup_files=[{'path':str(p.relative_to(h.root)),'mode':stat.S_IMODE(p.stat().st_mode)} for p in (h.service.bootstrap_file,h.service.identity_file)]
created_dirs=h.service.private.created_directories[:]
process=None;report={'status':'failed','reason':'browser_not_run'};known={}
try:
    metadata={'private_file':str(h.service.bootstrap_file),'origin':h.service.origin,
      'desired_route':'#/p/explorer-alpha/entry/urn%3Asys4ai%3Aontology%3Aproject%3Aexplorer-alpha%3Aentry-00000',
      'mode':mode,'control_file':str(h.base/'lifecycle-control.json'),'control_ack':str(h.base/'lifecycle-ack.json')}
    job=h.base/'browser-job.json';job.write_text(json.dumps(metadata))
    node='/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    process=subprocess.Popen([node,str(stage/'lifecycle-browser.cjs'),str(job)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','TMPDIR':'/private/tmp'})
    deadline=time.monotonic()+95
    while True:
        control=h.base/'lifecycle-control.json';ack=h.base/'lifecycle-ack.json'
        if mode in ('stop','entry_deadline') and control.exists() and not ack.exists():
            st=control.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=128
            expected='stop_service' if mode=='stop' else 'suspend_owned_worker'
            assert json.loads(control.read_text())=={'action':expected}
            if mode=='stop':
                h.service.stopping=True;h.thread.join(8);h.service.close();assert not h.thread.is_alive() and h.service.worker.process is None
                ack.write_text(json.dumps({'service_stopped':True}))
            else:
                blocked_worker=h.service.worker.process;assert isinstance(blocked_worker,subprocess.Popen) and blocked_worker.poll() is None
                os.kill(blocked_worker.pid,signal.SIGSTOP)
                ack.write_text(json.dumps({'worker_suspended':True,'request_seconds':h.service.policy['request_seconds']}))
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
    report['node_exit_code']=process.returncode
    report['raw_stderr_suppressed']=bool(stderr)
    signals,exited=cleanup_descendants(known)
    report['observed_browser_descendants_exited']=exited;report['emergency_descendant_signals']=signals
    if not exited or process.returncode!=0:report['status']='failed'
finally:
    if process and process.poll() is None:process.terminate();process.wait(10)
    h.service.stopping=True;h.thread.join(8);h.service.close()
    report['owned_read_worker_reaped']=h.service.worker.process is None;report['suspended_owned_worker_reaped']=blocked_worker is None or blocked_worker.poll() is not None
    after=test_explorer_service.inventory(h.root);after_dirs=directories()
    report['fixture_regular_files_unchanged']=before==after
    report['fixture_protected_before']=before;report['fixture_protected_after']=after
    report['fixture_directory_modes_before']=before_dirs;report['fixture_directory_modes_after']=after_dirs
    report['exact_startup_files']=startup_files;report['exact_startup_created_directories']=created_dirs
    directory_changes={k:after_dirs.get(k) for k in set(before_dirs)|set(after_dirs) if before_dirs.get(k)!=after_dirs.get(k)}
    report['only_exact_startup_directory_changes']=directory_changes=={k:0o700 for k in created_dirs}
    report['exact_startup_files_removed']=all(not (h.root/r['path']).exists() for r in startup_files)
    if not report['only_exact_startup_directory_changes'] or not report['exact_startup_files_removed']:report['status']='failed'
    verify();report['stage_inputs_unchanged']=True
    print(json.dumps(report,sort_keys=True));h.close()
raise SystemExit(0 if report['status']=='passed' and report['fixture_regular_files_unchanged'] else 1)
