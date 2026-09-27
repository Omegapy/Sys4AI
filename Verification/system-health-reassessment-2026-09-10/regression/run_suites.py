#!/usr/bin/env python3
"""Capture ordinary installed test processes; no test loader or source monkeypatches."""
import argparse, datetime, hashlib, json, os, pathlib, re, subprocess, sys, time
ROOT = pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = ROOT / 'Verification/system-health-reassessment-2026-09-10/regression'
PYTHON = ROOT / '.venv/bin/python'
SELECTORS = {'PYTHONDONTWRITEBYTECODE':'1', 'GIT_OPTIONAL_LOCKS':'0', 'SYS4AI_STANDARDS_PYTHON':str(ROOT / '.venv-ontology-standards/bin/python'), 'SYS4AI_SEMANTIC_ACCEPTANCE_ROOT':str(ROOT), 'SYS4AI_TEST_DEPOT_ROOT':str(ROOT)}
SPECS = {
 'ontology':(ROOT, ['-m','unittest','discover','-s','.agents/skills/ontology/tests','-v']),
 'memory':(ROOT, ['-m','unittest','discover','-s','.agents/skills/memory/tests','-v']),
 'initializer-static':(ROOT, ['-m','unittest','discover','-s','.agents/skills/init-new-project/tests','-p','test_static_readiness.py','-v']),
 'template-contract':(ROOT / 'Projects/Sys4AI-Template-Project', ['-m','unittest','discover','-s','tests','-p','test_template_contract.py','-v']),
}
def dump(p,value): p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def source_snapshot():
    paths = set()
    for name in ['.agents/skills/ontology','.agents/skills/memory','.agents/skills/init-new-project','SKILLS-depo/ontology','SKILLS-depo/memory','SKILLS-depo/init-new-project','reference-assets/ONTOLOGY-depo','reference-assets/MEMORY-depo','Projects/Sys4AI-Template-Project/tests']:
        paths.update(p for p in (ROOT/name).rglob('*') if p.is_file() and not {'__pycache__','.DS_Store'} & set(p.parts) and p.suffix != '.pyc')
    for name in ['AGENTS.md','SOUL.md','ROLE.md','SPECS.md','Roles/project-sub-agent/AGENTS.md','Roles/project-sub-agent/ROLE.md','.agents/skills/communication/SKILL.md','Verification/system-health-reassessment-2026-09-10/PLAN.md','Verification/ontology-health-repairs/REPORT.md','Verification/ontology-health-repairs/test-discovery/REPORT.md','Verification/ontology-health-repairs/initializer/REPORT.md','Verification/ontology-health-repairs/required-test-inventory.json','SPECS-depo/template-tests/test_template_contract.py','.venv/pyvenv.cfg','.venv-ontology-standards/pyvenv.cfg','.venv-ontology-standards/certification.json','.venv-ontology-semantic/pyvenv.cfg','.sys4ai/ontology/semantic/model.json','depot/projects.json','ontology.yaml','ontology-advanced.yaml','memory.yaml']:
        paths.add(ROOT/name)
    return {str(p.relative_to(ROOT)):{'sha256':digest(p),'mtime_ns':p.stat().st_mtime_ns,'size':p.stat().st_size} for p in sorted(paths)}
def run(name):
    cwd,args = SPECS[name]; dest=OUT/name; dest.mkdir(exist_ok=True)
    before=source_snapshot(); dump(dest/'inputs-before.json',before)
    environment=os.environ.copy()
    for key in list(environment):
        if key.startswith('SYS4AI_') or key in ('PYTHONPATH','PYTHONHOME'): environment.pop(key)
    environment.update(SELECTORS)
    command=[str(PYTHON),*args]
    start=datetime.datetime.now(datetime.timezone.utc).isoformat(); mono=time.monotonic()
    with (dest/'stdout.log').open('wb') as stdout, (dest/'stderr.log').open('wb') as stderr:
        process=subprocess.Popen(command,cwd=cwd,env=environment,stdout=stdout,stderr=stderr)
        dump(dest/'running.json',{'pid':process.pid,'command':command,'cwd':str(cwd),'started_at':start,'runtime_selectors':SELECTORS})
        code=process.wait()
    elapsed=time.monotonic()-mono
    after=source_snapshot(); dump(dest/'inputs-after.json',after)
    changes=[k for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]
    raw=(dest/'stderr.log').read_text(); rows=[]
    for line in raw.splitlines():
        match=re.match(r'^(test\S*) \(([^)]+)\)(?:.*)? \.\.\. (ok|FAIL|ERROR|skipped .+|expected failure|unexpected success)$',line)
        if match:
            method,owner,outcome=match.groups()
            rows.append({'id':owner if owner.endswith('.'+method) else owner+'.'+method,'outcome':outcome})
    count=re.findall(r'^Ran (\d+) tests? in ([\d.]+)s$',raw,re.M)
    ids=[r['id'] for r in rows]
    receipt={'suite':name,'command':command,'cwd':str(cwd),'runtime_selectors':SELECTORS,'started_at':start,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':round(elapsed,6),'exit_code':code,'timed_out':False,'reported_test_count':int(count[-1][0]) if count else None,'unittest_elapsed_seconds':float(count[-1][1]) if count else None,'parsed_identity_count':len(rows),'unique_identity_count':len(set(ids)),'duplicate_identities':sorted({i for i in ids if ids.count(i)>1}),'outcome_counts':{v:sum(row['outcome']==v for row in rows) for v in sorted({row['outcome'] for row in rows})},'source_changes':changes,'stdout_sha256':digest(dest/'stdout.log'),'stderr_sha256':digest(dest/'stderr.log'),'source_before_sha256':digest(dest/'inputs-before.json'),'source_after_sha256':digest(dest/'inputs-after.json')}
    dump(dest/'test-identities.json',rows); dump(dest/'receipt.json',receipt)
    (dest/'running.json').unlink()
    print(json.dumps(receipt),flush=True)
    return code
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('suite',choices=SPECS); args=parser.parse_args();sys.exit(run(args.suite))
