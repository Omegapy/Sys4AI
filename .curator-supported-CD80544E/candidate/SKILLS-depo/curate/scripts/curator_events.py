"""Bounded local delivery envelopes. Signals are data, never execution authority."""
from pathlib import PurePosixPath
import re

from curator_policy import bounded, canonical, digest, exact, moment, require, sha

MAX_EVENT_BYTES = 32768
KINDS = {'manual_correction', 'commit', 'accepted_work', 'catch_up', 'dependency_due', 'stale_product'}
PAYLOADS = {
    'manual_correction': ('request',),
    'commit': ('commit',),
    'accepted_work': ('completion', 'effect'),
    'catch_up': ('previous_commit', 'commit'),
    'dependency_due': ('check_id', 'due_at'),
    'stale_product': ('product_id', 'owner', 'input_sha256'),
}
CONTEXT_FIELDS = ('project_id', 'repository_id', 'coordination_root', 'branch', 'snapshot', 'policy_sha256', 'source_sha256')
EVENT_FIELDS = ('schema_version', 'event_id', 'operation_id', 'causal_parent', 'kind', 'created_at', *CONTEXT_FIELDS, 'sources', 'payload')


def identifier(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', value), 'identifier', 'Expected a bounded opaque identifier.')


def git_oid(value):
    require(type(value) is str and re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})', value), 'git_oid', 'Expected a complete object ID.')


def reference(value):
    exact(value, ('owner', 'path', 'sha256'))
    require(value['owner'] in ('project', 'task', 'memory', 'ontology', 'curate', 'setup'), 'owner', 'Unknown reference owner.')
    p = value['path']
    require(type(p) is str and 0 < len(p.encode()) <= 2048 and not any(ord(c) < 32 for c in p)
            and not PurePosixPath(p).is_absolute() and '..' not in PurePosixPath(p).parts
            and str(PurePosixPath(p)) == p and p != '.' and '\\' not in p, 'reference', 'Expected a bounded relative evidence path.')
    sha(value['sha256'])


def validate_context(value):
    exact(value, CONTEXT_FIELDS)
    for key in ('project_id', 'repository_id'): identifier(value[key])
    root = value['coordination_root']
    require(type(root) is str and root.startswith('/') and len(root.encode()) <= 4096
            and not any(ord(c) < 32 for c in root) and str(PurePosixPath(root)) == root
            and '..' not in PurePosixPath(root).parts, 'root', 'Expected an absolute canonical coordination root.')
    branch = value['branch']
    require(type(branch) is str and 0 < len(branch.encode()) <= 1024 and not any(ord(c) < 32 for c in branch), 'branch', 'Expected a selected branch identity.')
    for key in ('snapshot', 'policy_sha256', 'source_sha256'): sha(value[key])


def validate_event(event):
    bounded(event); exact(event, EVENT_FIELDS)
    require(type(event['schema_version']) is int and event['schema_version'] == 1, 'version', 'Unknown event version.')
    for key in ('event_id', 'operation_id'): identifier(event[key])
    if event['causal_parent'] is not None: identifier(event['causal_parent'])
    require(type(event['kind']) is str and event['kind'] in KINDS, 'event_kind', 'Unknown event kind.')
    moment(event['created_at']); validate_context({k: event[k] for k in CONTEXT_FIELDS})
    require(type(event['sources']) is list and len(event['sources']) <= 50, 'sources', 'Expected bounded source references.')
    for ref in event['sources']: reference(ref)
    require(len({digest(r) for r in event['sources']}) == len(event['sources']), 'sources', 'Duplicate source reference.')
    payload = event['payload']; exact(payload, PAYLOADS[event['kind']])
    kind = event['kind']
    if kind == 'manual_correction': reference(payload['request'])
    elif kind == 'commit': git_oid(payload['commit'])
    elif kind == 'accepted_work':
        reference(payload['completion'])
        require(payload['completion']['owner'] in ('task', 'project'), 'owner', 'Completion is an existing owner reference.')
        require(payload['effect'] in ('repair', 'documentation', 'knowledge', 'derivative'), 'effect', 'Unknown accepted effect.')
    elif kind == 'catch_up':
        if payload['previous_commit'] is not None: git_oid(payload['previous_commit'])
        git_oid(payload['commit'])
    elif kind == 'dependency_due': identifier(payload['check_id']); moment(payload['due_at'])
    elif kind == 'stale_product':
        identifier(payload['product_id']); sha(payload['input_sha256'])
        require(payload['owner'] in ('memory', 'ontology'), 'owner', 'Product requires its existing knowledge owner.')
    require(len(canonical(event)) <= MAX_EVENT_BYTES, 'event_limit', 'Event exceeds the bounded envelope.')
    return event


def make_event(context, kind, operation_id, payload, *, created_at, causal_parent=None, sources=()):
    """Human and agent commits deliberately use the identical envelope."""
    event = {'schema_version': 1, **context, 'operation_id': operation_id,
             'causal_parent': causal_parent, 'kind': kind, 'created_at': created_at,
             'sources': list(sources), 'payload': payload}
    event['event_id'] = 'evt-' + digest(event)
    return validate_event(event)


def commit_signal(context, commit, *, created_at):
    git_oid(commit)
    return make_event(context, 'commit', 'git-' + digest([context['repository_id'], context['branch'], commit]),
                      {'commit': commit}, created_at=created_at)


def catch_up_signal(context, previous_commit, commit, *, created_at):
    """One missed-hook signal binds endpoints; the bounded Git adapter computes changes."""
    if previous_commit == commit: return None
    return make_event(context, 'catch_up', 'catch-' + digest([context, previous_commit, commit]),
                      {'previous_commit': previous_commit, 'commit': commit}, created_at=created_at)
