"""Freeze the separate keyboard03 protocol with the unchanged native driver."""
from pathlib import Path
import ast
import hashlib
import json
import os
import stat

root = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
stage = Path('/private/tmp/explorer-qualification-native-keyboard-03')


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


previous = json.loads(read_regular(out / 'host-native-keyboard-02.json'))
source = json.loads(read_regular(out / 'stage-security-07.json'))['files']
prepared = []
for item in source:
    name = item['path']
    if name == 'host-security-runner.py' or name.endswith('/test_explorer_security.py'):
        continue
    raw = read_regular(root / name)
    assert row(name, raw) == item
    prepared.append((name, raw))
for name in ('host-native-at-driver.py', 'native-remaining-protocol-03.md'):
    prepared.append((name, read_regular(out / name)))
old_driver = Path(previous['staging_root']) / 'host-native-at-driver.py'
assert read_regular(old_driver) == dict(prepared)['host-native-at-driver.py']
ast.parse(dict(prepared)['host-native-at-driver.py'])
tools = previous['external_tools']
for tool in tools:
    actual = Path(tool['path']).resolve()
    assert str(actual) == tool['resolved']
    raw = read_regular(actual)
    assert hashlib.sha256(raw).hexdigest() == tool['sha256']
    assert len(raw) == tool['bytes']

job_path = out / 'host-native-keyboard-03.json'
copy_path = out / 'stage-native-keyboard-03.json'
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
    'command': [str(root / '.venv/bin/python'), '-I', '-B', str(stage / 'host-native-at-driver.py')],
    'staging_root': str(stage),
    'manifest': {'path': str(stage / 'inputs.json'), 'sha256': hashlib.sha256(manifest).hexdigest()},
    'inputs_count': len(rows),
    'external_tools': tools,
    'timeout_seconds': 900,
    'driver_lifetime_seconds': 850,
    'protocol': row(str(out / 'native-remaining-protocol-03.md'), dict(prepared)['native-remaining-protocol-03.md']),
    'source_writes': False,
    'intended_writes': [
        'Owned disposable explorer-http-* fixture/service and one owned Safari document; root temporarily changes only reviewed theme/zoom/motion/developer/viewport/Inspector/window preferences and positively restores each baseline.',
        'Close exact owned document and stop retained driver; collect receipt before final Safari running-state restoration and positive absence observation. Preserve unrelated tabs/windows.'
    ],
    'credentials': 'Bootstrap only in0600 per-instance file/process memory; no private URL, raw errors, cookies, storage, headers, trace, HAR or clipboard inspection.',
    'scenarios': [
        'Actual Light chosen-result/source focus/List Back; exact different root00001 to00000.',
        'Actual ordinary/reduced-motion transitions and original-setting restoration.',
        'Reviewed Safari Responsive Design Mode plus owned main-frame read-only Inspector measurements before any320CSS claim, scoped native surrounding content/control observations and exact restoration.'
    ],
    'gate': 'Manager review/release required; root alone operates host UI after clean native_ready. TASK021 is previously accepted. Each actual group outcome and restoration must be supplied separately; no speech/fullTASK022/WCAG/participant result from driver pass. No TASK023/024/025 execution.'
}
job_path.write_text(json.dumps(job, indent=2) + '\n')
for item in rows:
    assert row(item['path'], read_regular(stage / item['path'])) == item
print(json.dumps({'job': row(str(job_path), read_regular(job_path)),
                  'manifest': job['manifest'], 'protocol': job['protocol'],
                  'inputs_count': len(rows), 'external_tools': len(tools),
                  'unchanged_native_driver': True, 'host_execution': False}))
