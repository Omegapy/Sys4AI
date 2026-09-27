"""Typed cooperative orchestration state. No native tools or external services.

Only task_state.py publishes this state, using its existing response transaction.
Receipts are evidence supplied by the coordinator, not OS authentication.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


class OrchestrationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def need(condition, code, message):
    if not condition:
        raise OrchestrationError(code, message)


def keys(value, required, optional=()):
    need(isinstance(value, dict), 'ORCH_OBJECT', 'Expected an object.')
    need(set(required) <= set(value) and set(value) <= set(required) | set(optional),
         'ORCH_FIELDS', 'Missing or unsupported orchestration fields: ' + ', '.join(sorted(set(value) ^ set(required))))


def text(value, nullable=False):
    need((nullable and value is None) or (isinstance(value, str) and value.strip() and len(value) <= 20000 and not any(ord(c) < 32 and c not in '\n\t' for c in value)), 'ORCH_TEXT', 'Expected bounded nonblank text.')


def ident(value):
    need(isinstance(value, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,95}', value), 'ORCH_ID', 'Invalid stable record ID.')


def digest(value):
    need(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'ORCH_DIGEST', 'Expected a SHA256 digest.')


def integer(value, minimum=0):
    need(type(value) is int and value >= minimum, 'ORCH_INTEGER', 'Expected an integer in range.')


def strings(value, nonempty=False):
    need(isinstance(value, list) and len(value) <= 500 and (not nonempty or value), 'ORCH_LIST', 'Expected a bounded text array.')
    for item in value:
        text(item)
    need(len(value) == len(set(value)), 'ORCH_DUPLICATE', 'Duplicate list item.')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def hash_json(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def task_digest(task):
    return hash_json({k: task[k] for k in ('description', 'definition_of_done')})


def confined(root, raw, *, must_exist=False):
    text(raw)
    p = Path(raw)
    need(not p.is_absolute() and '..' not in p.parts and p.parts and not any(ord(c) < 32 for c in raw), 'ORCH_PATH', 'Expected a confined relative path.')
    target = root / p
    cursor = root
    for part in p.parts:
        cursor /= part
        need(not cursor.is_symlink(), 'ORCH_SYMLINK', 'Symlink components are prohibited.')
    need(target.resolve().is_relative_to(root.resolve()), 'ORCH_PATH', 'Path escapes the owning root.')
    if must_exist:
        need(target.is_file() and target.stat().st_size <= 250000, 'ORCH_FILE', 'Evidence must be a bounded regular file.')
    return target


def evidence(value, root=None):
    keys(value, ('path', 'sha256'))
    text(value['path']); digest(value['sha256'])
    if root is not None:
        p = confined(root, value['path'], must_exist=True)
        need(sha(p.read_bytes()) == value['sha256'], 'ORCH_EVIDENCE_CHANGED', 'Inspected evidence bytes changed: ' + value['path'])


def evidence_list(values, root=None, nonempty=False):
    need(isinstance(values, list) and len(values) <= 200 and (not nonempty or values), 'ORCH_EVIDENCE', 'Expected bounded evidence references.')
    for value in values:
        evidence(value, root)


def native_id(value):
    text(value)
    need(re.fullmatch(r'/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+', value) and len(value) < 300, 'ORCH_NATIVE_ID', 'Expected an actual canonical native agent ID, not a role or logical ID.')


def receipt(value, *, launch=False, subject=None):
    keys(value, ('tool', 'result'))
    if launch:
        need(value['tool'] == 'collaboration.spawn_agent', 'ORCH_NATIVE_RECEIPT', 'Launch identity requires a native spawn receipt.')
        keys(value['result'], ('task_name',))
        native_id(value['result']['task_name'])
        return value['result']['task_name']
    need(value['tool'] == 'collaboration.list_agents', 'ORCH_NATIVE_RECEIPT', 'Status requires a native list_agents receipt.')
    keys(value['result'], ('agents',))
    need(isinstance(value['result']['agents'], list), 'ORCH_NATIVE_RECEIPT', 'Invalid native roster.')
    seen = set(); found = None
    for item in value['result']['agents']:
        keys(item, ('agent_name', 'agent_status')); native_id(item['agent_name'])
        need(item['agent_name'] not in seen, 'ORCH_NATIVE_RECEIPT', 'Duplicate native roster ID.'); seen.add(item['agent_name'])
        status = item['agent_status']
        if isinstance(status, dict):
            keys(status, ('completed',)); text(status['completed']); status = 'completed'
        need(status in ('running', 'completed', 'interrupted', 'failed', 'idle'), 'ORCH_NATIVE_STATUS', 'Unsupported native state.')
        if item['agent_name'] == subject:
            found = status
    return found


def settings(value, root=None):
    keys(value, ('mode', 'model', 'effort', 'evidence'))
    need(value['mode'] in ('observed_equal', 'verified_inheritance'), 'ORCH_SETTINGS', 'Unverified settings prevent dispatch.')
    text(value['model'], nullable=True); text(value['effort'], nullable=True)
    if value['mode'] == 'observed_equal':
        need(value['model'] and value['effort'], 'ORCH_SETTINGS', 'Observed identity needs exact model and effort.')
    evidence_list(value['evidence'], root, nonempty=True)


def runtime(value, root=None):
    keys(value, ('tools', 'depth', 'available_slots', 'evidence'))
    strings(value['tools'], True); integer(value['depth'], 1); integer(value['available_slots'])
    need({'spawn_agent', 'list_agents', 'send_message', 'followup_task', 'interrupt_agent'} <= set(value['tools']), 'ORCH_CAPABILITY', 'Native controls are unavailable.')
    evidence_list(value['evidence'], root, nonempty=True)


def role(value, root=None):
    keys(value, ('name', 'agents_path', 'role_path', 'agents_sha256', 'role_sha256', 'catalog'))
    ident(value['name']); digest(value['agents_sha256']); digest(value['role_sha256']); evidence(value['catalog'], root)
    # Stored provenance keeps its original spelling. Only a fresh Roles pair
    # can authorize a new live reservation; validation never migrates history.
    layouts = ('Roles', 'roles') if root is None else ('Roles',)
    need(any(value['agents_path'] == f"{layout}/{value['name']}/AGENTS.md" and value['role_path'] == f"{layout}/{value['name']}/ROLE.md" for layout in layouts), 'ORCH_ROLE_PAIR', 'Role must be the exact current Roles pair; lowercase paths are historical provenance only.')
    if root is None:
        return
    need(sorted(p.name for p in root.iterdir() if p.name.casefold() == 'roles') == ['Roles'], 'ORCH_ROLE_ROOT', 'The active directory must be spelled exactly Roles without a competing case variant.')
    for key, digest_key in (('agents_path', 'agents_sha256'), ('role_path', 'role_sha256')):
        p = confined(root, value[key], must_exist=True)
        need(sha(p.read_bytes()) == value[digest_key], 'ORCH_ROLE_CHANGED', 'Role changed after selection.')
    helper = confined(root, '.agents/skills/manage-subagent-roles/scripts/role_catalog.py', must_exist=True)
    spec = importlib.util.spec_from_file_location('_sys4ai_live_role_catalog', helper)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
    try:
        catalog = module.build_catalog(root)
        entry = module.find_valid_role(catalog, value['name'])
    except module.CatalogError as exc:
        raise OrchestrationError('ORCH_ROLE_INVALID', str(exc)) from exc
    need(entry.valid, 'ORCH_ROLE_INVALID', 'Selected bundle is invalid.')
    saved = json.loads(confined(root, value['catalog']['path'], must_exist=True).read_text())
    # The catalog fingerprint is generated by the role helper, not a role name assertion.
    current = catalog.as_dict() if hasattr(catalog, 'as_dict') else catalog.to_dict()
    need(current.get('role_root') == 'Roles' and entry.agents_file == value['agents_path'] and entry.role_file == value['role_path'], 'ORCH_ROLE_PAIR', 'The live catalog must identify the exact Roles pair.')
    need(current.get('index_status') == 'current', 'ORCH_ROLE_INDEX', 'Publish a current role index before assignment.')
    need(saved == current, 'ORCH_CATALOG_STALE', 'Role selection requires a fresh matching filesystem catalog.')


def fit(value, root=None):
    keys(value, ('objective', 'capabilities', 'reads', 'writes', 'deliverable', 'tools', 'skills', 'authority', 'risk', 'stop', 'rationale'))
    for key in ('objective', 'deliverable', 'authority', 'risk', 'stop', 'rationale'):
        text(value[key])
    for key in ('capabilities', 'reads', 'writes', 'tools', 'skills'):
        strings(value[key], key == 'capabilities')
    if root:
        for p in value['reads'] + value['writes']:
            confined(root, p)


FIELDS = ('version execution_id generation stage bootstrap manager_id writer settings context source_refs authority task_digest subtasks assignments artifacts candidates reviews conflicts syntheses acceptances results verifications blockers events history').split()
COLLECTIONS = ('subtasks assignments artifacts candidates reviews conflicts syntheses acceptances results').split()
ASSIGN_FIELDS = ('assignment_id subtask_id slot function perspective role fit runtime settings context state native_id native_receipt role_reads observations generation acceptance_id baseline round input_receipt').split()
BASE_FIELDS = ('objective requirements inputs dependencies criteria category rationale reads writes protected authority implementation_required deliverable stop slots').split()
CAND_FIELDS = ('candidate_id assignment_id artifact_id baseline round supersedes findings revalidation').split()
REVIEW_FIELDS = ('review_id assignment_id candidate_id baseline round outcome findings').split()
SYNTH_FIELDS = ('synthesis_id assignment_id candidate_ids review_ids baseline round artifact_id dispositions resolved_conflicts').split()
ACCEPT_FIELDS = ('acceptance_id synthesis_id inspection').split()
RESULT_FIELDS = ('result_id assignment_id acceptance_id baseline round artifact_ids changes checks limitations').split()


def empty():
    o = {k: {} for k in COLLECTIONS}
    o.update(version=1, execution_id=None, generation=0, stage='unassigned', bootstrap=None, manager_id=None, writer=None, settings=None, context=[], source_refs=[], authority=None, task_digest=None, verifications=[], blockers=[], events=[], history=[])
    return o


def validate(o):
    keys(o, FIELDS); need(type(o['version']) is int and o['version'] == 1, 'ORCH_VERSION', 'Unsupported orchestration version.')
    integer(o['generation'])
    need(o['stage'] in ('unassigned', 'reserved', 'receipt_recorded', 'active', 'stopping', 'stopped', 'blocked', 'finished'), 'ORCH_STAGE', 'Invalid execution stage.')
    if o['execution_id'] is not None:
        ident(o['execution_id']); digest(o['task_digest']); native_id(o['bootstrap']); native_id(o['writer']); settings(o['settings'])
    else:
        need(o == empty(), 'ORCH_UNASSIGNED', 'Unassigned orchestration cannot invent execution state.')
    for k in COLLECTIONS:
        need(isinstance(o[k], dict), 'ORCH_COLLECTION', 'Expected record map.')
        for record_id in o[k]: ident(record_id)
    evidence_list(o['context']); evidence_list(o['source_refs']); strings(o['blockers'])
    for a in o['assignments'].values():
        keys(a, ASSIGN_FIELDS); ident(a['assignment_id']); role(a['role']); fit(a['fit']); runtime(a['runtime']); settings(a['settings']); evidence_list(a['context'])
        need(a['state'] in ('reserved', 'launch_uncertain', 'active', 'stop_requested', 'stopped', 'completed', 'failed', 'revoked'), 'ORCH_ASSIGNMENT_STATE', 'Invalid assignment state.')
        integer(a['generation'], 1); digest(a['baseline']); integer(a['round'])
        if a['native_id'] is not None: native_id(a['native_id']); need(receipt(a['native_receipt'], launch=True) == a['native_id'], 'ORCH_NATIVE_RECEIPT', 'Native ID disagrees with stored launch receipt.')
        need(isinstance(a['observations'], list), 'ORCH_OBSERVATION', 'Invalid observations.')
        for obs in a['observations']:
            keys(obs, ('receipt', 'changes')); receipt(obs['receipt'], subject=a['native_id']); evidence_list(obs['changes'])
    for s in o['subtasks'].values():
        keys(s, ('baseline', 'digest', 'task_digest', 'round', 'versions', 'verified', 'dependency_versions', 'active_conflicts'))
        baseline(s['baseline']); digest(s['digest']); digest(s['task_digest']); integer(s['round'], 1)
        need(hash_json(s['baseline']) == s['digest'], 'ORCH_BASELINE_HASH', 'Baseline digest does not match stored fields.')
        strings(s['active_conflicts'])
        need(all(cid in o['conflicts'] for cid in s['active_conflicts']), 'ORCH_REFERENCE', 'Active conflict reference is missing.')
        need(isinstance(s['dependency_versions'], dict), 'ORCH_DEPENDENCY', 'Invalid dependency version bindings.')
        for dep, value in s['dependency_versions'].items(): ident(dep); digest(value)
        need(isinstance(s['versions'], list) and isinstance(s['verified'], list), 'ORCH_HISTORY', 'Invalid subtask history.')
        for old in s['versions']:
            keys(old, ('baseline', 'digest', 'task_digest', 'round', 'dependency_versions', 'active_conflicts')); baseline(old['baseline']); digest(old['digest']); digest(old['task_digest']); integer(old['round'], 1)
    for v in o['artifacts'].values():
        keys(v, ('path', 'sha256', 'size', 'assignment_id', 'generation')); digest(v['sha256']); text(v['path']); integer(v['size']); integer(v['generation'], 1)
    for collection, fields in [('candidates', CAND_FIELDS), ('reviews', REVIEW_FIELDS), ('syntheses', SYNTH_FIELDS), ('acceptances', ACCEPT_FIELDS), ('results', RESULT_FIELDS)]:
        for v in o[collection].values():
            keys(v, fields)
            event_kind = {'candidates':'candidate.record', 'reviews':'review.record', 'syntheses':'synthesis.record', 'acceptances':'acceptance.record', 'results':'result.record'}[collection]
            validate_event_data(event_kind, v)
    for v in o['conflicts'].values():
        keys(v, ('conflict_id', 'assignment_id', 'candidate_ids', 'baseline', 'round', 'explanation', 'deliveries', 'progress'))
    need(isinstance(o['events'], list) and isinstance(o['history'], list) and isinstance(o['verifications'], list), 'ORCH_HISTORY', 'Invalid event/history array.')
    seen = set()
    for event in o['events']:
        keys(event, ('event_id', 'actor', 'execution_id', 'generation', 'kind', 'data', 'sha256', 'revision'))
        ident(event['event_id']); native_id(event['actor']); ident(event['execution_id']); integer(event['generation'], 1); integer(event['revision'], 1); digest(event['sha256'])
        need(event['event_id'] not in seen, 'ORCH_DUPLICATE_EVENT', 'Duplicate stored event ID.'); seen.add(event['event_id'])
        validate_event_data(event['kind'], event['data'])
        original = {k: event[k] for k in ('event_id', 'actor', 'execution_id', 'generation', 'kind', 'data')}
        need(hash_json(original) == event['sha256'], 'ORCH_EVENT_HASH', 'Stored event payload digest differs.')
    for old in o['history']:
        keys(old, set(FIELDS) - {'history', 'events'}); validate({**old, 'events': [], 'history': []})
    if o['manager_id']:
        need(o['manager_id'] in o['assignments'], 'ORCH_REFERENCE', 'Missing manager assignment.')
    for key, a in o['assignments'].items():
        need(key == a['assignment_id'], 'ORCH_REFERENCE', 'Assignment map identity differs.')
        need(a['subtask_id'] is None or a['subtask_id'] in o['subtasks'], 'ORCH_REFERENCE', 'Missing assignment subtask.')
    for collection in ('candidates', 'reviews', 'syntheses', 'results', 'conflicts'):
        for v in o[collection].values():
            need(v['assignment_id'] in o['assignments'], 'ORCH_REFERENCE', 'Missing producer assignment.')
    for v in o['reviews'].values(): need(v['candidate_id'] in o['candidates'], 'ORCH_REFERENCE', 'Missing reviewed candidate.')
    for v in o['acceptances'].values(): need(v['synthesis_id'] in o['syntheses'], 'ORCH_REFERENCE', 'Missing accepted synthesis.')
    for v in o['results'].values(): need(v['acceptance_id'] is None or v['acceptance_id'] in o['acceptances'], 'ORCH_REFERENCE', 'Missing implementation acceptance.')
    for collection, field in (('candidates','candidate_id'), ('reviews','review_id'), ('conflicts','conflict_id'), ('syntheses','synthesis_id'), ('acceptances','acceptance_id'), ('results','result_id')):
        for record_id, value in o[collection].items():
            need(value[field] == record_id, 'ORCH_REFERENCE', 'Record ID differs from its canonical map key.')
    for artifact in o['artifacts'].values():
        need(artifact['assignment_id'] in o['assignments'], 'ORCH_REFERENCE', 'Artifact producer assignment is missing.')
        need(artifact['path'].startswith('artifacts/orchestration/') and not Path(artifact['path']).is_absolute() and '..' not in Path(artifact['path']).parts, 'ORCH_PATH', 'Unsafe registered artifact path.')
    for collection in ('candidates', 'syntheses', 'results', 'reviews', 'conflicts'):
        for record in o[collection].values():
            artifact_ids = record.get('artifact_ids', []) + ([record['artifact_id']] if 'artifact_id' in record else []) + ([record['findings']] if collection == 'reviews' else []) + ([record['explanation']] if collection == 'conflicts' else [])
            for artifact_id in artifact_ids:
                need(artifact_id in o['artifacts'] and o['artifacts'][artifact_id]['assignment_id'] == record['assignment_id'], 'ORCH_REFERENCE', 'Result artifact is missing or attributed to another producer.')
            if 'candidate_ids' in record:
                need(all(cid in o['candidates'] for cid in record['candidate_ids']), 'ORCH_REFERENCE', 'Synthesis/conflict references a missing candidate.')
            if 'review_ids' in record:
                need(all(rid in o['reviews'] for rid in record['review_ids']), 'ORCH_REFERENCE', 'Synthesis references a missing review.')
    for cid, candidate in o['candidates'].items():
        seen = {cid}; previous = candidate['supersedes']; origin = o['assignments'][candidate['assignment_id']]
        while previous is not None:
            need(previous in o['candidates'] and previous not in seen, 'ORCH_REFERENCE', 'Candidate revision chain is missing or cyclic.')
            seen.add(previous); prior = o['candidates'][previous]; producer_assignment = o['assignments'][prior['assignment_id']]
            need((origin['subtask_id'], origin['slot']) == (producer_assignment['subtask_id'], producer_assignment['slot']), 'ORCH_REFERENCE', 'Candidate revision changed its originating solver slot.')
            previous = prior['supersedes']
    for a in o['assignments'].values():
        if a['acceptance_id'] is not None: need(a['acceptance_id'] in o['acceptances'], 'ORCH_REFERENCE', 'Implementation assignment has a missing acceptance target.')
    for st in o['subtasks'].values():
        for v in st['verified']:
            validate_event_data('subtask.verify', v)
            need(all(aid in o['artifacts'] for aid in v['artifacts']), 'ORCH_REFERENCE', 'Verification references a missing artifact.')
            need(v['result_id'] is None or v['result_id'] in o['results'], 'ORCH_REFERENCE', 'Verification result is missing.')
            need(v['acceptance_id'] is None or v['acceptance_id'] in o['acceptances'], 'ORCH_REFERENCE', 'Verification acceptance is missing.')
    for sid in o['subtasks']: dependency_cycle(o, sid, set())


def baseline(v, root=None):
    keys(v, BASE_FIELDS)
    for k in ('objective', 'rationale', 'deliverable', 'stop', 'authority'): text(v[k])
    for k in ('requirements', 'dependencies', 'criteria', 'reads', 'writes', 'protected'): strings(v[k], k in ('requirements', 'criteria'))
    evidence_list(v['inputs'], root)
    need(v['category'] in ('generic', 'complex', 'extra-complex'), 'ORCH_CATEGORY', 'Invalid required category.')
    need(type(v['implementation_required']) is bool, 'ORCH_BOOLEAN', 'implementation_required must be boolean.')
    need(isinstance(v['slots'], list) and v['slots'], 'ORCH_TEAM', 'A frozen logical team is required.')
    ids = set(); solvers = []; reviewers = []; others = []
    for slot in v['slots']:
        keys(slot, ('slot', 'function', 'perspective', 'solver_slot')); ident(slot['slot']); text(slot['perspective'])
        need(slot['slot'] not in ids, 'ORCH_TEAM', 'Duplicate logical slot.'); ids.add(slot['slot'])
        need(slot['function'] in ('worker', 'solver', 'reviewer', 'senior', 'implementer'), 'ORCH_FUNCTION', 'Invalid worker function.')
        (solvers if slot['function'] == 'solver' else reviewers if slot['function'] == 'reviewer' else others).append(slot)
        need((slot['function'] == 'reviewer') == (slot['solver_slot'] is not None), 'ORCH_REVIEW_MAPPING', 'Only reviewers map to a solver slot.')
    functions = [s['function'] for s in v['slots']]
    if v['category'] == 'generic':
        need(functions == ['worker'], 'ORCH_TEAM', 'Generic work has exactly one worker and no other function.')
    else:
        need(len(solvers) >= 2 and len({s['perspective'].casefold() for s in solvers}) == len(solvers), 'ORCH_TEAM', 'Multi-solution work needs distinct solver perspectives.')
        need(functions.count('senior') == 1 and functions.count('worker') == 0 and functions.count('implementer') == int(v['implementation_required']), 'ORCH_TEAM', 'Multi-solution work requires one senior and the authorized implementation owner only when needed.')
        if v['category'] == 'extra-complex':
            need(len(reviewers) == len(solvers) and {s['solver_slot'] for s in reviewers} == {s['slot'] for s in solvers}, 'ORCH_REVIEW_MAPPING', 'Reviewer mapping must be one-to-one.')
        else:
            need(not reviewers, 'ORCH_TEAM', 'Complex work has no per-candidate reviewer stage.')
    if root:
        for raw in v['reads'] + v['writes'] + v['protected']: confined(root, raw)
        for raw in v['writes']:
            parts = Path(raw).parts
            role_control = parts[0].casefold() == 'roles' and (len(parts) == 1 or (len(parts) == 2 and parts[1].casefold() == 'index.md'))
            need(not raw.startswith('Tasks/') and raw not in ('Tasks', '.git') and not raw.startswith('.git/') and not role_control, 'ORCH_WRITE_SCOPE', 'Worker scope cannot include canonical Task state, the Roles root/index, or Git internals (including case aliases).')


def dependency_cycle(o, sid, seen):
    need(sid not in seen, 'ORCH_DEPENDENCY_CYCLE', 'Cyclic subtask dependencies.')
    seen = seen | {sid}
    for dep in o['subtasks'][sid]['baseline']['dependencies']:
        need(dep in o['subtasks'], 'ORCH_DEPENDENCY', 'Missing dependency target.')
        dependency_cycle(o, dep, seen)


def unresolved(o, *, manager=True):
    return [a for a in o['assignments'].values() if (manager or a['function'] != 'manager') and a['state'] in ('reserved', 'launch_uncertain', 'active', 'stop_requested')]


def auth(task, payload, *, recovery=False, allow_unassigned=False):
    if task.get('schema_version') != 2: return
    o = task['orchestration']; validate(o)
    for k in ('actor', 'execution_id', 'generation'): need(k in payload, 'ORCH_ACTOR_REQUIRED', 'Schema-2 writes require actor, execution_id and generation.')
    need(payload['execution_id'] == o['execution_id'] and payload['generation'] == o['generation'], 'ORCH_STALE_GENERATION', 'Execution/generation is stale.')
    if o['execution_id'] is None and allow_unassigned:
        integer(payload['generation']); native_id(payload['actor'])
        need(receipt(payload.get('bootstrap_receipt'), subject=payload['actor']) == 'running', 'ORCH_BOOTSTRAP_RECEIPT', 'Unassigned maintenance needs a current running bootstrap receipt.')
        return
    integer(payload['generation'])
    native_id(payload['actor'])
    allowed = {o['writer']}
    if recovery and payload.get('recovery_authorized') is True and not unresolved(o): allowed.add(o['bootstrap'])
    need(payload['actor'] in allowed and payload['actor'] is not None, 'ORCH_WRITER', 'Only the designated current writer can mutate canonical state.')


def lifecycle(task, payload, command, target, root=None, folder=None):
    if task.get('schema_version') != 2: return
    if command == 'reopen':
        o = copy.deepcopy(task['orchestration'])
        need(payload.get('actor') == o['bootstrap'] and payload.get('execution_id') == o['execution_id'] and payload.get('generation') == o['generation'] and payload.get('user_authorized') is True, 'ORCH_RECOVERY_OWNER', 'Explicit reopening requires the original bootstrap and current execution binding.')
        reconcile_observations(o, payload.get('reconciliation'), root)
        need(not unresolved(o), 'ORCH_STOP_REQUIRED', 'Reconcile every prior native owner before reopening.')
        for a in o['assignments'].values(): a['state'] = 'revoked'
        o.update(writer=o['bootstrap'], stage='finished')
        return o
    auth(task, payload)
    o = task['orchestration']
    if target == 'completed':
        need(o['stage'] == 'finished' and o['verifications'] and o['verifications'][-1]['outcome'] == 'delivered', 'ORCH_COMPLETION', 'Current delivered execution and main-Task verification are required.')
        if root is not None:
            evidence_list(o['verifications'][-1]['inspection'], root, True)
            for sid in o['subtasks']:
                verified_current(o, sid, task, root, folder)
    if target in ('paused', 'cancelled', 'close-old-task'):
        need(o['stage'] in ('stopped', 'finished') and not unresolved(o, manager=False), 'ORCH_STOP_REQUIRED', 'Reconcile every worker before a stopped lifecycle claim.')
    if command == 'reopen':
        need(not unresolved(o), 'ORCH_STOP_REQUIRED', 'Reopen requires reconciled prior execution ownership.')
    if payload.get('updates') and {'description', 'definition_of_done'} & payload['updates'].keys():
        need(not unresolved(o, manager=False), 'ORCH_BASELINE_OWNERS', 'Reconcile affected write owners before changing Task criteria.')


def age_guard(task):
    if task.get('schema_version') == 2:
        o = task['orchestration']
        need(not unresolved(o) and o['stage'] in ('unassigned', 'stopped', 'finished'), 'ORCH_AGE_OWNERS', 'Native ownership must be reconciled before age-based matching or closure: ' + task['task_id'])


def evidence_current(o, artifact_id, folder):
    need(artifact_id in o['artifacts'], 'ORCH_ARTIFACT', 'Missing registered artifact.')
    a = o['artifacts'][artifact_id]
    p = confined(folder, a['path'], must_exist=True)
    need(sha(p.read_bytes()) == a['sha256'], 'ORCH_ARTIFACT_CHANGED', 'Referenced immutable artifact bytes changed.')
    return a


def current_subtask(o, sid, task, root, folder, *, dependencies=True):
    need(sid in o['subtasks'], 'ORCH_SUBTASK', 'Missing subtask.')
    s = o['subtasks'][sid]
    need(s['task_digest'] == task_digest(task), 'ORCH_TASK_BASELINE', 'Task objective or criteria changed; revise this subtask baseline.')
    evidence_list(s['baseline']['inputs'], root)
    if dependencies:
        for dep in s['baseline']['dependencies']:
            ds = current_subtask(o, dep, task, root, folder)
            need(ds['verified'], 'ORCH_DEPENDENCY_PENDING', 'Dependency is not currently verified.')
            verified_current(o, dep, task, root, folder)
            if s['dependency_versions']:
                need(s['dependency_versions'].get(dep) == hash_json(ds['verified'][-1]), 'ORCH_DEPENDENCY_CHANGED', 'Dependency delivery changed after this subtask input was bound.')
    return s


def producer(o, aid, function=None):
    need(aid in o['assignments'], 'ORCH_ASSIGNMENT', 'Unknown producer assignment.')
    a = o['assignments'][aid]
    need(a['generation'] == o['generation'] and a['state'] in ('active', 'completed') and a['native_id'] and a['role_reads'], 'ORCH_PRODUCER', 'Producer lacks current native/role-read provenance or ownership.')
    if a['subtask_id'] is not None:
        st = o['subtasks'][a['subtask_id']]
        matching = [x for x in st['baseline']['slots'] if x['slot'] == a['slot'] and x['function'] == a['function']]
        need(matching and a['baseline'] == st['digest'] and a['round'] == st['round'], 'ORCH_ASSIGNMENT_BASELINE', 'Producer assignment is not bound to the current baseline, function slot and round; explicitly rebind or replace it.')
    if function: need(a['function'] == function, 'ORCH_FUNCTION', 'Wrong producing function.')
    return a


def candidate_current(o, cid, task, root, folder):
    need(cid in o['candidates'], 'ORCH_CANDIDATE', 'Missing candidate.')
    c = o['candidates'][cid]; a = producer(o, c['assignment_id'], 'solver'); s = current_subtask(o, a['subtask_id'], task, root, folder)
    need(c['baseline'] == s['digest'] and c['round'] == s['round'], 'ORCH_STALE_CANDIDATE', 'Candidate baseline/round is stale.')
    newer = [v for v in o['candidates'].values() if v['supersedes'] == cid]
    need(not newer, 'ORCH_STALE_CANDIDATE', 'Candidate has been superseded.')
    evidence_current(o, c['artifact_id'], folder)
    return c


def candidate_set(o, sid, task, root, folder):
    s = current_subtask(o, sid, task, root, folder); found = []
    for slot in [x['slot'] for x in s['baseline']['slots'] if x['function'] == 'solver']:
        values = [c for c in o['candidates'].values() if o['assignments'][c['assignment_id']]['subtask_id'] == sid and o['assignments'][c['assignment_id']]['slot'] == slot and c['baseline'] == s['digest'] and c['round'] == s['round'] and not any(n['supersedes'] == c['candidate_id'] for n in o['candidates'].values())]
        need(len(values) == 1, 'ORCH_REQUIRED_CANDIDATE', 'Every frozen solver slot needs exactly one current candidate.')
        candidate_current(o, values[0]['candidate_id'], task, root, folder); found.append(values[0]['candidate_id'])
    return found


def review_set(o, sid, cids, root=None, folder=None):
    s = o['subtasks'][sid]; selected = []
    if s['baseline']['category'] != 'extra-complex': return selected
    for cid in cids:
        c = o['candidates'][cid]; solver = o['assignments'][c['assignment_id']]['slot']
        valid = [v for v in o['reviews'].values() if v['candidate_id'] == cid and v['baseline'] == s['digest'] and v['round'] == s['round']]
        need(valid and valid[-1]['outcome'] == 'passed', 'ORCH_REVIEW_GATE', 'Every current candidate requires its assigned reviewer pass.')
        reviewer = producer(o, valid[-1]['assignment_id'], 'reviewer')
        if folder is not None: evidence_current(o, valid[-1]['findings'], folder)
        slots = [x for x in s['baseline']['slots'] if x['slot'] == reviewer['slot']]
        need(slots[0]['solver_slot'] == solver, 'ORCH_REVIEW_MAPPING', 'Reviewer is assigned to another solver.')
        selected.append(valid[-1]['review_id'])
    return selected


def synthesis_current(o, synthesis_id, task, root, folder):
    need(synthesis_id in o['syntheses'], 'ORCH_SYNTHESIS', 'Missing synthesis.')
    v = o['syntheses'][synthesis_id]; a = producer(o, v['assignment_id'], 'senior'); s = current_subtask(o, a['subtask_id'], task, root, folder)
    need(v['baseline'] == s['digest'] and v['round'] == s['round'] and set(v['candidate_ids']) == set(candidate_set(o, a['subtask_id'], task, root, folder)), 'ORCH_STALE_SYNTHESIS', 'Synthesis input set or baseline is stale.')
    need(set(v['review_ids']) == set(review_set(o, a['subtask_id'], v['candidate_ids'], root, folder)), 'ORCH_REVIEW_GATE', 'Synthesis review versions are stale.')
    evidence_current(o, v['artifact_id'], folder)
    return v


EVENT_KEYS = {
 'manager.reserve': ('assignment_id', 'role', 'fit', 'runtime', 'settings', 'context', 'source_refs', 'authority', 'bootstrap_receipt'),
 'manager.receipt': ('assignment_id', 'receipt'), 'manager.activate': ('assignment_id', 'role_reads'),
 'manager.reconnect': ('assignment_id', 'receipt'),
 'subtask.define': ('subtask_id', 'baseline'), 'subtask.revise': ('subtask_id', 'baseline', 'reason'),
 'assignment.reserve': ('assignment_id', 'subtask_id', 'slot', 'role', 'fit', 'runtime', 'settings', 'context'),
 'assignment.receipt': ('assignment_id', 'receipt'), 'assignment.reads': ('assignment_id', 'role_reads'),
 'assignment.inputs': ('assignment_id', 'role', 'fit', 'runtime', 'context', 'receipt', 'reason'),
 'assignment.observe': ('assignment_id', 'receipt', 'changes'), 'assignment.uncertain': ('assignment_id', 'reason'),
 'assignment.revoke': ('assignment_id', 'reason'), 'assignment.resume': ('assignment_id', 'runtime', 'reason'),
 'artifact.register': ('artifact_id', 'assignment_id', 'source_path'),
 'candidate.record': tuple(CAND_FIELDS), 'review.record': tuple(REVIEW_FIELDS),
 'conflict.record': ('conflict_id', 'assignment_id', 'candidate_ids', 'baseline', 'round', 'explanation', 'progress'),
 'conflict.deliver': ('conflict_id', 'solver_slot', 'receipt'),
 'synthesis.record': tuple(SYNTH_FIELDS), 'acceptance.record': tuple(ACCEPT_FIELDS),
 'result.record': tuple(RESULT_FIELDS),
 'subtask.verify': ('subtask_id', 'baseline', 'round', 'result_id', 'acceptance_id', 'artifacts', 'criteria', 'inspection'),
 'stop.request': ('reason', 'action'), 'stop.finish': ('reason',), 'execution.resume': ('settings', 'reason'),
 'manager.replace': ('reason', 'user_authorized', 'observations'),
 'execution.finish': ('outcome', 'criteria', 'inspection'), 'block': ('reason', 'next_step'),
}


def validate_event_data(kind, data):
    need(kind in EVENT_KEYS, 'ORCH_EVENT_KIND', 'Unknown typed event kind.')
    keys(data, EVENT_KEYS[kind])
    for field, value in data.items():
        if field.endswith('_id') or field in ('slot', 'solver_slot', 'artifact_id') or (field == 'findings' and kind == 'review.record'):
            if value is not None: ident(value)
        elif field in ('candidate_ids', 'review_ids', 'artifact_ids', 'artifacts', 'resolved_conflicts'):
            strings(value)
            for item in value: ident(item)
        elif field == 'baseline' and kind not in ('subtask.define', 'subtask.revise'): digest(value)
        elif field == 'round': integer(value, 1)
        elif field == 'role': role(value)
        elif field == 'fit': fit(value)
        elif field == 'runtime': runtime(value)
        elif field == 'settings': settings(value)
        elif field in ('context', 'source_refs', 'inspection', 'changes', 'checks'): evidence_list(value, nonempty=field in ('context', 'source_refs', 'inspection', 'checks'))
        elif field in ('reason', 'next_step', 'authority', 'progress', 'source_path'): text(value)
    if kind in ('subtask.define', 'subtask.revise'): baseline(data['baseline'])
    if kind == 'review.record': need(data['outcome'] in ('passed', 'rejected'), 'ORCH_REVIEW_GATE', 'Invalid review outcome.')
    if kind == 'candidate.record':
        for field in ('findings', 'revalidation'): text(data[field], True)
        if data['supersedes'] is not None: ident(data['supersedes'])
    if kind == 'result.record': strings(data['limitations'])
    if kind in ('subtask.verify', 'execution.finish'):
        need(isinstance(data['criteria'], list), 'ORCH_CRITERIA', 'Criterion evidence must be a list.')
        for item in data['criteria']: keys(item, ('criterion', 'evidence')); text(item['criterion']); text(item['evidence'])


def overlap(a, b):
    return a == b or a.startswith(b.rstrip('/') + '/') or b.startswith(a.rstrip('/') + '/')


def reserve(o, data, task, root, folder, *, manager=False, external_owners=(), rebinding=False):
    aid = data['assignment_id']; ident(aid)
    need((aid in o['assignments']) == rebinding, 'ORCH_DUPLICATE_ASSIGNMENT', 'Only an explicit input handoff can replace an existing assignment record.')
    previous = o['assignments'].get(aid) if rebinding else None
    role(data['role'], root); fit(data['fit'], root); runtime(data['runtime'], root); settings(data['settings'], root); evidence_list(data['context'], root, nonempty=True)
    need(data['settings'] == o['settings'], 'ORCH_SETTINGS', 'Assignment settings differ from the manager identity contract.')
    need(data['runtime']['available_slots'] > 0, 'ORCH_CAPACITY', 'No observed native capacity; retain the logical slot queued.')
    sid = None if manager else data['subtask_id']; function = 'manager'; perspective = 'Project Director'; slot_name = 'manager'; acceptance_id = None
    if not manager:
        need(data['runtime']['depth'] >= 2, 'ORCH_CAPABILITY', 'Nested worker dispatch requires observed depth two support.')
        s = current_subtask(o, sid, task, root, folder); slot_name = data['slot']
        if not s['dependency_versions']:
            s['dependency_versions'] = {dep: hash_json(o['subtasks'][dep]['verified'][-1]) for dep in s['baseline']['dependencies']}
        common_path = str(folder.relative_to(root) / 'artifacts/orchestration' / ('baseline_' + s['digest'] + '.json'))
        need({'path': common_path, 'sha256': s['digest']} in data['context'], 'ORCH_COMMON_PACKET', 'Every assigned worker receives the identical immutable complete baseline packet.')
        slots = [x for x in s['baseline']['slots'] if x['slot'] == slot_name]; need(len(slots) == 1, 'ORCH_SLOT', 'Assignment is not in the frozen required team.')
        function = slots[0]['function']; perspective = slots[0]['perspective']
        need(not any(a is not previous and a['subtask_id'] == sid and a['slot'] == slot_name and a['state'] != 'revoked' for a in o['assignments'].values()), 'ORCH_SLOT_OWNER', 'Revoke reconciled old ownership before replacing a logical slot.')
        if function in ('solver', 'reviewer', 'senior'):
            allowed = str(folder.relative_to(root) / 'artifacts' / 'orchestration' / 'work' / aid)
            need(data['fit']['writes'] and all(p == allowed or p.startswith(allowed + '/') for p in data['fit']['writes']), 'ORCH_CANDIDATE_SCOPE', 'Candidate functions own only their separate artifact workspace.')
        else:
            need(all(any(p == q or p.startswith(q.rstrip('/') + '/') for q in s['baseline']['writes']) for p in data['fit']['writes']), 'ORCH_WRITE_SCOPE', 'Assignment exceeds authorized baseline writes.')
        if function == 'senior': candidate_set(o, sid, task, root, folder); review_set(o, sid, candidate_set(o, sid, task, root, folder), root, folder)
        if function == 'implementer':
            accepts = [v for v in event_records(o, 'acceptance.record', 'acceptance_id', 'acceptances') if o['assignments'][o['syntheses'][v['synthesis_id']]['assignment_id']]['subtask_id'] == sid]
            need(accepts, 'ORCH_ACCEPTANCE', 'Implementation requires manager acceptance first.'); synthesis_current(o, accepts[-1]['synthesis_id'], task, root, folder); acceptance_id = accepts[-1]['acceptance_id']
    for a in [*unresolved(o), *external_owners]:
        if a is previous: continue
        need(not any(overlap(p, q) for p in data['fit']['writes'] for q in a['fit']['writes']), 'ORCH_WRITE_OVERLAP', 'Another unresolved assignment owns overlapping writes.')
    o['assignments'][aid] = dict(assignment_id=aid, subtask_id=sid, slot=slot_name, function=function, perspective=perspective, role=data['role'], fit=data['fit'], runtime=data['runtime'], settings=data['settings'], context=data['context'], state='reserved', native_id=None, native_receipt=None, role_reads=None, observations=[], generation=o['generation'], acceptance_id=acceptance_id, baseline=o['task_digest'] if manager else s['digest'], round=0 if manager else s['round'], input_receipt=None)
    if not manager: require_input_packet(o, o['assignments'][aid], task, root, folder)


def role_reads(a, value):
    keys(value, ('agents_sha256', 'role_sha256', 'evidence'))
    need(value['agents_sha256'] == a['role']['agents_sha256'] and value['role_sha256'] == a['role']['role_sha256'], 'ORCH_ROLE_READS', 'Worker did not confirm the selected exact role pair.')
    text(value['evidence'])


def apply(task, event, root, folder, other_tasks=()):
    keys(event, ('event_id', 'actor', 'execution_id', 'generation', 'kind', 'data'))
    ident(event['event_id']); native_id(event['actor']); integer(event['generation'])
    kind = event['kind']; data = copy.deepcopy(event['data']); validate_event_data(kind, data)
    # The owning Task transaction carries the exact semantic decision. This
    # pure state transform does not create a second writer or acquire a lock.
    import sys
    guard = sys.modules.get('ontology_guards')
    if guard is not None:
        guard.checkpoint(targets=False)
    o = copy.deepcopy(task['orchestration']); validate(o); writes = []
    external_owners = [a for other in other_tasks if other.get('schema_version') == 2 and other['task_id'] != task['task_id'] for a in unresolved(other['orchestration'])]
    need(not any(e['event_id'] == event['event_id'] for e in o['events']), 'ORCH_DUPLICATE_EVENT', 'Event was already accepted; inspect state, do not replay.')
    starting = kind == 'manager.reserve' and o['stage'] in ('unassigned', 'finished')
    recovering = kind == 'manager.replace'
    if starting:
        need(event['execution_id'] is not None, 'ORCH_EXECUTION_ID', 'Supply a new stable execution ID for reservation.'); ident(event['execution_id'])
        need(event['generation'] == 1 and event['execution_id'] != o['execution_id'] and not any(h['execution_id'] == event['execution_id'] for h in o['history']), 'ORCH_EXECUTION_ID', 'New execution needs unique identity and generation 1.')
        need(task['status'] == 'open' and not unresolved(o), 'ORCH_LIFECYCLE', 'Start only open work after previous ownership is reconciled.')
        history = o['history']; events = o['events']
        if o['execution_id']:
            history.append({k: v for k, v in o.items() if k not in ('history', 'events')})
        o = empty(); o.update(execution_id=event['execution_id'], generation=1, bootstrap=event['actor'], writer=event['actor'], stage='reserved', task_digest=task_digest(task), history=history, events=events)
        need(receipt(data['bootstrap_receipt'], subject=event['actor']) == 'running', 'ORCH_BOOTSTRAP_RECEIPT', 'Bootstrap must be observed running in the native roster.')
        settings(data['settings'], root); evidence_list(data['context'], root, True); evidence_list(data['source_refs'], root, True); text(data['authority'])
        o.update(settings=data['settings'], context=data['context'], source_refs=data['source_refs'], authority=data['authority'])
        reserve(o, data, task, root, folder, manager=True, external_owners=external_owners); o['manager_id'] = data['assignment_id']
    else:
        need(event['execution_id'] == o['execution_id'] and event['generation'] == o['generation'], 'ORCH_STALE_GENERATION', 'Stale execution/generation.')
        if recovering:
            need(event['actor'] == o['bootstrap'] and data['user_authorized'] is True, 'ORCH_RECOVERY_OWNER', 'Recovery requires explicit original-bootstrap authority.')
            reconcile_observations(o, data['observations'], root)
            need(not unresolved(o), 'ORCH_RECOVERY_OWNER', 'Unconfirmed owners prevent atomic writer replacement.')
        else:
            need(event['actor'] == o['writer'] and event['actor'] is not None, 'ORCH_WRITER', 'Actor is not the sole canonical writer.')
        controls = ('assignment.observe', 'assignment.uncertain', 'assignment.revoke', 'stop.request', 'stop.finish', 'execution.resume', 'manager.replace', 'block', 'manager.receipt', 'manager.activate', 'manager.reconnect', 'manager.reserve', 'assignment.receipt')
        need(o['stage'] == 'active' or kind in controls, 'ORCH_DISPATCH_STOPPED', 'Execution is not active; only controlling reconciliation is permitted.')
        if kind in ('manager.receipt', 'assignment.receipt'):
            aid = data['assignment_id']; need(aid in o['assignments'], 'ORCH_ASSIGNMENT', 'Unknown reservation.'); a = o['assignments'][aid]
            need(a['state'] in ('reserved', 'launch_uncertain') and a['native_id'] is None, 'ORCH_DUPLICATE_RECEIPT', 'The original reservation already has a receipt.')
            nid = receipt(data['receipt'], launch=True)
            parent = o['bootstrap'] if a['function'] == 'manager' else o['writer']
            need(nid != parent and nid.startswith(parent.rstrip('/') + '/') and not any(x['native_id'] == nid for x in [*o['assignments'].values(), *external_owners]), 'ORCH_NATIVE_DISTINCT', 'Native instance must be a new distinct child of the designated coordinator.')
            a.update(native_id=nid, native_receipt=data['receipt'], state='active')
            if a['function'] == 'manager': o['stage'] = 'receipt_recorded'
        elif kind in ('assignment.reads', 'manager.activate'):
            aid = data['assignment_id']; need(aid in o['assignments'], 'ORCH_ASSIGNMENT', 'Unknown assignment.'); a = o['assignments'][aid]
            need(a['native_id'] and a['state'] == 'active', 'ORCH_RECEIPT_REQUIRED', 'A confirmed native receipt is required first.'); role_reads(a, data['role_reads']); a['role_reads'] = data['role_reads']
            if kind == 'manager.activate':
                need(aid == o['manager_id'] and o['stage'] == 'receipt_recorded', 'ORCH_HANDOFF', 'Invalid manager activation.'); o.update(writer=a['native_id'], stage='active')
        elif kind == 'manager.reconnect':
            need(data['assignment_id'] == o['manager_id'], 'ORCH_MANAGER', 'Reconnect only the designated manager.')
            manager = o['assignments'][o['manager_id']]
            need(o['stage'] == 'active' and manager['native_id'] is not None and o['writer'] == manager['native_id'] and manager['role_reads'], 'ORCH_MANAGER_NOT_LIVE', 'Reconnection requires an activated confirmed manager, not a running bootstrap host.')
            need(receipt(data['receipt'], subject=manager['native_id']) == 'running', 'ORCH_MANAGER_NOT_LIVE', 'Reconnect requires current native live evidence.')
        elif kind in ('subtask.define', 'subtask.revise'):
            sid = data['subtask_id']; ident(sid); baseline(data['baseline'], root)
            if kind == 'subtask.define': need(sid not in o['subtasks'], 'ORCH_DUPLICATE_SUBTASK', 'Subtask exists.')
            else:
                need(sid in o['subtasks'], 'ORCH_SUBTASK', 'Missing subtask.'); text(data['reason'])
                affected = {sid}
                while True:
                    expanded = affected | {key for key, sub in o['subtasks'].items() if set(sub['baseline']['dependencies']) & affected}
                    if expanded == affected: break
                    affected = expanded
                need(not any(a['subtask_id'] in affected for a in unresolved(o)), 'ORCH_BASELINE_OWNERS', 'Reconcile/revoke affected workers before changing baseline.')
                old = o['subtasks'][sid]
                has_candidates = any(o['assignments'][x['assignment_id']]['subtask_id'] == sid for x in o['candidates'].values())
                resolved = False
                if old['verified']:
                    try:
                        verified_current(o, sid, task, root, folder); resolved = True
                    except OrchestrationError:
                        pass
                if old['active_conflicts'] or (has_candidates and not resolved):
                    need(data['baseline']['category'] == old['baseline']['category'] and data['baseline']['slots'] == old['baseline']['slots'], 'ORCH_RECLASSIFICATION', 'Frozen originating solver/reviewer slots cannot change while their cycle is unresolved.')
            prior = o['subtasks'].get(sid); versions = [] if prior is None else prior['versions'] + [{k: prior[k] for k in ('baseline', 'digest', 'task_digest', 'round', 'dependency_versions', 'active_conflicts')}]
            o['subtasks'][sid] = dict(baseline=data['baseline'], digest=hash_json(data['baseline']), task_digest=task_digest(task), round=1 if prior is None else prior['round'] + 1, versions=versions, verified=[], dependency_versions={}, active_conflicts=[] if prior is None else list(prior['active_conflicts']))
            dependency_cycle(o, sid, set())
            artifact_id = 'baseline_' + o['subtasks'][sid]['digest']
            if artifact_id not in o['artifacts']:
                raw = json.dumps(data['baseline'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
                rel = 'artifacts/orchestration/' + artifact_id + '.json'
                need(not confined(folder, rel).exists(), 'ORCH_ARTIFACT_COLLISION', 'Baseline version path already exists.')
                o['artifacts'][artifact_id] = dict(path=rel, sha256=sha(raw), size=len(raw), assignment_id=o['manager_id'], generation=o['generation'])
                writes.append({'path': rel, 'content': raw})
        elif kind == 'assignment.reserve': reserve(o, data, task, root, folder, external_owners=external_owners)
        elif kind == 'assignment.inputs':
            aid = data['assignment_id']; need(aid in o['assignments'], 'ORCH_ASSIGNMENT', 'Unknown input-handoff assignment.')
            previous = o['assignments'][aid]
            need(previous['generation'] == o['generation'] and previous['state'] in ('active', 'completed', 'stopped') and previous['function'] != 'manager', 'ORCH_ASSIGNMENT_BASELINE', 'Only an existing non-revoked worker can receive a context rebind.')
            need(all(data['role'][key] == previous['role'][key] for key in ('name', 'agents_path', 'role_path', 'agents_sha256', 'role_sha256')), 'ORCH_ROLE_CHANGED', 'A context rebind cannot silently change the loaded role pair.')
            current_slot = [x for x in o['subtasks'][previous['subtask_id']]['baseline']['slots'] if x['slot'] == previous['slot'] and x['function'] == previous['function']]
            need(current_slot, 'ORCH_ASSIGNMENT_BASELINE', 'Incompatible category/function change requires revocation and a suitable replacement.')
            text(data['reason']); keys(data['receipt'], ('tool', 'native_id', 'artifact_sha256s', 'evidence'))
            need(data['receipt']['tool'] in ('collaboration.send_message', 'collaboration.followup_task') and data['receipt']['native_id'] == previous['native_id'], 'ORCH_INPUT_RECEIPT', 'Input handoff must target the same actual native instance.')
            strings(data['receipt']['artifact_sha256s']); text(data['receipt']['evidence'])
            need(set(data['receipt']['artifact_sha256s']) == {r['sha256'] for r in data['context']}, 'ORCH_INPUT_RECEIPT', 'Input handoff must identify the exact packet digests.')
            # Dependencies and historical candidates still resolve through this
            # record while reservation checks run. Exclude only its own lease.
            reserve(o, {'assignment_id':aid, 'subtask_id':previous['subtask_id'], 'slot':previous['slot'], 'role':data['role'], 'fit':data['fit'], 'runtime':data['runtime'], 'settings':previous['settings'], 'context':data['context']}, task, root, folder, external_owners=external_owners, rebinding=True)
            rebound = o['assignments'][aid]
            for key in ('native_id', 'native_receipt', 'role_reads', 'observations'): rebound[key] = previous[key]
            rebound.update(state='active', input_receipt=data['receipt'])
        elif kind in ('assignment.observe', 'assignment.uncertain', 'assignment.revoke', 'assignment.resume'):
            aid = data['assignment_id']; need(aid in o['assignments'], 'ORCH_ASSIGNMENT', 'Unknown assignment.'); a = o['assignments'][aid]
            need(a['generation'] == o['generation'], 'ORCH_STALE_GENERATION', 'Old generation assignment.')
            need(a['state'] != 'revoked', 'ORCH_REVOKED', 'Revoked ownership cannot be restored by observation or uncertainty; reconcile unexpected native activity as a blocker.')
            if kind == 'assignment.observe':
                observed = receipt(data['receipt'], subject=a['native_id']); evidence_list(data['changes'], root)
                need(observed is not None, 'ORCH_NATIVE_UNCONFIRMED', 'Absence from a roster does not prove stopping.')
                need(observed not in ('running', 'idle') or a['state'] not in ('completed', 'stopped', 'failed'), 'ORCH_RESUME_REQUIRED', 'Returning activity requires explicit assignment.resume with current capacity and scope checks.')
                a['observations'].append({'receipt': data['receipt'], 'changes': data['changes']})
                if not (a['state'] == 'stop_requested' and observed in ('running', 'idle')):
                    a['state'] = {'running': 'active', 'completed': 'completed', 'interrupted': 'stopped', 'failed': 'failed', 'idle': 'active'}[observed]
            elif kind == 'assignment.uncertain':
                text(data['reason']); a['state'] = 'launch_uncertain'
            elif kind == 'assignment.revoke':
                text(data['reason']); need(a['state'] in ('stopped', 'completed', 'failed') and a['observations'], 'ORCH_REVOKE_UNCONFIRMED', 'Revoke only an observed stopped/completed assignment.'); a['state'] = 'revoked'
            else:
                text(data['reason']); runtime(data['runtime'], root); need(data['runtime']['available_slots'] > 0 and a['state'] in ('completed', 'stopped') and a['observations'], 'ORCH_RESUME', 'Reconnection requires observed state and capacity.')
                need(not any(overlap(p, q) for other in [*unresolved(o), *external_owners] if other is not a for p in a['fit']['writes'] for q in other['fit']['writes']), 'ORCH_WRITE_OVERLAP', 'Scope is now owned by another assignment.'); a['state'] = 'active'
        elif kind == 'artifact.register':
            ident(data['artifact_id']); need(data['artifact_id'] not in o['artifacts'], 'ORCH_ARTIFACT_COLLISION', 'Artifact version already exists.'); a = producer(o, data['assignment_id'])
            if a['function'] == 'solver':
                st = o['subtasks'][a['subtask_id']]
                planned_slots = {x['slot'] for x in st['baseline']['slots'] if x['function'] == 'solver'}
                dispatched_slots = {x['slot'] for x in o['assignments'].values() if x['subtask_id'] == a['subtask_id'] and x['function'] == 'solver' and x['native_id'] and x['generation'] == o['generation'] and x['baseline'] == st['digest'] and x['round'] == st['round'] and x['state'] != 'revoked'}
                need(planned_slots <= dispatched_slots, 'ORCH_INDEPENDENT_DISPATCH', 'Dispatch every initial queued solver before importing candidate bytes.')
            source = confined(root, data['source_path'], must_exist=True)
            need(any(data['source_path'] == p or data['source_path'].startswith(p.rstrip('/') + '/') for p in a['fit']['writes']), 'ORCH_ARTIFACT_OWNER', 'Producer does not own the source artifact path.')
            content = source.read_bytes(); suffix = source.suffix if re.fullmatch(r'\.[A-Za-z0-9]{1,10}', source.suffix) else '.bin'
            rel = 'artifacts/orchestration/' + data['artifact_id'] + suffix
            target = confined(folder, rel); need(not target.exists(), 'ORCH_ARTIFACT_COLLISION', 'Immutable version path already exists.')
            o['artifacts'][data['artifact_id']] = dict(path=rel, sha256=sha(content), size=len(content), assignment_id=data['assignment_id'], generation=o['generation'])
            writes.append({'path': rel, 'content': content})
        elif kind == 'candidate.record':
            a = producer(o, data['assignment_id'], 'solver'); s = current_subtask(o, a['subtask_id'], task, root, folder)
            need(data['baseline'] == s['digest'] and data['round'] == s['round'], 'ORCH_STALE_CANDIDATE', 'Candidate must use the current complete baseline and round.')
            ident(data['candidate_id']); need(data['candidate_id'] not in o['candidates'], 'ORCH_DUPLICATE_CANDIDATE', 'Candidate ID exists.')
            art = evidence_current(o, data['artifact_id'], folder); need(art['assignment_id'] == a['assignment_id'], 'ORCH_ARTIFACT_OWNER', 'Candidate producer does not own artifact.')
            same = [v for v in o['candidates'].values() if o['assignments'][v['assignment_id']]['slot'] == a['slot'] and o['assignments'][v['assignment_id']]['subtask_id'] == a['subtask_id']]
            leaves = [v for v in same if not any(n['supersedes'] == v['candidate_id'] for n in same)]
            need((not same and data['supersedes'] is None) or (len(leaves) == 1 and data['supersedes'] == leaves[0]['candidate_id']), 'ORCH_CANDIDATE_CHAIN', 'Revisions must preserve originating solver and prior candidate.')
            if same:
                need(data['findings'] or data['revalidation'], 'ORCH_PROGRESS', 'A revision needs findings response or versioned revalidation.'); text(data['findings'], True); text(data['revalidation'], True)
                old_art = o['artifacts'][leaves[0]['artifact_id']]
                need(art['sha256'] != old_art['sha256'] or data['revalidation'], 'ORCH_PROGRESS', 'Unchanged candidate needs evidence-backed revalidation.')
            for conflict_id in s['active_conflicts']:
                conflict = o['conflicts'][conflict_id]
                required = {o['assignments'][o['candidates'][cid]['assignment_id']]['slot'] for cid in conflict['candidate_ids']}
                need(set(conflict['deliveries']) == required, 'ORCH_CONFLICT_DELIVERY', 'Deliver identical conflict to every originating solver before revisions, including after baseline changes.')
            o['candidates'][data['candidate_id']] = data
        elif kind == 'review.record':
            a = producer(o, data['assignment_id'], 'reviewer'); require_input_packet(o, a, task, root, folder); c = candidate_current(o, data['candidate_id'], task, root, folder); ca = o['assignments'][c['assignment_id']]; s = o['subtasks'][a['subtask_id']]
            slot = next(x for x in s['baseline']['slots'] if x['slot'] == a['slot'])
            need(a['subtask_id'] == ca['subtask_id'] and slot['solver_slot'] == ca['slot'] and a['native_id'] != ca['native_id'], 'ORCH_REVIEW_MAPPING', 'Reviewer does not independently own this solver mapping.')
            need(data['baseline'] == c['baseline'] and data['round'] == c['round'] and data['outcome'] in ('passed', 'rejected'), 'ORCH_REVIEW_GATE', 'Review must attest exact current version and permitted outcome.')
            need(evidence_current(o, data['findings'], folder)['assignment_id'] == a['assignment_id'], 'ORCH_ARTIFACT_OWNER', 'Reviewer must produce its own findings.')
            need(not any(v['candidate_id'] == data['candidate_id'] for v in o['reviews'].values()), 'ORCH_REVIEW_REPLAY', 'A rejection requires a new/revalidated candidate, not a manager override.')
            ident(data['review_id']); need(data['review_id'] not in o['reviews'], 'ORCH_DUPLICATE_REVIEW', 'Review ID exists.'); o['reviews'][data['review_id']] = data
        elif kind in ('synthesis.record', 'conflict.record'):
            a = producer(o, data['assignment_id'], 'senior'); require_input_packet(o, a, task, root, folder); s = current_subtask(o, a['subtask_id'], task, root, folder); expected = candidate_set(o, a['subtask_id'], task, root, folder)
            need(set(data['candidate_ids']) == set(expected) and len(data['candidate_ids']) == len(expected) and data['baseline'] == s['digest'] and data['round'] == s['round'], 'ORCH_SYNTHESIS_INPUTS', 'Use every required exact current candidate.')
            passed = review_set(o, a['subtask_id'], expected, root, folder)
            if kind == 'synthesis.record':
                strings(data['resolved_conflicts'])
                need(set(data['resolved_conflicts']) == set(s['active_conflicts']), 'ORCH_CONFLICT_RESOLUTION', 'Synthesis must explicitly resolve every active shared conflict.')
                need(set(data['review_ids']) == set(passed), 'ORCH_REVIEW_GATE', 'Synthesis must name exact current review passes.'); need(evidence_current(o, data['artifact_id'], folder)['assignment_id'] == a['assignment_id'], 'ORCH_ARTIFACT_OWNER', 'Senior must produce the synthesis artifact.')
                keys(data['dispositions'], ('retained', 'omitted', 'differences', 'assumptions', 'interfaces', 'requirements', 'risks', 'verification', 'unresolved'))
                strings(data['dispositions']['unresolved']); need(not data['dispositions']['unresolved'], 'ORCH_CONTRADICTION', 'Unresolved core commitments cannot be accepted.')
                for k in ('retained', 'assumptions', 'interfaces', 'requirements', 'verification'): strings(data['dispositions'][k], True)
                for k in ('omitted', 'risks'): strings(data['dispositions'][k])
                need(set(data['dispositions']['differences']) == {'complementary', 'terminology', 'scope', 'evidence', 'exclusive'}, 'ORCH_DISPOSITIONS', 'Classify every required difference type.')
                for v in data['dispositions']['differences'].values(): text(v)
                ident(data['synthesis_id']); need(data['synthesis_id'] not in o['syntheses'], 'ORCH_DUPLICATE_SYNTHESIS', 'Synthesis ID exists.'); o['syntheses'][data['synthesis_id']] = data
            else:
                text(data['progress']); art = evidence_current(o, data['explanation'], folder); need(art['assignment_id'] == a['assignment_id'], 'ORCH_ARTIFACT_OWNER', 'Senior must produce conflict explanation.')
                ident(data['conflict_id']); need(data['conflict_id'] not in o['conflicts'], 'ORCH_DUPLICATE_CONFLICT', 'Conflict ID exists.')
                o['conflicts'][data['conflict_id']] = {**data, 'deliveries': {}}; s['active_conflicts'].append(data['conflict_id']); s['round'] += 1
        elif kind == 'conflict.deliver':
            need(data['conflict_id'] in o['conflicts'], 'ORCH_CONFLICT', 'Missing conflict.'); c = o['conflicts'][data['conflict_id']]; sid = o['assignments'][c['assignment_id']]['subtask_id']; slots = {o['assignments'][o['candidates'][cid]['assignment_id']]['slot'] for cid in c['candidate_ids']}
            need(data['solver_slot'] in slots and data['solver_slot'] not in c['deliveries'], 'ORCH_CONFLICT_DELIVERY', 'Invalid or repeated conflict recipient.')
            keys(data['receipt'], ('native_id', 'explanation_sha256', 'evidence')); native_id(data['receipt']['native_id']); text(data['receipt']['evidence'])
            need(any(a['slot'] == data['solver_slot'] and a['subtask_id'] == sid and a['native_id'] == data['receipt']['native_id'] and a['state'] != 'revoked' for a in o['assignments'].values()), 'ORCH_CONFLICT_DELIVERY', 'Delivery recipient is not the originating current solver.')
            need(data['receipt']['explanation_sha256'] == evidence_current(o, c['explanation'], folder)['sha256'], 'ORCH_CONFLICT_DELIVERY', 'All solvers must receive identical conflict bytes.'); c['deliveries'][data['solver_slot']] = data['receipt']
        elif kind == 'acceptance.record':
            syn = synthesis_current(o, data['synthesis_id'], task, root, folder)
            sid = o['assignments'][syn['assignment_id']]['subtask_id']
            need(not any(a['subtask_id'] == sid and a['function'] == 'implementer' for a in unresolved(o)), 'ORCH_IMPLEMENTATION_OWNER', 'Reconcile the current implementer before replacing acceptance.')
            evidence_list(data['inspection'], root, True); ident(data['acceptance_id']); need(data['acceptance_id'] not in o['acceptances'], 'ORCH_DUPLICATE_ACCEPTANCE', 'Acceptance ID exists.'); o['acceptances'][data['acceptance_id']] = data
            o['subtasks'][sid]['active_conflicts'] = []
        elif kind == 'result.record':
            a = producer(o, data['assignment_id']); require_input_packet(o, a, task, root, folder); need(a['function'] in ('worker', 'implementer'), 'ORCH_FUNCTION', 'Only dedicated execution owner supplies results.'); s = current_subtask(o, a['subtask_id'], task, root, folder)
            need(data['baseline'] == s['digest'] and data['round'] == s['round'], 'ORCH_RESULT_BASELINE', 'Result must bind to current baseline and round.')
            if a['function'] == 'implementer':
                need(data['acceptance_id'] == a['acceptance_id'], 'ORCH_IMPLEMENTATION_TARGET', 'Result must target the exact acceptance bound at implementation assignment.'); syn = acceptance_current(o, data['acceptance_id'], task, root, folder)
                need(o['assignments'][syn['assignment_id']]['subtask_id'] == a['subtask_id'], 'ORCH_IMPLEMENTATION_TARGET', 'Implementation targets another subtask.')
            else: need(data['acceptance_id'] is None, 'ORCH_GENERIC', 'Generic work has no synthesis acceptance.')
            strings(data['artifact_ids'], True)
            for aid in data['artifact_ids']: need(evidence_current(o, aid, folder)['assignment_id'] == a['assignment_id'], 'ORCH_ARTIFACT_OWNER', 'Deliverable owner differs.')
            evidence_list(data['changes'], root, s['baseline']['implementation_required']); evidence_list(data['checks'], root, True); strings(data['limitations'])
            ident(data['result_id']); need(data['result_id'] not in o['results'], 'ORCH_DUPLICATE_RESULT', 'Result ID exists.'); o['results'][data['result_id']] = data
        elif kind == 'subtask.verify':
            s = current_subtask(o, data['subtask_id'], task, root, folder)
            need(data['baseline'] == s['digest'] and data['round'] == s['round'], 'ORCH_VERIFICATION_STALE', 'Verification uses a stale baseline/round.')
            need(not any(a['subtask_id'] == data['subtask_id'] for a in unresolved(o)), 'ORCH_VERIFY_OWNERS', 'Observe every child stopped/completed before final subtask verification.')
            criteria_cover(data['criteria'], s['baseline']['criteria']); evidence_list(data['inspection'], root, True)
            for aid in data['artifacts']: evidence_current(o, aid, folder)
            need(data['artifacts'], 'ORCH_DELIVERY', 'Direct inspected artifacts are required.')
            if s['baseline']['category'] == 'generic' or s['baseline']['implementation_required']:
                need(data['result_id'] in o['results'], 'ORCH_DELIVERY', 'Performed work result is required.')
                rr = o['results'][data['result_id']]; result_current(o, rr, task, root, folder); need(rr['baseline'] == s['digest'] and rr['round'] == s['round'], 'ORCH_RESULT_BASELINE', 'Performed result is stale.'); producer(o, rr['assignment_id']); need(o['assignments'][rr['assignment_id']]['subtask_id'] == data['subtask_id'] and set(rr['artifact_ids']) <= set(data['artifacts']), 'ORCH_DELIVERY', 'Verify the actual assigned deliverables.')
                if rr['acceptance_id']: acceptance_current(o, rr['acceptance_id'], task, root, folder)
            else:
                need(data['acceptance_id'] in o['acceptances'], 'ORCH_ACCEPTANCE', 'Analysis requires accepted current synthesis.'); syn = acceptance_current(o, data['acceptance_id'], task, root, folder)
                need(o['assignments'][syn['assignment_id']]['subtask_id'] == data['subtask_id'] and syn['artifact_id'] in data['artifacts'], 'ORCH_DELIVERY', 'Inspect the accepted analysis artifact.')
            s['verified'].append(data)
        elif kind == 'stop.request':
            text(data['reason']); need(data['action'] in ('pause', 'cancel', 'replace', 'settings', 'failure'), 'ORCH_STOP', 'Unknown controlling stop action.'); o['stage'] = 'stopping'
            for a in unresolved(o, manager=False):
                if a['native_id']: a['state'] = 'stop_requested'
        elif kind == 'stop.finish':
            text(data['reason']); need(not unresolved(o, manager=False), 'ORCH_STOP_UNCONFIRMED', 'Worker ownership is unresolved.'); o['stage'] = 'stopped'
        elif kind == 'execution.resume':
            text(data['reason']); need(o['stage'] == 'stopped' and not unresolved(o, manager=False), 'ORCH_STOP_UNCONFIRMED', 'Reconcile team before resuming or changing settings.'); settings(data['settings'], root)
            need(data['settings'] == o['settings'], 'ORCH_SETTINGS_REPLACEMENT', 'A setting change requires reconciled manager replacement and a new generation.'); o['stage'] = 'active'
        elif kind == 'manager.replace':
            text(data['reason'])
            for a in o['assignments'].values(): a['state'] = 'revoked'
            o.update(generation=o['generation'] + 1, writer=o['bootstrap'], manager_id=None, stage='stopped')
            # A new reservation is required through the explicit replacement reservation event.
        elif kind == 'execution.finish':
            need(data['outcome'] in ('delivered', 'stopped', 'cancelled'), 'ORCH_OUTCOME', 'Invalid finish outcome.'); need(not unresolved(o, manager=False), 'ORCH_STOP_UNCONFIRMED', 'All workers require native reconciliation.'); evidence_list(data['inspection'], root, True)
            if data['outcome'] == 'delivered':
                criteria_cover(data['criteria'], task['definition_of_done']); need(o['subtasks'], 'ORCH_COMPLETION', 'At least one bounded subtask is required.')
                for sid in o['subtasks']:
                    verified_current(o, sid, task, root, folder)
            o['verifications'].append(data); o['stage'] = 'finished' if data['outcome'] == 'delivered' else 'stopped'
        elif kind == 'block':
            text(data['reason']); text(data['next_step']); o['blockers'].append(data['reason']); o['stage'] = 'blocked'
        elif kind == 'manager.reserve':
            need(o['stage'] == 'stopped' and o['manager_id'] is None and event['actor'] == o['bootstrap'], 'ORCH_DUPLICATE_MANAGER', 'An execution already has its designated manager.')
            settings(data['settings'], root); evidence_list(data['context'], root, True); evidence_list(data['source_refs'], root, True); text(data['authority']); o.update(settings=data['settings'], context=data['context'], source_refs=data['source_refs'], authority=data['authority']); reserve(o, data, task, root, folder, manager=True, external_owners=external_owners); o['manager_id'] = data['assignment_id']; o['stage'] = 'reserved'
    o['events'].append({**copy.deepcopy(event), 'execution_id': o['execution_id'], 'generation': event['generation'], 'sha256': hash_json(event), 'revision': task['revision'] + 1})
    validate(o)
    return o, writes



def reconcile_observations(o, observations, root):
    need(isinstance(observations, list), 'ORCH_RECOVERY_OWNER', 'Recovery needs exact native observations.')
    observed_ids = set()
    for item in observations:
        keys(item, ('assignment_id', 'receipt', 'changes'))
        aid = item['assignment_id']; need(aid in o['assignments'] and aid not in observed_ids, 'ORCH_RECOVERY_OWNER', 'Invalid recovery observation mapping.'); observed_ids.add(aid)
        a = o['assignments'][aid]; state = receipt(item['receipt'], subject=a['native_id']); evidence_list(item['changes'], root)
        need(state in ('completed', 'interrupted', 'failed'), 'ORCH_RECOVERY_OWNER', 'Every native owner must be confirmed stopped, completed or failed.')
        a['observations'].append({'receipt': item['receipt'], 'changes': item['changes']}); a['state'] = {'completed':'completed', 'interrupted':'stopped', 'failed':'failed'}[state]




def require_input_packet(o, a, task, root, folder):
    sid = a['subtask_id']; st = current_subtask(o, sid, task, root, folder)
    required = [{'path':str(folder.relative_to(root) / 'artifacts/orchestration' / ('baseline_' + st['digest'] + '.json')), 'sha256':st['digest']}]
    artifact_ids = []
    if a['function'] == 'reviewer':
        solver = next(x['solver_slot'] for x in st['baseline']['slots'] if x['slot'] == a['slot'])
        candidates = [c for c in o['candidates'].values() if o['assignments'][c['assignment_id']]['subtask_id'] == sid and o['assignments'][c['assignment_id']]['slot'] == solver and c['baseline'] == st['digest'] and c['round'] == st['round'] and not any(n['supersedes'] == c['candidate_id'] for n in o['candidates'].values())]
        need(len(candidates) == 1, 'ORCH_REVIEW_INPUT', 'Reviewer dispatch requires its own solver current candidate.')
        artifact_ids = [candidate_current(o, candidates[0]['candidate_id'], task, root, folder)['artifact_id']]
    elif a['function'] == 'senior':
        cids = candidate_set(o, sid, task, root, folder)
        artifact_ids = [o['candidates'][cid]['artifact_id'] for cid in cids]
        artifact_ids += [o['reviews'][rid]['findings'] for rid in review_set(o, sid, cids, root, folder)]
    elif a['function'] == 'implementer':
        syn = acceptance_current(o, a['acceptance_id'], task, root, folder)
        artifact_ids = [syn['artifact_id']]
    artifact_ids += [o['conflicts'][cid]['explanation'] for cid in st['active_conflicts']]
    for aid in artifact_ids:
        artifact = evidence_current(o, aid, folder)
        required.append({'path':str(folder.relative_to(root) / artifact['path']), 'sha256':artifact['sha256']})
    need(all(ref in a['context'] for ref in required), 'ORCH_INPUT_PACKET', 'Dispatch/input handoff is missing an exact current candidate, review, conflict or implementation artifact.')



def result_current(o, result, task, root, folder):
    a = o['assignments'][result['assignment_id']]
    st = current_subtask(o, a['subtask_id'], task, root, folder)
    need(result['baseline'] == st['digest'] and result['round'] == st['round'], 'ORCH_RESULT_BASELINE', 'Performed result is stale.')
    producer(o, result['assignment_id'])
    evidence_list(result['changes'], root, st['baseline']['implementation_required'])
    evidence_list(result['checks'], root, True)
    for aid in result['artifact_ids']: evidence_current(o, aid, folder)
    if result['acceptance_id']:
        need(result['acceptance_id'] == a['acceptance_id'], 'ORCH_IMPLEMENTATION_TARGET', 'Result target differs from the assigned accepted proposal.')
        acceptance_current(o, result['acceptance_id'], task, root, folder)
    return result


def event_records(o, kind, key, collection):
    return [o[collection][e['data'][key]] for e in o['events'] if e['kind'] == kind and e['execution_id'] == o['execution_id'] and e['generation'] == o['generation'] and e['data'][key] in o[collection]]


def acceptance_current(o, aid, task, root, folder):
    need(aid in o['acceptances'], 'ORCH_ACCEPTANCE', 'Missing acceptance.')
    accepted = o['acceptances'][aid]
    evidence_list(accepted['inspection'], root, True)
    syn = synthesis_current(o, accepted['synthesis_id'], task, root, folder)
    sid = o['assignments'][syn['assignment_id']]['subtask_id']
    current = [a for a in event_records(o, 'acceptance.record', 'acceptance_id', 'acceptances') if o['assignments'][o['syntheses'][a['synthesis_id']]['assignment_id']]['subtask_id'] == sid]
    need(current and current[-1]['acceptance_id'] == aid, 'ORCH_STALE_ACCEPTANCE', 'A newer manager acceptance supersedes this implementation target.')
    return syn


def verified_current(o, sid, task, root, folder):
    st = current_subtask(o, sid, task, root, folder)
    need(st['verified'] and st['verified'][-1]['baseline'] == st['digest'] and st['verified'][-1]['round'] == st['round'], 'ORCH_COMPLETION', 'Subtask verification is stale or absent.')
    verification = st['verified'][-1]
    evidence_list(verification['inspection'], root, True)
    for aid in verification['artifacts']: evidence_current(o, aid, folder)
    if verification['result_id'] is not None:
        current = [v for v in event_records(o, 'result.record', 'result_id', 'results') if o['assignments'][v['assignment_id']]['subtask_id'] == sid and v['baseline'] == st['digest'] and v['round'] == st['round']]
        need(current and current[-1]['result_id'] == verification['result_id'], 'ORCH_VERIFICATION_STALE', 'The current delivered result has not been directly verified.')
        result_current(o, current[-1], task, root, folder)
        if current[-1]['acceptance_id']: acceptance_current(o, current[-1]['acceptance_id'], task, root, folder)
    elif verification['acceptance_id']:
        acceptance_current(o, verification['acceptance_id'], task, root, folder)
    return verification


def criteria_cover(items, expected):
    need(isinstance(items, list), 'ORCH_CRITERIA', 'Criterion evidence must be a list.')
    for item in items: keys(item, ('criterion', 'evidence')); text(item['criterion']); text(item['evidence'])
    need(len(items) == len(expected) and {x['criterion'] for x in items} == set(expected), 'ORCH_CRITERIA', 'Evidence must cover every current criterion exactly once.')


def summary(o):
    if o['execution_id'] is None: return '\n## Orchestration\n\nEnabled; no execution or native identity assigned.\n'
    lines = ['\n## Orchestration\n', f"Execution: {o['execution_id']}; generation: {o['generation']}; stage: {o['stage']}.", f"Writer: {o['writer']}; manager assignment: {o['manager_id']}.", f"Subtasks: {len(o['subtasks'])}; artifacts: {len(o['artifacts'])}; accepted solutions: {len(o['acceptances'])}."]
    for aid, a in o['assignments'].items(): lines.append(f"- {aid}: {a['function']}, {a['state']}, native {a['native_id'] or 'unassigned'}.")
    if o['blockers']: lines.append('Blockers: ' + '; '.join(o['blockers']))
    return '\n'.join(lines) + '\n'
