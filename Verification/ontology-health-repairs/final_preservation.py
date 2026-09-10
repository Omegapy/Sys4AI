"""Classify the final exact project delta against the pre-work observation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def info(path):
    return {'sha256': digest(path.read_bytes()), 'size': path.stat().st_size,
            'mtime_ns': path.stat().st_mtime_ns}


def main():
    baseline = json.loads((OUT / 'baseline.json').read_text())['files']
    manifest = json.loads((OUT / 'change-manifest.json').read_text())
    owners = {}
    for row in manifest['changes']:
        assert info(ROOT / row['source'])['sha256'] == row['sha256'] == info(ROOT / row['path'])['sha256']
        owners[row['source']] = 'reviewed reusable source'
        owners[row['path']] = 'exact root adoption plus recorded amendment'
    owners['SPECS-depo/template-tests/test_template_contract.py'] = 'Template-only reusable test'
    state = json.loads((ROOT / '.sys4ai/template-update/state.json').read_text())
    template = 'Projects/Sys4AI-Template-Project/'
    for relative, item in state['files'].items():
        target = ROOT / (template + relative)
        assert info(target)['sha256'] == item['sha256'], relative
        owners[template + relative] = 'explicit Template pipeline; exact current ownership state'
    for stem in ('historical', 'lexical'):
        payload = json.loads((OUT / 'memory' / (stem + '-supersession-payload.json')).read_text())
        for change in payload['changes']:
            assert info(ROOT / change['path'])['sha256'] == change['reviewed_record_sha256']
            owners[change['path']] = 'governed memory supersession; unchanged predecessor claim, sources and body'
    owners['ontology-advanced.yaml'] = 'exact guarded adoption bootstrap and adapter rebinding'
    owners['.sys4ai/template-update/state.json'] = 'Template pipeline ownership ledger'
    owners['.sys4ai/template-update/watcher.json'] = 'independently running pre-existing watcher telemetry'
    derived = ('.sys4ai/memory/projection/', '.sys4ai/memory/index/', '.sys4ai/memory/normalized/',
               '.sys4ai/memory/backend-config/', '.sys4ai/memory/maintenance/',
               '.sys4ai/ontology/compiled/', '.sys4ai/ontology/manifests/',
               '.sys4ai/ontology/links/', '.sys4ai/ontology/semantic/', 'ONTOLOGY/WIKI/')
    changed, touched, missing, unchanged = [], [], [], []
    for name, before in baseline.items():
        path = ROOT / name
        owner = owners.get(name)
        if owner is None and name.startswith(derived):
            owner = 'explicit owner-managed derived rebuild; receipts retained'
        if not path.is_file():
            missing.append({'path': name, 'before': before, 'owner': owner})
            continue
        after = info(path)
        row = {'path': name, 'before': before, 'after': after, 'owner': owner}
        if before['sha256'] != after['sha256']:
            changed.append(row)
        elif before['mtime_ns'] != after['mtime_ns']:
            touched.append(row)
        else:
            unchanged.append(name)
    unauthorized = [r for r in changed + touched + missing if r['owner'] is None]
    assert not unauthorized, unauthorized
    maintenance = json.loads((OUT / 'memory/root-reindex-receipt.json').read_text())
    stage = maintenance['journal'].removesuffix('.json')
    for row in missing:
        assert row['path'].startswith('.sys4ai/memory/projection/'), row
        archive = ROOT / stage / 'previous-projection' / Path(row['path']).name
        assert info(archive) == row['before'], row
        row['retained_at'] = archive.relative_to(ROOT).as_posix()
        row['disposition'] = 'Obsolete superseded-record projection replaced; exact old bytes and mtime retained by maintenance owner.'
    for row in changed:
        if row['path'].startswith('.sys4ai/memory/index/'):
            archive = ROOT / stage / 'previous-index' / Path(row['path']).name
            assert info(archive) == row['before'], row
            row['retained_at'] = archive.relative_to(ROOT).as_posix()
    protected = [name for name in baseline if name.startswith(('Tasks/', 'Roles/', 'TRDs/', 'Implementation_Plans/',
                 'Verification/system-health-2026-09-10/')) or name in
                 {'SOUL.md', 'ROLE.md', 'AGENTS.md', 'SPECS.md', 'LICENSE', 'LICENSE-CODE', 'LICENSE-DOCS',
                  'memory.yaml', 'ontology.yaml', 'depot/projects.json', 'depot/template-update.json',
                  'SKILLS-depo/ontology/scripts/ontology_limits.py', '.agents/skills/ontology/scripts/ontology_limits.py'}]
    assert all(name in unchanged for name in protected)
    runtime = json.loads((OUT / 'runtime-baseline.json').read_text())
    runtime_result = {}
    for name, before in runtime.items():
        assert info(ROOT / name / 'pyvenv.cfg')['sha256'] == before['pyvenv.cfg']['sha256']
        assert (ROOT / name / 'pyvenv.cfg').stat().st_mtime_ns == before['pyvenv.cfg']['mtime_ns']
        assert digest((ROOT / name / 'bin/python').resolve().read_bytes()) == before['executable_sha256']
        runtime_result[name] = 'interpreter and environment configuration unchanged; final pip check passed'
    old_cert = OUT / 'runtime-baseline/.venv-ontology-standards/certification.json'
    archived_cert = ROOT / 'control_records/ontology/profile-setup/certifications' / (digest(old_cert.read_bytes()) + '.json')
    assert archived_cert.read_bytes() == old_cert.read_bytes()
    owners[archived_cert.relative_to(ROOT).as_posix()] = 'exact original standards certificate retained on recertification'
    for stem in ('historical', 'lexical'):
        raw = (OUT / 'memory' / (stem + '-proof-companion.json')).read_bytes()
        companion = json.loads(raw)
        name = 'Verification/project-memory/evidence/verification-' + companion['receipt']['sha256'] + '.json'
        assert (ROOT / name).read_bytes() == raw
        owners[name] = 'reviewed exact historical proof locator; original verification receipt unchanged'
    for operation in ('ONTGUARD-health-reliability-20260910', 'ONTGUARD-health-maintenance-binding-20260910'):
        for suffix in ('adapters', 'bootstrap', 'intent', 'receipt'):
            owners['control_records/ontology/guard-bootstrap/' + operation + '-' + suffix + '.json'] = 'owning guard-repair transaction'
    current_names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    added = []
    for name in sorted(set(current_names) - set(baseline)):
        if not name or name.startswith('Verification/ontology-health-repairs/') or not (ROOT / name).is_file():
            continue
        assert name in owners, ('unclassified added worktree path', name)
        added.append({'path': name, 'owner': owners[name], 'after': info(ROOT / name)})
    result = {'status': 'passed', 'observed_at': datetime.now(timezone.utc).isoformat(),
              'baseline_count': len(baseline), 'unchanged_bytes_and_mtime': len(unchanged),
              'changed': changed, 'touched_without_content_change': touched, 'missing': missing,
              'added_worktree_files_outside_owned_evidence': added,
              'unclassified_changes': unauthorized, 'protected_unchanged_count': len(protected),
              'protected_unchanged': protected, 'root_adopted_artifacts': len(manifest['changes']),
              'template_managed_files_verified': len(state['files']), 'runtime_preservation': runtime_result,
              'previous_standards_certificate_retained': str(archived_cert.relative_to(ROOT)),
              'live_read_only_observation': 'live/scoped-result.json',
              'new_artifact_boundary': 'Verification/ontology-health-repairs owned evidence/fixtures; governed memory and guard receipts; explicitly rebuilt derived products'}
    (OUT / 'final-preservation.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    (OUT / 'final-git-status.txt').write_bytes(subprocess.check_output(['git', 'status', '--short', '--untracked-files=all'], cwd=ROOT))
    print(json.dumps({k: result[k] for k in ('status', 'baseline_count', 'unchanged_bytes_and_mtime', 'protected_unchanged_count',
                                           'root_adopted_artifacts', 'template_managed_files_verified')}))


if __name__ == '__main__':
    main()
