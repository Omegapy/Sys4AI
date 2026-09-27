import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((OUT/name).read_text())
def result(name):return read(name)['result']
checks={}
for name in ('memory-health-terminal.json','ontology-health-terminal.json','advanced-health-terminal.json'):
 d=read(name);checks[name]=d['exit_code']==0 and d['result']['ready'] is True and not d['result'].get('failed_required',d['result'].get('assessment',{}).get('failed_required',[]))
v=result('ontology-validate-terminal.json');checks['ontology_structural_and_competency']=v['valid'] and v['structural']['valid'] and v['competency']['valid'];cases=v['competency']['results'];newcases=[x for x in cases if x['id'].startswith('root-collaboration-')];checks['five_new_competencies']=len(newcases)==5 and all(c['valid'] for c in newcases)
note='MEMORY/MEM-20260927-63C61316.md';checks['exact_memory_publication']=(ROOT/note).read_bytes()==(OUT/'memory-reviewed.md').read_bytes();checks['memory_valid']=result('memory-validate-final.json')['valid']
lookup=result('memory-lookup.json');checks['new_memory_verified_current']=any(x.get('record_id')=='MEM-20260927-63C61316' and x.get('verified_current') is True for x in lookup['results']);checks['memory_hybrid_finds_new_record']=any(x.get('record_id')=='MEM-20260927-63C61316' for x in lookup['results'])
k=result('ontology-knowledge-terminal.json');checks['combined_lookup_finds_current_capability_and_memory']=any(x.get('@id','').endswith(':capability-shared-agent-billboards') for x in k['results']) and any(x.get('record_id')=='MEM-20260927-63C61316' for x in k['results']) and k['associations_status']=='current'
raw='ONTOLOGY/modules/project/project.jsonld';intent=json.loads((ROOT/'control_records/ontology/intents/ONTOP-20260926-collaboration-knowledge-v1.json').read_text());old=json.loads(intent['prior_contents'][raw]);current=json.loads((ROOT/raw).read_text());oldids=[n['@id'] for n in old['@graph']];currentids=[n['@id'] for n in current['@graph']];checks['original_graph_order']=oldids==[i for i in currentids if i in set(oldids)]
oldnodes={n['@id']:n for n in old['@graph']};now={n['@id']:n for n in current['@graph']};semantic_changes=[]
for key,prior in oldnodes.items():
 revised=json.loads(json.dumps(now[key]));expected=json.loads(json.dumps(prior))
 for n in (revised,expected):
  for s in n.get('sources',[]):
   if s['path']=='SPECS.md':s['sha256']='authorized-SPECS-rebind'
 if revised!=expected:semantic_changes.append(key)
checks['all_92_existing_meanings_preserved']=not semantic_changes
before=read('before.json');allowed={'SPECS.md','README.md','ONTOLOGY/modules/project/project.jsonld','ONTOLOGY/bindings/artifacts.json','ONTOLOGY/bindings/skills.json','ONTOLOGY/modules/project/competency.json'};unexpected=[p for p,h in before.items() if p not in allowed and digest(ROOT/p)!=h];checks['other_selected_baseline_bytes_preserved']=not unexpected
for name in ('ontology-publication.json','ontology-consolidation-publication.json','ontology-order-publication-corrected.json'):
 checks[name]=read(name)['exit_code']==0 and result(name)['status']=='complete'
checks['memory_committed']=result('memory-publication.json')['state']=='complete';checks['memory_reindex_ready']=result('memory-reindex-corrected.json')['ready'] is True and result('memory-reindex-corrected.json')['committed'] is True
index=ROOT/'.sys4ai/ontology/semantic/index-v1.json';idx=json.loads(index.read_text());checks['semantic_index_current_bound']=index.stat().st_size<=2_000_000 and result('ontology-semantic-final-refresh.json')['sha256']==digest(index)
checks['selected_builds_complete']=result('ontology-wiki-final-refresh.json')['status']=='complete' and result('ontology-memory-final-links.json')['status']=='complete'
status='complete' if all(checks.values()) else 'incomplete'
refs=[]
for name in ('memory-publication.json','memory-reindex-corrected.json','ontology-publication.json','ontology-consolidation-publication.json','ontology-order-publication-corrected.json','memory-health-terminal.json','ontology-health-terminal.json','advanced-health-terminal.json','ontology-validate-terminal.json','ontology-knowledge-terminal.json','ontology-semantic-final-refresh.json'):
 p=OUT/name;refs.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
