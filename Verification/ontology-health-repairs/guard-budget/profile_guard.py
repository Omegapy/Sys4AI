"""Measure the exact selected guard fixture without changing its deadline."""
from pathlib import Path
import hashlib, importlib, json, os, sys, tempfile, time
from unittest.mock import patch

out=Path(__file__).resolve().parent
root=out.parents[2]
sys.dont_write_bytecode=True
tempfile.tempdir=str(out)
sys.path.insert(0,str(root/'SKILLS-depo/ontology/tests'))
import test_action_semantics as tests
factory=tests.ActionSemanticsTests()
started=time.monotonic()
project,owner,proposal=factory.extension_candidate()
setup_seconds=time.monotonic()-started
modules={name:importlib.import_module('ontology_'+name) for name in ('guards','standards','profiles','worker','core')}
records=[];patches=[];start=None

def observe(module,name,label=None):
    actual=getattr(module,name)
    def measured(*args,**kwargs):
        entered=time.monotonic(); row={'function':label or module.__name__+'.'+name,'start':entered-start}; records.append(row)
        if name=='run_worker':row['operation']=args[1]
        try:
            result=actual(*args,**kwargs)
            if isinstance(result,dict):
                row['status']=result.get('status');row['complete']=result.get('complete')
                if result.get('worker'):row['worker']=result['worker']
            return result
        except Exception as error:
            row['error']=type(error).__name__;row['code']=getattr(error,'code',None)
            raise
        finally:row['elapsed']=time.monotonic()-entered
    patches.append(patch.object(module,name,measured))

for module,names in ((modules['standards'],('_prepare','dataset','validate','infer','load_project')),
                     (modules['profiles'],('health','fingerprint')),
                     (modules['worker'],('run_worker',)),
                     (modules['guards'],('_context','_direct_facts','_semantic_triples'))):
    for name in names:observe(module,name)
inputs={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for top in ('ONTOLOGY','reference-assets/ONTOLOGY-depo') for p in (project/top).rglob('*') if p.is_file()}
source={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (project/'.agents/skills/ontology/scripts').glob('*.py')}
cert=json.loads((project/'.venv-ontology-standards/certification.json').read_text())
try:
    for entry in patches:entry.start()
    start=time.monotonic()
    try:
        decision=modules['guards'].begin_action(project,'ontology','publish',{'proposal':proposal},[row['path'] for row in proposal['changes']])
        result={'status':'conformant','evaluation_seconds':decision.evaluation_seconds,'budget_seconds':decision.evaluation_budget_seconds}
    except Exception as error:
        result={'status':getattr(error,'code',type(error).__name__),'error':str(error),'details':{k:v for k,v in getattr(error,'details',{}).items() if k!='backend'}}
    result['elapsed_seconds']=time.monotonic()-start
finally:
    for entry in reversed(patches):entry.stop()
    factory.doCleanups()
result.update(setup_seconds=setup_seconds,records=records,source_sha256=source,input_sha256=inputs,certificate_fingerprint=cert['fingerprint'])
(out/(sys.argv[1] if len(sys.argv)>1 else 'baseline-profile.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','elapsed_seconds','records')},indent=2))
