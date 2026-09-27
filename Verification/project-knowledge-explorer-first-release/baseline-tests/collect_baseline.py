"""Read-only implementation baseline; writes only this evidence directory."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'Verification/project-knowledge-explorer-first-release'
LOGS = OUT / 'baseline-tests'
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')

def metadata(path):
    st = path.lstat()
    if path.is_symlink():
        return {'kind': 'symlink', 'mtime_ns': st.st_mtime_ns, 'target': os.readlink(path)}
    raw = path.read_bytes()
    return {'kind': 'file', 'sha256': digest(raw), 'mtime_ns': st.st_mtime_ns, 'size': len(raw)}

SKIP = {'.git', '__pycache__', '.DS_Store', '.sys4ai', 'node_modules', 'dist', 'build'}
TREES = ['MEMORY', 'ONTOLOGY', 'control_records', '.agents', 'Tasks',
         'Projects/Sys4AI-Template-Project', 'SKILLS-depo/ontology',
         'SKILLS-depo/init-new-project', 'ONTOLOGY-depo', 'reference-assets/ONTOLOGY-depo']
SINGLES = ['memory.yaml', 'ontology.yaml', 'ontology-advanced.yaml', 'depot/projects.json',
           'depot/template-update.json', 'tools/template_update.py', 'SOUL.md', 'AGENTS.md',
           'ROLE.md', 'SPECS.md', 'CURATOR.md', 'curator.yaml', 'curator-session.yaml',
           'Implementation_Plans/Plan_project-knowledge-explorer-full-first-release_2026-09-20_9B9964BA/plan.json',
           'TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md']

def inventory():
    paths = {ROOT / p for p in SINGLES if (ROOT / p).exists()}
    for tree in TREES:
        for parent, dirs, files in os.walk(ROOT / tree, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith('.venv'))
            for name in files:
                p = Path(parent) / name
                if name not in SKIP and not name.endswith(('.pyc', '.pyo')):
                    paths.add(p)
    return {str(p.relative_to(ROOT)): metadata(p) for p in sorted(paths)}

def run(name, argv, timeout=180):
    start = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=ROOT, env=ENV, capture_output=True, timeout=timeout)
        stdout, stderr, rc, state = p.stdout, p.stderr, p.returncode, 'completed'
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, rc, state = exc.stdout or b'', exc.stderr or b'', None, 'timeout'
    (LOGS / (name + '.stdout.log')).write_bytes(stdout)
    (LOGS / (name + '.stderr.log')).write_bytes(stderr)
    result = {'name': name, 'argv': argv, 'cwd': str(ROOT), 'environment': {'PYTHONDONTWRITEBYTECODE': '1'},
              'observed_at': now(), 'duration_seconds': round(time.monotonic()-start, 3),
              'returncode': rc, 'state': state, 'stdout_sha256': digest(stdout), 'stderr_sha256': digest(stderr),
              'stdout': str((LOGS / (name + '.stdout.log')).relative_to(ROOT)),
              'stderr': str((LOGS / (name + '.stderr.log')).relative_to(ROOT))}
    write(LOGS / (name + '.receipt.json'), result)
    print(name, state, rc, flush=True)
    return result

def main():
    if (OUT / 'baseline.json').exists():
        raise SystemExit('Refusing to overwrite an existing baseline.')
    baseline = {'schema_version': 1, 'task_id': 'TASK-20260919-1FA1F620', 'plan_task': 'TASK-001',
                'captured_at': now(), 'project_root': str(ROOT), 'worker': '/root/explorer_manager_g3/baseline_worker',
                'inventory_scope': {'trees': TREES, 'single_files': SINGLES, 'excluded_components': sorted(SKIP),
                                    'exclusions': ['virtual environments', 'independent non-Template product projects',
                                                   'runtime session credentials', 'Git internals']},
                'protected_before': inventory(), 'checks': []}
    write(OUT / 'baseline.json', baseline)
    python = '.venv/bin/python'
    ontology = '.agents/skills/ontology/scripts/ontology.py'
    commands = [
        ('git-head', ['git','rev-parse','HEAD']),
        ('git-status', ['git','status','--short','--untracked-files=all']),
        ('git-diff-stat', ['git','diff','--stat']),
        ('python-version', [python, '--version']),
        ('query-retrieval-tests', [python,'-m','unittest','discover','-s','SKILLS-depo/ontology/tests','-p','test_query_retrieval.py','-v']),
        ('publication-tests', [python,'-m','unittest','discover','-s','SKILLS-depo/ontology/tests','-p','test_publication.py','-v']),
        ('template-check', [python,'tools/template_update.py','check']),
        ('installed-core-check', [python,'.agents/skills/ontology/scripts/check_ontology.py','--project-root',str(ROOT)]),
        ('core-health', [python,ontology,'--project-root',str(ROOT),'health']),
        ('advanced-health', [python,ontology,'--project-root',str(ROOT),'advanced-health']),
        ('workbench-help', [python,ontology,'--project-root',str(ROOT),'workbench','--help']),
        ('term-task', [python,ontology,'--project-root',str(ROOT),'term','Task']),
        ('process-read', [python,ontology,'--project-root',str(ROOT),'read','urn:sys4ai:ontology:project:sys4ai-depot:curator-process']),
    ]
    for name, argv in commands:
        baseline['checks'].append(run(name, argv))
        write(OUT / 'baseline.json', baseline)
    baseline['protected_after'] = inventory()
    before, after = baseline['protected_before'], baseline['protected_after']
    baseline['protected_comparison'] = {
        'added': sorted(set(after)-set(before)), 'removed': sorted(set(before)-set(after)),
        'changed': [{'path': p, 'before': before[p], 'after': after[p]} for p in sorted(set(before)&set(after)) if before[p]!=after[p]],
        'interpretation': 'Concurrent manager Task writes must be distinguished from this worker. These commands do not grant repair or mutation authority.'}
    baseline['completed_at'] = now()
    write(OUT / 'baseline.json', baseline)

if __name__ == '__main__':
    main()
