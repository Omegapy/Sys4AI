import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
C='urn:sys4ai:ontology:core:';P='urn:sys4ai:ontology:project:sys4ai-depot:'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def enc(v):return json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
src={'path':'SPECS.md','sha256':sha((ROOT/'SPECS.md').read_bytes()),'locator':'section:Shared agent billboards and collaboration release'}
def node(key,label,definition,kind='concept',typ='OntologyConcept',**extra):
 return {'@id':P+key,'@type':[C+typ],'kind':kind,'label':label,'definition':definition,'fact_kind':'asserted','lifecycle':'approved','module':'project','sources':[src],**extra}
cap=node('capability-shared-agent-billboards','Shared agent billboard collaboration','Task-governed direct collaboration through immutable participant posts, scoped reads, reply/correction links, bounded derived views and exact owner snapshots. The reusable source and neutral Template provide the capability; the depot live installation remains unadopted. Posting changes no Task or publication authority.','instance','Capability',aliases=['shared agent billboards','Task-governed collaboration'],scope_note='Cooperative filesystem and actor checks provide no OS authentication or raw-filesystem confinement. Initial candidates and assigned first reviews remain sealed. Actual generic V1/extra-complex V2 pilots and current V4 deterministic/adoption evidence remain distinct; no current V4 native replay or performance advantage is claimed.')
skill=node('reusable-collaborate','Reusable collaborate skill','The source skill at SKILLS-depo/collaborate/SKILL.md and its checked neutral Template copy supply the collaboration capability. It is not installed in the depot active .agents/skills directory; finding this source grants no invocation, lifecycle, publication or external-action authority.','instance','Skill',aliases=['collaborate reusable source'],scope_note='Existing projects require separately selected adoption. Communication retains the human-facing writing role.')
artifact=node('artifact-collaboration-specification','Collaboration release technical specification','Project-local SPECS.md documents the released reusable collaboration capability, current evidence levels and unadopted live-installation boundary.','instance','Artifact')
concepts=[
 node('collaboration-post','Immutable collaboration post','An immutable participant-authored message retains its author, Task/subtask, exact version, visibility and source references. Direct posting within an existing native assignment and registered policy supplies no additional authority.'),
 node('collaboration-reading-receipt','Collaboration reading receipt','A receipt acknowledges one exact message version as reported reading. Reading is distinct from independently established comprehension and incorporation.'),
 node('collaboration-notification-receipt','Recipient-observed notification receipt','Receipt schema 2 records actual addressed-mailbox observation by the current recipient. Notification is independent of reading; empty sender API returns remain unconfirmed.',aliases=['collaboration receipt2']),
 node('collaboration-material-evidence','Material collaboration evidence','A material message identifies an affected exact candidate/version for current owner assessment. All material message types participate; affected reviews, synthesis and acceptance require the existing invalidation and revalidation gates.'),
 node('collaboration-owner-snapshot','Collaboration owner snapshot','An exact selected view binds visible posts, objections and candidate versions for the responsible senior or manager. The snapshot changes no decision authority.'),
 node('collaboration-knowledge-proposal','Pending collaboration knowledge proposal','A sourced proposal remains pending for separately authorized memory, ontology or Curator owner review. Posting, replying, acknowledging or accepting discussion does not publish knowledge or execute maintenance.')]
def relation(key,subject,predicate,obj,definition):
 return node(key,definition,definition,'relation','Relationship',subject=P+subject,predicate=C+predicate,object=(P+obj if not obj.startswith('urn:') else obj))
rels=[relation('collaborate-provides','reusable-collaborate','providesCapability','capability-shared-agent-billboards','Reusable collaborate source provides Shared agent billboard collaboration'),relation('collaborate-defined-by','reusable-collaborate','definedBy','artifact-collaboration-specification','Reusable collaborate source is described by the project technical specification'),relation('collaboration-task-boundary','capability-shared-agent-billboards','relatedTo',C+'Task','Shared agent billboard collaboration remains within existing Task authority')]
rels += [relation('collaboration-rel-'+n['@id'].split(':')[-1],'capability-shared-agent-billboards','relatedTo',n['@id'], 'Shared agent billboard collaboration uses '+n['label']) for n in concepts]
paths=['ONTOLOGY/modules/project/project.jsonld','ONTOLOGY/bindings/artifacts.json','ONTOLOGY/bindings/skills.json','ONTOLOGY/modules/project/competency.json']
changes=[]
for raw in paths:
 original=(ROOT/raw).read_bytes();doc=json.loads(original)
 if '@graph' in doc:
  for n in doc['@graph']:
   for s in n.get('sources',[]):
    if s['path']=='SPECS.md':s['sha256']=src['sha256']
 if raw==paths[0]:
  additions=[cap,skill,artifact,*concepts,*rels]
  existing={n['@id'] for n in doc['@graph']}
  assert not existing.intersection(n['@id'] for n in additions)
  doc['@graph']+=additions;doc['@graph'].sort(key=lambda n:n['@id'])
 elif raw==paths[2]:
  doc['@graph'].append(node('binding-skill-collaborate-reusable','Reusable collaborate source binding','Resolve the reusable collaboration source and its unadopted live-depot boundary; this is not an installed skill or an execution grant.','binding','SourceBinding',binding_type='skill',entity=P+'reusable-collaborate'));doc['@graph'].sort(key=lambda n:n['@id'])
 elif raw==paths[3]:
  cases=[('collaboration-capability','capability','Shared agent billboard collaboration',['capability-shared-agent-billboards','reusable-collaborate'],['unadopted']),('collaboration-notification','definition','Recipient-observed notification receipt',['collaboration-notification-receipt'],['empty sender API returns remain unconfirmed']),('collaboration-reading','definition','Collaboration reading receipt',['collaboration-reading-receipt'],['reported reading']),('collaboration-material','definition','Material collaboration evidence',['collaboration-material-evidence'],['All material message types']),('collaboration-proposal','definition','Pending collaboration knowledge proposal',['collaboration-knowledge-proposal'],['does not publish knowledge'])]
  doc['questions'] += [{'id':'root-'+key,'intent':intent,'query':query,'expected_ids':[P+k for k in ids],'expected_sources':['SPECS.md'],'expected_terms':terms} for key,intent,query,ids,terms in cases]
 content=enc(doc);changes.append({'path':raw,'expected_sha256':sha(original),'content':content,'sha256':sha(content.encode())})
payload={'schema_version':1,'operation_id':'ONTOP-20260926-collaboration-knowledge-v1','operation':'publish','reason':'Explicit user request to update project ontology and memory after the verified collaboration release; add project-local meanings and reusable-source boundaries, retaining existing identities and current source provenance.','changes':changes}
(OUT/'ontology-proposal.json').write_text(enc(payload));print(json.dumps({'changes':[{'path':x['path'],'sha256':x['sha256']} for x in changes],'new_graph_nodes':len(additions),'new_bindings':1,'new_competencies':5,'source_rebinds':21}))
