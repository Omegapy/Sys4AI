"""Freeze one reviewed worker-owned production-browser job; does not execute it."""
from pathlib import Path
import importlib.util
import json
import sys

ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
E=Path(__file__).absolute().parent
spec=importlib.util.spec_from_file_location('read_audit',E.parent/'process-catalog-correction/final-v3/audit.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
number=len(list(E.glob('host-browser-job-*.json')))+1
stage=Path(f'/private/tmp/explorer-narrow-layout-browser-{number:02}')
stage.mkdir()
def copy(source,relative):
    raw=a.read(source);target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
base=a.load(ROOT/'Verification/project-knowledge-explorer-first-release/service-tests/stage-browser-03-inputs.json')
for row in base['files']:
    relative=row['path']
    if relative.startswith('SKILLS-depo/ontology/explorer/assets/') or '/' not in relative:continue
    copy(ROOT/relative,relative)
for row in a.tree(ROOT/'SKILLS-depo/ontology/explorer/assets'):copy(ROOT/row['path'],row['path'])
kind=sys.argv[1] if len(sys.argv)>1 else 'narrow'
assert kind in ('narrow','advanced','bounds','neutral','session')
copy(E/f'host-{kind}.py','host-playwright-driver.py')
copy(E/f'browser-{kind}.cjs',f'browser-{kind}.cjs')
if kind in ('narrow','advanced','session'):copy(E/'fixture.py','fixture.py')
if kind=='advanced':copy(E/'mutate-snapshot.py','mutate-snapshot.py')
admission=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/qualification-headless-runtime-admission-v3.json'
runtime=a.load(admission)
for row in runtime['complete_files']:a.verify(row,Path(runtime['root']))
copy(admission,'headless-runtime.json')
bundled=Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node')
tool_paths=[ROOT/'.venv/bin/python',Path('/bin/ps'),bundled/'bin/node',*[bundled/'node_modules'/package/name for package,names in [('playwright',['package.json','index.js']),('playwright-core',['package.json','index.js','browsers.json'])] for name in names]]
tools=[]
for invoke in tool_paths:
    resolved=invoke.resolve();row=a.ref(resolved);tools.append({'path':str(invoke),'resolved':str(resolved),'sha256':row['sha256'],'bytes':row['bytes']})
for row in runtime['complete_files']:
    resolved=str(Path(runtime['root'])/row['path']);tools.append({**row,'path':resolved,'resolved':resolved})
(stage/'external-tools.json').write_text(json.dumps({'tools':tools},indent=2)+'\n')
rows=[]
for file in sorted(stage.rglob('*')):
    if file.is_file():
        row=a.ref(file);row['path']=str(file.relative_to(stage));rows.append(row)
raw=(json.dumps({'files':rows},indent=2)+'\n').encode();(stage/'inputs.json').write_bytes(raw)
(E/f'stage-browser-{number:02}-inputs.json').write_bytes(raw)
job={'kind':kind,'command':[str(ROOT/'.venv/bin/python'),'-I','-B',str(stage/'host-playwright-driver.py')], 'stage':str(stage),'manifest':{'path':str(stage/'inputs.json'),'sha256':a.sha(raw)},'inputs_count':len(rows),'runtime_manifest':a.ref(ROOT/'SKILLS-depo/ontology/explorer/assets/manifest.json'),'headless_runtime_admission':a.ref(admission),'browser':'Explicit pinned Chrome Headless Shell 151.0.7922.34; current system Chrome is not used.','timeout_seconds':180,'intended_writes':['Owned disposable synthetic fixture/private runtime/browser profile only; worker-owned exact stage remains frozen.','Safe viewport PNGs, when produced, only under a fresh /private/tmp/explorer-narrow-views-* folder after explicit bootstrap-fragment absence assertion. No trace/HAR or browser chrome capture.'],'cleanup':'Close owned page/context/browser; reap exact service/worker/descendants; compare every fixture and stage member; verify all 20 admitted browser runtime members before/after.','secret_boundary':'No launch URL, cookies, token, headers, response bodies, raw navigation errors, trace or HAR in logs. Private authentication and delayed real response stay in memory/private runtime.','scope':'Original REQ036 navigation drawer and phone details correction; actual keyboard, responsive focus, source return, theme/reduced-motion and renderer-failure behavior. No Safari, actual speech, native browser zoom, participant or whole-release claim.'}
job['external_tools']=tools
job['output_limits']={'safe_stdout_bytes':250000,'stderr_expected_bytes':0,'screenshots':'At most four viewport-only PNGs; each hash/size reported after clean-route assertion. No screenshots of browser chrome.'}
if kind=='advanced':job['intended_writes'].append('Existing bounded advanced fixture mutation: exact selected partition, docs/inert.md and ontology-explorer.yaml only; no other fixture path change.')
(E/f'host-browser-job-{number:02}.json').write_text(json.dumps(job,indent=2)+'\n')
print(json.dumps({'job':a.ref(E/f'host-browser-job-{number:02}.json'),'manifest':job['manifest'],'inputs_count':len(rows),'kind':kind,'runtime':job['runtime_manifest']}))
