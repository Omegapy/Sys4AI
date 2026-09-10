"""Restricted byte parsers and attributed interchange; imports never publish."""
from ontology_core import OntologyError, canonical_bytes, decode_json, require, sha256

FORMATS={'json-ld','turtle','xml'}


def parse(data, format, *, graph_id=None, bound=None):
    from rdflib import Dataset, Graph, URIRef
    from ontology_rdf import ADV
    from ontology_advanced import OWL
    require(format in FORMATS,'unsupported_format','Supported interchange formats are json-ld, turtle and xml.')
    require(isinstance(data,str),'invalid_input','Parser accepts selected UTF-8 bytes as text only.')
    if bound: require(len(data.encode())<=bound['input_bytes'],'resource_limit','Parser input exceeds input_bytes.')
    if format=='json-ld':
        document=decode_json(data.encode())
        def inspect(value):
            if isinstance(value,dict):
                for k,v in value.items():
                    if k=='@context':
                        require(not isinstance(v,str),'prohibited_resource','Remote and file JSON-LD contexts are forbidden.')
                        if isinstance(v,list): require(not any(isinstance(x,str) for x in v),'prohibited_resource','Remote JSON-LD contexts are forbidden.')
                    require(k not in {'@import','@base'},'prohibited_resource','Context imports and base resolution are forbidden.')
                    inspect(v)
            elif isinstance(value,list):
                for item in value: inspect(item)
        inspect(document)
    if format=='xml':
        # Reject the XML DTD structure with Expat, before the RDF/XML parser sees
        # entity text. OS confinement independently denies any resource access.
        import xml.parsers.expat
        parser=xml.parsers.expat.ParserCreate()
        def forbidden(*args): raise OntologyError('prohibited_resource','XML DTDs and external entities are forbidden.')
        parser.StartDoctypeDeclHandler=forbidden; parser.ExternalEntityRefHandler=forbidden
        try: parser.Parse(data,True)
        except OntologyError: raise
        except xml.parsers.expat.ExpatError as exc: raise OntologyError('malformed_rdf','Malformed XML.') from exc
    ds=Dataset(default_union=False)
    target=ds if format=='json-ld' and graph_id is None else ds.graph(URIRef(graph_id or ADV+'import'))
    try: target.parse(data=data,format=format,publicID='urn:sys4ai:ontology:import:base')
    except Exception as exc: raise OntologyError('malformed_rdf',str(exc)[:500]) from exc
    require(not any(ds.quads((None,URIRef(OWL+'imports'),None,None))),'prohibited_resource','OWL imports are not selected resources.')
    if bound: require(sum(1 for _ in ds.quads((None,None,None,None)))<=bound['input_triples'],'resource_limit','Parsed RDF exceeds input_triples.')
    return ds


def export(dataset, names, format, selected_graph=None):
    from rdflib import URIRef
    from ontology_rdf import quad_rows
    require(format in FORMATS,'unsupported_format','Unsupported export format.')
    if format!='json-ld': require(selected_graph in set(names)|set(names.values()),'graph_required','Graph-only export requires an explicit selected graph and its manifest.')
    graph_id=names.get(selected_graph,selected_graph)
    source=dataset if graph_id is None else dataset.graph(URIRef(graph_id))
    if format=='json-ld':
        # RDFLib 7.6.0's serializer wraps use_native_types in a truthy tuple.
        # Its public converter accepts the Boolean correctly, retaining lexical
        # forms such as xsd:integer "003" rather than coercing them to JSON 3.
        import json
        from rdflib.plugins.serializers.jsonld import from_rdf
        content=json.dumps(from_rdf(source,use_native_types=False),ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    elif format=='turtle':
        # Explicit RDF term syntax is a valid Turtle subset. Numeric shorthand
        # is avoided because its parser coerces the literal's lexical form.
        from ontology_rdf import normalized_triples,node
        content='\n'.join(' '.join(node(value).n3() for value in triple)+' .' for triple in normalized_triples(source))+'\n'
    else: content=source.serialize(format=format)
    manifest={'schema_version':1,'format':format,'selected_graph':graph_id,'graph_names':names,
        'content_sha256':sha256(content.encode()),'semantic_sha256':sha256(canonical_bytes(quad_rows(dataset if graph_id is None else _single(source,graph_id)))),
        'provenance':'PROV-O triples remain in their original graph; other graph classes are explicitly excluded from a selected-graph export.',
        'approval':False}
    return {'status':'ok','complete':True,'content':content,'manifest':manifest}


def _single(graph,graph_id):
    from rdflib import Dataset,URIRef
    ds=Dataset()
    for triple in graph: ds.graph(URIRef(graph_id)).add(triple)
    return ds


def stage(data,format,manifest,bound):
    from ontology_rdf import quad_rows
    if format!='json-ld':
        require(isinstance(manifest,dict) and manifest.get('selected_graph'),'graph_required','A graph-only import requires its context/provenance manifest.')
    if manifest:
        require(manifest.get('content_sha256')==sha256(data.encode()),'manifest_changed','Import bytes differ from their export manifest.')
    ds=parse(data,format,graph_id=manifest.get('selected_graph') if manifest else None,bound=bound)
    rows=quad_rows(ds); semantic=sha256(canonical_bytes(rows))
    if manifest: require(manifest.get('semantic_sha256')==semantic,'semantic_mismatch','Interchange does not preserve selected dataset semantics.')
    from ontology_advanced import OWL
    unsupported=sorted({r[1] for r in rows if r[1].startswith(OWL) and r[1].rsplit('#',1)[-1] not in {'equivalentClass','equivalentProperty','sameAs','differentFrom','inverseOf','disjointWith','propertyDisjointWith','sourceIndividual','assertionProperty','targetIndividual','targetValue'}})
    return {'status':'staged','complete':True,'proposal_kind':'rdf-import','approved':False,'quads':rows,
        'content_sha256':sha256(data.encode()),'semantic_sha256':semantic,'unsupported_constructs':unsupported,
        'diagnostics':[{'code':'unsupported_semantics','message':x} for x in unsupported]}
