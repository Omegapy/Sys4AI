from pathlib import Path
import json,sys,importlib.util,hashlib,datetime,re
root=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
out=root/'Tasks/Task-plan-integrated-curator-ontology-and-project-initialization-2026-09-13--3ADCACFC/artifacts/orchestration/work/plan_solver_b'
entry=root/'.agents/skills/to-implementation-plan/scripts/plan_state.py'
spec=importlib.util.spec_from_file_location('solver_b_plan_state',entry)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
payload=json.loads((out/'create-input.json').read_text())
result={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':'pure in-memory validation; no managed plan writes','helper':str(entry.relative_to(root)),'helper_sha256':hashlib.sha256(entry.read_bytes()).hexdigest(),'calls':[]}
try:
 ctx=m.resolve_context(str(root),'Implementation_Plans'); result['calls'].append('resolve_context')
 p=m.normalize_plan_input(payload,ctx);result['calls'].append('normalize_plan_input')
 m.ensure_initial_lifecycle_state(p);result['calls'].append('ensure_initial_lifecycle_state')
 directory=m._assign_new_identity(p,set());result['calls'].append('_assign_new_identity')
 p['history']=[m.history_entry(p,revision=1,event_time=p['created_at'],action_id='TO-IP-001',affected_ids=m.stable_record_ids(p),status_before=None,status_after='draft',summary='Created the initial tracked implementation-plan draft.',authority_basis='Current explicit create operation for this project root.')];result['calls'].append('history_entry')
 m.recompute_phase_statuses(p);result['calls'].append('recompute_phase_statuses')
 m.refresh_validation(p,p['updated_at']);result['calls'].append('refresh_validation')
 m.ensure_structurally_valid(p,ctx,directory_name=directory,input_context=True,check_snapshot=True);result['calls'].append('ensure_structurally_valid')
 result.update(structural_status='pass',validation=p['validation'],readiness_findings=m.readiness_findings(p),requirements=len(p['requirements']),acceptance_clauses=sum(len(r['acceptance_criteria']) for r in p['requirements']),phases=len(p['phases']),tasks=len(p['tasks']),all_tasks_planned=all(t['status']=='planned' and not t['evidence'] for t in p['tasks']),all_requirements_active=all(r['status']=='active' and not r['evidence'] for r in p['requirements']))
except Exception as e:
 result.update(structural_status='error',exception=type(e).__name__,message=str(e),details=getattr(e,'details',None))
result['candidate_sha256']=hashlib.sha256((out/'create-input.json').read_bytes()).hexdigest()
trd=(root/payload['sources'][0]['locator']).read_text()
expected=[]
for match in re.finditer(r'^### (REQ-\d{3}) — ([^\n]+)\n(.*?)(?=^### REQ-|^## Decisions)',trd,re.M|re.S):
 rid,title,body=match.groups();expected.append((rid,re.search(r'^- Requirement: (.*)$',body,re.M).group(1),re.findall(r'^- Acceptance: (.*)$',body,re.M),re.findall(r'REQ-\d{3}',re.search(r'^- Depends on: (.*)$',body,re.M).group(1))))
actual=[(r['requirement_id'],r['outcome'],r['acceptance_criteria'],r['dependencies']) for r in payload['requirements']]
result['verbatim_trd_requirement_acceptance_dependency_comparison']='pass' if expected==actual else 'fail'
result['source_freshness']=[{'source_id':s['source_id'],'path':s['locator'],'matches':s['digest']=='sha256:'+hashlib.sha256((root/s['locator']).read_bytes()).hexdigest()} for s in payload['sources'] if s['provenance_mode']=='agent_inspected']
(out/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
