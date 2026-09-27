"""Freeze the current expired-session accessibility observation job only."""
from pathlib import Path
import hashlib, json, os, stat

out = Path(__file__).resolve().parent
q = out.parent
root = q.parents[2]

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
prior = json.loads(read(q / 'host-accessibility-browser-13.json'))
for item in prior['external_tools']:
    if '/explorer-qualification-axe-4.13.0/' not in item['path']:
        continue
    actual = Path(item['path']).resolve()
    assert str(actual) == item['resolved']
    raw = read(actual)
    assert hashlib.sha256(raw).hexdigest() == item['sha256'] and len(raw) == item['bytes']
    pins['external_tools'].append(item)
assert len(pins['external_tools']) == 31
stage = Path('/private/tmp/explorer-qualification-expiry-accessibility-02')
prepared = []
for item in source:
    if item['path'] == 'host-security-runner.py' or item['path'].endswith('/test_explorer_security.py'):
        continue
    raw = read(root / item['path'])
    assert row(item['path'], raw) == item
    prepared.append((item['path'], raw))
extra = ('host-expiry-accessibility.py', 'expiry-accessibility-browser.cjs', 'test-browser-runtime.json')
for name in extra:
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
(q / 'stage-expiry-accessibility-02.json').write_bytes(manifest)
job = json.loads(read(q / 'host-expiry-accessibility-01.json'))
job.update(command=[str(root / '.venv/bin/python'), '-I', '-B', str(stage / extra[0])],
           staging_root=str(stage), manifest=row(stage / 'inputs.json', manifest),
           inputs_count=len(rows), external_tools=pins['external_tools'],
           tool_admission_source=row(pin_path, read(pin_path)),
           source_mapping={name: str(out / name) for name in extra},
           expected_state_theme_count=2,
           browser_runtime={'name': 'Chrome Headless Shell', 'revision': '1234', 'expected_version': '151.0.7922.34', 'executable':runtime['executable'], 'complete_inventory_root':runtime['root'], 'complete_file_count':20, 'inventory_stage_file':'test-browser-runtime.json', 'pre_post_required':True},
           scenarios=['Real unchanged60-second selected synthetic session expiry; exact recorded entry/route retained; actual expired-state light and dark axe scans with full raw reports.'],
           gate='TASK022 only after current TASK021 acceptance and exact manager-reviewed root release. Two expired-state scans supplement main70 states; no native speech, complete manual accessibility or WCAG claim.')
job.pop('required_state_coverage',None)
target = q / 'host-expiry-accessibility-02.json'
assert not target.exists()
target.write_text(json.dumps(job, indent=2) + '\n')
for item in rows:
    assert row(item['path'], read(stage / item['path'])) == item
print(json.dumps({'job': row(target, read(target)), 'manifest': job['manifest'], 'inputs_count':len(rows), 'tools':31, 'runtime_members':20, 'states':2, 'host_execution':False}))
