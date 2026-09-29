"""Read-only final delivery checks; writes evidence only in this directory."""
from pathlib import Path
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
now = datetime.now(timezone.utc).isoformat()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda path: json.loads((OUT / path).read_text())
def digest(path):
    return sha(path.read_bytes()) if path.is_file() else None
def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

baseline = read('manifests/protected-before.json')
changed = []
for name, before in baseline.items():
    p = ROOT / name
    if 'symlink' in before:
        after = {'symlink': os.readlink(p)} if p.is_symlink() else None
    elif 'absent' in before:
        after = {'absent': True} if not p.exists() and not p.is_symlink() else None
    else:
        after = {'sha256': digest(p), 'mode': stat.S_IMODE(p.stat().st_mode)} if p.is_file() and not p.is_symlink() else None
    if before != after:
        changed.append({'path': name, 'before': before, 'after': after})
additions = []
for folder in ['Tasks', 'TRDs', 'Implementation_Plans', 'MEMORY', 'ONTOLOGY', 'Roles', 'control_records']:
    for p in (ROOT / folder).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}:
            name = str(p.relative_to(ROOT))
            if name not in baseline:
                additions.append({'path': name, 'sha256': digest(p)})
allowed_additions = [r for r in additions if 'ONTGUARD-project-app-20260929' in r['path']]
session_events = {
    'control_records/curator/events/evt-7918b9ab82d7aebbd9f1acab765f07e2e7fea664cab113c70e0e753eb4601055.json': 'cd883a33fc45279c462d1089758443a1e4d32f18a84e674f44bef9caa9a0bc31',
    'control_records/curator/events/evt-82c02fc2eaaa4e7c262d817017895b312fbad59f9e2e534cc45eaef0023d4a16.json': '73a8cbeee0789bf3f4bfc7901641e7d53530543eb6cab1a7f116ae2b71f4f05e',
}
session_additions = [r for r in additions if session_events.get(r['path']) == r['sha256']]
unexpected_additions = [r for r in additions if r not in allowed_additions + session_additions]
save('final-preservation.json', {'observed_at': now, 'checked_entries': len(baseline),
    'changed': changed, 'operation_owned_additions': allowed_additions,
    'separate_session_catch_up_events': session_additions,
    'session_event_review': 'Both catch_up events predate browser acceptance, retain the same current/previous commit and have no sources. They are session checkpoint evidence, not app reading side effects.',
    'unexpected_additions': unexpected_additions,
    'status': 'preserved' if not changed and not unexpected_additions else 'failed'})
assert not changed and not unexpected_additions, 'protected record drift'

adoption = read('root-adoption.json')
latest = {r['destination']: {'source': r['source'], 'sha256': r['source_sha256'], 'mode': r['mode']} for r in adoption['files']}
installed_modes = {**read('manifests/installed-ontology-before.json'), **read('manifests/installed-initializer-before.json')}
for name, record in latest.items():
    if name in installed_modes:
        record['mode'] = installed_modes[name]['mode']
for r in read('root-layout-adoption.json')['files']:
    latest[r['destination']] = {'source': r['source'], 'sha256': r['after'], 'mode': latest.get(r['destination'], {}).get('mode', 0o644)}
for name, record in latest.items():
    p = ROOT / name
    assert digest(p) == record['sha256'], name
    if record['source']:
        assert digest(ROOT / record['source']) == record['sha256'], record['source']
        assert stat.S_IMODE(p.stat().st_mode) == record['mode'], name + ' mode'
installed_before = read('manifests/installed-ontology-before.json')
for name in adoption['preserved_preexisting_source_installed_differences']:
    prior = installed_before.get(name)
    if prior:
        assert digest(ROOT / name) == prior['sha256'], name
    else:
        assert not (ROOT / name).exists(), name

package = ROOT / 'SKILLS-depo/ontology'
build = read('production-build.json')
for row in build['inputs']['record']['files']:
    name = row['path']
    if name.startswith('$schema/'):
        p = ROOT / 'ONTOLOGY-depo/schema' / name.split('/', 1)[1]
    elif name.startswith('$tooling/'):
        p = package / 'scripts' / name.split('/', 1)[1]
    elif name.startswith('$project-app/scripts/'):
        p = package / 'scripts' / name.rsplit('/', 1)[1]
    elif name.startswith('$project-app/assets/'):
        p = package / 'assets/project-app' / name.rsplit('/', 1)[1]
    else:
        p = package / 'explorer' / name
    assert digest(p) == row['sha256'], name
