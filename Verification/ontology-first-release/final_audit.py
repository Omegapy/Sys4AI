"""Read current release evidence; write audit reports only in this directory."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TEMPLATE = ROOT / 'Projects/Sys4AI-Template-Project'
PLAN = ROOT / 'Implementation_Plans/Plan_sys4ai-ontology-knowledge-system-first-release_2026-09-09_731308FD/plan.json'


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def inventory(base, *, distribution=False):
    base = Path(base)
    if not base.exists() and not base.is_symlink():
        return {'absent': True}
    if base.is_symlink():
        return {'symlink': str(base.readlink())}
    if base.is_file():
        return {'sha256': digest(base)}
    files, symlinks = {}, {}
    for path in sorted(base.rglob('*')):
        relative = path.relative_to(base)
        if any(p in {'.git', '__pycache__'} for p in relative.parts):
            continue
        if distribution and path.name == '.DS_Store':
            continue
        if path.is_symlink():
            symlinks[relative.as_posix()] = str(path.readlink())
        elif path.is_file():
            files[relative.as_posix()] = digest(path)
    return {'files': files, 'symlinks': symlinks}


def preservation():
    baseline = read(OUT / 'baseline.json')
    observations = []
    for relative, before in baseline['protected'].items():
        # APFS resolves the retired mixed-case name to new uppercase ONTOLOGY.
        # Compare directory entries, preserving the actual retired spelling.
        if relative == 'Ontology/' and 'Ontology' not in {p.name for p in ROOT.iterdir()}:
            after = {'absent': True}
            note = 'Exact retired directory entry Ontology remains absent; the authorized new ONTOLOGY entry is distinct in spelling.'
        else:
            after = inventory(ROOT / relative)
            note = None
        entry = {'path': relative, 'preserved': before == after,
                 'baseline_inventory_sha256': json_digest(before),
                 'current_inventory_sha256': json_digest(after),
                 'file_count': len(after.get('files', {})) if 'files' in after else int('sha256' in after),
                 'symlink_count': len(after.get('symlinks', {})), 'note': note}
        if before != after:
            entry['differences'] = {k: {'before': before.get(k), 'after': after.get(k)}
                                    for k in sorted(set(before) | set(after)) if before.get(k) != after.get(k)}
        observations.append(entry)
    plan = read(PLAN)
    result = {'schema_version': 1, 'plan_id': plan['plan_id'], 'observed_at': stamp(),
              'method': 'Reopened every protected regular file and symlink; SHA256 inventory using the same .git/__pycache__ exclusions as baseline. No production writes.',
              'baseline': 'Verification/ontology-first-release/baseline.json',
              'protected_paths': observations, 'path_count': len(observations),
              'all_preserved': all(x['preserved'] for x in observations),
              'selected_plan': {'revision': plan['revision'], 'status': plan['status'],
                               'sha256': digest(PLAN), 'preserved': digest(PLAN) == baseline['plan_sha256']},
              'root_task_state': read(OUT / 'final-root-task-status.json'),
              'retired_spelling_absent': 'Ontology' not in {p.name for p in ROOT.iterdir()},
              'new_uppercase_present': 'ONTOLOGY' in {p.name for p in ROOT.iterdir()},
              'registry_unchanged': next(x['preserved'] for x in observations if x['path'] == 'depot/projects.json')}
    write('preservation-audit.json', result)
    assert result['all_preserved'] and result['selected_plan']['preserved'], 'Preservation mismatch; inspect the report.'
    return result


def distribution():
    pairs = []
    for skill in ('ontology', 'init-new-project'):
        source = ROOT / 'SKILLS-depo' / skill
        for target in (ROOT / '.agents/skills' / skill, TEMPLATE / '.agents/skills' / skill):
            a, b = inventory(source, distribution=True), inventory(target, distribution=True)
            source_modes = {name: oct((source / name).stat().st_mode & 0o777) for name in a['files']}
            target_modes = {name: oct((target / name).stat().st_mode & 0o777) for name in b['files']}
            pairs.append({'source': str(source.relative_to(ROOT)), 'destination': str(target.relative_to(ROOT)),
                          'equal': a == b and source_modes == target_modes,
                          'file_modes_equal': source_modes == target_modes,
                          'file_count': len(a['files']), 'inventory_sha256': json_digest(a)})
    source = ROOT / 'ONTOLOGY-depo/modules/sys4ai-core/1.0.0'
    for target in (ROOT / 'ONTOLOGY-depo/starter/ONTOLOGY/modules/sys4ai-core/1.0.0',
                   ROOT / 'ONTOLOGY/modules/sys4ai-core/1.0.0', TEMPLATE / 'ONTOLOGY/modules/sys4ai-core/1.0.0'):
        a, b = inventory(source, distribution=True), inventory(target, distribution=True)
        pairs.append({'source': str(source.relative_to(ROOT)), 'destination': str(target.relative_to(ROOT)),
                      'equal': a == b, 'file_count': len(a['files']), 'inventory_sha256': json_digest(a)})
    a = inventory(ROOT / 'reference-assets/ONTOLOGY-depo', distribution=True)
    b = inventory(TEMPLATE / 'reference-assets/ONTOLOGY-depo', distribution=True)
    pairs.append({'source': 'reference-assets/ONTOLOGY-depo',
                  'destination': 'Projects/Sys4AI-Template-Project/reference-assets/ONTOLOGY-depo',
                  'equal': a == b, 'file_count': len(a['files']), 'inventory_sha256': json_digest(a)})
    promoted = read(OUT / 'change-manifest.json')['source_entries']
    source_entries = [{'path': x['destination'], 'sha256': digest(ROOT / x['destination']),
                       'matches_reviewed': digest(ROOT / x['destination']) == x['after_sha256']} for x in promoted]
    seeds = read(OUT / 'root-seed/manifest.json')['documents']
    root_entries = [{'path': x['destination'], 'sha256': digest(ROOT / x['destination']),
                     'matches_published': digest(ROOT / x['destination']) == x['sha256']} for x in seeds]
    cfg = read(TEMPLATE / 'ontology.yaml')
    neutral = {'identity_null': all(cfg['project'][k] is None for k in ('id', 'name', 'purpose', 'namespace')),
               'publication_disabled_unbound': cfg['publication'] == {'enabled': False, 'binding': None},
               'project_and_binding_graphs_empty': all(read(TEMPLATE / p)['@graph'] == [] for p in cfg['project_files'] + cfg['binding_files']),
               'no_generated_or_control_state': all(not (TEMPLATE / p).exists() for p in ('ONTOLOGY/WIKI', '.sys4ai/ontology', 'control_records/ontology')),
               'no_root_private_identity': all('urn:sys4ai:ontology:project:sys4ai-depot:' not in p.read_text()
                    for p in (TEMPLATE / 'ONTOLOGY').rglob('*') if p.is_file() and p.suffix in {'.json', '.jsonld', '.md'})}
    result = {'schema_version': 1, 'observed_at': stamp(), 'pairs': pairs,
              'reviewed_source_entries': source_entries, 'published_root_seed': root_entries,
              'template_neutrality': neutral,
              'template_update': read(OUT / 'final-template-current.json'),
              'watcher': read(OUT / 'final-watcher-status.json'),
              'all_equal': all(x['equal'] for x in pairs) and all(x['matches_reviewed'] for x in source_entries)
                  and all(x['matches_published'] for x in root_entries) and all(neutral.values())}
    result['all_equal'] = result['all_equal'] and result['template_update']['status'] == 'current' and result['watcher']['ready']
    write('distribution-parity.json', result)
    assert result['all_equal'], 'Distribution mismatch; inspect the report.'
    sys.path.insert(0, str(ROOT / '.agents/skills/ontology/scripts'))
    from ontology_core import load_project
    current = load_project(ROOT).context()
    observed = read(OUT / 'final-competency-check.json')['context']
    assert current == observed, 'The accepted root context changed.'
    write('release-candidate.json', {'schema_version': 1, 'plan_id': 'PLAN-20260909-731308FD',
          'recorded_at': stamp(), 'status': 'current', 'context': current,
          'context_matches_installed_acceptance': current == observed,
          'initializer_version': '10.0.0', 'setup_contract': 'governance-starter-v8',
          'initializer_helper_sha256': digest(ROOT / 'SKILLS-depo/init-new-project/scripts/init_new_project.py'),
          'parity_evidence': 'Verification/ontology-first-release/distribution-parity.json',
          'root_publication': 'control_records/ontology/receipts/ONTOP-root-first-release-20260909.json',
          'evidence_sequence': 'Source promotion and root publication froze these bytes before installed, memory and native observations; this final manifest reopens and confirms the same context.'})
    return result


def test_results():
    logs = ('source-ontology-tests.log', 'installed-ontology-tests.log', 'template-ontology-tests.log',
            'source-initializer-tests.log', 'installed-initializer-tests.log', 'final-root-tests.log',
            'template-contract-tests.log', 'memory-regression-tests.log', 'task-regression-tests.log')
    suites = []
    for name in logs:
        content = (OUT / name).read_text()
        run = re.search(r'Ran (\d+) tests in ([0-9.]+)s', content)
        assert run and re.search(r'^OK(?: \(skipped=\d+\))?$', content, re.M), name
        skip = re.search(r'^OK \(skipped=(\d+)\)$', content, re.M)
        suites.append({'suite': name.removesuffix('-tests.log'), 'tests_run': int(run[1]),
                       'skipped': int(skip[1]) if skip else 0, 'seconds': float(run[2]),
                       'skip_reasons': re.findall(r"\.\.\. skipped '([^']+)'", content),
                       'result': 'passed', 'log': str((OUT / name).relative_to(ROOT)),
                       'log_sha256': digest(OUT / name)})
    check = read(OUT / 'final-competency-check.json')
    assert check['valid'] and check['mutated'] is False
    write('test-results.json', {'schema_version': 1, 'observed_at': stamp(), 'all_passed': True,
          'classification': 'Deterministic local suites; actual installed/native observations have separate receipts.',
          'overlap': 'Source, root-installed and Template suites repeat the same tests against their separate copies; counts are not unique-test totals.',
          'suites': suites, 'combined_acceptance': {'valid': check['valid'],
              'competency_questions': len(check['competency']['results']),
              'evidence': 'Verification/ontology-first-release/final-competency-check.json'},
          'environment': 'Existing Python 3.12 virtual environment, PYTHONDONTWRITEBYTECODE=1; no dependency installation or new service.',
          'git_diff_check_passed': (OUT / 'final-diff-check.log').read_text() == ''})


def initializer():
    baseline = read(OUT / 'initializer-v7-preservation-baseline.json')
    fixture = OUT / 'fixtures/edition-depot/Projects'
    observations = []
    for project, groups in baseline.items():
        entries = []
        for group, files in groups.items():
            if group in {'base_receipt', 'base_receipt_sha256'}:
                continue
            if project == 'Prior-Edition' and group == 'MEMORY':
                entries.append({'group': group, 'result': 'separately_superseded_after_preserved_adoption',
                                'evidence': 'Verification/ontology-first-release/memory-integration-observations.json',
                                'note': 'The accepted record was intentionally superseded later through the real fixture memory publisher; its historical body was preserved.'})
                continue
            comparisons = [{'path': p, 'preserved': (fixture / project / p).is_file()
                            and digest(fixture / project / p) == expected} for p, expected in files.items()]
            assert all(x['preserved'] for x in comparisons), (project, group)
            entries.append({'group': group, 'result': 'preserved', 'files': comparisons})
        before_receipt = groups['base_receipt']
        current_receipt = read(fixture / project / 'control_records/project-setup.json')
        changed_receipt_keys = [k for k in sorted(set(before_receipt) | set(current_receipt))
                                if before_receipt.get(k) != current_receipt.get(k)]
        assert current_receipt['setup_contract'] == before_receipt['setup_contract']
        entries.append({'group': 'setup-receipt', 'base_edition_preserved': True,
                        'base_edition': current_receipt['setup_contract'],
                        'changed_receipt_keys': changed_receipt_keys,
                        'note': 'Explicit adoption and refresh append module_adoptions to the existing base receipt; base edition remains v7.'})
        observations.append({'project': project, 'observations': entries})
    write('initializer-observations.json', {'schema_version': 1, 'observed_at': stamp(),
          'verification_level': 'Actual installed initializer CLI in isolated disposable projects; persistent receipts reopened.',
          'new_create': 'Verification/ontology-first-release/initializer-native-create.json',
          'first_preparation': 'Verification/ontology-first-release/initializer-first-prepare.json',
          'prior_editions': read(OUT / 'initializer-edition-observations.json'),
          'refresh': read(OUT / 'initializer-refresh-observations.json'),
          'preservation': observations,
          'scope': 'All test projects belong to the disposable fixture depot. The real root project registry and independent real projects remain unchanged.',
          'runtime_boundary': 'Initializer receipts report static import/config/binding readiness separately from semantic health, live runtime and an operation-specific publication grant.'})


if __name__ == '__main__':
    operations = {'preservation': preservation, 'distribution': distribution,
                  'tests': test_results, 'initializer': initializer}
    for name in sys.argv[1:] or operations:
        operations[name]()
        print(name + ': passed')
