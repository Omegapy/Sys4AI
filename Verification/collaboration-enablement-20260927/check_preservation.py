from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((OUT/'root-before.json').read_text());allowed={'.agents/skills/task/SKILL.md','.agents/skills/agent-task/SKILL.md','ontology-advanced.yaml'}
allowed.update(p for p in before if p.startswith('.agents/skills/init-new-project/'))
changed=[p for p,h in before.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h];bad=[p for p in changed if p not in allowed]
new_protected=[str(p.relative_to(ROOT)) for name in ['Tasks','Roles','.agents/skills/agent-task'] for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and str(p.relative_to(ROOT)) not in before]
report={'captured':len(before),'changed_allowed':changed,'unexpected_changes':bad,'unexpected_protected_additions':new_protected,'canonical_tasks_role_pairs_helpers_unchanged':not bad and not new_protected,'registry_unchanged':sha(ROOT/'depot/projects.json')==before['depot/projects.json']}
(OUT/'preservation.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='changed_allowed'}));assert not bad and not new_protected
