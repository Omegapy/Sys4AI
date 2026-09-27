"""Explicit compact-v1 to RDF mapping. Never parse the compact context as OWL."""
from ontology_core import CORE, canonical_bytes, sha256
from ontology_advanced import RDF, RDFS, OWL, term

FIELD = CORE + "field:"
ADV = "urn:sys4ai:ontology:advanced:"
PROV = "http://www.w3.org/ns/prov#"


def node(value):
    from rdflib import URIRef, Literal, BNode
    term(value, blank=True)
    if isinstance(value, str): return URIRef(value)
    if 'bnode' in value: return BNode(value['bnode'])
    return Literal(value['value'], datatype=URIRef(value['datatype']) if 'datatype' in value else None,
                   lang=value.get('language'), normalize=False)


def encode(value):
    from rdflib import URIRef, Literal, BNode
    if isinstance(value, URIRef): return str(value)
    if isinstance(value, BNode): return {'bnode': str(value)}
    if isinstance(value, Literal):
        result = {'value': str(value)}
        if value.language: result['language'] = value.language.lower()
        elif value.datatype: result['datatype'] = str(value.datatype)
        return result
    raise ValueError('Unsupported RDF term')


def graph_ids(project_id):
    return {kind: 'urn:sys4ai:ontology:graph:' + project_id + ':' + kind for kind in ('asserted', 'derived', 'inferred', 'external')}


def normalized_triples(graph):
    from rdflib.compare import to_canonical_graph
    rows = [[encode(v) for v in triple] for triple in to_canonical_graph(graph)]
    return sorted(rows, key=canonical_bytes)


def quad_rows(dataset):
    # Canonicalize a reified quad graph once, retaining bnode identity across graphs.
    from rdflib import Graph, BNode, URIRef
    from rdflib.compare import to_canonical_graph
    # Ground RDF terms already have stable identities; introducing quad bnodes
    # makes canonicalization expensive without changing their encoded values.
    if not any(isinstance(value,BNode) for quad in dataset.quads((None,None,None,None)) for value in quad):
        return sorted([[encode(value) for value in quad] for quad in dataset.quads((None,None,None,None))],key=canonical_bytes)
    q = Graph()
    keys = [URIRef(ADV+k) for k in ('s','p','o','g')]
    for index, (s,p,o,g) in enumerate(dataset.quads((None,None,None,None))):
        n=BNode('quad'+str(index))
        for key,value in zip(keys, (s,p,o,g)): q.add((n,key,value))
    q=to_canonical_graph(q)
    rows=[]
    for n in q.subjects(keys[0], None):
        rows.append([encode(q.value(n,key)) for key in keys])
    return sorted(rows,key=canonical_bytes)


def from_quads(rows):
    from rdflib import Dataset
    ds=Dataset(default_union=False)
    for s,p,o,g in rows: ds.graph(node(g)).add((node(s),node(p),node(o)))
    return ds


def project_dataset(payload):
    from rdflib import Dataset, URIRef, Literal
    ds = Dataset(default_union=False)
    names=graph_ids(payload['context']['project_id'])
    graphs={name: ds.graph(URIRef(iri)) for name,iri in names.items()}
    provenance=graphs['derived']; premises=[]
    sources={canonical_bytes({k:s[k] for k in ('path','sha256','locator')}):s for s in payload['sources']}
    for record in payload['records']:
        subject=URIRef(record['@id']); kind=record.get('fact_kind','asserted')
        graph=graphs[kind]
        current=all(sources.get(canonical_bytes(s),{}).get('status')=='current' for s in record.get('sources',[]))
        approved=record.get('lifecycle')=='approved' and kind=='asserted' and current and bool(record.get('sources'))
        semantic=[]
        for typ in record.get('@type',[]): semantic.append((subject,URIRef(RDF+'type'),URIRef(typ)))
        if record['kind']=='concept': graph.add((subject,URIRef(RDF+'type'),URIRef(RDFS+'Class')))
        if record['kind']=='predicate': graph.add((subject,URIRef(RDF+'type'),URIRef(RDF+'Property')))
        if record['kind']=='relation':
            predicate=RDFS+'subClassOf' if record.get('predicate')==CORE+'subtypeOf' else record.get('predicate')
            if record.get('subject') and predicate and record.get('object'):
                semantic.append((URIRef(record['subject']),URIRef(predicate),URIRef(record['object'])))
        for triple in semantic:
            graph.add(triple)
            if approved:
                premises.append({'id':record['@id']+':'+sha256(canonical_bytes([encode(x) for x in triple]))[:16],
                    'triple':[encode(x) for x in triple], 'record_id':record['@id'], 'sources':record['sources'], 'approved':True})
        for key,value in record.items():
            if key.startswith('@') or key=='sources': continue
            if isinstance(value,str):
                graph.add((subject,URIRef(FIELD+key),URIRef(value) if key in {'subject','predicate','object','entity','replacement'} else Literal(value)))
            elif isinstance(value,list):
                for entry in value:
                    if isinstance(entry,str): graph.add((subject,URIRef(FIELD+key),URIRef(entry) if key in {'domain','range','ambiguity_with'} else Literal(entry)))
                    else: graph.add((subject,URIRef(FIELD+key),Literal(canonical_bytes(entry).decode(),datatype=URIRef(RDF+'JSON'),normalize=False)))
            elif isinstance(value,dict): graph.add((subject,URIRef(FIELD+key),Literal(canonical_bytes(value).decode(),datatype=URIRef(RDF+'JSON'),normalize=False)))
            elif isinstance(value,(bool,int,float)): graph.add((subject,URIRef(FIELD+key),Literal(value)))
        if record.get('lifecycle') in {'approved','deprecated'}:
            provenance.add((subject,URIRef(RDF+'type'),URIRef(ADV+'ApprovedRecord')))
        from ontology_provenance import add_sources
        add_sources(provenance,subject,record.get('sources',[]),sources,payload['context'])
    for extension in payload.get('extensions',[]):
        for field in ('axioms','annotations'):
            for statement in extension[field]:
                triple=tuple(node(statement[k]) for k in ('subject','predicate','object'))
                graphs['asserted'].add(triple)
                if field=='axioms' and all(sources.get(canonical_bytes(s),{}).get('status')=='current' for s in statement['sources']):
                    premises.append({'id':statement['id'],'triple':[encode(x) for x in triple], 'record_id':statement['id'], 'sources':statement['sources'], 'approved':True})
                from ontology_provenance import add_sources
                add_sources(provenance,URIRef(statement['id']),statement['sources'],sources,payload['context'])
        for statement in extension['negative_assertions']:
            identifier=URIRef(statement['id']); graph=graphs['asserted']
            graph.add((identifier,URIRef(RDF+'type'),URIRef(OWL+'NegativePropertyAssertion')))
            graph.add((identifier,URIRef(OWL+'sourceIndividual'),node(statement['subject'])))
            graph.add((identifier,URIRef(OWL+'assertionProperty'),node(statement['predicate'])))
            target='targetIndividual' if isinstance(statement['object'],str) else 'targetValue'
            graph.add((identifier,URIRef(OWL+target),node(statement['object'])))
            from ontology_provenance import add_sources
            add_sources(provenance,identifier,statement['sources'],sources,payload['context'])
    return ds, names, sorted(premises,key=lambda p:p['id'])
