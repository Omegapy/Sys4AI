"""Session-enabled v11 Curator capability and exact adoption through the setup owner.

This inspector parses source/configuration only. Runtime authority, host setup,
Task activation and owner publication remain separate selected operations.
"""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

MODULE = 'project-curator'
EDITION = 'governance-starter-v12'
SESSION = 'curator-session.yaml'
CONFIG = 'curator.yaml'
REFERENCE = 'reference-assets/CURATION-depo'
ROLES = ('curator-manager', 'documentation-curator', 'knowledge-curator', 'improvement-maintenance')
SKILLS = ('curate', 'agent-task', 'task', 'memory', 'ontology', 'what-did-you-learn', 'manage-subagent-roles', 'init-new-project')
LEGACY_PACKAGES = tuple('.agents/skills/' + name for name in SKILLS) + (REFERENCE,) + tuple('Roles/' + name for name in ROLES)
INTEGRATION_REFERENCE = 'reference-assets/ONTOLOGY-depo/integrations/curator/1.0.0'
PACKAGES = (*LEGACY_PACKAGES, INTEGRATION_REFERENCE)
SPECIAL_FILES = {CONFIG, SESSION, 'CURATOR.md', 'document-ownership.json', 'Roles/INDEX.md'}
STARTERS = {CONFIG, SESSION, 'CURATOR.md', 'document-ownership.json'}
RESOURCES = {REFERENCE + '/contract.json', *('.agents/skills/' + name + '/SKILL.md' for name in SKILLS),
             *('Roles/' + name + '/' + leaf for name in ROLES for leaf in ('AGENTS.md', 'ROLE.md'))}
FROZEN = ('new_curator_files', 'protected_inventory', 'prerequisites')


def fail(h, condition, message):
    if not condition: raise h.InitializationError(message)


def source_files(h, depot, *, legacy=False):
    original = h.template_sources(depot)[0]
    return {name: raw for name, raw in original.items() if name in SPECIAL_FILES or any(name.startswith(root + '/') for root in (LEGACY_PACKAGES if legacy else PACKAGES))}


def validate_static(h, files, *, neutral, identity=None):
    fail(h, (STARTERS - {SESSION}) | RESOURCES <= files.keys(), 'Curator requires its complete charter, configuration, owner packages and paired roles')
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
    if SESSION in files:
        session = validate_session(h, h.unique_json(files[SESSION]))
        fail(h, session['project_id'] == (None if neutral else identity['project_id']), 'Curator session identity mismatch')
        fail(h, not neutral or not session['enabled'], 'Template session policy must remain neutral')
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



def validate_session(h, value):
    expected = {'schema_version', 'project_id', 'enabled', 'mode', 'catch_up',
                'unattended_background_ai', 'notices', 'bounds', 'iteration_limit', 'event_limit'}
    fail(h, isinstance(value, dict) and set(value) == expected and value['schema_version'] == 1
         and type(value['enabled']) is bool, 'unsupported Curator session policy')
    fail(h, value['mode'] == 'project-session' and value['catch_up'] == 'on-start-and-return'
         and value['unattended_background_ai'] is False and value['notices'] == 'actionable', 'unsupported Curator session mode')
    limits = {'model_calls': 2, 'work_seconds': 30, 'candidate_bytes': 1000000, 'concurrent_agents': 3}
    fail(h, isinstance(value['bounds'], dict) and set(value['bounds']) == set(limits)
         and all(type(value['bounds'][key]) is int and 0 <= value['bounds'][key] <= limit for key,limit in limits.items()), 'invalid Curator session bounds')
    fail(h, all(type(value[key]) is int and 0 <= value[key] <= limit for key,limit in [('iteration_limit',1),('event_limit',50)]), 'invalid Curator session event/iteration bounds')
    fail(h, value['project_id'] is None or isinstance(value['project_id'],str) and value['project_id'], 'invalid Curator session identity')
    fail(h, not value['enabled'] or value['project_id'] is not None, 'neutral session policy cannot be enabled')
    return value


def specialize_session(h, raw, identity):
    value = deepcopy(validate_session(h, h.unique_json(raw)))
    fail(h, value['project_id'] is None and not value['enabled'], 'specialize only a neutral session starter')
    value.update(project_id=identity['project_id'], enabled=True)
    return h.encoded(value)


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
    allowed=h._integration('owner_changes',destination,operation) if operation.get('schema_version')==2 else {}
    current=protected_inventory(h, destination, changed=set(operation['files'])|set(allowed))
    expected={name:value for name,value in operation['protected_inventory'].items() if name not in allowed}
    fail(h, current == expected,
         'Curator adoption observed changed authored records, settings, roles, identity or licensing')


