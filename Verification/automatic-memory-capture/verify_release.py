"""Reinspect local automatic-capture delivery and recorded test evidence."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def files(p):
    return {x.relative_to(p).as_posix(): digest(x) for x in p.rglob('*')
            if x.is_file() and '__pycache__' not in x.parts and x.name != '.DS_Store'}

checks = {}
for name in ('memory', 'init-new-project'):
    source = files(ROOT / 'SKILLS-depo' / name)
    checks[name + '_root_parity'] = source == files(ROOT / '.agents/skills' / name)
    checks[name + '_template_parity'] = source == files(ROOT / 'Projects/Sys4AI-Template-Project/.agents/skills' / name)
config = json.loads((ROOT / 'memory.yaml').read_text())
checks['root_capture_on'] = config['integration']['automatic_capture'] is True
checks['template_default_on'] = json.loads((ROOT / 'MEMORY-depo/starter/memory.yaml').read_text())['integration']['automatic_capture'] is True
checks['template_empty'] = set(files(ROOT / 'Projects/Sys4AI-Template-Project/MEMORY')) == {'README.md'}
checks['current_director_binding'] = all(digest(ROOT / r['path']) == r['sha256'] for r in config['publication']['director']['authority'])
adoption = json.loads((HERE / 'root-adoption.json').read_text())
checks['adoption_hashes'] = all(digest(ROOT / e['destination']) == e['after_sha256'] for e in adoption['entries'])
baseline = json.loads((HERE / 'baseline.json').read_text())
protected = ('Tasks/', 'Implementation_Plans/', 'TRDs/', 'Projects/Sys4AI-Electronics-Projects/', 'Verification/project-memory/')
changed_protected = [p for p, old in baseline.items() if (p.startswith(protected) or p == 'depot/projects.json' or '/to-trd/' in p)
                     and (not (ROOT / p).is_file() or digest(ROOT / p) != old)]
checks['protected_history_and_projects_unchanged'] = not changed_protected
runs = []
for name in ('source-memory-tests.txt', 'source-initializer-tests-final.txt', 'installed-memory-tests.txt',
             'installed-initializer-cli-tests.txt', 'repository-tests.txt', 'template-tests.txt'):
    raw = (HERE / name).read_text()
    match = re.search(r'Ran (\d+) tests? in ([\d.]+)s', raw)
    passed = bool(match and re.search(r'^OK(?: \(skipped=\d+\))?$', raw, re.M))
    checks[name] = passed
    runs.append({'log': str((HERE / name).relative_to(ROOT)), 'sha256': digest(HERE / name),
                 'run': int(match[1]) if match else None,
                 'skipped': int(m[1]) if (m := re.search(r'OK \(skipped=(\d+)\)', raw)) else 0, 'passed': passed})
command = [str(ROOT / '.venv/bin/python'), 'tools/template_update.py', 'check']
result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
(HERE / 'template-final-check.json').write_text(result.stdout)
checks['template_current'] = result.returncode == 0 and json.loads(result.stdout)['status'] == 'current'
assert all(checks.values()), {k: v for k, v in checks.items() if not v}
artifacts = ['memory.yaml', '.agents/skills/memory/scripts/memory_capture.py',
             '.agents/skills/memory/scripts/memory_core.py', '.agents/skills/init-new-project/scripts/init_new_project.py',
             'reference-assets/MEMORY-depo/schema/config-v1.json']
report = {'schema_version': 1, 'claim_level': 'verified_outcome', 'outcome': 'passed',
          'observed_at': datetime.now(timezone.utc).isoformat(),
          'command': '.venv/bin/python Verification/automatic-memory-capture/verify_release.py',
          'artifacts': [{'path': p, 'sha256': digest(ROOT / p)} for p in artifacts],
          'details': {'checks': checks, 'tests': runs,
                      'requirements': {f'R{i}': 'passed' for i in range(1, 7)}},
          'limitations': ['Automatic capture is an agent completion workflow, not a background scheduler.',
                         'Initializer and first-capture integration ran in disposable projects; native receipts in those tests are fixtures.',
                         'No sub-agents were launched. Existing product projects were not upgraded.',
                         'One case-sensitive-filesystem check was skipped in each applicable suite on this case-insensitive volume.',
                         'No Git publication was performed for this change.']}
(HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': 'passed', 'checks': len(checks), 'tests': runs}, indent=2))
