"""PROV-O production/evidence attribution. This vocabulary grants no authority."""
from ontology_core import canonical_bytes, sha256


def add_sources(graph, subject, references, statuses, context):
    from rdflib import URIRef, Literal
    from ontology_rdf import PROV, ADV
    from ontology_advanced import RDF
    activity=URIRef('urn:sys4ai:ontology:activity:projection:'+context['snapshot_sha256'])
    graph.add((activity,URIRef(RDF+'type'),URIRef(PROV+'Activity')))
    graph.add((activity,URIRef(ADV+'adapterVersion'),Literal('2.0.0')))
    graph.add((subject,URIRef(RDF+'type'),URIRef(PROV+'Entity')))
    graph.add((subject,URIRef(PROV+'wasGeneratedBy'),activity))
    for reference in references:
        source=URIRef('urn:sys4ai:ontology:source:'+sha256(canonical_bytes(reference)))
        graph.add((source,URIRef(RDF+'type'),URIRef(PROV+'Entity')))
        graph.add((subject,URIRef(PROV+'wasDerivedFrom'),source))
        graph.add((activity,URIRef(PROV+'used'),source))
        for key,value in reference.items(): graph.add((source,URIRef(ADV+key),Literal(value)))
        status=statuses.get(canonical_bytes(reference),{}).get('status','unavailable')
        graph.add((source,URIRef(ADV+'freshness'),Literal(status)))


def proof_quads(result,project_id):
    """Serializable PROV-O inference provenance, independent of RDF libraries."""
    from ontology_advanced import RDF
    from ontology_rdf import PROV,ADV,graph_ids
    graph=graph_ids(project_id)['derived'];rows=[]
    for proof in result.get('proofs',[]):
        identity=proof['id']
        rows.append([identity,RDF+'type',PROV+'Entity',graph])
        for field,value in zip(('subject','predicate','object'),proof['triple']): rows.append([identity,RDF+field,value,graph])
        if proof['rule']=='premise':
            for source in proof.get('sources',[]):
                entity='urn:sys4ai:ontology:source:'+sha256(canonical_bytes(source))
                rows.append([identity,PROV+'wasDerivedFrom',entity,graph])
        else:
            activity=identity+':activity'
            rows.extend([[identity,PROV+'wasGeneratedBy',activity,graph],[activity,RDF+'type',PROV+'Activity',graph],
                         [activity,ADV+'rule','urn:sys4ai:ontology:rule:'+proof['rule'],graph]])
            for premise in proof['premises']:
                rows.extend([[identity,PROV+'wasDerivedFrom',premise,graph],[activity,PROV+'used',premise,graph]])
    return sorted(rows,key=canonical_bytes)
