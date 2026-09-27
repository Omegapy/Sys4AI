from pathlib import Path
import hashlib,json,shutil,datetime
ROOT=Path.cwd().resolve();OUT=ROOT/'Verification/collaboration-enablement-20260927'
sha=lambda b:hashlib.sha256(b).hexdigest()
source=ROOT/'SKILLS-depo/collaborate';target=ROOT/'.agents/skills/collaborate'
assert not target.exists(),'unexpected prior root installation'
inventory={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
changes={};manifest=[]
for path,heading in [('.agents/skills/task/SKILL.md','## Task collaboration ownership'),('.agents/skills/agent-task/SKILL.md','## Collaboration message and owner gates')]:
    dest=ROOT/path;old=dest.read_bytes();raw=(ROOT/'SKILLS-depo'/Path(path).relative_to('.agents/skills')).read_text()
    start=raw.index(heading+'\n');end=raw.find('\n## ',start+len(heading));block=raw[start:] if end<0 else raw[start:end]
    new=old.rstrip()+('\n\n'+block.strip()+'\n').encode();assert b'<!-- sys4ai:collaboration-' not in old
    retained=OUT/'root-retained'/path;retained.parent.mkdir(parents=True,exist_ok=True);retained.write_bytes(old)
    changes[path]=new;manifest.append(dict(source='SKILLS-depo/'+str(Path(path).relative_to('.agents/skills')),destination=path,before=sha(old),after=sha(new),operation='append-scoped-instruction'))
for path,raw in inventory.items():
    dest=target/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    manifest.append(dict(source='SKILLS-depo/collaborate/'+path,destination='.agents/skills/collaborate/'+path,before=None,after=sha(raw),operation='install'))
for path,raw in changes.items(): (ROOT/path).write_bytes(raw)
receipt=dict(schema_version=1,project_root=str(ROOT),status='completed',authority='User requested root collaboration enablement and automatic initializer integration in this conversation.',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),package_inventory={'.agents/skills/collaborate/'+p:sha(raw) for p,raw in inventory.items()},guidance={p:sha(raw) for p,raw in changes.items()},manifest=manifest,limits=['Static readiness only; no native replay of this edition.','Existing Task helpers, role pairs and canonical records preserved.'])
path=ROOT/'control_records/collaboration-installation.json';assert not path.exists();path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
(OUT/'root-collaboration-adoption.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({'installed_files':len(inventory),'instruction_additions':len(changes),'receipt':str(path)}))
