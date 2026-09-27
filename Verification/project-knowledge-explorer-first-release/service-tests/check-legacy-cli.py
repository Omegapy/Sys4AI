"""Compare three ordinary legacy reads; only loader identity may differ."""
from pathlib import Path
import hashlib,json,subprocess,sys
root=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(root/'SKILLS-depo/ontology/tests'),str(root/'SKILLS-depo/ontology/scripts')]
from test_explorer_service import Harness,inventory
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
