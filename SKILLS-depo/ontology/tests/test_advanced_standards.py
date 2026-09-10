import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from advanced_support import *
from ontology_advanced import load_advanced,RDF,RDFS,OWL
from ontology_core import OntologyError,load_project
from ontology_limits import limits,DEFAULTS,CEILINGS
from ontology_profiles import health
from ontology_standards import dataset,query,validate,infer,export,stage_import,freshness,call
from ontology_derivations import verify


class StandardsAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory(prefix='ontology-advanced-tests-')
        cls.base=make_advanced(Path(cls.temporary.name)/'project')
        cls.saved={str(p.relative_to(cls.base)):p.read_bytes() for p in cls.base.rglob('*') if p.is_file() and '.venv-ontology-standards' not in p.parts}
    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()
    def setUp(self):
        self.root=self.base
        for p in self.root.rglob('*'):
            if p.is_file() and '.venv-ontology-standards' not in p.parts and str(p.relative_to(self.root)) not in self.saved: p.unlink()
        for relative,data in self.saved.items(): (self.root/relative).write_bytes(data)
    def ok(self,result,status='ok'):
        self.assertEqual(result.get('status'),status,json.dumps(result)[:2000]); self.assertTrue(result.get('complete'),result)
    def test_01_actual_profile_ready(self):
        r=health(self.root); self.assertEqual(r['status'],'ready',r); self.assertEqual(r['versions']['packages']['pyshacl'],'0.40.1')
    def test_02_v1_and_disabled_missing_versions(self):
        before=load_project(self.root).context(); cfg=read_json(self.root/'ontology-advanced.yaml')
        cfg['profiles']['standards']['enabled']=False; write_json(self.root/'ontology-advanced.yaml',cfg)
        self.assertEqual(health(self.root)['status'],'disabled'); self.assertEqual(query(self.root,'ASK {}')['status'],'profile_disabled')
        self.assertEqual(load_project(self.root).context(),before)
        cfg['schema_version']=99; write_json(self.root/'ontology-advanced.yaml',cfg)
        with self.assertRaises(OntologyError): load_advanced(self.root)
    def test_03_limits_are_finite(self):
        for key in DEFAULTS:
            for value in (0,-1,False,CEILINGS[key]+1,None):
                with self.assertRaises(OntologyError): limits({key:value})
        with self.assertRaises(OntologyError): limits({}, {'input_bytes':DEFAULTS['input_bytes']+1})
    def test_04_dataset_types_language_and_preservation(self):
        add_records(self.root,[record('item')])
        extension(self.root,annotations=[statement(self.root,'label-fr',project_id('item'),RDFS+'label',{'value':'Bonjour','language':'fr'}),statement(self.root,'number',project_id('item'),project_id('count'),{'value':'003','datatype':'http://www.w3.org/2001/XMLSchema#integer'})])
        protected={str(p):sha256(p) for p in (self.root/'ontology.yaml',self.root/'ONTOLOGY/modules/project/project.jsonld')}
        a=dataset(self.root); self.ok(a); b=dataset(self.root); self.ok(b)
        self.assertEqual(a['semantic_sha256'],b['semantic_sha256']); self.assertEqual(len(a['graphs']),4)
        self.assertTrue(any(row[2]=={'value':'Bonjour','language':'fr'} for row in a['quads']))
        self.assertEqual(protected,{p:sha256(Path(p)) for p in protected})
    def test_05_query_forms_and_from(self):
        add_records(self.root,[record('item')]); prefix='PREFIX f:<urn:sys4ai:ontology:core:field:> '
        for text,form in [(prefix+'SELECT ?s WHERE { ?s f:label "item" }','SELECT'),(prefix+'ASK { ?s f:label "item" }','ASK'),(prefix+'CONSTRUCT { ?s f:label "copy" } WHERE { ?s f:label "item" }','CONSTRUCT'),('DESCRIBE <'+project_id('item')+'>','DESCRIBE')]:
            result=query(self.root,text); self.ok(result); self.assertEqual(result['query_form'],form)
        name='urn:sys4ai:ontology:graph:example:asserted'
        self.ok(query(self.root,'SELECT ?s FROM <'+name+'> WHERE {?s ?p ?o} LIMIT 1'))
        self.ok(query(self.root,'ASK FROM NAMED <'+name+'> {GRAPH <'+name+'> {?s ?p ?o}}'))
    def test_06_prohibited_queries_and_partial(self):
        for text,status in [('INSERT DATA {<urn:a> <urn:b> <urn:c>}','prohibited_query'),('SELECT * WHERE {SERVICE <http://127.0.0.1:1/> {?s ?p ?o}}','prohibited_query'),('SELECT * FROM <file:///etc/passwd> WHERE {?s ?p ?o}','unselected_graph'),('SELECT','malformed_query'),('SELECT (RAND() AS ?x) WHERE {}','unsupported_query')]:
            r=query(self.root,text); self.assertEqual(r['status'],status,r); self.assertFalse(r['complete'])
        r=query(self.root,'SELECT * WHERE {?s ?p ?o}',limits={'result_rows':1}); self.assertEqual(r['status'],'resource_limit'); self.assertFalse(r['complete'])
        event=threading.Event(); event.set(); self.assertEqual(query(self.root,'ASK {}',cancel=event)['status'],'cancelled')
    def test_07_interchange_roundtrips(self):
        add_records(self.root,[record('item')])
        extension(self.root,annotations=[statement(self.root,'typed',project_id('item'),project_id('count'),{'value':'003','datatype':'http://www.w3.org/2001/XMLSchema#integer'}),statement(self.root,'label',project_id('item'),RDFS+'label',{'value':'bonjour','language':'fr'})])
        for format in ('json-ld','turtle','xml'):
            r=export(self.root,format,selected_graph=None if format=='json-ld' else 'asserted'); self.ok(r)
            restored=stage_import(self.root,r['content'],format,manifest=r['manifest']); self.ok(restored,'staged')
            self.assertEqual(restored['semantic_sha256'],r['manifest']['semantic_sha256']); self.assertFalse(restored['approved'])
        self.assertEqual(export(self.root,'turtle')['status'],'graph_required')
    def test_08_import_security(self):
        for format,content,status in [('json-ld','{"@context":"http://127.0.0.1:1/context","@id":"urn:a"}','prohibited_resource'),('xml','<!DOCTYPE rdf:RDF [<!ENTITY ext SYSTEM "file:///etc/passwd">]><rdf:RDF xmlns:rdf="'+RDF+'"></rdf:RDF>','prohibited_resource'),('turtle','<urn:a> <'+OWL+'imports> <file:///etc/passwd>.','prohibited_resource')]:
            manifest=None
            if format!='json-ld': manifest={'selected_graph':'urn:graph','content_sha256':sha256(content.encode())}
            self.assertEqual(stage_import(self.root,content,format,manifest)['status'],status)
    def test_09_real_shacl_overlap_and_failure(self):
        self.ok(validate(self.root),'conformant')
        add_records(self.root,[record('bad',definition='')]); r=validate(self.root); self.ok(r,'violation'); self.assertTrue(r['findings'])
        shape='@prefix sh:<http://www.w3.org/ns/shacl#>. <urn:s> a sh:NodeShape; sh:targetNode <urn:x>; sh:js [sh:jsFunctionName "evil"].'
        self.assertEqual(validate(self.root,triples=[],shapes=shape)['status'],'unsupported_feature')
        self.assertEqual(validate(self.root,triples=[],shapes='bad turtle')['status'],'malformed_rdf')
    def test_10_guard_shapes_actual(self):
        shape='@prefix sh:<http://www.w3.org/ns/shacl#>. <urn:s> a sh:NodeShape; sh:targetNode <urn:action>; sh:property [sh:path <urn:target>; sh:minCount 1; sh:maxCount 1; sh:nodeKind sh:IRI].'
        self.ok(validate(self.root,triples=[['urn:action','urn:target','urn:ok']],shapes=shape),'conformant')
        self.ok(validate(self.root,triples=[],shapes=shape),'violation')
    def test_11_generated_wiki_and_proofs(self):
        records=wiki(self.root); goal=[project_id('wiki'),RDF+'type',core_id('Artifact')]
        r=infer(self.root,goals=[goal,[project_id('wiki'),project_id('absent'),project_id('other')]]); self.ok(r)
        self.assertTrue(r['trusted']); self.assertEqual(r['conclusions'][0]['classification'],'entailed'); self.assertEqual(r['conclusions'][1]['classification'],'unproven'); self.assertTrue(verify(r['proofs']))
        again=infer(self.root,goals=[goal,[project_id('wiki'),project_id('absent'),project_id('other')]]); self.assertEqual(r['proofs'],again['proofs'])
        restricted=infer(self.root,goals=[goal],premise_ids=[records[1]['@id']]); self.ok(restricted); self.assertEqual(restricted['conclusions'][0]['classification'],'unproven')
    def test_12_property_and_oracle(self):
        p=project_id('rel'); inv=project_id('inverse'); sym=project_id('symmetric'); a,b,c=[project_id(x) for x in 'abc']
        axioms=[statement(self.root,'a1',p,RDF+'type',OWL+'TransitiveProperty'),statement(self.root,'a2',p,OWL+'inverseOf',inv),statement(self.root,'a3',a,p,b),statement(self.root,'a4',b,p,c),statement(self.root,'a5',sym,RDF+'type',OWL+'SymmetricProperty'),statement(self.root,'a6',a,sym,b),statement(self.root,'a7',project_id('small'),RDFS+'subPropertyOf',p),statement(self.root,'a8',a,project_id('small'),c)]
        extension(self.root,axioms=axioms)
        result=infer(self.root,goals=[[a,p,c],[c,inv,a],[b,sym,a]]); self.ok(result)
        self.assertTrue(all(c['classification']=='entailed' for c in result['conclusions']))
        oracle=call(self.root,'oracle'); self.ok(oracle)
        oracle_set={tuple(t) for t in oracle['triples'] if all(isinstance(x,str) for x in t)}
        self.assertTrue({tuple(t) for t in result['inferred']}<=oracle_set)
    def test_13_conflicts_negative_unproven(self):
        a,A,B=project_id('a'),project_id('A'),project_id('B')
        extension(self.root,axioms=[statement(self.root,'x1',a,RDF+'type',A),statement(self.root,'x2',a,RDF+'type',B),statement(self.root,'x3',A,OWL+'disjointWith',B)],negatives=[statement(self.root,'n1',a,project_id('p'),project_id('b'))])
        result=infer(self.root,goals=[[a,RDF+'type',A],[a,project_id('p'),project_id('b')]])
        self.ok(result,'inconsistent'); self.assertFalse(result['trusted']); self.assertEqual(result['conflicts'][0]['kind'],'disjoint_types')
        only=infer(self.root,goals=[[a,project_id('p'),project_id('b')]],premise_ids=[project_id('n1')]); self.ok(only); self.assertEqual(only['conclusions'][0]['classification'],'contradicted')
    def test_14_stale_unsupported_and_limits(self):
        wiki(self.root); result=infer(self.root); self.ok(result)
        (self.root/'SPECS.md').write_text('changed\n'); self.assertEqual(freshness(self.root,result)['status'],'stale_input'); self.assertEqual(infer(self.root)['status'],'stale_input')
        (self.root/'SPECS.md').write_bytes(self.saved['SPECS.md'])
        add_records(self.root,[record('wiki2',**{'@type':[project_id('GeneratedWikiPage')]})])
        result=infer(self.root,limits={'derived_triples':1,'proof_nodes':1000}); self.assertEqual(result['status'],'resource_limit'); self.assertFalse(result['complete'])
        extension(self.root,axioms=[statement(self.root,'unsupported',project_id('P'),RDF+'type',OWL+'FunctionalProperty')]); self.assertEqual(infer(self.root)['status'],'unsupported_semantics')
    def test_15_unselected_symlink_and_core_redefinition(self):
        path=self.root/'ONTOLOGY/extensions'; path.mkdir(exist_ok=True)
        (path/'linked.json').symlink_to(self.root/'ontology.yaml')
        cfg=read_json(self.root/'ontology-advanced.yaml');cfg['extensions']=[{'path':'ONTOLOGY/extensions/linked.json','sha256':sha256(self.root/'ontology.yaml')}];write_json(self.root/'ontology-advanced.yaml',cfg)
        self.assertEqual(query(self.root,'ASK {}')['status'],'unsafe_symlink')
        (path/'linked.json').unlink();extension(self.root,axioms=[statement(self.root,'redefine',core_id('Artifact'),RDFS+'subClassOf',project_id('Other'))])
        self.assertEqual(infer(self.root)['status'],'core_redefinition')
    def test_16_equivalence_identity_and_conflicts(self):
        a,b=project_id('a'),project_id('b'); A,B=project_id('A'),project_id('B'); p,q=project_id('p'),project_id('q')
        axioms=[statement(self.root,'eqc',A,OWL+'equivalentClass',B),statement(self.root,'eqp',p,OWL+'equivalentProperty',q),statement(self.root,'t',a,RDF+'type',A),statement(self.root,'edge',a,p,project_id('c')),statement(self.root,'eq',a,OWL+'sameAs',b)]
        extension(self.root,axioms=axioms)
        r=infer(self.root,goals=[[b,RDF+'type',B],[b,q,project_id('c')]]);self.ok(r);self.assertTrue(all(c['trusted'] for c in r['conclusions']))
        axioms.append(statement(self.root,'diff',a,OWL+'differentFrom',b)); extension(self.root,axioms=axioms)
        r=infer(self.root);self.ok(r,'inconsistent');self.assertTrue(any(c['kind']=='inconsistent_identity' for c in r['conflicts']))
    def test_17_draft_exclusion_and_preview(self):
        wiki(self.root); add_records(self.root,[record('draft',lifecycle='draft',**{'@type':[project_id('GeneratedWikiPage')]})])
        goal=[project_id('draft'),RDF+'type',core_id('Artifact')]
        r=infer(self.root,goals=[goal]);self.ok(r);self.assertEqual(r['conclusions'][0]['classification'],'unproven')
        rel='ONTOLOGY/modules/project/project.jsonld'; doc=read_json(self.root/rel)
        next(x for x in doc['@graph'] if x['@id']==project_id('draft'))['lifecycle']='approved'
        preview=infer(self.root,goals=[goal],overrides={rel:canonical_bytes(doc)});self.ok(preview);self.assertTrue(preview['context']['preview']);self.assertEqual(preview['conclusions'][0]['classification'],'entailed')
        self.assertEqual(next(x for x in read_json(self.root/rel)['@graph'] if x['@id']==project_id('draft'))['lifecycle'],'draft')
    def test_18_blanknode_semantic_roundtrip(self):
        from ontology_worker import run_worker
        env=self.root/'.venv-ontology-standards/bin/python'
        raw='[{"@id":"urn:graph","@graph":[{"@id":"_:a","urn:label":[{"@value":"français","@language":"fr"}],"urn:child":[{"@id":"_:b"}]},{"@id":"_:b","urn:label":[{"@value":"child"}]}]}]'
        a=stage_import(self.root,raw,'json-ld');self.ok(a,'staged')
        b=stage_import(self.root,raw.replace('_:a','_:renamed').replace('_:b','_:other'),'json-ld');self.ok(b,'staged');self.assertEqual(a['semantic_sha256'],b['semantic_sha256'])
    def test_19_query_budgets_and_selected_scope(self):
        r=query(self.root,'SELECT ?x WHERE { VALUES ?x {1 2} }',limits={'output_bytes':400});self.assertEqual(r['status'],'output_limit');self.assertFalse(r['complete'])
        r=query(self.root,'ASK {}',limits={'input_triples':1});self.assertEqual(r['status'],'resource_limit')
        r=query(self.root,'ASK {}',limits={'input_bytes':100});self.assertEqual(r['status'],'resource_limit')
        self.assertEqual(query(self.root,'ASK {}',graphs=['urn:other:project'])['status'],'unselected_graph')
        self.ok(query(self.root,'PREFIX g:<urn:sys4ai:ontology:graph:example:> ASK FROM g:asserted {?s ?p ?o}'))
    def test_20_real_worker_capacity(self):
        from ontology_worker import run_worker
        env=self.root/'.venv-ontology-standards/bin/python'; event=threading.Event(); outcomes=[]
        def run(): outcomes.append(run_worker(env,'probe_timeout',{},limits(overrides={'query_seconds':3}),cancel=event))
        first=threading.Thread(target=run); second=threading.Thread(target=run);first.start();second.start()
        import time
        time.sleep(.3)
        third=run_worker(env,'versions',{},limits());event.set();first.join();second.join()
        self.assertEqual(third['status'],'worker_capacity');self.assertTrue(all(r['status']=='cancelled' for r in outcomes))
        self.ok(run_worker(env,'versions',{},limits()))
    def test_21_inferred_provenance_interchange(self):
        wiki(self.root)
        result=infer(self.root);self.ok(result)
        self.assertTrue(any(q[1]=='http://www.w3.org/ns/prov#wasGeneratedBy' for q in result['provenance']))
        answer=query(self.root,'ASK {<'+project_id('wiki')+'> a <'+core_id('Artifact')+'>}',graphs=['inferred']);self.ok(answer);self.assertTrue(answer['answer'])
        exported=export(self.root,'turtle',selected_graph='inferred');self.ok(exported)
        restored=stage_import(self.root,exported['content'],'turtle',exported['manifest']);self.ok(restored,'staged')
        self.assertTrue(any(row[:3]==[project_id('wiki'),RDF+'type',core_id('Artifact')] for row in restored['quads']))
    def test_22_negative_and_structured_metadata_export(self):
        negative=statement(self.root,'negative',project_id('a'),project_id('p'),project_id('b'))
        extension(self.root,negatives=[negative])
        result=dataset(self.root);self.ok(result)
        self.assertTrue(any(row[:3]==[negative['id'],RDF+'type',OWL+'NegativePropertyAssertion'] for row in result['quads']))
        self.assertTrue(any(row[1]==core_id('field:cardinality') and isinstance(row[2],dict) and row[2].get('datatype')==RDF+'JSON' for row in result['quads']))
        result=export(self.root,'json-ld');self.ok(result)
        restored=stage_import(self.root,result['content'],'json-ld',result['manifest']);self.ok(restored,'staged');self.assertFalse(restored['unsupported_constructs'])


if __name__=='__main__': unittest.main()
