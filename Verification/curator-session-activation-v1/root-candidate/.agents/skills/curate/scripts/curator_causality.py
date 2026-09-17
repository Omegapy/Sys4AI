"""Deterministic obligation identities, owner-evidence reduction and finite stopping."""
from curator_events import CONTEXT_FIELDS, identifier, reference, validate_event
from curator_policy import bounded, digest, exact, require, sha

OBLIGATIONS = ('assessment', 'repair', 'documentation', 'knowledge', 'derivative')
OUTCOME_FIELDS = ('key', 'attempt', 'status', 'input_sha256', 'output_sha256', 'finding_sha256',
                  'reference', 'elapsed_ms', 'bytes')


def obligation_key(event, obligation):
    validate_event(event)
    require(obligation in OBLIGATIONS, 'obligation', 'Unknown obligation.')
    return digest([event['operation_id'], {k: event[k] for k in CONTEXT_FIELDS if k != 'snapshot'}, obligation])


def obligations_for(event):
    """A completed repair still receives documentation and knowledge assessment."""
    validate_event(event)
    if event['kind'] == 'stale_product': names = ['derivative']
    elif event['kind'] == 'accepted_work':
        effect = event['payload']['effect']
        names = ['documentation', 'knowledge'] if effect == 'repair' else ['derivative'] if effect == 'knowledge' else [] if effect == 'derivative' else ['knowledge']
    else: names = ['assessment']
    return [{'key': obligation_key(event, name), 'obligation': name} for name in names]


def validate_outcome(value):
    bounded(value); exact(value, OUTCOME_FIELDS)
    sha(value['key']); sha(value['input_sha256'])
    for key in ('output_sha256', 'finding_sha256'):
        if value[key] is not None: sha(value[key])
    for key in ('attempt', 'elapsed_ms', 'bytes'):
        require(type(value[key]) is int and 0 <= value[key] <= 2**31 - 1, 'outcome_bound', 'Expected finite measured counts.')
    require(value['attempt'] > 0, 'outcome_attempt', 'Attempt numbering starts at one.')
    require(value['status'] in ('satisfied', 'failed', 'held'), 'outcome_status', 'Unknown observed outcome.')
    if value['reference'] is not None: reference(value['reference'])
    require(value['status'] != 'satisfied' or (value['reference'] is not None and value['output_sha256'] is not None),
            'outcome_evidence', 'Satisfied effect requires an exact owner reference and output hash.')
    require(value['status'] == 'satisfied' or value['finding_sha256'] is not None, 'outcome_finding', 'Unresolved outcomes retain the finding identity.')
    return value


def reduce_outcomes(outcomes):
    """Out-of-order input yields the same result; conflicting retries remain held."""
    require(type(outcomes) is list and len(outcomes) <= 5000, 'outcome_limit', 'Outcome input exceeds the selected bound.')
    attempts = {}; conflicts = set()
    for value in outcomes:
        validate_outcome(value)
        identity = value['key'], value['attempt']
        variants = attempts.setdefault(identity, {})
        variants[digest(value)] = value
        if len(variants) > 1: conflicts.add(value['key'])
    grouped = {}
    for (key, _), variants in sorted(attempts.items()):
        grouped.setdefault(key, []).extend(variants.values())
    result = {}
    for key, values in sorted(grouped.items()):
        satisfied = [v for v in values if v['status'] == 'satisfied']
        outputs = {v['output_sha256'] for v in satisfied}
        input_versions = sorted({v['input_sha256'] for v in values})
        input_conflict = len(input_versions) > 1
        if len(outputs) > 1 or input_conflict: conflicts.add(key)
        state = 'held' if key in conflicts else 'satisfied' if satisfied else 'pending'
        result[key] = {'state': state, 'conflict': key in conflicts,
                       'input_versions': input_versions, 'input_conflict': input_conflict,
                       'attempts': sorted(values, key=lambda v: (v['attempt'], digest(v))),
                       'output_sha256': next(iter(outputs)) if len(outputs) == 1 and key not in conflicts else None}
    return result


def stopping_decision(key, outcomes, limits):
    sha(key); exact(limits, ('attempts', 'elapsed_ms', 'bytes'))
    for value in limits.values():
        require(type(value) is int and 0 <= value <= 2**31 - 1, 'limit', 'Select finite nonnegative stopping bounds.')
    item = reduce_outcomes(outcomes).get(key, {'state': 'pending', 'conflict': False, 'input_conflict': False, 'attempts': [], 'output_sha256': None})
    rows = item['attempts']; reasons = []
    if item['state'] == 'satisfied': reasons.append('satisfied')
    if item['conflict']: reasons.append('conflicting_outcomes')
    if item['input_conflict']: reasons.append('mixed_input_versions')
    if len({row['attempt'] for row in rows}) >= limits['attempts']: reasons.append('attempt_limit')
    if sum(row['elapsed_ms'] for row in rows) >= limits['elapsed_ms']: reasons.append('time_limit')
    if sum(row['bytes'] for row in rows) >= limits['bytes']: reasons.append('byte_limit')
    for before, after in zip(rows, rows[1:]):
        if before['input_sha256'] == after['input_sha256']:
            if before['status'] != 'satisfied' and after['status'] != 'satisfied' and before['finding_sha256'] == after['finding_sha256']:
                reasons.append('unchanged_failure')
            if before['output_sha256'] is not None and before['output_sha256'] == after['output_sha256']:
                reasons.append('unchanged_output')
    return {'key': key, 'state': item['state'], 'stop': bool(reasons), 'reasons': sorted(set(reasons)),
            'unresolved_findings': sorted({row['finding_sha256'] for row in rows if row['finding_sha256'] is not None})
                                  if item['state'] != 'satisfied' else [],
            'output_sha256': item['output_sha256']}
