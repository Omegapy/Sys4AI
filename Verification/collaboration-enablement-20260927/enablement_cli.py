import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent

def run(name, command):
 r=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
 try: result=json.loads(r.stdout)
 except ValueError: result={'stdout':r.stdout}
 (OUT/name).write_text(json.dumps({'command':command,'exit_code':r.returncode,'result':result,'stderr':r.stderr},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':name,'exit_code':r.returncode,'status':result.get('status',result.get('aggregate')),'enabled':result.get('enabled'),'ready':result.get('ready'),'valid':result.get('valid'),'error':result.get('error'),'keys':list(result)}))
 return r.returncode
if __name__=='__main__':
 mode,name=sys.argv[1:3];args=sys.argv[3:]
 if mode=='ontology' or mode=='memory':command=[str(ROOT/'.venv/bin/python'),str(ROOT/f'.agents/skills/{mode}/scripts/{mode}.py'),'--project-root',str(ROOT),*args]
 elif mode=='template':command=[str(ROOT/'.venv/bin/python'),str(ROOT/'tools/template_update.py'),*args]
 elif mode=='collaboration':command=[str(ROOT/'.venv/bin/python'),str(ROOT/'.agents/skills/collaborate/scripts/collaborate.py'),'--project-root',str(ROOT),*args]
 elif mode=='init':command=[str(ROOT/'.venv/bin/python'),str(ROOT/'.agents/skills/init-new-project/scripts/init_new_project.py'),*args]
 else:raise ValueError(mode)
 sys.exit(run(name,command))
