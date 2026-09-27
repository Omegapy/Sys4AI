"""Actual-worker RDF identity controls for ground and blank-node datasets."""
import copy
import json
import unittest

from support import standards_available, standards_environment
from ontology_core import canonical_bytes, sha256
from ontology_limits import limits
from ontology_worker import run_worker

INTEGER = 'http://www.w3.org/2001/XMLSchema#integer'


def ground_document():
    return [{'@id': 'urn:graph:one', '@graph': [{'@id': 'urn:subject',
        'urn:predicate': [{'@id': 'urn:object'}],
        'urn:number': [{'@value': '003', '@type': INTEGER}],
        'urn:label': [{'@value': 'Bonjour', '@language': 'fr'}]}]},
        {'@id': 'urn:graph:two', '@graph': [{'@id': 'urn:subject',
         'urn:predicate': [{'@id': 'urn:object'}]}]}]


def blank_document():
    return [{'@id': 'urn:graph:one', '@graph': [
        {'@id': '_:a', 'urn:link': [{'@id': '_:b'}], 'urn:label': [{'@value': 'root'}]},
        {'@id': '_:b', 'urn:link': [{'@id': '_:a'}]}]},
        {'@id': 'urn:graph:two', '@graph': [
        {'@id': '_:b', 'urn:label': [{'@value': 'shared'}]},
        {'@id': '_:a', 'urn:link': [{'@id': '_:c'}]},
        {'@id': '_:c', 'urn:number': [{'@value': '003', '@type': INTEGER}]}]}]


@unittest.skipUnless(standards_available(), 'Selected real backend is unavailable')
class RDFCanonicalizationTests(unittest.TestCase):
    def parse(self, document):
        payload = {'data': json.dumps(document), 'format': 'json-ld', 'records': [],
                   'extensions': [], 'sources': [],
                   'context': {'project_id': 'example', 'snapshot_sha256': 'a' * 64}}
        result = run_worker(standards_environment() / 'bin/python', 'parse', payload, limits())
        self.assertEqual(result['status'], 'staged', result)
        self.assertTrue(result['complete'])
        return result

    def test_ground_quads_keep_exact_terms_order_and_named_graph_identity(self):
        document = ground_document()
        result = self.parse(document)
        expected = sorted([
            ['urn:subject', 'urn:predicate', 'urn:object', 'urn:graph:one'],
            ['urn:subject', 'urn:predicate', 'urn:object', 'urn:graph:two'],
            ['urn:subject', 'urn:number', {'value': '003', 'datatype': INTEGER}, 'urn:graph:one'],
            ['urn:subject', 'urn:label', {'value': 'Bonjour', 'language': 'fr'}, 'urn:graph:one']],
            key=canonical_bytes)
        self.assertEqual(result['quads'], expected)
        self.assertEqual(result['semantic_sha256'], sha256(canonical_bytes(expected)))
        shuffled = list(reversed(document))
        shuffled[1]['@graph'][0] = dict(reversed(list(shuffled[1]['@graph'][0].items())))
        self.assertEqual(self.parse(shuffled)['quads'], expected)
        changed = copy.deepcopy(document); changed[0]['@id'] = 'urn:graph:other'
        self.assertNotEqual(self.parse(changed)['semantic_sha256'], result['semantic_sha256'])
        self.assertEqual(self.parse([])['quads'], [])

    def test_blank_nodes_keep_shared_cross_graph_identity_after_relabeling(self):
        document = blank_document()
        result = self.parse(document)
        renamed = json.loads(json.dumps(document).replace('_:a', '_:renamed-a')
                             .replace('_:b', '_:renamed-b').replace('_:c', '_:renamed-c'))
        renamed.reverse()
        for graph in renamed:
            graph['@graph'].reverse()
        again = self.parse(renamed)
        self.assertEqual(result['quads'], again['quads'])
        self.assertEqual(result['semantic_sha256'], again['semantic_sha256'])
        # A distinct node in the second graph must not be merged with the first.
        changed = copy.deepcopy(document)
        changed[1]['@graph'][0]['@id'] = '_:different'
        self.assertNotEqual(self.parse(changed)['semantic_sha256'], result['semantic_sha256'])


if __name__ == '__main__':
    unittest.main()
