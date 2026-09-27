"""Freeze one current short Safari Theme observation without executing it."""
from pathlib import Path
import ast
import hashlib
import json
import os
import stat

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
q = out.parent
stage = Path('/private/tmp/explorer-qualification-native-theme-01')


def read_regular(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read()
        after = os.fstat(fd)
        assert (before.st_ino, before.st_size, before.st_mtime_ns) == (
            after.st_ino, after.st_size, after.st_mtime_ns)
        return raw
    finally:
        os.close(fd)


def row(path, raw):
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


previous = json.loads(read_regular(q / 'host-native-keyboard-03.json'))
source = json.loads(read_regular(q / 'stage-security-08.json'))['files']
prepared = []
for item in source:
    name = item['path']
    if name == 'host-security-runner.py' or name.endswith('/test_explorer_security.py'):
        continue
    raw = read_regular(root / name)
    assert row(name, raw) == item
    prepared.append((name, raw))
for name in ('host-native-theme-driver.py', 'native-theme-protocol-01.md'):
    prepared.append((name, read_regular(out / name)))
ast.parse(dict(prepared)['host-native-theme-driver.py'])
tools = previous['external_tools']
for tool in tools:
    actual = Path(tool['path']).resolve()
    assert str(actual) == tool['resolved']
    raw = read_regular(actual)
    assert hashlib.sha256(raw).hexdigest() == tool['sha256']
    assert len(raw) == tool['bytes']

job_path = q / 'host-native-theme-01.json'
copy_path = q / 'stage-native-theme-01.json'
assert not stage.exists() and not job_path.exists() and not copy_path.exists()
stage.mkdir()
rows = []
for name, raw in prepared:
    target = stage / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append(row(name, raw))
manifest = (json.dumps({'files': rows}, indent=2) + '\n').encode()
(stage / 'inputs.json').write_bytes(manifest)
copy_path.write_bytes(manifest)
job = {
    'command': [str(root / '.venv/bin/python'), '-I', '-B', str(stage / 'host-native-theme-driver.py')],
    'staging_root': str(stage),
    'manifest': {'path': str(stage / 'inputs.json'), 'sha256': hashlib.sha256(manifest).hexdigest()},
    'inputs_count': len(rows),
    'external_tools': tools,
    'timeout_seconds': 180,
    'driver_lifetime_seconds': 120,
    'latest_stop_seconds': 90,
    'source_mapping': {name: str(out / name) for name in ('host-native-theme-driver.py', 'native-theme-protocol-01.md')},
    'protocol': row(str(out / 'native-theme-protocol-01.md'), dict(prepared)['native-theme-protocol-01.md']),
    'source_writes': False,
    'intended_writes': ['Owned disposable fixture/service and one owned Safari document. Only its Theme setting may change and must be restored. Preserve window dimensions, zoom, system/app settings and unrelated documents. Close owned document and obtain receipt before final Safari running-state restoration.'],
    'credentials': 'Bootstrap only in0600 per-instance file/process memory; no private URL, raw errors, cookies, storage, headers, trace, HAR or clipboard inspection.',
    'scenarios': ['One actual focused Theme control/menu/key/value observation with intermediate native state and exact restoration. No repeated blind sequence or other native walkthrough.'],
    'gate': 'TASK022 only after current TASK021 acceptance and exact manager review/release. Root alone operates native UI. Driver success proves owned lifecycle only; actual method-specific Theme outcome supplied separately. No speech/fullTASK022 or later-gate execution.'
}
job_path.write_text(json.dumps(job, indent=2) + '\n')
for item in rows:
    assert row(item['path'], read_regular(stage / item['path'])) == item
print(json.dumps({'job': row(str(job_path), read_regular(job_path)),
                  'manifest': job['manifest'], 'protocol': job['protocol'],
                  'inputs_count': len(rows), 'external_tools': len(tools),
                  'driver_change': '120-second lifetime and explicit stop-request reporting; same private-document and owned-cleanup mechanism', 'host_execution': False}))
