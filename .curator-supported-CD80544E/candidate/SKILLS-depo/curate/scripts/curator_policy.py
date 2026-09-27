"""Pure, bounded Curator policy inspection. No runtime imports or mutations."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

PERMISSIONS = frozenset(('analysis', 'documentation', 'technical', 'governance',
    'filesystem.read', 'filesystem.write', 'memory.publish', 'ontology.publish',
    'adoption', 'package-source', 'runtime.install', 'network', 'external-tool',
    'service', 'hook', 'commit', 'integration', 'push', 'merge', 'destruction',
    'cross-project', 'notification'))
MAX_BYTES = 250000


class PolicyError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def require(condition, code, message):
    if not condition:
        raise PolicyError(code, message)


def exact(value, fields):
    require(type(value) is dict and set(value) == set(fields), 'fields', 'Missing or unknown fields.')


def bounded(value, depth=0):
    require(depth <= 16, 'structure_limit', 'Nested structure exceeds limit.')
    if type(value) is str:
        require(len(value) <= 20000 and not any(ord(c) < 32 for c in value), 'text', 'Text is oversized or contains control characters.')
    elif type(value) in (dict, list):
        require(len(value) <= 500, 'structure_limit', 'Collection exceeds limit.')
        for item in (value.items() if type(value) is dict else enumerate(value)):
            if type(value) is dict:
                require(type(item[0]) is str, 'text', 'Object key must be text.')
                bounded(item[0], depth + 1)
            bounded(item[1], depth + 1)
    else:
        require(value is None or type(value) in (int, bool), 'type', 'Only integers, booleans, text, arrays, objects and null are supported.')


def decode(raw):
    require(len(raw) <= MAX_BYTES, 'structure_limit', 'Policy exceeds byte limit.')
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate_key', 'Duplicate JSON key.')
            out[key] = value
        return out
    try:
        result = json.loads(raw, object_pairs_hook=pairs)
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, PolicyError):
            raise
        raise PolicyError('malformed', 'Expected UTF-8 JSON-compatible YAML.') from exc
    bounded(result)
    return result


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(value):
    require(type(value) is str and re.fullmatch('[a-f0-9]{64}', value), 'digest', 'Expected SHA256.')


def text(value, nullable=False):
    require((nullable and value is None) or (type(value) is str and bool(value.strip())), 'text', 'Expected nonblank text.')


def texts(value):
    require(type(value) is list, 'type', 'Expected an array.')
    for item in value:
        text(item)
    require(len(value) == len(set(value)), 'duplicate', 'Duplicate selection.')


def moment(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.tzinfo is not None, 'timestamp', 'Timezone is required.')
        return result
    except (ValueError, TypeError, AttributeError) as exc:
        raise PolicyError('timestamp', 'Expected an ISO timestamp with timezone.') from exc


def validate_policy(document):
    bounded(document)
    exact(document, ('schema_version', 'module_id', 'module_version', 'project', 'branches',
        'controller', 'runtime', 'accepted_policy', 'entitlements', 'autonomous_write',
        'schedule', 'bounds', 'trusted_sources', 'tools', 'network', 'notifications',
        'service_installed', 'hook_installed', 'capabilities'))
    require(type(document['schema_version']) is int and document['schema_version'] == 1,
            'version', 'Unsupported configuration version.')
    require(document['module_id'] == 'project-curator' and document['module_version'] == '1.0.0',
            'version', 'Unsupported Curator module.')
    exact(document['project'], ('id', 'repository_id', 'coordination_root'))
    for value in document['project'].values():
        text(value, True)
    root = document['project']['coordination_root']
    require(root is None or Path(root).is_absolute(), 'root', 'Coordination root must be absolute.')
    exact(document['controller'], ('kind', 'charter'))
    require(document['controller']['kind'] in (None, 'curator', 'director'), 'controller', 'Unsupported controller.')
    charter = document['controller']['charter']
    if charter is not None:
        exact(charter, ('path', 'sha256')); text(charter['path']); sha(charter['sha256'])
    for name in ('branches', 'tools', 'network', 'capabilities'):
        texts(document[name])
    for name in ('autonomous_write', 'service_installed', 'hook_installed'):
        require(type(document[name]) is bool, 'type', 'Expected explicit boolean.')
    exact(document['schedule'], ('enabled', 'debounce_seconds', 'catch_up_seconds', 'dependency_cadence_seconds'))
    require(type(document['schedule']['enabled']) is bool, 'type', 'Expected schedule boolean.')
    exact(document['bounds'], ('model_calls', 'work_seconds', 'candidate_bytes', 'concurrent_agents'))
    for value in [*document['bounds'].values(), *[v for k, v in document['schedule'].items() if k != 'enabled']]:
        require(value is None or (type(value) is int and 0 <= value <= 2**31 - 1), 'bounds', 'Expected null or a finite nonnegative integer bound.')
    exact(document['notifications'], ('enabled', 'destinations'))
    require(type(document['notifications']['enabled']) is bool, 'type', 'Expected notification boolean.')
    texts(document['notifications']['destinations'])
    require(type(document['trusted_sources']) is list, 'type', 'Expected source array.')
    for ref in document['trusted_sources']:
        exact(ref, ('path', 'sha256')); text(ref['path']); sha(ref['sha256'])
    runtime = document['runtime']
    if runtime is not None:
        exact(runtime, ('backend', 'executable', 'sha256', 'schema_sha256', 'profile_sha256', 'model', 'effort'))
        require(runtime['backend'] == 'codex-app-server-v2', 'runtime_unsupported', 'Unsupported native backend.')
        for key in ('sha256', 'schema_sha256', 'profile_sha256'): sha(runtime[key])
        for key in ('executable', 'model', 'effort'): text(runtime[key])
        require(Path(runtime['executable']).is_absolute(), 'runtime', 'Runtime executable must be absolute.')
    accepted = document['accepted_policy']
    if accepted is not None:
        exact(accepted, ('id', 'edition', 'sha256', 'expires_at'))
        text(accepted['id']); text(accepted['edition']); sha(accepted['sha256']); moment(accepted['expires_at'])
    require(type(document['entitlements']) is list, 'type', 'Expected entitlement references.')
    for ref in document['entitlements']:
        exact(ref, ('id', 'sha256')); text(ref['id']); sha(ref['sha256'])
    return document


def load_policy(path):
    try:
        with Path(path).open('rb') as stream:
            return validate_policy(decode(stream.read(MAX_BYTES + 1)))
    except FileNotFoundError as exc:
        raise PolicyError('policy_unavailable', 'Selected policy is unavailable.') from exc


def decision(state, code, missing=(), observed=None, allowed=False):
    return {'state': state, 'code': code, 'missing': list(missing),
            'observed_bindings': observed or {}, 'allowed': allowed}


def inspect_policy(policy):
    validate_policy(policy)
    missing = [f'project.{k}' for k, v in policy['project'].items() if v is None]
    missing += [k for k in ('branches', 'runtime', 'accepted_policy', 'entitlements') if not policy[k]]
    missing += [f'controller.{k}' for k, v in policy['controller'].items() if v is None]
    missing += [f'bounds.{k}' for k, v in policy['bounds'].items() if v is None]
    return decision('installed_inactive' if missing else 'selected_unverified',
                    'selection_required' if missing else 'runtime_proof_required', missing)


def evaluate_operation(policy, accepted_entitlement, operation, observation, *, verification=False):
    """Issuer supplies previously verified entitlement data; candidate config never supplies authority."""
    try:
        current = inspect_policy(policy)
        if current['missing']: return current
        exact(operation, ('class', 'project_id', 'repository_id', 'coordination_root', 'branch',
            'paths', 'tools', 'network', 'payload_sha256', 'cost', 'automatic'))
        bounded(operation)
        require(type(operation['class']) is str and operation['class'] in PERMISSIONS, 'permission_unknown', 'Unsupported permission class.')
        sha(operation['payload_sha256'])
        for key in ('paths', 'tools', 'network'): texts(operation[key])
        exact(operation['cost'], policy['bounds'])
        require(type(operation['automatic']) is bool, 'type', 'Expected automatic boolean.')
        for key, value in operation['cost'].items():
            require(type(value) is int and 0 <= value <= policy['bounds'][key], 'bounds_exhausted', 'Operation exceeds selected bounds.')
        for key in ('id', 'repository_id', 'coordination_root'):
            require(operation['project_id' if key == 'id' else key] == policy['project'][key], 'project_mismatch', 'Operation names a different project.')
        require(operation['branch'] in policy['branches'], 'branch_mismatch', 'Branch is not selected.')
        require(type(observation) is dict and observation.get('root_available') is True and observation.get('runtime_available') is True,
                'runtime_unavailable', 'Selected root or native runtime is unavailable.')
        require((verification is True or observation.get('proof_current') is True) and observation.get('supported_bounds') == policy['bounds'],
                'runtime_proof_required', 'Current native/confinement evidence and supported bounds are required.')
        require(observation.get('policy_sha256') == digest(policy), 'policy_changed', 'Observed policy differs.')
        now = moment(observation['now'])
        require(now <= moment(policy['accepted_policy']['expires_at']), 'policy_expired', 'Accepted policy expired.')
        require(type(accepted_entitlement) is dict, 'entitlement_missing', 'Protected issuer has no accepted entitlement.')
        exact(accepted_entitlement, ('id', 'sha256', 'policy_sha256', 'project_id', 'repository_id',
            'coordination_root', 'branches', 'permissions', 'paths', 'tools', 'network', 'expires_at'))
        for key in ('branches','permissions','paths','tools','network'):
            texts(accepted_entitlement[key])
        require(set(accepted_entitlement['permissions']) <= PERMISSIONS, 'permission_unknown', 'Entitlement contains an unsupported permission.')
        for key in ('sha256','policy_sha256'): sha(accepted_entitlement[key])
        for key in ('id','project_id','repository_id','coordination_root'): text(accepted_entitlement[key])
        ref = {k: accepted_entitlement[k] for k in ('id', 'sha256')}
        require(ref in policy['entitlements'] and accepted_entitlement['policy_sha256'] == policy['accepted_policy']['sha256'],
                'entitlement_mismatch', 'Protected entitlement differs from accepted selection.')
        require(now <= moment(accepted_entitlement['expires_at']), 'entitlement_expired', 'Entitlement expired.')
        for key in ('project_id', 'repository_id', 'coordination_root'):
            require(accepted_entitlement[key] == operation[key], 'entitlement_scope', 'Entitlement project differs.')
        require(operation['branch'] in accepted_entitlement['branches'] and operation['class'] in accepted_entitlement['permissions'],
                'permission_denied', 'Operation is not independently entitled.')
        for key in ('tools', 'network'):
            require(set(operation[key]) <= set(policy[key]) & set(accepted_entitlement[key]), 'permission_denied', 'Tool/network selection is absent.')
        for path in operation['paths']:
            p = Path(path)
            require(not p.is_absolute() and '..' not in p.parts and bool(p.parts), 'path', 'Expected confined relative path.')
            require(any(path == scope or path.startswith(scope.rstrip('/') + '/') for scope in accepted_entitlement['paths']), 'entitlement_scope', 'Path is not entitled.')
        if operation['automatic'] and operation['class'] != 'analysis':
            require(policy['autonomous_write'], 'automatic_disabled', 'Automatic writing is disabled.')
        if operation['automatic'] and operation['class'] == 'memory.publish':
            require(observation.get('automatic_capture') is True, 'capture_disabled', 'Automatic memory capture is disabled.')
        return decision('allowed', 'authorized_disposable_verification' if verification else 'authorized',
                        observed={'policy_sha256': digest(policy), 'entitlement': ref,
                                  'admission': 'disposable_verification' if verification else 'production'}, allowed=True)
    except (PolicyError, KeyError) as exc:
        code = exc.code if isinstance(exc, PolicyError) else 'observation_missing'
        return decision('unavailable' if code.endswith('_unavailable') else 'blocked', code)
