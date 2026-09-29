"""Selected Project app delivery through the existing setup module transaction.

The complete shared reader package is one ownership unit. Project prose is a
separate preserved file. This module parses bytes; it executes no project reader.
"""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import stat

MODULE = 'project-app'
ROOT = '.agents/skills/ontology'
CONFIG = 'project-app.json'
LAUNCHER = 'Launch Project.command'
STARTERS = {CONFIG, LAUNCHER, 'Project App Setup.html'}
FROZEN = ('content', 'modes')
REQUIRED = {'scripts/project_app.py', 'scripts/project_app_core.py',
            'assets/project-app/project-app.schema.json', 'assets/project-app/owner-compatibility.json',
            'explorer/assets/manifest.json'}


def specialize(h, raw, identity):
    config = h.unique_json(raw)
    if not isinstance(config, dict) or config.get('schema_version') != 1 or config.get('project_id') is not None:
        raise h.InitializationError('Project app starter is not neutral')
    config['project_id'] = identity['project_id']
    return h.encoded(config)


def source_files(h, depot):
    template = h.safe(depot / h.TEMPLATE)
    package = h.package_files(template / ROOT)
    if not REQUIRED <= package.keys():
        raise h.InitializationError('Template Project app package is incomplete')
    if stat.S_IMODE((template / LAUNCHER).stat().st_mode) != 0o755:
        raise h.InitializationError('Template Project launcher must have reviewed mode 0755')
    original = {ROOT + '/' + name: raw for name, raw in package.items()}
    original.update({name: h.file_bytes(template / name) for name in STARTERS})
    return original


def plan(h, depot, destination, record, previous_raw):
    original = source_files(h, depot)
    before = h.package_inventory(destination, ROOT)
    after = h.inventory_from_files(ROOT, original)
    owned = h.module_owned_files(record)
    owned_package = h.inventory_from_files(ROOT, {n: d for n, d in owned.items() if n.startswith(ROOT + '/')})
    if before and before != after and before != owned_package:
        raise h.InitializationError('Project app adoption preserves the customized or incomplete reader package; exact reviewed package adoption is required')
    decision = 'preserved-package' if before == after else 'refreshed-owned-package' if before else 'adopted'
    proposed = {n: raw for n, raw in original.items() if n.startswith(ROOT + '/') and decision != 'preserved-package'}
    content, modes, preserved = {}, {}, {}
    for name in (h.IDENTITY, 'SOUL.md', 'AGENTS.md', 'ROLE.md'):
        preserved[name] = h.sha(h.file_bytes(h.destination_file(destination, name)))
    for name in sorted(STARTERS):
        target = h.destination_file(destination, name)
        if target.exists():
            preserved[name] = h.sha(h.file_bytes(target))
        else:
            proposed[name] = specialize(h, original[name], record['identity']) if name == CONFIG else original[name]
            if name == CONFIG:
                content[name] = proposed[name].decode('utf-8')
            modes[name] = 0o755 if name == LAUNCHER else 0o644
    files = {n: {'before': before.get(n), 'after': after.get(n)}
             for n in sorted(before.keys() | after.keys())
             if before.get(n) != 'directory' and after.get(n) != 'directory' and decision != 'preserved-package'}
    for name in proposed.keys() & STARTERS:
        files[name] = {'before': None, 'after': h.sha(proposed[name])}
    sources = []
    for name, raw in sorted(original.items()):
        digest = files[name]['after'] if name in files else after.get(name) if name.startswith(ROOT + '/') else preserved[name]
        sources.append(dict(source=h.TEMPLATE + '/' + name, destination=name, source_sha256=h.sha(raw),
            source_version='sha256:' + h.sha(raw), destination_sha256=digest,
            adoption=('specialized' if name == CONFIG else 'adopted') if name in files else 'preserved-project-owned'))
    operation = dict(schema_version=1, module_id=MODULE, module_version='1.0.0', project_root=str(destination),
        identity=record['identity'], base_receipt=h.archive_record(destination, previous_raw), refresh_dependencies=[],
        new_memory=False, sources=sources, packages={ROOT: dict(decision=decision, before=before, after=after, diagnostic=None)},
        files=files, preserved_files=preserved, content=content, modes=modes,
        operation_id='module-adoption-' + uuid4().hex, status='partial', completed_stages=[], active_stage='assets',
        checks=[], created_at=datetime.now(timezone.utc).isoformat())
    operation['manifest_sha256'] = h.sha(h.encoded({key: operation[key] for key in h.module_frozen(operation)}))
    return operation, proposed


