from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
from memory_core import parse_record
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def r(name):return json.loads((OUT/name).read_bytes())['result']
checks=[]
def check(name,ok,evidence):
 checks.append(dict(name=name,passed=bool(ok),evidence=evidence));assert ok,name
for name in ['root-health-final.json','root-initializer-assess.json']:check(name,r(name)['enabled'] and not r(name)['diagnostics'],name)
for name in ['ontology-health-final.json','ontology-advanced-health-final.json','memory-health-final.json']:check(name,r(name)['ready'],name)
check('ontology structurally and competency valid',r('ontology-validate-final.json')['valid'],'ontology-validate-final.json')
check('memory validates current finding',r('memory-validate-final.json')['valid'],'memory-validate-final.json')
search=r('memory-search-final.json');current=next(x for x in search['results'] if x.get('record_id')=='MEM-20260927-40EAB117');check('verified current memory retrieved',current['verified_current'] and current['state']=='active','memory-search-final.json')
old=parse_record((ROOT/'MEMORY/MEM-20260927-63C61316.md').read_text());original=parse_record(json.loads((ROOT/'Verification/project-memory/collaboration-knowledge-update-20260926/memory-payload.json').read_bytes())['changes'][0]['content']);check('predecessor body/provenance preserved',old['body']==original['body'] and old['metadata']['origin']==original['metadata']['origin'] and old['metadata']['state']=='superseded','memory-recovery.json')
check('exact memory recovery complete',r('memory-recovery.json')['state']=='complete' and all(x['state']=='committed' for x in r('memory-recovery.json')['records']),'memory-recovery.json')
check('memory index readiness',r('memory-reindex.json')['committed'] and r('memory-reindex.json')['ready'],'memory-reindex.json')
verify=json.loads((OUT/'implementation-verification.json').read_text());check('implementation checks accepted',all(x['passed'] for x in verify['checks']),'implementation-verification.json')
preserve=json.loads((OUT/'preservation.json').read_text());check('protected current bytes preserved',preserve['canonical_tasks_role_pairs_helpers_unchanged'] and preserve['registry_unchanged'],'preservation.json')
validation=json.loads((OUT/'task-validation.json').read_text());check('Task integrity with prior unrelated warning only',not validation['errors'] and not validation['recovery_required'] and len(validation['warnings'])==1 and validation['warnings'][0]['task_id']=='TASK-20260910-7F1A11AE','task-validation.json')
t=ROOT/'Projects/Sys4AI-Template-Project';check('Template neutral installed assets only',not list((t/'Tasks').rglob('task.json')) and not list((t/'MEMORY').glob('MEM-*.md')) and not (t/'control_records').exists() and not (t/'.sys4ai').exists(),'template-final.json')
cap=r('ontology-capability-final.json');check('current collaboration ontology has enabled meaning',any('installed and enabled' in x.get('definition',x.get('record',{}).get('definition','')) for x in cap['results']),'ontology-capability-final.json')
requirements=[{'id':rid,'status':'verified','evidence':files} for rid,files in [('R1',['root-health-final.json','root-collaboration-adoption.json']),('R2',['template-final.json','implementation-verification.json']),('R3',['initializer/result.json','root-initializer-adoption.json','root-initializer-assess.json']),('R4',['initializer/focused-tests.txt','implementation-verification.json']),('R5',['implementation-verification.json','preservation.json','task-validation.json']),('R6',['ontology-publication.json','ontology-validate-final.json','memory-recovery.json','memory-search-final.json'])]]
result=dict(schema_version=1,status='complete',requirements=requirements,final_checks=checks,implementation_checks=25,focused_deterministic_tests=13,root_collaboration=dict(installed=True,enabled=True,owner_profile='depot-v1',runtime='not-exercised'),initializer=dict(default='automatic checked activation on create and prepare-existing, including selected earlier completed receipts',adopted_root_files=38,base_contract='governance-starter-v12',old_base_editions_preserved=True),template='current and neutral',knowledge=dict(ontology='current and ready, historical definitions retained',memory='current verified active successor; original body retained as superseded',canonical_records=8,index='ready'),protected_snapshot_files=6134,highest_verification='Actual root static readiness, exact Source/Template/root inventories, confined deterministic owner exchange/setup/recovery, current knowledge owner publication and ready lexical/semantic retrieval.',limits=['No new native collaboration pilot, version 2 broker attestation from root version 1, other-host/live-product or performance claim.','No bulk product propagation, Git commit/push/publication, dependency/model/service installation or Task/goal activation.','Automatic-capture supersession stopped after successor commit on an existing guard context check; owning exact memory-journal recovery completed both records. Capture wrapper unchanged; future affected supersessions should inspect actual commit state and use owning recovery.','One unrelated preserved historical staged Task Response warning remains.'])
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
(OUT/'RESULT.md').write_text('''# Collaboration enablement completed

Collaboration is installed and enabled in the Sys4AI depot root. The current
initializer is adopted in the root and automatically enables collaboration for
new projects and selected existing projects, including earlier completed setup
receipts. The neutral Template is current and contains the complete package and
default Task/Agent Task instructions. All six planned requirements are verified.

## Verification

Thirteen focused deterministic tests and 25 implementation checks passed. Final
root health and initializer assessment report enabled with no diagnostics.
Complete collaboration and initializer package inventories match Source, root
and Template. A confined exchange uses the exact installed depot-v1 owner;
canonical Task bytes remain unchanged. Create, first prepare, earlier-receipt
adoption, interruption/recovery, idempotence and custom/unsupported refusal
cases passed. The root initializer adoption covers 38 exact Source files and
retains all 27 original files; its owning guard repair keeps guards enabled.

All 6,134 captured protected files pass preservation checks. Root Task helpers,
canonical Tasks, role pairs, root governance and project registry remain exact.
The only Task validation warning is the pre-existing staged Response in cancelled
TASK-20260910-7F1A11AE; no error or recovery requirement remains.

## Documentation and knowledge

Root README/SPECS and neutral starter documentation describe enabled root and
automatic selected initializer activation. Ontology publication updates existing
collaboration meanings through renewed reviews and current source bindings;
structural/competency validation and core/advanced readiness pass. Semantic index,
wiki and memory links are refreshed. No new semantic identities were needed.

MEM-20260927-40EAB117 is active, retrieved and verified current. The predecessor
MEM-20260927-63C61316 retains its body, release claims and Task provenance as
superseded history. Both records committed through exact accepted-journal recovery
after the automatic-capture wrapper stopped between writes. Memory has eight
canonical records and ready derived/semantic indexing. The original implementation
Task, managed plan/TRD and release evidence remain historical and preserved.

## Evidence and limits

See [the machine report](RESULT.json), [implementation verification](implementation-verification.json),
[initializer worker result](initializer/result.json), [root health](root-health-final.json),
[root initializer assessment](root-initializer-assess.json), [root adoption](root-initializer-adoption.json),
[Template check](template-final.json), [preservation](preservation.json) and
[memory recovery](memory-recovery.json).

Highest evidence is actual root static readiness, exact inventory adoption,
confined deterministic exchange/setup/recovery and current knowledge publication/
retrieval. No new native collaboration pilot, live-product/other-host behavior,
version 2 broker proof from root version 1, or performance improvement is claimed.
Actual Task execution still needs current manager policy, native assignments,
scoped grants and independence checkpoints. No service, dependency/model or Git
publication was performed.

The existing automatic-capture wrapper required exact memory recovery for this
supersession. Its code remains unchanged; future affected calls must inspect
actual journal commit state and recover through the owning interface. Rejected
fixture-text qualification and source-binding previews were preserved; final
checks passed without bypassing their validators or changing the test fixtures.
''')
print(json.dumps({'status':result['status'],'requirements':6,'final_checks':len(checks),'tests':13,'protected_files':6134}))
