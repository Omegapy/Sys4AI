"""Evidence driver; all Task state changes use the installed canonical helper."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TASK = 'TASK-20260908-4051880A'
FOLDER = 'Tasks/Task-native-learning-manager-and-frozen-inputs-2026-09-08--4051880A'
TASK_PATH = FOLDER + '/task.json'
ACTOR = '/root/native_learning_manager'
EXECUTION = 'wdyl-native-manager-001'
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'GIT_OPTIONAL_LOCKS': '0'}
sys.path.insert(0, str(ROOT / '.agents/skills/memory/scripts'))

def save(path, value):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError('Evidence already exists: ' + path)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    return ref(path)

def ref(path):
    return {'path': path, 'sha256': hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}

def state():
    return json.loads((ROOT/TASK_PATH).read_text())

def response(summary, evidence=None, next_step='Continue the current required verification gate.'):
    return {'work_completed':[summary], 'verification_evidence':evidence or [summary],
            'user_response_summary':summary, 'current_summary':summary,
            'next_step':next_step, 'blockers':[], 'open_questions':[], 'relevant_files':[]}

def call(command, payload, expected=None):
    s = state()
    args=[sys.executable, '-B', str(ROOT/'.agents/skills/agent-task/scripts/task_state.py'),
          '--project-root', str(ROOT), command, TASK, '--expected-revision',str(s['revision'])]
    cp=subprocess.run(args,input=json.dumps(payload),text=True,capture_output=True,env=ENV)
    try: result=json.loads(cp.stdout)
    except ValueError: result={'unparsed_stdout':cp.stdout,'stderr':cp.stderr}
    receipt={'command':args,'exit_code':cp.returncode,'result':result,'stderr':cp.stderr}
    save('coordination/receipts/' + str(time.time_ns()) + '-' + command + '.json',receipt)
    if expected:
        assert cp.returncode != 0 and result['errors'][0]['code']==expected, receipt
        assert result['mutated'] is False, receipt
    else:
        assert cp.returncode==0, receipt
    return result

def event(kind,data,summary,expected=None):
    payload={'event':{'event_id':'wdyl-'+str(time.time_ns()),'actor':ACTOR,
        'execution_id':EXECUTION,'generation':1,'kind':kind,'data':data},
        'response':response(summary)}
    return call('orchestrate',payload,expected)

def registered(artifact_id):
    a=state()['orchestration']['artifacts'][artifact_id]
    return {'path':FOLDER+'/'+a['path'], 'sha256':a['sha256']}

def baseline_ref():
    s=state()['orchestration']['subtasks']['intent-analysis']
    return {'path':FOLDER+'/artifacts/orchestration/baseline_'+s['digest']+'.json','sha256':s['digest']}

def catalog(label):
    args=[sys.executable,'-B',str(ROOT/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'),'--repo-root',str(ROOT),'list','--format','json']
    cp=subprocess.run(args,capture_output=True,text=True,env=ENV)
    assert cp.returncode==0, cp.stdout+cp.stderr
    value=json.loads(cp.stdout)
    return save('coordination/'+label+'-role-catalog.json',value)

def role(catalog_ref):
    return {'name':'project-sub-agent','agents_path':'Roles/project-sub-agent/AGENTS.md',
        'role_path':'Roles/project-sub-agent/ROLE.md','agents_sha256':ref('Roles/project-sub-agent/AGENTS.md')['sha256'],
        'role_sha256':ref('Roles/project-sub-agent/ROLE.md')['sha256'],'catalog':catalog_ref}

def assignment(aid,slot,catalog_ref,runtime_ref,slots,extras=()):
    st=state()['orchestration']['subtasks']['intent-analysis']
    work=FOLDER+'/artifacts/orchestration/work/'+aid
    context=st['baseline']['inputs']+[baseline_ref()]+list(extras)
    fit={'objective':st['baseline']['objective'],'capabilities':['bounded analysis','evidence verification','frozen source discipline'],
         'reads':st['baseline']['reads'], 'writes':[work], 'deliverable':work+'/candidate.json' if slot!='senior' else work+'/synthesis.json',
         'tools':['exec_command','read-only installed memory helpers'],'skills':['memory','what-did-you-learn'],
         'authority':'Analysis and assigned artifact only; no shared memory, Task state, fixture, configuration or external writes.',
         'risk':'Cooperative frozen context and exact evidence versions must remain valid.',
         'stop':'Return the complete current artifact with path/hash/status only; preserve all other files.',
         'rationale':'The fresh general role explicitly supports this bounded '+slot+' function; task-manager authority is unnecessary.'}
    runtime={'tools':['spawn_agent','list_agents','send_message','followup_task','interrupt_agent'],
             'depth':2,'available_slots':slots,'evidence':[runtime_ref,ref('evidence/manager-bootstrap/settings.json')]}
    settings={'mode':'verified_inheritance','model':None,'effort':None,'evidence':[ref('evidence/manager-bootstrap/settings.json')]}
    return {'assignment_id':aid,'subtask_id':'intent-analysis','slot':slot,'role':role(catalog_ref),
            'fit':fit,'runtime':runtime,'settings':settings,'context':context}
