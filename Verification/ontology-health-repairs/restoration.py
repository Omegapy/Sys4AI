"""Exact reviewed historical dispositions and existing-backend maintenance."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / '.agents/skills/memory/scripts'))
from memory_core import json_bytes, sha256, parse_record, validate_record


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def grant(observation, operation, payload, scope, reviewed=()):
    now = datetime.fromisoformat(observation['observed_at'])
    assert 0 <= (datetime.now(timezone.utc) - now).total_seconds() < 240
    return {'schema_version': 1, 'grant_id': 'health-repair-' + operation + '-' + now.isoformat(),
            'project_id': 'sys4ai-depot', 'actor_id': '/root', 'actor_kind': 'director',
            'operation': operation, 'payload_sha256': sha256(json_bytes(payload)),
            'config_sha256': sha256((ROOT / 'memory.yaml').read_bytes()),
            'scope': list(scope), 'native_receipt': observation['native_receipt'],
            'observed_at': now.isoformat(), 'expires_at': (now + timedelta(seconds=300)).isoformat(),
            'task': None, 'reviewed_records': list(reviewed), 'privacy_redaction': False}


def dispositions(observation):
    from memory_recovery import atomic_replace
    from memory_publish import publish
    for stem in ('historical', 'lexical'):
        companion_file = OUT / 'memory' / (stem + '-proof-companion.json')
        companion_raw = companion_file.read_bytes()
        companion = json.loads(companion_raw)
        receipt = companion['receipt']
        assert sha256((ROOT / receipt['path']).read_bytes()) == receipt['sha256']
        for ref in companion['artifacts']:
            assert sha256((ROOT / ref['retained_path']).read_bytes()) == ref['sha256']
        destination = 'Verification/project-memory/evidence/verification-' + receipt['sha256'] + '.json'
        target = ROOT / destination
        assert not target.exists(), destination
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_replace(ROOT, destination, companion_raw, None)
        assert target.read_bytes() == companion_raw
        payload = json.loads((OUT / 'memory' / (stem + '-supersession-payload.json')).read_text())
        for change in payload['changes']:
            assert sha256(change['content']) == change['reviewed_record_sha256']
            validate_record(parse_record(change['content']), 'sys4ai-depot')
            path = ROOT / change['path']
            assert (sha256(path.read_bytes()) if path.exists() else None) == change['expected_sha256']
        reviewed = [{'path': c['path'], 'sha256': c['reviewed_record_sha256'],
                     'expected_sha256': c['expected_sha256']} for c in payload['changes']]
        auth = grant(observation, 'supersede', payload, ['MEMORY'], reviewed)
        grant_path = 'Verification/ontology-health-repairs/memory/' + stem + '-grant.json'
        save(ROOT / grant_path, auth)
        result = publish(ROOT, payload, grant_path, '/root')
        save(OUT / 'memory' / (stem + '-publication-receipt.json'), result)
        assert result['state'] == 'complete', result
        for change in payload['changes']:
            assert sha256((ROOT / change['path']).read_bytes()) == change['reviewed_record_sha256']
        print(json.dumps({'disposition': stem, 'state': result['state'], 'records': len(reviewed)}), flush=True)


def reindex(observation):
    from memory_maintenance import reindex_payload, reindex
    from basic_memory_projection import canonical_json
    payload = reindex_payload(ROOT)
    save(OUT / 'memory' / 'root-reindex-payload.json', payload)
    auth = grant(observation, 'reindex', payload, payload['paths'])
    auth['payload_sha256'] = sha256(canonical_json(payload))
    grant_path = 'Verification/ontology-health-repairs/memory/root-reindex-grant.json'
    save(ROOT / grant_path, auth)
    result = reindex(ROOT, grant_file=grant_path, actor='/root', expected_payload_sha256=auth['payload_sha256'])
    save(OUT / 'memory' / 'root-reindex-receipt.json', result)
    print(json.dumps(result), flush=True)
    assert result.get('ready') is True, result


if __name__ == '__main__':
    observation = json.loads(Path(sys.argv[2]).read_text())
    {'dispositions': dispositions, 'reindex': reindex}[sys.argv[1]](observation)