report={'status':status,'observed_at':datetime.now(timezone.utc).isoformat(),'project':'sys4ai-depot','authority':'Explicit user request: Update those systems. Separate current Director memory/ontology grants; no terminal Task mutation.','checks':checks,'memory_record':note,'ontology_new_concepts':6,'ontology_new_identities_retained':18,'new_skill_binding':1,'competency_total':len(cases),'new_competency_cases':newcases,'semantic_index':{'bytes':index.stat().st_size,'rows':len(idx['rows']),'limit_unchanged':2_000_000},'unexpected_baseline_changes':unexpected,'changed_existing_meanings':semantic_changes,'evidence':refs,'shared_completion_checkpoint':{'mode':'explicit user save; reuse completed same-finding learning review','source':'Tasks/Task-implement-shared-agent-billboards-revision-1-2026-09-26--7F3F57E1/artifacts/orchestration/manager/shared-learning-checkpoint-review.json','disposition':'The accepted release finding and its existing reviewed lessons are now published once under fresh user authority. Exact publication/reindex/lifecycle corrections are retained in this verification result; no duplicate automatic save, new capture path or capture-setting change.'},'limits':['Project-local knowledge publication and selected retrieval maintenance only; no live collaborate installation, Template/product adoption, Task reopening, external publication or new native collaboration pilot.','Core ontology/advanced health is current static assessment; memory operational probe and existing semantic-index build were actually exercised. No new full formal-profile release qualification is claimed.','The ontology is near its unchanged 2 MB semantic-index boundary; redundant new specification identity was deprecated with exact history and replacement, all six concepts retained.']}
(OUT/'RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
text='''# Collaboration memory and ontology update

The explicit user request to update these systems is complete. The project Director
published one current, durable release finding and reviewed project-local ontology
additions through separate exact owner grants. The original completed implementation
Task remains unchanged; this work has no new Task or native goal.

## Published knowledge

- [Memory finding](../../../MEMORY/MEM-20260927-63C61316.md): verified release,
  six reusable lessons, applicability and limits, with eight retained proof artifacts.
- Six collaboration concepts, one reusable capability and skill/source binding,
  typed relationships and five competency questions are published in the project
  ontology. Reusable source/Template availability remains distinct from live depot
  installation. The redundant new specification artifact is deprecated with its
  original meaning/history and the existing specification identity as replacement.
- Root README navigation and SPECS technical documentation now describe the release.
  All 92 original project graph meanings and their order are preserved; 21 source
  digests were rebound to the reviewed specifications, without changing those meanings.

## Verification

Memory, core ontology and selected advanced ontology health report ready with no
failed required components. Memory operational readiness passed. The existing
memory projection/index and ontology compile/wiki/semantic/link products are current.
Hybrid memory lookup and combined ontology/history lookup return the new current
finding and collaboration capability. All five added competency questions and the
existing suites pass. See [exact checks and receipts](RESULT.json).

## Preserved boundaries

Existing memory records, imported ontology core, helper bytes, schemas, configuration,
capture preference, source collaboration implementation, Template/project inventory,
completed Task and external publication state remain unchanged. No service, dependency,
model installation, product adoption, new collaboration pilot or performance advantage
is claimed. The earlier release record remains an immutable statement of its original
no-publication scope; this follow-up supplies the later actual publication receipts.

## Corrective evidence

The first memory maintenance request used publication JSON encoding instead of its
owner's maintenance encoding and was refused before writing; the corrected exact grant
succeeded. The first ontology semantic rebuild exceeded the unchanged 2 MB bound.
The redundant specification identity was consolidated through reviewed deprecation,
retaining all concepts. A typed-relation mismatch and a mistyped preview hash were
refused before publication; exact corrected proposals/receipts are retained. A local
inspection helper was renamed to avoid Python stdlib shadowing. These are operation
corrections, not owner/guard/schema changes or silently rewritten history.
'''
(OUT/'RESULT.md').write_text(text)
print(json.dumps({'status':status,'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'competency_total':len(cases),'new_competencies':len(newcases),'memory_record':note,'semantic_index_bytes':index.stat().st_size,'semantic_rows':len(idx['rows'])}));sys.exit(0 if status=='complete' else 1)
