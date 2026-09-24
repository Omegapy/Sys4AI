from pathlib import Path
import json,re,sys,hashlib,importlib.util
ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
source=ROOT/'TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md'
planpath=Path(sys.argv[1]); p=json.loads(planpath.read_text())
reqs={r['requirement_id']:r for r in p['requirements']}
raw=source.read_text(); blocks=re.split(r'^### (REQ-\d{3}) - (.+)$',raw,flags=re.M)
findings=[];n=0
for i in range(1,len(blocks),3):
 rid,title,body=blocks[i:i+3]; body=body.split('\n## ')[0];n+=1
 if rid not in reqs: findings.append(rid+' missing');continue
 r=reqs[rid];req=re.search(r'^- Requirement: (.+)$',body,re.M).group(1)
 acc=re.findall(r'^- Acceptance: (.+)$',body,re.M)
 dep=re.search(r'^- Depends on: (.+)$',body,re.M).group(1)
 deps=re.findall(r'REQ-\d{3}',dep)
 if r['outcome']!=req:findings.append(rid+' outcome wording differs; inspect semantics')
 for a in acc:
  if not any(a in b for b in r['acceptance_criteria']):findings.append(rid+' acceptance text not preserved verbatim: '+a[:90])
 if r['dependencies']!=deps:findings.append(rid+' dependency differs')
req_ids=set(reqs);cov={x['requirement_id']:set(x['task_ids']) for x in p['coverage']['requirement_to_task']}
for r in req_ids:
 if not cov.get(r):findings.append(r+' no task coverage')
 for tid in cov.get(r,[]):
  t=next((t for t in p['tasks'] if t['task_id']==tid),None)
  if not t or r not in t['requirement_ids']:findings.append(r+' reverse task coverage mismatch '+tid)
ats=sorted(set(re.findall(r'AT-\d{2}',json.dumps(p['requirements']))));taskats=sorted(set(re.findall(r'AT-\d{2}',json.dumps(p['tasks']))))
for i in range(1,37):
 a=f'AT-{i:02}'
 if a not in ats:findings.append(a+' missing from requirement inventory')
 if a not in taskats:findings.append(a+' no explicit task acceptance/verification locator')
print(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'plan_sha256':hashlib.sha256(planpath.read_bytes()).hexdigest(),'source_requirements':n,'plan_requirements':len(reqs),'phases':len(p['phases']),'tasks':len(p['tasks']),'AT_requirement_count':len(ats),'AT_task_count':len(taskats),'findings':findings},indent=2))