def proposed_files(h, destination, identity, original, *, new_curator_files):
    proposed = {name: raw for name, raw in original.items() if any(name.startswith(root + '/') for root in PACKAGES)}
    for name in new_curator_files:
        proposed[name] = (specialize(h, original[name], identity, destination=destination) if name == CONFIG else
                          specialize_session(h, original[name], identity) if name == SESSION else original[name])
    role_files = {name: h.file_bytes(h.destination_file(destination, name)) for name, value in h.package_inventory(destination, 'Roles').items() if value != 'directory' and name != 'Roles/INDEX.md'}
    role_files.update(proposed)
    role_files['SOUL.md'] = h.file_bytes(h.destination_file(destination, 'SOUL.md'))
    proposed['Roles/INDEX.md'] = h.role_index_bytes(role_files, required=True, contract=EDITION)
    return proposed


def plan(h, depot, destination, record, previous_raw, refresh_modules=()):
    original = source_files(h, depot); validate_static(h, original, neutral=True)
    h.exact_role_root(destination, 'Roles')
    new_files = sorted(name for name in STARTERS if not h.destination_file(destination, name).exists())
    existing = {name: h.file_bytes(h.destination_file(destination, name)) for name in STARTERS if name not in new_files}
    if CONFIG in existing:
        current={**original, **existing}
        if SESSION in new_files:current.pop(SESSION,None)
        validate_static(h, current, neutral=False, identity=record['identity'])
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
        adoption = ('specialized' if name in {CONFIG, SESSION, 'Roles/INDEX.md'} else 'adopted') if name in changes else 'preserved-project-owned' if final else 'skipped-existing-package'
        sources.append({'source': h.TEMPLATE + '/' + name, 'destination': name, 'source_sha256': h.sha(raw), 'source_version': 'sha256:' + h.sha(raw), 'destination_sha256': final, 'adoption': adoption})
    checksum = h.sha(previous_raw)
    operation = {'schema_version': 2, 'integration_edition': h.INTEGRATION.EDITION, 'generated_contents': {}, 'refresh_modules': list(refresh_modules), 'curator_integration': {'edition':h.INTEGRATION.EDITION,'mode':'owner-publication','status':'pending','operation_id':None}, 'module_id': MODULE, 'module_version': '1.0.0', 'operation_id': 'module-adoption-' + uuid4().hex,
                 'project_root': str(destination), 'identity': deepcopy(record['identity']),
                 'base_receipt': {'path': 'control_records/project-setup-history/' + checksum + '.json', 'sha256': checksum},
                 'refresh_dependencies': [], 'new_memory': False, 'sources': sources, 'packages': packages, 'files': changes,
                 'preserved_files': preserved, 'new_curator_files': new_files, 'protected_inventory': protected_inventory(h, destination, changed=changes),
                 'prerequisites': [{'module_id': name, 'disposition': 'existing-owner-compatible-package'} for name in ('task', 'memory', 'ontology', 'learning')],
                 'status': 'partial', 'completed_stages': [], 'active_stage': 'assets', 'checks': [], 'created_at': datetime.now(timezone.utc).isoformat()}
    prior_modules=record.get('module_adoptions',[])
    if prior_modules and prior_modules[-1].get('module_id')==h.ONTOLOGY_MODULE and prior_modules[-1].get('new_ontology') and prior_modules[-1].get('status')=='completed':
        effective=dict(original)
        for name in list(effective):
            target=h.destination_file(destination,name)
            if name not in changes and target.is_file():effective[name]=h.file_bytes(target)
        effective.update(proposed)
        with h.INTEGRATION.owner(h) as api:
            for name in api.source_paths(h.INTEGRATION.recipe_files(original)):
                if name not in effective:effective[name]=h.file_bytes(h.destination_file(destination,name))
        effective['ontology.yaml']=h.file_bytes(h.destination_file(destination,'ontology.yaml'))
        generated=h._integration('render',record['identity'],effective,original)
        for name,raw in generated.items():
            target=h.destination_file(destination,name)
            if name!='ontology.yaml' and target.exists():raise h.InitializationError('Reserved Curator graph is unowned: '+name)
            changes[name]={'before':h.sha(h.file_bytes(target)) if target.exists() else None,'after':h.sha(raw)}
            proposed[name]=raw
            preserved.pop(name,None)
        operation['generated_contents']={name:raw.decode() for name,raw in generated.items()}
        operation['curator_integration']={'edition':h.INTEGRATION.EDITION,'mode':'setup-generated','status':'pending','files':{name:h.sha(raw) for name,raw in generated.items()},'prerequisite_operation':prior_modules[-1]['operation_id']}
        operation['protected_inventory']=protected_inventory(h,destination,changed=changes)
    operation['manifest_sha256'] = h.sha(h.encoded({key: operation[key] for key in h.module_frozen(operation)}))
    return operation, proposed


