"""Pure branch-bound checkpoint transitions and explicit reconciliation obligations."""
from copy import deepcopy

from curator_events import CONTEXT_FIELDS, reference, validate_context
from curator_policy import bounded, digest, exact, require, sha

STAGES = ('observed', 'assessed', 'integrated', 'reconciled')


def empty_checkpoint(context):
    validate_context(context)
    return {'schema_version': 1, 'project_id': context['project_id'], 'repository_id': context['repository_id'],
            'coordination_root': context['coordination_root'], 'branch': context['branch'],
            'observed': None, 'assessed': None, 'integrated': None, 'reconciled': None}


def validate_checkpoint(value):
    bounded(value)
    exact(value, ('schema_version', 'project_id', 'repository_id', 'coordination_root', 'branch', *STAGES))
    require(type(value['schema_version']) is int and value['schema_version'] == 1, 'version', 'Unsupported checkpoint.')
    validate_context({**{k: value[k] for k in CONTEXT_FIELDS if k in value},
                      'snapshot': '0' * 64, 'policy_sha256': '0' * 64, 'source_sha256': '0' * 64})
    for stage in STAGES:
        record = value[stage]
        if record is None: continue
        exact(record, ('context', 'evidence', 'obligations', 'predecessor_sha256'))
        if stage == 'observed':
            require(record['predecessor_sha256'] is None, 'checkpoint_predecessor', 'Observation has no predecessor.')
        else: sha(record['predecessor_sha256'])
        validate_context(record['context'])
        require(all(record['context'][key] == value[key] for key in ('project_id', 'repository_id', 'coordination_root', 'branch')),
                'checkpoint_scope', 'Checkpoint context crossed a branch or project.')
        require(type(record['evidence']) is list and len(record['evidence']) <= 50, 'checkpoint_evidence', 'Expected bounded evidence.')
        for ref in record['evidence']: reference(ref)
        require(type(record['obligations']) is list and len(record['obligations']) <= 100, 'obligations', 'Expected bounded obligation identities.')
        for item in record['obligations']: sha(item)
        require(len(set(record['obligations'])) == len(record['obligations']), 'obligations', 'Duplicate obligation.')
        require(stage == 'observed' or record['evidence'], 'checkpoint_evidence', 'Owner/assessment evidence must be supplied.')
    return value



def current_stages(checkpoint):
    """Validate current applicability without deleting stale historical records."""
    validate_checkpoint(checkpoint)
    current = {}; previous = None
    for stage in STAGES:
        record = checkpoint[stage]
        if stage == 'observed':
            current[stage] = record is not None
        else:
            predecessor = STAGES[STAGES.index(stage) - 1]
            current[stage] = bool(current[predecessor] and record is not None
                                  and record['context'] == previous['context']
                                  and record['predecessor_sha256'] == digest(previous)
                                  and set(previous['obligations']) <= set(record['obligations']))
        previous = record
    return current


def advance_checkpoint(checkpoint, stage, context, *, evidence=(), obligations=(), satisfied=()):
    """Owner refs are supplied observations, not independently verified publication.

    This pure transition is admitted only by the selected owner/broker integration.
    It never calls a publisher or equates assessment with integration.
    """
    validate_checkpoint(checkpoint); validate_context(context)
    require(stage in STAGES, 'checkpoint_stage', 'Unknown checkpoint stage.')
    require(all(checkpoint[k] == context[k] for k in ('project_id', 'repository_id', 'coordination_root', 'branch')),
            'checkpoint_scope', 'Checkpoint is bound to another branch or project.')
    previous = None
    if stage != 'observed':
        predecessor = STAGES[STAGES.index(stage) - 1]
        require(current_stages(checkpoint)[predecessor], 'checkpoint_stale', 'The preceding checkpoint record is stale.')
        previous = checkpoint[predecessor]
        require(previous is not None and previous['context'] == context, 'checkpoint_stale', 'The preceding stage does not bind these exact inputs.')
        require(checkpoint['observed']['context'] == context, 'checkpoint_stale', 'Source changed after assessment.')
        require(set(previous['obligations']) <= set(obligations), 'obligations_changed', 'A stage cannot drop preceding obligations.')
    if stage == 'reconciled':
        required = set(checkpoint['integrated']['obligations'])
        require(set(satisfied) == required, 'reconciliation_pending', 'Every required obligation needs an owner observation.')
        require(set(obligations) == required, 'obligations_changed', 'Reconciliation cannot drop integrated obligations.')
    candidate = deepcopy(checkpoint)
    candidate[stage] = {'context': deepcopy(context), 'evidence': deepcopy(list(evidence)), 'obligations': list(obligations),
                        'predecessor_sha256': None if previous is None else digest(previous)}
    validate_checkpoint(candidate)
    return candidate


def recompute_obligations(previous, current, *, ancestor=None, changes=(), root_available=True):
    """Git supplies actual ancestry and NUL-safe changed paths; no ancestry guessing."""
    if not root_available:
        return {'state': 'unavailable', 'obligations': [], 'reason': 'root_unavailable', 'retain_previous': True}
    validate_context(current['context'])
    if previous is not None: validate_context(previous['context'])
    kinds = []
    if previous is None: kinds.append('initial_snapshot')
    elif any(previous['context'][k] != current['context'][k] for k in ('project_id', 'repository_id', 'coordination_root')):
        return {'state': 'held', 'obligations': [], 'reason': 'identity_changed', 'retain_previous': True}
    else:
        if previous['context']['branch'] != current['context']['branch']: kinds.append('branch_switch')
        if previous['commit'] != current['commit']:
            require(type(ancestor) is bool, 'ancestry_unknown', 'Actual Git ancestry evidence is required.')
            kinds.append('forward_history' if ancestor else 'rewritten_history')
        if previous['context']['snapshot'] != current['context']['snapshot']: kinds.append('source_changed')
        if previous['context']['policy_sha256'] != current['context']['policy_sha256']: kinds.append('policy_changed')
    for change in changes:
        code = change['status'][0]
        if code in 'RC': kinds.append('rename' if code == 'R' else 'copy')
        elif code == 'D': kinds.append('deletion')
        else: kinds.append('content_change')
    # A rewrite may preserve the tree but still invalidate ancestry-bound evidence.
    obligations = [{'id': digest([current['context'], kind, list(changes)]), 'kind': kind,
                    'branch': current['context']['branch'], 'snapshot': current['context']['snapshot']}
                   for kind in sorted(set(kinds))]
    return {'state': 'pending' if obligations else 'idle', 'obligations': obligations,
            'reason': 'recompute' if obligations else 'unchanged', 'retain_previous': True}
