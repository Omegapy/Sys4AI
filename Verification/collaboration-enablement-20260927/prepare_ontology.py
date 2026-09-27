from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_lifecycle import transition
from ontology_core import canonical_bytes
sha=lambda raw:hashlib.sha256(raw).hexdigest()
C='urn:sys4ai:ontology:core:';P='urn:sys4ai:ontology:project:sys4ai-depot:'
reason='User-requested root installation and automatic selected initializer activation verified in current exact adoption/static/confined evidence; retain prior unadopted release meaning as history.'
changes=[];rebounds=0
paths=['ONTOLOGY/modules/project/project.jsonld','ONTOLOGY/bindings/artifacts.json','ONTOLOGY/bindings/skills.json','ONTOLOGY/modules/project/competency.json','ONTOLOGY/modules/project/curator.jsonld','ONTOLOGY/bindings/curator.jsonld']
for path in paths:
 raw=(ROOT/path).read_bytes();doc=json.loads(raw)
 for i,node in enumerate(doc.get('@graph',[])):
  key=node['@id'][len(P):] if node['@id'].startswith(P) else ''
  if key in {'capability-shared-agent-billboards','reusable-collaborate','binding-skill-collaborate-reusable'}:
   node=transition(node,'approved',reason=reason);doc['@graph'][i]=node
   if key=='capability-shared-agent-billboards':
    node['definition']='Task-governed direct collaboration through immutable participant posts, scoped reads, replies, bounded views and exact owner snapshots. Complete capability is installed and enabled in the depot root and neutral Template; current initializer automatically enables selected new and existing projects after checked adoption. Posting changes no Task or publication authority.'
    node['scope_note']='Static-ready root uses exact depot-v1 owner and default Task habits; execution still requires current scoped manager policy/grants. Version 1 supplies no version 2 native broker proof. Cooperative filesystem checks provide no OS authentication. Historical native pilots and current deterministic/adoption evidence remain distinct; no new native pilot or performance advantage is claimed.'
   elif key=='reusable-collaborate':
    node['definition']='The source skill at SKILLS-depo/collaborate/SKILL.md and checked neutral Template supply collaboration. A separate exact copy is installed and enabled at the depot root .agents/skills/collaborate. Current initializer create/prepare enables selected destinations by checked module adoption, preserving custom content and earlier base receipts. Discovery grants no invocation or publication authority.'
    node['scope_note']='Reusable source identity remains distinct from its reviewed root copy. Other products receive no bulk update; incompatible or customized installations block readiness. Communication retains the human-facing writing role.'
   else: node['definition']='Resolve the reusable collaboration source and the documented checked root installation/default initializer availability. Source discovery is neither invocation nor an execution grant.'
  for source in node.get('sources',[]):
   if source['path'] in {'SPECS.md','.agents/skills/task/SKILL.md','.agents/skills/agent-task/SKILL.md','.agents/skills/init-new-project/SKILL.md'}:
    value=sha((ROOT/source['path']).read_bytes())
    if source['sha256']!=value:source['sha256']=value;rebounds+=1
 if path.endswith('competency.json'):
  q=next(q for q in doc['questions'] if q['id']=='root-collaboration-capability');q['expected_terms']=['installed and enabled','automatically enables']
 content=canonical_bytes(doc);changes.append(dict(path=path,expected_sha256=sha(raw),sha256=sha(content),content=content.decode()))
payload=dict(schema_version=1,operation_id='ONTOP-20260927-collaboration-enabled-v4',operation='publish',reason=reason,changes=changes)
(OUT/'ontology-proposal.json').write_bytes(canonical_bytes(payload))
print(json.dumps({'changes':[p['path'] for p in changes],'source_rebinds':rebounds,'new_semantic_nodes':0,'renewed_existing_reviews':3}))
