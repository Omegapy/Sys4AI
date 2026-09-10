"""Parsed, read-only SPARQL over preloaded graph selections."""
from ontology_core import OntologyError, canonical_bytes, require


def _walk(value, depth=0):
    from pyparsing import ParseResults
    from rdflib.plugins.sparql.parserutils import CompValue
    if depth>256: raise OntologyError('query_depth', 'Query nesting exceeds the parser inspection bound.')
    if isinstance(value, CompValue):
        yield value, depth
        for child in value.values(): yield from _walk(child,depth+1)
    elif isinstance(value, (list, tuple, ParseResults)):
        for child in value: yield from _walk(child,depth+1)
    elif isinstance(value, dict):
        for child in value.values(): yield from _walk(child,depth+1)


def query(dataset, text, names, selected, bound):
    from rdflib import Dataset, URIRef
    from rdflib.plugins.sparql.parser import parseQuery, parseUpdate
    from rdflib.plugins.sparql.algebra import translateQuery
    from ontology_rdf import encode, normalized_triples
    require(isinstance(text,str) and len(text.encode())<=bound['input_bytes'], 'malformed_query', 'Expected bounded SPARQL text.')
    try: parsed=parseQuery(text)
    except Exception as query_error:
        try: update=parseUpdate(text)
        except Exception: raise OntologyError('malformed_query','SPARQL query syntax is invalid.') from query_error
        if update.get('request'): raise OntologyError('prohibited_query','SPARQL Update is outside the read-only profile.')
        raise OntologyError('malformed_query','SPARQL query syntax is invalid.')
    allowed=set(names[k] if k in names else k for k in selected)
    require(allowed<=set(names.values()),'unselected_graph','Query graph selection is outside the project dataset.')
    defaults=[]; named=[]
    ordered=bool(parsed[1].get('orderby'))
    # Algebra translation resolves prefixed IRIs and does not load a dataset.
    prepared=translateQuery(parsed)
    for value,depth in _walk(parsed):
        require(depth<=bound['query_depth'],'resource_limit','Parsed query exceeds query_depth.')
        if value.name=='ServiceGraphPattern': raise OntologyError('prohibited_query','SERVICE federation is forbidden.')
        if value.name in {'Builtin_RAND','Builtin_NOW','Builtin_UUID','Builtin_STRUUID','Builtin_BNODE'}:
            raise OntologyError('unsupported_query','Nondeterministic expressions are outside the repeatable query profile.')
        if value.name=='Function':
            uri=value.get('iri')
            require(str(uri).startswith('http://www.w3.org/2001/XMLSchema#'),'unsupported_query','Unselected custom SPARQL functions are forbidden.')
        if value.name=='DatasetClause':
            field='default' if 'default' in value else 'named'
            uri=str(value[field]); require(uri in allowed,'unselected_graph','FROM can only select an already permitted named graph.')
            (defaults if field=='default' else named).append(uri)
    # Removing parsed dataset clauses prevents RDFLib's automatic FROM loading.
    had_clauses=bool(defaults or named)
    prepared.algebra['datasetClause']=None
    active=Dataset(default_union=False)
    for graph_id in (named if had_clauses else sorted(allowed)):
        for triple in dataset.graph(URIRef(graph_id)): active.graph(URIRef(graph_id)).add(triple)
    for graph_id in (defaults if had_clauses else sorted(allowed)):
        for triple in dataset.graph(URIRef(graph_id)): active.default_graph.add(triple)
    result=active.query(prepared,use_store_provided=False)
    output={'status':'ok','complete':True,'query_form':result.type,'graph_scope':sorted(allowed),'diagnostics':[]}
    if result.type=='ASK': output['answer']=bool(result.askAnswer)
    elif result.type=='SELECT':
        variables=[str(v) for v in result.vars]; rows=[]
        for row in result:
            if len(rows)>=bound['result_rows']:
                output.update(status='resource_limit',complete=False,limit='result_rows'); break
            rows.append({name:encode(value) for name,value in zip(variables,row) if value is not None})
        # Preserve explicit ORDER BY, otherwise normalize the finite binding bag.
        if not ordered: rows.sort(key=canonical_bytes)
        output.update(variables=variables,rows=rows)
    else:
        triples=normalized_triples(result.graph)
        if len(triples)>bound['result_rows']:
            output.update(status='resource_limit',complete=False,limit='result_rows'); triples=triples[:bound['result_rows']]
        output['triples']=triples
        if result.type=='DESCRIBE': output['describe_policy']='RDFLib concise bounded description including reachable blank-node objects'
    if len(canonical_bytes(output))>bound['output_bytes']:
        return {'status':'output_limit','complete':False,'diagnostics':[{'code':'output_limit','message':'Query result exceeds output_bytes.'}],'query_form':result.type,'graph_scope':sorted(allowed)}
    return output
