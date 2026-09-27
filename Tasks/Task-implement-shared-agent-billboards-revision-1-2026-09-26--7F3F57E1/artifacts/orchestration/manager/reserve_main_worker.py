import json,sys,copy,subprocess
import event_driver as e

def prepare(sid,aid,contract,evidence,roster,extra_writes=None):
 s=e.state();b=s['orchestration']['subtasks'][sid]
 cat=e.MAN/(aid+'-catalog.json')
 cp=subprocess.run([str(e.ROOT/'.venv/bin/python'),str(e.ROOT/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'),'--repo-root',str(e.ROOT),'list','--format','json'],capture_output=True,text=True)
 if cp.returncode:raise RuntimeError(cp.stdout)
 cat.write_text(cp.stdout)
 role=copy.deepcopy(s['orchestration']['assignments']['package_worker']['role']);role['catalog']=e.ref(cat)
 ctx=[{'path':str((e.FOLDER/'artifacts/orchestration'/('baseline_'+b['digest']+'.json')).relative_to(e.ROOT)),'sha256':b['digest']}]+b['baseline']['inputs']+[e.ref(contract)]+[e.ref(p) for p in evidence]
 rt=e.write(aid+'-runtime.json',{'actual_roster':roster,'observed_running_count':sum(x['agent_status']=='running' for x in roster['result']['agents']),'available_slots_observed':1,'note':'One new native dispatch queued within four-total-slot ceiling; actual returned creation receipt must confirm successful capacity, completion alone is not proof.','guarantee':'Full-history fork without overrides inherits exact parent effective model/effort. This generic bounded implementation/integration worker has no solver independence claim.'})
 fit={'objective':b['baseline']['objective'],'capabilities':['bounded Python implementation','documentation','source/evidence verification'],'reads':b['baseline']['reads']+['SOUL.md','Roles/project-sub-agent',str(e.MAN.relative_to(e.ROOT))]+[x['path'] for x in ctx], 'writes':b['baseline']['writes'],'deliverable':b['baseline']['deliverable'],'tools':['exec_command','apply_patch'],'skills':[],'authority':b['baseline']['authority'],'risk':'Preserve explicit protected scope; completed native evidence is never a license for new source/runtime authority.','stop':b['baseline']['stop'],'rationale':'General project-sub-agent is narrowest valid role for one accountable bounded implementation/evidence worker; task-manager alternative is excluded because this worker receives no ledger/role ownership.'}
 fit['reads']=list(dict.fromkeys(fit['reads']))
 data={'assignment_id':aid,'subtask_id':sid,'slot':b['baseline']['slots'][0]['slot'],'role':role,'fit':fit,'runtime':{'tools':['spawn_agent','list_agents','send_message','followup_task','interrupt_agent'],'depth':2,'available_slots':1,'evidence':[rt]},'settings':s['orchestration']['settings'],'context':ctx}
 e.write(aid+'-reservation.json',data);e.event('assignment.reserve',data,'Current bounded '+aid+' role/context/scope reservation before actual native dispatch.')
 return data
