"""Bounded native verification driver. All ledger writes use the installed helper.

Native receipts are provided by the manager after actual tool observations.
This module neither launches agents nor invents their observed status.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PY = '/Volumes/P-SSD/AngryOwl/Sys4AI/.venv/bin/python'
TASK = 'TASK-20260908-300591ED'
FOLDER = 'Tasks/Task-native-project-memory-release-verification-2026-09-08--300591ED'
ACTOR = '/root/memory_native_manager'
EXECUTION = 'native-memory-release-001'
HELPER = ROOT / '.agents/skills/agent-task/scripts/task_state.py'

def state(): return json.loads((ROOT/FOLDER/'task.json').read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def ref(p): return {'path': str(p), 'sha256': sha(p)}
def save(p, data):
    target=ROOT/p; target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
    return ref(p)
def response(summary):
    return {'work_completed':[summary], 'verification_evidence':['Exact typed event and checked inputs retained in the canonical orchestration ledger.'],
            'user_response_summary':summary, 'current_summary':summary,
            'next_step':'Continue the required native memory verification gates.', 'blockers':[], 'open_questions':[], 'relevant_files':[]}
def event(kind,data,*,fail=None,actor=None,generation=1):
    s=state(); seq=s['revision']+1
    ev={'event_id':f'native-{seq}-{kind.replace(".","-")}', 'actor':actor or ACTOR,
        'execution_id':EXECUTION,'generation':generation,'kind':kind,'data':data}
    payload={'event':ev,'response':response(f'Observed {kind} for native memory verification.')}
    cp=subprocess.run([PY,'-B',str(HELPER),'--project-root',str(ROOT),'orchestrate',TASK,'--expected-revision',str(s['revision'])],
                      input=json.dumps(payload),capture_output=True,text=True)
    try: result=json.loads(cp.stdout)
    except ValueError: result={'stdout':cp.stdout,'stderr':cp.stderr}
    attempt=f'coordination/events/{seq}-{kind.replace(".","-")}{"-negative" if fail else ""}.json'
    save(attempt,{'event':ev,'returncode':cp.returncode,'result':result})
    if fail:
        assert cp.returncode!=0 and (fail is True or result['errors'][0]['code']==fail),result
        assert state()['revision']==s['revision']
    else: assert cp.returncode==0,result
    print(json.dumps({'kind':kind,'revision':state()['revision'],'returncode':cp.returncode,'errors':result.get('errors',[])}))
    return result
def current(sid): return state()['orchestration']['subtasks'][sid]
def arref(artifact_id):
    ar=state()['orchestration']['artifacts'][artifact_id]
    return {'path':FOLDER+'/'+ar['path'],'sha256':ar['sha256']}
def register(aid,arid,p):
    event('artifact.register',{'artifact_id':arid,'assignment_id':aid,'source_path':p})
    return arref(arid)
def context(sid,extra=()):
    st=current(sid)
    return st['baseline']['inputs']+[{'path':FOLDER+'/artifacts/orchestration/baseline_'+st['digest']+'.json','sha256':st['digest']}]+list(extra)
def baseline(sid,category,inputs,criteria,objective,implementation=False,dependencies=()):
    slots=[{'slot':'worker','function':'worker','perspective':'source recall and evidence capture','solver_slot':None}]
    if category!='generic':
        slots=[{'slot':'solver1','function':'solver','perspective':'source identity and literal precision','solver_slot':None},
               {'slot':'solver2','function':'solver','perspective':'provenance and independent recall','solver_slot':None},
               {'slot':'senior','function':'senior','perspective':'coherent integration and evidence limits','solver_slot':None}]
        if category=='extra-complex': slots += [{'slot':f'reviewer{i}','function':'reviewer','perspective':f'independent audit of solver {i}','solver_slot':f'solver{i}'} for i in (1,2)]
        if implementation:slots.append({'slot':'implementer','function':'implementer','perspective':'exact accepted artifact implementation','solver_slot':None})
    return {'objective':objective,'requirements':['PLAN-TASK-044' if sid=='generic' else 'PLAN-TASK-045' if sid=='complex' else 'PLAN-TASK-046','PLAN-TASK-047'],
        'inputs':inputs,'dependencies':list(dependencies),'criteria':criteria,'category':category,
        'rationale':{'generic':'One bounded actual recall/proposal needs one accountable worker.', 'complex':'Independent complete interpretations require two solvers and distinct synthesis.', 'extra-complex':'Artifact design requires two independent candidates, mapped review of each, synthesis and separate implementation.'}[category],
        'reads':['SOUL.md','Roles/project-sub-agent','.agents/skills/memory','README.md','research','MEMORY','context'],
        'writes':[f'output/{sid}'] if implementation or category=='generic' else [],
        'protected':['SOUL.md','AGENTS.md','ROLE.md','SPECS.md','Roles','memory.yaml','README.md','research','.agents'],
        'authority':'Disposable verification only; no external, installation, governance, canonical Task, or shared memory writes by children.',
        'implementation_required':implementation,'deliverable':'Versioned result and actual read-only recall evidence.',
        'stop':'Return exact versioned deliverable and stop; report any unmet required gate.','slots':slots}
def assignment(aid,sid,slot,observation,extra=()):
    cp=subprocess.run([PY,'-B',str(ROOT/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'),'--repo-root',str(ROOT),'list','--format','json'],capture_output=True,text=True)
    assert cp.returncode==0,cp.stdout
    catalog=json.loads(cp.stdout); assert catalog['index_status']=='current' and not catalog['invalid_roles']
    catref=save(f'coordination/catalog-{aid}-{state()["revision"]}.json',catalog)
    r=next(x for x in catalog['valid_roles'] if x['name']=='project-sub-agent')
    role={'name':r['name'],'agents_path':r['agents_file'],'role_path':r['role_file'],'agents_sha256':r['agents_sha256'],'role_sha256':r['role_sha256'],'catalog':catref}
    # Reopen both complete role files for every fit, retaining their exact versions.
    for p in (role['agents_path'],role['role_path']): (ROOT/p).read_text()
    st=current(sid); function=next(x['function'] for x in st['baseline']['slots'] if x['slot']==slot)
    writes=[f'output/{sid}'] if function in ('worker','implementer') else [FOLDER+'/artifacts/orchestration/work/'+aid]
    fit={'objective':st['baseline']['objective'], 'capabilities':['bounded analysis','source recall','evidence validation'],
         'reads':st['baseline']['reads']+[x['path'] for x in context(sid,extra)],'writes':writes,
         'deliverable':st['baseline']['deliverable'],'tools':['exec_command','memory helper'],'skills':['memory'],
         'authority':st['baseline']['authority'],'risk':'Cooperative shared filesystem; isolated assigned output and exact frozen inputs.',
         'stop':st['baseline']['stop'],'rationale':f'Fresh general project role explicitly supports the bounded {function} function; manager role grants excessive authority.'}
    runtime={'tools':['spawn_agent','list_agents','send_message','followup_task','interrupt_agent'],'depth':2,'available_slots':max(0,4-sum(1 for x in json.loads((ROOT/observation['path']).read_text())['result']['agents'] if x['agent_status']=='running')),
             'evidence':[observation,ref('Verification/native/bootstrap-runtime-settings.json')]}
    return {'assignment_id':aid,'subtask_id':sid,'slot':slot,'role':role,'fit':fit,'runtime':runtime,
            'settings':state()['orchestration']['settings'],'context':context(sid,extra)}
def receipt(aid,native):
    event('assignment.receipt',{'assignment_id':aid,'receipt':{'tool':'collaboration.spawn_agent','result':{'task_name':native}}})
def reads(aid,reported): event('assignment.reads',{'assignment_id':aid,'role_reads':reported})
def observe(aid,actual,changes=()): event('assignment.observe',{'assignment_id':aid,'receipt':actual,'changes':list(changes)})
def candidate(aid,cid,arid,supersedes=None):
    s=current(state()['orchestration']['assignments'][aid]['subtask_id'])
    event('candidate.record',{'candidate_id':cid,'assignment_id':aid,'artifact_id':arid,'baseline':s['digest'],'round':s['round'],
                             'supersedes':supersedes,'findings':'Current corrected or revalidated candidate.' if supersedes else None,'revalidation':None})

def freeze(sid,version='1',reason=None):
    sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
    from memory_packet import build_packet,freeze_packet
    packet=build_packet(ROOT,task_path=FOLDER+'/task.json',execution_id=EXECUTION,generation=1,actor=ACTOR,
                        allowed_sources=[ref('research/fixture.tex'),ref('README.md')],subtask_id=sid,revision_reason=reason)
    p=f'packets/{sid}-{version}.json'
    freeze_packet(ROOT,packet,p,actor=ACTOR)
    packetref=register('memory-manager',f'packet-{sid}-{version}',p)
    return packet,packetref

def publication(payload,actual_roster,*,fault=None,recovery=None):
    from datetime import datetime,timedelta,timezone
    sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
    from memory_core import load_config,json_bytes,sha256
    from memory_publish import publish
    from memory_recovery import recover
    now=datetime.now(timezone.utc);cfg=load_config(ROOT)
    op=payload['operation_id'];gpath=f'coordination/{op}-{"recover" if recovery else "publish"}-grant.json'
    grant={'schema_version':1,'grant_id':op+'-grant','project_id':cfg['project']['id'],'actor_id':ACTOR,'actor_kind':'manager',
           'operation':'recover' if recovery else payload['operation'],'payload_sha256':sha256(json_bytes(payload)),
           'config_sha256':sha('memory.yaml'),'scope':['MEMORY','.sys4ai/memory/maintenance'],
           'native_receipt':actual_roster,'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=4)).isoformat(),
           'task':{**ref(FOLDER+'/task.json'),'task_id':TASK,'execution_id':EXECUTION,'generation':1,'assignment_id':'memory-manager'},
           'reviewed_records':[{'path':x['path'],'sha256':x['reviewed_record_sha256'],'expected_sha256':x['expected_sha256']} for x in payload['changes']],
           'privacy_redaction':False}
    save(gpath,grant);save(f'coordination/{op}-payload.json',payload)
    if recovery: result=recover(ROOT,recovery,gpath,ACTOR)
    else: result=publish(ROOT,payload,gpath,ACTOR,fault=fault)
    save(f'Verification/manager/{op}-{"recover" if recovery else "publish"}-receipt.json',result)
    return result

def verify(sid,*,result_id=None,acceptance_id=None,artifacts=(),inspection=(),evidence='Direct current artifact and native observation inspection.',fail=None):
    st=current(sid)
    return event('subtask.verify',{'subtask_id':sid,'baseline':st['digest'],'round':st['round'],'result_id':result_id,
        'acceptance_id':acceptance_id,'artifacts':list(artifacts),'criteria':[{'criterion':c,'evidence':evidence} for c in st['baseline']['criteria']],
        'inspection':list(inspection)},fail=fail)
