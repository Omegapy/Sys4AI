"""Repeat the original live audit and observe the enabled final runtime scope."""
from pathlib import Path
import hashlib
import json
import sys
import subprocess

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
from execution import run, save
sys.path.insert(0, str(ROOT / '.agents/skills/ontology/scripts'))


def snapshot():
    names = set(json.loads((OUT / 'baseline.json').read_text())['files'])
    for prefix in ('.agents/skills', 'ONTOLOGY', 'MEMORY', 'Tasks', 'Roles', 'control_records',
                   '.sys4ai/ontology', '.sys4ai/memory', 'SKILLS-depo/ontology', 'SKILLS-depo/memory',
                   'SKILLS-depo/init-new-project'):
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT / prefix).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    records = {}
    for name in sorted(names):
        p = ROOT / name
        if OUT in p.parents or not p.is_file() or p.is_symlink():
            continue
        records[name] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                         'mtime_ns': p.stat().st_mtime_ns, 'size': p.stat().st_size}
    return records


def main():
    before = snapshot()
    save(OUT / 'live' / 'before.json', before)
    results = []
    for receipt_path in sorted((ROOT / 'Verification/system-health-2026-09-10/live').glob('*.receipt.json')):
        receipt = json.loads(receipt_path.read_text())
        label = 'live-' + receipt_path.name.removesuffix('.receipt.json')
        code = run(label, receipt['command'], timeout=120)
        results.append({'label': label, 'exit_code': code})
    memory = [str(ROOT / '.venv/bin/python'), '.agents/skills/memory/scripts/memory.py', '--project-root', str(ROOT)]
    for label, args in [('memory-operational', ['health', '--level', 'operational']),
                        ('memory-hybrid', ['search', 'automatic capture', '--mode', 'hybrid']),
                        ('memory-historical', ['search', 'lexical', '--historical', '--mode', 'lexical'])]:
        results.append({'label': 'live-' + label, 'exit_code': run('live-' + label, memory + args, timeout=120)})
    from ontology_workbench import Workbench, assess_service
    service = Workbench(ROOT, authority=None, port=0).start()
    origin = service.origin
    try:
        started = assess_service(ROOT, origin)
        save(OUT / 'live' / 'workbench-running.json', started)
        assert started['running'] is True, started
        command = [str(ROOT / '.venv/bin/python'), '.agents/skills/ontology/scripts/ontology.py',
                   '--project-root', str(ROOT), 'advanced-health', '--level', 'operational', '--workbench-url', origin]
        results.append({'label': 'live-advanced-operational', 'exit_code': run('live-advanced-operational', command, timeout=120)})
    finally:
        service.close()
    stopped = assess_service(ROOT, origin)
    save(OUT / 'live' / 'workbench-stopped.json', stopped)
    assert not service.thread.is_alive() and stopped['running'] is False
    after = snapshot()
    save(OUT / 'live' / 'after.json', after)
    delta = {'changed': [p for p in before if p in after and before[p]['sha256'] != after[p]['sha256']],
             'touched': [p for p in before if p in after and before[p]['mtime_ns'] != after[p]['mtime_ns']],
             'added': sorted(set(after) - set(before)), 'removed': sorted(set(before) - set(after))}
    preservation = {'before_count': len(before), 'after_count': len(after), **delta,
                    'preserved': not any(delta.values())}
    save(OUT / 'live' / 'preservation.json', preservation)
    result = {'commands': results, 'required_command_count': len(results),
              'workbench': {'running_observed': True, 'owned_service_stopped': True, 'persistent_session': False},
              'preservation': preservation,
              'status': 'passed' if preservation['preserved'] and all(r['exit_code'] == 0 for r in results) else 'failed'}
    save(OUT / 'live' / 'result.json', result)
    print(json.dumps({'status': result['status'], 'commands': len(results), 'preservation': preservation}), flush=True)
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
