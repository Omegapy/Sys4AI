"""Preserve the one actual root scanner16 run without executing a browser."""
import base64
import hashlib
import json
import os
from pathlib import Path
import stat

O = Path(__file__).resolve().parent
ROOT = O.parents[3]
SOURCE = Path('/private/tmp/explorer-task022-host-ezsz8iud')
OUT = O / 'actual-accessibility-16'


def read(p):
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        a = os.fstat(fd)
        assert stat.S_ISREG(a.st_mode) and a.st_nlink == 1
        with os.fdopen(fd, 'rb', closefd=False) as f:
            data = f.read()
        z = os.fstat(fd)
        assert (a.st_ino, a.st_size, a.st_mtime_ns, a.st_ctime_ns) == (z.st_ino, z.st_size, z.st_mtime_ns, z.st_ctime_ns)
        return data
    finally:
        os.close(fd)


def ref(p):
    p = Path(p)
    data = read(p)
    return {'path': str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def put(p, value):
    data = (json.dumps(value, indent=2) + '\n').encode()
    assert len(data) < 250000
    p.write_bytes(data)
    return ref(p)


def preserve(data, prefix):
    parts = []
    for i, offset in enumerate(range(0, len(data), 160000)):
        part = data[offset:offset + 160000]
        parts.append(put(OUT / 'raw-shards' / f'{prefix}-{i:03}.json', {'encoding': 'base64', 'offset': offset, 'decoded_bytes': len(part), 'data': base64.b64encode(part).decode()}))
    rebuilt = b''.join(base64.b64decode(json.loads(read(ROOT / p['path']))['data']) for p in parts)
    assert rebuilt == data
    return parts


assert not OUT.exists()
for name, expected in [('receipt.json', '88ce594f2074a111aaa844c76ea0102b76be2395e855671971cded6eab616190'), ('stdout.json', 'f0df16af8d3957a905a6bef8f933facf163611ed66438216b9f606d9d547a78f'), ('raw-index.json', '00cbf29b771f4492e2dd3724eddc756b753e6ef976e5447c23b21faac17da327')]:
    assert ref(SOURCE / name)['sha256'] == expected
report = json.loads(read(SOURCE / 'stdout.json'))
receipt = json.loads(read(SOURCE / 'receipt.json'))
job = json.loads(read(SOURCE / 'reviewed-job.json'))
assert report['status'] == receipt['status'] == 'passed'
assert report['scan_execution_complete'] and len(report['scans']) == 70
assert report['violation_nodes'] == 0 and report['incomplete_nodes'] == 336
assert report['async_failures'] == [] and len(report['narrow_checks']) == 8
assert receipt['post_verification_errors'] == [] and receipt['stderr_bytes'] == 0
members = json.loads(read(job['manifest']['path']))['files']
assert len(members) == 110
for member in members:
    for stage in [Path(job['staging_root']), Path(receipt['execution_stage'])]:
        actual = ref(stage / member['path'])
        assert actual['sha256'] == member['sha256'] and actual['bytes'] == member['bytes']
OUT.mkdir()
(OUT / 'raw-shards').mkdir()
(OUT / 'states').mkdir()
names = ['host-wrapper.py', 'reviewed-release.json', 'reviewed-job.json', 'raw-index.json', 'admission.json', 'receipt.json']
for name in names:
    data = read(SOURCE / name)
    assert len(data) < 250000
    (OUT / name).write_bytes(data)
stdout_index = put(OUT / 'stdout-index.json', {'encoding': 'lossless_base64_chunks', 'original': ref(SOURCE / 'stdout.json'), 'parts': preserve(read(SOURCE / 'stdout.json'), 'stdout'), 'qualification': 'Exact291972-byte root stdout preserved without truncation; registered references use this bounded index and parts.'})
rows = []
for i, scan in enumerate(report['scans']):
    original = scan['raw_report']
    data = read(original['path'])
    assert len(data) == original['bytes'] and hashlib.sha256(data).hexdigest() == original['sha256']
    parsed = json.loads(data)
    assert parsed['testEngine']['version'] == '4.13.0'
    rows.append({'name': scan['name'], 'theme': scan['theme'], 'compact_report': put(OUT / 'states' / f'{i:02}.json', scan), 'original': original, 'parts': preserve(data, f'{i:02}')})
raw_index = put(OUT / 'raw-shard-index.json', {'status': 'all70_original_reports_losslessly_preserved', 'rows': rows, 'raw_bytes': sum(s['original']['bytes'] for s in rows), 'qualification': 'Every violation, incomplete node, target candidate and full axe result retained. Execution pass does not resolve336 incomplete nodes or454 sub24px candidates.'})
summary = {k: v for k, v in report.items() if k != 'scans'}
summary.update(scans_count=70, scans_index=raw_index, raw_stdout=stdout_index, targets_below24=sum(len(s['targets_below24']) for s in report['scans']), qualification='Derived compact current scanner16 observation summary. Full exact root stdout and70 raw reports preserved through lossless bounded indexes. No native speech, target-exception adjudication or WCAG acceptance.')
summary_ref = put(OUT / 'observation-summary.json', summary)
attribution = put(OUT / 'attribution.json', {'status': 'all70_state_execution_passed_manual_adjudication_pending', 'actual_executor': '/root', 'root_source': str(SOURCE), 'references': [ref(OUT / name) for name in names], 'stdout': stdout_index, 'raw_reports': raw_index, 'summary': summary_ref, 'build_id': 'c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a', 'original_captured110_members_reverified': True, 'violations': 0, 'incomplete_nodes': 336, 'sub24px_candidates': 454, 'qualification': 'Only automated execution complete. Original14/15 failures remain; safe native document-focus departure classification is test-only. Actual geometry/contrast/target review and native speech remain separate.'})
print(json.dumps({'attribution': attribution, 'stdout': stdout_index, 'raw_index': raw_index, 'summary': summary_ref, 'raw_bytes': sum(s['original']['bytes'] for s in rows)}))