def proposed_files(h, original, operation):
    proposed = dict(original)
    proposed.update({n: raw.encode('utf-8') for n, raw in operation['content'].items()})
    return proposed


def assess(h, destination, operation=None):
    diagnostics = []
    for name in sorted(STARTERS | {ROOT + '/' + n for n in REQUIRED}):
        target = h.destination_file(destination, name)
        if not target.is_file(): diagnostics.append({'path': name, 'code': 'missing'})
    try:
        identity = h.unique_json(h.file_bytes(destination / h.IDENTITY))
        config = h.unique_json(h.file_bytes(destination / CONFIG))
        if config.get('project_id') != identity.get('project_id') or config.get('schema_version') != 1:
            diagnostics.append({'path': CONFIG, 'code': 'identity_mismatch'})
        if not stat.S_IMODE((destination / LAUNCHER).stat().st_mode) & 0o111:
            diagnostics.append({'path': LAUNCHER, 'code': 'launcher_not_executable'})
    except (OSError, ValueError, h.InitializationError):
        diagnostics.append({'path': CONFIG, 'code': 'configuration_unavailable'})
    return {'module': MODULE, 'installed': not diagnostics, 'static_ready': not diagnostics,
            'runtime': 'not-exercised', 'diagnostics': diagnostics}


def check_modes(h, destination, operation, *, complete=False):
    for name, mode in operation['modes'].items():
        path = h.destination_file(destination, name)
        if path.exists() and stat.S_IMODE(path.stat().st_mode) != mode:
            raise h.InitializationError('Project app owned mode changed during adoption: ' + name)
        if complete and not path.exists():
            raise h.InitializationError('Project app owned launcher is missing')


