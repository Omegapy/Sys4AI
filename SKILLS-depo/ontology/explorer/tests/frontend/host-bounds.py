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
import test_explorer_service,test_explorer_sessions,test_explorer_health

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


h=test_explorer_service.Harness(identity='explorer-bounds',limits={'page_items':5,'initial_nodes':6,'initial_edges':5,'display_nodes':10,'display_edges':12}).start()
before=h.before
process=None;report={'status':'failed','reason':'browser_not_run'};known={}
try:
    metadata={'private_file':str(h.service.bootstrap_file),'origin':h.service.origin,
              'project_name':'Explorer fixture explorer-bounds',
              'desired_route':'#/p/explorer-bounds/overview'}
    job=h.base/'browser-job.json';job.write_text(json.dumps(metadata))
    node='/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    process=subprocess.Popen([node,str(stage/'browser-bounds.cjs'),str(job)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','TMPDIR':'/private/tmp'})
    deadline=time.monotonic()+60
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
    report['node_exit_code']=process.returncode
    report['raw_stderr_suppressed']=bool(stderr)
    signals,exited=cleanup_descendants(known)
    report['observed_browser_descendants_exited']=exited;report['emergency_descendant_signals']=signals
    if not exited or process.returncode!=0:report['status']='failed'
finally:
    if process and process.poll() is None:process.terminate();process.wait(10)
    h.service.stopping=True;h.thread.join(8);h.service.close()
    report['owned_read_worker_reaped']=h.service.worker.process is None
    report['fixture_regular_files_unchanged']=before==test_explorer_service.inventory(h.root)
    verify();report['stage_inputs_unchanged']=True
    print(json.dumps(report,sort_keys=True));h.close()
raise SystemExit(0 if report['status']=='passed' and report['fixture_regular_files_unchanged'] else 1)
