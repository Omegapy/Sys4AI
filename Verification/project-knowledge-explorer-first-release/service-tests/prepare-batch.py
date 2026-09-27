"""Freeze current scoped tests/package into a new absent disposable host stage."""
from pathlib import Path
import hashlib,json,sys
number=sys.argv[1]
assert number.isdigit() and len(number)==2
root=Path('.').absolute();stage=Path('/private/tmp/explorer-service-batch-'+number);stage.mkdir()
paths=list(Path('SKILLS-depo/ontology/scripts').glob('ontology*.py'))
paths += [Path('SKILLS-depo/ontology/tests')/n for n in ('test_explorer_service.py','test_explorer_sessions.py','test_explorer_health.py','support.py','explorer_support.py')]
paths += list(Path('ONTOLOGY-depo').rglob('*'))
paths += [Path('SKILLS-depo/ontology/explorer')/n for n in ('package.json','package-lock.json','THIRD_PARTY_NOTICES.md','BUILD.md')]
paths += list(Path('SKILLS-depo/ontology/explorer/assets').rglob('*'))
rows=[]
for p in sorted(set(paths)):
    if not p.is_file() or '__pycache__' in p.parts:continue
    data=p.read_bytes();q=stage/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
    rows.append({'path':str(p),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
data=Path('Verification/project-knowledge-explorer-first-release/service-tests/host-runner.py').read_bytes()
(stage/'host-runner.py').write_bytes(data);rows.append({'path':'host-runner.py','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
(stage/'inputs.json').write_text(json.dumps({'files':rows},indent=2)+'\n')
job={'command':[str(root/'.venv/bin/python'),'-I','-B',str(stage/'host-runner.py')],'staging_root':str(stage),
     'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256((stage/'inputs.json').read_bytes()).hexdigest()},
     'inputs_count':len(rows),'intended_writes':['Fresh isolated test processes create/remove only /private/tmp/explorer-http-* fixture trees and their explicitly owned loopback listeners, private runtime files, worker/CLI children; every child is reaped.'],
     'source_writes':False,'credentials':'Only process memory and private runtime files; never command/output/evidence.','timeout_seconds':300}
p=Path('Verification/project-knowledge-explorer-first-release/service-tests')/('host-batch-'+number+'.json')
p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),**job}))
