"""Real pySHACL core constraint validation with closed feature selection."""
from ontology_core import OntologyError, canonical_bytes, require

SH='http://www.w3.org/ns/shacl#'
ALLOWED={'NodeShape','PropertyShape','targetNode','targetClass','targetSubjectsOf','targetObjectsOf',
    'property','path','minCount','maxCount','minLength','maxLength','datatype','class','nodeKind',
    'IRI','BlankNode','Literal','BlankNodeOrIRI','IRIOrLiteral','BlankNodeOrLiteral','in','hasValue',
    'node','or','and','not','xone','closed','ignoredProperties','pattern','flags','message','severity',
    'Violation','Warning','Info','name','description','order','deactivated','qualifiedValueShape',
    'qualifiedMinCount','qualifiedMaxCount','qualifiedValueShapesDisjoint','equals','disjoint',
    'lessThan','lessThanOrEquals','minInclusive','maxInclusive','minExclusive','maxExclusive',
    'languageIn','uniqueLang','alternativePath','inversePath','zeroOrMorePath','oneOrMorePath','zeroOrOnePath'}


def shapes_for_records(records):
    """Build every target, sharing only equal immutable constraint subgraphs."""
    from rdflib import Graph, URIRef, Literal, BNode
    from rdflib.collection import Collection
    from ontology_rdf import FIELD, PROV, ADV
    from ontology_advanced import RDF, CORE
    graph=Graph(); u=lambda v:URIRef(SH+v)
    # Per-call caches never retain shapes across input or package revisions.
    lists={}; properties={}
    by_id={r['@id']:r for r in records}; parents={}
    for r in records:
        if r.get('predicate')==CORE+'subtypeOf': parents.setdefault(r.get('subject'),set()).add(r.get('object'))
    def types(r):
        found=set(r.get('@type',[]))|({r['@id']} if r['kind']=='concept' else set()); todo=list(found)
        while todo:
            for t in parents.get(todo.pop(),()):
                if t not in found: found.add(t); todo.append(t)
        return found
    def prop(shape,path,**values):
        constraints=tuple(sorted((key,value if isinstance(value,(URIRef,BNode)) else Literal(value)) for key,value in values.items()))
        key=(path,constraints)
        if key not in properties:
            p=properties[key]=BNode(); graph.add((p,u('path'),URIRef(path)))
            for name,value in constraints: graph.add((p,u(name),value))
        graph.add((shape,u('property'),properties[key]))
    for r in records:
        rid=URIRef(r['@id']); shape=URIRef(ADV+'shape:'+r['@id']); graph.add((shape,URIRef(RDF+'type'),u('NodeShape'))); graph.add((shape,u('targetNode'),rid))
        if r.get('lifecycle') in {'approved','deprecated'}:
            for field in ('definition','label','module'):
                prop(shape,FIELD+field,minCount=1,minLength=1)
            prop(shape,PROV+'wasDerivedFrom',minCount=1,nodeKind=u('IRI'))
        for field in ('subject','predicate','object','entity'):
            if field in r:
                selected=list(by_id)
                if r['kind']=='relation' and r.get('predicate') in by_id:
                    predicate=by_id[r['predicate']]
                    if field in ('subject','object'):
                        eligible=set(predicate.get('domain' if field=='subject' else 'range',[]))
                        selected=[v['@id'] for v in records if types(v)&eligible]
                    elif field=='predicate': selected=[v['@id'] for v in records if v['kind']=='predicate']
                # Equal immutable value lists may share RDF cells. Keep this
                # cache local to this graph so changed inputs are always rebuilt.
                values=tuple(sorted(selected))
                if values not in lists:
                    lists[values]=BNode()
                    Collection(graph,lists[values],[URIRef(x) for x in values])
                prop(shape,FIELD+field,minCount=1,maxCount=1,nodeKind=u('IRI'),**{'in':lists[values]})
        for predicate in (v for v in records if v['kind']=='predicate'):
            cardinality=predicate.get('cardinality',{})
            if types(r)&set(predicate.get('domain',[])):
                values={'minCount':cardinality.get('min',0)}
                if cardinality.get('max') is not None: values['maxCount']=cardinality['max']
                prop(shape,predicate['@id'],**values)
    return graph


def validate(dataset,names,selected,records,shape_texts,bound,custom_triples=None):
    from rdflib import Graph, URIRef
    from ontology_rdf import node,encode
    from ontology_interchange import parse
    from ontology_advanced import RDF, OWL
    import pyshacl
    from pyshacl.errors import ValidationFailure
    require(not any(k in {'inferred',names['inferred']} for k in selected),'invalid_graph_scope','SHACL authoring validation cannot use inferred evidence.')
    data=Graph()
    if custom_triples is not None:
        for triple in custom_triples:
            require(isinstance(triple,list) and len(triple)==3,'invalid_input','Validation triples require three RDF terms.')
            data.add(tuple(node(x) for x in triple))
        shapes=Graph()
    else:
        for kind in selected:
            for triple in dataset.graph(URIRef(names.get(kind,kind))): data.add(triple)
        shapes=shapes_for_records(records)
    for text in shape_texts:
        parsed=parse(text,'turtle',graph_id='urn:sys4ai:ontology:shapes',bound=bound)
        for s,p,o,g in parsed.quads((None,None,None,None)): shapes.add((s,p,o))
    for s,p,o in shapes:
        for value in (p,o):
            if str(value).startswith(SH): require(str(value)[len(SH):] in ALLOWED,'unsupported_feature','SHACL feature is outside the selected non-executable profile: '+str(value))
        require(str(p)!=OWL+'imports','unsupported_feature','Shape imports are forbidden.')
    try:
        conforms,report,_=pyshacl.validate(data,shacl_graph=shapes,inference='none',advanced=False,js=False,
            do_owl_imports=False,meta_shacl=True,inplace=False,abort_on_first=False,allow_infos=False,allow_warnings=False,max_validation_depth=32)
    except Exception as exc:
        return {'status':'processing_failure','complete':False,'diagnostics':[{'code':type(exc).__name__,'message':str(exc)[:1000]}],'inference':'none','graph_scope':selected}
    if isinstance(report,ValidationFailure):
        return {'status':'processing_failure','complete':False,'diagnostics':[{'code':'ValidationFailure','message':str(report)[:1000]}],'inference':'none','graph_scope':selected}
    findings=[]
    for result in report.subjects(URIRef(RDF+'type'),URIRef(SH+'ValidationResult')):
        finding={}
        for label,predicate in (('focus_node','focusNode'),('path','resultPath'),('shape','sourceShape'),('severity','resultSeverity'),('message','resultMessage'),('constraint','sourceConstraintComponent')):
            value=report.value(result,URIRef(SH+predicate)); finding[label]=encode(value) if value is not None else None
        findings.append(finding)
    findings.sort(key=canonical_bytes)
    if len(findings)>bound['result_rows']:
        return {'status':'resource_limit','complete':False,'limit':'result_rows','findings':findings[:bound['result_rows']],'inference':'none','graph_scope':selected}
    return {'status':'conformant' if conforms else 'violation','complete':True,'conforms':bool(conforms),
        'findings':findings,'diagnostics':[],'inference':'none','graph_scope':selected,'authority':False}
