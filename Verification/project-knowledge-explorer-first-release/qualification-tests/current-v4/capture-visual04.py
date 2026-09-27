"""Preserve the one actual root visual04 run without executing a browser."""
import base64
import hashlib
import json
import os
from pathlib import Path
import stat

O = Path(__file__).resolve().parent
ROOT = O.parents[3]
SOURCE = Path('/private/tmp/explorer-task022-visual-host-j9mvy3w_')
OUT = O / 'actual-visual-04'


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
expected={'receipt.json':'4a4c09517fe21b19e05b6485074ff66bc4fac1aff1e318d03881ee1023cbe864','stdout.json':'f67e4d56bdfcbe5aea9181ef74b1d2fd30e1b0a954ccde81e38c1c35df83573b','raw-index.json':'115fae457b5068dc88a23502d1a4818679fd6ca40e91c9984021e97ced2ee9d1','root-visual-observation.json':'04d41e040506edc569a8e6f411fe61432a6c0a49654003d3f569d5ea947ac616'}
for name,digest in expected.items():
    assert ref(SOURCE/name)['sha256']==digest
report=json.loads(read(SOURCE/'stdout.json'));receipt=json.loads(read(SOURCE/'receipt.json'));job=json.loads(read(SOURCE/'reviewed-job.json'))
assert report['status']==receipt['status']=='passed' and report['observation_execution_complete']
assert len(report['scans'])==8 and report['async_failures']==[]
assert receipt['post_verification_errors']==[] and receipt['stderr_bytes']==0
members=json.loads(read(job['manifest']['path']))['files'];assert len(members)==108
for member in members:
    for stage in [Path(job['staging_root']),Path(receipt['execution_stage'])]:
        actual=ref(stage/member['path']);assert actual['sha256']==member['sha256'] and actual['bytes']==member['bytes']
OUT.mkdir();(OUT/'raw-shards').mkdir()
names=['host-wrapper.py','reviewed-release.json','reviewed-job.json','raw-index.json','root-visual-observation.json','stdout.json','admission.json','receipt.json']
for name in names:
    data=read(SOURCE/name);assert len(data)<250000;(OUT/name).write_bytes(data)
rows=[]
for i,scan in enumerate(report['scans']):
    row={'name':scan['name'],'theme':scan['theme'],'members':{}}
    for kind in ['raw_report','screenshot']:
        original=scan[kind];data=read(original['path']);assert len(data)==original['bytes'] and hashlib.sha256(data).hexdigest()==original['sha256']
        row['members'][kind]={'original':original,'parts':preserve(data,f'{i:02}-{kind}')}
    rows.append(row)
raw_index=put(OUT/'raw-shard-index.json',{'status':'all8_JSON_and8_PNG_losslessly_preserved','rows':rows,'raw_bytes':sum(x['original']['bytes'] for s in rows for x in s['members'].values()),'qualification':'Actual targeted scrolled JSON/PNG observations. Root visual review covers all8 images and preserves whole-page and native limits.'})
attribution=put(OUT/'attribution.json',{'status':'all8_targeted_visual_observations_passed_with_scoped_review','actual_executor':'/root','root_source':str(SOURCE),'references':[ref(OUT/name) for name in names],'raw_reports':raw_index,'build_id':'c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a','original_captured108_members_reverified':True,'qualification':'Root directly viewed all8 current targeted images, separately attributed. Worker inspection and individual geometry/contrast mapping remain separate; no native speech/WCAG claim.'})
print(json.dumps({'attribution':attribution,'raw_index':raw_index,'raw_bytes':sum(x['original']['bytes'] for s in rows for x in s['members'].values())}))
