"""Create a fresh immutable live-preservation stage from verified live inputs."""
from pathlib import Path
import hashlib,json,stat,sys
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
number=sys.argv[1];assert len(number)==2 and number.isdigit()
stage=Path('/private/tmp/explorer-qualification-live-preservation-'+number);stage.mkdir()
security_number=sys.argv[2];assert len(security_number)==2 and security_number.isdigit()
source=json.loads((out/('stage-security-'+security_number+'.json')).read_bytes())['files'];rows=[]
for row in source:
    if row['path']=='host-security-runner.py' or row['path'].endswith('/test_explorer_security.py'):continue
    p=root/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink()
    raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
    dest=stage/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);rows.append(row)
for name in ('host-live-preservation.py','live-preservation-browser.cjs','protected-inventory.py'):
    raw=(out/name).read_bytes();(stage/name).write_bytes(raw);rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
manifest=(json.dumps({'files':rows},indent=2)+'\n').encode();(stage/'inputs.json').write_bytes(manifest);(out/('stage-live-preservation-'+number+'.json')).write_bytes(manifest)
tools=[]
for p in [root/'.venv/bin/python',Path('/bin/ps'),Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'),Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json'),Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')]:
    actual=p.resolve();raw=actual.read_bytes();tools.append({'path':str(p),'resolved':str(actual),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
job={'command':[str(root/'.venv/bin/python'),'-I','-B',str(stage/'host-live-preservation.py')],'staging_root':str(stage),
 'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(manifest).hexdigest()},'inputs_count':len(rows),'external_tools':tools,
 'timeout_seconds':180,'gate':'Execute only after TASK022 and manager/root coordinated evidence-write freeze. Target is exact live depot. Driver captures fresh complete registered-source/protected baseline before startup and after cleanup. No worker comparison window has started.','source_writes':False,'intended_writes':['Exact live depot dedicated-service startup only: per-instance bootstrap/service files and necessary0700 directories under .sys4ai/ontology/explorer; owned Chrome profile and /private/tmp/explorer-live-preservation-* evidence. All source/config/content remain read-only; exact files removed at cleanup.'],
 'credentials':'Bootstrap URL only in 0600 per-instance file/process memory, no raw errors, headers, response bytes, traces or HAR.',
 'scenarios':['AT33 actual live selected project search/definition/source/Map/List/expansion/process-gap/malformed requests/close; complete protected SHA256/mtime/mode comparison including all actual registered sources. Composite real synthetic expiry is separately bound.']}
p=out/('host-live-preservation-'+number+'.json');p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'manifest':job['manifest'],'inputs_count':len(rows)}))
