"""Ordered immutable suffixes and real meta-SHACL collision rejection."""
import copy
import itertools
import sys
import types
import unittest
from unittest.mock import patch
from support import record,project_id,standards_available,standards_environment
from ontology_core import canonical_bytes,sha256
from ontology_advanced import RDF
from ontology_rdf import ADV
from ontology_shacl import SH,shapes_for_records,record_constraints
from ontology_worker import run_worker
from ontology_limits import limits
from test_shacl_lists import selected_payload


def list_id(members):
    tail=RDF+'nil'
    for member in reversed(members):tail=ADV+'shape-list:'+sha256(canonical_bytes((member,tail)))
    return tail


class NamedListStructureTests(unittest.TestCase):
    def test_order_suffix_sharing_empty_and_input_change(self):
        # Record emitted RDF without importing optional packages outside the worker.
        ids=itertools.count()
        class URIRef(str):pass
        class BNode(str):
            def __new__(cls):return super().__new__(cls,'_:test'+str(next(ids)))
        class Literal:
            def __init__(self,value):self.value=value
        class Graph:
            def __init__(self):self.triples=set()
            def add(self,triple):self.triples.add(triple)
        rdf=types.ModuleType('rdflib');rdf.URIRef=URIRef;rdf.BNode=BNode;rdf.Literal=Literal;rdf.Graph=Graph
        records=selected_payload()['records'];records[4]['@type'].append(project_id('C'))
        records += [record('C',kind='concept'),record('q',kind='predicate',domain=[project_id('A')],range=[project_id('C')]),
                    record('edge2',kind='relation',subject=project_id('a'),predicate=project_id('q'),object=project_id('c'))]
        with patch.dict(sys.modules,{'rdflib':rdf}):graph=shapes_for_records(records)
        expected={tuple(values['in']) for constraints in record_constraints(records).values() for _,values in constraints if 'in' in values}
        rows=graph.triples;first={s:o for s,p,o in rows if p==RDF+'first'};rest={s:o for s,p,o in rows if p==RDF+'rest'}
        self.assertEqual(set(first),set(rest));self.assertLess(len(first),sum(map(len,expected)))
        for members in expected:
            cell=list_id(members);seen=set();actual=[]
            while cell!=RDF+'nil':
                self.assertNotIn(cell,seen);seen.add(cell);actual.append(str(first[cell]));cell=rest[cell]
            self.assertEqual(tuple(actual),members)
        self.assertEqual(rest[list_id([project_id('b'),project_id('c')])],list_id([project_id('c')]))
        changed=copy.deepcopy(records);changed[4]['@type'].remove(project_id('C'))
        changed[-2]['range']=['urn:no-eligible-type']
        with patch.dict(sys.modules,{'rdflib':rdf}):new=shapes_for_records(changed)
        self.assertIn(RDF+'nil',{o for s,p,o in new.triples if p==SH+'in'})
        self.assertEqual(len({o for s,p,o in rows if p==SH+'targetNode'}),len(records))


@unittest.skipUnless(standards_available(), 'Selected real backend is unavailable')
class NamedListWorkerTests(unittest.TestCase):
    def validate(self,payload):
        return run_worker(standards_environment()/'bin/python','validate',payload,limits())
    def test_authored_first_and_rest_collisions_reject(self):
        payload=selected_payload()
        members=[project_id('b'),project_id('c')];head=list_id(members)
        for predicate,value in [(RDF+'first','urn:corrupt'),(RDF+'rest','urn:corrupt-tail')]:
            changed=copy.deepcopy(payload);changed['shapes'].append(f'<{head}> <{predicate}> <{value}> .')
            before=canonical_bytes(changed);result=self.validate(changed)
            self.assertEqual(result['status'],'processing_failure',result);self.assertFalse(result['complete'])
            self.assertEqual(canonical_bytes(changed),before)
        self.assertEqual(self.validate(payload)['status'],'conformant')
    def test_empty_eligible_membership_rejects_value(self):
        payload=selected_payload();payload['records'][5]['range']=['urn:no-eligible-type']
        result=self.validate(payload);self.assertEqual(result['status'],'violation',result)
        self.assertTrue(any(f['focus_node']==project_id('edge') and f['constraint'].endswith('InConstraintComponent') for f in result['findings']))

if __name__=='__main__':unittest.main()
