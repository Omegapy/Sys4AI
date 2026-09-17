from pathlib import Path
import sys,shutil,json,hashlib
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DEST=OUT/'root-copy'
sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_standards import _prepare
from ontology_core import canonical_bytes,sha256
cfg,payload,p=_prepare(ROOT)
assert not DEST.exists();DEST.mkdir()
for rel in ('ONTOLOGY','reference-assets/ONTOLOGY-depo','.agents/skills/ontology'):
 shutil.copytree(ROOT/rel,DEST/rel,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
files={s['path'] for s in payload['sources']}|{'ontology.yaml','ontology-advanced.yaml','SOUL.md','AGENTS.md','ROLE.md','SPECS.md'}
for rel in files:
 source=ROOT/rel;target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
shutil.copytree(ROOT/'.venv-ontology-standards',DEST/'.venv-ontology-standards',symlinks=True,ignore=shutil.ignore_patterns('wheels','__pycache__','*.pyc'))
rows=json.loads((OUT/'preimages.json').read_text())
for row in rows:
 source=ROOT/row['source'];dest=DEST/row['source'].replace('SKILLS-depo/ontology/','.agents/skills/ontology/')
 assert sha256(dest)==row['root_sha256'];shutil.copyfile(source,dest)
protected={str(x.relative_to(DEST)):sha256(x) for x in DEST.rglob('*') if x.is_file() and '.venv-ontology-standards' not in x.parts}
(OUT/'root-copy-inputs.json').write_bytes(canonical_bytes({'actual_root_snapshot':payload['context']['snapshot_sha256'],'records':len(p.records),'limits':cfg['limits'],'copied_sources':sorted(files),'protected':protected}))
print('copied',len(protected),'files; records',len(p.records))
