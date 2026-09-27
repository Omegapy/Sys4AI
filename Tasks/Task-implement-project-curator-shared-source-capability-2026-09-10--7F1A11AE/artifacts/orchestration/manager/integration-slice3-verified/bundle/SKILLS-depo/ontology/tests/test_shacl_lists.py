"""Actual worker regression controls for shared, immutable generated shapes."""
import copy
import threading
import unittest

from support import record, project_id, standards_available, standards_environment
from ontology_core import canonical_bytes
from ontology_limits import limits
from ontology_standards import contract_asset
from ontology_worker import run_worker


def selected_payload():
    identity = project_id
    records = [record('A', kind='concept'), record('B', kind='concept'),
        record('a', **{'@type': [identity('A')]}),
        record('b', **{'@type': [identity('B')]}),
        record('c', **{'@type': [identity('B')]}),
        record('p', kind='predicate', domain=[identity('A')], range=[identity('B')],
               cardinality={'min': 0, 'max': 1}),
        record('edge', kind='relation', subject=identity('a'),
               predicate=identity('p'), object=identity('b')),
        record('external', fact_kind='external')]
    return {'records': records, 'extensions': [],
        'sources': [{**records[0]['sources'][0], 'status': 'current'}],
        'context': {'project_id': 'example', 'snapshot_sha256': 'a' * 64},
        'shapes': [contract_asset('shapes/ontology-v1.ttl').read_text()],
        'graphs': ['asserted', 'derived', 'external']}


@unittest.skipUnless(standards_available(), 'Selected real backend is unavailable')
class SharedShapeTests(unittest.TestCase):
    def run_validation(self, payload, **kwargs):
        return run_worker(standards_environment() / 'bin/python', 'validate', payload,
                          limits(overrides=kwargs.pop('budgets', None)), **kwargs)

    def outcome(self, payload, status, **kwargs):
        before = canonical_bytes(payload)
        result = self.run_validation(payload, **kwargs)
        self.assertEqual(result['status'], status, result)
        self.assertEqual(result['complete'], status in {'conformant', 'violation'}, result)
        self.assertEqual(canonical_bytes(payload), before)
        return result

    def test_domain_range_cardinality_and_source_constraints(self):
        payload = selected_payload()
        self.outcome(payload, 'conformant')
        for field, value in (('subject', project_id('b')), ('object', project_id('a'))):
            changed = copy.deepcopy(payload)
            changed['records'][6][field] = value
            result = self.outcome(changed, 'violation')
            self.assertTrue(any(f['constraint'].endswith('InConstraintComponent') for f in result['findings']))
        changed = copy.deepcopy(payload)
        changed['records'].append(record('edge2', kind='relation', subject=project_id('a'),
                                         predicate=project_id('p'), object=project_id('c')))
        result = self.outcome(changed, 'violation')
        self.assertTrue(any(f['constraint'].endswith('MaxCountConstraintComponent') for f in result['findings']))
        changed = copy.deepcopy(payload)
        changed['records'][2]['sources'] = []
        result = self.outcome(changed, 'violation')
        self.assertTrue(any(f['path'] == 'http://www.w3.org/ns/prov#wasDerivedFrom' for f in result['findings']))

    def test_changed_inputs_rebuild_complete_constraint_values(self):
        payload = selected_payload()
        payload['records'].append(record('edge2', kind='relation', subject=project_id('a'),
                                         predicate=project_id('p'), object=project_id('c')))
        self.outcome(payload, 'violation')
        payload['records'][5]['cardinality']['max'] = 2
        self.outcome(payload, 'conformant')
        payload['records'][5]['range'] = [project_id('A')]
        self.outcome(payload, 'violation')

    def test_custom_shapes_meta_validation_and_explicit_graph_scope(self):
        payload = selected_payload()
        payload['graphs'] = ['asserted', 'derived']
        result = self.outcome(payload, 'violation')
        self.assertTrue(any(f['focus_node'] == project_id('external') for f in result['findings']))
        payload['graphs'] += ['external']
        self.outcome(payload, 'conformant')
        payload['graphs'] += ['inferred']
        self.outcome(payload, 'invalid_graph_scope')
        cases = [
            ('@prefix sh:<http://www.w3.org/ns/shacl#>. <urn:s> a sh:NodeShape; sh:targetNode <urn:missing>; sh:property [sh:path <urn:p>; sh:minCount 1].', 'violation'),
            ('@prefix sh:<http://www.w3.org/ns/shacl#>. <urn:s> a sh:NodeShape; sh:targetNode <urn:x>; sh:property [sh:path <urn:p>; sh:minCount "invalid"].', 'processing_failure'),
            ('@prefix sh:<http://www.w3.org/ns/shacl#>. <urn:s> a sh:NodeShape; sh:js [sh:jsFunctionName "bad"].', 'unsupported_feature'),
            ('invalid turtle', 'malformed_rdf')]
        for shape, expected in cases:
            with self.subTest(expected=expected):
                changed = selected_payload(); changed['shapes'].append(shape)
                self.outcome(changed, expected)

    def test_incomplete_resource_and_cancellation_outcomes_remain_distinct(self):
        payload = selected_payload()
        for budget, status in (({'input_bytes': 1}, 'resource_limit'),
                               ({'input_triples': 1}, 'resource_limit'),
                               ({'rss_bytes': 1}, 'memory_limit'),
                               ({'output_bytes': 1}, 'output_limit')):
            with self.subTest(budget=budget):
                self.outcome(payload, status, budgets=budget)
        changed = copy.deepcopy(payload)
        changed['records'][2]['sources'] = []
        self.outcome(changed, 'resource_limit', budgets={'result_rows': 1})
        cancel = threading.Event(); cancel.set()
        self.outcome(payload, 'cancelled', cancel=cancel)
        cancel.clear()
        timer = threading.Timer(.05, cancel.set); timer.start()
        try:
            result = self.outcome(payload, 'cancelled', cancel=cancel)
            self.assertEqual(result['worker']['exit_code'], -9)
        finally:
            timer.join()
        # The supervisor must release its capacity after an interrupted worker.
        self.outcome(payload, 'conformant')


if __name__ == '__main__':
    unittest.main()