def validate_operation(h, record, destination, op, index):
    required = {'schema_version','operation_id','manifest_sha256','status','completed_stages','active_stage','checks','created_at', *h.module_frozen(op)}
    optional = {'capabilities','current_files','verified_at','recovery','rerun','static_health'}
    if (set(op) - required - optional or not required <= op.keys() or op['schema_version'] != 1
            or op['module_version'] != '1.0.0' or op['identity'] != record['identity'] or op['project_root'] != str(destination)
            or op['refresh_dependencies'] != [] or op['new_memory'] is not False
            or not h.re.fullmatch(r'module-adoption-[0-9a-f]{32}', op['operation_id'])
            or op['manifest_sha256'] != h.sha(h.encoded({k: op[k] for k in h.module_frozen(op)}))):
        raise h.InitializationError('invalid frozen Project app operation')
    stages = op['completed_stages']
    if (op['status'] not in {'partial','completed'} or stages != h.MODULE_STAGES[:len(stages)]
            or op['active_stage'] not in {*h.MODULE_STAGES,None}
            or op['status'] == 'completed' and (stages != h.MODULE_STAGES or op['active_stage'] is not None)
            or op['status'] == 'partial' and index != len(record['module_adoptions'])-1):
        raise h.InitializationError('invalid Project app lifecycle')
    archive = op['base_receipt']
    if set(archive) != {'path','sha256'} or archive['path'] != 'control_records/project-setup-history/' + archive['sha256'] + '.json':
        raise h.InitializationError('invalid Project app base receipt')
    raw = h.file_bytes(h.destination_file(destination, archive['path'])); old = h.unique_json(raw)
    if (h.sha(raw) != archive['sha256'] or any(old.get(k) != record.get(k) for k in h.BASE_IMMUTABLE)
            or len(old.get('module_adoptions', [])) != index
            or any(p['operation_id'] != record['module_adoptions'][i]['operation_id'] or p['manifest_sha256'] != record['module_adoptions'][i]['manifest_sha256'] or p['status'] != 'completed' for i,p in enumerate(old.get('module_adoptions',[])))):
        raise h.InitializationError('Project app original setup provenance changed')
    if set(op['packages']) != {ROOT}: raise h.InitializationError('invalid Project app package scope')
    package = op['packages'][ROOT]
    if (set(package) != {'decision','before','after','diagnostic'} or package['decision'] not in {'adopted','refreshed-owned-package','preserved-package'}
            or package['decision'] == 'adopted' and package['before']
            or package['decision'] == 'preserved-package' and package['before'] != package['after']):
        raise h.InitializationError('invalid Project app package decision')
    for inv in (package['before'],package['after']):
        for name,digest in inv.items():
            h.safe(destination / name)
            if (name != ROOT and not name.startswith(ROOT + '/') or '..' in Path(name).parts or Path(name).as_posix() != name
                    or digest != 'directory' and not h.SHA256.fullmatch(digest)
                    or name != ROOT and inv.get(Path(name).parent.as_posix()) != 'directory'):
                raise h.InitializationError('invalid Project app inventory')
        if inv and inv.get(ROOT) != 'directory': raise h.InitializationError('Project app package root missing')
    if package['decision'] == 'refreshed-owned-package':
        owned = {n:d for n,d in h.module_owned_files(old).items() if n.startswith(ROOT + '/')}
        if package['before'] != h.inventory_from_files(ROOT,owned):
            raise h.InitializationError('Project app refresh lacks complete prior ownership')
    expected = {} if package['decision'] == 'preserved-package' else {n:{'before':package['before'].get(n),'after':package['after'].get(n)} for n in package['before'].keys() | package['after'].keys() if package['before'].get(n) != 'directory' and package['after'].get(n) != 'directory'}
    if {n:v for n,v in op['files'].items() if n.startswith(ROOT + '/')} != expected:
        raise h.InitializationError('Project app package change inventory disagrees')
    for name,change in op['files'].items():
        h.destination_file(destination,name)
        if (name not in STARTERS and not name.startswith(ROOT + '/') or set(change) != {'before','after'}
                or any(d is not None and not h.SHA256.fullmatch(d) for d in change.values())):
            raise h.InitializationError('invalid Project app target')
        if name in STARTERS and (change['before'] is not None or change['after'] is None):
            raise h.InitializationError('Project app cannot overwrite existing content or launcher')
    starters = op['files'].keys() & STARTERS
    if op['modes'] != {n:0o755 if n == LAUNCHER else 0o644 for n in starters}:
        raise h.InitializationError('Project app executable mode lacks exact ownership')
    if set(op['content']) != ({CONFIG} if CONFIG in starters else set()):
        raise h.InitializationError('invalid Project app content scope')
    if CONFIG in op['content'] and h.sha(op['content'][CONFIG].encode()) != op['files'][CONFIG]['after']:
        raise h.InitializationError('Project app content recovery bytes changed')
    names = set()
    for row in op['sources']:
        name = row['destination']; digest = op['files'][name]['after'] if name in op['files'] else package['after'].get(name) if name.startswith(ROOT + '/') else op['preserved_files'].get(name)
        adoption = ('specialized' if name == CONFIG else 'adopted') if name in op['files'] else 'preserved-project-owned'
        if (name in names or name not in STARTERS and not name.startswith(ROOT + '/') or row['source'] != h.TEMPLATE + '/' + name
                or not h.SHA256.fullmatch(row['source_sha256']) or row['source_version'] != 'sha256:' + row['source_sha256']
                or row['destination_sha256'] != digest or row['adoption'] != adoption
                or adoption == 'adopted' and row['source_sha256'] != digest):
            raise h.InitializationError('Project app source provenance disagrees')
        names.add(name)
    if names != STARTERS | {n for n,d in package['after'].items() if d != 'directory'}:
        raise h.InitializationError('Project app source inventory incomplete')
    if not {h.IDENTITY,'SOUL.md','AGENTS.md','ROLE.md'} <= op['preserved_files'].keys():
        raise h.InitializationError('Project app governance preservation missing')
    for name,digest in op['preserved_files'].items():
        h.destination_file(destination,name)
        if name in op['files'] or not h.SHA256.fullmatch(digest):
            raise h.InitializationError('invalid preserved Project app input')
