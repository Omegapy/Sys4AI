import json,hashlib,re
from pathlib import Path
from events import ROOT,TASK,MANAGER,ref,current
D=ROOT/'Verification/integrated-curator-ontology'
a=json.loads((D/'acceptance-matrix.json').read_text());f=json.loads((D/'final-manifest.json').read_text());p=json.loads((D/'plan-task-evidence.json').read_text())
plan=json.loads((ROOT/a['plan_source']['path']).read_text())
assert ref(a['plan_source']['path'])==a['plan_source']
assert a['plan_source']['sha256']=='bc30f80e0a9d8cc40406149510e40520b33077607ab64190fc128f77bba0abd5'
assert a['all_requirements_satisfied'] and f['all_requirements_satisfied'] and p['all_requirements_satisfied']
assert not a['pending_gate'] and not f['pending']
assert len(a['requirements'])==14 and all(x['status']=='supported' for x in a['requirements'])
assert len(a['clauses'])==34 and all(x['status']=='supported' for x in a['clauses'])
expected={r['requirement_id']+'-AC'+str(i+1).zfill(2):text for r in plan['requirements'] for i,text in enumerate(r['acceptance_criteria'])}
assert {r['id']:r['clause'] for r in a['clauses']}==expected
assert len(p['tasks'])==23 and all(x['execution_evidence_status'] in {'supported','supported_with_retained_owner_blocker'} for x in p['tasks'])
assert not p['canonical_plan_mutated']
checked={}
def check(x):
 if isinstance(x,dict):
  if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str):
   q=ROOT/x['path'];assert q.is_file(),str(q);h=hashlib.sha256(q.read_bytes()).hexdigest();assert h==x['sha256'],x['path'];checked[x['path']]=h
  for v in x.values():check(v)
 elif isinstance(x,list):
  for v in x:check(v)
for rows in [a['evidence_catalog']]+[x['evidence'] for x in a['clauses']]+[x['evidence'] for x in p['tasks']]:check(rows)
for group in ('sources','root_artifacts','template_artifacts','derived_artifacts','report_artifacts'):check(f[group])
check(f['evidence']);check(f['preservation']['unchanged_current_hashes']);check(f['registry']);check(f['template_state'])
assert not f['preservation']['unaccounted']
files=['REPORT.md','acceptance-matrix.json','plan-task-evidence.json','final-manifest.json','implementation/final-report-result.md']
report_refs=[ref(str((D/x).relative_to(ROOT))) for x in files]
assert all((ROOT/x['path']).stat().st_size<=250000 for x in report_refs)
criteria=[]
for req,text in zip(plan['requirements'],current()['definition_of_done']):
 clauses=[x for x in a['clauses'] if x['requirement']==req['requirement_id']]
 assert clauses
 criteria.append({'criterion':text,'evidence':req['requirement_id']+': '+' '.join(x['id']+' '+x['finding'] for x in clauses)+' See acceptance-matrix.json exact clause evidence and final-manifest.json current artifact hashes.'})
report={'status':'passed','task_revision_inspected':current()['revision'],'requirements':14,'clauses':34,'plan_tasks':23,'plan_revision_preserved':1,'current_unique_paths_reopened':len(checked),'manifest_groups':{k:len(f[k]) for k in ('sources','root_artifacts','template_artifacts','derived_artifacts','report_artifacts')},'reports':report_refs,'criteria':criteria,'inspection':'All exact original clause texts, evidence digests, current artifact rows and unchanged preservation rows reopened; scoped repairs and original predecessor history retained. Actual authenticated browser read/source navigation and intentionally retained foreground lifecycle reviewed separately from publication.','limitations':['Default full inference proof export retains unchanged bounded output_limit; full-selected-closure diagnostic and scoped proof are supported.','Ten pending Curator events retained; metadata collection is not source validation or completed dispatch.','Historical staged response retains current-owner blocker permitted by requirement; no cleanup was asserted.','Optional canonical memory capture remains outside current manager scope and pending prior owner reconciliation.','Service intentionally retained at user request; no service installation, autostart, background AI or unselected product/Git publication.']}
q=MANAGER/'completion-inspection-20260916.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','paths':len(checked),'reports':report_refs,'inspection':ref(q)},indent=2))
