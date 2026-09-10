"""Reuse reviewed static runners with a fresh final-delivery output boundary."""
from pathlib import Path
import hashlib
import importlib.util
import json
import runpy
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ORIGINAL=OUT.parent
ROOT=ORIGINAL.parents[2]
sys.path.insert(0,str(ORIGINAL))
import prepare_static as runner
runner.OUT=OUT
runner.FIXTURES=OUT/'fixtures'
assert runner.REAL==ROOT
for label in ('precheck',):
 command=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'tools/template_update.py'),'check']
 result=subprocess.run(command,cwd=ROOT,capture_output=True,check=False)
 (OUT/('template-'+label+'.json')).write_bytes(result.stdout)
 assert result.returncode==0 and json.loads(result.stdout)['status']=='current'
runner.prepare()
runpy.run_path(str(ORIGINAL/'earlier_edition_controls.py'),run_name='__main__')
result=subprocess.run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'tools/template_update.py'),'check'],cwd=ROOT,capture_output=True,check=False)
(OUT/'template-postcheck.json').write_bytes(result.stdout)
assert result.returncode==0 and json.loads(result.stdout)['status']=='current'
(OUT/'runner-provenance.json').write_text(json.dumps({'runner_sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ORIGINAL/'prepare_static.py',ORIGINAL/'earlier_edition_controls.py')},'output_boundary':str(OUT),'prior_results_preserved':True,'runtime_acceptance':'next stage'},indent=2)+'\n')
print(json.dumps({'status':'final_static_matrix_passed','out':str(OUT)}),flush=True)
