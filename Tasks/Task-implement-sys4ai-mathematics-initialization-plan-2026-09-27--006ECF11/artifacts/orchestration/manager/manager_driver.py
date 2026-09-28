from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
FOLDER=ROOT/'Tasks/Task-implement-sys4ai-mathematics-initialization-plan-2026-09-27--006ECF11'
AREA=FOLDER/'artifacts/orchestration/manager'
PY=ROOT/'.venv/bin/python'
TASK='TASK-20260927-006ECF11'
ACTOR='/root/mathematics_init_manager'
PLAN='PLAN-20260928-E1E65C37'
CHILD=ROOT/'Projects/Sys4AI-Mathematics'
PLANFILE=CHILD/'Implementation_Plans/Plan_initialize-sys4ai-mathematics_2026-09-28_E1E65C37/plan.json'
def read_task():return json.loads((FOLDER/'task.json').read_text())
def ref(path):
 p=ROOT/path if not Path(path).is_absolute() else Path(path)
 return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def save(name,value):
 p=AREA/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');return ref(p)
def run(args,input=None):
 r=subprocess.run([str(PY),*map(str,args)],input=None if input is None else json.dumps(input),text=True,capture_output=True,cwd=ROOT)
 try:out=json.loads(r.stdout)
 except ValueError:raise RuntimeError(r.stdout+r.stderr)
 if r.returncode or out.get('status') in ('error','partial'):
  error_path=AREA/('owner-error-'+hashlib.sha256(r.stdout.encode()).hexdigest()+'.json')
  if not error_path.exists():error_path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
  raise RuntimeError(json.dumps({'exit_code':r.returncode,'status':out.get('status'),'evidence':str(error_path.relative_to(ROOT)),'errors':[{'code':e.get('code'),'message':e.get('message')} for e in out.get('errors',[])[:3]]}))
 return out
def event(kind,data,summary,files=None,event_id=None):
 t=read_task();ev={'event_id':event_id or ('MATH_'+kind.replace('.','_')+'_'+str(t['revision']+1)),'actor':ACTOR,'execution_id':'EXEC_MATH_INIT_R1','generation':1,'kind':kind,'data':data}
 response={'work_completed':[summary],'verification_evidence':['Inspected current canonical revision '+str(t['revision'])+' and exact owner/event gates.'],'user_response_summary':summary,'current_summary':summary,'next_step':'Continue the current approved initialization gate.','blockers':[],'open_questions':[],'relevant_files':files or []}
 payload={'event':ev,'response':response};save('payload_'+ev['event_id']+'.json',payload)
 out=run([ROOT/'.agents/skills/agent-task/scripts/task_state.py','--project-root',ROOT,'orchestrate',TASK,'--expected-revision',t['revision'],'--payload-file','-'],payload)
 print(kind,read_task()['revision']);return out
def planrun(command,extra=None,input=None):
 show=run([ROOT/'.agents/skills/to-implementation-plan/scripts/plan_state.py','--project-root',CHILD,'show',PLAN])
 p=json.loads(PLANFILE.read_text());h=hashlib.sha256(PLANFILE.read_bytes()).hexdigest()
 args=[ROOT/'.agents/skills/to-implementation-plan/scripts/plan_state.py','--project-root',CHILD,command,PLAN]
 if extra:args+=extra
 if command not in ('show','validate'):
  args+=['--expect-revision',p['revision'],'--expect-sha256',h]
 if input is not None:args+=['--input','-']
 return run(args,input)
