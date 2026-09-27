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
h=test_explorer_service.Harness(identity='explorer-native-at').start()
window_id=None;ready=False;stopped=False;observed=[]
original_finish=h.service.finish_job
def finish(value):
    result=original_finish(value)
    body=value.get('body',{}) if isinstance(value,dict) else {}
    if body.get('operation') in h.module.OPERATIONS:
        observed.append({'operation':body['operation'],'status':body.get('status')})
    return result
h.service.finish_job=finish

def osa(script):
    # A private URL may enter this process input, never argv or emitted output.
    p=subprocess.run(['/usr/bin/osascript'],input=script,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=10)
    return p.returncode,p.stdout

def stop(signum,frame):
    global stopped
    stopped=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
report={'status':'failed','reason':'native_not_ready'}
try:
    private=json.loads(h.service.bootstrap_file.read_text());url=private['url']+'&route='+__import__('urllib.parse',fromlist=['quote']).quote('#/p/explorer-native-at/overview',safe='')
    code,raw=osa('tell application "Safari"\nmake new document with properties {URL:'+json.dumps(url)+'}\nactivate\nreturn id of front window\nend tell')
    url=None;private=None
    assert code==0 and raw.strip().isdigit(),'native_open_failed'
    window_id=int(raw.strip());deadline=time.monotonic()+120;next_poll=0
    while not stopped and time.monotonic()<deadline:
        if not ready and time.monotonic()>=next_poll:
            next_poll=time.monotonic()+.5
            code,actual=osa('tell application "Safari" to return URL of current tab of window id '+str(window_id))
            clean=code==0 and actual.strip().startswith(h.service.origin+'/#/p/explorer-native-at/') and 'bootstrap=' not in actual
            if clean and any(x['operation']=='context' and x['status']!='error' for x in observed):
                ready=True
                print(json.dumps({'status':'native_ready','browser':'Safari','owned_window_id':window_id,'clean_url':actual.strip(),'origin':h.service.origin,'bootstrap_removed':True,'context_response_processed':True,'fixture_identity':'explorer-native-at','build_id':h.assets.manifest['build_id'],'service_instance':h.service.instance}),flush=True)
        time.sleep(.1)
    report={'status':'completed' if ready and stopped else 'timeout','native_ready':ready,'stop_requested':stopped,'driver_lifetime_seconds':120,'owned_window_id':window_id,'observed_read_operations':observed,'qualification':'Actual Safari document opened through osascript process input, private URL never passed in argv/logs. Root supplies actual focused Theme keyboard/menu/value and restoration observations separately. No speech or whole accessibility claim.'}
except BaseException as exc:
    report={'status':'failed','reason':'native_driver_failed','exception_type':type(exc).__name__,'owned_window_id':window_id,'native_ready':ready}
finally:
    h.service.stopping=True;h.thread.join(8);h.service.close()
    report['owned_read_worker_reaped']=h.service.worker.process is None
    report['fixture_regular_files_unchanged']=h.before==test_explorer_service.inventory(h.root)
    if window_id:
        code,raw=osa('tell application "Safari" to return exists window id '+str(window_id));report['owned_safari_window_closed']=code==0 and raw.strip()=='false'
        # Return only a Boolean, never other tab URLs. Root independently records
        # closure of the exact CUA-owned document/tab and preserves later tabs.
        script='tell application "Safari"\nif not (exists window id '+str(window_id)+') then return true\nrepeat with t in tabs of window id '+str(window_id)+'\nif URL of t starts with '+json.dumps(h.service.origin+'/')+' then return false\nend repeat\nreturn true\nend tell'
        code,raw=osa(script);report['owned_document_origin_absent']=code==0 and raw.strip()=='true'
    if report['status']=='completed' and not (report['owned_read_worker_reaped'] and report['fixture_regular_files_unchanged'] and report.get('owned_document_origin_absent') is True):report.update(status='failed',reason='owned_cleanup_not_confirmed')
    verify();report['stage_inputs_unchanged']=True;print(json.dumps(report),flush=True);h.close()
raise SystemExit(0 if report['status']=='completed' and report['owned_read_worker_reaped'] and report['fixture_regular_files_unchanged'] and report.get('owned_document_origin_absent') is True else 1)
