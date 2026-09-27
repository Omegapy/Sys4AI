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

# This observer reads only the actual owned Service instance; it does not patch
# any production method or expose credential fields. The command itself performs
# the normal explicit --open path and its normal stop/cleanup.
import gc,threading
h=test_explorer_service.Harness(identity='explorer-browser-smoke')
before=test_explorer_service.inventory(h.root)
started=time.monotonic();done=threading.Event();observed={};held=[]
def observe():
    service=None;seen_context=False;reported=False
    while not done.wait(.02):
        if service is None:
            for obj in gc.get_objects():
                if isinstance(obj,h.module.Service) and getattr(obj,'root',None)==h.root:
                    service=obj;held.append(obj);break
        if service is None:continue
        process=getattr(getattr(service,'worker',None),'process',None)
        if process is not None:observed['owned_process']=process
        active=getattr(service,'active',None)
        if active is not None and getattr(active,'operation',None)=='context':seen_context=True
        connections=list(getattr(service,'connections',{}).values())
        if any(c.operation=='context' for c in connections):seen_context=True
        if not reported and getattr(service,'sessions',{}) and seen_context and active is None:
            reported=True
            observed['ready']=True
            print(json.dumps({'kind':'browser_ready','origin':service.origin,
                'expected_clean_url':service.origin+'/#/p/explorer-browser-smoke/overview',
                'bootstrap_consumed':True,'context_request_completed':True,
                'inspection':'Inspect only this credential-free URL and recorded project text; no credentials were emitted.'}),flush=True)
        if time.monotonic()-started>150:
            service.stopping=True
            if not reported:print(json.dumps({'kind':'browser_not_ready','reason':'No completed browser context request observed; do not inspect a potentially uncleared bootstrap tab.'}),flush=True)
            return
monitor=threading.Thread(target=observe,daemon=True);monitor.start();exit_code=2
try:
    exit_code=h.module.command(['--project-root',str(h.root),'explore','--open'],h.package,h.assets)
finally:
    done.set();monitor.join(2)
    for service in held:service.close()
    unchanged=before==test_explorer_service.inventory(h.root)
    process=observed.get('owned_process')
    reaped=process is None or process.poll() is not None
    verify()
    print(json.dumps({'kind':'browser_cleanup','exit_code':exit_code,'context_observed':observed.get('ready',False),
        'owned_worker_reaped':reaped,'fixture_regular_files_unchanged':unchanged,'stage_inputs_unchanged':True}),flush=True)
    h.close()
raise SystemExit(exit_code)
