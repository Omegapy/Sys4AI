#!/usr/bin/env python3
"""Capture reproducible local audit evidence without treating exit zero as healthy."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PYTHON = str(ROOT / '.venv/bin/python')
ONTOLOGY = '.agents/skills/ontology/scripts/ontology.py'
MEMORY = '.agents/skills/memory/scripts/memory.py'
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def snapshot(label):
    paths = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
    for name in ('.agents/skills', 'ONTOLOGY', 'MEMORY', 'Tasks', 'depot',
                 'control_records/ontology', 'control_records/memory',
                 'SKILLS-depo/ontology', 'SKILLS-depo/memory', 'ONTOLOGY-depo',
                 '.sys4ai/ontology/compiled', '.sys4ai/ontology/manifests',
                 '.sys4ai/ontology/links'):
        selected = ROOT / name
        if selected.exists():
            paths.update(str(p.relative_to(ROOT)) for p in selected.rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    paths.update(('ontology.yaml', 'ontology-advanced.yaml', 'memory.yaml',
                  'SOUL.md', 'AGENTS.md', 'ROLE.md', 'SPECS.md'))
    records = {}
    for relative in sorted(paths):
        p = ROOT / relative
        if not relative or not p.is_file() or p.is_symlink() or OUT in p.parents:
            continue
        records[relative] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                             'size': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns}
    write_json(OUT / (label + '-files.json'), records)
    (OUT / (label + '-git-status.txt')).write_bytes(subprocess.check_output(
        ['git', 'status', '--short', '--untracked-files=all'], cwd=ROOT))
    if label == 'after':
        before = json.loads((OUT / 'before-files.json').read_text())
        changed = [p for p in before if p in records and before[p]['sha256'] != records[p]['sha256']]
        missing = sorted(set(before) - set(records))
        added = sorted(set(records) - set(before))
        touched = [p for p in before if p in records and before[p]['mtime_ns'] != records[p]['mtime_ns']]
        result = {'before_count': len(before), 'after_count': len(records),
                  'changed': changed, 'missing': missing, 'added': added, 'mtime_changed': touched,
                  'preserved': not any((changed, missing, added, touched))}
        write_json(OUT / 'preservation.json', result)
        print(json.dumps(result))
    else:
        print(json.dumps({'snapshot': label, 'files': len(records)}))


def runtime_snapshot(label):
    records = {}
    for folder in ('.sys4ai/ontology', '.sys4ai/memory'):
        for p in sorted((ROOT / folder).rglob('*')):
            if p.is_file() and not p.is_symlink():
                records[str(p.relative_to(ROOT))] = {
                    'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                    'size': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns}
    for relative in ('.venv-ontology-standards/certification.json',
                     '.venv-ontology-semantic/certification.json'):
        p = ROOT / relative
        if p.is_file():
            records[relative] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                                 'size': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns}
    write_json(OUT / ('runtime-' + label + '.json'), records)
    if label == 'after':
        before = json.loads((OUT / 'runtime-before.json').read_text())
        changes = [p for p in sorted(set(before) | set(records)) if before.get(p) != records.get(p)]
        result = {'before_count': len(before), 'after_count': len(records),
                  'changed': changes, 'preserved': not changes}
        write_json(OUT / 'runtime-preservation.json', result)
        print(json.dumps(result))
    else:
        print(json.dumps({'runtime_snapshot': label, 'files': len(records)}))


def run(label, argv, timeout=180, emit=True):
    started = datetime.now(timezone.utc).isoformat()
    begin = time.monotonic()
    timed_out = False
    try:
        result = subprocess.run(argv, cwd=ROOT, env=ENV, capture_output=True, timeout=timeout)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code = error.stdout or b'', error.stderr or b'', None
        timed_out = True
    target = OUT / 'live'
    target.mkdir(exist_ok=True)
    (target / (label + '.stdout')).write_bytes(stdout)
    (target / (label + '.stderr')).write_bytes(stderr)
    receipt = {'label': label, 'command': argv, 'cwd': str(ROOT), 'started_utc': started,
               'duration_seconds': round(time.monotonic() - begin, 3),
               'exit_code': code, 'timed_out': timed_out}
    write_json(target / (label + '.receipt.json'), receipt)
    try:
        data = json.loads(stdout)
        write_json(target / (label + '.json'), data)
        receipt['observed'] = {k: data[k] for k in ('status', 'valid', 'complete', 'mutated', 'error') if k in data}
    except (json.JSONDecodeError, UnicodeDecodeError):
        receipt['output_tail'] = stdout.decode(errors='replace')[-500:]
    if emit:
        print(json.dumps(receipt), flush=True)
    return receipt


if __name__ == '__main__':
    if sys.argv[1] == 'snapshot':
        snapshot(sys.argv[2])
    elif sys.argv[1] == 'runtime-snapshot':
        runtime_snapshot(sys.argv[2])
    else:
        label, kind, *args = sys.argv[1:]
        if kind in ('ontology', 'memory'):
            argv = [PYTHON, ONTOLOGY if kind == 'ontology' else MEMORY,
                    '--project-root', str(ROOT), *args]
        else:
            argv = args
        run(label, argv)
