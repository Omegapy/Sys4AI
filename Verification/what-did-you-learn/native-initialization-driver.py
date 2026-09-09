#!/usr/bin/env python3
"""Observed installed CLI scenarios in one explicitly isolated verification depot.

Historical v6 receipts are constructed fixtures, not production history.
The fault mode injects a process-local publication failure without editing any
initializer package; subsequent recovery uses the normal installed CLI.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE_ROOT = HERE.parents[1]
DEPOT = HERE / 'fixtures/initializer-native-depot'
TEMPLATE_REL = 'Projects/Sys4AI-Template-Project'
TEMPLATE = DEPOT / TEMPLATE_REL
INITIALIZER_REL = '.agents/skills/init-new-project/scripts/init_new_project.py'
PYTHON = Path('/opt/homebrew/bin/python3.12').resolve(strict=True)
RESULTS = HERE / 'native-initialization-results.json'
IGNORE = shutil.ignore_patterns('.git', '.venv', 'venv', 'env', 'ENV', '.sys4ai', '__pycache__', '.DS_Store', '._*', '.ruff_cache', '.pytest_cache', '*.pyc')
COMMANDS = []
CASES = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def manifest(root):
    if not root.exists():
        return {}
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = 'symlink:' + os.readlink(path)
        elif path.is_dir():
            result[relative] = 'directory'
        else:
            result[relative] = sha(path.read_bytes())
    return result


def load_helper(path):
    spec = importlib.util.spec_from_file_location('native_fixture_initializer', path)
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    spec.loader.exec_module(helper)
    return helper


def command(label, arguments, *, cwd=DEPOT, expected=0, kind='normal-installed-cli'):
    index = len(COMMANDS) + 1
    argv = [str(PYTHON), '-B', *map(str, arguments)]
    completed = subprocess.run(argv, cwd=cwd, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'GIT_OPTIONAL_LOCKS': '0', 'TMPDIR': str(DEPOT / 'tmp')},
                               text=True, capture_output=True, timeout=180, check=False)
    prefix = f'native-initializer-{index:02d}-{label}'
    stdout = HERE / (prefix + '.stdout.json')
    stderr = HERE / (prefix + '.stderr.log')
    stdout.write_text(completed.stdout)
    stderr.write_text(completed.stderr)
    observation = {'label': label, 'kind': kind, 'argv': argv, 'cwd': str(cwd), 'exit_code': completed.returncode,
                   'expected_exit_code': expected, 'stdout': stdout.name, 'stdout_sha256': sha(completed.stdout.encode()),
                   'stderr': stderr.name, 'stderr_sha256': sha(completed.stderr.encode())}
    COMMANDS.append(observation)
    assert completed.returncode == expected, observation
    result = json.loads(completed.stdout)
    observation['status'] = result.get('status')
    return result


def identity(target, project_id, name=None, purpose='Observe installed initialization and local learning capability.'):
    return {'schema_version': 1, 'project_id': project_id, 'project_name': name or project_id.replace('-', ' ').title(),
            'purpose': purpose, 'relative_path': target.relative_to(DEPOT).as_posix()}


def setup_args(mode, target, ident, *extra):
    return [mode, '--destination', target, '--project-id', ident['project_id'], '--project-name', ident['project_name'], '--purpose', ident['purpose'], *extra]


def initialize(label, mode, target, ident, *extra, expected=0):
    return command(label, [DEPOT / INITIALIZER_REL, *setup_args(mode, target, ident, *extra)], expected=expected)


def receipt(target):
    return json.loads((target / 'control_records/project-setup.json').read_text())


def immutable_base(helper, record):
    return {key: record.get(key) for key in helper.BASE_IMMUTABLE}


def history_hashes(target):
    return manifest(target / 'control_records/project-setup-history')


def assert_history_retained(before, target):
    after = history_hashes(target)
    assert all(after.get(name) == digest for name, digest in before.items())


def local_binding(target, project_id):
    raw = (target / 'memory.yaml').read_bytes()
    config = json.loads(raw)
    assert config['project']['id'] == project_id and config['project']['root'] == '.'
    assert config['contract_root'] == 'reference-assets/MEMORY-depo'
    assert config['backend'] == {'name': 'basic-memory', 'enabled': False, 'semantic_enabled': False}
    assert not any(str(SOURCE_ROOT) in str(value) for value in config['state'].values())
    binding = config['publication']['director']
    assert binding and all(sha((target / ref['path']).read_bytes()) == ref['sha256'] for ref in binding['authority'])
    return {'config_sha256': sha(raw), 'project': config['project'], 'automatic_capture': config['integration']['automatic_capture'],
            'backend': config['backend'], 'authority': binding['authority'], 'scope': binding['scope']}


def inspect_local(label, target):
    before = manifest(target)
    resolver = command(label + '-resolver', [target / '.agents/skills/what-did-you-learn/scripts/learning_contract.py', '--project-root', target])
    assert resolver['layout'] == 'installed'
    assert resolver['module']['root'] == str(target / 'reference-assets/LEARNING-depo')
    assert resolver['memory']['root'] == str(target / '.agents/skills/memory')
    assert resolver['capabilities']['manual_review'] is True and resolver['capabilities']['shared_automatic_checkpoint'] is True
    status = command(label + '-capture-status', [target / '.agents/skills/memory/scripts/memory.py', '--project-root', target, 'capture-status'])
    search = command(label + '-memory-search', [target / '.agents/skills/memory/scripts/memory.py', '--project-root', target, 'search', 'initialization readiness preservation', '--mode', 'lexical', '--limit', '5'])
    assert manifest(target) == before
    governing = ['SOUL.md', 'AGENTS.md', 'ROLE.md', '.agents/skills/what-did-you-learn/SKILL.md',
                 '.agents/skills/memory/references/automatic-capture.md', 'reference-assets/LEARNING-depo/policy.md',
                 'reference-assets/LEARNING-depo/review-contract.md', 'reference-assets/LEARNING-depo/assets/lesson-body-template.md']
    assert all((target / name).is_file() for name in governing)
    return {'root': str(target), 'resolver': resolver, 'capture_status': status, 'memory_search': search,
            'local_read_sources': {name: sha((target / name).read_bytes()) for name in governing}, 'inspection_tree_unchanged': True,
            'manual_review': 'pending native agent review of these local sources and observations'}


def seed_v6(helper, target, ident):
    proposed, sources, original = helper.source_snapshot(DEPOT, DEPOT / '.agents/skills/init-new-project', ident,
                                                       contract=helper.CAPTURE_CONTRACT, destination=target)
    for entry in sources:
        name = entry['destination']
        entry['adoption'] = 'specialized' if name in helper.SPECIALIZED_FILES and proposed[name] != original.get(name) else 'adopted'
    record = {'schema_version': 1, 'setup_contract': helper.CAPTURE_CONTRACT, 'status': 'partial', 'mode': 'create',
              'operation_id': 'project-setup-' + uuid4().hex, 'identity': ident, 'project_root': str(target), 'sources': sources,
              'owned_files': {name: sha(raw) for name, raw in proposed.items()}, 'preserved_files': {}, 'preserved_licenses': {}, 'preserved_memory': {},
              'recovery_before': {name: None for name in proposed}, 'completed_stages': [], 'active_stage': 'assets', 'checks': [],
              'created_at': datetime.now(timezone.utc).isoformat(), 'git_setup': 'separate'}
    path = target / 'control_records/project-setup.json'
    path.parent.mkdir(parents=True)
    path.write_bytes(helper.encoded(record))
    helper.validate_record(record, target, ident)
    return {'fixture_kind': 'constructed historical v6 pending receipt; not production history', 'seed_receipt_sha256': sha(path.read_bytes()),
            'operation_id': record['operation_id'], 'source_snapshot_sha256': sha(encode(sources)), 'source_count': len(sources)}


def fault_main(arguments):
    assert DEPOT.is_dir()
    helper = load_helper(DEPOT / INITIALIZER_REL)
    args = list(arguments)
    target = Path(args[args.index('--destination') + 1])
    assert target.is_relative_to(DEPOT / 'Projects')
    original = helper.atomic_write
    count = 0
    def interrupted(path, data, expected, **kwargs):
        nonlocal count
        if path.is_relative_to(target / helper.LEARNING_ROOT):
            count += 1
            if count == 2:
                raise helper.InitializationError('Deliberate native verification fault before the second learning asset publication.')
        return original(path, data, expected, **kwargs)
    helper.atomic_write = interrupted
    return helper.main(args)


def main():
    resuming_construction = DEPOT.exists()
    if resuming_construction:
        assert sorted(path.name for path in (DEPOT / 'Projects').iterdir()) == ['Sys4AI-Template-Project'], 'Refuse to replace observed project state.'
        prior = json.loads(RESULTS.read_text())
        assert prior['status'] == 'incomplete' and not prior['cases']
        COMMANDS.extend(prior['commands'])
        COMMANDS[0]['fixture_correction'] = 'Retained failed preflight; corrected isolated workspace_name to the required Sys4AI literal before any destination setup.'
    else:
        DEPOT.mkdir(parents=True)
        (DEPOT / 'tmp').mkdir()
    tempfile.tempdir = str(DEPOT / 'tmp')
    parent_registry_before = sha((SOURCE_ROOT / 'depot/projects.json').read_bytes())
    parent_config_before = sha((SOURCE_ROOT / 'memory.yaml').read_bytes())
    source_helper = load_helper(SOURCE_ROOT / INITIALIZER_REL)
    source_files, _, _, source_renderer, source_policy = source_helper.template_sources(SOURCE_ROOT)
    shutil.copytree(SOURCE_ROOT / TEMPLATE_REL, TEMPLATE, ignore=IGNORE, dirs_exist_ok=resuming_construction)
    shutil.copytree(SOURCE_ROOT / '.agents/skills/init-new-project', DEPOT / '.agents/skills/init-new-project', ignore=IGNORE, dirs_exist_ok=resuming_construction)
    registry = json.loads((SOURCE_ROOT / 'depot/projects.json').read_text())
    registry['workspace_name'] = 'Sys4AI'
    registry['projects'] = [item for item in registry['projects'] if item['id'] in {'sys4ai-depot', 'sys4ai-template-project'}]
    for item in registry['projects']:
        item['repository'] = {'status': 'not_initialized', 'remote': None}
        item['github_pages'] = {'status': 'not_configured', 'url': None}
        item['notes'] = 'Disposable local native initialization verification fixture; no independent Git or publication.'
    (DEPOT / 'depot').mkdir(exist_ok=resuming_construction)
    (DEPOT / 'depot/projects.json').write_bytes(encode(registry))
    helper = load_helper(DEPOT / INITIALIZER_REL)
    copied, _, _, renderer, policy = helper.template_sources(DEPOT)
    assert copied == source_files and renderer == source_renderer and policy == source_policy
    actual_initializer_files = source_helper.tree_files(SOURCE_ROOT / '.agents/skills/init-new-project')
    assert helper.tree_files(DEPOT / '.agents/skills/init-new-project') == actual_initializer_files
    source_evidence = {'actual_template_source_count': len(source_files), 'template_source_sha256': sha(encode({name: sha(raw) for name, raw in source_files.items()})),
                       'initializer_package_sha256': sha(encode({name: sha(raw) for name, raw in actual_initializer_files.items()})),
                       'initializer_script_sha256': sha((DEPOT / INITIALIZER_REL).read_bytes()), 'template_consumed_bytes_match': True,
                       'excluded_copy_content': ['virtual environments', 'Git metadata', 'runtime state', 'caches', 'macOS metadata'],
                       'python': str(PYTHON), 'python_version': sys.version}

    created = DEPOT / 'Projects/Created'
    created_id = identity(created, 'native-created')
    created_report = initialize('create', 'create', created, created_id)
    assert created_report['setup_contract'] == helper.SETUP_CONTRACT and created_report['status'] == 'completed'
    assert all(entry['source'].startswith(TEMPLATE_REL + '/') for entry in created_report['sources'])
    assert set(helper.tree_files(created / 'MEMORY')) == {'README.md'}
    assert not (created / '.sys4ai').exists() and not (created / '.venv').exists()
    created_case = {'case': 'actual-cli-create', 'root': str(created), 'status': 'passed', 'receipt_sha256': sha((created / helper.RECORD).read_bytes()),
                    'local_binding': local_binding(created, created_id['project_id']), 'capabilities': created_report['learning']}
    created_case['local_use'] = inspect_local('created', created)
    CASES.append(created_case)

    custom = DEPOT / 'Projects/Customized'; custom.mkdir()
    custom_id = identity(custom, 'native-custom', 'Owned project display', 'Owned purpose kept through preparation.')
    owned_identity = {**custom_id, 'owner_field': 'preserve additional identity metadata'}
    originals = {'project.json': encode(owned_identity), 'README.md': b'# Owned README\nPreserve project-specific overview.\n',
                 'SPECS.md': b'# Owned specifications\nRetain existing technical choices.\n', 'LICENSE': b'Fixture-specific existing license terms; preserve.\n',
                 'AGENTS.md': b'# Owned project instructions\nPreserve this text and established boundaries.\n',
                 'src/owned.py': b'VALUE = "project-owned-code"\n', 'Tasks/INDEX.md': b'# Owned Task index\nNo Task execution is authorized by preparation.\n'}
    for name, raw in originals.items():
        path = custom / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    for name in ('SOUL.md', 'ROLE.md'):
        shutil.copyfile(TEMPLATE / name, custom / name)
    shutil.copytree(TEMPLATE / 'Roles', custom / 'Roles')
    shutil.copytree(TEMPLATE / '.agents/skills/communication', custom / '.agents/skills/communication')
    (custom / '.agents/skills/communication/custom.txt').write_text('Keep this project-owned package extension.\n')
    before = manifest(custom)
    custom_report = initialize('custom-prepare', 'prepare-existing', custom, {**custom_id, 'project_name': 'Requested display', 'purpose': 'Requested purpose'})
    after = manifest(custom)
    allowed_before_change = {'AGENTS.md'}
    assert all(after.get(name) == digest for name, digest in before.items() if name not in allowed_before_change)
    assert (custom / 'AGENTS.md').read_bytes() == originals['AGENTS.md'] + helper.completion_link()
    assert (custom / 'project.json').read_bytes() == originals['project.json']
    assert custom_report['identity']['project_name'] == custom_id['project_name']
    assert not (custom / 'LICENSE-CODE').exists() and not (custom / 'LICENSE-DOCS').exists()
    custom_case = {'case': 'actual-cli-first-customized-prepare', 'root': str(custom), 'status': 'passed', 'before_inventory': before,
                   'preserved_original_entries': len(before) - 1, 'only_scoped_existing_change': 'AGENTS.md appended exact completion link before initial local binding',
                   'identity_bytes_preserved': True, 'local_binding': local_binding(custom, custom_id['project_id']), 'capabilities': custom_report['learning']}
    custom_case['local_use'] = inspect_local('customized', custom)
    CASES.append(custom_case)

    manual = DEPOT / 'Projects/ManualCopy'
    shutil.copytree(TEMPLATE, manual, ignore=IGNORE)
    manual_before = manifest(manual)
    manual_id = identity(manual, 'native-manual-copy')
    manual_report = initialize('manual-template-prepare', 'prepare-existing', manual, manual_id)
    manual_after = manifest(manual)
    assert all(manual_after.get(name) == digest for name, digest in manual_before.items() if name not in {'README.md', 'memory.yaml'})
    CASES.append({'case': 'actual-cli-manual-template-copy', 'root': str(manual), 'status': 'passed', 'preserved_template_copy_entries': len(manual_before) - 2,
                  'expected_specializations': ['README.md', 'memory.yaml', 'new project.json'], 'local_binding': local_binding(manual, manual_id['project_id']),
                  'capabilities': manual_report['learning']})

    snapshot = DEPOT / 'scenario-sources/current-template'
    shutil.copytree(TEMPLATE, snapshot, ignore=IGNORE)
    shutil.rmtree(TEMPLATE / helper.LEARNING_ROOT)
    shutil.rmtree(TEMPLATE / helper.LEARNING_SKILL)
    policy = json.loads((TEMPLATE / helper.TEMPLATE_POLICY).read_text())
    policy['starter_files'] = sorted(helper.required_starters(helper.CAPTURE_CONTRACT))
    (TEMPLATE / helper.TEMPLATE_POLICY).write_bytes(encode(policy))
    (TEMPLATE / '.agents/skills/memory/references/automatic-capture.md').write_text('# Constructed v6 memory-only completion fixture\nNo learning module was present in this scenario edition.\n')
    retired = TEMPLATE / '.agents/skills/memory/legacy/retired-guide.md'
    retired.parent.mkdir(); retired.write_text('Owned file present only in the constructed earlier fixture edition.\n')
    historical = {}
    for name, pid in (('PriorV6', 'native-prior-v6'), ('CaptureOff', 'native-capture-off'), ('Interrupted', 'native-interrupted')):
        target = DEPOT / 'Projects' / name; ident = identity(target, pid)
        construction = seed_v6(helper, target, ident)
        report = initialize(name.lower() + '-v6-base-recovery', 'create', target, ident)
        assert report['setup_contract'] == helper.CAPTURE_CONTRACT and report['status'] == 'completed'
        historical[name] = {'target': target, 'identity': ident, 'base': immutable_base(helper, report), 'history': history_hashes(target), 'construction': construction}
    shutil.rmtree(TEMPLATE); shutil.copytree(snapshot, TEMPLATE, ignore=IGNORE)
    assert helper.template_sources(DEPOT)[0] == source_files

    old = historical['PriorV6']; target = old['target']; ident = old['identity']
    config_before = (target / 'memory.yaml').read_bytes()
    ordinary = initialize('prior-v6-ordinary-rerun', 'create', target, ident)
    assert immutable_base(helper, ordinary) == old['base'] and not (target / helper.LEARNING_ROOT).exists()
    registry_before = (DEPOT / 'depot/projects.json').read_bytes()
    bare = initialize('prior-v6-adopt', 'prepare-existing', target, ident, '--adopt-module', helper.LEARNING_MODULE)
    assert bare['module_adoptions'][-1]['capabilities']['shared_automatic_checkpoint'] == 'unavailable'
    refreshed = initialize('prior-v6-refresh-owned-memory', 'prepare-existing', target, ident, '--adopt-module', helper.LEARNING_MODULE, '--refresh-dependency', 'memory')
    assert refreshed['module_adoptions'][-1]['capabilities']['shared_automatic_checkpoint'] == 'available'
    assert refreshed['module_adoptions'][-1]['packages']['.agents/skills/memory']['decision'] == 'refreshed-owned-package'
    assert not (target / '.agents/skills/memory/legacy/retired-guide.md').exists()
    local_edit = target / helper.LEARNING_ROOT / 'README.md'; local_edit.write_bytes(local_edit.read_bytes() + b'\nObserved post-adoption project-owned addition.\n')
    local_bytes = local_edit.read_bytes()
    repeated_bare = initialize('prior-v6-repeat-bare', 'prepare-existing', target, ident, '--adopt-module', helper.LEARNING_MODULE)
    repeated_refresh = initialize('prior-v6-repeat-refresh', 'prepare-existing', target, ident, '--adopt-module', helper.LEARNING_MODULE, '--refresh-dependency', 'memory')
    final_old = initialize('prior-v6-final-ordinary-rerun', 'create', target, ident)
    assert all(immutable_base(helper, item) == old['base'] for item in (bare, refreshed, repeated_bare, repeated_refresh, final_old))
    assert len(final_old['module_adoptions']) == 2 and (target / 'memory.yaml').read_bytes() == config_before
    assert local_edit.read_bytes() == local_bytes and (DEPOT / 'depot/projects.json').read_bytes() == registry_before
    assert_history_retained(old['history'], target)
    CASES.append({'case': 'actual-cli-prior-v6-selection-and-owned-refresh', 'root': str(target), 'status': 'passed', 'construction': old['construction'],
                  'ordinary_rerun_preserved_v6_without_learning': True, 'base_fields_preserved': True, 'config_sha256_unchanged': sha(config_before),
                  'original_history_retained': True, 'registry_bytes_unchanged_by_selection': True, 'module_operations': 2,
                  'operation_ids': [op['operation_id'] for op in final_old['module_adoptions']], 'post_adoption_edit_sha256': sha(local_bytes),
                  'final_capabilities': final_old['learning']})

    off = historical['CaptureOff']; target = off['target']; ident = off['identity']
    config_sha = sha((target / 'memory.yaml').read_bytes())
    command('capture-off-explicit-preference', [target / '.agents/skills/memory/scripts/memory.py', '--project-root', target, 'set-capture', 'off', '--expected-config-sha256', config_sha])
    (target / '.agents/skills/memory/scripts/memory_recovery.py').unlink()
    (target / '.agents/skills/memory/project-resource.txt').write_text('Preserve this incompatible custom package.\n')
    for name in ('MEMORY/retained-local.txt', 'control_records/memory/preserved-operation.json', '.sys4ai/memory/backend-config/native-sentinel.txt'):
        path = target / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('Synthetic preservation fixture; not a published memory record.\n')
    memory_before = helper.memory_inventory(target); history_before = manifest(target / 'control_records/memory'); runtime_before = manifest(target / '.sys4ai')
    config_before = (target / 'memory.yaml').read_bytes(); registry_before = (DEPOT / 'depot/projects.json').read_bytes()
    incompatible = initialize('capture-off-incompatible-adoption', 'prepare-existing', target, ident, '--adopt-module', helper.LEARNING_MODULE, '--refresh-dependency', 'memory')
    operation = incompatible['module_adoptions'][-1]
    assert operation['packages']['.agents/skills/memory']['decision'] == 'preserved-incompatible-refresh'
    assert operation['capabilities']['shared_automatic_checkpoint'] == 'off' and operation['capabilities']['manual_review'] == 'unavailable'
    assert helper.memory_inventory(target) == memory_before and manifest(target / 'control_records/memory') == history_before and manifest(target / '.sys4ai') == runtime_before
    assert (target / 'memory.yaml').read_bytes() == config_before and (DEPOT / 'depot/projects.json').read_bytes() == registry_before
    assert immutable_base(helper, incompatible) == off['base']; assert_history_retained(off['history'], target)
    CASES.append({'case': 'actual-cli-capture-off-and-incompatible-preservation', 'root': str(target), 'status': 'passed', 'construction': off['construction'],
                  'config_sha256_unchanged_after_explicit_off': sha(config_before), 'memory_inventory_preserved': memory_before,
                  'history_inventory_preserved': history_before, 'runtime_inventory_preserved': runtime_before,
                  'diagnostic': operation['packages']['.agents/skills/memory']['diagnostic'], 'capabilities': operation['capabilities']})

    fault = historical['Interrupted']; target = fault['target']; ident = fault['identity']
    extra = ['--adopt-module', helper.LEARNING_MODULE, '--refresh-dependency', 'memory']
    injected = command('injected-adoption-interruption', [Path(__file__).resolve(), '--fault-initialize', *setup_args('prepare-existing', target, ident, *extra)],
                       expected=2, kind='fault-injected-process-local-helper-cli')
    saved = receipt(target); pending = saved['module_adoptions'][-1]
    assert injected['status'] == 'partial' and saved['status'] == 'completed' and pending['status'] == 'partial'
    after_paths = [name for name, change in pending['files'].items() if change['after'] is not None and (target / name).is_file() and sha((target / name).read_bytes()) == change['after']]
    assert any(name.startswith(helper.LEARNING_ROOT + '/') for name in after_paths)
    pending_receipt_sha = sha((target / helper.RECORD).read_bytes()); history_before = history_hashes(target)
    recovered = initialize('normal-cli-exact-adoption-recovery', 'prepare-existing', target, ident, *extra)
    completed = recovered['module_adoptions'][-1]
    assert completed['status'] == 'completed' and completed['operation_id'] == pending['operation_id'] and completed['manifest_sha256'] == pending['manifest_sha256']
    assert completed['capabilities']['shared_automatic_checkpoint'] == 'available' and immutable_base(helper, recovered) == fault['base']
    assert_history_retained(history_before, target)
    files_before_repeat = {root: manifest(target / root) for root in helper.MODULE_PACKAGES}
    repeated = initialize('recovered-repeat-same-request', 'prepare-existing', target, ident, *extra)
    assert len(repeated['module_adoptions']) == 1 and repeated['module_adoptions'][-1]['operation_id'] == pending['operation_id']
    assert all(manifest(target / root) == data for root, data in files_before_repeat.items())
    CASES.append({'case': 'fault-injected-interruption-with-normal-cli-recovery', 'root': str(target), 'status': 'passed', 'construction': fault['construction'],
                  'fault_was_deliberately_injected': True, 'pending_receipt_sha256': pending_receipt_sha, 'committed_after_paths_at_interruption': after_paths,
                  'operation_id': completed['operation_id'], 'manifest_sha256': completed['manifest_sha256'], 'normal_cli_recovered_same_operation': True,
                  'repeat_preserved_packages': True, 'base_fields_and_prior_history_preserved': True, 'capabilities': completed['capabilities']})

    final_registry = json.loads((DEPOT / 'depot/projects.json').read_text())
    assert len(final_registry['projects']) == 8 and len({item['id'] for item in final_registry['projects']}) == 8
    assert all(not (DEPOT / item['path'] / '.git').exists() for item in final_registry['projects'])
    assert sha((SOURCE_ROOT / 'depot/projects.json').read_bytes()) == parent_registry_before
    assert sha((SOURCE_ROOT / 'memory.yaml').read_bytes()) == parent_config_before
    assert helper.tree_files(DEPOT / '.agents/skills/init-new-project') == actual_initializer_files
    assert source_helper.tree_files(SOURCE_ROOT / '.agents/skills/init-new-project') == actual_initializer_files
    assert source_helper.template_sources(SOURCE_ROOT)[0] == source_files
    result = {'status': 'cli-scenarios-passed-native-manual-review-pending', 'fixture_root': str(DEPOT), 'sources': source_evidence,
              'commands': COMMANDS, 'cases': CASES, 'registry': {'entries': 8, 'unique_identities': True, 'path': str(DEPOT / 'depot/projects.json')},
              'parent_preservation': {'registry_sha256': parent_registry_before, 'memory_config_sha256': parent_config_before,
                                      'registry_and_config_unchanged': True, 'actual_template_consumed_sources_unchanged': True, 'actual_installed_initializer_unchanged': True},
              'limits': ['Historical v6 is an explicitly constructed recovery fixture, not production provenance.',
                         'The interruption is deliberately injected; recovery and other setup actions are normal installed CLI processes.',
                         'No native per-operation publication grant or memory publication was attempted.',
                         'No backend, dependency, environment, model, Git repository or external resource was provisioned.']}
    RESULTS.write_bytes(encode(result))
    print(json.dumps({'status': result['status'], 'cases': len(CASES), 'commands': len(COMMANDS), 'result': str(RESULTS)}, indent=2))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fault-initialize':
        raise SystemExit(fault_main(sys.argv[2:]))
    try:
        main()
    except BaseException as exc:
        RESULTS.write_bytes(encode({'status': 'incomplete', 'error_type': type(exc).__name__, 'reason': str(exc), 'commands': COMMANDS, 'cases': CASES}))
        raise
