from pathlib import Path
import sys,time,json
OUT=Path(__file__).parent;ROOT=OUT/'root-copy';sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_core import canonical_bytes,sha256
from ontology_standards import _prepare,infer,infer_diagnostic,validate
from ontology_profiles import certify
from ontology_health import advanced_health
from check_ontology import run_checks
from ontology_shacl import record_constraints
summary=[]
def observe(name,fn):
 started=time.monotonic();result=fn();raw=canonical_bytes(result);(OUT/(name+'.json')).write_bytes(raw)
 row={'operation':name,'status':result.get('status'),'complete':result.get('complete'),'valid':result.get('valid'),
 'elapsed_seconds':round(time.monotonic()-started,4),'bytes':len(raw),'sha256':sha256(raw),'worker':result.get('worker')}
 summary.append(row);print(json.dumps(row),flush=True);return result
cert=observe('root-copy-certification',lambda:certify(ROOT));assert cert['status']=='validated'
config,payload,p=_prepare(ROOT);constraints=record_constraints(p.records)
(OUT/'root-copy-constraints.json').write_bytes(canonical_bytes(constraints))
(OUT/'root-copy-payload.json').write_bytes(canonical_bytes(payload))
result=observe('root-copy-shacl',lambda:validate(ROOT));assert result['status']=='conformant' and result['complete'],result
result=observe('root-copy-infer-diagnostic',lambda:infer_diagnostic(ROOT));assert result['status']=='ok' and result['complete'] and result['trusted'],result
result=observe('root-copy-infer-full',lambda:infer(ROOT));assert result['status']=='output_limit' and not result['complete'],result
result=observe('root-copy-infer-selected',lambda:infer(ROOT,premise_ids=[p.namespace+'curator-function-review'],goals=[[p.namespace+'curator-function-review','http://www.w3.org/1999/02/22-rdf-syntax-ns#type','urn:sys4ai:ontology:core:Capability']]));assert result['complete'] and result['conclusions'][0]['classification']=='entailed',result
result=observe('root-copy-competencies',lambda:run_checks(ROOT));assert result['valid'] and len(result['competency']['results'])==48,result
result=observe('root-copy-health',lambda:advanced_health(ROOT,scope='canonical',level='operational',required=['standards','inference']));assert result['ready'],result
before=json.loads((OUT/'root-copy-inputs.json').read_text())['protected'];after={str(x.relative_to(ROOT)):sha256(x) for x in ROOT.rglob('*') if x.is_file() and '.venv-ontology-standards' not in x.parts and not str(x.relative_to(ROOT)).startswith('control_records/ontology/profile-setup/')}
assert before==after,{'changed':[p for p in before if before[p]!=after.get(p)]}
(OUT/'root-copy-summary.json').write_bytes(canonical_bytes({'observations':summary,'protected_unchanged':True,'targets':len(constraints),'groups':len({canonical_bytes(v) for v in constraints.values()}),'limits':config['limits'],'actual_runtime':'copied existing certified runtime; recertified; no provisioning'}))
