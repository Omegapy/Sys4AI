"""Add default collaboration through the existing setup/module receipt transaction.

Only the bundled hash-pinned pure inspector executes. Copied owner/skill Python
is inspected as bytes or literal AST data, never imported during setup.
"""
import ast
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

MODULE = 'collaborate'
ROOT = '.agents/skills/collaborate'
GUIDANCE = {
    '.agents/skills/task/SKILL.md': ('## Task collaboration ownership', '<!-- sys4ai:collaboration-default-v1 -->'),
    '.agents/skills/agent-task/SKILL.md': ('## Collaboration message and owner gates', '<!-- sys4ai:collaboration-owner-gates-v1 -->'),
}
FROZEN = ('guidance_contents',)
INSPECTOR_SHA256 = '329fe3ca24b252a8f40b73cc8b85129e906595a38ba6f9c917c18301fab3a8ee'


def inspector(h):
    path = Path(__file__).resolve().parent.parent / 'assets/collaboration_install.py'
    raw = h.file_bytes(path)
    if h.sha(raw) != INSPECTOR_SHA256:
        raise h.InitializationError('collaboration inspector is not the reviewed initializer asset')
    spec = importlib.util.spec_from_file_location('_sys4ai_initializer_collaboration_inspector_' + INSPECTOR_SHA256, path)
    module = importlib.util.module_from_spec(spec)
    # Freeze verified bytes rather than importing a replaceable path.
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def source_files(h, depot):
    template = h.safe(depot / h.TEMPLATE)
    original = {ROOT + '/' + name: raw for name, raw in h.package_files(template / ROOT).items()}
    original.update({name: h.file_bytes(template / name) for name in GUIDANCE})
    expected = {name: h.sha(raw) for name, raw in original.items() if name.startswith(ROOT + '/')}
    assessment = inspector(h).assess_project(template, expected_inventory=expected)
    if not assessment['enabled']:
        raise h.InitializationError('Template collaboration is incomplete or incompatible: ' + str(assessment.get('diagnostics', []))[:1000])
    return original


def profiles(h, raw):
    try:
        value = next(ast.literal_eval(node.value) for node in ast.parse(raw).body
                     if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'OWNER_PROFILES' for target in node.targets))
    except (SyntaxError, StopIteration, ValueError, TypeError) as error:
        raise h.InitializationError('collaboration owner profiles are unavailable as literal data') from error
    return value


def owner_inputs(h, destination, original):
    for profile in profiles(h, original[ROOT + '/scripts/collaboration_task.py']).values():
        files = profile['files']
        try:
            actual = {name: h.sha(h.file_bytes(h.destination_file(destination, name))) for name in files}
        except (h.InitializationError, OSError):
            continue
        if actual == files:
            return actual
    raise h.InitializationError('collaboration enabled-readiness blocked: unsupported current Task owner; preserved without execution')


def section(raw, heading, marker):
    text = raw.decode('utf-8')
    start = text.index(heading + '\n')
    end = text.find('\n## ', start + len(heading))
    block = text[start:] if end == -1 else text[start:end]
    if marker not in block:
        raise ValueError('collaboration source instruction marker missing')
    return ('\n\n' + block.strip() + '\n').encode()


