"""Run only after user approval: restore the existing lock in isolated build staging."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'SKILLS-depo/ontology/explorer'
stage=Path(tempfile.mkdtemp(prefix='project-app-locked-build-',dir='/private/tmp')).resolve()
for name in ('package.json','package-lock.json'):(stage/name).write_bytes((SOURCE/name).read_bytes())
for name in ('npm-user.conf','npm-global.conf'):(stage/name).write_text('')
env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','LANG':'en_US.UTF-8','npm_config_userconfig':str(stage/'npm-user.conf'),'npm_config_globalconfig':str(stage/'npm-global.conf'),'npm_config_cache':str(stage/'npm-cache'),'npm_config_audit':'false','npm_config_fund':'false','npm_config_update_notifier':'false'}
command=['/opt/homebrew/bin/npm','ci','--ignore-scripts','--no-audit','--no-fund']
result=subprocess.run(command,cwd=stage,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
(OUT/'dependency-restore.log').write_text(result.stdout)
report={'stage':str(stage),'command':command,'exit_code':result.returncode,'lock_sha256':hashlib.sha256((SOURCE/'package-lock.json').read_bytes()).hexdigest(),'lock_preserved':(SOURCE/'package-lock.json').read_bytes()==(stage/'package-lock.json').read_bytes(),'scripts_disabled':True,'versions_upgraded':False}
(OUT/'dependency-restore.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
raise SystemExit(result.returncode)
