from pathlib import Path
import json,hashlib,subprocess,os,sys
ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
TASK='TASK-20260919-FA1E4FB6'
TD=ROOT/'Tasks/Task-plan-project-knowledge-explorer-full-first-release-2026-09-19--FA1E4FB6'
MD=TD/'artifacts/orchestration/manager'
ACTOR='/root/pke_plan_manager'
EX='EXEC_PKE_PLAN_20260919'
def ref(p):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def state(): return json.loads((TD/'task.json').read_text())
def response(s): return {'work_completed':[s],'verification_evidence':['Current exact Task state and event evidence inspected.'],'user_response_summary':s,'current_summary':s,'next_step':'Produce and validate the full-release managed draft plan.','blockers':[],'open_questions':[],'relevant_files':[]}
def event(eid,kind,data,summary):
 t=state();payload={'event':{'event_id':eid,'actor':ACTOR,'execution_id':EX,'generation':1,'kind':kind,'data':data},'response':response(summary)}
 (MD/(eid+'-input.json')).write_text(json.dumps(payload,indent=2)+'\n')
 p=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(ROOT),'orchestrate',TASK,'--expected-revision',str(t['revision'])],input=json.dumps(payload),capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 (MD/(eid+'-stdout.json')).write_text(p.stdout);(MD/(eid+'-stderr.txt')).write_text(p.stderr)
 v=json.loads(p.stdout);print(json.dumps({k:v.get(k) for k in ['status','revision_after','errors','recovery_required']}))
 if p.returncode: raise SystemExit(p.returncode)
 return v
if __name__=='__main__':
 v=json.load(open(sys.argv[1]));event(v['event_id'],v['kind'],v['data'],v['summary'])
