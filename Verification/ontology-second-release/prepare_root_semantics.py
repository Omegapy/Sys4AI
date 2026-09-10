"""Prepare exact depot records and companion adoption for the selected release."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_core import canonical_bytes,sha256,atomic_write,load_project
from ontology_publication import preview
OUT=ROOT/'Verification/ontology-second-release'
cfg=json.loads((ROOT/'ontology.yaml').read_text())
companion=json.loads((ROOT/'ONTOLOGY-depo/starter/ontology-advanced.yaml').read_text())
companion['project_id']=cfg['project']['id']
companion['publication']={'enabled':True,'binding':copy.deepcopy(cfg['publication']['binding'])}
companion['publication']['binding']['scope']=['ontology-advanced.yaml','ONTOLOGY/extensions']
for name in ['standards','inference','semantic','workbench']: companion['profiles'][name]['enabled']=True
raw=canonical_bytes(companion)
selection={'schema_version':1,'plan_id':'PLAN-20260909-4B15BB49','path':'ontology-advanced.yaml','expected_sha256':None,'sha256':sha256(raw),'content':raw.decode(),'reason':'Explicit root adoption and activation selected by the implementation goal; each runtime is provisioned/certified separately.'}
(OUT/'root-companion-selection.json').write_bytes(canonical_bytes(selection))
if not (ROOT/'ontology-advanced.yaml').exists(): atomic_write(ROOT,'ontology-advanced.yaml',raw,None)
else: assert (ROOT/'ontology-advanced.yaml').read_bytes()==raw,'Review existing companion before changing it'
ns=cfg['project']['namespace']; core='urn:sys4ai:ontology:core:'
src={'path':'SPECS.md','sha256':sha256(ROOT/'SPECS.md'),'locator':'section:Ontology second release and initialization v9'}
def record(id,label,definition,kind='instance',type='Capability',**extra):
 return {'@id':ns+id,'@type':[core+type],'label':label,'definition':definition,'kind':kind,'fact_kind':'asserted','lifecycle':'approved','module':'project','sources':[src],**extra}
capabilities=[
 ('standards','Local RDF SPARQL SHACL','Project-local RDF datasets, read-only SPARQL queries, loss-aware interchange, and SHACL validation using the separately selected pinned standards backend.'),
 ('inference','Formal ontology inference','Finite type and declared property inference from approved premises, with inspectable derivations, exact versions, and conflict/incomplete diagnostics.'),
 ('semantic','Semantic ontology retrieval','A selected local embedding model ranks approved ontology records; similarity grants neither identity equivalence nor authority.'),
 ('proposals','Sourced ontology proposals','A native agent generates attributed candidates from explicitly selected inputs, with validation, directed revision, exact review, and separately authorized publication.'),
 ('guards','Guarded helper dispatch','Declared ontology, memory, Task, TRD, plan, role, Template and setup helper boundaries validate semantic conditions and current authority before their owning mutation.'),
 ('workbench','Ontology visual workbench','A local browser service searches definitions, inspects relationships and derivations, preserves draft revisions, reviews diffs, and publishes through the same guarded interfaces.')]
changes=[]
for relative in cfg['project_files']+cfg['binding_files']:
 path=ROOT/relative; doc=json.loads(path.read_text()); original=copy.deepcopy(doc)
 for item in doc['@graph']:
  for source in item['sources']:
   target=ROOT/source['path']; source['sha256']=sha256(target)
 if relative==cfg['project_files'][0]:
  existing={r['@id'] for r in doc['@graph']}
  for slug,label,definition in capabilities:
   for r in [record('capability-ontology-'+slug,label,definition),record('ontology-provides-'+slug,'Ontology skill provides '+label,definition,kind='relation',type='Relationship',subject=ns+'installed-ontology',predicate=core+'providesCapability',object=ns+'capability-ontology-'+slug)]:
    assert r['@id'] not in existing; doc['@graph'].append(r)
  doc['@graph'].extend([
   record('GeneratedWikiPage','Generated ontology wiki page','A generated ontology wiki page is an Artifact subtype; it is rebuildable and does not replace canonical records.',kind='concept',type='OntologyConcept'),
   record('generated-wiki-page-artifact','Generated wiki page is an Artifact','Every generated ontology wiki page is an Artifact.',kind='relation',type='Relationship',subject=ns+'GeneratedWikiPage',predicate=core+'subtypeOf',object=core+'Artifact'),
   record('ontology-wiki-index','Generated ontology wiki index','The rebuildable ONTOLOGY/WIKI/INDEX.md is a generated ontology wiki page.',**{'@type':[ns+'GeneratedWikiPage']})])
 if doc!=original:
  content=canonical_bytes(doc); changes.append({'path':relative,'expected_sha256':sha256(path),'sha256':sha256(content),'content':content.decode()})
relative=cfg['competency_files'][0]; path=ROOT/relative; doc=json.loads(path.read_text())
for slug,label,_ in capabilities:
 doc['questions'].append({'id':'root-advanced-'+slug,'intent':'capability','query':label,'expected_ids':[ns+'capability-ontology-'+slug,ns+'installed-ontology'],'expected_sources':['SPECS.md']})
content=canonical_bytes(doc);changes.append({'path':relative,'expected_sha256':sha256(path),'sha256':sha256(content),'content':content.decode()})
proposal={'schema_version':1,'operation_id':'ONTOP-root-advanced-adoption-20260909','operation':'publish','reason':'Publish source-backed second-release capability bindings, wiki type hierarchy and competency cases; refresh only hashes of explicitly selected current root sources. Preserve all existing IDs and records.','changes':changes}
(OUT/'root-semantic-proposal.json').write_bytes(canonical_bytes(proposal))
pre=preview(ROOT,proposal);(OUT/'root-semantic-preview.json').write_bytes(canonical_bytes(pre))
print(json.dumps({'status':'previewed','files':len(changes),'preview_sha256':pre['preview_sha256'],'valid':pre['valid'],'companion_sha256':selection['sha256']}))
