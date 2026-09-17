"""Full computation equivalence and explicit bounded diagnostic failures."""
import copy
import threading
import unittest
from advanced_support import *
from support import standards_available, standards_environment
from ontology_advanced import RDF,RDFS
from ontology_backend import _diagnostic
from ontology_limits import limits
from ontology_standards import infer,infer_diagnostic,call
from ontology_worker import run_worker
from test_shacl_lists import selected_payload


@unittest.skipUnless(standards_available(), 'Selected real backend is unavailable')
class DiagnosticWorkerTests(unittest.TestCase):
    def run_infer(self,payload,**budgets):
        return run_worker(standards_environment()/'bin/python','infer',payload,limits(overrides=budgets))

    def test_identical_full_computation_counts_digests_and_negative_conflict(self):
        payload=selected_payload()
        source=payload['records'][0]['sources']
        def stmt(name,s,p,o): return {'id':'urn:'+name,'subject':s,'predicate':p,'object':o,'sources':source}
        payload['extensions']=[{'axioms':[stmt('type','urn:a',RDF+'type','urn:A'),
          stmt('duplicate','urn:a',RDF+'type','urn:A'),stmt('subclass','urn:A',RDFS+'subClassOf','urn:B')],
          'annotations':[],'negative_assertions':[stmt('negative','urn:a',RDF+'type','urn:B')]}]
        payload['goals']=[['urn:a',RDF+'type','urn:B']]
        full=self.run_infer(payload); self.assertEqual(full['status'],'inconsistent',full)
        diagnostic=self.run_infer({**payload,'result_mode':'diagnostic'})
        for key,value in _diagnostic(full,payload).items():
            if key not in {'worker','versions'}: self.assertEqual(diagnostic[key],value,key)
        self.assertFalse(diagnostic['trusted']);self.assertTrue(diagnostic['complete'])
        self.assertEqual(diagnostic['reasoning_scope'],'full_selected_closure')
        self.assertNotIn('proofs',diagnostic);self.assertNotIn('provenance',diagnostic)
        subset={**payload,'premise_ids':['urn:negative'],'result_mode':'diagnostic'}
        result=self.run_infer(subset);self.assertEqual(result['status'],'ok',result)
        self.assertEqual(result['reasoning_scope'],'selected_premise_closure')
        self.assertEqual(result['conclusions'][0]['classification'],'contradicted')
        self.assertEqual(result['evidence']['negative_assertions']['count'],1)

    def test_full_output_limit_retained_and_diagnostic_output_bounded(self):
        payload=selected_payload()
        payload['records'] += [record('additional-'+str(i)) for i in range(800)]
        before=canonical_bytes(payload)
        self.assertEqual(self.run_infer(payload)['status'],'output_limit')
        diagnostic=self.run_infer({**payload,'result_mode':'diagnostic'})
        self.assertEqual(diagnostic['status'],'ok',diagnostic);self.assertTrue(diagnostic['complete'])
        self.assertEqual(self.run_infer({**payload,'result_mode':'diagnostic'},output_bytes=1)['status'],'output_limit')
        self.assertEqual(canonical_bytes(payload),before)

    def test_rejection_incompleteness_and_cancellation(self):
        payload={**selected_payload(),'result_mode':'diagnostic'}
        for mode in ('typo',[],{},None,False):
            self.assertEqual(self.run_infer({**payload,'result_mode':mode})['status'],'invalid_result_mode')
        self.assertEqual(self.run_infer({**payload,'premise_ids':['urn:unselected']})['status'],'unselected_premise')
        changed=copy.deepcopy(payload);changed['sources'][0]['status']='stale'
        stale=self.run_infer(changed);self.assertEqual(stale['status'],'stale_input');self.assertFalse(stale['trusted'])
        self.assertIsNone(stale['evidence']['proofs'])
        for budget,status in [({'proof_nodes':1},'resource_limit'),({'input_bytes':1},'resource_limit'),
                              ({'input_triples':1},'resource_limit'),({'rss_bytes':1},'memory_limit')]:
            result=self.run_infer(payload,**budget);self.assertEqual(result['status'],status,result);self.assertFalse(result['complete'])
        source=payload['records'][0]['sources']
        axioms=[{'id':'urn:s'+str(i),'subject':'urn:A'+str(i),'predicate':RDFS+'subClassOf','object':'urn:A'+str(i+1),'sources':source} for i in range(10)]
        changed={**payload,'extensions':[{'axioms':axioms,'annotations':[],'negative_assertions':[]}]}
        for budget in ({'derived_triples':1},{'rule_rounds':1}):
            result=self.run_infer(changed,**budget);self.assertEqual(result['status'],'resource_limit',result);self.assertFalse(result['trusted'])
        chain=[{'id':'urn:t'+str(i),'subject':'urn:T'+str(i),'predicate':RDFS+'subClassOf',
                'object':'urn:T'+str(i+1),'sources':source} for i in range(150)]
        large={**payload,'extensions':[{'axioms':chain,'annotations':[],'negative_assertions':[]}]}
        self.assertEqual(self.run_infer(large,reasoning_seconds=1)['status'],'timeout')
        cancel=threading.Event();cancel.set()
        result=run_worker(standards_environment()/'bin/python','infer',payload,limits(),cancel=cancel)
        self.assertEqual(result['status'],'cancelled');self.assertFalse(result['complete'])


@unittest.skipUnless(standards_available(), 'Selected real backend is unavailable')
class DiagnosticPublicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.temp=tempfile.TemporaryDirectory();cls.base=make_advanced(Path(cls.temp.name)/'project')
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def test_public_snapshot_profile_and_health_scope(self):
        from ontology_health import advanced_health
        root=self.base; result=infer_diagnostic(root)
        self.assertEqual(result['status'],'ok',result)
        self.assertEqual(infer_diagnostic(root,expected_snapshot='0'*64)['status'],'stale_input')
        before=(root/'SPECS.md').read_bytes();(root/'SPECS.md').write_text('changed')
        # The core fixture has no project source records; add one to exercise stale provenance.
        add_records(root,[record('source')]);self.assertEqual(infer_diagnostic(root)['status'],'stale_input')
        (root/'SPECS.md').write_bytes(before)
        result=advanced_health(root,scope='canonical',level='operational',required=['inference'])
        component=result['assessment']['components']['inference'];self.assertTrue(component['ready'],result)
        self.assertIn('counts_and_digests_only',component['probe_scope'])
        self.assertIn('not_exercised',component['full_proof_delivery'])
        static=advanced_health(root,scope='canonical',required=['inference'])
        self.assertEqual(static['assessment']['components']['inference']['observed_operation'],'not_exercised')
        cfg=read_json(root/'ontology-advanced.yaml');cfg['profiles']['inference']['enabled']=False;write_json(root/'ontology-advanced.yaml',cfg)
        self.assertEqual(infer_diagnostic(root)['status'],'profile_disabled')
        self.assertEqual(infer(root)['status'],'profile_disabled')

if __name__=='__main__':unittest.main()
