"""Disposable worker-only stack sampling; unchanged validation and time bound."""
from pathlib import Path
import sys,json
OUT=Path(__file__).parent;ROOT=OUT/'root-copy';sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_core import canonical_bytes
from ontology_limits import limits
import ontology_worker,importlib
p=ROOT/'.agents/skills/ontology/scripts/ontology_shacl.py';before=p.read_bytes()
worker=ROOT/'.agents/skills/ontology/scripts/ontology_worker.py';worker_before=worker.read_bytes()
try:
 worker.write_text(worker_before.decode().replace('if stopped: return failure(*stopped, worker=observation)',"if stopped: return failure(*stopped, worker=observation, stderr=err.decode(errors='replace')[:16000])"))
 importlib.reload(ontology_worker)
 text=before.decode().replace('    import pyshacl\n','    import pyshacl\n    import faulthandler\n    faulthandler.dump_traceback_later(3, repeat=True)\n')
 p.write_text(text)
 payload=json.loads((OUT/'root-copy-payload.json').read_text());payload['graphs']=['asserted','derived','external']
 result=ontology_worker.run_worker(ROOT/'.venv-ontology-standards/bin/python','validate',payload,limits())
 (OUT/'root-copy-shacl-stack-sampling.json').write_bytes(canonical_bytes(result));print(result.get('stderr',''),flush=True)
finally:
 p.write_bytes(before);worker.write_bytes(worker_before)
