"""Bounded disposable-Task bootstrap utility. State remains in each owner ledger."""
import json, pathlib, subprocess, tempfile, hashlib
DEPOT=pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
LIMIT=DEPOT/'Verification/shared-agent-billboards'
def selected(root):
 root=pathlib.Path(root).resolve()
 if not root.is_relative_to(LIMIT.resolve()): raise ValueError('Fixture root outside selected verification boundary.')
 return root
def ref(root,path):
 root=selected(root);p=pathlib.Path(path);p=p if p.is_absolute() else root/p
 if not p.resolve().is_relative_to(root): raise ValueError('Evidence outside selected fixture.')
 return {'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def state(root,task_id):
 root=selected(root)
 hits=[]
 for p in (root/'Tasks').glob('Task-*/task.json'):
  d=json.loads(p.read_text())
  if d['task_id']==task_id:hits.append((p,d))
 if len(hits)!=1:raise ValueError('Exact fixture Task missing or ambiguous.')
 return hits[0]
def command(root,kind,payload,task_id=None,expected=None):
 root=selected(root)
 with tempfile.NamedTemporaryFile('w',delete=False,suffix='.json') as f:json.dump(payload,f);tmp=f.name
 args=[str(DEPOT/'.venv/bin/python'),str(root/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(root),kind]
 if task_id:args.append(task_id)
 if expected is not None:args+=['--expected-revision',str(expected)]
 args+=['--payload-file',tmp]
 p=subprocess.run(args,capture_output=True,text=True)
 try:d=json.loads(p.stdout)
 except ValueError:raise RuntimeError('Fixture helper returned unsupported output.')
 print(json.dumps({k:d.get(k) for k in ('status','task_id','revision_after','errors','recovery_required')}))
 if p.returncode:raise RuntimeError(json.dumps(d.get('errors')))
 return d
def event(root,task_id,actor,execution,generation,kind,data,summary):
 _,s=state(root,task_id)
 payload={'event':{'event_id':'EV_'+str(s['revision']+1)+'_'+kind.replace('.','_'),'actor':actor,'execution_id':execution,'generation':generation,'kind':kind,'data':data},'response':{'work_completed':[summary],'verification_evidence':['Exact role/native/baseline bindings checked by the selected fixture helper.'],'user_response_summary':summary,'current_summary':summary,'next_step':'Continue the current controlled native gate.','blockers':[],'open_questions':[],'relevant_files':[]}}
 return command(root,'orchestrate',payload,task_id,s['revision'])
