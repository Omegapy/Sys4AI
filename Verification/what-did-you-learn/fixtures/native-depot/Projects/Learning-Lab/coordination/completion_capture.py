"""Run only after direct integrated verification; publish through the installed memory helper."""
from datetime import datetime, timezone, timedelta
import json
from manager_ops import *
from memory_core import load_config, load_record, render_record, json_bytes, sha256
from memory_evidence import validate_publication_evidence
from memory_publish import transaction_payload
from memory_capture import capture, capture_status
from memory_search import search

s = state()
o = s['orchestration']
assert o['stage'] == 'active' and o['writer'] == ACTOR
assert o['subtasks']['intent-analysis']['verified']
assert all(o['assignments'][a]['state'] == 'completed' for a in ('solver1', 'solver2', 'senior'))
verification = json.loads((ROOT/'Verification/manager/completion-verification.json').read_text())
assert verification['outcome'] == 'passed'
roster = json.loads((ROOT/'coordination/completion-native-observation.json').read_text())
assert any(a['agent_name'] == ACTOR and a['agent_status'] == 'running' for a in roster['result']['agents'])
now = datetime.now(timezone.utc)
status = capture_status(ROOT)
assert status['automatic_capture'] is True
review = {
    'mode': 'automatic task-completed checkpoint after direct verification and before terminal response',
    'entry': '.agents/skills/memory/references/automatic-capture.md',
    'evaluations_for_this_final_work_boundary': 1,
    'owner': ACTOR,
    'capture_status': status,
    'verified_evidence': ref('Verification/manager/completion-verification.json'),
    'comparison': 'The accepted behavioral notes already cover the intent and empty-field design, and the initial protocol note covers frozen launch inputs. The actual partial-work capacity error and narrowly authorized active-lease continuation add a distinct supported operational finding.',
    'disposition': 'contextual_recall_only',
    'required_publication_status': 'The earlier exact manager publication is already committed and retrieved; this final checkpoint does not retry or duplicate that finding.',
    'optional_failure': 'The optional old-grant repeated delivery failed with task_changed and changed no Task, note or journal.',
    'limits': 'General native errored-state recovery remains unsupported by the inspected helper; this one explicitly authorized active-lease continuation supplies no general recovery authority or helper fix.'
}
save('Verification/manager/completion-learning-review.json', review)
record_id = 'MEM-20260909-E5F6A7B8'
operation_id = 'MEMOP-wdyl-manager-partial-work-001'
origin_role = {k:o['assignments']['wdyl-manager']['role'][k] for k in ('name','agents_path','role_path','agents_sha256','role_sha256')}
metadata = {
    'schema_version': 1, 'id': record_id, 'project_id': 'wdyl-lab', 'type': 'lesson',
    'title': 'Inspect partial solver work before continuing a still-active assignment',
    'state': 'active', 'created': now.isoformat(), 'modified': now.isoformat(),
    'claim': {'level': 'verified_outcome', 'summary': 'After a native model-capacity error, direct inspection found preserved round2 checks; a separately authorized continuation under the unchanged active lease produced the complete current candidate without rerunning those checks or changing settings.'},
    'applicability': ['This isolated Learning-Lab Task and comparable cooperative native assignments only after rechecking actual state, artifacts, inputs, scope and current authority.'],
    'limitations': ['One observed active-lease continuation; no general errored-state parser or assignment.resume recovery support was established. The service reported capacity but its infrastructure cause was not independently diagnosed. No production code, helper, configuration, model or effort changed.'],
    'confidence': 'high',
    'sources': [{**ref('Verification/manager/completion-verification.json'), 'locator': 'document', 'kind': 'verification'}],
    'origin': {'task_id': TASK, 'task_path': TASK_PATH, 'execution_id': EXECUTION, 'generation': 1, 'role': origin_role},
    'lifecycle': {'supersedes': [], 'superseded_by': None, 'reason': None},
    'publication': {'actor_id': ACTOR, 'actor_kind': 'manager', 'operation_id': operation_id, 'approved_at': now.isoformat()}
}
body = '''## Observation

The actual native capacity error followed a round2 check receipt. A no-work retry precondition therefore failed. The complete candidate was still missing, and the unchanged Task helper rejected the native errored object.

## Evidence

Verification/manager/completion-verification.json binds the exact partial receipt, actual failed-status evidence, preserved current inputs, explicit active-lease decision, completed candidate and final native team verification.

## Lesson and applicability

Inspect actual assigned artifacts and current ownership after a native error. An error does not prove that no work occurred. Preserve useful partial evidence and distinguish it from a complete candidate. Continue only within current authority and exact inputs; never invent completed or interrupted native status to pass a helper gate.

## Limitations

The inspected helper does not accept its observed errored object or provide ordinary failed-state resume. This Task used one specifically authorized continuation under an assignment that remained active throughout. No assignment.resume event, general recovery support, changed model or universal reliability is claimed.

## Improvement disposition

Contextual recall only. Existing artifact, lease and evidence checks were sufficient for the narrowly granted continuation. General errored-state compatibility remains a separately scoped Task-helper concern; this record does not authorize a helper change or another execution.

## Validation and follow-up

The same native solver completed its current candidate from preserved partial checks, and the distinct senior assessed both complete current candidates. Future work must reopen current helper behavior and obtain any separately needed recovery authority. Publication, helper compatibility and completed product behavior remain distinct claims.
'''
record = {'metadata': metadata, 'body': body}
validate_publication_evidence(ROOT, record)
content = render_record(record)
target = 'MEMORY/' + record_id + '.md'
payload = transaction_payload(operation_id, 'publish', [
    {'path': target, 'expected_sha256': None, 'content': content,
     'reviewed_record_sha256': sha256(content)}
], 'Capture the verified partial-work and explicitly bounded native continuation lesson at the final manager checkpoint.')
save('control_records/memory/manager-completion-payload.json', payload)
grant = {
    'schema_version': 1, 'grant_id': 'wdyl-manager-completion-grant-001', 'project_id': 'wdyl-lab',
    'actor_id': ACTOR, 'actor_kind': 'manager', 'operation': 'publish',
    'payload_sha256': sha256(json_bytes(payload)), 'config_sha256': ref('memory.yaml')['sha256'],
    'scope': ['MEMORY', 'control_records/memory', '.sys4ai/memory/maintenance'],
    'native_receipt': roster, 'observed_at': now.isoformat(), 'expires_at': (now+timedelta(minutes=5)).isoformat(),
    'task': {**ref(TASK_PATH), 'task_id': TASK, 'execution_id': EXECUTION, 'generation': 1, 'assignment_id': 'wdyl-manager'},
    'reviewed_records': [{'path': target, 'sha256': sha256(content), 'expected_sha256': None}],
    'privacy_redaction': False
}
gref = save('control_records/memory/manager-completion-grant.json', grant)
result = capture(ROOT, payload, gref['path'], ACTOR, trigger='task-completed')
assert result['publication']['state'] == 'complete'
saved = save('Verification/manager/completion-publication.json', result)
canonical = load_record(ROOT, target)
assert canonical['sha256'] == sha256(content)
retrieved = search(ROOT, 'Inspect partial solver work', mode='lexical')
assert any(r['path'] == target and not r['diagnostics'] for r in retrieved['results'])
save('Verification/manager/completion-retrieval.json', {'status': 'passed', 'record': ref(target), 'publication': saved, 'lexical': retrieved})
event('artifact.register', {'artifact_id':'completion-publication', 'assignment_id':'wdyl-manager', 'source_path':saved['path']},
      'Record the actual final shared manager learning checkpoint publication and verified canonical retrieval before terminal Task completion.')
print(json.dumps({'status':'captured_and_retrieved','record':ref(target),'task_revision':state()['revision']}, indent=2))
