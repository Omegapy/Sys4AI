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
baseline=subprocess.run(['git','show','HEAD:SKILLS-depo/ontology/scripts/ontology.py'],cwd=root,capture_output=True,check=True).stdout
h=Harness();rows=[]
try:
    cli=h.scripts/'ontology.py';current=cli.read_bytes();before=inventory(h.root)
    for args in [['term','Alignment'],['search','fixture'],['read','urn:sys4ai:ontology:project:explorer-fixture:entry-00000']]:
        runs=[]
        for data in [current,baseline]:
            cli.write_bytes(data)
            done=subprocess.run([sys.executable,'-B',str(cli),'--project-root',str(h.root),*args],capture_output=True,timeout=10)
            assert done.returncode==0 and not done.stderr
            runs.append(json.loads(done.stdout))
        snapshots=[entry['context'].pop('snapshot_sha256') for entry in runs]
        assert all(len(value)==64 for value in snapshots) and snapshots[0]!=snapshots[1]
        assert runs[0]==runs[1]
        rows.append({'operation':args[0],'exit_code':0,'same_knowledge_and_metadata_except_loader_snapshot':True})
    cli.write_bytes(current);assert before==inventory(h.root)
    result={'status':'passed','current_cli_sha256':hashlib.sha256(current).hexdigest(),
        'baseline_cli_sha256':hashlib.sha256(baseline).hexdigest(),
        'baseline_source':'Git HEAD ontology.py read-only comparison; both commands use identical current other-helper bytes and disposable canonical fixture.',
        'cases':rows,'canonical_fixture_unchanged':True,
        'expected_difference':'Only context.snapshot_sha256 differs because canonical retrieval binds actual ontology helper bytes, including changed CLI.',
        'qualification':'Three ordinary reads plus separately exercised workbench help. No authoring mutation, workbench retirement or broad optional-backend certification claimed.'}
finally:h.close()
print(json.dumps(result,sort_keys=True))

verify()
