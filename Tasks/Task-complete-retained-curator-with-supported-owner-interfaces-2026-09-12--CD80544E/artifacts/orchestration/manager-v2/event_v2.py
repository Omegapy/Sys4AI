from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[5]
TD=ROOT/"Tasks/Task-complete-retained-curator-with-supported-owner-interfaces-2026-09-12--CD80544E"
OUT=Path(__file__).parent
ACTOR="/root/supported_curator_manager"
EXECUTION="curator_supported_cd80544e"
GENERATION=2

def ref(path):
 p=Path(path);p=p if p.is_absolute() else ROOT/p
 return {"path":str(p.relative_to(ROOT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
def run(event_id,kind,data,summary,files=()):
 d=json.loads((TD/"task.json").read_text());o=d["orchestration"]
 assert o["writer"]==ACTOR and o["generation"]==GENERATION and o["execution_id"]==EXECUTION
 payload={"event":{"event_id":event_id,"actor":ACTOR,"execution_id":EXECUTION,"generation":GENERATION,"kind":kind,"data":data},"response":{"work_completed":[summary],"verification_evidence":["Inspected current canonical binding and referenced exact evidence before the typed owner operation."],"user_response_summary":summary,"current_summary":summary,"next_step":"Complete the retained caller/setup repairs and required combined verification.","blockers":[],"open_questions":[],"relevant_files":[{"path":str(p),"note":"Exact current supporting evidence."} for p in files]}}
 raw=json.dumps(payload,indent=2)+"\n";(OUT/(event_id+".input.json")).write_text(raw)
 p=subprocess.run([str(ROOT/".venv/bin/python"),str(ROOT/".agents/skills/agent-task/scripts/task_state.py"),"--project-root",str(ROOT),"orchestrate",d["task_id"],"--expected-revision",str(d["revision"])],input=raw,text=True,capture_output=True)
 (OUT/(event_id+".stdout.json")).write_text(p.stdout);(OUT/(event_id+".stderr")).write_text(p.stderr)
 try:r=json.loads(p.stdout)
 except Exception: print(json.dumps({"exit_code":p.returncode,"parse_error":True,"output_prefix":str(OUT/event_id)}));raise SystemExit(1)
 print(json.dumps({"event":event_id,"exit_code":p.returncode,"status":r.get("status"),"revision":r.get("revision_after"),"errors":r.get("errors"),"recovery_required":r.get("recovery_required")}))
 if p.returncode:raise SystemExit(p.returncode)
 return r
