"""Ordinary installed unittest invocation with exact retained identity accounting."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
prepared=json.loads((OUT/'runtime-preparation.json').read_text())
project=Path(prepared['relocated_project'])
folder=OUT/'installed-suite';folder.mkdir(exist_ok=False)
temporary=folder/'tmp';temporary.mkdir()
inv_source=ROOT/'Verification/ontology-health-repairs/required-test-inventory.json'
inv_raw=inv_source.read_bytes();inventory=json.loads(inv_raw);assert len(inventory['tests'])==183
(folder/'required-test-inventory.json').write_bytes(inv_raw)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
paths=['ontology.yaml','ontology-advanced.yaml','memory.yaml','depot/projects.json','.venv-ontology-standards/certification.json','.sys4ai/ontology/semantic/model.json','.sys4ai/ontology/semantic/index-v1.json']
shared_before={p:sha((ROOT/p).read_bytes()) for p in paths}
local_before={str(p.relative_to(project)):sha(p.read_bytes()) for p in project.rglob('*') if p.is_file()}
helpers={str(p.relative_to(project)):sha(p.read_bytes()) for p in (project/'.agents/skills').rglob('*') if p.is_file()}
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','TMPDIR':str(temporary),
 'SYS4AI_STANDARDS_PYTHON':str(ROOT/'.venv-ontology-standards/bin/python'),'SYS4AI_SEMANTIC_ACCEPTANCE_ROOT':str(ROOT),'SYS4AI_TEST_DEPOT_ROOT':str(ROOT)}
env.pop('SYS4AI_GUARD_INSTALLED_ROOT',None)
for name,suffix in [('SYS4AI_GUARD_EVIDENCE','guard-dispatch'),('SYS4AI_GUARD_BOUNDARY_EVIDENCE','guard-boundary'),('SYS4AI_GUARD_DEADLINE_EVIDENCE','guard-deadline'),('SYS4AI_SEMANTIC_PACKET_EVIDENCE','semantic-packet'),('SYS4AI_ADVANCED_MEMORY_EVIDENCE','advanced-memory')]:
 env[name]=str(folder/(suffix+'.json'))
command=[str(ROOT/'.venv/bin/python'),'-B','-m','unittest','discover','-s','.agents/skills/ontology/tests','-v']
started=datetime.now(timezone.utc).isoformat();clock=time.monotonic()
with (folder/'stdout.log').open('wb') as out,(folder/'stderr.log').open('wb') as err:
 try:
  process=subprocess.run(command,cwd=project,env=env,stdout=out,stderr=err,timeout=3600)
  exit_code=process.returncode;timed_out=False
 except subprocess.TimeoutExpired:
  exit_code=None;timed_out=True
receipt={'command':command,'cwd':str(project),'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),
 'elapsed_seconds':round(time.monotonic()-clock,4),'exit_code':exit_code,'timed_out':timed_out,
 'environment_selection':{k:env[k] for k in ('SYS4AI_STANDARDS_PYTHON','SYS4AI_SEMANTIC_ACCEPTANCE_ROOT','SYS4AI_TEST_DEPOT_ROOT')},
 'shared_semantic_origin':'Explicit existing shared root; semantic test copies the selected runtime/model into its own isolated fixture. This is not fixture-local semantic activation.',
 'inventory_sha256':sha(inv_raw),'stdout_sha256':sha((folder/'stdout.log').read_bytes()),'stderr_sha256':sha((folder/'stderr.log').read_bytes()),
 'delivered_helpers':helpers,'shared_input_hashes_before':shared_before,'shared_input_hashes_after':{p:sha((ROOT/p).read_bytes()) for p in paths},
 'delivered_fixture_unchanged':local_before=={str(p.relative_to(project)):sha(p.read_bytes()) for p in project.rglob('*') if p.is_file()}}
(folder/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
rows=[];pending=None
for line in (folder/'stderr.log').read_text().splitlines():
 m=re.fullmatch(r'(test_\w+) \(([\w.]+)\) \.\.\. (.*)',line)
 if m:
  method,identity,outcome=m.groups();identity=identity if identity.endswith('.'+method) else identity+'.'+method
  pending=identity
  if outcome=='ok' or outcome in {'FAIL','ERROR'} or outcome.startswith('skipped '):
   rows.append({'id':identity,'outcome':'passed' if outcome=='ok' else 'skipped' if outcome.startswith('skipped ') else outcome.lower(),'detail':outcome});pending=None
 elif pending and (line=='ok' or line in {'FAIL','ERROR'} or line.startswith('skipped ')):
  rows.append({'id':pending,'outcome':'passed' if line=='ok' else 'skipped' if line.startswith('skipped ') else line.lower(),'detail':line});pending=None
expected={t['id'] for t in inventory['tests']};found={t['id'] for t in rows}
count=re.search(r'^Ran (\d+) tests? in ',(folder/'stderr.log').read_text(),re.M)
valid=exit_code==0 and not timed_out and expected==found and len(rows)==len(found)==183 and count and int(count[1])==183 and all(r['outcome']=='passed' for r in rows)
report={'status':'passed' if valid else 'failed','required_count':183,'observed_count':len(rows),'original_baseline_obligations':153,
 'missing':sorted(expected-found),'unexpected':sorted(found-expected),'duplicate_ids':len(rows)-len(found),'tests':rows,
 'optional_skips_permitted':False,'selected_profiles':['standards','semantic'],'route':'ordinary installed python -B -m unittest discover with exact verbose identity accounting',
 'receipt_sha256':sha((folder/'receipt.json').read_bytes()),'inventory_sha256':sha(inv_raw),'fixture_unchanged':receipt['delivered_fixture_unchanged'],
 'shared_selected_inputs_unchanged':receipt['shared_input_hashes_before']==receipt['shared_input_hashes_after']}
(folder/'test-identities.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:report[k] for k in ('status','required_count','observed_count','missing','unexpected','fixture_unchanged','shared_selected_inputs_unchanged')}),flush=True)
raise SystemExit(0 if valid and report['fixture_unchanged'] and report['shared_selected_inputs_unchanged'] else 1)
