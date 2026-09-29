"""Publish the one-line wrapping correction and its reviewed build assets."""
from pathlib import Path
import hashlib,json,shutil,re
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
PKG=ROOT/'SKILLS-depo/ontology';BUILD=Path('/private/tmp/project-app-locked-build-a2r9rugo/SKILLS-depo/ontology/explorer')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
record=json.loads((BUILD/'dist/.explorer-build.json').read_text())
for row in record['inputs']['record']['files']:
 name=row['path']
 if name.startswith('$schema/'):p=ROOT/'ONTOLOGY-depo/schema'/name.split('/',1)[1]
 elif name.startswith('$tooling/'):p=PKG/'scripts'/name.split('/',1)[1]
 elif name.startswith('$project-app/scripts/'):p=PKG/'scripts'/name.rsplit('/',1)[1]
 elif name.startswith('$project-app/assets/'):p=PKG/'assets/project-app'/name.rsplit('/',1)[1]
 else:p=PKG/'explorer'/name
 assert sha(p.read_bytes())==row['sha256'],name
source=PKG/'explorer/assets';new=json.loads((BUILD/'assets/manifest.json').read_text());old=json.loads((source/'manifest.json').read_text())
for row in old['assets']:assert sha((source/row['path']).read_bytes())==row['sha256']
oldnames={r['path'] for r in old['assets']};newnames={r['path'] for r in new['assets']}
for name in oldnames|{'manifest.json'}:
 p=source/name;backup=OUT/'preimages-layout'/p.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,backup)
for row in new['assets']:
 p=source/row['path'];raw=(BUILD/'assets'/row['path']).read_bytes();assert sha(raw)==row['sha256'];assert not p.exists() or row['path'] in oldnames
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for name in oldnames-newnames:(source/name).unlink()
(source/'manifest.json').write_bytes((BUILD/'assets/manifest.json').read_bytes())
p=ROOT/'SKILLS-depo/init-new-project/assets/static-capability-v1.json';d=json.loads(p.read_text());key='.agents/skills/ontology';prefix=key+'/explorer/assets/'
d['packages'][key]=sorted({n for n in d['packages'][key] if not n.startswith(prefix)}|{prefix+n for n in newnames}|{prefix+'manifest.json'});p.write_text(json.dumps(d,indent=2)+'\n')
h=ROOT/'SKILLS-depo/init-new-project/scripts/init_static_health.py';h.write_text(re.sub(r'INVENTORY_SHA256 = "[a-f0-9]{64}"','INVENTORY_SHA256 = "'+sha(p.read_bytes())+'"',h.read_text()))
# The running root app was authenticated-stopped before these byte changes.
assert not list((ROOT/'.sys4ai/project-app').glob('service-*.json'))
prior=json.loads((OUT/'root-adoption.json').read_text());expected={r['destination']:r['source_sha256'] for r in prior['files']}
selected=['.agents/skills/ontology/explorer/src/styles.css','.agents/skills/init-new-project/assets/static-capability-v1.json','.agents/skills/init-new-project/scripts/init_static_health.py']
installed=ROOT/'.agents/skills/ontology/explorer/assets';oldinstalled=json.loads((installed/'manifest.json').read_text());priorassets={r['path']:r['sha256'] for r in oldinstalled['assets']}
rows=[]
for dest in selected:
 p=ROOT/dest;assert sha(p.read_bytes())==expected[dest],dest
 sourcepath=dest.replace('.agents/skills/','SKILLS-depo/',1);rows.append({'source':sourcepath,'destination':dest,'before':sha(p.read_bytes()),'after':sha((ROOT/sourcepath).read_bytes())})
for name in priorassets.keys()|newnames|{'manifest.json'}:
 dest='.agents/skills/ontology/explorer/assets/'+name;p=ROOT/dest;src=source/name
 before=sha(p.read_bytes()) if p.exists() else None
 if name in priorassets:assert before==priorassets[name],dest
 elif name=='manifest.json':assert before==expected[dest]
 else:assert before is None,dest
 after=sha(src.read_bytes()) if src.exists() else None
 if before!=after:rows.append({'source':str(src.relative_to(ROOT)) if after else None,'destination':dest,'before':before,'after':after})
(OUT/'root-layout-adoption-manifest.json').write_text(json.dumps({'reason':'Observed narrow-layout overflow from an unbroken Task SHA; one CSS rule and generated package identity only.','files':rows},indent=2)+'\n')
for row in rows:
 p=ROOT/row['destination'];assert (sha(p.read_bytes()) if p.exists() else None)==row['before']
 if p.exists():
  backup=OUT/'preimages-layout'/row['destination'];backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,backup)
 if row['source']:
  raw=(ROOT/row['source']).read_bytes();assert sha(raw)==row['after'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 else:p.unlink()
for row in rows:assert (sha((ROOT/row['destination']).read_bytes()) if (ROOT/row['destination']).exists() else None)==row['after']
shutil.copy2(OUT/'production-build.json',OUT/'production-build-before-layout.json');shutil.copy2(BUILD/'dist/.explorer-build.json',OUT/'production-build.json')
report={'status':'applied-verified','build_id':new['build_id'],'manifest_sha256':sha((source/'manifest.json').read_bytes()),'files':rows,'check':'exact source input and root pre/post hash comparisons','source_inputs_verified':len(record['inputs']['record']['files'])}
(OUT/'root-layout-adoption.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'build_id':new['build_id'],'files':len(rows)}))
