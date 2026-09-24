import json,subprocess,sys
from pathlib import Path
root=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
task=root/'Tasks/Task-capture-project-knowledge-explorer-requirements-2026-09-19--46D79848/task.json'
def call(kind,data,summary,event_id,status=None):
 t=json.loads(task.read_text())
 response={'work_completed':[summary],'verification_evidence':['Current canonical Task identity, writer, generation and input references were inspected before this helper transaction.'],'user_response_summary':summary,'current_summary':summary,'next_step':'Prepare and verify the complete first-release To-TRD payload; await exact document approval.','blockers':[],'open_questions':[],'relevant_files':[]}
 if kind=='response':
  response.update(actor='/root/knowledge_explorer_manager',execution_id='knowledge_explorer_trd_20260919',generation=1)
  if status: response.update(status_after=status,status_reason='The actual user selected the full proposed first release.')
  payload=response;command='record-response'
 else:
  payload={'event':{'event_id':event_id,'actor':'/root/knowledge_explorer_manager','execution_id':'knowledge_explorer_trd_20260919','generation':1,'kind':kind,'data':data},'response':response};command='orchestrate'
 r=subprocess.run([str(root/'.venv/bin/python'),str(root/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(root),command,t['task_id'],'--expected-revision',str(t['revision']),'--payload-file','-'],input=json.dumps(payload),text=True,capture_output=True)
 d=json.loads(r.stdout);print(json.dumps({k:v for k,v in d.items() if k not in ('ontology_guard','task')},indent=2));print(r.stderr)
 if r.returncode: raise SystemExit(r.returncode)
 return json.loads(task.read_text())
