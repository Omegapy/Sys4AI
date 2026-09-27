"""Pure static collaboration installation assessment; executes no project Python."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

TASK_MARKER = '<!-- sys4ai:collaboration-default-v1 -->'
OWNER_MARKER = '<!-- sys4ai:collaboration-owner-gates-v1 -->'
PACKAGE = '.agents/skills/collaborate'
# Fixed reviewed provider declaration, independent of selected-project code.
PROFILES_SHA256 = '77240fce4ad473cfa76d97c8e8d6959b5b820dfaf0961d5e87e01b7f32877d64'
REQUIRED_FILES = (
    'SKILL.md', 'README.md',
    'references/collaboration-contract.md', 'references/commands.md',
    'references/task-integration.md', 'references/native-delivery.md',
    'references/knowledge-and-maintenance.md', 'references/project-overview.md',
    'scripts/collaborate.py', 'scripts/collaboration_store.py',
    'scripts/collaboration_task.py', 'scripts/collaboration_read.py',
    'scripts/collaboration_views.py', 'scripts/collaboration_delivery.py',
    'scripts/collaboration_decisions.py', 'scripts/collaboration_proposals.py',
    'scripts/collaboration_overview.py', 'scripts/collaboration_install.py',
    'tests/test_collaboration_acceptance.py', 'tests/test_gate_corrections.py',
)


def _read(root, raw):
    path = root / raw
    if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError('missing-or-unsafe:' + raw)
    parent = path.parent
    while parent != root:
        if parent.is_symlink():
            raise ValueError('unsafe-parent:' + raw)
        parent = parent.parent
    return path.read_bytes()


def owner_profiles(raw):
    """Read only the declarative reviewed provider pins, never import the target."""
    tree = ast.parse(raw.decode('utf-8'))
    values = [node for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'OWNER_PROFILES' for t in node.targets)]
    if len(values) != 1:
        raise ValueError('owner-profiles-unavailable')
    result = ast.literal_eval(values[0].value)
    if not isinstance(result, dict) or not result:
        raise ValueError('owner-profiles-invalid')
    for profile in result.values():
        if not isinstance(profile, dict) or set(profile) != {'files', 'versions'}:
            raise ValueError('owner-profile-invalid')
        if not isinstance(profile['files'], dict) or not profile['files'] or not isinstance(profile['versions'], list):
            raise ValueError('owner-profile-invalid')
        for path, value in profile['files'].items():
            p = Path(path)
            if p.is_absolute() or '..' in p.parts or not path.startswith('.agents/skills/') or len(value) != 64:
                raise ValueError('owner-profile-unsafe')
    if hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != PROFILES_SHA256:
        raise ValueError('owner-profiles-not-reviewed')
    return result


def reviewed_inventory(root):
    """Read recorded reviewed bytes; these cooperative receipts grant no authority."""
    for path in ('control_records/collaboration-installation.json', 'control_records/project-setup.json'):
        try:
            record = json.loads(_read(root, path))
            if record.get('project_root') != str(root):
                continue
            if path.endswith('collaboration-installation.json'):
                if record.get('schema_version') == 1 and record.get('status') == 'completed':
                    return record['package_inventory']
            else:
                for op in reversed(record.get('module_adoptions', [])):
                    if op.get('module_id') == 'collaborate' and op.get('status') == 'completed':
                        return {p: h for p, h in op['packages'][PACKAGE]['after'].items() if h != 'directory'}
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return None


def assess_project(root, *, expected_inventory=None):
    root = Path(root).resolve()
    diagnostics = []
    missing = []
    installed = (root / PACKAGE / 'SKILL.md').is_file()
    profile_name = None
    actual = {}
    for raw in REQUIRED_FILES:
        try:
            _read(root, PACKAGE + '/' + raw)
        except (OSError, ValueError) as exc:
            missing.append(PACKAGE + '/' + raw)
    if missing:
        diagnostics.append({'code': 'COLLAB_PACKAGE_INCOMPLETE', 'paths': missing})
    package = root / PACKAGE
    if package.is_dir() and not package.is_symlink():
        for path in package.rglob('*'):
            if '__pycache__' in path.parts:
                continue
            if path.is_symlink():
                diagnostics.append({'code': 'COLLAB_UNSAFE_PACKAGE', 'path': str(path.relative_to(root))})
            elif path.is_file():
                actual[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_inventory is None:
        expected_inventory = reviewed_inventory(root)
    if expected_inventory is None:
        diagnostics.append({'code': 'COLLAB_REVIEWED_INVENTORY_REQUIRED'})
    if expected_inventory is not None:
        if (not isinstance(expected_inventory, dict) or not expected_inventory
                or any(not isinstance(p, str) or not p.startswith(PACKAGE + '/')
                       or '..' in Path(p).parts or not isinstance(h, str) or len(h) != 64
                       for p, h in expected_inventory.items())):
            raise ValueError('Expected inventory must use complete project-relative collaborate paths')
        mismatch = sorted(p for p in actual.keys() | expected_inventory.keys() if actual.get(p) != expected_inventory.get(p))
        if mismatch:
            diagnostics.append({'code': 'COLLAB_PACKAGE_VERSION', 'paths': mismatch})
    if not diagnostics:
        try:
            profiles = owner_profiles(_read(root, PACKAGE + '/scripts/collaboration_task.py'))
            for name, profile in profiles.items():
                try:
                    if all(hashlib.sha256(_read(root, raw)).hexdigest() == expected for raw, expected in profile['files'].items()):
                        profile_name = name
                        break
                except (OSError, ValueError):
                    continue
            if profile_name is None:
                diagnostics.append({'code': 'COLLAB_OWNER_UNSUPPORTED'})
        except (OSError, ValueError, SyntaxError, TypeError) as exc:
            diagnostics.append({'code': 'COLLAB_OWNER_UNSUPPORTED', 'detail': str(exc)})
    for path, marker in (('.agents/skills/task/SKILL.md', TASK_MARKER),
                         ('.agents/skills/agent-task/SKILL.md', OWNER_MARKER)):
        try:
            present = marker in _read(root, path).decode('utf-8')
        except (OSError, ValueError, UnicodeError):
            present = False
        if not present:
            diagnostics.append({'code': 'COLLAB_DEFAULT_HABIT_MISSING', 'path': path})
    ready = installed and not diagnostics
    return {'schema_version': 1, 'project_root': str(root), 'installed': installed,
            'enabled': ready, 'ready': ready, 'status': 'enabled' if ready else 'unavailable',
            'owner_profile': profile_name, 'missing_files': missing, 'diagnostics': diagnostics,
            'runtime': 'not-exercised',
            'limits': ['Static package, provider and default-habit assessment only.',
                       'Task execution still needs current manager policy, native assignment and exact grants.',
                       'No background service, automatic idle wakeup or v2 broker proof from a v1 owner.']}
