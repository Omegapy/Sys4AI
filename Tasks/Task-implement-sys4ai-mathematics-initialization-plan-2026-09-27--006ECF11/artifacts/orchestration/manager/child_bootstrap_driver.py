from manager_driver import *
INFO=AREA/'child-task-created.json'
def childinfo():return json.loads(INFO.read_text())
def childfolder():return CHILD/childinfo()['folder']
def childref(path):
 p=Path(path);return {'path':str(p.relative_to(CHILD)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def childsave(name,value):
 p=childfolder()/'artifacts/orchestration/bootstrap'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');return childref(p)
def childread():return json.loads((childfolder()/'task.json').read_text())
def childevent(kind,data,summary,event_id=None):
 t=childread();event={'event_id':event_id or 'MATHCHILD_'+kind.replace('.','_')+'_'+str(t['revision']+1),'actor':ACTOR,'execution_id':'EXEC_MATH_RESEARCH_R1','generation':1,'kind':kind,'data':data}
 response={'work_completed':[summary],'verification_evidence':['Current child revision '+str(t['revision'])+' and owner/native gates inspected.'],'user_response_summary':summary,'current_summary':summary,'next_step':'Complete actual child manager bootstrap and activate its sole-writer handoff.','blockers':[],'open_questions':[],'relevant_files':[]};payload={'event':event,'response':response};save('child-payload-'+event['event_id']+'.json',payload)
 out=run([CHILD/'.agents/skills/agent-task/scripts/task_state.py','--project-root',CHILD,'orchestrate',t['task_id'],'--expected-revision',t['revision'],'--payload-file','-'],payload);print(kind,childread()['revision'],flush=True);return out
