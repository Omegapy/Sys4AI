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


def record_constraints(records):
    """Exact immutable constraints per target; optional packages are unnecessary."""
    from ontology_rdf import FIELD, PROV
    from ontology_advanced import CORE
    by_id={r['@id']:r for r in records}; parents={}; type_cache={}
    for r in records:
        if r.get('predicate')==CORE+'subtypeOf': parents.setdefault(r.get('subject'),set()).add(r.get('object'))
    def types(r):
        if r['@id'] not in type_cache:
            found=set(r.get('@type',[]))|({r['@id']} if r['kind']=='concept' else set()); todo=list(found)
            while todo:
                for t in parents.get(todo.pop(),()):
                    if t not in found: found.add(t); todo.append(t)
            type_cache[r['@id']]=frozenset(found)
        return type_cache[r['@id']]
    result={}; predicates=[v for v in records if v['kind']=='predicate']
    for r in records:
        constraints=[]
        def prop(path,**values): constraints.append([path,values])
        if r.get('lifecycle') in {'approved','deprecated'}:
            for field in ('definition','label','module'): prop(FIELD+field,minCount=1,minLength=1)
            prop(PROV+'wasDerivedFrom',minCount=1,nodeKind=SH+'IRI')
        for field in ('subject','predicate','object','entity'):
            if field in r:
                selected=list(by_id)
                if r['kind']=='relation' and r.get('predicate') in by_id:
                    predicate=by_id[r['predicate']]
                    if field in ('subject','object'):
                        eligible=set(predicate.get('domain' if field=='subject' else 'range',[]))
                        selected=[v['@id'] for v in records if types(v)&eligible]
                    elif field=='predicate': selected=[v['@id'] for v in predicates]
                prop(FIELD+field,minCount=1,maxCount=1,nodeKind=SH+'IRI',**{'in':sorted(selected)})
        for predicate in predicates:
            cardinality=predicate.get('cardinality',{})
            if types(r)&set(predicate.get('domain',[])):
                values={'minCount':cardinality.get('min',0)}
                if cardinality.get('max') is not None: values['maxCount']=cardinality['max']
                prop(predicate['@id'],**values)
        # RDF graphs are sets: equal constraints occur only once per target.
        result[r['@id']]=[v for _,v in sorted({canonical_bytes(c):c for c in constraints}.items())]
    return result


def shapes_for_records(records):
    """Group only identical complete constraint sets, retaining every target."""
    from rdflib import Graph, URIRef, Literal, BNode
    from ontology_rdf import ADV
    from ontology_advanced import RDF
    from ontology_core import sha256
    graph=Graph(); u=lambda v:URIRef(SH+v)
    lists={}; cells={}; properties={}; groups={}
    for rid,constraints in record_constraints(records).items():
        key=canonical_bytes(constraints)
        if key not in groups:
            shape=groups[key]=URIRef(ADV+'shape-group:'+sha256(key))
            graph.add((shape,URIRef(RDF+'type'),u('NodeShape')))
            for path,values in constraints:
                pkey=canonical_bytes([path,values])
                if pkey not in properties:
                    prop=properties[pkey]=BNode(); graph.add((prop,u('path'),URIRef(path)))
                    for name,value in values.items():
                        if name=='in':
                            members=tuple(value)
                            if members not in lists:
                                tail=URIRef(RDF+'nil')
                                for member in reversed(members):
                                    pair=(member,str(tail))
                                    if pair not in cells:
                                        cell=cells[pair]=URIRef(ADV+'shape-list:'+sha256(canonical_bytes(pair)))
                                        graph.add((cell,URIRef(RDF+'first'),URIRef(member)))
                                        graph.add((cell,URIRef(RDF+'rest'),tail))
                                    tail=cells[pair]
                                lists[members]=tail
                            term=lists[members]
                        else: term=URIRef(value) if name=='nodeKind' else Literal(value)
                        graph.add((prop,u(name),term))
                graph.add((shape,u('property'),properties[pkey]))
        graph.add((groups[key],u('targetNode'),URIRef(rid)))
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
