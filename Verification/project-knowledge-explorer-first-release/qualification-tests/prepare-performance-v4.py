"""Create a fresh immutable performance-recipes stage from verified live inputs."""
from pathlib import Path
import hashlib,json,stat,sys
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
number=sys.argv[1];assert len(number)==2 and number.isdigit()
stage=Path('/private/tmp/explorer-qualification-performance-recipes-'+number);stage.mkdir()
security_number=sys.argv[2];assert len(security_number)==2 and security_number.isdigit()
source=json.loads((out/('stage-security-'+security_number+'.json')).read_bytes())['files'];rows=[]
for row in source:
    if row['path']=='host-security-runner.py' or row['path'].endswith('/test_explorer_security.py'):continue
    p=root/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink()
    raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
    dest=stage/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);rows.append(row)
for name in ('host-performance-recipes.py','performance-case.py','performance-control.py','performance-browser-case.py','performance-browser.cjs','compressed-runtime.cjs'):
    raw=(out/name).read_bytes();(stage/name).write_bytes(raw);rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
runtime_path=root/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/qualification-headless-runtime-admission-v3.json'
runtime_raw=runtime_path.read_bytes();assert hashlib.sha256(runtime_raw).hexdigest()=='dc54ad75688e722fc61aa93320c520a71c16063e33aba20e0bdb90047492eb14';runtime=json.loads(runtime_raw)
(stage/'test-browser-runtime.json').write_bytes(runtime_raw);rows.append({'path':'test-browser-runtime.json','sha256':hashlib.sha256(runtime_raw).hexdigest(),'bytes':len(runtime_raw)})
manifest=(json.dumps({'files':rows},indent=2)+'\n').encode();(stage/'inputs.json').write_bytes(manifest);(out/('stage-performance-recipes-'+number+'.json')).write_bytes(manifest)
pin_path=root/'Verification/project-knowledge-explorer-first-release/service-tests/service-v4/tool-pins.json'
pin_raw=pin_path.read_bytes();assert hashlib.sha256(pin_raw).hexdigest()=='7099d9b64f22b897f4c9981fc768f18bd4194b4ec2ae999822a009c3a7853ae2'
pins=json.loads(pin_raw);assert pins['headless_runtime']==runtime;tools=pins['external_tools'][:]
old=json.loads((out/'host-performance-recipes-04.json').read_bytes())
for row in old['external_tools']:
    if row['path'] in ('/usr/sbin/sysctl','/usr/bin/sw_vers'):tools.append(row)
assert len(tools)==30
for row in tools:
    p=Path(row['path']);actual=p.resolve();assert str(actual)==row['resolved'];st=actual.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
    raw=actual.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['bytes']
    if 'mode' in row:assert stat.S_IMODE(st.st_mode)==row['mode']
assert {str(p.relative_to(runtime['root'])) for p in Path(runtime['root']).rglob('*') if p.is_file()}=={r['path'] for r in runtime['complete_files']} and not any(p.is_symlink() for p in Path(runtime['root']).rglob('*'))
job={'command':[str(root/'.venv/bin/python'),'-I','-B',str(stage/'host-performance-recipes.py')],'staging_root':str(stage),
 'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(manifest).hexdigest()},'inputs_count':len(rows),'external_tools':tools,
 'tool_admission_source':{'path':str(pin_path),'sha256':hashlib.sha256(pin_raw).hexdigest()},'timeout_seconds':10800,'budget':{'maximum_cases':76,'sum_case_deadline_seconds':8520,'cleanup_allowance_seconds':988,'inventory_version_and_runtime_margin_seconds':600,'total_calculated_seconds':10108,'outer_timeout_seconds':10800,'timeout_outcome':'Incomplete failed execution; never reduce recipe/repetition/sample counts to fit.'},'browser_runtime':{'name':'Chrome Headless Shell','revision':'1234','expected_version':'151.0.7922.34','executable':runtime['executable'],'complete_inventory_root':runtime['root'],'complete_file_count':20,'inventory_stage_file':'test-browser-runtime.json','pre_post_required':True,'qualification':'Test-only runtime; no old Chrome154 or native Safari/VoiceOver equivalence.'},'gate':'Execute only after TASK023 and with no concurrent owned scanner/build/browser work. Sequential fresh subprocesses; preserve full recipe counts and every admitted/refused result.','source_writes':False,'intended_writes':['Only new /private/tmp/explorer-perfdata-* canonical fixtures, private result/job files and dedicated loopback service workers. No source or shared configuration edits. Cleanup retains evidence and removes every owned runtime process.'],
 'credentials':'Bootstrap URL only in 0600 per-instance file/process memory, no raw errors, headers, response bytes, traces or HAR.',
 'scenarios':['TASK024 three complete recipes with3canonical/3Service repetitions each; exact canonical2000000/2000001byte document boundary; separate bounded service relationship-axis adjacent admission; each fully admitted shape5cold browser/5fresh-model Map and20search/entry/selection samples; source-validation profile; all5runtime raw/gzip/Brotli sizes including vendor. All measurements remain unexecuted before TASK023.']}
p=out/('host-performance-recipes-'+number+'.json');p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'manifest':job['manifest'],'inputs_count':len(rows)}))
