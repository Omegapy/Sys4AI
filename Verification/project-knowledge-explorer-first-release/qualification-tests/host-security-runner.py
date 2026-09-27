"""Frozen disposable test executor: outputs evidence, edits no project files."""
import traceback
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
import test_explorer_service,test_explorer_security

class SafeResult(unittest.TextTestResult):
    def _exc_info_to_string(self,err,test):
        # No exception text, values, locals, source lines or response bytes.
        frames=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(err[2])]
        return json.dumps({'case':test.id(),'exception_type':err[0].__name__,'frames':frames},sort_keys=True)
if len(sys.argv)==2 and sys.argv[1]=='--redaction-self-test':
    class Probe(unittest.TestCase):
        def runTest(self):self.assertNotIn(b'CSRF_PRIVATE_SENTINEL',b'CSRF_PRIVATE_SENTINEL')
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,resultclass=SafeResult).run(Probe())
    safe=json.dumps({'failures':[v for _,v in r.failures],'log':stream.getvalue()})
    assert 'CSRF_PRIVATE_SENTINEL' not in safe and len(r.failures)==1
    print(json.dumps({'status':'passed','deliberate_assertion_failure':True,'secret_sentinel_absent_from_report':True,'safe_frame_locations_retained':True}))
    raise SystemExit(0)
modules=(test_explorer_security,)
if len(sys.argv)==3 and sys.argv[1]=='--case':
    # Record actual Popen objects solely for emergency cleanup; every spawn
    # still uses the real subprocess implementation and actual owned process.
    spawned=[];original_popen=subprocess.Popen
    def tracked_popen(*args,**kwargs):
        value=original_popen(*args,**kwargs);spawned.append(value);return value
    subprocess.Popen=tracked_popen
    def interrupted(signum,frame):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,interrupted)
    suite=unittest.defaultTestLoader.loadTestsFromName(sys.argv[2])
    stream=io.StringIO();start=time.monotonic();report=None
    try:
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=SafeResult).run(suite)
        report={'status':'passed' if result.wasSuccessful() else 'failed','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
                'skips':len(result.skipped),'elapsed_seconds':time.monotonic()-start,'inputs_unchanged':True,
                'safe_test_log':stream.getvalue()[-12000:],'observations':test_explorer_service.OBSERVATIONS}
    except BaseException as exc:
        report={'status':'failed','tests_run':0,'failures':0,'errors':1,'skips':0,'elapsed_seconds':time.monotonic()-start,
                'safe_test_log':stream.getvalue()[-12000:],'observations':test_explorer_service.OBSERVATIONS,'interrupted_type':type(exc).__name__}
    finally:
        # Cleanup is explicit even when the parent's per-case deadline fires.
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        for harness in list(test_explorer_service.LIVE_HARNESSES):
            try:harness.close()
            except Exception:pass
        for process in reversed(spawned):
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=2)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
        subprocess.Popen=original_popen
    verify();report['owned_children_reaped']=all(p.poll() is not None for p in spawned)
    print(json.dumps(report,sort_keys=True));raise SystemExit(0 if report['status']=='passed' and report['owned_children_reaped'] else 1)
assert len(sys.argv)==1
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in modules)
def tests(suite):
    for t in suite:
        if isinstance(t,unittest.TestSuite):yield from tests(t)
        else:yield t.id()
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

start=time.monotonic();cases=[]
for name in tests(suite):
    process=subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--case',name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    timed_out=False;known={};deadline=time.monotonic()+45
    while True:
        remember_descendants(process.pid,known)
        try:
            stdout,stderr=process.communicate(timeout=min(.25,max(.01,deadline-time.monotonic())))
            break
        except subprocess.TimeoutExpired:
            if time.monotonic()<deadline:continue
            timed_out=True;process.terminate()
            try:stdout,stderr=process.communicate(timeout=15)
            except subprocess.TimeoutExpired:process.kill();stdout,stderr=process.communicate(timeout=3)
            break
    killed,descendants_exited=cleanup_descendants(known)
    try:row=json.loads(stdout)
    except ValueError:row={'status':'failed','tests_run':0,'failures':0,'errors':1,'skips':0,'log':'Isolated test process did not return its bounded report.','observations':[],'owned_children_reaped':False}
    row.update(case=name,exit_code=process.returncode,timed_out=timed_out,observed_descendants_exited=descendants_exited,emergency_descendant_signals=killed)
    if timed_out or not descendants_exited:row['status']='failed'
    row['raw_stderr_suppressed']=bool(stderr);row['stderr_bytes']=len(stderr.encode())
    cases.append(row)
verify()
report={'status':'passed' if all(c['status']=='passed' and c['exit_code']==0 for c in cases) else 'failed',
        'tests_run':sum(c['tests_run'] for c in cases),'failures':sum(c['failures'] for c in cases),'errors':sum(c['errors'] for c in cases),
        'skips':sum(c['skips'] for c in cases),'elapsed_seconds':time.monotonic()-start,'inputs_unchanged':True,'cases':cases,
        'executor':'Primary host executes this frozen worker-authored driver. Each case uses a fresh process; all test writes stay in disposable explorer-http-* roots.'}
print(json.dumps(report,sort_keys=True));raise SystemExit(0 if report['status']=='passed' else 1)
