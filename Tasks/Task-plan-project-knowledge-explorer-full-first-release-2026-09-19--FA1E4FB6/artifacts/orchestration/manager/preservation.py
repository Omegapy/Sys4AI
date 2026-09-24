from pathlib import Path
import json,hashlib,subprocess,os,sys
from events import ROOT,MD,ref,TD
scopes=['AGENTS.md','SOUL.md','ROLE.md','SPECS.md','TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md','depot','SKILLS-depo/ontology','ONTOLOGY-depo','.agents/skills/ontology','ONTOLOGY','ontology.yaml','ontology-advanced.yaml','memory.yaml','MEMORY','Projects/Sys4AI-Template-Project']
def tree(p):
 p=ROOT/p
 if p.is_file(): return {'files':1,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 h=hashlib.sha256();n=0
 for base,ds,fs in os.walk(p,followlinks=False):
  ds[:]=sorted(d for d in ds if d not in ('.git','.venv','__pycache__','node_modules'))
  for name in sorted(fs):
   q=Path(base)/name
   if q.is_symlink(): content=('symlink:'+os.readlink(q)).encode()
   else: content=q.read_bytes()
   h.update(str(q.relative_to(p)).encode()+b'\0'+hashlib.sha256(content).digest());n+=1
 return {'files':n,'sha256':h.hexdigest()}
out={'scopes':{p:tree(p) for p in scopes},'excluded':'Git internals, virtual environments, node_modules and Python cache directories; no product runtime/external behavior assessed.','head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'tracked_diff':subprocess.check_output(['git','diff','--name-status'],text=True),'staged_diff':subprocess.check_output(['git','diff','--cached','--name-status'],text=True)}
name=sys.argv[1]
if name=='final':
 base=json.loads((MD/'preservation-baseline.json').read_text());out['comparison']={p:out['scopes'][p]==base['scopes'][p] for p in scopes};out['git_head_unchanged']=out['head']==base['head'];out['staged_unchanged']=out['staged_diff']==base['staged_diff']
(MD/('preservation-'+name+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'file':str(MD/('preservation-'+name+'.json')),'files_hashed':sum(x['files'] for x in out['scopes'].values()),'comparison':out.get('comparison')}))
