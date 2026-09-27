"""Explicit project projection over independently authorized Task board contexts."""
from collaboration_delivery import transport_allowed
from collaboration_store import digest, encoded, rebuild, require


def overview(boards, *, search=None, offset=0, items=20):
    """A viewer needs a real assignment in every selected Task; roles grant no access."""
    require(isinstance(boards, (list, tuple)) and 1 <= len(boards) <= 20, 'COLLAB_BOUND')
    actor = boards[0].c.actor
    require(all(b.c.actor == actor and b.c.root == boards[0].c.root for b in boards), 'COLLAB_IDENTITY')
    require(type(offset) is int and offset >= 0 and type(items) is int and 1 <= items <= min(b.c.policy['bounds']['page_items'] for b in boards), 'COLLAB_BOUND')
    require(search is None or isinstance(search, str) and len(search) <= 200, 'COLLAB_FILTER')
    entries = []
    selected = []
    for board in boards:
        c = board.c; c.current()
        require(c.scope(c.task_path), 'COLLAB_SCOPE')
        task_ref = {'path': c.task_path, 'sha256': c.task_sha256}
        selected.append({'task': c.task['task_id'], 'source': task_ref, 'policy': c.policy_ref,
                         'assignment': c.assignment, 'actor': c.actor, 'role': c.a['role']['name'],
                         'status': c.task['status'], 'execution_stage': c.o['stage']})
        visible = [x for x in board.messages() if transport_allowed(board, x['message'])]
        receipts = board.receipts(visible)
        for item in visible:
            m = item['message']
            kind = {'blocker': 'blocker', 'question': 'decision-request', 'help-request': 'decision-request',
                    'change-notice': 'concern', 'challenge': 'concern', 'finding': 'concern',
                    'proposal': 'maintenance-proposal'}.get(m['type'])
            if kind is None: continue
            if search is not None and search.casefold() not in (m['title'] + '\n' + m['body']).casefold(): continue
            states = sorted({r['receipt']['state'] for r in receipts if r['receipt']['message_id'] == m['message_id']})
            entries.append({'kind': kind, 'title': m['title'], 'message_id': m['message_id'],
                            'source': item['source'], 'task_source': task_ref, 'task': c.task['task_id'],
                            'status': c.task['status'], 'execution_stage': c.o['stage'],
                            'viewer_assignment': c.assignment, 'subtask': m['subtask'],
                            'communication_states': states,
                            'communication_unresolved': not any(s in states for s in ('answered', 'handled')),
                            'completion_source': 'canonical-task',
                            'limit': 'Communication handling does not establish semantic resolution or Task acceptance.'})
        c.current()
    entries.sort(key=lambda x: (x['task'], x['message_id']))
    cap = min(b.c.policy['bounds']['output_bytes'] for b in boards)
    result = {'version': 1, 'selected_tasks': selected, 'entries': [], 'total': len(entries),
              'returned': 0, 'remaining': max(0, len(entries) - offset), 'offset': offset,
              'checkpoint': digest(encoded(entries)), 'derived': True,
              'coverage': 'Selected authorized Tasks and eligible visible concerns only; no hidden or unselected counts.'}
    require(len(encoded(result)) <= cap, 'COLLAB_SIZE')
    for item in entries[offset:offset + items]:
        trial = {**result, 'entries': result['entries'] + [item], 'returned': result['returned'] + 1,
                 'remaining': len(entries) - offset - result['returned'] - 1}
        if len(encoded(trial)) > cap: break
        result = trial
    if not result['returned'] and entries[offset:]: result['next_item_exceeds_output'] = True
    return result


def rebuild_overview(boards, **filters):
    """Write only the active viewer's own derived view; never cache broader grants."""
    result = overview(boards, **filters)
    c = boards[0].c; raw = c.namespace + '/views/PROJECT-BILLBOARD.json'
    c.writable(raw)
    rebuild(c.root, raw, encoded(result) + b'\n', c.policy['bounds']['output_bytes'])
    return {'path': raw, 'derived': True, 'returned': result['returned'], 'remaining': result['remaining'],
            'source_checkpoint': result['checkpoint']}