packages = [package, ROOT / '.agents/skills/ontology', ROOT / 'Projects/Sys4AI-Template-Project/.agents/skills/ontology']
manifest_digest = digest(package / 'explorer/assets/manifest.json')
for selected in packages:
    manifest = selected / 'explorer/assets/manifest.json'
    assert digest(manifest) == manifest_digest, str(manifest)
    data = json.loads(manifest.read_text())
    assert data['build_id'] == build['inputs']['build_id']
    for row in data['assets']:
        assert digest(manifest.parent / row['path']) == row['sha256'], row['path']
    assert {str(p.relative_to(manifest.parent)) for p in manifest.parent.rglob('*') if p.is_file()} == {'manifest.json'} | {r['path'] for r in data['assets']}

guard = read('guard-repair-result.json')
assert guard['status'] == 'complete'
for row in guard['files']:
    assert digest(ROOT / row['path']) == row['sha256'], row['path']
sys.path.insert(0, str(ROOT / 'SKILLS-depo/init-new-project/scripts'))
import init_new_project
copied, origins, versions, renderer, policy = init_new_project.template_sources(ROOT)
neutral = json.loads((ROOT / 'Projects/Sys4AI-Template-Project/project-app.json').read_text())
assert neutral['project_id'] is None
assert not (ROOT / 'Projects/Sys4AI-Template-Project/.sys4ai/project-app').exists()
assert stat.S_IMODE((ROOT / 'Projects/Sys4AI-Template-Project/Launch Project.command').stat().st_mode) == 0o755
watch = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/template_watch.py'), 'status'], capture_output=True, text=True, check=True)
watcher = json.loads(watch.stdout)
save('watcher-restored.json', watcher)
assert watcher['loaded'] and watcher['state'] == 'running' and watcher['ready'] and not watcher['check_stale']
assert watcher['last_check']['result']['status'] == 'current'
save('final-delivery.json', {'observed_at': now, 'status': 'verified',
    'build_id': build['inputs']['build_id'], 'manifest_sha256': manifest_digest,
    'source_inputs_verified': len(build['inputs']['record']['files']),
    'destinations': [str(p.relative_to(ROOT)) for p in packages],
    'selected_root_destinations': latest,
    'preserved_existing_root_package_differences': len(adoption['preserved_preexisting_source_installed_differences']),
    'guard': {'status': guard['status'], 'operation': guard['operation_id'], 'current_bindings_match': True},
    'template_starter_files_verified': len(copied), 'template_contract': init_new_project.SETUP_CONTRACT,
    'launcher_mode': '0755', 'template_check': read('template-check.json'),
    'mode_policy': 'Existing installed-file modes are preserved; root-adoption source mode fields are not claims of chmod. New files use their selected modes and the launcher is 0755.',
    'watcher': 'restored, running and current', 'real_child_adoption': 'not performed',
    'git_publication': 'not performed'})

# Reverse traceability includes tracked changes, newly visible files, and edits
# to package files that were already untracked at intake.
before_status = set((OUT / 'manifests/git-status-before.bin').read_bytes().decode().split('\0')) - {''}
status = subprocess.run(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=ROOT, capture_output=True, check=True).stdout.decode()
current_status = set(status.split('\0')) - {''}
assert {r for r in current_status if r[0] not in {' ', '?'}} == {r for r in before_status if r[0] not in {' ', '?'}}, 'staged index changed'
paths = {r[3:] for r in current_status - before_status}
paths.update(latest)
for name in ['source-ontology-before.json', 'source-initializer-before.json', 'installed-ontology-before.json', 'installed-initializer-before.json']:
    earlier = read('manifests/' + name)
    for path, record in earlier.items():
        if digest(ROOT / path) != record.get('sha256'):
            paths.add(path)

