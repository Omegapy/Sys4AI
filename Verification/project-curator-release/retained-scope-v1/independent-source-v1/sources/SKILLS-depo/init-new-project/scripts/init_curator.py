"""Neutral v10 Curator capability and exact adoption through the setup owner.

This inspector parses source/configuration only. Runtime authority, host setup,
Task activation and owner publication remain separate selected operations.
"""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

MODULE = 'project-curator'
EDITION = 'governance-starter-v10'
CONFIG = 'curator.yaml'
REFERENCE = 'reference-assets/CURATION-depo'
ROLES = ('curator-manager', 'documentation-curator', 'knowledge-curator', 'improvement-maintenance')
SKILLS = ('curate', 'agent-task', 'task', 'memory', 'ontology', 'what-did-you-learn', 'manage-subagent-roles', 'init-new-project')
PACKAGES = tuple('.agents/skills/' + name for name in SKILLS) + (REFERENCE,) + tuple('Roles/' + name for name in ROLES)
SPECIAL_FILES = {CONFIG, 'CURATOR.md', 'document-ownership.json', 'Roles/INDEX.md'}
STARTERS = {CONFIG, 'CURATOR.md', 'document-ownership.json'}
RESOURCES = {REFERENCE + '/contract.json', *('.agents/skills/' + name + '/SKILL.md' for name in SKILLS),
             *('Roles/' + name + '/' + leaf for name in ROLES for leaf in ('AGENTS.md', 'ROLE.md'))}
FROZEN = ('new_curator_files', 'protected_inventory', 'prerequisites')


def fail(h, condition, message):
    if not condition: raise h.InitializationError(message)


def source_files(h, depot):
    original = h.template_sources(depot)[0]
    return {name: raw for name, raw in original.items() if name in SPECIAL_FILES or any(name.startswith(root + '/') for root in PACKAGES)}


