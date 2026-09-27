"""Create a fresh immutable accessibility-browser stage from verified live inputs."""
from pathlib import Path
import hashlib,json,stat,sys
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
number=sys.argv[1];assert len(number)==2 and number.isdigit()
stage=Path('/private/tmp/explorer-qualification-expiry-accessibility-'+number);stage.mkdir()
security_number=sys.argv[2];assert len(security_number)==2 and security_number.isdigit()
source=json.loads((out/('stage-security-'+security_number+'.json')).read_bytes())['files'];rows=[]
for row in source:
    if row['path']=='host-security-runner.py' or row['path'].endswith('/test_explorer_security.py'):continue
    p=root/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink()
    raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
    dest=stage/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);rows.append(row)
for name in ('host-expiry-accessibility.py','expiry-accessibility-browser.cjs'):
    raw=(out/name).read_bytes();(stage/name).write_bytes(raw);rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
manifest=(json.dumps({'files':rows},indent=2)+'\n').encode();(stage/'inputs.json').write_bytes(manifest);(out/('stage-expiry-accessibility-'+number+'.json')).write_bytes(manifest)
tools=[]
for p in [root/'.venv/bin/python',Path('/bin/ps'),Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'),Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json'),Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),Path('/private/tmp/explorer-qualification-axe-4.13.0/axe.min.js'),Path('/private/tmp/explorer-qualification-axe-4.13.0/LICENSE'),Path('/private/tmp/explorer-qualification-axe-4.13.0/LICENSE-3RD-PARTY.txt')]:
    actual=p.resolve();raw=actual.read_bytes();tools.append({'path':str(p),'resolved':str(actual),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
job={'command':[str(root/'.venv/bin/python'),'-I','-B',str(stage/'host-expiry-accessibility.py')],'staging_root':str(stage),
 'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(manifest).hexdigest()},'inputs_count':len(rows),'external_tools':tools,
 'timeout_seconds':300,'source_writes':False,'intended_writes':['Owned disposable explorer-http-* fixture; actual loopback service and Chrome child/profile; bounded cleanup/reaping. Complete raw axe reports in fresh private /private/tmp/explorer-a11y-evidence-* survive fixture cleanup for exact later hash verification and bounded sharding.'],
 'credentials':'Bootstrap URL only in 0600 per-instance file/process memory, no raw errors, headers, response bytes, traces or HAR.',
 'scenarios':['TASK022 WCAG-tagged axe4.13.0 scans for2 actual expired-session theme states after real60-second unmodified service/client session timing'],'gate':'Do not execute until TASK021 passes. Scans are declared DevTools instrumentation, not inline/CSP/VoiceOver or blanket WCAG compliance proof.'}
p=out/('host-expiry-accessibility-'+number+'.json');p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'manifest':job['manifest'],'inputs_count':len(rows)}))
