"""Closed backend dispatcher loaded only inside the confined worker."""
import importlib.metadata
import json
import sys
from ontology_core import OntologyError, canonical_bytes, require, sha256


def versions():
    names=('rdflib','pyshacl','owlrl','pyparsing','packaging','prettytable','html5rdf','wcwidth')
    return {'python':'.'.join(map(str,sys.version_info[:3])), 'packages':{name:importlib.metadata.version(name) for name in names}}


def _close_plugins():
    import rdflib
    rdflib.NORMALIZE_LITERALS=False
    import rdflib.plugin
    from rdflib.parser import Parser
    from rdflib.serializer import Serializer
    from rdflib.store import Store
    from rdflib.query import Processor,Result
    for key,value in list(rdflib.plugin._plugins.items()):
        name,kind=key
        allowed=(kind is Parser and name in {'json-ld','turtle','xml'}) or (kind is Serializer and name in {'json-ld','turtle','xml'}) or (kind is Store and name in {'Memory','default'}) or (kind in {Processor,Result} and name=='sparql')
        if not allowed or not getattr(value,'module_path','').startswith('rdflib.'):
            del rdflib.plugin._plugins[key]
    import rdflib.plugins.sparql.operators as operators
    for key in list(operators._CUSTOM_FUNCTIONS):
        if not str(key).startswith('http://www.w3.org/2001/XMLSchema#'): del operators._CUSTOM_FUNCTIONS[key]


def dispatch(operation,payload,bound):
    import rdflib, pyshacl, owlrl
    _close_plugins()
    observed=versions()
    if operation=='versions': return {'status':'ok','complete':True,'versions':observed}
    if operation.startswith('probe_'): return _probe(operation,payload,bound)
    from ontology_rdf import project_dataset,quad_rows,node,normalized_triples
    if operation=='parse':
        from ontology_interchange import stage
        result=stage(payload['data'],payload['format'],payload.get('manifest'),bound)
        existing,_,_=project_dataset(payload)
        from ontology_rdf import encode
        known={str(s) for s,p,o,g in existing.quads((None,None,None,None))}
        canonical={}
        for s,p,o,g in existing.quads((None,None,None,None)):
            canonical.setdefault((str(s),str(p)),set()).add(canonical_bytes(encode(o)))
        conflicts=[]
        for s,p,o,g in result['quads']:
            if isinstance(s,str) and s in known and canonical_bytes(o) not in canonical.get((s,p),set()):
                conflicts.append({'subject':s,'predicate':p,'object':o,'graph':g,'code':'existing_identity_change'})
        result['namespace_conflicts']=conflicts
        if conflicts: result['diagnostics'].append({'code':'namespace_conflict','message':'Imported statements change existing selected identities and require explicit semantic review.'})
    else:
        ds,names,premises=project_dataset(payload)
        require(sum(1 for _ in ds.quads((None,None,None,None)))<=bound['input_triples'],'resource_limit','Dataset exceeds input_triples.')
        selected=payload.get('graphs') or ['asserted','derived']
        require(set(selected)<=set(names)|set(names.values()),'unselected_graph','Requested graph is not a selected project graph.')
        needs_inferred=payload.get('include_inferred',False) or (operation=='query' and any(x in {'inferred',names['inferred']} for x in selected)) or (operation=='export' and payload.get('selected_graph') in {'inferred',names['inferred']})
        if needs_inferred:
            require(payload.get('inference_enabled',False),'profile_disabled','Inferred graph scope requires the selected inference profile.')
            reasoning=_reason(payload,premises,bound)
            require(reasoning['complete'] and reasoning['trusted'],'incomplete_inference','Inferred graph scope requires complete trusted reasoning.')
            for triple in reasoning['inferred']: ds.graph(node(names['inferred'])).add(tuple(node(x) for x in triple))
            for s,p,o,g in reasoning.get('provenance',[]): ds.graph(node(g)).add((node(s),node(p),node(o)))
        if operation=='dataset':
            rows=quad_rows(ds)
            allowed={names.get(x,x) for x in selected}
            rows=[r for r in rows if r[3] in allowed]
            result={'status':'ok','complete':True,'quads':rows,'graphs':names,'graph_scope':selected,'semantic_sha256':sha256(canonical_bytes(rows))}
        elif operation=='query':
            from ontology_sparql import query
            result=query(ds,payload['query'],names,selected,bound)
        elif operation=='validate':
            from ontology_shacl import validate
            result=validate(ds,names,selected,payload['records'],payload.get('shapes',[]),bound,payload.get('triples'))
        elif operation=='infer':
            mode=payload.get('result_mode','full')
            require(type(mode) is str and mode in {'full','diagnostic'},'invalid_result_mode','Select full or diagnostic inference output.')
            result=_reason(payload,premises,bound)
            if mode=='diagnostic': result=_diagnostic(result,payload)
        elif operation=='export':
            from ontology_interchange import export
            result=export(ds,names,payload['format'],payload.get('selected_graph'))
        elif operation=='oracle':
            from rdflib import Graph
            graph=Graph()
            for premise in premises:
                if all(isinstance(x,str) for x in premise['triple']): graph.add(tuple(node(x) for x in premise['triple']))
            owlrl.DeductiveClosure(owlrl.OWLRL_Semantics,axiomatic_triples=False,datatype_axioms=False).expand(graph)
            result={'status':'ok','complete':True,'triples':normalized_triples(graph)}
        else: raise OntologyError('unsupported_operation','Unselected standards operation.')
    result['versions']=observed
    return result


