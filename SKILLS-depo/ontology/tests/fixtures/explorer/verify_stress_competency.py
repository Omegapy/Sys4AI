"""Isolate the existing competency helper after the combined stress probe timeout."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parents[1]))
from explorer_support import make_explorer_project, canonical_bytes

with tempfile.TemporaryDirectory(prefix='explorer-stress-competency-') as temporary:
    fixture=make_explorer_project(Path(temporary).resolve()/'project',scale='stress')
    command=[sys.executable,'-B',str(ROOT/'SKILLS-depo/ontology/scripts/check_ontology.py'),'--project-root',str(fixture['root'])]
    start=time.perf_counter()
    try:
        cp=subprocess.run(command,capture_output=True,text=True,timeout=45,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        stdout,stderr,code=cp.stdout,cp.stderr,cp.returncode
        observed=json.loads(stdout)
        state='completed'
    except subprocess.TimeoutExpired as exc:
        stdout,stderr=exc.stdout or b'',exc.stderr or b''
        stdout=stdout.decode() if isinstance(stdout,bytes) else stdout
        stderr=stderr.decode() if isinstance(stderr,bytes) else stderr
        code=None;observed=None;state='timeout'
    refs=[]
    for suffix,body in [('stdout.json',stdout),('stderr.txt',stderr)]:
        p=HERE/'validation'/('stress-competency-'+suffix)
        p.write_text(body)
        refs.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    result={'schema_version':1,'kind':'stress_competency_only_probe','state':state,'timeout_seconds':45,'elapsed_seconds':time.perf_counter()-start,
            'exit_code':code,'counts':fixture['counts'],'raw_evidence':refs,
            'qualification':'Canonical competency helper only. This isolates the second stage after an earlier combined probe exhausted its total time budget. No Explorer request or production timing was tested.'}
    if observed:
        result.update(valid=observed['valid'],structural_valid=observed['structural']['valid'],competency=observed['competency'])
    (HERE/'validation/stress-competency-result.json').write_bytes(canonical_bytes(result))
    print(json.dumps({k:v for k,v in result.items() if k not in ('competency','counts')},indent=2))
