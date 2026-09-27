"""Preserve the one actual root geometry04 run without executing a browser."""
import base64
import hashlib
import json
import os
from pathlib import Path
import stat

O = Path(__file__).resolve().parent
ROOT = O.parents[3]
SOURCE = Path('/private/tmp/explorer-task022-host-bmq88_7t')
OUT = O / 'actual-geometry-04'


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
expected={'receipt.json':'5015d68a9913b0c329d941839448c859576987819344e08cf82d3a8e8fcb82a1','stdout.json':'63ac49c256fcb99df67b1c4728832a82b3da5d187823d2671a43f66e53cba2b4','raw-index.json':'8a72576693a5c14fa45f9dcd62f3c094b0ae13a26b6d3cca64741dd426b6cfcd','root-visual-observation.json':'adeebe08ea13717766e0887234d9c2fa1c7e42176f307d3ba3bb0bd548a6c467'}
for name,digest in expected.items():
    assert ref(SOURCE/name)['sha256']==digest
report=json.loads(read(SOURCE/'stdout.json'));receipt=json.loads(read(SOURCE/'receipt.json'));job=json.loads(read(SOURCE/'reviewed-job.json'))
assert report['status']==receipt['status']=='passed' and report['observation_execution_complete']
assert len(report['scans'])==46 and len(report['label_activations'])==2 and len(report['narrow_checks'])==8 and report['async_failures']==[]
assert receipt['post_verification_errors']==[] and receipt['stderr_bytes']==0
members=json.loads(read(job['manifest']['path']))['files'];assert len(members)==110
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
raw_index=put(OUT/'raw-shard-index.json',{'status':'all46_JSON_and46_PNG_losslessly_preserved','rows':rows,'raw_bytes':sum(x['original']['bytes'] for s in rows for x in s['members'].values()),'qualification':'Actual geometry and screenshot observations; one-for-one scanner336 incomplete/454 target adjudication remains pending. Root visual observation retains its viewport and source-content limits.'})
attribution=put(OUT/'attribution.json',{'status':'all46_state_geometry_execution_passed_manual_adjudication_pending','actual_executor':'/root','root_source':str(SOURCE),'references':[ref(OUT/name) for name in names],'raw_reports':raw_index,'build_id':'c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a','original_captured110_members_reverified':True,'label_click_scope':'Trusted draft-label activation/restoration twice per theme; measured associations/hits for other labels are not claimed as their individual clicked behavior.','qualification':'Root directly viewed16 added narrow-state viewport PNGs, separately attributed. Observations do not resolve all contrast/target findings or prove native speech/WCAG.'})
print(json.dumps({'attribution':attribution,'raw_index':raw_index,'raw_bytes':sum(x['original']['bytes'] for s in rows for x in s['members'].values())}))
