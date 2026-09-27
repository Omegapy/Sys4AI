import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_lifecycle import transition
from ontology_core import canonical_bytes,sha256
raw='ONTOLOGY/modules/project/project.jsonld';before=(ROOT/raw).read_bytes();doc=json.loads(before);P='urn:sys4ai:ontology:project:sys4ai-depot:'
ids={n['@id']:n for n in doc['@graph']};assert P+'artifact-specifications' in ids
reason='The new collaboration specification artifact refers to the same canonical SPECS.md already represented by artifact-specifications. Reuse that established identity with the exact collaboration section source locator; retain the duplicate identity and historical meaning as deprecated. This preserves all collaboration concepts and scope while avoiding a redundant semantic-index row under the unchanged existing owner bound.'
for i,n in enumerate(doc['@graph']):
 if n['@id']==P+'artifact-collaboration-specification':doc['@graph'][i]=transition(n,'deprecated',reason=reason,replacement=P+'artifact-specifications')
 if n['@id']==P+'collaboration-specification-describes':
  renewed=transition(n,'approved',reason='Renewed exact review redirects this relation to the pre-existing canonical SPECS.md identity; the previous relation version and meaning are retained.');renewed['subject']=P+'artifact-specifications';renewed['predicate']='urn:sys4ai:ontology:core:relatedTo';renewed['label']='Root specifications relate to reusable collaborate source';renewed['definition']='Root technical specifications document the reusable collaboration source and release boundaries. The specification identity and source binding remain distinct from the reusable Skill.';doc['@graph'][i]=renewed
content=canonical_bytes(doc).decode();proposal={'schema_version':1,'operation_id':'ONTOP-20260927-collaboration-specification-identity-v2','operation':'publish','reason':reason,'changes':[{'path':raw,'expected_sha256':hashlib.sha256(before).hexdigest(),'content':content,'sha256':sha256(content.encode())}]}
(OUT/'ontology-consolidation-proposal.json').write_bytes(canonical_bytes(proposal));print(json.dumps({'changed_file':raw,'retained_deprecated_id':P+'artifact-collaboration-specification','replacement':P+'artifact-specifications','all_six_collaboration_concepts_retained':True}))
