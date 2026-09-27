"""Synthetic configured catalog cases; preserve canonical starting_ids."""
import json

def specialize(h):
 cfg=json.loads((h.root/'ontology.yaml').read_text());ns=cfg['project']['namespace'];documents=[];records={}
 for relative in cfg['project_files']:
  p=h.root/relative;doc=json.loads(p.read_text());documents.append((relative,p,doc));records.update({r['@id']:r for r in doc['@graph']})
 a,b=ns+'entry-00018',ns+'entry-00019'
 for ident,other in [(a,b),(b,a)]:records[ident].update(label='Recorded duplicate process',ambiguity_with=[other],scope_note='Recorded catalog identity '+ident)
 for relative,p,doc in documents:
  p.write_text(json.dumps(doc,ensure_ascii=False))
  if any(r['@id']==ns+'entry-00014' for r in doc['@graph']):h.catalog_mutation_path=relative
 presentation=json.loads((h.root/'ontology-explorer.yaml').read_text());starting=list(presentation['starting_ids'])
 for ident in [a,b,ns+'entry-00003']:presentation['process_views'].append({'id':ident,'field_relations':{},'field_sources':{},'ordered_source':None})
 assert presentation['starting_ids']==starting and ns+'entry-00014' not in starting
 (h.root/'ontology-explorer.yaml').write_text(json.dumps(presentation))
 h.catalog_ids=[row['id'] for row in presentation['process_views']]