def plan(h, depot, destination, record, previous_raw):
    original = source_files(h, depot)
    owner = owner_inputs(h, destination, original)
    before = h.package_inventory(destination, ROOT)
    expected = h.inventory_from_files(ROOT, {name: h.sha(raw) for name, raw in original.items() if name.startswith(ROOT + '/')})
    if before and before != expected:
        raise h.InitializationError('collaboration enabled-readiness blocked: customized/incomplete package is preserved as a whole')
    owned = h.module_owned_files(record)
    proposed = {name: raw for name, raw in original.items() if name.startswith(ROOT + '/') and not before}
    guidance_contents = {}
    preserved = {name: h.sha(h.file_bytes(h.destination_file(destination, name)))
                 for name in (h.IDENTITY, 'SOUL.md', 'AGENTS.md', 'ROLE.md')}
    preserved.update(owner)
    for name, (heading, marker) in GUIDANCE.items():
        target = h.destination_file(destination, name)
        if not target.is_file():
            raise h.InitializationError('collaboration enabled-readiness blocked: missing preserved Task guidance: ' + name)
        raw = h.file_bytes(target)
        if marker.encode() not in raw:
            if owned.get(name) != h.sha(raw):
                raise h.InitializationError('collaboration enabled-readiness blocked: customized unbound Task guidance is preserved: ' + name)
            proposed[name] = raw.rstrip() + section(original[name], heading, marker)
            guidance_contents[name] = proposed[name].decode('utf-8')
        else:
            preserved[name] = h.sha(raw)
    files = {name: {'before': h.sha(h.file_bytes(h.destination_file(destination, name))) if h.destination_file(destination, name).exists() else None,
                    'after': h.sha(raw)} for name, raw in proposed.items()}
    packages = {ROOT: {'decision': 'preserved-package' if before else 'adopted', 'before': before, 'after': expected, 'diagnostic': None}}
    sources = []
    for name, raw in sorted(original.items()):
        after = files[name]['after'] if name in files else expected.get(name) if name.startswith(ROOT + '/') else preserved.get(name)
        sources.append(dict(source=h.TEMPLATE + '/' + name, destination=name, source_sha256=h.sha(raw),
            source_version='sha256:' + h.sha(raw), destination_sha256=after,
            adoption=('specialized' if name in GUIDANCE else 'adopted') if name in files else 'preserved-project-owned'))
    archive = h.archive_record(destination, previous_raw)
    operation = dict(schema_version=1, module_id=MODULE, module_version='1.0.0', project_root=str(destination), identity=record['identity'],
        base_receipt=archive, refresh_dependencies=[], new_memory=False, sources=sources, packages=packages, files=files,
        preserved_files=preserved, guidance_contents=guidance_contents, operation_id='module-adoption-' + uuid4().hex,
        status='partial', completed_stages=[], active_stage='assets', checks=[], created_at=datetime.now(timezone.utc).isoformat())
    operation['manifest_sha256'] = h.sha(h.encoded({key: operation[key] for key in h.module_frozen(operation)}))
    return operation, proposed


def proposed_files(h, original, operation):
    proposed = {name: raw for name, raw in original.items() if name.startswith(ROOT + '/')}
    proposed.update({name: raw.encode('utf-8') for name, raw in operation['guidance_contents'].items()})
    return proposed


def assess(h, destination, operation=None, *, expected_inventory=None):
    if expected_inventory is not None:
        expected = expected_inventory or None
    elif operation is None:
        depot, _ = h.installed_locations()
        original = source_files(h, depot)
        expected = {name: h.sha(raw) for name, raw in original.items() if name.startswith(ROOT + '/')}
    else:
        expected = {row['destination']: row['destination_sha256'] for row in operation['sources'] if row['destination'].startswith(ROOT + '/')}
    return inspector(h).assess_project(destination, expected_inventory=expected)


