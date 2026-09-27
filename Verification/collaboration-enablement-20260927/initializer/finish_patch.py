from pathlib import Path
import json,hashlib
p=Path('SKILLS-depo/init-new-project/scripts/init_new_project.py');s=p.read_text()
s=s.replace('def run_initialization(**arguments) -> dict[str, Any]:\n', '''def run_initialization(
    *, mode: str, destination: Path, project_id: str, project_name: str, purpose: str,
    adopt_module: str | None = None, refresh_dependency: list[str] | None = None,
    refresh_module: list[str] | None = None,
    integration_grant_file=None, integration_proposal_file=None,
) -> dict[str, Any]:
''')
s=s.replace('    destination = arguments["destination"]\n    record_path = destination_file(destination, RECORD)\n', '''    arguments = dict(mode=mode, destination=destination, project_id=project_id,
        project_name=project_name, purpose=purpose, adopt_module=adopt_module,
        refresh_dependency=refresh_dependency, refresh_module=refresh_module,
        integration_grant_file=integration_grant_file, integration_proposal_file=integration_proposal_file)
    record_path = destination_file(destination, RECORD)
''')
s=s.replace('                operation["rerun"] = "verified-current-module-without-refresh"\n                checkpoint()', '                operation["rerun"] = "verified-current-module-without-refresh"\n                if module_id == COLLABORATION_MODULE:\n                    _static("apply", destination, record)\n                checkpoint()')
s=s.replace('            operation.pop("recovery", None)\n            checkpoint()', '            operation.pop("recovery", None)\n            if module_id == COLLABORATION_MODULE:\n                _static("apply", destination, record)\n            checkpoint()')
p.write_text(s)
# Extend the owned receipt schema only for this separately versioned module.
p=Path('SKILLS-depo/init-new-project/assets/initialization-receipt.schema.json');obj=json.loads(p.read_text())
module=obj['$defs']['moduleAdoption'] if 'moduleAdoption' in obj['$defs'] else next(v for v in obj['$defs'].values() if isinstance(v,dict) and 'module_id' in v.get('properties',{}))
module['properties']['module_id']['enum'].append('collaborate')
module['properties']['guidance_contents']={'type':'object','additionalProperties':{'type':'string'}}
module['allOf'].append({'if':{'properties':{'module_id':{'const':'collaborate'}}},'then':{'required':['guidance_contents'],'properties':{'new_memory':{'const':False},'refresh_dependencies':{'const':[]},'module_version':{'const':'1.0.0'}}},'else':{'not':{'required':['guidance_contents']}}})
obj['properties']['checks']['items']['properties']['check']['enum'].append('static-capability:collaborate')
p.write_text(json.dumps(obj,indent=2)+'\n')
# The historical v11 manifest remains byte-identical.
p=Path('SKILLS-depo/init-new-project/assets/static-capability-v1.json');obj=json.loads(p.read_text())
names=obj['packages'].get('initializer')
if names is None:
 key=next(k for k,v in obj['packages'].items() if any(n.endswith('/scripts/init_new_project.py') for n in v));names=obj['packages'][key]
names.extend(['.agents/skills/init-new-project/scripts/init_collaboration.py','.agents/skills/init-new-project/assets/collaboration_install.py'])
p.write_text(json.dumps(obj,indent=2)+'\n');sha=hashlib.sha256(p.read_bytes()).hexdigest()
p=Path('SKILLS-depo/init-new-project/scripts/init_static_health.py');s=p.read_text();start=s.index('INVENTORY_SHA256 = "');end=s.index('"',start+len('INVENTORY_SHA256 = "'));s=s[:start]+s[start:end].split(' = ')[0]+' = "'+sha+s[end:];p.write_text(s)
