import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
TASK=ROOT/'Tasks/Task-capture-integrated-curator-ontology-and-initialization-requi-2026-09-13--2F67C831/task.json'
def ref(p):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def state():return json.loads(TASK.read_text())
def response(summary,next_step='Complete current bounded document gate.'):
 return {'work_completed':[summary],'verification_evidence':['Exact current source, native or artifact evidence is bound by this event.'],'user_response_summary':summary,'current_summary':summary,'next_step':next_step,'blockers':[],'open_questions':[],'relevant_files':[{'path':'Verification/curator-ontology-integration-trd-20260913-v1/request.md','note':'Current expanded user intent.'}]}
def event(kind,data,summary,event_id=None):
 s=state();o=s['orchestration']; eid=event_id or kind.replace('.','_')+'_'+str(s['revision']+1)
 payload={'event':{'event_id':eid,'actor':'/root/curator_integration_trd_manager','execution_id':o['execution_id'],'generation':o['generation'],'kind':kind,'data':data},'response':response(summary)}
 cp=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(ROOT),'orchestrate',s['task_id'],'--expected-revision',str(s['revision'])],input=json.dumps(payload),text=True,capture_output=True)
 (OUT/(eid+'.stdout.json')).write_text(cp.stdout);(OUT/(eid+'.stderr')).write_text(cp.stderr)
 try:r=json.loads(cp.stdout)
 except ValueError:r={'raw':'See preserved stdout/stderr.'}
 print(json.dumps({'event':kind,'code':cp.returncode,'revision':state()['revision'],'errors':r.get('errors',[]),'warnings':r.get('warnings',[])}))
 if cp.returncode:raise SystemExit(cp.returncode)
 return r
