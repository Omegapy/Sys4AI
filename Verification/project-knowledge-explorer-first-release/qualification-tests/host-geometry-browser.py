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


assert len(sys.argv)==1
def a11y_states(h):
    with (h.root/'docs/inert.md').open('a') as f:f.write('\nSynthetic changed evidence for accessibility state coverage.\n')
    (h.root/'docs/ambiguous.md').unlink()
    import ontology_core,ontology_retrieval
    project=ontology_core.load_project(h.root,validate=True)
    selected=types.SimpleNamespace(records=[r for r in project.records if r['kind']!='binding' and r['lifecycle']=='approved' and r['fact_kind']=='asserted'])
    assert ontology_retrieval.ranked(selected,'qzxvplmnbvtrewq')==[],'Prechecked genuinely absent canonical query'
h=test_explorer_service.Harness(identity='explorer-a11y',limits={'initial_nodes':5,'display_nodes':10},mutator=a11y_states).start()
before=h.before
process=None;report={'status':'failed','reason':'browser_not_run'};known={}
try:
    raw_dir=__import__('tempfile').mkdtemp(prefix='explorer-a11y-evidence-',dir='/private/tmp')
    metadata={'raw_dir':raw_dir,'private_file':str(h.service.bootstrap_file),'origin':h.service.origin,
      'desired_route':'#/p/explorer-a11y/overview'}
    job=h.base/'browser-job.json';job.write_text(json.dumps(metadata))
    node='/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    process=subprocess.Popen([node,str(stage/'geometry-browser.cjs'),str(job)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','TMPDIR':'/private/tmp'})
    deadline=time.monotonic()+240
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
    verify();report['stage_inputs_unchanged']=True;report['complete_headless_runtime_inventory_unchanged']=True;report['headless_runtime_files']=20
    print(json.dumps(report,sort_keys=True));h.close()
raise SystemExit(0 if report['status']=='passed' and report['fixture_regular_files_unchanged'] else 1)