def _reason(payload,premises,bound):
    from ontology_reasoning import infer
    if any(s.get('status')!='current' for s in payload['sources']):
        return {'status':'stale_input','complete':False,'trusted':False,'diagnostics':[{'code':'stale_input','message':'Reasoning sources are stale or unavailable.'}]}
    ids=payload.get('premise_ids')
    if ids is not None:
        available={p['id'] for p in premises}|{p['record_id'] for p in premises}|{n['id'] for e in payload.get('extensions',[]) for n in e['negative_assertions']}
        require(isinstance(ids,list) and set(ids)<=available,'unselected_premise','Requested premise is not an approved exact selected assertion.')
        premises=[p for p in premises if p['id'] in ids or p['record_id'] in ids]
    negatives=[s for e in payload.get('extensions',[]) for s in e['negative_assertions']]
    if ids is not None: negatives=[n for n in negatives if n['id'] in ids]
    result=infer(premises,negatives,payload.get('goals',[]),payload['context'],bound)
    result['selected_premise_ids']=[p['id'] for p in premises]
    from ontology_provenance import proof_quads
    result['provenance']=proof_quads(result,payload['context']['project_id'])
    return result


def _diagnostic(result,payload):
    """Summarize only after identical bounded reasoning and conflict detection."""
    fields=('selected_premise_ids','negative_assertions','inferred','proofs','conflicts','provenance')
    evidence={name:({'count':len(result[name]),'sha256':sha256(canonical_bytes(result[name]))}
                    if name in result else None) for name in fields}
    retained={k:v for k,v in result.items() if k not in fields}
    return {**retained,'diagnostic_schema_version':1,'result_mode':'diagnostic',
        'reasoning_scope':'full_selected_closure' if payload.get('premise_ids') is None else 'selected_premise_closure',
        'proof_detail':'counts_and_digests_only','evidence':evidence,'authority':False,
        'requested_premises':None if payload.get('premise_ids') is None else {
            'count':len(payload['premise_ids']),'sha256':sha256(canonical_bytes(payload['premise_ids']))},
        'proof_retrieval':{'api':'infer(root, premise_ids=[exact_assertion_or_record_id], goals=[triple])',
            'scope':'An exact premise query proves only its selected premise closure.',
            'full_proof_delivery':'not_exercised; default full infer retains its output bound and may return output_limit'}}


def _probe(operation,payload,bound):
    import time
    from pathlib import Path
    if operation=='probe_file':
        try: Path(payload['path']).read_bytes(); denied=False
        except PermissionError: denied=True
        return {'status':'ok','complete':True,'denied':denied}
    if operation=='probe_network':
        import socket
        sock=socket.socket()
        try: sock.connect(('127.0.0.1',payload['port'])); denied=False
        except PermissionError: denied=True
        finally: sock.close()
        return {'status':'ok','complete':True,'denied':denied}
    if operation=='probe_parser':
        from rdflib import Graph
        try: Graph().parse(data=payload['data'],format=payload['format']); denied=False
        except Exception as exc: return {'status':'ok','complete':True,'denied':True,'exception':type(exc).__name__,'message':str(exc)[:200]}
        return {'status':'ok','complete':True,'denied':denied}
    if operation=='probe_memory':
        blocks=[]
        while True: blocks.append(bytearray(1024*1024)); time.sleep(.001)
    if operation=='probe_timeout': time.sleep(120)
    if operation=='probe_crash': import os; os._exit(17)
    if operation=='probe_malformed': print('invalid-json'); return {'status':'ok','complete':True}
    if operation=='probe_output': print('x'*(bound['output_bytes']+1)); return {'status':'ok','complete':True}
    raise OntologyError('unsupported_operation','Unselected probe.')
