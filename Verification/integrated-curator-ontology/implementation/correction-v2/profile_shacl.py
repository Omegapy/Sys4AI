"""Confined diagnostic profile, deliberately interrupted before the time limit."""
from pathlib import Path
import sys,json,importlib
OUT=Path(__file__).parent;ROOT=OUT/'root-copy';sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_core import canonical_bytes
from ontology_limits import limits
import ontology_worker
p=ROOT/'.agents/skills/ontology/scripts/ontology_shacl.py';before=p.read_bytes()
worker=ROOT/'.agents/skills/ontology/scripts/ontology_worker.py';worker_before=worker.read_bytes()
try:
 worker.write_text(worker_before.decode().replace('if stopped: return failure(*stopped, worker=observation)',"if stopped: return failure(*stopped, worker=observation, stderr=err.decode(errors='replace')[:16000])").replace("result['worker'] = observation", "result['stderr'] = err.decode(errors='replace')[:16000]\n        result['worker'] = observation"));importlib.reload(ontology_worker)
 instrument='''    import cProfile,pstats,signal,sys,time
    diagnostic_profile=cProfile.Profile();diagnostic_profile.enable()
    def diagnostic_stop(signum,frame):
        diagnostic_profile.disable()
        pstats.Stats(diagnostic_profile,stream=sys.stderr).sort_stats('cumulative').print_stats(15)
        raise RuntimeError('diagnostic_profile_interrupted_after_5_seconds')
    signal.signal(signal.SIGALRM,diagnostic_stop);signal.alarm(5)
'''
 text=before.decode().replace('    import pyshacl\n','    import pyshacl\n'+instrument)
 p.write_text(text)
 payload=json.loads((OUT/'root-copy-payload.json').read_text());payload['graphs']=['asserted','derived','external']
 result=ontology_worker.run_worker(ROOT/'.venv-ontology-standards/bin/python','validate',payload,limits())
 (OUT/'root-copy-shacl-profile.json').write_bytes(canonical_bytes(result));print(result.get('stderr',''),flush=True)
finally:p.write_bytes(before);worker.write_bytes(worker_before)
