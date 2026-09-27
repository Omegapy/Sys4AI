import json,hashlib,subprocess,sys,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
PY="/Volumes/P-SSD/AngryOwl/Sys4AI/.venv/bin/python"
FOLDER="Tasks/Task-generic-collaboration-and-recovery-native-pilot-2026-09-26--B9F05B47"
M=FOLDER+"/artifacts/orchestration/manager"
TASK="TASK-20260926-B9F05B47"
ACTOR="/root/billboards_manager/generic_manager"
MID="generic_manager_v2"
def current(): return json.loads((ROOT/(FOLDER+"/task.json")).read_text())
def write(name,data):
    q=ROOT/M/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(data,indent=2)+"\n");return ref(str(q.relative_to(ROOT)))
def ref(path): return {"path":path,"sha256":hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
def art(aid):
    a=current()["orchestration"]["artifacts"][aid];return {"path":FOLDER+"/"+a["path"],"sha256":a["sha256"]}
def event(kind,data,note):
    t=current();v=t["revision"];payload={"event":{"event_id":"GEN_"+str(v+1)+"_"+kind.replace(".","_"),"actor":ACTOR,"execution_id":"EXEC_GENERIC_PILOT","generation":2,"kind":kind,"data":data},"response":{"work_completed":[note],"verification_evidence":["Exact current helper checks and referenced immutable evidence."],"user_response_summary":note,"current_summary":note,"next_step":"Continue controlled native pilot gate.","blockers":[],"open_questions":[],"relevant_files":[]}}
    r=subprocess.run([PY,str(ROOT/".agents/skills/agent-task/scripts/task_state.py"),"--project-root",str(ROOT),"orchestrate",TASK,"--expected-revision",str(v)],input=json.dumps(payload),text=True,capture_output=True);print(r.stdout);
    if r.returncode: raise RuntimeError(r.stderr or r.stdout)
    return current()
def collab(cmd,payload=None,extra=()):
    p=art("generic_policy_v1");args=[PY,str(ROOT/".agents/skills/collaborate/scripts/collaborate.py"),"--project-root",str(ROOT),"--task-path",FOLDER+"/task.json","--assignment",MID,"--actor",ACTOR,"--execution","EXEC_GENERIC_PILOT","--generation","2","--policy-path",p["path"],"--policy-sha256",p["sha256"]]
    if payload is not None:
        path=write("payload_"+payload.get("operation_id",cmd)+".json",payload)["path"];args += ["--payload-file",path]
    r=subprocess.run(args+list(extra)+[cmd],text=True,capture_output=True);print(r.stdout)
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
    return json.loads(r.stdout)
