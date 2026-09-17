import json,sys,subprocess,hashlib
from pathlib import Path
ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
TASK=ROOT/'Tasks/Task-implement-integrated-curator-ontology-and-project-initializa-2026-09-13--E83FCC98'
MANAGER=TASK/'artifacts/orchestration/manager'
def ref(p):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def current(): return json.loads((TASK/'task.json').read_text())
def event(kind,data,summary,event_id=None):
 d=current(); payload={'event':{'event_id':event_id or kind.replace('.','_')+'_'+str(d['revision']+1),'actor':'/root/integration_manager','execution_id':'integrated_curator_E83FCC98','generation':1,'kind':kind,'data':data},'response':{'work_completed':[summary],'verification_evidence':['Current canonical revision, exact input digests and native owner inspected.'],'user_response_summary':summary,'current_summary':summary,'next_step':'Continue the exact authorized integration plan through its next gate.','blockers':[],'open_questions':[],'relevant_files':[]}}
 r=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(ROOT),'orchestrate','TASK-20260913-E83FCC98','--expected-revision',str(d['revision'])],input=json.dumps(payload),capture_output=True,text=True)
 if r.returncode: raise RuntimeError(r.stdout+r.stderr)
 z=json.loads(r.stdout);print(kind,z.get('status'),z.get('revision_after'),flush=True);return z
if __name__=='__main__':
 p=json.loads(Path(sys.argv[1]).read_text());event(p['kind'],p['data'],p['summary'])