def validate_static(h, files, *, neutral, identity=None):
    fail(h, STARTERS | RESOURCES <= files.keys(), 'Curator requires its complete charter, configuration, owner packages and paired roles')
    contract = h.unique_json(files[REFERENCE + '/contract.json'])
    fail(h, contract.get('schema_version') == 2 and contract.get('module_id') == MODULE and contract.get('configuration_schema') == 1,
         'unsupported Curator application contract')
    required = {'.agents/skills/curate/' + name for name in contract['required_skill_resources']} | {REFERENCE + '/' + name for name in contract['required_contract_resources']}
    fail(h, required <= files.keys(), 'Curator application resource closure is incomplete: ' + ', '.join(sorted(required - files.keys())))
    cfg = h.unique_json(files[CONFIG]); starter = h.unique_json(files[REFERENCE + '/starter/curator.yaml'])
    fail(h, isinstance(cfg, dict) and set(cfg) == set(starter) and cfg.get('schema_version') == 1 and cfg.get('module_id') == MODULE and cfg.get('module_version') == '1.0.0',
         'unsupported Curator configuration')
    fail(h, isinstance(cfg['project'], dict) and set(cfg['project']) == {'id', 'repository_id', 'coordination_root'}, 'unsupported Curator identity')
    if neutral:
        fail(h, cfg == starter and all(value is None for value in cfg['project'].values()), 'Template Curator must remain neutral and unselected')
    else:
        fail(h, identity is not None and cfg['project']['id'] == identity['project_id'], 'Curator destination identity mismatch')
        root = cfg['project']['coordination_root']
        fail(h, isinstance(root, str) and Path(root).is_absolute(), 'Curator destination requires an absolute selected preparation root')
    # Static installation cannot make runtime or standing permissions current.
    for key in set(starter) - {'project'}:
        fail(h, cfg[key] == starter[key], 'Curator adoption preserves only neutral inactive configuration; select configured-state repair separately: ' + key)
    ownership = h.unique_json(files['document-ownership.json'])
    fail(h, isinstance(ownership, dict) and ownership.get('schema_version') == 1 and isinstance(ownership.get('entries'), list), 'unsupported documentation ownership map')
    for name in sorted(files):
        if name.endswith('.py'):
            try: ast.parse(files[name], filename=name)
            except (SyntaxError, UnicodeError) as error: raise h.InitializationError('Curator owner source syntax is invalid: ' + name) from error
    for name, entries in contract['owner_entry_points'].items():
        fail(h, name in files, 'Curator owner adapter is missing: ' + name)
        functions = {node.name for node in ast.walk(ast.parse(files[name], filename=name)) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        fail(h, set(entries) <= functions, 'Curator owner adapter entry points are incompatible: ' + name)
    return cfg


def specialize(h, raw, identity, *, destination=None):
    fail(h, destination is not None and Path(destination).is_absolute(), 'Select the exact destination before specializing Curator identity')
    cfg = deepcopy(h.unique_json(raw))
    cfg['project'] = {'id': identity['project_id'], 'repository_id': None,
                      'coordination_root': str(destination)}
    return h.encoded(cfg)


def protected_inventory(h, destination, *, changed=()):
    result = {}
    for root in ('MEMORY', 'ONTOLOGY', 'Tasks', 'control_records/curator', '.sys4ai/curator', 'Roles'):
        result.update(h.package_inventory(destination, root))
    result.update(h.license_inventory(destination))
    for name in (h.IDENTITY, 'SOUL.md', 'AGENTS.md', 'ROLE.md', 'memory.yaml', 'ontology.yaml', 'ontology-advanced.yaml', *STARTERS):
        path = h.destination_file(destination, name)
        if path.exists(): result[name] = h.sha(h.file_bytes(path))
    # New role packages and the generated index are exact selected targets.
    return {name: value for name, value in result.items() if name not in changed and not any(name == root or name.startswith(root + '/') for root in PACKAGES if root.startswith('Roles/'))}


def check_protected(h, destination, operation):
    fail(h, protected_inventory(h, destination, changed=operation['files']) == operation['protected_inventory'],
         'Curator adoption observed changed authored records, settings, roles, identity or licensing')


def proposed_files(h, destination, identity, original, *, new_curator_files):
    proposed = {name: raw for name, raw in original.items() if any(name.startswith(root + '/') for root in PACKAGES)}
    for name in new_curator_files: proposed[name] = specialize(h, original[name], identity, destination=destination) if name == CONFIG else original[name]
    role_files = {name: h.file_bytes(h.destination_file(destination, name)) for name, value in h.package_inventory(destination, 'Roles').items() if value != 'directory' and name != 'Roles/INDEX.md'}
    role_files.update(proposed)
    role_files['SOUL.md'] = h.file_bytes(h.destination_file(destination, 'SOUL.md'))
    proposed['Roles/INDEX.md'] = h.role_index_bytes(role_files, required=True, contract=EDITION)
    return proposed


def plan(h, depot, destination, record, previous_raw):
    original = source_files(h, depot); validate_static(h, original, neutral=True)
    h.exact_role_root(destination, 'Roles')
    new_files = sorted(name for name in STARTERS if not h.destination_file(destination, name).exists())
    existing = {name: h.file_bytes(h.destination_file(destination, name)) for name in STARTERS if name not in new_files}
    if CONFIG in existing:
        validate_static(h, {**original, **existing}, neutral=False, identity=record['identity'])
        fail(h, h.unique_json(existing[CONFIG])['project']['coordination_root'] == str(destination), 'relocated Curator identity requires separately selected reconciliation')
    proposed = proposed_files(h, destination, record['identity'], original, new_curator_files=new_files)
    owned = h.module_owned_files(record); packages, changes = {}, {}
    for root in PACKAGES:
        before = h.package_inventory(destination, root)
        after = h.inventory_from_files(root, {name: raw for name, raw in proposed.items() if name.startswith(root + '/')})
        prior = {name: value for name, value in owned.items() if name.startswith(root + '/')}
        expected = h.inventory_from_files(root, prior) if prior else {}
        if not before:
            fail(h, not prior, 'missing receipt-owned Curator dependency requires exact repair: ' + root); decision = 'adopted'
        elif before == after: decision = 'preserved-package'
        elif prior and before == expected: decision = 'refreshed-owned-package'
        else: raise h.InitializationError('customized, partial or unowned package preserved; exact compatible adoption requires selected repair: ' + root)
        fail(h, not any((before[name] == 'directory') != (after[name] == 'directory') for name in before.keys() & after.keys()), 'Curator package type transition requires separate repair')
        packages[root] = {'decision': decision, 'before': before, 'after': after, 'diagnostic': None}
        if decision != 'preserved-package':
            for name in sorted(before.keys() | after.keys()):
                if before.get(name) != 'directory' and after.get(name) != 'directory': changes[name] = {'before': before.get(name), 'after': after.get(name)}
    for name in [*new_files, 'Roles/INDEX.md']:
        path = h.destination_file(destination, name); before = h.sha(h.file_bytes(path)) if path.exists() else None
        after = h.sha(proposed[name])
        generated_before = False
        if name == 'Roles/INDEX.md' and before is not None:
            current_roles = {key: h.file_bytes(h.destination_file(destination, key)) for key,value in h.package_inventory(destination, 'Roles').items() if value != 'directory' and key != name}
            current_roles['SOUL.md'] = h.file_bytes(h.destination_file(destination, 'SOUL.md'))
            current_roles[h.ROLE_HELPER] = original[h.ROLE_HELPER]
            generated_before = h.sha(h.role_index_bytes(current_roles, required=True, contract=EDITION)) == before
        fail(h, before is None or before == after or owned.get(name) == before or generated_before, 'customized Curator standalone resource preserved: ' + name)
        if before != after: changes[name] = {'before': before, 'after': after}
    preserved = {}
    for name in (h.IDENTITY, 'SOUL.md', 'AGENTS.md', 'ROLE.md', 'memory.yaml', 'ontology.yaml', 'ontology-advanced.yaml', *SPECIAL_FILES):
        path = h.destination_file(destination, name)
        if name not in changes and path.exists(): preserved[name] = h.sha(h.file_bytes(path))
    sources = []
    for name, raw in sorted(original.items()):
        root = next((root for root in PACKAGES if name.startswith(root + '/')), None)
        final = changes[name]['after'] if name in changes else packages[root]['after'].get(name) if root else preserved.get(name)
        adoption = ('specialized' if name in {CONFIG, 'Roles/INDEX.md'} else 'adopted') if name in changes else 'preserved-project-owned' if final else 'skipped-existing-package'
        sources.append({'source': h.TEMPLATE + '/' + name, 'destination': name, 'source_sha256': h.sha(raw), 'source_version': 'sha256:' + h.sha(raw), 'destination_sha256': final, 'adoption': adoption})
    checksum = h.sha(previous_raw)
    operation = {'schema_version': 1, 'module_id': MODULE, 'module_version': '1.0.0', 'operation_id': 'module-adoption-' + uuid4().hex,
                 'project_root': str(destination), 'identity': deepcopy(record['identity']),
                 'base_receipt': {'path': 'control_records/project-setup-history/' + checksum + '.json', 'sha256': checksum},
                 'refresh_dependencies': [], 'new_memory': False, 'sources': sources, 'packages': packages, 'files': changes,
                 'preserved_files': preserved, 'new_curator_files': new_files, 'protected_inventory': protected_inventory(h, destination, changed=changes),
                 'prerequisites': [{'module_id': name, 'disposition': 'existing-owner-compatible-package'} for name in ('task', 'memory', 'ontology', 'learning')],
                 'status': 'partial', 'completed_stages': [], 'active_stage': 'assets', 'checks': [], 'created_at': datetime.now(timezone.utc).isoformat()}
    operation['manifest_sha256'] = h.sha(h.encoded({key: operation[key] for key in h.module_frozen(operation)}))
    return operation, proposed


def selected_source_files(h, depot, operation): return source_files(h, depot)


def validate_operation(h, destination, operation):
    fail(h, isinstance(operation['new_curator_files'], list) and operation['new_curator_files'] == sorted(set(operation['new_curator_files'])) and set(operation['new_curator_files']) <= STARTERS,
         'invalid Curator missing-resource selection')
    fail(h, operation['prerequisites'] == [{'module_id': name, 'disposition': 'existing-owner-compatible-package'} for name in ('task', 'memory', 'ontology', 'learning')], 'invalid Curator existing-owner prerequisites')
    for name in STARTERS:
        change = operation['files'].get(name)
        fail(h, (change is not None and change['before'] is None and change['after'] is not None) if name in operation['new_curator_files'] else change is None, 'Curator cannot overwrite an existing charter, configuration or ownership map')
    fail(h, isinstance(operation['protected_inventory'], dict), 'Curator lacks authored-resource preservation evidence')
    for name, value in operation['protected_inventory'].items():
        fail(h, isinstance(name, str) and Path(name).as_posix() == name and not Path(name).is_absolute() and '..' not in Path(name).parts and name not in operation['files'] and isinstance(value, str) and (value == 'directory' or h.SHA256.fullmatch(value)), 'invalid Curator protected inventory')
        h.safe(destination / name)


def assess(h, destination):
    result = {'module_id': MODULE, 'module_version': '1.0.0', 'installed': False, 'configured': False, 'authorized': False,
              'compatible': False, 'structural_readiness': 'unavailable', 'runtime_observed': False, 'runtime': 'not-exercised',
              'inspector_execution': 'none', 'publication_enabled': False, 'diagnostics': [],
              'compatibility_scope': 'static-package-only',
              'connected_application': {'state': 'unavailable', 'code': 'application_interface_unavailable'}}
    try:
        files = {name: h.file_bytes(h.destination_file(destination, name)) for root in PACKAGES for name, value in h.package_inventory(destination, root).items() if value != 'directory'}
        for name in SPECIAL_FILES: files[name] = h.file_bytes(h.destination_file(destination, name))
        result['installed'] = STARTERS <= files.keys()
        locked = h._static('inventory').get('curator_locked_resources', {})
        fail(h, bool(locked) and all(name in files and h.sha(files[name]) == expected for name,expected in locked.items()),
             'Curator owner code differs from its reviewed compatibility inventory; customized code is preserved without execution')
        identity = h.unique_json(h.file_bytes(h.destination_file(destination, h.IDENTITY)))
        cfg = validate_static(h, files, neutral=False, identity=identity)
        fail(h, cfg['project']['coordination_root'] == str(destination), 'Curator coordination root changed; reconcile relocation explicitly')
        result.update(installed=True, compatible=True, structural_readiness='available', project_id=identity['project_id'], config_sha256=h.sha(files[CONFIG]), state='installed_inactive')
    except (h.InitializationError, OSError, ValueError, KeyError, TypeError) as error:
        result['diagnostics'].append({'code': 'curator_capability_unavailable', 'message': str(error)[:1200]})
    return result
