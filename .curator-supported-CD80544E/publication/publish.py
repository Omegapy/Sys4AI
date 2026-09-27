"""Exact reviewed source delivery and bounded, retained owner evidence."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CANDIDATE = ROOT / '.curator-supported-CD80544E/candidate'
PACKAGE = ROOT / 'Verification/project-curator-supported-release-v1/manager/promotion-candidate-v1.json'
TEMPLATE = ROOT / 'Projects/Sys4AI-Template-Project'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def save(name, value):
    path = OUT / name
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size}

def inventory(paths):
    result = {}
    for base in paths:
        base = ROOT / base
        files = sorted(base.rglob('*')) if base.is_dir() else [base]
        for p in files:
            if p.name in {'.DS_Store'} or '__pycache__' in p.parts or p.suffix == '.pyc':
                continue
            key = p.relative_to(ROOT).as_posix()
            if p.is_symlink():
                result[key] = {'symlink': os.readlink(p)}
            elif p.is_file():
                result[key] = sha(p)
    return result

def source_check():
    package = json.loads(PACKAGE.read_text())
    assert sha(PACKAGE) == '608e04e06af7df924ab85883cde2107a3ce92f518da4f603cefef0a01f1870e0'
    assert len(package['rows']) == 90
    for row in package['rows']:
        assert sha(CANDIDATE / row['path']) == row['candidate_sha256'], row['path']
    return package

def owner(label, mode):
    cmd = [str(ROOT / '.venv/bin/python'), '-B', str(ROOT / 'tools/template_update.py'), mode]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    for suffix, data in [('stdout', result.stdout), ('stderr', result.stderr)]:
        path = OUT / (label + '.' + suffix)
        assert not path.exists(), path
        path.write_bytes(data)
    parsed = json.loads(result.stdout)
    summary = {'command': cmd, 'returncode': result.returncode, 'keys': list(parsed), 'result': parsed}
    save(label + '.json', summary)
    print(json.dumps({'label': label, 'returncode': result.returncode, 'keys': list(parsed), 'status': parsed.get('status'), 'counts': {k:len(v) for k,v in parsed.items() if isinstance(v,list)}}))
    return parsed, result.returncode

def main():
    mode = sys.argv[1]
    package = source_check()
    if mode == 'before':
        for row in package['rows']:
            assert sha(ROOT / row['path']) == row['live_current_sha256'], row['path']
        sources = [p.name for p in ROOT.iterdir() if p.is_dir() and p.name.endswith('-depo')]
        protection = ['.agents/skills','Roles','SOUL.md','ROLE.md','AGENTS.md','SPECS.md','README.md','depot/projects.json']
        snapshot = {'sources':inventory(sources + ['tools','tests','depot']), 'protected':inventory(protection), 'template':inventory(['Projects/Sys4AI-Template-Project']), 'owner_state':inventory(['.sys4ai/template-update'])}
        ref = save('before.json', snapshot)
        print(json.dumps({'snapshot':ref, 'counts':{k:len(v) for k,v in snapshot.items()}}))
        owner('before-check','check')
    elif mode == 'copy':
        checked = json.loads((OUT / 'before-check.json').read_text())
        assert checked['returncode'] == 0
        changes=[]
        for row in package['rows']:
            assert sha(ROOT / row['path']) == row['live_current_sha256'], row['path']
        for row in package['rows']:
            if not row['promotion_needed']:
                continue
            dest = ROOT / row['path']
            assert dest.resolve().is_relative_to(ROOT) and not dest.is_symlink()
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(CANDIDATE / row['path'],dest)
            assert sha(dest) == row['candidate_sha256']
            changes.append(row)
        assert len(changes)==69
        ref=save('source-copy.json',{'status':'copied_exact_package','changed_files':changes,'all_selected':[{'path':r['path'],'sha256':sha(ROOT/r['path'])} for r in package['rows']]})
        print(json.dumps({'copied':len(changes),'receipt':ref}))
    elif mode == 'check':
        owner('proposed-check','check')
    elif mode == 'apply':
        owner('apply','apply')
    elif mode == 'after':
        owner('after-check','check')
    else:
        raise ValueError(mode)

if __name__ == '__main__':
    main()
