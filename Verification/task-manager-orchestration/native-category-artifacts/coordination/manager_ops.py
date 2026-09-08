from pathlib import Path
import json,hashlib,uuid
import validation_api as api
ROOT=api.PROJECT
MANAGER='/root/task_manager_validation'
TASK=Path(json.loads((ROOT/'coordination/bootstrap.json').read_text())['task_folder'])
TASKREL=TASK.relative_to(ROOT).as_posix()

def put(rel,value):
 p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(value,indent=2)+'\n' if not isinstance(value,str) else value)
 return api.ref(p)

def observe_runtime(agents):
 observed={'tool':'collaboration.list_agents','result':{'agents':agents}}
 ref=put('coordination/roster_'+uuid.uuid4().hex+'.json',observed)
 active=sum(x['agent_status'] in ('running','idle') for x in agents if isinstance(x['agent_status'],str))
 return {'tools':['spawn_agent','send_message','followup_task','list_agents','wait_agent','interrupt_agent'],'depth':2,'available_slots':4-active,'evidence':[api.ref('context/native-runtime.json'),ref]}

def ev(kind,data,expect_error=None):
 before=api.state();raw=(TASK/'task.json').read_bytes()
 event_id='event_'+uuid.uuid4().hex
 o=before['orchestration'];payload={'event':{'event_id':event_id,'actor':MANAGER,'execution_id':o['execution_id'],'generation':o['generation'],'kind':kind,'data':data},'response':api.response('Observed '+kind+'.')}
 put('coordination/event-requests/'+event_id+'.json',{'canonical_before_sha256':hashlib.sha256(raw).hexdigest(),'revision_before':before['revision'],'payload':payload})
 r=api.cli(['orchestrate',before['task_id'],'--expected-revision',str(before['revision'])],payload,expect_error)
 if expect_error:assert raw==(TASK/'task.json').read_bytes(),'Rejected call changed canonical bytes'
 else:api.cli(['validate',before['task_id']])
 print(json.dumps({'event':kind,'status':r['status'],'revision':api.state()['revision'],'errors':r['errors']}))
 return r

def sub(sid):return api.state()['orchestration']['subtasks'][sid]
def bref(sid):return api.ref(TASK/'artifacts/orchestration'/('baseline_'+sub(sid)['digest']+'.json'))
def aref(art):return api.ref(TASK/api.state()['orchestration']['artifacts'][art]['path'])
def work(aid):return TASKREL+'/artifacts/orchestration/work/'+aid

def reserve(aid,sid,slot,objective,writes,runtime,inputs=None):
 role=api.role('project-sub-agent')
 fit={'objective':objective,'capabilities':['bounded project analysis','documentation','focused testing and verification'] if not slot in ('worker','implementer') else ['bounded implementation','focused testing and verification'],
      'reads':['SOUL.md','AGENTS.md','ROLE.md','SPECS.md',role['agents_path'],role['role_path'],'context',TASKREL+'/artifacts/orchestration'],
      'writes':writes,'deliverable':objective,'tools':['native assignment messages','Python standard library','filesystem inspection'],'skills':[],
      'authority':'Only the exact disposable project assignment. No canonical ledger or role-index writes, nested delegation, external actions or other-project changes.',
      'risk':'Controlled local fixture; writes are exclusive and bounded. No product or external state.',
      'stop':'Return exact role-read and artifact receipts when mandatory assigned criteria are met, or report a concrete blocker.',
      'rationale':'The current project-sub-agent pair supports this bounded '+next(x['function'] for x in sub(sid)['baseline']['slots'] if x['slot']==slot)+' function through analysis, documentation and focused verification; no specialist capability or manager authority is needed.'}
 context=[bref(sid)]+(inputs or [])
 ev('assignment.reserve',{'assignment_id':aid,'subtask_id':sid,'slot':slot,'role':role,'fit':fit,'runtime':runtime,'settings':api.state()['orchestration']['settings'],'context':context})
 return put('coordination/packet_'+aid+'.json',{'assignment_id':aid,'project_root':str(ROOT),'task_id':api.state()['task_id'],'execution_id':api.EXECUTION,'generation':1,'role':role,'fit':fit,'context':context,'baseline':bref(sid),'artifact_workspace':work(aid) if slot not in ('worker','implementer') else None})

def launched(aid,nid):ev('assignment.receipt',{'assignment_id':aid,'receipt':{'tool':'collaboration.spawn_agent','result':{'task_name':nid}}})
def reads(aid,path):
 r=json.loads((ROOT/path).read_text());rr=r.get('role_reads',r)
 ev('assignment.reads',{'assignment_id':aid,'role_reads':rr})
def completed(aid,nid,changes):
 ev('assignment.observe',{'assignment_id':aid,'receipt':{'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':nid,'agent_status':'completed'}]}},'changes':[api.ref(x) for x in changes]})
def reg(aid,artifact,path):ev('artifact.register',{'assignment_id':aid,'artifact_id':artifact,'source_path':path})
def candidate(aid,cid,artifact,sid,supersedes=None,findings=None,revalidation=None):ev('candidate.record',{'candidate_id':cid,'assignment_id':aid,'artifact_id':artifact,'baseline':sub(sid)['digest'],'round':sub(sid)['round'],'supersedes':supersedes,'findings':findings,'revalidation':revalidation})

def prepare_rebind(aid,label,runtime,inputs,objective):
 a=api.state()['orchestration']['assignments'][aid]
 role=api.role('project-sub-agent');fit=dict(a['fit']);fit.update(objective=objective,deliverable=objective,rationale='Same existing native '+a['function']+' receives exact revised inputs; the unchanged loaded generic pair supports this bounded function.')
 context=[bref(a['subtask_id'])]+inputs
 rel='coordination/rebind_'+aid+'_'+label+'.json'
 packet={'assignment_id':aid,'native_id':a['native_id'],'role':role,'fit':fit,'runtime':runtime,'context':context,'reason':objective,'project_root':str(ROOT),'artifact_workspace':work(aid)}
 print(json.dumps({'packet':put(rel,packet),'native_id':a['native_id'],'context':context}))
 return rel

def commit_rebind(rel):
 p=json.loads((ROOT/rel).read_text())
 ev('assignment.inputs',{'assignment_id':p['assignment_id'],'role':p['role'],'fit':p['fit'],'runtime':p['runtime'],'context':p['context'],'receipt':{'tool':'collaboration.send_message','native_id':p['native_id'],'artifact_sha256s':[r['sha256'] for r in p['context']],'evidence':'Actual native send_message delivered this exact packet and its listed current artifact digests without waking the completed instance; native tool returned success.'},'reason':p['reason']})
