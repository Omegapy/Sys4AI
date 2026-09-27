"""Freeze current malicious-text checks with the admitted headless runtime."""
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
configs = [('accessibility','16','host-accessibility-browser-15.json',{'narrow-states.cjs':out/'narrow-states-focus-classified.cjs'}),('geometry','04','host-geometry-browser-03.json',{'narrow-states.cjs':out/'narrow-states-focus-classified.cjs','geometry-browser.cjs':out/'geometry-browser-focus-classified.cjs'})]
for kind,number,previous,replacements in configs:
    previous_path = q / previous
    job = json.loads(read(previous_path))
    oldstage = Path(job['staging_root'])
    oldmanifest = read(oldstage/'inputs.json')
    assert hashlib.sha256(oldmanifest).hexdigest() == job['manifest']['sha256']
    source_rows = json.loads(oldmanifest)['files']
    prepared = []
    for item in source_rows:
        original = read(oldstage/item['path'])
        assert row(item['path'],original) == item
        live = Path(job.get('source_mapping',{}).get(item['path'],root/item['path']))
        assert read(live) == original
        prepared.append((item['path'],read(replacements[item['path']]) if item['path'] in replacements else original))
    stage = Path('/private/tmp/explorer-qualification-'+kind+'-browser-'+number)
    assert not stage.exists()
    stage.mkdir()
    rows = []
    for name,raw in prepared:
        p = stage/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(raw)
        rows.append(row(name,raw))
    manifest=(json.dumps({'files':rows},indent=2)+'\n').encode()
    (stage/'inputs.json').write_bytes(manifest)
    (q/('stage-'+kind+'-browser-'+number+'.json')).write_bytes(manifest)
    job.update(command=[str(root/'.venv/bin/python'),'-I','-B',str(stage/('host-'+kind+'-browser.py'))],staging_root=str(stage),manifest=row(stage/'inputs.json',manifest),external_tools=pins['external_tools'])
    job['source_mapping'].update({k:str(v) for k,v in replacements.items()})
    job.pop('diagnostic_successor',None)
    job['focus_classification_successor']={'previous_job':row(previous_path,read(previous_path)),'actual_basis':row(out/'actual-accessibility-15-failed/attribution.json',read(out/'actual-accessibility-15-failed/attribution.json')),'full_named_state_coverage_unchanged':True,'bounded_change':'Permit only BODY/root with document.hasFocus=false and actual modal/dialog stillopen. Every next Tab must return inside with document focus; actual focused backgroundcontrol fails. Final visible focused modalcontrol asserted; full safe trace retained. No product change/browser-chrome destination claim.','synthetic_classification_cases':7,'browser_execution':False}
    target=q/('host-'+kind+'-browser-'+number+'.json')
    assert not target.exists()
    target.write_text(json.dumps(job,indent=2)+'\n')
    for item in rows:
        assert row(item['path'],read(stage/item['path'])) == item
    print(json.dumps({'job':row(target,read(target)),'manifest':job['manifest'],'drivers':[row(v,read(v)) for v in replacements.values()],'files':len(rows),'tools':len(pins['external_tools']),'runtime_files':20,'executed':False}))
