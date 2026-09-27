from pathlib import Path
import hashlib,json,shutil,stat,sys
ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI');E=ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests/process-catalog-correction'
number=len(list(E.glob('host-browser-job-*.json')))+1
stage=Path(f'/private/tmp/explorer-process-catalog-browser-{number:02}');stage.mkdir()
old=json.loads((ROOT/'Verification/project-knowledge-explorer-first-release/service-tests/stage-browser-03-inputs.json').read_text())
for row in old['files']:
 name=row['path']
 if name.startswith('SKILLS-depo/ontology/explorer/assets/') or '/' not in name:continue
 source=ROOT/name;assert source.is_file();dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
shutil.copytree(ROOT/'SKILLS-depo/ontology/explorer/assets',stage/'SKILLS-depo/ontology/explorer/assets')
kind=sys.argv[1];assert kind in ('keyboard','catalog','advanced','bounds','neutral')
files={'keyboard':['keyboard-catalog.cjs'],'catalog':['browser-catalog.cjs','catalog-fixture.py','mutate-catalog.py'],'advanced':['browser-advanced.cjs','fixture.py','mutate-snapshot.py'],'bounds':['browser-bounds.cjs'],'neutral':['browser-neutral.cjs']}
source_dir=E if kind in ('keyboard','catalog') else ROOT/'SKILLS-depo/ontology/explorer/tests/frontend'
host=E/('host-'+kind+'.py') if kind in ('keyboard','catalog') else source_dir/('host-'+kind+'.py')
shutil.copyfile(host,stage/'host-playwright-driver.py')
for name in files[kind]:shutil.copyfile(source_dir/name,stage/name)
rows=[]
for file in sorted(stage.rglob('*')):
 if file.is_file():
  st=file.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1;rows.append({'path':file.relative_to(stage).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bytes':st.st_size})
raw=json.dumps({'files':rows},indent=2)+'\n';(stage/'inputs.json').write_text(raw);(E/f'stage-browser-{number:02}-inputs.json').write_text(raw)
job={'kind':kind,'command':[str(ROOT/'.venv/bin/python'),'-I','-B',str(stage/'host-playwright-driver.py')],'stage':str(stage),'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(raw.encode()).hexdigest()},'inputs_count':len(rows),'timeout_seconds':180,'intended_writes':['Owned disposable synthetic fixture/runtime/job under /private/tmp/explorer-http-*; fresh temporary browser profile. No project/evidence writes by host.'],'cleanup':'Close only owned context/browser and reap exact service/worker/descendants; compare frozen stage and fixture inventories.','secret_boundary':'Private bootstrap/CSRF and held real responses remain in memory/private runtime only. No URLs, raw errors, headers, trace/HAR/screenshots in diagnostics.','scope':'Current production frontend process catalog correction, exact keyboard label discovery and/or instrumented races. No native assistive technology or human comprehension claim.'}
if kind=='catalog':job['intended_writes'].append('Exactly the disposable fixture partition containing entry-00014 changes its selected label through the hash-bound Python mutation; all other fields and files must remain unchanged. Initial fixture deliberately adds two duplicate-label configured processes and a long-label configured process, leaving starting_ids unchanged.')
if kind=='advanced':job['intended_writes'].append('Existing reviewed advanced fixture mutation of exact selected partition,docs/inert.md,ontology-explorer.yaml only.')
(E/f'host-browser-job-{number:02}.json').write_text(json.dumps(job,indent=2)+'\n');print(json.dumps(job,indent=2))
