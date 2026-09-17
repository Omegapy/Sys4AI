from pathlib import Path
import json,hashlib,re
root=Path.cwd();base=root/'SKILLS-depo/init-new-project/assets';path=base/'static-capability-v1.json';data=json.loads(path.read_text());mapping=json.loads((root/'depot/template-update.json').read_text())
reverse={v:k for k,v in {**mapping['overrides'],**mapping.get('additional_mappings',{})}.items()}
def source(name):
 if name in reverse:return root/reverse[name]
 if name.startswith('.agents/skills/'):return root/'SKILLS-depo'/name.removeprefix('.agents/skills/')
 if name.startswith('reference-assets/'):return root/name.removeprefix('reference-assets/')
 if name.startswith('Roles/'):
  _,role,leaf=name.split('/');return root/'ROLES-depo'/(role+'-'+leaf)
 return root/name
for key in ('locked_resources','curator_locked_resources'):
 for name in data[key]:
  p=source(name)
  if p.is_file():data[key][name]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('.agents/skills/ontology/scripts/ontology_integration.py','.agents/skills/init-new-project/scripts/init_curator_integration.py','.agents/skills/init-new-project/assets/static-capability-v11.json'):
 package=name.split('/scripts/')[0] if '/scripts/' in name else name.split('/assets/')[0]
 data['packages'].setdefault(package,[])
 if name not in data['packages'][package]:data['packages'][package].append(name);data['packages'][package].sort()
 if 'ontology_integration' in name:data['curator_locked_resources'][name]=hashlib.sha256(source(name).read_bytes()).hexdigest()
for package,names in data['packages'].items():
 data['packages'][package]=[n for n in names if not n.endswith('/competencies.json')]
for key in ('locked_resources','curator_locked_resources'):
 data[key]={n:d for n,d in data[key].items() if not n.endswith('/competencies.json')}
for p in sorted((root/'ONTOLOGY-depo/integrations/curator/1.0.0').iterdir()):
 name='reference-assets/'+p.relative_to(root).as_posix();package='reference-assets/ONTOLOGY-depo'
 data['packages'].setdefault(package,[])
 if name not in data['packages'][package]:data['packages'][package].append(name);data['packages'][package].sort()
 data['curator_locked_resources'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
path.write_text(json.dumps(data,indent=2)+'\n')
p=root/'SKILLS-depo/init-new-project/scripts/init_static_health.py';s=p.read_text();s=re.sub(r'^INVENTORY_SHA256 = "[a-f0-9]+"', 'INVENTORY_SHA256 = "'+hashlib.sha256(path.read_bytes()).hexdigest()+'"',s,flags=re.M);p.write_text(s)
