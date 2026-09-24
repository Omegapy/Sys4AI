"""Disposable semantic cases for real frontend integration, never root content."""
import json

def specialize(h):
 from explorer_support import reference_id
 cfg=json.loads((h.root/'ontology.yaml').read_text());documents=[];rows={}
 for relative in cfg['project_files']:
  p=h.root/relative;value=json.loads(p.read_text());documents.append((p,value))
  rows.update({r['@id']:r for r in value['@graph']})
 ns=cfg['project']['namespace'];rid=lambda local:ns+local
 predicate=rows[rid('documents')]
 predicate['range'].append('urn:sys4ai:ontology:core:Relationship')
 predicate['domain'].append('urn:sys4ai:ontology:core:Relationship')
 predicate['qualifiers']['count']={'type':'integer','required':False}
 rows[rid('relation-000012')]['predicate']=rid('documents')
 rows[rid('relation-000012')]['object']=rid('relation-000000')
 rows[rid('relation-000013')].update(predicate=rid('documents'),subject=rid('relation-000000'),object=rid('entry-00001'))
 rows[rid('relation-000005')]['qualifiers']={'count':9007199254740993,'condition':'Exact long condition '+('Q'*40000)}
 process=rows[rid('entry-00014')];binding=None
 # The binding is stored separately from project files.
 for relative in cfg['binding_files']:
  p=h.root/relative;value=json.loads(p.read_text())
  for row in value['@graph']:
   if row['@id']==h.ids['binding']:row.update(entity=process['@id'],sources=process['sources'])
  p.write_text(json.dumps(value))
 presentation=json.loads((h.root/'ontology-explorer.yaml').read_text());view=presentation['process_views'][0]
 endpoint=rows[rid('entry-00012')];view['field_sources']['roles']=[{'owner_id':endpoint['@id'],'reference_id':reference_id(endpoint['@id'],endpoint['sources'][0]),'extract_locator':None}]
 binding_ref=reference_id(h.ids['binding'],process['sources'][0]);view['field_sources']['inputs']=[{'owner_id':h.ids['binding'],'reference_id':binding_ref,'extract_locator':None}]
 view['ordered_source'].update(owner_id=h.ids['binding'],reference_id=binding_ref)
 (h.root/'ontology-explorer.yaml').write_text(json.dumps(presentation))
 for p,value in documents:p.write_text(json.dumps(value))
 h.frontend_mutation_files=[str(p.relative_to(h.root)) for p,value in documents if any(row['@id'] in [h.ids['focus'],rid('relation-000000')] for row in value['@graph'])]
