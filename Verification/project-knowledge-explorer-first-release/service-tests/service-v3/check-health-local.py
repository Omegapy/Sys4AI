"""Frozen disposable test executor: outputs evidence, edits no project files."""
import hashlib,importlib.abc,importlib.util,io,json,os,signal,stat,subprocess,sys,time,types,unittest
from pathlib import Path
stage=Path('/private/tmp/explorer-service-v3-batch-01')
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


root=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
Harness=test_explorer_service.Harness
inventory=test_explorer_service.inventory
h=Harness();result={}
try:
    source=h.root/'SPECS.md';source.write_text(source.read_text()+'\nChanged selected fixture source.\n')
    before=inventory(h.root)
    facts=h.package.modules['ontology_explorer_health'].inspect(h.package,h.assets,h.root)
    assert facts['configured'] is True and facts['readable'] is True and facts['stale'] is True
    assert facts['running'] is None and facts['wrong_project'] is None and not facts['unavailable']
    assert before==inventory(h.root)
    (h.explorer/'assets/manifest.json').unlink()
    launch=subprocess.run([sys.executable,'-B',str(h.scripts/'ontology.py'),'--project-root',str(h.root),'explore'],capture_output=True,text=True,timeout=8)
    response=json.loads(launch.stdout)
    assert launch.returncode==2 and response['error']=='package_incomplete' and 'BUILD.md' in response['maintenance']
    assert not (h.root/'.sys4ai/ontology/explorer').exists()
    result={'status':'passed','stale_source_remains_readable':True,'health_no_runtime_files':True,
            'missing_bundle_launch_exit':launch.returncode,'missing_bundle_error':response['error'],'maintenance_route_present':True,
            'source_inputs':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in
                [root/'SKILLS-depo/ontology/scripts'/name for name in ('ontology_explorer.py','ontology_explorer_worker.py','ontology_explorer_health.py','ontology.py')]]}
finally:h.close()
print(json.dumps(result,sort_keys=True))

verify()
