import hashlib,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
from memory_core import render_record,validate_record,json_bytes,sha256
from memory_publish import transaction_payload
release=ROOT/'Verification/shared-agent-billboards';audit=json.loads((release/'requirement-evidence.json').read_text());result=json.loads((release/'release-worker-result.json').read_text())
refs={}
def walk(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):refs[(v['path'],v['sha256'])]=v
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(audit)
for ref in result['final_outputs']:refs[(ref['path'],ref['sha256'])]=ref
for (raw,want),ref in refs.items():assert hashlib.sha256((ROOT/raw).read_bytes()).hexdigest()==want,raw
assert {r['requirement_id'] for r in audit['requirements']}=={f'REQ-{i:03d}' for i in range(1,64)}
assert {t for r in audit['requirements'] for t in r['plan_task_ids']}=={f'TASK-{i:03d}' for i in range(1,18)}
assert not result['blockers']
task_path='Tasks/Task-implement-shared-agent-billboards-revision-1-2026-09-26--7F3F57E1/task.json';task=json.loads((ROOT/task_path).read_text());assert task['status']=='completed' and task['revision']==56
now=datetime.now(timezone.utc).isoformat();selected=[task_path,'Tasks/Task-implement-shared-agent-billboards-revision-1-2026-09-26--7F3F57E1/responses/Task-Response-0055-2026-09-26T19-30-29-06-00.md','Tasks/Task-implement-shared-agent-billboards-revision-1-2026-09-26--7F3F57E1/artifacts/orchestration/manager/main-terminal-validation-v2.json','Verification/shared-agent-billboards/RELEASE.md','Verification/shared-agent-billboards/requirement-evidence.json','Verification/shared-agent-billboards/release-worker-result.json','Verification/shared-agent-billboards/comparison/results.json','SKILLS-depo/collaborate/SKILL.md']
artifacts=[]
for index,raw in enumerate(selected):
 src=ROOT/raw;retained=OUT/'retained'/f'{index:02d}-{src.name}';shutil.copyfile(src,retained);assert src.read_bytes()==retained.read_bytes();artifacts.append({'path':raw,'sha256':sha256(src.read_bytes()),'retained_path':retained.relative_to(ROOT).as_posix()})
