from pathlib import Path
import sys,json,hashlib,copy,shutil
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
from memory_core import parse_record,render_record,validate_record,json_bytes,sha256
from memory_publish import transaction_payload
now=datetime.now(timezone.utc).isoformat();oldpath='MEMORY/MEM-20260927-63C61316.md';oldraw=(ROOT/oldpath).read_bytes();old=parse_record(oldraw.decode());oldbody=old['body']
newid='MEM-20260927-40EAB117';newpath='MEMORY/'+newid+'.md';op='MEMOP-20260927-collaboration-enable-v3'
reason='Root collaboration is now installed and enabled; current initializer automatically enables selected new/existing projects. Supersede the earlier unadopted-current boundary while preserving its release claim, body, sources and original Task history.'
selected=['SPECS.md','README.md','.agents/skills/task/SKILL.md','.agents/skills/agent-task/SKILL.md','.agents/skills/agent-task/scripts/task_state.py','.agents/skills/agent-task/scripts/orchestration_state.py','.agents/skills/manage-subagent-roles/scripts/role_catalog.py','control_records/collaboration-installation.json']
for package in ['.agents/skills/collaborate','.agents/skills/init-new-project']:
 selected += [p.relative_to(ROOT).as_posix() for p in (ROOT/package).rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tests' not in p.parts]
selected += ['Verification/collaboration-enablement-20260927/'+name for name in ['implementation-verification.json','root-health.json','root-initializer-assess.json','root-initializer-adoption.json','template-final.json','preservation.json','task-validation.json','initializer/result.json','initializer/focused-tests.txt','acceptance-tests.log','guard-repair-result.json']]
assert len(selected)<=200;artifacts=[]
for i,path in enumerate(dict.fromkeys(selected)):
 source=ROOT/path;retained=OUT/'memory-retained'/f'{i:03d}-{source.name}';retained.parent.mkdir(exist_ok=True);shutil.copyfile(source,retained)
 artifacts.append(dict(path=path,sha256=sha256(source.read_bytes()),retained_path=retained.relative_to(ROOT).as_posix()))
receipt=dict(schema_version=1,claim_level='verified_outcome',outcome='passed',applicability='current',command='.venv/bin/python Verification/collaboration-enablement-20260927/verify_implementation.py',observed_at=now,artifacts=artifacts,details={'implementation_checks':25,'deterministic_tests':13,'root_static_enabled':True,'root_owner_profile':'depot-v1','canonical_Task_role_helper_records_preserved':True,'initializer_create_prepare_prior_receipt_recovery_idempotence_conflict':'passed'},limitations=['Static installation and confined deterministic setup/exchange only; no new native pilot or performance claim.','No bulk product propagation or new Task, goal, service, dependency, model or Git publication.'])
receipt_path=OUT/'enablement-verification.json';receipt_path.write_bytes(json_bytes(receipt))
meta=dict(schema_version=1,id=newid,project_id='sys4ai-depot',type='finding',title='Root collaboration enabled and automatic initializer adoption',state='active',created=now,modified=now,claim={'level':'verified_outcome','summary':'Complete collaboration is installed and enabled in the Sys4AI depot root and neutral Template; current initializer automatically enables selected new/existing projects via checked additive module adoption, preserving base receipt editions and custom files.'},applicability=['Sys4AI root collaboration static readiness and future governed Task dispatch','Current initializer create/prepare including selected earlier completed setup receipts','Exact owner compatibility and neutral Template distribution'],limitations=receipt['limitations']+['Actual Task exchange still requires a current manager-produced registered policy, native assignments and scoped grants; root version 1 offers no version 2 broker attestation.','Original generic V1/extra-complex V2 native pilots remain historical evidence distinct from this current deterministic edition.','Cooperative checks supply no OS authentication or raw-filesystem confinement.'],confidence='high',sources=[{'path':receipt_path.relative_to(ROOT).as_posix(),'sha256':sha256(receipt_path.read_bytes()),'locator':'json:/details','kind':'verification'}],origin={'task_id':None,'task_path':None,'execution_id':None,'generation':None,'role':None},lifecycle={'supersedes':[old['metadata']['id']],'superseded_by':None,'reason':reason},publication={'actor_id':'/root','actor_kind':'director','approved_at':now,'operation_id':op})
body='''## Observation and evidence

The depot root now contains a complete exact collaboration package and compatible exact depot-v1 owner with default Task/Agent Task habits. Root collaboration health and the adopted initializer's read-only assessment both report enabled with no diagnostics. Source, root and neutral Template package inventories match. The guard repair recognizes the reviewed current initializer while retaining enabled guards, existing backends and prior verification history.

Current initializer create and prepare-existing automatically enable collaboration, including a selected earlier completed receipt. Existing base edition, operation identity, governance, setup history and project-owned content survive. All thirteen focused deterministic tests pass: current collaboration gates, actual installed depot owner in a confined exchange, installation assessment and initializer create/first prepare/earlier receipt/recovery/idempotence/conflict cases. Twenty-five integration checks confirm the accepted package/version/preservation evidence. No new native pilot was performed.

## Historical release and material correction

PLAN-20260926-40C61316 revision 1 remains completed in TASK-20260926-7F3F57E1 revision 56 with 63 requirements and 17 plan tasks. The predecessor record and retained release evidence preserve that result and the then-unadopted root state. This standalone Director work changes the current installation/default initializer boundary; it does not rewrite the original Task, goal, managed requirements or release receipts. The old note is superseded for current recall, with its body and original provenance preserved.

## Lessons and applicability

Verify installed bytes as a whole: adjacent reusable source and package presence alone cannot establish compatibility or default readiness. A separately reviewed exact v1 provider can be supported without replacing the installed Task owner; never claim v2 broker proof from that interface. The pure initializer assessor uses fixed known provider declarations and frozen reviewed package inventories, executing no unknown target code.

Use the existing setup/module transaction for additive default capability. Preserve base editions, exact history, custom packages and unchanged receipt-owned instructions. Report missing/custom/unsupported combinations as unavailable and stop before overwrite. Durable partial adoption resumes the same frozen operation; repeated completed setup preserves the module identity.

Keep posts, notification and reading receipts separate from incorporation and canonical decisions. Independent candidate/first-review barriers, all-material-type assessment, current exact target versions and existing input-before-wake gates still apply. Manager policy and current native grants remain necessary after enabled installation. Empty notification returns remain unconfirmed. Pending knowledge proposals require separately authorized owners.

## Disposition and validation

The targeted improvement is implemented in the root collaborate installation, current reusable/root initializer, default Task/Agent Task instructions and neutral Template. Reuse the installed collaboration health or initializer assess-collaboration route, then inspect the current manager policy/native grants for real execution. Custom installations require selected review; do not overwrite or infer bulk adoption. Future benefits require later observed evidence; no speed, efficiency, quality or universal reliability advantage is claimed.
'''
new={'metadata':meta,'body':body};validate_record(new,'sys4ai-depot');newcontent=render_record(new)
old['metadata'].update(state='superseded',modified=now,publication={'actor_id':'/root','actor_kind':'director','approved_at':now,'operation_id':op});old['metadata']['lifecycle'].update(superseded_by=newid,reason=reason);assert old['body']==oldbody;validate_record(old,'sys4ai-depot');oldcontent=render_record(old)
payload=transaction_payload(op,'supersede',[{'path':newpath,'expected_sha256':None,'content':newcontent,'reviewed_record_sha256':sha256(newcontent)},{'path':oldpath,'expected_sha256':sha256(oldraw),'content':oldcontent,'reviewed_record_sha256':sha256(oldcontent)}],reason)
(OUT/'memory-reviewed.md').write_text(newcontent);(OUT/'memory-payload.json').write_bytes(json_bytes(payload));print(json.dumps({'record':newpath,'supersedes':oldpath,'retained_artifacts':len(artifacts),'origin':'standalone Director, no Task origin','prior_body_preserved':True}))
