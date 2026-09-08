"""Build concise navigation from the final canonical fixture state, not a ledger."""
import json
import manager_ops as m

def build():
 s=m.api.state();o=s['orchestration']
 assert s['status']=='completed' and o['stage']=='finished'
 assert all(a['state']=='completed' and a['observations'] for a in o['assignments'].values() if a['function']!='manager')
 native=[]
 for aid,a in o['assignments'].items():
  native.append({'assignment_id':aid,'function':a['function'],'subtask_id':a['subtask_id'],'slot':a['slot'],'native_id':a['native_id'],'role':a['role'],'role_reads':a['role_reads'],'settings':a['settings'],'native_launch_receipt':a['native_receipt'],'last_observation':a['observations'][-1] if a['observations'] else None,'canonical_assignment_state':a['state'],'baseline':a['baseline'],'round':a['round'],'current_context':a['context'],'input_receipt':a['input_receipt']})
 native_ref=m.put('coordination/native-receipt-index.json',{'canonical_task':m.api.ref(m.TASK/'task.json'),'execution_id':o['execution_id'],'generation':o['generation'],'manager_native_status_boundary':'Manager is running while producing this handoff; host must observe its final completion. Every child has its own completed observation after its last work.','count_children':len(native)-1,'assignments':native,'raw_queued_status_evidence':'coordination/repair-raw-native-roster.json','queued_normalization':'coordination/repair-native-normalization.json'})
 mapping=m.put('coordination/version-and-review-index.json',{'canonical_task':m.api.ref(m.TASK/'task.json'),'subtasks':{sid:{k:st[k] for k in ['digest','round','dependency_versions','active_conflicts','verified','versions']} for sid,st in o['subtasks'].items()},'candidates':o['candidates'],'reviews':o['reviews'],'conflicts':o['conflicts'],'syntheses':o['syntheses'],'acceptances':o['acceptances'],'results':o['results']})
 failures=[r for r in [json.loads(x) for x in (m.ROOT/'coordination/helper-receipts.jsonl').read_text().splitlines()] if r['result']['errors']]
 controls=m.put('coordination/rejected-control-index.json',{'rejections':failures,'actual_helper_defect':'coordination/rebind-defect-report.json','repair_boundary':'coordination/repair-continuation-boundary.json','future_exact_payloads':'coordination/event-requests/','interpretation':'Expected missing/stale guards left canonical bytes unchanged; one native-path helper defect was reported, independently repaired by host, and then exercised successfully without native relaunch.'})
 artifacts={key:m.aref(key) for key in o['artifacts']}
 handoff=m.put('coordination/final-handoff.json',{'canonical_task':m.api.ref(m.TASK/'task.json'),'task_id':s['task_id'],'status':s['status'],'revision':s['revision'],'execution_stage':o['stage'],'last_response':s['last_response'],'highest_verification':'end_to_end_behavior_verified_for_this_controlled_disposable_scenario','native_receipts':native_ref,'version_review_mapping':mapping,'negative_controls':controls,'accepted_analysis':m.aref('analysis_proposal_v1'),'accepted_coding_design':m.aref('coding_proposal_v2'),'direct_integration':m.api.ref('coordination/integration-evidence-v2.json'),'all_registered_artifacts':artifacts,'main_criteria':s['definition_of_done'],'native_limits':['Exact effective model/effort equality uses verified full-history inheritance; literal identity telemetry unavailable.','Shared-filesystem context boundaries are cooperative; no OS sandbox is claimed.','The host will observe manager completion after this final turn.','Stop/replacement/settings recovery scenario is separate and not claimed by this category scenario.'],'scope':'Only this disposable fixture. No Git, dependency install, user settings or external action.'})
 print(json.dumps(handoff))
if __name__=='__main__':build()
