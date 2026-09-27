"""Freeze current malicious-text checks with the admitted headless runtime."""
from pathlib import Path
import hashlib, json, os, stat

out = Path(__file__).resolve().parent
q = out.parent
root = q.parents[2]
stage = Path('/private/tmp/explorer-qualification-security-browser-03')

def read(p):
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        a = os.fstat(fd)
        assert stat.S_ISREG(a.st_mode) and a.st_nlink == 1
        with os.fdopen(fd, 'rb', closefd=False) as f:
            b = f.read()
        z = os.fstat(fd)
        assert (a.st_ino, a.st_size, a.st_mtime_ns) == (z.st_ino, z.st_size, z.st_mtime_ns)
        return b
    finally:
        os.close(fd)

def row(p, b):
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

pin_path = root / 'Verification/project-knowledge-explorer-first-release/service-tests/service-v4/tool-pins.json'
pins = json.loads(read(pin_path))
assert hashlib.sha256(read(pin_path)).hexdigest() == '7099d9b64f22b897f4c9981fc768f18bd4194b4ec2ae999822a009c3a7853ae2'
runtime = pins['headless_runtime']
for item in pins['external_tools']:
    actual = Path(item['path']).resolve()
    assert str(actual) == item['resolved']
    value = row(item['path'], read(actual))
    assert value['sha256'] == item['sha256'] and value['bytes'] == item['bytes']
    if 'mode' in item:
        assert stat.S_IMODE(actual.stat().st_mode) == item['mode']
observed = []
for p in Path(runtime['root']).rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        observed.append(str(p.relative_to(runtime['root'])))
assert set(observed) == {r['path'] for r in runtime['complete_files']}
assert json.loads(read(out / 'test-browser-runtime.json')) == runtime

source = json.loads(read(q / 'stage-security-08.json'))['files']
prepared = []
for item in source:
    if item['path'] == 'host-security-runner.py':
        continue
    raw = read(root / item['path'])
    assert row(item['path'], raw) == item
    prepared.append((item['path'], raw))
for name in ('host-security-browser.py', 'security-browser.cjs', 'test-browser-runtime.json'):
    prepared.append((name, read(out / name)))
assert not stage.exists()
stage.mkdir()
rows = []
for name, raw in prepared:
    target = stage / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append(row(name, raw))
manifest = (json.dumps({'files': rows}, indent=2) + '\n').encode()
(stage / 'inputs.json').write_bytes(manifest)
(q / 'stage-security-browser-03.json').write_bytes(manifest)
job = json.loads(read(q / 'host-security-browser-02.json'))
job.update(command=[str(root / '.venv/bin/python'), '-I', '-B', str(stage / 'host-security-browser.py')],
           staging_root=str(stage), manifest=row(stage / 'inputs.json', manifest),
           inputs_count=len(rows), external_tools=pins['external_tools'],
           tool_admission_source=row(pin_path, read(pin_path)),
           browser_runtime={'name': 'Chrome Headless Shell', 'revision': '1234',
                            'expected_version': '151.0.7922.34', 'executable': runtime['executable'],
                            'complete_inventory_root': runtime['root'], 'complete_file_count': 20,
                            'inventory_stage_file': 'test-browser-runtime.json', 'pre_post_required': True,
                            'qualification': 'Explicit admitted test runtime; no system Chrome or native Safari equivalence.'},
           source_mapping={name: str(out / name) for name in ('host-security-browser.py', 'security-browser.cjs', 'test-browser-runtime.json')},
           gate='Manager review/release before root execution. Four unchanged AT27 browser groups; current production assets and explicit admitted headless runtime. No TASK022/VoiceOver/participant claim.')
p = q / 'host-security-browser-03.json'
assert not p.exists()
p.write_text(json.dumps(job, indent=2) + '\n')
for item in rows:
    assert row(item['path'], read(stage / item['path'])) == item
print(json.dumps({'job': row(p, read(p)), 'manifest': job['manifest'],
                  'inputs_count': len(rows), 'tool_pins': len(job['external_tools']),
                  'runtime_members': len(observed), 'host_execution': False}))