receipt={'schema_version':1,'claim_level':'verified_outcome','outcome':'passed','applicability':'current','command':'.venv/bin/python Verification/project-memory/collaboration-knowledge-update-20260926/prepare_memory.py','observed_at':now,'artifacts':artifacts,'details':{'task_status':'completed','task_revision':56,'requirements_exact':63,'plan_tasks_exact':17,'current_refs_inspected':len(refs),'hash_mismatches':0,'native_evidence':'Existing actual native pilot/baseline evidence accepted in the completed Task; this is current source/evidence inspection, not a new native run.'},'limitations':['Recorded artifacts only; no root/product collaboration adoption or new native/physics/performance claim.','Generic V1/enabled V2 native results and current V4 deterministic/adoption evidence remain separate.']}
receipt_path=OUT/'release-verification.json';receipt_path.write_bytes(json_bytes(receipt))
record_id='MEM-20260927-63C61316';op='MEMOP-20260927-collaboration-release-handoff-v1'
metadata={'schema_version':1,'id':record_id,'project_id':'sys4ai-depot','type':'finding','title':'Shared agent billboard collaboration release and evidence boundaries','state':'active','created':now,'modified':now,'claim':{'level':'verified_outcome','summary':'PLAN-20260926-40C61316 revision 1 completed in TASK-20260926-7F3F57E1 revision 56 with 63 requirement/17 plan-task coverage, scoped Template distribution and verified disposable/native evidence; live depot/product collaboration remains unadopted.'},'applicability':['Sys4AI depot reusable collaboration capability and selected future adoption','Governed native Task collaboration evidence and bounded recovery','Exact current installed-owner compatibility and knowledge publication separation'],'limitations':receipt['limitations']+['One matched comparison established no causal speed, efficiency or quality advantage; token/full-prompt telemetry unavailable.','Cooperative filesystem visibility/identity checks are not OS authentication or raw-filesystem confinement.','This note publishes accepted release knowledge; it does not reopen a Task, install the capability, execute pending proposals or grant publication authority.'],'confidence':'high','sources':[{'path':receipt_path.relative_to(ROOT).as_posix(),'sha256':sha256(receipt_path.read_bytes()),'locator':'json:/details','kind':'verification'}],'origin':{'task_id':task['task_id'],'task_path':task_path,'execution_id':'EXEC_BILLBOARDS_R1','generation':1,'role':None},'lifecycle':{'supersedes':[],'superseded_by':None,'reason':None},'publication':{'actor_id':'/root','actor_kind':'director','approved_at':now,'operation_id':op}}
body='''## Verified handoff

Shared agent billboard collaboration is released as reusable source under SKILLS-depo/collaborate and checked neutral Template content. Completed Task TASK-20260926-7F3F57E1 records all 17 plan tasks, 63 requirements, three verified main subtasks and five definition-of-done criteria. Final Task validation has no errors or recovery requirement; an unrelated historical Curator staged-response warning remains preserved.

## Evidence levels and scope

Four focused deterministic bundles and affected correction checks, actual generic and extra-complex native pilots, one clean same-packet/team/settings baseline, scoped overview integration, 53 exact source-to-Template mappings and two disposable adoptions support the recorded release. Both original analyses met the same five semantic criteria. Different timing provenance, validation and recovery workloads prevent performance or quality inference.

The actual generic pilot used V1 and the enabled extra-complex pilot V2. Current V4 and overview changes have targeted deterministic, installed-adoption and scoped-read evidence. No final V4 native replay is claimed. The depot active .agents/skills installation and live products remain unadopted.

## Reusable lessons

- Verify the actual selected project's installed owner bytes before execution; neighboring reusable source is not proof of the installed provider.
- Keep substantive native notices closed until independent candidate and first-review barriers pass. Operational labels cannot make authored draft content harmless.
- Assess every material message type against its exact affected version. Candidate supersession invalidates affected reviews, synthesis and acceptance while preserved history remains attributable.
- Keep immutable collaboration posts, collaboration reading receipts and recipient-observed notification receipts distinct. Empty {} or null sender returns supply no success confirmation. Reported reading, comprehension claims and independently inspected incorporation require separate evidence.
- Bind material same-ID inputs through the existing owner gate before a wake. Raw pending_init and uncertain delivery stay explicit; neither is a supported stopped-state receipt.
- A collaboration owner snapshot is selected evidence for an existing responsible owner. A pending collaboration knowledge proposal is neither memory publication nor ontology approval.

## Operational recall

Read SPECS.md section Shared agent billboards and collaboration release for current project-local meanings, SKILLS-depo/collaborate/SKILL.md for the reusable workflow, and Verification/shared-agent-billboards/RELEASE.md for proof chronology and limitations. Ontology discovery does not install the source or invoke an operation. Knowledge records, Task state, native goals and publication grants remain separate.

## Retained proof

The cited current verification receipt binds exact retained copies of the canonical completed Task, final Response, terminal inspection, release/audit/result/comparison and reusable skill. The current inspection matched all 49 unique direct audit/final-output references without mismatch. Future source changes require current reinspection; retained bytes preserve historical support without claiming the later version was exercised.
'''
record={'metadata':metadata,'body':body};validate_record(record,'sys4ai-depot');content=render_record(record);path='MEMORY/'+record_id+'.md';assert not (ROOT/path).exists();payload=transaction_payload(op,'publish',[{'path':path,'expected_sha256':None,'content':content,'reviewed_record_sha256':sha256(content)}],'Explicit user update request: publish the evidence-backed collaboration release handoff and reusable limits through current project Director authority.')
(OUT/'memory-reviewed.md').write_text(content);(OUT/'memory-payload.json').write_bytes(json_bytes(payload));print(json.dumps({'record':path,'reviewed_sha256':sha256(content),'retained_artifacts':len(artifacts),'inspected_refs':len(refs),'source_receipt':receipt_path.relative_to(ROOT).as_posix(),'origin':'Completed real Task; standalone Director publication, no Task mutation.'}))
