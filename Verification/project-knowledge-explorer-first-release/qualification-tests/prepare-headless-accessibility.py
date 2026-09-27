"""Create a fresh immutable accessibility-browser stage from verified live inputs."""
from pathlib import Path
import hashlib,json,stat,sys
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
number=sys.argv[1];assert len(number)==2 and number.isdigit()
stage=Path('/private/tmp/explorer-qualification-accessibility-browser-'+number);stage.mkdir()
security_number=sys.argv[2];assert len(security_number)==2 and security_number.isdigit()
source=json.loads((out/('stage-security-'+security_number+'.json')).read_bytes())['files'];rows=[]
for row in source:
    if row['path']=='host-security-runner.py' or row['path'].endswith('/test_explorer_security.py'):continue
    p=root/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink()
    raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
    dest=stage/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);rows.append(row)
for name in ('host-accessibility-browser.py','accessibility-browser.cjs'):
    raw=(out/name).read_bytes();(stage/name).write_bytes(raw);rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
runtime_path=root/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/qualification-headless-runtime-admission-v3.json'
runtime_raw=runtime_path.read_bytes();assert hashlib.sha256(runtime_raw).hexdigest()=='dc54ad75688e722fc61aa93320c520a71c16063e33aba20e0bdb90047492eb14'
runtime=json.loads(runtime_raw);(stage/'test-browser-runtime.json').write_bytes(runtime_raw);rows.append({'path':'test-browser-runtime.json','sha256':hashlib.sha256(runtime_raw).hexdigest(),'bytes':len(runtime_raw)})
manifest=(json.dumps({'files':rows},indent=2)+'\n').encode();(stage/'inputs.json').write_bytes(manifest);(out/('stage-accessibility-browser-'+number+'.json')).write_bytes(manifest)
tools=[]
for p in [root/'.venv/bin/python',Path('/bin/ps'),Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'),Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json'),Path('/private/tmp/explorer-qualification-axe-4.13.0/axe.min.js'),Path('/private/tmp/explorer-qualification-axe-4.13.0/LICENSE'),Path('/private/tmp/explorer-qualification-axe-4.13.0/LICENSE-3RD-PARTY.txt')]:
    actual=p.resolve();raw=actual.read_bytes();tools.append({'path':str(p),'resolved':str(actual),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
for row in runtime['complete_files']:
    p=Path(runtime['root'])/row['path'];st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and not p.is_symlink();raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['bytes'] and stat.S_IMODE(st.st_mode)==row['mode'];tools.append({'path':str(p),'resolved':str(p),'sha256':row['sha256'],'bytes':row['bytes'],'mode':row['mode']})
row=runtime['registry'];p=Path(row['path']);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];tools.append({'path':str(p),'resolved':str(p),'sha256':row['sha256'],'bytes':row['bytes']})
job={'command':[str(root/'.venv/bin/python'),'-I','-B',str(stage/'host-accessibility-browser.py')],'staging_root':str(stage),
 'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(manifest).hexdigest()},'inputs_count':len(rows),'external_tools':tools,
 'timeout_seconds':300,'browser_runtime':{'name':'Chrome Headless Shell','revision':'1234','expected_version':'151.0.7922.34','executable':runtime['executable'],'complete_inventory_root':runtime['root'],'complete_file_count':20,'inventory_stage_file':'test-browser-runtime.json','pre_post_required':True,'qualification':'Test-only runtime successor, no prior Chrome154 equivalence or native Safari/VoiceOver claim.'},'source_writes':False,'intended_writes':['Owned disposable explorer-http-* fixture; actual loopback service and Chrome child/profile; bounded cleanup/reaping. Complete raw axe reports in fresh private /private/tmp/explorer-a11y-evidence-* survive fixture cleanup for exact later hash verification and bounded sharding.'],
 'credentials':'Bootstrap URL only in 0600 per-instance file/process memory, no raw errors, headers, response bytes, traces or HAR.',
 'scenarios':['TASK022 WCAG-tagged axe4.13.0 scans for54 named destination/state/theme combinations and24px target candidates'],'gate':'Do not execute until TASK021 passes. Scans are declared DevTools instrumentation, not inline/CSP/VoiceOver or blanket WCAG compliance proof.'}
p=out/('host-accessibility-browser-'+number+'.json');p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'manifest':job['manifest'],'inputs_count':len(rows)}))
