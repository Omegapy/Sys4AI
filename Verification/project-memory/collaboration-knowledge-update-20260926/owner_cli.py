import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
PYTHON=ROOT/'.venv/bin/python'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name,data):
 p=OUT/name;p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n');return p

def run(name,kind,args):
 helper=ROOT/f'.agents/skills/{kind}/scripts/{kind}.py'
 command=[str(PYTHON),str(helper),'--project-root',str(ROOT),*args]
 r=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
 try:data=json.loads(r.stdout)
 except ValueError:data={'stdout':r.stdout,'stderr':r.stderr}
 save(name,{'command':command,'exit_code':r.returncode,'result':data,'stderr':r.stderr})
 return r.returncode,data
if __name__=='__main__':
 if sys.argv[1]=='baseline':
  cfg=json.loads((ROOT/'ontology.yaml').read_text());paths=['SPECS.md','README.md','memory.yaml','ontology.yaml','ontology-advanced.yaml',*cfg['project_files'],*cfg['binding_files'],*cfg['competency_files']]
  paths += [str(p.relative_to(ROOT)) for p in (ROOT/'MEMORY').glob('*.md')]
  paths += ['SKILLS-depo/collaborate/SKILL.md','depot/projects.json','depot/template-update.json','AGENTS.md','ROLE.md','SOUL.md']
  save('before.json',{p:sha(ROOT/p) for p in paths})
  for kind,args,name in [('memory',['health'],'memory-health-before.json'),('ontology',['health'],'ontology-health-before.json'),('ontology',['advanced-health'],'advanced-health-before.json')]:
   rc,d=run(name,kind,args);print(json.dumps({'kind':kind,'command':args[0],'exit_code':rc,'ready':d.get('ready'),'status':d.get('status',d.get('aggregate')),'failed_required':d.get('failed_required',d.get('assessment',{}).get('failed_required'))}))
 elif sys.argv[1]=='run':
  rc,d=run(sys.argv[2],sys.argv[3],sys.argv[4:]);print(json.dumps({'exit_code':rc,'status':d.get('status',d.get('aggregate')),'ready':d.get('ready'),'failed_required':d.get('failed_required',d.get('assessment',{}).get('failed_required')),'error':d.get('error'),'keys':list(d)}));sys.exit(rc)
