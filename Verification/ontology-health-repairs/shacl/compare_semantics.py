"""Replay required semantic controls against frozen original and current workers."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import unittest

evidence = Path(__file__).resolve().parent
root = evidence.parents[2]
sys.path.insert(0, str(root / 'SKILLS-depo/ontology/tests'))
import test_shacl_lists as tests
from ontology_core import canonical_bytes

spec = importlib.util.spec_from_file_location('before_worker', evidence / 'before-scripts/ontology_worker.py')
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)
current = tests.run_worker
results = {}
with (evidence / 'semantic-comparison-tests.log').open('w') as log:
    for name, run in [('before', before.run_worker), ('after', current)]:
        observed = []
        def measured(python, operation, payload, bound, **kwargs):
            result = run(python, operation, payload, bound, **kwargs)
            normalized = {'status': result['status'], 'complete': result['complete'],
                'findings': sorted([{k: v for k, v in f.items() if k not in {'shape', 'message'}}
                                    for f in result.get('findings', [])], key=canonical_bytes)}
            observed.append({'payload_sha256': hashlib.sha256(canonical_bytes(payload)).hexdigest(),
                             'normalized': normalized, 'raw': result})
            return result
        tests.run_worker = measured
        suite = unittest.TestSuite(tests.SharedShapeTests(method) for method in (
            'test_domain_range_cardinality_and_source_constraints',
            'test_changed_inputs_rebuild_complete_constraint_values',
            'test_custom_shapes_meta_validation_and_explicit_graph_scope'))
        outcome = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        results[name] = {'passed': outcome.wasSuccessful(), 'observations': observed}

def comparable(variant):
    return [{k: v for k, v in row.items() if k != 'raw'} for row in results[variant]['observations']]

equivalent = comparable('before') == comparable('after')
report = {'status': 'pass' if equivalent and all(r['passed'] for r in results.values()) else 'fail',
    'validation_cases_per_version': len(results['before']['observations']),
    'comparison': 'Exact input, result status/completeness and every finding focus/path/severity/constraint with multiplicity. Generated blank-node identities and diagnostic prose are retained raw but excluded from semantic equality.',
    'results': results}
(evidence / 'semantic-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
print(report['status'], report['validation_cases_per_version'], 'actual worker controls per version')
raise SystemExit(0 if report['status'] == 'pass' else 1)