def validate_operation(h, record, destination, operation, index):
    required = {'schema_version', 'operation_id', 'manifest_sha256', 'status', 'completed_stages', 'active_stage', 'checks', 'created_at', *h.module_frozen(operation)}
    optional = {'capabilities', 'current_files', 'verified_at', 'recovery', 'rerun', 'static_health'}
    if (set(operation) - required - optional or not required <= operation.keys()
            or operation['schema_version'] != 1 or operation['module_version'] != '1.0.0'
            or operation['identity'] != record['identity'] or operation['project_root'] != str(destination)
            or operation['refresh_dependencies'] != [] or operation['new_memory'] is not False
            or not h.re.fullmatch(r'module-adoption-[0-9a-f]{32}', operation['operation_id'])
            or operation['manifest_sha256'] != h.sha(h.encoded({key: operation[key] for key in h.module_frozen(operation)}))):
        raise h.InitializationError('invalid frozen collaboration module identity')
    stages = operation['completed_stages']
    if (operation['status'] not in {'partial', 'completed'} or stages != h.MODULE_STAGES[:len(stages)]
            or operation['active_stage'] not in {*h.MODULE_STAGES, None}
            or operation['status'] == 'completed' and (stages != h.MODULE_STAGES or operation['active_stage'] is not None)
            or operation['status'] == 'partial' and index != len(record['module_adoptions']) - 1):
        raise h.InitializationError('invalid collaboration module lifecycle')
    archive = operation['base_receipt']
    raw = h.file_bytes(h.destination_file(destination, archive['path']))
    old = h.unique_json(raw)
    if (set(archive) != {'path', 'sha256'} or h.sha(raw) != archive['sha256']
            or archive['path'] != 'control_records/project-setup-history/' + archive['sha256'] + '.json'
            or any(old.get(key) != record.get(key) for key in h.BASE_IMMUTABLE)
            or len(old.get('module_adoptions', [])) != index
            or any(prior['operation_id'] != record['module_adoptions'][position]['operation_id'] or prior['manifest_sha256'] != record['module_adoptions'][position]['manifest_sha256'] or prior['status'] != 'completed'
                   for position, prior in enumerate(old.get('module_adoptions', [])))):
        raise h.InitializationError('collaboration adoption lacks exact base receipt provenance')
    if set(operation['packages']) != {ROOT}:
        raise h.InitializationError('invalid collaboration package scope')
    package = operation['packages'][ROOT]
    if (set(package) != {'decision', 'before', 'after', 'diagnostic'} or package['decision'] not in {'adopted', 'preserved-package'}
            or package['decision'] == 'adopted' and package['before']
            or package['decision'] == 'preserved-package' and package['before'] != package['after']):
        raise h.InitializationError('collaboration cannot overwrite an existing package')
    for inventory in (package['before'], package['after']):
        for name, digest in inventory.items():
            if (name != ROOT and not name.startswith(ROOT + '/') or h.Path(name).as_posix() != name or '..' in h.Path(name).parts
                    or digest != 'directory' and not h.SHA256.fullmatch(digest)
                    or name != ROOT and inventory.get(h.Path(name).parent.as_posix()) != 'directory'):
                raise h.InitializationError('invalid collaboration package inventory')
            h.safe(destination / name)
        if inventory and inventory.get(ROOT) != 'directory':
            raise h.InitializationError('collaboration package lacks root directory evidence')
    package_changes = {name for name in operation['files'] if name.startswith(ROOT + '/')}
    expected_changes = set() if package['decision'] == 'preserved-package' else {name for name, digest in package['after'].items() if digest != 'directory'}
    if package_changes != expected_changes or set(operation['guidance_contents']) != set(operation['files']) - package_changes:
        raise h.InitializationError('collaboration module omits or adds target changes')
    for name, change in operation['files'].items():
        h.destination_file(destination, name)
        if (set(change) != {'before', 'after'} or not h.SHA256.fullmatch(change['after']) or change['before'] is not None and not h.SHA256.fullmatch(change['before'])
                or name not in GUIDANCE and not name.startswith(ROOT + '/')):
            raise h.InitializationError('invalid collaboration target change')
        if name in GUIDANCE:
            if h.sha(operation['guidance_contents'][name].encode()) != change['after'] or GUIDANCE[name][1] not in operation['guidance_contents'][name] or h.module_owned_files(old).get(name) != change['before']:
                raise h.InitializationError('collaboration guidance edit lacks receipt ownership')
    source_names = set()
    for row in operation['sources']:
        name = row['destination']
        if (name in source_names or row['source'] != h.TEMPLATE + '/' + name or row['source_version'] != 'sha256:' + row['source_sha256']
                or not h.SHA256.fullmatch(row['source_sha256']) or not h.SHA256.fullmatch(row['destination_sha256'])
                or name not in GUIDANCE and not name.startswith(ROOT + '/')):
            raise h.InitializationError('invalid collaboration source provenance')
        source_names.add(name)
        after = operation['files'][name]['after'] if name in operation['files'] else package['after'].get(name) if name.startswith(ROOT + '/') else operation['preserved_files'].get(name)
        adoption = ('specialized' if name in GUIDANCE else 'adopted') if name in operation['files'] else 'preserved-project-owned'
        if row['destination_sha256'] != after or row['adoption'] != adoption or adoption == 'adopted' and row['source_sha256'] != after:
            raise h.InitializationError('collaboration source/target evidence disagrees')
    if source_names != {name for name, digest in package['after'].items() if digest != 'directory'} | set(GUIDANCE):
        raise h.InitializationError('collaboration source inventory is incomplete')
    if not {h.IDENTITY, 'SOUL.md', 'AGENTS.md', 'ROLE.md'} <= operation['preserved_files'].keys():
        raise h.InitializationError('collaboration lacks preserved governance')
    for name, digest in operation['preserved_files'].items():
        h.destination_file(destination, name)
        if not h.SHA256.fullmatch(digest) or name in operation['files']:
            raise h.InitializationError('invalid preserved collaboration input')
