"""Host-only exact bootstrap; never writes after the manager activation handoff."""
import json,sys,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];f=ROOT/'Verification/ontology-second-release/fixtures/native-context';h=f/'control_records/native-context/host';h.mkdir(parents=True,exist_ok=True)
write=lambda p,v:p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def ref(p):return {'path':p.relative_to(f).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
mode=sys.argv[1]
created=json.loads((ROOT/'Verification/ontology-second-release/native-task-create.json').read_text());task=Path(created['task_folder'])/'task.json';state=json.loads(task.read_text())
value=json.loads((f/('preparation/manager-'+mode+'.template.json')).read_text());e=value['event'];e.update(actor='/root',event_id='NATIVE_CONTEXT_HOST_'+mode.upper()+'_001')
response=value['response'];response.update(work_completed=['Host '+mode+' for the exact fixture manager.'],verification_evidence=['Current helper, role, native and exact input evidence retained in control_records/native-context/host.'],current_summary='Bounded native context acceptance bootstrap.',user_response_summary='The native goal authorizes this isolated acceptance protocol.',next_step='Observe and record actual native receipt and role reads before transferring writer ownership.',relevant_files=[task.relative_to(f).as_posix()])
if mode=='reserve':
 catalog=h/'roles-catalog.json';r=subprocess.run([sys.executable,str(f/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'),'--repo-root',str(f),'list','--format','json'],capture_output=True,text=True,check=True);catalog.write_text(r.stdout)
 native={'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':'/root','agent_status':'running'}]}}
 observation={'observed_at':datetime.now(timezone.utc).isoformat(),'native_receipt':native,'scope':'Exact current root-running entry normalized from native roster; all three previous workers observed completed.','available_slots':3,'capacity_source':'Native collaboration tool advertises four total slots.','tools':['spawn_agent','list_agents','send_message','followup_task','interrupt_agent'],'inheritance':'Native tool contract: full-history forks inherit parent model and reasoning effort; overrides are omitted.','context_independence':'No native-context solver candidates exist. Manager must dispatch both initial solvers before reading or receiving candidate content; responses contain paths and hashes only until then.','observed_model':None,'observed_effort':None}
 observed=h/'runtime-settings.json';write(observed,observation);e['data']['bootstrap_receipt']=native;e['data']['role']['catalog']=ref(catalog)
 e['data']['runtime'].update(depth=1,available_slots=3,evidence=[ref(observed)]);e['data']['settings']['evidence']=[ref(observed)]
elif mode=='receipt':
 e['generation']=state['orchestration']['generation']; e['data']['assignment_id']=state['orchestration']['manager_id']; e['event_id'] += '_G'+str(e['generation'])
 e['data']['receipt']=json.loads((h/('actual-launch'+('-v2' if e['generation']==2 else '')+'.json')).read_text())
elif mode=='activate':
 e['generation']=state['orchestration']['generation']; e['data']['assignment_id']=state['orchestration']['manager_id']; e['event_id'] += '_G'+str(e['generation'])
 reads=json.loads((h/('actual-role-reads'+('-v2' if e['generation']==2 else '')+'.json')).read_text());e['data']['role_reads']=reads;response['next_step']='Handoff only to the activated manager; host stops fixture Task writes.'
label=mode+'-g'+str(e['generation']);payload=h/(label+'-payload.json');write(payload,value)
command=[sys.executable,str(f/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(f),'orchestrate',state['task_id'],'--expected-revision',str(state['revision']),'--payload-file',str(payload)]
r=subprocess.run(command,capture_output=True,text=True);(h/(label+'-result.json')).write_text(r.stdout);(h/(label+'-stderr.txt')).write_text(r.stderr)
print(r.stdout);sys.exit(r.returncode)
