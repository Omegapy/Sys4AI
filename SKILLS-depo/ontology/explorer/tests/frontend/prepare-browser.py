from pathlib import Path
import hashlib,json,shutil,stat,sys
ROOT=Path(__file__).resolve().parents[5];E=ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests'
number=len(list(E.glob('host-browser-job-*.json')))+1
stage=Path(f'/private/tmp/explorer-frontend-browser-{number:02}');stage.mkdir()
old=json.loads((ROOT/'Verification/project-knowledge-explorer-first-release/service-tests/stage-browser-03-inputs.json').read_text())
for row in old['files']:
 name=row['path']
 if name.startswith('SKILLS-depo/ontology/explorer/assets/') or '/' not in name:continue
 source=ROOT/name;assert source.is_file();dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
shutil.copytree(ROOT/'SKILLS-depo/ontology/explorer/assets',stage/'SKILLS-depo/ontology/explorer/assets')
advanced='--advanced' in sys.argv;neutral='--neutral' in sys.argv;visual='--visual' in sys.argv;bounds='--bounds' in sys.argv
driver=(ROOT/'Verification/project-knowledge-explorer-first-release/service-tests/host-playwright-driver.py').read_text().replace('explorer-browser-smoke','explorer-frontend-smoke').replace("str(stage/'browser-bootstrap.cjs')","str(stage/'browser-flow.cjs')").replace('time.monotonic()+60','time.monotonic()+150')
if advanced:driver=(Path(__file__).parent/'host-advanced.py').read_text()
if neutral:driver=(Path(__file__).parent/'host-neutral.py').read_text()
if visual:driver=(Path(__file__).parent/'host-visual.py').read_text()
if bounds:driver=(Path(__file__).parent/'host-bounds.py').read_text()
(stage/'host-playwright-driver.py').write_text(driver)
if bounds:shutil.copyfile(Path(__file__).parent/'browser-bounds.cjs',stage/'browser-bounds.cjs')
if visual:shutil.copyfile(Path(__file__).parent/'browser-visual.cjs',stage/'browser-visual.cjs')
if neutral:shutil.copyfile(Path(__file__).parent/'browser-neutral.cjs',stage/'browser-neutral.cjs')
if advanced:
 shutil.copyfile(Path(__file__).parent/'mutate-snapshot.py',stage/'mutate-snapshot.py')
 shutil.copyfile(Path(__file__).parent/'fixture.py',stage/'fixture.py')
 shutil.copyfile(Path(__file__).parent/'browser-advanced.cjs',stage/'browser-advanced.cjs')
shutil.copyfile(Path(__file__).parent/'browser-flow.cjs',stage/'browser-flow.cjs')
rows=[]
for file in sorted(stage.rglob('*')):
 if file.is_file():
  st=file.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1;rows.append({'path':file.relative_to(stage).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bytes':st.st_size})
raw=json.dumps({'files':rows},indent=2)+'\n';(stage/'inputs.json').write_text(raw);(E/f'stage-browser-{number:02}-inputs.json').write_text(raw)
job={'command':[str(ROOT/'.venv/bin/python'),'-I','-B',str(stage/'host-playwright-driver.py')],'stage':str(stage),'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(raw.encode()).hexdigest()},'inputs_count':len(rows),'timeout_seconds':180,'intended_writes':['Owned disposable fixture/runtime/job under /private/tmp/explorer-http-*; fresh temporary browser profile. No project/evidence writes by host.'],'cleanup':'Close owned context/browser, stop and reap service/worker, recorded exact descendant identities only; unchanged input fixtures audited.','secret_boundary':'Private URL stays in memory; no raw errors, traces, HAR, screenshots, credentials in args or logs. Fixed diagnostic checkpoints only.','scope':'Production frontend smoke; actual Chrome DOM, flows, map and CSP. No OS dispatch or manual accessibility claim.'}
if visual:
 job['intended_writes'].append('Twelve synthetic-data screenshots after positive credential-fragment removal, kept under a new private /private/tmp/explorer-frontend-views-* directory for visual review. No browser chrome or live user content.')
 job['secret_boundary']='Private URL remains in memory. No raw errors/traces/HAR. Screenshots occur only after positive fragment removal and contain synthetic fixture content.'
 job['scope']='Actual autocomplete keyboard, safe visual review captures,full-canvas and ordered-passage framing,320px dark source/process and200percent text reflow; no OS dispatch or manual assistive-technology claim.'
if advanced:
 job['scope']='Extended actual production frontend checks, including deliberately mutated disposable fixture snapshots/sources and existing exact source-owner mappings; not root preservation or human accessibility.'
 job['intended_writes'].append('For advanced cases only, the exact disposable fixture project-file paths containing focus/first relation plus docs/inert.md and ontology-explorer.yaml are modified by reviewed driver; all other fixture paths are audited unchanged.')
(E/f'host-browser-job-{number:02}.json').write_text(json.dumps(job,indent=2)+'\n');print(json.dumps(job,indent=2))
