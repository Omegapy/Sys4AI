"""Complete target constraints and actual confined grouped-target negatives."""
import copy
import unittest
from support import record,project_id,standards_available,standards_environment
from ontology_core import canonical_bytes
from ontology_shacl import record_constraints
from ontology_limits import limits
from ontology_worker import run_worker
from test_shacl_lists import selected_payload

class ConstraintPlanTests(unittest.TestCase):
    def test_complete_target_membership_and_single_constraint_separation(self):
        payload=selected_payload();records=payload['records'];plans=record_constraints(records)
        self.assertEqual(set(plans),{r['@id'] for r in records})
        self.assertEqual(plans[project_id('b')],plans[project_id('c')])
        self.assertNotEqual(plans[project_id('a')],plans[project_id('b')])
        changed=copy.deepcopy(records);changed[4]['lifecycle']='draft'
        self.assertNotEqual(record_constraints(changed)[project_id('c')],plans[project_id('b')])
        changed=copy.deepcopy(records);changed[5]['cardinality']['min']=1
        self.assertNotEqual(record_constraints(changed)[project_id('a')],plans[project_id('a')])
        changed=copy.deepcopy(records);changed[5]['range']=[project_id('A')]
        self.assertNotEqual(record_constraints(changed)[project_id('edge')],plans[project_id('edge')])
        self.assertEqual(record_constraints(list(reversed(records))),plans)

@unittest.skipUnless(standards_available(), 'Selected real backend is unavailable')
class GroupedTargetNegatives(unittest.TestCase):
    def validate(self,payload):
        before=canonical_bytes(payload)
        result=run_worker(standards_environment()/'bin/python','validate',payload,limits())
        self.assertEqual(before,canonical_bytes(payload));return result
    def test_each_shared_target_and_binding_metadata_cardinality(self):
        payload=selected_payload();self.assertEqual(self.validate(payload)['status'],'conformant')
        for index,field,value in [(3,'definition',''),(4,'label',''),(3,'module',''),(4,'sources',[])]:
            changed=copy.deepcopy(payload);changed['records'][index][field]=value
            result=self.validate(changed);self.assertEqual(result['status'],'violation',result)
            self.assertTrue(any(f['focus_node']==changed['records'][index]['@id'] for f in result['findings']))
        changed=copy.deepcopy(payload);changed['records'][5]['cardinality']['min']=1;changed['records'].pop(6)
        result=self.validate(changed);self.assertEqual(result['status'],'violation',result)
        self.assertTrue(any(f['focus_node']==project_id('a') and f['constraint'].endswith('MinCountConstraintComponent') for f in result['findings']))
        for value,constraint in [('urn:absent','InConstraintComponent'),({'value':'literal'},'NodeKindConstraintComponent')]:
            changed=copy.deepcopy(payload);changed['records'].append(record('binding',kind='binding',entity=value))
            result=self.validate(changed);self.assertEqual(result['status'],'violation',result)
            self.assertTrue(any(f['focus_node']==project_id('binding') and f['constraint'].endswith(constraint) for f in result['findings']))
        changed=copy.deepcopy(payload);changed['shapes'].append('<urn:s> <http://www.w3.org/2002/07/owl#imports> <file:///etc/passwd>.')
        self.assertEqual(self.validate(changed)['status'],'prohibited_resource')

if __name__=='__main__':unittest.main()
