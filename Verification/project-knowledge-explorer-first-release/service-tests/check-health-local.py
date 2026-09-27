"""No-listener local health and missing-package launch regression."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
root=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(root/'SKILLS-depo/ontology/tests'),str(root/'SKILLS-depo/ontology/scripts')]
from test_explorer_service import Harness,inventory
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
