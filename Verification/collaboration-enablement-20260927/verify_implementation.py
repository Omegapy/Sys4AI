from pathlib import Path
import json,hashlib,ast
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail));assert ok,name
for name in ['collaborate','init-new-project']:
 src=ROOT/'SKILLS-depo'/name
 inventory={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 for title,parent in [('root',ROOT/'.agents/skills'),('Template',ROOT/'Projects/Sys4AI-Template-Project/.agents/skills')]:
  dst=parent/name;actual={p.relative_to(dst).as_posix():sha(p) for p in dst.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
  check(name+' complete exact '+title,actual==inventory,dict(files=len(inventory),missing=sorted(set(inventory)-set(actual)),extra=sorted(set(actual)-set(inventory))))
for path in ['root-health.json','root-initializer-assess.json']:
 d=json.loads((OUT/path).read_text());check(path,d['exit_code']==0 and d['result']['enabled'] and not d['result']['diagnostics'])
p=json.loads((OUT/'preservation.json').read_text());check('Task helpers records roles registry preserved',p['canonical_tasks_role_pairs_helpers_unchanged'] and p['registry_unchanged'])
d=json.loads((OUT/'template-final.json').read_text());check('Template updater current',d['exit_code']==0 and d['result']['status']=='current')
d=json.loads((OUT/'initializer/result.json').read_text());check('Initializer confined cases',not d['blockers'] and d['checks'][0]['tests']==3 and d['checks'][0]['outcome']=='passed')
for row in d['inputs']+d['evidence']:
 check('Worker current '+row['path'].split('/')[-1],sha(Path(row['path']))==row['sha256'])
check('Current profile affected scope/canonical gates', '\nOK\n' in (OUT/'acceptance-tests.log').read_text())
check('Guard exact initializer repair',json.loads((OUT/'guard-repair-result.json').read_text())['status']=='complete')
result=dict(schema_version=1,status='verified',checks=checks,observed_checks=len(checks),root_owner_profile='depot-v1',default_initializer_contract='governance-starter-v12',deterministic_tests={'acceptance':4,'gate_corrections':4,'installation':2,'initializer':3},actual_gate_observation={'gate_corrections':'Observed tools reported 4 passing in 8.507s','installation':'Observed tools reported 2 passing in 1.748s'},limits=['Static Root readiness and deterministic confined exchange/setup, no new native pilot.','Original Task/goal/managed plan and registry preserved; no live product bulk propagation or Git publication.'])
(OUT/'implementation-verification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(checks),'tests':13}))
