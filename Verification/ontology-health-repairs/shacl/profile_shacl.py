"""Replay a frozen full payload in the original or repaired diagnostic worker.

Example: .venv/bin/python Verification/ontology-health-repairs/shacl/profile_shacl.py
    --variant final --output final-replay.json

The diagnostic copies add phase reporting only. The selected existing runtime,
worker confinement, graph inputs and finite limits are retained.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

evidence = Path(__file__).resolve().parent
root = evidence.parents[2]
sys.path.insert(0, str(root / 'SKILLS-depo/ontology/scripts'))
from ontology_core import canonical_bytes
from ontology_limits import limits

parser = argparse.ArgumentParser()
parser.add_argument('--variant', choices=('before', 'final'), default='final')
parser.add_argument('--payload', default='full-authoring-payload.json')
parser.add_argument('--seconds', type=int, default=10)
parser.add_argument('--output', required=True)
args = parser.parse_args()
directory = evidence / (args.variant + '-scripts')
spec = importlib.util.spec_from_file_location('diagnostic_worker', directory / 'ontology_worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
payload = json.loads((evidence / args.payload).read_text())
bound = limits({'query_seconds': args.seconds})
result = worker.run_worker(root / '.venv-ontology-standards/bin/python', 'validate', payload, bound)
result['measurement'] = {
    'payload_sha256': hashlib.sha256(canonical_bytes(payload)).hexdigest(),
    'diagnostic_helper_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(directory.glob('*.py'))},
    'bounds': bound,
    'source_shacl_sha256': hashlib.sha256((root / 'SKILLS-depo/ontology/scripts/ontology_shacl.py').read_bytes()).hexdigest(),
}
(evidence / args.output).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result.get(k) for k in ('status', 'complete', 'conforms', 'worker')}, indent=2))