def requirements(path):
    normalized = path.removeprefix('Projects/Sys4AI-Template-Project/').replace('.agents/skills/', 'SKILLS-depo/', 1)
    if normalized.startswith('SKILLS-depo/init-new-project/') or normalized.startswith('.template/'):
        return [23, 26, 27, 31]
    if normalized.startswith('SKILLS-depo/ontology/'):
        if '/tests/' in normalized:
            return [20, 21, 22, 27, 28, 29, 30]
        name = Path(normalized).name
        if name == 'project_app_core.py': return [1, 2, 3, 7, 8, 19, 20, 21]
        if name == 'project_app_work.py': return [6, 13, 14, 15, 20]
        if name == 'project_app_sources.py': return [5, 8, 15, 20, 21, 22]
        if name == 'project_app_search.py': return [16, 21]
        if name == 'project_app_capabilities.py': return [17, 18, 19]
        if name == 'project_app_knowledge.py': return [10, 11, 12, 16, 17]
        if name == 'project_app.py': return [19, 23, 24, 25, 28]
        if name.startswith('ontology_explorer'): return [1, 10, 19, 20, 21, 22, 25, 28]
        if '/src/' in normalized: return list(range(1, 23)) + [25, 28]
        if '/explorer/' in normalized: return [1, 22, 23, 26, 28, 31]
        if '/assets/project-app/' in normalized: return [1, 2, 3, 4, 7, 8, 19, 21, 23, 24, 26]
        if '/references/' in normalized: return [2, 7, 8, 18, 20, 23, 24, 25, 26, 27, 28, 31]
    if normalized in {'project-app.json', 'Launch Project.command', 'Project App Setup.html'}:
        return [1, 2, 3, 4, 7, 8, 19, 23, 24, 25, 26]
    if normalized.startswith(('ONTOLOGY-depo/schema/project-app-v1.json', 'reference-assets/ONTOLOGY-depo/schema/project-app-v1.json')):
        return [2, 8, 14, 15, 19, 20, 21, 22]
    if path.startswith('control_records/ontology/guard-bootstrap/ONTGUARD-project-app-20260929') or path == 'ontology-advanced.yaml':
        return [20, 21, 27, 31]
    if path in session_events: return [20, 31]
    if normalized in {'README.md', 'SPECS.md'} or path in {'SPECS-depo/project-template-README.md', 'SPECS-depo/project-template-SPECS.md', 'depot/template-update.md', 'depot/template-update.json'}:
        return [18, 23, 24, 25, 26, 27, 28, 31]
    raise AssertionError('unaccounted artifact: ' + path)

product = []
transient_count = 0
for path in sorted(paths):
    if path.startswith('Verification/shared-project-app/'):
        continue
    if path.startswith('.sys4ai/project-app/'):
        assert stat.S_IMODE((ROOT / path).stat().st_mode) & 0o077 == 0, 'runtime credential permissions'
        transient_count += 1
        continue
    product.append({'path': path, 'sha256': digest(ROOT / path),
        'requirement_ids': ['REQ-%03d' % n for n in requirements(path)]})
save('artifact-traceability.json', {'observed_at': now, 'status': 'accounted', 'product_artifacts': product,
    'app_owned_transient_files': {'count': transient_count, 'permissions': 'owner only', 'publication': 'Excluded from deliverable manifests; do not stage private .sys4ai/project-app state.'},
    'evidence_artifacts': {'root': 'Verification/shared-project-app/', 'requirement_ids': ['REQ-029', 'REQ-030', 'REQ-031'], 'purpose': 'Execution baseline, focused checks, review, exact delivery, preimages and final acceptance evidence.'},
    'preexisting_tracked_edits_preserved': ['Implementation_Plans/INDEX.md', 'TRDs/INDEX.md'],
    'planned_artifact_substitutions': {
        'home.ts': 'project-views.ts implements Home with the related supporting views.',
        'project_app_lifecycle.py': 'project_app.py implements launch, authenticated reopen and stop together.',
        'test_project_app.py': 'test_project_app_readers.py and test_project_app_service.py separate pure owner reads and transport.',
        'build-receipt.json': 'production-build.json is the exact publisher input/output receipt.',
        'existing Explorer modules': 'Unchanged API, routes, state, map and source components are reused; integration lives in project-app.ts and app.ts.'}})
print(json.dumps({'status': 'verified', 'protected_entries': len(baseline), 'selected_root_destinations': len(latest), 'template_files': len(copied), 'build_id': build['inputs']['build_id']}))
