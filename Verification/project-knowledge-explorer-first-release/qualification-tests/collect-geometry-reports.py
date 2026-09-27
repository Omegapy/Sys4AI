"""Retain exact root-produced geometry JSON and PNG bytes in bounded shards."""
from pathlib import Path
import base64, hashlib, json, os, re, stat, sys

ROOT = Path(__file__).resolve().parents[3]
Q = Path(__file__).resolve().parent
assert len(sys.argv) == 2 and re.fullmatch(r'actual-(geometry|visual)-[0-9]{2}(?:-failed)?', sys.argv[1])
kind = 'visual' if sys.argv[1].startswith('actual-visual-') else 'geometry'
folder = Q / sys.argv[1]
stdout = (folder / 'stdout.json').read_bytes()
report = json.loads(stdout)
destination = folder / (kind + '-raw-shards')
destination.mkdir()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def save(path, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(raw) <= 250000
    with path.open('xb') as stream:
        stream.write(raw)
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(raw), 'bytes': len(raw)}

def retain(index, kind, reference):
    path = Path(reference['path'])
    assert path.parent.parent == Path('/private/tmp')
    assert path.parent.name.startswith('explorer-a11y-evidence-')
    assert path.suffix == ('.json' if kind == 'raw_report' else '.png')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        start = os.fstat(stream.fileno())
        assert stat.S_ISREG(start.st_mode) and start.st_nlink == 1 and start.st_size <= 8000000
        raw = stream.read()
        end = os.fstat(stream.fileno())
        assert (start.st_ino, start.st_size, start.st_mtime_ns) == (end.st_ino, end.st_size, end.st_mtime_ns)
    assert len(raw) == reference['bytes'] and sha(raw) == reference['sha256']
    if kind == 'raw_report':
        parsed = json.loads(raw)
        assert parsed['name'] == scan['name'] and parsed['theme'] == scan['theme']
    else:
        assert raw.startswith(b'\x89PNG\r\n\x1a\n')
    shards, restored = [], bytearray()
    for offset in range(0, len(raw), 120000):
        part = raw[offset:offset + 120000]
        member = destination / f'{index:02d}-{kind}-{offset // 120000:03d}.json'
        shards.append(save(member, {'whole_sha256': sha(raw), 'offset': offset,
                                   'decoded_bytes': len(part), 'encoding': 'base64 of exact original bytes',
                                   'data': base64.b64encode(part).decode()}))
        restored.extend(base64.b64decode(json.loads(member.read_text())['data'], validate=True))
    assert bytes(restored) == raw
    return {'original_location': str(path), 'sha256': sha(raw), 'bytes': len(raw), 'lossless_shards': shards}

states = []
for index, scan in enumerate(report['scans']):
    states.append({'name': scan['name'], 'theme': scan['theme'],
                   'raw_report': retain(index, 'raw_report', scan['raw_report']),
                   'screenshot': retain(index, 'screenshot', scan['screenshot']),
                   'candidate_count': scan['candidate_count']})
assert len({(s['name'], s['theme']) for s in states}) == len(states)
if report['status'] == 'passed':
    assert len(states) == (6 if kind == 'visual' else 30) and report['manual_acceptance'] == 'pending review'
result = save(folder / (kind + '-complete-report-index.json'), {
    'status': 'all_observed_original_reports_and_screenshots_preserved_losslessly',
    'actual_executor': '/root', 'source_stdout_sha256': sha(stdout),
    'original_execution_status': report['status'], 'manual_acceptance': 'pending review',
    'states': states, 'evidence_cap_bytes': 250000,
    'reconstruction': 'For each member concatenate base64-decoded shards in offset order and verify whole SHA256. JSON and PNG bytes are exact; original root-produced files remain at the recorded paths. No finding or image bytes are discarded.'})
print(json.dumps(result))
