from pathlib import Path
import hashlib,json,subprocess,os,uuid
PROJECT=Path(__file__).resolve().parents[1]
PYTHON='/Volumes/P-SSD/AngryOwl/Sys4AI/.venv/bin/python'
HELPER=PROJECT/'.agents/skills/agent-task/scripts/task_state.py'
EXECUTION='recovery_validation_20260908'
def ref(path):
 p=Path(path);p=p if p.is_absolute() else PROJECT/p
 return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def state():
 p=Path(json.loads((PROJECT/'coordination/bootstrap.json').read_text())['task_folder'])/'task.json'
 return json.loads(p.read_text())
def response(summary='Recorded observed validation work.'):
 return {'work_completed':[summary],'verification_evidence':['Exact current inputs and returned native/artifact evidence are retained.'],'user_response_summary':summary,'current_summary':summary,'next_step':'Continue the bounded approved validation.','blockers':[],'open_questions':[],'relevant_files':[]}
def cli(args,payload=None,expect_error=None):
 cp=subprocess.run([PYTHON,str(HELPER),'--project-root',str(PROJECT),*args],input=json.dumps(payload) if payload is not None else None,text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 result=json.loads(cp.stdout)
 log=PROJECT/'coordination/helper-receipts.jsonl'
 with log.open('a') as f:f.write(json.dumps({'arguments':args,'exit_code':cp.returncode,'result':result})+'\n')
 if expect_error:
  assert cp.returncode and result['errors'][0]['code']==expect_error,result
 else:assert cp.returncode==0,(result,cp.stderr)
 return result
def event(kind,data,actor=None,expect_error=None,summary=None):
 s=state();o=s['orchestration'];e={'event_id':'event_'+uuid.uuid4().hex,'actor':actor or o['writer'],'execution_id':o['execution_id'] or EXECUTION,'generation':o['generation'] or 1,'kind':kind,'data':data}
 return cli(['orchestrate',s['task_id'],'--expected-revision',str(s['revision'])],{'event':e,'response':response(summary or 'Observed '+kind+'.')},expect_error)
def role(name):
 script=PROJECT/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'
 cp=subprocess.run([PYTHON,str(script),'--repo-root',str(PROJECT),'list','--format','json'],capture_output=True,text=True);assert cp.returncode==0,cp.stdout
 catalog=json.loads(cp.stdout);assert catalog['index_status']=='current' and not catalog['invalid_roles']
 path=PROJECT/'coordination'/('catalog_'+uuid.uuid4().hex+'.json');path.write_text(json.dumps(catalog,indent=2)+'\n')
 entry=next(x for x in catalog['valid_roles'] if x['name']==name)
 return {'name':name,'agents_path':entry['agents_file'],'role_path':entry['role_file'],'agents_sha256':entry['agents_sha256'],'role_sha256':entry['role_sha256'],'catalog':ref(path)}
