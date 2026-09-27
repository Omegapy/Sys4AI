"""Create a fresh immutable lifecycle-browser stage from verified live inputs."""
from pathlib import Path
import hashlib,json,stat,sys
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
number=sys.argv[1];assert len(number)==2 and number.isdigit()
stage=Path('/private/tmp/explorer-qualification-lifecycle-browser-'+number);stage.mkdir()
security_number=sys.argv[2];assert len(security_number)==2 and security_number.isdigit()
source=json.loads((out/('stage-security-'+security_number+'.json')).read_bytes())['files'];rows=[]
for row in source:
    if row['path']=='host-security-runner.py' or row['path'].endswith('/test_explorer_security.py'):continue
    p=root/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink()
    raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
    dest=stage/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);rows.append(row)
for name in ('host-lifecycle-browser.py','lifecycle-browser.cjs'):
    raw=(out/name).read_bytes();(stage/name).write_bytes(raw);rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
manifest=(json.dumps({'files':rows},indent=2)+'\n').encode();(stage/'inputs.json').write_bytes(manifest);(out/('stage-lifecycle-browser-'+number+'.json')).write_bytes(manifest)
tools=[]
for p in [root/'.venv/bin/python',Path('/bin/ps'),Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'),Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json'),Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')]:
    actual=p.resolve();raw=actual.read_bytes();tools.append({'path':str(p),'resolved':str(actual),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
job={'command':[str(root/'.venv/bin/python'),'-I','-B',str(stage/'host-lifecycle-browser.py'),'expiry'],'staging_root':str(stage),
 'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(manifest).hexdigest()},'inputs_count':len(rows),'external_tools':tools,
 'timeout_seconds':130,'source_writes':False,'intended_writes':['Owned disposable explorer-http-* fixture; actual loopback service and Chrome child/profile; bounded cleanup/reaping.'],
 'credentials':'Bootstrap URL only in 0600 per-instance file/process memory, no raw errors, headers, response bytes, traces or HAR.',
 'scenarios':['AT-23 actual60-second expiry or owned-service stop; exact route/text retention and truthful explicit reopening help']}
p=out/('host-lifecycle-browser-'+number+'-expiry.json');p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'manifest':job['manifest'],'inputs_count':len(rows)}))

job['command'][-1]='stop';p=out/('host-lifecycle-browser-'+number+'-stop.json');p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
