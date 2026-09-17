"""Standard-library structural accounting, not an optional backend execution."""
from pathlib import Path
import sys,json,collections
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_standards import _prepare
from ontology_core import canonical_bytes,sha256,CORE
from ontology_limits import limits
from ontology_advanced import RDF,RDFS
from ontology_reasoning import infer
from ontology_provenance import proof_quads
cfg,payload,p=_prepare(ROOT);bound=limits(cfg['limits'])
statuses={canonical_bytes({k:s[k] for k in ('path','sha256','locator')}):s for s in payload['sources']}
premises=[]
for r in payload['records']:
 current=all(statuses.get(canonical_bytes(s),{}).get('status')=='current' for s in r.get('sources',[]))
 approved=r.get('lifecycle')=='approved' and r.get('fact_kind','asserted')=='asserted' and current and bool(r.get('sources'))
 if not approved:continue
 triples=[[r['@id'],RDF+'type',typ] for typ in r.get('@type',[])]
 if r['kind']=='relation':triples.append([r['subject'],RDFS+'subClassOf' if r['predicate']==CORE+'subtypeOf' else r['predicate'],r['object']])
 for t in triples:premises.append({'id':r['@id']+':'+sha256(canonical_bytes(t))[:16],'triple':t,'record_id':r['@id'],'sources':r['sources'],'approved':True})
for ext in payload['extensions']:
 for s in ext['axioms']:
  if all(statuses.get(canonical_bytes(ref),{}).get('status')=='current' for ref in s['sources']):premises.append({'id':s['id'],'triple':[s[k] for k in ('subject','predicate','object')],'record_id':s['id'],'sources':s['sources'],'approved':True})
premises.sort(key=lambda p:p['id']);negatives=[s for e in payload['extensions'] for s in e['negative_assertions']]
reasoned=infer(premises,negatives,[],payload['context'],bound)
reasoned['selected_premise_ids']=[r['id'] for r in premises];reasoned['provenance']=proof_quads(reasoned,p.project_id)
# Validate the pure accounting against a small, already available actual confined
# worker counterfactual result: proof counts and retained triples must match.
old=json.loads((Path(__file__).parent/'without-curator-infer.json').read_text())
base=[r for r in premises if not r['record_id'].startswith(p.namespace+'curator-')]
oldcalc=infer(base,negatives,[],old['context'],bound)
oldcheck={k:oldcalc[k]==old[k] for k in ('status','complete','trusted','inferred','proofs','conflicts','conclusions')}
parents={}
for r in payload['records']:
 if r.get('predicate')==CORE+'subtypeOf':parents.setdefault(r['subject'],set()).add(r['object'])
def types(r):
 found=set(r.get('@type',[]))|({r['@id']} if r['kind']=='concept' else set());todo=list(found)
 while todo:
  for t in parents.get(todo.pop(),set()):
   if t not in found:found.add(t);todo.append(t)
 return found
alltypes={r['@id']:types(r) for r in payload['records']};by_id=p.by_id
preds=[r for r in payload['records'] if r['kind']=='predicate'];groups=collections.defaultdict(list)
for r in payload['records']:
 constraints=[]
 if r.get('lifecycle') in ('approved','deprecated'):
  constraints += [(f,('minCount',1),('minLength',1)) for f in ('definition','label','module')]
  constraints += [('wasDerivedFrom',('minCount',1),('nodeKind','IRI'))]
 for field in ('subject','predicate','object','entity'):
  if field not in r:continue
  selected=sorted(by_id)
  if r['kind']=='relation' and r.get('predicate') in by_id:
   predicate=by_id[r['predicate']]
   if field in ('subject','object'):
    eligible=set(predicate.get('domain' if field=='subject' else 'range',[]));selected=sorted(rid for rid,typeset in alltypes.items() if typeset&eligible)
   elif field=='predicate':selected=sorted(v['@id'] for v in preds)
  constraints.append((field,('minCount',1),('maxCount',1),('nodeKind','IRI'),('in',tuple(selected))))
 for pred in preds:
  if alltypes[r['@id']]&set(pred.get('domain',[])):
   values=[('minCount',pred.get('cardinality',{}).get('min',0))]
   if pred.get('cardinality',{}).get('max') is not None:values.append(('maxCount',pred['cardinality']['max']))
   constraints.append((pred['@id'],*values))
 groups[sha256(canonical_bytes(sorted(set(constraints))))].append(r['@id'])
summary={'scope':'Pure standard-library exact structure accounting only; not a replacement for current confined operational inference/SHACL result',
 'context':payload['context']['snapshot_sha256'],'all_sources_current':all(s['status']=='current' for s in payload['sources']),
 'premises':len(premises),'unique_proofs':len(reasoned.get('proofs',[])),'inferred_triples':len(reasoned.get('inferred',[])),'negative_assertions':len(negatives),'conflicts':len(reasoned.get('conflicts',[])),
 'full_result_without_versions_worker_or_public_context_pretty_bytes':len(canonical_bytes(reasoned)),
 'full_result_without_versions_worker_or_public_context_compact_bytes':len(json.dumps(reasoned,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()),
 'field_pretty_bytes':{k:len(canonical_bytes(v)) for k,v in reasoned.items()},'pure_replay_matches_actual_counterfactual':oldcheck,
 'generated_node_shapes':len(payload['records']),'identical_constraint_groups':len(groups),'group_sizes':sorted([len(v) for v in groups.values()],reverse=True),
 'every_original_target_retained':sum(map(len,groups.values()))==len(payload['records']),
 'group_members':dict(groups)}
(Path(__file__).parent/'structural-metrics.json').write_bytes(canonical_bytes(summary))
print(json.dumps({k:v for k,v in summary.items() if k!='group_members'},indent=2))
