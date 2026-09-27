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
for name in ('host-performance-recipes.py','performance-case.py'):
    raw=(out/name).read_bytes();(stage/name).write_bytes(raw);rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
manifest=(json.dumps({'files':rows},indent=2)+'\n').encode();(stage/'inputs.json').write_bytes(manifest);(out/('stage-performance-recipes-'+number+'.json')).write_bytes(manifest)
tools=[]
for p in [root/'.venv/bin/python',Path('/bin/ps'),Path('/usr/sbin/sysctl'),Path('/usr/bin/sw_vers')]:
    actual=p.resolve();raw=actual.read_bytes();tools.append({'path':str(p),'resolved':str(actual),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
job={'command':[str(root/'.venv/bin/python'),'-I','-B',str(stage/'host-performance-recipes.py')],'staging_root':str(stage),
 'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(manifest).hexdigest()},'inputs_count':len(rows),'external_tools':tools,
 'timeout_seconds':1100,'gate':'Execute only after TASK023 and with no concurrent owned scanner/build/browser work. Sequential fresh subprocesses; preserve full recipe counts and every admitted/refused result.','source_writes':False,'intended_writes':['Only new /private/tmp/explorer-perfdata-* canonical fixtures, private result/job files and dedicated loopback service workers. No source or shared configuration edits. Cleanup retains evidence and removes every owned runtime process.'],
 'credentials':'Bootstrap URL only in 0600 per-instance file/process memory, no raw errors, headers, response bytes, traces or HAR.',
 'scenarios':['TASK024 complete small/representative/stress canonical-loader and Service repetitions,20 warm HTTP samples per operation for admitted shape,adjacent one-axis capacity boundary,source-validation immutable-reuse profile. Browser/compression measurement is separate.']}
p=out/('host-performance-recipes-'+number+'.json');p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'manifest':job['manifest'],'inputs_count':len(rows)}))
