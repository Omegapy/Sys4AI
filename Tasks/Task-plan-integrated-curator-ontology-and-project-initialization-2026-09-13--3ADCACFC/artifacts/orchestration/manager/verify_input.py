import sys,pathlib,json,re,hashlib,importlib.util
r=pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI');path=pathlib.Path(sys.argv[1]);payload=json.loads(path.read_text());source=r/'TRDs/trd_integrated-project-curator-ontology-and-project-initializati_2026-09-13.md';text=source.read_text()
errors=[];reqs={x['requirement_id']:x for x in payload['requirements']};count=0
for match in re.finditer(r'^### (REQ-\d+) — (.*?)\n(.*?)(?=^### REQ-|^## Decisions)',text,re.M|re.S):
 rid,title,body=match.groups();clauses=re.findall(r'^- Acceptance: (.+)$',body,re.M);count+=len(clauses)
 if rid not in reqs:errors.append(rid+' missing');continue
 for i,c in enumerate(clauses,1):
  if c not in reqs[rid]['acceptance_criteria']:errors.append(rid+' clause '+str(i)+' not retained verbatim; semantic review required')
 dep=re.search(r'^- Depends on: (.+)$',body,re.M).group(1);deps=[] if dep=='None.' else dep.split(', ')
 if reqs[rid]['dependencies']!=deps:errors.append(rid+' dependency mismatch')
 if reqs[rid].get('status')!='active' or reqs[rid].get('evidence'):errors.append(rid+' contains premature completion/evidence')
if len(reqs)!=14:errors.append('Expected exactly 14 original requirements')
s=importlib.util.spec_from_file_location('planning_validator',r/'.agents/skills/to-implementation-plan/scripts/plan_state.py');p=importlib.util.module_from_spec(s);sys.modules[s.name]=p;s.loader.exec_module(p)
ctx=p.resolve_context(str(r),'Implementation_Plans');plan=p.normalize_plan_input(payload,ctx);p.ensure_initial_lifecycle_state(plan);directory=p._assign_new_identity(plan,set());plan['history']=[p.history_entry(plan,revision=1,event_time=plan['created_at'],action_id='TO-IP-001',affected_ids=p.stable_record_ids(plan),status_before=None,status_after='draft',summary='Created the initial tracked implementation-plan draft.',authority_basis='Current explicit create operation for this project root.')];p.recompute_phase_statuses(plan);p.refresh_validation(plan,plan['updated_at']);p.ensure_structurally_valid(plan,ctx,directory_name=directory,input_context=True,check_snapshot=True)
result={'input_path':str(path),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'requirement_count':len(reqs),'acceptance_clause_count':count,'phase_count':len(plan['phases']),'task_count':len(plan['tasks']),'verbatim_clause_findings':errors,'helper_validation':plan['validation'],'readiness_findings':p.readiness_findings(plan),'mutation':False,'note':'Synthetic plan identity existed only in memory and is not a published ID.'};print(json.dumps(result,indent=2))
if errors or any(x.get('severity')=='error' and x.get('status')=='open' for x in result['helper_validation']['findings']):sys.exit(1)
