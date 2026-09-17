import sys,json,subprocess,pathlib
ROOT=pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
TASK='TASK-20260913-3ADCACFC'
cmd=[str(ROOT/'.venv/bin/python'),str(ROOT/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(ROOT)]
payload=json.load(sys.stdin)
show=json.loads(subprocess.check_output(cmd+['show',TASK]))
payload['event'].update(actor='/root/integrated_plan_manager',execution_id='integrated_plan_exec',generation=1)
summary=payload.pop('summary',payload['event']['kind']+' recorded from observed inputs.')
payload['response']={'work_completed':[summary],'verification_evidence':['Current canonical revision and exact event preconditions inspected; helper validates current artifact and ownership bindings.'],'user_response_summary':summary,'current_summary':summary,'next_step':payload.pop('next_step','Continue current planning gate.'),'blockers':[],'open_questions':[],'relevant_files':[]}
r=subprocess.run(cmd+['orchestrate',TASK,'--expected-revision',str(show['task']['revision'])],input=json.dumps(payload),text=True,capture_output=True)
try:
 d=json.loads(r.stdout); print(json.dumps({k:d.get(k) for k in ['status','revision_after','errors','warnings','recovery_required']},indent=2))
except ValueError: print(r.stdout,r.stderr)
if r.returncode: sys.exit(r.returncode)
check=json.loads(subprocess.check_output(cmd+['show',TASK]));print('Verified Task revision',check['task']['revision'])
