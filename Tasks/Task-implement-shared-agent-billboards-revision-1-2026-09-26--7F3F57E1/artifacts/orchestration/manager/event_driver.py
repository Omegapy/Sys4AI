import json, pathlib, subprocess, sys, tempfile, hashlib
ROOT=pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
TASK='TASK-20260926-7F3F57E1'
FOLDER=ROOT/'Tasks/Task-implement-shared-agent-billboards-revision-1-2026-09-26--7F3F57E1'
MAN=FOLDER/'artifacts/orchestration/manager'
def state(): return json.loads((FOLDER/'task.json').read_text())
def ref(path):
 p=pathlib.Path(path);p=p if p.is_absolute() else ROOT/p
 return {'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def write(name, data):
 p=MAN/name;p.write_text(json.dumps(data,indent=2)+'\n');return ref(p)
def event(kind,data,summary=None):
 s=state();summary=summary or kind
 payload={'event':{'event_id':'EV_'+str(s['revision']+1)+'_'+kind.replace('.','_'),'actor':'/root/billboards_manager','execution_id':'EXEC_BILLBOARDS_R1','generation':1,'kind':kind,'data':data},'response':{'work_completed':[summary],'verification_evidence':['Exact current bindings checked by Task helper.'],'user_response_summary':summary,'current_summary':summary,'next_step':'Continue authorized plan through its next current gate.','blockers':[],'open_questions':[],'relevant_files':[]}}
 with tempfile.NamedTemporaryFile('w',delete=False,suffix='.json') as f: json.dump(payload,f);tmp=f.name
 p=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(ROOT),'orchestrate',TASK,'--expected-revision',str(s['revision']),'--payload-file',tmp],capture_output=True,text=True)
 if not p.stdout.strip(): raise RuntimeError("helper returned no JSON: "+str(p.returncode)+" "+p.stderr)
 result=json.loads(p.stdout); print(json.dumps({k:result.get(k) for k in ('status','revision_after','errors','recovery_required')}));
 if p.returncode: raise RuntimeError(p.stderr or p.stdout)
 return state()
if __name__=='__main__': event(sys.argv[1],json.loads(sys.argv[2]),sys.argv[3] if len(sys.argv)>3 else None)
