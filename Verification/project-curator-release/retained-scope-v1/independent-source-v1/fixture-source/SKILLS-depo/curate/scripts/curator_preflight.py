"""Pure relevance and due checks. Decisions neither invoke models nor grant writes."""
from fnmatch import fnmatchcase

from curator_classification import classify_target, relative
from curator_events import validate_event
from curator_policy import digest, exact, moment, require

IGNORED_PREFIXES = ('.sys4ai/curator/', 'control_records/curator/')
COUNTERS = {'model_calls': 0, 'task_writes': 0, 'knowledge_writes': 0, 'content_writes': 0}


def coalesce(events):
    """Stable order and causal identity survive duplicate/reordered deliveries."""
    require(type(events) in (list, tuple) and len(events) <= 5000, 'event_limit', 'Too many events for one preflight.')
    seen_ids = {}; logical = {}
    for event in events:
        validate_event(event)
        key = event['event_id']; value = digest(event)
        require(key not in seen_ids or seen_ids[key] == value, 'event_conflict', 'Same event ID differs.')
        seen_ids[key] = value
        identity = digest({k: v for k, v in event.items() if k not in ('event_id', 'created_at')})
        if identity not in logical or event['event_id'] < logical[identity]['event_id']: logical[identity] = event
    return [logical[key] for key in sorted(logical)]


def preflight(context, *, events=(), deltas=(), ownership, snapshot, relevant_paths, due_checks=(), now,
              pending=False, root_available=True, runtime_available=True, owner_available=True,
              recovery_pending=False, policy_current=True):
    from curator_events import validate_context
    validate_context(context); moment(now)
    require(type(deltas) in (list, tuple) and len(deltas) <= 500 and len(due_checks) <= 500 and len(relevant_paths) <= 500,
            'preflight_limit', 'Preflight collections exceed their bounds.')
    require(type(snapshot) is dict and len(snapshot) <= 500 and all(type(v) is bytes for v in snapshot.values())
            and sum(len(v) for v in snapshot.values()) <= 8000000, 'snapshot_limit', 'Bounded exact source bytes are required.')
    require(all(type(x) is bool for x in (pending, root_available, runtime_available, owner_available, recovery_pending, policy_current)),
            'preflight_input', 'Availability and pending inputs must be explicit booleans.')
    result = {'state': 'idle', 'reasons': [], 'routes': [], 'event_ids': [], 'counters': dict(COUNTERS)}
    if not root_available:
        return {**result, 'state': 'unavailable', 'reasons': ['root_unavailable']}
    if not policy_current or recovery_pending or not owner_available:
        return {**result, 'state': 'held', 'reasons': ['policy_changed' if not policy_current else 'recovery_pending' if recovery_pending else 'owner_unavailable']}
    reasons = []; routes = set(); holds = []
    for pattern in relevant_paths: relative(pattern)
    for event in coalesce(events):
        if any(event[k] != context[k] for k in ('project_id', 'repository_id', 'coordination_root', 'branch')):
            holds.append('event_scope'); continue
        if any(event[k] != context[k] for k in ('snapshot', 'policy_sha256', 'source_sha256')):
            holds.append('event_stale'); continue
        if event['kind'] == 'dependency_due' and moment(event['payload']['due_at']) > moment(now): continue
        result['event_ids'].append(event['event_id'])
        if event['kind'] not in ('commit', 'catch_up'): reasons.append(event['kind'])
        if event['kind'] == 'stale_product': routes.add(event['payload']['owner'] + '.maintenance')
    for delta in deltas:
        exact(delta, ('identity', 'ranges'))
        path = delta['identity']['path']; relative(path)
        if path.startswith(IGNORED_PREFIXES): continue
        if not any(fnmatchcase(path, pattern) for pattern in relevant_paths): continue
        classification = classify_target(ownership, delta['identity'], delta['ranges'], snapshot)
        if classification['state'] != 'classified': holds.append(classification['code']); continue
        reasons.append('relevant_delta'); routes.add(classification['route'])
    for check in due_checks:
        exact(check, ('id', 'due_at', 'enabled'))
        require(type(check['enabled']) is bool, 'due_check', 'Due-check selection must be explicit.')
        if check['enabled'] and moment(check['due_at']) <= moment(now): reasons.append('dependency_due')
    if pending: reasons.append('pending_work')
    result.update(reasons=sorted(set(reasons + holds)), routes=sorted(routes))
    if holds: result['state'] = 'held'
    elif reasons: result['state'] = 'ready' if runtime_available else 'unavailable'
    if reasons and not runtime_available: result['reasons'].append('runtime_unavailable')
    return result