def selected_source_files(h, depot, operation): return source_files(h, depot, legacy=operation.get('schema_version')==1)


def validate_operation(h, destination, operation):
    if operation.get('schema_version')==2:
        fail(h,operation.get('integration_edition')==h.INTEGRATION.EDITION and operation.get('refresh_modules') in ([],[MODULE])
             and operation.get('curator_integration',{}).get('edition')==h.INTEGRATION.EDITION,'invalid integrated Curator operation edition/selection')
        generated=operation.get('generated_contents',{})
        fail(h,isinstance(generated,dict) and (not generated or set(generated)=={*h.INTEGRATION.GENERATED,'ontology.yaml'}),'invalid generated integration inventory')
        for name,raw in generated.items():
            fail(h,isinstance(raw,str) and operation['files'].get(name,{}).get('after')==h.sha(raw.encode()),'generated integration differs from frozen target')
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


def assess(h, destination, *, integration_required=None):
    result = {'module_id': MODULE, 'module_version': '1.0.0', 'installed': False, 'configured': False, 'authorized': False,
              'compatible': False, 'structural_readiness': 'unavailable', 'runtime_observed': False, 'runtime': 'not-exercised',
              'inspector_execution': 'none', 'publication_enabled': False, 'diagnostics': [],
              'compatibility_scope': 'static-package-only',
              'connected_application': {'state': 'not_exercised', 'code': 'native_runtime_not_exercised'}}
    try:
        files = {name: h.file_bytes(h.destination_file(destination, name)) for root in PACKAGES for name, value in h.package_inventory(destination, root).items() if value != 'directory'}
        for name in SPECIAL_FILES:
            if name != SESSION or h.destination_file(destination, name).exists():
                files[name] = h.file_bytes(h.destination_file(destination, name))
        result['installed'] = (STARTERS - {SESSION}) <= files.keys()
        if integration_required is None:
            receipt = h.destination_file(destination,h.RECORD)
            saved = h.unique_json(h.file_bytes(receipt)) if receipt.exists() else {}
            integration_required = saved.get('setup_contract') in {h.INTEGRATED_CONTRACT, h.SETUP_CONTRACT} or any(op.get('integration_edition') == h.INTEGRATION.EDITION for op in saved.get('module_adoptions',[]))
        locked = h._static('inventory', legacy=not integration_required).get('curator_locked_resources', {})
        current_locked=h._static('inventory').get('curator_locked_resources',{})
        fail(h, bool(locked) and all(name in files and h.sha(files[name]) in ({expected,current_locked.get(name)} if not integration_required else {expected}) for name,expected in locked.items()),
             'Curator owner code differs from its reviewed compatibility inventory; customized code is preserved without execution')
        identity = h.unique_json(h.file_bytes(h.destination_file(destination, h.IDENTITY)))
        cfg = validate_static(h, files, neutral=False, identity=identity)
        fail(h, cfg['project']['coordination_root'] == str(destination), 'Curator coordination root changed; reconcile relocation explicitly')
        session = h.unique_json(files[SESSION]) if SESSION in files else None
        enabled = session is not None and session['enabled']
        semantic = h._integration('assess',destination) if integration_required else {'required':False,'edition':'historical-package-only'}
        if integration_required: fail(h,semantic['compatible'],str(semantic['diagnostics']))
        result['semantic_integration'] = semantic
        result.update(installed=True, compatible=True, structural_readiness='available', project_id=identity['project_id'], config_sha256=h.sha(files[CONFIG]),
                      configured=enabled, session_enabled=enabled, unattended_background_ai=False,
                      state='installed_session_enabled' if enabled else 'installed_inactive')
    except (h.InitializationError, OSError, ValueError, KeyError, TypeError) as error:
        result['diagnostics'].append({'code': 'curator_capability_unavailable', 'message': str(error)[:1200]})
    return result
